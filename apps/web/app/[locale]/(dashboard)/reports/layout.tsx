/**
 * apps/web/app/[locale]/(dashboard)/reports/layout.tsx — cj-282a wire sprint (cj-style 283번째)
 *
 * Story 30.1 CSV export auth gate layout (FR-30-1).
 *
 * Per cj-282 PRD entry spec §F44.1 + AD-22:
 *   - Require active session (sb-access-token cookie present).
 *   - Capability gate require_exports_csv + owner/admin RBAC 결정 wire 보류:
 *     backend route 의 owner/admin RBAC + tenant context 가 canonical gate
 *     (CR 12-5 D-GATE-01 inversion).
 *   - Frontend layout only performs session-presence check 결정 wire.
 *
 * Pattern verbatim from `apps/web/app/[locale]/(dashboard)/audit-log/layout.tsx:23-37`.
 *
 * CR 11-3 honest-DEFER 223번째:
 *   - Capability gate require_exports_csv EXTENSION cj-style 284+ 적용 결정 wire 보류.
 *   - ko-KR.json EXTENSION cj-style 284+ 적용 결정 wire 보류.
 */
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";

interface ReportsLayoutProps {
  children: ReactNode;
}

export default async function ReportsLayout({
  children,
}: ReportsLayoutProps): Promise<ReactNode> {
  const cookieStore = await cookies();
  const hasSession = cookieStore.get("sb-access-token")?.value;
  if (!hasSession) {
    // Unauthenticated → /login (locale-aware redirect).
    redirect("/ko-KR/login");
  }
  return children;
}