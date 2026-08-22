/**
 * apps/web/components/auth/MagicLinkForm.tsx — Magic link request form.
 *
 * Epic 15 — T2.1 (AC #1.2) — F17.1 Magic link UI.
 * - Single email field + send button (D-001 actual mount, no stubs).
 * - Calls `sendMagicLink()` (lib/auth/magic-link.ts).
 * - 2FA gate handled by the auth-callback page after link click.
 * - Korean copy via ko-KR.json SSOT (CR 11-4 D-002 lesson carry).
 */
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { sendMagicLink } from "@/lib/auth/magic-link";

export interface MagicLinkFormProps {
  locale: string;
  redirectTo?: string;
}

export function MagicLinkForm({ locale, redirectTo }: MagicLinkFormProps) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setMessage(null);

    const result = await sendMagicLink({ email, locale });

    // Security invariant: always navigate to the success page (never reveal
    // whether the email is registered).
    if (result.ok) {
      const target = redirectTo
        ? `/${locale}/magic-link-sent?redirect=${encodeURIComponent(redirectTo)}`
        : `/${locale}/magic-link-sent`;
      router.push(target);
      return;
    }

    setSubmitting(false);
    setMessage(result.message);
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
      aria-labelledby="magic-link-form-heading"
    >
      <h1
        id="magic-link-form-heading"
        style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}
      >
        매직 링크로 로그인
      </h1>
      <p style={{ color: "#475569", marginBottom: "1.5rem", fontSize: "0.875rem" }}>
        이메일로 전송된 링크를 클릭하면 로그인됩니다.
      </p>

      <div style={{ marginBottom: "1rem" }}>
        <label
          htmlFor="magic-link-email"
          style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: 4 }}
        >
          이메일 주소
        </label>
        <input
          id="magic-link-email"
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

      {message && (
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
          {message}
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
        {submitting ? "전송 중..." : "매직 링크 전송"}
      </button>

      <div
        style={{
          textAlign: "center",
          fontSize: "0.875rem",
          color: "#475569",
        }}
      >
        <a
          href={`/${locale}/login`}
          style={{ color: "#0f172a", textDecoration: "underline" }}
        >
          비밀번호 로그인으로 돌아가기
        </a>
      </div>
    </form>
  );
}
