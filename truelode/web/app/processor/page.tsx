"use client";
import { useState } from "react";

import BatchTable from "@/components/BatchTable";
import FlagsPanel from "@/components/FlagsPanel";
import PendingHandovers from "@/components/PendingHandovers";
import ProcessTools from "@/components/ProcessTools";
import Shell from "@/components/Shell";
import PageHeader from "@/components/shell/PageHeader";
import Tabs, { useTab } from "@/components/shell/Tabs";
import StatGrid from "@/components/StatGrid";

export default function ProcessorPage() {
  const [batchId, setBatchId] = useState("");
  const [tab, setTab] = useTab("overview");

  return (
    <Shell role="PROCESSOR">
      <PageHeader title="Processor" subtitle="Plant floor" />
      <Tabs tab={tab} onSelect={setTab} tabs={[
        { key: "overview", label: "Overview" }, { key: "process", label: "Process" },
        { key: "batches", label: "Batches" }, { key: "alerts", label: "Alerts" }]} />
      {tab === "overview" && <StatGrid />}
      {tab === "process" && (
        <>
          <PendingHandovers role="PROCESSOR" />
          <p className="muted" style={{ marginTop: 16 }}>Scan a batch QR, click a row in Batches, or paste an id.</p>
          <ProcessTools batchId={batchId} setBatchId={setBatchId} />
        </>
      )}
      {tab === "batches" && <BatchTable onSelect={(b) => { setBatchId(b.id); setTab("process"); }} />}
      {tab === "alerts" && <FlagsPanel canClear />}
    </Shell>
  );
}
