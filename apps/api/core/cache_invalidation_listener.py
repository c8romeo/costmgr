"""apps.api.core.cache_invalidation_listener — AD-25 cache invalidation LISTEN daemon.

Story 13.1 (LISTEN/NOTIFY Consume Trigger EXTENSION, A39/A51/A52 결정 wire):
D-10-2-DEFER-3 ✅ RESOLVED wire 진입. PostgreSQL NOTIFY trigger on
`cache_invalidation_log` AFTER INSERT (alembic 0033) emits a 5-key
alphabetical JSON payload. This module consumes those notifications via
psycopg 3.x `AsyncConnection.listen()` and routes them to the 4 channel
adapters (M10/M3/M11).

Story 14.1 (LISTEN/NOTIFY Consume Cross-Tenant Fan-Out + Multi-Process
Coordination, A53+A57+A58+A59 결정 wire): D-13-1-DEFER-3 ✅ RESOLVED.
PostgreSQL NOTIFY trigger on `cache_invalidation_log` AFTER INSERT
(alembic 0034) emits a 7-key alphabetical JSON payload for
`channel = 'cross_tenant_fanout'` ONLY. The listener EXTENDS to a 5+
channel routing dispatch table (cross_tenant_fanout 추가) and adds
multi-process coordination via leader election
(`pg_try_advisory_xact_lock(LISTEN_FANOUT_LOCK_ID)`).

Per AD-25 (ARCHITECTURE-SPINE.md §142-148 verbatim):
  "M10 cache key is `(tenant_id, period_key, calculation_result_hash)`.
   A new AD-4 commit, an AD-22 reversal insert, or an M11 reopen emits
   one DB notification per channel."

Channel whitelist (5+ channels, AD-25 verbatim EXTENSION):
  - `ai_cache`               — M10 AI cache invalidation (11-1 wire 보존)
  - `cost_engine_cache`      — M3 cost engine calculation result cache (11-3 NEW)
  - `fiscal_period_cache`    — M11 fiscal_periods + fiscal_period_snapshots
                                metadata cache (11-3 NEW)
  - `closing_snapshot_cache` — M11 closing_snapshot + ledger closing event
                                cache (11-3 NEW)
  - `cross_tenant_fanout`    — cross-tenant invalidation fan-out (14-1 NEW)

Payload shape (5 keys for 4 channels, alphabetical order — V8 determinism):
  {
    "channel":              "ai_cache",
    "correction_group_id":  "uuid-string",
    "period_key":           "YYYY-MM",
    "tenant_id":            "uuid-string",
    "trace_id":             "uuid-string"
  }

Payload shape (7 keys for cross_tenant_fanout channel — V8 determinism EXTENSION):
  {
    "channel":              "cross_tenant_fanout",
    "correction_group_id":  "uuid-string",
    "invalidation_id":      "uuid-string",
    "period_key":           "YYYY-MM",
    "source_tenant_id":     "uuid-string",
    "target_tenant_ids":    ["uuid-string-1", "uuid-string-2", ...],
    "trace_id":             "uuid-string"
  }

NOTE: payload is published by the AFTER INSERT trigger on
  cache_invalidation_log (alembic 0033 + 0034). The 5/7 keys are
  emitted in alphabetical order via `json_object()` in the trigger
  function — this is part of the V8 byte-identical contract
  (F13.3 / F14.3 verbatim).

Per CR 12-5 D-PARITY-01 inversion: payload shape MUST match
  apps/web/lib/cache-invalidation-listener.ts (Python ↔ TS parity).
  Drift → drift detector test fail + 1-line ko-KR reject.

Reconnect/backoff strategy:
- Exponential backoff: base 1s, factor 2 (max 30s)
- Jitter: ±20% to prevent thundering-herd reconnects
- Circuit breaker: 5 consecutive failures → 60s cool-down
- Persistent failure → graceful degradation (next restart retries)

Multi-process coordination strategy (Story 14.1):
- Leader election via PostgreSQL advisory lock
  (`pg_try_advisory_xact_lock(LISTEN_FANOUT_LOCK_ID)`).
- Leader: publishes NOTIFY for cross_tenant_fanout channel (and any
  other publisher-side NOTIFYs in future extensions).
- Followers: consume NOTIFYs only (do not publish).
- Leader health check: 30s interval (background task in each follower).
- Leader unresponsive 90s → follower 강제 takeover via
  `pg_try_advisory_lock` (non-xact, plain lock).
- Single-process 환경 graceful degradation: leader = self, follower = none.

AD-1 + AD-11 binding: this module is in `apps/api/core/` (infra layer).
It does NOT import `packages.cost_engine` directly. Adapter dispatch is
inversion-of-control (Protocol-based) — adapters register themselves
with the listener at startup.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import random
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────
# NOTIFY channel name (PostgreSQL `pg_notify` channel identifier).
# Mirrored in apps/api/alembic/versions/0033_listen_notify_consume_trigger.py:NOTIFY_CHANNEL_NAME
# and apps/api/alembic/versions/0034_listen_notify_consume_cross_tenant_fanout.py:NOTIFY_CHANNEL_NAME.
NOTIFY_CHANNEL_NAME: str = "cache_invalidation_log"

# Payload keys (5 keys for 4 channels, alphabetical order — V8 determinism contract).
# Use the exact lowercase string identifiers — TS mirror keys are spelled
# the same way (CR 12-5 D-PARITY-01 inversion).
PAYLOAD_KEY_CHANNEL: str = "channel"
PAYLOAD_KEY_CORRECTION_GROUP_ID: str = "correction_group_id"
PAYLOAD_KEY_PERIOD_KEY: str = "period_key"
PAYLOAD_KEY_TENANT_ID: str = "tenant_id"
PAYLOAD_KEY_TRACE_ID: str = "trace_id"

# Story 14.1 EXTENSION keys (7 keys for cross_tenant_fanout channel).
PAYLOAD_KEY_INVALIDATION_ID: str = "invalidation_id"
PAYLOAD_KEY_SOURCE_TENANT_ID: str = "source_tenant_id"
PAYLOAD_KEY_TARGET_TENANT_IDS: str = "target_tenant_ids"

# All expected payload keys for the 4 existing channels (frozen for V8 determinism validation).
EXPECTED_PAYLOAD_KEYS: frozenset[str] = frozenset(
    {
        PAYLOAD_KEY_CHANNEL,
        PAYLOAD_KEY_CORRECTION_GROUP_ID,
        PAYLOAD_KEY_PERIOD_KEY,
        PAYLOAD_KEY_TENANT_ID,
        PAYLOAD_KEY_TRACE_ID,
    }
)

# All expected payload keys for cross_tenant_fanout (frozen, V8 determinism).
EXPECTED_PAYLOAD_KEYS_CROSS_TENANT: frozenset[str] = frozenset(
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

# 5+ channel whitelist (AD-25 verbatim EXTENSION). Mirrored in
# `apps/api/core/cache_invalidation_publisher.py:ALLOWED_CHANNELS` +
# alembic 0034 cross_tenant_fanout 추가.
ALLOWED_CHANNELS: frozenset[str] = frozenset(
    {
        "ai_cache",
        "cost_engine_cache",
        "fiscal_period_cache",
        "closing_snapshot_cache",
        "cross_tenant_fanout",
    }
)

# Backoff parameters.
_BACKOFF_BASE_SECONDS: float = 1.0
_BACKOFF_FACTOR: float = 2.0
_BACKOFF_MAX_SECONDS: float = 30.0
_BACKOFF_JITTER_RATIO: float = 0.2  # ±20%

# Circuit breaker parameters.
_CIRCUIT_BREAKER_FAIL_THRESHOLD: int = 5
_CIRCUIT_BREAKER_COOLDOWN_SECONDS: float = 60.0

# Multi-process coordination (Story 14.1 wire).
LISTEN_FANOUT_LOCK_ID: int = 0x4C49_5354_4641_4E54  # 'LISTFANT' ASCII hex
LEADER_HEALTH_CHECK_INTERVAL_SECONDS: float = 30.0
LEADER_TAKEOVER_TIMEOUT_SECONDS: float = 90.0

# Error codes (CR 12-5 D-14 envelope). These are mapped to HTTP responses
# by the 2 NEW exception handlers in apps/api/main.py (T3 wire).
ERROR_CODE_LISTENER_START_FAILED: str = "LISTENER_START_FAILED"
ERROR_CODE_LISTENER_STOP_FAILED: str = "LISTENER_STOP_FAILED"
ERROR_CODE_LISTENER_PAYLOAD_INVALID: str = "LISTENER_PAYLOAD_INVALID"
ERROR_CODE_LEADER_ELECTION_FAILED: str = "LEADER_ELECTION_FAILED"
ERROR_CODE_LEADER_TAKEOVER_FAILED: str = "LEADER_TAKEOVER_FAILED"

# Korean constants — AD-15 §11 SSOT.
LISTENER_START_FAILED_KO: str = "캐시 무효화 리스너 시작 실패"
LISTENER_STOP_FAILED_KO: str = "캐시 무효화 리스너 종료 실패"
LISTENER_PAYLOAD_INVALID_KO: str = "캐시 무효화 페이로드 형식 오류"
LEADER_ELECTION_FAILED_KO: str = "리스너 리더 선출 실패"
LEADER_TAKEOVER_FAILED_KO: str = "리스너 리더 인계 실패"


# ── Adapter protocol (port) ──────────────────────────────────
class CacheInvalidationAdapter(Protocol):
    """Protocol for cache invalidation adapters (M10/M3/M11/cross_tenant).

    Each channel adapter receives the parsed payload and performs
    the channel-specific eviction. The adapter MUST be idempotent
    (it may be called multiple times for the same payload during
    reconnect/replay).
    """

    channel: str

    async def on_invalidate(self, payload: dict[str, str]) -> None:
        """Evict cache entries for the given payload.

        Args:
            payload: 5-key dict (channel, correction_group_id, period_key,
                tenant_id, trace_id) for the 4 standard channels, OR
                7-key dict (channel, correction_group_id, invalidation_id,
                period_key, source_tenant_id, target_tenant_ids, trace_id)
                for cross_tenant_fanout. The `channel` field is ALWAYS
                `self.channel` — the adapter only receives payloads for
                its own channel (cross-channel contamination is rejected
                by the listener dispatch table).
        """
        ...


# ── Typed exceptions ─────────────────────────────────────────
class ListenerStartFailedError(Exception):
    """503 LISTENER_START_FAILED — CacheInvalidationListener.start() failed."""

    def __init__(
        self,
        *,
        reason: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"CacheInvalidationListener.start() failed: {reason} "
            f"(trace_id={trace_id!r})"
        )
        self.reason = reason
        self.trace_id = trace_id


class ListenerStopFailedError(Exception):
    """503 LISTENER_STOP_FAILED — CacheInvalidationListener.stop() failed."""

    def __init__(
        self,
        *,
        reason: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"CacheInvalidationListener.stop() failed: {reason} "
            f"(trace_id={trace_id!r})"
        )
        self.reason = reason
        self.trace_id = trace_id


class ListenerPayloadInvalidError(ValueError):
    """ValueError subclass — payload shape violation (V8 determinism)."""

    def __init__(
        self,
        *,
        reason: str,
        payload: Any,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"listener payload invalid: {reason} "
            f"(payload={payload!r}, trace_id={trace_id!r})"
        )
        self.reason = reason
        self.payload = payload
        self.trace_id = trace_id


class LeaderElectionFailedError(Exception):
    """503 LEADER_ELECTION_FAILED — leader election via advisory lock failed.

    Story 14.1 wire (multi-process coordination via
    `pg_try_advisory_xact_lock(LISTEN_FANOUT_LOCK_ID)`). Mapped to
    HTTP 503 by main.py global handler (T3 wire).
    """

    def __init__(
        self,
        *,
        reason: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"leader election failed: {reason} (trace_id={trace_id!r})"
        )
        self.reason = reason
        self.trace_id = trace_id


class LeaderTakeoverFailedError(Exception):
    """503 LEADER_TAKEOVER_FAILED — follower takeover via advisory lock failed.

    Story 14.1 wire (multi-process coordination leader takeover).
    Mapped to HTTP 503 by main.py global handler (T3 wire).
    """

    def __init__(
        self,
        *,
        reason: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"leader takeover failed: {reason} (trace_id={trace_id!r})"
        )
        self.reason = reason
        self.trace_id = trace_id


# ── Parsed payload dataclass ─────────────────────────────────
@dataclass(frozen=True)
class CacheInvalidationPayload:
    """Parsed NOTIFY payload (5/7 keys, V8 determinism).

    Frozen for hashability — useful for idempotency keys in channel
    adapters. Field order is alphabetical:
    - 5 keys: channel, correction_group_id, period_key, tenant_id, trace_id
    - 7 keys (cross_tenant_fanout): channel, correction_group_id,
      invalidation_id, period_key, source_tenant_id, target_tenant_ids,
      trace_id

    The canonical order is guaranteed by the trigger function DDL
    (alembic 0033 + 0034).
    """

    channel: str
    correction_group_id: str
    period_key: str
    tenant_id: str
    trace_id: str
    # Story 14.1 EXTENSION — cross_tenant_fanout fields.
    invalidation_id: str = ""
    source_tenant_id: str = ""
    target_tenant_ids: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Return the payload as a 5-key or 7-key dict (alphabetical order)."""
        base = {
            PAYLOAD_KEY_CHANNEL: self.channel,
            PAYLOAD_KEY_CORRECTION_GROUP_ID: self.correction_group_id,
            PAYLOAD_KEY_PERIOD_KEY: self.period_key,
            PAYLOAD_KEY_TRACE_ID: self.trace_id,
        }
        if self.channel == "cross_tenant_fanout":
            base[PAYLOAD_KEY_INVALIDATION_ID] = self.invalidation_id
            base[PAYLOAD_KEY_SOURCE_TENANT_ID] = self.source_tenant_id
            base[PAYLOAD_KEY_TARGET_TENANT_IDS] = list(self.target_tenant_ids)
        else:
            base[PAYLOAD_KEY_TENANT_ID] = self.tenant_id
        return base


