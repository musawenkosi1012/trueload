"""Dashboard: per-role summary feed, map geojson, ledger view."""
from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt

from app.models.batch import Batch
from app.models.custody import Trip
from app.models.enums import FlagStatus
from app.models.flag import Flag
from app.models.ledger import LedgerEntry
from app.models.weigh import GpsPing
from app.services import ledger

from .utils import role_required

bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@bp.get("/summary")
@role_required()
def summary():
    role = get_jwt().get("role")
    return jsonify({
        "role": role,
        "open_flags": Flag.query.filter_by(status=FlagStatus.OPEN).count(),
        "active_trips": Trip.query.filter_by(status="ACTIVE").count(),
        "batches": Batch.query.count(),
        "recent_flags": [f.to_dict() for f in
                         Flag.query.order_by(Flag.created_at.desc()).limit(10)],
    })


@bp.get("/map/<trip_id>")
@role_required()
def trip_map(trip_id):
    pings = GpsPing.query.filter_by(trip_id=trip_id).order_by(GpsPing.ts.asc()).all()
    return jsonify({"trip_id": trip_id, "track": [p.to_dict() for p in pings]})


@bp.get("/ledger")
@role_required("REGULATOR", "ADMIN")
def ledger_feed():
    rows = LedgerEntry.query.order_by(LedgerEntry.seq.desc()).limit(100).all()
    return jsonify([r.to_dict() for r in rows])


@bp.get("/ledger/verify")
@role_required("REGULATOR", "ADMIN")
def ledger_verify():
    """Recompute the whole hash chain and report the first break, if any."""
    return jsonify(ledger.verify_chain())
