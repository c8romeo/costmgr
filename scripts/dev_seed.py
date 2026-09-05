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
import json
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

# cj-278a (Epic 29+ Stories 29.2/29.4/29.5/29.6): deterministic
# fiscal_periods + ledger event identities for the 4 m11 scenario seeds
# (D-WEB-E2E-2 ownership absorbed from cj-274 honest-DEFER).
DEV_FISCAL_PERIOD_2026_08_ID = uuid.uuid5(_NS, "costmgr-dev-fiscal-period-2026-08")
DEV_FISCAL_PERIOD_2026_07_ID = uuid.uuid5(_NS, "costmgr-dev-fiscal-period-2026-07")
DEV_LEDGER_EVT_001_ID = uuid.uuid5(_NS, "costmgr-dev-ledger-evt-001-2026-07")
DEV_AI_INSIGHT_CACHE_2026_07_ID = uuid.uuid5(
    _NS, "costmgr-dev-ai-insight-cache-2026-07"
)

# cj-278b (Epic 29+ Stories 29.7/29.8/29.9/29.10): deterministic user
# identities for the 4 m12-2FA scenario seeds (D-WEB-E2E-3 ownership
# absorbed from cj-274 honest-DEFER). Each scenario requires a distinct
# `users` row with the right `totp_*` column state per spec AC.
DEV_USER_NO_2FA_ID = uuid.uuid5(_NS, "costmgr-dev-user-no-2fa")
DEV_USER_LOCK_ID = uuid.uuid5(_NS, "costmgr-dev-user-lock")
DEV_USER_REC_ID = uuid.uuid5(_NS, "costmgr-dev-user-rec")
DEV_USER_SETUP_ID = uuid.uuid5(_NS, "costmgr-dev-user-setup")

# cj-278c (Epic 29+ Stories 29.11/29.12/29.13/29.14): deterministic
# tenant + user + audit identities for the 4 m12-3 deletion scenario
# seeds (D-WEB-E2E-4 ownership absorbed from cj-274 honest-DEFER).
#
# 29.11 + 29.12 deliberately reuse DEV_TENANT_ID: both spec ACs only
# require `status='active'`, and the dev JWT's `app_metadata.tenant_id`
# points at DEV_TENANT_ID, so a separate tenant would be unreachable by
# the E2E session. 29.13 + 29.14 need `status='pending_deletion'`, which
# would break every *other* scenario if applied to DEV_TENANT_ID, so
# each gets its own tenant + requester user.
DEV_TENANT_DELETION_PENDING_ID = uuid.uuid5(_NS, "costmgr-dev-tenant-deletion-pending")
DEV_TENANT_DELETION_EXPIRED_ID = uuid.uuid5(_NS, "costmgr-dev-tenant-deletion-expired")
DEV_USER_DELETION_PENDING_ID = uuid.uuid5(_NS, "costmgr-dev-user-deletion-pending")
DEV_USER_DELETION_EXPIRED_ID = uuid.uuid5(_NS, "costmgr-dev-user-deletion-expired")
DEV_MEMBERSHIP_DELETION_PENDING_ID = uuid.uuid5(
    _NS, "costmgr-dev-membership-deletion-pending"
)
DEV_MEMBERSHIP_DELETION_EXPIRED_ID = uuid.uuid5(
    _NS, "costmgr-dev-membership-deletion-expired"
)

# `audit_logs` is append-only (alembic 0001 installs BEFORE UPDATE and
# BEFORE DELETE triggers that RAISE), so every seeded audit row uses a
# deterministic id + `ON CONFLICT DO NOTHING`. Never DO UPDATE here —
# the trigger would fire and abort the whole seed.
DEV_AUDIT_DEL_PENDING_CONSENT_ID = uuid.uuid5(
    _NS, "costmgr-dev-audit-deletion-pending-consent"
)
DEV_AUDIT_DEL_PENDING_REQUESTED_ID = uuid.uuid5(
    _NS, "costmgr-dev-audit-deletion-pending-requested"
)
DEV_AUDIT_DEL_EXPIRED_CONSENT_ID = uuid.uuid5(
    _NS, "costmgr-dev-audit-deletion-expired-consent"
)
DEV_AUDIT_DEL_EXPIRED_REQUESTED_ID = uuid.uuid5(
    _NS, "costmgr-dev-audit-deletion-expired-requested"
)

# Audit `action` values quoted verbatim from
# packages/services/m12_account/account_deletion.py:47-51. The Story
# 29.12/29.13/29.14 ACs name *different* strings — see the spec-drift
# notes on each deletion seed function.
ACTION_DELETION_CONSENT_GIVEN = "deletion_consent_given"
ACTION_DELETION_REQUESTED = "deletion_requested"

# `emit_audit_typed()` writes ActionClass.ACCOUNT_DELETION.value into
# audit_logs.target_table (account_deletion_service.py:648-675).
AUDIT_TARGET_TABLE_ACCOUNT_DELETION = "account_deletion"

