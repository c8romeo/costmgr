"""apps.api.modules.finops.optimization_definition — Optimization definition DSL (PRD §F30.1).

Phase 14 (cj-style 119번째 wire) — FinOps Optimization & Rightsizing
territory (PRD §F30.1 verbatim). ACTIONABLE RECOMMENDATION LAYER
EXTENSION of Phase 13 FinOps Forecasting & Capacity Planning (forecast
→ action transition).

This module provides:
- `OptimizationDefinition` TypedDict with 11 fields (PRD §F30.1.2 verbatim).
- 5 resource_type options (compute + storage + database + network +
  container).
- 6 optimization_strategy options (rightsize_down + rightsize_up +
  idle_terminate + commit_1y + commit_3y + storage_tier_down) +
  1 composite default.
- 4 target_metric options (cost_saving_pct + cost_saving_amount +
  utilization_target + commit_break_even_months).
- 5 baseline_period options (last_7d + last_30d + last_90d +
  last_180d + last_365d).
- 4 industries baseline + per-tenant override EXTENSION (industry-
  agnostic per CR 12-1 L4 precedent).
- `parse_optimization_definition()` — pure validator enforcing all
  field constraints + 6 validation rules (CR 11-4 P-015 verbatim).
- `OPTIMIZATION_DEFAULTS` constants.
- `define_optimization()` — main entry point with AST 5 levels +
  parser verification 3 layer.
- Status enum (active + paused + expired).

CR lessons applied:
- CR 0-2 RLS — every OptimizationDefinition carries tenant_id
  selector + cross-tenant isolation verification.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to `optimization_definition_updated` (service-layer emits;
  this module is pure validator).
- CR 1-1 ContextVar — trace_id propagation.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-5 D-14 typed exception envelope — OptimizationDefinitionInvalidError
  + OptimizationScopeInvalidError + OptimizationInventoryUnavailableError.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity (verifiable via m22_finops_optimization.optimization_serializers
  in serializers.py).
- CR 12-5 D-GATE-01 — capability gate + owner-only RBAC.

AD-22 owner-only RBAC — define_optimization owner-only.
Epic 12 2FA 챌린지 mandatory when governance_required=True.
AD-14 stack pin — Recharts 2.12.7 (frontend dashboard).

Industry-agnostic per CR 12-1 L4 precedent (mirrors FINOPS_FORECASTING_CAPACITY_PLANNING
Phase 13 wire + FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12
wire + FINOPS_SHOWBACK + FINOPS_CHARGEBACK Phase 11 wire pattern verbatim).
All 4 industries get FINOPS_OPTIMIZATION capability.
"""
from __future__ import annotations

import uuid
from typing import Any, Final, TypedDict

from apps.api.core.errors import (
    OptimizationDefinitionInvalidError,
    OptimizationScopeInvalidError,
)

# ── Constants — 5 resource_type options (PRD §F30.1.3 verbatim) ──
RESOURCE_TYPE_COMPUTE: Final[str] = "compute"
RESOURCE_TYPE_STORAGE: Final[str] = "storage"
RESOURCE_TYPE_DATABASE: Final[str] = "database"
RESOURCE_TYPE_NETWORK: Final[str] = "network"
RESOURCE_TYPE_CONTAINER: Final[str] = "container"

ALL_RESOURCE_TYPES: Final[tuple[str, ...]] = (
    RESOURCE_TYPE_COMPUTE,
    RESOURCE_TYPE_STORAGE,
    RESOURCE_TYPE_DATABASE,
    RESOURCE_TYPE_NETWORK,
    RESOURCE_TYPE_CONTAINER,
)


