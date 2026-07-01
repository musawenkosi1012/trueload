"""Vehicle and Driver: the tipper trucks and people who move batches."""
from app.extensions import db

from .base import TimestampMixin


class Vehicle(TimestampMixin, db.Model):
    __tablename__ = "vehicle"

    plate = db.Column(db.String(20), unique=True, nullable=False, index=True)
    tare_kg = db.Column(db.Float, default=0)
    transporter_id = db.Column(db.String(32), db.ForeignKey("account.id"))

    def to_dict(self) -> dict:
        return {"id": self.id, "plate": self.plate, "tare_kg": self.tare_kg,
                "transporter_id": self.transporter_id}


class Driver(TimestampMixin, db.Model):
    __tablename__ = "driver"

    name = db.Column(db.String(120), nullable=False)
    license_no = db.Column(db.String(60))
    phone = db.Column(db.String(40))
    transporter_id = db.Column(db.String(32), db.ForeignKey("account.id"))

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "license_no": self.license_no,
                "phone": self.phone, "transporter_id": self.transporter_id}
