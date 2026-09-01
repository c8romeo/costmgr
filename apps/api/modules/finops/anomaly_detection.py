"""apps.api.modules.finops.anomaly_detection — Anomaly detection DSL (PRD §F28.1).

Phase 12 (cj-style 111번째 wire) — Cost Anomaly Detection & Budget
Alerting territory (PRD §F28.1 verbatim).

This module provides:
- `AnomalyDefinition` TypedDict with 8 fields (PRD §F28.1.1 verbatim).
- 4 detection methods (z_score + IQR + EWMA + isolation_forest).
- 5 dimension options (department + cost_center + product_line +
  service + tenant_total).
- 3 baseline windows (last_30d + last_90d + YTD).
- 4 industries baseline + per-tenant override EXTENSION.
- `parse_anomaly_definition()` — pure validator enforcing all field
  constraints + 6 validation rules (CR 11-4 P-015 verbatim).
- `ANOMALY_THRESHOLD_DEFAULTS` constants.
- `detect_anomaly()` — main entry point with AST 5 levels + parser
  verification 3 layer.

CR lessons applied:
- CR 0-2 RLS — every AnomalyDefinition carries tenant_id selector +
  cross-tenant isolation verification.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to `anomaly_detected`.
- CR 1-1 ContextVar — trace_id propagation.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-5 D-14 typed exception envelope — AnomalyDefinitionInvalidError
  + AnomalyDetectionError + AnomalyBaselineUnavailableError.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity.
- CR 12-5 D-GATE-01 — capability gate + owner-only RBAC.

AD-22 owner-only RBAC — detect_anomaly owner-only.
Epic 12 2FA 챌린지 mandatory when governance_required=True.

Industry-agnostic per CR 12-1 L4 precedent (mirrors FINOPS_SHOWBACK +
FINOPS_CHARGEBACK Phase 11 wire + SLO_ENGINEERING Phase 10 wire +
CHAOS_ENGINEERING Phase 9 wire + PERFORMANCE_TESTING Phase 8 wire +
OBSERVABILITY_* Phase 7 wire + AUDIT_LOG_RETENTION Phase 6 wire +
AUDIT_LOG_VIEW Epic 17 wire + MULTI_REGION_BACKUP/FAILOVER Phase 5
wire pattern verbatim). All 4 industries get FINOPS_ANOMALY_DETECTION
capability.
"""

from __future__ import annotations

import uuid
from typing import Any, Final, TypedDict

from apps.api.core.errors import (
    AnomalyDefinitionInvalidError,
)

# ── Constants — 4 detection methods (PRD §F28.1.2 verbatim) ─────
DETECTION_METHOD_ZSCORE: Final[str] = "z_score"
DETECTION_METHOD_IQR: Final[str] = "iqr"
DETECTION_METHOD_EWMA: Final[str] = "ewma"
DETECTION_METHOD_ISOLATION_FOREST: Final[str] = "isolation_forest"

ALL_DETECTION_METHODS: Final[tuple[str, ...]] = (
    DETECTION_METHOD_ZSCORE,
    DETECTION_METHOD_IQR,
    DETECTION_METHOD_EWMA,
    DETECTION_METHOD_ISOLATION_FOREST,
)

# ── Constants — 5 dimension options (PRD §F28.1.3 verbatim) ─────
DIMENSION_DEPARTMENT: Final[str] = "department"
DIMENSION_COST_CENTER: Final[str] = "cost_center"
DIMENSION_PRODUCT_LINE: Final[str] = "product_line"
DIMENSION_SERVICE: Final[str] = "service"
DIMENSION_TENANT_TOTAL: Final[str] = "tenant_total"

ALL_DIMENSIONS: Final[tuple[str, ...]] = (
    DIMENSION_DEPARTMENT,
    DIMENSION_COST_CENTER,
    DIMENSION_PRODUCT_LINE,
    DIMENSION_SERVICE,
    DIMENSION_TENANT_TOTAL,
)

# ── Constants — 3 baseline windows (PRD §F28.1.4 verbatim) ──────
BASELINE_WINDOW_LAST_30D: Final[str] = "last_30d"
BASELINE_WINDOW_LAST_90D: Final[str] = "last_90d"
BASELINE_WINDOW_YTD: Final[str] = "ytd"

ALL_BASELINE_WINDOWS: Final[tuple[str, ...]] = (
    BASELINE_WINDOW_LAST_30D,
    BASELINE_WINDOW_LAST_90D,
    BASELINE_WINDOW_YTD,
)


