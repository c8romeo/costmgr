"""tests.api.core.test_phase_11_audit_action — ActionClass.FINOPS audit action.

Phase 11 (cj-style 107번째 wire) — Mirrors Phase 10 cj-style 103번째
wire `test_phase_10_audit_action.py` pattern verbatim. 6 NEW pytest
cases PASS.
"""
from __future__ import annotations

import pytest

from apps.api.core.audit_action import (
    ActionClass,
    AuditAction,
    FinopsAction,
    SloEngineeringAction,
    _ActionRegistry,
)


# ── 6 NEW pytest cases (Phase 11 T6 backend extension) ──────────


def test_action_class_finops_enum_value() -> None:
    """CR 12-5 D-14 — ActionClass.FINOPS enum present."""
    assert hasattr(ActionClass, "FINOPS")
    assert ActionClass.FINOPS.value == "finops"


def test_finops_action_literal_has_4_values() -> None:
    """PRD §F27 — 4 NEW FinopsAction values verbatim."""
    expected = {
        "showback_generated",
        "department_mapping_updated",
        "chargeback_calculated",
        "chargeback_exported",
    }
    actual = set(FinopsAction.__args__)
    assert expected.issubset(actual)


def test_action_registry_routes_finops_to_audit_logs() -> None:
    """ActionClass.FINOPS routes to audit_logs (CR 0-2 RLS verbatim)."""
    log_type, accepted = _ActionRegistry._REGISTRY[ActionClass.FINOPS]
    assert log_type == "audit_logs"
    assert "showback_generated" in accepted
    assert "department_mapping_updated" in accepted
    assert "chargeback_calculated" in accepted
    assert "chargeback_exported" in accepted


def test_action_registry_validates_known_finops_action() -> None:
    """_ActionRegistry.validate() accepts the 4 NEW values."""
    log_type = _ActionRegistry.validate(
        action_class=ActionClass.FINOPS,
        action="showback_generated",
    )
    assert log_type == "audit_logs"

    log_type = _ActionRegistry.validate(
        action_class=ActionClass.FINOPS,
        action="chargeback_exported",
    )
    assert log_type == "audit_logs"


def test_action_registry_rejects_unknown_action_for_finops() -> None:
    """CR 1-1 — free-form string drift forbidden (Phase 9 + 10 verbatim)."""
    with pytest.raises(ValueError) as exc_info:
        _ActionRegistry.validate(
            action_class=ActionClass.FINOPS,
            action="bogus_finops_action",
        )
    assert "bogus_finops_action" in str(exc_info.value)


def test_audit_action_union_includes_finops_action() -> None:
    """AuditAction Union EXTENSION preserves FinopsAction + SloEngineeringAction.

    Flattens the union recursively via typing.get_args to extract all
    concrete string literals — comparing strings directly against
    `AuditAction.__args__` (Literal types) is always False.
    """
    import typing

    def _flatten_literals(tp: object) -> set[str]:
        out: set[str] = set()
        for arg in typing.get_args(tp):
            if isinstance(arg, str):
                out.add(arg)
            else:
                out.update(_flatten_literals(arg))
        return out

    union_args = _flatten_literals(AuditAction)
    expected_literals = {
        "showback_generated",
        "department_mapping_updated",
        "chargeback_calculated",
        "chargeback_exported",
        # Phase 10 carry-over
        "slo_target_updated",
        "slo_budget_exhausted",
        "slo_violation_detected",
    }
    assert expected_literals.issubset(union_args), (
        f"missing from AuditAction union: {expected_literals - union_args}"
    )
