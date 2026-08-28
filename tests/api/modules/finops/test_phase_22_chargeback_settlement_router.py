"""tests.api.modules.finops.test_phase_22_chargeback_settlement_router — Phase 22 router drift.

Phase 22 wire (cj-style 160번째) — FinOps Chargeback Settlement territory.
Layer 2 P1 carry-over (cj-style 189번째): pytest test backfill for chargeback
settlement router endpoints, mirroring the Phase 17~20 router drift pattern.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

from fastapi import APIRouter

from apps.api.modules.finops.chargeback_settlement.chargeback_settlement_routes import (
    router as chargeback_settlement_router,
)
from apps.api.modules.finops.chargeback_settlement.serializers import (
    CHARGEBACK_SETTLEMENT_ENGINE_MODEL_VERSION,
    MAX_ALLOCATION_LINES,
    MAX_INVOICE_BYTES,
    RECONCILIATION_AMOUNT_TOLERANCE_KRW,
    RECONCILIATION_MAX_RETRIES,
    RECONCILIATION_TOLERANCE_PCT,
)

ROUTER_PREFIX = "/api/v1/finops/chargeback-settlement"
ROUTER_TAGS = ["finops", "chargeback_settlement"]
EXPECTED_ROUTE_COUNT = 8
EXPECTED_ROUTE_PATHS = frozenset(
    {
        "/api/v1/finops/chargeback-settlement/healthcheck",
        "/api/v1/finops/chargeback-settlement/settlement-rules",
        "/api/v1/finops/chargeback-settlement/settlement-rules/{settlement_id}",
        "/api/v1/finops/chargeback-settlement/allocation",
        "/api/v1/finops/chargeback-settlement/invoice",
        "/api/v1/finops/chargeback-settlement/reconciliation",
        "/api/v1/finops/chargeback-settlement/dispatch",
        "/api/v1/finops/chargeback-settlement/cadence-preview",
    }
)
SETTLEMENT_RULES_PATH = "/api/v1/finops/chargeback-settlement/settlement-rules"


def test_chargeback_settlement_router_is_api_router_instance() -> None:
    """Test 1 — Router is a FastAPI APIRouter instance (not None)."""
    assert chargeback_settlement_router is not None
    assert isinstance(chargeback_settlement_router, APIRouter)


def test_chargeback_settlement_router_prefix_and_tags() -> None:
    """Test 2 — Router prefix matches expected + tags match expected."""
    assert chargeback_settlement_router.prefix == ROUTER_PREFIX
    assert list(chargeback_settlement_router.tags) == ROUTER_TAGS


def test_chargeback_settlement_router_has_eight_distinct_paths() -> None:
    """Test 3 — Router exposes exactly 8 distinct paths per Phase 22 spec."""
    route_paths = {
        getattr(route, "path", "")
        for route in chargeback_settlement_router.routes
    }
    assert len(route_paths) == EXPECTED_ROUTE_COUNT


def test_chargeback_settlement_router_routes_match_expected_paths() -> None:
    """Test 4 — Router's route set exactly matches the 8 expected paths."""
    route_paths = {
        getattr(route, "path", "")
        for route in chargeback_settlement_router.routes
    }
    assert route_paths == EXPECTED_ROUTE_PATHS


def test_chargeback_settlement_settlement_rules_supports_post_and_get() -> None:
    """Test 5 — /settlement-rules carries both POST (create) and GET (list)."""
    methods: set[str] = set()
    for route in chargeback_settlement_router.routes:
        if getattr(route, "path", "") == SETTLEMENT_RULES_PATH:
            methods |= set(getattr(route, "methods", set()))
    assert "POST" in methods
    assert "GET" in methods


def test_chargeback_settlement_settlement_rule_update_is_put() -> None:
    """Test 6 — /settlement-rules/{settlement_id} is a PUT (idempotent update)."""
    update_routes = [
        route
        for route in chargeback_settlement_router.routes
        if getattr(route, "path", "").endswith("/{settlement_id}")
    ]
    assert len(update_routes) == 1
    assert set(getattr(update_routes[0], "methods", set())) == {"PUT"}


def test_chargeback_settlement_invoice_and_reconciliation_are_post() -> None:
    """Test 7 — /invoice and /reconciliation are POST (audit-first INSERT, CR 1-1)."""
    post_only_paths = {
        "/api/v1/finops/chargeback-settlement/invoice",
        "/api/v1/finops/chargeback-settlement/reconciliation",
        "/api/v1/finops/chargeback-settlement/allocation",
    }
    for route in chargeback_settlement_router.routes:
        if getattr(route, "path", "") in post_only_paths:
            assert set(getattr(route, "methods", set())) == {"POST"}


def test_chargeback_settlement_serializer_thresholds_are_stable() -> None:
    """Test 8 — Reconciliation tolerance + invoice caps preserved (Phase 22 invariant)."""
    assert CHARGEBACK_SETTLEMENT_ENGINE_MODEL_VERSION == "1.0.0"
    assert RECONCILIATION_TOLERANCE_PCT == 1.0
    assert RECONCILIATION_MAX_RETRIES == 3
    assert RECONCILIATION_AMOUNT_TOLERANCE_KRW == 0.01
    assert MAX_INVOICE_BYTES == 10 * 1024 * 1024
    assert MAX_ALLOCATION_LINES == 10_000
