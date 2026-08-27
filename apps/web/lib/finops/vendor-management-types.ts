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
    cost_score: number;
    performance_score: number;
    reliability_score: number;
    compliance_score: number;
    strategic_fit_score: number;
    risk_score: number;
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
    cost_score: number;
    performance_score: number;
    reliability_score: number;
    compliance_score: number;
    strategic_fit_score: number;
    weighted_total_score: number;
    per_tenant_override: boolean;
    score_version: number;
    excluded_by_threshold: boolean;
    created_at: string;
}

export interface VendorContract {
    contract_id: string;
    vendor_id: string;
    tenant_id: string;
    contract_name: string;
    contract_value_krw: number;
    lifecycle: VendorContractLifecycle;
    step_index: number;
    approval_chain: string[];
    auto_renewal_enabled: boolean;
    high_value: boolean;
    requires_2fa: boolean;
    computed_total_contract_value: number;
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
    sla_compliance_score: number;
    cost_efficiency_score: number;
    support_quality_score: number;
    innovation_score: number;
    weighted_total_score: number;
    severity: VendorPerformanceSeverity;
    monthly_score: number;
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
    actual_amount: number;
    budget_amount: number;
    variance_amount: number;
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
    cost: number;
    performance: number;
    reliability: number;
    compliance: number;
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
    sla_compliance: number;
    cost_efficiency: number;
    support_quality: number;
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