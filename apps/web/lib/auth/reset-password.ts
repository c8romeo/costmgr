/**
 * apps/web/lib/auth/reset-password.ts — Password reset confirmation wrapper.
 *
 * Phase 3-1 — T6.6 (AC #5.3, #5.4) — F-15.5 + CR 1-1 audit-first INSERT.
 * 1. Verify the recovery `code` (Supabase session token) → establish a session.
 * 2. `supabase.auth.updateUser({ password })` to set the new password.
 * 3. Backend audit INSERT (`action_name='password_reset'`) — best-effort.
 * 4. Sign out + return to the form.
 */
"use client";

import { createSupabaseBrowserClient } from "@/lib/supabase/client";

const PASSWORD_STRENGTH =
  /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]).{10,}$/;

export interface ResetPasswordArgs {
  code: string;
  password: string;
  passwordConfirm: string;
}

export interface ResetPasswordResult {
  ok: boolean;
  message: string;
  code?: string;
}

export async function resetPassword(args: ResetPasswordArgs): Promise<ResetPasswordResult> {
  if (!args.code) {
    return {
      ok: false,
      code: "INVALID_TOKEN",
      message: "재설정 링크가 유효하지 않거나 만료되었습니다. 다시 요청해 주세요.",
    };
  }
  if (!PASSWORD_STRENGTH.test(args.password)) {
    return {
      ok: false,
      code: "WEAK_PASSWORD",
      message: "비밀번호가 보안 규칙에 부합하지 않습니다.",
    };
  }
  if (args.password !== args.passwordConfirm) {
    return {
      ok: false,
      code: "PASSWORD_MISMATCH",
      message: "비밀번호 확인이 일치하지 않습니다.",
    };
  }

  let supabaseClient;
  try {
    supabaseClient = createSupabaseBrowserClient();
  } catch {
    return {
      ok: false,
      code: "NETWORK_ERROR",
      message: "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
    };
  }

  // Establish a recovery session using the supabase.auth.verifyOtp pattern.
  // `exchangeCodeForSession` is the canonical @supabase/ssr entry point.
  const { error: exchangeError } = await supabaseClient.auth.exchangeCodeForSession(
    args.code,
  );
  if (exchangeError) {
    return {
      ok: false,
      code: "INVALID_TOKEN",
      message: "재설정 링크가 유효하지 않거나 만료되었습니다. 다시 요청해 주세요.",
    };
  }

  const { data, error } = await supabaseClient.auth.updateUser({
    password: args.password,
  });

  if (error) {
    const msg = error.message.toLowerCase();
    if (msg.includes("password") || msg.includes("weak")) {
      return {
        ok: false,
        code: "WEAK_PASSWORD",
        message: "비밀번호가 보안 규칙에 부합하지 않습니다.",
      };
    }
    return {
      ok: false,
      code: "UPDATE_FAILED",
      message: "비밀번호 변경에 실패했습니다. 잠시 후 다시 시도해 주세요.",
    };
  }

  // Best-effort backend audit INSERT.
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const accessToken = data?.user ? null : null;
  const userId = data?.user?.id ?? null;
  const tenantId = (data?.user?.app_metadata?.tenant_id as string | undefined) ?? null;
  if (userId) {
    try {
      const session = await supabaseClient.auth.getSession();
      const tok = session.data.session?.access_token;
      if (tok) {
        await fetch("/api/v1/auth/password-reset", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${tok}`,
          },
          body: JSON.stringify({
            actor_user_id: userId,
            tenant_id: tenantId,
            reset_method: "email_link",
            session_invalidated: true,
          }),
        });
      }
    } catch {
      // Non-fatal.
    }
  }

  // Sign out so the user goes back to /login cleanly.
  await supabaseClient.auth.signOut();
  return { ok: true, message: "OK" };
}
