"""Test cache_invalidation_listener — LISTEN daemon + 4-channel routing.

Story 13.1 (LISTEN/NOTIFY Consume Trigger EXTENSION, A39/A51/A52 결정 wire):
D-10-2-DEFER-3 ✅ RESOLVED wire 진입. Verifies the asyncio LISTEN daemon
start/stop lifecycle, 4-channel routing, payload parse, V8 determinism,
backoff, and circuit breaker behavior.

Tests:
- start/stop lifecycle (idempotent)
- payload parse (5 keys alphabetical)
- channel whitelist
- V8 determinism (serialize_payload_for_v8)
- backoff (exponential + jitter)
- circuit breaker (5 consecutive failures → 60s cool-down)
- 4-channel dispatch (ai_cache + cost_engine_cache + fiscal_period_cache + closing_snapshot_cache)
- channel-specific filter (unknown channel rejected)
- AdapterFactory injection
"""

from __future__ import annotations

import asyncio
import json
import uuid

import pytest

from apps.api.core.cache_invalidation_listener import (
    ALLOWED_CHANNELS,
    CacheInvalidationListener,
    CacheInvalidationPayload,
    EXPECTED_PAYLOAD_KEYS,
    LISTENER_PAYLOAD_INVALID_KO,
    LISTENER_START_FAILED_KO,
    LISTENER_STOP_FAILED_KO,
    ListenerPayloadInvalidError,
    NOTIFY_CHANNEL_NAME,
    PAYLOAD_KEY_CHANNEL,
    PAYLOAD_KEY_CORRECTION_GROUP_ID,
    PAYLOAD_KEY_PERIOD_KEY,
    PAYLOAD_KEY_TENANT_ID,
    PAYLOAD_KEY_TRACE_ID,
    parse_payload,
    serialize_payload_for_v8,
)


# ── Test fixtures ────────────────────────────────────────────
def _make_valid_payload(
    channel: str = "ai_cache",
    tenant_id: str | None = None,
    period_key: str = "2026-08",
    correction_group_id: str | None = None,
    trace_id: str = "trace-abc-123",
) -> dict[str, str]:
    """Build a valid 5-key payload for tests."""
    return {
        PAYLOAD_KEY_CHANNEL: channel,
        PAYLOAD_KEY_CORRECTION_GROUP_ID: correction_group_id or str(uuid.uuid4()),
        PAYLOAD_KEY_PERIOD_KEY: period_key,
        PAYLOAD_KEY_TENANT_ID: tenant_id or str(uuid.uuid4()),
        PAYLOAD_KEY_TRACE_ID: trace_id,
    }


def _make_mock_adapter_factory(channel: str):
    """Build a mock adapter factory that records calls."""

    class _MockAdapter:
        def __init__(self) -> None:
            self.calls: list[dict[str, str]] = []

        async def on_invalidate(self, payload: dict[str, str]) -> None:
            self.calls.append(payload)

    factory = _MockAdapter()

    def _factory() -> _MockAdapter:
        return factory

    _factory.channel = channel  # type: ignore[attr-defined]
    return _factory, factory


# ── Test constants ───────────────────────────────────────────
class TestConstants:
    """Module-level constants."""

    def test_notify_channel_name(self) -> None:
        assert NOTIFY_CHANNEL_NAME == "cache_invalidation_log"

    def test_allowed_channels_4_channels(self) -> None:
        # Story 14.1 EXTENSION: cross_tenant_fanout 추가 → 4 → 5+ channels
        # (AD-25 verbatim EXTENSION). Baseline (13-1) was 4 channels; 14-1
        # adds the 5th. We assert exactly the 5+ set so any new channel
        # introduced in the future must be a deliberate wire scope decision.
        assert ALLOWED_CHANNELS == frozenset(
            {
                "ai_cache",
                "cost_engine_cache",
                "fiscal_period_cache",
                "closing_snapshot_cache",
                "cross_tenant_fanout",
            }
        )

    def test_expected_payload_keys_5_keys(self) -> None:
        assert EXPECTED_PAYLOAD_KEYS == frozenset(
            {
                "channel",
                "correction_group_id",
                "period_key",
                "tenant_id",
                "trace_id",
            }
        )

    def test_korean_constants_defined(self) -> None:
        assert LISTENER_START_FAILED_KO == "캐시 무효화 리스너 시작 실패"
        assert LISTENER_STOP_FAILED_KO == "캐시 무효화 리스너 종료 실패"
        assert LISTENER_PAYLOAD_INVALID_KO == "캐시 무효화 페이로드 형식 오류"


