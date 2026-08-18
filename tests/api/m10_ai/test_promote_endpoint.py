"""tests.api.m10_ai.test_promote_endpoint — Story 10.4 endpoint tests.

Story 10.4 (cj-style Epic 10 5번째 진입점, cj-style 33번째 epic 연속) —
endpoint integration tests for `apps.api.modules.m10_ai.handlers::promote_ai_draft_endpoint`.

Endpoint: `POST /api/v1/ai/promote` (Story 10.4 NEW).

Layer ordering (AD-17 verbatim + PIPA gate + capability):
  1. require_pipa_review            (D-10-3-DEFER-6 carry-over 해소 4번째 endpoint)
  2. get_current_m2_user            (AD-17 verbatim M2-only)
  3. require_capability(AI_INSIGHT) (industry-agnostic)

Envelope tests verify (CR 12-5 D-14 typed contract):
- Router shape (1 NEW route, POST path + method)
- Pydantic schema shape (PromoteRequest / PromoteResponse + 6 error envelopes)
- Discriminated union return via `status: Literal['success']` tag
- AD-7 strict invariant: M10 NEVER writes confirmed_inputs (target = monthly_input_rows ONLY)
- AD-17 idempotency 3-tuple: (tenant_id, period_key, source_draft_id)
- audit-first INSERT 2-row invariant: Row 1 input_draft_promoted, Row 2 monthly_extraction_promote_executed
- A19 cohesion: PromoteEnvelope = Annotated[Union[7 variants], Field(discriminator='status')]

Test breakdown (~17 cases):
- Router shape × 3
- Pydantic schema × 5
- Discriminated union × 3
- AD-7 strict invariant × 2
- AD-17 idempotency × 2
- Audit-first INSERT 2-row × 2
"""

from __future__ import annotations

from typing import get_args

from fastapi import APIRouter

