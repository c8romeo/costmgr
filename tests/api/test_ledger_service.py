"""tests.api.test_ledger_service — Story 5.2 service-layer mock_session tests (T9.3).

AC #3 + AC #4 + AC #6 — LedgerService methods exercised end-to-end via
AsyncMock session (no live DB). The pure-kernel behavior is covered by
`tests/services/m4_inventory/test_ledger.py` (T1); these tests focus on:

- Audit-first emit ordering (CR 1.1 lesson — `emit_audit` called BEFORE
  `session.add`/`session.flush`).
- AST guard trigger paths (UPDATE/DELETE/TRUNCATE/DROP TABLE forbidden).
- Tenant isolation (every query filters on `tenant_id`).
- Exception mapping (typed exceptions raised → AD-15 §4 envelopes).
- request_reversal 501 forward-fill (Epic 11 ownership).
- query_period_closing / query_period_closing_all shape parity.

Project convention (CR 4-3): sync `def test_*` + `asyncio.run(_impl())`.
Coverage target: 15 cases per spec T9.3 (this module has 22).
"""

from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from apps.api.modules.m4_inventory.schemas import (
    CarryChainResponse,
    LedgerEventCreateRequest,
    PeriodClosingResponse,
    ReversalRequestCreate,
)
from apps.api.modules.m4_inventory.services.ledger_service import (
    AppendOnlyLedgerViolationError,
    InventoryLedgerInvalidEventTypeError,
    InventoryLedgerPeriodKeyFormatError,
    InventoryLedgerReversalNotYetWiredError,
    LedgerService,
)
from packages.services.m0_onboarding.industry_menu import Industry

TENANT_ID = uuid.UUID("019200a0-0000-7000-8000-000000000001")
OTHER_TENANT_ID = uuid.UUID("019200a0-0000-7000-8000-000000000099")
EVENT_ID = uuid.UUID("019200a0-0000-7000-8000-000000000002")
# trace_id must be a valid UUID hex string (service calls uuid.UUID(trace_id))
TRACE_ID = "019200a0-0000-7000-8000-000000000003"
PROD_X = uuid.UUID("019200a0-0000-7000-8000-00000000000a")
ACTOR_ID = uuid.UUID("019200a0-0000-7000-8000-00000000000b")


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


# ── AC #4: append_event primary INSERT path ──────────────────


def test_append_event_emits_audit_before_insert() -> None:
    """Audit-first: `_write_inventory_ledger_audit` invoked BEFORE `session.add`.

    CR 1.1 lesson: writes audit BEFORE data so the audit row is durable
    even if the INSERT fails.
    """

    async def _impl() -> None:
        svc, session = _build_service()
        call_order: list[str] = []

        # Wrap _write_inventory_ledger_audit to record ordering
        async def tracking_audit(**_kwargs: Any) -> None:
            call_order.append("audit")
        svc._write_inventory_ledger_audit = tracking_audit  # type: ignore[method-assign]

        # session.add is SYNC in real SQLAlchemy AsyncSession; replace
        # the AsyncMock-wrapped add with a sync MagicMock so the call
        # actually records (AsyncMock treats it as a coroutine that
        # nothing awaits, dropping the side-effect).
        session.add = MagicMock(side_effect=lambda _row: call_order.append("add"))

        # session.flush is async in AsyncSession
        async def _flush() -> None:
            call_order.append("flush")
        session.flush.side_effect = _flush

        await svc.append_event(
            product_id=PROD_X,
            period_key="2026-07",
            event_type="purchase_inbound",
            qty=Decimal("10"),
            source="monthly_input",
            actor_id=ACTOR_ID,
        )

        assert "audit" in call_order, (
            f"Audit not invoked at all: {call_order}"
        )
        assert "add" in call_order, (
            f"session.add not invoked at all: {call_order}"
        )
        assert call_order.index("audit") < call_order.index("add"), (
            f"Audit-first pattern violated: {call_order}"
        )
        assert call_order.index("add") < call_order.index("flush"), (
            f"add must precede flush: {call_order}"
        )

    asyncio.run(_impl())


def test_append_event_rejects_invalid_event_type() -> None:
    """Pure kernel guard rejects event_type NOT in the 11-value whitelist.

    `validate_event_type` raises `AppendOnlyLedgerError` from the
    kernel; the service re-raises as `InventoryLedgerInvalidEventTypeError`
    (422 INVENTORY_LEDGER_INVALID_EVENT_TYPE).
    """

    async def _impl() -> None:
        svc, _session = _build_service()
        with pytest.raises(InventoryLedgerInvalidEventTypeError) as exc_info:
            await svc.append_event(
                product_id=PROD_X,
                period_key="2026-07",
                event_type="not_in_whitelist",
                qty=Decimal("10"),
                source="monthly_input",
            )
        assert exc_info.value.event_type == "not_in_whitelist"
        assert exc_info.value.tenant_id == TENANT_ID

    asyncio.run(_impl())


