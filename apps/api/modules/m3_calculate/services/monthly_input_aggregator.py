"""apps.api.modules.m3_calculate.services.monthly_input_aggregator — Read M2 inputs.

Story 4.2 (Task 2.3) — aggregate `monthly_input_rows` for a tenant's period
into the engine's `MonthlyInput` value object (4 KRW fields + FTE headcount).

The M2 module already aggregates for the UI list response (Story 3.1) and
the FTE headcount for the labor stream (Story 3.2). For Story 4.2 the
calc service needs a clean read of the 6 streams:

- direct_material_krw = SUM(amount_krw WHERE stream IN ('purchases'))
- direct_labor_krw    = SUM(monthly_salary_basis_krw + overtime + welfare +
                            bonus + retirement_reserve
                            WHERE stream = 'labor')
- indirect_krw        = SUM(amount_krw WHERE stream = 'expenses')
- fte_headcount       = total_fte (Story 3.2 `compute_fte_for_*` over all
                          labor rows; summed across all rows)

Returns the engine port's `MonthlyInput` (frozen dataclass). AD-5: no
clock, no random — but DB reads are OK at the adapter layer.

CR 1.1 + 2.1 lesson — reuse the M2 FTE helpers from
`packages.services.m2_input.labor_conversion` rather than re-implementing
the conversion logic. This avoids drift between calc and UI values.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.db_models import (
    MonthlyInputPeriod,
    MonthlyInputRow,
    TenantSettings,
)
from packages.cost_engine.core.money import KRW
from packages.cost_engine.ports.calc_port import MonthlyInput


class MonthlyInputAggregator:
    """Read monthly_input_rows for a (tenant, period) and shape into
    engine's `MonthlyInput` (frozen, pure value object).
    """

    def __init__(self, *, session: AsyncSession, trace_id: str) -> None:
        self._session = session
        self._trace_id = trace_id

    async def aggregate(
        self,
        *,
        tenant_id: uuid.UUID,
        period_key: str,
    ) -> MonthlyInput:
        """Aggregate 6 streams into `MonthlyInput`.

        Steps:
        1. Read period_id (FK target) via `monthly_input_periods`.
        2. Sum `amount_krw` over `purchases` rows → direct_material_krw.
        3. Sum 5 labor breakdown fields over `labor` rows → direct_labor_krw.
        4. Sum `amount_krw` over `expenses` rows → indirect_krw.
        5. Sum `fte_headcount` (computed from `labor_conversion`) → fte.
        6. Shape as `MonthlyInput` and return.

        Returns MonthlyInput. Empty sums → 0 (not NULL) so the engine's
        pure validation doesn't reject empty periods.
        """
        period_id = await self._load_period_id(tenant_id=tenant_id, period_key=period_key)
        if period_id is None:
            # No period — engine will reject via baseline gate. Return
            # zeroed MonthlyInput so caller can decide.
            return MonthlyInput(
                tenant_id=tenant_id,
                period_key=period_key,
                direct_material_krw=KRW(0),
                direct_labor_krw=KRW(0),
                indirect_krw=KRW(0),
                fte_headcount=Decimal("0"),
            )

        direct_material_krw = await self._sum_purchases(tenant_id=tenant_id, period_id=period_id)
        direct_labor_krw = await self._sum_labor_breakdown(tenant_id=tenant_id, period_id=period_id)
        indirect_krw = await self._sum_expenses(tenant_id=tenant_id, period_id=period_id)
        fte_headcount = await self._sum_fte(tenant_id=tenant_id, period_id=period_id)

        return MonthlyInput(
            tenant_id=tenant_id,
            period_key=period_key,
            direct_material_krw=KRW(int(direct_material_krw)),
            direct_labor_krw=KRW(int(direct_labor_krw)),
            indirect_krw=KRW(int(indirect_krw)),
            fte_headcount=fte_headcount,
        )

    # ── Internals ─────────────────────────────────────────────
    async def _load_period_id(self, *, tenant_id: uuid.UUID, period_key: str) -> uuid.UUID | None:
        stmt = select(MonthlyInputPeriod.period_id).where(
            MonthlyInputPeriod.tenant_id == tenant_id,
            MonthlyInputPeriod.period_key == period_key,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def _sum_purchases(self, *, tenant_id: uuid.UUID, period_id: uuid.UUID) -> int:
        """purchases stream → direct_material_krw."""
        stmt = select(func.coalesce(func.sum(MonthlyInputRow.amount_krw), 0)).where(
            MonthlyInputRow.tenant_id == tenant_id,
            MonthlyInputRow.period_id == period_id,
            MonthlyInputRow.stream == "purchases",
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def _sum_labor_breakdown(self, *, tenant_id: uuid.UUID, period_id: uuid.UUID) -> int:
        """labor stream → direct_labor_krw = sum of 5 breakdown fields.

        Story 3.2 §6.1 인건비 구성:
            monthly_salary_basis_krw + overtime_krw + welfare_krw +
            bonus_krw + retirement_reserve_krw

        COALESCE each column for NULL-safety (Story 3.2 nullable across
        all 6 streams; only set on labor).
        """
        col_sum = (
            func.coalesce(MonthlyInputRow.monthly_salary_basis_krw, 0)
            + func.coalesce(MonthlyInputRow.overtime_krw, 0)
            + func.coalesce(MonthlyInputRow.welfare_krw, 0)
            + func.coalesce(MonthlyInputRow.bonus_krw, 0)
            + func.coalesce(MonthlyInputRow.retirement_reserve_krw, 0)
        )
        stmt = select(func.coalesce(func.sum(col_sum), 0)).where(
            MonthlyInputRow.tenant_id == tenant_id,
            MonthlyInputRow.period_id == period_id,
            MonthlyInputRow.stream == "labor",
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def _sum_expenses(self, *, tenant_id: uuid.UUID, period_id: uuid.UUID) -> int:
        """expenses stream → indirect_krw."""
        stmt = select(func.coalesce(func.sum(MonthlyInputRow.amount_krw), 0)).where(
            MonthlyInputRow.tenant_id == tenant_id,
            MonthlyInputRow.period_id == period_id,
            MonthlyInputRow.stream == "expenses",
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def _sum_fte(self, *, tenant_id: uuid.UUID, period_id: uuid.UUID) -> Decimal:
        """Sum FTE headcount across all labor rows.

        Story 3.2 `compute_fte_for_*` decides monthly vs daily by
        `pay_type` per row. We iterate rows in Python (small set;
        MVP limit ~50 rows per tenant per period) and reuse the helper
        to avoid re-implementing the conversion logic (CR 2.1 lesson).
        """
        from packages.services.m2_input.labor_conversion import (
            compute_fte_for_daily,
            compute_fte_for_monthly,
        )

        stmt = select(
            MonthlyInputRow.pay_type,
            MonthlyInputRow.workers,
            MonthlyInputRow.days_per_worker,
            MonthlyInputRow.daily_wage_krw,
        ).where(
            MonthlyInputRow.tenant_id == tenant_id,
            MonthlyInputRow.period_id == period_id,
            MonthlyInputRow.stream == "labor",
        )
        result = await self._session.execute(stmt)
        rows = result.all()

        total = Decimal("0")
        for pay_type, workers, days_per_worker, _daily_wage in rows:
            if workers is None or workers <= 0:
                continue
            if pay_type == "daily":
                total += compute_fte_for_daily(
                    workers=workers,
                    days_per_worker=days_per_worker or 0,
                )
            else:  # 'monthly' or NULL → monthly default
                total += compute_fte_for_monthly(workers=workers)
        return total

    async def _read_tenant_payroll_settings(self, *, tenant_id: uuid.UUID) -> dict:
        """Read `tenant_settings.payroll` JSONB.

        Returns empty dict if unset. Story 3.2 FTE helpers accept empty
        defaults so this is safe.
        """
        stmt = select(TenantSettings.payroll).where(TenantSettings.tenant_id == tenant_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() or {}
