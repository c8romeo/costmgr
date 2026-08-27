"""apps.api.modules.finops.budget_planning — Phase 24 FinOps Budget Planning module.

Phase 24 wire (cj-style 169번째) — FinOps Budget Planning pre-allocation
layer territory (PRD §F40.1~§F40.8 verbatim + AD-52 (a)~(g) 7
sub-decisions).

5-NEW backend budget_planning modules + scheduled job + FastAPI router
(mirroring Phase 22 5-module + scheduled dispatch + router pattern verbatim +
Phase 23 5-module + scheduled calculation + router pattern verbatim EXTENSION):

1. `budget_plan_engine.py` — budget_plan engine + 5-dim cross-join
   (derived from Phase 22 allocation_lines + Phase 23 unit_economics_results
   ledger data)
2. `budget_allocation.py` — 5-dim weighted allocation
   (cost_center 0.30 + department 0.25 + business_unit 0.20 + tag 0.15 +
   tenant 0.10) + per-tenant override > industry baseline > system default
   precedence + ±0.01 KRW total verification + 3 auto-retries +
   admin email alert + zero/negative amount preservation
3. `budget_approval_workflow.py` — sequential approval chain (step_index
   ordering) + 4-state step status (pending/approved/rejected/skipped) +
   Epic 12 2FA 챌린지 mandatory ≥10M KRW/year (RFC 6238 TOTP) +
   tenant_owner approval_chain + Slack DM notification + rejection rolls
   plan back to draft
4. `budget_vs_actual.py` — variance computation
   (Phase 22 settlement_results.total_settlement_amount JOIN
    Phase 24 BudgetPlan.total_budget_amount on
    (tenant_id, period_key, dimension))
   + variance_amount = budget_allocation - actual_allocation +
   variance_pct = variance_amount / budget_allocation +
   over-budget detection (warning 10% + critical 25%)
5. `budget_alert.py` — over-budget alert + auto-escalation chain
   (warning Slack DM + critical admin email + Teams #critical-alerts +
   on-call rotation) + 1 NEW CLI flag
   `--finops-budget-planning-over-budget-alert-dry-run`
6. `scheduled_budget_planning_jobs.py` — apscheduler 3.10.4 +
   pytz 2024.1 + 4 cadence (daily_lifecycle 04:00 + weekly_variance 04:30 +
   monthly_rollover 05:00 + quarterly_review 05:30 KST) +
   4 LISTEN/NOTIFY channels
7. `budget_planning_routes.py` — FastAPI router 9 endpoints
8. `serializers.py` — TypedDicts + Enums + Constants

Module tag: `m24_finops_budget_planning`
ALLOWED_SERVICE_SUBMODULES EXTENSION 신규 결정 wire
(Phase 22 m22_finops_chargeback_settlement + Phase 23 m23_finops_unit_economics
패턴 verbatim mirror).

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — 8 NEW audit actions.
- CR 1-1 ContextVar — trace_id propagation.
- CR 1-1 RSC boundary.
- CR 5-1 banker's rounding — Decimal precision verbatim.
- CR 11-2 AUTHORIZABLE_TARGET_EVENT_TYPES — auth-layer check.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 16 NEW typed exceptions.
- CR 12-5 D-PARITY-01 — TypeScript mirror parity.
- CR 12-5 D-GATE-01 — capability gate fail-closed.
- AD-14 stack pin — Recharts 2.12.7 + noto-sans-cjk-kr +
  apscheduler 3.10.4 + pytz 2024.1.
- AD-22 owner-only RBAC.
- AD-52 (a)~(g) 7 sub-decisions.
- Epic 12 2FA 챌린지 mandatory high-value (≥10M KRW/year).
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT (finops_budget_planning.* namespace EXTENSION).
- D-FINOPS-13 honestly DEFER (multi-currency FX + zero-based budgeting +
  incremental budgeting + envelope budgeting + scenario A/B testing +
  per-budget approval override — all honestly DEFER to future Phase 24.x).
- CR 11-3 ALLOWED_SERVICE_SUBMODULES 즉시 sweep EXTENSION
  m24_finops_budget_planning (Phase 24 58th honest-DEFER cycle).
"""
from __future__ import annotations

