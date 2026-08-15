"""tests.integration.test_capability_matrix_v1_17_drift — Story 7.1 + 8.1 capability pin.

Pins v1.17 capability additions (2 NEW):
- BUDGET_SCENARIO  (Story 8.1) — POST /budget/scenarios + GET list + GET detail
- CVP_SIMULATION   (Story 7.1) — POST /simulation/cvp/compute + GET baseline

Industry matrix (per docs/capability-matrix.md v1.17):
- Manufacturing (3 variants) ✅ enabled
- Service-only ✅ enabled (industry-agnostic financial baseline — CR 12-1 L4)

CR 12-1 L4 precedent: both BUDGET_SCENARIO (financial planning) and
CVP_SIMULATION (financial planning) are documented as industry-agnostic
gate entries. Capability enum is industry-agnostic — the route uses
`require_role("owner"|"member")` for write access.

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

# ── 2 NEW capabilities per v1.17 ─────────────────────────────
_NEW_V1_17_CAPABILITIES: tuple[Capability, ...] = (
    Capability.BUDGET_SCENARIO,
    Capability.CVP_SIMULATION,
)


def _load_capability_matrix_docs() -> str:
    """Read the capability matrix docs for drift detection."""
    repo_root = Path(__file__).resolve().parents[2]
    return (
        repo_root / "docs" / "capability-matrix.md"
    ).read_text(encoding="utf-8")


# ── 1. BUDGET_SCENARIO enum + 4-industry pin (industry-agnostic) ──
def test_capability_budget_scenario_enum_exists() -> None:
    """`Capability.BUDGET_SCENARIO` enum value must exist (v1.17 — Story 8.1)."""
    assert hasattr(Capability, "BUDGET_SCENARIO")
    assert Capability.BUDGET_SCENARIO.value == "budget_scenario"


def test_capability_budget_scenario_wired_manufacturing() -> None:
    """Manufacturing industry matrix includes BUDGET_SCENARIO (v1.17 — Story 8.1)."""
    assert industry_supports(Industry.MANUFACTURING, Capability.BUDGET_SCENARIO)


def test_capability_budget_scenario_wired_service_only() -> None:
    """Service-only industry matrix INCLUDES BUDGET_SCENARIO (industry-agnostic)."""
    assert industry_supports(Industry.SERVICE, Capability.BUDGET_SCENARIO)


def test_capability_budget_scenario_wired_mfg_service() -> None:
    """mfg+service industry matrix includes BUDGET_SCENARIO (v1.17 — Story 8.1)."""
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE, Capability.BUDGET_SCENARIO
    )


def test_capability_budget_scenario_wired_mixed() -> None:
    """Mixed industry matrix includes BUDGET_SCENARIO (v1.17 — Story 8.1)."""
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE_OTHER, Capability.BUDGET_SCENARIO
    )


# ── 2. CVP_SIMULATION enum + 4-industry pin (industry-agnostic) ──
def test_capability_cvp_simulation_enum_exists() -> None:
    """`Capability.CVP_SIMULATION` enum value must exist (v1.17 — Story 7.1)."""
    assert hasattr(Capability, "CVP_SIMULATION")
    assert Capability.CVP_SIMULATION.value == "cvp_simulation"


def test_capability_cvp_simulation_wired_manufacturing() -> None:
    """Manufacturing industry matrix includes CVP_SIMULATION (v1.17 — Story 7.1)."""
    assert industry_supports(Industry.MANUFACTURING, Capability.CVP_SIMULATION)


def test_capability_cvp_simulation_wired_service_only() -> None:
    """Service-only industry matrix INCLUDES CVP_SIMULATION (industry-agnostic).

    CR 12-1 L4 precedent: CVP is financial planning infrastructure,
    granted to all 4 industries including service-only. This mirrors
    BUDGET_SCENARIO + BACKUP_EXPORT + TWO_FACTOR_AUTH + ACCOUNT_DELETION
    industry-agnostic patterns.
    """
    assert industry_supports(Industry.SERVICE, Capability.CVP_SIMULATION)


def test_capability_cvp_simulation_wired_mfg_service() -> None:
    """mfg+service industry matrix includes CVP_SIMULATION (v1.17 — Story 7.1)."""
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE, Capability.CVP_SIMULATION
    )


def test_capability_cvp_simulation_wired_mixed() -> None:
    """Mixed industry matrix includes CVP_SIMULATION (v1.17 — Story 7.1)."""
    assert industry_supports(
        Industry.MANUFACTURING_SERVICE_OTHER, Capability.CVP_SIMULATION
    )


# ── 3. Docs-version pin (drift detector) ─────────────────────
def test_capability_matrix_docs_pin_v1_17() -> None:
    """docs/capability-matrix.md must declare v1.17 (Story 7.1 + 8.1 wire)."""
    docs = _load_capability_matrix_docs()
    assert "# Capability Matrix (v1.17)" in docs, (
        "docs/capability-matrix.md title must be v1.17 (Story 7.1 + 8.1)"
    )
    assert "v1.17" in docs
    assert "Story 7.1" in docs
    assert "Story 8.1" in docs
    assert "CVP_SIMULATION" in docs
    assert "BUDGET_SCENARIO" in docs


# ── 4. Docs table-row pins (drift detector) ─────────────────
def test_capability_matrix_docs_table_has_budget_scenario_row() -> None:
    """docs capability table must list the v1.17 BUDGET_SCENARIO row."""
    docs = _load_capability_matrix_docs()
    pattern = r"\|\s*`BUDGET_SCENARIO`\s*\|"
    assert re.search(pattern, docs), (
        "docs capability table missing row for BUDGET_SCENARIO"
    )


def test_capability_matrix_docs_table_has_cvp_simulation_row() -> None:
    """docs capability table must list the v1.17 CVP_SIMULATION row."""
    docs = _load_capability_matrix_docs()
    pattern = r"\|\s*`CVP_SIMULATION`\s*\|"
    assert re.search(pattern, docs), (
        "docs capability table missing row for CVP_SIMULATION"
    )


# ── 5. Cross-pin: enum ↔ docs (drift detector) ────────────────
def test_capability_matrix_enum_count_matches_table_rows_v1_17() -> None:
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
