/**
 * apps/web/lib/auth/middleware.ts — Route-group fetch decision.
 *
 * Phase 3-1 — T4.2 (AC #3.1, #3.2, #3.3, #3.4, #3.6) — F-15.3.
 *
 * Lifecycle:
 *   1. Supabase SSR Edge variant refreshes the session cookie
 *      (apps/web/lib/supabase/middleware.ts).
 *   2. This helper reads the `user` from the response and decides
 *      what to do based on the route group:
 *        - /api/v1/*           → bypass (backend owns Supabase JWT).
 *        - (auth)/*            → public (login, signup, forgot-password).
 *        - (dashboard)/*       → protected:
 *            - no session       → /login?redirect=<original>
 *            - session aal=aal1 → /account/security?reason=2fa_required
 *        - else                → render (root / goes through intl).
 *
 * Edge Runtime compatible — uses NextRequest + NextResponse only.
 *
 * Tests MUST `vi.mock('@/lib/auth/middleware')` AND `vi.mock('@/lib/supabase/middleware')`.
 */
import { NextResponse, type NextRequest } from "next/server";

import { updateSupabaseSession } from "@/lib/supabase/middleware";

export interface RouteGuardRequest extends NextRequest {}

const DASHBOARD_PREFIX = "/(dashboard)";
const AUTH_PREFIX = "/(auth)";
const ACCOUNT_SECURITY_PATH = "/account/security";
const LOGIN_PATH = "/login";
const TWO_FA_PATH = "/auth/2fa";

function isDashboardPath(pathname: string): boolean {
  // We can't see "(dashboard)" in the actual URL — Next.js strips route groups.
  // The dashboard routes are at root under [locale]/(dashboard)/<page> i.e.
  // /[locale]/dashboard. Auth/landing pages are at /[locale]/(auth)/<page>
  // i.e. /[locale]/login, /[locale]/signup, etc.
  // Distinguish by Pathname: /dashboard/* is protected; /login, /signup, /forgot-password are public.
  // Match both /dashboard and /<locale>/dashboard (with optional locale prefix).
  return /^\/(?:(?:[a-z]{2}-[A-Z]{2})\/)?dashboard(\/|$)/.test(pathname);
}

function isAuthPath(pathname: string): boolean {
  return (
    /^\/(?:[a-z]{2}-[A-Z]{2})?\/login(\/|$|\?)/.test(pathname) ||
    /^\/(?:[a-z]{2}-[A-Z]{2})?\/signup(\/|$|\?)/.test(pathname) ||
    /^\/(?:[a-z]{2}-[A-Z]{2})?\/forgot-password(\/|$|\?)/.test(pathname) ||
    /^\/(?:[a-z]{2}-[A-Z]{2})?\/reset-password(\/|$|\?)/.test(pathname) ||
    /^\/(?:[a-z]{2}-[A-Z]{2})?\/auth\/2fa(\/|$|\?)/.test(pathname) ||
    // Epic 15 (cj-style 60번째) — magic link + OAuth callback + SSO
    // login pages are public (the auth-callback itself only finalizes
    // a session that was initiated by a signed-in caller).
    /^\/(?:[a-z]{2}-[A-Z]{2})?\/magic-link(\/|$|\?)/.test(pathname) ||
    /^\/(?:[a-z]{2}-[A-Z]{2})?\/magic-link-sent(\/|$|\?)/.test(pathname) ||
    /^\/(?:[a-z]{2}-[A-Z]{2})?\/auth-callback(\/|$|\?)/.test(pathname) ||
    /^\/(?:[a-z]{2}-[A-Z]{2})?\/sso\/[^/]+\/login(\/|$|\?)/.test(pathname)
  );
}

function stripLocale(pathname: string): string {
  const match = pathname.match(/^\/([a-z]{2}-[A-Z]{2})(\/.*|$)/);
  return match ? (match[2] || "/") : pathname;
}

function parseAAL(headers: Headers): "aal1" | "aal2" | null {
  const aal = headers.get("x-user-aal");
  return aal === "aal1" || aal === "aal2" ? aal : null;
}

export async function routeGuard(
  request: RouteGuardRequest,
  intlResponse: NextResponse,
): Promise<NextResponse> {
  const { pathname } = request.nextUrl;

  // Step 1 — refresh Supabase session (Edge variant).
  const supabaseResponse = await updateSupabaseSession(request);

  // Step 2 — bypass for /api/v1/* (already in matcher, but defensive).
  if (pathname.startsWith("/api/")) {
    return supabaseResponse;
  }

  // Step 3 — public (auth) routes: just let them through.
  if (isAuthPath(pathname)) {
    return supabaseResponse;
  }

  // Step 4 — (dashboard) routes require session.
  if (isDashboardPath(pathname)) {
    const userId = supabaseResponse.headers.get("x-user-id");
    if (!userId) {
      const redirectUrl = request.nextUrl.clone();
      const originalPath = pathname + request.nextUrl.search;
      redirectUrl.pathname = stripLocale(pathname).startsWith("/")
        ? `${stripLocale(pathname).split("/").slice(0, 2).join("/") || ""}/login`
        : LOGIN_PATH;
      // Use the actual locale prefix in the URL — strip then re-prepend.
      const localeMatch = pathname.match(/^\/([a-z]{2}-[A-Z]{2})/);
      const locale = localeMatch ? `/${localeMatch[1]}` : "";
      redirectUrl.pathname = `${locale}/login`;
      redirectUrl.search = `?redirect=${encodeURIComponent(originalPath)}`;
      return NextResponse.redirect(redirectUrl);
    }

    // 2FA gate (AC #3.4).
    const aal = parseAAL(supabaseResponse.headers);
    if (aal === "aal1") {
      const localeMatch = pathname.match(/^\/([a-z]{2}-[A-Z]{2})/);
      const locale = localeMatch ? `/${localeMatch[1]}` : "";
      const accountUrl = request.nextUrl.clone();
      accountUrl.pathname = `${locale}${ACCOUNT_SECURITY_PATH}`;
      accountUrl.search = "?reason=2fa_required";
      return NextResponse.redirect(accountUrl);
    }
  }

  // Default: return the supabase response (session cookies updated).
  return supabaseResponse;
}

// Re-export constants for tests.
export const ROUTE_GUARD_CONSTANTS = {
  DASHBOARD_PREFIX,
  AUTH_PREFIX,
  ACCOUNT_SECURITY_PATH,
  LOGIN_PATH,
  TWO_FA_PATH,
};