from apps.api.modules.finops.budget_planning.budget_alert import (
    acknowledge_alert,
    aggregate_budget_alerts,
    escalate_alert,
    trigger_over_budget_alert,
    validate_budget_alert,
)
from apps.api.modules.finops.budget_planning.budget_allocation import (
    BUDGET_ALLOCATION_AMOUNT_QUANTUM,
    aggregate_budget_allocations,
    allocate_budget,
    validate_budget_allocation,
)
from apps.api.modules.finops.budget_planning.budget_approval_workflow import (
    APPROVAL_CHAIN_MAX_STEPS,
    aggregate_approval_steps,
    record_approval_decision,
    reject_plan,
    submit_for_approval,
    validate_approval_chain,
)
from apps.api.modules.finops.budget_planning.budget_plan_engine import (
    BUDGET_PLAN_AMOUNT_QUANTUM,
    BUDGET_PLAN_DIMENSION_WEIGHT_SUM,
    aggregate_budget_plans,
    create_budget_plan,
    list_budget_plans,
    update_budget_plan,
    validate_budget_plan,
)
from apps.api.modules.finops.budget_planning.budget_planning_routes import (
    router as budget_planning_router,
)
from apps.api.modules.finops.budget_planning.budget_vs_actual import (
    BUDGET_VS_ACTUAL_AMOUNT_QUANTUM,
    BUDGET_VS_ACTUAL_PCT_QUANTUM,
    aggregate_budget_vs_actual,
    compute_budget_vs_actual,
    validate_budget_vs_actual,
)
from apps.api.modules.finops.budget_planning.scheduled_budget_planning_jobs import (
    LISTEN_NOTIFY_CHANNELS,
    compute_budget_planning_period,
    consume_notify,
    execute_lifecycle,
    schedule_cadence_lifecycle,
    validate_cadence,
)
from apps.api.modules.finops.budget_planning.serializers import (
    ALL_BUDGET_ALERT_SEVERITIES,
    ALL_BUDGET_ALERT_SEVERITY_VALUES,
    ALL_BUDGET_APPROVAL_STEP_STATUS_VALUES,
    ALL_BUDGET_APPROVAL_STEP_STATUSES,
    ALL_BUDGET_PLAN_DIMENSION_VALUES,
    ALL_BUDGET_PLAN_DIMENSIONS,
    ALL_BUDGET_PLAN_DRY_RUN_MODE_VALUES,
    ALL_BUDGET_PLAN_DRY_RUN_MODES,
    ALL_BUDGET_PLAN_LIFECYCLE_VALUES,
    ALL_BUDGET_PLAN_LIFECYCLES,
    ALL_BUDGET_PLAN_PERIOD_TYPE_VALUES,
    ALL_BUDGET_PLAN_PERIOD_TYPES,
    BUDGET_ALERT_RECIPIENT_TEMPLATES,
    BUDGET_CRITICAL_THRESHOLD_PCT,
    BUDGET_PLANNING_CADENCE_HOURS_KST,
    BUDGET_PLANNING_DEFAULTS,
    BUDGET_PLANNING_DIMENSION_WEIGHTS,
    BUDGET_PLANNING_ENGINE_MODEL_VERSION,
    BUDGET_PLANNING_RECIPIENT_TEMPLATES,
    BUDGET_WARNING_THRESHOLD_PCT,
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    MAX_ALLOCATIONS_PER_PLAN,
    MAX_BUDGET_OVERRIDE_KRW,
    MAX_BUDGET_PLANS_PER_TENANT,
    TOTAL_VERIFICATION_TOLERANCE_KRW,
    BudgetAlert,
    BudgetAlertSeverity,
    BudgetAllocationLine,
    BudgetApprovalStep,
    BudgetApprovalStepStatus,
    BudgetPlan,
    BudgetPlanDimension,
    BudgetPlanDryRunMode,
    BudgetPlanLifecycle,
    BudgetPlanPeriodType,
    BudgetVsActual,
)

# ── Module tag for ALLOWED_SERVICE_SUBMODULES sweep ────────────────────────
MODULE_TAG = "m24_finops_budget_planning"


