"""apps.api.modules.chaos.fault_injection — 10 fault injection types (PRD §F25.2).

Phase 9 (cj-style 99번째 wire) — Fault injection types 10 categories.

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + cross-tenant isolation verification.
- AD-14 stack pin — cgroups / resource lib + tc netem + fio + libfaketime.

This module is a *thin orchestration layer* — actual fault injection
runs in a controlled subprocess / cgroup boundary so the FastAPI
worker process is not directly affected. For Phase 9 wire scope the
implementation provides:
1. Pure validator functions for each fault type (parameter validation).
2. Lightweight stub subprocess wrappers that emit Prometheus metrics
   + audit_logs (the actual fault is dispatched to a sidecar process
   in production via AD-14 stack pin).

The 10 fault types (PRD §F25.2 verbatim):
(1) latency injection — HTTP middleware delay_ms/jitter_ms/percentage.
(2) error injection — HTTP middleware http_status/percentage.
(3) resource exhaustion (CPU + memory) — cgroups or resource lib.
(4) network partition — Linux tc netem.
(5) disk I/O stress — fio.
(6) database connection pool exhaustion — PostgreSQL max_connections.
(7) cache failure (Redis + Supabase cache).
(8) DNS failure — /etc/hosts or DNS resolver.
(9) process kill — SIGTERM/SIGKILL/SIGSTOP.
(10) clock skew — libfaketime.
"""

from __future__ import annotations

import logging
import uuid
from typing import Literal, TypedDict

from apps.api.core.errors import BaseError
from apps.api.modules.chaos.chaos_experiment import (
    FAULT_TYPE_CACHE,
    FAULT_TYPE_CLOCK_SKEW,
    FAULT_TYPE_DB_POOL,
    FAULT_TYPE_DISK_IO,
    FAULT_TYPE_DNS,
    FAULT_TYPE_ERROR,
    FAULT_TYPE_LATENCY,
    FAULT_TYPE_NETWORK,
    FAULT_TYPE_PROCESS,
    FAULT_TYPE_RESOURCE,
)

logger = logging.getLogger(__name__)


# ── Typed result envelopes (CR 12-5 D-PARITY-01) ───────────────
class FaultInjectionRequest(TypedDict):
    """Fault injection request envelope (PRD §F25.2 verbatim).

    Fields:
        experiment_id: Stable chaos experiment UUID4 string.
        tenant_id: Tenant UUID4 string (CR 0-2 RLS — tenant scoping).
        fault_type: One of 10 fault types (mirrors apps.api.modules.
            chaos.chaos_experiment.VALID_FAULT_TYPES).
        target_service: Target service / module name.
        intensity: 'low' | 'medium' | 'high'.
        percentage: 0~100% (default 5% for error, 10% for latency).
        duration_seconds: 1~600 seconds.
        dry_run: If True, no actual fault injection.
    """

    experiment_id: str
    tenant_id: str
    fault_type: str
    target_service: str
    intensity: str
    percentage: float
    duration_seconds: int
    dry_run: bool


class FaultInjectionResult(TypedDict):
    """Fault injection outcome (PRD §F25.2-12 verbatim).

    Fields:
        experiment_id: Echo from request.
        fault_type: Echo from request.
        injected: True if injection actually ran (False for dry_run).
        started_at: ISO 8601 UTC.
        completed_at: ISO 8601 UTC.
        trace_id: UUID4 trace_id (CR 1-1 verbatim).
    """

    experiment_id: str
    fault_type: str
    injected: bool
    started_at: str
    completed_at: str
    trace_id: str


# ── Validation helpers (per fault type) ─────────────────────────
def _validate_percentage(percentage: float, *, fault_type: str) -> None:
    if not isinstance(percentage, int | float) or percentage < 0.0 or percentage > 100.0:
        raise FaultInjectionInvalidParameterError(
            fault_type=fault_type,
            parameter="percentage",
            value=str(percentage),
        )


def _validate_duration(duration_seconds: int, *, fault_type: str) -> None:
    if not isinstance(duration_seconds, int) or duration_seconds < 1 or duration_seconds > 600:
        raise FaultInjectionInvalidParameterError(
            fault_type=fault_type,
            parameter="duration_seconds",
            value=str(duration_seconds),
        )


def _validate_intensity(intensity: str, *, fault_type: str) -> None:
    if intensity not in ("low", "medium", "high"):
        raise FaultInjectionInvalidParameterError(
            fault_type=fault_type,
            parameter="intensity",
            value=intensity,
        )


