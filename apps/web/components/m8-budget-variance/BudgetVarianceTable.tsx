/**
 * apps/web/components/m8-budget-variance/BudgetVarianceTable.tsx — Story 8.2
 *
 * Main budget-actual variance table container (PRD §F8.2 verbatim).
 *
 * 5-column table:
 *   - label (항목)
 *   - budget_value (예산)
 *   - actual_value (실적)
 *   - difference (차액)
 *   - variance_pct (차이율 %)
 *
 * Plus 6th column (severity) for accessibility + 7th 5-column ABCD 회색 배지.
 * 합계 row always present at the bottom.
 *
 * Composition: <ABCDGrayBadge> + <VarianceRow> × N + <VarianceSummary> + <VariancePdfButton>
 */

"use client";

import { useTranslations } from "next-intl";

import { ABCDGrayBadge } from "@/components/m8-budget-variance/ABCDGrayBadge";
import { VariancePdfButton } from "@/components/m8-budget-variance/VariancePdfButton";
import { VarianceRow } from "@/components/m8-budget-variance/VarianceRow";
import { VarianceSummary } from "@/components/m8-budget-variance/VarianceSummary";
import type { VarianceTableResponse } from "@/lib/m8-budget-variance";

interface BudgetVarianceTableProps {
  initialTable: VarianceTableResponse | null;
  accessToken: string | undefined;
  initialError: string | null;
}

export function BudgetVarianceTable({
  initialTable,
  accessToken,
  initialError,
}: BudgetVarianceTableProps): React.ReactElement {
  const t = useTranslations("budget_variance");

  if (initialError || !initialTable) {
    return (
      <main className="p-6">
        <h1 className="text-2xl font-semibold">{t("page_title")}</h1>
        <p className="mt-3 text-sm text-red-600">
          {t("load_failed")}{" "}
          {initialError ? `(${initialError})` : ""}
        </p>
      </main>
    );
  }

  {/* eslint-disable-next-line camelcase */}
  const { rows, total_row, abcd_disabled_badge, abcd_disabled_note } =
    initialTable;

  return (
    <main className="p-6">
      <h1 className="text-2xl font-semibold">{t("page_title")}</h1>
      <p className="mt-1 text-sm text-gray-600">{t("page_subtitle")}</p>

      <section className="mt-6 rounded border p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">{t("panel_title")}</h2>
          {/* eslint-disable-next-line camelcase */}
          <ABCDGrayBadge badge={abcd_disabled_badge} />
        </div>
        <p className="mt-2 text-sm text-gray-600">
          {t("panel_description")}
        </p>
        {/* eslint-disable-next-line camelcase */}
        <p className="mt-1 text-xs text-gray-500">{abcd_disabled_note}</p>

        {rows.length === 0 ? (
          <p className="mt-3 text-sm text-gray-500">{t("empty_message")}</p>
        ) : (
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="py-2 px-3 text-left">{t("col_label")}</th>
                  <th className="py-2 px-3 text-right">{t("col_budget")}</th>
                  <th className="py-2 px-3 text-right">{t("col_actual")}</th>
                  <th className="py-2 px-3 text-right">
                    {t("col_difference")}
                  </th>
                  <th className="py-2 px-3 text-right">
                    {t("col_variance_pct")}
                  </th>
                  <th className="py-2 px-3 text-center">
                    {t("col_severity")}
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, idx) => (
                  // Use label+idx for the key — period_key is unique per scenario.
                  <VarianceRow key={`${r.label}-${idx}`} row={r} />
                ))}
                {/* eslint-disable-next-line camelcase */}
                <VarianceSummary totalRow={total_row} />
              </tbody>
            </table>
          </div>
        )}

        <VariancePdfButton
          accessToken={accessToken}
          periodKey={initialTable.period_key}
          envelope={null}
        />
      </section>
    </main>
  );
}
