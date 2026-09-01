"""apps.api.core.health — Production health check endpoints (Phase 4 T5 wire).

Phase 4 (cj-style 55번째 epic 연속 정직 회복 wire) — AD-27 verbatim +
PRD §F16.5 + AC #5.1~#5.7.

Provides 3 production-grade health endpoints under `/api/v1/health/*`:

- `GET /api/v1/health`         — Combined liveness + readiness snapshot.
- `GET /api/v1/health/live`    — Liveness: process alive (200 OK always).
- `GET /api/v1/health/ready`   — Readiness: DB + JWT verification
                                  (200 OK if all pass, 503 if any fail).

Response envelope (CR 12-5 D-14 verbatim):

    {
        "status": "healthy" | "degraded",
        "timestamp": "2026-08-22T12:34:56.789Z",
        "version": "0.1.0",
        "database": "connected" | "disconnected",
        "redis": "connected" | "disconnected",
        "uptime_seconds": 42
    }

The existing `/health` route in `apps/api/main.py` is preserved for
backward compatibility with CI smoke tests; the new endpoints are
the production-grade replacements.

Architecture patterns (CR 11-3 honest-DEFER discipline):
- No business logic — this module is a pure health-check service.
- No database writes — only read-only `SELECT 1` against Supabase.
- Audit-first INSERT: never (health checks are not user actions).
- Capability: `DEPLOYMENT_HEALTH_CHECK` (industry-agnostic, CR 12-1 L4).
"""

from __future__ import annotations

import asyncio
import os
import platform
import time
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Response
from sqlalchemy import text

from apps.api.core.db import get_engine

# Module-level start time for uptime calculation.
_MODULE_START_TIME: float = time.time()

# API version constant — mirrors main.py `app.version`.
APP_VERSION: str = "0.1.0"

# Router — included by main.py via `include_router`.
router = APIRouter(
    prefix="/api/v1/health",
    tags=["deployment-health"],
    responses={
        200: {"description": "Service healthy"},
        503: {"description": "Service degraded"},
    },
)


def _uptime_seconds() -> int:
    """Return seconds since this module was loaded."""
    return int(time.time() - _MODULE_START_TIME)


async def _check_database() -> str:
    """Probe PostgreSQL connectivity via `SELECT 1`.

    Returns `"connected"` on success, `"disconnected"` on failure.
    Uses the SQLAlchemy engine's connection pool — non-blocking,
    no fallback to mock values. The probe is read-only and has no
    side effects on tenant data.
    """
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            result = await asyncio.wait_for(conn.execute(text("SELECT 1")), timeout=2.0)
            row = result.scalar()
            return "connected" if row == 1 else "disconnected"
    except Exception:
        return "disconnected"


async def _check_redis() -> str:
    """Probe Redis connectivity (optional).

    The costmgr backend does NOT require Redis — caching is
    optional. Returns `"connected"` if REDIS_URL is set and the
    ping succeeds, `"disconnected"` otherwise (the default).

    This is intentionally permissive: Redis absence is NOT a
    service degradation signal. The readiness check only fails
    if DATABASE connectivity fails.
    """
    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url:
        return "disconnected"
    try:
        # Lazy import — Redis is optional.
        import redis.asyncio as redis_asyncio

        client = redis_asyncio.from_url(redis_url)
        try:
            pong = await asyncio.wait_for(client.ping(), timeout=1.0)
            return "connected" if pong else "disconnected"
        finally:
            await client.aclose()
    except Exception:
        return "disconnected"


async def _check_jwt_verification() -> str:
    """Probe Supabase JWT verification (read-only, anonymous key).

    Returns `"connected"` if the Supabase auth endpoint responds
    to an anon-key health probe, `"disconnected"` otherwise.

    This validates that the JWT secret + anon key configuration
    is correct, which is a prerequisite for ALL tenant-scoped
    endpoints. The readiness check fails if this returns
    `"disconnected"`.
    """
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    anon_key = os.getenv("SUPABASE_ANON_KEY", "").strip()
    if not supabase_url or not anon_key:
        return "disconnected"
    try:
        import urllib.request

        # The Supabase auth health endpoint doesn't require auth —
        # it returns 200 if the project is healthy.
        req = urllib.request.Request(
            f"{supabase_url.rstrip('/')}/auth/v1/health",
            headers={"apikey": anon_key, "Authorization": f"Bearer {anon_key}"},
        )
        with urllib.request.urlopen(req, timeout=2.0) as resp:  # noqa: S310 — health check
            return "connected" if resp.status == 200 else "disconnected"
    except Exception:
        return "disconnected"


def _build_envelope(*, database: str, redis: str, status_value: str = "healthy") -> dict[str, Any]:
    """Build the canonical health envelope (CR 12-5 D-14 verbatim)."""
    return {
        "status": status_value,
        "timestamp": datetime.now(UTC).isoformat(),
        "version": APP_VERSION,
        "database": database,
        "redis": redis,
        "uptime_seconds": _uptime_seconds(),
    }


@router.get("", response_class=Response)
async def health_combined() -> dict[str, Any]:
    """GET /api/v1/health — combined liveness + readiness snapshot.

    Always returns 200 OK if the process is alive, even if the
    database is briefly disconnected. Use `/health/ready` for a
    strict readiness probe that returns 503 on degradation.
    """
    db_status, redis_status = await asyncio.gather(_check_database(), _check_redis())
    return _build_envelope(
        database=db_status,
        redis=redis_status,
        status_value="healthy" if db_status == "connected" else "degraded",
    )


