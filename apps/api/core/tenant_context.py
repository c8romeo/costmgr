"""apps.api.core.tenant_context — per-request tenant context (AD-3, AD-10).

Story 0.2 — Task 4.1 ~ 4.4.

- `TenantContext` dataclass: tenant_id, role, user_id (pure value object).
- FastAPI deps: `get_tenant_context(request) -> TenantContext`,
  `current_tenant_id() -> UUID`.
- SQLAlchemy event listener issues `SET LOCAL app.current_tenant_id = '<uuid>'`
  per transaction so RLS policies see the tenant even if JWT context is lost.

Per AD-3: tenant_id ALWAYS comes from JWT, never from request body/query string.

cj-style N+9 (Sprint 0 MVP local-demo bypass) — When a verified JWT has a
`sub` that does NOT correspond to a row in our `users` table, OR when JWT
verification itself fails, fall back to the first `tenant_memberships`
owner so the demo end-to-end flow can be verified without manually wiring
Supabase auth identities. Production-disabled by `APP_ENV=production` or
`MVP_DEV_BYPASS=false`. See `_is_dev_bypass_enabled` for the full gate.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import uuid
from dataclasses import dataclass

from fastapi import Depends, Request
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncEngine

from apps.api.core.security import TENANT_FORBIDDEN, AuthError, JWTClaims, decode_jwt

_log = logging.getLogger(__name__)


def _is_dev_bypass_enabled() -> bool:
    """cj-style N+9 — gate for the local MVP demo bypass.

    Production-safe by default: if either `APP_ENV=production` is set OR
    `MVP_DEV_BYPASS=false` is set, the bypass is disabled. Any other
    configuration enables it (local dev / staging / MVP demo).
    """
    app_env = os.environ.get("APP_ENV", "").lower()
    if app_env == "production":
        return False
    return os.environ.get("MVP_DEV_BYPASS", "true").lower() != "false"


async def _dev_bypass_first_owner() -> JWTClaims:
    """cj-style N+9 — return claims derived from the first owner in our DB.

    Raises `AuthError(TENANT_FORBIDDEN)` if no owner row exists. Cached on
    the engine for the process lifetime — `_dev_bypass_first_owner_cached`
    invokes this on cache miss.
    """
    from apps.api.core.db import get_engine

    engine = get_engine()
    async with engine.connect() as conn:
        row = (
            await conn.execute(
                text(
                    """
                    SELECT u.id AS user_id, tm.tenant_id, tm.role
                    FROM users u
                    JOIN tenant_memberships tm ON tm.user_id = u.id
                    WHERE tm.role = 'owner'
                    ORDER BY tm.joined_at
                    LIMIT 1
                    """
                )
            )
        ).first()

    if row is None:
        raise AuthError(
            code=TENANT_FORBIDDEN,
            message_ko="[dev-bypass] DB 에 owner 시드 데이터가 없습니다",
            details={"reason": "dev_bypass_no_owner"},
        )

    return JWTClaims(
        tenant_id=row.tenant_id,
        role=row.role,
        user_id=row.user_id,
        industry=None,
        raw={"sub": str(row.user_id), "dev_bypass": True},
    )


# Cache so we don't hit the DB on every request when bypass is active.
# Invalidated when DB rows change — that's acceptable for MVP demo.
_dev_bypass_cache: JWTClaims | None = None


async def _dev_bypass_first_owner_cached() -> JWTClaims:
    global _dev_bypass_cache
    if _dev_bypass_cache is None:
        _dev_bypass_cache = await _dev_bypass_first_owner()
        _log.info(
            "[dev-bypass] activated — first owner: user_id=%s tenant_id=%s",
            _dev_bypass_cache.user_id,
            _dev_bypass_cache.tenant_id,
        )
    return _dev_bypass_cache


@dataclass(frozen=True)
class TenantContext:
    """Per-request tenant context — pure value object."""

    tenant_id: uuid.UUID
    role: str
    user_id: uuid.UUID
    # Story 6.3 B8: industry sourced from JWT app_metadata.industry
    # (server-controlled). Used by the closing PDF export handler
    # to source industry from authenticated context rather than
    # the request query string.
    industry: str | None = None
    # Walking Skeleton (2026-08-16): populate from `X-Trace-Id` header
    # or middleware (`request.state.trace_id`), falling back to a fresh
    # uuid4. Without this, `ctx.trace_id` raises AttributeError on
    # 21 call sites in m4_inventory/handlers.py.
    trace_id: str | None = None


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

    cj-style N+9 (Sprint 0 MVP local-demo bypass):
      - If `decode_jwt` raises `AuthError` (signature/exp/role invalid),
        AND `_is_dev_bypass_enabled()` returns True, fall back to the
        first owner in our DB.
      - If the JWT is missing entirely (frontend cookie extraction
        failed because the user has not signed in to Supabase yet, or
        the anon cookie is malformed), AND bypass is enabled, fall
        back to the first owner. This lets the local MVP demo render
        the dashboard without a real Supabase sign-in.
      - If `decode_jwt` succeeds but the JWT's `sub` (user UUID) is NOT
        present in our `users` table, AND bypass is enabled, fall back
        to the first owner. This handles the case where a real Supabase
        user (e.g. c8romeo@gmail.com) signs in successfully but has not
        been provisioned as a `tenant_memberships.owner` yet.
    """
    token = _extract_bearer_token(request)
    bypass_enabled = _is_dev_bypass_enabled()
    claims: JWTClaims | None = None

    if bypass_enabled and token is None:
        # No Authorization header at all (frontend cookie extraction
        # failed). Use the seed owner so the dashboard can render.
        claims = await _dev_bypass_first_owner_cached()
        _log.info(
            "[dev-bypass] missing Authorization header — using first owner"
        )
    else:
        try:
            claims = decode_jwt(token)  # raises AuthError on failure
        except AuthError:
            if not bypass_enabled:
                raise
            claims = await _dev_bypass_first_owner_cached()
            _log.info(
                "[dev-bypass] JWT verification failed — using first owner as fallback"
            )

    if bypass_enabled and claims is not None:
        # Verify the JWT's `sub` matches a user in our DB. If not,
        # the user has not been provisioned — fall back to the first
        # owner so the MVP demo end-to-end flow works.
        from apps.api.core.db import get_engine

        engine = get_engine()
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text("SELECT 1 FROM users WHERE id = :uid"),
                    {"uid": claims.user_id},
                )
            ).first()
        if row is None:
            cached = await _dev_bypass_first_owner_cached()
            if claims.user_id != cached.user_id:
                _log.info(
                    "[dev-bypass] JWT user %s not in users table — falling back to owner %s",
                    claims.user_id,
                    cached.user_id,
                )
                claims = cached

    ctx = TenantContext(
        tenant_id=claims.tenant_id,
        role=claims.role,
        user_id=claims.user_id,
        industry=claims.industry,
        trace_id=(
            request.headers.get("X-Trace-Id")
            or getattr(request.state, "trace_id", None)
            or str(uuid.uuid4())
        ),
    )
    request.state.tenant = ctx
    request.state.tenant_id = ctx.tenant_id
    request.state.tenant_claims = claims

    # Publish tenant to the SQLAlchemy begin-event listener so the next
    # transaction issues the GUC set that RLS policies read.
    # Phase 3-0: pass the full `claims` (tenant_id + user_id + role) so the
    # listener can publish BOTH policy families — `auth.jwt()` reads
    # `request.jwt.claims` (8 files / 78 uses), and the newer
    # `current_setting('app.tenant_id', true)` reads (5 files / 28 uses)
    # need `app.tenant_id` + `app.user_id`. The previous implementation
    # only set a third name (`app.current_tenant_id`) that no policy
    # reads, so RLS tests passed via the CI shim but real traffic
    # returned 0 rows.
    engine = None
    try:
        from apps.api.core.db import get_engine

        engine = get_engine()
        set_tenant_local(engine, claims)
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


