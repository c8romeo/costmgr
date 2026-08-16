"""M8 Budget vs Actual services — Story 8.1 + 8.2 thin orchestration layer.

`apps/api/modules/m8_budget/services/budget_scenario_service.py` owns
the CRUD + scenario lock enforcement (CR 12-5 L3 3-layer defense:
route @require_role + service validate_scenario_uniqueness + DB UNIQUE
constraint).

`apps/api/modules/m8_budget/services/budget_variance_service.py` owns
the read-only variance fetch (PRD §F8.2) + ABCD 회색 배지 placeholder
(PRD §15 NON-GOAL #1) + 합계 calculation.

Pure kernel lives at `packages/cost_engine/budget_period_key.py` (8.1)
+ `packages/cost_engine/budget_variance.py` (8.2).
"""

from apps.api.modules.m8_budget.services.budget_scenario_service import (
    BudgetScenarioService,
)
from apps.api.modules.m8_budget.services.budget_variance_service import (
    BudgetVarianceService,
    VarianceAggregationRow,
    validate_variance_inputs,
)

__all__ = [
    "BudgetScenarioService",
    "BudgetVarianceService",
    "VarianceAggregationRow",
    "validate_variance_inputs",
]
