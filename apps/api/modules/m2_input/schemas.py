"""apps.api.modules.m2_input.schemas — M2 monthly input Pydantic models (Story 3.1 + 3.2 + 3.3).

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

Story 3.2 (this revision — Task 2.3):
- Adds the FTE precision sub-schemas `PayTypeBreakdownResponse` and
  `PayrollSettingsResponse`.
- Extends `MonthlyInputRowCreate` / `MonthlyInputRowUpdate` /
  `MonthlyInputRowResponse` with the 7 FTE precision fields
  (`pay_type`, `monthly_salary_basis_krw`, `overtime_krw`, `welfare_krw`,
  `bonus_krw`, `retirement_reserve_krw`, `company_burden_rate`).
- Upgrades `FteDisplay` with `pay_type`, `breakdown`, `source_rows`,
  and `payroll_settings` so the [인원] tab can render the PRD §6.1
  인건비 5개 항목 breakdown.

Story 3.3 (Task 2.3 — this revision):
- Adds `WarningResponse` (code, severity, message_ko, details, stream,
  trace_id, timestamp) — mirrors the pure `Warning` NamedTuple.
- `MonthlyInputStateResponse` extended with:
  - `warnings: list[WarningResponse]` — sorted by severity ASC + closing_qty ASC
  - `is_blocked: bool` — `len(warnings) > 0` (PRD §A11 close-time rule)
  - `warnings_count: int` — `len(warnings)` (UI echo)
  - `top_n_severity: int` — currently 1 (most severe warning)
- `MonthlyInputRowUpdate` keeps `extra='forbid'` (Story 3.1 base) — PATCH
  on `warnings` / `is_blocked` triggers 400 INVALID_PAYLOAD via AC #7.

AD binds enforced here:
- AD-15 — snake_case field names; `extra="forbid"` Pydantic v2 config;
  Korean labels are user-facing data (not code identifiers).
- AD-8 — KRW is `int` (BIGINT); `company_burden_rate` is `Decimal`
  (NUMERIC(5,4)). Float drift is forbidden — `company_burden_rate`
  crosses the Python/TS boundary as a Decimal string.
- AD-1 — this file imports only from `packages.services.m2_input`
  (engine-independent) and `pydantic`.
- AD-13 — the schema mirrors what `MonthInputAdapter` will eventually
  normalize to `MonthlyInput`. For Story 3.1/3.2/3.3 the adapter is not
  yet written (Epic 4 first_calc), so the schema is the canonical
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
    # Stream + Mode (re-exported)  # noqa: ERA001
    "Stream",
    "Mode",
    "STREAM_LABELS_KO",
    "STREAMS_FOR_INDUSTRY",
    "MonthlyCompletionStatus",
    "StreamCompletionStatus",
    # Money type alias (AD-8)
    "KRW",
    # Story 3.2 sub-schemas
    "PayType",
    "PayTypeBreakdownResponse",
    "PayrollSettingsResponse",
    # Story 3.3 sub-schemas
    "WarningResponse",
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


# ── Story 3.2 — pay_type discriminator (PRD §6.1) ────────────────
# Literals aligned with `packages.services.m2_input.labor_conversion.PayType`.
PayType = str  # Literal["monthly", "daily"]


# ── Story 3.2 sub-schemas ─────────────────────────────────────────
class PayTypeBreakdownResponse(BaseModel):
    """PRD §6.1 인건비 5개 항목 breakdown.

    All amounts are KRW `int`. `total_krw` is the row's
    per-worker labor cost — `base + overtime + welfare + bonus +
    retirement_reserve × company_burden_rate`.

    AD-8: `company_burden_rate` flows as `Decimal` (NUMERIC(5,4));
    serialization on the JSONResponse layer encodes it as a string
    to avoid float drift.
    """

    model_config = ConfigDict(extra="forbid")

    base_krw: int
    overtime_krw: int
    welfare_krw: int
    bonus_krw: int
    retirement_reserve_krw: int
    retirement_burden_krw: int
    company_burden_rate: Decimal
    total_krw: int


class PayrollSettingsResponse(BaseModel):
    """Resolved payroll settings for the period's labor display.

    Mirrors `packages.services.m2_input.labor_conversion.PayrollSettings`
    (Story 3.2 §Task 1.2). `merge_payroll_settings` is the source — this
    shape is the wire format returned by `GET .../fte` (Task 3.4).

    AD-8: `monthly_salary_basis_krw` is BIGINT, `company_burden_rate`
    is NUMERIC(5,4) — Decimal across the boundary.
    """

    model_config = ConfigDict(extra="forbid")

    monthly_salary_basis_krw: int
    workdays_in_month: int
    standard_monthly_hours: int
    company_burden_rate: Decimal


# ── Story 3.3 — Warning response ─────────────────────────────────
class WarningResponse(BaseModel):
    """Single warning entry (PRD §A11 오류의 가시화 — Story 3.3).

    Mirrors `packages.services.m2_input.warnings.Warning` NamedTuple
    (pure kernel). The wire format is JSON-serializable:
    - `code` — one of `WarningCode` values (NEGATIVE_CLOSING_INVENTORY,
      OVERCAPACITY_OPERATING_RATE)
    - `severity` — error | warning | info (PRD §A11 hierarchy)
    - `message_ko` — Korean friendly message (PRD §V3·V5 literal)
    - `details` — free-form dict (product_id, closing_qty, etc.)
    - `stream` — the originating stream (sales, production, ...)
    - `trace_id` — request trace_id (for support)
    - `timestamp` — ISO-8601 UTC

    AC #7: server-side defense — `warnings` is NOT in `MonthlyInputRowUpdate`
    (which uses `extra="forbid"`). PATCH attempts return 400 INVALID_PAYLOAD.
    """

    model_config = ConfigDict(extra="forbid")

    code: str
    severity: str
    message_ko: str
    details: dict
    stream: str
    trace_id: str
    timestamp: datetime


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

    Story 3.2 (Task 2.3) extends the labor branch with `pay_type` +
    the 5 breakdown fields + `company_burden_rate`. Per-stream shape
    is enforced by `_validate_labor_shape` in the service layer
    (Task 3.1) — these fields are all OPTIONAL at the schema level
    so the same `MonthlyInputRowCreate` covers all 6 streams.

    Story 3.3 (Task 2.3): the schema retains `extra="forbid"`; the
    `warnings` / `is_blocked` fields are NOT in this model — they're
    only present in `MonthlyInputStateResponse` (read-only, computed).
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

    # Story 3.2 — labor precision fields (Story 3.2 §Task 2.3)
    pay_type: PayType | None = None
    monthly_salary_basis_krw: KRW | None = None
    overtime_krw: KRW | None = None
    welfare_krw: KRW | None = None
    bonus_krw: KRW | None = None
    retirement_reserve_krw: KRW | None = None
    company_burden_rate: Decimal | None = Field(
        default=None, ge=Decimal("0"), le=Decimal("1")
    )


class MonthlyInputRowUpdate(BaseModel):
    """PATCH a row — all fields optional (CR 1.1 idempotent no-op semantics).

    `exclude_unset=True` on `model_dump` is the magic that makes
    partial-update work without sending unchanged fields. The service
    layer computes the (before, after) snapshot for the audit row from
    `exclude_unset` + the DB-loaded row.

    Story 3.2 — adds the 7 FTE precision fields. The existing
    `*_krw` field constraint (ge=0) carries through.

    Story 3.3 (AC #7): `extra="forbid"` ensures that any PATCH attempt
    on `warnings` / `is_blocked` (computed fields) returns 400
    INVALID_PAYLOAD via Pydantic's `extra_fields_not_allowed` error.
    """

    model_config = ConfigDict(extra="forbid")

    qty: Decimal | None = Field(default=None, ge=0)
    unit_price_krw: KRW | None = None
    amount_krw: KRW | None = None
    workers: int | None = Field(default=None, ge=0)
    days_per_worker: int | None = Field(default=None, ge=0)
    daily_wage_krw: KRW | None = None
    memo: str | None = Field(default=None, max_length=500)

    # Story 3.2 — labor precision fields
    pay_type: PayType | None = None
    monthly_salary_basis_krw: KRW | None = None
    overtime_krw: KRW | None = None
    welfare_krw: KRW | None = None
    bonus_krw: KRW | None = None
    retirement_reserve_krw: KRW | None = None
    company_burden_rate: Decimal | None = Field(
        default=None, ge=Decimal("0"), le=Decimal("1")
    )


# ── Response ─────────────────────────────────────────────────
class MonthlyInputRowResponse(BaseModel):
    """Single row response — read shape.

    Story 3.2: mirrors the new labor precision fields on the ORM
    (`db_models.MonthlyInputRow` — Task 2.2).
    """

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

    # Story 3.2 — labor precision fields (Task 2.3)
    pay_type: str | None = None
    monthly_salary_basis_krw: int | None = None
    overtime_krw: int | None = None
    welfare_krw: int | None = None
    bonus_krw: int | None = None
    retirement_reserve_krw: int | None = None
    company_burden_rate: Decimal | None = None

    created_at: datetime
    updated_at: datetime


class FteDisplay(BaseModel):
    """FTE display for the [인원] tab (Story 3.1 surface — Story 3.2 precision).

    Story 3.1 only rendered the basis 환산 values. Story 3.2 (Task 3.4
    — `_compute_fte_for_state`) adds the full PRD §6.1 인건비 5개 항목
    breakdown + per-row source attribution + resolved payroll settings.

    Empty dict (no display) when the tenant has no labor rows for the
    period.

    AD-8 — Decimals cross the boundary as strings; service layer (Task
    3.3) normalizes through `Decimal.quantize(Decimal("0.0001"))`.
    """

    model_config = ConfigDict(extra="forbid")

    # ── Story 3.1 fields (kept, still populated for backward compat) ──
    total_workers: int
    total_days_per_worker: int
    total_daily_wage_krw: int
    fte_headcount: Decimal  # 2dp, ROUND_HALF_EVEN
    fte_wage_krw: int
    monthly_salary_basis_krw: int

    # ── Story 3.2 additions (Task 2.3) ────────────────────────────────
    # pay_type discriminator ('monthly' | 'daily') — source-of-truth
    # for which formula produced the breakdown.
    pay_type: str
    # PRD §6.1 인건비 5개 항목 + 1 derived burden_total.
    breakdown: PayTypeBreakdownResponse
    # Row attribution — counts (not the row data itself; reveals whether
    # the number is from 1 row or 20 in audit / UI debug).
    source_rows: int
    # Resolved payroll settings used for this period (override aware).
    payroll_settings: PayrollSettingsResponse


class MonthlyInputStateResponse(BaseModel):
    """Page-mount payload — GET /api/v2/monthly-input/{period}/state.

    Drives:
    - The horizontal tab strip (capability_mask)
    - The yellow dot per tab (completion.<stream>)
    - The [계산] button state (is_complete + missing)
    - The [인원] tab FTE display (fte_display — Story 3.1 read-only;
      Story 3.2 with full breakdown)
    - The [마감] button state (Story 3.3 — `is_blocked`)
    - The Korean warning toast + alert (Story 3.3 — `warnings[]`)

    Story 3.3 (Task 2.3) extends the response with:
    - `warnings: list[WarningResponse]` — sorted (severity ASC +
      closing_qty ASC for inventory)
    - `is_blocked: bool` — `len(warnings) > 0` (PRD §A11 close-time rule)
    - `warnings_count: int` — UI echo
    - `top_n_severity: int` — most severe warning ordinal (UI hint)

    Story 5.1 (Epic 5) extends the response with 3 opening-carry
    fields (PRD §F4.1):
    - `opening_inventory: dict[str, str]` — product_id_str → qty_str
      (Decimal serialization for cross-language drift prevention)
    - `opening_inventory_locked: bool` — `_locked` JSONB sub-key
      (False until first-row INSERT, then True)
    - `opening_inventory_lock_reason_ko: str | None` — Korean reason
      for the lock (default: "전월 기말 자동 이월")
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
    # Story 3.3 — warning aggregate (PRD §A11)
    warnings: list[WarningResponse] = Field(default_factory=list)
    is_blocked: bool = False
    warnings_count: int = 0
    top_n_severity: int = 0
    # Story 5.1 — opening inventory auto-carry fields (PRD §F4.1)
    opening_inventory: dict[str, str] = Field(default_factory=dict)
    opening_inventory_locked: bool = False
    opening_inventory_lock_reason_ko: str | None = None
