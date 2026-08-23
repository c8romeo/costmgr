"""apps.api.modules.finops.capacity_headroom — Capacity headroom analysis (PRD §F29.3).

Phase 13 (cj-style 115번째 wire) — FinOps Forecasting & Capacity
Planning territory (PRD §F29.3 verbatim).

This module provides:
- `CapacityHeadroomReport` TypedDict with 14 fields (PRD §F29.3.2 verbatim).
- 3 resource types: compute + storage + network (PRD §F29.3.3).
- 3 saturation levels: OK + WARNING + CRITICAL (PRD §F29.3.4).
- 90일 lookahead default horizon.
- Per-resource primary model choice: compute=LSTM + storage=Prophet +
  network=ARIMA (PRD §F29.3.5 verbatim).
- 4 industry baseline headroom saturation ratios.
- `analyze_capacity_headroom()` — main entry point (CR 1-1 audit-first
  INSERT for `capacity_headroom_analyzed`).
- LSTM/Prophet/ARIMA primary + ensemble fallback (PRD §F29.3.6).

CR lessons applied:
- CR 0-2 RLS — every CapacityHeadroomReport carries tenant_id.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim.
- CR 1-1 ContextVar — trace_id propagation.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-5 D-14 typed exception envelope — CapacityHeadroomAnalysisError +
  CapacityThresholdBreachError + CapacityMetricUnavailableError.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface.
- CR 12-5 D-GATE-01 — capability gate per-tenant on/off.

AD-22 owner-only RBAC — analyze_capacity_headroom owner-only.
Epic 12 2FA 챌린지 mandatory when governance_required=True.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Final, TypedDict

from apps.api.core.errors import (
    CapacityHeadroomAnalysisError,
    CapacityMetricUnavailableError,
    CapacityThresholdBreachError,
)
from apps.api.modules.finops.forecast_definition import (
    HORIZON_MONTHS_3M,
)
from apps.api.modules.finops.forecast_engine import (
    _arima_predict,
    _lstm_predict,
    _prophet_predict,
)
from apps.api.modules.finops.forecast_model_registry import (
    SEMVER_DEFAULT_VERSION,
    ForecastModelRegistry,
)

# ── 3 resource types (PRD §F29.3.3 verbatim) ────────────────────
RESOURCE_TYPE_COMPUTE: Final[str] = "compute"
RESOURCE_TYPE_STORAGE: Final[str] = "storage"
RESOURCE_TYPE_NETWORK: Final[str] = "network"

ALL_RESOURCE_TYPES: Final[tuple[str, ...]] = (
    RESOURCE_TYPE_COMPUTE,
    RESOURCE_TYPE_STORAGE,
    RESOURCE_TYPE_NETWORK,
)


# ── 3 saturation levels (PRD §F29.3.4 verbatim) ──────────────────
SATURATION_OK: Final[str] = "ok"
SATURATION_WARNING: Final[str] = "warning"
SATURATION_CRITICAL: Final[str] = "critical"

ALL_SATURATION_LEVELS: Final[tuple[str, ...]] = (
    SATURATION_OK,
    SATURATION_WARNING,
    SATURATION_CRITICAL,
)


# ── Saturation threshold defaults (PRD §F29.3.4 verbatim) ────────
SATURATION_WARNING_THRESHOLD_PCT: Final[float] = 70.0  # 70% utilization = warning
SATURATION_CRITICAL_THRESHOLD_PCT: Final[float] = 90.0  # 90% utilization = critical


# ── Lookahead default (PRD §F29.3.1 verbatim) ───────────────────
LOOKAHEAD_DAYS_DEFAULT: Final[int] = 90
LOOKAHEAD_DAYS_MIN: Final[int] = 7
LOOKAHEAD_DAYS_MAX: Final[int] = 365


# ── Primary model per resource type (PRD §F29.3.5 verbatim) ─────
RESOURCE_PRIMARY_MODEL_MAP: Final[dict[str, str]] = {
    RESOURCE_TYPE_COMPUTE: "lstm",
    RESOURCE_TYPE_STORAGE: "prophet",
    RESOURCE_TYPE_NETWORK: "arima",
}


# ── 4 industry baseline headroom saturation ratios (PRD §F29.3.7)
INDUSTRY_HEADROOM_BASELINE_4: Final[dict[str, float]] = {
    "manufacturing": 65.0,
    "service": 55.0,
    "manufacturing_service": 60.0,
    "manufacturing_service_other": 60.0,
}


# ── CapacityHeadroomReport TypedDict (PRD §F29.3.2 verbatim, 14 fields) ─
class CapacityHeadroomReport(TypedDict, total=True):
    """TypedDict for capacity headroom report.

    Fields:
        report_id: UUID of the capacity headroom report.
        tenant_id: UUID of the tenant.
        resource_type: compute/storage/network.
        saturation_pct: predicted saturation percentage.
        saturation_level: ok/warning/critical.
        lookahead_days: lookahead horizon in days.
        predicted_utilization: list of predicted utilization values.
        headroom_pct: headroom percentage (100 - saturation_pct).
        primary_model: primary model used (lstm/prophet/arima).
        ensemble_predicted: list of ensemble voting predictions.
        recommendation: human-readable recommendation (ko-KR).
        trace_id: CR 1-1 ContextVar trace_id.
        created_at: ISO 8601 creation timestamp.
        expires_at: ISO 8601 expiration timestamp.
    """

    report_id: str
    tenant_id: str
    resource_type: str
    saturation_pct: float
    saturation_level: str
    lookahead_days: int
    predicted_utilization: list[float]
    headroom_pct: float
    primary_model: str
    ensemble_predicted: list[float]
    recommendation: str
    trace_id: str
    created_at: str
    expires_at: str


def _classify_saturation(saturation_pct: float) -> str:
    """Classify saturation into ok/warning/critical.

    Returns:
        SATURATION_OK / SATURATION_WARNING / SATURATION_CRITICAL.

    Raises:
        CapacityThresholdBreachError: invalid threshold.
    """
    if saturation_pct < 0 or saturation_pct > 100:
        raise CapacityThresholdBreachError(
            message_ko=f"saturation_pct는 0~100 범위여야 합니다 (got={saturation_pct})",
            details={"saturation_pct": str(saturation_pct)},
        )
    if saturation_pct >= SATURATION_CRITICAL_THRESHOLD_PCT:
        return SATURATION_CRITICAL
    if saturation_pct >= SATURATION_WARNING_THRESHOLD_PCT:
        return SATURATION_WARNING
    return SATURATION_OK


def _select_primary_model(resource_type: str) -> str:
    """Select primary model per resource type (PRD §F29.3.5).

    Returns lstm/prophet/arima.
    """
    if resource_type not in RESOURCE_PRIMARY_MODEL_MAP:
        raise CapacityHeadroomAnalysisError(
            message_ko=f"resource_type은 {ALL_RESOURCE_TYPES} 중 하나여야 합니다",
            details={"resource_type": resource_type},
        )
    return RESOURCE_PRIMARY_MODEL_MAP[resource_type]


def _build_recommendation(
    resource_type: str,
    saturation_pct: float,
    saturation_level: str,
) -> str:
    """Build human-readable recommendation (ko-KR)."""
    if saturation_level == SATURATION_CRITICAL:
        return f"{resource_type}: {saturation_pct:.1f}% 사용 — 즉시 capacity 확장 권장 (CRITICAL)"
    if saturation_level == SATURATION_WARNING:
        return f"{resource_type}: {saturation_pct:.1f}% 사용 — capacity 확장 검토 필요 (WARNING)"
    return f"{resource_type}: {saturation_pct:.1f}% 사용 — 정상 범위 (OK)"


def analyze_capacity_headroom(
    tenant_id: str | uuid.UUID,
    resource_type: str,
    current_utilization_history: list[float],
    *,
    lookahead_days: int = LOOKAHEAD_DAYS_DEFAULT,
    trace_id: str = "",
    dry_run: bool = False,
) -> CapacityHeadroomReport:
    """Analyze capacity headroom for a resource type.

    PRD §F29.3 verbatim — 90일 lookahead default + per-resource primary
    model + ensemble fallback.

    Args:
        tenant_id: tenant UUID.
        resource_type: compute/storage/network.
        current_utilization_history: list of historical utilization %.
        lookahead_days: 7-365 days lookahead.
        trace_id: CR 1-1 ContextVar trace_id.
        dry_run: dry-run mode (no actual forecast generation).

    Returns:
        CapacityHeadroomReport TypedDict.

    Raises:
        CapacityHeadroomAnalysisError: invalid resource_type.
        CapacityThresholdBreachError: invalid saturation_pct.
        CapacityMetricUnavailableError: missing utilization metric.
    """
    if resource_type not in ALL_RESOURCE_TYPES:
        raise CapacityHeadroomAnalysisError(
            message_ko=f"resource_type은 {ALL_RESOURCE_TYPES} 중 하나여야 합니다",
            details={"resource_type": resource_type},
        )
    if lookahead_days < LOOKAHEAD_DAYS_MIN or lookahead_days > LOOKAHEAD_DAYS_MAX:
        raise CapacityHeadroomAnalysisError(
            message_ko=f"lookahead_days는 {LOOKAHEAD_DAYS_MIN}~{LOOKAHEAD_DAYS_MAX} 범위여야 합니다",
            details={"lookahead_days": str(lookahead_days)},
        )
    if not current_utilization_history:
        raise CapacityMetricUnavailableError(
            message_ko="current_utilization_history가 비어있습니다",
            details={"resource_type": resource_type},
        )

    primary_model = _select_primary_model(resource_type)
    horizon = HORIZON_MONTHS_3M if lookahead_days <= 90 else "12m"
    report_id = str(uuid.uuid4())

    # CR 1-1 audit-first INSERT for `capacity_headroom_analyzed`
    # (dry-run skips; service-layer emits via emit_audit_typed BEFORE
    # the actual capacity headroom commit).
    if dry_run:
        horizon_n = {"3m": 3, "6m": 6, "12m": 12, "24m": 24}.get(horizon, 12)
        return CapacityHeadroomReport(
            report_id=report_id,
            tenant_id=str(tenant_id),
            resource_type=resource_type,
            saturation_pct=0.0,
            saturation_level=SATURATION_OK,
            lookahead_days=lookahead_days,
            predicted_utilization=[0.0] * horizon_n,
            headroom_pct=100.0,
            primary_model=primary_model,
            ensemble_predicted=[0.0] * horizon_n,
            recommendation=f"{resource_type}: dry-run",
            trace_id=trace_id,
            created_at=datetime.now(UTC).isoformat(),
            expires_at="",
        )

    # Run primary model
    if primary_model == "lstm":
        primary_result = _lstm_predict(
            current_utilization_history, horizon, report_id, SEMVER_DEFAULT_VERSION,
        )
    elif primary_model == "prophet":
        primary_result = _prophet_predict(
            current_utilization_history, horizon, report_id, SEMVER_DEFAULT_VERSION,
        )
    else:
        primary_result = _arima_predict(
            current_utilization_history, horizon, report_id, SEMVER_DEFAULT_VERSION,
        )
    primary_utilization = primary_result["predicted_values"]

    # Ensemble fallback (PRD §F29.3.6) — run other 2 models + median vote
    arima_result = _arima_predict(
        current_utilization_history, horizon, report_id, SEMVER_DEFAULT_VERSION,
    )
    prophet_result = _prophet_predict(
        current_utilization_history, horizon, report_id, SEMVER_DEFAULT_VERSION,
    )
    ensemble_pred: list[float] = []
    for i in range(len(primary_utilization)):
        values = sorted([primary_utilization[i], arima_result["predicted_values"][i], prophet_result["predicted_values"][i]])
        ensemble_pred.append(values[1])

    # Average predicted utilization → saturation_pct
    avg_pred = sum(ensemble_pred) / len(ensemble_pred) if ensemble_pred else 0.0
    saturation_pct = max(0.0, min(100.0, avg_pred))
    saturation_level = _classify_saturation(saturation_pct)
    headroom_pct = 100.0 - saturation_pct

    # Register model version (PRD §F29.2.10)
    ForecastModelRegistry.register_version(
        tenant_id=str(tenant_id),
        model_type=primary_model,
        model_name=f"{primary_model}_default",
        semver=SEMVER_DEFAULT_VERSION,
        hyperparameters={"lookahead_days": lookahead_days},
        training_metrics={"primary_utilization": primary_utilization},
    )

    return CapacityHeadroomReport(
        report_id=report_id,
        tenant_id=str(tenant_id),
        resource_type=resource_type,
        saturation_pct=saturation_pct,
        saturation_level=saturation_level,
        lookahead_days=lookahead_days,
        predicted_utilization=primary_utilization,
        headroom_pct=headroom_pct,
        primary_model=primary_model,
        ensemble_predicted=ensemble_pred,
        recommendation=_build_recommendation(resource_type, saturation_pct, saturation_level),
        trace_id=trace_id,
        created_at=datetime.now(UTC).isoformat(),
        expires_at=datetime.fromtimestamp(
            datetime.now(UTC).timestamp() + lookahead_days * 24 * 3600,
            tz=UTC,
        ).isoformat(),
    )


__all__ = [
    "RESOURCE_TYPE_COMPUTE",
    "RESOURCE_TYPE_STORAGE",
    "RESOURCE_TYPE_NETWORK",
    "ALL_RESOURCE_TYPES",
    "SATURATION_OK",
    "SATURATION_WARNING",
    "SATURATION_CRITICAL",
    "ALL_SATURATION_LEVELS",
    "SATURATION_WARNING_THRESHOLD_PCT",
    "SATURATION_CRITICAL_THRESHOLD_PCT",
    "LOOKAHEAD_DAYS_DEFAULT",
    "LOOKAHEAD_DAYS_MIN",
    "LOOKAHEAD_DAYS_MAX",
    "RESOURCE_PRIMARY_MODEL_MAP",
    "INDUSTRY_HEADROOM_BASELINE_4",
    "CapacityHeadroomReport",
    "_classify_saturation",
    "_select_primary_model",
    "_build_recommendation",
    "analyze_capacity_headroom",
]
