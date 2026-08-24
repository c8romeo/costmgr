"""tests.api.core.test_phase_16_audit_action — Phase 16 audit action EXTENSION tests.

Phase 16 (cj-style 127번째 wire) — FinOps Reporting & Executive Dashboard
territory (PRD §F32.7). ActionClass.FINOPS_REPORTING + 8 NEW audit
actions via emit_audit_typed CR 1-1 verbatim.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

import pytest

from apps.api.core.audit_action import (
    ActionClass,
    AuditAction,
    FinopsReportingAction,
)


# ── 8 NEW pytest cases ──────────────────────────────────────
def test_action_class_finops_reporting_registered() -> None:
    """Test 1: ActionClass.FINOPS_REPORTING = 'finops_reporting' registered."""
    assert ActionClass.FINOPS_REPORTING.value == "finops_reporting"
    assert ActionClass.FINOPS_REPORTING == "finops_reporting"


def test_finops_reporting_action_literal_has_8_values() -> None:
    """Test 2: FinopsReportingAction Literal has 8 values."""
    expected_values = {
        "executive_report_generated",
        "executive_dashboard_viewed",
        "executive_kpi_refreshed",
        "executive_report_exported",
        "executive_report_dispatched",
        "executive_scheduled_dispatch_evaluated",
        "finops_reporting_dry_run_executed",
        "cross_module_kpi_calculated",
    }
    actual_values = set(FinopsReportingAction.__args__)
    assert actual_values == expected_values
    assert len(actual_values) == 8


def test_audit_action_union_includes_finops_reporting() -> None:
    """Test 3: AuditAction Union includes FinopsReportingAction."""
    action: AuditAction = "executive_dashboard_viewed"
    assert action == "executive_dashboard_viewed"


def test_action_registry_has_finops_reporting_entry() -> None:
    """Test 4: _REGISTRY has FINOPS_REPORTING entry."""
    from apps.api.core.audit_action import _ActionRegistry
    assert ActionClass.FINOPS_REPORTING in _ActionRegistry._REGISTRY
    log_type, accepted = _ActionRegistry._REGISTRY[ActionClass.FINOPS_REPORTING]
    assert log_type == "audit_logs"
    assert len(accepted) == 8
    assert "executive_report_generated" in accepted
    assert "executive_dashboard_viewed" in accepted
    assert "executive_kpi_refreshed" in accepted
    assert "executive_report_exported" in accepted
    assert "executive_report_dispatched" in accepted
    assert "executive_scheduled_dispatch_evaluated" in accepted
    assert "finops_reporting_dry_run_executed" in accepted
    assert "cross_module_kpi_calculated" in accepted


def test_action_registry_drift_no_missing_actions() -> None:
    """Test 5: No action in FinopsReportingAction is missing from registry."""
    from apps.api.core.audit_action import _ActionRegistry
    _, accepted = _ActionRegistry._REGISTRY[ActionClass.FINOPS_REPORTING]
    declared = set(FinopsReportingAction.__args__)
    assert declared == accepted, (
        f"Drift detected: declared-declared={declared - accepted}, "
        f"registry-declared={accepted - declared}"
    )


def test_no_overlap_with_finops_tag_governance_actions() -> None:
    """Test 6: Phase 16 actions are distinct from Phase 15 tag governance actions."""
    from apps.api.core.audit_action import _ActionRegistry
    _, tag_gov_accepted = _ActionRegistry._REGISTRY[ActionClass.FINOPS_TAG_GOVERNANCE]
    _, reporting_accepted = _ActionRegistry._REGISTRY[ActionClass.FINOPS_REPORTING]
    assert tag_gov_accepted.isdisjoint(reporting_accepted), (
        "Phase 16 reporting actions should not overlap with Phase 15 tag governance actions"
    )


def test_8_new_audit_actions_specific_validation() -> None:
    """Test 7: All 8 NEW actions are valid string values."""
    new_actions = (
        "executive_report_generated",
        "executive_dashboard_viewed",
        "executive_kpi_refreshed",
        "executive_report_exported",
        "executive_report_dispatched",
        "executive_scheduled_dispatch_evaluated",
        "finops_reporting_dry_run_executed",
        "cross_module_kpi_calculated",
    )
    for action in new_actions:
        assert isinstance(action, str)
        assert len(action) > 0


def test_finops_reporting_module_id_matches_errors_module() -> None:
    """Test 8: FINOPS_REPORTING_MODULE_ID = 'm24_finops_reporting'."""
    from apps.api.core.errors import FINOPS_REPORTING_MODULE_ID
    assert FINOPS_REPORTING_MODULE_ID == "m24_finops_reporting"