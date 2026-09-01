"""apps.api.modules.finops.vendor_management.serializers — Phase 25 Vendor Management serializers.

Phase 25 wire (cj-style 173번째) — FinOps Vendor Management post-budget-allocation
layer serializers (PRD §F41.1~§F41.8 verbatim + AD-53 (a)~(g) 7
sub-decisions + Phase 14 + Phase 18 + Phase 19 + Phase 22 + Phase 23 + Phase 24
ledger data 활용 pattern verbatim mirror).

Provides:
- Enums: VendorStatus (4: active/inactive/under_review/blacklisted) +
  VendorCategory (6: cloud/saas/outsourcing/consulting/hardware/other) +
  VendorContractLifecycle (7: draft/pending_approval/approved/active/
  expiring_soon/renewed/expired/terminated) +
  VendorPerformanceSeverity (3: excellent/needs_improvement/critical) +
  VendorSelectionMode (3: actual/preview/skip).
- TypedDicts: Vendor (18 fields) + VendorSelectionScore (12 fields) +
  VendorContract (16 fields) + VendorPerformanceScorecard (14 fields) +
  VendorSpendAttribution (12 fields) + VendorBlacklistEntry (10 fields).
- Constants: VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION +
  VENDOR_SELECTION_DIMENSION_WEIGHTS (cost 0.30 + performance 0.25 +
  reliability 0.20 + compliance 0.15 + strategic_fit 0.10) +
  VENDOR_PERFORMANCE_DIMENSION_WEIGHTS (sla_compliance 0.30 +
  cost_efficiency 0.25 + support_quality 0.25 + innovation 0.20) +
  VENDOR_CADENCE_HOURS_KST (daily_lifecycle 04:00 + monthly_perf 03:00 +
  quarterly_review 03:30 + monthly_spend 03:15 KST) +
  VENDOR_RECIPIENT_TEMPLATES + VENDOR_DEFAULTS +
  VENDOR_BLACKLIST_GATE_FLAGS + SELECTION_THRESHOLD_DEFAULT=60.00 +
  SELECTION_CANDIDATE_LIMIT_DEFAULT=10.

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — 12 NEW audit actions via
  ActionClass.FINOPS_VENDOR_MANAGEMENT.
- CR 1-1 ContextVar — trace_id propagation.
- CR 1-1 RSC boundary — apps/web Next.js 15.x RSC.
- CR 5-1 banker's rounding — Decimal precision verbatim.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 16 NEW typed exceptions.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface parity.
- CR 12-5 D-GATE-01 — capability gate fail-closed.
- AD-14 stack pin — Recharts 2.12.7 + TanStack Table v8 +
  noto-sans-cjk-kr + apscheduler 3.10.4 + pytz 2024.1.
- AD-22 owner-only RBAC.
- AD-53 (a)~(g) 7 sub-decisions (Phase 25 wire).
- Epic 12 2FA 챌린지 mandatory high-value (≥10M KRW/year contract).
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT (finops_vendor_management.* namespace EXTENSION).
- D-FINOPS-14 honestly DEFER (vendor marketplace + auto-procurement +
  vendor consolidation + vendor ESG + AI-driven RFP + SLA auto-inforcement +
  multi-currency FX + invoice OCR + KYC + risk scoring ML — all honestly
  DEFER to future Phase 25.x).
- CR 11-3 ALLOWED_SERVICE_SUBMODULES 즉시 sweep EXTENSION
  m25_finops_vendor_management (Phase 25 64th honest-DEFER cycle).
"""

from __future__ import annotations

import enum
from typing import TypedDict

# ── Module constants ──────────────────────────────────────────────────────
VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION = "1.0.0"

# High-value threshold for owner approval flow (PRD §F41.3 + AD-53 (g))
HIGH_VALUE_THRESHOLD_KRW_PER_YEAR = 10_000_000.0  # 10M KRW/year

# 5-dim weighted scoring for vendor_selection (PRD §F41.2 + AD-53 (b)
# verbatim — derived from Phase 14 + Phase 18 + Phase 19 ledger data)
VENDOR_SELECTION_DIMENSION_WEIGHTS: dict[str, float] = {
    "cost": 0.30,
    "performance": 0.25,
    "reliability": 0.20,
    "compliance": 0.15,
    "strategic_fit": 0.10,
}

