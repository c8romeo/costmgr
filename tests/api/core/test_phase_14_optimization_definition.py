"""tests.api.core.test_phase_14_optimization_definition — Phase 14 optimization definition tests.

Phase 14 (cj-style 119번째 wire) — FinOps Optimization & Rightsizing
territory (PRD §F30.1). ACTIONABLE RECOMMENDATION LAYER EXTENSION.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

import uuid

import pytest

from apps.api.core.errors import (
    OptimizationDefinitionInvalidError,
    OptimizationScopeInvalidError,
)
from apps.api.modules.finops.optimization_definition import (
    ALL_BASELINE_PERIODS,
    ALL_OPTIMIZATION_STRATEGIES,
    ALL_OPTIMIZATION_STATUSES,
    ALL_RESOURCE_TYPES,
    ALL_TARGET_METRICS,
    OPTIMIZATION_DEFAULTS,
    OptimizationDefinition,
    define_optimization,
    parse_optimization_definition,
)

TENANT_ID: str = str(uuid.uuid4())


# ── 6 NEW pytest cases ──────────────────────────────────────
def test_define_optimization_default_returns_valid_definition() -> None:
    """Test 1: define_optimization with defaults returns valid definition."""
    definition = define_optimization(tenant_id=TENANT_ID)
    assert isinstance(definition, dict)
    assert definition["tenant_id"] == TENANT_ID
    assert definition["resource_type"] == OPTIMIZATION_DEFAULTS.RESOURCE_TYPE
    assert definition["optimization_strategy"] == OPTIMIZATION_DEFAULTS.OPTIMIZATION_STRATEGY
    assert definition["target_metric"] == OPTIMIZATION_DEFAULTS.TARGET_METRIC
    assert definition["baseline_period"] == OPTIMIZATION_DEFAULTS.BASELINE_PERIOD
    assert definition["status"] == "active"
    assert "optimization_id" in definition
    assert "created_at" in definition
    assert "trace_id" in definition
    assert "metadata" in definition


def test_parse_optimization_definition_validates_required_fields() -> None:
    """Test 2: parse_optimization_definition enforces 6 required fields."""
    with pytest.raises(OptimizationDefinitionInvalidError):
        parse_optimization_definition(TENANT_ID, {})


def test_parse_optimization_definition_validates_resource_type() -> None:
    """Test 3: parse_optimization_definition enforces resource_type enum (5 options)."""
    with pytest.raises(OptimizationScopeInvalidError):
        parse_optimization_definition(
            TENANT_ID,
            {
                "resource_type": "invalid_resource",
                "optimization_strategy": "composite",
                "target_metric": "cost_saving_pct",
                "baseline_period": "last_30d",
                "status": "active",
            },
        )


def test_parse_optimization_definition_validates_optimization_strategy() -> None:
    """Test 4: parse_optimization_definition enforces optimization_strategy enum (7 options)."""
    with pytest.raises(OptimizationDefinitionInvalidError):
        parse_optimization_definition(
            TENANT_ID,
            {
                "resource_type": "compute",
                "optimization_strategy": "unknown_strategy",
                "target_metric": "cost_saving_pct",
                "baseline_period": "last_30d",
                "status": "active",
            },
        )


def test_parse_optimization_definition_validates_baseline_period_and_target_metric() -> None:
    """Test 5: parse_optimization_definition enforces baseline_period + target_metric enums."""
    with pytest.raises(OptimizationDefinitionInvalidError):
        parse_optimization_definition(
            TENANT_ID,
            {
                "resource_type": "compute",
                "optimization_strategy": "composite",
                "target_metric": "invalid_target_metric",
                "baseline_period": "last_30d",
                "status": "active",
            },
        )
    with pytest.raises(OptimizationDefinitionInvalidError):
        parse_optimization_definition(
            TENANT_ID,
            {
                "resource_type": "compute",
                "optimization_strategy": "composite",
                "target_metric": "cost_saving_pct",
                "baseline_period": "last_3d",  # invalid (not in 5 options)
                "status": "active",
            },
        )


def test_parse_optimization_definition_validates_status_and_tenant_id() -> None:
    """Test 6: parse_optimization_definition enforces status enum + tenant_id UUID format."""
    with pytest.raises(OptimizationDefinitionInvalidError):
        parse_optimization_definition(
            TENANT_ID,
            {
                "resource_type": "compute",
                "optimization_strategy": "composite",
                "target_metric": "cost_saving_pct",
                "baseline_period": "last_30d",
                "status": "unknown_status",
            },
        )
    with pytest.raises(OptimizationDefinitionInvalidError):
        parse_optimization_definition(
            "not-a-uuid",
            {
                "resource_type": "compute",
                "optimization_strategy": "composite",
                "target_metric": "cost_saving_pct",
                "baseline_period": "last_30d",
                "status": "active",
            },
        )


# ── enum completeness invariants ─────────────────────────────
def test_enum_completeness_invariants() -> None:
    """Test 7: All enum invariants + composite default present."""
    assert len(ALL_RESOURCE_TYPES) == 5
    assert len(ALL_OPTIMIZATION_STRATEGIES) == 7  # 6 + 1 composite
    assert "composite" in ALL_OPTIMIZATION_STRATEGIES
    assert len(ALL_TARGET_METRICS) == 4
    assert len(ALL_BASELINE_PERIODS) == 5
    assert len(ALL_OPTIMIZATION_STATUSES) == 3
    # defaults match spec
    assert OPTIMIZATION_DEFAULTS.RESOURCE_TYPE == "compute"
    assert OPTIMIZATION_DEFAULTS.OPTIMIZATION_STRATEGY == "composite"
    assert OPTIMIZATION_DEFAULTS.TARGET_METRIC == "cost_saving_pct"
    assert OPTIMIZATION_DEFAULTS.BASELINE_PERIOD == "last_30d"
    assert OPTIMIZATION_DEFAULTS.IDLE_CPU_THRESHOLD_PCT == 5.0
    assert OPTIMIZATION_DEFAULTS.IDLE_DETECTION_WINDOW_DAYS == 30
    assert OPTIMIZATION_DEFAULTS.MIN_SAVINGS_AMOUNT_KRW == 10000
    assert OPTIMIZATION_DEFAULTS.COMMIT_BREAK_EVEN_MONTHS_1Y == 8
    assert OPTIMIZATION_DEFAULTS.COMMIT_BREAK_EVEN_MONTHS_3Y == 18
    # TypedDict shape (TypedDict doesn't support isinstance in Python 3.10+)
    definition = define_optimization(tenant_id=TENANT_ID)
    assert isinstance(definition, dict)
    assert len(definition) == 11
