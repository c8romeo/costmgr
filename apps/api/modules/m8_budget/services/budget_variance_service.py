"""apps.api.modules.m8_budget.services.budget_variance_service — Story 8.2.

Service-layer orchestration for budget-actual variance fetch (PRD §F8.2).
READ-ONLY — no DB writes (CR 1.1 invariant + AC #5 test).

Pure kernel lives at `packages.cost_engine.budget_variance.py` (3 NEW
pure functions + 3 frozen dataclasses). Service layer wraps the kernel
with DB I/O + JSON envelope mapping.

AD-22 ledger append-only: 8-2 read-only — no audit emit per CR 1.1
invariant. A5 forward-lock 변경 0 (CR 11-3 D-2 즉시 sweep 회피).

Architecture (matches 8-1 budget_scenario_service pattern):
  - handler → service → engine (pure kernel)
  - `_to_budget_variance_row` ORM→kernel boundary (CR 12-1 L3 precedent)
  - 3-layer defense (CR 12-5 L3): route @require_role + service
    validate_variance_inputs + DB UNIQUE constraint (no-op for read-only)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Final

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.db_models import BudgetScenario
from apps.api.modules.m8_budget.exceptions import (
    BudgetVarianceNotFoundError,
    InvalidVariancePeriodError,
)
from packages.cost_engine.budget_variance import (
    Severity,
    VarianceRow,
    compute_abcd_disabled_badge,
    compute_variance,
    compute_variance_color,
)
from packages.services.m8_budget.budget_variance_serializers import (
    serialize_abcd_disabled_badge,
)

# V8 determinism + idempotency — 8-2는 read-only (no audit emit per CR 1.1
# invariant — 8-2는 A5 forward-lock 변경 0). audit_first=False 명시.
BUDGET_VARIANCE_INDUSTRY_AGNOSTIC: Final[bool] = True

# Period key pattern (AD-24 virtual `YYYY-MM#B<n>` — 8-1 wire).
VIRTUAL_BUDGET_PERIOD_KEY_PATTERN: Final[str] = (
    r"^\d{4}-(0[1-9]|1[0-2])#B([1-9]\d*)$"
)


@dataclass(frozen=True, slots=True)
class VarianceAggregationRow:
    """Internal aggregation row (story 8.2 read-only fetch shape).

    Service-layer DTO that mirrors the JOIN output of:
      budget_scenarios + monthly_input_periods + fiscal_period_snapshots
      + products (PRD §F8.2 verbatim).

    `label` = 항목명 (예: "직접재료", "직접노무", "제조경비")
    `budget_value` = Decimal (KRW integer, BIGINT)
    `actual_value` = Decimal (KRW integer, BIGINT)
    """

    label: str
    budget_value: Decimal
    actual_value: Decimal


def _to_budget_variance_row(
    aggregation: VarianceAggregationRow,
) -> VarianceRow:
    """ORM-aggregation → kernel boundary conversion (CR 12-1 L3 precedent).

    `VarianceAggregationRow` (service-layer DTO) →
    `packages.cost_engine.budget_variance.VarianceRow` (frozen dataclass).

    Pure kernel delegation: `compute_variance` + `compute_variance_color`.
    """
    variance = compute_variance(
        budget_value=aggregation.budget_value,
        actual_value=aggregation.actual_value,
    )
    color = compute_variance_color(variance_pct=variance.variance_pct)
    return VarianceRow(
        label=aggregation.label,
        variance=variance,
        color=color,
    )


def validate_variance_inputs(*, period_key: str) -> None:
    """CR 12-5 L3 3-layer defense — service-layer period key validation.

    Delegates to `parse_virtual_budget_period_key` (8-1 wire) to validate
    AD-24 virtual pattern `YYYY-MM#B<n>`. Real fiscal key (`2026-07`)
    또는 malformed string → `InvalidVariancePeriodError` (CR 12-5 D-14 envelope
    422 INVALID_VARIANCE_PERIOD).

    Pure kernel delegation (AD-5 + AD-11).
    """
    # Imported lazily to avoid circular import at module load.
    from packages.cost_engine.budget_period_key import (
        parse_virtual_budget_period_key,
    )

    try:
        parse_virtual_budget_period_key(period_key=period_key)
    except ValueError as exc:
        raise InvalidVariancePeriodError(
            (
                f"period_key must match YYYY-MM#B<n> for variance: "
                f"got {period_key!r}"
            ),
            period_key=period_key,
            expected_pattern=VIRTUAL_BUDGET_PERIOD_KEY_PATTERN,
        ) from exc


class BudgetVarianceService:
    """Story 8.2 — AD-24 virtual period key + PRD §F8.2 variance orchestrator.

    Thin orchestration wrapper around `packages.cost_engine.budget_variance`
    pure kernel. DB I/O lives here; pure logic lives in the kernel.

    8-2 is READ-ONLY: no INSERT/UPDATE/DELETE on budget_scenarios or
    fiscal_period_snapshots. CR 1.1 invariant — no audit emit.
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID,
        trace_id: str,
    ) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.actor_id = actor_id
        self.trace_id = trace_id

    async def fetch_variance_table(
        self, *, period_key: str
    ) -> list[VarianceRow]:
        """Fetch variance rows for the given period_key (PRD §F8.2).

        1. Delegate to `validate_variance_inputs(period_key)` (CR 12-5 L3
           service-layer validation, raises `InvalidVariancePeriodError`).
        2. SELECT FROM budget_scenarios WHERE tenant_id = :tenant_id AND
           period_key = :period_key (RLS same-tenant filter AD-3).
        3. Aggregate予算 vs 실적 from joined fiscal_period_snapshots
           (engine_type='trad', state='verified') + monthly_input_periods.
        4. For each row, delegate to `_to_budget_variance_row` (pure kernel
           compute_variance + compute_variance_color).
        5. Return list[VarianceRow] (sorted by label ASC, 8-3 honestly DEFER
           scenario-level grouping).

        Raises:
          InvalidVariancePeriodError — invalid period_key pattern (422).
          BudgetVarianceNotFoundError — no scenario for tenant (404).
        """
        # 1. Service-layer validation (CR 12-5 L3 3-layer defense).
        validate_variance_inputs(period_key=period_key)

        # 2. DB read (budget scenario lookup).
        stmt = (
            select(BudgetScenario)
            .where(
                BudgetScenario.tenant_id == self.tenant_id,
                BudgetScenario.period_key == period_key,
            )
        )
        result = await self.session.execute(stmt)
        scenario_row = result.scalar_one_or_none()
        if scenario_row is None:
            raise BudgetVarianceNotFoundError(
                period_key=period_key,
                tenant_id=str(self.tenant_id),
            )

        # 3-4. Aggregate budget vs actual from joined tables.
        # NOTE: monthly_budget_total column is honestly DEFER to a follow-up
        # Sprint (8-2 read-only + budget_scenarios table wire baseline only).
        # For 8-2 atomic wire, `_aggregate_variance_rows` returns empty list
        # by default; downstream handlers should treat empty as "no data".
        # 8-3 follow-up sprint will wire the actual JOIN query.
        aggregations = await self._aggregate_variance_rows(
            scenario_row=scenario_row,
        )
        return [_to_budget_variance_row(agg) for agg in aggregations]

    async def _aggregate_variance_rows(
        self,
        *,
        scenario_row: BudgetScenario,  # noqa: ARG002 (8-3 wire signature)
    ) -> list[VarianceAggregationRow]:
        """Aggregate budget vs actual for the given scenario (8-2 wire baseline).

        8-2 atomic wire: returns empty list (production-grade JOIN query
        honestly DEFER to follow-up sprint per CR 11-3 discipline).

        8-3 follow-up sprint: wire budget_scenarios JOIN monthly_input_periods
        JOIN fiscal_period_snapshots (engine_type='trad', state='verified')
        JOIN products aggregation. Read-only (no DB writes).

        Args:
          scenario_row: ORM BudgetScenario row (RLS-filtered).

        Returns:
          list[VarianceAggregationRow] — empty for 8-2 atomic wire.
        """
        # 8-2 atomic wire: empty aggregation (8-3 follow-up).
        return []

    async def compute_variance_total(
        self, *, rows: list[VarianceRow]
    ) -> VarianceRow:
        """Compute 합계 row from list of variance rows.

        1. sum of budget_value + actual_value across rows.
        2. Delegate to `compute_variance` (pure kernel).
        3. Return VarianceRow with label="합계" + is_total=True.

        Pure kernel delegation (AD-5 + AD-11).
        """
        if not rows:
            # Empty rows → zero variance (defense-in-depth).
            total_variance = compute_variance(
                budget_value=Decimal("0"),
                actual_value=Decimal("0"),
            )
            total_color = compute_variance_color(
                variance_pct=total_variance.variance_pct,
            )
            return VarianceRow(
                label="합계",
                variance=total_variance,
                color=total_color,
            )

        total_budget = sum(
            (row.variance.budget_value for row in rows),
            Decimal("0"),
        )
        total_actual = sum(
            (row.variance.actual_value for row in rows),
            Decimal("0"),
        )
        total_variance = compute_variance(
            budget_value=total_budget,
            actual_value=total_actual,
        )
        total_color = compute_variance_color(
            variance_pct=total_variance.variance_pct,
        )
        return VarianceRow(
            label="합계",
            variance=total_variance,
            color=total_color,
        )

    async def fetch_abcd_disabled_badge(
        self, *, variant: str = "variance"
    ) -> dict[str, object]:
        """Fetch A×B×C×D 회색 배지 placeholder (PRD §15 NON-GOAL #1 + §10 M8 (b)).

        1차 MVP: 회색 배지 disabled + "2차 예정" + "A×B×C×D 편성 엔진 미구현".
        8-3 follow-up: engine_type='abcd' retrofit foundation.

        Pure kernel delegation (AD-5 + AD-11).
        """
        if variant not in ("variance", "trend", "sensitivity"):
            raise ValueError(
                f"variant must be one of 'variance'/'trend'/'sensitivity', "
                f"got {variant!r}"
            )
        badge = compute_abcd_disabled_badge(variant=variant)  # type: ignore[arg-type]
        return serialize_abcd_disabled_badge(badge)

    async def generate_budget_variance_pdf(
        self,
        *,
        period_key: str,
        scenario_index: int = 1,
    ) -> bytes:
        """Generate budget variance PDF (8-3 wire activation, 8-2 DEFER 해소).

        8-2 atomic wire: placeholder `pass` → empty bytes.
        8-3 wire (8-2 spec line 273 placeholder 해소): delegate to
        `BudgetPreStandardService.generate_budget_variance_pdf` (8-3 wire)
        which reuses the pre-standard snapshot + Epic 6 M5 PDF generator
        (READ-ONLY pattern, A4 portrait + KRW integer + ko-KR only).

        425 if pre-standard snapshot NOT yet inserted (8-2 race condition
        방지 동일 패턴).
        """
        # 8-3 wire activation: delegate to BudgetPreStandardService for the
        # actual PDF generation (8-2 placeholder 활성화).
        from apps.api.modules.m8_budget.services import (
            BudgetPreStandardService,
        )

        pre_standard_service = BudgetPreStandardService(
            self.session,
            tenant_id=self.tenant_id,
            actor_id=self.actor_id,
            trace_id=self.trace_id,
        )
        return await pre_standard_service.generate_budget_variance_pdf(
            period_key=period_key,
            scenario_index=scenario_index,
        )

    async def fetch_variance_with_total(
        self, *, period_key: str
    ) -> tuple[list[VarianceRow], VarianceRow]:
        """Fetch variance rows + 합계 row (atomic convenience method).

        1. Delegate to `fetch_variance_table(period_key)`.
        2. Delegate to `compute_variance_total(rows)`.
        3. Return (rows, total_row) tuple.

        AC #3 + AC #6 endpoint convenience wrapper.
        """
        rows = await self.fetch_variance_table(period_key=period_key)
        total_row = await self.compute_variance_total(rows=rows)
        return rows, total_row


# Severity type alias for external import convenience.
BudgetVarianceSeverity = Severity
