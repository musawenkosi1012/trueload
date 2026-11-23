"""MassBalanceEngine: reconcile transport and conserve contained Li2O during processing.

Grades use percent units: 1.4 means 1.4%, never a fraction. Conversion is
strictly conservative; a tolerance supplied by a client cannot authorize the
creation of additional contained lithium. Recovery < 100% is normal.
"""
from decimal import Decimal, InvalidOperation


def within_pct(a: float, b: float, tol_pct: float) -> bool:
    """True if b is within tol_pct of a (relative to a)."""
    if a == 0:
        return b == 0
    return abs(b - a) / abs(a) * 100.0 <= tol_pct


def reconcile_transport(out_kg: float, in_kg: float, tol_pct: float,
                        out_grade: float | None = None,
                        in_grade: float | None = None,
                        grade_tol_pct: float | None = None) -> dict:
    """Compare mine-out vs plant-in weight (and optionally grade)."""
    weight_ok = within_pct(out_kg, in_kg, tol_pct)
    delta = in_kg - out_kg
    result = {"weight_ok": weight_ok, "out_kg": out_kg, "in_kg": in_kg,
              "delta_kg": delta, "tol_pct": tol_pct, "grade_ok": None}
    if out_grade is not None and in_grade is not None and grade_tol_pct is not None:
        result["grade_ok"] = within_pct(out_grade, in_grade, grade_tol_pct)
        result["out_grade"] = out_grade
        result["in_grade"] = in_grade
    result["ok"] = weight_ok and (result["grade_ok"] in (None, True))
    return result


def _quantity(value: float | str | Decimal | None, name: str) -> Decimal:
    if value is None or isinstance(value, bool):
        raise ValueError(f"{name} is required")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not number.is_finite() or number < 0:
        raise ValueError(f"{name} must be a non-negative finite number")
    return number


def _grade(value: float | str | Decimal | None, name: str) -> Decimal:
    number = _quantity(value, name)
    if number > 100:
        raise ValueError(f"{name} must be between 0 and 100 percent")
    return number


def contained_metal(net_kg: float, grade_pct: float | None) -> float:
    """Kilograms of contained Li2O. Missing grade is not assumed to be zero."""
    return float(_quantity(net_kg, "net_kg") *
                 _grade(grade_pct, "grade_pct") / Decimal("100"))


def reconcile_processing(parents: list[dict], child: dict, declared_loss_kg: float,
                         tol_pct: float, yield_band: tuple[float, float]) -> dict:
    """Conserve Li2O across a transformation and sanity-check material yield.

    The only physical hard limit is contained_Li2O_out <= contained_Li2O_in.
    Recovery can be below 100%; a loss/grade at tailings must be measured, not
    implicitly inferred using the output concentrate's grade. tol_pct is kept
    in the response for legacy API compatibility; it never relaxes the hard
    conservation check.
    """
    if not parents:
        raise ValueError("at least one parent batch is required")
    parent_values = [(_quantity(p["net_kg"], "parent net_kg"),
                      _grade(p.get("grade_pct"), "parent grade_pct"))
                     for p in parents]
    if any(weight == 0 for weight, _ in parent_values):
        raise ValueError("parent weight must be positive")
    output_weight = _quantity(child["net_kg"], "output net_kg")
    output_grade = _grade(child.get("grade_pct"), "output grade_pct")
    if output_weight == 0:
        raise ValueError("output weight must be positive")
    declared_loss = _quantity(declared_loss_kg, "declared_loss_kg")
    _quantity(tol_pct, "tol_pct")
    if len(yield_band) != 2 or yield_band[0] <= 0 or yield_band[1] < yield_band[0]:
        raise ValueError("invalid yield band")

    input_weight = sum((w for w, _ in parent_values), Decimal("0"))
    if declared_loss > input_weight:
        raise ValueError("declared loss cannot exceed total input mass")
    metal_in = sum((w * g / Decimal("100") for w, g in parent_values),
                   Decimal("0"))
    metal_out = output_weight * output_grade / Decimal("100")
    conservation_ok = metal_out <= metal_in
    ratio = input_weight / output_weight
    lo, hi = (Decimal(str(x)) for x in yield_band)
    yield_ok = lo <= ratio <= hi
    recovered_pct = metal_out / metal_in * 100 if metal_in else Decimal("0")
    remaining_li2o_kg = metal_in - metal_out

    return {
        "ok": conservation_ok and yield_ok,
        "conservation_ok": conservation_ok, "yield_ok": yield_ok,
        "metal_in_kg": round(float(metal_in), 4),
        "metal_out_kg": round(float(metal_out), 4),
        "li2o_balance_kg": round(float(remaining_li2o_kg), 4),
        "recovery_pct": round(float(recovered_pct), 4),
        "ratio": round(float(ratio), 3),
        "yield_band": [float(lo), float(hi)],
        "tol_pct": tol_pct,
        "note": "Li2O loss is inferred from input minus output, not an assayed tailings measurement",
    }
