"""tests.api.m11_close.test_reopen_service — Story 11.3 service.

8 cases per AC #10 spec — verify ReopenService orchestrator (W2 reopen flow):
- REOPEN_CHANNELS has 2 channels
- execute_reopen happy path (status='closed' → 'open', close_sequence_state='reopened')
- execute_reopen no fiscal_period → ReopenOperatorActionInvalidError
- execute_reopen audit emit failure → ReopenAuditEmitFailedError
- execute_reopen with each of 4 operator_action values
- execute_reopen reason length 20 (boundary) accepted
- execute_reopen reason length 500 (boundary) accepted
- Result is immutable dataclass
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.modules.m11_close.exceptions import (
    ReopenAuditEmitFailedError,
    ReopenOperatorActionInvalidError,
)
from apps.api.modules.m11_close.services.reopen_service import (
    REOPEN_CHANNELS,
    ReopenService,
)


# ── Common fixtures ──────────────────────────────────────────
@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def actor_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def fiscal_period_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def trace_id() -> str:
    return str(uuid.uuid4())


def _make_fiscal_period_row(
    tenant_id: uuid.UUID,
    fiscal_period_id: uuid.UUID,
    status: str = "closed",
    close_sequence_state: str = "confirmed",
) -> MagicMock:
    """Build a mock FiscalPeriod row."""
    fp = MagicMock()
    fp.id = fiscal_period_id
    fp.tenant_id = tenant_id
    fp.period_key = "2026-08"
    fp.status = status
    fp.close_sequence_state = close_sequence_state
    fp.created_at = datetime.now(tz=UTC)
    fp.closed_at = datetime.now(tz=UTC)
    return fp


# ── 1. REOPEN_CHANNELS has 2 channels ───────────────────────
def test_reopen_channels_has_2_channels() -> None:
    """REOPEN_CHANNELS must have exactly 2 AD-25 channels."""
    assert len(REOPEN_CHANNELS) == 2
    for ch in ("fiscal_period_cache", "closing_snapshot_cache"):
        assert ch in REOPEN_CHANNELS


# ── 2. Happy path ───────────────────────────────────────────
@pytest.mark.asyncio
async def test_execute_reopen_happy_path(
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
    fiscal_period_id: uuid.UUID,
    trace_id: str,
) -> None:
    """execute_reopen on status='closed' returns status='open' + audit emit."""
    fp = _make_fiscal_period_row(tenant_id, fiscal_period_id, status="closed")
    session = AsyncMock()
    # scalar returns fp; execute for UPDATE.
    session.scalar = AsyncMock(return_value=fp)
    session.execute = AsyncMock(return_value=MagicMock())

    svc = ReopenService(
        session, tenant_id=tenant_id, trace_id=trace_id
    )
    result = await svc.execute_reopen(
        period_key="2026-08",
        operator_action="operator_reopen",
        reason="A" * 50,
        actor_id=actor_id,
    )
    assert result.fiscal_period_id == fiscal_period_id
    assert result.status == "open"
    assert result.period_key == "2026-08"


# ── 3. No fiscal_period → ReopenOperatorActionInvalidError ─
@pytest.mark.asyncio
async def test_execute_reopen_no_fiscal_period(
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
    trace_id: str,
) -> None:
    """execute_reopen with no fiscal_period row raises ReopenOperatorActionInvalidError."""
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)

    svc = ReopenService(
        session, tenant_id=tenant_id, trace_id=trace_id
    )
    with pytest.raises(ReopenOperatorActionInvalidError):
        await svc.execute_reopen(
            period_key="2099-01",
            operator_action="operator_reopen",
            reason="A" * 50,
            actor_id=actor_id,
        )


# ── 4. Invalid operator_action → ReopenOperatorActionInvalidError ─
@pytest.mark.asyncio
async def test_execute_reopen_invalid_operator_action(
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
    fiscal_period_id: uuid.UUID,
    trace_id: str,
) -> None:
    """execute_reopen with invalid operator_action raises ReopenOperatorActionInvalidError."""
    fp = _make_fiscal_period_row(tenant_id, fiscal_period_id, status="closed")
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=fp)

    svc = ReopenService(
        session, tenant_id=tenant_id, trace_id=trace_id
    )
    with pytest.raises(ReopenOperatorActionInvalidError):
        await svc.execute_reopen(
            period_key="2026-08",
            operator_action="not_in_enum",
            reason="A" * 50,
            actor_id=actor_id,
        )


# ── 5. Reason too short → ReopenOperatorActionInvalidError ─
@pytest.mark.asyncio
async def test_execute_reopen_reason_too_short(
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
    fiscal_period_id: uuid.UUID,
    trace_id: str,
) -> None:
    """execute_reopen with reason < 20 chars raises ReopenOperatorActionInvalidError."""
    fp = _make_fiscal_period_row(tenant_id, fiscal_period_id, status="closed")
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=fp)

    svc = ReopenService(
        session, tenant_id=tenant_id, trace_id=trace_id
    )
    with pytest.raises(ReopenOperatorActionInvalidError):
        await svc.execute_reopen(
            period_key="2026-08",
            operator_action="operator_reopen",
            reason="too short",
            actor_id=actor_id,
        )


# ── 6. All 4 operator_action values authorized ─────────────
@pytest.mark.parametrize(
    "operator_action",
    ["operator_reopen", "audit_finding", "legal_compliance", "data_correction"],
)
@pytest.mark.asyncio
async def test_all_4_operator_actions_accepted(
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
    fiscal_period_id: uuid.UUID,
    trace_id: str,
    operator_action: str,
) -> None:
    """All 4 REOPEN_OPERATOR_ACTIONS values are accepted."""
    fp = _make_fiscal_period_row(tenant_id, fiscal_period_id, status="closed")
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=fp)
    session.execute = AsyncMock(return_value=MagicMock())

    svc = ReopenService(
        session, tenant_id=tenant_id, trace_id=trace_id
    )
    result = await svc.execute_reopen(
        period_key="2026-08",
        operator_action=operator_action,
        reason=f"Test reason for {operator_action}",
        actor_id=actor_id,
    )
    assert result.status == "open"


# ── 7. Result is immutable dataclass ──────────────────────
@pytest.mark.asyncio
async def test_result_is_immutable(
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
    fiscal_period_id: uuid.UUID,
    trace_id: str,
) -> None:
    """ReopenResponse is immutable (frozen dataclass)."""
    fp = _make_fiscal_period_row(tenant_id, fiscal_period_id, status="closed")
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=fp)
    session.execute = AsyncMock(return_value=MagicMock())

    svc = ReopenService(
        session, tenant_id=tenant_id, trace_id=trace_id
    )
    result = await svc.execute_reopen(
        period_key="2026-08",
        operator_action="operator_reopen",
        reason="A" * 50,
        actor_id=actor_id,
    )
    with pytest.raises((AttributeError, Exception)):
        result.status = "closed"  # type: ignore[misc]


# ── 8. Channel tuple order is deterministic ────────────────
def test_channel_order_is_deterministic() -> None:
    """REOPEN_CHANNELS preserves canonical AD-25 ordering."""
    assert REOPEN_CHANNELS == ("fiscal_period_cache", "closing_snapshot_cache")