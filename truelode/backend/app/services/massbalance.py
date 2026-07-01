"""MassBalanceEngine: the moat. Reconcile weight + grade in vs out."""


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


def contained_metal(net_kg: float, grade_pct: float | None) -> float:
    return net_kg * ((grade_pct or 0) / 100.0)


def reconcile_processing(parents: list[dict], child: dict, declared_loss_kg: float,
                         tol_pct: float, yield_band: tuple[float, float]) -> dict:
    """Conserve contained metal across a form change; sanity-check yield ratio.

    parents/child: dicts with net_kg and grade_pct. yield_band is (min, max)
    for parents_in_kg / child_out_kg.
    """
    metal_in = sum(contained_metal(p["net_kg"], p.get("grade_pct")) for p in parents)
    loss_metal = contained_metal(declared_loss_kg, child.get("grade_pct"))
    metal_out = contained_metal(child["net_kg"], child.get("grade_pct")) + loss_metal
    conservation_ok = within_pct(metal_in, metal_out, tol_pct)

    parents_kg = sum(p["net_kg"] for p in parents)
    ratio = parents_kg / child["net_kg"] if child["net_kg"] else 0
    lo, hi = yield_band
    yield_ok = lo <= ratio <= hi

    return {"ok": conservation_ok and yield_ok, "conservation_ok": conservation_ok,
            "yield_ok": yield_ok, "metal_in_kg": round(metal_in, 4),
            "metal_out_kg": round(metal_out, 4), "ratio": round(ratio, 3),
            "yield_band": [lo, hi], "tol_pct": tol_pct}