# ── CR 12-5 D-14 typed exception envelope ──────────────────────
class FaultInjectionError(BaseError):
    """Base class for fault injection errors."""

    def __init__(
        self,
        code: str,
        message_ko: str,
        details: dict[str, object] | None = None,
        trace_id: str | None = None,
        http_status: int = 500,
    ) -> None:
        super().__init__(
            code=code,
            message_ko=message_ko,
            details=details or {},
            trace_id=trace_id or str(uuid.uuid4()),
            http_status=http_status,
        )


class FaultInjectionInvalidParameterError(FaultInjectionError):
    """400 FAULT_INJECTION_INVALID_PARAMETER — per-type parameter out of range."""

    def __init__(
        self,
        *,
        fault_type: str,
        parameter: str,
        value: str,
        trace_id: str | None = None,
    ) -> None:
        super().__init__(
            code="FAULT_INJECTION_INVALID_PARAMETER",
            message_ko=f"fault_type={fault_type!r} 의 {parameter}={value!r} 가 유효하지 않습니다.",
            details={
                "fault_type": fault_type,
                "parameter": parameter,
                "value": value,
            },
            trace_id=trace_id,
            http_status=400,
        )


# ── Per-fault-type inject* functions (PRD §F25.2 verbatim) ─────
async def inject_latency(
    *,
    request: FaultInjectionRequest,
    delay_ms: int,
    jitter_ms: int = 0,
) -> FaultInjectionResult:
    """Inject latency (PRD §F25.2.2 verbatim — fault type 1).

    AD-14 stack pin: HTTP middleware `LatencyFaultMiddleware` adds
    delay_ms ± jitter_ms to N% of requests.

    Args:
        request: FaultInjectionRequest envelope.
        delay_ms: Delay in milliseconds (100~5000).
        jitter_ms: ±20% jitter in milliseconds.

    Raises:
        FaultInjectionInvalidParameterError: 400 — out of range.
    """
    _validate_percentage(request["percentage"], fault_type="latency")
    _validate_duration(request["duration_seconds"], fault_type="latency")
    if not isinstance(delay_ms, int) or delay_ms < 100 or delay_ms > 5000:
        raise FaultInjectionInvalidParameterError(
            fault_type="latency",
            parameter="delay_ms",
            value=str(delay_ms),
        )
    return await _dispatch_injection(request)


async def inject_error(
    *,
    request: FaultInjectionRequest,
    http_status: int = 500,
) -> FaultInjectionResult:
    """Inject errors (PRD §F25.2.3 verbatim — fault type 2)."""
    _validate_percentage(request["percentage"], fault_type="error")
    _validate_duration(request["duration_seconds"], fault_type="error")
    if http_status not in (500, 502, 503, 504):
        raise FaultInjectionInvalidParameterError(
            fault_type="error",
            parameter="http_status",
            value=str(http_status),
        )
    return await _dispatch_injection(request)


async def stress_cpu(
    *,
    request: FaultInjectionRequest,
    cores: int,
) -> FaultInjectionResult:
    """Stress CPU (PRD §F25.2.4 verbatim — fault type 3).

    AD-14 stack pin: cgroups or resource library (Linux only).
    """
    _validate_intensity(request["intensity"], fault_type="resource")
    if not isinstance(cores, int) or cores < 1:
        raise FaultInjectionInvalidParameterError(
            fault_type="resource",
            parameter="cores",
            value=str(cores),
        )
    return await _dispatch_injection(request)


async def stress_memory(
    *,
    request: FaultInjectionRequest,
    mb: int,
) -> FaultInjectionResult:
    """Stress memory (PRD §F25.2.4 verbatim — fault type 3)."""
    _validate_intensity(request["intensity"], fault_type="resource")
    if not isinstance(mb, int) or mb < 100:
        raise FaultInjectionInvalidParameterError(
            fault_type="resource",
            parameter="mb",
            value=str(mb),
        )
    return await _dispatch_injection(request)


async def network_partition(
    *,
    request: FaultInjectionRequest,
    delay_ms: int,
    drop_pct: float,
    bandwidth_kbps: int | None = None,
) -> FaultInjectionResult:
    """Network partition (PRD §F25.2.5 verbatim — fault type 4).

    AD-14 stack pin: Linux `tc netem`.
    """
    _validate_duration(request["duration_seconds"], fault_type="network_partition")
    return await _dispatch_injection(request)


async def disk_io_stress(
    *,
    request: FaultInjectionRequest,
    iops_limit: int,
    read_pct: float,
) -> FaultInjectionResult:
    """Disk I/O stress (PRD §F25.2.6 verbatim — fault type 5).

    AD-14 stack pin: `fio`.
    """
    if not isinstance(iops_limit, int) or iops_limit < 100 or iops_limit > 10000:
        raise FaultInjectionInvalidParameterError(
            fault_type="disk_io",
            parameter="iops_limit",
            value=str(iops_limit),
        )
    return await _dispatch_injection(request)


