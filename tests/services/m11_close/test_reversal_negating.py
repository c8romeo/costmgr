"""tests.services.m11_close.test_reversal_negating — Story 11.1 pure kernel #1.

10 cases per AC #8 spec:
- build_reversal_negating_event (4): 정상 + 4 self-reversal 거부
- validate_reversal_negating_constraints (3): opening_carried / purchase_inbound /
  closing_snapshot reversal 가능 검증 + reversal_negating/reversal_corrected 자체 reversal 불가
- banker's rounding (2)
- M11_AUTHORIZE_KO constants (1)
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from packages.services.m4_inventory.ledger import InventoryLedgerEvent
from packages.services.m11_close.reversal_negating import (
    ERROR_CODE_EMPTY_REASON,
    ERROR_CODE_SELF_REVERSAL,
    ERROR_CODE_TARGET_NOT_REVERSIBLE,
    M11_AUTHORIZE_KO,
    REVERSAL_NEGATING_EVENT_TYPE,
    REVERSIBLE_TARGET_EVENT_TYPES,
    ReversalNegatingBuildError,
    build_reversal_negating_event,
    validate_reversal_negating_constraints,
)


def _make_target_event(
    *,
    event_type: str = "purchase_inbound",
    qty: Decimal | None = Decimal("100"),
    period_key: str = "2026-08",
) -> InventoryLedgerEvent:
    """Build a test InventoryLedgerEvent row."""
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


class TestBuildReversalNegatingEvent:
    """build_reversal_negating_event: 4 정상 + 4 self-reversal 거부."""

    def test_normal_purchase_inbound_reversal(self) -> None:
        """정상 — purchase_inbound qty=100 → negating qty=-100.0000."""
        target = _make_target_event(qty=Decimal("100"))
        result = build_reversal_negating_event(
            target_event=target,
            reason="테스트 — PRD §F11.3 sign flip",
            actor_id=uuid.uuid4(),
            correction_group_id=uuid.uuid4(),
            trace_id=uuid.uuid4(),
        )
        assert result.event_type == REVERSAL_NEGATING_EVENT_TYPE
        assert result.qty == Decimal("-100.0000")
        assert result.reverses_event_id == target.event_id
        assert result.correction_group_id is not None
        assert result.period_key == target.period_key
        assert result.reversal_of_period_key == target.period_key
        assert result.tenant_id == target.tenant_id
        assert result.product_id == target.product_id

    def test_normal_sales_outbound_reversal(self) -> None:
        """정상 — sales_outbound qty=-50 → negating qty=50.0000."""
        target = _make_target_event(
            event_type="sales_outbound", qty=Decimal("-50")
        )
        result = build_reversal_negating_event(
            target_event=target,
            reason="테스트 — sign flip 음수",
            actor_id=uuid.uuid4(),
            correction_group_id=uuid.uuid4(),
            trace_id=uuid.uuid4(),
        )
        assert result.qty == Decimal("50.0000")

    def test_zero_qty_reversal(self) -> None:
        """정상 — qty=0 → negating qty=0.0000 (sign flip is trivial)."""
        target = _make_target_event(qty=Decimal("0"))
        result = build_reversal_negating_event(
            target_event=target,
            reason="테스트 — zero qty",
            actor_id=uuid.uuid4(),
            correction_group_id=uuid.uuid4(),
            trace_id=uuid.uuid4(),
        )
        assert result.qty == Decimal("0.0000")

    def test_self_reversal_negating_rejected(self) -> None:
        """reversal_negating 자체 reversal 불가 — ERROR_CODE_SELF_REVERSAL."""
        target = _make_target_event(
            event_type="reversal_negating", qty=Decimal("100")
        )
        with pytest.raises(ReversalNegatingBuildError) as exc_info:
            build_reversal_negating_event(
                target_event=target,
                reason="테스트 — self reversal",
                actor_id=uuid.uuid4(),
                correction_group_id=uuid.uuid4(),
                trace_id=uuid.uuid4(),
            )
        assert exc_info.value.error_code == ERROR_CODE_SELF_REVERSAL

    def test_self_reversal_corrected_rejected(self) -> None:
        """reversal_corrected 자체 reversal 불가 — ERROR_CODE_SELF_REVERSAL."""
        target = _make_target_event(
            event_type="reversal_corrected", qty=Decimal("100")
        )
        with pytest.raises(ReversalNegatingBuildError) as exc_info:
            build_reversal_negating_event(
                target_event=target,
                reason="테스트 — self reversal corrected",
                actor_id=uuid.uuid4(),
                correction_group_id=uuid.uuid4(),
                trace_id=uuid.uuid4(),
            )
        assert exc_info.value.error_code == ERROR_CODE_SELF_REVERSAL

    def test_empty_reason_rejected(self) -> None:
        """reason 빈 문자열 거부 — ERROR_CODE_EMPTY_REASON."""
        target = _make_target_event()
        with pytest.raises(ReversalNegatingBuildError) as exc_info:
            build_reversal_negating_event(
                target_event=target,
                reason="",
                actor_id=uuid.uuid4(),
                correction_group_id=uuid.uuid4(),
                trace_id=uuid.uuid4(),
            )
        assert exc_info.value.error_code == ERROR_CODE_EMPTY_REASON

    def test_non_uuid_actor_rejected(self) -> None:
        """actor_id non-UUID 거부."""
        target = _make_target_event()
        with pytest.raises(ReversalNegatingBuildError) as exc_info:
            build_reversal_negating_event(
                target_event=target,
                reason="테스트",
                actor_id="not-a-uuid",  # type: ignore[arg-type]
                correction_group_id=uuid.uuid4(),
                trace_id=uuid.uuid4(),
            )
        assert "actor_id must be UUID" in exc_info.value.message

    def test_qty_none_rejected(self) -> None:
        """target.qty=None 거부 — sign-negating requires non-None qty."""
        target = _make_target_event(qty=None)
        with pytest.raises(ReversalNegatingBuildError) as exc_info:
            build_reversal_negating_event(
                target_event=target,
                reason="테스트",
                actor_id=uuid.uuid4(),
                correction_group_id=uuid.uuid4(),
                trace_id=uuid.uuid4(),
            )
        # QTY_REQUIRED from AppendOnlyLedgerError path (we reuse parent's code)
        assert "qty" in exc_info.value.message.lower()


class TestValidateReversalNegatingConstraints:
    """validate_reversal_negating_constraints: opening_carried / purchase_inbound /
    closing_snapshot 모두 reversal 가능 검증 + reversal 자체 reversal 불가."""

    def test_opening_carried_reversible(self) -> None:
        """opening_carried → reversible (5-1 carry chain row)."""
        target = _make_target_event(event_type="opening_carried")
        validate_reversal_negating_constraints(target)  # no raise

    def test_purchase_inbound_reversible(self) -> None:
        """purchase_inbound → reversible (PRD §6.2 입고)."""
        target = _make_target_event(event_type="purchase_inbound")
        validate_reversal_negating_constraints(target)  # no raise

    def test_closing_snapshot_reversible(self) -> None:
        """closing_snapshot → reversible (PRD §F11.3 — 마감 후 발견된 오류)."""
        target = _make_target_event(event_type="closing_snapshot")
        validate_reversal_negating_constraints(target)  # no raise

    def test_non_reversible_event_type_rejected(self) -> None:
        """unknown event_type 거부 — ERROR_CODE_TARGET_NOT_REVERSIBLE."""
        target = _make_target_event(event_type="unknown_event_type")
        with pytest.raises(ReversalNegatingBuildError) as exc_info:
            validate_reversal_negating_constraints(target)
        assert exc_info.value.error_code == ERROR_CODE_TARGET_NOT_REVERSIBLE


class TestBankersRounding:
    """Banker's rounding parity (CR 0-4)."""

    def test_qty_half_even_rounding(self) -> None:
        """ROUND_HALF_EVEN at QTY_QUANTUM: 0.00005 → 0.0000 (banker's rounding)."""
        # 0.00005 quantized to 0.0001 with ROUND_HALF_EVEN → 0.0000
        # (0.00005 is exactly between 0.0000 and 0.0001; banker's
        # rounds to even = 0.0000)
        target = _make_target_event(qty=Decimal("0.00005"))
        result = build_reversal_negating_event(
            target_event=target,
            reason="테스트 — banker's rounding",
            actor_id=uuid.uuid4(),
            correction_group_id=uuid.uuid4(),
            trace_id=uuid.uuid4(),
        )
        # Sign flip → -0.00005 → quantized to -0.0000
        assert result.qty == Decimal("0.0000") or result.qty == Decimal("-0.0000")

    def test_qty_5_decimal_places_quantized(self) -> None:
        """5+ 자릿수 값 → NUMERIC(18,4) quantization."""
        target = _make_target_event(qty=Decimal("123.45678"))
        result = build_reversal_negating_event(
            target_event=target,
            reason="테스트 — 5+ 자릿수",
            actor_id=uuid.uuid4(),
            correction_group_id=uuid.uuid4(),
            trace_id=uuid.uuid4(),
        )
        # ROUND_HALF_EVEN of 123.45678 → 123.4568 (8 is even)
        # Sign flip → -123.4568
        assert result.qty == Decimal("-123.4568")


class TestKoreanConstants:
    """M11_AUTHORIZE_KO constant parity (AD-15 §11)."""

    def test_m11_authorize_ko_value(self) -> None:
        """M11_AUTHORIZE_KO = 'M11 모듈 권한 OK' (AD-15 §11 SSOT)."""
        assert M11_AUTHORIZE_KO == "M11 모듈 권한 OK"

    def test_reversible_target_event_types_count(self) -> None:
        """REVERSIBLE_TARGET_EVENT_TYPES has 9 entries (excluding reversal_* itself)."""
        assert len(REVERSIBLE_TARGET_EVENT_TYPES) == 9
        assert "reversal_negating" not in REVERSIBLE_TARGET_EVENT_TYPES
        assert "reversal_corrected" not in REVERSIBLE_TARGET_EVENT_TYPES
