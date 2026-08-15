"""apps.api.jobs.tenant_hard_delete — 30-day tenant hard-delete cron.

Story 12.3 — Task 3 (T3).

This module is the **cron entry point** for the destructive endpoint
NFR4 2절 (5년 audit 보존 + 30일 후 완전 삭제). It is invoked by the
external scheduler (Railway cron / GitHub Actions schedule) once per
day and delegates to `DeletionService.hard_delete_expired_tenants` for
the actual work. The cron wrapper exists to:

1. Provide a stable import path for the scheduler
   (`apps.api.jobs.tenant_hard_delete:run`).
2. Catch top-level exceptions and log them so a single bad run doesn't
   silently disappear (CR 0.2 lesson — defense-in-depth logging).
3. Read the DB engine lazily so the module imports even in environments
   without a live DB (e.g. test fixture collections).

Privacy contract (PRD §F12.3 + NFR4 2절):
- Tenants in `pending_deletion` status whose `deletion_scheduled_for`
  anchor has elapsed (30-day default retention) are hard-deleted
  (status → 'deleted' + tenant row anonymized + scheduled_for cleared).
- The `deletion_consents` table is INSERT-only (AD-2 invariant) and
  survives for forensic chain (NFR4 2절 5년 audit 보존).
- Per-tenant soft-fail: `AccountDeletionHardDeleteError` on one tenant
  does NOT abort the sweep — the service continues with the next tenant.

Operational deployment:
- Railway cron: schedule daily 04:00 KST (UTC 19:00) — outside peak
  (Story 12.2 backup cron at 02:00 KST + Story 1.3 retention at 03:00
  KST; 04:00 KST keeps tenant_hard_delete in the off-peak batch).
- Failure behavior: any exception in this module is logged + the cron
  runner sends a Slack alert via Railway's notification hook.

CR 11-2 L10: NO bare `except Exception` (UP038 tuple form).
"""

from __future__ import annotations

import contextlib
import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.db import get_session
from apps.api.modules.m12_account.services.account_deletion_service import (
    DeletionService,
    HardDeleteResult,
)

logger = logging.getLogger(__name__)


async def run(*, now: datetime | None = None) -> HardDeleteResult:
    """Cron entry point — hard-delete tenants past 30-day retention window.

    The scheduler invokes this as:
        python -c "from apps.api.jobs.tenant_hard_delete import run; import asyncio; asyncio.run(run())"

    Returns the hard-delete summary so the cron runner can log it.
    """
    trace_id = str(uuid.uuid4())
    now = now or datetime.now(tz=UTC)

    # Lazy DB session (Story 0.2 pattern) — never block module import.
    session_gen = get_session()
    session: AsyncSession = await session_gen.__anext__()
    try:
        # service_role context — bypasses RLS for the cron sweep.
        # Owner_id is None (system actor — no human owner).
        service = DeletionService(
            session,
            tenant_id=uuid.UUID(int=0),  # sentinel — cron iterates ALL tenants
            actor_id=None,
            trace_id=trace_id,
        )
        result = await service.run_hard_delete_cron(now=now)
        logger.info(
            "tenant_hard_delete.run completed",
            extra={
                "trace_id": trace_id,
                "deleted_tenant_count": len(result.deleted_tenant_ids),
                "failed_tenant_count": len(result.failed_tenant_ids),
                "cutoff": now.isoformat(),
            },
        )
        return result
    except (KeyboardInterrupt, SystemExit):
        # CR 11-2 L10 — UP038-compliant tuple form. Bare except is
        # forbidden; explicitly allow process-control signals.
        raise
    except Exception:  # pragma: no cover — cron runner catches & alerts
        logger.exception(
            "tenant_hard_delete.run failed",
            extra={"trace_id": trace_id},
        )
        raise
    finally:
        with contextlib.suppress(StopAsyncIteration):
            await session_gen.__anext__()  # trigger __aexit__ / close
