"""tests.api.core.test_phase_6_retention_audit_action — Phase 6 audit action extension.

Phase 6 (cj-style 87번째 epic 연속 정직 회복 wire) — T5 (AC #5.6) — F22.5.

Verifies that the 5 NEW audit actions defined for Phase 6 are
recognized by the AuditAction Literal and registered in the
_ActionRegistry for ActionClass.AUDIT:

  - audit_log_purged           (#5.1 — purge job BEFORE DELETE)
  - audit_log_archived         (#5.2 — purge job BEFORE archive snapshot)
  - audit_log_pii_masked       (#5.3 — erasure BEFORE PII mask UPDATE)
  - audit_log_cold_archived    (#5.4 — manual cold-archive BEFORE S3 copy)
  - audit_log_personal_data_erased (#5.5 — GDPR Article 17 BEFORE erasure)

Plus:
  - 1 carry-over: AUDIT_LOG_VIEW enum presence from Epic 17.

6 NEW pytest cases.
"""
from __future__ import annotations

from typing import Union, get_args

import pytest

from apps.api.core.audit_action import (
    ActionClass,
    AuditAction,
    _ActionRegistry,
)


def _flatten_audit_action_literals() -> set[str]:
    """AuditAction is a Union of Literals (one per ActionClass) —
    flatten all values to a single set of strings.
    """
    flat: set[str] = set()
    for arg in get_args(AuditAction):
        flat.update(get_args(arg))
    return flat

EXPECTED_PHASE_6_AUDIT_ACTIONS = (
    "audit_log_purged",
    "audit_log_archived",
    "audit_log_pii_masked",
    "audit_log_cold_archived",
    "audit_log_personal_data_erased",
)


class TestPhase6AuditActionLiteral:
    """§F22.5 — 5 NEW AuditAction Literal values."""

    @pytest.mark.parametrize("action", EXPECTED_PHASE_6_AUDIT_ACTIONS)
    def test_action_in_literal(self, action: str) -> None:
        assert action in _flatten_audit_action_literals()

    def test_audit_log_exported_carried_over_from_epic_17(self) -> None:
        # Epic 17 baseline MUST still be present (no regression).
        assert "audit_log_exported" in _flatten_audit_action_literals()


class TestPhase6ActionRegistry:
    """§F22.5 — ActionClass.AUDIT registry extension."""

    @pytest.mark.parametrize("action", EXPECTED_PHASE_6_AUDIT_ACTIONS)
    def test_action_in_registry_audit(self, action: str) -> None:
        registry_actions = _ActionRegistry._REGISTRY[ActionClass.AUDIT][1]
        assert action in registry_actions

    def test_audit_registry_carries_over_audit_log_exported(self) -> None:
        registry_actions = _ActionRegistry._REGISTRY[ActionClass.AUDIT][1]
        assert "audit_log_exported" in registry_actions

    def test_audit_registry_total_actions_count(self) -> None:
        # 5 Phase 6 NEW + 1 Epic 17 (audit_log_exported) = 6 total.
        registry_actions = _ActionRegistry._REGISTRY[ActionClass.AUDIT][1]
        assert len(registry_actions) == 6

    def test_action_class_audit_registered(self) -> None:
        # ActionClass.AUDIT itself must exist in the registry.
        assert ActionClass.AUDIT in _ActionRegistry._REGISTRY


class TestPhase6AuditActionPhaseChain:
    """Phase 6 carry-over from Epic 17 — VERBATIM chain preservation."""

    def test_audit_action_class_value(self) -> None:
        assert ActionClass.AUDIT.value == "audit"

    def test_resource_table_for_audit_logs(self) -> None:
        # The resource table is "audit_logs" (F22.5 verbatim).
        resource_table = _ActionRegistry._REGISTRY[ActionClass.AUDIT][0]
        assert resource_table == "audit_logs"
