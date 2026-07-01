"use client";
import { useEffect, useState } from "react";

import AssayRow from "@/components/AssayRow";
import Shell from "@/components/Shell";
import PageHeader from "@/components/shell/PageHeader";
import { get } from "@/lib/api";
import { getSocket } from "@/lib/socket";

export default function LabPage() {
  const [samples, setSamples] = useState<any[]>([]);
  const [grades, setGrades] = useState<Record<string, number>>({});
  const [assays, setAssays] = useState<Record<string, any[]>>({});

  const loadSamples = () => get("/api/samples").then(setSamples).catch(() => {});
  const loadAssays = () => get("/api/assays").then((rows: any[]) => {
    const by: Record<string, any[]> = {};
    rows.forEach((a) => { (by[a.sample_id] ??= []).push(a); });
    setAssays(by);
  }).catch(() => {});

  useEffect(() => {
    loadSamples();
    loadAssays();
    get("/api/batches").then((bs: any[]) => {
      const g: Record<string, number> = {};
      bs.forEach((b) => { if (b.grade_pct != null) g[b.id] = b.grade_pct; });
      setGrades(g);
    }).catch(() => {});
    const s = getSocket();
    s.on("assay.recorded", loadAssays);
    return () => { s.off("assay.recorded", loadAssays); };
  }, []);

  const onRecorded = () => { loadAssays(); };

  return (
    <Shell role="LAB">
      <PageHeader title="Lab" subtitle="Samples awaiting assay" />
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Sample</th><th>Batch</th><th>Stage</th><th>Declared</th>
              <th>Analyte</th><th>Value</th><th>History</th><th></th>
            </tr>
          </thead>
          <tbody>
            {samples.map((s) => (
              <AssayRow key={s.id} sample={s} declared={grades[s.batch_id]}
                history={assays[s.id] ?? []} onRecorded={onRecorded} />
            ))}
            {samples.length === 0 && (
              <tr><td className="muted" colSpan={8}>No samples awaiting assay.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </Shell>
  );
}
