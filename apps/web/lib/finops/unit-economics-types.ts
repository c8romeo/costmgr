/**
 * Phase 23 wire (cj-style 164번째) — FinOps Unit Economics
 * TypeScript types.
 *
 * Mirrors Python
 * `apps/api/modules/finops/unit_economics/serializers.py`
 * TypedDicts verbatim (CR 12-5 D-PARITY-01 inversion).
 *
 * UnitEconomicsCalculationStatus enum: 5 values
 *   pending | computing | completed | failed | dry_run_completed
 *
 * UnitEconomicsDimension enum: 5 values (same as Phase 22
 * AllocationDimension — derived from Phase 22 allocation_lines ledger
 * data)
 *   cost_center | department | business_unit | tag | tenant
 *
 * CostPerXMetric enum: 4 values
 *   cost_per_business_unit | cost_per_transaction |
 *   cost_per_department | cost_per_cost_center
 *
 * MarginAnalysisStatus enum: 4 values
 *   healthy | warning | critical | negative
 *
 * UnitEconomicsAlertSeverity enum: 3 values
 *   info | warning | critical
 *
 * UnitEconomicsCadence enum: 4 values
 *   daily | weekly | monthly | quarterly
 *
 * D-FINOPS-12 honestly DEFER (cost_per_customer CRM + multi-currency
 * FX + real-time stream — all honestly DEFER to future Phase 23.x).
 */

export type UnitEconomicsCalculationStatus =
    | "pending"
    | "computing"
    | "completed"
    | "failed"
    | "dry_run_completed";

export const ALL_UNIT_ECONOMICS_CALCULATION_STATUSES: UnitEconomicsCalculationStatus[] =
    ["pending", "computing", "completed", "failed", "dry_run_completed"];

export type UnitEconomicsDimension =
    | "cost_center"
    | "department"
    | "business_unit"
    | "tag"
    | "tenant";

export const ALL_UNIT_ECONOMICS_DIMENSIONS: UnitEconomicsDimension[] = [
    "cost_center",
    "department",
    "business_unit",
    "tag",
    "tenant",
];

export type CostPerXMetric =
    | "cost_per_business_unit"
    | "cost_per_transaction"
    | "cost_per_department"
    | "cost_per_cost_center";

export const ALL_COST_PER_X_METRICS: CostPerXMetric[] = [
    "cost_per_business_unit",
    "cost_per_transaction",
    "cost_per_department",
    "cost_per_cost_center",
];

export type MarginAnalysisStatus =
    | "healthy"
    | "warning"
    | "critical"
    | "negative";

export const ALL_MARGIN_ANALYSIS_STATUSES: MarginAnalysisStatus[] = [
    "healthy",
    "warning",
    "critical",
    "negative",
];

export type UnitEconomicsAlertSeverity = "info" | "warning" | "critical";

export const ALL_UNIT_ECONOMICS_ALERT_SEVERITIES: UnitEconomicsAlertSeverity[] =
    ["info", "warning", "critical"];

export type UnitEconomicsCadence =
    | "daily"
    | "weekly"
    | "monthly"
    | "quarterly";

export const ALL_UNIT_ECONOMICS_CADENCES: UnitEconomicsCadence[] = [
    "daily",
    "weekly",
    "monthly",
    "quarterly",
];

// ── Constants (mirrors Python verbatim) ─────────────────────────────────
export const UNIT_ECONOMICS_ENGINE_MODEL_VERSION = "1.0.0";
export const HIGH_VALUE_THRESHOLD_KRW_PER_YEAR = 10_000_000.0;
export const MARGIN_HEALTHY_THRESHOLD_PCT = 30.0;
export const MARGIN_WARNING_THRESHOLD_PCT = 15.0;
export const MARGIN_CRITICAL_THRESHOLD_PCT = 15.0;
export const MARGIN_NEGATIVE_PCT = 0.0;
export const MAX_BUSINESS_UNITS_PER_TENANT = 1000;
export const MAX_TRANSACTIONS_PER_PERIOD = 100_000;
export const MAX_COST_PER_X_OVERRIDE_KRW = 10_000_000.0;

