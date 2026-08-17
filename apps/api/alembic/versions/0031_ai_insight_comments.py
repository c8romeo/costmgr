"""Story 10.3 — ai_insight_comments table + AD-7 badge separation (cj-style 30번째 epic 연속).

Per AD-7 (ARCHITECTURE-SPINE.md §72-76 + master PRD §8.1 M10-(b) verbatim):
  "M10 NEVER writes confirmed_inputs. AI commentary is labeled
  `source_kind='ai_reference'`; deterministic template analysis is labeled
  `source_kind='auto_analysis'`. M10 attempts to write confirmed-input
  tables are denied and counted (target zero)."

Per F10.2-(a)~(d) verbatim (workspace canonical PRD lines 95-112):
  (a) `source_kind='auto_analysis'` → 파란 배지 '📊 자동 분석'
      `source_kind='ai_reference'`  → 보라 배지 '🤖 AI 참고(검증 필요)'
  (b) `source_kind` 미매칭 value → strict reject + 1행 counter increment
  (c) `auto_analysis` 의견 수정 시도 → denied + 동일 카운터 추적 (SM-3a)
  (d) 1-line ko-KR 메시지로 reject ("분석 의견 출처가 불분명합니다")

Per AD-25 (ARCHITECTURE-SPINE.md §296-301):
  cache key = (tenant_id, period_key, calculation_result_hash).

Schema changes:
- NEW TABLE `ai_insight_comments`:
    * comment_id        UUID PK DEFAULT gen_random_uuid()  (UUID v7, CR 1.1)
    * tenant_id         UUID NOT NULL FK → tenants(id) ON DELETE RESTRICT
                                                          (AD-3 RLS 정합)
    * period_key        VARCHAR(32) NOT NULL
                        (master PRD §V4 fiscal key format YYYY-MM,
                         AD-24 typed period-key namespaces)
    * calculation_result_hash VARCHAR(64) NOT NULL
                        (Epic 4 SHA-256 hex digest)
    * comment_kind      VARCHAR(32) NOT NULL CHECK IN
                        ('cost_reduction_candidate', 'anomaly_pattern',
                         'forecast', 'risk_warning', 'industry_benchmark')
                        (master PRD §12 + AD-15 SSOT)
    * source_kind       VARCHAR(32) NOT NULL CHECK
                        IN ('auto_analysis', 'ai_reference')
                        (AD-7 verbatim + 10-2 kernel SSOT 보존)
    * body_text         TEXT NOT NULL   (ko-KR string, master PRD §13.1)
    * evidence_ref      TEXT NULL       (master PRD §A11 evidence provenance)
    * generated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
- UNIQUE constraint `uq_ai_insight_comments_tenant_period_kind_hash`
  ON (tenant_id, period_key, comment_kind, calculation_result_hash)
  — AD-25 verbatim 3-tuple + per-kind row 정합 + idempotent INSERT.
- 3 NEW indexes:
    * idx_ai_insight_comments_tenant_period (cache lookup PRIMARY path)
    * idx_ai_insight_comments_calculation_hash (AD-25 key 3-tuple 정합)
    * idx_ai_insight_comments_source_kind (F10.2-(a) 분기 렌더링 PRIMARY path)
- AD-2 INSERT-only trigger EXTENSION: UPDATE/DELETE 시 audit_logs append
  (CR 1.1 audit-first invariant 정합 + F10.2-(c) auto_analysis read-only).
- COMMENT ON TABLE for AD-25 + AD-7 verbatim 명시.

Counter note (F10.2-(b)(c)): 별도 counter table 을 신설하지 않는다. 카운터는
`audit_logs` row count 로 derive 한다 (action IN
('ai_insight_cache_invalid_source_kind',
 'ai_insight_cache_auto_analysis_modify_denied')) — CR 1.1 audit-first verbatim
보존 + SM-3a "계산 결과 변경 시도 = 0건" 별도 추적 정합.

Down revision: 0030_ai_insight_cache.

NFR18 lock: column semantics captured in DB schema (NFR18 lock policy).
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0031_ai_insight_comments"
down_revision = "0030_ai_insight_cache"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Story 10.3 — AD-7 ai_insight_comments table + badge separation wire."""
    # ── 1. Create `ai_insight_comments` table ──────────────────
    op.execute(
        """
        CREATE TABLE ai_insight_comments (
            comment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL
                REFERENCES tenants(id) ON DELETE RESTRICT,
            period_key VARCHAR(32) NOT NULL,
            calculation_result_hash VARCHAR(64) NOT NULL,
            comment_kind VARCHAR(32) NOT NULL,
            source_kind VARCHAR(32) NOT NULL,
            body_text TEXT NOT NULL,
            evidence_ref TEXT NULL,
            generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "COMMENT ON TABLE ai_insight_comments IS "
        "'AD-25 + AD-7 verbatim AI insight comment table. "
        "Cache key = (tenant_id, period_key, calculation_result_hash). "
        "source_kind discriminator ''auto_analysis'' | ''ai_reference''. "
        "F10.2 (a)~(d) badge separation verbatim wire. "
        "Per (tenant, period, kind, hash) UNIQUE constraint. "
        "Source: master PRD §F10.2 + epics.md Story 10.3. NFR18 lock.'"
    )

    # ── 2. AD-25 verbatim 3-tuple + per-kind UNIQUE constraint ──
    op.execute(
        """
        ALTER TABLE ai_insight_comments
        ADD CONSTRAINT uq_ai_insight_comments_tenant_period_kind_hash
        UNIQUE (tenant_id, period_key, comment_kind, calculation_result_hash)
        """
    )

    # ── 3. CHECK constraints (master PRD §12 + AD-7 + AD-15 SSOT) ──
    op.execute(
        """
        ALTER TABLE ai_insight_comments
        ADD CONSTRAINT ck_ai_insight_comments_comment_kind
        CHECK (comment_kind IN ('cost_reduction_candidate', 'anomaly_pattern', 'forecast', 'risk_warning', 'industry_benchmark'))
        """
    )
    op.execute(
        """
        ALTER TABLE ai_insight_comments
        ADD CONSTRAINT ck_ai_insight_comments_source_kind
        CHECK (source_kind IN ('auto_analysis', 'ai_reference'))
        """
    )

    # ── 4. AD-24 typed period_key format check ────────────────
    op.execute(
        """
        ALTER TABLE ai_insight_comments
        ADD CONSTRAINT ck_ai_insight_comments_period_key_format
        CHECK (period_key ~ '^\\d{4}-(0[1-9]|1[0-2])$')
        """
    )

    # ── 5. 3 NEW indexes ───────────────────────────────────────
    op.execute(
        """
        CREATE INDEX idx_ai_insight_comments_tenant_period
        ON ai_insight_comments (tenant_id, period_key)
        """
    )
    op.execute(
        """
        CREATE INDEX idx_ai_insight_comments_calculation_hash
        ON ai_insight_comments (calculation_result_hash)
        """
    )
    op.execute(
        """
        CREATE INDEX idx_ai_insight_comments_source_kind
        ON ai_insight_comments (tenant_id, source_kind)
        """
    )

    # ── 6. AD-2 INSERT-only trigger (F10.2-(c) auto_analysis read-only) ──
    # CR 1.1 verbatim: "audit_logs INSERT BEFORE data mutation". Any UPDATE /
    # DELETE attempt is audited then rejected — this is the DB-level mirror of
    # the service-layer `AICommentImmutableAutoAnalysisError` guard.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION trg_ai_insight_comments_no_update_delete()
        RETURNS trigger AS $$
        BEGIN
            INSERT INTO audit_logs (
                audit_id, tenant_id, actor_id, action_class, target_id,
                reason, payload, occurred_at
            )
            VALUES (
                gen_random_uuid(),
                COALESCE(NEW.tenant_id, OLD.tenant_id),
                NULL,
                'ai_insight_cache_accessed',  -- ActionClass.AI_INSIGHT_CACHE_ACCESSED (category, not verb)
                COALESCE(NEW.comment_id, OLD.comment_id)::text,
                TG_OP || ' blocked by AD-2 INSERT-only invariant (F10.2-(c))',
                jsonb_build_object(
                    'op', TG_OP,
                    'comment_id', COALESCE(NEW.comment_id, OLD.comment_id),
                    'period_key', COALESCE(NEW.period_key, OLD.period_key),
                    'comment_kind', COALESCE(NEW.comment_kind, OLD.comment_kind),
                    'source_kind', COALESCE(NEW.source_kind, OLD.source_kind)
                ),
                NOW()
            );
            RAISE EXCEPTION 'ai_insight_comments is INSERT-only (AD-2) — % blocked', TG_OP
                USING ERRCODE = '40006';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_ai_insight_comments_update_block
        BEFORE UPDATE ON ai_insight_comments
        FOR EACH ROW
        EXECUTE FUNCTION trg_ai_insight_comments_no_update_delete()
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_ai_insight_comments_delete_block
        BEFORE DELETE ON ai_insight_comments
        FOR EACH ROW
        EXECUTE FUNCTION trg_ai_insight_comments_no_update_delete()
        """
    )


def downgrade() -> None:
    """Story 10.3 — drop ai_insight_comments table + triggers."""
    op.execute(
        "DROP TRIGGER IF EXISTS trg_ai_insight_comments_update_block ON ai_insight_comments"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS trg_ai_insight_comments_delete_block ON ai_insight_comments"
    )
    op.execute("DROP FUNCTION IF EXISTS trg_ai_insight_comments_no_update_delete()")
    op.execute("DROP TABLE IF EXISTS ai_insight_comments")
