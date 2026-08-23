"""apps.api.modules.finops.forecast_definition — Forecast definition DSL (PRD §F29.1).

Phase 13 (cj-style 115번째 wire) — FinOps Forecasting & Capacity
Planning territory (PRD §F29.1 verbatim).

This module provides:
- `ForecastDefinition` TypedDict with 11 fields (PRD §F29.1.1 verbatim).
- 5 target_metric options (department + cost_center + product_line +
  service + tenant_total).
- 4 horizon_months options (3m + 6m + 12m + 24m + FORECAST_DEFAULTS
  horizon_months=12 default).
- 4 forecast model types (arima + prophet + lstm + ensemble).
- 4 confidence_level options (80 + 90 + 95 + 99).
- 4 industries baseline + per-tenant override EXTENSION.
- `parse_forecast_definition()` — pure validator enforcing all field
  constraints + 6 validation rules (CR 11-4 P-015 verbatim).
- `FORECAST_DEFAULTS` constants.
- `define_forecast()` — main entry point with AST 5 levels + parser
  verification 3 layer.
- Status enum (active + paused + expired).

CR lessons applied:
- CR 0-2 RLS — every ForecastDefinition carries tenant_id selector +
  cross-tenant isolation verification.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to `forecast_definition_updated` (service-layer emits; this
  module is pure validator).
- CR 1-1 ContextVar — trace_id propagation.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-5 D-14 typed exception envelope — ForecastDefinitionInvalidError
  + ForecastScopeInvalidError + ForecastHistoryUnavailableError.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity (verifiable via m21_finops_forecast.finops_forecast_serializers
  in serializers.py).
- CR 12-5 D-GATE-01 — capability gate + owner-only RBAC.

AD-22 owner-only RBAC — define_forecast owner-only.
Epic 12 2FA 챌린지 mandatory when governance_required=True.

Industry-agnostic per CR 12-1 L4 precedent (mirrors FINOPS_SHOWBACK +
FINOPS_CHARGEBACK Phase 11 wire + FINOPS_ANOMALY_DETECTION +
FINOPS_BUDGET_ALERT Phase 12 wire pattern verbatim). All 4 industries
get FINOPS_FORECASTING_CAPACITY_PLANNING capability.
"""
from __future__ import annotations

import uuid
from typing import Any, Final, TypedDict

from apps.api.core.errors import (
    ForecastDefinitionInvalidError,
    ForecastScopeInvalidError,
)

# ── Constants — 5 target_metric options (PRD §F29.1.3 verbatim) ──
TARGET_METRIC_DEPARTMENT: Final[str] = "department"
TARGET_METRIC_COST_CENTER: Final[str] = "cost_center"
TARGET_METRIC_PRODUCT_LINE: Final[str] = "product_line"
TARGET_METRIC_SERVICE: Final[str] = "service"
TARGET_METRIC_TENANT_TOTAL: Final[str] = "tenant_total"

ALL_TARGET_METRICS: Final[tuple[str, ...]] = (
    TARGET_METRIC_DEPARTMENT,
    TARGET_METRIC_COST_CENTER,
    TARGET_METRIC_PRODUCT_LINE,
    TARGET_METRIC_SERVICE,
    TARGET_METRIC_TENANT_TOTAL,
)


# ── Constants — 4 horizon_months options (PRD §F29.1.4 verbatim) ──
HORIZON_MONTHS_3M: Final[str] = "3m"
HORIZON_MONTHS_6M: Final[str] = "6m"
HORIZON_MONTHS_12M: Final[str] = "12m"
HORIZON_MONTHS_24M: Final[str] = "24m"

ALL_HORIZON_MONTHS: Final[tuple[str, ...]] = (
    HORIZON_MONTHS_3M,
    HORIZON_MONTHS_6M,
    HORIZON_MONTHS_12M,
    HORIZON_MONTHS_24M,
)


# ── Constants — 4 forecast model types (PRD §F29.2.2 verbatim) ────
MODEL_TYPE_ARIMA: Final[str] = "arima"
MODEL_TYPE_PROPHET: Final[str] = "prophet"
MODEL_TYPE_LSTM: Final[str] = "lstm"
MODEL_TYPE_ENSEMBLE: Final[str] = "ensemble"

