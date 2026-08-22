"""tests.integration.test_capability_matrix_v1_26_drift — capability v1.26 drift detector.

Epic 15 (cj-style 60번째 epic 연속 정직 회복 wire) — AC #7.7.
Verifies `apps/api/core/capability.py` enum stays in lockstep with
`docs/capability-matrix.md` v1.26 — 5 NEW rows introduced:
  - MAGIC_LINK
  - SOCIAL_OAUTH_GOOGLE
  - SOCIAL_OAUTH_NAVER
  - SOCIAL_OAUTH_KAKAO
  - SSO_ENTERPRISE
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


EXPECTED_V126_NEW_ENUMS = (
    "MAGIC_LINK",
    "SOCIAL_OAUTH_GOOGLE",
    "SOCIAL_OAUTH_NAVER",
    "SOCIAL_OAUTH_KAKAO",
    "SSO_ENTERPRISE",
)


class TestCapabilityMatrixVersion:
    def test_matrix_at_v1_26(self, capability_matrix_version: str) -> None:
        assert capability_matrix_version == "1.26"


class TestV126NewEnums:
    @pytest.mark.parametrize("enum_name", EXPECTED_V126_NEW_ENUMS)
    def test_enum_in_capability_py(
        self, capability_py_content: str, enum_name: str
    ) -> None:
        pattern = rf"^\s*{enum_name}\s*=\s*\""
        assert re.search(
            pattern, capability_py_content, flags=re.MULTILINE
        ), f"{enum_name} not declared in capability.py"

    @pytest.mark.parametrize("enum_name", EXPECTED_V126_NEW_ENUMS)
    def test_enum_in_capability_matrix(
        self, capability_matrix_content: str, enum_name: str
    ) -> None:
        assert (
            enum_name in capability_matrix_content
        ), f"{enum_name} not declared in capability-matrix.md"

    def test_5_new_enums_total(self, capability_py_content: str) -> None:
        # Count the `MAGIC_LINK` / `SOCIAL_OAUTH_*` / `SSO_ENTERPRISE` enum declarations.
        all_5 = (
            capability_py_content.count("MAGIC_LINK =")
            + capability_py_content.count("SOCIAL_OAUTH_GOOGLE =")
            + capability_py_content.count("SOCIAL_OAUTH_NAVER =")
            + capability_py_content.count("SOCIAL_OAUTH_KAKAO =")
            + capability_py_content.count("SSO_ENTERPRISE =")
        )
        assert all_5 >= 5, f"Expected 5 NEW enums, found {all_5}"


class TestV126IndustryGrants:
    """All 4 industries (manufacturing + service + mfg+service + mfg+service+other)
    must have the 5 new capabilities (industry-agnostic, CR 12-1 L4)."""

    @pytest.fixture
    def industry_grants(self, capability_py_content: str) -> dict[str, int]:
        industries = (
            "MANUFACTURING",
            "SERVICE",
            "MANUFACTURING_SERVICE",
            "MANUFACTURING_SERVICE_OTHER",
        )
        return {
            ind: capability_py_content.count(f"Industry.{ind}:")
            for ind in industries
        }

    def test_all_4_industries_have_5_new(
        self, capability_py_content: str
    ) -> None:
        # Each industry has Capability.MAGIC_LINK + 4 social/SSO entries.
        for enum_name in EXPECTED_V126_NEW_ENUMS:
            count = capability_py_content.count(f"Capability.{enum_name},")
            assert count == 4, (
                f"Capability.{enum_name} granted to {count} industries, "
                f"expected 4 (CR 12-1 L4 precedent — industry-agnostic)"
            )


class TestAuditActionAuthClass:
    """The AUTH ActionClass must be declared + registered in audit_action.py."""

    @pytest.fixture
    def audit_action_content(self) -> str:
        path = REPO_ROOT / "apps" / "api" / "core" / "audit_action.py"
        assert path.exists()
        return path.read_text(encoding="utf-8")

    def test_auth_class_declared(self, audit_action_content: str) -> None:
        assert "AUTH = " in audit_action_content
        assert '"auth"' in audit_action_content

    def test_auth_actions_registered(self, audit_action_content: str) -> None:
        for action in ("magic_link_sent", "social_oauth_initiated", "sso_identity_linked"):
            assert action in audit_action_content, f"{action} not in audit registry"
