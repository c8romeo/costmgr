"""apps.api.modules.m10_ai.schemas — Pydantic request/response models.

Story 1.3 — Task 3.

Pydantic v2 models. Mirrored by `apps/web/lib/extraction-types.ts`
(drift caught by `tests/integration/test_extraction_parity.py`).

Layering note (AD-1):
- `apps.api.modules.m10_ai.schemas` is FastAPI-coupled (Pydantic + route
  I/O). The port in `packages.services.m10_ai.extraction_port` is
  pure stdlib. NEVER import from this module in the port or adapters.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── Request schemas ────────────────────────────────────────
class DocumentUploadRequest(BaseModel):
    """Body of `POST /api/v1/ai-documents`.

    The file bytes themselves travel as base64 in the JSON body. For
    MVP we don't use multipart/form-data — keeps the API surface
    uniform with the rest of the codebase (which is JSON-only).
    """

    model_config = ConfigDict(extra="forbid")

    mime_type: str = Field(..., description="application/pdf | image/png | image/jpeg | image/webp")
    filename: str = Field(..., min_length=1, max_length=255)
    document_b64: str = Field(..., description="base64-encoded document bytes")

    @field_validator("mime_type")
    @classmethod
    def _validate_mime(cls, v: str) -> str:
        # The service layer re-validates against ALLOWED_MIME; this is a
        # first-pass cheap check so 415 errors surface before we decode
        # the bytes.
        allowed = {"application/pdf", "image/png", "image/jpeg", "image/webp"}
        if v not in allowed:
            raise ValueError(f"mime_type must be one of {sorted(allowed)}")
        return v


# ── Response schemas ───────────────────────────────────────
class EvidenceResponse(BaseModel):
    page: int | None
    text: str
    bbox: list[float] | None = None


class DraftResponse(BaseModel):
    draft_id: uuid.UUID
    document_id: uuid.UUID
    field_name: str
    ai_value: dict[str, Any]
    confirmed_value: dict[str, Any] | None = None
    confidence: Decimal | None = None
    state: Literal["draft", "reviewed", "superseded"]
    evidence: EvidenceResponse
    version: int
    requested_at: datetime
    reviewed_at: datetime | None = None


class DocumentResponse(BaseModel):
    document_id: uuid.UUID
    tenant_id: uuid.UUID
    mime_type: str
    byte_size: int
    job_status: Literal["queued", "processing", "completed", "failed"]
    uploaded_at: datetime
    error_code: str | None = None
    error_message_ko: str | None = None
    drafts: list[DraftResponse] = Field(default_factory=list)


class DocumentSummary(BaseModel):
    """For list endpoint — no drafts to keep payload small."""

    document_id: uuid.UUID
    mime_type: str
    byte_size: int
    job_status: Literal["queued", "processing", "completed", "failed"]
    uploaded_at: datetime
    error_code: str | None = None


class DraftListResponse(BaseModel):
    drafts: list[DraftResponse]


class DraftUpdateRequest(BaseModel):
    """Body of `PATCH /api/v1/ai-drafts/{draft_id}`."""

    model_config = ConfigDict(extra="forbid")
    action: Literal["confirm", "reject"]
    confirmed_value: dict[str, Any] | None = None

    @field_validator("confirmed_value")
    @classmethod
    def _check_confirm_has_value(cls, v: dict[str, Any] | None, info: Any) -> dict[str, Any] | None:
        if info.data.get("action") == "confirm" and v is None:
            raise ValueError("confirmed_value is required when action='confirm'")
        return v


class OnboardingPromoteRequest(BaseModel):
    """Body of `POST /api/v1/ai-drafts/promote` (Story 1.3, renamed 10-4).

    Story 10.4 free the names `PromoteRequest` / `PromoteResponse` for the
    new `POST /api/v1/ai/promote` AD-17 verbatim input-draft promotion port.
    No wire/semantic change to the Story 1.3 endpoint; pure namespace
    uniquification (CR 12-1 immediately-sweep pattern).
    """

    model_config = ConfigDict(extra="forbid")
    document_id: uuid.UUID


class OnboardingPromoteResponse(BaseModel):
    document_id: uuid.UUID
    promoted_at: datetime
    fields: dict[str, Any]
    missing_optional: list[str]
    settings_version: int


# ── Story 10.1 EXTENSION: Monthly Input Extraction Schemas ──
# (cj-style Epic 10 2번째 진입점 wire, 2026-08-17)
#
# Pydantic v2 frozen models. Mirrored by `apps/web/lib/ai-extract.ts`
# (drift caught by `tests/integration/test_ai_extract_parity.py` — to be
# wired in Story 10-1 follow-up sprint D-10-1-DEFER-3 frontend tier).
#
# AD-7 verbatim: AI output → input_drafts only. Monthly extraction results
# NEVER write to `confirmed_inputs` (M10 → confirmed_inputs bypass → denied
# + counter increment; see handler envelope).


class MonthlyExtractRequest(BaseModel):
    """Body of `POST /api/v1/ai/extract-monthly`.

    6-stream monthly input extraction fields per master PRD §3.1
    (직접재료비/직접노무비/제조간접비/판매관리비/매출/기말재고).
    """

    model_config = ConfigDict(extra="forbid")

    period_key: str = Field(
        ...,
        min_length=1,
        max_length=32,
        description="YYYY-MM period (e.g. '2026-07')",
    )
    document_b64: str = Field(
        ...,
        description="base64-encoded document bytes (PDF or Excel)",
    )
    document_type: Literal["pdf", "xlsx"] = Field(
        ...,
        description="Document MIME family (PDF or Excel)",
    )


class MonthlyDraftResponse(BaseModel):
    """One AI-extracted monthly input draft row.

    `confidence` < 0.70 → RED badge (master PRD §8.1 M0-c 70% 임계값).
    `target_table` discriminator = 'monthly_inputs' (AD-7 strict invariant).
    """

    field_name: str
    value: Decimal
    confidence: Decimal
    target_table: Literal["monthly_inputs"] = "monthly_inputs"
    evidence_page: int | None = None
    requires_user_confirmation: bool


class MonthlyExtractResponse(BaseModel):
    """Body of `POST /api/v1/ai/extract-monthly` success envelope.

    Discriminated union pattern (CR 11-3 즉시 sweep 회피 pattern): the
    `status` tag discriminator lets the frontend narrow the response shape
    safely (`status='low_confidence_warning'` → user confirm flow required).
    """

    extraction_id: uuid.UUID
    period_key: str
    drafts: list[MonthlyDraftResponse]
    low_confidence_count: int
    status: Literal["success", "low_confidence_warning"] = "success"


class MonthlyExtractError(BaseModel):
    """Error envelope (CR 12-5 D-14 verbatim)."""

    error_code: Literal[
        "AI_PIPA_CONSENT_MISSING",
        "INVALID_MONTHLY_FIELD_VALUE",
        "MONTHLY_EXTRACTION_ERROR",
    ]
    message_ko: str
    trace_id: str


# ── Story 10.2 EXTENSION: Three-Insight Cache Schemas ──────
# (cj-style Epic 10 3번째 진입점 wire, 2026-08-17)
#
# Pydantic v2 frozen models. Discriminated union pattern:
# - `InsightEntry` carries insight_kind + source_kind tag discriminators
# - `InsightListResponse` success envelope with `status='success'` tag
# - `InsightCacheError` error envelope with error_code tag discriminator
#
# AD-15 cross-language parity SSOT:
# - Python: apps/api/modules/m10_ai/schemas.py (InsightEntry)
# - TS:     apps/web/lib/ai-insights.ts (InsightEntryTS) — honestly DEFER (d)
#
# AD-7 verbatim: 10-2 wire 진입 시점에 all 3 default insights are
# `source_kind='auto_analysis'`. `source_kind='ai_reference'` 추가는
# Story 10.3 wire 진입 시점에 detailed wire (badge separation).


class InsightEntry(BaseModel):
    """One AI insight entry returned by the M10 cache lookup.

    Discriminator fields:
      - insight_kind: Literal['cost_reduction_candidate', 'anomaly_pattern', 'forecast']
      - source_kind:  Literal['auto_analysis', 'ai_reference']
                      (10-2 wire 진입 시점: only 'auto_analysis' surfaced;
                       'ai_reference' 추가 wire는 Story 10.3 진입 시점)
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    insight_kind: Literal["cost_reduction_candidate", "anomaly_pattern", "forecast"]
    question: str
    answer: str
    source_kind: Literal["auto_analysis", "ai_reference"]
    evidence_ref: str | None = None
    generated_at: datetime


