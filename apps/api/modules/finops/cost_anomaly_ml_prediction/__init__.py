"""apps.api.modules.finops.cost_anomaly_ml_prediction — Phase 26 FinOps Cost Anomaly ML Prediction.

Phase 26 wire (cj-style 181번째) — ML-driven pre-detection layer for FinOps
cost anomalies (PRD §F42 + AD-55 (a)~(g) 7 sub-decisions).

Module tag (CR 0-2 RLS selector, ALLOWED_SERVICE_SUBMODULES sweep EXTENSION):
    MODULE_TAG = "m34_finops_cost_anomaly_ml_prediction"

5 model types ensemble (PRD §F42.1 + AD-55 (a)):
    prophet (0.30) + lstm (0.30) + arima (0.15) + isolation_forest (0.15) +
    autoencoder (0.10)

8 features extracted from multi-phase ledger (PRD §F42.3 + AD-55 (c)):
    cost_total_krw (Phase 11) + cost_per_unit (Phase 23) + variance_pct (Phase 24) +
    budget_consumption_pct (Phase 24) + settlement_3way_match_score (Phase 22) +
    optimization_savings_amount (Phase 14) + month_seasonality + holiday_flag.

CR lessons applied:
    CR 0-2 RLS + CR 1-1 audit-first INSERT + CR 5-1 Decimal +
    CR 9-6 atomic commit + CR 11-3 honest-DEFER + CR 12-1 L4 industry-agnostic +
    CR 12-5 D-14 typed exception envelope + AD-22 owner-only RBAC +
    AD-14 stack pin (apscheduler==3.10.4 + pytz==2024.1).
"""

from __future__ import annotations

# ── Module metadata ───────────────────────────────────────────────────────
MODULE_TAG: str = "m34_finops_cost_anomaly_ml_prediction"
MODULE_NAME: str = "FinOps Cost Anomaly ML Prediction"
MODULE_VERSION: str = "1.0.0"

# Re-export core public API
from apps.api.modules.finops.cost_anomaly_ml_prediction.anomaly_ml_prediction_engine import (
    FEATURE_NAMES,
    MODEL_HYPERPARAMETERS,
    PREDICTION_HORIZON_DAYS_DEFAULT,
    aggregate_predictions,
    create_prediction,
    list_predictions,
    read_prediction,
    retire_prediction,
    update_prediction,
)
from apps.api.modules.finops.cost_anomaly_ml_prediction.serializers import (
    BOOTSTRAP_SAMPLES,
    COST_ANOMALY_ML_PREDICTION_ENGINE_MODEL_VERSION,
    DEFAULT_ENSEMBLE_WEIGHTS,
    DRIFT_PSI_THRESHOLD,
    ENSEMBLE_CONSENSUS_THRESHOLD,
    LISTEN_NOTIFY_CHANNELS,
    ML_BATCH_SIZE_DEFAULT,
    ML_BATCH_SIZE_MAX,
    ML_CADENCE_HOURS_KST,
    ML_DEFAULTS,
    ML_INFERENCE_P95_LATENCY_MS,
    ML_MODEL_LRU_CACHE_MAX,
    ML_RECIPIENT_TEMPLATES,
    AnomalyMLDryRunMode,
    AnomalyMLPrediction,
    AnomalyMLScoreResult,
    DriftType,
    ModelRegistryEntry,
    ModelTrainingJob,
    ModelType,
    PredictionMethod,
    PredictionStatus,
    TrainingJobStatus,
)

