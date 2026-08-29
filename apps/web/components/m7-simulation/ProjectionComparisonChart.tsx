"use client";

/**
 * apps/web/components/m7-simulation/ProjectionComparisonChart.tsx — Story 7.2
 *
 * Recharts ComposedChart comparing baseline vs projected 4 variables:
 *   - revenue (Bar)
 *   - variable cost (Bar)
 *   - fixed cost (Bar)
 *   - after_tax_income (Line, overlay)
 *
 * Per AC #4 chart requirement. Mirrors 7-1 `CVPComparisonChart` pattern
 * (CVPSimulationClient uses table; we upgrade to ComposedChart for richer
 * projection visualization).
 */

import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface ProjectionComparisonChartProps {
  baseline: {
    projected_revenue: string;
    projected_variable_cost: string;
    projected_fixed_cost: string;
    after_tax_income: string;
  };
  sourceBaseline: {
    monthly_revenue: string;
    monthly_variable_cost: string;
    monthly_fixed_cost: string;
    after_tax_income: string;
  };
}

interface ChartDatum {
  name: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  baseline: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  projected: number;
}

export function ProjectionComparisonChart({
  baseline,
  sourceBaseline,
}: ProjectionComparisonChartProps): React.ReactElement {
  const data: ChartDatum[] = [
    {
      name: "매출",
      baseline: parseFloat(sourceBaseline.monthly_revenue) || 0,
      projected: parseFloat(baseline.projected_revenue) || 0,
    },
    {
      name: "변동비",
      baseline: parseFloat(sourceBaseline.monthly_variable_cost) || 0,
      projected: parseFloat(baseline.projected_variable_cost) || 0,
    },
    {
      name: "고정비",
      baseline: parseFloat(sourceBaseline.monthly_fixed_cost) || 0,
      projected: parseFloat(baseline.projected_fixed_cost) || 0,
    },
    {
      name: "세후이익",
      baseline: parseFloat(sourceBaseline.after_tax_income) || 0,
      projected: parseFloat(baseline.after_tax_income) || 0,
    },
  ];

  return (
    <div
      className="h-80 w-full"
      data-testid="projection-comparison-chart"
      role="img"
      aria-label="예측 결과 비교 차트 (기준 vs 추정)"
    >
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={data}
          margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="name" tick={{ fontSize: 12 }} />
          <YAxis
            tick={{ fontSize: 12 }}
            // eslint-disable-next-line @typescript-eslint/no-restricted-types
            tickFormatter={(v: number) => v.toLocaleString("ko-KR")}
          />
          <Tooltip
            // eslint-disable-next-line @typescript-eslint/no-restricted-types
            formatter={(value: number) => value.toLocaleString("ko-KR") + " 원"}
            labelStyle={{ fontWeight: "bold" }}
          />
          <Legend />
          <Bar dataKey="baseline" name="기준" fill="#9ca3af" />
          <Bar dataKey="projected" name="추정" fill="#3b82f6" />
          <Line
            type="monotone"
            dataKey="projected"
            name="추정 추세"
            stroke="#10b981"
            strokeWidth={2}
            dot={{ r: 4 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
