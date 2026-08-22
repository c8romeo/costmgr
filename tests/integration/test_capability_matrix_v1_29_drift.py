"""tests.integration.test_capability_matrix_v1_29_drift — capability v1.29 drift detector.

Phase 5 (cj-style 75번째 epic 연속 정직 회복 wire) — AC #6.3.
Verifies `apps/api/core/capability.py` enum stays in lockstep with
`docs/capability-matrix.md` v1.29 — 2 NEW rows introduced:
  - MULTI_REGION_BACKUP
  - MULTI_REGION_FAILOVER
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


EXPECTED_V129_NEW_ENUMS = (
    "MULTI_REGION_BACKUP",
    "MULTI_REGION_FAILOVER",
)


class TestCapabilityMatrixVersion:
    def test_matrix_at_v1_29(self, capability_matrix_version: str) -> None:
        assert capability_matrix_version == "1.29"


class TestV129NewEnums:
    @pytest.mark.parametrize("enum_name", EXPECTED_V129_NEW_ENUMS)
    def test_enum_in_capability_py(
        self, capability_py_content: str, enum_name: str
    ) -> None:
        pattern = rf"^\s*{enum_name}\s*=\s*\""
        assert re.search(
            pattern, capability_py_content, flags=re.MULTILINE
        ), f"{enum_name} not declared in capability.py"

    @pytest.mark.parametrize("enum_name", EXPECTED_V129_NEW_ENUMS)
    def test_enum_in_capability_matrix(
        self, capability_matrix_content: str, enum_name: str
    ) -> None:
        assert (
            enum_name in capability_matrix_content
        ), f"{enum_name} not declared in capability-matrix.md"

    def test_2_new_enums_total(self, capability_py_content: str) -> None:
        # MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER are the 2 NEW
        # enums in v1.29.
        for enum_name in EXPECTED_V129_NEW_ENUMS:
            assert capability_py_content.count(f"{enum_name} =") >= 1, (
                f"{enum_name} not declared in capability.py"
            )


class TestV129IndustryGrants:
    """Phase 5 — MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER are
    industry-agnostic (CR 12-1 L4).

    All 4 industries must have both capabilities. The Capability enum
    and _INDUSTRY_CAPABILITIES map must agree (4 occurrences each:
    4 industry grants × 2 capabilities = 8 references total).
    """

    @pytest.mark.parametrize("enum_name", EXPECTED_V129_NEW_ENUMS)
    def test_4_industry_grants(
        self, capability_py_content: str, enum_name: str
    ) -> None:
        grant_count = capability_py_content.count(f"Capability.{enum_name}")
        assert grant_count == 4, (
            f"Expected 4 industry grants for {enum_name}, "
            f"found {grant_count}. {enum_name} must be industry-agnostic "
            "per CR 12-1 L4."
        )


class TestV129CapabilityGateDep:
    """Phase 5 — T6 (AC #6.3) — the dep module exposes named gates."""

    def test_capability_module_imports(self) -> None:
        from apps.api.dependencies import capability

        assert hasattr(capability, "require_tenant_idp_management")