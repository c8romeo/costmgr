/**
 * apps/web/lib/supabase/middleware.ts — Supabase SSR Edge variant for middleware.
 *
 * Phase 3-1 — T1.5 (AC #1.5, #1.6, #3.5) — Edge Runtime compatible.
 * The Edge variant uses `NextRequest.cookies` + `NextResponse.cookies` directly
 * (no `next/headers.cookies()` — the latter is Node-runtime-only).
 *
 * The middleware helper at `apps/web/lib/auth/middleware.ts` (T4.2) wraps
 * this to do the route-group fetch decision (auth redirect / dashboard
 * protect / 2FA gate). This separation keeps the Supabase-specific
 * cookie plumbing here and the route policy in the auth helper.
 *
 * Tests MUST `vi.mock('@/lib/supabase/middleware')` to avoid the Edge
 * runtime dependency.
 */
import { createServerClient, type CookieOptions } from "@supabase/ssr";
import { type NextRequest, NextResponse } from "next/server";


import { getSupabaseEnv } from "./env";

export interface SupabaseMiddlewareClient {
  response: NextResponse;
  user: { id: string; email: string; app_metadata: Record<string, unknown> } | null;
}

export async function updateSupabaseSession(
  request: NextRequest,
): Promise<NextResponse> {
  const { url, anonKey } = getSupabaseEnv();
  let response = NextResponse.next({ request });

  const supabase = createServerClient(url, anonKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        for (const { name, value, options } of cookiesToSet) {
          request.cookies.set(name, value);
          response.cookies.set(name, value, options as CookieOptions);
        }
      },
    },
  });

  // CRITICAL: do not run any code between createServerClient and
  // getUser(). A simple mistake could make it very hard to debug
  // issues with users being randomly logged out.
  //
  // Ref: https://supabase.com/docs/guides/auth/server-side/nextjs
  const {
    data: { user },
  } = await supabase.auth.getUser();

  // Pass the user id forward to the route handler chain via a request
  // header so downstream Server Components can read it without re-decoding.
  if (user) {
    response.headers.set("x-user-id", user.id);
  }

  return response;
}
