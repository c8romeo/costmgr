"use client";

/**
 * VendorSelectionScorePanel — Phase 25 FinOps Vendor Management Selection Score.
 *
 * PRD §F41.2 + AD-53 (b) — 5-dim weighted scoring
 * (cost 0.30 + performance 0.25 + reliability 0.20 + compliance 0.15 +
 * strategic_fit 0.10) + threshold filter (default 60.00) +
 * per-tenant override > industry baseline > system default.
 */

import { useEffect, useState } from "react";

import {
    fetchVendorSelection,
    runVendorSelection,
} from "@/lib/finops/vendor-management-client";
import type { VendorSelectionScore } from "@/lib/finops/vendor-management-types";

const SELECTION_DIMENSION_WEIGHTS = {
    cost: 0.30,
    performance: 0.25,
    reliability: 0.20,
    compliance: 0.15,
    strategic_fit: 0.10,
};

interface VendorSelectionScorePanelProps {
    dryRun: boolean;
}

export function VendorSelectionScorePanel({
    dryRun,
}: VendorSelectionScorePanelProps) {
    const [selections, setSelections] = useState<VendorSelectionScore[]>([]);
    const [threshold, setThreshold] = useState<number>(60.00);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchVendorSelection()
            .then((data) => {
                setSelections(data.selected_vendors || []);
                setLoading(false);
            })
            .catch((e) => {
                setError(String(e));
                setLoading(false);
            });
    }, []);

    const handleRun = async () => {
        try {
            const result = await runVendorSelection({
                vendor_ids: [],
                threshold,
                candidate_limit: 10,
            });
            setSelections(result.selected_vendors || []);
        } catch (e) {
            setError(String(e));
        }
    };

    if (loading) {
        return (
            <div className="text-slate-400">Loading selection scores...</div>
        );
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
            aria-label="Vendor selection scores"
            className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
        >
            <header className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900">
                    Vendor Selection Score Panel
                </h2>
                <div className="flex items-center gap-2">
                    <label
                        htmlFor="threshold"
                        className="text-sm font-medium text-slate-700"
                    >
                        Threshold:
                    </label>
                    <input
                        id="threshold"
                        type="number"
                        min={0}
                        max={100}
                        step={0.5}
                        value={threshold}
                        onChange={(e) => setThreshold(parseFloat(e.target.value))}
                        className="w-20 rounded border border-slate-300 px-2 py-1 text-sm"
                    />
                    <button
                        type="button"
                        onClick={handleRun}
                        className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                    >
                        {dryRun ? "Preview Selection" : "Run Selection"}
                    </button>
                </div>
            </header>

            <dl className="mt-4 grid grid-cols-5 gap-2 text-xs">
                {Object.entries(SELECTION_DIMENSION_WEIGHTS).map(([dim, w]) => (
                    <div
                        key={dim}
                        className="rounded-lg bg-slate-50 px-3 py-2 text-center"
                    >
                        <dt className="font-medium text-slate-700">
                            {dim.replace("_", " ")}
                        </dt>
                        <dd className="text-base font-bold text-blue-600">
                            {w.toFixed(2)}
                        </dd>
                    </div>
                ))}
            </dl>

            <div className="mt-6 overflow-x-auto">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-slate-200">
                            <th className="py-2 text-left font-medium text-slate-700">
                                Vendor
                            </th>
                            <th className="py-2 text-right font-medium text-slate-700">
                                Cost
                            </th>
                            <th className="py-2 text-right font-medium text-slate-700">
                                Performance
                            </th>
                            <th className="py-2 text-right font-medium text-slate-700">
                                Reliability
                            </th>
                            <th className="py-2 text-right font-medium text-slate-700">
                                Compliance
                            </th>
                            <th className="py-2 text-right font-medium text-slate-700">
                                Strategic Fit
                            </th>
                            <th className="py-2 text-right font-medium text-slate-700">
                                Weighted
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {selections.slice(0, 10).map((s) => (
                            <tr
                                key={s.selection_id}
                                className="border-b border-slate-100"
                            >
                                <td className="py-2 font-mono text-xs text-slate-700">
                                    {s.vendor_id.slice(0, 8)}
                                </td>
                                <td className="py-2 text-right">
                                    {s.cost_score.toFixed(1)}
                                </td>
                                <td className="py-2 text-right">
                                    {s.performance_score.toFixed(1)}
                                </td>
                                <td className="py-2 text-right">
                                    {s.reliability_score.toFixed(1)}
                                </td>
                                <td className="py-2 text-right">
                                    {s.compliance_score.toFixed(1)}
                                </td>
                                <td className="py-2 text-right">
                                    {s.strategic_fit_score.toFixed(1)}
                                </td>
                                <td className="py-2 text-right font-bold text-blue-600">
                                    {s.weighted_total_score.toFixed(2)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </section>
    );
}