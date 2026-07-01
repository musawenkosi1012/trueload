"""LoadTicket, Trip, and CustodyHandover: birth and chain-of-custody transfers."""
from app.extensions import db

from .base import TimestampMixin, utcnow
from .enums import HandoverStatus


class LoadTicket(TimestampMixin, db.Model):
    """Created at the mine weighbridge; births a batch."""
    __tablename__ = "load_ticket"

    batch_id = db.Column(db.String(32), db.ForeignKey("batch.id"), nullable=False)
    mine_site_id = db.Column(db.String(32), db.ForeignKey("site.id"), nullable=False)
    vehicle_id = db.Column(db.String(32), db.ForeignKey("vehicle.id"))
    driver_id = db.Column(db.String(32), db.ForeignKey("driver.id"))
    net_weight_kg = db.Column(db.Float, nullable=False)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    photo_asset_id = db.Column(db.String(32), db.ForeignKey("photo_asset.id"))

    def to_dict(self) -> dict:
        return {"id": self.id, "batch_id": self.batch_id,
                "mine_site_id": self.mine_site_id, "vehicle_id": self.vehicle_id,
                "driver_id": self.driver_id, "net_weight_kg": self.net_weight_kg,
                "lat": self.lat, "lng": self.lng,
                "photo_asset_id": self.photo_asset_id}


class Trip(TimestampMixin, db.Model):
    __tablename__ = "trip"

    batch_id = db.Column(db.String(32), db.ForeignKey("batch.id"), nullable=False)
    route_id = db.Column(db.String(32), db.ForeignKey("route.id"))
    vehicle_id = db.Column(db.String(32), db.ForeignKey("vehicle.id"))
    status = db.Column(db.String(20), default="ACTIVE")  # ACTIVE | ARRIVED
    started_at = db.Column(db.DateTime, default=utcnow)
    ended_at = db.Column(db.DateTime)

    def to_dict(self) -> dict:
        return {"id": self.id, "batch_id": self.batch_id, "route_id": self.route_id,
                "vehicle_id": self.vehicle_id, "status": self.status}


class CustodyHandover(TimestampMixin, db.Model):
    """One row per custody transfer offer. Accepted row = future blockchain tx."""
    __tablename__ = "custody_handover"

    batch_id            = db.Column(db.String(32), db.ForeignKey("batch.id"),   nullable=False)
    from_org_id         = db.Column(db.String(32), db.ForeignKey("account.id"), nullable=False)
    to_org_id           = db.Column(db.String(32), db.ForeignKey("account.id"), nullable=False)
    status              = db.Column(db.String(20), default=HandoverStatus.PENDING, nullable=False)
    # set by acceptor / rejector
    accepted_by_user_id = db.Column(db.String(32), db.ForeignKey("user.id"),    nullable=True)
    accepted_at         = db.Column(db.DateTime,                                nullable=True)
    vehicle_id          = db.Column(db.String(32), db.ForeignKey("vehicle.id"), nullable=True)
    driver_id           = db.Column(db.String(32), db.ForeignKey("driver.id"),  nullable=True)
    eta                 = db.Column(db.DateTime,                                nullable=True)
    notes               = db.Column(db.String(500),                             nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "batch_id": self.batch_id,
            "from_org_id": self.from_org_id, "to_org_id": self.to_org_id,
            "status": self.status,
            "accepted_by_user_id": self.accepted_by_user_id,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "vehicle_id": self.vehicle_id, "driver_id": self.driver_id,
            "eta": self.eta.isoformat() if self.eta else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
