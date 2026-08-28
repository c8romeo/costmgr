"""tests.api.modules.finops.test_phase_25_vendor_management_router — Phase 25 router drift.

Phase 25 wire — FinOps Vendor Management territory.
Layer 2 P1 carry-over (cj-style 189번째): pytest test backfill for vendor
management router endpoints, mirroring the Phase 17~20 router drift pattern.

Phase 25 extra=forbid tightening (cj-style 190th): all 7 Pydantic request
BaseModels now declare `ConfigDict(extra="forbid")` (verbatim mirror of
Phase 21 reserved_capacity_routes posture). Test 6 is flipped from the prior
honest-default pin to the tightened post-change pin so the drift detector
reflects the new contract.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

import pytest
from fastapi import APIRouter
from pydantic import ValidationError

from apps.api.modules.finops.vendor_management.serializers import (
    AUTO_RENEWAL_WINDOW_DAYS,
    MAX_CONTRACT_OVERRIDE_KRW,
    MAX_CONTRACTS_PER_VENDOR,
    MAX_VENDORS_PER_TENANT,
    TOTAL_VERIFICATION_TOLERANCE_KRW,
    VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION,
    VENDOR_RISK_HIGH_THRESHOLD,
    VENDOR_RISK_LOW_THRESHOLD,
    VENDOR_RISK_MEDIUM_THRESHOLD,
)
from apps.api.modules.finops.vendor_management.vendor_management_routes import (
    AdvanceContractRequest,
    BlacklistVendorRequest,
    CreateContractRequest,
    CreateVendorRequest,
    DryRunRequest,
    UpdateVendorRequest,
    VendorSelectionRequest,
)
from apps.api.modules.finops.vendor_management.vendor_management_routes import (
    router as vendor_management_router,
)

ROUTER_PREFIX = "/api/finops/vendor-management"
ROUTER_TAGS = ["finops-vendor-management"]
EXPECTED_ROUTE_COUNT = 7
EXPECTED_ROUTE_PATHS = frozenset(
    {
        "/api/finops/vendor-management/vendors",
        "/api/finops/vendor-management/vendors/{vendor_id}",
        "/api/finops/vendor-management/vendors/{vendor_id}/blacklist",
        "/api/finops/vendor-management/selection",
        "/api/finops/vendor-management/contracts",
        "/api/finops/vendor-management/contracts/{contract_id}/advance",
        "/api/finops/vendor-management/dry-run",
    }
)
EXPECTED_REQUEST_MODELS = (
    CreateVendorRequest,
    UpdateVendorRequest,
    BlacklistVendorRequest,
    VendorSelectionRequest,
    CreateContractRequest,
    AdvanceContractRequest,
    DryRunRequest,
)
VENDORS_PATH = "/api/finops/vendor-management/vendors"
VENDOR_DETAIL_PATH = "/api/finops/vendor-management/vendors/{vendor_id}"
VALID_VENDOR_PAYLOAD = {
    "vendor_name": "Acme Cloud",
    "vendor_category": "cloud_infrastructure",
    "cost_score": 80.0,
    "performance_score": 75.0,
    "reliability_score": 90.0,
    "compliance_score": 85.0,
    "strategic_fit_score": 70.0,
}


def test_vendor_management_router_is_api_router_instance() -> None:
    """Test 1 — Router is a FastAPI APIRouter instance (not None)."""
    assert vendor_management_router is not None
    assert isinstance(vendor_management_router, APIRouter)


def test_vendor_management_router_prefix_and_tags() -> None:
    """Test 2 — Router prefix matches expected + tags match expected."""
    assert vendor_management_router.prefix == ROUTER_PREFIX
    assert list(vendor_management_router.tags) == ROUTER_TAGS


def test_vendor_management_router_has_seven_distinct_paths() -> None:
    """Test 3 — Router exposes exactly 7 distinct paths (9 operations) per Phase 25."""
    route_paths = {
        getattr(route, "path", "") for route in vendor_management_router.routes
    }
    assert len(route_paths) == EXPECTED_ROUTE_COUNT


def test_vendor_management_router_routes_match_expected_paths() -> None:
    """Test 4 — Router's route set exactly matches the 7 expected paths."""
    route_paths = {
        getattr(route, "path", "") for route in vendor_management_router.routes
    }
    assert route_paths == EXPECTED_ROUTE_PATHS


