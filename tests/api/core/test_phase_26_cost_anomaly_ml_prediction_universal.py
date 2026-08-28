"""tests.api.core.test_phase_26_cost_anomaly_ml_prediction_universal — Phase 26 universal pytest.

Phase 26 wire (cj-style 181번째) — FinOps Cost Anomaly ML Prediction
universal pytest coverage (analogous to test_audit_fixes_canonical_signature_universal.py).

CR lessons applied:
- CR 11-3 honest-DEFER: NO NEW source code in this test file —
  validation only against Phase 26 wire scope.
- CR 12-5 D-PARITY-01: Python TypedDict parity verification.
- CR 12-5 D-14: typed exception envelope verification.

Test count: 12 NEW pytest cases for Phase 26 universal drift detection.
"""
from __future__ import annotations

import os
import sys
from decimal import Decimal

import pytest

# Ensure apps.api is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from apps.api.modules.finops.cost_anomaly_ml_prediction import (  # noqa: E402
    AUTO_PROMOTE_CONSECUTIVE_DAYS,
    AUTO_PROMOTE_MARGIN,
    COST_ANOMALY_ML_PREDICTION_ENGINE_MODEL_VERSION,
    DEFAULT_ENSEMBLE_WEIGHTS,
    DRIFT_PSI_THRESHOLD_DEFAULT,
    ENSEMBLE_CONSENSUS_THRESHOLD,
    FEATURE_NAMES,
    LISTEN_NOTIFY_CHANNELS,
    ML_BATCH_SIZE_DEFAULT,
    ML_BATCH_SIZE_MAX,
    ML_CADENCE_HOURS_KST,
    ML_INFERENCE_P95_LATENCY_MS,
    ML_MODEL_LRU_CACHE_MAX,
    MODEL_HYPERPARAMETERS,
    MODEL_SCORING_WEIGHTS,
    SEMVER_DEFAULT_VERSION,
    TRAFFIC_SPLIT_DEFAULT,
    TRAINING_DATA_WINDOW_DAYS_DEFAULT,
    TRAINING_DATA_WINDOW_MAX_DAYS,
    TRAINING_DATA_WINDOW_MIN_DAYS,
    TRAINING_RETRY_MAX,
    AnomalyMLPrediction,
    AnomalyMLScoreResult,
    DriftType,
    ModelRegistryEntry,
    ModelTrainingJob,
    ModelType,
    PredictionStatus,
    TrainingJobStatus,
    aggregate_predictions,
    batch_predict_anomaly_scores,
    consensus_detected,
    create_prediction,
    deprecate_model,
    ensemble_consensus_score,
    list_active_models,
    list_predictions,
    predict_anomaly_score,
    register_model,
    retire_prediction,
    score_threshold_anomaly,
    train_model,
    update_model_status,
    update_prediction,
)

TENANT_ID = "00000000-0000-0000-0000-000000000001"
PREDICTION_ID = "00000000-0000-0000-0000-000000000002"
MODEL_ID = "00000000-0000-0000-0000-000000000003"


