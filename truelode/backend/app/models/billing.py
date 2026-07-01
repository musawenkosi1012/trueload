"""Billing models: plans, subscriptions, prepaid wallet, ledger and payments.

Money is stored in USD as floats (cents-precision is fine for this demo). The wallet
is prepaid: Payonify top-ups credit it; per-batch PAYG, per-seat and flat fees debit it.
"""
from app.extensions import db

from .base import TimestampMixin, utcnow
from .enums import BillingKind, PaymentStatus, PlanType


class Plan(TimestampMixin, db.Model):
    __tablename__ = "plan"

    name = db.Column(db.String(80), nullable=False)
    plan_type = db.Column(db.String(20), nullable=False)  # enums.PlanType
    flat_fee_usd = db.Column(db.Float, default=0.0)       # INDIVIDUAL recurring
    seat_fee_usd = db.Column(db.Float, default=0.0)       # ORG per active staff
    per_batch_fee_usd = db.Column(db.Float, default=0.0)  # ORG PAYG per batch
    currency = db.Column(db.String(8), default="USD")

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "plan_type": self.plan_type,
                "flat_fee_usd": self.flat_fee_usd, "seat_fee_usd": self.seat_fee_usd,
                "per_batch_fee_usd": self.per_batch_fee_usd, "currency": self.currency}


class Subscription(TimestampMixin, db.Model):
    __tablename__ = "subscription"

    account_id = db.Column(db.String(32), db.ForeignKey("account.id"), nullable=False)
    plan_id = db.Column(db.String(32), db.ForeignKey("plan.id"), nullable=False)
    status = db.Column(db.String(20), default="ACTIVE")  # ACTIVE | PAST_DUE | CANCELLED
    period_start = db.Column(db.DateTime, default=utcnow)
    period_end = db.Column(db.DateTime)
    next_invoice_at = db.Column(db.DateTime)

    plan = db.relationship("Plan")

    def to_dict(self) -> dict:
        return {"id": self.id, "account_id": self.account_id, "plan_id": self.plan_id,
                "status": self.status,
                "plan": self.plan.to_dict() if self.plan else None}


class Wallet(TimestampMixin, db.Model):
    __tablename__ = "wallet"

    account_id = db.Column(db.String(32), db.ForeignKey("account.id"),
                           unique=True, nullable=False)
    balance_usd = db.Column(db.Float, nullable=False, default=0.0)

    def to_dict(self) -> dict:
        return {"id": self.id, "account_id": self.account_id,
                "balance_usd": round(self.balance_usd, 2)}


class BillingEntry(TimestampMixin, db.Model):
    """Append-only ledger of every wallet movement."""
    __tablename__ = "billing_entry"

    account_id = db.Column(db.String(32), db.ForeignKey("account.id"), nullable=False)
    kind = db.Column(db.String(20), nullable=False)  # enums.BillingKind
    amount_usd = db.Column(db.Float, nullable=False)  # signed: debit < 0, credit > 0
    ref_id = db.Column(db.String(32))  # batch id, user id, payment id...
    balance_after = db.Column(db.Float)
    note = db.Column(db.String(160))

    def to_dict(self) -> dict:
        return {"id": self.id, "account_id": self.account_id, "kind": self.kind,
                "amount_usd": round(self.amount_usd, 2), "ref_id": self.ref_id,
                "balance_after": round(self.balance_after, 2)
                if self.balance_after is not None else None,
                "note": self.note,
                "created_at": self.created_at.isoformat() if self.created_at else None}


class Payment(TimestampMixin, db.Model):
    """A Payonify checkout/top-up. Created PENDING, confirmed PAID by webhook."""
    __tablename__ = "payment"

    account_id = db.Column(db.String(32), db.ForeignKey("account.id"), nullable=False)
    payonify_reference = db.Column(db.String(80), index=True)  # our idempotency key
    checkout_session_id = db.Column(db.String(120))
    amount_usd = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default=PaymentStatus.PENDING)
    method = db.Column(db.String(20))  # ECOCASH | ONEMONEY | ZIMSWITCH | CARD
    raw = db.Column(db.JSON, default=dict)
    paid_at = db.Column(db.DateTime)

    def to_dict(self) -> dict:
        return {"id": self.id, "account_id": self.account_id,
                "payonify_reference": self.payonify_reference,
                "amount_usd": round(self.amount_usd, 2), "status": self.status,
                "method": self.method,
                "created_at": self.created_at.isoformat() if self.created_at else None}
