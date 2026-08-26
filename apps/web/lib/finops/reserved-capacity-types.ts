/**
 * Phase 21 wire (cj-style 151번째) — FinOps Reserved Capacity Planning
 * TypeScript types.
 *
 * Mirrors Python `apps/api/modules/finops/reserved_capacity/serializers.py`
 * TypedDicts verbatim (CR 12-5 D-PARITY-01 inversion).
 *
 * ReservedCapacityTier enum: 6 values
 *   1y_no_upfront | 1y_partial_upfront | 1y_all_upfront |
 *   3y_no_upfront | 3y_partial_upfront | 3y_all_upfront
 *
 * ExecutionStrategy enum: 4 values
 *   auto_execute_ready | manual_review_required |
 *   owner_approval_required | low_confidence
 *
 * ReservedCapacityCadence enum: 4 values
 *   daily | weekly | monthly | quarterly
 *
 * OrchestrationScope enum: 4 values (industry)
 *   manufacturing | service | manufacturing_service | manufacturing_service_other
 */

export type ReservedCapacityTier =
    | "1y_no_upfront"
    | "1y_partial_upfront"
    | "1y_all_upfront"
    | "3y_no_upfront"
    | "3y_partial_upfront"
    | "3y_all_upfront";

export const ALL_RESERVED_CAPACITY_TIERS: ReservedCapacityTier[] = [
    "1y_no_upfront",
    "1y_partial_upfront",
    "1y_all_upfront",
    "3y_no_upfront",
    "3y_partial_upfront",
    "3y_all_upfront",
];

export type ExecutionStrategy =
    | "auto_execute_ready"
    | "manual_review_required"
    | "owner_approval_required"
    | "low_confidence";

export const ALL_EXECUTION_STRATEGIES: ExecutionStrategy[] = [
    "auto_execute_ready",
    "manual_review_required",
    "owner_approval_required",
    "low_confidence",
];

export type ReservedCapacityCadence =
    | "daily"
    | "weekly"
    | "monthly"
    | "quarterly";

export const ALL_RESERVED_CAPACITY_CADENCES: ReservedCapacityCadence[] = [
    "daily",
    "weekly",
    "monthly",
    "quarterly",
];

export type OrchestrationScope =
    | "manufacturing"
    | "service"
    | "manufacturing_service"
    | "manufacturing_service_other";

export const ALL_ORCHESTRATION_SCOPES: OrchestrationScope[] = [
    "manufacturing",
    "service",
    "manufacturing_service",
    "manufacturing_service_other",
];

export interface ReservedCapacityDemandForecast {
    demand_forecast_id: string;
    tenant_id: string;
    period_key: string;
    industry: OrchestrationScope;
    scope_chain: Record<string, unknown>;
    forecasted_demand_krw: number;
    confidence_interval_low_krw: number;
    confidence_interval_high_krw: number;
    seasonal_factor: number;
    growth_rate_pct: number;
    five_module_attribution: Record<string, unknown>;
    confidence_pct: number;
    model_version: string;
    computed_at: string;
    last_updated_at: string;
    trace_id: string;
}

export interface ReservedCapacityPlan {
    capacity_plan_id: string;
    tenant_id: string;
    period_key: string;
    demand_forecast_id: string;
    industry: OrchestrationScope;
    recommended_tier: ReservedCapacityTier;
    break_even_utilization_pct: number;
    capacity_headroom_pct: number;
    target_reserved_capacity_units: number;
    estimated_savings_krw: number;
    estimated_savings_pct: number;
    minimum_savings_krw_threshold: number;
    commitment_term_months: number;
    upfront_payment_option: "no_upfront" | "partial_upfront" | "all_upfront";
    capacity_plan_status: "proposed" | "approved" | "executed" | "rejected";
    model_version: string;
    computed_at: string;
    trace_id: string;
}

export interface CommitmentRecommendation {
    commitment_recommendation_id: string;
    tenant_id: string;
    capacity_plan_id: string;
    period_key: string;
    industry: OrchestrationScope;
    recommended_tier: ReservedCapacityTier;
    confidence_score: number;
    risk_score: number;
    execution_strategy: ExecutionStrategy;
    high_value_flag: boolean;
    requires_2fa_challenge: boolean;
    estimated_annual_savings_krw: number;
    estimated_annual_savings_pct: number;
    confidence_breakdown: Record<string, unknown>;
    risk_breakdown: Record<string, unknown>;
    model_version: string;
    computed_at: string;
    trace_id: string;
}

export interface ReservedCapacityOrchestration {
    orchestration_id: string;
    tenant_id: string;
    period_key: string;
    scope_chain: unknown[];
    composition_step_chain: unknown[];
    composition_step_results: Record<string, unknown>;
    cadence: ReservedCapacityCadence;
    cadence_hour_kst: number;
    cadence_minute_kst: number;
    next_run_at: string | null;
    dry_run: boolean;
    commitment_recommendation_id: string | null;
    capacity_plan_id: string | null;
    demand_forecast_id: string | null;
    orchestration_status:
        | "pending"
        | "running"
        | "completed"
        | "failed"
        | "dry_run";
    high_value_flag: boolean;
    owner_approval_required: boolean;
    model_version: string;
    computed_at: string;
    trace_id: string;
}

export interface ScheduledReservedCapacityDispatch {
    dispatch_id: string;
    tenant_id: string;
    dispatch_schedule: ReservedCapacityCadence;
    cron_expression: string;
    recipient_strategy:
        | "owner_only"
        | "executive"
        | "finops_team"
        | "custom_recipients";
    recipient_list: Record<string, unknown>;
    orchestration_id: string | null;
    status:
        | "scheduled"
        | "running"
        | "completed"
        | "failed"
        | "cancelled";
    scheduled_at: string;
    last_run_at: string | null;
    next_run_at: string | null;
    trace_id: string;
}

export interface ReservedCapacityKPIDashboard {
    kpi_refresh_id: string;
    tenant_id: string;
    period_key: string;
    industry: OrchestrationScope;
    total_reserved_capacity_units: number;
    total_estimated_savings_krw: number;
    average_break_even_utilization_pct: number;
    high_value_commitment_count: number;
    low_confidence_count: number;
    refresh_status: "success" | "failed" | "pending";
    refreshed_at: string;
    model_version: string;
    trace_id: string;
}