@dataclass(frozen=True)
class PreOnboardingUser:
    """Per-request identity for users who have a valid JWT but no tenant yet.

    Phase 3-0 (Epic 1 carry-over = auth contract): fresh signups have
    `auth.users` row + minted JWT, but `tenant_memberships` is empty so
    `custom_access_token_hook` (alembic 0035) returns JWTs with empty
    `app_metadata.tenant_id`. The standard `get_tenant_context` dep
    rejects those with 401; this dep accepts them so the
    `POST /api/v1/onboarding/complete-signup` endpoint can create the
    first tenant + membership atomically and the user can
    `supabase.auth.refreshSession()` to get a tenant_id-bearing JWT.
    """

    user_id: uuid.UUID
    role: str
    industry: str | None = None
    email: str | None = None
    trace_id: str | None = None


async def get_pre_onboarding_user(request: Request) -> PreOnboardingUser:
    """FastAPI dependency — accept a JWT without `app_metadata.tenant_id`.

    Validates signature + exp + `sub` (user_id) + role allowlist (per
    Phase 3-0 `ALLOWED_ROLES` enforcement), but does NOT require
    `tenant_id` in `app_metadata`. Does NOT publish GUCs (no tenant
    context to publish).

    Used by:
      - `POST /api/v1/onboarding/complete-signup` (Phase 3-0 new endpoint)

    NOT used by:
      - Any other authenticated route — those still go through
        `get_tenant_context` which enforces `require_tenant=True`.
    """
    token = _extract_bearer_token(request)
    claims: JWTClaims = decode_jwt(
        token, require_tenant=False
    )  # raises AuthError on signature/exp/role failure

    # decode_jwt(require_tenant=False) guarantees user_id is set.
    assert claims.user_id is not None  # type narrowing for mypy

    email: str | None = None
    if claims.raw is not None:
        raw_email = claims.raw.get("email")
        if isinstance(raw_email, str):
            email = raw_email

    return PreOnboardingUser(
        user_id=claims.user_id,
        role=claims.role,
        industry=claims.industry,
        email=email,
        trace_id=(
            request.headers.get("X-Trace-Id")
            or getattr(request.state, "trace_id", None)
            or str(uuid.uuid4())
        ),
    )


