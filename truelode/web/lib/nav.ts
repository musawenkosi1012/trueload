// Single source of truth for role-aware navigation — drives the sidebar and the
// command palette. `href` = a real route (cross-role); otherwise `key` is an
// in-page tab synced to the URL hash.
export type NavItem = { key: string; label: string; icon: string; href?: string };

export const NAV: Record<string, NavItem[]> = {
  MINE: [
    { key: "overview", label: "Overview", icon: "▦" },
    { key: "ticket", label: "Load ticket", icon: "⛏" },
    { key: "batches", label: "Batches", icon: "▣" },
  ],
  TRANSPORTER: [
    { key: "trips", label: "Trips", icon: "◎" },
    { key: "alerts", label: "Alerts", icon: "⚑" },
  ],
  PROCESSOR: [
    { key: "overview", label: "Overview", icon: "▦" },
    { key: "process", label: "Process", icon: "⚗" },
    { key: "batches", label: "Batches", icon: "▣" },
    { key: "alerts", label: "Alerts", icon: "⚑" },
  ],
  BUYER: [
    { key: "products", label: "Products", icon: "▣" },
    { key: "verify", label: "Verify", icon: "✓" },
  ],
  REGULATOR: [
    { key: "overview", label: "Overview", icon: "▦" },
    { key: "map", label: "Map", icon: "◍" },
    { key: "alerts", label: "Alerts", icon: "⚑" },
    { key: "ledger", label: "Ledger", icon: "⛓" },
  ],
  LAB: [
    { key: "samples", label: "Samples", icon: "⚗" },
  ],
  ADMIN: [
    { key: "overview", label: "Overview", icon: "▦" },
    { key: "accounts", label: "Accounts", icon: "◔" },
    { key: "registry", label: "Registry", icon: "▤" },
  ],
};

export function navFor(role?: string): NavItem[] {
  return (role && NAV[role]) || [];
}
