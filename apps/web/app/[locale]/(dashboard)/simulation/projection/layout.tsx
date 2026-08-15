/**
 * apps/web/app/[locale]/(dashboard)/simulation/projection/layout.tsx — Story 7.2
 *
 * Auth gate + locale forwarding layout for /simulation/projection.
 *
 * Mirrors the simulation/cvp layout pattern (Story 7.1): cookies detect
 * session and redirect to /login if unauthenticated. Inherits the
 * (dashboard) layout (Sidebar + MenuProvider).
 */

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";

interface ProjectionLayoutProps {
  children: ReactNode;
}

export default async function ProjectionLayout({
  children,
}: ProjectionLayoutProps): Promise<ReactNode> {
  const cookieStore = await cookies();
  const hasSession = cookieStore.get("sb-access-token")?.value;
  if (!hasSession) {
    redirect("/ko-KR/login");
  }
  return children;
}
