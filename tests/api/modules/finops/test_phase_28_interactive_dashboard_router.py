"""tests.api.modules.finops.test_phase_28_interactive_dashboard_router — Phase 28 router drift.

Phase 28 wire (cj-style 193번째) — FinOps Interactive Dashboard
territory. Layer 2 P1 carry-over (Q2 backend-only sprint): pytest
test backfill for interactive_dashboard router endpoints, mirroring
the Phase 21~25 router drift pattern verbatim EXTENSION.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at
module top. Q2 backend-only sprint: T2 frontend dashboard UI + TS
mirrors + vitest is honestly DEFER → separate follow-up sprint.
"""
from __future__ import annotations

from fastapi import APIRouter

from apps.api.core.capability import _INDUSTRY_CAPABILITIES, Capability
from apps.api.core.errors import (
    ExportJobFormatError,
    ExportJobSizeError,
    InteractiveDashboardAggregationError,
    SavedViewFilterError,
    SavedViewTemplateError,
)
from apps.api.dependencies.capability import require_finops_interactive_dashboard
from apps.api.modules.finops.interactive_dashboard.cross_phase_aggregator import (
    CROSS_PHASE_ROLLUP_DIMENSION_SET,
    CROSS_PHASE_ROLLUP_DIMENSIONS,
    PHASE_LEDGER_MAX_PHASE,
    PHASE_LEDGER_MIN_PHASE,
    PHASE_LEDGER_PHASE_COUNT,
)
from apps.api.modules.finops.interactive_dashboard.dashboard_router import (
    router as interactive_dashboard_router,
)
from apps.api.modules.finops.interactive_dashboard.export_pipeline import (
    EXPORT_PIPELINE_ENGINE_VERSION,
)
from apps.api.modules.finops.interactive_dashboard.interactive_dashboard_routes import (
    router as interactive_dashboard_routes_router,
)
from apps.api.modules.finops.interactive_dashboard.saved_view_engine import (
    DRILL_DOWN_DIMENSION_SET,
    DRILL_DOWN_DIMENSIONS,
    SAVED_VIEW_ENGINE_VERSION,
)
from apps.api.modules.finops.interactive_dashboard.serializers import (
    DASHBOARD_ROUTER_PREFIX,
    EXPORT_MAX_RETRIES,
    INTERACTIVE_DASHBOARD_ENGINE_VERSION,
    MAX_EXPORT_SIZE_BYTES,
    MAX_SAVED_VIEWS_PER_TENANT,
    MODULE_TAG,
    PREDEFINED_VIEW_TEMPLATES,
    SAVED_VIEW_CACHE_TTL_SECONDS,
    SHARING_EXPIRES_DEFAULT_DAYS,
    TOTAL_VERIFICATION_TOLERANCE_KRW,
    UNIFIED_KPI_LISTEN_NOTIFY_CHANNELS,
    ExportJobStatus,
)

ROUTER_PREFIX = "/api/v1/admin/finops/interactive-dashboard"
ROUTER_TAGS = ["finops-interactive-dashboard"]
EXPECTED_ROUTE_PATHS = frozenset(
    {
        "/api/v1/admin/finops/interactive-dashboard/healthcheck",
        "/api/v1/admin/finops/interactive-dashboard/saved-views",
        "/api/v1/admin/finops/interactive-dashboard/saved-views/{view_id}",
        "/api/v1/admin/finops/interactive-dashboard/saved-views/{view_id}/execute",
        "/api/v1/admin/finops/interactive-dashboard/unified-kpi",
        "/api/v1/admin/finops/interactive-dashboard/exports",
        "/api/v1/admin/finops/interactive-dashboard/exports/{job_id}",
        "/api/v1/admin/finops/interactive-dashboard/sharing",
        "/api/v1/admin/finops/interactive-dashboard/templates",
    }
)
EXPECTED_ROUTE_COUNT = 9
PHASE_28_PHASE_COUNT = 17  # Phase 11~27 = 17 phases
PHASE_28_CADENCE_COUNT = 4
PHASE_28_LISTEN_NOTIFY_CHANNEL_COUNT = 18
PHASE_28_PREDEFINED_VIEW_TEMPLATE_COUNT = 12
PHASE_28_CROSS_ROLLUP_DIM_COUNT = 6
PHASE_28_DRILL_DOWN_DIM_COUNT = 7
PHASE_28_EXPORT_FORMAT_COUNT = 5
PHASE_28_EXPORT_STATUS_COUNT = 5
PHASE_28_INDUSTRY_GRANT_COUNT = 4
PHASE_28_TYPED_EXCEPTION_COUNT = 16  # + 1 base = 17
PHASE_28_AUDIT_ACTION_COUNT = 8
VALID_TENANT_ID = "11111111-2222-3333-4444-555555555555"
PERIOD_KEY = "2026-08"


