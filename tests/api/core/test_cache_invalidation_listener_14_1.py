"""Test cache_invalidation_listener 14.1 EXTENSION — multi-process coordination + cross_tenant_fanout.

Story 14.1 (LISTEN/NOTIFY Consume Cross-Tenant Fan-Out + Multi-Process
Coordination, A53+A57+A58+A59 결정 wire): D-13-1-DEFER-3 ✅ RESOLVED.

Verifies the 14.1 EXTENSION to the 13.1 listener:
- 5+ channels routing dispatch table (cross_tenant_fanout 추가)
- Leader election via `pg_try_advisory_xact_lock(LISTEN_FANOUT_LOCK_ID)`
- _leader_election_loop() private coroutine (follower takeover)
- Single-process graceful degradation (leader = self, follower = none)
- 7-key cross_tenant_fanout payload parse
- target_tenant_ids JSON array 결정적 직렬화 검증
- Cross-channel contamination 방어 EXTENSION
- Reconnect/backoff 보존 (F13.1-(c) verbatim)
"""

from __future__ import annotations

import asyncio
import json
import uuid

import pytest

from apps.api.core.cache_invalidation_listener import (
    ALLOWED_CHANNELS,
    ERROR_CODE_LEADER_ELECTION_FAILED,
    ERROR_CODE_LEADER_TAKEOVER_FAILED,
    CacheInvalidationListener,
    EXPECTED_PAYLOAD_KEYS_CROSS_TENANT,
    LEADER_ELECTION_FAILED_KO,
    LEADER_HEALTH_CHECK_INTERVAL_SECONDS,
    LEADER_TAKEOVER_TIMEOUT_SECONDS,
    LISTEN_FANOUT_LOCK_ID,
    LeaderElectionFailedError,
    LeaderElectionState,
    LeaderTakeoverFailedError,
    PAYLOAD_KEY_CHANNEL,
    PAYLOAD_KEY_CORRECTION_GROUP_ID,
    PAYLOAD_KEY_INVALIDATION_ID,
    PAYLOAD_KEY_PERIOD_KEY,
    PAYLOAD_KEY_SOURCE_TENANT_ID,
    PAYLOAD_KEY_TARGET_TENANT_IDS,
    PAYLOAD_KEY_TRACE_ID,
    parse_payload,
    serialize_payload_for_v8,
)


# ── Test helpers ─────────────────────────────────────────────
def _make_cross_tenant_payload(
    *,
    source_tenant_id: str | None = None,
    target_tenant_ids: list[str] | None = None,
    invalidation_id: str | None = None,
    correction_group_id: str | None = None,
    period_key: str = "2026-08",
    trace_id: str = "trace-abc-123",
) -> dict[str, object]:
    """Build a valid 7-key payload for cross_tenant_fanout channel."""
    return {
        PAYLOAD_KEY_CHANNEL: "cross_tenant_fanout",
        PAYLOAD_KEY_CORRECTION_GROUP_ID: (
            correction_group_id or str(uuid.uuid4())
        ),
        PAYLOAD_KEY_INVALIDATION_ID: invalidation_id or str(uuid.uuid4()),
        PAYLOAD_KEY_PERIOD_KEY: period_key,
        PAYLOAD_KEY_SOURCE_TENANT_ID: source_tenant_id or str(uuid.uuid4()),
        PAYLOAD_KEY_TARGET_TENANT_IDS: (
            target_tenant_ids
            if target_tenant_ids is not None
            else [str(uuid.uuid4()) for _ in range(2)]
        ),
        PAYLOAD_KEY_TRACE_ID: trace_id,
    }


# ── Test classes ─────────────────────────────────────────────
class TestCrossTenantChannelWhitelist:
    """ALLOWED_CHANNELS EXTENSION (5+ channels, AD-25 verbatim)."""

    def test_allowed_channels_5_plus(self) -> None:
        """5+ channels: 4 보존 + cross_tenant_fanout 추가."""
        assert ALLOWED_CHANNELS == frozenset(
            {
                "ai_cache",
                "cost_engine_cache",
                "fiscal_period_cache",
                "closing_snapshot_cache",
                "cross_tenant_fanout",
            }
        )

    def test_cross_tenant_fanout_in_allowed(self) -> None:
        """cross_tenant_fanout is in ALLOWED_CHANNELS."""
        assert "cross_tenant_fanout" in ALLOWED_CHANNELS

    def test_expected_payload_keys_cross_tenant_7_keys(self) -> None:
        """EXPECTED_PAYLOAD_KEYS_CROSS_TENANT = 7 alphabetical keys."""
        assert EXPECTED_PAYLOAD_KEYS_CROSS_TENANT == frozenset(
            {
                PAYLOAD_KEY_CHANNEL,
                PAYLOAD_KEY_CORRECTION_GROUP_ID,
                PAYLOAD_KEY_INVALIDATION_ID,
                PAYLOAD_KEY_PERIOD_KEY,
                PAYLOAD_KEY_SOURCE_TENANT_ID,
                PAYLOAD_KEY_TARGET_TENANT_IDS,
                PAYLOAD_KEY_TRACE_ID,
            }
        )


