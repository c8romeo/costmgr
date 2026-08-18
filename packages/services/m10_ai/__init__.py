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
    - F10.2-(a)~(d) verbatim bind: 파란 배지 '� 자동 분석' (auto_analysis) /
      보라 배지 '🤖 AI 참고(검증 필요)' (ai_reference) + SM-3a counter increment.

Story 10.4 EXTENSION (AI promotion port idempotency, cj-style Epic 10
5번째 진입점 = cj-style 33번째 epic 연속):
    - PROMOTE_STATUS_VALUES (6 values: success + idempotent_replay +
      draft_not_found + draft_superseded + idempotency_mismatch + m2_only_denied)
    - PromotionRequest frozen dataclass (tenant_id + period_key +
      source_draft_id + actor_id + actor_role)
    - PromotionResult frozen dataclass (promotion_id + idempotency_key +
      status + monthly_input_row_id + idempotent_replay + trace_id)
    - compute_promotion_idempotency_key pure function (UUID v5 derivation
      on 3-tuple, AD-17 verbatim "idempotent on (tenant_id, period_key,
      source_draft_id)")
    - validate_promotion_request pure function (period_key YYYY-MM +
      actor_role='m2_service_role' ONLY, AD-17 verbatim "only M2 may call")
    - InputPromoterPort Protocol (port contract for DB adapter)
    - D-10-3-DEFER-6 PIPA gate carry-over 해소 wire 진입 (T4 handler 진입
      시점에 4 endpoints 모두 `Depends(require_pipa_review)` 적용)

AD-1 / AD-11 layering: pure kernel layer. Service layer
(`apps/api/modules/m10_ai/`) imports from here.
"""

from packages.services.m10_ai.extraction_port import (
    ALLOWED_INPUT_TARGET_TABLES,
    MONTHLY_INPUT_FIELD_NAMES,
    SUPPORTED_FIELD_NAMES,
    DocumentExtractionJob,
    DocumentExtractionPort,
    ExtractionEvidence,
    ExtractionField,
    ExtractionRequest,
    FieldName,
    InputTargetTable,
    MonthlyFieldName,
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
from packages.services.m10_ai.promoter_port import (
    ALLOWED_PROMOTER_ACTOR_ROLE,
    PERIOD_KEY_PATTERN,
    PROMOTE_STATUS_VALUES,
    InputPromoterPort,
    PromotionRequest,
    PromotionResult,
    compute_promotion_idempotency_key,
    validate_promotion_request,
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
    # Story 10.4 EXTENSION (AI promotion port idempotency)
    "PROMOTE_STATUS_VALUES",
    "ALLOWED_PROMOTER_ACTOR_ROLE",
    "PERIOD_KEY_PATTERN",
    "PromotionRequest",
    "PromotionResult",
    "compute_promotion_idempotency_key",
    "validate_promotion_request",
    "InputPromoterPort",
)