class InsightListResponse(BaseModel):
    """Body of `GET /api/v1/ai/insights` success envelope.

    Discriminated union tag discriminator `status='success'` lets the
    frontend narrow the response shape safely against `InsightCacheError`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    insights: list[InsightEntry]
    period_key: str
    calculation_result_hash: str
    hit_count: int
    miss_count: int
    status: Literal["success"] = "success"


class InsightCacheError(BaseModel):
    """Error envelope for `GET /api/v1/ai/insights` (CR 12-5 D-14 verbatim).

    Discriminator `error_code` covers:
      - AI_PIPA_CONSENT_MISSING     (403 — carry-over from 10-1)
      - INSIGHT_CACHE_KEY_ERROR     (422 — invalid period_key / hash format)
      - INSIGHT_COLD_COMPUTE_TIMEOUT (503 — NFR11 P95 ≤ 30s exceeded)
      - AI_INSIGHT_CACHE_CONTAMINATION (500 — cross-channel leakage)
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    error_code: Literal[
        "AI_PIPA_CONSENT_MISSING",
        "INSIGHT_CACHE_KEY_ERROR",
        "INSIGHT_COLD_COMPUTE_TIMEOUT",
        "AI_INSIGHT_CACHE_CONTAMINATION",
    ]
    message_ko: str
    details: dict[str, Any] = Field(default_factory=dict)
    trace_id: str


