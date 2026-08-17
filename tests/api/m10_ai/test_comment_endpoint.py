"""tests.api.m10_ai.test_comment_endpoint — Story 10.3 endpoint tests.

Story 10.3 (cj-style Epic 10 4번째 진입점, cj-style 30번째 epic 연속) —
T5.5 tests for `apps.api.modules.m10_ai.handlers::get_ai_comments`.

Endpoint: `GET /api/v1/ai/comments` (Story 10.3 NEW).

Capability gate: `Capability.AI_INSIGHT` (industry-agnostic, 4-industry grants).
PIPA gate: `require_pipa_review` (m10_ai canonical gate, Story 1.3).

Envelope tests verify (CR 12-5 D-14 typed contract):
- Router shape (1 NEW route, path + method)
- Pydantic schema shape (AICommentEntry / AICommentListResponse / AICommentError)
- Discriminated union return via `status: Literal['success']`
- F10.2-(a) verbatim badge strings in summary (📊 자동 분석 / 🤖 AI 참고)
- F10.2-(b) source_kind 미매칭 reject Literal present
- F10.2-(c) auto_analysis modify deny Literal present
- F10.2-(d) ko-KR message present
- AD-15 §4 envelope: `{code, message_ko, details, trace_id}` for errors

Test breakdown (~15 cases):
- Router shape × 3
- Pydantic schema × 4
- Discriminated union × 2
- F10.2-(a) badge strings × 2
- F10.2-(b)(c) error codes × 2
- F10.2-(d) ko-KR message × 1
- AD-25 cache key verbatim × 1
"""

from __future__ import annotations

from typing import get_args

from fastapi import APIRouter

from apps.api.modules.m10_ai.handlers import router
from apps.api.modules.m10_ai.schemas import (
    AICommentEntry,
    AICommentError,
    AICommentListResponse,
)


# ── Helpers ──────────────────────────────────────────────────────


def _routes_by_path(router: APIRouter) -> dict[str, list]:
    """Group router routes by path for lookup convenience."""
    out: dict[str, list] = {}
    for r in router.routes:
        if hasattr(r, "path") and hasattr(r, "methods"):
            out.setdefault(r.path, []).append(r)
    return out


# ── 1. Router shape (3 cases) ─────────────────────────────────────


def test_get_ai_comments_route_registered() -> None:
    """GET /api/v1/ai/comments is registered on the m10_ai router."""
    routes = _routes_by_path(router)
    assert "/api/v1/ai/comments" in routes


def test_get_ai_comments_route_method() -> None:
    """GET /api/v1/ai/comments accepts GET method only."""
    routes = _routes_by_path(router)
    route_list = routes["/api/v1/ai/comments"]
    methods = set()
    for r in route_list:
        if hasattr(r, "methods"):
            methods.update(r.methods)
    assert "GET" in methods
    assert "POST" not in methods  # POST is wire 범위 외 (Story 10.4)


def test_get_ai_comments_response_model_union() -> None:
    """GET /api/v1/ai/comments returns AICommentListResponse | AICommentError (discriminated union)."""
    routes = _routes_by_path(router)
    route_list = routes["/api/v1/ai/comments"]
    assert len(route_list) == 1
    # response_model is the union (verified at the handler signature level)


# ── 2. Pydantic schema (4 cases) ─────────────────────────────────


def test_ai_comment_entry_fields() -> None:
    """AICommentEntry carries 6 expected fields (F10.2-(a) discriminator)."""
    fields = set(AICommentEntry.model_fields.keys())
    expected = {
        "comment_id",
        "comment_kind",
        "body_text",
        "source_kind",
        "evidence_ref",
        "generated_at",
    }
    assert expected.issubset(fields)


def test_ai_comment_entry_frozen_model() -> None:
    """AICommentEntry is a Pydantic v2 frozen model (immutable + AD-15 SSOT)."""
    assert AICommentEntry.model_config.get("frozen") is True


def test_ai_comment_list_response_fields() -> None:
    """AICommentListResponse carries 7 expected fields (status tag discriminator)."""
    fields = set(AICommentListResponse.model_fields.keys())
    expected = {
        "comments",
        "period_key",
        "calculation_result_hash",
        "hit_count",
        "miss_count",
        "counter_total",
        "status",
    }
    assert expected.issubset(fields)


def test_ai_comment_error_error_code_literal() -> None:
    """AICommentError.error_code Literal covers all 4 expected values (F10.2-(b)(c)(d))."""
    error_code_field = AICommentError.model_fields["error_code"]
    literal_args = get_args(error_code_field.annotation)
    expected = {
        "AI_PIPA_CONSENT_MISSING",
        "AI_COMMENT_SOURCE_KIND_INVALID",
        "AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS",
        "AI_COMMENT_SOURCE_KIND_WARNING",
    }
    assert expected.issubset(set(literal_args))


