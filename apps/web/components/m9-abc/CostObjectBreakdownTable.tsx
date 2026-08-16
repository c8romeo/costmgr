"use client";

/**
 * apps/web/components/m9-abc/CostObjectBreakdownTable.tsx — Story 9.2
 *
 * PRD §F9.2 Cost Object Breakdown 4컬럼 테이블 (원가풀·활동·동인·배부액).
 *
 * Per AC #4 (Story 9.2):
 *  - 4컬럼: 상품(product_id) + 활동(activity_id) + 동인(driver_id) + 배부액(allocated_krw).
 *  - Σ balance row at the bottom showing total breakdown sum.
 *  - V7 balance check (is_balanced) shown as badge.
 *
 * Parent: <AbcAllocationPanel>.
 */

import { useTranslations } from "next-intl";

import type {
  CostObjectRow as CostObjectRowType,
  ActivityMapping,
} from "@/lib/m9-abc-allocation";

interface CostObjectBreakdownTableProps {
  activityMappings: ActivityMapping[];
  rows: CostObjectRowType[];
  totalBreakdownSum: string;
  isBalanced: boolean;
}

function formatKRW(value: string): string {
  const num = Number(value);
  if (!Number.isFinite(num)) return value;
  return new Intl.NumberFormat("ko-KR").format(num);
}

export function CostObjectBreakdownTable({
  activityMappings,
  rows,
  totalBreakdownSum,
  isBalanced,
}: CostObjectBreakdownTableProps): React.ReactElement {
  const t = useTranslations("abc_allocation");

  // Build lookup from activity_id → CCR amount for breadcrumb-style display.
  const activityLookup = new Map<string, ActivityMapping>();
  for (const m of activityMappings) {
    activityLookup.set(m.activity_id, m);
  }

  return (
    <div
      className="rounded border border-gray-300 p-4"
      data-testid="cost-object-breakdown-table"
    >
      <div className="flex items-center justify-between">
        <h3 className="text-base font-medium">
          {t("cost_object_breakdown_title")}
        </h3>
        <span
          className={`rounded px-2 py-0.5 text-xs text-white ${
            isBalanced ? "bg-green-600" : "bg-red-600"
          }`}
          data-testid="cost-object-breakdown-balance-badge"
        >
          {isBalanced
            ? t("cost_object_breakdown_balanced")
            : t("cost_object_breakdown_unbalanced")}
        </span>
      </div>

      <table className="mt-3 w-full text-sm">
        <thead>
          <tr className="border-b">
            <th className="py-1 text-left">{t("cost_object_column_product")}</th>
            <th className="py-1 text-left">{t("cost_object_column_activity")}</th>
            <th className="py-1 text-left">{t("cost_object_column_driver")}</th>
            <th className="py-1 text-right">{t("cost_object_column_allocated")}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => {
            const mapping = activityLookup.get(row.activity_id);
            return (
              <tr
                key={`${row.product_id}-${row.activity_id}-${idx}`}
                className="border-b"
                data-testid="cost-object-breakdown-row"
              >
                <td className="py-1 font-mono">{row.product_id}</td>
                <td className="py-1 font-mono">
                  {row.activity_id}
                  {mapping !== undefined ? (
                    <span className="ml-1 text-xs text-gray-500">
                      ({mapping.hours}h)
                    </span>
                  ) : null}
                </td>
                <td className="py-1 font-mono">{row.driver_id}</td>
                <td
                  className="py-1 text-right font-mono"
                  data-testid="cost-object-breakdown-allocated"
                >
                  {formatKRW(row.allocated_krw)}
                  {t("cost_object_krw_unit")}
                </td>
              </tr>
            );
          })}
        </tbody>
        <tfoot>
          <tr className="border-t-2">
            <td colSpan={3} className="py-1 text-right text-sm font-medium">
              {t("cost_object_total_label")}
            </td>
            <td
              className="py-1 text-right font-mono font-semibold"
              data-testid="cost-object-breakdown-total"
            >
              {formatKRW(totalBreakdownSum)}
              {t("cost_object_krw_unit")}
            </td>
          </tr>
        </tfoot>
      </table>

      {rows.length === 0 ? (
        <p
          className="mt-3 text-sm text-gray-500"
          data-testid="cost-object-breakdown-empty"
        >
          {t("cost_object_breakdown_empty")}
        </p>
      ) : null}
    </div>
  );
}