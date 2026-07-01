"""Samples + assays: grab samples and lab grade results."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt

from app.extensions import db
from app.models.sampling import AssayResult, Sample
from app.services import ledger
from app.services.realtime import emit_event

from .utils import role_required

bp = Blueprint("sampling", __name__, url_prefix="/api")


@bp.get("/samples")
@role_required()
def list_samples():
    return jsonify([s.to_dict() for s in Sample.query.order_by(
        Sample.created_at.desc()).all()])


@bp.post("/samples")
@role_required("MINE", "PROCESSOR")
def create_sample():
    d = request.get_json() or {}
    s = Sample(batch_id=d["batch_id"], site_id=d.get("site_id"),
               label=d.get("label"), stage_tag=d.get("stage_tag", "LOADING"))
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_dict()), 201


@bp.get("/assays")
@role_required()
def list_assays():
    q = Sample.query
    if batch_id := request.args.get("batch_id"):
        q = q.filter_by(batch_id=batch_id)
    ids = [s.id for s in q.all()]
    res = AssayResult.query.filter(AssayResult.sample_id.in_(ids)).all() if ids else []
    return jsonify([a.to_dict() for a in res])


@bp.post("/assays")
@role_required("LAB")
def create_assay():
    d = request.get_json() or {}
    a = AssayResult(sample_id=d["sample_id"], lab_org_id=get_jwt().get("account_id"),
                    analyte=d.get("analyte", "Li2O"), value=d["value"],
                    method=d.get("method"))
    db.session.add(a)
    ledger.append("ASSAY_RECORDED", {"sample_id": d["sample_id"],
                                     "analyte": a.analyte, "value": a.value},
                  actor_id=get_jwt().get("sub"))
    db.session.commit()
    emit_event("assay.recorded", a.to_dict(), roles=["PROCESSOR", "REGULATOR"])
    return jsonify(a.to_dict()), 201
