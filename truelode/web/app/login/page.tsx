"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/lib/auth";
import { ROLE_HOME, Role } from "@/lib/config";

const DEMO = ["MINE", "TRANSPORTER", "PROCESSOR", "BUYER", "REGULATOR", "LAB", "ADMIN"];

export default function Login() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("mine@truelode.test");
  const [password, setPassword] = useState("password");
  const [err, setErr] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    try {
      const u = await login(email, password);
      router.replace(ROLE_HOME[u.role as Role] ?? "/");
    } catch (e: any) {
      setErr(e.message);
    }
  }

  return (
    <div className="container" style={{ maxWidth: 420 }}>
      <h1 className="brand">⛏ TRUELODE</h1>
      <p className="muted">Chain of custody for clean Zimbabwean lithium.</p>
      <form className="card" onSubmit={submit}>
        <label>Email</label>
        <input data-demo="email" value={email} onChange={(e) => setEmail(e.target.value)} style={{ width: "100%" }} />
        <label>Password</label>
        <input data-demo="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} style={{ width: "100%" }} />
        {err && <p style={{ color: "var(--red)" }}>{err}</p>}
        <button data-demo="signin" style={{ marginTop: 14, width: "100%" }}>Sign in</button>
      </form>
      <p className="muted" style={{ textAlign: "center", marginTop: 12 }}>
        No account?{" "}
        <a href="/signup" style={{ color: "var(--green)" }}>Create one</a>
        {"  ·  "}
        <a href="/join" style={{ color: "var(--green)" }}>Join with a code</a>
      </p>
      <div className="card">
        <div className="muted">Demo logins (password: <b>password</b>)</div>
        <div className="row" style={{ marginTop: 8 }}>
          {DEMO.map((r) => (
            <button key={r} data-demo={`chip-${r.toLowerCase()}`} className="ghost"
              onClick={() => setEmail(`${r.toLowerCase()}@truelode.test`)}>{r}</button>
          ))}
        </div>
      </div>
    </div>
  );
}
