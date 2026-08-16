/**
 * apps/web/components/m8-budget-variance/VarianceSummary.tsx — Story 8.2
 *
 * 합계 row renderer — PRD §F8.2 verbatim.
 * Always rendered at the bottom of the variance table (테이블 하단 합계 row).
 * Identical layout to <VarianceRow> but with `is_total` flag.
 */

import { useTranslations } from "next-intl";

import {
  formatKRWTS,
  formatVariancePctTS,
  getVarianceColorClassTS,
  getVarianceTextClassTS,
  type VarianceRowSerialized,
} from "@/lib/m8-budget-variance";

interface VarianceSummaryProps {
  totalRow: VarianceRowSerialized;
}

export function VarianceSummary({
  totalRow,
}: VarianceSummaryProps): React.ReactElement {
  const t = useTranslations("budget_variance");
  const bgClass = getVarianceColorClassTS(totalRow.color);
  const pctClass = getVarianceTextClassTS(totalRow.color);

  const severityLabel =
    totalRow.severity === "critical"
      ? t("variance_critical")
      : totalRow.severity === "warning"
      ? t("variance_warning")
      : t("variance_normal");

  return (
    <tr
      className={`${bgClass} border-t-2 border-gray-400 font-semibold`}
      data-testid="variance-summary-total"
    >
      <td className="py-2 px-3 text-left">{t("total_row_label")}</td>
      <td className="py-2 px-3 text-right tabular-nums">
        {formatKRWTS(totalRow.budget_value)}
      </td>
      <td className="py-2 px-3 text-right tabular-nums">
        {formatKRWTS(totalRow.actual_value)}
      </td>
      <td className="py-2 px-3 text-right tabular-nums">
        {formatKRWTS(totalRow.difference)}
      </td>
      <td className={`py-2 px-3 text-right tabular-nums ${pctClass}`}>
        {formatVariancePctTS(totalRow.variance_pct)}
      </td>
      <td className="py-2 px-3 text-center">{severityLabel}</td>
    </tr>
  );
}
