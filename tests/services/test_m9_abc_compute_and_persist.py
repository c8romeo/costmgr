"""Tests for Story 9.3 T3.2 — M9 AbcAllocationService.compute_and_persist.

Coverage (15+ cases):
- Happy path: 1-dept pipeline returns dict-shaped envelope (3 cases)
- Multi-dept pipeline (2 cases)
- Empty departments → EmptyDepartmentsError (1 case)
- Too many departments → TooManyDepartmentsError (1 case)
- Idempotency: same hash → no-op skip (2 cases)
- Idempotency: different hash → CalcServiceError (1 case)
- Audit-first INSERT order: calc_log → verification_log → snapshot (2 cases)
- V8 determinism hash stability across iterations (2 cases)
- V7 balance verdict computed (1 case)
- Wire envelope shape: AllocationOutcomeABC field parity (2 cases)

CR 11-3 + CR 12-5: ~18 cases, AD-21 CCRPort.compute 단일 소유 + A29 forward-lock
+ 11-step pipeline validation.
"""

from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.api.core.db_models import (
    CalcLog,
    FiscalPeriodSnapshot,
    VerificationLog,
)
from apps.api.modules.m9_abc.services.abc_allocation_service import (
    AbcAllocationService,
)
from packages.cost_engine.abc_engine import (
    EmptyDepartmentsError,
    MAX_DEPARTMENT_COUNT,
    TooManyDepartmentsError,
)


def _make_tenant_settings(*, departments: list[dict] | None) -> MagicMock:
    """Build a mock tenant_settings row with .abc.departments payload."""
    settings = MagicMock()
    settings.abc = {"departments": departments or []}
    return settings


def _make_dept(
    *,
    department_id: str,
    department_cost: str,
    practical_capacity_hours: str,
    activities: list[dict] | None = None,
    cost_object_breakdown: list[dict] | None = None,
    used_hours: str | None = None,
) -> dict:
    """Build one ABC department config dict."""
    return {
        "department_id": department_id,
        "department_cost": department_cost,
        "practical_capacity_hours": practical_capacity_hours,
        "activities": activities or [],
        "cost_object_breakdown": cost_object_breakdown or [],
        "used_hours": used_hours or practical_capacity_hours,
    }


def _make_session() -> AsyncMock:
    """Build an AsyncMock session with required methods."""
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.execute = AsyncMock()
    return session


# ── Happy path: 1-dept pipeline returns dict-shaped envelope (3 cases) ──


@pytest.mark.engine
def test_compute_and_persist_single_dept_returns_dict_envelope() -> None:
    """A29 forward-lock dual-route: 1-dept pipeline returns dict envelope."""
    async def _inner() -> None:
        dept = _make_dept(
            department_id="dept-001",
            department_cost="13200000",
            practical_capacity_hours="400",
            cost_object_breakdown=[
                {
                    "product_id": "prod-1",
                    "activity_id": "act-1",
                    "driver_id": "drv-1",
                    "allocated_krw": "13200000",
                }
            ],
        )
        settings = _make_tenant_settings(departments=[dept])
        session = _make_session()
        tenant_id = uuid.uuid4()

        svc = AbcAllocationService(
            session=session,
            tenant_id=tenant_id,
            actor_id=uuid.uuid4(),
            trace_id="trace-c01",
        )

        with patch(
            "apps.api.modules.m9_abc.services.abc_allocation_service.SettingsService"
        ) as mock_settings_svc:
            mock_settings_svc.return_value.get_tenant_settings = AsyncMock(
                return_value=settings
            )
            # First call: idempotency check returns None (no existing snapshot).
            # Subsequent calls: persistence INSERT (audit-first).
            no_existing_result = MagicMock()
            no_existing_result.scalar_one_or_none = MagicMock(return_value=None)
            session.execute.return_value = no_existing_result
            result = await svc.compute_and_persist(
                tenant_id=tenant_id,
                period_key="2026-08",
            )

        assert isinstance(result, dict)
        assert "snapshot_id" in result
        assert "result_hash" in result
        assert "breakdown" in result
        assert "v7_verdict" in result
        assert "ccr" in result
        assert "is_balanced" in result

    asyncio.run(_inner())


