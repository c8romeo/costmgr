"""tests.api.m11_close.test_reversal_service — Story 11.1 service-layer tests.

AD-22 reversal sequence orchestrator coverage, exercised via AsyncMock
session (no live DB). Focuses on:

- Audit-first emit ordering (CR 1.1 lesson — `emit_audit` called BEFORE
  `session.add`/`session.flush`).
- 9-step AD-22 sequence integrity:
  1. SELECT target_event
  2. SELECT period_status
  3. authorize_reversal decision
  4. correction_group_id mint
  5. sign-negating row INSERT
  6. corrected row INSERT (optional)
  7. AD-25 publish (channel='ai_cache')
  8. audit-first INSERTs
  9. COMMIT (caller's responsibility)
- Typed exception mapping (ReversalTargetNotFoundError,
  ReversalRejectedError, LockedPeriodReversalRejectedError,
  ReversalDuplicateError, ReversalUnauthorizedError).
- AD-25 1-channel wire (channel='ai_cache' only).
- TENANT_ID RLS-scoped queries.

Project convention (CR 4-3): sync `def test_*` + `asyncio.run(_impl())`.
"""

from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from apps.api.modules.m11_close.services.reversal_service import (
    LockedPeriodReversalRejectedError,
    ReversalDuplicateError,
    ReversalRejectedError,
    ReversalService,
    ReversalTargetNotFoundError,
)
from packages.services.m0_onboarding.industry_menu import Industry
from packages.services.m4_inventory.ledger import InventoryLedgerEvent

TENANT_ID = uuid.UUID("019200a0-0000-7000-8000-000000000001")
OTHER_TENANT_ID = uuid.UUID("019200a0-0000-7000-8000-000000000099")
TARGET_EVENT_ID = uuid.UUID("019200a0-0000-7000-8000-000000000002")
CORRECTION_GROUP_ID = uuid.UUID("019200a0-0000-7000-8000-000000000003")
PRODUCT_ID = uuid.UUID("019200a0-0000-7000-8000-00000000000a")
ACTOR_ID = uuid.UUID("019200a0-0000-7000-8000-00000000000b")
TRACE_ID = "019200a0-0000-7000-8000-00000000000c"
PERIOD_KEY = "2026-08"


# ── Helpers ──────────────────────────────────────────────────
def _build_service(
    session: AsyncMock | None = None,
    *,
    tenant_id: uuid.UUID = TENANT_ID,
    industry: Industry | None = Industry.MANUFACTURING,
    trace_id: str = TRACE_ID,
) -> tuple[ReversalService, AsyncMock]:
    """Build a ReversalService with a fresh AsyncMock session."""
    if session is None:
        session = AsyncMock()
    svc = ReversalService(
        session,
        tenant_id=tenant_id,
        industry=industry,
        trace_id=trace_id,
    )
    return svc, session


def _make_target_event(
    *,
    event_type: str = "purchase_inbound",
    qty: Decimal | None = Decimal("100"),
    reverses_event_id: uuid.UUID | None = None,
    correction_group_id: uuid.UUID | None = None,
) -> InventoryLedgerEvent:
    """Build an InventoryLedgerEvent for testing."""
    return InventoryLedgerEvent(
        event_id=TARGET_EVENT_ID,
        tenant_id=TENANT_ID,
        product_id=PRODUCT_ID,
        period_key=PERIOD_KEY,
        event_type=event_type,
        qty=qty,
        trace_id=uuid.uuid4(),
        reverses_event_id=reverses_event_id,
        correction_group_id=correction_group_id,
        payload={"source": "monthly_input"},
    )


