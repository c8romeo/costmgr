"""
apps/api/lib/observability/sentry-alerts.py — Sentry alert wiring (backend).

1st release launch (cj-style 64번째 진입점) — T5.3 (AC #5.4) — F18.5 Production verification.
- Sentry alert wiring backend production 환경 결정 wire.
- 5 alert rules: 5xx / tenant isolation / alembic / audit log / PITR drill.
"""
from __future__ import annotations

import logging
from typing import Final

logger = logging.getLogger(__name__)

# 5 alert rules (cj-style 1st release launch 64번째 진입점 정합)
ALERT_RULES: Final[tuple[str, ...]] = (
    "5xx_api_error_rate",
    "tenant_isolation_violation",
    "alembic_migration_failure",
    "audit_log_integrity_failure",
    "pitr_drill_overdue",
)


def capture_alert(rule: str, message: str, *, level: str = "error", tags: dict | None = None, extra: dict | None = None) -> None:
    """Capture a Sentry alert for a production environment violation.

    1st release launch 결정 wire — production environment alert wiring.
    """
    try:
        import sentry_sdk

        sentry_sdk.capture_message(
            f"[1st-release] {rule}: {message}",
            level=level,
            tags={"alert_rule": rule, **(tags or {})},
            extra=extra,
        )
    except ImportError:
        logger.warning("sentry-sdk not installed; alert not sent: %s — %s", rule, message)


def check_tenant_isolation(violation: bool, tenant_id: str) -> None:
    """Check tenant isolation (CR 0-2 RLS lesson) and capture alert if violated."""
    if violation:
        capture_alert(
            "tenant_isolation_violation",
            f"Tenant isolation violation detected for tenant_id={tenant_id}",
            level="fatal",
            tags={"tenant_id": tenant_id},
        )