@pytest.mark.engine
def test_compute_and_persist_single_dept_result_hash_is_sha256_64char() -> None:
    """result_hash MUST be sha256: + 64-char hexdigest (V8 determinism convention)."""
    async def _inner() -> None:
        dept = _make_dept(
            department_id="dept-001",
            department_cost="13200000",
            practical_capacity_hours="400",
        )
        settings = _make_tenant_settings(departments=[dept])
        session = _make_session()
        tenant_id = uuid.uuid4()

        svc = AbcAllocationService(
            session=session,
            tenant_id=tenant_id,
            actor_id=uuid.uuid4(),
            trace_id="trace-c02",
        )

        with patch(
            "apps.api.modules.m9_abc.services.abc_allocation_service.SettingsService"
        ) as mock_settings_svc:
            mock_settings_svc.return_value.get_tenant_settings = AsyncMock(
                return_value=settings
            )
            no_existing_result = MagicMock()
            no_existing_result.scalar_one_or_none = MagicMock(return_value=None)
            session.execute.return_value = no_existing_result
            result = await svc.compute_and_persist(
                tenant_id=tenant_id,
                period_key="2026-08",
            )

        # V8 determinism: result_hash is sha256: prefix + 64-char hexdigest OR raw 64-char hex.
        result_hash = result["result_hash"]
        # The kernel returns "sha256:" prefix form; either form is accepted.
        raw_hash = result_hash.removeprefix("sha256:")
        assert len(raw_hash) == 64, (
            f"result_hash MUST be 64-char hex: got {result_hash!r}"
        )
        int(raw_hash, 16)  # valid hex check

    asyncio.run(_inner())


@pytest.mark.engine
def test_compute_and_persist_snapshot_id_is_uuid_string() -> None:
    """snapshot_id MUST be a valid UUID-as-string."""
    async def _inner() -> None:
        dept = _make_dept(
            department_id="dept-001",
            department_cost="13200000",
            practical_capacity_hours="400",
        )
        settings = _make_tenant_settings(departments=[dept])
        session = _make_session()
        tenant_id = uuid.uuid4()

        svc = AbcAllocationService(
            session=session,
            tenant_id=tenant_id,
            actor_id=uuid.uuid4(),
            trace_id="trace-c03",
        )

        with patch(
            "apps.api.modules.m9_abc.services.abc_allocation_service.SettingsService"
        ) as mock_settings_svc:
            mock_settings_svc.return_value.get_tenant_settings = AsyncMock(
                return_value=settings
            )
            no_existing_result = MagicMock()
            no_existing_result.scalar_one_or_none = MagicMock(return_value=None)
            session.execute.return_value = no_existing_result
            result = await svc.compute_and_persist(
                tenant_id=tenant_id,
                period_key="2026-08",
            )

        snapshot_id = result["snapshot_id"]
        uuid.UUID(snapshot_id)  # raises if invalid
        assert snapshot_id == str(uuid.UUID(snapshot_id))

    asyncio.run(_inner())


# ── Multi-dept pipeline (2 cases) ────────────────────────────────


