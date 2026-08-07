"""apps.api.modules.m4_inventory.services.closing_period_service — Story 6.1.

Service layer for the closing period service (PRD §F4.3 + §F5 + §V4 + §A11).

Wraps the pure kernel in `packages.services.m4_inventory.closing_period`
+ `packages.cost_engine.closing_period_snapshot` with:

- 3 service operations:
  - `evaluate_closing_period` (T3.1) — read-only status check via
    `LedgerService.query_period_closing_all` (5-2 SSOT) +
    `classify_closing_period_status` (T1 pure kernel).
  - `confirm_closing_period` (T3.2) — close-time confirmation wire
    (PRD §F4.3 + AD-6 fiscal-period close lock). Reads closing
    snapshot aggregate + emits per-product closing_snapshot ledger
    events + UPDATE monthly_input_periods.status='closed'.
  - `get_closing_period_audit_trail` (T3.3) — audit log emission
    trace (CR 1.1 observability).

- 4 typed exceptions (AD-15 §4 envelope mapping):
  - `ClosingPeriodBlockedError` (409 CLOSING_PERIOD_BLOCKED) — closing
    attempt blocked by CLOSING_BLOCKED status.
  - `ClosingPeriodAlreadyClosedError` (409 ALREADY_CLOSED) — idempotent
    re-confirm guard (already closed).
  - `ClosingPeriodEmptyPeriodError` (409 EMPTY_PERIOD) — no ledger
    events at all.
  - `ClosingPeriodAuditEmitError` (500) — audit-first emit failure.

Layering (AD-11):
- Pure kernel: `packages/services/m4_inventory/closing_period.py` (T1 ✅)
- Pure kernel #2: `packages/cost_engine/closing_period_snapshot.py` (T2 ✅)
- Service layer (this file): SQLAlchemy AsyncSession + audit-first emit
  (CR 1.1 lesson) + 4 typed exceptions.

A5 forward-lock:
- Audit rows route to `audit_logs` (ActionClass.CLOSING_PERIOD) via
  `emit_audit_typed()`. NEW 3 actions:
  - `closing_period_confirmed`
  - `closing_period_blocked`
  - `closing_period_snapshot_inconsistency`
- Drift detector: `tests/integration/test_audit_action_consistency.py`
  + `tests/services/test_audit_action_centralization.py` extensions.

AD-22 reversal entrypoint preserved (5-2 wire + Epic 11 forward-fill):
closing_snapshot ledger events are append-only; correction flow is
Epic 11 module authority (reversal_negating + reversal_corrected
event type fill).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from apps.api.core.db_models import MonthlyInputPeriod
from packages.services.m4_inventory.closing_period import (
    CLOSING_PERIOD_STATUS_BLOCKED,
    CLOSING_PERIOD_STATUS_EMPTY_PERIOD,
    CLOSING_PERIOD_STATUS_READY,
    ClosingPeriodResult,
    ClosingSnapshotEntry,
    classify_closing_period_status,
    compute_closing_snapshot,
    is_closing_period_allowed,
)
from packages.services.m4_inventory.closing_period import (
    ClosingPeriodError as ClosingPeriodPureError,
)


def _now_utc() -> datetime:
    """UTC now (AD-5: pure kernel no clock, service layer owns)."""
    return datetime.now(tz=UTC)


def _to_iso(dt: datetime) -> str:
    """ISO-8601 UTC timestamp string."""
    return dt.isoformat()


# ─────────────────────────────────────────────────────────────
# Typed exceptions (mapped to HTTP by handlers.py / main.py)
# ─────────────────────────────────────────────────────────────


class ClosingPeriodBlockedError(Exception):
    """409 CLOSING_PERIOD_BLOCKED — closing attempt blocked.

    PRD §F4.3 + §V4: closing period status CLOSING_BLOCKED → 마감 차단.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        details: dict[str, Any],
        trace_id: str,
    ) -> None:
        super().__init__(
            f"closing_period blocked for {period_key} " f"(tenant {tenant_id}): {details}"
        )
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.details = details
        self.trace_id = trace_id


class ClosingPeriodAlreadyClosedError(Exception):
    """409 ALREADY_CLOSED — closing period already confirmed.

    PRD §F4.3 + AD-6: idempotent no-op skip when monthly_input_periods
    already status='closed'. CR 1.1 lesson: no INSERT + no UPDATE + no
    audit emit on idempotent re-confirm.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        finalized_at: str | None,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"closing_period already closed for {period_key} "
            f"(tenant {tenant_id}, finalized_at={finalized_at})"
        )
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.finalized_at = finalized_at
        self.trace_id = trace_id


class ClosingPeriodEmptyPeriodError(Exception):
    """409 EMPTY_PERIOD — no ledger events at all.

    PRD §F4.3 + §V4: closing period with 0 ledger events cannot be
    confirmed (no material to snapshot).
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"closing_period empty for {period_key} (tenant {tenant_id})"
        )
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.trace_id = trace_id


