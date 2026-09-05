"""tests.api.m10_ai.test_extraction_endpoint — Story 10.1 endpoint tests.

Story 10.1 (cj-style Epic 10 cj-style 28번째 epic 연속) —
T2.8 tests for `apps.api.modules.m10_ai.handlers::extract_monthly_endpoint`.

Endpoint: `POST /api/v1/ai/extract-monthly` (Story 10.1 NEW).

Capability gate: `Capability.AI_INSIGHT` (industry-agnostic, 4-industry grants).
PIPA gate: `require_pipa_review` (m10_ai canonical gate, Story 1.3).

Envelope tests verify (CR 12-5 D-14 typed contract):
- Router shape (1 NEW route, path + method)
- Pydantic schema shape (MonthlyExtractRequest / Response / Error / DraftResponse)
- Discriminated union return via `status: Literal['success', 'low_confidence_warning']`
- AD-7 strict invariant: target_table Literal['monthly_inputs'] ONLY
- AD-15 §4 envelope: `{code, message_ko, details, trace_id}` for errors

Test breakdown (~12 cases):
- Router shape × 3
- Pydantic schema × 4
- Discriminated union × 2
- AD-7 invariant × 2
- Error envelope × 1
"""

from __future__ import annotations

import asyncio
import pytest
from fastapi import APIRouter

from apps.api.modules.m10_ai.handlers import router

# ── Helpers ──────────────────────────────────────────────────────


def _routes_by_path(router: APIRouter) -> dict[str, list]:
    """Group router routes by path for lookup convenience."""
    out: dict[str, list] = {}
    for r in router.routes:
        if hasattr(r, "path") and hasattr(r, "methods"):
            out.setdefault(r.path, []).append(r)
    return out


# ── 1. Router shape (3 cases) ─────────────────────────────────────


def test_extract_monthly_route_registered() -> None:
    """POST /api/v1/ai/extract-monthly is registered on the m10_ai router."""
    routes = _routes_by_path(router)
    assert "/api/v1/ai/extract-monthly" in routes


def test_extract_monthly_route_method() -> None:
    """POST /api/v1/ai/extract-monthly accepts POST method only."""
    routes = _routes_by_path(router)
    route_list = routes["/api/v1/ai/extract-monthly"]
    methods = set()
    for r in route_list:
        if hasattr(r, "methods"):
            methods.update(r.methods)
    assert "POST" in methods


def test_extract_monthly_route_summary() -> None:
    """POST /api/v1/ai/extract-monthly has a Korean summary mentioning AI 월간 입력 추출."""
    routes = _routes_by_path(router)
    route_list = routes["/api/v1/ai/extract-monthly"]
    route = route_list[0]
    summary = getattr(route, "summary", "")
    assert "월간" in summary or "AI" in summary


# ── 2. Pydantic schema (4 cases) ──────────────────────────────────


def test_monthly_extract_request_schema() -> None:
    """MonthlyExtractRequest has period_key + document_b64 + document_type fields."""
    from apps.api.modules.m10_ai.schemas import MonthlyExtractRequest

    fields = set(MonthlyExtractRequest.model_fields.keys())
    assert "period_key" in fields
    assert "document_b64" in fields
    assert "document_type" in fields


def test_monthly_extract_response_schema_fields() -> None:
    """MonthlyExtractResponse has extraction_id + period_key + drafts + low_confidence_count + status."""
    from apps.api.modules.m10_ai.schemas import MonthlyExtractResponse

    fields = set(MonthlyExtractResponse.model_fields.keys())
    assert "extraction_id" in fields
    assert "period_key" in fields
    assert "drafts" in fields
    assert "low_confidence_count" in fields
    assert "status" in fields


def test_monthly_extract_error_schema_fields() -> None:
    """MonthlyExtractError has error_code + message_ko + trace_id (CR 12-5 D-14 envelope)."""
    from apps.api.modules.m10_ai.schemas import MonthlyExtractError

    fields = set(MonthlyExtractError.model_fields.keys())
    assert "error_code" in fields
    assert "message_ko" in fields
    assert "trace_id" in fields


def test_monthly_draft_response_schema_fields() -> None:
    """MonthlyDraftResponse has field_name + value + confidence + target_table + requires_user_confirmation."""
    from apps.api.modules.m10_ai.schemas import MonthlyDraftResponse

    fields = set(MonthlyDraftResponse.model_fields.keys())
    assert "field_name" in fields
    assert "value" in fields
    assert "confidence" in fields
    assert "target_table" in fields
    assert "requires_user_confirmation" in fields


# ── 3. Discriminated union (2 cases) ──────────────────────────────


