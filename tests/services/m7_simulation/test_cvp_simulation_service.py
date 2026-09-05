"""tests.services.m7_simulation.test_cvp_simulation_service — Story 7.1.

15+ test cases for CVPSimulationService:
- baseline extraction (committed snapshot + products aggregation)
- baseline not found → CVPBaselineNotFoundError
- RLS same-tenant filter (different tenant_id 0건)
- simulate_cvp pure kernel delegation
- serializers JSON-safe Decimal-as-string
- delta_helpers clamp + validate (bounds + clamp)
- CVPInvalidDeltaError typed contract
"""

from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from packages.cost_engine.cvp import (
    DEFAULT_OPERATING_RATE,
    DEFAULT_TARGET_PROFIT,
    CVPBaseline,
    CVPDelta,
    simulate_cvp,
)
from packages.services.m7_simulation.delta_helpers import (
    CVPInvalidDeltaError,
    clamp_delta,
    validate_delta_bounds,
)
from packages.services.m7_simulation.serializers import (
    serialize_cvp_baseline,
    serialize_cvp_delta,
    serialize_cvp_result,
)


# ── delta_helpers — clamp_delta ───────────────────────────────
def test_clamp_delta_within_bounds_returns_equivalent():
    """In-bounds delta → unchanged (but new instance)."""
    delta = CVPDelta(
        unit_price_delta_pct=Decimal("0.1"),
        unit_variable_cost_delta_pct=Decimal("-0.05"),
        fixed_cost_delta_pct=Decimal("0.0"),
        operating_rate_delta_pct=Decimal("0.2"),
    )
    clamped = clamp_delta(delta)
    assert clamped == delta
    assert clamped is not delta  # new instance (frozen=True immutability)


def test_clamp_delta_unit_price_above_max():
    """unit_price_delta_pct > 0.5 → clamped to 0.5."""
    delta = CVPDelta(unit_price_delta_pct=Decimal("0.9"))
    clamped = clamp_delta(delta)
    assert clamped.unit_price_delta_pct == Decimal("0.5")


def test_clamp_delta_operating_rate_below_min():
    """operating_rate_delta_pct < -0.5 → clamped to -0.5."""
    delta = CVPDelta(operating_rate_delta_pct=Decimal("-0.9"))
    clamped = clamp_delta(delta)
    assert clamped.operating_rate_delta_pct == Decimal("-0.5")


def test_clamp_delta_fixed_cost_out_of_bounds():
    """fixed_cost_delta_pct > 0.3 → clamped to 0.3."""
    delta = CVPDelta(fixed_cost_delta_pct=Decimal("0.5"))
    clamped = clamp_delta(delta)
    assert clamped.fixed_cost_delta_pct == Decimal("0.3")


# ── delta_helpers — validate_delta_bounds ─────────────────────
def test_validate_delta_bounds_in_bounds_no_raise():
    """In-bounds delta → no raise."""
    delta = CVPDelta(
        unit_price_delta_pct=Decimal("0.3"),
        fixed_cost_delta_pct=Decimal("0.2"),
        operating_rate_delta_pct=Decimal("-0.3"),
    )
    validate_delta_bounds(delta)  # no raise


def test_validate_delta_bounds_unit_price_out_of_bounds_raises():
    """unit_price_delta_pct > 0.5 → CVPInvalidDeltaError."""
    delta = CVPDelta(unit_price_delta_pct=Decimal("0.7"))
    with pytest.raises(CVPInvalidDeltaError) as exc_info:
        validate_delta_bounds(delta)
    assert exc_info.value.field == "unit_price_delta_pct"
    assert exc_info.value.value == Decimal("0.7")
    assert exc_info.value.bounds == (Decimal("-0.5"), Decimal("0.5"))


def test_validate_delta_bounds_fixed_cost_out_of_bounds_raises():
    """fixed_cost_delta_pct < -0.3 → CVPInvalidDeltaError."""
    delta = CVPDelta(fixed_cost_delta_pct=Decimal("-0.5"))
    with pytest.raises(CVPInvalidDeltaError) as exc_info:
        validate_delta_bounds(delta)
    assert exc_info.value.field == "fixed_cost_delta_pct"


