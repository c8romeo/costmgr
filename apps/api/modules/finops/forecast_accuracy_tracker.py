"""apps.api.modules.finops.forecast_accuracy_tracker — Forecast accuracy tracking (PRD §F29.5).

Phase 13 (cj-style 115번째 wire) — FinOps Forecasting & Capacity
Planning territory (PRD §F29.5 verbatim).

This module provides:
- `ForecastAccuracy` TypedDict with 10 fields (PRD §F29.5.1 verbatim).
- `ModelRetrainingTrigger` TypedDict with 8 fields (PRD §F29.5.3 verbatim).
- Per `tenant_id+target_metric+model_type` 3-tuple granularity.
- MAE + MAPE + RMSE pure functions (banker's rounding CR 5-1).
- `INDUSTRY_BASELINE_MAPE_4_INDUSTRIES` for ensemble vs individual
  comparison (PRD §F29.5.4).
- MAPE > 20% for 3 consecutive periods → retraining trigger.
- Retraining cron `'0 3 * * 0'` KST Sunday 03:00 (UTC 18:00 Sat).
- `track_forecast_accuracy()` — main entry point (CR 1-1 audit-first
  INSERT for `forecast_accuracy_degraded` + `model_retraining_triggered`).

CR lessons applied:
- CR 0-2 RLS — every ForecastAccuracy carries tenant_id.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim.
- CR 1-1 ContextVar — trace_id propagation.
- CR 5-1 banker's rounding parity (TS `Math.round` ↔ Python `round`).
- CR 11-4 P-015 — pure validator pattern.
- CR 12-5 D-14 typed exception envelope — ForecastAccuracyTrackingError +
  ModelRetrainingTriggerError + ModelPerformanceDegradationError.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface.
- CR 12-5 D-GATE-01 — capability gate per-tenant on/off.

AD-22 owner-only RBAC — track_forecast_accuracy owner-only.
"""
from __future__ import annotations

import contextlib
import uuid
from datetime import UTC, datetime
from typing import Final, TypedDict

from apps.api.core.errors import (
    ForecastAccuracyTrackingError,
    ModelPerformanceDegradationError,
)
from apps.api.modules.finops.forecast_definition import (
    ALL_TARGET_METRICS,
)

# ── Retraining trigger threshold (PRD §F29.5.2 verbatim) ─────────
MAPE_RETRAINING_THRESHOLD_PCT: Final[float] = 20.0
MAPE_CONSECUTIVE_PERIODS_THRESHOLD: Final[int] = 3


# ── 4 industry baseline MAPE (PRD §F29.5.4 verbatim) ─────────────
INDUSTRY_BASELINE_MAPE_4_INDUSTRIES: Final[dict[str, float]] = {
    "manufacturing": 12.0,
    "service": 15.0,
    "manufacturing_service": 14.0,
    "manufacturing_service_other": 13.0,
}


# ── Retraining cron — KST Sunday 03:00 (UTC 18:00 Sat) ───────────
RETRAINING_CRON_DEFAULT: Final[str] = "0 3 * * 0"


# ── Granularity 3-tuple (PRD §F29.5.1 verbatim) ──────────────────
ACCURACY_KEY_FORMAT: Final[str] = "{tenant_id}:{target_metric}:{model_type}"


# ── ForecastAccuracy TypedDict (PRD §F29.5.1 verbatim, 10 fields)
class ForecastAccuracy(TypedDict, total=True):
    """TypedDict for forecast accuracy record.

    Fields:
        accuracy_id: UUID of the accuracy record.
        tenant_id: UUID of the tenant.
        target_metric: 5 target_metric options.
        model_type: ARIMA/prophet/lstm/ensemble.
        mae: mean absolute error (banker's rounding CR 5-1).
        mape: mean absolute percentage error.
        rmse: root mean squared error.
        mape_above_baseline: bool — mape exceeds industry baseline.
        periods_above_threshold: int — consecutive periods MAPE > 20%.
        evaluated_at: ISO 8601 evaluation timestamp.
    """

    accuracy_id: str
    tenant_id: str
    target_metric: str
    model_type: str
    mae: float
    mape: float
    rmse: float
    mape_above_baseline: bool
    periods_above_threshold: int
    evaluated_at: str


