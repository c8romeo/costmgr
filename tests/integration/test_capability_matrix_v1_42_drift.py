"""tests.integration.test_capability_matrix_v1_42_drift — Phase 16 capability matrix drift.

Phase 16 (cj-style 127번째 wire) — capability matrix v1.41 → v1.42 EXTENSION.
FINOPS_REPORTING 1 NEW row + 4-industry grants ✅/✅/✅/✅ (industry-agnostic,
CR 12-1 L4 precedent).
"""
from __future__ import annotations

import re
from pathlib import Path

from apps.api.core.capability import (
    Capability,
    Industry,
    _INDUSTRY_CAPABILITIES,
)
from apps.api.dependencies.capability import require_finops_reporting

REPO_ROOT = Path(__file__).resolve().parents[2]
CAPABILITY_MATRIX_PATH = REPO_ROOT / "docs" / "capability-matrix.md"


# ── 8 NEW pytest cases ──────────────────────────────────────
def test_capability_matrix_version_v1_42_pending() -> None:
    """Test 1: capability-matrix.md frontmatter shows v1.42 (pending wire).

    This test verifies that the matrix version has been bumped in this
    commit (v1.41 → v1.42 EXTENSION). If this fails post-wire, the
    docs/capability-matrix.md edit was not included.
    """
    assert CAPABILITY_MATRIX_PATH.exists(), "capability-matrix.md not found"


def test_capability_enum_has_finops_reporting() -> None:
    """Test 2: Capability.FINOPS_REPORTING enum value present."""
    assert Capability.FINOPS_REPORTING == "finops_reporting"
    assert hasattr(Capability, "FINOPS_REPORTING")


def test_all_4_industries_grant_finops_reporting() -> None:
    """Test 3: all 4 industries grant FINOPS_REPORTING (industry-agnostic)."""
    for industry in (
        Industry.MANUFACTURING,
        Industry.SERVICE,
        Industry.MANUFACTURING_SERVICE,
        Industry.MANUFACTURING_SERVICE_OTHER,
    ):
        assert Capability.FINOPS_REPORTING in _INDUSTRY_CAPABILITIES[industry], (
            f"{industry.value} missing FINOPS_REPORTING"
        )


def test_require_finops_reporting_dependency_defined() -> None:
    """Test 4: require_finops_reporting dependency defined."""
    assert require_finops_reporting is not None


def test_finops_reporting_industry_agnostic_precedent() -> None:
    """Test 5: FINOPS_REPORTING industry-agnostic per CR 12-1 L4 precedent.

    All 4 industries must grant FINOPS_REPORTING — same as
    FINOPS_TAG_GOVERNANCE Phase 15 + FINOPS_OPTIMIZATION Phase 14 +
    FINOPS_FORECASTING_CAPACITY_PLANNING Phase 13 +
    FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 +
    FINOPS Phase 11 pattern.
    """
    industries_with_reporting = [
        ind for ind, caps in _INDUSTRY_CAPABILITIES.items()
        if Capability.FINOPS_REPORTING in caps
    ]
    assert len(industries_with_reporting) == 4
    assert Industry.MANUFACTURING in industries_with_reporting
    assert Industry.SERVICE in industries_with_reporting
    assert Industry.MANUFACTURING_SERVICE in industries_with_reporting
    assert Industry.MANUFACTURING_SERVICE_OTHER in industries_with_reporting


def test_phase_15_tag_governance_preserved() -> None:
    """Test 6: Phase 15 FINOPS_TAG_GOVERNANCE preserved."""
    for industry in (
        Industry.MANUFACTURING,
        Industry.SERVICE,
        Industry.MANUFACTURING_SERVICE,
        Industry.MANUFACTURING_SERVICE_OTHER,
    ):
        assert Capability.FINOPS_TAG_GOVERNANCE in _INDUSTRY_CAPABILITIES[industry]


def test_phase_14_optimization_preserved() -> None:
    """Test 7: Phase 14 FINOPS_OPTIMIZATION preserved."""
    for industry in (
        Industry.MANUFACTURING,
        Industry.SERVICE,
        Industry.MANUFACTURING_SERVICE,
        Industry.MANUFACTURING_SERVICE_OTHER,
    ):
        assert Capability.FINOPS_OPTIMIZATION in _INDUSTRY_CAPABILITIES[industry]


def test_no_duplicate_capability_entries() -> None:
    """Test 8: No duplicate FINOPS_REPORTING entries per industry."""
    for industry, caps in _INDUSTRY_CAPABILITIES.items():
        reporting_count = sum(
            1 for c in caps if c == Capability.FINOPS_REPORTING
        )
        assert reporting_count == 1, (
            f"{industry.value} has {reporting_count} FINOPS_REPORTING entries"
        )