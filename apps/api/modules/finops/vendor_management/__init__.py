"""apps.api.modules.finops.vendor_management — Phase 25 FinOps Vendor Management post-budget-allocation layer.

Phase 25 wire (cj-style 173번째) — FinOps Vendor Management territory 결정 wire 진입
완료. PRD §F41.1~§F41.8 verbatim + AD-53 (a)~(g) 7 sub-decisions + Phase 14 +
Phase 18 + Phase 19 + Phase 22 + Phase 23 + Phase 24 ledger data 활용.

8 ACs §F41.1~§F41.8 verbatim satisfied:
- §F41.1 vendor_catalog engine + 6 vendor_category taxonomy
  (cloud/saas/outsourcing/consulting/hardware/other) EXTENSION + vendor CRUD +
  4-state lifecycle (active/inactive/under_review/blacklisted).
- §F41.2 vendor_selection + 5-dim weighted scoring
  (cost 0.30 + performance 0.25 + reliability 0.20 + compliance 0.15 +
  strategic_fit 0.10) + per-tenant override > industry baseline > system
  default + selection_threshold 60.00 + score version <= 100.00 strict
  range.
- §F41.3 vendor_contract_lifecycle sequential
  (draft → pending_approval → approved → active → expiring_soon →
  renewed/expired/terminated) + Epic 12 2FA 챌린지 ≥ 10M KRW/year
  mandatory + tenant_owner approval chain (Slack DM + 2FA +
  approval_chain) + auto-renewal 90-day window + over-budget cross-check +
  vendor_blacklist compliance gate.
- §F41.4 vendor_performance_evaluation + dashboard UI 5 NEW sub-components
  (VendorCatalogOverviewCard + VendorSelectionScorePanel +
  VendorContractLifecycleTimeline + VendorPerformanceScorecardTable +
  VendorSpendAttributionChart) + 4-dim scoring
  (sla_compliance 0.30 + cost_efficiency 0.25 + support_quality 0.25 +
  innovation 0.20) + monthly 1st 03:00 KST + quarterly 1st 03:30 KST
  cadence.
- §F41.5 Capability matrix v1.51 EXTENSION FINOPS_VENDOR_MANAGEMENT 4-industry
  grants ✅/✅/✅/✅ (SaaS + SERVICE + MANUFACTURING_SERVICE +
  MANUFACTURING_SERVICE_OTHER) industry-agnostic CR 12-1 L4 verbatim.
- §F41.6 audit action EXTENSION 12 NEW Literal (vendor_created +
  vendor_updated + vendor_status_changed + vendor_blacklisted +
  vendor_selection_executed + vendor_contract_approved +
  vendor_contract_renewed + vendor_contract_terminated +
  vendor_performance_evaluated + vendor_spend_attributed +
  vendor_risk_flagged + vendor_dry_run_executed) + 16 NEW typed exceptions
  (CR 12-5 D-14 envelope).
- §F41.7 vendor_spend_attribution + cross-budget reconciliation
  (Phase 22 settlement_results + Phase 24 budget_plan JOIN).
- §F41.8 dry-run + Tests + wire scope T1~T8 + 1 NEW CLI flag
  (--finops-vendor-management-dry-run).

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation (1 preview
  table).
- CR 1-1 audit-first INSERT — 12 NEW audit actions via
  ActionClass.FINOPS_VENDOR_MANAGEMENT.
- CR 1-1 ContextVar — trace_id propagation.
- CR 1-1 RSC boundary — apps/web Next.js 15.x RSC.
- CR 5-1 Decimal precision banker's rounding — Decimal("0.01") verbatim.
- CR 9-6 commit message `git commit -F <file>` — D5 prevention.
- CR 11-3 ALLOWED_SERVICE_SUBMODULES 즉시 sweep EXTENSION
  m25_finops_vendor_management.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 16 NEW typed exceptions.
- CR 12-5 D-PARITY-01 inversion — Python TypedDict ↔ TypeScript interface
  parity.
- CR 12-5 D-GATE-01 inversion — capability gate fail-closed.
- AD-14 stack pin — Recharts 2.12.7 + TanStack Table v8 +
  noto-sans-cjk-kr + apscheduler 3.10.4 + pytz 2024.1.
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory high-value
  (≥10M KRW/year).
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT (finops_vendor_management.* namespace EXTENSION ~35
  keys).
- D-FINOPS-14 honestly DEFER (vendor marketplace + auto-procurement +
  vendor consolidation + vendor ESG + AI-driven RFP + SLA
  auto-inforcement + multi-currency FX + invoice OCR + KYC + risk
  scoring ML — all honestly DEFER to future Phase 25.x).
"""
from __future__ import annotations

