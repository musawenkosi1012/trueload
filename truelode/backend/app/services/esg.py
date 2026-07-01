"""Rough ESG / carbon profile for a batch chain.

Estimates only — hard-rock spodumene → battery-grade lithium is energy-intensive
(~12 t CO2e per tonne of product is a common order-of-magnitude figure). These are
clearly-labelled approximations for the passport, not audited LCA numbers.
"""

PRODUCT_FACTOR_KG_PER_T = 12_000.0   # kg CO2e per tonne of processed product
TRUCK_FACTOR_KG_PER_T_KM = 0.12      # diesel haulage, per tonne-km


def carbon_profile(product_kg: float, ore_kg: float, distance_km: float) -> dict:
    product_t = product_kg / 1000.0
    ore_t = ore_kg / 1000.0
    processing = product_t * PRODUCT_FACTOR_KG_PER_T
    transport = ore_t * distance_km * TRUCK_FACTOR_KG_PER_T_KM
    total = round(processing + transport)
    per_t = round(total / product_t) if product_t else 0
    return {"carbon_kg_co2e": total, "carbon_kg_per_tonne": per_t,
            "processing_kg": round(processing), "transport_kg": round(transport),
            "estimate": True}


def composition(grade_pct: float | None, stage: str) -> dict:
    """Rough material composition from the headline grade."""
    g = grade_pct or 0
    return {"Li2O_pct": round(g, 2), "balance_pct": round(max(0.0, 100 - g), 2),
            "form": stage, "hazardous_substances": "none declared"}
