"use client";
import { QRCodeSVG } from "qrcode.react";
import { useState } from "react";

type Batch = { code: string; qr_token: string };

export default function MintedBatch({ batch }: { readonly batch: Batch }) {
  const [copied, setCopied] = useState(false);

  function copy() {
    navigator.clipboard?.writeText(batch.qr_token).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }

  return (
    <div className="card" style={{ display: "flex", gap: 16, alignItems: "center" }}>
      <div style={{ background: "#fff", padding: 10, borderRadius: 8 }}>
        <QRCodeSVG value={batch.qr_token} size={110} />
      </div>
      <div style={{ flex: 1 }}>
        <div className="stat">{batch.code}</div>
        <div className="muted">
          Driver carries this QR. The processor scans it at handover — no typing.
        </div>
        <button className="ghost" style={{ marginTop: 8 }} onClick={copy}>
          {copied ? "Copied ✓" : "Copy token"}
        </button>
      </div>
    </div>
  );
}
