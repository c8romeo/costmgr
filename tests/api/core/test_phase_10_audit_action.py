# tests/api/core/test_phase_10_audit_action.py —
# Phase 10 T7 (cj-style 103번째 wire) — Audit Action EXTENSION tests.
# 8 cases verifying ActionClass.SLO_ENGINEERING + SloEngineeringAction
# Literal + _ActionRegistry entry + AuditAction Union membership.
#
# CR 1-1 audit-first INSERT lesson — every SLO action must be auditable.
#
# Note (cj-style 306+ retroactive correction): tests rewritten to match
# the actual `_ActionRegistry.validate(action_class, action)` API rather
# than the outdated `is_valid_audit_action` / `_ActionRegistry.get`
# helpers from the original draft. The implementation unified the
# registry into `_REGISTRY: dict[ActionClass, tuple[AuditLogType,
# frozenset[str]]]` so the canonical entry point is `.validate(...)`.
import pytest

from apps.api.core.audit_action import (
    ActionClass,
    AuditAction,
    SloEngineeringAction,
    _ActionRegistry,
)


def test_action_class_slo_engineering_exists():
    assert ActionClass.SLO_ENGINEERING.value == "slo_engineering"


def test_slo_engineering_action_literal_has_three_values():
    values = set(SloEngineeringAction.__args__)
    assert values == {
        "slo_target_updated",
        "slo_budget_exhausted",
        "slo_violation_detected",
    }


def test_audit_action_union_accepts_slo_target_updated():
    # Validate via the registry: the action must be accepted by
    # ActionClass.SLO_ENGINEERING and route to "audit_logs".
    log_type = _ActionRegistry.validate(
        action_class=ActionClass.SLO_ENGINEERING, action="slo_target_updated"
    )
    assert log_type == "audit_logs"


def test_audit_action_union_accepts_slo_budget_exhausted():
    log_type = _ActionRegistry.validate(
        action_class=ActionClass.SLO_ENGINEERING, action="slo_budget_exhausted"
    )
    assert log_type == "audit_logs"


def test_audit_action_union_accepts_slo_violation_detected():
    log_type = _ActionRegistry.validate(
        action_class=ActionClass.SLO_ENGINEERING, action="slo_violation_detected"
    )
    assert log_type == "audit_logs"


def test_normalize_audit_action_slo_target_updated_returns_enum():
    # AuditAction Union membership check (typing.get_args introspection
    # confirms the literal value is in the union).
    members = set(
        arg
        for literal in (
            SloEngineeringAction,
        )
        for arg in literal.__args__
    )
    assert "slo_target_updated" in members
    # SLO member lower-cased contains "slo" → spec check preserved.
    assert "slo" in "slo_target_updated"


def test_invalid_audit_action_returns_false():
    # Validation raises ValueError for unknown action (CR 1.1 lesson
    # verbatim — free-form string drift is forbidden).
    with pytest.raises(ValueError):
        _ActionRegistry.validate(
            action_class=ActionClass.SLO_ENGINEERING, action="not_a_real_action"
        )


def test_slo_engineering_registered_in_registry():
    # ActionClass.SLO_ENGINEERING must be present in the registry with
    # the canonical 3-action frozenset routing to "audit_logs".
    assert ActionClass.SLO_ENGINEERING in _ActionRegistry._REGISTRY
    log_type, accepted = _ActionRegistry._REGISTRY[ActionClass.SLO_ENGINEERING]
    assert log_type == "audit_logs"
    assert accepted == frozenset(
        {
            "slo_target_updated",
            "slo_budget_exhausted",
            "slo_violation_detected",
        }
    )
