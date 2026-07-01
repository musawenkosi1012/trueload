"use client";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { post } from "@/lib/api";

function MockCheckout() {
  const params = useSearchParams();
  const reference = params.get("reference") || "";
  const amount = params.get("amount") || "0";
  const returnUrl = params.get("return_url") || "/billing";
  const [status, setStatus] = useState<"idle" | "paying" | "done">("idle");
  const [err, setErr] = useState("");

  async function pay() {
    setStatus("paying");
    setErr("");
    try {
      await post("/api/payments/mock-complete", { reference });
      setStatus("done");
      setTimeout(() => { window.location.href = returnUrl; }, 900);
    } catch (e: any) {
      setErr(e.message);
      setStatus("idle");
    }
  }

  return (
    <div className="container" style={{ maxWidth: 420 }}>
      <h1 className="brand">Payonify</h1>
      <p className="muted">Simulated hosted checkout (demo mode — no live gateway).</p>
      <div className="card">
        <div className="muted">Paying</div>
        <div className="stat">${amount}</div>
        <div className="muted">ref {reference}</div>
        <div className="row" style={{ marginTop: 12 }}>
          <button style={{ flex: 1 }} onClick={pay} disabled={status !== "idle"}>
            {status === "idle" ? "Pay with EcoCash" :
              status === "paying" ? "Processing…" : "Paid ✓ redirecting…"}
          </button>
        </div>
        {err && <p style={{ color: "var(--red)" }}>{err}</p>}
      </div>
      <p className="muted" style={{ textAlign: "center" }}>
        With a live <code>sk_live_</code> key this page is Payonify&apos;s real checkout.
      </p>
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<div className="container muted">Loading…</div>}>
      <MockCheckout />
    </Suspense>
  );
}
