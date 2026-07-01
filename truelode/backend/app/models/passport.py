"""Passport: the signed, scannable provenance record for a final batch."""
from app.extensions import db

from .base import TimestampMixin


class Passport(TimestampMixin, db.Model):
    __tablename__ = "passport"

    final_batch_id = db.Column(db.String(32), db.ForeignKey("batch.id"), nullable=False)
    qr_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    snapshot = db.Column(db.JSON, nullable=False, default=dict)
    signature = db.Column(db.Text, nullable=False)
    issued_by = db.Column(db.String(32), db.ForeignKey("user.id"))

    def to_dict(self) -> dict:
        return {"id": self.id, "final_batch_id": self.final_batch_id,
                "qr_token": self.qr_token, "snapshot": self.snapshot,
                "issued_by": self.issued_by,
                "issued_at": self.created_at.isoformat() if self.created_at else None}
