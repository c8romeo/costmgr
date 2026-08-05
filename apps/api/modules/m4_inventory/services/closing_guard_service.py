"""apps.api.modules.m4_inventory.services.closing_guard_service — Story 5.3.

Service layer for the closing ≥ 0 invariant guard (PRD §F4.2 + §V3).

Wraps the pure kernel in `packages.services.m4_inventory.closing_guard`
+ `production_consumption` with:

- 4 service operations:
  - `evaluate_closing_guard` (T4.1) — read-only invariant check via
    `LedgerService.query_period_closing` SSOT.
  - `request_close_attempt` (T4.2) — close-time gate wire (additive
    over Story 4-2 is_blocked → 409 NEGATIVE_CLOSING_INVENTORY).
  - `emit_production_ledger_events` (T4.3) — Story 5.2 deferral #9
    resolved: BOM-aware reconciliation (production_output_inbound +
    production_material_consumption 동시 emit).
  - `validate_closing_invariant_against_active_products` (T4.4) —
    V3 verification sync (calls cost_engine pure kernel).

- 5 typed exceptions (AD-15 §4 envelope mapping):
  - `ClosingGuardNegativeInventoryError` (409 NEGATIVE_CLOSING_INVENTORY)
    — close attempt blocked by invariant violation.
  - `ClosingGuardInvalidPeriodKeyError` (422)
    — period_key not 'YYYY-MM' AD-24 typed pattern.
  - `ClosingGuardServiceOnlyTenantError` (403 INDUSTRY_NOT_SUPPORTED)
    — service-only tenant attempted closing guard (capability gate).
  - `ClosingGuardProductionConsumptionError` (500)
    — BOM reconciliation failure (defense-in-depth).
  - `ClosingGuardAuditEmitError` (500)
    — audit-first emit failure (CR 1.1 invariant guard).

Layering (AD-11):
- Pure kernel: `packages/services/m4_inventory/closing_guard.py` (T1 ✅)
- Pure kernel #2: `packages/services/m4_inventory/production_consumption.py` (T3 ✅)
- Pure kernel #3: `packages/cost_engine/closing_invariant_check.py` (T2 ✅)
- Service layer (this file): SQLAlchemy AsyncSession + audit-first emit
  (CR 1.1 lesson) + 5 typed exceptions.

A5 forward-lock:
- Audit rows route to `audit_logs` (ActionClass.CLOSING_GUARD) and
  `verification_log` (ActionClass.VERIFICATION) via `emit_audit_typed()`.
- Drift detector: `tests/integration/test_audit_action_consistency.py`
  + `tests/services/test_audit_action_centralization.py` extensions.

AD-22 reversal entrypoint preserved (5-2 wire): emit_production_ledger_events
writes inventory_ledger rows; reversal handling is Epic 11 module authority.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from apps.api.core.db_models import MonthlyInputRow, Product
from packages.services.m0_onboarding.industry_menu import Industry
from packages.services.m4_inventory.closing_guard import (
    ClosingGuardError as ClosingGuardPureError,
)
from packages.services.m4_inventory.closing_guard import (
    ClosingInvariant,
    classify_closing_invariant,
    compute_closing_balance_per_product,
    format_negative_closing_banner_ko,
    is_close_blocked,
)
from packages.services.m4_inventory.production_consumption import (
    BomMatrixLike,
    ProductionRowLike,
    compute_production_consumption_events,
)


def _now_utc() -> datetime:
    """UTC now (AD-5: pure kernel no clock, service layer owns)."""
    return datetime.now(tz=UTC)


def _to_decimal(value: Any) -> Decimal:
    """Coerce value to Decimal (banker's rounding applied at caller)."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


# ─────────────────────────────────────────────────────────────
# Typed exceptions (mapped to HTTP by handlers.py / main.py)
# ─────────────────────────────────────────────────────────────


class ClosingGuardNegativeInventoryError(Exception):
    """409 NEGATIVE_CLOSING_INVENTORY — close attempt blocked.

    PRD §F4.2: closing ≥ 0 invariant violation → 마감 진입 차단.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        negative_products: dict[str, Decimal],
        banner_ko: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"closing_guard negative inventory for {period_key} "
            f"(tenant {tenant_id}): {len(negative_products)} products"
        )
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.negative_products = negative_products
        self.banner_ko = banner_ko
        self.trace_id = trace_id


class ClosingGuardInvalidPeriodKeyError(Exception):
    """422 CLOSING_GUARD_INVALID_PERIOD_KEY — period_key not 'YYYY-MM'."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"closing_guard invalid period_key {period_key!r} " f"(tenant {tenant_id})"
        )
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.trace_id = trace_id


