"""apps.api.modules.m9_abc.handlers — M9 ABC scaffold (Story 1.2).

Scaffold-only. Full ABC engine lands in Epic 9 (Story 9.x). This module
provides the driver count read endpoint needed by SettingsCompletionService.

Storage strategy (scaffold): drivers live in `tenant_settings.abc.drivers`
JSONB array. Epic 9 will lift this into a proper `abc_drivers` table.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.db import get_session
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.modules.m0_onboarding.services.settings_service import SettingsService
from apps.api.modules.m9_abc.schemas import DriverCountResponse, DriverRequest

router = APIRouter(prefix="/api/v1/abc", tags=["m9-abc"])


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
        "`tenant_settings.abc.drivers`. Full CRUD lands in Epic 9 (Story 9.x)."
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