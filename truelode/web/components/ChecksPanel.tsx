"use client";

import { fmtDateTime } from "@/lib/fmt";

type Recon = { ok: boolean };
type Trip = { deviations_total: number; deviations_cleared: number; pings: number };

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
  // A leg with no GPS pings was not monitored — never report a vacuous pass.
  const monitored = transport?.some((t) => t.pings > 0);
  const routeOk = monitored
    ? transport!.every((t) => t.pings === 0 ||
        t.deviations_total - t.deviations_cleared === 0)
    : null;
  return (
    <div className="card">
      <h3>What we checked</h3>
      <Row label="Cryptographic signature" ok={signatureValid} />
      <Row label="Ledger hash-chain" ok={ledgerIntact} />
      <Row label="Mass balance (weight in vs out)" ok={massOk} />
      <Row label="Route / geofence" ok={routeOk} />
      <div className="muted" style={{ marginTop: 8 }}>
        Verified {fmtDateTime(new Date().toISOString())}
      </div>
    </div>
  );
}
