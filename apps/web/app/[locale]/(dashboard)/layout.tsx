/**
 * apps/web/app/[locale]/(dashboard)/layout.tsx — dashboard shell.
 *
 * Story 1.1 — Task 4.4. Wraps every dashboard page with
 *   <MenuProvider> (which fetches tenant settings on mount) + <Sidebar>
 *   (which renders the industry-filtered menu).
 *
 * F-1: a Server Component CANNOT pass a function prop to a Client Component
 * (Next.js cannot serialize function references across the RSC boundary).
 * The token (a string) is read here and passed to client components as
 * a stable serializable prop.
 *
 * F-38: the accessToken is read once via `cookies()` and is stable across
 * re-renders for the duration of the request — `MenuProvider` receives
 * the string and uses it directly. No re-render refetch cascade.
 *
 * Sub-route folders for each menu item are NOT created here — they
 * land in their respective stories (m1_baseline, m2_input, …). The
 * catch-all `[...rest]/page.tsx` keeps the URL stable.
 */

import { cookies } from "next/headers";
import type { ReactNode } from "react";

import { MenuProvider } from "@/components/sidebar/MenuContext";
import { Sidebar } from "@/components/sidebar/Sidebar";

export const dynamic = "force-dynamic";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  // F-1 + F-38: read the access token once and pass the STRING (not a function).
  // This is serializable across the RSC boundary.
  const accessToken = cookies().get("sb-access-token")?.value;

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar accessToken={accessToken} />
      <main style={{ flex: 1, padding: "1.5rem 2rem" }}>
        <MenuProvider accessToken={accessToken}>{children}</MenuProvider>
      </main>
    </div>
  );
}