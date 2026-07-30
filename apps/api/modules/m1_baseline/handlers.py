"""apps.api.modules.m1_baseline.handlers — M1 baseline scaffold (Story 1.2).

Scaffold-only module. Full CRUD lands in Epic 2 (Story 2.x). For now this
provides:

- `POST /api/v1/baseline/accounts/classification` — set an account's
  `direct_indirect` / `fixed_variable` tag.
- `GET  /api/v1/baseline/accounts/classification` — return the per-tag
  count for the wizard's completion status.

Storage strategy (scaffold): rows live in the existing
`tenant_settings.baseline` JSONB namespace under
`{"account_classifications": [...]}` so we don't need a new Alembic
migration. Epic 2 will lift this into a proper `account_classifications`
table.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.db import get_session
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.modules.m0_onboarding.services.settings_service import (
    ForbiddenRoleError,
    SettingsService,
)
from apps.api.modules.m1_baseline.schemas import (
    AccountClassificationRequest,
    AccountClassificationResponse,
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


@router.post(
    "/accounts/classification",
    response_model=AccountClassificationResponse,
    status_code=status.HTTP_200_OK,
    summary="계정 분류 (직접/간접 · 고정/변동) 저장",
    description=(
        "Story 1.2 — Task 4.1. Scaffold endpoint. Stores the classification in "
        "`tenant_settings.baseline.account_classifications` (JSONB). Full CRUD "
        "lands in Epic 2 (Story 2.x)."
    ),
)
async def save_account_classification(
    body: AccountClassificationRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> AccountClassificationResponse:
    settings = await SettingsService(session).get_tenant_settings(tenant_id=ctx.tenant_id)
    baseline = dict(settings.baseline or {})
    rows: list[dict[str, Any]] = list(baseline.get("account_classifications") or [])

    # Upsert by account_id.
    target = next(
        (r for r in rows if r.get("account_id") == body.account_id), None
    )
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
    from datetime import UTC, datetime

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
    description="Story 1.2 — Task 4.1. Returns {direct_indirect, fixed_variable} counts.",
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