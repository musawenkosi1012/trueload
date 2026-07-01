"""Invite: a reusable join code an ENTERPRISE owner shares so people join the org.

The code is reusable until revoked (active=False). The role is fixed by the owner at
creation, so everyone joining with a given code lands with that function.
"""
import secrets

from app.extensions import db

from .base import TimestampMixin

# Unambiguous alphabet (no 0/O/1/I) for codes people read off a screen.
_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def new_code() -> str:
    return "TL-" + "".join(secrets.choice(_ALPHABET) for _ in range(6))


class Invite(TimestampMixin, db.Model):
    __tablename__ = "invite"

    account_id = db.Column(db.String(32), db.ForeignKey("account.id"), nullable=False)
    code = db.Column(db.String(16), unique=True, nullable=False, index=True,
                     default=new_code)
    role = db.Column(db.String(20), nullable=False)  # function the joiner inherits
    active = db.Column(db.Boolean, nullable=False, default=True)
    uses = db.Column(db.Integer, nullable=False, default=0)  # how many joined with it

    account = db.relationship("Account")

    def to_dict(self) -> dict:
        return {"id": self.id, "code": self.code, "role": self.role,
                "active": self.active, "uses": self.uses,
                "created_at": self.created_at.isoformat() if self.created_at else None}
