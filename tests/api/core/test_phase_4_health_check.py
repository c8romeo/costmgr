"""tests/api/core/test_phase_4_health_check.py — health endpoint validation.

Phase 4 (cj-style 55번째 epic 연속 정직 회복 wire) — AC #7.4.
FastAPI /api/v1/health endpoint envelope + liveness/readiness separation.
"""

from __future__ import annotations

import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
HEALTH_PY = (
    REPO_ROOT
    / "apps"
    / "api"
    / "core"
    / "health.py"
)


@pytest.fixture(scope="module")
def health_module_content() -> str:
    assert HEALTH_PY.exists(), "apps/api/core/health.py missing"
    return HEALTH_PY.read_text(encoding="utf-8")


class TestHealthModuleExists:
    """apps/api/core/health.py MUST exist (Phase 4 T5 wire)."""

    def test_health_py_exists(self) -> None:
        assert HEALTH_PY.is_file()


class TestHealthRouterShape:
    """health router MUST expose /api/v1/health + liveness/readiness."""

    def test_router_prefix_is_api_v1_health(
        self, health_module_content: str
    ) -> None:
        assert 'prefix="/api/v1/health"' in health_module_content

    def test_health_endpoint_defined(
        self, health_module_content: str
    ) -> None:
        assert '@router.get(""' in health_module_content

    def test_liveness_endpoint_defined(
        self, health_module_content: str
    ) -> None:
        assert '@router.get("/live")' in health_module_content

    def test_readiness_endpoint_defined(
        self, health_module_content: str
    ) -> None:
        assert '@router.get("/ready")' in health_module_content


class TestHealthEnvelope:
    """Health response MUST follow CR 12-5 D-14 envelope shape."""

    def test_status_field_present(self, health_module_content: str) -> None:
        assert '"status"' in health_module_content

    def test_timestamp_field_present(self, health_module_content: str) -> None:
        assert '"timestamp"' in health_module_content

    def test_version_field_present(self, health_module_content: str) -> None:
        assert '"version"' in health_module_content

    def test_database_field_present(self, health_module_content: str) -> None:
        assert '"database"' in health_module_content

    def test_redis_field_present(self, health_module_content: str) -> None:
        assert '"redis"' in health_module_content

    def test_uptime_seconds_field_present(
        self, health_module_content: str
    ) -> None:
        assert '"uptime_seconds"' in health_module_content


class TestHealthDatabaseCheck:
    """Database connectivity check MUST use `SELECT 1` (non-blocking)."""

    def test_select_1_used(self, health_module_content: str) -> None:
        assert "SELECT 1" in health_module_content

    def test_uses_sqlalchemy_text(self, health_module_content: str) -> None:
        assert "from sqlalchemy import text" in health_module_content


class TestHealthJwtCheck:
    """JWT verification check MUST probe Supabase auth endpoint."""

    def test_jwt_verification_function_present(
        self, health_module_content: str
    ) -> None:
        assert "_check_jwt_verification" in health_module_content

    def test_supabase_auth_health_endpoint_used(
        self, health_module_content: str
    ) -> None:
        assert "/auth/v1/health" in health_module_content


class TestHealthMainWiring:
    """apps/api/main.py MUST include the health router."""

    def test_main_py_imports_health_router(self) -> None:
        main_py = REPO_ROOT / "apps" / "api" / "main.py"
        content = main_py.read_text(encoding="utf-8")
        assert "from apps.api.core.health import router as health_router" in content
        assert "app.include_router(health_router)" in content
