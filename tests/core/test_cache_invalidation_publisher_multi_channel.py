"""tests.core.test_cache_invalidation_publisher_multi_channel — AD-25 4-channel.

15 cases per AC #1 spec — verify the AD-25 multi-channel wire:
- ALLOWED_CHANNELS expanded 1 → 4 channels
- publish() still works for each of the 4 channels (back-compat)
- publish_multi() emits one receipt per channel
- publish_multi() validates channels + rejects empty set + rejects invalid
- Receipt ordering is deterministic (CHANNEL_ORDER_11_3)
- Receipt → dict conversion works for multi-channel payloads
- De-duplication in publish_multi()
"""

from __future__ import annotations

import uuid

import pytest

from apps.api.core.cache_invalidation_publisher import (
    ALLOWED_CHANNELS,
    CACHE_INVALIDATION_PUBLISHED_KO,
    CacheInvalidationChannelInvalidError,
    CacheInvalidationEmptyChannelSetError,
    CacheInvalidationPublisher,
    CacheInvalidationReceipt,
    ERROR_CODE_EMPTY_CHANNEL_SET,
    ERROR_CODE_INVALID_CHANNEL,
    PAYLOAD_KEY_CHANNEL,
)


# ── Common fixtures ──────────────────────────────────────────
@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def event_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def correction_group_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def trace_id() -> str:
    return "test-trace-11-3"


@pytest.fixture
def publisher() -> CacheInvalidationPublisher:
    return CacheInvalidationPublisher()


# ── 1. ALLOWED_CHANNELS expanded to 4 ────────────────────────
def test_allowed_channels_has_4_channels(publisher: CacheInvalidationPublisher) -> None:
    """ALLOWED_CHANNELS must have 4 channels after 11-3 expansion."""
    assert len(ALLOWED_CHANNELS) == 4
    for ch in (
        "ai_cache",
        "cost_engine_cache",
        "fiscal_period_cache",
        "closing_snapshot_cache",
    ):
        assert ch in ALLOWED_CHANNELS


# ── 2. publish() back-compat for each channel ────────────────
@pytest.mark.parametrize(
    "channel",
    [
        "ai_cache",
        "cost_engine_cache",
        "fiscal_period_cache",
        "closing_snapshot_cache",
    ],
)
def test_publish_single_channel_back_compat(
    publisher: CacheInvalidationPublisher,
    tenant_id: uuid.UUID,
    event_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    trace_id: str,
    channel: str,
) -> None:
    """publish() must still work for each of the 4 channels (back-compat)."""
    receipt = publisher.publish(
        channel=channel,
        tenant_id=tenant_id,
        event_id=event_id,
        correction_group_id=correction_group_id,
        trace_id=trace_id,
    )
    assert isinstance(receipt, CacheInvalidationReceipt)
    assert receipt.channel == channel
    assert receipt.tenant_id == tenant_id
    assert receipt.target_event_id == event_id
    assert receipt.correction_group_id == correction_group_id
    assert receipt.trace_id == trace_id


# ── 3. publish() rejects invalid channel ─────────────────────
def test_publish_rejects_invalid_channel(
    publisher: CacheInvalidationPublisher,
    tenant_id: uuid.UUID,
    event_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    trace_id: str,
) -> None:
    """publish() must raise on a channel not in ALLOWED_CHANNELS."""
    with pytest.raises(CacheInvalidationChannelInvalidError) as exc_info:
        publisher.publish(
            channel="not_a_channel",
            tenant_id=tenant_id,
            event_id=event_id,
            correction_group_id=correction_group_id,
            trace_id=trace_id,
        )
    assert exc_info.value.channel == "not_a_channel"
    assert exc_info.value.trace_id == trace_id