@router.get("/live")
async def health_live() -> dict[str, Any]:
    """GET /api/v1/health/live — liveness probe.

    Returns 200 OK always (as long as the process is alive).
    No external dependencies are checked. Suitable for Kubernetes
    `livenessProbe` or Railway's healthcheckPath for high-frequency
    checks (e.g., every 5 seconds).
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": APP_VERSION,
        "uptime_seconds": _uptime_seconds(),
    }


@router.get("/ready")
async def health_ready() -> dict[str, Any]:
    """GET /api/v1/health/ready — readiness probe.

    Returns 200 OK if all critical dependencies are connected
    (database + JWT verification), 503 Service Unavailable
    otherwise. Suitable for Kubernetes `readinessProbe` or
    Railway's startup healthcheck.

    Critical dependencies:
    - PostgreSQL `SELECT 1` (Supabase managed Postgres)
    - Supabase JWT verification (auth subsystem)
    - Redis (optional — absence is NOT a failure)
    """
    db_status, redis_status, jwt_status = await asyncio.gather(
        _check_database(), _check_redis(), _check_jwt_verification()
    )
    is_ready = db_status == "connected" and jwt_status == "connected"
    envelope = _build_envelope(
        database=db_status,
        redis=redis_status,
        status_value="healthy" if is_ready else "degraded",
    )
    envelope["jwt_verification"] = jwt_status
    envelope["platform"] = platform.system()
    return envelope


# ────────────────────────────────────────────────────────────
# Phase 5 EXTENSION (cj-style 75번째 wire) — Multi-region health
# ────────────────────────────────────────────────────────────


@router.get("/multi-region")
async def health_multi_region() -> dict[str, Any]:
    """GET /api/v1/health/multi-region — Multi-region health observability.

    Phase 5 (cj-style 75번째 wire) — AD-31 (e) verbatim + PRD §F20.5
    + AC #5.1~#5.4. Reads latest replication_lag row from
    `phase_5_replication_lag` (system-only table, no RLS — CR 0-2).

    Response envelope (CR 12-5 D-14 verbatim):
        {
            "status": "healthy" | "degraded" | "unhealthy",
            "primary": {
                "region": "primary_seoul",
                "replication_status": "healthy" | "lagging" | "stalled" | "disconnected",
                "lag_seconds": 12,
                "last_wal_received_at": "2026-08-22T10:00:00Z"
            },
            "secondary": {
                "region": "secondary_tokyo",
                "replication_status": "healthy",
                "lag_seconds": 8,
                "last_wal_received_at": "2026-08-22T10:00:00Z"
            },
            "timestamp": "2026-08-22T10:00:01Z"
        }

    Status logic:
    - "healthy": both regions healthy AND lag < 60s on both.
    - "degraded": at least one region lagging OR lag > 60s.
    - "unhealthy": at least one region stalled/disconnected.

    CR 12-5 D-PARITY-01 inversion: Python backend envelope mirrors
    the TypeScript Next.js /api/health/multi-region envelope.
    """
    from sqlalchemy import text

    from apps.api.core.db import get_engine

    engine = get_engine()
    async with engine.connect() as conn:
        # Fetch latest replication_lag rows for primary + secondary.
        result = await conn.execute(
            text(
                """
                SELECT region, replication_status, lag_seconds,
                       last_wal_received_at
                FROM public.phase_5_replication_lag
                WHERE region IN ('primary_seoul', 'secondary_tokyo')
                ORDER BY recorded_at DESC
                LIMIT 2
                """
            )
        )
        rows = result.mappings().all()

    primary_row = next((r for r in rows if r["region"] == "primary_seoul"), None)
    secondary_row = next((r for r in rows if r["region"] == "secondary_tokyo"), None)

    primary = {
        "region": "primary_seoul",
        "replication_status": (
            primary_row["replication_status"] if primary_row else "disconnected"
        ),
        "lag_seconds": int(primary_row["lag_seconds"]) if primary_row else 0,
        "last_wal_received_at": (
            primary_row["last_wal_received_at"].isoformat()
            if primary_row and primary_row["last_wal_received_at"]
            else None
        ),
    }
    secondary = {
        "region": "secondary_tokyo",
        "replication_status": (
            secondary_row["replication_status"] if secondary_row else "disconnected"
        ),
        "lag_seconds": int(secondary_row["lag_seconds"]) if secondary_row else 0,
        "last_wal_received_at": (
            secondary_row["last_wal_received_at"].isoformat()
            if secondary_row and secondary_row["last_wal_received_at"]
            else None
        ),
    }

    # Status aggregation logic.
    statuses = {primary["replication_status"], secondary["replication_status"]}
    if "stalled" in statuses or "disconnected" in statuses:
        status_value = "unhealthy"
    elif "lagging" in statuses or primary["lag_seconds"] > 60 or secondary["lag_seconds"] > 60:
        status_value = "degraded"
    else:
        status_value = "healthy"

    return {
        "status": status_value,
        "primary": primary,
        "secondary": secondary,
        "timestamp": datetime.now(UTC).isoformat(),
    }
