# tests/api/core/test_phase_10_audit_action.py —
# Phase 10 T7 (cj-style 103번째 wire) — Audit Action EXTENSION tests.
# 8 cases verifying ActionClass.SLO_ENGINEERING + SloEngineeringAction
# Literal + _ActionRegistry entry + AuditAction Union membership.
#
# CR 1-1 audit-first INSERT lesson — every SLO action must be auditable.
import pytest

from apps.api.core.audit_action import (
    ActionClass,
    AuditAction,
    SloEngineeringAction,
    is_valid_audit_action,
    normalize_audit_action,
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
    action: AuditAction = "slo_target_updated"
    assert is_valid_audit_action(action) is True


def test_audit_action_union_accepts_slo_budget_exhausted():
    action: AuditAction = "slo_budget_exhausted"
    assert is_valid_audit_action(action) is True


def test_audit_action_union_accepts_slo_violation_detected():
    action: AuditAction = "slo_violation_detected"
    assert is_valid_audit_action(action) is True


def test_normalize_audit_action_slo_target_updated_returns_enum():
    normalized = normalize_audit_action("slo_target_updated")
    assert normalized is not None
    assert "slo" in str(normalized).lower()


def test_invalid_audit_action_returns_false():
    assert is_valid_audit_action("not_a_real_action") is False


def test_slo_engineering_registered_in_registry():
    from apps.api.core.audit_action import _ActionRegistry

    slo_actions = _ActionRegistry.get(ActionClass.SLO_ENGINEERING)
    assert slo_actions is not None
    assert slo_actions == {
        frozenset({"slo_target_updated"}),
        frozenset({"slo_budget_exhausted"}),
        frozenset({"slo_violation_detected"}),
    }
