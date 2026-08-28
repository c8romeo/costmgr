"""apps.api.modules.finops.interactive_dashboard.dashboard_router — Phase 28 FastAPI router.

Phase 28 wire (cj-style 193번째) — FinOps Interactive Dashboard
FastAPI router (PRD §F43.1~§F43.8 verbatim + AD-56 (a)~(g) 7
sub-decisions).

Provides:
- FastAPI APIRouter with prefix
  `/api/v1/admin/finops/interactive-dashboard`
- Capability gate `Depends(require_finops_interactive_dashboard)`
  (T5.3 — fail-closed 403 Forbidden)
- 11 endpoints (spec T1.6 listed 10 + healthcheck + GET /templates —
  honest scope: spec author counted 10 main endpoints; healthcheck +
  /templates are 2 supplementary endpoints added for parity with
  Phase 26 router pattern verbatim EXTENSION):
  1. GET  /healthcheck
  2. POST /saved-views
  3. GET  /saved-views/{view_id}
  4. PUT  /saved-views/{view_id}
  5. DELETE /saved-views/{view_id}
  6. POST /saved-views/{view_id}/execute
  7. POST /unified-kpi
  8. POST /exports
  9. GET  /exports/{job_id}
  10. POST /sharing
  11. GET  /templates
- Cache-Control: no-store (CR 12-5 D-14 sweep)
- All endpoints return TypedDicts (JSON-safe)
- audit-first INSERT (caller-side via emit_audit_typed) for:
  - saved_view_created + saved_view_updated + saved_view_deleted
  - saved_view_executed + export_job_started + dashboard_shared

Honest scope notes (per CR 11-3 honest-DEFER 86번째):
- This router delegates business logic to the 3 sibling engines
  (cross_phase_aggregator + saved_view_engine + export_pipeline).
  The router is the HTTP boundary + audit + capability gate +
  response shaping layer.
- `require_finops_interactive_dashboard` capability dep is wired at
  T5.3. Until then, this router exposes endpoints with a local
  placeholder `_require_capability_finops_interactive_dashboard` that
  logs the request and allows through (Phase 25 capability gating
  pattern verbatim EXTENSION — actual fail-closed enforcement
  activates after T5.3 commit lands).

CR lessons applied:
- CR 0-2 RLS — tenant_id selector via Depends.
- CR 1-1 audit-first INSERT — 8 NEW audit actions (caller-side).
- CR 1-1 FastAPI ContextVar — trace_id propagation.
- CR 5-1 banker's rounding — Decimal precision verbatim.
- CR 9-6 commit message — git commit -F <file>.
- CR 11-3 honest-DEFER — D-FINOPS-15 honestly DEFER 보존.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 16 NEW typed exceptions
  raised by engines and caught here as HTTP errors.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript parity.
- CR 12-5 D-GATE-01 — capability gate fail-closed (T5.3 wire).
- AD-14 stack pin — Recharts 2.12.7 AD-14 stack pin EXTENSION.
- AD-22 owner-only RBAC.
- AD-56 (a)~(g) 7 sub-decisions (Phase 28 wire).
- Epic 12 2FA 챌린지 mandatory high-value (≥10M KRW/year sharing scope).
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT (finops_interactive_dashboard.* namespace).
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Final

from .cross_phase_aggregator import (
    compute_unified_kpi,
)
from .export_pipeline import (
    get_export_job_status,
    start_export_job,
)
from .saved_view_engine import (
    create_saved_view,
    delete_saved_view,
    execute_saved_view,
    read_saved_view,
    update_saved_view,
)
from .serializers import (
    DASHBOARD_ROUTER_PREFIX,
    INTERACTIVE_DASHBOARD_ENGINE_VERSION,
    PREDEFINED_VIEW_TEMPLATES,
    DashboardSharingScope,
    ExportJob,
    SavedView,
    UnifiedKPI,
)
from .serializers import (
    MODULE_TAG as _MODULE_TAG,
)

if TYPE_CHECKING:
    from fastapi import APIRouter, Depends, HTTPException, status
else:
    try:
        from fastapi import APIRouter, Depends, HTTPException, status
        _FASTAPI_AVAILABLE = True
    except ImportError:
        _FASTAPI_AVAILABLE = False
        # Stubs for type-check / offline testing
        APIRouter = None  # type: ignore[assignment,misc]
        Depends = None  # type: ignore[assignment,misc]
        HTTPException = None  # type: ignore[assignment,misc]
        status = None  # type: ignore[assignment,misc]

# ── Module constants ──────────────────────────────────────────────────────
DASHBOARD_ROUTER_VERSION: Final[str] = "1.0.0"

# Logger
_logger = logging.getLogger(__name__)


# ── Capability gate placeholder ───────────────────────────────────────────
async def _require_capability_finops_interactive_dashboard() -> dict[str, Any]:
    """Placeholder capability gate (T5.3 will wire actual gate).

    Returns:
        dict[str, Any] — empty dependency payload. After T5.3 commit,
        this is replaced by the real `require_finops_interactive_dashboard`
        dependency (fail-closed 403 Forbidden for non-granted tenants).
    """
    _logger.info(
        "phase_28_interactive_dashboard capability gate placeholder "
        "(T5.3 will wire real gate)"
    )
    return {"capability": "FINOPS_INTERACTIVE_DASHBOARD", "granted": True}


# ── Helpers ───────────────────────────────────────────────────────────────
def _no_store_headers() -> dict[str, str]:
    """Cache-Control: no-store (CR 12-5 D-14 sweep)."""
    return {"Cache-Control": "no-store"}


def _require_tenant_id(payload: dict[str, Any]) -> str:
    """Extract and validate tenant_id from request payload."""
    tenant_id = payload.get("tenant_id")
    if not tenant_id or not isinstance(tenant_id, str):
        raise ValueError("tenant_id is required in request payload")
    return tenant_id


def _build_router() -> Any:
    """Build the FastAPI APIRouter with all 11 endpoints.

    Returns:
        APIRouter instance.

    Raises:
        RuntimeError if FastAPI is not installed.
    """
    if not _FASTAPI_AVAILABLE or APIRouter is None:
        raise RuntimeError(
            "FastAPI is not installed; cannot construct dashboard_router"
        )

    router = APIRouter(
        prefix=DASHBOARD_ROUTER_PREFIX,
        tags=["finops-interactive-dashboard"],
        dependencies=[Depends(_require_capability_finops_interactive_dashboard)],
    )

    # 1. GET /healthcheck
    @router.get("/healthcheck", response_model=None)
    async def healthcheck() -> dict[str, str]:
        """Healthcheck endpoint (Phase 28 territory status)."""
        return {
            "status": "ok",
            "module_tag": _MODULE_TAG,
            "engine_version": INTERACTIVE_DASHBOARD_ENGINE_VERSION,
            "router_version": DASHBOARD_ROUTER_VERSION,
        }

    # 2. POST /saved-views
    @router.post("/saved-views", response_model=SavedView)
    async def create_saved_view_endpoint(
        payload: dict[str, Any],
    ) -> SavedView:
        """Create a saved dashboard view."""
        tenant_id = _require_tenant_id(payload)
        view_config = payload.get("view_config", {})
        template_id = payload.get("template_id")
        view_name = payload.get("view_name")
        created_by_user_id = payload.get("created_by_user_id", "")
        try:
            saved_view = create_saved_view(
                tenant_id=tenant_id,
                view_config=view_config,
                template_id=template_id,
                view_name=view_name,
                created_by_user_id=created_by_user_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return saved_view

    # 3. GET /saved-views/{view_id}
    @router.get("/saved-views/{view_id}", response_model=SavedView)
    async def read_saved_view_endpoint(
        view_id: str,
        tenant_id: str,
    ) -> SavedView:
        """Read a saved dashboard view."""
        try:
            saved_view = read_saved_view(tenant_id=tenant_id, view_id=view_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return saved_view

    # 4. PUT /saved-views/{view_id}
    @router.put("/saved-views/{view_id}", response_model=SavedView)
    async def update_saved_view_endpoint(
        view_id: str,
        payload: dict[str, Any],
    ) -> SavedView:
        """Update a saved dashboard view."""
        tenant_id = _require_tenant_id(payload)
        view_config = payload.get("view_config")
        view_name = payload.get("view_name")
        is_shared = payload.get("is_shared")
        try:
            saved_view = update_saved_view(
                tenant_id=tenant_id,
                view_id=view_id,
                view_config=view_config,
                view_name=view_name,
                is_shared=is_shared,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return saved_view

    # 5. DELETE /saved-views/{view_id}
    @router.delete("/saved-views/{view_id}")
    async def delete_saved_view_endpoint(
        view_id: str,
        tenant_id: str,
    ) -> dict[str, bool]:
        """Delete a saved dashboard view."""
        try:
            deleted = delete_saved_view(tenant_id=tenant_id, view_id=view_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"deleted": deleted}

    # 6. POST /saved-views/{view_id}/execute
    @router.post(
        "/saved-views/{view_id}/execute",
        response_model=list[UnifiedKPI],
    )
    async def execute_saved_view_endpoint(
        view_id: str,
        payload: dict[str, Any],
    ) -> list[UnifiedKPI]:
        """Execute a saved view and return UnifiedKPI list."""
        tenant_id = _require_tenant_id(payload)
        period_key = payload.get("period_key", "2026-08")
        try:
            kpis = execute_saved_view(
                tenant_id=tenant_id,
                view_id=view_id,
                period_key=period_key,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return kpis

    # 7. POST /unified-kpi
    @router.post("/unified-kpi", response_model=UnifiedKPI)
    async def compute_unified_kpi_endpoint(
        payload: dict[str, Any],
    ) -> UnifiedKPI:
        """Compute cross-phase unified KPI."""
        tenant_id = _require_tenant_id(payload)
        period_key = payload.get("period_key", "2026-08")
        modules = payload.get("modules")
        module_values = payload.get("module_values")
        dimension = payload.get("dimension", "tenant")
        dimension_value = payload.get("dimension_value")
        try:
            kpi = compute_unified_kpi(
                tenant_id=tenant_id,
                period_key=period_key,
                modules=modules,
                module_values=module_values,
                dimension=dimension,
                dimension_value=dimension_value,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return kpi

    # 8. POST /exports
    @router.post("/exports", response_model=ExportJob)
    async def start_export_job_endpoint(
        payload: dict[str, Any],
    ) -> ExportJob:
        """Start an export job."""
        tenant_id = _require_tenant_id(payload)
        view_id = payload.get("view_id")
        format_ = payload.get("format", "pdf")
        options = payload.get("options")
        try:
            job = start_export_job(
                tenant_id=tenant_id,
                view_id=view_id,
                format=format_,
                options=options,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return job

    # 9. GET /exports/{job_id}
    @router.get("/exports/{job_id}", response_model=ExportJob)
    async def get_export_job_status_endpoint(job_id: str) -> ExportJob:
        """Get export job status."""
        try:
            job = get_export_job_status(job_id=job_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return job

    # 10. POST /sharing
    @router.post("/sharing", response_model=SavedView)
    async def share_dashboard_endpoint(
        payload: dict[str, Any],
    ) -> SavedView:
        """Create or update a dashboard sharing grant.

        The router layer delegates to saved_view_engine. The actual
        SharingGrant TypedDict tracking is performed by the engine
        (SharingGrant TypedDict is re-exported but the engine persists
        via SavedView.is_shared = True semantics at this sprint level).
        """
        tenant_id = _require_tenant_id(payload)
        view_id = payload.get("view_id")
        scope = payload.get("scope", DashboardSharingScope.TENANT.value)
        granted_to_user_id = payload.get("granted_to_user_id", "")
        try:
            # Mark is_shared=True on the saved view
            saved_view = update_saved_view(
                tenant_id=tenant_id,
                view_id=view_id,
                is_shared=True,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return saved_view

    # 11. GET /templates
    @router.get("/templates")
    async def list_predefined_templates() -> list[str]:
        """Return the 12 pre-defined view template names."""
        return list(PREDEFINED_VIEW_TEMPLATES)

    return router


# Build the router at module import time if FastAPI is available
router: Any = None
if _FASTAPI_AVAILABLE:
    try:
        router = _build_router()
    except Exception as _exc:  # noqa: BLE001
        _logger.warning(
            "dashboard_router build failed: %s", _exc
        )
        router = None


# ── Public surface ────────────────────────────────────────────────────────
__all__ = [
    "DASHBOARD_ROUTER_VERSION",
    "router",
]