# packages/services/m12_account/account_deletion.py:39 — MVP fixed 30일.
DELETION_RETENTION_DAYS = 30

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


# ── Epic 29+ m11 scenario seeds (cj-278a wire) ──────────────
async def _seed_close_sequence_partial(conn: asyncpg.Connection) -> None:
    """Story 29.2 — seed fiscal_periods row with partial close sequence
    state (제조·ABC·공동 단계 미완료) so that the [마감] button is
    disabled and the banner displays the partial-close ko-KR string.

    AD-6 close lock + AD-20 state machine:
      - close_sequence_state='manufacturing' means divisions completed
        but manufacturing / abc / common NOT yet completed.
      - divisions_completed_at=NOW(), others NULL → defense-in-depth
        CHECK constraint allows this state.
      - status='closing' is the visible pre-close state.
      - close_sequence_blocked_reason_ko carries the partial-close
        banner string verbatim per Story 29.2 ko-KR spec.

    Idempotent: ON CONFLICT (tenant_id, period_key) DO UPDATE.
    """
    await conn.execute(
        """
        INSERT INTO fiscal_periods (
            id, tenant_id, period_key, status,
            divisions_completed_at, manufacturing_completed_at,
            abc_completed_at, common_completed_at,
            close_sequence_state, close_sequence_blocked_reason_ko
        )
        VALUES (
            $1, $2, '2026-08', 'closing',
            NOW(), NULL, NULL, NULL,
            'manufacturing',
            '제조·ABC·공동 단계 미완료 — 전체 완료 후 마감 가능'
        )
        ON CONFLICT (tenant_id, period_key) DO UPDATE SET
            status = EXCLUDED.status,
            close_sequence_state = EXCLUDED.close_sequence_state,
            close_sequence_blocked_reason_ko = EXCLUDED.close_sequence_blocked_reason_ko,
            divisions_completed_at = EXCLUDED.divisions_completed_at,
            manufacturing_completed_at = EXCLUDED.manufacturing_completed_at,
            abc_completed_at = EXCLUDED.abc_completed_at,
            common_completed_at = EXCLUDED.common_completed_at
        """,
        DEV_FISCAL_PERIOD_2026_08_ID,
        DEV_TENANT_ID,
    )


async def _seed_reversal_input(conn: asyncpg.Connection) -> None:
    """Story 29.4 — seed fiscal_periods row with status='closed' +
    close_sequence_state='confirmed' (i.e. fully committed period)
    so that operator can trigger [역분개] action against an existing
    committed period.

    Spec drift: Story 29.4 AC references `state='committed'` but the
    actual fiscal_periods schema (alembic 0020) uses
    `status='closed' AND close_sequence_state='confirmed'` to represent
    a committed period. cj-280 retro scope.

    Idempotent: ON CONFLICT (tenant_id, period_key) DO UPDATE.
    """
    await conn.execute(
        """
        INSERT INTO fiscal_periods (
            id, tenant_id, period_key, status,
            divisions_completed_at, manufacturing_completed_at,
            abc_completed_at, common_completed_at,
            close_sequence_state, closed_at, closed_by_actor_id
        )
        VALUES (
            $1, $2, '2026-07', 'closed',
            NOW(), NOW(), NOW(), NOW(),
            'confirmed', NOW(), $3
        )
        ON CONFLICT (tenant_id, period_key) DO UPDATE SET
            status = EXCLUDED.status,
            close_sequence_state = EXCLUDED.close_sequence_state,
            divisions_completed_at = EXCLUDED.divisions_completed_at,
            manufacturing_completed_at = EXCLUDED.manufacturing_completed_at,
            abc_completed_at = EXCLUDED.abc_completed_at,
            common_completed_at = EXCLUDED.common_completed_at,
            closed_at = EXCLUDED.closed_at,
            closed_by_actor_id = EXCLUDED.closed_by_actor_id
        """,
        DEV_FISCAL_PERIOD_2026_07_ID,
        DEV_TENANT_ID,
        DEV_USER_ID,
    )


