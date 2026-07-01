"use client";
import { useEffect, useState } from "react";

import { get } from "@/lib/api";
import { getSocket } from "@/lib/socket";

const EVENTS = ["batch.created", "flag.raised", "weigh.recorded", "processing.completed"];

export default function ChainIntegrity() {
  const [v, setV] = useState<any>(null);
  const load = () => get("/api/dashboard/ledger/verify").then(setV).catch(() => {});

  useEffect(() => {
    load();
    const s = getSocket();
    EVENTS.forEach((e) => s.on(e, load));
    return () => EVENTS.forEach((e) => s.off(e, load));
  }, []);

  if (!v) return null;
  return (
    <div className="card" style={{ borderColor: v.ok ? "var(--green)" : "var(--red)" }}>
      <span className={`badge ${v.ok ? "green" : "red"}`}>
        {v.ok ? "✓ CHAIN INTACT" : "✗ CHAIN BROKEN"}
      </span>{" "}
      <span className="muted">
        {v.ok ? `${v.entries} ledger entries verified` : `broken at seq ${v.broken_at}: ${v.reason}`}
      </span>
    </div>
  );
}