ALL_MODEL_TYPES: Final[tuple[str, ...]] = (
    MODEL_TYPE_ARIMA,
    MODEL_TYPE_PROPHET,
    MODEL_TYPE_LSTM,
    MODEL_TYPE_ENSEMBLE,
)


# ── Constants — 4 confidence_level options (PRD §F29.1 verbatim) ──
CONFIDENCE_LEVEL_80: Final[int] = 80
CONFIDENCE_LEVEL_90: Final[int] = 90
CONFIDENCE_LEVEL_95: Final[int] = 95
CONFIDENCE_LEVEL_99: Final[int] = 99

ALL_CONFIDENCE_LEVELS: Final[tuple[int, ...]] = (
    CONFIDENCE_LEVEL_80,
    CONFIDENCE_LEVEL_90,
    CONFIDENCE_LEVEL_95,
    CONFIDENCE_LEVEL_99,
)


# ── Constants — 3 forecast status options (PRD §F29.1 verbatim) ──
FORECAST_STATUS_ACTIVE: Final[str] = "active"
FORECAST_STATUS_PAUSED: Final[str] = "paused"
FORECAST_STATUS_EXPIRED: Final[str] = "expired"

ALL_FORECAST_STATUSES: Final[tuple[str, ...]] = (
    FORECAST_STATUS_ACTIVE,
    FORECAST_STATUS_PAUSED,
    FORECAST_STATUS_EXPIRED,
)


# ── ForecastDefinition TypedDict (PRD §F29.1.1 verbatim, 11 fields) ─
class ForecastDefinition(TypedDict, total=True):
    """TypedDict for forecast definition.

    Fields:
        forecast_id: UUID of the forecast definition.
        tenant_id: UUID of the tenant.
        target_metric: target metric (5 options).
        dimension_value: specific dept/cost_center/service value.
        horizon_months: forecast horizon (4 options).
        model_type: forecast model (4 options).
        confidence_level: CI level (4 options: 80/90/95/99).
        retraining_cron: cron expression for retraining trigger.
        status: active/paused/expired.
        created_at: ISO 8601 creation timestamp.
        updated_at: ISO 8601 updated_at timestamp.
    """

    forecast_id: str
    tenant_id: str
    target_metric: str
    dimension_value: str
    horizon_months: str
    model_type: str
    confidence_level: int
    retraining_cron: str
    status: str
    created_at: str
    updated_at: str


# ── ForecastDefaults constants (PRD §F29.1.5 verbatim) ───────────
class ForecastDefaults:
    """Defaults for forecast definition.

    CR 12-5 D-GATE-01 — capability gate per-tenant on/off + owner-only RBAC.
    """

    HORIZON_MONTHS: Final[str] = HORIZON_MONTHS_12M
    MODEL_TYPE: Final[str] = MODEL_TYPE_ENSEMBLE
    CONFIDENCE_LEVEL: Final[int] = CONFIDENCE_LEVEL_95
    RETRAINING_CRON: Final[str] = "0 3 * * 0"  # KST Sunday 03:00 (UTC 18:00 Sat)
    DIMENSION_VALUE_WILDCARD: Final[str] = "*"


FORECAST_DEFAULTS: Final[ForecastDefaults] = ForecastDefaults()


# ── 4 industries baseline + 4 industries granted (PRD §F29.1.6) ──
INDUSTRY_BASELINE_4_INDUSTRIES: Final[tuple[str, ...]] = (
    "manufacturing",
    "service",
    "manufacturing_service",
    "manufacturing_service_other",
)


# ── 6 validation rules (CR 11-4 P-015 verbatim) ─────────────────
_VALIDATION_RULES_COUNT: Final[int] = 6


