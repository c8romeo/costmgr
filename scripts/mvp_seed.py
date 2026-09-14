"""scripts.mvp_seed — MVP 로컬 시연용 seed data (실제 schema 매칭).

사용법:
    uv run python scripts/mvp_seed.py
    (DATABASE_URL 환경변수 또는 .mvp_local_db_url 파일에서 자동 로드)

생성 데이터:
    - 1 tenant + 1 owner user (tenant_memberships owner role)
    - 5 products (raw_material + sub_assembly + finished_good)
    - 2 bom_lines (parent=PROD-005, child=PROD-004/PROD-003)
    - 1 monthly_input_period (2026-08) + 2 monthly_input_rows

Sprint 0 (cj-style N+8, 2026-09-13 KST, D-1) — actual alembic schema 적용 후.
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from pathlib import Path

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
OWNER_USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
PERIOD_KEY = "2026-08"


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    project_root = Path(__file__).parent.parent
    dburl_file = project_root / ".mvp_local_db_url"
    if dburl_file.exists():
        return dburl_file.read_text().strip()
    print("[mvp_seed] ERROR: DATABASE_URL not set")
    sys.exit(1)


async def main() -> int:
    import asyncpg
    db_url = _database_url()
    sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    print(f"[mvp_seed] connecting to {sync_url[:60]}...")

    conn = await asyncpg.connect(sync_url)
    try:
        # Sprint 0 (cj-style N+8) — RLS bypass via SET LOCAL service_role.
        # Production Supabase also routes admin operations via service_role.
        await conn.execute("SET LOCAL ROLE service_role")

        # 1. Tenant
        print("[mvp_seed] creating tenant...")
        await conn.execute(
            """
            INSERT INTO tenants (id, name, industry, slug, status, created_at)
            VALUES ($1, $2, $3, $4, $5, now())
            ON CONFLICT (id) DO NOTHING
            """,
            TENANT_ID,
            "Demo Manufacturing Co.",
            "manufacturing",
            "demo",
            "active",
        )

        # 2. Owner user (no display_name column)
        print("[mvp_seed] creating owner user...")
        await conn.execute(
            """
            INSERT INTO users (id, tenant_id, email, role, twofa_enabled, created_at)
            VALUES ($1, $2, $3, $4, $5, now())
            ON CONFLICT (id) DO NOTHING
            """,
            OWNER_USER_ID,
            TENANT_ID,
            "demo@costmgr.local",
            "owner",
            False,
        )

        # 3. Membership (tenant_memberships) — idempotent
        print("[mvp_seed] creating owner membership...")
        await conn.execute(
            """
            INSERT INTO tenant_memberships (id, tenant_id, user_id, role, joined_at)
            VALUES ($1, $2, $3, $4, now())
            ON CONFLICT (tenant_id, user_id) DO NOTHING
            """,
            uuid.uuid4(),
            TENANT_ID,
            OWNER_USER_ID,
            "owner",
        )

        # 4. Products (5) — idempotent
        print("[mvp_seed] upserting 5 products...")
        # product_type CHECK constraint: product/semi_product/material/goods/service
        products = [
            ("PROD-001", "Steel Sheet A",        "material",      1000),
            ("PROD-002", "Aluminum Bar B",       "material",       500),
            ("PROD-003", "Bolt M8",              "semi_product",    50),
            ("PROD-004", "Housing Unit",         "semi_product",   200),
            ("PROD-005", "Final Widget",         "goods",         5000),
        ]
        for code, name, ptype, unit_cost in products:
            await conn.execute(
                """
                INSERT INTO products (id, tenant_id, product_type, code, name, unit, unit_cost_krw, is_active, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, true, now())
                ON CONFLICT (tenant_id, code) DO UPDATE SET updated_at = now()
                """,
                uuid.uuid4(),
                TENANT_ID,
                ptype,
                code,
                name,
                "EA",
                unit_cost,
            )
        # Re-fetch by code (idempotent: returns existing ids on re-run)
        product_ids: dict[str, uuid.UUID] = {}
        rows = await conn.fetch(
            "SELECT code, id FROM products WHERE tenant_id = $1", TENANT_ID
        )
        for r in rows:
            product_ids[r["code"]] = r["id"]
        print(f"[mvp_seed] product_ids: {product_ids}")

        # 5. Monthly input period — unique (tenant_id, period_key, baseline_revision)
        print(f"[mvp_seed] creating monthly input period {PERIOD_KEY}...")
        period_id = uuid.uuid4()
        await conn.execute(
            """
            INSERT INTO monthly_input_periods (period_id, tenant_id, period_key, mode, status, baseline_revision, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, now())
            ON CONFLICT (tenant_id, period_key, baseline_revision) DO NOTHING
            """,
            period_id,
            TENANT_ID,
            PERIOD_KEY,
            "month_total",
            "open",
            1,
        )
        # Re-fetch actual period_id (idempotent)
        actual_period_id = await conn.fetchval(
            "SELECT period_id FROM monthly_input_periods WHERE tenant_id=$1 AND period_key=$2 LIMIT 1",
            TENANT_ID, PERIOD_KEY,
        )
        if actual_period_id is None:
            raise RuntimeError("period not found after upsert")
        period_id = actual_period_id

        # 6. Monthly input rows (2 rows for raw materials)
        # Idempotent via uq_monthly_input_rows_natural (tenant_id, period_id, stream, product_id, day_no)
        # day_no NULL → COALESCE(0). delete-then-insert is simpler and matches seed intent.
        await conn.execute(
            "DELETE FROM monthly_input_rows WHERE tenant_id=$1 AND period_id=$2",
            TENANT_ID, period_id,
        )
        print("[mvp_seed] creating monthly input rows...")
        await conn.execute(
            """
            INSERT INTO monthly_input_rows (row_id, tenant_id, period_id, stream, product_id, qty, unit_price_krw, amount_krw, created_via, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, now())
            """,
            uuid.uuid4(),
            TENANT_ID,
            period_id,
            "purchases",
            product_ids["PROD-001"],
            100,
            1000,
            100000,
            "manual",
        )
        await conn.execute(
            """
            INSERT INTO monthly_input_rows (row_id, tenant_id, period_id, stream, product_id, qty, unit_price_krw, amount_krw, created_via, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, now())
            """,
            uuid.uuid4(),
            TENANT_ID,
            period_id,
            "purchases",
            product_ids["PROD-002"],
            200,
            500,
            100000,
            "manual",
        )

        # 7. BOM lines (PROD-005 = PROD-004 * 1 + PROD-003 * 4)
        # Idempotent: delete existing then insert
        await conn.execute(
            "DELETE FROM bom_lines WHERE tenant_id=$1 AND parent_product_id=$2",
            TENANT_ID, product_ids["PROD-005"],
        )
        print("[mvp_seed] creating BOM lines...")
        await conn.execute(
            """
            INSERT INTO bom_lines (id, tenant_id, parent_product_id, child_product_id, ratio, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, now(), now())
            """,
            uuid.uuid4(),
            TENANT_ID,
            product_ids["PROD-005"],
            product_ids["PROD-004"],
            1,
        )
        await conn.execute(
            """
            INSERT INTO bom_lines (id, tenant_id, parent_product_id, child_product_id, ratio, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, now(), now())
            """,
            uuid.uuid4(),
            TENANT_ID,
            product_ids["PROD-005"],
            product_ids["PROD-003"],
            4,
        )

        # 8. tenant_settings — D-Day MVP demo seed (cj-style N+13)
        # Insert with onboarding.industry = "manufacturing" so the dashboard
        # renders the populated industry menu (15 items for manufacturing per
        # packages/services/m0_onboarding/industry_menu.py). Without this row,
        # the dev bypass synthesizes a response with settings_version=0, but
        # the frontend MenuContext also requires accessToken to fetch — see
        # cj-style N+13 frontend fix.
        print("[mvp_seed] creating tenant_settings (manufacturing)...")
        await conn.execute(
            """
            INSERT INTO tenant_settings (
                tenant_id, settings_version, onboarding, baseline, abc, ai, payroll, updated_at
            )
            VALUES (
                $1, 1,
                jsonb_build_object(
                    'industry', 'manufacturing',
                    'selected_at', to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
                    'is_initial', true
                ),
                '{}'::jsonb,
                '{}'::jsonb,
                '{}'::jsonb,
                '{}'::jsonb,
                now()
            )
            ON CONFLICT (tenant_id) DO UPDATE SET
                settings_version = EXCLUDED.settings_version + 1,
                onboarding = EXCLUDED.onboarding,
                updated_at = now()
            """,
            TENANT_ID,
        )

        # Verify
        tenant_count = await conn.fetchval("SELECT COUNT(*) FROM tenants WHERE id = $1", TENANT_ID)
        product_count = await conn.fetchval("SELECT COUNT(*) FROM products WHERE tenant_id = $1", TENANT_ID)
        row_count = await conn.fetchval("SELECT COUNT(*) FROM monthly_input_rows WHERE tenant_id = $1", TENANT_ID)
        bom_count = await conn.fetchval("SELECT COUNT(*) FROM bom_lines WHERE tenant_id = $1", TENANT_ID)
        member_count = await conn.fetchval("SELECT COUNT(*) FROM tenant_memberships WHERE tenant_id = $1", TENANT_ID)
        settings_count = await conn.fetchval("SELECT COUNT(*) FROM tenant_settings WHERE tenant_id = $1", TENANT_ID)
        settings_industry = await conn.fetchval(
            "SELECT onboarding->>'industry' FROM tenant_settings WHERE tenant_id = $1", TENANT_ID
        )

        print("[mvp_seed] DONE - verify:")
        print(f"  tenants: {tenant_count}")
        print(f"  users: {member_count}")
        print(f"  products: {product_count}")
        print(f"  bom_lines: {bom_count}")
        print(f"  monthly_input_rows: {row_count}")
        print(f"  tenant_settings: {settings_count} (industry={settings_industry})")
        print(f"[mvp_seed] TENANT_ID = {TENANT_ID}")
        print("[mvp_seed] OWNER_EMAIL = demo@costmgr.local")
        return 0
    except Exception as e:
        print(f"[mvp_seed] FAILED: {e!r}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await conn.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
