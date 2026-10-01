"use client";
import { useEffect, useState } from "react";

import BatchTable from "@/components/BatchTable";
import HandoverOffer from "@/components/HandoverOffer";
import MintedBatch from "@/components/MintedBatch";
import Shell from "@/components/Shell";
import PageHeader from "@/components/shell/PageHeader";
import Tabs, { useTab } from "@/components/shell/Tabs";
import StatGrid from "@/components/StatGrid";
import { get, post } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function MinePage() {
  const { user, refresh } = useAuth();
  const [sites, setSites] = useState<any[]>([]);
  const [routes, setRoutes] = useState<any[]>([]);
  const [orgs, setOrgs] = useState<any[]>([]);
  const [form, setForm] = useState({ mine_site_id: "", route_id: "", weight: 30, grade: 1.5 });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState<any[]>([]);
  const [tab, setTab] = useTab("overview");

  const delinquent = user?.account_status === "DELINQUENT";

  useEffect(() => {
    get("/api/sites").then((s) => {
      setSites(s);
      setForm((f) => ({ ...f, mine_site_id: f.mine_site_id || s[0]?.id || "" }));
    }).catch(() => {});
    get("/api/routes").then((r) => {
      setRoutes(r);
      setForm((f) => ({ ...f, route_id: f.route_id || r[0]?.id || "" }));
    }).catch(() => {});
    get("/api/accounts").then(setOrgs).catch(() => {});
  }, []);

  const weightOk = form.weight > 0 && form.weight <= 1000;
  const gradeOk = form.grade >= 0 && form.grade <= 100;
  const canSubmit = weightOk && gradeOk && !!form.mine_site_id && !delinquent && !busy;

  async function createTicket(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    setBusy(true);
    const site = sites.find((s) => s.id === form.mine_site_id);
    try {
      const res = await post("/api/loadtickets", {
        mine_site_id: form.mine_site_id, net_weight_kg: form.weight * 1000,
        grade_pct: form.grade, route_id: form.route_id,
        lat: site?.lat, lng: site?.lng, source: "MANUAL",
      });
      setHistory((h) => [res.batch, ...h]);
      refresh(); // wallet was debited — pull the new balance
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Shell role="MINE">
      <PageHeader title="Mine" subtitle="Load tickets" />
      <Tabs tab={tab} onSelect={setTab} tabs={[
        { key: "overview", label: "Overview" }, { key: "ticket", label: "Load ticket" },
        { key: "batches", label: "Batches" }]} />
      {tab === "overview" && (<>
        <StatGrid />
        <BatchTable />
      </>)}
      {tab === "ticket" && (<>
      <form className="card" onSubmit={createTicket}>
        <div className="row">
          <div>
            <label>Mine site</label>
            <select value={form.mine_site_id} onChange={(e) => setForm({ ...form, mine_site_id: e.target.value })}>
              {sites.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          <div>
            <label>Route</label>
            <select value={form.route_id} onChange={(e) => setForm({ ...form, route_id: e.target.value })}>
              {routes.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
            </select>
          </div>
          <div>
            <label>Net weight (t)</label>
            <input type="number" min={0.1} max={1000} step={0.1} value={form.weight}
              onChange={(e) => setForm({ ...form, weight: +e.target.value })} />
            <div className={`hint${weightOk ? "" : " bad"}`}>
              {weightOk ? `${(form.weight * 1000).toLocaleString()} kg` : "Enter 0–1000 t"}
            </div>
          </div>
          <div>
            <label>Grade Li₂O %</label>
            <input type="number" step={0.1} min={0} max={100} value={form.grade}
              onChange={(e) => setForm({ ...form, grade: +e.target.value })} />
            {!gradeOk && <div className="hint bad">Grade must be 0–100%</div>}
          </div>
          <button data-demo="weigh-out" disabled={!canSubmit}>{busy ? "Creating…" : "Weigh out & create batch"}</button>
        </div>
        <p className="muted">
          Creating a batch debits a per-batch fee from your wallet
          {typeof user?.balance_usd === "number" ? ` · balance $${user.balance_usd.toFixed(2)}` : ""}.
        </p>
        {delinquent && (
          <p style={{ color: "var(--red)" }}>
            Account past due — top up on the Billing page to create batches.
          </p>
        )}
        {err && <p style={{ color: "var(--red)" }}>{err}</p>}
      </form>
      {history.map((b) => (
        <div key={b.id}>
          <MintedBatch batch={b} />
          <HandoverOffer batchId={b.id} orgs={orgs} toRoles={["TRANSPORTER"]}
            prompt="Hand to transporter:" selectLabel="Transporter org"
            doneText="Handover offered — the transporter must scan the batch QR to accept." />
        </div>
      ))}
      </>)}
      {tab === "batches" && <BatchTable />}
    </Shell>
  );
}
