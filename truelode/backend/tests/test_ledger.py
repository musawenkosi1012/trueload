"""Ledger hash-chain integrity + tamper detection."""
from app.extensions import db
from app.models.ledger import LedgerEntry
from app.services import ledger


def test_chain_appends_and_verifies(app):
    ledger.append("A", {"x": 1})
    ledger.append("B", {"x": 2})
    ledger.append("C", {"x": 3})
    db.session.commit()
    result = ledger.verify_chain()
    assert result["ok"] is True
    assert result["entries"] == 3


def test_tamper_breaks_chain(app):
    ledger.append("A", {"x": 1})
    e2 = ledger.append("B", {"x": 2})
    db.session.commit()
    # Simulate someone editing a stored payload after the fact.
    row = db.session.get(LedgerEntry, e2.seq)
    row.payload = {"x": 999}
    db.session.commit()
    result = ledger.verify_chain()
    assert result["ok"] is False
    assert result["broken_at"] == e2.seq
