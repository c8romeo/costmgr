"""apps.api.core.cache_invalidation_publisher — AD-25 cache invalidation publisher.

AD-25 cache invalidation notification (Story 11.1 → 11.3 wire expansion).

Story 11.1 ships a 1-channel publisher:
- channel FROZENSET = `{'ai_cache'}` (M10 AI cache invalidation target)
- M11 reversal sequence completes → publish(channel='ai_cache', ...) →
  M10 cache invalidation queue + AI cache reset.

Story 11.3 wire expands to 4 channels:
- `ai_cache`               — M10 AI cache invalidation (11-1 보존)
- `cost_engine_cache`      — M3 cost engine calculation result cache
- `fiscal_period_cache`    — M11 fiscal_periods + fiscal_period_snapshots
                              metadata cache
- `closing_snapshot_cache` — M11 closing_snapshot + ledger closing event
                              cache

Per AD-25:
  "M10 cache key is `(tenant_id, period_key, calculation_result_hash)`.
   A new AD-4 commit, an AD-22 reversal insert, or an M11 reopen emits
   one DB notification per channel."

Cross-channel fan-out: `publish_multi()` emits one receipt per channel
(all share the same correction_group_id + trace_id). Channels must
form a non-empty subset of ALLOWED_CHANNELS — invalid channels raise
`CacheInvalidationChannelInvalidError` with the offending channel in
the exception body.

AD-1 + AD-11 binding: this module is in `apps/api/core/` (infra layer).
It does NOT import `packages.cost_engine` directly. Pure-Python, no DB,
no clock in the publish() method (callers supply trace_id + published_at).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Final, NamedTuple

# ── Constants ────────────────────────────────────────────────
# AD-25 multi-channel wire (Story 11.3 expansion).
# FROZENSET — channel registry is immutable. Channel additions require
# explicit code change (no dynamic registration in MVP — this prevents
# accidental channel sprawl).
#
# Mirrored in apps/api/alembic/versions/0021_cache_invalidation_multi_channel.py
ALLOWED_CHANNELS: Final[frozenset[str]] = frozenset(
    {
        "ai_cache",
        "cost_engine_cache",
        "fiscal_period_cache",
        "closing_snapshot_cache",
    }
)

# Channel ordering — used by publish_multi() to produce a stable receipt
# sequence. The order is the same as in the DB CHECK constraint.
_CHANNEL_ORDER_11_3: Final[tuple[str, ...]] = (
    "ai_cache",
    "cost_engine_cache",
    "fiscal_period_cache",
    "closing_snapshot_cache",
)

# Error codes.
ERROR_CODE_INVALID_CHANNEL: Final[str] = "INVALID_CACHE_INVALIDATION_CHANNEL"
ERROR_CODE_NON_UUID_TENANT: Final[str] = "NON_UUID_TENANT_ID"
ERROR_CODE_NON_UUID_EVENT: Final[str] = "NON_UUID_EVENT_ID"
ERROR_CODE_NON_UUID_CORRECTION_GROUP: Final[str] = "NON_UUID_CORRECTION_GROUP_ID"
ERROR_CODE_NON_STR_TRACE_ID: Final[str] = "NON_STR_TRACE_ID"
ERROR_CODE_EMPTY_CHANNEL_SET: Final[str] = "EMPTY_CACHE_INVALIDATION_CHANNEL_SET"

# Channel discriminator — payload self-describing (CR 1.1 lesson).
PAYLOAD_KEY_CHANNEL: Final[str] = "channel"
PAYLOAD_KEY_TENANT_ID: Final[str] = "tenant_id"
PAYLOAD_KEY_EVENT_ID: Final[str] = "event_id"
PAYLOAD_KEY_CORRECTION_GROUP_ID: Final[str] = "correction_group_id"
PAYLOAD_KEY_TRACE_ID: Final[str] = "trace_id"
PAYLOAD_KEY_PUBLISHED_AT: Final[str] = "published_at"

# Korean constants — AD-15 §11 SSOT.
CACHE_INVALIDATION_PUBLISHED_KO: Final[str] = "캐시 무효화 알림 발행 완료"
CACHE_INVALIDATION_INVALID_CHANNEL_KO: Final[str] = "지원하지 않는 캐시 무효화 채널"
CACHE_INVALIDATION_MULTI_PUBLISHED_KO: Final[str] = "다중 채널 캐시 무효화 발행 완료"


# ── Typed exception ──────────────────────────────────────────
class CacheInvalidationChannelInvalidError(Exception):
    """422 CACHE_INVALIDATION_INVALID_CHANNEL — channel not in FROZENSET."""

    def __init__(
        self,
        *,
        channel: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"cache invalidation channel {channel!r} not in allowed "
            f"set {sorted(ALLOWED_CHANNELS)}"
        )
        self.channel = channel
        self.trace_id = trace_id


class CacheInvalidationEmptyChannelSetError(ValueError):
    """ValueError subclass — empty channel set passed to publish_multi()."""

    def __init__(self, *, trace_id: str) -> None:
        super().__init__(
            "publish_multi() requires at least one channel " f"(trace_id={trace_id!r})"
        )
        self.trace_id = trace_id


# ── CacheInvalidationReceipt NamedTuple ──────────────────────
class CacheInvalidationReceipt(NamedTuple):
    """Receipt envelope — service layer returns this to callers."""

    channel: str
    tenant_id: uuid.UUID
    target_event_id: uuid.UUID
    correction_group_id: uuid.UUID
    published_at: str
    trace_id: str


# ── CacheInvalidationPublisher ───────────────────────────────
class CacheInvalidationPublisher:
    """AD-25 publisher — 4-channel (Story 11.3 wire).

    Pure-Python — does NOT issue DB writes. Callers integrate the
    receipt into their audit payload (audit-first CR 1.1 pattern).

    Two entry points:
    - publish() — single channel (back-compat with 11-1 wire)
    - publish_multi() — fan-out across a non-empty subset of channels
      (AD-25 multi-channel wire)

    Both return / yield `CacheInvalidationReceipt` envelopes. All
    receipts in a publish_multi() call share the same correction_group_id
    + trace_id + target_event_id + tenant_id — they differ only in the
    `channel` field, which is what each cache consumer (M10 AI, M3 cost
    engine, M11 fiscal_period, M11 closing_snapshot) listens on.
    """

    def publish(
        self,
        *,
        channel: str,
        tenant_id: uuid.UUID,
        event_id: uuid.UUID,
        correction_group_id: uuid.UUID,
        trace_id: str,
        published_at: str | None = None,
    ) -> CacheInvalidationReceipt:
        """Publish a cache invalidation receipt for `channel`.

        Args:
            channel: One of ALLOWED_CHANNELS (4 channels: ai_cache +
                cost_engine_cache + fiscal_period_cache + closing_snapshot_cache).
            tenant_id: Owning tenant.
            event_id: inventory_ledger.event_id of the reversal target.
            correction_group_id: correction_group_id linking negating +
                corrected rows.
            trace_id: Request correlation ID.
            published_at: Optional ISO-8601 timestamp. Defaults to
                `datetime.now(tz=UTC).isoformat()`.

        Returns:
            CacheInvalidationReceipt named tuple.

        Raises:
            CacheInvalidationChannelInvalidError: channel not in ALLOWED_CHANNELS.
            ValueError: input shape violations.
        """
        if not isinstance(tenant_id, uuid.UUID):
            raise ValueError(f"tenant_id must be UUID, got {type(tenant_id).__name__!r}")
        if not isinstance(event_id, uuid.UUID):
            raise ValueError(f"event_id must be UUID, got {type(event_id).__name__!r}")
        if not isinstance(correction_group_id, uuid.UUID):
            raise ValueError(
                f"correction_group_id must be UUID, got " f"{type(correction_group_id).__name__!r}"
            )
        if not isinstance(trace_id, str):
            raise ValueError(f"trace_id must be str, got {type(trace_id).__name__!r}")
        if not isinstance(channel, str):
            raise ValueError(f"channel must be str, got {type(channel).__name__!r}")
        if channel not in ALLOWED_CHANNELS:
            raise CacheInvalidationChannelInvalidError(channel=channel, trace_id=trace_id)

        # Defense-in-depth: trace_id non-empty.
        if not trace_id:
            raise ValueError("trace_id must be non-empty")

        ts = published_at if published_at is not None else datetime.now(tz=UTC).isoformat()
        return CacheInvalidationReceipt(
            channel=channel,
            tenant_id=tenant_id,
            target_event_id=event_id,
            correction_group_id=correction_group_id,
            published_at=ts,
            trace_id=trace_id,
        )

    def publish_multi(
        self,
        *,
        channels: list[str] | tuple[str, ...],
        tenant_id: uuid.UUID,
        event_id: uuid.UUID,
        correction_group_id: uuid.UUID,
        trace_id: str,
        published_at: str | None = None,
    ) -> list[CacheInvalidationReceipt]:
        """AD-25 multi-channel fan-out — emit one receipt per channel.

        All receipts share the same correction_group_id + trace_id +
        target_event_id + tenant_id; they differ only in `channel`.

        Channels must be a non-empty subset of ALLOWED_CHANNELS. The
        output order is deterministic: channels are sorted by
        `_CHANNEL_ORDER_11_3` (same order as the DB CHECK constraint).

        Args:
            channels: Non-empty list/tuple of channel names.
            tenant_id: Owning tenant.
            event_id: Trigger event_id (typically inventory_ledger.event_id
                for AD-22 reversals, or fiscal_period_snapshots.snapshot_id
                for AD-20 commit transitions).
            correction_group_id: correction_group_id linking the
                reversal pair (AD-22) or commit broadcast (AD-4).
            trace_id: Request correlation ID.
            published_at: Optional ISO-8601 timestamp applied to all
                receipts. Defaults to `datetime.now(tz=UTC).isoformat()`.

        Returns:
            List of CacheInvalidationReceipt — one per channel.

        Raises:
            CacheInvalidationEmptyChannelSetError: empty channel set.
            CacheInvalidationChannelInvalidError: any channel not in
                ALLOWED_CHANNELS (the FIRST invalid channel is reported).
            ValueError: input shape violations.
        """
        if not isinstance(channels, list | tuple):
            raise ValueError(f"channels must be list or tuple, got " f"{type(channels).__name__!r}")
        if not channels:
            raise CacheInvalidationEmptyChannelSetError(trace_id=trace_id)

        # Validate ALL channels first (fail-fast — report the first invalid).
        for ch in channels:
            if not isinstance(ch, str):
                raise ValueError(f"channel must be str, got {type(ch).__name__!r}")
            if ch not in ALLOWED_CHANNELS:
                raise CacheInvalidationChannelInvalidError(channel=ch, trace_id=trace_id)

        # Validate the shared inputs ONCE (publish() would re-validate).
        if not isinstance(tenant_id, uuid.UUID):
            raise ValueError(f"tenant_id must be UUID, got {type(tenant_id).__name__!r}")
        if not isinstance(event_id, uuid.UUID):
            raise ValueError(f"event_id must be UUID, got {type(event_id).__name__!r}")
        if not isinstance(correction_group_id, uuid.UUID):
            raise ValueError(
                f"correction_group_id must be UUID, got " f"{type(correction_group_id).__name__!r}"
            )
        if not isinstance(trace_id, str):
            raise ValueError(f"trace_id must be str, got {type(trace_id).__name__!r}")
        if not trace_id:
            raise ValueError("trace_id must be non-empty")

        # Stable ordering: _CHANNEL_ORDER_11_3. De-dupe while preserving
        # the canonical order (so callers can pass a `set` if desired).
        order_index = {c: i for i, c in enumerate(_CHANNEL_ORDER_11_3)}
        unique_channels = sorted(set(channels), key=lambda c: order_index[c])

        ts = published_at if published_at is not None else datetime.now(tz=UTC).isoformat()
        return [
            CacheInvalidationReceipt(
                channel=ch,
                tenant_id=tenant_id,
                target_event_id=event_id,
                correction_group_id=correction_group_id,
                published_at=ts,
                trace_id=trace_id,
            )
            for ch in unique_channels
        ]

    # ── Receipt → dict (for audit-first payload) ────────────────
    @staticmethod
    def receipt_to_dict(receipt: CacheInvalidationReceipt) -> dict[str, str]:
        """Convert receipt to audit payload dict (CR 1.1 self-describing)."""
        return {
            PAYLOAD_KEY_CHANNEL: receipt.channel,
            PAYLOAD_KEY_TENANT_ID: str(receipt.tenant_id),
            PAYLOAD_KEY_EVENT_ID: str(receipt.target_event_id),
            PAYLOAD_KEY_CORRECTION_GROUP_ID: str(receipt.correction_group_id),
            PAYLOAD_KEY_TRACE_ID: receipt.trace_id,
            PAYLOAD_KEY_PUBLISHED_AT: receipt.published_at,
        }

    @staticmethod
    def receipts_to_dicts(
        receipts: list[CacheInvalidationReceipt],
    ) -> list[dict[str, str]]:
        """Convert a multi-channel receipt list to a list of audit payload dicts."""
        return [CacheInvalidationPublisher.receipt_to_dict(r) for r in receipts]


__all__ = [
    "ALLOWED_CHANNELS",
    "CACHE_INVALIDATION_INVALID_CHANNEL_KO",
    "CACHE_INVALIDATION_MULTI_PUBLISHED_KO",
    "CACHE_INVALIDATION_PUBLISHED_KO",
    "CacheInvalidationChannelInvalidError",
    "CacheInvalidationEmptyChannelSetError",
    "CacheInvalidationPublisher",
    "CacheInvalidationReceipt",
    "ERROR_CODE_EMPTY_CHANNEL_SET",
    "ERROR_CODE_INVALID_CHANNEL",
    "PAYLOAD_KEY_CHANNEL",
    "PAYLOAD_KEY_CORRECTION_GROUP_ID",
    "PAYLOAD_KEY_EVENT_ID",
    "PAYLOAD_KEY_PUBLISHED_AT",
    "PAYLOAD_KEY_TENANT_ID",
    "PAYLOAD_KEY_TRACE_ID",
]
