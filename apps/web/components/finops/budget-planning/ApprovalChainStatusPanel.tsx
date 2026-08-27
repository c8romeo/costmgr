"use client";

/**
 * ApprovalChainStatusPanel — Phase 24 FinOps Budget Planning sequential approval.
 *
 * PRD §F40.3 + AD-52 (c) — Sequential approval visualization.
 * Shows: step_index, approver, status (pending/approved/rejected/skipped),
 * requires_2fa flag, two_fa_verified flag.
 */

import { useState } from "react";

import {
    submitForApproval,
} from "@/lib/finops/budget-planning-client";
import type { BudgetApprovalStep } from "@/lib/finops/budget-planning-types";

export function ApprovalChainStatusPanel() {
    const [steps, setSteps] = useState<BudgetApprovalStep[]>([]);
    const [loading, setLoading] = useState<boolean>(false);

    const handleSubmit = async () => {
        setLoading(true);
        try {
            const newSteps = await submitForApproval({
                plan_id: "demo-plan",
                tenant_id: "demo",
                plan_total_budget_amount: 15_000_000.0,
                approval_chain: ["approver-1", "approver-2", "tenant_owner"],
            });
            setSteps(newSteps);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
            <div className="mb-3 flex items-center justify-between">
                <h2 className="text-lg font-medium text-slate-100">
                    Approval Chain Status
                </h2>
                <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={loading}
                    className="rounded bg-emerald-600 px-3 py-1 text-sm text-white hover:bg-emerald-500 disabled:opacity-50"
                >
                    Submit for Approval (high-value)
                </button>
            </div>
            <ol className="space-y-2">
                {steps.map((step) => (
                    <li
                        key={step.step_id}
                        className="flex items-center justify-between rounded border border-slate-700 p-3"
                    >
                        <div className="flex items-center gap-3">
                            <span className="rounded-full bg-slate-700 px-2 py-0.5 text-xs text-slate-300">
                                Step {step.step_index + 1}
                            </span>
                            <span className="text-sm text-slate-200">
                                {step.approver_actor_id}
                            </span>
                        </div>
                        <div className="flex items-center gap-2">
                            {step.requires_2fa && (
                                <span className="rounded bg-rose-900 px-2 py-0.5 text-xs text-rose-200">
                                    2FA required
                                </span>
                            )}
                            <span
                                className={`rounded px-2 py-0.5 text-xs ${
                                    step.status === "approved"
                                        ? "bg-emerald-900 text-emerald-200"
                                        : step.status === "rejected"
                                          ? "bg-rose-900 text-rose-200"
                                          : step.status === "skipped"
                                            ? "bg-slate-700 text-slate-300"
                                            : "bg-amber-900 text-amber-200"
                                }`}
                            >
                                {step.status}
                            </span>
                        </div>
                    </li>
                ))}
                {steps.length === 0 && (
                    <li className="text-center text-sm text-slate-500">
                        No approval chain started. Click "Submit for Approval" to begin.
                    </li>
                )}
            </ol>
        </div>
    );
}

export default ApprovalChainStatusPanel;