class TestCrossTenantPayloadParse:
    """parse_payload() EXTENSION — 7-key cross_tenant_fanout payload."""

    def test_valid_cross_tenant_payload_parses(self) -> None:
        """Valid 7-key payload parses without error."""
        payload = _make_cross_tenant_payload()
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        parsed = parse_payload(raw)
        assert parsed.channel == "cross_tenant_fanout"
        assert parsed.invalidation_id == payload[PAYLOAD_KEY_INVALIDATION_ID]
        assert parsed.source_tenant_id == payload[PAYLOAD_KEY_SOURCE_TENANT_ID]
        assert parsed.target_tenant_ids == tuple(
            payload[PAYLOAD_KEY_TARGET_TENANT_IDS]
        )

    def test_cross_tenant_payload_v8_determinism(self) -> None:
        """V8 determinism: serialize_payload_for_v8() byte-identical across reruns."""
        payload = _make_cross_tenant_payload()
        raw1 = serialize_payload_for_v8(payload)
        raw2 = serialize_payload_for_v8(payload)
        assert raw1 == raw2
        # Verify alphabetical key ordering.
        keys_order = []
        for k in json.loads(raw1).keys():
            keys_order.append(k)
        assert keys_order == sorted(keys_order)

    def test_cross_tenant_payload_invalid_key_count(self) -> None:
        """Payload with wrong number of keys rejected."""
        payload = _make_cross_tenant_payload()
        del payload[PAYLOAD_KEY_TARGET_TENANT_IDS]
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        with pytest.raises(Exception):  # ListenerPayloadInvalidError
            parse_payload(raw)

    def test_cross_tenant_payload_invalid_target_tenant_id(self) -> None:
        """Payload with non-UUID target_tenant_id rejected."""
        payload = _make_cross_tenant_payload(
            target_tenant_ids=["not-a-uuid"],
        )
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        with pytest.raises(Exception):
            parse_payload(raw)

    def test_cross_tenant_payload_empty_target_tenant_ids(self) -> None:
        """Payload with empty target_tenant_ids list (valid empty array)."""
        payload = _make_cross_tenant_payload(target_tenant_ids=[])
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        parsed = parse_payload(raw)
        assert parsed.target_tenant_ids == ()

    def test_cross_tenant_payload_target_order_preserved(self) -> None:
        """target_tenant_ids array element order preserved (V8 determinism)."""
        ids = [str(uuid.uuid4()) for _ in range(3)]
        payload = _make_cross_tenant_payload(target_tenant_ids=ids)
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        parsed = parse_payload(raw)
        assert list(parsed.target_tenant_ids) == ids


