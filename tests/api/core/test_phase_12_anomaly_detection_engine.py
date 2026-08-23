# tests/api/core/test_phase_12_anomaly_detection_engine.py —
# Phase 12 T6.5 (cj-style 111번째 wire) — Anomaly detection engine tests.
# 10 cases per cj-style Phase 11 Chargeback engine pattern verbatim mirror.
import pytest

from apps.api.core.errors import (
    AnomalyBaselineUnavailableError,
    AnomalyDetectionError,
)
from apps.api.modules.finops.anomaly_detection import (
    BASELINE_WINDOW_LAST_30D,
    DETECTION_METHOD_EWMA,
    DETECTION_METHOD_IQR,
    DETECTION_METHOD_ZSCORE,
    DIMENSION_DEPARTMENT,
    parse_anomaly_definition,
)
from apps.api.modules.finops.anomaly_detection_engine import (
    DETECTION_STATUS_CONFIRMED,
    DETECTION_STATUS_FALSE_POSITIVE,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    DetectionResult,
    run_anomaly_detection,
    _assign_severity,
    _iqr_method,
    _isolation_forest_method,
    _voting_consensus,
    _z_score_method,
)


_TENANT_ID = "11111111-1111-1111-1111-111111111111"


def _make_definition(**overrides):
    base = {
        "period_key": "2026-08",
        "dimension": DIMENSION_DEPARTMENT,
        "dimension_value": "DEPT-001",
        "threshold_method": DETECTION_METHOD_ZSCORE,
        "threshold_value": 3.0,
        "baseline_window": BASELINE_WINDOW_LAST_30D,
        "consecutive_periods_required": 3,
    }
    base.update(overrides)
    return parse_anomaly_definition(_TENANT_ID, base)


def test_z_score_method_clear_anomaly():
    """Z-score detects clear anomaly when observed is far from mean."""
    history = [100.0, 100.0, 100.0, 100.0, 100.0]
    assert _z_score_method(500.0, history, 3.0) is True


def test_z_score_method_no_anomaly_when_close():
    history = [100.0, 100.0, 100.0, 100.0, 100.0]
    assert _z_score_method(101.0, history, 3.0) is False


def test_z_score_baseline_unavailable_raises():
    with pytest.raises(AnomalyBaselineUnavailableError):
        _z_score_method(100.0, [100.0], 3.0)


def test_iqr_method_outlier_detected():
    history = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 200.0]
    assert _iqr_method(500.0, history, 1.5) is True


def test_iqr_baseline_unavailable_raises():
    with pytest.raises(AnomalyBaselineUnavailableError):
        _iqr_method(100.0, [100.0, 101.0, 102.0], 1.5)


def test_isolation_forest_outlier_detected():
    history = [100.0, 101.0, 102.0, 103.0, 104.0]
    assert _isolation_forest_method(500.0, history, 0.1) is True


def test_voting_consensus_3_of_4_confirms_anomaly():
    method_votes = {
        DETECTION_METHOD_ZSCORE: True,
        DETECTION_METHOD_IQR: True,
        DETECTION_METHOD_EWMA: True,
        "isolation_forest": False,
    }
    assert _voting_consensus(method_votes) is True


def test_voting_consensus_2_of_4_no_anomaly():
    method_votes = {
        DETECTION_METHOD_ZSCORE: True,
        DETECTION_METHOD_IQR: True,
        DETECTION_METHOD_EWMA: False,
        "isolation_forest": False,
    }
    assert _voting_consensus(method_votes) is False


def test_assign_severity_levels():
    assert _assign_severity(0.10) == SEVERITY_LOW
    assert _assign_severity(0.30) == SEVERITY_MEDIUM
    assert _assign_severity(0.70) == SEVERITY_HIGH
    assert _assign_severity(1.50) == SEVERITY_CRITICAL


def test_run_anomaly_detection_tenant_id_mismatch_raises():
    definition = _make_definition()
    with pytest.raises(AnomalyDetectionError):
        run_anomaly_detection(
            "22222222-2222-2222-2222-222222222222",
            "2026-08",
            definition,
            [100.0, 100.0, 100.0, 100.0],
            100.0,
        )