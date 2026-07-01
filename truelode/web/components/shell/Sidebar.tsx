"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/lib/auth";
import { navFor } from "@/lib/nav";

export default function Sidebar({
  role, collapsed,
}: {
  readonly role?: string;
  readonly collapsed: boolean;
}) {
  const { user } = useAuth();
  const pathname = usePathname();
  const [hash, setHash] = useState("");

  useEffect(() => {
    const f = () => setHash(globalThis.location?.hash.slice(1) || "");
    f();
    globalThis.addEventListener?.("hashchange", f);
    return () => globalThis.removeEventListener?.("hashchange", f);
  }, []);

  const items = navFor(role);
  const showStaff = user?.is_account_owner && !!user?.features?.team;

  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      {items.map((it, idx) => {
        const active = it.href ? pathname === it.href : (hash ? hash === it.key : idx === 0);
        return (
          <a key={it.key} href={it.href ?? `#${it.key}`}
            className={`sidebar-item ${active ? "active" : ""}`} title={it.label}>
            <span className="ic">{it.icon}</span><span>{it.label}</span>
          </a>
        );
      })}
      <div className="grow" />
      <div className="sb-sep" />
      {!user?.account?.exempt && (
        <Link href="/billing" className="sidebar-item" title="Billing">
          <span className="ic">$</span><span>Billing</span></Link>
      )}
      {showStaff && (
        <Link href="/staff" className="sidebar-item" title="Team">
          <span className="ic">◍</span><span>Team</span></Link>
      )}
      {user?.role === "ADMIN" && (
        <Link href="/admin" className="sidebar-item" title="Admin">
          <span className="ic">⚙</span><span>Admin</span></Link>
      )}
    </aside>
  );
}
