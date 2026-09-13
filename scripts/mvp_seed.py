"""scripts.mvp_seed — MVP 로컬 시연용 seed data.

사용법:
    uv run python scripts/mvp_seed.py
    (DATABASE_URL 환경변수 또는 .mvp_local_db_url 파일에서 자동 로드)

생성 데이터:
    - 1 tenant (id=11111111-1111-1111-1111-111111111111)
    - 1 owner user (auth_user_id placeholder, since local stub)
    - 5 products (item_master)
    - 1 BOM (bom_matrix)
    - 1 month data (monthly_input)

Sprint 0 (cj-style N+7, 2026-09-13 KST, D-1).
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from pathlib import Path

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
OWNER_USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    project_root = Path(__file__).parent.parent
    dburl_file = project_root / ".mvp_local_db_url"
    if dburl_file.exists():
        return dburl_file.read_text().strip()
    print("[mvp_seed] ERROR: DATABASE_URL not set and .mvp_local_db_url missing")
    sys.exit(1)


async def main() -> int:
    import asyncpg
    db_url = _database_url()
    sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    print(f"[mvp_seed] connecting to {sync_url[:60]}...")

    conn = await asyncpg.connect(sync_url)
    try:
        # 1. Tenant
        print("[mvp_seed] creating tenant...")
        await conn.execute(
            """
            INSERT INTO tenants (id, name, industry, slug, created_at)
            VALUES ($1, $2, $3, $4, now())
            ON CONFLICT (id) DO NOTHING
            """,
            TENANT_ID,
            "Demo Manufacturing Co.",
            "manufacturing",
            "demo",
        )

        # 2. Owner user (users table)
        print("[mvp_seed] creating owner user...")
        await conn.execute(
            """
            INSERT INTO users (id, email, display_name, created_at)
            VALUES ($1, $2, $3, now())
            ON CONFLICT (id) DO NOTHING
            """,
            OWNER_USER_ID,
            "demo@costmgr.local",
            "Demo Owner",
        )

        # 3. Membership (tenant_users)
        print("[mvp_seed] creating owner membership...")
        await conn.execute(
            """
            INSERT INTO tenant_users (tenant_id, user_id, role, created_at)
            VALUES ($1, $2, $3, now())
            ON CONFLICT (tenant_id, user_id) DO NOTHING
            """,
            TENANT_ID,
            OWNER_USER_ID,
            "owner",
        )

        # 4. Products (item_master)
        print("[mvp_seed] creating 5 products...")
        products = [
            ("PROD-001", "Steel Sheet A", "raw_material", 1000),
            ("PROD-002", "Aluminum Bar B", "raw_material", 500),
            ("PROD-003", "Bolt M8", "sub_assembly", 50),
            ("PROD-004", "Housing Unit", "sub_assembly", 200),
            ("PROD-005", "Final Widget", "finished_good", 5000),
        ]
        for code, name, ptype, unit_cost in products:
            await conn.execute(
                """
                INSERT INTO item_master (id, tenant_id, code, name, type, unit_cost, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, now())
                ON CONFLICT (tenant_id, code) DO NOTHING
                """,
                uuid.uuid4(),
                TENANT_ID,
                code,
                name,
                ptype,
                unit_cost,
            )

        # 5. BOM (one BOM for Final Widget using sub-assemblies)
        print("[mvp_seed] creating BOM for Final Widget...")
        await conn.execute(
            """
            INSERT INTO bom_matrix (id, tenant_id, parent_product_code, child_product_code, quantity, created_at)
            VALUES ($1, $2, $3, $4, $5, now())
            ON CONFLICT (tenant_id, parent_product_code, child_product_code) DO NOTHING
            """,
            uuid.uuid4(),
            TENANT_ID,
            "PROD-005",
            "PROD-004",
            1,
        )
        await conn.execute(
            """
            INSERT INTO bom_matrix (id, tenant_id, parent_product_code, child_product_code, quantity, created_at)
            VALUES ($1, $2, $3, $4, $5, now())
            ON CONFLICT (tenant_id, parent_product_code, child_product_code) DO NOTHING
            """,
            uuid.uuid4(),
            TENANT_ID,
            "PROD-005",
            "PROD-003",
            4,
        )

        # 6. Monthly input (1 month of demo data)
        print("[mvp_seed] creating monthly input for 2026-08...")
        await conn.execute(
            """
            INSERT INTO monthly_input (id, tenant_id, period, product_code, quantity, unit_cost, total_cost, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, now())
            ON CONFLICT (tenant_id, period, product_code) DO NOTHING
            """,
            uuid.uuid4(),
            TENANT_ID,
            "2026-08",
            "PROD-001",
            100,
            1000,
            100000,
        )
        await conn.execute(
            """
            INSERT INTO monthly_input (id, tenant_id, period, product_code, quantity, unit_cost, total_cost, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, now())
            ON CONFLICT (tenant_id, period, product_code) DO NOTHING
            """,
            uuid.uuid4(),
            TENANT_ID,
            "2026-08",
            "PROD-002",
            200,
            500,
            100000,
        )

        print("[mvp_seed] DONE — 1 tenant + 1 owner + 5 products + 1 BOM + 1 month data")
        print(f"[mvp_seed] TENANT_ID = {TENANT_ID}")
        print(f"[mvp_seed] OWNER_EMAIL = demo@costmgr.local")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
