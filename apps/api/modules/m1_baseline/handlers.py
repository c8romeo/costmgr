"""apps.api.modules.m1_baseline.handlers — M1 baseline FastAPI routes (Story 1.2 + 2.1 + 2.2 + 2.3).

Story 1.2 (preserved):
- POST /api/v1/baseline/accounts/classification
- GET  /api/v1/baseline/accounts/classification

Story 2.1 (PRD §8.M1):
- POST   /api/v1/baseline/products            — register a product
- GET    /api/v1/baseline/products            — list products (paginated)
- GET    /api/v1/baseline/products/{id}       — single fetch
- PATCH  /api/v1/baseline/products/{id}       — partial update + soft-delete toggle

Story 2.2 (PRD §8.M1(b) — BOM matrix):
- GET    /api/v1/baseline/products/{id}/bom   — fetch BOM (lines + totals)
- PUT    /api/v1/baseline/products/{id}/bom   — bulk replace
- DELETE /api/v1/baseline/products/{id}/bom   — clear all rows

Story 2.3 (PRD §6.1 — item type change integrity guard):
- PATCH  /api/v1/baseline/products/{id}       — `product_type` change now
  CONDITIONAL: allowed iff BOM + ledger references = 0. Otherwise the
  request is rejected with 409 PRODUCT_TYPE_HAS_REFERENCES. `code` remains
  strictly immutable (403 PRODUCT_IMMUTABLE_FIELD).

Each route carries `require_capability(Capability.BOM)` (Story 2.2 AC #4
defense in depth). Mutating routes additionally require `require_role("owner")`.

Error contract (AD-15 §4 `{code, message_ko, details, trace_id}`):
- 200 — successful GET / PUT
- 204 — successful DELETE (clear)
- 403 INDUSTRY_NOT_SUPPORTED       — service tenant accessing BOM routes
- 403 FORBIDDEN_ROLE               — member/viewer attempting BOM mutation
- 403 PRODUCT_IMMUTABLE_FIELD      — `code` rejected (AD-18)
- 404 BOM_PARENT_NOT_FOUND         — parent product does not exist
- 404 PRODUCT_NOT_FOUND            — product row missing
- 409 PRODUCT_CODE_DUPLICATE       — same (tenant, code) collision
- 409 PRODUCT_TYPE_HAS_REFERENCES  — type change blocked by BOM/ledger refs
- 422 BOM_INVALID_PARENT_TYPE      — parent not in {product, semi_product}
- 422 BOM_INVALID_CHILD_TYPE       — child not in {material, semi_product}
- 422 BOM_DUPLICATE_CHILD          — same child twice in PUT payload
- 422 BOM_INVALID_RATIO            — ratio out of range / > 4 decimal places
- 422 INVALID_PRODUCT_CODE         — malformed manual code

Mirrors the inline-JSONResponse pattern from
`apps/api/modules/m0_onboarding/handlers.py` (Story 1.1/1.2).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.capability import (
    Capability,
    require_capability,
    require_role,
)
from apps.api.core.db import get_session
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.modules.m0_onboarding.services.settings_service import (
    SettingsService,
    TenantSettingsNotFoundError,
)
from apps.api.modules.m1_baseline.schemas import (
    AccountClassificationRequest,
    AccountClassificationResponse,
    BOMResponse,
    BOMSetRequest,
    ProductCreateRequest,
    ProductListResponse,
    ProductResponse,
    ProductUpdateRequest,
)
from apps.api.modules.m1_baseline.services.bom_service import (
    BOMChildNotFoundError,
    BOMDuplicateChildError,
    BOMInvalidChildTypeError,
    BOMInvalidParentTypeError,
    BOMInvalidRatioError,
    BOMParentNotFoundError,
    BOMService,
)
from apps.api.modules.m1_baseline.services.product_service import (
    InvalidProductCodeError,
    InvalidProductTypeError,
    ProductCapabilityError,
    ProductCodeDuplicateError,
    ProductImmutableFieldError,
    ProductNotFoundError,
    ProductService,
    ProductTypeHasReferencesError,
)

router = APIRouter(prefix="/api/v1/baseline", tags=["m1-baseline"])


async def count_account_classifications(
    session: AsyncSession, *, tenant_id: uuid.UUID
) -> dict[str, int]:
    """Return {direct_indirect, fixed_variable} counts for a tenant.

    Story 1.2 / SettingsCompletionService calls this. Returns zeros when
    the baseline JSONB is empty.
    """
    settings = await SettingsService(session).get_tenant_settings(tenant_id=tenant_id)
    baseline = dict(settings.baseline or {})
    rows: list[dict[str, Any]] = list(baseline.get("account_classifications") or [])
    di = sum(1 for r in rows if r.get("direct_indirect"))
    fv = sum(1 for r in rows if r.get("fixed_variable"))
    return {"direct_indirect": di, "fixed_variable": fv}


# ── Story 1.2 routes (preserved scaffold) ────────────────────
@router.post(
    "/accounts/classification",
    response_model=AccountClassificationResponse,
    status_code=status.HTTP_200_OK,
    summary="계정 분류 (직접/간접 · 고정/변동) 저장",
)
async def save_account_classification(
    body: AccountClassificationRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> AccountClassificationResponse:
    settings = await SettingsService(session).get_tenant_settings(tenant_id=ctx.tenant_id)
    baseline = dict(settings.baseline or {})
    rows: list[dict[str, Any]] = list(baseline.get("account_classifications") or [])
    target = next((r for r in rows if r.get("account_id") == body.account_id), None)
    if target is None:
        target = {"account_id": body.account_id}
        rows.append(target)
    if body.direct_indirect is not None:
        target["direct_indirect"] = body.direct_indirect
    if body.fixed_variable is not None:
        target["fixed_variable"] = body.fixed_variable
    baseline["account_classifications"] = rows
    settings.baseline = baseline
    settings.settings_version = settings.settings_version + 1
    settings.updated_at = datetime.now(tz=UTC)
    await session.flush()

    counts = await count_account_classifications(session, tenant_id=ctx.tenant_id)
    return AccountClassificationResponse(
        direct_indirect_count=counts["direct_indirect"],
        fixed_variable_count=counts["fixed_variable"],
    )


@router.get(
    "/accounts/classification",
    response_model=AccountClassificationResponse,
    status_code=status.HTTP_200_OK,
    summary="계정 분류 카운트 조회",
)
async def get_account_classification(
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> AccountClassificationResponse:
    counts = await count_account_classifications(session, tenant_id=ctx.tenant_id)
    return AccountClassificationResponse(
        direct_indirect_count=counts["direct_indirect"],
        fixed_variable_count=counts["fixed_variable"],
    )


# ── Helpers ──────────────────────────────────────────────────
async def _resolve_industry_for_capability(
    *, session: AsyncSession, tenant_id: uuid.UUID, trace_id: str
):
    """Resolve the tenant's industry for the in-service PRODUCT_MATERIAL gate.

    H6: only catch `TenantSettingsNotFoundError`. Other exceptions
    (DB outage, schema drift, programming errors) must propagate so the
    caller surfaces them as 500 — NOT a misleading 403
    INDUSTRY_NOT_SUPPORTED. Bad industry string in the JSONB is treated
    as no industry (conservative deny for material/semi_product).
    """
    try:
        row = await SettingsService(session, trace_id=trace_id).get_tenant_settings(
            tenant_id=tenant_id
        )
    except TenantSettingsNotFoundError:
        return None
    onboarding = dict(row.onboarding or {})
    industry_raw = onboarding.get("industry")
    if not industry_raw:
        return None
    from packages.services.m0_onboarding.industry_menu import Industry

    try:
        return Industry(industry_raw)
    except ValueError:
        return None


def _product_to_response(p) -> ProductResponse:
    """ORM-to-Pydantic conversion (kept module-local to avoid circular imports)."""
    return ProductResponse(
        id=p.id,
        tenant_id=p.tenant_id,
        product_type=p.product_type,
        code=p.code,
        name=p.name,
        unit=p.unit,
        unit_cost_krw=p.unit_cost_krw,
        unit_cost_usd=p.unit_cost_usd,
        description=p.description,
        is_active=p.is_active,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _err(
    *,
    status_code: int,
    code: str,
    message_ko: str,
    details: dict[str, Any],
    trace_id: str,
) -> JSONResponse:
    """AD-15 §4 envelope helper."""
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message_ko": message_ko,
            "details": details,
            "trace_id": trace_id,
        },
    )


def _format_type_references_message_ko(err: ProductTypeHasReferencesError) -> str:
    """Build the Korean error message for a type-change blocked by references.

    Story 2.3 / PRD §6.1 — UX requirement. The exception carries the counts
    (no DB access). The handler-side formatter keeps Korean wording in
    `_err` callers (consistent with the rest of the baseline module) and
    avoids burdening the service layer with UI strings (AD-11 layering).

    D1 (post-review): format pinned to AC #1 literal. AC #1 says:
    ``"BOM {N}건에서 참조 중 — 신규 품목 생성 후 참조 이관 후 삭제"``.
    We render this verbatim with the optional `· 수불 {N}건` suffix
    when ledger references exist (always 0 until Epic 5).
    """
    parts = [f"BOM {err.bom_count}건에서 참조 중"]
    if err.ledger_count > 0:
        parts.append(f"· 수불 {err.ledger_count}건")
    parts.append(" — 신규 품목 생성 후 참조 이관 후 삭제 (품목 유형은 참조 0건일 때만 변경 가능)")
    return "".join(parts)


# ── Story 2.1 routes ─────────────────────────────────────────
@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="품목 등록",
    dependencies=[
        Depends(require_capability(Capability.PRODUCT)),
        # H3 / AD-10 / T4.2 — owner role only.
        Depends(require_role("owner")),
    ],
)
async def create_product(
    body: ProductCreateRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
):
    trace_id = str(uuid.uuid4())
    industry = await _resolve_industry_for_capability(
        session=session, tenant_id=ctx.tenant_id, trace_id=trace_id
    )
    service = ProductService(session, trace_id=trace_id)
    try:
        row = await service.create_product(
            tenant_id=ctx.tenant_id,
            actor_id=ctx.user_id,
            industry=industry,
            body=body,
        )
    except ProductCapabilityError as err:
        return _err(
            status_code=status.HTTP_403_FORBIDDEN,
            code="INDUSTRY_NOT_SUPPORTED",
            message_ko="제조업 업종에서만 등록 가능한 유형입니다",
            details={
                "current_industry": err.current_industry.value if err.current_industry else None,
                "requested_type": err.requested_type.value,
            },
            trace_id=err.trace_id,
        )
    except InvalidProductCodeError as err:
        return _err(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="INVALID_PRODUCT_CODE",
            message_ko="잘못된 코드 형식입니다 (예: MAT-0042)",
            details={"code": err.code, "reason": err.reason},
            trace_id=err.trace_id,
        )
    except ProductCodeDuplicateError as err:
        return _err(
            status_code=status.HTTP_409_CONFLICT,
            code="PRODUCT_CODE_DUPLICATE",
            message_ko="이미 존재하는 코드입니다",
            details={
                "code": err.code,
                "product_id": str(err.existing_product_id) if err.existing_product_id else None,
            },
            trace_id=err.trace_id,
        )

    return _product_to_response(row)


@router.get(
    "/products",
    response_model=ProductListResponse,
    status_code=status.HTTP_200_OK,
    summary="품목 목록 (paginated, filterable)",
    dependencies=[Depends(require_capability(Capability.PRODUCT))],
)
async def list_products(
    product_type: str | None = None,
    is_active: bool | None = None,
    # M4: Pydantic Query validation. Outs limit/offset to FastAPI,
    # removing the in-service clamp that silently turned bad client
    # values into 1/1000. Mirrors Story 1.2 baseline patterns.
    limit: int = Query(100, ge=1, le=1000, description="페이지 크기 (1..1000)"),
    offset: int = Query(0, ge=0, description="오프셋 (>=0)"),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
):
    from packages.services.m1_baseline.schemas import ProductType

    parsed_type: ProductType | None = None
    if product_type is not None:
        try:
            parsed_type = ProductType(product_type)
        except ValueError:
            return _err(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="INVALID_PRODUCT_TYPE",
                message_ko="유효하지 않은 제품 유형입니다",
                details={"product_type": product_type},
                trace_id="",
            )

    service = ProductService(session, trace_id=str(uuid.uuid4()))
    items, total = await service.list_products(
        tenant_id=ctx.tenant_id,
        product_type=parsed_type,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    return ProductListResponse(
        items=[_product_to_response(p) for p in items],
        total=total,
    )


@router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="품목 단건 조회",
    dependencies=[Depends(require_capability(Capability.PRODUCT))],
)
async def get_product(
    product_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
):
    trace_id = str(uuid.uuid4())
    service = ProductService(session, trace_id=trace_id)
    try:
        row = await service.get_product(
            tenant_id=ctx.tenant_id,
            product_id=product_id,
        )
    except ProductNotFoundError as err:
        return _err(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_NOT_FOUND",
            message_ko="품목을 찾을 수 없습니다",
            details={"product_id": str(err.product_id)},
            trace_id=err.trace_id,
        )
    return _product_to_response(row)


@router.patch(
    "/products/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="품목 부분 수정 (이름, 단가, 활성화 등)",
    dependencies=[
        Depends(require_capability(Capability.PRODUCT)),
        # H3 / AD-10 / T4.2 — owner role only.
        Depends(require_role("owner")),
    ],
)
async def update_product(
    product_id: uuid.UUID,
    body: ProductUpdateRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
):
    trace_id = str(uuid.uuid4())
    service = ProductService(session, trace_id=trace_id)
    # H7: route `is_active` toggle to soft_delete_product to produce a
    # dedicated audit event (product_soft_deleted / product_reactivated).
    # If the body is ONLY `{is_active: false}`, skip update_product and
    # go straight to soft_delete_product. If mixed, run update_product
    # first for the metadata fields, then soft_delete_product.
    if body.is_active is not None and body.model_dump(exclude_unset=True).keys() == {"is_active"}:
        try:
            row = await service.soft_delete_product(
                tenant_id=ctx.tenant_id,
                actor_id=ctx.user_id,
                product_id=product_id,
                is_active=body.is_active,
            )
        except ProductNotFoundError as err:
            return _err(
                status_code=status.HTTP_404_NOT_FOUND,
                code="PRODUCT_NOT_FOUND",
                message_ko="품목을 찾을 수 없습니다",
                details={"product_id": str(err.product_id)},
                trace_id=err.trace_id,
            )
        return _product_to_response(row)

    try:
        # Metadata update path (audit-first, idempotent no-op skip).
        row = await service.update_product(
            tenant_id=ctx.tenant_id,
            actor_id=ctx.user_id,
            product_id=product_id,
            body=body,
        )
        # Soft-delete toggle is a separate audit event (CR 1.1 lesson).
        if body.is_active is not None:
            row = await service.soft_delete_product(
                tenant_id=ctx.tenant_id,
                actor_id=ctx.user_id,
                product_id=product_id,
                is_active=body.is_active,
            )
    except ProductNotFoundError as err:
        return _err(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUCT_NOT_FOUND",
            message_ko="품목을 찾을 수 없습니다",
            details={"product_id": str(err.product_id)},
            trace_id=err.trace_id,
        )
    except ProductTypeHasReferencesError as err:
        # Story 2.3 — type change blocked by BOM/ledger references (409).
        # Placed BEFORE `ProductImmutableFieldError` per AD-15 §4: more
        # specific exception first. (`code` is still strictly immutable;
        # `product_type` is now CONDITIONAL on ref-count == 0.)
        return _err(
            status_code=status.HTTP_409_CONFLICT,
            code="PRODUCT_TYPE_HAS_REFERENCES",
            message_ko=_format_type_references_message_ko(err),
            details={
                "product_id": str(err.product_id),
                "requested_type": err.requested_type.value,
                "bom_count": err.bom_count,
                "ledger_count": err.ledger_count,
                "total_count": err.total_count,
            },
            trace_id=err.trace_id,
        )
    except ProductImmutableFieldError as err:
        return _err(
            status_code=status.HTTP_403_FORBIDDEN,
            code="PRODUCT_IMMUTABLE_FIELD",
            message_ko=f"{err.field} 필드는 생성 후 변경할 수 없습니다",
            details={"field": err.field},
            trace_id=err.trace_id,
        )
    except InvalidProductTypeError as err:
        return _err(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="INVALID_PRODUCT_TYPE",
            message_ko=(
                "품목 유형은 null로 변경할 수 없습니다 (omit하여 변경하지 않거나, "
                "원하는 유형 값을 명시하세요)"
            ),
            details={"reason": err.reason},
            trace_id=err.trace_id,
        )

    return _product_to_response(row)


# ── Story 2.2 routes — BOM matrix (PRD §8.M1(b)) ──────────────


@router.get(
    "/products/{product_id}/bom",
    response_model=BOMResponse,
    status_code=status.HTTP_200_OK,
    summary="BOM 조회 (lines + 합계 + 완료 여부)",
    dependencies=[Depends(require_capability(Capability.BOM))],
)
async def get_bom(
    product_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
):
    """Story 2.2 AC #1 — fetch a parent's BOM (RLS-scoped).

    `is_complete` is derived at read time (CR 2.1 lesson — derived
    values must not be stored). `missing_ratio` is clamped at 0 (UX:
    "비중 합 100% 필요 (현재 X%)").
    """
    trace_id = str(uuid.uuid4())
    service = BOMService(session, trace_id=trace_id)
    try:
        bom = await service.get_bom(
            tenant_id=ctx.tenant_id,
            parent_product_id=product_id,
        )
    except BOMParentNotFoundError as err:
        return _err(
            status_code=status.HTTP_404_NOT_FOUND,
            code="BOM_PARENT_NOT_FOUND",
            message_ko="모품목을 찾을 수 없습니다",
            details={"parent_product_id": str(err.parent_product_id)},
            trace_id=err.trace_id,
        )
    except BOMInvalidParentTypeError as err:
        return _err(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="BOM_INVALID_PARENT_TYPE",
            message_ko="모품목은 제품 또는 반제품만 가능합니다",
            details={
                "parent_product_id": str(err.parent_product_id),
                "parent_type": err.parent_type.value,
                "allowed_parent_types": ["product", "semi_product"],
            },
            trace_id=err.trace_id,
        )
    return bom


@router.put(
    "/products/{product_id}/bom",
    response_model=BOMResponse,
    status_code=status.HTTP_200_OK,
    summary="BOM 일괄 저장 (bulk replace, 100% invariant atomic)",
    dependencies=[
        Depends(require_capability(Capability.BOM)),
        # H3 / AD-10 — owner-only mutation. member/viewer are read-only.
        Depends(require_role("owner")),
    ],
)
async def set_bom(
    product_id: uuid.UUID,
    body: BOMSetRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
):
    """Story 2.2 AC #2/AC #3 — bulk-replace the entire BOM atomically.

    Per CR 2.1 lesson: per-row endpoints would let the BOM dip below
    100% temporarily (between two PATCH calls). The 100% invariant must
    hold atomically — the bulk-replace PUT is the only mutation path.

    Idempotent no-op skip (CR 2.1): if the new payload exactly equals
    the stored state, the service returns the existing BOM WITHOUT
    emitting an audit row. The first write (stored empty) always emits.
    """
    trace_id = str(uuid.uuid4())
    service = BOMService(session, trace_id=trace_id)
    try:
        bom = await service.set_bom(
            tenant_id=ctx.tenant_id,
            actor_id=ctx.user_id,
            parent_product_id=product_id,
            body=body,
        )
    except BOMParentNotFoundError as err:
        return _err(
            status_code=status.HTTP_404_NOT_FOUND,
            code="BOM_PARENT_NOT_FOUND",
            message_ko="모품목을 찾을 수 없습니다",
            details={"parent_product_id": str(err.parent_product_id)},
            trace_id=err.trace_id,
        )
    except BOMChildNotFoundError as err:
        # L6 (Review): a child ID in the payload is not visible to the tenant.
        # Surfaced as 404 with a distinct code so the client can identify the
        # missing entity.
        return _err(
            status_code=status.HTTP_404_NOT_FOUND,
            code="BOM_CHILD_NOT_FOUND",
            message_ko="BOM 자식 품목을 찾을 수 없습니다",
            details={
                "child_product_id": str(err.child_product_id),
                "parent_product_id": str(err.parent_product_id),
            },
            trace_id=err.trace_id,
        )
    except BOMInvalidParentTypeError as err:
        return _err(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="BOM_INVALID_PARENT_TYPE",
            message_ko="모품목은 제품 또는 반제품만 가능합니다",
            details={
                "parent_product_id": str(err.parent_product_id),
                "parent_type": err.parent_type.value,
                "allowed_parent_types": ["product", "semi_product"],
            },
            trace_id=err.trace_id,
        )
    except BOMInvalidChildTypeError as err:
        return _err(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="BOM_INVALID_CHILD_TYPE",
            message_ko="BOM 자식 품목은 원자재 또는 반제품만 가능합니다",
            details={
                "child_product_id": str(err.child_product_id),
                "child_type": err.child_type.value,
                "allowed_types": ["material", "semi_product"],
            },
            trace_id=err.trace_id,
        )
    except BOMDuplicateChildError as err:
        return _err(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="BOM_DUPLICATE_CHILD",
            message_ko="동일한 자식 품목이 두 번 등록되었습니다",
            details={
                "duplicate_child_product_id": str(err.duplicate_child_product_id),
                "occurrences": err.occurrences,
            },
            trace_id=err.trace_id,
        )
    except BOMInvalidRatioError as err:
        return _err(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="BOM_INVALID_RATIO",
            message_ko="비중은 소수점 4자리까지 입력 가능합니다",
            details={
                "child_product_id": str(err.child_product_id),
                "ratio": str(err.ratio),
                "max_decimal_places": err.max_decimal_places,
            },
            trace_id=err.trace_id,
        )
    return bom


@router.delete(
    "/products/{product_id}/bom",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="BOM 전체 삭제 (이 제품 BOM 초기화)",
    dependencies=[
        Depends(require_capability(Capability.BOM)),
        Depends(require_role("owner")),
    ],
)
async def clear_bom(
    product_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
):
    """Story 2.2 — clear all BOM rows for a parent.

    Audit-first (`bom_cleared`). Empty BOM is a valid state
    (`is_complete=false`, [계산] disabled).
    """
    trace_id = str(uuid.uuid4())
    service = BOMService(session, trace_id=trace_id)
    try:
        await service.clear_bom(
            tenant_id=ctx.tenant_id,
            actor_id=ctx.user_id,
            parent_product_id=product_id,
        )
    except BOMParentNotFoundError as err:
        return _err(
            status_code=status.HTTP_404_NOT_FOUND,
            code="BOM_PARENT_NOT_FOUND",
            message_ko="모품목을 찾을 수 없습니다",
            details={"parent_product_id": str(err.parent_product_id)},
            trace_id=err.trace_id,
        )
    except BOMInvalidParentTypeError as err:
        return _err(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="BOM_INVALID_PARENT_TYPE",
            message_ko="모품목은 제품 또는 반제품만 가능합니다",
            details={
                "parent_product_id": str(err.parent_product_id),
                "parent_type": err.parent_type.value,
                "allowed_parent_types": ["product", "semi_product"],
            },
            trace_id=err.trace_id,
        )
    # L8 (Review): RFC 7231 says 204 must have an empty body. Use plain
    # `Response` instead of `JSONResponse(content=None)` which serializes
    # to the literal string `null`.
    return Response(status_code=status.HTTP_204_NO_CONTENT)