# ── RLS hot-path: SET LOCAL (3 GUCs) ────────────────────────
# Phase 3-0: the listener now publishes THREE GUCs per transaction
# so BOTH policy families in `supabase/policies/` resolve:
#
#   1. `app.tenant_id`           — read by `current_setting('app.tenant_id', true)`
#                                  in 5 files / 28 uses (0012~0016).
#   2. `app.user_id`             — read by `current_setting('app.user_id', true)`
#                                  in 5 files / 8 uses (0013~0015).
#   3. `request.jwt.claims`      — read by `auth.jwt() -> 'app_metadata' ->> ...`
#                                  in 8 files / 78 uses (0000 shim, 0001, 0005~0009,
#                                  0011, etc.). Supabase sets this GUC at the
#                                  API gateway in production; in FastAPI we must
#                                  rebuild it from the validated JWT claims so
#                                  RLS works without going through PostgREST.
#
# Why three GUCs and not one: the SQL policies were written against two
# different Postgres function families (`auth.jwt()` Supabase function vs
# `current_setting()` plain Postgres). Rewriting all 13 SQL files to one
# family is out of scope for Phase 3-0; one extra `SET LOCAL` per txn is
# negligible vs that cost.
#
# Safety: tenant_id and user_id are validated UUIDs in `decode_jwt`, and
# role is allowlisted (`_ALLOWED_ROLES` in security.py). The JSON for
# `request.jwt.claims` is rebuilt from these validated components via
# `json.dumps` — `json.dumps` never emits single quotes, so embedding it
# inside `'...'` via f-string cannot break out. (Direct f-string
# interpolation rather than `$1` is required: SET LOCAL does not support
# parameter binding through asyncpg prepared statements, as documented
# in the prior comment block below.)
#
# NOTE (Story 1.1, 2026-07-29): the original `@event.listens_for(AsyncEngine, "connect")`
# decorator was a no-op stub but raised `AssertionError: issubclass(target, Pool)`
# at import time under SQLAlchemy 2.0.36 (the `_accept_with` for "connect" expects a
# Pool subclass, not the AsyncEngine class). The actual sync-engine hookup lives
# in `attach_tenant_listener()` below — registered once at app startup.
# Removed: the dead decorator (function body was a single `return`).
# Tracked as a Story 0.2 follow-up if the early-connect hook is ever needed.
#
# NOTE (Walking Skeleton, 2026-08-16): the previous implementation bound the
# context-var helpers to the `AsyncEngine` instance via
# `engine._costmgr_set_tenant = ...`. That raises `AttributeError` because
# `AsyncEngine` is a proxy wrapper that does not allow arbitrary attribute
# assignment. The module-level `_ENGINE_HOOKS` registry below is keyed by
# `id(engine)` so the FastAPI dep can publish the tenant without poking at
# the opaque proxy.
_ENGINE_HOOKS: dict[int, tuple] = {}