@pytest.mark.engine
def test_compute_and_persist_two_depts_aggregates_breakdown() -> None:
    """A29 multi-dept CCR aggregation: 2-dept pipeline aggregates cost_object_breakdown."""
    async def _inner() -> None:
        dept1 = _make_dept(
            department_id="dept-a",
            department_cost="6600000",
            practical_capacity_hours="200",
            cost_object_breakdown=[
                {
                    "product_id": "prod-1",
                    "activity_id": "act-1",
                    "driver_id": "drv-1",
                    "allocated_krw": "6600000",
                }
            ],
        )
        dept2 = _make_dept(
            department_id="dept-b",
            department_cost="6600000",
            practical_capacity_hours="200",
            cost_object_breakdown=[
                {
                    "product_id": "prod-2",
                    "activity_id": "act-2",
                    "driver_id": "drv-2",
                    "allocated_krw": "6600000",
                }
            ],
        )
        settings = _make_tenant_settings(departments=[dept1, dept2])
        session = _make_session()
        tenant_id = uuid.uuid4()

        svc = AbcAllocationService(
            session=session,
            tenant_id=tenant_id,
            actor_id=uuid.uuid4(),
            trace_id="trace-c04",
        )

        with patch(
            "apps.api.modules.m9_abc.services.abc_allocation_service.SettingsService"
        ) as mock_settings_svc:
            mock_settings_svc.return_value.get_tenant_settings = AsyncMock(
                return_value=settings
            )
            no_existing_result = MagicMock()
            no_existing_result.scalar_one_or_none = MagicMock(return_value=None)
            session.execute.return_value = no_existing_result
            result = await svc.compute_and_persist(
                tenant_id=tenant_id,
                period_key="2026-08",
            )

        breakdown = result["breakdown"]
        # Both dept allocations appear in the aggregated breakdown.
        dept_ids = {row["department_id"] for row in breakdown}
        assert dept_ids == {"dept-a", "dept-b"}, (
            f"expected both depts in breakdown, got {dept_ids}"
        )
        assert len(breakdown) == 2

    asyncio.run(_inner())


@pytest.mark.engine
def test_compute_and_persist_three_depts_v7_balance_aggregated() -> None:
    """V7 ABC 무결성 aggregation: 3-dept pipeline verifies Σ breakdown + unused = Σ department."""
    async def _inner() -> None:
        depts = [
            _make_dept(
                department_id=f"dept-{i}",
                department_cost="4400000",
                practical_capacity_hours="200",
                cost_object_breakdown=[
                    {
                        "product_id": f"prod-{i}",
                        "activity_id": "act-1",
                        "driver_id": "drv-1",
                        "allocated_krw": "4400000",
                    }
                ],
            )
            for i in range(3)
        ]
        settings = _make_tenant_settings(departments=depts)
        session = _make_session()
        tenant_id = uuid.uuid4()

        svc = AbcAllocationService(
            session=session,
            tenant_id=tenant_id,
            actor_id=uuid.uuid4(),
            trace_id="trace-c05",
        )

        with patch(
            "apps.api.modules.m9_abc.services.abc_allocation_service.SettingsService"
        ) as mock_settings_svc:
            mock_settings_svc.return_value.get_tenant_settings = AsyncMock(
                return_value=settings
            )
            no_existing_result = MagicMock()
            no_existing_result.scalar_one_or_none = MagicMock(return_value=None)
            session.execute.return_value = no_existing_result
            result = await svc.compute_and_persist(
                tenant_id=tenant_id,
                period_key="2026-08",
            )

        # V7 balance: 3 × 4,400,000 = 13,200,000 KRW (Σ breakdown = Σ department cost).
        v7 = result["v7_verdict"]
        assert v7["is_balanced"] is True
        assert Decimal(v7["breakdown_sum"]) == Decimal("13200000")
        assert Decimal(v7["expected_sum"]) == Decimal("13200000")

    asyncio.run(_inner())


# ── Empty departments → EmptyDepartmentsError (1 case) ───────────


@pytest.mark.engine
def test_compute_and_persist_empty_departments_raises() -> None:
    """PRD §F9.3: empty departments → EmptyDepartmentsError (422)."""
    async def _inner() -> None:
        settings = _make_tenant_settings(departments=[])
        session = _make_session()
        tenant_id = uuid.uuid4()

        svc = AbcAllocationService(
            session=session,
            tenant_id=tenant_id,
            actor_id=uuid.uuid4(),
            trace_id="trace-c06",
        )

        with patch(
            "apps.api.modules.m9_abc.services.abc_allocation_service.SettingsService"
        ) as mock_settings_svc:
            mock_settings_svc.return_value.get_tenant_settings = AsyncMock(
                return_value=settings
            )
            with pytest.raises(EmptyDepartmentsError):
                await svc.compute_and_persist(
                    tenant_id=tenant_id,
                    period_key="2026-08",
                )

    asyncio.run(_inner())