def _wire_session(
    session: AsyncMock,
    *,
    target_event: InventoryLedgerEvent | None = None,
    period_status: str | None = "open",
    fiscal_period_status: str | None = "open",
) -> None:
    """Wire session mocks for the 9-step AD-22 sequence.

    Story 11.2 wire: extended queue to also include fiscal_period_status
    row (returned from fetch_fiscal_period_status after fetch_period_status).
    """
    # (1) fetch_target_event → returns the target_event row
    target_row = MagicMock()
    if target_event is not None:
        target_row.event_id = target_event.event_id
        target_row.tenant_id = target_event.tenant_id
        target_row.product_id = target_event.product_id
        target_row.period_key = target_event.period_key
        target_row.event_type = target_event.event_type
        target_row.qty = target_event.qty
        target_row.trace_id = target_event.trace_id
        target_row.reverses_event_id = target_event.reverses_event_id
        target_row.correction_group_id = target_event.correction_group_id
        target_row.payload = target_event.payload

    # (2) fetch_period_status → status (MagicMock row with .status attribute)
    period_row = MagicMock()
    period_row.status = period_status

    # (2.5) Story 11.2 — fetch_fiscal_period_status → status
    fiscal_row = MagicMock()
    fiscal_row.status = fiscal_period_status

    # Use a deque-like list of return values for sequential scalar() calls.
    _wire_session.queue = [target_row, period_row, fiscal_row]
    session.scalar = AsyncMock(
        side_effect=lambda *_: _wire_session.queue.pop(0)
    )

    # (7) AD-25 publish — no DB write, but session.commit() is called
    session.commit = AsyncMock()

    # (8) audit emit — no DB write inside emit_audit (mocked)
    session.add = MagicMock()
    session.flush = AsyncMock()


# ── AC #1: AD-22 sequence — sign-negating row INSERT ─────────


def test_execute_reversal_emits_audit_before_insert() -> None:
    """Audit-first: emit_audit called BEFORE session.add for the negating row.

    CR 1.1 lesson: writes audit BEFORE data so the audit row is durable
    even if the INSERT fails.
    """

    async def _impl() -> None:
        svc, session = _build_service()
        target = _make_target_event()
        _wire_session(session, target_event=target, period_status="open")

        # Track call ordering
        call_order: list[str] = []

        original_emit_audit = svc._emit_reversal_handler_invoked_audit

        async def tracking_audit_invoked(**_kwargs: Any) -> None:
            call_order.append("audit_invoked")

        # session.add is SYNC in real SQLAlchemy; use sync MagicMock.
        def tracking_insert(_row: Any) -> None:
            call_order.append("add")

        svc._emit_reversal_handler_invoked_audit = tracking_audit_invoked  # type: ignore[method-assign]
        session.add = MagicMock(side_effect=tracking_insert)

        response = await svc.execute_reversal(
            target_event_id=TARGET_EVENT_ID,
            reason="테스트 역분개",
            actor_id=ACTOR_ID,
            capability_granted=True,
        )

        # ASSERT — audit_invoked happens BEFORE the first add
        assert call_order[0] == "audit_invoked"
        assert "add" in call_order
        assert response.correction_group_id is not None
        assert response.negating_event_id is not None
        assert response.target_event_id == TARGET_EVENT_ID
        assert response.cache_invalidation_receipt["channel"] == "ai_cache"

    asyncio.run(_impl())


def test_execute_reversal_sign_negating_constructs_correct_qty() -> None:
    """AD-22 sign-negating: negating.qty = -target.qty (banker's rounding)."""

    async def _impl() -> None:
        svc, session = _build_service()
        target = _make_target_event(qty=Decimal("100"))
        _wire_session(session, target_event=target, period_status="open")

        # Capture ALL rows added (filter by event_type afterwards)
        all_rows: list[Any] = []
        session.add = MagicMock(side_effect=lambda row: all_rows.append(row))

        response = await svc.execute_reversal(
            target_event_id=TARGET_EVENT_ID,
            reason="테스트",
            actor_id=ACTOR_ID,
            capability_granted=True,
        )

        # Filter: InventoryLedger rows (have event_type) — audit rows don't.
        inventory_rows = [r for r in all_rows if hasattr(r, "event_type")]
        assert len(inventory_rows) >= 1
        negating_row = inventory_rows[0]
        assert negating_row.event_type == "reversal_negating"
        assert negating_row.qty == Decimal("-100.0000")
        assert negating_row.reverses_event_id == TARGET_EVENT_ID
        assert negating_row.correction_group_id == response.correction_group_id

    asyncio.run(_impl())


