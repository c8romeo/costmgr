"""apps.api.modules.finops.reserved_capacity.serializers — Phase 21 Reserved Capacity serializers.

Phase 21 wire (cj-style 151번째) — FinOps Reserved Capacity Planning
serializers (PRD §F37.1~§F37.8 verbatim + AD-49 (a)~(g) 7 sub-decisions).

Provides:
- Enums: ReservedCapacityTier (6) + ExecutionStrategy (4) +
  ReservedCapacityCadence (4) + OrchestrationScope (4).
- TypedDicts: ReservedCapacityDemandForecast (16) + ReservedCapacityPlan (18)
  + CommitmentRecommendation (17) + ReservedCapacityOrchestration (19).
- Constants: RESERVED_CAPACITY_ENGINE_MODEL_VERSION + RESERVED_CAPACITY_DEFAULTS.
- ALL_* constants derived from each enum (Phase 20 ALL_NEGOTIATION_COMMITMENT_TERMS
  honest deviation lesson: ensure ALL_* list exists for every enum).

CR lessons applied:
- CR 11-4 P-015 — pure validator pattern (validate_*).
- CR 12-1 L4 industry-agnostic — 4-industry growth_baseline_pct.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface parity.
- AD-49 (a)~(g) 7 sub-decisions.
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT.
"""

from __future__ import annotations

import enum
from typing import TypedDict

# ── Module constants ──────────────────────────────────────────────────────
RESERVED_CAPACITY_ENGINE_MODEL_VERSION = "1.0.0"

# Minimum savings thresholds (PRD §F37.2 verbatim)
MINIMUM_SAVINGS_PCT = 5.0
MINIMUM_SAVINGS_KRW = 1_000_000.0  # 1M KRW
MINIMUM_BREAK_EVEN_UTILIZATION_PCT = 70.0
CAPACITY_HEADROOM_MIN_PCT = 10.0
CAPACITY_HEADROOM_MAX_PCT = 20.0

# High-value threshold for owner approval flow (PRD §F37.3 + AD-49 (g))
HIGH_VALUE_THRESHOLD_KRW_PER_YEAR = 10_000_000.0  # 10M KRW/year savings

# Industry growth baselines per year (PRD §F37.1 verbatim 4 industries)
INDUSTRY_GROWTH_BASELINE_PCT: dict[str, float] = {
    "manufacturing": 8.0,
    "service": 12.0,
    "manufacturing_service": 10.0,
    "manufacturing_service_other": 15.0,
}

# Module weights for 5-module cross-join (PRD §F37.1 verbatim)
FIVE_MODULE_WEIGHTS: dict[str, float] = {
    "phase_13_forecast": 0.25,
    "phase_14_optimization": 0.20,
    "phase_18_commitment": 0.20,
    "phase_19_pricing": 0.15,
    "phase_20_multi_cloud": 0.20,
}

# Confidence score weights (PRD §F37.3 verbatim)
CONFIDENCE_SCORE_WEIGHTS: dict[str, float] = {
    "utilization_stability": 0.4,
    "historical_accuracy": 0.3,
    "demand_forecast_confidence_pct": 0.3,
}

# Risk score weights (PRD §F37.3 verbatim)
RISK_SCORE_WEIGHTS: dict[str, float] = {
    "savings_pct": 0.4,
    "commitment_term": 0.3,
    "commitment_flexibility": 0.3,
}

# 4 cadence schedule KST pytz (PRD §F37.4 + AD-49 (e) verbatim)
RESERVED_CAPACITY_CADENCE_HOURS_KST: dict[str, tuple[int, int]] = {
    "daily": (2, 0),  # 02:00 KST daily
    "weekly": (3, 0),  # 03:00 KST Monday
    "monthly": (4, 0),  # 04:00 KST 1st day of month
    "quarterly": (5, 0),  # 05:00 KST 1st day of quarter
}

# Recipient strategy templates (PRD §F37.4 verbatim)
RESERVED_CAPACITY_RECIPIENT_TEMPLATES: dict[str, dict[str, object]] = {
    "owner_only": {
        "slack_channels": ["#finops-reserved-capacity"],
        "email_recipients": ["tenant_owner"],
        "ms_teams_channels": [],
        "s3_archive_enabled": True,
    },
    "executive": {
        "slack_channels": ["#finops-executive"],
        "email_recipients": ["tenant_owner", "tenant_admin"],
        "ms_teams_channels": ["FinOps Reserved Capacity"],
        "s3_archive_enabled": True,
    },
}

