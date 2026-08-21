/**
 * apps/web/components/auth/ForgotPasswordForm.tsx — Forgot password form.
 *
 * Phase 3-1 — T6.2 (AC #5.2, #5.5) — F-15.5.
 * - Email field + [재설정 링크 보내기] button.
 * - Supabase `resetPasswordForEmail` with `redirectTo` = /<locale>/reset-password.
 * - SECURITY: Always returns 200 OK + generic success message regardless
 *   of whether the email exists, so attackers can't enumerate accounts.
 *   (AC #5.5 + AD-26 verbatim.)
 */
"use client";

import { useState } from "react";

import { requestPasswordReset } from "@/lib/auth/forgot-password";

export interface ForgotPasswordFormProps {
  locale: string;
}

export function ForgotPasswordForm({ locale }: ForgotPasswordFormProps) {
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    try {
      // SECURITY (AD-26 + AC #5.5): always show generic message regardless of
      // whether resetPasswordForEmail resolves or rejects — never leak email
      // existence to the client.
      await requestPasswordReset({ email: email.trim(), locale });
    } catch {
      // Swallow error — security invariant: UI must not reflect failure.
    } finally {
      setSubmitting(false);
      setSubmitted(true);
    }
  }

  // After submission, security invariant: always show the same generic message.
  if (submitted) {
    return (
      <section
        style={{
          maxWidth: 420,
          width: "100%",
          padding: "1.5rem",
          borderRadius: 12,
          background: "#ffffff",
          boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
        }}
      >
        <h1 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          비밀번호 찾기
        </h1>
        <p style={{ color: "#475569", fontSize: "0.875rem" }}>
          이메일이 등록된 경우, 재설정 링크가 곧 도착합니다.
        </p>
        <div style={{ marginTop: "1.5rem", fontSize: "0.875rem" }}>
          <a
            href={`/${locale}/login`}
            style={{ color: "#0f172a", textDecoration: "underline" }}
          >
            로그인으로 돌아가기
          </a>
        </div>
      </section>
    );
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
      aria-labelledby="forgot-password-heading"
    >
      <h1
        id="forgot-password-heading"
        style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}
      >
        비밀번호 찾기
      </h1>
      <p style={{ color: "#475569", marginBottom: "1.5rem", fontSize: "0.875rem" }}>
        가입한 이메일을 입력하시면 재설정 링크를 보내드립니다.
      </p>

      <div style={{ marginBottom: "1rem" }}>
        <label
          htmlFor="forgot-email"
          style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: 4 }}
        >
          이메일
        </label>
        <input
          id="forgot-email"
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
        {submitting ? "전송 중..." : "재설정 링크 보내기"}
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
