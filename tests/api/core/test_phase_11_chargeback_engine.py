# tests/api/core/test_phase_11_chargeback_engine.py —
# Phase 11 T2 (cj-style 107번째 wire) — Chargeback engine tests.
# 7 cases per cj-style Phase 10 SLO pattern verbatim mirror.
#
# CR 12-5 D-14 typed exception envelope — tests verify
# ChargebackCalculationError + ChargebackRuleInvalidError raise with
# correct HTTP status codes 500 + 400 and message_ko envelope.
import pytest
from decimal import Decimal

from apps.api.core.errors import (
    ChargebackCalculationError,
    ChargebackRuleInvalidError,
)
from apps.api.modules.finops.chargeback_engine import (
    ALLOWED_COST_ALLOCATION_METHODS,
    ALLOWED_RULE_TYPES,
    COST_ALLOCATION_DIRECT,
    COST_ALLOCATION_INDIRECT,
    MARKUP_PCT_MAX,
    MARKUP_PCT_MIN,
    RULE_TYPE_FLAT_FEE,
    RULE_TYPE_METERED,
    RULE_TYPE_PROPORTIONAL_ALLOCATION,
    TAX_PCT_MIN,
    ChargebackResult,
    compute_chargeback,
)
from apps.api.modules.finops.chargeback_rule_evaluator import (
    evaluate_chargeback_rule,
)


def _valid_rule(**overrides):
    base = {
        "tenant_id": "11111111-1111-1111-1111-111111111111",
        "rule_type": RULE_TYPE_FLAT_FEE,
        "cost_allocation_method": COST_ALLOCATION_DIRECT,
        "flat_fee_amount": "1000.00",
        "markup_pct": "10",
        "tax_pct": "10",
        "currency_code": "KRW",
    }
    base.update(overrides)
    return base


def test_flat_fee_chargeback_computed():
    rule = _valid_rule()
    result = compute_chargeback(
        rule,
        department_total="0",
        period_key="2026-08",
        department_id="dept-1",
        cost_center_id="CC-0001",
    )
    # flat_fee 1000.00 + direct weight 1.0 + 10% markup + 10% tax
    # base = 1000.00, markup = 100.00, subtotal = 1100.00, tax = 110.00
    # total = 1210.00
    assert result["base_amount"] == "1000.00"
    assert result["markup_amount"] == "100.00"
    assert result["tax_amount"] == "110.00"
    assert result["total_amount"] == "1210.00"
    assert result["currency_code"] == "KRW"
    assert result["rule_type"] == RULE_TYPE_FLAT_FEE


def test_proportional_allocation_chargeback_computed():
    rule = _valid_rule(
        rule_type=RULE_TYPE_PROPORTIONAL_ALLOCATION,
        proportional_share_pct="50",
    )
    del rule["flat_fee_amount"]
    result = compute_chargeback(
        rule,
        department_total="2000.00",
        period_key="2026-08",
        department_id="dept-1",
        cost_center_id="CC-0001",
    )
    # 2000 * 0.5 = 1000.00 base + 10% markup + 10% tax = 1210.00
    assert result["base_amount"] == "1000.00"
    assert result["total_amount"] == "1210.00"


def test_metered_chargeback_computed():
    rule = _valid_rule(
        rule_type=RULE_TYPE_METERED,
        metered_unit_price="10.00",
        metered_quantity="100",
    )
    del rule["flat_fee_amount"]
    result = compute_chargeback(
        rule,
        department_total="0",
        period_key="2026-08",
        department_id="dept-1",
        cost_center_id="CC-0001",
    )
    # 10 * 100 = 1000.00 base + 10% markup + 10% tax = 1210.00
    assert result["base_amount"] == "1000.00"
    assert result["total_amount"] == "1210.00"


def test_cost_allocation_indirect_weight_applied():
    rule = _valid_rule(
        cost_allocation_method=COST_ALLOCATION_INDIRECT,
    )
    result = compute_chargeback(
        rule,
        department_total="0",
        period_key="2026-08",
        department_id="dept-1",
        cost_center_id="CC-0001",
    )
    # 1000.00 * 0.5 = 500.00 base + 10% markup + 10% tax = 605.00
    assert result["base_amount"] == "500.00"
    assert result["total_amount"] == "605.00"


