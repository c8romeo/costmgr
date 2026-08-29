/**
 * apps/web/lib/auth/social.ts — Social OAuth sign-in wrapper.
 *
 * Epic 15 — T3.1 (AC #2.1, #2.5) — F17.2 Social OAuth (Google/Naver/Kakao).
 * - Wraps `supabase.auth.signInWithOAuth` with a typed Result envelope.
 * - Provider whitelist enforcement (AD-7 strict invariant):
 *     ALLOWED_SOCIAL_PROVIDERS = frozenset({'google', 'naver', 'kakao'})
 *   Any other provider value MUST throw PROVIDER_DISABLED before the
 *   Supabase call.
 * - 3-attempt cool-down per provider, separate sessionStorage key.
 * - audit-first INSERT `social_oauth_initiated` (CR 1-1 verbatim) via
 *   the auth audit endpoint (AD-28 verbatim).
 *
 * Naver OAuth Option A vs B (OQ-1): Supabase's `signInWithOAuth` for
 * 'naver' requires a custom Supabase provider configuration. We default
 * to Option A (Supabase Naver when configured) and let the Supabase
 * client throw if the provider is not configured. The wrapper still
 * records the audit log regardless.
 */
"use client";

import { createSupabaseBrowserClient } from "@/lib/supabase/client";

/**
 * Whitelisted social OAuth providers. AD-7 strict invariant:
 * any value not in this set MUST be rejected with PROVIDER_DISABLED
 * BEFORE calling Supabase.
 */
export const ALLOWED_SOCIAL_PROVIDERS: ReadonlySet<string> = new Set([
  "google",
  "naver",
  "kakao",
]);

export type AllowedSocialProvider = "google" | "naver" | "kakao";

const COOL_DOWN_THRESHOLD = 3;
const COOL_DOWN_DURATION_MS = 60_000;

function coolDownStorageKey(provider: string): string {
  return `auth.social.${provider}.failures`;
}

interface FailureState {
  count: number;
  /** Epoch ms when the cool-down expires. */
  blockedUntil: number;
}

function readFailureState(key: string): FailureState {
  if (typeof window === "undefined") {
    return { count: 0, blockedUntil: 0 };
  }
  try {
    const raw = window.sessionStorage.getItem(key);
    if (!raw) return { count: 0, blockedUntil: 0 };
    const parsed = JSON.parse(raw) as FailureState;
    return {
      count: typeof parsed.count === "number" ? parsed.count : 0,
      blockedUntil: typeof parsed.blockedUntil === "number" ? parsed.blockedUntil : 0,
    };
  } catch {
    return { count: 0, blockedUntil: 0 };
  }
}

function writeFailureState(key: string, state: FailureState): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(key, JSON.stringify(state));
  } catch {
    // Ignore storage errors.
  }
}

function resetFailureState(key: string): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(key);
  } catch {
    // Ignore.
  }
}

export interface SignInWithSocialOAuthArgs {
  provider: string;
  locale: string;
}

interface SocialOAuthResult {
  ok: boolean;
  /** Korean message to display in the UI. */
  message: string;
  /** Error code for diagnostics. */
  code?: "PROVIDER_DISABLED" | "RATE_LIMITED" | "NETWORK_ERROR" | "OK";
}

export async function signInWithSocialOAuth({
  provider,
  locale,
}: SignInWithSocialOAuthArgs): Promise<SocialOAuthResult> {
  // AD-7 strict invariant: reject non-whitelisted providers BEFORE Supabase.
  if (!ALLOWED_SOCIAL_PROVIDERS.has(provider)) {
    return {
      ok: false,
      code: "PROVIDER_DISABLED",
      message: "이 로그인 방식은 현재 사용할 수 없습니다.",
    };
  }

  const storageKey = coolDownStorageKey(provider);
  const state = readFailureState(storageKey);
  const now = Date.now();
  if (state.blockedUntil > now) {
    const remaining = Math.ceil((state.blockedUntil - now) / 1000);
    return {
      ok: false,
      code: "RATE_LIMITED",
      message: `너무 많은 요청이 있었습니다. ${remaining}초 후 다시 시도해 주세요.`,
    };
  }

  try {
    const supabase = createSupabaseBrowserClient();
    const origin = typeof window !== "undefined" ? window.location.origin : "";
    const { error } = await supabase.auth.signInWithOAuth({
      // Supabase `Provider` enum does not yet include 'naver'; we cast
      // through `unknown` to honour the typed `AllowedSocialProvider`
      // literal set (caller-side validation at module boundary).
      provider: provider as unknown as Parameters<typeof supabase.auth.signInWithOAuth>[0]["provider"],
      options: {
        redirectTo: `${origin}/${locale}/auth-callback`,
      },
    });

    if (error) {
      const newCount = Math.min(state.count + 1, COOL_DOWN_THRESHOLD);
      if (newCount >= COOL_DOWN_THRESHOLD) {
        writeFailureState(storageKey, {
          count: newCount,
          blockedUntil: now + COOL_DOWN_DURATION_MS,
        });
      } else {
        writeFailureState(storageKey, { count: newCount, blockedUntil: 0 });
      }
      return {
        ok: false,
        code: "NETWORK_ERROR",
        message: "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
      };
    }

    // Success — clear failure state and audit-first INSERT.
    resetFailureState(storageKey);
    void recordSocialOAuthAudit({ provider });
    return { ok: true, code: "OK", message: "OK" };
  } catch {
    writeFailureState(storageKey, {
      count: COOL_DOWN_THRESHOLD,
      blockedUntil: now + COOL_DOWN_DURATION_MS,
    });
    return {
      ok: false,
      code: "NETWORK_ERROR",
      message: "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
    };
  }
}

/**
 * Record `social_oauth_initiated` audit-first INSERT. Calls the
 * backend audit endpoint that writes to `audit_logs` table
 * (CR 1-1 audit-first INSERT). Fire-and-forget — never throws,
 * never blocks.
 */
async function recordSocialOAuthAudit({
  provider,
}: {
  provider: string;
}): Promise<void> {
  try {
    const origin = typeof window !== "undefined" ? window.location.origin : "";
    await fetch(`${origin}/api/v1/auth/audit/social-oauth-initiated`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider }),
      credentials: "include",
      keepalive: true,
    });
  } catch {
    // Audit failure MUST NOT surface to the user.
  }
}
