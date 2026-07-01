"use client";

type Node = {
  code: string; stage: string; net_weight_kg: number; grade_pct?: number;
  origin?: { name: string } | null; parents?: Node[];
};

export default function Lineage({ nodes }: { nodes: Node[] }) {
  return (
    <div style={{ borderLeft: "2px solid var(--line)", paddingLeft: 14, marginLeft: 6 }}>
      {nodes.map((n, i) => (
        <div key={i} style={{ marginBottom: 12 }}>
          <div>
            <span className="badge green">{n.stage}</span>{" "}
            <b>{n.code}</b>{" "}
            <span className="muted">
              {(n.net_weight_kg / 1000).toFixed(2)} t
              {n.grade_pct ? ` · ${n.grade_pct}% Li₂O` : ""}
              {n.origin ? ` · ${n.origin.name}` : ""}
            </span>
          </div>
          {n.parents && n.parents.length > 0 && <Lineage nodes={n.parents} />}
        </div>
      ))}
    </div>
  );
}
