"use client";
import { useEffect, useState } from "react";

import { getSocket } from "@/lib/socket";

const EVENTS = [
  "batch.created", "flag.raised", "flag.cleared", "weigh.recorded",
  "gps.ingested", "assay.recorded", "processing.completed",
];

export default function LiveFeed() {
  const [items, setItems] = useState<{ e: string; t: string }[]>([]);

  useEffect(() => {
    const s = getSocket();
    const handlers = EVENTS.map((e) => {
      const h = () => setItems((prev) =>
        [{ e, t: new Date().toLocaleTimeString() }, ...prev].slice(0, 12));
      s.on(e, h);
      return [e, h] as const;
    });
    return () => handlers.forEach(([e, h]) => s.off(e, h));
  }, []);

  return (
    <div className="card">
      <h3>Live feed</h3>
      {items.length === 0 && <div className="muted">Waiting for events…</div>}
      {items.map((i, idx) => (
        <div key={idx} className="muted">
          <span style={{ color: "var(--accent)" }}>{i.e}</span> · {i.t}
        </div>
      ))}
    </div>
  );
}
