"""apps.api.modules.m11_close.services.reversal_service — Story 11.1 PRIMARY.

AD-22 reversal sequence orchestrator (M11 module authority).

Service-layer wrapper for the M11 pure kernels in
`packages/services/m11_close/`. Provides:
- `execute_reversal` — AD-22 9-step sequence (SELECT target, authorize,
  sign-negating INSERT, optional corrected INSERT, AD-25 publish,
  audit-first emit). All inside one REPEATABLE READ transaction
  (4-2 wire pattern).
- `get_reversal_history` — observability for reversal pairs.
- `reject_reversal` — M11 reject path (audit emit + raise).

AD-22 sequence:
1. SELECT target_event FROM inventory_ledger (RLS-scoped)
2. SELECT period_status FROM monthly_input_periods
3. authorize_reversal decision
4. correction_group_id mint (uuid7 fallback uuid4)
5. sign-negating row INSERT
6. corrected row INSERT (optional)
7. AD-25 publisher publish (channel='ai_cache')
8. audit-first INSERT to reversal_log + audit_logs (CR 1.1)
9. COMMIT (atomic transaction)
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, NamedTuple

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit import emit_audit
from apps.api.core.cache_invalidation_publisher import (
    CacheInvalidationPublisher,
)
from apps.api.core.db_models import InventoryLedger
from apps.api.modules.m11_close.services.reversal_kernel_adapter import (
    dispatch_build_reversal_corrected,
    dispatch_build_reversal_negating,
    fetch_fiscal_period_status,
    fetch_period_status,
    fetch_target_event,
)
from packages.services.m4_inventory.ledger import InventoryLedgerEvent
from packages.services.m11_close.reversal_authorization import (
    authorize_reversal,
)
from packages.services.m11_close.reversal_corrected import (
    ReversalCorrectedEvent,
)

# ── Concurrency constants (ECH #12-14) ───────────────────────
# AD-4 REPEATABLE READ: prevents concurrent reversal requests from
# racing past the (tenant_id, reverses_event_id) UNIQUE INDEX check.
# PG error code 40001 = serialization_failure (caller is expected to retry).
_RETRY_BACKOFF_MS: tuple[int, ...] = (50, 100, 200)
_PG_SERIALIZATION_FAILURE: str = "40001"


# ── Typed exceptions (AD-15 §4 envelope) ────────────────────
class ReversalTargetNotFoundError(Exception):
    """404 REVERSAL_TARGET_NOT_FOUND — target_event_id not found in tenant."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        target_event_id: uuid.UUID,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"target event_id={target_event_id} not found for tenant={tenant_id}"
        )
        self.tenant_id = tenant_id
        self.target_event_id = target_event_id
        self.trace_id = trace_id


class ReversalRejectedError(Exception):
    """403 REVERSAL_REJECTED — capability/period gate rejected."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        target_event_id: uuid.UUID,
        reason_ko: str,
        trace_id: str,
    ) -> None:
        super().__init__(reason_ko)
        self.tenant_id = tenant_id
        self.target_event_id = target_event_id
        self.reason_ko = reason_ko
        self.trace_id = trace_id


class ReversalUnauthorizedError(Exception):
    """403 REVERSAL_UNAUTHORIZED — caller is not the actor or role mismatch."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID,
        target_event_id: uuid.UUID,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"actor_id={actor_id} unauthorized for reversal of event_id={target_event_id}"
        )
        self.tenant_id = tenant_id
        self.actor_id = actor_id
        self.target_event_id = target_event_id
        self.trace_id = trace_id


class ReversalDuplicateError(Exception):
    """422 REVERSAL_DUPLICATE — (tenant_id, reverses_event_id) unique violation."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        target_event_id: uuid.UUID,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"event_id={target_event_id} has already been reversed"
        )
        self.tenant_id = tenant_id
        self.target_event_id = target_event_id
        self.trace_id = trace_id


class LockedPeriodReversalRejectedError(Exception):
    """422 LOCKED_PERIOD_REVERSAL_REJECTED — period_status='locked'."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        target_event_id: uuid.UUID,
        period_key: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"period {period_key} is locked; reversal of event_id={target_event_id} rejected"
        )
        self.tenant_id = tenant_id
        self.target_event_id = target_event_id
        self.period_key = period_key
        self.trace_id = trace_id


