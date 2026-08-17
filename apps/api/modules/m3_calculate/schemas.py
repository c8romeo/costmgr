"""apps.api.modules.m3_calculate.schemas — Pydantic v2 schemas for M3 calculation.

Story 4.2 — `POST /api/v1/calc` request/response envelope.
Story 4.3 — verdict envelope extension (VerificationItem + Verdict +
CalcResponse.verdict field).
Story 9.3 (T2.3) — A29 forward-lock dual-route EXTENSION:
  - `AllocationOutcomeABC` — M9 ABC allocation result envelope
  - `CalcAbcResponse` — discriminated union member for service industry
    (engine_type: Literal["abc"] tag discriminator)

AD-15 §4: `{code, message_ko, details, trace_id}` envelope.
AD-24: period_key = YYYY-MM typed format.
EP-IC-1: KRW = int (AD-8 BIGINT); `result_hash` = 64-char hex.
AD-20: verification_status enum (pending|passed|failed) — exposed as
'passed' | 'failed' only (pending is internal transient).
AD-19: M3 owns ONLY public endpoint; M9 owns service layer ONLY.
  Discriminated union: CalcResponse (engine_type='trad') OR
  CalcAbcResponse (engine_type='abc').
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# AD-24 typed period key — YYYY-MM (mirrors `period_cost._PERIOD_KEY_PATTERN`).
_PERIOD_KEY_PATTERN: re.Pattern[str] = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
# EP-IC-1: 64-char hex SHA-256 (mirrors `period_cost._compute_result_hash`).
_RESULT_HASH_PATTERN: re.Pattern[str] = re.compile(r"^[0-9a-f]{64}$")


class CalcRequest(BaseModel):
    """`POST /api/v1/calc` body.

    Spec: `extra='forbid'` (CR 2.3 lesson) — unknown field → 422 INVALID_PAYLOAD.
    """

    model_config = ConfigDict(extra="forbid")

    period_key: str = Field(
        ...,
        pattern=_PERIOD_KEY_PATTERN.pattern,
        description="YYYY-MM (AD-24 typed period key).",
        examples=["2026-07"],
    )


# ── Story 4.3 — verification envelope (AD-12 + AD-20) ───────────────
class VerificationItem(BaseModel):
    """V1·V4·V7·V8 rule 발동 결과 (1 rule = 1 item).

    Story 4.3 (Task 3.1) — AC #3 envelope shape:
        - `code`: V1/V4/V7/V8 discriminator (PRD §11).
        - `status`: passed/failed. `skipped` rules do NOT appear in
          `verifications[]` (applies_to=False → silent skip).
        - `message_ko`: Korean diagnostic. Deterministic for V8 regression.
        - `details`: rule-specific payload (V1: delta_krw, V4: 4_elements,
          V7: pools/activities, V8: placeholder flags).

    `extra='forbid'` (CR 2.3 lesson) — unknown field → 422 INVALID_PAYLOAD.
    """

    model_config = ConfigDict(extra="forbid")

    code: Literal["V1", "V4", "V7", "V8"]
    status: Literal["passed", "failed"]
    message_ko: str
    details: dict[str, Any] = Field(default_factory=dict)


class Verdict(BaseModel):
    """AD-20 verification envelope — `CalcResponse.verdict` field.

    Story 4.3 (Task 3.1) — AD-20 invariant:
        - `verification_status` ∈ {passed, failed} (pending internal-only).
        - `top_failure` is non-null iff `verification_status == 'failed'`.
          AD-20 invariant: top_failure = first failed item.

    Pydantic v2 + `extra='forbid'` (CR 2.3 lesson).
    """

    model_config = ConfigDict(extra="forbid")

    verification_status: Literal["passed", "failed"]
    verifications: list[VerificationItem] = Field(default_factory=list)
    top_failure: VerificationItem | None = None
    trace_id: str


class CalcResponse(BaseModel):
    """`POST /api/v1/calc` success envelope (200 OK).

    State is `Literal["verified"]` only — engine returns `draft`
    (AD-22), service transitions to `verified` after verification pass
    + idempotency check + INSERT. `committed` and `reversed` are M11
    territory (Epic 11).

    Story 4.3 extension: `verdict` field added (AD-12 + AD-20 envelope).
    On `verification_status == 'failed'` the orchestrator ROLLBACKs but
    still returns 200 OK with the verdict envelope (calculation itself
    succeeded; lock is service-layer concern, NOT 4xx).
    """

    model_config = ConfigDict(extra="forbid")

    tenant_id: uuid.UUID
    period_key: str = Field(..., pattern=_PERIOD_KEY_PATTERN.pattern)
    baseline_revision: int = Field(..., ge=1)

    material_cost: int = Field(..., description="직접재료 (KRW int, AD-8)")
    labor_cost: int = Field(..., description="직접노무 (KRW int, AD-8)")
    overhead_cost: int = Field(..., description="제조간접 (KRW int, AD-8)")
    manufacturing_cost: int = Field(..., description="제조원가 합계 (KRW int, AD-8)")
    inventory_adjustment: int = Field(
        default=0, description="기말재고 조정 (Story 4.1 = KRW(0) 고정, Epic 5 fold-in)"
    )

    result_hash: str = Field(..., pattern=_RESULT_HASH_PATTERN.pattern)
    state: Literal["verified"] = "verified"

    trace_id: str = Field(..., description="AD-15 §4 — envelope trace_id.")

    # ── Story 4.3 — verdict envelope (AD-12 + AD-20) ───────────────
    verdict: Verdict = Field(
        ...,
        description=(
            "AD-12 verification envelope (V1·V4·V7·V8 결과). "
            "verification_status='passed' → 정상. 'failed' → 회계 잠금, "
            "fiscal_period_snapshots INSERT 안 됨, calc_log action='rollback'."
        ),
    )


class CalcErrorResponse(BaseModel):
    """AD-15 §4 typed error envelope — `{code, message_ko, details, trace_id}`."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message_ko: str
    details: dict = Field(default_factory=dict)
    trace_id: str