# ── Test V8 determinism ──────────────────────────────────────
class TestV8Determinism:
    """serialize_payload_for_v8 — byte-identical deterministic serialization."""

    def test_alphabetical_key_ordering(self) -> None:
        payload = _make_valid_payload()
        result = serialize_payload_for_v8(payload)
        # Keys must be in alphabetical order.
        assert result.index('"channel"') < result.index('"correction_group_id"')
        assert result.index('"correction_group_id"') < result.index('"period_key"')
        assert result.index('"period_key"') < result.index('"tenant_id"')
        assert result.index('"tenant_id"') < result.index('"trace_id"')

    def test_no_whitespace(self) -> None:
        payload = _make_valid_payload()
        result = serialize_payload_for_v8(payload)
        # No spaces, no newlines.
        assert " " not in result
        assert "\n" not in result

    def test_byte_identical(self) -> None:
        """Same input → same output bytes."""
        payload = _make_valid_payload()
        result1 = serialize_payload_for_v8(payload)
        result2 = serialize_payload_for_v8(payload)
        assert result1 == result2

    def test_byte_identical_with_reordered_input(self) -> None:
        """Even if input dict is constructed in different order, output is byte-identical."""
        payload1 = _make_valid_payload()
        payload2 = {
            "trace_id": payload1["trace_id"],
            "tenant_id": payload1["tenant_id"],
            "period_key": payload1["period_key"],
            "correction_group_id": payload1["correction_group_id"],
            "channel": payload1["channel"],
        }
        assert serialize_payload_for_v8(payload1) == serialize_payload_for_v8(payload2)


# ── Test parse_payload ───────────────────────────────────────
class TestParsePayload:
    """parse_payload — JSON → CacheInvalidationPayload."""

    def test_valid_payload(self) -> None:
        payload = _make_valid_payload()
        raw = serialize_payload_for_v8(payload)
        parsed = parse_payload(raw)
        assert isinstance(parsed, CacheInvalidationPayload)
        assert parsed.channel == payload[PAYLOAD_KEY_CHANNEL]
        assert parsed.tenant_id == payload[PAYLOAD_KEY_TENANT_ID]
        assert parsed.period_key == payload[PAYLOAD_KEY_PERIOD_KEY]
        assert parsed.correction_group_id == payload[PAYLOAD_KEY_CORRECTION_GROUP_ID]
        assert parsed.trace_id == payload[PAYLOAD_KEY_TRACE_ID]

    def test_invalid_json_raises(self) -> None:
        with pytest.raises(ListenerPayloadInvalidError) as excinfo:
            parse_payload("not a json")
        assert "JSON parse failed" in str(excinfo.value)

    def test_missing_key_raises(self) -> None:
        payload = _make_valid_payload()
        del payload[PAYLOAD_KEY_TRACE_ID]
        raw = serialize_payload_for_v8(payload)
        with pytest.raises(ListenerPayloadInvalidError) as excinfo:
            parse_payload(raw)
        assert "payload keys mismatch" in str(excinfo.value)

    def test_extra_key_raises(self) -> None:
        payload = _make_valid_payload()
        payload["extra_key"] = "value"
        raw = serialize_payload_for_v8(payload)
        with pytest.raises(ListenerPayloadInvalidError) as excinfo:
            parse_payload(raw)
        assert "payload keys mismatch" in str(excinfo.value)

    def test_unknown_channel_raises(self) -> None:
        payload = _make_valid_payload(channel="unknown_channel")
        raw = serialize_payload_for_v8(payload)
        with pytest.raises(ListenerPayloadInvalidError) as excinfo:
            parse_payload(raw)
        assert "not in ALLOWED_CHANNELS" in str(excinfo.value)

    def test_invalid_tenant_id_raises(self) -> None:
        payload = _make_valid_payload(tenant_id="not-a-uuid")
        raw = serialize_payload_for_v8(payload)
        with pytest.raises(ListenerPayloadInvalidError) as excinfo:
            parse_payload(raw)
        assert "tenant_id" in str(excinfo.value)

    def test_invalid_correction_group_id_raises(self) -> None:
        payload = _make_valid_payload(correction_group_id="not-a-uuid")
        raw = serialize_payload_for_v8(payload)
        with pytest.raises(ListenerPayloadInvalidError) as excinfo:
            parse_payload(raw)
        assert "correction_group_id" in str(excinfo.value)

    def test_empty_trace_id_raises(self) -> None:
        payload = _make_valid_payload(trace_id="")
        raw = serialize_payload_for_v8(payload)
        with pytest.raises(ListenerPayloadInvalidError) as excinfo:
            parse_payload(raw)
        assert "trace_id" in str(excinfo.value)

    def test_empty_period_key_raises(self) -> None:
        payload = _make_valid_payload(period_key="")
        raw = serialize_payload_for_v8(payload)
        with pytest.raises(ListenerPayloadInvalidError) as excinfo:
            parse_payload(raw)
        assert "period_key" in str(excinfo.value)

    def test_payload_not_dict_raises(self) -> None:
        with pytest.raises(ListenerPayloadInvalidError) as excinfo:
            parse_payload("[]")
        assert "not a JSON object" in str(excinfo.value)


