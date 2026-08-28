"""tests.api.modules.finops.test_phase_18_commitment_router — Phase 18 router drift.

Phase 20.5 wire (cj-style 147번째) — Layer 1 P0 critical router include.
Layer 2 P1 (Phase 20.5 §F37.2 T2.3 — Carrying-over to cj-style 188): pytest
test backfill for commitment router endpoints.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

from fastapi import APIRouter

from apps.api.modules.finops.commitment.commitment_routes import (
    GenerateCommitmentReportRequest,
    ScheduleCommitmentDispatchRequest,
)
from apps.api.modules.finops.commitment.commitment_routes import (
    router as commitment_router,
)

ROUTER_PREFIX = "/api/v1/admin/finops/commitment"
ROUTER_TAGS = ["finops-commitment"]
EXPECTED_ROUTE_COUNT = 8
EXPECTED_ROUTE_PATHS = frozenset(
    {
        "/api/v1/admin/finops/commitment/health",
        "/api/v1/admin/finops/commitment/rollup",
        "/api/v1/admin/finops/commitment/kpis",
        "/api/v1/admin/finops/commitment/reports",
        "/api/v1/admin/finops/commitment/dispatches",
        "/api/v1/admin/finops/commitment/dispatches/deliver",
        "/api/v1/admin/finops/commitment/utilization-trend",
        "/api/v1/admin/finops/commitment/dry-run",
    }
)


def test_commitment_router_is_api_router_instance() -> None:
    """Test 1 — Router is a FastAPI APIRouter instance (not None)."""
    assert commitment_router is not None
    assert isinstance(commitment_router, APIRouter)


def test_commitment_router_prefix_and_tags() -> None:
    """Test 2 — Router prefix matches expected + tags match expected."""
    assert commitment_router.prefix == ROUTER_PREFIX
    assert list(commitment_router.tags) == ROUTER_TAGS


def test_commitment_router_has_eight_routes() -> None:
    """Test 3 — Router has exactly 8 routes per Phase 18/20.5 spec."""
    route_paths = {
        getattr(route, "path", "") for route in commitment_router.routes
    }
    assert len(route_paths) == EXPECTED_ROUTE_COUNT


def test_commitment_router_routes_match_expected_paths() -> None:
    """Test 4 — Router's route set exactly matches the 8 expected paths (with prefix)."""
    route_paths = {
        getattr(route, "path", "") for route in commitment_router.routes
    }
    assert route_paths == EXPECTED_ROUTE_PATHS


def test_commitment_router_routes_include_dry_run_post() -> None:
    """Test 5 — Router contains /dry-run POST endpoint (CRITICAL preview flag pattern)."""
    dry_run_routes = [
        route
        for route in commitment_router.routes
        if getattr(route, "path", "").endswith("/dry-run")
    ]
    assert len(dry_run_routes) == 1


def test_commitment_request_models_have_extra_forbid() -> None:
    """Test 6 — Request models ConfigDict extra=forbid (CR 12-5 D-14)."""
    assert GenerateCommitmentReportRequest.model_config["extra"] == "forbid"
    assert (
        ScheduleCommitmentDispatchRequest.model_config["extra"] == "forbid"
    )


def test_commitment_request_model_default_export_format_pdf() -> None:
    """Test 7 — GenerateCommitmentReportRequest default export_format = pdf."""
    body = GenerateCommitmentReportRequest()
    assert body.export_format == "pdf"
    assert body.framework == "FINOPS_FOUNDATION"
    assert body.cadence == "monthly"


def test_commitment_request_model_default_dispatch_schedule_monthly() -> None:
    """Test 8 — ScheduleCommitmentDispatchRequest default schedule = monthly."""
    body = ScheduleCommitmentDispatchRequest()
    assert body.dispatch_schedule == "monthly"
    assert body.recipient_strategy == "owner_only"
