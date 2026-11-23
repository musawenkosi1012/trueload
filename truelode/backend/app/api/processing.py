"""Processing steps: consume parent batches, yield a child, reconcile metal."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt

from app.extensions import db
from app.models.batch import Batch, BatchLink
from app.models.enums import BatchStage, BatchState
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
    parent_ids = d.get("parent_ids")
    if not isinstance(parent_ids, list) or not parent_ids or len(parent_ids) != len(set(parent_ids)):
        return jsonify({"error": "parent_ids must be a nonempty list of unique identifiers"}), 400
    parents = [find_batch(pid) for pid in parent_ids]
    if any(p is None for p in parents):
        return jsonify({"error": "all parent batches must exist"}), 404
    if len({p.id for p in parents}) != len(parents):
        return jsonify({"error": "duplicate parent batch"}), 400
    if any(p.state == BatchState.CONSUMED for p in parents):
        return jsonify({"error": "a parent batch was already consumed"}), 409
    if any(p.current_custodian_org_id != claims.get("account_id") for p in parents) and claims.get("role") != "ADMIN":
        return jsonify({"error": "processor must have custody of all inputs"}), 403

    out_stage = d.get("out_stage")
    stage_order = (BatchStage.RAW_ORE, BatchStage.CONCENTRATE, BatchStage.LI_SULPHATE, BatchStage.PRODUCT)
    if out_stage not in stage_order[1:]:
        return jsonify({"error": "invalid output material stage"}), 400
    if any(stage_order.index(p.stage) >= stage_order.index(out_stage) for p in parents):
        return jsonify({"error": "processing must advance the material stage"}), 400
    if d.get("tol_pct", 5.0) < 0:
        return jsonify({"error": "invalid tolerance"}), 400
    try:
        out_kg = float(d["out_kg"])
        out_grade = float(d["out_grade"])
        declared_loss = float(d.get("declared_loss_kg", 0))
        result = massbalance.reconcile_processing(
            [{"net_kg": p.net_weight_kg, "grade_pct": p.grade_pct} for p in parents],
            {"net_kg": out_kg, "grade_pct": out_grade},
            declared_loss, d.get("tol_pct", 5.0),
            YIELD_BANDS.get(out_stage, (1.0, 12.0)))
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        return jsonify({"error": str(exc)}), 400
    if not result["ok"]:
        # No child or lineage is created and no parents are consumed.
        # A rejected event is retained in the audit ledger for regulator review.
        ledger.append("PROCESSING_REJECTED", {
            "parents": [p.code for p in parents], "out_stage": out_stage,
            "out_kg": out_kg, "out_grade": out_grade, "result": result,
        }, actor_id=claims.get("sub"))
        db.session.commit()
        return jsonify({"error": "processing failed mass-balance or yield checks",
                        "result": result}), 422

    child = Batch(code=d.get("code") or (parents[0].code + "-" + out_stage[:3]),
                  stage=out_stage, state=BatchState.OPEN, net_weight_kg=out_kg,
                  grade_pct=out_grade,
                  origin_site_id=parents[0].origin_site_id,
                  current_custodian_org_id=claims.get("account_id"),
                  unit_count=d.get("unit_count"), unit_label=d.get("unit_label"))
    db.session.add(child)
    db.session.flush()

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
    db.session.commit()
    emit_event("processing.completed",
               {"child": child.to_dict(), "result": result},
               roles=["REGULATOR", "PROCESSOR", "BUYER"])
    return jsonify({"child": child.to_dict(), "step": step.to_dict(),
                    "result": result}), 201
