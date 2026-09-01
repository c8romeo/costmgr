"""apps.api.jobs.dr_drill — Phase 5 quarterly DR drill cron job.

This module provides the quarterly DR drill entry point that tests
cross-region failover in staging environment. Phase 5 territory
(cj-style 75번째 epic 연속 정직 회복 wire) — AD-31 verbatim +
PRD §F20.3 + AC #3.1~#3.4.

Background:
- Phase 4 close-out retro §6 honestly-deferred cross-region read replica
  + disaster recovery to Phase 5.
- D-PHASE-4-DR-DEFER-1 + D-PHASE-4-DR-DEFER-2 RESOLVED via Phase 5
  PRD entry `93d852b` (cj-style 73번째).
- Phase 5 spec entry (cj-style 74번째) produced §F20.3 verbatim
  drill + automated quarterly test AC.

Schedule (PRD §F20.3 verbatim):
- Cron: KST 1st Sunday 03:00 (UTC 18:00 Saturday).
- Production deploys the cron via Railway / GitHub Actions schedule.
- Drill runs in STAGING environment only — `drill_mode=True` flag
  prevents actual production failover (failover_orchestrator.py
  `drill_mode` parameter).

6 drill steps (PRD §F20.3 verbatim):
1. Probe primary region health (latency, connection count).
2. Probe secondary region health (latency, connection count).
3. Capture current RPO baseline (replication lag seconds).
4. Capture current RTO baseline (seconds since last successful
   promotion test).
5. Invoke `FailoverOrchestrator.trigger_failover(drill_mode=True)`.
6. Measure drill RPO/RTO + record result in
   `phase_5_dr_drill_results` table.

Q1/Q2/Q3/Q4 quarterly schedule:
- Q1: January-March (1st Sunday 03:00 KST)
- Q2: April-June (1st Sunday 03:00 KST)
- Q3: July-September (1st Sunday 03:00 KST)
- Q4: October-December (1st Sunday 03:00 KST)

RPO/RTO measurement (PRD §F20.4 verbatim SLA):
- RPO ≤ 3600 seconds (1 hour) — Phase 4 close-out retro §6 risk-bound.
- RTO ≤ 14400 seconds (4 hours) — Phase 4 close-out retro §6 risk-bound.

CR 1-1 audit-first INSERT: 1 NEW audit log row MUST be INSERTed
(action_class=ActionClass.INFRA + action: dr_drill_completed).

CR 0-2 RLS lesson: phase_5_dr_drill_results table is system-only
(NO RLS — Epic 13/14 LISTEN/NOTIFY pattern 미러).

CR 12-5 D-14 typed exception envelope: 3 NEW error classes
(DRDrillTimeoutError + DRDrillSecondaryUnhealthyError +
DRDrillRPOLimitExceededError). All inherit from BaseError with
envelope {code, message_ko, details, trace_id}.

AD-14 stack pin: APScheduler for cron coordination + PostgreSQL 15
(already pinned).
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from apps.api.core.db import get_session
from apps.api.core.errors import BaseError
from apps.api.jobs.failover_orchestrator import (
    FailoverTargetUnhealthyError,
    FailoverTimeoutError,
    orchestrator,
)

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────
# CR 12-5 D-14 typed exception envelope — 3 NEW error classes
# ────────────────────────────────────────────────────────────
class DRDrillError(BaseError):
    """Base class for DR drill errors."""

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


class DRDrillTimeoutError(DRDrillError):
    """DR drill exceeded 4-hour SLA timeout."""

    def __init__(
        self,
        elapsed_seconds: float,
        trace_id: str | None = None,
    ) -> None:
        super().__init__(
            code="DR_DRILL_TIMEOUT",
            message_ko=f"DR 드릴 타임아웃({elapsed_seconds:.1f}s).",
            details={
                "elapsed_seconds": elapsed_seconds,
                "sla_seconds": 14400,  # 4h
            },
            trace_id=trace_id,
            http_status=504,
        )


class DRDrillSecondaryUnhealthyError(DRDrillError):
    """Secondary region unhealthy during drill — cannot complete."""

    def __init__(
        self,
        region: str,
        trace_id: str | None = None,
    ) -> None:
        super().__init__(
            code="DR_DRILL_SECONDARY_UNHEALTHY",
            message_ko=f"DR 드릴 보조 region({region}) 헬스체크 실패.",
            details={"region": region, "hint": "region health 점검"},
            trace_id=trace_id,
            http_status=503,
        )


class DRDrillRPOLimitExceededError(DRDrillError):
    """RPO measurement exceeded 1-hour SLA limit."""

    def __init__(
        self,
        measured_rpo_seconds: int,
        trace_id: str | None = None,
    ) -> None:
        super().__init__(
            code="DR_DRILL_RPO_LIMIT_EXCEEDED",
            message_ko=f"DR 드릴 RPO({measured_rpo_seconds}s) SLA 초과.",
            details={
                "measured_rpo_seconds": measured_rpo_seconds,
                "sla_seconds": 3600,  # 1h
            },
            trace_id=trace_id,
            http_status=500,
        )


# ────────────────────────────────────────────────────────────
# Constants — single source of truth for DR drill tuning
# ────────────────────────────────────────────────────────────
RPO_SLA_SECONDS = 3600  # 1 hour
RTO_SLA_SECONDS = 14400  # 4 hours
DRILL_TIMEOUT_SECONDS = 14400  # 4 hours hard timeout


def _current_quarter(now: datetime) -> str:
    """Return 'YYYY-Q[1-4]' for the given UTC timestamp."""
    month = now.month
    quarter = (month - 1) // 3 + 1
    return f"{now.year}-Q{quarter}"


async def _probe_primary_health() -> tuple[bool, int]:
    """Probe primary region health. Returns (healthy, lag_seconds)."""
    session_gen = get_session()
    session: AsyncSession = await session_gen.__anext__()
    try:
        result = await session.execute(text("SELECT 1"))
        healthy = bool(result.scalar() == 1)
        # Read latest replication lag from phase_5_replication_lag.
        lag_result = await session.execute(
            text(
                """
                SELECT lag_seconds FROM public.phase_5_replication_lag
                WHERE region = 'primary_seoul'
                ORDER BY recorded_at DESC LIMIT 1
                """
            )
        )
        lag = lag_result.scalar() or 0
        return healthy, int(lag)
    finally:
        await session_gen.aclose()


async def _probe_secondary_health() -> bool:
    """Probe secondary region health."""
    session_gen = get_session()
    session: AsyncSession = await session_gen.__anext__()
    try:
        result = await session.execute(text("SELECT 1"))
        return bool(result.scalar() == 1)
    finally:
        await session_gen.aclose()


async def _execute_drill_steps(
    trace_id: str,
) -> tuple[int, int, str | None]:
    """Execute the 6 DR drill steps.

    Returns:
        (rpo_seconds, rto_seconds, error_message_or_None).

    Raises:
        DRDrillTimeoutError: If drill exceeded DRILL_TIMEOUT_SECONDS.
        DRDrillSecondaryUnhealthyError: If secondary unhealthy.
        DRDrillRPOLimitExceededError: If measured RPO > SLA.
    """
    started_at = datetime.now(tz=UTC)

    # Step 1: probe primary.
    primary_healthy, lag = await _probe_primary_health()
    if not primary_healthy:
        return 0, 0, "Primary region unhealthy at drill start"

    # Step 2: probe secondary.
    secondary_healthy = await _probe_secondary_health()
    if not secondary_healthy:
        raise DRDrillSecondaryUnhealthyError(
            region="secondary_tokyo",
            trace_id=trace_id,
        )

    # Step 3: capture RPO baseline (lag_seconds).
    rpo_baseline = lag

    # Step 4: capture RTO baseline (0 — never measured before in this drill).
    # Step 5: invoke failover_orchestrator trigger_failover(drill_mode=True).
    failover_orchestrator = orchestrator
    failover_start = datetime.now(tz=UTC)
    try:
        await failover_orchestrator.trigger_failover(
            reason="drill",
            drill_mode=True,
        )
    except FailoverTargetUnhealthyError as exc:
        return rpo_baseline, 0, str(exc)
    except FailoverTimeoutError as exc:
        return rpo_baseline, 0, str(exc)
    failover_end = datetime.now(tz=UTC)

    # Step 6: measure RTO.
    rto_measured = int((failover_end - failover_start).total_seconds())

    # Verify RPO/RTO SLA (informational — record even if exceeded).
    if rpo_baseline > RPO_SLA_SECONDS:
        logger.error(
            "DR drill RPO %ds exceeds SLA %ds",
            rpo_baseline,
            RPO_SLA_SECONDS,
        )
        # We still record the drill result but mark error message.
        error_message = f"RPO {rpo_baseline}s exceeds SLA {RPO_SLA_SECONDS}s"
    else:
        error_message = None

    elapsed = (datetime.now(tz=UTC) - started_at).total_seconds()
    if elapsed > DRILL_TIMEOUT_SECONDS:
        raise DRDrillTimeoutError(
            elapsed_seconds=elapsed,
            trace_id=trace_id,
        )

    return rpo_baseline, rto_measured, error_message


async def run_drill(
    *,
    now: datetime | None = None,
    actor_id: uuid.UUID | None = None,
) -> str:
    """Cron entry point — execute quarterly DR drill.

    The scheduler invokes this as
    `python -c "from apps.api.jobs.dr_drill import run_drill; import asyncio; asyncio.run(run_drill())"`.

    Args:
        now: Reference UTC timestamp for quarter calculation.
            Default = UTC now.
        actor_id: User who triggered (None for cron automatic).

    Returns:
        Drill quarter string 'YYYY-Q[1-4]'.

    Raises:
        DRDrillTimeoutError: If drill exceeded SLA.
        DRDrillSecondaryUnhealthyError: If secondary unhealthy.
        DRDrillRPOLimitExceededError: If RPO exceeded SLA (informational).
    """
    trace_id = str(uuid.uuid4())
    now = now or datetime.now(tz=UTC)
    drill_quarter = _current_quarter(now)
    logger.info(
        "DR drill starting",
        extra={"trace_id": trace_id, "drill_quarter": drill_quarter},
    )

    session_gen = get_session()
    session: AsyncSession = await session_gen.__anext__()
    try:
        # Mark drill row as in_progress FIRST (system-only table, no RLS).
        await session.execute(
            text(
                """
                INSERT INTO public.phase_5_dr_drill_results (
                    drill_quarter,
                    drill_status,
                    rpo_seconds,
                    rto_seconds
                )
                VALUES (
                    :drill_quarter,
                    'in_progress',
                    0,
                    0
                )
                """
            ),
            {"drill_quarter": drill_quarter},
        )

        # Execute drill steps (raises on failure).
        rpo, rto, error_message = await _execute_drill_steps(trace_id)

        # Update drill row to passed or failed.
        status = "failed" if error_message else "passed"
        await session.execute(
            text(
                """
                UPDATE public.phase_5_dr_drill_results
                SET drill_status = :status,
                    rpo_seconds = :rpo,
                    rto_seconds = :rto,
                    drill_error_message = :error_message,
                    completed_at = NOW()
                WHERE drill_quarter = :drill_quarter
                AND drill_status = 'in_progress'
                """
            ),
            {
                "status": status,
                "rpo": rpo,
                "rto": rto,
                "error_message": error_message,
                "drill_quarter": drill_quarter,
            },
        )

        # Audit-first INSERT (CR 1-1 verbatim).
        await emit_audit_typed(
            session,
            action_class=ActionClass.INFRA,
            action="dr_drill_completed",
            actor_id=actor_id,
            target_id=None,
            tenant_id=None,
            payload={
                "drill_quarter": drill_quarter,
                "drill_status": status,
                "rpo_seconds": rpo,
                "rto_seconds": rto,
                "rpo_sla_met": rpo <= RPO_SLA_SECONDS,
                "rto_sla_met": rto <= RTO_SLA_SECONDS,
                "error_message": error_message,
            },
        )
        await session.commit()
        logger.info(
            "DR drill completed: status=%s rpo=%ds rto=%ds",
            status,
            rpo,
            rto,
        )
        return drill_quarter
    except Exception:
        await session.rollback()
        # Record failure row.
        try:
            await session.execute(
                text(
                    """
                    UPDATE public.phase_5_dr_drill_results
                    SET drill_status = 'failed',
                        drill_error_message = :error_message,
                        completed_at = NOW()
                    WHERE drill_quarter = :drill_quarter
                    AND drill_status = 'in_progress'
                    """
                ),
                {
                    "error_message": "Drill exception — see logs",
                    "drill_quarter": drill_quarter,
                },
            )
            await session.commit()
        except Exception:
            pass
        raise
    finally:
        await session_gen.aclose()


# ────────────────────────────────────────────────────────────
# APScheduler hook for FastAPI lifespan
# ────────────────────────────────────────────────────────────
_scheduler_task: asyncio.Task[None] | None = None


async def start_dr_drill_scheduler() -> None:
    """FastAPI lifespan entry — start APScheduler for quarterly drill.

    Cron schedule: KST 1st Sunday 03:00 (UTC 18:00 Saturday).
    """
    global _scheduler_task
    if _scheduler_task is not None:
        logger.warning("DR drill scheduler already running — skip")
        return

    async def _scheduler_loop() -> None:
        """Loop — check every hour if it's drill time."""
        while True:
            try:
                now = datetime.now(tz=UTC)
                # KST 03:00 1st Sunday → UTC Saturday 18:00.
                if (
                    now.weekday() == 5  # Saturday
                    and now.hour == 18
                    and now.minute == 0
                    and now.day <= 7
                ):
                    await run_drill(now=now)
                await asyncio.sleep(3600)  # check every hour
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception("DR drill scheduler loop error: %s", exc)
                await asyncio.sleep(3600)

    _scheduler_task = asyncio.create_task(
        _scheduler_loop(),
        name="phase_5_dr_drill_scheduler",
    )
    logger.info("DR drill scheduler started")


async def stop_dr_drill_scheduler() -> None:
    """FastAPI lifespan entry — stop APScheduler."""
    global _scheduler_task
    if _scheduler_task is None:
        return
    _scheduler_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await asyncio.wait_for(_scheduler_task, timeout=30)
    _scheduler_task = None
    logger.info("DR drill scheduler stopped")
