"""Transport journey, custody chain, and ESG sections for the passport."""
from app.extensions import db
from app.models.batch import Batch
from app.models.custody import CustodyHandover, Trip
from app.models.enums import FlagStatus, FlagType, HandoverStatus
from app.models.fleet import Vehicle
from app.models.flag import Flag
from app.models.route import Route
from app.models.site import Site
from app.models.weigh import GpsPing
from app.services import esg, geofence

from .passport_assemble import org_name

ROUTE_FLAGS = (FlagType.OFF_ROUTE, FlagType.UNKNOWN_STOP)


def transport(batches: list[Batch]) -> list[dict]:
    out = []
    for b in batches:
        for trip in Trip.query.filter_by(batch_id=b.id).all():
            route = db.session.get(Route, trip.route_id) if trip.route_id else None
            flags = Flag.query.filter(Flag.trip_id == trip.id,
                                      Flag.type.in_(ROUTE_FLAGS)).all()
            out.append({
                "batch_code": b.code,
                "route": route.name if route else "—",
                "distance_km": geofence.route_length_km(route.path) if route else 0,
                "pings": GpsPing.query.filter_by(trip_id=trip.id).count(),
                "deviations_total": len(flags),
                "deviations_cleared": sum(1 for f in flags
                                          if f.status == FlagStatus.CLEARED)})
    return out


def custody(batches: list[Batch], final: Batch) -> dict:
    origin = batches[-1] if batches else final
    site = db.session.get(Site, origin.origin_site_id) if origin.origin_site_id else None

    # Read handover chain for explicit custody transfers
    accepted_handovers = []
    for b in batches:
        hs = (CustodyHandover.query
              .filter_by(batch_id=b.id, status=HandoverStatus.ACCEPTED)
              .order_by(CustodyHandover.created_at.asc()).all())
        accepted_handovers.extend(hs)

    transporter = None
    for h in accepted_handovers:
        from app.models.account import Account
        acct = db.session.get(Account, h.to_org_id)
        if acct and acct.primary_role == "TRANSPORTER":
            transporter = acct.name
            break

    # Fallback: infer transporter from vehicle owner (pre-handover batches)
    if not transporter:
        for b in batches:
            trip = Trip.query.filter_by(batch_id=b.id).first()
            veh = db.session.get(Vehicle, trip.vehicle_id) if trip and trip.vehicle_id else None
            if veh:
                transporter = org_name(veh.transporter_id)
                break

    handover_chain = [
        {"from_org": org_name(h.from_org_id), "to_org": org_name(h.to_org_id),
         "accepted_at": h.accepted_at.isoformat() if h.accepted_at else None,
         "vehicle_id": h.vehicle_id}
        for h in accepted_handovers
    ]

    return {"mine": org_name(site.account_id) if site else None,
            "transporter": transporter,
            "processor": org_name(final.current_custodian_org_id),
            "handover_chain": handover_chain}


def esg_profile(final: Batch, batches: list[Batch], transport_rows: list[dict]) -> dict:
    ore_kg = max((b.net_weight_kg for b in batches), default=final.net_weight_kg)
    distance = sum(t["distance_km"] for t in transport_rows)
    profile = esg.carbon_profile(final.net_weight_kg, ore_kg, distance)
    profile["recycled_pct"] = final.recycled_pct or 0.0
    profile["composition"] = esg.composition(final.grade_pct, final.stage)
    origin = batches[-1] if batches else final
    profile["permit_ref"] = origin.permit_ref or final.permit_ref
    return profile
