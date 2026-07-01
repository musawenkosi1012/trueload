"use client";
import { useEffect, useState } from "react";

import { fetchPassport } from "@/lib/passport";

import Anomalies from "./Anomalies";
import Assays from "./Assays";
import ChecksPanel from "./ChecksPanel";
import Custody from "./Custody";
import Esg from "./Esg";
import Issuer from "./Issuer";
import Lineage from "./Lineage";
import PassportHeader from "./PassportHeader";
import PublicKey from "./PublicKey";
import Reconciliation from "./Reconciliation";
import Transport from "./Transport";

function ErrorCard({ err, onRetry }: { readonly err: string; readonly onRetry: () => void }) {
  const notFound = /not found/i.test(err);
  return (
    <div className="container">
      <div className="card" role="alert">
        <h3>{notFound ? "Passport not found" : "Couldn’t load passport"}</h3>
        <div className="muted">{notFound ? "Check the link or rescan the QR code." : err}</div>
        {!notFound && (
          <button className="ghost" style={{ marginTop: 10 }} onClick={onRetry}>Retry</button>
        )}
      </div>
    </div>
  );
}

export default function PassportView({
  token, initialData, initialError,
}: {
  readonly token: string;
  readonly initialData: any | null;
  readonly initialError: string | null;
}) {
  const [data, setData] = useState<any>(initialData);
  const [err, setErr] = useState<string | null>(initialError);
  const [share, setShare] = useState("");

  useEffect(() => { setShare(globalThis.location?.href ?? ""); }, []);
  useEffect(() => {
    if (!data && !err) fetchPassport(token).then((r) => r.error ? setErr(r.error) : setData(r.data));
  }, [token, data, err]);

  if (err) return <ErrorCard err={err} onRetry={() => setErr(null)} />;
  if (!data) return <div className="container muted" aria-busy="true">Loading passport…</div>;

  const snap = data.passport.snapshot;
  return (
    <div className="container" style={{ maxWidth: 760 }}>
      <h1 className="brand">⛏ TRUELODE — Battery Passport</h1>
      <PassportHeader data={data} shareUrl={share} />

      <div className="card">
        <h3>Provenance — mine to product</h3>
        <Lineage nodes={snap.lineage} />
      </div>

      <Custody custody={snap.custody} />
      <Transport rows={snap.transport} />

      <div className="card">
        <h3>Mass balance — weight in vs out</h3>
        <Reconciliation rows={snap.reconciliations} />
      </div>

      <Assays rows={snap.assays} />
      <Esg esg={snap.esg} />
      <Issuer issuer={snap.issuer} issuedAt={snap.issued_at} />
      <Anomalies rows={snap.anomalies} />
      <ChecksPanel signatureValid={data.signature_valid} ledgerIntact={data.ledger_intact}
        reconciliations={snap.reconciliations} transport={snap.transport} />
      <PublicKey pubB64={data.public_key} />
    </div>
  );
}
