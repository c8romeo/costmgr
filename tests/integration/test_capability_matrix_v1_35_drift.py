# tests/integration/test_capability_matrix_v1_35_drift.py —
# Phase 10 T7 (cj-style 103번째 wire) — Capability matrix v1.35
# drift detector. 4 NEW pytest cases verifying that:
#   - matrix version is v1.35
#   - 4 INDUSTRY_CAPABILITIES blocks all include Capability.SLO_ENGINEERING
#   - Capability enum has SLO_ENGINEERING entry
#   - require_slo_engineering dependency exists
import pytest

from apps.api.core.capability import (
    Capability,
    INDUSTRY_CAPABILITIES,
)
from apps.api.dependencies.capability import (
    require_slo_engineering,
)


def test_capability_matrix_version_is_v1_35():
    from pathlib import Path
    repo_root = Path(__file__).resolve().parents[2]
    matrix = repo_root / "docs" / "capability-matrix.md"
    content = matrix.read_text(encoding="utf-8")
    assert "v1.35" in content or "1.35" in content, (
        "capability-matrix.md must reference v1.35 for Phase 10"
    )


def test_capability_slo_engineering_enum_exists():
    assert hasattr(Capability, "SLO_ENGINEERING")
    assert Capability.SLO_ENGINEERING.value == "slo_engineering"


def test_all_four_industries_grant_slo_engineering():
    for industry_key, capabilities in INDUSTRY_CAPABILITIES.items():
        assert Capability.SLO_ENGINEERING in capabilities, (
            f"Industry {industry_key} must grant Capability.SLO_ENGINEERING"
        )


def test_require_slo_engineering_dependency_exists():
    assert callable(require_slo_engineering)
