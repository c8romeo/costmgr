/**
 * apps/web/lib/auth/login.ts — Sign-in wrapper + 5-failure cool-down.
 *
 * Phase 3-1 — T2.3 (AC #1.2, #1.3, #1.4) — F-15.1.
 * - Wraps `supabase.auth.signInWithPassword` with a typed Result
 *   envelope so callers don't have to handle exceptions in render flow.
 * - 5-failure cool-down uses sessionStorage so it survives page reload
 *   but not across browsers/devices. (Server-side rate limiting is out
 *   of scope for Phase 3 — see spec OQ-2 for follow-up decision.)
 * - Returns the Supabase session's AAL claim so the form can branch
 *   to /auth/2fa when AAL is 'aal1' (Epic 12 wire).
 */
"use client";

import { createSupabaseBrowserClient } from "@/lib/supabase/client";

const COOL_DOWN_THRESHOLD = 5;
const COOL_DOWN_DURATION_MS = 30_000;
const COOL_DOWN_STORAGE_KEY = "auth.login.failures";

interface FailureState {
  count: number;
  /** Epoch ms when the cool-down expires. */
  blockedUntil: number;
}

interface SignInResult {
  ok: boolean;
  /** Korean message to display in the UI. */
  message: string;
  /** AAL claim from the session, present only when ok=true. */
  aal?: "aal1" | "aal2";
  /** Error code for diagnostics. */
  code?: string;
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

export interface SignInArgs {
  email: string;
  password: string;
}

export async function signInWithPassword({
  email,
  password,
}: SignInArgs): Promise<SignInResult> {
  const trimmedEmail = email.trim();
  if (!trimmedEmail || !password) {
    return { ok: false, code: "INVALID_INPUT", message: "이메일과 비밀번호를 입력해 주세요." };
  }

  // Cool-down gate (AC #1.3).
  const state = readFailureState();
  const now = Date.now();
  if (state.blockedUntil > now) {
    const remaining = Math.ceil((state.blockedUntil - now) / 1000);
    return {
      ok: false,
      code: "RATE_LIMITED",
      message: `로그인 5회 실패로 30초간 제한됩니다 (${remaining}초 후 다시 시도).`,
    };
  }

  let supabaseClient;
  try {
    supabaseClient = createSupabaseBrowserClient();
    const { data, error } = await supabaseClient.auth.signInWithPassword({
      email: trimmedEmail,
      password,
    });
    if (error) {
      const newCount = state.count + 1;
      if (newCount >= COOL_DOWN_THRESHOLD) {
        writeFailureState({
          count: newCount,
          blockedUntil: now + COOL_DOWN_DURATION_MS,
        });
        return {
          ok: false,
          code: "RATE_LIMITED",
          message: "로그인 5회 실패로 30초간 제한됩니다.",
        };
      }
      writeFailureState({ count: newCount, blockedUntil: 0 });
      const INVALID_CREDENTIALS = "이메일 또는 비밀번호가 올바르지 않습니다.";
      return {
        ok: false,
        code: "INVALID_CREDENTIALS",
        message: INVALID_CREDENTIALS,
      };
    }

    // Success — clear failure state.
    resetFailureState();

    // AAL claim lives in the session payload. Epic 12 wire keeps it on
    // app_metadata.aal; we fall back to default 'aal1' if missing.
    const aal = (data.session?.user?.app_metadata?.aal ?? "aal1") as "aal1" | "aal2";
    return { ok: true, aal, message: "OK" };
  } catch (err) {
    const NETWORK_ERROR = "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.";
    return {
      ok: false,
      code: "NETWORK_ERROR",
      message: NETWORK_ERROR,
    };
  }
}
