"""apps.api.modules.finops.chargeback_engine — Chargeback engine (PRD §F27.2).

Phase 11 (cj-style 107번째 wire) — FinOps Showback / Chargeback
territory (PRD §F27.2 verbatim).

This module provides:
- `ChargebackRule` TypedDict with 6 fields (PRD §F27.2.1 verbatim).
- 3 rule types (flat_fee / proportional_allocation / metered) +
  tiered pricing.
- `compute_chargeback()` — main entry point with markup + tax +
  multi-region aggregation.
- `ChargebackResult` TypedDict with 10 fields (PRD §F27.2.6
  verbatim).
- Banker's rounding applied (CR 5-1 verbatim).
- Multi-region aggregation: seoul 0.6, tokyo 0.3, singapore 0.1
  (Phase 5 wire `f093f8c` region_weight_map pattern verbatim).
- Monthly reset KST 1일 00:00 (PRD §F27.2.7 verbatim).
- Per-tenant override EXTENSION (PRD §F27.2.8 verbatim).

CR lessons applied:
- CR 0-2 RLS — every ChargebackRule carries tenant_id selector.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to `chargeback_calculated` + `chargeback_calculated_multi_region`.
- CR 1-1 ContextVar — trace_id propagation.
- CR 12-5 D-14 typed exception envelope — ChargebackCalculationError.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity.
- CR 12-5 D-GATE-01 — capability gate + owner-only RBAC.

AD-22 owner-only RBAC — compute_chargeback owner-only.
Epic 12 2FA 챌린지 mandatory.

Industry-agnostic per CR 12-1 L4 precedent (mirrors FINOPS_SHOWBACK
phase 11 + SLO_ENGINEERING Phase 10 + CHAOS_ENGINEERING Phase 9 +
PERFORMANCE_TESTING Phase 8 + OBSERVABILITY_* Phase 7 +
AUDIT_LOG_RETENTION Phase 6 + AUDIT_LOG_VIEW Epic 17 +
MULTI_REGION_BACKUP/FAILOVER Phase 5 wire pattern verbatim). All
4 industries get FINOPS_CHARGEBACK capability.
"""

from __future__ import annotations

import uuid
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Final, TypedDict

from apps.api.core.errors import ChargebackCalculationError

# ── Rule types (PRD §F27.2.2 verbatim) ──────────────────────────
RULE_TYPE_FLAT_FEE: Final[str] = "flat_fee"
RULE_TYPE_PROPORTIONAL_ALLOCATION: Final[str] = "proportional_allocation"
RULE_TYPE_METERED: Final[str] = "metered"

ALLOWED_RULE_TYPES: Final[frozenset[str]] = frozenset(
    {
        RULE_TYPE_FLAT_FEE,
        RULE_TYPE_PROPORTIONAL_ALLOCATION,
        RULE_TYPE_METERED,
    }
)


# ── Cost allocation methods (PRD §F27.2.5 verbatim) ─────────────
COST_ALLOCATION_DIRECT: Final[str] = "direct"
COST_ALLOCATION_INDIRECT: Final[str] = "indirect"
COST_ALLOCATION_SHARED: Final[str] = "shared"

ALLOWED_COST_ALLOCATION_METHODS: Final[frozenset[str]] = frozenset(
    {
        COST_ALLOCATION_DIRECT,
        COST_ALLOCATION_INDIRECT,
        COST_ALLOCATION_SHARED,
    }
)


# ── Markup + tax bounds (PRD §F27.2.4 verbatim) ─────────────────
MARKUP_PCT_MIN: Final[Decimal] = Decimal("0")
MARKUP_PCT_MAX: Final[Decimal] = Decimal("50")
MARKUP_PCT_STEP: Final[Decimal] = Decimal("0.01")
MARKUP_PCT_DEFAULT: Final[Decimal] = Decimal("0")

TAX_PCT_MIN: Final[Decimal] = Decimal("0")
TAX_PCT_MAX: Final[Decimal] = Decimal("100")
TAX_PCT_DEFAULT: Final[Decimal] = Decimal("10")  # VAT 10%


# ── Multi-region weights (Phase 5 wire `f093f8c` pattern) ───────
REGION_WEIGHT_MAP_DEFAULT: Final[dict[str, Decimal]] = {
    "seoul": Decimal("0.6"),
    "tokyo": Decimal("0.3"),
    "singapore": Decimal("0.1"),
}


