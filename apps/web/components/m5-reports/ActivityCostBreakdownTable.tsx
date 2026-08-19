"use client";

/**
 * apps/web/components/m5-reports/ActivityCostBreakdownTable.tsx — Story 11.6
 *
 * Activity cost breakdown table (PRD §9 #15 + §7.1 ABC Step 0~3):
 *   activity_name_ko · activity_name_en · total_cost_krw · total_cost_usd ·
 *   driver_count · cost_per_driver_krw · cost_per_driver_usd
 *
 * Memoized for performance (re-renders only when rows change).
 */

import { useTranslations } from "next-intl";
import { memo } from "react";

import type { Report15ActivityCostRow } from "@/lib/report15";

interface ActivityCostBreakdownTableProps {
  rows: ReadonlyArray<Report15ActivityCostRow>;
}

function formatKrw(value: string): string {
  // Decimal-as-string → KRW display (e.g., "6600000" → "6,600,000원")
  return Number(value).toLocaleString("ko-KR");
}

function formatUsd(value: string): string {
  // Decimal-as-string → USD display (e.g., "4950" → "4,950")
  return Number(value).toLocaleString("en-US");
}

function ActivityCostBreakdownTableImpl({
  rows,
}: ActivityCostBreakdownTableProps): React.ReactElement {
  const t = useTranslations("report15");

  if (rows.length === 0) {
    return <p data-testid="report15-activity-empty">{t("activity_breakdown_empty")}</p>;
  }

  const totalKrw = rows.reduce(
    (acc, r) => acc + Number(r.total_cost_krw),
    0,
  );
  const totalUsd = rows.reduce(
    (acc, r) => acc + Number(r.total_cost_usd),
    0,
  );
  const totalDrivers = rows.reduce((acc, r) => acc + r.driver_count, 0);

  return (
    <table data-testid="report15-activity-table">
      <thead>
        <tr>
          <th>{t("activity_column_name_ko")}</th>
          <th>{t("activity_column_name_en")}</th>
          <th>{t("activity_column_total_krw")}</th>
          <th>{t("activity_column_total_usd")}</th>
          <th>{t("activity_column_driver_count")}</th>
          <th>{t("activity_column_cost_per_driver_krw")}</th>
          <th>{t("activity_column_cost_per_driver_usd")}</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={`${row.activity_id}-${i}`}>
            <td>{row.activity_name_ko}</td>
            <td>{row.activity_name_en}</td>
            <td>
              {formatKrw(row.total_cost_krw)}
              {t("krw_unit")}
            </td>
            <td>
              ${formatUsd(row.total_cost_usd)}
            </td>
            <td>{row.driver_count}</td>
            <td>
              {formatKrw(row.cost_per_driver_krw)}
              {t("krw_unit")}
            </td>
            <td>
              ${formatUsd(row.cost_per_driver_usd)}
            </td>
          </tr>
        ))}
      </tbody>
      <tfoot>
        <tr>
          <td colSpan={2}>{t("activity_total_label")}</td>
          <td>
            {formatKrw(String(totalKrw))}
            {t("krw_unit")}
          </td>
          <td>
            ${formatUsd(String(totalUsd))}
          </td>
          <td>{totalDrivers}</td>
          <td colSpan={2}>—</td>
        </tr>
      </tfoot>
    </table>
  );
}

export const ActivityCostBreakdownTable = memo(ActivityCostBreakdownTableImpl);