"""tests/rls/test_service_role_audit.py — service_role bypass audit-first guarantee.

Story 0.2 — Task 9.1. These tests are pure unit tests (no DB required)
and run in CI alongside the tenant isolation tests.

The audit-first guarantee:
1. Audit row is inserted BEFORE the wrapped action runs.
2. If the audit insert fails, the action is NOT invoked.
3. `target_table` and `actor_id` are required — `ValueError` otherwise.

Note: tests are written as `def` (synchronous) and use `asyncio.run` to drive
async helpers. This avoids the pytest-asyncio dep (incompatible with
pytest==9.1.1 per spec).
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.core.audit import emit_audit
from apps.api.core.db_models import AuditLog
from apps.api.core.security import (
    CROSS_TENANT_ACCESS,
    CROSS_TENANT_MESSAGE_KO,
    raise_cross_tenant_access,
)
from apps.api.core.service_role import (
    SYSTEM_ACTOR_ID,
    run_with_service_role,
    with_service_role,
)


# ── emit_audit unit tests ─────────────────────────────────


def test_emit_audit_requires_target_table() -> None:
    """AC #4 audit-helper: target_table is required."""
    session = AsyncMock()

    async def run() -> None:
        await emit_audit(
            session,
            actor_id=uuid.uuid4(),
            action="login",
            target_table="",
        )

    with pytest.raises(ValueError, match="target_table"):
        asyncio.run(run())


def test_emit_audit_requires_action() -> None:
    """AC #4 audit-helper: action is required."""
    session = AsyncMock()

    async def run() -> None:
        await emit_audit(
            session,
            actor_id=uuid.uuid4(),
            action="",
            target_table="users",
        )

    with pytest.raises(ValueError, match="action"):
        asyncio.run(run())


def test_emit_audit_persists_row() -> None:
    """AC #4 audit-helper: inserts an AuditLog row with required fields."""
    session = AsyncMock()

    async def run() -> None:
        await emit_audit(
            session,
            actor_id=uuid.uuid4(),
            action="login",
            target_table="users",
            reason="user signed in",
            target_id=uuid.uuid4(),
        )

    asyncio.run(run())
    session.add.assert_called_once()
    row = session.add.call_args[0][0]
    assert isinstance(row, AuditLog)
    assert row.action == "login"
    assert row.target_table == "users"
    assert row.reason == "user signed in"
    assert row.occurred_at.tzinfo is not None


# ── with_service_role audit-first tests ────────────────────


def test_audit_written_before_action() -> None:
    """AC #4 (a): audit row is added BEFORE the action runs."""
    actor_id = uuid.uuid4()
    session = AsyncMock()
    # session.add is sync in SQLAlchemy — use a regular Mock so side_effect runs sync.
    session.add = MagicMock()
    session.flush = AsyncMock()

    call_order: list[str] = []

    def track_add(row: Any) -> None:
        call_order.append("audit_add")

    session.add.side_effect = track_add

    async def fake_session_iter():
        yield session

    import apps.api.core.service_role as sr_module

    sr_module.get_session = fake_session_iter  # type: ignore[assignment]

    action_called = False

    async def action(session: AsyncMock) -> None:
        nonlocal action_called
        action_called = True
        call_order.append("action")

    async def run() -> None:
        await run_with_service_role(
            actor_id=actor_id,
            reason="backfill tenant_settings",
            target_table="tenant_settings",
            action=action,
        )

    asyncio.run(run())

    assert action_called, "action was never invoked"
    assert "audit_add" in call_order, "audit row was never added"
    assert call_order.index("audit_add") < call_order.index("action"), (
        "audit row must be added BEFORE action runs"
    )


def test_audit_failure_aborts_action() -> None:
    """AC #4 (b): if audit insert fails, action is NOT invoked."""
    actor_id = uuid.uuid4()
    session = AsyncMock()
    session.flush = AsyncMock(side_effect=RuntimeError("audit insert failed"))

    async def fake_session_iter():
        yield session

    import apps.api.core.service_role as sr_module

    sr_module.get_session = fake_session_iter  # type: ignore[assignment]

    action_called = False

    async def action(session: AsyncMock) -> None:
        nonlocal action_called
        action_called = True

    async def run() -> None:
        await run_with_service_role(
            actor_id=actor_id,
            reason="bad reason",
            target_table="tenant_settings",
            action=action,
        )

    with pytest.raises(RuntimeError, match="audit insert failed"):
        asyncio.run(run())

    assert not action_called, "action ran even though audit failed"


def test_audit_target_table_required() -> None:
    """AC #4 (c): with_service_role rejects empty target_table."""

    async def run() -> None:
        async with with_service_role(
            actor_id=uuid.uuid4(),
            reason="missing target",
            target_table="",
        ):
            pass

    with pytest.raises(ValueError, match="target_table"):
        asyncio.run(run())


def test_audit_actor_id_required() -> None:
    """AC #4 (c): with_service_role rejects None actor_id."""

    async def run() -> None:
        async with with_service_role(
            actor_id=None,  # type: ignore[arg-type]
            reason="missing actor",
            target_table="users",
        ):
            pass

    with pytest.raises(ValueError, match="actor_id"):
        asyncio.run(run())


def test_audit_reason_required() -> None:
    """AC #4 (c): with_service_role rejects empty reason."""

    async def run() -> None:
        async with with_service_role(
            actor_id=uuid.uuid4(),
            reason="",
            target_table="users",
        ):
            pass

    with pytest.raises(ValueError, match="reason"):
        asyncio.run(run())


def test_audit_logs_model_has_required_columns() -> None:
    """AC #4 (d): AuditLog ORM model has the required columns (AD-2 contract)."""
    import apps.api.core.db_models as db_models

    assert hasattr(db_models, "AuditLog"), "AuditLog model must be defined"
    audit = db_models.AuditLog
    for col in ("tenant_id", "actor_id", "action", "target_table", "occurred_at"):
        assert hasattr(audit, col), f"AuditLog missing column: {col}"


def test_system_actor_id_is_deterministic() -> None:
    """SYSTEM_ACTOR_ID is a stable sentinel for platform-initiated actions."""
    assert str(SYSTEM_ACTOR_ID) == "00000000-0000-0000-0000-000000000000"


# ── Cross-tenant access error (AC #3) ───────────────────────


def test_cross_tenant_access_error_contract() -> None:
    """AC #3: spec mandates the exact Korean message + code when a tenant
    tries to access another tenant's data. `raise_cross_tenant_access`
    is the canonical raise site for service-layer cross-tenant detection
    (RLS policy violations return 0 rows, not exceptions).
    """
    expected = uuid.uuid4()
    actual = uuid.uuid4()

    async def run() -> None:
        raise_cross_tenant_access(expected, actual)

    with pytest.raises(Exception) as exc_info:
        asyncio.run(run())

    # The AuthError exception is caught by `except Exception`. Inspect attributes.
    err = exc_info.value
    # Import here to avoid coupling test to internal symbol ordering.
    from apps.api.core.security import AuthError

    assert isinstance(err, AuthError)
    assert err.code == CROSS_TENANT_ACCESS
    assert err.message_ko == CROSS_TENANT_MESSAGE_KO
    assert err.message_ko == "다른 테넌트 데이터에 접근할 수 없습니다"
    assert err.details["expected_tenant_id"] == str(expected)
    assert err.details["actual_tenant_id"] == str(actual)
    assert err.trace_id  # generated if not provided
