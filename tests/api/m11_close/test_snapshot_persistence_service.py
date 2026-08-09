"""tests.api.m11_close.test_snapshot_persistence_service — Story 11.3 service.

8 cases per AC #3 spec — verify SnapshotPersistenceService orchestrator:
- commit_snapshot happy path (verified → committed + audit + 4-channel publish)
- commit_snapshot idempotent no-op (state='committed' returns idempotent_ok)
- commit_snapshot terminal rejection (state='reversed' raises exception)
- commit_snapshot not-found (snapshot_id not in tenant)
- get_snapshot happy path (returns current state)
- get_snapshot not-found (no row → None)
- SNAPSHOT_COMMIT_CHANNELS has exactly 4 channels
- Receipts list contains 4 channel entries (one per channel)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.api.modules.m11_close.exceptions import SnapshotAlreadyCommittedError
from apps.api.modules.m11_close.services.snapshot_persistence_service import (
    SNAPSHOT_COMMIT_CHANNELS,
    SnapshotPersistenceService,
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
    return "test-trace-11-3"


def _make_snapshot_row(state: str, snapshot_id: uuid.UUID, tenant_id: uuid.UUID):
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


@pytest.fixture
def mock_session_verified(
    snapshot_id: uuid.UUID, tenant_id: uuid.UUID
) -> AsyncMock:
    """Session mock where SELECT returns a verified snapshot."""
    snap = _make_snapshot_row("verified", snapshot_id, tenant_id)
    session = AsyncMock()
    # session.execute(...) for SELECT
    session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=snap)))
    # session.execute for UPDATE — same callable
    return session


# ── 1. SNAPSHOT_COMMIT_CHANNELS has 4 channels ────────────────
def test_snapshot_commit_channels_has_4_channels() -> None:
    """SNAPSHOT_COMMIT_CHANNELS must have exactly 4 AD-25 channels."""
    assert len(SNAPSHOT_COMMIT_CHANNELS) == 4
    for ch in (
        "closing_snapshot_cache",
        "fiscal_period_cache",
        "cost_engine_cache",
        "ai_cache",
    ):
        assert ch in SNAPSHOT_COMMIT_CHANNELS


# ── 2. commit_snapshot happy path (verified → committed) ──────
@pytest.mark.asyncio
async def test_commit_snapshot_happy_path(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
    trace_id: str,
) -> None:
    """commit_snapshot on state='verified' returns state='committed' + 4 receipts."""
    snap = _make_snapshot_row("verified", snapshot_id, tenant_id)
    session = AsyncMock()
    # SELECT FOR UPDATE returns the snapshot, UPDATE is also via execute.
    select_result = MagicMock(scalar_one_or_none=MagicMock(return_value=snap))
    update_result = MagicMock()
    session.execute = AsyncMock(side_effect=[select_result, update_result])

    svc = SnapshotPersistenceService(
        session, tenant_id=tenant_id, trace_id=trace_id
    )
    result = await svc.commit_snapshot(
        period_key="2026-08",
        snapshot_id=snapshot_id,
        actor_id=actor_id,
    )
    assert result.snapshot_id == snapshot_id
    assert result.state == "committed"
    assert result.period_key == "2026-08"
    # 4 AD-25 channel receipts emitted.
    assert len(result.cache_invalidation_receipts) == 4


# ── 3. commit_snapshot idempotent no-op ──────────────────────
@pytest.mark.asyncio
async def test_commit_snapshot_idempotent_noop(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
    trace_id: str,
) -> None:
    """commit_snapshot on state='committed' returns idempotent_ok=True (no UPDATE)."""
    snap = _make_snapshot_row("committed", snapshot_id, tenant_id)
    session = AsyncMock()
    select_result = MagicMock(scalar_one_or_none=MagicMock(return_value=snap))
    session.execute = AsyncMock(return_value=select_result)

    svc = SnapshotPersistenceService(
        session, tenant_id=tenant_id, trace_id=trace_id
    )
    result = await svc.commit_snapshot(
        period_key="2026-08",
        snapshot_id=snapshot_id,
        actor_id=actor_id,
    )
    assert result.state == "committed"
    # Idempotent no-op: no UPDATE executed, no AD-25 publish.
    assert result.cache_invalidation_receipts == []
    # Only one execute (SELECT), no UPDATE.
    assert session.execute.await_count == 1


# ── 4. commit_snapshot terminal rejection (reversed state) ───
@pytest.mark.asyncio
async def test_commit_snapshot_terminal_rejection(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
    trace_id: str,
) -> None:
    """commit_snapshot on state='reversed' raises SnapshotAlreadyCommittedError."""
    snap = _make_snapshot_row("reversed", snapshot_id, tenant_id)
    session = AsyncMock()
    select_result = MagicMock(scalar_one_or_none=MagicMock(return_value=snap))
    session.execute = AsyncMock(return_value=select_result)

    svc = SnapshotPersistenceService(
        session, tenant_id=tenant_id, trace_id=trace_id
    )
    with pytest.raises(SnapshotAlreadyCommittedError) as exc_info:
        await svc.commit_snapshot(
            period_key="2026-08",
            snapshot_id=snapshot_id,
            actor_id=actor_id,
        )
    assert exc_info.value.current_state == "reversed"


# ── 5. commit_snapshot not-found ─────────────────────────────
@pytest.mark.asyncio
async def test_commit_snapshot_not_found(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
    trace_id: str,
) -> None:
    """commit_snapshot on missing snapshot raises SnapshotAlreadyCommittedError."""
    session = AsyncMock()
    select_result = MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    session.execute = AsyncMock(return_value=select_result)

    svc = SnapshotPersistenceService(
        session, tenant_id=tenant_id, trace_id=trace_id
    )
    with pytest.raises(SnapshotAlreadyCommittedError) as exc_info:
        await svc.commit_snapshot(
            period_key="2026-08",
            snapshot_id=snapshot_id,
            actor_id=actor_id,
        )
    assert exc_info.value.current_state == "not_found"


# ── 6. commit_snapshot non-committable (draft state) ──────────
@pytest.mark.asyncio
async def test_commit_snapshot_draft_state_rejected(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    actor_id: uuid.UUID,
    trace_id: str,
) -> None:
    """commit_snapshot on state='draft' raises SnapshotAlreadyCommittedError."""
    snap = _make_snapshot_row("draft", snapshot_id, tenant_id)
    session = AsyncMock()
    select_result = MagicMock(scalar_one_or_none=MagicMock(return_value=snap))
    session.execute = AsyncMock(return_value=select_result)

    svc = SnapshotPersistenceService(
        session, tenant_id=tenant_id, trace_id=trace_id
    )
    with pytest.raises(SnapshotAlreadyCommittedError) as exc_info:
        await svc.commit_snapshot(
            period_key="2026-08",
            snapshot_id=snapshot_id,
            actor_id=actor_id,
        )
    assert exc_info.value.current_state == "draft"


# ── 7. get_snapshot happy path ───────────────────────────────
@pytest.mark.asyncio
async def test_get_snapshot_happy_path(
    tenant_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    trace_id: str,
) -> None:
    """get_snapshot returns the current state for the given period_key."""
    snap = _make_snapshot_row("verified", snapshot_id, tenant_id)
    session = AsyncMock()
    select_result = MagicMock(scalar_one_or_none=MagicMock(return_value=snap))
    session.execute = AsyncMock(return_value=select_result)

    svc = SnapshotPersistenceService(
        session, tenant_id=tenant_id, trace_id=trace_id
    )
    result = await svc.get_snapshot(period_key="2026-08")
    assert result.snapshot_id == snapshot_id
    assert result.state == "verified"
    assert result.period_key == "2026-08"


# ── 8. get_snapshot not-found ────────────────────────────────
@pytest.mark.asyncio
async def test_get_snapshot_not_found(
    tenant_id: uuid.UUID, trace_id: str
) -> None:
    """get_snapshot returns None for missing period."""
    session = AsyncMock()
    select_result = MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    session.execute = AsyncMock(return_value=select_result)

    svc = SnapshotPersistenceService(
        session, tenant_id=tenant_id, trace_id=trace_id
    )
    result = await svc.get_snapshot(period_key="2099-01")
    assert result.snapshot_id is None
    assert result.state is None
    assert result.committed_at is None
    assert result.period_key == "2099-01"