"use client";
import { useEffect, useRef, useState } from "react";

import { getSocket } from "@/lib/socket";

const LABELS: Record<string, string> = {
  "batch.created": "Batch created", "flag.raised": "Alert raised",
  "flag.cleared": "Alert cleared", "weigh.recorded": "Weigh recorded",
  "gps.ingested": "GPS logged", "assay.recorded": "Assay recorded",
  "processing.completed": "Batch processed", "batch.claimed": "Batch claimed",
};

export default function Notifications() {
  const [items, setItems] = useState<{ label: string; t: string }[]>([]);
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const s = getSocket();
    const hs = Object.entries(LABELS).map(([e, label]) => {
      const h = () => {
        setItems((p) => [{ label, t: new Date().toLocaleTimeString() }, ...p].slice(0, 30));
        setUnread((u) => u + 1);
      };
      s.on(e, h);
      return [e, h] as const;
    });
    return () => hs.forEach(([e, h]) => s.off(e, h));
  }, []);

  useEffect(() => {
    const close = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  function toggle() {
    setOpen((o) => !o);
    if (!open) setUnread(0);
  }

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button className="icon-btn" aria-label="Notifications" onClick={toggle}>
        🔔{unread > 0 && <span className="dot">{unread > 9 ? "9+" : unread}</span>}
      </button>
      {open && (
        <div className="menu" style={{ minWidth: 280 }}>
          <div className="head">Activity</div>
          {items.length === 0 && <div className="head">No recent events.</div>}
          {items.map((i, idx) => (
            <div key={idx} style={{ padding: "8px 10px", fontSize: 13 }}>
              <span style={{ color: "var(--accent)" }}>{i.label}</span>{" "}
              <span className="muted">· {i.t}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
