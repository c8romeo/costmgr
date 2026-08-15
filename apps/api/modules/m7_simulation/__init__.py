"""M7 CVP/BEP Simulation module — Epic 7 stories 7.1~7.2 populate this.

Story 7.1 wire (2026-08-15):
- 2 routes under /api/v1/simulation/cvp/* (compute + baseline)
- 4 INDUSTRY-AGNOSTIC capability gate (`CVP_SIMULATION`)
- 4 typed exceptions (CVPInvalidInputError + CVPBaselineNotFoundError +
  CVPInvalidDeltaError + CVPInvalidInputError kernel)
- 4-delegate service: fetch_cvp_baseline + simulate_cvp + compute + SERIALIZE
"""

from apps.api.modules.m7_simulation.handlers import router

__all__ = ["router"]
