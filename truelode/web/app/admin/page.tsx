"use client";
import { useEffect, useState } from "react";

import NewAccountForm from "@/components/NewAccountForm";
import NewSiteRouteForm from "@/components/NewSiteRouteForm";
import Shell from "@/components/Shell";
import PageHeader from "@/components/shell/PageHeader";
import Tabs, { useTab } from "@/components/shell/Tabs";
import StatGrid from "@/components/StatGrid";
import { get, patch } from "@/lib/api";

export default function AdminPage() {
  const [orgs, setOrgs] = useState<any[]>([]);
  const [sites, setSites] = useState<any[]>([]);
  const [routes, setRoutes] = useState<any[]>([]);
  const [query, setQuery] = useState("");
  const [tab, setTab] = useTab("overview");

  const loadOrgs = () => get("/api/accounts").then(setOrgs).catch(() => {});
  const loadSites = () => get("/api/sites").then(setSites).catch(() => {});
  const loadRoutes = () => get("/api/routes").then(setRoutes).catch(() => {});
  useEffect(() => { loadOrgs(); loadSites(); loadRoutes(); }, []);

  async function setStatus(id: string, status: string) {
    await patch(`/api/accounts/${id}`, { status });
    loadOrgs();
  }

  const rows = orgs.filter((o) =>
    !query || o.name.toLowerCase().includes(query.toLowerCase()));

  return (
    <Shell role="ADMIN">
      <PageHeader title="Admin" subtitle="Registry & accounts" />
      <Tabs tab={tab} onSelect={setTab} tabs={[
        { key: "overview", label: "Overview" }, { key: "accounts", label: "Accounts" },
        { key: "registry", label: "Registry" }]} />
      {tab === "overview" && <StatGrid />}
      {tab === "accounts" && (<>
      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h3 style={{ margin: 0 }}>Accounts</h3>
          <input placeholder="Search accounts" value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>
        <table>
          <thead><tr><th>Name</th><th>Type</th><th>Role</th><th>Status</th><th></th></tr></thead>
          <tbody>
            {rows.map((o) => (
              <tr key={o.id}>
                <td>{o.name}</td>
                <td>{o.account_type}{o.exempt ? " · exempt" : ""}</td>
                <td>{o.primary_role}</td>
                <td><span className={`badge ${o.status === "ACTIVE" ? "green" : "red"}`}>{o.status}</span></td>
                <td>
                  {o.status === "ACTIVE"
                    ? <button className="ghost" onClick={() => setStatus(o.id, "SUSPENDED")}>Suspend</button>
                    : <button className="ghost" onClick={() => setStatus(o.id, "ACTIVE")}>Reactivate</button>}
                </td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td className="muted" colSpan={5}>No accounts.</td></tr>}
          </tbody>
        </table>
      </div>
      <NewAccountForm onCreated={loadOrgs} />
      </>)}
      {tab === "registry" && (<>
      <div className="grid">
        <div className="card">
          <h3>Sites</h3>
          {sites.map((s) => <div key={s.id} className="muted">{s.name} · {s.type}</div>)}
          {sites.length === 0 && <div className="muted">No sites.</div>}
        </div>
        <div className="card">
          <h3>Corridors</h3>
          {routes.map((r) => <div key={r.id} className="muted">{r.name} · buffer {r.buffer_m} m</div>)}
          {routes.length === 0 && <div className="muted">No corridors.</div>}
        </div>
      </div>
      <NewSiteRouteForm accounts={orgs} sites={sites} onChanged={() => { loadSites(); loadRoutes(); }} />
      </>)}
    </Shell>
  );
}