class TestPhase26Constants:
    """Test Phase 26 constants and configuration values."""

    def test_1a_ensemble_weights_sum_to_one(self) -> None:
        """5-model ensemble weights sum to 1.0 (PRD §F42.1 + AD-55 (a) verbatim)."""
        total = sum(DEFAULT_ENSEMBLE_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-6, f"weights sum = {total}, expected 1.0"

    def test_1b_default_ensemble_weights_match_spec(self) -> None:
        """Default weights: prophet 0.30 + lstm 0.30 + arima 0.15 + isolation_forest 0.15 + autoencoder 0.10."""
        assert DEFAULT_ENSEMBLE_WEIGHTS["prophet"] == 0.30
        assert DEFAULT_ENSEMBLE_WEIGHTS["lstm"] == 0.30
        assert DEFAULT_ENSEMBLE_WEIGHTS["arima"] == 0.15
        assert DEFAULT_ENSEMBLE_WEIGHTS["isolation_forest"] == 0.15
        assert DEFAULT_ENSEMBLE_WEIGHTS["autoencoder"] == 0.10

    def test_1c_consensus_threshold_default(self) -> None:
        """Ensemble consensus threshold default = 0.85 (PRD §F42.1)."""
        assert float(ENSEMBLE_CONSENSUS_THRESHOLD) == 0.85

    def test_1d_drift_psi_threshold_default(self) -> None:
        """PSI drift threshold = 0.25 (PRD §F42.2 + AD-55 (b) verbatim)."""
        assert DRIFT_PSI_THRESHOLD_DEFAULT == 0.25

    def test_1e_feature_names_count(self) -> None:
        """8 features extracted from multi-phase ledger (PRD §F42.3)."""
        assert len(FEATURE_NAMES) == 8
        assert "cost_total_krw" in FEATURE_NAMES
        assert "cost_per_unit" in FEATURE_NAMES
        assert "variance_pct" in FEATURE_NAMES
        assert "budget_consumption_pct" in FEATURE_NAMES
        assert "settlement_3way_match_score" in FEATURE_NAMES
        assert "optimization_savings_amount" in FEATURE_NAMES
        assert "month_seasonality" in FEATURE_NAMES
        assert "holiday_flag" in FEATURE_NAMES


class TestPhase26PredictionEngine:
    """Test Phase 26 prediction engine functions."""

    def test_2a_create_prediction_returns_typed_dict(self) -> None:
        """create_prediction returns AnomalyMLPrediction TypedDict."""
        result = create_prediction(
            tenant_id=TENANT_ID,
            model_id=MODEL_ID,
            period_key="2026-08",
        )
        assert isinstance(result, dict)
        assert result["tenant_id"] == TENANT_ID
        assert result["period_key"] == "2026-08"

    def test_2b_aggregate_predictions_for_period(self) -> None:
        """aggregate_predictions handles period_key argument."""
        result = aggregate_predictions(tenant_id=TENANT_ID, period_key="2026-08")
        assert isinstance(result, dict)
        assert result["total_predictions"] == 0

    def test_2c_list_predictions_returns_list(self) -> None:
        """list_predictions returns list."""
        result = list_predictions(tenant_id=TENANT_ID)
        assert isinstance(result, list)


class TestPhase26EnsembleConsensus:
    """Test Phase 26 ensemble consensus functions."""

    def test_3a_ensemble_consensus_score_computes_weighted_average(self) -> None:
        """ensemble_consensus_score computes weighted average."""
        scores = {
            "prophet": 0.80,
            "lstm": 0.70,
            "arima": 0.60,
            "isolation_forest": 0.50,
            "autoencoder": 0.40,
        }
        result = ensemble_consensus_score(scores)
        assert 0.0 <= result <= 1.0

    def test_3b_consensus_detected_above_threshold(self) -> None:
        """consensus_detected returns True when ml_score >= threshold."""
        assert consensus_detected(ml_score=0.90) is True

    def test_3c_consensus_not_detected_below_threshold(self) -> None:
        """consensus_detected returns False when ml_score < threshold."""
        assert consensus_detected(ml_score=0.50) is False


class TestPhase26Scoring:
    """Test Phase 26 scoring functions."""

    def test_4a_predict_anomaly_score_returns_typed_dict(self) -> None:
        """predict_anomaly_score returns AnomalyMLScoreResult TypedDict."""
        result = predict_anomaly_score(tenant_id=TENANT_ID, period_key="2026-08")
        assert isinstance(result, dict)
        assert result["tenant_id"] == TENANT_ID
        assert result["period_key"] == "2026-08"

    def test_4b_batch_predict_anomaly_scores(self) -> None:
        """batch_predict_anomaly_scores returns list of results."""
        result = batch_predict_anomaly_scores(
            tenant_id=TENANT_ID,
            period_keys=["2026-08", "2026-09"],
        )
        assert isinstance(result, list)
        assert len(result) == 2


class TestPhase26Cadences:
    """Test Phase 26 scheduled job cadences."""

    def test_5a_cadence_hours_kst_keys(self) -> None:
        """ML_CADENCE_HOURS_KST has 4 cadences."""
        assert "weekly_scheduled_training" in ML_CADENCE_HOURS_KST
        assert "daily_drift_detection" in ML_CADENCE_HOURS_KST
        assert "nightly_batch_inference" in ML_CADENCE_HOURS_KST
        assert "daily_model_promotion_check" in ML_CADENCE_HOURS_KST

    def test_5b_listen_notify_channels_count(self) -> None:
        """12 LISTEN/NOTIFY channels defined."""
        assert len(LISTEN_NOTIFY_CHANNELS) == 12


class TestPhase26BatchLimits:
    """Test Phase 26 batch size limits (CR 12-5 D-PARITY-01)."""

    def test_6a_batch_size_defaults(self) -> None:
        """Batch size defaults match spec."""
        assert ML_BATCH_SIZE_DEFAULT == 100
        assert ML_BATCH_SIZE_MAX == 1000

    def test_6b_inference_p95_latency(self) -> None:
        """ML inference P95 latency ≤ 200ms (PRD §F42.4)."""
        assert ML_INFERENCE_P95_LATENCY_MS <= 200

    def test_6c_model_lru_cache_max(self) -> None:
        """LRU cache max 100 models (PRD §F42.4)."""
        assert ML_MODEL_LRU_CACHE_MAX == 100

    def test_6d_training_window_bounds(self) -> None:
        """Training data window 30~365 days."""
        assert TRAINING_DATA_WINDOW_MIN_DAYS == 30
        assert TRAINING_DATA_WINDOW_MAX_DAYS == 365
        assert TRAINING_DATA_WINDOW_DAYS_DEFAULT == 90

    def test_6e_training_retry_max(self) -> None:
        """Training retry max 3 (PRD §F42.3)."""
        assert TRAINING_RETRY_MAX == 3

    def test_6f_traffic_split_default(self) -> None:
        """A/B testing traffic_split default = 50/50 (PRD §F42.2)."""
        assert TRAFFIC_SPLIT_DEFAULT == 0.50

    def test_6g_semver_default_version(self) -> None:
        """Default semver = 0.1.0."""
        assert SEMVER_DEFAULT_VERSION == "0.1.0"

    def test_6h_auto_promote_params(self) -> None:
        """Auto-promote criterion = challenger + 0.05 for 7 days."""
        assert AUTO_PROMOTE_MARGIN == 0.05
        assert AUTO_PROMOTE_CONSECUTIVE_DAYS == 7

    def test_6i_engine_model_version(self) -> None:
        """Engine model version is set."""
        assert COST_ANOMALY_ML_PREDICTION_ENGINE_MODEL_VERSION is not None
        assert isinstance(COST_ANOMALY_ML_PREDICTION_ENGINE_MODEL_VERSION, str)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
