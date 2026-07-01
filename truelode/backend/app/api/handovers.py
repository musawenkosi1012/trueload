"""Custody handovers: explicit QR-scan acceptance at each mineral transfer point."""
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt

from app.extensions import db
from app.models.batch import Batch
from app.models.custody import CustodyHandover, Trip
from app.models.enums import HandoverStatus
from app.services import ledger
from app.services.realtime import emit_event

from .utils import current_account, err, role_required

bp = Blueprint("handovers", __name__, url_prefix="/api")


@bp.get("/handovers")
@role_required()
def list_handovers():
    """Pending incoming handovers for the caller's org."""
    claims = get_jwt()
    account_id = claims.get("account_id")
    q = CustodyHandover.query.filter_by(to_org_id=account_id)
    if request.args.get("pending"):
        q = q.filter_by(status=HandoverStatus.PENDING)
    return jsonify([h.to_dict() for h in q.order_by(CustodyHandover.created_at.desc()).all()])


@bp.post("/batches/<batch_id>/transfer")
@role_required("MINE", "TRANSPORTER", "PROCESSOR")
def offer_transfer(batch_id):
    """Current custodian offers custody to another org."""
    claims = get_jwt()
    account_id = claims.get("account_id")

    batch = db.session.get(Batch, batch_id)
    if not batch:
        return err("batch not found", 404)
    if batch.current_custodian_org_id != account_id:
        return err("you are not the current custodian", 403)

    existing = CustodyHandover.query.filter_by(
        batch_id=batch_id, status=HandoverStatus.PENDING).first()
    if existing:
        return err("a pending handover already exists for this batch", 409)

    d = request.get_json() or {}
    to_org_id = d.get("to_org_id")
    if not to_org_id:
        return err("to_org_id required", 400)

    eta = None
    if d.get("eta"):
        try:
            eta = datetime.fromisoformat(d["eta"].replace("Z", "+00:00"))
        except ValueError:
            return err("invalid eta format", 400)

    handover = CustodyHandover(
        batch_id=batch_id, from_org_id=account_id,
        to_org_id=to_org_id, eta=eta, notes=d.get("notes"),
    )
    db.session.add(handover)
    db.session.flush()

    ledger.append("CUSTODY_OFFERED", {
        "batch_id": batch_id, "batch_code": batch.code,
        "from_org_id": account_id, "to_org_id": to_org_id,
        "handover_id": handover.id,
    }, actor_id=claims.get("sub"))

    db.session.commit()
    emit_event("handover.offered", handover.to_dict(),
               roles=["TRANSPORTER", "PROCESSOR", "BUYER", "REGULATOR"])
    return jsonify(handover.to_dict()), 201


@bp.post("/handovers/<handover_id>/accept")
@role_required("TRANSPORTER", "PROCESSOR", "BUYER")
def accept_handover(handover_id):
    """Receiving party scans QR / enters code to accept custody."""
    claims = get_jwt()
    account_id = claims.get("account_id")

    handover = db.session.get(CustodyHandover, handover_id)
    if not handover:
        return err("handover not found", 404)
    if handover.status != HandoverStatus.PENDING:
        return err("handover is not pending", 409)
    if handover.to_org_id != account_id:
        return err("this handover is not addressed to your organisation", 403)

    d = request.get_json() or {}
    qr_token = d.get("qr_token", "").strip()

    batch = db.session.get(Batch, handover.batch_id)
    if not batch:
        return err("batch not found", 404)
    if qr_token != batch.qr_token:
        return err("QR token does not match — scan the batch QR to confirm custody", 400)

    eta = handover.eta
    if d.get("eta"):
        try:
            eta = datetime.fromisoformat(d["eta"].replace("Z", "+00:00"))
        except ValueError:
            return err("invalid eta format", 400)

    handover.status = HandoverStatus.ACCEPTED
    handover.accepted_by_user_id = claims.get("sub")
    handover.accepted_at = datetime.now(timezone.utc)
    handover.vehicle_id = d.get("vehicle_id") or handover.vehicle_id
    handover.driver_id = d.get("driver_id") or handover.driver_id
    handover.eta = eta
    if d.get("notes"):
        handover.notes = d["notes"]

    batch.current_custodian_org_id = account_id

    # Keep trip vehicle/driver in sync when transporter accepts
    trip = Trip.query.filter_by(batch_id=batch.id).order_by(Trip.created_at.desc()).first()
    if trip and handover.vehicle_id:
        trip.vehicle_id = handover.vehicle_id
    if trip and handover.driver_id:
        trip.driver_id = handover.driver_id

    db.session.flush()
    ledger.append("CUSTODY_ACCEPTED", {
        "batch_id": batch.id, "batch_code": batch.code,
        "from_org_id": handover.from_org_id, "to_org_id": account_id,
        "handover_id": handover.id,
        "vehicle_id": handover.vehicle_id, "driver_id": handover.driver_id,
    }, actor_id=claims.get("sub"))

    db.session.commit()
    emit_event("handover.accepted", handover.to_dict(),
               roles=["MINE", "TRANSPORTER", "PROCESSOR", "REGULATOR"])
    return jsonify({"handover": handover.to_dict(), "batch": batch.to_dict()})


@bp.post("/handovers/<handover_id>/reject")
@role_required("TRANSPORTER", "PROCESSOR", "BUYER")
def reject_handover(handover_id):
    """Receiving party rejects — batch stays with from_org."""
    claims = get_jwt()
    account_id = claims.get("account_id")

    handover = db.session.get(CustodyHandover, handover_id)
    if not handover:
        return err("handover not found", 404)
    if handover.status != HandoverStatus.PENDING:
        return err("handover is not pending", 409)
    if handover.to_org_id != account_id:
        return err("this handover is not addressed to your organisation", 403)

    d = request.get_json() or {}
    qr_token = d.get("qr_token", "").strip()
    batch = db.session.get(Batch, handover.batch_id)
    if batch and qr_token and qr_token != batch.qr_token:
        return err("QR token does not match", 400)

    handover.status = HandoverStatus.REJECTED
    handover.accepted_by_user_id = claims.get("sub")
    handover.accepted_at = datetime.now(timezone.utc)
    handover.notes = d.get("notes") or handover.notes

    db.session.flush()
    ledger.append("CUSTODY_REJECTED", {
        "batch_id": handover.batch_id,
        "from_org_id": handover.from_org_id, "to_org_id": account_id,
        "handover_id": handover.id, "notes": handover.notes,
    }, actor_id=claims.get("sub"))

    db.session.commit()
    emit_event("handover.rejected", handover.to_dict(),
               roles=["MINE", "TRANSPORTER", "PROCESSOR", "REGULATOR"])
    return jsonify(handover.to_dict())
