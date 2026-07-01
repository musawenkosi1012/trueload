"use client";
import { useState } from "react";

import { post } from "@/lib/api";

const ANALYTES = ["Li2O", "Fe2O3", "Na2O", "moisture"];

type Sample = { id: string; label?: string; batch_id: string; stage_tag?: string };
type Assay = { analyte: string; value: number };

export default function AssayRow({
  sample, declared, history, onRecorded,
}: {
  readonly sample: Sample;
  readonly declared?: number;
  readonly history: Assay[];
  readonly onRecorded: () => void;
}) {
  const [analyte, setAnalyte] = useState("Li2O");
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);

  const num = parseFloat(value);
  const valid = value !== "" && !Number.isNaN(num) && num >= 0 && num <= 100;
  const diff = analyte === "Li2O" && declared != null && valid ? num - declared : null;
  const mismatch = diff != null && Math.abs(diff) > 0.5;

  async function submit() {
    if (!valid) return;
    if (!globalThis.confirm(`Record ${analyte} = ${num}% for ${sample.label || sample.id.slice(0, 8)}? This is signed into the ledger.`)) return;
    setBusy(true);
    try {
      await post("/api/assays", { sample_id: sample.id, analyte, value: num });
      setValue("");
      onRecorded();
    } finally {
      setBusy(false);
    }
  }

  return (
    <tr>
      <td>{sample.label || sample.id.slice(0, 8)}</td>
      <td className="muted">{sample.batch_id.slice(0, 8)}</td>
      <td>{sample.stage_tag}</td>
      <td className="muted">{declared != null ? `${declared}%` : "—"}</td>
      <td>
        <select value={analyte} onChange={(e) => setAnalyte(e.target.value)}>
          {ANALYTES.map((a) => <option key={a} value={a}>{a}</option>)}
        </select>
      </td>
      <td>
        <input type="number" step={0.1} min={0} max={100} style={{ width: 90 }}
          value={value} onChange={(e) => setValue(e.target.value)} />
        {diff != null && (
          <div className={`hint${mismatch ? " bad" : ""}`}>
            {mismatch ? `${diff > 0 ? "+" : ""}${diff.toFixed(2)} vs declared` : "matches declared"}
          </div>
        )}
      </td>
      <td className="muted">
        {history.length === 0 ? "—" : history.map((a, i) => (
          <div key={i}>{a.analyte}: {a.value}%</div>
        ))}
      </td>
      <td>
        <button disabled={!valid || busy} onClick={submit}>{busy ? "…" : "Record"}</button>
      </td>
    </tr>
  );
}
