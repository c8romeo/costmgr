"use client";

/**
 * VendorPerformanceScorecardTable — Phase 25 FinOps Vendor Management Performance Scorecard.
 *
 * PRD §F41.4 + AD-53 (d) — 4-dim performance scoring
 * (sla_compliance 0.30 + cost_efficiency 0.25 + support_quality 0.25 +
 * innovation 0.20) + 3-tier severity (excellent / needs_improvement /
 * critical) + monthly + quarterly cadence.
 */

import { useEffect, useState } from "react";

import { fetchVendorPerformance } from "@/lib/finops/vendor-management-client";
import type { VendorPerformanceScorecard } from "@/lib/finops/vendor-management-types";

interface VendorPerformanceScorecardTableProps {
    dryRun: boolean;
}

const SEVERITY_COLORS: Record<string, string> = {
    excellent: "bg-emerald-100 text-emerald-700",
    needs_improvement: "bg-amber-100 text-amber-700",
    critical: "bg-rose-100 text-rose-700",
};

export function VendorPerformanceScorecardTable({
    dryRun,
}: VendorPerformanceScorecardTableProps) {
    const [scorecards, setScorecards] = useState<VendorPerformanceScorecard[]>(
        []
    );
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchVendorPerformance()
            .then((data) => {
                setScorecards(data.scorecards || []);
                setLoading(false);
            })
            .catch((e) => {
                setError(String(e));
                setLoading(false);
            });
    }, []);

    if (loading) {
        return <div className="text-slate-400">Loading scorecards...</div>;
    }
    if (error) {
        return (
            <div className="text-rose-400" role="alert">
                Error: {error}
            </div>
        );
    }

    return (
        <section
            aria-label="Vendor performance scorecards"
            className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
        >
            <h2 className="text-lg font-semibold text-slate-900">
                Vendor Performance Scorecard
            </h2>

            <div className="mt-4 overflow-x-auto">
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
                                SLA
                            </th>
                            <th className="py-2 text-right font-medium text-slate-700">
                                Cost Eff.
                            </th>
                            <th className="py-2 text-right font-medium text-slate-700">
                                Support
                            </th>
                            <th className="py-2 text-right font-medium text-slate-700">
                                Innovation
                            </th>
                            <th className="py-2 text-right font-medium text-slate-700">
                                Total
                            </th>
                            <th className="py-2 text-center font-medium text-slate-700">
                                Severity
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {scorecards.slice(0, 10).map((s) => (
                            <tr
                                key={s.scorecard_id}
                                className="border-b border-slate-100"
                            >
                                <td className="py-2 font-mono text-xs text-slate-700">
                                    {s.vendor_id.slice(0, 8)}
                                </td>
                                <td className="py-2 text-slate-700">
                                    {s.period_key}
                                </td>
                                <td className="py-2 text-right">
                                    {s.sla_compliance_score.toFixed(1)}
                                </td>
                                <td className="py-2 text-right">
                                    {s.cost_efficiency_score.toFixed(1)}
                                </td>
                                <td className="py-2 text-right">
                                    {s.support_quality_score.toFixed(1)}
                                </td>
                                <td className="py-2 text-right">
                                    {s.innovation_score.toFixed(1)}
                                </td>
                                <td className="py-2 text-right font-bold text-blue-600">
                                    {s.weighted_total_score.toFixed(2)}
                                </td>
                                <td className="py-2 text-center">
                                    <span
                                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                                            SEVERITY_COLORS[s.severity] ||
                                            "bg-slate-100 text-slate-700"
                                        }`}
                                    >
                                        {s.severity}
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {dryRun && (
                <p className="mt-3 text-xs text-slate-500">
                    Dry-run mode active — no actions persisted.
                </p>
            )}
        </section>
    );
}