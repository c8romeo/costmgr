/**
 * apps/web/app/[locale]/(dashboard)/account/security/layout.tsx — Story 12.5
 *
 * Auth gate + locale forwarding layout for /account/security.
 *
 * Uses cookies to detect a session and redirects to /login if not
 * authenticated. Inherits (dashboard) layout (Sidebar + MenuProvider).
 */

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";

interface SecurityLayoutProps {
  children: ReactNode;
}

export default async function AccountSecurityLayout({
  children,
}: SecurityLayoutProps): Promise<ReactNode> {
  const cookieStore = await cookies();
  const hasSession = cookieStore.get("sb-access-token")?.value;
  if (!hasSession) {
    // Unauthenticated → /login (locale-aware redirect).
    redirect("/ko-KR/login");
  }
  return children;
}
