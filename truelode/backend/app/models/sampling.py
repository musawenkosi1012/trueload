"""Sample and AssayResult: grab samples and the lab grades that test loads."""
from app.extensions import db

from .base import TimestampMixin, utcnow


class Sample(TimestampMixin, db.Model):
    __tablename__ = "sample"

    batch_id = db.Column(db.String(32), db.ForeignKey("batch.id"), nullable=False)
    site_id = db.Column(db.String(32), db.ForeignKey("site.id"))
    label = db.Column(db.String(40))  # usually the batch code
    stage_tag = db.Column(db.String(20), default="LOADING")  # LOADING | ARRIVAL

    def to_dict(self) -> dict:
        return {"id": self.id, "batch_id": self.batch_id, "site_id": self.site_id,
                "label": self.label, "stage_tag": self.stage_tag}


class AssayResult(TimestampMixin, db.Model):
    __tablename__ = "assay_result"

    sample_id = db.Column(db.String(32), db.ForeignKey("sample.id"), nullable=False)
    lab_org_id = db.Column(db.String(32), db.ForeignKey("account.id"))
    analyte = db.Column(db.String(20), default="Li2O")
    value = db.Column(db.Float, nullable=False)  # percent
    method = db.Column(db.String(60))
    status = db.Column(db.String(20), default="FINAL")
    ts = db.Column(db.DateTime, default=utcnow)

    def to_dict(self) -> dict:
        return {"id": self.id, "sample_id": self.sample_id,
                "lab_org_id": self.lab_org_id, "analyte": self.analyte,
                "value": self.value, "method": self.method, "status": self.status}
