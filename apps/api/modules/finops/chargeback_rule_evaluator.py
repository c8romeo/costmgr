"""apps.api.modules.finops.chargeback_rule_evaluator — Rule evaluation (PRD §F27.2.3).

Phase 11 (cj-style 107번째 wire) — FinOps Showback / Chargeback
territory (PRD §F27.2.3 verbatim).

This module provides:
- `evaluate_chargeback_rule()` — validates ChargebackRule +
  returns enriched rule ready for compute_chargeback().
- 4 validation rules (PRD §F27.2.3 verbatim):
  1. rule_type ∈ ALLOWED_RULE_TYPES
  2. cost_allocation_method ∈ ALLOWED_COST_ALLOCATION_METHODS
  3. markup_pct ∈ [0, 50]
  4. tax_pct ∈ [0, 100]
- ChargebackRuleInvalidError(400) + ChargebackCalculationError(500)
  typed exception envelope.

CR lessons applied:
- CR 11-4 P-015 — pure validator pattern.
- CR 12-5 D-14 typed exception envelope.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity.
- CR 12-5 D-GATE-01 — capability gate + owner-only RBAC.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Final

from apps.api.core.errors import (
    ChargebackCalculationError,
    ChargebackRuleInvalidError,
)

from apps.api.modules.finops.chargeback_engine import (
    ALLOWED_COST_ALLOCATION_METHODS,
    ALLOWED_RULE_TYPES,
    MARKUP_PCT_MAX,
    MARKUP_PCT_MIN,
    TAX_PCT_MAX,
    TAX_PCT_MIN,
    ChargebackRule,
)


# ── Tiered pricing constants (PRD §F27.2.2 verbatim) ────────────
MAX_TIER_BREAKS: Final[int] = 5


def _validate_rule_type(rule_type: str) -> None:
    if rule_type not in ALLOWED_RULE_TYPES:
        raise ChargebackRuleInvalidError(
            message=f"rule_type {rule_type!r} not in {sorted(ALLOWED_RULE_TYPES)}",
            message_ko=f"rule_type {rule_type!r} 은(는) 허용되지 않습니다.",
            code="CHARGEBACK_RULE_INVALID_TYPE",
            details={"allowed": sorted(ALLOWED_RULE_TYPES)},
        )


def _validate_cost_allocation_method(method: str) -> None:
    if method not in ALLOWED_COST_ALLOCATION_METHODS:
        raise ChargebackRuleInvalidError(
            message=f"cost_allocation_method {method!r} not in {sorted(ALLOWED_COST_ALLOCATION_METHODS)}",
            message_ko=f"cost_allocation_method {method!r} 은(는) 허용되지 않습니다.",
            code="CHARGEBACK_RULE_INVALID_COST_ALLOCATION",
            details={"allowed": sorted(ALLOWED_COST_ALLOCATION_METHODS)},
        )


def _validate_markup_pct(markup_pct: Decimal) -> None:
    if not (MARKUP_PCT_MIN <= markup_pct <= MARKUP_PCT_MAX):
        raise ChargebackRuleInvalidError(
            message=f"markup_pct {markup_pct} outside [{MARKUP_PCT_MIN}, {MARKUP_PCT_MAX}]",
            message_ko=f"markup_pct {markup_pct} 이(는) 범위 [{MARKUP_PCT_MIN}, {MARKUP_PCT_MAX}] 를 벗어났습니다.",
            code="CHARGEBACK_RULE_MARKUP_OUT_OF_RANGE",
            details={"min": str(MARKUP_PCT_MIN), "max": str(MARKUP_PCT_MAX)},
        )


def _validate_tax_pct(tax_pct: Decimal) -> None:
    if not (TAX_PCT_MIN <= tax_pct <= TAX_PCT_MAX):
        raise ChargebackRuleInvalidError(
            message=f"tax_pct {tax_pct} outside [{TAX_PCT_MIN}, {TAX_PCT_MAX}]",
            message_ko=f"tax_pct {tax_pct} 이(는) 범위 [{TAX_PCT_MIN}, {TAX_PCT_MAX}] 를 벗어났습니다.",
            code="CHARGEBACK_RULE_TAX_OUT_OF_RANGE",
            details={"min": str(TAX_PCT_MIN), "max": str(TAX_PCT_MAX)},
        )


def evaluate_chargeback_rule(
    rule: ChargebackRule,
) -> ChargebackRule:
    """Validate a ChargebackRule (CR 11-4 P-015 pure validator).

    Enforces 4 validation rules:
    1. rule_type ∈ ALLOWED_RULE_TYPES
    2. cost_allocation_method ∈ ALLOWED_COST_ALLOCATION_METHODS
    3. markup_pct ∈ [0, 50]
    4. tax_pct ∈ [0, 100]

    Raises:
        ChargebackRuleInvalidError: HTTP 400 envelope.
        ChargebackCalculationError: HTTP 500 envelope (when rule
            references invalid Decimal values).
    """
    if not rule.get("tenant_id"):
        raise ChargebackRuleInvalidError(
            message="tenant_id is required",
            message_ko="tenant_id 가 필요합니다.",
            code="CHARGEBACK_RULE_TENANT_ID_REQUIRED",
        )

    if not rule.get("rule_type"):
        raise ChargebackRuleInvalidError(
            message="rule_type is required",
            message_ko="rule_type 이 필요합니다.",
            code="CHARGEBACK_RULE_TYPE_REQUIRED",
        )

    _validate_rule_type(rule["rule_type"])

    if not rule.get("cost_allocation_method"):
        raise ChargebackRuleInvalidError(
            message="cost_allocation_method is required",
            message_ko="cost_allocation_method 가 필요합니다.",
            code="CHARGEBACK_RULE_COST_ALLOCATION_REQUIRED",
        )

    _validate_cost_allocation_method(rule["cost_allocation_method"])

    markup_pct_raw = rule.get("markup_pct", "0")
    try:
        markup_pct = Decimal(str(markup_pct_raw))
    except (TypeError, ValueError) as exc:
        raise ChargebackCalculationError(
            message=f"invalid markup_pct {markup_pct_raw!r}",
            message_ko=f"markup_pct {markup_pct_raw!r} 이(는) 유효하지 않습니다.",
            code="CHARGEBACK_RULE_MARKUP_PARSE",
        ) from exc
    _validate_markup_pct(markup_pct)

    tax_pct_raw = rule.get("tax_pct", "10")
    try:
        tax_pct = Decimal(str(tax_pct_raw))
    except (TypeError, ValueError) as exc:
        raise ChargebackCalculationError(
            message=f"invalid tax_pct {tax_pct_raw!r}",
            message_ko=f"tax_pct {tax_pct_raw!r} 이(는) 유효하지 않습니다.",
            code="CHARGEBACK_RULE_TAX_PARSE",
        ) from exc
    _validate_tax_pct(tax_pct)

    tier_breaks = rule.get("tier_breaks", [])
    if len(tier_breaks) > MAX_TIER_BREAKS:
        raise ChargebackRuleInvalidError(
            message=f"tier_breaks {len(tier_breaks)} exceeds max {MAX_TIER_BREAKS}",
            message_ko=f"tier_breaks {len(tier_breaks)} 은(는) 최대 {MAX_TIER_BREAKS} 을(를) 초과합니다.",
            code="CHARGEBACK_RULE_TIER_BREAKS_EXCEEDED",
            details={"max": MAX_TIER_BREAKS},
        )

    return rule


__all__ = [
    "MAX_TIER_BREAKS",
    "evaluate_chargeback_rule",
]