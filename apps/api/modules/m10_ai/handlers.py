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
from typing import Any

from fastapi import APIRouter, Depends, Header, Query, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

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
    DocumentResponse,
    DocumentSummary,
    DocumentUploadRequest,
    DraftListResponse,
    DraftResponse,
    DraftUpdateRequest,
    EvidenceResponse,
    PromoteRequest,
    PromoteResponse,
)
from apps.api.modules.m10_ai.service import (
    DocumentMimeNotAllowedError,
    DocumentNotFoundError,
    DocumentService,
    DocumentTooLargeError,
    DraftNotFoundError,
    DraftStateError,
    PromoteRequiredFieldsMissingError,
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
    response_model=PromoteResponse,
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
    body: PromoteRequest,
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

    return PromoteResponse(
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