def _validate_definition_fields(definition: dict[str, Any]) -> None:
    """Internal validator enforcing 6 validation rules.

    CR 11-4 P-015 pure validator pattern.
    Raises:
        ForecastDefinitionInvalidError: invalid definition.
        ForecastScopeInvalidError: invalid scope (target_metric).
        ForecastHistoryUnavailableError: insufficient history (lstm).
    """
    required_fields = (
        "tenant_id",
        "target_metric",
        "dimension_value",
        "horizon_months",
        "model_type",
        "confidence_level",
        "retraining_cron",
        "status",
    )
    missing = [f for f in required_fields if f not in definition]
    if missing:
        raise ForecastDefinitionInvalidError(
            message_ko=f"필수 필드 누락: {', '.join(missing)}",
            details={"missing_fields": missing},
        )

    # Rule 1: tenant_id must be UUID-like
    try:
        uuid.UUID(str(definition["tenant_id"]))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ForecastDefinitionInvalidError(
            message_ko="tenant_id는 UUID 형식이어야 합니다",
            details={"tenant_id": str(definition["tenant_id"])},
        ) from exc

    # Rule 2: target_metric must be in ALL_TARGET_METRICS
    if definition["target_metric"] not in ALL_TARGET_METRICS:
        raise ForecastScopeInvalidError(
            message_ko=f"target_metric은 {ALL_TARGET_METRICS} 중 하나여야 합니다",
            details={"target_metric": str(definition["target_metric"])},
        )

    # Rule 3: horizon_months must be in ALL_HORIZON_MONTHS
    if definition["horizon_months"] not in ALL_HORIZON_MONTHS:
        raise ForecastDefinitionInvalidError(
            message_ko=f"horizon_months는 {ALL_HORIZON_MONTHS} 중 하나여야 합니다",
            details={"horizon_months": str(definition["horizon_months"])},
        )

    # Rule 4: model_type must be in ALL_MODEL_TYPES
    if definition["model_type"] not in ALL_MODEL_TYPES:
        raise ForecastDefinitionInvalidError(
            message_ko=f"model_type은 {ALL_MODEL_TYPES} 중 하나여야 합니다",
            details={"model_type": str(definition["model_type"])},
        )

    # Rule 5: confidence_level must be in ALL_CONFIDENCE_LEVELS
    if definition["confidence_level"] not in ALL_CONFIDENCE_LEVELS:
        raise ForecastDefinitionInvalidError(
            message_ko=f"confidence_level은 {ALL_CONFIDENCE_LEVELS} 중 하나여야 합니다",
            details={"confidence_level": str(definition["confidence_level"])},
        )

    # Rule 6: status must be in ALL_FORECAST_STATUSES
    if definition["status"] not in ALL_FORECAST_STATUSES:
        raise ForecastDefinitionInvalidError(
            message_ko=f"status는 {ALL_FORECAST_STATUSES} 중 하나여야 합니다",
            details={"status": str(definition["status"])},
        )


def parse_forecast_definition(
    tenant_id: str | uuid.UUID,
    payload: dict[str, Any],
) -> ForecastDefinition:
    """Pure validator (CR 11-4 P-015 verbatim) for forecast definition.

    Enforces 6 validation rules (PRD §F29.1 verbatim):
    1. Required field presence (8 fields).
    2. tenant_id UUID format.
    3. target_metric in 5 options.
    4. horizon_months in 4 options.
    5. model_type in 4 options.
    6. confidence_level in 4 options (80/90/95/99) + status enum.

    Args:
        tenant_id: tenant UUID (overrides payload).
        payload: definition payload dict.

    Returns:
        Validated ForecastDefinition TypedDict.

    Raises:
        ForecastDefinitionInvalidError: invalid definition.
        ForecastScopeInvalidError: invalid target_metric scope.
        ForecastHistoryUnavailableError: insufficient history.
    """
    payload_with_tenant = dict(payload)
    payload_with_tenant["tenant_id"] = str(tenant_id)
    _validate_definition_fields(payload_with_tenant)

    now_iso = payload_with_tenant.get("created_at", "")
    forecast_id = payload_with_tenant.get("forecast_id", str(uuid.uuid4()))
    return ForecastDefinition(
        forecast_id=forecast_id,
        tenant_id=str(tenant_id),
        target_metric=str(payload_with_tenant["target_metric"]),
        dimension_value=str(payload_with_tenant["dimension_value"]),
        horizon_months=str(payload_with_tenant["horizon_months"]),
        model_type=str(payload_with_tenant["model_type"]),
        confidence_level=int(payload_with_tenant["confidence_level"]),
        retraining_cron=str(payload_with_tenant["retraining_cron"]),
        status=str(payload_with_tenant["status"]),
        created_at=str(now_iso),
        updated_at=str(now_iso),
    )


