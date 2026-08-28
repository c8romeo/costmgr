"""tests.api.modules.finops.test_phase_16_20_router_include — Layer 1 P0 smoke test.

Phase 20.5 wire (cj-style 147번째) — Layer 1 P0 critical router include verification
+ Layer 2 P1 smoke test (Phase 20.5 §F37.2 T2.8 — Carrying-over to cj-style 188).

Verifies that the 4 routers (Phase 17 sustainability + Phase 18 commitment +
Phase 19 pricing + Phase 20 multi-cloud) are wired into apps/api/main.py
AND mounted on the FastAPI app via include_router().

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
MAIN_PY = REPO_ROOT / "apps" / "api" / "main.py"

EXPECTED_ROUTER_IMPORTS = frozenset(
    {
        "commitment_router",
        "sustainability_router",
        "pricing_router",
        "multi_cloud_router",
    }
)
EXPECTED_INCLUDE_CALLS = frozenset(
    {
        "app.include_router(sustainability_router)",
        "app.include_router(commitment_router)",
        "app.include_router(pricing_router)",
        "app.include_router(multi_cloud_router)",
    }
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


def test_main_py_imports_all_four_finops_routers() -> None:
    """Test 2 — main.py imports the 4 Phase 17/18/19/20 routers via aliases."""
    source = _read_main_py_source()
    for router_alias in EXPECTED_ROUTER_IMPORTS:
        pattern = rf"router as {router_alias}"
        assert re.search(pattern, source), (
            f"main.py missing `router as {router_alias}` import"
        )


def test_main_py_calls_include_router_for_all_four() -> None:
    """Test 3 — main.py calls app.include_router() for all 4 routers."""
    source = _read_main_py_source()
    for include_call in EXPECTED_INCLUDE_CALLS:
        assert include_call in source, (
            f"main.py missing include_router call: {include_call}"
        )


def test_main_py_routers_ordered_after_executive_dashboard() -> None:
    """Test 4 — 4 include_router calls appear AFTER executive_dashboard_router
    per Phase 20.5 §F37.1-5 (CRITICAL section-order invariant)."""
    source = _read_main_py_source()
    exec_idx = source.find("app.include_router(executive_dashboard_router)")
    sustainability_idx = source.find("app.include_router(sustainability_router)")
    commitment_idx = source.find("app.include_router(commitment_router)")
    pricing_idx = source.find("app.include_router(pricing_router)")
    multi_cloud_idx = source.find("app.include_router(multi_cloud_router)")
    assert exec_idx != -1
    assert sustainability_idx > exec_idx
    assert commitment_idx > sustainability_idx
    assert pricing_idx > commitment_idx
    assert multi_cloud_idx > pricing_idx
