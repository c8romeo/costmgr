/**
 * apps/web/components/landing/LandingHero.tsx — Hero section for /landing.
 *
 * 1st release launch (cj-style 64번째 진입점) — T1.2 (AC #1.2) — F18.1 Marketing landing.
 * - Hero section + headline + sub-headline + 2 CTA buttons 결정 wire.
 * - Dark MVP / WCAG AA / Professional / ko-KR UX v1.0 정합 (memory ux-locked-decisions).
 * - D-001 actual mount validate (CR 11-4 D-001).
 */
"use client";

import { useTranslations } from "next-intl";

export function LandingHero() {
  const t = useTranslations("landing");

  return (
    <section
      style={{
        padding: "6rem 1.5rem 4rem",
        textAlign: "center",
        maxWidth: "64rem",
        margin: "0 auto",
      }}
      aria-labelledby="landing-hero-title"
    >
      <h1
        id="landing-hero-title"
        style={{
          fontSize: "clamp(2rem, 5vw, 3.5rem)",
          fontWeight: 700,
          lineHeight: 1.2,
          marginBottom: "1.25rem",
        }}
      >
        {t("title")}
      </h1>
      <p
        style={{
          fontSize: "clamp(1rem, 2vw, 1.25rem)",
          lineHeight: 1.6,
          marginBottom: "2.5rem",
          opacity: 0.85,
        }}
      >
        {t("subtitle")}
      </p>
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
            padding: "0.875rem 2rem",
            background: "var(--primary, #2563eb)",
            color: "#fff",
            borderRadius: "0.5rem",
            textDecoration: "none",
            fontWeight: 600,
          }}
        >
          {t("cta_primary")}
        </a>
        <a
          href="/ko-KR/login"
          style={{
            display: "inline-block",
            padding: "0.875rem 2rem",
            border: "1px solid currentColor",
            color: "inherit",
            borderRadius: "0.5rem",
            textDecoration: "none",
            fontWeight: 600,
          }}
        >
          {t("cta_secondary")}
        </a>
      </div>
    </section>
  );
}
