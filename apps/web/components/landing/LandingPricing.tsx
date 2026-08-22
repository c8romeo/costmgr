/**
 * apps/web/components/landing/LandingPricing.tsx — 단일 pricing tier 결정 wire.
 *
 * 1st release launch (cj-style 64번째 진입점) — T1.2 (AC #1.4) — F18.1 Marketing landing.
 * - AD-29 verbatim — "심플한 가격" + "월 1만원" + "VAT 포함" + "14일 무료 체험".
 * - ko-KR SSOT 사용 (landing.pricing_*).
 */
"use client";

import { useTranslations } from "next-intl";

export function LandingPricing() {
  const t = useTranslations("landing");

  return (
    <section
      style={{
        padding: "4rem 1.5rem",
        maxWidth: "48rem",
        margin: "0 auto",
        textAlign: "center",
      }}
      aria-labelledby="landing-pricing-title"
    >
      <h2
        id="landing-pricing-title"
        style={{
          fontSize: "1.75rem",
          fontWeight: 700,
          marginBottom: "2rem",
        }}
      >
        {t("pricing_title")}
      </h2>
      <div
        style={{
          padding: "2.5rem 2rem",
          border: "1px solid rgba(255,255,255,0.15)",
          borderRadius: "1rem",
          background: "rgba(255,255,255,0.04)",
        }}
      >
        <div
          style={{
            fontSize: "2.5rem",
            fontWeight: 700,
            marginBottom: "0.5rem",
          }}
        >
          {t("pricing_price")}
        </div>
        <div
          style={{
            fontSize: "0.95rem",
            opacity: 0.7,
            marginBottom: "1.5rem",
          }}
        >
          {t("pricing_period")}
        </div>
        <div
          style={{
            fontSize: "1rem",
            fontWeight: 600,
            color: "var(--primary, #2563eb)",
          }}
        >
          {t("trial_notice")}
        </div>
      </div>
    </section>
  );
}