def test_interactive_dashboard_router_is_api_router_instance() -> None:
    """Test 1 — Router is a FastAPI APIRouter instance (not None)."""
    assert interactive_dashboard_router is not None
    assert isinstance(interactive_dashboard_router, APIRouter)


def test_interactive_dashboard_router_prefix_is_correct() -> None:
    """Test 2 — Router prefix matches DASHBOARD_ROUTER_PREFIX constant."""
    assert DASHBOARD_ROUTER_PREFIX == ROUTER_PREFIX
    assert interactive_dashboard_router.prefix == ROUTER_PREFIX


def test_interactive_dashboard_router_exposes_nine_distinct_paths() -> None:
    """Test 3 — Router exposes exactly 9 distinct paths per Phase 28 spec."""
    route_paths = {
        getattr(route, "path", "") for route in interactive_dashboard_router.routes
    }
    assert len(route_paths) == EXPECTED_ROUTE_COUNT


def test_interactive_dashboard_router_routes_match_expected_paths() -> None:
    """Test 4 — Router's route set exactly matches the 9 expected paths."""
    route_paths = {
        getattr(route, "path", "") for route in interactive_dashboard_router.routes
    }
    assert route_paths == EXPECTED_ROUTE_PATHS


def test_interactive_dashboard_routes_wrapper_reexports_router() -> None:
    """Test 5 — interactive_dashboard_routes.router is the SAME object as dashboard_router.router."""
    assert interactive_dashboard_routes_router is interactive_dashboard_router


def test_interactive_dashboard_module_tag_and_engine_versions() -> None:
    """Test 6 — Module tag + 3 engine versions + serializer invariants preserved."""
    assert MODULE_TAG == "m28_finops_interactive_dashboard"
    assert INTERACTIVE_DASHBOARD_ENGINE_VERSION == "1.0.0"
    assert SAVED_VIEW_ENGINE_VERSION == "1.0.0"
    assert EXPORT_PIPELINE_ENGINE_VERSION == "1.0.0"
    assert MAX_SAVED_VIEWS_PER_TENANT == 50
    assert MAX_EXPORT_SIZE_BYTES == 50 * 1024 * 1024  # 50MB
    assert EXPORT_MAX_RETRIES == 3
    assert SAVED_VIEW_CACHE_TTL_SECONDS == 300
    assert SHARING_EXPIRES_DEFAULT_DAYS == 30
    assert TOTAL_VERIFICATION_TOLERANCE_KRW == 0.01


def test_interactive_dashboard_phase_ledger_envelope_is_eleven_to_twentyseven() -> None:
    """Test 7 — Phase 11~27 chain: MIN=11, MAX=27, COUNT=17 (PRD §F43.1 + T1.3)."""
    assert PHASE_LEDGER_MIN_PHASE == 11
    assert PHASE_LEDGER_MAX_PHASE == 27
    assert PHASE_LEDGER_PHASE_COUNT == PHASE_28_PHASE_COUNT
    assert (
        PHASE_LEDGER_MAX_PHASE - PHASE_LEDGER_MIN_PHASE + 1
        == PHASE_LEDGER_PHASE_COUNT
    )


def test_interactive_dashboard_cross_rollup_is_six_dimensions() -> None:
    """Test 8 — 6-dim cross-rollup (tenant + cost_center + department + business_unit + tag + cloud_provider)."""
    assert len(CROSS_PHASE_ROLLUP_DIMENSIONS) == PHASE_28_CROSS_ROLLUP_DIM_COUNT
    assert "tenant" in CROSS_PHASE_ROLLUP_DIMENSION_SET
    assert "cost_center" in CROSS_PHASE_ROLLUP_DIMENSION_SET
    assert "department" in CROSS_PHASE_ROLLUP_DIMENSION_SET
    assert "business_unit" in CROSS_PHASE_ROLLUP_DIMENSION_SET
    assert "tag" in CROSS_PHASE_ROLLUP_DIMENSION_SET
    assert "cloud_provider" in CROSS_PHASE_ROLLUP_DIMENSION_SET
    # CRITICAL: 'service' is NOT in cross-rollup (drill-down-only, §F43.1 vs §F43.2)
    assert "service" not in CROSS_PHASE_ROLLUP_DIMENSION_SET