class ClosingPeriodAuditEmitError(Exception):
    """500 CLOSING_PERIOD_AUDIT_EMIT_ERROR — audit-first invariant guard.

    CR 1.1 lesson: audit-first emit failure MUST raise (not silent skip).
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        details: dict[str, Any],
        trace_id: str,
    ) -> None:
        super().__init__(f"closing_period audit emit failed for tenant {tenant_id}: {details}")
        self.tenant_id = tenant_id
        self.details = details
        self.trace_id = trace_id


# ─────────────────────────────────────────────────────────────
# ClosingPeriodService
# ─────────────────────────────────────────────────────────────


class ClosingPeriodService:
    """Story 6.1 — closing period service.

    All state-changing operations write a typed audit row BEFORE the
    data write (AD-2), with idempotent no-op skip on already-closed
    periods (CR 1.1 lesson).

    Constructor:
        session: AsyncSession (per-request).
        tenant_id: tenant UUID (from JWT).
        trace_id: request trace ID.
    """

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

    # ── Operation 1: evaluate closing period (read-only) ────────
    async def evaluate_closing_period(
        self,
        period_key: str,
    ) -> ClosingPeriodResult:
        """Read-only closing period status check (PRD §F4.3).

        Reads inventory_ledger aggregate via
        `LedgerService.query_period_closing_all` (5-2 SSOT) →
        `classify_closing_period_status` (T1 pure kernel).

        Args:
            period_key: 'YYYY-MM' AD-24 typed period key.

        Returns:
            `ClosingPeriodResult` NamedTuple with status + allowed +
            closing_per_product + closing_snapshot_count +
            ledger_event_count + period_key.

        Raises:
            ClosingPeriodPureError: invalid period_key (defense-in-depth).
        """

        # 5-2 wire SSOT — multi-product read.
        closing_per_product, ledger_event_count, closing_snapshot_count = (
            await self._query_closing_via_ledger(period_key)
        )

        # Check if already closed (AD-6 fiscal-period close lock).
        is_already_closed = await self._is_period_closed(period_key)

        # Pure kernel dispatch.
        status = classify_closing_period_status(
            closing_per_product,
            ledger_event_count=ledger_event_count,
            is_already_closed=is_already_closed,
        )
        allowed = is_closing_period_allowed(status)

        return ClosingPeriodResult(
            status=status,
            allowed=allowed,
            closing_per_product=closing_per_product,
            closing_snapshot_count=closing_snapshot_count,
            ledger_event_count=ledger_event_count,
            period_key=period_key,
        )

    # ── Operation 2: confirm closing period (close-time hook) ───
    async def confirm_closing_period(
        self,
        period_key: str,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Close-time confirmation wire (PRD §F4.3 + AD-6 + AD-22).

        Flow (CR 1.1 audit-first ordering):
        1. SELECT FOR UPDATE on monthly_input_periods (AD-4 atomicity +
           idempotent no-op skip on already-closed).
        2. evaluate_closing_period → status check.
        3. CLOSING_READY → compute closing_snapshot entries +
           LedgerService.append_event per product (5-2 wire 진입점).
        4. UPDATE monthly_input_periods.status='closed' +
           closed_at=now() + closed_by_actor_id=actor_id +
           closing_snapshot_event_count=N.
        5. Audit-first emit (closing_period_confirmed).
        6. V4 verification dispatch (deferred to m6_verification
           module — VerificationRunner invokes V4 verifier post-confirm).

        Args:
            period_key: 'YYYY-MM' AD-24 typed period key.
            actor_id: actor who triggered; None for system cron.

        Returns:
            dict with `confirmed: True, closing_snapshot_count,
            period_key, finalized_at`.

        Raises:
            ClosingPeriodAlreadyClosedError: monthly_input_periods.status='closed'.
            ClosingPeriodBlockedError: status=CLOSING_BLOCKED.
            ClosingPeriodEmptyPeriodError: status=EMPTY_PERIOD.
            ClosingPeriodAuditEmitError: audit-first emit failed.
        """
        # AD-4 atomicity: SELECT FOR UPDATE on monthly_input_periods
        # (5-3 wire pattern preserved).
        from apps.api.modules.m4_inventory.services.ledger_service import (
            LedgerService,
        )

        period_row = await self.session.scalar(
            select(MonthlyInputPeriod).where(
                MonthlyInputPeriod.tenant_id == self.tenant_id,
                MonthlyInputPeriod.period_key == period_key,
            ).with_for_update()
        )

        # Idempotent no-op skip — already closed.
        if period_row is not None and period_row.status == "closed":
            raise ClosingPeriodAlreadyClosedError(
                tenant_id=self.tenant_id,
                period_key=period_key,
                finalized_at=getattr(period_row, "finalized_at", None)
                and period_row.finalized_at.isoformat()
                or None,
                trace_id=self.trace_id,
            )

        # Evaluate first (reads ledger aggregate + closing_period status).
        result = await self.evaluate_closing_period(period_key)

        if result.status == CLOSING_PERIOD_STATUS_BLOCKED:
            # Audit-first emit (CLOSING_BLOCKED) before raising.
            await self._emit_audit_blocked(
                period_key=period_key,
                actor_id=actor_id,
                details={"negative_products_count": len(result.closing_per_product)},
            )
            raise ClosingPeriodBlockedError(
                tenant_id=self.tenant_id,
                period_key=period_key,
                details={"closing_per_product": _decimal_to_str(result.closing_per_product)},
                trace_id=self.trace_id,
            )

        if result.status == CLOSING_PERIOD_STATUS_EMPTY_PERIOD:
            # EMPTY_PERIOD — no audit emit (defense-in-depth: not a
            # violation, just an empty period).
            raise ClosingPeriodEmptyPeriodError(
                tenant_id=self.tenant_id,
                period_key=period_key,
                trace_id=self.trace_id,
            )

        # ALREADY_CLOSED already raised above; only CLOSING_READY reaches here.
        if not result.allowed or result.status != CLOSING_PERIOD_STATUS_READY:
            raise ClosingPeriodPureError(
                message=(
                    f"closing_period unexpected status {result.status!r} "
                    f"after guard checks"
                ),
                error_code="UNEXPECTED_CLOSING_PERIOD_STATUS",
                period_key=period_key,
                tenant_id=self.tenant_id,
            )

        # CR 1.1 audit-first ordering: ledger INSERT before
        # monthly_input_periods UPDATE before audit log INSERT.
        finalized_at_dt = _now_utc()
        finalized_at = _to_iso(finalized_at_dt)

        # (1) Compute closing_snapshot entries (pure kernel).
        snapshot_entries: list[ClosingSnapshotEntry] = compute_closing_snapshot(
            result.closing_per_product,
            period_key=period_key,
            finalized_at=finalized_at,
        )

        # (2) Emit per-product closing_snapshot ledger events
        #     (5-2 LedgerService.append_event dispatch — AD-2 append-only).
        ledger_service = LedgerService(
            self.session,
            tenant_id=self.tenant_id,
            trace_id=self.trace_id,
        )
        for entry in snapshot_entries:
            await ledger_service.append_event(
                product_id=entry.product_id,
                period_key=period_key,
                event_type="closing_snapshot",
                qty=entry.closing_qty,
                source="close_snapshot",
                metadata={
                    "finalized_at": finalized_at,
                    "closing_period_status": CLOSING_PERIOD_STATUS_READY,
                },
                actor_id=actor_id,
            )

        # (3) UPDATE monthly_input_periods — AD-6 close hook.
        if period_row is not None:
            period_row.status = "closed"
            period_row.finalized_at = finalized_at_dt
            period_row.closed_by_actor_id = actor_id
            period_row.closing_snapshot_event_count = len(snapshot_entries)
            await self.session.flush()
        else:
            # period_row is None — month_input_periods doesn't exist yet.
            # Defensive: raise typed error rather than silent insert.
            raise ClosingPeriodPureError(
                message=(
                    f"monthly_input_periods row not found for "
                    f"period_key={period_key!r} tenant_id={self.tenant_id}"
                ),
                error_code="MONTHLY_INPUT_PERIOD_NOT_FOUND",
                period_key=period_key,
                tenant_id=self.tenant_id,
            )

        # (4) Audit-first emit (closing_period_confirmed) — CR 1.1.
        await self._emit_audit_confirmed(
            period_key=period_key,
            actor_id=actor_id,
            finalized_at=finalized_at,
            closing_snapshot_count=len(snapshot_entries),
        )

        return {
            "confirmed": True,
            "closing_snapshot_count": len(snapshot_entries),
            "period_key": period_key,
            "finalized_at": finalized_at,
        }

    # ── Operation 3: audit trail query ──────────────────────────
    async def get_closing_period_audit_trail(
        self,
        period_key: str,
    ) -> list[dict[str, Any]]:
        """Audit log emission trace for the closing period (CR 1.1).

        Returns audit_logs rows where action_class='closing_period'
        for the current period_key, time DESC, capped at 10.
        """
        from sqlalchemy import text

        # JSONB expression on payload->>'period_key' (audit_logs schema
        # has no dedicated period_key column).
        result = await self.session.execute(
            text(
                """
                SELECT action, payload, occurred_at
                FROM audit_logs
                WHERE tenant_id = :tenant_id
                  AND target_table = 'closing_period'
                  AND payload->>'period_key' = :period_key
                ORDER BY occurred_at DESC
                LIMIT 10
                """
            ),
            {
                "tenant_id": str(self.tenant_id),
                "period_key": period_key,
            },
        )
        rows = result.fetchall()
        return [
            {
                "action": row[0],
                "payload": row[1] if isinstance(row[1], dict) else {},
                "occurred_at": row[2].isoformat() if row[2] is not None else None,
            }
            for row in rows
        ]

    # ── Internal helpers ────────────────────────────────────────
    async def _query_closing_via_ledger(
        self,
        period_key: str,
    ) -> tuple[dict[uuid.UUID, Decimal], int, int]:
        """Read multi-product ledger aggregate via 5-2 LedgerService SSOT.

        Returns:
            (closing_per_product, ledger_event_count,
             closing_snapshot_count).
        """
        from apps.api.modules.m4_inventory.services.ledger_service import (
            LedgerService,
        )

        ledger_service = LedgerService(
            self.session,
            tenant_id=self.tenant_id,
            trace_id=self.trace_id,
        )
        closing_per_product = await ledger_service.query_period_closing_all(
            period_key=period_key,
        )
        ledger_event_count = await ledger_service.count_period_events(
            period_key=period_key,
        )
        closing_snapshot_count = await ledger_service.count_period_events(
            period_key=period_key,
            event_type="closing_snapshot",
        )
        return closing_per_product, ledger_event_count, closing_snapshot_count

    async def _is_period_closed(self, period_key: str) -> bool:
        """Check AD-6 fiscal-period close lock."""
        from sqlalchemy import text

        result = await self.session.scalar(
            text(
                "SELECT status FROM monthly_input_periods "
                "WHERE tenant_id = :tenant_id AND period_key = :period_key"
            ),
            {
                "tenant_id": str(self.tenant_id),
                "period_key": period_key,
            },
        )
        return result == "closed"

    async def _emit_audit_confirmed(
        self,
        *,
        period_key: str,
        actor_id: uuid.UUID | None,
        finalized_at: str,
        closing_snapshot_count: int,
    ) -> None:
        """Audit-first emit (CR 1.1) for closing_period_confirmed."""
        try:
            await emit_audit_typed(
                self.session,
                action_class=ActionClass.CLOSING_PERIOD,
                action="closing_period_confirmed",
                actor_id=actor_id,
                target_id=self.tenant_id,
                tenant_id=self.tenant_id,
                payload={
                    "period_key": period_key,
                    "finalized_at": finalized_at,
                    "closing_snapshot_count": closing_snapshot_count,
                    "trace_id": self.trace_id,
                },
            )
        except Exception as err:
            raise ClosingPeriodAuditEmitError(
                tenant_id=self.tenant_id,
                details={
                    "action": "closing_period_confirmed",
                    "period_key": period_key,
                    "error": str(err),
                },
                trace_id=self.trace_id,
            ) from err

    async def _emit_audit_blocked(
        self,
        *,
        period_key: str,
        actor_id: uuid.UUID | None,
        details: dict[str, Any],
    ) -> None:
        """Audit-first emit (CR 1.1) for closing_period_blocked."""
        try:
            await emit_audit_typed(
                self.session,
                action_class=ActionClass.CLOSING_PERIOD,
                action="closing_period_blocked",
                actor_id=actor_id,
                target_id=self.tenant_id,
                tenant_id=self.tenant_id,
                payload={
                    "period_key": period_key,
                    **details,
                    "trace_id": self.trace_id,
                },
            )
        except Exception as err:
            raise ClosingPeriodAuditEmitError(
                tenant_id=self.tenant_id,
                details={
                    "action": "closing_period_blocked",
                    "period_key": period_key,
                    "error": str(err),
                },
                trace_id=self.trace_id,
            ) from err


def _decimal_to_str(d: dict[uuid.UUID, Decimal]) -> dict[str, str]:
    """Decimal → str for JSON serialization (AD-8 monetary types)."""
    return {str(pid): f"{qty:f}" for pid, qty in d.items()}


__all__ = [
    "ClosingPeriodAlreadyClosedError",
    "ClosingPeriodAuditEmitError",
    "ClosingPeriodBlockedError",
    "ClosingPeriodEmptyPeriodError",
    "ClosingPeriodService",
]
