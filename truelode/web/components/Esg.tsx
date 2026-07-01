"use client";

type Composition = { Li2O_pct: number; balance_pct: number; form: string; hazardous_substances: string };
type Esg = {
  carbon_kg_co2e: number; carbon_kg_per_tonne: number;
  processing_kg: number; transport_kg: number; estimate?: boolean;
  recycled_pct?: number; composition?: Composition; permit_ref?: string | null;
};

const t = (kg: number) => (kg / 1000).toFixed(1);

export default function Esg({ esg }: { readonly esg?: Esg }) {
  if (!esg) return null;
  const c = esg.composition;
  return (
    <div className="card">
      <h3>ESG & composition {esg.estimate && <span className="badge amber">estimate</span>}</h3>
      <div className="muted">
        Carbon: <b style={{ color: "var(--text)" }}>≈ {t(esg.carbon_kg_co2e)} t CO₂e</b>{" "}
        ({esg.carbon_kg_per_tonne} kg/t · processing {t(esg.processing_kg)} t · transport {t(esg.transport_kg)} t)
      </div>
      {c && (
        <div className="muted">
          Composition: {c.Li2O_pct}% Li₂O · {c.balance_pct}% balance · form {c.form} · hazardous: {c.hazardous_substances}
        </div>
      )}
      <div className="muted">
        Recycled content: {esg.recycled_pct ?? 0}% · Permit: {esg.permit_ref ?? "—"}
      </div>
    </div>
  );
}
