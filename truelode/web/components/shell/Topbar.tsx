"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { useAuth } from "@/lib/auth";

import Notifications from "./Notifications";

export default function Topbar({
  onOpenPalette, onToggleSidebar,
}: {
  readonly onOpenPalette: () => void;
  readonly onToggleSidebar: () => void;
}) {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [menu, setMenu] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const c = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setMenu(false);
    };
    document.addEventListener("mousedown", c);
    return () => document.removeEventListener("mousedown", c);
  }, []);

  const showBilling = !user?.account?.exempt;
  const showStaff = user?.is_account_owner && !!user?.features?.team;
  const initial = (user?.name || "?").charAt(0).toUpperCase();

  return (
    <header className="topbar">
      <button className="icon-btn" aria-label="Toggle sidebar" onClick={onToggleSidebar}>☰</button>
      <span className="brand">⛏ TRUELODE</span>
      <button className="search-btn" onClick={onOpenPalette} aria-label="Open command palette">
        🔍 Search batches, trips, views… <span className="kbd">⌘K</span>
      </button>
      <Notifications />
      <span className="chip">{user?.role} · {user?.account?.name ?? "personal"}</span>
      <div ref={ref} style={{ position: "relative" }}>
        <button className="avatar" onClick={() => setMenu((m) => !m)} aria-label="Account menu">{initial}</button>
        {menu && (
          <div className="menu">
            <div className="head">{user?.name} · {user?.role}</div>
            <div className="sep" />
            {showBilling && <Link href="/billing">Billing{typeof user?.balance_usd === "number" ? ` · $${user.balance_usd.toFixed(2)}` : ""}</Link>}
            {showStaff && <Link href="/staff">Team</Link>}
            {user?.role === "ADMIN" && <Link href="/admin">Admin</Link>}
            <div className="sep" />
            <button onClick={() => { logout(); router.replace("/login"); }}>Sign out</button>
          </div>
        )}
      </div>
    </header>
  );
}
