"""apps.api.core.cache_invalidation_listener_adapters — LISTEN daemon adapter factories.

Story 13.1 (LISTEN/NOTIFY Consume Trigger EXTENSION, A39/A51/A52 결정 wire):
Builds the 4 channel adapter factories (M10/M3/M11) for the LISTEN
daemon. Each adapter handles channel-specific cache eviction:

  - `ai_cache`               → M10AIInvalidationAdapter (DELETE FROM ai_insight_cache)
  - `cost_engine_cache`      → M3CostEngineInvalidationAdapter (in-process LRU evict)
  - `fiscal_period_cache`    → M11FiscalPeriodInvalidationAdapter (fiscal_periods cache evict)
  - `closing_snapshot_cache` → M11ClosingSnapshotInvalidationAdapter (snapshot cache evict)

Per AD-25 (ARCHITECTURE-SPINE.md §142-148 verbatim):
  "M10 cache key is `(tenant_id, period_key, calculation_result_hash)`.
   A new AD-4 commit, an AD-22 reversal insert, or an M11 reopen emits
   one DB notification per channel."

Cross-channel contamination 방어: each adapter's `on_invalidate` method
accepts payloads ONLY for its own channel — the listener's dispatch
table isolates channel-specific logic so an adapter cannot accidentally
process a payload intended for another channel.

AD-1 + AD-11 binding: this module is in `apps/api/core/` (infra layer).
It does NOT import `packages.cost_engine` directly. Adapters lazily
import their respective modules to avoid circular imports.
"""

from __future__ import annotations

import logging
from typing import Any

from apps.api.core.cache_invalidation_listener import (
    PAYLOAD_KEY_CHANNEL,
    PAYLOAD_KEY_PERIOD_KEY,
    PAYLOAD_KEY_TENANT_ID,
    PAYLOAD_KEY_TRACE_ID,
    CacheInvalidationAdapter,
)
from apps.api.core.cache_invalidation_publisher import ALLOWED_CHANNELS

logger = logging.getLogger(__name__)


# ── Adapter factory return type ──────────────────────────────
def _make_adapter(channel: str) -> CacheInvalidationAdapter:
    """Build the channel-specific adapter instance.

    Lazy dispatch via per-channel factory functions. Keeps the import
    graph clean (M10/M3/M11 are imported only when their adapter is
    first looked up).
    """
    if channel == "ai_cache":
        return _M10AIInvalidationAdapter()
    if channel == "cost_engine_cache":
        return _M3CostEngineInvalidationAdapter()
    if channel == "fiscal_period_cache":
        return _M11FiscalPeriodInvalidationAdapter()
    if channel == "closing_snapshot_cache":
        return _M11ClosingSnapshotInvalidationAdapter()
    raise ValueError(
        f"unknown channel {channel!r} (not in ALLOWED_CHANNELS)"
    )


def build_default_adapter_factories() -> dict[str, Any]:
    """Build the default adapter factory map for the 4 channels.

    Returns:
        Dict mapping channel name → adapter factory callable. The
        listener calls each factory to instantiate a fresh adapter.
    """
    return {
        channel: (lambda c=channel: _make_adapter(c))
        for channel in ALLOWED_CHANNELS
    }


