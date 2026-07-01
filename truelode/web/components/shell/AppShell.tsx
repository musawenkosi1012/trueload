"use client";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/lib/auth";
import { subscribe } from "@/lib/socket";

import CommandPalette from "./CommandPalette";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

export default function AppShell({
  role, children,
}: {
  readonly role?: string;
  readonly children: React.ReactNode;
}) {
  const { user, ready, refresh } = useAuth();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const [palette, setPalette] = useState(false);

  useEffect(() => {
    if (!ready) return;
    if (!user) { router.replace("/login"); return; }
    subscribe(user.role, user.account_id);
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, user?.id]);

  useEffect(() => {
    const k = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPalette((p) => !p);
      }
    };
    document.addEventListener("keydown", k);
    return () => document.removeEventListener("keydown", k);
  }, []);

  if (!ready) return <div className="container muted">Loading…</div>;
  if (!user) return null;
  if (role && user.role !== role && user.role !== "ADMIN") {
    return (
      <div className="container">
        <div className="card">This dashboard is for {role}. You are {user.role}.</div>
      </div>
    );
  }

  const navRole = role ?? user.role;
  const delinquent = user.account_status === "DELINQUENT";

  return (
    <div className="app">
      <Topbar onOpenPalette={() => setPalette(true)} onToggleSidebar={() => setCollapsed((c) => !c)} />
      <Sidebar role={navRole} collapsed={collapsed} />
      <main className={`content ${collapsed ? "wide" : ""}`}>
        <div className="inner">
          {delinquent && (
            <div className="card" style={{ borderColor: "var(--red)", color: "var(--red)" }}>
              Account past due — top up on the Billing page to create batches.
            </div>
          )}
          {children}
        </div>
      </main>
      <CommandPalette open={palette} onClose={() => setPalette(false)} role={navRole} />
    </div>
  );
}
