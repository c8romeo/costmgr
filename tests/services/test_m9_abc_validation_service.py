"""tests.services.test_m9_abc_validation_service — Story 9.1.

Service-layer unit tests for `AbcValidationService`. Exercises:
  - validate_100_percent_guard orchestrator delegation (3-layer)
  - validate_cost_pool_only / validate_activity_only / validate_driver_only
    single-layer endpoints
  - CR 12-5 L3 3-layer defense (validate_abc_pct_list) — type / range /
    empty guards
  - _to_validation_state ORM→kernel boundary conversion
  - JSON-safe serializer delegation (CR 11-4 D-002 ko-KR SSOT)
  - fetch_tenant_abc_drivers (Story 1.2 scaffold JSONB re-use)

Mocking strategy:
  - DB session: AsyncMock + MagicMock (no Postgres dependency)
  - SettingsService: AsyncMock returning mocked tenant_settings
  - Typed exceptions: real (no mocking) so envelope contracts are exercised

Async tests use `asyncio.run` pattern (CR 4-3 lessons — no pytest-asyncio).

Kernel-level parity is already covered by
`tests/cost_engine/test_abc_engine.py` (36 tests) +
`tests/cost_engine/test_abc_engine_no_io_imports.py` (5 AST tests) +
`tests/cost_engine/test_abc_engine_determinism.py` (6 V8 tests).
"""

from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.modules.m9_abc.exceptions import (
    ABC_ACTIVITY_INVALID_SUM_KO,
    ABC_COST_POOL_INVALID_SUM_KO,
    ABC_DRIVER_INVALID_SUM_KO,
    ABC_VALIDATION_NOT_FOUND_KO,
)
from apps.api.modules.m9_abc.services.abc_validation_service import (
    ABC_VALIDATION_INDUSTRY_AGNOSTIC,
    AbcValidationService,
    AbcValidationState,
    _to_validation_state,
    validate_abc_pct_list,
)
from packages.cost_engine.abc_engine import (
    AbcValidationNotFoundError,
    ActivityValidation,
    ActivityValidationError,
    CostPoolValidation,
    CostPoolValidationError,
    DriverValidation,
    DriverValidationError,
)
from packages.services.m9_abc.abc_validation_serializers import (
    serialize_validation_state,
)

# ── Test helpers ──────────────────────────────────────────────


def _make_session(
    *,
    drivers: list[dict[str, Any]] | None = None,
) -> AsyncMock:
    """Build a mock AsyncSession + SettingsService chain for fetch_tenant_abc_drivers."""
    session = AsyncMock()
    settings = MagicMock()
    settings.abc = {"drivers": drivers or []}
    settings_service = MagicMock()
    settings_service.get_tenant_settings = AsyncMock(return_value=settings)

    # Patch SettingsService constructor inside the service module to return
    # our mock. Patch via direct attribute swap (monkeypatch style).
    return session


def _patch_settings_service(monkeypatch: pytest.MonkeyPatch, drivers: list[dict[str, Any]]) -> None:
    """Patch SettingsService in abc_validation_service module to return a mock."""

    class _FakeSettingsService:
        def __init__(self, _session: Any) -> None:
            self._session = _session

        async def get_tenant_settings(self, *, tenant_id: uuid.UUID) -> Any:  # noqa: ARG002
            settings = MagicMock()
            settings.abc = {"drivers": drivers}
            return settings

    monkeypatch.setattr(
        "apps.api.modules.m9_abc.services.abc_validation_service.SettingsService",
        _FakeSettingsService,
    )


# ── 1. Module-level constants (industry-agnostic pin) ─────────


def test_abc_validation_industry_agnostic_constant() -> None:
    """9-1 = industry-agnostic (financial baseline per CR 12-1 L4)."""
    assert ABC_VALIDATION_INDUSTRY_AGNOSTIC is True


