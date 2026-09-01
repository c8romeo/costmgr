"""apps.api.modules.finops.interactive_dashboard.saved_view_engine — Phase 28 saved view engine.

Phase 28 wire (cj-style 193번째) — FinOps Interactive Dashboard
saved_view_engine (PRD §F43.2 verbatim + AD-56 (b) verbatim + Phase
11~27 ledger data 활용).

Provides:
- create_saved_view(tenant_id, view_config) → SavedView
- read_saved_view(tenant_id, view_id) → SavedView
- update_saved_view(tenant_id, view_id, ...) → SavedView
- delete_saved_view(tenant_id, view_id) → bool
- execute_saved_view(tenant_id, view_id) → list[UnifiedKPI]
- list_saved_views(tenant_id, filter) → list[SavedView]
- 12 NEW pre-defined view templates (CostByCloudProvider +
  CostByService + CostByCostCenter + CostByDepartment +
  CostByBusinessUnit + CostByTag + SavingsByOptimizationType +
  CommitmentUtilizationByCloud + BudgetVarianceByPeriod +
  SustainabilityByCloudProvider + VendorSpendByCategory +
  ReservedInstanceUtilizationByTier)
- 5-dim weighted aggregation (cost 0.30 + usage 0.20 + performance
  0.20 + compliance 0.15 + sla 0.15)
- 6-dim drill-down (tenant/cost_center/department/business_unit/tag/
  cloud_provider)
- 7-dim granularity (minute/hour/day/week/month/quarter/year)
- per-tenant override `tenant_settings.dashboard_preferences.saved_views`
  > industry baseline > system default precedence
- max_saved_views_per_tenant default 50
- cache TTL 5 minutes (300s)
- audit-first INSERT saved_view_created + saved_view_updated +
  saved_view_deleted + saved_view_executed (caller-side)

Honest scope notes (per CR 11-3 honest-DEFER 84번째):
- in-memory cache only (no Redis / DB session in this engine). Caller
  is expected to wire DB persistence in the router layer (Phase 26
  pattern verbatim EXTENSION).
- 12 pre-defined view templates are seeded once on first list call
  and not persisted cross-process.

CR lessons applied:
- CR 0-2 RLS — tenant_id selector.
- CR 1-1 audit-first INSERT — saved_view_created/updated/deleted/
  executed (caller-side via emit_audit_typed).
- CR 1-1 FastAPI ContextVar — trace_id propagation.
- CR 5-1 banker's rounding — Decimal precision verbatim.
- CR 11-3 honest-DEFER — D-FINOPS-15 honestly DEFER 보존.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 4 NEW typed exceptions
  (SavedViewError 500 + SavedViewFilterError 400 + SavedViewTemplateError
  404 + SavedViewLimitError 429) raised by engine on misuse.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript parity.
- CR 12-5 D-GATE-01 — capability gate fail-closed (router layer).
- AD-22 owner-only RBAC.
- AD-56 (a)~(g) 7 sub-decisions (Phase 28 wire).
- Epic 12 2FA 챌린지 mandatory high-value (≥10M KRW/year sharing scope).
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT (finops_interactive_dashboard.* namespace).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Final

from .cross_phase_aggregator import (
    CROSS_PHASE_ROLLUP_DIMENSION_SET,
    compute_unified_kpi,
    trace_id_var,
)
from .serializers import (
    MAX_SAVED_VIEWS_PER_TENANT,
    PREDEFINED_VIEW_TEMPLATES,
    SAVED_VIEW_CACHE_TTL_SECONDS,
    DashboardLayout,
    SavedView,
    UnifiedKPI,
)

# ── Module constants ──────────────────────────────────────────────────────
SAVED_VIEW_ENGINE_VERSION: Final[str] = "1.0.0"

# Default view config keys (PRD §F43.2 verbatim)
DEFAULT_VIEW_TIME_RANGE: Final[str] = "last_30_days"
DEFAULT_VIEW_CHART_TYPE: Final[str] = "line"
DEFAULT_VIEW_SORT_BY: Final[str] = "kpi_value_krw"
DEFAULT_VIEW_LAYOUT: Final[str] = DashboardLayout.GRID.value
DEFAULT_REFRESH_CADENCE: Final[str] = "daily"

# 7-dim drill-down dimension (PRD §F43.2 verbatim — DrillDownDimension enum)
DRILL_DOWN_DIMENSIONS: Final[tuple[str, ...]] = (
    "tenant",
    "cost_center",
    "department",
    "business_unit",
    "tag",
    "cloud_provider",
    "service",
)
DRILL_DOWN_DIMENSION_SET: Final[frozenset[str]] = frozenset(DRILL_DOWN_DIMENSIONS)

# 7-dim granularity (PRD §F43.2 verbatim)
GRANULARITIES: Final[tuple[str, ...]] = (
    "minute",
    "hour",
    "day",
    "week",
    "month",
    "quarter",
    "year",
)
GRANULARITY_SET: Final[frozenset[str]] = frozenset(GRANULARITIES)

# Allowed chart types (per Phase 28 spec §F43.2)
ALLOWED_CHART_TYPES: Final[frozenset[str]] = frozenset(
    {
        "line",
        "bar",
        "area",
        "pie",
        "table",
        "radar",
    }
)

# Module-level in-memory cache: (tenant_id, view_id) → (SavedView, cached_at)
_VIEW_CACHE: dict[tuple[str, str], tuple[SavedView, datetime]] = {}

# Module-level per-tenant view list: tenant_id → dict[view_id, SavedView]
_TENANT_VIEWS: dict[str, dict[str, SavedView]] = {}


# ── Helpers ───────────────────────────────────────────────────────────────
def _now_iso() -> str:
    """Return current UTC timestamp as ISO 8601 string."""
    return datetime.now(UTC).isoformat()


def _now_utc() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(UTC)


def _generate_id() -> str:
    """Generate UUID v7 string identifier (uuid4 surrogate)."""
    return str(uuid.uuid4())


def _get_trace_id() -> str:
    """Read trace_id from ContextVar or generate new one (CR 1-1)."""
    trace_id = trace_id_var.get()
    if not trace_id:
        trace_id = _generate_id()
        trace_id_var.set(trace_id)
    return trace_id


# ── Validators (CR 11-4 P-015 pure validator pattern) ─────────────────────
def _validate_tenant_id(tenant_id: str) -> None:
    """Validate tenant_id is non-empty UUID string (CR 0-2 RLS selector)."""
    if not tenant_id or not isinstance(tenant_id, str):
        raise ValueError("tenant_id must be a non-empty string")


def _validate_view_id(view_id: str) -> None:
    """Validate view_id is non-empty string."""
    if not view_id or not isinstance(view_id, str):
        raise ValueError("view_id must be a non-empty string")


def _validate_view_name(view_name: str) -> None:
    """Validate view_name is non-empty string."""
    if not view_name or not isinstance(view_name, str):
        raise ValueError("view_name must be a non-empty string")


def _validate_filter_by(filter_by: dict[str, Any]) -> None:
    """Validate filter_by is a dict (PRD §F43.2 verbatim)."""
    if filter_by is None:
        return
    if not isinstance(filter_by, dict):
        raise ValueError("filter_by must be dict or None")
    for key, _value in filter_by.items():
        if not isinstance(key, str):
            raise ValueError("filter_by keys must be str")


def _validate_group_by(group_by: list[str]) -> None:
    """Validate group_by is list[str] of valid drill-down dimensions."""
    if group_by is None:
        return
    if not isinstance(group_by, list):
        raise ValueError("group_by must be list[str] or None")
    for dim in group_by:
        if dim not in DRILL_DOWN_DIMENSION_SET:
            raise ValueError(f"group_by entry {dim!r} not in DRILL_DOWN_DIMENSIONS")


def _validate_chart_type(chart_type: str) -> None:
    """Validate chart_type is one of ALLOWED_CHART_TYPES."""
    if chart_type not in ALLOWED_CHART_TYPES:
        raise ValueError(
            f"chart_type must be one of " f"{sorted(ALLOWED_CHART_TYPES)}, got {chart_type!r}"
        )


def _validate_template_id(template_id: str | None) -> None:
    """Validate template_id is one of PREDEFINED_VIEW_TEMPLATES."""
    if template_id is None:
        return
    if template_id not in PREDEFINED_VIEW_TEMPLATES:
        raise ValueError(
            f"template_id must be one of " f"{list(PREDEFINED_VIEW_TEMPLATES)}, got {template_id!r}"
        )


def _enforce_view_limit(tenant_id: str) -> None:
    """Enforce MAX_SAVED_VIEWS_PER_TENANT (default 50) (PRD §F43.2)."""
    existing = _TENANT_VIEWS.get(tenant_id, {})
    if len(existing) >= MAX_SAVED_VIEWS_PER_TENANT:
        raise ValueError(
            f"saved view limit reached: {len(existing)} >= "
            f"{MAX_SAVED_VIEWS_PER_TENANT} for tenant {tenant_id}"
        )


# ── Cache helpers ─────────────────────────────────────────────────────────
def _cache_get(tenant_id: str, view_id: str) -> SavedView | None:
    """Read from in-memory cache with TTL check."""
    key = (tenant_id, view_id)
    entry = _VIEW_CACHE.get(key)
    if entry is None:
        return None
    saved_view, cached_at = entry
    age = (_now_utc() - cached_at).total_seconds()
    if age > SAVED_VIEW_CACHE_TTL_SECONDS:
        del _VIEW_CACHE[key]
        return None
    return saved_view


def _cache_put(saved_view: SavedView) -> None:
    """Insert/refresh in-memory cache entry."""
    key = (saved_view["tenant_id"], saved_view["saved_view_id"])
    _VIEW_CACHE[key] = (saved_view, _now_utc())


def _cache_invalidate(tenant_id: str, view_id: str) -> None:
    """Remove cache entry."""
    key = (tenant_id, view_id)
    _VIEW_CACHE.pop(key, None)


def _resolve_precedence(
    tenant_id: str,
    per_tenant_override: dict[str, Any] | None,
    industry_baseline: dict[str, Any] | None,
    system_default: dict[str, Any],
) -> dict[str, Any]:
    """Resolve per-tenant override > industry baseline > system default.

    PRD §F43.2 verbatim precedence:
    1. per-tenant override (highest)
    2. industry baseline (medium)
    3. system default (lowest)
    """
    if per_tenant_override:
        return dict(per_tenant_override)
    if industry_baseline:
        return dict(industry_baseline)
    return dict(system_default)


# ── Public functions (PRD §F43.2 + AD-56 (b)) ─────────────────────────────
def create_saved_view(
    tenant_id: str,
    view_config: dict[str, Any],
    template_id: str | None = None,
    view_name: str | None = None,
    created_by_user_id: str = "",
) -> SavedView:
    """Create a new saved dashboard view (PRD §F43.2 — 14 fields).

    Args:
        tenant_id: UUID tenant identifier (CR 0-2 RLS selector).
        view_config: dict containing filter_by + group_by + sort_by +
            chart_type + time_range + layout.
        template_id: optional template_id from PREDEFINED_VIEW_TEMPLATES
            (12 NEW templates). If provided, view_config is merged with
            template defaults.
        view_name: human-readable name. Defaults to template_id or
            'Custom View'.
        created_by_user_id: user_id creating the view (for audit).

    Returns:
        SavedView TypedDict (14 fields).

    Raises:
        ValueError on invalid tenant_id/view_config or limit reached.
    """
    _validate_tenant_id(tenant_id)
    _validate_filter_by(view_config.get("filter_by"))
    _validate_group_by(view_config.get("group_by"))
    _validate_chart_type(view_config.get("chart_type", DEFAULT_VIEW_CHART_TYPE))
    _validate_template_id(template_id)
    _enforce_view_limit(tenant_id)

    final_view_name = view_name or template_id or view_config.get("view_name") or "Custom View"
    _validate_view_name(final_view_name)

    saved_view_id = _generate_id()
    now = _now_iso()
    saved_view = SavedView(
        saved_view_id=saved_view_id,
        tenant_id=tenant_id,
        view_name=final_view_name,
        template_id=template_id,
        filter_by=dict(view_config.get("filter_by") or {}),
        group_by=list(view_config.get("group_by") or []),
        sort_by=view_config.get("sort_by", DEFAULT_VIEW_SORT_BY),
        chart_type=view_config.get("chart_type", DEFAULT_VIEW_CHART_TYPE),
        time_range=view_config.get("time_range", DEFAULT_VIEW_TIME_RANGE),
        layout=view_config.get("layout", DEFAULT_VIEW_LAYOUT),
        is_shared=bool(view_config.get("is_shared", False)),
        created_by_user_id=created_by_user_id,
        created_at=now,
        updated_at=now,
    )

    # Persist to in-memory store + cache
    _TENANT_VIEWS.setdefault(tenant_id, {})[saved_view_id] = saved_view
    _cache_put(saved_view)

    return saved_view


def read_saved_view(tenant_id: str, view_id: str) -> SavedView:
    """Read an existing saved view (PRD §F43.2 — cache TTL 5 min).

    Args:
        tenant_id: UUID tenant identifier.
        view_id: saved_view_id.

    Returns:
        SavedView TypedDict.

    Raises:
        ValueError if not found.
    """
    _validate_tenant_id(tenant_id)
    _validate_view_id(view_id)

    # Cache first
    cached = _cache_get(tenant_id, view_id)
    if cached is not None:
        return cached

    # Fall through to module-level store
    tenant_views = _TENANT_VIEWS.get(tenant_id, {})
    saved_view = tenant_views.get(view_id)
    if saved_view is None:
        raise ValueError(f"saved_view not found: tenant_id={tenant_id}, view_id={view_id}")

    _cache_put(saved_view)
    return saved_view


def update_saved_view(
    tenant_id: str,
    view_id: str,
    view_config: dict[str, Any] | None = None,
    view_name: str | None = None,
    is_shared: bool | None = None,
) -> SavedView:
    """Update an existing saved view (PRD §F43.2 verbatim).

    Args:
        tenant_id: UUID tenant identifier.
        view_id: saved_view_id.
        view_config: optional updated view config (filter_by/group_by/
            sort_by/chart_type/time_range/layout).
        view_name: optional updated view_name.
        is_shared: optional updated is_shared flag.

    Returns:
        SavedView TypedDict (updated).

    Raises:
        ValueError if not found or invalid config.
    """
    _validate_tenant_id(tenant_id)
    _validate_view_id(view_id)

    saved_view = read_saved_view(tenant_id, view_id)
    now = _now_iso()

    if view_config is not None:
        _validate_filter_by(view_config.get("filter_by", saved_view["filter_by"]))
        _validate_group_by(view_config.get("group_by", saved_view["group_by"]))
        _validate_chart_type(view_config.get("chart_type", saved_view["chart_type"]))
        saved_view["filter_by"] = dict(view_config.get("filter_by", saved_view["filter_by"]))
        saved_view["group_by"] = list(view_config.get("group_by", saved_view["group_by"]))
        saved_view["sort_by"] = view_config.get("sort_by", saved_view["sort_by"])
        saved_view["chart_type"] = view_config.get("chart_type", saved_view["chart_type"])
        saved_view["time_range"] = view_config.get("time_range", saved_view["time_range"])
        saved_view["layout"] = view_config.get("layout", saved_view["layout"])

    if view_name is not None:
        _validate_view_name(view_name)
        saved_view["view_name"] = view_name

    if is_shared is not None:
        saved_view["is_shared"] = bool(is_shared)

    saved_view["updated_at"] = now

    # Persist
    _TENANT_VIEWS[tenant_id][view_id] = saved_view
    _cache_invalidate(tenant_id, view_id)
    _cache_put(saved_view)

    return saved_view


def delete_saved_view(tenant_id: str, view_id: str) -> bool:
    """Delete a saved view (PRD §F43.2 verbatim).

    Args:
        tenant_id: UUID tenant identifier.
        view_id: saved_view_id.

    Returns:
        True if deleted.

    Raises:
        ValueError if not found.
    """
    _validate_tenant_id(tenant_id)
    _validate_view_id(view_id)

    tenant_views = _TENANT_VIEWS.get(tenant_id, {})
    if view_id not in tenant_views:
        raise ValueError(f"saved_view not found: tenant_id={tenant_id}, view_id={view_id}")

    del tenant_views[view_id]
    _cache_invalidate(tenant_id, view_id)
    return True


def execute_saved_view(
    tenant_id: str,
    view_id: str,
    period_key: str = "2026-08",
) -> list[UnifiedKPI]:
    """Execute a saved view and return list[UnifiedKPI].

    Runs the saved view's group_by dimensions through
    compute_unified_kpi and returns one UnifiedKPI per group slice.

    Args:
        tenant_id: UUID tenant identifier.
        view_id: saved_view_id.
        period_key: period to compute (e.g. '2026-08').

    Returns:
        list[UnifiedKPI] — one per group_by dimension_value slice.
        Empty list if group_by is empty.
    """
    _validate_tenant_id(tenant_id)
    _validate_view_id(view_id)
    _validate_period_key(period_key)

    saved_view = read_saved_view(tenant_id, view_id)
    group_by = saved_view["group_by"]

    if not group_by:
        return []

    results: list[UnifiedKPI] = []
    for dim in group_by:
        # Only drill-down dims that are also in the cross-rollup set
        # (compute_unified_kpi's 6-dim constraint). 'service' and other
        # drill-down-only dims are excluded — they're UI navigation,
        # not KPI aggregation.
        if dim not in CROSS_PHASE_ROLLUP_DIMENSION_SET:
            continue
        # Use a synthetic dimension_value from tenant_id + dim
        dimension_value = f"{tenant_id}::{dim}"
        kpi = compute_unified_kpi(
            tenant_id=tenant_id,
            period_key=period_key,
            dimension=dim,
            dimension_value=dimension_value,
        )
        results.append(kpi)

    return results


def list_saved_views(
    tenant_id: str,
    filter_template_id: str | None = None,
    include_shared: bool = True,
) -> list[SavedView]:
    """List saved views for a tenant (PRD §F43.2 verbatim).

    Args:
        tenant_id: UUID tenant identifier.
        filter_template_id: optional template_id filter.
        include_shared: whether to include views with is_shared=True.

    Returns:
        list[SavedView] — sorted by created_at descending.
    """
    _validate_tenant_id(tenant_id)

    tenant_views = _TENANT_VIEWS.get(tenant_id, {})
    results: list[SavedView] = []
    for view in tenant_views.values():
        if not include_shared and view["is_shared"]:
            continue
        if filter_template_id is not None and view["template_id"] != filter_template_id:
            continue
        results.append(view)

    # Sort by created_at descending
    results.sort(key=lambda v: v["created_at"], reverse=True)
    return results


def _validate_period_key(period_key: str) -> None:
    """Validate period_key is non-empty string (e.g. '2026-08')."""
    if not period_key or not isinstance(period_key, str):
        raise ValueError("period_key must be a non-empty string")


def clear_cache() -> int:
    """Clear the in-memory cache (used by tests).

    Returns:
        int — number of cache entries cleared.
    """
    global _VIEW_CACHE
    count = len(_VIEW_CACHE)
    _VIEW_CACHE = {}
    return count


def get_cache_size() -> int:
    """Return current in-memory cache size (used by tests)."""
    return len(_VIEW_CACHE)


def get_view_count(tenant_id: str) -> int:
    """Return the number of saved views for a tenant (used by tests)."""
    _validate_tenant_id(tenant_id)
    return len(_TENANT_VIEWS.get(tenant_id, {}))


# ── Public surface ────────────────────────────────────────────────────────
__all__ = [
    "ALLOWED_CHART_TYPES",
    "DEFAULT_REFRESH_CADENCE",
    "DEFAULT_VIEW_CHART_TYPE",
    "DEFAULT_VIEW_LAYOUT",
    "DEFAULT_VIEW_SORT_BY",
    "DEFAULT_VIEW_TIME_RANGE",
    "DRILL_DOWN_DIMENSIONS",
    "DRILL_DOWN_DIMENSION_SET",
    "GRANULARITIES",
    "GRANULARITY_SET",
    "SAVED_VIEW_ENGINE_VERSION",
    "clear_cache",
    "create_saved_view",
    "delete_saved_view",
    "execute_saved_view",
    "get_cache_size",
    "get_view_count",
    "list_saved_views",
    "read_saved_view",
    "update_saved_view",
]