# 4-dim scoring for vendor_performance_evaluation (PRD §F41.4 + AD-53 (d)
# verbatim — derived from Phase 11 chargeback + Phase 18 commitment +
# Phase 22 settlement_results + Phase 24 budget_vs_actual ledger data)
VENDOR_PERFORMANCE_DIMENSION_WEIGHTS: dict[str, float] = {
    "sla_compliance": 0.30,
    "cost_efficiency": 0.25,
    "support_quality": 0.25,
    "innovation": 0.20,
}

# Selection threshold defaults (PRD §F41.2 + AD-53 (b) verbatim)
SELECTION_THRESHOLD_DEFAULT: float = 60.00  # Below threshold 자동 excluded
SELECTION_CANDIDATE_LIMIT_DEFAULT: int = 10  # top-N candidates
SELECTION_SCORE_VERSION_MAX: float = 100.00  # strict range 0.00~100.00

# Vendor risk score thresholds (PRD §F41.4 + AD-53 (d) verbatim)
VENDOR_RISK_LOW_THRESHOLD = 30.0
VENDOR_RISK_MEDIUM_THRESHOLD = 60.0
VENDOR_RISK_HIGH_THRESHOLD = 80.0

# Cost guards (PRD §F41.1 verbatim)
MAX_VENDORS_PER_TENANT = 5000
MAX_CONTRACTS_PER_VENDOR = 100
MAX_CONTRACT_OVERRIDE_KRW = 10_000_000.0  # override requires owner 2FA
TOTAL_VERIFICATION_TOLERANCE_KRW = 0.01  # ±0.01 KRW
AUTO_RENEWAL_WINDOW_DAYS = 90  # PRD §F41.3 auto-renewal window

# Cadence schedule KST pytz (PRD §F41.1 + AD-53 (c) verbatim)
VENDOR_CADENCE_HOURS_KST: dict[str, tuple[int, int]] = {
    "daily_lifecycle": (4, 0),  # 04:00 KST daily (vendor lifecycle)
    "monthly_performance_evaluation": (3, 0),  # 03:00 KST 1st-of-month
    "monthly_spend_attribution": (3, 15),  # 03:15 KST 1st-of-month
    "quarterly_review": (3, 30),  # 03:30 KST 1st-of-quarter
}

# Recipient strategy templates (PRD §F41.4 verbatim, extended)
VENDOR_RECIPIENT_TEMPLATES: dict[str, dict[str, object]] = {
    "owner_only": {
        "slack_channels": ["#finops-vendor-management"],
        "email_recipients": ["tenant_owner"],
        "ms_teams_channels": [],
        "s3_archive_enabled": True,
    },
    "executive": {
        "slack_channels": ["#finops-vendor-management", "#finops-executive"],
        "email_recipients": ["tenant_owner", "tenant_admin"],
        "ms_teams_channels": ["FinOps Vendor Management"],
        "s3_archive_enabled": True,
    },
    "audit_only": {
        "slack_channels": [],
        "email_recipients": ["tenant_owner"],
        "ms_teams_channels": [],
        "s3_archive_enabled": True,
    },
}

# Blacklist compliance gate flags (PRD §F41.3 + AD-53 (g))
VENDOR_BLACKLIST_GATE_FLAGS: dict[str, bool] = {
    "block_contract_approval": True,  # blacklisted vendor cannot get contracts
    "block_selection": True,  # blacklisted vendor excluded from selection
    "block_spend_attribution": False,  # historical spend attribution still allowed
    "block_performance_evaluation": True,  # blacklisted vendor skipped from perf eval
    "require_owner_override": True,  # override requires owner-only RBAC + 2FA
}

# LISTEN/NOTIFY channels (PRD §F41.1 verbatim)
LISTEN_NOTIFY_CHANNELS: tuple[str, ...] = (
    "phase_25_vendor_created",
    "phase_25_vendor_updated",
    "phase_25_vendor_status_changed",
    "phase_25_vendor_blacklisted",
    "phase_25_vendor_selection_executed",
    "phase_25_vendor_contract_approved",
    "phase_25_vendor_contract_renewed",
    "phase_25_vendor_contract_terminated",
    "phase_25_vendor_performance_evaluated",
    "phase_25_vendor_spend_attributed",
    "phase_25_vendor_risk_flagged",
    "phase_25_vendor_dry_run_executed",
)

