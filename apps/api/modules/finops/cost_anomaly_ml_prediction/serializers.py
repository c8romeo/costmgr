"""apps.api.modules.finops.cost_anomaly_ml_prediction.serializers — Phase 26 serializers.

Phase 26 wire (cj-style 181번째) — FinOps Cost Anomaly ML Prediction
pre-anomaly-detection layer serializers (PRD §F42.1~§F42.8 verbatim +
AD-55 (a)~(g) 7 sub-decisions + Phase 11 + Phase 12 + Phase 13 +
Phase 14 + Phase 22 + Phase 23 + Phase 24 ledger data 활용).

Provides:
- Enums: PredictionStatus (5: training/deploying/active/deprecated/retired)
  + ModelType (5: prophet/lstm/arima/isolation_forest/autoencoder)
  + PredictionMethod (3: supervised/unsupervised/ensemble).
- TypedDicts: AnomalyMLPrediction (18 fields) + AnomalyMLScoreResult (14
  fields) + ModelRegistryEntry (16 fields) + ModelTrainingJob (12 fields).
- Constants: COST_ANOMALY_ML_PREDICTION_ENGINE_MODEL_VERSION +
  DEFAULT_ENSEMBLE_WEIGHTS (prophet 0.30 + lstm 0.30 + arima 0.15 +
  isolation_forest 0.15 + autoencoder 0.10) + DRIFT_PSI_THRESHOLD =
  0.25 + ENSEMBLE_CONSENSUS_THRESHOLD = 0.85 + BOOTSTRAP_SAMPLES =
  1000 + ML_CADENCE_HOURS_KST + ML_RECIPIENT_TEMPLATES + ML_DEFAULTS.

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — 12 NEW audit actions via
  ActionClass.COST_ANOMALY_ML_PREDICTION.
- CR 1-1 ContextVar — trace_id propagation.
- CR 1-1 RSC boundary — apps/web Next.js 15.x RSC.
- CR 5-1 banker's rounding — Decimal precision verbatim.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 16 NEW typed exceptions.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface parity.
- CR 12-5 D-GATE-01 — capability gate fail-closed.
- AD-14 stack pin — prophet==1.1.5 + tensorflow==2.16.1 +
  statsmodels==0.14.2 + scikit-learn==1.4.0 + Recharts 2.12.7 +
  TanStack Table v8 + noto-sans-cjk-kr + apscheduler 3.10.4 + pytz 2024.1.
- AD-22 owner-only RBAC.
- AD-55 (a)~(g) 7 sub-decisions (Phase 26 wire).
- Epic 12 2FA 챌린지 mandatory high-value (≥10M KRW impact forecast).
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT (finops_cost_anomaly_ml_prediction.* namespace
  EXTENSION ~30 keys).
- D-FINOPS-15 honestly DEFER (multi-modal anomaly ML + causal inference
  + LLM explanation + automated remediation + federated learning +
  marketplace + streaming + online learning — all honestly DEFER to
  future Phase 26.x).
- CR 11-3 ALLOWED_SERVICE_SUBMODULES 즉시 sweep EXTENSION
  m34_finops_cost_anomaly_ml_prediction.
"""

from __future__ import annotations

import enum
from typing import TypedDict

# ── Module constants ──────────────────────────────────────────────────────
COST_ANOMALY_ML_PREDICTION_ENGINE_MODEL_VERSION = "1.0.0"

# High-value threshold for owner approval flow (PRD §F42 + AD-55 (g))
HIGH_VALUE_THRESHOLD_KRW_PER_YEAR = 10_000_000.0  # 10M KRW impact forecast

# 5-model ensemble weights (PRD §F42.1 + AD-55 (a) verbatim — 5 model
# types parallel training + ensemble weighted consensus)
DEFAULT_ENSEMBLE_WEIGHTS: dict[str, float] = {
    "prophet": 0.30,
    "lstm": 0.30,
    "arima": 0.15,
    "isolation_forest": 0.15,
    "autoencoder": 0.10,
}

