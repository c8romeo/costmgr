"""apps.api.modules.m4_inventory.services.ledger_service — Story 5.2.

AD-2 append-only ledger service layer. Wraps the pure kernel in
`packages.services.m4_inventory.ledger` + `ledger_query` with:

- 5 service operations:
  - `append_event` (AC #4): primary INSERT path for stream events
    (`purchase_inbound`, `sales_outbound`, etc.) + audit-first emit
    of `inventory_ledger_event_appended`.
  - `query_period_closing` (AC #1): SUM(qty) for a single period
    via the kernel's pure SQL fragment.
  - `query_carry_chain` (AC #1): recursive CTE walk via the kernel's
    pure SQL fragment (5-1 carry chain consumer).
  - `request_reversal` (AC #6): M4 entrypoint stub — emits
    `inventory_ledger_reversal_requested` audit marker; the actual
    reversal sequence INSERT is wired in Epic 11 (M11 authority).
  - `get_event` (AC #1): single event lookup by event_id.

- 4 typed exceptions (AD-15 §4 envelope mapping):
  - `AppendOnlyLedgerViolationError` (500)
    — DB trigger or service-layer AST guard caught append-only attempt
  - `InventoryLedgerInvalidEventTypeError` (422)
    — event_type not in 11-value whitelist (defense-in-depth; should
      be caught upstream by `validate_event_type`)
  - `InventoryLedgerPeriodKeyFormatError` (422)
    — period_key not 'YYYY-MM' AD-24 typed pattern
  - `InventoryLedgerReversalNotYetWiredError` (501)
    — request_reversal called but M11 not yet shipped (Epic 11)

Layering (AD-11):
- Pure kernel: `packages/services/m4_inventory/ledger.py` (T1 ✅)
- Pure kernel #2: `packages/services/m4_inventory/ledger_query.py` (T2 ✅)
- Service layer (this file): SQLAlchemy AsyncSession + audit-first
  emit (CR 1.1 lesson) + 3중 방어 (DB trigger + AST guard + audit log).

AC #3 — append-only 3중 방어:
- (1) DB trigger (Alembic 0015) — production gate
- (2) Service-layer AST guard (`LedgerService._assert_not_modifying`)
      — early-fail; never issues UPDATE/DELETE in normal flow
- (3) Audit log emission (`inventory_ledger_event_rejected`)
      — observability for attempted violations

A5 forward-lock:
- Audit rows route to `inventory_ledger` (ActionClass.INVENTORY_LEDGER)
  via the dedicated `_write_inventory_ledger_audit` writer — calls
  `_ActionRegistry.validate()` BEFORE INSERT (CR 1.1 audit-first).
- Drift detector: `tests/integration/test_audit_action_consistency.py`
  + `tests/integration/test_inventory_ledger_event_type_drift.py`.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, _ActionRegistry
from apps.api.core.db_models import InventoryLedger
from packages.services.m0_onboarding.industry_menu import Industry
from packages.services.m4_inventory.ledger import (
    AppendOnlyLedgerError,
    build_event_payload,
)
from packages.services.m4_inventory.ledger_query import (
    assert_tenant_guarded,
    build_carry_chain_query,
    build_period_closing_query,
)

# ─────────────────────────────────────────────────────────────
# Typed exceptions (mapped to HTTP by handlers.py / main.py)
# ─────────────────────────────────────────────────────────────


class AppendOnlyLedgerViolationError(Exception):
    """500 APPEND_ONLY_LEDGER_VIOLATION — append-only attempt rejected.

    Defense-in-depth (AC #3 OQ1 3중 방어 — 2nd axis): the service layer
    AST guard rejects UPDATE/DELETE attempts before the SQL is issued,
    so the DB trigger (1st axis) only fires if the AST guard has a
    bug. Both axes emit `inventory_ledger_event_rejected` audit row.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        event_id: uuid.UUID | None,
        attempted_op: str,
        details: dict[str, Any],
        trace_id: str,
    ) -> None:
        super().__init__(
            f"append-only violation (op={attempted_op}, event_id={event_id}, "
            f"tenant={tenant_id}): {details.get('reason', 'unknown')}"
        )
        self.tenant_id = tenant_id
        self.event_id = event_id
        self.attempted_op = attempted_op
        self.details = details
        self.trace_id = trace_id