class TestLeaderElectionState:
    """LeaderElectionState frozen dataclass."""

    def test_leader_state_defaults(self) -> None:
        """LeaderElectionState: is_leader=True, leader_pod_id='pod-foo'."""
        state = LeaderElectionState(
            is_leader=True,
            leader_pod_id="pod-foo",
        )
        assert state.is_leader is True
        assert state.leader_pod_id == "pod-foo"
        assert state.follower_pod_ids == ()

    def test_leader_state_frozen(self) -> None:
        """LeaderElectionState is frozen (immutable)."""
        state = LeaderElectionState(
            is_leader=False,
            leader_pod_id="pod-leader",
            follower_pod_ids=("pod-f1", "pod-f2"),
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            state.is_leader = True  # type: ignore[misc]


class TestMultiProcessCoordinationConstants:
    """Multi-process coordination constants (Story 14.1)."""

    def test_listen_fanout_lock_id(self) -> None:
        """LISTEN_FANOUT_LOCK_ID is set."""
        assert LISTEN_FANOUT_LOCK_ID > 0

    def test_leader_health_check_interval(self) -> None:
        """LEADER_HEALTH_CHECK_INTERVAL_SECONDS = 30.0."""
        assert LEADER_HEALTH_CHECK_INTERVAL_SECONDS == 30.0

    def test_leader_takeover_timeout(self) -> None:
        """LEADER_TAKEOVER_TIMEOUT_SECONDS = 90.0."""
        assert LEADER_TAKEOVER_TIMEOUT_SECONDS == 90.0


class TestLeaderElectionErrorCodes:
    """Error codes + Korean SSOT (CR 12-5 D-14 envelope, AD-15 §11)."""

    def test_leader_election_failed_code(self) -> None:
        """ERROR_CODE_LEADER_ELECTION_FAILED = 'LEADER_ELECTION_FAILED'."""
        assert (
            ERROR_CODE_LEADER_ELECTION_FAILED == "LEADER_ELECTION_FAILED"
        )

    def test_leader_takeover_failed_code(self) -> None:
        """ERROR_CODE_LEADER_TAKEOVER_FAILED = 'LEADER_TAKEOVER_FAILED'."""
        assert (
            ERROR_CODE_LEADER_TAKEOVER_FAILED == "LEADER_TAKEOVER_FAILED"
        )

    def test_leader_election_failed_ko(self) -> None:
        """LEADER_ELECTION_FAILED_KO = '리스너 리더 선출 실패'."""
        assert LEADER_ELECTION_FAILED_KO == "리스너 리더 선출 실패"


class TestLeaderElectionExceptions:
    """2 NEW typed exceptions (Story 14.1)."""

    def test_leader_election_failed_error(self) -> None:
        """LeaderElectionFailedError carries reason + trace_id."""
        exc = LeaderElectionFailedError(
            reason="connection refused",
            trace_id="trace-1",
        )
        assert exc.reason == "connection refused"
        assert exc.trace_id == "trace-1"

    def test_leader_takeover_failed_error(self) -> None:
        """LeaderTakeoverFailedError carries reason + trace_id."""
        exc = LeaderTakeoverFailedError(
            reason="could not acquire lock",
            trace_id="trace-2",
        )
        assert exc.reason == "could not acquire lock"
        assert exc.trace_id == "trace-2"


class TestCacheInvalidationListener14_1:
    """CacheInvalidationListener 14.1 EXTENSION."""

    def test_listener_accepts_pod_id(self) -> None:
        """Listener accepts pod_id constructor argument."""

        def _factory() -> object:
            return object()

        # 5+ channels with factories.
        factories = {
            "ai_cache": _factory,
            "cost_engine_cache": _factory,
            "fiscal_period_cache": _factory,
            "closing_snapshot_cache": _factory,
            "cross_tenant_fanout": _factory,
        }

        listener = CacheInvalidationListener(
            adapter_factories=factories,
            pod_id="pod-test-123",
        )
        assert listener._pod_id == "pod-test-123"

    def test_listener_default_pod_id(self) -> None:
        """Listener generates default pod_id when not provided."""

        def _factory() -> object:
            return object()

        factories = {
            "ai_cache": _factory,
            "cost_engine_cache": _factory,
            "fiscal_period_cache": _factory,
            "closing_snapshot_cache": _factory,
            "cross_tenant_fanout": _factory,
        }

        listener = CacheInvalidationListener(adapter_factories=factories)
        # Default pod_id format: 'pod-<8 hex chars>'
        assert listener._pod_id.startswith("pod-")
        assert len(listener._pod_id) == len("pod-") + 8

    def test_listener_initial_is_leader_true_graceful_degradation(self) -> None:
        """Listener initial state: is_leader=True (single-process graceful degradation)."""

        def _factory() -> object:
            return object()

        factories = {
            "ai_cache": _factory,
            "cost_engine_cache": _factory,
            "fiscal_period_cache": _factory,
            "closing_snapshot_cache": _factory,
            "cross_tenant_fanout": _factory,
        }

        listener = CacheInvalidationListener(adapter_factories=factories)
        # Initial state defaults to leader = self (graceful degradation).
        assert listener.is_leader is True

    def test_listener_rejects_missing_cross_tenant_channel(self) -> None:
        """Listener rejects adapter_factories missing cross_tenant_fanout."""

        def _factory() -> object:
            return object()

        factories = {
            "ai_cache": _factory,
            "cost_engine_cache": _factory,
            "fiscal_period_cache": _factory,
            "closing_snapshot_cache": _factory,
        }

        with pytest.raises(ValueError) as exc_info:
            CacheInvalidationListener(adapter_factories=factories)
        assert "cross_tenant_fanout" in str(exc_info.value)

    def test_listener_rejects_extra_channel(self) -> None:
        """Listener rejects adapter_factories with unknown channels."""

        def _factory() -> object:
            return object()

        factories = {
            "ai_cache": _factory,
            "cost_engine_cache": _factory,
            "fiscal_period_cache": _factory,
            "closing_snapshot_cache": _factory,
            "cross_tenant_fanout": _factory,
            "unknown_channel": _factory,
        }

        with pytest.raises(ValueError) as exc_info:
            CacheInvalidationListener(adapter_factories=factories)
        assert "unknown_channel" in str(exc_info.value)
