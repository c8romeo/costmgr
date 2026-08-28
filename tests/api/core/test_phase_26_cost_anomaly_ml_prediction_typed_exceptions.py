"""tests.api.core.test_phase_26_cost_anomaly_ml_prediction_typed_exceptions — Phase 26 typed exceptions EXTENSION tests.

Phase 26 (cj-style 184번째 wire follow-up) — FinOps Cost Anomaly ML
Prediction territory typed exceptions EXTENSION (PRD §F42.7 verbatim).
CR 12-5 D-14 envelope applied to 16 NEW typed exception classes shared
across cost_anomaly_ml_prediction modules (serializers + engine +
model_registry + training_pipeline + scoring + ensemble_consensus +
scheduled_jobs).

Phase 26 wire cycle (cj-style 179 + 180 + 181 + 182 + 183 → cj-style 184 = typed exceptions EXTENSION):
- cj-style 179: Phase 26 PRD entry (PRD §F42 EXTENSION)
- cj-style 180: Phase 26 spec entry (8 ACs §F42.1~§F42.8 verbatim)
- cj-style 181: Phase 26 atomic wire (4 NEW backend modules + alembic 0055 +
  dry-run CLI + 24 NEW pytest PASS)
- cj-style 182: Phase 26 close-out retro (5 files docs-only)
- cj-style 183: Phase 26 audit_action EXTENSION sprint (12 NEW Literal +
  ActionClass.FINOPS_COST_ANOMALY_ML_PREDICTION + _REGISTRY entry, CR 1-1)
- cj-style 184 (this sprint): Phase 26 typed exceptions EXTENSION sprint —
  FinopsCostAnomalyMLPredictionError base + 16 NEW typed exception classes
  CR 12-5 D-14 envelope.

CR 11-3 honest-DEFER: prior sprints (181 + 182 + 183) honestly DEFER'd this
typed exceptions EXTENSION. This sprint is the honest recovery — 16 NEW
typed exception classes organized in 4 functional groups:

1. Cost Anomaly ML Prediction core (3 NEW):
   - AnomalyMLPredictionNotFoundError (HTTP 404)
   - AnomalyMLPredictionStatusTransitionError (HTTP 400)
   - AnomalyMLPredictionComplianceViolationError (HTTP 403)

2. Model Registry (4 NEW):
   - ModelRegistryEntryNotFoundError (HTTP 404)
   - ModelArtifactChecksumMismatchError (HTTP 422)
   - ModelStatusTransitionError (HTTP 400)
   - ModelArtifactSizeError (HTTP 413)

3. Model Training Pipeline (4 NEW):
   - ModelTrainingJobNotFoundError (HTTP 404)
   - ModelTrainingFailedError (HTTP 500)
   - ModelTrainingDataInsufficientError (HTTP 422)
   - ModelTrainingTimeoutError (HTTP 504)

4. Anomaly ML Scoring (5 NEW):
   - AnomalyMLScoringError (HTTP 500)
   - AnomalyMLInferenceTimeoutError (HTTP 504)
   - AnomalyMLFeatureExtractionError (HTTP 422)
   - AnomalyMLComparisonError (HTTP 500)
   - AnomalyMLEnsembleConsensusError (HTTP 500)

Module identifier: m34_finops_cost_anomaly_ml_prediction (FINOPS_COST_ANOMALY_ML_PREDICTION_MODULE_ID).

All exceptions inherit from FinopsCostAnomalyMLPredictionError which inherits
from FinopsError which inherits from BaseError. Envelope shape:
{code, message_ko, details, trace_id, module_id} CR 12-5 D-14 verbatim.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

import pytest

from apps.api.core.errors import (
    FINOPS_COST_ANOMALY_ML_PREDICTION_MODULE_ID,
    AnomalyMLComparisonError,
    AnomalyMLEnsembleConsensusError,
    AnomalyMLFeatureExtractionError,
    AnomalyMLInferenceTimeoutError,
    AnomalyMLPredictionComplianceViolationError,
    AnomalyMLPredictionNotFoundError,
    AnomalyMLPredictionStatusTransitionError,
    AnomalyMLScoringError,
    BaseError,
    FinopsCostAnomalyMLPredictionError,
    FinopsError,
    ModelArtifactChecksumMismatchError,
    ModelArtifactSizeError,
    ModelRegistryEntryNotFoundError,
    ModelStatusTransitionError,
    ModelTrainingDataInsufficientError,
    ModelTrainingFailedError,
    ModelTrainingJobNotFoundError,
    ModelTrainingTimeoutError,
    VendorPermissionError,
)


# ── 16 NEW pytest cases ──────────────────────────────────────
def test_finops_cost_anomaly_ml_prediction_module_id_registered() -> None:
    """Test 1: FINOPS_COST_ANOMALY_ML_PREDICTION_MODULE_ID = 'm34_finops_cost_anomaly_ml_prediction'."""
    assert FINOPS_COST_ANOMALY_ML_PREDICTION_MODULE_ID == "m34_finops_cost_anomaly_ml_prediction"


def test_finops_cost_anomaly_ml_prediction_error_base_registered() -> None:
    """Test 2: FinopsCostAnomalyMLPredictionError base class registered with module_id."""
    assert issubclass(FinopsCostAnomalyMLPredictionError, FinopsError)
    assert issubclass(FinopsCostAnomalyMLPredictionError, BaseError)
    assert FinopsCostAnomalyMLPredictionError.module_id == FINOPS_COST_ANOMALY_ML_PREDICTION_MODULE_ID
    assert FinopsCostAnomalyMLPredictionError.http_status == 500  # BaseError default


def test_anomaly_ml_prediction_not_found_error_registered() -> None:
    """Test 3: AnomalyMLPredictionNotFoundError = HTTP 404 (PRD §F42.4 lifecycle: created → updated → retired)."""
    assert issubclass(AnomalyMLPredictionNotFoundError, FinopsCostAnomalyMLPredictionError)
    assert AnomalyMLPredictionNotFoundError.http_status == 404
    assert AnomalyMLPredictionNotFoundError.module_id == FINOPS_COST_ANOMALY_ML_PREDICTION_MODULE_ID


def test_anomaly_ml_prediction_status_transition_error_registered() -> None:
    """Test 4: AnomalyMLPredictionStatusTransitionError = HTTP 400 (PRD §F42.4 lifecycle invariants)."""
    assert issubclass(AnomalyMLPredictionStatusTransitionError, FinopsCostAnomalyMLPredictionError)
    assert AnomalyMLPredictionStatusTransitionError.http_status == 400


def test_anomaly_ml_prediction_compliance_violation_error_registered() -> None:
    """Test 5: AnomalyMLPredictionComplianceViolationError = HTTP 403 (AD-55 (g) Epic 12 2FA 챌린지 mandatory)."""
    assert issubclass(AnomalyMLPredictionComplianceViolationError, FinopsCostAnomalyMLPredictionError)
    assert AnomalyMLPredictionComplianceViolationError.http_status == 403


def test_model_registry_entry_not_found_error_registered() -> None:
    """Test 6: ModelRegistryEntryNotFoundError = HTTP 404 (semver 0.1.0, AD-55 (b))."""
    assert issubclass(ModelRegistryEntryNotFoundError, FinopsCostAnomalyMLPredictionError)
    assert ModelRegistryEntryNotFoundError.http_status == 404


def test_model_artifact_checksum_mismatch_error_registered() -> None:
    """Test 7: ModelArtifactChecksumMismatchError = HTTP 422 (artifact integrity, AD-55 (b))."""
    assert issubclass(ModelArtifactChecksumMismatchError, FinopsCostAnomalyMLPredictionError)
    assert ModelArtifactChecksumMismatchError.http_status == 422


def test_model_status_transition_error_registered() -> None:
    """Test 8: ModelStatusTransitionError = HTTP 400 (5 lifecycle states, AD-55 (b))."""
    assert issubclass(ModelStatusTransitionError, FinopsCostAnomalyMLPredictionError)
    assert ModelStatusTransitionError.http_status == 400


def test_model_artifact_size_error_registered() -> None:
    """Test 9: ModelArtifactSizeError = HTTP 413 (100 MB max, AD-55 (b))."""
    assert issubclass(ModelArtifactSizeError, FinopsCostAnomalyMLPredictionError)
    assert ModelArtifactSizeError.http_status == 413


def test_model_training_job_not_found_error_registered() -> None:
    """Test 10: ModelTrainingJobNotFoundError = HTTP 404 (AD-55 (c))."""
    assert issubclass(ModelTrainingJobNotFoundError, FinopsCostAnomalyMLPredictionError)
    assert ModelTrainingJobNotFoundError.http_status == 404


def test_model_training_failed_error_registered() -> None:
    """Test 11: ModelTrainingFailedError = HTTP 500 (5 model types ensemble, AD-55 (c))."""
    assert issubclass(ModelTrainingFailedError, FinopsCostAnomalyMLPredictionError)
    assert ModelTrainingFailedError.http_status == 500


def test_model_training_data_insufficient_error_registered() -> None:
    """Test 12: ModelTrainingDataInsufficientError = HTTP 422 (8 features × 300 days, AD-55 (c))."""
    assert issubclass(ModelTrainingDataInsufficientError, FinopsCostAnomalyMLPredictionError)
    assert ModelTrainingDataInsufficientError.http_status == 422


def test_model_training_timeout_error_registered() -> None:
    """Test 13: ModelTrainingTimeoutError = HTTP 504 (3600s timeout, AD-55 (c))."""
    assert issubclass(ModelTrainingTimeoutError, FinopsCostAnomalyMLPredictionError)
    assert ModelTrainingTimeoutError.http_status == 504


def test_anomaly_ml_scoring_error_registered() -> None:
    """Test 14: AnomalyMLScoringError = HTTP 500 (3-attempt retry, AD-55 (d))."""
    assert issubclass(AnomalyMLScoringError, FinopsCostAnomalyMLPredictionError)
    assert AnomalyMLScoringError.http_status == 500


def test_anomaly_ml_inference_timeout_error_registered() -> None:
    """Test 15: AnomalyMLInferenceTimeoutError = HTTP 504 (200ms P95, AD-55 (d))."""
    assert issubclass(AnomalyMLInferenceTimeoutError, FinopsCostAnomalyMLPredictionError)
    assert AnomalyMLInferenceTimeoutError.http_status == 504


def test_anomaly_ml_feature_extraction_error_registered() -> None:
    """Test 16: AnomalyMLFeatureExtractionError = HTTP 422 (8 features, AD-55 (c))."""
    assert issubclass(AnomalyMLFeatureExtractionError, FinopsCostAnomalyMLPredictionError)
    assert AnomalyMLFeatureExtractionError.http_status == 422


def test_anomaly_ml_comparison_error_registered() -> None:
    """Test 17: AnomalyMLComparisonError = HTTP 500 (AnomalyScoreComparison 12 fields, AD-55 (d))."""
    assert issubclass(AnomalyMLComparisonError, FinopsCostAnomalyMLPredictionError)
    assert AnomalyMLComparisonError.http_status == 500


def test_anomaly_ml_ensemble_consensus_error_registered() -> None:
    """Test 18: AnomalyMLEnsembleConsensusError = HTTP 500 (5 model types ensemble, AD-55 (a))."""
    assert issubclass(AnomalyMLEnsembleConsensusError, FinopsCostAnomalyMLPredictionError)
    assert AnomalyMLEnsembleConsensusError.http_status == 500


def test_16_new_exception_classes_count() -> None:
    """Test 19: Phase 26 typed exceptions EXTENSION = 16 NEW subclasses registered."""
    expected_classes = {
        AnomalyMLPredictionNotFoundError,
        AnomalyMLPredictionStatusTransitionError,
        AnomalyMLPredictionComplianceViolationError,
        ModelRegistryEntryNotFoundError,
        ModelArtifactChecksumMismatchError,
        ModelStatusTransitionError,
        ModelArtifactSizeError,
        ModelTrainingJobNotFoundError,
        ModelTrainingFailedError,
        ModelTrainingDataInsufficientError,
        ModelTrainingTimeoutError,
        AnomalyMLScoringError,
        AnomalyMLInferenceTimeoutError,
        AnomalyMLFeatureExtractionError,
        AnomalyMLComparisonError,
        AnomalyMLEnsembleConsensusError,
    }
    actual_classes = {
        cls
        for cls in FinopsCostAnomalyMLPredictionError.__subclasses__()
        if cls in expected_classes
    }
    assert actual_classes == expected_classes, (
        f"Phase 26 typed exceptions EXTENSION drift detected: "
        f"missing={expected_classes - actual_classes}, "
        f"extra={actual_classes - expected_classes}"
    )


def test_no_overlap_with_finops_vendor_management_exceptions() -> None:
    """Test 20: Phase 26 typed exceptions are distinct from Phase 25 vendor management typed exceptions."""
    from apps.api.core.errors import FINOPS_VENDOR_MANAGEMENT_MODULE_ID, FinopsVendorManagementError
    phase_26_classes = set(FinopsCostAnomalyMLPredictionError.__subclasses__())
    phase_25_classes = set(FinopsVendorManagementError.__subclasses__())
    assert phase_26_classes.isdisjoint(phase_25_classes), (
        "Phase 26 cost anomaly ML prediction exceptions should not overlap "
        "with Phase 25 vendor management exceptions"
    )
    assert FINOPS_COST_ANOMALY_ML_PREDICTION_MODULE_ID != FINOPS_VENDOR_MANAGEMENT_MODULE_ID


def test_no_overlap_with_finops_anomaly_exceptions() -> None:
    """Test 21: Phase 26 ML prediction exceptions are distinct from Phase 12 rule-based anomaly exceptions."""
    from apps.api.core.errors import FINOPS_ANOMALY_MODULE_ID, FinopsAnomalyError
    phase_26_classes = set(FinopsCostAnomalyMLPredictionError.__subclasses__())
    phase_12_classes = set(FinopsAnomalyError.__subclasses__())
    assert phase_26_classes.isdisjoint(phase_12_classes), (
        "Phase 26 ML-driven prediction exceptions should be complementary "
        "(not overlap) with Phase 12 rule-based anomaly exceptions"
    )
    assert FINOPS_COST_ANOMALY_ML_PREDICTION_MODULE_ID != FINOPS_ANOMALY_MODULE_ID


def test_typed_exception_envelope_shape_preserved() -> None:
    """Test 22: CR 12-5 D-14 envelope shape `{code, message_ko, details, trace_id, module_id}` preserved."""
    error = AnomalyMLPredictionNotFoundError(
        message="prediction not found",
        message_ko="예측을 찾을 수 없습니다",
        details={"prediction_id": "pred-123"},
    )
    assert error.message == "prediction not found"
    assert error.message_ko == "예측을 찾을 수 없습니다"
    assert error.details == {"prediction_id": "pred-123"}
    assert error.code == "AnomalyMLPredictionNotFoundError"
    assert error.module_id == FINOPS_COST_ANOMALY_ML_PREDICTION_MODULE_ID
    assert error.http_status == 404
    assert isinstance(error.trace_id, str)
    assert len(error.trace_id) > 0


def test_typed_exception_module_id_propagation() -> None:
    """Test 23: All 16 NEW exceptions propagate module_id = FINOPS_COST_ANOMALY_ML_PREDICTION_MODULE_ID."""
    exception_classes = [
        AnomalyMLPredictionNotFoundError,
        AnomalyMLPredictionStatusTransitionError,
        AnomalyMLPredictionComplianceViolationError,
        ModelRegistryEntryNotFoundError,
        ModelArtifactChecksumMismatchError,
        ModelStatusTransitionError,
        ModelArtifactSizeError,
        ModelTrainingJobNotFoundError,
        ModelTrainingFailedError,
        ModelTrainingDataInsufficientError,
        ModelTrainingTimeoutError,
        AnomalyMLScoringError,
        AnomalyMLInferenceTimeoutError,
        AnomalyMLFeatureExtractionError,
        AnomalyMLComparisonError,
        AnomalyMLEnsembleConsensusError,
    ]
    for cls in exception_classes:
        assert cls.module_id == FINOPS_COST_ANOMALY_ML_PREDICTION_MODULE_ID, (
            f"{cls.__name__}.module_id = {cls.module_id}, "
            f"expected {FINOPS_COST_ANOMALY_ML_PREDICTION_MODULE_ID}"
        )


def test_typed_exception_caught_by_finops_error() -> None:
    """Test 24: All 16 NEW exceptions can be caught by `except FinopsError` block (CR 12-5 D-14)."""
    exception_classes = [
        AnomalyMLPredictionNotFoundError,
        AnomalyMLPredictionStatusTransitionError,
        AnomalyMLPredictionComplianceViolationError,
        ModelRegistryEntryNotFoundError,
        ModelArtifactChecksumMismatchError,
        ModelStatusTransitionError,
        ModelArtifactSizeError,
        ModelTrainingJobNotFoundError,
        ModelTrainingFailedError,
        ModelTrainingDataInsufficientError,
        ModelTrainingTimeoutError,
        AnomalyMLScoringError,
        AnomalyMLInferenceTimeoutError,
        AnomalyMLFeatureExtractionError,
        AnomalyMLComparisonError,
        AnomalyMLEnsembleConsensusError,
    ]
    for cls in exception_classes:
        with pytest.raises(FinopsError) as exc_info:
            raise cls(message="test", message_ko="테스트") from None
        assert exc_info.value.module_id == FINOPS_COST_ANOMALY_ML_PREDICTION_MODULE_ID
        assert exc_info.value.http_status > 0


def test_typed_exception_caught_by_base_error() -> None:
    """Test 25: All 16 NEW exceptions can be caught by `except BaseError` block (CR 11-4 P-015)."""
    exception_classes = [
        AnomalyMLPredictionNotFoundError,
        AnomalyMLPredictionStatusTransitionError,
        AnomalyMLPredictionComplianceViolationError,
        ModelRegistryEntryNotFoundError,
        ModelArtifactChecksumMismatchError,
        ModelStatusTransitionError,
        ModelArtifactSizeError,
        ModelTrainingJobNotFoundError,
        ModelTrainingFailedError,
        ModelTrainingDataInsufficientError,
        ModelTrainingTimeoutError,
        AnomalyMLScoringError,
        AnomalyMLInferenceTimeoutError,
        AnomalyMLFeatureExtractionError,
        AnomalyMLComparisonError,
        AnomalyMLEnsembleConsensusError,
    ]
    for cls in exception_classes:
        with pytest.raises(BaseError) as exc_info:
            raise cls(message="test", message_ko="테스트") from None
        assert exc_info.value.code == cls.__name__
        assert isinstance(exc_info.value.trace_id, str)


def test_typed_exception_distinct_from_phase25_vendor_permission() -> None:
    """Test 26: Phase 26 typed exceptions do not collide with Phase 25 VendorPermissionError (HTTP 403)."""
    # VendorPermissionError = HTTP 403 from Phase 25.
    # AnomalyMLPredictionComplianceViolationError = HTTP 403 from Phase 26.
    # Both are 403 but they are different classes with different module_ids.
    assert VendorPermissionError.http_status == 403
    assert AnomalyMLPredictionComplianceViolationError.http_status == 403
    assert VendorPermissionError.module_id == "m25_finops_vendor_management"
    assert AnomalyMLPredictionComplianceViolationError.module_id == FINOPS_COST_ANOMALY_ML_PREDICTION_MODULE_ID