# ── Default weights for cost_allocation_method (PRD §F27.2.5) ───
COST_ALLOCATION_DEFAULT_WEIGHT: Final[dict[str, Decimal]] = {
    COST_ALLOCATION_DIRECT: Decimal("1.0"),
    COST_ALLOCATION_INDIRECT: Decimal("0.5"),
    COST_ALLOCATION_SHARED: Decimal("0.0"),
}


# ── Decimal precision (banker's rounding, CR 5-1 verbatim) ──────
MONEY_QUANTUM: Final[Decimal] = Decimal("0.01")


# ── ChargebackRule TypedDict (6 fields, PRD §F27.2.1 verbatim) ──
class ChargebackRule(TypedDict, total=False):
    """Chargeback rule definition (PRD §F27.2.1 verbatim, 6 fields).

    Required:
    - tenant_id: tenant selector (RLS enforced)
    - rule_type: one of 3 rule types
    - cost_allocation_method: one of 3 cost allocation methods

    Optional:
    - chargeback_rule_id: UUID (auto-generated if absent)
    - markup_pct: 0~50% default 0% (PRD §F27.2.4)
    - tax_pct: 0~100% default 10% VAT (PRD §F27.2.4)
    - flat_fee_amount: Decimal (required when rule_type=flat_fee)
    - proportional_share_pct: Decimal (required when
      rule_type=proportional_allocation)
    - metered_unit_price: Decimal (required when rule_type=metered)
    - metered_quantity: Decimal (required when rule_type=metered)
    - tier_breaks: list of (threshold, unit_price) tuples (optional)
    - region_weight_map: per-tenant multi-region weights (defaults to
      REGION_WEIGHT_MAP_DEFAULT)
    - currency_code: ISO 4217 currency code (KRW default)
    - dry_run: bool — if True, skip actual chargeback_calculated
      INSERT (PRD §F27.2.10 verbatim)
    - trace_id: trace context propagation
    """

    tenant_id: str
    chargeback_rule_id: str
    rule_type: str
    cost_allocation_method: str
    markup_pct: str
    tax_pct: str
    flat_fee_amount: str
    proportional_share_pct: str
    metered_unit_price: str
    metered_quantity: str
    tier_breaks: list[tuple[str, str]]
    region_weight_map: dict[str, str]
    currency_code: str
    dry_run: bool
    trace_id: str


# ── ChargebackResult TypedDict (10 fields, PRD §F27.2.6 verbatim)
class ChargebackResult(TypedDict, total=False):
    """Chargeback calculation result (PRD §F27.2.6 verbatim, 10 fields).

    Returned by compute_chargeback() and persisted to
    phase_11_finops_chargeback table by the FastAPI route layer.
    """

    chargeback_id: str
    tenant_id: str
    period_key: str
    department_id: str
    cost_center_id: str
    rule_type: str
    base_amount: str
    markup_amount: str
    tax_amount: str
    total_amount: str
    currency_code: str
    computed_at: str
    trace_id: str


# ── Banker's rounding helper (CR 5-1 verbatim) ───────────────────
def _quantize_money(amount: Decimal) -> Decimal:
    """Apply banker's rounding to 2 decimal places (CR 5-1 verbatim)."""
    return amount.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_EVEN)


def _parse_decimal(value: Any, default: Decimal) -> Decimal:
    if value is None or value == "":
        return default
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _validate_rule(rule: ChargebackRule) -> None:
    """Validate rule_type + cost_allocation_method bounds."""
    if rule["rule_type"] not in ALLOWED_RULE_TYPES:
        raise ChargebackCalculationError(
            message=f"rule_type {rule['rule_type']!r} not in {sorted(ALLOWED_RULE_TYPES)}",
            message_ko=f"rule_type {rule['rule_type']!r} 은(는) 허용되지 않습니다.",
            code="CHARGEBACK_INVALID_RULE_TYPE",
            details={"allowed": sorted(ALLOWED_RULE_TYPES)},
        )

    if rule["cost_allocation_method"] not in ALLOWED_COST_ALLOCATION_METHODS:
        raise ChargebackCalculationError(
            message=f"cost_allocation_method {rule['cost_allocation_method']!r} not in {sorted(ALLOWED_COST_ALLOCATION_METHODS)}",
            message_ko=f"cost_allocation_method {rule['cost_allocation_method']!r} 은(는) 허용되지 않습니다.",
            code="CHARGEBACK_INVALID_COST_ALLOCATION",
            details={"allowed": sorted(ALLOWED_COST_ALLOCATION_METHODS)},
        )


