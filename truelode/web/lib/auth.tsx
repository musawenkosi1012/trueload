"use client";
import { createContext, useContext, useEffect, useState } from "react";

import { post } from "./api";

export type Account = {
  id: string;
  name: string;
  account_type: string;
  primary_role: string;
  status: string;
  exempt: boolean;
};

export type User = {
  id: string;
  name: string;
  role: string;
  account_id: string | null;
  is_account_owner: boolean;
  account_type?: string;
  account_status?: string;
  balance_usd?: number;
  account?: Account;
  features?: Record<string, boolean>;
};

export type SignupPayload = {
  email: string;
  name: string;
  password: string;
  role: string;
  account_type: "INDIVIDUAL" | "ENTERPRISE";
  account_name?: string;
};

type AuthCtx = {
  user: User | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<User>;
  signup: (payload: SignupPayload) => Promise<User>;
  join: (payload: { name: string; email: string; password: string; code: string }) => Promise<User>;
  refresh: () => Promise<void>;
  logout: () => void;
};

const Ctx = createContext<AuthCtx>({} as AuthCtx);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const raw = localStorage.getItem("tl_user");
    if (raw) setUser(JSON.parse(raw));
    setReady(true);
  }, []);

  function persist(u: User) {
    localStorage.setItem("tl_user", JSON.stringify(u));
    setUser(u);
  }

  async function login(email: string, password: string) {
    const res = await post<{ token: string; user: User }>("/api/auth/login", {
      email,
      password,
    });
    localStorage.setItem("tl_token", res.token);
    persist(res.user);
    return res.user;
  }

  async function signup(payload: SignupPayload) {
    const res = await post<{ token: string; user: User }>("/api/auth/register", payload);
    localStorage.setItem("tl_token", res.token);
    persist(res.user);
    return res.user;
  }

  async function join(payload: { name: string; email: string; password: string; code: string }) {
    const res = await post<{ token: string; user: User }>("/api/auth/join", payload);
    localStorage.setItem("tl_token", res.token);
    persist(res.user);
    return res.user;
  }

  async function refresh() {
    const { get } = await import("./api");
    try {
      const u = await get<User>("/api/auth/me");
      if (u && u.id) persist(u);
    } catch {
      /* ignore */
    }
  }

  function logout() {
    localStorage.removeItem("tl_token");
    localStorage.removeItem("tl_user");
    setUser(null);
  }

  return (
    <Ctx.Provider value={{ user, ready, login, signup, join, refresh, logout }}>
      {children}
    </Ctx.Provider>
  );
}

export const useAuth = () => useContext(Ctx);