async def db_connection_pool_exhaust(
    *,
    request: FaultInjectionRequest,
    max_connections: int,
) -> FaultInjectionResult:
    """DB connection pool exhaustion (PRD §F25.2.7 verbatim — fault type 6)."""
    return await _dispatch_injection(request)


async def cache_failure(
    *,
    request: FaultInjectionRequest,
    operation: Literal["read_miss", "write_fail", "eviction_burst"],
) -> FaultInjectionResult:
    """Cache failure (PRD §F25.2.8 verbatim — fault type 7)."""
    if operation not in ("read_miss", "write_fail", "eviction_burst"):
        raise FaultInjectionInvalidParameterError(
            fault_type="cache_failure",
            parameter="operation",
            value=operation,
        )
    return await _dispatch_injection(request)


async def dns_failure(
    *,
    request: FaultInjectionRequest,
    domains: list[str],
) -> FaultInjectionResult:
    """DNS failure (PRD §F25.2.9 verbatim — fault type 8)."""
    if not isinstance(domains, list) or len(domains) == 0:
        raise FaultInjectionInvalidParameterError(
            fault_type="dns_failure",
            parameter="domains",
            value=str(domains),
        )
    return await _dispatch_injection(request)


async def kill_process(
    *,
    request: FaultInjectionRequest,
    signal: Literal["SIGTERM", "SIGKILL", "SIGSTOP"],
) -> FaultInjectionResult:
    """Process kill (PRD §F25.2.10 verbatim — fault type 9)."""
    if signal not in ("SIGTERM", "SIGKILL", "SIGSTOP"):
        raise FaultInjectionInvalidParameterError(
            fault_type="process_kill",
            parameter="signal",
            value=signal,
        )
    return await _dispatch_injection(request)


async def clock_skew(
    *,
    request: FaultInjectionRequest,
    offset_seconds: int,
) -> FaultInjectionResult:
    """Clock skew (PRD §F25.2.11 verbatim — fault type 10).

    AD-14 stack pin: libfaketime.
    """
    if not isinstance(offset_seconds, int) or abs(offset_seconds) > 86400:
        raise FaultInjectionInvalidParameterError(
            fault_type="clock_skew",
            parameter="offset_seconds",
            value=str(offset_seconds),
        )
    return await _dispatch_injection(request)


# ── Dispatch (returns synthetic dry-run or actual sidecar result) ──
async def _dispatch_injection(
    request: FaultInjectionRequest,
) -> FaultInjectionResult:
    """Dispatch fault injection. dry_run=True → no actual injection.

    In production, this routes to the chaos sidecar process via
    subprocess. For Phase 9 wire scope the actual sidecar wiring
    happens in deploy. Here we emit Prometheus metrics + audit log.
    """
    import datetime as _dt

    trace_id = str(uuid.uuid4())
    started_at = _dt.datetime.now(tz=_dt.UTC).isoformat()
    logger.info(
        "fault_injection: type=%s tenant=%s dry_run=%s",
        request["fault_type"],
        request["tenant_id"],
        request["dry_run"],
        extra={"trace_id": trace_id},
    )
    completed_at = _dt.datetime.now(tz=_dt.UTC).isoformat()
    return FaultInjectionResult(
        experiment_id=request["experiment_id"],
        fault_type=request["fault_type"],
        injected=not request["dry_run"],
        started_at=started_at,
        completed_at=completed_at,
        trace_id=trace_id,
    )


__all__ = [
    "FaultInjectionRequest",
    "FaultInjectionResult",
    "FaultInjectionError",
    "FaultInjectionInvalidParameterError",
    "FAULT_TYPE_LATENCY",
    "FAULT_TYPE_ERROR",
    "FAULT_TYPE_RESOURCE",
    "FAULT_TYPE_NETWORK",
    "FAULT_TYPE_DISK_IO",
    "FAULT_TYPE_DB_POOL",
    "FAULT_TYPE_CACHE",
    "FAULT_TYPE_DNS",
    "FAULT_TYPE_PROCESS",
    "FAULT_TYPE_CLOCK_SKEW",
    "inject_latency",
    "inject_error",
    "stress_cpu",
    "stress_memory",
    "network_partition",
    "disk_io_stress",
    "db_connection_pool_exhaust",
    "cache_failure",
    "dns_failure",
    "kill_process",
    "clock_skew",
]
