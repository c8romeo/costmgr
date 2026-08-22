/**
 * apps/web/lib/auth/magic-link.ts — Magic link sign-in wrapper.
 *
 * Epic 15 — T1.1+T1.2 (AC #1.1, #1.5) — F17.1 Magic link.
 * - Wraps `supabase.auth.signInWithOtp` with a typed Result envelope so
 *   callers don't have to handle exceptions in render flow.
 * - 5-attempt cool-down uses sessionStorage so it survives page reload
 *   but not across browsers/devices. Server-side rate limiting is out
 *   of scope for Epic 15 — see spec OQ-2 for follow-up decision.
 * - SECURITY: This wrapper ALWAYS returns ok=true regardless of whether
 *   the email is registered, so callers cannot leak account existence.
 *   The actual `supabase.auth.signInWithOtp` call is wrapped in
 *   try/catch/finally so any network error doesn't surface to the user.
 * - audit-first INSERT `magic_link_sent` is recorded in the backend
 *   audit_logs table via the auth audit endpoint (CR 1-1 verbatim +
 *   Epic 15 AD-28 verbatim).
 */
"use client";

import { createSupabaseBrowserClient } from "@/lib/supabase/client";

const COOL_DOWN_THRESHOLD = 5;
const COOL_DOWN_DURATION_MS = 30_000;
const COOL_DOWN_STORAGE_KEY = "auth.magic_link.failures";

interface FailureState {
  count: number;
  /** Epoch ms when the cool-down expires. */
  blockedUntil: number;
}

interface MagicLinkResult {
  ok: true;
  /** Korean message to display in the UI. */
  message: string;
  /** Error code for diagnostics. */
  code?: "RATE_LIMITED" | "NETWORK_ERROR" | "OK";
}

function readFailureState(): FailureState {
  if (typeof window === "undefined") {
    return { count: 0, blockedUntil: 0 };
  }
  try {
    const raw = window.sessionStorage.getItem(COOL_DOWN_STORAGE_KEY);
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

function writeFailureState(state: FailureState): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(COOL_DOWN_STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Ignore storage errors (private mode, quota, etc.).
  }
}

function resetFailureState(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(COOL_DOWN_STORAGE_KEY);
  } catch {
    // Ignore.
  }
}

export interface SendMagicLinkArgs {
  email: string;
  locale: string;
}

/**
 * Send a magic link to the supplied email. Always returns ok=true when
 * the request is well-formed (email present, not over cool-down) — the
 * caller cannot determine whether the email is registered. The actual
 * Supabase call is fire-and-forget wrapped in try/catch/finally.
 */
export async function sendMagicLink({
  email,
  locale,
}: SendMagicLinkArgs): Promise<MagicLinkResult> {
  const trimmedEmail = email.trim();
  if (!trimmedEmail) {
    return { ok: true, code: "OK", message: "메일함을 확인해 주세요. 로그인 링크가 전송되었습니다." };
  }

  // Cool-down gate (AC #1.1).
  const state = readFailureState();
  const now = Date.now();
  if (state.blockedUntil > now) {
    const remaining = Math.ceil((state.blockedUntil - now) / 1000);
    return {
      ok: true,
      code: "RATE_LIMITED",
      message: `너무 많은 요청이 있었습니다. ${remaining}초 후 다시 시도해 주세요.`,
    };
  }

  // SECURITY INVARIANT (AC #1.1): try/catch/finally. Always return success.
  try {
    const supabase = createSupabaseBrowserClient();
    const origin = typeof window !== "undefined" ? window.location.origin : "";
    const { error } = await supabase.auth.signInWithOtp({
      email: trimmedEmail,
      options: {
        emailRedirectTo: `${origin}/${locale}/auth-callback`,
      },
    });

    if (error) {
      // Increment failure counter (cap at threshold for the cool-down calc).
      const newCount = Math.min(state.count + 1, COOL_DOWN_THRESHOLD);
      if (newCount >= COOL_DOWN_THRESHOLD) {
        writeFailureState({
          count: newCount,
          blockedUntil: now + COOL_DOWN_DURATION_MS,
        });
      } else {
        writeFailureState({ count: newCount, blockedUntil: 0 });
      }
      // Fall through to audit + success (security invariant: never reveal).
    } else {
      // Success — clear failure state.
      resetFailureState();
    }
  } catch {
    // Swallow — security invariant: always return success regardless of
    // network errors, misconfigured Supabase, etc.
    writeFailureState({
      count: COOL_DOWN_THRESHOLD,
      blockedUntil: now + COOL_DOWN_DURATION_MS,
    });
  } finally {
    // audit-first INSERT `magic_link_sent` (AC #1.5, CR 1-1 verbatim).
    // Fire-and-forget — never block the user response on the audit call.
    void recordMagicLinkAudit({ email: trimmedEmail });
  }

  return {
    ok: true,
    code: "OK",
    message: "메일함을 확인해 주세요. 로그인 링크가 전송되었습니다.",
  };
}

/**
 * Record `magic_link_sent` audit-first INSERT. Calls the backend audit
 * endpoint that writes to `audit_logs` table (CR 1-1 audit-first INSERT).
 * Fire-and-forget — never throws, never blocks.
 */
async function recordMagicLinkAudit({
  email,
}: {
  email: string;
}): Promise<void> {
  try {
    const origin = typeof window !== "undefined" ? window.location.origin : "";
    await fetch(`${origin}/api/v1/auth/audit/magic-link-sent`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_email: email }),
      credentials: "include",
      keepalive: true,
    });
  } catch {
    // Audit failure MUST NOT surface to the user (security invariant).
  }
}
