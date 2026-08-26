/**
 * Phase 21 wire (cj-style 151번째) — FinOps Reserved Capacity Planning
 * Client SDK.
 *
 * Mirrors Python `apps/api/modules/finops/reserved_capacity/*` aggregator
 * functions via REST calls to `/api/v1/admin/finops/reserved-capacity/*`.
 *
 * 8 endpoints:
 *   GET /health                          — healthcheck
 *   POST /demand-forecast                — 5-module cross-join aggregator
 *   POST /capacity-plan                  — 6 reserved_capacity_tier selector
 *   POST /commitment-recommendation      — confidence + risk + execution_strategy
 *   POST /orchestrate                    — 5-step composition chain
 *   POST /dispatches                     — 4 cadence KST pytz scheduling
 *   GET /cadence-preview                 — preview cadence schedule
 *   POST /dry-run                        — dry-run mode preview
 *
 * CR 12-5 D-PARITY-01 — TypeScript types match Python TypedDict
 * via `lib/finops/reserved-capacity-types.ts` verbatim.
 * AD-14 stack pin — fetch API + AbortSignal + idempotency-key header.
 */

import type {
    ReservedCapacityDemandForecast,
    ReservedCapacityPlan,
    CommitmentRecommendation,
    ReservedCapacityOrchestration,
    ScheduledReservedCapacityDispatch,
    ReservedCapacityKPIDashboard,
    ReservedCapacityCadence,
    OrchestrationScope,
} from "./reserved-capacity-types";

const RESERVED_CAPACITY_API_PREFIX =
    "/api/v1/admin/finops/reserved-capacity";

async function fetchTyped<T>(
    url: string,
    init: RequestInit = {},
    traceId: string = crypto.randomUUID(),
): Promise<T> {
    const headers = new Headers(init.headers);
    headers.set("Content-Type", "application/json");
    headers.set("X-Trace-Id", traceId);
    const response = await fetch(url, { ...init, headers });
    if (!response.ok) {
        const errPayload = (await response.json().catch(() => ({}))) as {
            detail?: string;
        };
        throw new Error(
            errPayload.detail ?? `HTTP ${response.status} on ${url}`,
        );
    }
    return (await response.json()) as T;
}

export interface AggregateDemandForecastRequest {
    tenant_id: string;
    period_key: string;
    industry: OrchestrationScope;
    five_module_inputs: Record<string, number>;
    confidence_pct?: number;
    previous_demand_krw?: number | null;
    dry_run?: boolean;
}

export interface PlanReservedCapacityRequest {
    tenant_id: string;
    period_key: string;
    demand_forecast_id: string;
    industry: OrchestrationScope;
    dry_run?: boolean;
}

export interface CommitmentRecommendationRequest {
    tenant_id: string;
    capacity_plan_id: string;
    industry: OrchestrationScope;
    dry_run?: boolean;
}

export interface OrchestrateReservedCapacityRequest {
    tenant_id: string;
    period_key: string;
    industry: OrchestrationScope;
    scope_chain: string[];
    cadence: ReservedCapacityCadence;
    dry_run?: boolean;
}

export interface ScheduleDispatchRequest {
    tenant_id: string;
    dispatch_schedule: ReservedCapacityCadence;
    recipient_strategy: "owner_only" | "executive" | "finops_team" | "custom_recipients";
    orchestration_id?: string | null;
    dry_run?: boolean;
}

export interface CadencePreviewResponse {
    cadence: ReservedCapacityCadence;
    cron_expression: string;
    next_run_at_kst: string;
    cadence_hour_kst: number;
    cadence_minute_kst: number;
}

export interface DryRunRequest {
    tenant_id: string;
    period_key: string;
    industry: OrchestrationScope;
    cadence: ReservedCapacityCadence;
}

export interface DryRunResponse {
    orchestration_id: string;
    orchestration_status: "dry_run";
    composition_step_chain: string[];
    composition_step_results: Record<string, unknown>;
    audit_action: "reserved_capacity_dry_run_executed";
    dry_run: true;
    computed_at: string;
}

export async function aggregateDemandForecast(
    req: AggregateDemandForecastRequest,
    traceId?: string,
): Promise<ReservedCapacityDemandForecast> {
    return fetchTyped<ReservedCapacityDemandForecast>(
        `${RESERVED_CAPACITY_API_PREFIX}/demand-forecast`,
        { method: "POST", body: JSON.stringify(req) },
        traceId,
    );
}

export async function planReservedCapacity(
    req: PlanReservedCapacityRequest,
    traceId?: string,
): Promise<ReservedCapacityPlan> {
    return fetchTyped<ReservedCapacityPlan>(
        `${RESERVED_CAPACITY_API_PREFIX}/capacity-plan`,
        { method: "POST", body: JSON.stringify(req) },
        traceId,
    );
}

export async function generateCommitmentRecommendation(
    req: CommitmentRecommendationRequest,
    traceId?: string,
): Promise<CommitmentRecommendation> {
    return fetchTyped<CommitmentRecommendation>(
        `${RESERVED_CAPACITY_API_PREFIX}/commitment-recommendation`,
        { method: "POST", body: JSON.stringify(req) },
        traceId,
    );
}

export async function orchestrateReservedCapacity(
    req: OrchestrateReservedCapacityRequest,
    traceId?: string,
): Promise<ReservedCapacityOrchestration> {
    return fetchTyped<ReservedCapacityOrchestration>(
        `${RESERVED_CAPACITY_API_PREFIX}/orchestrate`,
        { method: "POST", body: JSON.stringify(req) },
        traceId,
    );
}

export async function scheduleReservedCapacityDispatch(
    req: ScheduleDispatchRequest,
    traceId?: string,
): Promise<ScheduledReservedCapacityDispatch> {
    return fetchTyped<ScheduledReservedCapacityDispatch>(
        `${RESERVED_CAPACITY_API_PREFIX}/dispatches`,
        { method: "POST", body: JSON.stringify(req) },
        traceId,
    );
}

export async function fetchCadencePreview(
    cadence: ReservedCapacityCadence,
    traceId?: string,
): Promise<CadencePreviewResponse> {
    return fetchTyped<CadencePreviewResponse>(
        `${RESERVED_CAPACITY_API_PREFIX}/cadence-preview?cadence=${cadence}`,
        { method: "GET" },
        traceId,
    );
}

export async function runDryRun(
    req: DryRunRequest,
    traceId?: string,
): Promise<DryRunResponse> {
    return fetchTyped<DryRunResponse>(
        `${RESERVED_CAPACITY_API_PREFIX}/dry-run`,
        { method: "POST", body: JSON.stringify(req) },
        traceId,
    );
}

export async function fetchReservedCapacityKPI(
    tenantId: string,
    periodKey: string,
    traceId?: string,
): Promise<ReservedCapacityKPIDashboard[]> {
    return fetchTyped<ReservedCapacityKPIDashboard[]>(
        `${RESERVED_CAPACITY_API_PREFIX}/kpi?tenant_id=${encodeURIComponent(tenantId)}&period_key=${encodeURIComponent(periodKey)}`,
        { method: "GET" },
        traceId,
    );
}