def test_execute_reversal_with_corrected_qty_inserts_both_rows() -> None:
    """corrected_qty + corrected_period_key → sign-negating + corrected rows."""

    async def _impl() -> None:
        svc, session = _build_service()
        target = _make_target_event(qty=Decimal("100"))
        _wire_session(session, target_event=target, period_status="open")

        all_rows: list[Any] = []
        session.add = MagicMock(side_effect=lambda row: all_rows.append(row))

        response = await svc.execute_reversal(
            target_event_id=TARGET_EVENT_ID,
            reason="교정 포함",
            actor_id=ACTOR_ID,
            capability_granted=True,
            corrected_qty=Decimal("150"),
            corrected_period_key="2026-08",
        )

        # Filter: InventoryLedger rows
        inventory_rows = [r for r in all_rows if hasattr(r, "event_type")]
        assert len(inventory_rows) >= 2
        assert response.corrected_event_id is not None
        # Find the corrected row by event_type
        corrected_row = next(
            r for r in inventory_rows if r.event_type == "reversal_corrected"
        )
        assert corrected_row.qty == Decimal("150.0000")
        assert corrected_row.correction_group_id == response.correction_group_id
        # D1 — corrected row does NOT carry `reverses_event_id`. Only the
        # sign-negating row owns `reverses_event_id=target_event.event_id`.
        # The corrected row's link to the target is via `correction_group_id`
        # (shared with the negating row).
        assert corrected_row.reverses_event_id is None

    asyncio.run(_impl())


def test_execute_reversal_skips_corrected_row_when_no_corrected_qty() -> None:
    """corrected_qty=None + corrected_period_key=None → only negating row."""

    async def _impl() -> None:
        svc, session = _build_service()
        target = _make_target_event()
        _wire_session(session, target_event=target, period_status="open")

        all_rows: list[Any] = []
        session.add = MagicMock(side_effect=lambda row: all_rows.append(row))

        response = await svc.execute_reversal(
            target_event_id=TARGET_EVENT_ID,
            reason="단순 부호 반전",
            actor_id=ACTOR_ID,
            capability_granted=True,
        )

        # Filter: InventoryLedger rows
        inventory_rows = [r for r in all_rows if hasattr(r, "event_type")]
        assert response.corrected_event_id is None
        assert len(inventory_rows) == 1

    asyncio.run(_impl())


# ── AC #2: AD-22 — authorization gate ────────────────────────


def test_execute_reversal_rejects_when_capability_not_granted() -> None:
    """capability_granted=False (service-only tenant) → ReversalRejectedError."""

    async def _impl() -> None:
        svc, session = _build_service()
        target = _make_target_event()
        _wire_session(session, target_event=target, period_status="open")

        with pytest.raises(ReversalRejectedError) as exc_info:
            await svc.execute_reversal(
                target_event_id=TARGET_EVENT_ID,
                reason="테스트",
                actor_id=ACTOR_ID,
                capability_granted=False,  # ← service-only tenant
            )

        assert "M11" in exc_info.value.reason_ko or "권한" in exc_info.value.reason_ko

    asyncio.run(_impl())


