/**
 * apps/web/components/m8-budget-variance/VarianceRow.tsx — Story 8.2
 *
 * Single variance row renderer — PRD §F8.2 verbatim.
 * 4 columns: budget / actual / difference / variance_pct + 5th severity badge.
 * Color (gray/yellow/red) follows the spec thresholds (±5% / ±10%).
 */

import { useTranslations } from "next-intl";

import {
  formatKRWTS,
  formatVariancePctTS,
  getVarianceColorClassTS,
  getVarianceTextClassTS,
  type VarianceRowSerialized,
} from "@/lib/m8-budget-variance";

interface VarianceRowProps {
  row: VarianceRowSerialized;
}

export function VarianceRow({ row }: VarianceRowProps): React.ReactElement {
  const t = useTranslations("budget_variance");
  const bgClass = getVarianceColorClassTS(row.color);
  const pctClass = getVarianceTextClassTS(row.color);

  const severityLabel =
    row.severity === "critical"
      ? t("variance_critical")
      : row.severity === "warning"
      ? t("variance_warning")
      : t("variance_normal");

  return (
    <tr className={bgClass} data-testid="variance-row">
      <td className="py-2 px-3 text-left font-medium">{row.label}</td>
      <td className="py-2 px-3 text-right tabular-nums">
        {formatKRWTS(row.budget_value)}
      </td>
      <td className="py-2 px-3 text-right tabular-nums">
        {formatKRWTS(row.actual_value)}
      </td>
      <td className="py-2 px-3 text-right tabular-nums">
        {formatKRWTS(row.difference)}
      </td>
      <td className={`py-2 px-3 text-right tabular-nums ${pctClass}`}>
        {formatVariancePctTS(row.variance_pct)}
      </td>
      <td className="py-2 px-3 text-center">{severityLabel}</td>
    </tr>
  );
}
