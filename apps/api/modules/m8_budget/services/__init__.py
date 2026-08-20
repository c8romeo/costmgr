"""M8 Budget vs Actual services — Story 8.1 + 8.2 + 8.3 thin orchestration layer.

`apps/api/modules/m8_budget/services/budget_scenario_service.py` owns
the CRUD + scenario lock enforcement (CR 12-5 L3 3-layer defense:
route @require_role + service validate_scenario_uniqueness + DB UNIQUE
constraint).

`apps/api/modules/m8_budget/services/budget_variance_service.py` owns
the read-only variance fetch (PRD §F8.2) + ABCD 회색 배지 placeholder
(PRD §15 NON-GOAL #1) + 합계 calculation.

`apps/api/modules/m8_budget/services/budget_pre_standard_service.py`
owns the pre-standard cost compute + UPSERT (PRD §F8.3 + AD-22 + 4-2
wire reuse) + §9 #20 PDF export (8-2 honestly DEFER #5 해소).

Pure kernel lives at `packages/cost_engine/budget_period_key.py` (8.1)
+ `packages/cost_engine/budget_variance.py` (8.2) +
`packages/cost_engine/budget_pre_standard.py` (8.3).
"""

from apps.api.modules.m8_budget.services.budget_pre_standard_service import (
    BUDGET_PRE_STANDARD_INDUSTRY_AGNOSTIC,
    VIRTUAL_BUDGET_PERIOD_KEY_PATTERN_PRE_STANDARD,
    BudgetPreStandardService,
    PreStandardSnapshotState,
    validate_pre_standard_inputs,
)
from apps.api.modules.m8_budget.services.budget_scenario_service import (
    BudgetScenarioService,
)
from apps.api.modules.m8_budget.services.budget_variance_service import (
    BudgetVarianceService,
    VarianceAggregationRow,
    validate_variance_inputs,
)

__all__ = [
    # Story 8.1
    "BudgetScenarioService",
    # Story 8.2
    "BudgetVarianceService",
    "VarianceAggregationRow",
    "validate_variance_inputs",
    # Story 8.3 — Budget Pre-Standard Cost
    "BudgetPreStandardService",
    "PreStandardSnapshotState",
    "validate_pre_standard_inputs",
    "BUDGET_PRE_STANDARD_INDUSTRY_AGNOSTIC",
    "VIRTUAL_BUDGET_PERIOD_KEY_PATTERN_PRE_STANDARD",
]
