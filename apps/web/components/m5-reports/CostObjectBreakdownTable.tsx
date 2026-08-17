"use client";

/**
 * apps/web/components/m5-reports/CostObjectBreakdownTable.tsx — Story 9.4
 *
 * 4-column Cost Object Breakdown table (PRD §9 #21 + §F9.2):
 * product_id · activity_id · driver_id · allocated_krw
 *
 * Memoized for performance (re-renders only when rows change).
 */

import { useTranslations } from "next-intl";
import { memo } from "react";

import type { Report21CostObjectRow } from "@/lib/report21";

interface CostObjectBreakdownTableProps {
  rows: ReadonlyArray<Report21CostObjectRow>;
}

function formatKrw(value: string): string {
  // Decimal-as-string → KRW display (e.g., "6600000" → "6,600,000원")
  return Number(value).toLocaleString("ko-KR");
}

function CostObjectBreakdownTableImpl({
  rows,
}: CostObjectBreakdownTableProps): React.ReactElement {
  const t = useTranslations("report21");

  if (rows.length === 0) {
    return <p data-testid="report21-cost-empty">{t("cost_object_breakdown_empty")}</p>;
  }

  const total = rows.reduce(
    (acc, r) => acc + Number(r.allocated_krw),
    0,
  );

  return (
    <table data-testid="report21-cost-table">
      <thead>
        <tr>
          <th>{t("cost_object_column_product")}</th>
          <th>{t("cost_object_column_activity")}</th>
          <th>{t("cost_object_column_driver")}</th>
          <th>{t("cost_object_column_allocated")}</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={`${row.product_id}-${i}`}>
            <td>{row.product_id}</td>
            <td>{row.activity_id}</td>
            <td>{row.driver_id}</td>
            <td>
              {formatKrw(row.allocated_krw)}
              {t("cost_object_krw_unit")}
            </td>
          </tr>
        ))}
      </tbody>
      <tfoot>
        <tr>
          <td colSpan={3}>{t("cost_object_total_label")}</td>
          <td>
            {formatKrw(String(total))}
            {t("cost_object_krw_unit")}
          </td>
        </tr>
      </tfoot>
    </table>
  );
}

export const CostObjectBreakdownTable = memo(CostObjectBreakdownTableImpl);
