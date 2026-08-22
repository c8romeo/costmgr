/**
 * apps/web/app/[locale]/(dashboard)/settings/sso/layout.tsx — Epic 16 T4 (AC #7.1)
 *
 * Auth gate + role check for /settings/sso (Tenant IdP admin management UI).
 *
 * Per Epic 16 §F19.4 PRD + AD-30 (d):
 *   - Require active session (sb-access-token cookie present).
 *   - Render the page for authenticated callers; the Client Component
 *     surfaces backend 403 responses for non-owner/admin roles
 *     (capability gate TENANT_IDP_MANAGEMENT enforced server-side).
 *
 * Layout-level auth check matches the (dashboard)/account/security/
 * layout pattern (Phase 3-1 T4.2 verbatim). Middleware (`apps/web/
 * middleware.ts`) is intentionally NOT modified — CR 9-6 minimize
 * scope discipline applies.
 *
 * The CR 12-5 D-GATE-01 inversion (capability gate per-tenant on/off)
 * is enforced at the backend route layer; the frontend layout only
 * performs the session-presence check.
 */
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";

interface SsoLayoutProps {
  children: ReactNode;
}

export default async function SettingsSsoLayout({
  children,
}: SsoLayoutProps): Promise<ReactNode> {
  const cookieStore = await cookies();
  const hasSession = cookieStore.get("sb-access-token")?.value;
  if (!hasSession) {
    // Unauthenticated → /login (locale-aware redirect).
    redirect("/ko-KR/login");
  }
  return children;
}
