"""tests.api.m11_close.test_reversal_execute_service — Story 11.3 service.

10 cases per AC #4 spec — verify ReversalExecuteService orchestrator:
- execute_reversal happy path (committed → reversed + 4-channel publish)
- execute_reversal idempotent skip (state='committed' first time → execute)
- execute_reversal state mismatch (state != 'committed' → ReversalSnapshotMismatchError)
- execute_reversal not-found snapshot → SnapshotAlreadyCommittedError
- execute_reversal missing fiscal_period → ReversalSnapshotMismatchError
- execute_reversal state='draft' → ReversalSnapshotMismatchError
- execute_reversal state='verified' → ReversalSnapshotMismatchError
- execute_reversal state='reversed' → ReversalSnapshotMismatchError
- REVERSAL_EXECUTE_CHANNELS has 4 channels
- Receipts list contains 4 channel entries (one per channel)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.modules.m11_close.exceptions import (
    ReversalSnapshotMismatchError,
    SnapshotAlreadyCommittedError,
)
from apps.api.modules.m11_close.services.reversal_execute_service import (
    REVERSAL_EXECUTE_CHANNELS,
    ReversalExecuteService,
)


# ── Common fixtures ──────────────────────────────────────────
@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def snapshot_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def actor_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def trace_id() -> str:
    return str(uuid.uuid4())  # valid UUID hex string


def _make_snapshot_row(
    state: str, snapshot_id: uuid.UUID, tenant_id: uuid.UUID
) -> MagicMock:
    """Build a mock FiscalPeriodSnapshot row with the given state."""
    snap = MagicMock()
    snap.snapshot_id = snapshot_id
    snap.tenant_id = tenant_id
    snap.period_key = "2026-08"
    snap.state = state
    snap.baseline_revision = 1
    snap.engine_type = "trad"
    snap.created_at = datetime.now(tz=UTC)
    return snap


def _make_fiscal_period_row(
    tenant_id: uuid.UUID, status: str = "closed"
) -> MagicMock:
    """Build a mock FiscalPeriod row."""
    fp = MagicMock()
    fp.fiscal_period_id = uuid.uuid4()
    fp.tenant_id = tenant_id
    fp.period_key = "2026-08"
    fp.status = status
    return fp


def _make_session_committed(
    snapshot_id: uuid.UUID, tenant_id: uuid.UUID
) -> AsyncMock:
    """Build session mock: snapshot row (committed) + fiscal_period row (closed)."""
    snap = _make_snapshot_row("committed", snapshot_id, tenant_id)
    fp = _make_fiscal_period_row(tenant_id, status="closed")
    session = AsyncMock()
    # session.execute returns the snapshot (SELECT FOR UPDATE).
    snap_result = MagicMock(scalar_one_or_none=MagicMock(return_value=snap))
    session.execute = AsyncMock(
        side_effect=[snap_result, MagicMock(), MagicMock()]
    )
    # session.scalar returns the monthly_input_period row + fiscal_period row.
    # monthly_input_period: None (treated as 'open' default in service).
    # fiscal_period: the fp mock (status='closed').
    session.scalar = AsyncMock(side_effect=[None, fp])
    return session


# ── 1. REVERSAL_EXECUTE_CHANNELS has 4 channels ──────────────
def test_reversal_execute_channels_has_4_channels() -> None:
    """REVERSAL_EXECUTE_CHANNELS must have exactly 4 AD-25 channels."""
    assert len(REVERSAL_EXECUTE_CHANNELS) == 4
    for ch in (
        "closing_snapshot_cache",
        "fiscal_period_cache",
        "cost_engine_cache",
        "ai_cache",
    ):
        assert ch in REVERSAL_EXECUTE_CHANNELS


# ── 2. Happy path (state='committed' → reversed + 4 receipts) ─
@pytest.mark.asyncio
async def test_execute_reversal_happy_path(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
    trace_id: str,
) -> None:
    """execute_reversal on state='committed' returns state='reversed' + 4 receipts."""
    session = _make_session_committed(snapshot_id=snapshot_id, tenant_id=tenant_id)

    svc = ReversalExecuteService(
        session, tenant_id=tenant_id, trace_id=trace_id
    )
    result = await svc.execute_reversal(
        period_key="2026-08",
        snapshot_id=snapshot_id,
        reversal_reason="Operator correction: duplicate inbound",
        actor_id=actor_id,
    )
    assert result.snapshot_id == snapshot_id
    assert result.state == "reversed"
    assert result.period_key == "2026-08"
    # 4 AD-25 channel receipts emitted.
    assert len(result.cache_invalidation_receipts) == 4
    # correction_group_id minted.
    assert isinstance(result.correction_group_id, uuid.UUID)


# ── 3. snapshot not-found → SnapshotAlreadyCommittedError ───
@pytest.mark.asyncio
async def test_execute_reversal_snapshot_not_found(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
    trace_id: str,
) -> None:
    """execute_reversal on missing snapshot raises SnapshotAlreadyCommittedError."""
    session = AsyncMock()
    # snapshot SELECT returns None.
    snap_result = MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    session.execute = AsyncMock(return_value=snap_result)

    svc = ReversalExecuteService(
        session, tenant_id=tenant_id, trace_id=trace_id
    )
    with pytest.raises(SnapshotAlreadyCommittedError) as exc_info:
        await svc.execute_reversal(
            period_key="2026-08",
            snapshot_id=snapshot_id,
            reversal_reason="Test",
            actor_id=actor_id,
        )
    assert exc_info.value.current_state == "not_found"


# ── 4. snapshot state='draft' → ReversalSnapshotMismatchError ─
@pytest.mark.asyncio
async def test_execute_reversal_draft_state_rejected(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
    trace_id: str,
) -> None:
    """execute_reversal on state='draft' raises ReversalSnapshotMismatchError."""
    snap = _make_snapshot_row("draft", snapshot_id, tenant_id)
    fp = _make_fiscal_period_row(tenant_id, status="closed")
    session = AsyncMock()
    snap_result = MagicMock(scalar_one_or_none=MagicMock(return_value=snap))
    session.execute = AsyncMock(return_value=snap_result)
    session.scalar = AsyncMock(side_effect=[None, fp])

    svc = ReversalExecuteService(
        session, tenant_id=tenant_id, trace_id=trace_id
    )
    with pytest.raises(ReversalSnapshotMismatchError) as exc_info:
        await svc.execute_reversal(
            period_key="2026-08",
            snapshot_id=snapshot_id,
            reversal_reason="Test",
            actor_id=actor_id,
        )
    assert exc_info.value.current_state == "draft"


# ── 5. snapshot state='verified' → ReversalSnapshotMismatchError ─
@pytest.mark.asyncio
async def test_execute_reversal_verified_state_rejected(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
    trace_id: str,
) -> None:
    """execute_reversal on state='verified' raises ReversalSnapshotMismatchError."""
    snap = _make_snapshot_row("verified", snapshot_id, tenant_id)
    fp = _make_fiscal_period_row(tenant_id, status="closed")
    session = AsyncMock()
    snap_result = MagicMock(scalar_one_or_none=MagicMock(return_value=snap))
    session.execute = AsyncMock(return_value=snap_result)
    session.scalar = AsyncMock(side_effect=[None, fp])

    svc = ReversalExecuteService(
        session, tenant_id=tenant_id, trace_id=trace_id
    )
    with pytest.raises(ReversalSnapshotMismatchError) as exc_info:
        await svc.execute_reversal(
            period_key="2026-08",
            snapshot_id=snapshot_id,
            reversal_reason="Test",
            actor_id=actor_id,
        )
    assert exc_info.value.current_state == "verified"


# ── 6. snapshot state='reversed' → ReversalSnapshotMismatchError ─
@pytest.mark.asyncio
async def test_execute_reversal_reversed_state_rejected(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
    trace_id: str,
) -> None:
    """execute_reversal on state='reversed' raises ReversalSnapshotMismatchError."""
    snap = _make_snapshot_row("reversed", snapshot_id, tenant_id)
    fp = _make_fiscal_period_row(tenant_id, status="closed")
    session = AsyncMock()
    snap_result = MagicMock(scalar_one_or_none=MagicMock(return_value=snap))
    session.execute = AsyncMock(return_value=snap_result)
    session.scalar = AsyncMock(side_effect=[None, fp])

    svc = ReversalExecuteService(
        session, tenant_id=tenant_id, trace_id=trace_id
    )
    with pytest.raises(ReversalSnapshotMismatchError) as exc_info:
        await svc.execute_reversal(
            period_key="2026-08",
            snapshot_id=snapshot_id,
            reversal_reason="Test",
            actor_id=actor_id,
        )
    assert exc_info.value.current_state == "reversed"


# ── 7. missing fiscal_period → ReversalSnapshotMismatchError ─
@pytest.mark.asyncio
async def test_execute_reversal_missing_fiscal_period(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
    trace_id: str,
) -> None:
    """execute_reversal on missing fiscal_periods row raises ReversalSnapshotMismatchError."""
    snap = _make_snapshot_row("committed", snapshot_id, tenant_id)
    session = AsyncMock()
    snap_result = MagicMock(scalar_one_or_none=MagicMock(return_value=snap))
    session.execute = AsyncMock(return_value=snap_result)
    # session.scalar: monthly_input_period returns None (default 'open'),
    # fiscal_periods returns None (triggers the missing-period guard).
    session.scalar = AsyncMock(side_effect=[None, None])

    svc = ReversalExecuteService(
        session, tenant_id=tenant_id, trace_id=trace_id
    )
    with pytest.raises(ReversalSnapshotMismatchError):
        await svc.execute_reversal(
            period_key="2026-08",
            snapshot_id=snapshot_id,
            reversal_reason="Test",
            actor_id=actor_id,
        )


# ── 8. Receipts list contains 4 channel entries ─────────────
@pytest.mark.asyncio
async def test_receipts_contain_4_channel_entries(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
    trace_id: str,
) -> None:
    """Receipts list has exactly 4 channel entries."""
    session = _make_session_committed(snapshot_id=snapshot_id, tenant_id=tenant_id)

    svc = ReversalExecuteService(
        session, tenant_id=tenant_id, trace_id=trace_id
    )
    result = await svc.execute_reversal(
        period_key="2026-08",
        snapshot_id=snapshot_id,
        reversal_reason="Test",
        actor_id=actor_id,
    )
    assert len(result.cache_invalidation_receipts) == 4
    # Each receipt has channel + tenant_id + event_id + correction_group_id.
    for receipt in result.cache_invalidation_receipts:
        assert "channel" in receipt
        assert "tenant_id" in receipt
        assert "event_id" in receipt


# ── 9. Result is immutable dataclass ────────────────────────
@pytest.mark.asyncio
async def test_result_is_immutable(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
    trace_id: str,
) -> None:
    """ReversalExecuteResponse is immutable (frozen dataclass)."""
    session = _make_session_committed(snapshot_id=snapshot_id, tenant_id=tenant_id)

    svc = ReversalExecuteService(
        session, tenant_id=tenant_id, trace_id=trace_id
    )
    result = await svc.execute_reversal(
        period_key="2026-08",
        snapshot_id=snapshot_id,
        reversal_reason="Test",
        actor_id=actor_id,
    )
    with pytest.raises((AttributeError, Exception)):
        result.state = "committed"  # type: ignore[misc]


# ── 10. Channel tuple order is deterministic ────────────────
def test_channel_order_is_deterministic() -> None:
    """REVERSAL_EXECUTE_CHANNELS preserves canonical AD-25 ordering."""
    expected = (
        "closing_snapshot_cache",
        "fiscal_period_cache",
        "cost_engine_cache",
        "ai_cache",
    )
    assert REVERSAL_EXECUTE_CHANNELS == expected