# Defaults dict (used by aggregators)
VENDOR_DEFAULTS: dict[str, object] = {
    "model_version": VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
    "high_value_threshold_krw_per_year": HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    "selection_dimension_weights": VENDOR_SELECTION_DIMENSION_WEIGHTS,
    "performance_dimension_weights": VENDOR_PERFORMANCE_DIMENSION_WEIGHTS,
    "selection_threshold_default": SELECTION_THRESHOLD_DEFAULT,
    "selection_candidate_limit_default": SELECTION_CANDIDATE_LIMIT_DEFAULT,
    "selection_score_version_max": SELECTION_SCORE_VERSION_MAX,
    "vendor_risk_low_threshold": VENDOR_RISK_LOW_THRESHOLD,
    "vendor_risk_medium_threshold": VENDOR_RISK_MEDIUM_THRESHOLD,
    "vendor_risk_high_threshold": VENDOR_RISK_HIGH_THRESHOLD,
    "max_vendors_per_tenant": MAX_VENDORS_PER_TENANT,
    "max_contracts_per_vendor": MAX_CONTRACTS_PER_VENDOR,
    "max_contract_override_krw": MAX_CONTRACT_OVERRIDE_KRW,
    "total_verification_tolerance_krw": TOTAL_VERIFICATION_TOLERANCE_KRW,
    "auto_renewal_window_days": AUTO_RENEWAL_WINDOW_DAYS,
    "cadence_hours_kst": VENDOR_CADENCE_HOURS_KST,
    "recipient_templates": VENDOR_RECIPIENT_TEMPLATES,
    "blacklist_gate_flags": VENDOR_BLACKLIST_GATE_FLAGS,
    "listen_notify_channels": LISTEN_NOTIFY_CHANNELS,
    "dry_run_default": True,  # VendorCatalogOverviewCard 진입 시 default dry-run
}


# ── Enums ─────────────────────────────────────────────────────────────────
class VendorStatus(enum.StrEnum):
    """PRD §F41.1 + AD-53 (a) — 4-state vendor lifecycle."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    UNDER_REVIEW = "under_review"
    BLACKLISTED = "blacklisted"


ALL_VENDOR_STATUSES = frozenset(item.value for item in VendorStatus)


class VendorCategory(enum.StrEnum):
    """PRD §F41.1 + AD-53 (a) — 6 vendor_category taxonomy."""

    CLOUD = "cloud"
    SAAS = "saas"
    OUTSOURCING = "outsourcing"
    CONSULTING = "consulting"
    HARDWARE = "hardware"
    OTHER = "other"


ALL_VENDOR_CATEGORIES = frozenset(item.value for item in VendorCategory)


class VendorContractLifecycle(enum.StrEnum):
    """PRD §F41.3 + AD-53 (c) — 7-state vendor contract lifecycle."""

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ACTIVE = "active"
    EXPIRING_SOON = "expiring_soon"
    RENEWED = "renewed"
    EXPIRED = "expired"
    TERMINATED = "terminated"


ALL_VENDOR_CONTRACT_LIFECYCLES = frozenset(item.value for item in VendorContractLifecycle)


class VendorPerformanceSeverity(enum.StrEnum):
    """PRD §F41.4 + AD-53 (d) — 3-tier vendor performance severity."""

    EXCELLENT = "excellent"
    NEEDS_IMPROVEMENT = "needs_improvement"
    CRITICAL = "critical"


ALL_VENDOR_PERFORMANCE_SEVERITIES = frozenset(item.value for item in VendorPerformanceSeverity)


class VendorSelectionMode(enum.StrEnum):
    """PRD §F41.8 + AD-53 (a) — 3 dry-run modes for vendor selection."""

    ACTUAL = "actual"
    PREVIEW = "preview"
    SKIP = "skip"


ALL_VENDOR_SELECTION_MODES = frozenset(item.value for item in VendorSelectionMode)


class VendorApprovalStepStatus(enum.StrEnum):
    """PRD §F41.3 + AD-53 (c) — 4-state approval step status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"


ALL_VENDOR_APPROVAL_STEP_STATUSES = frozenset(item.value for item in VendorApprovalStepStatus)


