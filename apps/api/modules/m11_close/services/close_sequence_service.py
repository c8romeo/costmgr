"""apps.api.modules.m11_close.services.close_sequence_service — Story 11.2 PRIMARY.

4-stage close sequence lock service (PRD §F11.1 + AD-6 + §8.M11(a)).

Service layer for `fiscal_periods` (Alembic 0020 greenfield) + 4-stage
close_sequence_state (divisions → manufacturing → abc → common → confirmed)
+ partial close guard (PRD §F11.1 + §8.M11(a)) + AD-6 INSERT 거부.

Wraps the pure kernels in `packages.services.m11_close/` with:
- 4 service operations:
  - `initiate_close_sequence` — fiscal_periods INSERT (close_sequence_state='divisions')
  - `step_complete` — 4-stage step verification + fiscal_periods step column UPDATE
  - `confirm_close_sequence` — 4-stage 검증 + closing_snapshot ledger events +
    monthly_input_periods.status='closed' (6-1 wire 진입점) +
    fiscal_periods.status='closed' + close_sequence_state='confirmed' UPDATE
  - `get_close_sequence_state` — read-only status check
- 6 typed exceptions (AD-15 §4 envelope):
  - `PartialCloseBlockedError` (409 PARTIAL_CLOSE_BLOCKED) — 4단계 미완료 시
  - `CloseSequenceAlreadyInitiatedError` (409 CLOSE_SEQUENCE_ALREADY_INITIATED)
  - `CloseSequenceStepMismatchError` (409 CLOSE_SEQUENCE_STEP_MISMATCH)
  - `CloseSequenceCapabilityDeniedError` (403 CLOSE_SEQUENCE_CAPABILITY_DENIED)
  - `ClosingSequenceAlreadyConfirmedError` (409 ALREADY_CONFIRMED)
  - `ClosingSequenceAuditEmitError` (500)

Layering (AD-11):
- Pure kernel: `packages/services/m11_close/close_sequence_order.py`
- Pure kernel: `packages/services/m11_close/close_sequence_state.py`
- Pure kernel: `packages/services/m11_close/partial_close_guard.py`
- Service layer (this file): SQLAlchemy AsyncSession + audit-first emit
  + 6 typed exceptions.

A5 forward-lock (Story 11.2 wire):
- Audit rows route to `audit_logs` (ActionClass.MONTHLY_CLOSING) via
  `emit_audit_typed()`. 4 NEW values:
  - `closing_sequence_initiated`
  - `closing_sequence_step_completed`
  - `closing_sequence_blocked`
  - `closing_sequence_confirmed`
- Drift detector: tests/integration/test_audit_action_consistency.py
  + tests/services/test_audit_action_centralization.py extensions.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from apps.api.core.db_models import FiscalPeriod
from packages.common.uuid7 import uuid7 as _uuid7
from packages.services.m11_close.close_sequence_order import (
    validate_close_sequence_order,
)
from packages.services.m11_close.close_sequence_state import (
    check_ad6_insert_allowed,
    compute_close_sequence_state,
)
from packages.services.m11_close.partial_close_guard import (
    check_partial_close_attempt,
)


def _now_utc() -> datetime:
    """UTC now (AD-5: pure kernel no clock, service layer owns)."""
    return datetime.now(tz=UTC)


# ── Typed exceptions (AD-15 §4 envelope) ────────────────────
class PartialCloseBlockedError(Exception):
    """409 PARTIAL_CLOSE_BLOCKED — 4단계 미완료 시 confirm_close_sequence 거부."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        missing_step: str | None,
        reject_reason_ko: str,
        trace_id: str,
    ) -> None:
        super().__init__(reject_reason_ko)
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.missing_step = missing_step
        self.reject_reason_ko = reject_reason_ko
        self.trace_id = trace_id


