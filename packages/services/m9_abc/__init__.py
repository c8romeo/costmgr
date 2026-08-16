"""packages.services.m9_abc — Story 9.1 + 9.2 thin serializers layer.

Pure re-export of thin JSON-safe serializers (`Decimal-as-string`,
UUID-as-string) for `packages.cost_engine.abc_engine` frozen dataclasses.

AD-15 §11 cross-language parity with TS mirrors:
- `apps/web/lib/m9-abc-validation.ts` (9-1) — `validateCostPoolTS` + etc.
- `apps/web/lib/m9-abc-allocation.ts` (9-2) — `computeCcrTS` + etc.

CR 11-3 D-2 ALLOWED_SERVICE_SUBMODULES sweep — `m9_abc.abc_validation_serializers`
+ `m9_abc.abc_allocation_serializers` registered in
`tests/architecture/test_api_calls_only_ports.py` (T2 wire).
"""

from packages.services.m9_abc.abc_allocation_serializers import (
    serialize_allocation_state,
    serialize_ccr_state,
)
from packages.services.m9_abc.abc_validation_serializers import (
    serialize_validation_state,
)

__all__ = [
    "serialize_validation_state",
    "serialize_ccr_state",
    "serialize_allocation_state",
]