# ── Story 10.3 EXTENSION: AI Reference vs Auto Analysis Badge Schemas ──
# (cj-style Epic 10 4번째 진입점 wire, 2026-08-17)
#
# F10.2 (a)~(d) verbatim wire:
#   (a) source_kind='auto_analysis' → 파란 배지 '📊 자동 분석'
#       source_kind='ai_reference'  → 보라 배지 '🤖 AI 참고(검증 필요)'
#   (b) source_kind 미매칭 value → strict reject + 1행 counter increment
#   (c) auto_analysis 의견 수정 시도 → denied + 동일 카운터 추적 (SM-3a)
#   (d) 1-line ko-KR 메시지로 reject ("분석 의견 출처가 불분명합니다")
#
# Discriminated union pattern (CR 12-5 D-13/D-14 verbatim):
#   - `AICommentEntry` carries source_kind Literal tag discriminator
#   - `AICommentListResponse` success envelope with `status='success'` tag
#   - `AICommentError` discriminated union with error_code tag discriminator
#
# AD-15 cross-language parity SSOT (TS mirror:
# apps/web/lib/ai-comments.ts — honestly DEFER (d), A35 dedicated sprint).
#
# AD-7 verbatim: 10-3 wire 진입 시점에 3 auto_analysis + 1 ai_reference opinions
# surface. ai_reference async LLM generation pipeline is honestly DEFER (b)
# retro input — seed 1 row with deterministic Korean body for shape verification.


class AICommentEntry(BaseModel):
    """One AI comment entry returned by the M10 comment lookup.

    Discriminator fields:
      - comment_kind:  Literal['cost_reduction_candidate', 'anomaly_pattern',
                                'forecast', 'risk_warning', 'industry_benchmark']
                       (master PRD §12 + 10-3 forward-fill 2 kinds)
      - source_kind:   Literal['auto_analysis', 'ai_reference']
                       (F10.2-(a) verbatim: badge 결정자)
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    comment_id: uuid.UUID
    comment_kind: Literal[
        "cost_reduction_candidate",
        "anomaly_pattern",
        "forecast",
        "risk_warning",
        "industry_benchmark",
    ]
    body_text: str
    source_kind: Literal["auto_analysis", "ai_reference"]
    evidence_ref: str | None = None
    generated_at: datetime


class AICommentListResponse(BaseModel):
    """Body of `GET /api/v1/ai/comments` success envelope.

    Discriminated union tag discriminator `status='success'` lets the
    frontend narrow the response shape safely against `AICommentError`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    comments: list[AICommentEntry]
    period_key: str
    calculation_result_hash: str
    hit_count: int
    miss_count: int
    counter_total: int
    status: Literal["success"] = "success"


