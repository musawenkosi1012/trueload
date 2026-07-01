"use client";

type AssayRow = {
  batch_code: string; stage_tag?: string; analyte: string;
  value: number; lab?: string | null;
};

export default function Assays({ rows }: { readonly rows?: AssayRow[] }) {
  return (
    <div className="card">
      <h3>Lab assays — independent grade</h3>
      {!rows || rows.length === 0 ? (
        <div className="muted">No lab assays recorded.</div>
      ) : (
        <table>
          <thead>
            <tr><th>Batch</th><th>Stage</th><th>Analyte</th><th>Value</th><th>Lab</th></tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                <td><b>{r.batch_code}</b></td>
                <td>{r.stage_tag ?? "—"}</td>
                <td>{r.analyte}</td>
                <td>{r.value}%</td>
                <td>{r.lab ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
