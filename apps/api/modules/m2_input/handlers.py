"""apps.api.modules.m2_input.handlers — M2 monthly input FastAPI routes (Story 3.1).

PRD §8.M2 — six-stream monthly input capture.

Routes:
- GET  /api/v2/monthly-input/{period_key}/state
    → Page-mount payload (rows + completion + capability_mask + fte_display)
- POST /api/v2/monthly-input/{period_key}/rows
    → Save (insert or update) a row; audit-first + idempotent no-op
- PATCH /api/v2/monthly-input/{period_key}/rows/{row_id}
    → Partial update with audit-first + idempotent no-op
- DELETE /api/v2/monthly-input/{period_key}/rows/{row_id}
    → Delete + audit (PRD §8.M2 user-input, not ledger)
- POST /api/v2/monthly-input/{period_key}/mode
    → Toggle month_total ↔ daily (no baseline_revision bump)

Defense in depth:
- All routes: `get_tenant_context` (JWT → TenantContext)
- Mutating routes: `require_role("owner")` (AD-10)
- Production stream gate: enforced in service layer (per-row check,
  not a router-level dependency because the gate depends on the request
  body `stream` field). Service raises `MonthlyInputCapabilityError`
  → 403 INDUSTRY_NOT_SUPPORTED envelope.

Error contract (AD-15 §4 `{code, message_ko, details, trace_id}`):
- 200 — successful GET / POST / PATCH
- 204 — successful DELETE
- 400 MONTHLY_INPUT_INVALID_PAYLOAD — semantic validation failure
- 403 FORBIDDEN_ROLE                  — member/viewer mutation
- 403 INDUSTRY_NOT_SUPPORTED          — service tenant writing production
- 404 MONTHLY_INPUT_NOT_FOUND         — row or period missing
- 409 MONTH_INPUT_PERIOD_LOCKED       — first_calc lock (Epic 4)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.capability import require_role
from apps.api.core.db import get_session
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.modules.m0_onboarding.services.settings_service import (
    SettingsService,
    TenantSettingsNotFoundError,
)
from apps.api.modules.m2_input.schemas import (
    MonthlyInputRowCreate,
    MonthlyInputRowUpdate,
    MonthlyInputStateResponse,
)
from apps.api.modules.m2_input.services import MonthlyInputService
from apps.api.modules.m2_input.services.monthly_input_service import (
    MonthlyInputCapabilityError,
)
from packages.services.m0_onboarding.industry_menu import Industry

router = APIRouter(prefix="/api/v2/monthly-input", tags=["m2-input"])


# ── Industry resolution (for capability gate) ────────────────
async def _resolve_industry(
    *, session: AsyncSession, tenant_id: uuid.UUID
) -> Industry | None:
    """Read the tenant's industry from `tenant_settings.onboarding.industry`.

    Returns None if no tenant_settings row exists (e.g. tenant created
    but M0 wizard not finished yet). The service layer treats None as
    "most restrictive" — service tenant defaults. Defensive: only catch
    `TenantSettingsNotFoundError`; let DB / schema errors propagate.
    """
    try:
        row = await SettingsService(session).get_tenant_settings(
            tenant_id=tenant_id
        )
    except TenantSettingsNotFoundError:
        return None
    onboarding = dict(row.onboarding or {})
    industry_raw = onboarding.get("industry")
    if not industry_raw:
        return None
    try:
        return Industry(industry_raw)
    except ValueError:
        return None


# ── GET /state ────────────────────────────────────────────────
@router.get(
    "/{period_key}/state",
    response_model=MonthlyInputStateResponse,
    status_code=status.HTTP_200_OK,
    summary="월 입력 페이지 마운트 페이로드 (탭 + 노란 점 + FTE)",
)
async def get_monthly_input_state(
    period_key: str,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> MonthlyInputStateResponse:
    """Return the page-mount payload.

    Drives the horizontal tab strip + yellow dots + [계산] button state
    + read-only FTE display. RLS-scoped via `tenant_id` from JWT.
    """
    industry = await _resolve_industry(
        session=session, tenant_id=ctx.tenant_id
    )
    trace_id = str(uuid.uuid4())
    service = MonthlyInputService(
        session,
        tenant_id=ctx.tenant_id,
        industry=industry,
        trace_id=trace_id,
    )
    return await service.get_state(period_key=period_key)


# ── POST /rows ────────────────────────────────────────────────
@router.post(
    "/{period_key}/rows",
    response_model=MonthlyInputStateResponse,
    status_code=status.HTTP_200_OK,
    summary="월 입력 행 저장 (insert 또는 update) + 완료 게이트 재계산",
)
async def save_monthly_input_row(
    period_key: str,
    body: MonthlyInputRowCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _role: TenantContext = Depends(require_role("owner")),
) -> MonthlyInputStateResponse:
    """Save a row — insert or update with audit-first + idempotent no-op.

    Returns the full state payload (rows + completion + missing) so the
    frontend can clear the yellow dot + update the [계산] button state
    without an extra round-trip.
    """
    industry = await _resolve_industry(
        session=session, tenant_id=ctx.tenant_id
    )
    trace_id = str(uuid.uuid4())
    service = MonthlyInputService(
        session,
        tenant_id=ctx.tenant_id,
        industry=industry,
        trace_id=trace_id,
    )
    try:
        row, completion, missing = await service.save_row(
            period_key=period_key,
            payload=body,
            actor_id=ctx.user_id,
        )
    except MonthlyInputCapabilityError as exc:
        # Service-level 403 (production stream + non-manufacturing industry).
        # Returned inline (mirrors Story 2.1 PRODUCT_MATERIAL pattern).
        return _industry_not_supported_response(exc)

    # Wrap the row + completion + missing into the full state response.
    # (Spec returns the full state so the frontend doesn't round-trip.)
    return await service.get_state(period_key=period_key)


# ── PATCH /rows/{row_id} ──────────────────────────────────────
@router.patch(
    "/{period_key}/rows/{row_id}",
    response_model=MonthlyInputStateResponse,
    status_code=status.HTTP_200_OK,
    summary="월 입력 행 부분 수정 (CR 1.1 idempotent no-op)",
)
async def update_monthly_input_row(
    period_key: str,
    row_id: uuid.UUID,
    body: MonthlyInputRowUpdate,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _role: TenantContext = Depends(require_role("owner")),
) -> MonthlyInputStateResponse:
    """PATCH a row — partial update with audit-first + idempotent no-op.

    `exclude_unset=True` semantics are honored at the Pydantic boundary
    (`body.model_dump(exclude_unset=True)`).
    """
    industry = await _resolve_industry(
        session=session, tenant_id=ctx.tenant_id
    )
    trace_id = str(uuid.uuid4())
    service = MonthlyInputService(
        session,
        tenant_id=ctx.tenant_id,
        industry=industry,
        trace_id=trace_id,
    )
    await service.update_row(
        period_key=period_key,
        row_id=row_id,
        payload=body,
        actor_id=ctx.user_id,
    )
    return await service.get_state(period_key=period_key)


# ── DELETE /rows/{row_id} ─────────────────────────────────────
@router.delete(
    "/{period_key}/rows/{row_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="월 입력 행 삭제 + audit",
)
async def delete_monthly_input_row(
    period_key: str,
    row_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _role: TenantContext = Depends(require_role("owner")),
) -> Response:
    """Delete a row — PRD §8.M2 user-input, NOT a ledger.

    Audit row written BEFORE the data DELETE (AD-2).
    """
    industry = await _resolve_industry(
        session=session, tenant_id=ctx.tenant_id
    )
    trace_id = str(uuid.uuid4())
    service = MonthlyInputService(
        session,
        tenant_id=ctx.tenant_id,
        industry=industry,
        trace_id=trace_id,
    )
    await service.delete_row(
        period_key=period_key,
        row_id=row_id,
        actor_id=ctx.user_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── POST /mode ────────────────────────────────────────────────
@router.post(
    "/{period_key}/mode",
    response_model=MonthlyInputStateResponse,
    status_code=status.HTTP_200_OK,
    summary="월합계/일자별 모드 토글 (F2.1) — baseline_revision은 미증가",
)
async def set_monthly_input_mode(
    period_key: str,
    mode: str,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _role: TenantContext = Depends(require_role("owner")),
) -> MonthlyInputStateResponse:
    """Toggle month_total ↔ daily mode.

    `mode` is sent as a query param (POST /mode?mode=daily) to keep the
    body empty and to match the F2.1 spec shape. No baseline_revision
    bump — mode is a UI preference, not a baseline change.
    """
    industry = await _resolve_industry(
        session=session, tenant_id=ctx.tenant_id
    )
    trace_id = str(uuid.uuid4())
    service = MonthlyInputService(
        session,
        tenant_id=ctx.tenant_id,
        industry=industry,
        trace_id=trace_id,
    )
    await service.set_mode(
        period_key=period_key,
        mode=mode,
        actor_id=ctx.user_id,
    )
    return await service.get_state(period_key=period_key)


# ── Inline error response helpers ─────────────────────────────
def _industry_not_supported_response(
    exc: MonthlyInputCapabilityError,
) -> MonthlyInputStateResponse:
    """Return a 403 typed envelope (Story 2.1 inline JSONResponse pattern).

    Note: this helper returns a Pydantic response model, not a
    JSONResponse. FastAPI's exception handler chain in `main.py` maps
    `IndustryCapabilityError` (the router-level variant) to 403. This
    inline variant fires when the gate is per-row (production stream
    check happens in the service layer).
    """
    # Raise the global IndustryCapabilityError so main.py's exception
    # handler produces the canonical 403 envelope. We can't import
    # IndustryCapabilityError directly here without the inline pattern
    # divergence — instead, we surface the same envelope via FastAPI's
    # HTTPException.
    from fastapi import HTTPException

    raise HTTPException(
        status_code=403,
        detail={
            "code": "INDUSTRY_NOT_SUPPORTED",
            "message_ko": "제조업 업종에서만 입력 가능합니다",
            "details": {
                "current_industry": (
                    exc.current_industry.value
                    if exc.current_industry
                    else None
                ),
                "requested_stream": "production",
            },
            "trace_id": exc.trace_id,
        },
    )