class AICommentError(BaseModel):
    """Error envelope for `GET /api/v1/ai/comments` (CR 12-5 D-14 verbatim).

    Discriminator `error_code` covers:
      - AI_PIPA_CONSENT_MISSING            (403 — carry-over from 10-1/10-2)
      - AI_COMMENT_SOURCE_KIND_INVALID     (422 — F10.2-(b) strict reject)
      - AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS (422 — F10.2-(c) modify deny)
      - AI_COMMENT_SOURCE_KIND_WARNING     (200 — F10.2-(d) 1-line ko-KR
                                                          warning envelope)
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    error_code: Literal[
        "AI_PIPA_CONSENT_MISSING",
        "AI_COMMENT_SOURCE_KIND_INVALID",
        "AI_COMMENT_IMMUTABLE_AUTO_ANALYSIS",
        "AI_COMMENT_SOURCE_KIND_WARNING",
    ]
    message_ko: str
    details: dict[str, Any] = Field(default_factory=dict)
    trace_id: str


# ──────────────────────────────────────────────────────────────────────
# Story 10.4 EXTENSION: AI Promotion Port Schemas
# (cj-style Epic 10 5번째 진입점 wire, 2026-08-18)
#
# AD-17 verbatim invariants:
#   - Only M2 may call `InputPromoter.promote(tenant_id, period_key,
#     source_draft_id)` → MonthlyInput
#   - Idempotent on (tenant_id, period_key, source_draft_id) 3-tuple via
#     UNIQUE constraint + state='promoted' 1회 전이 (no replay beyond that)
#   - Audit-first INSERT 2행 append (CR 1.1 verbatim):
#     Row 1: action_class=INPUT_DRAFT, action=input_draft_promoted (NEW)
#     Row 2: action_class=AI_EXTRACTION_EXECUTED,
#            action=monthly_extraction_promote_executed (NEW)
#   - Canonical 6-stream shape (master PRD §3.1: 직접재료비/직접노무비/
#     제조간접비/판매관리비/매출/기말재고) from `input_drafts.confirmed_value`
#     JSONB.
#
# AD-7 strict invariant: M10 NEVER writes `confirmed_inputs` /
# `monthly_input_rows` except via the canonical `InputPromoter.promote(...)`
# path. Direct INSERT attempts are rejected with 422 INPUT_PROMOTION_DENIED +
# `monthly_extraction_promote_denied` counter increment (10-1 forward-fill
# audit_logs slot — AD-25 cross-channel counter).
#
# Discriminated union envelope pattern with `status` tag discriminator
# (CR 12-5 D-13 verbatim — `status` is the Pydantic v2 discriminator field):
#   `PromoteResponse | PromoteDraftImmutableError | ... | AiPipaConsentMissingError`
#
# `status` discriminator values (each envelope carries exactly one literal):
#   - "success"                 → PromoteResponse (200)
#   - "draft_immutable"         → PromoteDraftImmutableError (409)
#   - "source_draft_not_found"  → PromoteSourceDraftNotFoundError (404)
#   - "idempotency_mismatch"    → PromoteIdempotencyMismatchError (422)
#   - "m2_only"                 → PromoteM2OnlyError (403, AD-17 verbatim)
#   - "pipa_consent_missing"    → AiPipaConsentMissingError (403, D-10-3-DEFER-6)
#   - "promotion_denied"        → InputPromotionDeniedError (422, AD-7 guard)
#
# AD-15 cross-language parity SSOT:
#   Python: apps/api/modules/m10_ai/schemas.py (this file)
#   TS:     apps/web/lib/ai-promote.ts (honestly DEFER (d), A35 dedicated sprint)
#
# Pre-existing `PromoteRequest` / `PromoteResponse` (Story 1.3
# onboarding drafts → company info subblock) renamed to
# `OnboardingPromoteRequest` / `OnboardingPromoteResponse` to free the
# names for the new AD-17 spec verbatim envelopes. No semantic change to
# the Story 1.3 endpoint; pure namespace uniquification
# (CR 12-1 immediately-sweep pattern).
# ──────────────────────────────────────────────────────────────────────


class PromoteRequest(BaseModel):
    """Body of `POST /api/v1/ai/promote` (Story 10.4 spec verbatim, AC #4).

    AD-17 verbatim: only M2 may call `InputPromoter.promote(...)`. `actor_id`
    is the M2 service-role actor (synthetic identifier emitted by M2 module
    authority). HTTP-layer M2-only check (`get_current_m2_user` capability
    gate) validates the caller's role membership in `m2_service_role`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    tenant_id: uuid.UUID = Field(
        ...,
        description="Tenant scope (AD-22 + CR 1.1 audit baseline)",
    )
    period_key: str = Field(
        ...,
        min_length=1,
        max_length=32,
        description="YYYY-MM period key (master PRD §V4 format, e.g. '2026-07')",
    )
    source_draft_id: uuid.UUID = Field(
        ...,
        description="input_drafts.draft_id row to promote (AD-7 strict invariant target)",
    )
    confirmed_value_hash: str | None = Field(
        default=None,
        max_length=256,
        description=(
            "Hex-encoded SHA-256 of `input_drafts.confirmed_value` "
            "(optional integrity check; AD-17 idempotency 3-tuple anchor)"
        ),
    )
    actor_id: uuid.UUID = Field(
        ...,
        description="M2 service-role actor_id (synthetic; AD-17 verbatim only M2 may call)",
    )


