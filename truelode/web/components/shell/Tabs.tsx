"use client";
import { useEffect, useState } from "react";

// Active tab synced to the URL hash (#batches) for deep-linking + back-button,
// without useSearchParams (keeps static build clean).
export function useTab(initial: string) {
  const [tab, setTab] = useState(initial);
  useEffect(() => {
    const fromHash = () => {
      const h = globalThis.location?.hash.slice(1);
      if (h) setTab(h);
    };
    fromHash();
    globalThis.addEventListener?.("hashchange", fromHash);
    return () => globalThis.removeEventListener?.("hashchange", fromHash);
  }, []);
  const select = (k: string) => {
    setTab(k);
    if (globalThis.location) globalThis.location.hash = k;
  };
  return [tab, select] as const;
}

export default function Tabs({
  tabs, tab, onSelect,
}: {
  readonly tabs: { key: string; label: string }[];
  readonly tab: string;
  readonly onSelect: (k: string) => void;
}) {
  return (
    <div className="tabs" role="tablist">
      {tabs.map((t) => (
        <button key={t.key} role="tab" aria-selected={t.key === tab} data-demo={`tab-${t.key}`}
          className={`tab ${t.key === tab ? "active" : ""}`} onClick={() => onSelect(t.key)}>
          {t.label}
        </button>
      ))}
    </div>
  );
}
