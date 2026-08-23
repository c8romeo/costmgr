# tests/integration/test_capability_matrix_v1_36_drift.py —
# Phase 11 T7 (cj-style 107번째 wire) — Capability matrix v1.36
# drift detector. 5 NEW pytest cases verifying that:
#   - matrix version is v1.36
#   - 4 INDUSTRY_CAPABILITIES blocks all include Capability.FINOPS_SHOWBACK
#     + Capability.FINOPS_CHARGEBACK
#   - Capability enum has FINOPS_SHOWBACK + FINOPS_CHARGEBACK entries
#   - require_finops_showback + require_finops_chargeback dependencies exist
import pytest

from apps.api.core.capability import (
    Capability,
    _INDUSTRY_CAPABILITIES,
)
from apps.api.dependencies.capability import (
    require_finops_chargeback,
    require_finops_showback,
)


def test_capability_matrix_version_is_v1_36():
    from pathlib import Path
    repo_root = Path(__file__).resolve().parents[2]
    matrix = repo_root / "docs" / "capability-matrix.md"
    content = matrix.read_text(encoding="utf-8")
    assert "v1.36" in content or "1.36" in content, (
        "capability-matrix.md must reference v1.36 for Phase 11"
    )


def test_capability_finops_showback_enum_exists():
    assert hasattr(Capability, "FINOPS_SHOWBACK")
    assert Capability.FINOPS_SHOWBACK.value == "finops_showback"


def test_capability_finops_chargeback_enum_exists():
    assert hasattr(Capability, "FINOPS_CHARGEBACK")
    assert Capability.FINOPS_CHARGEBACK.value == "finops_chargeback"


def test_all_four_industries_grant_finops_showback():
    for industry_key, capabilities in _INDUSTRY_CAPABILITIES.items():
        assert Capability.FINOPS_SHOWBACK in capabilities, (
            f"Industry {industry_key} must grant Capability.FINOPS_SHOWBACK"
        )


def test_all_four_industries_grant_finops_chargeback():
    for industry_key, capabilities in _INDUSTRY_CAPABILITIES.items():
        assert Capability.FINOPS_CHARGEBACK in capabilities, (
            f"Industry {industry_key} must grant Capability.FINOPS_CHARGEBACK"
        )


def test_require_finops_showback_dependency_exists():
    assert callable(require_finops_showback)


def test_require_finops_chargeback_dependency_exists():
    assert callable(require_finops_chargeback)