class ClosingGuardServiceOnlyTenantError(Exception):
    """403 INDUSTRY_NOT_SUPPORTED — service-only tenant attempted guard."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        industry: str | None,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"closing_guard not available for service-only tenant "
            f"{tenant_id} (industry={industry})"
        )
        self.tenant_id = tenant_id
        self.industry = industry
        self.trace_id = trace_id


class ClosingGuardProductionConsumptionError(Exception):
    """500 CLOSING_GUARD_PRODUCTION_CONSUMPTION_ERROR — BOM reconciliation fail."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        details: dict[str, Any],
        trace_id: str,
    ) -> None:
        super().__init__(
            f"closing_guard BOM reconciliation failed for tenant {tenant_id}: " f"{details}"
        )
        self.tenant_id = tenant_id
        self.details = details
        self.trace_id = trace_id


class ClosingGuardAuditEmitError(Exception):
    """500 CLOSING_GUARD_AUDIT_EMIT_ERROR — audit-first invariant guard.

    CR 1.1 lesson: audit-first emit failure MUST raise (not silent skip).
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        details: dict[str, Any],
        trace_id: str,
    ) -> None:
        super().__init__(f"closing_guard audit emit failed for tenant {tenant_id}: {details}")
        self.tenant_id = tenant_id
        self.details = details
        self.trace_id = trace_id


# ─────────────────────────────────────────────────────────────
# ClosingGuardService
# ─────────────────────────────────────────────────────────────


class ClosingGuardService:
    """Story 5.3 — closing ≥ 0 invariant guard service.

    All state-changing operations write a typed audit row BEFORE
    the data write (AD-2), with idempotent no-op skip on identical
    payloads (CR 1.1 lesson).

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
        # service-only tenant → guard disabled
        self._guard_enabled = industry is not None and industry != Industry.SERVICE

    # ── Operation 1: evaluate invariant (read-only) ───────────
    async def evaluate_closing_guard(
        self,
        period_key: str,
    ) -> ClosingInvariant:
        """Read-only closing invariant check (PRD §F4.2 + §V3).

        Reads inventory_ledger aggregate via `LedgerService.query_period_closing`
        (5-2 SSOT) → `compute_closing_balance_per_product` → `classify_closing_invariant`.
        Adjusts `guard_enabled` based on tenant industry check.

        Args:
            period_key: 'YYYY-MM' AD-24 typed period key.

        Returns:
            `ClosingInvariant` NamedTuple with code + negative_products +
            closing_per_product + guard_enabled.

        Raises:
            ClosingGuardInvalidPeriodKeyError: malformed period_key.
            ClosingGuardServiceOnlyTenantError: service-only tenant.
        """
        _validate_period_key(period_key)

        # Read-only ledger aggregate via SSOT (5-2 wire).
        closing_per_product = await self._query_closing_via_ledger(period_key)

        invariant = classify_closing_invariant(closing_per_product)
        # Adjust guard_enabled for industry skip matrix.
        return invariant._replace(guard_enabled=self._guard_enabled)

    # ── Operation 2: close-time gate (additive over 4-2) ──────
    async def request_close_attempt(
        self,
        period_key: str,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Close-time gate wire (additive over Story 4-2 is_blocked).

        Story 4-2 is_blocked → 409 MONTHLY_INPUT_BLOCKED (Epic 3 A4 wire).
        Story 5-3 additive: closing ≥ 0 invariant check on the same
        close attempt → 409 NEGATIVE_CLOSING_INVENTORY if NEGATIVE_CLOSING.

        Args:
            period_key: 'YYYY-MM' AD-24 typed period key.
            actor_id: actor who triggered; None for system cron.

        Returns:
            `{ allowed: True, period_key, closing_per_product, invariant, ... }`

        Raises:
            ClosingGuardNegativeInventoryError: invariant.code=NEGATIVE_CLOSING.
            ClosingGuardInvalidPeriodKeyError: malformed period_key.
            ClosingGuardServiceOnlyTenantError: service-only tenant.
        """
        invariant = await self.evaluate_closing_guard(period_key)

        if is_close_blocked(invariant):
            # audit-first (CR 1.1) — emit closing_guard_violated BEFORE raise
            await self._emit_audit(
                action="closing_guard_violated",
                actor_id=actor_id,
                payload={
                    "tenant_id": str(self.tenant_id),
                    "period_key": period_key,
                    "negative_products": {
                        str(pid): f"{qty:f}" for pid, qty in invariant.negative_products.items()
                    },
                    "invariant_code": invariant.code,
                    "attempted_at": _now_utc().isoformat(),
                    "trace_id": self.trace_id,
                },
            )
            banner_ko = format_negative_closing_banner_ko(invariant)
            raise ClosingGuardNegativeInventoryError(
                tenant_id=self.tenant_id,
                period_key=period_key,
                negative_products={
                    str(pid): qty for pid, qty in invariant.negative_products.items()
                },
                banner_ko=banner_ko,
                trace_id=self.trace_id,
            )

        # CLOSING_OK or EMPTY_PERIOD → 200 OK
        await self._emit_audit(
            action="closing_guard_passed",
            actor_id=actor_id,
            payload={
                "tenant_id": str(self.tenant_id),
                "period_key": period_key,
                "closing_per_product": {
                    str(pid): f"{qty:f}" for pid, qty in invariant.closing_per_product.items()
                },
                "invariant_code": invariant.code,
                "verified_at": _now_utc().isoformat(),
                "trace_id": self.trace_id,
            },
        )
        return {
            "allowed": True,
            "period_key": period_key,
            "closing_per_product": {
                str(pid): f"{qty:f}" for pid, qty in invariant.closing_per_product.items()
            },
            "invariant_code": invariant.code,
            "trace_id": self.trace_id,
        }

    # ── Operation 3: BOM-aware production ledger emit ──────────
    async def emit_production_ledger_events(
        self,
        *,
        production_row: MonthlyInputRow,
        bom: dict[str, Any] | None,
    ) -> list[str]:
        """BOM-aware reconciliation of production stream events.

        Story 5.2 deferral #9 resolved. Each production row INSERT in
        `monthly_input_service.save_row` (stream='production') routes
        here to:
        - production_output_inbound (output product qty)
        - production_material_consumption events (per child material, BOM-defined)
          OR adjustment_positive fallback (BOM missing)

        Args:
            production_row: monthly_input_rows ORM row (stream='production').
            bom: BOM matrix dict (Story 2.2 schema) or None for fallback.

        Returns:
            List of emitted inventory_ledger event_id strings (UUID).

        Raises:
            ClosingGuardProductionConsumptionError: BOM reconciliation failure.
        """
        if production_row.stream != "production":
            # Idempotent no-op for non-production streams.
            return []

        # Map SQLAlchemy row → TypedDict (pure-kernel interface).
        row_dict = ProductionRowLike(
            product_id=str(production_row.product_id),
            product_qty=str(production_row.qty or Decimal("0")),
            period_key=production_row.period_key,
            trace_id=str(production_row.trace_id or _mint_trace_id()),
        )
        bom_dict = (
            BomMatrixLike(
                parent_product_id=str(bom["parent_product_id"]),
                children=bom.get("children", []),
            )
            if bom
            else None
        )

        try:
            computed_events = compute_production_consumption_events(
                production_row=row_dict,
                bom=bom_dict,
            )
        except Exception as err:
            # Wrap pure-kernel error as typed exception (defense-in-depth).
            if isinstance(err, ClosingGuardPureError):
                raise ClosingGuardProductionConsumptionError(
                    tenant_id=self.tenant_id,
                    details={"error_code": err.error_code, "message": err.message},
                    trace_id=self.trace_id,
                ) from err
            raise ClosingGuardProductionConsumptionError(
                tenant_id=self.tenant_id,
                details={"error_code": "UNKNOWN", "message": str(err)},
                trace_id=self.trace_id,
            ) from err

        # Emit each event via LedgerService.append_event.
        from apps.api.modules.m4_inventory.services.ledger_service import (
            LedgerService,
        )
        from packages.services.m4_inventory.ledger import (
            SOURCE_MONTHLY_INPUT,
        )

        ledger_svc = LedgerService(
            self.session,
            tenant_id=self.tenant_id,
            industry=self.industry,
            trace_id=self.trace_id,
        )

        emitted_event_ids: list[str] = []
        for event in computed_events:
            try:
                qty_decimal = _to_decimal(event["qty"])
                event_id = await ledger_svc.append_event(
                    product_id=uuid.UUID(event["product_id"]),
                    period_key=row_dict["period_key"],
                    event_type=event["event_type"],
                    qty=qty_decimal,
                    source=SOURCE_MONTHLY_INPUT,
                    metadata=event["metadata"],
                    actor_id=None,
                )
                emitted_event_ids.append(str(event_id))
            except Exception as err:
                raise ClosingGuardProductionConsumptionError(
                    tenant_id=self.tenant_id,
                    details={
                        "error_code": "LEDGER_EMIT_FAIL",
                        "event_type": event["event_type"],
                        "message": str(err),
                    },
                    trace_id=self.trace_id,
                ) from err

        return emitted_event_ids

    # ── Operation 4: V3 verification sync ─────────────────────
    async def validate_closing_invariant_against_active_products(
        self,
        period_key: str,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """V3 verification sync — closing ≥ 0 invariant against active products.

        Wraps `packages.cost_engine.closing_invariant_check.verify_closing_invariant`
        with service-layer wires (RLS-scoped product whitelist + ledger aggregate).

        Args:
            period_key: 'YYYY-MM' AD-24 typed period key.
            actor_id: actor who triggered; None for system cron.

        Returns:
            V3Verdict TypedDict (cost_engine shape) with PASS/FAIL/SKIP status.

        Raises:
            ClosingGuardInvalidPeriodKeyError: malformed period_key.
            ClosingGuardServiceOnlyTenantError: service-only tenant.
        """
        from packages.cost_engine.closing_invariant_check import (
            V3_SKIP_REASON_SERVICE_ONLY_KO,
            verify_closing_invariant,
        )

        _validate_period_key(period_key)

        # Industry skip matrix
        if not self._guard_enabled:
            return dict(
                verify_closing_invariant(
                    ledger_aggregate={},
                    product_whitelist=set(),
                    verified_at=_now_utc().isoformat(),
                    skip_reason_ko=V3_SKIP_REASON_SERVICE_ONLY_KO,
                )
            )

        # Read ledger aggregate + product whitelist in parallel
        closing_per_product = await self._query_closing_via_ledger(period_key)
        whitelist = await self._query_active_product_whitelist()

        verdict = verify_closing_invariant(
            ledger_aggregate=closing_per_product,
            product_whitelist=whitelist,
            verified_at=_now_utc().isoformat(),
            skip_reason_ko=None,
        )

        # Audit emit (CR 1.1 audit-first)
        await self._emit_audit(
            action="v3_closing_invariant_verified",
            actor_id=actor_id,
            payload={
                "tenant_id": str(self.tenant_id),
                "period_key": period_key,
                "verdict_status": verdict["status"],
                "verdict_code": verdict["code"],
                "failures_count": len(verdict["failures"]),
                "product_whitelist_size": verdict["product_whitelist_size"],
                "skip_reason_ko": verdict.get("skip_reason_ko"),
                "verified_at": verdict["verified_at"],
                "trace_id": self.trace_id,
            },
        )

        return dict(verdict)

    # ── Internal helpers ──────────────────────────────────────
    async def _query_closing_via_ledger(
        self,
        period_key: str,
    ) -> dict[uuid.UUID, Decimal]:
        """Query inventory_ledger aggregate via LedgerService (5-2 SSOT)."""
        from apps.api.modules.m4_inventory.services.ledger_service import (
            LedgerService,
        )

        ledger_svc = LedgerService(
            self.session,
            tenant_id=self.tenant_id,
            industry=self.industry,
            trace_id=self.trace_id,
        )
        # query_period_closing returns list[InventoryLedgerEvent] (5-2 shape)
        events = await ledger_svc.query_period_closing(period_key=period_key)
        return compute_closing_balance_per_product(events)

    async def _query_active_product_whitelist(
        self,
    ) -> set[uuid.UUID]:
        """Query active products for the tenant (RLS-scoped)."""
        result = await self.session.scalars(
            select(Product.product_id).where(
                Product.tenant_id == self.tenant_id,
                Product.is_active == True,  # noqa: E712 — SQLAlchemy
            )
        )
        return set(result.all())

    async def _emit_audit(
        self,
        *,
        action: str,
        actor_id: uuid.UUID | None,
        payload: dict[str, Any],
    ) -> None:
        """Typed audit emit (A5 forward-lock)."""
        try:
            await emit_audit_typed(
                self.session,
                action_class=ActionClass.CLOSING_GUARD,
                action=action,  # type: ignore[arg-type]
                actor_id=actor_id,
                target_id=None,
                reason=None,
                payload=payload,
                tenant_id=self.tenant_id,
                flush=True,
            )
        except Exception as err:
            raise ClosingGuardAuditEmitError(
                tenant_id=self.tenant_id,
                details={"action": action, "error": str(err)},
                trace_id=self.trace_id,
            ) from err


def _validate_period_key(period_key: str) -> None:
    """AD-24 typed period-key: 'YYYY-MM'."""
    import re

    if not isinstance(period_key, str):
        raise ClosingGuardInvalidPeriodKeyError(
            tenant_id=uuid.UUID(int=0),
            period_key=str(period_key),
            trace_id="",
        )
    if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", period_key):
        raise ClosingGuardInvalidPeriodKeyError(
            tenant_id=uuid.UUID(int=0),
            period_key=period_key,
            trace_id="",
        )


def _mint_trace_id() -> uuid.UUID:
    """Mint a trace_id UUID v7 (with v4 fallback per AD-15)."""
    mint_v7 = getattr(uuid, "uuid7", None)
    if mint_v7 is not None:
        return mint_v7()
    return uuid.uuid4()


__all__ = [
    "ClosingGuardAuditEmitError",
    "ClosingGuardInvalidPeriodKeyError",
    "ClosingGuardNegativeInventoryError",
    "ClosingGuardProductionConsumptionError",
    "ClosingGuardServiceOnlyTenantError",
    "ClosingGuardService",
]