def test_invalid_rule_type_raises():
    rule = _valid_rule(rule_type="invalid_rule_type")
    with pytest.raises(ChargebackCalculationError) as excinfo:
        compute_chargeback(
            rule,
            department_total="0",
            period_key="2026-08",
            department_id="dept-1",
            cost_center_id="CC-0001",
        )
    assert excinfo.value.http_status == 500
    assert excinfo.value.code == "CHARGEBACK_INVALID_RULE_TYPE"


def test_invalid_cost_allocation_raises():
    rule = _valid_rule(cost_allocation_method="invalid_method")
    with pytest.raises(ChargebackCalculationError):
        compute_chargeback(
            rule,
            department_total="0",
            period_key="2026-08",
            department_id="dept-1",
            cost_center_id="CC-0001",
        )


def test_markup_pct_out_of_range_raises():
    rule = _valid_rule(markup_pct=str(MARKUP_PCT_MAX + 1))
    with pytest.raises(ChargebackCalculationError) as excinfo:
        compute_chargeback(
            rule,
            department_total="0",
            period_key="2026-08",
            department_id="dept-1",
            cost_center_id="CC-0001",
        )
    assert excinfo.value.http_status == 500
    assert excinfo.value.code == "CHARGEBACK_MARKUP_OUT_OF_RANGE"


def test_evaluate_chargeback_rule_3_rule_types_accepted():
    for rule_type in ALLOWED_RULE_TYPES:
        rule = _valid_rule(rule_type=rule_type)
        if rule_type == RULE_TYPE_PROPORTIONAL_ALLOCATION:
            rule["proportional_share_pct"] = "50"
            del rule["flat_fee_amount"]
        elif rule_type == RULE_TYPE_METERED:
            rule["metered_unit_price"] = "10.00"
            rule["metered_quantity"] = "100"
            del rule["flat_fee_amount"]
        validated = evaluate_chargeback_rule(rule)
        assert validated["rule_type"] == rule_type


def test_evaluate_chargeback_rule_invalid_rule_type_raises():
    with pytest.raises(ChargebackRuleInvalidError) as excinfo:
        evaluate_chargeback_rule(_valid_rule(rule_type="bad_type"))
    assert excinfo.value.http_status == 400


def test_evaluate_chargeback_rule_invalid_markup_pct_raises():
    with pytest.raises(ChargebackRuleInvalidError) as excinfo:
        evaluate_chargeback_rule(_valid_rule(markup_pct="51"))
    assert excinfo.value.http_status == 400
    assert excinfo.value.code == "CHARGEBACK_RULE_MARKUP_OUT_OF_RANGE"


def test_evaluate_chargeback_rule_tax_pct_below_zero_raises():
    with pytest.raises(ChargebackRuleInvalidError) as excinfo:
        evaluate_chargeback_rule(_valid_rule(tax_pct=str(int(TAX_PCT_MIN) - 1)))
    assert excinfo.value.http_status == 400
    assert excinfo.value.code == "CHARGEBACK_RULE_TAX_OUT_OF_RANGE"


def test_banker_rounding_applied():
    rule = _valid_rule(
        rule_type=RULE_TYPE_METERED,
        metered_unit_price="0.005",
        metered_quantity="3",
    )
    del rule["flat_fee_amount"]
    result = compute_chargeback(
        rule,
        department_total="0",
        period_key="2026-08",
        department_id="dept-1",
        cost_center_id="CC-0001",
    )
    # 0.005 * 3 = 0.015; banker's rounding to 0.02
    assert result["base_amount"] == "0.02"


def test_chargeback_result_typed_dict_10_fields():
    rule = _valid_rule()
    result = compute_chargeback(
        rule,
        department_total="0",
        period_key="2026-08",
        department_id="dept-1",
        cost_center_id="CC-0001",
    )
    required_fields = {
        "chargeback_id",
        "tenant_id",
        "period_key",
        "department_id",
        "cost_center_id",
        "rule_type",
        "base_amount",
        "markup_amount",
        "tax_amount",
        "total_amount",
        "currency_code",
        "computed_at",
        "trace_id",
    }
    for field in required_fields:
        assert field in result, f"missing field {field}"


def test_chargeback_default_currency_krw():
    rule = _valid_rule()
    del rule["currency_code"]
    result = compute_chargeback(
        rule,
        department_total="0",
        period_key="2026-08",
        department_id="dept-1",
        cost_center_id="CC-0001",
    )
    assert result["currency_code"] == "KRW"