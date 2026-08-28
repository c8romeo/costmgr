"""tests.api.modules.finops.test_phase_24_budget_planning_router — Phase 24 router drift.

Phase 24 wire — FinOps Budget Planning territory.
Layer 2 P1 carry-over (cj-style 189번째): pytest test backfill for budget
planning router endpoints, mirroring the Phase 17~20 router drift pattern.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

from fastapi import APIRouter

from apps.api.modules.finops.budget_planning.budget_planning_routes import (
    router as budget_planning_router,
)
from apps.api.modules.finops.budget_planning.serializers import (
    ALL_BUDGET_ALERT_SEVERITIES,
    ALL_BUDGET_PLAN_LIFECYCLES,
    BUDGET_CRITICAL_THRESHOLD_PCT,
    BUDGET_PLANNING_ENGINE_MODEL_VERSION,
    BUDGET_WARNING_THRESHOLD_PCT,
    MAX_ALLOCATIONS_PER_PLAN,
    MAX_BUDGET_OVERRIDE_KRW,
    MAX_BUDGET_PLANS_PER_TENANT,
    TOTAL_VERIFICATION_TOLERANCE_KRW,
)

ROUTER_PREFIX = "/finops/budget-planning"
ROUTER_TAGS = ["finops", "budget-planning"]
EXPECTED_ROUTE_COUNT = 7
EXPECTED_ROUTE_PATHS = frozenset(
    {
        "/finops/budget-planning/plans",
        "/finops/budget-planning/plans/{plan_id}",
        "/finops/budget-planning/plans/{plan_id}/allocate",
        "/finops/budget-planning/plans/{plan_id}/submit-approval",
        "/finops/budget-planning/plans/{plan_id}/approve-step",
        "/finops/budget-planning/plans/{plan_id}/vs-actual",
        "/finops/budget-planning/plans/{plan_id}/alerts/trigger",
    }
)
PLANS_PATH = "/finops/budget-planning/plans"
PLAN_DETAIL_PATH = "/finops/budget-planning/plans/{plan_id}"


def test_budget_planning_router_is_api_router_instance() -> None:
    """Test 1 — Router is a FastAPI APIRouter instance (not None)."""
    assert budget_planning_router is not None
    assert isinstance(budget_planning_router, APIRouter)


def test_budget_planning_router_prefix_and_tags() -> None:
    """Test 2 — Router prefix matches expected + tags match expected."""
    assert budget_planning_router.prefix == ROUTER_PREFIX
    assert list(budget_planning_router.tags) == ROUTER_TAGS


def test_budget_planning_router_has_seven_distinct_paths() -> None:
    """Test 3 — Router exposes exactly 7 distinct paths (9 operations) per Phase 24."""
    route_paths = {
        getattr(route, "path", "") for route in budget_planning_router.routes
    }
    assert len(route_paths) == EXPECTED_ROUTE_COUNT


def test_budget_planning_router_routes_match_expected_paths() -> None:
    """Test 4 — Router's route set exactly matches the 7 expected paths."""
    route_paths = {
        getattr(route, "path", "") for route in budget_planning_router.routes
    }
    assert route_paths == EXPECTED_ROUTE_PATHS


def test_budget_planning_plans_collection_supports_post_and_get() -> None:
    """Test 5 — /plans carries both POST (create) and GET (list)."""
    methods: set[str] = set()
    for route in budget_planning_router.routes:
        if getattr(route, "path", "") == PLANS_PATH:
            methods |= set(getattr(route, "methods", set()))
    assert "POST" in methods
    assert "GET" in methods


def test_budget_planning_plan_detail_supports_get_and_patch() -> None:
    """Test 6 — /plans/{plan_id} carries GET (read) and PATCH (partial update)."""
    methods: set[str] = set()
    for route in budget_planning_router.routes:
        if getattr(route, "path", "") == PLAN_DETAIL_PATH:
            methods |= set(getattr(route, "methods", set()))
    assert "GET" in methods
    assert "PATCH" in methods
    assert "PUT" not in methods


def test_budget_planning_approval_workflow_endpoints_are_post() -> None:
    """Test 7 — Approval workflow + alert endpoints are POST (audit-first, CR 1-1)."""
    post_only_paths = {
        "/finops/budget-planning/plans/{plan_id}/allocate",
        "/finops/budget-planning/plans/{plan_id}/submit-approval",
        "/finops/budget-planning/plans/{plan_id}/approve-step",
        "/finops/budget-planning/plans/{plan_id}/vs-actual",
        "/finops/budget-planning/plans/{plan_id}/alerts/trigger",
    }
    for route in budget_planning_router.routes:
        if getattr(route, "path", "") in post_only_paths:
            assert set(getattr(route, "methods", set())) == {"POST"}


def test_budget_planning_serializer_thresholds_are_stable() -> None:
    """Test 8 — Budget band thresholds + tenant caps preserved (Phase 24 invariant)."""
    assert BUDGET_PLANNING_ENGINE_MODEL_VERSION == "1.0.0"
    assert BUDGET_WARNING_THRESHOLD_PCT == 10.0
    assert BUDGET_CRITICAL_THRESHOLD_PCT == 25.0
    assert BUDGET_WARNING_THRESHOLD_PCT < BUDGET_CRITICAL_THRESHOLD_PCT
    assert MAX_BUDGET_PLANS_PER_TENANT == 1000
    assert MAX_ALLOCATIONS_PER_PLAN == 100_000
    assert MAX_BUDGET_OVERRIDE_KRW == 10_000_000.0
    assert TOTAL_VERIFICATION_TOLERANCE_KRW == 0.01
    assert len(ALL_BUDGET_PLAN_LIFECYCLES) > 0
    assert len(ALL_BUDGET_ALERT_SEVERITIES) > 0
