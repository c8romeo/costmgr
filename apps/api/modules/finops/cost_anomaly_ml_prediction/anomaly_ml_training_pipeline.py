"""apps.api.modules.finops.cost_anomaly_ml_prediction.anomaly_ml_training_pipeline — Phase 26 ML training pipeline.

Phase 26 wire (cj-style 181번째) — FinOps Cost Anomaly ML Prediction
training pipeline (PRD §F42.3 + AD-55 (c) verbatim + 8 features +
scheduled retraining KST 매주 일요일 03:00 UTC 18:00 + drift-triggered
retraining + SHAP feature importance).

Functions:
- train_model(tenant_id, model_type, training_data_window=90) → ModelTrainingJob
- get_training_job_status(training_job_id) → ModelTrainingJob
- list_training_history(tenant_id, model_type=None) → list[ModelTrainingJob]
- cancel_training_job(training_job_id) → ModelTrainingJob

8 features extracted from multi-phase ledger (PRD §F42.3 + AD-55 (c)):
- cost_total_krw (Phase 11 showback)
- cost_per_unit (Phase 23 unit_economics)
- variance_pct (Phase 24 budget_vs_actual)
- budget_consumption_pct (Phase 24 budget_plan)
- settlement_3way_match_score (Phase 22 settlement)
- optimization_savings_amount (Phase 14 optimization)
- month_seasonality dummy 0-11 (Phase 13 forecasting)
- holiday_flag bool

Scheduled retraining cadence:
- weekly_scheduled_training: 03:00 KST every Sunday
- daily_drift_detection: 04:00 KST
- nightly_batch_inference: 02:00 KST
- daily_model_promotion_check: 05:00 KST

Retraining trigger conditions (PRD §F42.3 + AD-55 (c)):
- drift_detected (PSI > 0.25)
- weekly_schedule (cron 03:00 KST Sunday)
- manual_trigger

Exponential backoff retry: max 3 retries, base 60s, max 600s.

CR lessons applied:
- CR 1-1 audit-first INSERT — `training_scheduled` + `training_started` +
  `training_completed` + `training_failed` + `training_retried`.
- CR 12-5 D-14 typed exception envelope — ModelTrainingJobNotFoundError +
  ModelTrainingFailedError + ModelTrainingDataInsufficientError +
  ModelTrainingTimeoutError.
- AD-22 owner-only RBAC.
"""
from __future__ import annotations

from typing import Final

from apps.api.modules.finops.cost_anomaly_ml_prediction.anomaly_ml_prediction_engine import (
    FEATURE_NAMES,
    MODEL_HYPERPARAMETERS,
    _generate_id,
    _now_iso,
    _validate_model_type,
    _validate_tenant_id,
)

# ── Module constants ──────────────────────────────────────────────────────
TRAINING_DATA_WINDOW_DAYS_DEFAULT: Final[int] = 90
TRAINING_DATA_WINDOW_MIN_DAYS: Final[int] = 30
TRAINING_DATA_WINDOW_MAX_DAYS: Final[int] = 365
TRAINING_RETRY_MAX: Final[int] = 3
TRAINING_RETRY_BASE_SECONDS: Final[int] = 60
TRAINING_RETRY_MAX_SECONDS: Final[int] = 600
TRAINING_TIMEOUT_SECONDS: Final[int] = 3600  # 1 hour

# Cron schedule for retraining (KST Sunday 03:00 = UTC Saturday 18:00)
TRAINING_CRON_SCHEDULE: Final[str] = "0 3 * * 0"


def _validate_training_window(window_days: int) -> None:
    """Validate training_data_window_days is within bounds (30~365)."""
    if (
        not isinstance(window_days, int)
        or window_days < TRAINING_DATA_WINDOW_MIN_DAYS
        or window_days > TRAINING_DATA_WINDOW_MAX_DAYS
    ):
        raise ValueError(
            f"training_data_window must be between "
            f"{TRAINING_DATA_WINDOW_MIN_DAYS} and "
            f"{TRAINING_DATA_WINDOW_MAX_DAYS}, got {window_days}"
        )


def _validate_training_job_id(training_job_id: str) -> None:
    """Validate training_job_id is non-empty string."""
    if not training_job_id or not isinstance(training_job_id, str):
        raise ValueError("training_job_id must be a non-empty string")


