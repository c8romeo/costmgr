"""tests.api.core.test_phase_14_rightsizing_engine — Phase 14 rightsizing engine tests.

Phase 14 (cj-style 119번째 wire) — FinOps Optimization & Rightsizing
territory (PRD §F30.2). 5 resource types + 80+ AWS EC2 instance type
mapping + projected_savings + confidence_score + audit-first INSERT.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

import uuid

import pytest

from apps.api.core.errors import (
    InstanceTypeMappingError,
    RecommendationConfidenceLowError,
    RightsizingEngineError,
)
from apps.api.modules.finops.rightsizing_engine import (
    ALL_INSTANCE_FAMILIES,
    ALL_SEVERITIES,
    ALL_STORAGE_TIERS,
    CONFIDENCE_LOW_THRESHOLD,
    CONFIDENCE_MEDIUM_THRESHOLD,
    INSTANCE_TYPE_DOWNGRADE_MAP,
    INSTANCE_TYPE_UPGRADE_MAP,
    RIGHTSIZING_ENGINE_MODEL_VERSION,
    STORAGE_TIER_DOWNGRADE_MAP,
    STORAGE_TIER_STANDARD,
    STORAGE_TIER_STANDARD_IA,
    STORAGE_TIER_GLACIER,
    RightsizingRecommendation,
    StorageRecommendation,
    recommend_rightsizing,
)
from apps.api.modules.finops.optimization_definition import (
    RESOURCE_TYPE_COMPUTE,
    RESOURCE_TYPE_CONTAINER,
    RESOURCE_TYPE_DATABASE,
    RESOURCE_TYPE_NETWORK,
    RESOURCE_TYPE_STORAGE,
)

TENANT_ID: str = str(uuid.uuid4())


# ── 8 NEW pytest cases ──────────────────────────────────────
def test_instance_type_downgrade_map_has_80_plus_entries() -> None:
    """Test 1: INSTANCE_TYPE_DOWNGRADE_MAP has 80+ AWS EC2 instance types."""
    assert len(INSTANCE_TYPE_DOWNGRADE_MAP) >= 80
    # Spot check 4 families
    assert "m5.large" in INSTANCE_TYPE_DOWNGRADE_MAP
    assert "c5.large" in INSTANCE_TYPE_DOWNGRADE_MAP
    assert "r5.large" in INSTANCE_TYPE_DOWNGRADE_MAP
    assert "i3.large" in INSTANCE_TYPE_DOWNGRADE_MAP


def test_compute_rightsizing_recommendation_shape() -> None:
    """Test 2: compute rightsizing produces valid RightsizingRecommendation."""
    from apps.api.modules.finops.rightsizing_engine import (
        _recommend_compute_rightsizing,
    )
    rec = _recommend_compute_rightsizing(
        tenant_id=TENANT_ID,
        resource_id="i-12345",
        current_instance_type="m5.2xlarge",
        current_cost_krw=200000.0,
        forecast_p99=0.65,
    )
    assert rec["tenant_id"] == TENANT_ID
    assert rec["resource_type"] == RESOURCE_TYPE_COMPUTE
    assert rec["current_instance_type"] == "m5.2xlarge"
    assert rec["recommended_instance_type"] == "m5.xlarge"
    assert rec["current_cost_krw"] == 200000.0
    assert rec["recommended_cost_krw"] == 100000.0
    assert rec["projected_savings_pct"] == 50.0
    assert rec["projected_savings_amount_krw"] == 100000.0
    assert 0.0 <= rec["confidence_score"] <= 100.0
    assert rec["recommendation_severity"] in ALL_SEVERITIES


def test_storage_rightsizing_recommendation_shape() -> None:
    """Test 3: storage rightsizing tier downgrade Standard → Standard-IA."""
    from apps.api.modules.finops.rightsizing_engine import (
        _recommend_storage_rightsizing,
    )
    rec = _recommend_storage_rightsizing(
        tenant_id=TENANT_ID,
        resource_id="bucket-prod",
        current_tier=STORAGE_TIER_STANDARD,
        current_cost_krw=100000.0,
    )
    assert rec["tenant_id"] == TENANT_ID
    assert rec["resource_type"] == RESOURCE_TYPE_STORAGE
    assert rec["current_tier"] == STORAGE_TIER_STANDARD
    assert rec["recommended_tier"] == STORAGE_TIER_STANDARD_IA
    assert rec["recommended_cost_krw"] == 55000.0  # 0.55 multiplier


def test_database_rightsizing_recommendation_shape() -> None:
    """Test 4: database rightsizing 3-metric based (connection + CPU + memory)."""
    from apps.api.modules.finops.rightsizing_engine import (
        _recommend_database_rightsizing,
    )
    rec = _recommend_database_rightsizing(
        tenant_id=TENANT_ID,
        resource_id="db.r5.2xlarge-1",
        current_instance_type="db.r5.2xlarge",
        current_cost_krw=400000.0,
        connection_count_p95=20,
        cpu_utilization_p95=15.0,
        memory_utilization_p95=25.0,
    )
    assert rec["resource_type"] == RESOURCE_TYPE_DATABASE
    assert rec["current_instance_type"] == "db.r5.2xlarge"
    assert rec["recommended_instance_type"] == "db.r5.xlarge"  # RDS downgrade via db.* mapping


def test_network_rightsizing_unattached_eip_recommend_terminate() -> None:
    """Test 5: network rightsizing unattached EIP → terminate recommendation."""
    from apps.api.modules.finops.rightsizing_engine import (
        _recommend_network_rightsizing,
    )
    rec = _recommend_network_rightsizing(
        tenant_id=TENANT_ID,
        resource_id="eip-1234",
        resource_subtype="eip",
        current_cost_krw=5000.0,
        eip_associated=False,
    )
    assert rec["resource_type"] == RESOURCE_TYPE_NETWORK
    assert rec["recommended_instance_type"] == "terminate"
    assert rec["recommended_cost_krw"] == 0.0
    assert rec["projected_savings_pct"] == 100.0


def test_container_rightsizing_downsizes_when_underutilized() -> None:
    """Test 6: container rightsizing EKS desired count reduction."""
    from apps.api.modules.finops.rightsizing_engine import (
        _recommend_container_rightsizing,
    )
    rec = _recommend_container_rightsizing(
        tenant_id=TENANT_ID,
        resource_id="eks-cluster-prod",
        desired_count=10,
        max_utilization_p95=20.0,  # 20% < 30% threshold → downsize
        current_cost_krw=1000000.0,
    )
    assert rec["resource_type"] == RESOURCE_TYPE_CONTAINER
    assert rec["current_instance_type"] == "eks:10"
    assert rec["recommended_instance_type"] == "eks:7"


def test_recommend_rightsizing_unknown_resource_type_raises() -> None:
    """Test 7: recommend_rightsizing rejects unknown resource_type."""
    with pytest.raises(RightsizingEngineError):
        recommend_rightsizing(
            tenant_id=TENANT_ID,
            resource_type="unknown_resource",
        )


def test_unknown_instance_type_raises_instance_type_mapping_error() -> None:
    """Test 8: unknown instance_type raises InstanceTypeMappingError."""
    from apps.api.modules.finops.rightsizing_engine import (
        _recommend_compute_rightsizing,
    )
    with pytest.raises(InstanceTypeMappingError):
        _recommend_compute_rightsizing(
            tenant_id=TENANT_ID,
            resource_id="i-bad",
            current_instance_type="unknown.instance.type",
            current_cost_krw=100.0,
            forecast_p99=0.5,
        )


# ── enum invariants ─────────────────────────────────────────
def test_enum_invariants_and_storage_tier_downgrade() -> None:
    """Test 9: enum invariants + storage tier downgrade chain."""
    assert len(ALL_SEVERITIES) == 3
    assert len(ALL_INSTANCE_FAMILIES) == 4
    assert len(ALL_STORAGE_TIERS) == 3
    assert CONFIDENCE_LOW_THRESHOLD == 70.0
    assert CONFIDENCE_MEDIUM_THRESHOLD == 90.0
    assert RIGHTSIZING_ENGINE_MODEL_VERSION == "1.0.0"
    # Storage tier downgrade chain
    assert STORAGE_TIER_DOWNGRADE_MAP[STORAGE_TIER_STANDARD] == STORAGE_TIER_STANDARD_IA
    assert STORAGE_TIER_DOWNGRADE_MAP[STORAGE_TIER_STANDARD_IA] == STORAGE_TIER_GLACIER
    assert STORAGE_TIER_DOWNGRADE_MAP[STORAGE_TIER_GLACIER] == STORAGE_TIER_GLACIER
    # Upgrade map is reverse of downgrade (auto-derived 1-step reverse)
    assert INSTANCE_TYPE_UPGRADE_MAP["m5.large"] == "m5.xlarge"
    assert INSTANCE_TYPE_UPGRADE_MAP["c5.large"] == "c5.xlarge"