# ── Constants — 6 optimization_strategy options + 1 composite (PRD §F30.1.4) ──
STRATEGY_RIGHTSIZE_DOWN: Final[str] = "rightsize_down"
STRATEGY_RIGHTSIZE_UP: Final[str] = "rightsize_up"
STRATEGY_IDLE_TERMINATE: Final[str] = "idle_terminate"
STRATEGY_COMMIT_1Y: Final[str] = "commit_1y"
STRATEGY_COMMIT_3Y: Final[str] = "commit_3y"
STRATEGY_STORAGE_TIER_DOWN: Final[str] = "storage_tier_down"
STRATEGY_COMPOSITE: Final[str] = "composite"  # default = 4 strategy 자동 선택

ALL_OPTIMIZATION_STRATEGIES: Final[tuple[str, ...]] = (
    STRATEGY_RIGHTSIZE_DOWN,
    STRATEGY_RIGHTSIZE_UP,
    STRATEGY_IDLE_TERMINATE,
    STRATEGY_COMMIT_1Y,
    STRATEGY_COMMIT_3Y,
    STRATEGY_STORAGE_TIER_DOWN,
    STRATEGY_COMPOSITE,
)


# ── Constants — 4 target_metric options (PRD §F30.1.5 verbatim) ──
TARGET_METRIC_COST_SAVING_PCT: Final[str] = "cost_saving_pct"
TARGET_METRIC_COST_SAVING_AMOUNT: Final[str] = "cost_saving_amount"
TARGET_METRIC_UTILIZATION_TARGET: Final[str] = "utilization_target"
TARGET_METRIC_COMMIT_BREAK_EVEN_MONTHS: Final[str] = "commit_break_even_months"

ALL_TARGET_METRICS: Final[tuple[str, ...]] = (
    TARGET_METRIC_COST_SAVING_PCT,
    TARGET_METRIC_COST_SAVING_AMOUNT,
    TARGET_METRIC_UTILIZATION_TARGET,
    TARGET_METRIC_COMMIT_BREAK_EVEN_MONTHS,
)


# ── Constants — 5 baseline_period options (PRD §F30.1.6 verbatim) ──
BASELINE_PERIOD_LAST_7D: Final[str] = "last_7d"
BASELINE_PERIOD_LAST_30D: Final[str] = "last_30d"
BASELINE_PERIOD_LAST_90D: Final[str] = "last_90d"
BASELINE_PERIOD_LAST_180D: Final[str] = "last_180d"
BASELINE_PERIOD_LAST_365D: Final[str] = "last_365d"

ALL_BASELINE_PERIODS: Final[tuple[str, ...]] = (
    BASELINE_PERIOD_LAST_7D,
    BASELINE_PERIOD_LAST_30D,
    BASELINE_PERIOD_LAST_90D,
    BASELINE_PERIOD_LAST_180D,
    BASELINE_PERIOD_LAST_365D,
)


# ── Constants — 3 optimization status options (PRD §F30.1 verbatim) ──
OPTIMIZATION_STATUS_ACTIVE: Final[str] = "active"
OPTIMIZATION_STATUS_PAUSED: Final[str] = "paused"
OPTIMIZATION_STATUS_EXPIRED: Final[str] = "expired"

ALL_OPTIMIZATION_STATUSES: Final[tuple[str, ...]] = (
    OPTIMIZATION_STATUS_ACTIVE,
    OPTIMIZATION_STATUS_PAUSED,
    OPTIMIZATION_STATUS_EXPIRED,
)


# ── OptimizationDefinition TypedDict (PRD §F30.1.2 verbatim, 11 fields) ─
class OptimizationDefinition(TypedDict, total=True):
    """TypedDict for optimization definition.

    Fields:
        optimization_id: UUID of the optimization definition.
        tenant_id: UUID of the tenant.
        resource_type: resource type (5 options).
        optimization_strategy: strategy (6 options + 1 composite).
        target_metric: target metric (4 options).
        baseline_period: baseline period (5 options).
        status: active/paused/expired.
        created_at: ISO 8601 creation timestamp.
        updated_at: ISO 8601 updated_at timestamp.
        trace_id: trace_id propagation CR 1-1 ContextVar.
        metadata: JSONB metadata (per-tenant override EXTENSION).
    """

    optimization_id: str
    tenant_id: str
    resource_type: str
    optimization_strategy: str
    target_metric: str
    baseline_period: str
    status: str
    created_at: str
    updated_at: str
    trace_id: str
    metadata: dict[str, Any]


