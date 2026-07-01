"""LedgerService: append-only hash chain over all state-changing events."""
import hashlib
import json

from app.extensions import db
from app.models.ledger import LedgerEntry

GENESIS = "0" * 64


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_payload(payload: dict) -> str:
    return _sha(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def append(event_type: str, payload: dict, actor_id: str | None = None) -> LedgerEntry:
    """Append one entry; entry_hash binds prev_hash + payload + position + actor."""
    prev = LedgerEntry.query.order_by(LedgerEntry.seq.desc()).first()
    prev_hash = prev.entry_hash if prev else GENESIS
    next_seq = (prev.seq + 1) if prev else 1
    p_hash = hash_payload(payload)
    entry_hash = _sha(f"{prev_hash}{p_hash}{next_seq}{actor_id or ''}")

    entry = LedgerEntry(event_type=event_type, actor_id=actor_id, payload=payload,
                        payload_hash=p_hash, prev_hash=prev_hash, entry_hash=entry_hash)
    db.session.add(entry)
    db.session.flush()
    return entry


def verify_chain() -> dict:
    """Recompute the whole chain; report first break if any."""
    prev_hash = GENESIS
    count = 0
    for e in LedgerEntry.query.order_by(LedgerEntry.seq.asc()).all():
        count += 1
        if e.prev_hash != prev_hash:
            return {"ok": False, "broken_at": e.seq, "reason": "prev_hash mismatch"}
        if hash_payload(e.payload) != e.payload_hash:
            return {"ok": False, "broken_at": e.seq, "reason": "payload altered"}
        expect = _sha(f"{e.prev_hash}{e.payload_hash}{e.seq}{e.actor_id or ''}")
        if expect != e.entry_hash:
            return {"ok": False, "broken_at": e.seq, "reason": "entry_hash mismatch"}
        prev_hash = e.entry_hash
    return {"ok": True, "entries": count}