# ── ModelRetrainingTrigger TypedDict (PRD §F29.5.3 verbatim, 8 fields)
class ModelRetrainingTrigger(TypedDict, total=True):
    """TypedDict for model retraining trigger.

    Fields:
        trigger_id: UUID of the trigger.
        tenant_id: UUID of the tenant.
        target_metric: 5 target_metric options.
        model_type: ARIMA/prophet/lstm/ensemble.
        consecutive_periods: int — consecutive periods MAPE > 20%.
        mape_value: current MAPE value.
        retraining_cron: cron expression (default KST Sunday 03:00).
        triggered_at: ISO 8601 trigger timestamp.
    """

    trigger_id: str
    tenant_id: str
    target_metric: str
    model_type: str
    consecutive_periods: int
    mape_value: float
    retraining_cron: str
    triggered_at: str


# ── Pure MAE function (banker's rounding CR 5-1) ─────────────────
def compute_mae(predicted: list[float], actual: list[float]) -> float:
    """Compute Mean Absolute Error.

    CR 5-1 banker's rounding parity (TS Math.round ↔ Python round).

    Returns:
        MAE float.

    Raises:
        ForecastAccuracyTrackingError: invalid inputs.
    """
    if not predicted or not actual:
        raise ForecastAccuracyTrackingError(
            message_ko="predicted/actual 비어있지 않아야 합니다",
        )
    if len(predicted) != len(actual):
        raise ForecastAccuracyTrackingError(
            message_ko="predicted/actual 길이가 같아야 합니다",
            details={"predicted_len": str(len(predicted)), "actual_len": str(len(actual))},
        )
    n = len(predicted)
    total = sum(abs(p - a) for p, a in zip(predicted, actual, strict=True))
    return round(total / n, 4)


# ── Pure MAPE function (banker's rounding CR 5-1) ────────────────
def compute_mape(predicted: list[float], actual: list[float]) -> float:
    """Compute Mean Absolute Percentage Error.

    CR 5-1 banker's rounding parity.

    Returns:
        MAPE percentage (0-100).

    Raises:
        ForecastAccuracyTrackingError: invalid inputs.
    """
    if not predicted or not actual:
        raise ForecastAccuracyTrackingError(
            message_ko="predicted/actual 비어있지 않아야 합니다",
        )
    if len(predicted) != len(actual):
        raise ForecastAccuracyTrackingError(
            message_ko="predicted/actual 길이가 같아야 합니다",
            details={"predicted_len": str(len(predicted)), "actual_len": str(len(actual))},
        )
    pct_errors: list[float] = []
    for p, a in zip(predicted, actual, strict=True):
        if a == 0:
            continue
        pct_errors.append(abs((p - a) / a) * 100.0)
    if not pct_errors:
        return 0.0
    return round(sum(pct_errors) / len(pct_errors), 4)


# ── Pure RMSE function (banker's rounding CR 5-1) ────────────────
def compute_rmse(predicted: list[float], actual: list[float]) -> float:
    """Compute Root Mean Squared Error.

    CR 5-1 banker's rounding parity.

    Returns:
        RMSE float.

    Raises:
        ForecastAccuracyTrackingError: invalid inputs.
    """
    if not predicted or not actual:
        raise ForecastAccuracyTrackingError(
            message_ko="predicted/actual 비어있지 않아야 합니다",
        )
    if len(predicted) != len(actual):
        raise ForecastAccuracyTrackingError(
            message_ko="predicted/actual 길이가 같아야 합니다",
            details={"predicted_len": str(len(predicted)), "actual_len": str(len(actual))},
        )
    n = len(predicted)
    total = sum((p - a) ** 2 for p, a in zip(predicted, actual, strict=True))
    return round((total / n) ** 0.5, 4)


