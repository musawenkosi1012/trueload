"""Batches: list and walk lineage trees."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt

from app.extensions import db
from app.models.batch import Batch
from app.services import ledger
from app.services.passport import _lineage
from app.services.realtime import emit_event

from .utils import err, find_batch, role_required

bp = Blueprint("batches", __name__, url_prefix="/api/batches")


@bp.get("")
@role_required()
def list_batches():
    q = Batch.query.order_by(Batch.created_at.desc())
    if stage := request.args.get("stage"):
        q = q.filter_by(stage=stage)
    if state := request.args.get("state"):
        q = q.filter_by(state=state)
    return jsonify([b.to_dict() for b in q.all()])


@bp.get("/resolve/<qr_token>")
@role_required()
def resolve_qr(qr_token):
    """Resolve a scanned batch QR token to its batch (mineral handover)."""
    batch = Batch.query.filter_by(qr_token=qr_token).first()
    return (jsonify(batch.to_dict()) if batch
            else (jsonify({"error": "no batch for this QR"}), 404))


@bp.get("/<batch_id>")
@role_required()
def get_batch(batch_id):
    batch = find_batch(batch_id)
    return (jsonify(batch.to_dict()) if batch
            else (jsonify({"error": "not found"}), 404))


@bp.get("/<batch_id>/lineage")
@role_required()
def lineage(batch_id):
    return jsonify(_lineage(batch_id, set()))


@bp.post("/<batch_id>/claim")
@role_required("BUYER")
def claim(batch_id):
    """Buyer takes custody of a product batch — records the transfer on the chain.
    Requires the batch's passport QR token: digital claim follows physical
    possession of the scanned goods."""
    batch = find_batch(batch_id)
    if not batch:
        return err("batch not found", 404)
    d = request.get_json() or {}
    if (d.get("qr_token") or "").strip() != batch.qr_token:
        return err("scan the batch QR to claim custody — token does not match", 400)
    claims = get_jwt()
    batch.current_custodian_org_id = claims.get("account_id")
    ledger.append("BATCH_CLAIMED", {"batch_code": batch.code,
                                    "buyer_org_id": claims.get("account_id")},
                  actor_id=claims.get("sub"))
    db.session.commit()
    emit_event("batch.claimed", batch.to_dict(),
               roles=["REGULATOR", "BUYER", "PROCESSOR"])
    return jsonify(batch.to_dict())
