"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/lib/auth";
import { ROLE_HOME, Role } from "@/lib/config";

export default function Home() {
  const { user, ready } = useAuth();
  const router = useRouter();

  // Logged-in users skip the landing and go straight to their dashboard.
  useEffect(() => {
    if (ready && user) router.replace(ROLE_HOME[user.role as Role] ?? "/login");
  }, [ready, user, router]);

  if (ready && user) return <div className="container muted">Loading…</div>;

  return (
    <>
      <nav className="lp-nav">
        <span className="brand">⛏ TRUELODE</span>
        <span className="spacer" />
        <Link className="ghost" href="/join">Join with a code</Link>
        <Link className="ghost" href="/login">Sign in</Link>
        <Link href="/signup"><button>Get started</button></Link>
      </nav>

      <header className="lp-hero">
        <h1>Prove every gram of <span className="accent">clean lithium</span>.</h1>
        <p>
          Truelode is the chain-of-custody platform for Zimbabwean lithium — weighbridge,
          assay and GPS reconciled at every hop, sealed into a tamper-evident passport
          buyers can verify with a scan.
        </p>
        <div className="lp-cta">
          <Link href="/signup"><button className="btn-lg">Create an account</button></Link>
          <Link href="/join"><button className="ghost btn-lg">Join an organisation</button></Link>
        </div>
      </header>

      <section className="lp-grid">
        {[
          ["⚖️", "Weighbridge reconciliation", "Mine-out vs plant-in matched to tolerance — overloads flag instantly."],
          ["🛰️", "Geofenced transport", "Live GPS against approved corridors; off-route and unknown stops raise alerts."],
          ["🔬", "Lab-grade assays", "Independent labs certify grade; mass balance is checked end to end."],
          ["🔐", "Signed passports", "Every product batch carries an Ed25519-signed, ledger-anchored provenance record."],
        ].map(([ic, h, p]) => (
          <div className="lp-feature" key={h}>
            <div className="ic">{ic}</div>
            <h3>{h}</h3>
            <p className="muted" style={{ margin: 0 }}>{p}</p>
          </div>
        ))}
      </section>

      <section className="lp-tiers">
        <div className="lp-tier">
          <h3>Individual</h3>
          <div className="price">$15<span className="muted" style={{ fontSize: 14 }}> / cycle</span></div>
          <p className="muted" style={{ margin: 0 }}>Solo operators — drivers, miners, lab techs.</p>
          <ul>
            <li>One seat, one role</li>
            <li>Single site</li>
            <li>Issue passports</li>
            <li>Flat fee, unlimited batches</li>
          </ul>
          <Link href="/signup"><button className="ghost" style={{ width: "100%" }}>Start individual</button></Link>
        </div>
        <div className="lp-tier featured">
          <h3>Enterprise <span className="badge green">popular</span></h3>
          <div className="price">$10<span className="muted" style={{ fontSize: 14 }}> / seat + $5 / batch</span></div>
          <p className="muted" style={{ margin: 0 }}>Companies with teams and multiple sites.</p>
          <ul>
            <li>Unlimited staff seats</li>
            <li>Multiple sites</li>
            <li>Team activity dashboard</li>
            <li>Invite codes for your crew</li>
            <li>Pay-as-you-go + priority support</li>
          </ul>
          <Link href="/signup"><button style={{ width: "100%" }}>Start enterprise</button></Link>
        </div>
      </section>

      <footer className="container muted" style={{ textAlign: "center", paddingBottom: 40 }}>
        Already onboard? <Link href="/login">Sign in</Link> · Got a code?{" "}
        <Link href="/join">Join your organisation</Link>
      </footer>
    </>
  );
}