# ── TypedDicts ────────────────────────────────────────────────────────────
class Vendor(TypedDict, total=False):
    """PRD §F41.1 + AD-53 (a) — Vendor record (18 fields).

    Fields:
    - vendor_id (str): UUID v7 vendor identifier
    - tenant_id (str): UUID tenant
    - vendor_name (str): vendor display name
    - vendor_category (str): VendorCategory (cloud/saas/outsourcing/consulting/hardware/other)
    - status (str): VendorStatus (active/inactive/under_review/blacklisted)
    - cost_score (float): 0.00~100.00
    - performance_score (float): 0.00~100.00
    - reliability_score (float): 0.00~100.00
    - compliance_score (float): 0.00~100.00
    - strategic_fit_score (float): 0.00~100.00
    - risk_score (float): 0.00~100.00 (composite)
    - contract_count (int): active contracts
    - blacklist_reason (str): reason if blacklisted
    - high_value (bool): ≥10M KRW/year contract
    - requires_2fa (bool): Epic 12 2FA 챌린지 mandatory
    - source_attribution (dict): Phase 14/18/19 ledger JSONB
    - created_at (str): ISO 8601
    - updated_at (str): ISO 8601
    """

    vendor_id: str
    tenant_id: str
    vendor_name: str
    vendor_category: str
    status: str
    cost_score: float
    performance_score: float
    reliability_score: float
    compliance_score: float
    strategic_fit_score: float
    risk_score: float
    contract_count: int
    blacklist_reason: str
    high_value: bool
    requires_2fa: bool
    source_attribution: dict[str, object]
    created_at: str
    updated_at: str


class VendorSelectionScore(TypedDict, total=False):
    """PRD §F41.2 + AD-53 (b) — Vendor selection score (12 fields).

    Fields:
    - selection_id (str): UUID v7
    - vendor_id (str): parent Vendor vendor_id
    - tenant_id (str): UUID tenant
    - cost_score (float): 0.00~100.00
    - performance_score (float): 0.00~100.00
    - reliability_score (float): 0.00~100.00
    - compliance_score (float): 0.00~100.00
    - strategic_fit_score (float): 0.00~100.00
    - weighted_total_score (float): 0.00~100.00
    - per_tenant_override (bool): override flag
    - score_version (float): 0.00~100.00
    - excluded_by_threshold (bool): below threshold 자동 excluded
    - created_at (str): ISO 8601
    """

    selection_id: str
    vendor_id: str
    tenant_id: str
    cost_score: float
    performance_score: float
    reliability_score: float
    compliance_score: float
    strategic_fit_score: float
    weighted_total_score: float
    per_tenant_override: bool
    score_version: float
    excluded_by_threshold: bool
    created_at: str


class VendorContract(TypedDict, total=False):
    """PRD §F41.3 + AD-53 (c) — Vendor contract (16 fields).

    Fields:
    - contract_id (str): UUID v7
    - vendor_id (str): parent Vendor
    - tenant_id (str): UUID tenant
    - contract_name (str): display name
    - contract_value_krw (float): KRW total
    - lifecycle (str): VendorContractLifecycle (7 states)
    - step_index (int): sequential approval chain ordering
    - approval_chain (list[str]): approver actor_ids
    - auto_renewal_enabled (bool): 90-day window flag
    - high_value (bool): ≥10M KRW/year
    - requires_2fa (bool): Epic 12 2FA 챌린지 mandatory
    - computed_total_contract_value (float): within budget ceiling auto-approved
    - budget_ceiling_krw (float): budget ceiling
    - over_budget (bool): over budget ceiling flag
    - blacklist_gate_passed (bool): vendor_blacklist compliance gate
    - audit_log_id (str): audit log reference
    - created_at (str): ISO 8601
    - updated_at (str): ISO 8601
    """

    contract_id: str
    vendor_id: str
    tenant_id: str
    contract_name: str
    contract_value_krw: float
    lifecycle: str
    step_index: int
    approval_chain: list[str]
    auto_renewal_enabled: bool
    high_value: bool
    requires_2fa: bool
    computed_total_contract_value: float
    budget_ceiling_krw: float
    over_budget: bool
    blacklist_gate_passed: bool
    audit_log_id: str
    created_at: str
    updated_at: str