# Defaults dict (used by aggregators)
RESERVED_CAPACITY_DEFAULTS: dict[str, object] = {
    "model_version": RESERVED_CAPACITY_ENGINE_MODEL_VERSION,
    "minimum_savings_pct": MINIMUM_SAVINGS_PCT,
    "minimum_savings_krw": MINIMUM_SAVINGS_KRW,
    "minimum_break_even_utilization_pct": MINIMUM_BREAK_EVEN_UTILIZATION_PCT,
    "capacity_headroom_min_pct": CAPACITY_HEADROOM_MIN_PCT,
    "capacity_headroom_max_pct": CAPACITY_HEADROOM_MAX_PCT,
    "high_value_threshold_krw_per_year": HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    "industry_growth_baseline_pct": INDUSTRY_GROWTH_BASELINE_PCT,
    "five_module_weights": FIVE_MODULE_WEIGHTS,
    "confidence_score_weights": CONFIDENCE_SCORE_WEIGHTS,
    "risk_score_weights": RISK_SCORE_WEIGHTS,
    "reserved_capacity_cadence_hours_kst": RESERVED_CAPACITY_CADENCE_HOURS_KST,
    "reserved_capacity_recipient_templates": RESERVED_CAPACITY_RECIPIENT_TEMPLATES,
    "audit_first_insert": True,
    "dry_run_supported": True,
}


# ── Enums ─────────────────────────────────────────────────────────────────
class ReservedCapacityTier(str, enum.Enum):
    """6 reserved capacity tier (PRD §F37.2 + AD-49 (b) verbatim).

    6 tiers = (1-year vs 3-year) × (no upfront vs partial upfront vs all upfront).
    """

    ONE_YEAR_NO_UPFRONT = "1y_no_upfront"
    ONE_YEAR_PARTIAL_UPFRONT = "1y_partial_upfront"
    ONE_YEAR_ALL_UPFRONT = "1y_all_upfront"
    THREE_YEAR_NO_UPFRONT = "3y_no_upfront"
    THREE_YEAR_PARTIAL_UPFRONT = "3y_partial_upfront"
    THREE_YEAR_ALL_UPFRONT = "3y_all_upfront"


ALL_RESERVED_CAPACITY_TIERS: list[str] = [tier.value for tier in ReservedCapacityTier]


class ExecutionStrategy(str, enum.Enum):
    """4 execution strategy (PRD §F37.3 + AD-49 (c) verbatim)."""

    AUTO_EXECUTE_READY = "auto_execute_ready"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    OWNER_APPROVAL_REQUIRED = "owner_approval_required"
    LOW_CONFIDENCE = "low_confidence"


ALL_EXECUTION_STRATEGIES: list[str] = [s.value for s in ExecutionStrategy]


class ReservedCapacityCadence(str, enum.Enum):
    """4 cadence schedule (PRD §F37.4 + AD-49 (e) verbatim KST pytz)."""

    DAILY = "daily"  # 02:00 KST
    WEEKLY = "weekly"  # Mon 03:00 KST
    MONTHLY = "monthly"  # 1st-day 04:00 KST
    QUARTERLY = "quarterly"  # 1st-day 05:00 KST


ALL_RESERVED_CAPACITY_CADENCES: list[str] = [c.value for c in ReservedCapacityCadence]


class OrchestrationScope(str, enum.Enum):
    """4 orchestration scope (4 industries verbatim)."""

    MANUFACTURING = "manufacturing"
    SERVICE = "service"
    MANUFACTURING_SERVICE = "manufacturing_service"
    MANUFACTURING_SERVICE_OTHER = "manufacturing_service_other"


ALL_ORCHESTRATION_SCOPES: list[str] = [s.value for s in OrchestrationScope]


# ── TypedDicts (PRD §F37.1~§F37.4 verbatim) ───────────────────────────────
class ReservedCapacityDemandForecast(TypedDict, total=False):
    """16 fields (PRD §F37.1 verbatim)."""

    demand_forecast_id: str
    tenant_id: str
    period_key: str
    industry: str  # OrchestrationScope value
    scope_chain: dict  # 5-module cross-rollup
    forecasted_demand_krw: float
    confidence_interval_low_krw: float
    confidence_interval_high_krw: float
    seasonal_factor: float
    growth_rate_pct: float
    five_module_attribution: dict  # phase_13 + phase_14 + phase_18 + phase_19 + phase_20 weights
    confidence_pct: float  # 0~100
    model_version: str
    computed_at: str  # ISO timestamp
    last_updated_at: str
    trace_id: str


