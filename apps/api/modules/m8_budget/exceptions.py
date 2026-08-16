"""apps.api.modules.m8_budget.exceptions — Story 8.1 + 8.2 typed exceptions.

5 NEW typed exceptions (CR 12-5 D-14 envelope main.py handler 등록):
  - 8.1:
    - ScenarioLimitExceededError → HTTP 409 SCENARIO_LIMIT_EXCEEDED
    - InvalidVirtualBudgetPeriodKeyError → HTTP 422 INVALID_VIRTUAL_BUDGET_PERIOD_KEY
    - BudgetScenarioNotFoundError → HTTP 404 BUDGET_SCENARIO_NOT_FOUND
  - 8.2 (Story 8.2 — Budget vs Actual Variance):
    - InvalidVariancePeriodError → HTTP 422 INVALID_VARIANCE_PERIOD
    - BudgetVarianceNotFoundError → HTTP 404 BUDGET_VARIANCE_NOT_FOUND

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
BUDGET_VARIANCE_NOT_FOUND_KO: str = "예산-실적 대조 데이터를 찾을 수 없습니다"
BUDGET_INVALID_VARIANCE_PERIOD_KO: str = "예산-실적 대조 기간 키가 올바르지 않습니다"


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


class BudgetVarianceNotFoundError(Exception):
    """PRD §F8.2 + AD-15 envelope — GET /budget/variance/{period_key} 대조 데이터 미존재.

    HTTP 404 BUDGET_VARIANCE_NOT_FOUND envelope (CR 12-5 D-14).
    Story 8.2 read-only — period_key에 해당하는 budget scenario가 없거나
    fiscal_period_snapshots verified row가 없는 경우 raise.
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
        self.message = (
            message or f"Budget variance not found: period_key={period_key}"
        )
        super().__init__(self.message)


class InvalidVariancePeriodError(ValueError):
    """PRD §F8.2 + AD-24 period key validation — invalid period_key for variance.

    HTTP 422 INVALID_VARIANCE_PERIOD envelope (CR 12-5 D-14).
    period_key는 `YYYY-MM#B<n>` virtual pattern (8-1 wire) + real_period_key
    `YYYY-MM` (Story 4-2) 모두 mismatch 시 raise.
    """

    def __init__(
        self,
        message: str,
        *,
        period_key: str,
        expected_pattern: str,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.period_key = period_key
        self.expected_pattern = expected_pattern


__all__ = [
    "ScenarioLimitExceededError",
    "InvalidVirtualBudgetPeriodKeyError",
    "BudgetScenarioNotFoundError",
    "BudgetVarianceNotFoundError",
    "InvalidVariancePeriodError",
    "BUDGET_SCENARIO_NOT_FOUND_KO",
    "BUDGET_SCENARIO_LIMIT_EXCEEDED_KO",
    "BUDGET_INVALID_VIRTUAL_KEY_KO",
    "BUDGET_VARIANCE_NOT_FOUND_KO",
    "BUDGET_INVALID_VARIANCE_PERIOD_KO",
]
