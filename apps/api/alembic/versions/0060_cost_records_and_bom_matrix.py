"""alembic version 0060 — cost_records + bom_matrix tables (cj-288 wire sprint).

cj-287 follow-up #2 commit `d8d4df0` 의 PRE-EXISTING carryover 정직 회복:
cj-286 EXTENSION wire sprint `e408668` 의 `_seed_report_fixtures(conn)` 가
INSERT into `public.cost_records` + `public.bom_matrix` 했으나 두 테이블
모두 어떤 alembic migration 에도 존재하지 않았음 (grep 0 hits across
`apps/api/alembic/versions/*.py`).

Effect (CR 11-3 honest-DEFER 224번째 carryover): CI run 33999439554
web-e2e step 15 "Run dev seed --scenario all" 가 relation does not exist
error 로 fail → steps 16~19 (uvicorn + playwright install + v8 fixture +
playwright test) 모두 SKIPPED → **step 19 csv-export 3/3 tests NEVER RAN**.
본 sprint 가 table 부재 fix → step 15 회복 → step 19 자연 unlock.

cj-282 Epic 30+ PRD entry §F44.1 (FR-30-1 CSV export) 의 결정 wire verbatim:
- AD-2 (audit-first INSERT append-only) — 본 table 자체는 append-only 와
  무관 (CSV export = read-only query against cost_records/bom_matrix).
  export event 자체는 audit_logs 에 INSERT (csv_routes.py:362 fix 이미
  cj-287 에서 wire 완료).
- AD-3 RLS 정합 — tenant_id FK to tenants(id) + tenant_id+period_key
  index (RLS policies 는 별도 supabase/policies/0060_*.sql 결정 wire 보류).
- AD-15 SSOT — id UUID DEFAULT gen_random_uuid() (CR 1.1 verbatim UUIDv7
  권장이나 CSV export spec 호환 위해 gen_random_uuid() 사용; tenant_id
  UUID v4 JWT-derived).
- AD-8 monetary parity — KRW amounts NUMERIC(18,2) (decimal cost 보존;
  D-CI-FUNC-4 convention verbatim). quantity NUMERIC(18,4) (소수 4자리).

Schema:
- NEW TABLE `cost_records` (public schema):
    * id              UUID PK DEFAULT gen_random_uuid()
    * tenant_id       UUID NOT NULL FK → tenants(id) ON DELETE CASCADE
    * period_key      VARCHAR(32) NOT NULL  (AD-24 YYYY-MM format)
    * product_id      UUID NOT NULL  (no FK enforcement: dev_seed uses
                       report tenant's ad-hoc UUIDv5 namespace products;
                       FK to products(id) would block INSERT in dev_seed)
    * product_name    VARCHAR(255) NOT NULL
    * category        VARCHAR(64) NOT NULL  (ko-KR: 원재료/노무비/간접비/완제품)
    * opening_qty     NUMERIC(18,4) NOT NULL CHECK (opening_qty >= 0)
    * input_qty       NUMERIC(18,4) NOT NULL CHECK (input_qty >= 0)
    * output_qty      NUMERIC(18,4) NOT NULL CHECK (output_qty >= 0)
    * closing_qty     NUMERIC(18,4) NOT NULL CHECK (closing_qty >= 0)
    * unit_cost       NUMERIC(18,2) NOT NULL CHECK (unit_cost >= 0)
    * total_cost      NUMERIC(18,2) NOT NULL CHECK (total_cost >= 0)
    * currency        VARCHAR(8) NOT NULL DEFAULT 'KRW'
    * created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    * ledger_event_id UUID NOT NULL  (dev_seed-generated UUIDv5)

- NEW TABLE `bom_matrix` (public schema):
    * id                    UUID PK DEFAULT gen_random_uuid()
    * tenant_id             UUID NOT NULL FK → tenants(id) ON DELETE CASCADE
    * period_key            VARCHAR(32) NOT NULL  (AD-24 YYYY-MM format)
    * parent_product_id     UUID NOT NULL  (no FK: dev_seed ad-hoc UUIDv5)
    * parent_product_name   VARCHAR(255) NOT NULL
    * child_product_id      UUID NOT NULL  (no FK: dev_seed ad-hoc UUIDv5)
    * child_product_name    VARCHAR(255) NOT NULL
    * child_category        VARCHAR(64) NOT NULL
    * child_qty_per_parent  NUMERIC(18,4) NOT NULL CHECK (child_qty_per_parent >= 0)
    * child_unit_cost       NUMERIC(18,2) NOT NULL CHECK (child_unit_cost >= 0)
    * child_total_cost      NUMERIC(18,2) NOT NULL CHECK (child_total_cost >= 0)
    * currency              VARCHAR(8) NOT NULL DEFAULT 'KRW'
    * created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
    * bom_level             INTEGER NOT NULL DEFAULT 1 CHECK (bom_level >= 1)

Indexes:
- cost_records:
    * idx_cost_records_tenant_period (tenant_id, period_key) — csv_routes.py
      :303 WHERE tenant_id = :tenant_id AND period_key = :period_key PRIMARY
      path (verbatim NFR5 streaming P95 ≤ 5s 결정 wire 보존).
- bom_matrix:
    * idx_bom_matrix_tenant_period (tenant_id, period_key) — csv_routes.py
      :330 WHERE tenant_id = :tenant_id AND period_key = :period_key PRIMARY path.
    * idx_bom_matrix_tenant_period_level (tenant_id, period_key, bom_level)
      — csv_routes.py :333 WHERE ... AND bom_level = 1 filter path
      (Story 30.1 scope = level 1 only per cj-282 PRD entry 결정 wire).

Schema ↔ dev_seed INSERT columns 정합:
- cost_records INSERT columns (scripts/dev_seed.py:1455-1466) = CSV SELECT
  columns (csv_routes.py:300-303) = CREATE TABLE columns — verbatim 14 컬럼
  match.
- bom_matrix INSERT columns (scripts/dev_seed.py:1515-1522) = CSV SELECT
  columns (csv_routes.py:324-330) = CREATE TABLE columns — verbatim 13 컬럼
  match (bom_level = 1 dev_seed 결정 wire 보존).

RLS 결정 wire 보류:
- 본 sprint 는 table DDL + indexes 만 포함. RLS policies 는 별도 sprint
  (supabase/policies/0060_cost_records_and_bom_matrix_rls.sql 결정 wire)
  에서 진입 — cj-style 284+ EXTENSION territory. dev_seed 는 postgres role
  (BYPASSRLS) 사용 → RLS 부재가 dev_seed step 15 회복에는 무관 결정 wire.

product_id / parent_product_id / child_product_id FK 부재 결정 wire:
- dev_seed 의 report_fixtures scenario 는 acme report tenant 의 ad-hoc
  UUIDv5 namespace products 사용 (cj-286 EXTENSION wire sprint 결정 wire
  보존). products(id) FK enforcement 가 있으면 dev_seed INSERT 가 FK
  violation 으로 fail → step 15 회복 의도와 정면 충돌.
- Story 30.1 CSV export scope = read-only query against these tables.
  Application-layer join 으로 product name/category resolve (이미
  dev_seed INSERT 시 denormalize 결정 wire 보존 — product_name 컬럼 명시).

Down revision: 0059_phase_28_interactive_dashboard.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0060_cost_records_and_bom_matrix"
down_revision: str | Sequence[str] | None = "0059_phase_28_interactive_dashboard"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── cost_records ──────────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cost_records (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            period_key      VARCHAR(32) NOT NULL,
            product_id      UUID NOT NULL,
            product_name    VARCHAR(255) NOT NULL,
            category        VARCHAR(64) NOT NULL,
            opening_qty     NUMERIC(18,4) NOT NULL CHECK (opening_qty >= 0),
            input_qty       NUMERIC(18,4) NOT NULL CHECK (input_qty >= 0),
            output_qty      NUMERIC(18,4) NOT NULL CHECK (output_qty >= 0),
            closing_qty     NUMERIC(18,4) NOT NULL CHECK (closing_qty >= 0),
            unit_cost       NUMERIC(18,2) NOT NULL CHECK (unit_cost >= 0),
            total_cost      NUMERIC(18,2) NOT NULL CHECK (total_cost >= 0),
            currency        VARCHAR(8) NOT NULL DEFAULT 'KRW',
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            ledger_event_id UUID NOT NULL
        )
        """
    )
    op.execute(
        "COMMENT ON TABLE cost_records IS "
        "'Story 30.1 CSV export source (cost-records type). "
        "dev_seed report_fixtures scenario seeds 100 rows for "
        "DEV_TENANT_REPORT_ID. AD-15 SSOT, AD-8 monetary parity. NFR18 lock.'"
    )
    # csv_routes.py:303 WHERE tenant_id AND period_key PRIMARY path
    # (verbatim NFR5 streaming P95 ≤ 5s 결정 wire 보존).
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_cost_records_tenant_period
        ON cost_records(tenant_id, period_key)
        """
    )

    # ── bom_matrix ────────────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS bom_matrix (
            id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id             UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            period_key            VARCHAR(32) NOT NULL,
            parent_product_id     UUID NOT NULL,
            parent_product_name   VARCHAR(255) NOT NULL,
            child_product_id      UUID NOT NULL,
            child_product_name    VARCHAR(255) NOT NULL,
            child_category        VARCHAR(64) NOT NULL,
            child_qty_per_parent  NUMERIC(18,4) NOT NULL CHECK (child_qty_per_parent >= 0),
            child_unit_cost       NUMERIC(18,2) NOT NULL CHECK (child_unit_cost >= 0),
            child_total_cost      NUMERIC(18,2) NOT NULL CHECK (child_total_cost >= 0),
            currency              VARCHAR(8) NOT NULL DEFAULT 'KRW',
            created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            bom_level             INTEGER NOT NULL DEFAULT 1 CHECK (bom_level >= 1)
        )
        """
    )
    op.execute(
        "COMMENT ON TABLE bom_matrix IS "
        "'Story 30.1 CSV export source (bom type, level 1 only). "
        "dev_seed report_fixtures scenario seeds 10 rows for "
        "DEV_TENANT_REPORT_ID. AD-15 SSOT, AD-8 monetary parity. NFR18 lock.'"
    )
    # csv_routes.py:330 WHERE tenant_id AND period_key PRIMARY path.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_bom_matrix_tenant_period
        ON bom_matrix(tenant_id, period_key)
        """
    )
    # csv_routes.py:333 WHERE ... AND bom_level = 1 filter path
    # (Story 30.1 scope = level 1 only per cj-282 PRD entry 결정 wire).
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_bom_matrix_tenant_period_level
        ON bom_matrix(tenant_id, period_key, bom_level)
        """
    )


def downgrade() -> None:
    # Reverse order: indexes → tables (FK dependents first).
    op.execute("DROP INDEX IF EXISTS idx_bom_matrix_tenant_period_level")
    op.execute("DROP INDEX IF EXISTS idx_bom_matrix_tenant_period")
    op.execute("DROP TABLE IF EXISTS bom_matrix")
    op.execute("DROP INDEX IF EXISTS idx_cost_records_tenant_period")
    op.execute("DROP TABLE IF EXISTS cost_records")