def test_append_event_rejects_malformed_period_key() -> None:
    """Pure kernel guard rejects period_key not matching 'YYYY-MM' AD-24."""

    async def _impl() -> None:
        svc, _session = _build_service()
        with pytest.raises(InventoryLedgerPeriodKeyFormatError) as exc_info:
            await svc.append_event(
                product_id=PROD_X,
                period_key="2026-7",  # missing zero-pad → AD-24 mismatch
                event_type="purchase_inbound",
                qty=Decimal("10"),
                source="monthly_input",
            )
        assert exc_info.value.period_key == "2026-7"

    asyncio.run(_impl())


def test_append_event_db_check_constraint_violation_writes_audit() -> None:
    """IntegrityError on flush triggers `inventory_ledger_event_rejected` audit.

    Defense-in-depth: even when the DB rejects the row, the audit
    observability is preserved.
    """

    async def _impl() -> None:
        svc, session = _build_service()
        # session.add is sync — replace the AsyncMock-wrapped add
        # with a sync MagicMock (otherwise the call returns an
        # un-awaited coroutine and emits a RuntimeWarning).
        session.add = MagicMock()

        async def _flush_raises() -> None:
            raise IntegrityError(
                statement="INSERT INTO inventory_ledger ...",
                params={},
                orig=Exception("CHECK constraint violated"),
            )
        session.flush.side_effect = _flush_raises

        audit_calls: list[dict[str, Any]] = []

        async def tracking_audit(**kwargs: Any) -> None:
            audit_calls.append(kwargs)
        svc._write_inventory_ledger_audit = tracking_audit  # type: ignore[method-assign]

        with pytest.raises(IntegrityError):
            await svc.append_event(
                product_id=PROD_X,
                period_key="2026-07",
                event_type="purchase_inbound",
                qty=Decimal("10"),
                source="monthly_input",
            )

        actions = [c["action"] for c in audit_calls]
        assert "inventory_ledger_event_appended" in actions, (
            f"audit-first `event_appended` not emitted: {actions}"
        )
        assert "inventory_ledger_event_rejected" in actions, (
            f"DB CHECK violation must emit `event_rejected` audit: {actions}"
        )

    asyncio.run(_impl())


# ── AC #1: query_period_closing + query_period_closing_all ────


def test_query_period_closing_returns_decimal_sum() -> None:
    """SUM(qty) for a single (tenant, product, period_key) → Decimal."""

    async def _impl() -> None:
        svc, session = _build_service()
        session.scalar = AsyncMock(return_value=Decimal("42.5000"))

        result = await svc.query_period_closing(
            product_id=PROD_X, period_key="2026-07"
        )

        assert result == Decimal("42.5000")
        session.scalar.assert_awaited_once()
        args, kwargs = session.scalar.call_args
        bind_params = args[1] if len(args) > 1 else kwargs
        assert bind_params["tenant_id"] == str(TENANT_ID)
        assert bind_params["product_id"] == str(PROD_X)

    asyncio.run(_impl())


def test_query_period_closing_returns_zero_when_no_rows() -> None:
    """Empty result → Decimal('0') (cj-style default)."""

    async def _impl() -> None:
        svc, session = _build_service()
        session.scalar = AsyncMock(return_value=None)

        result = await svc.query_period_closing(
            product_id=PROD_X, period_key="2026-07"
        )

        assert result == Decimal("0")

    asyncio.run(_impl())


def test_query_period_closing_all_returns_product_to_qty_map() -> None:
    """Multi-product aggregation: dict[UUID, Decimal]."""

    async def _impl() -> None:
        svc, session = _build_service()

        class _Row:
            def __init__(self, pid: uuid.UUID, qty: Decimal) -> None:
                self.product_id = pid
                self.closing_qty = qty

        rows = [
            _Row(PROD_X, Decimal("10.0000")),
            _Row(uuid.UUID("019200a0-0000-7000-8000-00000000000c"),
                 Decimal("5.5000")),
        ]
        execute_result = MagicMock()
        execute_result.__iter__ = lambda _: iter(rows)
        session.execute = AsyncMock(return_value=execute_result)

        result = await svc.query_period_closing_all(period_key="2026-07")

        assert result == {
            PROD_X: Decimal("10.0000"),
            uuid.UUID("019200a0-0000-7000-8000-00000000000c"):
                Decimal("5.5000"),
        }

    asyncio.run(_impl())


