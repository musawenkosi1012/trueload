"""PhotoAsset: a stored photo/document with its content hash."""
from app.extensions import db

from .base import TimestampMixin


class PhotoAsset(TimestampMixin, db.Model):
    __tablename__ = "photo_asset"

    storage_key = db.Column(db.String(240), nullable=False)  # local path or S3 key
    sha256 = db.Column(db.String(64), nullable=False)
    mime = db.Column(db.String(60), default="image/jpeg")

    def to_dict(self) -> dict:
        return {"id": self.id, "storage_key": self.storage_key,
                "sha256": self.sha256, "mime": self.mime}
