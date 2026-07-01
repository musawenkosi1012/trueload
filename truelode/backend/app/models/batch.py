"""Batch: the central custody object (a DAG node), plus its lineage links."""
from app.extensions import db

from .base import TimestampMixin, new_id
from .enums import BatchStage, BatchState


class Batch(TimestampMixin, db.Model):
    __tablename__ = "batch"

    code = db.Column(db.String(40), unique=True, nullable=False, index=True)
    stage = db.Column(db.String(20), nullable=False, default=BatchStage.RAW_ORE)
    state = db.Column(db.String(20), nullable=False, default=BatchState.OPEN)
    net_weight_kg = db.Column(db.Float, nullable=False, default=0)
    grade_pct = db.Column(db.Float)  # e.g. Li2O %
    origin_site_id = db.Column(db.String(32), db.ForeignKey("site.id"))
    current_custodian_org_id = db.Column(db.String(32), db.ForeignKey("account.id"))
    qr_token = db.Column(db.String(64), unique=True, default=new_id)
    unit_count = db.Column(db.Integer)   # set on final PRODUCT batch
    unit_label = db.Column(db.String(40))  # e.g. "drums"
    permit_ref = db.Column(db.String(60))  # MMCZ / movement-permit number
    recycled_pct = db.Column(db.Float, default=0.0)  # virgin-mined = 0

    def to_dict(self) -> dict:
        return {"id": self.id, "code": self.code, "stage": self.stage,
                "state": self.state, "net_weight_kg": self.net_weight_kg,
                "grade_pct": self.grade_pct, "origin_site_id": self.origin_site_id,
                "custodian": self.current_custodian_org_id, "qr_token": self.qr_token,
                "unit_count": self.unit_count, "unit_label": self.unit_label,
                "permit_ref": self.permit_ref, "recycled_pct": self.recycled_pct}


class BatchLink(TimestampMixin, db.Model):
    """parent -> child edge: how much of a parent fed into a child batch."""
    __tablename__ = "batch_link"

    parent_batch_id = db.Column(db.String(32), db.ForeignKey("batch.id"), nullable=False)
    child_batch_id = db.Column(db.String(32), db.ForeignKey("batch.id"), nullable=False)
    contribution_kg = db.Column(db.Float, default=0)
    ratio = db.Column(db.Float)
