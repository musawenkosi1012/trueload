"use client";
import { useState } from "react";

import { post } from "@/lib/api";
import { ACCOUNT_TYPES, ROLES } from "@/lib/config";

const BLANK = { name: "", account_type: "ENTERPRISE", primary_role: "MINE" };

export default function NewAccountForm({ onCreated }: { readonly onCreated: () => void }) {
  const [f, setF] = useState(BLANK);
  const [err, setErr] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    try { await post("/api/accounts", f); setF(BLANK); onCreated(); }
    catch (e: any) { setErr(e.message); }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h3>New account</h3>
      <div className="row">
        <div><label>Name</label>
          <input value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></div>
        <div><label>Type</label>
          <select value={f.account_type} onChange={(e) => setF({ ...f, account_type: e.target.value })}>
            {ACCOUNT_TYPES.map((t) => <option key={t}>{t}</option>)}</select></div>
        <div><label>Primary role</label>
          <select value={f.primary_role} onChange={(e) => setF({ ...f, primary_role: e.target.value })}>
            {ROLES.map((r) => <option key={r}>{r}</option>)}</select></div>
        <button disabled={!f.name}>Create</button>
      </div>
      {err && <p style={{ color: "var(--red)" }}>{err}</p>}
    </form>
  );
}
