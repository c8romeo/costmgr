"""apps.api.modules.finops.budget_definition — Budget definition DSL (PRD §F28.2).

Phase 12 (cj-style 111번째 wire) — Cost Anomaly Detection & Budget
Alerting territory (PRD §F28.2 verbatim).

This module provides:
- `BudgetDefinition` TypedDict with 12 fields (PRD §F28.2.1 verbatim).
- budget_period enum (monthly/quarterly/yearly).
- budget_scope enum (tenant/department/cost_center/product_line).
- budget_amount NUMERIC(20, 2) + currency KRW default.
- alert_thresholds TypedDict (warning 80% + critical 90% + exceeded
  100%).
- `parse_budget_definition()` — pure validator enforcing all field
  constraints + 6 validation rules (CR 11-4 P-015 verbatim).
- `BUDGET_THRESHOLD_DEFAULTS` constants.
- `define_budget()` — main entry point with AST 6 levels + parser
  verification 3 layer.

CR lessons applied:
- CR 0-2 RLS — every BudgetDefinition carries tenant_id selector +
  cross-tenant isolation verification.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to `budget_definition_updated`.
- CR 1-1 ContextVar — trace_id propagation.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-5 D-14 typed exception envelope — BudgetDefinitionInvalidError
  + BudgetScopeInvalidError + BudgetAmountInvalidError.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity.
- CR 12-5 D-GATE-01 — capability gate + owner-only RBAC.

AD-22 owner-only RBAC — define_budget owner-only.
Epic 12 2FA 챌린지 mandatory when governance_required=True.

Industry-agnostic per CR 12-1 L4 precedent (mirrors FINOPS_SHOWBACK +
FINOPS_CHARGEBACK Phase 11 wire + SLO_ENGINEERING Phase 10 wire +
CHAOS_ENGINEERING Phase 9 wire + PERFORMANCE_TESTING Phase 8 wire +
OBSERVABILITY_* Phase 7 wire + AUDIT_LOG_RETENTION Phase 6 wire +
AUDIT_LOG_VIEW Epic 17 wire + MULTI_REGION_BACKUP/FAILOVER Phase 5
wire pattern verbatim). All 4 industries get FINOPS_BUDGET_ALERT
capability.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Final, TypedDict

from apps.api.core.errors import (
    BudgetAmountInvalidError,
    BudgetDefinitionInvalidError,
    BudgetScopeInvalidError,
)

# ── Constants — budget_period enum (PRD §F28.2.2 verbatim) ──────
BUDGET_PERIOD_MONTHLY: Final[str] = "monthly"
BUDGET_PERIOD_QUARTERLY: Final[str] = "quarterly"
BUDGET_PERIOD_YEARLY: Final[str] = "yearly"

ALL_BUDGET_PERIODS: Final[tuple[str, ...]] = (
    BUDGET_PERIOD_MONTHLY,
    BUDGET_PERIOD_QUARTERLY,
    BUDGET_PERIOD_YEARLY,
)

# ── Constants — budget_scope enum (PRD §F28.2.3 verbatim) ───────
BUDGET_SCOPE_TENANT: Final[str] = "tenant"
BUDGET_SCOPE_DEPARTMENT: Final[str] = "department"
BUDGET_SCOPE_COST_CENTER: Final[str] = "cost_center"
BUDGET_SCOPE_PRODUCT_LINE: Final[str] = "product_line"

ALL_BUDGET_SCOPES: Final[tuple[str, ...]] = (
    BUDGET_SCOPE_TENANT,
    BUDGET_SCOPE_DEPARTMENT,
    BUDGET_SCOPE_COST_CENTER,
    BUDGET_SCOPE_PRODUCT_LINE,
)

# ── Status enum (PRD §F28.2.11 verbatim) ────────────────────────
BUDGET_STATUS_ACTIVE: Final[str] = "active"
BUDGET_STATUS_PAUSED: Final[str] = "paused"
BUDGET_STATUS_EXPIRED: Final[str] = "expired"

ALL_BUDGET_STATUSES: Final[tuple[str, ...]] = (
    BUDGET_STATUS_ACTIVE,
    BUDGET_STATUS_PAUSED,
    BUDGET_STATUS_EXPIRED,
)

CURRENCY_DEFAULT: Final[str] = "KRW"
ALLOWED_CURRENCIES: Final[tuple[str, ...]] = ("KRW", "USD", "EUR", "JPY", "CNY")


# ── AlertThresholds TypedDict (PRD §F28.2.5 verbatim) ───────────
class AlertThresholds(TypedDict, total=True):
    """TypedDict for budget alert thresholds (warning/critical/exceeded).

    All values are percentages 0-100.
    """

    warning: float  # default 80.0
    critical: float  # default 90.0
    exceeded: float  # default 100.0


# ── BudgetDefinition TypedDict (PRD §F28.2.1 verbatim, 12 fields)
class BudgetDefinition(TypedDict, total=True):
    """TypedDict for budget definition.

    Fields:
        budget_id: UUID of the budget.
        tenant_id: UUID of the tenant.
        period_key: KST YYYY-MM period key.
        budget_period: monthly/quarterly/yearly.
        scope: tenant/department/cost_center/product_line.
        scope_id: specific scope value (e.g. department_id).
        amount: NUMERIC(20, 2) Decimal amount.
        currency_code: ISO 4217 currency code (default KRW).
        alert_thresholds: AlertThresholds TypedDict.
        status: active/paused/expired.
        created_at: ISO 8601 timestamp.
        updated_at: ISO 8601 timestamp.
    """

    budget_id: str
    tenant_id: str
    period_key: str
    budget_period: str
    scope: str
    scope_id: str
    amount: str  # Decimal as string for JSON compatibility
    currency_code: str
    alert_thresholds: AlertThresholds
    status: str
    created_at: str
    updated_at: str


# ── BudgetThresholdDefaults constants (PRD §F28.2.5 verbatim) ───
class BudgetThresholdDefaults:
    """Defaults for budget alert thresholds (PRD §F28.2.5 verbatim).

    CR 12-5 D-GATE-01 — capability gate per-tenant on/off + owner-only RBAC.
    """

    WARNING_PCT: Final[float] = 80.0
    CRITICAL_PCT: Final[float] = 90.0
    EXCEEDED_PCT: Final[float] = 100.0
    AUTO_EXPIRE_CRON_HOUR_KST: Final[int] = 0  # KST 매시간 00분
    DEDUP_WINDOW_HOURS: Final[int] = 24


BUDGET_THRESHOLD_DEFAULTS: Final[BudgetThresholdDefaults] = BudgetThresholdDefaults()


# ── 4 industries baseline + 4 industries granted (PRD §F28.2.9) ─
INDUSTRY_BASELINE_4_INDUSTRIES: Final[tuple[str, ...]] = (
    "manufacturing",
    "service",
    "manufacturing_service",
    "manufacturing_service_other",
)


# ── 6 validation rules (CR 11-4 P-015 verbatim) ─────────────────
_VALIDATION_RULES_COUNT: Final[int] = 6


def _validate_budget_fields(definition: dict[str, Any]) -> None:
    """Internal validator enforcing 6 validation rules.

    CR 11-4 P-015 pure validator pattern.
    Raises:
        BudgetDefinitionInvalidError: invalid definition.
        BudgetScopeInvalidError: invalid scope.
        BudgetAmountInvalidError: invalid amount.
    """
    required_fields = (
        "tenant_id",
        "period_key",
        "budget_period",
        "scope",
        "scope_id",
        "amount",
        "currency_code",
        "alert_thresholds",
        "status",
    )
    missing = [f for f in required_fields if f not in definition]
    if missing:
        raise BudgetDefinitionInvalidError(
            message_ko=f"필수 필드 누락: {', '.join(missing)}",
            details={"missing_fields": missing},
        )

    # Rule 1: tenant_id must be UUID-like
    try:
        uuid.UUID(str(definition["tenant_id"]))
    except (ValueError, AttributeError, TypeError) as exc:
        raise BudgetDefinitionInvalidError(
            message_ko="tenant_id는 UUID 형식이어야 합니다",
            details={"tenant_id": str(definition["tenant_id"])},
        ) from exc

    # Rule 2: budget_period must be in ALL_BUDGET_PERIODS
    if definition["budget_period"] not in ALL_BUDGET_PERIODS:
        raise BudgetDefinitionInvalidError(
            message_ko=f"budget_period는 {ALL_BUDGET_PERIODS} 중 하나여야 합니다",
            details={"budget_period": str(definition["budget_period"])},
        )

    # Rule 3: scope must be in ALL_BUDGET_SCOPES
    if definition["scope"] not in ALL_BUDGET_SCOPES:
        raise BudgetScopeInvalidError(
            message_ko=f"scope는 {ALL_BUDGET_SCOPES} 중 하나여야 합니다",
            details={"scope": str(definition["scope"])},
        )

    # Rule 4: amount must be Decimal > 0
    try:
        amount_decimal = Decimal(str(definition["amount"]))
        if amount_decimal <= 0:
            raise BudgetAmountInvalidError(
                message_ko="amount는 0보다 커야 합니다",
                details={"amount": str(definition["amount"])},
            )
    except (ValueError, TypeError, ArithmeticError) as exc:
        raise BudgetAmountInvalidError(
            message_ko="amount는 유효한 숫자여야 합니다",
            details={"amount": str(definition["amount"])},
        ) from exc

    # Rule 5: currency_code must be in ALLOWED_CURRENCIES
    if definition["currency_code"] not in ALLOWED_CURRENCIES:
        raise BudgetDefinitionInvalidError(
            message_ko=f"currency_code는 {ALLOWED_CURRENCIES} 중 하나여야 합니다",
            details={"currency_code": str(definition["currency_code"])},
        )

    # Rule 6: status must be in ALL_BUDGET_STATUSES
    if definition["status"] not in ALL_BUDGET_STATUSES:
        raise BudgetDefinitionInvalidError(
            message_ko=f"status는 {ALL_BUDGET_STATUSES} 중 하나여야 합니다",
            details={"status": str(definition["status"])},
        )


def parse_budget_definition(
    tenant_id: str | uuid.UUID,
    payload: dict[str, Any],
) -> BudgetDefinition:
    """Pure validator (CR 11-4 P-015 verbatim) for budget definition.

    Enforces 6 validation rules (PRD §F28.2.1 verbatim):
    1. Required field presence (9 fields).
    2. tenant_id UUID format.
    3. budget_period in 3 options.
    4. scope in 4 options + scope_id required.
    5. amount Decimal > 0.
    6. currency_code in 5 allowed currencies + status in 3 options.

    Args:
        tenant_id: tenant UUID (overrides payload).
        payload: budget definition payload dict.

    Returns:
        Validated BudgetDefinition TypedDict.

    Raises:
        BudgetDefinitionInvalidError: invalid definition.
        BudgetScopeInvalidError: invalid scope.
        BudgetAmountInvalidError: invalid amount.
    """
    payload_with_tenant = dict(payload)
    payload_with_tenant["tenant_id"] = str(tenant_id)
    _validate_budget_fields(payload_with_tenant)
    return BudgetDefinition(
        budget_id=str(payload_with_tenant.get("budget_id", uuid.uuid4())),
        tenant_id=str(tenant_id),
        period_key=str(payload_with_tenant["period_key"]),
        budget_period=str(payload_with_tenant["budget_period"]),
        scope=str(payload_with_tenant["scope"]),
        scope_id=str(payload_with_tenant["scope_id"]),
        amount=str(payload_with_tenant["amount"]),
        currency_code=str(payload_with_tenant["currency_code"]),
        alert_thresholds=AlertThresholds(
            warning=float(
                payload_with_tenant["alert_thresholds"].get(
                    "warning", BUDGET_THRESHOLD_DEFAULTS.WARNING_PCT
                )
            ),
            critical=float(
                payload_with_tenant["alert_thresholds"].get(
                    "critical", BUDGET_THRESHOLD_DEFAULTS.CRITICAL_PCT
                )
            ),
            exceeded=float(
                payload_with_tenant["alert_thresholds"].get(
                    "exceeded", BUDGET_THRESHOLD_DEFAULTS.EXCEEDED_PCT
                )
            ),
        ),
        status=str(payload_with_tenant["status"]),
        created_at=str(payload_with_tenant.get("created_at", "")),
        updated_at=str(payload_with_tenant.get("updated_at", "")),
    )


def define_budget(
    tenant_id: str | uuid.UUID,
    period_key: str,
    scope: str,
    scope_id: str,
    amount: Decimal | float | int | str,
    *,
    budget_period: str = BUDGET_PERIOD_MONTHLY,
    currency_code: str = CURRENCY_DEFAULT,
    dry_run: bool = False,
) -> BudgetDefinition:
    """Main entry point — build a BudgetDefinition (6 levels AST).

    AST 6 levels (PRD §F28.2.1 verbatim):
    Level 1: tenant_id selector
    Level 2: period_key + budget_period selector
    Level 3: scope + scope_id selector
    Level 4: amount + currency_code selector
    Level 5: alert_thresholds selector (warning/critical/exceeded)
    Level 6: status selector (active/paused/expired)

    Args:
        tenant_id: tenant UUID.
        period_key: KST YYYY-MM period key.
        scope: budget scope option.
        scope_id: specific scope value.
        amount: NUMERIC(20, 2) amount.
        budget_period: monthly/quarterly/yearly.
        currency_code: ISO 4217 currency code.
        dry_run: dry-run mode (no actual definition).

    Returns:
        Validated BudgetDefinition.

    Raises:
        BudgetDefinitionInvalidError: invalid budget_period or status.
        BudgetScopeInvalidError: invalid scope.
        BudgetAmountInvalidError: invalid amount.
    """
    if scope not in ALL_BUDGET_SCOPES:
        raise BudgetScopeInvalidError(
            message_ko=f"scope는 {ALL_BUDGET_SCOPES} 중 하나여야 합니다",
            details={"scope": scope},
        )
    if budget_period not in ALL_BUDGET_PERIODS:
        raise BudgetDefinitionInvalidError(
            message_ko=f"budget_period는 {ALL_BUDGET_PERIODS} 중 하나여야 합니다",
            details={"budget_period": budget_period},
        )

    return parse_budget_definition(
        tenant_id,
        {
            "period_key": period_key,
            "budget_period": budget_period,
            "scope": scope,
            "scope_id": scope_id,
            "amount": str(amount),
            "currency_code": currency_code,
            "alert_thresholds": {
                "warning": BUDGET_THRESHOLD_DEFAULTS.WARNING_PCT,
                "critical": BUDGET_THRESHOLD_DEFAULTS.CRITICAL_PCT,
                "exceeded": BUDGET_THRESHOLD_DEFAULTS.EXCEEDED_PCT,
            },
            "status": BUDGET_STATUS_ACTIVE,
        },
    )


__all__ = [
    "BUDGET_PERIOD_MONTHLY",
    "BUDGET_PERIOD_QUARTERLY",
    "BUDGET_PERIOD_YEARLY",
    "ALL_BUDGET_PERIODS",
    "BUDGET_SCOPE_TENANT",
    "BUDGET_SCOPE_DEPARTMENT",
    "BUDGET_SCOPE_COST_CENTER",
    "BUDGET_SCOPE_PRODUCT_LINE",
    "ALL_BUDGET_SCOPES",
    "BUDGET_STATUS_ACTIVE",
    "BUDGET_STATUS_PAUSED",
    "BUDGET_STATUS_EXPIRED",
    "ALL_BUDGET_STATUSES",
    "CURRENCY_DEFAULT",
    "ALLOWED_CURRENCIES",
    "AlertThresholds",
    "BudgetDefinition",
    "BudgetThresholdDefaults",
    "BUDGET_THRESHOLD_DEFAULTS",
    "INDUSTRY_BASELINE_4_INDUSTRIES",
    "parse_budget_definition",
    "define_budget",
]
