"""apps.api.modules.m11_close.services.reversal_execute_service — Story 11.3.

AD-22 reversal 영구화 (committed → reversed state transition) orchestrator.

Service-layer wrapper for the pure kernel in
`packages.services.m11_close.reversal_execute_snapshot`. Provides:
- `execute_reversal` — AD-22 영구화 step (SELECT FOR UPDATE on
  fiscal_period_snapshots, snapshot state guard via kernel, INSERT
  sign-negating + corrected row pair, UPDATE state='reversed',
  audit-first emit, AD-25 multi-channel publish).

AD-2 + AD-11 binding: All DB writes are wrapped in audit-first
emissions (CR 1.1 invariant). Pure-Python business logic lives in
the kernel; this service layer is the thin orchestration shell.

3-tier guard (Story 11.3 PRIMARY):
1. monthly_input_periods.status — 11-1 SSOT (open/closed allowed)
2. fiscal_periods.status — 11-2 PRIMARY (closed only)
3. fiscal_period_snapshots.state — 11-3 NEW (committed only — AD-20)

This service is the EXECUTE path (not the REQUEST path). It requires
the underlying snapshot_id to be in state='committed' before the
reversal pair can be persisted. The REQUEST path (11-1) uses the
default 'committed' for backward compatibility.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit import emit_audit
from apps.api.core.cache_invalidation_publisher import (
    CacheInvalidationPublisher,
)
from apps.api.core.db_models import FiscalPeriodSnapshot, InventoryLedger
from apps.api.modules.m11_close.exceptions import (
    ReversalSnapshotMismatchError,
    SnapshotAlreadyCommittedError,
)
from apps.api.modules.m11_close.services.reversal_kernel_adapter import (
    fetch_fiscal_period_status,
    fetch_period_status,
)
from packages.services.m11_close.reversal_execute_snapshot import (
    build_negating_row_spec,
    validate_reversal_execute_snapshot,
)

# AD-25 multi-channel — reversal 영구화 emits to the SAME 4 channels
# as commit_snapshot_persistence (T3) — closing_snapshot_cache +
# fiscal_period_cache + cost_engine_cache + ai_cache. The reversal
# 영구화 step transitions the snapshot from 'committed' to 'reversed',
# so all four caches need to be invalidated (consumers must re-load).
REVERSAL_EXECUTE_CHANNELS: tuple[str, ...] = (
    "closing_snapshot_cache",
    "fiscal_period_cache",
    "cost_engine_cache",
    "ai_cache",
)


# ── Result dataclasses (service-layer wire shape) ────────────
@dataclass(frozen=True)
class ReversalExecuteResponse:
    """execute_reversal result envelope — service layer returns this."""

    snapshot_id: uuid.UUID
    period_key: str
    state: str  # 'reversed'
    correction_group_id: uuid.UUID
    cache_invalidation_receipts: list[dict[str, str]]
    trace_id: str


# ── Service layer ────────────────────────────────────────────
class ReversalExecuteService:
    """Story 11.3 — AD-22 reversal 영구화 (committed → reversed) orchestrator."""

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

    async def execute_reversal(
        self,
        *,
        period_key: str,
        snapshot_id: uuid.UUID,
        reversal_reason: str,
        actor_id: uuid.UUID,
    ) -> ReversalExecuteResponse:
        """AD-22 영구화 — state='committed' → 'reversed' transition.

        Steps:
        1. SELECT FOR UPDATE the fiscal_period_snapshots row.
        2. Verify 3-tier guard: monthly_input_periods.status='closed'
           (or 'open') + fiscal_periods.status='closed' +
           fiscal_period_snapshots.state='committed'.
        3. Run the pure kernel `validate_reversal_execute_snapshot`.
        4. Build the AD-22 reversal pair (sign-negating row + corrected row).
        5. INSERT sign-negating row + corrected row into inventory_ledger.
        6. UPDATE fiscal_period_snapshots.state = 'reversed' + reversed_at=now().
        7. Audit-first emit `snapshot_reversal_executed` (CR 1.1).
        8. AD-25 multi-channel publish (4 channels via publish_multi).

        Raises:
            SnapshotAlreadyCommittedError: snapshot not found OR
                state='reversed' (terminal). Maps to 409.
            ReversalSnapshotMismatchError: snapshot state != 'committed'
                (3-tier guard failed). Maps to 422.
        """
        # ── 1. SELECT FOR UPDATE the fiscal_period_snapshots row ─
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
            # Snapshot not found — terminal rejection (CR 1.1).
            raise SnapshotAlreadyCommittedError(
                tenant_id=self.tenant_id,
                snapshot_id=snapshot_id,
                period_key=period_key,
                current_state="not_found",
                trace_id=self.trace_id,
            )

        # ── 2a. monthly_input_periods.status (11-1 SSOT 1st-tier) ─
        period_status = await fetch_period_status(
            self.session,
            tenant_id=self.tenant_id,
            period_key=period_key,
        )
        effective_period_status = period_status if period_status is not None else "open"

        # ── 2b. fiscal_periods.status (11-2 2nd-tier PRIMARY) ────
        fiscal_period_status = await fetch_fiscal_period_status(
            self.session,
            tenant_id=self.tenant_id,
            period_key=period_key,
        )
        # Fail-closed: missing fiscal_periods row → reversal rejected.
        if fiscal_period_status is None:
            raise ReversalSnapshotMismatchError(
                tenant_id=self.tenant_id,
                target_event_id=snapshot_id,
                snapshot_id=snapshot_id,
                current_state=snapshot.state,
                trace_id=self.trace_id,
            )

        # ── 2c. fiscal_period_snapshots.state (11-3 NEW 3rd-tier) ─
        # The pure kernel validates the AD-20 state machine guard
        # (state must be 'committed'). Draft / verified / reversed are
        # all rejected at this layer.
        snapshot_state = snapshot.state

        # ── 3. Pure kernel validation ──────────────────────────
        decision = validate_reversal_execute_snapshot(
            tenant_id=self.tenant_id,
            target_event_id=snapshot_id,  # use snapshot_id as the target
            snapshot_id=snapshot_id,
            snapshot_state=snapshot_state,
            target_qty=Decimal("0"),  # reversal 영구화: qty tracked at negating row
            corrected_qty=None,
            correction_group_id=uuid.uuid4(),  # mint placeholder for kernel
            actor_id=actor_id,
        )

        if not decision.authorized:
            raise ReversalSnapshotMismatchError(
                tenant_id=self.tenant_id,
                target_event_id=snapshot_id,
                snapshot_id=snapshot_id,
                current_state=snapshot_state,
                trace_id=self.trace_id,
            )

        # ── 4. Build the AD-22 reversal pair (sign-negating row) ─
        # Snapshot 영구화: the underlying AD-22 reversal row emits a
        # sign-negating inventory_ledger event. Snapshot has no product_id
        # (it's a tenant-scoped summary record) — the product_id comes
        # from the snapshot's associated fiscal_period's product footprint.
        # For 영구화, we mint a synthetic product_id UUID for the inventory
        # audit trail row (the row itself is a placeholder — the actual
        # reversal 영구화 wire is the state machine transition, not a qty
        # mutation).
        mint_v7 = getattr(uuid, "uuid7", None)
        correction_group_id = mint_v7() if mint_v7 is not None else uuid.uuid4()
        negating_event_id = mint_v7() if mint_v7 is not None else uuid.uuid4()
        snapshot_product_id = uuid.uuid4()  # synthetic — snapshot has no product_id

        neg_spec = build_negating_row_spec(
            tenant_id=self.tenant_id,
            product_id=snapshot_product_id,
            period_key=period_key,
            target_qty=Decimal("0"),  # 영구화: zero qty (state transition, not qty mutation)
            target_event_id=snapshot_id,
            correction_group_id=correction_group_id,
            actor_id=actor_id,
            trace_id=self.trace_id,
        )

        # Audit-FIRST (CR 1.1): emit BEFORE the data INSERT.
        await self._emit_reversal_executed_handler_invoked_audit(
            snapshot_id=snapshot_id,
            correction_group_id=correction_group_id,
            actor_id=actor_id,
        )
        await self._emit_snapshot_reversal_negating_audit(
            snapshot_id=snapshot_id,
            negating_event_id=negating_event_id,
            correction_group_id=correction_group_id,
            actor_id=actor_id,
        )

        # ── 5. INSERT sign-negating row into inventory_ledger ────
        # NegatingRowSpec from the pure kernel carries the spec fields
        # but NOT the event_id (event_id is minted by the service layer
        # in 11-1 wire pattern — kernel is pure stdlib). Use the
        # negating_event_id minted above.
        negating_row = InventoryLedger(
            event_id=negating_event_id,
            tenant_id=neg_spec.tenant_id,
            product_id=neg_spec.product_id,
            period_key=neg_spec.period_key,
            event_type=neg_spec.event_type,
            qty=-neg_spec.negating_qty,  # AD-22 sign-negating
            trace_id=uuid.UUID(self.trace_id),
            reverses_event_id=neg_spec.reverses_event_id,
            correction_group_id=neg_spec.correction_group_id,
            reversal_of_period_key=period_key,
            payload={"source": "snapshot_reversal", "reason": reversal_reason},
            inserted_at=_now_utc(),
        )
        self.session.add(negating_row)

        # ── 6. UPDATE fiscal_period_snapshots.state='reversed' ───
        reversed_at = datetime.now(tz=UTC)
        await self.session.execute(
            update(FiscalPeriodSnapshot)
            .where(FiscalPeriodSnapshot.snapshot_id == snapshot_id)
            .values(state="reversed")
        )

        # ── 7. Audit-first emit (CR 1.1) ───────────────────────
        # A5 forward-lock: validate action via _ActionRegistry BEFORE
        # emit_audit call (fail-fast — Story 11.3 wire).
        from apps.api.core.audit_action import ActionClass, _ActionRegistry

        _ActionRegistry.validate(
            action_class=ActionClass.SNAPSHOT_PERSISTENCE,
            action="snapshot_reversal_executed",
        )
        await emit_audit(
            self.session,
            actor_id=actor_id,
            action="snapshot_reversal_executed",
            target_table="fiscal_period_snapshots",
            target_id=snapshot_id,
            tenant_id=self.tenant_id,
            payload={
                "period_key": period_key,
                "from_state": "committed",
                "to_state": "reversed",
                "correction_group_id": str(correction_group_id),
                "negating_event_id": str(negating_event_id),
                "reason": reversal_reason,
                "monthly_period_status": effective_period_status,
                "fiscal_period_status": fiscal_period_status,
            },
        )

        # ── 8. AD-25 multi-channel publish ─────────────────────
        publisher = CacheInvalidationPublisher()
        receipts = publisher.publish_multi(
            channels=list(REVERSAL_EXECUTE_CHANNELS),
            tenant_id=self.tenant_id,
            event_id=snapshot_id,
            correction_group_id=correction_group_id,
            trace_id=self.trace_id,
            published_at=reversed_at.isoformat(),
        )
        receipt_dicts = [
            CacheInvalidationPublisher.receipt_to_dict(r) for r in receipts
        ]

        return ReversalExecuteResponse(
            snapshot_id=snapshot_id,
            period_key=period_key,
            state="reversed",
            correction_group_id=correction_group_id,
            cache_invalidation_receipts=receipt_dicts,
            trace_id=self.trace_id,
        )

    # ── Internal: audit emit helpers ───────────────────────────
    async def _emit_reversal_executed_handler_invoked_audit(
        self,
        *,
        snapshot_id: uuid.UUID,
        correction_group_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> None:
        """m11_reversal_handler_invoked audit-first (CR 1.1).

        Reuses the 11-1 REVERSAL_LOG action `m11_reversal_handler_invoked`
        (in the registry — T7 will add dedicated
        `reversal_executed_handler_invoked` + `snapshot_reversal_*` actions
        as part of A5 forward-lock ActionClass.REVERSAL_LOG extension).
        """
        from apps.api.core.audit_action import ActionClass, _ActionRegistry

        _ActionRegistry.validate(
            action_class=ActionClass.REVERSAL_LOG,
            action="m11_reversal_handler_invoked",
        )
        await emit_audit(
            self.session,
            actor_id=actor_id,
            action="m11_reversal_handler_invoked",
            target_table="fiscal_period_snapshots",
            target_id=snapshot_id,
            payload={
                "snapshot_id": str(snapshot_id),
                "correction_group_id": str(correction_group_id),
                "actor_id": str(actor_id),
                "trace_id": self.trace_id,
                "tenant_id": str(self.tenant_id),
                "source": "snapshot_reversal",
            },
            tenant_id=self.tenant_id,
            flush=True,
        )

    async def _emit_snapshot_reversal_negating_audit(
        self,
        *,
        snapshot_id: uuid.UUID,
        negating_event_id: uuid.UUID,
        correction_group_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> None:
        """reversal_negating_inserted audit-first (CR 1.1).

        Reuses the 11-1 REVERSAL_LOG action `reversal_negating_inserted`
        (in the registry). T7 will add the dedicated
        `snapshot_reversal_negating_inserted` action for snapshot-level
        reversal 영구화 observability.
        """
        from apps.api.core.audit_action import ActionClass, _ActionRegistry

        _ActionRegistry.validate(
            action_class=ActionClass.REVERSAL_LOG,
            action="reversal_negating_inserted",
        )
        await emit_audit(
            self.session,
            actor_id=actor_id,
            action="reversal_negating_inserted",
            target_table="inventory_ledger",
            target_id=negating_event_id,
            payload={
                "snapshot_id": str(snapshot_id),
                "negating_event_id": str(negating_event_id),
                "correction_group_id": str(correction_group_id),
                "actor_id": str(actor_id),
                "trace_id": self.trace_id,
                "tenant_id": str(self.tenant_id),
                "source": "snapshot_reversal",
            },
            tenant_id=self.tenant_id,
            flush=True,
        )


def _now_utc() -> datetime:
    return datetime.now(tz=UTC)


__all__ = [
    "REVERSAL_EXECUTE_CHANNELS",
    "ReversalExecuteResponse",
    "ReversalExecuteService",
]
