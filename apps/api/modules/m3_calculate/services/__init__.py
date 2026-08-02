"""apps.api.modules.m3_calculate.services — M3 calculation service layer.

Story 4.2 (Task 2.1) — service exports.
Story 4.3 (Task 2.4) — VerificationRunner + Verdict re-export added.

Re-exports `CalcOrchestrator` + `MonthlyInputAggregator` + `BaselineLoader`
+ `VerificationRunner` + the typed exception hierarchy so callers can
`from apps.api.modules.m3_calculate.services import CalcOrchestrator`.
"""

from apps.api.modules.m3_calculate.services.baseline_loader import (
    BaselineLoader,
    BaselineNotReadyError,
)
from apps.api.modules.m3_calculate.services.calc_orchestrator import (
    CalcOrchestrator,
    CalcServiceError,
    FiscalPeriodSnapshotDivergedError,
    MonthlyInputBlockedError,
)
from apps.api.modules.m3_calculate.services.monthly_input_aggregator import (
    MonthlyInputAggregator,
)
from apps.api.modules.m3_calculate.services.verification_runner import (
    Verdict,
    VerificationRunner,
)

__all__ = [
    # Service entry point
    "CalcOrchestrator",
    # Service helpers
    "MonthlyInputAggregator",
    "BaselineLoader",
    "VerificationRunner",  # Story 4.3 — AD-12 verifier
    "Verdict",  # Story 4.3 — AD-20 envelope
    # Typed exceptions
    "MonthlyInputBlockedError",  # 409 MONTHLY_INPUT_BLOCKED
    "FiscalPeriodSnapshotDivergedError",  # 409 FISCAL_PERIOD_SNAPSHOT_DIVERGED
    "BaselineNotReadyError",  # 422 BASELINE_NOT_READY
    "CalcServiceError",  # 500 INTERNAL_ERROR
]
