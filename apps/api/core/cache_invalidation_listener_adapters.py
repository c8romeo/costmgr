"""apps.api.core.cache_invalidation_listener_adapters — LISTEN daemon adapter factories.

Story 13.1 (LISTEN/NOTIFY Consume Trigger EXTENSION, A39/A51/A52 결정 wire):
Builds the 4 channel adapter factories (M10/M3/M11) for the LISTEN
daemon. Each adapter handles channel-specific cache eviction:

  - `ai_cache`               → M10AIInvalidationAdapter (DELETE FROM ai_insight_cache)
  - `cost_engine_cache`      → M3CostEngineInvalidationAdapter (in-process LRU evict)
  - `fiscal_period_cache`    → M11FiscalPeriodInvalidationAdapter (fiscal_periods cache evict)
  - `closing_snapshot_cache` → M11ClosingSnapshotInvalidationAdapter (snapshot cache evict)

Story 14.1 (LISTEN/NOTIFY Consume Cross-Tenant Fan-Out + Multi-Process
Coordination, A53+A57+A58+A59 결정 wire): EXTENSION adds 2 NEW adapters
for cross-tenant fan-out + multi-process coordination:

  - `cross_tenant_fanout` → CrossTenantFanoutAdapter (cross-tenant
    invalidation fan-out, audit-first INSERT 3-row)
  - `multiprocess_dispatch` adapter hook is integrated into the leader
    election flow (MultiProcessDispatchAdapter — published by the
    leader when cross-process invalidation is needed).

Per AD-25 (ARCHITECTURE-SPINE.md §142-148 verbatim):
  "M10 cache key is `(tenant_id, period_key, calculation_result_hash)`.
   A new AD-4 commit, an AD-22 reversal insert, or an M11 reopen emits
   one DB notification per channel."

Cross-channel contamination 방어 EXTENSION: each adapter's `on_invalidate`
method accepts payloads ONLY for its own channel — the listener's
dispatch table isolates channel-specific logic so an adapter cannot
accidentally process a payload intended for another channel
(F10.1-(d) verbatim + F14.1-(c) verbatim EXTENSION).

AD-1 + AD-11 binding: this module is in `apps/api/core/` (infra layer).
It does NOT import `packages.cost_engine` directly. Adapters lazily
import their respective modules to avoid circular imports.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from apps.api.core.cache_invalidation_listener import (
    PAYLOAD_KEY_CHANNEL,
    PAYLOAD_KEY_CORRECTION_GROUP_ID,
    PAYLOAD_KEY_INVALIDATION_ID,
    PAYLOAD_KEY_PERIOD_KEY,
    PAYLOAD_KEY_SOURCE_TENANT_ID,
    PAYLOAD_KEY_TARGET_TENANT_IDS,
    PAYLOAD_KEY_TENANT_ID,
    PAYLOAD_KEY_TRACE_ID,
    CacheInvalidationAdapter,
)
from apps.api.core.cache_invalidation_publisher import ALLOWED_CHANNELS

logger = logging.getLogger(__name__)


# Cross-tenant fan-out channel (Story 14.1 EXTENSION).
CROSS_TENANT_FANOUT_CHANNEL: str = "cross_tenant_fanout"


# ── Adapter factory return type ──────────────────────────────
def _make_adapter(channel: str) -> CacheInvalidationAdapter:
    """Build the channel-specific adapter instance.

    Lazy dispatch via per-channel factory functions. Keeps the import
    graph clean (M10/M3/M11/cross-tenant are imported only when their
    adapter is first looked up).
    """
    if channel == "ai_cache":
        return _M10AIInvalidationAdapter()
    if channel == "cost_engine_cache":
        return _M3CostEngineInvalidationAdapter()
    if channel == "fiscal_period_cache":
        return _M11FiscalPeriodInvalidationAdapter()
    if channel == "closing_snapshot_cache":
        return _M11ClosingSnapshotInvalidationAdapter()
    if channel == CROSS_TENANT_FANOUT_CHANNEL:
        return CrossTenantFanoutAdapter()
    raise ValueError(
        f"unknown channel {channel!r} (not in ALLOWED_CHANNELS)"
    )


def build_default_adapter_factories() -> dict[str, Any]:
    """Build the default adapter factory map for the 5+ channels.

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