class ReservedCapacityPlan(TypedDict, total=False):
    """18 fields (PRD §F37.2 verbatim)."""

    capacity_plan_id: str
    tenant_id: str
    period_key: str
    demand_forecast_id: str  # FK to ReservedCapacityDemandForecast
    industry: str
    recommended_tier: str  # ReservedCapacityTier value
    break_even_utilization_pct: float  # >= 70.0
    capacity_headroom_pct: float  # 10~20
    target_reserved_capacity_units: int
    estimated_savings_krw: float
    estimated_savings_pct: float  # >= MINIMUM_SAVINGS_PCT=5.0
    minimum_savings_krw_threshold: float  # MINIMUM_SAVINGS_KRW=1M
    commitment_term_months: int  # 12 or 36
    upfront_payment_option: str  # no/partial/all
    capacity_plan_status: str  # proposed/approved/executed/rejected
    model_version: str
    computed_at: str
    trace_id: str


class CommitmentRecommendation(TypedDict, total=False):
    """17 fields (PRD §F37.3 verbatim)."""

    commitment_recommendation_id: str
    tenant_id: str
    capacity_plan_id: str  # FK to ReservedCapacityPlan
    period_key: str
    industry: str
    recommended_tier: str  # ReservedCapacityTier value
    confidence_score: float  # 0~100
    risk_score: float  # 0~100
    execution_strategy: str  # ExecutionStrategy value
    high_value_flag: bool  # >= HIGH_VALUE_THRESHOLD_KRW_PER_YEAR=10M
    requires_2fa_challenge: (
        bool  # high_value_flag AND execution_strategy == OWNER_APPROVAL_REQUIRED
    )
    estimated_annual_savings_krw: float
    estimated_annual_savings_pct: float
    confidence_breakdown: (
        dict  # utilization_stability + historical_accuracy + demand_forecast_confidence_pct
    )
    risk_breakdown: dict  # savings_pct + commitment_term + commitment_flexibility
    model_version: str
    computed_at: str
    trace_id: str


class ReservedCapacityOrchestration(TypedDict, total=False):
    """19 fields (PRD §F37.4 verbatim)."""

    orchestration_id: str
    tenant_id: str
    period_key: str
    scope_chain: list  # composition_step_chain 5 step trace
    composition_step_chain: (
        list  # [demand_forecast, capacity_planning, commitment_recommendation, approval, execute]
    )
    composition_step_results: dict  # step_index → {step_name, status, computed_at, output}
    cadence: str  # ReservedCapacityCadence value
    cadence_hours_kst: tuple  # (hour, minute) KST
    next_run_at: str  # ISO timestamp KST
    dry_run: bool
    commitment_recommendation_id: str  # FK to CommitmentRecommendation
    capacity_plan_id: str  # FK to ReservedCapacityPlan
    demand_forecast_id: str  # FK to ReservedCapacityDemandForecast
    orchestration_status: str  # pending/running/completed/failed/dry_run
    high_value_flag: bool
    owner_approval_required: bool
    model_version: str
    computed_at: str
    trace_id: str


__all__ = [
    "RESERVED_CAPACITY_ENGINE_MODEL_VERSION",
    "RESERVED_CAPACITY_DEFAULTS",
    "MINIMUM_SAVINGS_PCT",
    "MINIMUM_SAVINGS_KRW",
    "MINIMUM_BREAK_EVEN_UTILIZATION_PCT",
    "CAPACITY_HEADROOM_MIN_PCT",
    "CAPACITY_HEADROOM_MAX_PCT",
    "HIGH_VALUE_THRESHOLD_KRW_PER_YEAR",
    "INDUSTRY_GROWTH_BASELINE_PCT",
    "FIVE_MODULE_WEIGHTS",
    "CONFIDENCE_SCORE_WEIGHTS",
    "RISK_SCORE_WEIGHTS",
    "RESERVED_CAPACITY_CADENCE_HOURS_KST",
    "RESERVED_CAPACITY_RECIPIENT_TEMPLATES",
    "ReservedCapacityTier",
    "ALL_RESERVED_CAPACITY_TIERS",
    "ExecutionStrategy",
    "ALL_EXECUTION_STRATEGIES",
    "ReservedCapacityCadence",
    "ALL_RESERVED_CAPACITY_CADENCES",
    "OrchestrationScope",
    "ALL_ORCHESTRATION_SCOPES",
    "ReservedCapacityDemandForecast",
    "ReservedCapacityPlan",
    "CommitmentRecommendation",
    "ReservedCapacityOrchestration",
]
