/**
 * apps/web/components/auth/ResetPasswordForm.tsx — Reset password form.
 *
 * Phase 3-1 — T6.4 (AC #5.3, #5.4, #5.5) — F-15.5.
 * - New password + confirm 2 fields.
 * - F-15.2-(b) strength regex (10+ chars, lower + upper + digit + special).
 * - `supabase.auth.updateUser({ password })` then redirect to /login?reset=success.
 * - Backend audit INSERT (`action_name='password_reset'`) is best-effort.
 */
"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { resetPassword } from "@/lib/auth/reset-password";

export interface ResetPasswordFormProps {
  locale: string;
  code: string;
}

export function ResetPasswordForm({ locale, code }: ResetPasswordFormProps) {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    const result = await resetPassword({
      code,
      password,
      passwordConfirm,
    });

    if (!result.ok) {
      setError(result.message);
      setSubmitting(false);
      return;
    }

    router.push(`/${locale}/login?reset=success`);
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
      aria-labelledby="reset-password-heading"
    >
      <h1
        id="reset-password-heading"
        style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}
      >
        비밀번호 재설정
      </h1>
      <p style={{ color: "#475569", marginBottom: "1.5rem", fontSize: "0.875rem" }}>
        새 비밀번호를 입력해 주세요.
      </p>

      <div style={{ marginBottom: "1rem" }}>
        <label
          htmlFor="reset-password"
          style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: 4 }}
        >
          새 비밀번호
        </label>
        <input
          id="reset-password"
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
          htmlFor="reset-password-confirm"
          style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: 4 }}
        >
          비밀번호 확인
        </label>
        <input
          id="reset-password-confirm"
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
        }}
      >
        {submitting ? "변경 중..." : "비밀번호 변경"}
      </button>
    </form>
  );
}
