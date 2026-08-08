"""apps.api.modules.m11_close.services.reversal_kernel_adapter — pure-kernel dispatch.

Story 11.1 — thin adapter that dispatches the M11 pure kernels from
`packages/services/m11_close/`. Exists to:
1. Centralize pure-kernel dispatch (single place to update if kernels refactor).
2. Provide DB-agnostic helpers to the service layer (ReversalService).

AD-11 layering: this module is in `apps/api/modules/` — it does NOT
import `packages.cost_engine` directly. It DOES import `packages.services.m11_close`
(pure kernels, stdlib-only) and bridges them to the SQLAlchemy world.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.db_models import FiscalPeriod, InventoryLedger, MonthlyInputPeriod
from packages.services.m4_inventory.ledger import InventoryLedgerEvent
from packages.services.m11_close.reversal_corrected import (
    ReversalCorrectedEvent,
    build_reversal_corrected_event,
)
from packages.services.m11_close.reversal_negating import (
    ReversalNegatingEvent,
    build_reversal_negating_event,
)


async def fetch_target_event(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    target_event_id: uuid.UUID,
) -> InventoryLedgerEvent | None:
    """Fetch the target inventory_ledger row for reversal.

    Returns None if the event doesn't exist or belongs to another tenant
    (RLS-scoped). The service layer decides whether None is an error
    (404 REVERSAL_TARGET_NOT_FOUND) or an idempotent skip.

    Story 11.1 P12 — SELECT FOR UPDATE row-level lock prevents concurrent
    reversal requests from racing past the (tenant_id, reverses_event_id)
    PARTIAL UNIQUE INDEX check. Combined with REPEATABLE READ at the
    transaction boundary, this prevents two concurrent reversal attempts
    from both passing the existence check and both INSERTing a negating
    row, where the second INSERT would fail the unique constraint.

    NOTE: tenant_id filter is RLS-scoped — even without explicit filter,
    the session's RLS context would auto-filter. We add the explicit
    filter as defense-in-depth.
    """
    row = await session.scalar(
        select(InventoryLedger)
        .where(
            InventoryLedger.event_id == target_event_id,
            InventoryLedger.tenant_id == tenant_id,
        )
        .with_for_update()
    )
    if row is None:
        return None
    return InventoryLedgerEvent(
        event_id=row.event_id,
        tenant_id=row.tenant_id,
        product_id=row.product_id,
        period_key=row.period_key,
        event_type=row.event_type,
        qty=row.qty,
        trace_id=row.trace_id,
        reverses_event_id=row.reverses_event_id,
        correction_group_id=row.correction_group_id,
        payload=dict(row.payload or {}),
    )


async def fetch_period_status(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    period_key: str,
) -> str | None:
    """Fetch the period_status from monthly_input_periods.

    Returns None if the period doesn't exist for this tenant. Service
    layer treats None as 'open' default (period not yet initialized).
    """
    row = await session.scalar(
        select(MonthlyInputPeriod).where(
            MonthlyInputPeriod.tenant_id == tenant_id,
            MonthlyInputPeriod.period_key == period_key,
        )
    )
    if row is None:
        return None
    return row.status  # type: ignore[no-any-return]


async def fetch_fiscal_period_status(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    period_key: str,
) -> str | None:
    """Fetch the fiscal_periods.status — Story 11.2 PRIMARY guard.

    AD-6 close lock mirror at the authorization layer. Returns None
    if no fiscal_periods row exists for (tenant_id, period_key) —
    service layer treats None as 'open' default (close_sequence has
    not been initiated for this period yet).

    Lightweight single-row SELECT (indexed via UNIQUE
    (tenant_id, period_key)).
    """
    row = await session.scalar(
        select(FiscalPeriod).where(
            FiscalPeriod.tenant_id == tenant_id,
            FiscalPeriod.period_key == period_key,
        )
    )
    if row is None:
        return None
    return row.status  # type: ignore[no-any-return]


def dispatch_build_reversal_negating(
    *,
    target_event: InventoryLedgerEvent,
    reason: str,
    actor_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    trace_id: uuid.UUID,
    event_id: uuid.UUID | None = None,
) -> ReversalNegatingEvent:
    """Dispatch build_reversal_negating_event from pure kernel."""
    return build_reversal_negating_event(
        target_event=target_event,
        reason=reason,
        actor_id=actor_id,
        correction_group_id=correction_group_id,
        trace_id=trace_id,
        event_id=event_id,
    )


def dispatch_build_reversal_corrected(
    *,
    target_event: InventoryLedgerEvent,
    correction_group_id: uuid.UUID,
    corrected_qty: Decimal | None,
    corrected_period_key: str | None,
    actor_id: uuid.UUID,
    trace_id: uuid.UUID,
    event_id: uuid.UUID | None = None,
) -> ReversalCorrectedEvent | None:
    """Dispatch build_reversal_corrected_event from pure kernel."""
    return build_reversal_corrected_event(
        target_event=target_event,
        correction_group_id=correction_group_id,
        corrected_qty=corrected_qty,
        corrected_period_key=corrected_period_key,
        actor_id=actor_id,
        trace_id=trace_id,
        event_id=event_id,
    )


__all__ = [
    "dispatch_build_reversal_corrected",
    "dispatch_build_reversal_negating",
    "fetch_fiscal_period_status",
    "fetch_period_status",
    "fetch_target_event",
]
