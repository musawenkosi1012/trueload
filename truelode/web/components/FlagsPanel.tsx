"use client";
import { useEffect, useState } from "react";

import { get, post } from "@/lib/api";
import { getSocket } from "@/lib/socket";

type Flag = {
  id: string; type: string; status: string; batch_id?: string; detail?: any;
};

export default function FlagsPanel({ canClear }: { canClear?: boolean }) {
  const [flags, setFlags] = useState<Flag[]>([]);

  const load = () => get<Flag[]>("/api/flags").then(setFlags).catch(() => {});

  useEffect(() => {
    load();
    const s = getSocket();
    const refresh = () => load();
    s.on("flag.raised", refresh);
    s.on("flag.cleared", refresh);
    return () => { s.off("flag.raised", refresh); s.off("flag.cleared", refresh); };
  }, []);

  async function clear(id: string) {
    await post(`/api/flags/${id}/clear`, { note: "reviewed" });
    load();
  }

  return (
    <div className="card">
      <h3>Alerts {flags.filter((f) => f.status === "OPEN").length > 0 &&
        <span className="badge red">{flags.filter((f) => f.status === "OPEN").length} open</span>}</h3>
      <table>
        <tbody>
          {flags.map((f) => (
            <tr key={f.id}>
              <td><span className={`badge ${f.status === "OPEN" ? "red" : "green"}`}>{f.type}</span></td>
              <td className="muted">{f.detail?.distance_m ? `${f.detail.distance_m} m off` :
                f.detail?.delta_kg ? `+${f.detail.delta_kg} kg` : f.status}</td>
              {canClear && (
                <td>{f.status === "OPEN" &&
                  <button onClick={() => clear(f.id)}>Clear</button>}</td>
              )}
            </tr>
          ))}
          {flags.length === 0 && <tr><td className="muted">No alerts.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
