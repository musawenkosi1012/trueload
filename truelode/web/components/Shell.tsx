"use client";
import AppShell from "./shell/AppShell";

// Thin wrapper: every page that used <Shell role> now gets the full GitHub-style
// app shell (topbar + sidebar + command palette) via AppShell.
export default function Shell({
  role, children,
}: {
  readonly role?: string;
  readonly children: React.ReactNode;
}) {
  return <AppShell role={role}>{children}</AppShell>;
}