# Re-export DRIFT_PSI_THRESHOLD with full canonical name
DRIFT_PSI_THRESHOLD_DEFAULT = DRIFT_PSI_THRESHOLD
from apps.api.modules.finops.cost_anomaly_ml_prediction.anomaly_ml_ensemble_consensus import (
    DEFAULT_THRESHOLD,
    DEFAULT_WEIGHTS,
    consensus_detected,
    ensemble_consensus_score,
)
from apps.api.modules.finops.cost_anomaly_ml_prediction.anomaly_ml_model_registry import (
    AUTO_PROMOTE_CONSECUTIVE_DAYS,
    AUTO_PROMOTE_MARGIN,
    DRIFT_PSI_THRESHOLD_DEFAULT,
    MODEL_SCORING_WEIGHTS,
    SEMVER_DEFAULT_VERSION,
    TRAFFIC_SPLIT_DEFAULT,
    deprecate_model,
    list_active_models,
    register_model,
    update_model_status,
)
from apps.api.modules.finops.cost_anomaly_ml_prediction.anomaly_ml_scoring import (
    batch_predict_anomaly_scores,
    predict_anomaly_score,
    score_threshold_anomaly,
)
from apps.api.modules.finops.cost_anomaly_ml_prediction.anomaly_ml_training_pipeline import (
    TRAINING_CRON_SCHEDULE,
    TRAINING_DATA_WINDOW_DAYS_DEFAULT,
    TRAINING_DATA_WINDOW_MAX_DAYS,
    TRAINING_DATA_WINDOW_MIN_DAYS,
    TRAINING_RETRY_BASE_SECONDS,
    TRAINING_RETRY_MAX,
    TRAINING_RETRY_MAX_SECONDS,
    TRAINING_TIMEOUT_SECONDS,
    cancel_training_job,
    get_training_job_status,
    list_training_history,
    train_model,
)
from apps.api.modules.finops.cost_anomaly_ml_prediction.scheduled_cost_anomaly_ml_prediction_jobs import (
    KST_TIMEZONE,
    daily_drift_detection_job,
    daily_model_promotion_check_job,
    nightly_batch_inference_job,
    notify_listen_channels,
    schedule_cost_anomaly_ml_prediction_jobs,
    weekly_scheduled_training_job,
)

__all__ = [
    # Module metadata
    "MODULE_TAG",
    "MODULE_NAME",
    "MODULE_VERSION",
    # Serializers — types
    "AnomalyMLPrediction",
    "AnomalyMLScoreResult",
    "ModelRegistryEntry",
    "ModelTrainingJob",
    "PredictionStatus",
    "ModelType",
    "PredictionMethod",
    "DriftType",
    "TrainingJobStatus",
    "AnomalyMLDryRunMode",
    # Serializers — constants
    "LISTEN_NOTIFY_CHANNELS",
    "ML_BATCH_SIZE_DEFAULT",
    "ML_BATCH_SIZE_MAX",
    "ML_CADENCE_HOURS_KST",
    "ML_DEFAULTS",
    "ML_INFERENCE_P95_LATENCY_MS",
    "ML_MODEL_LRU_CACHE_MAX",
    "ML_RECIPIENT_TEMPLATES",
    # Engine
    "COST_ANOMALY_ML_PREDICTION_ENGINE_MODEL_VERSION",
    "DEFAULT_ENSEMBLE_WEIGHTS",
    "FEATURE_NAMES",
    "MODEL_HYPERPARAMETERS",
    "PREDICTION_HORIZON_DAYS_DEFAULT",
    "create_prediction",
    "read_prediction",
    "update_prediction",
    "retire_prediction",
    "list_predictions",
    "aggregate_predictions",
    # Model registry
    "AUTO_PROMOTE_CONSECUTIVE_DAYS",
    "AUTO_PROMOTE_MARGIN",
    "DRIFT_PSI_THRESHOLD_DEFAULT",
    "MODEL_SCORING_WEIGHTS",
    "SEMVER_DEFAULT_VERSION",
    "TRAFFIC_SPLIT_DEFAULT",
    "register_model",
    "update_model_status",
    "list_active_models",
    "deprecate_model",
    # Training pipeline
    "TRAINING_CRON_SCHEDULE",
    "TRAINING_DATA_WINDOW_DAYS_DEFAULT",
    "TRAINING_DATA_WINDOW_MAX_DAYS",
    "TRAINING_DATA_WINDOW_MIN_DAYS",
    "TRAINING_RETRY_BASE_SECONDS",
    "TRAINING_RETRY_MAX",
    "TRAINING_RETRY_MAX_SECONDS",
    "TRAINING_TIMEOUT_SECONDS",
    "train_model",
    "get_training_job_status",
    "list_training_history",
    "cancel_training_job",
    # Scoring
    "batch_predict_anomaly_scores",
    "predict_anomaly_score",
    "score_threshold_anomaly",
    # Ensemble consensus
    "DEFAULT_THRESHOLD",
    "DEFAULT_WEIGHTS",
    "consensus_detected",
    "ensemble_consensus_score",
    # Scheduled jobs
    "KST_TIMEZONE",
    "weekly_scheduled_training_job",
    "daily_drift_detection_job",
    "nightly_batch_inference_job",
    "daily_model_promotion_check_job",
    "notify_listen_channels",
    "schedule_cost_anomaly_ml_prediction_jobs",
]
