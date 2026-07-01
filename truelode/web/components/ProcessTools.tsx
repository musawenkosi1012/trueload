"use client";
import { useEffect, useState } from "react";

import { get, post } from "@/lib/api";

import BatchPicker from "./BatchPicker";

const PRESETS: Record<string, { kg: number; grade: number; units: number }> = {
  CONCENTRATE: { kg: 8, grade: 6, units: 0 },
  LI_SULPHATE: { kg: 6, grade: 9, units: 0 },
  PRODUCT: { kg: 4, grade: 11, units: 20 },
};

export default function ProcessTools({
  batchId, setBatchId,
}: {
  readonly batchId: string;
  readonly setBatchId: (v: string) => void;
}) {
  const [batch, setBatch] = useState<any>(null);
  const [inKg, setInKg] = useState(30);
  const [out, setOut] = useState({ kg: 4, grade: 11, units: 20, stage: "PRODUCT" });
  const [recon, setRecon] = useState<any>(null);
  const [pass, setPass] = useState<any>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState("");

  const loadBatch = () => batchId
    ? get(`/api/batches/${batchId}`).then(setBatch).catch(() => setBatch(null))
    : setBatch(null);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { loadBatch(); }, [batchId]);

  const canWeighIn = batch?.state === "IN_TRANSIT";
  const canProcess = batch?.state === "RECEIVED";
  const outOk = out.kg > 0 && out.grade >= 0 && out.grade <= 100 && out.units >= 0;

  function pickStage(stage: string) {
    setOut({ ...PRESETS[stage], stage });
  }

  async function run(label: string, fn: () => Promise<void>) {
    setErr(""); setBusy(label);
    try { await fn(); } catch (e: any) { setErr(e.message); } finally { setBusy(""); }
  }

  const weighIn = () => run("weigh", async () => {
    const r = await post("/api/weighevents", { batch_id: batchId, kind: "PLANT_IN", net_kg: inKg * 1000 });
    setRecon(r.reconcile); loadBatch();
  });
  const processStep = () => run("process", async () => {
    const r = await post("/api/processing-steps", {
      parent_ids: [batchId], out_stage: out.stage, out_kg: out.kg * 1000,
      out_grade: out.grade, unit_count: out.units, unit_label: "drums", tol_pct: 50,
    });
    setBatchId(r.child.id); setRecon(r.result);
  });
  const issue = () => run("issue", async () => setPass(await post(`/api/passport/${batchId}`, {})));

  return (
    <div className="card">
      <h3>Processor actions</h3>
      <BatchPicker batchId={batchId} setBatchId={setBatchId} />
      {batch && <p className="muted">State: <span className={`badge ${batch.state === "RECEIVED" || batch.state === "CLOSED" ? "green" : "amber"}`}>{batch.state}</span> · {batch.stage}</p>}

      <div className="row" style={{ marginTop: 10 }}>
        <div><label>Arrival weight (t)</label>
          <input type="number" min={0.1} value={inKg} onChange={(e) => setInKg(+e.target.value)} /></div>
        <button onClick={weighIn} disabled={!canWeighIn || inKg <= 0 || !!busy}>
          {busy === "weigh" ? "…" : "Weigh in & reconcile"}</button>
        {batchId && !canWeighIn && <span className="hint">Weigh-in needs an IN_TRANSIT batch.</span>}
      </div>

      <div className="row" style={{ marginTop: 10 }}>
        <div><label>Out stage</label>
          <select value={out.stage} onChange={(e) => pickStage(e.target.value)}>
            {Object.keys(PRESETS).map((s) => <option key={s} value={s}>{s}</option>)}
          </select></div>
        <div><label>Out (t)</label>
          <input type="number" min={0.01} value={out.kg} onChange={(e) => setOut({ ...out, kg: +e.target.value })} /></div>
        <div><label>Out grade %</label>
          <input type="number" min={0} max={100} value={out.grade} onChange={(e) => setOut({ ...out, grade: +e.target.value })} /></div>
        <div><label>Units</label>
          <input type="number" min={0} value={out.units} onChange={(e) => setOut({ ...out, units: +e.target.value })} /></div>
        <button onClick={processStep} disabled={!canProcess || !outOk || !!busy}>
          {busy === "process" ? "…" : "Process → child batch"}</button>
        {batchId && !canProcess && <span className="hint">Process needs a RECEIVED batch.</span>}
      </div>

      {recon && (
        <p>Mass balance:{" "}
          <span className={`badge ${recon.ok ? "green" : "red"}`}>{recon.ok ? "PASS" : "FAIL"}</span>
          {recon.out_kg !== undefined && <span className="muted"> {recon.out_kg} → {recon.in_kg} kg</span>}
          {recon.delta_kg !== undefined && <span className="muted"> · Δ {recon.delta_kg} kg</span>}
          {recon.ratio !== undefined && <span className="muted"> · ratio {recon.ratio}</span>}
        </p>
      )}
      <button onClick={issue} disabled={!batchId || !!busy} style={{ marginTop: 8 }}>
        {busy === "issue" ? "…" : "Issue passport"}</button>
      {pass && <p style={{ color: "var(--green)" }}>Passport: <a href={`/verify/${pass.qr_token}`} target="_blank">/verify/{pass.qr_token.slice(0, 10)}…</a></p>}
      {err && <p style={{ color: "var(--red)" }}>{err}</p>}
    </div>
  );
}
