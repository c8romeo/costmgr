/**
 * apps/web/lib/supabase/client.ts — Supabase SSR client for browser.
 *
 * Phase 3-1 — T1.3 (AC #1.5, #1.6) — Story 1.1 F-1 honestly RESOLVE.
 * Browser-side client uses the same PKCE flow the server side initiates,
 * so the `sb-access-token` cookie + Supabase auto-refresh stay in sync
 * with the server-side session. CSRF defense is the PKCE flow + the
 * `sameSite=lax` cookie (no separate CSRF token per AD-26).
 *
 * MUST be invoked from a Client Component (`"use client"`), otherwise
 * Next.js will warn about serverleaks. The wrapper functions in
 * `apps/web/lib/auth/{login,signup,logout,forgot-password,reset-password}.ts`
 * are the canonical entry points.
 */
"use client";

import { createBrowserClient } from "@supabase/ssr";

import { getSupabaseEnv } from "./env";

export function createSupabaseBrowserClient() {
  const { url, anonKey } = getSupabaseEnv();
  return createBrowserClient(url, anonKey);
}
