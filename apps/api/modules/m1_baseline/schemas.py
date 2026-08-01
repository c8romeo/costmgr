"""apps.api.modules.m1_baseline.schemas — M1 baseline Pydantic models (Story 1.2 + 2.1).

Pydantic v2 models for the M1 baseline module.

Story 1.2 (preserved): AccountClassificationRequest / Response used by the
settings wizard scaffold endpoint.

Story 2.1 (this revision):
- `ProductType` re-exported from `packages.services.m1_baseline.schemas`
  (single source of truth).
- `ProductCreateRequest`, `ProductUpdateRequest`, `ProductResponse`,
  `ProductListResponse` for the four product routes (POST / GET /
  GET-id / PATCH).
- `KRW` / `USD` NewType helpers + `MoneyKRW` / `MoneyUSD` Pydantic
  wrappers for unit cost — per AD-8 money types cross-language parity
  (BIGINT KRW, NUMERIC(18,2) USD).

AD binds enforced here:
- AD-15 — snake_case field names. Pydantic v2 config (`extra="forbid"`).
- AD-8 — KRW is `int` (BIGINT) and USD is `Decimal` (NUMERIC(18,2)). The
  service layer enforces the parity via the `KRW` / `USD` NewType aliases
  (no runtime effect, used by mypy / ruff import-linter for drift check).
- AD-1 — this file imports only from `packages.services.m1_baseline`
  (engine-independent) and `pydantic` (no DB / no clock / no random).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import NewType
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from packages.services.m1_baseline.schemas import (
    PRODUCT_TYPE_LABEL_KO,
    PRODUCT_TYPE_PREFIX,
    ProductType,
)

__all__ = [
    # Story 1.2 (preserved)
    "AccountClassificationRequest",
    "AccountClassificationResponse",
    # Story 2.1 — domain re-exports
    "ProductType",
    "PRODUCT_TYPE_PREFIX",
    "PRODUCT_TYPE_LABEL_KO",
    "KRW",
    "USD",
    # Story 2.1 — Pydantic schemas
    "MoneyKRW",
    "MoneyUSD",
    "ProductCreateRequest",
    "ProductUpdateRequest",
    "ProductResponse",
    "ProductListResponse",
    # Story 2.2 — BOM schemas
    "BOMRowInput",
    "BOMSetRequest",
    "BOMLineResponse",
    "BOMResponse",
]


# ── Story 1.2 — preserved scaffold models ────────────────────
class AccountClassificationRequest(BaseModel):
    """Body of POST /api/v1/baseline/accounts/classification.

    Story 1.2 Task 4.1 — scaffold endpoint that the wizard calls to set an
    account's `direct_indirect` / `fixed_variable` classification. The
    real Epic 2 module will move this into a full account CRUD surface.
    """

    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(..., description="Logical account id (UUID string).")
    direct_indirect: str | None = Field(
        default=None,
        description="`direct` | `indirect` (null = unclassified).",
    )
    fixed_variable: str | None = Field(
        default=None,
        description="`fixed` | `variable` (null = unclassified).",
    )


class AccountClassificationResponse(BaseModel):
    """Body of GET /api/v1/baseline/accounts/classification."""

    model_config = ConfigDict(extra="forbid")

    direct_indirect_count: int = Field(
        ..., description="Number of accounts with `direct_indirect` set."
    )
    fixed_variable_count: int = Field(
        ..., description="Number of accounts with `fixed_variable` set."
    )


# ── Money types (AD-8) — NewType aliases + Pydantic wrappers ──
# KRW: stored as BIGINT (no fractional won). USD: stored as NUMERIC(18,2).
# NewTypes carry no runtime semantics — they're for type-checkers + drift
# detection in linters.
KRW = NewType("KRW", int)
USD = NewType("USD", Decimal)


class MoneyKRW(BaseModel):
    """KRW amount wrapper carrying non-negative constraint (AD-8).

    Use this for input validation when the endpoint needs to *carry* the
    value as a nested object (e.g. service-to-service calls). The HTTP
    boundary uses plain `int` (BIGINT) on `ProductCreateRequest` directly.
    """

    model_config = ConfigDict(extra="forbid")

    value: int = Field(..., ge=0, description="KRW amount (non-negative integer, BIGINT in DB).")


class MoneyUSD(BaseModel):
    """USD amount wrapper (AD-8 — NUMERIC(18,2), 2 decimal places)."""

    model_config = ConfigDict(extra="forbid")

    value: Decimal = Field(
        ...,
        ge=Decimal("0"),
        max_digits=18,
        decimal_places=2,
        description="USD amount (non-negative, 2 decimal places, NUMERIC(18,2) in DB).",
    )


# ── Product CRUD schemas (Story 2.1 — Task 1.1) ──────────────
# Bound to `apps/api/modules/m1_baseline/handlers.py` and consumed by
# `ProductService`.
#
# Immutable-after-create fields:
# - `code` (PRD §8.M1 + AD-18 single product identity)
# - `product_type` (Story 2.3 territory for type-change integrity guard)
#
# These are explicitly excluded from ProductUpdateRequest; the service
# maps any attempt to set them via PATCH to 403 PRODUCT_IMMUTABLE_FIELD.


class ProductCreateRequest(BaseModel):
    """Body of POST /api/v1/baseline/products (AC #1).

    Optional `code` allows the form to either auto-generate or supply a
    manual code. If absent, the service generates the next sequence
    number for (tenant_id, product_type).

    `unit_cost_krw` / `unit_cost_usd` are stored per AD-8 (BIGINT KRW,
    NUMERIC(18,2) USD). Either (or both) may be set per the tenant's
    dual-currency mode (Story 1.2 wizard).
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=200, description="제품/품목 이름 (1..200자).")
    product_type: ProductType = Field(..., description="5지선다 enum (제품·반제품·원자재·상품·서비스).")
    code: str | None = Field(
        default=None,
        max_length=20,
        description="수동 코드 (선택). 미입력 시 서비스가 next-sequence를 자동 생성.",
    )
    unit: str | None = Field(default=None, max_length=20, description="단위 (EA, KG, BOX 등).")
    unit_cost_krw: int | None = Field(
        default=None,
        ge=0,
        description="단가 (KRW). BIGINT. 미설정 시 null.",
    )
    unit_cost_usd: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        max_digits=18,
        decimal_places=2,
        description="단가 (USD). NUMERIC(18,2). 미설정 시 null.",
    )
    description: str | None = Field(default=None, max_length=2000, description="설명 (최대 2000자).")


