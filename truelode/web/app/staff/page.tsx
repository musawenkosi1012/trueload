"use client";
import { Fragment, useEffect, useState } from "react";

import Shell from "@/components/Shell";
import { del, get, patch, post } from "@/lib/api";
import { eventLabel, relativeTime } from "@/lib/activity";
import { ROLES, Role } from "@/lib/config";

type Staff = {
  id: string; name: string; email: string; role: string;
  is_account_owner: boolean; active: boolean; last_login_at: string | null;
  event_count: number; last_event: { event_type: string; ts: string } | null;
};
type Activity = { seq: number; event_type: string; ts: string; payload: any };
type Invite = { id: string; code: string; role: string; active: boolean; uses: number };

export default function TeamPage() {
  const [staff, setStaff] = useState<Staff[]>([]);
  const [form, setForm] = useState({ name: "", email: "", role: "MINE" as Role, password: "" });
  const [err, setErr] = useState("");

  const [openId, setOpenId] = useState<string | null>(null);
  const [activity, setActivity] = useState<Activity[]>([]);
  const [resetId, setResetId] = useState<string | null>(null);
  const [resetPw, setResetPw] = useState("");
  const [notice, setNotice] = useState("");

  const [invites, setInvites] = useState<Invite[]>([]);
  const [inviteRole, setInviteRole] = useState<Role>("TRANSPORTER");
  const [copied, setCopied] = useState("");

  function load() {
    get<Staff[]>("/api/staff").then(setStaff).catch((e) => setErr(e.message));
    get<Invite[]>("/api/staff/invites").then(setInvites).catch(() => {});
  }
  useEffect(load, []);

  async function genInvite() {
    setErr("");
    try { await post("/api/staff/invites", { role: inviteRole }); load(); }
    catch (e: any) { setErr(e.message); }
  }
  async function revokeInvite(id: string) {
    await post(`/api/staff/invites/${id}/revoke`, {});
    load();
  }
  function copyCode(code: string) {
    const link = `${window.location.origin}/join?code=${code}`;
    navigator.clipboard?.writeText(link);
    setCopied(code);
    setTimeout(() => setCopied(""), 1500);
  }

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    try {
      await post("/api/staff", form);
      setForm({ name: "", email: "", role: "MINE", password: "" });
      load();
    } catch (e: any) { setErr(e.message); }
  }

  async function changeRole(id: string, role: string) {
    await patch(`/api/staff/${id}`, { role });
    load();
  }
  async function setActive(id: string, active: boolean) {
    if (active) await patch(`/api/staff/${id}`, { active: true });
    else await del(`/api/staff/${id}`);
    load();
  }
  async function viewActivity(id: string) {
    if (openId === id) { setOpenId(null); return; }
    setOpenId(id);
    setActivity(await get<Activity[]>(`/api/staff/${id}/activity`));
  }
  async function submitReset(id: string) {
    setNotice("");
    try {
      await post(`/api/staff/${id}/reset-password`, { password: resetPw });
      setResetId(null); setResetPw("");
      setNotice("Password reset.");
    } catch (e: any) { setErr(e.message); }
  }

  const activeSeats = staff.filter((s) => s.active).length;
  const recentlyActive = staff.filter(
    (s) => s.last_login_at && Date.now() - new Date(s.last_login_at).getTime() < 86400000
  ).length;

  return (
    <Shell>
      <h2>Team</h2>
      <p className="muted">Manage your team&apos;s users and watch their activity.</p>

      <div className="grid">
        <div className="card"><div className="muted">Members</div><div className="stat">{staff.length}</div></div>
        <div className="card"><div className="muted">Active seats (billable)</div><div className="stat">{activeSeats}</div></div>
        <div className="card"><div className="muted">Active in last 24h</div><div className="stat">{recentlyActive}</div></div>
      </div>

      {notice && <div className="card" style={{ color: "var(--green)" }}>{notice}</div>}

      <form className="card" onSubmit={add}>
        <div className="head" style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
          <h3 style={{ margin: "0 0 6px" }}>Add a team member</h3>
        </div>
        <div className="row">
          <div><label>Name</label>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
          <div><label>Email</label>
            <input type="email" value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })} required /></div>
          <div><label>Role</label>
            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as Role })}>
              {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
            </select></div>
          <div><label>Temp password</label>
            <input type="password" value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })} required /></div>
          <button>Add member</button>
        </div>
        {err && <p style={{ color: "var(--red)" }}>{err}</p>}
      </form>

      <div className="card">
        <div className="head" style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
          <h3 style={{ margin: "0 0 4px" }}>Invite codes</h3>
        </div>
        <p className="muted" style={{ marginTop: 0 }}>
          Share a code so people join your organisation themselves — they inherit the role
          you pick. Reusable until you revoke it.
        </p>
        <div className="row">
          <div><label>Role for this code</label>
            <select value={inviteRole} onChange={(e) => setInviteRole(e.target.value as Role)}>
              {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
            </select></div>
          <button type="button" onClick={genInvite}>Generate code</button>
        </div>
        <table style={{ marginTop: 12 }}>
          <tbody>
            {invites.filter((i) => i.active).length === 0 && (
              <tr><td className="muted">No active codes. Generate one above.</td></tr>
            )}
            {invites.filter((i) => i.active).map((i) => (
              <tr key={i.id}>
                <td><b style={{ letterSpacing: 1 }}>{i.code}</b></td>
                <td><span className="badge green">{i.role}</span></td>
                <td className="muted">{i.uses} joined</td>
                <td>
                  <div className="row" style={{ gap: 6 }}>
                    <button className="ghost" type="button" onClick={() => copyCode(i.code)}>
                      {copied === i.code ? "Copied link ✓" : "Copy link"}
                    </button>
                    <button className="ghost" type="button" onClick={() => revokeInvite(i.id)}>Revoke</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <table>
          <thead>
            <tr><th>Member</th><th>Role</th><th>Status</th><th>Last login</th>
              <th>Actions</th><th>Last activity</th><th></th></tr>
          </thead>
          <tbody>
            {staff.map((s) => (
              <Fragment key={s.id}>
                <tr>
                  <td>
                    {s.name || "—"}
                    {s.is_account_owner && <span className="badge green" style={{ marginLeft: 6 }}>owner</span>}
                    <div className="muted">{s.email}</div>
                  </td>
                  <td>
                    {s.is_account_owner ? s.role : (
                      <select value={s.role} onChange={(e) => changeRole(s.id, e.target.value)}>
                        {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                      </select>
                    )}
                  </td>
                  <td><span className={`badge ${s.active ? "green" : "red"}`}>{s.active ? "active" : "inactive"}</span></td>
                  <td className="muted">{relativeTime(s.last_login_at)}</td>
                  <td>{s.event_count}</td>
                  <td className="muted">
                    {s.last_event ? `${eventLabel(s.last_event.event_type)} · ${relativeTime(s.last_event.ts)}` : "—"}
                  </td>
                  <td>
                    <div className="row" style={{ gap: 6 }}>
                      <button className="ghost" onClick={() => viewActivity(s.id)}>
                        {openId === s.id ? "Hide" : "Activity"}
                      </button>
                      <button className="ghost" onClick={() => { setResetId(s.id); setResetPw(""); }}>Reset pw</button>
                      {!s.is_account_owner && (
                        <button className="ghost" onClick={() => setActive(s.id, !s.active)}>
                          {s.active ? "Deactivate" : "Reactivate"}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
                {resetId === s.id && (
                  <tr>
                    <td colSpan={7}>
                      <div className="row" style={{ alignItems: "flex-end" }}>
                        <div><label>New password for {s.email}</label>
                          <input type="password" value={resetPw}
                            onChange={(e) => setResetPw(e.target.value)} placeholder="min 6 characters" /></div>
                        <button onClick={() => submitReset(s.id)} disabled={resetPw.length < 6}>Set password</button>
                        <button className="ghost" onClick={() => setResetId(null)}>Cancel</button>
                      </div>
                    </td>
                  </tr>
                )}
                {openId === s.id && (
                  <tr>
                    <td colSpan={7}>
                      <div className="muted" style={{ marginBottom: 6 }}>Recent activity</div>
                      {activity.length === 0 && <div className="muted">No recorded actions yet.</div>}
                      {activity.map((a) => (
                        <div key={a.seq} style={{ display: "flex", gap: 10, padding: "3px 0" }}>
                          <span className="badge green">{eventLabel(a.event_type)}</span>
                          <span className="muted">{relativeTime(a.ts)}</span>
                          <span className="muted">
                            {a.payload?.batch_code || a.payload?.child || a.payload?.batch_id || ""}
                          </span>
                        </div>
                      ))}
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </Shell>
  );
}
