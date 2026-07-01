"""User: a login belonging to one account, carrying its functional role."""
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

from .base import TimestampMixin


class User(TimestampMixin, db.Model):
    __tablename__ = "user"

    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # enums.OrgType (function/permission)
    account_id = db.Column(db.String(32), db.ForeignKey("account.id"), nullable=True)
    is_account_owner = db.Column(db.Boolean, nullable=False, default=False)  # ORG admin
    active = db.Column(db.Boolean, nullable=False, default=True)  # seat billable if True
    last_login_at = db.Column(db.DateTime, nullable=True)

    account = db.relationship("Account", back_populates="users")

    def set_password(self, raw: str) -> None:
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)

    def to_dict(self) -> dict:
        return {"id": self.id, "email": self.email, "name": self.name,
                "role": self.role, "account_id": self.account_id,
                "is_account_owner": self.is_account_owner, "active": self.active,
                "last_login_at": self.last_login_at.isoformat()
                if self.last_login_at else None}
