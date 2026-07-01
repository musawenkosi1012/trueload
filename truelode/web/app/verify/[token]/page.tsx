import type { Metadata } from "next";

import PassportView from "@/components/PassportView";
import { fetchPassport } from "@/lib/passport";

type Props = { params: Promise<{ token: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { token } = await params;
  const { data } = await fetchPassport(token);
  const snap = data?.passport?.snapshot;
  const code = snap?.final_batch?.code;
  const verified = data?.signature_valid && data?.ledger_intact;
  const title = code ? `Truelode Passport — ${code}` : "Truelode Battery Passport";
  const description = snap
    ? `${snap.unit_count ?? ""} ${snap.unit_label ?? "units"} · ${snap.final_batch?.grade_pct ?? "?"}% Li₂O · ${verified ? "verified" : "unverified"} provenance, mine to product.`
    : "Tamper-evident battery passport — provenance from mine to product.";
  return {
    title,
    description,
    openGraph: { title, description, type: "website" },
    twitter: { card: "summary", title, description },
  };
}

export default async function VerifyPage({ params }: Props) {
  const { token } = await params;
  const { data, error } = await fetchPassport(token);
  return <PassportView token={token} initialData={data ?? null} initialError={error ?? null} />;
}