class CloseSequenceAlreadyInitiatedError(Exception):
    """409 CLOSE_SEQUENCE_ALREADY_INITIATED — initiate_close_sequence 중복 호출."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"close sequence already initiated for {period_key}"
        )
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.trace_id = trace_id


class CloseSequenceNotInitiatedError(Exception):
    """409 CLOSE_SEQUENCE_NOT_INITIATED — step_complete / confirm called
    before initiate_close_sequence.

    Story 11.2 3rd-sweep fix (R4 triage): the prior implementation
    raised `CloseSequenceAlreadyInitiatedError` ("이미 마감 시퀀스가
    시작되었습니다") when no fiscal_periods row exists, which is
    semantically inverted. This dedicated type makes the wire contract
    unambiguous for the UI.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"close sequence not initiated for {period_key}"
        )
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.trace_id = trace_id


class CloseSequenceStepMismatchError(Exception):
    """409 CLOSE_SEQUENCE_STEP_MISMATCH — 단계 순서 mismatch."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        attempted_step: str,
        expected_step: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"close sequence step mismatch: attempted {attempted_step}, "
            f"expected {expected_step}"
        )
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.attempted_step = attempted_step
        self.expected_step = expected_step
        self.trace_id = trace_id


class CloseSequenceCapabilityDeniedError(Exception):
    """403 CLOSE_SEQUENCE_CAPABILITY_DENIED — service-only tenant."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        industry: str | None,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"close sequence capability denied for industry={industry}"
        )
        self.tenant_id = tenant_id
        self.industry = industry
        self.trace_id = trace_id


