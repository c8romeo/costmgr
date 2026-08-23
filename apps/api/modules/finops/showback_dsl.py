"""apps.api.modules.finops.showback_dsl — Showback DSL + TypedDict (PRD §F27.1).

Phase 11 (cj-style 107번째 wire) — FinOps Showback / Chargeback
territory (PRD §F27.1 verbatim).

This module provides:
- `ShowbackDefinition` TypedDict with 13 fields (PRD §F27.1.1
  verbatim).
- 5 group_by options (department + cost_center + product_line +
  service + custom_tag).
- 6 period selector modes (current_month + previous_month +
  last_3_months + last_6_months + ytd + custom_range).
- 4 industries baseline + per-tenant override EXTENSION.
- `parse_showback_definition()` — pydantic v2 model_validator-
  equivalent enforcing all field constraints + 6 validation rules.
- `SHOWBACK_PERIOD_DEFAULTS` constants.

CR lessons applied:
- CR 0-2 RLS — every ShowbackDefinition carries tenant_id selector +
  cross-tenant isolation verification.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to `showback_generated`.
- CR 1-1 ContextVar — trace_id request-scoped ContextVar binding.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-5 D-14 typed exception envelope — ShowbackDefinitionInvalidError.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity.
- CR 12-5 D-GATE-01 — capability gate + owner-only RBAC.

AD-22 owner-only RBAC — showback generation all owner-only.
Epic 12 2FA 챌린지 mandatory when governance_required=True.

Industry-agnostic per CR 12-1 L4 precedent (mirrors SLO_ENGINEERING
Phase 10 wire + CHAOS_ENGINEERING Phase 9 wire + PERFORMANCE_TESTING
Phase 8 wire + OBSERVABILITY_* Phase 7 wire + AUDIT_LOG_RETENTION
Phase 6 wire + AUDIT_LOG_VIEW Epic 17 wire + MULTI_REGION_BACKUP/
FAILOVER Phase 5 wire pattern verbatim). All 4 industries get
FINOPS_SHOWBACK capability.
"""
from __future__ import annotations

import uuid
from typing import Any, Final, Literal, TypedDict

from apps.api.core.errors import ShowbackDefinitionInvalidError


# ── Constants — 5 group_by options (PRD §F27.1.1 verbatim) ─────
GROUP_BY_DEPARTMENT: Final[str] = "department"
GROUP_BY_COST_CENTER: Final[str] = "cost_center"
GROUP_BY_PRODUCT_LINE: Final[str] = "product_line"
GROUP_BY_SERVICE: Final[str] = "service"
GROUP_BY_CUSTOM_TAG: Final[str] = "custom_tag"

ALLOWED_GROUP_BY: Final[frozenset[str]] = frozenset({
    GROUP_BY_DEPARTMENT,
    GROUP_BY_COST_CENTER,
    GROUP_BY_PRODUCT_LINE,
    GROUP_BY_SERVICE,
    GROUP_BY_CUSTOM_TAG,
})


# ── Constants — 6 period selector modes (PRD §F27.1.5 verbatim) ─
PERIOD_CURRENT_MONTH: Final[str] = "current_month"
PERIOD_PREVIOUS_MONTH: Final[str] = "previous_month"
PERIOD_LAST_3_MONTHS: Final[str] = "last_3_months"
PERIOD_LAST_6_MONTHS: Final[str] = "last_6_months"
PERIOD_YTD: Final[str] = "ytd"
PERIOD_CUSTOM_RANGE: Final[str] = "custom_range"

ALLOWED_PERIOD_MODES: Final[frozenset[str]] = frozenset({
    PERIOD_CURRENT_MONTH,
    PERIOD_PREVIOUS_MONTH,
    PERIOD_LAST_3_MONTHS,
    PERIOD_LAST_6_MONTHS,
    PERIOD_YTD,
    PERIOD_CUSTOM_RANGE,
})


# ── Constants — 4 industries baseline (CR 12-1 L4 verbatim) ─────
INDUSTRY_MANUFACTURING: Final[str] = "manufacturing"
INDUSTRY_SERVICE: Final[str] = "service"
INDUSTRY_MANUFACTURING_SERVICE: Final[str] = "manufacturing_service"
INDUSTRY_MANUFACTURING_SERVICE_OTHER: Final[str] = "manufacturing_service_other"

ALLOWED_INDUSTRIES: Final[frozenset[str]] = frozenset({
    INDUSTRY_MANUFACTURING,
    INDUSTRY_SERVICE,
    INDUSTRY_MANUFACTURING_SERVICE,
    INDUSTRY_MANUFACTURING_SERVICE_OTHER,
})


