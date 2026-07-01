"""Payonify webhook: confirm payments and credit wallets."""
from flask import Blueprint, current_app, jsonify, request

from app.extensions import db
from app.models.account import Account
from app.models.base import utcnow
from app.models.billing import Payment
from app.models.enums import PaymentStatus
from app.services import billing as billing_svc
from app.services.payments import get_provider

bp = Blueprint("payments", __name__, url_prefix="/api/payments")


def _mark_paid(payment: Payment, method: str | None = None, raw: dict | None = None):
    if payment.status == PaymentStatus.PAID:
        return
    payment.status = PaymentStatus.PAID
    payment.method = method
    payment.raw = raw or {}
    payment.paid_at = utcnow()
    account = db.session.get(Account, payment.account_id)
    billing_svc.credit_wallet(account, payment.amount_usd, ref_id=payment.id,
                             note=f"Payonify {payment.payonify_reference}")


@bp.post("/webhook")
def webhook():
    raw = request.get_data()  # exact bytes for signature verification
    provider = get_provider()
    if not provider.verify_webhook(headers=dict(request.headers), raw_body=raw):
        return jsonify({"error": "invalid signature"}), 400

    event = provider.parse_event(raw)
    reference = event.get("reference")
    if not reference:
        return jsonify({"error": "missing reference"}), 400

    payment = Payment.query.filter_by(payonify_reference=reference).first()
    if not payment:
        return jsonify({"error": "unknown reference"}), 404
    if payment.status == PaymentStatus.PAID:
        return jsonify({"ok": True, "idempotent": True})  # already processed

    payment.method = event.get("method")
    payment.raw = event.get("raw", {})

    if event["status"] == "PAID":
        _mark_paid(payment, event.get("method"), event.get("raw"))
    elif event["status"] == "FAILED":
        payment.status = PaymentStatus.FAILED

    db.session.commit()
    return jsonify({"ok": True, "status": payment.status})


@bp.post("/mock-complete")
def mock_complete():
    """Demo-only: finish a top-up without a live Payonify callback.

    Enabled only when the provider runs on the placeholder key (no live creds).
    The hosted mock-checkout page calls this to credit the wallet.
    """
    if not get_provider()._is_demo:
        return jsonify({"error": "not available in live mode"}), 403
    d = request.get_json() or {}
    payment = Payment.query.filter_by(
        payonify_reference=d.get("reference")).first()
    if not payment:
        return jsonify({"error": "unknown reference"}), 404
    _mark_paid(payment, method="ECOCASH", raw={"demo": True})
    db.session.commit()
    return jsonify({"ok": True, "status": payment.status})
