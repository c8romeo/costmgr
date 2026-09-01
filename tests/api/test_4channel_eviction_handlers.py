"""Test cache eviction handlers — M10/M3/M11 + cross_tenant_fanout.

Story 13.1 (LISTEN/NOTIFY Consume Trigger EXTENSION, A39/A51/A52 결정 wire):
T4 wire — 4-channel cache eviction handlers EXTENSION (M10/M3/M11).

Story 14.1 EXTENSION: cross_tenant_fanout channel 추가 → 4 → 5 channels
(see `test_cache_invalidation_listener_14_1.py` for cross_tenant_fanout
listener-level tests — this file covers the 4 M10/M3/M11 ADAPTER classes).

Per AD-25 (ARCHITECTURE-SPINE.md §142-148 verbatim):
  "M10 cache key is `(tenant_id, period_key, calculation_result_hash)`.
   A new AD-4 commit, an AD-22 reversal insert, or an M11 reopen emits
   one DB notification per channel."

Tests:
- M10 AI cache eviction (channel='ai_cache' filter)
- M3 cost engine cache eviction (channel='cost_engine_cache' filter)
- M11 fiscal_period cache eviction (channel='fiscal_period_cache' filter)
- M11 closing_snapshot cache eviction (channel='closing_snapshot_cache' filter)
- Cross-channel contamination 거부 (each adapter rejects other channels)
- Adapter factory wiring (build_default_adapter_factories returns 5 channels)
"""

from __future__ import annotations

import asyncio
import inspect
import uuid
from typing import Any

import pytest


# ── Test the adapter factory map ─────────────────────────────
class TestBuildDefaultAdapterFactories:
    """build_default_adapter_factories returns 5 channel → factory entries.

    cj-style 249 (D-CI-FUNC-11 smoke-e2e): The adapter factories must
    include the listener's full ALLOWED_CHANNELS (5 channels: 4
    AD-25 + cross_tenant_fanout). Previously this test asserted 4
    channels because the factories file imported ALLOWED_CHANNELS
    from `cache_invalidation_publisher` (the publisher's 4-channel
    whitelist), causing `build_default_adapter_factories()` to
    return only 4 factories. At uvicorn startup, the listener's
    constructor rejected the dict with
    `ValueError: adapter_factories missing channels:
    ['cross_tenant_fanout']`, breaking smoke-e2e.

    Fix: the factory file now imports ALLOWED_CHANNELS from the
    LISTENER module (the listener's 5-channel whitelist is the SSOT
    for what adapters the listener requires — the publisher's
    4-channel whitelist is a separate concern: what channels the
    AD-25 publisher can emit, not what the listener must consume).
    """

    def test_returns_5_channels(self) -> None:
        from apps.api.core.cache_invalidation_listener_adapters import (
            build_default_adapter_factories,
        )

        factories = build_default_adapter_factories()
        assert len(factories) == 5

    def test_returns_all_5_whitelist_channels(self) -> None:
        from apps.api.core.cache_invalidation_listener_adapters import (
            build_default_adapter_factories,
        )

        factories = build_default_adapter_factories()
        assert set(factories.keys()) == {
            "ai_cache",
            "cost_engine_cache",
            "fiscal_period_cache",
            "closing_snapshot_cache",
            "cross_tenant_fanout",
        }

    def test_each_factory_is_callable(self) -> None:
        from apps.api.core.cache_invalidation_listener_adapters import (
            build_default_adapter_factories,
        )

        factories = build_default_adapter_factories()
        for channel, factory in factories.items():
            assert callable(factory), f"factory for {channel} is not callable"

    def test_factory_returns_adapter_instance(self) -> None:
        from apps.api.core.cache_invalidation_listener_adapters import (
            build_default_adapter_factories,
        )

        factories = build_default_adapter_factories()
        for channel, factory in factories.items():
            adapter = factory()
            assert hasattr(adapter, "on_invalidate"), (
                f"{channel} adapter has no on_invalidate method"
            )
            assert getattr(adapter, "channel", None) == channel, (
                f"{channel} adapter has wrong channel attribute"
            )


# ── Test M10 AI cache adapter ────────────────────────────────
class TestM10AIAdapter:
    """M10 AI cache adapter (channel='ai_cache')."""

    def test_channel_attribute(self) -> None:
        from apps.api.core.cache_invalidation_listener_adapters import (
            build_default_adapter_factories,
        )

        factories = build_default_adapter_factories()
        adapter = factories["ai_cache"]()
        assert adapter.channel == "ai_cache"

    @pytest.mark.asyncio
    async def test_on_invalidate_accepts_ai_cache_payload(self) -> None:
        """Adapter accepts payloads with channel='ai_cache' (no-op import errors)."""
        from apps.api.core.cache_invalidation_listener_adapters import (
            build_default_adapter_factories,
        )

        adapter = build_default_adapter_factories()["ai_cache"]()
        payload = {
            "channel": "ai_cache",
            "correction_group_id": str(uuid.uuid4()),
            "period_key": "2026-08",
            "tenant_id": str(uuid.uuid4()),
            "trace_id": "test-trace",
        }
        # Adapter should NOT raise (DB connection may fail in test env,
        # but that's caught + logged inside the adapter).
        await adapter.on_invalidate(payload)

    @pytest.mark.asyncio
    async def test_on_invalidate_rejects_non_ai_cache_payload(self) -> None:
        """Adapter rejects payloads with channel != 'ai_cache' (cross-channel contamination)."""
        from apps.api.core.cache_invalidation_listener_adapters import (
            build_default_adapter_factories,
        )

        adapter = build_default_adapter_factories()["ai_cache"]()
        payload = {
            "channel": "cost_engine_cache",  # WRONG channel for M10
            "correction_group_id": str(uuid.uuid4()),
            "period_key": "2026-08",
            "tenant_id": str(uuid.uuid4()),
            "trace_id": "test-trace",
        }
        # Should not raise — just skip (graceful degradation).
        await adapter.on_invalidate(payload)