async def _seed_reversal_cache_invalidation(conn: asyncpg.Connection) -> None:
    """Story 29.5 — seed fiscal_periods row (status='closed') +
    populated ai_insight_cache row so that operator can trigger a
    reversal INSERT (per Story 29.4 sequence) and then verify AD-25
    cache invalidation + cold compute (≤ 30s, NFR11).

    ai_insight_cache row is pre-populated with the verbatim
    `calculation_result_hash` from cj-276 (`a` * 64) so the cache
    key is deterministic across re-runs. Per AD-25 the cache key is
    `(tenant_id, period_key, calculation_result_hash)`.

    Idempotent: ON CONFLICT (tenant_id, period_key, insight_kind,
    calculation_result_hash) DO UPDATE.
    """
    # 1. fiscal_periods row (same as reversal_input — idempotent)
    await conn.execute(
        """
        INSERT INTO fiscal_periods (
            id, tenant_id, period_key, status,
            divisions_completed_at, manufacturing_completed_at,
            abc_completed_at, common_completed_at,
            close_sequence_state, closed_at, closed_by_actor_id
        )
        VALUES (
            $1, $2, '2026-07', 'closed',
            NOW(), NOW(), NOW(), NOW(),
            'confirmed', NOW(), $3
        )
        ON CONFLICT (tenant_id, period_key) DO UPDATE SET
            status = EXCLUDED.status,
            close_sequence_state = EXCLUDED.close_sequence_state,
            closed_at = EXCLUDED.closed_at
        """,
        DEV_FISCAL_PERIOD_2026_07_ID,
        DEV_TENANT_ID,
        DEV_USER_ID,
    )

    # 2. ai_insight_cache row populated
    # NOTE: insight_kind and source_kind must respect the alembic 0030
    # CHECK constraints (insight_kind IN ('cost_reduction_candidate',
    # 'anomaly_pattern', 'forecast'); source_kind IN ('auto_analysis',
    # 'ai_reference')). Story 29.5 verification reuses 'forecast' as the
    # closest m11 close summary surface — cj-280 retro scope if Story
    # 29.5 AC requires a dedicated 'period_summary' enum value.
    await conn.execute(
        """
        INSERT INTO ai_insight_cache (
            insight_cache_id, tenant_id, period_key,
            calculation_result_hash, insight_kind, source_kind,
            question, answer
        )
        VALUES (
            $1, $2, '2026-07',
            $3, 'forecast', 'auto_analysis',
            '2026-07 기간 마감 요약', 'cached AI insight for AD-25 invalidation verification'
        )
        ON CONFLICT (tenant_id, period_key, insight_kind, calculation_result_hash)
        DO UPDATE SET
            answer = EXCLUDED.answer,
            generated_at = NOW()
        """,
        DEV_AI_INSIGHT_CACHE_2026_07_ID,
        DEV_TENANT_ID,
        DEV_RESULT_HASH_COMMITTED,
    )


async def _seed_reopen_audit(conn: asyncpg.Connection) -> None:
    """Story 29.6 — seed fiscal_periods row with status='closed' +
    close_sequence_state='confirmed' (i.e. committed period) so that
    operator can trigger reopen action with reason + audit_logs row
    verification.

    Spec drift: Story 29.6 AC references `state='committed'` but the
    actual schema uses `status='closed' AND close_sequence_state='confirmed'`
    — same drift as Story 29.4. cj-280 retro scope.

    Idempotent: ON CONFLICT (tenant_id, period_key) DO UPDATE.
    """
    await conn.execute(
        """
        INSERT INTO fiscal_periods (
            id, tenant_id, period_key, status,
            divisions_completed_at, manufacturing_completed_at,
            abc_completed_at, common_completed_at,
            close_sequence_state, closed_at, closed_by_actor_id
        )
        VALUES (
            $1, $2, '2026-07', 'closed',
            NOW(), NOW(), NOW(), NOW(),
            'confirmed', NOW(), $3
        )
        ON CONFLICT (tenant_id, period_key) DO UPDATE SET
            status = EXCLUDED.status,
            close_sequence_state = EXCLUDED.close_sequence_state,
            closed_at = EXCLUDED.closed_at
        """,
        DEV_FISCAL_PERIOD_2026_07_ID,
        DEV_TENANT_ID,
        DEV_USER_ID,
    )


# ── Epic 29+ m12-2FA scenario seeds (cj-278b wire) ────────────
async def _seed_two_factor_challenge(conn: asyncpg.Connection) -> None:
    """Story 29.7 — seed users row with `totp_enabled_at IS NULL`
    (i.e. NOT 2FA-enrolled) so that the M2 [월 입력] gate fires the
    2FA setup modal per AD-10 + NFR7 2FA mandatory policy.

    Spec drift: Story 29.7 AC references `totp_enabled=false` but the
    actual schema (alembic 0022) uses `totp_enabled_at IS NULL` as
    the authoritative 2FA-enrolled predicate (the legacy `twofa_enabled`
    BOOLEAN column from alembic 0001 is kept in sync). cj-278b seeds
    BOTH columns correctly: `totp_enabled_at = NULL` + `twofa_enabled =
    FALSE`. cj-280 retro scope.

    Idempotent: ON CONFLICT (id) DO UPDATE.
    """
    await conn.execute(
        """
        INSERT INTO users (
            id, tenant_id, email, role,
            twofa_enabled,
            totp_secret, totp_enabled_at,
            totp_failed_attempts, totp_lockout_until,
            totp_recovery_codes_hash
        )
        VALUES (
            $1, $2, 'no-2fa@costmgr.local', 'owner',
            FALSE,
            NULL, NULL,
            0, NULL,
            NULL
        )
        ON CONFLICT (id) DO UPDATE SET
            tenant_id = EXCLUDED.tenant_id,
            email = EXCLUDED.email,
            role = EXCLUDED.role,
            twofa_enabled = EXCLUDED.twofa_enabled,
            totp_secret = EXCLUDED.totp_secret,
            totp_enabled_at = EXCLUDED.totp_enabled_at,
            totp_failed_attempts = EXCLUDED.totp_failed_attempts,
            totp_lockout_until = EXCLUDED.totp_lockout_until,
            totp_recovery_codes_hash = EXCLUDED.totp_recovery_codes_hash
        """,
        DEV_USER_NO_2FA_ID,
        DEV_TENANT_ID,
    )


