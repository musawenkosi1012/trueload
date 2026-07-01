"""WeighEvent and GpsPing: scale readings and location pings."""
from app.extensions import db

from .base import TimestampMixin, utcnow


class WeighEvent(TimestampMixin, db.Model):
    __tablename__ = "weigh_event"

    batch_id = db.Column(db.String(32), db.ForeignKey("batch.id"), nullable=False)
    site_id = db.Column(db.String(32), db.ForeignKey("site.id"))
    kind = db.Column(db.String(20), nullable=False)  # enums.WeighKind
    gross_kg = db.Column(db.Float)
    tare_kg = db.Column(db.Float)
    net_kg = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(20), default="MANUAL")  # MANUAL | SCALE_API
    operator_id = db.Column(db.String(32), db.ForeignKey("user.id"))
    ts = db.Column(db.DateTime, default=utcnow)

    def to_dict(self) -> dict:
        return {"id": self.id, "batch_id": self.batch_id, "site_id": self.site_id,
                "kind": self.kind, "net_kg": self.net_kg, "source": self.source,
                "ts": self.ts.isoformat() if self.ts else None}


class GpsPing(TimestampMixin, db.Model):
    __tablename__ = "gps_ping"

    trip_id = db.Column(db.String(32), db.ForeignKey("trip.id"), nullable=False, index=True)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    speed = db.Column(db.Float)
    ts = db.Column(db.DateTime, default=utcnow)

    def to_dict(self) -> dict:
        return {"id": self.id, "trip_id": self.trip_id, "lat": self.lat,
                "lng": self.lng, "speed": self.speed,
                "ts": self.ts.isoformat() if self.ts else None}