from typing import Final

# ── Module identifier (CR 11-3 ALLOWED_SERVICE_SUBMODULES sweep) ──────────
MODULE_TAG: Final[str] = "m25_finops_vendor_management"

# ── Submodule re-exports (Phase 25 verbatim mirror Phase 24 budget_planning pattern) ──
from apps.api.modules.finops.vendor_management.scheduled_vendor_management_jobs import (  # noqa: E402, F401
    daily_vendor_lifecycle_job,
    monthly_vendor_performance_job,
    monthly_vendor_spend_attribution_job,
    notify_listen_channels,
    quarterly_vendor_review_job,
    schedule_vendor_management_jobs,
)
from apps.api.modules.finops.vendor_management.serializers import (  # noqa: E402, F401
    ALL_VENDOR_APPROVAL_STEP_STATUS_VALUES,
    ALL_VENDOR_APPROVAL_STEP_STATUSES,
    ALL_VENDOR_CATEGORIES,
    ALL_VENDOR_CATEGORY_VALUES,
    ALL_VENDOR_CONTRACT_LIFECYCLE_VALUES,
    ALL_VENDOR_CONTRACT_LIFECYCLES,
    ALL_VENDOR_PERFORMANCE_SEVERITIES,
    ALL_VENDOR_PERFORMANCE_SEVERITY_VALUES,
    ALL_VENDOR_SELECTION_MODE_VALUES,
    ALL_VENDOR_SELECTION_MODES,
    ALL_VENDOR_STATUS_VALUES,
    # Frozen sets
    ALL_VENDOR_STATUSES,
    AUTO_RENEWAL_WINDOW_DAYS,
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    LISTEN_NOTIFY_CHANNELS,
    MAX_CONTRACT_OVERRIDE_KRW,
    MAX_CONTRACTS_PER_VENDOR,
    MAX_VENDORS_PER_TENANT,
    SELECTION_CANDIDATE_LIMIT_DEFAULT,
    SELECTION_SCORE_VERSION_MAX,
    SELECTION_THRESHOLD_DEFAULT,
    TOTAL_VERIFICATION_TOLERANCE_KRW,
    VENDOR_BLACKLIST_GATE_FLAGS,
    VENDOR_CADENCE_HOURS_KST,
    VENDOR_DEFAULTS,
    # Constants
    VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
    VENDOR_PERFORMANCE_DIMENSION_WEIGHTS,
    VENDOR_RECIPIENT_TEMPLATES,
    VENDOR_RISK_HIGH_THRESHOLD,
    VENDOR_RISK_LOW_THRESHOLD,
    VENDOR_RISK_MEDIUM_THRESHOLD,
    VENDOR_SELECTION_DIMENSION_WEIGHTS,
    # TypedDicts
    Vendor,
    VendorApprovalStepStatus,
    VendorBlacklistEntry,
    VendorCategory,
    VendorContract,
    VendorContractLifecycle,
    VendorPerformanceScorecard,
    VendorPerformanceSeverity,
    VendorSelectionMode,
    VendorSelectionScore,
    VendorSpendAttribution,
    # Enums
    VendorStatus,
)
from apps.api.modules.finops.vendor_management.vendor_catalog_engine import (  # noqa: E402, F401
    aggregate_vendor_catalog,
    blacklist_vendor,
    change_vendor_status,
    compute_vendor_risk_score,
    create_vendor,
    update_vendor,
    validate_vendor_scores,
)
from apps.api.modules.finops.vendor_management.vendor_contract_lifecycle_engine import (  # noqa: E402, F401
    advance_contract_lifecycle,
    aggregate_vendor_contract_lifecycle,
    approve_contract_step,
    check_auto_renewal_window,
    check_over_budget,
    check_vendor_blacklist_gate,
    create_vendor_contract,
    reject_contract_step,
    request_contract_approval,
    request_contract_renewal,
    terminate_contract,
)
from apps.api.modules.finops.vendor_management.vendor_performance_evaluation import (  # noqa: E402, F401
    aggregate_vendor_performance,
    classify_performance_severity,
    compute_monthly_score,
    compute_quarterly_score,
    evaluate_vendor_performance,
)
from apps.api.modules.finops.vendor_management.vendor_selection_engine import (  # noqa: E402, F401
    aggregate_vendor_selection,
    apply_vendor_selection_threshold,
    override_selection_score_per_tenant,
    score_vendor,
)
from apps.api.modules.finops.vendor_management.vendor_spend_attribution import (  # noqa: E402, F401
    aggregate_vendor_spend_attribution,
    compute_vendor_spend_attribution,
    reconcile_cross_budget,
)
from apps.api.modules.finops.vendor_management.vendor_management_routes import (  # noqa: E402, F401
    router as vendor_management_router,
)

