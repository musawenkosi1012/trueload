"""Common column mixins and helpers."""
import uuid
from datetime import datetime, timezone

from app.extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return uuid.uuid4().hex


class TimestampMixin:
    """Adds id (uuid hex) + created_at to a model."""

    id = db.Column(db.String(32), primary_key=True, default=new_id)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
