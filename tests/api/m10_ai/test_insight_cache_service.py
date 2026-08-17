"""tests.api.m10_ai.test_insight_cache_service — Story 10.2 service-layer tests.

Story 10.2 (cj-style Epic 10 cj-style 29번째 epic 연속) —
T4.3 tests for `apps.api.modules.m10_ai.service::InsightCacheService`.

Test breakdown (~18 cases, no DB):
- import sanity × 4 (InsightCacheService + 4 typed exceptions)
- signature contract × 4 (get_or_compute_insights + InsightListResult fields)
- AD-25 verbatim 3-tuple cache key × 3 (compose_insight_cache_key format)
- F10.1-(d) channel filter × 2 (cross-channel contamination 방지)
- audit-first INSERT × 2 (CR 1.1 verbatim)
- AIInsightCacheAction Literal × 2
- AD-7 strict invariant × 1 (source_kind='auto_analysis' ONLY)

P-015 SSOT pattern: capability matrix drift detector runs in
`tests/integration/test_capability_matrix_v1_21_drift.py` (T6.1, 15 cases PASS).
"""

from __future__ import annotations

import inspect
import uuid

import pytest

from apps.api.core.audit_action import ActionClass, AIInsightCacheAction
from apps.api.core.db_models import AiInsightCache
from apps.api.modules.m10_ai.service import (
    AiInsightCacheContaminationError,
    AiPipaConsentMissingError,
    InsightCacheKeyError,
    InsightCacheService,
    InsightColdComputeTimeoutError,
    InsightListResult,
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


# ── 1. Import sanity (4 cases) ────────────────────────────────────


def test_insight_cache_service_importable() -> None:
    """InsightCacheService class exists and is importable."""
    assert InsightCacheService is not None
    assert inspect.isclass(InsightCacheService)


def test_4_typed_exceptions_importable() -> None:
    """4 NEW typed exceptions all importable."""
    assert InsightCacheKeyError is not None
    assert InsightColdComputeTimeoutError is not None
    assert AiInsightCacheContaminationError is not None
    assert AiPipaConsentMissingError is not None


def test_insight_list_result_dataclass_fields() -> None:
    """InsightListResult carries the 6 expected fields."""
    fields = {f.name for f in InsightListResult.__dataclass_fields__.values()}
    expected = {"insights", "period_key", "calculation_result_hash", "hit_count", "miss_count", "trace_id"}
    assert expected.issubset(fields)


def test_ai_insight_cache_action_literal_present() -> None:
    """AIInsightCacheAction Literal includes 4 expected values."""
    args = AIInsightCacheAction.__args__
    assert "ai_insight_cache_hit" in args
    assert "ai_insight_cache_miss" in args
    assert "ai_insight_cache_cold_compute" in args
    assert "ai_insight_cache_invalidation" in args


# ── 2. Signature contract (4 cases) ────────────────────────────────


def test_insight_cache_service_constructor_signature() -> None:
    """__init__(session, *, trace_id) — session + trace_id required."""
    sig = inspect.signature(InsightCacheService.__init__)
    params = sig.parameters
    assert "self" in params
    assert "session" in params
    assert "trace_id" in params


def test_get_or_compute_insights_signature() -> None:
    """get_or_compute_insights(self, *, tenant_id, period_key, calculation_result_hash)."""
    sig = inspect.signature(InsightCacheService.get_or_compute_insights)
    params = sig.parameters
    assert "tenant_id" in params
    assert "period_key" in params
    assert "calculation_result_hash" in params


def test_get_or_compute_insights_is_coroutine() -> None:
    """get_or_compute_insights is an async coroutine function."""
    assert inspect.iscoroutinefunction(InsightCacheService.get_or_compute_insights)


def test_ai_insight_cache_contamination_error_attributes() -> None:
    """AiInsightCacheContaminationError carries observed/expected channel + trace_id."""
    err = AiInsightCacheContaminationError(
        observed_channel="cost_engine_cache",
        expected_channel="ai_cache",
        trace_id="trace-1",
    )
    assert err.observed_channel == "cost_engine_cache"
    assert err.expected_channel == "ai_cache"
    assert err.trace_id == "trace-1"


# ── 3. AD-25 verbatim 3-tuple cache key (3 cases) ────────────────


def test_ad25_cache_key_3_tuple_components() -> None:
    """AD-25 verbatim: (tenant_id, period_key, calculation_result_hash)."""
    tenant_id = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    key = InsightCacheKey(
        tenant_id=tenant_id,
        period_key="2026-07",
        calculation_result_hash="abc123",
    )
    assert isinstance(key.tenant_id, uuid.UUID)
    assert isinstance(key.period_key, str)
    assert isinstance(key.calculation_result_hash, str)


def test_compose_insight_cache_key_canonical_form() -> None:
    """compose_insight_cache_key produces 'tenant|period|hash' canonical form."""
    tenant_id = uuid.UUID("11111111-2222-3333-4444-555555555555")
    key = compose_insight_cache_key(
        tenant_id=tenant_id,
        period_key="2026-07",
        calculation_result_hash="deadbeef",
    )
    assert key == "11111111-2222-3333-4444-555555555555|2026-07|deadbeef"


def test_compose_insight_cache_key_invalid_period_key() -> None:
    """compose_insight_cache_key raises InsightCacheKeyShapeError on empty period_key."""
    with pytest.raises(InsightCacheKeyShapeError):
        compose_insight_cache_key(
            tenant_id=uuid.uuid4(),
            period_key="",
            calculation_result_hash="abc",
        )


# ── 4. F10.1-(d) channel filter (2 cases) ─────────────────────────


def test_ai_insight_cache_channel_filter_constant() -> None:
    """F10.1-(d) verbatim: 'ai_cache' channel filter 강제 (in service source)."""
    import apps.api.modules.m10_ai.service as svc

    source = inspect.getsource(svc)
    assert "'ai_cache'" in source  # channel filter string literal present


def test_cross_channel_contamination_typed_exception() -> None:
    """AiInsightCacheContaminationError surfaces cross-channel leakage detection."""
    err = AiInsightCacheContaminationError(
        observed_channel="fiscal_period_cache",
        expected_channel="ai_cache",
        trace_id="trace-2",
    )
    assert err.observed_channel != err.expected_channel
    assert "fiscal_period_cache" in str(err)


# ── 5. Audit-first INSERT (CR 1.1 verbatim) (2 cases) ─────────────


def test_audit_first_emits_hit_action_before_select() -> None:
    """Service emits 'ai_insight_cache_hit' (optimistic) audit row before cache SELECT."""
    import apps.api.modules.m10_ai.service as svc

    source = inspect.getsource(svc.InsightCacheService.get_or_compute_insights)
    # audit-first emit must appear before any SELECT statement
    audit_first_idx = source.find('action="ai_insight_cache_hit"')
    select_idx = source.find("select(AiInsightCache)")
    assert audit_first_idx > 0
    assert select_idx > 0
    assert audit_first_idx < select_idx


def test_action_class_ai_insight_cache_accessed_value() -> None:
    """ActionClass.AI_INSIGHT_CACHE_ACCESSED enum value = 'ai_insight_cache_accessed'."""
    assert ActionClass.AI_INSIGHT_CACHE_ACCESSED.value == "ai_insight_cache_accessed"


# ── 6. AD-7 strict invariant × 1 ──────────────────────────────────


def test_ad7_strict_invariant_auto_analysis_only() -> None:
    """AD-7 strict invariant: 10-2 wire 진입 시점에 all 3 default insights are auto_analysis."""
    insights = make_default_insights("2026-07")
    for entry in insights:
        assert entry.source_kind == SourceKind.AUTO_ANALYSIS
    # 'auto_analysis' present in canonical value set
    assert "auto_analysis" in SOURCE_KIND_VALUES


# ── 7. AiInsightCache ORM (2 cases) ───────────────────────────────


def test_ai_insight_cache_orm_table_name() -> None:
    """AiInsightCache ORM maps to 'ai_insight_cache' table."""
    assert AiInsightCache.__tablename__ == "ai_insight_cache"


def test_ai_insight_cache_orm_columns() -> None:
    """AiInsightCache ORM has all 10 expected columns."""
    columns = {c.name for c in AiInsightCache.__table__.columns}
    expected = {
        "insight_cache_id",
        "tenant_id",
        "period_key",
        "calculation_result_hash",
        "insight_kind",
        "source_kind",
        "question",
        "answer",
        "evidence_ref",
        "generated_at",
    }
    assert expected.issubset(columns)