"""Flags: list anomalies and clear them (with an audit trail)."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt

from app.extensions import db
from app.models.enums import FlagStatus
from app.models.flag import Flag
from app.services import ledger
from app.services.realtime import emit_event

from .utils import role_required

bp = Blueprint("flags", __name__, url_prefix="/api/flags")


@bp.get("")
@role_required()
def list_flags():
    q = Flag.query.order_by(Flag.created_at.desc())
    if status := request.args.get("status"):
        q = q.filter_by(status=status)
    return jsonify([f.to_dict() for f in q.all()])


@bp.post("/<flag_id>/clear")
@role_required("REGULATOR")
def clear_flag(flag_id):
    """Only the regulator may clear a flag — the flagged party cannot clear
    its own anomaly. A written justification is mandatory and lands on the
    ledger beside the original flag."""
    flag = db.session.get(Flag, flag_id)
    if not flag:
        return jsonify({"error": "not found"}), 404
    note = ((request.get_json() or {}).get("note") or "").strip()
    if not note:
        return jsonify({"error": "a written justification is required to "
                                 "clear a flag"}), 400
    flag.status = FlagStatus.CLEARED
    ledger.append("FLAG_CLEARED", {"flag_id": flag.id, "note": note},
                  actor_id=get_jwt().get("sub"))
    db.session.commit()
    emit_event("flag.cleared", flag.to_dict(), roles=["REGULATOR"])
    return jsonify(flag.to_dict())
