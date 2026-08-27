"""apps.api.modules.finops.unit_economics — Phase 23 FinOps Unit Economics module.

Phase 23 wire (cj-style 164번째) — FinOps Unit Economics derived metric
layer territory (PRD §F39.1~§F39.8 verbatim + AD-51 (a)~(g) 7
sub-decisions).

4-NEW backend unit_economics modules + scheduled calculation job +
FastAPI router (mirroring Phase 22 5-module + scheduled dispatch +
router pattern verbatim):

1. `unit_economics_engine.py` — unit_economics engine + 5-dim cross-join
   (derived from Phase 22 settlement_id → allocation_lines ledger)
2. `cost_per_business_unit.py` — 5-dim rollup + ledger-key dedup +
   Decimal precision + Epic 12 2FA 챌린지 detection
3. `cost_per_transaction.py` — tag propagation + ledger-key dedup +
   tag filter dimensions
4. `margin_analysis.py` — OPTIONAL revenue attribution + 3-tier status
   thresholds + alert generation + Epic 12 2FA 챌린지 detection
5. `scheduled_unit_economics_calculation.py` — apscheduler 3.10.4 +
   pytz 2024.1 + 4 cadence (daily 03:30 + weekly 04:00 + monthly 04:30
   + quarterly 05:00 KST)
6. `unit_economics_routes.py` — FastAPI router 9 endpoints
7. `serializers.py` — TypedDicts + Enums + Constants

Module tag: `m31_finops_unit_economics`
ALLOWED_SERVICE_SUBMODULES EXTENSION 신규 결정 wire
(Phase 22 m30_finops_chargeback_settlement 패턴 verbatim mirror).

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — 7 NEW audit actions.
- CR 1-1 ContextVar — trace_id propagation.
- CR 1-1 idempotent no-op — duplicate calculation cached.
- CR 5-1 banker's rounding — Decimal precision verbatim.
- CR 11-2 AUTHORIZABLE_TARGET_EVENT_TYPES — auth-layer check.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 15 NEW typed exceptions.
- CR 12-5 D-PARITY-01 — TypeScript mirror parity.
- CR 12-5 D-GATE-01 — capability gate fail-closed.
- AD-14 stack pin — Recharts 2.12.7 + noto-sans-cjk-kr + apscheduler 3.10.4 + pytz 2024.1.
- AD-22 owner-only RBAC.
- AD-51 (a)~(g) 7 sub-decisions.
- Epic 12 2FA 챌린지 mandatory high-value (≥10M KRW/year).
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT (finops_unit_economics.* namespace EXTENSION).
- D-FINOPS-12 honestly DEFER (cost_per_customer CRM + multi-currency
  FX + real-time stream — all honestly DEFER to future Phase 23.x).
- CR 11-3 ALLOWED_SERVICE_SUBMODULES 즉시 sweep EXTENSION
  m31_finops_unit_economics (Phase 23 53rd honest-DEFER cycle).
"""
from __future__ import annotations