# ── M10 AI cache invalidation adapter ────────────────────────
class _M10AIInvalidationAdapter:
    """AD-25 channel adapter for `ai_cache` (M10 AI cache invalidation).

    Story 11.1 wire: DELETE FROM ai_insight_cache WHERE tenant_id=? AND
    period_key=?. F10.1-(d) verbatim `channel = 'ai_cache'` filter ONLY
    consume (cross-channel contamination 방어).

    Per AD-25: M10 cache key is `(tenant_id, period_key,
    calculation_result_hash)`. The hash component is NOT in the
    payload — eviction is by (tenant_id, period_key) tuple only.
    """

    channel: str = "ai_cache"

    async def on_invalidate(self, payload: dict[str, str]) -> None:
        """Evict AI insight cache entries for the given (tenant_id, period_key).

        Args:
            payload: 5-key dict (channel, correction_group_id, period_key,
                tenant_id, trace_id). `channel` MUST be `ai_cache` —
                the listener's dispatch table enforces this.
        """
        # Channel-specific filter (F10.1-(d) verbatim cross-channel
        # contamination 방어). The listener's dispatch table already
        # routes by channel, but we re-verify here for defense-in-depth.
        if payload[PAYLOAD_KEY_CHANNEL] != "ai_cache":
            logger.warning(
                "M10AIInvalidationAdapter received non-ai_cache payload "
                "(channel=%s) — skipping",
                payload.get(PAYLOAD_KEY_CHANNEL),
            )
            return

        tenant_id = payload[PAYLOAD_KEY_TENANT_ID]
        period_key = payload[PAYLOAD_KEY_PERIOD_KEY]
        trace_id = payload[PAYLOAD_KEY_TRACE_ID]

        # Delete from ai_insight_cache (Story 11.1 wire pattern).
        # NOTE: lazy import to avoid circular dependency.
        try:
            from apps.api.core.db import get_asyncpg_pool

            pool = await get_asyncpg_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    DELETE FROM ai_insight_cache
                    WHERE tenant_id = $1::uuid AND period_key = $2
                    """,
                    tenant_id,
                    period_key,
                )
            logger.info(
                "M10AIInvalidationAdapter: evicted ai_insight_cache "
                "(tenant_id=%s, period_key=%s, trace_id=%s)",
                tenant_id,
                period_key,
                trace_id,
            )
        except Exception as exc:
            logger.exception(
                "M10AIInvalidationAdapter eviction failed: %s", exc
            )


# ── M3 cost engine invalidation adapter ──────────────────────
class _M3CostEngineInvalidationAdapter:
    """AD-25 channel adapter for `cost_engine_cache` (M3 cost engine).

    Story 11.3 wire: in-process LRU cache eviction hook. AD-5 stdlib-only
    보존 (NO DB write from kernel). The cost engine maintains an in-process
    LRU keyed by (tenant_id, period_key) for calculation result cache.
    """

    channel: str = "cost_engine_cache"

    async def on_invalidate(self, payload: dict[str, str]) -> None:
        """Evict cost engine LRU cache entries for the given (tenant_id, period_key).

        Args:
            payload: 5-key dict (channel, correction_group_id, period_key,
                tenant_id, trace_id). `channel` MUST be `cost_engine_cache`.
        """
        if payload[PAYLOAD_KEY_CHANNEL] != "cost_engine_cache":
            logger.warning(
                "M3CostEngineInvalidationAdapter received non-cost_engine_cache "
                "payload (channel=%s) — skipping",
                payload.get(PAYLOAD_KEY_CHANNEL),
            )
            return

        tenant_id = payload[PAYLOAD_KEY_TENANT_ID]
        period_key = payload[PAYLOAD_KEY_PERIOD_KEY]
        trace_id = payload[PAYLOAD_KEY_TRACE_ID]

        # M3 cost engine in-process LRU eviction (AD-5 stdlib-only).
        try:
            from packages.cost_engine.lru_cache import evict_period_key

            evict_period_key(tenant_id=tenant_id, period_key=period_key)
            logger.info(
                "M3CostEngineInvalidationAdapter: evicted LRU "
                "(tenant_id=%s, period_key=%s, trace_id=%s)",
                tenant_id,
                period_key,
                trace_id,
            )
        except ImportError:
            # packages.cost_engine.lru_cache may not be available in
            # MVP test environments — log + skip (graceful degradation).
            logger.warning(
                "M3CostEngineInvalidationAdapter: cost_engine.lru_cache "
                "not available — skipping"
            )
        except Exception as exc:
            logger.exception(
                "M3CostEngineInvalidationAdapter eviction failed: %s", exc
            )


# ── M11 fiscal period invalidation adapter ───────────────────
class _M11FiscalPeriodInvalidationAdapter:
    """AD-25 channel adapter for `fiscal_period_cache` (M11 fiscal_periods).

    Story 11.3 wire: invalidate in-memory fiscal_period cache when state
    transitions to 'committed' (AD-20 commit broadcast).
    """

    channel: str = "fiscal_period_cache"

    async def on_invalidate(self, payload: dict[str, str]) -> None:
        """Evict fiscal_period cache entries for the given (tenant_id, period_key).

        Args:
            payload: 5-key dict (channel, correction_group_id, period_key,
                tenant_id, trace_id). `channel` MUST be `fiscal_period_cache`.
        """
        if payload[PAYLOAD_KEY_CHANNEL] != "fiscal_period_cache":
            logger.warning(
                "M11FiscalPeriodInvalidationAdapter received non-fiscal_period_cache "
                "payload (channel=%s) — skipping",
                payload.get(PAYLOAD_KEY_CHANNEL),
            )
            return

        tenant_id = payload[PAYLOAD_KEY_TENANT_ID]
        period_key = payload[PAYLOAD_KEY_PERIOD_KEY]
        trace_id = payload[PAYLOAD_KEY_TRACE_ID]

        try:
            from apps.api.modules.m11_close.services.fiscal_period_service import (
                invalidate_fiscal_period_cache,
            )

            invalidate_fiscal_period_cache(
                tenant_id=tenant_id, period_key=period_key
            )
            logger.info(
                "M11FiscalPeriodInvalidationAdapter: evicted fiscal_period_cache "
                "(tenant_id=%s, period_key=%s, trace_id=%s)",
                tenant_id,
                period_key,
                trace_id,
            )
        except ImportError:
            logger.warning(
                "M11FiscalPeriodInvalidationAdapter: invalidate_fiscal_period_cache "
                "not available — skipping"
            )
        except Exception as exc:
            logger.exception(
                "M11FiscalPeriodInvalidationAdapter eviction failed: %s", exc
            )


# ── M11 closing snapshot invalidation adapter ───────────────
class _M11ClosingSnapshotInvalidationAdapter:
    """AD-25 channel adapter for `closing_snapshot_cache` (M11 closing_snapshot).

    Story 11.3 wire: invalidate closing_snapshot hash cache when a new
    snapshot is committed, forcing a recompute on next read.
    """

    channel: str = "closing_snapshot_cache"

    async def on_invalidate(self, payload: dict[str, str]) -> None:
        """Evict closing_snapshot cache entries for the given (tenant_id, period_key).

        Args:
            payload: 5-key dict (channel, correction_group_id, period_key,
                tenant_id, trace_id). `channel` MUST be `closing_snapshot_cache`.
        """
        if payload[PAYLOAD_KEY_CHANNEL] != "closing_snapshot_cache":
            logger.warning(
                "M11ClosingSnapshotInvalidationAdapter received non-closing_snapshot_cache "
                "payload (channel=%s) — skipping",
                payload.get(PAYLOAD_KEY_CHANNEL),
            )
            return

        tenant_id = payload[PAYLOAD_KEY_TENANT_ID]
        period_key = payload[PAYLOAD_KEY_PERIOD_KEY]
        trace_id = payload[PAYLOAD_KEY_TRACE_ID]

        try:
            from apps.api.modules.m11_close.services.snapshot_service import (
                invalidate_closing_snapshot_cache,
            )

            invalidate_closing_snapshot_cache(
                tenant_id=tenant_id, period_key=period_key
            )
            logger.info(
                "M11ClosingSnapshotInvalidationAdapter: evicted closing_snapshot_cache "
                "(tenant_id=%s, period_key=%s, trace_id=%s)",
                tenant_id,
                period_key,
                trace_id,
            )
        except ImportError:
            logger.warning(
                "M11ClosingSnapshotInvalidationAdapter: invalidate_closing_snapshot_cache "
                "not available — skipping"
            )
        except Exception as exc:
            logger.exception(
                "M11ClosingSnapshotInvalidationAdapter eviction failed: %s", exc
            )


__all__ = [
    "build_default_adapter_factories",
]
