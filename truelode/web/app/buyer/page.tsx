"use client";
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

import Shell from "@/components/Shell";
import PageHeader from "@/components/shell/PageHeader";
import Tabs, { useTab } from "@/components/shell/Tabs";
import VerifiedBadge from "@/components/VerifiedBadge";
import { get, post } from "@/lib/api";

const QrScanner = dynamic(() => import("@/components/QrScanner"), { ssr: false });

export default function BuyerPage() {
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState("");
  const [query, setQuery] = useState("");
  const [sortGrade, setSortGrade] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [msg, setMsg] = useState("");
  const [tab, setTab] = useTab("products");

  const load = () => get("/api/batches?stage=PRODUCT")
    .then(setProducts).catch(() => {}).finally(() => setLoading(false));
  useEffect(() => { load(); }, []);

  function onScan(text: string) {
    setScanning(false);
    if (text.startsWith("__error__")) { setMsg("Camera error — paste the token instead."); return; }
    setToken(text.trim().split(/[?#]/)[0].split("/").filter(Boolean).pop() || "");
  }

  async function claim(id: string) {
    setMsg("");
    const qr = window.prompt("Scan or paste the passport QR token on the goods to claim custody:");
    if (!qr) return;
    try { await post(`/api/batches/${id}/claim`, { qr_token: qr.trim() }); setMsg("Custody claimed — recorded on the ledger."); load(); }
    catch (e: any) { setMsg(e.message); }
  }

  const rows = products
    .filter((b) => !query || b.code.toLowerCase().includes(query.toLowerCase()))
    .sort((a, b) => sortGrade ? (b.grade_pct ?? 0) - (a.grade_pct ?? 0) : 0);

  return (
    <Shell role="BUYER">
      <PageHeader title="Buyer" subtitle="Verified provenance" />
      <Tabs tab={tab} onSelect={setTab} tabs={[
        { key: "products", label: "Products" }, { key: "verify", label: "Verify" }]} />
      {tab === "verify" && (
      <div className="card">
        <label>Scan or paste a passport QR token</label>
        <div className="row">
          <input value={token} onChange={(e) => setToken(e.target.value)} style={{ flex: 1, minWidth: 220 }} />
          <button className="ghost" onClick={() => { setMsg(""); setScanning(true); }}>📷 Scan</button>
          <a href={`/verify/${token}`} target="_blank"><button disabled={!token}>Open passport</button></a>
        </div>
        {scanning && <div style={{ marginTop: 10 }}>
          <QrScanner onResult={onScan} onClose={() => setScanning(false)} /></div>}
        {msg && <p className="muted" style={{ color: "var(--green)" }}>{msg}</p>}
      </div>
      )}

      {tab === "products" && (
      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h3 style={{ margin: 0 }}>Battery-grade product batches</h3>
          <div className="row">
            <input placeholder="Filter by code" value={query} onChange={(e) => setQuery(e.target.value)} />
            <button className="ghost" onClick={() => setSortGrade((v) => !v)}>
              {sortGrade ? "Sorted by grade ↓" : "Sort by grade"}</button>
          </div>
        </div>
        <table>
          <thead><tr><th>Code</th><th>Units</th><th>Grade</th><th>Status</th><th>Passport</th><th></th></tr></thead>
          <tbody>
            {rows.map((b) => (
              <tr key={b.id}>
                <td>{b.code}</td>
                <td>{b.unit_count ?? "—"} {b.unit_label ?? ""}</td>
                <td>{b.grade_pct}%</td>
                <td><VerifiedBadge token={b.qr_token} /></td>
                <td><a href={`/verify/${b.qr_token}`} target="_blank">verify →</a></td>
                <td><button className="ghost" onClick={() => claim(b.id)}>Claim</button></td>
              </tr>
            ))}
            {loading && <tr><td className="muted" colSpan={6}>Loading…</td></tr>}
            {!loading && rows.length === 0 && <tr><td className="muted" colSpan={6}>No product batches yet.</td></tr>}
          </tbody>
        </table>
      </div>
      )}
    </Shell>
  );
}
