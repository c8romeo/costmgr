"""tests.api.modules.finops.test_phase_17_sustainability_router — Phase 17 router drift.

Phase 20.5 wire (cj-style 147번째) — Layer 1 P0 critical router include.
Layer 2 P1 (Phase 20.5 §F37.2 T2.2 — Carrying-over to cj-style 188): pytest
test backfill for sustainability router endpoints.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

from fastapi import APIRouter

from apps.api.modules.finops.sustainability.sustainability_routes import (
    GenerateSustainabilityReportRequest,
    ScheduleSustainabilityDispatchRequest,
)
from apps.api.modules.finops.sustainability.sustainability_routes import (
    router as sustainability_router,
)

ROUTER_PREFIX = "/api/v1/admin/finops/sustainability"
ROUTER_TAGS = ["finops-sustainability"]
EXPECTED_ROUTE_COUNT = 8
EXPECTED_ROUTE_PATHS = frozenset(
    {
        "/api/v1/admin/finops/sustainability/health",
        "/api/v1/admin/finops/sustainability/rollup",
        "/api/v1/admin/finops/sustainability/kpis",
        "/api/v1/admin/finops/sustainability/reports",
        "/api/v1/admin/finops/sustainability/dispatches",
        "/api/v1/admin/finops/sustainability/dispatches/deliver",
        "/api/v1/admin/finops/sustainability/carbon-trend",
        "/api/v1/admin/finops/sustainability/dry-run",
    }
)


def test_sustainability_router_is_api_router_instance() -> None:
    """Test 1 — Router is a FastAPI APIRouter instance (not None)."""
    assert sustainability_router is not None
    assert isinstance(sustainability_router, APIRouter)


def test_sustainability_router_prefix_and_tags() -> None:
    """Test 2 — Router prefix matches expected + tags match expected."""
    assert sustainability_router.prefix == ROUTER_PREFIX
    assert list(sustainability_router.tags) == ROUTER_TAGS


def test_sustainability_router_has_eight_routes() -> None:
    """Test 3 — Router has exactly 8 routes per Phase 17/20.5 spec."""
    route_paths = {
        getattr(route, "path", "") for route in sustainability_router.routes
    }
    assert len(route_paths) == EXPECTED_ROUTE_COUNT


def test_sustainability_router_routes_match_expected_paths() -> None:
    """Test 4 — Router's route set exactly matches the 8 expected paths (with prefix)."""
    route_paths = {
        getattr(route, "path", "") for route in sustainability_router.routes
    }
    assert route_paths == EXPECTED_ROUTE_PATHS


def test_sustainability_router_routes_include_dry_run_post() -> None:
    """Test 5 — Router contains /dry-run POST endpoint (CRITICAL preview flag pattern)."""
    dry_run_routes = [
        route
        for route in sustainability_router.routes
        if getattr(route, "path", "").endswith("/dry-run")
    ]
    assert len(dry_run_routes) == 1


def test_sustainability_request_models_have_extra_forbid() -> None:
    """Test 6 — Request models ConfigDict extra=forbid (CR 12-5 D-14)."""
    assert GenerateSustainabilityReportRequest.model_config["extra"] == "forbid"
    assert (
        ScheduleSustainabilityDispatchRequest.model_config["extra"] == "forbid"
    )


def test_sustainability_request_model_default_export_format_pdf() -> None:
    """Test 7 — GenerateSustainabilityReportRequest default export_format = pdf."""
    body = GenerateSustainabilityReportRequest()
    assert body.export_format == "pdf"
    assert body.framework == "CSRD"
    assert body.cadence == "monthly"


def test_sustainability_request_model_default_dispatch_schedule_monthly() -> None:
    """Test 8 — ScheduleSustainabilityDispatchRequest default schedule = monthly."""
    body = ScheduleSustainabilityDispatchRequest()
    assert body.dispatch_schedule == "monthly"
    assert body.recipient_strategy == "owner_only"
