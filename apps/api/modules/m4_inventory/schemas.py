"""apps.api.modules.m4_inventory.schemas — Story 5.2 Pydantic schemas.

AD-15 envelope + CR 2.3 `extra='forbid'` discipline. All 4 NEW types
mirror the `apps/api/modules/m4_inventory/handlers.py` 4 routes.

Schemas:
1. `LedgerEventCreateRequest` — operator manual INSERT (recovery /
   backfill entry) on POST /api/v1/inventory/ledger/events.
2. `PeriodClosingResponse` — read-only closing projection on
   GET /api/v1/inventory/ledger/period-closing?period_key=...
3. `CarryChainResponse` — read-only chain walk on
   GET /api/v1/inventory/ledger/carry-chain?period_key=...&depth=N
4. `ReversalRequestCreate` — M4 reversal entrypoint body on
   POST /api/v1/inventory/ledger/reversal-requests.

AD-11 layering: this module is FastAPI-coupled (Pydantic v2); pure
helpers live in `packages/services/m4_inventory/`.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── 1. LedgerEventCreateRequest ───────────────────────────────
class LedgerEventCreateRequest(BaseModel):
    """POST /api/v1/inventory/ledger/events body.

    Operator manual INSERT (recovery / backfill entry). Pure kernel
    validates event_type (11-value whitelist) + period_key (AD-24
    pattern 'YYYY-MM') + qty (Decimal, nullable for non-quantitative
    events) at the service layer.

    CR 2.3: `extra='forbid'` — reject undeclared fields.

    AD-22 reversal fields: `reverses_event_id` + `correction_group_id`
    are only set when Epic 11 module authority inserts reversal rows.
    Manual operator INSERTs in 5-2 MUST NOT set these (Epic 11 scope).
    """

    model_config = ConfigDict(extra="forbid")

    product_id: uuid.UUID = Field(..., description="AD-18 single product identity SSOT")
    period_key: str = Field(..., description="AD-24 typed 'YYYY-MM' fiscal key")
    event_type: str = Field(
        ...,
        description=(
            "11-value whitelist (see INVENTORY_LEDGER_EVENT_TYPES in "
            "packages/services/m4_inventory/ledger.py)"
        ),
    )
    qty: Decimal | None = Field(
        default=None,
        description="NUMERIC(18,4) nullable; non-quantitative events may be null",
    )
    trace_id: uuid.UUID | None = Field(
        default=None,
        description="Optional override; service mints UUIDv7 if None",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional JSONB metadata (additional keys for audit context)",
    )

    @field_validator("period_key")
    @classmethod
    def _validate_period_key_format(cls, v: str) -> str:
        """AD-24 pattern check at the Pydantic boundary (defense-in-depth)."""
        import re

        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", v):
            raise ValueError(f"period_key {v!r} must match 'YYYY-MM' AD-24 typed pattern")
        return v


# ── 2. PeriodClosingResponse ──────────────────────────────────
class PeriodClosingResponse(BaseModel):
    """GET /api/v1/inventory/ledger/period-closing response.

    Read-only closing projection. `closing` is
    `dict[product_id_str → Decimal_str]` (json-serializable — AD-8).

    CR 2.3: `extra='forbid'`. Only the documented fields are accepted.
    """

    model_config = ConfigDict(extra="forbid")

    period_key: str
    closing: dict[str, str] = Field(
        default_factory=dict,
        description="product_id (str UUID) → closing_qty (str Decimal, AD-8 serialization)",
    )
    trace_id: str


# ── 3. CarryChainResponse ─────────────────────────────────────
class CarryChainEntry(BaseModel):
    """Single carry-chain row in the response."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    period_key: str
    qty: str | None
    inserted_at: str | None


class CarryChainResponse(BaseModel):
    """GET /api/v1/inventory/ledger/carry-chain response.

    `depth` echoes the effective walk depth (≤ INVENTORY_PERIOD_CHAIN_LIMIT=12).

    CR 2.3: `extra='forbid'`.
    """

    model_config = ConfigDict(extra="forbid")

    product_id: str
    period_key: str
    depth: int
    chain: list[CarryChainEntry]
    trace_id: str


