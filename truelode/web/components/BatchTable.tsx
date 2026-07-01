"use client";
import { useEffect, useState } from "react";

import { get } from "@/lib/api";
import { getSocket } from "@/lib/socket";

type Batch = {
  id: string; code: string; stage: string; state: string;
  net_weight_kg: number; grade_pct?: number;
};

const stateColor: Record<string, string> = {
  RECEIVED: "green", IN_TRANSIT: "amber", CONSUMED: "amber",
  OPEN: "amber", CLOSED: "green",
};

export default function BatchTable({ onSelect }: { onSelect?: (b: Batch) => void }) {
  const [batches, setBatches] = useState<Batch[]>([]);
  const load = () => get<Batch[]>("/api/batches").then(setBatches).catch(() => {});

  useEffect(() => {
    load();
    const s = getSocket();
    s.on("batch.created", load);
    s.on("weigh.recorded", load);
    s.on("processing.completed", load);
    return () => {
      s.off("batch.created", load);
      s.off("weigh.recorded", load);
      s.off("processing.completed", load);
    };
  }, []);

  return (
    <div className="card">
      <h3>Batches</h3>
      <table>
        <thead><tr><th>Code</th><th>Stage</th><th>State</th><th>Weight</th><th>Grade</th></tr></thead>
        <tbody>
          {batches.map((b) => (
            <tr key={b.id} style={{ cursor: onSelect ? "pointer" : "default" }}
                onClick={() => onSelect?.(b)}>
              <td>{b.code}</td>
              <td>{b.stage}</td>
              <td><span className={`badge ${stateColor[b.state] || "amber"}`}>{b.state}</span></td>
              <td>{(b.net_weight_kg / 1000).toFixed(2)} t</td>
              <td>{b.grade_pct ? `${b.grade_pct}%` : "—"}</td>
            </tr>
          ))}
          {batches.length === 0 && <tr><td className="muted" colSpan={5}>No batches yet.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