export const DERIVATION_DIMENSION_WEIGHTS: Record<
    UnitEconomicsDimension,
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    number
> = {
    cost_center: 0.30,
    department: 0.25,
    business_unit: 0.20,
    tag: 0.15,
    tenant: 0.10,
};

// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const COST_PER_X_METRIC_WEIGHTS: Record<CostPerXMetric, number> = {
    cost_per_business_unit: 0.40,
    cost_per_transaction: 0.30,
    cost_per_department: 0.20,
    cost_per_cost_center: 0.10,
};

export const UNIT_ECONOMICS_CADENCE_HOURS_KST: Record<
    UnitEconomicsCadence,
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    readonly [number, number]
> = {
    daily: [3, 30], // 03:30 KST daily (lightweight rollup)
    weekly: [4, 0], // 04:00 KST weekly Monday
    monthly: [4, 30], // 04:30 KST monthly 1st-day
    quarterly: [5, 0], // 05:00 KST quarterly 1st-day
};

export const ALLOWED_TAG_KEYS: string[] = [
    "cost_center",
    "department",
    "business_unit",
    "environment",
    "project",
    "owner",
    "tenant",
];

// ── TypedDicts (mirrors Python verbatim 16+12+10+14+8 fields) ───────────
export interface UnitEconomicsResult {
    unit_economics_id: string;
    tenant_id: string;
    period_key: string;
    source_settlement_id: string; // FK to Phase 22 SettlementResult
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_cost_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_revenue_krw: number; // OPTIONAL — D-FINOPS-12 if no revenue registered
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_units: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_transactions: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    cost_per_business_unit_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    cost_per_transaction_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    margin_pct: number;
    margin_status: MarginAnalysisStatus;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    confidence_pct: number;
    dry_run: boolean;
    computed_at: string;
    last_updated_at: string;
    model_version: string;
    trace_id: string;
}

export interface CostPerBusinessUnitBreakdown {
    breakdown_id: string;
    unit_economics_id: string;
    tenant_id: string;
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
    cost_per_unit_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    confidence_pct: number;
    requires_2fa_challenge: boolean;
    model_version: string;
    computed_at: string;
    trace_id: string;
}

export interface CostPerTransactionBreakdown {
    transaction_id: string;
    unit_economics_id: string;
    tenant_id: string;
    period_key: string;
    business_unit: string;
    cost_center: string;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    allocated_cost_krw: number;
    tag_propagation_json: {
        tags: Record<string, string>;
        // eslint-disable-next-line @typescript-eslint/no-restricted-types
        propagated_tag_count: number;
        // eslint-disable-next-line @typescript-eslint/no-restricted-types
        skipped_tag_count: number;
        tag_filter_dimensions: string[];
    };
    requires_2fa_challenge: boolean;
    model_version: string;
    computed_at: string;
    trace_id: string;
}

export interface MarginAnalysisResult {
    margin_id: string;
    unit_economics_id: string;
    tenant_id: string;
    period_key: string;
    business_unit: string;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_cost_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_revenue_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    margin_amount_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    margin_pct: number;
    margin_status: MarginAnalysisStatus;
    revenue_sources: string[];
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    revenue_completeness_pct: number;
    requires_2fa_challenge: boolean;
    model_version: string;
    computed_at: string;
    trace_id: string;
}

export interface UnitEconomicsAlert {
    alert_id: string;
    tenant_id: string;
    period_key: string;
    margin_id: string;
    severity: UnitEconomicsAlertSeverity;
    alert_type: string;
    alert_message: string;
    requires_2fa_challenge: boolean;
    model_version: string;
    triggered_at: string;
    trace_id: string;
}
