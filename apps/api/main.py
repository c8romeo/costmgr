"""
apps/api/main.py — FastAPI entry (Story 0.1 stub + Story 0.2 attach).

Only a single /health route in this story. Domain endpoints are added in Epic 4+.

AD-1, AD-11 compliance:
  - This module imports only stdlib + FastAPI/uvicorn
  - It does NOT import packages.cost_engine.core directly
  - It MAY import packages.cost_engine.ports (via apps.api.core.ports_bridge — added in later stories)
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from apps.api.core.capability import (
    ForbiddenRoleError,
    IndustryCapabilityError,
)
from apps.api.core.security import AuthError
from apps.api.modules.m0_onboarding import router as m0_onboarding_router
from apps.api.modules.m1_baseline import router as m1_baseline_router
from apps.api.modules.m9_abc import router as m9_abc_router

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
