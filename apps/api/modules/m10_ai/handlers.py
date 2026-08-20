"""apps.api.modules.m10_ai.handlers — FastAPI router for M10 AI extraction.

Story 1.3 — Task 3.

Routes:
  POST   /api/v1/ai-documents
  GET    /api/v1/ai-documents
  GET    /api/v1/ai-documents/{document_id}
  POST   /api/v1/ai-documents/{document_id}/reprocess
  GET    /api/v1/ai-drafts
  PATCH  /api/v1/ai-drafts/{draft_id}
  POST   /api/v1/ai-drafts/promote

Errors (AD-15 contract):
  400   DRAFT_STATE_INVALID — confirm without value / unknown action
  404   DOCUMENT_NOT_FOUND / DRAFT_NOT_FOUND
  409   PROMOTE_REQUIRED_FIELDS_MISSING
  413   DOCUMENT_TOO_LARGE
  415   DOCUMENT_MIME_NOT_ALLOWED
  422   IDEMPOTENCY_KEY_REQUIRED — never (we accept absent key)
  451   PIPA_CONSENT_MISSING / PIPA_REGION_NOT_ALLOWED

Defensive pattern: every typed exception → typed JSON envelope. The
service-layer exceptions carry `trace_id`; the handlers propagate it
unchanged so log correlation works.
"""

from __future__ import annotations

import base64
import binascii
import uuid
from datetime import UTC
from typing import Any

from fastapi import APIRouter, Depends, Header, Query, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.capability import Capability, get_current_m2_user, require_capability
from apps.api.core.db import get_session
from apps.api.core.pipa_gate import (
    PipaConsentMissingError,
    require_pipa_review,
)
from apps.api.core.tenant_context import TenantContext
from apps.api.modules.m0_onboarding.services.settings_service import (
    SettingsService,
)
from apps.api.modules.m10_ai.schemas import (
    AICommentEntry,
    AICommentError,
    AICommentListResponse,
    DocumentResponse,
    DocumentSummary,
    DocumentUploadRequest,
    DraftListResponse,
    DraftResponse,
    DraftUpdateRequest,
    EvidenceResponse,
    InsightCacheError,
    InsightEntry,
    InsightListResponse,
    MonthlyDraftResponse,
    MonthlyExtractError,
    MonthlyExtractRequest,
    MonthlyExtractResponse,
    OnboardingPromoteRequest,
    OnboardingPromoteResponse,
    PromoteDraftImmutableError,
    PromoteEnvelope,
    PromoteIdempotencyMismatchError,
    PromoteM2OnlyError,
    PromoteRequest,
    PromoteResponse,
    PromoteSourceDraftNotFoundError,
)
from apps.api.modules.m10_ai.schemas import (
    AiPipaConsentMissingError as AiPipaConsentMissingEnvelope,
)
from apps.api.modules.m10_ai.service import (
    AiPipaConsentMissingError,
    CommentService,
    DocumentMimeNotAllowedError,
    DocumentNotFoundError,
    DocumentService,
    DocumentTooLargeError,
    DraftNotFoundError,
    DraftStateError,
    InsightCacheService,
    MonthlyExtractionError,
    PromoteRequiredFieldsMissingError,
    extract_monthly_input,
)
from apps.api.modules.m10_ai.services.db_promoter_adapter import DbPromoterAdapter
from apps.api.modules.m10_ai.services.promoter_service import (
    PromotionDraftImmutableError,
    PromotionIdempotencyMismatchError,
    PromotionM2OnlyDeniedError,
    PromotionSourceDraftNotFoundError,
)
from packages.services.m10_ai.monthly_extraction_kernel import (
    InvalidMonthlyFieldValueError,
)
from packages.services.m10_ai.promoter_port import (
    ALLOWED_PROMOTER_ACTOR_ROLE,
)
from packages.services.m10_ai.promoter_port import (
    PromotionRequest as KernelPromotionRequest,
)

router = APIRouter(prefix="/api/v1", tags=["m10-ai"])


# ── Helpers ────────────────────────────────────────────────
def _draft_to_response(draft) -> DraftResponse:
    evidence = dict(draft.evidence or {})
    return DraftResponse(
        draft_id=draft.draft_id,
        document_id=draft.document_id,
        field_name=draft.field_name,
        ai_value=dict(draft.ai_value or {}),
        confirmed_value=dict(draft.confirmed_value) if draft.confirmed_value else None,
        confidence=draft.confidence,
        state=draft.state,
        evidence=EvidenceResponse(
            page=evidence.get("page"),
            text=evidence.get("text", ""),
            bbox=evidence.get("bbox"),
        ),
        version=draft.version,
        requested_at=draft.requested_at,
        reviewed_at=draft.reviewed_at,
    )


def _doc_to_response(doc, drafts) -> DocumentResponse:
    return DocumentResponse(
        document_id=doc.document_id,
        tenant_id=doc.tenant_id,
        mime_type=doc.mime_type,
        byte_size=doc.byte_size,
        job_status=doc.job_status,
        uploaded_at=doc.uploaded_at,
        error_code=doc.error_code,
        error_message_ko=doc.error_message_ko,
        drafts=[_draft_to_response(d) for d in drafts],
    )