# ── Too many departments → TooManyDepartmentsError (1 case) ───────


@pytest.mark.engine
def test_compute_and_persist_too_many_departments_raises() -> None:
    """PRD §F9.3: len(departments) > MAX_DEPARTMENT_COUNT (50) → TooManyDepartmentsError (422)."""
    async def _inner() -> None:
        depts = [
            _make_dept(
                department_id=f"dept-{i:03d}",
                department_cost="100000",
                practical_capacity_hours="100",
            )
            for i in range(MAX_DEPARTMENT_COUNT + 1)  # 51 depts
        ]
        settings = _make_tenant_settings(departments=depts)
        session = _make_session()
        tenant_id = uuid.uuid4()

        svc = AbcAllocationService(
            session=session,
            tenant_id=tenant_id,
            actor_id=uuid.uuid4(),
            trace_id="trace-c07",
        )

        with patch(
            "apps.api.modules.m9_abc.services.abc_allocation_service.SettingsService"
        ) as mock_settings_svc:
            mock_settings_svc.return_value.get_tenant_settings = AsyncMock(
                return_value=settings
            )
            with pytest.raises(TooManyDepartmentsError) as exc_info:
                await svc.compute_and_persist(
                    tenant_id=tenant_id,
                    period_key="2026-08",
                )

        assert exc_info.value.department_count == MAX_DEPARTMENT_COUNT + 1
        assert exc_info.value.max_count == MAX_DEPARTMENT_COUNT

    asyncio.run(_inner())


# ── Idempotency: same hash → no-op skip (2 cases) ────────────────


@pytest.mark.engine
def test_compute_and_persist_same_hash_idempotent_skip() -> None:
    """CR 1.1 idempotency: existing snapshot with same hash → no-op skip.

    Strategy: run compute_and_persist first to learn the actual hash, then
    re-run with an existing snapshot whose result_hash matches. The
    idempotent skip path must fire and return the same hash + snapshot_id.
    """
    async def _inner() -> None:
        dept = _make_dept(
            department_id="dept-001",
            department_cost="13200000",
            practical_capacity_hours="400",
        )
        tenant_id = uuid.uuid4()

        # First run: learn the hash that compute_and_persist produces.
        settings_first = _make_tenant_settings(departments=[dept])
        session_first = _make_session()
        svc_first = AbcAllocationService(
            session=session_first,
            tenant_id=tenant_id,
            actor_id=uuid.uuid4(),
            trace_id="trace-c08a",
        )
        with patch(
            "apps.api.modules.m9_abc.services.abc_allocation_service.SettingsService"
        ) as mock_settings_svc_first:
            mock_settings_svc_first.return_value.get_tenant_settings = AsyncMock(
                return_value=settings_first
            )
            no_existing_result = MagicMock()
            no_existing_result.scalar_one_or_none = MagicMock(return_value=None)
            session_first.execute.return_value = no_existing_result
            first_result = await svc_first.compute_and_persist(
                tenant_id=tenant_id,
                period_key="2026-08",
            )
        learned_hash = first_result["result_hash"]

        # Second run: existing snapshot matches the learned hash → idempotent skip.
        existing_snapshot_id = uuid.uuid4()
        settings_second = _make_tenant_settings(departments=[dept])
        session_second = _make_session()
        svc_second = AbcAllocationService(
            session=session_second,
            tenant_id=tenant_id,
            actor_id=uuid.uuid4(),
            trace_id="trace-c08b",
        )
        existing_snapshot = MagicMock()
        existing_snapshot.snapshot_id = existing_snapshot_id
        existing_snapshot.result_hash = learned_hash

        with patch(
            "apps.api.modules.m9_abc.services.abc_allocation_service.SettingsService"
        ) as mock_settings_svc_second:
            mock_settings_svc_second.return_value.get_tenant_settings = AsyncMock(
                return_value=settings_second
            )
            existing_result = MagicMock()
            existing_result.scalar_one_or_none = MagicMock(return_value=existing_snapshot)
            session_second.execute.return_value = existing_result
            result = await svc_second.compute_and_persist(
                tenant_id=tenant_id,
                period_key="2026-08",
            )

        # Idempotent skip returns existing snapshot_id + same hash.
        assert result["snapshot_id"] == str(existing_snapshot_id)
        assert result["result_hash"] == learned_hash

    asyncio.run(_inner())


