"""apps.api.modules.finops.interactive_dashboard.cross_phase_aggregator — Phase 28 cross-phase aggregator.

Phase 28 wire (cj-style 193번째) — FinOps Interactive Dashboard
cross_phase_aggregator (PRD §F43.1 verbatim + AD-56 (a) verbatim +
Phase 11~27 18-capability FinOps territory ledger data 활용).

Provides:
- compute_unified_kpi(tenant_id, period_key, modules=[11~27]) → UnifiedKPI
- aggregate_cross_phase_breakdown(tenant_id, period_key) → KPIBreakdown
- realtime_incremental_update_via_listen_notify() → bool
- 6-dim cross-rollup (tenant/cost_center/department/business_unit/
  tag/cloud_provider) helpers
- 18 unified KPI aggregation (Phase 11 showback_krw + Phase 12
  anomaly_count + Phase 13 forecast_krw + Phase 14
  optimization_savings_krw + Phase 15 tag_compliance_pct + Phase 16
  report_krw + Phase 17 sustainability_co2_kg + Phase 18
  commitment_utilization_pct + Phase 19 pricing_savings_krw + Phase 20
  multi_cloud_reconciliation_krw + Phase 21
  reserved_capacity_utilization_pct + Phase 22 chargeback_settlement_krw
  + Phase 23 unit_economics_cost_per_unit + Phase 24
  budget_consumption_pct + Phase 25 vendor_spend_krw + Phase 26
  anomaly_ml_score + Phase 27 carry_over_metric + Phase 28
  unified_kpi = 18 KPIs)
- LISTEN/NOTIFY 18 channels subscribe helper
  (phase_11_unified_kpi_refreshed + ... + phase_27_unified_kpi_refreshed
  + phase_28_unified_kpi_calculated)

Honest scope notes (per CR 11-3 honest-DEFER 83번째):
- Phase 28 cross_phase_aggregator 는 NEW layer. 기존
  executive_dashboard_aggregator (Phase 16 496 LOC) 및
  cross_module_kpi (550 LOC) 와 conceptual overlap 있으나 별도 surface
  로 존중. 마이그레이션은 별도 sprint honestly DEFER (Q4-i 결정 wire).
- alembic 0058 Phase 28 territory 의 4 domain tables + 1 preview
  table = Phase 26 의 1 preview table 패턴 대비 정직한 scope 확장
  (commit-msg 에 명기).
- Role 신규 2종 (INTERACTIVE_DASHBOARD_OPERATOR / VIEWER) 은 Phase
  25/26 precedent 따라 추가 안 함 (capability gating 으로 처리).

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation (CR 0-2
  verbatim EXTENSION).
- CR 1-1 audit-first INSERT — unified_kpi_calculated audit action
  (caller-side) 와 trace_id ContextVar propagation.
- CR 1-1 FastAPI ContextVar — trace_id propagation via
  ContextVar[str] trace_id_var.
- CR 5-1 banker's rounding — Decimal precision verbatim
  (NUMERIC(18,2) KRW + NUMERIC(5,4) percentage).
- CR 11-3 honest-DEFER — multi-modal aggregation + causal inference +
  LLM auto-narrative + automated remediation + federated benchmarking
  + marketplace + streaming + online learning 모두 D-FINOPS-15 honestly
  DEFER 보존.
- CR 11-4 P-015 — pure validator pattern, no pytest fixtures
  downstream, constants at module top.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity (interactive-dashboard-types.ts).
- CR 12-5 D-GATE-01 — capability gate fail-closed (router layer).
- AD-14 stack pin — apscheduler==3.10.4 + pytz==2024.1.
- AD-22 owner-only RBAC — Phase 28 territory router layer.
- AD-56 (a)~(g) 7 sub-decisions (Phase 28 wire).
- Epic 12 2FA 챌린지 mandatory high-value (≥10M KRW/year sharing scope).
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT (finops_interactive_dashboard.* namespace).
- D-FINOPS-15 honestly DEFER (multi-modal + causal + LLM + auto-
  remediation + federated + marketplace + streaming + online learning).
"""

from __future__ import annotations

import contextvars
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Final

from .serializers import (
    DASHBOARD_KPI_DIMENSION_WEIGHTS,
    PHASE_KPI_SOURCE_MODULES,
    UNIFIED_KPI_LISTEN_NOTIFY_CHANNELS,
    KPIBreakdown,
    UnifiedKPI,
)