class PromoteResponse(BaseModel):
    """Body of `POST /api/v1/ai/promote` success envelope (AC #5 verbatim).

    Discriminator `status='success'` distinguishes from error envelopes. The
    `audit_log_ids` tuple carries the audit-first INSERT 2-row UUIDs
    (Row 1: INPUT_DRAFT/input_draft_promoted + Row 2: AI_EXTRACTION_EXECUTED/
    monthly_extraction_promote_executed, in order).

    `idempotent_replay=True` indicates the call replayed an existing
    promotion (3-tuple match) without re-emitting new audit rows —
    the prior `monthly_input_promotions` row is returned as-is.

    `promotion_id` and `idempotency_key` mirror the kernel
    `PromotionResult` wire contract (T1) so the HTTP surface stays
    1:1 with the port contract (AD-15 cross-language parity SSOT).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["success"] = "success"
    tenant_id: uuid.UUID
    period_key: str
    source_draft_id: uuid.UUID
    promotion_id: uuid.UUID = Field(
        ...,
        description=(
            "monthly_input_promotions.promotion_id PRIMARY KEY (mirror of "
            "kernel PromotionResult.promotion_id — AD-15 parity SSOT)"
        ),
    )
    idempotency_key: uuid.UUID = Field(
        ...,
        description=(
            "UUID v5 derivation of 3-tuple (kernel PromotionResult.idempotency_key — "
            "AD-17 verbatim 3-tuple anchor + AD-15 parity SSOT)"
        ),
    )
    confirmed_input_row_id: uuid.UUID = Field(
        ...,
        description=(
            "monthly_input_rows.id PRIMARY KEY (AD-7 strict invariant target — "
            "service INSERTs into monthly_input_rows ONLY via this path)"
        ),
    )
    promoted_at: datetime
    draft_hash: bytes = Field(
        ...,
        description="SHA-256 of the promoted draft content (idempotency anchor + audit linkage)",
    )
    idempotent_replay: bool = Field(
        ...,
        description="True if 3-tuple idempotency replay (no new audit rows emitted this call)",
    )
    audit_log_ids: tuple[uuid.UUID, uuid.UUID] = Field(
        ...,
        description=(
            "Audit-first INSERT 2 row UUIDs (Row 1 + Row 2). Tuple enforces "
            "fixed-length exactly 2 elements per audit-first invariant."
        ),
    )


# ── Story 10.4 error envelopes (CR 12-5 D-14 verbatim wire shape
# `{status, code, message_ko, details, trace_id}` — `status` is the
# discriminated-union tag discriminator) ──


class PromoteDraftImmutableError(BaseModel):
    """409 PROMOTE_DRAFT_IMMUTABLE — source_draft already in 'promoted' state.

    AD-17 verbatim 1회 전이: once a draft transitions to state='promoted',
    no further promote attempts on the same `draft_id` are accepted. The
    3-tuple `(tenant_id, period_key, source_draft_id)` UNIQUE on
    `monthly_input_promotions` enforces this at the DB layer; the
    service-layer state check + this envelope are defense-in-depth.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["draft_immutable"] = "draft_immutable"
    code: Literal["PROMOTE_DRAFT_IMMUTABLE"] = "PROMOTE_DRAFT_IMMUTABLE"
    message_ko: str
    details: dict[str, Any] = Field(default_factory=dict)
    trace_id: str


