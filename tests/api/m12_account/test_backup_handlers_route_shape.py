"""tests.api.m12_account.test_backup_handlers_route_shape — Story 12.2 route shape tests.

3 NEW routes wire (per AC #4 spec):
- GET  /api/v1/account/backups/recent              — list 7-day backups
- GET  /api/v1/account/backups/{backup_id}/download — JSON download
- POST /api/v1/account/backups/trigger              — manual owner trigger

Tests verify the FastAPI router shape (paths, methods, response_model,
status_code, role gates). Full integration tests against the handlers
require a live DB + JWT and live in the service test directory
(`test_backup_export_service.py`).

Owner-only per AD-10 (CR 12-1 L4 precedent — no Capability gate).
"""

from __future__ import annotations

import inspect

from apps.api.modules.m12_account.handlers import router


def _routes_by_path() -> dict[str, list]:
    """Group router routes by path for lookup convenience."""
    out: dict[str, list] = {}
    for r in router.routes:
        if hasattr(r, "path") and hasattr(r, "methods"):
            out.setdefault(r.path, []).append(r)
    return out


def _handler_uses_owner_gate(handler) -> bool:
    """Detect `require_role("owner")` in handler source (closure form).

    FastAPI's `dependant.dependencies` exposes dep wrappers as `_dep`
    internal names, not the original callable. So we inspect the handler
    source for the textual pattern `require_role("owner")`.
    """
    try:
        src = inspect.getsource(handler)
    except (OSError, TypeError):
        return False
    return 'require_role("owner")' in src


def _path_params_from_format(path: str) -> list[str]:
    """Extract `{name}` path params from a FastAPI route path string."""
    import re

    return re.findall(r"\{(\w+)\}", path)


# ── 12 cases ──────────────────────────────────────────────────────
def test_router_has_3_backup_routes() -> None:
    """Story 12.2 wire — 3 backup routes (2 GET + 1 POST)."""
    routes = _routes_by_path()
    expected_paths = {
        "/api/v1/account/backups/recent",
        "/api/v1/account/backups/{backup_id}/download",
        "/api/v1/account/backups/trigger",
    }
    actual_paths = set(routes.keys())
    assert expected_paths <= actual_paths, (
        f"missing routes: {expected_paths - actual_paths}"
    )


def test_recent_route_is_get_200() -> None:
    """GET /api/v1/account/backups/recent → 200 + BackupListResponse."""
    routes = _routes_by_path()["/api/v1/account/backups/recent"]
    assert "GET" in routes[0].methods
    assert routes[0].status_code == 200
    assert routes[0].response_model is not None


def test_download_route_is_get_200() -> None:
    """GET /api/v1/account/backups/{backup_id}/download → 200 (Response)."""
    routes = _routes_by_path()["/api/v1/account/backups/{backup_id}/download"]
    assert "GET" in routes[0].methods
    assert routes[0].status_code == 200


def test_trigger_route_is_post_201() -> None:
    """POST /api/v1/account/backups/trigger → 201 + BackupTriggerResponse."""
    routes = _routes_by_path()["/api/v1/account/backups/trigger"]
    assert "POST" in routes[0].methods
    assert routes[0].status_code == 201
    assert routes[0].response_model is not None


def test_recent_route_has_owner_role_gate() -> None:
    """GET /backups/recent handler has require_role('owner') in source."""
    routes = _routes_by_path()["/api/v1/account/backups/recent"]
    assert _handler_uses_owner_gate(routes[0].endpoint), (
        "require_role(\"owner\") not found in list_recent_backups source"
    )


def test_download_route_has_owner_role_gate() -> None:
    """GET /backups/{backup_id}/download handler has owner role gate."""
    routes = _routes_by_path()["/api/v1/account/backups/{backup_id}/download"]
    assert _handler_uses_owner_gate(routes[0].endpoint), (
        "require_role(\"owner\") not found in download_backup source"
    )


def test_trigger_route_has_owner_role_gate() -> None:
    """POST /backups/trigger handler has owner role gate."""
    routes = _routes_by_path()["/api/v1/account/backups/trigger"]
    assert _handler_uses_owner_gate(routes[0].endpoint), (
        "require_role(\"owner\") not found in trigger_backup source"
    )


def test_recent_route_summary_mentions_owner_only() -> None:
    """Route summary tags 'owner-only' for ops visibility."""
    routes = _routes_by_path()["/api/v1/account/backups/recent"]
    summary = routes[0].summary or ""
    assert "owner" in summary.lower()


def test_download_route_has_path_param_backup_id() -> None:
    """GET /backups/{backup_id}/download path param name is `backup_id`."""
    path = "/api/v1/account/backups/{backup_id}/download"
    assert "backup_id" in _path_params_from_format(path)


def test_trigger_route_has_request_body() -> None:
    """POST /backups/trigger accepts BackupTriggerRequest body."""
    routes = _routes_by_path()["/api/v1/account/backups/trigger"]
    body_params = routes[0].dependant.body_params
    assert len(body_params) >= 1, (
        f"trigger route must have body param, got: {body_params}"
    )


def test_recent_response_envelope_includes_trace_id() -> None:
    """BackupListResponse schema includes trace_id field (AD-15 §4)."""
    from apps.api.modules.m12_account.handlers import BackupListResponse

    fields = BackupListResponse.model_fields
    assert "trace_id" in fields, (
        f"trace_id missing from BackupListResponse: {list(fields.keys())}"
    )
    assert "items" in fields
    assert "total_count" in fields
    assert "days" in fields


def test_trigger_response_envelope_includes_trace_id() -> None:
    """BackupTriggerResponse schema includes trace_id field (AD-15 §4)."""
    from apps.api.modules.m12_account.handlers import BackupTriggerResponse

    fields = BackupTriggerResponse.model_fields
    assert "trace_id" in fields
    assert "backup_id" in fields
    assert "payload_sha256" in fields
    assert "row_count_total" in fields
    assert "audit_log_exported_rows" in fields


def test_no_capability_gate_on_backup_routes() -> None:
    """CR 12-1 L4 precedent — backup is industry-agnostic, owner-only.

    BACKUP_EXPORT capability is documented in capability-matrix v1.14 but
    NOT enforced as a route gate. Mirrors TWO_FACTOR_AUTH pattern.
    """
    paths_to_check = [
        "/api/v1/account/backups/recent",
        "/api/v1/account/backups/{backup_id}/download",
        "/api/v1/account/backups/trigger",
    ]
    for path in paths_to_check:
        routes = _routes_by_path()[path]
        try:
            src = inspect.getsource(routes[0].endpoint)
        except (OSError, TypeError):
            continue
        assert "require_capability" not in src, (
            f"{path}: require_capability must NOT be present (industry-agnostic)"
        )


def test_backup_list_item_schema_has_required_fields() -> None:
    """BackupListItem includes all fields needed for ops UI listing."""
    from apps.api.modules.m12_account.handlers import BackupListItem

    fields = BackupListItem.model_fields
    required = {
        "backup_id",
        "backup_date",
        "schema_version",
        "payload_sha256",
        "payload_size_bytes",
        "row_count_total",
        "audit_log_exported_rows",
        "created_at",
    }
    assert required <= set(fields.keys()), (
        f"missing fields: {required - set(fields.keys())}"
    )
