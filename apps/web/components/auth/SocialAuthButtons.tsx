/**
 * apps/web/components/auth/SocialAuthButtons.tsx — 3-provider OAuth buttons.
 *
 * Epic 15 — T3.2 (AC #2.2) — F17.2 Social OAuth buttons.
 * - Google + Naver + Kakao buttons (provider-specific branding).
 * - Each button calls `signInWithSocialOAuth(provider)` (lib/auth/social.ts).
 * - 3-attempt cool-down per provider (delegated to the wrapper).
 */
"use client";

import { useState } from "react";

import {
  ALLOWED_SOCIAL_PROVIDERS,
  signInWithSocialOAuth,
  type AllowedSocialProvider,
} from "@/lib/auth/social";

const PROVIDER_LABELS: Record<AllowedSocialProvider, string> = {
  google: "구글로 계속하기",
  naver: "네이버로 계속하기",
  kakao: "카카오로 계속하기",
};

const PROVIDER_GLYPHS: Record<AllowedSocialProvider, string> = {
  google: "G",
  naver: "N",
  kakao: "K",
};

const PROVIDER_BACKGROUND: Record<AllowedSocialProvider, string> = {
  google: "#ffffff",
  naver: "#03c75a",
  kakao: "#fee500",
};

const PROVIDER_TEXT_COLOR: Record<AllowedSocialProvider, string> = {
  google: "#1f2937",
  naver: "#ffffff",
  kakao: "#000000",
};

export interface SocialAuthButtonsProps {
  locale: string;
  /** Optional divider label (defaults to "또는"). */
  dividerLabel?: string;
}

export function SocialAuthButtons({ locale, dividerLabel = "또는" }: SocialAuthButtonsProps) {
  const [submittingProvider, setSubmittingProvider] = useState<AllowedSocialProvider | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleProvider(provider: AllowedSocialProvider) {
    setSubmittingProvider(provider);
    setError(null);
    const result = await signInWithSocialOAuth({ provider, locale });
    if (!result.ok) {
      setSubmittingProvider(null);
      setError(result.message);
    }
    // On success the wrapper navigates via Supabase redirect — no further action.
  }

  return (
    <div style={{ width: "100%" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          margin: "1.25rem 0 1rem",
          color: "#94a3b8",
          fontSize: "0.75rem",
        }}
        aria-hidden="true"
      >
        <div style={{ flex: 1, height: 1, background: "#e2e8f0" }} />
        <span>{dividerLabel}</span>
        <div style={{ flex: 1, height: 1, background: "#e2e8f0" }} />
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {(Array.from(ALLOWED_SOCIAL_PROVIDERS) as AllowedSocialProvider[]).map((provider) => {
          const isSubmitting = submittingProvider === provider;
          return (
            <button
              key={provider}
              type="button"
              onClick={() => handleProvider(provider)}
              disabled={submittingProvider !== null}
              aria-label={PROVIDER_LABELS[provider]}
              data-provider={provider}
              style={{
                width: "100%",
                padding: "0.625rem 1rem",
                borderRadius: 6,
                border: provider === "google" ? "1px solid #cbd5e1" : "1px solid transparent",
                background: isSubmitting ? "#94a3b8" : PROVIDER_BACKGROUND[provider],
                color: PROVIDER_TEXT_COLOR[provider],
                fontWeight: 600,
                fontSize: "0.875rem",
                cursor: submittingProvider !== null ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 8,
              }}
            >
              <span
                aria-hidden="true"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: 20,
                  height: 20,
                  borderRadius: 4,
                  background: provider === "google" ? "#ffffff" : "rgba(255,255,255,0.2)",
                  color: provider === "google" ? "#1f2937" : PROVIDER_TEXT_COLOR[provider],
                  fontWeight: 700,
                  fontSize: "0.75rem",
                }}
              >
                {PROVIDER_GLYPHS[provider]}
              </span>
              {isSubmitting ? "로그인 중..." : PROVIDER_LABELS[provider]}
            </button>
          );
        })}
      </div>

      {error && (
        <p
          role="alert"
          style={{
            marginTop: "0.75rem",
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
    </div>
  );
}
