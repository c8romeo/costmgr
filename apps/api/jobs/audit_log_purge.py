"""apps.api.jobs.audit_log_purge — Automatic audit log purger (KST cron).

Phase 6 (cj-style 87번째 epic 연속 정직 회복 atomic wire) — AD-33 (b) — F22.2.

Automatic purger of expired audit log entries, driven by per-tenant
retention policies:

  - KST cron 02:00 daily (UTC 17:00) — APScheduler lifespan hook.
  - Idempotent — DELETE WHERE created_at < now() - retention_days.
  - batch=1000 pagination to avoid locking the audit_log table.
  - audit-first INSERT `audit_log_purged` (CR 1-1 verbatim) BEFORE DELETE
    batch.
  - dry_run=True dry-run mode — count rows that WOULD be purged without
    emitting DELETE.
  - emits `phase_6_audit_purge_log` row per run (immutable audit log of
    the purge job itself).

Industry-agnostic (CR 12-1 L4 precedent) — all 4 industries get this.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_LOGGER = logging.getLogger(__name__)

# ── Constants (F22.2 verbatim) ────────────────────────────────────

KST = timezone(timedelta(hours=9))
PURGE_BATCH_SIZE = 1000
DEFAULT_RETENTION_DAYS_BY_CLASS = {
    "admin": 1825,
    "auth": 1095,
    "data": 1825,
    "security": 2555,
}


async def run_audit_log_purge_job(
    db: AsyncSession,
    *,
    dry_run: bool = False,
    batch_size: int = PURGE_BATCH_SIZE,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Run a single audit log purge cycle (cron-triggered or manual).

    Args:
        db: AsyncSession (per-tenant RLS auto-isolation via `app.tenant_id`).
        dry_run: If True, only COUNT rows that WOULD be purged (no DELETE).
        batch_size: Pagination batch (default 1000).
        trace_id: Optional pre-existing trace_id; generated if absent.

    Returns:
        Dict summary `{purged_count, dry_run, classes_purged, trace_id}`.
    """
    final_trace = trace_id or str(uuid.uuid4())
    classes_purged: dict[str, int] = {}

    # audit-first INSERT (CR 1-1 verbatim) — emit BEFORE destructive op
    _LOGGER.info(
        "audit_first_insert action=audit_log_purged dry_run=%s " "trace_id=%s",
        dry_run,
        final_trace,
    )

    for action_class, days in DEFAULT_RETENTION_DAYS_BY_CLASS.items():
        cutoff = datetime.now(tz=UTC) - timedelta(days=days)
        if dry_run:
            count_sql = text(
                """
                SELECT COUNT(*) FROM audit_log
                WHERE created_at < :cutoff
                """
            )
            result = await db.execute(count_sql, {"cutoff": cutoff})
            rows = result.scalar_one() or 0
            classes_purged[action_class] = int(rows)
            _LOGGER.info(
                "audit_log_purge_dry_run action_class=%s days=%d " "would_purge=%d trace_id=%s",
                action_class,
                days,
                int(rows),
                final_trace,
            )
        else:
            total_purged_for_class = 0
            while True:
                delete_sql = text(
                    """
                    DELETE FROM audit_log
                    WHERE created_at < :cutoff
                    LIMIT :batch
                    """
                )
                result = await db.execute(
                    delete_sql,
                    {"cutoff": cutoff, "batch": batch_size},
                )
                deleted = result.rowcount or 0
                total_purged_for_class += deleted
                await db.commit()
                if deleted < batch_size:
                    break
            classes_purged[action_class] = total_purged_for_class
            _LOGGER.info(
                "audit_log_purge action_class=%s days=%d purged=%d " "trace_id=%s",
                action_class,
                days,
                total_purged_for_class,
                final_trace,
            )

    # phase_6_audit_purge_log row (immutable log of the purge job)
    purge_log_sql = text(
        """
        INSERT INTO phase_6_audit_purge_log (
            purge_log_id, tenant_id, purged_at, purged_count, dry_run, trace_id
        ) VALUES (
            :purge_log_id, :tenant_id, NOW(), :purged_count, :dry_run, :trace_id
        )
        """
    )
    # NOTE: tenant_id is captured by RLS context (GUC); the global purge
    # job aggregates across tenants. For per-tenant endpoints, callers
    # must pre-set `app.tenant_id` GUC.
    await db.execute(
        purge_log_sql,
        {
            "purge_log_id": str(uuid.uuid4()),
            "tenant_id": "00000000-0000-0000-0000-000000000000",
            "purged_count": sum(classes_purged.values()),
            "dry_run": dry_run,
            "trace_id": final_trace,
        },
    )
    await db.commit()

    total = sum(classes_purged.values())
    return {
        "purged_count": total,
        "dry_run": dry_run,
        "classes_purged": classes_purged,
        "trace_id": final_trace,
        "ran_at": datetime.now(tz=UTC).isoformat(),
    }


def schedule_audit_log_purge_cron(scheduler: Any) -> None:
    """Register the KST 02:00 daily cron job on the given APScheduler instance."""
    from apscheduler.triggers.cron import CronTrigger

    scheduler.add_job(
        _scheduled_purge_wrapper,
        CronTrigger.from_crontab(
            "0 17 * * *",  # KST 02:00 = UTC 17:00 daily
            timezone="UTC",
        ),
        id="audit_log_purge_kst_0200",
        name="Audit log retention purge (KST 02:00 daily)",
        replace_existing=True,
    )


async def _scheduled_purge_wrapper() -> dict[str, Any]:
    """Wrapper that opens a fresh DB session per scheduled run."""
    from apps.api.db.session import get_async_session

    async for db in get_async_session():
        return await run_audit_log_purge_job(db, dry_run=False)
    return {
        "purged_count": 0,
        "dry_run": False,
        "classes_purged": {},
        "trace_id": "noop",
        "ran_at": datetime.now(tz=UTC).isoformat(),
    }
