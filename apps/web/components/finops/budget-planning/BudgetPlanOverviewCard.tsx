"use client";

/**
 * BudgetPlanOverviewCard — Phase 24 FinOps Budget Planning Plan Summary Card.
 *
 * PRD §F40.4 + AD-52 (d) — Plan summary with CRUD actions.
 * Shows: plan_id, period_key, total_budget_amount, lifecycle,
 * approval_chain step count, high_value flag, requires_2fa flag.
 */

import { useEffect, useState } from "react";

import {
    createBudgetPlan,
    fetchBudgetPlanningPlans,
} from "@/lib/finops/budget-planning-client";
import type { BudgetPlan } from "@/lib/finops/budget-planning-types";

interface BudgetPlanOverviewCardProps {
    dryRun: boolean;
}

export function BudgetPlanOverviewCard({ dryRun }: BudgetPlanOverviewCardProps) {
    const [plans, setPlans] = useState<BudgetPlan[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchBudgetPlanningPlans()
            .then((data) => {
                setPlans(data.plans || []);
                setLoading(false);
            })
            .catch((e) => {
                setError(String(e));
                setLoading(false);
            });
    }, []);

    const handleCreate = async () => {
        const now = new Date();
        // eslint-disable-next-line camelcase
        const period_key = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
        try {
            const plan = await createBudgetPlan({
                tenant_id: "demo",
                // eslint-disable-next-line camelcase
                period_key,
                period_type: "monthly",
                scope: ["cost_center", "department", "business_unit", "tag", "tenant"],
                total_budget_amount: 5_000_000.0,
                approval_chain: ["tenant_owner"],
                dry_run: dryRun,
            });
            setPlans([plan, ...plans]);
        } catch (e) {
            setError(String(e));
        }
    };

    if (loading) {
        return <div className="text-slate-400">Loading budget plans...</div>;
    }

    return (
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
            <div className="mb-3 flex items-center justify-between">
                <h2 className="text-lg font-medium text-slate-100">
                    Budget Plan Overview
                </h2>
                <button
                    type="button"
                    onClick={handleCreate}
                    className="rounded bg-emerald-600 px-3 py-1 text-sm text-white hover:bg-emerald-500"
                >
                    New Plan {dryRun ? "(dry-run)" : ""}
                </button>
            </div>
            {error && (
                <p className="mb-3 text-sm text-rose-400">Error: {error}</p>
            )}
            <ul className="space-y-2">
                {plans.map((plan) => (
                    <li
                        key={plan.plan_id}
                        className="rounded border border-slate-700 p-3"
                    >
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-slate-200">
                                    {plan.plan_id} ({plan.period_key})
                                </p>
                                <p className="text-xs text-slate-400">
                                    {plan.period_type} •{" "}
                                    {plan.lifecycle} •{" "}
                                    {plan.total_budget_amount.toLocaleString()} KRW
                                </p>
                            </div>
                            <div className="flex gap-2">
                                {plan.high_value && (
                                    <span className="rounded bg-amber-900 px-2 py-0.5 text-xs text-amber-200">
                                        High-value
                                    </span>
                                )}
                                {plan.requires_2fa && (
                                    <span className="rounded bg-rose-900 px-2 py-0.5 text-xs text-rose-200">
                                        2FA required
                                    </span>
                                )}
                                {plan.dry_run && (
                                    <span className="rounded bg-slate-700 px-2 py-0.5 text-xs text-slate-300">
                                        Dry-run
                                    </span>
                                )}
                            </div>
                        </div>
                    </li>
                ))}
                {plans.length === 0 && (
                    <li className="text-center text-sm text-slate-500">
                        No budget plans yet. Click "New Plan" to create one.
                    </li>
                )}
            </ul>
        </div>
    );
}

export default BudgetPlanOverviewCard;
