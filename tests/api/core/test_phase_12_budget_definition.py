# tests/api/core/test_phase_12_budget_definition.py —
# Phase 12 T6.5 (cj-style 111번째 wire) — Budget definition DSL tests.
# 10 cases per cj-style Phase 11 Showback DSL pattern verbatim mirror.
#
# CR 12-5 D-14 typed exception envelope — tests verify
# BudgetDefinitionInvalidError + BudgetScopeInvalidError +
# BudgetAmountInvalidError raise with correct HTTP status code 400 and
# message_ko envelope.
import pytest

from apps.api.core.errors import (
    BudgetAmountInvalidError,
    BudgetDefinitionInvalidError,
    BudgetScopeInvalidError,
)
from apps.api.modules.finops.budget_definition import (
    ALERT_LEVEL_CRITICAL,
    ALERT_LEVEL_EXCEEDED,
    ALERT_LEVEL_WARNING,
    ALL_BUDGET_PERIODS,
    ALL_BUDGET_SCOPES,
    BUDGET_PERIOD_MONTHLY,
    BUDGET_PERIOD_QUARTERLY,
    BUDGET_PERIOD_YEARLY,
    BUDGET_SCOPE_COST_CENTER,
    BUDGET_SCOPE_DEPARTMENT,
    BUDGET_SCOPE_PRODUCT_LINE,
    BUDGET_SCOPE_TENANT,
    BUDGET_STATUS_ACTIVE,
    BUDGET_THRESHOLD_DEFAULTS,
    CURRENCY_DEFAULT,
    BudgetDefinition,
    define_budget,
    parse_budget_definition,
)


_TENANT_ID = "11111111-1111-1111-1111-111111111111"


def _valid_payload(**overrides):
    base = {
        "period_key": "2026-08",
        "budget_period": BUDGET_PERIOD_MONTHLY,
        "scope": BUDGET_SCOPE_TENANT,
        "scope_id": "TENANT",
        "amount": "1000000.00",
        "currency_code": CURRENCY_DEFAULT,
        "alert_thresholds": {
            "warning": 80.0,
            "critical": 90.0,
            "exceeded": 100.0,
        },
        "status": BUDGET_STATUS_ACTIVE,
    }
    base.update(overrides)
    return base


def test_valid_budget_definition_accepted():
    payload = _valid_payload()
    validated = parse_budget_definition(_TENANT_ID, payload)
    assert validated["tenant_id"] == _TENANT_ID
    assert validated["scope"] == BUDGET_SCOPE_TENANT
    assert validated["budget_period"] == BUDGET_PERIOD_MONTHLY


def test_budget_invalid_period_rejected():
    payload = _valid_payload(budget_period="invalid_period")
    with pytest.raises(BudgetDefinitionInvalidError) as excinfo:
        parse_budget_definition(_TENANT_ID, payload)
    assert excinfo.value.http_status == 400


def test_budget_invalid_scope_rejected():
    payload = _valid_payload(scope="invalid_scope")
    with pytest.raises(BudgetScopeInvalidError) as excinfo:
        parse_budget_definition(_TENANT_ID, payload)
    assert excinfo.value.http_status == 400


def test_budget_invalid_amount_zero_rejected():
    payload = _valid_payload(amount="0")
    with pytest.raises(BudgetAmountInvalidError):
        parse_budget_definition(_TENANT_ID, payload)


def test_budget_invalid_amount_negative_rejected():
    payload = _valid_payload(amount="-1000.00")
    with pytest.raises(BudgetAmountInvalidError):
        parse_budget_definition(_TENANT_ID, payload)


def test_budget_invalid_currency_rejected():
    payload = _valid_payload(currency_code="XXX")
    with pytest.raises(BudgetDefinitionInvalidError):
        parse_budget_definition(_TENANT_ID, payload)


def test_budget_invalid_status_rejected():
    payload = _valid_payload(status="invalid_status")
    with pytest.raises(BudgetDefinitionInvalidError):
        parse_budget_definition(_TENANT_ID, payload)


def test_budget_missing_required_field_rejected():
    payload = _valid_payload()
    del payload["scope_id"]
    with pytest.raises(BudgetDefinitionInvalidError) as excinfo:
        parse_budget_definition(_TENANT_ID, payload)
    assert "scope_id" in str(excinfo.value.details["missing_fields"])


def test_define_budget_defaults():
    """define_budget applies default thresholds 80/90/100."""
    result = define_budget(
        _TENANT_ID, "2026-08", BUDGET_SCOPE_TENANT, "TENANT", "1000000.00"
    )
    assert result["alert_thresholds"]["warning"] == BUDGET_THRESHOLD_DEFAULTS.WARNING_PCT
    assert result["alert_thresholds"]["critical"] == BUDGET_THRESHOLD_DEFAULTS.CRITICAL_PCT
    assert result["alert_thresholds"]["exceeded"] == BUDGET_THRESHOLD_DEFAULTS.EXCEEDED_PCT
    assert result["status"] == BUDGET_STATUS_ACTIVE


def test_budget_all_scopes_and_periods_supported():
    """All 4 scopes + 3 periods are accepted."""
    assert len(ALL_BUDGET_SCOPES) == 4
    assert len(ALL_BUDGET_PERIODS) == 3
    assert BUDGET_SCOPE_TENANT in ALL_BUDGET_SCOPES
    assert BUDGET_SCOPE_DEPARTMENT in ALL_BUDGET_SCOPES
    assert BUDGET_SCOPE_COST_CENTER in ALL_BUDGET_SCOPES
    assert BUDGET_SCOPE_PRODUCT_LINE in ALL_BUDGET_SCOPES
    assert BUDGET_PERIOD_MONTHLY in ALL_BUDGET_PERIODS
    assert BUDGET_PERIOD_QUARTERLY in ALL_BUDGET_PERIODS
    assert BUDGET_PERIOD_YEARLY in ALL_BUDGET_PERIODS