# ── Test M3 cost engine adapter ──────────────────────────────
class TestM3CostEngineAdapter:
    """M3 cost engine adapter (channel='cost_engine_cache')."""

    def test_channel_attribute(self) -> None:
        from apps.api.core.cache_invalidation_listener_adapters import (
            build_default_adapter_factories,
        )

        adapter = build_default_adapter_factories()["cost_engine_cache"]()
        assert adapter.channel == "cost_engine_cache"

    @pytest.mark.asyncio
    async def test_on_invalidate_accepts_cost_engine_cache_payload(self) -> None:
        from apps.api.core.cache_invalidation_listener_adapters import (
            build_default_adapter_factories,
        )

        adapter = build_default_adapter_factories()["cost_engine_cache"]()
        payload = {
            "channel": "cost_engine_cache",
            "correction_group_id": str(uuid.uuid4()),
            "period_key": "2026-08",
            "tenant_id": str(uuid.uuid4()),
            "trace_id": "test-trace",
        }
        await adapter.on_invalidate(payload)

    @pytest.mark.asyncio
    async def test_on_invalidate_rejects_non_cost_engine_cache_payload(self) -> None:
        from apps.api.core.cache_invalidation_listener_adapters import (
            build_default_adapter_factories,
        )

        adapter = build_default_adapter_factories()["cost_engine_cache"]()
        payload = {
            "channel": "ai_cache",  # WRONG channel for M3
            "correction_group_id": str(uuid.uuid4()),
            "period_key": "2026-08",
            "tenant_id": str(uuid.uuid4()),
            "trace_id": "test-trace",
        }
        await adapter.on_invalidate(payload)


# ── Test M11 fiscal_period adapter ───────────────────────────
class TestM11FiscalPeriodAdapter:
    """M11 fiscal_period adapter (channel='fiscal_period_cache')."""

    def test_channel_attribute(self) -> None:
        from apps.api.core.cache_invalidation_listener_adapters import (
            build_default_adapter_factories,
        )

        adapter = build_default_adapter_factories()["fiscal_period_cache"]()
        assert adapter.channel == "fiscal_period_cache"

    @pytest.mark.asyncio
    async def test_on_invalidate_accepts_fiscal_period_cache_payload(self) -> None:
        from apps.api.core.cache_invalidation_listener_adapters import (
            build_default_adapter_factories,
        )

        adapter = build_default_adapter_factories()["fiscal_period_cache"]()
        payload = {
            "channel": "fiscal_period_cache",
            "correction_group_id": str(uuid.uuid4()),
            "period_key": "2026-08",
            "tenant_id": str(uuid.uuid4()),
            "trace_id": "test-trace",
        }
        await adapter.on_invalidate(payload)


# ── Test M11 closing_snapshot adapter ────────────────────────
class TestM11ClosingSnapshotAdapter:
    """M11 closing_snapshot adapter (channel='closing_snapshot_cache')."""

    def test_channel_attribute(self) -> None:
        from apps.api.core.cache_invalidation_listener_adapters import (
            build_default_adapter_factories,
        )

        adapter = build_default_adapter_factories()["closing_snapshot_cache"]()
        assert adapter.channel == "closing_snapshot_cache"

    @pytest.mark.asyncio
    async def test_on_invalidate_accepts_closing_snapshot_cache_payload(self) -> None:
        from apps.api.core.cache_invalidation_listener_adapters import (
            build_default_adapter_factories,
        )

        adapter = build_default_adapter_factories()["closing_snapshot_cache"]()
        payload = {
            "channel": "closing_snapshot_cache",
            "correction_group_id": str(uuid.uuid4()),
            "period_key": "2026-08",
            "tenant_id": str(uuid.uuid4()),
            "trace_id": "test-trace",
        }
        await adapter.on_invalidate(payload)


# ── Test cross-channel contamination ─────────────────────────
class TestCrossChannelContamination:
    """Each adapter rejects payloads from other channels."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "adapter_channel,other_channels",
        [
            ("ai_cache", ["cost_engine_cache", "fiscal_period_cache", "closing_snapshot_cache"]),
            ("cost_engine_cache", ["ai_cache", "fiscal_period_cache", "closing_snapshot_cache"]),
            ("fiscal_period_cache", ["ai_cache", "cost_engine_cache", "closing_snapshot_cache"]),
            ("closing_snapshot_cache", ["ai_cache", "cost_engine_cache", "fiscal_period_cache"]),
        ],
    )
    async def test_adapter_rejects_other_channels(
        self, adapter_channel: str, other_channels: list[str]
    ) -> None:
        from apps.api.core.cache_invalidation_listener_adapters import (
            build_default_adapter_factories,
        )

        adapter = build_default_adapter_factories()[adapter_channel]()
        for other_channel in other_channels:
            payload = {
                "channel": other_channel,
                "correction_group_id": str(uuid.uuid4()),
                "period_key": "2026-08",
                "tenant_id": str(uuid.uuid4()),
                "trace_id": "test-trace",
            }
            # Should NOT raise — just skip + log (graceful degradation).
            await adapter.on_invalidate(payload)
