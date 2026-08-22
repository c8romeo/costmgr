"""tests/api/core/test_phase_4_railway_config.py — railway.toml schema validation.

Phase 4 (cj-style 55번째 epic 연속 정직 회복 wire) — AC #7.2.
TOML schema verification of root `railway.toml` deployment config.
"""

from __future__ import annotations

import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
RAILWAY_TOML = REPO_ROOT / "railway.toml"


@pytest.fixture(scope="module")
def railway_config() -> dict:
    assert RAILWAY_TOML.exists(), f"railway.toml not found at {RAILWAY_TOML}"
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]
    with RAILWAY_TOML.open("rb") as f:
        return tomllib.load(f)


class TestRailwayTomlSchema:
    """railway.toml MUST satisfy the Railway deployment config schema."""

    def test_railway_toml_exists(self) -> None:
        assert RAILWAY_TOML.is_file()

    def test_railway_toml_parses_as_valid_toml(self, railway_config: dict) -> None:
        assert isinstance(railway_config, dict)
        assert len(railway_config) > 0


class TestRailwayBuild:
    """[build] section MUST use DOCKERFILE + apps/api/Dockerfile."""

    def test_build_section_present(self, railway_config: dict) -> None:
        assert "build" in railway_config

    def test_build_builder_is_dockerfile(self, railway_config: dict) -> None:
        assert railway_config["build"].get("builder") == "DOCKERFILE"

    def test_dockerfile_path_targets_api(self, railway_config: dict) -> None:
        path = railway_config["build"].get("dockerfilePath", "")
        assert path == "apps/api/Dockerfile"


class TestRailwayDeploy:
    """[deploy] section MUST configure health check + restart policy."""

    def test_deploy_section_present(self, railway_config: dict) -> None:
        assert "deploy" in railway_config

    def test_healthcheck_path_targets_api_v1_health(
        self, railway_config: dict
    ) -> None:
        path = railway_config["deploy"].get("healthcheckPath", "")
        assert path == "/api/v1/health"

    def test_healthcheck_timeout_is_reasonable(self, railway_config: dict) -> None:
        timeout = railway_config["deploy"].get("healthcheckTimeout")
        assert timeout is not None
        assert 30 <= timeout <= 600

    def test_restart_policy_is_on_failure(self, railway_config: dict) -> None:
        assert (
            railway_config["deploy"].get("restartPolicyType")
            == "ON_FAILURE"
        )

    def test_restart_max_retries_is_set(self, railway_config: dict) -> None:
        retries = railway_config["deploy"].get("restartPolicyMaxRetries")
        assert retries is not None
        assert retries >= 1


class TestRailwayEnv:
    """[env] section MUST map required Supabase + Sentry vars."""

    def test_env_section_present(self, railway_config: dict) -> None:
        assert "env" in railway_config

    def test_database_url_configured(self, railway_config: dict) -> None:
        assert "DATABASE_URL" in railway_config["env"]

    def test_supabase_jwt_secret_configured(self, railway_config: dict) -> None:
        assert "SUPABASE_JWT_SECRET" in railway_config["env"]

    def test_sentry_dsn_configured(self, railway_config: dict) -> None:
        assert "SENTRY_DSN" in railway_config["env"]

    def test_environment_set_to_production(self, railway_config: dict) -> None:
        env_value = railway_config["env"].get("ENVIRONMENT", "")
        assert env_value == "production"
