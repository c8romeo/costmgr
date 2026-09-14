/**
 * apps/web/app/[locale]/(dashboard)/simulation/cvp/layout.tsx — Story 7.1
 *
 * Auth gate + locale forwarding layout for /simulation/cvp.
 *
 * Mirrors the budget/scenarios layout pattern (Story 8.1): cookies
 * detect session and redirect to /login if unauthenticated. Inherits
 * the (dashboard) layout (Sidebar + MenuProvider).
 *
 * cj-style N+16 (D-Day MVP demo): MVP dev bypass — skip redirect when
 * `NEXT_PUBLIC_MVP_DEV_BYPASS=true` (mirrors backend `MVP_DEV_BYPASS`).
 */

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { isDevBypassActive } from "@/lib/auth/dev-bypass";

interface CVPLayoutProps {
  children: ReactNode;
}

export default async function CVPLayout({
  children,
}: CVPLayoutProps): Promise<ReactNode> {
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