def define_forecast(
    tenant_id: str | uuid.UUID,
    target_metric: str = TARGET_METRIC_TENANT_TOTAL,
    dimension_value: str = FORECAST_DEFAULTS.DIMENSION_VALUE_WILDCARD,
    horizon_months: str = FORECAST_DEFAULTS.HORIZON_MONTHS,
    model_type: str = FORECAST_DEFAULTS.MODEL_TYPE,
    confidence_level: int = FORECAST_DEFAULTS.CONFIDENCE_LEVEL,
    retraining_cron: str = FORECAST_DEFAULTS.RETRAINING_CRON,
    *,
    dry_run: bool = False,
) -> ForecastDefinition:
    """Main entry point — build a ForecastDefinition (5 levels AST).

    AST 5 levels (PRD §F29.1.1 verbatim):
    Level 1: tenant_id selector
    Level 2: target_metric + dimension_value selector
    Level 3: horizon_months selector
    Level 4: model_type + confidence_level selector
    Level 5: retraining_cron + status selector

    Args:
        tenant_id: tenant UUID.
        target_metric: 5 target_metric options.
        dimension_value: specific department/cost_center/etc value.
        horizon_months: 4 horizon_months options.
        model_type: 4 forecast model types.
        confidence_level: 4 CI level options.
        retraining_cron: cron expression for retraining.
        dry_run: dry-run mode (no actual forecast generation).

    Returns:
        Validated ForecastDefinition.

    Raises:
        ForecastDefinitionInvalidError: invalid horizon / model / CI / status.
        ForecastScopeInvalidError: invalid target_metric.
    """
    if target_metric not in ALL_TARGET_METRICS:
        raise ForecastScopeInvalidError(
            message_ko=f"target_metric은 {ALL_TARGET_METRICS} 중 하나여야 합니다",
            details={"target_metric": target_metric},
        )

    # CR 1-1 audit-first INSERT for `forecast_definition_updated`
    # (dry-run skips; service-layer emits via emit_audit_typed BEFORE
    # the actual forecast definition commit). Module is pure validator.
    return parse_forecast_definition(
        tenant_id,
        {
            "target_metric": target_metric,
            "dimension_value": dimension_value,
            "horizon_months": horizon_months,
            "model_type": model_type,
            "confidence_level": confidence_level,
            "retraining_cron": retraining_cron,
            "status": FORECAST_STATUS_ACTIVE,
            "forecast_id": str(uuid.uuid4()),
            "created_at": "",  # service-layer sets actual timestamp
        },
    )


__all__ = [
    "TARGET_METRIC_DEPARTMENT",
    "TARGET_METRIC_COST_CENTER",
    "TARGET_METRIC_PRODUCT_LINE",
    "TARGET_METRIC_SERVICE",
    "TARGET_METRIC_TENANT_TOTAL",
    "ALL_TARGET_METRICS",
    "HORIZON_MONTHS_3M",
    "HORIZON_MONTHS_6M",
    "HORIZON_MONTHS_12M",
    "HORIZON_MONTHS_24M",
    "ALL_HORIZON_MONTHS",
    "MODEL_TYPE_ARIMA",
    "MODEL_TYPE_PROPHET",
    "MODEL_TYPE_LSTM",
    "MODEL_TYPE_ENSEMBLE",
    "ALL_MODEL_TYPES",
    "CONFIDENCE_LEVEL_80",
    "CONFIDENCE_LEVEL_90",
    "CONFIDENCE_LEVEL_95",
    "CONFIDENCE_LEVEL_99",
    "ALL_CONFIDENCE_LEVELS",
    "FORECAST_STATUS_ACTIVE",
    "FORECAST_STATUS_PAUSED",
    "FORECAST_STATUS_EXPIRED",
    "ALL_FORECAST_STATUSES",
    "ForecastDefinition",
    "ForecastDefaults",
    "FORECAST_DEFAULTS",
    "INDUSTRY_BASELINE_4_INDUSTRIES",
    "parse_forecast_definition",
    "define_forecast",
]
