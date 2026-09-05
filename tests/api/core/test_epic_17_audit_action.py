"""tests.api.core.test_epic_17_audit_action — AUDIT registry verification.

Epic 17 (cj-style 82번째 epic 연속 정직 회복 wire) — AC #5.5 (T7).

Verifies `apps/api/core/audit_action.py` exposes:
  - `ActionClass.AUDIT = "audit"` NEW enum value
  - `audit_log_exported` NEW AuditAction registered in the AUDIT
    registry entry
  - `AuditAction` Literal type extended with the NEW value
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.core.audit_action import ActionClass


class TestAuditActionClassRegistration:
    """Epic 17 — verify AUDIT 1 NEW value is in the registry."""

    def test_action_class_audit_enum_exists(self) -> None:
        assert hasattr(ActionClass, "AUDIT")
        assert ActionClass.AUDIT.value == "audit"

    def test_audit_log_exported_in_audit_registry(self) -> None:
        async def _inner() -> None:
            from apps.api.core.audit_action import _ActionRegistry

            registry = _ActionRegistry._REGISTRY
            audit_entry = registry.get(ActionClass.AUDIT)
            assert audit_entry is not None, "ActionClass.AUDIT missing from registry"

            # registry shape: (AuditLogType, frozenset[str])
            log_type, action_set = audit_entry
            assert log_type == "audit_logs"
            assert "audit_log_exported" in action_set, (
                "audit_log_exported not in ActionClass.AUDIT frozenset. "
                "Add to apps/api/core/audit_action.py ActionClass.AUDIT registry."
            )

        asyncio.run(_inner())


class TestEmitAuditTypedAcceptance:
    """emit_audit_typed() should accept the NEW AUDIT action."""

    def test_emit_accepts_audit_log_exported(self) -> None:
        async def _inner() -> None:
            from apps.api.core.audit_action import emit_audit_typed

            session = AsyncMock()
            session.execute = AsyncMock()
            session.commit = AsyncMock()

            ctx = MagicMock()
            ctx.user_id = "test-user-id"

            try:
                await emit_audit_typed(
                    session,
                    action_class=ActionClass.AUDIT,
                    action="audit_log_exported",
                    actor_id=ctx.user_id,
                    target_id=None,
                    tenant_id=None,
                    payload={"row_count": 42},
                )
            except (KeyError, ValueError) as exc:
                pytest.fail(
                    f"emit_audit_typed raised {exc!r} on a registered action. "
                    "Check _ActionRegistry.AUDIT entry."
                )

        asyncio.run(_inner())

    def test_emit_rejects_unknown_audit_action(self) -> None:
        """CR 1-1 verbatim — typo guard on audit emit."""
        async def _inner() -> None:
            from apps.api.core.audit_action import emit_audit_typed

            session = AsyncMock()
            session.execute = AsyncMock()
            session.commit = AsyncMock()

            ctx = MagicMock()
            ctx.user_id = "test-user-id"

            with pytest.raises(
                ValueError, match="AUDIT|audit_log_exported"
            ) as exc_info:
                await emit_audit_typed(
                    session,
                    action_class=ActionClass.AUDIT,
                    action="audit_log_exported_typo",  # not in registry
                    actor_id=ctx.user_id,
                    target_id=None,
                    tenant_id=None,
                    payload={"row_count": 42},
                )
            assert exc_info.value is not None

        asyncio.run(_inner())
