"""apps.api.modules.finops.budget_planning.serializers — Phase 24 Budget Planning serializers.

Phase 24 wire (cj-style 169번째) — FinOps Budget Planning pre-allocation
layer serializers (PRD §F40.1~§F40.8 verbatim + AD-52 (a)~(g) 7
sub-decisions + Phase 23 unit_economics + Phase 22 chargeback_settlement
pattern verbatim mirror).

Provides:
- Enums: BudgetPlanPeriodType (3: annual/quarterly/monthly) +
  BudgetPlanLifecycle (4: draft/pending_approval/approved/closed) +
  BudgetPlanDryRunMode (3: actual/preview/skip) +
  BudgetApprovalStepStatus (4: pending/approved/rejected/skipped) +
  BudgetAlertSeverity (3: warning/critical/escalated) +
  BudgetPlanDimension (5: cost_center/department/business_unit/tag/tenant).
- TypedDicts: BudgetPlan (14 fields) + BudgetAllocationLine (12 fields) +
  BudgetApprovalStep (10 fields) + BudgetVsActual (16 fields) +
  BudgetAlert (12 fields).
- Constants: BUDGET_PLANNING_ENGINE_MODEL_VERSION +
  BUDGET_PLANNING_DIMENSION_WEIGHTS (5-dim cross-join weights) +
  BUDGET_PLANNING_CADENCE_HOURS_KST (daily 04:00 KST) +
  BUDGET_PLANNING_RECIPIENT_TEMPLATES + BUDGET_PLANNING_DEFAULTS +
  BUDGET_ALERT_RECIPIENT_TEMPLATES + BUDGET_WARNING_THRESHOLD_PCT=10 +
  BUDGET_CRITICAL_THRESHOLD_PCT=25.

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — 8 NEW audit actions.
- CR 1-1 ContextVar — trace_id propagation.
- CR 1-1 RSC boundary — apps/web Next.js 15.x RSC.
- CR 5-1 banker's rounding — Decimal precision verbatim.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 16 NEW typed exceptions.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface parity.
- CR 12-5 D-GATE-01 — capability gate fail-closed.
- AD-14 stack pin — Recharts 2.12.7 + noto-sans-cjk-kr +
  apscheduler 3.10.4 + pytz 2024.1.
- AD-22 owner-only RBAC.
- AD-52 (a)~(g) 7 sub-decisions (Phase 24 wire).
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

import enum
from typing import TypedDict

# ── Module constants ──────────────────────────────────────────────────────
BUDGET_PLANNING_ENGINE_MODEL_VERSION = "1.0.0"

# High-value threshold for owner approval flow (PRD §F40.3 + AD-52 (g))
HIGH_VALUE_THRESHOLD_KRW_PER_YEAR = 10_000_000.0  # 10M KRW/year

# 5-dim cross-join weights for budget_plan engine (PRD §F40.1 + AD-52 (a)
# verbatim — derived from Phase 22 allocation_lines ledger data + Phase 23
# unit_economics_results ledger data)
BUDGET_PLANNING_DIMENSION_WEIGHTS: dict[str, float] = {
    "cost_center": 0.30,
    "department": 0.25,
    "business_unit": 0.20,
    "tag": 0.15,
    "tenant": 0.10,
}

# Variance / alert thresholds (PRD §F40.5 + AD-52 (d) verbatim)
BUDGET_WARNING_THRESHOLD_PCT = 10.0  # ≥10% over → warning
BUDGET_CRITICAL_THRESHOLD_PCT = 25.0  # ≥25% over → critical + escalation

# Cost guards (PRD §F40.2 verbatim)
MAX_BUDGET_PLANS_PER_TENANT = 1000
MAX_ALLOCATIONS_PER_PLAN = 100_000
MAX_BUDGET_OVERRIDE_KRW = 10_000_000.0  # override requires owner 2FA
TOTAL_VERIFICATION_TOLERANCE_KRW = 0.01  # ±0.01 KRW

# Cadence schedule KST pytz (PRD §F40.1 + AD-52 (c) verbatim)
BUDGET_PLANNING_CADENCE_HOURS_KST: dict[str, tuple[int, int]] = {
    "daily_lifecycle": (4, 0),  # 04:00 KST daily (lifecycle + auto-escalation)
    "weekly_variance": (4, 30),  # 04:30 KST weekly Monday
    "monthly_rollover": (5, 0),  # 05:00 KST monthly 1st-day (plan rollover)
    "quarterly_review": (5, 30),  # 05:30 KST quarterly 1st-day
}

# Recipient strategy templates (PRD §F40.5 verbatim, extended)
BUDGET_PLANNING_RECIPIENT_TEMPLATES: dict[str, dict[str, object]] = {
    "owner_only": {
        "slack_channels": ["#finops-budget-planning"],
        "email_recipients": ["tenant_owner"],
        "ms_teams_channels": [],
        "s3_archive_enabled": True,
    },
    "executive": {
        "slack_channels": ["#finops-budget-planning", "#finops-executive"],
        "email_recipients": ["tenant_owner", "tenant_admin"],
        "ms_teams_channels": ["FinOps Budget Planning"],
        "s3_archive_enabled": True,
    },
    "audit_only": {
        "slack_channels": [],
        "email_recipients": ["tenant_owner"],
        "ms_teams_channels": [],
        "s3_archive_enabled": True,
    },
}

BUDGET_ALERT_RECIPIENT_TEMPLATES: dict[str, dict[str, object]] = {
    "warning_slack_dm": {
        "slack_channels": ["#finops-budget-alerts"],
        "email_recipients": [],
        "ms_teams_channels": [],
        "s3_archive_enabled": False,
    },
    "critical_email_admin": {
        "slack_channels": ["#critical-alerts"],
        "email_recipients": ["tenant_admin", "tenant_owner"],
        "ms_teams_channels": ["FinOps Critical Alerts"],
        "s3_archive_enabled": True,
    },
    "escalation_oncall": {
        "slack_channels": ["#critical-alerts", "#oncall-rotation"],
        "email_recipients": ["tenant_owner", "oncall_rotation"],
        "ms_teams_channels": ["FinOps Critical Alerts", "OnCall"],
        "s3_archive_enabled": True,
    },
}

# Defaults dict (used by aggregators)
BUDGET_PLANNING_DEFAULTS: dict[str, object] = {
    "model_version": BUDGET_PLANNING_ENGINE_MODEL_VERSION,
    "high_value_threshold_krw_per_year": HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    "dimension_weights": BUDGET_PLANNING_DIMENSION_WEIGHTS,
    "warning_threshold_pct": BUDGET_WARNING_THRESHOLD_PCT,
    "critical_threshold_pct": BUDGET_CRITICAL_THRESHOLD_PCT,
    "max_budget_plans_per_tenant": MAX_BUDGET_PLANS_PER_TENANT,
    "max_allocations_per_plan": MAX_ALLOCATIONS_PER_PLAN,
    "max_budget_override_krw": MAX_BUDGET_OVERRIDE_KRW,
    "total_verification_tolerance_krw": TOTAL_VERIFICATION_TOLERANCE_KRW,
    "cadence_hours_kst": BUDGET_PLANNING_CADENCE_HOURS_KST,
    "recipient_templates": BUDGET_PLANNING_RECIPIENT_TEMPLATES,
    "alert_recipient_templates": BUDGET_ALERT_RECIPIENT_TEMPLATES,
    "dry_run_default": True,  # BudgetPlanOverviewCard 진입 시 default dry-run
}


# ── Enums ─────────────────────────────────────────────────────────────────
class BudgetPlanPeriodType(str, enum.Enum):
    """PRD §F40.1 + AD-52 (a) — 3 period types for budget plans."""

    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"


ALL_BUDGET_PLAN_PERIOD_TYPES = frozenset(item.value for item in BudgetPlanPeriodType)


class BudgetPlanLifecycle(str, enum.Enum):
    """PRD §F40.1 + AD-52 (c) — 4-state budget plan lifecycle."""

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    CLOSED = "closed"


ALL_BUDGET_PLAN_LIFECYCLES = frozenset(item.value for item in BudgetPlanLifecycle)


class BudgetPlanDryRunMode(str, enum.Enum):
    """PRD §F40.8 + AD-52 (a) — 3 dry-run modes."""

    ACTUAL = "actual"
    PREVIEW = "preview"
    SKIP = "skip"


ALL_BUDGET_PLAN_DRY_RUN_MODES = frozenset(item.value for item in BudgetPlanDryRunMode)


class BudgetApprovalStepStatus(str, enum.Enum):
    """PRD §F40.3 + AD-52 (c) — 4-state step status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"