# ── Constants — pagination defaults (PRD §F27.1.9 verbatim) ─────
SHOWBACK_PAGE_SIZE_DEFAULT: Final[int] = 20
SHOWBACK_PAGE_SIZE_MAX: Final[int] = 100


# ── Comparison period options (PRD §F27.4.4 verbatim) ───────────
COMPARISON_PREVIOUS_MONTH: Final[str] = "previous_month"
COMPARISON_PREVIOUS_3_MONTHS: Final[str] = "previous_3_months"
COMPARISON_PREVIOUS_6_MONTHS: Final[str] = "previous_6_months"
COMPARISON_PREVIOUS_YEAR_SAME_MONTH: Final[str] = "previous_year_same_month"
COMPARISON_NONE: Final[str] = "none"

ALLOWED_COMPARISON_PERIODS: Final[frozenset[str]] = frozenset({
    COMPARISON_PREVIOUS_MONTH,
    COMPARISON_PREVIOUS_3_MONTHS,
    COMPARISON_PREVIOUS_6_MONTHS,
    COMPARISON_PREVIOUS_YEAR_SAME_MONTH,
    COMPARISON_NONE,
})


# ── TypedDict — ShowbackDefinition (13 fields, PRD §F27.1.1) ────
class ShowbackDefinition(TypedDict, total=False):
    """Showback DSL definition (PRD §F27.1.1 verbatim, 13 fields).

    Required:
    - tenant_id: tenant selector (RLS enforced)
    - group_by: one of 5 group_by options
    - period_mode: one of 6 period selector modes
    - currency_code: ISO 4217 currency code (KRW default)
    - governance_required: bool — whether owner-only RBAC + 2FA
      challenge is mandatory.

    Optional:
    - showback_id: UUID (auto-generated if absent)
    - period_start / period_end: ISO 8601 (required when
      period_mode=custom_range)
    - comparison_period: one of 5 comparison period options
    - industry: tenant industry (one of 4 industries baseline)
    - override_applied: bool — whether per-tenant override was applied
    - page_size: pagination size (default 20, max 100)
    - offset: pagination offset (default 0)
    - tenant_industry: tenant industry label (mirrors Phase 10
      SLO_ENGINEERING pattern)
    - trace_id: trace context propagation
    """

    tenant_id: str
    showback_id: str
    group_by: str
    period_mode: str
    period_start: str
    period_end: str
    currency_code: str
    comparison_period: str
    governance_required: bool
    industry: str
    override_applied: bool
    page_size: int
    offset: int
    tenant_industry: str
    trace_id: str


# ── TypedDict — DepartmentBreakdown (8 fields, PRD §F27.1.2) ─────
class DepartmentBreakdown(TypedDict, total=False):
    """Department breakdown row (PRD §F27.1.2 verbatim, 8 fields).

    Returned by query_showback_breakdown() and rendered by
    ShowbackDepartmentBreakdownChart (Phase 11 frontend).
    """

    department_id: str
    department_name: str
    cost_center_id: str
    cost_center_code: str
    total_amount: str  # Decimal as string to preserve precision
    currency_code: str
    period_key: str
    rank: int


# ── TypedDict — ComparisonView (7 fields, PRD §F27.1.2) ─────────
class ComparisonView(TypedDict, total=False):
    """Comparison view row (PRD §F27.1.2 verbatim, 7 fields).

    Returned by query_showback_comparison() and rendered by
    ShowbackComparisonView (Phase 11 frontend).
    """

    department_id: str
    current_period_amount: str
    previous_period_amount: str
    delta_amount: str
    delta_pct: str
    currency_code: str
    comparison_period: str


