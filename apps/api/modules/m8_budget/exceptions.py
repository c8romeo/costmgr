"""apps.api.modules.m8_budget.exceptions — Story 8.1 typed exceptions.

3 NEW typed exceptions (CR 12-5 D-14 envelope main.py handler 등록):
  - ScenarioLimitExceededError → HTTP 409 SCENARIO_LIMIT_EXCEEDED
  - InvalidVirtualBudgetPeriodKeyError → HTTP 422 INVALID_VIRTUAL_BUDGET_PERIOD_KEY
  - BudgetScenarioNotFoundError → HTTP 404 BUDGET_SCENARIO_NOT_FOUND

Pure re-export from `packages.cost_engine.budget_period_key` (kernel-owned)
+ service-layer extensions (AD-15 §4 envelope shape).
"""

from __future__ import annotations

from packages.cost_engine.budget_period_key import (
    InvalidVirtualBudgetPeriodKeyError,
    ScenarioLimitExceededError,
)

# Korean messages for HTTP envelopes (CR 12-5 D-14 typed contract).
# Module-level re-bindings to keep main.py handler imports flat.
BUDGET_SCENARIO_NOT_FOUND_KO: str = "예산 시나리오를 찾을 수 없습니다"
BUDGET_SCENARIO_LIMIT_EXCEEDED_KO: str = (
    "1차 MVP는 시나리오 1개만 지원합니다 (2차 예정)"
)
BUDGET_INVALID_VIRTUAL_KEY_KO: str = "가상 예산 기간 키가 올바르지 않습니다"


class BudgetScenarioNotFoundError(Exception):
    """PRD §F8.1 + AD-15 envelope — GET /budget/scenarios/{period_key} 시나리오 미존재.

    HTTP 404 BUDGET_SCENARIO_NOT_FOUND envelope (CR 12-5 D-14).
    """

    def __init__(
        self,
        *,
        period_key: str,
        tenant_id: str,
        message: str | None = None,
    ) -> None:
        self.period_key = period_key
        self.tenant_id = tenant_id
        self.message = message or f"Budget scenario not found: period_key={period_key}"
        super().__init__(self.message)


__all__ = [
    "ScenarioLimitExceededError",
    "InvalidVirtualBudgetPeriodKeyError",
    "BudgetScenarioNotFoundError",
    "BUDGET_SCENARIO_NOT_FOUND_KO",
    "BUDGET_SCENARIO_LIMIT_EXCEEDED_KO",
    "BUDGET_INVALID_VIRTUAL_KEY_KO",
]
