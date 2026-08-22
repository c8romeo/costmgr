/**
 * apps/web/components/onboarding/OnboardingTooltip.tsx — 4 tooltips for first-run wizard.
 *
 * 1st release launch (cj-style 64번째 진입점) — T3.2 (AC #3.2) — F18.3 Onboarding guide.
 * - first-run wizard EXTENSION 결정 wire (Epic 1 partial scaffold 정합).
 * - 4 tooltips: dashboard / 데이터 입력 / 보고서 / 2FA 설정.
 *
 * D-EPIC-16-REVIEW-DEFER-6 (L11) RESOLVED (cj-style 78번째 wire 진입 시점):
 * SSOT discipline (P-015 + CR 11-4 D-002) — tooltip strings now live in
 * `apps/web/messages/ko-KR.json` `onboarding.tooltip_*` keys and are
 * loaded via `useTranslations("onboarding")`. Removed hardcoded Korean
 * literals to prevent drift between this component and the wizard page
 * (`apps/web/app/[locale]/(auth)/onboarding/page.tsx`).
 */
"use client";

import { useTranslations } from "next-intl";

export function OnboardingTooltip({ step }: { step: 1 | 2 | 3 | 4 }) {
  const t = useTranslations("onboarding");

  const tooltipKey: Record<number, string> = {
    1: "tooltip_dashboard",
    2: "tooltip_data",
    3: "tooltip_reports",
    4: "tooltip_security",
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
      {t(tooltipKey[step])}
    </div>
  );
}
