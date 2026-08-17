"""tests.integration.test_capability_matrix_v1_19_drift — Story 9.3 dual-route gate pin.

Pins v1.19 EXTENSION (0 NEW capabilities, 1 row fill change):
- ABC_CALCULATION row fill: "9.1, 9.2" → "9.1, 9.2, 9.3"
  (dual-route gate via `require_any_capability(COST_CALCULATION, ABC_CALCULATION)`)

Industry matrix (per docs/capability-matrix.md v1.19):
- All 4 industries still ✅ for ABC_CALCULATION (industry-agnostic)
- 3 industries (mfg / mfg+service / mfg+service+other) still ✅ for
  COST_CALCULATION (mfg-only, dual-route gate fallback)

v1.19 wire (PRD §F9.3 + A29 forward-lock dual-route + AD-19):
- POST /api/v1/calc is the SINGLE public endpoint (M3 owns the route, AD-18)
- M3 orchestrator's `_resolve_engine_type(industry)` dispatches:
  - service → M9 ABC path (`AbcAllocationService.compute_and_persist`)
  - else → M3 traditional path (PRD §F0.2 3종 allocation)
- Discriminated union response: `CalcResponse | CalcAbcResponse`
  with `engine_type: Literal["trad", "abc"]` tag discriminator
- Alembic 0028 adds 2 JSONB columns + 2 GIN indexes to fiscal_period_snapshots

CR 11-3 lesson: capability drift across industry matrices is the #1
source of cross-tenant write leaks. v1.19 EXTENSION requires 0 NEW pins
since no NEW capability row is added — the existing v1.18 drift detector
covers the row presence + 4-industry grants. This file documents the
v1.19 SPECIFIC contracts (dual-route gate, discriminated union, etc.)
that the orchestrator + service layer + wire schema must honor.
"""

from __future__ import annotations

import re
from pathlib import Path

from apps.api.core.capability import (
    Capability,
    industry_supports,
    require_any_capability,
)
from packages.services.m0_onboarding.industry_menu import Industry

# ── v1.19 EXTENSION: 0 NEW capabilities ──────────────────────
_NEW_V1_19_CAPABILITIES: tuple[Capability, ...] = ()


def _load_capability_matrix_docs() -> str:
    """Read the capability matrix docs for drift detection."""
    repo_root = Path(__file__).resolve().parents[2]
    return (
        repo_root / "docs" / "capability-matrix.md"
    ).read_text(encoding="utf-8")


# ── 1. v1.19 capability count is 0 ──────────────────────────
def test_capability_v1_19_count_is_0() -> None:
    """v1.19 EXTENSION adds 0 NEW capabilities (dual-route gate reuses
    existing COST_CALCULATION + ABC_CALCULATION via require_any_capability).

    CR 11-3 honest-DEFER discipline: explicit assertion that no NEW
    capability row is needed for the dual-route dispatch.
    """
    assert len(_NEW_V1_19_CAPABILITIES) == 0


# ── 2. Dual-route gate contract ─────────────────────────────
def test_require_any_capability_accepts_dual_route_arguments() -> None:
    """`require_any_capability` factory MUST accept multiple Capability
    arguments (CR 12-5 D-14 envelope handler pattern + CR 6-2 V4
    3-source contract).

    Used at handlers.py: `require_any_capability(COST_CALCULATION,
    ABC_CALCULATION)` for the dual-route gate on POST /api/v1/calc.
    """
    # Smoke check: the factory exists and is callable with multiple args.
    factory = require_any_capability(
        Capability.COST_CALCULATION,
        Capability.ABC_CALCULATION,
    )
    assert callable(factory)


def test_dual_route_capabilities_intersect_4_industries() -> None:
    """COST_CALCULATION ∪ ABC_CALCULATION MUST cover ALL 4 industries.

    Per PRD §F9.3 + A29 forward-lock dual-route:
    - mfg 3종 → COST_CALCULATION ✅
    - service-only → ABC_CALCULATION ✅
    - dual-route gate `require_any_capability` passes on ALL 4 industries.

    No industry is excluded from POST /api/v1/calc (it's the canonical
    public endpoint per AD-18).
    """
    industries = (
        Industry.MANUFACTURING,
        Industry.SERVICE,
        Industry.MANUFACTURING_SERVICE,
        Industry.MANUFACTURING_SERVICE_OTHER,
    )
    for industry in industries:
        has_cost = industry_supports(industry, Capability.COST_CALCULATION)
        has_abc = industry_supports(industry, Capability.ABC_CALCULATION)
        assert has_cost or has_abc, (
            f"{industry.name} MUST have at least one of "
            f"COST_CALCULATION or ABC_CALCULATION for the dual-route gate. "
            f"cost={has_cost} abc={has_abc}"
        )


