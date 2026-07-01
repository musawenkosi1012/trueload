"""Load tickets: birth a batch at the mine weighbridge."""
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt

from app.extensions import db
from app.models.batch import Batch
from app.models.custody import LoadTicket, Trip
from app.models.base import new_id
from app.models.enums import BatchStage, BatchState, WeighKind
from app.models.sampling import Sample
from app.models.weigh import WeighEvent
from app.services import billing, ledger
from app.services.realtime import emit_event

from .utils import current_account, err, role_required

bp = Blueprint("loadtickets", __name__, url_prefix="/api/loadtickets")


def _batch_code() -> str:
    return ("TL-" + datetime.now(timezone.utc).strftime("%y%m%d-%H%M%S")
            + "-" + new_id()[:4])


@bp.post("")
@role_required("MINE")
def create_ticket():
    d = request.get_json() or {}
    claims = get_jwt()

    # Pay-as-you-go gate: a non-exempt account must have wallet funds for this batch.
    account = current_account()
    if not billing.account_can_transact(account):
        return err("payment required: top up your wallet to create a batch", 402)

    batch = Batch(code=_batch_code(), stage=BatchStage.RAW_ORE,
                  state=BatchState.IN_TRANSIT, net_weight_kg=d["net_weight_kg"],
                  grade_pct=d.get("grade_pct"), origin_site_id=d["mine_site_id"],
                  current_custodian_org_id=claims.get("account_id"),
                  permit_ref=d.get("permit_ref"))
    db.session.add(batch)
    db.session.flush()

    # Grab-sample at loading so a partner lab can assay the grade.
    db.session.add(Sample(batch_id=batch.id, site_id=d["mine_site_id"],
                          label=batch.code, stage_tag="LOADING"))

    ticket = LoadTicket(batch_id=batch.id, mine_site_id=d["mine_site_id"],
                        vehicle_id=d.get("vehicle_id"), driver_id=d.get("driver_id"),
                        net_weight_kg=d["net_weight_kg"], lat=d.get("lat"),
                        lng=d.get("lng"), photo_asset_id=d.get("photo_asset_id"))
    weigh = WeighEvent(batch_id=batch.id, site_id=d["mine_site_id"],
                       kind=WeighKind.MINE_OUT, net_kg=d["net_weight_kg"],
                       source=d.get("source", "MANUAL"), operator_id=claims.get("sub"))
    trip = Trip(batch_id=batch.id, route_id=d.get("route_id"),
                vehicle_id=d.get("vehicle_id"))
    db.session.add_all([ticket, weigh, trip])
    db.session.flush()

    ledger.append("LOAD_TICKET_CREATED",
                  {"batch_code": batch.code, "net_kg": d["net_weight_kg"],
                   "mine_site_id": d["mine_site_id"], "trip_id": trip.id,
                   "lat": d.get("lat"), "lng": d.get("lng")},
                  actor_id=claims.get("sub"))

    # Meter the batch against the account wallet (no-op for exempt accounts).
    if account:
        billing.charge_batch(account, batch.id)
    db.session.commit()
    emit_event("batch.created", {"batch": batch.to_dict(), "trip_id": trip.id},
               roles=["REGULATOR", "PROCESSOR", "TRANSPORTER"])
    return jsonify({"batch": batch.to_dict(), "ticket": ticket.to_dict(),
                    "trip": trip.to_dict()}), 201
