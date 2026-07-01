"use client";
import { useEffect, useState } from "react";

import { get } from "@/lib/api";
import { getSocket } from "@/lib/socket";

export default function FlagBreakdown() {
  const [flags, setFlags] = useState<any[]>([]);
  const load = () => get("/api/flags").then(setFlags).catch(() => {});

  useEffect(() => {
    load();
    const s = getSocket();
    s.on("flag.raised", load);
    s.on("flag.cleared", load);
    return () => { s.off("flag.raised", load); s.off("flag.cleared", load); };
  }, []);

  const byType: Record<string, { open: number; total: number }> = {};
  flags.forEach((f) => {
    byType[f.type] ??= { open: 0, total: 0 };
    byType[f.type].total++;
    if (f.status === "OPEN") byType[f.type].open++;
  });
  const keys = Object.keys(byType);

  return (
    <div className="card">
      <h3>Flags by type</h3>
      {keys.length === 0 && <div className="muted">No flags raised.</div>}
      {keys.map((k) => (
        <div key={k} className="muted">
          {k}: <b style={{ color: byType[k].open ? "var(--red)" : "var(--text)" }}>{byType[k].open} open</b> / {byType[k].total} total
        </div>
      ))}
    </div>
  );
}
