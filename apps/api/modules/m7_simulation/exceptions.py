"""apps.api.modules.m7_simulation.exceptions — Story 7.1 typed exceptions.

2 NEW typed exceptions (CR 12-5 D-14 envelope main.py handler 등록):
  - CVPBaselineNotFoundError   → HTTP 404 CVP_BASELINE_NOT_FOUND
  - CVPInvalidDeltaError       → HTTP 422 CVP_INVALID_DELTA (re-export from
    `packages.services.m7_simulation.delta_helpers`)

Pure re-export from `packages.cost_engine.cvp` (kernel-owned) +
service-layer extensions (AD-15 §4 envelope shape).
"""

from __future__ import annotations

from packages.cost_engine.cvp import CVPInvalidInputError
from packages.services.m7_simulation.delta_helpers import CVPInvalidDeltaError

# Korean messages for HTTP envelopes (CR 12-5 D-14 typed contract).
# Module-level re-bindings to keep main.py handler imports flat.
CVP_BASELINE_NOT_FOUND_KO: str = "계산된 마감 스냅샷이 없어 CVP 베이스라인을 만들 수 없습니다"
CVP_INVALID_DELTA_KO: str = "CVP 변동률이 허용 범위를 벗어났습니다"


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


__all__ = [
    "CVPInvalidInputError",
    "CVPInvalidDeltaError",
    "CVPBaselineNotFoundError",
    "CVP_BASELINE_NOT_FOUND_KO",
    "CVP_INVALID_DELTA_KO",
]