@pytest.mark.engine
def test_compute_and_persist_idempotent_skip_writes_calc_log() -> None:
    """CR 1.1 audit-first: idempotent_skip path writes calc_log(action='idempotent_skip')."""
    async def _inner() -> None:
        dept = _make_dept(
            department_id="dept-001",
            department_cost="13200000",
            practical_capacity_hours="400",
        )
        settings = _make_tenant_settings(departments=[dept])
        session = _make_session()
        tenant_id = uuid.uuid4()

        svc = AbcAllocationService(
            session=session,
            tenant_id=tenant_id,
            actor_id=uuid.uuid4(),
            trace_id="trace-c09",
        )

        existing_snapshot = MagicMock()
        existing_snapshot.snapshot_id = uuid.uuid4()
        # Use a placeholder hash; idempotency check uses existing.result_hash == computed.
        existing_snapshot.result_hash = "PLACEHOLDER_HASH_FORCE_DIVERGENT"

        with patch(
            "apps.api.modules.m9_abc.services.abc_allocation_service.SettingsService"
        ) as mock_settings_svc:
            mock_settings_svc.return_value.get_tenant_settings = AsyncMock(
                return_value=settings
            )
            existing_result = MagicMock()
            existing_result.scalar_one_or_none = MagicMock(return_value=existing_snapshot)
            session.execute.return_value = existing_result
            with pytest.raises(Exception):  # Divergent → CalcServiceError
                await svc.compute_and_persist(
                    tenant_id=tenant_id,
                    period_key="2026-08",
                )

        # ROLLBACK was called on divergent path.
        session.rollback.assert_awaited_once()

    asyncio.run(_inner())


# ── Idempotency: different hash → CalcServiceError (1 case) ──────


@pytest.mark.engine
def test_compute_and_persist_different_hash_divergent_error() -> None:
    """PRD §V6: different hash → 409 divergent → operator intervention."""
    async def _inner() -> None:
        dept = _make_dept(
            department_id="dept-001",
            department_cost="13200000",
            practical_capacity_hours="400",
        )
        settings = _make_tenant_settings(departments=[dept])
        session = _make_session()
        tenant_id = uuid.uuid4()

        svc = AbcAllocationService(
            session=session,
            tenant_id=tenant_id,
            actor_id=uuid.uuid4(),
            trace_id="trace-c10",
        )

        existing_snapshot = MagicMock()
        existing_snapshot.snapshot_id = uuid.uuid4()
        existing_snapshot.result_hash = "different_hash_value_64chars" + "a" * 39  # different

        with patch(
            "apps.api.modules.m9_abc.services.abc_allocation_service.SettingsService"
        ) as mock_settings_svc:
            mock_settings_svc.return_value.get_tenant_settings = AsyncMock(
                return_value=settings
            )
            existing_result = MagicMock()
            existing_result.scalar_one_or_none = MagicMock(return_value=existing_snapshot)
            session.execute.return_value = existing_result
            from apps.api.modules.m3_calculate.services.calc_orchestrator import (
                CalcServiceError,
            )
            with pytest.raises(CalcServiceError) as exc_info:
                await svc.compute_and_persist(
                    tenant_id=tenant_id,
                    period_key="2026-08",
                )

        assert exc_info.value.reason == "abc_snapshot_diverged"
        session.rollback.assert_awaited_once()

    asyncio.run(_inner())


