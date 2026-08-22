"""
tests/api/core/test_1st_release_capability_v1_27.py — Capability v1.27 EXTENSION drift detector.

1st release launch (cj-style 64번째 진입점) — T7.2 (AC #9.5) — F18.7 Capability v1.27.
- 4 NEW rows SSOT 정합 sweep (LAUNCH_LANDING + LAUNCH_TOS + LAUNCH_SUPPORT + LAUNCH_MONITORING).
- P-015 ko-KR.json SSOT drift detector 패턴 미러.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
CAPABILITY_PATH = REPO_ROOT / "apps" / "api" / "core" / "capability.py"


@pytest.fixture(scope="module")
def capability_module():
    """Load capability module (this is a real module, not a script)."""
    sys.path.insert(0, str(REPO_ROOT))
    try:
        # Clear any cached version
        if "apps.api.core.capability" in sys.modules:
            del sys.modules["apps.api.core.capability"]
        return importlib.import_module("apps.api.core.capability")
    finally:
        pass


def test_capability_module_loads(capability_module):
    assert capability_module is not None


def test_launch_landing_enum_exists(capability_module):
    """LAUNCH_LANDING enum should exist."""
    assert hasattr(capability_module.Capability, "LAUNCH_LANDING")
    assert capability_module.Capability.LAUNCH_LANDING.value == "launch_landing"


def test_launch_tos_enum_exists(capability_module):
    """LAUNCH_TOS enum should exist."""
    assert hasattr(capability_module.Capability, "LAUNCH_TOS")
    assert capability_module.Capability.LAUNCH_TOS.value == "launch_tos"


def test_launch_support_enum_exists(capability_module):
    """LAUNCH_SUPPORT enum should exist."""
    assert hasattr(capability_module.Capability, "LAUNCH_SUPPORT")
    assert capability_module.Capability.LAUNCH_SUPPORT.value == "launch_support"


def test_launch_monitoring_enum_exists(capability_module):
    """LAUNCH_MONITORING enum should exist."""
    assert hasattr(capability_module.Capability, "LAUNCH_MONITORING")
    assert capability_module.Capability.LAUNCH_MONITORING.value == "launch_monitoring"


def test_industry_supports_launch_landing_for_manufacturing(capability_module):
    """manufacturing industry supports LAUNCH_LANDING (CR 12-1 L4)."""
    from packages.services.m0_onboarding.industry_menu import Industry

    assert capability_module.industry_supports(
        Industry.MANUFACTURING, capability_module.Capability.LAUNCH_LANDING
    )


def test_industry_supports_launch_tos_for_service(capability_module):
    """service industry supports LAUNCH_TOS (CR 12-1 L4)."""
    from packages.services.m0_onboarding.industry_menu import Industry

    assert capability_module.industry_supports(
        Industry.SERVICE, capability_module.Capability.LAUNCH_TOS
    )


def test_industry_supports_launch_support_for_manufacturing_service(capability_module):
    """manufacturing_service industry supports LAUNCH_SUPPORT (CR 12-1 L4)."""
    from packages.services.m0_onboarding.industry_menu import Industry

    assert capability_module.industry_supports(
        Industry.MANUFACTURING_SERVICE, capability_module.Capability.LAUNCH_SUPPORT
    )


def test_industry_supports_launch_monitoring_for_manufacturing_service_other(capability_module):
    """manufacturing_service_other industry supports LAUNCH_MONITORING (CR 12-1 L4)."""
    from packages.services.m0_onboarding.industry_menu import Industry

    assert capability_module.industry_supports(
        Industry.MANUFACTURING_SERVICE_OTHER,
        capability_module.Capability.LAUNCH_MONITORING,
    )


def test_capability_matrix_v1_27_doc_updated():
    """docs/capability-matrix.md v1.27 should mention LAUNCH_* rows."""
    matrix_path = REPO_ROOT / "docs" / "capability-matrix.md"
    content = matrix_path.read_text(encoding="utf-8")
    assert "v1.27" in content
    assert "LAUNCH_LANDING" in content
    assert "LAUNCH_TOS" in content
    assert "LAUNCH_SUPPORT" in content
    assert "LAUNCH_MONITORING" in content
