/**
 * Phase 23 wire (cj-style 164번째) — FinOps Unit Economics Client.
 *
 * Mirrors Python
 * `apps/api/modules/finops/unit_economics/unit_economics_routes.py`
 * verbatim (CR 12-5 D-PARITY-01 inversion).
 *
 * 9 endpoints:
 * 1. computeUnitEconomics — POST /api/v1/finops/unit-economics/compute
 * 2. refreshCostPerBusinessUnit — POST /api/v1/finops/unit-economics/cost-per-business-unit
 * 3. computeCostPerTransaction — POST /api/v1/finops/unit-economics/cost-per-transaction
 * 4. executeMarginAnalysis — POST /api/v1/finops/unit-economics/margin-analysis
 * 5. runDryRun — POST /api/v1/finops/unit-economics/dry-run
 * 6. fetchTrend — GET /api/v1/finops/unit-economics/trend
 * 7. executeCalculation — POST /api/v1/finops/unit-economics/calculation
 * 8. fetchCadencePreview — GET /api/v1/finops/unit-economics/cadence-preview
 * 9. healthcheck — GET /api/v1/finops/unit-economics/healthcheck
 *
 * D-FINOPS-12 honestly DEFER (cost_per_customer CRM + multi-currency
 * FX + real-time stream — all honestly DEFER to future Phase 23.x).
 */

import type {
    CostPerBusinessUnitBreakdown,
    CostPerTransactionBreakdown,
    MarginAnalysisResult,
    UnitEconomicsCadence,
    UnitEconomicsDimension,
    UnitEconomicsResult,
} from "@/lib/finops/unit-economics-types";

const API_BASE_URL = "/api/v1/finops/unit-economics";

export interface ComputeUnitEconomicsRequest {
    period_key: string;
    source_settlement_id: string;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_cost_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_revenue_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_units: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_transactions: number;
    target_dimensions: UnitEconomicsDimension[];
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    five_dim_inputs: Record<string, number>;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    allocation_count: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    revenue_completeness_pct: number;
    calculation_status?: string;
    requires_2fa_challenge?: boolean;
    dry_run?: boolean;
}

export interface RefreshCostPerBusinessUnitRequest {
    unit_economics_id: string;
    period_key: string;
    business_unit: string;
    cost_center: string;
    department: string;
    tag_key: string;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    allocated_cost_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    transaction_count: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    cost_center_amount_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    department_amount_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    business_unit_amount_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    tag_amount_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    tenant_amount_krw: number;
    is_override?: boolean;
    requires_2fa_challenge?: boolean;
    dry_run?: boolean;
}

export interface ComputeCostPerTransactionRequest {
    unit_economics_id: string;
    period_key: string;
    transaction_id: string;
    business_unit: string;
    cost_center: string;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    allocated_cost_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    transaction_count: number;
    phase_22_settlement_tags?: Record<string, string>;
    requires_2fa_challenge?: boolean;
    dry_run?: boolean;
}

export interface ExecuteMarginAnalysisRequest {
    unit_economics_id: string;
    period_key: string;
    business_unit: string;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_cost_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_revenue_krw: number;
    revenue_sources?: string[];
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    revenue_completeness_pct?: number;
    requires_2fa_challenge?: boolean;
    dry_run?: boolean;
}

export interface DryRunRequest {
    period_key: string;
    source_settlement_id: string;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_cost_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_revenue_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_units: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_transactions: number;
    target_dimensions: UnitEconomicsDimension[];
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    five_dim_inputs: Record<string, number>;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    allocation_count: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    revenue_completeness_pct: number;
}

export interface CalculationRequest {
    source_settlement_id: string;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    five_dim_inputs: Record<string, number>;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_cost_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_revenue_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_units: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_transactions: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    allocation_count: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    revenue_completeness_pct: number;
    target_dimensions: UnitEconomicsDimension[];
    cadence: UnitEconomicsCadence;
    dry_run?: boolean;
}

async function postJson<T>(path: string, body: object): Promise<T> {
    const res = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        throw new Error(`POST ${path} failed: ${res.status}`);
    }
    return res.json() as Promise<T>;
}

async function getJson<T>(path: string): Promise<T> {
    const res = await fetch(path, { method: "GET" });
    if (!res.ok) {
        throw new Error(`GET ${path} failed: ${res.status}`);
    }
    return res.json() as Promise<T>;
}

export async function computeUnitEconomics(
    req: ComputeUnitEconomicsRequest
): Promise<{ result: UnitEconomicsResult; trace_id: string }> {
    return postJson(`${API_BASE_URL}/compute`, req);
}

export async function refreshCostPerBusinessUnit(
    req: RefreshCostPerBusinessUnitRequest
): Promise<{ breakdown: CostPerBusinessUnitBreakdown; trace_id: string }> {
    return postJson(`${API_BASE_URL}/cost-per-business-unit`, req);
}

export async function computeCostPerTransaction(
    req: ComputeCostPerTransactionRequest
): Promise<{ transaction: CostPerTransactionBreakdown; trace_id: string }> {
    return postJson(`${API_BASE_URL}/cost-per-transaction`, req);
}

export async function executeMarginAnalysis(
    req: ExecuteMarginAnalysisRequest
): Promise<{ margin: MarginAnalysisResult; trace_id: string }> {
    return postJson(`${API_BASE_URL}/margin-analysis`, req);
}

export async function runDryRun(
    req: DryRunRequest
): Promise<{ dry_run_result: UnitEconomicsResult; trace_id: string; dry_run: boolean }> {
    return postJson(`${API_BASE_URL}/dry-run`, req);
}

export async function fetchTrend(
    // eslint-disable-next-line camelcase
    period_key: string | null
): Promise<{
    results: UnitEconomicsResult[];
    period_key: string | null;
    tenant_id: string;
    trace_id: string;
}> {
    const params = new URLSearchParams();
    // eslint-disable-next-line camelcase
    if (period_key) {
        params.set("period_key", period_key);
    }
    const qs = params.toString();
    return getJson(
        qs ? `${API_BASE_URL}/trend?${qs}` : `${API_BASE_URL}/trend`
    );
}

export async function executeCalculation(
    req: CalculationRequest
): Promise<{ result: UnitEconomicsResult; trace_id: string }> {
    return postJson(`${API_BASE_URL}/calculation`, req);
}

export async function fetchCadencePreview(): Promise<{
    schedule: Record<
        UnitEconomicsCadence,
        {
            // eslint-disable-next-line @typescript-eslint/no-restricted-types
            hour_kst: number;
            // eslint-disable-next-line @typescript-eslint/no-restricted-types
            minute_kst: number;
            period_key: string;
            timezone: string;
        }
    >;
    now_kst: string;
    all_cadences: UnitEconomicsCadence[];
    trace_id: string;
}> {
    return getJson(`${API_BASE_URL}/cadence-preview`);
}

export async function healthcheck(): Promise<{
    status: string;
    module: string;
    module_id: string;
    model_version: string;
    tenant_id: string;
    trace_id: string;
    capability: string;
    all_cost_per_x_metrics: string[];
    all_cadences: UnitEconomicsCadence[];
}> {
    return getJson(`${API_BASE_URL}/healthcheck`);
}