def test_abc_validation_state_is_frozen() -> None:
    """AbcValidationState must be frozen dataclass (CR 12-1 L3 boundary)."""
    state = AbcValidationState(
        cost_pool=None,
        activity=None,
        driver=None,
        all_valid=False,
        cost_pool_message_ko=None,
        activity_message_ko=None,
        driver_message_ko=None,
    )
    with pytest.raises((AttributeError, TypeError, Exception)):  # frozen check
        state.all_valid = True  # type: ignore[misc]


# ── 2. _to_validation_state boundary conversion (CR 12-1 L3) ──


def test_to_validation_state_all_valid() -> None:
    """All 3 layers valid → all_valid=True, no Korean messages."""
    cost_pool = CostPoolValidation(
        department_id="d1",
        sum_pct=Decimal("100"),
        department_count=4,
        is_valid=True,
        hash="sha256:cp1",
    )
    activity = ActivityValidation(
        cost_pool_id="cp1",
        sum_pct=Decimal("100"),
        activity_count=3,
        is_valid=True,
        hash="sha256:act1",
    )
    driver = DriverValidation(
        activity_id="act1",
        sum_pct=Decimal("100"),
        driver_count=2,
        is_valid=True,
        hash="sha256:drv1",
    )
    state = _to_validation_state(
        {
            "cost_pool": cost_pool,
            "activity": activity,
            "driver": driver,
            "all_valid": True,
        }
    )
    assert state.cost_pool is cost_pool
    assert state.activity is activity
    assert state.driver is driver
    assert state.all_valid is True
    assert state.cost_pool_message_ko is None
    assert state.activity_message_ko is None
    assert state.driver_message_ko is None


def test_to_validation_state_cost_pool_invalid_message() -> None:
    """Cost pool invalid → Korean message includes current sum_pct."""
    cost_pool = CostPoolValidation(
        department_id="d1",
        sum_pct=Decimal("105"),
        department_count=4,
        is_valid=False,
        hash="sha256:cp1",
    )
    state = _to_validation_state(
        {
            "cost_pool": cost_pool,
            "activity": None,
            "driver": None,
            "all_valid": False,
        }
    )
    assert state.all_valid is False
    assert state.cost_pool_message_ko is not None
    assert ABC_COST_POOL_INVALID_SUM_KO in state.cost_pool_message_ko
    assert "105" in state.cost_pool_message_ko


def test_to_validation_state_activity_invalid_message() -> None:
    """Activity invalid → Korean message includes current sum_pct."""
    activity = ActivityValidation(
        cost_pool_id="cp1",
        sum_pct=Decimal("92"),
        activity_count=3,
        is_valid=False,
        hash="sha256:act1",
    )
    state = _to_validation_state(
        {
            "cost_pool": None,
            "activity": activity,
            "driver": None,
            "all_valid": False,
        }
    )
    assert state.all_valid is False
    assert state.activity_message_ko is not None
    assert ABC_ACTIVITY_INVALID_SUM_KO in state.activity_message_ko
    assert "92" in state.activity_message_ko


def test_to_validation_state_driver_invalid_message() -> None:
    """Driver invalid → Korean message includes current sum_pct."""
    driver = DriverValidation(
        activity_id="act1",
        sum_pct=Decimal("80"),
        driver_count=2,
        is_valid=False,
        hash="sha256:drv1",
    )
    state = _to_validation_state(
        {
            "cost_pool": None,
            "activity": None,
            "driver": driver,
            "all_valid": False,
        }
    )
    assert state.all_valid is False
    assert state.driver_message_ko is not None
    assert ABC_DRIVER_INVALID_SUM_KO in state.driver_message_ko
    assert "80" in state.driver_message_ko


def test_to_validation_state_no_inputs() -> None:
    """Empty guard_result → all layers None + all_valid=False."""
    state = _to_validation_state(
        {"cost_pool": None, "activity": None, "driver": None, "all_valid": False}
    )
    assert state.cost_pool is None
    assert state.activity is None
    assert state.driver is None
    assert state.all_valid is False
    assert state.cost_pool_message_ko is None
    assert state.activity_message_ko is None
    assert state.driver_message_ko is None


# ── 3. validate_abc_pct_list — CR 12-5 L3 3-layer defense ──