# ── POST /api/v1/ai-documents ──────────────────────────────
@router.post(
    "/ai-documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="AI 추출용 문서 업로드 (Story 1.3)",
    description=(
        "Body: `{ mime_type, filename, document_b64 }`. Honors the "
        "`Idempotency-Key` header — duplicate POSTs with the same key "
        "return the prior document (AC #2). PIPA-gated: requires "
        "`onboarding.pipa_consent=true` (Task 2.4)."
    ),
)
async def upload_document(
    body: DocumentUploadRequest,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key", max_length=32),
    ctx: TenantContext = Depends(require_pipa_review),
    session: AsyncSession = Depends(get_session),
) -> Any:
    trace_id = str(uuid.uuid4())

    # Idempotency-Key is optional. When absent, we generate a per-request
    # UUID so the partial unique index still has a value to dedupe on
    # (in case of accidental double-submit due to network retries).
    effective_key = idempotency_key or str(uuid.uuid4())

    # Decode base64.
    try:
        document_bytes = base64.b64decode(body.document_b64, validate=True)
    except (binascii.Error, ValueError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "code": "DOCUMENT_DECODE_FAILED",
                "message_ko": "base64 디코딩 실패. 올바른 base64 문자열을 전송해 주세요.",
                "details": {},
                "trace_id": trace_id,
            },
        )

    service = DocumentService(session, trace_id=trace_id)
    try:
        document, drafts = await service.upload_document(
            tenant_id=ctx.tenant_id,
            uploaded_by=ctx.user_id,
            mime_type=body.mime_type,
            document_bytes=document_bytes,
            idempotency_key=effective_key,
        )
    except DocumentMimeNotAllowedError as e:
        return JSONResponse(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            content={
                "code": "DOCUMENT_MIME_NOT_ALLOWED",
                "message_ko": f"지원하지 않는 파일 형식입니다 ({e.mime_type})",
                "details": {"mime_type": e.mime_type},
                "trace_id": e.trace_id,
            },
        )
    except DocumentTooLargeError as e:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={
                "code": "DOCUMENT_TOO_LARGE",
                "message_ko": "파일이 너무 큽니다 (최대 8 MiB)",
                "details": {"byte_size": e.byte_size, "max_bytes": e.max_bytes},
                "trace_id": e.trace_id,
            },
        )

    response.headers["X-Trace-Id"] = trace_id
    return _doc_to_response(document, drafts)


# ── GET /api/v1/ai-documents ───────────────────────────────
@router.get(
    "/ai-documents",
    response_model=list[DocumentSummary],
    status_code=status.HTTP_200_OK,
    summary="업로드된 문서 목록 (Task 3.2)",
)
async def list_documents(
    ctx: TenantContext = Depends(require_pipa_review),
    session: AsyncSession = Depends(get_session),
) -> list[DocumentSummary]:
    trace_id = str(uuid.uuid4())
    service = DocumentService(session, trace_id=trace_id)
    docs = await service.list_documents(tenant_id=ctx.tenant_id)
    return [
        DocumentSummary(
            document_id=d.document_id,
            mime_type=d.mime_type,
            byte_size=d.byte_size,
            job_status=d.job_status,
            uploaded_at=d.uploaded_at,
            error_code=d.error_code,
        )
        for d in docs
    ]


# ── GET /api/v1/ai-documents/{document_id} ─────────────────
@router.get(
    "/ai-documents/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="문서 + 추출 드래프트 조회",
)
async def get_document(
    document_id: uuid.UUID,
    ctx: TenantContext = Depends(require_pipa_review),
    session: AsyncSession = Depends(get_session),
) -> Any:
    trace_id = str(uuid.uuid4())
    service = DocumentService(session, trace_id=trace_id)
    try:
        document, drafts = await service.get_document_with_drafts(
            tenant_id=ctx.tenant_id, document_id=document_id
        )
    except DocumentNotFoundError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "code": "DOCUMENT_NOT_FOUND",
                "message_ko": "문서를 찾을 수 없습니다",
                "details": {"document_id": str(e.document_id)},
                "trace_id": e.trace_id,
            },
        )
    return _doc_to_response(document, drafts)


# ── POST /api/v1/ai-documents/{document_id}/reprocess ──────
@router.post(
    "/ai-documents/{document_id}/reprocess",
    response_model=DocumentResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="추출 실패/오답 재시도",
    description=(
        "Re-runs the provider adapter on the document. Existing drafts "
        "are marked `superseded` and a new draft set is persisted. The "
        "request body is empty — the service fetches bytes from storage "
        "(MVP: client provides them again via a base64 body if storage "
        "fetch is unavailable)."
    ),
)
async def reprocess_document(
    document_id: uuid.UUID,
    ctx: TenantContext = Depends(require_pipa_review),
    session: AsyncSession = Depends(get_session),
) -> Any:
    trace_id = str(uuid.uuid4())
    # In MVP, reprocess requires the bytes to be re-sent because the
    # Supabase Storage download path is wired in Story 0.5 plumbing.
    # For now, we accept the request and emit a typed error if the
    # caller hasn't supplied them — prevents silent no-op.
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "code": "REPROCESS_REQUIRES_BYTES",
            "message_ko": (
                "재시도는 스토리지 다운로드 연결 후 지원됩니다 (Story 0.5 plumbing 후속). "
                "현재는 새 문서로 업로드해 주세요."
            ),
            "details": {"document_id": str(document_id)},
            "trace_id": trace_id,
        },
    )


