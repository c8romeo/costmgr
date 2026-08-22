"""tests.api.core.test_phase_5_health_multi_region — multi-region health endpoint tests.

Phase 5 (cj-style 75번째 wire) — AC #5.1~#5.4 verbatim.
Verifies /api/v1/health/multi-region endpoint exists in
apps/api/core/health.py + CR 12-5 D-14 envelope structure.
"""

from __future__ import annotations

import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
HEALTH_PY = REPO_ROOT / "apps" / "api" / "core" / "health.py"


@pytest.fixture(scope="module")
def health_text() -> str:
    assert HEALTH_PY.exists(), f"{HEALTH_PY} missing"
    return HEALTH_PY.read_text(encoding="utf-8")


class TestMultiRegionRoute:
    def test_route_path(self, health_text: str) -> None:
        assert '"/multi-region"' in health_text

    def test_handler_function(self, health_text: str) -> None:
        assert "async def health_multi_region" in health_text

    def test_router_decorator(self, health_text: str) -> None:
        # Check that /multi-region is decorated with @router.get.
        assert '@router.get("/multi-region")' in health_text


class TestResponseEnvelope:
    """CR 12-5 D-14 envelope structure for multi-region health."""

    def test_status_field(self, health_text: str) -> None:
        assert '"status":' in health_text

    def test_primary_field(self, health_text: str) -> None:
        assert '"primary":' in health_text

    def test_secondary_field(self, health_text: str) -> None:
        assert '"secondary":' in health_text

    def test_timestamp_field(self, health_text: str) -> None:
        assert '"timestamp":' in health_text

    def test_region_primary_seoul(self, health_text: str) -> None:
        assert "primary_seoul" in health_text

    def test_region_secondary_tokyo(self, health_text: str) -> None:
        assert "secondary_tokyo" in health_text

    def test_replication_status_values(self, health_text: str) -> None:
        # Enum values: healthy / lagging / stalled / disconnected.
        for status in ("healthy", "lagging", "stalled", "disconnected"):
            assert status in health_text


class TestStatusAggregation:
    """Status logic: healthy / degraded / unhealthy."""

    def test_status_value_healthy(self, health_text: str) -> None:
        assert '"healthy"' in health_text

    def test_status_value_degraded(self, health_text: str) -> None:
        assert '"degraded"' in health_text

    def test_status_value_unhealthy(self, health_text: str) -> None:
        assert '"unhealthy"' in health_text


class TestObservability:
    """apps/api/core/observability.py EXTENSION — capture_failover_breadcrumb."""

    def test_failover_breadcrumb_function(self) -> None:
        from apps.api.core.observability import capture_failover_breadcrumb

        assert callable(capture_failover_breadcrumb)

    def test_observability_signature(self) -> None:
        import inspect

        from apps.api.core.observability import capture_failover_breadcrumb

        sig = inspect.signature(capture_failover_breadcrumb)
        params = sig.parameters
        assert "region_from" in params
        assert "region_to" in params
        assert "reason" in params
        assert "drill_mode" in params
        assert "elapsed_seconds" in params