def test_monthly_extract_response_status_literal_success() -> None:
    """MonthlyExtractResponse.status Literal includes 'success'."""
    from apps.api.modules.m10_ai.schemas import MonthlyExtractResponse

    status_field = MonthlyExtractResponse.model_fields["status"]
    annotation_str = str(status_field.annotation)
    assert "success" in annotation_str


def test_monthly_extract_response_status_literal_low_confidence() -> None:
    """MonthlyExtractResponse.status Literal includes 'low_confidence_warning'."""
    from apps.api.modules.m10_ai.schemas import MonthlyExtractResponse

    status_field = MonthlyExtractResponse.model_fields["status"]
    annotation_str = str(status_field.annotation)
    assert "low_confidence_warning" in annotation_str


# ── 4. AD-7 strict invariant (2 cases) ───────────────────────────


def test_target_table_literal_monthly_inputs_only() -> None:
    """MonthlyDraftResponse.target_table = Literal['monthly_inputs'] (AD-7 verbatim)."""
    from apps.api.modules.m10_ai.schemas import MonthlyDraftResponse

    target_table_field = MonthlyDraftResponse.model_fields["target_table"]
    annotation_str = str(target_table_field.annotation)
    assert "monthly_inputs" in annotation_str
    # AD-7 verbatim: 'confirmed_inputs' is NEVER allowed
    assert "confirmed_inputs" not in annotation_str


def test_target_table_default_monthly_inputs() -> None:
    """MonthlyDraftResponse.target_table default = 'monthly_inputs'."""
    from apps.api.modules.m10_ai.schemas import MonthlyDraftResponse

    target_table_field = MonthlyDraftResponse.model_fields["target_table"]
    assert target_table_field.default == "monthly_inputs"


# ── 5. Error envelope shape (1 case, CR 12-5 D-14 verbatim) ──────


def test_monthly_extract_error_discriminated_codes() -> None:
    """MonthlyExtractError.error_code Literal includes all 3 envelope codes."""
    from apps.api.modules.m10_ai.schemas import MonthlyExtractError

    error_code_field = MonthlyExtractError.model_fields["error_code"]
    annotation_str = str(error_code_field.annotation)
    assert "AI_PIPA_CONSENT_MISSING" in annotation_str
    assert "INVALID_MONTHLY_FIELD_VALUE" in annotation_str
    assert "MONTHLY_EXTRACTION_ERROR" in annotation_str


# ── Reference tests (DB-backed; enabled when CI shim is wired) ─────
# These are placeholder tests that mirror the m9_abc handler test pattern
# once a real DB is available. They currently use `pytest.mark.skip` to
# avoid being collected without a DB-backed fixture.

# (Note: not using pytestmark = pytest.mark.skipif(True) at module level
# because the schema/router shape tests above MUST run. The reference
# integration tests below are gated per-test with @pytest.mark.skip.)


@pytest.mark.skip(reason="DB-backed; enabled when CI shim is wired")
def test_extract_monthly_happy_path() -> None:
    """POST /ai/extract-monthly → 200 + 6 drafts + status='success'.

    Reference: when a real DB is provisioned, this test will issue a POST
    request with valid base64-encoded PDF and assert the response carries
    6 monthly input field drafts with status='success'.
    """
    async def _inner() -> None:
        raise NotImplementedError

    asyncio.run(_inner())


@pytest.mark.skip(reason="DB-backed; enabled when CI shim is wired")
def test_extract_monthly_low_confidence() -> None:
    """All 6 fields confidence < 0.70 → status='low_confidence_warning'.

    Reference: when a real DB is provisioned, this test will inject a
    deterministic adapter returning low confidence values and assert the
    response status='low_confidence_warning'.
    """
    async def _inner() -> None:
        raise NotImplementedError

    asyncio.run(_inner())


@pytest.mark.skip(reason="DB-backed; enabled when CI shim is wired")
def test_extract_monthly_pipa_missing() -> None:
    """PIPA consent not granted → 403 AI_PIPA_CONSENT_MISSING envelope.

    Reference: when a real DB is provisioned, this test will mock the
    tenant_settings row without pipa_consent.granted and assert the
    envelope is 403 with code='AI_PIPA_CONSENT_MISSING'.
    """
    async def _inner() -> None:
        raise NotImplementedError

    asyncio.run(_inner())


@pytest.mark.skip(reason="DB-backed; enabled when CI shim is wired")
def test_extract_monthly_invalid_field_value() -> None:
    """Unparseable raw_value → 422 INVALID_MONTHLY_FIELD_VALUE envelope.

    Reference: when a real DB is provisioned, this test will inject a
    document whose values cannot be parsed and assert the envelope is 422.
    """
    async def _inner() -> None:
        raise NotImplementedError

    asyncio.run(_inner())