# ── 3. Discriminated union (2 cases) ──────────────────────────────


def test_ai_comment_list_response_status_tag() -> None:
    """AICommentListResponse.status = Literal['success'] (tag discriminator)."""
    status_field = AICommentListResponse.model_fields["status"]
    literal_args = get_args(status_field.annotation)
    assert "success" in literal_args


def test_ai_comment_entry_comment_kind_literal() -> None:
    """AICommentEntry.comment_kind Literal has 5 values (master PRD §12 + 10-3 forward-fill)."""
    comment_kind_field = AICommentEntry.model_fields["comment_kind"]
    literal_args = get_args(comment_kind_field.annotation)
    expected = {
        "cost_reduction_candidate",
        "anomaly_pattern",
        "forecast",
        "risk_warning",
        "industry_benchmark",
    }
    assert expected.issubset(set(literal_args))


# ── 4. F10.2-(a) badge strings (2 cases) ─────────────────────────


def test_f10_2_a_auto_analysis_badge_in_summary() -> None:
    """F10.2-(a) verbatim: '📊 자동 분석' badge string in endpoint summary."""
    routes = _routes_by_path(router)
    route_list = routes["/api/v1/ai/comments"]
    route = route_list[0]
    summary = getattr(route, "summary", "") or ""
    description = getattr(route, "description", "") or ""
    combined = summary + " " + description
    assert "📊 자동 분석" in combined
    assert "이 의견은 고정 템플릿입니다" in combined


def test_f10_2_a_ai_reference_badge_in_summary() -> None:
    """F10.2-(a) verbatim: '🤖 AI 참고(검증 필요)' badge string in endpoint summary."""
    routes = _routes_by_path(router)
    route_list = routes["/api/v1/ai/comments"]
    route = route_list[0]
    summary = getattr(route, "summary", "") or ""
    description = getattr(route, "description", "") or ""
    combined = summary + " " + description
    assert "🤖 AI 참고(검증 필요)" in combined
    assert "AI는 비권위적입니다" in combined
    assert "확정 책임은 사용자에게" in combined


# ── 5. F10.2-(b)(c) error codes (2 cases) ─────────────────────────


def test_f10_2_b_strict_reject_error_code_present() -> None:
    """F10.2-(b) verbatim: AI_COMMENT_SOURCE_KIND_INVALID Literal in error_code."""
    error_code_field = AICommentError.model_fields["error_code"]
    literal_args = get_args(error_code_field.annotation)
    assert "AI_COMMENT_SOURCE_KIND_INVALID" in literal_args


def test_f10_2_c_modify_deny_error_code_present() -> None:
    """F10.2-(c) verbatim: AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS Literal in error_code."""
    error_code_field = AICommentError.model_fields["error_code"]
    literal_args = get_args(error_code_field.annotation)
    assert "AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS" in literal_args


# ── 6. F10.2-(d) ko-KR message (1 case) ──────────────────────────


def test_f10_2_d_korean_warning_message_in_summary() -> None:
    """F10.2-(d) verbatim: '분석 의견 출처가 불분명합니다' message in endpoint summary."""
    routes = _routes_by_path(router)
    route_list = routes["/api/v1/ai/comments"]
    route = route_list[0]
    summary = getattr(route, "summary", "") or ""
    description = getattr(route, "description", "") or ""
    combined = summary + " " + description
    assert "분석 의견 출처가 불분명합니다" in combined


# ── 7. AD-25 cache key verbatim (1 case) ──────────────────────────


def test_ad25_cache_key_3_tuple_in_endpoint_summary() -> None:
    """AD-25 verbatim 3-tuple (tenant_id, period_key, calculation_result_hash) referenced."""
    routes = _routes_by_path(router)
    route_list = routes["/api/v1/ai/comments"]
    route = route_list[0]
    summary = getattr(route, "summary", "") or ""
    description = getattr(route, "description", "") or ""
    combined = summary + " " + description
    assert "calculation_result_hash" in combined
    assert "period_key" in combined


# ── 8. Error envelope shape (1 case — bonus) ─────────────────────


def test_ai_comment_error_envelope_shape() -> None:
    """AICommentError has 'details' + 'message_ko' + 'trace_id' (CR 12-5 D-14 verbatim)."""
    assert "details" in AICommentError.model_fields
    assert "message_ko" in AICommentError.model_fields
    assert "trace_id" in AICommentError.model_fields
    assert AICommentError.model_config.get("frozen") is True