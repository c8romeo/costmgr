"""tests.api.m10_ai.test_comment_service — Story 10.3 service-layer tests.

Story 10.3 (cj-style Epic 10 4번째 진입점, cj-style 30번째 epic 연속) —
T4.3 tests for `apps.api.modules.m10_ai.service::CommentService`.

Test breakdown (~18 cases, no DB):
- import sanity × 3 (CommentService + 2 NEW typed exceptions + AICommentListResult)
- signature contract × 4 (list_comments + AICommentListResult fields + 2 helpers)
- AD-25 verbatim 3-tuple cache key × 1 (CommentService uses AiInsightComment ORM)
- F10.1-(d) channel filter × 1 (CHANNEL = 'ai_cache' string literal present)
- audit-first INSERT × 2 (CR 1.1 verbatim — 2 NEW actions emit BEFORE raise)
- AIInsightCacheAction Literal × 1 (2 NEW 10-3 values present)
- AD-7 strict invariant × 2 (validate_source_kind + assert_comment_mutable)
- F10.2-(b)(c) Korean SSOT message constants × 1
- derive_counter pure SQL form × 1
- AiInsightComment ORM shape × 2

P-015 SSOT pattern: capability matrix drift detector runs in
`tests/integration/test_capability_matrix_v1_21_drift.py` (T6.1, 16 cases PASS after T6 wire).
"""

from __future__ import annotations

import inspect
import uuid

import pytest

from apps.api.core.audit_action import (
    AIInsightCacheAction,
    ActionClass,
)
from apps.api.core.db_models import AiInsightComment
from apps.api.modules.m10_ai.service import (
    AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS_KO,
    AI_COMMENT_SOURCE_KIND_INVALID_KO,
    AICommentImmutableAutoAnalysisError,
    AICommentListResult,
    AICommentSourceKindInvalidError,
    CommentService,
    assert_comment_mutable,
    validate_source_kind,
)
from packages.services.m10_ai.insight_cache_kernel import (
    SOURCE_KIND_VALUES,
    SourceKind,
    make_default_insights,
)


# ── 1. Import sanity (3 cases) ────────────────────────────────────


def test_comment_service_importable() -> None:
    """CommentService class exists and is importable (T4.1 wire)."""
    assert CommentService is not None
    assert inspect.isclass(CommentService)


def test_2_new_typed_exceptions_importable() -> None:
    """2 NEW typed exceptions all importable (T4.1 wire)."""
    assert AICommentSourceKindInvalidError is not None
    assert AICommentImmutableAutoAnalysisError is not None


def test_ai_comment_list_result_dataclass_fields() -> None:
    """AICommentListResult carries the 7 expected fields (F10.2-(a))."""
    fields = {f.name for f in AICommentListResult.__dataclass_fields__.values()}
    expected = {
        "comments",
        "period_key",
        "calculation_result_hash",
        "hit_count",
        "miss_count",
        "counter_total",
        "trace_id",
    }
    assert expected.issubset(fields)


# ── 2. Signature contract (4 cases) ────────────────────────────────


def test_comment_service_constructor_signature() -> None:
    """__init__(session, *, trace_id) — session + trace_id required."""
    sig = inspect.signature(CommentService.__init__)
    params = sig.parameters
    assert "self" in params
    assert "session" in params
    assert "trace_id" in params


def test_list_comments_signature() -> None:
    """list_comments(self, *, tenant_id, period_key, calculation_result_hash, comment_kind=None)."""
    sig = inspect.signature(CommentService.list_comments)
    params = sig.parameters
    assert "tenant_id" in params
    assert "period_key" in params
    assert "calculation_result_hash" in params
    assert "comment_kind" in params


def test_list_comments_is_coroutine() -> None:
    """list_comments is an async coroutine function."""
    assert inspect.iscoroutinefunction(CommentService.list_comments)


def test_comment_kind_optional_filter_param() -> None:
    """comment_kind parameter defaults to None (F10.2-(a) 분기)."""
    sig = inspect.signature(CommentService.list_comments)
    assert sig.parameters["comment_kind"].default is None


# ── 3. AD-25 verbatim 3-tuple cache key (1 case) ──────────────────


def test_list_comments_selects_on_ad25_3_tuple() -> None:
    """list_comments SELECT WHERE (tenant_id, period_key, calculation_result_hash)."""
    import apps.api.modules.m10_ai.service as svc

    source = inspect.getsource(svc.CommentService.list_comments)
    # 3 AD-25 components present in SELECT WHERE
    assert "AiInsightComment.tenant_id == tenant_id" in source
    assert "AiInsightComment.period_key == period_key" in source
    assert (
        "AiInsightComment.calculation_result_hash == calculation_result_hash"
        in source
    )


# ── 4. F10.1-(d) channel filter (1 case) ──────────────────────────


def test_ai_cache_channel_filter_constant() -> None:
    """F10.1-(d) verbatim: 'ai_cache' channel filter 강제 (in service source)."""
    import apps.api.modules.m10_ai.service as svc

    source = inspect.getsource(svc)
    assert "'ai_cache'" in source  # channel filter string literal present


# ── 5. Audit-first INSERT (CR 1.1 verbatim) (2 cases) ─────────────