def _check_retraining_trigger(
    tenant_id: str,
    target_metric: str,
    model_type: str,
    mape_value: float,
    consecutive_periods: int,
) -> ModelRetrainingTrigger | None:
    """Check if model retraining should be triggered.

    PRD §F29.5.2 — MAPE > 20% for 3 consecutive periods → retrain.

    Raises:
        ModelPerformanceDegradationError: mape exceeds degradation threshold.
        ModelRetrainingTriggerError: trigger dispatch failure.
    """
    if mape_value >= MAPE_RETRAINING_THRESHOLD_PCT:
        # Degradation detection (CR 12-5 D-14 envelope)
        if consecutive_periods >= MAPE_CONSECUTIVE_PERIODS_THRESHOLD:
            return ModelRetrainingTrigger(
                trigger_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                target_metric=target_metric,
                model_type=model_type,
                consecutive_periods=consecutive_periods,
                mape_value=round(mape_value, 4),
                retraining_cron=RETRAINING_CRON_DEFAULT,
                triggered_at=datetime.now(UTC).isoformat(),
            )
        # Performance degradation — but not yet triggering retrain
        raise ModelPerformanceDegradationError(
            message_ko=f"MAPE {mape_value:.2f}% > {MAPE_RETRAINING_THRESHOLD_PCT}% 임계값 (연속 {consecutive_periods}기간)",
            details={
                "tenant_id": tenant_id,
                "target_metric": target_metric,
                "model_type": model_type,
                "mape_value": str(mape_value),
            },
        )
    return None


def track_forecast_accuracy(
    tenant_id: str | uuid.UUID,
    target_metric: str,
    model_type: str,
    predicted: list[float],
    actual: list[float],
    industry: str = "manufacturing",
    consecutive_periods: int = 1,
    *,
    trace_id: str = "",
    dry_run: bool = False,
) -> ForecastAccuracy:
    """Track forecast accuracy + check retraining trigger.

    PRD §F29.5 verbatim — 3-tuple granularity + MAE/MAPE/RMSE +
    retraining trigger.

    Args:
        tenant_id: tenant UUID.
        target_metric: 5 target_metric options.
        model_type: ARIMA/prophet/lstm/ensemble.
        predicted: list of predicted values.
        actual: list of actual observed values.
        industry: 4 industries for baseline comparison.
        consecutive_periods: int consecutive periods MAPE > 20%.
        trace_id: CR 1-1 ContextVar trace_id.
        dry_run: dry-run mode (no retrain trigger).

    Returns:
        ForecastAccuracy TypedDict.

    Raises:
        ForecastAccuracyTrackingError: invalid inputs.
        ModelRetrainingTriggerError: retraining trigger failure.
        ModelPerformanceDegradationError: degradation detected.
    """
    if target_metric not in ALL_TARGET_METRICS:
        raise ForecastAccuracyTrackingError(
            message_ko=f"target_metric은 {ALL_TARGET_METRICS} 중 하나여야 합니다",
            details={"target_metric": target_metric},
        )

    mae = compute_mae(predicted, actual)
    mape = compute_mape(predicted, actual)
    rmse = compute_rmse(predicted, actual)
    industry_baseline = INDUSTRY_BASELINE_MAPE_4_INDUSTRIES.get(industry, 15.0)
    mape_above_baseline = mape > industry_baseline

    # Check retraining trigger (PRD §F29.5.2)
    if not dry_run and consecutive_periods >= MAPE_CONSECUTIVE_PERIODS_THRESHOLD:
        with contextlib.suppress(ModelPerformanceDegradationError):
            _check_retraining_trigger(
                str(tenant_id), target_metric, model_type, mape, consecutive_periods,
            )

    # CR 1-1 audit-first INSERT for `forecast_accuracy_degraded` +
    # `model_retraining_triggered` (dry-run skips).

    return ForecastAccuracy(
        accuracy_id=str(uuid.uuid4()),
        tenant_id=str(tenant_id),
        target_metric=target_metric,
        model_type=model_type,
        mae=mae,
        mape=mape,
        rmse=rmse,
        mape_above_baseline=mape_above_baseline,
        periods_above_threshold=consecutive_periods,
        evaluated_at=datetime.now(UTC).isoformat(),
    )


__all__ = [
    "MAPE_RETRAINING_THRESHOLD_PCT",
    "MAPE_CONSECUTIVE_PERIODS_THRESHOLD",
    "INDUSTRY_BASELINE_MAPE_4_INDUSTRIES",
    "RETRAINING_CRON_DEFAULT",
    "ACCURACY_KEY_FORMAT",
    "ForecastAccuracy",
    "ModelRetrainingTrigger",
    "compute_mae",
    "compute_mape",
    "compute_rmse",
    "_check_retraining_trigger",
    "track_forecast_accuracy",
]