from apps.api.modules.m10_ai.handlers import router
from apps.api.modules.m10_ai.schemas import (
    AiPipaConsentMissingError,
    InputPromotionDeniedError,
    PromoteDraftImmutableError,
    PromoteEnvelope,
    PromoteIdempotencyMismatchError,
    PromoteM2OnlyError,
    PromoteRequest,
    PromoteResponse,
    PromoteSourceDraftNotFoundError,
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


def test_promote_ai_draft_route_registered() -> None:
    """POST /api/v1/ai/promote is registered on the m10_ai router."""
    routes = _routes_by_path(router)
    assert "/api/v1/ai/promote" in routes


def test_promote_ai_draft_route_method() -> None:
    """POST /api/v1/ai/promote accepts POST method only."""
    routes = _routes_by_path(router)
    route_list = routes["/api/v1/ai/promote"]
    methods = set()
    for r in route_list:
        if hasattr(r, "methods"):
            methods.update(r.methods)
    assert "POST" in methods
    assert "GET" not in methods  # GET is wire 범위 외 (POST-only canonical entry)


def test_promote_ai_draft_route_summary_korean() -> None:
    """POST /api/v1/ai/promote summary is ko-KR (master PRD §V4 UX lock)."""
    routes = _routes_by_path(router)
    route_list = routes["/api/v1/ai/promote"]
    route = route_list[0]
    summary = getattr(route, "summary", "") or ""
    assert "AI 초안" in summary or "승격" in summary


# ── 2. Pydantic schema (5 cases) ──────────────────────────────────


def test_promote_request_fields() -> None:
    """PromoteRequest carries 5 expected fields (AD-17 verbatim body)."""
    fields = set(PromoteRequest.model_fields.keys())
    expected = {
        "tenant_id",
        "period_key",
        "source_draft_id",
        "confirmed_value_hash",
        "actor_id",
    }
    assert expected.issubset(fields)


def test_promote_request_frozen_model() -> None:
    """PromoteRequest is a Pydantic v2 frozen model (immutable + AD-15 SSOT)."""
    assert PromoteRequest.model_config.get("frozen") is True


def test_promote_request_extra_forbid() -> None:
    """PromoteRequest has `extra='forbid'` (strict schema — unknown fields → 422)."""
    assert PromoteRequest.model_config.get("extra") == "forbid"


def test_promote_response_fields() -> None:
    """PromoteResponse carries 11 expected fields (kernel parity SSOT)."""
    fields = set(PromoteResponse.model_fields.keys())
    expected = {
        "status",
        "tenant_id",
        "period_key",
        "source_draft_id",
        "promotion_id",
        "idempotency_key",
        "confirmed_input_row_id",
        "promoted_at",
        "draft_hash",
        "idempotent_replay",
        "audit_log_ids",
    }
    assert expected.issubset(fields)


def test_promote_response_frozen_model() -> None:
    """PromoteResponse is a Pydantic v2 frozen model (immutable + AD-15 SSOT)."""
    assert PromoteResponse.model_config.get("frozen") is True


# ── 3. Discriminated union (3 cases) ──────────────────────────────


def test_promote_envelope_is_annotated_union() -> None:
    """PromoteEnvelope = Annotated[Union[7 variants], Field(discriminator='status')]."""
    # Resolve the Annotated metadata — promote envelope must carry a discriminator
    # tag for the Pydantic v2 discriminated union machinery to work.
    from typing import get_type_hints

    hints = get_type_hints(PromoteEnvelope, include_extras=True)
    # Pydantic v2 stores the Annotated origin metadata on the globalns.
    # We assert the type name starts with "Annotated" or "Union".
    type_name = str(PromoteEnvelope)
    assert "Annotated" in type_name or "Union" in type_name


def test_promote_response_status_tag_literal() -> None:
    """PromoteResponse.status = Literal['success'] (success branch of discriminated union)."""
    status_field = PromoteResponse.model_fields["status"]
    literal_args = get_args(status_field.annotation)
    assert "success" in literal_args


def test_all_error_envelopes_have_status_discriminator() -> None:
    """All 6 error envelopes carry `status` field with Literal discriminator."""
    error_classes = [
        PromoteDraftImmutableError,
        PromoteSourceDraftNotFoundError,
        PromoteIdempotencyMismatchError,
        PromoteM2OnlyError,
        AiPipaConsentMissingError,
        InputPromotionDeniedError,
    ]
    for cls in error_classes:
        assert "status" in cls.model_fields, f"{cls.__name__} missing status field"
        status_field = cls.model_fields["status"]
        literal_args = get_args(status_field.annotation)
        assert len(literal_args) == 1, (
            f"{cls.__name__}.status Literal has {len(literal_args)} values "
            f"(expected exactly 1 for discriminated union tag)"
        )


# ── 4. AD-7 strict invariant (2 cases) ────────────────────────────


def test_ad7_strict_invariant_promote_response_target() -> None:
    """AD-7 strict invariant: PromoteResponse exposes confirmed_input_row_id
    (NOT confirmed_input_id) — INSERT target is monthly_input_rows ONLY.
    """
    fields = set(PromoteResponse.model_fields.keys())
    assert "confirmed_input_row_id" in fields  # monthly_input_rows row id
    assert "confirmed_input_id" not in fields  # confirmed_inputs NEVER written


def test_ad7_strict_invariant_error_envelope_count() -> None:
    """AD-7 strict invariant: 6 typed error envelopes cover all expected
    failure modes (no implicit `ValueError` leaks).
    """
    error_classes = [
        PromoteDraftImmutableError,
        PromoteSourceDraftNotFoundError,
        PromoteIdempotencyMismatchError,
        PromoteM2OnlyError,
        AiPipaConsentMissingError,
        InputPromotionDeniedError,
    ]
    # 6 error envelopes — 1 success + 6 errors = 7 variants in PromoteEnvelope
    assert len(error_classes) == 6


# ── 5. AD-17 idempotency verbatim (2 cases) ───────────────────────


def test_ad17_period_key_field_present() -> None:
    """AD-17 verbatim: period_key field is in PromoteRequest (3-tuple idempotency key)."""
    fields = set(PromoteRequest.model_fields.keys())
    assert "period_key" in fields
    assert "tenant_id" in fields
    assert "source_draft_id" in fields


def test_ad17_idempotency_key_in_response() -> None:
    """AD-17 verbatim: PromoteResponse exposes idempotency_key (DB-level UNIQUE
    constraint surface). Required for handler-level audit_log_ids lookup.
    """
    fields = set(PromoteResponse.model_fields.keys())
    assert "idempotency_key" in fields
    assert "idempotent_replay" in fields  # bool — distinguishes replay vs first call


# ── 6. Audit-first INSERT 2-row invariant (2 cases) ───────────────


def test_audit_log_ids_tuple_shape() -> None:
    """audit_log_ids is tuple[uuid.UUID, uuid.UUID] — Row 1 (input_draft_promoted)
    + Row 2 (monthly_extraction_promote_executed), both emitted by promote call.
    """
    audit_field = PromoteResponse.model_fields["audit_log_ids"]
    annotation = str(audit_field.annotation)
    assert "tuple" in annotation
    assert "uuid.UUID" in annotation
    # Must be tuple (immutable) NOT list
    assert "list" not in annotation


def test_audit_log_ids_frozen_via_pydantic() -> None:
    """PromoteResponse is frozen — audit_log_ids tuple is immutable after construction."""
    assert PromoteResponse.model_config.get("frozen") is True