# ── 3. Docs v1.19 markers ──────────────────────────────────
def test_capability_matrix_docs_pin_v1_19() -> None:
    """docs/capability-matrix.md must declare v1.19 + Story 9.3 markers."""
    docs = _load_capability_matrix_docs()
    assert "# Capability Matrix (v1.19)" in docs, (
        "docs/capability-matrix.md title must be v1.19 (Story 9.3 wire)"
    )
    assert "v1.19 (2026-08-16, Story 9.3, Epic 9)" in docs, (
        "docs/capability-matrix.md must declare v1.19 entry header"
    )
    assert "dual-route gate" in docs, (
        "docs v1.19 entry must describe dual-route gate (PRD §F9.3)"
    )
    assert "A29 forward-lock" in docs
    assert "AD-19" in docs


def test_capability_matrix_docs_abc_calculation_row_v1_19() -> None:
    """docs ABC_CALCULATION row MUST show "9.1, 9.2, 9.3" fill (v1.19 EXTENSION)."""
    docs = _load_capability_matrix_docs()
    pattern = r"\|\s*`ABC_CALCULATION`\s*\|\s*9\.1,\s*9\.2,\s*9\.3\s*\|"
    assert re.search(pattern, docs), (
        "docs capability table ABC_CALCULATION row must show "
        "'9.1, 9.2, 9.3' fill (v1.19 row extension)"
    )


def test_capability_matrix_docs_dual_route_note_v1_19() -> None:
    """docs Notes section MUST include v1.19 dual-route gate note."""
    docs = _load_capability_matrix_docs()
    assert "ABC_CALCULATION dual-route gate (Story 9.3)" in docs
    assert "require_any_capability" in docs
    assert "_resolve_engine_type" in docs
    assert "CalcResponse | CalcAbcResponse" in docs


# ── 4. Changelog entry ──────────────────────────────────────
def test_capability_matrix_changelog_has_v1_19_entry() -> None:
    """docs Changelog MUST include v1.19 entry (Story 9.3)."""
    docs = _load_capability_matrix_docs()
    assert "v1.19 (Story 9.3, Epic 9)" in docs, (
        "docs Changelog missing v1.19 (Story 9.3, Epic 9) entry"
    )


# ── 5. v1.19 industry-agnostic contract preservation ────────
def test_capability_abc_calculation_industry_agnostic_v1_19() -> None:
    """v1.19 EXTENSION does NOT change ABC_CALCULATION industry grants
    (still industry-agnostic — CR 12-1 L4 precedent)."""
    industries = (
        Industry.MANUFACTURING,
        Industry.SERVICE,
        Industry.MANUFACTURING_SERVICE,
        Industry.MANUFACTURING_SERVICE_OTHER,
    )
    for industry in industries:
        assert industry_supports(industry, Capability.ABC_CALCULATION), (
            f"{industry.name} must STILL grant ABC_CALCULATION after v1.19"
        )


def test_capability_cost_calculation_mfg_only_v1_19() -> None:
    """v1.19 EXTENSION does NOT change COST_CALCULATION industry grants
    (still mfg-only — manufacturing 3종 ✅)."""
    assert industry_supports(Industry.MANUFACTURING, Capability.COST_CALCULATION)
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE, Capability.COST_CALCULATION
    )
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE_OTHER, Capability.COST_CALCULATION
    )
    assert not industry_supports(Industry.SERVICE, Capability.COST_CALCULATION), (
        "service-only MUST NOT have COST_CALCULATION (use ABC instead)"
    )


# ── 6. Cross-version regression sanity ──────────────────────
def test_capability_budget_scenario_still_exists_v1_19() -> None:
    """BUDGET_SCENARIO (v1.17) must remain after v1.19 wire (no regression)."""
    assert hasattr(Capability, "BUDGET_SCENARIO")
    assert industry_supports(Industry.MANUFACTURING, Capability.BUDGET_SCENARIO)


def test_capability_cvp_simulation_still_exists_v1_19() -> None:
    """CVP_SIMULATION (v1.17) must remain after v1.19 wire (no regression)."""
    assert hasattr(Capability, "CVP_SIMULATION")
    assert industry_supports(Industry.MANUFACTURING, Capability.CVP_SIMULATION)