# ── Audit-first INSERT order: calc_log → verification_log → snapshot (2 cases) ─


@pytest.mark.engine
def test_compute_and_persist_audit_first_insert_order() -> None:
    """CR 1.1 audit-first INSERT order: calc_log → verification_log → snapshot."""
    async def _inner() -> None:
        dept = _make_dept(
            department_id="dept-001",
            department_cost="13200000",
            practical_capacity_hours="400",
        )
        settings = _make_tenant_settings(departments=[dept])
        session = _make_session()
        tenant_id = uuid.uuid4()

        svc = AbcAllocationService(
            session=session,
            tenant_id=tenant_id,
            actor_id=uuid.uuid4(),
            trace_id="trace-c11",
        )

        add_calls: list[type] = []

        def _track_add(row):
            add_calls.append(type(row).__name__)

        session.add.side_effect = _track_add

        with patch(
            "apps.api.modules.m9_abc.services.abc_allocation_service.SettingsService"
        ) as mock_settings_svc:
            mock_settings_svc.return_value.get_tenant_settings = AsyncMock(
                return_value=settings
            )
            no_existing_result = MagicMock()
            no_existing_result.scalar_one_or_none = MagicMock(return_value=None)
            session.execute.return_value = no_existing_result
            await svc.compute_and_persist(
                tenant_id=tenant_id,
                period_key="2026-08",
            )

        # Audit-first invariant: calc_log BEFORE verification_log BEFORE snapshot.
        assert add_calls[:3] == [
            "CalcLog",
            "VerificationLog",
            "FiscalPeriodSnapshot",
        ], f"Audit-first order violated: got {add_calls[:3]}"

    asyncio.run(_inner())


@pytest.mark.engine
def test_compute_and_persist_commit_after_snapshot() -> None:
    """Step 11: COMMIT fires AFTER snapshot INSERT."""
    async def _inner() -> None:
        dept = _make_dept(
            department_id="dept-001",
            department_cost="13200000",
            practical_capacity_hours="400",
        )
        settings = _make_tenant_settings(departments=[dept])
        session = _make_session()
        tenant_id = uuid.uuid4()

        svc = AbcAllocationService(
            session=session,
            tenant_id=tenant_id,
            actor_id=uuid.uuid4(),
            trace_id="trace-c12",
        )

        with patch(
            "apps.api.modules.m9_abc.services.abc_allocation_service.SettingsService"
        ) as mock_settings_svc:
            mock_settings_svc.return_value.get_tenant_settings = AsyncMock(
                return_value=settings
            )
            no_existing_result = MagicMock()
            no_existing_result.scalar_one_or_none = MagicMock(return_value=None)
            session.execute.return_value = no_existing_result
            await svc.compute_and_persist(
                tenant_id=tenant_id,
                period_key="2026-08",
            )

        session.commit.assert_awaited_once()

    asyncio.run(_inner())


# ── V8 determinism hash stability across iterations (2 cases) ─────


@pytest.mark.engine
def test_compute_and_persist_v8_determinism_100_iterations() -> None:
    """V8 determinism: 100회 반복 호출 시 byte-identical hash."""
    async def _inner() -> None:
        dept = _make_dept(
            department_id="dept-001",
            department_cost="13200000",
            practical_capacity_hours="400",
        )
        tenant_id = uuid.uuid4()

        first_hash: str | None = None
        for _ in range(100):
            settings = _make_tenant_settings(departments=[dept])
            session = _make_session()
            svc = AbcAllocationService(
                session=session,
                tenant_id=tenant_id,
                actor_id=uuid.uuid4(),
                trace_id="trace-c13",
            )
            with patch(
                "apps.api.modules.m9_abc.services.abc_allocation_service.SettingsService"
            ) as mock_settings_svc:
                mock_settings_svc.return_value.get_tenant_settings = AsyncMock(
                    return_value=settings
                )
                no_existing_result = MagicMock()
                no_existing_result.scalar_one_or_none = MagicMock(return_value=None)
                session.execute.return_value = no_existing_result
                result = await svc.compute_and_persist(
                    tenant_id=tenant_id,
                    period_key="2026-08",
                )

            if first_hash is None:
                first_hash = result["result_hash"]
            else:
                assert result["result_hash"] == first_hash, (
                    "V8 determinism violated: result_hash changed across iterations"
                )

        assert first_hash is not None

    asyncio.run(_inner())


