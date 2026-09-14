/**
 * apps/web/app/[locale]/(dashboard)/account/backups/layout.tsx — Story 12.2
 *
 * Auth gate + locale forwarding layout for /account/backups.
 *
 * Owner-only — same auth gate pattern as /account/security (Story 12.5).
 * Inherits (dashboard) layout (Sidebar + MenuProvider).
 *
 * cj-style N+16 (D-Day MVP demo): MVP dev bypass — skip redirect when
 * `NEXT_PUBLIC_MVP_DEV_BYPASS=true` (mirrors backend `MVP_DEV_BYPASS`).
 */

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { isDevBypassActive } from "@/lib/auth/dev-bypass";

interface AccountBackupsLayoutProps {
  children: ReactNode;
}

export default async function AccountBackupsLayout({
  children,
}: AccountBackupsLayoutProps): Promise<ReactNode> {
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
