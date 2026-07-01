"""Billing API: plans, account billing state, usage ledger, wallet top-ups."""
import uuid

from flask import Blueprint, current_app, jsonify, request

from app.extensions import db
from app.models.account import Account
from app.models.billing import BillingEntry, Payment, Plan
from app.services import billing as billing_svc
from app.services.payments import get_provider

from .utils import current_account, current_user, err, role_required

bp = Blueprint("billing", __name__, url_prefix="/api/billing")


@bp.get("/plans")
def list_plans():
    return jsonify([p.to_dict() for p in Plan.query.all()])


@bp.get("/account")
@role_required()
def my_billing():
    acct = current_account()
    if not acct:
        return jsonify({"account": None})
    wallet = billing_svc.get_wallet(acct.id)
    recent = (BillingEntry.query.filter_by(account_id=acct.id)
              .order_by(BillingEntry.created_at.desc()).limit(10).all())
    return jsonify({
        "account": acct.to_dict(),
        "balance_usd": round(wallet.balance_usd, 2) if wallet else 0.0,
        "fees": {"per_batch_usd": billing_svc.per_batch_fee(acct),
                 "seat_usd": billing_svc.seat_fee(acct),
                 "flat_usd": billing_svc.flat_fee(acct)},
        "recent": [e.to_dict() for e in recent],
    })


@bp.get("/usage")
@role_required()
def usage():
    acct = current_account()
    if not acct:
        return jsonify([])
    limit = min(int(request.args.get("limit", 50)), 200)
    entries = (BillingEntry.query.filter_by(account_id=acct.id)
               .order_by(BillingEntry.created_at.desc()).limit(limit).all())
    return jsonify([e.to_dict() for e in entries])


@bp.post("/topup")
@role_required()
def topup():
    acct = current_account()
    if not acct:
        return err("no account", 400)
    d = request.get_json() or {}
    try:
        amount = float(d.get("amount_usd", 0))
    except (TypeError, ValueError):
        return err("invalid amount", 400)
    if amount <= 0:
        return err("amount must be positive", 400)

    reference = "tl_" + uuid.uuid4().hex[:18]
    payment = Payment(account_id=acct.id, payonify_reference=reference,
                      amount_usd=amount)
    db.session.add(payment)
    db.session.flush()

    user = current_user()
    web = current_app.config["WEB_BASE_URL"].rstrip("/")
    session = get_provider().create_checkout(
        amount_usd=amount, reference=reference,
        return_url=f"{web}/billing?ref={reference}",
        customer_email=user.email if user else None,
        description=f"Truelode top-up for {acct.name}")
    payment.checkout_session_id = session["session_id"]
    db.session.commit()

    return jsonify({"checkout_url": session["checkout_url"],
                    "reference": reference, "amount_usd": amount}), 201


@bp.post("/run-cycle")
@role_required("ADMIN")
def run_cycle():
    """Manually trigger recurring (seat/flat) billing for all accounts (demo)."""
    results = []
    for acct in Account.query.all():
        results.append(billing_svc.run_billing_cycle(acct))
    db.session.commit()
    return jsonify({"cycles": results})