async def _seed_two_factor_lockout(conn: asyncpg.Connection) -> None:
    """Story 29.8 — seed users row with `totp_enabled_at = NOW()`
    (i.e. 2FA-enrolled) and `totp_failed_attempts = 4` so that ONE
    more wrong TOTP code triggers the lockout policy per AD-10 +
    NFR7 (MAX_FAILED_ATTEMPTS=5).

    Spec drifts logged for cj-280 retro:
      ① Story 29.8 AC references `recent_failures=4` but actual schema
        column is `totp_failed_attempts` (alembic 0022). cj-278b seeds
        the schema-accurate column name.
      ② Story 29.8 AC references "30 minutes lockout" but actual backend
        uses `LOCKOUT_DURATION_SECONDS=900s=15min` (packages/services/
        m12_account/totp.py:45). cj-278b seeds `totp_lockout_until =
        NULL` so the test exercises the live lockout transition on the
        5th failure (which will set lockout to NOW()+15min, not 30min).
      ③ `totp_secret` is NULL in cj-278b seed (not AES-256-GCM encrypted
        test bytes). Reason: dev_seed.py runs in CI without
        `COSTMGR_AT_REST_KEY_V1` env-var (verified via grep), so the
        key_manager ephemeral-fallback generates a fresh key per
        process → decrypt at API runtime would fail. cj-278b source
        sprint honestly accepts this scope: the seed creates the
        schema-correct `totp_failed_attempts=4` state; the actual
        verify_totp_code decrypt path is a cj-280 retro scope (set
        `COSTMGR_AT_REST_KEY_V1` in CI + dev env consistently).
    """
    await conn.execute(
        """
        INSERT INTO users (
            id, tenant_id, email, role,
            twofa_enabled,
            totp_secret, totp_enabled_at,
            totp_failed_attempts, totp_lockout_until,
            totp_recovery_codes_hash
        )
        VALUES (
            $1, $2, 'lock-2fa@costmgr.local', 'owner',
            TRUE,
            NULL, NOW(),
            4, NULL,
            NULL
        )
        ON CONFLICT (id) DO UPDATE SET
            tenant_id = EXCLUDED.tenant_id,
            email = EXCLUDED.email,
            role = EXCLUDED.role,
            twofa_enabled = EXCLUDED.twofa_enabled,
            totp_secret = EXCLUDED.totp_secret,
            totp_enabled_at = EXCLUDED.totp_enabled_at,
            totp_failed_attempts = EXCLUDED.totp_failed_attempts,
            totp_lockout_until = EXCLUDED.totp_lockout_until,
            totp_recovery_codes_hash = EXCLUDED.totp_recovery_codes_hash
        """,
        DEV_USER_LOCK_ID,
        DEV_TENANT_ID,
    )


