/**
 * apps/web/lib/supabase/server.ts — Supabase SSR client for Server Components.
 *
 * Phase 3-1 — T1.2 (AC #1.5, #1.6) — Story 1.1 F-1 honestly RESOLVE.
 * AD-26 verbatim: `sb-access-token` cookie session httpOnly + secure +
 * sameSite=lax + path=/ + maxAge=3600 — read via Next.js `cookies()` API.
 * The server runtime is `nodejs` (NOT `'edge'`) — see ADR for the
 * RSC+Node split rationale. Middleware uses the Edge variant
 * (`apps/web/lib/supabase/middleware.ts`) which avoids the cookies()
 * helper Edge-incompatibility.
 *
 * Usage:
 *   import { createSupabaseServerClient } from '@/lib/supabase/server';
 *   const supabase = await createSupabaseServerClient();
 *   const { data: { user } } = await supabase.auth.getUser();
 *
 * Tests MUST `vi.mock('@/lib/supabase/server')` to avoid real cookies().
 */
import { createServerClient, type CookieOptions } from "@supabase/ssr";
import { cookies } from "next/headers";


import { getSupabaseEnv } from "./env";

export async function createSupabaseServerClient() {
  const { url, anonKey } = getSupabaseEnv();
  const cookieStore = await cookies();

  return createServerClient(url, anonKey, {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      setAll(cookiesToSet) {
        try {
          for (const { name, value, options } of cookiesToSet) {
            cookieStore.set(name, value, options as CookieOptions);
          }
        } catch {
          // RSC: set() is a no-op when called from a Server Component
          // (the cookies() API is read-only there). Middleware REFRESHES
          // the session and writes the cookie via NextResponse — this
          // try/catch is the canonical pattern from @supabase/ssr docs.
        }
      },
    },
  });
}
