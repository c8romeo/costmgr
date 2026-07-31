"""apps.api.core.tenant_context — per-request tenant context (AD-3, AD-10).

Story 0.2 — Task 4.1 ~ 4.4.

- `TenantContext` dataclass: tenant_id, role, user_id (pure value object).
- FastAPI deps: `get_tenant_context(request) -> TenantContext`,
  `current_tenant_id() -> UUID`.
- SQLAlchemy event listener issues `SET LOCAL app.current_tenant_id = '<uuid>'`
  per transaction so RLS policies see the tenant even if JWT context is lost.

Per AD-3: tenant_id ALWAYS comes from JWT, never from request body/query string.
"""

from __future__ import annotations

import contextlib
import uuid
from dataclasses import dataclass

from fastapi import Depends, Request
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine

from apps.api.core.security import JWTClaims, decode_jwt


@dataclass(frozen=True)
class TenantContext:
    """Per-request tenant context — pure value object."""

    tenant_id: uuid.UUID
    role: str
    user_id: uuid.UUID


def _extract_bearer_token(request: Request) -> str | None:
    """Pull `Bearer <token>` from the Authorization header."""
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if not auth_header:
        return None
    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None


async def get_tenant_context(request: Request) -> TenantContext:
    """FastAPI dependency — decode JWT from Authorization header, return TenantContext.

    Stores claims on `request.state.tenant` AND `request.state.tenant_id`
    (per AC #3 spec) for downstream handlers.
    Publishes the tenant_id to the SQLAlchemy listener via
    `set_tenant_local(engine, ...)` so the next transaction's
    `SET LOCAL app.current_tenant_id` is wired correctly.
    Raises `TENANT_FORBIDDEN` (401) on invalid/expired token.

    F-12: yields a context and clears the engine ContextVar on request end
    so pooled execution contexts don't carry tenant A's tenant_id into
    tenant B's transaction.
    """
    token = _extract_bearer_token(request)
    claims: JWTClaims = decode_jwt(token)  # raises AuthError on failure

    ctx = TenantContext(
        tenant_id=claims.tenant_id,
        role=claims.role,
        user_id=claims.user_id,
    )
    request.state.tenant = ctx
    request.state.tenant_id = ctx.tenant_id
    request.state.tenant_claims = claims

    # Publish tenant to the SQLAlchemy begin-event listener so the next
    # transaction issues `SET LOCAL app.current_tenant_id`. The engine
    # may be unset in unit-test environments without a DB.
    engine = None
    try:
        from apps.api.core.db import get_engine

        engine = get_engine()
        set_tenant_local(engine, ctx.tenant_id)
    except RuntimeError:
        # No engine configured (e.g. service_role unit tests, README
        # quickstart). Skip — the listener simply won't fire.
        pass

    try:
        yield ctx
    finally:
        # F-12: clear tenant_id from the ContextVar so pooled execution
        # contexts don't carry the previous tenant into the next request.
        if engine is not None:
            with contextlib.suppress(Exception):  # pragma: no cover — best-effort cleanup
                clear_tenant_local(engine)


async def current_tenant_id(
    ctx: TenantContext = Depends(get_tenant_context),
) -> uuid.UUID:
    """FastAPI dependency — return only the tenant UUID for endpoint handlers."""
    return ctx.tenant_id


# ── RLS hot-path: SET LOCAL app.current_tenant_id ────────────
# This ensures RLS policies that read `current_setting('app.current_tenant_id', true)`
# fall back to the session-level tenant even when the JWT context is lost
# (e.g. service_role bypass).
#
# NOTE (Story 1.1, 2026-07-29): the original `@event.listens_for(AsyncEngine, "connect")`
# decorator was a no-op stub but raised `AssertionError: issubclass(target, Pool)`
# at import time under SQLAlchemy 2.0.36 (the `_accept_with` for "connect" expects a
# Pool subclass, not the AsyncEngine class). The actual sync-engine hookup lives
# in `attach_tenant_listener()` below — registered once at app startup.
# Removed: the dead decorator (function body was a single `return`).
# Tracked as a Story 0.2 follow-up if the early-connect hook is ever needed.


def attach_tenant_listener(engine: AsyncEngine) -> None:
    """Wire a SQLAlchemy event listener that issues
    `SET LOCAL app.current_tenant_id = :tid` for each new transaction.

    The tenant_id is read from a ContextVar set by the FastAPI dependency.
    Falls back to a no-op if the var is unset (service_role path).
    """
    from contextvars import ContextVar

    _current_tenant_var: ContextVar[str | None] = ContextVar(
        "current_tenant_id_local", default=None
    )

    def set_tenant(tenant_id: uuid.UUID) -> None:
        _current_tenant_var.set(str(tenant_id))

    def clear_tenant() -> None:
        _current_tenant_var.set(None)

    @event.listens_for(engine.sync_engine, "begin")
    def _begin_transaction(dbapi_connection, transaction):  # noqa: ARG001
        tid = _current_tenant_var.get()
        if tid:
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("SET LOCAL app.current_tenant_id = %s", (tid,))
            finally:
                cursor.close()

    # Expose context-var helpers on the engine for the FastAPI dep
    engine._costmgr_set_tenant = set_tenant  # type: ignore[attr-defined]
    engine._costmgr_clear_tenant = clear_tenant  # type: ignore[attr-defined]


def set_tenant_local(engine: AsyncEngine, tenant_id: uuid.UUID) -> None:
    """Called by the FastAPI dependency to publish the tenant for the next txn."""
    set_tenant_fn = getattr(engine, "_costmgr_set_tenant", None)
    if set_tenant_fn is not None:
        set_tenant_fn(tenant_id)


def clear_tenant_local(engine: AsyncEngine) -> None:
    """Clear the tenant context after the request scope ends."""
    clear_tenant_fn = getattr(engine, "_costmgr_clear_tenant", None)
    if clear_tenant_fn is not None:
        clear_tenant_fn()