# ── Story 9.3 (T2.3) — ABC dual-route envelope (AD-19) ──────────────


class AllocationOutcomeABC(BaseModel):
    """M9 AbcAllocationService.compute_and_persist result envelope.

    Story 9.3 (T2.3) — discriminated union member for ABC dual-route
    response. The M9 service layer returns this dict-shaped envelope; we
    surface it verbatim on the wire so frontend RSC components can read
    breakdown / unused_capacity / v7_verdict / ccr blocks without an
    additional reshape step.

    Fields:
        breakdown: list of cost-object breakdown rows (PRD §F9.2 + §A6).
        unused_capacity: unused capacity sub-row payload (PRD §A9).
        v7_verdict: V7 ABC 무결성 verdict (Σ breakdown + unused = Σ department).
        ccr: CCR computation summary per department.
        is_balanced: V7 boolean shortcut (frontend hint).

    `extra='forbid'` (CR 2.3 lesson) — unknown field → 422 INVALID_PAYLOAD.
    """

    model_config = ConfigDict(extra="forbid")

    breakdown: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Cost-object breakdown rows (PRD §F9.2 + §A6)",
    )
    unused_capacity: dict[str, Any] = Field(
        default_factory=dict,
        description="Unused capacity sub-row payload (PRD §A9)",
    )
    v7_verdict: dict[str, Any] = Field(
        default_factory=dict,
        description="V7 ABC 무결성 verdict (Σ breakdown + unused = Σ department)",
    )
    ccr: dict[str, Any] = Field(
        default_factory=dict,
        description="CCR computation summary per department",
    )
    is_balanced: bool = Field(
        default=False,
        description="V7 boolean shortcut (frontend hint)",
    )


class CalcAbcResponse(BaseModel):
    """`POST /api/v1/calc` success envelope for service industry (ABC path).

    Story 9.3 (T2.3) — A29 forward-lock dual-route wire. Discriminated
    union member alongside `CalcResponse`. Pydantic v2 + FastAPI support
    `Union[A, B]` with discriminator tag (`engine_type`).

    Discriminator tag: `engine_type: Literal["abc"]`. The paired
    `CalcResponse` carries `engine_type: Literal["trad"]` (implicit via
    `state: Literal["verified"]` — same state machine).

    State is `Literal["verified"]` only — engine returns `draft`
    (AD-22), service transitions to `verified` after V7 balance +
    idempotency check + INSERT. `committed` and `reversed` are M11
    territory (Epic 11).

    `extra='forbid'` (CR 2.3 lesson) — unknown field → 422 INVALID_PAYLOAD.
    """

    model_config = ConfigDict(extra="forbid")

    engine_type: Literal["abc"] = "abc"

    tenant_id: uuid.UUID
    period_key: str = Field(..., pattern=_PERIOD_KEY_PATTERN.pattern)
    baseline_revision: int = Field(..., ge=1)

    # M9 AbcAllocationService.compute_and_persist result envelope.
    # Verbatim dict-shaped surface so frontend RSC reads breakdown /
    # unused_capacity / v7_verdict / ccr blocks without reshape.
    allocation_outcome: AllocationOutcomeABC

    # fiscal_period_snapshots.id (UUID) for the ABC path row.
    # NOT a UUID-as-string (unlike the CalcOutcomeABC service-layer
    # frozen dataclass) — wire-level UUID serialization is canonical.
    snapshot_id: uuid.UUID

    result_hash: str = Field(..., pattern=_RESULT_HASH_PATTERN.pattern)
    state: Literal["verified"] = "verified"

    trace_id: str = Field(..., description="AD-15 §4 — envelope trace_id.")

    # ── Story 4.3 — verdict envelope (AD-12 + AD-20) ───────────────
    verdict: Verdict = Field(
        ...,
        description=(
            "AD-12 verification envelope (V1·V4·V7·V8 결과). service industry = "
            "V7 + V8 only (V1/V4 universal-but-skipped). "
            "verification_status='passed' → 정상. 'failed' → 회계 잠금, "
            "fiscal_period_snapshots INSERT 안 됨, calc_log action='rollback'."
        ),
    )
