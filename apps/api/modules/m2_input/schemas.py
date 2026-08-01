"""apps.api.modules.m2_input.schemas — M2 monthly input Pydantic models (Story 3.1).

Pydantic v2 models for the M2 monthly input module.

Story 3.1 (this revision):
- `Stream` / `Mode` re-exported from `packages.services.m2_input.stream_completion`
  (single source of truth).
- `MonthlyInputRowCreate` / `MonthlyInputRowUpdate` for the POST / PATCH
  row endpoints.
- `MonthlyInputRowResponse` for GET state.
- `MonthlyInputStateResponse` for the page-mount payload.
- `FteDisplay` for the read-only [인원] tab FTE display.
- KRW NewType alias for AD-8 money parity (BIGINT KRW).

AD binds enforced here:
- AD-15 — snake_case field names; `extra="forbid"` Pydantic v2 config;
  Korean labels are user-facing data (not code identifiers).
- AD-8 — KRW is `int` (BIGINT).
- AD-1 — this file imports only from `packages.services.m2_input`
  (engine-independent) and `pydantic`.
- AD-13 — the schema mirrors what `MonthInputAdapter` will eventually
  normalize to `MonthlyInput`. For Story 3.1 the adapter is not yet
  written (Epic 4 first_calc), so the schema is the canonical
  user-input shape.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import NewType
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from packages.services.m2_input.stream_completion import (
    STREAM_LABELS_KO,
    STREAMS_FOR_INDUSTRY,
    MonthlyCompletionStatus,
    StreamCompletionStatus,
)

__all__ = [
    # Stream + Mode (re-exported)
    "Stream",
    "Mode",
    "STREAM_LABELS_KO",
    "STREAMS_FOR_INDUSTRY",
    "MonthlyCompletionStatus",
    "StreamCompletionStatus",
    # Money type alias (AD-8)
    "KRW",
    # Pydantic schemas
    "MonthlyInputRowCreate",
    "MonthlyInputRowUpdate",
    "MonthlyInputRowResponse",
    "FteDisplay",
    "MonthlyInputStateResponse",
]


# AD-8 KRW type alias — runtime no-op; used by mypy / ruff import-linter
# for cross-language drift detection (TS side mirrors `bigint`).
KRW = NewType("KRW", int)


# Stream + Mode literal types — Python `str` enum values.
# Backend canonical values per AD-15 (snake_case).
Stream = str  # Literal["orders","production","sales","purchases","expenses","labor"]
Mode = str  # Literal["month_total","daily"]


# ── Create / Update ─────────────────────────────────────────
class MonthlyInputRowCreate(BaseModel):
    """Create a new monthly input row (POST /rows).

    Story 3.1 AC #4: rows have (stream, product_id, day_no) tuple semantics:
    - month_total mode → day_no MUST be None
    - daily mode → day_no in [1, 31]
    - labor / expenses → product_id MUST be None (no FK)
    - orders / production / sales / purchases → product_id MUST be set
    - production → also requires MONTHLY_INPUT_PRODUCTION capability
      (enforced at the handler, not here)
    """

    model_config = ConfigDict(extra="forbid")

    stream: Stream
    product_id: UUID | None = None
    day_no: int | None = Field(default=None, ge=1, le=31)
    qty: Decimal | None = Field(default=None, ge=0)
    unit_price_krw: KRW | None = None
    amount_krw: KRW | None = None
    workers: int | None = Field(default=None, ge=0)
    days_per_worker: int | None = Field(default=None, ge=0)
    daily_wage_krw: KRW | None = None
    memo: str | None = Field(default=None, max_length=500)


class MonthlyInputRowUpdate(BaseModel):
    """PATCH a row — all fields optional (CR 1.1 idempotent no-op semantics).

    `exclude_unset=True` on `model_dump` is the magic that makes
    partial-update work without sending unchanged fields. The service
    layer computes the (before, after) snapshot for the audit row from
    `exclude_unset` + the DB-loaded row.
    """

    model_config = ConfigDict(extra="forbid")

    qty: Decimal | None = Field(default=None, ge=0)
    unit_price_krw: KRW | None = None
    amount_krw: KRW | None = None
    workers: int | None = Field(default=None, ge=0)
    days_per_worker: int | None = Field(default=None, ge=0)
    daily_wage_krw: KRW | None = None
    memo: str | None = Field(default=None, max_length=500)


# ── Response ─────────────────────────────────────────────────
class MonthlyInputRowResponse(BaseModel):
    """Single row response — read shape."""

    model_config = ConfigDict(extra="forbid")

    row_id: UUID
    period_id: UUID
    period_key: str
    stream: Stream
    product_id: UUID | None = None
    day_no: int | None = None
    qty: Decimal | None = None
    unit_price_krw: int | None = None
    amount_krw: int | None = None
    workers: int | None = None
    days_per_worker: int | None = None
    daily_wage_krw: int | None = None
    memo: str | None = None
    mode: Mode
    created_at: datetime
    updated_at: datetime


class FteDisplay(BaseModel):
    """Read-only FTE display for the [인원] tab (Story 3.2 hook surface).

    Story 3.1 only renders this; Story 3.2 will add the full
    labor cost calculation pipeline. The display is always populated
    when at least one labor row exists; empty dict (no display) when
    the tenant has no labor rows yet.
    """

    model_config = ConfigDict(extra="forbid")

    # Total inputs across all labor rows for the period (sum of each
    # row's (workers × days_per_worker)). Story 3.1 keeps it simple —
    # a single sum.
    total_workers: int
    total_days_per_worker: int
    total_daily_wage_krw: int
    # Computed
    fte_headcount: Decimal  # 2dp, ROUND_HALF_EVEN
    fte_wage_krw: int
    monthly_salary_basis_krw: int


class MonthlyInputStateResponse(BaseModel):
    """Page-mount payload — GET /api/v2/monthly-input/{period}/state.

    Drives:
    - The horizontal tab strip (capability_mask)
    - The yellow dot per tab (completion.<stream>)
    - The [계산] button state (is_complete + missing)
    - The read-only FTE display on the [인원] tab (fte_display)
    """

    model_config = ConfigDict(extra="forbid")

    period_key: str
    mode: Mode
    baseline_revision: int
    rows: list[MonthlyInputRowResponse]
    completion: dict[str, bool]  # stream name → bool
    is_complete: bool
    missing: list[str]  # Korean labels, ordered PRD §8.M2(b)
    capability_mask: list[str]  # sorted stream names visible for industry
    fte_display: FteDisplay | None = None