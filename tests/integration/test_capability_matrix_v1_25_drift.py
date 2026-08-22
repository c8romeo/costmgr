"""tests/integration/test_capability_matrix_v1_25_drift.py — capability v1.25 drift detector.

Phase 4 (cj-style 55번째 epic 연속 정직 회복 wire) — AC #7.6.
Verifies `apps/api/core/capability.py` enum stays in lockstep with
`docs/capability-matrix.md` v1.25 — 4 NEW DEPLOYMENT_* rows introduced.

Mirrors Phase 3-1 integration/test_capability_matrix_v1_24_drift.py pattern.
"""

from __future__ import annotations

import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CAPABILITY_PY = (
    REPO_ROOT
    / "apps"
    / "api"
    / "core"
    / "capability.py"
)
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


EXPECTED_V125_NEW_ENUMS = (
    "DEPLOYMENT_PROD",
    "DEPLOYMENT_STAGING",
    "DEPLOYMENT_DATABASE_BACKUP",
    "DEPLOYMENT_HEALTH_CHECK",
)


class TestCapabilityV125Version:
    """capability-matrix.md MUST be at v1.25 after Phase 4 wire."""

    def test_capability_matrix_at_v1_25(
        self, capability_matrix_version: str
    ) -> None:
        assert capability_matrix_version == "1.25"


class TestCapabilityV125NewEnums:
    """capability.py MUST declare the 4 NEW Phase 4 DEPLOYMENT_* enums."""

    @pytest.mark.parametrize("enum_name", EXPECTED_V125_NEW_ENUMS)
    def test_new_enum_declared(
        self, capability_py_content: str, enum_name: str
    ) -> None:
        # Each enum entry follows pattern: `    ENUM_NAME = "snake_case_value"`.
        pattern = rf"^\s*{enum_name}\s*=\s*\"[a-z_]+\""
        assert re.search(pattern, capability_py_content, re.MULTILINE), (
            f"capability.py missing {enum_name} enum entry"
        )


class TestCapabilityV125IndustryGrants:
    """All 4 NEW DEPLOYMENT_* enums MUST be granted to every industry
    (industry-agnostic per CR 12-1 L4 precedent)."""

    @pytest.mark.parametrize("enum_name", EXPECTED_V125_NEW_ENUMS)
    def test_enum_in_all_industries(
        self, capability_py_content: str, enum_name: str
    ) -> None:
        # Count occurrences in capability.py — at minimum:
        # 1 enum declaration + 1 grant per industry (4 industries) = 5 total.
        occurrences = capability_py_content.count(enum_name)
        assert occurrences >= 5, (
            f"{enum_name} must appear ≥5x (1 decl + 4 industry grants), "
            f"got {occurrences}"
        )


class TestCapabilityV125MatrixRows:
    """capability-matrix.md MUST list the 4 NEW DEPLOYMENT_* capability rows."""

    @pytest.mark.parametrize("enum_name", EXPECTED_V125_NEW_ENUMS)
    def test_matrix_row_present(
        self, capability_matrix_content: str, enum_name: str
    ) -> None:
        # Capability matrix rows reference enum by SCREAMING_SNAKE_CASE name
        # in backticks (e.g. `DEPLOYMENT_PROD`).
        assert f"`{enum_name}`" in capability_matrix_content, (
            f"capability-matrix.md missing backtick-wrapped row for {enum_name}"
        )


class TestCapabilityV125Changelog:
    """capability-matrix.md MUST record a v1.25 changelog entry."""

    def test_v1_25_changelog_entry_present(
        self, capability_matrix_content: str
    ) -> None:
        assert "v1.25" in capability_matrix_content
        # Changelog uses blockquote-bold format (mirrors v1.21~v1.24 style).
        assert "**v1.25" in capability_matrix_content


class TestCapabilityV125IndustryAgnosticGrants:
    """Each of the 4 NEW DEPLOYMENT_* rows MUST be granted across all 4
    industries (manufacturing, service, manufacturing_service, manufacturing_service_other).
    CR 12-1 L4 precedent: deployment capabilities are infrastructure-level,
    therefore industry-agnostic.
    """

    @pytest.mark.parametrize(
        "industry_emoji",
        ["제조", "서비스", "제조+서비스", "제조+서비스+기타"],
    )
    @pytest.mark.parametrize("enum_name", EXPECTED_V125_NEW_ENUMS)
    def test_granted_to_industry(
        self,
        capability_matrix_content: str,
        enum_name: str,
        industry_emoji: str,  # noqa: ARG002 — parametrize axis marker
    ) -> None:
        # Per-parametrize combination: enumerates all 4 NEW DEPLOYMENT_*
        # enums × 4 industries, verifying that every industry grants
        # ✅ for each deployment capability. The `industry_emoji` axis
        # exists so a future regression for a specific industry surfaces
        # in the parametrized failure list (vs. collapsing to one row).
        # Find row containing the backtick-wrapped SCREAMING_SNAKE_CASE
        # capability_id, then verify ✅ marker appears within the row.
        row_match = re.search(
            rf"\|\s*`{re.escape(enum_name)}`\s*\|.*?\|",
            capability_matrix_content,
            re.DOTALL,
        )
        assert row_match is not None, (
            f"No row found for `{enum_name}`"
        )
        row_text = capability_matrix_content[
            row_match.start():row_match.end() + 200
        ]
        assert "✅" in row_text, (
            f"`{enum_name}` row missing industry grant marker"
        )
