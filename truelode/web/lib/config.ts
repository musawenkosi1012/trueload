// Default to the host the page was served from so other LAN devices work with no
// per-device config (phone at http://<ip>:3000 -> API/socket at http://<ip>:5000).
// Falls back to localhost on the server (SSR) and when no window exists.
function defaultBase(): string {
  if (typeof window !== "undefined") {
    return `http://${window.location.hostname}:5000`;
  }
  return "http://localhost:5000";
}

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || defaultBase();
export const SOCKET_URL = process.env.NEXT_PUBLIC_SOCKET_URL || defaultBase();

export const ROLES = [
  "MINE",
  "TRANSPORTER",
  "PROCESSOR",
  "BUYER",
  "REGULATOR",
  "LAB",
  "ADMIN",
] as const;

export type Role = (typeof ROLES)[number];

export const ACCOUNT_TYPES = ["INDIVIDUAL", "ENTERPRISE"] as const;
export type AccountType = (typeof ACCOUNT_TYPES)[number];

// Roles a user may pick during open self-registration. ADMIN (superuser) and
// REGULATOR (billing-exempt oversight) are provisioned by the platform only.
export const SIGNUP_ROLES = ["MINE", "TRANSPORTER", "PROCESSOR", "BUYER", "LAB"] as const;

// Friendly labels for the supply-chain functions shown in signup.
export const ROLE_LABELS: Record<string, { label: string; blurb: string }> = {
  MINE: { label: "Mine", blurb: "Extract ore, weigh out batches at source" },
  TRANSPORTER: { label: "Transporter", blurb: "Haul batches along approved corridors" },
  PROCESSOR: { label: "Processor", blurb: "Refine ore and issue passports" },
  BUYER: { label: "Buyer", blurb: "Purchase product and verify provenance" },
  LAB: { label: "Lab", blurb: "Assay grade and certify samples" },
};

export const ROLE_HOME: Record<Role, string> = {
  MINE: "/mine",
  TRANSPORTER: "/transporter",
  PROCESSOR: "/processor",
  BUYER: "/buyer",
  REGULATOR: "/regulator",
  LAB: "/lab",
  ADMIN: "/admin",
};
