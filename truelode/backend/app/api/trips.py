"""Trips + GPS ingest: store pings, run corridor checks, raise flags."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt

from app.extensions import db
from app.models.custody import Trip
from app.models.enums import FlagType
from app.models.flag import Flag
from app.models.route import Route
from app.models.site import Site
from app.models.weigh import GpsPing
from app.services import geofence, ledger
from app.services.realtime import emit_event

from .utils import role_required

bp = Blueprint("trips", __name__, url_prefix="/api")


@bp.get("/trips")
@role_required()
def list_trips():
    return jsonify([t.to_dict() for t in Trip.query.all()])


def _raise_flag(ftype: str, trip: Trip, detail: dict) -> Flag:
    flag = Flag(type=ftype, trip_id=trip.id, batch_id=trip.batch_id, detail=detail)
    db.session.add(flag)
    db.session.flush()
    ledger.append("FLAG_RAISED", {"flag_type": ftype, "trip_id": trip.id,
                                  "detail": detail})
    emit_event("flag.raised", flag.to_dict(),
               roles=["REGULATOR", "TRANSPORTER", "PROCESSOR"])
    return flag


@bp.post("/gps/bulk")
@role_required("TRANSPORTER", "MINE")
def ingest_gps():
    d = request.get_json() or {}
    trip = db.session.get(Trip, d["trip_id"])
    if not trip:
        return jsonify({"error": "trip not found"}), 404
    route = db.session.get(Route, trip.route_id) if trip.route_id else None
    sites = [(s.lat, s.lng) for s in Site.query.all()]
    flags = []
    for ping in d.get("pings", []):
        gp = GpsPing(trip_id=trip.id, lat=ping["lat"], lng=ping["lng"],
                     speed=ping.get("speed"))
        db.session.add(gp)
        if route and route.path:
            off, dist = geofence.is_off_route(route.path, ping["lat"], ping["lng"],
                                              route.buffer_m)
            if off:
                flags.append(_raise_flag(FlagType.OFF_ROUTE, trip,
                             {"distance_m": round(dist), "lat": ping["lat"],
                              "lng": ping["lng"]}))
        if (ping.get("speed", 1) or 0) < 1 and not geofence.near_known_site(
                sites, ping["lat"], ping["lng"]):
            flags.append(_raise_flag(FlagType.UNKNOWN_STOP, trip,
                         {"lat": ping["lat"], "lng": ping["lng"]}))
    db.session.commit()
    emit_event("gps.ingested", {"trip_id": trip.id, "count": len(d.get("pings", []))},
               roles=["REGULATOR", "TRANSPORTER"])
    return jsonify({"stored": len(d.get("pings", [])),
                    "flags": [f.to_dict() for f in flags]})
