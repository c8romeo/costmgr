"""apps.api.modules.m8_budget.services.budget_scenario_service — Story 8.1.

Service-layer orchestration for budget scenario CRUD + scenario lock
enforcement (CR 12-5 L3 3-layer defense — service `validate_scenario_uniqueness`
+ DB UNIQUE constraint defense-in-depth).

Pure kernel lives at `packages.cost_engine.budget_period_key.py` (4 NEW
pure functions + 3 frozen dataclasses + 2 typed exceptions).

AD-22 ledger append-only: 8-1 is read-mostly with scenario creation only.
No `fiscal_period_snapshots` row touched. A5 forward-lock 변경 0 (CR 11-3
D-2 즉시 sweep 회피).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Final

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.db_models import BudgetScenario
from apps.api.modules.m8_budget.exceptions import BudgetScenarioNotFoundError
from packages.cost_engine.budget_period_key import (
    BudgetScenario as BudgetScenarioKernel,
)
from packages.cost_engine.budget_period_key import (
    compute_budget_scenario_hash,
    derive_budget_period_key,
    parse_virtual_budget_period_key,
    validate_scenario_uniqueness,
)

# V8 determinism + idempotency — 8-1은 read-mostly (no audit emit per CR 1.1
# invariant — 8-1은 A5 forward-lock 변경 0). audit_first=False 명시.
BUDGET_SCENARIO_INDUSTRY_AGNOSTIC: Final[bool] = True


def _to_budget_scenario(orm_row: BudgetScenario) -> BudgetScenarioKernel:
    """ORM → kernel boundary conversion (CR 12-1 L3 precedent).

    `BudgetScenario` ORM row (apps/api/core/db_models.py) →
    `packages.cost_engine.budget_period_key.BudgetScenario` (frozen dataclass).

    `created_at_kst` 결정론 — service layer가 ISO 8601 str로 변환 후
    hash input으로 사용 (NOT engine inject — kernel은 clock 없음).
    """
    return BudgetScenarioKernel(
        id=str(orm_row.id),
        tenant_id=str(orm_row.tenant_id),
        period_key=orm_row.period_key,
        real_period_key=orm_row.real_period_key,
        scenario_index=orm_row.scenario_index,
        created_by=str(orm_row.created_by),
        created_at_kst=orm_row.created_at_kst.isoformat(),
    )


class BudgetScenarioService:
    """Story 8.1 — AD-24 virtual period key + scenario lock orchestrator.

    Thin orchestration wrapper around `packages.cost_engine.budget_period_key`
    pure kernel. DB I/O lives here; pure logic lives in the kernel.
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

    async def count_scenarios(self) -> int:
        """SELECT COUNT(*) FROM budget_scenarios WHERE tenant_id = :tenant_id.

        RLS same-tenant filter (AD-3). Returns 0 or 1 (1차 MVP 한도).
        """
        stmt = (
            select(BudgetScenario)
            .where(BudgetScenario.tenant_id == self.tenant_id)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return len(rows)

    async def create_scenario(self, *, real_period_key: str) -> BudgetScenarioKernel:
        """Create a new budget scenario for the tenant.

        1. Delegate to `derive_budget_period_key(real_period_key, scenario_index=1)`
           (pure kernel, AD-5).
        2. Delegate to `validate_scenario_uniqueness(existing_count=count)`
           (scenario lock, 1차 MVP = 1개 only).
        3. DB INSERT INTO budget_scenarios (UUID v7 id + scenario_hash via
           `compute_budget_scenario_hash` + AD-9 Seoul created_at_kst).
        4. **DB UNIQUE 제약 활용** (`UNIQUE(tenant_id, real_period_key)`
           defense-in-depth — race condition 가드).

        Raises:
          ScenarioLimitExceededError — existing_count >= 1 (CR 12-5 D-14 envelope
            409 SCENARIO_LIMIT_EXCEEDED).
          ValueError — invalid real_period_key pattern (delegated from
            `derive_budget_period_key`).
          IntegrityError — DB UNIQUE constraint violation (race condition
            defense-in-depth — translate to ScenarioLimitExceededError).
        """
        # 1. Pure kernel derive (scenario_index=1 hard-coded — 1차 MVP 한도).
        period_key = derive_budget_period_key(
            real_period_key=real_period_key, scenario_index=1
        )

        # 2. Scenario lock — `existing_count >= 1` 시 ScenarioLimitExceededError.
        existing_count = await self.count_scenarios()
        validate_scenario_uniqueness(existing_count=existing_count)

        # 3. Create ORM row.
        scenario_id = uuid.uuid4()
        created_at_kst = datetime.now(UTC)
        orm_row = BudgetScenario(
            id=scenario_id,
            tenant_id=self.tenant_id,
            period_key=period_key,
            real_period_key=real_period_key,
            scenario_index=1,
            scenario_hash="placeholder",  # pre-compute then update (hash needs id)
            created_by=self.actor_id,
            created_at_kst=created_at_kst,
        )
        # Compute scenario_hash via kernel (after we know id + tenant + period_key).
        kernel = _to_budget_scenario(orm_row)
        scenario_hash = compute_budget_scenario_hash(scenario=kernel)
        orm_row.scenario_hash = scenario_hash

        self.session.add(orm_row)
        try:
            await self.session.flush()
        except IntegrityError as exc:
            # DB UNIQUE constraint race condition (concurrent INSERT) →
            # translate to ScenarioLimitExceededError (CR 12-5 D-14 envelope).
            from packages.cost_engine.budget_period_key import (
                ScenarioLimitExceededError,
            )

            await self.session.rollback()
            raise ScenarioLimitExceededError(
                existing_count=existing_count,
            ) from exc

        return kernel

    async def list_scenarios(self) -> list[BudgetScenarioKernel]:
        """List all budget scenarios for the tenant (ORDER BY created_at_kst DESC).

        RLS same-tenant filter (AD-3). 1차 MVP = 0 or 1 row.
        """
        stmt = (
            select(BudgetScenario)
            .where(BudgetScenario.tenant_id == self.tenant_id)
            .order_by(BudgetScenario.created_at_kst.desc())
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [_to_budget_scenario(r) for r in rows]

    async def get_scenario(self, *, period_key: str) -> BudgetScenarioKernel:
        """Get single budget scenario by virtual period_key.

        1. Delegate to `parse_virtual_budget_period_key(period_key)` (pure
           kernel — validates virtual pattern).
        2. SELECT * FROM budget_scenarios WHERE tenant_id = :tenant_id
           AND period_key = :period_key.
        3. Not found → `BudgetScenarioNotFoundError` (CR 12-5 D-14 envelope
           404 BUDGET_SCENARIO_NOT_FOUND).

        Raises:
          ValueError — invalid period_key pattern (delegated from
            `parse_virtual_budget_period_key`).
          BudgetScenarioNotFoundError — not found.
        """
        # 1. Pure kernel parse (validates virtual pattern, raises ValueError).
        parse_virtual_budget_period_key(period_key=period_key)

        # 2. DB read.
        stmt = (
            select(BudgetScenario)
            .where(
                BudgetScenario.tenant_id == self.tenant_id,
                BudgetScenario.period_key == period_key,
            )
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            raise BudgetScenarioNotFoundError(
                period_key=period_key,
                tenant_id=str(self.tenant_id),
            )

        # 3. ORM → kernel boundary conversion.
        return _to_budget_scenario(row)
