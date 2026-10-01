"use client";

type TripRow = {
  batch_code: string; route: string; distance_km: number;
  pings: number; deviations_total: number; deviations_cleared: number;
};

export default function Transport({ rows }: { readonly rows?: TripRow[] }) {
  return (
    <div className="card">
      <h3>Transport integrity</h3>
      {!rows || rows.length === 0 ? (
        <div className="muted">No transport legs recorded.</div>
      ) : (
        <table>
          <thead>
            <tr><th>Batch</th><th>Route</th><th>Distance</th><th>GPS pings</th><th>Deviations</th></tr>
          </thead>
          <tbody>
            {rows.map((r, i) => {
              const open = r.deviations_total - r.deviations_cleared;
              const unmonitored = r.pings === 0;
              return (
                <tr key={i}>
                  <td><b>{r.batch_code}</b></td>
                  <td>{r.route}</td>
                  <td>{Math.round(r.distance_km)} km</td>
                  <td>{r.pings}</td>
                  <td>
                    {unmonitored ? (
                      <span className="badge amber">no telemetry — unverified</span>
                    ) : (
                      <span className={`badge ${open > 0 ? "amber" : "green"}`}>
                        {r.deviations_cleared}/{r.deviations_total} cleared
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