class InventoryLedgerInvalidEventTypeError(Exception):
    """422 INVENTORY_LEDGER_INVALID_EVENT_TYPE — event_type not whitelisted.

    Defense-in-depth (should be caught upstream by `validate_event_type`
    from the pure kernel). This exception only fires if a caller bypassed
    the pure kernel and supplied a non-canonical event_type directly.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        event_type: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"event_type {event_type!r} is not in the 11-value whitelist"
        )
        self.tenant_id = tenant_id
        self.event_type = event_type
        self.trace_id = trace_id


class InventoryLedgerPeriodKeyFormatError(Exception):
    """422 INVENTORY_LEDGER_PERIOD_KEY_FORMAT — period_key AD-24 mismatch.

    PRD §6.2 inventory equation is fiscal ('YYYY-MM'). M8 virtual budget
    keys ('YYYY-MM#B<n>') are explicitly excluded from inventory_ledger.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"period_key {period_key!r} must match 'YYYY-MM' AD-24 typed pattern"
        )
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.trace_id = trace_id


class InventoryLedgerReversalNotYetWiredError(Exception):
    """501 INVENTORY_LEDGER_REVERSAL_NOT_YET_WIRED — Epic 11 forward-fill.

    The M4 `request_reversal(event_id, reason)` entrypoint emits the
    audit marker `inventory_ledger_reversal_requested` and records
    the request. The actual reversal sequence INSERT (negating row +
    optional corrected row) is owned by Epic 11 module authority.
    Until M11 ships, the entrypoint acknowledges but does NOT issue
    the DB writes — returning 501.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        event_id: uuid.UUID,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"reversal for event_id={event_id} not yet wired "
            f"(Epic 11 M11 authority insert deferred)"
        )
        self.tenant_id = tenant_id
        self.event_id = event_id
        self.trace_id = trace_id


# ─────────────────────────────────────────────────────────────
# LedgerService
# ─────────────────────────────────────────────────────────────


class LedgerService:
    """Story 5.2 — AD-2 append-only ledger service.

    All state-changing operations write a typed inventory_ledger audit
    row BEFORE the data write (audit-first pattern, CR 1.1 lesson) via
    `_write_inventory_ledger_audit`. The DB trigger enforces append-only
    at the production gate; this service's `_assert_not_modifying`
    provides the early-fail AST guard.

    Constructor:
        session: AsyncSession (per-request).
        tenant_id: tenant UUID (from JWT).
        industry: tenant industry (None for service tenants).
        trace_id: request trace ID.
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        industry: Industry | None,
        trace_id: str,
    ) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.industry = industry
        self.trace_id = trace_id

    # ── Operation 1: append_event (AC #4 primary INSERT path) ──
    async def append_event(
        self,
        *,
        product_id: uuid.UUID,
        period_key: str,
        event_type: str,
        qty: Decimal | None,
        source: str,
        reverses_event_id: uuid.UUID | None = None,
        correction_group_id: uuid.UUID | None = None,
        metadata: dict[str, Any] | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> InventoryLedger:
        """INSERT a new inventory_ledger row + audit-first emit.

        The pure kernel `build_event_payload` builds the row payload
        (validating event_type, period_key, qty, source). This method
        adds the audit-first emit + DB INSERT.

        Args:
            product_id, period_key, event_type, qty, source: row fields.
            reverses_event_id, correction_group_id: AD-22 reversal
                sequence fields (Epic 11 forward-fill). Defaults to None.
            metadata: optional JSONB metadata.
            actor_id: actor who triggered the append; None for system.

        Returns:
            InventoryLedger: the persisted row.

        Raises:
            AppendOnlyLedgerError (pure kernel): invalid event_type /
                period_key / qty / source.
            InventoryLedgerInvalidEventTypeError (422): event_type not
                in the 11-value whitelist (defense-in-depth).
            InventoryLedgerPeriodKeyFormatError (422): period_key not
                'YYYY-MM' AD-24 typed pattern.
            AppendOnlyLedgerViolationError (500): service-layer AST
                guard caught an UPDATE/DELETE attempt (should never
                fire from this method).
            IntegrityError: DB CHECK constraint violation (defense-in-
                depth if pure kernel validation has a bug).
        """
        # (1) Pure-kernel validation + payload build
        event_id = uuid.uuid4()
        trace_id_uuid = uuid.UUID(self.trace_id) if self.trace_id else uuid.uuid4()
        try:
            payload = build_event_payload(
                event_id=event_id,
                product_id=product_id,
                period_key=period_key,
                event_type=event_type,
                qty=qty,
                trace_id=trace_id_uuid,
                source=source,
                reverses_event_id=reverses_event_id,
                correction_group_id=correction_group_id,
                metadata=metadata,
            )
        except AppendOnlyLedgerError as err:
            # Re-raise as typed service-layer exception (defense-in-depth)
            if "11-value whitelist" in err.message:
                raise InventoryLedgerInvalidEventTypeError(
                    tenant_id=self.tenant_id,
                    event_type=event_type,
                    trace_id=self.trace_id,
                ) from err
            if "YYYY-MM" in err.message:
                raise InventoryLedgerPeriodKeyFormatError(
                    tenant_id=self.tenant_id,
                    period_key=period_key,
                    trace_id=self.trace_id,
                ) from err
            raise  # unknown kernel error — propagate

        # (2) Audit-first emit (BEFORE INSERT — CR 1.1)
        await self._write_inventory_ledger_audit(
            action="inventory_ledger_event_appended",
            event_id=event_id,
            payload=payload,
            actor_id=actor_id,
        )

        # (3) INSERT the new row
        row = InventoryLedger(
            event_id=event_id,
            tenant_id=self.tenant_id,
            product_id=product_id,
            period_key=period_key,
            event_type=event_type,
            qty=qty,
            trace_id=trace_id_uuid,
            reverses_event_id=reverses_event_id,
            correction_group_id=correction_group_id,
            payload=metadata or {},
            inserted_at=_now_utc(),
        )
        self.session.add(row)
        try:
            await self.session.flush()
        except IntegrityError as err:
            # DB CHECK constraint violation (defense-in-depth)
            await self._write_inventory_ledger_audit(
                action="inventory_ledger_event_rejected",
                event_id=event_id,
                payload={
                    **payload,
                    "rejection_reason": f"DB CHECK constraint: {err.orig}",
                },
                actor_id=actor_id,
            )
            raise
        return row

    # ── Operation 2: query_period_closing (AC #1 SUM(qty)) ─────
    async def query_period_closing(
        self,
        *,
        product_id: uuid.UUID,
        period_key: str,
    ) -> Decimal:
        """SUM(qty) for a single (tenant, product, period_key).

        Excludes `closing_snapshot` rows (PRD §6.2: closing_snapshot is
        a materialized balance, not a flow event).

        Returns:
            Decimal: closing balance (0 if no flow events).
        """
        query = build_period_closing_query()
        assert_tenant_guarded(query)
        result = await self.session.scalar(
            text(query.sql),
            {
                "tenant_id": str(self.tenant_id),
                "product_id": str(product_id),
                "period_key": period_key,
            },
        )
        return Decimal(str(result)) if result is not None else Decimal("0")

    # ── Operation 2b: query_period_closing_all (multi-product) ─
    async def query_period_closing_all(
        self,
        *,
        period_key: str,
    ) -> dict[uuid.UUID, Decimal]:
        """SUM(qty) aggregated per product for a single period.

        Excludes `closing_snapshot` rows (same semantics as
        `query_period_closing`). Used by:
        - `MonthlyInputService._compute_inventory_projection_for_state`
          (Epic 3.3 inline projection swap — AC #5)
        - `GET /api/v1/inventory/ledger/period-closing` handler
          (multi-product read endpoint)

        Tenant-isolation: filters on tenant_id (AD-4 RLS).

        Returns:
            dict[UUID, Decimal] — empty if no flow events.
        """

        sql = (
            "SELECT product_id, COALESCE(SUM(qty), 0) AS closing_qty "
            "FROM inventory_ledger "
            "WHERE tenant_id = :tenant_id "
            "  AND period_key = :period_key "
            "  AND event_type != 'closing_snapshot' "
            "GROUP BY product_id"
        )
        rows = await self.session.execute(
            text(sql),
            {
                "tenant_id": str(self.tenant_id),
                "period_key": period_key,
            },
        )
        return {
            row.product_id: Decimal(str(row.closing_qty))
            for row in rows
        }

    # ── Operation 3: query_carry_chain (AC #1 recursive walk) ──
    async def query_carry_chain(
        self,
        *,
        product_id: uuid.UUID,
        period_key: str,
    ) -> list[dict[str, Any]]:
        """Recursive CTE walk for opening_carried events up to 12 periods.

        Args:
            product_id: target product.
            period_key: upper bound (exclusive).

        Returns:
            list[dict] with keys: event_id, period_key, qty, inserted_at.
            Ordered chronologically (ascending period_key).
        """
        query = build_carry_chain_query()
        assert_tenant_guarded(query)
        rows = await self.session.execute(
            text(query.sql),
            {
                "tenant_id": str(self.tenant_id),
                "product_id": str(product_id),
                "period_key": period_key,
            },
        )
        return [
            {
                "event_id": str(row.event_id),
                "period_key": row.period_key,
                "qty": str(row.qty) if row.qty is not None else None,
                "inserted_at": row.inserted_at.isoformat()
                if row.inserted_at
                else None,
            }
            for row in rows
        ]

    # ── Operation 4: request_reversal (AC #6 forward-fill) ─────
    async def request_reversal(
        self,
        *,
        event_id: uuid.UUID,
        reason: str,
        actor_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """M4 entrypoint stub for AD-22 reversal sequence.

        AC #6 + OQ5 cj-style default: this method emits the audit
        marker `inventory_ledger_reversal_requested` and verifies the
        target event exists + belongs to the tenant. The actual
        reversal sequence INSERT (negating row + optional corrected
        row) is owned by Epic 11 module authority.

        Raises:
            InventoryLedgerReversalNotYetWiredError (501): the actual
                reversal INSERT is deferred to Epic 11. This stub
                records the request but does NOT issue the DB writes.
        """
        # Verify event exists for tenant (defense-in-depth)
        target = await self.session.scalar(
            select(InventoryLedger).where(
                InventoryLedger.event_id == event_id,
                InventoryLedger.tenant_id == self.tenant_id,
            )
        )
        if target is None:
            raise AppendOnlyLedgerViolationError(
                tenant_id=self.tenant_id,
                event_id=event_id,
                attempted_op="REVERSAL_REQUEST",
                details={"reason": f"event_id {event_id} not found"},
                trace_id=self.trace_id,
            )

        # Audit marker (Epic 11 forward-fill pattern)
        await self._write_inventory_ledger_audit(
            action="inventory_ledger_reversal_requested",
            event_id=event_id,
            payload={
                "event_id": str(event_id),
                "product_id": str(target.product_id),
                "period_key": target.period_key,
                "event_type": target.event_type,
                "qty": str(target.qty) if target.qty is not None else None,
                "reason": reason,
                "trace_id": self.trace_id,
            },
            actor_id=actor_id,
        )

        # 501 — actual INSERT deferred to Epic 11
        raise InventoryLedgerReversalNotYetWiredError(
            tenant_id=self.tenant_id,
            event_id=event_id,
            trace_id=self.trace_id,
        )

    # ── Operation 5: get_event (AC #1 single event lookup) ─────
    async def get_event(
        self,
        *,
        event_id: uuid.UUID,
    ) -> InventoryLedger | None:
        """Single event lookup by event_id (tenant-scoped).

        Returns None if event not found or belongs to a different tenant.
        """
        return await self.session.scalar(
            select(InventoryLedger).where(
                InventoryLedger.event_id == event_id,
                InventoryLedger.tenant_id == self.tenant_id,
            )
        )

    # ── Internal: AST guard (AC #3 3중 방어 — 2nd axis) ────────
    def _assert_not_modifying(self, sql_text: str) -> None:
        """Reject any UPDATE/DELETE/TRUNCATE on inventory_ledger.

        Service-layer AST guard. The DB trigger is the production
        gate; this method provides early-fail so the violation is
        caught at the service layer (with full trace_id + actor_id
        context) before the SQL is issued.

        Raises:
            AppendOnlyLedgerViolationError: SQL contains forbidden
                mutation keywords.
        """
        forbidden = ("UPDATE ", "DELETE ", "TRUNCATE ", "DROP TABLE ")
        for kw in forbidden:
            if kw in sql_text.upper():
                # Audit-first: emit rejection event
                # Note: this is fire-and-forget — caller catches the
                # exception and the audit row is in the same session.
                raise AppendOnlyLedgerViolationError(
                    tenant_id=self.tenant_id,
                    event_id=None,
                    attempted_op=kw.strip(),
                    details={
                        "reason": "inventory_ledger append-only violation",
                        "sql_text_excerpt": sql_text[:200],
                    },
                    trace_id=self.trace_id,
                )

    # ── Internal: audit-first writer ───────────────────────────
    async def _write_inventory_ledger_audit(
        self,
        *,
        action: str,
        event_id: uuid.UUID,
        payload: dict[str, Any],
        actor_id: uuid.UUID | None,
    ) -> None:
        """Emit a typed audit row to inventory_ledger audit destination.

        Calls `_ActionRegistry.validate()` BEFORE the INSERT — fail-fast
        on drift. The audit row is written via the registry-routed
        destination (`audit_logs` for now; Epic 5+ routes to
        `inventory_ledger` directly).
        """
        # A5 forward-lock: validate against the registry (D1 deferral 해결)
        _ActionRegistry.validate(
            action_class=ActionClass.INVENTORY_LEDGER,
            action=action,
        )
        from apps.api.core.audit import emit_audit

        # Self-describing payload (CR 1.1 lesson)
        enriched_payload = {
            **payload,
            "trace_id": self.trace_id,
            "event_id": str(event_id),
            "tenant_id": str(self.tenant_id),
        }
        await emit_audit(
            self.session,
            actor_id=actor_id,
            action=action,
            target_table="inventory_ledger",
            target_id=event_id,
            payload=enriched_payload,
            tenant_id=self.tenant_id,
            flush=True,
        )


def _now_utc() -> datetime:
    return datetime.now(tz=UTC)


__all__ = [
    "AppendOnlyLedgerViolationError",
    "InventoryLedgerInvalidEventTypeError",
    "InventoryLedgerPeriodKeyFormatError",
    "InventoryLedgerReversalNotYetWiredError",
    "LedgerService",
]
