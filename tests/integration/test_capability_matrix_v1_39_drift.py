"""tests.integration.test_capability_matrix_v1_39_drift — Phase 13 capability matrix drift.

Phase 13 (cj-style 115번째 wire) — capability matrix v1.38 → v1.39 EXTENSION.
"""
from __future__ import annotations

import re
from pathlib import Path

from apps.api.core.capability import (
    Capability,
    Industry,
    _INDUSTRY_CAPABILITIES,
)
from apps.api.dependencies.capability import (
    require_finops_anomaly_detection,
    require_finops_budget_alert,
    require_finops_forecast,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CAPABILITY_MATRIX_PATH = REPO_ROOT / "docs" / "capability-matrix.md"


# ── 4 NEW pytest cases ──────────────────────────────────────
def test_capability_matrix_version_v1_39() -> None:
    """Test 1: capability-matrix.md frontmatter shows v1.39."""
    content = CAPABILITY_MATRIX_PATH.read_text(encoding="utf-8")
    assert "# Capability Matrix (v1.39)" in content


def test_capability_matrix_has_finops_forecasting_row() -> None:
    """Test 2: capability-matrix.md has FINOPS_FORECASTING_CAPACITY_PLANNING row."""
    content = CAPABILITY_MATRIX_PATH.read_text(encoding="utf-8")
    assert "FINOPS_FORECASTING_CAPACITY_PLANNING" in content


def test_capability_matrix_has_phase_12_backfill_rows() -> None:
    """Test 3: Phase 12 backfill rows present."""
    content = CAPABILITY_MATRIX_PATH.read_text(encoding="utf-8")
    assert "FINOPS_ANOMALY_DETECTION" in content
    assert "FINOPS_BUDGET_ALERT" in content


def test_all_4_industries_grant_finops_forecasting() -> None:
    """Test 4: all 4 industries grant FINOPS_FORECASTING_CAPACITY_PLANNING."""
    for industry in (
        Industry.MANUFACTURING,
        Industry.SERVICE,
        Industry.MANUFACTURING_SERVICE,
        Industry.MANUFACTURING_SERVICE_OTHER,
    ):
        assert Capability.FINOPS_FORECASTING_CAPACITY_PLANNING in _INDUSTRY_CAPABILITIES[industry]


def test_require_finops_forecast_dependency_defined() -> None:
    """Test 5: require_finops_forecast dependency defined."""
    assert require_finops_forecast is not None


def test_require_finops_anomaly_detection_backfill() -> None:
    """Test 6: require_finops_anomaly_detection Phase 12 backfill defined."""
    assert require_finops_anomaly_detection is not None


def test_require_finops_budget_alert_backfill() -> None:
    """Test 7: require_finops_budget_alert Phase 12 backfill defined."""
    assert require_finops_budget_alert is not None


def test_capability_matrix_v1_39_drift_no_legacy_v1_37_only() -> None:
    """Test 8: drift detector confirms v1.39 is current, not legacy v1.37."""
    content = CAPABILITY_MATRIX_PATH.read_text(encoding="utf-8")
    # Check that v1.39 is mentioned (current version)
    assert re.search(r"v1\.39.*Phase 13 wire DONE", content, re.DOTALL) is not None