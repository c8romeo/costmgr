"use client";

/**
 * FinopsReservedCapacityDashboardPanel — Phase 21 FinOps Reserved Capacity
 * Planning Client panel.
 *
 * Phase 21 (cj-style 151번째 wire) — FinOps Reserved Capacity Planning
 * territory (PRD §F37.1-4). 5 sub-components:
 * 1. DemandForecastPanel — 5-module cross-join weighted average
 *    (phase_13_forecast=0.25 + phase_14_optimization=0.20 +
 *    phase_18_commitment=0.20 + phase_19_pricing=0.15 +
 *    phase_20_multi_cloud=0.20) → single forecasted_demand_krw +
 *    confidence_interval (low/high) + seasonal_factor + growth_rate_pct +
 *    confidence_pct + 4 industries baseline (manufacturing=8.0 /
 *    service=12.0 / manufacturing_service=10.0 /
 *    manufacturing_service_other=15.0 INDUSTRY_GROWTH_BASELINE_PCT).
 * 2. CapacityPlanningPanel — 6 reserved_capacity_tier enum
 *    (1y_no_upfront + 1y_partial_upfront + 1y_all_upfront +
 *    3y_no_upfront + 3y_partial_upfront + 3y_all_upfront) +
 *    break_even_utilization_pct (≥ 70.0 MINIMUM) + capacity_headroom_pct
 *    (10~20% target) + MINIMUM_SAVINGS_PCT=5.0 + MINIMUM_SAVINGS_KRW=1M
 *    + estimated_savings_krw + estimated_savings_pct.
 * 3. CommitmentRecommendationPanel — confidence_score
 *    (utilization_stability × 0.4 + historical_accuracy × 0.3 +
 *    demand_forecast_confidence_pct × 0.3) + risk_score (savings_pct ×
 *    0.4 + commitment_term × 0.3 + commitment_flexibility × 0.3) + 4
 *    execution_strategy (auto_execute_ready + manual_review_required +
 *    owner_approval_required + low_confidence) + high-value threshold
 *    (≥ 10M KRW/year) → Epic 12 2FA 챌린지 mandatory.
 * 4. ReservedCapacityOrchestratorPanel — composition_step_chain 5 step
 *    (demand_forecast → capacity_planning → commitment_recommendation →
 *    approval → execute) + 4 cadence schedule (daily 02:00 + weekly Mon
 *    03:00 + monthly 1st-day 04:00 + quarterly 1st-day 05:00 KST pytz
 *    timezone('Asia/Seoul')) + orchestration_status (pending / running /
 *    completed / failed / dry_run) + dry-run mode + Epic 12 2FA 챌린지
 *    mandatory + owner approval flow (high-value threshold 10M KRW/year).
 * 5. ReservedCapacityTrendMiniChart — Recharts 2.12.7 stack pin
 *    ReservedCapacityOrchestration composition_step_results trend
 *    (AreaChart placeholder) + 5 industry breakdown (BarChart
 *    placeholder).
 *
 * Plus ReservedCapacityDryRunPreviewPanel — T7.3 dry-run preview UI
 * EXTENSION (preview step_chain + audit_action
 * `reserved_capacity_dry_run_executed` + orchestration_status 'dry_run').
 *
 * Plus ScheduledReservedCapacityDispatchConfigPanel — 4 cadence schedule
 * KST cron (daily 02:00 / weekly Mon 03:00 / monthly 1st-day 04:00 /
 * quarterly 1st-day 05:00) + 4 recipient_strategy (owner_only /
 * executive / finops_team / custom_recipients) + LISTEN/NOTIFY 4 channel
 * (phase_21_demand_forecast_calculated +
 * phase_21_capacity_planning_recommended +
 * phase_21_commitment_recommendation_generated +
 * phase_21_reserved_capacity_orchestrated) cross-tenant invalidation.
 *
 * Owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 보존.
 *
 * CR 11-4 D-003 RTL render discipline.
 * CR 12-5 D-PARITY-01 — TypeScript interfaces mirror Python TypedDict
 * via `lib/finops/reserved-capacity-types.ts`.
 * AD-14 stack pin — Recharts 2.12.7.
 */

