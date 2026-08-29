"use client";

/**
 * FinopsVendorManagementDashboardPanel — Phase 25 FinOps Vendor Management Dashboard Panel.
 *
 * Phase 25 wire (cj-style 173번째) — Main dashboard panel composing
 * 5 sub-components:
 * - VendorCatalogOverviewCard
 * - VendorSelectionScorePanel
 * - VendorContractLifecycleTimeline
 * - VendorPerformanceScorecardTable
 * - VendorSpendAttributionChart
 *
 * Provides 5-tab layout (Catalog / Selection / Contracts / Performance / Spend)
 * with dry-run toggle (default ON per CR 11-3 honest-DEFER discipline).
 */

import { useState } from "react";

import { VendorCatalogOverviewCard } from "./vendor-management/VendorCatalogOverviewCard";
import { VendorContractLifecycleTimeline } from "./vendor-management/VendorContractLifecycleTimeline";
import { VendorPerformanceScorecardTable } from "./vendor-management/VendorPerformanceScorecardTable";
import { VendorSelectionScorePanel } from "./vendor-management/VendorSelectionScorePanel";
import { VendorSpendAttributionChart } from "./vendor-management/VendorSpendAttributionChart";

type TabKey =
    | "catalog"
    | "selection"
    | "contracts"
    | "performance"
    | "spend";

const TABS: Array<{ key: TabKey; label: string }> = [
    { key: "catalog", label: "Catalog" },
    { key: "selection", label: "Selection" },
    { key: "contracts", label: "Contracts" },
    { key: "performance", label: "Performance" },
    { key: "spend", label: "Spend" },
];

export function FinopsVendorManagementDashboardPanel() {
    const [activeTab, setActiveTab] = useState<TabKey>("catalog");
    const [dryRun, setDryRun] = useState<boolean>(true);

    return (
        <div className="mx-auto max-w-7xl space-y-6 p-6">
            <header className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">
                        FinOps Vendor Management
                    </h1>
                    <p className="mt-1 text-sm text-slate-600">
                        Post-budget-allocation layer: vendor catalog +
                        selection + contract lifecycle + performance
                        evaluation + spend attribution.
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <label
                        htmlFor="dry-run-toggle"
                        className="text-sm font-medium text-slate-700"
                    >
                        Dry-run mode
                    </label>
                    <input
                        id="dry-run-toggle"
                        type="checkbox"
                        checked={dryRun}
                        onChange={(e) => setDryRun(e.target.checked)}
                        className="h-4 w-4 rounded border-slate-300 text-blue-600"
                    />
                </div>
            </header>

            <nav className="border-b border-slate-200">
                <ul className="-mb-px flex gap-2">
                    {TABS.map((tab) => (
                        <li key={tab.key}>
                            <button
                                type="button"
                                onClick={() => setActiveTab(tab.key)}
                                className={`rounded-t-lg border border-b-0 px-4 py-2 text-sm font-medium ${
                                    activeTab === tab.key
                                        ? "border-blue-600 bg-blue-50 text-blue-700"
                                        : "border-transparent text-slate-600 hover:border-slate-300"
                                }`}
                            >
                                {tab.label}
                            </button>
                        </li>
                    ))}
                </ul>
            </nav>

            <div>
                {activeTab === "catalog" && (
                    <VendorCatalogOverviewCard dryRun={dryRun} />
                )}
                {activeTab === "selection" && (
                    <VendorSelectionScorePanel dryRun={dryRun} />
                )}
                {activeTab === "contracts" && (
                    <VendorContractLifecycleTimeline dryRun={dryRun} />
                )}
                {activeTab === "performance" && (
                    <VendorPerformanceScorecardTable dryRun={dryRun} />
                )}
                {activeTab === "spend" && (
                    <VendorSpendAttributionChart dryRun={dryRun} />
                )}
            </div>
        </div>
    );
}