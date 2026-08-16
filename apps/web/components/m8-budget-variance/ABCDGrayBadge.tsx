/**
 * apps/web/components/m8-budget-variance/ABCDGrayBadge.tsx — Story 8.2
 *
 * A×B×C×D 회색 배지 placeholder (PRD §15 NON-GOAL #1 + §10 M8 (b)).
 * 1차 MVP: 회색 배경 + disabled + "2차 예정" tooltip.
 * 8-3 follow-up: engine_type='abcd' retrofit foundation.
 */

import { useTranslations } from "next-intl";

import type { ABCDDisabledBadgeSerialized } from "@/lib/m8-budget-variance";

interface ABCDGrayBadgeProps {
  badge: ABCDDisabledBadgeSerialized;
}

export function ABCDGrayBadge({
  badge,
}: ABCDGrayBadgeProps): React.ReactElement {
  const t = useTranslations("budget_variance");

  return (
    <span
      className="inline-flex items-center gap-2 rounded bg-gray-300 px-3 py-1 text-sm text-gray-700"
      data-testid="abcd-gray-badge"
      title={badge.tooltip || t("abcd_badge_tooltip")}
    >
      <span aria-hidden="true">🚧</span>
      <span>{t("abcd_badge_label")}</span>
      <span aria-hidden="true">{badge.disabled ? "🔒" : ""}</span>
    </span>
  );
}
