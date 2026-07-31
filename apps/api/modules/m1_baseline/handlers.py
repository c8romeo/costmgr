"""apps.api.modules.m1_baseline.handlers — M1 baseline FastAPI routes (Story 1.2 + 2.1).

Story 1.2 (preserved):
- POST /api/v1/baseline/accounts/classification
- GET  /api/v1/baseline/accounts/classification

Story 2.1 (this revision, PRD §8.M1):
- POST   /api/v1/baseline/products            — register a product
- GET    /api/v1/baseline/products            — list products (paginated)
- GET    /api/v1/baseline/products/{id}       — single fetch
- PATCH  /api/v1/baseline/products/{id}       — partial update + soft-delete toggle

Each route carries `require_capability(Capability.PRODUCT)` (AC #6 defense
in depth). POST additionally gates `material` / `semi_product` types via
the in-service PRODUCT_MATERIAL check (service tenants cannot register
physical catalog items).

Error contract (AD-15 §4 `{code, message_ko, details, trace_id}`):
- 201 — successful POST
- 200 — successful GET / PATCH
- 403 PRODUCT_IMMUTABLE_FIELD — PATCH attempts to change `code`/`product_type`
- 403 INDUSTRY_NOT_SUPPORTED   — material/semi_product by service tenant
- 404 PRODUCT_NOT_FOUND        — single fetch miss
- 409 PRODUCT_CODE_DUPLICATE   — same (tenant, code) collision (AC #3)
- 422 INVALID_PRODUCT_CODE     — manual `code` does not match PREFIX-XXXX

Mirrors the inline-JSONResponse pattern from
`apps/api/modules/m0_onboarding/handlers.py` (Story 1.1/1.2).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, status
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
    ProductCreateRequest,
    ProductListResponse,
    ProductResponse,
    ProductUpdateRequest,
)
from apps.api.modules.m1_baseline.services.product_service import (
    InvalidProductCodeError,
    ProductCapabilityError,
    ProductCodeDuplicateError,
    ProductImmutableFieldError,
    ProductNotFoundError,
    ProductService,
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
    if (
        body.is_active is not None
        and body.model_dump(exclude_unset=True).keys() == {"is_active"}
    ):
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
    except ProductImmutableFieldError as err:
        return _err(
            status_code=status.HTTP_403_FORBIDDEN,
            code="PRODUCT_IMMUTABLE_FIELD",
            message_ko=f"{err.field} 필드는 생성 후 변경할 수 없습니다",
            details={"field": err.field},
            trace_id=err.trace_id,
        )

    return _product_to_response(row)
