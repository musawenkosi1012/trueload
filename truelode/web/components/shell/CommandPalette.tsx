"use client";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import { get } from "@/lib/api";
import { navFor } from "@/lib/nav";

type Cmd = { type: string; label: string; go: () => void };

export default function CommandPalette({
  open, onClose, role,
}: {
  readonly open: boolean;
  readonly onClose: () => void;
  readonly role?: string;
}) {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [batches, setBatches] = useState<any[]>([]);
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) return;
    setQ(""); setActive(0);
    setTimeout(() => inputRef.current?.focus(), 0);
    get("/api/batches").then(setBatches).catch(() => {});
  }, [open]);

  const results = useMemo<Cmd[]>(() => {
    const ql = q.toLowerCase();
    const nav = navFor(role)
      .filter((n) => n.label.toLowerCase().includes(ql))
      .map((n) => ({ type: "View", label: n.label, go: () => {
        if (n.href) router.push(n.href);
        else if (globalThis.location) globalThis.location.hash = n.key;
      } }));
    const batchHits = (ql ? batches.filter((b) => b.code.toLowerCase().includes(ql)) : [])
      .slice(0, 6)
      .map((b) => ({ type: "Batch", label: b.code, go: () => router.push(`/verify/${b.qr_token}`) }));
    return [...nav, ...batchHits];
  }, [q, role, batches, router]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      else if (e.key === "ArrowDown") { e.preventDefault(); setActive((a) => Math.min(a + 1, results.length - 1)); }
      else if (e.key === "ArrowUp") { e.preventDefault(); setActive((a) => Math.max(a - 1, 0)); }
      else if (e.key === "Enter") { results[active]?.go(); onClose(); }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, results, active, onClose]);

  if (!open) return null;
  return (
    <div className="cmdk-overlay" onClick={onClose}>
      <div className="cmdk" onClick={(e) => e.stopPropagation()}>
        <input ref={inputRef} placeholder="Jump to a view, or search batches by code…"
          value={q} onChange={(e) => { setQ(e.target.value); setActive(0); }} />
        <div className="cmdk-list">
          {results.length === 0 && <div className="cmdk-group">No matches</div>}
          {results.map((r, i) => (
            <div key={`${r.type}-${i}`} className={`cmdk-item ${i === active ? "active" : ""}`}
              onMouseEnter={() => setActive(i)} onClick={() => { r.go(); onClose(); }}>
              <span className={r.type === "Batch" ? "mono" : ""}>{r.label}</span>
              <span className="meta">{r.type}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
