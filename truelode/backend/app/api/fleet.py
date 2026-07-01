"""Fleet + routes: vehicles, drivers, transport corridors."""
from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models.fleet import Driver, Vehicle
from app.models.route import Route

from .utils import role_required

bp = Blueprint("fleet", __name__, url_prefix="/api")


@bp.get("/vehicles")
@role_required()
def list_vehicles():
    return jsonify([v.to_dict() for v in Vehicle.query.all()])


@bp.post("/vehicles")
@role_required("ADMIN", "TRANSPORTER")
def create_vehicle():
    d = request.get_json() or {}
    v = Vehicle(plate=d["plate"], tare_kg=d.get("tare_kg", 0),
                transporter_id=d.get("transporter_id"))
    db.session.add(v)
    db.session.commit()
    return jsonify(v.to_dict()), 201


@bp.get("/drivers")
@role_required()
def list_drivers():
    return jsonify([d.to_dict() for d in Driver.query.all()])


@bp.post("/drivers")
@role_required("ADMIN", "TRANSPORTER")
def create_driver():
    d = request.get_json() or {}
    drv = Driver(name=d["name"], license_no=d.get("license_no"),
                 phone=d.get("phone"), transporter_id=d.get("transporter_id"))
    db.session.add(drv)
    db.session.commit()
    return jsonify(drv.to_dict()), 201


@bp.get("/routes")
@role_required()
def list_routes():
    return jsonify([r.to_dict() for r in Route.query.all()])


@bp.post("/routes")
@role_required("ADMIN", "REGULATOR")
def create_route():
    d = request.get_json() or {}
    r = Route(name=d["name"], origin_site_id=d["origin_site_id"],
              dest_site_id=d["dest_site_id"], path=d.get("path", []),
              buffer_m=d.get("buffer_m", 500),
              weight_tolerance_pct=d.get("weight_tolerance_pct", 2.0),
              grade_tolerance_pct=d.get("grade_tolerance_pct", 5.0))
    db.session.add(r)
    db.session.commit()
    return jsonify(r.to_dict()), 201
