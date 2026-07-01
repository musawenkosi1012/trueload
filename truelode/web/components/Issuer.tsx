"use client";

type IssuerInfo = { name: string; org?: string | null };

export default function Issuer({
  issuer, issuedAt,
}: {
  readonly issuer?: IssuerInfo | null;
  readonly issuedAt?: string;
}) {
  if (!issuer && !issuedAt) return null;
  const when = issuedAt ? new Date(issuedAt).toLocaleString() : "—";
  return (
    <div className="card">
      <h3>Issued by</h3>
      <div className="muted">
        {issuer ? (
          <>
            <b style={{ color: "var(--text)" }}>{issuer.name}</b>
            {issuer.org ? ` · ${issuer.org}` : ""}
          </>
        ) : (
          "Unknown issuer"
        )}
        {" · "}{when}
      </div>
    </div>
  );
}
