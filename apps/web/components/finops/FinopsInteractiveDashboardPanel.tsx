"use client";

/**
 * FinopsInteractiveDashboardPanel — Phase 28 T2 Interactive Dashboard Panel.
 *
 * Epic 28 T2 frontend follow-up wire (cj-style 197번째) — Main dashboard
 * panel composing 5 sub-components:
 * - CrossPhaseKPIOverview
 * - SavedViewManager
 * - DrillDownExplorer
 * - ExportConfigPanel
 * - DashboardSharingPanel
 *
 * Provides 5-tab layout (Overview / Saved Views / Drill-Down / Export /
 * Sharing) with dry-run toggle (default ON per CR 11-3 honest-DEFER
 * discipline).
 *
 * Capability gate: require_finops_interactive_dashboard
 * (Phase 28 capability matrix v1.53 EXTENSION).
 */

import { useState } from "react";

import { CrossPhaseKPIOverview } from "./interactive-dashboard/CrossPhaseKPIOverview";
import { DashboardSharingPanel } from "./interactive-dashboard/DashboardSharingPanel";
import { DrillDownExplorer } from "./interactive-dashboard/DrillDownExplorer";
import { ExportConfigPanel } from "./interactive-dashboard/ExportConfigPanel";
import { SavedViewManager } from "./interactive-dashboard/SavedViewManager";

type TabKey =
    | "overview"
    | "saved_views"
    | "drill_down"
    | "export"
    | "sharing";

interface FinopsInteractiveDashboardPanelProps {
    periodKey?: string;
    isOwner?: boolean;
    savedViewCount?: number;
    impactKrwPerYear?: number;
}

const TABS: ReadonlyArray<{ key: TabKey; label: string }> = [
    { key: "overview", label: "개요 (Overview)" },
    { key: "saved_views", label: "Saved Views" },
    { key: "drill_down", label: "Drill-Down" },
    { key: "export", label: "Export" },
    { key: "sharing", label: "Sharing" },
];

export function FinopsInteractiveDashboardPanel({
    periodKey = "2026-08",
    isOwner = true,
    savedViewCount = 0,
    impactKrwPerYear = 0,
}: FinopsInteractiveDashboardPanelProps) {
    const [activeTab, setActiveTab] = useState<TabKey>("overview");
    const [dryRun, setDryRun] = useState<boolean>(true);

    return (
        <div className="mx-auto max-w-7xl space-y-6 p-6">
            <header className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">
                        FinOps Interactive Dashboard
                    </h1>
                    <p className="mt-1 text-sm text-slate-600">
                        Epic 28 T2 frontend follow-up — Phase 28 backend
                        (cj-193) 의 4 NEW backend modules 의 executive
                        dashboard UI surface
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <label
                        htmlFor="dry-run-toggle-phase28"
                        className="text-sm font-medium text-slate-700"
                    >
                        Dry-run mode
                    </label>
                    <input
                        id="dry-run-toggle-phase28"
                        data-testid="dry-run-toggle"
                        type="checkbox"
                        checked={dryRun}
                        onChange={(e) => setDryRun(e.target.checked)}
                        className="h-4 w-4 rounded border-slate-300 text-blue-600"
                    />
                </div>
            </header>

            <nav
                className="flex gap-2 border-b border-slate-200"
                role="tablist"
                aria-label="Dashboard tabs"
            >
                {TABS.map((tab) => (
                    <button
                        key={tab.key}
                        role="tab"
                        aria-selected={activeTab === tab.key}
                        data-testid={`tab-${tab.key}`}
                        onClick={() => setActiveTab(tab.key)}
                        className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium transition ${
                            activeTab === tab.key
                                ? "border-blue-600 text-blue-700"
                                : "border-transparent text-slate-500 hover:text-slate-700"
                        }`}
                    >
                        {tab.label}
                    </button>
                ))}
            </nav>

            <main role="tabpanel">
                {activeTab === "overview" && (
                    <CrossPhaseKPIOverview
                        dryRun={dryRun}
                        periodKey={periodKey}
                    />
                )}
                {activeTab === "saved_views" && (
                    <SavedViewManager
                        dryRun={dryRun}
                        periodKey={periodKey}
                    />
                )}
                {activeTab === "drill_down" && (
                    <DrillDownExplorer
                        dryRun={dryRun}
                        periodKey={periodKey}
                    />
                )}
                {activeTab === "export" && (
                    <ExportConfigPanel
                        dryRun={dryRun}
                        periodKey={periodKey}
                    />
                )}
                {activeTab === "sharing" && (
                    <DashboardSharingPanel
                        dryRun={dryRun}
                        periodKey={periodKey}
                        isOwner={isOwner}
                        impactKrwPerYear={impactKrwPerYear}
                        savedViewCount={savedViewCount}
                    />
                )}
            </main>
        </div>
    );
}