__all__ = [
    # ── Module tag ─────────────────────────────────────────────────────────
    "MODULE_TAG",
    # ── Serializers: Constants ─────────────────────────────────────────────
    "BUDGET_PLANNING_ENGINE_MODEL_VERSION",
    "HIGH_VALUE_THRESHOLD_KRW_PER_YEAR",
    "BUDGET_PLANNING_DIMENSION_WEIGHTS",
    "BUDGET_WARNING_THRESHOLD_PCT",
    "BUDGET_CRITICAL_THRESHOLD_PCT",
    "MAX_BUDGET_PLANS_PER_TENANT",
    "MAX_ALLOCATIONS_PER_PLAN",
    "MAX_BUDGET_OVERRIDE_KRW",
    "TOTAL_VERIFICATION_TOLERANCE_KRW",
    "BUDGET_PLANNING_CADENCE_HOURS_KST",
    "BUDGET_PLANNING_RECIPIENT_TEMPLATES",
    "BUDGET_ALERT_RECIPIENT_TEMPLATES",
    "BUDGET_PLANNING_DEFAULTS",
    # ── Serializers: Enums ─────────────────────────────────────────────────
    "BudgetPlanPeriodType",
    "ALL_BUDGET_PLAN_PERIOD_TYPES",
    "ALL_BUDGET_PLAN_PERIOD_TYPE_VALUES",
    "BudgetPlanLifecycle",
    "ALL_BUDGET_PLAN_LIFECYCLES",
    "ALL_BUDGET_PLAN_LIFECYCLE_VALUES",
    "BudgetPlanDryRunMode",
    "ALL_BUDGET_PLAN_DRY_RUN_MODES",
    "ALL_BUDGET_PLAN_DRY_RUN_MODE_VALUES",
    "BudgetApprovalStepStatus",
    "ALL_BUDGET_APPROVAL_STEP_STATUSES",
    "ALL_BUDGET_APPROVAL_STEP_STATUS_VALUES",
    "BudgetAlertSeverity",
    "ALL_BUDGET_ALERT_SEVERITIES",
    "ALL_BUDGET_ALERT_SEVERITY_VALUES",
    "BudgetPlanDimension",
    "ALL_BUDGET_PLAN_DIMENSIONS",
    "ALL_BUDGET_PLAN_DIMENSION_VALUES",
    # ── Serializers: TypedDicts ────────────────────────────────────────────
    "BudgetPlan",
    "BudgetAllocationLine",
    "BudgetApprovalStep",
    "BudgetVsActual",
    "BudgetAlert",
    # ── budget_plan_engine ─────────────────────────────────────────────────
    "BUDGET_PLAN_AMOUNT_QUANTUM",
    "BUDGET_PLAN_DIMENSION_WEIGHT_SUM",
    "create_budget_plan",
    "list_budget_plans",
    "update_budget_plan",
    "validate_budget_plan",
    "aggregate_budget_plans",
    # ── budget_allocation ──────────────────────────────────────────────────
    "BUDGET_ALLOCATION_AMOUNT_QUANTUM",
    "allocate_budget",
    "validate_budget_allocation",
    "aggregate_budget_allocations",
    # ── budget_approval_workflow ───────────────────────────────────────────
    "APPROVAL_CHAIN_MAX_STEPS",
    "submit_for_approval",
    "record_approval_decision",
    "reject_plan",
    "validate_approval_chain",
    "aggregate_approval_steps",
    # ── budget_vs_actual ───────────────────────────────────────────────────
    "BUDGET_VS_ACTUAL_AMOUNT_QUANTUM",
    "BUDGET_VS_ACTUAL_PCT_QUANTUM",
    "compute_budget_vs_actual",
    "validate_budget_vs_actual",
    "aggregate_budget_vs_actual",
    # ── budget_alert ───────────────────────────────────────────────────────
    "trigger_over_budget_alert",
    "escalate_alert",
    "acknowledge_alert",
    "validate_budget_alert",
    "aggregate_budget_alerts",
    # ── scheduled_budget_planning_jobs ─────────────────────────────────────
    "LISTEN_NOTIFY_CHANNELS",
    "compute_budget_planning_period",
    "execute_lifecycle",
    "schedule_cadence_lifecycle",
    "validate_cadence",
    "consume_notify",
    # ── budget_planning_routes ─────────────────────────────────────────────
    "budget_planning_router",
]