async def _seed_two_factor_recovery(conn: asyncpg.Connection) -> None:
    """Story 29.9 — seed users row with `totp_enabled_at = NOW()`
    (2FA-enrolled) AND `totp_recovery_codes_hash` = JSONB array of
    8 PBKDF2-HMAC-SHA256 entries with EXACTLY 3 unused (`used_at=''`)
    and 5 used (`used_at='2026-09-04T10:00:00Z'`).

    Salt + hash hex values are deterministic placeholder strings
    (`a` * 64 for salt, `b` * 64 for hash). The test spec will need
    to update one of the unused entries with a real PBKDF2 hash of a
    known recovery code before exercising the recovery flow — that
    real-hash update is a cj-278b close sprint scope (or cj-280 retro
    if it requires COSTMGR_AT_REST_KEY_V1 env-var setup).

    Spec drift: Story 29.9 AC references `recovery_codes_remaining=3`
    (count of unused codes) but actual schema stores the full array
    of 8 entries with per-entry `used_at` marker. cj-278b seeds with
    3 unused + 5 used entries → `recovery_codes_remaining=3` per spec.

    Idempotent: ON CONFLICT (id) DO UPDATE.
    """
    # JSONB array: 3 unused + 5 used entries, deterministic hex placeholders.
    # Real recovery code hash verification requires replacing these with
    # `apps.api.core.crypto`-encrypted + `hash_recovery_code()` PBKDF2
    # blobs — cj-278b close sprint / cj-280 retro scope.
    recovery_codes_json = json.dumps(
        [
            {"salt": "a" * 64, "hash": "b" * 64, "used_at": ""},
            {"salt": "a" * 64, "hash": "b" * 64, "used_at": ""},
            {"salt": "a" * 64, "hash": "b" * 64, "used_at": ""},
            {"salt": "a" * 64, "hash": "b" * 64, "used_at": "2026-09-04T10:00:00Z"},
            {"salt": "a" * 64, "hash": "b" * 64, "used_at": "2026-09-04T10:00:00Z"},
            {"salt": "a" * 64, "hash": "b" * 64, "used_at": "2026-09-04T10:00:00Z"},
            {"salt": "a" * 64, "hash": "b" * 64, "used_at": "2026-09-04T10:00:00Z"},
            {"salt": "a" * 64, "hash": "b" * 64, "used_at": "2026-09-04T10:00:00Z"},
        ]
    )
    await conn.execute(
        """
        INSERT INTO users (
            id, tenant_id, email, role,
            twofa_enabled,
            totp_secret, totp_enabled_at,
            totp_failed_attempts, totp_lockout_until,
            totp_recovery_codes_hash
        )
        VALUES (
            $1, $2, 'rec-2fa@costmgr.local', 'owner',
            TRUE,
            NULL, NOW(),
            0, NULL,
            $3::jsonb
        )
        ON CONFLICT (id) DO UPDATE SET
            tenant_id = EXCLUDED.tenant_id,
            email = EXCLUDED.email,
            role = EXCLUDED.role,
            twofa_enabled = EXCLUDED.twofa_enabled,
            totp_secret = EXCLUDED.totp_secret,
            totp_enabled_at = EXCLUDED.totp_enabled_at,
            totp_failed_attempts = EXCLUDED.totp_failed_attempts,
            totp_lockout_until = EXCLUDED.totp_lockout_until,
            totp_recovery_codes_hash = EXCLUDED.totp_recovery_codes_hash
        """,
        DEV_USER_REC_ID,
        DEV_TENANT_ID,
        recovery_codes_json,
    )


async def _seed_two_factor_setup(conn: asyncpg.Connection) -> None:
    """Story 29.10 — seed users row with `totp_enabled_at = NULL` +
    `totp_secret = NULL` (i.e. NOT yet enrolled) so that the 2FA
    setup wizard flow can be exercised end-to-end: (1) QR code
    generated, (2) TOTP code verified, (3) `totp_enabled_at` flips to
    NOW(), (4) audit log row appended.

    The setup wizard itself generates the AES-256-GCM encrypted
    `totp_secret` via `apps.api.core.crypto.encrypt_at_rest` (real
    production path with COSTMGR_AT_REST_KEY_V1). cj-278b seeds only
    the pre-state (no 2FA enrolled); the setup flow populates the
    rest.

    Idempotent: ON CONFLICT (id) DO UPDATE.
    """
    await conn.execute(
        """
        INSERT INTO users (
            id, tenant_id, email, role,
            twofa_enabled,
            totp_secret, totp_enabled_at,
            totp_failed_attempts, totp_lockout_until,
            totp_recovery_codes_hash
        )
        VALUES (
            $1, $2, 'setup-2fa@costmgr.local', 'owner',
            FALSE,
            NULL, NULL,
            0, NULL,
            NULL
        )
        ON CONFLICT (id) DO UPDATE SET
            tenant_id = EXCLUDED.tenant_id,
            email = EXCLUDED.email,
            role = EXCLUDED.role,
            twofa_enabled = EXCLUDED.twofa_enabled,
            totp_secret = EXCLUDED.totp_secret,
            totp_enabled_at = EXCLUDED.totp_enabled_at,
            totp_failed_attempts = EXCLUDED.totp_failed_attempts,
            totp_lockout_until = EXCLUDED.totp_lockout_until,
            totp_recovery_codes_hash = EXCLUDED.totp_recovery_codes_hash
        """,
        DEV_USER_SETUP_ID,
        DEV_TENANT_ID,
    )


# ── Epic 29+ m12-3 deletion scenario seeds (cj-278c wire) ─────
async def _reset_tenant_to_active(conn: asyncpg.Connection) -> None:
    """Return DEV_TENANT_ID to a clean `status='active'` pre-state.

    Shared by Stories 29.11 and 29.12: both ACs ask for exactly
    `(tenant_id, status='active')` and nothing more, because the flow
    under test is the *transition* the operator drives through the UI.

    Every deletion column is cleared as well, so a re-run after a prior
    deletion E2E leaves no half-deleted residue. `tenants` carries no
    append-only trigger (unlike `audit_logs` / `deletion_consents`), so
    a plain UPDATE is legal here.
    """
    await conn.execute(
        """
        UPDATE tenants
           SET status = 'active',
               deletion_requested_at = NULL,
               deletion_requested_by_user_id = NULL,
               deletion_consent_id = NULL,
               deletion_scheduled_for = NULL,
               deletion_anonymized_at = NULL,
               deleted_at = NULL
         WHERE id = $1
        """,
        DEV_TENANT_ID,
    )


