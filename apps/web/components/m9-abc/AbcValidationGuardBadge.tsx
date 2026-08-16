"use client";

/**
 * apps/web/components/m9-abc/AbcValidationGuardBadge.tsx — Story 9.1
 *
 * 3-layer 100% guard badge — PRD §F9.1 verbatim "[계산]이 잠기는 것" 메커니즘.
 *
 * Per AC #4 (Story 9.1):
 *  - Shows 3-layer state (cost_pool / activity / driver) as colored circles.
 *  - all_valid=True → green "계산 활성화" badge.
 *  - all_valid=False → red "계산 잠김" badge with disabled=true.
 *
 * Parent: <AbcValidationPanel>.
 */

import { useTranslations } from "next-intl";

import type { ValidationResponse } from "@/lib/m9-abc-validation";

interface AbcValidationGuardBadgeProps {
  response: ValidationResponse;
}

export function AbcValidationGuardBadge({
  response,
}: AbcValidationGuardBadgeProps): React.ReactElement {
  const t = useTranslations("abc_validation");

  const layersByTarget = new Map(response.layers.map((l) => [l.target, l]));

  const colorFor = (
    target: "cost_pool" | "activity" | "driver",
  ): string => {
    const layer = layersByTarget.get(target);
    if (layer === undefined) return "bg-gray-300";
    return layer.is_valid ? "bg-green-500" : "bg-red-500";
  };

  return (
    <div
      className="rounded border p-3"
      data-testid="abc-validation-guard-badge"
      data-all-valid={response.all_valid ? "true" : "false"}
    >
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">{t("guard_title")}</h3>
        <span
          className={
            response.all_valid
              ? "rounded bg-green-200 px-2 py-0.5 text-xs font-medium text-green-800"
              : "rounded bg-red-200 px-2 py-0.5 text-xs font-medium text-red-800"
          }
        >
          {response.all_valid
            ? t("guard_unlocked")
            : t("guard_locked")}
        </span>
      </div>

      <div className="mt-3 flex items-center gap-3">
        {(["cost_pool", "activity", "driver"] as const).map((target) => (
          <div
            key={target}
            className="flex items-center gap-1"
            data-testid={`guard-layer-${target}`}
          >
            <span
              aria-hidden="true"
              className={`inline-block h-3 w-3 rounded-full ${colorFor(target)}`}
            />
            <span className="text-xs text-gray-700">
              {t(`target_label_${target}`)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}