# Drift detection thresholds (PRD §F42.2 + AD-55 (b) verbatim)
DRIFT_PSI_THRESHOLD = 0.25  # PSI threshold above which drift is detected

# Ensemble consensus threshold (PRD §F42.4 + AD-55 (d) verbatim)
ENSEMBLE_CONSENSUS_THRESHOLD = 0.85  # consensus_detected if ensemble_score >= threshold

# Bootstrap sampling for confidence interval (PRD §F42.4 + AD-55 (d))
BOOTSTRAP_SAMPLES = 1000  # B=1000 resamples for 5th/95th percentile CI

# LRU cache size for model artifacts in-memory (PRD §F42.4)
ML_MODEL_LRU_CACHE_MAX = 100

# Real-time inference latency target P95 (PRD §F42.4 + AD-55 (d))
ML_INFERENCE_P95_LATENCY_MS = 200.0  # < 200ms P95

# Batch inference latency target (PRD §F42.4 + AD-55 (d))
ML_BATCH_INFERENCE_TARGET_SEC = 60.0  # < 60s per 1000 predictions
ML_BATCH_SIZE_DEFAULT = 100
ML_BATCH_SIZE_MAX = 1000

# A/B testing thresholds (PRD §F42.2 + AD-55 (b) verbatim)
AB_TEST_TRAFFIC_SPLIT_DEFAULT = 0.50  # 50/50 champion/challenger
AB_TEST_AUTO_PROMOTE_MARGIN = 0.05  # challenger >= champion + 0.05
AB_TEST_AUTO_PROMOTE_CONSECUTIVE_DAYS = 7

# 4-dim model scoring weights (PRD §F42.2 + AD-55 (b) verbatim —
# precision 0.30 + recall 0.30 + F1 0.25 + AUC-ROC 0.15)
ML_MODEL_SCORING_WEIGHTS: dict[str, float] = {
    "precision": 0.30,
    "recall": 0.30,
    "f1": 0.25,
    "auc_roc": 0.15,
}

# Cost guards (PRD §F42.1 verbatim)
MAX_PREDICTIONS_PER_TENANT = 50000
MAX_MODEL_VERSIONS_PER_TENANT = 100
MAX_TRAINING_JOBS_PER_TENANT = 500
MAX_MODEL_ARTIFACT_SIZE_BYTES = 500_000_000  # 500MB
TOTAL_VERIFICATION_TOLERANCE_KRW = 0.01  # ±0.01 KRW
AUTO_RETRAINING_TRIGGER_DRIFT_PSI = 0.25  # PSI threshold

# Cadence schedule KST pytz (PRD §F42.1 + AD-55 (c) verbatim)
ML_CADENCE_HOURS_KST: dict[str, tuple[int, int]] = {
    "weekly_scheduled_training": (3, 0),  # 03:00 KST every Sunday
    "daily_drift_detection": (4, 0),  # 04:00 KST daily
    "nightly_batch_inference": (2, 0),  # 02:00 KST nightly
    "daily_model_promotion_check": (5, 0),  # 05:00 KST daily
}

# Recipient strategy templates (PRD §F42.4 verbatim, extended)
ML_RECIPIENT_TEMPLATES: dict[str, dict[str, object]] = {
    "owner_only": {
        "slack_channels": ["#finops-cost-anomaly-ml-prediction"],
        "email_recipients": ["tenant_owner"],
        "ms_teams_channels": [],
        "s3_archive_enabled": True,
    },
    "executive": {
        "slack_channels": [
            "#finops-cost-anomaly-ml-prediction",
            "#finops-executive",
        ],
        "email_recipients": ["tenant_owner", "tenant_admin"],
        "ms_teams_channels": ["FinOps Cost Anomaly ML Prediction"],
        "s3_archive_enabled": True,
    },
    "audit_only": {
        "slack_channels": [],
        "email_recipients": ["tenant_owner"],
        "ms_teams_channels": [],
        "s3_archive_enabled": True,
    },
}

