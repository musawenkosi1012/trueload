"""Account: a tenant on the platform — either an INDIVIDUAL or an ENTERPRISE.

Replaces the old Organization model. account_type decides the billing shape and the
entitlement set: INDIVIDUAL = one user, flat fee, core features; ENTERPRISE = many staff,
per-seat + per-batch PAYG, full feature set. REGULATOR / ADMIN accounts carry exempt=True
(never billed, all features). See services/entitlements.py.
"""
from app.extensions import db

from .base import TimestampMixin
from .enums import AccountStatus, AccountType


class Account(TimestampMixin, db.Model):
    __tablename__ = "account"

    name = db.Column(db.String(160), nullable=False)
    account_type = db.Column(db.String(20), nullable=False,
                             default=AccountType.INDIVIDUAL)  # enums.AccountType
    primary_role = db.Column(db.String(20), nullable=False)  # enums.OrgType (function)
    country = db.Column(db.String(80), default="Zimbabwe")
    kyc_ref = db.Column(db.String(120))  # link to Sukanov KYC record
    status = db.Column(db.String(20), nullable=False,
                       default=AccountStatus.ACTIVE)  # enums.AccountStatus
    exempt = db.Column(db.Boolean, nullable=False, default=False)  # REGULATOR/ADMIN

    users = db.relationship("User", back_populates="account", lazy="dynamic")
    sites = db.relationship("Site", back_populates="account", lazy="dynamic")

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "account_type": self.account_type,
                "primary_role": self.primary_role, "country": self.country,
                "status": self.status, "exempt": self.exempt}
