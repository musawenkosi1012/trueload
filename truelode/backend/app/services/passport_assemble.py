"""Helpers that gather passport sections from a batch lineage."""
from app.extensions import db
from app.models.batch import Batch, BatchLink
from app.models.enums import WeighKind
from app.models.account import Account
from app.models.sampling import AssayResult, Sample
from app.models.weigh import WeighEvent
from app.services import massbalance


def gather_batches(final_id: str) -> list[Batch]:
    """Return the final batch plus every ancestor (lineage closure)."""
    out, seen, stack = [], set(), [final_id]
    while stack:
        bid = stack.pop()
        if bid in seen:
            continue
        seen.add(bid)
        b = db.session.get(Batch, bid)
        if not b:
            continue
        out.append(b)
        stack.extend(l.parent_batch_id for l in
                     BatchLink.query.filter_by(child_batch_id=bid).all())
    return out


def org_name(org_id: str | None) -> str | None:
    acct = db.session.get(Account, org_id) if org_id else None
    return acct.name if acct else None


def weigh_stages(batches: list[Batch]) -> list[dict]:
    rows = []
    for b in batches:
        for w in WeighEvent.query.filter_by(batch_id=b.id).order_by(
                WeighEvent.ts.asc()).all():
            rows.append({"batch_code": b.code, "stage": b.stage, "kind": w.kind,
                         "net_kg": w.net_kg, "source": w.source,
                         "ts": w.ts.isoformat() if w.ts else None})
    return rows


def reconciliations(batches: list[Batch], tol_pct: float = 2.0) -> list[dict]:
    out = []
    for b in batches:
        mo = WeighEvent.query.filter_by(batch_id=b.id, kind=WeighKind.MINE_OUT).first()
        pi = WeighEvent.query.filter_by(batch_id=b.id, kind=WeighKind.PLANT_IN).first()
        if mo and pi:
            r = massbalance.reconcile_transport(mo.net_kg, pi.net_kg, tol_pct)
            out.append({"batch_code": b.code, **r})
    return out


def assays(batches: list[Batch]) -> list[dict]:
    out = []
    for b in batches:
        for s in Sample.query.filter_by(batch_id=b.id).all():
            for a in AssayResult.query.filter_by(sample_id=s.id).all():
                out.append({"batch_code": b.code, "stage_tag": s.stage_tag,
                            "analyte": a.analyte, "value": a.value,
                            "lab": org_name(a.lab_org_id)})
    return out
