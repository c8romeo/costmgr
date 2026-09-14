/**
 * apps/web/app/[locale]/(dashboard)/account/settings/layout.tsx — Story 12.3
 *
 * Auth gate + locale forwarding layout for /account/settings.
 *
 * Owner-only — same auth gate pattern as /account/security (Story 12.5)
 * and /account/backups (Story 12.2). Inherits (dashboard) layout
 * (Sidebar + MenuProvider).
 *
 * The destructive endpoint `POST /api/v1/account/deletion/request` is
 * gated server-side at the FastAPI route layer
 * (`require_role("owner")` + `require_capability(ACCOUNT_DELETION)`).
 * This layout only enforces session presence.
 *
 * cj-style N+16 (D-Day MVP demo): MVP dev bypass — skip redirect when
 * `NEXT_PUBLIC_MVP_DEV_BYPASS=true` (mirrors backend `MVP_DEV_BYPASS`).
 */

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { isDevBypassActive } from "@/lib/auth/dev-bypass";

interface AccountSettingsLayoutProps {
  children: ReactNode;
}

export default async function AccountSettingsLayout({
  children,
}: AccountSettingsLayoutProps): Promise<ReactNode> {
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
