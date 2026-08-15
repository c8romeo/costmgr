"""packages.services.m7_simulation — Story 7.1 thin wrappers layer.

Pure re-export of `packages.cost_engine.cvp` (CR A19 math surface SSOT)
plus thin JSON-safe serializers (`Decimal-as-string`) + delta helpers
(clamp + validate).

AD-15 §1 cross-language parity with TS mirror
`apps/web/lib/m7-simulation-cvp.ts` (TS re-implementation of BEP math).
"""

from packages.services.m7_simulation.delta_helpers import (
    clamp_delta,
    validate_delta_bounds,
)
from packages.services.m7_simulation.serializers import (
    serialize_cvp_baseline,
    serialize_cvp_delta,
    serialize_cvp_result,
)

__all__ = [
    "serialize_cvp_baseline",
    "serialize_cvp_delta",
    "serialize_cvp_result",
    "clamp_delta",
    "validate_delta_bounds",
]
