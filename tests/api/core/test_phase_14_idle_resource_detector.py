"""tests.api.core.test_phase_14_idle_resource_detector — Phase 14 idle resource detector tests.

Phase 14 (cj-style 119번째 wire) — FinOps Optimization & Rightsizing
territory (PRD §F30.3). 5 idle definitions + z-score detection + severity
classification + action recommendation.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

import uuid

import pytest

from apps.api.core.errors import (
    IdleMetricUnavailableError,
    IdleResourceDetectionError,
    IdleSeverityClassificationError,
)
from apps.api.modules.finops.idle_resource_detector import (
    ACTION_DOWNSIZE,
    ACTION_REVIEW,
    ACTION_TERMINATE,
    ALL_DETECTION_METHODS,
    ALL_IDLE_ACTIONS,
    ALL_IDLE_SEVERITIES,
    DETECTION_METHOD_Z_SCORE,
    IDLE_CPU_THRESHOLD_PCT,
    IDLE_DETECTION_WINDOW_DAYS,
    IDLE_SEVERITY_HIGH,
    IDLE_SEVERITY_LOW,
    IDLE_SEVERITY_MEDIUM,
    IDLE_Z_SCORE_THRESHOLD,
    SEVERITY_LOW_MAX_KRW,
    SEVERITY_MEDIUM_MAX_KRW,
    IdleResource,
    detect_idle_resources,
)
from apps.api.modules.finops.optimization_definition import (
    RESOURCE_TYPE_COMPUTE,
    RESOURCE_TYPE_DATABASE,
    RESOURCE_TYPE_NETWORK,
    RESOURCE_TYPE_STORAGE,
)

TENANT_ID: str = str(uuid.uuid4())


# ── 8 NEW pytest cases ──────────────────────────────────────
def test_z_score_threshold_and_severity_thresholds() -> None:
    """Test 1: z-score threshold -2.0 + severity thresholds."""
    assert IDLE_Z_SCORE_THRESHOLD == -2.0
    assert IDLE_CPU_THRESHOLD_PCT == 5.0
    assert IDLE_DETECTION_WINDOW_DAYS == 30
    assert SEVERITY_LOW_MAX_KRW == 10000
    assert SEVERITY_MEDIUM_MAX_KRW == 100000


def test_classify_idle_severity_boundaries() -> None:
    """Test 2: severity classification thresholds."""
    from apps.api.modules.finops.idle_resource_detector import (
        _classify_idle_severity,
    )
    assert _classify_idle_severity(5000.0) == IDLE_SEVERITY_LOW
    assert _classify_idle_severity(50000.0) == IDLE_SEVERITY_MEDIUM
    assert _classify_idle_severity(500000.0) == IDLE_SEVERITY_HIGH
    assert _classify_idle_severity(10000.0) == IDLE_SEVERITY_MEDIUM  # boundary
    assert _classify_idle_severity(100000.0) == IDLE_SEVERITY_HIGH  # boundary


def test_classify_action_by_severity() -> None:
    """Test 3: action recommendation per severity."""
    from apps.api.modules.finops.idle_resource_detector import (
        _classify_action,
    )
    assert _classify_action(IDLE_SEVERITY_LOW) == ACTION_REVIEW
    assert _classify_action(IDLE_SEVERITY_MEDIUM) == ACTION_DOWNSIZE
    assert _classify_action(IDLE_SEVERITY_HIGH) == ACTION_TERMINATE


def test_detect_idle_compute_low_cpu_classified_idle() -> None:
    """Test 4: compute idle detection (CPU < 5% for 30d)."""
    from apps.api.modules.finops.idle_resource_detector import (
        _detect_idle_compute,
    )
    result = _detect_idle_compute(
        tenant_id=TENANT_ID,
        resource_id="i-compute-idle",
        current_cost_krw_per_month=50000.0,
        cpu_utilization_p95=2.0,  # < 5% threshold
        memory_utilization_p95=8.0,
        network_in_bytes_p95=500_000,  # < 1MB
    )
    assert result is not None
    assert result["tenant_id"] == TENANT_ID
    assert result["resource_type"] == RESOURCE_TYPE_COMPUTE
    assert result["idle_severity"] == IDLE_SEVERITY_MEDIUM  # 50000 in medium range
    assert result["action"] == ACTION_DOWNSIZE
    assert result["detection_method"] == DETECTION_METHOD_Z_SCORE


def test_detect_idle_storage_unattached_ebs() -> None:
    """Test 5: storage idle detection unattached EBS volume."""
    from apps.api.modules.finops.idle_resource_detector import (
        _detect_idle_storage,
    )
    result = _detect_idle_storage(
        tenant_id=TENANT_ID,
        resource_id="vol-ebs-unattached",
        current_cost_krw_per_month=5000.0,
        last_accessed_days_ago=14,
        size_gb=20.0,
        attached=False,
    )
    assert result is not None
    assert result["resource_type"] == RESOURCE_TYPE_STORAGE
    assert result["idle_reason"] == "unattached"


def test_detect_idle_database_zero_connections() -> None:
    """Test 6: database idle detection (connection_count_p95=0 for 30d)."""
    from apps.api.modules.finops.idle_resource_detector import (
        _detect_idle_database,
    )
    result = _detect_idle_database(
        tenant_id=TENANT_ID,
        resource_id="db.r5.xlarge-idle",
        current_cost_krw_per_month=200000.0,
        connection_count_p95=0,
    )
    assert result is not None
    assert result["resource_type"] == RESOURCE_TYPE_DATABASE
    assert result["idle_reason"] == "zero_connections"
    assert result["idle_severity"] == IDLE_SEVERITY_HIGH  # 200000 > 100000


def test_detect_idle_network_unassociated_eip() -> None:
    """Test 7: network idle detection unassociated EIP."""
    from apps.api.modules.finops.idle_resource_detector import (
        _detect_idle_network,
    )
    result = _detect_idle_network(
        tenant_id=TENANT_ID,
        resource_id="eip-orphan",
        current_cost_krw_per_month=4500.0,
        eip_associated=False,
    )
    assert result is not None
    assert result["resource_type"] == RESOURCE_TYPE_NETWORK
    assert result["idle_reason"] == "unattached"
    assert result["action"] == ACTION_REVIEW  # < 10000 = low severity


def test_compute_z_score_calculation() -> None:
    """Test 8: z-score calculation (PRD §F30.3.8 verbatim)."""
    from apps.api.modules.finops.idle_resource_detector import (
        _compute_z_score,
    )
    # z_score = (util - mean) / std
    assert _compute_z_score(20.0, 50.0, 10.0) == -3.0  # idle
    assert _compute_z_score(50.0, 50.0, 10.0) == 0.0  # baseline
    assert _compute_z_score(70.0, 50.0, 10.0) == 2.0  # high
    assert _compute_z_score(30.0, 50.0, 0.0) == 0.0  # std=0 safe


# ── enum invariants ─────────────────────────────────────────
def test_enum_invariants() -> None:
    """Test 9: enum completeness + detection methods."""
    assert len(ALL_IDLE_SEVERITIES) == 3
    assert len(ALL_IDLE_ACTIONS) == 3
    assert len(ALL_DETECTION_METHODS) == 3
    assert IDLE_SEVERITY_LOW in ALL_IDLE_SEVERITIES
    assert IDLE_SEVERITY_MEDIUM in ALL_IDLE_SEVERITIES
    assert IDLE_SEVERITY_HIGH in ALL_IDLE_SEVERITIES
    assert ACTION_REVIEW in ALL_IDLE_ACTIONS
    assert ACTION_DOWNSIZE in ALL_IDLE_ACTIONS
    assert ACTION_TERMINATE in ALL_IDLE_ACTIONS
    assert DETECTION_METHOD_Z_SCORE in ALL_DETECTION_METHODS
    assert detect_idle_resources(tenant_id=TENANT_ID) == []
