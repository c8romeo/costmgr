"use client";

/**
 * FinopsCostAnomalyMLPredictionDashboardPanel — Phase 26 FinOps Cost
 * Anomaly ML Prediction Dashboard Panel.
 *
 * Phase 26 wire (cj-style 186번째) — Main dashboard panel composing
 * 5 sub-components:
 * - AnomalyMLPredictionOverviewCard
 * - EnsembleConsensusScorePanel
 * - MLvsThresholdComparisonChart
 * - ModelDriftDetectionPanel
 * - ABTestChampionChallengerPanel
 *
 * Provides 5-tab layout (Overview / Ensemble / Comparison / Drift / A-B)
 * with dry-run toggle (default ON per CR 11-3 honest-DEFER discipline).
 *
 * Capability gate: require_finops_cost_anomaly_ml_prediction
 * (Phase 26 capability matrix v1.52 EXTENSION).
 */

import { useState } from "react";

import { ABTestChampionChallengerPanel } from "./cost-anomaly-ml-prediction/ABTestChampionChallengerPanel";
import { AnomalyMLPredictionOverviewCard } from "./cost-anomaly-ml-prediction/AnomalyMLPredictionOverviewCard";
import { EnsembleConsensusScorePanel } from "./cost-anomaly-ml-prediction/EnsembleConsensusScorePanel";
import { MLvsThresholdComparisonChart } from "./cost-anomaly-ml-prediction/MLvsThresholdComparisonChart";
import { ModelDriftDetectionPanel } from "./cost-anomaly-ml-prediction/ModelDriftDetectionPanel";

type TabKey =
    | "overview"
    | "ensemble"
    | "comparison"
    | "drift"
    | "ab_test";

interface FinopsCostAnomalyMLPredictionDashboardPanelProps {
    periodKey?: string;
}

const TABS: Array<{ key: TabKey; label: string }> = [
    { key: "overview", label: "개요 (Overview)" },
    { key: "ensemble", label: "앙상블 합의" },
    { key: "comparison", label: "ML vs 임계값" },
    { key: "drift", label: "드리프트 감지" },
    { key: "ab_test", label: "A/B 테스트" },
];

export function FinopsCostAnomalyMLPredictionDashboardPanel({
    periodKey = "2026-08",
}: FinopsCostAnomalyMLPredictionDashboardPanelProps) {
    const [activeTab, setActiveTab] = useState<TabKey>("overview");
    const [dryRun, setDryRun] = useState<boolean>(true);

    return (
        <div className="mx-auto max-w-7xl space-y-6 p-6">
            <header className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">
                        FinOps Cost Anomaly ML Prediction
                    </h1>
                    <p className="mt-1 text-sm text-slate-600">
                        ML-driven 사전 이상탐지 레이어 (Phase 26) — Phase 12
                        rule-based 사후 detection 과 complementary ledger.
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <label
                        htmlFor="dry-run-toggle-phase26"
                        className="text-sm font-medium text-slate-700"
                    >
                        Dry-run mode
                    </label>
                    <input
                        id="dry-run-toggle-phase26"
                        type="checkbox"
                        checked={dryRun}
                        onChange={(e) => setDryRun(e.target.checked)}
                        className="h-4 w-4 rounded border-slate-300 text-blue-600"
                    />
                </div>
            </header>

            <nav className="border-b border-slate-200">
                <ul className="-mb-px flex flex-wrap gap-2">
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
                {activeTab === "overview" && (
                    <AnomalyMLPredictionOverviewCard
                        dryRun={dryRun}
                        periodKey={periodKey}
                    />
                )}
                {activeTab === "ensemble" && (
                    <EnsembleConsensusScorePanel
                        dryRun={dryRun}
                        periodKey={periodKey}
                    />
                )}
                {activeTab === "comparison" && (
                    <MLvsThresholdComparisonChart
                        dryRun={dryRun}
                        periodKey={periodKey}
                    />
                )}
                {activeTab === "drift" && (
                    <ModelDriftDetectionPanel
                        dryRun={dryRun}
                        periodKey={periodKey}
                    />
                )}
                {activeTab === "ab_test" && (
                    <ABTestChampionChallengerPanel
                        dryRun={dryRun}
                        periodKey={periodKey}
                    />
                )}
            </div>
        </div>
    );
}