ALL_BUDGET_APPROVAL_STEP_STATUSES = frozenset(
    item.value for item in BudgetApprovalStepStatus
)


class BudgetAlertSeverity(str, enum.Enum):
    """PRD §F40.5 + AD-52 (d) — 3-tier alert severity."""

    WARNING = "warning"
    CRITICAL = "critical"
    ESCALATED = "escalated"


ALL_BUDGET_ALERT_SEVERITIES = frozenset(item.value for item in BudgetAlertSeverity)


class BudgetPlanDimension(str, enum.Enum):
    """PRD §F40.1 + AD-52 (a) — 5-dim cross-join dimensions."""

    COST_CENTER = "cost_center"
    DEPARTMENT = "department"
    BUSINESS_UNIT = "business_unit"
    TAG = "tag"
    TENANT = "tenant"


ALL_BUDGET_PLAN_DIMENSIONS = frozenset(item.value for item in BudgetPlanDimension)


# ── TypedDicts ────────────────────────────────────────────────────────────
class BudgetPlan(TypedDict, total=False):
    """PRD §F40.1 + AD-52 (a) — Budget plan summary (14 fields).

    Fields:
    - plan_id (str): UUID v7 plan identifier
    - tenant_id (str): UUID tenant
    - period_key (str): "YYYY" / "YYYY-Qn" / "YYYY-MM"
    - period_type (str): BudgetPlanPeriodType
    - lifecycle (str): BudgetPlanLifecycle (default draft)
    - total_budget_amount (float): KRW total
    - scope_dimensions (list[str]): 5-dim scope
    - approval_chain (list[str]): approver actor_ids
    - high_value (bool): ≥10M KRW/year override
    - requires_2fa (bool): Epic 12 2FA 챌린지 mandatory
    - source_attribution (dict): 5-dim source attribution JSONB
    - created_at (str): ISO 8601
    - updated_at (str): ISO 8601
    - dry_run (bool): dry-run mode flag
    """

    plan_id: str
    tenant_id: str
    period_key: str
    period_type: str
    lifecycle: str
    total_budget_amount: float
    scope_dimensions: list[str]
    approval_chain: list[str]
    high_value: bool
    requires_2fa: bool
    source_attribution: dict[str, object]
    created_at: str
    updated_at: str
    dry_run: bool