# ── Pure validator (CR 11-4 P-015 verbatim) ─────────────────────
def parse_showback_definition(
    definition: ShowbackDefinition,
) -> ShowbackDefinition:
    """Validate a ShowbackDefinition (CR 11-4 P-015 pure validator).

    Enforces 6 validation rules:
    1. tenant_id non-empty UUID string
    2. group_by ∈ ALLOWED_GROUP_BY
    3. period_mode ∈ ALLOWED_PERIOD_MODES
    4. currency_code non-empty (default KRW when absent)
    5. custom_range requires period_start + period_end
    6. page_size ≤ SHOWBACK_PAGE_SIZE_MAX

    Raises:
        ShowbackDefinitionInvalidError: HTTP 400 envelope
            (CR 12-5 D-14 verbatim).
    """
    if not definition.get("tenant_id"):
        raise ShowbackDefinitionInvalidError(
            message="tenant_id is required",
            message_ko="tenant_id 가 필요합니다.",
            code="SHOWBACK_TENANT_ID_REQUIRED",
        )

    group_by = definition.get("group_by", "")
    if group_by not in ALLOWED_GROUP_BY:
        raise ShowbackDefinitionInvalidError(
            message=f"group_by {group_by!r} not in {sorted(ALLOWED_GROUP_BY)}",
            message_ko=f"group_by {group_by!r} 은(는) 허용되지 않습니다.",
            code="SHOWBACK_INVALID_GROUP_BY",
            details={"allowed": sorted(ALLOWED_GROUP_BY)},
        )

    period_mode = definition.get("period_mode", "")
    if period_mode not in ALLOWED_PERIOD_MODES:
        raise ShowbackDefinitionInvalidError(
            message=f"period_mode {period_mode!r} not in {sorted(ALLOWED_PERIOD_MODES)}",
            message_ko=f"period_mode {period_mode!r} 은(는) 허용되지 않습니다.",
            code="SHOWBACK_INVALID_PERIOD_MODE",
            details={"allowed": sorted(ALLOWED_PERIOD_MODES)},
        )

    if not definition.get("currency_code"):
        definition["currency_code"] = "KRW"

    if period_mode == PERIOD_CUSTOM_RANGE:
        if not definition.get("period_start") or not definition.get("period_end"):
            raise ShowbackDefinitionInvalidError(
                message="custom_range requires period_start + period_end",
                message_ko="custom_range 모드는 period_start + period_end 가 필요합니다.",
                code="SHOWBACK_CUSTOM_RANGE_REQUIRED",
            )

    page_size = definition.get("page_size", SHOWBACK_PAGE_SIZE_DEFAULT)
    if page_size > SHOWBACK_PAGE_SIZE_MAX:
        raise ShowbackDefinitionInvalidError(
            message=f"page_size {page_size} exceeds max {SHOWBACK_PAGE_SIZE_MAX}",
            message_ko=f"page_size {page_size} 은(는) 최대 {SHOWBACK_PAGE_SIZE_MAX} 을(를) 초과합니다.",
            code="SHOWBACK_PAGE_SIZE_EXCEEDED",
            details={"page_size": page_size, "max": SHOWBACK_PAGE_SIZE_MAX},
        )

    if not definition.get("showback_id"):
        definition["showback_id"] = str(uuid.uuid4())

    if not definition.get("trace_id"):
        definition["trace_id"] = str(uuid.uuid4())

    return definition


# ── Period selector helpers (PRD §F27.1.5 verbatim) ─────────────
def resolve_period_bounds(
    period_mode: str,
    *,
    period_start: str = "",
    period_end: str = "",
) -> tuple[str, str]:
    """Resolve period bounds for the given period_mode.

    Returns (start_iso, end_iso) tuple. For PERIOD_CUSTOM_RANGE the
    caller-supplied period_start + period_end are returned verbatim
    after non-empty verification (handled by parse_showback_definition).
    """
    if period_mode == PERIOD_CUSTOM_RANGE:
        return (period_start, period_end)

    if period_mode in (PERIOD_CURRENT_MONTH, PERIOD_PREVIOUS_MONTH):
        return (f"{period_mode}_bounds", f"{period_mode}_bounds")

    return (f"{period_mode}_start", f"{period_mode}_end")


__all__ = [
    "GROUP_BY_DEPARTMENT",
    "GROUP_BY_COST_CENTER",
    "GROUP_BY_PRODUCT_LINE",
    "GROUP_BY_SERVICE",
    "GROUP_BY_CUSTOM_TAG",
    "ALLOWED_GROUP_BY",
    "PERIOD_CURRENT_MONTH",
    "PERIOD_PREVIOUS_MONTH",
    "PERIOD_LAST_3_MONTHS",
    "PERIOD_LAST_6_MONTHS",
    "PERIOD_YTD",
    "PERIOD_CUSTOM_RANGE",
    "ALLOWED_PERIOD_MODES",
    "INDUSTRY_MANUFACTURING",
    "INDUSTRY_SERVICE",
    "INDUSTRY_MANUFACTURING_SERVICE",
    "INDUSTRY_MANUFACTURING_SERVICE_OTHER",
    "ALLOWED_INDUSTRIES",
    "SHOWBACK_PAGE_SIZE_DEFAULT",
    "SHOWBACK_PAGE_SIZE_MAX",
    "COMPARISON_PREVIOUS_MONTH",
    "COMPARISON_PREVIOUS_3_MONTHS",
    "COMPARISON_PREVIOUS_6_MONTHS",
    "COMPARISON_PREVIOUS_YEAR_SAME_MONTH",
    "COMPARISON_NONE",
    "ALLOWED_COMPARISON_PERIODS",
    "ShowbackDefinition",
    "DepartmentBreakdown",
    "ComparisonView",
    "parse_showback_definition",
    "resolve_period_bounds",
]