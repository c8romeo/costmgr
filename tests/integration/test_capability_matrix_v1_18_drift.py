"""tests.integration.test_capability_matrix_v1_18_drift — Story 9.1 capability pin.

Pins v1.18 capability addition (1 NEW):
- ABC_CALCULATION  (Story 9.1) — POST /abc/cost-pools + /activities +
  /drivers/validate + /validate (4 NEW endpoints, PRD §F9.1 verbatim)

Industry matrix (per docs/capability-matrix.md v1.18 → v1.19 EXTENSION):
- Manufacturing (3 variants) ✅ enabled
- Service-only ✅ enabled (industry-agnostic financial baseline — CR 12-1 L4)

v1.19 EXTENSION (Story 9.3, Epic 9) — no NEW capability row.
Existing ABC_CALCULATION row fill changes from "9.1, 9.2" to
"9.1, 9.2, 9.3" (Story 9.3 dual-route gate via
`require_any_capability(COST_CALCULATION, ABC_CALCULATION)`).

CR 12-1 L4 precedent: ABC_CALCULATION is documented as industry-agnostic
gate entry (cost accounting financial baseline). Capability enum is
industry-agnostic — the route uses `require_role("owner"|"member")` for
write access.

CR 11-3 lesson: capability drift across industry matrices is the #1
source of cross-tenant write leaks. Each capability addition needs a
4-industry pin + a docs-version pin + a table-row pin.
"""

from __future__ import annotations

import re
from pathlib import Path

from apps.api.core.capability import (
    Capability,
    industry_supports,
)
from packages.services.m0_onboarding.industry_menu import Industry

# ── 1 NEW capability per v1.18 (extended to v1.19, no new rows) ─
_NEW_V1_18_CAPABILITIES: tuple[Capability, ...] = (
    Capability.ABC_CALCULATION,
)


def _load_capability_matrix_docs() -> str:
    """Read the capability matrix docs for drift detection."""
    repo_root = Path(__file__).resolve().parents[2]
    return (
        repo_root / "docs" / "capability-matrix.md"
    ).read_text(encoding="utf-8")


# ── 1. ABC_CALCULATION enum + 4-industry pin (industry-agnostic) ──
def test_capability_abc_calculation_enum_exists() -> None:
    """`Capability.ABC_CALCULATION` enum value must exist (v1.18 — Story 9.1)."""
    assert hasattr(Capability, "ABC_CALCULATION")
    assert Capability.ABC_CALCULATION.value == "abc_calculation"


def test_capability_abc_calculation_wired_manufacturing() -> None:
    """Manufacturing industry matrix includes ABC_CALCULATION (v1.18 — Story 9.1)."""
    assert industry_supports(Industry.MANUFACTURING, Capability.ABC_CALCULATION)


def test_capability_abc_calculation_wired_service_only() -> None:
    """Service-only industry matrix INCLUDES ABC_CALCULATION (industry-agnostic).

    CR 12-1 L4 precedent: ABC is financial planning infrastructure,
    granted to all 4 industries including service-only. This mirrors
    BUDGET_SCENARIO + CVP_SIMULATION + BACKUP_EXPORT + TWO_FACTOR_AUTH +
    ACCOUNT_DELETION industry-agnostic patterns.
    """
    assert industry_supports(Industry.SERVICE, Capability.ABC_CALCULATION)


def test_capability_abc_calculation_wired_mfg_service() -> None:
    """mfg+service industry matrix includes ABC_CALCULATION (v1.18 — Story 9.1)."""
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE, Capability.ABC_CALCULATION
    )


def test_capability_abc_calculation_wired_mixed() -> None:
    """Mixed industry matrix includes ABC_CALCULATION (v1.18 — Story 9.1)."""
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE_OTHER, Capability.ABC_CALCULATION
    )


# ── 2. Docs-version pin (drift detector — extended to v1.19) ───
def test_capability_matrix_docs_pin_v1_18_v1_19() -> None:
    """docs/capability-matrix.md must declare v1.19 (current HEAD).

    v1.18 → v1.19 EXTENSION (Story 9.3) does NOT add a new capability row.
    The title is bumped to v1.19, and v1.18 markers remain in the changelog
    + table row fill (`9.1, 9.2, 9.3`).
    """
    docs = _load_capability_matrix_docs()
    assert "# Capability Matrix (v1.19)" in docs, (
        "docs/capability-matrix.md title must be v1.19 (Story 9.3 wire)"
    )
    assert "v1.18" in docs, (
        "docs/capability-matrix.md must retain v1.18 markers (changelog)"
    )
    assert "v1.19" in docs
    assert "Story 9.3" in docs
    assert "ABC_CALCULATION" in docs


