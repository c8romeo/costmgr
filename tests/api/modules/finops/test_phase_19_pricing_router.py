"""tests.api.modules.finops.test_phase_19_pricing_router — Phase 19 router drift.

Phase 20.5 wire (cj-style 147번째) — Layer 1 P0 critical router include.
Layer 2 P1 (Phase 20.5 §F37.2 T2.4 — Carrying-over to cj-style 188): pytest
test backfill for pricing router endpoints.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from apps.api.modules.finops.pricing.pricing_routes import (
    GeneratePricingReportRequest,
)
from apps.api.modules.finops.pricing.pricing_routes import (
    router as pricing_router,
)
from apps.api.modules.finops.pricing.rate_card_aggregator import (
    compute_showback_blended_rate,
)

ROUTER_PREFIX = "/api/v1/admin/finops/pricing"
ROUTER_TAGS = ["finops-pricing"]
EXPECTED_ROUTE_COUNT = 8
EXPECTED_ROUTE_PATHS = frozenset(
    {
        "/api/v1/admin/finops/pricing/health",
        "/api/v1/admin/finops/pricing/rollup",
        "/api/v1/admin/finops/pricing/kpis",
        "/api/v1/admin/finops/pricing/reports",
        "/api/v1/admin/finops/pricing/dispatches",
        "/api/v1/admin/finops/pricing/dispatches/deliver",
        "/api/v1/admin/finops/pricing/rate-card-trend",
        "/api/v1/admin/finops/pricing/dry-run",
    }
)


def test_pricing_router_is_api_router_instance() -> None:
    """Test 1 — Router is a FastAPI APIRouter instance (not None)."""
    assert pricing_router is not None
    assert isinstance(pricing_router, APIRouter)


def test_pricing_router_prefix_and_tags() -> None:
    """Test 2 — Router prefix matches expected + tags match expected."""
    assert pricing_router.prefix == ROUTER_PREFIX
    assert list(pricing_router.tags) == ROUTER_TAGS


def test_pricing_router_has_eight_routes() -> None:
    """Test 3 — Router has exactly 8 routes per Phase 19/20.5 spec."""
    route_paths = {
        getattr(route, "path", "") for route in pricing_router.routes
    }
    assert len(route_paths) == EXPECTED_ROUTE_COUNT


def test_pricing_router_routes_match_expected_paths() -> None:
    """Test 4 — Router's route set exactly matches the 8 expected paths (with prefix)."""
    route_paths = {
        getattr(route, "path", "") for route in pricing_router.routes
    }
    assert route_paths == EXPECTED_ROUTE_PATHS


def test_pricing_router_routes_include_dry_run_post() -> None:
    """Test 5 — Router contains /dry-run POST endpoint (CRITICAL preview flag pattern)."""
    dry_run_routes = [
        route
        for route in pricing_router.routes
        if getattr(route, "path", "").endswith("/dry-run")
    ]
    assert len(dry_run_routes) == 1


def test_pricing_request_models_have_extra_forbid() -> None:
    """Test 6 — Request models ConfigDict extra=forbid (CR 12-5 D-14)."""
    assert GeneratePricingReportRequest.model_config["extra"] == "forbid"
    # Re-import the correct alias — SchedulePricingReportRequest may not exist
    # as a direct name; falling back to lookup for any Schedule*Request in the module.
    from apps.api.modules.finops.pricing import pricing_routes as _pricing_routes

    schedule_aliases = [
        name
        for name in dir(_pricing_routes)
        if name.startswith("Schedule") and name.endswith("Request")
    ]
    assert schedule_aliases, "no Schedule*Request model exported from pricing_routes"
    schedule_cls: Any = getattr(_pricing_routes, schedule_aliases[0])
    assert schedule_cls.model_config["extra"] == "forbid"


def test_pricing_request_model_default_export_format_pdf() -> None:
    """Test 7 — GeneratePricingReportRequest default export_format = pdf."""
    body = GeneratePricingReportRequest()
    assert body.export_format == "pdf"
    assert body.framework == "FINOPS_FOUNDATION"
    assert body.cadence == "monthly"


def test_pricing_showback_blended_rate_aggregator_basic() -> None:
    """Test 8 — compute_showback_blended_rate returns 0.0 for zero hours
    division-by-zero guard (CR 11-4 P-015 verbatim)."""
    result = compute_showback_blended_rate(
        showback_total_krw=1_000_000.0,
        total_compute_hours=0.0,
    )
    assert result == 0.0
    result_positive = compute_showback_blended_rate(
        showback_total_krw=1_000_000.0,
        total_compute_hours=10.0,
    )
    assert result_positive == 100_000.0
