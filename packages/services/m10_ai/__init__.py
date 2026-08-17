"""packages.services.m10_ai — Story 1.3 + Story 10.1 (Epic 10 EXTENSION).

Story 1.3 baseline (onboarding extraction):
    - SUPPORTED_FIELD_NAMES (5 onboarding fields)
    - FieldName enum
    - DocumentExtractionPort Protocol
    - ExtractionEvidence / ExtractionField / DocumentExtractionJob / ExtractionRequest

Story 10.1 EXTENSION (monthly input extraction):
    - MONTHLY_INPUT_FIELD_NAMES (6 monthly input fields)
    - MonthlyFieldName enum
    - InputTargetTable discriminated union ('onboarding_inputs' | 'monthly_inputs')
    - MonthlyInputDraftRow dataclass (target_table='monthly_inputs')
    - normalize_monthly_field_value / compute_extraction_confidence pure functions
    - InvalidMonthlyFieldValueError typed exception

AD-1 / AD-11 layering: pure kernel layer. Service layer
(`apps/api/modules/m10_ai/`) imports from here.
"""

from packages.services.m10_ai.extraction_port import (
    ALLOWED_INPUT_TARGET_TABLES,
    DocumentExtractionJob,
    DocumentExtractionPort,
    ExtractionEvidence,
    ExtractionField,
    ExtractionRequest,
    FieldName,
    InputTargetTable,
    MONTHLY_INPUT_FIELD_NAMES,
    MonthlyFieldName,
    SUPPORTED_FIELD_NAMES,
)
from packages.services.m10_ai.monthly_extraction_kernel import (
    CONFIDENCE_RED_THRESHOLD,
    CONFIDENCE_YELLOW_THRESHOLD,
    InvalidMonthlyFieldValueError,
    MonthlyInputDraftRow,
    compute_extraction_confidence,
    normalize_monthly_field_value,
)

__all__ = (
    # Story 1.3 baseline (onboarding extraction)
    "SUPPORTED_FIELD_NAMES",
    "FieldName",
    "ExtractionEvidence",
    "ExtractionField",
    "DocumentExtractionJob",
    "ExtractionRequest",
    "DocumentExtractionPort",
    # Story 10.1 EXTENSION (monthly input extraction)
    "ALLOWED_INPUT_TARGET_TABLES",
    "MONTHLY_INPUT_FIELD_NAMES",
    "MonthlyFieldName",
    "InputTargetTable",
    "CONFIDENCE_RED_THRESHOLD",
    "CONFIDENCE_YELLOW_THRESHOLD",
    "MonthlyInputDraftRow",
    "InvalidMonthlyFieldValueError",
    "normalize_monthly_field_value",
    "compute_extraction_confidence",
)