/**
 * apps/web/app/[locale]/(dashboard)/audit-log/layout.tsx — Epic 17 T2 (AC #2.7)
 *
 * Auth gate for /audit-log (audit log viewer).
 *
 * Per PRD §F21.2 + AD-32 (b):
 *   - Require active session (sb-access-token cookie present).
 *   - Capability gate AUDIT_LOG_VIEW + owner/admin RBAC is enforced
 *     server-side at the backend route layer (CR 12-5 D-GATE-01 inversion).
 *     The frontend layout only performs the session-presence check.
 *
 * Layout-level auth check matches the (dashboard)/settings/sso/
 * layout pattern (Epic 16 T4 wire `ff5c3b5` verbatim).
 *
 * Middleware (`apps/web/middleware.ts`) is intentionally NOT modified —
 * CR 9-6 minimize scope discipline applies.
 */
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";

interface AuditLogLayoutProps {
  children: ReactNode;
}

export default async function AuditLogLayout({
  children,
}: AuditLogLayoutProps): Promise<ReactNode> {
  const cookieStore = await cookies();
  const hasSession = cookieStore.get("sb-access-token")?.value;
  if (!hasSession) {
    // Unauthenticated → /login (locale-aware redirect).
    redirect("/ko-KR/login");
  }
  return children;
}
