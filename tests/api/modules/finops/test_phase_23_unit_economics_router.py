"""tests.api.modules.finops.test_phase_23_unit_economics_router — Phase 23 router drift.

Phase 23 wire (cj-style 164번째) — FinOps Unit Economics territory.
Layer 2 P1 carry-over (cj-style 189번째): pytest test backfill for unit
economics router endpoints, mirroring the Phase 17~20 router drift pattern.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

from fastapi import APIRouter

from apps.api.modules.finops.unit_economics.serializers import (
    MARGIN_CRITICAL_THRESHOLD_PCT,
    MARGIN_HEALTHY_THRESHOLD_PCT,
    MARGIN_NEGATIVE_PCT,
    MARGIN_WARNING_THRESHOLD_PCT,
    MAX_BUSINESS_UNITS_PER_TENANT,
    MAX_COST_PER_X_OVERRIDE_KRW,
    MAX_TRANSACTIONS_PER_PERIOD,
    UNIT_ECONOMICS_ENGINE_MODEL_VERSION,
)
from apps.api.modules.finops.unit_economics.unit_economics_routes import (
    router as unit_economics_router,
)

ROUTER_PREFIX = "/api/v1/finops/unit-economics"
ROUTER_TAGS = ["finops", "unit_economics"]
EXPECTED_ROUTE_COUNT = 9
EXPECTED_ROUTE_PATHS = frozenset(
    {
        "/api/v1/finops/unit-economics/healthcheck",
        "/api/v1/finops/unit-economics/compute",
        "/api/v1/finops/unit-economics/cost-per-business-unit",
        "/api/v1/finops/unit-economics/cost-per-transaction",
        "/api/v1/finops/unit-economics/margin-analysis",
        "/api/v1/finops/unit-economics/dry-run",
        "/api/v1/finops/unit-economics/trend",
        "/api/v1/finops/unit-economics/calculation",
        "/api/v1/finops/unit-economics/cadence-preview",
    }
)
EXPECTED_GET_PATHS = frozenset(
    {
        "/api/v1/finops/unit-economics/healthcheck",
        "/api/v1/finops/unit-economics/trend",
        "/api/v1/finops/unit-economics/cadence-preview",
    }
)


def test_unit_economics_router_is_api_router_instance() -> None:
    """Test 1 — Router is a FastAPI APIRouter instance (not None)."""
    assert unit_economics_router is not None
    assert isinstance(unit_economics_router, APIRouter)


def test_unit_economics_router_prefix_and_tags() -> None:
    """Test 2 — Router prefix matches expected + tags match expected."""
    assert unit_economics_router.prefix == ROUTER_PREFIX
    assert list(unit_economics_router.tags) == ROUTER_TAGS


def test_unit_economics_router_has_nine_routes() -> None:
    """Test 3 — Router has exactly 9 distinct route paths per Phase 23 spec."""
    route_paths = {
        getattr(route, "path", "") for route in unit_economics_router.routes
    }
    assert len(route_paths) == EXPECTED_ROUTE_COUNT


def test_unit_economics_router_routes_match_expected_paths() -> None:
    """Test 4 — Router's route set exactly matches the 9 expected paths."""
    route_paths = {
        getattr(route, "path", "") for route in unit_economics_router.routes
    }
    assert route_paths == EXPECTED_ROUTE_PATHS


def test_unit_economics_router_read_endpoints_are_get() -> None:
    """Test 5 — healthcheck/trend/cadence-preview are read-only GET endpoints."""
    for route in unit_economics_router.routes:
        if getattr(route, "path", "") in EXPECTED_GET_PATHS:
            assert set(getattr(route, "methods", set())) == {"GET"}


def test_unit_economics_router_routes_include_dry_run_post() -> None:
    """Test 6 — Router contains /dry-run POST endpoint (preview flag pattern)."""
    dry_run_routes = [
        route
        for route in unit_economics_router.routes
        if getattr(route, "path", "").endswith("/dry-run")
    ]
    assert len(dry_run_routes) == 1
    assert "POST" in set(getattr(dry_run_routes[0], "methods", set()))


def test_unit_economics_margin_thresholds_are_ordered() -> None:
    """Test 7 — Margin band thresholds preserve healthy > warning > negative order."""
    assert MARGIN_HEALTHY_THRESHOLD_PCT == 30.0
    assert MARGIN_WARNING_THRESHOLD_PCT == 15.0
    assert MARGIN_CRITICAL_THRESHOLD_PCT == 15.0
    assert MARGIN_NEGATIVE_PCT == 0.0
    assert MARGIN_HEALTHY_THRESHOLD_PCT > MARGIN_WARNING_THRESHOLD_PCT
    assert MARGIN_WARNING_THRESHOLD_PCT > MARGIN_NEGATIVE_PCT


def test_unit_economics_serializer_caps_are_stable() -> None:
    """Test 8 — Tenant scale caps + 2FA override ceiling preserved (Phase 23 invariant)."""
    assert UNIT_ECONOMICS_ENGINE_MODEL_VERSION == "1.0.0"
    assert MAX_BUSINESS_UNITS_PER_TENANT == 1000
    assert MAX_TRANSACTIONS_PER_PERIOD == 100_000
    assert MAX_COST_PER_X_OVERRIDE_KRW == 10_000_000.0