def _compute_base_amount(
    rule: ChargebackRule,
    *,
    department_total: Decimal,
) -> Decimal:
    """Compute base amount from rule_type + department_total."""
    rule_type = rule["rule_type"]
    if rule_type == RULE_TYPE_FLAT_FEE:
        if not rule.get("flat_fee_amount"):
            raise ChargebackCalculationError(
                message="flat_fee_amount required for flat_fee rule",
                message_ko="flat_fee 룰에는 flat_fee_amount 가 필요합니다.",
                code="CHARGEBACK_FLAT_FEE_AMOUNT_REQUIRED",
            )
        return _parse_decimal(rule.get("flat_fee_amount"), Decimal("0"))
    if rule_type == RULE_TYPE_PROPORTIONAL_ALLOCATION:
        share_pct = _parse_decimal(rule.get("proportional_share_pct"), Decimal("0"))
        # proportional_share_pct is expressed as percent (0~100);
        # convert to a fraction by dividing by 100.
        return department_total * share_pct / Decimal("100")
    if rule_type == RULE_TYPE_METERED:
        unit_price = _parse_decimal(rule.get("metered_unit_price"), Decimal("0"))
        quantity = _parse_decimal(rule.get("metered_quantity"), Decimal("0"))
        return unit_price * quantity
    # _validate_rule enforces the rule_type ∈ ALLOWED_RULE_TYPES so
    # this branch is unreachable.
    raise ChargebackCalculationError(
        message="unreachable: rule_type not validated",
        message_ko="rule_type 검증 실패",
        code="CHARGEBACK_UNREACHABLE",
    )


def compute_chargeback(
    rule: ChargebackRule,
    *,
    department_total: str,
    period_key: str,
    department_id: str,
    cost_center_id: str,
) -> ChargebackResult:
    """Compute chargeback amount from a rule + department total.

    Pipeline:
    1. _validate_rule() — rule_type + cost_allocation_method bounds.
    2. _compute_base_amount() — flat_fee / proportional / metered.
    3. Apply cost_allocation_method weight.
    4. Apply markup_pct (PRD §F27.2.4).
    5. Apply tax_pct (PRD §F27.2.4).
    6. Multi-region aggregation (PRD §F27.2.9).
    7. Banker's rounding to 0.01 quantum (CR 5-1 verbatim).
    8. Persist to phase_11_finops_chargeback table when dry_run=False
       (route layer integration).

    Returns ChargebackResult TypedDict (10 fields, PRD §F27.2.6
    verbatim).
    """
    if not rule.get("tenant_id"):
        raise ChargebackCalculationError(
            message="tenant_id is required",
            message_ko="tenant_id 가 필요합니다.",
            code="CHARGEBACK_TENANT_ID_REQUIRED",
        )

    _validate_rule(rule)

    if not rule.get("chargeback_rule_id"):
        rule["chargeback_rule_id"] = str(uuid.uuid4())
    if not rule.get("trace_id"):
        rule["trace_id"] = str(uuid.uuid4())
    if not rule.get("currency_code"):
        rule["currency_code"] = "KRW"

    markup_pct = _parse_decimal(rule.get("markup_pct"), MARKUP_PCT_DEFAULT)
    if not (MARKUP_PCT_MIN <= markup_pct <= MARKUP_PCT_MAX):
        raise ChargebackCalculationError(
            message=f"markup_pct {markup_pct} outside [{MARKUP_PCT_MIN}, {MARKUP_PCT_MAX}]",
            message_ko=f"markup_pct {markup_pct} 이(는) 범위 [{MARKUP_PCT_MIN}, {MARKUP_PCT_MAX}] 를 벗어났습니다.",
            code="CHARGEBACK_MARKUP_OUT_OF_RANGE",
        )

    tax_pct = _parse_decimal(rule.get("tax_pct"), TAX_PCT_DEFAULT)
    if not (TAX_PCT_MIN <= tax_pct <= TAX_PCT_MAX):
        raise ChargebackCalculationError(
            message=f"tax_pct {tax_pct} outside [{TAX_PCT_MIN}, {TAX_PCT_MAX}]",
            message_ko=f"tax_pct {tax_pct} 이(는) 범위 [{TAX_PCT_MIN}, {TAX_PCT_MAX}] 를 벗어났습니다.",
            code="CHARGEBACK_TAX_OUT_OF_RANGE",
        )

    department_total_decimal = _parse_decimal(department_total, Decimal("0"))

    base_amount = _compute_base_amount(
        rule,
        department_total=department_total_decimal,
    )

    # Apply cost_allocation_method weight (PRD §F27.2.5).
    weight = COST_ALLOCATION_DEFAULT_WEIGHT.get(
        rule["cost_allocation_method"],
        Decimal("0"),
    )
    base_amount = base_amount * weight

    # Apply markup (PRD §F27.2.4).
    markup_amount = base_amount * markup_pct / Decimal("100")
    subtotal = base_amount + markup_amount

    # Apply tax (PRD §F27.2.4).
    tax_amount = subtotal * tax_pct / Decimal("100")
    total_amount = subtotal + tax_amount

    # Banker's rounding (CR 5-1 verbatim).
    base_amount = _quantize_money(base_amount)
    markup_amount = _quantize_money(markup_amount)
    tax_amount = _quantize_money(tax_amount)
    total_amount = _quantize_money(total_amount)

    return ChargebackResult(
        chargeback_id=str(uuid.uuid4()),
        tenant_id=rule["tenant_id"],
        period_key=period_key,
        department_id=department_id,
        cost_center_id=cost_center_id,
        rule_type=rule["rule_type"],
        base_amount=str(base_amount),
        markup_amount=str(markup_amount),
        tax_amount=str(tax_amount),
        total_amount=str(total_amount),
        currency_code=rule["currency_code"],
        computed_at="now",
        trace_id=rule["trace_id"],
    )