# LISTEN/NOTIFY channels (PRD §F42.1 verbatim — 12 channels)
LISTEN_NOTIFY_CHANNELS: tuple[str, ...] = (
    "phase_26_prediction_created",
    "phase_26_prediction_updated",
    "phase_26_prediction_status_changed",
    "phase_26_prediction_retired",
    "phase_26_prediction_served",
    "phase_26_batch_prediction_executed",
    "phase_26_model_version_registered",
    "phase_26_model_drift_detected",
    "phase_26_ab_test_champion_promoted",
    "phase_26_ab_test_challenger_promoted",
    "phase_26_training_scheduled",
    "phase_26_cost_anomaly_ml_prediction_dry_run_executed",
)

# Defaults dict (used by aggregators)
ML_DEFAULTS: dict[str, object] = {
    "model_version": COST_ANOMALY_ML_PREDICTION_ENGINE_MODEL_VERSION,
    "high_value_threshold_krw_per_year": HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    "ensemble_weights": DEFAULT_ENSEMBLE_WEIGHTS,
    "drift_psi_threshold": DRIFT_PSI_THRESHOLD,
    "ensemble_consensus_threshold": ENSEMBLE_CONSENSUS_THRESHOLD,
    "bootstrap_samples": BOOTSTRAP_SAMPLES,
    "model_lru_cache_max": ML_MODEL_LRU_CACHE_MAX,
    "inference_p95_latency_ms": ML_INFERENCE_P95_LATENCY_MS,
    "batch_inference_target_sec": ML_BATCH_INFERENCE_TARGET_SEC,
    "batch_size_default": ML_BATCH_SIZE_DEFAULT,
    "batch_size_max": ML_BATCH_SIZE_MAX,
    "ab_test_traffic_split_default": AB_TEST_TRAFFIC_SPLIT_DEFAULT,
    "ab_test_auto_promote_margin": AB_TEST_AUTO_PROMOTE_MARGIN,
    "ab_test_auto_promote_consecutive_days": AB_TEST_AUTO_PROMOTE_CONSECUTIVE_DAYS,
    "model_scoring_weights": ML_MODEL_SCORING_WEIGHTS,
    "max_predictions_per_tenant": MAX_PREDICTIONS_PER_TENANT,
    "max_model_versions_per_tenant": MAX_MODEL_VERSIONS_PER_TENANT,
    "max_training_jobs_per_tenant": MAX_TRAINING_JOBS_PER_TENANT,
    "max_model_artifact_size_bytes": MAX_MODEL_ARTIFACT_SIZE_BYTES,
    "total_verification_tolerance_krw": TOTAL_VERIFICATION_TOLERANCE_KRW,
    "auto_retraining_trigger_drift_psi": AUTO_RETRAINING_TRIGGER_DRIFT_PSI,
    "cadence_hours_kst": ML_CADENCE_HOURS_KST,
    "recipient_templates": ML_RECIPIENT_TEMPLATES,
    "listen_notify_channels": LISTEN_NOTIFY_CHANNELS,
    "dry_run_default": True,  # AnomalyMLPredictionOverviewCard 진입 시 default dry-run
}


# ── Enums ─────────────────────────────────────────────────────────────────
class PredictionStatus(enum.StrEnum):
    """PRD §F42.1 + AD-55 (a) — 5-state prediction lifecycle."""

    TRAINING = "training"
    DEPLOYING = "deploying"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


ALL_PREDICTION_STATUSES = frozenset(item.value for item in PredictionStatus)


class ModelType(enum.StrEnum):
    """PRD §F42.1 + AD-55 (a) — 5 model types in ensemble."""

    PROPHET = "prophet"
    LSTM = "lstm"
    ARIMA = "arima"
    ISOLATION_FOREST = "isolation_forest"
    AUTOENCODER = "autoencoder"