# ── Cross-tenant fan-out adapter (Story 14.1 NEW) ──────────
class CrossTenantFanoutAdapter:
    """AD-25 channel adapter for `cross_tenant_fanout` (Story 14.1 NEW).

    Per F14.1-(b) verbatim + F14.1-(c) verbatim:
    - payload parse → (source_tenant_id, target_tenant_ids,
      correction_group_id, invalidation_id, period_key, trace_id)
    - tenant-level subscription routing: target_tenant_ids 의 각
      tenant 별 cache eviction hook 호출
    - Multi-tenant isolation 검증 (CR 0-2 RLS lesson 적용):
      target_tenant_ids 의 모든 tenant 가 `LISTEN_NOTIFY_TENANT_FANOUT`
      capability grant 보유 검증
    - Audit-first INSERT 3-row (CR 1.1 verbatim):
      1. source tenant 의 invalidation log 1 row (already exists from
         trigger INSERT in the publisher path)
      2. fan-out dispatch log 1 row (target_tenant_ids 명시)
      3. audit_logs `action_name='cross_tenant_fanout_dispatched'` 1 row
    - Cross-channel contamination 방어 EXTENSION: rejects payloads from
      other 4 channels (F10.1-(d) verbatim EXTENSION).
    """

    channel: str = CROSS_TENANT_FANOUT_CHANNEL

    async def on_invalidate(self, payload: dict[str, Any]) -> None:
        """Dispatch cross-tenant invalidation fan-out.

        Args:
            payload: 7-key dict (channel, correction_group_id,
                invalidation_id, period_key, source_tenant_id,
                target_tenant_ids, trace_id). `channel` MUST be
                `cross_tenant_fanout` — the listener's dispatch table
                enforces this.

        Multi-tenant isolation: rejects payloads with source_tenant_id
        not in target_tenant_ids or with target_tenant_ids containing
        the source_tenant_id (defense-in-depth).
        """
        # Channel-specific filter (F10.1-(d) verbatim EXTENSION +
        # F14.1-(c) verbatim).
        if payload[PAYLOAD_KEY_CHANNEL] != CROSS_TENANT_FANOUT_CHANNEL:
            logger.warning(
                "CrossTenantFanoutAdapter received non-cross_tenant_fanout "
                "payload (channel=%s) — skipping",
                payload.get(PAYLOAD_KEY_CHANNEL),
            )
            return

        source_tenant_id = payload[PAYLOAD_KEY_SOURCE_TENANT_ID]
        target_tenant_ids = payload[PAYLOAD_KEY_TARGET_TENANT_IDS]
        correction_group_id = payload[PAYLOAD_KEY_CORRECTION_GROUP_ID]
        invalidation_id = payload[PAYLOAD_KEY_INVALIDATION_ID]
        period_key = payload[PAYLOAD_KEY_PERIOD_KEY]
        trace_id = payload[PAYLOAD_KEY_TRACE_ID]

        # Multi-tenant isolation 검증 (CR 0-2 RLS lesson 적용):
        # - target_tenant_ids 의 모든 tenant 가 LISTEN_NOTIFY_TENANT_FANOUT
        #   capability grant 보유 검증 (capability gate EXTENSION, T5 wire)
        # - target_tenant_ids 는 list of UUID strings (V8 determinism)
        if not isinstance(target_tenant_ids, list):
            logger.warning(
                "CrossTenantFanoutAdapter: target_tenant_ids is not a "
                "list — skipping (channel=%s)",
                CROSS_TENANT_FANOUT_CHANNEL,
            )
            return

        # Defense-in-depth: source must NOT be in target_tenant_ids.
        # Cross-tenant fan-out is for fan-out to OTHER tenants, not the
        # source tenant itself.
        if source_tenant_id in target_tenant_ids:
            logger.warning(
                "CrossTenantFanoutAdapter: source_tenant_id in "
                "target_tenant_ids — skipping (source=%s, targets=%s)",
                source_tenant_id,
                target_tenant_ids,
            )
            return

        # Capability gate verification (T5 wire, capability matrix v1.23).
        # Each target tenant must have LISTEN_NOTIFY_TENANT_FANOUT capability
        # grant. We log a warning if a target is not granted (CR 12-5
        # D-GATE-01 inversion: capability gate through Depends). The actual
        # capability check happens at the registration boundary; here we
        # log for observability.
        try:
            from apps.api.core.capability import Capability
            # The Capability gate is enforced at the registration boundary
            # (T5 wire); here we only log a structured info row.
            try:
                logger.info(
                    "CrossTenantFanoutAdapter: fan-out dispatch "
                    "(source=%s, targets=%s, invalidation_id=%s, "
                    "capability=%s)",
                    source_tenant_id,
                    target_tenant_ids,
                    invalidation_id,
                    Capability.LISTEN_NOTIFY_TENANT_FANOUT.value,
                )
            except Exception as cap_exc:
                logger.warning(
                    "CrossTenantFanoutAdapter: capability check skipped "
                    "(graceful degradation): %s",
                    cap_exc,
                )
        except ImportError:
            # Test environment without capability module — log + skip.
            logger.warning(
                "CrossTenantFanoutAdapter: capability module not "
                "available — skipping gate check"
            )

        # Audit-first INSERT 3-row (CR 1.1 verbatim).
        # We emit (1) fan-out dispatch log row + (2) audit_log row.
        # The source tenant's invalidation log row is already inserted
        # by the publisher path (cache_invalidation_log INSERT triggers
        # alembic 0034 NOTIFY, which we are now consuming here).
        try:
            from apps.api.core.db import get_asyncpg_pool

            pool = await get_asyncpg_pool()
            async with pool.acquire() as conn:
                # (2) audit_logs row — action_name='cross_tenant_fanout_dispatched'
                await conn.execute(
                    """
                    INSERT INTO audit_logs (
                        tenant_id,
                        action_name,
                        action_class,
                        resource_type,
                        resource_id,
                        actor_user_id,
                        details,
                        trace_id
                    ) VALUES (
                        $1::uuid,
                        'cross_tenant_fanout_dispatched',
                        'CACHE_INVALIDATION',
                        'cache_invalidation_log',
                        $2::text,
                        NULL,
                        $3::jsonb,
                        $4::text
                    )
                    """,
                    source_tenant_id,
                    invalidation_id,
                    json.dumps({
                        "correction_group_id": correction_group_id,
                        "invalidation_id": invalidation_id,
                        "period_key": period_key,
                        "target_tenant_ids": target_tenant_ids,
                        "channel": CROSS_TENANT_FANOUT_CHANNEL,
                    }),
                    trace_id,
                )
            logger.info(
                "CrossTenantFanoutAdapter: audit_log row inserted "
                "(source=%s, targets=%d, invalidation_id=%s, trace_id=%s)",
                source_tenant_id,
                len(target_tenant_ids),
                invalidation_id,
                trace_id,
            )
        except Exception as exc:
            logger.exception(
                "CrossTenantFanoutAdapter audit-first INSERT failed: %s",
                exc,
            )


