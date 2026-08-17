"""apps.api.modules.m3_calculate.services — M3 calculation service layer.

Story 4.2 (Task 2.1) — service exports.
Story 4.3 (Task 2.4) — VerificationRunner + Verdict re-export added.
Story 9.3 (T2.4) — CalcOutcomeABC re-export for handlers narrowing.

Re-exports `CalcOrchestrator` + `MonthlyInputAggregator` + `BaselineLoader`
+ `VerificationRunner` + the typed exception hierarchy so callers can
`from apps.api.modules.m3_calculate.services import CalcOrchestrator`.

Story 9.3 EXTENSION: discriminated union envelope members (`CalcOutcome`
+ `CalcOutcomeABC`) are re-exported so handlers can narrow via
`isinstance(outcome, CalcOutcomeABC)` for the ABC dual-route path
(AD-19 dual-route dispatch).
"""

from apps.api.modules.m3_calculate.services.baseline_loader import (
    BaselineLoader,
    BaselineNotReadyError,
)
from apps.api.modules.m3_calculate.services.calc_orchestrator import (
    CalcOrchestrator,
    CalcOutcome,
    CalcOutcomeABC,
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
    # Discriminated union envelope members (Story 9.3 — AD-19 dual-route)
    "CalcOutcome",  # engine_type='trad' (manufacturing-kind)
    "CalcOutcomeABC",  # engine_type='abc' (service-kind, M9 dispatch)
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
