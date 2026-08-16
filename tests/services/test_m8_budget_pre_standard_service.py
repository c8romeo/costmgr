"""tests.services.test_m8_budget_pre_standard_service — Story 8.3.

Service-layer unit tests for `BudgetPreStandardService`. These tests
exercise the pure-kernel delegation + DB I/O orchestration +
idempotency via UNIQUE constraint + ORM→kernel boundary conversion
(CR 12-1 L3 precedent).

Mocking strategy:
  - DB session: AsyncMock + MagicMock (no Postgres dependency)
  - FiscalPeriodSnapshot ORM: MagicMock with all required fields
  - IntegrityError: simulated race condition test

Kernel-level parity is already covered by
`tests/cost_engine/test_budget_pre_standard.py` (28 tests).

Async tests use `asyncio.run` pattern (CR 4-3 lessons — no pytest-asyncio).
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from apps.api.modules.m8_budget.exceptions import (
    BudgetVariancePdfNotReadyError,
    InvalidPreStandardInputError,
    PreStandardAlreadyExistsError,
    PreStandardSnapshotNotFoundError,
)
from apps.api.modules.m8_budget.services.budget_pre_standard_service import (
    BUDGET_PRE_STANDARD_INDUSTRY_AGNOSTIC,
    BudgetPreStandardService,
    PreStandardSnapshotState,
    VIRTUAL_BUDGET_PERIOD_KEY_PATTERN_PRE_STANDARD,
    _to_pre_standard_cost_state,
    validate_pre_standard_inputs,
)
from packages.cost_engine.budget_pre_standard import (
    PRE_STANDARD_DEFAULT_BASELINE_REVISION,
    PRE_STANDARD_ENGINE_TYPE,
    PRE_STANDARD_STATE_VERIFIED,
    PreStandardCost,
    compute_pre_standard_cost,
    compute_pre_standard_hash,
)


# ── Test helpers ──────────────────────────────────────────────


def _make_orm_snapshot(
    *,
    snapshot_id: uuid.UUID | None = None,
    tenant_id: uuid.UUID | None = None,
    period_key: str = "2026-07#B1",
    baseline_revision: int = PRE_STANDARD_DEFAULT_BASELINE_REVISION,
    engine_type: str = PRE_STANDARD_ENGINE_TYPE,
    material_cost: int = 10000,
    labor_cost: int = 40000,
    overhead_cost: int = 8000,
    manufacturing_cost: int = 58000,
    inventory_adjustment: int = 0,
    result_hash: str = "sha256:abc123",
    state: str = PRE_STANDARD_STATE_VERIFIED,
    created_at: datetime | None = None,
) -> Any:
    """Build a mock FiscalPeriodSnapshot ORM row."""
    row = MagicMock()
    row.snapshot_id = snapshot_id or uuid.uuid4()
    row.tenant_id = tenant_id or uuid.uuid4()
    row.period_key = period_key
    row.baseline_revision = baseline_revision
    row.engine_type = engine_type
    row.material_cost = material_cost
    row.labor_cost = labor_cost
    row.overhead_cost = overhead_cost
    row.manufacturing_cost = manufacturing_cost
    row.inventory_adjustment = inventory_adjustment
    row.result_hash = result_hash
    row.state = state
    row.created_at = created_at or datetime.now(UTC)
    return row


def _make_session(
    *,
    existing_snapshot: Any = None,
    flush_raises: Exception | None = None,
) -> AsyncMock:
    """Build a mock AsyncSession with controllable snapshot lookup."""
    session = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = existing_snapshot
    session.execute = AsyncMock(return_value=execute_result)

    if flush_raises is not None:
        session.flush = AsyncMock(side_effect=flush_raises)
    else:
        session.flush = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session


def _make_service(
    *,
    existing_snapshot: Any = None,
    flush_raises: Exception | None = None,
) -> tuple[BudgetPreStandardService, AsyncMock]:
    """Build a service with a mock session."""
    session = _make_session(
        existing_snapshot=existing_snapshot,
        flush_raises=flush_raises,
    )
    service = BudgetPreStandardService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-pre-standard-001",
    )
    return service, session


# ── validate_pre_standard_inputs tests ─────────────────────────


def test_validate_pre_standard_inputs_accepts_valid() -> None:
    """Valid inputs → no raise."""
    validate_pre_standard_inputs(
        period_key="2026-07#B1",
        material_unit_cost=Decimal("1000"),
        labor_unit_cost=Decimal("5000"),
        overhead_rate=Decimal("20"),
        material_qty=Decimal("10"),
        labor_hours=Decimal("8"),
    )
    # No exception raised → success.


def test_validate_pre_standard_inputs_rejects_negative_cost() -> None:
    """material_unit_cost < 0 → InvalidPreStandardInputError."""
    with pytest.raises(InvalidPreStandardInputError) as exc_info:
        validate_pre_standard_inputs(
            period_key="2026-07#B1",
            material_unit_cost=Decimal("-1"),
            labor_unit_cost=Decimal("5000"),
            overhead_rate=Decimal("20"),
            material_qty=Decimal("10"),
            labor_hours=Decimal("8"),
        )
    assert exc_info.value.field == "material_unit_cost"
    assert exc_info.value.reason == "negative_value"


def test_validate_pre_standard_inputs_rejects_overhead_rate_over_100() -> None:
    """overhead_rate > 100 → InvalidPreStandardInputError."""
    with pytest.raises(InvalidPreStandardInputError) as exc_info:
        validate_pre_standard_inputs(
            period_key="2026-07#B1",
            material_unit_cost=Decimal("1000"),
            labor_unit_cost=Decimal("5000"),
            overhead_rate=Decimal("101"),
            material_qty=Decimal("10"),
            labor_hours=Decimal("8"),
        )
    assert exc_info.value.field == "overhead_rate"
    assert exc_info.value.reason == "exceeds_max"


def test_validate_pre_standard_inputs_rejects_invalid_period_key() -> None:
    """invalid period_key → InvalidPreStandardInputError."""
    with pytest.raises(InvalidPreStandardInputError) as exc_info:
        validate_pre_standard_inputs(
            period_key="2026-07",
            material_unit_cost=Decimal("1000"),
            labor_unit_cost=Decimal("5000"),
            overhead_rate=Decimal("20"),
            material_qty=Decimal("10"),
            labor_hours=Decimal("8"),
        )
    assert exc_info.value.field == "period_key"
    assert "period_key must match YYYY-MM#B<n>" in exc_info.value.reason


def test_validate_pre_standard_inputs_accepts_zero_overhead() -> None:
    """overhead_rate == 0 → OK (no overhead applied)."""
    validate_pre_standard_inputs(
        period_key="2026-07#B1",
        material_unit_cost=Decimal("1000"),
        labor_unit_cost=Decimal("5000"),
        overhead_rate=Decimal("0"),
        material_qty=Decimal("10"),
        labor_hours=Decimal("8"),
    )


def test_validate_pre_standard_inputs_accepts_overhead_100() -> None:
    """overhead_rate == 100 → OK (edge case)."""
    validate_pre_standard_inputs(
        period_key="2026-07#B1",
        material_unit_cost=Decimal("1000"),
        labor_unit_cost=Decimal("5000"),
        overhead_rate=Decimal("100"),
        material_qty=Decimal("10"),
        labor_hours=Decimal("8"),
    )


# ── compute_pre_standard_snapshot tests ────────────────────────


def test_compute_pre_standard_snapshot_inserts_new_row() -> None:
    """No existing snapshot → INSERT new row + return PreStandardSnapshotState."""
    service, session = _make_service(existing_snapshot=None)

    state = asyncio.run(
        service.compute_pre_standard_snapshot(
            period_key="2026-07#B1",
            material_unit_cost=Decimal("1000"),
            labor_unit_cost=Decimal("5000"),
            overhead_rate=Decimal("20"),
            material_qty=Decimal("10"),
            labor_hours=Decimal("8"),
        )
    )

    assert isinstance(state, PreStandardSnapshotState)
    assert state.pre_standard_cost.engine_type == "budget"
    assert state.state == PRE_STANDARD_STATE_VERIFIED
    assert state.inventory_adjustment == 0
    assert state.result_hash.startswith("sha256:")
    assert session.add.called
    assert session.flush.called


def test_compute_pre_standard_snapshot_idempotent_same_hash() -> None:
    """Same hash → idempotent skip (no new INSERT)."""
    # Compute the expected hash for the inputs.
    pre_standard_cost = compute_pre_standard_cost(
        material_unit_cost=Decimal("1000"),
        labor_unit_cost=Decimal("5000"),
        overhead_rate=Decimal("20"),
        material_qty=Decimal("10"),
        labor_hours=Decimal("8"),
        period_key="2026-07#B1",
    )
    expected_hash = compute_pre_standard_hash(pre_standard_cost=pre_standard_cost)

    existing = _make_orm_snapshot(
        result_hash=expected_hash,
        material_cost=10000,
        labor_cost=40000,
        overhead_cost=8000,
        manufacturing_cost=58000,
    )
    service, session = _make_service(existing_snapshot=existing)

    state = asyncio.run(
        service.compute_pre_standard_snapshot(
            period_key="2026-07#B1",
            material_unit_cost=Decimal("1000"),
            labor_unit_cost=Decimal("5000"),
            overhead_rate=Decimal("20"),
            material_qty=Decimal("10"),
            labor_hours=Decimal("8"),
        )
    )

    # Same hash → idempotent skip (no session.add).
    assert not session.add.called
    assert state.result_hash == expected_hash


def test_compute_pre_standard_snapshot_raises_on_different_hash() -> None:
    """Different hash → PreStandardAlreadyExistsError (409 envelope)."""
    existing = _make_orm_snapshot(
        result_hash="sha256:different_hash",
    )
    service, _ = _make_service(existing_snapshot=existing)

    with pytest.raises(PreStandardAlreadyExistsError) as exc_info:
        asyncio.run(
            service.compute_pre_standard_snapshot(
                period_key="2026-07#B1",
                material_unit_cost=Decimal("1000"),
                labor_unit_cost=Decimal("5000"),
                overhead_rate=Decimal("20"),
                material_qty=Decimal("10"),
                labor_hours=Decimal("8"),
            )
        )
    assert exc_info.value.period_key == "2026-07#B1"
    assert exc_info.value.existing_hash == "sha256:different_hash"


def test_compute_pre_standard_snapshot_race_condition_integrity_error() -> None:
    """Concurrent INSERT → IntegrityError → PreStandardAlreadyExistsError."""
    service, _ = _make_service(
        existing_snapshot=None,
        flush_raises=IntegrityError("INSERT", {}, Exception("UNIQUE violation")),
    )

    with pytest.raises(PreStandardAlreadyExistsError):
        asyncio.run(
            service.compute_pre_standard_snapshot(
                period_key="2026-07#B1",
                material_unit_cost=Decimal("1000"),
                labor_unit_cost=Decimal("5000"),
                overhead_rate=Decimal("20"),
                material_qty=Decimal("10"),
                labor_hours=Decimal("8"),
            )
        )


def test_compute_pre_standard_snapshot_rejects_invalid_input() -> None:
    """Invalid input → InvalidPreStandardInputError (no DB I/O)."""
    service, session = _make_service()

    with pytest.raises(InvalidPreStandardInputError):
        asyncio.run(
            service.compute_pre_standard_snapshot(
                period_key="2026-07#B1",
                material_unit_cost=Decimal("-1"),
                labor_unit_cost=Decimal("5000"),
                overhead_rate=Decimal("20"),
                material_qty=Decimal("10"),
                labor_hours=Decimal("8"),
            )
        )
    assert not session.add.called


# ── fetch_pre_standard_snapshot tests ────────────────────────


def test_fetch_pre_standard_snapshot_returns_state() -> None:
    """Existing snapshot → returns PreStandardSnapshotState."""
    existing = _make_orm_snapshot()
    service, _ = _make_service(existing_snapshot=existing)

    state = asyncio.run(
        service.fetch_pre_standard_snapshot(period_key="2026-07#B1")
    )

    assert state.pre_standard_cost.engine_type == "budget"
    assert state.state == PRE_STANDARD_STATE_VERIFIED


def test_fetch_pre_standard_snapshot_not_found() -> None:
    """No snapshot → PreStandardSnapshotNotFoundError (404 envelope)."""
    service, _ = _make_service(existing_snapshot=None)

    with pytest.raises(PreStandardSnapshotNotFoundError) as exc_info:
        asyncio.run(
            service.fetch_pre_standard_snapshot(period_key="2026-07#B1")
        )
    assert exc_info.value.period_key == "2026-07#B1"


def test_fetch_pre_standard_snapshot_invalid_period_key() -> None:
    """Invalid period_key → InvalidPreStandardInputError (422 envelope)."""
    service, _ = _make_service()

    with pytest.raises(InvalidPreStandardInputError):
        asyncio.run(
            service.fetch_pre_standard_snapshot(period_key="2026-07")
        )


def test_fetch_pre_standard_snapshot_wrong_engine_type() -> None:
    """Wrong engine_type → PreStandardSnapshotNotFoundError (defense-in-depth)."""
    existing = _make_orm_snapshot(engine_type="trad")
    service, _ = _make_service(existing_snapshot=existing)

    with pytest.raises(PreStandardSnapshotNotFoundError):
        asyncio.run(
            service.fetch_pre_standard_snapshot(period_key="2026-07#B1")
        )


# ── ORM → kernel boundary conversion tests ────────────────────


def test_to_pre_standard_cost_state_round_trip() -> None:
    """ORM → PreStandardSnapshotState boundary conversion."""
    existing = _make_orm_snapshot(
        material_cost=10000,
        labor_cost=40000,
        overhead_cost=8000,
        manufacturing_cost=58000,
    )
    state = _to_pre_standard_cost_state(existing)

    assert isinstance(state.pre_standard_cost, PreStandardCost)
    assert state.pre_standard_cost.material_cost == Decimal("10000")
    assert state.pre_standard_cost.labor_cost == Decimal("40000")
    assert state.pre_standard_cost.overhead_cost == Decimal("8000")
    assert state.pre_standard_cost.manufacturing_cost == Decimal("58000")
    assert state.pre_standard_cost.engine_type == "budget"
    assert state.inventory_adjustment == 0
    assert state.state == PRE_STANDARD_STATE_VERIFIED


def test_to_pre_standard_cost_state_preserves_decimal_precision() -> None:
    """Decimal precision preserved at ORM boundary."""
    existing = _make_orm_snapshot(
        material_cost=123457,
        labor_cost=400000,
        overhead_cost=80000,
        manufacturing_cost=603457,
    )
    state = _to_pre_standard_cost_state(existing)
    assert state.pre_standard_cost.manufacturing_cost == Decimal("603457")


# ── PDF generation tests (8-2 wire EXTENSION activation) ──────


def test_generate_budget_pre_standard_pdf_no_snapshot_raises() -> None:
    """No pre-standard snapshot → BudgetVariancePdfNotReadyError (425)."""
    service, _ = _make_service(existing_snapshot=None)

    with pytest.raises(BudgetVariancePdfNotReadyError):
        asyncio.run(
            service.generate_budget_pre_standard_pdf(period_key="2026-07#B1")
        )


def test_generate_budget_pre_standard_pdf_returns_bytes() -> None:
    """Existing snapshot → returns PDF bytes (A4 portrait + ko-KR)."""
    existing = _make_orm_snapshot()
    service, _ = _make_service(existing_snapshot=existing)

    pdf_bytes = asyncio.run(
        service.generate_budget_pre_standard_pdf(period_key="2026-07#B1")
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    # PDF magic header.
    assert pdf_bytes.startswith(b"%PDF-1.7")


def test_generate_budget_variance_pdf_delegates_to_pre_standard() -> None:
    """8-2 wire EXTENSION: BudgetVarianceService delegates to PreStandard service."""
    existing = _make_orm_snapshot()
    service, _ = _make_service(existing_snapshot=existing)

    pdf_bytes = asyncio.run(
        service.generate_budget_variance_pdf(period_key="2026-07#B1")
    )

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-1.7")


def test_generate_budget_variance_pdf_no_snapshot_raises_425() -> None:
    """No pre-standard snapshot → BudgetVariancePdfNotReadyError (425)."""
    service, _ = _make_service(existing_snapshot=None)

    with pytest.raises(BudgetVariancePdfNotReadyError):
        asyncio.run(
            service.generate_budget_variance_pdf(period_key="2026-07#B1")
        )


# ── Constants tests ─────────────────────────────────────────────


def test_industry_agnostic_flag() -> None:
    """BUDGET_PRE_STANDARD_INDUSTRY_AGNOSTIC = True (12-1 L4 precedent)."""
    assert BUDGET_PRE_STANDARD_INDUSTRY_AGNOSTIC is True


def test_period_key_pattern_pattern() -> None:
    """VIRTUAL_BUDGET_PERIOD_KEY_PATTERN_PRE_STANDARD matches AD-24."""
    assert VIRTUAL_BUDGET_PERIOD_KEY_PATTERN_PRE_STANDARD == (
        r"^\d{4}-(0[1-9]|1[0-2])#B([1-9]\d*)$"
    )
