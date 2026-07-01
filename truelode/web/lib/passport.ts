import { API_BASE } from "./config";

export type VerifyResult = { data?: any; error?: string };

// Shared by the server page (SSR + OG metadata) and the client view (fallback
// fetch + retry). API_BASE resolves to localhost on the server, window-host in
// the browser — see lib/config.ts.
export async function fetchPassport(token: string): Promise<VerifyResult> {
  try {
    const r = await fetch(`${API_BASE}/api/verify/${token}`, { cache: "no-store" });
    const d = await r.json();
    if (d.error) return { error: d.error };
    return { data: d };
  } catch (e) {
    return { error: String(e) };
  }
}
