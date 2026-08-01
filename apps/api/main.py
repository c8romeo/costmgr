"""
apps/api/main.py — FastAPI entry (Story 0.1 stub + Story 0.2 attach).

Only a single /health route in this story. Domain endpoints are added in Epic 4+.

AD-1, AD-11 compliance:
  - This module imports only stdlib + FastAPI/uvicorn
  - It does NOT import packages.cost_engine.core directly
  - It MAY import packages.cost_engine.ports (via apps.api.core.ports_bridge — added in later stories)
"""

import uuid as _uuid_mod

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from apps.api.core.capability import (
    ForbiddenRoleError,
    IndustryCapabilityError,
)
from apps.api.core.pipa_gate import PipaConsentMissingError
from apps.api.core.security import AuthError
from apps.api.modules.m0_onboarding import router as m0_onboarding_router
from apps.api.modules.m1_baseline import router as m1_baseline_router
from apps.api.modules.m2_input import router as m2_input_router
from apps.api.modules.m2_input.services.monthly_input_service import (
    MonthlyInputCompanyBurdenRateError,
    MonthlyInputFteReadOnlyError,
    MonthlyInputInventoryProjectionError,
    MonthlyInputInvalidLaborShapeError,
    MonthlyInputPayTypeMismatchError,
    MonthlyInputPayrollSettingsInvalidError,
    MonthlyInputWarningsReadOnlyError,
)
from apps.api.modules.m9_abc import router as m9_abc_router
from apps.api.modules.m10_ai import router as m10_ai_router
from apps.api.modules.m10_ai.handlers import _pipa_error_response

app = FastAPI(
    title="bizup/costmgr API",
    version="0.1.0",
    description="원가 관리 SaaS — FastAPI modular monolith (AD-1)",
)

# Story 1.1 — M0 onboarding (industry selector + menu auto-toggle)
app.include_router(m0_onboarding_router)

# Story 1.2 — Settings wizard scaffolds (M1 baseline + M9 ABC read endpoints)
app.include_router(m1_baseline_router)
app.include_router(m9_abc_router)

# Story 1.3 — M10 AI document extraction (upload / list / reprocess + drafts CRUD / promote)
app.include_router(m10_ai_router)

# Story 3.1 — M2 monthly input capture (6-stream tabs + 일자별 toggle + completion gate)
# Story 3.2 — M2 labor precision (pay_type 분기 + 5 breakdown fields + tenant payroll override)
app.include_router(m2_input_router)


@app.exception_handler(AuthError)
async def _auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
    """Map `AuthError` (AD-15) to HTTP 401 with the typed error contract.

    Without this handler, FastAPI returns HTTP 500 for any `AuthError`
    raised in a dependency (AD-15 contract violation).
    """
    return JSONResponse(
        status_code=401,
        content={
            "code": exc.code,
            "message_ko": exc.message_ko,
            "details": exc.details,
            "trace_id": exc.trace_id,
        },
    )


# H5 / AD-15 §4 + AC #6: typed envelope for IndustryCapabilityError.
# Without this, FastAPI returns HTTP 500 for capability mismatches —
# violating the `{code, message_ko, details, trace_id}` contract.
@app.exception_handler(IndustryCapabilityError)
async def _industry_capability_handler(
    request: Request, exc: IndustryCapabilityError
) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "code": "INDUSTRY_NOT_SUPPORTED",
            "message_ko": "현재 업종에서 지원하지 않는 기능입니다",
            "details": {
                "current_industry": (
                    exc.current_industry.value if exc.current_industry else None
                ),
                "requested_capability": exc.capability.value,
            },
            "trace_id": exc.trace_id,
        },
    )


# H3 / AD-10 / T4.2: typed envelope for ForbiddenRoleError.
# Without this, FastAPI returns HTTP 500 for role gate failures.
@app.exception_handler(ForbiddenRoleError)
async def _forbidden_role_handler(
    request: Request, exc: ForbiddenRoleError
) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "code": "FORBIDDEN_ROLE",
            "message_ko": "소유자(Owner) 권한이 필요합니다",
            "details": {
                "role": exc.role,
                "required_role": exc.required_role,
            },
            "trace_id": exc.trace_id,
        },
    )