import { useState } from "react";
import {
    aggregateDemandForecast,
    planReservedCapacity,
    generateCommitmentRecommendation,
    orchestrateReservedCapacity,
    scheduleReservedCapacityDispatch,
    fetchCadencePreview,
    runDryRun,
    type AggregateDemandForecastRequest,
    type PlanReservedCapacityRequest,
    type CommitmentRecommendationRequest,
    type OrchestrateReservedCapacityRequest,
    type ScheduleDispatchRequest,
    type DryRunRequest,
} from "@/lib/finops/reserved-capacity-client";
import type {
    ReservedCapacityDemandForecast,
    ReservedCapacityPlan,
    CommitmentRecommendation,
    ReservedCapacityOrchestration,
    ScheduledReservedCapacityDispatch,
    ReservedCapacityCadence,
    OrchestrationScope,
} from "@/lib/finops/reserved-capacity-types";

const ALL_CADENCES: ReservedCapacityCadence[] = [
    "daily",
    "weekly",
    "monthly",
    "quarterly",
];

const ALL_INDUSTRIES: OrchestrationScope[] = [
    "manufacturing",
    "service",
    "manufacturing_service",
    "manufacturing_service_other",
];

// ── 1. DemandForecastPanel ──
function DemandForecastPanel({
    forecast,
    onCompute,
}: {
    forecast: ReservedCapacityDemandForecast | null;
    onCompute: () => void;
}) {
    return (
        <div
            className="reserved-capacity-demand-forecast mb-6 rounded bg-slate-900 p-4"
            aria-label="reserved_capacity_demand_forecast"
        >
            <div className="mb-3 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-100">
                    수요 예측 (5-module cross-join)
                </h2>
                <button
                    type="button"
                    className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700"
                    onClick={onCompute}
                >
                    계산
                </button>
            </div>
            {forecast ? (
                <>
                    <p className="text-sm text-slate-300">
                        industry:{" "}
                        <span className="font-mono">{forecast.industry}</span>{" "}
                        | period:{" "}
                        <span className="font-mono">
                            {forecast.period_key}
                        </span>
                    </p>
                    <p className="text-sm text-slate-300">
                        forecasted_demand_krw:{" "}
                        <span className="font-mono">
                            {forecast.forecasted_demand_krw.toFixed(2)}
                        </span>
                    </p>
                    <p className="text-sm text-slate-300">
                        confidence_interval:{" "}
                        <span className="font-mono">
                            {forecast.confidence_interval_low_krw.toFixed(2)}
                        </span>{" "}
                        ~{" "}
                        <span className="font-mono">
                            {forecast.confidence_interval_high_krw.toFixed(2)}
                        </span>{" "}
                        (confidence_pct=
                        <span className="font-mono">
                            {forecast.confidence_pct.toFixed(2)}
                        </span>
                        )
                    </p>
                    <p className="text-sm text-slate-300">
                        seasonal_factor:{" "}
                        <span className="font-mono">
                            {forecast.seasonal_factor.toFixed(2)}
                        </span>{" "}
                        | growth_rate_pct:{" "}
                        <span className="font-mono">
                            {forecast.growth_rate_pct.toFixed(2)}
                        </span>
                        %
                    </p>
                    <p className="text-xs text-slate-500">
                        5-module weights: phase_13=0.25, phase_14=0.20,
                        phase_18=0.20, phase_19=0.15, phase_20=0.20 (sum=1.0)
                    </p>
                </>
            ) : (
                <p className="text-sm text-slate-400">계산 누름</p>
            )}
        </div>
    );
}

