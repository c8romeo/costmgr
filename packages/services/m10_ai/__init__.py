"""packages.services.m10_ai — Story 1.3 + Story 10.1 + Story 10.2 (Epic 10 EXTENSION).

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

Story 10.2 EXTENSION (three-insight cache policy):
    - INSIGHT_KIND_VALUES (3 values: cost_reduction_candidate + anomaly_pattern + forecast)
    - SOURCE_KIND_VALUES (2 values: auto_analysis + ai_reference; 10-3 forward-bind)
    - InsightKind + SourceKind enums (AD-15 cross-language parity SSOT)
    - InsightEntry frozen dataclass
    - InsightCacheKey frozen dataclass (AD-25 verbatim 3-tuple)
    - compose_insight_cache_key pure function (canonical string serialization)
    - make_default_insights pure function (3 default rule-based insights)
    - InsightCacheKeyShapeError typed exception

Story 10.3 EXTENSION note (AI reference vs auto analysis badge separation):
    - `SourceKind` / `SOURCE_KIND_VALUES` re-export **그대로 보존** (SSOT 변경 0건).
    - `ai_reference` opinion surface 는 service layer 로 진입
      (`apps/api/modules/m10_ai/service.py::CommentService` + `ai_insight_comments`).
    - F10.2-(a)~(d) verbatim bind: 파란 배지 '📊 자동 분석' (auto_analysis) /
      보라 배지 '🤖 AI 참고(검증 필요)' (ai_reference) + SM-3a counter increment.

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
from packages.services.m10_ai.insight_cache_kernel import (
    INSIGHT_KIND_VALUES,
    SOURCE_KIND_VALUES,
    InsightCacheKey,
    InsightCacheKeyShapeError,
    InsightEntry,
    InsightKind,
    SourceKind,
    compose_insight_cache_key,
    make_default_insights,
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
    # Story 10.2 EXTENSION (three-insight cache policy)
    "INSIGHT_KIND_VALUES",
    "SOURCE_KIND_VALUES",
    "InsightKind",
    "SourceKind",
    "InsightEntry",
    "InsightCacheKey",
    "compose_insight_cache_key",
    "make_default_insights",
    "InsightCacheKeyShapeError",
)
