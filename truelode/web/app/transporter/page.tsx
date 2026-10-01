"use client";
import { useEffect, useState } from "react";

import FlagsPanel from "@/components/FlagsPanel";
import HandoverOffer from "@/components/HandoverOffer";
import PendingHandovers from "@/components/PendingHandovers";
import Shell from "@/components/Shell";
import PageHeader from "@/components/shell/PageHeader";
import Tabs, { useTab } from "@/components/shell/Tabs";
import TripMap from "@/components/TripMap";
import { get, post } from "@/lib/api";
import { getSocket } from "@/lib/socket";

export default function TransporterPage() {
  const [trips, setTrips] = useState<any[]>([]);
  const [routes, setRoutes] = useState<any[]>([]);
  const [orgs, setOrgs] = useState<any[]>([]);
  const [codes, setCodes] = useState<Record<string, string>>({});
  const [tripId, setTripId] = useState("");
  const [track, setTrack] = useState<any[]>([]);
  const [speed, setSpeed] = useState(40);
  const [busy, setBusy] = useState(false);
  const [geoErr, setGeoErr] = useState("");
  const [tab, setTab] = useTab("trips");

  const loadTrips = () => get("/api/trips").then((t) => {
    setTrips(t); if (!tripId && t[0]) setTripId(t[0].id);
  });
  const loadTrack = () => {
    if (tripId) get(`/api/dashboard/map/${tripId}`).then((d) => setTrack(d.track));
  };

  useEffect(() => {
    loadTrips();
    get("/api/routes").then(setRoutes);
    get("/api/accounts").then(setOrgs).catch(() => {});
    get("/api/batches").then((bs: any[]) =>
      setCodes(Object.fromEntries(bs.map((b) => [b.id, b.code]))));
    const s = getSocket();
    s.on("gps.ingested", loadTrack);
    return () => { s.off("gps.ingested", loadTrack); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(loadTrack, [tripId]);

  const trip = trips.find((t) => t.id === tripId);
  const route = routes.find((r) => r.id === trip?.route_id);
  const corridor = route?.path || [];
  const ready = !!tripId && corridor.length > 0;

  async function sendPing(lat: number, lng: number, sp: number) {
    if (!tripId) return;
    setBusy(true);
    try {
      await post("/api/gps/bulk", { trip_id: tripId, pings: [{ lat, lng, speed: sp }] });
      loadTrack();
    } finally { setBusy(false); }
  }

  function base(): [number, number] {
    return corridor[1] || corridor[0] || [-18.9, 31.05];
  }
  function useMyLocation() {
    setGeoErr("");
    if (!navigator.geolocation) { setGeoErr("Geolocation unavailable on this device."); return; }
    navigator.geolocation.getCurrentPosition(
      (p) => sendPing(p.coords.latitude, p.coords.longitude, p.coords.speed ?? 0),
      (e) => setGeoErr(e.message),
    );
  }

  return (
    <Shell role="TRANSPORTER">
      <PageHeader title="Transporter" subtitle="Live trips" />
      <Tabs tab={tab} onSelect={setTab} tabs={[
        { key: "trips", label: "Trips" }, { key: "alerts", label: "Alerts" }]} />
      {tab === "trips" && (<>
      <div className="card">
        <div className="row">
          <div>
            <label>Trip</label>
            <select value={tripId} onChange={(e) => setTripId(e.target.value)}>
              {trips.map((t) => <option key={t.id} value={t.id}>
                {codes[t.batch_id] || t.id.slice(0, 8)} · {t.status}</option>)}
            </select>
          </div>
          <div>
            <label>Speed (km/h)</label>
            <input type="number" min={0} style={{ width: 90 }} value={speed}
              onChange={(e) => setSpeed(+e.target.value)} />
          </div>
          <button data-demo="ping-on" disabled={!ready || busy} onClick={() => sendPing(base()[0], base()[1], speed)}>On-route ping</button>
          <button data-demo="ping-off" className="ghost" disabled={!ready || busy} onClick={() => sendPing(base()[0], base()[1] + 1.5, speed)}>Off-route ping</button>
          <button data-demo="ping-stop" className="ghost" disabled={!ready || busy} onClick={() => sendPing(base()[0], base()[1], 0)}>Stop ping</button>
          <button className="ghost" disabled={!tripId || busy} onClick={useMyLocation}>Use my GPS</button>
        </div>
        {trip && (
          <p className="muted">
            Batch {codes[trip.batch_id] || trip.batch_id.slice(0, 8)} · route {route?.name ?? "—"}
            {route ? ` · corridor buffer ${route.buffer_m} m` : ""} · {track.length} pings logged
          </p>
        )}
        {!ready && <p className="hint bad">Select a trip with an assigned corridor to send synthetic pings.</p>}
        {geoErr && <p style={{ color: "var(--red)" }}>{geoErr}</p>}
      </div>
      <div className="card">
        <TripMap corridor={corridor}
          track={track.map((p) => ({ lat: p.lat, lng: p.lng }))} />
      </div>
      {trip && (
        <div className="card" key={trip.batch_id}>
          <HandoverOffer batchId={trip.batch_id} orgs={orgs} toRoles={["PROCESSOR"]}
            prompt="At the plant gate? Hand the batch to the processor:"
            selectLabel="Processor org"
            doneText="Handover offered — the plant must scan the batch QR to accept custody." />
        </div>
      )}
      </>)}
      {tab === "alerts" && <FlagsPanel />}
      {tab === "trips" && <PendingHandovers role="TRANSPORTER" onAccepted={loadTrips} />}
    </Shell>
  );
}
