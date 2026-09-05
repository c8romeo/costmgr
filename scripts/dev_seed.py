"""scripts/dev_seed.py — local development seed + dev JWT minter.

Walking Skeleton verification sprint.

Purpose
-------
The repo had no way to bring up a *usable* tenant: CI only ever created
schema, and every DB-backed test was skipped. Without a real tenant row
there is no way to answer "does the monthly-close path actually work?".

This script creates the minimum identity graph the API needs:

    tenants  ->  users  ->  tenant_memberships  ->  tenant_settings

and then mints an HS256 JWT that `apps/api/core/security.py::decode_jwt`
will accept, with `tenant_id` / `role` in `app_metadata` per AD-3
(NEVER in `user_metadata` — that field is user-editable).

Deliberately minimal: it seeds *identity only*, not business data. The
smoke driver (`scripts/smoke_e2e.py`) fills settings, products, BOM and
monthly input through the real HTTP endpoints, because driving the real
endpoints is the whole point of the exercise. Seeding business rows
directly would hide exactly the integration bugs we are hunting.

Idempotent: UUIDs are deterministic (UUIDv5 over a fixed namespace), so
re-running updates rather than duplicating.

Usage
-----
    make db-seed
    # or
    set -a; source apps/api/.env; set +a
    uv run python scripts/dev_seed.py

Outputs the dev access token and the exact browser cookie to paste.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as _dt
import os
import sys
import uuid

import asyncpg
import jwt

# ── Deterministic dev identity ─────────────────────────────────
# UUIDv5 keeps re-runs idempotent without needing a lookup round-trip.
_NS = uuid.UUID("11111111-2222-3333-4444-555555555555")

DEV_TENANT_ID = uuid.uuid5(_NS, "costmgr-dev-tenant")
DEV_USER_ID = uuid.uuid5(_NS, "costmgr-dev-user")
DEV_MEMBERSHIP_ID = uuid.uuid5(_NS, "costmgr-dev-membership")

# cj-276 (Epic 29+ Story 29.1): deterministic PRD-NEG product for the
# closing-guard NEGATIVE_CLOSING_PERIOD scenario seed. UUIDv5 keeps
# re-runs idempotent across invocations.
DEV_PRODUCT_ID_NEG = uuid.uuid5(_NS, "costmgr-dev-product-prd-neg")

# cj-276 (Epic 29+ Story 29.3): deterministic fiscal_period_snapshots
# row identity for the snapshot_persisted scenario seed.
DEV_SNAPSHOT_COMMITTED_ID = uuid.uuid5(
    _NS, "costmgr-dev-snapshot-committed-2026-07"
)
DEV_RESULT_HASH_COMMITTED = "a" * 64  # 64-char hex SHA-256 placeholder

DEV_EMAIL = "dev@costmgr.local"
DEV_ROLE = "owner"
DEV_TENANT_NAME = "개발용 테넌트"

# AD-10 industry enum.
#
# ⚠️ KNOWN CROSS-LAYER DRIFT (found by this sprint — see the truth report):
#   DB CHECK  (alembic 0001, tenants.industry):
#       manufacturing | manufacturing_retail | service | mixed
#   App canonical (packages/services/m0_onboarding/industry_menu.py:33):
#       manufacturing | service | manufacturing_service | manufacturing_service_other
#   Only `manufacturing` and `service` exist in BOTH. Writing the canonical
#   `manufacturing_service` / `manufacturing_service_other` to tenants.industry
#   would violate the DB CHECK.
#
# `manufacturing` is chosen as the default because it is valid under both
# vocabularies AND holds the full capability matrix (BOM, COST_CALCULATION,
# INVENTORY_LEDGER, MONTHLY_CLOSING_REPORT, CLOSE_SEQUENCE_LOCK), which is
# exactly what the MVP critical path needs.
DEFAULT_INDUSTRY = "manufacturing"

# Values the DB CHECK constraint will accept today.
DB_ALLOWED_INDUSTRIES = ("manufacturing", "manufacturing_retail", "service", "mixed")

TOKEN_TTL_HOURS = 24 * 30  # long-lived: this is a localhost dev token


def _sync_dsn(database_url: str) -> str:
    """Strip the SQLAlchemy async driver marker for raw asyncpg."""
    return database_url.replace("postgresql+asyncpg://", "postgresql://")


def mint_dev_token(
    *,
    secret: str,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    role: str,
    industry: str,
    ttl_hours: int = TOKEN_TTL_HOURS,
) -> str:
    """Mint a Supabase-shaped HS256 JWT that decode_jwt() accepts.

    AD-3: tenant_id and role live in `app_metadata` (server-controlled),
    never in `user_metadata`.
    """
    now = _dt.datetime.now(tz=_dt.timezone.utc)
    payload = {
        "sub": str(user_id),
        "aud": "authenticated",
        "role": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int((now + _dt.timedelta(hours=ttl_hours)).timestamp()),
        "email": DEV_EMAIL,
        "app_metadata": {
            "tenant_id": str(tenant_id),
            "role": role,
            "industry": industry,
        },
        "user_metadata": {},
    }
    return jwt.encode(payload, secret, algorithm="HS256")


async def seed(conn: asyncpg.Connection, industry: str) -> None:
    """Insert (or refresh) the dev identity graph."""
    await conn.execute(
        """
        INSERT INTO tenants (id, name, industry)
        VALUES ($1, $2, $3)
        ON CONFLICT (id) DO UPDATE
            SET name = EXCLUDED.name,
                industry = EXCLUDED.industry,
                deleted_at = NULL
        """,
        DEV_TENANT_ID,
        DEV_TENANT_NAME,
        industry,
    )

    await conn.execute(
        """
        INSERT INTO users (id, tenant_id, email, role)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (id) DO UPDATE
            SET tenant_id = EXCLUDED.tenant_id,
                email = EXCLUDED.email,
                role = EXCLUDED.role
        """,
        DEV_USER_ID,
        DEV_TENANT_ID,
        DEV_EMAIL,
        DEV_ROLE,
    )

    await conn.execute(
        """
        INSERT INTO tenant_memberships (id, tenant_id, user_id, role)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (tenant_id, user_id) DO UPDATE
            SET role = EXCLUDED.role
        """,
        DEV_MEMBERSHIP_ID,
        DEV_TENANT_ID,
        DEV_USER_ID,
        DEV_ROLE,
    )

    # tenant_settings: create the row only. The JSONB namespaces are
    # populated through the real settings-wizard endpoints by the smoke
    # driver, so that path gets exercised rather than bypassed.
    await conn.execute(
        """
        INSERT INTO tenant_settings (tenant_id)
        VALUES ($1)
        ON CONFLICT (tenant_id) DO NOTHING
        """,
        DEV_TENANT_ID,
    )


# ── Epic 29+ scenario seeds (cj-276 wire) ──────────────────
async def _seed_closing_guard_negative(conn: asyncpg.Connection) -> None:
    """Story 29.1 — seed PRD-NEG product + inventory_ledger events so
    `closing_qty(PRD-NEG, 2026-08)` aggregates to -5.

    Story 5.2 wire: `closing_qty` is **derived** from `inventory_ledger`
    aggregate via `compute_closing_balance_per_product`. To force a
    NEGATIVE_CLOSING invariant, we insert 1 `adjustment_negative` event
    with qty=-5 (no opening_carried carry — period starts at 0).

    Idempotent: ON CONFLICT DO NOTHING on `products(id)` and
    `inventory_ledger(event_id)`. re-runs are safe.
    """
    # 1. product PRD-NEG (idempotent)
    await conn.execute(
        """
        INSERT INTO products (
            id, tenant_id, product_type, code, name, unit,
            unit_cost_krw, is_active
        )
        VALUES ($1, $2, 'goods', 'PRD-NEG', 'PRD-NEG closing-guard fixture', 'EA',
                0, TRUE)
        ON CONFLICT (id) DO NOTHING
        """,
        DEV_PRODUCT_ID_NEG,
        DEV_TENANT_ID,
    )

    # 2. inventory_ledger event (idempotent via deterministic event_id)
    event_id = uuid.uuid5(_NS, "costmgr-dev-ledger-prd-neg-2026-08")
    await conn.execute(
        """
        INSERT INTO inventory_ledger (
            event_id, tenant_id, product_id, period_key,
            event_type, qty, trace_id
        )
        VALUES ($1, $2, $3, '2026-08', 'adjustment_negative', -5, $4)
        ON CONFLICT (event_id) DO NOTHING
        """,
        event_id,
        DEV_TENANT_ID,
        DEV_PRODUCT_ID_NEG,
        DEV_USER_ID,  # trace_id uses UUID; reuse DEV_USER_ID as fixture
    )


async def _seed_snapshot_persisted(conn: asyncpg.Connection) -> None:
    """Story 29.3 — seed 1 fiscal_period_snapshots row with
    state='committed' for period '2026-07'.

    cj-275 spec calls for deterministic `result_hash` (placeholder
    accepted — actual hash comes from real engine run via Story 4.2).
    5 KRW fields set to 0 (placeholder; spec AC is row existence +
    state='committed' + result_hash, not exact KRW values).

    Idempotent: ON CONFLICT DO UPDATE on the unique key
    `(tenant_id, period_key, baseline_revision, engine_type)`.
    """
    await conn.execute(
        """
        INSERT INTO fiscal_period_snapshots (
            snapshot_id, tenant_id, period_key, baseline_revision, engine_type,
            material_cost, labor_cost, overhead_cost, manufacturing_cost,
            inventory_adjustment, result_hash, state
        )
        VALUES (
            $1, $2, '2026-07', 1, 'trad',
            0, 0, 0, 0, 0, $3, 'committed'
        )
        ON CONFLICT (tenant_id, period_key, baseline_revision, engine_type)
        DO UPDATE SET
            state = EXCLUDED.state,
            result_hash = EXCLUDED.result_hash
        """,
        DEV_SNAPSHOT_COMMITTED_ID,
        DEV_TENANT_ID,
        DEV_RESULT_HASH_COMMITTED,
    )


async def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the local dev tenant.")
    parser.add_argument(
        "--industry",
        default=DEFAULT_INDUSTRY,
        choices=list(DB_ALLOWED_INDUSTRIES),
        help="Industry for the dev tenant (default: manufacturing). "
        "Constrained to the DB CHECK vocabulary, which currently drifts "
        "from the app's canonical enum — see the comment above.",
    )
    parser.add_argument(
        "--token-only",
        action="store_true",
        help="Skip DB writes; just print a token for the existing dev tenant.",
    )
    parser.add_argument(
        "--scenario",
        choices=["closing_guard_negative", "snapshot_persisted", "all"],
        default=None,
        help=(
            "cj-276 (Epic 29+ wire): optional business-data scenario seed "
            "beyond identity. Use 'closing_guard_negative' for Story 29.1 "
            "NEGATIVE_CLOSING_PERIOD fixture, 'snapshot_persisted' for "
            "Story 29.3 fiscal_period_snapshots row, or 'all' for both."
        ),
    )
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    secret = os.environ.get("SUPABASE_JWT_SECRET")

    if not secret:
        print(
            "ERROR: SUPABASE_JWT_SECRET is not set.\n"
            "       Run via `make db-seed`, or: set -a; source apps/api/.env; set +a",
            file=sys.stderr,
        )
        return 2

    if not args.token_only:
        if not database_url:
            print("ERROR: DATABASE_URL is not set.", file=sys.stderr)
            return 2
        conn = await asyncpg.connect(_sync_dsn(database_url))
        try:
            await seed(conn, args.industry)
            if args.scenario in ("closing_guard_negative", "all"):
                await _seed_closing_guard_negative(conn)
            if args.scenario in ("snapshot_persisted", "all"):
                await _seed_snapshot_persisted(conn)
        finally:
            await conn.close()

    token = mint_dev_token(
        secret=secret,
        tenant_id=DEV_TENANT_ID,
        user_id=DEV_USER_ID,
        role=DEV_ROLE,
        industry=args.industry,
    )

    print("=" * 68)
    print("  costmgr dev seed complete")
    print("=" * 68)
    print(f"  tenant_id : {DEV_TENANT_ID}")
    print(f"  user_id   : {DEV_USER_ID}")
    print(f"  email     : {DEV_EMAIL}")
    print(f"  role      : {DEV_ROLE}")
    print(f"  industry  : {args.industry}")
    print("-" * 68)
    print("  Access token (Authorization: Bearer <token>):")
    print(f"{token}")
    print("-" * 68)
    print("  Browser cookie — paste into DevTools console on http://localhost:3000 :")
    print(f'    document.cookie = "sb-access-token={token}; path=/"')
    print("=" * 68)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