class PromoteSourceDraftNotFoundError(BaseModel):
    """404 PROMOTE_SOURCE_DRAFT_NOT_FOUND — tenant-scoped `source_draft_id` missing.

    Service-layer SELECT enforces `input_drafts.tenant_id = ctx.tenant_id`
    before promoting. Cross-tenant `source_draft_id` is rejected as
    not-found (NOT 403 — tenant isolation is invisible to caller).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["source_draft_not_found"] = "source_draft_not_found"
    code: Literal["PROMOTE_SOURCE_DRAFT_NOT_FOUND"] = "PROMOTE_SOURCE_DRAFT_NOT_FOUND"
    message_ko: str
    details: dict[str, Any] = Field(default_factory=dict)
    trace_id: str


class PromoteIdempotencyMismatchError(BaseModel):
    """422 PROMOTE_IDEMPOTENCY_MISMATCH — same 3-tuple called with different value hash.

    AD-17 verbatim idempotency: a 3-tuple replay MUST use the same
    `confirmed_value_hash`. If the new call carries a different hash,
    the service rejects (the original promotion stays intact and
    idempotent on subsequent same-hash replays).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["idempotency_mismatch"] = "idempotency_mismatch"
    code: Literal["PROMOTE_IDEMPOTENCY_MISMATCH"] = "PROMOTE_IDEMPOTENCY_MISMATCH"
    message_ko: str
    details: dict[str, Any] = Field(default_factory=dict)
    trace_id: str


class PromoteM2OnlyError(BaseModel):
    """403 INPUT_PROMOTION_M2_ONLY — AD-17 verbatim only M2 may call.

    HTTP-layer enforcement: `get_current_m2_user` capability gate
    (T4.3 capability.py EXTENSION) verifies the caller carries
    `m2_service_role` in their authenticated session roles. The
    kernel-side `validate_promotion_request` re-checks the
    `actor_role='m2_service_role'` Literal in the request payload
    as a defense-in-depth audit anchor.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["m2_only"] = "m2_only"
    code: Literal["INPUT_PROMOTION_M2_ONLY"] = "INPUT_PROMOTION_M2_ONLY"
    message_ko: str
    details: dict[str, Any] = Field(default_factory=dict)
    trace_id: str


class AiPipaConsentMissingError(BaseModel):
    """403 AI_PIPA_CONSENT_MISSING — PIPA consent missing at promote time.

    D-10-3-DEFER-6 PIPA gate 4 endpoints carry-over 해소 verification:
    this envelope is now reachable on `POST /api/v1/ai/promote` in
    addition to 10-1's `/ai/extract-monthly`, 10-2's `/ai/insights`,
    and 10-3's `/ai/comments`. All 4 endpoints share the
    `Depends(require_pipa_review)` dependency, so a single
    `PipaConsentMissingError` → 403 AI_PIPA_CONSENT_MISSING mapping
    fires uniformly across the AI surface.

    Name `AiPipaConsentMissingError` is verbatim from the 10-4 spec;
    the Pydantic envelope coexists with the Python exception of the
    same name (defined in `apps.api.modules.m10_ai.service`) by virtue
    of living in a different module. `handlers.py` disambiguates via
    `import ... as AiPipaConsentMissingEnvelope` for the schemas-side
    Pydantic model.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["pipa_consent_missing"] = "pipa_consent_missing"
    code: Literal["AI_PIPA_CONSENT_MISSING"] = "AI_PIPA_CONSENT_MISSING"
    message_ko: str
    details: dict[str, Any] = Field(default_factory=dict)
    trace_id: str


class InputPromotionDeniedError(BaseModel):
    """422 INPUT_PROMOTION_DENIED — AD-7 strict invariant guard.

    Service-layer defense-in-depth: M10 service attempting direct INSERT
    into `confirmed_inputs` / `monthly_input_rows` outside the canonical
    `InputPromoter.promote(...)` path is rejected. The
    `monthly_extraction_promote_denied` counter is incremented
    (10-1 forward-fill slot — audit_logs counter via
    `monthly_extraction_promote_denied`) and a 1-row audit INSERT is
    emitted (action_class=AI_EXTRACTION_EXECUTED,
    action=monthly_extraction_promote_denied carry-over from 10-1).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["promotion_denied"] = "promotion_denied"
    code: Literal["INPUT_PROMOTION_DENIED"] = "INPUT_PROMOTION_DENIED"
    message_ko: str
    details: dict[str, Any] = Field(default_factory=dict)
    trace_id: str


# ── Discriminated union (CR 12-5 D-13 verbatim `status` tag discriminator)
# `status` field on each envelope carries a unique Literal value; Pydantic v2
# uses it for OpenAPI schema discrimination AND for runtime serialization
# branch resolution.
PromoteEnvelope = Annotated[
    Union[
        PromoteResponse,
        PromoteDraftImmutableError,
        PromoteSourceDraftNotFoundError,
        PromoteIdempotencyMismatchError,
        PromoteM2OnlyError,
        AiPipaConsentMissingError,
        InputPromotionDeniedError,
    ],
    Field(discriminator="status"),
]