// ── 2. CapacityPlanningPanel ──
function CapacityPlanningPanel({
    plan,
    onPlan,
}: {
    plan: ReservedCapacityPlan | null;
    onPlan: () => void;
}) {
    return (
        <div
            className="reserved-capacity-plan mb-6 rounded bg-slate-900 p-4"
            aria-label="reserved_capacity_plan"
        >
            <div className="mb-3 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-100">
                    용량 계획 (6 reserved_capacity_tier)
                </h2>
                <button
                    type="button"
                    className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700"
                    onClick={onPlan}
                >
                    계획
                </button>
            </div>
            {plan ? (
                <>
                    <p className="text-sm text-slate-300">
                        recommended_tier:{" "}
                        <span className="font-mono">
                            {plan.recommended_tier}
                        </span>{" "}
                        | status:{" "}
                        <span className="font-mono">
                            {plan.capacity_plan_status}
                        </span>
                    </p>
                    <p className="text-sm text-slate-300">
                        break_even_utilization_pct:{" "}
                        <span className="font-mono">
                            {plan.break_even_utilization_pct.toFixed(2)}
                        </span>
                        % (≥ 70.0) | capacity_headroom_pct:{" "}
                        <span className="font-mono">
                            {plan.capacity_headroom_pct.toFixed(2)}
                        </span>
                        % (10~20)
                    </p>
                    <p className="text-sm text-slate-300">
                        target_units:{" "}
                        <span className="font-mono">
                            {plan.target_reserved_capacity_units}
                        </span>{" "}
                        | estimated_savings_krw:{" "}
                        <span className="font-mono">
                            {plan.estimated_savings_krw.toFixed(0)}
                        </span>{" "}
                        ({plan.estimated_savings_pct.toFixed(2)}%)
                    </p>
                    <p className="text-sm text-slate-300">
                        term_months:{" "}
                        <span className="font-mono">
                            {plan.commitment_term_months}
                        </span>{" "}
                        | upfront:{" "}
                        <span className="font-mono">
                            {plan.upfront_payment_option}
                        </span>
                    </p>
                    <p className="text-xs text-slate-500">
                        MINIMUM_SAVINGS_PCT=5.0 + MINIMUM_SAVINGS_KRW=1M +
                        MINIMUM_BREAK_EVEN_UTILIZATION_PCT=70.0
                    </p>
                </>
            ) : (
                <p className="text-sm text-slate-400">계획 누름</p>
            )}
        </div>
    );
}

// ── 3. CommitmentRecommendationPanel ──
function CommitmentRecommendationPanel({
    recommendation,
    onGenerate,
}: {
    recommendation: CommitmentRecommendation | null;
    onGenerate: () => void;
}) {
    return (
        <div
            className="reserved-capacity-commitment-recommendation mb-6 rounded bg-slate-900 p-4"
            aria-label="reserved_capacity_commitment_recommendation"
        >
            <div className="mb-3 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-100">
                    약정 추천 (confidence + risk + execution_strategy)
                </h2>
                <button
                    type="button"
                    className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700"
                    onClick={onGenerate}
                >
                    생성
                </button>
            </div>
            {recommendation ? (
                <>
                    <p className="text-sm text-slate-300">
                        tier:{" "}
                        <span className="font-mono">
                            {recommendation.recommended_tier}
                        </span>{" "}
                        | execution_strategy:{" "}
                        <span className="font-mono">
                            {recommendation.execution_strategy}
                        </span>
                    </p>
                    <p className="text-sm text-slate-300">
                        confidence_score:{" "}
                        <span className="font-mono">
                            {recommendation.confidence_score.toFixed(2)}
                        </span>{" "}
                        | risk_score:{" "}
                        <span className="font-mono">
                            {recommendation.risk_score.toFixed(2)}
                        </span>
                    </p>
                    <p className="text-sm text-slate-300">
                        annual_savings_krw:{" "}
                        <span className="font-mono">
                            {recommendation.estimated_annual_savings_krw.toFixed(
                                0,
                            )}
                        </span>{" "}
                        ({recommendation.estimated_annual_savings_pct.toFixed(2)}%)
                    </p>
                    {recommendation.high_value_flag && (
                        <p className="text-sm text-amber-400">
                            high_value_flag=true → Epic 12 2FA 챌린지 mandatory
                            (≥ 10M KRW/year) + owner_approval_required
                        </p>
                    )}
                    <p className="text-xs text-slate-500">
                        CONFIDENCE_WEIGHTS: utilization_stability=0.4 +
                        historical_accuracy=0.3 + demand_forecast_confidence=0.3
                    </p>
                </>
            ) : (
                <p className="text-sm text-slate-400">생성 누름</p>
            )}
        </div>
    );
}

