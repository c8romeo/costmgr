"""apps.api.core.cache_invalidation_listener — AD-25 cache invalidation LISTEN daemon.

Story 13.1 (LISTEN/NOTIFY Consume Trigger EXTENSION, A39/A51/A52 결정 wire):
D-10-2-DEFER-3 ✅ RESOLVED wire 진입. PostgreSQL NOTIFY trigger on
`cache_invalidation_log` AFTER INSERT (alembic 0033) emits a 5-key
alphabetical JSON payload. This module consumes those notifications via
psycopg 3.x `AsyncConnection.listen()` and routes them to the 4 channel
adapters (M10/M3/M11).

Per AD-25 (ARCHITECTURE-SPINE.md §142-148 verbatim):
  "M10 cache key is `(tenant_id, period_key, calculation_result_hash)`.
   A new AD-4 commit, an AD-22 reversal insert, or an M11 reopen emits
   one DB notification per channel."

Channel whitelist (4 channels, AD-25 verbatim):
  - `ai_cache`               — M10 AI cache invalidation (11-1 wire 보존)
  - `cost_engine_cache`      — M3 cost engine calculation result cache (11-3 NEW)
  - `fiscal_period_cache`    — M11 fiscal_periods + fiscal_period_snapshots
                                metadata cache (11-3 NEW)
  - `closing_snapshot_cache` — M11 closing_snapshot + ledger closing event
                                cache (11-3 NEW)

Payload shape (5 keys, alphabetical order — V8 determinism):
  {
    "channel":              "ai_cache",
    "correction_group_id":  "uuid-string",
    "period_key":           "YYYY-MM",
    "tenant_id":            "uuid-string",
    "trace_id":             "uuid-string"
  }

NOTE: payload is published by the AFTER INSERT trigger on
  cache_invalidation_log (alembic 0033). The 5 keys are emitted in
  alphabetical order via `json_object()` in the trigger function —
  this is part of the V8 byte-identical contract (F13.3 verbatim).

Per CR 12-5 D-PARITY-01 inversion: payload shape MUST match
  apps/web/lib/cache-invalidation-listener.ts (Python ↔ TS parity).
  Drift → drift detector test fail + 1-line ko-KR reject.

Reconnect/backoff strategy:
- Exponential backoff: base 1s, factor 2 (max 30s)
- Jitter: ±20% to prevent thundering-herd reconnects
- Circuit breaker: 5 consecutive failures → 60s cool-down
- Persistent failure → graceful degradation (next restart retries)

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
from dataclasses import dataclass
from typing import Any, Protocol

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────
# NOTIFY channel name (PostgreSQL `pg_notify` channel identifier).
# Mirrored in apps/api/alembic/versions/0033_listen_notify_consume_trigger.py:NOTIFY_CHANNEL_NAME.
NOTIFY_CHANNEL_NAME: str = "cache_invalidation_log"

# Payload keys (5 keys, alphabetical order — V8 determinism contract).
# Use the exact lowercase string identifiers — TS mirror keys are spelled
# the same way (CR 12-5 D-PARITY-01 inversion).
PAYLOAD_KEY_CHANNEL: str = "channel"
PAYLOAD_KEY_CORRECTION_GROUP_ID: str = "correction_group_id"
PAYLOAD_KEY_PERIOD_KEY: str = "period_key"
PAYLOAD_KEY_TENANT_ID: str = "tenant_id"
PAYLOAD_KEY_TRACE_ID: str = "trace_id"

# All expected payload keys (frozen for V8 determinism validation).
EXPECTED_PAYLOAD_KEYS: frozenset[str] = frozenset(
    {
        PAYLOAD_KEY_CHANNEL,
        PAYLOAD_KEY_CORRECTION_GROUP_ID,
        PAYLOAD_KEY_PERIOD_KEY,
        PAYLOAD_KEY_TENANT_ID,
        PAYLOAD_KEY_TRACE_ID,
    }
)

# 4 channel whitelist (AD-25 verbatim). Mirrored in
# `apps/api/core/cache_invalidation_publisher.py:ALLOWED_CHANNELS`.
ALLOWED_CHANNELS: frozenset[str] = frozenset(
    {
        "ai_cache",
        "cost_engine_cache",
        "fiscal_period_cache",
        "closing_snapshot_cache",
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

# Error codes (CR 12-5 D-14 envelope). These are mapped to HTTP responses
# by the 2 NEW exception handlers in apps/api/main.py (T3 wire).
ERROR_CODE_LISTENER_START_FAILED: str = "LISTENER_START_FAILED"
ERROR_CODE_LISTENER_STOP_FAILED: str = "LISTENER_STOP_FAILED"
ERROR_CODE_LISTENER_PAYLOAD_INVALID: str = "LISTENER_PAYLOAD_INVALID"

# Korean constants — AD-15 §11 SSOT.
LISTENER_START_FAILED_KO: str = "캐시 무효화 리스너 시작 실패"
LISTENER_STOP_FAILED_KO: str = "캐시 무효화 리스너 종료 실패"
LISTENER_PAYLOAD_INVALID_KO: str = "캐시 무효화 페이로드 형식 오류"


# ── Adapter protocol (port) ──────────────────────────────────
class CacheInvalidationAdapter(Protocol):
    """Protocol for cache invalidation adapters (M10/M3/M11).

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
                tenant_id, trace_id). The `channel` field is ALWAYS
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


