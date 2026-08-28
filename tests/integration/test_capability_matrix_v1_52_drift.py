"""tests.integration.test_capability_matrix_v1_52_drift — Phase 26 capability matrix drift detector.

Phase 26 wire (cj-style 185번째) — FinOps Cost Anomaly ML Prediction capability
matrix v1.52 EXTENSION 1 NEW row drift detector.

This test enforces:
- 3-way gate: matrix.md ↔ Capability enum ↔ 4-industry grants
- FINOPS_COST_ANOMALY_ML_PREDICTION 1 NEW row verified
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


def _read_capability_module() -> str:
    """Read apps/api/core/capability.py source."""
    path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "apps",
        "api",
        "core",
        "capability.py",
    )
    with open(path, encoding="utf-8") as f:
        return f.read()


def _read_dependencies_capability_module() -> str:
    """Read apps/api/dependencies/capability.py source."""
    path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "apps",
        "api",
        "dependencies",
        "capability.py",
    )
    with open(path, encoding="utf-8") as f:
        return f.read()


# ── 12 NEW pytest cases ──────────────────────────────────────────────────
def test_capability_matrix_v1_52_header_present() -> None:
    """Test 1: capability matrix is at v1.52."""
    matrix = _read_matrix()
    # Header must mention v1.52 (Phase 26 wire EXTENSION).
    assert "Capability Matrix (v1.52)" in matrix, (
        "Capability matrix header must be at v1.52 after Phase 26 wire"
    )


def test_capability_matrix_phase_26_entry_present() -> None:
    """Test 2: Phase 26 entry exists in matrix."""
    matrix = _read_matrix()
    assert "Phase 26" in matrix, "Phase 26 entry must exist"
    assert "FINOPS_COST_ANOMALY_ML_PREDICTION" in matrix, (
        "FINOPS_COST_ANOMALY_ML_PREDICTION must be referenced"
    )


def test_capability_matrix_cost_anomaly_ml_prediction_4_industry_grants() -> None:
    """Test 3: FINOPS_COST_ANOMALY_ML_PREDICTION has 4-industry grants."""
    matrix = _read_matrix()
    pattern = (
        r"\|\s*`FINOPS_COST_ANOMALY_ML_PREDICTION`\s*\|\s*Phase 26\s*\|"
        r"\s*✅\s*\|\s*✅\s*\|\s*✅\s*\|\s*✅\s*\|"
    )
    assert re.search(pattern, matrix), (
        "FINOPS_COST_ANOMALY_ML_PREDICTION must have 4-industry grants"
    )


def test_capability_matrix_lists_all_18_finops_capabilities() -> None:
    """Test 4: capability matrix has all 18 FINOPS capabilities listed."""
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
        "FINOPS_COST_ANOMALY_ML_PREDICTION",
    ]
    for cap in expected:
        assert cap in matrix, f"Missing capability {cap}"


def test_capability_enum_finops_cost_anomaly_ml_prediction_registered() -> None:
    """Test 5: Capability enum has FINOPS_COST_ANOMALY_ML_PREDICTION entry."""
    src = _read_capability_module()
    pattern = (
        r"FINOPS_COST_ANOMALY_ML_PREDICTION\s*=\s*"
        r"[\"']finops_cost_anomaly_ml_prediction[\"']"
    )
    assert re.search(pattern, src), (
        "Capability.FINOPS_COST_ANOMALY_ML_PREDICTION must be registered"
        " with value 'finops_cost_anomaly_ml_prediction'"
    )


def test_capability_enum_4_industry_grants_for_cost_anomaly_ml_prediction() -> None:
    """Test 6: Capability enum grants FINOPS_COST_ANOMALY_ML_PREDICTION to all 4 industries."""
    src = _read_capability_module()
    # Count occurrences of `Capability.FINOPS_COST_ANOMALY_ML_PREDICTION,`
    # inside the 4 industry maps. Should be 4 (one per industry).
    pattern = r"Capability\.FINOPS_COST_ANOMALY_ML_PREDICTION\s*,\s*$"
    matches = re.findall(pattern, src, re.MULTILINE)
    assert len(matches) == 4, (
        f"Expected 4 industry grants for FINOPS_COST_ANOMALY_ML_PREDICTION,"
        f" got {len(matches)}"
    )


def test_capability_matrix_finops_cost_anomaly_ml_prediction_industry_agnostic() -> None:
    """Test 7: FINOPS_COST_ANOMALY_ML_PREDICTION explicitly industry-agnostic."""
    matrix = _read_matrix()
    # Phase 26 entry description must mention industry-agnostic per CR 12-1 L4.
    pattern = r"FINOPS_COST_ANOMALY_ML_PREDICTION.*industry.agnostic"
    assert re.search(pattern, matrix, re.DOTALL), (
        "FINOPS_COST_ANOMALY_ML_PREDICTION entry must mention"
        " industry-agnostic per CR 12-1 L4"
    )


def test_capability_matrix_finops_cost_anomaly_ml_prediction_ad_55() -> None:
    """Test 8: FINOPS_COST_ANOMALY_ML_PREDICTION entry references AD-55."""
    matrix = _read_matrix()
    # AD-55 should appear in the matrix somewhere.
    assert "AD-55" in matrix, "AD-55 must be referenced in matrix"


def test_capability_matrix_phase_26_8_acs() -> None:
    """Test 9: Phase 26 entry references 8 ACs §F42.1~§F42.8."""
    matrix = _read_matrix()
    # At least one §F42.N reference should exist.
    for i in range(1, 9):
        ac_ref = f"§F42.{i}"
        assert ac_ref in matrix, f"Phase 26 must reference {ac_ref}"


def test_capability_matrix_d_finops_15_honest_defer() -> None:
    """Test 10: D-FINOPS-15 honestly DEFER preserved."""
    matrix = _read_matrix()
    assert "D-FINOPS-15" in matrix, "D-FINOPS-15 must be referenced in matrix"
    assert "DEFER" in matrix, "DEFER keyword must be present"


def test_dependencies_capability_require_finops_cost_anomaly_ml_prediction() -> None:
    """Test 11: require_finops_cost_anomaly_ml_prediction dependency helper registered."""
    deps_src = _read_dependencies_capability_module()
    # __all__ export entry.
    assert '"require_finops_cost_anomaly_ml_prediction"' in deps_src, (
        "require_finops_cost_anomaly_ml_prediction must be in __all__"
    )
    # helper definition.
    pattern = (
        r"require_finops_cost_anomaly_ml_prediction\s*=\s*"
        r"require_capability\(\s*Capability\.FINOPS_COST_ANOMALY_ML_PREDICTION\s*\)"
    )
    assert re.search(pattern, deps_src), (
        "require_finops_cost_anomaly_ml_prediction must call"
        " require_capability(Capability.FINOPS_COST_ANOMALY_ML_PREDICTION)"
    )


def test_capability_matrix_v1_52_5_model_ensemble_consensus() -> None:
    """Test 12: Phase 26 entry mentions 5-model ensemble consensus decision."""
    matrix = _read_matrix()
    # 5 model types (prophet + lstm + arima + isolation_forest + autoencoder)
    # should be referenced.
    for model in ("prophet", "lstm", "arima", "isolation_forest", "autoencoder"):
        assert model in matrix, f"Phase 26 must reference model type {model}"