class ProductUpdateRequest(BaseModel):
    """Body of PATCH /api/v1/baseline/products/{product_id} (AC #4).

    All fields optional. `is_active` is the soft-delete toggle (AC #5) —
    when present, the handler routes to `soft_delete_product` to produce
    a dedicated audit event (`product_soft_deleted` /
    `product_reactivated`) per CR 1.1 lesson.

    `code` and `product_type` ARE declared here so Pydantic accepts them
    on the wire. The service layer then rejects them with 403
    PRODUCT_IMMUTABLE_FIELD (H4: the 422 path was unreachable because
    `extra="forbid"` blocked them at validation time). Keep
    `extra="forbid"` so unknown fields still 422.
    """

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    unit: str | None = Field(default=None, max_length=20)
    unit_cost_krw: int | None = Field(default=None, ge=0)
    unit_cost_usd: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        max_digits=18,
        decimal_places=2,
    )
    description: str | None = Field(default=None, max_length=2000)
    # AC #5: soft-delete toggle. Routed to soft_delete_product by handler.
    is_active: bool | None = Field(
        default=None, description="False = 비활성(soft-delete), True = 활성."
    )
    # AC #4: immutable fields. Service rejects attempts to set them.
    code: str | None = Field(
        default=None,
        max_length=20,
        description="Immutable. Service rejects with 403 PRODUCT_IMMUTABLE_FIELD.",
    )
    # Story 2.3 / P5 (post-review): `product_type` is **conditionally**
    # mutable (allowed iff BOM+ledger references = 0). The schema stays
    # optional so partial-update semantics work (omit = no change), but
    # an explicit `null` value is rejected by the service layer with
    # a typed `InvalidProductTypeError` (422 INVALID_PRODUCT_TYPE).
    # Cannot "clear" the type — every product must have one.
    product_type: ProductType | None = Field(
        default=None,
        description="품목 유형 (omit = 변경 없음). null 명시 시 INVALID_PRODUCT_TYPE (422).",
    )


