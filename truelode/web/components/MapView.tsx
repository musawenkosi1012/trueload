"use client";
import "leaflet/dist/leaflet.css";
import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip } from "react-leaflet";

type Pt = [number, number];

export default function MapView({
  corridor = [],
  track = [],
}: {
  corridor?: Pt[];
  track?: { lat: number; lng: number; off?: boolean }[];
}) {
  const center: Pt = corridor[Math.floor(corridor.length / 2)] ||
    (track[0] ? [track[0].lat, track[0].lng] : [-19, 31]);

  return (
    <MapContainer center={center} zoom={7} style={{ height: 380, borderRadius: 10 }}>
      <TileLayer
        attribution="© OpenStreetMap"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {corridor.length > 1 && (
        <Polyline positions={corridor} pathOptions={{ color: "#2ea043", weight: 4 }} />
      )}
      {track.map((p, i) => (
        <CircleMarker
          key={i}
          center={[p.lat, p.lng]}
          radius={6}
          pathOptions={{ color: p.off ? "#e5484d" : "#58a6ff" }}
        >
          <Tooltip>{p.off ? "OFF ROUTE" : "on route"}</Tooltip>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