class BudgetAllocationLine(TypedDict, total=False):
    """PRD §F40.2 + AD-52 (b) — Per-dim allocation line (12 fields).

    Fields:
    - allocation_id (str): UUID v7
    - plan_id (str): parent BudgetPlan plan_id
    - tenant_id (str): UUID tenant
    - dimension (str): BudgetPlanDimension
    - dimension_value (str): e.g. "cost-center-001"
    - weight (float): 5-dim weight
    - allocated_amount (float): KRW
    - per_tenant_override (bool): override flag
    - source_line_id (str): Phase 22 allocation_lines ledger reference
    - created_at (str): ISO 8601
    - verified (bool): total verification ±0.01 KRW pass
    - retry_count (int): auto-retry count (max 3)
    """

    allocation_id: str
    plan_id: str
    tenant_id: str
    dimension: str
    dimension_value: str
    weight: float
    allocated_amount: float
    per_tenant_override: bool
    source_line_id: str
    created_at: str
    verified: bool
    retry_count: int


class BudgetApprovalStep(TypedDict, total=False):
    """PRD §F40.3 + AD-52 (c) — Approval workflow step (10 fields).

    Fields:
    - step_id (str): UUID v7
    - plan_id (str): parent BudgetPlan
    - step_index (int): sequential ordering
    - approver_actor_id (str): tenant_owner approval chain
    - status (str): BudgetApprovalStepStatus
    - decided_at (str): ISO 8601 or null
    - requires_2fa (bool): Epic 12 2FA 챌린지
    - two_fa_verified (bool): 2FA verified
    - comment (str): approver comment
    - audit_log_id (str): audit log reference
    """

    step_id: str
    plan_id: str
    step_index: int
    approver_actor_id: str
    status: str
    decided_at: str  # or None
    requires_2fa: bool
    two_fa_verified: bool
    comment: str
    audit_log_id: str


