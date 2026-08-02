"""M3 Cost Calculation module — Epic 4 stories 4.1~4.4.

Story 4.2 — Single Calculation Endpoint (`POST /api/v1/calc`).
AD-19: One calculation entry point and owner. The single endpoint
dispatches this port for traditional costing; (Epic 9) M9 ABC routing
is a separate endpoint.

Module layout (Story 4.2):
- `apps/api/modules/m3_calculate/handlers.py` — FastAPI router (`POST /api/v1/calc`)
- `apps/api/modules/m3_calculate/schemas.py` — Pydantic v2 CalcRequest/CalcResponse
- `apps/api/modules/m3_calculate/services/calc_orchestrator.py` — REPEATABLE READ transaction + 9-step flow
- `apps/api/modules/m3_calculate/services/monthly_input_aggregator.py` — 6-stream aggregation
- `apps/api/modules/m3_calculate/services/baseline_loader.py` — baseline.standard_monthly_hours + BOM + allocation

Engine (`packages.cost_engine.core.period_cost`) is pure — service layer
imports it. AD-1: handler → service → engine, no reverse direction.
"""

from apps.api.modules.m3_calculate.handlers import router
from apps.api.modules.m3_calculate.services import (
    BaselineNotReadyError,
    CalcOrchestrator,
    CalcServiceError,
    FiscalPeriodSnapshotDivergedError,
    MonthlyInputAggregator,
    MonthlyInputBlockedError,
)

__all__ = [
    "router",
    "CalcOrchestrator",
    "MonthlyInputAggregator",
    "BaselineNotReadyError",
    "CalcServiceError",
    "FiscalPeriodSnapshotDivergedError",
    "MonthlyInputBlockedError",
]
