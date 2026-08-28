"""tests.api.modules.finops.test_phase_20_multi_cloud_router — Phase 20 router drift.

Phase 20.5 wire (cj-style 147번째) — Layer 1 P0 critical router include.
Layer 2 P1 (Phase 20.5 §F37.2 T2.5 — Carrying-over to cj-style 188): pytest
test backfill for multi-cloud router endpoints.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter

from apps.api.modules.finops.multi_cloud.cost_reconciliation_aggregator import (
    validate_multi_cloud_cost_reconciliation,
)
from apps.api.modules.finops.multi_cloud.multi_cloud_routes import (
    NegotiationBotRequest,
    ScheduleMultiCloudDispatchRequest,
)
from apps.api.modules.finops.multi_cloud.multi_cloud_routes import (
    router as multi_cloud_router,
)

ROUTER_PREFIX = "/api/v1/admin/finops/multi-cloud"
ROUTER_TAGS = ["finops-multi-cloud"]
EXPECTED_ROUTE_COUNT = 8
EXPECTED_ROUTE_PATHS = frozenset(
    {
        "/api/v1/admin/finops/multi-cloud/health",
        "/api/v1/admin/finops/multi-cloud/rate-card-reconciliations",
        "/api/v1/admin/finops/multi-cloud/cost-reconciliations",
        "/api/v1/admin/finops/multi-cloud/negotiation-bot/trigger",
        "/api/v1/admin/finops/multi-cloud/blended-unblended",
        "/api/v1/admin/finops/multi-cloud/marketplace-saas/integrate",
        "/api/v1/admin/finops/multi-cloud/dispatches",
        "/api/v1/admin/finops/multi-cloud/dry-run",
    }
)


def test_multi_cloud_router_is_api_router_instance() -> None:
    """Test 1 — Router is a FastAPI APIRouter instance (not None)."""
    assert multi_cloud_router is not None
    assert isinstance(multi_cloud_router, APIRouter)


def test_multi_cloud_router_prefix_and_tags() -> None:
    """Test 2 — Router prefix matches expected + tags match expected."""
    assert multi_cloud_router.prefix == ROUTER_PREFIX
    assert list(multi_cloud_router.tags) == ROUTER_TAGS


def test_multi_cloud_router_has_eight_routes() -> None:
    """Test 3 — Router has exactly 8 routes per Phase 20/20.5 spec."""
    route_paths = {
        getattr(route, "path", "") for route in multi_cloud_router.routes
    }
    assert len(route_paths) == EXPECTED_ROUTE_COUNT


def test_multi_cloud_router_routes_match_expected_paths() -> None:
    """Test 4 — Router's route set exactly matches the 8 expected paths (with prefix)."""
    route_paths = {
        getattr(route, "path", "") for route in multi_cloud_router.routes
    }
    assert route_paths == EXPECTED_ROUTE_PATHS


def test_multi_cloud_router_routes_include_dry_run_post() -> None:
    """Test 5 — Router contains /dry-run POST endpoint (CRITICAL preview flag pattern)."""
    dry_run_routes = [
        route
        for route in multi_cloud_router.routes
        if getattr(route, "path", "").endswith("/dry-run")
    ]
    assert len(dry_run_routes) == 1


def test_multi_cloud_request_models_have_extra_forbid() -> None:
    """Test 6 — Request models ConfigDict extra=forbid (CR 12-5 D-14)."""
    assert NegotiationBotRequest.model_config["extra"] == "forbid"
    assert (
        ScheduleMultiCloudDispatchRequest.model_config["extra"] == "forbid"
    )


def test_multi_cloud_negotiation_bot_request_envelope() -> None:
    """Test 7 — NegotiationBotRequest fields match provider flow semantics."""
    body = NegotiationBotRequest()
    assert body.provider == "AWS"
    assert body.min_savings_pct == 5.0
    assert body.min_savings_krw == 1_000_000.0


def test_multi_cloud_validate_reconciliation_raises_on_missing_fields() -> None:
    """Test 8 — validate_multi_cloud_cost_reconciliation raises on missing
    required fields (Phase 20 TypedDict 19 fields strict invariant)."""
    incomplete_reconciliation = {
        "cost_reconciliation_id": str(uuid.uuid4()),
        # Other required fields intentionally missing
    }
    raised = False
    try:
        validate_multi_cloud_cost_reconciliation(incomplete_reconciliation)
    except Exception:
        raised = True
    assert raised
