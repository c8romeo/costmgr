"use client";

/**
 * VendorSpendAttributionChart — Phase 25 FinOps Vendor Management Spend Attribution.
 *
 * PRD §F41.7 + AD-53 (d) — Phase 22 settlement_results + Phase 24
 * budget_plan cross-join attribution with over-budget detection +
 * cross-budget reconciliation flag.
 */

import { useEffect, useState } from "react";

import { fetchVendorSpendAttribution } from "@/lib/finops/vendor-management-client";
import type { VendorSpendAttribution } from "@/lib/finops/vendor-management-types";

interface VendorSpendAttributionChartProps {
    dryRun: boolean;
}

export function VendorSpendAttributionChart({
    dryRun,
}: VendorSpendAttributionChartProps) {
    const [attributions, setAttributions] = useState<VendorSpendAttribution[]>(
        []
    );
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchVendorSpendAttribution()
            .then((data) => {
                setAttributions(data.attributions || []);
                setLoading(false);
            })
            .catch((e) => {
                setError(String(e));
                setLoading(false);
            });
    }, []);

    if (loading) {
        return (
            <div className="text-slate-400">Loading spend attribution...</div>
        );
    }
    if (error) {
        return (
            <div className="text-rose-400" role="alert">
                Error: {error}
            </div>
        );
    }

    const totalActual = attributions.reduce(
        (sum, a) => sum + a.actual_amount,
        0
    );
    const totalBudget = attributions.reduce(
        (sum, a) => sum + a.budget_amount,
        0
    );
    const overBudgetCount = attributions.filter((a) => a.over_budget).length;

    return (
        <section
            aria-label="Vendor spend attribution"
            className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
        >
            <h2 className="text-lg font-semibold text-slate-900">
                Vendor Spend Attribution
            </h2>

            <dl className="mt-4 grid grid-cols-3 gap-4 text-sm">
                <div className="rounded-lg bg-slate-50 p-3">
                    <dt className="font-medium text-slate-700">
                        Total Actual (KRW)
                    </dt>
                    <dd className="text-xl font-bold text-slate-900">
                        {totalActual.toLocaleString()}
                    </dd>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                    <dt className="font-medium text-slate-700">
                        Total Budget (KRW)
                    </dt>
                    <dd className="text-xl font-bold text-blue-600">
                        {totalBudget.toLocaleString()}
                    </dd>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                    <dt className="font-medium text-slate-700">Over Budget</dt>
                    <dd
                        className={`text-xl font-bold ${
                            overBudgetCount > 0 ? "text-rose-600" : "text-emerald-600"
                        }`}
                    >
                        {overBudgetCount}
                    </dd>
                </div>
            </dl>

            <div className="mt-6 overflow-x-auto">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-slate-200">
                            <th className="py-2 text-left font-medium text-slate-700">
                                Vendor
                            </th>
                            <th className="py-2 text-left font-medium text-slate-700">
                                Period
                            </th>
                            <th className="py-2 text-right font-medium text-slate-700">
                                Actual
                            </th>
                            <th className="py-2 text-right font-medium text-slate-700">
                                Budget
                            </th>
                            <th className="py-2 text-right font-medium text-slate-700">
                                Variance
                            </th>
                            <th className="py-2 text-right font-medium text-slate-700">
                                Variance %
                            </th>
                            <th className="py-2 text-center font-medium text-slate-700">
                                Reconciled
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {attributions.slice(0, 10).map((a) => (
                            <tr
                                key={a.attribution_id}
                                className="border-b border-slate-100"
                            >
                                <td className="py-2 font-mono text-xs text-slate-700">
                                    {a.vendor_id.slice(0, 8)}
                                </td>
                                <td className="py-2 text-slate-700">
                                    {a.period_key}
                                </td>
                                <td className="py-2 text-right">
                                    {a.actual_amount.toLocaleString()}
                                </td>
                                <td className="py-2 text-right">
                                    {a.budget_amount.toLocaleString()}
                                </td>
                                <td
                                    className={`py-2 text-right ${
                                        a.over_budget ? "text-rose-600" : "text-emerald-600"
                                    }`}
                                >
                                    {a.variance_amount.toLocaleString()}
                                </td>
                                <td className="py-2 text-right">
                                    {a.variance_pct.toFixed(1)}%
                                </td>
                                <td className="py-2 text-center">
                                    {a.cross_budget_reconciled ? (
                                        <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
                                            Yes
                                        </span>
                                    ) : (
                                        <span className="text-xs text-slate-500">
                                            No
                                        </span>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </section>
    );
}