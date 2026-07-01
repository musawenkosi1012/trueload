// Humanise ledger event types and timestamps for the Team activity views.

export const EVENT_LABELS: Record<string, string> = {
  LOAD_TICKET_CREATED: "Created batch",
  WEIGH_RECORDED: "Recorded weigh",
  ASSAY_RECORDED: "Recorded assay",
  PROCESSING_STEP: "Processed batch",
  FLAG_RAISED: "Raised flag",
  FLAG_CLEARED: "Cleared flag",
  PASSPORT_ISSUED: "Issued passport",
  GPS_INGESTED: "Logged GPS",
};

export function eventLabel(type: string): string {
  return EVENT_LABELS[type] ?? type.replace(/_/g, " ").toLowerCase();
}

export function relativeTime(iso: string | null | undefined): string {
  if (!iso) return "never";
  // SQLite stores naive UTC; if no timezone offset is present, treat it as UTC.
  const hasTz = /[zZ]|[+-]\d{2}:?\d{2}$/.test(iso);
  const then = new Date(hasTz ? iso : iso + "Z").getTime();
  const diff = Date.now() - then;
  if (diff < 0) return "just now";
  const min = Math.floor(diff / 60000);
  if (min < 1) return "just now";
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const day = Math.floor(hr / 24);
  if (day < 30) return `${day}d ago`;
  return new Date(iso).toLocaleDateString();
}
