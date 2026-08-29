"use client";

/**
 * OverBudgetAlertPanel — Phase 24 FinOps Budget Planning over-budget alert panel.
 *
 * PRD §F40.5 + AD-52 (d) — Variance alerts + auto-escalation status.
 * Shows: severity (warning/critical/escalated), variance_pct,
 * escalation level, channels notified.
 */

import { useEffect, useState } from "react";

import { triggerOverBudgetAlert } from "@/lib/finops/budget-planning-client";
import type { BudgetAlert } from "@/lib/finops/budget-planning-types";

interface OverBudgetAlertPanelProps {
    // No props currently — uses fetch + manual trigger
}

export function OverBudgetAlertPanel(_: OverBudgetAlertPanelProps = {}) {
    const [alerts, setAlerts] = useState<BudgetAlert[]>([]);
    const [loading, setLoading] = useState<boolean>(false);

    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    const handleTrigger = async (variance_pct: number) => {
        setLoading(true);
        try {
            const alert = await triggerOverBudgetAlert({
                plan_id: "demo-plan",
                tenant_id: "demo",
                variance_pct,
                plan_total_budget_amount: 15_000_000.0,
                dry_run: true,
            });
            setAlerts([alert, ...alerts]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        // No initial fetch — manual trigger only
    }, []);

    return (
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
            <div className="mb-3 flex items-center justify-between">
                <h2 className="text-lg font-medium text-slate-100">
                    Over-Budget Alerts
                </h2>
                <div className="flex gap-2">
                    <button
                        type="button"
                        onClick={() => handleTrigger(12)}
                        disabled={loading}
                        className="rounded bg-amber-600 px-3 py-1 text-sm text-white hover:bg-amber-500 disabled:opacity-50"
                    >
                        Test Warning (12%)
                    </button>
                    <button
                        type="button"
                        onClick={() => handleTrigger(28)}
                        disabled={loading}
                        className="rounded bg-rose-600 px-3 py-1 text-sm text-white hover:bg-rose-500 disabled:opacity-50"
                    >
                        Test Critical (28%)
                    </button>
                </div>
            </div>
            <ul className="space-y-2">
                {alerts.map((alert) => (
                    <li
                        key={alert.alert_id}
                        className={`rounded border p-3 ${
                            alert.severity === "critical"
                                ? "border-rose-700 bg-rose-950"
                                : alert.severity === "escalated"
                                  ? "border-purple-700 bg-purple-950"
                                  : "border-slate-700"
                        }`}
                    >
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-slate-200">
                                    {alert.severity.toUpperCase()} — {alert.variance_pct.toFixed(1)}%
                                </p>
                                <p className="text-xs text-slate-400">
                                    Plan: {alert.plan_id} • Level: {alert.escalation_level}
                                </p>
                            </div>
                            <div className="flex flex-wrap gap-1">
                                {alert.channels_notified.map((ch) => (
                                    <span
                                        key={ch}
                                        className="rounded bg-slate-700 px-2 py-0.5 text-xs text-slate-300"
                                    >
                                        {ch}
                                    </span>
                                ))}
                            </div>
                        </div>
                    </li>
                ))}
                {alerts.length === 0 && (
                    <li className="text-center text-sm text-slate-500">
                        No alerts. Click a test button to trigger a warning or critical alert.
                    </li>
                )}
            </ul>
        </div>
    );
}

export default OverBudgetAlertPanel;
