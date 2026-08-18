"""packages.services.m10_ai.promoter_port — Story 10.4 pure kernel.

Story 10.4 (cj-style Epic 10 5번째 진입점 = cj-style 33번째 epic 연속) —
T1 kernel for the InputPromoter promotion port (AD-17 verbatim).

This module is the **stdlib-only, pure-Python** kernel that defines:
- `PromotionRequest` + `PromotionResult` frozen dataclasses
- `PROMOTE_STATUS_VALUES` frozenset (AD-15 cross-language parity SSOT)
- `compute_promotion_idempotency_key` — deterministic UUID v5 derivation
  on (tenant_id, period_key, source_draft_id) 3-tuple (AD-17 verbatim)
- `validate_promotion_request` — Pydantic-free shape validation
  (period_key YYYY-MM format + actor_role='m2_service_role' ONLY)
- `InputPromoterPort` Protocol — port contract for DB adapter
  implementation

Why a separate kernel (vs. extending extraction_port or insight_cache_kernel):
- AD-5 engine purity — no I/O, no clock, no random (UUID v5 is
  deterministic via uuid.NAMESPACE_URL + frozen seed).
- AD-7 strict invariant — M10 NEVER writes confirmed_inputs;
  this kernel defines the contract that AD-7 strict invariant guard
  enforces upstream (M10 service → monthly_input_rows direct INSERT
  시도 → 422 INPUT_PROMOTION_DENIED).
- AD-15 cross-language parity — TS mirror at `apps/web/lib/ai-promote.ts`
  mirrors this kernel (drift caught by
  `apps/web/__tests__/lib/ai-promote-parity.test.ts`, honestly DEFER (d)
  frontend dedicated sprint).
- AD-17 verbatim bind — only M2 may call; idempotency on 3-tuple
  enforced at DB-level (alembic 0032 `monthly_input_promotions`
  UNIQUE constraint) + kernel deterministic UUID v5 derivation.
- AD-1 / AD-11 layering — service layer (apps/api/modules/m10_ai/services/
  promoter_service.py) imports this kernel; UI / handlers never reach
  into raw values.

Anti-pattern guards:
- Do NOT call any I/O (no DB, no network, no clock, no random).
- Do NOT import Pydantic — these are kept at the service layer boundary.
- Do NOT import AI SDK — pure kernel only.
- Do NOT bake provider-specific keys, model IDs, or SDK calls into the
  port — see `apps/api/modules/m10_ai/config.py` for those.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Final, Literal, Protocol

# ── Status discriminator (AD-15 SSOT) ────────────────────────
# 6 canonical statuses that match the Discriminated union envelope
# `status` tag in `apps/api/modules/m10_ai/schemas.py` (T4 wire).
# AD-15 cross-language parity SSOT: TS mirror
# `apps/web/lib/ai-promote.ts` MUST mirror this frozenset.
# Drift detector: `apps/web/__tests__/lib/ai-promote-parity.test.ts`
# (honestly DEFER (d) frontend dedicated sprint).
PROMOTE_STATUS_VALUES: Final[frozenset[str]] = frozenset(
    {
        "success",  # 1st call → INSERT + 2 audit_log_rows + state='promoted'
        "idempotent_replay",  # 2nd call → no INSERT + 1 audit_log_id from Row 1
        "draft_not_found",  # source_draft_id 미존재 → 404
        "draft_superseded",  # state='superseded' → 409
        "idempotency_mismatch",  # replay 인데 confirmed_value_hash 다름 → 422
        "m2_only_denied",  # actor_role != 'm2_service_role' → 403
    }
)


# ── Period key format (master PRD §V4) ───────────────────────
# YYYY-MM format: 4-digit year + dash + 2-digit month (01-12).
# Matches `handlers.py` Query param pattern for /ai/insights and
# /ai/comments endpoints (10-2 / 10-3 wire 보존).
PERIOD_KEY_PATTERN: Final[re.Pattern[str]] = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


# ── M2-only role enforcement (AD-17 verbatim) ────────────────
# AD-17 verbatim: "only M2 may call InputPromoter.promote(...).
# Promotion retains the draft with state='promoted', records actor
# plus draft hash in audit_logs, and writes the canonical
# confirmed-input shape."
ALLOWED_PROMOTER_ACTOR_ROLE: Final[str] = "m2_service_role"


# ── Idempotency key namespace (deterministic UUID v5) ─────────
# Fixed namespace URL ensures cross-process consistency. Any change to
# this constant would invalidate ALL existing idempotency keys — do
# NOT modify after first deploy.
_IDEMPOTENCY_KEY_NAMESPACE: Final[uuid.UUID] = uuid.NAMESPACE_URL


# ── Frozen dataclasses (AD-5 stdlib-only, AD-15 parity) ──────


@dataclass(frozen=True)
class PromotionRequest:
    """Input to InputPromoterPort.promote() — AD-17 verbatim 4 fields.

    Fields:
    - tenant_id: UUID v7 of the tenant (RLS isolation key, AD-3)
    - period_key: YYYY-MM fiscal period (master PRD §V4)
    - source_draft_id: UUID v7 of the input_drafts row to promote
    - actor_id: UUID v7 of the actor performing the promotion
    - actor_role: Literal role (only 'm2_service_role' accepted,
      AD-17 verbatim "Only M2 may call")
    """

    tenant_id: uuid.UUID
    period_key: str
    source_draft_id: uuid.UUID
    actor_id: uuid.UUID
    actor_role: str


@dataclass(frozen=True)
class PromotionResult:
    """Output from InputPromoterPort.promote() — Discriminated union envelope.

    Fields:
    - promotion_id: UUID v7 of the new monthly_input_promotions row
      (or existing row on idempotent_replay)
    - idempotency_key: UUID v5 derivation of 3-tuple (DB-level UNIQUE
      constraint verification mirror)
    - status: one of PROMOTE_STATUS_VALUES (6 values, AD-15 SSOT)
    - monthly_input_row_id: UUID v7 of the new (or existing) monthly_input_rows
    - idempotent_replay: True if 2nd+ call (no new INSERT); False if 1st
    - trace_id: CR 12-5 D-14 verbatim envelope trace_id
    """

    promotion_id: uuid.UUID
    idempotency_key: uuid.UUID
    status: Literal[
        "success",
        "idempotent_replay",
        "draft_not_found",
        "draft_superseded",
        "idempotency_mismatch",
        "m2_only_denied",
    ]
    monthly_input_row_id: uuid.UUID
    idempotent_replay: bool
    trace_id: str


# ── Pure functions (no I/O, no clock, no random) ─────────────


def compute_promotion_idempotency_key(
    *,
    tenant_id: uuid.UUID,
    period_key: str,
    source_draft_id: uuid.UUID,
) -> uuid.UUID:
    """Compute deterministic UUID v5 idempotency key (AD-17 verbatim).

    AD-17 verbatim: idempotent on (tenant_id, period_key, source_draft_id).
    DB-level UNIQUE constraint on `monthly_input_promotions` enforces
    the same 3-tuple; this UUID v5 key is the deterministic
    application-level mirror used for:
    - idempotent replay detection (2nd call → same UUID → no INSERT)
    - log correlation (1 audit_log_id per promote call traceable to key)
    - TS mirror parity verification (apps/web/lib/ai-promote.ts)

    Args:
        tenant_id: UUID v7 of tenant
        period_key: YYYY-MM fiscal period
        source_draft_id: UUID v7 of input_drafts row

    Returns:
        UUID v5 derivation (deterministic, same inputs → same output)

    Anti-pattern guards:
    - Do NOT use uuid.uuid4() (random) — would break idempotency
    - Do NOT use uuid.uuid1() (clock-based) — would break determinism
    - Do NOT use uuid.uuid3() (MD5 hash) — use uuid5 (SHA-1) for stronger
      collision resistance on long-lived idempotency keys
    """
    # Compose the deterministic seed string.
    # Canonical format mirrors AD-25 verbatim 3-tuple cache key
    # (insight_cache_kernel) — pipe-separated tenant, period, draft UUIDs.
    seed = f"{tenant_id}|{period_key}|{source_draft_id}"
    return uuid.uuid5(_IDEMPOTENCY_KEY_NAMESPACE, seed)


def validate_promotion_request(request: PromotionRequest) -> None:
    """Validate PromotionRequest shape — raises ValueError on invalid input.

    Validation rules (AD-17 + master PRD §V4):
    1. period_key matches YYYY-MM format (master PRD §V4)
    2. actor_role == 'm2_service_role' (AD-17 verbatim "only M2 may call")

    Note: This is a Pydantic-free shape validation (kernel stays
    stdlib-only per AD-5). Pydantic v2 Literal 검증 is reused at the
    service layer boundary (CR 12-1 L3 ORM→kernel boundary pattern).

    Args:
        request: PromotionRequest to validate

    Raises:
        ValueError: if period_key format is invalid or actor_role
            is not 'm2_service_role'
    """
    if not PERIOD_KEY_PATTERN.match(request.period_key):
        raise ValueError(
            f"period_key format invalid: {request.period_key!r} "
            f"(expected YYYY-MM, master PRD §V4)"
        )
    if request.actor_role != ALLOWED_PROMOTER_ACTOR_ROLE:
        raise ValueError(
            f"actor_role invalid: {request.actor_role!r} "
            f"(AD-17 verbatim only M2 may call; "
            f"expected {ALLOWED_PROMOTER_ACTOR_ROLE!r})"
        )


# ── Port contract (Protocol) ──────────────────────────────────


class InputPromoterPort(Protocol):
    """Port contract for InputPromoter — DB adapter implements.

    The M10 service layer (`apps/api/modules/m10_ai/services/
    promoter_service.py`) imports this Protocol; the DB adapter
    (`apps/api/modules/m10_ai/services/db_promoter_adapter.py`)
    implements it. UI/handlers NEVER reach into this Protocol — they
    call the service layer instead.

    This mirrors the pattern established by `extraction_port.py`
    (Story 1.3) and `insight_cache_kernel.py` (Story 10.2).
    """

    async def promote(
        self,
        request: PromotionRequest,
    ) -> PromotionResult:
        """Promote a single input_drafts row to monthly_input_rows.

        AD-17 verbatim:
        - only M2 may call (validate_promotion_request enforces)
        - idempotent on (tenant_id, period_key, source_draft_id)
          (compute_promotion_idempotency_key + DB-level UNIQUE)
        - audit-first INSERT 2행 append (CR 1.1 verbatim):
          Row 1: action_class=INPUT_DRAFT, action=input_draft_promoted
          Row 2: action_class=AI_EXTRACTION_EXECUTED, action=monthly_extraction_promote_executed
        - canonical 6-stream shape (master PRD §3.1: 직접재료비/직접노무비/
          제조간접비/판매관리비/매출/기말재고) from input_drafts.confirmed_value JSONB
        - state='promoted' 1회 전이 (input_drafts.state machine EXTENSION
          alembic 0032 v2 CHECK constraint)

        Returns:
            PromotionResult with status='success' (1st call) or
            status='idempotent_replay' (2nd+ call) or one of the
            4 error statuses (draft_not_found / draft_superseded /
            idempotency_mismatch / m2_only_denied)
        """
        ...
