"""apps.api.modules.m8_budget.exceptions — Story 8.1 + 8.2 + 8.3 typed exceptions.

9 NEW typed exceptions (CR 12-5 D-14 envelope main.py handler 등록):
  - 8.1:
    - ScenarioLimitExceededError → HTTP 409 SCENARIO_LIMIT_EXCEEDED
    - InvalidVirtualBudgetPeriodKeyError → HTTP 422 INVALID_VIRTUAL_BUDGET_PERIOD_KEY
    - BudgetScenarioNotFoundError → HTTP 404 BUDGET_SCENARIO_NOT_FOUND
  - 8.2 (Story 8.2 — Budget vs Actual Variance):
    - InvalidVariancePeriodError → HTTP 422 INVALID_VARIANCE_PERIOD
    - BudgetVarianceNotFoundError → HTTP 404 BUDGET_VARIANCE_NOT_FOUND
  - 8.3 (Story 8.3 — Budget Pre-Standard Cost Preview):
    - InvalidPreStandardInputError → HTTP 422 INVALID_PRE_STANDARD_INPUT
    - PreStandardSnapshotNotFoundError → HTTP 404 PRE_STANDARD_SNAPSHOT_NOT_FOUND
    - PreStandardAlreadyExistsError → HTTP 409 PRE_STANDARD_ALREADY_EXISTS
    - BudgetVariancePdfNotReadyError → HTTP 425 BUDGET_VARIANCE_PDF_NOT_READY

Pure re-export from `packages.cost_engine.budget_period_key` (kernel-owned)
+ `packages.cost_engine.budget_pre_standard` (kernel-owned, 8-3) +
service-layer extensions (AD-15 §4 envelope shape).
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
# Story 8.3 — Budget Pre-Standard Cost Preview envelopes.
BUDGET_INVALID_PRE_STANDARD_INPUT_KO: str = "예산 사전 표준원가 입력이 올바르지 않습니다"
BUDGET_PRE_STANDARD_SNAPSHOT_NOT_FOUND_KO: str = (
    "예산 사전 표준원가 스냅샷을 찾을 수 없습니다"
)
BUDGET_PRE_STANDARD_ALREADY_EXISTS_KO: str = (
    "동일 기간에 다른 예산 사전 표준원가 결과가 있습니다"
)
BUDGET_VARIANCE_PDF_NOT_READY_KO: str = (
    "예산-실적 차이 명세서 PDF는 예측 실행 후 다운로드할 수 있습니다"
)


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


class InvalidPreStandardInputError(Exception):
    """PRD §F8.3 + AD-15 envelope — POST /budget/pre-standard 입력 검증 실패.

    HTTP 422 INVALID_PRE_STANDARD_INPUT envelope (CR 12-5 D-14).
    pre-standard cost 계산 시 invalid input (음수, overhead_rate > 100,
    invalid period_key, scenario_index != 1) raise.

    `field` identifies which input field is invalid (machine code),
    `reason` is a human-readable Korean reason (e.g., 'negative_value',
    'over_rate_exceeded', 'invalid_period_key').
    """

    def __init__(
        self,
        message: str,
        *,
        field: str,
        reason: str,
    ) -> None:
        self.message = message
        self.field = field
        self.reason = reason
        super().__init__(message)


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


# ── Story 8.3 — Budget Pre-Standard Cost Preview typed exceptions ──


class PreStandardSnapshotNotFoundError(Exception):
    """PRD §F8.3 + AD-15 envelope — GET /budget/pre-standard 미존재.

    HTTP 404 PRE_STANDARD_SNAPSHOT_NOT_FOUND envelope (CR 12-5 D-14).
    period_key에 해당하는 fiscal_period_snapshots.engine_type='budget' row가
    없는 경우 raise.
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
            message
            or f"Pre-standard snapshot not found: period_key={period_key}"
        )
        super().__init__(self.message)


class PreStandardAlreadyExistsError(Exception):
    """PRD §F8.3 + AD-22 ledger append-only — same (tenant, period, baseline, engine)
    row exists with DIFFERENT result_hash.

    HTTP 409 PRE_STANDARD_ALREADY_EXISTS envelope (CR 12-5 D-14).
    4-2 wire idempotency: same hash → skip, different hash → raise.
    """

    def __init__(
        self,
        *,
        period_key: str,
        tenant_id: str,
        existing_hash: str,
        new_hash: str,
        message: str | None = None,
    ) -> None:
        self.period_key = period_key
        self.tenant_id = tenant_id
        self.existing_hash = existing_hash
        self.new_hash = new_hash
        self.message = (
            message
            or (
                f"Pre-standard snapshot already exists with different hash: "
                f"period_key={period_key}"
            )
        )
        super().__init__(self.message)


class BudgetVariancePdfNotReadyError(Exception):
    """PRD §F8.3 + §9 #20 — pre-standard snapshot 미저장 시 PDF 425.

    HTTP 425 BUDGET_VARIANCE_PDF_NOT_READY envelope (CR 12-5 D-14).
    `/variance/{period_key}/pdf` endpoint 호출 시점에 pre-standard snapshot이
    INSERT되어 있지 않으면 raise (race condition 방지, 8-2 PDF placeholder와
    동일 패턴).
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
            message
            or (
                f"Pre-standard snapshot not yet inserted: "
                f"period_key={period_key}"
            )
        )
        super().__init__(self.message)


__all__ = [
    "ScenarioLimitExceededError",
    "InvalidVirtualBudgetPeriodKeyError",
    "BudgetScenarioNotFoundError",
    "BudgetVarianceNotFoundError",
    "InvalidVariancePeriodError",
    # Story 8.3 — Budget Pre-Standard Cost Preview
    "InvalidPreStandardInputError",
    "PreStandardSnapshotNotFoundError",
    "PreStandardAlreadyExistsError",
    "BudgetVariancePdfNotReadyError",
    # Korean messages (CR 12-5 D-14)
    "BUDGET_SCENARIO_NOT_FOUND_KO",
    "BUDGET_SCENARIO_LIMIT_EXCEEDED_KO",
    "BUDGET_INVALID_VIRTUAL_KEY_KO",
    "BUDGET_VARIANCE_NOT_FOUND_KO",
    "BUDGET_INVALID_VARIANCE_PERIOD_KO",
    "BUDGET_INVALID_PRE_STANDARD_INPUT_KO",
    "BUDGET_PRE_STANDARD_SNAPSHOT_NOT_FOUND_KO",
    "BUDGET_PRE_STANDARD_ALREADY_EXISTS_KO",
    "BUDGET_VARIANCE_PDF_NOT_READY_KO",
]
