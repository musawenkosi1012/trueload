"use client";

type Anomaly = {
  type: string; severity?: string; status: string;
  detail?: Record<string, unknown>; created_at?: string | null;
};

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
                <td><b>{r.type}</b></td>
                <td>{r.severity ?? "—"}</td>
                <td>
                  <span className={`badge ${r.status === "CLEARED" ? "green" : "amber"}`}>
                    {r.status}
                  </span>
                </td>
                <td className="muted">
                  {r.detail ? JSON.stringify(r.detail) : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
