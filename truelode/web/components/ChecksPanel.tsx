"use client";

type Recon = { ok: boolean };
type Trip = { deviations_total: number; deviations_cleared: number };

function Row({ label, ok }: { readonly label: string; readonly ok: boolean | null }) {
  const cls = ok === null ? "muted" : ok ? "badge green" : "badge red";
  const mark = ok === null ? "— not checked" : ok ? "✓ pass" : "✗ fail";
  return (
    <div style={{ display: "flex", justifyContent: "space-between", padding: "4px 0" }}>
      <span className="muted">{label}</span>
      <span className={cls} role="status" aria-label={`${label}: ${mark}`}>{mark}</span>
    </div>
  );
}

export default function ChecksPanel({
  signatureValid, ledgerIntact, reconciliations, transport,
}: {
  readonly signatureValid: boolean;
  readonly ledgerIntact: boolean;
  readonly reconciliations?: Recon[];
  readonly transport?: Trip[];
}) {
  const massOk = reconciliations?.length ? reconciliations.every((r) => r.ok) : null;
  const routeOk = transport?.length
    ? transport.every((t) => t.deviations_total - t.deviations_cleared === 0)
    : null;
  return (
    <div className="card">
      <h3>What we checked</h3>
      <Row label="Cryptographic signature" ok={signatureValid} />
      <Row label="Ledger hash-chain" ok={ledgerIntact} />
      <Row label="Mass balance (weight in vs out)" ok={massOk} />
      <Row label="Route / geofence" ok={routeOk} />
      <div className="muted" style={{ marginTop: 8 }}>
        Verified {new Date().toLocaleString()}
      </div>
    </div>
  );
}
