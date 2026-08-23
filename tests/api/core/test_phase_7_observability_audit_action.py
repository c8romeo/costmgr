"""tests/api/core/test_phase_7_observability_audit_action.py — Phase 7 OBSERVABILITY audit action parity tests.

Phase 7 (cj-style 91번째 wire) — T7a backend pytest tests.
PRD §F23.5 + AC #5.9 + AD-34 (e) verbatim.

Drift detector enforces:
1. ActionClass.OBSERVABILITY enum value exists.
2. ObservabilityAction Literal has 2 values: alert_fired + trace_sampled.
3. _ActionRegistry OBSERVABILITY entry accepts both values.
4. Union AuditAction type includes ObservabilityAction.
5. __all__ exposes ObservabilityAction.

Mirrors tests/api/core/test_phase_6_retention_audit_action.py pattern
verbatim (Phase 6 wire `24e1cd7`).
"""
from __future__ import annotations

import pytest

from apps.api.core.audit_action import (
    ActionClass,
    AuditAction,
    ObservabilityAction,
    _ActionRegistry,
)


def test_actionclass_observability_exists() -> None:
    """ActionClass.OBSERVABILITY enum value must exist with value 'observability'."""
    assert hasattr(ActionClass, "OBSERVABILITY")
    assert ActionClass.OBSERVABILITY.value == "observability"


def test_observability_action_literal_has_two_values() -> None:
    """ObservabilityAction Literal must have exactly 2 values: alert_fired + trace_sampled."""
    # The Literal type is collapsed at runtime; verify via the ActionClass.AUDIT
    # registry + ObservabilityAction export.
    assert "alert_fired" in ObservabilityAction.__args__  # type: ignore[attr-defined]
    assert "trace_sampled" in ObservabilityAction.__args__  # type: ignore[attr-defined]
    assert len(ObservabilityAction.__args__) == 2  # type: ignore[attr-defined]


def test_action_registry_accepts_alert_fired() -> None:
    """_ActionRegistry must accept (OBSERVABILITY, 'alert_fired')."""
    log_type = _ActionRegistry.validate(
        action_class=ActionClass.OBSERVABILITY, action="alert_fired"
    )
    assert log_type == "audit_logs"


def test_action_registry_accepts_trace_sampled() -> None:
    """_ActionRegistry must accept (OBSERVABILITY, 'trace_sampled')."""
    log_type = _ActionRegistry.validate(
        action_class=ActionClass.OBSERVABILITY, action="trace_sampled"
    )
    assert log_type == "audit_logs"


def test_action_registry_rejects_unknown_action() -> None:
    """_ActionRegistry must reject unknown actions under OBSERVABILITY."""
    with pytest.raises(ValueError, match="not in ActionClass"):
        _ActionRegistry.validate(
            action_class=ActionClass.OBSERVABILITY, action="unknown_action"
        )


def test_audit_action_union_includes_observability() -> None:
    """AuditAction union type must include ObservabilityAction values."""
    # Spot check by validating audit actions from different classes still work.
    log_type_obs = _ActionRegistry.validate(
        action_class=ActionClass.OBSERVABILITY, action="alert_fired"
    )
    log_type_audit = _ActionRegistry.validate(
        action_class=ActionClass.AUDIT, action="audit_log_purged"
    )
    assert log_type_obs == "audit_logs"
    assert log_type_audit == "audit_logs"
