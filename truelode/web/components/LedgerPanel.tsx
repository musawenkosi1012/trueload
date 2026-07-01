"use client";
import { useEffect, useState } from "react";

import { get } from "@/lib/api";
import { getSocket } from "@/lib/socket";

export default function LedgerPanel() {
  const [rows, setRows] = useState<any[]>([]);
  const load = () => get("/api/dashboard/ledger").then(setRows).catch(() => {});

  useEffect(() => {
    load();
    const s = getSocket();
    const refresh = () => load();
    ["batch.created", "flag.raised", "weigh.recorded", "processing.completed"]
      .forEach((e) => s.on(e, refresh));
    return () => ["batch.created", "flag.raised", "weigh.recorded", "processing.completed"]
      .forEach((e) => s.off(e, refresh));
  }, []);

  return (
    <div className="card">
      <h3>Tamper-evident ledger</h3>
      <table>
        <thead><tr><th>#</th><th>Event</th><th>Hash</th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.seq}>
              <td>{r.seq}</td>
              <td>{r.event_type}</td>
              <td className="muted">{r.entry_hash.slice(0, 12)}…</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
