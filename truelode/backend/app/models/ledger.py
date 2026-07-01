"""LedgerEntry: the append-only hash-chained audit record."""
from app.extensions import db

from .base import utcnow


class LedgerEntry(db.Model):
    """One row per state-changing event. Never UPDATE or DELETE these."""
    __tablename__ = "ledger_entry"

    seq = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_type = db.Column(db.String(40), nullable=False)
    actor_id = db.Column(db.String(32))
    payload = db.Column(db.JSON, nullable=False, default=dict)
    payload_hash = db.Column(db.String(64), nullable=False)
    prev_hash = db.Column(db.String(64), nullable=False)
    entry_hash = db.Column(db.String(64), nullable=False, index=True)
    ts = db.Column(db.DateTime, default=utcnow, nullable=False)
    tx_hash = db.Column(db.String(66), nullable=True)  # ponytail: filled by blockchain adapter when wired

    def to_dict(self) -> dict:
        return {"seq": self.seq, "event_type": self.event_type,
                "actor_id": self.actor_id, "payload": self.payload,
                "payload_hash": self.payload_hash, "prev_hash": self.prev_hash,
                "entry_hash": self.entry_hash,
                "ts": self.ts.isoformat() if self.ts else None,
                "tx_hash": self.tx_hash}
