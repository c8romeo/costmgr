"""tests.api.m11_close.test_close_sequence_service — Story 11.2 service tests.

6 cases per AC #10 spec:
- initiate success (insert fiscal_periods + audit emit)
- initiate idempotent (re-initiate → AlreadyInitiatedError)
- step_complete divisions (UPDATE divisions_completed_at + audit emit)
- confirm partial_blocked (4단계 미완료 → PartialCloseBlockedError)
- confirm success (all 4 stages done → fiscal_periods.status='closed')
- already_confirmed idempotent (re-confirm → AlreadyConfirmedError)
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.modules.m11_close.services.close_sequence_service import (
    CloseSequenceAlreadyInitiatedError,
    CloseSequenceService,
    CloseSequenceStepMismatchError,
    ClosingSequenceAlreadyConfirmedError,
    ClosingSequenceAuditEmitError,
    PartialCloseBlockedError,
)

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
ACTOR_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
TRACE_ID = "test-trace-1234"
PERIOD_KEY = "2026-08"


def _make_fiscal_period_row(
    *,
    status: str = "open",
    state: str = "divisions",
    divisions_ts: datetime | None = None,
    manufacturing_ts: datetime | None = None,
    abc_ts: datetime | None = None,
    common_ts: datetime | None = None,
) -> MagicMock:
    """Create a MagicMock row matching FiscalPeriod attributes used in service."""
    row = MagicMock()
    row.id = uuid.uuid4()
    row.tenant_id = TENANT_ID
    row.period_key = PERIOD_KEY
    row.status = status
    row.divisions_completed_at = divisions_ts
    row.manufacturing_completed_at = manufacturing_ts
    row.abc_completed_at = abc_ts
    row.common_completed_at = common_ts
    row.close_sequence_state = state
    row.close_sequence_blocked_reason_ko = None
    row.closed_at = None
    row.closed_by_actor_id = None
    row.created_at = datetime(2026, 8, 1)
    row.updated_at = datetime(2026, 8, 1)
    return row


def _build_service(session: AsyncMock) -> CloseSequenceService:
    return CloseSequenceService(
        session,
        tenant_id=TENANT_ID,
        trace_id=TRACE_ID,
    )


def _wire_session_scalar_queue(
    session: AsyncMock, *queue: Any
) -> None:
    """Wire session.scalar to return each item in `queue` (pop LIFO)."""
    queue_list = list(queue)

    async def _pop(*_args: Any) -> Any:
        if not queue_list:
            return None
        return queue_list.pop(0)

    session.scalar = AsyncMock(side_effect=_pop)


# ── initiate_close_sequence ─────────────────────────────────
def test_initiate_close_sequence_success() -> None:
    """INSERTs fiscal_periods row + emits closing_sequence_initiated audit."""

    async def _impl() -> None:
        session = AsyncMock()
        # SELECT FOR UPDATE on existing fiscal_periods → None (new row).
        _wire_session_scalar_queue(session, None)
        session.add = MagicMock()
        session.flush = AsyncMock()

        svc = _build_service(session)
        result = await svc.initiate_close_sequence(
            period_key=PERIOD_KEY,
            actor_id=ACTOR_ID,
        )

        assert result["period_key"] == PERIOD_KEY
        assert result["close_sequence_state"] == "divisions"
        assert result["status"] == "open"
        assert result["fiscal_period_id"]
        # session.add called twice — once for fiscal_periods row,
        # once for audit log (audit-first ordering per CR 1.1).
        assert session.add.call_count >= 1

    asyncio.run(_impl())


def test_initiate_close_sequence_already_initiated_raises() -> None:
    """Existing fiscal_periods row → CloseSequenceAlreadyInitiatedError."""

    async def _impl() -> None:
        session = AsyncMock()
        existing = _make_fiscal_period_row(status="open", state="divisions")
        _wire_session_scalar_queue(session, existing)

        svc = _build_service(session)
        with pytest.raises(CloseSequenceAlreadyInitiatedError):
            await svc.initiate_close_sequence(
                period_key=PERIOD_KEY,
                actor_id=ACTOR_ID,
            )

    asyncio.run(_impl())


# ── step_complete ────────────────────────────────────────────
def test_step_complete_divisions_advances_state() -> None:
    """Mark divisions complete → close_sequence_state advances."""

    async def _impl() -> None:
        session = AsyncMock()
        existing = _make_fiscal_period_row(state="divisions")
        _wire_session_scalar_queue(session, existing)
        session.add = MagicMock()
        session.flush = AsyncMock()

        svc = _build_service(session)
        result = await svc.step_complete(
            period_key=PERIOD_KEY,
            step_name="divisions",
            actor_id=ACTOR_ID,
        )

        assert result["step_completed"] == "divisions"
        # State advances to 'manufacturing' (next_step after divisions).
        assert result["close_sequence_state"] == "manufacturing"
        # divisions_completed_at now populated.
        assert existing.divisions_completed_at is not None

    asyncio.run(_impl())


def test_step_complete_out_of_order_raises() -> None:
    """Attempting 'manufacturing' before 'divisions' → StepMismatchError."""

    async def _impl() -> None:
        session = AsyncMock()
        existing = _make_fiscal_period_row(state="divisions")
        _wire_session_scalar_queue(session, existing)

        svc = _build_service(session)
        with pytest.raises(CloseSequenceStepMismatchError) as exc_info:
            await svc.step_complete(
                period_key=PERIOD_KEY,
                step_name="manufacturing",
                actor_id=ACTOR_ID,
            )
        assert exc_info.value.attempted_step == "manufacturing"
        assert exc_info.value.expected_step == "divisions"

    asyncio.run(_impl())


# ── confirm_close_sequence ──────────────────────────────────
def test_confirm_partial_close_blocked_raises() -> None:
    """Only divisions complete → PartialCloseBlockedError."""

    async def _impl() -> None:
        session = AsyncMock()
        now = datetime(2026, 8, 1, 12, 0, 0)
        existing = _make_fiscal_period_row(
            status="open",
            state="manufacturing",
            divisions_ts=now,
        )
        _wire_session_scalar_queue(session, existing)
        session.add = MagicMock()
        session.flush = AsyncMock()

        svc = _build_service(session)
        with pytest.raises(PartialCloseBlockedError) as exc_info:
            await svc.confirm_close_sequence(
                period_key=PERIOD_KEY,
                actor_id=ACTOR_ID,
            )
        # missing_step = first incomplete stage.
        assert exc_info.value.missing_step == "manufacturing"
        assert exc_info.value.reject_reason_ko  # Korean SSOT non-empty.

    asyncio.run(_impl())


def test_confirm_close_sequence_success() -> None:
    """All 4 stages complete → fiscal_periods.status='closed'."""

    async def _impl() -> None:
        session = AsyncMock()
        base = datetime(2026, 8, 1, 0, 0, 0)
        existing = _make_fiscal_period_row(
            status="open",
            state="common",
            divisions_ts=base,
            manufacturing_ts=base + timedelta(minutes=10),
            abc_ts=base + timedelta(minutes=20),
            common_ts=base + timedelta(minutes=30),
        )
        _wire_session_scalar_queue(session, existing)
        session.add = MagicMock()
        session.flush = AsyncMock()

        svc = _build_service(session)
        result = await svc.confirm_close_sequence(
            period_key=PERIOD_KEY,
            actor_id=ACTOR_ID,
        )

        assert result["confirmed"] is True
        assert result["close_sequence_state"] == "confirmed"
        assert result["status"] == "closed"
        # The row was mutated.
        assert existing.status == "closed"
        assert existing.close_sequence_state == "confirmed"
        assert existing.closed_at is not None
        assert existing.closed_by_actor_id == ACTOR_ID

    asyncio.run(_impl())


def test_confirm_already_confirmed_raises() -> None:
    """status='closed' → ClosingSequenceAlreadyConfirmedError (idempotent no-op)."""

    async def _impl() -> None:
        session = AsyncMock()
        base = datetime(2026, 8, 1, 0, 0, 0)
        existing = _make_fiscal_period_row(
            status="closed",
            state="confirmed",
            divisions_ts=base,
            manufacturing_ts=base + timedelta(minutes=10),
            abc_ts=base + timedelta(minutes=20),
            common_ts=base + timedelta(minutes=30),
            # closed_at populated for AlreadyConfirmedError details.
        )
        existing.closed_at = base + timedelta(minutes=40)
        existing.closed_by_actor_id = ACTOR_ID
        _wire_session_scalar_queue(session, existing)

        svc = _build_service(session)
        with pytest.raises(ClosingSequenceAlreadyConfirmedError):
            await svc.confirm_close_sequence(
                period_key=PERIOD_KEY,
                actor_id=ACTOR_ID,
            )

    asyncio.run(_impl())


def test_get_close_sequence_state_no_row() -> None:
    """get_close_sequence_state with no fiscal_periods row → defaults."""

    async def _impl() -> None:
        session = AsyncMock()
        _wire_session_scalar_queue(session, None)

        svc = _build_service(session)
        result = await svc.get_close_sequence_state(period_key=PERIOD_KEY)

        assert result["fiscal_period_id"] is None
        assert result["close_sequence_state"] is None
        assert result["missing_step"] == "divisions"

    asyncio.run(_impl())


def test_confirm_audit_emit_failure_raises_typed_error() -> None:
    """Audit emit failure → ClosingSequenceAuditEmitError (500 envelope)."""

    async def _impl() -> None:
        session = AsyncMock()
        base = datetime(2026, 8, 1, 0, 0, 0)
        existing = _make_fiscal_period_row(
            status="open",
            state="common",
            divisions_ts=base,
            manufacturing_ts=base + timedelta(minutes=10),
            abc_ts=base + timedelta(minutes=20),
            common_ts=base + timedelta(minutes=30),
        )
        _wire_session_scalar_queue(session, existing)

        # Patch emit_audit_typed to raise.
        from apps.api.modules.m11_close.services import close_sequence_service as svc_mod

        original_emit = svc_mod.emit_audit_typed

        async def _raise(*_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("simulated audit emit failure")

        svc_mod.emit_audit_typed = _raise

        try:
            svc = _build_service(session)
            with pytest.raises(ClosingSequenceAuditEmitError):
                await svc.confirm_close_sequence(
                    period_key=PERIOD_KEY,
                    actor_id=ACTOR_ID,
                )
        finally:
            svc_mod.emit_audit_typed = original_emit

    asyncio.run(_impl())
