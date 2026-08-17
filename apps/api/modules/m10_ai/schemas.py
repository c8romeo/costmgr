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
from typing import Any, Literal

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


class PromoteRequest(BaseModel):
    """Body of `POST /api/v1/ai-drafts/promote`."""

    model_config = ConfigDict(extra="forbid")
    document_id: uuid.UUID


class PromoteResponse(BaseModel):
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