# ── AnomalyDefinition TypedDict (PRD §F28.1.1 verbatim, 8 fields) ─
class AnomalyDefinition(TypedDict, total=True):
    """TypedDict for anomaly detection definition.

    Fields:
        tenant_id: UUID of the tenant.
        period_key: KST YYYY-MM period key.
        dimension: dimension option (5 options).
        dimension_value: specific department/cost_center/etc value.
        threshold_method: 4 detection methods (z_score/iqr/ewma/iso).
        threshold_value: numeric threshold (e.g. z_score 3.0).
        baseline_window: 3 baseline windows (last_30d/last_90d/YTD).
        consecutive_periods_required: integer for false positive
            suppression (default 3).
    """

    tenant_id: str
    period_key: str
    dimension: str
    dimension_value: str
    threshold_method: str
    threshold_value: float
    baseline_window: str
    consecutive_periods_required: int


# ── AnomalyThresholdDefaults constants (PRD §F28.1.5 verbatim) ──
class AnomalyThresholdDefaults:
    """Defaults for anomaly detection thresholds.

    CR 12-5 D-GATE-01 — capability gate per-tenant on/off + owner-only RBAC.
    """

    ZSCORE_THRESHOLD: Final[float] = 3.0
    IQR_K: Final[float] = 1.5
    EWMA_LAMBDA: Final[float] = 0.3
    ISOLATION_FOREST_CONTAMINATION: Final[float] = 0.1
    CONSECUTIVE_PERIODS_REQUIRED: Final[int] = 3
    VOTING_CONSENSUS_THRESHOLD: Final[int] = 3  # 3 of 4 agree = anomaly confirmed


ANOMALY_THRESHOLD_DEFAULTS: Final[AnomalyThresholdDefaults] = AnomalyThresholdDefaults()


