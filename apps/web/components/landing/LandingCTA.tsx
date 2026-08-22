/**
 * apps/web/components/landing/LandingCTA.tsx — Final CTA buttons.
 *
 * 1st release launch (cj-style 64번째 진입점) — T1.2 (AC #1.5) — F18.1 Marketing landing.
 * - signup CTA button (`/signup` redirect) + login CTA button (`/login` redirect).
 * - UX v1.0 정합 (Primary / Secondary 버튼 styling 결정).
 */
"use client";

import { useTranslations } from "next-intl";

export function LandingCTA() {
  const t = useTranslations("landing");

  return (
    <section
      style={{
        padding: "4rem 1.5rem 6rem",
        textAlign: "center",
      }}
    >
      <div
        style={{
          display: "flex",
          gap: "1rem",
          justifyContent: "center",
          flexWrap: "wrap",
        }}
      >
        <a
          href="/ko-KR/signup"
          style={{
            display: "inline-block",
            padding: "1rem 2.5rem",
            background: "var(--primary, #2563eb)",
            color: "#fff",
            borderRadius: "0.5rem",
            textDecoration: "none",
            fontWeight: 600,
            fontSize: "1.05rem",
          }}
        >
          {t("cta_primary")}
        </a>
        <a
          href="/ko-KR/login"
          style={{
            display: "inline-block",
            padding: "1rem 2.5rem",
            border: "1px solid currentColor",
            color: "inherit",
            borderRadius: "0.5rem",
            textDecoration: "none",
            fontWeight: 600,
            fontSize: "1.05rem",
          }}
        >
          {t("cta_secondary")}
        </a>
      </div>
    </section>
  );
}