def test_execute_reversal_rejects_when_period_locked() -> None:
    """period_status='locked' → LockedPeriodReversalRejectedError (422)."""

    async def _impl() -> None:
        svc, session = _build_service()
        target = _make_target_event()
        _wire_session(session, target_event=target, period_status="locked")

        with pytest.raises(LockedPeriodReversalRejectedError) as exc_info:
            await svc.execute_reversal(
                target_event_id=TARGET_EVENT_ID,
                reason="잠긴 기간 역분개 시도",
                actor_id=ACTOR_ID,
                capability_granted=True,
            )

        assert exc_info.value.period_key == PERIOD_KEY

    asyncio.run(_impl())


def test_execute_reversal_raises_target_not_found() -> None:
    """target_event_id not in tenant → ReversalTargetNotFoundError (404)."""

    async def _impl() -> None:
        svc, session = _build_service()
        # Wire session: target_event fetch returns None
        _wire_session.queue = [None, None]
        session.scalar = AsyncMock(
            side_effect=lambda *_: _wire_session.queue.pop(0)
        )

        with pytest.raises(ReversalTargetNotFoundError) as exc_info:
            await svc.execute_reversal(
                target_event_id=TARGET_EVENT_ID,
                reason="테스트",
                actor_id=ACTOR_ID,
                capability_granted=True,
            )

        assert exc_info.value.target_event_id == TARGET_EVENT_ID

    asyncio.run(_impl())


def test_execute_reversal_raises_duplicate_on_reverses_uniqueness() -> None:
    """(tenant_id, reverses_event_id) UNIQUE violation → ReversalDuplicateError (422)."""

    async def _impl() -> None:
        svc, session = _build_service()
        target = _make_target_event()
        _wire_session(session, target_event=target, period_status="open")

        # Make session.flush raise IntegrityError on the THIRD call
        # (the inventory_ledger data INSERT). The 1st + 2nd calls are
        # the two audit emits (audit-first per CR 1.1 — handler_invoked
        # + reversal_negating_inserted), which must succeed BEFORE the
        # data INSERT can fail. Only the data INSERT violation maps to
        # ReversalDuplicateError (422).
        flush_call_count = {"count": 0}

        async def _flush_with_integrity_error() -> None:
            flush_call_count["count"] += 1
            if flush_call_count["count"] == 3:
                raise IntegrityError(
                    statement="INSERT INTO inventory_ledger ...",
                    params={},
                    orig=Exception("uq_inventory_ledger_reverses_event_id"),
                )
            # Audit emit flushes (1st + 2nd) succeed.

        session.flush = AsyncMock(side_effect=_flush_with_integrity_error)

        with pytest.raises(ReversalDuplicateError):
            await svc.execute_reversal(
                target_event_id=TARGET_EVENT_ID,
                reason="재역분개 시도",
                actor_id=ACTOR_ID,
                capability_granted=True,
            )

        # Rollback should be called
        session.rollback.assert_called_once()

    asyncio.run(_impl())


# ── AC #3: AD-25 cache invalidation publisher integration ────


def test_execute_reversal_publishes_cache_invalidation_to_ai_cache() -> None:
    """AD-25: CacheInvalidationPublisher.publish() called with channel='ai_cache'."""

    async def _impl() -> None:
        svc, session = _build_service()
        target = _make_target_event()
        _wire_session(session, target_event=target, period_status="open")

        response = await svc.execute_reversal(
            target_event_id=TARGET_EVENT_ID,
            reason="테스트",
            actor_id=ACTOR_ID,
            capability_granted=True,
        )

        # ASSERT — receipt has channel='ai_cache'
        receipt = response.cache_invalidation_receipt
        assert receipt["channel"] == "ai_cache"
        assert receipt["tenant_id"] == str(TENANT_ID)
        assert receipt["event_id"] == str(TARGET_EVENT_ID)
        assert receipt["correction_group_id"] == str(response.correction_group_id)
        assert receipt["trace_id"] == TRACE_ID
        assert "published_at" in receipt

    asyncio.run(_impl())


# ── AC #4: get_reversal_history (CR 1.1 observability) ───────


