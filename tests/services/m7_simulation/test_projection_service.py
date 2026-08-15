"""tests.services.m7_simulation.test_projection_service — Story 7.2.

15+ test cases for ProjectionService + boundary conversion:
- chronological invariant validation (projection_month > period_key)
- AD-24 YYYY-MM format validation
- ProjectionBaselineNotFoundError wrap of CVPBaselineNotFoundError
- project_next_month pure kernel delegation (loss + profit scenarios)
- _to_projection_inputs boundary conversion
- ProjectionInputsInvalidError on bad Decimal cast
- serializers Decimal-as-string parity
- PDF envelope builder (M5 §9 #20+ shape)
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.modules.m7_simulation.exceptions import (
    CVPBaselineNotFoundError,
    InvalidProjectionMonthError,
    ProjectionBaselineNotFoundError,
    ProjectionInputsInvalidError,
)
from apps.api.modules.m7_simulation.services.projection_service import (
    ProjectionService,
    _to_projection_inputs,
)
from packages.cost_engine.cvp import CVPBaseline
from packages.cost_engine.projection import (
    PROJECTION_MONTH_PATTERN,
    NextMonthProjection,
    ProjectionInputs,
    project_next_month,
)
from packages.services.m7_simulation.projection_pdf_helpers import (
    PROJECTION_PDF_REPORT_CODE,
    PROJECTION_PDF_TITLE_KO,
    serialize_projection_pdf_envelope,
)
from packages.services.m7_simulation.projection_serializers import (
    serialize_projection_inputs,
    serialize_projection_result,
)


# ── Fixtures ────────────────────────────────────────────────────
def _make_baseline() -> CVPBaseline:
    """Construct a profitable CVPBaseline.

    unit_price (1,000,000) × operating_rate (0.85) = 850,000 (per-unit revenue proxy)
    unit_variable_cost (200,000) × operating_rate (0.85) = 170,000 (per-unit variable cost proxy)
    gross margin per unit proxy = 680,000 > fixed_cost (1,000) = profit
    """
    return CVPBaseline(
        fixed_cost=Decimal("1000"),
        unit_variable_cost=Decimal("200000"),
        unit_price=Decimal("1000000"),
        operating_rate=Decimal("0.85"),
        target_profit=Decimal("500000"),
    )


def _make_loss_baseline() -> CVPBaseline:
    """Construct a high-cost CVPBaseline for loss projection.

    unit_price (10,000) × operating_rate (0.7) = 7,000 (per-unit revenue proxy)
    unit_variable_cost (8,000) × operating_rate (0.7) = 5,600 (per-unit variable cost proxy)
    gross margin per unit proxy = 1,400 < fixed_cost (10,000,000) → loss when scaled
    """
    return CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("8000"),
        unit_price=Decimal("10000"),
        operating_rate=Decimal("0.7"),
        target_profit=Decimal("0"),
    )


def _make_inputs(
    *,
    loan_amount: str = "10000000",
    interest_rate: str = "5",
    cost_inflation_rate: str = "0",
    corporate_tax_rate: str = "22",
) -> ProjectionInputs:
    return ProjectionInputs(
        loan_amount=Decimal(loan_amount),
        interest_rate=Decimal(interest_rate),
        cost_inflation_rate=Decimal(cost_inflation_rate),
        corporate_tax_rate=Decimal(corporate_tax_rate),
    )


def _make_service() -> ProjectionService:
    """Build ProjectionService with mocked AsyncSession."""
    return ProjectionService(
        session=MagicMock(),
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="test-trace-123",
    )


# ── PROJECTION_MONTH_PATTERN constant ───────────────────────────
def test_projection_month_pattern_matches_valid_format() -> None:
    """AD-24 YYYY-MM regex matches valid periods."""
    import re

    valid = ["2025-01", "2025-12", "2026-06"]
    for v in valid:
        assert re.match(PROJECTION_MONTH_PATTERN, v), f"should match {v}"


def test_projection_month_pattern_rejects_invalid_format() -> None:
    """AD-24 YYYY-MM regex rejects malformed periods."""
    import re

    invalid = ["25-01", "2025-1", "2025/01", "abc", "2025-13", "2025-00"]
    for inv in invalid:
        assert not re.match(PROJECTION_MONTH_PATTERN, inv), f"should not match {inv}"


# ── project_next_month — profit scenario ───────────────────────
def test_project_next_month_profit_scenario_has_positive_after_tax() -> None:
    """Profit baseline → after_tax_income > 0 + corporate_tax > 0."""
    baseline = _make_baseline()
    inputs = _make_inputs()
    projection = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs
    )
    assert isinstance(projection, NextMonthProjection)
    assert projection.after_tax_income > Decimal("0")
    assert projection.corporate_tax > Decimal("0")
    assert projection.interest_expense == Decimal("500000")  # 10000000 * 5%


# ── project_next_month — loss scenario ─────────────────────────
def test_project_next_month_loss_scenario_zero_corporate_tax() -> None:
    """Loss baseline → after_tax_income < 0 + corporate_tax = 0 (CR 12-1 contract)."""
    baseline = _make_loss_baseline()
    inputs = _make_inputs(cost_inflation_rate="-50")
    projection = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs
    )
    assert projection.after_tax_income < Decimal("0")
    assert projection.corporate_tax == Decimal("0")


# ── _to_projection_inputs — happy path ─────────────────────────
def test_to_projection_inputs_valid_returns_frozen_dataclass() -> None:
    """Valid form_data → ProjectionInputs (frozen=True, slots=True)."""
    form_data = {
        "loan_amount": "10000000",
        "interest_rate": "5",
        "cost_inflation_rate": "3",
        "corporate_tax_rate": "22",
    }
    inputs = _to_projection_inputs(form_data)
    assert isinstance(inputs, ProjectionInputs)
    assert inputs.loan_amount == Decimal("10000000")
    assert inputs.interest_rate == Decimal("5")
    assert inputs.cost_inflation_rate == Decimal("3")
    assert inputs.corporate_tax_rate == Decimal("22")


# ── _to_projection_inputs — bad Decimal cast ──────────────────
def test_to_projection_inputs_bad_decimal_raises_service_error() -> None:
    """Non-numeric string → ProjectionInputsInvalidError (service layer)."""
    form_data = {
        "loan_amount": "not-a-number",
        "interest_rate": "5",
        "cost_inflation_rate": "3",
        "corporate_tax_rate": "22",
    }
    with pytest.raises(ProjectionInputsInvalidError) as exc_info:
        _to_projection_inputs(form_data)
    assert exc_info.value.reason  # has explanation


def test_to_projection_inputs_missing_field_raises_service_error() -> None:
    """Missing field → ProjectionInputsInvalidError."""
    form_data = {
        "loan_amount": "10000000",
        # interest_rate missing
        "cost_inflation_rate": "3",
        "corporate_tax_rate": "22",
    }
    with pytest.raises(ProjectionInputsInvalidError):
        _to_projection_inputs(form_data)


# ── fetch_projection_baseline — format validation ──────────────
@pytest.mark.asyncio
async def test_fetch_projection_baseline_rejects_bad_period_key() -> None:
    """period_key not YYYY-MM → InvalidProjectionMonthError."""
    service = _make_service()
    with pytest.raises(InvalidProjectionMonthError) as exc_info:
        await service.fetch_projection_baseline(
            period_key="25-01", projection_month="2025-02"
        )
    assert "format" in exc_info.value.reason.lower() or "must match" in exc_info.value.reason.lower()


@pytest.mark.asyncio
async def test_fetch_projection_baseline_rejects_bad_projection_month() -> None:
    """projection_month not YYYY-MM → InvalidProjectionMonthError."""
    service = _make_service()
    with pytest.raises(InvalidProjectionMonthError):
        await service.fetch_projection_baseline(
            period_key="2025-01", projection_month="bad-month"
        )


# ── fetch_projection_baseline — chronological invariant ───────
@pytest.mark.asyncio
async def test_fetch_projection_baseline_rejects_equal_month() -> None:
    """projection_month == period_key → InvalidProjectionMonthError (strict >)."""
    service = _make_service()
    with pytest.raises(InvalidProjectionMonthError) as exc_info:
        await service.fetch_projection_baseline(
            period_key="2025-06", projection_month="2025-06"
        )
    assert "strictly after" in exc_info.value.reason.lower()


@pytest.mark.asyncio
async def test_fetch_projection_baseline_rejects_earlier_month() -> None:
    """projection_month < period_key → InvalidProjectionMonthError."""
    service = _make_service()
    with pytest.raises(InvalidProjectionMonthError):
        await service.fetch_projection_baseline(
            period_key="2025-12", projection_month="2025-01"
        )


# ── fetch_projection_baseline — CVP wrap to Projection 404 ────
@pytest.mark.asyncio
async def test_fetch_projection_baseline_wraps_cvp_not_found() -> None:
    """CVPBaselineNotFoundError → ProjectionBaselineNotFoundError."""
    import sys

    fake_instance = MagicMock()
    fake_instance.fetch_cvp_baseline = AsyncMock(
        side_effect=CVPBaselineNotFoundError(
            tenant_id="00000000-0000-0000-0000-000000000000",
            period_key="2025-06",
        )
    )

    class FakeCVPService:
        def __init__(self, session, **kwargs):
            self.session = session
            self.kwargs = kwargs

        async def fetch_cvp_baseline(self, *, period_key):
            return await fake_instance.fetch_cvp_baseline(period_key=period_key)

    # Patch the lazy-import target via sys.modules so the
    # `from apps.api.modules.m7_simulation.services.cvp_simulation_service import CVPSimulationService`
    # inside `projection_service.fetch_projection_baseline` returns our fake.
    cvp_svc_module_path = (
        "apps.api.modules.m7_simulation.services.cvp_simulation_service"
    )
    original_module = sys.modules.get(cvp_svc_module_path)
    sys.modules[cvp_svc_module_path] = MagicMock()
    sys.modules[cvp_svc_module_path].CVPSimulationService = FakeCVPService
    try:
        service = _make_service()
        with pytest.raises(ProjectionBaselineNotFoundError):
            await service.fetch_projection_baseline(
                period_key="2025-06", projection_month="2025-07"
            )
    finally:
        if original_module is not None:
            sys.modules[cvp_svc_module_path] = original_module
        else:
            sys.modules.pop(cvp_svc_module_path, None)


# ── compute — happy path ──────────────────────────────────────
@pytest.mark.asyncio
async def test_compute_returns_baseline_and_projection() -> None:
    """Happy path: returns (CVPBaseline, NextMonthProjection) tuple."""
    service = _make_service()
    baseline = _make_baseline()
    inputs = _make_inputs()

    # Patch fetch_projection_baseline to return our baseline.
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            service,
            "fetch_projection_baseline",
            AsyncMock(return_value=baseline),
        )
        result_baseline, result_projection = await service.compute(
            period_key="2025-06",
            projection_month="2025-07",
            projection_inputs=inputs,
        )
    assert isinstance(result_baseline, CVPBaseline)
    assert isinstance(result_projection, NextMonthProjection)
    assert result_projection.after_tax_income > Decimal("0")


# ── compute — ProjectionInputsInvalidError wrap ───────────────
@pytest.mark.asyncio
async def test_compute_wraps_kernel_invalid_input_error() -> None:
    """ProjectionInvalidInputError (kernel) → ProjectionInputsInvalidError (service)."""
    service = _make_service()
    baseline = _make_baseline()
    # Negative loan_amount triggers kernel validation.
    bad_inputs = _make_inputs(loan_amount="-1")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            service,
            "fetch_projection_baseline",
            AsyncMock(return_value=baseline),
        )
        with pytest.raises(ProjectionInputsInvalidError) as exc_info:
            await service.compute(
                period_key="2025-06",
                projection_month="2025-07",
                projection_inputs=bad_inputs,
            )
    assert exc_info.value.reason


# ── Serializers — Decimal-as-string parity ─────────────────────
def test_serialize_projection_inputs_returns_decimal_strings() -> None:
    """ProjectionInputs → dict of Decimal-as-string (AD-15 §1)."""
    inputs = _make_inputs(cost_inflation_rate="3")
    serialized = serialize_projection_inputs(inputs)
    assert serialized == {
        "loan_amount": "10000000",
        "interest_rate": "5",
        "cost_inflation_rate": "3",
        "corporate_tax_rate": "22",
    }
    assert all(isinstance(v, str) for v in serialized.values())


def test_serialize_projection_result_returns_decimal_strings() -> None:
    """NextMonthProjection → dict of Decimal-as-string (AD-15 §1)."""
    baseline = _make_baseline()
    inputs = _make_inputs()
    projection = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs
    )
    serialized = serialize_projection_result(projection)
    expected_keys = {
        "projected_revenue",
        "projected_variable_cost",
        "projected_fixed_cost",
        "interest_expense",
        "pre_tax_income",
        "corporate_tax",
        "after_tax_income",
    }
    assert set(serialized.keys()) == expected_keys
    assert all(isinstance(v, str) for v in serialized.values())


# ── PDF envelope — M5 §9 #20+ shape ────────────────────────────
def test_serialize_projection_pdf_envelope_shape() -> None:
    """PDF envelope carries report_code='COST_PREDICTION' + title='원가 예측 보고서'."""
    baseline = _make_baseline()
    inputs = _make_inputs()
    projection = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs
    )
    envelope = serialize_projection_pdf_envelope(
        baseline=baseline,
        projection_inputs=inputs,
        projection=projection,
        period_key="2025-06",
        projection_month="2025-07",
    )
    assert envelope["report_code"] == PROJECTION_PDF_REPORT_CODE
    assert envelope["report_code"] == "COST_PREDICTION"
    assert envelope["title"] == PROJECTION_PDF_TITLE_KO
    assert envelope["title"] == "원가 예측 보고서"
    assert envelope["period_key"] == "2025-06"
    assert envelope["projection_month"] == "2025-07"
    # All values must be Decimal-as-string (no raw floats).
    for key, value in envelope.items():
        if isinstance(value, dict):
            for nested_key, nested_value in value.items():
                assert isinstance(nested_value, (str, type(None))) or not isinstance(
                    nested_value, float
                ), f"{key}.{nested_key} must be string (got {type(nested_value)})"


# ── Frozen enforcement ─────────────────────────────────────────
def test_projection_inputs_is_frozen() -> None:
    """ProjectionInputs is frozen (AD-5 immutability)."""
    from dataclasses import FrozenInstanceError

    inputs = _make_inputs()
    with pytest.raises(FrozenInstanceError):
        inputs.loan_amount = Decimal("0")  # type: ignore[misc]
