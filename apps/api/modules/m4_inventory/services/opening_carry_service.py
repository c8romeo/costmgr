"""apps.api.modules.m4_inventory.services.opening_carry_service — Story 5.1.

Backend service for the opening_inventory JSONB auto-carry chain
(PRD §F4.1). Wraps the pure kernel in
`packages.services.m2_input.opening_carry` with:

- 5 service operations (T2): `trigger_carry_chain_for_period`,
  `auto_carry_on_get_state`, `lock_opening_after_first_row`,
  `recompute_opening_on_prev_change`, `validate_opening_lock_consistency`.
- 4 typed exceptions (AD-15 §4 envelope mapping):
  - `MonthlyInputOpeningManualEditError` (400)
    — user attempts to write `stream='opening_inventory'` row
  - `MonthlyInputOpeningLockViolationError` (500)
    — JSONB shape guard, defense-in-depth (Epic 11 reversal entrypoint)
  - `MonthlyInputCarryChainLimitError` (422)
    — chain depth > 12 (manual trigger required)
  - `MonthlyInputCarryPrevPeriodNotFoundError` (422)
    — prev_period_key has no period row for the tenant

Layering (AD-11):
- Pure kernel: `packages/services/m2_input/opening_carry.py` (T1, ✅)
- Service layer (this file): SQLAlchemy AsyncSession + audit-first
  emit (CR 1.1 lesson) + 12-period chain limit guard.

Concurrency:
- `SELECT FOR UPDATE` on `monthly_input_periods` to prevent concurrent
  carry-chain races (Story 3.1 m2_input_service.save_row pattern).
- DB-level UNIQUE constraint on (tenant_id, period_key,
  baseline_revision) ensures the prev_period lookup is safe under
  concurrent INSERT.

A5 forward-lock:
- Audit rows route to `audit_logs` (not `inventory_ledger`) for
  Story 5.1 (5-2 wires the dedicated inventory_ledger destination).
- ActionClass.MONTHLY_INPUT_PERIOD used; new action literal
  `opening_carry_auto` extends the registry in
  `apps.api/core/audit_action.py` (T5 forward-fill).
"""

from __future__ import annotations

import uuid
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from apps.api.core.db_models import MonthlyInputPeriod, MonthlyInputRow
from packages.services.m0_onboarding.industry_menu import Industry
from packages.services.m2_input.inventory_projection import (
    build_inventory_projection,
)
from packages.services.m2_input.opening_carry import (
    INVENTORY_PERIOD_CHAIN_LIMIT,
    OpeningCarryDecision,
    compute_carry_chain,
    lock_opening_after_first_row,
    resolve_opening_balance,
)
from packages.services.m2_input.opening_carry import (
    validate_opening_lock_consistency as _validate_kernel_lock_consistency,
)

# ─────────────────────────────────────────────────────────────
# Typed exceptions (mapped to HTTP by handlers.py / main.py)
# ─────────────────────────────────────────────────────────────


class MonthlyInputOpeningManualEditError(Exception):
    """400 MONTHLY_INPUT_OPENING_MANUAL_EDIT — user tried to write
    `stream='opening_inventory'` row.

    PRD §F4.1: opening_inventory is auto-carried after first-row lock;
    manual write is rejected.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"opening_inventory for {period_key} (tenant {tenant_id}) "
            f"is auto-carried; manual row write rejected"
        )
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.trace_id = trace_id


class MonthlyInputOpeningLockViolationError(Exception):
    """500 MONTHLY_INPUT_OPENING_LOCK_VIOLATION — JSONB shape
    inconsistent.

    Defense-in-depth guard against drift between opening_inventory JSONB
    and lock state. tenant-wide consistency check should catch
    corruption before it spreads to other tenants.
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
            f"opening_inventory lock shape violated for {period_key} "
            f"(tenant {tenant_id}): {details}"
        )
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.details = details
        self.trace_id = trace_id