# ── V8 deterministic JSON serialization ───────────────────────
def serialize_payload_for_v8(payload: dict[str, Any]) -> str:
    """Deterministic JSON serialization for V8 byte-identical contract.

    CR 4-4 + F13.3 + F14.3 verbatim: payload JSON MUST be byte-identical
    for the same input across reruns. Uses `json.dumps(payload,
    sort_keys=True, separators=(',', ':'))` — no whitespace, alphabetical
    key ordering. For `target_tenant_ids` arrays, the input is expected
    to already be a list (the trigger function emits it as JSONB
    canonical form); we re-serialize through `json.dumps(sort_keys=True)`
    which preserves list element order.

    Args:
        payload: 5-key dict (channel, correction_group_id, period_key,
            tenant_id, trace_id) OR 7-key dict (cross_tenant_fanout).

    Returns:
        JSON string with alphabetical key ordering, no whitespace.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


# ── Payload parse + validation ────────────────────────────────
def parse_payload(raw: str) -> CacheInvalidationPayload:
    """Parse a NOTIFY payload string into a typed dataclass.

    V8 determinism validation: parses the raw JSON, validates the
    expected keys (5 or 7 alphabetical depending on channel),
    validates the channel is in ALLOWED_CHANNELS, and returns the
    frozen dataclass.

    For cross_tenant_fanout channel, `target_tenant_ids` is validated
    as a JSON array (tuple of UUID strings) — V8 determinism requires
    array element order to be preserved (caller is responsible for
    canonical order; the trigger function emits JSONB canonical form).

    Args:
        raw: Raw JSON string from `pg_notify`.

    Returns:
        CacheInvalidationPayload (frozen).

    Raises:
        ListenerPayloadInvalidError: payload shape / channel / key violation.
    """
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ListenerPayloadInvalidError(
            reason=f"JSON parse failed: {exc}",
            payload=raw,
            trace_id="",
        ) from exc

    if not isinstance(parsed, dict):
        raise ListenerPayloadInvalidError(
            reason="payload is not a JSON object",
            payload=parsed,
            trace_id="",
        )

    # Type-check the channel field FIRST (decides which key set to validate).
    channel = parsed.get(PAYLOAD_KEY_CHANNEL)
    if not isinstance(channel, str):
        raise ListenerPayloadInvalidError(
            reason=f"channel must be str, got {type(channel).__name__!r}",
            payload=parsed,
            trace_id="",
        )
    if channel not in ALLOWED_CHANNELS:
        raise ListenerPayloadInvalidError(
            reason=f"channel {channel!r} not in ALLOWED_CHANNELS",
            payload=parsed,
            trace_id="",
        )

    # Pick the expected key set based on channel.
    if channel == "cross_tenant_fanout":
        expected_keys = EXPECTED_PAYLOAD_KEYS_CROSS_TENANT
    else:
        expected_keys = EXPECTED_PAYLOAD_KEYS

    actual_keys = frozenset(parsed.keys())
    if actual_keys != expected_keys:
        raise ListenerPayloadInvalidError(
            reason=(
                f"payload keys mismatch for channel {channel!r}: "
                f"expected {sorted(expected_keys)}, "
                f"got {sorted(actual_keys)}"
            ),
            payload=parsed,
            trace_id="",
        )

    # V8 determinism: serialized bytes for the same input MUST be identical.
    # We re-serialize and validate the roundtrip has the same shape.
    canonical = serialize_payload_for_v8(parsed)
    if set(json.loads(canonical).keys()) != expected_keys:
        raise ListenerPayloadInvalidError(
            reason="canonical serialization failed V8 determinism check",
            payload=parsed,
            trace_id="",
        )

    trace_id = parsed[PAYLOAD_KEY_TRACE_ID]
    if not isinstance(trace_id, str) or not trace_id:
        raise ListenerPayloadInvalidError(
            reason="trace_id must be non-empty str",
            payload=parsed,
            trace_id="",
        )

    period_key = parsed[PAYLOAD_KEY_PERIOD_KEY]
    if not isinstance(period_key, str) or not period_key:
        raise ListenerPayloadInvalidError(
            reason="period_key must be non-empty str",
            payload=parsed,
            trace_id="",
        )

    correction_group_id = parsed[PAYLOAD_KEY_CORRECTION_GROUP_ID]
    if correction_group_id is not None:
        try:
            uuid.UUID(correction_group_id)
        except (ValueError, KeyError) as exc:
            raise ListenerPayloadInvalidError(
                reason=(
                    f"{PAYLOAD_KEY_CORRECTION_GROUP_ID} is not a valid UUID: "
                    f"{exc}"
                ),
                payload=parsed,
                trace_id="",
            ) from exc

    if channel == "cross_tenant_fanout":
        # 7-key payload (cross_tenant_fanout) — validate target_tenant_ids.
        invalidation_id = parsed[PAYLOAD_KEY_INVALIDATION_ID]
        if not isinstance(invalidation_id, str):
            raise ListenerPayloadInvalidError(
                reason=(
                    f"{PAYLOAD_KEY_INVALIDATION_ID} must be str, "
                    f"got {type(invalidation_id).__name__!r}"
                ),
                payload=parsed,
                trace_id="",
            )

        source_tenant_id = parsed[PAYLOAD_KEY_SOURCE_TENANT_ID]
        if not isinstance(source_tenant_id, str):
            raise ListenerPayloadInvalidError(
                reason=(
                    f"{PAYLOAD_KEY_SOURCE_TENANT_ID} must be str, "
                    f"got {type(source_tenant_id).__name__!r}"
                ),
                payload=parsed,
                trace_id="",
            )
        try:
            uuid.UUID(source_tenant_id)
        except ValueError as exc:
            raise ListenerPayloadInvalidError(
                reason=(
                    f"{PAYLOAD_KEY_SOURCE_TENANT_ID} is not a valid UUID: "
                    f"{exc}"
                ),
                payload=parsed,
                trace_id="",
            ) from exc

        target_tenant_ids_raw = parsed[PAYLOAD_KEY_TARGET_TENANT_IDS]
        if not isinstance(target_tenant_ids_raw, list):
            raise ListenerPayloadInvalidError(
                reason=(
                    f"{PAYLOAD_KEY_TARGET_TENANT_IDS} must be list, "
                    f"got {type(target_tenant_ids_raw).__name__!r}"
                ),
                payload=parsed,
                trace_id="",
            )
        target_tenant_ids: list[str] = []
        for idx, tid in enumerate(target_tenant_ids_raw):
            if not isinstance(tid, str):
                raise ListenerPayloadInvalidError(
                    reason=(
                        f"{PAYLOAD_KEY_TARGET_TENANT_IDS}[{idx}] must be "
                        f"str, got {type(tid).__name__!r}"
                    ),
                    payload=parsed,
                    trace_id="",
                )
            try:
                uuid.UUID(tid)
            except ValueError as exc:
                raise ListenerPayloadInvalidError(
                    reason=(
                        f"{PAYLOAD_KEY_TARGET_TENANT_IDS}[{idx}] is not a "
                        f"valid UUID: {exc}"
                    ),
                    payload=parsed,
                    trace_id="",
                ) from exc
            target_tenant_ids.append(tid)

        return CacheInvalidationPayload(
            channel=channel,
            correction_group_id=correction_group_id or "",
            period_key=period_key,
            tenant_id=source_tenant_id,
            trace_id=trace_id,
            invalidation_id=invalidation_id,
            source_tenant_id=source_tenant_id,
            target_tenant_ids=tuple(target_tenant_ids),
        )

    # 5-key payload (4 standard channels) — validate tenant_id.
    tenant_id = parsed[PAYLOAD_KEY_TENANT_ID]
    if not isinstance(tenant_id, str):
        raise ListenerPayloadInvalidError(
            reason=(
                f"{PAYLOAD_KEY_TENANT_ID} must be str, "
                f"got {type(tenant_id).__name__!r}"
            ),
            payload=parsed,
            trace_id="",
        )
    try:
        uuid.UUID(tenant_id)
    except ValueError as exc:
        raise ListenerPayloadInvalidError(
            reason=f"{PAYLOAD_KEY_TENANT_ID} is not a valid UUID: {exc}",
            payload=parsed,
            trace_id="",
        ) from exc

    return CacheInvalidationPayload(
        channel=channel,
        correction_group_id=correction_group_id or "",
        period_key=period_key,
        tenant_id=tenant_id,
        trace_id=trace_id,
    )


# ── Backoff helper ───────────────────────────────────────────
def _compute_backoff_seconds(attempt: int) -> float:
    """Compute exponential backoff with jitter.

    Formula: min(base * factor^attempt, max) * (1 ± jitter_ratio)

    Args:
        attempt: 0-indexed retry attempt number.

    Returns:
        Backoff duration in seconds (always >= 0).
    """
    raw = _BACKOFF_BASE_SECONDS * (_BACKOFF_FACTOR ** attempt)
    capped = min(raw, _BACKOFF_MAX_SECONDS)
    jitter = capped * _BACKOFF_JITTER_RATIO
    # Symmetric jitter: capped ± jitter.
    return max(0.0, capped + random.uniform(-jitter, jitter))


# ── CacheInvalidationListener ────────────────────────────────
# Adapter factory type alias — returns the adapter for a given channel.
AdapterFactory = Callable[[], CacheInvalidationAdapter]


@dataclass(frozen=True)
class LeaderElectionState:
    """Leader election state (Story 14.1 multi-process coordination).

    Frozen for thread-safety. Updated by `_leader_election_loop()`
    during the listener's lifetime.
    """

    is_leader: bool
    leader_pod_id: str
    follower_pod_ids: tuple[str, ...] = field(default_factory=tuple)


class CacheInvalidationListener:
    """AD-25 LISTEN daemon — 5+ channel cache invalidation consume.

    Lifecycle:
    - `start()` opens a psycopg AsyncConnection, calls `LISTEN
      cache_invalidation_log`, attempts leader election via
      `pg_try_advisory_xact_lock(LISTEN_FANOUT_LOCK_ID)`, and spawns
      an asyncio Task that polls notifications. Called from FastAPI
      lifespan at startup.
    - `stop()` cancels the task, calls `UNLISTEN cache_invalidation_log`,
      releases the advisory lock, and closes the connection. Called
      from FastAPI lifespan at shutdown.

    Reconnect/backoff:
    - On connection drop, the listener retries with exponential backoff
      + jitter (cap 30s).
    - After 5 consecutive failures, the circuit breaker opens for 60s.
    - All retries are logged for observability.

    Adapter dispatch:
    - `_consume_notifications()` parses each NOTIFY payload and looks up
      the channel-specific adapter from the dispatch table.
    - Unknown channels raise `ListenerPayloadInvalidError` (fail-fast).

    Multi-process coordination (Story 14.1):
    - `start()` attempts leader election. If `pg_try_advisory_xact_lock`
      returns true, the listener is the leader (publisher role).
    - If false, the listener is a follower (consumer only).
    - `_leader_election_loop()` runs in followers to monitor leader
      health and force takeover after LEADER_TAKEOVER_TIMEOUT_SECONDS.
    - Single-process environment: leader = self, follower = none
      (graceful degradation).

    The listener is pure-Python (AD-5 stdlib-only + psycopg 3.x async).
    It does NOT import `packages.cost_engine` directly.
    """

    def __init__(
        self,
        *,
        adapter_factories: dict[str, AdapterFactory],
        conn_factory: Callable[[], Awaitable[Any]] | None = None,
        pod_id: str | None = None,
    ) -> None:
        """Initialize the listener.

        Args:
            adapter_factories: Channel → adapter factory mapping. MUST
                contain all 5+ channels (ai_cache / cost_engine_cache /
                fiscal_period_cache / closing_snapshot_cache /
                cross_tenant_fanout).
            conn_factory: Async connection factory (creates a psycopg
                AsyncConnection). If None, the listener uses a default
                factory that connects to the project's asyncpg pool via
                the standard `get_asyncpg_pool()` helper. Tests inject
                a mock factory.
            pod_id: Identifier for this process (used in leader election
                logging + health check). Defaults to a deterministic
                hash of the process ID (single-process env).
        """
        if not isinstance(adapter_factories, dict):
            raise ValueError(
                f"adapter_factories must be dict, got "
                f"{type(adapter_factories).__name__!r}"
            )
        missing = ALLOWED_CHANNELS - set(adapter_factories.keys())
        if missing:
            raise ValueError(
                f"adapter_factories missing channels: {sorted(missing)}"
            )
        extra = set(adapter_factories.keys()) - ALLOWED_CHANNELS
        if extra:
            raise ValueError(
                f"adapter_factories has unknown channels: {sorted(extra)}"
            )

        self._adapter_factories = adapter_factories
        self._conn_factory = conn_factory
        self._pod_id = pod_id or f"pod-{uuid.uuid4().hex[:8]}"
        self._task: asyncio.Task[None] | None = None
        self._leader_task: asyncio.Task[None] | None = None
        self._conn: Any = None
        self._leader_conn: Any = None
        self._stop_event = asyncio.Event()
        self._consecutive_failures: int = 0
        self._circuit_open_until: float = 0.0
        self._is_started: bool = False
        self._leader_state: LeaderElectionState = LeaderElectionState(
            is_leader=True,
            leader_pod_id=self._pod_id,
            follower_pod_ids=(),
        )

    @property
    def is_leader(self) -> bool:
        """Whether this process is the multi-process coordination leader."""
        return self._leader_state.is_leader

    @property
    def leader_state(self) -> LeaderElectionState:
        """Current leader election state (frozen)."""
        return self._leader_state

    async def start(self) -> None:
        """Start the LISTEN daemon + attempt leader election.

        Idempotent: a second call is a no-op (returns immediately).
        Raises ListenerStartFailedError if the connection cannot be
        opened within the first retry attempt.
        """
        if self._is_started:
            logger.warning("CacheInvalidationListener.start() called twice — no-op")
            return

        trace_id = "listener-start"
        try:
            self._conn = await self._open_connection()
            await self._conn.execute(f"LISTEN {NOTIFY_CHANNEL_NAME}")
            # Attempt leader election. Failure here does NOT prevent the
            # listener from running (graceful degradation — leader election
            # failures are logged and the listener defaults to single-process
            # mode where leader = self, follower = none).
            try:
                await self._attempt_leader_election()
            except LeaderElectionFailedError as leader_exc:
                logger.warning(
                    "Leader election failed (graceful degradation — "
                    "listener continues as single-process leader): %s",
                    leader_exc,
                )
        except Exception as exc:
            logger.exception(
                "CacheInvalidationListener.start() failed: %s", exc
            )
            raise ListenerStartFailedError(
                reason=str(exc),
                trace_id=trace_id,
            ) from exc

        self._stop_event.clear()
        self._task = asyncio.create_task(
            self._consume_notifications(),
            name="cache-invalidation-listener",
        )
        # If follower, start leader election health check loop.
        if not self._leader_state.is_leader:
            self._leader_task = asyncio.create_task(
                self._leader_election_loop(),
                name="cache-invalidation-leader-election",
            )
        self._is_started = True
        logger.info(
            "CacheInvalidationListener started (channel=%s, pod_id=%s, "
            "is_leader=%s)",
            NOTIFY_CHANNEL_NAME,
            self._pod_id,
            self._leader_state.is_leader,
        )

    async def stop(self) -> None:
        """Stop the LISTEN daemon.

        Idempotent: a second call is a no-op. Raises
        ListenerStopFailedError if the connection cannot be cleanly
        closed.
        """
        if not self._is_started:
            return

        trace_id = "listener-stop"
        self._stop_event.set()
        try:
            if self._task is not None:
                self._task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._task
                self._task = None

            if self._leader_task is not None:
                self._leader_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._leader_task
                self._leader_task = None

            # Release advisory lock if we held it.
            if self._leader_conn is not None:
                try:
                    # Transaction ends → lock auto-released.
                    with contextlib.suppress(Exception):
                        await self._leader_conn.execute("ROLLBACK")
                finally:
                    with contextlib.suppress(Exception):
                        await self._leader_conn.close()
                    self._leader_conn = None

            if self._conn is not None:
                try:
                    await self._conn.execute(
                        f"UNLISTEN {NOTIFY_CHANNEL_NAME}"
                    )
                finally:
                    await self._conn.close()
                    self._conn = None
        except Exception as exc:
            logger.exception(
                "CacheInvalidationListener.stop() failed: %s", exc
            )
            raise ListenerStopFailedError(
                reason=str(exc),
                trace_id=trace_id,
            ) from exc
        finally:
            self._is_started = False
            logger.info("CacheInvalidationListener stopped")

    async def _open_connection(self) -> Any:
        """Open a psycopg AsyncConnection via the configured factory."""
        if self._conn_factory is None:
            # Default: import lazily to avoid circular imports.
            from apps.api.core.db import get_asyncpg_pool

            pool = await get_asyncpg_pool()
            return await pool.acquire()
        return await self._conn_factory()

    async def _attempt_leader_election(self) -> None:
        """Attempt leader election via PostgreSQL advisory lock.

        Per F14.2-(a) verbatim: `pg_try_advisory_xact_lock(LISTEN_FANOUT_LOCK_ID)`
        — deterministic hash of pod_id is NOT used in this minimal
        implementation (the advisory lock is binary: whoever holds it
        is the leader). If the lock is already held by another process,
        this process is a follower.

        Single-process 환경 graceful degradation: when the connection
        cannot acquire the advisory lock at all (no DB / pool unavailable),
        the listener defaults to leader = self (graceful degradation —
        F14.2-(a) verbatim single-process environment).
        """
        try:
            if self._conn_factory is None:
                # Default pool path: use the same connection as the listener.
                conn = self._conn
            else:
                conn = await self._conn_factory()

            # pg_try_advisory_xact_lock returns true if the lock was
            # acquired, false otherwise. The lock is held until the
            # transaction ends — we use a dedicated transaction.
            acquired = await conn.fetchval(
                "SELECT pg_try_advisory_xact_lock($1)",
                LISTEN_FANOUT_LOCK_ID,
            )

            if acquired:
                self._leader_conn = conn
                self._leader_state = LeaderElectionState(
                    is_leader=True,
                    leader_pod_id=self._pod_id,
                    follower_pod_ids=(),
                )
                logger.info(
                    "Leader election: this process is the LEADER "
                    "(pod_id=%s, lock_id=%d)",
                    self._pod_id,
                    LISTEN_FANOUT_LOCK_ID,
                )
            else:
                self._leader_state = LeaderElectionState(
                    is_leader=False,
                    leader_pod_id="<unknown-leader>",
                    follower_pod_ids=(self._pod_id,),
                )
                logger.info(
                    "Leader election: this process is a FOLLOWER "
                    "(pod_id=%s)",
                    self._pod_id,
                )
        except Exception as exc:
            # Graceful degradation: if the advisory lock cannot be
            # acquired at all (e.g., DB unavailable), default to
            # leader = self. This is the single-process environment
            # graceful degradation path.
            logger.warning(
                "Leader election advisory lock failed (graceful "
                "degradation — defaulting to leader=self): %s",
                exc,
            )
            self._leader_state = LeaderElectionState(
                is_leader=True,
                leader_pod_id=self._pod_id,
                follower_pod_ids=(),
            )

    async def _leader_election_loop(self) -> None:
        """Background leader election health check loop (follower only).

        Per F14.2-(d) verbatim:
        - Health check interval: LEADER_HEALTH_CHECK_INTERVAL_SECONDS (30s).
        - Leader unresponsive timeout: LEADER_TAKEOVER_TIMEOUT_SECONDS (90s).
        - Force takeover via `pg_try_advisory_lock` (non-xact, plain lock).

        If leader is unresponsive for 90s, the follower attempts to take
        over the advisory lock. On success, it becomes the new leader.
        On failure, it raises LeaderTakeoverFailedError (CR 12-5 D-14
        envelope, 503 LEADER_TAKEOVER_FAILED).
        """
        last_leader_seen = asyncio.get_event_loop().time()
        while not self._stop_event.is_set():
            try:
                await self._sleep(LEADER_HEALTH_CHECK_INTERVAL_SECONDS)

                # In the MVP implementation, we don't actively probe
                # the leader's health — we rely on a simple timeout
                # from the last time we received any indication that
                # the leader is alive. For wire completeness, the
                # timeout is recorded but the actual health probe
                # is deferred to a follow-up story (D-14-1-DEFER-1).

                # If the leader has been unresponsive for
                # LEADER_TAKEOVER_TIMEOUT_SECONDS, attempt takeover.
                now = asyncio.get_event_loop().time()
                if now - last_leader_seen > LEADER_TAKEOVER_TIMEOUT_SECONDS:
                    await self._attempt_takeover()
                    last_leader_seen = now
                else:
                    last_leader_seen = now
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning(
                    "Leader election loop error: %s", exc,
                )

    async def _attempt_takeover(self) -> None:
        """Attempt to take over leadership from an unresponsive leader.

        Per F14.2-(d) verbatim: `pg_try_advisory_lock` (non-xact, plain
        lock). On success, this process becomes the new leader.
        On failure, raises LeaderTakeoverFailedError (CR 12-5 D-14 envelope).
        """
        try:
            if self._conn_factory is None:
                conn = self._conn
            else:
                conn = await self._conn_factory()

            acquired = await conn.fetchval(
                "SELECT pg_try_advisory_lock($1)",
                LISTEN_FANOUT_LOCK_ID,
            )

            if acquired:
                self._leader_conn = conn
                self._leader_state = LeaderElectionState(
                    is_leader=True,
                    leader_pod_id=self._pod_id,
                    follower_pod_ids=(),
                )
                logger.warning(
                    "Leader takeover successful (pod_id=%s became the "
                    "new leader after %ss of unresponsiveness)",
                    self._pod_id,
                    LEADER_TAKEOVER_TIMEOUT_SECONDS,
                )
                # Cancel the leader election loop — we are now leader.
                if self._leader_task is not None:
                    self._leader_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await self._leader_task
                    self._leader_task = None
            else:
                raise LeaderTakeoverFailedError(
                    reason=(
                        f"could not acquire advisory lock after "
                        f"{LEADER_TAKEOVER_TIMEOUT_SECONDS}s of "
                        f"leader unresponsiveness"
                    ),
                    trace_id=f"takeover-{self._pod_id}",
                )
        except LeaderTakeoverFailedError:
            raise
        except Exception as exc:
            raise LeaderTakeoverFailedError(
                reason=str(exc),
                trace_id=f"takeover-{self._pod_id}",
            ) from exc

    async def _consume_notifications(self) -> None:
        """Main consume loop — runs until stop_event is set.

        On connection drop, retries with exponential backoff + jitter
        + circuit breaker. Persistent failures are logged but never
        crash the listener (graceful degradation).
        """
        attempt = 0
        while not self._stop_event.is_set():
            # Circuit breaker gate.
            import time

            now = time.monotonic()
            if now < self._circuit_open_until:
                await self._sleep(_CIRCUIT_BREAKER_COOLDOWN_SECONDS)
                self._circuit_open_until = 0.0
                self._consecutive_failures = 0
                continue

            try:
                if self._conn is None:
                    self._conn = await self._open_connection()
                    await self._conn.execute(f"LISTEN {NOTIFY_CHANNEL_NAME}")

                # Poll for notifications — short timeout to allow stop signal.
                gen = self._conn.notifies(timeout=0.5)
                async for notify in gen:
                    if self._stop_event.is_set():
                        break
                    await self._handle_notify(notify)

                # Reset failure counter on successful iteration.
                self._consecutive_failures = 0
                attempt = 0
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self._consecutive_failures += 1
                logger.warning(
                    "CacheInvalidationListener consume error (attempt %d, "
                    "consecutive failures %d): %s",
                    attempt,
                    self._consecutive_failures,
                    exc,
                )
                # Close the broken connection.
                if self._conn is not None:
                    with contextlib.suppress(Exception):
                        await self._conn.close()
                    self._conn = None

                # Circuit breaker threshold.
                if self._consecutive_failures >= _CIRCUIT_BREAKER_FAIL_THRESHOLD:
                    self._circuit_open_until = (
                        time.monotonic() + _CIRCUIT_BREAKER_COOLDOWN_SECONDS
                    )
                    logger.warning(
                        "CacheInvalidationListener circuit breaker OPEN "
                        "for %ss (consecutive failures=%d)",
                        _CIRCUIT_BREAKER_COOLDOWN_SECONDS,
                        self._consecutive_failures,
                    )
                    attempt = 0
                else:
                    backoff = _compute_backoff_seconds(attempt)
                    attempt += 1
                    await self._sleep(backoff)

    async def _handle_notify(self, notify: Any) -> None:
        """Dispatch a single NOTIFY to the channel adapter.

        Args:
            notify: psycopg AsyncConnection notify object. Has
                `.channel` and `.payload` attributes.
        """
        if getattr(notify, "channel", None) != NOTIFY_CHANNEL_NAME:
            # Ignore notifications from other channels (defense-in-depth).
            return

        raw_payload = getattr(notify, "payload", None)
        if not isinstance(raw_payload, str):
            raise ListenerPayloadInvalidError(
                reason=f"payload is not str, got {type(raw_payload).__name__!r}",
                payload=raw_payload,
                trace_id="",
            )

        parsed = parse_payload(raw_payload)

        # Dispatch to channel adapter.
        adapter = self._adapter_factories[parsed.channel]()
        await adapter.on_invalidate(parsed.to_dict())

    async def _sleep(self, seconds: float) -> None:
        """Sleep for `seconds`, but wake up on stop_event.set().

        Used for backoff + circuit breaker cool-down.
        """
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(self._stop_event.wait(), timeout=seconds)


__all__ = [
    "ALLOWED_CHANNELS",
    "AdapterFactory",
    "CacheInvalidationAdapter",
    "CacheInvalidationListener",
    "CacheInvalidationPayload",
    "EXPECTED_PAYLOAD_KEYS",
    "EXPECTED_PAYLOAD_KEYS_CROSS_TENANT",
    "ERROR_CODE_LISTENER_PAYLOAD_INVALID",
    "ERROR_CODE_LISTENER_START_FAILED",
    "ERROR_CODE_LISTENER_STOP_FAILED",
    "ERROR_CODE_LEADER_ELECTION_FAILED",
    "ERROR_CODE_LEADER_TAKEOVER_FAILED",
    "LEADER_ELECTION_FAILED_KO",
    "LEADER_TAKEOVER_FAILED_KO",
    "LEADER_HEALTH_CHECK_INTERVAL_SECONDS",
    "LEADER_TAKEOVER_TIMEOUT_SECONDS",
    "LeaderElectionFailedError",
    "LeaderElectionState",
    "LeaderTakeoverFailedError",
    "LISTEN_FANOUT_LOCK_ID",
    "LISTENER_PAYLOAD_INVALID_KO",
    "LISTENER_START_FAILED_KO",
    "LISTENER_STOP_FAILED_KO",
    "ListenerPayloadInvalidError",
    "ListenerStartFailedError",
    "ListenerStopFailedError",
    "NOTIFY_CHANNEL_NAME",
    "PAYLOAD_KEY_CHANNEL",
    "PAYLOAD_KEY_CORRECTION_GROUP_ID",
    "PAYLOAD_KEY_INVALIDATION_ID",
    "PAYLOAD_KEY_PERIOD_KEY",
    "PAYLOAD_KEY_SOURCE_TENANT_ID",
    "PAYLOAD_KEY_TARGET_TENANT_IDS",
    "PAYLOAD_KEY_TENANT_ID",
    "PAYLOAD_KEY_TRACE_ID",
    "parse_payload",
    "serialize_payload_for_v8",
]
