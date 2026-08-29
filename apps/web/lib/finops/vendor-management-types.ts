/**
 * vendor-management-types — Phase 25 TypeScript types for FinOps Vendor Management.
 *
 * Phase 25 wire (cj-style 173번째) — Mirrors Python TypedDicts in
 * `apps/api/modules/finops/vendor_management/serializers.py`. CR 12-5
 * D-PARITY-01 inversion — Python TypedDict ↔ TypeScript interface
 * parity preserved.
 *
 * Provides:
 * - VendorStatus (4-state lifecycle)
 * - VendorCategory (6-category taxonomy)
 * - VendorContractLifecycle (7-state contract lifecycle)
 * - VendorPerformanceSeverity (3-tier severity)
 * - VendorSelectionMode (3 dry-run modes)
 * - VendorApprovalStepStatus (4-state approval step)
 * - Vendor (18 fields)
 * - VendorSelectionScore (12 fields)
 * - VendorContract (16 fields)
 * - VendorPerformanceScorecard (14 fields)
 * - VendorSpendAttribution (12 fields)
 * - VendorBlacklistEntry (10 fields)
 */

export type VendorStatus =
    | "active"
    | "inactive"
    | "under_review"
    | "blacklisted";

export type VendorCategory =
    | "cloud"
    | "saas"
    | "outsourcing"
    | "consulting"
    | "hardware"
    | "other";

export type VendorContractLifecycle =
    | "draft"
    | "pending_approval"
    | "approved"
    | "active"
    | "expiring_soon"
    | "renewed"
    | "expired"
    | "terminated";

export type VendorPerformanceSeverity =
    | "excellent"
    | "needs_improvement"
    | "critical";

export type VendorSelectionMode = "actual" | "preview" | "skip";

export type VendorApprovalStepStatus =
    | "pending"
    | "approved"
    | "rejected"
    | "skipped";

export interface Vendor {
    vendor_id: string;
    tenant_id: string;
    vendor_name: string;
    vendor_category: VendorCategory;
    status: VendorStatus;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    cost_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    performance_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    reliability_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    compliance_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    strategic_fit_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    risk_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    contract_count: number;
    blacklist_reason: string;
    high_value: boolean;
    requires_2fa: boolean;
    source_attribution: Record<string, unknown>;
    created_at: string;
    updated_at: string;
}

export interface VendorSelectionScore {
    selection_id: string;
    vendor_id: string;
    tenant_id: string;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    cost_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    performance_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    reliability_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    compliance_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    strategic_fit_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    weighted_total_score: number;
    per_tenant_override: boolean;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    score_version: number;
    excluded_by_threshold: boolean;
    created_at: string;
}

export interface VendorContract {
    contract_id: string;
    vendor_id: string;
    tenant_id: string;
    contract_name: string;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    contract_value_krw: number;
    lifecycle: VendorContractLifecycle;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    step_index: number;
    approval_chain: string[];
    auto_renewal_enabled: boolean;
    high_value: boolean;
    requires_2fa: boolean;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    computed_total_contract_value: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    budget_ceiling_krw: number;
    over_budget: boolean;
    blacklist_gate_passed: boolean;
    audit_log_id: string;
    created_at: string;
    updated_at: string;
}

export interface VendorPerformanceScorecard {
    scorecard_id: string;
    vendor_id: string;
    tenant_id: string;
    period_key: string;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    sla_compliance_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    cost_efficiency_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    support_quality_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    innovation_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    weighted_total_score: number;
    severity: VendorPerformanceSeverity;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    monthly_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    quarterly_score: number;
    source_attribution: Record<string, unknown>;
    audit_log_id: string;
    computed_at: string;
}

export interface VendorSpendAttribution {
    attribution_id: string;
    vendor_id: string;
    tenant_id: string;
    period_key: string;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    actual_amount: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    budget_amount: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    variance_amount: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    variance_pct: number;
    over_budget: boolean;
    cross_budget_reconciled: boolean;
    audit_log_id: string;
    computed_at: string;
}

export interface VendorBlacklistEntry {
    blacklist_id: string;
    vendor_id: string;
    tenant_id: string;
    reason: string;
    severity: string;
    block_contract_approval: boolean;
    block_selection: boolean;
    block_performance_evaluation: boolean;
    requires_owner_override: boolean;
    created_at: string;
}

export interface VendorSelectionDimensionWeights {
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    cost: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    performance: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    reliability: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    compliance: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    strategic_fit: number;
}

export const VENDOR_SELECTION_DIMENSION_WEIGHTS: VendorSelectionDimensionWeights = {
    cost: 0.30,
    performance: 0.25,
    reliability: 0.20,
    compliance: 0.15,
    strategic_fit: 0.10,
};

export interface VendorPerformanceDimensionWeights {
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    sla_compliance: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    cost_efficiency: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    support_quality: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    innovation: number;
}

export const VENDOR_PERFORMANCE_DIMENSION_WEIGHTS: VendorPerformanceDimensionWeights = {
    sla_compliance: 0.30,
    cost_efficiency: 0.25,
    support_quality: 0.25,
    innovation: 0.20,
};

export const SELECTION_THRESHOLD_DEFAULT = 60.0;
export const SELECTION_CANDIDATE_LIMIT_DEFAULT = 10;
export const SELECTION_SCORE_VERSION_MAX = 100.0;
export const HIGH_VALUE_THRESHOLD_KRW_PER_YEAR = 10_000_000.0;
export const AUTO_RENEWAL_WINDOW_DAYS = 90;