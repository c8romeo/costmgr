"""apps.api.jobs.backup_daily — Story 12.2 daily auto-backup cron.

This module is the **cron entry point** for daily backups. It is invoked
by the external scheduler (Railway cron / GitHub Actions schedule) once
per day and delegates to `BackupExportService.run_backup()` per tenant.

Precedent: `apps/api/jobs/document_retention.py:51-83` (Story 1.3).

Cron wrapper exists to:
1. Provide a stable import path for the scheduler
   (`apps.api.jobs.backup_daily:run`).
2. Iterate over all tenants — `BackupExportService` is per-tenant.
3. Catch per-tenant failures (one tenant's failure doesn't block others).
4. Emit `backup_failed` audit emit BEFORE raise (CR 1.1 audit-first).
5. Read DB engine lazily so module imports even without a live DB.

Operational deployment:
- Railway cron: schedule daily 02:00 KST (UTC 17:00) — outside peak.
- Failure behavior: any exception is logged + cron runner sends Slack
  alert via Railway's notification hook.

NFR4 (PRD §NFR4): "RPO 24h / RTO 4h / 백업 보관 30일(자동), 1년(분기) /
감사로그 5년 append-only".

AD-2 INSERT-only: tenant_backups is INSERT-only; the cron never UPDATEs
or DELETEs (30-day retention sweep is a separate cron — backup_retention).
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
    BackupResult,
)

logger = logging.getLogger(__name__)


async def _list_tenant_ids(session: AsyncSession) -> list[uuid.UUID]:
    """SELECT all tenant IDs (tenant_backups is per-tenant)."""
    result = await session.execute(select(Tenant.id))
    return [row[0] for row in result.all()]


async def run(*, now: datetime | None = None) -> list[BackupResult]:
    """Cron entry point — daily backup for all tenants.

    The scheduler invokes this as
    `python -c "from apps.api.jobs.backup_daily import run; import asyncio; asyncio.run(run())"`.

    Args:
        now: Reference "now" for backup_date (KST date) + created_at
            (UTC timestamp). Default = UTC now.

    Returns:
        List of BackupResult, one per tenant. Caller (cron runner) can
        log a summary.
    """
    trace_id = str(uuid.uuid4())
    now = now or datetime.now(tz=UTC)

    # Lazy DB session (Story 0.2 pattern) — never block module import.
    session_gen = get_session()
    session: AsyncSession = await session_gen.__anext__()
    results: list[BackupResult] = []
    try:
        tenant_ids = await _list_tenant_ids(session)
        logger.info(
            "backup_daily.run starting",
            extra={"trace_id": trace_id, "tenant_count": len(tenant_ids)},
        )

        for tenant_id in tenant_ids:
            # Per-tenant failure isolation — one tenant's failure doesn't
            # block others. Audit `backup_failed` is emitted by service
            # layer (CR 1.1) — but cron wrapper also catches the
            # exception to keep iteration going.
            try:
                svc = BackupExportService(
                    session,
                    tenant_id=tenant_id,
                    actor_id=None,  # cron path — no actor
                    trace_id=trace_id,
                )
                result = await svc.run_backup()
                results.append(result)
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "backup_daily.run tenant failed",
                    extra={
                        "trace_id": trace_id,
                        "tenant_id": str(tenant_id),
                        "error": str(exc),
                    },
                )
                # Continue with next tenant — don't re-raise here.

        logger.info(
            "backup_daily.run completed",
            extra={
                "trace_id": trace_id,
                "successful_tenants": len(results),
                "total_tenants": len(tenant_ids),
            },
        )
        return results
    except Exception:  # pragma: no cover — top-level cron runner alert
        logger.exception(
            "backup_daily.run failed",
            extra={"trace_id": trace_id},
        )
        raise
    finally:
        with contextlib.suppress(StopAsyncIteration):
            await session_gen.__anext__()  # trigger __aexit__ / close
