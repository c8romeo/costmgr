/**
 * apps/web/app/[locale]/(dashboard)/account/security/layout.tsx — Story 12.5
 *
 * Auth gate + locale forwarding layout for /account/security.
 *
 * Uses cookies to detect a session and redirects to /login if not
 * authenticated. Inherits (dashboard) layout (Sidebar + MenuProvider).
 *
 * cj-style N+16 (D-Day MVP demo): MVP dev bypass — skip redirect when
 * `NEXT_PUBLIC_MVP_DEV_BYPASS=true` (mirrors backend `MVP_DEV_BYPASS`).
 */

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { isDevBypassActive } from "@/lib/auth/dev-bypass";

interface SecurityLayoutProps {
  children: ReactNode;
}

export default async function AccountSecurityLayout({
  children,
}: SecurityLayoutProps): Promise<ReactNode> {
  if (isDevBypassActive()) {
    return children;
  }
  const cookieStore = await cookies();
  const hasSession = cookieStore.get("sb-access-token")?.value;
  if (!hasSession) {
    // Unauthenticated → /login (locale-aware redirect).
    redirect("/ko-KR/login");
  }
  return children;
}