def test_validate_abc_pct_list_happy_path() -> None:
    """All Decimal in [0, 100] → no raise."""
    validate_abc_pct_list(
        allocation_pcts=[Decimal("25"), Decimal("75")],
        target="cost_pool",
        target_id="d1",
    )  # no exception


def test_validate_abc_pct_list_empty_raises_not_found() -> None:
    """Empty list → AbcValidationNotFoundError (404 envelope)."""
    with pytest.raises(AbcValidationNotFoundError) as exc_info:
        validate_abc_pct_list(
            allocation_pcts=[],
            target="cost_pool",
            target_id="d1",
        )
    assert ABC_VALIDATION_NOT_FOUND_KO in str(exc_info.value)
    assert exc_info.value.target == "cost_pool"


def test_validate_abc_pct_list_non_decimal_type_cost_pool() -> None:
    """Non-Decimal in cost_pool list → CostPoolValidationError."""
    with pytest.raises(CostPoolValidationError) as exc_info:
        validate_abc_pct_list(
            allocation_pcts=[Decimal("50"), "not_a_decimal"],  # type: ignore[list-item]
            target="cost_pool",
            target_id="d1",
        )
    assert exc_info.value.reason == "type_mismatch"


def test_validate_abc_pct_list_non_decimal_type_activity() -> None:
    """Non-Decimal in activity list → ActivityValidationError."""
    with pytest.raises(ActivityValidationError) as exc_info:
        validate_abc_pct_list(
            allocation_pcts=[Decimal("50"), 50],  # type: ignore[list-item]
            target="activity",
            target_id="cp1",
        )
    assert exc_info.value.reason == "type_mismatch"


def test_validate_abc_pct_list_non_decimal_type_driver() -> None:
    """Non-Decimal in driver list → DriverValidationError."""
    with pytest.raises(DriverValidationError) as exc_info:
        validate_abc_pct_list(
            allocation_pcts=[Decimal("50"), None],  # type: ignore[list-item]
            target="driver",
            target_id="act1",
        )
    assert exc_info.value.reason == "type_mismatch"


def test_validate_abc_pct_list_out_of_range_low_cost_pool() -> None:
    """Negative value in cost_pool list → CostPoolValidationError out_of_range."""
    with pytest.raises(CostPoolValidationError) as exc_info:
        validate_abc_pct_list(
            allocation_pcts=[Decimal("-1"), Decimal("101")],
            target="cost_pool",
            target_id="d1",
        )
    assert exc_info.value.reason == "out_of_range"


def test_validate_abc_pct_list_out_of_range_high_activity() -> None:
    """Value > 100 in activity list → ActivityValidationError out_of_range."""
    with pytest.raises(ActivityValidationError) as exc_info:
        validate_abc_pct_list(
            allocation_pcts=[Decimal("150")],
            target="activity",
            target_id="cp1",
        )
    assert exc_info.value.reason == "out_of_range"


def test_validate_abc_pct_list_out_of_range_high_driver() -> None:
    """Value > 100 in driver list → DriverValidationError out_of_range."""
    with pytest.raises(DriverValidationError) as exc_info:
        validate_abc_pct_list(
            allocation_pcts=[Decimal("200")],
            target="driver",
            target_id="act1",
        )
    assert exc_info.value.reason == "out_of_range"


# ── 4. Service orchestration — 3-layer 100% guard ────────────


def test_service_validate_100_percent_guard_all_valid() -> None:
    """All 3 layers sum=100 → all_valid=True, no exceptions."""
    asyncio.run(
        _run_validate_100_percent_guard_all_valid()
    )


async def _run_validate_100_percent_guard_all_valid() -> None:
    service = AbcValidationService(
        session=AsyncMock(),
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-1",
    )
    state = await service.validate_100_percent_guard(
        cost_pool=[Decimal("25"), Decimal("75")],
        activities=[Decimal("50"), Decimal("50")],
        drivers=[Decimal("60"), Decimal("40")],
        cost_pool_id="cp1",
        activity_id="act1",
    )
    assert state.all_valid is True
    assert state.cost_pool is not None
    assert state.cost_pool.is_valid
    assert state.activity is not None
    assert state.activity.is_valid
    assert state.driver is not None
    assert state.driver.is_valid