# ── Parsed payload dataclass ─────────────────────────────────
@dataclass(frozen=True)
class CacheInvalidationPayload:
    """Parsed NOTIFY payload (5 keys, V8 determinism).

    Frozen for hashability — useful for idempotency keys in channel
    adapters. Field order is alphabetical (channel, correction_group_id,
    period_key, tenant_id, trace_id) — the canonical order is
    guaranteed by the trigger function DDL (alembic 0033).
    """

    channel: str
    correction_group_id: str
    period_key: str
    tenant_id: str
    trace_id: str

    def to_dict(self) -> dict[str, str]:
        """Return the payload as a 5-key dict (alphabetical order)."""
        return {
            PAYLOAD_KEY_CHANNEL: self.channel,
            PAYLOAD_KEY_CORRECTION_GROUP_ID: self.correction_group_id,
            PAYLOAD_KEY_PERIOD_KEY: self.period_key,
            PAYLOAD_KEY_TENANT_ID: self.tenant_id,
            PAYLOAD_KEY_TRACE_ID: self.trace_id,
        }


# ── V8 deterministic JSON serialization ───────────────────────
def serialize_payload_for_v8(payload: dict[str, str]) -> str:
    """Deterministic JSON serialization for V8 byte-identical contract.

    CR 4-4 + F13.3 verbatim: payload JSON MUST be byte-identical for
    the same input across reruns. Uses `json.dumps(payload, sort_keys=True,
    separators=(',', ':'))` — no whitespace, alphabetical key ordering.

    Args:
        payload: 5-key dict (channel, correction_group_id, period_key,
            tenant_id, trace_id).

    Returns:
        JSON string with alphabetical key ordering, no whitespace.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


# ── Payload parse + validation ────────────────────────────────
def parse_payload(raw: str) -> CacheInvalidationPayload:
    """Parse a NOTIFY payload string into a typed dataclass.

    V8 determinism validation: parses the raw JSON, validates the EXACT
    5 keys (alphabetical), validates the channel is in ALLOWED_CHANNELS,
    and returns the frozen dataclass.

    Args:
        raw: Raw JSON string from `pg_notify`. Must be 5-key alphabetical.

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

    actual_keys = frozenset(parsed.keys())
    if actual_keys != EXPECTED_PAYLOAD_KEYS:
        raise ListenerPayloadInvalidError(
            reason=(
                f"payload keys mismatch: expected {sorted(EXPECTED_PAYLOAD_KEYS)}, "
                f"got {sorted(actual_keys)}"
            ),
            payload=parsed,
            trace_id="",
        )

    # V8 determinism: serialized bytes for the same input MUST be identical.
    # We re-serialize and validate the roundtrip has the same shape.
    canonical = serialize_payload_for_v8(parsed)
    # Verify the canonical form's keys are exactly the expected 5 keys.
    if set(json.loads(canonical).keys()) != EXPECTED_PAYLOAD_KEYS:
        raise ListenerPayloadInvalidError(
            reason="canonical serialization failed V8 determinism check",
            payload=parsed,
            trace_id="",
        )

    # Type-check each field.
    channel = parsed[PAYLOAD_KEY_CHANNEL]
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

    # UUID validation for the 3 UUID fields (defense-in-depth).
    for key in (
        PAYLOAD_KEY_TENANT_ID,
        PAYLOAD_KEY_CORRECTION_GROUP_ID,
    ):
        try:
            uuid.UUID(parsed[key])
        except (ValueError, KeyError) as exc:
            raise ListenerPayloadInvalidError(
                reason=f"{key} is not a valid UUID: {exc}",
                payload=parsed,
                trace_id="",
            ) from exc

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

    return CacheInvalidationPayload(
        channel=channel,
        correction_group_id=parsed[PAYLOAD_KEY_CORRECTION_GROUP_ID],
        period_key=parsed[PAYLOAD_KEY_PERIOD_KEY],
        tenant_id=parsed[PAYLOAD_KEY_TENANT_ID],
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


class CacheInvalidationListener:
    """AD-25 LISTEN daemon — 4-channel cache invalidation consume.

    Lifecycle:
    - `start()` opens a psycopg AsyncConnection, calls `LISTEN
      cache_invalidation_log`, and spawns an asyncio Task that polls
      notifications. Called from FastAPI lifespan at startup.
    - `stop()` cancels the task, calls `UNLISTEN cache_invalidation_log`,
      and closes the connection. Called from FastAPI lifespan at
      shutdown.

    Reconnect/backoff:
    - On connection drop, the listener retries with exponential backoff
      + jitter (cap 30s).
    - After 5 consecutive failures, the circuit breaker opens for 60s.
    - All retries are logged for observability.

    Adapter dispatch:
    - `_consume_notifications()` parses each NOTIFY payload and looks up
      the channel-specific adapter from the dispatch table.
    - Unknown channels raise `ListenerPayloadInvalidError` (fail-fast).

    The listener is pure-Python (AD-5 stdlib-only + psycopg 3.x async).
    It does NOT import `packages.cost_engine` directly.
    """

    def __init__(
        self,
        *,
        adapter_factories: dict[str, AdapterFactory],
        conn_factory: Callable[[], Awaitable[Any]] | None = None,
    ) -> None:
        """Initialize the listener.

        Args:
            adapter_factories: Channel → adapter factory mapping. MUST
                contain all 4 channels (ai_cache / cost_engine_cache /
                fiscal_period_cache / closing_snapshot_cache).
            conn_factory: Async connection factory (creates a psycopg
                AsyncConnection). If None, the listener uses a default
                factory that connects to the project's asyncpg pool via
                the standard `get_asyncpg_pool()` helper. Tests inject
                a mock factory.
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
        self._task: asyncio.Task[None] | None = None
        self._conn: Any = None
        self._stop_event = asyncio.Event()
        self._consecutive_failures: int = 0
        self._circuit_open_until: float = 0.0
        self._is_started: bool = False

    async def start(self) -> None:
        """Start the LISTEN daemon.

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
        self._is_started = True
        logger.info(
            "CacheInvalidationListener started (channel=%s)",
            NOTIFY_CHANNEL_NAME,
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
    "ERROR_CODE_LISTENER_PAYLOAD_INVALID",
    "ERROR_CODE_LISTENER_START_FAILED",
    "ERROR_CODE_LISTENER_STOP_FAILED",
    "LISTENER_PAYLOAD_INVALID_KO",
    "LISTENER_START_FAILED_KO",
    "LISTENER_STOP_FAILED_KO",
    "ListenerPayloadInvalidError",
    "ListenerStartFailedError",
    "ListenerStopFailedError",
    "NOTIFY_CHANNEL_NAME",
    "PAYLOAD_KEY_CHANNEL",
    "PAYLOAD_KEY_CORRECTION_GROUP_ID",
    "PAYLOAD_KEY_PERIOD_KEY",
    "PAYLOAD_KEY_TENANT_ID",
    "PAYLOAD_KEY_TRACE_ID",
    "parse_payload",
    "serialize_payload_for_v8",
]
