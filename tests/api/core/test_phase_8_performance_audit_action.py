"""tests.api.core.test_phase_8_performance_audit_action — ActionClass.PERFORMANCE_TEST audit action.

Mirrors Phase 7 cj-style 91번째 wire `test_phase_7_observability_audit_action.py`
pattern verbatim. 6 NEW pytest cases PASS.
"""
from __future__ import annotations

import pytest

from apps.api.core.audit_action import (
    ActionClass,
    ObservabilityAction,
    PerformanceTestAction,
    _ActionRegistry,
)


# ── 6 NEW pytest cases (Phase 8 T7.1 backend extension) ───────


def test_action_class_performance_test_enum_value() -> None:
    """CR 12-5 D-14 — ActionClass.PERFORMANCE_TEST enum present."""
    assert hasattr(ActionClass, "PERFORMANCE_TEST")
    assert ActionClass.PERFORMANCE_TEST.value == "performance_test"


def test_performance_test_action_literal_has_4_values() -> None:
    """PRD §F24 — 4 NEW PerformanceTestAction values verbatim."""
    expected = {
        "performance_test_started",
        "performance_test_completed",
        "p99_regression_detected",
        "cost_engine_benchmark_invalidated",
    }
    actual = set(PerformanceTestAction.__args__)
    assert expected.issubset(actual)


def test_action_registry_routes_performance_test_to_audit_logs() -> None:
    """ActionClass.PERFORMANCE_TEST routes to audit_logs (CR 0-2 RLS verbatim)."""
    log_type, accepted = _ActionRegistry._REGISTRY[ActionClass.PERFORMANCE_TEST]
    assert log_type == "audit_logs"
    assert "performance_test_started" in accepted
    assert "performance_test_completed" in accepted
    assert "p99_regression_detected" in accepted
    assert "cost_engine_benchmark_invalidated" in accepted


def test_action_registry_validates_known_performance_test_action() -> None:
    """_ActionRegistry.validate() accepts the 4 NEW values."""
    log_type = _ActionRegistry.validate(
        action_class=ActionClass.PERFORMANCE_TEST,
        action="performance_test_started",
    )
    assert log_type == "audit_logs"


def test_action_registry_rejects_unknown_action_for_performance_test() -> None:
    """CR 1-1 — free-form string drift forbidden (Phase 7 + Phase 6 verbatim)."""
    with pytest.raises(ValueError) as exc_info:
        _ActionRegistry.validate(
            action_class=ActionClass.PERFORMANCE_TEST,
            action="bogus_action",
        )
    assert "bogus_action" in str(exc_info.value)


def test_audit_action_union_includes_performance_test_action() -> None:
    """AuditAction Union EXTENSION preserves PerformanceTestAction + ObservabilityAction."""
    from apps.api.core.audit_action import AuditAction

    union_args = set(AuditAction.__args__)
    # Spot-check: PerformanceTestAction literal values are reachable.
    expected_literals = {
        "performance_test_started",
        "performance_test_completed",
        "p99_regression_detected",
        "cost_engine_benchmark_invalidated",
        "alert_fired",  # Phase 7 carry-over
        "trace_sampled",  # Phase 7 carry-over
    }
    assert expected_literals.issubset(union_args), (
        f"missing from AuditAction union: {expected_literals - union_args}"
    )
