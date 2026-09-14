/**
 * apps/web/app/[locale]/(dashboard)/activity/layout.tsx — Epic 17 T3 (AC #3.6)
 *
 * Auth gate for /activity (activity stream timeline).
 *
 * Per PRD §F21.3 + AD-32 (c):
 *   - Require active session (sb-access-token cookie present).
 *   - Activity stream is available to ALL tenant members
 *     (owner / admin / member / viewer) — no capability gate is
 *     applied at the backend route layer per PRD §F21.3 verbatim.
 *
 * Layout-level auth check matches the (dashboard)/audit-log/ layout
 * pattern (Epic 17 T2 wire verbatim).
 *
 * cj-style N+16 (D-Day MVP demo): MVP dev bypass — skip redirect when
 * `NEXT_PUBLIC_MVP_DEV_BYPASS=true` (mirrors backend `MVP_DEV_BYPASS`).
 */
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { isDevBypassActive } from "@/lib/auth/dev-bypass";

interface ActivityLayoutProps {
  children: ReactNode;
}

export default async function ActivityLayout({
  children,
}: ActivityLayoutProps): Promise<ReactNode> {
  if (isDevBypassActive()) {
    return children;
  }
  const cookieStore = await cookies();
  const hasSession = cookieStore.get("sb-access-token")?.value;
  if (!hasSession) {
    redirect("/ko-KR/login");
  }
  return children;
}
