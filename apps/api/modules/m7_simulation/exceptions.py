"""apps.api.modules.m7_simulation.exceptions — Story 7.1 + 7.2 typed exceptions.

5 typed exceptions (CR 12-5 D-14 envelope main.py handler 등록):
  - CVPBaselineNotFoundError        → HTTP 404 CVP_BASELINE_NOT_FOUND
  - CVPInvalidDeltaError            → HTTP 422 CVP_INVALID_DELTA (re-export
    from `packages.services.m7_simulation.delta_helpers`)
  - InvalidProjectionMonthError     → HTTP 422 INVALID_PROJECTION_MONTH
  - ProjectionInputsInvalidError    → HTTP 422 PROJECTION_INPUTS_INVALID
  - ProjectionBaselineNotFoundError → HTTP 404 PROJECTION_BASELINE_NOT_FOUND

Pure re-export from `packages.cost_engine.cvp` + `packages.cost_engine.projection`
(kernel-owned) + service-layer extensions (AD-15 §4 envelope shape).
"""

from __future__ import annotations

from packages.cost_engine.projection import (
    InvalidProjectionMonthError,
    ProjectionBaselineNotFoundError,
    ProjectionInvalidInputError,
)
from packages.services.m7_simulation.delta_helpers import CVPInvalidDeltaError

# Korean messages for HTTP envelopes (CR 12-5 D-14 typed contract).
# Module-level re-bindings to keep main.py handler imports flat.
CVP_BASELINE_NOT_FOUND_KO: str = (
    "계산된 마감 스냅샷이 없어 CVP 베이스라인을 만들 수 없습니다"
)
CVP_INVALID_DELTA_KO: str = "CVP 변동률이 허용 범위를 벗어났습니다"
INVALID_PROJECTION_MONTH_KO: str = (
    "차월 추정 기간은 YYYY-MM 형식이며 기준 기간보다 이후여야 합니다"
)
PROJECTION_INPUTS_INVALID_KO: str = (
    "차월 추정 입력값(차입금·이자율·원가 상승률·법인세율)이 유효하지 않습니다"
)
PROJECTION_BASELINE_NOT_FOUND_KO: str = (
    "차월 추정 베이스라인이 없습니다. 직전 월 마감을 먼저 실행하세요"
)


class CVPBaselineNotFoundError(Exception):
    """PRD §F7.1 + AD-15 envelope — GET /simulation/cvp/baseline baseline 미존재.

    HTTP 404 CVP_BASELINE_NOT_FOUND envelope (CR 12-5 D-14).
    """

    def __init__(
        self,
        *,
        tenant_id: str,
        period_key: str,
        message: str | None = None,
    ) -> None:
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.message = (
            message
            or f"CVP baseline not found: tenant_id={tenant_id}, period_key={period_key}"
        )
        super().__init__(self.message)


class ProjectionInputsInvalidError(Exception):
    """422 PROJECTION_INPUTS_INVALID — 4종 파라미터 (차입금·이자율·상승률·세율) 범위/형식 위반.

    Service-layer validator wraps `ProjectionInvalidInputError` from the
    pure kernel for HTTP envelope (CR 12-5 D-14).
    """

    def __init__(
        self,
        *,
        tenant_id: str,
        period_key: str,
        field: str | None = None,
        reason: str,
        message: str | None = None,
    ) -> None:
        self.tenant_id = tenant_id
        self.period_key = period_key
        self.field = field
        self.reason = reason
        self.message = (
            message
            or f"Projection inputs invalid: tenant_id={tenant_id}, "
            f"period_key={period_key}, field={field}, reason={reason}"
        )
        super().__init__(self.message)


__all__ = [
    # 7.1 CVP
    "CVPInvalidDeltaError",
    "CVPBaselineNotFoundError",
    "CVP_BASELINE_NOT_FOUND_KO",
    "CVP_INVALID_DELTA_KO",
    # 7.2 projection
    "InvalidProjectionMonthError",
    "ProjectionInvalidInputError",
    "ProjectionBaselineNotFoundError",
    "ProjectionInputsInvalidError",
    "INVALID_PROJECTION_MONTH_KO",
    "PROJECTION_INPUTS_INVALID_KO",
    "PROJECTION_BASELINE_NOT_FOUND_KO",
]