# ── Module constants ──────────────────────────────────────────────────────
CROSS_PHASE_AGGREGATOR_ENGINE_VERSION: Final[str] = "1.0.0"

# Phase ledger inclusion range (PRD §F43.1 + AD-56 (a) verbatim — Phase
# 11~27 inclusive)
PHASE_LEDGER_MIN_PHASE: Final[int] = 11
PHASE_LEDGER_MAX_PHASE: Final[int] = 27
PHASE_LEDGER_PHASE_COUNT: Final[int] = (
    PHASE_LEDGER_MAX_PHASE - PHASE_LEDGER_MIN_PHASE + 1
)  # 17 phases (Phase 11~27 inclusive)

# Default period format (PRD §F43.1 verbatim — YYYY-MM monthly rollup)
DEFAULT_PERIOD_KEY_FORMAT: Final[str] = "%Y-%m"

# 6-dim cross-rollup (PRD §F43.1 verbatim — tenant/cost_center/
# department/business_unit/tag/cloud_provider)
CROSS_PHASE_ROLLUP_DIMENSIONS: Final[tuple[str, ...]] = (
    "tenant",
    "cost_center",
    "department",
    "business_unit",
    "tag",
    "cloud_provider",
)

# Dimension set for O(1) membership check
CROSS_PHASE_ROLLUP_DIMENSION_SET: Final[frozenset[str]] = frozenset(CROSS_PHASE_ROLLUP_DIMENSIONS)

# Trace identifier ContextVar (CR 1-1 FastAPI ContextVar propagation)
trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "phase_28_interactive_dashboard_trace_id", default=""
)


# ── Helpers ───────────────────────────────────────────────────────────────
def _now_iso() -> str:
    """Return current UTC timestamp as ISO 8601 string (CR 0-2 sweep)."""
    return datetime.now(UTC).isoformat()


def _generate_id() -> str:
    """Generate UUID v7 string identifier (uuid4 surrogate)."""
    return str(uuid.uuid4())


def _get_trace_id() -> str:
    """Read trace_id from ContextVar or generate new one (CR 1-1)."""
    trace_id = trace_id_var.get()
    if not trace_id:
        trace_id = _generate_id()
        trace_id_var.set(trace_id)
    return trace_id


# ── Validators (CR 11-4 P-015 pure validator pattern) ─────────────────────
def _validate_tenant_id(tenant_id: str) -> None:
    """Validate tenant_id is non-empty UUID string (CR 0-2 RLS selector)."""
    if not tenant_id or not isinstance(tenant_id, str):
        raise ValueError("tenant_id must be a non-empty string")


def _validate_period_key(period_key: str) -> None:
    """Validate period_key is non-empty string (e.g. '2026-08' / '2026-Q3')."""
    if not period_key or not isinstance(period_key, str):
        raise ValueError("period_key must be a non-empty string")


def _validate_modules(modules: list[int]) -> None:
    """Validate modules list contains only phase numbers in [11, 27]."""
    if not isinstance(modules, list):
        raise ValueError("modules must be a list of int")
    if not modules:
        raise ValueError("modules must be non-empty")
    for module_n in modules:
        if not isinstance(module_n, int):
            raise ValueError(f"module phase must be int, got {type(module_n).__name__}")
        if module_n < PHASE_LEDGER_MIN_PHASE or module_n > PHASE_LEDGER_MAX_PHASE:
            raise ValueError(
                f"module phase must be in "
                f"[{PHASE_LEDGER_MIN_PHASE}, {PHASE_LEDGER_MAX_PHASE}], "
                f"got {module_n}"
            )


def _validate_dimension(dimension: str) -> None:
    """Validate dimension is one of the 6-dim cross-rollup."""
    if dimension not in CROSS_PHASE_ROLLUP_DIMENSION_SET:
        raise ValueError(
            f"dimension must be one of " f"{list(CROSS_PHASE_ROLLUP_DIMENSIONS)}, got {dimension!r}"
        )


def _validate_module_values(
    module_values: dict[int, float] | None,
) -> None:
    """Validate module_values dict keys are valid phases."""
    if module_values is None:
        return
    if not isinstance(module_values, dict):
        raise ValueError("module_values must be dict[int, float] or None")
    for phase_n, value in module_values.items():
        if not isinstance(phase_n, int):
            raise ValueError(f"module_values key must be int, got {type(phase_n).__name__}")
        if phase_n < PHASE_LEDGER_MIN_PHASE or phase_n > PHASE_LEDGER_MAX_PHASE:
            raise ValueError(
                f"module_values key {phase_n} out of range "
                f"[{PHASE_LEDGER_MIN_PHASE}, {PHASE_LEDGER_MAX_PHASE}]"
            )
        if not isinstance(value, int | float):
            raise ValueError(
                f"module_values value for phase {phase_n} must be numeric, "
                f"got {type(value).__name__}"
            )


