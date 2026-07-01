"use client";

type ReconRow = {
  batch_code: string; out_kg: number; in_kg: number;
  delta_kg: number; ok: boolean;
};

const t = (kg: number) => (kg / 1000).toFixed(2);

export default function Reconciliation({ rows }: { rows?: ReconRow[] }) {
  if (!rows || rows.length === 0)
    return <div className="muted">No transport reconciliation recorded.</div>;

  return (
    <table>
      <thead>
        <tr><th>Batch</th><th>Mine-out</th><th>Plant-in</th><th>Δ</th><th>Result</th></tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>
            <td><b>{r.batch_code}</b></td>
            <td>{t(r.out_kg)} t</td>
            <td>{t(r.in_kg)} t</td>
            <td>{r.delta_kg > 0 ? "+" : ""}{t(r.delta_kg)} t</td>
            <td>
              <span className={`badge ${r.ok ? "green" : "red"}`}>
                {r.ok ? "PASS" : `FAIL (${r.delta_kg > 0 ? "+" : ""}${Math.round(r.delta_kg)} kg)`}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