# ── 4. ReversalRequestCreate ──────────────────────────────────
class ReversalRequestCreate(BaseModel):
    """POST /api/v1/inventory/ledger/reversal-requests body.

    M4 reversal entrypoint forward-fill (AD-22). Epic 11 module
    authority owns the actual reversal sequence INSERT. This body
    only triggers the audit marker emit + 501 forward-fill response
    until M11 ships.

    CR 2.3: `extra='forbid'`.
    """

    model_config = ConfigDict(extra="forbid")

    event_id: uuid.UUID = Field(
        ...,
        description="inventory_ledger.event_id of the row to reverse",
    )
    reason: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Human-readable reversal reason (Korean allowed)",
    )


# ── 5. Story 5.3 — Closing guard schemas (AC #2 + AC #4 + AC #5) ─
class ClosingGuardEvaluateRequest(BaseModel):
    """POST /api/v1/inventory/closing-guard/evaluate body.

    Read-only closing invariant check (PRD §F4.2 + §V3).
    Triggers `ClosingGuardService.evaluate_closing_guard(period_key)`.

    CR 2.3: `extra='forbid'`.
    """

    model_config = ConfigDict(extra="forbid")

    period_key: str = Field(..., description="AD-24 typed 'YYYY-MM' fiscal key")

    @field_validator("period_key")
    @classmethod
    def _validate_period_key_format(cls, v: str) -> str:
        """AD-24 pattern check at the Pydantic boundary (defense-in-depth)."""
        import re

        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", v):
            raise ValueError(f"period_key {v!r} must match 'YYYY-MM' AD-24 typed pattern")
        return v


class NegativeProductEntry(BaseModel):
    """Single product entry in the negative_products list."""

    model_config = ConfigDict(extra="forbid")

    product_id: str = Field(..., description="product_id UUID string")
    closing_qty: str = Field(..., description="Negative Decimal as AD-8 string")


class ClosingGuardEvaluateResponse(BaseModel):
    """POST /api/v1/inventory/closing-guard/evaluate response.

    Returns the ClosingInvariant NamedTuple fields in wire format:
    - `code`: 'CLOSING_OK' | 'NEGATIVE_CLOSING' | 'EMPTY_PERIOD'
    - `closing_per_product`: dict[product_id_str → Decimal_str]
    - `negative_products`: list of {product_id, closing_qty} (empty when OK/EMPTY)
    - `guard_enabled`: True if industry supports inventory guard
    - `banner_ko`: Korean message for UI display

    CR 2.3: `extra='forbid'`.
    """

    model_config = ConfigDict(extra="forbid")

    period_key: str
    code: str
    closing_per_product: dict[str, str] = Field(default_factory=dict)
    negative_products: list[NegativeProductEntry] = Field(default_factory=list)
    guard_enabled: bool
    banner_ko: str
    trace_id: str


class ClosingGuardCloseAttemptRequest(BaseModel):
    """POST /api/v1/inventory/closing-guard/close-attempt body.

    Close-time gate wire (additive over Story 4-2 is_blocked →
    409 MONTHLY_INPUT_BLOCKED). When invariant.code='NEGATIVE_CLOSING',
    returns 409 NEGATIVE_CLOSING_INVENTORY with the Korean banner.

    CR 2.3: `extra='forbid'`.
    """

    model_config = ConfigDict(extra="forbid")

    period_key: str = Field(..., description="AD-24 typed 'YYYY-MM' fiscal key")

    @field_validator("period_key")
    @classmethod
    def _validate_period_key_format(cls, v: str) -> str:
        import re

        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", v):
            raise ValueError(f"period_key {v!r} must match 'YYYY-MM' AD-24 typed pattern")
        return v


class ClosingGuardCloseAttemptResponse(BaseModel):
    """POST /api/v1/inventory/closing-guard/close-attempt response (200 OK).

    Returns `allowed: True` with the closing projection for UI echo.

    CR 2.3: `extra='forbid'`.
    """

    model_config = ConfigDict(extra="forbid")

    allowed: bool
    period_key: str
    closing_per_product: dict[str, str] = Field(default_factory=dict)
    invariant_code: str
    trace_id: str


__all__ = [
    "CarryChainEntry",
    "CarryChainResponse",
    "ClosingGuardEvaluateRequest",
    "ClosingGuardEvaluateResponse",
    "ClosingGuardCloseAttemptRequest",
    "ClosingGuardCloseAttemptResponse",
    "LedgerEventCreateRequest",
    "NegativeProductEntry",
    "PeriodClosingResponse",
    "ReversalRequestCreate",
]