# Story 1.3 — PIPA gate dependency-raised exception → 451 typed envelope.
# Without this handler, FastAPI returns HTTP 500 for PIPA gate failures.
@app.exception_handler(PipaConsentMissingError)
async def _pipa_consent_handler(
    request: Request, exc: PipaConsentMissingError
) -> JSONResponse:
    return _pipa_error_response(exc)


# Story 3.2 — labor precision error envelopes (AD-15 §4).
# Without these, FastAPI returns HTTP 500 for the new `_validate_labor_shape`
# + `_load_payroll_settings` failure paths. Mapped to typed codes so the
# frontend can show specific Korean hints ("daily mode doesn't use
# monthly_salary_basis_krw", etc).
@app.exception_handler(MonthlyInputInvalidLaborShapeError)
async def _m2_invalid_labor_shape_handler(
    request: Request, exc: MonthlyInputInvalidLaborShapeError
) -> JSONResponse:
    """400 MONTHLY_INPUT_INVALID_LABOR_SHAPE — labor stream missing required
    pay_type-specific fields (Task 3.1 `_validate_labor_shape` AC #4)."""
    return JSONResponse(
        status_code=400,
        content={
            "code": "MONTHLY_INPUT_INVALID_LABOR_SHAPE",
            "message_ko": "인건비 입력 항목이 부족합니다",
            "details": exc.details,
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(MonthlyInputFteReadOnlyError)
async def _m2_fte_read_only_handler(
    request: Request, exc: MonthlyInputFteReadOnlyError
) -> JSONResponse:
    """400 MONTHLY_INPUT_FTE_READ_ONLY — AC #5 direct write attempt on
    `fte_headcount` / `fte_wage_krw` (derived fields)."""
    return JSONResponse(
        status_code=400,
        content={
            "code": "MONTHLY_INPUT_FTE_READ_ONLY",
            "message_ko": "FTE 인원·인건비는 자동 계산 항목입니다 (직접 수정 불가)",
            "details": {"field": exc.field},
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(MonthlyInputPayrollSettingsInvalidError)
async def _m2_payroll_settings_invalid_handler(
    request: Request, exc: MonthlyInputPayrollSettingsInvalidError
) -> JSONResponse:
    """400 MONTHLY_INPUT_PAYROLL_SETTINGS_INVALID — out-of-range value in
    `tenant_settings.payroll.*` (Task 3.1 `_load_payroll_settings`)."""
    return JSONResponse(
        status_code=400,
        content={
            "code": "MONTHLY_INPUT_PAYROLL_SETTINGS_INVALID",
            "message_ko": "인건비 정책 값이 올바르지 않습니다",
            "details": exc.details,
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(MonthlyInputCompanyBurdenRateError)
async def _m2_company_burden_rate_handler(
    request: Request, exc: MonthlyInputCompanyBurdenRateError
) -> JSONResponse:
    """422 MONTHLY_INPUT_COMPANY_BURDEN_RATE — service-side re-check
    catches bypasses (Task 3.1)."""
    return JSONResponse(
        status_code=422,
        content={
            "code": "MONTHLY_INPUT_COMPANY_BURDEN_RATE",
            "message_ko": "회사부담임률은 0과 1 사이여야 합니다",
            "details": {"value": exc.value},
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(MonthlyInputPayTypeMismatchError)
async def _m2_pay_type_mismatch_handler(
    request: Request, exc: MonthlyInputPayTypeMismatchError
) -> JSONResponse:
    """400 MONTHLY_INPUT_PAY_TYPE_MISMATCH — pay_type별 forbidden 필드
    사용 시 (예: daily + monthly_salary_basis_krw)."""
    return JSONResponse(
        status_code=400,
        content={
            "code": "MONTHLY_INPUT_PAY_TYPE_MISMATCH",
            "message_ko": "급여유형과 입력 항목이 맞지 않습니다",
            "details": exc.details,
            "trace_id": exc.trace_id,
        },
    )


# Story 3.3 — warning / projection error envelopes (AD-15 §4).
# Maps the 2 new typed exceptions (Task 3.2) so the frontend can
# distinguish advisory warnings from server-side errors.
@app.exception_handler(MonthlyInputWarningsReadOnlyError)
async def _m2_warnings_read_only_handler(
    request: Request, exc: MonthlyInputWarningsReadOnlyError
) -> JSONResponse:
    """400 MONTHLY_INPUT_WARNINGS_READ_ONLY — AC #7 server-side defense.

    `warnings` / `is_blocked` / `warnings_count` / `top_n_severity`
    are DERIVED fields (PRD §A11); PATCH attempts on them surface as
    `extra_fields_not_allowed` via Pydantic v2's `extra="forbid"`
    first. This handler covers the defense-in-depth path that
    bypasses Pydantic (raw DB writes, internal scripts).
    """
    return JSONResponse(
        status_code=400,
        content={
            "code": "MONTHLY_INPUT_WARNINGS_READ_ONLY",
            "message_ko": "경고 항목은 자동 계산 항목입니다 (직접 수정 불가)",
            "details": {"field": exc.field},
            "trace_id": exc.trace_id,
        },
    )


@app.exception_handler(MonthlyInputInventoryProjectionError)
async def _m2_inventory_projection_handler(
    request: Request, exc: MonthlyInputInventoryProjectionError
) -> JSONResponse:
    """422 MONTHLY_INPUT_INVENTORY_PROJECTION — projection kernel failure.

    Fires when the inventory projection kernel (PRD §6.2) cannot
    reach a deterministic state. Mapped to 422 (PRD §V6 ENVELOPE
    for "data not processable") — operator-facing message hints at
    "raw balance out of range" / "missing product metadata" so the
    user can self-correct without needing to read a trace_id.
    """
    return JSONResponse(
        status_code=422,
        content={
            "code": "MONTHLY_INPUT_INVENTORY_PROJECTION",
            "message_ko": "재고 계산에 실패했습니다 (기초재고 또는 제품정보 확인)",
            "details": exc.details,
            "trace_id": exc.trace_id,
        },
    )


# H3 (Review) / AD-15 §4: detect BOM ratio decimal-places violations and
# convert them to a typed 422 BOM_INVALID_RATIO envelope. Without this,
# Pydantic's `max_digits=7, decimal_places=4` violation on BOMRowInput.ratio
# returns a generic FastAPI 422 — violating the typed error contract.
#
# All other RequestValidationError paths fall back to FastAPI's default
# `{"detail": [...]}` shape to preserve client compatibility.
@app.exception_handler(RequestValidationError)
async def _bom_validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Map BOMRowInput.ratio decimal-places violations to typed envelope.

    Match shape: loc == ("body", "lines", <index>, "ratio") and
    type in {decimal_max_places, decimal_max_digits, greater_than,
    less_than_equal}. Other validation errors are passed through with
    the default `detail` shape.
    """
    errors = exc.errors()
    trace_id = str(_uuid_mod.uuid4())
    for err in errors:
        loc = err.get("loc", ())
        if (
            len(loc) == 4
            and loc[0] == "body"
            and loc[1] == "lines"
            and loc[2].__class__.__name__ == "int"
            and loc[3] == "ratio"
            and err.get("type")
            in {"decimal_max_places", "decimal_max_digits",
                "greater_than", "less_than_equal", "decimal_whole_digits"}
        ):
            child_idx: int = loc[2]
            return JSONResponse(
                status_code=422,
                content={
                    "code": "BOM_INVALID_RATIO",
                    "message_ko": (
                        f"비중은 0보다 크고 100 이하이며 소수점 4자리까지 "
                        f"입력 가능합니다 (행 {child_idx})."
                    ),
                    "details": {
                        "field": "ratio",
                        "index": child_idx,
                        "violation": err.get("type"),
                        "input": err.get("input"),
                    },
                    "trace_id": trace_id,
                },
            )
    # Non-BOM validation errors — fall through to FastAPI default shape.
    return JSONResponse(
        status_code=422,
        content={"detail": errors},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint — used by Railway / Vercel / CI smoke tests."""
    return {"status": "ok", "service": "costmgr-api", "version": "0.1.0"}


@app.on_event("startup")
async def _attach_tenant_listener() -> None:
    """Story 0.2 — wire the SET LOCAL app.current_tenant_id listener.

    Imported lazily so test environments without a real DB engine don't crash.
    """
    try:
        from apps.api.core.db import get_engine
        from apps.api.core.tenant_context import attach_tenant_listener

        attach_tenant_listener(get_engine())
    except RuntimeError:
        # No DATABASE_URL configured (e.g. README quickstart smoke test). Skip.
        pass