# ── 4. publish_multi() emits one receipt per channel ─────────
def test_publish_multi_emits_one_receipt_per_channel(
    publisher: CacheInvalidationPublisher,
    tenant_id: uuid.UUID,
    event_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    trace_id: str,
) -> None:
    """publish_multi() with 4 channels must emit 4 receipts."""
    channels = (
        "ai_cache",
        "cost_engine_cache",
        "fiscal_period_cache",
        "closing_snapshot_cache",
    )
    receipts = publisher.publish_multi(
        channels=channels,
        tenant_id=tenant_id,
        event_id=event_id,
        correction_group_id=correction_group_id,
        trace_id=trace_id,
    )
    assert len(receipts) == 4
    for receipt, ch in zip(receipts, channels, strict=True):
        assert receipt.channel == ch
        assert receipt.tenant_id == tenant_id
        assert receipt.target_event_id == event_id
        assert receipt.correction_group_id == correction_group_id
        assert receipt.trace_id == trace_id


# ── 5. publish_multi() with subset of channels ──────────────
def test_publish_multi_subset_of_channels(
    publisher: CacheInvalidationPublisher,
    tenant_id: uuid.UUID,
    event_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    trace_id: str,
) -> None:
    """publish_multi() with 2 channels must emit 2 receipts."""
    channels = ["fiscal_period_cache", "closing_snapshot_cache"]
    receipts = publisher.publish_multi(
        channels=channels,
        tenant_id=tenant_id,
        event_id=event_id,
        correction_group_id=correction_group_id,
        trace_id=trace_id,
    )
    assert len(receipts) == 2
    channels_in_receipts = {r.channel for r in receipts}
    assert channels_in_receipts == set(channels)


# ── 6. publish_multi() rejects empty channel set ────────────
def test_publish_multi_rejects_empty_set(
    publisher: CacheInvalidationPublisher,
    tenant_id: uuid.UUID,
    event_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    trace_id: str,
) -> None:
    """publish_multi() with empty channels must raise EmptyChannelSetError."""
    with pytest.raises(CacheInvalidationEmptyChannelSetError) as exc_info:
        publisher.publish_multi(
            channels=[],
            tenant_id=tenant_id,
            event_id=event_id,
            correction_group_id=correction_group_id,
            trace_id=trace_id,
        )
    assert exc_info.value.trace_id == trace_id
    assert ERROR_CODE_EMPTY_CHANNEL_SET == "EMPTY_CACHE_INVALIDATION_CHANNEL_SET"


# ── 7. publish_multi() rejects invalid channel (fail-fast) ───
def test_publish_multi_rejects_invalid_channel_fail_fast(
    publisher: CacheInvalidationPublisher,
    tenant_id: uuid.UUID,
    event_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    trace_id: str,
) -> None:
    """publish_multi() must fail-fast on the FIRST invalid channel."""
    with pytest.raises(CacheInvalidationChannelInvalidError) as exc_info:
        publisher.publish_multi(
            channels=["ai_cache", "not_a_channel", "cost_engine_cache"],
            tenant_id=tenant_id,
            event_id=event_id,
            correction_group_id=correction_group_id,
            trace_id=trace_id,
        )
    assert exc_info.value.channel == "not_a_channel"


# ── 8. publish_multi() deterministic ordering ───────────────
def test_publish_multi_deterministic_ordering(
    publisher: CacheInvalidationPublisher,
    tenant_id: uuid.UUID,
    event_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    trace_id: str,
) -> None:
    """publish_multi() output must follow CHANNEL_ORDER_11_3."""
    # Pass channels in REVERSE order — output must still be in
    # canonical order.
    channels = [
        "closing_snapshot_cache",
        "fiscal_period_cache",
        "cost_engine_cache",
        "ai_cache",
    ]
    receipts = publisher.publish_multi(
        channels=channels,
        tenant_id=tenant_id,
        event_id=event_id,
        correction_group_id=correction_group_id,
        trace_id=trace_id,
    )
    actual = [r.channel for r in receipts]
    expected = [
        "ai_cache",
        "cost_engine_cache",
        "fiscal_period_cache",
        "closing_snapshot_cache",
    ]
    assert actual == expected


# ── 9. publish_multi() de-duplicates channels ────────────────
def test_publish_multi_deduplicates_channels(
    publisher: CacheInvalidationPublisher,
    tenant_id: uuid.UUID,
    event_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    trace_id: str,
) -> None:
    """publish_multi() must de-dupe duplicate channels."""
    channels = ["ai_cache", "ai_cache", "cost_engine_cache"]
    receipts = publisher.publish_multi(
        channels=channels,
        tenant_id=tenant_id,
        event_id=event_id,
        correction_group_id=correction_group_id,
        trace_id=trace_id,
    )
    assert len(receipts) == 2
    assert [r.channel for r in receipts] == ["ai_cache", "cost_engine_cache"]