class VendorPerformanceScorecard(TypedDict, total=False):
    """PRD §F41.4 + AD-53 (d) — Vendor performance scorecard (14 fields).

    Fields:
    - scorecard_id (str): UUID v7
    - vendor_id (str): parent Vendor
    - tenant_id (str): UUID tenant
    - period_key (str): "YYYY" / "YYYY-Qn" / "YYYY-MM"
    - sla_compliance_score (float): 0.00~100.00
    - cost_efficiency_score (float): 0.00~100.00
    - support_quality_score (float): 0.00~100.00
    - innovation_score (float): 0.00~100.00
    - weighted_total_score (float): 0.00~100.00
    - severity (str): VendorPerformanceSeverity
    - monthly_score (float): monthly cadence
    - quarterly_score (float): quarterly cadence
    - source_attribution (dict): Phase 11/18/22/24 ledger JSONB
    - audit_log_id (str): audit log reference
    - computed_at (str): ISO 8601
    """

    scorecard_id: str
    vendor_id: str
    tenant_id: str
    period_key: str
    sla_compliance_score: float
    cost_efficiency_score: float
    support_quality_score: float
    innovation_score: float
    weighted_total_score: float
    severity: str
    monthly_score: float
    quarterly_score: float
    source_attribution: dict[str, object]
    audit_log_id: str
    computed_at: str


class VendorSpendAttribution(TypedDict, total=False):
    """PRD §F41.7 + AD-53 (d) — Vendor spend attribution (12 fields).

    Fields:
    - attribution_id (str): UUID v7
    - vendor_id (str): parent Vendor
    - tenant_id (str): UUID tenant
    - period_key (str): "YYYY" / "YYYY-Qn" / "YYYY-MM"
    - actual_amount (float): KRW actual (Phase 22 settlement_results)
    - budget_amount (float): KRW budget (Phase 24 budget_plan)
    - variance_amount (float): budget - actual
    - variance_pct (float): variance / budget
    - over_budget (bool): over budget flag
    - cross_budget_reconciled (bool): Phase 24 reconciliation flag
    - audit_log_id (str): audit log reference
    - computed_at (str): ISO 8601
    """

    attribution_id: str
    vendor_id: str
    tenant_id: str
    period_key: str
    actual_amount: float
    budget_amount: float
    variance_amount: float
    variance_pct: float
    over_budget: bool
    cross_budget_reconciled: bool
    audit_log_id: str
    computed_at: str


class VendorBlacklistEntry(TypedDict, total=False):
    """PRD §F41.1 + AD-53 (g) — Vendor blacklist entry (10 fields).

    Fields:
    - blacklist_id (str): UUID v7
    - vendor_id (str): blacklisted vendor
    - tenant_id (str): UUID tenant
    - reason (str): blacklist reason (compliance violation / SLA breach / data breach / etc.)
    - severity (str): blacklist severity
    - block_contract_approval (bool): vendor_blacklist compliance gate
    - block_selection (bool): exclude from vendor_selection
    - block_performance_evaluation (bool): skip from perf eval
    - requires_owner_override (bool): owner-only RBAC + 2FA 챌린지
    - created_at (str): ISO 8601
    """

    blacklist_id: str
    vendor_id: str
    tenant_id: str
    reason: str
    severity: str
    block_contract_approval: bool
    block_selection: bool
    block_performance_evaluation: bool
    requires_owner_override: bool
    created_at: str


# ── ALL_* constants derived from each enum ─────────────────────────────────
ALL_VENDOR_STATUS_VALUES = ALL_VENDOR_STATUSES
ALL_VENDOR_CATEGORY_VALUES = ALL_VENDOR_CATEGORIES
ALL_VENDOR_CONTRACT_LIFECYCLE_VALUES = ALL_VENDOR_CONTRACT_LIFECYCLES
ALL_VENDOR_PERFORMANCE_SEVERITY_VALUES = ALL_VENDOR_PERFORMANCE_SEVERITIES
ALL_VENDOR_SELECTION_MODE_VALUES = ALL_VENDOR_SELECTION_MODES
ALL_VENDOR_APPROVAL_STEP_STATUS_VALUES = ALL_VENDOR_APPROVAL_STEP_STATUSES