class MonthlyInputCarryChainLimitError(Exception):
    """422 MONTHLY_INPUT_CARRY_CHAIN_LIMIT — chain depth > 12.

    Manual trigger required for deeper chains. Operator must
    explicitly invoke POST /api/v1/inventory/opening-carry/{period_id}
    to extend beyond the 12-period limit.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        depth: int,
        period_key: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"carry chain depth {depth} exceeds limit "
            f"{INVENTORY_PERIOD_CHAIN_LIMIT} for {period_key} "
            f"(tenant {tenant_id})"
        )
        self.tenant_id = tenant_id
        self.depth = depth
        self.period_key = period_key
        self.trace_id = trace_id


class MonthlyInputCarryPrevPeriodNotFoundError(Exception):
    """422 MONTHLY_INPUT_CARRY_PREV_PERIOD_NOT_FOUND — prev_period_key
    has no period row for the tenant.

    Auto-carry cannot proceed without a previous period's projection
    target. Operator should create the prev period first OR pass
    `prev_period_key=None` to skip carry (creates empty opening).
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        prev_period_key: str,
        current_period_key: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"prev period {prev_period_key} not found for tenant "
            f"{tenant_id} (current={current_period_key})"
        )
        self.tenant_id = tenant_id
        self.prev_period_key = prev_period_key
        self.current_period_key = current_period_key
        self.trace_id = trace_id


# ─────────────────────────────────────────────────────────────
# Helper: decode opening_inventory JSONB
# ─────────────────────────────────────────────────────────────


def _decode_opening_jsonb(
    raw: dict[str, Any] | None,
) -> dict[uuid.UUID, Decimal]:
    """Decode `monthly_input_periods.opening_inventory` JSONB into
    `dict[UUID, Decimal]`, stripping special lock markers
    (`_locked`, `_lock_reason_ko`).

    H7: Malformed values (NaN/Infinity/null/non-string/non-numeric) raise
    MonthlyInputOpeningLockViolationError (500 AD-15 envelope) instead of
    silent skip — defense-in-depth guard for JSONB 정합성.
    """
    if not raw:
        return {}
    out: dict[uuid.UUID, Decimal] = {}
    for k, v in raw.items():
        if k.startswith("_"):
            continue  # lock markers
        try:
            value_decimal = Decimal(str(v))
            if not value_decimal.is_finite():
                raise ValueError(f"non-finite Decimal: {v}")
            out[uuid.UUID(k)] = value_decimal
        except (ValueError, TypeError, InvalidOperation) as err:
            # H7: silent continue → typed exception (defense-in-depth)
            raise MonthlyInputOpeningLockViolationError(
                tenant_id=None,
                period_key="<decode>",
                lock_reason_ko=f"opening_inventory JSONB malformed: key={k}, value={v}",
                trace_id=None,
            ) from err
    return out


# ─────────────────────────────────────────────────────────────
# OpeningCarryService
# ─────────────────────────────────────────────────────────────