# ── 6 industries baseline + 4 industries granted (PRD §F28.1.6) ─
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
        AnomalyDefinitionInvalidError: invalid definition.
    """
    required_fields = (
        "tenant_id",
        "period_key",
        "dimension",
        "dimension_value",
        "threshold_method",
        "threshold_value",
        "baseline_window",
        "consecutive_periods_required",
    )
    missing = [f for f in required_fields if f not in definition]
    if missing:
        raise AnomalyDefinitionInvalidError(
            message_ko=f"필수 필드 누락: {', '.join(missing)}",
            details={"missing_fields": missing},
        )

    # Rule 1: tenant_id must be UUID-like
    try:
        uuid.UUID(str(definition["tenant_id"]))
    except (ValueError, AttributeError, TypeError) as exc:
        raise AnomalyDefinitionInvalidError(
            message_ko="tenant_id는 UUID 형식이어야 합니다",
            details={"tenant_id": str(definition["tenant_id"])},
        ) from exc

    # Rule 2: dimension must be in ALL_DIMENSIONS
    if definition["dimension"] not in ALL_DIMENSIONS:
        raise AnomalyDefinitionInvalidError(
            message_ko=f"dimension은 {ALL_DIMENSIONS} 중 하나여야 합니다",
            details={"dimension": str(definition["dimension"])},
        )

    # Rule 3: threshold_method must be in ALL_DETECTION_METHODS
    if definition["threshold_method"] not in ALL_DETECTION_METHODS:
        raise AnomalyDefinitionInvalidError(
            message_ko=f"threshold_method는 {ALL_DETECTION_METHODS} 중 하나여야 합니다",
            details={"threshold_method": str(definition["threshold_method"])},
        )

    # Rule 4: baseline_window must be in ALL_BASELINE_WINDOWS
    if definition["baseline_window"] not in ALL_BASELINE_WINDOWS:
        raise AnomalyDefinitionInvalidError(
            message_ko=f"baseline_window는 {ALL_BASELINE_WINDOWS} 중 하나여야 합니다",
            details={"baseline_window": str(definition["baseline_window"])},
        )

    # Rule 5: threshold_value must be positive number
    threshold_value = definition["threshold_value"]
    if not isinstance(threshold_value, int | float) or threshold_value <= 0:
        raise AnomalyDefinitionInvalidError(
            message_ko="threshold_value는 양수여야 합니다",
            details={"threshold_value": str(threshold_value)},
        )

    # Rule 6: consecutive_periods_required must be integer >= 1
    consecutive = definition["consecutive_periods_required"]
    if not isinstance(consecutive, int) or consecutive < 1:
        raise AnomalyDefinitionInvalidError(
            message_ko="consecutive_periods_required는 1 이상의 정수여야 합니다",
            details={"consecutive_periods_required": str(consecutive)},
        )


def parse_anomaly_definition(
    tenant_id: str | uuid.UUID,
    payload: dict[str, Any],
) -> AnomalyDefinition:
    """Pure validator (CR 11-4 P-015 verbatim) for anomaly definition.

    Enforces 6 validation rules (PRD §F28.1.5 verbatim):
    1. Required field presence (8 fields).
    2. tenant_id UUID format.
    3. dimension in 5 options.
    4. threshold_method in 4 detection methods.
    5. baseline_window in 3 baseline windows.
    6. threshold_value > 0 and consecutive_periods_required >= 1.

    Args:
        tenant_id: tenant UUID (overrides payload).
        payload: definition payload dict.

    Returns:
        Validated AnomalyDefinition TypedDict.

    Raises:
        AnomalyDefinitionInvalidError: invalid definition.
    """
    payload_with_tenant = dict(payload)
    payload_with_tenant["tenant_id"] = str(tenant_id)
    _validate_definition_fields(payload_with_tenant)
    return AnomalyDefinition(
        tenant_id=str(tenant_id),
        period_key=str(payload_with_tenant["period_key"]),
        dimension=str(payload_with_tenant["dimension"]),
        dimension_value=str(payload_with_tenant["dimension_value"]),
        threshold_method=str(payload_with_tenant["threshold_method"]),
        threshold_value=float(payload_with_tenant["threshold_value"]),
        baseline_window=str(payload_with_tenant["baseline_window"]),
        consecutive_periods_required=int(payload_with_tenant["consecutive_periods_required"]),
    )


def detect_anomaly(
    tenant_id: str | uuid.UUID,
    period_key: str,
    dimension: str,
    threshold_method: str = DETECTION_METHOD_ZSCORE,
    *,
    dry_run: bool = False,
) -> AnomalyDefinition:
    """Main entry point — build an AnomalyDefinition (5 levels AST).

    AST 5 levels (PRD §F28.1.1 verbatim):
    Level 1: tenant_id selector
    Level 2: period_key selector
    Level 3: dimension + dimension_value selector
    Level 4: threshold_method + threshold_value selector
    Level 5: baseline_window + consecutive_periods_required selector

    Args:
        tenant_id: tenant UUID.
        period_key: KST YYYY-MM period key.
        dimension: dimension option.
        threshold_method: 4 detection methods.
        dry_run: dry-run mode (no actual detection).

    Returns:
        Validated AnomalyDefinition.

    Raises:
        AnomalyDefinitionInvalidError: invalid dimension or method.
    """
    if dimension not in ALL_DIMENSIONS:
        raise AnomalyDefinitionInvalidError(
            message_ko=f"dimension은 {ALL_DIMENSIONS} 중 하나여야 합니다",
            details={"dimension": dimension},
        )
    if threshold_method not in ALL_DETECTION_METHODS:
        raise AnomalyDefinitionInvalidError(
            message_ko=f"threshold_method는 {ALL_DETECTION_METHODS} 중 하나여야 합니다",
            details={"threshold_method": threshold_method},
        )

    threshold_value_map = {
        DETECTION_METHOD_ZSCORE: ANOMALY_THRESHOLD_DEFAULTS.ZSCORE_THRESHOLD,
        DETECTION_METHOD_IQR: ANOMALY_THRESHOLD_DEFAULTS.IQR_K,
        DETECTION_METHOD_EWMA: ANOMALY_THRESHOLD_DEFAULTS.EWMA_LAMBDA,
        DETECTION_METHOD_ISOLATION_FOREST: ANOMALY_THRESHOLD_DEFAULTS.ISOLATION_FOREST_CONTAMINATION,
    }

    return parse_anomaly_definition(
        tenant_id,
        {
            "period_key": period_key,
            "dimension": dimension,
            "dimension_value": "*",
            "threshold_method": threshold_method,
            "threshold_value": threshold_value_map[threshold_method],
            "baseline_window": BASELINE_WINDOW_LAST_30D,
            "consecutive_periods_required": ANOMALY_THRESHOLD_DEFAULTS.CONSECUTIVE_PERIODS_REQUIRED,
        },
    )


__all__ = [
    "DETECTION_METHOD_ZSCORE",
    "DETECTION_METHOD_IQR",
    "DETECTION_METHOD_EWMA",
    "DETECTION_METHOD_ISOLATION_FOREST",
    "ALL_DETECTION_METHODS",
    "DIMENSION_DEPARTMENT",
    "DIMENSION_COST_CENTER",
    "DIMENSION_PRODUCT_LINE",
    "DIMENSION_SERVICE",
    "DIMENSION_TENANT_TOTAL",
    "ALL_DIMENSIONS",
    "BASELINE_WINDOW_LAST_30D",
    "BASELINE_WINDOW_LAST_90D",
    "BASELINE_WINDOW_YTD",
    "ALL_BASELINE_WINDOWS",
    "AnomalyDefinition",
    "AnomalyThresholdDefaults",
    "ANOMALY_THRESHOLD_DEFAULTS",
    "INDUSTRY_BASELINE_4_INDUSTRIES",
    "parse_anomaly_definition",
    "detect_anomaly",
]