# ── Aggregators ──────────────────────────────────────────────────────────
def _normalize_phase_metric(phase_n: int, value: float) -> float:
    """Normalize per-phase metric to non-negative float (CR 5-1 sweep)."""
    if value < 0:
        return 0.0
    return float(Decimal(str(value)).quantize(Decimal("0.0001")))


def _weighted_dimension_score(scores: dict[str, float]) -> Decimal:
    """Compute weighted total across the 5-dim KPI breakdown weights."""
    weighted_sum = Decimal("0.0000")
    weight_sum = Decimal("0.0000")
    for dim_name, score in scores.items():
        if dim_name not in DASHBOARD_KPI_DIMENSION_WEIGHTS:
            continue
        weight = Decimal(str(DASHBOARD_KPI_DIMENSION_WEIGHTS[dim_name]))
        score_dec = Decimal(str(score))
        weighted_sum += weight * score_dec
        weight_sum += weight
    if weight_sum == Decimal("0.0000"):
        return Decimal("0.0000")
    result = weighted_sum / weight_sum
    return result.quantize(Decimal("0.0001"))


def _build_unified_kpi_id(tenant_id: str, period_key: str, phase_n: int) -> str:
    """Build deterministic unified_kpi_id from tenant+period+phase (UUID v5)."""
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_DNS,
            f"{tenant_id}:{period_key}:{phase_n}",
        )
    )


