"use client";

/**
 * FinopsOptimizationDashboardPanel — Phase 14 FinOps Optimization Client panel.
 *
 * Phase 14 (cj-style 119번째 wire) — FinOps Optimization & Rightsizing
 * territory (PRD §F30.6). 5 sub-components (OptimizationStrategySelector +
 * RightsizingRecommendationTable + IdleResourcePanel +
 * CommitmentRecommendationPanel + OptimizationAccuracyPanel) +
 * owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 보존.
 *
 * CR 11-4 D-003 RTL render discipline.
 * CR 12-5 D-PARITY-01 — TypeScript interfaces mirror Python TypedDict
 * via `lib/finops-optimization/finops-optimization-client.ts`.
 */

import { useState } from "react";

import {
  fetchOptimizationRecommendations,
  fetchIdleResources,
  fetchCommitmentRecommendations,
  fetchOptimizationAccuracy,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  type OptimizationDefinition,
  type RightsizingRecommendation,
  type IdleResource,
  type CommitmentRecommendation,
  type OptimizationAccuracyReport,
} from "@/lib/finops-optimization/finops-optimization-client";

// ── OptimizationStrategySelector ──
function OptimizationStrategySelector({
  onChange,
}: {
  onChange: (strategy: string, resourceType: string, baseline: string) => void;
}) {
  return (
    <div className="optimization-strategy-selector mb-6 rounded bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Optimization Strategy Selector
      </h2>
      <div className="grid grid-cols-3 gap-3">
        <select
          aria-label="optimization_strategy"
          className="rounded bg-slate-800 text-slate-100 p-2"
          onChange={(e) => {
            const sel = e.target;
            onChange(
              sel.value,
              (document.getElementById("resource-type-sel") as HTMLSelectElement)?.value ?? "compute",
              (document.getElementById("baseline-period-sel") as HTMLSelectElement)?.value ?? "last_30d",
            );
          }}
        >
          <option value="composite">composite (default)</option>
          <option value="rightsize_down">rightsize_down</option>
          <option value="rightsize_up">rightsize_up</option>
          <option value="idle_terminate">idle_terminate</option>
          <option value="commit_1y">commit_1y</option>
          <option value="commit_3y">commit_3y</option>
          <option value="storage_tier_down">storage_tier_down</option>
        </select>
        <select
          id="resource-type-sel"
          aria-label="resource_type"
          className="rounded bg-slate-800 text-slate-100 p-2"
        >
          <option value="compute">compute</option>
          <option value="storage">storage</option>
          <option value="database">database</option>
          <option value="network">network</option>
          <option value="container">container</option>
        </select>
        <select
          id="baseline-period-sel"
          aria-label="baseline_period"
          className="rounded bg-slate-800 text-slate-100 p-2"
        >
          <option value="last_7d">last_7d</option>
          <option value="last_30d">last_30d (default)</option>
          <option value="last_90d">last_90d</option>
          <option value="last_180d">last_180d</option>
          <option value="last_365d">last_365d</option>
        </select>
      </div>
    </div>
  );
}

