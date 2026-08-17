"""packages.services.m10_ai.extraction_port — M10 AI extraction port contract.

Story 1.3 — Task 1.1 / Task 2.1.

This module is the **pure-Python, stdlib-only** port interface between the
M0 onboarding surface and the M10 AI module. The M0 onboarding handler
imports this port; M10 ships the adapter implementation.

Why a port (vs. inlining the adapter into M0):
- AD-1 / AD-11 layering — M0 must not depend on the AI SDK (M10 owns the
  provider; M0 owns the user surface).
- Tests use a `FakeDocumentExtractionAdapter` so we can exercise the full
  M0 → M10 contract without an API key, network, or a real provider.
- `compute_completion()` (Story 1.2 settings_completion.py) reads only the
  DraftSummary fields; the port outputs them so the caller never has to
  re-derive.

The port accepts a base64-encoded document payload and returns one
`ExtractionField` per AI-extracted field. The adapter is responsible for
calling the provider, normalizing failures, applying redaction, and
computing `confidence` from the provider's self-rated heuristic.

Anti-pattern guards:
- Do NOT let Pydantic / FastAPI leak into this module. It must remain
  stdlib-only (AD-1 / AD-5). Schema-validated types live in M10's
  `schemas.py`; the port exposes frozen dataclasses only.
- Do NOT bake provider-specific keys, model IDs, or SDK calls into the
  port — see `apps/api/modules/m10_ai/config.py` for those.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Final, Literal, Protocol

# ── Canonical field schema (Story 1.3 — Task 1.1) ─────────────
# MVP set per Open Question 1 (cj-style default applied 2026-08-01):
# PRD §F0.3 names business_registration_number as the minimum required
# field; the MVP extraction set also includes company_name, address,
# representative_name, and industry (5 fields). The schema is extensible
# — adding a new field requires updating `SUPPORTED_FIELD_NAMES` AND the
# TS mirror in `apps/web/lib/extraction-fields.ts` (drift caught by
# `tests/integration/test_badge_consistency.py`).
SUPPORTED_FIELD_NAMES: Final[frozenset[str]] = frozenset(
    {
        "business_registration_number",  # 사업자등록번호
        "company_name",  # 회사명
        "address",  # 주소
        "representative_name",  # 대표자명
        "industry",  # 업종 분류
    }
)


class FieldName(str, Enum):
    """Canonical field_name enum. Mirrors SUPPORTED_FIELD_NAMES."""

    BUSINESS_REGISTRATION_NUMBER = "business_registration_number"
    COMPANY_NAME = "company_name"
    ADDRESS = "address"
    REPRESENTATIVE_NAME = "representative_name"
    INDUSTRY = "industry"


# ── Pure dataclasses (AD-5: no I/O, no clock, no random) ──────
@dataclass(frozen=True)
class ExtractionEvidence:
    """Source location of an extracted value.

    The `text` field is capped at 200 characters by the provider adapter
    (see `apps/api/modules/m10_ai/service.py` Task 2.3 — evidence policy).
    The redactor (`apps/api/core/logging.py redact_processor`) also
    scrubs emails, KR phone numbers, and business registration numbers
    from the text before it ever hits a log line.

    `page` is 1-indexed (per PDF page) or None for image-only inputs.
    `bbox` is reserved for future use (PDF coordinates); MVP leaves it
    None to keep the JSONB payload small.
    """

    page: int | None
    text: str  # max 200 chars; redacted by service before persistence
    bbox: tuple[float, float, float, float] | None = None


@dataclass(frozen=True)
class ExtractionField:
    """One AI-extracted field returned by the provider.

    `confidence` is the model's self-rated heuristic in `[0, 1]`. NULL
    confidence is represented as `confidence=None` here; the downstream
    reviewer (settings_completion.is_review_required) treats NULL as
    review-required.

    `ai_value` is the raw provider output, kept as the canonical
    `dict | str | int | float | None` JSON-serializable shape so it can
    land directly in `input_drafts.ai_value JSONB`. The service layer
    normalizes scalar vs structured outputs before persistence.
    """

    field_name: str
    ai_value: str | int | float | bool | dict | None
    confidence: float | None  # 0.00..1.00; None = unscored
    evidence: ExtractionEvidence | None


@dataclass(frozen=True)
class DocumentExtractionJob:
    """In-memory representation of one uploaded document + its extraction.

    This is the *port input*: the M10 adapter takes a raw document
    payload (bytes + MIME) and returns this job result. The service
    layer (M10) is responsible for persisting the corresponding
    `uploaded_documents` + `input_drafts` rows via service_role — but
    that wiring is OUTSIDE this port (port = pure contract).

    `status` follows the 4-state provider-job FSM:
        queued → processing → (completed | failed)
    distinct from `input_drafts.state` (draft → reviewed → superseded).
    """

    document_id: uuid.UUID
    tenant_id: uuid.UUID
    mime_type: str
    byte_size: int
    content_sha256: bytes
    status: str
    fields: tuple[ExtractionField, ...] = ()
    error_code: str | None = None
    error_message_ko: str | None = None


@dataclass(frozen=True)
class ExtractionRequest:
    """Port input — what the M0 onboarding handler passes to M10.

    `idempotency_key` is the `Idempotency-Key` header value (or the
    generated one if the client didn't send it). The adapter is free
    to honor it (return the prior result for the same key) or to
    ignore it; the contract guarantees ONLY that two requests with
    the same key produce the same `document_id` (Story 1.3 Task 3.1).
    """

    tenant_id: uuid.UUID
    uploaded_by: uuid.UUID
    document_id: uuid.UUID  # UUID v7 — generated by the caller (M0)
    mime_type: str  # validated by service against ALLOWED_MIME
    byte_size: int  # validated by service against MAX_UPLOAD_BYTES
    document_bytes: bytes  # raw bytes; NEVER logged
    idempotency_key: str
    request_id: str  # trace_id for log correlation
    storage_path: str = ""  # Supabase Storage path; filled by caller


# ── Port interface (Protocol — duck-typed) ────────────────────
class DocumentExtractionPort(Protocol):
    """The port M0 depends on. M10 ships the adapter that satisfies it.

    Implementations:
    - `apps/api/modules/m10_ai/adapters/claude_vision.py` (production;
      gated by [STACK BUMP] + ANTHROPIC_API_KEY)
    - `apps/api/modules/m10_ai/adapters/fake_adapter.py` (tests + dev
      without API key; returns deterministic fields per file hash)
    """

    def extract(self, request: ExtractionRequest) -> DocumentExtractionJob:
        """Run extraction synchronously and return the populated job.

        The adapter is responsible for:
        - provider timeout enforcement (`PROVIDER_TIMEOUT_S`)
        - redaction of `document_bytes` from logs (redact_processor)
        - normalization of provider output into `ExtractionField` tuples
        - mapping low-level provider errors into the 4-state job FSM
          (`status='failed', error_code='AI_PROVIDER_TIMEOUT'` etc.)

        The adapter MUST NOT raise on transient provider failures —
        instead, it returns a `DocumentExtractionJob` with
        `status='failed'` and a populated `error_code` so the API
        surface can render the typed error envelope without try/except.
        """
        ...


# ── Story 10.1 EXTENSION: Monthly Input Field Schema ────────
# (cj-style Epic 10 2번째 진입점 wire 진입, 2026-08-17)
#
# 6-stream monthly input extraction fields (master PRD §3.1):
# - 직접재료비 / 직접노무비 / 제조간접비 / 판매관리비 / 매출 / 기말재고
#
# Story 1.3 baseline (onboarding extraction) 보존 — MONTHLY_INPUT_FIELD_NAMES
# 별도 frozenset + MonthlyFieldName 별도 enum + MonthlyInputDraftRow 별도
# dataclass (target_table discriminator).
#
# AD-7 verbatim bind: AI output → input_drafts only. confirmed_inputs 도달은
# AD-17 promotion port만 (Story 10.4 detailed wire).
MONTHLY_INPUT_FIELD_NAMES: Final[frozenset[str]] = frozenset(
    {
        "direct_material_cost",  # 직접재료비
        "direct_labor_cost",  # 직접노무비
        "manufacturing_overhead",  # 제조간접비
        "selling_admin_cost",  # 판매관리비
        "revenue",  # 매출
        "inventory_closing",  # 기말재고
    }
)


class MonthlyFieldName(str, Enum):
    """Canonical monthly input field_name enum. Mirrors MONTHLY_INPUT_FIELD_NAMES."""

    DIRECT_MATERIAL_COST = "direct_material_cost"
    DIRECT_LABOR_COST = "direct_labor_cost"
    MANUFACTURING_OVERHEAD = "manufacturing_overhead"
    SELLING_ADMIN_COST = "selling_admin_cost"
    REVENUE = "revenue"
    INVENTORY_CLOSING = "inventory_closing"


# ── Story 10.1 EXTENSION: target_table discriminator ─────────
# Discriminated union discriminator for input_drafts.target_table:
# - 'onboarding_inputs' = Story 1.3 wire (5 onboarding fields)
# - 'monthly_inputs' = Story 10.1 wire (6 monthly input fields)
# AD-7 strict invariant: M10 NEVER writes to 'confirmed_inputs'.
InputTargetTable = Literal["onboarding_inputs", "monthly_inputs"]
ALLOWED_INPUT_TARGET_TABLES: Final[frozenset[str]] = frozenset(
    {"onboarding_inputs", "monthly_inputs"}
)


# ── Constants re-exported for cross-language parity tests ────
# `tests/integration/test_badge_consistency.py` reads these constants
# from the Python source (regex-parse) and asserts the TS mirror has
# the same set.
__all__: Final[tuple[str, ...]] = (
    "SUPPORTED_FIELD_NAMES",
    "FieldName",
    "ExtractionEvidence",
    "ExtractionField",
    "DocumentExtractionJob",
    "ExtractionRequest",
    "DocumentExtractionPort",
    # Story 10.1 EXTENSION (monthly input extraction)
    "MONTHLY_INPUT_FIELD_NAMES",
    "MonthlyFieldName",
    "InputTargetTable",
    "ALLOWED_INPUT_TARGET_TABLES",
)
