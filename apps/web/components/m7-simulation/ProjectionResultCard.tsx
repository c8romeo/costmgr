"use client";

/**
 * apps/web/components/m7-simulation/ProjectionResultCard.tsx — Story 7.2 (Epic 7)
 *
 * Single result card for next-month projection results. Mirrors 7-1
 * `ResultCard` (CVPSimulationClient) — shows baseline vs simulated with
 * delta indicator (↑ improved / ↓ worsened / = same).
 *
 * For projection: "improvement" depends on the metric:
 * - Revenue / after_tax_income: higher is better
 * - Variable cost / fixed cost: lower is better
 */

import { formatKRWTS } from "@/lib/m7-simulation-projection";

interface ProjectionResultCardProps {
  title: string;
  value: string;
  baseline_value?: string;
  higherIsBetter?: boolean;
  testId?: string;
}

export function ProjectionResultCard({
  title,
  value,
  // eslint-disable-next-line camelcase
  baseline_value,
  higherIsBetter = true,
  testId,
}: ProjectionResultCardProps): React.ReactElement {
  const currentValue = parseFloat(value);
  const baseValue =
    // eslint-disable-next-line camelcase
    baseline_value !== undefined ? parseFloat(baseline_value) : null;

  let arrow = "=";
  let colorClass = "text-gray-500";
  let deltaText: string | null = null;

  if (
    baseValue !== null &&
    Number.isFinite(currentValue) &&
    Number.isFinite(baseValue) &&
    baseValue !== 0
  ) {
    const delta = currentValue - baseValue;
    const deltaPct = (delta / baseValue) * 100;
    deltaText = `${delta >= 0 ? "+" : ""}${deltaPct.toFixed(2)}%`;
    if (delta === 0) {
      arrow = "=";
      colorClass = "text-gray-500";
    } else if ((higherIsBetter && delta > 0) || (!higherIsBetter && delta < 0)) {
      arrow = "↑";
      colorClass = "text-green-600";
    } else {
      arrow = "↓";
      colorClass = "text-red-600";
    }
  }

  return (
    <div
      className="rounded border p-3"
      data-testid={testId ?? "projection-result-card"}
    >
      <p className="text-sm text-gray-500">{title}</p>
      <p className="mt-1 font-mono text-lg">
        {formatKRWTS(value)} 원
      </p>
      {/* eslint-disable-next-line camelcase */}
      {baseline_value !== undefined ? (
        <p className="mt-1 text-xs text-gray-400">
          {t_baseline()}: {formatKRWTS(baseline_value)} 원
        </p>
      ) : null}
      <p className={`mt-1 text-sm ${colorClass}`} data-testid="projection-result-card-arrow">
        {arrow}
        {deltaText !== null ? ` ${deltaText}` : ""}
      </p>
    </div>
  );
}

// Local helper to avoid pulling in the translations provider for a
// simple label — we display "기준" inline as the baseline reference.
// eslint-disable-next-line @typescript-eslint/naming-convention, camelcase
function t_baseline(): string {
  return "기준";
}
