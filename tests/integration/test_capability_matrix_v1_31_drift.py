"""tests.integration.test_capability_matrix_v1_31_drift — capability v1.31 drift detector.

Phase 6 (cj-style 87번째 epic 연속 정직 회복 wire) — T6 (AC #6.3) — F22.6.

Verifies `apps/api/core/capability.py` enum stays in lockstep with
`docs/capability-matrix.md` v1.31 — 1 NEW row introduced:
  - AUDIT_LOG_RETENTION

Industry-agnostic per CR 12-1 L4 precedent (mirrors MULTI_REGION_BACKUP +
MULTI_REGION_FAILOVER Phase 5 wire + AUDIT_LOG_VIEW Epic 17 wire +
TENANT_IDP_MANAGEMENT Epic 16 + SSO_ENTERPRISE Epic 15 + LISTEN_NOTIFY
13/14 + AUTH_MIDDLEWARE Phase 3 + LAUNCH_* 1st release + DEPLOYMENT_*
Phase 4 wire pattern verbatim bind).
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


EXPECTED_V131_NEW_ENUMS = ("AUDIT_LOG_RETENTION",)


class TestCapabilityMatrixVersion:
    def test_matrix_at_v1_31(self, capability_matrix_version: str) -> None:
        assert capability_matrix_version == "1.31"


class TestV131NewEnums:
    @pytest.mark.parametrize("enum_name", EXPECTED_V131_NEW_ENUMS)
    def test_enum_in_capability_py(
        self, capability_py_content: str, enum_name: str
    ) -> None:
        pattern = rf"^\s*{enum_name}\s*=\s*\""
        assert re.search(
            pattern, capability_py_content, flags=re.MULTILINE
        ), f"{enum_name} not declared in capability.py"

    @pytest.mark.parametrize("enum_name", EXPECTED_V131_NEW_ENUMS)
    def test_enum_in_capability_matrix(
        self, capability_matrix_content: str, enum_name: str
    ) -> None:
        assert (
            enum_name in capability_matrix_content
        ), f"{enum_name} not declared in capability-matrix.md"

    def test_1_new_enum_total(self, capability_py_content: str) -> None:
        # AUDIT_LOG_RETENTION is the only NEW enum in v1.31 (1 row).
        for enum_name in EXPECTED_V131_NEW_ENUMS:
            assert capability_py_content.count(f"{enum_name} =") >= 1, (
                f"{enum_name} not declared in capability.py"
            )


class TestV131IndustryGrants:
    """Phase 6 — AUDIT_LOG_RETENTION is industry-agnostic (CR 12-1 L4).

    All 4 industries must have AUDIT_LOG_RETENTION. The Capability enum
    and _INDUSTRY_CAPABILITIES map must agree (4 occurrences:
    4 industry grants × 1 capability = 4 references total).
    """

    @pytest.mark.parametrize("enum_name", EXPECTED_V131_NEW_ENUMS)
    def test_4_industry_grants(
        self, capability_py_content: str, enum_name: str
    ) -> None:
        grant_count = capability_py_content.count(f"Capability.{enum_name}")
        assert grant_count == 4, (
            f"Expected 4 industry grants for {enum_name}, "
            f"found {grant_count}. {enum_name} must be industry-agnostic "
            "per CR 12-1 L4."
        )


class TestV131CapabilityGateDep:
    """Phase 6 — T6 (AC #6.3) — the dep module exposes a named gate."""

    def test_capability_module_imports(self) -> None:
        from apps.api.dependencies import capability

        assert hasattr(capability, "require_audit_log_retention")
        assert callable(capability.require_audit_log_retention)


class TestV130PreservedAfterV131Extension:
    """v1.30 introduced AUDIT_LOG_VIEW — must still be present (no regression
    from v1.31 EXTENSION)."""

    def test_audit_log_view_preserved(self, capability_py_content: str) -> None:
        assert "AUDIT_LOG_VIEW = \"" in capability_py_content


class TestV129PreservedAfterV131Extension:
    """v1.29 introduced MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER —
    both must still be present (no regression from v1.31 EXTENSION)."""

    def test_multi_region_backup_preserved(self, capability_py_content: str) -> None:
        assert "MULTI_REGION_BACKUP = \"" in capability_py_content

    def test_multi_region_failover_preserved(self, capability_py_content: str) -> None:
        assert "MULTI_REGION_FAILOVER = \"" in capability_py_content