def test_service_validate_100_percent_guard_cost_pool_invalid() -> None:
    """Cost pool sum != 100 → state.all_valid=False (no raise)."""
    asyncio.run(_run_validate_100_percent_guard_cost_pool_invalid())


async def _run_validate_100_percent_guard_cost_pool_invalid() -> None:
    service = AbcValidationService(
        session=AsyncMock(),
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-1",
    )
    state = await service.validate_100_percent_guard(
        cost_pool=[Decimal("30"), Decimal("75")],  # sum=105
        activities=[Decimal("50"), Decimal("50")],
        drivers=[Decimal("60"), Decimal("40")],
        cost_pool_id="cp1",
        activity_id="act1",
    )
    assert state.all_valid is False
    assert state.cost_pool is not None
    assert not state.cost_pool.is_valid
    assert state.cost_pool_message_ko is not None


def test_service_validate_100_percent_guard_raises_on_empty_cost_pool() -> None:
    """Empty cost_pool list → AbcValidationNotFoundError (CR 12-5 L3)."""
    asyncio.run(_run_validate_100_percent_guard_raises_on_empty())


async def _run_validate_100_percent_guard_raises_on_empty() -> None:
    service = AbcValidationService(
        session=AsyncMock(),
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-1",
    )
    with pytest.raises(AbcValidationNotFoundError):
        await service.validate_100_percent_guard(
            cost_pool=[],
            activities=[Decimal("50"), Decimal("50")],
            drivers=[Decimal("60"), Decimal("40")],
        )


# ── 5. Service single-layer endpoints ────────────────────────


def test_service_validate_cost_pool_only_valid() -> None:
    """validate_cost_pool_only → CostPoolValidation.is_valid=True."""
    asyncio.run(_run_validate_cost_pool_only_valid())


async def _run_validate_cost_pool_only_valid() -> None:
    service = AbcValidationService(
        session=AsyncMock(),
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-1",
    )
    state = await service.validate_cost_pool_only(
        department_id="d1",
        allocation_pcts=[Decimal("50"), Decimal("50")],
    )
    assert state.is_valid is True
    assert state.sum_pct == Decimal("100")
    assert state.department_count == 2


def test_service_validate_cost_pool_only_invalid() -> None:
    """validate_cost_pool_only sum != 100 → CostPoolValidation.is_valid=False."""
    asyncio.run(_run_validate_cost_pool_only_invalid())


async def _run_validate_cost_pool_only_invalid() -> None:
    service = AbcValidationService(
        session=AsyncMock(),
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-1",
    )
    state = await service.validate_cost_pool_only(
        department_id="d1",
        allocation_pcts=[Decimal("60"), Decimal("50")],  # sum=110
    )
    assert state.is_valid is False
    assert state.sum_pct == Decimal("110")


def test_service_validate_cost_pool_only_empty_raises_not_found() -> None:
    """Empty allocation_pcts → AbcValidationNotFoundError (CR 12-5 L3)."""
    asyncio.run(_run_validate_cost_pool_only_empty())


async def _run_validate_cost_pool_only_empty() -> None:
    service = AbcValidationService(
        session=AsyncMock(),
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-1",
    )
    with pytest.raises(AbcValidationNotFoundError):
        await service.validate_cost_pool_only(
            department_id="d1",
            allocation_pcts=[],
        )


def test_service_validate_activity_only_valid() -> None:
    """validate_activity_only → ActivityValidation.is_valid=True."""
    asyncio.run(_run_validate_activity_only_valid())


async def _run_validate_activity_only_valid() -> None:
    service = AbcValidationService(
        session=AsyncMock(),
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-1",
    )
    state = await service.validate_activity_only(
        cost_pool_id="cp1",
        activity_pcts=[Decimal("33.33"), Decimal("33.33"), Decimal("33.34")],
    )
    assert state.is_valid is True
    assert state.activity_count == 3


