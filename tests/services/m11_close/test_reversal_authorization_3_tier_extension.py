"""tests.services.m11_close.test_reversal_authorization_3_tier_extension — Story 11.3.

Tests the Story 11.3 3rd-tier guard extension to the reversal_authorization
kernel (fiscal_period_snapshots.state='committed' gate).

10 cases:
- 3rd-tier guard constants stable
- state='committed' (default + explicit) → authorized
- state='draft' → rejected with M11_REJECT_SNAPSHOT_NOT_COMMITTED_KO
- state='verified' → rejected
- state='reversed' → rejected
- invalid state raises ReversalAuthorizationError
- Result NamedTuple has snapshot_state field
- Default value preserves 11-1/11-2 backward compatibility
- Korean SSOT constants
"""

from __future__ import annotations

import uuid

import pytest

from packages.services.m4_inventory.ledger import InventoryLedgerEvent
from packages.services.m11_close.reversal_authorization import (
    ERROR_CODE_INVALID_SNAPSHOT_STATE,
    M11_REJECT_SNAPSHOT_NOT_COMMITTED_KO,
    SNAPSHOT_STATE_ALLOWED,
    SNAPSHOT_STATE_REJECTED,
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
        qty=None,
        trace_id=uuid.uuid4(),
        reverses_event_id=None,
        correction_group_id=None,
        payload={},
    )


# ── 1. Constants ────────────────────────────────────────────
def test_snapshot_state_allowed_is_committed_only() -> None:
    """SNAPSHOT_STATE_ALLOWED = {committed} only (11-3 3rd-tier guard)."""
    assert SNAPSHOT_STATE_ALLOWED == frozenset({"committed"})


def test_snapshot_state_rejected_excludes_committed() -> None:
    """SNAPSHOT_STATE_REJECTED = {draft, verified, reversed}."""
    assert SNAPSHOT_STATE_REJECTED == frozenset(
        {"draft", "verified", "reversed"}
    )


def test_korean_ssot_snapshot_rejection() -> None:
    """Korean SSOT constant for snapshot state rejection."""
    assert M11_REJECT_SNAPSHOT_NOT_COMMITTED_KO == (
        "스냅샷이 커밋 상태가 아닙니다 — 영구화 역분개 불가"
    )


# ── 2. Default snapshot_state preserves backward compatibility ─
def test_default_snapshot_state_is_committed() -> None:
    """authorize_reversal with no snapshot_state defaults to 'committed'."""
    result = authorize_reversal(
        tenant_id=uuid.uuid4(),
        target_event=_make_target_event(),
        actor_id=uuid.uuid4(),
        period_status="closed",
        capability_granted=True,
        fiscal_period_status="closed",
    )
    assert result.authorized is True
    assert result.snapshot_state == "committed"


# ── 3. Valid state='committed' (explicit) ───────────────────
def test_explicit_committed_state_authorized() -> None:
    """snapshot_state='committed' (explicit) → authorized."""
    result = authorize_reversal(
        tenant_id=uuid.uuid4(),
        target_event=_make_target_event(),
        actor_id=uuid.uuid4(),
        period_status="closed",
        capability_granted=True,
        fiscal_period_status="closed",
        snapshot_state="committed",
    )
    assert result.authorized is True
    assert result.snapshot_state == "committed"


# ── 4-6. State rejections ──────────────────────────────────
@pytest.mark.parametrize(
    "rejected_state",
    ["draft", "verified", "reversed"],
)
def test_non_committed_states_rejected(rejected_state: str) -> None:
    """snapshot_state in {draft, verified, reversed} → rejected with snapshot KOR."""
    result = authorize_reversal(
        tenant_id=uuid.uuid4(),
        target_event=_make_target_event(),
        actor_id=uuid.uuid4(),
        period_status="closed",
        capability_granted=True,
        fiscal_period_status="closed",
        snapshot_state=rejected_state,
    )
    assert result.authorized is False
    assert result.reject_reason_ko == M11_REJECT_SNAPSHOT_NOT_COMMITTED_KO
    assert result.snapshot_state == rejected_state


# ── 7. Invalid snapshot_state raises ─────────────────────────
def test_invalid_snapshot_state_raises() -> None:
    """snapshot_state='bogus' raises ReversalAuthorizationError."""
    with pytest.raises(ReversalAuthorizationError) as exc_info:
        authorize_reversal(
            tenant_id=uuid.uuid4(),
            target_event=_make_target_event(),
            actor_id=uuid.uuid4(),
            period_status="closed",
            capability_granted=True,
            fiscal_period_status="closed",
            snapshot_state="bogus",
        )
    assert exc_info.value.error_code == ERROR_CODE_INVALID_SNAPSHOT_STATE


# ── 8. Result NamedTuple has snapshot_state field ───────────
def test_result_namedtuple_has_snapshot_state_field() -> None:
    """ReversalAuthorizationResult exposes snapshot_state field (11-3 NEW)."""
    result = authorize_reversal(
        tenant_id=uuid.uuid4(),
        target_event=_make_target_event(),
        actor_id=uuid.uuid4(),
        period_status="closed",
        capability_granted=True,
        fiscal_period_status="closed",
        snapshot_state="committed",
    )
    assert hasattr(result, "snapshot_state")
    assert result.snapshot_state == "committed"


# ── 9. snapshot_state check fires AFTER fiscal_period_status check ─
def test_snapshot_state_check_fires_after_fiscal_period_check() -> None:
    """fiscal_period_status='open' rejects BEFORE snapshot_state is checked."""
    result = authorize_reversal(
        tenant_id=uuid.uuid4(),
        target_event=_make_target_event(),
        actor_id=uuid.uuid4(),
        period_status="closed",
        capability_granted=True,
        fiscal_period_status="open",  # rejected at 2nd-tier gate
        snapshot_state="committed",  # valid
    )
    assert result.authorized is False
    # Rejection comes from fiscal_period gate (M11_REJECT_LOCKED_KO),
    # NOT from snapshot gate (M11_REJECT_SNAPSHOT_NOT_COMMITTED_KO).
    assert result.reject_reason_ko != M11_REJECT_SNAPSHOT_NOT_COMMITTED_KO


# ── 10. Error code for invalid snapshot state ───────────────
def test_error_code_invalid_snapshot_state() -> None:
    """ERROR_CODE_INVALID_SNAPSHOT_STATE = 'INVALID_SNAPSHOT_STATE'."""
    assert ERROR_CODE_INVALID_SNAPSHOT_STATE == "INVALID_SNAPSHOT_STATE"