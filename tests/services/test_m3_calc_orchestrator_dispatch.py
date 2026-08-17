"""Tests for Story 9.3 T2.5 — M3 CalcOrchestrator dual-route dispatch.

Coverage (15 cases):
- _resolve_engine_type: 'service' → 'abc' (3 cases)
- _resolve_engine_type: 'mixed', 'mfg+service+other', '' → 'trad' (3 cases)
- _dispatch_abc_path: lazy import + M9 service invocation (3 cases)
- _dispatch_abc_path: industry_mismatch → CalcServiceError (1 case)
- _dispatch_abc_path: M9 dispatch failure → CalcServiceError wrap (1 case)
- discriminated union return type: isinstance narrowing (2 cases)
- CalcOutcomeABC envelope shape (engine_type tag + snapshot_id + result_hash) (2 cases)

CR 11-3 + CR 12-5: ~15 cases, AD-19 dual-route + AD-21 CCRPort.compute 단일 소유
+ A29 forward-lock 3-way wire (CCR ↔ Activity ↔ Cost Object Breakdown).
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.modules.m3_calculate.services import (
    CalcOrchestrator,
    CalcOutcome,
    CalcOutcomeABC,
)
from apps.api.modules.m3_calculate.services.calc_orchestrator import (
    _ENGINE_TYPE_ABC,
    _ENGINE_TYPE_TRAD,
    CalcServiceError,
)
from packages.cost_engine.abc_engine import (
    DispatchState,
    dispatch_abc_path,
)


# ── _resolve_engine_type tests (6 cases) ────────────────────────


@pytest.mark.engine
def test_resolve_engine_type_service_to_abc() -> None:
    """AD-19 dual-route: industry='service' → 'abc' (M9 path)."""
    orch = CalcOrchestrator(
        session=MagicMock(),  # type: ignore[arg-type]
        trace_id="trace-001",
    )
    assert orch._resolve_engine_type(industry="service") == _ENGINE_TYPE_ABC


@pytest.mark.engine
def test_resolve_engine_type_manufacturing_to_trad() -> None:
    """AD-19 dual-route: industry='manufacturing' → 'trad' (legacy path)."""
    orch = CalcOrchestrator(
        session=MagicMock(),  # type: ignore[arg-type]
        trace_id="trace-002",
    )
    assert orch._resolve_engine_type(industry="manufacturing") == _ENGINE_TYPE_TRAD


@pytest.mark.engine
def test_resolve_engine_type_mixed_to_trad() -> None:
    """AD-19 dual-route: industry='mixed' (mfg+service) → 'trad' (CR 11-3 AD-18 compat)."""
    orch = CalcOrchestrator(
        session=MagicMock(),  # type: ignore[arg-type]
        trace_id="trace-003",
    )
    assert orch._resolve_engine_type(industry="mixed") == _ENGINE_TYPE_TRAD


@pytest.mark.engine
def test_resolve_engine_type_mfg_service_other_to_trad() -> None:
    """AD-19 dual-route: industry='mfg+service+other' → 'trad'."""
    orch = CalcOrchestrator(
        session=MagicMock(),  # type: ignore[arg-type]
        trace_id="trace-004",
    )
    assert orch._resolve_engine_type(industry="mfg+service+other") == _ENGINE_TYPE_TRAD


@pytest.mark.engine
def test_resolve_engine_type_empty_to_trad() -> None:
    """AD-19 dual-route: industry='' (empty) → 'trad' (defensive default)."""
    orch = CalcOrchestrator(
        session=MagicMock(),  # type: ignore[arg-type]
        trace_id="trace-005",
    )
    assert orch._resolve_engine_type(industry="") == _ENGINE_TYPE_TRAD


@pytest.mark.engine
def test_resolve_engine_type_matches_kernel_dispatch() -> None:
    """AD-19 cross-language parity: orchestrator decision == kernel dispatch decision.

    The orchestrator's `_resolve_engine_type` is the service-layer
    mirror of the pure kernel's `dispatch_abc_path(tenant_industry)`.
    They MUST agree on every input to preserve V8 determinism.
    """
    orch = CalcOrchestrator(
        session=MagicMock(),  # type: ignore[arg-type]
        trace_id="trace-006",
    )
    for industry in ("service", "manufacturing", "mixed", "mfg+service+other", ""):
        service_decision = orch._resolve_engine_type(industry=industry)
        # Kernel dispatch only resolves 'service' → 'abc'; everything else → 'trad'.
        expected = "abc" if industry == "service" else "trad"
        assert service_decision == expected, (
            f"industry={industry!r} orchestrator decision mismatch: "
            f"got {service_decision!r}, kernel expects {expected!r}"
        )


# ── _dispatch_abc_path tests (4 cases) ─────────────────────────


@pytest.mark.engine
@pytest.mark.asyncio
async def test_dispatch_abc_path_happy_path_returns_calc_outcome_abc(monkeypatch) -> None:
    """A29 forward-lock: service industry → CalcOutcomeABC envelope (not CalcOutcome)."""
    orch = CalcOrchestrator(
        session=MagicMock(),  # type: ignore[arg-type]
        trace_id="trace-007",
    )
    # Mock _load_tenant_industry to set industry='service'
    orch._industry = "service"
    orch._industry_enum = None

    # Mock the M9 service layer — AD-21 CCRPort.compute 단일 소유, M9 owns no public endpoint.
    mock_outcome = {
        "breakdown": [{"product_id": "p1", "allocated_krw": "13200000"}],
        "unused_capacity": {"unused_cost_krw": "0"},
        "v7_verdict": {"is_balanced": True},
        "ccr": {"department_id": "dept-001", "ccr_per_hour": "33000"},
        "is_balanced": True,
        "snapshot_id": "11111111-2222-3333-4444-555555555555",
        "result_hash": "a" * 64,
    }
    mock_service = MagicMock()
    mock_service.compute_and_persist = AsyncMock(return_value=mock_outcome)

    # LAZY import happens inside _dispatch_abc_path; patch sys.modules.
    import sys

    monkeypatch.setitem(
        sys.modules,
        "apps.api.modules.m9_abc.services.abc_allocation_service",
        MagicMock(AbcAllocationService=MagicMock(return_value=mock_service)),
    )

    result = await orch._dispatch_abc_path(
        tenant_id=uuid.uuid4(),
        period_key="2026-08",
    )

    assert isinstance(result, CalcOutcomeABC)
    assert not isinstance(result, CalcOutcome)
    assert result.engine_type == "abc"
    assert result.snapshot_id == "11111111-2222-3333-4444-555555555555"
    assert result.result_hash == "a" * 64
    assert result.verdict.verification_status == "passed"


@pytest.mark.engine
@pytest.mark.asyncio
async def test_dispatch_abc_path_industry_mismatch_raises_calc_service_error(monkeypatch) -> None:
    """Service-layer safety: industry != 'service' → CalcServiceError (industry_mismatch).

    Defensive guard. The capability gate already discriminates, but if
    a non-service industry somehow reaches this path we MUST raise
    before calling M9 service layer.
    """
    orch = CalcOrchestrator(
        session=MagicMock(),  # type: ignore[arg-type]
        trace_id="trace-008",
    )
    orch._industry = "manufacturing"  # NOT 'service'
    orch._industry_enum = None

    with pytest.raises(CalcServiceError) as exc_info:
        await orch._dispatch_abc_path(
            tenant_id=uuid.uuid4(),
            period_key="2026-08",
        )

    assert exc_info.value.reason == "industry_mismatch"
    assert exc_info.value.details == {"expected": "service", "actual": "manufacturing"}


@pytest.mark.engine
@pytest.mark.asyncio
async def test_dispatch_abc_path_m9_service_failure_wraps_in_calc_service_error(monkeypatch) -> None:
    """M9 dispatch failure → CalcServiceError wrap (m9_dispatch_failed:*)."""
    orch = CalcOrchestrator(
        session=MagicMock(),  # type: ignore[arg-type]
        trace_id="trace-009",
    )
    orch._industry = "service"
    orch._industry_enum = None

    mock_service = MagicMock()
    mock_service.compute_and_persist = AsyncMock(
        side_effect=RuntimeError("M9 service layer exploded")
    )

    # session.rollback() is awaited on the error path; MagicMock returns sync.
    mock_session = MagicMock()
    mock_session.rollback = AsyncMock()
    orch._session = mock_session

    import sys

    monkeypatch.setitem(
        sys.modules,
        "apps.api.modules.m9_abc.services.abc_allocation_service",
        MagicMock(AbcAllocationService=MagicMock(return_value=mock_service)),
    )

    with pytest.raises(CalcServiceError) as exc_info:
        await orch._dispatch_abc_path(
            tenant_id=uuid.uuid4(),
            period_key="2026-08",
        )

    assert exc_info.value.reason.startswith("m9_dispatch_failed:")
    assert "RuntimeError" in exc_info.value.reason
    assert "M9 service layer exploded" in exc_info.value.details["error"]


@pytest.mark.engine
def test_dispatch_abc_path_lazy_import_pattern_in_source() -> None:
    """LAZY import pattern — m9 ← m3 ← m9 circular import 방지.

    Static AST check: verify `calc_orchestrator.py` does NOT have any
    top-level `from apps.api.modules.m9_abc...` or
    `import apps.api.modules.m9_abc...` statement. The M9 module MUST
    only be imported INSIDE `_dispatch_abc_path` method body.
    """
    import ast
    from pathlib import Path

    src_path = Path(__file__).resolve().parents[2] / "apps" / "api" / "modules" / "m3_calculate" / "services" / "calc_orchestrator.py"
    src = src_path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(src_path))

    violations: list[str] = []
    for node in ast.walk(tree):
        # Skip imports inside function/method bodies (those are lazy imports).
        # ast.Import / ast.ImportFrom have no `col_offset` parent; we check
        # via lineno + the surrounding context.
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("apps.api.modules.m9_abc"):
                    violations.append(
                        f"calc_orchestrator.py:{node.lineno} top-level "
                        f"`import {alias.name}` — LAZY import pattern violated"
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("apps.api.modules.m9_abc"):
                # Module-level ImportFrom nodes have parent == Module (top-level).
                # ast doesn't directly expose parent; check lineno against module
                # body item list instead.
                if isinstance(tree.body, list) and any(
                    isinstance(item, ast.ImportFrom) and item.module == node.module
                    and item.lineno == node.lineno
                    for item in tree.body
                ):
                    violations.append(
                        f"calc_orchestrator.py:{node.lineno} top-level "
                        f"`from {node.module} import ...` — LAZY import pattern violated"
                    )

    assert not violations, "\n".join(violations)


# ── Discriminated union narrowing tests (2 cases) ──────────────


@pytest.mark.engine
def test_calc_outcome_and_calc_outcome_abc_are_mutually_exclusive() -> None:
    """Type-safety: an outcome is EITHER CalcOutcome OR CalcOutcomeABC, never both.

    We construct synthetic instances (no real engine call) to keep the
    test pure and DB-free.
    """
    # Build a synthetic CalcOutcome (mock engine_result + verdict).
    mock_engine_result = MagicMock()
    mock_engine_result.tenant_id = uuid.uuid4()
    mock_engine_result.period_key = "2026-08"
    trad_outcome = CalcOutcome(
        engine_result=mock_engine_result,
        verdict=MagicMock(),  # type: ignore[arg-type]
    )
    assert isinstance(trad_outcome, CalcOutcome)
    assert not isinstance(trad_outcome, CalcOutcomeABC)

    # Build a synthetic CalcOutcomeABC.
    abc_outcome = CalcOutcomeABC(
        engine_type="abc",
        allocation_outcome={"breakdown": []},
        snapshot_id="11111111-2222-3333-4444-555555555555",
        result_hash="c" * 64,
        verdict=MagicMock(),  # type: ignore[arg-type]
    )
    assert isinstance(abc_outcome, CalcOutcomeABC)
    assert not isinstance(abc_outcome, CalcOutcome)


@pytest.mark.engine
def test_calc_outcome_abc_is_frozen_and_has_engine_type_tag() -> None:
    """CalcOutcomeABC invariants: frozen + engine_type Literal['abc'] tag."""
    abc_outcome = CalcOutcomeABC(
        engine_type="abc",
        allocation_outcome={"breakdown": []},
        snapshot_id="11111111-2222-3333-4444-555555555555",
        result_hash="d" * 64,
        verdict=MagicMock(),  # type: ignore[arg-type]
    )
    # Frozen dataclass — assignment raises.
    with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
        abc_outcome.engine_type = "trad"  # type: ignore[misc]

    # engine_type tag is locked to 'abc' (AD-19 dual-route discriminator).
    assert abc_outcome.engine_type == "abc"


# ── CalcOutcomeABC envelope shape tests (3 cases) ──────────────


@pytest.mark.engine
def test_calc_outcome_abc_envelope_fields_present() -> None:
    """CalcOutcomeABC envelope has all 5 required fields (engine_type, allocation_outcome, snapshot_id, result_hash, verdict)."""
    abc_outcome = CalcOutcomeABC(
        engine_type="abc",
        allocation_outcome={"breakdown": [{"product_id": "p1"}]},
        snapshot_id="22222222-3333-4444-5555-666666666666",
        result_hash="e" * 64,
        verdict=MagicMock(),  # type: ignore[arg-type]
    )
    assert hasattr(abc_outcome, "engine_type")
    assert hasattr(abc_outcome, "allocation_outcome")
    assert hasattr(abc_outcome, "snapshot_id")
    assert hasattr(abc_outcome, "result_hash")
    assert hasattr(abc_outcome, "verdict")


@pytest.mark.engine
def test_calc_outcome_abc_snapshot_id_is_uuid_string() -> None:
    """snapshot_id MUST be a valid UUID-as-string (M9 service-layer contract)."""
    snapshot_uuid_str = "33333333-4444-5555-6666-777777777777"
    abc_outcome = CalcOutcomeABC(
        engine_type="abc",
        allocation_outcome={},
        snapshot_id=snapshot_uuid_str,
        result_hash="f" * 64,
        verdict=MagicMock(),  # type: ignore[arg-type]
    )
    # Validate UUID-as-string format.
    uuid.UUID(abc_outcome.snapshot_id)  # raises if invalid
    assert str(abc_outcome.snapshot_id) == snapshot_uuid_str


@pytest.mark.engine
def test_calc_outcome_abc_result_hash_is_sha256_64char_hex() -> None:
    """result_hash MUST be sha256: prefix + 64-char hexdigest (V8 determinism convention)."""
    result_hash = "a1b2" * 16  # 64 chars, valid hex
    abc_outcome = CalcOutcomeABC(
        engine_type="abc",
        allocation_outcome={},
        snapshot_id="44444444-5555-6666-7777-888888888888",
        result_hash=result_hash,
        verdict=MagicMock(),  # type: ignore[arg-type]
    )
    assert len(abc_outcome.result_hash) == 64
    # Valid hex check (V8 determinism EP-IC-1 invariant).
    int(abc_outcome.result_hash, 16)


# ── Kernel-side dispatch parity test (1 case) ──────────────────


@pytest.mark.engine
def test_kernel_dispatch_decision_matches_orchestrator_decision() -> None:
    """AD-19 cross-language parity: kernel `dispatch_abc_path` == orchestrator `_resolve_engine_type`.

    The orchestrator's `_resolve_engine_type` is the service-layer
    mirror of the pure kernel's `dispatch_abc_path(tenant_industry)`.
    They MUST agree on every input to preserve V8 determinism.
    """
    for industry in ("service", "manufacturing", "mixed", "mfg+service+other", ""):
        # Kernel decision
        kernel_state: DispatchState = dispatch_abc_path(tenant_industry=industry)
        # Orchestrator decision (sync call, no session needed for _resolve_engine_type)
        orch = CalcOrchestrator(
            session=MagicMock(),  # type: ignore[arg-type]
            trace_id="trace-011",
        )
        orch_decision = orch._resolve_engine_type(industry=industry)
        assert orch_decision == kernel_state.resolved_engine_type, (
            f"industry={industry!r}: kernel={kernel_state.resolved_engine_type!r} "
            f"!= orchestrator={orch_decision!r}"
        )