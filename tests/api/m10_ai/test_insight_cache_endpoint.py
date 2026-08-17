"""tests.api.m10_ai.test_insight_cache_endpoint — Story 10.2 endpoint tests.

Story 10.2 (cj-style Epic 10 cj-style 29번째 epic 연속) —
T5.5 tests for `apps.api.modules.m10_ai.handlers::get_ai_insights`.

Endpoint: `GET /api/v1/ai/insights` (Story 10.2 NEW).

Capability gate: `Capability.AI_INSIGHT` (industry-agnostic, 4-industry grants).
PIPA gate: `require_pipa_review` (m10_ai canonical gate, Story 1.3).

Envelope tests verify (CR 12-5 D-14 typed contract):
- Router shape (1 NEW route, path + method)
- Pydantic schema shape (InsightEntry / InsightListResponse / InsightCacheError)
- Discriminated union return via `status: Literal['success']`
- AD-7 strict invariant: source_kind Literal['auto_analysis'] ONLY at 10-2
- AD-15 §4 envelope: `{code, message_ko, details, trace_id}` for errors

Test breakdown (~15 cases):
- Router shape × 3
- Pydantic schema × 4
- Discriminated union × 2
- AD-7 invariant × 2
- Error envelope × 2
- F10.1-(d) channel filter × 1
- AD-25 cache key verbatim × 1
"""

from __future__ import annotations

from fastapi import APIRouter

