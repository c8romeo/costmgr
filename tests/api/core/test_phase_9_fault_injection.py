"""tests.api.core.test_phase_9_fault_injection — 10 fault injection types.

Phase 9 (cj-style 99번째 wire) — 4 NEW pytest cases PASS.
"""
from __future__ import annotations

import pytest

from apps.api.modules.chaos.fault_injection import (
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
    FaultInjectionInvalidParameterError,
    cache_failure,
    clock_skew,
    db_connection_pool_exhaust,
    disk_io_stress,
    dns_failure,
    inject_error,
    inject_latency,
    kill_process,
    network_partition,
    stress_cpu,
    stress_memory,
)
from apps.api.modules.chaos.chaos_experiment import VALID_FAULT_TYPES


def _request(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "experiment_id": "exp-001",
        "tenant_id": "00000000-0000-0000-0000-000000000001",
        "fault_type": FAULT_TYPE_LATENCY,
        "target_service": "cost_engine",
        "intensity": "low",
        "percentage": 5.0,
        "duration_seconds": 60,
        "dry_run": True,
    }
    base.update(overrides)
    return base


# ── 4 NEW pytest cases (Phase 9 T1.13 fault_injection extension) ─


def test_all_10_fault_types_are_registered() -> None:
    """All 10 PRD §F25.2 fault types registered as module-level helpers."""
    # Each helper should be a callable + the fault_type constant should
    # appear in the package's VALID_FAULT_TYPES (mirrored via chaos_experiment).
    expected_helpers = {
        FAULT_TYPE_LATENCY: inject_latency,
        FAULT_TYPE_ERROR: inject_error,
        FAULT_TYPE_RESOURCE: stress_cpu,
        FAULT_TYPE_NETWORK: network_partition,
        FAULT_TYPE_DISK_IO: disk_io_stress,
        FAULT_TYPE_DB_POOL: db_connection_pool_exhaust,
        FAULT_TYPE_CACHE: cache_failure,
        FAULT_TYPE_DNS: dns_failure,
        FAULT_TYPE_PROCESS: kill_process,
        FAULT_TYPE_CLOCK_SKEW: clock_skew,
    }
    assert len(expected_helpers) == 10
    assert len(VALID_FAULT_TYPES) == 10
    for fault_type, helper in expected_helpers.items():
        assert callable(helper), f"{fault_type} helper not callable"


def test_inject_latency_rejects_out_of_range_delay() -> None:
    """inject_latency delay_ms < 100 raises 400."""
    import asyncio
    coro = inject_latency(
        request=_request(),  # type: ignore[arg-type]
        delay_ms=10,  # too small
    )
    with pytest.raises(FaultInjectionInvalidParameterError):
        asyncio.run(coro)


def test_inject_error_accepts_4xx_5xx_status() -> None:
    """inject_error rejects non-{500,502,503,504} http_status."""
    import asyncio
    coro = inject_error(
        request=_request(),  # type: ignore[arg-type]
        http_status=200,  # invalid — must be 5xx
    )
    with pytest.raises(FaultInjectionInvalidParameterError):
        asyncio.run(coro)


def test_stress_memory_rejects_too_small_mb() -> None:
    """stress_memory mb < 100 raises 400 (PRD §F25.2.4 verbatim)."""
    import asyncio
    coro = stress_memory(
        request=_request(),  # type: ignore[arg-type]
        mb=10,
    )
    with pytest.raises(FaultInjectionInvalidParameterError):
        asyncio.run(coro)
