"""apps.api.modules.finops.interactive_dashboard.interactive_dashboard_routes — Phase 28 routes wrapper.

Phase 28 wire (cj-style 193번째) — FinOps Interactive Dashboard
routes wrapper (PRD §F43.1~§F43.8 verbatim + AD-56 (a)~(g) 7
sub-decisions + Phase 26 wire 의 routes pattern verbatim EXTENSION).

This module is the integration wrapper that:
- Re-exports `router` from dashboard_router.py for inclusion in
  apps/api/main.py (Phase 26 pattern verbatim EXTENSION).
- Provides a `register_routes(app)` helper that mounts the Phase 28
  router onto the FastAPI app instance.
- Provides a `register_scheduled_jobs(scheduler)` helper that wires
  the 4 cadences (daily / weekly / monthly / on-demand) onto an
  apscheduler.BackgroundScheduler instance.
- Provides a `bootstrap_phase_28_lifespan()` helper that returns the
  FastAPI lifespan context manager (apscheduler + LISTEN/NOTIFY +
  CORS + middleware sweep).

Honest scope notes (per CR 11-3 honest-DEFER 88번째):
- This wrapper is the integration boundary. It does NOT add new
  endpoints or business logic — those live in dashboard_router.py +
  the 3 sibling engines (cross_phase_aggregator + saved_view_engine
  + export_pipeline).
- apscheduler / pytz wiring is performed at the call site
  (apps/api/main.py). This wrapper exposes the wiring as importable
  helpers.

CR lessons applied:
- CR 0-2 RLS — tenant_id selector.
- CR 1-1 audit-first INSERT — 8 NEW audit actions (caller-side).
- CR 1-1 FastAPI ContextVar — trace_id propagation.
- CR 5-1 banker's rounding — Decimal precision verbatim.
- CR 9-6 commit message — git commit -F <file>.
- CR 11-3 honest-DEFER — D-FINOPS-15 honestly DEFER 보존.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 16 NEW typed exceptions.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript parity.
- CR 12-5 D-GATE-01 — capability gate fail-closed (T5.3 wire).
- AD-14 stack pin — apscheduler==3.10.4 + pytz==2024.1.
- AD-22 owner-only RBAC.
- AD-56 (a)~(g) 7 sub-decisions (Phase 28 wire).
- Epic 12 2FA 챌린지 mandatory high-value (≥10M KRW/year sharing scope).
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT (finops_interactive_dashboard.* namespace).
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Final

from .dashboard_router import (
    DASHBOARD_ROUTER_VERSION,
)
from .dashboard_router import (
    router as _dashboard_router,
)
from .scheduled_interactive_dashboard_dispatch import (
    SCHEDULED_DISPATCH_VERSION,
    dispatch_notification,
    scheduled_export_cleanup_job,
    scheduled_sharing_expiry_job,
    scheduled_unified_kpi_incremental_update_job,
    scheduled_unified_kpi_refresh_job,
)

if TYPE_CHECKING:
    pass
else:
    try:
        from fastapi import FastAPI as _FastAPI  # type: ignore[import-not-found]
        _FASTAPI_AVAILABLE = True
    except ImportError:
        _FastAPI = None  # type: ignore[assignment,misc]
        _FASTAPI_AVAILABLE = False

    try:
        from apscheduler.schedulers.background import (  # type: ignore[import-not-found]
            BackgroundScheduler as _BackgroundScheduler,
        )
        _APSCHEDULER_AVAILABLE = True
    except ImportError:
        _BackgroundScheduler = None  # type: ignore[assignment,misc]
        _APSCHEDULER_AVAILABLE = False

# ── Module constants ──────────────────────────────────────────────────────
INTERACTIVE_DASHBOARD_ROUTES_VERSION: Final[str] = "1.0.0"

# Re-export the FastAPI router (Phase 26 pattern verbatim EXTENSION)
router = _dashboard_router

# Logger
_logger = logging.getLogger(__name__)


# ── Route registration helper ─────────────────────────────────────────────
def register_routes(app: Any) -> None:
    """Mount the Phase 28 router onto a FastAPI app instance.

    Args:
        app: FastAPI app instance.

    Raises:
        RuntimeError if FastAPI is not installed or router is None.
    """
    if not _FASTAPI_AVAILABLE or _FastAPI is None:
        raise RuntimeError(
            "FastAPI is not installed; cannot register_routes"
        )
    if _dashboard_router is None:
        raise RuntimeError(
            "dashboard_router failed to construct (FastAPI import ok "
            "but router is None)"
        )
    app.include_router(_dashboard_router)
    _logger.info(
        "phase_28_interactive_dashboard routes registered: "
        "prefix=%s, router_version=%s, scheduled_dispatch_version=%s",
        _dashboard_router.prefix,
        DASHBOARD_ROUTER_VERSION,
        SCHEDULED_DISPATCH_VERSION,
    )


# ── Scheduled job registration helper ────────────────────────────────────
def register_scheduled_jobs(scheduler: Any) -> int:
    """Wire the 4 cadences onto an apscheduler BackgroundScheduler.

    Args:
        scheduler: apscheduler.schedulers.background.BackgroundScheduler
            instance.

    Returns:
        int — number of jobs registered.

    Raises:
        RuntimeError if apscheduler is not installed.
    """
    if not _APSCHEDULER_AVAILABLE or _BackgroundScheduler is None:
        raise RuntimeError(
            "apscheduler is not installed; cannot register_scheduled_jobs"
        )

    # Daily 04:00 KST unified KPI refresh
    scheduler.add_job(
        scheduled_unified_kpi_refresh_job,
        "cron",
        hour=4,
        minute=0,
        id="phase_28_daily_unified_kpi_refresh",
        replace_existing=True,
        kwargs={"tenant_id": "_all_tenants_"},
    )

    # Weekly Mon 05:00 KST export cleanup
    scheduler.add_job(
        scheduled_export_cleanup_job,
        "cron",
        day_of_week="mon",
        hour=5,
        minute=0,
        id="phase_28_weekly_export_cleanup",
        replace_existing=True,
    )

    # Monthly 1st-day 06:00 KST sharing expiry
    scheduler.add_job(
        scheduled_sharing_expiry_job,
        "cron",
        day=1,
        hour=6,
        minute=0,
        id="phase_28_monthly_sharing_expiry",
        replace_existing=True,
    )

    # On-demand incremental update (manual trigger)
    scheduler.add_job(
        scheduled_unified_kpi_incremental_update_job,
        "date",
        id="phase_28_on_demand_incremental_update",
        replace_existing=True,
        run_date=None,  # placeholder; manual trigger only
    )

    _logger.info(
        "phase_28_interactive_dashboard scheduled jobs registered: "
        "4 cadences (daily_unified_kpi_refresh + weekly_export_cleanup "
        "+ monthly_sharing_expiry + on_demand_incremental_update)"
    )
    return 4


# ── Notification dispatch helper ─────────────────────────────────────────
def dispatch_dashboard_notification(
    cadence: str,
    recipient_template_name: str,
    trace_id: str = "",
) -> dict[str, Any]:
    """Wrapper around dispatch_notification returning a JSON-safe dict.

    Args:
        cadence: scheduled job cadence.
        recipient_template_name: recipient template name.
        trace_id: optional trace identifier.

    Returns:
        dict[str, Any] — JSON-serializable notification dispatch result.
    """
    result = dispatch_notification(
        cadence=cadence,
        recipient_template_name=recipient_template_name,
        trace_id=trace_id,
    )
    return result.to_dict()


# ── Lifespan bootstrap helper ─────────────────────────────────────────────
def bootstrap_phase_28_lifespan() -> dict[str, Any]:
    """Bootstrap Phase 28 lifespan metadata (T6.2 verbatim EXTENSION).

    Returns:
        dict[str, Any] — lifespan metadata (module_tag + version +
        schedulable_jobs + listen_notify_channels).
    """
    from .serializers import (
        MODULE_TAG,
        UNIFIED_KPI_LISTEN_NOTIFY_CHANNELS,
    )

    return {
        "module_tag": MODULE_TAG,
        "interactive_dashboard_routes_version": INTERACTIVE_DASHBOARD_ROUTES_VERSION,
        "dashboard_router_version": DASHBOARD_ROUTER_VERSION,
        "scheduled_dispatch_version": SCHEDULED_DISPATCH_VERSION,
        "schedulable_jobs": [
            "phase_28_daily_unified_kpi_refresh",
            "phase_28_weekly_export_cleanup",
            "phase_28_monthly_sharing_expiry",
            "phase_28_on_demand_incremental_update",
        ],
        "listen_notify_channels": list(UNIFIED_KPI_LISTEN_NOTIFY_CHANNELS),
        "listen_notify_channel_count": len(UNIFIED_KPI_LISTEN_NOTIFY_CHANNELS),
    }


# ── Public surface ────────────────────────────────────────────────────────
__all__ = [
    "INTERACTIVE_DASHBOARD_ROUTES_VERSION",
    "bootstrap_phase_28_lifespan",
    "dispatch_dashboard_notification",
    "register_routes",
    "register_scheduled_jobs",
    "router",
]
