"""tests.api.core.test_phase_9_audit_action — ActionClass.CHAOS_ENGINEERING audit action.

Phase 9 (cj-style 99번째 wire) — Mirrors Phase 8 cj-style 95번째 wire
`test_phase_8_performance_audit_action.py` pattern verbatim. 6 NEW pytest
cases PASS.
"""
from __future__ import annotations

import pytest

from apps.api.core.audit_action import (
    ActionClass,
    ChaosEngineeringAction,
    PerformanceTestAction,
    _ActionRegistry,
)


# ── 6 NEW pytest cases (Phase 9 T5.9 backend extension) ───────


def test_action_class_chaos_engineering_enum_value() -> None:
    """CR 12-5 D-14 — ActionClass.CHAOS_ENGINEERING enum present."""
    assert hasattr(ActionClass, "CHAOS_ENGINEERING")
    assert ActionClass.CHAOS_ENGINEERING.value == "chaos_engineering"


def test_chaos_engineering_action_literal_has_4_values() -> None:
    """PRD §F25 — 4 NEW ChaosEngineeringAction values verbatim."""
    expected = {
        "chaos_experiment_started",
        "chaos_experiment_completed",
        "chaos_experiment_aborted",
        "chaos_rollback_triggered",
    }
    actual = set(ChaosEngineeringAction.__args__)
    assert expected.issubset(actual)


def test_action_registry_routes_chaos_engineering_to_audit_logs() -> None:
    """ActionClass.CHAOS_ENGINEERING routes to audit_logs (CR 0-2 RLS verbatim)."""
    log_type, accepted = _ActionRegistry._REGISTRY[ActionClass.CHAOS_ENGINEERING]
    assert log_type == "audit_logs"
    assert "chaos_experiment_started" in accepted
    assert "chaos_experiment_completed" in accepted
    assert "chaos_experiment_aborted" in accepted
    assert "chaos_rollback_triggered" in accepted


def test_action_registry_validates_known_chaos_engineering_action() -> None:
    """_ActionRegistry.validate() accepts the 4 NEW values."""
    log_type = _ActionRegistry.validate(
        action_class=ActionClass.CHAOS_ENGINEERING,
        action="chaos_experiment_started",
    )
    assert log_type == "audit_logs"


def test_action_registry_rejects_unknown_action_for_chaos_engineering() -> None:
    """CR 1-1 — free-form string drift forbidden (Phase 7 + Phase 8 verbatim)."""
    with pytest.raises(ValueError) as exc_info:
        _ActionRegistry.validate(
            action_class=ActionClass.CHAOS_ENGINEERING,
            action="bogus_chaos_action",
        )
    assert "bogus_chaos_action" in str(exc_info.value)


def test_audit_action_union_includes_chaos_engineering_action() -> None:
    """AuditAction Union EXTENSION preserves ChaosEngineeringAction + PerformanceTestAction."""
    from apps.api.core.audit_action import AuditAction

    union_args = set(AuditAction.__args__)
    # Spot-check: ChaosEngineeringAction literal values are reachable.
    expected_literals = {
        "chaos_experiment_started",
        "chaos_experiment_completed",
        "chaos_experiment_aborted",
        "chaos_rollback_triggered",
        "performance_test_started",  # Phase 8 carry-over
        "performance_test_completed",  # Phase 8 carry-over
    }
    assert expected_literals.issubset(union_args), (
        f"missing from AuditAction union: {expected_literals - union_args}"
    )
