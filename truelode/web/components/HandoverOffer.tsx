"use client";
import { useState } from "react";

import { post } from "@/lib/api";

export default function HandoverOffer({ batchId, orgs, toRoles, prompt, selectLabel, doneText }: {
  readonly batchId: string;
  readonly orgs: any[];
  readonly toRoles: string[];
  readonly prompt: string;
  readonly selectLabel: string;
  readonly doneText: string;
}) {
  // Sensible default: preselect the first recipient (companies before
  // individual accounts) — the user can always change it.
  const recipients = orgs
    .filter((o) => toRoles.includes(o.primary_role))
    .sort((a, b) => (a.account_type === "INDIVIDUAL" ? 1 : 0)
      - (b.account_type === "INDIVIDUAL" ? 1 : 0));
  const [toOrgId, setToOrgId] = useState(recipients[0]?.id ?? "");
  const [eta, setEta] = useState("");
  const [notes, setNotes] = useState("");
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function offer(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setErr("");
    try {
      await post(`/api/batches/${batchId}/transfer`, { to_org_id: toOrgId, eta: eta || undefined, notes: notes || undefined });
      setDone(true);
    } catch (ex: any) { setErr(ex.message); }
    finally { setBusy(false); }
  }

  if (done) return <p className="muted" style={{ marginTop: 8 }}>✓ {doneText}</p>;

  return (
    <form onSubmit={offer} style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
      <p className="muted" style={{ marginBottom: 4 }}>{prompt}</p>
      <div className="row">
        <div>
          <label>{selectLabel}</label>
          <select data-demo="handover-org" value={toOrgId} onChange={(e) => setToOrgId(e.target.value)} required>
            <option value="">— select —</option>
            {recipients.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
          </select>
        </div>
        <div>
          <label>ETA (optional)</label>
          <input type="datetime-local" value={eta} onChange={(e) => setEta(e.target.value)} />
        </div>
        <div>
          <label>Notes</label>
          <input type="text" value={notes} placeholder="optional" onChange={(e) => setNotes(e.target.value)} />
        </div>
        <button data-demo="offer-handover" disabled={!toOrgId || busy}>{busy ? "Offering…" : "Offer handover"}</button>
      </div>
      {err && <p style={{ color: "var(--red)" }}>{err}</p>}
    </form>
  );
}
