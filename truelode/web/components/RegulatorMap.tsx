"use client";
import { useEffect, useState } from "react";

import { get } from "@/lib/api";
import { getSocket } from "@/lib/socket";

import TripMap from "./TripMap";

export default function RegulatorMap() {
  const [trips, setTrips] = useState<any[]>([]);
  const [routes, setRoutes] = useState<any[]>([]);
  const [codes, setCodes] = useState<Record<string, string>>({});
  const [tripId, setTripId] = useState("");
  const [track, setTrack] = useState<any[]>([]);

  const loadTrack = () => {
    if (tripId) get(`/api/dashboard/map/${tripId}`).then((d) => setTrack(d.track));
  };

  useEffect(() => {
    get("/api/trips").then((t) => { setTrips(t); if (!tripId && t[0]) setTripId(t[0].id); });
    get("/api/routes").then(setRoutes);
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
  const corridor = routes.find((r) => r.id === trip?.route_id)?.path || [];

  return (
    <div className="card">
      <div className="row">
        <div>
          <label>Trip</label>
          <select value={tripId} onChange={(e) => setTripId(e.target.value)}>
            {trips.map((t) => <option key={t.id} value={t.id}>
              {codes[t.batch_id] || t.id.slice(0, 8)} · {t.status}</option>)}
          </select>
        </div>
      </div>
      <TripMap corridor={corridor} track={track.map((p) => ({ lat: p.lat, lng: p.lng }))} />
    </div>
  );
}
