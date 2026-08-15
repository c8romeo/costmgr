"""apps.api.modules.m7_simulation.services.cvp_simulation_service — Story 7.1.

Service-layer orchestration for CVP/BEP simulation (read-only, no DB writes).

AD-1 / AD-11 binding: handler → service (here) → packages.cost_engine.cvp
(pure kernel, stdlib-only). All DB I/O lives here; pure logic lives in
the kernel.

AD-22 ledger append-only: 7-1 is read-only (slider simulation), no audit
emit (CR 1.1 honest-DEFER — read-only operations skip audit). Verified
by `tests/integration/test_m7_simulation_no_db_writes.py` (audit_logs
row 0건 + fiscal_period_snapshots/monthly_input_periods no UPDATE).

CR 12-1 L3 precedent: `_to_cvp_baseline(snapshot, product)` ORM→kernel
boundary conversion (mirrors 12-1 `_to_totp_state` and 8-1
`_to_budget_scenario` patterns).
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.db_models import FiscalPeriodSnapshot, Product
from apps.api.modules.m7_simulation.exceptions import CVPBaselineNotFoundError
from packages.cost_engine.cvp import (
    DEFAULT_OPERATING_RATE,
    DEFAULT_TARGET_PROFIT,
    CVPBaseline,
    CVPDelta,
    CVPResult,
    simulate_cvp,
)


# V8 determinism + idempotency — 7-1 is read-only (no audit emit per CR 1.1
# honest-DEFER — simulation skips audit_logs). `audit_first=False` enforced
# by integration test (no DB writes).
class CVPSimulationService:
    """Story 7.1 — CVP/BEP simulation thin orchestrator.

    Thin orchestration wrapper around `packages.cost_engine.cvp` pure kernel.
    DB I/O lives here (baseline fetch); pure logic lives in the kernel.
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

    async def fetch_cvp_baseline(
        self, *, period_key: str
    ) -> tuple[CVPBaseline, str, str]:
        """Fetch CVP baseline from latest committed snapshot + products.

        Data source:
        - `fiscal_period_snapshots` WHERE tenant_id = :tenant_id
          AND state = 'committed' AND period_key = :period_key
          (latest `created_at` DESC, 1 row top)
        - `products` WHERE tenant_id = :tenant_id AND is_active = TRUE
          (AVG unit_cost_krw as `unit_price` proxy, unit_variable_cost
          derived as 60% of unit_price baseline — PRD §F7.1 단순화)

        Returns:
            (CVPBaseline, source_period_key, fiscal_period_state) tuple.

        Raises:
            CVPBaselineNotFoundError: no committed snapshot for the period.
        """
        # 1. Latest committed snapshot (RLS same-tenant filter, AD-3).
        snap_stmt = (
            select(FiscalPeriodSnapshot)
            .where(
                FiscalPeriodSnapshot.tenant_id == self.tenant_id,
                FiscalPeriodSnapshot.period_key == period_key,
                FiscalPeriodSnapshot.state == "committed",
            )
            .order_by(FiscalPeriodSnapshot.created_at.desc())
            .limit(1)
        )
        snap_result = await self.session.execute(snap_stmt)
        snapshot = snap_result.scalar_one_or_none()
        if snapshot is None:
            raise CVPBaselineNotFoundError(
                tenant_id=str(self.tenant_id),
                period_key=period_key,
            )

        # 2. Active products aggregation (unit_price baseline).
        prod_stmt = (
            select(
                func.avg(Product.unit_cost_krw).label("avg_unit_price"),
            )
            .where(
                Product.tenant_id == self.tenant_id,
                Product.is_active.is_(True),
                Product.unit_cost_krw.is_not(None),
            )
        )
        prod_result = await self.session.execute(prod_stmt)
        row = prod_result.first()
        avg_unit_price = (
            Decimal(int(row.avg_unit_price))
            if row is not None and row.avg_unit_price is not None
            else Decimal("0")
        )

        # 3. Derive baseline CVP fields:
        # - fixed_cost = snapshot.overhead_cost + snapshot.material_cost (KRW)
        # - unit_variable_cost = avg_unit_price * 0.6 (PRD §F7.1 단순화)
        # - unit_price = avg_unit_price (or fallback to 1 if 0)
        # - operating_rate = DEFAULT_OPERATING_RATE (1.0)
        # - target_profit = DEFAULT_TARGET_PROFIT (0)
        fixed_cost = Decimal(int(snapshot.overhead_cost + snapshot.material_cost))
        unit_price = (
            avg_unit_price
            if avg_unit_price > 0
            else Decimal("10000")  # fallback default — 10,000원/unit
        )
        unit_variable_cost = unit_price * Decimal("0.6")

        baseline = CVPBaseline(
            fixed_cost=fixed_cost,
            unit_variable_cost=unit_variable_cost,
            unit_price=unit_price,
            operating_rate=DEFAULT_OPERATING_RATE,
            target_profit=DEFAULT_TARGET_PROFIT,
        )

        return (
            baseline,
            snapshot.period_key,
            snapshot.state,
        )

    async def simulate_cvp(
        self,
        *,
        baseline: CVPBaseline,
        delta: CVPDelta,
    ) -> CVPResult:
        """Simulate CVP with delta applied — pure kernel delegation.

        No DB reads or writes (CR 11-3 honest-DEFER — read-only operation
        skips audit_logs). Verified by integration test
        `test_m7_simulation_no_db_writes.py` (audit_logs row 0건).
        """
        return simulate_cvp(baseline=baseline, delta=delta)

    async def compute(
        self,
        *,
        period_key: str,
        delta: CVPDelta,
    ) -> tuple[CVPBaseline, CVPResult, str]:
        """End-to-end: fetch baseline + simulate.

        Returns:
            (CVPBaseline, CVPResult, source_period_key) tuple.
        """
        baseline, source_period_key, _state = await self.fetch_cvp_baseline(
            period_key=period_key
        )
        result = await self.simulate_cvp(baseline=baseline, delta=delta)
        return baseline, result, source_period_key


__all__ = ["CVPSimulationService"]
