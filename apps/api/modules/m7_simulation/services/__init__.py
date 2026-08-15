"""M7 CVP/BEP Simulation services — Story 7.1 thin orchestration layer.

`apps/api/modules/m7_simulation/services/cvp_simulation_service.py` owns
the baseline extraction (RLS same-tenant `fiscal_period_snapshots` +
`products` JOIN) + CVP simulation dispatch (delegates to pure kernel
`packages.cost_engine.cvp`).

Read-only operation (CR 11-3 honest-DEFER + CR 1.1 AD-2 audit skip):
- no `audit_logs` rows written (verified by `tests/integration/test_m7_simulation_no_db_writes.py`)
- no `monthly_input_periods` / `fiscal_period_snapshots` UPDATE
- baseline fetch is `SELECT` only (AD-3 same-tenant RLS)
"""

from apps.api.modules.m7_simulation.services.cvp_simulation_service import (
    CVPSimulationService,
)

__all__ = ["CVPSimulationService"]