// ── RightsizingRecommendationTable ──
function RightsizingRecommendationTable({
  recommendations,
}: {
  recommendations: RightsizingRecommendation[];
}) {
  return (
    <div className="rightsizing-recommendation-table mb-6 rounded bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Rightsizing Recommendations ({recommendations.length})
      </h2>
      <table className="w-full text-sm text-slate-200">
        <thead>
          <tr className="text-left">
            <th className="p-2">resource_id</th>
            <th className="p-2">current → recommended</th>
            <th className="p-2">cost_savings %</th>
            <th className="p-2">confidence</th>
            <th className="p-2">severity</th>
          </tr>
        </thead>
        <tbody>
          {recommendations.map((rec) => (
            <tr key={rec.recommendation_id} className="border-t border-slate-700">
              <td className="p-2 font-mono">{rec.resource_id}</td>
              <td className="p-2">
                {rec.current_instance_type} → {rec.recommended_instance_type}
              </td>
              <td className="p-2">{rec.projected_savings_pct.toFixed(2)}%</td>
              <td className="p-2">{rec.confidence_score.toFixed(1)}</td>
              <td className={`p-2 severity-${rec.recommendation_severity}`}>
                {rec.recommendation_severity}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── IdleResourcePanel ──
function IdleResourcePanel({ resources }: { resources: IdleResource[] }) {
  return (
    <div className="idle-resource-panel mb-6 rounded bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Idle Resources ({resources.length})
      </h2>
      <table className="w-full text-sm text-slate-200">
        <thead>
          <tr className="text-left">
            <th className="p-2">resource_id</th>
            <th className="p-2">reason</th>
            <th className="p-2">idle_duration_days</th>
            <th className="p-2">potential_savings_krw</th>
            <th className="p-2">severity</th>
            <th className="p-2">action</th>
          </tr>
        </thead>
        <tbody>
          {resources.map((res) => (
            <tr key={res.idle_resource_id} className="border-t border-slate-700">
              <td className="p-2 font-mono">{res.resource_id}</td>
              <td className="p-2">{res.idle_reason}</td>
              <td className="p-2">{res.idle_duration_days}</td>
              <td className="p-2">{res.potential_savings_krw_per_month.toFixed(0)}</td>
              <td className={`p-2 severity-${res.idle_severity}`}>
                {res.idle_severity}
              </td>
              <td className="p-2">{res.action}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── CommitmentRecommendationPanel ──
function CommitmentRecommendationPanel({
  recommendations,
}: {
  recommendations: CommitmentRecommendation[];
}) {
  return (
    <div className="commitment-recommendation-panel mb-6 rounded bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        RI/SP Commitment Recommendations ({recommendations.length})
      </h2>
      <table className="w-full text-sm text-slate-200">
        <thead>
          <tr className="text-left">
            <th className="p-2">type</th>
            <th className="p-2">term</th>
            <th className="p-2">resource_pattern</th>
            <th className="p-2">savings %</th>
            <th className="p-2">break_even</th>
            <th className="p-2">ROI %</th>
            <th className="p-2">severity</th>
          </tr>
        </thead>
        <tbody>
          {recommendations.map((rec) => (
            <tr key={rec.recommendation_id} className="border-t border-slate-700">
              <td className="p-2">{rec.commitment_type}</td>
              <td className="p-2">{rec.commitment_term}</td>
              <td className="p-2 font-mono">{rec.resource_pattern}</td>
              <td className="p-2">{rec.projected_savings_pct.toFixed(2)}%</td>
              <td className="p-2">{rec.break_even_months}mo</td>
              <td className="p-2">{rec.roi_pct.toFixed(1)}%</td>
              <td className={`p-2 severity-${rec.recommendation_severity}`}>
                {rec.recommendation_severity}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── OptimizationAccuracyPanel ──
function OptimizationAccuracyPanel({
  reports,
}: {
  reports: OptimizationAccuracyReport[];
}) {
  return (
    <div className="optimization-accuracy-panel mb-6 rounded bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Optimization Accuracy Tracking ({reports.length})
      </h2>
      <table className="w-full text-sm text-slate-200">
        <thead>
          <tr className="text-left">
            <th className="p-2">resource_type</th>
            <th className="p-2">strategy</th>
            <th className="p-2">precision</th>
            <th className="p-2">recall</th>
            <th className="p-2">accuracy_score</th>
            <th className="p-2">realized_savings_krw</th>
          </tr>
        </thead>
        <tbody>
          {reports.map((rep) => (
            <tr key={rep.report_id} className="border-t border-slate-700">
              <td className="p-2">{rep.resource_type}</td>
              <td className="p-2">{rep.optimization_strategy}</td>
              <td className="p-2">{rep.precision.toFixed(2)}%</td>
              <td className="p-2">{rep.recall.toFixed(2)}%</td>
              <td className="p-2">{rep.accuracy_score.toFixed(2)}%</td>
              <td className="p-2">{rep.realized_savings_krw.toFixed(0)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Main Dashboard Panel ──
export function FinopsOptimizationDashboardPanel() {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [optimizationStrategy, setOptimizationStrategy] = useState("composite");
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [resourceType, setResourceType] = useState("compute");
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [baselinePeriod, setBaselinePeriod] = useState("last_30d");
  const [recommendations, setRecommendations] = useState<RightsizingRecommendation[]>([]);
  const [idleResources, setIdleResources] = useState<IdleResource[]>([]);
  const [commitments, setCommitments] = useState<CommitmentRecommendation[]>([]);
  const [accuracyReports, setAccuracyReports] = useState<OptimizationAccuracyReport[]>([]);

  return (
    <div className="finops-optimization-dashboard">
      <OptimizationStrategySelector
        onChange={(strategy, resource, baseline) => {
          setOptimizationStrategy(strategy);
          setResourceType(resource);
          setBaselinePeriod(baseline);
          // Refresh data — owner-only RBAC AD-22 + Epic 12 2FA 챌린지 보존
          void refreshData(strategy, resource, baseline, {
            setRecommendations,
            setIdleResources,
            setCommitments,
            setAccuracyReports,
          });
        }}
      />
      <RightsizingRecommendationTable recommendations={recommendations} />
      <IdleResourcePanel resources={idleResources} />
      <CommitmentRecommendationPanel recommendations={commitments} />
      <OptimizationAccuracyPanel reports={accuracyReports} />
    </div>
  );
}

async function refreshData(
  strategy: string,
  resourceType: string,
  baselinePeriod: string,
  setSetters: {
    setRecommendations: (r: RightsizingRecommendation[]) => void;
    setIdleResources: (r: IdleResource[]) => void;
    setCommitments: (r: CommitmentRecommendation[]) => void;
    setAccuracyReports: (r: OptimizationAccuracyReport[]) => void;
  },
): Promise<void> {
  const [recs, idle, commits, accuracy] = await Promise.all([
    fetchOptimizationRecommendations(strategy, resourceType, baselinePeriod),
    fetchIdleResources(resourceType, baselinePeriod),
    fetchCommitmentRecommendations(baselinePeriod),
    fetchOptimizationAccuracy(resourceType, strategy),
  ]);
  setSetters.setRecommendations(recs);
  setSetters.setIdleResources(idle);
  setSetters.setCommitments(commits);
  setSetters.setAccuracyReports(accuracy);
}
