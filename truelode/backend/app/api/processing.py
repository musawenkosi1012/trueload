"""Processing steps: consume parent batches, yield a child, reconcile metal."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt

from app.extensions import db
from app.models.batch import Batch, BatchLink
from app.models.enums import BatchStage, BatchState, FlagType
from app.models.flag import Flag
from app.models.processing import ProcessingStep
from app.services import ledger, massbalance
from app.services.realtime import emit_event

from .utils import find_batch, role_required

bp = Blueprint("processing", __name__, url_prefix="/api/processing-steps")

# Expected parents-in : child-out band per output stage.
YIELD_BANDS = {BatchStage.CONCENTRATE: (3.0, 12.0),
               BatchStage.LI_SULPHATE: (6.0, 9.0),
               BatchStage.PRODUCT: (1.0, 9.0)}


@bp.post("")
@role_required("PROCESSOR")
def run_step():
    d = request.get_json() or {}
    claims = get_jwt()
    parents = [find_batch(pid) for pid in d["parent_ids"]]
    parents = [p for p in parents if p]
    if not parents:
        return jsonify({"error": "no valid parents"}), 400

    out_stage = d["out_stage"]
    child = Batch(code=d.get("code") or (parents[0].code + "-" + out_stage[:3]),
                  stage=out_stage, state=BatchState.OPEN, net_weight_kg=d["out_kg"],
                  grade_pct=d.get("out_grade"),
                  origin_site_id=parents[0].origin_site_id,
                  current_custodian_org_id=claims.get("account_id"),
                  unit_count=d.get("unit_count"), unit_label=d.get("unit_label"))
    db.session.add(child)
    db.session.flush()

    p_dicts = [{"net_kg": p.net_weight_kg, "grade_pct": p.grade_pct} for p in parents]
    result = massbalance.reconcile_processing(
        p_dicts, {"net_kg": d["out_kg"], "grade_pct": d.get("out_grade")},
        d.get("declared_loss_kg", 0), d.get("tol_pct", 5.0),
        YIELD_BANDS.get(out_stage, (1.0, 12.0)))

    for p in parents:
        db.session.add(BatchLink(parent_batch_id=p.id, child_batch_id=child.id,
                                 contribution_kg=p.net_weight_kg))
        p.state = BatchState.CONSUMED

    step = ProcessingStep(processor_org_id=claims.get("account_id"),
                          site_id=d.get("site_id"), child_batch_id=child.id,
                          parent_ids=[p.id for p in parents],
                          recipe_ratio=result["ratio"],
                          declared_loss_kg=d.get("declared_loss_kg", 0),
                          mass_balance_status="PASS" if result["ok"] else "FAIL",
                          detail=result)
    db.session.add(step)
    ledger.append("PROCESSING_STEP", {"child": child.code, "parents":
                  [p.code for p in parents], "result": result},
                  actor_id=claims.get("sub"))
    if not result["ok"]:
        db.session.add(Flag(type=FlagType.YIELD_ANOMALY, batch_id=child.id,
                            detail=result))
    db.session.commit()
    emit_event("processing.completed",
               {"child": child.to_dict(), "result": result},
               roles=["REGULATOR", "PROCESSOR", "BUYER"])
    return jsonify({"child": child.to_dict(), "step": step.to_dict(),
                    "result": result}), 201
