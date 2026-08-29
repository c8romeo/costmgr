"use client";

/**
 * FinopsBudgetPlanningDashboardPanel — Phase 24 FinOps Budget Planning
 * pre-allocation layer dashboard panel (cj-style 169번째 wire).
 *
 * 5-tab layout + 5 sub-components:
 * 1. BudgetPlanOverviewCard — plan summary + CRUD actions
 * 2. BudgetAllocationBreakdownPanel — 5-dim Recharts pie chart
 * 3. BudgetVsActualTrendChart — 12-month Recharts line chart
 * 4. OverBudgetAlertPanel — variance alerts + auto-escalation status
 * 5. ApprovalChainStatusPanel — sequential approval visualization
 *
 * Dry-run toggle default: dry-run.
 *
 * CR lessons applied:
 * - AD-22 owner-only RBAC.
 * - Epic 12 2FA 챌린지 mandatory high-value (≥10M KRW/year).
 * - NFR4 PII minimization PRESERVED.
 * - NFR18 ko-KR SSOT (finops_budget_planning.* namespace).
 */

import { useState } from "react";

import { fetchBudgetPlanningHealthcheck } from "@/lib/finops/budget-planning-client";

import {
    ApprovalChainStatusPanel,
} from "./budget-planning/ApprovalChainStatusPanel";
import {
    BudgetAllocationBreakdownPanel,
} from "./budget-planning/BudgetAllocationBreakdownPanel";
import {
    BudgetPlanOverviewCard,
} from "./budget-planning/BudgetPlanOverviewCard";
import {
    BudgetVsActualTrendChart,
} from "./budget-planning/BudgetVsActualTrendChart";
import {
    OverBudgetAlertPanel,
} from "./budget-planning/OverBudgetAlertPanel";


type TabKey =
    | "overview"
    | "allocation"
    | "variance"
    | "alerts"
    | "approval";

const TABS: Array<{ key: TabKey; label: string; ko: string }> = [
    { key: "overview", label: "Overview", ko: "개요" },
    { key: "allocation", label: "Allocation", ko: "할당" },
    { key: "variance", label: "Variance", ko: "차이" },
    { key: "alerts", label: "Alerts", ko: "알림" },
    { key: "approval", label: "Approval", ko: "승인" },
];

export function FinopsBudgetPlanningDashboardPanel() {
    const [activeTab, setActiveTab] = useState<TabKey>("overview");
    const [dryRun, setDryRun] = useState<boolean>(true);
    const [healthcheck, setHealthcheck] = useState<string>("unknown");

    // Lightweight health-check on mount (non-blocking)
    useState(() => {
        fetchBudgetPlanningHealthcheck()
            .then((res) => setHealthcheck(res.status))
            .catch(() => setHealthcheck("error"));
    });

    return (
        <div className="finops-budget-planning-dashboard">
            {/* Header */}
            <header className="mb-6 flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-semibold text-slate-100">
                        FinOps Budget Planning
                    </h1>
                    <p className="text-sm text-slate-400">
                        Phase 24 pre-allocation layer — budget plan + allocation +
                        approval + variance + alert
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <label className="flex items-center gap-2 text-sm text-slate-300">
                        <input
                            type="checkbox"
                            checked={dryRun}
                            onChange={(e) => setDryRun(e.target.checked)}
                            aria-label="Dry-run mode toggle"
                        />
                        Dry-run
                    </label>
                    <span className="text-xs text-slate-500">
                        Health: {healthcheck}
                    </span>
                </div>
            </header>

            {/* Tabs */}
            <nav className="mb-4 flex border-b border-slate-800" role="tablist">
                {TABS.map((tab) => (
                    <button
                        key={tab.key}
                        type="button"
                        role="tab"
                        aria-selected={activeTab === tab.key}
                        onClick={() => setActiveTab(tab.key)}
                        className={`px-4 py-2 text-sm transition-colors ${
                            activeTab === tab.key
                                ? "border-b-2 border-emerald-500 text-emerald-400"
                                : "text-slate-400 hover:text-slate-200"
                        }`}
                    >
                        {tab.label}
                        <span className="ml-1 text-xs text-slate-500">
                            ({tab.ko})
                        </span>
                    </button>
                ))}
            </nav>

            {/* Content */}
            <div role="tabpanel">
                {activeTab === "overview" && (
                    <BudgetPlanOverviewCard dryRun={dryRun} />
                )}
                {activeTab === "allocation" && (
                    <BudgetAllocationBreakdownPanel />
                )}
                {activeTab === "variance" && <BudgetVsActualTrendChart />}
                {activeTab === "alerts" && <OverBudgetAlertPanel />}
                {activeTab === "approval" && <ApprovalChainStatusPanel />}
            </div>
        </div>
    );
}

export default FinopsBudgetPlanningDashboardPanel;
