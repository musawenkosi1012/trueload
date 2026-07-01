"use client";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { get } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { ROLE_HOME, Role } from "@/lib/config";

type Preview = { valid: boolean; code: string; role: string; organisation: string };

function JoinForm() {
  const { join } = useAuth();
  const router = useRouter();
  const params = useSearchParams();

  const [code, setCode] = useState(params.get("code") ?? "");
  const [preview, setPreview] = useState<Preview | null>(null);
  const [checking, setChecking] = useState(false);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  // Look up the org/role a code grants whenever the code looks complete.
  useEffect(() => {
    const c = code.trim().toUpperCase();
    setErr("");
    if (c.length < 6) { setPreview(null); return; }
    setChecking(true);
    get<Preview>(`/api/auth/invite/${c}`)
      .then((p) => setPreview(p))
      .catch(() => setPreview(null))
      .finally(() => setChecking(false));
  }, [code]);

  const pwTooShort = password.length > 0 && password.length < 6;
  const pwMismatch = confirm.length > 0 && confirm !== password;
  const valid = preview?.valid && name.trim() && email.trim()
    && password.length >= 6 && confirm === password;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    if (!valid) return;
    setLoading(true);
    try {
      const u = await join({ name: name.trim(), email: email.trim(), password,
                             code: code.trim().toUpperCase() });
      router.replace(ROLE_HOME[u.role as Role] ?? "/");
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth">
      <h1 className="brand">⛏ TRUELODE</h1>
      <p className="muted">Join your organisation with the code they gave you.</p>

      <form onSubmit={submit}>
        <div className="section">
          <div className="head"><span className="step">1</span><h3>Invite code</h3></div>
          <input value={code} onChange={(e) => setCode(e.target.value.toUpperCase())}
            placeholder="TL-XXXXXX" style={{ width: "100%", letterSpacing: 1 }} />
          {checking && <div className="hint">Checking…</div>}
          {preview?.valid && (
            <div className="hint" style={{ color: "var(--green)" }}>
              ✓ Joining <b>{preview.organisation}</b> as <b>{preview.role}</b>
            </div>
          )}
          {!checking && code.trim().length >= 6 && !preview && (
            <div className="hint bad">Invalid or revoked code.</div>
          )}
        </div>

        <div className="section">
          <div className="head"><span className="step">2</span><h3>Your details</h3></div>
          <div className="fields">
            <div className="fields two">
              <div><label>Full name</label>
                <input value={name} onChange={(e) => setName(e.target.value)} required /></div>
              <div><label>Work email</label>
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></div>
            </div>
            <div className="fields two">
              <div><label>Password</label>
                <input type="password" value={password}
                  onChange={(e) => setPassword(e.target.value)} placeholder="min 6 characters" required />
                {pwTooShort && <div className="hint bad">At least 6 characters.</div>}</div>
              <div><label>Confirm password</label>
                <input type="password" value={confirm}
                  onChange={(e) => setConfirm(e.target.value)} required />
                {pwMismatch && <div className="hint bad">Passwords don&apos;t match.</div>}</div>
            </div>
          </div>
        </div>

        {err && <p style={{ color: "var(--red)" }}>{err}</p>}
        <button style={{ width: "100%", padding: 12 }} disabled={loading || !valid}>
          {loading ? "Joining…" : "Join organisation"}
        </button>
      </form>

      <p className="muted" style={{ textAlign: "center", marginTop: 14 }}>
        Want your own account instead? <a href="/signup">Sign up</a>
      </p>
    </div>
  );
}

export default function JoinPage() {
  return (
    <Suspense fallback={<div className="container muted">Loading…</div>}>
      <JoinForm />
    </Suspense>
  );
}
