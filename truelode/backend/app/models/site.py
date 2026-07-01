"""Site: a physical location (mine, plant, weighbridge, lab) with coordinates."""
from app.extensions import db

from .base import TimestampMixin


class Site(TimestampMixin, db.Model):
    __tablename__ = "site"

    name = db.Column(db.String(160), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # enums.SiteType
    account_id = db.Column(db.String(32), db.ForeignKey("account.id"), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(240))

    account = db.relationship("Account", back_populates="sites")

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "type": self.type,
                "account_id": self.account_id, "lat": self.lat, "lng": self.lng,
                "address": self.address}
