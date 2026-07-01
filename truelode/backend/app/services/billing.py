"""Billing core: wallet movements, per-batch PAYG, seat/flat cycles, transaction gates.

The wallet is prepaid. Every movement appends an immutable BillingEntry and updates
the wallet balance in the same DB session (the caller commits). Exempt accounts
(REGULATOR / ADMIN) never accrue charges and always pass the transaction gate.
"""
from flask import current_app

from app.extensions import db
from app.models.account import Account
from app.models.billing import BillingEntry, Plan, Subscription, Wallet
from app.models.enums import AccountStatus, AccountType, BillingKind, PlanType


# ----- provisioning -------------------------------------------------------------

def default_plan(account_type: str) -> Plan | None:
    ptype = (PlanType.INDIVIDUAL_FLAT if account_type == AccountType.INDIVIDUAL
             else PlanType.ORG)
    return Plan.query.filter_by(plan_type=ptype).first()


def get_wallet(account_id: str) -> Wallet | None:
    return Wallet.query.filter_by(account_id=account_id).first()


def provision_account(account: Account, starting_balance: float = 0.0) -> Wallet:
    """Create the wallet (+ subscription for billable accounts) at registration."""
    wallet = get_wallet(account.id)
    if not wallet:
        wallet = Wallet(account_id=account.id, balance_usd=starting_balance)
        db.session.add(wallet)
    if not account.exempt:
        plan = default_plan(account.account_type)
        if plan and not Subscription.query.filter_by(account_id=account.id).first():
            db.session.add(Subscription(account_id=account.id, plan_id=plan.id))
    db.session.flush()
    return wallet


# ----- fee lookup ---------------------------------------------------------------

def _plan_for(account: Account) -> Plan | None:
    sub = Subscription.query.filter_by(account_id=account.id).first()
    if sub and sub.plan:
        return sub.plan
    return default_plan(account.account_type)


def per_batch_fee(account: Account) -> float:
    plan = _plan_for(account)
    if plan and plan.per_batch_fee_usd:
        return plan.per_batch_fee_usd
    return float(current_app.config.get("PER_BATCH_FEE_USD", 0.0))


def seat_fee(account: Account) -> float:
    plan = _plan_for(account)
    if plan and plan.seat_fee_usd:
        return plan.seat_fee_usd
    return float(current_app.config.get("SEAT_FEE_USD", 0.0))


def flat_fee(account: Account) -> float:
    plan = _plan_for(account)
    if plan and plan.flat_fee_usd:
        return plan.flat_fee_usd
    return float(current_app.config.get("INDIVIDUAL_FLAT_USD", 0.0))


# ----- wallet movements ---------------------------------------------------------

def _move(account: Account, kind: str, amount: float, ref_id: str | None = None,
          note: str | None = None) -> BillingEntry | None:
    """Apply a signed amount to the wallet and append a ledger entry."""
    wallet = get_wallet(account.id)
    if not wallet:
        wallet = provision_account(account)
    wallet.balance_usd = round(wallet.balance_usd + amount, 4)
    entry = BillingEntry(account_id=account.id, kind=kind, amount_usd=amount,
                         ref_id=ref_id, balance_after=wallet.balance_usd, note=note)
    db.session.add(entry)
    if wallet.balance_usd < 0 and not account.exempt:
        account.status = AccountStatus.DELINQUENT
    return entry


def credit_wallet(account: Account, amount: float, ref_id: str | None = None,
                  note: str | None = None) -> BillingEntry:
    entry = _move(account, BillingKind.TOPUP, abs(amount), ref_id, note or "top-up")
    if account.status == AccountStatus.DELINQUENT and get_wallet(account.id).balance_usd >= 0:
        account.status = AccountStatus.ACTIVE
    return entry


# ----- charges ------------------------------------------------------------------

def account_can_transact(account: Account | None) -> bool:
    """True if the account may perform a billable action (e.g. create a batch)."""
    if not account:
        return False
    if account.exempt:
        return True
    if account.status == AccountStatus.SUSPENDED:
        return False
    wallet = get_wallet(account.id)
    balance = wallet.balance_usd if wallet else 0.0
    return balance >= per_batch_fee(account)


def charge_batch(account: Account, batch_id: str | None = None) -> BillingEntry | None:
    """Debit one batch's PAYG fee. No-op for exempt accounts."""
    if account.exempt:
        return None
    fee = per_batch_fee(account)
    if fee <= 0:
        return None
    return _move(account, BillingKind.BATCH_PAYG, -fee, batch_id,
                 note="batch created")


def run_billing_cycle(account: Account) -> dict:
    """Accrue recurring fees: INDIVIDUAL flat, or ORG per active staff seat."""
    if account.exempt:
        return {"account_id": account.id, "charged": 0.0, "skipped": "exempt"}
    if account.account_type == AccountType.INDIVIDUAL:
        fee = flat_fee(account)
        if fee > 0:
            _move(account, BillingKind.INDIVIDUAL_FLAT, -fee, account.id,
                  note="monthly subscription")
        return {"account_id": account.id, "charged": fee, "seats": 1}
    # ENTERPRISE: charge per active staff user
    from app.models.user import User
    seats = User.query.filter_by(account_id=account.id, active=True).count()
    per = seat_fee(account)
    total = round(per * seats, 2)
    if total > 0:
        _move(account, BillingKind.SEAT_FEE, -total, account.id,
              note=f"{seats} seat(s) @ ${per}")
    return {"account_id": account.id, "charged": total, "seats": seats}
