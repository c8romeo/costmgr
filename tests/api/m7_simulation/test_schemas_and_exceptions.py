"""tests.api.m7_simulation.test_schemas_and_exceptions — M7 simulation source health tests.

Source health 갭 회복 wire (순서 2, cj-style 307번째 정직 회복) — M7 module-scoped:
M7 simulation 모듈 (CVP/BEP + 차월 추정, PRD §F7.1 + §F7.2) 의 source health 검증.
env-free (Pydantic + pure exception only), LOW risk.

검증 항목:

1. **CVPSimulationRequest period_key validation (AD-24)**
   - YYYY-MM 7자 fixed length
   - period_key regex pattern matching M3 contract

2. **CVPDeltaRequest Decimal-as-string validation (AD-8)**
   - 4 percentage delta fields, default "0"
   - Decimal 변환 가능해야 함 (Pydantic field_validator)
   - 잘못된 decimal string rejected
   - frozen=True (불변 request contract)

3. **ProjectionInputsRequest 4종 파라미터 (PRD §F7.2)**
   - loan_amount + interest_rate + cost_inflation_rate + corporate_tax_rate
   - 모두 Decimal-as-string, AD-15 §1 parity

4. **Typed exceptions (CR 12-5 D-14 envelope)**
   - 5 typed exceptions + 5 Korean message constants
   - __all__ export completeness
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError


# ── Test 1 — CVPSimulationRequest period_key validation ──────────────


def test_cvp_simulation_request_period_key_yyyy_mm_validation():
    """AD-24: period_key 7자 YYYY-MM format.

    (a) 유효한 "2026-07" → accepted
    (b) 6자 "2026-7" → rejected (min_length=7)
    (c) 8자 "2026-077" → rejected (max_length=7)
    (d) 잘못된 월 "2026-13" → rejected (regex pattern)
    """
    from apps.api.modules.m7_simulation.schemas import CVPSimulationRequest

    # (a) valid
    req = CVPSimulationRequest(period_key="2026-07")
    assert req.period_key == "2026-07"

    # (b) too short
    with pytest.raises(ValidationError):
        CVPSimulationRequest(period_key="2026-7")

    # (c) too long
    with pytest.raises(ValidationError):
        CVPSimulationRequest(period_key="2026-077")

    # (d) invalid month
    with pytest.raises(ValidationError):
        CVPSimulationRequest(period_key="2026-13")


def test_cvp_simulation_request_extra_forbid_and_frozen():
    """CVPSimulationRequest: extra='forbid' + frozen=True (불변 contract).

    (a) extra field rejected
    (b) mutation rejected (frozen)
    """
    from apps.api.modules.m7_simulation.schemas import CVPSimulationRequest

    req = CVPSimulationRequest(period_key="2026-07")

    # (a) extra forbid
    with pytest.raises(ValidationError):
        CVPSimulationRequest(period_key="2026-07", unknown="bad")  # type: ignore[call-arg]

    # (b) frozen — assignment rejected
    with pytest.raises(ValidationError):
        req.period_key = "2026-08"  # type: ignore[misc]


# ── Test 2 — CVPDeltaRequest Decimal-as-string validation ────────────


def test_cvp_delta_request_4_fields_decimal_string_validation():
    """AD-8 + AD-15: CVPDeltaRequest 4 fields Decimal-as-string.

    (a) all 4 fields default "0"
    (b) invalid decimal string rejected ("abc", empty)
    (c) valid decimal accepted ("0.5", "-0.3", "1.234")
    """
    from apps.api.modules.m7_simulation.schemas import CVPDeltaRequest

    # (a) defaults
    delta = CVPDeltaRequest()
    assert delta.unit_price_delta_pct == "0"
    assert delta.unit_variable_cost_delta_pct == "0"
    assert delta.fixed_cost_delta_pct == "0"
    assert delta.operating_rate_delta_pct == "0"

    # (b) invalid decimal strings
    for bad in ["abc", "", "not-a-number", "1.2.3"]:
        with pytest.raises(ValidationError):
            CVPDeltaRequest(unit_price_delta_pct=bad)

    # (c) valid decimal strings (range doesn't matter at Pydantic layer —
    # range validation is service-layer / pure kernel responsibility)
    for good in ["0", "0.5", "-0.3", "1.234", "0.0001"]:
        delta = CVPDeltaRequest(unit_price_delta_pct=good)
        assert delta.unit_price_delta_pct == good


# ── Test 3 — ProjectionInputsRequest 4종 파라미터 ────────────────────


def test_projection_inputs_request_4_fields_decimal_validation():
    """PRD §F7.2: ProjectionInputsRequest 4종 파라미터 강제.

    (a) loan_amount required (no default)
    (b) interest_rate / cost_inflation_rate / corporate_tax_rate default "0"
    (c) all Decimal-as-string (AD-15 §1 parity)
    (d) invalid decimal rejected
    """
    from apps.api.modules.m7_simulation.schemas import ProjectionInputsRequest

    # (a) + (b) minimal
    inp = ProjectionInputsRequest(loan_amount="100000000")
    assert inp.loan_amount == "100000000"
    assert inp.interest_rate == "0"
    assert inp.cost_inflation_rate == "0"
    assert inp.corporate_tax_rate == "0"

    # (b) full
    inp_full = ProjectionInputsRequest(
        loan_amount="50000000",
        interest_rate="3.5",
        cost_inflation_rate="2.1",
        corporate_tax_rate="22",
    )
    assert inp_full.interest_rate == "3.5"
    assert inp_full.cost_inflation_rate == "2.1"

    # (c) + (d) invalid decimal rejected for any field
    with pytest.raises(ValidationError):
        ProjectionInputsRequest(loan_amount="not-a-number")
    with pytest.raises(ValidationError):
        ProjectionInputsRequest(
            loan_amount="0", interest_rate="invalid"
        )
    with pytest.raises(ValidationError):
        ProjectionInputsRequest(
            loan_amount="0", cost_inflation_rate="bad"
        )
    with pytest.raises(ValidationError):
        ProjectionInputsRequest(
            loan_amount="0", corporate_tax_rate="bad"
        )


def test_projection_compute_request_period_key_and_projection_month_validation():
    """PRD §F7.2: ProjectionComputeRequest period_key + projection_month both YYYY-MM.

    (a) valid combination accepted
    (b) projection_month invalid month → rejected
    (c) extra forbid
    """
    from apps.api.modules.m7_simulation.schemas import (
        ProjectionComputeRequest,
        ProjectionInputsRequest,
    )

    # (a) valid
    req = ProjectionComputeRequest(
        period_key="2026-07",
        projection_month="2026-08",
        inputs=ProjectionInputsRequest(loan_amount="0"),
    )
    assert req.period_key == "2026-07"
    assert req.projection_month == "2026-08"

    # (b) invalid month
    with pytest.raises(ValidationError):
        ProjectionComputeRequest(
            period_key="2026-07",
            projection_month="2026-13",  # invalid month
            inputs=ProjectionInputsRequest(loan_amount="0"),
        )

    # (c) extra forbid
    with pytest.raises(ValidationError):
        ProjectionComputeRequest(
            period_key="2026-07",
            projection_month="2026-08",
            inputs=ProjectionInputsRequest(loan_amount="0"),
            bad_field="x",  # type: ignore[call-arg]
        )


# ── Test 4 — Typed exceptions + Korean messages (CR 12-5 D-14) ──────


def test_m7_typed_exceptions_and_korean_message_constants():
    """CR 12-5 D-14: 5 typed exceptions + 5 Korean message constants.

    - CVPBaselineNotFoundError + CVP_BASELINE_NOT_FOUND_KO (404)
    - CVPInvalidDeltaError + CVP_INVALID_DELTA_KO (422)
    - InvalidProjectionMonthError + INVALID_PROJECTION_MONTH_KO (422)
    - ProjectionInputsInvalidError + PROJECTION_INPUTS_INVALID_KO (422)
    - ProjectionBaselineNotFoundError + PROJECTION_BASELINE_NOT_FOUND_KO (404)
    """
    import inspect

    from apps.api.modules.m7_simulation import exceptions as exc_mod

    # (a) exception classes
    expected_classes = [
        "CVPBaselineNotFoundError",
        "CVPInvalidDeltaError",
        "InvalidProjectionMonthError",
        "ProjectionInputsInvalidError",
        "ProjectionBaselineNotFoundError",
    ]
    for cls_name in expected_classes:
        cls_obj = getattr(exc_mod, cls_name, None)
        assert cls_obj is not None, (
            f"M7 must export {cls_name} (CR 12-5 D-14 typed exception)"
        )
        assert inspect.isclass(cls_obj), (
            f"{cls_name} must be a class, got {type(cls_obj).__name__}"
        )

    # (b) Korean message constants
    expected_messages = [
        "CVP_BASELINE_NOT_FOUND_KO",
        "CVP_INVALID_DELTA_KO",
        "INVALID_PROJECTION_MONTH_KO",
        "PROJECTION_INPUTS_INVALID_KO",
        "PROJECTION_BASELINE_NOT_FOUND_KO",
    ]
    for msg_name in expected_messages:
        msg_value = getattr(exc_mod, msg_name, None)
        assert msg_value is not None, (
            f"M7 must export {msg_name} (CR 12-5 D-14 envelope Korean message)"
        )
        assert isinstance(msg_value, str) and len(msg_value) > 0, (
            f"{msg_name} must be non-empty Korean string, got {msg_value!r}"
        )
        # must contain Korean (Hangul Syllables U+AC00~U+D7A3)
        korean_pattern = __import__("re").compile(r"[가-힣]")
        assert korean_pattern.search(msg_value), (
            f"{msg_name}={msg_value!r} must contain Korean characters"
        )

    # (c) __all__ export completeness
    all_exports = getattr(exc_mod, "__all__", None)
    assert all_exports is not None, "M7 exceptions must define __all__"
    for name in expected_classes + expected_messages:
        assert name in all_exports, (
            f"M7 exceptions.__all__ must include {name}. got={all_exports}"
        )


def test_cvp_baseline_not_found_error_attributes_preserved():
    """CR 12-5 D-14: CVPBaselineNotFoundError attribute contract.

    - tenant_id, period_key 보존 (HTTP envelope 메타데이터)
    - message attribute (default or custom)
    - super().__init__(message) — Exception 상속
    """
    from apps.api.modules.m7_simulation.exceptions import CVPBaselineNotFoundError

    err = CVPBaselineNotFoundError(
        tenant_id="tenant-001",
        period_key="2026-07",
    )
    assert err.tenant_id == "tenant-001"
    assert err.period_key == "2026-07"
    assert "2026-07" in str(err), (
        f"Exception message must include period_key for diagnosis. got={str(err)!r}"
    )
    assert "tenant-001" in str(err), (
        f"Exception message must include tenant_id for diagnosis. got={str(err)!r}"
    )

    # custom message override
    err_custom = CVPBaselineNotFoundError(
        tenant_id="tenant-001",
        period_key="2026-07",
        message="custom Korean message",
    )
    assert err_custom.message == "custom Korean message"
    assert str(err_custom) == "custom Korean message"
