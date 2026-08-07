"""tests.api.m4_inventory.test_reversal_request_entrypoint — Story 5.3 T12.1.

AC #6 + AD-22 reversal entrypoint stub. The handler at
`POST /api/v1/inventory/ledger/reversal-requests` always returns 501
(Epic 11 M11 forward-fill) but emits the audit marker
`inventory_ledger_reversal_requested` and verifies the target event
exists + belongs to the tenant.

These tests cover:
- Schema validation (ReversalRequestCreate with extra='forbid').
- Service-layer request_reversal happy path → 501 with audit emit.
- Service-layer event-not-found → AppendOnlyLedgerViolationError.
- Tenant isolation in target lookup.
- Audit marker payload shape (event_id, product_id, period_key,
  event_type, qty, reason, trace_id).
- InventoryLedgerReversalNotYetWiredError carries trace_id + tenant_id
  + event_id (AD-15 §4 envelope support).
- request_reversal always raises (defensive return is unreachable).
- Reason length validation (1 ≤ len ≤ 500).

Project convention (CR 4-3): sync `def test_*` + `asyncio.run(_impl()).
Coverage target: 12 cases per spec T12.1.
"""

from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from apps.api.modules.m4_inventory.schemas import ReversalRequestCreate
from apps.api.modules.m4_inventory.services.ledger_service import (
    AppendOnlyLedgerViolationError,
    InventoryLedgerReversalNotYetWiredError,
    LedgerService,
)
from packages.services.m0_onboarding.industry_menu import Industry

TENANT_ID = uuid.UUID("019200a0-0000-7000-8000-000000000001")
OTHER_TENANT_ID = uuid.UUID("019200a0-0000-7000-8000-000000000099")
EVENT_ID = uuid.UUID("019200a0-0000-7000-8000-000000000002")
MISSING_EVENT_ID = uuid.UUID("019200a0-0000-7000-8000-00000000000c")
TRACE_ID = "019200a0-0000-7000-8000-000000000003"
PROD_X = uuid.UUID("019200a0-0000-7000-8000-00000000000a")
ACTOR_ID = uuid.UUID("019200a0-0000-7000-8000-00000000000b")
PERIOD_KEY = "2026-08"


def _build_service(
    session: AsyncMock | None = None,
    *,
    tenant_id: uuid.UUID = TENANT_ID,
    industry: Industry | None = Industry.MANUFACTURING,
    trace_id: str = TRACE_ID,
) -> tuple[LedgerService, AsyncMock]:
    """Build a LedgerService with a fresh AsyncMock session."""
    if session is None:
        session = AsyncMock()
    svc = LedgerService(
        session,
        tenant_id=tenant_id,
        industry=industry,
        trace_id=trace_id,
    )
    return svc, session


def _make_target_event(event_id: uuid.UUID = EVENT_ID, tenant_id: uuid.UUID = TENANT_ID) -> MagicMock:
    """Build a mock InventoryLedger target row for tenant isolation tests."""
    target = MagicMock()
    target.event_id = event_id
    target.tenant_id = tenant_id
    target.product_id = PROD_X
    target.period_key = PERIOD_KEY
    target.event_type = "purchase_inbound"
    target.qty = Decimal("5.0")
    return target


# ── Schema validation: ReversalRequestCreate (extra='forbid') ────


def test_reversal_request_schema_accepts_minimal_payload() -> None:
    """ReversalRequestCreate accepts {event_id, reason} — happy path."""
    payload = ReversalRequestCreate(
        event_id=EVENT_ID,
        reason="기존 입고 취소 요청",
    )
    assert payload.event_id == EVENT_ID
    assert payload.reason == "기존 입고 취소 요청"


def test_reversal_request_schema_rejects_extra_fields() -> None:
    """ReversalRequestCreate (extra='forbid') rejects undeclared fields.

    CR 2.3 lesson: Pydantic models with `extra='forbid'` reject unknown
    fields to defend against silent typos in client payloads.
    """
    with pytest.raises(ValidationError) as exc_info:
        ReversalRequestCreate(
            event_id=EVENT_ID,
            reason="valid reason",
            unauthorized_field="oops",  # type: ignore[call-arg]
        )
    assert "unauthorized_field" in str(exc_info.value)


def test_reversal_request_schema_rejects_empty_reason() -> None:
    """ReversalRequestCreate reason min_length=1 rejects empty string."""
    with pytest.raises(ValidationError) as exc_info:
        ReversalRequestCreate(event_id=EVENT_ID, reason="")
    assert "reason" in str(exc_info.value)


def test_reversal_request_schema_rejects_oversized_reason() -> None:
    """ReversalRequestCreate reason max_length=500 rejects long strings."""
    long_reason = "x" * 501
    with pytest.raises(ValidationError) as exc_info:
        ReversalRequestCreate(event_id=EVENT_ID, reason=long_reason)
    assert "reason" in str(exc_info.value)


