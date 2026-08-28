"""tests.api.modules.finops.test_phase_21_26_router_include — Layer 2 P1 smoke test.

Layer 2 P1 carry-over (cj-style 189번째) — Phase 21~26 router include verification,
mirroring `test_phase_16_20_router_include.py` (cj-style 188번째).

Verifies that the 5 routers (Phase 21 reserved_capacity + Phase 22
chargeback_settlement + Phase 23 unit_economics + Phase 24 budget_planning +
Phase 25 vendor_management) are wired into apps/api/main.py AND mounted on the
FastAPI app via include_router(), in the declared dependency order.

Honest note (Phase 26): FinOps Cost Anomaly ML Prediction ships NO FastAPI
router — the territory is an engine/serializer layer consumed by the Next.js
dashboard. Test 6 pins that absence so a future router wire is an explicit,
reviewed change rather than an unnoticed gap.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
MAIN_PY = REPO_ROOT / "apps" / "api" / "main.py"
PHASE_26_PACKAGE = (
    REPO_ROOT
    / "apps"
    / "api"
    / "modules"
    / "finops"
    / "cost_anomaly_ml_prediction"
)

EXPECTED_ROUTER_IMPORTS = frozenset(
    {
        "reserved_capacity_router",
        "chargeback_settlement_router",
        "unit_economics_router",
        "budget_planning_router",
        "vendor_management_router",
    }
)
EXPECTED_INCLUDE_CALLS = (
    "app.include_router(reserved_capacity_router)",
    "app.include_router(chargeback_settlement_router)",
    "app.include_router(unit_economics_router)",
    "app.include_router(budget_planning_router)",
    "app.include_router(vendor_management_router)",
)


def _read_main_py_source() -> str:
    """Read apps/api/main.py source as a string for static assertions."""
    assert MAIN_PY.exists(), f"main.py not found at {MAIN_PY}"
    return MAIN_PY.read_text(encoding="utf-8")


def test_main_py_source_is_readable() -> None:
    """Test 1 — main.py exists and is non-empty (file accessibility)."""
    source = _read_main_py_source()
    assert isinstance(source, str)
    assert len(source) > 1_000


def test_main_py_imports_all_five_finops_routers() -> None:
    """Test 2 — main.py imports the 5 Phase 21~25 routers via aliases."""
    source = _read_main_py_source()
    for router_alias in EXPECTED_ROUTER_IMPORTS:
        pattern = rf"router as {router_alias}"
        assert re.search(pattern, source), (
            f"main.py missing `router as {router_alias}` import"
        )


def test_main_py_calls_include_router_for_all_five() -> None:
    """Test 3 — main.py calls app.include_router() for all 5 routers."""
    source = _read_main_py_source()
    for include_call in EXPECTED_INCLUDE_CALLS:
        assert include_call in source, (
            f"main.py missing include_router call: {include_call}"
        )


def test_main_py_phase_21_25_includes_follow_multi_cloud() -> None:
    """Test 4 — Phase 21~25 includes appear AFTER the Phase 20 multi-cloud include."""
    source = _read_main_py_source()
    multi_cloud_idx = source.find("app.include_router(multi_cloud_router)")
    assert multi_cloud_idx != -1
    for include_call in EXPECTED_INCLUDE_CALLS:
        assert source.find(include_call) > multi_cloud_idx


def test_main_py_phase_21_25_includes_are_in_dependency_order() -> None:
    """Test 5 — Includes are ordered 21 → 22 → 23 → 24 → 25 (derivation chain)."""
    source = _read_main_py_source()
    indices = [source.find(call) for call in EXPECTED_INCLUDE_CALLS]
    assert all(idx != -1 for idx in indices)
    assert indices == sorted(indices)


def test_phase_26_cost_anomaly_ml_prediction_has_no_router() -> None:
    """Test 6 — Phase 26 ships no APIRouter and is not included in main.py."""
    assert PHASE_26_PACKAGE.is_dir()
    router_sources = [
        path
        for path in PHASE_26_PACKAGE.glob("*.py")
        if "APIRouter" in path.read_text(encoding="utf-8")
    ]
    assert router_sources == []
    source = _read_main_py_source()
    assert "cost_anomaly_ml_prediction" not in source