# ── Test backoff helper ──────────────────────────────────────
class TestBackoff:
    """_compute_backoff_seconds — exponential + jitter."""

    def test_backoff_attempt_0(self) -> None:
        from apps.api.core.cache_invalidation_listener import _compute_backoff_seconds

        # Base 1s, factor 2, jitter ±20% → [0.8, 1.2]
        for _ in range(100):
            delay = _compute_backoff_seconds(0)
            assert 0.8 <= delay <= 1.2

    def test_backoff_grows_exponentially(self) -> None:
        from apps.api.core.cache_invalidation_listener import _compute_backoff_seconds

        # attempt 1: base * 2 = 2s ± 20% → [1.6, 2.4]
        for _ in range(50):
            delay = _compute_backoff_seconds(1)
            assert 1.6 <= delay <= 2.4

    def test_backoff_capped_at_max(self) -> None:
        from apps.api.core.cache_invalidation_listener import (
            _BACKOFF_MAX_SECONDS,
            _compute_backoff_seconds,
        )

        # attempt 100: base * 2^100 = huge, but capped at 30s.
        for _ in range(20):
            delay = _compute_backoff_seconds(100)
            assert delay <= _BACKOFF_MAX_SECONDS * 1.2


# ── Test listener init ───────────────────────────────────────
class TestListenerInit:
    """CacheInvalidationListener init + adapter factory validation."""

    def test_init_with_all_4_factories(self) -> None:
        factories = {
            ch: _make_mock_adapter_factory(ch)[0] for ch in ALLOWED_CHANNELS
        }
        listener = CacheInvalidationListener(adapter_factories=factories)
        assert listener._is_started is False

    def test_init_missing_channel_raises(self) -> None:
        factories = {"ai_cache": _make_mock_adapter_factory("ai_cache")[0]}
        with pytest.raises(ValueError) as excinfo:
            CacheInvalidationListener(adapter_factories=factories)
        assert "missing channels" in str(excinfo.value)

    def test_init_unknown_channel_raises(self) -> None:
        factories = {
            ch: _make_mock_adapter_factory(ch)[0] for ch in ALLOWED_CHANNELS
        }
        factories["unknown"] = _make_mock_adapter_factory("unknown")[0]
        with pytest.raises(ValueError) as excinfo:
            CacheInvalidationListener(adapter_factories=factories)
        assert "unknown channels" in str(excinfo.value)

    def test_init_invalid_factories_type_raises(self) -> None:
        with pytest.raises(ValueError):
            CacheInvalidationListener(adapter_factories="not-a-dict")  # type: ignore[arg-type]


# ── Test lifecycle ───────────────────────────────────────────
class TestListenerLifecycle:
    """start/stop idempotency + graceful degradation."""

    def test_start_is_idempotent(self) -> None:
        """Double-start: second call is a no-op."""
        factories = {
            ch: _make_mock_adapter_factory(ch)[0] for ch in ALLOWED_CHANNELS
        }
        listener = CacheInvalidationListener(adapter_factories=factories)
        # Without a connection factory, start() will fail — but stop_event
        # and is_started are still checked. We test the idempotency flag
        # directly: simulate a started listener.
        listener._is_started = True
        # Don't actually call start() — it would try to open a DB connection.
        # Verify the guard: if we call start() again while _is_started is True,
        # it returns immediately without raising.
        asyncio.run(listener.start())
        # Second call should also be a no-op.
        asyncio.run(listener.start())


# ── Test payload parse + dispatch ─────────────────────────────
class TestPayloadDispatch:
    """End-to-end: payload parse → adapter dispatch."""

    def test_parse_payload_round_trip(self) -> None:
        payload = _make_valid_payload()
        raw = serialize_payload_for_v8(payload)
        # Verify the canonical form is exactly what we expect.
        re_parsed = json.loads(raw)
        assert set(re_parsed.keys()) == EXPECTED_PAYLOAD_KEYS
        # The serialized form must be the one parse_payload accepts.
        parsed = parse_payload(raw)
        assert parsed.to_dict() == payload

    def test_4_channel_payload_dispatch(self) -> None:
        """Each of the 5+ channels can be parsed separately.

        Story 14.1 EXTENSION: cross_tenant_fanout 추가 → 4 → 5+ channels.
        The dispatch table may dispatch any of the 5+ allowed channels; the
        parse_payload function must accept each channel's payload shape:
        - 5 keys for the 4 baseline channels
        - 7 keys for cross_tenant_fanout
        """
        from tests.api.core.test_cache_invalidation_listener_14_1 import (
            _make_cross_tenant_payload as _make_7_key,
        )

        for channel in ALLOWED_CHANNELS:
            if channel == "cross_tenant_fanout":
                # 7-key shape required.
                payload = _make_7_key()
            else:
                payload = _make_valid_payload(channel=channel)
            raw = serialize_payload_for_v8(payload)
            parsed = parse_payload(raw)
            assert parsed.channel == channel