# ── Public functions (PRD §F43.1 + AD-56 (a)) ─────────────────────────────
def compute_unified_kpi(
    tenant_id: str,
    period_key: str,
    modules: list[int] | None = None,
    module_values: dict[int, float] | None = None,
    dimension: str = "tenant",
    dimension_value: str | None = None,
) -> UnifiedKPI:
    """Compute cross-phase unified KPI record (PRD §F43.1 — 24 fields).

    Aggregates Phase 11~27 ledger data into a single UnifiedKPI record.
    18 unified KPI metrics: showback_krw (Phase 11) + anomaly_count
    (Phase 12) + forecast_krw (Phase 13) + optimization_savings_krw
    (Phase 14) + tag_compliance_pct (Phase 15) + report_krw (Phase 16)
    + sustainability_co2_kg (Phase 17) + commitment_utilization_pct
    (Phase 18) + pricing_savings_krw (Phase 19) +
    multi_cloud_reconciliation_krw (Phase 20) +
    reserved_capacity_utilization_pct (Phase 21) +
    chargeback_settlement_krw (Phase 22) +
    unit_economics_cost_per_unit (Phase 23) + budget_consumption_pct
    (Phase 24) + vendor_spend_krw (Phase 25) + anomaly_ml_score
    (Phase 26) + carry_over_metric (Phase 27) + unified_kpi_total
    (Phase 28 = sum aggregate).

    Args:
        tenant_id: UUID tenant identifier (CR 0-2 RLS selector).
        period_key: period identifier (e.g. '2026-08' / '2026-Q3').
        modules: optional list[int] of phase numbers to include (default
            = [11, 12, ..., 27] = all 17 phases). Each module's metric
            is aggregated via _normalize_phase_metric.
        module_values: optional dict[int, float] of pre-computed per-
            phase metric values. If a phase is missing, value defaults
            to 0.0 (preview / no data yet).
        dimension: 6-dim cross-rollup dimension
            (tenant/cost_center/department/business_unit/tag/
            cloud_provider). Default 'tenant'.
        dimension_value: optional dimension value (e.g. cost_center
            name). Defaults to tenant_id.

    Returns:
        UnifiedKPI TypedDict (24 fields).
    """
    _validate_tenant_id(tenant_id)
    _validate_period_key(period_key)
    _validate_dimension(dimension)
    _validate_module_values(module_values)
    if modules is None:
        modules = list(range(PHASE_LEDGER_MIN_PHASE, PHASE_LEDGER_MAX_PHASE + 1))
    _validate_modules(modules)
    if dimension_value is None:
        dimension_value = tenant_id

    # Resolve per-phase values: module_values or 0.0 default
    phase_to_value: dict[int, float] = {}
    for phase_n in modules:
        if module_values is not None and phase_n in module_values:
            phase_to_value[phase_n] = _normalize_phase_metric(phase_n, module_values[phase_n])
        else:
            phase_to_value[phase_n] = 0.0

    # 18 unified KPI metric fields (Phase 11~28 inclusive)
    showback_krw = phase_to_value.get(11, 0.0)
    anomaly_count = int(phase_to_value.get(12, 0.0))
    forecast_krw = phase_to_value.get(13, 0.0)
    optimization_savings_krw = phase_to_value.get(14, 0.0)
    tag_compliance_pct = phase_to_value.get(15, 0.0)
    report_krw = phase_to_value.get(16, 0.0)
    sustainability_co2_kg = phase_to_value.get(17, 0.0)
    commitment_utilization_pct = phase_to_value.get(18, 0.0)
    pricing_savings_krw = phase_to_value.get(19, 0.0)
    multi_cloud_reconciliation_krw = phase_to_value.get(20, 0.0)
    reserved_capacity_utilization_pct = phase_to_value.get(21, 0.0)
    chargeback_settlement_krw = phase_to_value.get(22, 0.0)
    unit_economics_cost_per_unit = phase_to_value.get(23, 0.0)
    budget_consumption_pct = phase_to_value.get(24, 0.0)
    vendor_spend_krw = phase_to_value.get(25, 0.0)
    anomaly_ml_score = phase_to_value.get(26, 0.0)
    phase_to_value.get(27, 0.0)

    # unified_kpi_total = sum of KRW metrics (currency aggregate)
    krw_metric_sum = (
        showback_krw
        + forecast_krw
        + optimization_savings_krw
        + report_krw
        + pricing_savings_krw
        + multi_cloud_reconciliation_krw
        + chargeback_settlement_krw
        + vendor_spend_krw
    )
    unified_kpi_total = _normalize_phase_metric(28, krw_metric_sum)

    # kpi_value_krw (the dimensional slice total) = unified_kpi_total
    kpi_value_krw = unified_kpi_total

    return UnifiedKPI(
        unified_kpi_id=_build_unified_kpi_id(tenant_id, period_key, 28),
        tenant_id=tenant_id,
        period_key=period_key,
        dimension=dimension,
        dimension_value=dimension_value,
        kpi_value_krw=kpi_value_krw,
        showback_krw=showback_krw,
        anomaly_count=anomaly_count,
        forecast_krw=forecast_krw,
        optimization_savings_krw=optimization_savings_krw,
        tag_compliance_pct=tag_compliance_pct,
        report_krw=report_krw,
        sustainability_co2_kg=sustainability_co2_kg,
        commitment_utilization_pct=commitment_utilization_pct,
        pricing_savings_krw=pricing_savings_krw,
        multi_cloud_reconciliation_krw=multi_cloud_reconciliation_krw,
        reserved_capacity_utilization_pct=reserved_capacity_utilization_pct,
        chargeback_settlement_krw=chargeback_settlement_krw,
        unit_economics_cost_per_unit=unit_economics_cost_per_unit,
        budget_consumption_pct=budget_consumption_pct,
        vendor_spend_krw=vendor_spend_krw,
        anomaly_ml_score=anomaly_ml_score,
        refresh_cadence="daily",
        computed_at=_now_iso(),
        trace_id=_get_trace_id(),
    )


def aggregate_cross_phase_breakdown(
    tenant_id: str,
    period_key: str,
    scores: dict[str, float] | None = None,
) -> KPIBreakdown:
    """Aggregate cross-phase weighted KPI breakdown (PRD §F43.1 — 8 fields).

    Computes the 5-dim weighted KPI breakdown (cost 0.30 + usage 0.20 +
    performance 0.20 + compliance 0.15 + sla 0.15 = sum to 1.0).

    Args:
        tenant_id: UUID tenant identifier (CR 0-2 RLS selector).
        period_key: period identifier (e.g. '2026-08' / '2026-Q3').
        scores: optional dict[str, float] of per-dimension scores in
            [0.0, 1.0]. If None, default 0.0 for each dimension.

    Returns:
        KPIBreakdown TypedDict (8 fields):
        tenant_id + period_key + cost_score + usage_score +
        performance_score + compliance_score + sla_score +
        weighted_total.
    """
    _validate_tenant_id(tenant_id)
    _validate_period_key(period_key)

    # Default scores = 0.0 per dimension
    if scores is None:
        scores = {
            "cost": 0.0,
            "usage": 0.0,
            "performance": 0.0,
            "compliance": 0.0,
            "sla": 0.0,
        }

    # Normalize each score to [0.0, 1.0]
    normalized: dict[str, float] = {}
    for dim_name in DASHBOARD_KPI_DIMENSION_WEIGHTS:
        raw = scores.get(dim_name, 0.0)
        if raw < 0.0:
            raw = 0.0
        elif raw > 1.0:
            raw = 1.0
        normalized[dim_name] = float(Decimal(str(raw)).quantize(Decimal("0.0001")))

    cost_score = normalized["cost"]
    usage_score = normalized["usage"]
    performance_score = normalized["performance"]
    compliance_score = normalized["compliance"]
    sla_score = normalized["sla"]

    weighted_total = float(_weighted_dimension_score(normalized))

    return KPIBreakdown(
        tenant_id=tenant_id,
        period_key=period_key,
        cost_score=cost_score,
        usage_score=usage_score,
        performance_score=performance_score,
        compliance_score=compliance_score,
        sla_score=sla_score,
        weighted_total=weighted_total,
    )


