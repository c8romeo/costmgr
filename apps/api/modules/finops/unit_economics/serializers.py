"""apps.api.modules.finops.unit_economics.serializers — Phase 23 Unit Economics serializers.

Phase 23 wire (cj-style 164번째) — FinOps Unit Economics derived metric
layer serializers (PRD §F39.1~§F39.8 verbatim + AD-51 (a)~(g) 7
sub-decisions + Phase 22 chargeback_settlement pattern verbatim mirror).

Provides:
- Enums: UnitEconomicsCalculationStatus (5) +
  UnitEconomicsDimension (5) + CostPerXMetric (4) +
  MarginAnalysisStatus (4) + UnitEconomicsAlertSeverity (3).
- TypedDicts: UnitEconomicsResult (16) +
  CostPerBusinessUnitBreakdown (12) + CostPerTransactionBreakdown
  (10) + MarginAnalysisResult (14) + UnitEconomicsAlert (8).
- Constants: UNIT_ECONOMICS_ENGINE_MODEL_VERSION + DEFAULTS.
- DERIVATION_DIMENSION_WEIGHTS for 5-dim cross-join (cost_center +
  department + business_unit + tag + tenant — derived from Phase 22
  allocation_lines ledger data).
- COST_PER_X_METRIC_WEIGHTS for 4 cost_per_X dimensions (business_unit
  + transaction + department + cost_center).
- MARGIN_ANALYSIS_REVENUE_SOURCES for OPTIONAL revenue attribution
  (Phase 23 derives margin only when revenue is registered in tenant
  revenue table — D-FINOPS-12 honestly DEFER for cost_per_customer).
- UNIT_ECONOMICS_CADENCE_HOURS_KST (4 cadence daily + weekly + monthly
  + quarterly KST pytz).
- RECIPIENT_TEMPLATES.
- DEFAULTS dict aggregator functions consume.
- ALL_* constants derived from each enum.

CR lessons applied:
- CR 11-4 P-015 — pure validator pattern (validate_*).
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface parity.
- CR 12-5 D-GATE-01 — capability gate per-tenant on/off.
- AD-14 stack pin — Recharts 2.12.7 + noto-sans-cjk-kr +
  apscheduler 3.10.4 + pytz 2024.1.
- AD-51 (a)~(g) 7 sub-decisions.
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT (finops_unit_economics.* namespace EXTENSION).
- D-FINOPS-12 honestly DEFER (cost_per_customer CRM + multi-currency
  FX + real-time stream + tenant revenue auto-import — all honestly
  DEFER to future Phase 23.x sprint).
"""
from __future__ import annotations

import enum
from typing import TypedDict

# ── Module constants ──────────────────────────────────────────────────────
UNIT_ECONOMICS_ENGINE_MODEL_VERSION = "1.0.0"

# High-value threshold for owner approval flow (PRD §F39.5 + AD-51 (g))
HIGH_VALUE_THRESHOLD_KRW_PER_YEAR = 10_000_000.0  # 10M KRW/year

# 5-dim cross-join weights for unit_economics engine derivation
# (PRD §F39.1 + AD-51 (a) verbatim — derived from Phase 22
# allocation_lines ledger data)
DERIVATION_DIMENSION_WEIGHTS: dict[str, float] = {
    "cost_center": 0.30,
    "department": 0.25,
    "business_unit": 0.20,
    "tag": 0.15,
    "tenant": 0.10,
}

# 4 cost_per_X dimension weights (PRD §F39.2 + AD-51 (b) verbatim)
COST_PER_X_METRIC_WEIGHTS: dict[str, float] = {
    "cost_per_business_unit": 0.40,
    "cost_per_transaction": 0.30,
    "cost_per_department": 0.20,
    "cost_per_cost_center": 0.10,
}

# Margin analysis 3-tier thresholds (PRD §F39.4 + AD-51 (d))
MARGIN_HEALTHY_THRESHOLD_PCT = 30.0  # ≥30% = healthy
MARGIN_WARNING_THRESHOLD_PCT = 15.0  # 15~30% = warning
MARGIN_CRITICAL_THRESHOLD_PCT = 15.0  # <15% = critical
MARGIN_NEGATIVE_PCT = 0.0  # <0% = negative (alert + Epic 12 2FA)

# Cost-per-X guards (PRD §F39.2 + AD-51 (b) verbatim)
MAX_BUSINESS_UNITS_PER_TENANT = 1000
MAX_TRANSACTIONS_PER_PERIOD = 100_000
MAX_COST_PER_X_OVERRIDE_KRW = 10_000_000.0  # override requires owner 2FA

# 4 cadence schedule KST pytz (PRD §F39.1 + AD-51 (e))
UNIT_ECONOMICS_CADENCE_HOURS_KST: dict[str, tuple[int, int]] = {
    "daily": (3, 30),      # 03:30 KST daily (lightweight rollup)
    "weekly": (4, 0),      # 04:00 KST weekly Monday
    "monthly": (4, 30),    # 04:30 KST monthly 1st-day
    "quarterly": (5, 0),   # 05:00 KST quarterly 1st-day
}

