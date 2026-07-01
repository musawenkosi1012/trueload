"use client";
import { QRCodeSVG } from "qrcode.react";

const BADGE = {
  ok: { cls: "green", text: "✓ VERIFIED — signature & chain intact" },
  caution: (n: number) => ({ cls: "amber", text: `⚠ VERIFIED — ${n} open flag(s)` }),
  fail: { cls: "red", text: "✗ VERIFICATION FAILED" },
};

export default function PassportHeader({
  data, shareUrl,
}: {
  readonly data: any;
  readonly shareUrl: string;
}) {
  const snap = data.passport.snapshot;
  const integrity = data.signature_valid && data.ledger_intact;
  const openFlags = (snap.anomalies ?? []).filter((f: any) => f.status === "OPEN").length;
  const badge = !integrity ? BADGE.fail : openFlags > 0 ? BADGE.caution(openFlags) : BADGE.ok;

  return (
    <div className="card" style={{ display: "flex", gap: 20, alignItems: "center" }}>
      <div style={{ background: "#fff", padding: 10, borderRadius: 8 }}>
        <QRCodeSVG value={shareUrl || data.passport.qr_token} size={120} />
      </div>
      <div style={{ flex: 1 }}>
        <div className="stat">{snap.final_batch?.code}</div>
        <div className="muted">
          {snap.unit_count ?? "—"} {snap.unit_label ?? "units"} · {snap.final_batch?.grade_pct}% Li₂O
        </div>
        {snap.per_unit_kg ? (
          <div className="muted">
            {snap.per_unit_kg} kg each{snap.custody?.mine ? ` · from ${snap.custody.mine}` : ""}
          </div>
        ) : null}
        <div style={{ marginTop: 8 }}>
          <span className={`badge ${badge.cls}`} role="status" aria-label={badge.text}>{badge.text}</span>
        </div>
      </div>
      <button className="ghost no-print" onClick={() => globalThis.print()}
        aria-label="Print or save passport as PDF">🖨 Print / PDF</button>
    </div>
  );
}