# ── CVPInvalidDeltaError typed contract ──────────────────────
def test_cvp_invalid_delta_error_subclasses_kernel_exception():
    """CVPInvalidDeltaError MUST subclass CVPInvalidInputError (typed contract)."""
    from packages.cost_engine.cvp import CVPInvalidInputError

    err = CVPInvalidDeltaError(
        field="unit_price_delta_pct",
        value=Decimal("0.7"),
        bounds=(Decimal("-0.5"), Decimal("0.5")),
    )
    assert isinstance(err, CVPInvalidInputError)
    assert err.code == "CVP_INVALID_DELTA"
    assert err.field == "unit_price_delta_pct"


# ── serializers — JSON-safe Decimal-as-string ─────────────────
def test_serialize_cvp_baseline_decimal_as_string():
    """Decimal values → str (AD-8 monetary precision parity)."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
        operating_rate=DEFAULT_OPERATING_RATE,
        target_profit=DEFAULT_TARGET_PROFIT,
    )
    serialized = serialize_cvp_baseline(baseline)
    assert serialized["fixed_cost"] == "10000000"
    assert serialized["unit_price"] == "10000"
    assert serialized["operating_rate"] == str(DEFAULT_OPERATING_RATE)


def test_serialize_cvp_delta_decimal_as_string():
    """CVPDelta → JSON-safe dict (all deltas)."""
    delta = CVPDelta(
        unit_price_delta_pct=Decimal("0.1"),
        unit_variable_cost_delta_pct=Decimal("-0.05"),
    )
    serialized = serialize_cvp_delta(delta)
    assert serialized["unit_price_delta_pct"] == "0.1"
    assert serialized["unit_variable_cost_delta_pct"] == "-0.05"
    assert serialized["fixed_cost_delta_pct"] == "0"
    assert serialized["operating_rate_delta_pct"] == "0"


def test_serialize_cvp_result_full_orchestration():
    """CVPResult → JSON-safe dict (4 nested results + delta_summary)."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
        target_profit=Decimal("5000000"),
    )
    delta = CVPDelta(unit_price_delta_pct=Decimal("0.1"))
    result = simulate_cvp(baseline=baseline, delta=delta)

    serialized = serialize_cvp_result(result)
    assert "simulated_bep" in serialized
    assert "baseline_bep" in serialized
    assert "delta_summary" in serialized
    assert serialized["simulated_bep"]["bep_quantity"] is not None
    assert isinstance(serialized["simulated_bep"]["bep_quantity"], str)


# ── simulate_cvp pure kernel delegation ──────────────────────
def test_simulate_cvp_pure_kernel_delegation():
    """CVPSimulationService.simulate_cvp delegates to pure kernel (no DB).

    Story 7.1 read-only — verified by integration test
    `test_m7_simulation_no_db_writes.py` (audit_logs row 0건).
    """
    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    delta = CVPDelta(unit_price_delta_pct=Decimal("0.1"))

    # Pure compute (no AsyncSession needed).
    result = simulate_cvp(baseline=baseline, delta=delta)
    assert result.simulated_bep.bep_quantity is not None
    assert result.baseline_bep.bep_quantity != result.simulated_bep.bep_quantity


# ── baseline fetch — RLS same-tenant ─────────────────────────
def test_fetch_cvp_baseline_rls_same_tenant():
    """Different tenant_id → 0 rows (AD-3 RLS).

    Uses a mock session to verify the service uses `tenant_id` filter.
    """
    async def _inner() -> None:
        from apps.api.modules.m7_simulation.services.cvp_simulation_service import (
            CVPSimulationService,
        )

        tenant_b = uuid.uuid4()

        # Mock session — returns None for tenant_b (simulating RLS).
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: None
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = CVPSimulationService(
            session=mock_session,
            tenant_id=tenant_b,
            actor_id=uuid.uuid4(),
            trace_id="trace-test-rls",
        )

        from apps.api.modules.m7_simulation.exceptions import CVPBaselineNotFoundError

        with pytest.raises(CVPBaselineNotFoundError):
            await service.fetch_cvp_baseline(period_key="2026-07")

    asyncio.run(_inner())


