"""apps.api.core.observability — Sentry FastAPI integration (Phase 4 T5 wire).

Phase 4 (cj-style 55번째 epic 연속 정직 회복 wire) — AD-27 verbatim +
PRD §F16.5 + AC #5.4.

Provides Sentry server-side initialization for the FastAPI backend
deployed on Railway. Pairs with `apps/web/lib/observability/sentry.ts`
(browser Sentry) for full-stack observability.

Architecture patterns (CR 11-3 honest-DEFER discipline):
- Optional integration: if `SENTRY_DSN` is not set, the module is
  a no-op (returns early). No hard dependency on Sentry at runtime.
- No tenant data leak: Sentry breadcrumbs are scrubbed of request
  bodies (only metadata + path + method are captured).
- Fail-closed: if Sentry init fails, the module logs but does not
  raise — the application must still start.

Capability gate: `DEPLOYMENT_HEALTH_CHECK` (industry-agnostic).
"""

from __future__ import annotations

import logging
import os
from typing import Any

_LOGGER = logging.getLogger(__name__)

# Module-level flags — set once by `init_sentry()`.
_SENTRY_INITIALIZED: bool = False


def _is_sentry_dsn_set() -> bool:
    """Return True if `SENTRY_DSN` env var is non-empty."""
    return bool(os.getenv("SENTRY_DSN", "").strip())


def init_sentry(*, app: Any = None) -> bool:
    """Initialize Sentry for the FastAPI backend.

    Behavior:
    - If `SENTRY_DSN` is unset → returns False, no-op.
    - If `sentry_sdk` import fails → returns False, logs warning.
    - If `app` is provided → installs FastAPI integration +
      SQLAlchemy integration (DB query tracing).
    - `traces_sample_rate=0.1` (10% of requests).
    - `environment` is read from `ENVIRONMENT` env var
      (defaults to `"development"`).

    Returns True on successful init, False otherwise.
    Never raises — observability is opt-in.
    """
    global _SENTRY_INITIALIZED
    if _SENTRY_INITIALIZED:
        return True
    if not _is_sentry_dsn_set():
        _LOGGER.info("Sentry DSN not set — skipping init (no-op)")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
    except ImportError as exc:
        _LOGGER.warning(
            "sentry-sdk not installed — skipping init: %s", exc
        )
        return False

    dsn = os.getenv("SENTRY_DSN", "").strip()
    environment = os.getenv("ENVIRONMENT", "development").strip()

    try:
        integrations = [
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ]
        # SQLAlchemy integration is opt-in — only enable if DB is
        # configured. Avoids noisy DB query traces in tests.
        if os.getenv("DATABASE_URL", "").strip():
            integrations.append(SqlalchemyIntegration())

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=0.1,
            integrations=integrations,
            # Don't send PII by default — request bodies are scrubbed.
            send_default_pii=False,
            # Lower the breadcrumb level for noisy INFO logs.
            max_breadcrumbs=50,
        )
        _SENTRY_INITIALIZED = True
        _LOGGER.info(
            "Sentry initialized (environment=%s, traces_sample_rate=0.1)",
            environment,
        )
        return True
    except Exception as exc:  # noqa: BLE001 — init must never raise
        _LOGGER.warning("Sentry init failed: %s", exc)
        return False


def capture_exception(exc: Exception, *, context: dict[str, Any] | None = None) -> None:
    """Capture an exception in Sentry (no-op if not initialized).

    Used by error handlers and middleware to forward exceptions
    without coupling to the Sentry SDK directly.
    """
    if not _SENTRY_INITIALIZED:
        return
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_exception(exc)
    except Exception:  # noqa: BLE001 — capture must never raise
        pass


def capture_message(message: str, *, level: str = "info") -> None:
    """Capture a message in Sentry (no-op if not initialized)."""
    if not _SENTRY_INITIALIZED:
        return
    try:
        import sentry_sdk

        sentry_sdk.capture_message(message, level=level)
    except Exception:  # noqa: BLE001 — capture must never raise
        pass


def capture_failover_breadcrumb(
    *,
    region_from: str,
    region_to: str,
    reason: str,
    drill_mode: bool = False,
    elapsed_seconds: float | None = None,
) -> None:
    """Capture a failover breadcrumb in Sentry.

    Phase 5 (cj-style 75번째 wire) — AD-31 (e) verbatim + PRD §F20.5
    + AC #5.4. Adds a structured breadcrumb to the Sentry trail so
    on-call engineers can correlate failover events with downstream
    symptoms (e.g., 503 spikes, latency increase).

    Args:
        region_from: Source region ('primary_seoul' | 'secondary_tokyo').
        region_to: Destination region.
        reason: Trigger reason ('health_probe' | 'manual' | 'drill').
        drill_mode: True if drill test (no actual production failover).
        elapsed_seconds: Measured failover time (None if not completed).
    """
    if not _SENTRY_INITIALIZED:
        return
    try:
        import sentry_sdk

        data: dict[str, Any] = {
            "region_from": region_from,
            "region_to": region_to,
            "reason": reason,
            "drill_mode": drill_mode,
        }
        if elapsed_seconds is not None:
            data["elapsed_seconds"] = elapsed_seconds
        sentry_sdk.add_breadcrumb(
            category="failover",
            message=f"Failover {region_from} → {region_to} ({reason})",
            level="info" if drill_mode else "warning",
            data=data,
        )
    except Exception:  # noqa: BLE001 — capture must never raise
        pass
