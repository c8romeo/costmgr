"""tests/api/core/test_phase_4_dockerfile_parity.py — per-app Dockerfile validation.

Phase 4 (cj-style 55번째 epic 연속 정직 회복 wire) — AC #7.3.
Multi-stage build + AD-14 digest pin + CMD entrypoint verification
for both `apps/web/Dockerfile` + `apps/api/Dockerfile`.
"""

from __future__ import annotations

import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
WEB_DOCKERFILE = REPO_ROOT / "apps" / "web" / "Dockerfile"
API_DOCKERFILE = REPO_ROOT / "apps" / "api" / "Dockerfile"
ROOT_DOCKERFILE = REPO_ROOT / "Dockerfile"


@pytest.fixture(scope="module")
def web_dockerfile_content() -> str:
    assert WEB_DOCKERFILE.exists(), "apps/web/Dockerfile missing"
    return WEB_DOCKERFILE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def api_dockerfile_content() -> str:
    assert API_DOCKERFILE.exists(), "apps/api/Dockerfile missing"
    return API_DOCKERFILE.read_text(encoding="utf-8")


class TestWebDockerfile:
    """apps/web/Dockerfile MUST be a valid Next.js standalone container."""

    def test_web_dockerfile_exists(self) -> None:
        assert WEB_DOCKERFILE.is_file()

    def test_web_dockerfile_uses_node_base(
        self, web_dockerfile_content: str
    ) -> None:
        from_lines = [
            line for line in web_dockerfile_content.splitlines()
            if line.startswith("FROM ")
        ]
        assert any("node:" in line for line in from_lines)

    def test_web_dockerfile_uses_digest_pin(
        self, web_dockerfile_content: str
    ) -> None:
        from_lines = [
            line for line in web_dockerfile_content.splitlines()
            if line.startswith("FROM ")
        ]
        # AD-14 verbatim: every base image MUST be pinned by @sha256: digest.
        for line in from_lines:
            assert "@sha256:" in line, (
                f"Base image not digest-pinned: {line}"
            )

    def test_web_dockerfile_is_multi_stage(
        self, web_dockerfile_content: str
    ) -> None:
        # Multi-stage: count AS <stage> markers.
        as_count = sum(
            1
            for line in web_dockerfile_content.splitlines()
            if re.match(r"^FROM\s+\S+\s+AS\s+", line)
        )
        assert as_count >= 2, f"Multi-stage build expected, got {as_count}"

    def test_web_dockerfile_has_healthcheck(
        self, web_dockerfile_content: str
    ) -> None:
        assert "HEALTHCHECK" in web_dockerfile_content

    def test_web_dockerfile_has_cmd(
        self, web_dockerfile_content: str
    ) -> None:
        assert "CMD" in web_dockerfile_content


class TestApiDockerfile:
    """apps/api/Dockerfile MUST be a valid FastAPI uvicorn container."""

    def test_api_dockerfile_exists(self) -> None:
        assert API_DOCKERFILE.is_file()

    def test_api_dockerfile_uses_python_base(
        self, api_dockerfile_content: str
    ) -> None:
        from_lines = [
            line for line in api_dockerfile_content.splitlines()
            if line.startswith("FROM ")
        ]
        assert any("python:" in line for line in from_lines)

    def test_api_dockerfile_uses_digest_pin(
        self, api_dockerfile_content: str
    ) -> None:
        from_lines = [
            line for line in api_dockerfile_content.splitlines()
            if line.startswith("FROM ")
        ]
        # AD-14 verbatim: every base image MUST be pinned by @sha256: digest.
        for line in from_lines:
            assert "@sha256:" in line, (
                f"Base image not digest-pinned: {line}"
            )

    def test_api_dockerfile_is_multi_stage(
        self, api_dockerfile_content: str
    ) -> None:
        as_count = sum(
            1
            for line in api_dockerfile_content.splitlines()
            if re.match(r"^FROM\s+\S+\s+AS\s+", line)
        )
        assert as_count >= 2, f"Multi-stage build expected, got {as_count}"

    def test_api_dockerfile_runs_uvicorn(
        self, api_dockerfile_content: str
    ) -> None:
        assert "uvicorn" in api_dockerfile_content

    def test_api_dockerfile_has_healthcheck(
        self, api_dockerfile_content: str
    ) -> None:
        assert "HEALTHCHECK" in api_dockerfile_content


class TestRootDockerfilePreserved:
    """Root Dockerfile MUST be preserved verbatim (development/CI baseline)."""

    def test_root_dockerfile_still_exists(self) -> None:
        assert ROOT_DOCKERFILE.is_file()

    def test_root_dockerfile_is_multi_stage(self) -> None:
        content = ROOT_DOCKERFILE.read_text(encoding="utf-8")
        as_count = sum(
            1
            for line in content.splitlines()
            if re.match(r"^FROM\s+\S+\s+AS\s+", line)
        )
        # Root baseline = 4-stage (frontend-builder + backend-builder +
        # backend-runtime + frontend-runtime).
        assert as_count >= 4, f"Root Dockerfile expected ≥4 stages, got {as_count}"
