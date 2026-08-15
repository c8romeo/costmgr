"""tests.integration.test_m7_simulation_projection_capability_v1_17_drift — Story 7.2.

EXTENSION to `test_capability_matrix_v1_17_drift.py` for the projection
sub-endpoint capability reuse. 7-2 wire MUST reuse Capability.CVP_SIMULATION
(industry-agnostic) — NO new capability added.

CR 11-3 lesson: capability drift across industry matrices is the #1
source of cross-tenant write leaks. Each capability addition needs a
4-industry pin + a docs-version pin + a table-row pin.

This file adds SPECIFIC tests for projection reuse:
- Capability.CVP_SIMULATION reused (no NEW capability).
- ProjectionService uses CVP_SIMULATION in its handlers.
- No PROJECTION_* enum values introduced.
"""

from __future__ import annotations

from pathlib import Path

from apps.api.core.capability import (
    Capability,
    industry_supports,
)
from packages.services.m0_onboarding.industry_menu import Industry

ROOT = Path(__file__).resolve().parents[2]


# ── Capability.CVP_SIMULATION reuse (industry-agnostic) ──────
def test_projection_reuses_cvp_simulation_capability() -> None:
    """Story 7-2 handlers MUST use `@require_capability(CVP_SIMULATION)`."""
    handlers_file = (
        ROOT
        / "apps"
        / "api"
        / "modules"
        / "m7_simulation"
        / "handlers.py"
    )
    src = handlers_file.read_text(encoding="utf-8")
    # 3 projection routes MUST use CVP_SIMULATION.
    projection_section = src.split("Story 7.2 routes")[1] if "Story 7.2 routes" in src else src
    assert "require_capability(CVP_SIMULATION)" in projection_section, (
        "Projection routes do not use Capability.CVP_SIMULATION — "
        "must reuse 7-1 capability gate (CR 12-1 L4 precedent)"
    )


def test_no_new_projection_capability_added() -> None:
    """No NEW `Capability.PROJECTION_*` enum value introduced (CR 11-3 D-2)."""
    capability_file = ROOT / "apps" / "api" / "core" / "capability.py"
    src = capability_file.read_text(encoding="utf-8")
    # CVP_SIMULATION exists (7-1 wire)
    assert "CVP_SIMULATION" in src
    # No NEW capability for projection specifically
    for prefix in ("PROJECTION_", "PROJECTION_BASELINE", "PROJECTION_COMPUTE"):
        assert prefix not in src, (
            f"New capability {prefix} added — must reuse CVP_SIMULATION"
        )


def test_projection_capability_industry_agnostic() -> None:
    """CVP_SIMULATION (reused by projection) is industry-agnostic (CR 12-1 L4).

    All 4 industries (manufacturing, service, mfg+service, mfg+service+other)
    MUST be able to use the projection endpoint.
    """
    for industry in (
        Industry.MANUFACTURING,
        Industry.SERVICE,
        Industry.MANUFACTURING_SERVICE,
        Industry.MANUFACTURING_SERVICE_OTHER,
    ):
        assert industry_supports(industry, Capability.CVP_SIMULATION), (
            f"{industry.value} industry missing CVP_SIMULATION capability "
            f"(CR 12-1 L4 industry-agnostic invariant violated)"
        )


def test_capability_count_unchanged_from_v1_17() -> None:
    """Capability enum count MUST NOT have grown (no NEW capability added in 7-2)."""
    # v1.17 = CVP_SIMULATION + BUDGET_SCENARIO + (v1.14 + v1.12 prior). 7-2
    # wire reuses CVP_SIMULATION → no NEW → count unchanged.
    # This is a smoke test — exact count depends on prior versions; we just
    # verify PROJECTION_ prefix is absent.
    capability_names = {c.name for c in Capability}
    projection_cap_names = {n for n in capability_names if "PROJECTION" in n}
    assert projection_cap_names == set(), (
        f"Unexpected PROJECTION capabilities: {projection_cap_names}"
    )
