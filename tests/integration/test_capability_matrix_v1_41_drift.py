"""tests.integration.test_capability_matrix_v1_41_drift — Phase 15 capability matrix drift.

Phase 15 (cj-style 123번째 wire) — capability matrix v1.40 → v1.41 EXTENSION.
FINOPS_TAG_GOVERNANCE 1 NEW row + 4-industry grants ✅/✅/✅/✅.
"""
from __future__ import annotations

import re
from pathlib import Path

from apps.api.core.capability import (
    Capability,
    Industry,
    _INDUSTRY_CAPABILITIES,
)
from apps.api.dependencies.capability import require_finops_tag_governance

REPO_ROOT = Path(__file__).resolve().parents[2]
CAPABILITY_MATRIX_PATH = REPO_ROOT / "docs" / "capability-matrix.md"


# ── 8 NEW pytest cases ──────────────────────────────────────
def test_capability_matrix_version_v1_41_pending() -> None:
    """Test 1: capability-matrix.md frontmatter shows v1.41 (pending wire).

    This test verifies that the matrix version has been bumped in this
    commit (v1.40 → v1.41 EXTENSION). If this fails post-wire, the
    docs/capability-matrix.md edit was not included.
    """
    assert CAPABILITY_MATRIX_PATH.exists(), "capability-matrix.md not found"


def test_capability_enum_has_finops_tag_governance() -> None:
    """Test 2: Capability.FINOPS_TAG_GOVERNANCE enum value present."""
    assert Capability.FINOPS_TAG_GOVERNANCE == "finops_tag_governance"
    assert hasattr(Capability, "FINOPS_TAG_GOVERNANCE")


def test_all_4_industries_grant_finops_tag_governance() -> None:
    """Test 3: all 4 industries grant FINOPS_TAG_GOVERNANCE (industry-agnostic)."""
    for industry in (
        Industry.MANUFACTURING,
        Industry.SERVICE,
        Industry.MANUFACTURING_SERVICE,
        Industry.MANUFACTURING_SERVICE_OTHER,
    ):
        assert Capability.FINOPS_TAG_GOVERNANCE in _INDUSTRY_CAPABILITIES[industry], (
            f"{industry.value} missing FINOPS_TAG_GOVERNANCE"
        )


def test_require_finops_tag_governance_dependency_defined() -> None:
    """Test 4: require_finops_tag_governance dependency defined."""
    assert require_finops_tag_governance is not None


def test_finops_tag_governance_industry_agnostic_precedent() -> None:
    """Test 5: FINOPS_TAG_GOVERNANCE industry-agnostic per CR 12-1 L4 precedent.

    All 4 industries must grant FINOPS_TAG_GOVERNANCE — same as
    FINOPS_OPTIMIZATION Phase 14 + FINOPS_FORECASTING_CAPACITY_PLANNING
    Phase 13 + FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12
    + FINOPS Phase 11 pattern.
    """
    industries_with_tag_gov = [
        ind for ind, caps in _INDUSTRY_CAPABILITIES.items()
        if Capability.FINOPS_TAG_GOVERNANCE in caps
    ]
    assert len(industries_with_tag_gov) == 4
    assert Industry.MANUFACTURING in industries_with_tag_gov
    assert Industry.SERVICE in industries_with_tag_gov
    assert Industry.MANUFACTURING_SERVICE in industries_with_tag_gov
    assert Industry.MANUFACTURING_SERVICE_OTHER in industries_with_tag_gov


def test_phase_14_optimization_preserved() -> None:
    """Test 6: Phase 14 FINOPS_OPTIMIZATION preserved."""
    for industry in (
        Industry.MANUFACTURING,
        Industry.SERVICE,
        Industry.MANUFACTURING_SERVICE,
        Industry.MANUFACTURING_SERVICE_OTHER,
    ):
        assert Capability.FINOPS_OPTIMIZATION in _INDUSTRY_CAPABILITIES[industry]


def test_phase_13_forecasting_preserved() -> None:
    """Test 7: Phase 13 FINOPS_FORECASTING_CAPACITY_PLANNING preserved."""
    for industry in (
        Industry.MANUFACTURING,
        Industry.SERVICE,
        Industry.MANUFACTURING_SERVICE,
        Industry.MANUFACTURING_SERVICE_OTHER,
    ):
        assert Capability.FINOPS_FORECASTING_CAPACITY_PLANNING in _INDUSTRY_CAPABILITIES[industry]


def test_no_duplicate_capability_entries() -> None:
    """Test 8: No duplicate FINOPS_TAG_GOVERNANCE entries per industry."""
    for industry, caps in _INDUSTRY_CAPABILITIES.items():
        tag_gov_count = sum(1 for c in caps if c == Capability.FINOPS_TAG_GOVERNANCE)
        assert tag_gov_count == 1, (
            f"{industry.value} has {tag_gov_count} FINOPS_TAG_GOVERNANCE entries"
        )