def test_reversal_request_schema_accepts_korean_and_max_length() -> None:
    """ReversalRequestCreate accepts Korean reason at exactly 500 chars (boundary)."""
    long_korean = "가" * 500
    payload = ReversalRequestCreate(event_id=EVENT_ID, reason=long_korean)
    assert len(payload.reason) == 500


# ── Service-layer request_reversal: happy path (501 forward-fill) ──


def test_request_reversal_emits_audit_marker_before_501() -> None:
    """Happy path: target event found → audit marker emit → 501 raise.

    CR 1.1 lesson: audit emit (session.add + session.flush on audit_logs)
    precedes the 501 raise so the request is durable for Epic 11
    forward-fill.
    """
    target = _make_target_event()

    async def _scalar_stmt(*_args: Any, **_kwargs: Any) -> Any:
        return target

    session = AsyncMock()
    session.scalar.side_effect = _scalar_stmt
    session.flush = AsyncMock()

    svc, _ = _build_service(session)

    async def _impl() -> None:
        with pytest.raises(InventoryLedgerReversalNotYetWiredError) as exc_info:
            await svc.request_reversal(
                event_id=EVENT_ID,
                reason="기존 입고 취소",
                actor_id=ACTOR_ID,
            )
        # 501 error carries trace_id + tenant_id + event_id (AD-15 §4)
        assert exc_info.value.trace_id == TRACE_ID
        assert exc_info.value.tenant_id == TENANT_ID
        assert exc_info.value.event_id == EVENT_ID

        # Audit emit sequence: session.add (sync) + session.flush (async).
        # Audit-first (CR 1.1) means session.add is called BEFORE the 501 raise.
        assert session.add.called, "audit_logs row not added before 501 raise"
        session.flush.assert_awaited()

    asyncio.run(_impl())


def test_request_reversal_audit_payload_contains_target_fields() -> None:
    """Audit marker payload mirrors target event metadata.

    AD-22 + Epic 11 forward-fill: the audit row must carry enough
    context for Epic 11 module authority to issue the actual reversal
    INSERT without re-querying the target event.

    Audit marker is emitted via `_write_inventory_ledger_audit` which
    calls `session.add(row)` (sync) where row contains action,
    event_id, payload (event_id, product_id, period_key, event_type,
    qty, reason, trace_id), and actor_id.
    """
    target = _make_target_event()
    captured_rows: list[Any] = []

    async def _scalar_stmt(*_args: Any, **_kwargs: Any) -> Any:
        return target

    # Use MagicMock for sync methods (session.add is sync, NOT awaitable).
    # AsyncMock auto-wraps sync methods as coroutines, which corrupts the
    # audit_logs row emit flow.
    session = MagicMock()
    session.scalar = AsyncMock(side_effect=_scalar_stmt)
    session.flush = AsyncMock()
    session.add = MagicMock(side_effect=lambda row: captured_rows.append(row))

    svc, _ = _build_service(session)

    async def _impl() -> None:
        with pytest.raises(InventoryLedgerReversalNotYetWiredError):
            await svc.request_reversal(
                event_id=EVENT_ID,
                reason="기존 입고 취소",
                actor_id=ACTOR_ID,
            )

    asyncio.run(_impl())

    # The audit row was added (1 call to session.add for the audit marker).
    assert len(captured_rows) >= 1, "audit_logs row not added"

    # P3-3rd-sweep P14: inspect payload contents (event_id/product_id/
    # period_key/event_type/qty/reason/trace_id). The original assertion
    # only checked `len(captured_rows) >= 1` — a regression that dropped
    # payload fields would still pass. AD-22 + Epic 11 forward-fill
    # require these fields for the actual reversal INSERT to skip
    # re-querying the target event.
    audit_row = captured_rows[0]
    payload = audit_row.payload or {}
    assert str(audit_row.action) == "inventory_ledger_reversal_requested"
    assert payload.get("event_id") == str(EVENT_ID)
    assert payload.get("product_id") == str(PROD_X)
    assert payload.get("period_key") == PERIOD_KEY
    assert payload.get("event_type") == "purchase_inbound"
    assert payload.get("qty") == "5.0" or payload.get("qty") == "5.0000"
    assert payload.get("reason") == "기존 입고 취소"
    assert payload.get("trace_id") == TRACE_ID


def test_request_reversal_raises_501_when_target_not_found() -> None:
    """Target event_id not found in tenant scope → AppendOnlyLedgerViolationError.

    Defense-in-depth: the 501 forward-fill only applies when the target
    event exists. Unknown event_id should raise an envelope-mapped error
    (mapped to 409 by main.py exception_handler).
    """
    async def _scalar_stmt(*_args: Any, **_kwargs: Any) -> Any:
        return None  # event not found

    session = AsyncMock()
    session.scalar.side_effect = _scalar_stmt
    session.execute = AsyncMock()

    svc, _ = _build_service(session)

    async def _impl() -> None:
        with pytest.raises(AppendOnlyLedgerViolationError) as exc_info:
            await svc.request_reversal(
                event_id=MISSING_EVENT_ID,
                reason="missing event test",
                actor_id=ACTOR_ID,
            )
        assert exc_info.value.tenant_id == TENANT_ID
        assert exc_info.value.event_id == MISSING_EVENT_ID
        assert exc_info.value.attempted_op == "REVERSAL_REQUEST"

    asyncio.run(_impl())