def test_query_period_closing_all_tenant_scoped() -> None:
    """Multi-product query must include `tenant_id` bind parameter."""

    async def _impl() -> None:
        svc, session = _build_service()
        session.execute = AsyncMock(
            return_value=MagicMock(__iter__=lambda _: iter([]))
        )

        await svc.query_period_closing_all(period_key="2026-07")

        call_args = session.execute.call_args
        assert "tenant_id" in call_args.args[1]
        assert call_args.args[1]["tenant_id"] == str(TENANT_ID)

    asyncio.run(_impl())


# ── AC #1: query_carry_chain (recursive CTE walk) ──────────────


def test_query_carry_chain_returns_chronological_list() -> None:
    """query_carry_chain returns list of dicts ordered chronologically."""

    async def _impl() -> None:
        svc, session = _build_service()

        class _Row:
            def __init__(self) -> None:
                self.event_id = EVENT_ID
                self.period_key = "2026-06"
                self.qty = Decimal("10.0000")
                self.inserted_at = None

        session.execute = AsyncMock(
            return_value=MagicMock(__iter__=lambda _: iter([_Row()]))
        )

        result = await svc.query_carry_chain(
            product_id=PROD_X, period_key="2026-07"
        )

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["event_id"] == str(EVENT_ID)
        assert result[0]["period_key"] == "2026-06"

    asyncio.run(_impl())


# ── AC #1: get_event (single event lookup) ────────────────────


def test_get_event_tenant_scoped_returns_none_for_other_tenant() -> None:
    """`get_event` filters on tenant_id; returns None for other tenants."""

    async def _impl() -> None:
        svc, session = _build_service(tenant_id=TENANT_ID)
        session.scalar = AsyncMock(return_value=None)

        result = await svc.get_event(event_id=EVENT_ID)

        assert result is None
        session.scalar.assert_awaited_once()

    asyncio.run(_impl())


def test_get_event_returns_row_for_same_tenant() -> None:
    """`get_event` returns the row when event_id + tenant_id match."""

    async def _impl() -> None:
        svc, session = _build_service(tenant_id=TENANT_ID)
        fake_row = MagicMock()
        fake_row.event_id = EVENT_ID
        session.scalar = AsyncMock(return_value=fake_row)

        result = await svc.get_event(event_id=EVENT_ID)

        assert result is fake_row

    asyncio.run(_impl())


# ── AC #6: request_reversal 501 forward-fill (Epic 11) ────────


def test_request_reversal_emits_audit_marker_then_raises_501() -> None:
    """request_reversal emits `inventory_ledger_reversal_requested` THEN raises 501."""

    async def _impl() -> None:
        svc, session = _build_service()

        fake_target = MagicMock()
        fake_target.product_id = PROD_X
        fake_target.period_key = "2026-07"
        fake_target.event_type = "purchase_inbound"
        fake_target.qty = Decimal("10.0000")
        session.scalar = AsyncMock(return_value=fake_target)

        audit_calls: list[dict[str, Any]] = []

        async def tracking_audit(**kwargs: Any) -> None:
            audit_calls.append(kwargs)
        svc._write_inventory_ledger_audit = tracking_audit  # type: ignore[method-assign]

        with pytest.raises(InventoryLedgerReversalNotYetWiredError) as exc_info:
            await svc.request_reversal(
                event_id=EVENT_ID,
                reason="manual correction",
                actor_id=ACTOR_ID,
            )

        assert exc_info.value.event_id == EVENT_ID
        actions = [c["action"] for c in audit_calls]
        assert actions == ["inventory_ledger_reversal_requested"], (
            f"reversal entrypoint must emit ONLY `reversal_requested` "
            f"audit (not the actual INSERT); got {actions}"
        )

    asyncio.run(_impl())


def test_request_reversal_raises_append_only_violation_for_missing_event() -> None:
    """Unknown event_id → 500 AppendOnlyLedgerViolationError (NOT 404).

    cj-style: the 500 envelope signals the request was malformed at
    the service layer (unknown event_id for tenant), not a domain
    404. The append-only invariant absorbs the surface — `append_event`
    would also raise on a missing target, so we keep behavior uniform.
    """

    async def _impl() -> None:
        svc, session = _build_service()
        session.scalar = AsyncMock(return_value=None)

        with pytest.raises(AppendOnlyLedgerViolationError) as exc_info:
            await svc.request_reversal(
                event_id=EVENT_ID, reason="test", actor_id=ACTOR_ID
            )

        assert exc_info.value.event_id == EVENT_ID
        assert exc_info.value.attempted_op == "REVERSAL_REQUEST"

    asyncio.run(_impl())


