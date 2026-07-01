"use client";
import dynamic from "next/dynamic";

const MapView = dynamic(() => import("./MapView"), {
  ssr: false,
  loading: () => <div className="muted">Loading map…</div>,
});

export default MapView;