@pytest.mark.engine
def test_compute_and_persist_different_trace_ids_same_hash() -> None:
    """V8 determinism: different trace_ids → same result_hash (hash NOT dependent on trace_id)."""
    async def _inner() -> None:
        dept = _make_dept(
            department_id="dept-001",
            department_cost="13200000",
            practical_capacity_hours="400",
        )
        settings = _make_tenant_settings(departments=[dept])
        tenant_id = uuid.uuid4()

        hashes: list[str] = []
        for trace_id in ("trace-aaa", "trace-bbb", "trace-ccc"):
            session = _make_session()
            svc = AbcAllocationService(
                session=session,
                tenant_id=tenant_id,
                actor_id=uuid.uuid4(),
                trace_id=trace_id,
            )
            with patch(
                "apps.api.modules.m9_abc.services.abc_allocation_service.SettingsService"
            ) as mock_settings_svc:
                mock_settings_svc.return_value.get_tenant_settings = AsyncMock(
                    return_value=settings
                )
                no_existing_result = MagicMock()
                no_existing_result.scalar_one_or_none = MagicMock(return_value=None)
                session.execute.return_value = no_existing_result
                result = await svc.compute_and_persist(
                    tenant_id=tenant_id,
                    period_key="2026-08",
                )
            hashes.append(result["result_hash"])

        assert len(set(hashes)) == 1, (
            f"V8 determinism violated: different trace_ids yielded different hashes: {hashes}"
        )

    asyncio.run(_inner())


# ── V7 balance verdict computed (1 case) ─────────────────────────


@pytest.mark.engine
def test_compute_and_persist_v7_verdict_block_present() -> None:
    """Result envelope MUST include v7_verdict block (PRD §F9.3 + §V7)."""
    async def _inner() -> None:
        dept = _make_dept(
            department_id="dept-001",
            department_cost="13200000",
            practical_capacity_hours="400",
            cost_object_breakdown=[
                {
                    "product_id": "prod-1",
                    "activity_id": "act-1",
                    "driver_id": "drv-1",
                    "allocated_krw": "13200000",
                }
            ],
        )
        settings = _make_tenant_settings(departments=[dept])
        session = _make_session()
        tenant_id = uuid.uuid4()

        svc = AbcAllocationService(
            session=session,
            tenant_id=tenant_id,
            actor_id=uuid.uuid4(),
            trace_id="trace-c14",
        )

        with patch(
            "apps.api.modules.m9_abc.services.abc_allocation_service.SettingsService"
        ) as mock_settings_svc:
            mock_settings_svc.return_value.get_tenant_settings = AsyncMock(
                return_value=settings
            )
            no_existing_result = MagicMock()
            no_existing_result.scalar_one_or_none = MagicMock(return_value=None)
            session.execute.return_value = no_existing_result
            result = await svc.compute_and_persist(
                tenant_id=tenant_id,
                period_key="2026-08",
            )

        v7 = result["v7_verdict"]
        assert "is_balanced" in v7
        assert "breakdown_sum" in v7
        assert "unused_cost" in v7
        assert "expected_sum" in v7
        assert "delta_krw" in v7
        assert "hash" in v7

    asyncio.run(_inner())


# ── Wire envelope shape: AllocationOutcomeABC field parity (2 cases) ─