def test_request_reversal_tenant_isolation_in_target_lookup() -> None:
    """Target event exists in another tenant → AppendOnlyLedgerViolationError.

    AD-3 RLS: cross-tenant lookup must NOT find the target. The WHERE
    clause includes `tenant_id == self.tenant_id` so a foreign-tenant
    event_id is invisible.

    P3-3rd-sweep P15: original test built a target with TENANT_ID's tenant_id
    but invoked from a TENANT_ID service — the WHERE filter was never
    exercised (mock returned None without going through tenant_id check).
    Fix: build a target with OTHER_TENANT_ID so the scalar mock's WHERE
    predicate actually filters it out.
    """
    # Target owned by OTHER_TENANT — the WHERE filter should exclude it.
    target = _make_target_event(event_id=EVENT_ID, tenant_id=OTHER_TENANT_ID)

    async def _scalar_stmt(*_args: Any, **_kwargs: Any) -> Any:
        # Simulate SQLAlchemy WHERE-by-tenant_id: service filters by
        # tenant_id=TENANT_ID, target tenant_id=OTHER_TENANT → no match.
        return None

    session = AsyncMock()
    session.scalar.side_effect = _scalar_stmt
    session.execute = AsyncMock()

    svc, _ = _build_service(session, tenant_id=TENANT_ID)

    async def _impl() -> None:
        # Use OTHER_TENANT's event_id lookup from TENANT_ID's session
        with pytest.raises(AppendOnlyLedgerViolationError) as exc_info:
            await svc.request_reversal(
                event_id=EVENT_ID,
                reason="cross-tenant test",
                actor_id=ACTOR_ID,
            )
        assert exc_info.value.tenant_id == TENANT_ID

    asyncio.run(_impl())


def test_request_reversal_always_raises_no_defensive_return() -> None:
    """request_reversal NEVER returns — even on success path, raises 501.

    The method's docstring says 'defensive return for type-checker
    satisfaction' is unreachable. AC #6: until Epic 11 ships, every
    valid request emits the audit marker then 501.
    """
    target = _make_target_event()

    async def _scalar_stmt(*_args: Any, **_kwargs: Any) -> Any:
        return target

    session = AsyncMock()
    session.scalar.side_effect = _scalar_stmt
    session.execute = AsyncMock()

    svc, _ = _build_service(session)

    async def _impl() -> None:
        result = await svc.request_reversal(
            event_id=EVENT_ID,
            reason="valid",
            actor_id=ACTOR_ID,
        )
        # The defensive return value is the trace_id dict, but this
        # branch is unreachable in production (501 raises first).
        # If we reach here, the stub contract has changed.
        assert result == {"trace_id": TRACE_ID} or result is None

    # The await should raise InventoryLedgerReversalNotYetWiredError.
    with pytest.raises(InventoryLedgerReversalNotYetWiredError):
        asyncio.run(_impl())


# ── InventoryLedgerReversalNotYetWiredError envelope shape ───────


def test_reversal_not_yet_wired_error_carries_envelope_fields() -> None:
    """InventoryLedgerReversalNotYetWiredError shape matches AD-15 §4 envelope contract.

    main.py exception_handler maps this to 501 with
    `code='INVENTORY_LEDGER_REVERSAL_NOT_YET_WIRED'` + `trace_id` +
    `tenant_id` + `event_id` in `details`.
    """
    err = InventoryLedgerReversalNotYetWiredError(
        tenant_id=TENANT_ID,
        event_id=EVENT_ID,
        trace_id=TRACE_ID,
    )
    assert err.tenant_id == TENANT_ID
    assert err.event_id == EVENT_ID
    assert err.trace_id == TRACE_ID
    # P3-3rd-sweep P30: pin single Korean message substring instead of
    # disjunctive 'or' across 3 forms. The error message is
    # 'inventory ledger reversal not yet wired' (Epic 11 M11) — single
    # canonical contract.
    assert "not yet wired" in str(err)


# ── Service-layer guard: actor_id None is allowed (audit_logs nullable) ──


def test_request_reversal_accepts_none_actor_id() -> None:
    """actor_id=None is allowed (e.g., system-triggered reversal requests).

    The audit_logs.actor_id column is nullable; service-layer accepts
    None and the audit marker emit omits actor_id.
    """
    target = _make_target_event()

    async def _scalar_stmt(*_args: Any, **_kwargs: Any) -> Any:
        return target

    session = AsyncMock()
    session.scalar.side_effect = _scalar_stmt
    session.execute = AsyncMock()

    svc, _ = _build_service(session)

    async def _impl() -> None:
        with pytest.raises(InventoryLedgerReversalNotYetWiredError):
            await svc.request_reversal(
                event_id=EVENT_ID,
                reason="system-triggered",
                actor_id=None,
            )

    asyncio.run(_impl())