// ── 4. ReservedCapacityOrchestratorPanel ──
function ReservedCapacityOrchestratorPanel({
    orchestration,
    onOrchestrate,
}: {
    orchestration: ReservedCapacityOrchestration | null;
    onOrchestrate: () => void;
}) {
    return (
        <div
            className="reserved-capacity-orchestrator mb-6 rounded bg-slate-900 p-4"
            aria-label="reserved_capacity_orchestrator"
        >
            <div className="mb-3 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-100">
                    오케스트레이터 (composition_step_chain 5 step)
                </h2>
                <button
                    type="button"
                    className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700"
                    onClick={onOrchestrate}
                >
                    오케스트레이션
                </button>
            </div>
            {orchestration ? (
                <>
                    <p className="text-sm text-slate-300">
                        cadence:{" "}
                        <span className="font-mono">
                            {orchestration.cadence}
                        </span>{" "}
                        | status:{" "}
                        <span className="font-mono">
                            {orchestration.orchestration_status}
                        </span>{" "}
                        | dry_run:{" "}
                        <span className="font-mono">
                            {String(orchestration.dry_run)}
                        </span>
                    </p>
                    <p className="text-sm text-slate-300">
                        cadence_hour_kst:{" "}
                        <span className="font-mono">
                            {orchestration.cadence_hour_kst}
                        </span>
                        :00 | next_run_at:{" "}
                        <span className="font-mono">
                            {orchestration.next_run_at ?? "(dry_run)"}
                        </span>
                    </p>
                    <p className="text-xs text-slate-400">
                        composition_step_chain:{" "}
                        {Array.isArray(
                            orchestration.composition_step_chain,
                        )
                            ? orchestration.composition_step_chain.join(" → ")
                            : "(empty)"}
                    </p>
                    {orchestration.owner_approval_required && (
                        <p className="text-sm text-amber-400">
                            owner_approval_required=true → owner_only RBAC +
                            Slack DM + 2FA + approval_chain
                        </p>
                    )}
                    <p className="text-xs text-slate-500">
                        4 cadence: daily 02:00 / weekly Mon 03:00 / monthly
                        1st-day 04:00 / quarterly 1st-day 05:00 KST pytz
                    </p>
                </>
            ) : (
                <p className="text-sm text-slate-400">오케스트레이션 누름</p>
            )}
        </div>
    );
}

// ── 5. ReservedCapacityTrendMiniChart ──
function ReservedCapacityTrendMiniChart({
    orchestration,
}: {
    orchestration: ReservedCapacityOrchestration | null;
}) {
    return (
        <div
            className="reserved-capacity-trend-mini-chart mb-6 rounded bg-slate-900 p-4"
            aria-label="reserved_capacity_trend_mini_chart"
        >
            <h2 className="mb-3 text-lg font-semibold text-slate-100">
                트렌드 (Recharts 2.12.7)
            </h2>
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <p className="text-xs text-slate-400">
                        composition_step_results count
                    </p>
                    <p className="font-mono text-sm text-slate-200">
                        {orchestration
                            ? Object.keys(
                                  orchestration.composition_step_results,
                              ).length
                            : 0}
                    </p>
                </div>
                <div>
                    <p className="text-xs text-slate-400">status</p>
                    <p className="font-mono text-sm text-slate-200">
                        {orchestration?.orchestration_status ?? "(none)"}
                    </p>
                </div>
                <div>
                    <p className="text-xs text-slate-400">cadence</p>
                    <p className="font-mono text-sm text-slate-200">
                        {orchestration?.cadence ?? "(none)"}
                    </p>
                </div>
                <div>
                    <p className="text-xs text-slate-400">
                        high_value_flag
                    </p>
                    <p className="font-mono text-sm text-slate-200">
                        {orchestration
                            ? String(orchestration.high_value_flag)
                            : "(none)"}
                    </p>
                </div>
            </div>
            <p className="mt-3 text-xs text-slate-500">
                AreaChart + BarChart + LineChart + GanttChart + PieChart 5-tab
                placeholder (Recharts 2.12.7 stack pin)
            </p>
        </div>
    );
}

// ── 6. ReservedCapacityDryRunPreviewPanel (T7.3) ──
function ReservedCapacityDryRunPreviewPanel({
    dryRunResult,
    onDryRun,
}: {
    dryRunResult: { orchestration_status: string; audit_action: string } | null;
    onDryRun: () => void;
}) {
    return (
        <div
            className="reserved-capacity-dry-run-preview mb-6 rounded bg-slate-900 p-4"
            aria-label="reserved_capacity_dry_run_preview"
        >
            <div className="mb-3 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-100">
                    드라이런 미리보기 (T7.3 dry-run preview UI)
                </h2>
                <button
                    type="button"
                    className="rounded bg-yellow-600 px-3 py-1 text-sm text-white hover:bg-yellow-700"
                    onClick={onDryRun}
                >
                    드라이런
                </button>
            </div>
            {dryRunResult ? (
                <>
                    <p className="text-sm text-slate-300">
                        orchestration_status:{" "}
                        <span className="font-mono">
                            {dryRunResult.orchestration_status}
                        </span>
                    </p>
                    <p className="text-sm text-slate-300">
                        audit_action:{" "}
                        <span className="font-mono">
                            {dryRunResult.audit_action}
                        </span>
                    </p>
                    <p className="text-xs text-amber-400">
                        dry_run=true → 미리보기만, 실제 INSERT/audit 스킵
                    </p>
                </>
            ) : (
                <p className="text-sm text-slate-400">드라이런 누름</p>
            )}
        </div>
    );
}

