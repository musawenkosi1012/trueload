"""Regression tests for the lithium conservation gate in pit-to-port processing."""
import pytest

from app.services.massbalance import reconcile_processing


def run(input_kg=20000, input_grade=1.4, output_kg=3500, output_grade=6.0):
    return reconcile_processing(
        [{"net_kg": input_kg, "grade_pct": input_grade}],
        {"net_kg": output_kg, "grade_pct": output_grade},
        declared_loss_kg=0, tol_pct=5.0, yield_band=(3.0, 12.0),
    )


def test_valid_75_percent_recovery():
    result = run()
    assert result["ok"] is True
    assert result["metal_in_kg"] == 280.0
    assert result["metal_out_kg"] == 210.0
    assert result["li2o_balance_kg"] == 70.0
    assert result["recovery_pct"] == 75.0


def test_reject_ore_laundering_even_with_large_tolerance():
    result = reconcile_processing(
        [{"net_kg": 20000, "grade_pct": 1.4}],
        {"net_kg": 10000, "grade_pct": 6.0},
        declared_loss_kg=0, tol_pct=100.0, yield_band=(1.0, 12.0),
    )
    assert result["ok"] is False
    assert result["conservation_ok"] is False
    assert result["metal_out_kg"] == 600.0


@pytest.mark.parametrize("weight,grade", [
    (-1, 1.4), (0, 1.4), (20000, None),
    (20000, 101), (20000, float("nan")), (20000, float("inf")),
])
def test_invalid_inputs_are_rejected(weight, grade):
    with pytest.raises(ValueError):
        run(input_kg=weight, input_grade=grade)


def test_no_invented_metal_from_zero_grade_parent():
    result = run(input_grade=0, output_grade=6)
    assert result["ok"] is False


def test_declared_loss_cannot_exceed_input_mass():
    with pytest.raises(ValueError):
        reconcile_processing(
            [{"net_kg": 20000, "grade_pct": 1.4}],
            {"net_kg": 3500, "grade_pct": 6},
            declared_loss_kg=21000, tol_pct=5, yield_band=(3, 12),
        )
