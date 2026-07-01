"use client";
import { API_BASE } from "./config";

function token(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("tl_token");
}

export async function api<T = any>(
  path: string,
  opts: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(opts.headers as Record<string, string>),
  };
  const t = token();
  if (t) headers.Authorization = `Bearer ${t}`;

  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `${res.status} ${res.statusText}`);
  }
  return res.json();
}

export const get = <T = any>(p: string) => api<T>(p);
export const post = <T = any>(p: string, body: unknown) =>
  api<T>(p, { method: "POST", body: JSON.stringify(body) });
export const patch = <T = any>(p: string, body: unknown) =>
  api<T>(p, { method: "PATCH", body: JSON.stringify(body) });
export const del = <T = any>(p: string) => api<T>(p, { method: "DELETE" });
