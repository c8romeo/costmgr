"""tests.services.m11_close.test_reversal_authorization — Story 11.1 pure kernel #3.

6 cases per AC #8 spec:
- authorize_reversal (3): capability_granted / period_status 가드 / event_type reversal 가능 검증
- M11_REJECT_KO constants (3)
"""

from __future__ import annotations

import uuid

import pytest

from packages.services.m4_inventory.ledger import InventoryLedgerEvent
from packages.services.m11_close.reversal_authorization import (
    ERROR_CODE_INVALID_PERIOD_STATUS,
    ERROR_CODE_NO_CAPABILITY,
    M11_AUTHORIZE_KO,
    M11_REJECT_LOCKED_KO,
    M11_REJECT_NO_CAPABILITY_KO,
    M11_REJECT_TARGET_NOT_REVERSIBLE_KO,
    ReversalAuthorizationError,
    authorize_reversal,
)


def _make_target_event(
    *, event_type: str = "purchase_inbound"
) -> InventoryLedgerEvent:
    return InventoryLedgerEvent(
        event_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        product_id=uuid.uuid4(),
        period_key="2026-08",
        event_type=event_type,
        qty=None,  # authorization doesn't need qty
        trace_id=uuid.uuid4(),
        reverses_event_id=None,
        correction_group_id=None,
        payload={"source": "monthly_input"},
    )


class TestAuthorizeReversal:
    """authorize_reversal — capability + period_status + event_type 3-axis gate."""

    def test_authorized_when_all_gates_pass(self) -> None:
        """capability_granted=True + period_status='closed' + reversible event → authorized."""
        result = authorize_reversal(
            tenant_id=uuid.uuid4(),
            target_event=_make_target_event(event_type="purchase_inbound"),
            actor_id=uuid.uuid4(),
            period_status="closed",
            capability_granted=True,
        )
        assert result.authorized is True
        assert result.reject_reason_ko is None
        assert result.period_status == "closed"
        assert result.capability_granted is True
        assert result.target_reversible is True

    def test_no_capability_rejected(self) -> None:
        """capability_granted=False → ERROR_CODE_NO_CAPABILITY."""
        result = authorize_reversal(
            tenant_id=uuid.uuid4(),
            target_event=_make_target_event(),
            actor_id=uuid.uuid4(),
            period_status="closed",
            capability_granted=False,
        )
        assert result.authorized is False
        assert result.reject_reason_ko == M11_REJECT_NO_CAPABILITY_KO
        assert result.capability_granted is False

    def test_locked_period_rejected(self) -> None:
        """period_status='locked' → M11_REJECT_LOCKED_KO."""
        result = authorize_reversal(
            tenant_id=uuid.uuid4(),
            target_event=_make_target_event(),
            actor_id=uuid.uuid4(),
            period_status="locked",
            capability_granted=True,
        )
        assert result.authorized is False
        assert result.reject_reason_ko == M11_REJECT_LOCKED_KO

    def test_non_reversible_event_type_rejected(self) -> None:
        """event_type='reversal_negating' → M11_REJECT_TARGET_NOT_REVERSIBLE_KO (self-reversal)."""
        result = authorize_reversal(
            tenant_id=uuid.uuid4(),
            target_event=_make_target_event(event_type="reversal_negating"),
            actor_id=uuid.uuid4(),
            period_status="closed",
            capability_granted=True,
        )
        assert result.authorized is False
        assert result.reject_reason_ko == M11_REJECT_TARGET_NOT_REVERSIBLE_KO
        assert result.target_reversible is False


class TestErrorGuards:
    """authorize_reversal error guards."""

    def test_unknown_period_status_raises(self) -> None:
        """period_status='unknown' (not in known set) raises ReversalAuthorizationError."""
        with pytest.raises(ReversalAuthorizationError) as exc_info:
            authorize_reversal(
                tenant_id=uuid.uuid4(),
                target_event=_make_target_event(),
                actor_id=uuid.uuid4(),
                period_status="unknown",
                capability_granted=True,
            )
        assert exc_info.value.error_code == ERROR_CODE_INVALID_PERIOD_STATUS

    def test_non_uuid_actor_raises(self) -> None:
        """actor_id non-UUID raises ReversalAuthorizationError."""
        with pytest.raises(ReversalAuthorizationError):
            authorize_reversal(
                tenant_id=uuid.uuid4(),
                target_event=_make_target_event(),
                actor_id="not-a-uuid",  # type: ignore[arg-type]
                period_status="closed",
                capability_granted=True,
            )


class TestKoreanConstants:
    """M11_REJECT_KO constants parity (AD-15 §11)."""

    def test_m11_authorize_ko(self) -> None:
        """M11_AUTHORIZE_KO = 'M11 모듈 권한 OK'."""
        assert M11_AUTHORIZE_KO == "M11 모듈 권한 OK"

    def test_m11_reject_locked_ko(self) -> None:
        """M11_REJECT_LOCKED_KO = '잠긴 기간 — 역분개 불가'."""
        assert M11_REJECT_LOCKED_KO == "잠긴 기간 — 역분개 불가"

    def test_m11_reject_no_capability_ko(self) -> None:
        """M11_REJECT_NO_CAPABILITY_KO = '역분개 권한 미보유'."""
        assert M11_REJECT_NO_CAPABILITY_KO == "역분개 권한 미보유"
