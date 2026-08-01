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
