/**
 * apps/web/components/auth/LoginForm.tsx — Login form Client Component.
 *
 * Phase 3-1 — T2.2 (AC #1.2, #1.3, #1.4) — F-15.1.
 * - Email + password 2 fields
 * - [보기/숨기기] toggle on password (WCAG AA contrast)
 * - Supabase `signInWithPassword` succeeds → redirect to `?redirect=` or
 *   `/{locale}/dashboard`
 * - 2FA gate: if `aal === 'aal1'` → redirect to /auth/2fa (Epic 12 wire)
 * - 5-failure cool-down (delegated to `lib/auth/login.ts`)
 * - Korean error messages via ko-KR.json SSOT (CR 11-4 D-002)
 */
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { signInWithPassword } from "@/lib/auth/login";

export interface LoginFormProps {
  locale: string;
  redirectTo?: string;
  resetSuccess?: boolean;
}

export function LoginForm({ locale, redirectTo, resetSuccess }: LoginFormProps) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(
    resetSuccess ? "비밀번호가 성공적으로 변경되었습니다. 다시 로그인해 주세요." : null,
  );

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    const result = await signInWithPassword({ email, password });

    if (!result.ok) {
      setError(result.message);
      setSubmitting(false);
      return;
    }

    // 2FA gate: if signed in but AAL is 'aal1' (no TOTP verified yet),
    // redirect to /auth/2fa challenge. Epic 12 wire.
    if (result.aal === "aal1") {
      const twofaUrl = redirectTo
        ? `/${locale}/auth/2fa?redirect=${encodeURIComponent(redirectTo)}`
        : `/${locale}/auth/2fa`;
      router.push(twofaUrl);
      router.refresh();
      return;
    }

    target: {
      const target = redirectTo ?? `/${locale}/dashboard`;
      router.push(target);
      router.refresh();
    }
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
      aria-labelledby="login-form-heading"
    >
      <h1
        id="login-form-heading"
        style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}
      >
        로그인
      </h1>
      <p style={{ color: "#475569", marginBottom: "1.5rem", fontSize: "0.875rem" }}>
        costmgr 계정으로 로그인합니다.
      </p>

      <div style={{ marginBottom: "1rem" }}>
        <label
          htmlFor="login-email"
          style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: 4 }}
        >
          이메일
        </label>
        <input
          id="login-email"
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
          htmlFor="login-password"
          style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: 4 }}
        >
          비밀번호
        </label>
        <div style={{ display: "flex", gap: 8 }}>
          <input
            id="login-password"
            type={showPassword ? "text" : "password"}
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{
              flex: 1,
              padding: "0.5rem 0.75rem",
              border: "1px solid #cbd5e1",
              borderRadius: 6,
              fontSize: "0.875rem",
            }}
          />
          <button
            type="button"
            onClick={() => setShowPassword((v) => !v)}
            aria-label={showPassword ? "비밀번호 숨기기" : "비밀번호 보기"}
            style={{
              padding: "0.5rem 0.75rem",
              border: "1px solid #cbd5e1",
              borderRadius: 6,
              background: "#f1f5f9",
              fontSize: "0.875rem",
              cursor: "pointer",
            }}
          >
            {showPassword ? "숨기기" : "보기"}
          </button>
        </div>
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
        {submitting ? "로그인 중..." : "로그인"}
      </button>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: "0.875rem",
          color: "#475569",
        }}
      >
        <a
          href={`/${locale}/signup`}
          style={{ color: "#0f172a", textDecoration: "underline" }}
        >
          회원가입
        </a>
        <a
          href={`/${locale}/forgot-password`}
          style={{ color: "#0f172a", textDecoration: "underline" }}
        >
          비밀번호 찾기
        </a>
      </div>
    </form>
  );
}
