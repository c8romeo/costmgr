/**
 * apps/web/components/auth/SignupForm.tsx — Signup form Client Component.
 *
 * Phase 3-1 — T3.2 (AC #2.2, #2.3, #2.4, #2.5) — F-15.2.
 * - 4 fields: email + password + password_confirm + company_name
 * - Validation: email RFC 5322, password strength regex,
 *   password confirm match, company_name 1~100 chars (trim nonempty)
 * - Submit flow:
 *     1. `supabase.auth.signUp({ email, password, options: { data: { company_name } } })`
 *     2. If session exists, call `POST /api/v1/onboarding/complete-signup`
 *        with the pre-onboarding JWT to atomically create tenant +
 *        tenant_memberships + tenant_settings + audit_log.
 *     3. `supabase.auth.refreshSession()` so the SECOND mint hits the
 *        custom_access_token_hook (alembic 0035) which populates
 *        app_metadata.tenant_id + role + industry.
 *     4. Redirect to /auth/email-verification-pending (or /onboarding/industry
 *        if email was already verified).
 * - Korean error messages via ko-KR.json SSOT.
 */
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { signUpAndCreateTenant } from "@/lib/auth/signup";

export interface SignupFormProps {
  locale: string;
}

export function SignupForm({ locale }: SignupFormProps) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    const result = await signUpAndCreateTenant({
      email,
      password,
      passwordConfirm,
      companyName,
    });

    if (!result.ok) {
      setError(result.message);
      setSubmitting(false);
      return;
    }

    if (result.requiresEmailVerification) {
      router.push(`/${locale}/signup/email-verification-pending`);
      router.refresh();
      return;
    }

    // Pre-onboarding JWT minted a tenant; second refreshSession() picks up
    // the populated app_metadata (tenant_id + role + industry).
    router.push(`/${locale}/onboarding/industry`);
    router.refresh();
  }

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        maxWidth: 420,
        width: "100%",
        padding: "1.5rem",
        borderRadius: 12,
        background: "#ffffff",
        boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
      }}
      aria-labelledby="signup-form-heading"
    >
      <h1
        id="signup-form-heading"
        style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}
      >
        회원가입
      </h1>
      <p style={{ color: "#475569", marginBottom: "1.5rem", fontSize: "0.875rem" }}>
        비밀번호 10자 이상, 영문 대소문자·숫자·특수문자 각 1개 이상 포함.
      </p>

      <div style={{ marginBottom: "1rem" }}>
        <label
          htmlFor="signup-email"
          style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: 4 }}
        >
          이메일
        </label>
        <input
          id="signup-email"
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{
            width: "100%",
            padding: "0.5rem 0.75rem",
            border: "1px solid #cbd5e1",
            borderRadius: 6,
            fontSize: "0.875rem",
          }}
        />
      </div>

      <div style={{ marginBottom: "1rem" }}>
        <label
          htmlFor="signup-password"
          style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: 4 }}
        >
          비밀번호
        </label>
        <input
          id="signup-password"
          type="password"
          required
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{
            width: "100%",
            padding: "0.5rem 0.75rem",
            border: "1px solid #cbd5e1",
            borderRadius: 6,
            fontSize: "0.875rem",
          }}
        />
      </div>

      <div style={{ marginBottom: "1rem" }}>
        <label
          htmlFor="signup-password-confirm"
          style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: 4 }}
        >
          비밀번호 확인
        </label>
        <input
          id="signup-password-confirm"
          type="password"
          required
          autoComplete="new-password"
          value={passwordConfirm}
          onChange={(e) => setPasswordConfirm(e.target.value)}
          style={{
            width: "100%",
            padding: "0.5rem 0.75rem",
            border: "1px solid #cbd5e1",
            borderRadius: 6,
            fontSize: "0.875rem",
          }}
        />
      </div>

      <div style={{ marginBottom: "1rem" }}>
        <label
          htmlFor="signup-company"
          style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: 4 }}
        >
          회사명
        </label>
        <input
          id="signup-company"
          type="text"
          required
          minLength={1}
          maxLength={100}
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          style={{
            width: "100%",
            padding: "0.5rem 0.75rem",
            border: "1px solid #cbd5e1",
            borderRadius: 6,
            fontSize: "0.875rem",
          }}
        />
      </div>

      {error && (
        <p
          role="alert"
          style={{
            marginBottom: "1rem",
            padding: "0.75rem 1rem",
            borderRadius: 6,
            background: "#fee2e2",
            color: "#991b1b",
            fontSize: "0.875rem",
          }}
        >
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={submitting}
        style={{
          width: "100%",
          padding: "0.625rem 1rem",
          borderRadius: 6,
          background: submitting ? "#94a3b8" : "#0f172a",
          color: "#ffffff",
          fontWeight: 600,
          fontSize: "0.875rem",
          cursor: submitting ? "not-allowed" : "pointer",
          marginBottom: "0.75rem",
        }}
      >
        {submitting ? "가입 중..." : "가입하기"}
      </button>

      <div style={{ fontSize: "0.875rem", color: "#475569", textAlign: "center" }}>
        <a
          href={`/${locale}/login`}
          style={{ color: "#0f172a", textDecoration: "underline" }}
        >
          로그인으로 돌아가기
        </a>
      </div>
    </form>
  );
}
