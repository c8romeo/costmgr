"""apps.api.modules.m9_abc.exceptions — Story 9.1 typed exceptions.

4 NEW typed exceptions (CR 12-5 D-14 envelope main.py handler 등록):
  - CostPoolValidationError       (422 COST_POOL_INVALID_SUM)
  - ActivityValidationError       (422 ACTIVITY_INVALID_SUM)
  - DriverValidationError         (422 DRIVER_INVALID_SUM)
  - AbcValidationNotFoundError    (404 ABC_VALIDATION_NOT_FOUND)

Pure re-export from `packages.cost_engine.abc_engine` (kernel-owned)
+ service-layer extensions (AD-15 §4 envelope shape).
"""

from __future__ import annotations

from packages.cost_engine.abc_engine import (
    AbcValidationNotFoundError,
    ActivityValidationError,
    CostPoolValidationError,
    DriverValidationError,
)

# Korean messages for HTTP envelopes (CR 12-5 D-14 typed contract).
# Module-level re-bindings to keep main.py handler imports flat.
ABC_COST_POOL_INVALID_SUM_KO: str = "원가풀 행 합이 100%가 아닙니다"
ABC_ACTIVITY_INVALID_SUM_KO: str = "활동 열 합이 100%가 아닙니다"
ABC_DRIVER_INVALID_SUM_KO: str = "동인 합이 100%가 아닙니다"
ABC_VALIDATION_NOT_FOUND_KO: str = "ABC 검증 대상을 찾을 수 없습니다"


__all__ = [
    # Story 9.1 — Cost Pool + Activity + Driver 100% Validation
    "CostPoolValidationError",
    "ActivityValidationError",
    "DriverValidationError",
    "AbcValidationNotFoundError",
    # Korean messages (CR 12-5 D-14)
    "ABC_COST_POOL_INVALID_SUM_KO",
    "ABC_ACTIVITY_INVALID_SUM_KO",
    "ABC_DRIVER_INVALID_SUM_KO",
    "ABC_VALIDATION_NOT_FOUND_KO",
]