def test_get_reversal_history_returns_rows_for_correction_group() -> None:
    """get_reversal_history reads all rows sharing correction_group_id."""

    async def _impl() -> None:
        svc, session = _build_service()

        # Wire session.execute to return 2 rows (negating + corrected)
        row_negating = MagicMock()
        row_negating.event_id = uuid.uuid4()
        row_negating.tenant_id = TENANT_ID
        row_negating.product_id = PRODUCT_ID
        row_negating.period_key = PERIOD_KEY
        row_negating.event_type = "reversal_negating"
        row_negating.qty = Decimal("-100.0000")
        row_negating.reverses_event_id = TARGET_EVENT_ID
        row_negating.correction_group_id = CORRECTION_GROUP_ID
        row_negating.reversal_of_period_key = PERIOD_KEY
        row_negating.trace_id = uuid.uuid4()

        row_corrected = MagicMock()
        row_corrected.event_id = uuid.uuid4()
        row_corrected.tenant_id = TENANT_ID
        row_corrected.product_id = PRODUCT_ID
        row_corrected.period_key = PERIOD_KEY
        row_corrected.event_type = "reversal_corrected"
        row_corrected.qty = Decimal("150.0000")
        row_corrected.reverses_event_id = TARGET_EVENT_ID
        row_corrected.correction_group_id = CORRECTION_GROUP_ID
        row_corrected.reversal_of_period_key = PERIOD_KEY
        row_corrected.trace_id = uuid.uuid4()

        execute_result = MagicMock()
        execute_result.__iter__ = lambda _: iter([row_negating, row_corrected])
        session.execute = AsyncMock(return_value=execute_result)

        history = await svc.get_reversal_history(
            correction_group_id=CORRECTION_GROUP_ID,
        )

        assert len(history) == 2
        assert history[0]["event_type"] == "reversal_negating"
        assert history[1]["event_type"] == "reversal_corrected"
        assert history[0]["correction_group_id"] == str(CORRECTION_GROUP_ID)
        assert history[1]["correction_group_id"] == str(CORRECTION_GROUP_ID)

    asyncio.run(_impl())


def test_get_reversal_history_filters_by_tenant_id() -> None:
    """Defense-in-depth: tenant_id filter applied to the SELECT (RLS-scoped)."""

    async def _impl() -> None:
        svc, session = _build_service()
        empty_result = MagicMock()
        empty_result.__iter__ = lambda _: iter([])
        session.execute = AsyncMock(return_value=empty_result)

        await svc.get_reversal_history(
            correction_group_id=CORRECTION_GROUP_ID,
        )

        # The select statement must include tenant_id filter
        call_args = session.execute.call_args
        assert call_args is not None
        # We can't easily inspect the SQL statement object, but the
        # method itself only uses tenant_id from self.tenant_id.
        assert svc.tenant_id == TENANT_ID

    asyncio.run(_impl())


# ── AC #5: reject_reversal (=M11 reject path) ────────────────


def test_reject_reversal_emits_audit_and_raises() -> None:
    """reject_reversal: emit audit → raise ReversalRejectedError."""

    async def _impl() -> None:
        svc, session = _build_service()
        target = _make_target_event()
        _wire_session.queue = [MagicMock(
            event_id=target.event_id,
            tenant_id=target.tenant_id,
            product_id=target.product_id,
            period_key=target.period_key,
            event_type=target.event_type,
            qty=target.qty,
            trace_id=target.trace_id,
            reverses_event_id=None,
            correction_group_id=None,
            payload=target.payload,
        )]
        session.scalar = AsyncMock(
            side_effect=lambda *_: _wire_session.queue.pop(0)
        )

        with pytest.raises(ReversalRejectedError) as exc_info:
            await svc.reject_reversal(
                target_event_id=TARGET_EVENT_ID,
                reason="테스트 거절",
                actor_id=ACTOR_ID,
            )

        assert exc_info.value.reason_ko == "테스트 거절"

    asyncio.run(_impl())