class BudgetVsActual(TypedDict, total=False):
    """PRD §F40.4 + AD-52 (d) — Variance row (16 fields).

    Fields:
    - variance_id (str): UUID v7
    - plan_id (str): parent BudgetPlan
    - tenant_id (str): UUID tenant
    - period_key (str): "YYYY" / "YYYY-Qn" / "YYYY-MM"
    - dimension (str): BudgetPlanDimension
    - dimension_value (str): dimension value
    - budget_amount (float): KRW planned
    - actual_amount (float): KRW actual (Phase 22 settlement_results)
    - variance_amount (float): budget - actual
    - variance_pct (float): variance / budget
    - severity (str): BudgetAlertSeverity or "ok"
    - source_attribution (dict): 5-dim JSONB
    - computed_at (str): ISO 8601
    - over_budget (bool): any severity > warning
    - escalation_chain_id (str): escalation reference
    - audit_log_id (str): audit log reference
    """

    variance_id: str
    plan_id: str
    tenant_id: str
    period_key: str
    dimension: str
    dimension_value: str
    budget_amount: float
    actual_amount: float
    variance_amount: float
    variance_pct: float
    severity: str
    source_attribution: dict[str, object]
    computed_at: str
    over_budget: bool
    escalation_chain_id: str
    audit_log_id: str


class BudgetAlert(TypedDict, total=False):
    """PRD §F40.5 + AD-52 (d) — Over-budget alert (12 fields).

    Fields:
    - alert_id (str): UUID v7
    - plan_id (str): parent BudgetPlan
    - tenant_id (str): UUID tenant
    - severity (str): BudgetAlertSeverity
    - variance_pct (float): triggering variance
    - triggered_at (str): ISO 8601
    - channels_notified (list[str]): Slack DM / email / Teams
    - escalation_level (int): 0=warning, 1=critical, 2=oncall
    - high_value (bool): ≥10M KRW override
    - requires_2fa (bool): Epic 12 2FA 챌린지 mandatory
    - acknowledged_by (str): actor_id or null
    - audit_log_id (str): audit log reference
    """

    alert_id: str
    plan_id: str
    tenant_id: str
    severity: str
    variance_pct: float
    triggered_at: str
    channels_notified: list[str]
    escalation_level: int
    high_value: bool
    requires_2fa: bool
    acknowledged_by: str  # or None
    audit_log_id: str


# ── ALL_* constants derived from each enum ─────────────────────────────────
ALL_BUDGET_PLAN_PERIOD_TYPE_VALUES = ALL_BUDGET_PLAN_PERIOD_TYPES
ALL_BUDGET_PLAN_LIFECYCLE_VALUES = ALL_BUDGET_PLAN_LIFECYCLES
ALL_BUDGET_PLAN_DRY_RUN_MODE_VALUES = ALL_BUDGET_PLAN_DRY_RUN_MODES
ALL_BUDGET_APPROVAL_STEP_STATUS_VALUES = ALL_BUDGET_APPROVAL_STEP_STATUSES
ALL_BUDGET_ALERT_SEVERITY_VALUES = ALL_BUDGET_ALERT_SEVERITIES
ALL_BUDGET_PLAN_DIMENSION_VALUES = ALL_BUDGET_PLAN_DIMENSIONS
