"""apps.api.modules.finops.interactive_dashboard — Phase 28 territory root.

Phase 28 wire (cj-style 193번째) — FinOps Interactive Dashboard
territory root (PRD §F43.1~§F43.8 verbatim + AD-56 (a)~(g) 7
sub-decisions + Phase 11~27 18-capability FinOps territory ledger
data 활용).

This module re-exports the public surface of the
`interactive_dashboard` submodule (Phase 28 territory):
- cross_phase_aggregator (T1.3)
- saved_view_engine (T1.4)
- export_pipeline (T1.5)
- serializers (T1.2)

Architecture sweep note (per CR 11-3 ALLOWED_SERVICE_SUBMODULES sweep):
Phase 28 wire 진입 시점에 `apps/api/modules/finops/__init__.py` 의
submodule 목록 즉시 sweep EXTENSION + `tests/architecture/
test_api_calls_only_ports.py` 의 ALLOWED_SERVICE_SUBMODULES 신규 등록
= `m28_finops_interactive_dashboard` (Phase 22 m22 ~ Phase 26 m34
verbatim EXTENSION 패턴).

Module tag: m28_finops_interactive_dashboard

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — 8 NEW audit actions via
  ActionClass.FINOPS_INTERACTIVE_DASHBOARD (T4.2).
- CR 1-1 FastAPI ContextVar — trace_id propagation.
- CR 5-1 banker's rounding — Decimal precision verbatim.
- CR 11-3 honest-DEFER — D-FINOPS-15 honestly DEFER 보존.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 16 NEW typed exceptions.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript parity.
- CR 12-5 D-GATE-01 — capability gate fail-closed.
- AD-22 owner-only RBAC.
- AD-56 (a)~(g) 7 sub-decisions (Phase 28 wire).
- Epic 12 2FA 챌린지 mandatory high-value (≥10M KRW/year sharing scope).
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT (finops_interactive_dashboard.* namespace).
"""

from __future__ import annotations

# Re-export public surface from sibling submodules
from . import (
    cross_phase_aggregator,
    export_pipeline,
    saved_view_engine,
    serializers,
)

# Re-export key names from cross_phase_aggregator
from .cross_phase_aggregator import (
    CROSS_PHASE_AGGREGATOR_ENGINE_VERSION,
    CROSS_PHASE_ROLLUP_DIMENSION_SET,
    CROSS_PHASE_ROLLUP_DIMENSIONS,
    PHASE_LEDGER_MAX_PHASE,
    PHASE_LEDGER_MIN_PHASE,
    PHASE_LEDGER_PHASE_COUNT,
    aggregate_cross_phase_breakdown,
    compute_unified_kpi,
    list_cross_phase_rollup_dimensions,
    list_phase_kpi_source_modules,
    realtime_incremental_update_via_listen_notify,
    trace_id_var,
)

# Re-export key names from export_pipeline
from .export_pipeline import (
    ALLOWED_STATUS_TRANSITIONS as EXPORT_ALLOWED_STATUS_TRANSITIONS,
)
from .export_pipeline import (
    COMPLETED_PROGRESS_PCT,
    DEFAULT_EXPORT_EXPIRES_DAYS,
    DEFAULT_PROGRESS_PCT,
    EXPORT_PIPELINE_ENGINE_VERSION,
    cancel_export_job,
    clear_export_jobs,
    compute_retry_count,
    get_export_job_count,
    get_export_job_status,
    list_export_jobs,
    mark_export_job_failed,
    start_export_job,
    update_export_job_progress,
)

# Re-export key names from saved_view_engine
from .saved_view_engine import (
    ALLOWED_CHART_TYPES,
    DEFAULT_REFRESH_CADENCE,
    DEFAULT_VIEW_CHART_TYPE,
    DEFAULT_VIEW_LAYOUT,
    DEFAULT_VIEW_SORT_BY,
    DEFAULT_VIEW_TIME_RANGE,
    DRILL_DOWN_DIMENSION_SET,
    DRILL_DOWN_DIMENSIONS,
    GRANULARITIES,
    GRANULARITY_SET,
    SAVED_VIEW_ENGINE_VERSION,
    create_saved_view,
    delete_saved_view,
    execute_saved_view,
    get_view_count,
    list_saved_views,
    read_saved_view,
    update_saved_view,
)
from .saved_view_engine import (
    clear_cache as clear_saved_view_cache,
)
from .saved_view_engine import (
    get_cache_size as get_saved_view_cache_size,
)

