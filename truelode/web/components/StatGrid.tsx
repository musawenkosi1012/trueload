"use client";
import { useEffect, useState } from "react";

import { get } from "@/lib/api";
import { getSocket } from "@/lib/socket";

export default function StatGrid() {
  const [s, setS] = useState<any>({});
  const load = () => get("/api/dashboard/summary").then(setS).catch(() => {});

  useEffect(() => {
    load();
    const sock = getSocket();
    ["batch.created", "flag.raised", "flag.cleared", "processing.completed"]
      .forEach((e) => sock.on(e, load));
    return () => ["batch.created", "flag.raised", "flag.cleared", "processing.completed"]
      .forEach((e) => sock.off(e, load));
  }, []);

  return (
    <div className="grid">
      <div className="card"><div className="stat">{s.batches ?? 0}</div><div className="muted">Batches tracked</div></div>
      <div className="card"><div className="stat">{s.active_trips ?? 0}</div><div className="muted">Active trips</div></div>
      <div className="card"><div className="stat" style={{ color: s.open_flags ? "var(--red)" : "var(--green)" }}>{s.open_flags ?? 0}</div><div className="muted">Open alerts</div></div>
    </div>
  );
}