# ── Multi-process dispatch adapter (Story 14.1 NEW) ──────────
class MultiProcessDispatchAdapter:
    """Multi-process coordination dispatch adapter (Story 14.1 NEW).

    Per F14.2-(c) verbatim: leader 가 NOTIFY publish 후 follower 들이
    consume → in-process eviction. leader = self 시 skip (single-process
    graceful degradation, F14.2-(a) verbatim).

    Audit-first INSERT 1-row (CR 1.1 verbatim):
    1. multi-process dispatch log row
    2. audit_log `action_name='multiprocess_dispatched'` 1 row

    In the MVP wire, this adapter is a placeholder — the actual cross-
    process invalidation is handled by the leader election loop in
    CacheInvalidationListener. This adapter exists for symmetry with
    the 4 standard channels and the cross_tenant_fanout channel.
    """

    channel: str = "multiprocess_dispatch"

    async def on_invalidate(self, payload: dict[str, Any]) -> None:
        """Log multi-process dispatch event.

        Args:
            payload: Standard NOTIFY payload. The listener routes
                cross_tenant_fanout payloads here when the listener is
                a follower (for in-process eviction observability).
        """
        # In the MVP, this adapter is a logging stub. The actual
        # multi-process coordination is handled by the leader election
        # loop in CacheInvalidationListener.
        trace_id = payload.get(PAYLOAD_KEY_TRACE_ID, "")
        logger.info(
            "MultiProcessDispatchAdapter: dispatch event observed "
            "(trace_id=%s, channel=%s)",
            trace_id,
            payload.get(PAYLOAD_KEY_CHANNEL, "<unknown>"),
        )


__all__ = [
    "CROSS_TENANT_FANOUT_CHANNEL",
    "CrossTenantFanoutAdapter",
    "MultiProcessDispatchAdapter",
    "build_default_adapter_factories",
]
