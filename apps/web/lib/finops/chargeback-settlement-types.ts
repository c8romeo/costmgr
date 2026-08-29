/**
 * Phase 22 wire (cj-style 160번째) — FinOps Chargeback Settlement
 * TypeScript types.
 *
 * Mirrors Python
 * `apps/api/modules/finops/chargeback_settlement/serializers.py`
 * TypedDicts verbatim (CR 12-5 D-PARITY-01 inversion).
 *
 * SettlementRuleType enum: 4 values
 *   flat_fee | proportional_allocation | metered_volume | tag_weighted
 *
 * SettlementStatus enum: 5 values
 *   draft | pending_approval | approved | invoiced | reconciled
 *
 * AllocationDimension enum: 5 values
 *   cost_center | department | business_unit | tag | tenant
 *
 * InvoiceFormat enum: 3 values
 *   pdf | xlsx | csv
 *
 * SettlementCadence enum: 4 values
 *   monthly | quarterly | semi_annual | annual
 *
 * ReconciliationStatus enum: 4 values
 *   matched | variance_detected | retry_exhausted | needs_approval
 */

export type SettlementRuleType =
    | "flat_fee"
    | "proportional_allocation"
    | "metered_volume"
    | "tag_weighted";

export const ALL_SETTLEMENT_RULE_TYPES: SettlementRuleType[] = [
    "flat_fee",
    "proportional_allocation",
    "metered_volume",
    "tag_weighted",
];

export type SettlementStatus =
    | "draft"
    | "pending_approval"
    | "approved"
    | "invoiced"
    | "reconciled";

export const ALL_SETTLEMENT_STATUSES: SettlementStatus[] = [
    "draft",
    "pending_approval",
    "approved",
    "invoiced",
    "reconciled",
];

export type AllocationDimension =
    | "cost_center"
    | "department"
    | "business_unit"
    | "tag"
    | "tenant";

export const ALL_ALLOCATION_DIMENSIONS: AllocationDimension[] = [
    "cost_center",
    "department",
    "business_unit",
    "tag",
    "tenant",
];

export type InvoiceFormat = "pdf" | "xlsx" | "csv";

export const ALL_INVOICE_FORMATS: InvoiceFormat[] = ["pdf", "xlsx", "csv"];

export type SettlementCadence =
    | "monthly"
    | "quarterly"
    | "semi_annual"
    | "annual";

export const ALL_SETTLEMENT_CADENCES: SettlementCadence[] = [
    "monthly",
    "quarterly",
    "semi_annual",
    "annual",
];

export type ReconciliationStatus =
    | "matched"
    | "variance_detected"
    | "retry_exhausted"
    | "needs_approval";

export const ALL_RECONCILIATION_STATUSES: ReconciliationStatus[] = [
    "matched",
    "variance_detected",
    "retry_exhausted",
    "needs_approval",
];

// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const FIVE_MODULE_WEIGHTS: Record<string, number> = {
    phase_11_chargeback: 0.30,
    phase_18_commitment: 0.20,
    phase_19_pricing: 0.20,
    phase_20_multi_cloud: 0.15,
    phase_21_reserved_capacity: 0.15,
};

export const ALLOCATION_DIMENSION_WEIGHTS: Record<
    AllocationDimension,
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    number
> = {
    cost_center: 0.30,
    department: 0.25,
    business_unit: 0.20,
    tag: 0.15,
    tenant: 0.10,
};

export const HIGH_VALUE_THRESHOLD_KRW_PER_YEAR = 10_000_000;

export const RECONCILIATION_TOLERANCE_PCT = 1.0;

export const RECONCILIATION_MAX_RETRIES = 3;

export const RECONCILIATION_AMOUNT_TOLERANCE_KRW = 0.01;

export const MAX_INVOICE_BYTES = 10 * 1024 * 1024;

export const MAX_ALLOCATION_LINES = 10_000;

export interface SettlementRule {
    settlement_id: string;
    tenant_id: string;
    period_key: string;
    rule_name: string;
    rule_type: SettlementRuleType;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    target_amount_krw: number;
    target_dimensions: AllocationDimension[];
    scope_chain: Record<string, unknown>;
    settlement_status: SettlementStatus;
    requires_2fa_challenge: boolean;
    model_version: string;
    trace_id: string;
}

export interface AllocationLine {
    allocation_id: string;
    result_id: string;
    tenant_id: string;
    period_key: string;
    dimension: AllocationDimension;
    dimension_value: string;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    weight: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    allocated_amount_krw: number;
    audit_first_insert: boolean;
    computed_at: string;
    trace_id: string;
}

export interface SettlementResult {
    result_id: string;
    settlement_id: string;
    tenant_id: string;
    period_key: string;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_amount_krw: number;
    five_module_attribution: Record<string, unknown>;
    allocation_breakdown: Record<string, unknown>;
    allocation_lines: AllocationLine[];
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    allocation_count: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    confidence_pct: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    tolerance_band_krw: number;
    settlement_status: SettlementStatus;
    dry_run: boolean;
    computed_at: string;
    last_updated_at: string;
    model_version: string;
    trace_id: string;
}

export interface ReconciliationResult {
    reconciliation_id: string;
    result_id: string;
    tenant_id: string;
    period_key: string;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    allocation_amount_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    invoice_amount_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    ledger_amount_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    variance_pct: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    variance_krw: number;
    reconciliation_status: ReconciliationStatus;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    retry_attempts: number;
    requires_2fa_challenge: boolean;
    model_version: string;
    computed_at: string;
    trace_id: string;
}

export interface CadencePreviewResponse {
    cadence: SettlementCadence;
    period_key: string;
    schedule: Record<string, unknown>;
    scheduled_meta: Record<string, unknown>;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    five_module_weights: Record<string, number>;
}
