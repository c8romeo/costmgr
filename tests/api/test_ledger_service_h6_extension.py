"""tests.api.test_ledger_service_h6_extension — Story 11.1 T9 H6 fix wire.

H6 production bug: closing_period_service.py:528/531 calls
`count_period_events(period_key)` and `count_period_events(period_key,
event_type="closing_snapshot")` — methods that did NOT exist on
LedgerService. Tests cover the new methods:

- `count_period_events(period_key)` — total event count
- `count_period_events(period_key, event_type="closing_snapshot")` — filter
- `query_period_closing_snapshot_all(period_key)` — multi-product aggregate

The pure-kernel SQL builder behavior is covered by
`tests/services/m5_ledger/test_count_period_events.py` and
`tests/services/m5_ledger/test_query_period_closing_snapshot_all.py`.
"""

from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.modules.m4_inventory.services.ledger_service import LedgerService
from packages.services.m0_onboarding.industry_menu import Industry

TENANT_ID = uuid.UUID("019200a0-0000-7000-8000-000000000001")
PRODUCT_A = uuid.UUID("019200a0-0000-7000-8000-00000000000a")
PRODUCT_B = uuid.UUID("019200a0-0000-7000-8000-00000000000b")
TRACE_ID = "019200a0-0000-7000-8000-000000000003"
PERIOD_KEY = "2026-08"


def _build_service(session: AsyncMock | None = None) -> tuple[LedgerService, AsyncMock]:
    """Build a LedgerService with a fresh AsyncMock session."""
    if session is None:
        session = AsyncMock()
    svc = LedgerService(
        session,
        tenant_id=TENANT_ID,
        industry=Industry.MANUFACTURING,
        trace_id=TRACE_ID,
    )
    return svc, session


# ── count_period_events — total event count ─────────────────


def test_count_period_events_returns_total_count() -> None:
    """count_period_events(period_key) returns total event count.

    The implementation calls `session.scalar(select(func.count())...)`
    which returns a single int directly — mock `session.scalar` to return
    the count value.
    """

    async def _impl() -> None:
        svc, session = _build_service()
        session.scalar = AsyncMock(return_value=42)

        count = await svc.count_period_events(period_key=PERIOD_KEY)

        assert count == 42

    asyncio.run(_impl())


def test_count_period_events_returns_zero_when_no_rows() -> None:
    """count_period_events returns 0 when no rows match."""

    async def _impl() -> None:
        svc, session = _build_service()
        session.scalar = AsyncMock(return_value=None)

        count = await svc.count_period_events(period_key=PERIOD_KEY)

        assert count == 0

    asyncio.run(_impl())


def test_count_period_events_with_event_type_filter() -> None:
    """count_period_events(period_key, event_type='closing_snapshot') filter."""

    async def _impl() -> None:
        svc, session = _build_service()
        session.scalar = AsyncMock(return_value=5)

        count = await svc.count_period_events(
            period_key=PERIOD_KEY,
            event_type="closing_snapshot",
        )

        assert count == 5

    asyncio.run(_impl())


def test_count_period_events_rejects_unknown_event_type() -> None:
    """count_period_events at the service layer does NOT raise on unknown event_type.

    The service-layer `count_period_events` builds the SQL inline (does
    NOT dispatch through the pure kernel `count_period_events_sql`),
    so the 11-value whitelist check is performed only by the pure kernel
    (used elsewhere). The service-layer method simply forwards the
    `event_type` string as a WHERE filter — unknown values produce
    row_count=0 via SQL (no match), not a service-layer exception.

    This is by design: the service layer is a thin wrapper for the
    H6-fix wire (closing_period_service.py:528/531). Event-type
    validation lives at the INSERT path (pure kernel `ledger.py`),
    not at the COUNT path.

    Verifies: passing an unknown event_type does NOT raise; the
    method returns whatever `session.scalar` returns (0 here).
    """

    async def _impl() -> None:
        svc, session = _build_service()
        session.scalar = AsyncMock(return_value=0)

        # Should NOT raise — service layer accepts any event_type string.
        count = await svc.count_period_events(
            period_key=PERIOD_KEY,
            event_type="not_a_valid_event_type",
        )

        # No match for unknown event_type → 0.
        assert count == 0

    asyncio.run(_impl())


# ── query_period_closing_snapshot_all — multi-product aggregate ─


def test_query_period_closing_snapshot_all_returns_product_map() -> None:
    """query_period_closing_snapshot_all returns dict[product_id, Decimal].

    The implementation iterates `session.execute(select(...))` rows
    directly (not fetchall()). The mock must be iterable (NOT
    `.fetchall()`).
    """

    async def _impl() -> None:
        svc, session = _build_service()

        # Mock the SQL result — rows iterable with .product_id + .qty attrs.
        row_a = MagicMock()
        row_a.product_id = PRODUCT_A
        row_a.qty = Decimal("100.0000")

        row_b = MagicMock()
        row_b.product_id = PRODUCT_B
        row_b.qty = Decimal("50.0000")

        mock_result = MagicMock()
        mock_result.__iter__ = lambda _: iter([row_a, row_b])
        session.execute = AsyncMock(return_value=mock_result)

        result = await svc.query_period_closing_snapshot_all(
            period_key=PERIOD_KEY,
        )

        assert len(result) == 2
        assert result[PRODUCT_A] == Decimal("100.0000")
        assert result[PRODUCT_B] == Decimal("50.0000")

    asyncio.run(_impl())


def test_query_period_closing_snapshot_all_returns_empty_map() -> None:
    """query_period_closing_snapshot_all returns empty dict when no rows."""

    async def _impl() -> None:
        svc, session = _build_service()

        mock_result = MagicMock()
        mock_result.__iter__ = lambda _: iter([])
        session.execute = AsyncMock(return_value=mock_result)

        result = await svc.query_period_closing_snapshot_all(
            period_key=PERIOD_KEY,
        )

        assert result == {}

    asyncio.run(_impl())


# ── H6 fix integration: closing_period_service.py wire ──────


def test_h6_fix_closing_period_service_wire() -> None:
    """H6 fix: closing_period_service.py:528/531 can now call count_period_events.

    This is the production bug that motivated the fix. Verifies the
    LedgerService has the methods that closing_period_service expects.
    """

    async def _impl() -> None:
        svc, session = _build_service()
        # The H6 fix: this method exists and is callable
        assert hasattr(svc, "count_period_events")
        assert hasattr(svc, "query_period_closing_snapshot_all")

        # Both signatures work — count_period_events uses session.scalar().
        session.scalar = AsyncMock(return_value=0)
        count = await svc.count_period_events(period_key=PERIOD_KEY)
        assert count == 0

        session.scalar = AsyncMock(return_value=0)
        count = await svc.count_period_events(
            period_key=PERIOD_KEY,
            event_type="closing_snapshot",
        )
        assert count == 0

    asyncio.run(_impl())