def test_audit_first_emits_invalid_source_kind_action() -> None:
    """reject_invalid_source_kind emits audit BEFORE the raise (F10.2-(b))."""
    import apps.api.modules.m10_ai.service as svc

    source = inspect.getsource(svc.CommentService.reject_invalid_source_kind)
    audit_idx = source.find('action="ai_insight_cache_invalid_source_kind"')
    raise_idx = source.find("raise AICommentSourceKindInvalidError")
    assert audit_idx > 0
    assert raise_idx > 0
    assert audit_idx < raise_idx


def test_audit_first_emits_auto_analysis_modify_denied_action() -> None:
    """deny_auto_analysis_modify emits audit BEFORE the raise (F10.2-(c))."""
    import apps.api.modules.m10_ai.service as svc

    source = inspect.getsource(svc.CommentService.deny_auto_analysis_modify)
    audit_idx = source.find(
        'action="ai_insight_cache_auto_analysis_modify_denied"'
    )
    raise_idx = source.find("raise AICommentImmutableAutoAnalysisError")
    assert audit_idx > 0
    assert raise_idx > 0
    assert audit_idx < raise_idx


# ── 6. AIInsightCacheAction Literal (1 case) ──────────────────────


def test_ai_insight_cache_action_literal_10_3_values() -> None:
    """AIInsightCacheAction Literal includes 2 NEW 10-3 values (F10.2-(b)(c))."""
    args = AIInsightCacheAction.__args__
    assert "ai_insight_cache_invalid_source_kind" in args
    assert "ai_insight_cache_auto_analysis_modify_denied" in args
    # preserve 4 baseline + 2 NEW = 6 total
    assert len(args) >= 6


# ── 7. AD-7 strict invariant (2 cases) ────────────────────────────


def test_validate_source_kind_accepts_canonical_values() -> None:
    """validate_source_kind returns SourceKind for both canonical literals."""
    auto = validate_source_kind("auto_analysis")
    ai_ref = validate_source_kind("ai_reference")
    assert auto is SourceKind.AUTO_ANALYSIS
    assert ai_ref is SourceKind.AI_REFERENCE
    # SOURCE_KIND_VALUES SSOT preserved (no new value introduced at 10-3 wire)
    assert "auto_analysis" in SOURCE_KIND_VALUES
    assert "ai_reference" in SOURCE_KIND_VALUES


def test_validate_source_kind_strict_rejects_unknown_value() -> None:
    """validate_source_kind raises AICommentSourceKindInvalidError on unknown value."""
    with pytest.raises(AICommentSourceKindInvalidError) as exc:
        validate_source_kind("human_input", trace_id="trace-x")
    assert exc.value.received_value == "human_input"
    assert exc.value.trace_id == "trace-x"
    assert "auto_analysis" in exc.value.allowed_values
    assert "ai_reference" in exc.value.allowed_values


# ── 8. F10.2-(b)(c) Korean SSOT message constants (1 case) ─────────


def test_korean_ssot_message_constants() -> None:
    """Korean SSOT message constants match master PRD §13.1 ko-KR + NFR18."""
    assert AI_COMMENT_SOURCE_KIND_INVALID_KO == "분석 의견 출처가 불분명합니다"
    assert (
        AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS_KO
        == "자동 분석 의견은 고정 템플릿이므로 수정할 수 없습니다"
    )


# ── 9. assert_comment_mutable (1 case) ────────────────────────────


def test_assert_comment_mutable_denies_auto_analysis() -> None:
    """assert_comment_mutable denies modify on auto_analysis (F10.2-(c))."""
    with pytest.raises(AICommentImmutableAutoAnalysisError):
        assert_comment_mutable(
            source_kind="auto_analysis",
            comment_id="comment-1",
            trace_id="trace-z",
        )


def test_assert_comment_mutable_allows_ai_reference() -> None:
    """assert_comment_mutable allows modify on ai_reference (F10.2-(c) verbatim)."""
    # Should NOT raise
    assert_comment_mutable(
        source_kind="ai_reference",
        comment_id="comment-2",
        trace_id="trace-w",
    )


# ── 10. derive_counter pure SQL form (1 case) ─────────────────────


def test_derive_counter_selects_audit_logs_action_in() -> None:
    """derive_counter SELECT COUNT(audit_logs) WHERE action IN (2 NEW 10-3 actions)."""
    import apps.api.modules.m10_ai.service as svc

    source = inspect.getsource(svc.CommentService.derive_counter)
    assert "select(func.count())" in source
    assert "AuditLog" in source
    assert "ai_insight_cache_invalid_source_kind" in source
    assert "ai_insight_cache_auto_analysis_modify_denied" in source


# ── 11. AiInsightComment ORM (2 cases) ─────────────────────────────


def test_ai_insight_comment_orm_table_name() -> None:
    """AiInsightComment ORM maps to 'ai_insight_comments' table."""
    assert AiInsightComment.__tablename__ == "ai_insight_comments"


def test_ai_insight_comment_orm_columns() -> None:
    """AiInsightComment ORM has all 8 expected columns."""
    columns = {c.name for c in AiInsightComment.__table__.columns}
    expected = {
        "comment_id",
        "tenant_id",
        "period_key",
        "calculation_result_hash",
        "comment_kind",
        "source_kind",
        "body_text",
        "evidence_ref",
        "generated_at",
    }
    assert expected.issubset(columns)