async def _seed_pending_deletion_tenant(
    conn: asyncpg.Connection,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    membership_id: uuid.UUID,
    tenant_name: str,
    email: str,
    industry: str,
    days_remaining: int,
    audit_consent_id: uuid.UUID,
    audit_requested_id: uuid.UUID,
) -> None:
    """Seed one self-contained `status='pending_deletion'` tenant.

    Shared by Stories 29.13 (15 days left) and 29.14 (0 days left, i.e.
    hard-delete eligible). The grace window is expressed the way the
    schema actually models it (alembic 0025):

        deletion_requested_at = NOW() - (30 - days_remaining) days
        deletion_scheduled_for = NOW() + days_remaining days

    `tenants.deletion_requested_by_user_id` REFERENCES users(id) while
    `users.tenant_id` REFERENCES tenants(id) — a cycle. Broken by
    inserting the tenant with a NULL requester, then the user, then
    UPDATEing the requester back onto the tenant.

    `deletion_consent_id` is left NULL on purpose: `deletion_consents`
    requires `encrypted_consent_text BYTEA NOT NULL` (AES-256-GCM under
    AAD b"deletion_consent"), and dev_seed.py runs in CI without
    `COSTMGR_AT_REST_KEY_V1`, so any ciphertext written here would be
    undecryptable at API runtime. Same honest limitation cj-278b hit
    with `users.totp_secret` — cj-280 retro scope.
    """
    # 1. tenant, requester still NULL (FK cycle).
    await conn.execute(
        """
        INSERT INTO tenants (id, name, industry, status)
        VALUES ($1, $2, $3, 'pending_deletion')
        ON CONFLICT (id) DO UPDATE
            SET name = EXCLUDED.name,
                industry = EXCLUDED.industry,
                status = EXCLUDED.status,
                deletion_anonymized_at = NULL,
                deleted_at = NULL
        """,
        tenant_id,
        tenant_name,
        industry,
    )

    # 2. requester user (email is NOT NULL UNIQUE — alembic 0001:91).
    await conn.execute(
        """
        INSERT INTO users (id, tenant_id, email, role)
        VALUES ($1, $2, $3, 'owner')
        ON CONFLICT (id) DO UPDATE
            SET tenant_id = EXCLUDED.tenant_id,
                email = EXCLUDED.email,
                role = EXCLUDED.role
        """,
        user_id,
        tenant_id,
        email,
    )

    await conn.execute(
        """
        INSERT INTO tenant_memberships (id, tenant_id, user_id, role)
        VALUES ($1, $2, $3, 'owner')
        ON CONFLICT (tenant_id, user_id) DO UPDATE
            SET role = EXCLUDED.role
        """,
        membership_id,
        tenant_id,
        user_id,
    )

    await conn.execute(
        """
        INSERT INTO tenant_settings (tenant_id)
        VALUES ($1)
        ON CONFLICT (tenant_id) DO NOTHING
        """,
        tenant_id,
    )

    # 3. close the FK cycle + anchor the 30-day retention window.
    elapsed_days = DELETION_RETENTION_DAYS - days_remaining
    await conn.execute(
        """
        UPDATE tenants
           SET deletion_requested_by_user_id = $2,
               deletion_requested_at = NOW() - make_interval(days => $3::int),
               deletion_scheduled_for = NOW() + make_interval(days => $4::int)
         WHERE id = $1
        """,
        tenant_id,
        user_id,
        elapsed_days,
        days_remaining,
    )

    # 4. the two audit rows the real request_deletion() emits, in the
    #    same order (account_deletion_service.py:393-413). ON CONFLICT
    #    DO NOTHING — audit_logs forbids UPDATE (AD-2 append-only).
    for audit_id, action in (
        (audit_consent_id, ACTION_DELETION_CONSENT_GIVEN),
        (audit_requested_id, ACTION_DELETION_REQUESTED),
    ):
        await conn.execute(
            """
            INSERT INTO audit_logs (
                id, tenant_id, actor_id, action,
                target_table, target_id, reason, payload, occurred_at
            )
            VALUES (
                $1, $2, $3, $4,
                $5, $2, 'cj-278c Epic 29+ deletion scenario seed', $6::jsonb,
                NOW() - make_interval(days => $7::int)
            )
            ON CONFLICT (id) DO NOTHING
            """,
            audit_id,
            tenant_id,
            user_id,
            action,
            AUDIT_TARGET_TABLE_ACCOUNT_DELETION,
            json.dumps({"seeded_by": "dev_seed.py", "sprint": "cj-278c"}),
            elapsed_days,
        )


