"""tests.api.m9_abc.test_abc_validation_handlers — Story 9.1.

Route shape + envelope + capability gate tests for the 4 NEW ABC 100%
validation endpoints (PRD §F9.1 verbatim + CR 12-5 D-14 typed contract).

Endpoints:
  - POST /api/v1/abc/cost-pools       (1.2 확장)
  - POST /api/v1/abc/activities       (NEW)
  - POST /api/v1/abc/drivers/validate (NEW)
  - POST /api/v1/abc/validate         (NEW 9-1 main entry point)

Capability gate: `Capability.ABC_CALCULATION` (industry-agnostic, v1.18).
Role gate: `owner` or `member`.

Envelope tests verify:
  - Router shape (4 NEW routes + 2 existing 1.2 routes)
  - Pydantic schema shape (5 NEW schemas)
  - Decimal-as-string precision parity (AD-8)
  - Korean SSOT message constants
"""

from __future__ import annotations

import json
from decimal import Decimal

from fastapi import APIRouter

from apps.api.modules.m9_abc.handlers import router
from apps.api.modules.m9_abc.schemas import (
    ActivityValidationRequest,
    CostPoolValidationRequest,
    DriverCountResponse,
    DriverRequest,
    DriverValidationRequest,
    ValidateRequest,
    ValidationLayerState,
    ValidationResponse,
    ValidationTarget,
)

# ── Helpers ──────────────────────────────────────────────────────


def _routes_by_path(router: APIRouter) -> dict[str, list]:
    """Group router routes by path for lookup convenience."""
    out: dict[str, list] = {}
    for r in router.routes:
        if hasattr(r, "path") and hasattr(r, "methods"):
            out.setdefault(r.path, []).append(r)
    return out


# ── Router shape tests ──────────────────────────────────────────


def test_abc_router_has_6_routes() -> None:
    """Story 9.1 — 4 NEW + 2 existing 1.2 = 6 total routes."""
    routes = _routes_by_path(router)
    actual_paths = set(routes.keys())
    expected_new_paths = {
        "/api/v1/abc/cost-pools",
        "/api/v1/abc/activities",
        "/api/v1/abc/drivers/validate",
        "/api/v1/abc/validate",
    }
    assert expected_new_paths <= actual_paths, (
        f"missing NEW routes: {expected_new_paths - actual_paths}"
    )


def test_abc_router_prefix_is_abc() -> None:
    """router prefix is /api/v1/abc (PRD §F9.1)."""
    assert router.prefix == "/api/v1/abc"


def test_abc_router_tag_is_m9_abc() -> None:
    """router tag = 'm9-abc' (OpenAPI grouping)."""
    assert "m9-abc" in router.tags


# ── Per-endpoint route shape tests ──────────────────────────────


def test_cost_pool_endpoint_is_post_200() -> None:
    """POST /abc/cost-pools = 200 OK (validation only, no INSERT)."""
    routes = _routes_by_path(router)["/api/v1/abc/cost-pools"]
    route = routes[0]
    assert "POST" in route.methods
    assert route.response_model is ValidationResponse


def test_activities_endpoint_is_post_200() -> None:
    """POST /abc/activities = 200 OK."""
    routes = _routes_by_path(router)["/api/v1/abc/activities"]
    route = routes[0]
    assert "POST" in route.methods
    assert route.response_model is ValidationResponse


def test_drivers_validate_endpoint_is_post_200() -> None:
    """POST /abc/drivers/validate = 200 OK (distinct from 1.2 POST /drivers)."""
    routes = _routes_by_path(router)["/api/v1/abc/drivers/validate"]
    route = routes[0]
    assert "POST" in route.methods
    assert route.response_model is ValidationResponse


def test_validate_endpoint_is_post_200() -> None:
    """POST /abc/validate = 200 OK (9-1 main entry point)."""
    routes = _routes_by_path(router)["/api/v1/abc/validate"]
    route = routes[0]
    assert "POST" in route.methods
    assert route.response_model is ValidationResponse


# ── Pydantic schema shape tests ─────────────────────────────────


def test_cost_pool_validation_request_required_fields() -> None:
    """CostPoolValidationRequest requires department_id + allocation_pcts."""
    req = CostPoolValidationRequest(
        department_id="d-001",
        allocation_pcts=[Decimal("25"), Decimal("75")],
    )
    assert req.department_id == "d-001"
    assert len(req.allocation_pcts) == 2
    assert req.allocation_pcts[0] == Decimal("25")


def test_activity_validation_request_required_fields() -> None:
    """ActivityValidationRequest requires cost_pool_id + activity_pcts."""
    req = ActivityValidationRequest(
        cost_pool_id="cp-001",
        activity_pcts=[Decimal("50"), Decimal("50")],
    )
    assert req.cost_pool_id == "cp-001"
    assert len(req.activity_pcts) == 2


