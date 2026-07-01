"use client";
import { useEffect, useState } from "react";

import { get, post } from "@/lib/api";
import { getSocket } from "@/lib/socket";

type Handover = {
  id: string; batch_id: string; from_org_id: string; to_org_id: string;
  status: string; eta?: string; notes?: string; created_at?: string;
};

function AcceptForm({ handover, vehicles, drivers, onDone, onCancel }: {
  readonly handover: Handover;
  readonly vehicles: any[];
  readonly drivers: any[];
  readonly onDone: () => void;
  readonly onCancel: () => void;
}) {
  const [qr, setQr] = useState("");
  const [vehicleId, setVehicleId] = useState(vehicles[0]?.id ?? "");
  const [driverId, setDriverId] = useState(drivers[0]?.id ?? "");
  const [eta, setEta] = useState(handover.eta ? handover.eta.slice(0, 16) : "");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setErr("");
    try {
      await post(`/api/handovers/${handover.id}/accept`, {
        qr_token: qr.trim(), vehicle_id: vehicleId || undefined,
        driver_id: driverId || undefined,
        eta: eta ? new Date(eta).toISOString() : undefined,
        notes: notes || undefined,
      });
      onDone();
    } catch (ex: any) { setErr(ex.message); }
    finally { setBusy(false); }
  }

  return (
    <form onSubmit={submit} style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 8 }}>
      <div className="row">
        <div>
          <label>Batch QR token (scan or paste)</label>
          <input type="text" value={qr} onChange={(e) => setQr(e.target.value)}
            placeholder="Paste token or scan QR" required autoFocus />
        </div>
        {vehicles.length > 0 && (
          <div>
            <label>Vehicle</label>
            <select value={vehicleId} onChange={(e) => setVehicleId(e.target.value)}>
              <option value="">— none —</option>
              {vehicles.map((v) => <option key={v.id} value={v.id}>{v.reg_number}</option>)}
            </select>
          </div>
        )}
        {drivers.length > 0 && (
          <div>
            <label>Driver</label>
            <select value={driverId} onChange={(e) => setDriverId(e.target.value)}>
              <option value="">— none —</option>
              {drivers.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
        )}
        <div>
          <label>ETA</label>
          <input type="datetime-local" value={eta} onChange={(e) => setEta(e.target.value)} />
        </div>
        <div>
          <label>Notes</label>
          <input type="text" value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <button type="submit" disabled={!qr || busy}>{busy ? "Accepting…" : "Confirm acceptance"}</button>
        <button type="button" className="ghost" onClick={onCancel}>Cancel</button>
      </div>
      {err && <p style={{ color: "var(--red)" }}>{err}</p>}
    </form>
  );
}

function RejectForm({ handover, onDone, onCancel }: {
  readonly handover: Handover;
  readonly onDone: () => void;
  readonly onCancel: () => void;
}) {
  const [qr, setQr] = useState("");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setErr("");
    try {
      await post(`/api/handovers/${handover.id}/reject`, {
        qr_token: qr.trim(), notes: notes || undefined,
      });
      onDone();
    } catch (ex: any) { setErr(ex.message); }
    finally { setBusy(false); }
  }

  return (
    <form onSubmit={submit} style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 8 }}>
      <div className="row">
        <div>
          <label>Batch QR token</label>
          <input type="text" value={qr} onChange={(e) => setQr(e.target.value)}
            placeholder="Paste token or scan QR" autoFocus />
        </div>
        <div>
          <label>Reason</label>
          <input type="text" value={notes} onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. weight discrepancy at loading" required />
        </div>
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <button type="submit" style={{ background: "var(--red)" }} disabled={!notes || busy}>
          {busy ? "Rejecting…" : "Confirm rejection"}
        </button>
        <button type="button" className="ghost" onClick={onCancel}>Cancel</button>
      </div>
      {err && <p style={{ color: "var(--red)" }}>{err}</p>}
    </form>
  );
}

export default function PendingHandovers({
  role, onAccepted,
}: {
  readonly role: "TRANSPORTER" | "PROCESSOR" | "BUYER";
  readonly onAccepted?: () => void;
}) {
  const [handovers, setHandovers] = useState<Handover[]>([]);
  const [vehicles, setVehicles] = useState<any[]>([]);
  const [drivers, setDrivers] = useState<any[]>([]);
  const [active, setActive] = useState<{ id: string; mode: "accept" | "reject" } | null>(null);

  const load = () => get<Handover[]>("/api/handovers?pending=1")
    .then(setHandovers).catch(() => {});

  useEffect(() => {
    load();
    get("/api/vehicles").then(setVehicles).catch(() => {});
    get("/api/drivers").then(setDrivers).catch(() => {});
    const s = getSocket();
    s.on("handover.offered", load);
    s.on("handover.accepted", load);
    s.on("handover.rejected", load);
    return () => {
      s.off("handover.offered", load);
      s.off("handover.accepted", load);
      s.off("handover.rejected", load);
    };
  }, []);

  if (handovers.length === 0) return null;

  const label = role === "TRANSPORTER" ? "Pending pickups" : "Pending deliveries";

  return (
    <div className="card" style={{ borderLeft: "3px solid var(--green)" }}>
      <h3>{label} <span className="badge amber">{handovers.length}</span></h3>
      {handovers.map((h) => (
        <div key={h.id} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: "1px solid var(--border)" }}>
          <div className="row" style={{ alignItems: "center" }}>
            <span><b>{h.batch_id.slice(0, 8)}…</b></span>
            {h.eta && <span className="muted">ETA: {new Date(h.eta).toLocaleString()}</span>}
            {h.notes && <span className="muted">{h.notes}</span>}
            <button onClick={() => setActive({ id: h.id, mode: "accept" })}
              disabled={!!active}>Accept custody</button>
            <button className="ghost" onClick={() => setActive({ id: h.id, mode: "reject" })}
              disabled={!!active} style={{ color: "var(--red)" }}>Reject</button>
          </div>
          {active?.id === h.id && active.mode === "accept" && (
            <AcceptForm handover={h} vehicles={vehicles} drivers={drivers}
              onDone={() => { setActive(null); load(); onAccepted?.(); }}
              onCancel={() => setActive(null)} />
          )}
          {active?.id === h.id && active.mode === "reject" && (
            <RejectForm handover={h}
              onDone={() => { setActive(null); load(); }}
              onCancel={() => setActive(null)} />
          )}
        </div>
      ))}
    </div>
  );
}
