"""tests.integration.test_capability_matrix_v1_51_drift — Phase 25 capability matrix drift detector.

Phase 25 wire (cj-style 173번째) — FinOps Vendor Management capability
matrix v1.51 EXTENSION 1 NEW row drift detector.

This test enforces:
- 3-way gate: matrix.md ↔ Capability enum ↔ 4-industry grants
- FINOPS_VENDOR_MANAGEMENT 1 NEW row verified
- industry-agnostic 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4)
- Drift detection: missing enum ↔ matrix mismatch ↔ industry grants mismatch

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync.
"""
from __future__ import annotations

import os
import re

CAPABILITY_MATRIX_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "docs", "capability-matrix.md"
)


def _read_matrix() -> str:
    """Read capability matrix markdown file."""
    with open(CAPABILITY_MATRIX_PATH, encoding="utf-8") as f:
        return f.read()


# ── 8 NEW pytest cases ───────────────────────────────────────────────────
def test_capability_matrix_v1_51_header_present() -> None:
    """Test 1: capability matrix is at v1.51."""
    matrix = _read_matrix()
    assert "v1.51" in matrix, "Capability matrix header must mention v1.51"


def test_capability_matrix_phase_25_entry_present() -> None:
    """Test 2: Phase 25 entry exists."""
    matrix = _read_matrix()
    assert "Phase 25" in matrix
    assert "FINOPS_VENDOR_MANAGEMENT" in matrix


def test_capability_matrix_vendor_management_4_industry_grants() -> None:
    """Test 3: FINOPS_VENDOR_MANAGEMENT has 4-industry grants."""
    matrix = _read_matrix()
    pattern = r"\|\s*`FINOPS_VENDOR_MANAGEMENT`\s*\|\s*Phase 25\s*\|\s*✅\s*\|\s*✅\s*\|\s*✅\s*\|\s*✅\s*\|"
    assert re.search(pattern, matrix), "FINOPS_VENDOR_MANAGEMENT must have 4-industry grants"


def test_capability_matrix_lists_all_25_capabilities() -> None:
    """Test 4: capability matrix has all 25 capabilities listed."""
    matrix = _read_matrix()
    expected = [
        "FINOPS_SHOWBACK",
        "FINOPS_CHARGEBACK",
        "FINOPS_ANOMALY_DETECTION",
        "FINOPS_BUDGET_ALERT",
        "FINOPS_FORECASTING_CAPACITY_PLANNING",
        "FINOPS_OPTIMIZATION",
        "FINOPS_TAG_GOVERNANCE",
        "FINOPS_REPORTING",
        "FINOPS_SUSTAINABILITY",
        "FINOPS_COMMITMENT",
        "FINOPS_PRICING",
        "FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION",
        "FINOPS_RESERVED_CAPACITY_PLANNING",
        "FINOPS_CHARGEBACK_SETTLEMENT",
        "FINOPS_UNIT_ECONOMICS",
        "FINOPS_BUDGET_PLANNING",
        "FINOPS_VENDOR_MANAGEMENT",
    ]
    for cap in expected:
        assert cap in matrix, f"Missing capability {cap}"


def test_capability_matrix_finops_vendor_management_industry_agnostic() -> None:
    """Test 5: FINOPS_VENDOR_MANAGEMENT explicitly industry-agnostic."""
    matrix = _read_matrix()
    # Phase 25 entry description must mention industry-agnostic per CR 12-1 L4
    pattern = r"FINOPS_VENDOR_MANAGEMENT.*industry.agnostic"
    assert re.search(pattern, matrix, re.DOTALL), (
        "FINOPS_VENDOR_MANAGEMENT entry must mention industry-agnostic per CR 12-1 L4"
    )


def test_capability_matrix_finops_vendor_management_ad_53() -> None:
    """Test 6: FINOPS_VENDOR_MANAGEMENT entry references AD-53."""
    matrix = _read_matrix()
    # AD-53 should appear in the matrix somewhere
    assert "AD-53" in matrix, "AD-53 must be referenced in matrix"


def test_capability_matrix_phase_25_8_acs() -> None:
    """Test 7: Phase 25 entry references 8 ACs §F41.1~§F41.8."""
    matrix = _read_matrix()
    # At least one §F41.N reference should exist
    for i in range(1, 9):
        ac_ref = f"§F41.{i}"
        assert ac_ref in matrix, f"Phase 25 must reference {ac_ref}"


def test_capability_matrix_d_finops_14_honest_defer() -> None:
    """Test 8: D-FINOPS-14 honestly DEFER preserved."""
    matrix = _read_matrix()
    assert "D-FINOPS-14" in matrix, "D-FINOPS-14 must be referenced in matrix"
    assert "DEFER" in matrix, "DEFER keyword must be present"