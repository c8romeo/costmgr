"""apps.api.modules.m11_close.services.snapshot_persistence_service — Story 11.3.

AD-20 state machine orchestrator: `draft` → `verified` → `committed`
transition (the "commit_snapshot_persistence" step) + read access.

This is the M11 owner wire for sealing a verified snapshot as immutable
summary record. After this transition, only AD-22 reversal
(`ReversalExecuteService` — T4) can mutate the snapshot.

Service-layer wrapper for the pure kernel in
`packages/services.m11_close.commit_snapshot_persistence`. Provides:
- `commit_snapshot` — AD-20 verified → committed transition
  (SELECT FOR UPDATE, kernel validate, UPDATE state, audit-first emit,
  AD-25 multi-channel publish).
- `get_snapshot` — observability read of fiscal_period_snapshots state.

AD-2 + AD-11 binding: All DB writes are wrapped in audit-first
emissions (CR 1.1 invariant). Pure-Python business logic lives in
the kernel; this service layer is the thin orchestration shell.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit import emit_audit
from apps.api.core.cache_invalidation_publisher import (
    ALLOWED_CHANNELS,
    CacheInvalidationPublisher,
)
from apps.api.core.db_models import FiscalPeriodSnapshot
from apps.api.modules.m11_close.exceptions import SnapshotAlreadyCommittedError
from packages.services.m11_close.commit_snapshot_persistence import (
    validate_commit_snapshot_persistence,
)

# AD-25 multi-channel — Story 11.3 wire expands from 1 channel to 4
# channels (T2). The commit_snapshot_persistence step fans out to:
#   - closing_snapshot_cache  (primary — closing snapshot just sealed)
#   - fiscal_period_cache     (fiscal_periods metadata cache)
#   - cost_engine_cache       (downstream cost engine re-eval)
#   - ai_cache                (M10 AI cache invalidation — 11-1 보존)
SNAPSHOT_COMMIT_CHANNELS: tuple[str, ...] = (
    "closing_snapshot_cache",
    "fiscal_period_cache",
    "cost_engine_cache",
    "ai_cache",
)


# ── Result dataclasses (service-layer wire shape) ────────────
@dataclass(frozen=True)
class CommitSnapshotPersistenceResponse:
    """commit_snapshot result envelope — service layer returns this.

    Distinct from the pure-kernel `CommitSnapshotPersistenceResult`
    (which is the kernel's authorization decision). The service-layer
    response carries the AD-25 receipt list + wire IDs needed by the
    FastAPI handler.
    """

    snapshot_id: uuid.UUID
    period_key: str
    state: str
    cache_invalidation_receipts: list[dict[str, str]]
    trace_id: str


@dataclass(frozen=True)
class GetSnapshotResponse:
    """get_snapshot result envelope — service layer returns this."""

    period_key: str
    snapshot_id: uuid.UUID | None
    state: str | None
    committed_at: str | None
    trace_id: str


# ── Service layer ────────────────────────────────────────────
class SnapshotPersistenceService:
    """Story 11.3 — AD-20 verified → committed transition orchestrator."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        trace_id: str,
    ) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.trace_id = trace_id

    async def commit_snapshot(
        self,
        *,
        period_key: str,
        snapshot_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> CommitSnapshotPersistenceResponse:
        """AD-20 verified → committed transition.

        Steps:
        1. SELECT FOR UPDATE the fiscal_period_snapshots row.
        2. Run the pure kernel `validate_commit_snapshot_persistence`.
        3. If authorized: UPDATE state='committed' + committed_at=now().
        4. Audit-first emit `snapshot_persistence_committed` (CR 1.1).
        5. AD-25 multi-channel publish (4 channels via publish_multi).

        Idempotent no-op: if state='committed' already, skip the UPDATE
        and return idempotent_ok=True (CR 1.1 invariant).

        Raises:
            SnapshotAlreadyCommittedError: state='reversed' (terminal).
                Maps to 409 SNAPSHOT_ALREADY_COMMITTED.
        """
        # ── 1. SELECT FOR UPDATE ────────────────────────────────
        stmt = (
            select(FiscalPeriodSnapshot)
            .where(
                FiscalPeriodSnapshot.snapshot_id == snapshot_id,
                FiscalPeriodSnapshot.tenant_id == self.tenant_id,
            )
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        snapshot = result.scalar_one_or_none()
        if snapshot is None:
            # Snapshot not found — treated as terminal rejection (CR 1.1).
            raise SnapshotAlreadyCommittedError(
                tenant_id=self.tenant_id,
                snapshot_id=snapshot_id,
                period_key=period_key,
                current_state="not_found",
                trace_id=self.trace_id,
            )

        # ── 2. Pure kernel validation ──────────────────────────
        decision = validate_commit_snapshot_persistence(
            tenant_id=self.tenant_id,
            snapshot_id=snapshot_id,
            period_key=period_key,
            current_state=snapshot.state,
            actor_id=actor_id,
        )

        # ── 3a. Idempotent no-op (state='committed' already) ─────
        if decision.idempotent_ok:
            return CommitSnapshotPersistenceResponse(
                snapshot_id=snapshot_id,
                period_key=period_key,
                state="committed",
                cache_invalidation_receipts=[],
                trace_id=self.trace_id,
            )

        # ── 3b. Terminal rejection (state='reversed') ───────────
        if decision.terminal_rejected:
            raise SnapshotAlreadyCommittedError(
                tenant_id=self.tenant_id,
                snapshot_id=snapshot_id,
                period_key=period_key,
                current_state=snapshot.state,
                trace_id=self.trace_id,
            )

        # ── 3c. Non-committable rejection (state='draft') ───────
        if not decision.authorized:
            raise SnapshotAlreadyCommittedError(
                tenant_id=self.tenant_id,
                snapshot_id=snapshot_id,
                period_key=period_key,
                current_state=snapshot.state,
                trace_id=self.trace_id,
            )

        # ── 4. UPDATE state='committed' ─────────────────────────
        committed_at = datetime.now(tz=UTC)
        await self.session.execute(
            update(FiscalPeriodSnapshot)
            .where(FiscalPeriodSnapshot.snapshot_id == snapshot_id)
            .values(state="committed")
        )

        # ── 5. Audit-first emit (CR 1.1) ───────────────────────
        # A5 forward-lock: validate action via _ActionRegistry BEFORE
        # emit_audit call (fail-fast — Story 11.3 wire).
        from apps.api.core.audit_action import ActionClass, _ActionRegistry

        _ActionRegistry.validate(
            action_class=ActionClass.SNAPSHOT_PERSISTENCE,
            action="snapshot_persistence_committed",
        )
        await emit_audit(
            self.session,
            actor_id=actor_id,
            action="snapshot_persistence_committed",
            target_table="fiscal_period_snapshots",
            target_id=snapshot_id,
            tenant_id=self.tenant_id,
            payload={
                "period_key": period_key,
                "from_state": "verified",
                "to_state": "committed",
                "baseline_revision": snapshot.baseline_revision,
                "engine_type": snapshot.engine_type,
            },
        )

        # ── 6. AD-25 multi-channel publish ─────────────────────
        publisher = CacheInvalidationPublisher()
        receipts = publisher.publish_multi(
            channels=list(SNAPSHOT_COMMIT_CHANNELS),
            tenant_id=self.tenant_id,
            event_id=snapshot_id,
            correction_group_id=snapshot_id,  # use snapshot_id as cgroup for AD-25 self-correction tracking
            trace_id=self.trace_id,
            published_at=committed_at.isoformat(),
        )
        receipt_dicts = [
            CacheInvalidationPublisher.receipt_to_dict(r) for r in receipts
        ]

        return CommitSnapshotPersistenceResponse(
            snapshot_id=snapshot_id,
            period_key=period_key,
            state="committed",
            cache_invalidation_receipts=receipt_dicts,
            trace_id=self.trace_id,
        )

    async def get_snapshot(
        self,
        *,
        period_key: str,
    ) -> GetSnapshotResponse:
        """Read fiscal_period_snapshots state for the given period_key.

        Returns the most recent snapshot for the period (by created_at DESC).
        """
        stmt = (
            select(FiscalPeriodSnapshot)
            .where(
                FiscalPeriodSnapshot.tenant_id == self.tenant_id,
                FiscalPeriodSnapshot.period_key == period_key,
            )
            .order_by(FiscalPeriodSnapshot.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        snapshot = result.scalar_one_or_none()
        if snapshot is None:
            return GetSnapshotResponse(
                period_key=period_key,
                snapshot_id=None,
                state=None,
                committed_at=None,
                trace_id=self.trace_id,
            )
        return GetSnapshotResponse(
            period_key=period_key,
            snapshot_id=snapshot.snapshot_id,
            state=snapshot.state,
            committed_at=(
                snapshot.created_at.isoformat()
                if snapshot.state == "committed"
                else None
            ),
            trace_id=self.trace_id,
        )


__all__ = [
    "ALLOWED_CHANNELS",
    "CommitSnapshotPersistenceResponse",
    "GetSnapshotResponse",
    "SNAPSHOT_COMMIT_CHANNELS",
    "SnapshotPersistenceService",
]