def test_vendor_management_vendors_collection_and_detail_methods() -> None:
    """Test 5 — /vendors is POST+GET; /vendors/{vendor_id} is GET+PATCH."""
    collection_methods: set[str] = set()
    detail_methods: set[str] = set()
    for route in vendor_management_router.routes:
        path = getattr(route, "path", "")
        if path == VENDORS_PATH:
            collection_methods |= set(getattr(route, "methods", set()))
        elif path == VENDOR_DETAIL_PATH:
            detail_methods |= set(getattr(route, "methods", set()))
    assert {"POST", "GET"} <= collection_methods
    assert {"GET", "PATCH"} <= detail_methods


def test_vendor_management_request_models_use_extra_forbid() -> None:
    """Test 6 — Request models declare ConfigDict(extra="forbid") (Phase 25 tightening).

    Phase 25 extra=forbid 조이기 source sprint (cj-style 190th) tightened all 7
    request BaseModels to reject extra fields. Mirrors Phase 21 reserved_capacity
    posture (CR 12-5 D-14 typed exception envelope posture + AD-22 owner-only RBAC
    request-surface hardening + NFR4 PII minimization PRESERVED).
    """
    for model_cls in EXPECTED_REQUEST_MODELS:
        assert model_cls.model_config.get("extra") == "forbid"


def test_vendor_management_create_vendor_request_enforces_score_bounds() -> None:
    """Test 7 — CreateVendorRequest rejects out-of-range scores (0.0~100.0)."""
    valid = CreateVendorRequest(**VALID_VENDOR_PAYLOAD)
    assert valid.contract_count == 0

    with pytest.raises(ValidationError):
        CreateVendorRequest(**{**VALID_VENDOR_PAYLOAD, "cost_score": 100.1})

    with pytest.raises(ValidationError):
        CreateVendorRequest(**{**VALID_VENDOR_PAYLOAD, "performance_score": -1.0})


def test_vendor_management_request_models_reject_extra_fields() -> None:
    """Test 7b — All 7 request models reject unknown fields (extra=forbid contract).

    Phase 25 extra=forbid 조이기 source sprint (cj-style 190th) — exercises the
    tightened contract via ValidationError on rogue key for every request model.
    Mirrors Phase 21 reserved_capacity posture verbatim.
    """
    for model_cls in EXPECTED_REQUEST_MODELS:
        with pytest.raises(ValidationError):
            model_cls(**{"__rogue_extra_field__": "should_be_rejected"})


def test_vendor_management_serializer_thresholds_are_stable() -> None:
    """Test 8 — Risk bands + tenant caps + renewal window preserved (Phase 25 invariant)."""
    assert VENDOR_MANAGEMENT_ENGINE_MODEL_VERSION == "1.0.0"
    assert VENDOR_RISK_LOW_THRESHOLD == 30.0
    assert VENDOR_RISK_MEDIUM_THRESHOLD == 60.0
    assert VENDOR_RISK_HIGH_THRESHOLD == 80.0
    assert (
        VENDOR_RISK_LOW_THRESHOLD
        < VENDOR_RISK_MEDIUM_THRESHOLD
        < VENDOR_RISK_HIGH_THRESHOLD
    )
    assert MAX_VENDORS_PER_TENANT == 5000
    assert MAX_CONTRACTS_PER_VENDOR == 100
    assert MAX_CONTRACT_OVERRIDE_KRW == 10_000_000.0
    assert TOTAL_VERIFICATION_TOLERANCE_KRW == 0.01
    assert AUTO_RENEWAL_WINDOW_DAYS == 90
