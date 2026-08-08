"""apps.api.core.cache_invalidation_publisher — AD-25 cache invalidation publisher.

AD-25 cache invalidation notification (Story 11.1 PRIMARY wire — 1-channel).

Story 11.1 ships a single-channel publisher:
- channel FROZENSET = `{'ai_cache'}` (M10 AI cache invalidation target)
- M11 reversal sequence completes → publish(channel='ai_cache', ...) →
  M10 cache invalidation queue + AI cache reset.

Future expansion (deferred to 11-3 entry):
- channel FROZENSET extension: `cost_engine_cache`, `fiscal_period_cache`,
  `closing_snapshot_cache` etc.

AD-1 + AD-11 binding: this module is in `apps/api/core/` (infra layer).
It does NOT import `packages.cost_engine` directly. Pure-Python, no DB,
no clock in the publish() method (callers supply trace_id + published_at).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Final, NamedTuple

# ── Constants ────────────────────────────────────────────────
# AD-25 1-channel wire. FROZENSET — channel registry is immutable.
# Channel additions require explicit code change (no dynamic registration
# in MVP — this prevents accidental channel sprawl).
ALLOWED_CHANNELS: Final[frozenset[str]] = frozenset({"ai_cache"})

# Error codes.
ERROR_CODE_INVALID_CHANNEL: Final[str] = "INVALID_CACHE_INVALIDATION_CHANNEL"
ERROR_CODE_NON_UUID_TENANT: Final[str] = "NON_UUID_TENANT_ID"
ERROR_CODE_NON_UUID_EVENT: Final[str] = "NON_UUID_EVENT_ID"
ERROR_CODE_NON_UUID_CORRECTION_GROUP: Final[str] = "NON_UUID_CORRECTION_GROUP_ID"
ERROR_CODE_NON_STR_TRACE_ID: Final[str] = "NON_STR_TRACE_ID"

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
    """AD-25 publisher — 1-channel (ai_cache) for Story 11.1.

    Pure-Python — does NOT issue DB writes. Callers integrate the
    receipt into their audit payload (audit-first CR 1.1 pattern).
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
            channel: One of ALLOWED_CHANNELS. `ai_cache` is the only
                channel registered in 11-1 wire.
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
            raise ValueError(
                f"tenant_id must be UUID, got {type(tenant_id).__name__!r}"
            )
        if not isinstance(event_id, uuid.UUID):
            raise ValueError(
                f"event_id must be UUID, got {type(event_id).__name__!r}"
            )
        if not isinstance(correction_group_id, uuid.UUID):
            raise ValueError(
                f"correction_group_id must be UUID, got "
                f"{type(correction_group_id).__name__!r}"
            )
        if not isinstance(trace_id, str):
            raise ValueError(
                f"trace_id must be str, got {type(trace_id).__name__!r}"
            )
        if not isinstance(channel, str):
            raise ValueError(
                f"channel must be str, got {type(channel).__name__!r}"
            )
        if channel not in ALLOWED_CHANNELS:
            raise CacheInvalidationChannelInvalidError(
                channel=channel, trace_id=trace_id
            )

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


__all__ = [
    "ALLOWED_CHANNELS",
    "CACHE_INVALIDATION_INVALID_CHANNEL_KO",
    "CACHE_INVALIDATION_PUBLISHED_KO",
    "CacheInvalidationChannelInvalidError",
    "CacheInvalidationPublisher",
    "CacheInvalidationReceipt",
    "ERROR_CODE_INVALID_CHANNEL",
    "PAYLOAD_KEY_CHANNEL",
    "PAYLOAD_KEY_CORRECTION_GROUP_ID",
    "PAYLOAD_KEY_EVENT_ID",
    "PAYLOAD_KEY_PUBLISHED_AT",
    "PAYLOAD_KEY_TENANT_ID",
    "PAYLOAD_KEY_TRACE_ID",
]
