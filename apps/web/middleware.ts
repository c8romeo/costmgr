/**
 * apps/web/middleware.ts — Next.js middleware: next-intl + Supabase session +
 * (dashboard) protection + (auth) passthrough + 2FA gate.
 *
 * Phase 3-1 — T4.1 (AC #3.1, #3.2, #3.3, #3.4, #3.5) — F-15.3.
 *
 * Layering:
 *   1. next-intl middleware → handles locale routing (`/ko-KR/*` prefix logic).
 *   2. Supabase SSR Edge variant → refreshes the session cookie + reads user.
 *   3. Route-group fetch decision (auth/middleware.ts):
 *        - /api/v1/*           → bypass (backend handles Supabase JWT).
 *        - /_next, *.svg, ...  → bypass (static).
 *        - (auth)/*            → public (login, signup, forgot-password).
 *        - (dashboard)/*       → protected:
 *            - no session       → /login?redirect=<original>
 *            - session aal=aal1 → /account/security?reason=2fa_required
 *            - else             → render
 *
 * Edge Runtime (export const runtime = 'edge') — middleware-specific.
 * The Supabase SSR Edge variant in `apps/web/lib/supabase/middleware.ts`
 * avoids `next/headers.cookies()` (Node-only) and uses NextRequest +
 * NextResponse cookies directly.
 */
import createMiddleware from "next-intl/middleware";

import { routeGuard, type RouteGuardRequest } from "@/lib/auth/middleware";

export const runtime = "experimental-edge";

const intlMiddleware = createMiddleware({
  locales: ["ko-KR"],
  defaultLocale: "ko-KR",
  localePrefix: "as-needed",
});

export default async function middleware(request: RouteGuardRequest) {
  // Step 1 — next-intl handles locale routing.
  const intlResponse = intlMiddleware(request);

  // Step 2/3 — Supabase session refresh + route guard.
  const guarded = await routeGuard(request, intlResponse);
  return guarded;
}

export const config = {
  matcher: [
    // Skip Next.js internals, static assets, /api/v1 (backend owns auth).
    "/((?!api|_next|_vercel|.*\\..*).*)",
  ],
};
