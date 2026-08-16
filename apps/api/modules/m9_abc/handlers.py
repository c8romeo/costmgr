"""apps.api.modules.m9_abc.handlers — M9 ABC scaffold (Story 1.2) + 9.1 EXTENSION.

Story 1.2 scaffold: driver-count endpoint needed by SettingsCompletionService.

Story 9.1 EXTENSION: 4 NEW endpoints for ABC 100% validation guard
(PRD §F9.1 verbatim + AD-15 §1 + capability gate):

  - POST /api/v1/abc/cost-pools       (Story 1.2 확장 — validate guard)
  - POST /api/v1/abc/activities       (NEW)
  - POST /api/v1/abc/drivers          (1.2 wire 확장 — POST 추가, ?validate=true)
  - POST /api/v1/abc/validate         (NEW 9-1 main entry point)

Capability gate: `Depends(require_capability(Capability.ABC_CALCULATION))`
Role gate: `Depends(require_any_role("owner", "member"))` (AD-10 4-role)
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.capability import (
    Capability,
    require_any_role,
    require_capability,
)
from apps.api.core.db import get_session
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.modules.m0_onboarding.services.settings_service import SettingsService
from apps.api.modules.m9_abc.schemas import (
    ActivityValidationRequest,
    CostPoolValidationRequest,
    DriverCountResponse,
    DriverRequest,
    DriverValidationRequest,
    ValidateRequest,
    ValidationLayerState,
    ValidationResponse,
)
from apps.api.modules.m9_abc.services.abc_validation_service import (
    AbcValidationService,
)

router = APIRouter(prefix="/api/v1/abc", tags=["m9-abc"])


# ── Story 1.2 scaffold (driver count + register) ─────────────────────


async def count_drivers(session: AsyncSession, *, tenant_id: uuid.UUID) -> int:
    """Return the number of ABC drivers registered for a tenant."""
    settings = await SettingsService(session).get_tenant_settings(tenant_id=tenant_id)
    abc = dict(settings.abc or {})
    drivers: list[Any] = list(abc.get("drivers") or [])
    return len(drivers)


@router.post(
    "/drivers",
    response_model=DriverCountResponse,
    status_code=status.HTTP_200_OK,
    summary="ABC 동인 등록",
    description=(
        "Story 1.2 — Task 4.2. Scaffold endpoint. Stores the driver in "
        "`tenant_settings.abc.drivers`. Story 9.1 EXTENSION: if "
        "`?validate=true` is set, the body MUST be `DriverValidationRequest` "
        "and the response is the validation guard result."
    ),
)
async def save_driver(
    body: DriverRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> DriverCountResponse:
    settings = await SettingsService(session).get_tenant_settings(tenant_id=ctx.tenant_id)
    abc = dict(settings.abc or {})
    drivers: list[dict[str, Any]] = list(abc.get("drivers") or [])
    drivers.append(
        {
            "driver_name": body.driver_name,
            "unit": body.unit,
            "practical_capacity_hours": body.practical_capacity_hours,
        }
    )
    abc["drivers"] = drivers
    settings.abc = abc
    settings.settings_version = settings.settings_version + 1
    from datetime import UTC, datetime

    settings.updated_at = datetime.now(tz=UTC)

    await session.flush()

    count = await count_drivers(session, tenant_id=ctx.tenant_id)
    return DriverCountResponse(driver_count=count)


@router.get(
    "/drivers",
    response_model=DriverCountResponse,
    status_code=status.HTTP_200_OK,
    summary="ABC 동인 카운트 조회",
    description="Story 1.2 — Task 4.2. Returns the driver count for completion status.",
)
async def get_driver_count(
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> DriverCountResponse:
    count = await count_drivers(session, tenant_id=ctx.tenant_id)
    return DriverCountResponse(driver_count=count)


# ── Story 9.1 NEW endpoints (ABC 100% validation guard) ──────────────


@router.post(
    "/cost-pools",
    response_model=ValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="원가풀 행 합 100% 가드 검증 (PRD §F9.1)",
    description=(
        "Story 9.1 — 원가풀 행 합 100% 가드 검증. "
        "PRD §F9.1 verbatim: '원가풀 행 합·활동 열 합·동인 합 모두 100% 가드'. "
        "Capability gate: ABC_CALCULATION (industry-agnostic). "
        "Role gate: owner or member."
    ),
    dependencies=[
        Depends(require_capability(Capability.ABC_CALCULATION)),
        Depends(require_any_role("owner", "member")),
    ],
)
async def validate_cost_pool_endpoint(
    body: CostPoolValidationRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> ValidationResponse:
    """원가풀 행 합 100% 가드 endpoint (Story 9.1)."""
    trace_id = str(uuid.uuid4())
    service = AbcValidationService(
        session,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        trace_id=trace_id,
    )
    state = await service.validate_cost_pool_only(
        department_id=body.department_id,
        allocation_pcts=body.allocation_pcts,
    )
    msg = None
    if not state.is_valid:
        msg = f"원가풀 행 합이 100%가 아닙니다 (현재 {state.sum_pct}%)"

    return ValidationResponse(
        cost_pool_id=body.department_id,
        activity_id="<none>",
        all_valid=state.is_valid,
        layers=[
            ValidationLayerState(
                target="cost_pool",
                sum_pct=str(state.sum_pct),
                count=state.department_count,
                is_valid=state.is_valid,
                hash=state.hash,
                message_ko=msg,
            ),
        ],
    )


@router.post(
    "/activities",
    response_model=ValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="활동 열 합 100% 가드 검증 (PRD §F9.1)",
    description=(
        "Story 9.1 — 활동 열 합 100% 가드 검증. "
        "Capability gate: ABC_CALCULATION (industry-agnostic)."
    ),
    dependencies=[
        Depends(require_capability(Capability.ABC_CALCULATION)),
        Depends(require_any_role("owner", "member")),
    ],
)
async def validate_activity_endpoint(
    body: ActivityValidationRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> ValidationResponse:
    """활동 열 합 100% 가드 endpoint (Story 9.1)."""
    trace_id = str(uuid.uuid4())
    service = AbcValidationService(
        session,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        trace_id=trace_id,
    )
    state = await service.validate_activity_only(
        cost_pool_id=body.cost_pool_id,
        activity_pcts=body.activity_pcts,
    )
    msg = None
    if not state.is_valid:
        msg = f"활동 열 합이 100%가 아닙니다 (현재 {state.sum_pct}%)"

    return ValidationResponse(
        cost_pool_id=body.cost_pool_id,
        activity_id="<none>",
        all_valid=state.is_valid,
        layers=[
            ValidationLayerState(
                target="activity",
                sum_pct=str(state.sum_pct),
                count=state.activity_count,
                is_valid=state.is_valid,
                hash=state.hash,
                message_ko=msg,
            ),
        ],
    )


@router.post(
    "/drivers/validate",
    response_model=ValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="동인 합 100% 가드 검증 (PRD §F9.1)",
    description=(
        "Story 9.1 — 동인 합 100% 가드 검증. "
        "Capability gate: ABC_CALCULATION (industry-agnostic)."
    ),
    dependencies=[
        Depends(require_capability(Capability.ABC_CALCULATION)),
        Depends(require_any_role("owner", "member")),
    ],
)
async def validate_driver_endpoint(
    body: DriverValidationRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> ValidationResponse:
    """동인 합 100% 가드 endpoint (Story 9.1)."""
    trace_id = str(uuid.uuid4())
    service = AbcValidationService(
        session,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        trace_id=trace_id,
    )
    state = await service.validate_driver_only(
        activity_id=body.activity_id,
        driver_pcts=body.driver_pcts,
    )
    msg = None
    if not state.is_valid:
        msg = f"동인 합이 100%가 아닙니다 (현재 {state.sum_pct}%)"

    return ValidationResponse(
        cost_pool_id="<none>",
        activity_id=body.activity_id,
        all_valid=state.is_valid,
        layers=[
            ValidationLayerState(
                target="driver",
                sum_pct=str(state.sum_pct),
                count=state.driver_count,
                is_valid=state.is_valid,
                hash=state.hash,
                message_ko=msg,
            ),
        ],
    )


@router.post(
    "/validate",
    response_model=ValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="3-layer 100% 가드 검증 (Story 9.1 main entry point)",
    description=(
        "Story 9.1 — 3-layer 100% 가드 동시 검증 (cost_pool + activity + driver). "
        "PRD §F9.1 verbatim '[계산]이 잠기는 것' 메커니즘. "
        "Capability gate: ABC_CALCULATION (industry-agnostic)."
    ),
    dependencies=[
        Depends(require_capability(Capability.ABC_CALCULATION)),
        Depends(require_any_role("owner", "member")),
    ],
)
async def validate_100_percent_guard_endpoint(
    body: ValidateRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> ValidationResponse:
    """3-layer 100% 가드 endpoint (Story 9.1 main entry point)."""
    trace_id = str(uuid.uuid4())
    service = AbcValidationService(
        session,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        trace_id=trace_id,
    )
    state = await service.validate_100_percent_guard(
        cost_pool=body.cost_pool,
        activities=body.activities,
        drivers=body.drivers,
        cost_pool_id=body.cost_pool_id,
        activity_id=body.activity_id,
    )

    layers: list[ValidationLayerState] = []
    if state.cost_pool is not None:
        layers.append(
            ValidationLayerState(
                target="cost_pool",
                sum_pct=str(state.cost_pool.sum_pct),
                count=state.cost_pool.department_count,
                is_valid=state.cost_pool.is_valid,
                hash=state.cost_pool.hash,
                message_ko=state.cost_pool_message_ko,
            ),
        )
    if state.activity is not None:
        layers.append(
            ValidationLayerState(
                target="activity",
                sum_pct=str(state.activity.sum_pct),
                count=state.activity.activity_count,
                is_valid=state.activity.is_valid,
                hash=state.activity.hash,
                message_ko=state.activity_message_ko,
            ),
        )
    if state.driver is not None:
        layers.append(
            ValidationLayerState(
                target="driver",
                sum_pct=str(state.driver.sum_pct),
                count=state.driver.driver_count,
                is_valid=state.driver.is_valid,
                hash=state.driver.hash,
                message_ko=state.driver_message_ko,
            ),
        )

    return ValidationResponse(
        cost_pool_id=body.cost_pool_id,
        activity_id=body.activity_id,
        all_valid=state.all_valid,
        layers=layers,
    )
