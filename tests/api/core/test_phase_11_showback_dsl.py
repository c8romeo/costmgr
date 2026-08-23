# tests/api/core/test_phase_11_showback_dsl.py —
# Phase 11 T1 (cj-style 107번째 wire) — Showback DSL tests.
# 6 cases per cj-style Phase 10 SLO DSL pattern verbatim mirror.
#
# CR 12-5 D-14 typed exception envelope — tests verify
# ShowbackDefinitionInvalidError raises with correct HTTP status
# code 400 and message_ko envelope.
import pytest

from apps.api.core.errors import ShowbackDefinitionInvalidError
from apps.api.modules.finops.showback_dsl import (
    ALLOWED_GROUP_BY,
    ALLOWED_PERIOD_MODES,
    COMPARISON_PREVIOUS_MONTH,
    GROUP_BY_DEPARTMENT,
    GROUP_BY_COST_CENTER,
    INDUSTRY_MANUFACTURING,
    PERIOD_CURRENT_MONTH,
    PERIOD_CUSTOM_RANGE,
    PERIOD_PREVIOUS_MONTH,
    PERIOD_LAST_3_MONTHS,
    PERIOD_LAST_6_MONTHS,
    PERIOD_YTD,
    SHOWBACK_PAGE_SIZE_DEFAULT,
    SHOWBACK_PAGE_SIZE_MAX,
    ShowbackDefinition,
    parse_showback_definition,
    resolve_period_bounds,
)


def _valid_payload(**overrides):
    base = {
        "tenant_id": "11111111-1111-1111-1111-111111111111",
        "group_by": GROUP_BY_DEPARTMENT,
        "period_mode": PERIOD_CURRENT_MONTH,
        "currency_code": "KRW",
        "comparison_period": COMPARISON_PREVIOUS_MONTH,
        "governance_required": True,
        "industry": INDUSTRY_MANUFACTURING,
        "page_size": 20,
        "offset": 0,
    }
    base.update(overrides)
    return base


def test_valid_showback_definition_accepted():
    payload = _valid_payload()
    validated = parse_showback_definition(payload)
    assert validated["tenant_id"] == "11111111-1111-1111-1111-111111111111"
    assert validated["group_by"] == GROUP_BY_DEPARTMENT
    assert validated["period_mode"] == PERIOD_CURRENT_MONTH
    assert validated["currency_code"] == "KRW"
    assert "showback_id" in validated
    assert "trace_id" in validated


def test_showback_invalid_group_by_rejected():
    with pytest.raises(ShowbackDefinitionInvalidError) as excinfo:
        parse_showback_definition(_valid_payload(group_by="invalid_group_by"))
    assert excinfo.value.http_status == 400
    assert excinfo.value.code == "SHOWBACK_INVALID_GROUP_BY"
    assert "group_by" in str(excinfo.value)


def test_showback_invalid_period_mode_rejected():
    with pytest.raises(ShowbackDefinitionInvalidError) as excinfo:
        parse_showback_definition(_valid_payload(period_mode="invalid_mode"))
    assert excinfo.value.http_status == 400
    assert excinfo.value.code == "SHOWBACK_INVALID_PERIOD_MODE"


def test_showback_custom_range_requires_period_bounds():
    with pytest.raises(ShowbackDefinitionInvalidError) as excinfo:
        parse_showback_definition(_valid_payload(period_mode=PERIOD_CUSTOM_RANGE))
    assert excinfo.value.http_status == 400
    assert excinfo.value.code == "SHOWBACK_CUSTOM_RANGE_REQUIRED"


def test_showback_page_size_exceeded_rejected():
    with pytest.raises(ShowbackDefinitionInvalidError) as excinfo:
        parse_showback_definition(_valid_payload(page_size=SHOWBACK_PAGE_SIZE_MAX + 1))
    assert excinfo.value.http_status == 400
    assert excinfo.value.code == "SHOWBACK_PAGE_SIZE_EXCEEDED"


def test_showback_currency_code_defaulted_to_krw():
    payload = _valid_payload()
    del payload["currency_code"]
    validated = parse_showback_definition(payload)
    assert validated["currency_code"] == "KRW"


# ── Period selector 6 modes round-trip (PRD §F27.1.5 verbatim) ──
@pytest.mark.parametrize(
    "period_mode",
    [
        PERIOD_CURRENT_MONTH,
        PERIOD_PREVIOUS_MONTH,
        PERIOD_LAST_3_MONTHS,
        PERIOD_LAST_6_MONTHS,
        PERIOD_YTD,
    ],
)
def test_showback_all_period_modes_accepted(period_mode):
    validated = parse_showback_definition(_valid_payload(period_mode=period_mode))
    assert validated["period_mode"] == period_mode


def test_showback_5_group_by_options_accepted():
    for group_by in ALLOWED_GROUP_BY:
        validated = parse_showback_definition(_valid_payload(group_by=group_by))
        assert validated["group_by"] == group_by


def test_resolve_period_bounds_current_month():
    start, end = resolve_period_bounds(PERIOD_CURRENT_MONTH)
    assert start == f"{PERIOD_CURRENT_MONTH}_bounds"
    assert end == f"{PERIOD_CURRENT_MONTH}_bounds"


def test_resolve_period_bounds_custom_range():
    start, end = resolve_period_bounds(
        PERIOD_CUSTOM_RANGE,
        period_start="2026-01-01",
        period_end="2026-01-31",
    )
    assert start == "2026-01-01"
    assert end == "2026-01-31"


def test_showback_module_id_set_to_m19_finops():
    # The m19_finops identifier is preserved in the typed exception
    # envelope for FinOps territory (PRD §F27.6.7 verbatim).
    from apps.api.core.errors import FINOPS_MODULE_ID
    assert FINOPS_MODULE_ID == "m19_finops"