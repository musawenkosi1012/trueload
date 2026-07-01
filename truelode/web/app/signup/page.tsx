"use client";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { get } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { ROLE_HOME, ROLE_LABELS, SIGNUP_ROLES, Role } from "@/lib/config";

type AccountType = "INDIVIDUAL" | "ENTERPRISE";

const TIER_PERKS: Record<AccountType, string[]> = {
  INDIVIDUAL: ["Solo operator (1 seat)", "1 site", "Issue passports",
               "Flat monthly fee, unlimited batches"],
  ENTERPRISE: ["Unlimited staff seats", "Multiple sites", "Issue passports",
               "Pay-as-you-go per batch", "Team activity dashboard", "Priority support"],
};
type Plan = {
  plan_type: string;
  flat_fee_usd: number;
  seat_fee_usd: number;
  per_batch_fee_usd: number;
  currency: string;
};

export default function Signup() {
  const { signup } = useAuth();
  const router = useRouter();

  const [accountType, setAccountType] = useState<AccountType>("ENTERPRISE");
  const [role, setRole] = useState<Role>("MINE");
  const [accountName, setAccountName] = useState("");
  const [country, setCountry] = useState("Zimbabwe");

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");

  const [plans, setPlans] = useState<Plan[]>([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    get<Plan[]>("/api/billing/plans").then(setPlans).catch(() => {});
  }, []);

  const plan = useMemo(() => {
    const want = accountType === "ENTERPRISE" ? "ORG" : "INDIVIDUAL_FLAT";
    return plans.find((p) => p.plan_type === want);
  }, [plans, accountType]);

  // Validation
  const pwTooShort = password.length > 0 && password.length < 6;
  const pwMismatch = confirm.length > 0 && confirm !== password;
  const orgNameMissing = accountType === "ENTERPRISE" && !accountName.trim();
  const valid =
    name.trim() && email.trim() && password.length >= 6 &&
    confirm === password && !orgNameMissing;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    if (!valid) return;
    setLoading(true);
    try {
      const u = await signup({
        email: email.trim(),
        name: name.trim(),
        password,
        role,
        account_type: accountType,
        account_name: accountType === "ENTERPRISE" ? accountName.trim() : undefined,
      });
      router.replace(ROLE_HOME[u.role as Role] ?? "/");
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  const isOrg = accountType === "ENTERPRISE";
  const cur = plan?.currency ?? "USD";

  return (
    <div className="auth">
      <h1 className="brand">⛏ TRUELODE</h1>
      <p className="muted">Create your account and start tracking custody.</p>

      <form onSubmit={submit}>
        {/* Account type */}
        <div className="seg">
          {(["INDIVIDUAL", "ENTERPRISE"] as AccountType[]).map((t) => (
            <button key={t} type="button" className={accountType === t ? "on" : ""}
              onClick={() => setAccountType(t)}>
              {t === "INDIVIDUAL" ? "Individual" : "Enterprise"}
            </button>
          ))}
        </div>
        <p className="muted" style={{ marginTop: 8 }}>
          {isOrg
            ? "A company with staff. You become the owner — invite your team and pay per active seat plus per batch created."
            : "A single operator. One flat fee, unlimited use."}
        </p>

        {/* What this tier unlocks */}
        <ul style={{ margin: "8px 0 0", paddingLeft: 18 }}>
          {TIER_PERKS[accountType].map((p) => (
            <li key={p} className="muted" style={{ marginBottom: 2 }}>{p}</li>
          ))}
        </ul>

        {/* Enterprise details (enterprise only) */}
        {isOrg && (
          <div className="section">
            <div className="head"><span className="step">1</span><h3>Your organisation</h3></div>
            <div className="fields">
              <div>
                <label>Organisation name</label>
                <input value={accountName} onChange={(e) => setAccountName(e.target.value)}
                  placeholder="e.g. Bikita Minerals (Pvt) Ltd" required />
              </div>
              <div className="fields two">
                <div>
                  <label>Function in the supply chain</label>
                  <select value={role} onChange={(e) => setRole(e.target.value as Role)}>
                    {SIGNUP_ROLES.map((r) => (
                      <option key={r} value={r}>{ROLE_LABELS[r].label}</option>
                    ))}
                  </select>
                  <div className="hint">{ROLE_LABELS[role]?.blurb}</div>
                </div>
                <div>
                  <label>Country</label>
                  <input value={country} onChange={(e) => setCountry(e.target.value)} />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Owner / individual login */}
        <div className="section">
          <div className="head">
            <span className="step">{isOrg ? "2" : "1"}</span>
            <h3>{isOrg ? "Owner login" : "Your details"}</h3>
          </div>
          <div className="fields">
            {!isOrg && (
              <div>
                <label>Function</label>
                <select value={role} onChange={(e) => setRole(e.target.value as Role)}>
                  {SIGNUP_ROLES.map((r) => (
                    <option key={r} value={r}>{ROLE_LABELS[r].label}</option>
                  ))}
                </select>
                <div className="hint">{ROLE_LABELS[role]?.blurb}</div>
              </div>
            )}
            <div className="fields two">
              <div>
                <label>Full name</label>
                <input value={name} onChange={(e) => setName(e.target.value)}
                  placeholder="Musa Ngulube" required />
              </div>
              <div>
                <label>Work email</label>
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com" required />
              </div>
            </div>
            <div className="fields two">
              <div>
                <label>Password</label>
                <input type="password" value={password}
                  onChange={(e) => setPassword(e.target.value)} placeholder="min 6 characters" required />
                {pwTooShort && <div className="hint bad">At least 6 characters.</div>}
              </div>
              <div>
                <label>Confirm password</label>
                <input type="password" value={confirm}
                  onChange={(e) => setConfirm(e.target.value)} placeholder="re-enter password" required />
                {pwMismatch && <div className="hint bad">Passwords don&apos;t match.</div>}
              </div>
            </div>
          </div>
        </div>

        {/* Live plan summary */}
        <div className="price">
          <div className="muted" style={{ marginBottom: 4 }}>
            {isOrg ? "Enterprise — pay as you go" : "Individual — flat plan"}
          </div>
          {isOrg ? (
            <>
              <div className="line"><span>Per active staff seat</span>
                <b>{cur} {plan?.seat_fee_usd ?? 10} <span className="muted">/ cycle</span></b></div>
              <div className="line"><span>Per batch created</span>
                <b>{cur} {plan?.per_batch_fee_usd ?? 5}</b></div>
              <div className="line total muted">
                <span>Wallet starts at {cur} 0 — top up any time on the Billing page.</span></div>
            </>
          ) : (
            <div className="line"><span>Flat subscription</span>
              <b>{cur} {plan?.flat_fee_usd ?? 15} <span className="muted">/ cycle</span></b></div>
          )}
        </div>

        {err && <p style={{ color: "var(--red)" }}>{err}</p>}
        <button style={{ width: "100%", padding: 12 }} disabled={loading || !valid}>
          {loading ? "Creating account…"
            : isOrg ? "Create enterprise account" : "Create account"}
        </button>
      </form>

      <p className="muted" style={{ textAlign: "center", marginTop: 14 }}>
        Already have an account? <a href="/login">Sign in</a>
      </p>
    </div>
  );
}
