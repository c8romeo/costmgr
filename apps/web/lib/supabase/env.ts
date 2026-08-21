/**
 * apps/web/lib/supabase/env.ts — Supabase environment validation.
 *
 * Phase 3-1 — T1.1 (AC #1.5, #1.6) — Story 1.1 F-1 honestly RESOLVE.
 * AD-26 verbatim invariant: `NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY`
 * are the only two required env vars. They MUST be stable across server + client
 * builds (NEXT_PUBLIC_* prefix → inlined into both bundles).
 *
 * In test mode (vitest), allow missing env by returning a deterministic stub
 * pointing to a placeholder host. This is consistent with the existing
 * `apps/web/__tests__/IndustrySelector.test.tsx` pattern (no live Supabase,
 * MSW intercepts all /api/v1/* calls).
 *
 * The actual `sb-access-token` cookie is the enforced session boundary —
 * AC1.5 invariant: `httpOnly` + `secure` + `sameSite=lax` + `path=/` +
 * `maxAge=3600` (set by Supabase Auth server, not here).
 */
export interface SupabaseEnv {
  url: string;
  anonKey: string;
}

function isVitestTestMode(): boolean {
  if (typeof process === "undefined") return false;
  return (
    process.env.NODE_ENV === "test" ||
    process.env.VITEST === "true" ||
    Boolean(process.env.VITEST_WORKER_ID)
  );
}

export function getSupabaseEnv(): SupabaseEnv {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  // Test mode: return a deterministic stub so `vi.mock('@/lib/supabase/...')`
  // and the test suite can boot without a real Supabase instance.
  if (isVitestTestMode()) {
    return {
      url: url ?? "http://127.0.0.1:54321",
      anonKey: anonKey ?? "test-anon-key-stub",
    };
  }

  if (!url || url.trim() === "") {
    throw new Error(
      "NEXT_PUBLIC_SUPABASE_URL is required. Set it in .env.local or your CI environment.",
    );
  }
  if (!anonKey || anonKey.trim() === "") {
    throw new Error(
      "NEXT_PUBLIC_SUPABASE_ANON_KEY is required. Set it in .env.local or your CI environment.",
    );
  }
  // ACCEPT_POSTGRES_URL like 'http://127.0.0.1:54321' is the Supabase local dev
  // default — we don't reject it (it's a valid placeholder during dev).
  return { url: url.trim(), anonKey: anonKey.trim() };
}
