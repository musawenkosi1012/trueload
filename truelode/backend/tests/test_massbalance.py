"""Mass-balance math: the moat's core logic."""
from app.services import massbalance as mb


def test_transport_match_within_tolerance():
    r = mb.reconcile_transport(10000, 10100, tol_pct=2.0)
    assert r["ok"] is True


def test_transport_topup_flagged():
    # 10t left, 14t arrived -> someone added untracked rock.
    r = mb.reconcile_transport(10000, 14000, tol_pct=2.0)
    assert r["ok"] is False
    assert r["delta_kg"] == 4000


def test_grade_mismatch_flagged():
    r = mb.reconcile_transport(10000, 10000, tol_pct=2.0,
                               out_grade=1.5, in_grade=0.8, grade_tol_pct=5.0)
    assert r["grade_ok"] is False
    assert r["ok"] is False


def test_processing_conserves_contained_metal():
    parents = [{"net_kg": 8000, "grade_pct": 6.0}]   # 480 kg Li2O
    child = {"net_kg": 1000, "grade_pct": 47.0}       # 470 kg Li2O
    r = mb.reconcile_processing(parents, child, declared_loss_kg=20,
                                tol_pct=10.0, yield_band=(6.0, 9.0))
    assert r["conservation_ok"] is True
    assert r["yield_ok"] is True
    assert r["ok"] is True


def test_processing_yield_out_of_band_fails():
    parents = [{"net_kg": 2000, "grade_pct": 6.0}]
    child = {"net_kg": 1000, "grade_pct": 12.0}
    r = mb.reconcile_processing(parents, child, declared_loss_kg=0,
                                tol_pct=10.0, yield_band=(6.0, 9.0))
    assert r["yield_ok"] is False
    assert r["ok"] is False