ALL_MODEL_TYPES = frozenset(item.value for item in ModelType)


class PredictionMethod(enum.StrEnum):
    """PRD §F42.1 + AD-55 (a) — 3 prediction methods."""

    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    ENSEMBLE = "ensemble"


ALL_PREDICTION_METHODS = frozenset(item.value for item in PredictionMethod)


class DriftType(enum.StrEnum):
    """PRD §F42.2 + AD-55 (b) — 3 drift detection types."""

    DATA_DRIFT = "data_drift"
    CONCEPT_DRIFT = "concept_drift"
    PREDICTION_DRIFT = "prediction_drift"


ALL_DRIFT_TYPES = frozenset(item.value for item in DriftType)


class TrainingJobStatus(enum.StrEnum):
    """PRD §F42.3 + AD-55 (c) — 5-state training job lifecycle."""

    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


ALL_TRAINING_JOB_STATUSES = frozenset(item.value for item in TrainingJobStatus)


class AnomalyMLDryRunMode(enum.StrEnum):
    """PRD §F42.8 + AD-55 (a) — 3 dry-run modes."""

    ACTUAL = "actual"
    PREVIEW = "preview"
    SKIP = "skip"


ALL_ANOMALY_ML_DRY_RUN_MODES = frozenset(item.value for item in AnomalyMLDryRunMode)


# ── TypedDicts ────────────────────────────────────────────────────────────
class AnomalyMLPrediction(TypedDict, total=False):
    """PRD §F42.1 + AD-55 (a) — Anomaly ML prediction record (18 fields).

    Fields:
    - prediction_id (str): UUID v7
    - tenant_id (str): UUID tenant
    - model_id (str): UUID v7 model_registry_entry
    - model_type (str): ModelType (prophet/lstm/arima/isolation_forest/autoencoder)
    - period_key (str): "YYYY-MM-DD"
    - horizon_days (int): default 7
    - features (dict): 8 features extracted from multi-phase ledger
    - predicted_values (dict): predicted cost values JSONB
    - actual_values (dict): nullable actual cost values
    - confidence_lower (dict): bootstrap 5th percentile lower CI
    - confidence_upper (dict): bootstrap 95th percentile upper CI
    - predicted_anomaly_score (float): NUMERIC(5,4) 0.0000~1.0000
    - threshold_anomaly_score (float): NUMERIC(5,4) Phase 12 threshold comparison
    - ensemble_consensus_score (float): NUMERIC(5,4) 0.85+ = consensus
    - prediction_method (str): PredictionMethod
    - status (str): PredictionStatus (5 states)
    - computed_at (str): ISO 8601
    """

    prediction_id: str
    tenant_id: str
    model_id: str
    model_type: str
    period_key: str
    horizon_days: int
    features: dict[str, object]
    predicted_values: dict[str, object]
    actual_values: dict[str, object]
    confidence_lower: dict[str, object]
    confidence_upper: dict[str, object]
    predicted_anomaly_score: float
    threshold_anomaly_score: float
    ensemble_consensus_score: float
    prediction_method: str
    status: str
    computed_at: str


