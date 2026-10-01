"use client";

import { fmtDateTime } from "@/lib/fmt";

type HandoverLink = { from_org?: string | null; to_org?: string | null; accepted_at?: string | null; vehicle_id?: string | null };
type CustodyData = {
  mine?: string | null; transporter?: string | null; processor?: string | null;
  handover_chain?: HandoverLink[];
};

const STEPS: [keyof CustodyData, string][] = [
  ["mine", "Mine"], ["transporter", "Transporter"], ["processor", "Processor"],
];

export default function Custody({ custody }: { readonly custody?: CustodyData }) {
  if (!custody) return null;
  return (
    <div className="card">
      <h3>Custody chain</h3>
      <div className="muted">
        {STEPS.map(([k, label], i) => (
          <span key={k}>
            {i > 0 ? " → " : ""}
            {label}: <b style={{ color: "var(--text)" }}>{(custody[k] as string | null | undefined) ?? "—"}</b>
          </span>
        ))}
      </div>
      {custody.handover_chain && custody.handover_chain.length > 0 && (
        <table style={{ marginTop: 12, fontSize: "0.85em" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left" }}>From</th>
              <th style={{ textAlign: "left" }}>To</th>
              <th style={{ textAlign: "left" }}>Accepted at</th>
            </tr>
          </thead>
          <tbody>
            {custody.handover_chain.map((h, i) => (
              <tr key={i}>
                <td className="muted">{h.from_org ?? "—"}</td>
                <td className="muted">{h.to_org ?? "—"}</td>
                <td className="muted">{fmtDateTime(h.accepted_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