# ── 10. publish_multi() shared timestamp across all channels ─
def test_publish_multi_shared_published_at(
    publisher: CacheInvalidationPublisher,
    tenant_id: uuid.UUID,
    event_id: uuid.UUID,
    correction_group_id: uuid.UUID,
) -> None:
    """publish_multi() must apply the same published_at to all receipts."""
    fixed_ts = "2026-08-09T10:00:00+00:00"
    receipts = publisher.publish_multi(
        channels=["ai_cache", "cost_engine_cache"],
        tenant_id=tenant_id,
        event_id=event_id,
        correction_group_id=correction_group_id,
        trace_id="trace-xyz",
        published_at=fixed_ts,
    )
    assert all(r.published_at == fixed_ts for r in receipts)


# ── 11. publish_multi() shared trace_id across all channels ──
def test_publish_multi_shared_trace_id(
    publisher: CacheInvalidationPublisher,
    tenant_id: uuid.UUID,
    event_id: uuid.UUID,
    correction_group_id: uuid.UUID,
) -> None:
    """publish_multi() must apply the same trace_id to all receipts."""
    shared_trace = "shared-trace-id"
    receipts = publisher.publish_multi(
        channels=["ai_cache", "fiscal_period_cache"],
        tenant_id=tenant_id,
        event_id=event_id,
        correction_group_id=correction_group_id,
        trace_id=shared_trace,
    )
    assert all(r.trace_id == shared_trace for r in receipts)


# ── 12. receipt_to_dict() includes channel field ─────────────
def test_receipt_to_dict_includes_channel(
    publisher: CacheInvalidationPublisher,
    tenant_id: uuid.UUID,
    event_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    trace_id: str,
) -> None:
    """receipt_to_dict() must include channel field (CR 1.1 self-describing)."""
    receipt = publisher.publish(
        channel="closing_snapshot_cache",
        tenant_id=tenant_id,
        event_id=event_id,
        correction_group_id=correction_group_id,
        trace_id=trace_id,
    )
    payload = CacheInvalidationPublisher.receipt_to_dict(receipt)
    assert PAYLOAD_KEY_CHANNEL in payload
    assert payload[PAYLOAD_KEY_CHANNEL] == "closing_snapshot_cache"


# ── 13. receipts_to_dicts() converts multi-channel list ─────
def test_receipts_to_dicts_converts_list(
    publisher: CacheInvalidationPublisher,
    tenant_id: uuid.UUID,
    event_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    trace_id: str,
) -> None:
    """receipts_to_dicts() must convert a list of receipts to dicts."""
    receipts = publisher.publish_multi(
        channels=["ai_cache", "cost_engine_cache"],
        tenant_id=tenant_id,
        event_id=event_id,
        correction_group_id=correction_group_id,
        trace_id=trace_id,
    )
    payload = CacheInvalidationPublisher.receipts_to_dicts(receipts)
    assert len(payload) == 2
    assert payload[0][PAYLOAD_KEY_CHANNEL] == "ai_cache"
    assert payload[1][PAYLOAD_KEY_CHANNEL] == "cost_engine_cache"


# ── 14. CACHE_INVALIDATION_PUBLISHED_KO constant exists ─────
def test_korean_constant_exists() -> None:
    """CACHE_INVALIDATION_PUBLISHED_KO must exist (AD-15 §11)."""
    assert CACHE_INVALIDATION_PUBLISHED_KO == "캐시 무효화 알림 발행 완료"


# ── 15. ERROR_CODE_INVALID_CHANNEL stable identifier ────────
def test_error_code_stable_identifier() -> None:
    """ERROR_CODE_INVALID_CHANNEL must be the documented string."""
    assert ERROR_CODE_INVALID_CHANNEL == "INVALID_CACHE_INVALIDATION_CHANNEL"