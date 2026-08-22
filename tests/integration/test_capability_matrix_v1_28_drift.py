"""tests.integration.test_capability_matrix_v1_28_drift — capability v1.28 drift detector.

Epic 16 (cj-style 69번째 epic 연속 정직 회복 wire) — AC #7.7.
Verifies `apps/api/core/capability.py` enum stays in lockstep with
`docs/capability-matrix.md` v1.28 — 1 NEW row introduced:
  - TENANT_IDP_MANAGEMENT
"""

from __future__ import annotations

import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CAPABILITY_PY = REPO_ROOT / "apps" / "api" / "core" / "capability.py"
CAPABILITY_MATRIX_MD = REPO_ROOT / "docs" / "capability-matrix.md"


@pytest.fixture(scope="module")
def capability_py_content() -> str:
    assert CAPABILITY_PY.exists(), "apps/api/core/capability.py missing"
    return CAPABILITY_PY.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def capability_matrix_content() -> str:
    assert CAPABILITY_MATRIX_MD.exists(), "docs/capability-matrix.md missing"
    return CAPABILITY_MATRIX_MD.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def capability_matrix_version() -> str:
    content = CAPABILITY_MATRIX_MD.read_text(encoding="utf-8")
    match = re.search(r"v(\d+\.\d+)", content)
    assert match is not None, "capability-matrix.md missing version line"
    return match.group(1)


EXPECTED_V128_NEW_ENUMS = ("TENANT_IDP_MANAGEMENT",)


class TestCapabilityMatrixVersion:
    def test_matrix_at_v1_28(self, capability_matrix_version: str) -> None:
        assert capability_matrix_version == "1.28"


class TestV128NewEnums:
    @pytest.mark.parametrize("enum_name", EXPECTED_V128_NEW_ENUMS)
    def test_enum_in_capability_py(
        self, capability_py_content: str, enum_name: str
    ) -> None:
        pattern = rf"^\s*{enum_name}\s*=\s*\""
        assert re.search(
            pattern, capability_py_content, flags=re.MULTILINE
        ), f"{enum_name} not declared in capability.py"

    @pytest.mark.parametrize("enum_name", EXPECTED_V128_NEW_ENUMS)
    def test_enum_in_capability_matrix(
        self, capability_matrix_content: str, enum_name: str
    ) -> None:
        assert (
            enum_name in capability_matrix_content
        ), f"{enum_name} not declared in capability-matrix.md"

    def test_1_new_enum_total(self, capability_py_content: str) -> None:
        # TENANT_IDP_MANAGEMENT is the only NEW enum in v1.28.
        assert capability_py_content.count("TENANT_IDP_MANAGEMENT =") >= 1


class TestV128IndustryGrants:
    """Epic 16 — TENANT_IDP_MANAGEMENT is industry-agnostic (CR 12-1 L4).

    All 4 industries must have the capability. The Capability enum and
    _INDUSTRY_CAPABILITIES map must agree (4 occurrences: 1 enum decl
    + 4 industry grants).
    """

    def test_4_industry_grants(
        self, capability_py_content: str
    ) -> None:
        # 1 enum decl + 4 industry grants = 5 references total
        grant_count = capability_py_content.count(
            "Capability.TENANT_IDP_MANAGEMENT"
        )
        assert grant_count == 4, (
            f"Expected 4 industry grants, found {grant_count}. "
            "TENANT_IDP_MANAGEMENT must be industry-agnostic per CR 12-1 L4."
        )


class TestV128CapabilityGateDep:
    """Epic 16 — T6 (AC #6.3) — the dep module exposes a named gate."""

    def test_require_tenant_idp_management_exported(self) -> None:
        from apps.api.dependencies.capability import (
            require_tenant_idp_management,
        )

        assert callable(require_tenant_idp_management)

    def test_gate_in_all_list(self) -> None:
        from apps.api.dependencies import capability

        assert "require_tenant_idp_management" in capability.__all__
