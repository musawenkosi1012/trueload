"use client";
import { useState } from "react";

import { post } from "@/lib/api";

const SITE_TYPES = ["MINE", "PLANT", "WEIGHBRIDGE", "LAB"];

export default function NewSiteRouteForm({
  accounts, sites, onChanged,
}: {
  readonly accounts: any[];
  readonly sites: any[];
  readonly onChanged: () => void;
}) {
  const [site, setSite] = useState({ name: "", type: "MINE", account_id: "", lat: "", lng: "" });
  const [route, setRoute] = useState({ name: "", origin_site_id: "", dest_site_id: "", buffer_m: "500", path: "[]" });
  const [err, setErr] = useState("");

  async function addSite(e: React.FormEvent) {
    e.preventDefault(); setErr("");
    try {
      await post("/api/sites", { ...site, account_id: site.account_id || accounts[0]?.id, lat: +site.lat, lng: +site.lng });
      setSite({ name: "", type: "MINE", account_id: "", lat: "", lng: "" }); onChanged();
    } catch (e: any) { setErr(e.message); }
  }
  async function addRoute(e: React.FormEvent) {
    e.preventDefault(); setErr("");
    let path: any;
    try { path = JSON.parse(route.path); } catch { setErr("Path must be JSON like [[lat,lng],…]"); return; }
    try {
      await post("/api/routes", { name: route.name, origin_site_id: route.origin_site_id, dest_site_id: route.dest_site_id, buffer_m: +route.buffer_m, path });
      setRoute({ name: "", origin_site_id: "", dest_site_id: "", buffer_m: "500", path: "[]" }); onChanged();
    } catch (e: any) { setErr(e.message); }
  }

  return (
    <div className="grid">
      <form className="card" onSubmit={addSite}>
        <h3>New site</h3>
        <div className="row">
          <div><label>Name</label><input value={site.name} onChange={(e) => setSite({ ...site, name: e.target.value })} /></div>
          <div><label>Type</label><select value={site.type} onChange={(e) => setSite({ ...site, type: e.target.value })}>{SITE_TYPES.map((t) => <option key={t}>{t}</option>)}</select></div>
          <div><label>Account</label><select value={site.account_id} onChange={(e) => setSite({ ...site, account_id: e.target.value })}>{accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}</select></div>
          <div><label>Lat</label><input type="number" step="any" value={site.lat} onChange={(e) => setSite({ ...site, lat: e.target.value })} /></div>
          <div><label>Lng</label><input type="number" step="any" value={site.lng} onChange={(e) => setSite({ ...site, lng: e.target.value })} /></div>
          <button disabled={!site.name}>Add site</button>
        </div>
      </form>
      <form className="card" onSubmit={addRoute}>
        <h3>New corridor</h3>
        <div className="row">
          <div><label>Name</label><input value={route.name} onChange={(e) => setRoute({ ...route, name: e.target.value })} /></div>
          <div><label>Origin</label><select value={route.origin_site_id} onChange={(e) => setRoute({ ...route, origin_site_id: e.target.value })}><option value="">—</option>{sites.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select></div>
          <div><label>Dest</label><select value={route.dest_site_id} onChange={(e) => setRoute({ ...route, dest_site_id: e.target.value })}><option value="">—</option>{sites.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select></div>
          <div><label>Buffer (m)</label><input type="number" value={route.buffer_m} onChange={(e) => setRoute({ ...route, buffer_m: e.target.value })} /></div>
        </div>
        <label>Path — JSON [[lat,lng],…]</label>
        <input value={route.path} onChange={(e) => setRoute({ ...route, path: e.target.value })} style={{ width: "100%" }} />
        <button disabled={!route.name || !route.origin_site_id || !route.dest_site_id} style={{ marginTop: 8 }}>Add corridor</button>
      </form>
      {err && <p style={{ color: "var(--red)" }}>{err}</p>}
    </div>
  );
}
