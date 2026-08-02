"""apps.api.jobs.document_retention — 90-day document soft-delete cron.

Story 1.3 — Task 1.3.

This module is the **cron entry point**. It is invoked by the external
scheduler (Railway cron / GitHub Actions schedule) once per day and
delegates to `DocumentService.run_document_retention()` for the actual
work. The cron wrapper exists to:

1. Provide a stable import path for the scheduler
   (`apps.api.jobs.document_retention:run`).
2. Catch top-level exceptions and log them so a single bad run doesn't
   silently disappear (CR 0.2 lesson — defense-in-depth logging).
3. Read the DB engine lazily so the module imports even in environments
   without a live DB (e.g. test fixture collections).

Privacy contract (PRD §F0.4):
- After 90 days, documents are soft-deleted (`deleted_at` set) so the
  tenant's dashboard shows "만료됨" but the row remains for audit
  purposes.
- Hard delete (PG row removal) is NOT in MVP — Story 1.3 §NFR-22 says
  the operator must keep audit-grade records for 1 year. A separate
  cleanup job (out of scope for this story) handles hard delete.

Operational deployment:
- Railway cron: schedule daily 03:00 KST (UTC 18:00) — outside peak.
- Failure behavior: any exception in this module is logged + the cron
  runner sends a Slack alert via Railway's notification hook.
"""

from __future__ import annotations

import contextlib
import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.db import get_session
from apps.api.modules.m10_ai.service import (
    RetentionResult,
)
from apps.api.modules.m10_ai.service import (
    run_document_retention as _run_retention,
)

logger = logging.getLogger(__name__)


async def run(*, now: datetime | None = None) -> RetentionResult:
    """Cron entry point — soft-delete documents past retention window.

    The scheduler invokes this as `python -c "from apps.api.jobs.document_retention import run; import asyncio; asyncio.run(run())"`.

    Returns the retention summary so the cron runner can log it.
    """
    trace_id = str(uuid.uuid4())
    now = now or datetime.now(tz=UTC)

    # Lazy DB session (Story 0.2 pattern) — never block module import.
    session_gen = get_session()
    session: AsyncSession = await session_gen.__anext__()
    try:
        result = await _run_retention(session, trace_id=trace_id, now=now)
        logger.info(
            "document_retention.run completed",
            extra={
                "trace_id": trace_id,
                "soft_deleted_documents": result.soft_deleted_documents,
                "cutoff": result.cutoff.isoformat(),
            },
        )
        return result
    except Exception:  # pragma: no cover — cron runner catches & alerts
        logger.exception(
            "document_retention.run failed",
            extra={"trace_id": trace_id},
        )
        raise
    finally:
        with contextlib.suppress(StopAsyncIteration):
            await session_gen.__anext__()  # trigger __aexit__ / close
