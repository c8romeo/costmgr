"""packages.services.m7_simulation — Story 7.1 + 7.2 thin wrappers layer.

Pure re-export of `packages.cost_engine.cvp` + `packages.cost_engine.projection`
(CR A19 math surface SSOT) plus thin JSON-safe serializers
(`Decimal-as-string`) + delta helpers (clamp + validate) + projection
PDF envelope helpers (READ-ONLY).

AD-15 §1 cross-language parity with TS mirror
`apps/web/lib/m7-simulation-cvp.ts` + `apps/web/lib/m7-simulation-projection.ts`.
"""

from packages.services.m7_simulation.delta_helpers import (
    clamp_delta,
    validate_delta_bounds,
)
from packages.services.m7_simulation.projection_pdf_helpers import (
    PROJECTION_PDF_REPORT_CODE,
    PROJECTION_PDF_TITLE_KO,
    serialize_projection_pdf_envelope,
)
from packages.services.m7_simulation.projection_serializers import (
    serialize_projection_inputs,
    serialize_projection_result,
)
from packages.services.m7_simulation.serializers import (
    serialize_cvp_baseline,
    serialize_cvp_delta,
    serialize_cvp_result,
)

__all__ = [
    # 7.1 CVP serializers
    "serialize_cvp_baseline",
    "serialize_cvp_delta",
    "serialize_cvp_result",
    "clamp_delta",
    "validate_delta_bounds",
    # 7.2 projection serializers
    "serialize_projection_inputs",
    "serialize_projection_result",
    # 7.2 projection PDF envelope helpers
    "serialize_projection_pdf_envelope",
    "PROJECTION_PDF_REPORT_CODE",
    "PROJECTION_PDF_TITLE_KO",
]
