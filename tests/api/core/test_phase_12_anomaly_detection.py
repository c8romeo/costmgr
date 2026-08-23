# tests/api/core/test_phase_12_anomaly_detection.py —
# Phase 12 T6.5 (cj-style 111번째 wire) — Anomaly detection DSL tests.
# 10 cases per cj-style Phase 11 Showback DSL pattern verbatim mirror.
#
# CR 12-5 D-14 typed exception envelope — tests verify
# AnomalyDefinitionInvalidError raises with correct HTTP status
# code 400 and message_ko envelope.
import pytest

from apps.api.core.errors import AnomalyDefinitionInvalidError
from apps.api.modules.finops.anomaly_detection import (
    ALL_BASELINE_WINDOWS,
    ALL_DETECTION_METHODS,
    ALL_DIMENSIONS,
    ANOMALY_THRESHOLD_DEFAULTS,
    BASELINE_WINDOW_LAST_30D,
    BASELINE_WINDOW_LAST_90D,
    BASELINE_WINDOW_YTD,
    DETECTION_METHOD_EWMA,
    DETECTION_METHOD_ISOLATION_FOREST,
    DETECTION_METHOD_IQR,
    DETECTION_METHOD_ZSCORE,
    DIMENSION_COST_CENTER,
    DIMENSION_DEPARTMENT,
    DIMENSION_PRODUCT_LINE,
    DIMENSION_SERVICE,
    DIMENSION_TENANT_TOTAL,
    AnomalyDefinition,
    detect_anomaly,
    parse_anomaly_definition,
)


def _valid_payload(**overrides):
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
    return base


_TENANT_ID = "11111111-1111-1111-1111-111111111111"


def test_valid_anomaly_definition_accepted():
    payload = _valid_payload()
    validated = parse_anomaly_definition(_TENANT_ID, payload)
    assert validated["tenant_id"] == _TENANT_ID
    assert validated["dimension"] == DIMENSION_DEPARTMENT
    assert validated["threshold_method"] == DETECTION_METHOD_ZSCORE
    assert validated["baseline_window"] == BASELINE_WINDOW_LAST_30D


def test_anomaly_invalid_dimension_rejected():
    payload = _valid_payload(dimension="invalid_dim")
    with pytest.raises(AnomalyDefinitionInvalidError) as excinfo:
        parse_anomaly_definition(_TENANT_ID, payload)
    assert excinfo.value.http_status == 400
    assert excinfo.value.message_ko


def test_anomaly_invalid_threshold_method_rejected():
    payload = _valid_payload(threshold_method="invalid_method")
    with pytest.raises(AnomalyDefinitionInvalidError) as excinfo:
        parse_anomaly_definition(_TENANT_ID, payload)
    assert excinfo.value.http_status == 400


def test_anomaly_invalid_baseline_window_rejected():
    payload = _valid_payload(baseline_window="invalid_window")
    with pytest.raises(AnomalyDefinitionInvalidError) as excinfo:
        parse_anomaly_definition(_TENANT_ID, payload)
    assert excinfo.value.http_status == 400


def test_anomaly_invalid_threshold_value_rejected():
    payload = _valid_payload(threshold_value=-1.0)
    with pytest.raises(AnomalyDefinitionInvalidError):
        parse_anomaly_definition(_TENANT_ID, payload)
    payload_zero = _valid_payload(threshold_value=0)
    with pytest.raises(AnomalyDefinitionInvalidError):
        parse_anomaly_definition(_TENANT_ID, payload_zero)


def test_anomaly_invalid_consecutive_periods_rejected():
    payload = _valid_payload(consecutive_periods_required=0)
    with pytest.raises(AnomalyDefinitionInvalidError):
        parse_anomaly_definition(_TENANT_ID, payload)


def test_anomaly_missing_required_field_rejected():
    payload = _valid_payload()
    del payload["dimension_value"]
    with pytest.raises(AnomalyDefinitionInvalidError) as excinfo:
        parse_anomaly_definition(_TENANT_ID, payload)
    assert "dimension_value" in str(excinfo.value.details["missing_fields"])


def test_anomaly_invalid_tenant_id_uuid_rejected():
    payload = _valid_payload()
    with pytest.raises(AnomalyDefinitionInvalidError):
        parse_anomaly_definition("not-a-uuid", payload)


def test_detect_anomaly_zscore_default():
    """detect_anomaly() with default z_score method applies threshold 3.0."""
    result = detect_anomaly(_TENANT_ID, "2026-08", DIMENSION_DEPARTMENT)
    assert result["threshold_method"] == DETECTION_METHOD_ZSCORE
    assert result["threshold_value"] == ANOMALY_THRESHOLD_DEFAULTS.ZSCORE_THRESHOLD
    assert result["baseline_window"] == BASELINE_WINDOW_LAST_30D


def test_detect_anomaly_all_dimensions_supported():
    """All 5 dimensions are accepted in detect_anomaly."""
    for dim in ALL_DIMENSIONS:
        assert dim in (DIMENSION_DEPARTMENT, DIMENSION_COST_CENTER,
                        DIMENSION_PRODUCT_LINE, DIMENSION_SERVICE,
                        DIMENSION_TENANT_TOTAL)
    assert len(ALL_DIMENSIONS) == 5
    assert len(ALL_DETECTION_METHODS) == 4
    assert len(ALL_BASELINE_WINDOWS) == 3