"use client";
import { useEffect, useState } from "react";

import { fetchPassport } from "@/lib/passport";

type State = "loading" | "ok" | "caution" | "fail" | "none";

export default function VerifiedBadge({ token }: { readonly token?: string }) {
  const [state, setState] = useState<State>("loading");
  const [flags, setFlags] = useState(0);

  useEffect(() => {
    if (!token) { setState("none"); return; }
    let alive = true;
    fetchPassport(token).then((r) => {
      if (!alive) return;
      if (r.error || !r.data) { setState(r.error?.includes("not found") ? "none" : "fail"); return; }
      const d = r.data;
      const open = (d.passport.snapshot.anomalies ?? []).filter((f: any) => f.status === "OPEN").length;
      setFlags(open);
      setState(!(d.signature_valid && d.ledger_intact) ? "fail" : open > 0 ? "caution" : "ok");
    });
    return () => { alive = false; };
  }, [token]);

  if (state === "loading") return <span className="muted">…</span>;
  if (state === "none") return <span className="muted">no passport</span>;
  const map = {
    ok: ["green", "✓ verified"], caution: ["amber", `⚠ ${flags} flag(s)`], fail: ["red", "✗ failed"],
  } as const;
  const [cls, text] = map[state];
  return <span className={`badge ${cls}`}>{text}</span>;
}
