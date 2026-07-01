"""PassportService: walk batch lineage to origin, snapshot, sign, mint QR."""
import json

from sqlalchemy import or_

from app.extensions import db
from app.models.base import utcnow
from app.models.batch import Batch, BatchLink
from app.models.custody import Trip
from app.models.flag import Flag
from app.models.passport import Passport
from app.models.processing import ProcessingStep
from app.models.site import Site
from app.models.user import User
from app.models.weigh import WeighEvent

from . import signing
from .passport_assemble import (
    assays,
    gather_batches,
    org_name,
    reconciliations,
    weigh_stages,
)
from .passport_context import custody, esg_profile, transport


def _lineage(batch_id: str, seen: set[str]) -> list[dict]:
    """Recursively collect this batch and all its ancestors as stage nodes."""
    if batch_id in seen:
        return []
    seen.add(batch_id)
    batch = db.session.get(Batch, batch_id)
    if not batch:
        return []
    site = db.session.get(Site, batch.origin_site_id) if batch.origin_site_id else None
    node = {"batch_id": batch.id, "code": batch.code, "stage": batch.stage,
            "net_weight_kg": batch.net_weight_kg, "grade_pct": batch.grade_pct,
            "origin": site.to_dict() if site else None,
            "weigh_events": [w.to_dict() for w in
                             WeighEvent.query.filter_by(batch_id=batch.id).all()],
            "parents": []}
    for link in BatchLink.query.filter_by(child_batch_id=batch.id).all():
        node["parents"].extend(_lineage(link.parent_batch_id, seen))
    return [node]


def _anomalies(batches: list[Batch]) -> list[dict]:
    bids = [b.id for b in batches]
    tids = [t.id for b in batches
            for t in Trip.query.filter_by(batch_id=b.id).all()]
    q = Flag.query.filter(or_(Flag.batch_id.in_(bids), Flag.trip_id.in_(tids)))
    return [f.to_dict() for f in q.order_by(Flag.created_at.asc()).all()]


def _issuer(issued_by: str | None) -> dict | None:
    user = db.session.get(User, issued_by) if issued_by else None
    return {"name": user.name, "org": org_name(user.account_id)} if user else None


def build_snapshot(final_batch_id: str, issued_by: str | None = None) -> dict:
    final = db.session.get(Batch, final_batch_id)
    batches = gather_batches(final_batch_id)
    steps = ProcessingStep.query.filter_by(child_batch_id=final_batch_id).all()
    anomalies = _anomalies(batches)
    trans = transport(batches)
    units = final.unit_count if final else None
    per_unit = round(final.net_weight_kg / units, 2) if final and units else None
    return {
        "final_batch": final.to_dict() if final else None,
        "unit_count": units, "unit_label": final.unit_label if final else None,
        "per_unit_kg": per_unit,
        "issued_at": utcnow().isoformat(), "issuer": _issuer(issued_by),
        "lineage": _lineage(final_batch_id, set()),
        "weigh_stages": weigh_stages(batches),
        "reconciliations": reconciliations(batches),
        "transport": trans,
        "assays": assays(batches),
        "custody": custody(batches, final),
        "esg": esg_profile(final, batches, trans),
        "processing": [s.to_dict() for s in steps],
        "anomalies": anomalies,
        "checks_passed": all(f["status"] == "CLEARED" for f in anomalies),
    }


def issue(final_batch_id: str, issued_by: str | None = None) -> Passport:
    final = db.session.get(Batch, final_batch_id)
    snapshot = build_snapshot(final_batch_id, issued_by=issued_by)
    message = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    passport = Passport(final_batch_id=final_batch_id, qr_token=final.qr_token,
                        snapshot=snapshot, signature=signing.sign(message),
                        issued_by=issued_by)
    db.session.add(passport)
    db.session.flush()
    return passport
