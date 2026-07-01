"""Passport: issue (authed) and public verify-by-QR-token (no auth)."""
import json

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt

from app.extensions import db
from app.models.batch import Batch
from app.models.passport import Passport
from app.services import ledger, signing
from app.services.passport import issue

from .utils import role_required

bp = Blueprint("passport", __name__, url_prefix="/api")


@bp.post("/passport/<batch_id>")
@role_required("PROCESSOR")
def issue_passport(batch_id):
    if not db.session.get(Batch, batch_id):
        return jsonify({"error": "batch not found"}), 404
    passport = issue(batch_id, issued_by=get_jwt().get("sub"))
    ledger.append("PASSPORT_ISSUED", {"batch_id": batch_id,
                                      "qr_token": passport.qr_token},
                  actor_id=get_jwt().get("sub"))
    db.session.commit()
    return jsonify({"qr_token": passport.qr_token,
                    "verify_url": f"/verify/{passport.qr_token}"}), 201


@bp.get("/verify/<token>")
def verify(token):
    """Public: render the story card + prove signature and chain integrity."""
    passport = Passport.query.filter_by(qr_token=token).first()
    if not passport:
        return jsonify({"error": "passport not found"}), 404
    message = json.dumps(passport.snapshot, sort_keys=True,
                         separators=(",", ":")).encode()
    sig_ok = signing.verify(message, passport.signature)
    chain = ledger.verify_chain()
    return jsonify({"passport": passport.to_dict(),
                    "signature_valid": sig_ok,
                    "ledger_intact": chain["ok"],
                    "public_key": signing.public_key_b64()})
