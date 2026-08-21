/**
 * apps/web/components/auth/ResendVerificationButton.tsx — Resend verification.
 *
 * Phase 3-1 — T3.4 (AC #2.4) — F-15.2.
 * Calls `supabase.auth.resend({ type: 'signup', email })` to re-send
 * the verification email. Disabled while submitting.
 */
"use client";

import { useState } from "react";

import { createSupabaseBrowserClient } from "@/lib/supabase/client";

export interface ResendVerificationButtonProps {
  email: string;
  locale: string;
}

export function ResendVerificationButton({
  email,
  locale,
}: ResendVerificationButtonProps) {
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleResend() {
    if (!email) {
      setMessage("이메일을 먼저 입력해 주세요.");
      return;
    }
    setSubmitting(true);
    setMessage(null);
    try {
      const supabase = createSupabaseBrowserClient();
      const { error } = await supabase.auth.resend({
        type: "signup",
        email,
        options: {
          emailRedirectTo: `${window.location.origin}/${locale}/onboarding/industry`,
        },
      });
      if (error) {
        setMessage("재발송에 실패했습니다. 잠시 후 다시 시도해 주세요.");
      } else {
        setMessage("인증 메일을 다시 보냈습니다.");
      }
    } catch {
      setMessage("네트워크 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={handleResend}
        disabled={submitting}
        style={{
          padding: "0.5rem 1rem",
          borderRadius: 6,
          background: submitting ? "#94a3b8" : "#0f172a",
          color: "#ffffff",
          fontWeight: 600,
          fontSize: "0.875rem",
          border: "none",
          cursor: submitting ? "not-allowed" : "pointer",
        }}
      >
        {submitting ? "전송 중..." : "인증 메일 재발송"}
      </button>
      {message && (
        <p
          role="status"
          style={{
            marginTop: "0.75rem",
            fontSize: "0.875rem",
            color: "#475569",
          }}
        >
          {message}
        </p>
      )}
    </div>
  );
}