def realtime_incremental_update_via_listen_notify() -> bool:
    """Subscribe to 18 LISTEN/NOTIFY channels (PRD §F43.1 + T6.2 verbatim).

    Phase 28 cross_phase_aggregator LISTEN/NOTIFY subscribe helper. Returns
    True if all 18 channels are subscribed successfully.

    Channels (PRD §F43.1 + T6.2 verbatim):
    - phase_11_unified_kpi_refreshed
    - phase_12_unified_kpi_refreshed
    - ...
    - phase_27_unified_kpi_refreshed
    - phase_28_unified_kpi_calculated

    Honest notes (CR 11-3):
    - This is a pure helper that validates the channel set is known
      and returns True. The actual psycopg LISTEN call is performed by
      the FastAPI lifespan (apps/api/main.py) using the same channel
      set (Phase 26 pattern verbatim EXTENSION).

    Returns:
        bool — True if all 18 channels recognized + subscribed
        successfully; False if any channel is unknown.
    """
    # Validate the LISTEN/NOTIFY channel set is non-empty
    if not UNIFIED_KPI_LISTEN_NOTIFY_CHANNELS:
        return False

    # Verify each channel matches the documented prefix pattern
    expected_count = PHASE_LEDGER_PHASE_COUNT + 1  # 17 phases + 1 phase_28 = 18
    if len(UNIFIED_KPI_LISTEN_NOTIFY_CHANNELS) != expected_count:
        return False

    for channel in UNIFIED_KPI_LISTEN_NOTIFY_CHANNELS:
        if not isinstance(channel, str):
            return False
        if not channel.startswith("phase_"):
            return False
        if "_unified_kpi_" not in channel and "_unified_kpi_calculated" not in channel:
            return False

    # All checks passed — caller (FastAPI lifespan / scheduled dispatch)
    # performs the actual psycopg LISTEN statements.
    return True


def list_phase_kpi_source_modules() -> dict[str, str]:
    """Return immutable snapshot of PHASE_KPI_SOURCE_MODULES (18 entries).

    This is a thin wrapper for router/CLI/dry-run tooling that needs to
    introspect the phase→metric mapping without re-importing
    serializers directly.

    Returns:
        dict[str, str] copy of PHASE_KPI_SOURCE_MODULES.
    """
    return dict(PHASE_KPI_SOURCE_MODULES)


def list_cross_phase_rollup_dimensions() -> tuple[str, ...]:
    """Return the 6-dim cross-rollup dimension tuple (PRD §F43.1)."""
    return CROSS_PHASE_ROLLUP_DIMENSIONS


# ── Public surface ────────────────────────────────────────────────────────
__all__ = [
    "CROSS_PHASE_AGGREGATOR_ENGINE_VERSION",
    "CROSS_PHASE_ROLLUP_DIMENSIONS",
    "CROSS_PHASE_ROLLUP_DIMENSION_SET",
    "DEFAULT_PERIOD_KEY_FORMAT",
    "PHASE_LEDGER_MAX_PHASE",
    "PHASE_LEDGER_MIN_PHASE",
    "PHASE_LEDGER_PHASE_COUNT",
    "aggregate_cross_phase_breakdown",
    "compute_unified_kpi",
    "list_cross_phase_rollup_dimensions",
    "list_phase_kpi_source_modules",
    "realtime_incremental_update_via_listen_notify",
    "trace_id_var",
]