# Re-export key names from serializers
from .serializers import (
    DASHBOARD_CADENCE_HOURS,
    DASHBOARD_CADENCE_HOURS_KST,
    DASHBOARD_DEFAULTS,
    DASHBOARD_KPI_DIMENSION_WEIGHTS,
    DASHBOARD_RECIPIENT_TEMPLATES,
    DASHBOARD_ROUTER_PREFIX,
    EXPORT_MAX_RETRIES,
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    INTERACTIVE_DASHBOARD_ENGINE_VERSION,
    MAX_EXPORT_SIZE_BYTES,
    MAX_SAVED_VIEWS_PER_TENANT,
    MODULE_TAG,
    PHASE_KPI_SOURCE_MODULES,
    PREDEFINED_VIEW_TEMPLATES,
    SAVED_VIEW_CACHE_TTL_SECONDS,
    SHARING_EXPIRES_DEFAULT_DAYS,
    TOTAL_VERIFICATION_TOLERANCE_KRW,
    UNIFIED_KPI_LISTEN_NOTIFY_CHANNELS,
    DashboardLayout,  # noqa: F401
    DashboardSharingScope,  # noqa: F401
    DrillDownContext,  # noqa: F401
    DrillDownDimension,  # noqa: F401
    DrillDownGranularity,  # noqa: F401
    ExportFormat,  # noqa: F401
    ExportJob,  # noqa: F401
    ExportJobStatus,  # noqa: F401
    KPIBreakdown,  # noqa: F401
    KPIRefreshCadence,  # noqa: F401
    SavedView,  # noqa: F401
    SharingGrant,  # noqa: F401
    UnifiedKPI,  # noqa: F401
)

# Phase 28 territory version
INTERACTIVE_DASHBOARD_TERRITORY_VERSION = "1.0.0"

__all__ = [
    "ALLOWED_CHART_TYPES",
    "COMPLETED_PROGRESS_PCT",
    "CROSS_PHASE_AGGREGATOR_ENGINE_VERSION",
    "CROSS_PHASE_ROLLUP_DIMENSIONS",
    "CROSS_PHASE_ROLLUP_DIMENSION_SET",
    "DASHBOARD_CADENCE_HOURS",
    "DASHBOARD_CADENCE_HOURS_KST",
    "DASHBOARD_DEFAULTS",
    "DASHBOARD_KPI_DIMENSION_WEIGHTS",
    "DASHBOARD_RECIPIENT_TEMPLATES",
    "DASHBOARD_ROUTER_PREFIX",
    "DEFAULT_EXPORT_EXPIRES_DAYS",
    "DEFAULT_PROGRESS_PCT",
    "DEFAULT_REFRESH_CADENCE",
    "DEFAULT_VIEW_CHART_TYPE",
    "DEFAULT_VIEW_LAYOUT",
    "DEFAULT_VIEW_SORT_BY",
    "DEFAULT_VIEW_TIME_RANGE",
    "DRILL_DOWN_DIMENSIONS",
    "DRILL_DOWN_DIMENSION_SET",
    "EXPORT_ALLOWED_STATUS_TRANSITIONS",
    "EXPORT_MAX_RETRIES",
    "EXPORT_PIPELINE_ENGINE_VERSION",
    "GRANULARITIES",
    "GRANULARITY_SET",
    "HIGH_VALUE_THRESHOLD_KRW_PER_YEAR",
    "INTERACTIVE_DASHBOARD_ENGINE_VERSION",
    "INTERACTIVE_DASHBOARD_TERRITORY_VERSION",
    "MAX_EXPORT_SIZE_BYTES",
    "MAX_SAVED_VIEWS_PER_TENANT",
    "MODULE_TAG",
    "PHASE_KPI_SOURCE_MODULES",
    "PHASE_LEDGER_MAX_PHASE",
    "PHASE_LEDGER_MIN_PHASE",
    "PHASE_LEDGER_PHASE_COUNT",
    "PREDEFINED_VIEW_TEMPLATES",
    "SAVED_VIEW_CACHE_TTL_SECONDS",
    "SAVED_VIEW_ENGINE_VERSION",
    "SHARING_EXPIRES_DEFAULT_DAYS",
    "TOTAL_VERIFICATION_TOLERANCE_KRW",
    "UNIFIED_KPI_LISTEN_NOTIFY_CHANNELS",
    "aggregate_cross_phase_breakdown",
    "cancel_export_job",
    "clear_export_jobs",
    "clear_saved_view_cache",
    "compute_retry_count",
    "compute_unified_kpi",
    "create_saved_view",
    "cross_phase_aggregator",
    "delete_saved_view",
    "execute_saved_view",
    "export_pipeline",
    "get_export_job_count",
    "get_export_job_status",
    "get_saved_view_cache_size",
    "get_view_count",
    "list_cross_phase_rollup_dimensions",
    "list_export_jobs",
    "list_phase_kpi_source_modules",
    "list_saved_views",
    "mark_export_job_failed",
    "read_saved_view",
    "realtime_incremental_update_via_listen_notify",
    "saved_view_engine",
    "serializers",
    "start_export_job",
    "trace_id_var",
    "update_export_job_progress",
    "update_saved_view",
]
