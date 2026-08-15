/**
 * apps/web/app/[locale]/(dashboard)/budget/scenarios/layout.tsx — Story 8.1
 *
 * Auth gate + locale forwarding layout for /budget/scenarios.
 *
 * Mirrors the account/security layout pattern (Story 12.5): cookies
 * detect session and redirect to /login if unauthenticated. Inherits
 * the (dashboard) layout (Sidebar + MenuProvider).
 */

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";

interface BudgetScenariosLayoutProps {
  children: ReactNode;
}

export default async function BudgetScenariosLayout({
  children,
}: BudgetScenariosLayoutProps): Promise<ReactNode> {
  const cookieStore = await cookies();
  const hasSession = cookieStore.get("sb-access-token")?.value;
  if (!hasSession) {
    redirect("/ko-KR/login");
  }
  return children;
}