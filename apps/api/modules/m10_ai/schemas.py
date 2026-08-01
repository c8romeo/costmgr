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
