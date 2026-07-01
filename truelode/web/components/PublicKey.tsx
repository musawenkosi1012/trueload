"use client";
import { useEffect, useState } from "react";

function group(hex: string) {
  return hex.toUpperCase().match(/.{1,4}/g)?.join(" ") ?? hex;
}

export default function PublicKey({ pubB64 }: { readonly pubB64?: string }) {
  const [fp, setFp] = useState("");
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!pubB64 || !globalThis.crypto?.subtle) return;
    const bytes = Uint8Array.from(atob(pubB64), (c) => c.charCodeAt(0));
    globalThis.crypto.subtle.digest("SHA-256", bytes).then((buf) => {
      const hex = Array.from(new Uint8Array(buf))
        .map((b) => b.toString(16).padStart(2, "0")).join("");
      setFp(group(hex.slice(0, 16)));
    });
  }, [pubB64]);

  if (!pubB64) return null;
  return (
    <div className="card">
      <h3>Signing key</h3>
      <div className="muted">Fingerprint (SHA-256): <b style={{ color: "var(--text)" }}>{fp || "…"}</b></div>
      <button className="ghost" style={{ marginTop: 8 }} onClick={() => setOpen((v) => !v)}>
        {open ? "Hide" : "Show"} full key
      </button>
      {open && (
        <div className="muted" style={{ marginTop: 6, wordBreak: "break-all" }}>{pubB64}</div>
      )}
    </div>
  );
}
