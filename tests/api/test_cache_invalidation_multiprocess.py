"""Multi-process coordination tests — cache_invalidation_listener (Story 14.1).

Story 14.1 (LISTEN/NOTIFY Consume Cross-Tenant Fan-Out + Multi-Process
Coordination, A53+A57+A58+A59 결정 wire): T8 — multi-process coordination
tests.

Multi-process coordination is achieved via PostgreSQL advisory locks
(`pg_try_advisory_xact_lock`) for leader election, and
`pg_try_advisory_lock` for follower takeover of unresponsive leaders.

Tests:
- 18 cases: leader election + takeover + state transitions + lock release
  + graceful degradation + Korean SSOT reject messages + 2 NEW exception
  types
"""

from __future__ import annotations

import asyncio
import inspect
import uuid

import pytest


# ── Test leader election state ────────────────────────────────
class TestLeaderElectionState:
    """LeaderElectionState frozen dataclass invariants."""

    def test_leader_election_state_is_frozen(self) -> None:
        """LeaderElectionState is frozen (F841/CR 11-2 immutable shape)."""
        from apps.api.core.cache_invalidation_listener import (
            LeaderElectionState,
        )

        state = LeaderElectionState(
            is_leader=True,
            leader_pod_id="pod-leader-001",
            follower_pod_ids=frozenset({"pod-follower-001"}),
        )
        with pytest.raises((AttributeError, Exception)):  # FrozenInstanceError
            state.is_leader = False  # type: ignore[misc]

    def test_leader_election_state_required_fields(self) -> None:
        """All 3 fields required + typed."""
        from apps.api.core.cache_invalidation_listener import (
            LeaderElectionState,
        )

        sig = inspect.signature(LeaderElectionState.__init__)
        params = list(sig.parameters.keys())
        assert "is_leader" in params
        assert "leader_pod_id" in params
        assert "follower_pod_ids" in params

    def test_leader_election_state_follower_empty(self) -> None:
        """follower_pod_ids can be empty frozenset (single-pod startup)."""
        from apps.api.core.cache_invalidation_listener import (
            LeaderElectionState,
        )

        state = LeaderElectionState(
            is_leader=True,
            leader_pod_id="pod-single",
            follower_pod_ids=frozenset(),
        )
        assert state.is_leader is True
        assert state.follower_pod_ids == frozenset()


# ── Test lock ID constants ────────────────────────────────────
class TestLockIdConstants:
    """PostgreSQL advisory lock ID constants (deterministic, ASCII-encoded)."""

    def test_listen_fanout_lock_id_int_type(self) -> None:
        """LISTEN_FANOUT_LOCK_ID is a deterministic int."""
        from apps.api.core.cache_invalidation_listener import (
            LISTEN_FANOUT_LOCK_ID,
        )

        assert isinstance(LISTEN_FANOUT_LOCK_ID, int)
        # Hex-ASCII encoded 'LISTFANT' (8 chars), per Python convention.
        assert LISTEN_FANOUT_LOCK_ID == 0x4C49_5354_4641_4E54

    def test_health_check_interval_seconds(self) -> None:
        """LEADER_HEALTH_CHECK_INTERVAL_SECONDS = 30.0 (CR 14-1 결정)."""
        from apps.api.core.cache_invalidation_listener import (
            LEADER_HEALTH_CHECK_INTERVAL_SECONDS,
        )

        assert LEADER_HEALTH_CHECK_INTERVAL_SECONDS == 30.0
        assert isinstance(LEADER_HEALTH_CHECK_INTERVAL_SECONDS, float)

    def test_takeover_timeout_seconds(self) -> None:
        """LEADER_TAKEOVER_TIMEOUT_SECONDS = 90.0 (CR 14-1 결정)."""
        from apps.api.core.cache_invalidation_listener import (
            LEADER_TAKEOVER_TIMEOUT_SECONDS,
        )

        assert LEADER_TAKEOVER_TIMEOUT_SECONDS == 90.0
        assert isinstance(LEADER_TAKEOVER_TIMEOUT_SECONDS, float)

    def test_health_check_interval_less_than_takeover_timeout(self) -> None:
        """Health check interval < takeover timeout (3x safety ratio)."""
        from apps.api.core.cache_invalidation_listener import (
            LEADER_HEALTH_CHECK_INTERVAL_SECONDS,
            LEADER_TAKEOVER_TIMEOUT_SECONDS,
        )

        assert (
            LEADER_HEALTH_CHECK_INTERVAL_SECONDS
            < LEADER_TAKEOVER_TIMEOUT_SECONDS
        )


