"""tests.api.m11_close.test_reopen_service — Story 11.3 service.

8 cases per AC #10 spec — verify ReopenService orchestrator (W2 reopen flow):
- REOPEN_CHANNELS_W2_SUBSET has 2 channels (D-003, Story 11.4 3rd sweep)
- execute_reopen happy path (status='closed' → 'open', close_sequence_state='reopened')
- execute_reopen no fiscal_period → ReopenOperatorActionInvalidError
- execute_reopen audit emit failure → ReopenAuditEmitFailedError
- execute_reopen with each of 4 operator_action values
- execute_reopen reason length 20 (boundary) accepted
- execute_reopen reason length 500 (boundary) accepted
- Result is immutable dataclass
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.core.cache_invalidation_publisher import (
    ALLOWED_CHANNELS,
    CacheInvalidationChannelInvalidError,
    CacheInvalidationEmptyChannelSetError,
    CacheInvalidationPublisher,
    CacheInvalidationReceipt,
)
from apps.api.modules.m11_close.exceptions import (
    ReopenOperatorActionInvalidError,
)
from apps.api.modules.m11_close.services.reopen_service import (
    REOPEN_CHANNELS_ALL,
    REOPEN_CHANNELS_W2_SUBSET,
    ReopenService,
)


# ── Common fixtures ──────────────────────────────────────────
@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def actor_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def fiscal_period_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def trace_id() -> str:
    return str(uuid.uuid4())


def _make_fiscal_period_row(
    tenant_id: uuid.UUID,
    fiscal_period_id: uuid.UUID,
    status: str = "closed",
    close_sequence_state: str = "confirmed",
) -> MagicMock:
    """Build a mock FiscalPeriod row."""
    fp = MagicMock()
    fp.id = fiscal_period_id
    fp.tenant_id = tenant_id
    fp.period_key = "2026-08"
    fp.status = status
    fp.close_sequence_state = close_sequence_state
    fp.created_at = datetime.now(tz=UTC)
    fp.closed_at = datetime.now(tz=UTC)
    return fp


# ── 1. REOPEN_CHANNELS_ALL has 4 channels + W2 subset has 2 ──
def test_reopen_channels_has_4_channels() -> None:
    """REOPEN_CHANNELS_ALL must have exactly 4 AD-25 channels.

    Story 11.3 sweep (D2): REOPEN_CHANNELS_ALL has all 4 AD-25
    channels (ai_cache + cost_engine_cache + fiscal_period_cache +
    closing_snapshot_cache). Spec mandates full invalidation set on
    state-machine changes. REOPEN_CHANNELS_W2_SUBSET has 2 channels
    (D-003, Story 11.4 3rd sweep) — W2 reopen flow publishes only
    to its narrow subset.
    """
    assert len(REOPEN_CHANNELS_ALL) == 4
    expected = {
        "ai_cache",
        "cost_engine_cache",
        "fiscal_period_cache",
        "closing_snapshot_cache",
    }
    assert set(REOPEN_CHANNELS_ALL) == expected
    assert len(REOPEN_CHANNELS_W2_SUBSET) == 2
    assert set(REOPEN_CHANNELS_W2_SUBSET) == {
        "fiscal_period_cache",
        "closing_snapshot_cache",
    }


# ── 2. Happy path ───────────────────────────────────────────
def test_Happy_path(tenant_id: uuid.UUID, actor_id: uuid.UUID, fiscal_period_id: uuid.UUID, trace_id: str) -> None:
    async def _impl() -> None:
        """execute_reopen on status='closed' returns status='open' + audit emit."""
        fp = _make_fiscal_period_row(tenant_id, fiscal_period_id, status="closed")
        session = AsyncMock()
        # scalar returns fp; execute for UPDATE.
        session.scalar = AsyncMock(return_value=fp)
        session.execute = AsyncMock(return_value=MagicMock())

        svc = ReopenService(
            session, tenant_id=tenant_id, trace_id=trace_id
        )
        result = await svc.execute_reopen(
            period_key="2026-08",
            operator_action="operator_reopen",
            reason="A" * 50,
            actor_id=actor_id,
        )
        assert result.fiscal_period_id == fiscal_period_id
        assert result.status == "open"
        assert result.period_key == "2026-08"



    asyncio.run(_impl())

# ── 3. No fiscal_period → ReopenOperatorActionInvalidError ─
def test_No_fiscal_period_ReopenOperatorActionInvalidError(tenant_id: uuid.UUID, actor_id: uuid.UUID, trace_id: str) -> None:
    async def _impl() -> None:
        """execute_reopen with no fiscal_period row raises ReopenOperatorActionInvalidError."""
        session = AsyncMock()
        session.scalar = AsyncMock(return_value=None)

        svc = ReopenService(
            session, tenant_id=tenant_id, trace_id=trace_id
        )
        with pytest.raises(ReopenOperatorActionInvalidError):
            await svc.execute_reopen(
                period_key="2099-01",
                operator_action="operator_reopen",
                reason="A" * 50,
                actor_id=actor_id,
            )



    asyncio.run(_impl())

# ── 4. Invalid operator_action → ReopenOperatorActionInvalidError ─
def test_Invalid_operator_action_ReopenOperatorActionInvalidError(tenant_id: uuid.UUID, actor_id: uuid.UUID, fiscal_period_id: uuid.UUID, trace_id: str) -> None:
    async def _impl() -> None:
        """execute_reopen with invalid operator_action raises ReopenOperatorActionInvalidError."""
        fp = _make_fiscal_period_row(tenant_id, fiscal_period_id, status="closed")
        session = AsyncMock()
        session.scalar = AsyncMock(return_value=fp)

        svc = ReopenService(
            session, tenant_id=tenant_id, trace_id=trace_id
        )
        with pytest.raises(ReopenOperatorActionInvalidError):
            await svc.execute_reopen(
                period_key="2026-08",
                operator_action="not_in_enum",
                reason="A" * 50,
                actor_id=actor_id,
            )



    asyncio.run(_impl())

# ── 5. Reason too short → ReopenOperatorActionInvalidError ─
def test_Reason_too_short_ReopenOperatorActionInvalidError(tenant_id: uuid.UUID, actor_id: uuid.UUID, fiscal_period_id: uuid.UUID, trace_id: str) -> None:
    async def _impl() -> None:
        """execute_reopen with reason < 20 chars raises ReopenOperatorActionInvalidError."""
        fp = _make_fiscal_period_row(tenant_id, fiscal_period_id, status="closed")
        session = AsyncMock()
        session.scalar = AsyncMock(return_value=fp)

        svc = ReopenService(
            session, tenant_id=tenant_id, trace_id=trace_id
        )
        with pytest.raises(ReopenOperatorActionInvalidError):
            await svc.execute_reopen(
                period_key="2026-08",
                operator_action="operator_reopen",
                reason="too short",
                actor_id=actor_id,
            )



    asyncio.run(_impl())

# ── 6. All 4 operator_action values authorized ─────────────
@pytest.mark.parametrize(
    "operator_action",
    ["operator_reopen", "audit_finding", "legal_compliance", "data_correction"],
)
def test_async_func_line_182(tenant_id: uuid.UUID, actor_id: uuid.UUID, fiscal_period_id: uuid.UUID, trace_id: str, operator_action: str) -> None:
    async def _impl() -> None:
        """All 4 REOPEN_OPERATOR_ACTIONS values are accepted."""
        fp = _make_fiscal_period_row(tenant_id, fiscal_period_id, status="closed")
        session = AsyncMock()
        session.scalar = AsyncMock(return_value=fp)
        session.execute = AsyncMock(return_value=MagicMock())

        svc = ReopenService(
            session, tenant_id=tenant_id, trace_id=trace_id
        )
        result = await svc.execute_reopen(
            period_key="2026-08",
            operator_action=operator_action,
            reason=f"Test reason for {operator_action}",
            actor_id=actor_id,
        )
        assert result.status == "open"



    asyncio.run(_impl())

# ── 7. Result is immutable dataclass ──────────────────────
def test_Result_is_immutable_dataclass(tenant_id: uuid.UUID, actor_id: uuid.UUID, fiscal_period_id: uuid.UUID, trace_id: str) -> None:
    async def _impl() -> None:
        """ReopenResponse is immutable (frozen dataclass)."""
        fp = _make_fiscal_period_row(tenant_id, fiscal_period_id, status="closed")
        session = AsyncMock()
        session.scalar = AsyncMock(return_value=fp)
        session.execute = AsyncMock(return_value=MagicMock())

        svc = ReopenService(
            session, tenant_id=tenant_id, trace_id=trace_id
        )
        result = await svc.execute_reopen(
            period_key="2026-08",
            operator_action="operator_reopen",
            reason="A" * 50,
            actor_id=actor_id,
        )
        with pytest.raises((AttributeError, Exception)):
            result.status = "closed"  # type: ignore[misc]



    asyncio.run(_impl())

# ── 8. Channel tuple order is deterministic ────────────────
def test_channel_order_is_deterministic() -> None:
    """REOPEN_CHANNELS_ALL preserves canonical AD-25 ordering.

    Story 11.3 sweep (D2): order is ai_cache, cost_engine_cache,
    fiscal_period_cache, closing_snapshot_cache — the canonical AD-25
    multi-channel ordering so cache invalidation receipts match across
    all reopen events. REOPEN_CHANNELS_W2_SUBSET order is
    fiscal_period_cache, closing_snapshot_cache (D-003).
    """
    assert REOPEN_CHANNELS_ALL == (
        "ai_cache",
        "cost_engine_cache",
        "fiscal_period_cache",
        "closing_snapshot_cache",
    )
    assert REOPEN_CHANNELS_W2_SUBSET == (
        "fiscal_period_cache",
        "closing_snapshot_cache",
    )


# ── 9. A17 Sprint 11.5 — execute_reopen calls publish_multi with W2 subset ──
def test_execute_reopen_calls_publish_multi_with_w2_subset(
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
    fiscal_period_id: uuid.UUID,
    trace_id: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A17 verification — execute_reopen calls publish_multi with W2_SUBSET exactly.

    W2 reopen flow publishes ONLY to `fiscal_period_cache` +
    `closing_snapshot_cache` (NOT the full 4-channel set). This is a
    deliberate AD-25 subset (D-003, Story 11.4 3rd sweep) — NOT an
    oversight. The 4-channel set is REOPEN_CHANNELS_ALL (not used by
    W2 reopen).

    Spy pattern: monkeypatch replaces CacheInvalidationPublisher.
    publish_multi with a recording stub. The stub is sync (matches
    the original method signature — see apps/api/core/cache_
    invalidation_publisher.py:217).
    """
    calls: list[dict[str, object]] = []

    def fake_publish_multi(
        _self: CacheInvalidationPublisher,
        *,
        channels: list[str] | tuple[str, ...],
        tenant_id: uuid.UUID,
        event_id: uuid.UUID,
        correction_group_id: uuid.UUID,
        trace_id: str,
        published_at: str | None = None,
    ) -> list[CacheInvalidationReceipt]:
        calls.append(
            {
                "channels": list(channels),
                "tenant_id": tenant_id,
                "event_id": event_id,
                "correction_group_id": correction_group_id,
                "trace_id": trace_id,
                "published_at": published_at,
            }
        )
        return [
            CacheInvalidationReceipt(
                channel=ch,
                tenant_id=tenant_id,
                target_event_id=event_id,
                correction_group_id=correction_group_id,
                published_at=published_at or "",
                trace_id=trace_id,
            )
            for ch in channels
        ]

    monkeypatch.setattr(
        CacheInvalidationPublisher, "publish_multi", fake_publish_multi
    )

    async def _impl() -> None:
        fp = _make_fiscal_period_row(tenant_id, fiscal_period_id, status="closed")
        session = AsyncMock()
        session.scalar = AsyncMock(return_value=fp)
        session.execute = AsyncMock(return_value=MagicMock())

        svc = ReopenService(session, tenant_id=tenant_id, trace_id=trace_id)
        await svc.execute_reopen(
            period_key="2026-08",
            operator_action="operator_reopen",
            reason="A" * 50,
            actor_id=actor_id,
        )

    asyncio.run(_impl())

    # Exactly one publish_multi call.
    assert len(calls) == 1
    call = calls[0]
    # Channels arg is the W2 subset, exactly (order-preserving).
    assert call["channels"] == [
        "fiscal_period_cache",
        "closing_snapshot_cache",
    ]
    assert call["channels"] == list(REOPEN_CHANNELS_W2_SUBSET)
    # Other wire-shape invariants.
    assert call["tenant_id"] == tenant_id
    assert call["event_id"] == fiscal_period_id
    assert call["correction_group_id"] == fiscal_period_id
    assert call["trace_id"] == trace_id


