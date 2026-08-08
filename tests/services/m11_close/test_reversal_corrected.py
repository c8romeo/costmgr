"""tests.services.m11_close.test_reversal_corrected — Story 11.1 pure kernel #2.

8 cases per AC #8 spec:
- build_reversal_corrected_event (3): 정상 + corrected_qty=None skip + corrected_period_key 변경
- validate_reversal_corrected_constraints (2): correction_group_id 일치 / period_key AD-24 형식
- banker's rounding (2)
- period_key AD-24 validation (1)
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from packages.services.m4_inventory.ledger import InventoryLedgerEvent
from packages.services.m11_close.reversal_corrected import (
    ERROR_CODE_INCONSISTENT_CORRECTION_GROUP,
    ERROR_CODE_INVALID_CORRECTION_GROUP_ID,
    ERROR_CODE_MISSING_CORRECTED_PERIOD_KEY,
    ERROR_CODE_MISSING_CORRECTED_QTY,
    REVERSAL_CORRECTED_EVENT_TYPE,
    ReversalCorrectedBuildError,
    build_reversal_corrected_event,
    validate_reversal_corrected_constraints,
)


def _make_target_event(
    *,
    event_type: str = "purchase_inbound",
    qty: Decimal | None = Decimal("100"),
    period_key: str = "2026-08",
) -> InventoryLedgerEvent:
    return InventoryLedgerEvent(
        event_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        product_id=uuid.uuid4(),
        period_key=period_key,
        event_type=event_type,
        qty=qty,
        trace_id=uuid.uuid4(),
        reverses_event_id=None,
        correction_group_id=None,
        payload={"source": "monthly_input"},
    )


class TestBuildReversalCorrectedEvent:
    """build_reversal_corrected_event: 정상 + skip + period_key 변경."""

    def test_normal_corrected_row_same_period(self) -> None:
        """정상 — corrected_qty=150, corrected_period_key='2026-08' (same period)."""
        target = _make_target_event()
        cgid = uuid.uuid4()
        result = build_reversal_corrected_event(
            target_event=target,
            correction_group_id=cgid,
            corrected_qty=Decimal("150"),
            corrected_period_key="2026-08",
            actor_id=uuid.uuid4(),
            trace_id=uuid.uuid4(),
        )
        assert result is not None
        assert result.event_type == REVERSAL_CORRECTED_EVENT_TYPE
        assert result.qty == Decimal("150.0000")
        assert result.correction_group_id == cgid
        # D1 — corrected row does NOT carry `reverses_event_id`. Only the
        # sign-negating row owns `reverses_event_id=target_event.event_id`.
        # The corrected row's link to the target is via `correction_group_id`
        # (shared with the negating row). This prevents the (tenant_id,
        # reverses_event_id) PARTIAL UNIQUE INDEX from blocking a second
        # corrected INSERT on the same target.
        assert result.reverses_event_id is None
        assert result.period_key == "2026-08"

    def test_skip_when_corrected_qty_and_period_key_none(self) -> None:
        """skip path — corrected_qty=None AND corrected_period_key=None → None."""
        target = _make_target_event()
        result = build_reversal_corrected_event(
            target_event=target,
            correction_group_id=uuid.uuid4(),
            corrected_qty=None,
            corrected_period_key=None,
            actor_id=uuid.uuid4(),
            trace_id=uuid.uuid4(),
        )
        assert result is None

    def test_corrected_period_key_differs_from_target(self) -> None:
        """corrected_period_key가 target.period_key와 다른 경우 (cross-period correction)."""
        target = _make_target_event(period_key="2026-08")
        result = build_reversal_corrected_event(
            target_event=target,
            correction_group_id=uuid.uuid4(),
            corrected_qty=Decimal("50"),
            corrected_period_key="2026-09",
            actor_id=uuid.uuid4(),
            trace_id=uuid.uuid4(),
        )
        assert result is not None
        assert result.period_key == "2026-09"
        assert result.reversal_of_period_key == "2026-08"


class TestValidateReversalCorrectedConstraints:
    """correction_group_id 일치 + period_key AD-24 형식 검증."""

    def test_inconsistent_correction_group_rejected(self) -> None:
        """negating_correction_group_id와 다르면 ERROR_CODE_INCONSISTENT_CORRECTION_GROUP."""
        with pytest.raises(ReversalCorrectedBuildError) as exc_info:
            validate_reversal_corrected_constraints(
                target_event=_make_target_event(),
                correction_group_id=uuid.uuid4(),
                corrected_period_key="2026-08",
                negating_correction_group_id=uuid.uuid4(),  # 다른 UUID
            )
        assert exc_info.value.error_code == ERROR_CODE_INCONSISTENT_CORRECTION_GROUP

    def test_invalid_period_key_pattern_rejected(self) -> None:
        """period_key '2026-8' (1-digit month) 거부 — ERROR_CODE_INVALID_CORRECTION_GROUP_ID."""
        with pytest.raises(ReversalCorrectedBuildError) as exc_info:
            validate_reversal_corrected_constraints(
                target_event=_make_target_event(),
                correction_group_id=uuid.uuid4(),
                corrected_period_key="2026-8",  # 1-digit month — invalid
            )
        assert exc_info.value.error_code == ERROR_CODE_INVALID_CORRECTION_GROUP_ID

    def test_corrected_qty_without_period_key_rejected(self) -> None:
        """corrected_qty만 있고 corrected_period_key=None 시 거부."""
        with pytest.raises(ReversalCorrectedBuildError) as exc_info:
            build_reversal_corrected_event(
                target_event=_make_target_event(),
                correction_group_id=uuid.uuid4(),
                corrected_qty=Decimal("50"),
                corrected_period_key=None,
                actor_id=uuid.uuid4(),
                trace_id=uuid.uuid4(),
            )
        assert exc_info.value.error_code == ERROR_CODE_MISSING_CORRECTED_PERIOD_KEY

    def test_corrected_period_key_without_qty_rejected(self) -> None:
        """corrected_period_key만 있고 corrected_qty=None 시 거부."""
        with pytest.raises(ReversalCorrectedBuildError) as exc_info:
            build_reversal_corrected_event(
                target_event=_make_target_event(),
                correction_group_id=uuid.uuid4(),
                corrected_qty=None,
                corrected_period_key="2026-08",
                actor_id=uuid.uuid4(),
                trace_id=uuid.uuid4(),
            )
        assert exc_info.value.error_code == ERROR_CODE_MISSING_CORRECTED_QTY


class TestBankersRounding:
    """Banker's rounding parity for corrected_qty (CR 0-4)."""

    def test_corrected_qty_5_decimal_places_quantized(self) -> None:
        """5+ 자릿수 → NUMERIC(18,4) quantization with ROUND_HALF_EVEN."""
        target = _make_target_event()
        result = build_reversal_corrected_event(
            target_event=target,
            correction_group_id=uuid.uuid4(),
            corrected_qty=Decimal("200.56789"),
            corrected_period_key="2026-08",
            actor_id=uuid.uuid4(),
            trace_id=uuid.uuid4(),
        )
        assert result is not None
        # 200.56789 → ROUND_HALF_EVEN at 0.0001 → 200.5679
        assert result.qty == Decimal("200.5679")

    def test_corrected_qty_zero_rounding(self) -> None:
        """Decimal('0') → Decimal('0.0000') after quantization."""
        target = _make_target_event()
        result = build_reversal_corrected_event(
            target_event=target,
            correction_group_id=uuid.uuid4(),
            corrected_qty=Decimal("0"),
            corrected_period_key="2026-08",
            actor_id=uuid.uuid4(),
            trace_id=uuid.uuid4(),
        )
        assert result is not None
        assert result.qty == Decimal("0.0000")


class TestPeriodKeyValidation:
    """period_key AD-24 형식."""

    def test_valid_period_key_yyyy_mm(self) -> None:
        """'YYYY-MM' 형식 통과."""
        target = _make_target_event()
        # Should not raise
        validate_reversal_corrected_constraints(
            target_event=target,
            correction_group_id=uuid.uuid4(),
            corrected_period_key="2026-12",
        )

    def test_invalid_period_key_virtual_budget_excluded(self) -> None:
        """M8 virtual budget key 'YYYY-MM#B<n>' 거부 (5-2 wire pattern)."""
        target = _make_target_event()
        with pytest.raises(ReversalCorrectedBuildError) as exc_info:
            validate_reversal_corrected_constraints(
                target_event=target,
                correction_group_id=uuid.uuid4(),
                corrected_period_key="2026-08#B1",  # M8 virtual key
            )
        assert exc_info.value.error_code == ERROR_CODE_INVALID_CORRECTION_GROUP_ID
