const DT = new Intl.DateTimeFormat("en-GB", {
  day: "2-digit", month: "short", year: "numeric",
  hour: "2-digit", minute: "2-digit",
});

/** "27 Sep 2026, 16:53" — reads naturally for a Zimbabwean audience. */
export function fmtDateTime(iso?: string | null): string {
  const d = iso ? new Date(iso) : null;
  return d && !isNaN(d.getTime()) ? DT.format(d) : "—";
}
