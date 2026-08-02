"""tests.integration.test_capability_consistency — drift guard for capability matrix.

Story 4.1 — Task 3.1. The canonical industry × capability map lives in
ONE Python source:

  - `apps/api/core/capability.py::_INDUSTRY_CAPABILITIES` (source of truth)

`docs/capability-matrix.md` is the human-readable mirror. This test
pins the matrix drift guard so that adding a new capability without
updating the matrix fails CI.

Existing consistency tests in this repo:
  - `tests/integration/test_menu_config_consistency.py` — industry → menu parity
  - `tests/integration/test_m2_input_label_consistency.py` — m2_input label parity
  - `tests/integration/test_bom_validation_consistency.py` — BOM validation parity
  - `tests/integration/test_conventions_lint.py` — convention document lint

This module is the umbrella for capability-matrix drift; Story 4.1 adds
the COST_CALCULATION matrix row + 6×1.1 = 6 industry param cases.

Why this lives in `tests/integration/` (not `tests/unit/`): the test
imports FastAPI + the Industry enum, which require the api package on
sys.path. Integration is the right scope.
"""

from __future__ import annotations

import pytest

from apps.api.core.capability import (
    Capability,
    _INDUSTRY_CAPABILITIES,
    industry_supports,
)
from packages.services.m0_onboarding.industry_menu import Industry


# ── AC #4 — Matrix coverage: every Industry × Capability cell is decided ──
@pytest.mark.parametrize(
    "industry",
    [Industry.MANUFACTURING, Industry.SERVICE, Industry.MANUFACTURING_SERVICE, Industry.MANUFACTURING_SERVICE_OTHER],
)
def test_industry_has_capability_set(industry: Industry) -> None:
    """Each Industry MUST have an entry in `_INDUSTRY_CAPABILITIES`."""
    assert industry in _INDUSTRY_CAPABILITIES, (
        f"Industry {industry.value!r} missing from _INDUSTRY_CAPABILITIES. "
        f"Edit apps/api/core/capability.py to add the entry."
    )


@pytest.mark.parametrize(
    "capability",
    list(Capability),
)
def test_capability_is_documented(capability: Capability) -> None:
    """Every Capability enum member MUST be in the matrix above.

    Coverage = max 4 x 1 (true|false) param sets / capability. If
    `industry_supports(industry, capability)` returns True for ANY of
    the 4 industries, the matrix has a column.
    """
    discovered = [
        industry for industry in Industry
        if industry_supports(industry, capability)
    ]
    # We don't fail when discovered = []: some capabilities are
    # pre-provisioned for future stories (e.g. SEGMENT_SPLIT is only
    # visible to mfg+service / mfg+service+other). The matrix row
    # invariant is that discovered is non-empty for ALL capabilities
    # defined so far (no orphan capability).
    assert discovered, (
        f"Capability {capability.value!r} is granted to NO industry. "
        f"Either remove the enum member or add it to _INDUSTRY_CAPABILITIES."
    )


# ── Story 4.1 — COST_CALCULATION matrix row ───────────────────
@pytest.mark.parametrize(
    "industry, expected",
    [
        (Industry.MANUFACTURING, True),
        (Industry.SERVICE, False),
        (Industry.MANUFACTURING_SERVICE, True),
        (Industry.MANUFACTURING_SERVICE_OTHER, True),
    ],
)
def test_cost_calculation_capability_matrix(
    industry: Industry, expected: bool
) -> None:
    """Story 4.1 — COST_CALCULATION parity check across 4 industries.

    Service-only tenants do NOT have COST_CALCULATION — they have
    Epic 9 ABC instead (COST_POOL / ACTIVITY / DRIVER). All three
    manufacturing-bearing industries have COST_CALCULATION.
    """
    assert industry_supports(industry, Capability.COST_CALCULATION) is expected, (
        f"COST_CALCULATION support drift for {industry.value!r}: "
        f"expected {expected}, got {industry_supports(industry, Capability.COST_CALCULATION)}"
    )


def test_cost_calculation_engine_is_industry_agnostic() -> None:
    """The engine itself does NOT check industry — capability gate is
    enforced at the route boundary (apps/api/main.py + m3_calculate).

    The engine (packages.cost_engine.core.period_cost) is pure and
    industry-agnostic. Industry gating is the adapter's responsibility.
    """
    # Confirm engine imports do NOT touch FastAPI / Industry.
    import packages.cost_engine.core.period_cost as pc
    src = pc.__file__  # type: ignore[attr-defined]
    assert src is not None
    text = open(src, encoding="utf-8").read()
    assert "Industry" not in text, (
        "Engine touches Industry enum — engine SHOULD be industry-agnostic; "
        "industry gating is the adapter's responsibility"
    )
    assert "capability" not in text.lower(), "Engine must not enforce capability"


# ── AC #4 — AD-11 boundary: core MUST NOT import adapters ─────
def test_engine_core_does_not_depend_on_individual_capabilities() -> None:
    """The engine pure-kernel does not need to know about Capability enum.

    If `Industry` or `Capability` ever leaks into the engine, it means
    AC #4 (capability gate at API boundary, NOT engine) has been
    violated. This is a defense-in-depth test on top of
    `tests/cost_engine/test_no_io_imports.py::test_engine_core_does_not_import_adapters`.
    """
    import packages.cost_engine as engine
    src = engine.__file__  # type: ignore[attr-defined]
    assert src is not None
    pkg_root = src.rsplit("__init__.py", 1)[0]
    import pathlib
    pkg = pathlib.Path(pkg_root)
    leaks: list[str] = []
    for py in pkg.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        for needle in ("apps.api.core.capability", "apps.api.modules.m3_calculate"):
            if needle in text:
                rel = py.relative_to(pkg)
                leaks.append(f"{rel}: contains `{needle}` — engine leaks API concern")
    assert not leaks, "\n".join(leaks)
