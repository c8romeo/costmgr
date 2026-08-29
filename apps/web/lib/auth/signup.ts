/**
 * apps/web/lib/auth/signup.ts — Signup + tenant creation backend callback.
 *
 * Phase 3-1 — T3.3 (AC #2.2, #2.3, #2.4, #2.5) — F-15.2.
 * 1. `supabase.auth.signUp({ email, password, options: { data: { company_name } } })`
 *    → returns a session with a PRE-onboarding JWT (no `tenant_id` claim;
 *    `decode_jwt(require_tenant=False)` accepts it per Phase 3-0 wire).
 * 2. POST /api/v1/onboarding/complete-signup with the pre-onboarding
 *    access token. Backend atomically creates users + tenants +
 *    tenant_memberships + tenant_settings + audit_logs.
 * 3. `supabase.auth.refreshSession()` → second mint hits the
 *    custom_access_token_hook (alembic 0035) which populates
 *    app_metadata.tenant_id + role + industry.
 *
 * Returns Result envelope so React form code doesn't `try/catch` in render.
 *
 * Tests MUST `vi.mock('@/lib/auth/signup')`.
 */
"use client";

import { createSupabaseBrowserClient } from "@/lib/supabase/client";

const PASSWORD_STRENGTH =
  /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]).{10,}$/;

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const INDOTRY_VALUES = [
  "manufacturing",
  "service",
  "manufacturing_service",
  "manufacturing_service_other",
] as const;

export interface SignUpArgs {
  email: string;
  password: string;
  passwordConfirm: string;
  companyName: string;
}

export interface SignUpResult {
  ok: boolean;
  message: string;
  code?: string;
  /** When true, the user's email is not yet verified → go to /email-verification-pending. */
  requiresEmailVerification?: boolean;
}

export async function signUpAndCreateTenant(args: SignUpArgs): Promise<SignUpResult> {
  const email = args.email.trim();
  const password = args.password;
  const passwordConfirm = args.passwordConfirm;
  const companyName = args.companyName.trim();

  // Client-side validation.
  if (!email || !EMAIL_REGEX.test(email)) {
    return { ok: false, code: "INVALID_EMAIL", message: "이메일 형식이 올바르지 않습니다." };
  }
  if (!PASSWORD_STRENGTH.test(password)) {
    return {
      ok: false,
      code: "WEAK_PASSWORD",
      message: "비밀번호가 보안 규칙에 부합하지 않습니다 (10자 이상, 대소문자·숫자·특수문자 각 1개 이상).",
    };
  }
  if (password !== passwordConfirm) {
    return { ok: false, code: "PASSWORD_MISMATCH", message: "비밀번호 확인이 일치하지 않습니다." };
  }
  if (!companyName || companyName.length > 100) {
    return { ok: false, code: "INVALID_COMPANY_NAME", message: "회사명은 1~100자입니다." };
  }

  let supabaseClient;
  try {
    supabaseClient = createSupabaseBrowserClient();
  } catch {
    return { ok: false, code: "NETWORK_ERROR", message: "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해 주세요." };
  }

  // Step 1 — Supabase signUp.
  const { data, error } = await supabaseClient.auth.signUp({
    email,
    password,
    options: {
      data: { company_name: companyName },
    },
  });

  if (error) {
    const msg = error.message.toLowerCase();
    if (msg.includes("already registered") || msg.includes("user already")) {
      return { ok: false, code: "DUPLICATE_EMAIL", message: "이미 가입된 이메일입니다." };
    }
    if (msg.includes("password") || msg.includes("weak")) {
      return {
        ok: false,
        code: "WEAK_PASSWORD",
        message: "비밀번호가 보안 규칙에 부합하지 않습니다.",
      };
    }
    return {
      ok: false,
      code: "SIGNUP_FAILED",
      message: "가입에 실패했습니다. 잠시 후 다시 시도해 주세요.",
    };
  }

  // If no session, the user must verify their email first.
  if (!data.session) {
    return {
      ok: true,
      message: "이메일 인증 링크를 발송했습니다.",
      requiresEmailVerification: true,
    };
  }

  // Step 2 — backend tenant creation.
  const accessToken = data.session.access_token;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  const industry: (typeof INDOTRY_VALUES)[number] = "manufacturing"; // default; UI lets user change on /onboarding/industry
  try {
    const response = await fetch("/api/v1/onboarding/complete-signup", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ tenant_name: companyName, industry }),
    });

    if (!response.ok) {
      const errBody = (await response.json().catch(() => ({}))) as { code?: string };
      if (response.status === 409 && errBody.code === "ALREADY_HAS_TENANT") {
        return {
          ok: false,
          code: "ALREADY_HAS_TENANT",
          message: "이미 다른 테넌트에 속해 있습니다. 기존 계정으로 로그인해 주세요.",
        };
      }
      return {
        ok: false,
        code: "TENANT_CREATE_FAILED",
        message: "테넌트 생성에 실패했습니다. 잠시 후 다시 시도해 주세요.",
      };
    }
  } catch {
    return {
      ok: false,
      code: "NETWORK_ERROR",
      message: "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
    };
  }

  // Step 3 — refresh session so the second mint hits the
  // custom_access_token_hook (alembic 0035) which populates
  // app_metadata.tenant_id + role + industry.
  try {
    await supabaseClient.auth.refreshSession();
  } catch {
    // Refresh failure is non-fatal: the user can complete onboarding
    // and the hook will fire on the next token mint.
  }

  return { ok: true, message: "OK" };
}