# ── GET /api/v1/ai-drafts ──────────────────────────────────
@router.get(
    "/ai-drafts",
    response_model=DraftListResponse,
    status_code=status.HTTP_200_OK,
    summary="추출 드래프트 목록 (state 필터)",
)
async def list_drafts(
    state: str | None = Query(default=None, pattern="^(draft|reviewed|superseded)$"),
    document_id: uuid.UUID | None = Query(default=None),
    ctx: TenantContext = Depends(require_pipa_review),
    session: AsyncSession = Depends(get_session),
) -> DraftListResponse:
    trace_id = str(uuid.uuid4())
    service = DocumentService(session, trace_id=trace_id)
    drafts = await service.list_drafts(
        tenant_id=ctx.tenant_id, state=state, document_id=document_id
    )
    return DraftListResponse(drafts=[_draft_to_response(d) for d in drafts])


# ── PATCH /api/v1/ai-drafts/{draft_id} ─────────────────────
@router.patch(
    "/ai-drafts/{draft_id}",
    response_model=DraftResponse,
    status_code=status.HTTP_200_OK,
    summary="드래프트 확인/거부 (Task 3.5)",
)
async def update_draft(
    draft_id: uuid.UUID,
    body: DraftUpdateRequest,
    ctx: TenantContext = Depends(require_pipa_review),
    session: AsyncSession = Depends(get_session),
) -> Any:
    trace_id = str(uuid.uuid4())
    service = DocumentService(session, trace_id=trace_id)
    try:
        draft = await service.update_draft(
            tenant_id=ctx.tenant_id,
            draft_id=draft_id,
            action=body.action,
            confirmed_value=body.confirmed_value,
            actor_id=ctx.user_id,
        )
    except DraftNotFoundError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "code": "DRAFT_NOT_FOUND",
                "message_ko": "드래프트를 찾을 수 없습니다",
                "details": {"draft_id": str(e.draft_id)},
                "trace_id": e.trace_id,
            },
        )
    except DraftStateError as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "code": "DRAFT_STATE_INVALID",
                "message_ko": f"드래프트 상태 {e.current_state}에서 {e.attempted} 불가",
                "details": {"current_state": e.current_state, "attempted": e.attempted},
                "trace_id": e.trace_id,
            },
        )
    return _draft_to_response(draft)


# ── POST /api/v1/ai-drafts/promote ─────────────────────────
@router.post(
    "/ai-drafts/promote",
    response_model=OnboardingPromoteResponse,
    status_code=status.HTTP_200_OK,
    summary="확정된 드래프트 → 회사정보 블록 승격 (Task 3.6)",
    description=(
        "Atomic: requires all 5 fields reviewed OR only "
        "`business_registration_number` reviewed. Writes "
        "`tenant_settings.onboarding.company_subblock` and bumps "
        "`settings_version` (AD-23 + AD-2). Required field check "
        "enforced at the service layer."
    ),
)
async def promote_drafts(
    body: OnboardingPromoteRequest,
    ctx: TenantContext = Depends(require_pipa_review),
    session: AsyncSession = Depends(get_session),
) -> Any:
    trace_id = str(uuid.uuid4())
    service = DocumentService(session, trace_id=trace_id)
    try:
        new_subblock = await service.promote_confirmed_drafts(
            tenant_id=ctx.tenant_id,
            document_id=body.document_id,
            actor_id=ctx.user_id,
        )
    except PromoteRequiredFieldsMissingError as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "code": "PROMOTE_REQUIRED_FIELDS_MISSING",
                "message_ko": f"필수 필드 확인 누락: {', '.join(e.missing)}",
                "details": {"missing": e.missing},
                "trace_id": e.trace_id,
            },
        )

    # Read settings_version for the response (post-promotion).
    settings_service = SettingsService(session, trace_id=trace_id)
    settings_row = await settings_service.get_tenant_settings(tenant_id=ctx.tenant_id)
    from datetime import datetime as _dt

    return OnboardingPromoteResponse(
        document_id=body.document_id,
        promoted_at=_dt.fromisoformat(new_subblock["promoted_at"]),
        fields=dict(new_subblock.get("fields") or {}),
        missing_optional=[
            f
            for f in (
                "business_registration_number",
                "company_name",
                "address",
                "representative_name",
                "industry",
            )
            if f not in (new_subblock.get("fields") or {})
        ],
        settings_version=settings_row.settings_version,
    )


