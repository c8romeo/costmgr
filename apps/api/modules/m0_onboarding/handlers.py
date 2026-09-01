"""apps.api.modules.m0_onboarding.handlers — FastAPI router for M0 onboarding.

Story 1.1 — Tasks 2.2 / 5.1.

Routes:
  POST /api/v1/tenant-settings/onboarding/industry
       — Update the tenant's industry. Returns the canonical menu + version.
  GET  /api/v1/tenant-settings
       — Read the full tenant settings aggregate (used by `useMenuContext`).

Errors (AD-15 contract — `{code, message_ko, details, trace_id}`):
  422  invalid `industry` value (Pydantic)
  403  FORBIDDEN_ROLE — non-owner (Decision §3)
  404  TENANT_SETTINGS_NOT_FOUND — defensive (F-22)
  409  INDUSTRY_LOCKED — A7 전진법 (AC #4)
  500  INCONSISTENT_SETTINGS — persisted JSONB is unparseable (F-10/15/16)

The router depends on Story 0.2's `get_tenant_context` for JWT decoding +
RLS wiring. `tenant_id` is NEVER read from the request body.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.db import get_session
from apps.api.core.jsonb_schemas import (
    OnboardingField,
    OnboardingValidationError,
)
from apps.api.core.tenant_context import (
    PreOnboardingUser,
    TenantContext,
    get_pre_onboarding_user,
    get_tenant_context,
)
from apps.api.modules.m0_onboarding.schemas import (
    AllocationCriteriaUpdateRequest,
    CompletionStatusResponse,
    CurrencyField,
    CurrencyLockedError,
    FiscalYearLockedError,
    FiscalYearStartField,
    IndustryUpdateRequest,
    IndustryUpdateResponse,
    LanguageField,
    OnboardingFieldSavedResponse,
    SignupCompleteRequest,
    SignupCompleteResponse,
    TenantSettingsResponse,
)
from apps.api.modules.m0_onboarding.services.settings_service import (
    ForbiddenRoleError,
    InconsistentSettingsError,
    IndustryLockedError,
    SettingsService,
    TenantSettingsNotFoundError,
)
from apps.api.modules.m0_onboarding.services.signup_service import (
    AlreadyHasTenantError,
    SignupService,
    TenantNameValidationError,
)
from packages.services.m0_onboarding.industry_menu import Industry

router = APIRouter(prefix="/api/v1/tenant-settings", tags=["m0-onboarding"])

# Phase 3-0 — atomic signup-completion router. Separate from
# `router` (tenant-settings) because the auth contract is different:
# accepts JWTs without `app_metadata.tenant_id` (pre-onboarding
# state), routed through `get_pre_onboarding_user` instead of
# `get_tenant_context`.
signup_router = APIRouter(prefix="/api/v1/onboarding", tags=["m0-onboarding-signup"])


# ── POST /api/v1/onboarding/complete-signup (Phase 3-0 NEW) ───
@signup_router.post(
    "/complete-signup",
    response_model=SignupCompleteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="회원가입 완료 — 원자적 테넌트 생성",
    description=(
        "Phase 3-0 (Epic 1 carry-over = auth contract). Frontend 가 "
        "`supabase.auth.signUp()` 으로 발급받은 JWT (이때는 "
        "`app_metadata.tenant_id` 가 비어있음) 를 Authorization 헤더에 "
        "실어 호출. 응답으로 받은 `tenant_id` 를 클라이언트 상태에 저장한 "
        "뒤 `supabase.auth.refreshSession()` 으로 새 JWT 를 받으면 "
        "`app_metadata.tenant_id` 가 채워진다. 한 트랜잭션에서 users + "
        "tenants + tenant_memberships + tenant_settings + audit_logs "
        "원자적 INSERT (PRD §F15.2 verbatim)."
    ),
    responses={
        201: {"description": "Tenant created successfully."},
        401: {"description": "Invalid/expired JWT (TENANT_FORBIDDEN)."},
        409: {"description": "ALREADY_HAS_TENANT — user already has a tenant."},
        422: {"description": "Invalid body (Pydantic) or tenant_name invalid."},
    },
)
async def complete_signup(
    body: SignupCompleteRequest,
    user: PreOnboardingUser = Depends(get_pre_onboarding_user),
    session: AsyncSession = Depends(get_session),
) -> SignupCompleteResponse:
    """Atomic tenant creation for fresh signups.

    The pre-onboarding JWT has `sub` (= user_id) + role, but no
    `tenant_id`. This endpoint creates the first tenant for the user
    in a single transaction.
    """
    trace_id = str(uuid.uuid4())
    service = SignupService(session, trace_id=trace_id)
    try:
        result = await service.complete_signup(
            user_id=user.user_id,
            user_email=user.email,
            tenant_name=body.tenant_name,
            industry=body.industry,
        )
    except TenantNameValidationError as e:
        from fastapi.responses import JSONResponse

        return JSONResponse(  # type: ignore[return-value]
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "code": "TENANT_NAME_INVALID",
                "message_ko": "사업장 이름이 잘못되었습니다",
                "details": {"reason": e.reason},
                "trace_id": e.trace_id,
            },
        )
    except AlreadyHasTenantError as e:
        from fastapi.responses import JSONResponse

        return JSONResponse(  # type: ignore[return-value]
            status_code=status.HTTP_409_CONFLICT,
            content={
                "code": "ALREADY_HAS_TENANT",
                "message_ko": "이미 테넌트에 속해 있어 회원가입을 완료할 수 없습니다",
                "details": {
                    "existing_tenant_id": str(e.existing_tenant_id),
                    "existing_role": e.existing_role,
                },
                "trace_id": e.trace_id,
            },
        )
    except IntegrityError as e:
        from fastapi.responses import JSONResponse

        return JSONResponse(  # type: ignore[return-value]
            status_code=status.HTTP_409_CONFLICT,
            content={
                "code": "SIGNUP_INTEGRITY_ERROR",
                "message_ko": "회원가입 중 무결성 오류가 발생했습니다",
                "details": {"reason": str(e.orig)},
                "trace_id": trace_id,
            },
        )

    return SignupCompleteResponse(
        tenant_id=result.tenant_id,
        role=result.role,  # type: ignore[arg-type]
        industry=result.industry,
        settings_version=result.settings_version,
        trace_id=result.trace_id,
    )


# ── POST /api/v1/tenant-settings/onboarding/industry ────────
@router.post(
    "/onboarding/industry",
    response_model=IndustryUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="업종 선택/변경 (4지선다)",
    description=(
        "Story 1.1 — AC #1, #4. Body: `{ industry: Industry }`. "
        "Owner-only. Within 7 days of the previous selection, the response "
        "carries the `X-Onboarding-Warning: initial-change-allowed-for-7-days` "
        "header (F-39-resolved: fires for both `initial` and `within_grace`). "
        "After 7 days or after the first calculation: 409 INDUSTRY_LOCKED."
    ),
)
async def update_industry(
    body: IndustryUpdateRequest,
    response: Response,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> IndustryUpdateResponse:
    trace_id = str(uuid.uuid4())
    service = SettingsService(session, trace_id=trace_id)
    try:
        (
            industry,
            version,
            is_initial,
            selected_at,
            warning_header,
            trace_id,
        ) = await service.update_industry(
            tenant_id=ctx.tenant_id,
            target_industry=body.industry,
            actor_id=ctx.user_id,
            role=ctx.role,
        )
    except ForbiddenRoleError as e:
        from fastapi.responses import JSONResponse

        return JSONResponse(  # type: ignore[return-value]
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "code": "FORBIDDEN_ROLE",
                "message_ko": "업종 변경은 owner 역할만 가능합니다",
                "details": {"role": e.role},
                "trace_id": e.trace_id,
            },
        )
    except IndustryLockedError as e:
        from fastapi.responses import JSONResponse

        # F-34: include decision_reason + days_since_selection so support can
        # diagnose A7 lock conditions without a separate audit-log query.
        return JSONResponse(  # type: ignore[return-value]
            status_code=status.HTTP_409_CONFLICT,
            content={
                "code": "INDUSTRY_LOCKED",
                "message_ko": "업종 변경은 다음 회계연도부터 가능합니다 (A7 전진법)",
                "details": {
                    "current_industry": e.current_industry.value,
                    "next_fiscal_year_start": e.next_fiscal_year_start,
                    "decision_reason": e.decision_reason,
                    "days_since_selection": e.days_since_selection,
                },
                "trace_id": e.trace_id,
            },
        )
    except InconsistentSettingsError as e:
        from fastapi.responses import JSONResponse

        return JSONResponse(  # type: ignore[return-value]
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": "INCONSISTENT_SETTINGS",
                "message_ko": "테넌트 설정 데이터가 손상되었습니다. 관리자에게 문의하세요",
                "details": {
                    "field": e.field,
                    "reason": e.reason,
                    "raw_value": str(e.raw_value),
                },
                "trace_id": e.trace_id,
            },
        )
    except TenantSettingsNotFoundError as e:
        from fastapi.responses import JSONResponse

        return JSONResponse(  # type: ignore[return-value]
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "code": "TENANT_SETTINGS_NOT_FOUND",
                "message_ko": "테넌트 설정을 찾을 수 없습니다. 관리자에게 문의하세요",
                "details": {"tenant_id": str(e.tenant_id)},
                "trace_id": e.trace_id,
            },
        )

    # F-39-resolved: warning header fires for BOTH `initial` AND `within_grace`.
    if warning_header:
        response.headers["X-Onboarding-Warning"] = "initial-change-allowed-for-7-days"

    # F-43: surface trace_id in success envelope for audit correlation.
    response.headers["X-Trace-Id"] = trace_id

    return IndustryUpdateResponse.from_industry(
        industry,
        settings_version=version,
        is_initial=is_initial,
        selected_at=selected_at,
        trace_id=trace_id,
    )


# ── GET /api/v1/tenant-settings ──────────────────────────────
@router.get(
    "",
    response_model=TenantSettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="테넌트 설정 조회",
    description=(
        "Story 1.1 — Task 5.1. Returns the full `tenant_settings` aggregate "
        "(onboarding / baseline / abc / ai JSONB namespaces) plus `industry` "
        "(sugar for `onboarding.industry`) and `settings_version` (AD-23)."
    ),
)
async def get_tenant_settings(
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> TenantSettingsResponse:
    service = SettingsService(session)
    try:
        settings_row = await service.get_tenant_settings(tenant_id=ctx.tenant_id)
    except TenantSettingsNotFoundError as e:
        # F-22: GET must map missing tenant_settings to a typed 404, not 500.
        from fastapi.responses import JSONResponse

        return JSONResponse(  # type: ignore[return-value]
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "code": "TENANT_SETTINGS_NOT_FOUND",
                "message_ko": "테넌트 설정을 찾을 수 없습니다. 관리자에게 문의하세요",
                "details": {"tenant_id": str(e.tenant_id)},
                "trace_id": e.trace_id,
            },
        )

    onboarding = dict(settings_row.onboarding or {})
    industry_raw = onboarding.get("industry")
    if industry_raw is not None:
        try:
            industry = Industry(industry_raw)
        except ValueError:
            # F-10: unknown persisted value — return None rather than crash.
            industry = None
    else:
        industry = None

    return TenantSettingsResponse(
        tenant_id=settings_row.tenant_id,
        industry=industry,
        settings_version=settings_row.settings_version,
        onboarding=onboarding,
        baseline=dict(settings_row.baseline or {}),
        abc=dict(settings_row.abc or {}),
        ai=dict(settings_row.ai or {}),
    )


# ── Story 1.2 — Settings Wizard endpoints ────────────────────
def _onboarding_field_error_response(exc: OnboardingValidationError) -> dict:
    """Map `OnboardingValidationError` → 400 JSONB_SCHEMA_VIOLATION payload."""
    return {
        "code": "JSONB_SCHEMA_VIOLATION",
        "message_ko": "온보딩 데이터 형식이 올바르지 않습니다",
        "details": {
            "errors": [{"field": e.field, "reason": e.reason, "value": e.value} for e in exc.errors]
        },
        "trace_id": exc.trace_id,
    }


def _build_completion_response(
    completion,
    trace_id: str,
    *,
    last_calc_date: str | None = None,
) -> CompletionStatusResponse:
    """Adapter — `CompletionStatus` (dataclass) → API Pydantic response.

    F-7: surfaces the actual stored values for fiscal_year_start / currency
    / industry so the frontend wizard can seed its pickers on first render.
    F-34: `last_calc_date` flows in from settings_row.onboarding so the UI
    can warn about the A7 lock before the user attempts a save.
    """
    return CompletionStatusResponse(
        fiscal_year_start_completed=completion.fiscal_year_start.completed,
        currency_completed=completion.currency.completed,
        language_completed=completion.language.completed,
        allocation_criteria_completed=(
            completion.direct_indirect.completed
            and completion.fixed_variable.completed
            and completion.drivers.completed
        ),
        direct_indirect_count=completion.direct_indirect.count or 0,
        fixed_variable_count=completion.fixed_variable.count or 0,
        drivers_count=completion.drivers.count or 0,
        drivers_required=completion.drivers_required,
        is_complete=completion.is_complete,
        missing=completion.missing,
        trace_id=trace_id,
        fiscal_year_start_value=completion.fiscal_year_start_value,
        currency_value=completion.currency_value,
        industry=completion.industry,
        last_calc_date=last_calc_date,
    )


@router.post(
    "/onboarding/fiscal-year-start",
    response_model=OnboardingFieldSavedResponse,
    status_code=status.HTTP_200_OK,
    summary="회계연도 시작월 저장 (A1)",
    description="Story 1.2 — Task 3.1. Pydantic-validated YYYY-MM. A7 lock after first calc.",
)
async def save_fiscal_year_start(
    body: FiscalYearStartField,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> OnboardingFieldSavedResponse:
    trace_id = str(uuid.uuid4())
    service = SettingsService(session, trace_id=trace_id)
    from fastapi.responses import JSONResponse

    try:
        field, value, version, completion, trace_id = await service.update_onboarding_field(
            tenant_id=ctx.tenant_id,
            field=OnboardingField.FISCAL_YEAR_START,
            value=body.fiscal_year_start,
            actor_id=ctx.user_id,
            role=ctx.role,
        )
    except ForbiddenRoleError as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "code": "FORBIDDEN_ROLE",
                "message_ko": "owner 역할만 설정을 변경할 수 있습니다",
                "details": {"role": e.role},
                "trace_id": e.trace_id,
            },
        )
    except FiscalYearLockedError as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "code": "FISCAL_YEAR_LOCKED",
                "message_ko": "회계연도 시작월 변경은 다음 회계연도부터 가능합니다 (A7 전진법)",
                "details": {"next_fiscal_year_start": e.next_fiscal_year_start},
                "trace_id": e.trace_id,
            },
        )
    except OnboardingValidationError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_onboarding_field_error_response(e),
        )

    return OnboardingFieldSavedResponse(
        field="fiscal_year_start",
        value=value,
        settings_version=version,
        is_complete=completion.is_complete,
        missing=completion.missing,
        trace_id=trace_id,
    )


@router.post(
    "/onboarding/currency",
    response_model=OnboardingFieldSavedResponse,
    status_code=status.HTTP_200_OK,
    summary="통화 저장 (A6)",
    description="Story 1.2 — Task 3.1. KRW | USD. A7 lock after first calc.",
)
async def save_currency(
    body: CurrencyField,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> OnboardingFieldSavedResponse:
    trace_id = str(uuid.uuid4())
    service = SettingsService(session, trace_id=trace_id)
    from fastapi.responses import JSONResponse

    try:
        field, value, version, completion, trace_id = await service.update_onboarding_field(
            tenant_id=ctx.tenant_id,
            field=OnboardingField.CURRENCY,
            value=body.currency,
            actor_id=ctx.user_id,
            role=ctx.role,
        )
    except ForbiddenRoleError as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "code": "FORBIDDEN_ROLE",
                "message_ko": "owner 역할만 설정을 변경할 수 있습니다",
                "details": {"role": e.role},
                "trace_id": e.trace_id,
            },
        )
    except CurrencyLockedError as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "code": "CURRENCY_LOCKED",
                "message_ko": "통화 변경은 다음 회계연도부터 가능합니다 (A7 전진법)",
                "details": {"next_fiscal_year_start": e.next_fiscal_year_start},
                "trace_id": e.trace_id,
            },
        )

    return OnboardingFieldSavedResponse(
        field="currency",
        value=value,
        settings_version=version,
        is_complete=completion.is_complete,
        missing=completion.missing,
        trace_id=trace_id,
    )


@router.post(
    "/onboarding/language",
    response_model=OnboardingFieldSavedResponse,
    status_code=status.HTTP_200_OK,
    summary="언어 저장 (NFR-18)",
    description="Story 1.2 — Task 3.1. MVP is ko-KR only (NFR-18).",
)
async def save_language(
    body: LanguageField,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> OnboardingFieldSavedResponse:
    trace_id = str(uuid.uuid4())
    service = SettingsService(session, trace_id=trace_id)
    field, value, version, completion, trace_id = await service.update_onboarding_field(
        tenant_id=ctx.tenant_id,
        field=OnboardingField.LANGUAGE,
        value=body.language,
        actor_id=ctx.user_id,
        role=ctx.role,
    )
    return OnboardingFieldSavedResponse(
        field="language",
        value=value,
        settings_version=version,
        is_complete=completion.is_complete,
        missing=completion.missing,
        trace_id=trace_id,
    )


@router.post(
    "/onboarding/allocation-criteria",
    response_model=OnboardingFieldSavedResponse,
    status_code=status.HTTP_200_OK,
    summary="배부기준 3종 카운트 저장",
    description="Story 1.2 — Task 3.3. Body: `{criterion, count}`. count ≥ 1.",
)
async def save_allocation_criteria(
    body: AllocationCriteriaUpdateRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> OnboardingFieldSavedResponse:
    trace_id = str(uuid.uuid4())
    service = SettingsService(session, trace_id=trace_id)
    from fastapi.responses import JSONResponse

    try:
        criterion, count, version, completion, trace_id = await service.update_allocation_criteria(
            tenant_id=ctx.tenant_id,
            criterion=body.criterion,
            count=body.count,
            actor_id=ctx.user_id,
            role=ctx.role,
        )
    except ForbiddenRoleError as e:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "code": "FORBIDDEN_ROLE",
                "message_ko": "owner 역할만 설정을 변경할 수 있습니다",
                "details": {"role": e.role},
                "trace_id": e.trace_id,
            },
        )

    return OnboardingFieldSavedResponse(
        field="allocation_criteria",
        value={"criterion": criterion, "count": count},
        settings_version=version,
        is_complete=completion.is_complete,
        missing=completion.missing,
        trace_id=trace_id,
    )


@router.get(
    "/completion",
    response_model=CompletionStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="설정 완료도 조회 (계산 잠금 상태)",
    description=(
        "Story 1.2 — Task 3.4. Returns the canonical completion status used by "
        "the [계산] button to render its disabled/enabled state + tooltip."
    ),
)
async def get_completion(
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> CompletionStatusResponse:
    trace_id = str(uuid.uuid4())
    service = SettingsService(session, trace_id=trace_id)
    try:
        completion, last_calc_date = await service.get_completion(tenant_id=ctx.tenant_id)
    except TenantSettingsNotFoundError as e:
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "code": "TENANT_SETTINGS_NOT_FOUND",
                "message_ko": "테넌트 설정을 찾을 수 없습니다",
                "details": {"tenant_id": str(e.tenant_id)},
                "trace_id": e.trace_id,
            },
        )
    return _build_completion_response(completion, trace_id, last_calc_date=last_calc_date)