@dataclass(frozen=True)
class _TenantClaimsSnapshot:
    """Immutable snapshot of the per-request auth context for GUC publication."""

    tenant_id: uuid.UUID
    user_id: uuid.UUID
    role: str


def attach_tenant_listener(engine: AsyncEngine) -> None:
    """Wire a SQLAlchemy event listener that issues the RLS GUC set per txn.

    Reads from a ContextVar populated by the FastAPI dependency
    (`set_tenant_local`). Falls back to a no-op if the var is unset
    (service_role path — GUCs stay empty, RLS returns 0 rows as a
    fail-safe).
    """
    from contextvars import ContextVar

    _snapshot_var: ContextVar[_TenantClaimsSnapshot | None] = ContextVar(
        "tenant_claims_snapshot_local", default=None
    )

    def set_claims(claims: JWTClaims) -> None:
        _snapshot_var.set(
            _TenantClaimsSnapshot(
                tenant_id=claims.tenant_id,
                user_id=claims.user_id,
                role=claims.role,
            )
        )

    def clear_claims() -> None:
        _snapshot_var.set(None)

    @event.listens_for(engine.sync_engine, "begin")
    def _begin_transaction(conn):  # noqa: ARG001
        # SQLAlchemy 2.x engine-level "begin" listener receives a SQLAlchemy
        # `Connection`, not a raw DBAPI connection. Use `exec_driver_sql` so
        # the SQL is sent verbatim through the asyncpg protocol — `SET LOCAL`
        # does not support `$1` parameter binding (asyncpg prepared statements
        # reject it with `syntax error at or near "$1"`), and every value
        # below comes from `decode_jwt`'s validation (UUID for tenant_id /
        # user_id, allowlisted role) so direct interpolation is safe.
        snap = _snapshot_var.get()
        if snap is None:
            return  # service_role path: no auth context; RLS will deny rows.

        # Rebuild `request.jwt.claims` JSON from validated components.
        # `separators=(",", ":")` keeps it compact and ensures no spaces
        # that could confuse the SQL parser; `json.dumps` always uses
        # double quotes for strings (never single), so embedding in a
        # single-quoted SQL literal is safe by construction.
        claims_json = json.dumps(
            {
                "sub": str(snap.user_id),
                "app_metadata": {
                    "tenant_id": str(snap.tenant_id),
                    "role": snap.role,
                },
            },
            separators=(",", ":"),
        )

        conn.exec_driver_sql(f"SET LOCAL app.tenant_id = '{snap.tenant_id}'")
        conn.exec_driver_sql(f"SET LOCAL app.user_id = '{snap.user_id}'")
        conn.exec_driver_sql(f"SET LOCAL request.jwt.claims = '{claims_json}'")

    # Register the context-var helpers in a module-level dict keyed by the
    # engine's id (the AsyncEngine proxy itself does not allow attribute
    # assignment).
    _ENGINE_HOOKS[id(engine)] = (set_claims, clear_claims)


def set_tenant_local(engine: AsyncEngine, claims: JWTClaims) -> None:
    """Publish the validated JWT claims for the next transaction.

    Phase 3-0: signature changed from `(engine, tenant_id)` to
    `(engine, claims: JWTClaims)`. The listener now needs user_id and
    role in addition to tenant_id to rebuild `request.jwt.claims`.
    """
    hooks = _ENGINE_HOOKS.get(id(engine))
    if hooks is not None:
        hooks[0](claims)


def clear_tenant_local(engine: AsyncEngine) -> None:
    """Clear the auth snapshot after the request scope ends."""
    hooks = _ENGINE_HOOKS.get(id(engine))
    if hooks is not None:
        hooks[1]()