# ── ReversalResponse ────────────────────────────────────────
class ReversalResponse(NamedTuple):
    """Wire response shape for `POST /api/v1/close/reversal-requests`."""

    correction_group_id: uuid.UUID
    negating_event_id: uuid.UUID
    corrected_event_id: uuid.UUID | None
    target_event_id: uuid.UUID
    reversal_history: list[dict[str, Any]]
    trace_id: str
    cache_invalidation_receipt: dict[str, str]


# ── ReversalService ──────────────────────────────────────────
class ReversalService:
    """Story 11.1 — AD-22 reversal sequence orchestrator (M11 module authority)."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        industry: Any | None,
        trace_id: str,
    ) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.industry = industry
        self.trace_id = trace_id
        self._publisher = CacheInvalidationPublisher()

    # ── Operation 1: execute_reversal (AD-22 9-step sequence) ──
    async def execute_reversal(
        self,
        *,
        target_event_id: uuid.UUID,
        reason: str,
        actor_id: uuid.UUID,
        capability_granted: bool,
        corrected_qty: Decimal | None = None,
        corrected_period_key: str | None = None,
    ) -> ReversalResponse:
        """AD-22 sequence orchestrator. See module docstring for the 9 steps.

        Wrapped in a 40001 serialization-failure retry loop (3x exponential
        backoff: 50ms / 100ms / 200ms) — ECH #12-14. The inner body sets
        REPEATABLE READ isolation at transaction start so concurrent reversal
        requests serialize on the (tenant_id, reverses_event_id) PARTIAL UNIQUE
        INDEX.

        Args:
            target_event_id: inventory_ledger.event_id to reverse.
            reason: User-provided justification (Korean OK, audited).
            actor_id: UUID of the reversal initiator.
            capability_granted: Whether the tenant has Capability.REVERSAL_REQUEST.
            corrected_qty: Optional corrected qty (AD-22 sequence step 2).
            corrected_period_key: Optional corrected period key.

        Returns:
            ReversalResponse with correction_group_id + negating_event_id
            + corrected_event_id + reversal history + cache receipt.

        Raises:
            ReversalTargetNotFoundError: target_event_id not found.
            ReversalRejectedError: capability / period gate rejected.
            LockedPeriodReversalRejectedError: period_status='locked'.
            ReversalDuplicateError: (tenant_id, reverses_event_id) UNIQUE
                constraint violated (re-reversal).
            ReversalNegatingBuildError: pure kernel constraint violated.
            ReversalCorrectedBuildError: corrected row constraint violated.
        """
        # ECH #12-14: 40001 serialization_failure retry (3x exponential backoff).
        attempt = 0
        while True:
            try:
                return await self._execute_reversal_inner(
                    target_event_id=target_event_id,
                    reason=reason,
                    actor_id=actor_id,
                    capability_granted=capability_granted,
                    corrected_qty=corrected_qty,
                    corrected_period_key=corrected_period_key,
                )
            except DBAPIError as err:
                if not _is_serialization_failure(err):
                    raise
                if attempt >= len(_RETRY_BACKOFF_MS):
                    # Exhausted retries — re-raise.
                    raise
                await asyncio.sleep(_RETRY_BACKOFF_MS[attempt] / 1000.0)
                attempt += 1
                # Drain session so retry starts clean.
                await self.session.rollback()

    async def _execute_reversal_inner(
        self,
        *,
        target_event_id: uuid.UUID,
        reason: str,
        actor_id: uuid.UUID,
        capability_granted: bool,
        corrected_qty: Decimal | None,
        corrected_period_key: str | None,
    ) -> ReversalResponse:
        """Inner body of execute_reversal — runs inside the 40001 retry loop.

        Sets REPEATABLE READ isolation at transaction start (AD-4). All
        audit emits happen BEFORE the corresponding data INSERT (CR 1.1
        audit-first).
        """
        trace_id_uuid = uuid.UUID(self.trace_id)

        # AD-4 REPEATABLE READ: explicit transaction isolation. Combined
        # with SELECT FOR UPDATE on the target row (already in
        # `fetch_target_event`), this prevents two concurrent reversal
        # requests from both passing the existence check and both
        # INSERTing a negating row.
        await self.session.execute(
            text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        )

        # (1) SELECT target_event FROM inventory_ledger (RLS-scoped).
        target_event = await fetch_target_event(
            self.session,
            tenant_id=self.tenant_id,
            target_event_id=target_event_id,
        )
        if target_event is None:
            raise ReversalTargetNotFoundError(
                tenant_id=self.tenant_id,
                target_event_id=target_event_id,
                trace_id=self.trace_id,
            )

        # (2) SELECT period_status FROM monthly_input_periods.
        period_status = await fetch_period_status(
            self.session,
            tenant_id=self.tenant_id,
            period_key=target_event.period_key,
        )
        # period_status None (period not initialized) → treat as 'open'.
        effective_period_status = period_status if period_status is not None else "open"

        # Story 11.2 PRIMARY guard — fetch fiscal_periods.status (AD-6).
        # 3rd-sweep fix (AC#6(a) flipped semantics): reversal is permitted
        # ONLY when fiscal_periods.status='closed' (closed-period reversal
        # pattern). Missing fiscal_periods row → no period has been initiated
        # → reversal is NOT permitted (fail-closed). Once the 4-stage close
        # sequence reaches 'confirmed', reversals route through the dedicated
        # AD-22 reversal endpoints (which themselves gate on this status).
        # fetch_fiscal_period_status is a lightweight SELECT (one row, indexed
        # on tenant_period_unique).
        fiscal_period_status = await fetch_fiscal_period_status(
            self.session,
            tenant_id=self.tenant_id,
            period_key=target_event.period_key,
        )
        # Missing fiscal_periods row → reversal rejected (fail-closed).
        # Story 11.2 3rd-sweep: do NOT default to "open" — this would allow
        # reversal before any close has been initiated, which violates
        # AD-22 reverse-direction semantics.
        if fiscal_period_status is None:
            await self._emit_reversal_rejected_audit(
                target_event=target_event,
                actor_id=actor_id,
                reason_ko="마감 시퀀스가 시작되지 않은 기간 — 역분개 불가",
            )
            raise ReversalTargetNotFoundError(
                tenant_id=self.tenant_id,
                target_event_id=target_event_id,
                trace_id=self.trace_id,
            )
        effective_fiscal_period_status = fiscal_period_status

        # (3) authorize_reversal decision — Story 11.2 dual guard.
        auth = authorize_reversal(
            tenant_id=self.tenant_id,
            target_event=target_event,
            actor_id=actor_id,
            period_status=effective_period_status,
            capability_granted=capability_granted,
            fiscal_period_status=effective_fiscal_period_status,
        )
        if not auth.authorized:
            # Audit-first rejection (CR 1.1 lesson).
            await self._emit_reversal_rejected_audit(
                target_event=target_event,
                actor_id=actor_id,
                reason_ko=auth.reject_reason_ko or "M11 모듈 권한 거부",
            )
            # 422 for locked-period (different from 403 capability reject).
            # Story 11.2 dispatch: BOTH monthly_input_periods.status='locked'
            # AND fiscal_periods.status IN ('open', 'closing', 'reversed')
            # trigger LockedPeriodReversalRejectedError (AD-6 close lock +
            # closed-period reversal pattern). Only 'closed' is allowed.
            if effective_period_status == "locked" or effective_fiscal_period_status in (
                "open",
                "closing",
                "reversed",
            ):
                raise LockedPeriodReversalRejectedError(
                    tenant_id=self.tenant_id,
                    target_event_id=target_event_id,
                    period_key=target_event.period_key,
                    trace_id=self.trace_id,
                )
            raise ReversalRejectedError(
                tenant_id=self.tenant_id,
                target_event_id=target_event_id,
                reason_ko=auth.reject_reason_ko or "M11 모듈 권한 거부",
                trace_id=self.trace_id,
            )

        # (4) correction_group_id mint (uuid7 fallback uuid4).
        mint_v7 = getattr(uuid, "uuid7", None)
        correction_group_id = mint_v7() if mint_v7 is not None else uuid.uuid4()
        negating_event_id = mint_v7() if mint_v7 is not None else uuid.uuid4()
        corrected_event_id = (
            mint_v7() if mint_v7 is not None else uuid.uuid4()
        ) if (corrected_qty is not None and corrected_period_key is not None) else None

        # (5) sign-negating row INSERT (T1.1 pure kernel).
        negating_event = dispatch_build_reversal_negating(
            target_event=target_event,
            reason=reason,
            actor_id=actor_id,
            correction_group_id=correction_group_id,
            trace_id=trace_id_uuid,
            event_id=negating_event_id,
        )

        # Audit-FIRST (CR 1.1): m11_reversal_handler_invoked + reversal_negating_inserted
        # BEFORE the data INSERT.
        await self._emit_reversal_handler_invoked_audit(
            target_event=target_event,
            actor_id=actor_id,
            correction_group_id=correction_group_id,
        )
        await self._emit_reversal_negating_inserted_audit(
            target_event=target_event,
            negating_event_id=negating_event.event_id,
            correction_group_id=correction_group_id,
            actor_id=actor_id,
            trace_id_uuid=trace_id_uuid,
        )

        # INSERT sign-negating row.
        negating_row = InventoryLedger(
            event_id=negating_event.event_id,
            tenant_id=negating_event.tenant_id,
            product_id=negating_event.product_id,
            period_key=negating_event.period_key,
            event_type=negating_event.event_type,
            qty=negating_event.qty,
            trace_id=negating_event.trace_id,
            reverses_event_id=negating_event.reverses_event_id,
            correction_group_id=negating_event.correction_group_id,
            reversal_of_period_key=negating_event.reversal_of_period_key,
            payload=negating_event.payload,
            inserted_at=_now_utc(),
        )
        self.session.add(negating_row)
        try:
            await self.session.flush()
        except IntegrityError as err:
            # DB CHECK constraint violation — likely the (tenant_id, reverses_event_id)
            # PARTIAL UNIQUE INDEX (re-reversal attempt).
            await self._emit_reversal_rejected_audit(
                target_event=target_event,
                actor_id=actor_id,
                reason_ko="이미 역분개된 행",
            )
            await self.session.rollback()
            raise ReversalDuplicateError(
                tenant_id=self.tenant_id,
                target_event_id=target_event_id,
                trace_id=self.trace_id,
            ) from err

        # (6) corrected row INSERT (optional).
        corrected_event: ReversalCorrectedEvent | None = None
        if corrected_qty is not None and corrected_period_key is not None:
            corrected_event = dispatch_build_reversal_corrected(
                target_event=target_event,
                correction_group_id=correction_group_id,
                corrected_qty=corrected_qty,
                corrected_period_key=corrected_period_key,
                actor_id=actor_id,
                trace_id=trace_id_uuid,
                event_id=corrected_event_id,
            )

        if corrected_event is not None:
            # Audit-FIRST (CR 1.1): reversal_corrected_inserted BEFORE INSERT.
            await self._emit_reversal_corrected_inserted_audit(
                target_event=target_event,
                corrected_event=corrected_event,
                correction_group_id=correction_group_id,
                actor_id=actor_id,
            )

            corrected_row = InventoryLedger(
                event_id=corrected_event.event_id,
                tenant_id=corrected_event.tenant_id,
                product_id=corrected_event.product_id,
                period_key=corrected_event.period_key,
                event_type=corrected_event.event_type,
                qty=corrected_event.qty,
                trace_id=corrected_event.trace_id,
                reverses_event_id=corrected_event.reverses_event_id,
                correction_group_id=corrected_event.correction_group_id,
                reversal_of_period_key=corrected_event.reversal_of_period_key,
                payload=corrected_event.payload,
                inserted_at=_now_utc(),
            )
            self.session.add(corrected_row)
            try:
                await self.session.flush()
            except IntegrityError as err:
                await self.session.rollback()
                raise ReversalDuplicateError(
                    tenant_id=self.tenant_id,
                    target_event_id=target_event_id,
                    trace_id=self.trace_id,
                ) from err

        # (7) AD-25 publisher publish (channel='ai_cache').
        receipt = self._publisher.publish(
            channel="ai_cache",
            tenant_id=self.tenant_id,
            event_id=target_event_id,
            correction_group_id=correction_group_id,
            trace_id=self.trace_id,
        )
        receipt_dict = CacheInvalidationPublisher.receipt_to_dict(receipt)

        # Audit-first: cache invalidation receipt into audit_logs.
        await self._emit_cache_invalidation_audit(
            receipt_dict=receipt_dict,
            actor_id=actor_id,
        )

        # (8) Audit-first INSERT to reversal_log via audit_logs.
        # Done above via _emit_reversal_negating_inserted_audit +
        # _emit_reversal_corrected_inserted_audit (ActionClass.REVERSAL_LOG).

        # (9) COMMIT — atomic transaction. Caller is responsible for
        # committing the session.

        # Build reversal history for the response.
        reversal_history = await self._fetch_reversal_rows(
            correction_group_id=correction_group_id,
        )

        return ReversalResponse(
            correction_group_id=correction_group_id,
            negating_event_id=negating_event.event_id,
            corrected_event_id=corrected_event.event_id if corrected_event else None,
            target_event_id=target_event.event_id,
            reversal_history=reversal_history,
            trace_id=self.trace_id,
            cache_invalidation_receipt=receipt_dict,
        )

    # ── Operation 2: get_reversal_history (CR 1.1 observability) ─
    async def get_reversal_history(
        self,
        *,
        correction_group_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        """Read reversal pair (sign-negating + corrected) by correction_group_id."""
        return await self._fetch_reversal_rows(
            correction_group_id=correction_group_id,
        )

    # ── Operation 3: reject_reversal (M11 reject path) ─────────
    async def reject_reversal(
        self,
        *,
        target_event_id: uuid.UUID,
        reason: str,
        actor_id: uuid.UUID,
    ) -> None:
        """Audit emit + raise ReversalRejectedError for caller-driven reject."""
        # Build a placeholder target_event for audit attribution.
        target_event = await fetch_target_event(
            self.session,
            tenant_id=self.tenant_id,
            target_event_id=target_event_id,
        )
        await self._emit_reversal_rejected_audit(
            target_event=target_event,
            actor_id=actor_id,
            reason_ko=reason,
        )
        raise ReversalRejectedError(
            tenant_id=self.tenant_id,
            target_event_id=target_event_id,
            reason_ko=reason,
            trace_id=self.trace_id,
        )

    # ── Internal: audit emit helpers ───────────────────────────
    async def _emit_reversal_handler_invoked_audit(
        self,
        *,
        target_event: InventoryLedgerEvent | None,
        actor_id: uuid.UUID,
        correction_group_id: uuid.UUID,
    ) -> None:
        """m11_reversal_handler_invoked audit-first (pre-check 통과 시점).

        Routes to audit_logs (the bookkeeping table) via emit_audit.
        The reversal_log destination is INSERTed by the reversal_service
        itself (not via emit_audit_typed — that helper only handles
        audit_logs + calc_log destinations).
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
            target_table="reversal_log",
            target_id=correction_group_id,
            payload={
                "correction_group_id": str(correction_group_id),
                "target_event_id": (
                    str(target_event.event_id) if target_event else None
                ),
                "actor_id": str(actor_id),
                "trace_id": self.trace_id,
                "tenant_id": str(self.tenant_id),
                "source": "reversal_request",
            },
            tenant_id=self.tenant_id,
            flush=True,
        )

    async def _emit_inventory_ledger_audit(
        self,
        *,
        action: str,
        event_id: uuid.UUID,
        payload: dict[str, Any],
        actor_id: uuid.UUID,
    ) -> None:
        """inventory_ledger audit emit (A5 forward-lock).

        Routes to audit_logs via emit_audit. The inventory_ledger
        destination is INSERTed by the LedgerService itself (not via
        emit_audit_typed — that helper only handles audit_logs +
        calc_log destinations).
        """
        from apps.api.core.audit_action import ActionClass, _ActionRegistry

        _ActionRegistry.validate(
            action_class=ActionClass.INVENTORY_LEDGER,
            action=action,
        )
        await emit_audit(
            self.session,
            actor_id=actor_id,
            action=action,
            target_table="inventory_ledger",
            target_id=event_id,
            payload={
                **payload,
                "trace_id": self.trace_id,
                "tenant_id": str(self.tenant_id),
            },
            tenant_id=self.tenant_id,
            flush=True,
        )

    async def _emit_cache_invalidation_audit(
        self,
        *,
        receipt_dict: dict[str, str],
        actor_id: uuid.UUID,
    ) -> None:
        """AD-25 cache invalidation receipt → audit_logs (ActionClass.SYSTEM)."""
        await emit_audit(
            self.session,
            actor_id=actor_id,
            action="cache_invalidation_published",
            target_table="system",
            target_id=uuid.UUID(receipt_dict["correction_group_id"]),
            payload={
                **receipt_dict,
                "actor_id": str(actor_id),
                "source": "m11_reversal",
            },
            tenant_id=self.tenant_id,
            flush=True,
        )

    async def _emit_reversal_rejected_audit(
        self,
        *,
        target_event: InventoryLedgerEvent | None,
        actor_id: uuid.UUID,
        reason_ko: str,
    ) -> None:
        """Audit emit on reversal rejection (capability / period / duplicate).

        Uses ActionClass.REVERSAL_LOG → `reversal_rejected` (D3 R4 triage).
        Routes to audit_logs via emit_audit (the bookkeeping table).
        """
        from apps.api.core.audit_action import ActionClass, _ActionRegistry

        _ActionRegistry.validate(
            action_class=ActionClass.REVERSAL_LOG,
            action="reversal_rejected",
        )
        await emit_audit(
            self.session,
            actor_id=actor_id,
            action="reversal_rejected",
            target_table="reversal_log",
            target_id=target_event.event_id if target_event else None,
            payload={
                "reason_ko": reason_ko,
                "actor_id": str(actor_id),
                "trace_id": self.trace_id,
                "tenant_id": str(self.tenant_id),
                "target_event_id": (
                    str(target_event.event_id) if target_event else None
                ),
            },
            tenant_id=self.tenant_id,
            flush=True,
        )

    async def _emit_reversal_negating_inserted_audit(
        self,
        *,
        target_event: InventoryLedgerEvent,
        negating_event_id: uuid.UUID,
        correction_group_id: uuid.UUID,
        actor_id: uuid.UUID,
        trace_id_uuid: uuid.UUID,
    ) -> None:
        """Audit emit on sign-negating row INSERT (AD-22 step 1).

        Uses ActionClass.REVERSAL_LOG → `reversal_negating_inserted` (D3 R4 triage).
        Audit-first (CR 1.1): emitted BEFORE the data INSERT.
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
            target_table="reversal_log",
            target_id=negating_event_id,
            payload={
                "correction_group_id": str(correction_group_id),
                "negating_event_id": str(negating_event_id),
                "target_event_id": str(target_event.event_id),
                "actor_id": str(actor_id),
                "trace_id": str(trace_id_uuid),
                "tenant_id": str(self.tenant_id),
                "source": "reversal_request",
            },
            tenant_id=self.tenant_id,
            flush=True,
        )

    async def _emit_reversal_corrected_inserted_audit(
        self,
        *,
        target_event: InventoryLedgerEvent,
        corrected_event: ReversalCorrectedEvent,
        correction_group_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> None:
        """Audit emit on corrected row INSERT (AD-22 step 2).

        Uses ActionClass.REVERSAL_LOG → `reversal_corrected_inserted` (D3 R4 triage).
        Audit-first (CR 1.1): emitted BEFORE the data INSERT.
        """
        from apps.api.core.audit_action import ActionClass, _ActionRegistry

        _ActionRegistry.validate(
            action_class=ActionClass.REVERSAL_LOG,
            action="reversal_corrected_inserted",
        )
        await emit_audit(
            self.session,
            actor_id=actor_id,
            action="reversal_corrected_inserted",
            target_table="reversal_log",
            target_id=corrected_event.event_id,
            payload={
                "correction_group_id": str(correction_group_id),
                "corrected_event_id": str(corrected_event.event_id),
                "target_event_id": str(target_event.event_id),
                "qty": str(corrected_event.qty),
                "actor_id": str(actor_id),
                "trace_id": str(corrected_event.trace_id),
                "tenant_id": str(self.tenant_id),
                "source": "reversal_request",
            },
            tenant_id=self.tenant_id,
            flush=True,
        )

    async def _emit_reversal_unauthorized_audit(
        self,
        *,
        target_event_id: uuid.UUID,
        actor_id: uuid.UUID,
        reason_ko: str,
    ) -> None:
        """Audit emit on reversal unauthorized (caller role mismatch).

        Uses ActionClass.REVERSAL_LOG → `reversal_unauthorized` (D3 R4 triage).
        Routes to audit_logs via emit_audit.
        """
        from apps.api.core.audit_action import ActionClass, _ActionRegistry

        _ActionRegistry.validate(
            action_class=ActionClass.REVERSAL_LOG,
            action="reversal_unauthorized",
        )
        await emit_audit(
            self.session,
            actor_id=actor_id,
            action="reversal_unauthorized",
            target_table="reversal_log",
            target_id=target_event_id,
            payload={
                "reason_ko": reason_ko,
                "actor_id": str(actor_id),
                "trace_id": self.trace_id,
                "tenant_id": str(self.tenant_id),
                "target_event_id": str(target_event_id),
            },
            tenant_id=self.tenant_id,
            flush=True,
        )

    async def _emit_monthly_input_period_opening_unlocked_audit(
        self,
        *,
        period_key: str,
        actor_id: uuid.UUID,
    ) -> None:
        """Audit emit on opening inventory unlocked (cross-period reversal).

        Uses ActionClass.MONTHLY_INPUT_PERIOD → `monthly_input_period_opening_unlocked`
        (D3 R4 triage). Routes to audit_logs via emit_audit.
        """
        from apps.api.core.audit_action import ActionClass, _ActionRegistry

        _ActionRegistry.validate(
            action_class=ActionClass.MONTHLY_INPUT_PERIOD,
            action="monthly_input_period_opening_unlocked",
        )
        await emit_audit(
            self.session,
            actor_id=actor_id,
            action="monthly_input_period_opening_unlocked",
            target_table="monthly_input_period",
            target_id=self.tenant_id,
            payload={
                "period_key": period_key,
                "actor_id": str(actor_id),
                "trace_id": self.trace_id,
                "tenant_id": str(self.tenant_id),
                "source": "m11_reversal_unlock",
            },
            tenant_id=self.tenant_id,
            flush=True,
        )

    async def _fetch_reversal_rows(
        self,
        *,
        correction_group_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        """Read all rows sharing correction_group_id (sign-negating + corrected)."""
        from sqlalchemy import select

        rows = await self.session.execute(
            select(InventoryLedger).where(
                InventoryLedger.tenant_id == self.tenant_id,
                InventoryLedger.correction_group_id == correction_group_id,
            )
        )
        return [
            {
                "event_id": str(row.event_id),
                "tenant_id": str(row.tenant_id),
                "product_id": str(row.product_id),
                "period_key": row.period_key,
                "event_type": row.event_type,
                "qty": str(row.qty) if row.qty is not None else None,
                "reverses_event_id": (
                    str(row.reverses_event_id) if row.reverses_event_id else None
                ),
                "correction_group_id": (
                    str(row.correction_group_id)
                    if row.correction_group_id
                    else None
                ),
                "reversal_of_period_key": row.reversal_of_period_key,
                "trace_id": str(row.trace_id),
            }
            for row in rows
        ]


def _now_utc() -> datetime:
    return datetime.now(tz=UTC)


def _is_serialization_failure(err: DBAPIError) -> bool:
    """Detect PostgreSQL 40001 serialization_failure on a DBAPIError.

    ECH #12-14 retry gate: PG raises SQLSTATE 40001 when a REPEATABLE READ
    transaction must be rolled back and retried. SQLAlchemy wraps the
    underlying psycopg2/asyncpg error in a DBAPIError; we inspect both
    `err.orig.pgcode` (psycopg2) and the SQLSTATE attribute.
    """
    # DBAPIError exposes `.orig` (the underlying driver error). For
    # psycopg2 / asyncpg, the SQLSTATE is on `err.orig.pgcode` or
    # `err.orig.sqlstate`.
    orig = getattr(err, "orig", None)
    if orig is None:
        return False
    sqlstate = getattr(orig, "pgcode", None) or getattr(orig, "sqlstate", None)
    if sqlstate is None:
        return False
    return str(sqlstate) == _PG_SERIALIZATION_FAILURE


__all__ = [
    "LockedPeriodReversalRejectedError",
    "ReversalDuplicateError",
    "ReversalRejectedError",
    "ReversalResponse",
    "ReversalService",
    "ReversalTargetNotFoundError",
    "ReversalUnauthorizedError",
]
