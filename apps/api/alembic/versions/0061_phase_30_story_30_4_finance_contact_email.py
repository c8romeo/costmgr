"""alembic version 0061 — tenants.finance_contact_email column ADD (cj-300 wire sprint).

cj-300 wire sprint (cj-style 302번째 epic 연속 정직 회복 source+docs atomic
single sprint) — Story 30.4 Scheduled reports (FR-30-4) §F30.4-2 verbatim.

PRD §F30.4-2 — finance_contact_email column EXTENSION 결정 wire:
- ADD COLUMN `tenants.finance_contact_email VARCHAR(255) NULL`
- NFR4 PII minimization — finance_contact_email redact pattern
- RLS policy EXTENSION — tenant_id selector verbatim (CR 0-2 RLS)
- Null fallback 결정 wire — finance_contact_email = NULL 인 tenant 의
  경우 default admin email 발송 (audit log INSERT path
  `admin_fallback_dispatched`).

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation. 기존
  `tenants` 테이블의 RLS policy 가 자동으로 새 column 에도 적용
  (column-level RLS 결정 wire 보류 — Phase 30.5+ EXTENSION).
- CR 1-1 audit-first INSERT append-only — 본 migration 은 schema
  변경만, audit row emission 없음 (cj-299 email service 와 다른
  category).
- CR 9-6 commit message discipline — file-based commit-msg
  (`commit-msg-cj-300wire.txt`) 결정 wire 진입.
- CR 11-3 honest-DEFER 244번째 — cj-300 entry 의 243번째 + 본
  migration 의 244번째 epic 연속 정직 회복 결정 wire.
- CR 12-5 D-14 typed exception envelope verbatim — alembic migration
  실패 시 `ScheduledReportAlembicMigrationError` envelope 결정 wire
  보존.
- AD-3 production tenant isolation 8 NEW RLS policies (cj-290 보존) —
  tenants 테이블 자체의 RLS 가 자동 적용 결정 wire.
- AD-14 stack pin EXTENSION 결정 wire 보존 — apscheduler 3.10.4 +
  pytz 2024.1 이미 pinned, [STACK BUMP] tag 불필요 결정 wire.
- AD-15 SSOT — VARCHAR(255) email format 결정 wire 보존.

Schema:
- ALTER TABLE `public.tenants` ADD COLUMN `finance_contact_email`
  VARCHAR(255) NULL DEFAULT NULL
- Index on `tenants.finance_contact_email` (operational — owner/admin
  lookup performance). RLS 결정 wire 보존 (tenant_id selector 자동
  적용).

Upgrade/Downgrade round-trip PASS:
- upgrade(): ADD COLUMN + CREATE INDEX
- downgrade(): DROP INDEX + DROP COLUMN

Verbatim mirror of 0060_cost_records_and_bom_matrix.py 결정 wire
(cj-288 wire sprint 보존).
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0061_phase_30_story_30_4_finance_contact_email"
down_revision = "0060_cost_records_and_bom_matrix"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """cj-300 wire sprint — tenants.finance_contact_email column ADD 결정 wire.

    AD-3 production tenant isolation 보존:
    - tenants 테이블 RLS policy (`tenant_id = current_setting('app.tenant_id')::uuid`)
      가 자동으로 새 column 에도 적용 (CR 0-2 RLS 결정 wire).
    - 별도 column-level RLS 불필요 (cj-290 RLS EXTENSION 결정 wire 보존).

    NFR4 PII minimization 결정 wire:
    - finance_contact_email 컬럼 자체는 일반 VARCHAR(255) (email format).
    - PII minimization 은 audit log INSERT path 에서 처리 (scheduled_reports.py
      `_redact_finance_email_for_audit()` 결정 wire).
    """
    # ADD COLUMN `finance_contact_email` to `tenants` table.
    op.add_column(
        "tenants",
        sa.Column(
            "finance_contact_email",
            sa.String(length=255),
            nullable=True,
            comment=(
                "재무 담당자 이메일 (NFR4 PII minimization — audit log 에서 "
                "redact, scheduled_reports.py `_redact_finance_email_for_audit` "
                "결정 wire 적용). NULL fallback: admin email 자동 발송 결정 wire "
                "(cj-300 wire sprint PRD §F30.4-2 verbatim)."
            ),
        ),
    )

    # Operational index on finance_contact_email (owner/admin lookup performance).
    # Tenant_id selector 자동 적용 (CR 0-2 RLS 보존).
    op.create_index(
        "idx_tenants_finance_contact_email",
        "tenants",
        ["finance_contact_email"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    """cj-300 wire sprint — tenants.finance_contact_email column DROP 결정 wire.

    Round-trip upgrade/downgrade PASS 결정 wire.
    """
    op.drop_index(
        "idx_tenants_finance_contact_email",
        table_name="tenants",
        if_exists=True,
    )
    op.drop_column("tenants", "finance_contact_email")
