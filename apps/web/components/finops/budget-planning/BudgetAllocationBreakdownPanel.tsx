"use client";

/**
 * BudgetAllocationBreakdownPanel — Phase 24 FinOps Budget Planning 5-dim pie chart.
 *
 * PRD §F40.4 + AD-52 (d) — 5-dim Recharts PieChart visualization.
 * Shows allocation breakdown across cost_center 0.30 + department 0.25 +
 * business_unit 0.20 + tag 0.15 + tenant 0.10.
 */

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";

const DIMENSION_WEIGHTS = [
    { name: "cost_center", weight: 0.30, color: "#10b981" },
    { name: "department", weight: 0.25, color: "#3b82f6" },
    { name: "business_unit", weight: 0.20, color: "#f59e0b" },
    { name: "tag", weight: 0.15, color: "#ef4444" },
    { name: "tenant", weight: 0.10, color: "#8b5cf6" },
];

export function BudgetAllocationBreakdownPanel() {
    return (
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
            <h2 className="mb-3 text-lg font-medium text-slate-100">
                Allocation Breakdown (5-dim)
            </h2>
            <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={DIMENSION_WEIGHTS}
                            dataKey="weight"
                            nameKey="name"
                            cx="50%"
                            cy="50%"
                            outerRadius={100}
                            label={(entry) => `${entry.name} (${(entry.weight * 100).toFixed(0)}%)`}
                        >
                            {DIMENSION_WEIGHTS.map((entry) => (
                                <Cell key={entry.name} fill={entry.color} />
                            ))}
                        </Pie>
                        {/* eslint-disable-next-line @typescript-eslint/no-restricted-types */}
                        <Tooltip formatter={(value: number) => `${(value * 100).toFixed(0)}%`} />
                        <Legend />
                    </PieChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}

export default BudgetAllocationBreakdownPanel;