# ── 3. Docs table-row pins (drift detector) ─────────────────
def test_capability_matrix_docs_table_has_abc_calculation_row() -> None:
    """docs capability table must list the v1.18 ABC_CALCULATION row
    with v1.19 fill (Story 9.3 row extension)."""
    docs = _load_capability_matrix_docs()
    pattern = r"\|\s*`ABC_CALCULATION`\s*\|\s*9\.1,\s*9\.2,\s*9\.3\s*\|"
    assert re.search(pattern, docs), (
        "docs capability table ABC_CALCULATION row must show "
        "'9.1, 9.2, 9.3' fill (v1.19 row extension)"
    )


def test_capability_matrix_docs_dual_route_note_present() -> None:
    """docs Notes section must include v1.19 dual-route gate note
    (PRD §F9.3 + A29 forward-lock + AD-19)."""
    docs = _load_capability_matrix_docs()
    assert "ABC_CALCULATION dual-route gate (Story 9.3)" in docs, (
        "docs Notes section missing v1.19 dual-route gate note"
    )
    assert "require_any_capability" in docs


# ── 4. Cross-pin: enum ↔ docs (drift detector) ────────────────
def test_capability_matrix_enum_count_matches_table_rows_v1_19() -> None:
    """Capability enum count must match the docs table row count.

    Drift detector: a discrepancy means either the enum has values
    not documented, or the docs has rows for removed values. Either
    way the team must reconcile.
    """
    docs = _load_capability_matrix_docs()
    table_rows = re.findall(
        r"^\|\s*`([A-Z_]+)`\s*\|",
        docs,
        re.MULTILINE,
    )
    enum_count = len(Capability)
    cap_names = {c.name for c in Capability}
    table_name_set = set(table_rows)
    assert len(table_rows) == enum_count, (
        f"drift: docs table has {len(table_rows)} rows, "
        f"Capability enum has {enum_count} values. "
        f"Missing from docs: {cap_names - table_name_set}. "
        f"Extra in docs: {table_name_set - cap_names}"
    )


# ── 5. v1.18 capability count + matrix sanity (v1.19 EXTENSION) ─
def test_capability_v1_18_count_is_1() -> None:
    """v1.18 adds exactly 1 NEW capability (ABC_CALCULATION).

    v1.19 EXTENSION (Story 9.3) adds 0 NEW capabilities — uses existing
    `require_any_capability(COST_CALCULATION, ABC_CALCULATION)` ANY-OF
    semantics for the dual-route gate.
    """
    assert len(_NEW_V1_18_CAPABILITIES) == 1
    assert _NEW_V1_18_CAPABILITIES[0] is Capability.ABC_CALCULATION


def test_capability_v1_18_industry_agnostic_pattern() -> None:
    """ABC_CALCULATION is industry-agnostic — must grant all 4 industries.

    CR 12-1 L4 precedent (financial baseline infrastructure).
    """
    industries = (
        Industry.MANUFACTURING,
        Industry.SERVICE,
        Industry.MANUFACTURING_SERVICE,
        Industry.MANUFACTURING_SERVICE_OTHER,
    )
    for industry in industries:
        assert industry_supports(industry, Capability.ABC_CALCULATION), (
            f"{industry.name} must grant ABC_CALCULATION (industry-agnostic)"
        )


def test_capability_dual_route_cost_calculation_intact() -> None:
    """COST_CALCULATION capability must remain (mfg-only, dual-route gate).

    v1.19 dual-route gate uses
    `require_any_capability(COST_CALCULATION, ABC_CALCULATION)` —
    COST_CALCULATION is mfg-only (mfg 3종) and ABC_CALCULATION is
    industry-agnostic. Service-only tenants pass via ABC_CALCULATION.
    """
    assert hasattr(Capability, "COST_CALCULATION")
    assert industry_supports(Industry.MANUFACTURING, Capability.COST_CALCULATION)
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE, Capability.COST_CALCULATION
    )
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE_OTHER, Capability.COST_CALCULATION
    )


# ── 6. Capability matrix regression sanity ───────────────────
def test_capability_budget_scenario_still_exists_v1_18() -> None:
    """BUDGET_SCENARIO (v1.17) must remain after v1.18 wire (no regression)."""
    assert hasattr(Capability, "BUDGET_SCENARIO")
    assert industry_supports(Industry.MANUFACTURING, Capability.BUDGET_SCENARIO)
    assert industry_supports(Industry.SERVICE, Capability.BUDGET_SCENARIO)


def test_capability_cvp_simulation_still_exists_v1_18() -> None:
    """CVP_SIMULATION (v1.17) must remain after v1.18 wire (no regression)."""
    assert hasattr(Capability, "CVP_SIMULATION")
    assert industry_supports(Industry.MANUFACTURING, Capability.CVP_SIMULATION)
    assert industry_supports(Industry.SERVICE, Capability.CVP_SIMULATION)
