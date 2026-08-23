/**
 * apps/web/app/[locale]/(dashboard)/admin/slo/layout.tsx —
 * Phase 10 T7 (cj-style 103번째 wire) — RTL section wrapper for the SLO
 * Engineering admin dashboard. Mirrors the chaos admin layout.
 */
import type { ReactNode } from "react";

export default function SloAdminLayout({
  children,
}: {
  children: ReactNode;
}): React.ReactElement {
  return <section dir="ltr">{children}</section>;
}
