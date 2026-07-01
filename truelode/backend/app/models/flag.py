"""Flag: a raised anomaly (off-route, weight/grade mismatch, tamper...)."""
from app.extensions import db

from .base import TimestampMixin
from .enums import FlagStatus


class Flag(TimestampMixin, db.Model):
    __tablename__ = "flag"

    type = db.Column(db.String(24), nullable=False)  # enums.FlagType
    severity = db.Column(db.String(12), default="HIGH")
    status = db.Column(db.String(12), default=FlagStatus.OPEN)
    trip_id = db.Column(db.String(32), db.ForeignKey("trip.id"))
    batch_id = db.Column(db.String(32), db.ForeignKey("batch.id"))
    detail = db.Column(db.JSON, default=dict)

    def to_dict(self) -> dict:
        return {"id": self.id, "type": self.type, "severity": self.severity,
                "status": self.status, "trip_id": self.trip_id,
                "batch_id": self.batch_id, "detail": self.detail,
                "created_at": self.created_at.isoformat() if self.created_at else None}