def test_service_validate_driver_only_valid() -> None:
    """validate_driver_only → DriverValidation.is_valid=True."""
    asyncio.run(_run_validate_driver_only_valid())


async def _run_validate_driver_only_valid() -> None:
    service = AbcValidationService(
        session=AsyncMock(),
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-1",
    )
    state = await service.validate_driver_only(
        activity_id="act1",
        driver_pcts=[Decimal("100")],
    )
    assert state.is_valid is True
    assert state.driver_count == 1


# ── 6. JSON-safe serializer delegation (CR 11-4 D-002) ───────


def test_serialize_validation_state_cost_pool() -> None:
    """CostPoolValidation → JSON-safe dict (Decimal-as-string)."""
    state = CostPoolValidation(
        department_id="d1",
        sum_pct=Decimal("100"),
        department_count=4,
        is_valid=True,
        hash="sha256:abc",
    )
    serialized = serialize_validation_state(state)
    assert serialized["department_id"] == "d1"
    assert serialized["sum_pct"] == "100"
    assert serialized["department_count"] == 4
    assert serialized["is_valid"] is True
    assert serialized["hash"] == "sha256:abc"


def test_serialize_validation_state_activity() -> None:
    """ActivityValidation → JSON-safe dict."""
    state = ActivityValidation(
        cost_pool_id="cp1",
        sum_pct=Decimal("100"),
        activity_count=3,
        is_valid=True,
        hash="sha256:xyz",
    )
    serialized = serialize_validation_state(state)
    assert serialized["cost_pool_id"] == "cp1"
    assert serialized["sum_pct"] == "100"
    assert serialized["activity_count"] == 3


def test_serialize_validation_state_driver() -> None:
    """DriverValidation → JSON-safe dict."""
    state = DriverValidation(
        activity_id="act1",
        sum_pct=Decimal("100"),
        driver_count=2,
        is_valid=True,
        hash="sha256:drv",
    )
    serialized = serialize_validation_state(state)
    assert serialized["activity_id"] == "act1"
    assert serialized["driver_count"] == 2


def test_serialize_validation_state_invalid_type_raises() -> None:
    """Non-ValidationState input → ValueError."""
    with pytest.raises(ValueError, match="CostPoolValidation"):
        serialize_validation_state("not a state")  # type: ignore[arg-type]


# ── 7. fetch_tenant_abc_drivers (Story 1.2 scaffold re-use) ─


def test_fetch_tenant_abc_drivers_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """No drivers in tenant_settings.abc → empty list."""
    _patch_settings_service(monkeypatch, drivers=[])
    asyncio.run(_run_fetch_empty())


async def _run_fetch_empty() -> None:
    service = AbcValidationService(
        session=AsyncMock(),
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-1",
    )
    drivers = await service.fetch_tenant_abc_drivers()
    assert drivers == []


def test_fetch_tenant_abc_drivers_returns_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """Drivers stored in tenant_settings.abc.drivers → list of dicts."""
    sample = [
        {
            "driver_name": "Machine Hours",
            "unit": "hours",
            "practical_capacity_hours": 8000,
        }
    ]
    _patch_settings_service(monkeypatch, drivers=sample)
    asyncio.run(_run_fetch_returns(sample))


async def _run_fetch_returns(expected: list[dict[str, Any]]) -> None:
    service = AbcValidationService(
        session=AsyncMock(),
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-1",
    )
    drivers = await service.fetch_tenant_abc_drivers()
    assert drivers == expected


# ── 8. Constructor pinning (CR 11-3 D-2 ALLOWED_SUBMODULES) ─


def test_service_init_stores_fields() -> None:
    """AbcValidationService.__init__ stores all 4 fields verbatim."""
    session = AsyncMock()
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    trace_id = "trace-test-001"
    service = AbcValidationService(
        session=session,
        tenant_id=tenant_id,
        actor_id=actor_id,
        trace_id=trace_id,
    )
    assert service.session is session
    assert service.tenant_id == tenant_id
    assert service.actor_id == actor_id
    assert service.trace_id == trace_id