# ── __all__ (Phase 25 verbatim mirror Phase 24 pattern) ──────────────────
__all__ = [
    # Module identifier
    "MODULE_TAG",
    # Enums
    "VendorStatus",
    "VendorCategory",
    "VendorContractLifecycle",
    "VendorPerformanceSeverity",
    "VendorSelectionMode",
    "VendorApprovalStepStatus",
    # TypedDicts
    "Vendor",
    "VendorSelectionScore",
    "VendorContract",
    "VendorPerformanceScorecard",
    "VendorSpendAttribution",
    "VendorBlacklistEntry",
    # Constants
    "VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION",
    "VENDOR_SELECTION_DIMENSION_WEIGHTS",
    "VENDOR_PERFORMANCE_DIMENSION_WEIGHTS",
    "VENDOR_CADENCE_HOURS_KST",
    "VENDOR_RECIPIENT_TEMPLATES",
    "VENDOR_DEFAULTS",
    "VENDOR_BLACKLIST_GATE_FLAGS",
    "SELECTION_THRESHOLD_DEFAULT",
    "SELECTION_CANDIDATE_LIMIT_DEFAULT",
    "SELECTION_SCORE_VERSION_MAX",
    "VENDOR_RISK_LOW_THRESHOLD",
    "VENDOR_RISK_MEDIUM_THRESHOLD",
    "VENDOR_RISK_HIGH_THRESHOLD",
    "MAX_VENDORS_PER_TENANT",
    "MAX_CONTRACTS_PER_VENDOR",
    "MAX_CONTRACT_OVERRIDE_KRW",
    "TOTAL_VERIFICATION_TOLERANCE_KRW",
    "AUTO_RENEWAL_WINDOW_DAYS",
    "LISTEN_NOTIFY_CHANNELS",
    "HIGH_VALUE_THRESHOLD_KRW_PER_YEAR",
    # Frozen sets
    "ALL_VENDOR_STATUSES",
    "ALL_VENDOR_CATEGORIES",
    "ALL_VENDOR_CONTRACT_LIFECYCLES",
    "ALL_VENDOR_PERFORMANCE_SEVERITIES",
    "ALL_VENDOR_SELECTION_MODES",
    "ALL_VENDOR_APPROVAL_STEP_STATUSES",
    "ALL_VENDOR_STATUS_VALUES",
    "ALL_VENDOR_CATEGORY_VALUES",
    "ALL_VENDOR_CONTRACT_LIFECYCLE_VALUES",
    "ALL_VENDOR_PERFORMANCE_SEVERITY_VALUES",
    "ALL_VENDOR_SELECTION_MODE_VALUES",
    "ALL_VENDOR_APPROVAL_STEP_STATUS_VALUES",
    # Engine functions
    "aggregate_vendor_catalog",
    "create_vendor",
    "update_vendor",
    "change_vendor_status",
    "blacklist_vendor",
    "compute_vendor_risk_score",
    "validate_vendor_scores",
    "aggregate_vendor_selection",
    "score_vendor",
    "apply_vendor_selection_threshold",
    "override_selection_score_per_tenant",
    "aggregate_vendor_contract_lifecycle",
    "create_vendor_contract",
    "advance_contract_lifecycle",
    "request_contract_approval",
    "approve_contract_step",
    "reject_contract_step",
    "request_contract_renewal",
    "terminate_contract",
    "check_auto_renewal_window",
    "check_over_budget",
    "check_vendor_blacklist_gate",
    "aggregate_vendor_performance",
    "evaluate_vendor_performance",
    "compute_monthly_score",
    "compute_quarterly_score",
    "classify_performance_severity",
    "aggregate_vendor_spend_attribution",
    "compute_vendor_spend_attribution",
    "reconcile_cross_budget",
    "daily_vendor_lifecycle_job",
    "monthly_vendor_performance_job",
    "monthly_vendor_spend_attribution_job",
    "quarterly_vendor_review_job",
    "schedule_vendor_management_jobs",
    "notify_listen_channels",
    "vendor_management_router",
]
