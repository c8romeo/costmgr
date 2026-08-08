"""tests.services.m11_close.test_reversal_authorization_fiscal_period_extension — Story 11.2 dual guard.

~10 cases per AC #6 spec:
- fiscal_periods.status='closed' dispatch (AD-6 close lock PRIMARY guard)
- monthly_input_periods.status='closed' + fiscal_periods.status='open' → allowed
- monthly_input_periods.status='locked' → rejected (11-1 dispatch preserved)
- fiscal_periods.status in ('closing'/'closed'/'reversed') → rejected (11-2 NEW dispatch)
- REVERSIBLE_TARGET_EVENT_TYPES cross-product
- error code + reject_reason_ko Korean SSOT
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from packages.services.m4_inventory.ledger import InventoryLedgerEvent
from packages.services.m11_close.reversal_authorization import (
    FISCAL_PERIOD_STATUS_ALLOWED,
    FISCAL_PERIOD_STATUS_REJECTED,
    M11_REJECT_LOCKED_KO,
    PERIOD_STATUS_ALLOWED,
    PERIOD_STATUS_REJECTED,
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
        qty=Decimal("100.0000"),
        trace_id=uuid.uuid4(),
        reverses_event_id=None,
        correction_group_id=None,
        payload={},
    )


# ── Module surface ──────────────────────────────────────────
def test_fiscal_period_status_constants() -> None:
    assert frozenset({"open"}) == FISCAL_PERIOD_STATUS_ALLOWED
    assert frozenset(
        {"closing", "closed", "reversed"}
    ) == FISCAL_PERIOD_STATUS_REJECTED


def test_period_status_constants_preserved_for_backward_compat() -> None:
    """11-1 PERIO_DEFAULT_STATUS_ALLOWED/REJECTED preserved."""
    assert frozenset({"open", "closed"}) == PERIOD_STATUS_ALLOWED
    assert frozenset({"locked"}) == PERIOD_STATUS_REJECTED


# ── Authorized: both gates open ─────────────────────────────
def test_authorized_when_both_period_and_fiscal_open() -> None:
    """Both monthly_input_periods.status='open' AND fiscal_periods.status='open' → OK."""
    result = authorize_reversal(
        tenant_id=uuid.uuid4(),
        target_event=_make_target_event(event_type="purchase_inbound"),
        actor_id=uuid.uuid4(),
        period_status="open",
        capability_granted=True,
        fiscal_period_status="open",
    )
    assert result.authorized is True
    assert result.reject_reason_ko is None
    assert result.fiscal_period_status == "open"


# ── Authorized: monthly_input_periods.status='closed' + fiscal_periods.status='open' (11-1 compat) ──
def test_authorized_when_monthly_closed_and_fiscal_open() -> None:
    """monthly_input_periods.status='closed' but fiscal_periods.status='open' → OK.

    11-1 wire allowed reversal on monthly_input_periods.status='closed';
    11-2 adds fiscal_periods.status gate (still 'open' in this case).
    """
    result = authorize_reversal(
        tenant_id=uuid.uuid4(),
        target_event=_make_target_event(event_type="purchase_inbound"),
        actor_id=uuid.uuid4(),
        period_status="closed",
        capability_granted=True,
        fiscal_period_status="open",
    )
    assert result.authorized is True
    assert result.fiscal_period_status == "open"


# ── Rejected: fiscal_periods.status='closing' ───────────────
def test_rejected_when_fiscal_period_status_is_closing() -> None:
    """fiscal_periods.status='closing' → reject (4-stage verification in progress)."""
    result = authorize_reversal(
        tenant_id=uuid.uuid4(),
        target_event=_make_target_event(event_type="purchase_inbound"),
        actor_id=uuid.uuid4(),
        period_status="open",
        capability_granted=True,
        fiscal_period_status="closing",
    )
    assert result.authorized is False
    assert result.reject_reason_ko == M11_REJECT_LOCKED_KO
    assert result.fiscal_period_status == "closing"


# ── Rejected: fiscal_periods.status='closed' (AD-6 PRIMARY) ─
def test_rejected_when_fiscal_period_status_is_closed() -> None:
    """fiscal_periods.status='closed' (4-stage confirmed) → reject.

    This is the AD-6 INSERT 거부 guard mirrored at authorization layer.
    Once fiscal_periods reaches 'closed' (close sequence confirmed),
    no further reversals are authorized through this entrypoint —
    they must use dedicated AD-22 reversal endpoints (which
    themselves gate on fiscal_periods.status).
    """
    result = authorize_reversal(
        tenant_id=uuid.uuid4(),
        target_event=_make_target_event(event_type="purchase_inbound"),
        actor_id=uuid.uuid4(),
        period_status="closed",
        capability_granted=True,
        fiscal_period_status="closed",
    )
    assert result.authorized is False
    assert result.reject_reason_ko == M11_REJECT_LOCKED_KO
    assert result.fiscal_period_status == "closed"


# ── Rejected: fiscal_periods.status='reversed' ──────────────
def test_rejected_when_fiscal_period_status_is_reversed() -> None:
    """fiscal_periods.status='reversed' (reopen flow) → reject."""
    result = authorize_reversal(
        tenant_id=uuid.uuid4(),
        target_event=_make_target_event(event_type="purchase_inbound"),
        actor_id=uuid.uuid4(),
        period_status="open",
        capability_granted=True,
        fiscal_period_status="reversed",
    )
    assert result.authorized is False
    assert result.reject_reason_ko == M11_REJECT_LOCKED_KO


# ── Rejected: monthly_input_periods.status='locked' (11-1 dispatch) ─
def test_rejected_when_monthly_period_status_is_locked() -> None:
    """11-1 dispatch preserved: monthly_input_periods.status='locked' → reject."""
    result = authorize_reversal(
        tenant_id=uuid.uuid4(),
        target_event=_make_target_event(event_type="purchase_inbound"),
        actor_id=uuid.uuid4(),
        period_status="locked",
        capability_granted=True,
        fiscal_period_status="open",
    )
    assert result.authorized is False
    assert result.reject_reason_ko == M11_REJECT_LOCKED_KO


# ── Dual rejection: BOTH status locks ───────────────────────
def test_rejected_when_both_status_locks() -> None:
    """monthly='locked' + fiscal='closed' → reject (either gate suffices)."""
    result = authorize_reversal(
        tenant_id=uuid.uuid4(),
        target_event=_make_target_event(event_type="purchase_inbound"),
        actor_id=uuid.uuid4(),
        period_status="locked",
        capability_granted=True,
        fiscal_period_status="closed",
    )
    assert result.authorized is False
    assert result.reject_reason_ko == M11_REJECT_LOCKED_KO


# ── Invalid input shape ────────────────────────────────────
def test_invalid_fiscal_period_status_raises_error() -> None:
    """fiscal_period_status='unknown' raises ReversalAuthorizationError."""
    with pytest.raises(ReversalAuthorizationError) as exc_info:
        authorize_reversal(
            tenant_id=uuid.uuid4(),
            target_event=_make_target_event(),
            actor_id=uuid.uuid4(),
            period_status="open",
            capability_granted=True,
            fiscal_period_status="bogus",
        )
    assert exc_info.value.error_code == "INVALID_PERIOD_STATUS"


def test_default_fiscal_period_status_is_open() -> None:
    """fiscal_period_status defaults to 'open' for backward compat."""
    result = authorize_reversal(
        tenant_id=uuid.uuid4(),
        target_event=_make_target_event(event_type="purchase_inbound"),
        actor_id=uuid.uuid4(),
        period_status="open",
        capability_granted=True,
    )
    assert result.authorized is True
    assert result.fiscal_period_status == "open"


# ── REVERSIBLE_TARGET_EVENT_TYPES cross-product ────────────
def test_reversal_negating_target_allowed_when_both_gates_open() -> None:
    """reversal_negating event type (re-reversal attempt) allowed when both gates open."""
    result = authorize_reversal(
        tenant_id=uuid.uuid4(),
        target_event=_make_target_event(event_type="reversal_negating"),
        actor_id=uuid.uuid4(),
        period_status="open",
        capability_granted=True,
        fiscal_period_status="open",
    )
    assert result.authorized is True


def test_non_reversible_target_rejected_with_specific_reason() -> None:
    """closing_snapshot event_type → TARGET_NOT_REVERSIBLE reject (Korean SSOT)."""
    result = authorize_reversal(
        tenant_id=uuid.uuid4(),
        target_event=_make_target_event(event_type="closing_snapshot"),
        actor_id=uuid.uuid4(),
        period_status="open",
        capability_granted=True,
        fiscal_period_status="open",
    )
    assert result.authorized is False
    assert result.target_reversible is False
    assert "이벤트 타입은 역분개 대상이 아닙니다" in (result.reject_reason_ko or "")


def test_capability_denied_takes_precedence_over_fiscal_guard() -> None:
    """capability_granted=False → reject before fiscal_period_status check."""
    result = authorize_reversal(
        tenant_id=uuid.uuid4(),
        target_event=_make_target_event(event_type="purchase_inbound"),
        actor_id=uuid.uuid4(),
        period_status="open",
        capability_granted=False,
        fiscal_period_status="open",
    )
    assert result.authorized is False
    assert "권한" in (result.reject_reason_ko or "")


def test_authorization_result_namedtuple_includes_fiscal_period_status() -> None:
    """ReversalAuthorizationResult carries fiscal_period_status field (11-2 NEW)."""
    result = authorize_reversal(
        tenant_id=uuid.uuid4(),
        target_event=_make_target_event(event_type="purchase_inbound"),
        actor_id=uuid.uuid4(),
        period_status="open",
        capability_granted=True,
        fiscal_period_status="closed",
    )
    # Even when rejected, the result preserves the input fiscal_period_status.
    assert result.fiscal_period_status == "closed"
