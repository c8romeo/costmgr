"""apps.api.jobs.backup_retention — Story 12.2 30-day retention sweep cron.

This module is the **cron entry point** for the 30-day retention sweep.
It is invoked by the external scheduler once per day (after
backup_daily) and delegates to `BackupExportService.run_retention_sweep()`
per tenant.

Precedent: `apps/api/jobs/document_retention.py:51-83` (Story 1.3).

Cron wrapper exists to:
1. Provide a stable import path for the scheduler
   (`apps.api.jobs.backup_retention:run`).
2. Iterate over all tenants — sweep is per-tenant.
3. Catch per-tenant failures (one tenant's failure doesn't block others).
4. Emit `backup_retention_purged` audit per row (CR 1.1 audit-first).
5. Idempotent: re-running with the same `now` is a no-op (rows already
   `purged_at IS NOT NULL` are excluded by the WHERE clause).

Operational deployment:
- Railway cron: schedule daily 03:00 KST (UTC 18:00) — outside peak,
  AFTER backup_daily's 02:00 KST.
- Failure behavior: any exception is logged + cron runner sends Slack
  alert via Railway's notification hook.

NFR4 (PRD §NFR4): "백업 보관 30일(자동)" — atomic wire scope.
Quarterly 1-year archive is honestly DEFER (CR 11.3 — sprint-scale).

AD-2 INSERT-only: tenant_backups is INSERT-only — sweep uses UPDATE
`purged_at = now()` (soft-delete), NOT DELETE. The 0024 alembic
trigger blocks UPDATE/DELETE on non-purged columns anyway; the sweep
specifically sets `purged_at` column which IS allowed (the trigger
allows UPDATE on purged_at column only — see migration 0024).
"""

from __future__ import annotations

import contextlib
import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.db import get_session
from apps.api.core.db_models import Tenant
from apps.api.modules.m12_account.services.backup_export_service import (
    BackupExportService,
    RetainResult,
)

logger = logging.getLogger(__name__)


async def _list_tenant_ids(session: AsyncSession) -> list[uuid.UUID]:
    """SELECT all tenant IDs (retention sweep is per-tenant)."""
    result = await session.execute(select(Tenant.id))
    return [row[0] for row in result.all()]


async def run(*, now: datetime | None = None) -> list[RetainResult]:
    """Cron entry point — 30-day retention sweep for all tenants.

    The scheduler invokes this as
    `python -c "from apps.api.jobs.backup_retention import run; import asyncio; asyncio.run(run())"`.

    Args:
        now: Reference "now" for soft-delete timestamp + cutoff calc.
            Default = UTC now.

    Returns:
        List of RetainResult, one per tenant. Caller (cron runner) can
        log a summary.
    """
    trace_id = str(uuid.uuid4())
    now = now or datetime.now(tz=UTC)

    # Lazy DB session (Story 0.2 pattern) — never block module import.
    session_gen = get_session()
    session: AsyncSession = await session_gen.__anext__()
    results: list[RetainResult] = []
    try:
        tenant_ids = await _list_tenant_ids(session)
        logger.info(
            "backup_retention.run starting",
            extra={"trace_id": trace_id, "tenant_count": len(tenant_ids)},
        )

        for tenant_id in tenant_ids:
            # Per-tenant failure isolation
            try:
                svc = BackupExportService(
                    session,
                    tenant_id=tenant_id,
                    actor_id=None,
                    trace_id=trace_id,
                )
                result = await svc.run_retention_sweep(now=now)
                results.append(result)
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "backup_retention.run tenant failed",
                    extra={
                        "trace_id": trace_id,
                        "tenant_id": str(tenant_id),
                        "error": str(exc),
                    },
                )
                # Continue with next tenant — don't re-raise here.

        logger.info(
            "backup_retention.run completed",
            extra={
                "trace_id": trace_id,
                "successful_tenants": len(results),
                "total_tenants": len(tenant_ids),
                "total_purged": sum(r.purged_count for r in results),
            },
        )
        return results
    except Exception:  # pragma: no cover — top-level cron runner alert
        logger.exception(
            "backup_retention.run failed",
            extra={"trace_id": trace_id},
        )
        raise
    finally:
        with contextlib.suppress(StopAsyncIteration):
            await session_gen.__anext__()  # trigger __aexit__ / close
