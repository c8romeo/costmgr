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
 * Hot-fix 2026-08-22: <Sidebar> was rendered OUTSIDE <MenuProvider>, but
 * `Sidebar` calls `useMenuContext()` which throws if no provider is found.
 * Moved <Sidebar> INSIDE <MenuProvider> so the context is available.
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

var NEXT_PUBLIC_SUPABASE_URL =
  process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";

export default async function DashboardLayout({ children }: { children: ReactNode }) {
  // cj-style N+7 (admin 시점 verification gate fix) — Supabase 의
  // `@supabase/ssr` 가 cookie 에 저장하는 이름은
  // `sb-<project-ref>-auth-token` (예: `sb-zlluqhjywodsnmsiccuk-auth-token`)
  // 이며, 값은 base64(JSON) 안에 `access_token` 을 보관. 직접 cookie
  // name 으로 read + base64 decode 가 가장 확실. `auth.getSession()`
  // 은 Next.js 15 + react 19 환경에서 가끔 throw → fallback 으로
  // 진짜 cookie 에서 직접 추출.
  let accessToken: string | undefined;
  const cookieStore = await cookies();
  const allCookies = cookieStore.getAll();
  const cookieList = Array.isArray(allCookies)
    ? allCookies
    : Object.entries(allCookies).map(([name, value]) => ({
        name,
        value: typeof value === "string" ? value : (value as { value: string }).value,
      }));
  for (const { name, value: raw } of cookieList) {
    if (name.endsWith("-auth-token")) {
      try {
        const decoded = Buffer.from(raw, "base64").toString("utf8");
        const parsed = JSON.parse(decoded) as { access_token?: string };
        if (parsed.access_token) {
          accessToken = parsed.access_token;
          break;
        }
      } catch {
        // skip non-JSON cookies (anon-key, etc.)
      }
    }
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <MenuProvider accessToken={accessToken}>
        <Sidebar accessToken={accessToken} />
        <main style={{ flex: 1, padding: "1.5rem 2rem" }}>{children}</main>
      </MenuProvider>
    </div>
  );
}