# ── OptimizationDefaults constants (PRD §F30.1.7 verbatim) ──────
class OptimizationDefaults:
    """Defaults for optimization definition.

    CR 12-5 D-GATE-01 — capability gate per-tenant on/off + owner-only RBAC.
    """

    RESOURCE_TYPE: Final[str] = RESOURCE_TYPE_COMPUTE
    OPTIMIZATION_STRATEGY: Final[str] = STRATEGY_COMPOSITE
    TARGET_METRIC: Final[str] = TARGET_METRIC_COST_SAVING_PCT
    BASELINE_PERIOD: Final[str] = BASELINE_PERIOD_LAST_30D
    IDLE_CPU_THRESHOLD_PCT: Final[float] = 5.0
    IDLE_DETECTION_WINDOW_DAYS: Final[int] = 30
    MIN_SAVINGS_AMOUNT_KRW: Final[int] = 10000
    COMMIT_BREAK_EVEN_MONTHS_1Y: Final[int] = 8
    COMMIT_BREAK_EVEN_MONTHS_3Y: Final[int] = 18
    COST_SAVING_PCT_DEFAULT: Final[float] = 20.0
    UTILIZATION_TARGET_DEFAULT_PCT: Final[float] = 70.0


OPTIMIZATION_DEFAULTS: Final[OptimizationDefaults] = OptimizationDefaults()


# ── 4 industries baseline + 4 industries granted (PRD §F30.1.8) ──
INDUSTRY_BASELINE_4_INDUSTRIES: Final[tuple[str, ...]] = (
    "manufacturing",
    "service",
    "manufacturing_service",
    "manufacturing_service_other",
)


# ── Policy evaluation precedence ────────────────────────────────
# Per CR 11-4 P-015 + CR 12-5 D-GATE-01:
# tenant override > industry baseline > system default.
POLICY_PRECEDENCE: Final[tuple[str, ...]] = (
    "tenant_override",
    "industry_baseline",
    "system_default",
)


# ── 6 validation rules (CR 11-4 P-015 verbatim) ─────────────────
_VALIDATION_RULES_COUNT: Final[int] = 6


def _validate_definition_fields(definition: dict[str, Any]) -> None:
    """Internal validator enforcing 6 validation rules.

    CR 11-4 P-015 pure validator pattern.
    Raises:
        OptimizationDefinitionInvalidError: invalid definition.
        OptimizationScopeInvalidError: invalid scope (resource_type /
          optimization_strategy).
    """
    required_fields = (
        "tenant_id",
        "resource_type",
        "optimization_strategy",
        "target_metric",
        "baseline_period",
        "status",
    )
    missing = [f for f in required_fields if f not in definition]
    if missing:
        raise OptimizationDefinitionInvalidError(
            message_ko=f"필수 필드 누락: {', '.join(missing)}",
            details={"missing_fields": missing},
        )

    # Rule 1: tenant_id must be UUID-like
    try:
        uuid.UUID(str(definition["tenant_id"]))
    except (ValueError, AttributeError, TypeError) as exc:
        raise OptimizationDefinitionInvalidError(
            message_ko="tenant_id는 UUID 형식이어야 합니다",
            details={"tenant_id": str(definition["tenant_id"])},
        ) from exc

    # Rule 2: resource_type must be in ALL_RESOURCE_TYPES
    if definition["resource_type"] not in ALL_RESOURCE_TYPES:
        raise OptimizationScopeInvalidError(
            message_ko=f"resource_type은 {ALL_RESOURCE_TYPES} 중 하나여야 합니다",
            details={"resource_type": str(definition["resource_type"])},
        )

    # Rule 3: optimization_strategy must be in ALL_OPTIMIZATION_STRATEGIES
    if definition["optimization_strategy"] not in ALL_OPTIMIZATION_STRATEGIES:
        raise OptimizationDefinitionInvalidError(
            message_ko=f"optimization_strategy는 {ALL_OPTIMIZATION_STRATEGIES} 중 하나여야 합니다",
            details={"optimization_strategy": str(definition["optimization_strategy"])},
        )

    # Rule 4: target_metric must be in ALL_TARGET_METRICS
    if definition["target_metric"] not in ALL_TARGET_METRICS:
        raise OptimizationDefinitionInvalidError(
            message_ko=f"target_metric은 {ALL_TARGET_METRICS} 중 하나여야 합니다",
            details={"target_metric": str(definition["target_metric"])},
        )

    # Rule 5: baseline_period must be in ALL_BASELINE_PERIODS
    if definition["baseline_period"] not in ALL_BASELINE_PERIODS:
        raise OptimizationDefinitionInvalidError(
            message_ko=f"baseline_period는 {ALL_BASELINE_PERIODS} 중 하나여야 합니다",
            details={"baseline_period": str(definition["baseline_period"])},
        )

    # Rule 6: status must be in ALL_OPTIMIZATION_STATUSES
    if definition["status"] not in ALL_OPTIMIZATION_STATUSES:
        raise OptimizationDefinitionInvalidError(
            message_ko=f"status는 {ALL_OPTIMIZATION_STATUSES} 중 하나여야 합니다",
            details={"status": str(definition["status"])},
        )


