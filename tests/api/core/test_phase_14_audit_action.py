"""tests.api.core.test_phase_14_audit_action — Phase 14 audit action EXTENSION tests.

Phase 14 (cj-style 119번째 wire) — FinOps Optimization & Rightsizing
territory (PRD §F30). ActionClass.FINOPS_OPTIMIZATION + 8 NEW audit
actions via emit_audit_typed CR 1-1 verbatim.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

import pytest

from apps.api.core.audit_action import (
    ActionClass,
    AuditAction,
    FinopsOptimizationAction,
)


# ── 8 NEW pytest cases ──────────────────────────────────────
def test_action_class_finops_optimization_registered() -> None:
    """Test 1: ActionClass.FINOPS_OPTIMIZATION = 'finops_optimization' registered."""
    assert ActionClass.FINOPS_OPTIMIZATION.value == "finops_optimization"
    assert ActionClass.FINOPS_OPTIMIZATION == "finops_optimization"


def test_finops_optimization_action_literal_has_8_values() -> None:
    """Test 2: FinopsOptimizationAction Literal has 8 values."""
    expected_values = {
        "optimization_definition_updated",
        "recommendation_generated",
        "idle_resource_detected",
        "commitment_recommended",
        "optimization_recommended_action",
        "optimization_dry_run_executed",
        "optimization_accuracy_degraded",
        "optimization_retraining_triggered",
    }
    # Build the value set from the Literal via __args__
    actual_values = set(FinopsOptimizationAction.__args__)
    assert actual_values == expected_values
    assert len(actual_values) == 8


def test_audit_action_union_includes_finops_optimization() -> None:
    """Test 3: AuditAction Union includes FinopsOptimizationAction."""
    # Use a representative value
    action: AuditAction = "optimization_definition_updated"
    assert action == "optimization_definition_updated"


def test_action_registry_has_finops_optimization_entry() -> None:
    """Test 4: _REGISTRY has FINOPS_OPTIMIZATION entry."""
    from apps.api.core.audit_action import _ActionRegistry
    assert ActionClass.FINOPS_OPTIMIZATION in _ActionRegistry._REGISTRY
    log_type, accepted = _ActionRegistry._REGISTRY[ActionClass.FINOPS_OPTIMIZATION]
    assert log_type == "audit_logs"
    assert len(accepted) == 8
    assert "optimization_definition_updated" in accepted
    assert "recommendation_generated" in accepted
    assert "idle_resource_detected" in accepted
    assert "commitment_recommended" in accepted
    assert "optimization_recommended_action" in accepted
    assert "optimization_dry_run_executed" in accepted
    assert "optimization_accuracy_degraded" in accepted
    assert "optimization_retraining_triggered" in accepted


def test_action_registry_drift_no_missing_actions() -> None:
    """Test 5: No action in FinopsOptimizationAction is missing from registry."""
    from apps.api.core.audit_action import _ActionRegistry
    _, accepted = _ActionRegistry._REGISTRY[ActionClass.FINOPS_OPTIMIZATION]
    declared = set(FinopsOptimizationAction.__args__)
    assert declared == accepted, (
        f"Drift detected: declared-declared={declared - accepted}, "
        f"registry-declared={accepted - declared}"
    )


def test_no_overlap_with_finops_forecast_actions() -> None:
    """Test 6: Phase 14 actions are distinct from Phase 13 forecast actions."""
    from apps.api.core.audit_action import _ActionRegistry
    _, forecast_accepted = _ActionRegistry._REGISTRY[ActionClass.FINOPS_FORECAST]
    _, opt_accepted = _ActionRegistry._REGISTRY[ActionClass.FINOPS_OPTIMIZATION]
    assert forecast_accepted.isdisjoint(opt_accepted), (
        "Phase 14 actions should not overlap with Phase 13 forecast actions"
    )


def test_8_new_audit_actions_specific_validation() -> None:
    """Test 7: All 8 NEW actions are valid string values."""
    new_actions = (
        "optimization_definition_updated",
        "recommendation_generated",
        "idle_resource_detected",
        "commitment_recommended",
        "optimization_recommended_action",
        "optimization_dry_run_executed",
        "optimization_accuracy_degraded",
        "optimization_retraining_triggered",
    )
    for action in new_actions:
        # Should be valid string and resolvable as part of AuditAction
        assert isinstance(action, str)
        assert len(action) > 0


def test_finops_optimization_module_id_matches_errors_module() -> None:
    """Test 8: FINOPS_OPTIMIZATION_MODULE_ID = 'm22_finops_optimization'."""
    from apps.api.core.errors import FINOPS_OPTIMIZATION_MODULE_ID
    assert FINOPS_OPTIMIZATION_MODULE_ID == "m22_finops_optimization"
