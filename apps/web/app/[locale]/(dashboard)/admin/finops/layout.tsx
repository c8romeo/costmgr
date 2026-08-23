/**
 * apps/web/app/[locale]/(dashboard)/admin/finops/layout.tsx —
 * Phase 11 T7 (cj-style 107번째 wire) — RTL section wrapper for the
 * FinOps Showback / Chargeback admin dashboard. Mirrors the SLO admin
 * layout verbatim.
 */
import type { ReactNode } from "react";

export default function FinopsAdminLayout({
  children,
}: {
  children: ReactNode;
}): React.ReactElement {
  return <section dir="ltr">{children}</section>;
}