class OpeningCarryService:
    """Story 5.1 — opening inventory auto-carry chain service.

    All state-changing operations write a typed audit_logs row BEFORE
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

    # ── Operation 1: manual trigger ───────────────────────────
    async def trigger_carry_chain_for_period(
        self,
        period_id: uuid.UUID,
        *,
        prev_period_key: str | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Manual trigger via POST /api/v1/inventory/opening-carry/{period_id}.

        Loads current period + (optionally) prev period, builds carry
        chain decisions, resolves final opening balance, and UPDATEs
        `monthly_input_periods.opening_inventory` with audit-first.

        Args:
            period_id: target period_id.
            prev_period_key: explicit prev period_key override; None →
                load most recent prev period (period_key < current).
            actor_id: actor who triggered; None for system cron.

        Returns:
            Carry chain result envelope:
            {
              "period_id": str,
              "period_key": str,
              "prev_period_key": str | None,
              "decisions": list[dict],
              "opening_inventory": dict[str, str],
              "chain_depth": int,
              "trace_id": str,
            }

        Raises:
            MonthlyInputNotFoundError: period_id not found for tenant.
            MonthlyInputCarryChainLimitError: depth > 12.
        """
        period = await self._load_period_for_update(period_id)
        return await self._run_carry_chain(
            period,
            prev_period_key=prev_period_key,
            actor_id=actor_id,
            trigger_source="manual",
        )

    # ── Operation 2: get_state auto-carry hook ─────────────────
    async def auto_carry_on_get_state(
        self,
        period: MonthlyInputPeriod,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> list[OpeningCarryDecision]:
        """Hook for `monthly_input_service.get_state`.

        Called BEFORE the warning aggregate computes opening balance.
        If the current period's opening_inventory JSONB is empty AND
        a prev period exists, run the carry chain (silent — no
        explicit actor).

        Idempotent: if opening_inventory is already populated (locked
        or partial), no-op.

        Returns:
            List of OpeningCarryDecision applied (may be empty if
            no-op).
        """
        # Idempotent no-op: opening_inventory already has content
        current_decoded = _decode_opening_jsonb(period.opening_inventory)
        if current_decoded and period.opening_inventory.get("_locked"):
            return []  # already locked — first-row INSERT happened

        # Find prev period (period_key < current, baseline_revision == 1)
        prev_period_key = self._prev_period_key(period.period_key)
        if prev_period_key is None:
            return []  # cj-style default: no prev → empty opening

        # H8: 12-period chain depth guard (PRD §F4.1) — auto path 동일 적용
        chain_depth = await self._compute_chain_depth(prev_period_key)
        if chain_depth >= INVENTORY_PERIOD_CHAIN_LIMIT:
            # silent skip (manual trigger 시 422 MONTHLY_INPUT_CARRY_CHAIN_LIMIT 안내)
            return []

        # H3: SELECT FOR UPDATE on prev period (concurrency guard — CR 1.1 idempotent no-op)
        prev_period = await self._load_period_by_key_for_update(prev_period_key)
        if prev_period is None:
            return []  # cj-style default: silent no-op

        # Build prev period's closing balance
        prev_closing = await self._compute_period_closing(prev_period)

        # Carry chain
        decisions = compute_carry_chain(
            prev_period_projection=prev_closing,
            current_period_state=current_decoded,
            prev_period_key=prev_period_key,
        )
        # H10: empty decisions while current non-empty → silent no-op (이미 균형)
        if not decisions:
            if current_decoded:
                return []  # already balanced — silent no-op
            return []  # cj-style default: no prev closing → empty opening

        # Resolve + UPDATE
        final = resolve_opening_balance(
            current_opening_jsonb=period.opening_inventory,
            carry_chain_result=decisions,
        )
        await self._persist_opening(
            period,
            new_opening=final,
            decisions=decisions,
            prev_period_key=prev_period_key,
            actor_id=actor_id,
            trigger_source="auto_get_state",
        )
        return decisions

    # ── Operation 3: first-row lock hook ───────────────────────
    async def lock_opening_after_first_row(
        self,
        period: MonthlyInputPeriod,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> dict[uuid.UUID, Decimal | str]:
        """Hook for `monthly_input_service.save_row` (first INSERT).

        PRD §F4.1: after first row INSERT, opening_inventory is locked
        (manual writes rejected). Lock marker (`_locked`,
        `_lock_reason_ko`) is added to JSONB.

        Returns:
            Updated opening_inventory dict (incl. lock markers).
        """
        current_decoded = _decode_opening_jsonb(period.opening_inventory)
        if period.opening_inventory.get("_locked"):
            return period.opening_inventory  # idempotent

        locked = lock_opening_after_first_row(
            current_decoded,
            lock_reason_ko="전월 기말 자동 이월",
        )

        # Audit-first
        await emit_audit_typed(
            self.session,
            action_class=ActionClass.MONTHLY_INPUT_PERIOD,
            action="monthly_input_period_opening_locked",
            actor_id=actor_id,
            target_id=period.period_id,
            payload={
                "tenant_id": str(self.tenant_id),
                "period_key": period.period_key,
                "lock_reason_ko": "전월 기말 자동 이월",
                "trace_id": self.trace_id,
            },
            tenant_id=self.tenant_id,
            flush=True,
        )

        period.opening_inventory = locked  # type: ignore[assignment]
        period.updated_at = _now_utc()
        return locked  # type: ignore[return-value]

    # ── Operation 4: prev-period row mutation recompute ────────
    async def recompute_opening_on_prev_change(
        self,
        prev_period_key: str,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> list[OpeningCarryDecision]:
        """When prev period's monthly_input_rows are mutated
        (save_row / delete_row / update_row), recompute the next
        period's opening carry chain.

        Defensive — if next period's opening_inventory is locked,
        the lock marker is preserved (manual unlock required via
        Epic 11 reversal entrypoint).

        Returns:
            Decisions applied to next period (may be empty).
        """
        next_period_key = self._next_period_key(prev_period_key)
        if next_period_key is None:
            return []

        # H12: chain propagation (AC #3 "chain" 명시) — while loop walk forward
        # cycle guard: 다음 period가 다시 prev로 돌아오면 stop (depth limit + cycle)
        all_decisions: list[OpeningCarryDecision] = []
        depth = 0
        current_key = prev_period_key
        seen_keys: set[str] = {prev_period_key}

        while depth < INVENTORY_PERIOD_CHAIN_LIMIT:
            next_key = self._next_period_key(current_key)
            if next_key is None or next_key in seen_keys:
                break  # cycle guard + chain end
            seen_keys.add(next_key)

            next_period = await self._load_period_by_key_for_update(next_key)
            if next_period is None:
                break  # no next period yet — silent

            # Skip if locked (reversal entrypoint needed)
            if next_period.opening_inventory.get("_locked"):
                break  # lock marker 보존 (Epic 11 reversal 진입점)

            decisions = await self.auto_carry_on_get_state(
                next_period,
                actor_id=actor_id,
            )
            all_decisions.extend(decisions)
            if not decisions:
                break  # no propagation needed — early exit
            depth += 1
            current_key = next_key

        return all_decisions

    # ── Operation 5: tenant-wide consistency check ────────────
    async def validate_opening_lock_consistency(
        self,
        period: MonthlyInputPeriod,
    ) -> None:
        """Tenant-wide defense-in-depth guard for opening_inventory
        JSONB shape consistency.

        Wraps the pure kernel
        `validate_opening_lock_consistency()` with a typed exception
        for Epic 11 reversal entrypoint.
        """
        try:
            _validate_kernel_lock_consistency(period.opening_inventory)
        except Exception as e:
            raise MonthlyInputOpeningLockViolationError(
                tenant_id=self.tenant_id,
                period_key=period.period_key,
                details={"kernel_message": str(e)},
                trace_id=self.trace_id,
            ) from e

    # ── Internal helpers ──────────────────────────────────────
    async def _load_period_for_update(self, period_id: uuid.UUID) -> MonthlyInputPeriod:
        """SELECT FOR UPDATE — period row by id (tenant-scoped)."""
        period = await self.session.scalar(
            select(MonthlyInputPeriod)
            .where(
                MonthlyInputPeriod.tenant_id == self.tenant_id,
                MonthlyInputPeriod.period_id == period_id,
            )
            .with_for_update()
        )
        if period is None:
            from apps.api.modules.m2_input.services.monthly_input_service import (
                MonthlyInputNotFoundError,
            )

            raise MonthlyInputNotFoundError(
                tenant_id=self.tenant_id,
                period_key=None,
                row_id=None,
                trace_id=self.trace_id,
            )
        return period

    async def _load_period_by_key(self, period_key: str) -> MonthlyInputPeriod | None:
        """Load period by (tenant_id, period_key, baseline_revision=1)."""
        return await self.session.scalar(
            select(MonthlyInputPeriod).where(
                MonthlyInputPeriod.tenant_id == self.tenant_id,
                MonthlyInputPeriod.period_key == period_key,
                MonthlyInputPeriod.baseline_revision == 1,
            )
        )

    async def _load_period_by_key_for_update(self, period_key: str) -> MonthlyInputPeriod | None:
        """H3: SELECT FOR UPDATE on period — concurrency guard (CR 1.1 idempotent no-op).

        Used by auto_carry_on_get_state to prevent two concurrent get_state
        calls from emitting duplicate audit + UPDATE.
        """
        return await self.session.scalar(
            select(MonthlyInputPeriod)
            .where(
                MonthlyInputPeriod.tenant_id == self.tenant_id,
                MonthlyInputPeriod.period_key == period_key,
                MonthlyInputPeriod.baseline_revision == 1,
            )
            .with_for_update()
        )

    async def _compute_period_closing(self, period: MonthlyInputPeriod) -> dict[uuid.UUID, Decimal]:
        """Compute closing balance for a period (rebuilds projection
        from monthly_input_rows).

        Pure-kernel wrapper: reads `monthly_input_rows` for the period,
        feeds them to `build_inventory_projection`, returns
        `dict[UUID, Decimal]` (product_id → closing_qty).
        """
        rows = await self.session.scalars(
            select(MonthlyInputRow).where(
                MonthlyInputRow.tenant_id == self.tenant_id,
                MonthlyInputRow.period_id == period.period_id,
            )
        )
        rows_list = list(rows.all())

        opening_decoded = _decode_opening_jsonb(period.opening_inventory)
        projections = build_inventory_projection(rows_list, opening_decoded)

        from packages.services.m2_input.inventory_projection import (
            compute_closing_inventory,
        )

        closing: dict[uuid.UUID, Decimal] = {}
        for movement in projections:
            closing[movement.product_id] = compute_closing_inventory(
                movement.opening_qty,
                movement.inbound_qty,
                movement.outbound_qty,
            )
        return closing

    async def _persist_opening(
        self,
        period: MonthlyInputPeriod,
        *,
        new_opening: dict[uuid.UUID, Decimal],
        decisions: list[OpeningCarryDecision],
        prev_period_key: str,
        actor_id: uuid.UUID | None,
        trigger_source: str,
    ) -> None:
        """Persist updated opening_inventory JSONB + audit row.

        Story 5.2 addition: per-decision `inventory_ledger_event_appended`
        emit. Each carry decision becomes ONE ledger row (event_type
        `opening_carried` for fresh carry, `opening_carried_stale_overwrite`
        when the previous period's data shifted and we're overwriting a
        stale value — `decision.recompute=True`).

        The audit log emission happens AFTER the JSONB update so the
        decision metadata (period_key + product_id + qty + trace_id) is
        immutable at the time of the ledger INSERT.

        Preserves lock marker (`_locked`, `_lock_reason_ko`) if present.
        """
        merged: dict[str, Any] = {
            str(pid): str(qty) for pid, qty in sorted(new_opening.items(), key=lambda x: str(x[0]))
        }
        # Preserve lock marker
        if period.opening_inventory.get("_locked"):
            merged["_locked"] = True
            merged["_lock_reason_ko"] = period.opening_inventory.get(
                "_lock_reason_ko", "전월 기말 자동 이월"
            )

        # Audit-first (5-1 pattern — monthly_input_period_opening_carried)
        await emit_audit_typed(
            self.session,
            action_class=ActionClass.MONTHLY_INPUT_PERIOD,
            action="monthly_input_period_opening_carried",
            actor_id=actor_id,
            target_id=period.period_id,
            payload={
                "tenant_id": str(self.tenant_id),
                "period_key": period.period_key,
                "prev_period_key": prev_period_key,
                "trigger_source": trigger_source,
                "decisions_count": len(decisions),
                "decisions": [
                    {
                        "product_id": str(d.product_id),
                        "opening_qty": str(d.opening_qty),
                        "is_stale": d.is_stale,
                        "recompute": d.recompute,
                    }
                    for d in decisions
                ],
                "trace_id": self.trace_id,
            },
            tenant_id=self.tenant_id,
            flush=True,
        )

        period.opening_inventory = merged
        period.updated_at = _now_utc()

        # Story 5.2 — AD-2 append-only ledger emit (per-decision).
        # Each OpeningCarryDecision becomes one inventory_ledger row.
        # Two immutable logs are emitted simultaneously (CR 1.1):
        #   1. audit_logs.action='monthly_input_period_opening_carried'
        #      (above, MONTHLY_INPUT_PERIOD target — 5-1 wire)
        #   2. audit_logs.action='inventory_ledger_event_appended' +
        #      inventory_ledger.event_type IN ('opening_carried',
        #      'opening_carried_stale_overwrite')
        #      (LedgerService.append_event — this method)
        # Both rows are INSERT-only; AD-2 invariant preserved on
        # both targets.
        await self._emit_ledger_events_for_decisions(
            period=period,
            decisions=decisions,
            prev_period_key=prev_period_key,
            actor_id=actor_id,
            trigger_source=trigger_source,
        )

    async def _emit_ledger_events_for_decisions(
        self,
        *,
        period: MonthlyInputPeriod,
        decisions: list[OpeningCarryDecision],
        prev_period_key: str,
        actor_id: uuid.UUID | None,
        trigger_source: str,
    ) -> None:
        """Emit per-decision `inventory_ledger_event_appended` rows.

        Story 5.2 AC #4 — opening carry decisions are now routed to
        the inventory_ledger table (in addition to the 5-1 audit_logs
        emission that is preserved above).

        Mapping:
        - `decision.recompute=False` → event_type='opening_carried'
        - `decision.recompute=True`  → event_type='opening_carried_stale_overwrite'

        The ledger event_type SSOT is the 11-value whitelist in
        `packages/services/m4_inventory/ledger.py::INVENTORY_LEDGER_EVENT_TYPES`.

        Lazy import: LedgerService is in the same package, but lazy
        import keeps startup clean + avoids any circular-import risk.
        """
        # Lazy import (sibling module — no circular risk, but lazy for clarity)
        from apps.api.modules.m4_inventory.services.ledger_service import (
            LedgerService,
        )
        from packages.services.m4_inventory.ledger import (
            SOURCE_CARRY_CHAIN,
        )

        ledger_svc = LedgerService(
            self.session,
            tenant_id=self.tenant_id,
            industry=self.industry,
            trace_id=self.trace_id,
        )
        for decision in decisions:
            event_type = (
                "opening_carried_stale_overwrite" if decision.recompute else "opening_carried"
            )
            await ledger_svc.append_event(
                product_id=decision.product_id,
                period_key=period.period_key,
                event_type=event_type,
                qty=decision.opening_qty,
                source=SOURCE_CARRY_CHAIN,
                metadata={
                    "prev_period_key": prev_period_key,
                    "is_stale": decision.is_stale,
                    "trigger_source": trigger_source,
                },
                actor_id=actor_id,
            )

    async def _run_carry_chain(
        self,
        period: MonthlyInputPeriod,
        *,
        prev_period_key: str | None,
        actor_id: uuid.UUID | None,
        trigger_source: str,
    ) -> dict[str, Any]:
        """Run the carry chain end-to-end (manual + auto paths share)."""
        if prev_period_key is None:
            prev_period_key = self._prev_period_key(period.period_key)
            if prev_period_key is None:
                raise MonthlyInputCarryPrevPeriodNotFoundError(
                    tenant_id=self.tenant_id,
                    prev_period_key="<none>",
                    current_period_key=period.period_key,
                    trace_id=self.trace_id,
                )

        prev_period = await self._load_period_by_key(prev_period_key)
        if prev_period is None:
            raise MonthlyInputCarryPrevPeriodNotFoundError(
                tenant_id=self.tenant_id,
                prev_period_key=prev_period_key,
                current_period_key=period.period_key,
                trace_id=self.trace_id,
            )

        # Chain depth guard
        depth = await self._compute_chain_depth(prev_period)
        if depth > INVENTORY_PERIOD_CHAIN_LIMIT:
            raise MonthlyInputCarryChainLimitError(
                tenant_id=self.tenant_id,
                depth=depth,
                period_key=period.period_key,
                trace_id=self.trace_id,
            )

        prev_closing = await self._compute_period_closing(prev_period)
        current_decoded = _decode_opening_jsonb(period.opening_inventory)
        decisions = compute_carry_chain(
            prev_period_projection=prev_closing,
            current_period_state=current_decoded,
            prev_period_key=prev_period_key,
        )
        final = resolve_opening_balance(
            current_opening_jsonb=period.opening_inventory,
            carry_chain_result=decisions,
        )
        await self._persist_opening(
            period,
            new_opening=final,
            decisions=decisions,
            prev_period_key=prev_period_key,
            actor_id=actor_id,
            trigger_source=trigger_source,
        )
        return {
            "period_id": str(period.period_id),
            "period_key": period.period_key,
            "prev_period_key": prev_period_key,
            "decisions": [
                {
                    "product_id": str(d.product_id),
                    "opening_qty": str(d.opening_qty),
                    "is_stale": d.is_stale,
                    "recompute": d.recompute,
                }
                for d in decisions
            ],
            "opening_inventory": {str(pid): str(qty) for pid, qty in final.items()},
            "chain_depth": depth,
            "trigger_source": trigger_source,
            "trace_id": self.trace_id,
        }

    async def _compute_chain_depth(self, period: MonthlyInputPeriod) -> int:
        """Walk backward from `period` counting prev periods."""
        depth = 1
        cursor = period
        seen: set[uuid.UUID] = {period.period_id}
        for _ in range(INVENTORY_PERIOD_CHAIN_LIMIT + 1):
            prev_key = self._prev_period_key(cursor.period_key)
            if prev_key is None:
                return depth
            prev = await self._load_period_by_key(prev_key)
            if prev is None:
                return depth
            if prev.period_id in seen:
                return depth  # cycle guard (defensive)
            seen.add(prev.period_id)
            depth += 1
            cursor = prev
        return depth

    @staticmethod
    def _prev_period_key(period_key: str) -> str | None:
        """Return the previous period_key (YYYY-MM → YYYY-(MM-1)).

        cj-style default: returns None if period_key is malformed.

        M3: validation 강화 — month must be 1..12 (silent reject for
        malformed keys like 00, 13, 'XX').
        """
        try:
            year_str, month_str = period_key.split("-")
            year, month = int(year_str), int(month_str)
            if not (1 <= month <= 12):
                return None  # M3: month out of range
            if month == 1:
                return f"{year - 1}-12"
            return f"{year}-{month - 1:02d}"
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _next_period_key(period_key: str) -> str | None:
        """Return the next period_key (YYYY-MM → YYYY-(MM+1)).

        M3: validation 강화 — month must be 1..12.
        """
        try:
            year_str, month_str = period_key.split("-")
            year, month = int(year_str), int(month_str)
            if not (1 <= month <= 12):
                return None  # M3: month out of range
            if month == 12:
                return f"{year + 1}-01"
            return f"{year}-{month + 1:02d}"
        except (ValueError, AttributeError):
            return None


def _now_utc():
    from datetime import UTC, datetime

    return datetime.now(tz=UTC)


__all__ = [
    "MonthlyInputCarryChainLimitError",
    "MonthlyInputCarryPrevPeriodNotFoundError",
    "MonthlyInputOpeningLockViolationError",
    "MonthlyInputOpeningManualEditError",
    "OpeningCarryService",
]
