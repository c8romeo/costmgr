"""tests.services.test_m8_budget_scenario_service — Story 8.1.

Service-layer unit tests for `BudgetScenarioService`. These tests
exercise the pure-kernel delegation + DB UNIQUE constraint
defense-in-depth (CR 12-5 L3 3-layer defense) without spinning up a
real Postgres connection — the service layer is mocked at the
session boundary.

Kernel-level parity is already covered by
`tests/cost_engine/test_budget_period_key.py` (41 tests).

Async tests use `asyncio.run` pattern (CR 4-3 lessons — no pytest-asyncio).

CR 11-3 honest-DEFER discipline: full DB integration tests are
deferred to a future follow-up sprint (D-8-1-DEFER-1) — this service
test covers the orchestration logic + pure-kernel delegation
sufficiently for 8.1 atomic wire close-out.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.modules.m8_budget.exceptions import BudgetScenarioNotFoundError
from apps.api.modules.m8_budget.services.budget_scenario_service import (
    BudgetScenarioService,
)
from packages.cost_engine.budget_period_key import (
    REAL_PERIOD_KEY_PATTERN,
    SCENARIO_HASH_PREFIX,
    VIRTUAL_BUDGET_PERIOD_KEY_PATTERN,
    BudgetScenario,
    InvalidVirtualBudgetPeriodKeyError,
    ScenarioLimitExceededError,
    compute_budget_scenario_hash,
    derive_budget_period_key,
)


def _make_orm_row(
    *,
    scenario_id: uuid.UUID | None = None,
    tenant_id: uuid.UUID | None = None,
    period_key: str = "2026-07#B1",
    real_period_key: str = "2026-07",
    scenario_index: int = 1,
    scenario_hash: str = "sha256:abc123",
    created_by: uuid.UUID | None = None,
    created_at_kst: datetime | None = None,
) -> Any:
    """Build a mock ORM row (avoid DB dependency)."""
    row = MagicMock()
    row.id = scenario_id or uuid.uuid4()
    row.tenant_id = tenant_id or uuid.uuid4()
    row.period_key = period_key
    row.real_period_key = real_period_key
    row.scenario_index = scenario_index
    row.scenario_hash = scenario_hash
    row.created_by = created_by or uuid.uuid4()
    row.created_at_kst = created_at_kst or datetime.now(UTC)
    return row


def _make_session(
    *,
    select_results: list[Any] | None = None,
    scalar_one_or_none_result: Any = None,
    flush_raises: Exception | None = None,
) -> AsyncMock:
    """Build a mock AsyncSession with controllable query results."""
    session = AsyncMock()
    execute_result = MagicMock()
    if select_results is not None:
        execute_result.scalars.return_value.all.return_value = select_results
    execute_result.scalar_one_or_none.return_value = scalar_one_or_none_result
    session.execute = AsyncMock(return_value=execute_result)
    if flush_raises is not None:
        session.flush = AsyncMock(side_effect=flush_raises)
    else:
        session.flush = AsyncMock()
    session.add = MagicMock()
    session.rollback = AsyncMock()
    return session


def test_create_scenario_happy_path() -> None:
    """Service `create_scenario` derives period_key + delegates to kernel."""
    session = _make_session(select_results=[])
    service = BudgetScenarioService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-001",
    )

    kernel = asyncio.run(service.create_scenario(real_period_key="2026-07"))

    assert kernel.period_key == "2026-07#B1"
    assert kernel.real_period_key == "2026-07"
    assert kernel.scenario_index == 1
    assert kernel.tenant_id
    assert kernel.created_at_kst


def test_create_scenario_existing_count_zero_allows_first() -> None:
    """`existing_count == 0` → first scenario allowed (1차 MVP lock)."""
    session = _make_session(select_results=[])
    service = BudgetScenarioService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-002",
    )

    asyncio.run(service.create_scenario(real_period_key="2026-08"))

    session.add.assert_called_once()


def test_create_scenario_existing_count_one_raises_limit_exceeded() -> None:
    """`existing_count >= 1` → ScenarioLimitExceededError (1차 MVP 한도)."""
    existing_row = _make_orm_row(period_key="2026-07#B1")
    session = _make_session(select_results=[existing_row])
    service = BudgetScenarioService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-003",
    )

    with pytest.raises(ScenarioLimitExceededError) as exc_info:
        asyncio.run(service.create_scenario(real_period_key="2026-08"))

    assert exc_info.value.existing_count == 1
    session.add.assert_not_called()


def test_create_scenario_invalid_real_period_key_raises_value_error() -> None:
    """Invalid real_period_key pattern → ValueError (delegated from kernel)."""
    session = _make_session(select_results=[])
    service = BudgetScenarioService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-004",
    )

    with pytest.raises(ValueError, match="real_period_key"):
        asyncio.run(service.create_scenario(real_period_key="invalid"))


def test_create_scenario_db_unique_violation_translates_to_limit_error() -> None:
    """DB IntegrityError (race condition) → ScenarioLimitExceededError (CR 12-5 L3)."""
    from sqlalchemy.exc import IntegrityError

    session = _make_session(
        select_results=[],
        flush_raises=IntegrityError("mock", {}, Exception("unique violation")),
    )
    service = BudgetScenarioService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-005",
    )

    with pytest.raises(ScenarioLimitExceededError):
        asyncio.run(service.create_scenario(real_period_key="2026-07"))


def test_list_scenarios_returns_kernels() -> None:
    """`list_scenarios` returns kernels (ORM → kernel boundary conversion)."""
    row = _make_orm_row(period_key="2026-07#B1")
    session = _make_session(select_results=[row])
    service = BudgetScenarioService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-006",
    )

    kernels = asyncio.run(service.list_scenarios())

    assert len(kernels) == 1
    assert kernels[0].period_key == "2026-07#B1"
    assert kernels[0].real_period_key == "2026-07"
    assert kernels[0].scenario_index == 1


def test_list_scenarios_empty_returns_empty_list() -> None:
    """No scenarios → empty list (no exception)."""
    session = _make_session(select_results=[])
    service = BudgetScenarioService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-007",
    )

    kernels = asyncio.run(service.list_scenarios())

    assert kernels == []


def test_get_scenario_returns_kernel() -> None:
    """`get_scenario(period_key)` returns kernel when row exists."""
    row = _make_orm_row(period_key="2026-07#B1")
    session = _make_session(scalar_one_or_none_result=row)
    service = BudgetScenarioService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-008",
    )

    kernel = asyncio.run(service.get_scenario(period_key="2026-07#B1"))

    assert kernel.period_key == "2026-07#B1"
    assert kernel.scenario_index == 1


def test_get_scenario_not_found_raises_typed_exception() -> None:
    """Row missing → BudgetScenarioNotFoundError (CR 12-5 D-14 envelope 404)."""
    session = _make_session(scalar_one_or_none_result=None)
    service = BudgetScenarioService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-009",
    )

    with pytest.raises(BudgetScenarioNotFoundError) as exc_info:
        asyncio.run(service.get_scenario(period_key="2026-08#B1"))

    assert exc_info.value.period_key == "2026-08#B1"


def test_get_scenario_invalid_period_key_raises_typed_exception() -> None:
    """Invalid period_key → InvalidVirtualBudgetPeriodKeyError (kernel delegation)."""
    session = _make_session(scalar_one_or_none_result=None)
    service = BudgetScenarioService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-010",
    )

    with pytest.raises(InvalidVirtualBudgetPeriodKeyError):
        asyncio.run(service.get_scenario(period_key="not-virtual-format"))


# ── Kernel delegation unit tests ─────────────────────────────────
def test_kernel_derive_budget_period_key() -> None:
    """Pure kernel `derive_budget_period_key` — sanity check at service surface."""
    assert derive_budget_period_key(real_period_key="2026-07") == "2026-07#B1"


def test_kernel_compute_budget_scenario_hash_prefix() -> None:
    """Hash digest is sha256:32hex (V8 determinism)."""
    scenario = BudgetScenario(
        id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        period_key="2026-07#B1",
        real_period_key="2026-07",
        scenario_index=1,
        created_by=str(uuid.uuid4()),
        created_at_kst="2026-08-15T00:00:00+00:00",
    )
    digest = compute_budget_scenario_hash(scenario=scenario)
    assert digest.startswith(SCENARIO_HASH_PREFIX)
    # sha256: prefix (7 chars) + 64 hex chars
    assert len(digest) == len(SCENARIO_HASH_PREFIX) + 64


def test_kernel_pattern_constants_match_spec() -> None:
    """Pattern constants lock to AD-24 verbatim (CR 11-3 drift guard)."""
    assert REAL_PERIOD_KEY_PATTERN == r"^\d{4}-(0[1-9]|1[0-2])$"
    assert VIRTUAL_BUDGET_PERIOD_KEY_PATTERN == (
        r"^(\d{4})-(0[1-9]|1[0-2])#B([1-9]\d*)$"
    )