async def _seed_deletion_consent(conn: asyncpg.Connection) -> None:
    """Story 29.11 — put DEV_TENANT_ID in `status='active'` so the
    operator can open the deletion consent modal from a clean state.

    Spec drifts logged for cj-280 retro:
      ① AC names a tenant `TEN-ACTIVE`. This seed reuses DEV_TENANT_ID
        instead, because the dev JWT's `app_metadata.tenant_id` points
        there — a freshly-named tenant would not be reachable by the
        E2E session at all.
      ② AC requires `data-testid="delete-submit"` on the submit button.
        No such testid exists anywhere in the web app; the shipped
        modal exposes `id="deletion-consent"` / `id="deletion-totp"`
        and the live specs select the submit button by its accessible
        name (`/삭제 요청/`). Seed cannot supply a testid — this is a
        component change, cj-280 retro scope.
      ③ AC quotes the modal string "데이터 보관일수: 30일 / 30일 후
        완전 삭제 / 동의 체크 필수". The shipped consent template is
        "본인은 데이터 보존 기간 (30일) 및 삭제 시점을 이해했으며
        동의합니다" (account_deletion.py:78-80). The 30-day window
        agrees; the wording does not.
    """
    await _reset_tenant_to_active(conn)


async def _seed_deletion_audit(conn: asyncpg.Connection) -> None:
    """Story 29.12 — same clean `status='active'` pre-state as 29.11.

    The AC is about what the *transition* writes (status flips to
    `pending_deletion`, two new audit rows appear), so the seed's whole
    job is to guarantee the starting state. Nothing is pre-inserted
    into `audit_logs`: doing so would mask the very rows under test.

    Spec drifts logged for cj-280 retro:
      ① AC says `audit_logs.event_type`. The column is `action`
        (alembic 0001:146) and carries no CHECK constraint.
      ② AC says `actor` / `ts`. The columns are `actor_id` and
        `occurred_at` (alembic 0001:145,151).
      ③ AC expects `event_type='consent_checked'`. The backend emits
        `deletion_consent_given` (account_deletion.py:48). The second
        row, `deletion_requested`, matches the AC exactly.
    """
    await _reset_tenant_to_active(conn)


async def _seed_deletion_restore(conn: asyncpg.Connection) -> None:
    """Story 29.13 — a tenant sitting in `pending_deletion` with 15 of
    its 30 grace days left, so [취소하기] can revert it to `active`.

    Spec drifts logged for cj-280 retro:
      ① AC says `grace_period_remaining=15d`. No such column exists;
        the schema anchors the window on `deletion_scheduled_for`
        (alembic 0025), so 15 days remaining is seeded as
        `deletion_scheduled_for = NOW() + 15 days`.
      ② AC expects audit `event_type='deletion_restored'`. The backend
        emits `deletion_cancelled` (account_deletion.py:49).
      ③ AC labels the button "해지 취소"; the shipped UI renders
        "취소하기" (m12-3-deletion-cancel.spec.ts:92).
    """
    await _seed_pending_deletion_tenant(
        conn,
        tenant_id=DEV_TENANT_DELETION_PENDING_ID,
        user_id=DEV_USER_DELETION_PENDING_ID,
        membership_id=DEV_MEMBERSHIP_DELETION_PENDING_ID,
        tenant_name="해지 대기 테넌트 (15일 남음)",
        email="deletion-pending@costmgr.local",
        industry=DEFAULT_INDUSTRY,
        days_remaining=15,
        audit_consent_id=DEV_AUDIT_DEL_PENDING_CONSENT_ID,
        audit_requested_id=DEV_AUDIT_DEL_PENDING_REQUESTED_ID,
    )


