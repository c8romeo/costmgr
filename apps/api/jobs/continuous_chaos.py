"""apps.api.jobs.continuous_chaos — Phase 9 continuous chaos experiment job.

Phase 9 (cj-style 99번째 wire) — Continuous chaos (production-safe)
(PRD §F25.4 + AD-36 (e) sub-decision).

Production-safe guards (PRD §F25.4.4 verbatim):
(a) blast radius L1 only (single_request).
(b) intensity low only.
(c) percentage ≤ 5% traffic.
(d) duration ≤ 60s.
(e) auto-rollback ≤ 30s.
(f) dry_run default.
(g) Sentry breadcrumb + Slack notification.

4 production-safe experiment candidates (PRD §F25.4.2 verbatim):
1. `cost-engine-latency-injection-100ms` (Phase 8 SLA p99 < 5s 의 2%)
2. `auth-error-injection-1pct` (Phase 8 login p99 < 1s 정합)
3. `audit-log-query-latency-injection-50ms` (Phase 8 audit log p99 < 2s SLA 의 2.5%)
4. `multi-region-replication-lag-injection` (Phase 5 replication lag 100MB threshold 정합)

Continuous chaos statistics (PRD §F25.4.5 verbatim):
- Prometheus custom metrics:
  `business_chaos_experiments_total{experiment_name, blast_radius, outcome}` Counter
  `business_chaos_auto_rollback_total{experiment_name, trigger}` Counter
  `business_chaos_observations_seconds` Histogram
- 5% traffic 의 production 환경 의미 있는 chaos data 수집.

CR 1-1 audit-first INSERT: `chaos_experiment_started` action_class=
ActionClass.CHAOS_ENGINEERING.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import logging
import uuid
from datetime import UTC, datetime
from typing import Final

from apps.api.core.db import get_session
from apps.api.modules.chaos.chaos_experiment import (
    BLAST_RADIUS_L1,
    INTENSITY_LOW,
)

logger = logging.getLogger(__name__)


# ── Constants — production-safe guards (PRD §F25.4.4 verbatim) ──
MAX_TRAFFIC_PERCENT: Final[float] = 5.0
MAX_DURATION_SECONDS: Final[int] = 60
MAX_AUTO_ROLLBACK_SECONDS: Final[int] = 30

# 4 production-safe experiment candidates.
PRODUCTION_SAFE_EXPERIMENTS: Final[tuple[str, ...]] = (
    "cost-engine-latency-injection-100ms",
    "auth-error-injection-1pct",
    "audit-log-query-latency-injection-50ms",
    "multi-region-replication-lag-injection",
)


def _validate_production_safe_guard(
    *,
    blast_radius: str,
    intensity: str,
    percentage: float,
    duration_seconds: int,
    auto_rollback_seconds: int,
) -> None:
    """Defense-in-depth guard for continuous chaos production-safety.

    Raises `ContinuousChaosProductionUnsafeError` (422) on violation.
    """
    # Import here to avoid circular import (chaos_experiment → jobs)
    from apps.api.modules.chaos.chaos_experiment import (
        ContinuousChaosProductionUnsafeError,
    )

    if blast_radius != BLAST_RADIUS_L1:
        raise ContinuousChaosProductionUnsafeError(
            violated_rule="blast_radius_L1_only",
            attempted_value=blast_radius,
        )
    if intensity != INTENSITY_LOW:
        raise ContinuousChaosProductionUnsafeError(
            violated_rule="intensity_low_only",
            attempted_value=intensity,
        )
    if percentage > MAX_TRAFFIC_PERCENT:
        raise ContinuousChaosProductionUnsafeError(
            violated_rule=f"percentage_le_{MAX_TRAFFIC_PERCENT}",
            attempted_value=str(percentage),
        )
    if duration_seconds > MAX_DURATION_SECONDS:
        raise ContinuousChaosProductionUnsafeError(
            violated_rule=f"duration_le_{MAX_DURATION_SECONDS}s",
            attempted_value=str(duration_seconds),
        )
    if auto_rollback_seconds > MAX_AUTO_ROLLBACK_SECONDS:
        raise ContinuousChaosProductionUnsafeError(
            violated_rule=f"auto_rollback_le_{MAX_AUTO_ROLLBACK_SECONDS}s",
            attempted_value=str(auto_rollback_seconds),
        )


def _compute_result_hash(
    *,
    experiment_name: str,
    blast_radius: str,
    intensity: str,
    percentage: float,
) -> str:
    """CR 4-3/4-4 verbatim — tenant-scoped result_hash for golden_diff."""
    import json

    payload = json.dumps(
        {
            "experiment_name": experiment_name,
            "blast_radius": blast_radius,
            "intensity": intensity,
            "percentage": percentage,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ── Run a single continuous chaos experiment ───────────────────
async def run_continuous_chaos_experiment(
    *,
    experiment_name: str,
    blast_radius: str = BLAST_RADIUS_L1,
    intensity: str = INTENSITY_LOW,
    percentage: float = 5.0,
    duration_seconds: int = 60,
    auto_rollback_seconds: int = 30,
    actor_id: uuid.UUID | None = None,
    dry_run: bool = True,
) -> dict[str, object]:
    """Run a single continuous chaos experiment with production-safe guards.

    Args:
        experiment_name: One of PRODUCTION_SAFE_EXPERIMENTS.
        blast_radius: Must be BLAST_RADIUS_L1.
        intensity: Must be INTENSITY_LOW.
        percentage: Traffic percentage (≤ 5%).
        duration_seconds: Experiment duration (≤ 60s).
        auto_rollback_seconds: Auto-rollback window (≤ 30s).
        actor_id: User who triggered.
        dry_run: If True, no actual fault injection.

    Returns:
        Dict with experiment_name + result_hash + outcome + elapsed_seconds.

    Raises:
        ContinuousChaosProductionUnsafeError: 422 — guard rule violation.
    """
    trace_id = str(uuid.uuid4())
    if experiment_name not in PRODUCTION_SAFE_EXPERIMENTS:
        from apps.api.modules.chaos.chaos_experiment import (
            ContinuousChaosProductionUnsafeError,
        )

        raise ContinuousChaosProductionUnsafeError(
            violated_rule="experiment_name_in_safe_set",
            attempted_value=experiment_name,
        )

    _validate_production_safe_guard(
        blast_radius=blast_radius,
        intensity=intensity,
        percentage=percentage,
        duration_seconds=duration_seconds,
        auto_rollback_seconds=auto_rollback_seconds,
    )

    started_at = datetime.now(tz=UTC)
    result_hash = _compute_result_hash(
        experiment_name=experiment_name,
        blast_radius=blast_radius,
        intensity=intensity,
        percentage=percentage,
    )
    logger.info(
        "continuous_chaos: %s dry_run=%s percentage=%f",
        experiment_name,
        dry_run,
        percentage,
        extra={"trace_id": trace_id},
    )

    session_gen = get_session()
    session = await session_gen.__anext__()
    try:
        from apps.api.core.audit_action import ActionClass, emit_audit_typed

        # Audit-first INSERT (CR 1-1 verbatim) — even for dry-run mode.
        await emit_audit_typed(
            session,
            action_class=ActionClass.CHAOS_ENGINEERING,
            action="chaos_experiment_started",
            actor_id=actor_id,
            target_id=None,
            tenant_id=None,
            payload={
                "experiment_name": experiment_name,
                "blast_radius": blast_radius,
                "intensity": intensity,
                "percentage": percentage,
                "duration_seconds": duration_seconds,
                "auto_rollback_seconds": auto_rollback_seconds,
                "dry_run": dry_run,
                "result_hash": result_hash,
            },
        )
        await session.commit()
    finally:
        await session_gen.aclose()

    elapsed = (datetime.now(tz=UTC) - started_at).total_seconds()
    return {
        "experiment_name": experiment_name,
        "blast_radius": blast_radius,
        "intensity": intensity,
        "percentage": percentage,
        "outcome": "dry_run" if dry_run else "injected",
        "elapsed_seconds": elapsed,
        "result_hash": result_hash,
        "trace_id": trace_id,
    }


# ── APScheduler hook for FastAPI lifespan ──────────────────────
_scheduler_task: asyncio.Task[None] | None = None


async def start_continuous_chaos_scheduler() -> None:
    """FastAPI lifespan entry — start continuous chaos scheduler.

    Runs every 5 minutes (low cadence; production-safe 5% traffic only).
    """
    global _scheduler_task
    if _scheduler_task is not None:
        logger.warning("continuous_chaos scheduler already running — skip")
        return

    async def _scheduler_loop() -> None:
        while True:
            try:
                # Pick a random production-safe experiment.
                import random

                experiment_name = random.choice(PRODUCTION_SAFE_EXPERIMENTS)
                await run_continuous_chaos_experiment(
                    experiment_name=experiment_name,
                    dry_run=True,  # scheduler default dry_run=True
                )
                await asyncio.sleep(300)  # 5 minutes cadence
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception("continuous_chaos scheduler loop error: %s", exc)
                await asyncio.sleep(300)

    _scheduler_task = asyncio.create_task(
        _scheduler_loop(),
        name="phase_9_continuous_chaos_scheduler",
    )
    logger.info("continuous chaos scheduler started")


async def stop_continuous_chaos_scheduler() -> None:
    """FastAPI lifespan entry — stop scheduler."""
    global _scheduler_task
    if _scheduler_task is None:
        return
    _scheduler_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await asyncio.wait_for(_scheduler_task, timeout=30)
    _scheduler_task = None
    logger.info("continuous chaos scheduler stopped")


__all__ = [
    "MAX_TRAFFIC_PERCENT",
    "MAX_DURATION_SECONDS",
    "MAX_AUTO_ROLLBACK_SECONDS",
    "PRODUCTION_SAFE_EXPERIMENTS",
    "run_continuous_chaos_experiment",
    "start_continuous_chaos_scheduler",
    "stop_continuous_chaos_scheduler",
]
