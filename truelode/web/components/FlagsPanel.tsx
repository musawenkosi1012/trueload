"use client";
import { useEffect, useState } from "react";

import { get, post } from "@/lib/api";
import { getSocket } from "@/lib/socket";

type Flag = {
  id: string; type: string; status: string; batch_id?: string; detail?: any;
};

export default function FlagsPanel({ canClear }: { canClear?: boolean }) {
  const [flags, setFlags] = useState<Flag[]>([]);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState("");
  const [err, setErr] = useState("");

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
    setBusy(id); setErr("");
    try {
      await post(`/api/flags/${id}/clear`, { note: note.trim() });
      setNote("");
      load();
    } catch (e: any) { setErr(e.message); }
    finally { setBusy(""); }
  }

  return (
    <div className="card">
      <h3>Alerts {flags.filter((f) => f.status === "OPEN").length > 0 &&
        <span className="badge red">{flags.filter((f) => f.status === "OPEN").length} open</span>}</h3>
      {canClear && (
        <div className="row" style={{ marginBottom: 8 }}>
          <div style={{ flex: 1 }}>
            <label>Justification to clear (required, recorded on the ledger)</label>
            <input data-demo="clear-note" value={note} onChange={(e) => setNote(e.target.value)}
              placeholder="e.g. regulator re-weigh confirmed 30 t" />
          </div>
        </div>
      )}
      <table>
        <tbody>
          {flags.map((f) => {
            const firstOpen = f.status === "OPEN"
              && flags.find((x) => x.status === "OPEN")?.id === f.id;
            return (
            <tr key={f.id}>
              <td><span className={`badge ${f.status === "OPEN" ? "red" : "green"}`}>{f.type}</span></td>
              <td className="muted">{f.detail?.distance_m ? `${f.detail.distance_m} m off` :
                f.detail?.delta_kg ? `+${f.detail.delta_kg} kg` : f.status}</td>
              {canClear && (
                <td>{f.status === "OPEN" &&
                  <button data-demo={firstOpen ? "clear-flag" : undefined}
                    disabled={!note.trim() || busy === f.id}
                    onClick={() => clear(f.id)}>
                    {busy === f.id ? "…" : "Clear"}</button>}</td>
              )}
            </tr>
            );
          })}
          {flags.length === 0 && <tr><td className="muted">No alerts.</td></tr>}
        </tbody>
      </table>
      {err && <p style={{ color: "var(--red)" }}>{err}</p>}
    </div>
  );
}