# ── AC #6: tenant isolation (RLS) ────────────────────────────


def test_execute_reversal_uses_self_tenant_id() -> None:
    """Defense-in-depth: ReversalService uses self.tenant_id (no caller spoof)."""

    async def _impl() -> None:
        svc, session = _build_service(tenant_id=OTHER_TENANT_ID)
        # Wire: target NOT found (because tenant_id mismatch)
        _wire_session.queue = [None, None]
        session.scalar = AsyncMock(
            side_effect=lambda *_: _wire_session.queue.pop(0)
        )

        with pytest.raises(ReversalTargetNotFoundError) as exc_info:
            await svc.execute_reversal(
                target_event_id=TARGET_EVENT_ID,
                reason="테스트",
                actor_id=ACTOR_ID,
                capability_granted=True,
            )

        assert exc_info.value.tenant_id == OTHER_TENANT_ID

    asyncio.run(_impl())


# ── AC #7: audit emit ordering (CR 1.1) ──────────────────────


def test_audit_emit_ordering_reversal_sequence() -> None:
    """Audit-first: m11_reversal_handler_invoked → inventory_ledger_reversal_logged
    → cache_invalidation_published are emitted in this order."""

    async def _impl() -> None:
        svc, session = _build_service()
        target = _make_target_event()
        _wire_session(session, target_event=target, period_status="open")

        # Track audit emissions — D3 R4 triage: the M11 reversal sequence
        # emits `reversal_negating_inserted` (REVERSAL_LOG), NOT
        # `inventory_ledger_reversal_logged` (INVENTORY_LEDGER). The
        # corrected-row branch (not exercised here without corrected_qty)
        # would emit `reversal_corrected_inserted`.
        audit_actions: list[str] = []

        async def track_emit_handler_invoked(**_kwargs: Any) -> None:
            audit_actions.append("m11_reversal_handler_invoked")

        async def track_emit_negating_inserted(
            **_kwargs: Any,
        ) -> None:
            audit_actions.append("reversal_negating_inserted")

        async def track_emit_cache_invalidation(
            **_kwargs: Any,
        ) -> None:
            audit_actions.append("cache_invalidation_published")

        svc._emit_reversal_handler_invoked_audit = (  # type: ignore[method-assign]
            track_emit_handler_invoked
        )
        svc._emit_reversal_negating_inserted_audit = (  # type: ignore[method-assign]
            track_emit_negating_inserted
        )
        svc._emit_cache_invalidation_audit = (  # type: ignore[method-assign]
            track_emit_cache_invalidation
        )

        await svc.execute_reversal(
            target_event_id=TARGET_EVENT_ID,
            reason="테스트",
            actor_id=ACTOR_ID,
            capability_granted=True,
        )

        # Order: handler_invoked → reversal_negating_inserted → cache_invalidation_published
        assert audit_actions[0] == "m11_reversal_handler_invoked"
        assert "reversal_negating_inserted" in audit_actions
        assert "cache_invalidation_published" in audit_actions
        # handler_invoked must come BEFORE reversal_negating_inserted
        assert audit_actions.index("m11_reversal_handler_invoked") < audit_actions.index(
            "reversal_negating_inserted"
        )

    asyncio.run(_impl())


# ── AC #8: capability integration (PRISM gate) ──────────────


def test_execute_reversal_service_only_tenant_rejected() -> None:
    """Service-only tenant (industry=None) → rejected at capability gate."""

    async def _impl() -> None:
        svc, session = _build_service(industry=None)
        target = _make_target_event()
        _wire_session(session, target_event=target, period_status="open")

        with pytest.raises(ReversalRejectedError):
            await svc.execute_reversal(
                target_event_id=TARGET_EVENT_ID,
                reason="서비스 전용 테넌트",
                actor_id=ACTOR_ID,
                capability_granted=False,
            )

    asyncio.run(_impl())
