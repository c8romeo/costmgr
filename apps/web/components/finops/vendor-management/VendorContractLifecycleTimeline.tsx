"use client";

/**
 * VendorContractLifecycleTimeline — Phase 25 FinOps Vendor Management Contract Lifecycle.
 *
 * PRD §F41.3 + AD-53 (c) — Sequential contract lifecycle timeline
 * (draft → pending_approval → approved → active → expiring_soon →
 * renewed/expired/terminated) + Epic 12 2FA 챌린지 ≥ 10M KRW/year
 * mandatory + auto-renewal 90-day window + over-budget cross-check +
 * vendor_blacklist compliance gate.
 */

import { useEffect, useState } from "react";

import {
    advanceContractLifecycle,
    fetchVendorContracts,
} from "@/lib/finops/vendor-management-client";
import type { VendorContract } from "@/lib/finops/vendor-management-types";
import type { VendorContractLifecycle } from "@/lib/finops/vendor-management-types";

const LIFECYCLE_STAGES = [
    "draft",
    "pending_approval",
    "approved",
    "active",
    "expiring_soon",
    "renewed",
    "expired",
    "terminated",
] as const;

interface VendorContractLifecycleTimelineProps {
    dryRun: boolean;
}

export function VendorContractLifecycleTimeline({
    dryRun,
}: VendorContractLifecycleTimelineProps) {
    const [contracts, setContracts] = useState<VendorContract[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchVendorContracts()
            .then((data) => {
                setContracts(data.contracts || []);
                setLoading(false);
            })
            .catch((e) => {
                setError(String(e));
                setLoading(false);
            });
    }, []);

    const handleAdvance = async (contractId: string, target: VendorContractLifecycle) => {
        try {
            const updated = await advanceContractLifecycle(contractId, target);
            setContracts(
                contracts.map((c) =>
                    c.contract_id === contractId ? updated : c
                )
            );
        } catch (e) {
            setError(String(e));
        }
    };

    if (loading) {
        return <div className="text-slate-400">Loading contracts...</div>;
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
            aria-label="Vendor contract lifecycle"
            className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
        >
            <h2 className="text-lg font-semibold text-slate-900">
                Vendor Contract Lifecycle Timeline
            </h2>

            <div className="mt-4 overflow-x-auto">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-slate-200">
                            <th className="py-2 text-left font-medium text-slate-700">
                                Contract
                            </th>
                            <th className="py-2 text-right font-medium text-slate-700">
                                Value (KRW)
                            </th>
                            <th className="py-2 text-left font-medium text-slate-700">
                                Lifecycle
                            </th>
                            <th className="py-2 text-center font-medium text-slate-700">
                                High Value (2FA)
                            </th>
                            <th className="py-2 text-right font-medium text-slate-700">
                                Action
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {contracts.slice(0, 10).map((c) => {
                            const stageIndex = LIFECYCLE_STAGES.indexOf(
                                // eslint-disable-next-line @typescript-eslint/no-restricted-types
                                c.lifecycle as typeof LIFECYCLE_STAGES[number]
                            );
                            const nextStage =
                                stageIndex < LIFECYCLE_STAGES.length - 1
                                    ? LIFECYCLE_STAGES[stageIndex + 1]
                                    : null;
                            return (
                                <tr
                                    key={c.contract_id}
                                    className="border-b border-slate-100"
                                >
                                    <td className="py-2 font-mono text-xs text-slate-700">
                                        {c.contract_name}
                                    </td>
                                    <td className="py-2 text-right">
                                        {c.contract_value_krw.toLocaleString()}
                                    </td>
                                    <td className="py-2">
                                        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
                                            {c.lifecycle}
                                        </span>
                                    </td>
                                    <td className="py-2 text-center">
                                        {c.high_value ? (
                                            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
                                                Yes · 2FA Required
                                            </span>
                                        ) : (
                                            <span className="text-xs text-slate-500">
                                                No
                                            </span>
                                        )}
                                    </td>
                                    <td className="py-2 text-right">
                                        {nextStage ? (
                                            <button
                                                type="button"
                                                onClick={() =>
                                                    handleAdvance(
                                                        c.contract_id,
                                                        nextStage
                                                    )
                                                }
                                                className="rounded bg-blue-600 px-2 py-1 text-xs font-medium text-white hover:bg-blue-700"
                                                disabled={dryRun}
                                            >
                                                → {nextStage}
                                            </button>
                                        ) : (
                                            <span className="text-xs text-slate-400">
                                                Terminal
                                            </span>
                                        )}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </section>
    );
}