"use client";

/**
 * BudgetVsActualTrendChart — Phase 24 FinOps Budget Planning variance trend chart.
 *
 * PRD §F40.4 + AD-52 (d) — 12-month Recharts LineChart visualization.
 * Shows budget vs actual + variance % over 12 months.
 */

import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from "recharts";

interface TrendRow {
    month: string;
    budget: number;
    actual: number;
    variance_pct: number;
}

// Demo data — 12-month trend (placeholder)
const DEMO_TREND: TrendRow[] = Array.from({ length: 12 }, (_, i) => ({
    month: `M${String(i + 1).padStart(2, "0")}`,
    budget: 5_000_000,
    actual: 5_000_000 + Math.floor(Math.random() * 1_500_000 - 250_000),
    variance_pct: Math.random() * 25 - 5,
}));

export function BudgetVsActualTrendChart() {
    return (
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
            <h2 className="mb-3 text-lg font-medium text-slate-100">
                Budget vs Actual Trend (12-month)
            </h2>
            <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={DEMO_TREND}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="month" stroke="#94a3b8" />
                        <YAxis stroke="#94a3b8" />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: "#0f172a",
                                border: "1px solid #334155",
                            }}
                        />
                        <Legend />
                        <Line
                            type="monotone"
                            dataKey="budget"
                            stroke="#10b981"
                            strokeWidth={2}
                            name="Budget (KRW)"
                        />
                        <Line
                            type="monotone"
                            dataKey="actual"
                            stroke="#ef4444"
                            strokeWidth={2}
                            name="Actual (KRW)"
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}

export default BudgetVsActualTrendChart;
