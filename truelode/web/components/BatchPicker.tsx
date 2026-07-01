"use client";
import dynamic from "next/dynamic";
import { useState } from "react";

import { get } from "@/lib/api";

const QrScanner = dynamic(() => import("./QrScanner"), { ssr: false });

// Identify a batch at handover: type/click an id, OR scan its QR code.
export default function BatchPicker({
  batchId,
  setBatchId,
}: {
  batchId: string;
  setBatchId: (v: string) => void;
}) {
  const [scanning, setScanning] = useState(false);
  const [msg, setMsg] = useState("");

  async function onResult(text: string) {
    setScanning(false);
    if (text.startsWith("__error__")) {
      setMsg("Camera error — type the batch id instead.");
      return;
    }
    const token = text.trim().split(/[?#]/)[0].split("/").filter(Boolean).pop() || "";
    try {
      const batch = await get(`/api/batches/resolve/${encodeURIComponent(token)}`);
      setBatchId(batch.id);
      setMsg(`Scanned: ${batch.code} (${batch.stage})`);
    } catch {
      setMsg("No batch matches that QR.");
    }
  }

  return (
    <div>
      <label>Batch id (click a batch row, type, or scan QR)</label>
      <div className="row">
        <input value={batchId} onChange={(e) => setBatchId(e.target.value)}
          style={{ flex: 1, minWidth: 240 }} />
        <button className="ghost" onClick={() => { setMsg(""); setScanning(true); }}>
          📷 Scan QR
        </button>
      </div>
      {scanning && (
        <div style={{ marginTop: 10 }}>
          <QrScanner onResult={onResult} onClose={() => setScanning(false)} />
        </div>
      )}
      {msg && <p className="muted" style={{ color: "var(--green)" }}>{msg}</p>}
    </div>
  );
}
