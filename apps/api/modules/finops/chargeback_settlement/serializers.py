"""apps.api.modules.finops.chargeback_settlement.serializers — Phase 22 Chargeback Settlement serializers.

Phase 22 wire (cj-style 160번째) — FinOps Chargeback Settlement
serializers (PRD §F38.1~§F38.8 verbatim + AD-50 (a)~(g) 7 sub-decisions).

Provides:
- Enums: SettlementRuleType (4) + SettlementStatus (5) + AllocationDimension
  (5) + InvoiceFormat (3).
- TypedDicts: SettlementRule (12) + SettlementResult (16) + AllocationLine
  (10) + ReconciliationResult (12).
- Constants: CHARGEBACK_SETTLEMENT_ENGINE_MODEL_VERSION + DEFAULTS.
- FIVE_MODULE_WEIGHTS for settlement layer cross-join (Phase 11 chargeback
  + Phase 18 commitment + Phase 19 pricing + Phase 20 multi_cloud +
  Phase 21 reserved_capacity weighted average → single settlement_id).
- ALLOCATION_DIMENSION_WEIGHTS for 5-dim allocation (cost_center +
  department + business_unit + tag + tenant).
- SETTLEMENT_CADENCE_HOURS_KST (4 cadence).
- RECIPIENT_TEMPLATES.
- DEFAULTS dict aggregator functions consume.
- ALL_* constants derived from each enum.

CR lessons applied:
- CR 11-4 P-015 — pure validator pattern (validate_*).
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface parity.
- CR 12-5 D-GATE-01 — capability gate per-tenant on/off.
- AD-14 stack pin — reportlab 4.0.7 + xlsxwriter 3.1.9 + noto-sans-cjk-kr.
- AD-50 (a)~(g) 7 sub-decisions.
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT.
"""
from __future__ import annotations

import enum
from typing import TypedDict

# ── Module constants ──────────────────────────────────────────────────────
CHARGEBACK_SETTLEMENT_ENGINE_MODEL_VERSION = "1.0.0"

# High-value threshold for owner approval flow (PRD §F38.4 + AD-50 (g))
HIGH_VALUE_THRESHOLD_KRW_PER_YEAR = 10_000_000.0  # 10M KRW/year

# 5-module cross-join weights for settlement layer (PRD §F38.1 + AD-50 (a))
FIVE_MODULE_WEIGHTS: dict[str, float] = {
    "phase_11_chargeback": 0.30,
    "phase_18_commitment": 0.20,
    "phase_19_pricing": 0.20,
    "phase_20_multi_cloud": 0.15,
    "phase_21_reserved_capacity": 0.15,
}

# 5-dim allocation weights (PRD §F38.2 + AD-50 (b))
ALLOCATION_DIMENSION_WEIGHTS: dict[str, float] = {
    "cost_center": 0.30,
    "department": 0.25,
    "business_unit": 0.20,
    "tag": 0.15,
    "tenant": 0.10,
}

# Reconciliation 3-way match (PRD §F38.4 + AD-50 (d))
RECONCILIATION_TOLERANCE_PCT = 1.0  # 1.0% variance tolerance
RECONCILIATION_MAX_RETRIES = 3
RECONCILIATION_AMOUNT_TOLERANCE_KRW = 0.01  # banker's rounding round-off

# Invoice generation guards (PRD §F38.3 + AD-50 (c) + AD-14 stack pin)
MAX_INVOICE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_ALLOCATION_LINES = 10_000

# 4 cadence schedule KST pytz (PRD §F38.4 + AD-50 (e))
SETTLEMENT_CADENCE_HOURS_KST: dict[str, tuple[int, int]] = {
    "monthly": (4, 0),      # 1st-day 04:00 KST monthly
    "quarterly": (5, 0),    # 1st-day 05:00 KST quarterly
    "semi_annual": (6, 0),  # 1st-day 06:00 KST semi_annual
    "annual": (7, 0),       # 1st-day 07:00 KST annual
}

# Recipient strategy templates (PRD §F38.4 verbatim, extended)
SETTLEMENT_RECIPIENT_TEMPLATES: dict[str, dict[str, object]] = {
    "owner_only": {
        "slack_channels": ["#finops-chargeback-settlement"],
        "email_recipients": ["tenant_owner"],
        "ms_teams_channels": [],
        "s3_archive_enabled": True,
    },
    "executive": {
        "slack_channels": ["#finops-chargeback-executive"],
        "email_recipients": ["tenant_owner", "tenant_admin"],
        "ms_teams_channels": ["FinOps Chargeback Settlement"],
        "s3_archive_enabled": True,
    },
    "audit_only": {
        "slack_channels": [],
        "email_recipients": ["tenant_owner"],
        "ms_teams_channels": [],
        "s3_archive_enabled": True,
    },
}

# Defaults dict (used by aggregators)
CHARGEBACK_SETTLEMENT_DEFAULTS: dict[str, object] = {
    "model_version": CHARGEBACK_SETTLEMENT_ENGINE_MODEL_VERSION,
    "high_value_threshold_krw_per_year": HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    "five_module_weights": FIVE_MODULE_WEIGHTS,
    "allocation_dimension_weights": ALLOCATION_DIMENSION_WEIGHTS,
    "reconciliation_tolerance_pct": RECONCILIATION_TOLERANCE_PCT,
    "reconciliation_max_retries": RECONCILIATION_MAX_RETRIES,
    "reconciliation_amount_tolerance_krw": RECONCILIATION_AMOUNT_TOLERANCE_KRW,
    "max_invoice_bytes": MAX_INVOICE_BYTES,
    "max_allocation_lines": MAX_ALLOCATION_LINES,
    "settlement_cadence_hours_kst": SETTLEMENT_CADENCE_HOURS_KST,
    "settlement_recipient_templates": SETTLEMENT_RECIPIENT_TEMPLATES,
    "audit_first_insert": True,
    "dry_run_supported": True,
    "2fa_challenge_supported": True,
}


