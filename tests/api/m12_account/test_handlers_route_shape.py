"""tests.api.m12_account.test_handlers_route_shape — Story 12.4 route shape tests.

8+1 routes wire (per AC #9 spec):
- POST /api/v1/account/2fa/setup
- POST /api/v1/account/2fa/verify
- POST /api/v1/account/2fa/challenge
- POST /api/v1/account/2fa/recovery
- POST /api/v1/account/2fa/disable
- GET  /api/v1/account/2fa/status
- POST /api/v1/account/2fa/challenge-tokens
- POST /api/v1/account/2fa/challenge-tokens/consume
- GET  /api/v1/m2-entry-gate

Tests verify the FastAPI router shape (paths, methods, response_model,
status_code) — full integration tests against the route handlers
require a live DB + JWT and live in the service test directory
(`test_two_factor_service.py`, Story 12.1).
"""

from __future__ import annotations

from apps.api.modules.m12_account.handlers import router


def _routes_by_path() -> dict[str, list]:
    """Group router routes by path for lookup convenience."""
    out: dict[str, list] = {}
    for r in router.routes:
        if hasattr(r, "path") and hasattr(r, "methods"):
            out.setdefault(r.path, []).append(r)
    return out


def test_router_has_9_routes() -> None:
    """Story 12.4 wire — 8 account routes + 1 M2 entry gate."""
    routes = _routes_by_path()
    expected_paths = {
        "/api/v1/account/2fa/setup",
        "/api/v1/account/2fa/verify",
        "/api/v1/account/2fa/challenge",
        "/api/v1/account/2fa/recovery",
        "/api/v1/account/2fa/disable",
        "/api/v1/account/2fa/status",
        "/api/v1/account/2fa/challenge-tokens",
        "/api/v1/account/2fa/challenge-tokens/consume",
        "/api/v1/m2-entry-gate",
    }
    actual_paths = set(routes.keys())
    assert expected_paths <= actual_paths, (
        f"missing routes: {expected_paths - actual_paths}"
    )


def test_setup_route_is_post_201() -> None:
    routes = _routes_by_path()["/api/v1/account/2fa/setup"]
    assert "POST" in routes[0].methods
    assert routes[0].status_code == 201
    assert routes[0].response_model is not None


def test_verify_route_is_post_200() -> None:
    routes = _routes_by_path()["/api/v1/account/2fa/verify"]
    assert "POST" in routes[0].methods
    assert routes[0].status_code == 200


def test_challenge_route_is_post_200() -> None:
    routes = _routes_by_path()["/api/v1/account/2fa/challenge"]
    assert "POST" in routes[0].methods
    assert routes[0].status_code == 200


def test_recovery_route_is_post_200() -> None:
    routes = _routes_by_path()["/api/v1/account/2fa/recovery"]
    assert "POST" in routes[0].methods
    assert routes[0].status_code == 200


def test_disable_route_is_post_200() -> None:
    routes = _routes_by_path()["/api/v1/account/2fa/disable"]
    assert "POST" in routes[0].methods
    assert routes[0].status_code == 200


def test_status_route_is_get_200() -> None:
    routes = _routes_by_path()["/api/v1/account/2fa/status"]
    assert "GET" in routes[0].methods
    assert routes[0].status_code == 200


def test_issue_challenge_token_route_is_post_201() -> None:
    routes = _routes_by_path()["/api/v1/account/2fa/challenge-tokens"]
    assert "POST" in routes[0].methods
    assert routes[0].status_code == 201


def test_consume_challenge_token_route_is_post_200() -> None:
    routes = _routes_by_path()["/api/v1/account/2fa/challenge-tokens/consume"]
    assert "POST" in routes[0].methods
    assert routes[0].status_code == 200


def test_m2_entry_gate_route_is_get_200() -> None:
    routes = _routes_by_path()["/api/v1/m2-entry-gate"]
    assert "GET" in routes[0].methods
    assert routes[0].status_code == 200


def test_router_module_exports_router() -> None:
    """The module's __init__.py must re-export the router for FastAPI."""
    from apps.api.modules.m12_account import router as module_router

    assert module_router is router, (
        "apps.api.modules.m12_account.__init__ must re-export the same router "
        "as apps.api.modules.m12_account.handlers"
    )


def test_router_prefix_is_api_v1() -> None:
    """All M12 routes are under /api/v1 (CR 11-2 SSOT)."""
    assert router.prefix == "/api/v1"
    for r in router.routes:
        if hasattr(r, "path"):
            assert (
                r.path.startswith("/api/v1/account/")
                or r.path.startswith("/api/v1/m2-entry-gate")
            ), (
                f"unexpected route path: {r.path}"
            )
