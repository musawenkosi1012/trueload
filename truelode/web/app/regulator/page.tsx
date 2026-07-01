"use client";
import ChainIntegrity from "@/components/ChainIntegrity";
import FlagBreakdown from "@/components/FlagBreakdown";
import FlagsPanel from "@/components/FlagsPanel";
import LedgerPanel from "@/components/LedgerPanel";
import LiveFeed from "@/components/LiveFeed";
import RegulatorMap from "@/components/RegulatorMap";
import Shell from "@/components/Shell";
import PageHeader from "@/components/shell/PageHeader";
import Tabs, { useTab } from "@/components/shell/Tabs";
import StatGrid from "@/components/StatGrid";
import { get } from "@/lib/api";

export default function RegulatorPage() {
  const [tab, setTab] = useTab("overview");

  async function exportCsv() {
    const rows = await get<any[]>("/api/dashboard/ledger");
    const head = "seq,event_type,entry_hash,prev_hash\n";
    const body = rows.map((r) => `${r.seq},${r.event_type},${r.entry_hash},${r.prev_hash}`).join("\n");
    const blob = new Blob([head + body], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "truelode-ledger.csv"; a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <Shell role="REGULATOR">
      <PageHeader title="Regulator" subtitle="Ministry of Mines / MMCZ — corridor-wide oversight" />
      <Tabs tab={tab} onSelect={setTab} tabs={[
        { key: "overview", label: "Overview" }, { key: "map", label: "Map" },
        { key: "alerts", label: "Alerts" }, { key: "ledger", label: "Ledger" }]} />

      {tab === "overview" && (<>
        <ChainIntegrity />
        <StatGrid />
        <LiveFeed />
      </>)}
      {tab === "map" && <RegulatorMap />}
      {tab === "alerts" && (<>
        <FlagsPanel canClear />
        <FlagBreakdown />
      </>)}
      {tab === "ledger" && (<>
        <ChainIntegrity />
        <div className="row" style={{ justifyContent: "flex-end" }}>
          <button className="ghost" onClick={exportCsv}>Export ledger CSV</button>
        </div>
        <LedgerPanel />
      </>)}
    </Shell>
  );
}