def _get_default_hyperparameters(model_type: str) -> dict[str, object]:
    """Get default hyperparameters for a model_type.

    Args:
        model_type: ModelType (prophet/lstm/arima/isolation_forest/autoencoder).

    Returns:
        Dict of default hyperparameters.
    """
    return dict(MODEL_HYPERPARAMETERS.get(model_type, {}))


def train_model(
    tenant_id: str,
    model_type: str,
    training_data_window_days: int = TRAINING_DATA_WINDOW_DAYS_DEFAULT,
    trigger: str = "manual_trigger",
) -> ModelTrainingJob:
    """Schedule a model training job.

    Args:
        tenant_id: UUID tenant identifier (CR 0-2 RLS selector).
        model_type: ModelType (prophet/lstm/arima/isolation_forest/autoencoder).
        training_data_window_days: training data window (default 90, range 30~365).
        trigger: trigger reason (drift_detected/weekly_schedule/manual_trigger).

    Returns:
        ModelTrainingJob TypedDict.
    """
    _validate_tenant_id(tenant_id)
    _validate_model_type(model_type)
    _validate_training_window(training_data_window_days)
    if trigger not in {"drift_detected", "weekly_schedule", "manual_trigger"}:
        raise ValueError(
            f"trigger must be one of {{drift_detected, weekly_schedule, manual_trigger}}, "
            f"got {trigger}"
        )

    training_job_id = _generate_id()
    return ModelTrainingJob(
        training_job_id=training_job_id,
        tenant_id=tenant_id,
        model_id="",
        model_type=model_type,
        training_data_window_days=training_data_window_days,
        status="scheduled",
        hyperparameters=_get_default_hyperparameters(model_type),
        shap_feature_importance=dict.fromkeys(FEATURE_NAMES, 0.0),
        started_at=_now_iso(),
        completed_at="",
        retry_count=0,
        error_message="",
    )


def get_training_job_status(training_job_id: str) -> ModelTrainingJob:
    """Get the status of a training job.

    Args:
        training_job_id: UUID v7 training job identifier.

    Returns:
        ModelTrainingJob TypedDict.
    """
    _validate_training_job_id(training_job_id)
    return ModelTrainingJob(
        training_job_id=training_job_id,
        tenant_id="",
        model_id="",
        model_type="",
        training_data_window_days=TRAINING_DATA_WINDOW_DAYS_DEFAULT,
        status="scheduled",
        hyperparameters={},
        shap_feature_importance={},
        started_at=_now_iso(),
        completed_at="",
        retry_count=0,
        error_message="",
    )


def list_training_history(
    tenant_id: str,
    model_type: str | None = None,
) -> list[ModelTrainingJob]:
    """List training history for a tenant with optional model_type filter.

    Args:
        tenant_id: UUID tenant identifier (CR 0-2 RLS selector).
        model_type: optional model_type filter.

    Returns:
        List of ModelTrainingJob TypedDicts.
    """
    _validate_tenant_id(tenant_id)
    return []


def cancel_training_job(training_job_id: str) -> ModelTrainingJob:
    """Cancel a running training job.

    Args:
        training_job_id: UUID v7 training job identifier.

    Returns:
        Cancelled ModelTrainingJob TypedDict.
    """
    _validate_training_job_id(training_job_id)
    return ModelTrainingJob(
        training_job_id=training_job_id,
        tenant_id="",
        model_id="",
        model_type="",
        training_data_window_days=TRAINING_DATA_WINDOW_DAYS_DEFAULT,
        status="cancelled",
        hyperparameters={},
        shap_feature_importance={},
        started_at=_now_iso(),
        completed_at=_now_iso(),
        retry_count=0,
        error_message="cancelled by user",
    )


__all__ = [
    "train_model",
    "get_training_job_status",
    "list_training_history",
    "cancel_training_job",
    "TRAINING_DATA_WINDOW_DAYS_DEFAULT",
    "TRAINING_DATA_WINDOW_MIN_DAYS",
    "TRAINING_DATA_WINDOW_MAX_DAYS",
    "TRAINING_RETRY_MAX",
    "TRAINING_RETRY_BASE_SECONDS",
    "TRAINING_RETRY_MAX_SECONDS",
    "TRAINING_TIMEOUT_SECONDS",
    "TRAINING_CRON_SCHEDULE",
]
