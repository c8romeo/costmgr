"""apps.api.modules.m5_reports.handlers — M5 reports HTTP handlers (Story 9.4).

Story 9.4 (Epic 9 4번째 진입점) — 2 NEW HTTP handlers for Report #21:

  - GET /api/v1/reports/21                — Cost Object Breakdown 조회
                                            (PRD §9 #21 + §7.3 verbatim)
  - POST /api/v1/reports/21/pdf           — PDF export via A30 SHARED generator
                                            (Discriminated union report_id: Literal[15..21])

Capability gate: `Depends(require_any_capability(Capability.COST_CALCULATION,
Capability.ABC_CALCULATION))` — CR 12-1 L4 variadic helper reuse precedent.

Role gate: `Depends(require_any_role("owner", "member"))` (AD-10 4-role).

AD-18 single endpoint (1 endpoint per Report #N — wire = Report #21 only).
AD-19 dual-route dispatch (M3 calc → Report #21 wire 진입).
"""

from __future__ import annotations

import base64

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.capability import (
    Capability,
    require_any_capability,
    require_any_role,
)
from apps.api.core.db import get_session
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.modules.m5_reports.schemas import (
    Report21CostObjectRow,
    Report21PdfRequest,
    Report21PdfResponse,
    Report21Request,
    Report21Response,
    Report21UnusedCapacityRow,
)
from apps.api.modules.m5_reports.services import Report21Service
from packages.services.m5_reports.pdf_generator import REPORT21_REPORT_CODE

router = APIRouter(prefix="/api/v1/reports", tags=["m5-reports"])


@router.get(
    "/21",
    response_model=Report21Response,
    status_code=status.HTTP_200_OK,
    summary="원가대상별 원가 집계표 (Report #21)",
    description=(
        "Story 9.4 — Report #21 (Cost Object Breakdown) 진입점. "
        "PRD §9 #21 + §7.3 (법인세법 시행규칙 제76조 2기준) verbatim — "
        "V7 ABC 무결성 검증 + Report21Summary envelope assemble. "
        "Capability gate: COST_CALCULATION OR ABC_CALCULATION "
        "(industry-agnostic, CR 12-1 L4 variadic helper). "
        "Role gate: owner or member."
    ),
    dependencies=[
        Depends(
            require_any_capability(
                Capability.COST_CALCULATION, Capability.ABC_CALCULATION
            )
        ),
        Depends(require_any_role("owner", "member")),
    ],
)
async def get_report21(
    query: Report21Request = Depends(),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> Report21Response:
    """GET /api/v1/reports/21 — Cost Object Breakdown handler."""
    service = Report21Service()
    state = await service.build_report21(
        session=session,
        tenant_id=ctx.tenant_id,
        period_key=query.period_key,
    )

    cost_object_rows = [
        Report21CostObjectRow(
            product_id=r.product_id,
            activity_id=r.activity_id,
            driver_id=r.driver_id,
            allocated_krw=str(r.allocated_krw),
        )
        for r in state.cost_object_breakdown
    ]
    unused_rows = [
        Report21UnusedCapacityRow(
            department_id=u.department_id,
            unused_hours=str(u.unused_hours),
            unused_cost_krw=str(u.unused_cost_krw),
        )
        for u in state.unused_capacity_breakdown
    ]

    return Report21Response(
        period_key=state.period_key,
        cost_object_breakdown=cost_object_rows,
        unused_capacity_breakdown=unused_rows,
        v7_verdict_is_balanced=state.v7_verdict.is_balanced,
        generation_hash=state.summary.hash,
        report_code=state.report_code,
    )


@router.post(
    "/21/pdf",
    response_model=Report21PdfResponse,
    status_code=status.HTTP_200_OK,
    summary="Report #21 PDF export (A30 SHARED factory)",
    description=(
        "Story 9.4 — PDF export via A30 SHARED PDF generator factory "
        "(Discriminated union report_id: Literal[15..21]). "
        "Report #21 (Cost Object Breakdown) 본 진입점 + Report #15 (활동원가 "
        "내역서, 후속 진입점) = SHARED factory pattern. "
        "Capability gate: COST_CALCULATION OR ABC_CALCULATION."
    ),
    dependencies=[
        Depends(
            require_any_capability(
                Capability.COST_CALCULATION, Capability.ABC_CALCULATION
            )
        ),
        Depends(require_any_role("owner", "member")),
    ],
)
async def post_report21_pdf(
    body: Report21PdfRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> Report21PdfResponse:
    """POST /api/v1/reports/21/pdf — Report #21 PDF export handler."""
    service = Report21Service()
    pdf_result = await service.generate_report21_pdf(
        session=session,
        tenant_id=ctx.tenant_id,
        period_key=body.period_key,
    )

    pdf_base64 = base64.b64encode(pdf_result.pdf_bytes).decode("ascii")

    return Report21PdfResponse(
        period_key=body.period_key,
        pdf_base64=pdf_base64,
        size_bytes=pdf_result.size_bytes,
        generation_hash=pdf_result.generation_hash,
        report_code=REPORT21_REPORT_CODE,
    )


__all__ = ["router"]