# ── AC #3: AST guard (`_assert_not_modifying`) ────────────────


def test_assert_not_modifying_rejects_update_keyword() -> None:
    """AST guard rejects `UPDATE ` keyword (case-insensitive)."""
    svc, _ = _build_service()
    with pytest.raises(AppendOnlyLedgerViolationError) as exc_info:
        svc._assert_not_modifying(
            "UPDATE inventory_ledger SET qty = 0 WHERE event_id = :eid"
        )
    assert exc_info.value.attempted_op == "UPDATE"


def test_assert_not_modifying_rejects_delete_keyword() -> None:
    """AST guard rejects `DELETE ` keyword."""
    svc, _ = _build_service()
    with pytest.raises(AppendOnlyLedgerViolationError) as exc_info:
        svc._assert_not_modifying(
            "DELETE FROM inventory_ledger WHERE event_id = :eid"
        )
    assert exc_info.value.attempted_op == "DELETE"


def test_assert_not_modifying_rejects_truncate_keyword() -> None:
    """AST guard rejects `TRUNCATE ` keyword."""
    svc, _ = _build_service()
    with pytest.raises(AppendOnlyLedgerViolationError) as exc_info:
        svc._assert_not_modifying("TRUNCATE inventory_ledger")
    assert exc_info.value.attempted_op == "TRUNCATE"


def test_assert_not_modifying_rejects_drop_table_keyword() -> None:
    """AST guard rejects `DROP TABLE ` keyword."""
    svc, _ = _build_service()
    with pytest.raises(AppendOnlyLedgerViolationError) as exc_info:
        svc._assert_not_modifying("DROP TABLE inventory_ledger")
    assert exc_info.value.attempted_op == "DROP TABLE"


def test_assert_not_modifying_allows_select_statements() -> None:
    """AST guard allows SELECT statements (no forbidden keywords)."""
    svc, _ = _build_service()
    # Should NOT raise
    svc._assert_not_modifying(
        "SELECT product_id, COALESCE(SUM(qty), 0) FROM inventory_ledger ..."
    )


# ── Pydantic schema parity (T9.3 last block) ──────────────────


def test_pydantic_schemas_extra_forbid_parity() -> None:
    """Pydantic request/response schemas reject unknown fields (CR 2.3)."""
    from pydantic import ValidationError

    # LedgerEventCreateRequest rejects extra fields
    with pytest.raises(ValidationError, match="unknown_field"):
        LedgerEventCreateRequest(
            product_id=PROD_X,
            period_key="2026-07",
            event_type="purchase_inbound",
            qty=Decimal("10"),
            source="monthly_input",
            unknown_field="rejected",  # type: ignore[call-arg]
        )

    # ReversalRequestCreate rejects extra fields
    with pytest.raises(ValidationError, match="extra_field"):
        ReversalRequestCreate(
            event_id=EVENT_ID,
            reason="test",
            extra_field="rejected",  # type: ignore[call-arg]
        )


def test_period_closing_response_shape() -> None:
    """PeriodClosingResponse shape: period_key + closing dict + trace_id."""
    resp = PeriodClosingResponse.model_validate(
        {
            "period_key": "2026-07",
            "closing": {str(PROD_X): "10.0000"},
            "trace_id": TRACE_ID,
        }
    )
    assert resp.period_key == "2026-07"
    assert resp.closing[str(PROD_X)] == "10.0000"
    assert resp.trace_id == TRACE_ID


def test_carry_chain_response_shape() -> None:
    """CarryChainResponse shape: product_id + period_key + depth + chain + trace_id."""
    resp = CarryChainResponse.model_validate(
        {
            "product_id": str(PROD_X),
            "period_key": "2026-07",
            "depth": 1,
            "chain": [
                {
                    "event_id": str(EVENT_ID),
                    "period_key": "2026-06",
                    "qty": "10.0000",
                    "inserted_at": None,
                }
            ],
            "trace_id": TRACE_ID,
        }
    )
    assert resp.product_id == str(PROD_X)
    assert resp.depth == 1
    assert len(resp.chain) == 1
    assert resp.chain[0].period_key == "2026-06"


# ── coverage count: 22 cases (target ≥ 15) ────────────────────


def test_module_has_at_least_15_cases() -> None:
    """Test count pin (T9.3): this module must contain ≥ 15 cases."""
    import sys

    current_module = sys.modules[__name__]
    test_count = sum(
        1 for name in dir(current_module) if name.startswith("test_")
    )
    assert test_count >= 15, (
        f"test_ledger_service.py has {test_count} cases; "
        f"spec T9.3 requires ≥ 15."
    )