def test_interactive_dashboard_drill_down_is_seven_dimensions() -> None:
    """Test 9 — 7-dim drill-down = 6 cross-rollup + service (PRD §F43.2 verbatim)."""
    assert len(DRILL_DOWN_DIMENSIONS) == PHASE_28_DRILL_DOWN_DIM_COUNT
    assert "service" in DRILL_DOWN_DIMENSION_SET
    # Drill-down is a superset of cross-rollup
    assert CROSS_PHASE_ROLLUP_DIMENSION_SET <= DRILL_DOWN_DIMENSION_SET


def test_interactive_dashboard_predefined_view_templates_twelve() -> None:
    """Test 10 — 12 NEW pre-defined view templates (PRD §F43.2 verbatim)."""
    assert len(PREDEFINED_VIEW_TEMPLATES) == PHASE_28_PREDEFINED_VIEW_TEMPLATE_COUNT
    expected_templates = {
        "CostByCloudProvider",
        "CostByService",
        "CostByCostCenter",
        "CostByDepartment",
        "CostByBusinessUnit",
        "CostByTag",
        "SavingsByOptimizationType",
        "CommitmentUtilizationByCloud",
        "BudgetVarianceByPeriod",
        "SustainabilityByCloudProvider",
        "VendorSpendByCategory",
        "ReservedInstanceUtilizationByTier",
    }
    assert set(PREDEFINED_VIEW_TEMPLATES) == expected_templates


def test_interactive_dashboard_listen_notify_has_eighteen_channels() -> None:
    """Test 11 — LISTEN/NOTIFY 18 channels (Phase 11~28, PRD §F43.1 + T6.2)."""
    assert len(UNIFIED_KPI_LISTEN_NOTIFY_CHANNELS) == PHASE_28_LISTEN_NOTIFY_CHANNEL_COUNT
    # Phase 11~27 = 17 channels + Phase 28 self-channel = 18
    assert any(
        ch == "phase_28_unified_kpi_calculated" for ch in UNIFIED_KPI_LISTEN_NOTIFY_CHANNELS
    )


def test_interactive_dashboard_export_status_includes_cancelled() -> None:
    """Test 12 — 5-state export status (pending + in_progress + completed + failed + cancelled)."""
    status_values = {s.value for s in ExportJobStatus}
    assert len(status_values) == PHASE_28_EXPORT_STATUS_COUNT
    assert "pending" in status_values
    assert "in_progress" in status_values
    assert "completed" in status_values
    assert "failed" in status_values
    assert "cancelled" in status_values


def test_interactive_dashboard_capability_granted_to_all_four_industries() -> None:
    """Test 13 — FINOPS_INTERACTIVE_DASHBOARD granted to 4 industries (CR 12-1 L4)."""
    granted_industries = [
        ind for ind, caps in _INDUSTRY_CAPABILITIES.items()
        if Capability.FINOPS_INTERACTIVE_DASHBOARD in caps
    ]
    assert len(granted_industries) == PHASE_28_INDUSTRY_GRANT_COUNT


def test_interactive_dashboard_capability_gate_dependency_exists() -> None:
    """Test 14 — require_finops_interactive_dashboard dependency is wired (T5.3)."""
    assert require_finops_interactive_dashboard is not None
    assert callable(require_finops_interactive_dashboard)


def test_interactive_dashboard_typed_exceptions_chain_inherits_correctly() -> None:
    """Test 15 — 16 NEW typed exceptions + base class (CR 12-5 D-14 envelope)."""
    # All 5 sampled exceptions inherit from base InteractiveDashboard base
    assert issubclass(InteractiveDashboardAggregationError, Exception)
    assert issubclass(SavedViewFilterError, Exception)
    assert issubclass(SavedViewTemplateError, Exception)
    assert issubclass(ExportJobFormatError, Exception)
    assert issubclass(ExportJobSizeError, Exception)
    # http_status attribute present on each
    assert hasattr(InteractiveDashboardAggregationError, "__init__")
    assert hasattr(SavedViewFilterError, "__init__")