async def _seed_deletion_hard_delete(conn: asyncpg.Connection) -> None:
    """Story 29.14 — a tenant whose 30-day grace window has run out
    (`deletion_scheduled_for = NOW()`), i.e. eligible for the daily
    hard-delete cron, with its prior audit trail already on record.

    The point of the story is that `audit_logs` *survives* the tenant
    row. It does: `audit_logs.tenant_id` is deliberately NOT a foreign
    key at the DB level (alembic 0001:131-139 spells out the reason —
    compliance retention per AD-2), so a hard delete cannot cascade
    them away.

    Spec drifts logged for cj-280 retro:
      ① AC says `grace_period_remaining=0d, mock_hard_delete=true`.
        Neither is a column; 0 days left is seeded as
        `deletion_scheduled_for = NOW()`, and the mock-vs-real choice
        belongs to the test, not the schema.
      ② AC expects a `deletion_completed` row. The backend emits
        `tenant_hard_deleted` (account_deletion.py:51). It is NOT
        seeded here — that row is the *outcome* under test, and
        pre-writing it would fake the assertion.
      ③ AC expects `archived_at` on the rows. The column exists
        (alembic 0040) but is written by the retention job, so this
        seed leaves it NULL rather than backdating it.
    """
    await _seed_pending_deletion_tenant(
        conn,
        tenant_id=DEV_TENANT_DELETION_EXPIRED_ID,
        user_id=DEV_USER_DELETION_EXPIRED_ID,
        membership_id=DEV_MEMBERSHIP_DELETION_EXPIRED_ID,
        tenant_name="해지 유예 만료 테넌트 (0일 남음)",
        email="deletion-expired@costmgr.local",
        industry=DEFAULT_INDUSTRY,
        days_remaining=0,
        audit_consent_id=DEV_AUDIT_DEL_EXPIRED_CONSENT_ID,
        audit_requested_id=DEV_AUDIT_DEL_EXPIRED_REQUESTED_ID,
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
        choices=[
            "closing_guard_negative",
            "snapshot_persisted",
            "close_sequence_partial",
            "reversal_input",
            "reversal_cache_invalidation",
            "reopen_audit",
            "two_factor_challenge",
            "two_factor_lockout",
            "two_factor_recovery",
            "two_factor_setup",
            "deletion_consent",
            "deletion_audit",
            "deletion_restore",
            "deletion_hard_delete",
            "all",
        ],
        default=None,
        help=(
            "cj-276 (Epic 29+ wire) + cj-278a (Epic 29+ P1 m11) + cj-278b "
            "(Epic 29+ P1 m12-2FA) + cj-278c (Epic 29+ P1 m12-3 deletion): "
            "optional business-data scenario seed "
            "beyond identity. Use 'closing_guard_negative' for Story 29.1 "
            "NEGATIVE_CLOSING_PERIOD fixture, 'snapshot_persisted' for "
            "Story 29.3 fiscal_period_snapshots row, 'close_sequence_partial' "
            "for Story 29.2 partial close fixture, 'reversal_input' for "
            "Story 29.4 reversal seed, 'reversal_cache_invalidation' for "
            "Story 29.5 AD-25 cache seed, 'reopen_audit' for Story 29.6 "
            "reopen audit seed, 'two_factor_challenge' for Story 29.7 2FA "
            "challenge fixture (totp_enabled_at IS NULL), 'two_factor_lockout' "
            "for Story 29.8 2FA lockout fixture (totp_failed_attempts=4), "
            "'two_factor_recovery' for Story 29.9 2FA recovery fixture "
            "(recovery_codes_remaining=3), 'two_factor_setup' for Story 29.10 "
            "2FA setup fixture (totp_enabled_at IS NULL), 'deletion_consent' "
            "for Story 29.11 active-tenant consent-modal fixture, "
            "'deletion_audit' for Story 29.12 active-tenant audit fixture, "
            "'deletion_restore' for Story 29.13 pending_deletion fixture with "
            "15 grace days left, 'deletion_hard_delete' for Story 29.14 "
            "pending_deletion fixture with 0 grace days left, or 'all' for "
            "all 14."
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
            # cj-278a (Epic 29+ P1 m11): 4 NEW m11 scenario seeds.
            if args.scenario in ("close_sequence_partial", "all"):
                await _seed_close_sequence_partial(conn)
            if args.scenario in ("reversal_input", "all"):
                await _seed_reversal_input(conn)
            if args.scenario in ("reversal_cache_invalidation", "all"):
                await _seed_reversal_cache_invalidation(conn)
            if args.scenario in ("reopen_audit", "all"):
                await _seed_reopen_audit(conn)
            # cj-278b (Epic 29+ P1 m12-2FA): 4 NEW m12-2FA scenario seeds.
            if args.scenario in ("two_factor_challenge", "all"):
                await _seed_two_factor_challenge(conn)
            if args.scenario in ("two_factor_lockout", "all"):
                await _seed_two_factor_lockout(conn)
            if args.scenario in ("two_factor_recovery", "all"):
                await _seed_two_factor_recovery(conn)
            if args.scenario in ("two_factor_setup", "all"):
                await _seed_two_factor_setup(conn)
            # cj-278c (Epic 29+ P1 m12-3 deletion): 4 NEW deletion seeds.
            # 29.11/29.12 reset DEV_TENANT_ID to 'active'; 29.13/29.14
            # own separate tenants so the 'pending_deletion' state never
            # leaks into the other 12 scenarios under `--scenario all`.
            if args.scenario in ("deletion_consent", "all"):
                await _seed_deletion_consent(conn)
            if args.scenario in ("deletion_audit", "all"):
                await _seed_deletion_audit(conn)
            if args.scenario in ("deletion_restore", "all"):
                await _seed_deletion_restore(conn)
            if args.scenario in ("deletion_hard_delete", "all"):
                await _seed_deletion_hard_delete(conn)
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