def test_fetch_cvp_baseline_success_derives_fields():
    """Successful fetch → CVPBaseline with derived fields from snapshot + products."""
    async def _inner() -> None:
        from apps.api.modules.m7_simulation.services.cvp_simulation_service import (
            CVPSimulationService,
        )

        # Mock snapshot row.
        mock_snapshot = type("Snap", (), {})()
        mock_snapshot.overhead_cost = 5_000_000
        mock_snapshot.material_cost = 3_000_000
        mock_snapshot.period_key = "2026-07"
        mock_snapshot.state = "committed"
        mock_snapshot.created_at = None

        # Mock session — snapshot SELECT returns the row, products SELECT returns row.
        mock_result_snap = AsyncMock()
        mock_result_snap.scalar_one_or_none = lambda: mock_snapshot

        mock_result_prod = AsyncMock()
        mock_result_prod.first = lambda: type("Row", (), {"avg_unit_price": 10000})()

        mock_session = AsyncMock()

        async def _execute(stmt):
            # Distinguish between snapshot and product queries by inspecting the WHERE.
            from sqlalchemy import Select

            if isinstance(stmt, Select):
                sql = str(stmt)
                if "fiscal_period_snapshots" in sql:
                    return mock_result_snap
                if "products" in sql:
                    return mock_result_prod
            return mock_result_prod

        mock_session.execute = AsyncMock(side_effect=_execute)

        service = CVPSimulationService(
            session=mock_session,
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            trace_id="trace-test-success",
        )

        baseline, source_period_key, fiscal_period_state = await service.fetch_cvp_baseline(
            period_key="2026-07"
        )

        # fixed_cost = overhead_cost + material_cost = 5,000,000 + 3,000,000 = 8,000,000
        assert baseline.fixed_cost == Decimal("8000000")
        assert baseline.unit_price == Decimal("10000")
        assert baseline.unit_variable_cost == Decimal("6000.0")
        assert baseline.operating_rate == DEFAULT_OPERATING_RATE
        assert baseline.target_profit == DEFAULT_TARGET_PROFIT
        assert source_period_key == "2026-07"
        assert fiscal_period_state == "committed"

    asyncio.run(_inner())


def test_compute_end_to_end():
    """compute() orchestration: fetch baseline + simulate."""
    async def _inner() -> None:
        from apps.api.modules.m7_simulation.services.cvp_simulation_service import (
            CVPSimulationService,
        )

        mock_snapshot = type("Snap", (), {})()
        mock_snapshot.overhead_cost = 5_000_000
        mock_snapshot.material_cost = 3_000_000
        mock_snapshot.period_key = "2026-07"
        mock_snapshot.state = "committed"
        mock_snapshot.created_at = None

        mock_result_snap = AsyncMock()
        mock_result_snap.scalar_one_or_none = lambda: mock_snapshot

        mock_result_prod = AsyncMock()
        mock_result_prod.first = lambda: type("Row", (), {"avg_unit_price": 10000})()

        mock_session = AsyncMock()

        async def _execute(stmt):
            from sqlalchemy import Select

            if isinstance(stmt, Select):
                sql = str(stmt)
                if "fiscal_period_snapshots" in sql:
                    return mock_result_snap
                if "products" in sql:
                    return mock_result_prod
            return mock_result_prod

        mock_session.execute = AsyncMock(side_effect=_execute)

        service = CVPSimulationService(
            session=mock_session,
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            trace_id="trace-test-compute",
        )

        baseline, result, source_period_key = await service.compute(
            period_key="2026-07",
            delta=CVPDelta(unit_price_delta_pct=Decimal("0.1")),
        )

        assert baseline.fixed_cost == Decimal("8000000")
        assert result.simulated_bep.bep_quantity != result.baseline_bep.bep_quantity
        assert source_period_key == "2026-07"

    asyncio.run(_inner())