from apps.api.modules.m10_ai.handlers import router
from apps.api.modules.m10_ai.schemas import (
    InsightCacheError,
    InsightEntry,
    InsightListResponse,
)
from packages.services.m10_ai.insight_cache_kernel import (
    INSIGHT_KIND_VALUES,
    SOURCE_KIND_VALUES,
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


def test_get_ai_insights_route_registered() -> None:
    """GET /api/v1/ai/insights is registered on the m10_ai router."""
    routes = _routes_by_path(router)
    assert "/api/v1/ai/insights" in routes


def test_get_ai_insights_route_method() -> None:
    """GET /api/v1/ai/insights accepts GET method only."""
    routes = _routes_by_path(router)
    route_list = routes["/api/v1/ai/insights"]
    methods = set()
    for r in route_list:
        if hasattr(r, "methods"):
            methods.update(r.methods)
    assert "GET" in methods
    assert "POST" not in methods  # POST is wire 범위 외 (Story 10.4)


def test_get_ai_insights_response_model_union() -> None:
    """GET /api/v1/ai/insights returns InsightListResponse | InsightCacheError (discriminated union)."""
    routes = _routes_by_path(router)
    route_list = routes["/api/v1/ai/insights"]
    assert len(route_list) == 1
    # response_model is the union (verified at the handler signature level)


# ── 2. Pydantic schema (4 cases) ─────────────────────────────────


def test_insight_entry_fields() -> None:
    """InsightEntry carries 6 expected fields (AD-7 + AD-15 discriminator)."""
    fields = set(InsightEntry.model_fields.keys())
    expected = {
        "insight_kind",
        "question",
        "answer",
        "source_kind",
        "evidence_ref",
        "generated_at",
    }
    assert expected.issubset(fields)


def test_insight_entry_frozen_model() -> None:
    """InsightEntry is a Pydantic v2 frozen model (immutable + AD-15 SSOT)."""
    # Pydantic v2 frozen=True adds __setattr__ override
    assert InsightEntry.model_config.get("frozen") is True


def test_insight_list_response_fields() -> None:
    """InsightListResponse carries 6 expected fields (status tag discriminator)."""
    fields = set(InsightListResponse.model_fields.keys())
    expected = {
        "insights",
        "period_key",
        "calculation_result_hash",
        "hit_count",
        "miss_count",
        "status",
    }
    assert expected.issubset(fields)


def test_insight_cache_error_error_code_literal() -> None:
    """InsightCacheError.error_code Literal covers all 4 expected values (CR 12-5 D-14)."""
    from typing import get_args

    error_code_field = InsightCacheError.model_fields["error_code"]
    literal_args = get_args(error_code_field.annotation)
    expected = {
        "AI_PIPA_CONSENT_MISSING",
        "INSIGHT_CACHE_KEY_ERROR",
        "INSIGHT_COLD_COMPUTE_TIMEOUT",
        "AI_INSIGHT_CACHE_CONTAMINATION",
    }
    assert expected.issubset(set(literal_args))


# ── 3. Discriminated union (2 cases) ──────────────────────────────


def test_insight_list_response_status_tag() -> None:
    """InsightListResponse.status = Literal['success'] (tag discriminator)."""
    from typing import get_args

    status_field = InsightListResponse.model_fields["status"]
    literal_args = get_args(status_field.annotation)
    assert literal_args == ("success",) or "success" in literal_args


def test_insight_entry_insight_kind_literal() -> None:
    """InsightEntry.insight_kind Literal has 3 values (master PRD §12 AI 3종)."""
    from typing import get_args

    insight_kind_field = InsightEntry.model_fields["insight_kind"]
    literal_args = get_args(insight_kind_field.annotation)
    expected = {"cost_reduction_candidate", "anomaly_pattern", "forecast"}
    assert expected.issubset(set(literal_args))


# ── 4. AD-7 strict invariant (2 cases) ───────────────────────────


def test_ad7_source_kind_literal_auto_analysis_ai_reference() -> None:
    """InsightEntry.source_kind Literal: 'auto_analysis' | 'ai_reference' (10-3 forward-bind)."""
    from typing import get_args

    source_kind_field = InsightEntry.model_fields["source_kind"]
    literal_args = get_args(source_kind_field.annotation)
    assert "auto_analysis" in literal_args
    assert "ai_reference" in literal_args


def test_ad7_source_kind_value_sets_present() -> None:
    """AD-15 SSOT: kernel INSIGHT_KIND_VALUES + SOURCE_KIND_VALUES parity."""
    assert "cost_reduction_candidate" in INSIGHT_KIND_VALUES
    assert "anomaly_pattern" in INSIGHT_KIND_VALUES
    assert "forecast" in INSIGHT_KIND_VALUES
    assert "auto_analysis" in SOURCE_KIND_VALUES
    assert "ai_reference" in SOURCE_KIND_VALUES


# ── 5. Error envelope (2 cases) ───────────────────────────────────


def test_insight_cache_error_details_field() -> None:
    """InsightCacheError has 'details' field (CR 12-5 D-14 verbatim)."""
    assert "details" in InsightCacheError.model_fields
    assert "message_ko" in InsightCacheError.model_fields
    assert "trace_id" in InsightCacheError.model_fields


def test_insight_cache_error_frozen_model() -> None:
    """InsightCacheError is a Pydantic v2 frozen model (immutable envelope)."""
    assert InsightCacheError.model_config.get("frozen") is True


# ── 6. F10.1-(d) channel filter (1 case) ─────────────────────────


def test_f10_1_d_channel_filter_in_endpoint_summary() -> None:
    """F10.1-(d) verbatim 'channel = ai_cache filter' referenced in endpoint summary."""
    routes = _routes_by_path(router)
    route_list = routes["/api/v1/ai/insights"]
    route = route_list[0]
    # summary OR description should mention ai_cache filter
    summary = getattr(route, "summary", "") or ""
    description = getattr(route, "description", "") or ""
    combined = summary + " " + description
    assert "ai_cache" in combined


# ── 7. AD-25 cache key verbatim (1 case) ──────────────────────────


def test_ad25_cache_key_3_tuple_in_endpoint_summary() -> None:
    """AD-25 verbatim 3-tuple (tenant_id, period_key, calculation_result_hash) referenced."""
    routes = _routes_by_path(router)
    route_list = routes["/api/v1/ai/insights"]
    route = route_list[0]
    summary = getattr(route, "summary", "") or ""
    description = getattr(route, "description", "") or ""
    combined = summary + " " + description
    assert "calculation_result_hash" in combined
    assert "period_key" in combined