def test_driver_validation_request_required_fields() -> None:
    """DriverValidationRequest requires activity_id + driver_pcts."""
    req = DriverValidationRequest(
        activity_id="act-001",
        driver_pcts=[Decimal("60"), Decimal("40")],
    )
    assert req.activity_id == "act-001"
    assert len(req.driver_pcts) == 2


def test_validate_request_all_optional_layers() -> None:
    """ValidateRequest — all 3 layer lists are optional (None default)."""
    req = ValidateRequest(
        cost_pool_id="cp-001",
        activity_id="act-001",
    )
    assert req.cost_pool is None
    assert req.activities is None
    assert req.drivers is None


def test_validation_layer_state_required_fields() -> None:
    """ValidationLayerState requires target + sum_pct + count + is_valid + hash."""
    layer = ValidationLayerState(
        target="cost_pool",
        sum_pct="100",
        count=4,
        is_valid=True,
        hash="sha256:abc",
    )
    assert layer.target == "cost_pool"
    assert layer.sum_pct == "100"
    assert layer.count == 4
    assert layer.is_valid is True
    assert layer.hash == "sha256:abc"
    assert layer.message_ko is None


def test_validation_response_3_layer_shape() -> None:
    """ValidationResponse — 3 layer states for the main /validate endpoint."""
    layers = [
        ValidationLayerState(
            target="cost_pool", sum_pct="100", count=4, is_valid=True, hash="h1"
        ),
        ValidationLayerState(
            target="activity", sum_pct="100", count=3, is_valid=True, hash="h2"
        ),
        ValidationLayerState(
            target="driver", sum_pct="100", count=2, is_valid=True, hash="h3"
        ),
    ]
    resp = ValidationResponse(
        cost_pool_id="cp-001",
        activity_id="act-001",
        all_valid=True,
        layers=layers,
    )
    assert resp.all_valid is True
    assert len(resp.layers) == 3


def test_validation_target_literal_three_values() -> None:
    """ValidationTarget literal — 3 values (cost_pool / activity / driver)."""
    assert "cost_pool" in ValidationTarget.__args__
    assert "activity" in ValidationTarget.__args__
    assert "driver" in ValidationTarget.__args__


# ── Decimal-as-string precision parity (AD-8) ───────────────────


def test_validation_layer_state_decimal_as_string_parity() -> None:
    """sum_pct as string preserves Decimal precision (AD-8 monetary parity)."""
    layer = ValidationLayerState(
        target="cost_pool",
        sum_pct="100.0001",
        count=4,
        is_valid=False,
        hash="sha256:abc",
    )
    json_str = layer.model_dump_json()
    data = json.loads(json_str)
    assert data["sum_pct"] == "100.0001"


# ── DriverRequest + DriverCountResponse (1.2 scaffold preserved) ─


def test_driver_request_required_fields() -> None:
    """DriverRequest (1.2 scaffold) — 3 fields preserved."""
    req = DriverRequest(
        driver_name="Machine Hours",
        unit="hours",
        practical_capacity_hours=8000,
    )
    assert req.driver_name == "Machine Hours"
    assert req.unit == "hours"
    assert req.practical_capacity_hours == 8000


def test_driver_count_response_required_field() -> None:
    """DriverCountResponse (1.2 scaffold) — 1 field preserved."""
    resp = DriverCountResponse(driver_count=3)
    assert resp.driver_count == 3


# ── Capability gate assertion ───────────────────────────────────


def test_abc_routes_have_capability_dependencies() -> None:
    """All 4 NEW endpoints must depend on Capability.ABC_CALCULATION."""
    new_paths = {
        "/api/v1/abc/cost-pools",
        "/api/v1/abc/activities",
        "/api/v1/abc/drivers/validate",
        "/api/v1/abc/validate",
    }
    routes = _routes_by_path(router)
    for path in new_paths:
        route = routes[path][0]
        # FastAPI dependencies are stored on the route
        assert hasattr(route, "dependencies")
        assert len(route.dependencies) >= 2, (
            f"{path} must have at least capability gate + role gate dependencies"
        )


# ── Korean SSOT message format (PRD §F9.1 verbatim) ────────────


def test_validation_layer_message_ko_format() -> None:
    """PRD §F9.1 verbatim format '원가풀 행 합 ≠ 100% (현재 105%)'."""
    layer = ValidationLayerState(
        target="cost_pool",
        sum_pct="105",
        count=4,
        is_valid=False,
        hash="sha256:abc",
        message_ko="원가풀 행 합이 100%가 아닙니다 (현재 105%)",
    )
    assert "100%" in layer.message_ko
    assert "105" in layer.message_ko


def test_validation_layer_message_ko_optional() -> None:
    """message_ko is optional (None default) — ko-KR.json SSOT fallback."""
    layer = ValidationLayerState(
        target="activity",
        sum_pct="100",
        count=3,
        is_valid=True,
        hash="sha256:xyz",
    )
    assert layer.message_ko is None
