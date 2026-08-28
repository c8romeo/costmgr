"""tests.api.modules.finops.test_phase_21_reserved_capacity_router — Phase 21 router drift.

Phase 21 wire (cj-style 151번째) — FinOps Reserved Capacity Planning territory.
Layer 2 P1 carry-over (cj-style 189번째): pytest test backfill for reserved
capacity router endpoints, mirroring the Phase 17~20 router drift pattern.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

from fastapi import APIRouter

from apps.api.modules.finops.reserved_capacity.reserved_capacity_routes import (
    CapacityPlanRequest,
    CommitmentRecommendationRequest,
    DemandForecastRequest,
    OrchestrateRequest,
    ScheduleDispatchRequest,
)
from apps.api.modules.finops.reserved_capacity.reserved_capacity_routes import (
    router as reserved_capacity_router,
)
from apps.api.modules.finops.reserved_capacity.serializers import (
    CAPACITY_HEADROOM_MAX_PCT,
    CAPACITY_HEADROOM_MIN_PCT,
    MINIMUM_BREAK_EVEN_UTILIZATION_PCT,
    MINIMUM_SAVINGS_KRW,
    MINIMUM_SAVINGS_PCT,
    RESERVED_CAPACITY_ENGINE_MODEL_VERSION,
)

ROUTER_PREFIX = "/api/v1/admin/finops/reserved-capacity"
ROUTER_TAGS = ["finops-reserved-capacity"]
EXPECTED_ROUTE_COUNT = 8
EXPECTED_ROUTE_PATHS = frozenset(
    {
        "/api/v1/admin/finops/reserved-capacity/health",
        "/api/v1/admin/finops/reserved-capacity/demand-forecast",
        "/api/v1/admin/finops/reserved-capacity/capacity-plan",
        "/api/v1/admin/finops/reserved-capacity/commitment-recommendation",
        "/api/v1/admin/finops/reserved-capacity/orchestrate",
        "/api/v1/admin/finops/reserved-capacity/dispatches",
        "/api/v1/admin/finops/reserved-capacity/cadence-preview",
        "/api/v1/admin/finops/reserved-capacity/dry-run",
    }
)
EXPECTED_REQUEST_MODELS = (
    DemandForecastRequest,
    CapacityPlanRequest,
    CommitmentRecommendationRequest,
    OrchestrateRequest,
    ScheduleDispatchRequest,
)


def test_reserved_capacity_router_is_api_router_instance() -> None:
    """Test 1 — Router is a FastAPI APIRouter instance (not None)."""
    assert reserved_capacity_router is not None
    assert isinstance(reserved_capacity_router, APIRouter)


def test_reserved_capacity_router_prefix_and_tags() -> None:
    """Test 2 — Router prefix matches expected + tags match expected."""
    assert reserved_capacity_router.prefix == ROUTER_PREFIX
    assert list(reserved_capacity_router.tags) == ROUTER_TAGS


def test_reserved_capacity_router_has_eight_routes() -> None:
    """Test 3 — Router has exactly 8 distinct route paths per Phase 21 spec."""
    route_paths = {
        getattr(route, "path", "") for route in reserved_capacity_router.routes
    }
    assert len(route_paths) == EXPECTED_ROUTE_COUNT


def test_reserved_capacity_router_routes_match_expected_paths() -> None:
    """Test 4 — Router's route set exactly matches the 8 expected paths."""
    route_paths = {
        getattr(route, "path", "") for route in reserved_capacity_router.routes
    }
    assert route_paths == EXPECTED_ROUTE_PATHS


def test_reserved_capacity_router_routes_include_dry_run_post() -> None:
    """Test 5 — Router contains /dry-run POST endpoint (preview flag pattern)."""
    dry_run_routes = [
        route
        for route in reserved_capacity_router.routes
        if getattr(route, "path", "").endswith("/dry-run")
    ]
    assert len(dry_run_routes) == 1
    assert "POST" in set(getattr(dry_run_routes[0], "methods", set()))


def test_reserved_capacity_request_models_have_extra_forbid() -> None:
    """Test 6 — All 5 request models set ConfigDict extra=forbid (CR 12-5 D-14)."""
    for model_cls in EXPECTED_REQUEST_MODELS:
        assert model_cls.model_config["extra"] == "forbid"


def test_reserved_capacity_demand_forecast_request_defaults() -> None:
    """Test 7 — DemandForecastRequest defaults match 5-module cross-join semantics."""
    body = DemandForecastRequest()
    assert body.industry == "manufacturing"
    assert body.confidence_pct == 80.0
    assert body.dry_run is False
    assert body.previous_demand_krw is None


def test_reserved_capacity_serializer_thresholds_are_stable() -> None:
    """Test 8 — Serializer economics thresholds preserved (Phase 21 invariant)."""
    assert RESERVED_CAPACITY_ENGINE_MODEL_VERSION == "1.0.0"
    assert MINIMUM_SAVINGS_PCT == 5.0
    assert MINIMUM_SAVINGS_KRW == 1_000_000.0
    assert MINIMUM_BREAK_EVEN_UTILIZATION_PCT == 70.0
    assert CAPACITY_HEADROOM_MIN_PCT < CAPACITY_HEADROOM_MAX_PCT