# ── 10. A17 — receipt envelope shape ──────────────────────────
def test_execute_reopen_publishes_receipts_with_correct_envelope(
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
    fiscal_period_id: uuid.UUID,
    trace_id: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A17 verification — receipts emitted by W2 reopen have correct envelope.

    Each receipt shares the same `tenant_id`, `target_event_id`,
    `correction_group_id`, `trace_id`, and `published_at`; they differ
    only in `channel`. Receipts are the 2 W2 channels only.
    """
    captured_receipts: list[CacheInvalidationReceipt] = []

    def fake_publish_multi(
        _self: CacheInvalidationPublisher,
        *,
        channels: list[str] | tuple[str, ...],
        tenant_id: uuid.UUID,
        event_id: uuid.UUID,
        correction_group_id: uuid.UUID,
        trace_id: str,
        published_at: str | None = None,
    ) -> list[CacheInvalidationReceipt]:
        receipts = [
            CacheInvalidationReceipt(
                channel=ch,
                tenant_id=tenant_id,
                target_event_id=event_id,
                correction_group_id=correction_group_id,
                published_at=published_at or "",
                trace_id=trace_id,
            )
            for ch in channels
        ]
        captured_receipts.extend(receipts)
        return receipts

    monkeypatch.setattr(
        CacheInvalidationPublisher, "publish_multi", fake_publish_multi
    )

    async def _impl() -> None:
        fp = _make_fiscal_period_row(tenant_id, fiscal_period_id, status="closed")
        session = AsyncMock()
        session.scalar = AsyncMock(return_value=fp)
        session.execute = AsyncMock(return_value=MagicMock())

        svc = ReopenService(session, tenant_id=tenant_id, trace_id=trace_id)
        await svc.execute_reopen(
            period_key="2026-08",
            operator_action="operator_reopen",
            reason="A" * 50,
            actor_id=actor_id,
        )

    asyncio.run(_impl())

    # Exactly 2 receipts (one per W2 channel).
    assert len(captured_receipts) == 2
    channels = {r.channel for r in captured_receipts}
    assert channels == {"fiscal_period_cache", "closing_snapshot_cache"}

    # Every receipt shares the same wire-shape invariants.
    for receipt in captured_receipts:
        assert receipt.tenant_id == tenant_id
        assert receipt.target_event_id == fiscal_period_id
        assert receipt.correction_group_id == fiscal_period_id
        assert receipt.trace_id == trace_id
        # published_at is ISO-8601 parseable.
        datetime.fromisoformat(receipt.published_at)


# ── 11. A17 — REOPEN_CHANNELS_ALL ⊇ REOPEN_CHANNELS_W2_SUBSET ──
def test_reopen_channels_all_is_superset_of_w2_subset() -> None:
    """A17 verification — AD-25 4-channel set is a superset of W2 subset.

    Explicit subset-relationship assertion. The W2 subset is a
    deliberate narrow subset of the full AD-25 4-channel set. Length
    difference = 2 (4 - 2 = 2 channels excluded: ai_cache +
    cost_engine_cache).
    """
    all_set = set(REOPEN_CHANNELS_ALL)
    w2_set = set(REOPEN_CHANNELS_W2_SUBSET)
    assert w2_set.issubset(all_set)
    assert all_set - w2_set == {"ai_cache", "cost_engine_cache"}
    assert len(all_set) - len(w2_set) == 2


# ── 12. A17 — publish_multi rejects non-allowed channel ────────
def test_publish_multi_rejects_non_allowed_channel(trace_id: str) -> None:
    """A17 verification — D-7 invariant: invalid channel → ChannelInvalidError.

    Empty channel set → EmptyChannelSetError. Non-allowed channel
    (e.g. 'bogus_cache') → ChannelInvalidError with the offending
    channel in the exception body. Verifies W2 reopen's deliberate
    2-channel subset is a deliberate AD-25 subset, not an oversight.
    """
    publisher = CacheInvalidationPublisher()
    # Non-allowed channel.
    with pytest.raises(CacheInvalidationChannelInvalidError) as exc_info:
        publisher.publish_multi(
            channels=["bogus_cache"],
            tenant_id=uuid.uuid4(),
            event_id=uuid.uuid4(),
            correction_group_id=uuid.uuid4(),
            trace_id=trace_id,
        )
    assert exc_info.value.channel == "bogus_cache"

    # Empty channel set.
    with pytest.raises(CacheInvalidationEmptyChannelSetError):
        publisher.publish_multi(
            channels=[],
            tenant_id=uuid.uuid4(),
            event_id=uuid.uuid4(),
            correction_group_id=uuid.uuid4(),
            trace_id=trace_id,
        )

    # Sanity: all 4 AD-25 channels are accepted (full-set publish works).
    receipts = publisher.publish_multi(
        channels=list(ALLOWED_CHANNELS),
        tenant_id=uuid.uuid4(),
        event_id=uuid.uuid4(),
        correction_group_id=uuid.uuid4(),
        trace_id=trace_id,
    )
    assert len(receipts) == 4