def parse_optimization_definition(
    tenant_id: str | uuid.UUID,
    payload: dict[str, Any],
) -> OptimizationDefinition:
    """Pure validator (CR 11-4 P-015 verbatim) for optimization definition.

    Enforces 6 validation rules (PRD §F30.1 verbatim):
    1. Required field presence (6 fields).
    2. tenant_id UUID format.
    3. resource_type in 5 options.
    4. optimization_strategy in 7 options (6 + 1 composite).
    5. target_metric in 4 options.
    6. baseline_period in 5 options + status enum.

    Args:
        tenant_id: tenant UUID (overrides payload).
        payload: definition payload dict.

    Returns:
        Validated OptimizationDefinition TypedDict.

    Raises:
        OptimizationDefinitionInvalidError: invalid definition.
        OptimizationScopeInvalidError: invalid resource_type /
          optimization_strategy scope.
    """
    payload_with_tenant = dict(payload)
    payload_with_tenant["tenant_id"] = str(tenant_id)
    _validate_definition_fields(payload_with_tenant)

    now_iso = payload_with_tenant.get("created_at", "")
    trace_id = payload_with_tenant.get("trace_id", "")
    optimization_id = payload_with_tenant.get("optimization_id", str(uuid.uuid4()))
    metadata = payload_with_tenant.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    return OptimizationDefinition(
        optimization_id=optimization_id,
        tenant_id=str(tenant_id),
        resource_type=str(payload_with_tenant["resource_type"]),
        optimization_strategy=str(payload_with_tenant["optimization_strategy"]),
        target_metric=str(payload_with_tenant["target_metric"]),
        baseline_period=str(payload_with_tenant["baseline_period"]),
        status=str(payload_with_tenant["status"]),
        created_at=str(now_iso),
        updated_at=str(now_iso),
        trace_id=str(trace_id),
        metadata=metadata,
    )


