"use client";

type Anomaly = {
  type: string; severity?: string; status: string;
  detail?: Record<string, unknown>; created_at?: string | null;
};

const num = (v: unknown) => (typeof v === "number" ? v : null);
const kg = (v: number | null) => (v == null ? "?" : v.toLocaleString("en-GB"));

function describe(type: string, d?: Record<string, unknown>): string {
  if (!d) return "—";
  const outKg = num(d.out_kg), inKg = num(d.in_kg), deltaKg = num(d.delta_kg);
  switch (type) {
    case "WEIGHT_MISMATCH":
      return `weighed in ${kg(inKg)} kg against ${kg(outKg)} kg shipped`
        + (deltaKg ? ` — ${deltaKg > 0 ? "+" : ""}${kg(deltaKg)} kg unaccounted` : "")
        + (d.tol_pct != null ? ` · tolerance ${d.tol_pct}%` : "");
    case "OFF_ROUTE": {
      const dist = num(d.distance_m);
      return dist != null
        ? `${dist.toLocaleString("en-GB")} m outside the approved corridor`
        : "left the approved corridor";
    }
    case "UNKNOWN_STOP":
      return "stopped away from any known site";
    case "YIELD_ANOMALY": {
      const ratio = typeof d.ratio === "number" ? d.ratio : null;
      return "processing yield outside the expected band"
        + (ratio != null ? ` · ratio ${ratio}` : "");
    }
    default: {
      const raw = JSON.stringify(d);
      return raw.length > 90 ? raw.slice(0, 90) + "…" : raw;
    }
  }
}

export default function Anomalies({ rows }: { readonly rows?: Anomaly[] }) {
  return (
    <div className="card">
      <h3>Anomalies & checks</h3>
      {!rows || rows.length === 0 ? (
        <div className="muted">Clean run — no anomalies raised.</div>
      ) : (
        <table>
          <thead>
            <tr><th>Type</th><th>Severity</th><th>Status</th><th>Detail</th></tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                <td style={{ whiteSpace: "nowrap" }}><b>{r.type}</b></td>
                <td>{r.severity ?? "—"}</td>
                <td>
                  <span className={`badge ${r.status === "CLEARED" ? "green" : "amber"}`}>
                    {r.status}
                  </span>
                </td>
                <td className="muted">{describe(r.type, r.detail)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