# ── Enums ─────────────────────────────────────────────────────────────────
class SettlementRuleType(str, enum.Enum):
    """4 settlement rule type (PRD §F38.1 + AD-50 (a) verbatim)."""

    FLAT_FEE = "flat_fee"
    PROPORTIONAL_ALLOCATION = "proportional_allocation"
    METERED_VOLUME = "metered_volume"
    TAG_WEIGHTED = "tag_weighted"


ALL_SETTLEMENT_RULE_TYPES: list[str] = [t.value for t in SettlementRuleType]


class SettlementStatus(str, enum.Enum):
    """5 settlement status (PRD §F38.1 + AD-50 (a) verbatim)."""

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    INVOICED = "invoiced"
    RECONCILED = "reconciled"


ALL_SETTLEMENT_STATUSES: list[str] = [s.value for s in SettlementStatus]


class AllocationDimension(str, enum.Enum):
    """5 allocation dimension (PRD §F38.2 + AD-50 (b) verbatim)."""

    COST_CENTER = "cost_center"
    DEPARTMENT = "department"
    BUSINESS_UNIT = "business_unit"
    TAG = "tag"
    TENANT = "tenant"


ALL_ALLOCATION_DIMENSIONS: list[str] = [d.value for d in AllocationDimension]


class InvoiceFormat(str, enum.Enum):
    """3 invoice format (PRD §F38.3 + AD-50 (c) verbatim + AD-14 stack pin)."""

    PDF = "pdf"
    XLSX = "xlsx"
    CSV = "csv"


ALL_INVOICE_FORMATS: list[str] = [f.value for f in InvoiceFormat]


# ── TypedDicts (PRD §F38.1~§F38.4 verbatim) ───────────────────────────────
class SettlementRule(TypedDict, total=False):
    """12 fields (PRD §F38.1 verbatim)."""

    settlement_id: str
    tenant_id: str
    period_key: str
    rule_name: str
    rule_type: str  # SettlementRuleType value
    target_amount_krw: float
    target_dimensions: list  # list of AllocationDimension
    scope_chain: dict  # 5-module cross-join attribution
    settlement_status: str  # SettlementStatus value
    requires_2fa_challenge: bool  # high_value_flag AND owner_approval_required
    model_version: str
    trace_id: str


class SettlementResult(TypedDict, total=False):
    """16 fields (PRD §F38.1+§F38.2 verbatim)."""

    result_id: str
    settlement_id: str  # FK to SettlementRule
    tenant_id: str
    period_key: str
    total_amount_krw: float
    five_module_attribution: dict  # 5 module weighted breakdown
    allocation_breakdown: dict  # 5-dim weighted allocation
    allocation_lines: list  # individual AllocationLine records
    allocation_count: int
    confidence_pct: float  # 0~100
    tolerance_band_krw: float  # 1.0% tolerance pre-allocated
    settlement_status: str
    dry_run: bool
    computed_at: str  # ISO timestamp
    last_updated_at: str
    model_version: str
    trace_id: str


class AllocationLine(TypedDict, total=False):
    """10 fields (PRD §F38.2 verbatim)."""

    allocation_id: str
    result_id: str  # FK to SettlementResult
    tenant_id: str
    period_key: str
    dimension: str  # AllocationDimension value
    dimension_value: str
    weight: float  # 0~1 (per ALLOCATION_DIMENSION_WEIGHTS)
    allocated_amount_krw: float
    audit_first_insert: bool
    computed_at: str  # ISO timestamp
    trace_id: str


class ReconciliationResult(TypedDict, total=False):
    """12 fields (PRD §F38.4 verbatim)."""

    reconciliation_id: str
    result_id: str  # FK to SettlementResult
    tenant_id: str
    period_key: str
    allocation_amount_krw: float
    invoice_amount_krw: float
    ledger_amount_krw: float
    variance_pct: float  # signed variance vs allocation_amount
    variance_krw: float
    reconciliation_status: str  # matched/variance_detected/retry_exhausted/needs_approval
    retry_attempts: int  # 0~3
    requires_2fa_challenge: bool
    model_version: str
    computed_at: str  # ISO timestamp
    trace_id: str


__all__ = [
    "CHARGEBACK_SETTLEMENT_ENGINE_MODEL_VERSION",
    "HIGH_VALUE_THRESHOLD_KRW_PER_YEAR",
    "FIVE_MODULE_WEIGHTS",
    "ALLOCATION_DIMENSION_WEIGHTS",
    "RECONCILIATION_TOLERANCE_PCT",
    "RECONCILIATION_MAX_RETRIES",
    "RECONCILIATION_AMOUNT_TOLERANCE_KRW",
    "MAX_INVOICE_BYTES",
    "MAX_ALLOCATION_LINES",
    "SETTLEMENT_CADENCE_HOURS_KST",
    "SETTLEMENT_RECIPIENT_TEMPLATES",
    "CHARGEBACK_SETTLEMENT_DEFAULTS",
    "SettlementRuleType",
    "ALL_SETTLEMENT_RULE_TYPES",
    "SettlementStatus",
    "ALL_SETTLEMENT_STATUSES",
    "AllocationDimension",
    "ALL_ALLOCATION_DIMENSIONS",
    "InvoiceFormat",
    "ALL_INVOICE_FORMATS",
    "SettlementRule",
    "SettlementResult",
    "AllocationLine",
    "ReconciliationResult",
]