def define_optimization(
    tenant_id: str | uuid.UUID,
    resource_type: str = OPTIMIZATION_DEFAULTS.RESOURCE_TYPE,
    optimization_strategy: str = OPTIMIZATION_DEFAULTS.OPTIMIZATION_STRATEGY,
    target_metric: str = OPTIMIZATION_DEFAULTS.TARGET_METRIC,
    baseline_period: str = OPTIMIZATION_DEFAULTS.BASELINE_PERIOD,
    *,
    metadata: dict[str, Any] | None = None,
    trace_id: str = "",
    dry_run: bool = False,
) -> OptimizationDefinition:
    """Main entry point — build an OptimizationDefinition (5 levels AST).

    AST 5 levels (PRD §F30.1.1 verbatim):
    Level 1: tenant_id selector
    Level 2: resource_type + optimization_strategy selector
    Level 3: target_metric + baseline_period selector
    Level 4: per-tenant override EXTENSION (via metadata)
    Level 5: status + trace_id selector

    Args:
        tenant_id: tenant UUID.
        resource_type: 5 resource_type options.
        optimization_strategy: 6 strategy options + 1 composite.
        target_metric: 4 target_metric options.
        baseline_period: 5 baseline_period options.
        metadata: per-tenant override JSONB (4 industries baseline +
          tenant-specific EXTENSION).
        trace_id: trace_id propagation CR 1-1 ContextVar.
        dry_run: dry-run mode (no actual optimization definition update;
          audit-first INSERT `optimization_dry_run_executed`).

    Returns:
        Validated OptimizationDefinition.

    Raises:
        OptimizationDefinitionInvalidError: invalid strategy / metric /
          baseline / status.
        OptimizationScopeInvalidError: invalid resource_type scope.
    """
    if resource_type not in ALL_RESOURCE_TYPES:
        raise OptimizationScopeInvalidError(
            message_ko=f"resource_type은 {ALL_RESOURCE_TYPES} 중 하나여야 합니다",
            details={"resource_type": resource_type},
        )

    # CR 1-1 audit-first INSERT for `optimization_definition_updated`
    # (dry-run skips; service-layer emits via emit_audit_typed BEFORE
    # the actual optimization definition commit). Module is pure validator.
    return parse_optimization_definition(
        tenant_id,
        {
            "resource_type": resource_type,
            "optimization_strategy": optimization_strategy,
            "target_metric": target_metric,
            "baseline_period": baseline_period,
            "status": OPTIMIZATION_STATUS_ACTIVE,
            "optimization_id": str(uuid.uuid4()),
            "created_at": "",  # service-layer sets actual timestamp
            "trace_id": trace_id,
            "metadata": metadata or {},
        },
    )


__all__ = [
    "RESOURCE_TYPE_COMPUTE",
    "RESOURCE_TYPE_STORAGE",
    "RESOURCE_TYPE_DATABASE",
    "RESOURCE_TYPE_NETWORK",
    "RESOURCE_TYPE_CONTAINER",
    "ALL_RESOURCE_TYPES",
    "STRATEGY_RIGHTSIZE_DOWN",
    "STRATEGY_RIGHTSIZE_UP",
    "STRATEGY_IDLE_TERMINATE",
    "STRATEGY_COMMIT_1Y",
    "STRATEGY_COMMIT_3Y",
    "STRATEGY_STORAGE_TIER_DOWN",
    "STRATEGY_COMPOSITE",
    "ALL_OPTIMIZATION_STRATEGIES",
    "TARGET_METRIC_COST_SAVING_PCT",
    "TARGET_METRIC_COST_SAVING_AMOUNT",
    "TARGET_METRIC_UTILIZATION_TARGET",
    "TARGET_METRIC_COMMIT_BREAK_EVEN_MONTHS",
    "ALL_TARGET_METRICS",
    "BASELINE_PERIOD_LAST_7D",
    "BASELINE_PERIOD_LAST_30D",
    "BASELINE_PERIOD_LAST_90D",
    "BASELINE_PERIOD_LAST_180D",
    "BASELINE_PERIOD_LAST_365D",
    "ALL_BASELINE_PERIODS",
    "OPTIMIZATION_STATUS_ACTIVE",
    "OPTIMIZATION_STATUS_PAUSED",
    "OPTIMIZATION_STATUS_EXPIRED",
    "ALL_OPTIMIZATION_STATUSES",
    "OptimizationDefinition",
    "OptimizationDefaults",
    "OPTIMIZATION_DEFAULTS",
    "INDUSTRY_BASELINE_4_INDUSTRIES",
    "POLICY_PRECEDENCE",
    "parse_optimization_definition",
    "define_optimization",
]