# Recipient strategy templates (PRD §F39.5 verbatim, extended)
UNIT_ECONOMICS_RECIPIENT_TEMPLATES: dict[str, dict[str, object]] = {
    "owner_only": {
        "slack_channels": ["#finops-unit-economics"],
        "email_recipients": ["tenant_owner"],
        "ms_teams_channels": [],
        "s3_archive_enabled": True,
    },
    "executive": {
        "slack_channels": ["#finops-unit-economics", "#finops-executive"],
        "email_recipients": ["tenant_owner", "tenant_admin"],
        "ms_teams_channels": ["FinOps Unit Economics"],
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
UNIT_ECONOMICS_DEFAULTS: dict[str, object] = {
    "model_version": UNIT_ECONOMICS_ENGINE_MODEL_VERSION,
    "high_value_threshold_krw_per_year": HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    "derivation_dimension_weights": DERIVATION_DIMENSION_WEIGHTS,
    "cost_per_x_metric_weights": COST_PER_X_METRIC_WEIGHTS,
    "margin_healthy_threshold_pct": MARGIN_HEALTHY_THRESHOLD_PCT,
    "margin_warning_threshold_pct": MARGIN_WARNING_THRESHOLD_PCT,
    "margin_critical_threshold_pct": MARGIN_CRITICAL_THRESHOLD_PCT,
    "margin_negative_pct": MARGIN_NEGATIVE_PCT,
    "max_business_units_per_tenant": MAX_BUSINESS_UNITS_PER_TENANT,
    "max_transactions_per_period": MAX_TRANSACTIONS_PER_PERIOD,
    "max_cost_per_x_override_krw": MAX_COST_PER_X_OVERRIDE_KRW,
    "unit_economics_cadence_hours_kst": UNIT_ECONOMICS_CADENCE_HOURS_KST,
    "unit_economics_recipient_templates": UNIT_ECONOMICS_RECIPIENT_TEMPLATES,
    "audit_first_insert": True,
    "dry_run_supported": True,
    "2fa_challenge_supported": True,
}


# ── Enums ─────────────────────────────────────────────────────────────────
class UnitEconomicsCalculationStatus(str, enum.Enum):
    """5 calculation status (PRD §F39.1 + AD-51 (a) verbatim)."""

    PENDING = "pending"
    COMPUTING = "computing"
    COMPLETED = "completed"
    FAILED = "failed"
    DRY_RUN_COMPLETED = "dry_run_completed"


ALL_UNIT_ECONOMICS_CALCULATION_STATUSES: list[str] = [
    s.value for s in UnitEconomicsCalculationStatus
]


class UnitEconomicsDimension(str, enum.Enum):
    """5 derivation dimension (PRD §F39.1 + AD-51 (a) verbatim).

    Note: identical to Phase 22 AllocationDimension — derived from
    Phase 22 allocation_lines ledger data via 5-dim cross-join.
    """

    COST_CENTER = "cost_center"
    DEPARTMENT = "department"
    BUSINESS_UNIT = "business_unit"
    TAG = "tag"
    TENANT = "tenant"


ALL_UNIT_ECONOMICS_DIMENSIONS: list[str] = [d.value for d in UnitEconomicsDimension]


class CostPerXMetric(str, enum.Enum):
    """4 cost_per_X metric (PRD §F39.2 + AD-51 (b) verbatim)."""

    COST_PER_BUSINESS_UNIT = "cost_per_business_unit"
    COST_PER_TRANSACTION = "cost_per_transaction"
    COST_PER_DEPARTMENT = "cost_per_department"
    COST_PER_COST_CENTER = "cost_per_cost_center"


ALL_COST_PER_X_METRICS: list[str] = [m.value for m in CostPerXMetric]


class MarginAnalysisStatus(str, enum.Enum):
    """4 margin analysis status (PRD §F39.4 + AD-51 (d) verbatim)."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    NEGATIVE = "negative"


ALL_MARGIN_ANALYSIS_STATUSES: list[str] = [s.value for s in MarginAnalysisStatus]


class UnitEconomicsAlertSeverity(str, enum.Enum):
    """3 alert severity (PRD §F39.4 + AD-51 (d) verbatim)."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


ALL_UNIT_ECONOMICS_ALERT_SEVERITIES: list[str] = [
    s.value for s in UnitEconomicsAlertSeverity
]


# ── TypedDicts (PRD §F39.1~§F39.4 verbatim) ────────────────────────────────
class UnitEconomicsResult(TypedDict, total=False):
    """16 fields (PRD §F39.1 verbatim).

    Derived from Phase 22 settlement_id → allocation_lines ledger via
    5-dim cross-join + ledger-key dedup.
    """

    unit_economics_id: str
    tenant_id: str
    period_key: str
    source_settlement_id: str  # FK to Phase 22 SettlementResult
    total_cost_krw: float
    total_revenue_krw: float  # OPTIONAL — D-FINOPS-12 if no revenue registered
    total_units: int  # count_distinct(business_unit) for cost_per_business_unit
    total_transactions: int
    cost_per_business_unit_krw: float
    cost_per_transaction_krw: float
    margin_pct: float  # signed (revenue - cost) / revenue × 100
    margin_status: str  # MarginAnalysisStatus value
    confidence_pct: float  # 0~100 (derived from allocation_count + revenue_completeness)
    dry_run: bool
    computed_at: str  # ISO timestamp
    last_updated_at: str
    model_version: str
    trace_id: str


class CostPerBusinessUnitBreakdown(TypedDict, total=False):
    """12 fields (PRD §F39.2 verbatim)."""

    breakdown_id: str
    unit_economics_id: str  # FK to UnitEconomicsResult
    tenant_id: str
    period_key: str
    business_unit: str  # dimension_value
    cost_center: str
    department: str
    tag_key: str  # OPTIONAL tag filter
    allocated_cost_krw: float
    transaction_count: int
    cost_per_unit_krw: float
    confidence_pct: float
    requires_2fa_challenge: bool
    model_version: str
    computed_at: str
    trace_id: str


class CostPerTransactionBreakdown(TypedDict, total=False):
    """10 fields (PRD §F39.3 verbatim).

    Note: tag propagation — when Phase 22 settlement has tags, those tags
    are propagated into the transaction-level breakdown for filtering.
    """

    transaction_id: str
    unit_economics_id: str  # FK to UnitEconomicsResult
    tenant_id: str
    period_key: str
    business_unit: str
    cost_center: str
    allocated_cost_krw: float
    tag_propagation_json: dict  # tag → value pairs from Phase 22 settlement
    requires_2fa_challenge: bool
    model_version: str
    computed_at: str
    trace_id: str


class MarginAnalysisResult(TypedDict, total=False):
    """14 fields (PRD §F39.4 verbatim).

    OPTIONAL margin analysis — only computed when revenue is registered
    in tenant_revenue table. D-FINOPS-12 honestly DEFER if revenue not
    available (margin_pct = 0.0 + status = "warning" + audit action).
    """

    margin_id: str
    unit_economics_id: str  # FK to UnitEconomicsResult
    tenant_id: str
    period_key: str
    business_unit: str
    total_cost_krw: float
    total_revenue_krw: float
    margin_amount_krw: float  # revenue - cost
    margin_pct: float  # signed
    margin_status: str  # MarginAnalysisStatus value
    revenue_sources: list  # list of registered revenue source IDs
    revenue_completeness_pct: float  # 0~100 (impacts confidence)
    requires_2fa_challenge: bool  # high-value (margin positive ≥ 10M KRW/year)
    model_version: str
    computed_at: str
    trace_id: str


class UnitEconomicsAlert(TypedDict, total=False):
    """8 fields (PRD §F39.4 verbatim — margin critical/negative alerts)."""

    alert_id: str
    tenant_id: str
    period_key: str
    margin_id: str  # FK to MarginAnalysisResult (if margin-related)
    severity: str  # UnitEconomicsAlertSeverity value
    alert_type: str  # margin_negative / margin_critical / margin_warning /
    # cost_per_x_override / cost_per_business_unit_anomaly
    alert_message: str
    requires_2fa_challenge: bool
    model_version: str
    triggered_at: str
    trace_id: str


__all__ = [
    "UNIT_ECONOMICS_ENGINE_MODEL_VERSION",
    "HIGH_VALUE_THRESHOLD_KRW_PER_YEAR",
    "DERIVATION_DIMENSION_WEIGHTS",
    "COST_PER_X_METRIC_WEIGHTS",
    "MARGIN_HEALTHY_THRESHOLD_PCT",
    "MARGIN_WARNING_THRESHOLD_PCT",
    "MARGIN_CRITICAL_THRESHOLD_PCT",
    "MARGIN_NEGATIVE_PCT",
    "MAX_BUSINESS_UNITS_PER_TENANT",
    "MAX_TRANSACTIONS_PER_PERIOD",
    "MAX_COST_PER_X_OVERRIDE_KRW",
    "UNIT_ECONOMICS_CADENCE_HOURS_KST",
    "UNIT_ECONOMICS_RECIPIENT_TEMPLATES",
    "UNIT_ECONOMICS_DEFAULTS",
    "UnitEconomicsCalculationStatus",
    "ALL_UNIT_ECONOMICS_CALCULATION_STATUSES",
    "UnitEconomicsDimension",
    "ALL_UNIT_ECONOMICS_DIMENSIONS",
    "CostPerXMetric",
    "ALL_COST_PER_X_METRICS",
    "MarginAnalysisStatus",
    "ALL_MARGIN_ANALYSIS_STATUSES",
    "UnitEconomicsAlertSeverity",
    "ALL_UNIT_ECONOMICS_ALERT_SEVERITIES",
    "UnitEconomicsResult",
    "CostPerBusinessUnitBreakdown",
    "CostPerTransactionBreakdown",
    "MarginAnalysisResult",
    "UnitEconomicsAlert",
]
