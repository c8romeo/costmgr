/**
 * apps/web/components/auth/LogoutButton.tsx — Logout button Client Component.
 *
 * Phase 3-1 — T5.2 (AC #4.1, #4.2) — F-15.4.
 * Calls POST /api/v1/auth/logout (or the locale-prefixed /api/v1/.../auth/logout)
 * and redirects to /login on success. Designed for sidebar / dashboard header.
 */
"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export interface LogoutButtonProps {
  locale: string;
  className?: string;
}

export function LogoutButton({ locale, className }: LogoutButtonProps) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleLogout() {
    setSubmitting(true);
    setError(null);
    try {
      const response = await fetch(`/${locale}/api/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (!response.ok) {
        const body = (await response.json().catch(() => ({}))) as { code?: string };
        if (body.code === "NETWORK_ERROR") {
          setError("네트워크 오류로 로그아웃하지 못했습니다.");
        } else {
          setError("로그아웃에 실패했습니다. 잠시 후 다시 시도해 주세요.");
        }
        setSubmitting(false);
        return;
      }
      const body = (await response.json()) as { redirect?: string };
      router.push(body.redirect ?? `/${locale}/login`);
      router.refresh();
    } catch {
      setError("네트워크 오류로 로그아웃하지 못했습니다.");
      setSubmitting(false);
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={handleLogout}
        disabled={submitting}
        className={className}
        style={{
          padding: "0.5rem 1rem",
          borderRadius: 6,
          border: "1px solid #cbd5e1",
          background: "#ffffff",
          color: "#0f172a",
          fontWeight: 600,
          fontSize: "0.875rem",
          cursor: submitting ? "not-allowed" : "pointer",
        }}
      >
        {submitting ? "로그아웃 중..." : "로그아웃"}
      </button>
      {error && (
        <p
          role="alert"
          style={{
            marginTop: "0.5rem",
            fontSize: "0.875rem",
            color: "#991b1b",
          }}
        >
          {error}
        </p>
      )}
    </div>
  );
}
