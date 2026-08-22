/**
 * apps/web/components/onboarding/OnboardingTooltip.tsx — 4 tooltips for first-run wizard.
 *
 * 1st release launch (cj-style 64번째 진입점) — T3.2 (AC #3.2) — F18.3 Onboarding guide.
 * - first-run wizard EXTENSION 결정 wire (Epic 1 partial scaffold 정합).
 * - 4 tooltips: dashboard / 데이터 입력 / 보고서 / 2FA 설정.
 */
"use client";

import { useTranslations } from "next-intl";

export function OnboardingTooltip({ step }: { step: 1 | 2 | 3 | 4 }) {
  const t = useTranslations("onboarding");

  const messages: Record<number, string> = {
    1: "대시보드 위젯 5종을 자유롭게 추가/제거하세요",
    2: "ABC/TDABC 분석을 위한 원가 데이터를 입력하세요",
    3: "월간/분기/연간 보고서를 자동 생성합니다",
    4: "TOTP 앱으로 2차 인증을 설정하세요",
  };

  return (
    <div
      role="tooltip"
      style={{
        position: "absolute",
        background: "rgba(0,0,0,0.9)",
        color: "#fff",
        padding: "0.75rem 1rem",
        borderRadius: "0.5rem",
        fontSize: "0.875rem",
        maxWidth: "20rem",
        zIndex: 1000,
      }}
    >
      {messages[step]}
      <div style={{ fontSize: "0.75rem", opacity: 0.7, marginTop: "0.25rem" }}>
        {t("step_dashboard_title") === undefined ? "" : null}
      </div>
    </div>
  );
}
