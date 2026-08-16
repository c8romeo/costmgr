"use client";

/**
 * apps/web/components/m9-abc/UnusedCapacityRow.tsx — Story 9.2
 *
 * PRD §A9 verbatim "미사용능력 X,XXX원 별도 행" 회색 배지.
 *
 * Per AC #3 (Story 9.2):
 *  - Renders unused hours + unused cost KRW with Korean thousands separator.
 *  - Gray badge differentiates from activity breakdown rows.
 *  - V8 hash badge.
 *
 * Parent: <AbcAllocationPanel>.
 */

import { useTranslations } from "next-intl";

import type { UnusedCapacityRow as UnusedCapacityRowType } from "@/lib/m9-abc-allocation";

interface UnusedCapacityRowProps {
  unused: UnusedCapacityRowType;
}

function formatKRW(value: string): string {
  const num = Number(value);
  if (!Number.isFinite(num)) return value;
  return new Intl.NumberFormat("ko-KR").format(num);
}

export function UnusedCapacityRow({
  unused,
}: UnusedCapacityRowProps): React.ReactElement {
  const t = useTranslations("abc_allocation");

  return (
    <div
      className="rounded border border-gray-300 bg-gray-100 p-3"
      data-testid="unused-capacity-row"
    >
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-gray-700">
          {t("unused_capacity_title")}
        </h4>
        <span
          className="rounded bg-gray-600 px-2 py-0.5 text-xs text-white"
          data-testid="unused-capacity-badge"
        >
          {t("unused_capacity_separate_row")}
        </span>
      </div>

      <div className="mt-2 grid grid-cols-3 gap-3 text-sm">
        <div>
          <p className="text-gray-500">{t("unused_capacity_hours_label")}</p>
          <p
            className="font-mono text-base"
            data-testid="unused-capacity-hours"
          >
            {unused.unused_hours}h
          </p>
        </div>
        <div>
          <p className="text-gray-500">{t("unused_capacity_per_hour_label")}</p>
          <p className="font-mono text-base">
            {formatKRW(unused.ccr_per_hour)}
            {t("unused_capacity_per_hour_unit")}
          </p>
        </div>
        <div>
          <p className="text-gray-500">{t("unused_capacity_cost_label")}</p>
          <p
            className="text-base font-semibold"
            data-testid="unused-capacity-cost"
          >
            {formatKRW(unused.unused_cost_krw)}
            {t("unused_capacity_cost_unit")}
          </p>
        </div>
      </div>

      <div className="mt-2 border-t pt-2">
        <p className="text-xs text-gray-500">{t("unused_capacity_hash_label")}</p>
        <p
          className="mt-1 break-all font-mono text-xs text-gray-600"
          data-testid="unused-capacity-hash"
        >
          {unused.hash}
        </p>
      </div>
    </div>
  );
}