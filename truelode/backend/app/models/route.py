"""Route: an approved transport corridor (polyline + buffer + tolerances)."""
from app.extensions import db

from .base import TimestampMixin


class Route(TimestampMixin, db.Model):
    __tablename__ = "route"

    name = db.Column(db.String(160), nullable=False)
    origin_site_id = db.Column(db.String(32), db.ForeignKey("site.id"), nullable=False)
    dest_site_id = db.Column(db.String(32), db.ForeignKey("site.id"), nullable=False)
    # path: ordered [[lat, lng], ...] approximating the approved road.
    path = db.Column(db.JSON, nullable=False, default=list)
    buffer_m = db.Column(db.Float, default=500)
    weight_tolerance_pct = db.Column(db.Float, default=2.0)
    grade_tolerance_pct = db.Column(db.Float, default=5.0)

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name,
                "origin_site_id": self.origin_site_id,
                "dest_site_id": self.dest_site_id, "path": self.path,
                "buffer_m": self.buffer_m,
                "weight_tolerance_pct": self.weight_tolerance_pct,
                "grade_tolerance_pct": self.grade_tolerance_pct}