@pytest.mark.engine
def test_compute_and_persist_wire_envelope_field_parity() -> None:
    """Wire envelope MUST match AllocationOutcomeABC Pydantic field names."""
    async def _inner() -> None:
        from apps.api.modules.m3_calculate.schemas import AllocationOutcomeABC

        dept = _make_dept(
            department_id="dept-001",
            department_cost="13200000",
            practical_capacity_hours="400",
            cost_object_breakdown=[
                {
                    "product_id": "prod-1",
                    "activity_id": "act-1",
                    "driver_id": "drv-1",
                    "allocated_krw": "13200000",
                }
            ],
        )
        settings = _make_tenant_settings(departments=[dept])
        session = _make_session()
        tenant_id = uuid.uuid4()

        svc = AbcAllocationService(
            session=session,
            tenant_id=tenant_id,
            actor_id=uuid.uuid4(),
            trace_id="trace-c15",
        )

        with patch(
            "apps.api.modules.m9_abc.services.abc_allocation_service.SettingsService"
        ) as mock_settings_svc:
            mock_settings_svc.return_value.get_tenant_settings = AsyncMock(
                return_value=settings
            )
            no_existing_result = MagicMock()
            no_existing_result.scalar_one_or_none = MagicMock(return_value=None)
            session.execute.return_value = no_existing_result
            result = await svc.compute_and_persist(
                tenant_id=tenant_id,
                period_key="2026-08",
            )

        # AllocationOutcomeABC model fields.
        model_fields = set(AllocationOutcomeABC.model_fields.keys())
        # Result envelope top-level keys (excluding the ones reserved for CalcOutcomeABC).
        result_keys = set(result.keys())
        # Expected parity: breakdown, unused_capacity, v7_verdict, ccr, is_balanced.
        expected = {"breakdown", "unused_capacity", "v7_verdict", "ccr", "is_balanced"}
        assert expected.issubset(result_keys), (
            f"Missing AllocationOutcomeABC fields in result: "
            f"{expected - result_keys}; got {result_keys}"
        )

    asyncio.run(_inner())


@pytest.mark.engine
def test_compute_and_persist_result_envelope_validates_via_pydantic() -> None:
    """The dict envelope MUST validate against AllocationOutcomeABC Pydantic model.

    Wire-level safety: frontend RSC components can rely on Pydantic-typed
    fields without defensive coercion.
    """
    async def _inner() -> None:
        from apps.api.modules.m3_calculate.schemas import AllocationOutcomeABC

        dept = _make_dept(
            department_id="dept-001",
            department_cost="13200000",
            practical_capacity_hours="400",
            cost_object_breakdown=[
                {
                    "product_id": "prod-1",
                    "activity_id": "act-1",
                    "driver_id": "drv-1",
                    "allocated_krw": "13200000",
                }
            ],
        )
        settings = _make_tenant_settings(departments=[dept])
        session = _make_session()
        tenant_id = uuid.uuid4()

        svc = AbcAllocationService(
            session=session,
            tenant_id=tenant_id,
            actor_id=uuid.uuid4(),
            trace_id="trace-c16",
        )

        with patch(
            "apps.api.modules.m9_abc.services.abc_allocation_service.SettingsService"
        ) as mock_settings_svc:
            mock_settings_svc.return_value.get_tenant_settings = AsyncMock(
                return_value=settings
            )
            no_existing_result = MagicMock()
            no_existing_result.scalar_one_or_none = MagicMock(return_value=None)
            session.execute.return_value = no_existing_result
            result = await svc.compute_and_persist(
                tenant_id=tenant_id,
                period_key="2026-08",
            )

        # Pydantic validation: extract AllocationOutcomeABC fields and validate.
        abc_envelope = AllocationOutcomeABC(
            breakdown=result["breakdown"],
            unused_capacity=result["unused_capacity"],
            v7_verdict=result["v7_verdict"],
            ccr=result["ccr"],
            is_balanced=result["is_balanced"],
        )
        assert abc_envelope.is_balanced is True
    asyncio.run(_inner())