from apps.api.modules.finops.unit_economics.cost_per_business_unit import (
    COST_PER_BU_AMOUNT_QUANTUM,
    COST_PER_X_METRIC_WEIGHT_SUM,
    DERIVATION_DIMENSION_WEIGHT_SUM,
    aggregate_cost_per_business_unit,
    compute_cost_per_business_unit,
    validate_cost_per_business_unit,
)
from apps.api.modules.finops.unit_economics.cost_per_transaction import (
    ALLOWED_TAG_KEYS,
    COST_PER_TX_AMOUNT_QUANTUM,
    aggregate_cost_per_transaction,
    compute_cost_per_transaction,
    validate_cost_per_transaction,
)
from apps.api.modules.finops.unit_economics.margin_analysis import (
    MARGIN_AMOUNT_QUANTUM,
    MARGIN_PCT_QUANTUM,
    aggregate_margin_analysis,
    execute_margin_analysis,
    validate_margin_analysis,
)
from apps.api.modules.finops.unit_economics.scheduled_unit_economics_calculation import (
    ALL_UNIT_ECONOMICS_CADENCES,
    compute_unit_economics_period,
    execute_calculation,
    schedule_cadence_calculation,
    validate_cadence,
)
from apps.api.modules.finops.unit_economics.serializers import (
    ALL_COST_PER_X_METRICS,
    ALL_MARGIN_ANALYSIS_STATUSES,
    ALL_UNIT_ECONOMICS_ALERT_SEVERITIES,
    ALL_UNIT_ECONOMICS_CALCULATION_STATUSES,
    ALL_UNIT_ECONOMICS_DIMENSIONS,
    COST_PER_X_METRIC_WEIGHTS,
    DERIVATION_DIMENSION_WEIGHTS,
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    MARGIN_CRITICAL_THRESHOLD_PCT,
    MARGIN_HEALTHY_THRESHOLD_PCT,
    MARGIN_NEGATIVE_PCT,
    MARGIN_WARNING_THRESHOLD_PCT,
    MAX_BUSINESS_UNITS_PER_TENANT,
    MAX_COST_PER_X_OVERRIDE_KRW,
    MAX_TRANSACTIONS_PER_PERIOD,
    UNIT_ECONOMICS_CADENCE_HOURS_KST,
    UNIT_ECONOMICS_DEFAULTS,
    UNIT_ECONOMICS_ENGINE_MODEL_VERSION,
    UNIT_ECONOMICS_RECIPIENT_TEMPLATES,
    CostPerBusinessUnitBreakdown,
    CostPerTransactionBreakdown,
    CostPerXMetric,
    MarginAnalysisResult,
    MarginAnalysisStatus,
    UnitEconomicsAlert,
    UnitEconomicsAlertSeverity,
    UnitEconomicsCalculationStatus,
    UnitEconomicsDimension,
    UnitEconomicsResult,
)
from apps.api.modules.finops.unit_economics.unit_economics_engine import (
    compute_unit_economics,
    list_unit_economics_results,
    validate_unit_economics_result,
)
from apps.api.modules.finops.unit_economics.unit_economics_routes import (
    router as unit_economics_router,
)

# ── Module tag for ALLOWED_SERVICE_SUBMODULES sweep ───────────────────────
MODULE_TAG = "m31_finops_unit_economics"


__all__ = [
    # ── Module tag ─────────────────────────────────────────────────────────
    "MODULE_TAG",
    # ── Serializers: Constants ─────────────────────────────────────────────
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
    # ── Serializers: Enums ─────────────────────────────────────────────────
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
    # ── Serializers: TypedDicts ────────────────────────────────────────────
    "UnitEconomicsResult",
    "CostPerBusinessUnitBreakdown",
    "CostPerTransactionBreakdown",
    "MarginAnalysisResult",
    "UnitEconomicsAlert",
    # ── unit_economics_engine ──────────────────────────────────────────────
    "compute_unit_economics",
    "list_unit_economics_results",
    "validate_unit_economics_result",
    # ── cost_per_business_unit ─────────────────────────────────────────────
    "DERIVATION_DIMENSION_WEIGHT_SUM",
    "COST_PER_X_METRIC_WEIGHT_SUM",
    "COST_PER_BU_AMOUNT_QUANTUM",
    "compute_cost_per_business_unit",
    "validate_cost_per_business_unit",
    "aggregate_cost_per_business_unit",
    # ── cost_per_transaction ───────────────────────────────────────────────
    "ALLOWED_TAG_KEYS",
    "COST_PER_TX_AMOUNT_QUANTUM",
    "compute_cost_per_transaction",
    "validate_cost_per_transaction",
    "aggregate_cost_per_transaction",
    # ── margin_analysis ────────────────────────────────────────────────────
    "MARGIN_AMOUNT_QUANTUM",
    "MARGIN_PCT_QUANTUM",
    "execute_margin_analysis",
    "validate_margin_analysis",
    "aggregate_margin_analysis",
    # ── scheduled_unit_economics_calculation ──────────────────────────────
    "ALL_UNIT_ECONOMICS_CADENCES",
    "compute_unit_economics_period",
    "schedule_cadence_calculation",
    "execute_calculation",
    "validate_cadence",
    # ── unit_economics_routes ──────────────────────────────────────────────
    "unit_economics_router",
]