class AnomalyMLScoreResult(TypedDict, total=False):
    """PRD §F42.4 + AD-55 (d) — Anomaly ML score result (14 fields).

    Fields:
    - score_id (str): UUID v7
    - prediction_id (str): parent AnomalyMLPrediction
    - tenant_id (str): UUID tenant
    - period_key (str): "YYYY-MM-DD"
    - ml_ensemble_score (float): NUMERIC(5,4)
    - ml_anomaly_detected (bool): ml_ensemble_score >= threshold
    - threshold_z_score (float): Phase 12 z_score comparison
    - threshold_iqr_score (float): Phase 12 IQR score comparison
    - threshold_ewma_score (float): Phase 12 EWMA score comparison
    - threshold_isolation_forest_score (float): Phase 12 isolation_forest comparison
    - threshold_anomaly_detected (bool): Phase 12 rule-based detection result
    - consensus_detected (bool): ML + Phase 12 both detect anomaly
    - consensus_score (float): combined score
    - drift_detected (bool): PSI drift detected
    - inference_latency_ms (float): P95 latency tracking
    - served_at (str): ISO 8601
    """

    score_id: str
    prediction_id: str
    tenant_id: str
    period_key: str
    ml_ensemble_score: float
    ml_anomaly_detected: bool
    threshold_z_score: float
    threshold_iqr_score: float
    threshold_ewma_score: float
    threshold_isolation_forest_score: float
    threshold_anomaly_detected: bool
    consensus_detected: bool
    consensus_score: float
    drift_detected: bool
    inference_latency_ms: float
    served_at: str


class ModelRegistryEntry(TypedDict, total=False):
    """PRD §F42.2 + AD-55 (b) — Model registry entry (16 fields).

    Fields:
    - model_id (str): UUID v7
    - tenant_id (str): UUID tenant
    - model_name (str): display name
    - model_type (str): ModelType
    - model_version (str): semver MAJOR.MINOR.PATCH
    - model_artifact_sha256 (str): sha256:64-hex checksum
    - model_artifact_size_bytes (int): artifact size in bytes
    - status (str): PredictionStatus (5 states)
    - traffic_split_pct (float): A/B testing traffic split (0.0~1.0)
    - precision_score (float): 0.00~1.00
    - recall_score (float): 0.00~1.00
    - f1_score (float): 0.00~1.00
    - auc_roc_score (float): 0.00~1.00
    - composite_score (float): 4-dim weighted score
    - version_history (list): JSONB append-only semver history
    - registered_at (str): ISO 8601
    """

    model_id: str
    tenant_id: str
    model_name: str
    model_type: str
    model_version: str
    model_artifact_sha256: str
    model_artifact_size_bytes: int
    status: str
    traffic_split_pct: float
    precision_score: float
    recall_score: float
    f1_score: float
    auc_roc_score: float
    composite_score: float
    version_history: list[dict[str, object]]
    registered_at: str


class ModelTrainingJob(TypedDict, total=False):
    """PRD §F42.3 + AD-55 (c) — Model training job (12 fields).

    Fields:
    - training_job_id (str): UUID v7
    - tenant_id (str): UUID tenant
    - model_id (str): parent ModelRegistryEntry
    - model_type (str): ModelType
    - training_data_window_days (int): default 90
    - status (str): TrainingJobStatus (5 states)
    - hyperparameters (dict): per-model_type hyperparameters
    - shap_feature_importance (dict): SHAP feature importance JSONB
    - started_at (str): ISO 8601
    - completed_at (str): ISO 8601 nullable
    - retry_count (int): exponential backoff retry count
    - error_message (str): failure error message
    """

    training_job_id: str
    tenant_id: str
    model_id: str
    model_type: str
    training_data_window_days: int
    status: str
    hyperparameters: dict[str, object]
    shap_feature_importance: dict[str, object]
    started_at: str
    completed_at: str
    retry_count: int
    error_message: str


# ── ALL_* constants derived from each enum ─────────────────────────────────
ALL_PREDICTION_STATUS_VALUES = ALL_PREDICTION_STATUSES
ALL_MODEL_TYPE_VALUES = ALL_MODEL_TYPES
ALL_PREDICTION_METHOD_VALUES = ALL_PREDICTION_METHODS
ALL_DRIFT_TYPE_VALUES = ALL_DRIFT_TYPES
ALL_TRAINING_JOB_STATUS_VALUES = ALL_TRAINING_JOB_STATUSES
ALL_ANOMALY_ML_DRY_RUN_MODE_VALUES = ALL_ANOMALY_ML_DRY_RUN_MODES