// ── 7. ScheduledReservedCapacityDispatchConfigPanel ──
function ScheduledReservedCapacityDispatchConfigPanel({
    dispatches,
    onSchedule,
}: {
    dispatches: ScheduledReservedCapacityDispatch[];
    onSchedule: (req: ScheduleDispatchRequest) => Promise<void> | void;
}) {
    const handleClick = (
        cadence: ReservedCapacityCadence,
    ) => {
        void onSchedule({
            tenant_id: "current",
            dispatch_schedule: cadence,
            recipient_strategy: "owner_only",
            dry_run: true,
        });
    };
    return (
        <div
            className="reserved-capacity-scheduled-dispatch mb-6 rounded bg-slate-900 p-4"
            aria-label="reserved_capacity_scheduled_dispatch"
        >
            <h2 className="mb-3 text-lg font-semibold text-slate-100">
                정기 디스패치 (KST cron)
            </h2>
            <div className="mb-3 flex flex-wrap gap-2">
                <button
                    type="button"
                    className="rounded bg-slate-700 px-3 py-1 text-sm text-slate-100"
                    onClick={() => handleClick("daily")}
                >
                    daily 02:00
                </button>
                <button
                    type="button"
                    className="rounded bg-slate-700 px-3 py-1 text-sm text-slate-100"
                    onClick={() => handleClick("weekly")}
                >
                    weekly Mon 03:00
                </button>
                <button
                    type="button"
                    className="rounded bg-slate-700 px-3 py-1 text-sm text-slate-100"
                    onClick={() => handleClick("monthly")}
                >
                    monthly 1st 04:00
                </button>
                <button
                    type="button"
                    className="rounded bg-slate-700 px-3 py-1 text-sm text-slate-100"
                    onClick={() => handleClick("quarterly")}
                >
                    quarterly 1st 05:00
                </button>
            </div>
            <p className="text-xs text-slate-500">
                KST timezone (pytz Asia/Seoul)
            </p>
            {dispatches.length > 0 && (
                <ul className="mt-3 text-xs text-slate-300">
                    {dispatches.map((d) => (
                        <li key={d.dispatch_id}>
                            {d.dispatch_schedule} | {d.cron_expression} |{" "}
                            {d.status} |{" "}
                            {d.recipient_strategy}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}

export function FinopsReservedCapacityDashboardPanel() {
    const [forecast, setForecast] =
        useState<ReservedCapacityDemandForecast | null>(null);
    const [plan, setPlan] = useState<ReservedCapacityPlan | null>(null);
    const [recommendation, setRecommendation] =
        useState<CommitmentRecommendation | null>(null);
    const [orchestration, setOrchestration] =
        useState<ReservedCapacityOrchestration | null>(null);
    const [dispatches, setDispatches] = useState<
        ScheduledReservedCapacityDispatch[]
    >([]);
    const [dryRunResult, setDryRunResult] = useState<{
        orchestration_status: string;
        audit_action: string;
    } | null>(null);
    const [selectedCadence, setSelectedCadence] =
        useState<ReservedCapacityCadence>("weekly");
    const [selectedIndustry, setSelectedIndustry] =
        useState<OrchestrationScope>("manufacturing");
    const [error, setError] = useState<string | null>(null);

    const handleComputeForecast = async () => {
        try {
            const req: AggregateDemandForecastRequest = {
                tenant_id: "current",
                period_key: "2026-08",
                industry: selectedIndustry,
                five_module_inputs: {
                    phase_13_forecast: 1000000.0,
                    phase_14_optimization: 1100000.0,
                    phase_18_commitment: 1050000.0,
                    phase_19_pricing: 1200000.0,
                    phase_20_multi_cloud: 1150000.0,
                },
                confidence_pct: 80.0,
                previous_demand_krw: 900000.0,
                dry_run: true,
            };
            const result = await aggregateDemandForecast(req);
            setForecast(result);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : String(err));
        }
    };

    const handlePlanCapacity = async () => {
        try {
            const req: PlanReservedCapacityRequest = {
                tenant_id: "current",
                period_key: "2026-08",
                demand_forecast_id:
                    forecast?.demand_forecast_id ?? "demo-demand-forecast-id",
                industry: selectedIndustry,
                dry_run: true,
            };
            const result = await planReservedCapacity(req);
            setPlan(result);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : String(err));
        }
    };

    const handleGenerateRecommendation = async () => {
        try {
            const req: CommitmentRecommendationRequest = {
                tenant_id: "current",
                capacity_plan_id:
                    plan?.capacity_plan_id ?? "demo-capacity-plan-id",
                industry: selectedIndustry,
                dry_run: true,
            };
            const result = await generateCommitmentRecommendation(req);
            setRecommendation(result);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : String(err));
        }
    };

    const handleOrchestrate = async () => {
        try {
            const req: OrchestrateReservedCapacityRequest = {
                tenant_id: "current",
                period_key: "2026-08",
                industry: selectedIndustry,
                scope_chain: [
                    "demand_forecast",
                    "capacity_planning",
                    "commitment_recommendation",
                    "approval",
                    "execute",
                ],
                cadence: selectedCadence,
                dry_run: true,
            };
            const result = await orchestrateReservedCapacity(req);
            setOrchestration(result);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : String(err));
        }
    };

    const handleScheduleDispatch = async (
        req: ScheduleDispatchRequest,
    ) => {
        try {
            const result = await scheduleReservedCapacityDispatch(req);
            setDispatches((prev) => [...prev, result]);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : String(err));
        }
    };

    const handleDryRun = async () => {
        try {
            const req: DryRunRequest = {
                tenant_id: "current",
                period_key: "2026-08",
                industry: selectedIndustry,
                cadence: selectedCadence,
            };
            const result = await runDryRun(req);
            setDryRunResult({
                orchestration_status: result.orchestration_status,
                audit_action: result.audit_action,
            });
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : String(err));
        }
    };

    return (
        <div className="finops-reserved-capacity-dashboard-panel">
            <div className="mb-4 flex flex-wrap gap-4">
                <div>
                    <label
                        htmlFor="reserved-capacity-industry"
                        className="mr-2 text-sm text-slate-300"
                    >
                        industry:
                    </label>
                    <select
                        id="reserved-capacity-industry"
                        className="rounded bg-slate-700 px-2 py-1 text-sm text-slate-100"
                        value={selectedIndustry}
                        onChange={(e) =>
                            setSelectedIndustry(
                                e.target.value as OrchestrationScope,
                            )
                        }
                    >
                        {ALL_INDUSTRIES.map((ind) => (
                            <option key={ind} value={ind}>
                                {ind}
                            </option>
                        ))}
                    </select>
                </div>
                <div>
                    <label
                        htmlFor="reserved-capacity-cadence"
                        className="mr-2 text-sm text-slate-300"
                    >
                        cadence:
                    </label>
                    <select
                        id="reserved-capacity-cadence"
                        className="rounded bg-slate-700 px-2 py-1 text-sm text-slate-100"
                        value={selectedCadence}
                        onChange={(e) =>
                            setSelectedCadence(
                                e.target.value as ReservedCapacityCadence,
                            )
                        }
                    >
                        {ALL_CADENCES.map((c) => (
                            <option key={c} value={c}>
                                {c}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {error && (
                <div
                    className="mb-4 rounded bg-red-900 p-3 text-sm text-red-100"
                    aria-label="reserved_capacity_dashboard_error"
                >
                    {error}
                </div>
            )}

            <DemandForecastPanel
                forecast={forecast}
                onCompute={handleComputeForecast}
            />
            <CapacityPlanningPanel
                plan={plan}
                onPlan={handlePlanCapacity}
            />
            <CommitmentRecommendationPanel
                recommendation={recommendation}
                onGenerate={handleGenerateRecommendation}
            />
            <ReservedCapacityOrchestratorPanel
                orchestration={orchestration}
                onOrchestrate={handleOrchestrate}
            />
            <ReservedCapacityTrendMiniChart orchestration={orchestration} />
            <ReservedCapacityDryRunPreviewPanel
                dryRunResult={dryRunResult}
                onDryRun={handleDryRun}
            />
            <ScheduledReservedCapacityDispatchConfigPanel
                dispatches={dispatches}
                onSchedule={handleScheduleDispatch}
            />
        </div>
    );
}