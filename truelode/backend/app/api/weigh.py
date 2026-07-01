"""Weigh events: record arrivals and reconcile against mine-out (mass balance)."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt

from app.extensions import db
from app.models.batch import Batch
from app.models.custody import CustodyHandover, Trip
from app.models.enums import BatchState, FlagType, HandoverStatus, WeighKind
from app.models.flag import Flag
from app.models.route import Route
from app.models.weigh import WeighEvent
from app.services import ledger, massbalance
from app.services.realtime import emit_event

from .utils import role_required

bp = Blueprint("weigh", __name__, url_prefix="/api/weighevents")


@bp.post("")
@role_required("PROCESSOR", "MINE")
def record_weigh():
    d = request.get_json() or {}
    claims = get_jwt()
    batch = db.session.get(Batch, d["batch_id"])
    if not batch:
        return jsonify({"error": "batch not found"}), 404

    weigh = WeighEvent(batch_id=batch.id, site_id=d.get("site_id"), kind=d["kind"],
                       gross_kg=d.get("gross_kg"), tare_kg=d.get("tare_kg"),
                       net_kg=d["net_kg"], source=d.get("source", "MANUAL"),
                       operator_id=claims.get("sub"))
    db.session.add(weigh)
    ledger.append("WEIGH_RECORDED", {"batch_id": batch.id, "kind": d["kind"],
                                     "net_kg": d["net_kg"]}, actor_id=claims.get("sub"))

    result = None
    if d["kind"] == WeighKind.PLANT_IN:
        accepted = CustodyHandover.query.filter_by(
            batch_id=batch.id, status=HandoverStatus.ACCEPTED).first()
        if not accepted:
            return jsonify({"error": "weigh-in requires accepted custody handover — "
                                     "scan the batch QR to accept custody first"}), 409
        result = _reconcile_arrival(batch, d["net_kg"])
    db.session.commit()
    emit_event("weigh.recorded",
               {"batch": batch.to_dict(), "weigh": weigh.to_dict(),
                "reconcile": result}, roles=["REGULATOR", "PROCESSOR", "MINE"])
    return jsonify({"weigh": weigh.to_dict(), "reconcile": result}), 201


def _reconcile_arrival(batch: Batch, in_kg: float) -> dict:
    mine_out = WeighEvent.query.filter_by(
        batch_id=batch.id, kind=WeighKind.MINE_OUT).first()
    trip = Trip.query.filter_by(batch_id=batch.id).first()
    route = db.session.get(Route, trip.route_id) if trip and trip.route_id else None
    tol = route.weight_tolerance_pct if route else 2.0
    out_kg = mine_out.net_kg if mine_out else in_kg
    result = massbalance.reconcile_transport(out_kg, in_kg, tol)

    if result["ok"]:
        batch.state = BatchState.RECEIVED
    else:
        flag = Flag(type=FlagType.WEIGHT_MISMATCH, batch_id=batch.id, detail=result)
        db.session.add(flag)
        ledger.append("FLAG_RAISED", {"flag_type": FlagType.WEIGHT_MISMATCH,
                                      "batch_id": batch.id, "detail": result})
    return result