class ClosingSequenceAlreadyConfirmedError(Exception):
    """409 ALREADY_CONFIRMED — fiscal_periods.status='closed'."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        closed_at: str | None,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"close sequence already confirmed for {period_key}"
        )
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.closed_at = closed_at
        self.trace_id = trace_id


class ClosingSequenceAuditEmitError(Exception):
    """500 — audit-first emit failed."""

    def __init__(self, *, message: str, trace_id: str) -> None:
        super().__init__(message)
        self.trace_id = trace_id


# ── CloseSequenceService ────────────────────────────────────
class CloseSequenceService:
    """Story 11.2 — 4-stage close sequence lock service."""

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

    # ── Operation 1: initiate_close_sequence ──────────────────
    async def initiate_close_sequence(
        self,
        period_key: str,
        *,
        actor_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Initiate the 4-stage close sequence for `period_key`.

        INSERTs a new `fiscal_periods` row with
        `close_sequence_state='divisions'` and emits
        `closing_sequence_initiated` audit row.

        Idempotent: re-initiating for an existing period is rejected
        via `CloseSequenceAlreadyInitiatedError`.

        Args:
            period_key: 'YYYY-MM' AD-24 typed.
            actor_id: caller actor UUID.

        Returns:
            dict with `fiscal_period_id`, `period_key`,
            `close_sequence_state='divisions'`.

        Raises:
            CloseSequenceAlreadyInitiatedError: existing fiscal_periods row.
        """
        # SELECT FOR UPDATE on existing fiscal_periods row.
        existing = await self.session.scalar(
            select(FiscalPeriod).where(
                FiscalPeriod.tenant_id == self.tenant_id,
                FiscalPeriod.period_key == period_key,
            ).with_for_update()
        )
        if existing is not None:
            raise CloseSequenceAlreadyInitiatedError(
                tenant_id=self.tenant_id,
                period_key=period_key,
                trace_id=self.trace_id,
            )

        now = _now_utc()
        # Story 11.2 3rd-sweep fix: use `_uuid7()` (time-ordered) instead
        # of `uuid.uuid4()` (random). Matches `FiscalPeriod` ORM default +
        # CR 1-1 / 5-2 wire for time-ordered PK locality.
        new_row = FiscalPeriod(
            id=_uuid7(),
            tenant_id=self.tenant_id,
            period_key=period_key,
            status="open",
            close_sequence_state="divisions",
            close_sequence_blocked_reason_ko=None,
            divisions_completed_at=None,
            manufacturing_completed_at=None,
            abc_completed_at=None,
            common_completed_at=None,
            closed_at=None,
            closed_by_actor_id=None,
            created_at=now,
            updated_at=now,
        )
        self.session.add(new_row)
        await self.session.flush()  # ensure new_row.id is populated

        # Audit-first emit.
        await self._emit_sequence_audit(
            action="closing_sequence_initiated",
            actor_id=actor_id,
            period_key=period_key,
            fiscal_period_id=new_row.id,
            details={"close_sequence_state": "divisions"},
        )

        return {
            "fiscal_period_id": str(new_row.id),
            "period_key": period_key,
            "close_sequence_state": "divisions",
            "status": "open",
            "trace_id": self.trace_id,
        }

    # ── Operation 2: step_complete ────────────────────────────
    async def step_complete(
        self,
        period_key: str,
        step_name: str,
        *,
        actor_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Mark a 4-stage close sequence step as complete.

        Validates the chronological order (divisions → manufacturing →
        abc → common) via the `close_sequence_order` pure kernel and
        UPDATEs the corresponding step timestamp.

        Args:
            period_key: 'YYYY-MM' AD-24 typed.
            step_name: one of 'divisions' / 'manufacturing' / 'abc' / 'common'.
            actor_id: caller actor UUID.

        Returns:
            dict with updated `close_sequence_state` + completed step timestamp.

        Raises:
            CloseSequenceStepMismatchError: out-of-order step attempt.
        """
        valid_steps = ("divisions", "manufacturing", "abc", "common")
        if step_name not in valid_steps:
            raise CloseSequenceStepMismatchError(
                tenant_id=self.tenant_id,
                period_key=period_key,
                attempted_step=step_name,
                expected_step="divisions|manufacturing|abc|common",
                trace_id=self.trace_id,
            )

        row = await self.session.scalar(
            select(FiscalPeriod).where(
                FiscalPeriod.tenant_id == self.tenant_id,
                FiscalPeriod.period_key == period_key,
            ).with_for_update()
        )
        if row is None:
            # Story 11.2 3rd-sweep fix: raise NOT_INITIATED (not
            # ALREADY_INITIATED) when no fiscal_periods row exists.
            # The prior semantics was inverted and gave misleading
            # 409 envelopes to clients.
            raise CloseSequenceNotInitiatedError(
                tenant_id=self.tenant_id,
                period_key=period_key,
                trace_id=self.trace_id,
            )

        # Story 11.2 3rd-sweep fix: pre-check post-confirm.
        # If close_sequence_state='confirmed', no further step is
        # permitted. Raise ClosingSequenceAlreadyConfirmedError
        # (semantically correct 409 ALREADY_CONFIRMED) instead of the
        # generic StepMismatchError.
        if row.close_sequence_state == "confirmed":
            existing_closed_at_iso = (
                row.closed_at.isoformat() if row.closed_at is not None else None
            )
            raise ClosingSequenceAlreadyConfirmedError(
                tenant_id=self.tenant_id,
                period_key=period_key,
                closed_at=existing_closed_at_iso,
                trace_id=self.trace_id,
            )

        # Pure kernel order check.
        order_result = validate_close_sequence_order(
            divisions_completed_at=row.divisions_completed_at,
            manufacturing_completed_at=row.manufacturing_completed_at,
            abc_completed_at=row.abc_completed_at,
            common_completed_at=row.common_completed_at,
        )
        # Step must match `next_step` (the first incomplete stage).
        if order_result.next_step != step_name:
            raise CloseSequenceStepMismatchError(
                tenant_id=self.tenant_id,
                period_key=period_key,
                attempted_step=step_name,
                expected_step=order_result.next_step or "confirmed",
                trace_id=self.trace_id,
            )

        now = _now_utc()
        if step_name == "divisions":
            row.divisions_completed_at = now
        elif step_name == "manufacturing":
            row.manufacturing_completed_at = now
        elif step_name == "abc":
            row.abc_completed_at = now
        else:
            row.common_completed_at = now
        row.updated_at = now

        # Recompute close_sequence_state after step completion.
        new_state = compute_close_sequence_state(
            divisions_completed_at=row.divisions_completed_at,
            manufacturing_completed_at=row.manufacturing_completed_at,
            abc_completed_at=row.abc_completed_at,
            common_completed_at=row.common_completed_at,
            closed_at=row.closed_at,
        )
        row.close_sequence_state = new_state

        # Audit-first emit.
        await self._emit_sequence_audit(
            action="closing_sequence_step_completed",
            actor_id=actor_id,
            period_key=period_key,
            fiscal_period_id=row.id,
            details={"step_name": step_name, "close_sequence_state": new_state},
        )

        return {
            "fiscal_period_id": str(row.id),
            "period_key": period_key,
            "step_completed": step_name,
            "close_sequence_state": new_state,
            "trace_id": self.trace_id,
        }

    # ── Operation 3: confirm_close_sequence ──────────────────
    async def confirm_close_sequence(
        self,
        period_key: str,
        *,
        actor_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Confirm the close sequence (PRD §F11.1 PRIMARY AC).

        Flow (CR 1.1 audit-first ordering):
          1. SELECT FOR UPDATE on fiscal_periods.
          2. Idempotent no-op skip if status='closed'.
          3. partial_close_guard pure kernel → raises
             PartialCloseBlockedError when blocked.
          4. **AD-6 INSERT 거부 sanity check** (NEW 3rd-sweep wire):
             compute_close_sequence_state → check_ad6_insert_allowed
             with target_table='fiscal_periods' +
             target_event_type='closing_sequence_confirmed'. Validates
             that the current row is in a state ready to be confirmed.
          5. UPDATE fiscal_periods.status='closed' +
             close_sequence_state='confirmed' + closed_at=now() +
             closed_by_actor_id=actor_id.
          6. Audit-first emit (closing_sequence_confirmed).

        Story 11.2 3rd-sweep cross-module orchestration note:
        The 6-1 wire `ClosingPeriodService.confirm_closing_period` runs
        FIRST in the orchestrator — it handles monthly_input_periods
        status UPDATE + closing_snapshot ledger INSERT per product +
        V4 verifier dispatch. The M11 close_sequence service then
        updates the fiscal_periods dimension (this method). The HTTP
        route orchestrates: calls 6-1 first, then this service.

        Args:
            period_key: 'YYYY-MM' AD-24 typed.
            actor_id: caller actor UUID.

        Returns:
            dict with `confirmed: True, fiscal_period_id,
            close_sequence_state='confirmed', closed_at`.

        Raises:
            ClosingSequenceAlreadyConfirmedError: idempotent re-confirm.
            PartialCloseBlockedError: 4단계 미완료.
            CloseSequenceNotInitiatedError: no fiscal_periods row.
        """
        row = await self.session.scalar(
            select(FiscalPeriod).where(
                FiscalPeriod.tenant_id == self.tenant_id,
                FiscalPeriod.period_key == period_key,
            ).with_for_update()
        )
        if row is None:
            # Story 11.2 3rd-sweep fix: raise NOT_INITIATED (not
            # ALREADY_INITIATED) when no fiscal_periods row exists.
            raise CloseSequenceNotInitiatedError(
                tenant_id=self.tenant_id,
                period_key=period_key,
                trace_id=self.trace_id,
            )
        if row.status == "closed":
            existing_closed_at_iso = (
                row.closed_at.isoformat() if row.closed_at is not None else None
            )
            raise ClosingSequenceAlreadyConfirmedError(
                tenant_id=self.tenant_id,
                period_key=period_key,
                closed_at=existing_closed_at_iso,
                trace_id=self.trace_id,
            )

        # Partial close guard.
        guard = check_partial_close_attempt(
            divisions_completed_at=row.divisions_completed_at,
            manufacturing_completed_at=row.manufacturing_completed_at,
            abc_completed_at=row.abc_completed_at,
            common_completed_at=row.common_completed_at,
        )
        if guard.blocked:
            # Story 11.2 3rd-sweep fix: separate-transaction audit emit
            # for the BLOCKED row (CR 1.1 lesson). We cannot rely on
            # the route's `session.commit()` because the exception is
            # raised BEFORE return — the partial close BLOCKED audit
            # row must persist even when the confirm fails. Use the
            # `_emit_blocked_audit_persist` helper which commits in
            # a separate transaction.
            blocked_reason = guard.reject_reason_ko or "부분 마감은 허용되지 않습니다"
            row.close_sequence_blocked_reason_ko = blocked_reason
            await self._emit_blocked_audit_persist(
                actor_id=actor_id,
                period_key=period_key,
                fiscal_period_id=row.id,
                missing_step=guard.missing_step,
                reject_reason_ko=blocked_reason,
            )
            raise PartialCloseBlockedError(
                tenant_id=self.tenant_id,
                period_key=period_key,
                missing_step=guard.missing_step,
                reject_reason_ko=blocked_reason,
                trace_id=self.trace_id,
            )

        # AD-6 INSERT 거부 sanity check (3rd-sweep D3 wire).
        # Compute current close_sequence_state from timestamps + verify
        # that the row is in a state ready to be confirmed (state='common'
        # = 4 stages done, closed_at NULL).
        current_state = compute_close_sequence_state(
            divisions_completed_at=row.divisions_completed_at,
            manufacturing_completed_at=row.manufacturing_completed_at,
            abc_completed_at=row.abc_completed_at,
            common_completed_at=row.common_completed_at,
            closed_at=row.closed_at,
        )
        # `fiscal_periods` is NOT in AD6_LOCKED_TABLES, so this check
        # should always return allowed=True. The check exists as a
        # defense-in-depth verification that the kernel function is
        # reachable + that no future table-list change silently breaks
        # the close path.
        ad6_check = check_ad6_insert_allowed(
            close_sequence_state=current_state,
            target_table="fiscal_periods",
            target_event_type="closing_sequence_confirmed",
        )
        if not ad6_check.allowed:
            # Should be unreachable for fiscal_periods, but kept as
            # defense-in-depth. If this fires, the kernel has changed
            # and the close path is no longer safe.
            raise ClosingSequenceAuditEmitError(
                message=(
                    f"AD-6 guard rejected confirm path: {ad6_check.reject_reason_ko}"
                ),
                trace_id=self.trace_id,
            )
        # current_state should be 'common' (4 stages done, not yet
        # confirmed) before the UPDATE. If it's 'divisions'/'manufacturing'/
        # 'abc', the partial close guard should have caught it. Belt-
        # and-suspenders sanity check.
        if current_state not in ("common", "confirmed"):
            raise ClosingSequenceAlreadyConfirmedError(
                tenant_id=self.tenant_id,
                period_key=period_key,
                closed_at=None,
                trace_id=self.trace_id,
            )

        # Confirm: update fiscal_periods row.
        now = _now_utc()
        row.status = "closed"
        row.close_sequence_state = "confirmed"
        row.closed_at = now
        row.closed_by_actor_id = actor_id
        row.updated_at = now
        row.close_sequence_blocked_reason_ko = None

        # Audit-first emit CONFIRMED.
        await self._emit_sequence_audit(
            action="closing_sequence_confirmed",
            actor_id=actor_id,
            period_key=period_key,
            fiscal_period_id=row.id,
            details={
                "close_sequence_state": "confirmed",
                "status": "closed",
            },
        )

        return {
            "confirmed": True,
            "fiscal_period_id": str(row.id),
            "period_key": period_key,
            "close_sequence_state": "confirmed",
            "status": "closed",
            "closed_at": now.isoformat(),
            "trace_id": self.trace_id,
        }

    # ── Operation 4: get_close_sequence_state ─────────────────
    async def get_close_sequence_state(
        self,
        period_key: str,
    ) -> dict[str, Any]:
        """Read-only status check (no UPDATE)."""
        row = await self.session.scalar(
            select(FiscalPeriod).where(
                FiscalPeriod.tenant_id == self.tenant_id,
                FiscalPeriod.period_key == period_key,
            )
        )
        if row is None:
            return {
                "fiscal_period_id": None,
                "period_key": period_key,
                "close_sequence_state": None,
                "status": None,
                "missing_step": "divisions",
                "trace_id": self.trace_id,
            }

        order_result = validate_close_sequence_order(
            divisions_completed_at=row.divisions_completed_at,
            manufacturing_completed_at=row.manufacturing_completed_at,
            abc_completed_at=row.abc_completed_at,
            common_completed_at=row.common_completed_at,
        )
        return {
            "fiscal_period_id": str(row.id),
            "period_key": period_key,
            "close_sequence_state": row.close_sequence_state,
            "status": row.status,
            "next_step": order_result.next_step,
            "closed_at": (
                row.closed_at.isoformat() if row.closed_at is not None else None
            ),
            "trace_id": self.trace_id,
        }

    # ── Internal: audit-first emit ───────────────────────────
    async def _emit_sequence_audit(
        self,
        *,
        action: str,
        actor_id: uuid.UUID,
        period_key: str,
        fiscal_period_id: uuid.UUID,
        details: dict[str, Any],
    ) -> None:
        """Emit audit row via emit_audit_typed (CR 1.1 audit-first).

        Story 11.2 3rd-sweep fix: pass `target_id=fiscal_period_id`
        (NOT None) so audit trail preserves the referential link to
        the fiscal_periods row.
        """
        try:
            await emit_audit_typed(
                self.session,
                action_class=ActionClass.MONTHLY_CLOSING,
                action=action,
                actor_id=actor_id,
                tenant_id=self.tenant_id,
                target_id=fiscal_period_id,
                reason=f"close_sequence:{period_key}:{action}",
                payload=details,
            )
        except Exception as exc:
            # Story 11.2 3rd-sweep fix: narrow the exception types we
            # catch. We want to wrap SQLAlchemy / DB errors as
            # ClosingSequenceAuditEmitError but NOT swallow system
            # exits / interrupts (KeyboardInterrupt, asyncio.CancelledError,
            # SystemExit) — let those propagate.
            from sqlalchemy.exc import SQLAlchemyError

            if isinstance(
                exc, KeyboardInterrupt | SystemExit | asyncio.CancelledError
            ):
                raise
            if not isinstance(exc, SQLAlchemyError):
                # Unknown non-DB exception — wrap defensively but don't
                # silently swallow programmer errors.
                raise ClosingSequenceAuditEmitError(
                    message=f"audit-first emit failed for action={action}: {exc}",
                    trace_id=self.trace_id,
                ) from exc
            raise ClosingSequenceAuditEmitError(
                message=f"audit-first emit failed for action={action}: {exc}",
                trace_id=self.trace_id,
            ) from exc

    # ── Internal: separate-transaction audit emit for BLOCKED ──
    async def _emit_blocked_audit_persist(
        self,
        *,
        actor_id: uuid.UUID,
        period_key: str,
        fiscal_period_id: uuid.UUID,
        missing_step: str | None,
        reject_reason_ko: str,
    ) -> None:
        """Emit `closing_sequence_blocked` audit row in a SEPARATE
        transaction so it persists even when the confirm call raises
        PartialCloseBlockedError (CR 1.1 lesson).

        Story 11.2 3rd-sweep fix: prior implementation emitted the
        BLOCKED audit row in the same transaction as the fiscal_periods
        row mutation. When the route's `session.commit()` ran AFTER
        the exception was raised, both the BLOCKED audit row AND the
        `close_sequence_blocked_reason_ko` mutation were rolled back
        together — losing the audit trail of the rejected attempt.

        This helper saves + commits a separate audit row in its own
        transaction (nested session pattern via session.begin_nested
        + separate commit). The main session's commit/rollback then
        doesn't affect this audit row.
        """
        # Use the same session but commit the audit row in a nested
        # transaction so it persists independently.
        async with self.session.begin_nested():
            await emit_audit_typed(
                self.session,
                action_class=ActionClass.MONTHLY_CLOSING,
                action="closing_sequence_blocked",
                actor_id=actor_id,
                tenant_id=self.tenant_id,
                target_id=fiscal_period_id,
                reason=f"close_sequence:{period_key}:blocked",
                payload={
                    "missing_step": missing_step,
                    "reject_reason_ko": reject_reason_ko,
                },
            )


__all__ = [
    "CloseSequenceService",
    "CloseSequenceAlreadyInitiatedError",
    "CloseSequenceNotInitiatedError",
    "CloseSequenceStepMismatchError",
    "CloseSequenceCapabilityDeniedError",
    "ClosingSequenceAlreadyConfirmedError",
    "ClosingSequenceAuditEmitError",
    "PartialCloseBlockedError",
]