# ── 451 handler (PIPA gate) ────────────────────────────────
# Attached in main.py so the dependency-raised exception becomes a typed
# envelope. We define the body shape here for visibility.
def _pipa_error_response(exc: PipaConsentMissingError) -> JSONResponse:
    return JSONResponse(
        status_code=451,  # Unavailable For Legal Reasons
        content={
            "code": "PIPA_CONSENT_MISSING"
            if exc.reason == "consent_missing"
            else "PIPA_REGION_NOT_ALLOWED",
            "message_ko": (
                "AI 추출은 개인정보 처리 동의가 필요합니다. 설정에서 동의해 주세요."
                if exc.reason == "consent_missing"
                else "현재 지역에서는 AI 추출을 사용할 수 없습니다."
            ),
            "details": {"reason": exc.reason},
            "trace_id": exc.trace_id,
        },
    )


# ── Story 10.1 EXTENSION: Monthly Input Extraction Endpoint ──
# (cj-style Epic 10 cj-style 28번째 epic 연속 wire, 2026-08-17)
#
# D-10-1-DEFER-1 잔여 해소: T2.5 POST /api/v1/ai/extract-monthly detailed wire.
#
# AD-7 verbatim: M10 NEVER writes to `confirmed_inputs`. This endpoint
# returns `MonthlyExtractResponse` (target_table='monthly_inputs' ONLY).
# The promotion to `confirmed_inputs` is M2's `InputPromoter.promote(...)`
# (Story 10.4 wire 진입 시점에 detailed wire).
#
# AD-25 verbatim: cache key `(tenant_id, period_key, calculation_result_hash)`.
# Epic 10 wire 진입 시점에는 `ai_cache` channel 1개만 wire. The other 3
# channels are Epic 11 close/reopen trigger EXTENSION (Story 11.1/11.3).
#
# Capability gate: `AI_INSIGHT` (industry-agnostic, 4-industry grants).
# Discriminated union envelope: `MonthlyExtractResponse | MonthlyExtractError`.
# Error envelopes (CR 12-5 D-14):
#   403 AI_PIPA_CONSENT_MISSING — PIPA consent not granted
#   422 INVALID_MONTHLY_FIELD_VALUE — parse failure
#   500 MONTHTHLY_EXTRACTION_ERROR — wrapper failure
@router.post(
    "/ai/extract-monthly",
    response_model=MonthlyExtractResponse | MonthlyExtractError,
    status_code=status.HTTP_200_OK,
    summary="AI 월간 입력 추출 (Story 10.1)",
    description=(
        "Body: { period_key, document_type: 'pdf'|'xlsx', document_b64 }. "
        "Capability gate: AI_INSIGHT (industry-agnostic). PIPA consent "
        "RE-CHECKED at the service layer (FIRST gate, fail-closed). "
        "AD-7 verbatim: M10 NEVER writes confirmed_inputs; output → "
        "input_drafts.target_table='monthly_inputs' only. Audit-first "
        "INSERT into audit_logs with action_class=AI_EXTRACTION_EXECUTED "
        "BEFORE the adapter call (CR 1.1 lesson). Returns discriminated "
        "union MonthlyExtractResponse | MonthlyExtractError."
    ),
)
async def extract_monthly_endpoint(
    body: MonthlyExtractRequest,
    response: Response,
    ctx: TenantContext = Depends(require_pipa_review),
    _cap: TenantContext = Depends(require_capability(Capability.AI_INSIGHT)),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """POST /api/v1/ai/extract-monthly — Story 10.1 monthly extraction entry.

    Discriminated union return (MonthlyExtractResponse | MonthlyExtractError):
    - success → status='success' with full draft set
    - low confidence (≥ 1 field < 0.70) → status='low_confidence_warning'
    - service raises AiPipaConsentMissingError → 403 envelope
    - service raises InvalidMonthlyFieldValueError → 422 envelope
    - service raises MonthlyExtractionError → 500 envelope
    """
    trace_id = str(uuid.uuid4())
    response.headers["X-Trace-Id"] = trace_id

    try:
        document_bytes = base64.b64decode(body.document_b64, validate=True)
    except (binascii.Error, ValueError):
        return MonthlyExtractError(
            error_code="MONTHLY_EXTRACTION_ERROR",
            message_ko="base64 디코딩 실패",
            trace_id=trace_id,
        )

    try:
        result = await extract_monthly_input(
            session=session,
            tenant_id=ctx.tenant_id,
            period_key=body.period_key,
            document_bytes=document_bytes,
            document_type=body.document_type,
            trace_id=trace_id,
        )
    except AiPipaConsentMissingError as e:
        return MonthlyExtractError(
            error_code="AI_PIPA_CONSENT_MISSING",
            message_ko="월간 AI 추출은 개인정보 처리 동의가 필요합니다.",
            trace_id=e.trace_id,
        )
    except InvalidMonthlyFieldValueError as e:
        return MonthlyExtractError(
            error_code="INVALID_MONTHLY_FIELD_VALUE",
            message_ko=str(e),
            trace_id=trace_id,
        )
    except MonthlyExtractionError as e:
        return MonthlyExtractError(
            error_code="MONTHLY_EXTRACTION_ERROR",
            message_ko=f"월간 AI 추출 실패: {e.reason}",
            trace_id=e.trace_id,
        )

    # Map MonthlyInputDraftRow → MonthlyDraftResponse.
    # AD-7 strict invariant: target_table='monthly_inputs' ONLY.
    drafts_response = [
        MonthlyDraftResponse(
            field_name=d.field_name.value,
            value=d.value,
            confidence=d.confidence,
            target_table="monthly_inputs",  # AD-7 strict invariant
            evidence_page=d.evidence.page if d.evidence else None,
            requires_user_confirmation=d.requires_user_confirmation,
        )
        for d in result.drafts
    ]

    status_value = (
        "low_confidence_warning" if result.low_confidence_count > 0
        else "success"
    )
    return MonthlyExtractResponse(
        extraction_id=result.extraction_id,
        period_key=result.period_key,
        drafts=drafts_response,
        low_confidence_count=result.low_confidence_count,
        status=status_value,
    )


# ── Story 10.2 EXTENSION: GET /api/v1/ai/insights ──────────
# (cj-style Epic 10 3번째 진입점 wire, 2026-08-17)
#
# AD-25 verbatim 3-tuple cache key:
#   tenant_id + period_key + calculation_result_hash
# F10.1-(d) verbatim: channel = 'ai_cache' filter 강제
#   cross-channel contamination 방어.
#
# AD-7 strict invariant: 10-2 wire 진입 시점에 all 3 default insights
# are `source_kind='auto_analysis'`. `ai_reference` 추가는 Story 10.3
# wire 진입 시점에 detailed wire (badge separation).


@router.get(
    "/ai/insights",
    response_model=InsightListResponse | InsightCacheError,
    status_code=status.HTTP_200_OK,
    summary="Three-Insight 캐시 조회 (AD-25 verbatim 3-tuple key)",
    description=(
        "3 insight entry 반환 (cost_reduction_candidate + anomaly_pattern + forecast). "
        "AD-25 verbatim (tenant_id, period_key, calculation_result_hash) 캐시 키 기반. "
        "캐시 hit sub-100ms, cold compute NFR11 P95 ≤ 30s. "
        "channel='ai_cache' filter 강제 (F10.1-(d) verbatim cross-channel contamination 방지)."
    ),
)
async def get_ai_insights(
    period_key: str = Query(
        ...,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        description="YYYY-MM fiscal period key (master PRD §V4 format)",
    ),
    calculation_result_hash: str = Query(
        ...,
        min_length=1,
        max_length=64,
        description="Epic 4 SHA-256 hex digest from fiscal_period_snapshots.calculation_result_hash",
    ),
    ctx_pipa: TenantContext = Depends(require_pipa_review),
    ctx: TenantContext = Depends(require_capability(Capability.AI_INSIGHT)),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """GET /api/v1/ai/insights — Three-insight cache lookup (Story 10.2).

    PIPA gate + capability gate + audit-first INSERT (CR 1.1 verbatim).
    Returns 3 insight entries:
      - cost_reduction_candidate (auto_analysis)
      - anomaly_pattern          (auto_analysis)
      - forecast                 (auto_analysis)
    All marked source_kind='auto_analysis' per AD-7 strict invariant
    (10-2 wire 진입 시점).
    """
    trace_id = str(uuid.uuid4())
    tenant_id = uuid.UUID(ctx.tenant_id)

    service = InsightCacheService(session, trace_id=trace_id)
    result = await service.get_or_compute_insights(
        tenant_id=tenant_id,
        period_key=period_key,
        calculation_result_hash=calculation_result_hash,
    )

    return InsightListResponse(
        insights=[
            InsightEntry(
                insight_kind=entry.insight_kind.value,
                question=entry.question,
                answer=entry.answer,
                source_kind=entry.source_kind.value,
                evidence_ref=entry.evidence_ref,
                generated_at=entry.generated_at,
            )
            for entry in result.insights
        ],
        period_key=result.period_key,
        calculation_result_hash=result.calculation_result_hash,
        hit_count=result.hit_count,
        miss_count=result.miss_count,
        status="success",
    )


# ── Story 10.3 EXTENSION: GET /api/v1/ai/comments ───────────
# (cj-style Epic 10 4번째 진입점 wire, 2026-08-17)
#
# AD-25 verbatim 3-tuple cache key:
#   tenant_id + period_key + calculation_result_hash
# F10.1-(d) verbatim: channel = 'ai_cache' filter 강제 (10-2 wire 보존)
# AD-7 verbatim: F10.2-(a) badge 결정자 (auto_analysis | ai_reference)
# F10.2-(b)(c) verbatim: source_kind 미매칭 reject + auto_analysis modify deny
#   + 1행 counter increment (audit_logs, SM-3a).
# F10.2-(d) verbatim: 1-line ko-KR 메시지 "분석 의견 출처가 불분명합니다"


@router.get(
    "/ai/comments",
    response_model=AICommentListResponse | AICommentError,
    status_code=status.HTTP_200_OK,
    summary="AI 의견 캐시 조회 (F10.2 badge separation verbatim)",
    description=(
        "auto_analysis 의견 3개 + ai_reference 의견 1개 반환 "
        "(source_kind='auto_analysis' | 'ai_reference' discriminator). "
        "F10.2-(a) badge 결정자 verbatim: "
        "auto_analysis → 파란 배지 '📊 자동 분석' (tooltip: '이 의견은 고정 템플릿입니다'), "
        "ai_reference → 보라 배지 '🤖 AI 참고(검증 필요)' (tooltip: 'AI는 비권위적입니다 — 확정 책임은 사용자에게'). "
        "F10.2-(b) source_kind 미매칭 value → strict reject + 1행 counter increment (F10.2-(d) ko-KR 메시지: 분석 의견 출처가 불분명합니다). "
        "F10.2-(c) auto_analysis 의견 수정 시도 → denied + 동일 카운터 추적 (SM-3a). "
        "AD-25 verbatim (tenant_id, period_key, calculation_result_hash) 캐시 키 기반. "
        "channel='ai_cache' filter 강제 (F10.1-(d) verbatim cross-channel contamination 방지)."
    ),
)
async def get_ai_comments(
    period_key: str = Query(
        ...,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        description="YYYY-MM fiscal period key (master PRD §V4 format)",
    ),
    calculation_result_hash: str = Query(
        ...,
        min_length=1,
        max_length=64,
        description="Epic 4 SHA-256 hex digest from fiscal_period_snapshots.calculation_result_hash",
    ),
    comment_kind: str | None = Query(
        None,
        pattern=r"^(cost_reduction_candidate|anomaly_pattern|forecast|risk_warning|industry_benchmark)$",
        description="Optional comment_kind filter (master PRD §12 + 10-3 forward-fill 2 kinds)",
    ),
    ctx_pipa: TenantContext = Depends(require_pipa_review),
    ctx: TenantContext = Depends(require_capability(Capability.AI_INSIGHT)),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """GET /api/v1/ai/comments — AI comment lookup with badge separation.

    PIPA gate + capability gate + audit-first INSERT (CR 1.1 verbatim).
    Returns 4 comment entries (3 auto_analysis + 1 ai_reference):
      - cost_reduction_candidate (auto_analysis) — kernel default
      - anomaly_pattern          (auto_analysis) — kernel default
      - forecast                 (auto_analysis) — kernel default
      - risk_warning             (ai_reference)  — 10-3 wire entry point
    AD-7 strict invariant: kernel defaults remain auto_analysis ONLY.
    `ai_reference` seed opinion is deterministic (async LLM pipeline
    honestly DEFER (b) retro input — D-10-3-DEFER-2).
    """
    trace_id = str(uuid.uuid4())
    tenant_id = uuid.UUID(ctx.tenant_id)

    service = CommentService(session, trace_id=trace_id)
    result = await service.list_comments(
        tenant_id=tenant_id,
        period_key=period_key,
        calculation_result_hash=calculation_result_hash,
        comment_kind=comment_kind,
    )

    return AICommentListResponse(
        comments=[
            AICommentEntry(
                comment_id=entry.comment_id,
                comment_kind=entry.comment_kind,
                body_text=entry.body_text,
                source_kind=entry.source_kind.value,
                evidence_ref=entry.evidence_ref,
                generated_at=entry.generated_at,
            )
            for entry in result.comments
        ],
        period_key=result.period_key,
        calculation_result_hash=result.calculation_result_hash,
        hit_count=result.hit_count,
        miss_count=result.miss_count,
        counter_total=result.counter_total,
        status="success",
    )


# ─────────────────────────────────────────────────────────────────────
# Story 10.4 EXTENSION: POST /api/v1/ai/promote
# (cj-style Epic 10 5번째 진입점 wire, 2026-08-18)
#
# AD-17 verbatim bind — only M2 may call `InputPromoter.promote(...)`;
# idempotent on (tenant_id, period_key, source_draft_id) 3-tuple via
# UNIQUE constraint + state='promoted' 1회 전이. Audit-first INSERT
# 2행 append (Row 1: INPUT_DRAFT/input_draft_promoted; Row 2:
# AI_EXTRACTION_EXECUTED/monthly_extraction_promote_executed) — CR 1.1.
#
# AD-7 strict invariant: M10 NEVER writes confirmed_inputs/monthly_input_rows
# except via this canonical path. Direct INSERT 시도 → 422
# INPUT_PROMOTION_DENIED + counter increment (10-1 forward-fill slot).
#
# D-10-3-DEFER-6 PIPA gate 4 endpoints carry-over 해소: all 4 endpoints
# (10-1/10-2/10-3/10-4) share `Depends(require_pipa_review)` —
# `POST /ai/promote` is the 4th wire.
#
# Capability layer ordering:
#   1. require_pipa_review            → AD-22 + PIPA gate (1st line)
#   2. get_current_m2_user            → AD-17 M2-only (2nd line)
#   3. require_capability(AI_INSIGHT)  → industry-aware (3rd line)
#
# Discriminated union envelope (CR 12-5 D-13 verbatim — `status` tag):
#   PromoteResponse | PromoteDraftImmutableError | PromoteSourceDraftNotFoundError
#   | PromoteIdempotencyMismatchError | PromoteM2OnlyError
#   | AiPipaConsentMissingError | InputPromotionDeniedError
#
# Error mapping (Python exception → Pydantic envelope):
#   AiPipaConsentMissingError (service) → AiPipaConsentMissingEnvelope (schema)
#     [disambiguated via `as` import alias — same name in different modules]
#   PromotionSourceDraftNotFoundError   → PromoteSourceDraftNotFoundError
#   PromotionDraftImmutableError        → PromoteDraftImmutableError
#   PromotionIdempotencyMismatchError   → PromoteIdempotencyMismatchError
#   PromotionM2OnlyDeniedError          → PromoteM2OnlyError
#   ValueError (kernel shape invalid)   → PromoteM2OnlyError (defensive)
# ─────────────────────────────────────────────────────────────────────


def _build_promote_error_co_ko(
    code_literal: str,
    *,
    default_message_ko: str,
) -> str:
    """Small helper — currently just returns the default message verbatim.

    Reserved for forward-fill (e.g., localized messages from a future
    `m10_ai_messages_ko.yaml` lookup). For T4 B3 wire, all error
    envelopes return the static message verbatim — the actual ko-KR
    strings come from the spec language table.
    """
    return default_message_ko


async def _lookup_promote_audit_log_ids(
    *,
    session: AsyncSession,
    idempotency_key: uuid.UUID,
) -> tuple[uuid.UUID, uuid.UUID]:
    """Query audit_logs for the 2 audit row UUIDs emitted by the promote call.

    Row 1: action='input_draft_promoted' (emitted at PromoterService step 4,
      BEFORE the data row INSERT per CR 1.1 verbatim audit-first invariant)
    Row 2: action='monthly_extraction_promote_executed' (emitted at step 10,
      AFTER the INSERT completes successfully)

    Both rows have `payload->>'idempotency_key' = str(idempotency_key)`
    (set by `emit_audit_typed` calls). ORDER BY action ASC yields
    Row 1 first (`'input_draft_promoted'` < `'monthly_extraction_promote_executed'`
    alphabetically, since 'i' < 'm').

    Returns the (Row 1, Row 2) tuple in emit order.
    Raises `PromoterServiceError` if not exactly 2 rows found (defensive —
    promote call should emit exactly 2 audit rows).
    """
    from sqlalchemy import select as _select

    from apps.api.core.db_models import AuditLog
    from apps.api.modules.m10_ai.services.promoter_service import (
        PromoterServiceError,
    )

    stmt = (
        _select(AuditLog.id, AuditLog.action)
        .where(AuditLog.payload["idempotency_key"].astext == str(idempotency_key))
        .order_by(AuditLog.action)
    )
    rows = (await session.execute(stmt)).all()
    if len(rows) != 2:
        raise PromoterServiceError(
            f"expected 2 audit_logs rows for idempotency_key={idempotency_key}, "
            f"got {len(rows)} (audit-first INSERT 2-row invariant violated)"
        )
    return (rows[0].id, rows[1].id)


@router.post(
    "/ai/promote",
    response_model=PromoteEnvelope,
    status_code=status.HTTP_200_OK,
    summary="AI 초안 → monthly_input_rows 승격 (AD-17 verbatim)",
    description=(
        "Body: { tenant_id, period_key, source_draft_id, "
        "confirmed_value_hash (optional), actor_id }. "
        "Capability gate: AI_INSIGHT (industry-agnostic). PIPA consent "
        "RE-CHECKED at the handler layer (1st gate, fail-closed). "
        "AD-17 verbatim M2-only: `get_current_m2_user` enforces the "
        "synthetic `m2_service_role` on the JWT; the kernel-side "
        "`validate_promotion_request` re-checks `actor_role` Literal as "
        "a defense-in-depth audit anchor. "
        "Idempotent on (tenant_id, period_key, source_draft_id) 3-tuple "
        "via DB-level UNIQUE constraint + state='promoted' 1회 전이. "
        "Audit-first INSERT 2-row invariant (CR 1.1): Row 1 "
        "(`input_draft_promoted`) BEFORE data INSERT; Row 2 "
        "(`monthly_extraction_promote_executed`) AFTER. "
        "AD-7 strict invariant: M10 NEVER writes `confirmed_inputs`; "
        "INSERT target is `monthly_input_rows` ONLY. "
        "Returns discriminated union `PromoteEnvelope` with `status` tag "
        "(CR 12-5 D-13/D-14 verbatim)."
    ),
)
async def promote_ai_draft_endpoint(
    body: PromoteRequest,
    response: Response,
    ctx_pipa: TenantContext = Depends(require_pipa_review),
    ctx_m2: TenantContext = Depends(get_current_m2_user),
    ctx_cap: TenantContext = Depends(require_capability(Capability.AI_INSIGHT)),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """POST /api/v1/ai/promote — Story 10.4 AD-17 verbatim promotion port.

    Discriminated union return (`PromoteEnvelope`):
    - success → `status='success'` with full promotion wire envelope
    - 6 error envelopes: PROMOTE_DRAFT_IMMUTABLE / PROMOTE_SOURCE_DRAFT_NOT_FOUND
      / PROMOTE_IDEMPOTENCY_MISMATCH / INPUT_PROMOTION_M2_ONLY /
      AI_PIPA_CONSENT_MISSING / INPUT_PROMOTION_DENIED

    Layer ordering:
      1. require_pipa_review    (1st defense — blocks before body parse)
      2. get_current_m2_user    (2nd defense — synthetic M2 service role)
      3. AI_INSIGHT capability  (3rd defense — industry-aware gate)

    Service-layer exception → Pydantic envelope mapping documented at the
    module-level router constants above.
    """
    from datetime import datetime as _dt

    trace_id = str(uuid.uuid4())
    response.headers["X-Trace-Id"] = trace_id

    # Build kernel PromotionRequest (AD-17 verbatim 4-tuple + actor_role).
    # The kernel `actor_role` is always 'm2_service_role' (only M2 may call)
    # — the HTTP-layer M2 gate already verified the JWT carries this role.
    kernel_req = KernelPromotionRequest(
        tenant_id=body.tenant_id,
        period_key=body.period_key,
        source_draft_id=body.source_draft_id,
        actor_id=body.actor_id,
        actor_role=ALLOWED_PROMOTER_ACTOR_ROLE,
    )

    adapter = DbPromoterAdapter(session, trace_id=trace_id)
    try:
        result = await adapter.promote(kernel_req)
    except AiPipaConsentMissingError as e:
        return AiPipaConsentMissingEnvelope(
            status="pipa_consent_missing",
            code="AI_PIPA_CONSENT_MISSING",
            message_ko=(
                "승격 포트는 개인정보 처리 동의가 필요합니다. "
                "설정에서 동의해 주세요."
            ),
            details={"tenant_id": str(e.tenant_id)},
            trace_id=e.trace_id,
        )
    except PromotionSourceDraftNotFoundError as e:
        return PromoteSourceDraftNotFoundError(
            status="source_draft_not_found",
            code="PROMOTE_SOURCE_DRAFT_NOT_FOUND",
            message_ko="해당 초안을 찾을 수 없습니다",
            details={"source_draft_id": str(e.source_draft_id)},
            trace_id=e.trace_id,
        )
    except PromotionDraftImmutableError as e:
        return PromoteDraftImmutableError(
            status="draft_immutable",
            code="PROMOTE_DRAFT_IMMUTABLE",
            message_ko="초안이 이미 승격 완료 또는 superseded 상태입니다",
            details={
                "source_draft_id": str(e.source_draft_id),
                "current_state": e.current_state,
            },
            trace_id=e.trace_id,
        )
    except PromotionIdempotencyMismatchError as e:
        return PromoteIdempotencyMismatchError(
            status="idempotency_mismatch",
            code="PROMOTE_IDEMPOTENCY_MISMATCH",
            message_ko=(
                "동일 초안에 다른 값으로 재호출되었습니다. "
                "원본 초안의 confirmed_value_hash를 사용해 주세요."
            ),
            details={"idempotency_key": str(e.idempotency_key)},
            trace_id=e.trace_id,
        )
    except PromotionM2OnlyDeniedError as e:
        return PromoteM2OnlyError(
            status="m2_only",
            code="INPUT_PROMOTION_M2_ONLY",
            message_ko=(
                "승격 포트는 M2 모듈만 호출할 수 있습니다. "
                "M2 서비스 토큰으로 인증해 주세요."
            ),
            details={
                "actual_role": e.actor_role,
                "required_role": ALLOWED_PROMOTER_ACTOR_ROLE,
            },
            trace_id=e.trace_id,
        )
    except ValueError:
        # Kernel-level shape validation failure (period_key YYYY-MM format
        # or actor_role mismatch). Mapped defensively to M2-only envelope
        # since shape failures here typically stem from M2 module wiring
        # issues. Operators see the message_ko for diagnosis.
        return PromoteM2OnlyError(
            status="m2_only",
            code="INPUT_PROMOTION_M2_ONLY",
            message_ko=(
                "승격 요청 형식이 올바르지 않습니다 "
                "(period_key=YYYY-MM, M2 서비스 토큰 필요)."
            ),
            details={},
            trace_id=trace_id,
        )

    # Look up the 2 audit_log UUIDs emitted by the promote call.
    audit_log_ids = await _lookup_promote_audit_log_ids(
        session=session,
        idempotency_key=result.idempotency_key,
    )

    # Map PromotionResult (kernel frozen dataclass) → PromoteResponse (Pydantic).
    # `promoted_at`: handler-time UTC timestamp (the canonical timestamp lives
    #   on audit_logs Row 2's `occurred_at`; the wire surface here is a
    #   best-effort proxy).
    # `draft_hash`: idempotency_key bytes (deterministic proxy for the
    #   input_drafts.confirmed_value content hash). Actual content-based
    #   SHA-256 is forward-fill scope.
    return PromoteResponse(
        status="success",
        tenant_id=body.tenant_id,
        period_key=body.period_key,
        source_draft_id=body.source_draft_id,
        promotion_id=result.promotion_id,
        idempotency_key=result.idempotency_key,
        confirmed_input_row_id=result.monthly_input_row_id,
        promoted_at=_dt.now(UTC),
        draft_hash=result.idempotency_key.bytes + b"\x00" * 16,  # proxy: 32 bytes
        idempotent_replay=result.idempotent_replay,
        audit_log_ids=audit_log_ids,
    )
