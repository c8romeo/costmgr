/**
 * apps.web.lib.finops.budget-planning-types — Phase 24 TypeScript mirror.
 *
 * Phase 24 wire (cj-style 169번째) — FinOps Budget Planning pre-allocation
 * layer TypeScript interfaces (PRD §F40.1~§F40.8 verbatim + AD-52 (a)~(g)
 * 7 sub-decisions + CR 12-5 D-PARITY-01 inversion parity with
 * apps/api/modules/finops/budget_planning/serializers.py).
 *
 * 5 NEW TypeScript interfaces:
 * 1. BudgetPlan (14 fields)
 * 2. BudgetAllocationLine (12 fields)
 * 3. BudgetApprovalStep (10 fields)
 * 4. BudgetVsActual (16 fields)
 * 5. BudgetAlert (12 fields)
 *
 * CR lessons applied:
 * - CR 12-5 D-PARITY-01 inversion — Python TypedDict ↔ TypeScript
 *   interface parity verbatim mirror.
 * - AD-52 (a)~(g) 7 sub-decisions.
 * - NFR4 PII minimization PRESERVED.
 * - NFR18 ko-KR SSOT (finops_budget_planning.* namespace).
 */

export type BudgetPlanPeriodType = "annual" | "quarterly" | "monthly";

export type BudgetPlanLifecycle =
    | "draft"
    | "pending_approval"
    | "approved"
    | "closed";

export type BudgetPlanDryRunMode = "actual" | "preview" | "skip";

export type BudgetApprovalStepStatus =
    | "pending"
    | "approved"
    | "rejected"
    | "skipped";

export type BudgetAlertSeverity = "warning" | "critical" | "escalated" | "ok";

export type BudgetPlanDimension =
    | "cost_center"
    | "department"
    | "business_unit"
    | "tag"
    | "tenant";

export interface BudgetPlan {
    plan_id: string;
    tenant_id: string;
    period_key: string;
    period_type: BudgetPlanPeriodType;
    lifecycle: BudgetPlanLifecycle;
    total_budget_amount: number;
    scope_dimensions: string[];
    approval_chain: string[];
    high_value: boolean;
    requires_2fa: boolean;
    source_attribution: Record<string, unknown>;
    created_at: string;
    updated_at: string;
    dry_run: boolean;
}

export interface BudgetAllocationLine {
    allocation_id: string;
    plan_id: string;
    tenant_id: string;
    dimension: BudgetPlanDimension;
    dimension_value: string;
    weight: number;
    allocated_amount: number;
    per_tenant_override: boolean;
    source_line_id: string;
    created_at: string;
    verified: boolean;
    retry_count: number;
}

export interface BudgetApprovalStep {
    step_id: string;
    plan_id: string;
    step_index: number;
    approver_actor_id: string;
    status: BudgetApprovalStepStatus;
    decided_at: string;
    requires_2fa: boolean;
    two_fa_verified: boolean;
    comment: string;
    audit_log_id: string;
}

export interface BudgetVsActual {
    variance_id: string;
    plan_id: string;
    tenant_id: string;
    period_key: string;
    dimension: BudgetPlanDimension;
    dimension_value: string;
    budget_amount: number;
    actual_amount: number;
    variance_amount: number;
    variance_pct: number;
    severity: BudgetAlertSeverity;
    source_attribution: Record<string, unknown>;
    computed_at: string;
    over_budget: boolean;
    escalation_chain_id: string;
    audit_log_id: string;
}

export interface BudgetAlert {
    alert_id: string;
    plan_id: string;
    tenant_id: string;
    severity: BudgetAlertSeverity;
    variance_pct: number;
    triggered_at: string;
    channels_notified: string[];
    escalation_level: number;
    high_value: boolean;
    requires_2fa: boolean;
    acknowledged_by: string | null;
    audit_log_id: string;
}

// ── Input request types ───────────────────────────────────────────────────
export interface CreateBudgetPlanRequest {
    tenant_id: string;
    period_key: string;
    period_type: BudgetPlanPeriodType;
    scope: string[];
    total_budget_amount: number;
    approval_chain?: string[];
    dry_run?: boolean;
    actor_id?: string;
}

export interface AllocateBudgetRequest {
    plan_id: string;
    tenant_id: string;
    total_budget_amount: number;
    dim_rows: Array<{
        dimension: BudgetPlanDimension;
        dimension_value: string;
        source_line_id?: string;
    }>;
    per_tenant_override?: Record<string, number>;
    actor_id?: string;
    dry_run?: boolean;
}

export interface SubmitForApprovalRequest {
    plan_id: string;
    tenant_id: string;
    plan_total_budget_amount: number;
    approval_chain: string[];
    actor_id?: string;
}

export interface ApproveStepRequest {
    step_id: string;
    plan_id: string;
    decision: BudgetApprovalStepStatus;
    actor_id: string;
    two_fa_verified?: boolean;
    comment?: string;
}

export interface ComputeVsActualRequest {
    plan_id: string;
    tenant_id: string;
    period_key: string;
    actual_amounts: Record<string, number>;
    actor_id?: string;
}

export interface TriggerAlertRequest {
    plan_id: string;
    tenant_id: string;
    variance_pct: number;
    plan_total_budget_amount: number;
    actor_id?: string;
    dry_run?: boolean;
}

// ── Response types ────────────────────────────────────────────────────────
export interface BudgetPlanningHealthcheck {
    status: "ok" | "degraded" | "error";
    module_tag: string;
    model_version: string;
    high_value_threshold_krw_per_year: number;
}