class ProductResponse(BaseModel):
    """Response body for GET / POST / PATCH (single product)."""

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(..., description="UUID v7 (AD-15 §3, products PK).")
    tenant_id: UUID = Field(..., description="UUID v4 (AD-15 §3 variance, JWT-derived).")
    product_type: ProductType
    code: str = Field(..., description="형식: PREFIX-XXXX (e.g. MAT-0042).")
    name: str
    unit: str | None
    unit_cost_krw: int | None
    unit_cost_usd: Decimal | None
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    """Response body for GET /api/v1/baseline/products (paginated)."""

    model_config = ConfigDict(extra="forbid")

    items: list[ProductResponse]
    total: int = Field(..., ge=0, description="Total rows matching the filter (pre-pagination).")


# ── BOM schemas (Story 2.2 — Task 3.3) ────────────────────────
# Mirror `packages.services.m1_baseline.bom_validation` (pure) for the
# wire boundary. Pydantic v2 enforces NUMERIC(7,4) precision here, before
# the service layer runs `quantize_ratio` as defense-in-depth.


class BOMRowInput(BaseModel):
    """A single BOM row in the PUT payload (AC #2/AC #8).

    `ratio` is `NUMERIC(7,4)` — 4 decimal places, max 100.0000, min
    0.0001 (Pydantic `gt=0, le=100` + `max_digits=7, decimal_places=4`).
    The Pydantic constraints surface 422 BOM_INVALID_RATIO BEFORE the
    service runs. The service still calls `quantize_ratio` on the value
    as defense-in-depth (Story 0.4 chunk-B Decimal.set parity).
    """

    model_config = ConfigDict(extra="forbid")

    child_product_id: UUID = Field(
        ...,
        description="자식 품목 UUID (PRD §6.1 — material 또는 semi_product 만 허용).",
    )
    ratio: Decimal = Field(
        ...,
        gt=Decimal("0"),
        le=Decimal("100"),
        max_digits=7,
        decimal_places=4,
        description="비중 (%). NUMERIC(7,4) — 4 decimal places, max 100.0000.",
    )


class BOMSetRequest(BaseModel):
    """Body of PUT /api/v1/baseline/products/{product_id}/bom (AC #2).

    Bulk-replace semantics: the entire BOM is replaced atomically.
    - `lines=[]` is allowed (empty BOM, `is_complete=false`).
    - Max 500 rows per BOM (PRD §8.M1 sanity cap; real BOMs are 10-30 rows).
    - Duplicate `child_product_id` → 422 BOM_DUPLICATE_CHILD (service-level).
    """

    model_config = ConfigDict(extra="forbid")

    # L3 (Review): named constant for TS/Python parity. Drift-checked by
    # `tests/integration/test_bom_validation_consistency.py` (mirror suite).
    MAX_BOM_ROWS: int = 500

    lines: list[BOMRowInput] = Field(
        default_factory=list,
        max_length=MAX_BOM_ROWS,
        description="BOM 행 배열 (max 500). 빈 배열은 빈 BOM (sum=0%, is_complete=false).",
    )


class BOMLineResponse(BaseModel):
    """A single BOM row in the GET/PUT response (AC #1).

    Carries child metadata denormalized (code/name/product_type/is_active)
    so the matrix UI doesn't need a separate JOIN. `child_is_active=false`
    is shown with a muted "(비활성)" overlay (AC #9).
    """

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(..., description="BOM 행 UUID v7.")
    child_product_id: UUID
    child_code: str
    child_name: str
    child_product_type: ProductType
    child_is_active: bool
    ratio: Decimal
    created_at: datetime
    updated_at: datetime


class BOMResponse(BaseModel):
    """Body of GET / PUT / DELETE /api/v1/baseline/products/{product_id}/bom (AC #1).

    `is_complete` is a **derived** flag — computed at read time as
    `sum_ratios(lines) == TARGET_TOTAL`. The DB does NOT store it
    (CR 2.1 lesson: derived values invite drift).

    `missing_ratio` is `max(100 - total_ratio, 0)` — the "{missing}% 부족"
    UX message. Clamped at zero (over-100 still reports 0).
    """

    model_config = ConfigDict(extra="forbid")

    parent_product_id: UUID
    parent_code: str
    parent_name: str
    parent_product_type: ProductType
    parent_is_active: bool
    lines: list[BOMLineResponse]
    total_ratio: Decimal = Field(
        ..., description="비중 합계 (NUMERIC(7,4) precision)."
    )
    is_complete: bool = Field(
        ...,
        description="A6 invariant — True iff total_ratio == Decimal('100.0000').",
    )
    missing_ratio: Decimal = Field(
        ...,
        description="100 - total_ratio (clamped at 0). UI '{missing}% 부족' 표시용.",
    )
    updated_at: datetime | None
