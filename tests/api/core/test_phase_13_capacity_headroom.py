"""tests.api.core.test_phase_13_capacity_headroom — Phase 13 capacity headroom tests.

Phase 13 (cj-style 115번째 wire) — 3 resource types + saturation levels.
"""
from __future__ import annotations

import uuid

import pytest

from apps.api.core.errors import (
    CapacityHeadroomAnalysisError,
    CapacityMetricUnavailableError,
)
from apps.api.modules.finops.capacity_headroom import (
    ALL_RESOURCE_TYPES,
    ALL_SATURATION_LEVELS,
    RESOURCE_PRIMARY_MODEL_MAP,
    SATURATION_CRITICAL,
    SATURATION_OK,
    SATURATION_WARNING,
    analyze_capacity_headroom,
)

TENANT_ID: str = str(uuid.uuid4())
HISTORY_30: list[float] = [60.0 + i * 0.5 for i in range(30)]


# ── 6 NEW pytest cases ──────────────────────────────────────
def test_all_resource_types_exhaustive() -> None:
    """Test 1: ALL_RESOURCE_TYPES has 3 options."""
    assert len(ALL_RESOURCE_TYPES) == 3
    assert ALL_RESOURCE_TYPES == ("compute", "storage", "network")


def test_resource_primary_model_map_correct() -> None:
    """Test 2: RESOURCE_PRIMARY_MODEL_MAP assigns primary model per resource."""
    assert RESOURCE_PRIMARY_MODEL_MAP["compute"] == "lstm"
    assert RESOURCE_PRIMARY_MODEL_MAP["storage"] == "prophet"
    assert RESOURCE_PRIMARY_MODEL_MAP["network"] == "arima"


def test_analyze_capacity_headroom_compute_ok() -> None:
    """Test 3: analyze_capacity_headroom returns ok for low utilization."""
    history = [20.0 for _ in range(30)]  # 20% utilization
    report = analyze_capacity_headroom(
        tenant_id=TENANT_ID,
        resource_type="compute",
        current_utilization_history=history,
    )
    assert report["saturation_level"] in ALL_SATURATION_LEVELS
    assert report["primary_model"] == "lstm"


def test_analyze_capacity_headroom_invalid_resource_raises() -> None:
    """Test 4: invalid resource_type raises CapacityHeadroomAnalysisError."""
    with pytest.raises(CapacityHeadroomAnalysisError):
        analyze_capacity_headroom(
            tenant_id=TENANT_ID,
            resource_type="invalid",
            current_utilization_history=HISTORY_30,
        )


def test_analyze_capacity_headroom_empty_history_raises() -> None:
    """Test 5: empty history raises CapacityMetricUnavailableError."""
    with pytest.raises(CapacityMetricUnavailableError):
        analyze_capacity_headroom(
            tenant_id=TENANT_ID,
            resource_type="compute",
            current_utilization_history=[],
        )


def test_analyze_capacity_headroom_dry_run() -> None:
    """Test 6: dry_run returns ok/0.0 saturation."""
    report = analyze_capacity_headroom(
        tenant_id=TENANT_ID,
        resource_type="storage",
        current_utilization_history=HISTORY_30,
        dry_run=True,
    )
    assert report["saturation_level"] == SATURATION_OK
    assert report["saturation_pct"] == 0.0