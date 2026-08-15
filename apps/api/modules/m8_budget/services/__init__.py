"""M8 Budget vs Actual services — Story 8.1 thin orchestration layer.

`apps/api/modules/m8_budget/services/budget_scenario_service.py` owns
the CRUD + scenario lock enforcement (CR 12-5 L3 3-layer defense:
route @require_role + service validate_scenario_uniqueness + DB UNIQUE
constraint). Pure kernel lives at `packages/cost_engine/budget_period_key.py`.
"""

from apps.api.modules.m8_budget.services.budget_scenario_service import (
    BudgetScenarioService,
)

__all__ = ["BudgetScenarioService"]
