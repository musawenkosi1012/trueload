"use client";
import { useEffect, useState } from "react";

import Shell from "@/components/Shell";
import { get, post } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const FEATURE_LABELS: Record<string, string> = {
  team: "Team management (multiple staff)",
  multi_site: "Multiple sites",
  pay_as_you_go: "Pay-as-you-go metered billing",
  passport: "Issue provenance passports",
  priority_support: "Priority support",
};

type BillingState = {
  account: { name: string; account_type: string; status: string } | null;
  balance_usd: number;
  fees: { per_batch_usd: number; seat_usd: number; flat_usd: number };
  recent: any[];
};

export default function BillingPage() {
  const { user } = useAuth();
  const [state, setState] = useState<BillingState | null>(null);
  const [amount, setAmount] = useState(25);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  function load() {
    get<BillingState>("/api/billing/account").then(setState).catch(() => {});
  }
  useEffect(load, []);

  async function topup(e: React.FormEvent) {
    e.preventDefault();
    setMsg("");
    setLoading(true);
    try {
      const res = await post<{ checkout_url: string }>("/api/billing/topup", {
        amount_usd: amount,
      });
      // Redirect to the Payonify hosted checkout (or local mock in demo mode).
      window.location.href = res.checkout_url;
    } catch (e: any) {
      setMsg(e.message);
      setLoading(false);
    }
  }

  const acct = state?.account;
  const isOrg = acct?.account_type === "ENTERPRISE";

  return (
    <Shell>
      <h2>Billing</h2>

      <div className="grid">
        <div className="card">
          <div className="muted">Wallet balance</div>
          <div className="stat">${(state?.balance_usd ?? 0).toFixed(2)}</div>
          <div className="muted">{acct?.name} · {acct?.account_type}</div>
          <span className={`badge ${acct?.status === "ACTIVE" ? "green" : "red"}`}>
            {acct?.status}
          </span>
        </div>
        <div className="card">
          <div className="muted">Your rates</div>
          {isOrg ? (
            <>
              <div className="stat">${state?.fees.per_batch_usd}</div>
              <div className="muted">per batch (pay-as-you-go)</div>
              <div className="muted">+ ${state?.fees.seat_usd} per staff seat / cycle</div>
            </>
          ) : (
            <>
              <div className="stat">${state?.fees.flat_usd}</div>
              <div className="muted">flat per cycle · unlimited use</div>
            </>
          )}
        </div>
        <form className="card" onSubmit={topup}>
          <div className="muted">Top up via Payonify</div>
          <label>Amount (USD)</label>
          <input type="number" min={1} value={amount}
            onChange={(e) => setAmount(+e.target.value)} style={{ width: "100%" }} />
          <button style={{ marginTop: 10, width: "100%" }} disabled={loading}>
            {loading ? "Redirecting…" : "Pay with EcoCash / Card"}
          </button>
          {msg && <p style={{ color: "var(--red)" }}>{msg}</p>}
        </form>
      </div>

      <div className="card">
        <div className="muted" style={{ marginBottom: 6 }}>
          Your plan includes — <b>{acct?.account_type}</b>
          {!isOrg && <a href="/signup" style={{ marginLeft: 8 }}>upgrade to Enterprise →</a>}
        </div>
        <div className="grid">
          {Object.entries(FEATURE_LABELS).map(([key, label]) => {
            const on = !!user?.features?.[key];
            return (
              <div key={key} style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <span className={`badge ${on ? "green" : "red"}`}>{on ? "✓" : "—"}</span>
                <span style={{ color: on ? "var(--text)" : "var(--muted)" }}>{label}</span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="card">
        <div className="muted">Recent activity</div>
        <table>
          <thead>
            <tr><th>When</th><th>Type</th><th>Amount</th><th>Balance</th><th>Note</th></tr>
          </thead>
          <tbody>
            {(state?.recent ?? []).map((e) => (
              <tr key={e.id}>
                <td className="muted">{e.created_at?.slice(0, 19).replace("T", " ")}</td>
                <td>{e.kind}</td>
                <td style={{ color: e.amount_usd < 0 ? "var(--red)" : "var(--green)" }}>
                  {e.amount_usd < 0 ? "" : "+"}{e.amount_usd}
                </td>
                <td>{e.balance_after}</td>
                <td className="muted">{e.note}</td>
              </tr>
            ))}
            {!state?.recent?.length && (
              <tr><td colSpan={5} className="muted">No activity yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </Shell>
  );
}
