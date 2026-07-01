"""ProcessingStep: a plant operation that consumes parents and yields a child."""
from app.extensions import db

from .base import TimestampMixin, utcnow


class ProcessingStep(TimestampMixin, db.Model):
    __tablename__ = "processing_step"

    processor_org_id = db.Column(db.String(32), db.ForeignKey("account.id"))
    site_id = db.Column(db.String(32), db.ForeignKey("site.id"))
    child_batch_id = db.Column(db.String(32), db.ForeignKey("batch.id"), nullable=False)
    parent_ids = db.Column(db.JSON, default=list)  # input batch ids
    recipe_ratio = db.Column(db.Float)  # parents-in : child-out
    declared_loss_kg = db.Column(db.Float, default=0)
    mass_balance_status = db.Column(db.String(20), default="PENDING")  # PASS | FAIL
    detail = db.Column(db.JSON, default=dict)
    ts = db.Column(db.DateTime, default=utcnow)

    def to_dict(self) -> dict:
        return {"id": self.id, "child_batch_id": self.child_batch_id,
                "parent_ids": self.parent_ids, "recipe_ratio": self.recipe_ratio,
                "declared_loss_kg": self.declared_loss_kg,
                "mass_balance_status": self.mass_balance_status,
                "detail": self.detail}
