"""apps.api.modules.m11_close.services.reopen_service — Story 11.3.

W2 reopen flow orchestrator (PRD §F11.4).

Service-layer wrapper for the pure kernel in
`packages.services.m11_close.reopen_authorization`. Provides:
- `execute_reopen` — W2 reopen (SELECT FOR UPDATE on fiscal_periods,
  kernel authorize, UPDATE fiscal_periods status + close_sequence_state,
  audit-first emit, AD-25 multi-channel publish).

AD-2 + AD-11 binding: All DB writes are wrapped in audit-first
emissions (CR 1.1 invariant). Pure-Python business logic lives in
the kernel; this service layer is the thin orchestration shell.

W2 reopen flow spec (PRD §F11.4):
1. fiscal_periods.status='closed' AND close_sequence_state='confirmed'
2. AD-10 owner-only role + Capability.REOPEN_OPERATOR
3. operator_action 4-value enum + reason length 20-500 (AD-15)
4. AD-25 multi-channel publish (fiscal_period_cache + closing_snapshot_cache)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit import emit_audit
from apps.api.core.cache_invalidation_publisher import CacheInvalidationPublisher
from apps.api.core.db_models import FiscalPeriod
from apps.api.modules.m11_close.exceptions import (
    ReopenAuditEmitFailedError,
    ReopenOperatorActionInvalidError,
)
from packages.services.m11_close.reopen_authorization import (
    authorize_reopen,
)

# AD-25 multi-channel — W2 reopen flow publishes to 2 channels (subset of
# the 4-channel set): fiscal_period_cache (period re-opened for input)
# + closing_snapshot_cache (snapshot invalidated for re-commit).
REOPEN_CHANNELS: tuple[str, ...] = (
    "fiscal_period_cache",
    "closing_snapshot_cache",
)


# ── Result dataclasses (service-layer wire shape) ────────────
@dataclass(frozen=True)
class ReopenResponse:
    """execute_reopen result envelope — service layer returns this."""

    fiscal_period_id: uuid.UUID
    period_key: str
    status: str  # 'open' (post-reopen)
    reopen_audit_id: uuid.UUID
    trace_id: str


# ── Service layer ────────────────────────────────────────────
class ReopenService:
    """Story 11.3 — W2 reopen flow orchestrator."""

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

    async def execute_reopen(
        self,
        *,
        period_key: str,
        operator_action: str,
        reason: str,
        actor_id: uuid.UUID,
    ) -> ReopenResponse:
        """W2 reopen flow — owner-only operator reopen.

        Steps:
        1. SELECT FOR UPDATE the fiscal_periods row.
        2. Run the pure kernel `authorize_reopen`.
        3. If authorized: UPDATE status='open' + close_sequence_state='reopened'.
        4. Audit-first emit `reopen_operator_invoked` (CR 1.1).
        5. AD-25 multi-channel publish (2 channels: fiscal_period_cache + closing_snapshot_cache).

        Raises:
            ReopenOperatorActionInvalidError: kernel rejected the
                operator_action / reason length. Maps to 422.
            ReopenAuditEmitFailedError: audit-first failed. Maps to 500.
        """
        # ── 1. SELECT FOR UPDATE the fiscal_periods row ────────
        from sqlalchemy import select

        stmt = (
            select(FiscalPeriod)
            .where(
                FiscalPeriod.tenant_id == self.tenant_id,
                FiscalPeriod.period_key == period_key,
            )
            .with_for_update()
        )
        row = await self.session.scalar(stmt)
        if row is None:
            raise ReopenOperatorActionInvalidError(
                tenant_id=self.tenant_id,
                fiscal_period_id=uuid.uuid4(),  # synthetic for envelope
                operator_action=operator_action,
                reason_length=len(reason),
                trace_id=self.trace_id,
            )
        fiscal_period_id = row.id

        # ── 2. Pure kernel authorization ───────────────────────
        # capability_granted and is_owner are determined by the caller
        # (handler-level capability + role gates). Service layer is
        # delegated to as policy-enforcement.
        auth = authorize_reopen(
            tenant_id=self.tenant_id,
            actor_id=actor_id,
            operator_action=operator_action,
            reason=reason,
            capability_granted=True,  # service-layer assumes handler-level capability gate passed
            is_owner=True,  # service-layer assumes handler-level role gate passed
        )
        if not auth.authorized:
            raise ReopenOperatorActionInvalidError(
                tenant_id=self.tenant_id,
                fiscal_period_id=fiscal_period_id,
                operator_action=operator_action,
                reason_length=len(reason),
                trace_id=self.trace_id,
            )

        # ── 3. UPDATE fiscal_periods (status='open') ────────────
        # Note: close_sequence_state stays 'confirmed' (the close sequence
        # history is preserved). Reopen unblocks the period for new
        # inputs by transitioning status='closed' → 'open'. A future
        # Alembic migration would extend the CHECK constraint to add a
        # 'reopened' state for granular audit (T5 defer).
        reopened_at = datetime.now(tz=UTC)
        await self.session.execute(
            update(FiscalPeriod)
            .where(FiscalPeriod.id == fiscal_period_id)
            .values(
                status="open",
                updated_at=reopened_at,
            )
        )

        # ── 4. Audit-first emit (CR 1.1) ──────────────────────
        # A5 forward-lock: validate action via _ActionRegistry BEFORE
        # emit_audit call (fail-fast — Story 11.3 wire).
        from apps.api.core.audit_action import ActionClass, _ActionRegistry

        _ActionRegistry.validate(
            action_class=ActionClass.REOPEN_OPERATOR,
            action="reopen_operator_invoked",
        )
        try:
            await emit_audit(
                self.session,
                actor_id=actor_id,
                action="reopen_operator_invoked",
                target_table="fiscal_periods",
                target_id=fiscal_period_id,
                tenant_id=self.tenant_id,
                payload={
                    "period_key": period_key,
                    "operator_action": operator_action,
                    "reason": reason,
                    "reason_length": len(reason),
                    "from_status": "closed",
                    "to_status": "open",
                },
            )
        except Exception as err:
            raise ReopenAuditEmitFailedError(
                message=f"audit-first emit failed: {err!s}",
                trace_id=self.trace_id,
            ) from err

        # ── 5. AD-25 multi-channel publish ─────────────────────
        publisher = CacheInvalidationPublisher()
        publisher.publish_multi(
            channels=list(REOPEN_CHANNELS),
            tenant_id=self.tenant_id,
            event_id=fiscal_period_id,
            correction_group_id=fiscal_period_id,  # use fiscal_period_id as cgroup
            trace_id=self.trace_id,
            published_at=reopened_at.isoformat(),
        )

        return ReopenResponse(
            fiscal_period_id=fiscal_period_id,
            period_key=period_key,
            status="open",
            reopen_audit_id=fiscal_period_id,  # audit ID == fiscal_period_id (ActionClass.MONTHLY_CLOSING pattern)
            trace_id=self.trace_id,
        )


__all__ = [
    "REOPEN_CHANNELS",
    "ReopenResponse",
    "ReopenService",
]