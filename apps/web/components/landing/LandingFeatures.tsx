/**
 * apps/web/components/landing/LandingFeatures.tsx — 6 feature cards 결정 wire.
 *
 * 1st release launch (cj-style 64번째 진입점) — T1.2 (AC #1.3) — F18.1 Marketing landing.
 * - 6 feature cards: (1) ABC 엔진 (TDABC 통합) / (2) AI 인사이트 / (3) 4-industry grants /
 *   (4) 2FA 보안 / (5) LISTEN/NOTIFY 실시간 / (6) 다중 테넌트.
 */
"use client";

import { useTranslations } from "next-intl";

interface FeatureCard {
  key: "abc" | "ai_insight" | "industry" | "two_fa" | "listen_notify" | "multi_tenant";
  title: string;
  description: string;
}

const FEATURES: ReadonlyArray<FeatureCard> = [
  {
    key: "abc",
    title: "ABC 엔진 (TDABC 통합)",
    description: "활동기준원가 계산 + 시간동인 원가배분으로 정확한 원가 분석을 제공합니다.",
  },
  {
    key: "ai_insight",
    title: "AI 인사이트",
    description: "자동 패턴 감지로 비용 절감 후보, 이상 패턴, 예측 인사이트를 생성합니다.",
  },
  {
    key: "industry",
    title: "4-industry 지원",
    description: "제조 + 제조+유통 + 서비스 + IT 4개 산업군을 지원합니다.",
  },
  {
    key: "two_fa",
    title: "2FA 보안",
    description: "TOTP 기반 2차 인증으로 계정을 안전하게 보호합니다.",
  },
  {
    key: "listen_notify",
    title: "LISTEN/NOTIFY 실시간",
    description: "PostgreSQL NOTIFY 기반 실시간 데이터 동기화로 최신 원가를 즉시 반영합니다.",
  },
  {
    key: "multi_tenant",
    title: "다중 테넌트",
    description: "RLS 기반 tenant 격리로 데이터 무결성을 보장합니다.",
  },
];

export function LandingFeatures() {
  const t = useTranslations("landing");

  return (
    <section
      style={{
        padding: "4rem 1.5rem",
        maxWidth: "72rem",
        margin: "0 auto",
      }}
      aria-labelledby="landing-features-title"
    >
      <h2
        id="landing-features-title"
        style={{
          fontSize: "1.75rem",
          fontWeight: 700,
          textAlign: "center",
          marginBottom: "3rem",
        }}
      >
        {t("features_title")}
      </h2>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(16rem, 1fr))",
          gap: "1.5rem",
        }}
      >
        {FEATURES.map((f) => (
          <article
            key={f.key}
            style={{
              padding: "1.5rem",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: "0.75rem",
              background: "rgba(255,255,255,0.03)",
            }}
          >
            <h3 style={{ fontSize: "1.125rem", fontWeight: 600, marginBottom: "0.5rem" }}>
              {f.title}
            </h3>
            <p style={{ fontSize: "0.9rem", lineHeight: 1.5, opacity: 0.8 }}>{f.description}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