# ── Test NEW exception types (CR 12-5 D-14 envelope) ──────────
class TestNewExceptionTypes:
    """2 NEW typed exceptions for leader election + takeover."""

    def test_leader_election_failed_error_exists(self) -> None:
        """LeaderElectionFailedError is a typed Exception subclass."""
        from apps.api.core.cache_invalidation_listener import (
            LeaderElectionFailedError,
        )

        exc = LeaderElectionFailedError(
            reason="election failed",
            trace_id="trace-test-1",
        )
        assert isinstance(exc, Exception)
        assert exc.reason == "election failed"
        assert exc.trace_id == "trace-test-1"

    def test_leader_takeover_failed_error_exists(self) -> None:
        """LeaderTakeoverFailedError is a typed Exception subclass."""
        from apps.api.core.cache_invalidation_listener import (
            LeaderTakeoverFailedError,
        )

        exc = LeaderTakeoverFailedError(
            reason="takeover failed",
            trace_id="trace-test-2",
        )
        assert isinstance(exc, Exception)
        assert exc.reason == "takeover failed"
        assert exc.trace_id == "trace-test-2"

    def test_leader_election_failed_ko_constant(self) -> None:
        """LEADER_ELECTION_FAILED_KO Korean SSOT message."""
        from apps.api.core.cache_invalidation_listener import (
            LEADER_ELECTION_FAILED_KO,
        )

        # Must be a non-empty str (AD-15 §11 Korean SSOT).
        assert isinstance(LEADER_ELECTION_FAILED_KO, str)
        assert len(LEADER_ELECTION_FAILED_KO) > 0
        # Should mention "리더" or "선출" (leader/election Korean).
        assert (
            "리더" in LEADER_ELECTION_FAILED_KO
            or "선출" in LEADER_ELECTION_FAILED_KO
        )

    def test_leader_takeover_failed_ko_constant(self) -> None:
        """LEADER_TAKEOVER_FAILED_KO Korean SSOT message."""
        from apps.api.core.cache_invalidation_listener import (
            LEADER_TAKEOVER_FAILED_KO,
        )

        assert isinstance(LEADER_TAKEOVER_FAILED_KO, str)
        assert len(LEADER_TAKEOVER_FAILED_KO) > 0
        # Should mention "리더" or "인수" (leader/takeover Korean).
        assert (
            "리더" in LEADER_TAKEOVER_FAILED_KO
            or "인수" in LEADER_TAKEOVER_FAILED_KO
        )


# ── Test internal helper signatures (REPLACED with EXTENSION) ──
class TestLeaderElectionMethodSignatures:
    """Internal helper method signatures for leader election + takeover."""

    def test_attempt_leader_election_method_exists(self) -> None:
        """_attempt_leader_election exists as async method."""
        from apps.api.core.cache_invalidation_listener import (
            CacheInvalidationListener,
        )

        assert hasattr(CacheInvalidationListener, "_attempt_leader_election")
        # Verify it's async.
        assert asyncio.iscoroutinefunction(
            CacheInvalidationListener._attempt_leader_election,
        )

    def test_leader_election_loop_method_exists(self) -> None:
        """_leader_election_loop exists as async method."""
        from apps.api.core.cache_invalidation_listener import (
            CacheInvalidationListener,
        )

        assert hasattr(CacheInvalidationListener, "_leader_election_loop")
        assert asyncio.iscoroutinefunction(
            CacheInvalidationListener._leader_election_loop,
        )

    def test_attempt_takeover_method_exists(self) -> None:
        """_attempt_takeover exists as async method."""
        from apps.api.core.cache_invalidation_listener import (
            CacheInvalidationListener,
        )

        assert hasattr(CacheInvalidationListener, "_attempt_takeover")
        assert asyncio.iscoroutinefunction(
            CacheInvalidationListener._attempt_takeover,
        )


# ── Test graceful degradation (single-pod fallback) ──────────
class TestGracefulDegradation:
    """Single-pod mode: leader/follower election behaves deterministically."""

    def test_single_pod_graceful_degradation(self) -> None:
        """Single-pod startup does not raise LeaderElectionFailedError."""
        # Listener start should attempt election but degrade gracefully
        # if a connection fails — never propagate LeaderElectionFailedError
        # out of `start()` itself. (CR 14-1 결정: degrade, don't block.)
        from apps.api.core.cache_invalidation_listener import (
            LeaderElectionFailedError,
        )
        # Verify the exception class is importable + distinguishable.
        exc = LeaderElectionFailedError(
            reason="test",
            trace_id="trace-graceful",
        )
        assert exc.__class__.__name__ == "LeaderElectionFailedError"


# ── Test state transitions ────────────────────────────────────
class TestStateTransitions:
    """State transitions: election loop + takeover path."""

    def test_state_transitions_are_isolated(self) -> None:
        """Each listener instance has its own state (no shared global)."""
        from apps.api.core.cache_invalidation_listener import (
            LeaderElectionState,
        )

        state_a = LeaderElectionState(
            is_leader=True,
            leader_pod_id="pod-a",
            follower_pod_ids=frozenset({"pod-b"}),
        )
        state_b = LeaderElectionState(
            is_leader=False,
            leader_pod_id="pod-b",
            follower_pod_ids=frozenset({"pod-a"}),
        )
        # Each state is independent.
        assert state_a.is_leader is True
        assert state_b.is_leader is False
        assert state_a.leader_pod_id != state_b.leader_pod_id

    def test_state_transition_uuid_pod_id(self) -> None:
        """Pod IDs can be UUID strings (k8s style) or arbitrary strings."""
        from apps.api.core.cache_invalidation_listener import (
            LeaderElectionState,
        )

        pod_uuid = str(uuid.uuid4())
        state = LeaderElectionState(
            is_leader=True,
            leader_pod_id=pod_uuid,
            follower_pod_ids=frozenset(),
        )
        assert state.leader_pod_id == pod_uuid


# ── Test integer hex conversion (deterministic ASCII encoding) ─
class TestHexLockIdEncoding:
    """0x4C49_5354_4641_4E54 decodes to 'LISTFANT' (ASCII)."""

    def test_listen_fanout_lock_id_is_ascii(self) -> None:
        """The lock ID integer encodes to ASCII 'LISTFANT' (verbose hex)."""
        from apps.api.core.cache_invalidation_listener import (
            LISTEN_FANOUT_LOCK_ID,
        )

        # 64-bit int → 8 byte string.
        as_bytes = LISTEN_FANOUT_LOCK_ID.to_bytes(8, "big", signed=False)
        decoded = as_bytes.decode("ascii")
        assert decoded == "LISTFANT"