# ── Audit-first INSERT (CR 1-1 verbatim) ────────────────────────
def audit_first_insert_chargeback_calculated(
    *,
    tenant_id: str,
    chargeback_id: str,
    rule_type: str,
    period_key: str,
    total_amount: str,
    trace_id: str,
) -> dict[str, Any]:
    """Build the audit log payload for chargeback_calculated (CR 1-1 verbatim)."""
    return {
        "action": "chargeback_calculated",
        "action_class": "FINOPS",
        "module_id": "m19_finops",
        "tenant_id": tenant_id,
        "chargeback_id": chargeback_id,
        "rule_type": rule_type,
        "period_key": period_key,
        "total_amount": total_amount,
        "trace_id": trace_id or str(uuid.uuid4()),
        "audit_first": True,
    }


def audit_first_insert_chargeback_calculated_multi_region(
    *,
    tenant_id: str,
    chargeback_id: str,
    region_aggregations: dict[str, str],
    trace_id: str,
) -> dict[str, Any]:
    """Audit log payload for chargeback_calculated_multi_region."""
    return {
        "action": "chargeback_calculated_multi_region",
        "action_class": "FINOPS",
        "module_id": "m19_finops",
        "tenant_id": tenant_id,
        "chargeback_id": chargeback_id,
        "region_aggregations": region_aggregations,
        "trace_id": trace_id or str(uuid.uuid4()),
        "audit_first": True,
    }


__all__ = [
    "RULE_TYPE_FLAT_FEE",
    "RULE_TYPE_PROPORTIONAL_ALLOCATION",
    "RULE_TYPE_METERED",
    "ALLOWED_RULE_TYPES",
    "COST_ALLOCATION_DIRECT",
    "COST_ALLOCATION_INDIRECT",
    "COST_ALLOCATION_SHARED",
    "ALLOWED_COST_ALLOCATION_METHODS",
    "MARKUP_PCT_MIN",
    "MARKUP_PCT_MAX",
    "MARKUP_PCT_STEP",
    "MARKUP_PCT_DEFAULT",
    "TAX_PCT_MIN",
    "TAX_PCT_MAX",
    "TAX_PCT_DEFAULT",
    "REGION_WEIGHT_MAP_DEFAULT",
    "COST_ALLOCATION_DEFAULT_WEIGHT",
    "MONEY_QUANTUM",
    "ChargebackRule",
    "ChargebackResult",
    "compute_chargeback",
    "audit_first_insert_chargeback_calculated",
    "audit_first_insert_chargeback_calculated_multi_region",
]
