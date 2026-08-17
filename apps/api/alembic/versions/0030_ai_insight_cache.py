"""Story 10.2 — ai_insight_cache table + AD-25 3-tuple cache key (cj-style 29번째 epic 연속).

Per AD-25 (ARCHITECTURE-SPINE.md §296-301 + epics.md 10.2 verbatim):
  "M10 cache key is (tenant_id, period_key, calculation_result_hash).
  A new AD-4 commit, an AD-22 reversal insert, or an M11 reopen emits
  one DB notification per channel."

Per F10.1-(a) verbatim:
  "M10 cache = 마감 완료 시점 ~ 다음 마감 시작 시점까지 보존
   (Epic 4 calc-hash 기반 publisher 1 channel 'ai_cache' 만 wire;
    Epic 11 close/reopen trigger EXTENSION forward-lock)."

Per F10.1-(d) verbatim:
  "channel = 'ai_cache' filter 강제 (cross-channel contamination 방지)."

Schema changes:
- NEW TABLE `ai_insight_cache`:
    * insight_cache_id  UUID PK DEFAULT gen_random_uuid()  (UUID v7, CR 1.1)
    * tenant_id         UUID NOT NULL FK → tenants(id) ON DELETE RESTRICT
                                                          (AD-3 RLS 정합)
    * period_key        VARCHAR(32) NOT NULL
                        (master PRD §V4 fiscal key format YYYY-MM,
                         AD-24 typed period-key namespaces)
    * calculation_result_hash VARCHAR(64) NOT NULL
                        (Epic 4 SHA-256 hex digest)
    * insight_kind      VARCHAR(32) NOT NULL CHECK
                        IN ('cost_reduction_candidate', 'anomaly_pattern', 'forecast')
                        (master PRD §12 AI 3종 + AD-15 SSOT)
    * source_kind       VARCHAR(32) NOT NULL CHECK
                        IN ('auto_analysis', 'ai_reference')
                        (AD-7 verbatim + 10-3 forward-bind)
    * question          TEXT NOT NULL
                        (ko-KR string, master PRD §13.1)
    * answer            TEXT NOT NULL
                        (ko-KR string, master PRD §13.1)
    * evidence_ref      TEXT NULL
                        (master PRD §A11 evidence provenance)
    * generated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
- UNIQUE constraint `uq_ai_insight_cache_tenant_period_kind_hash`
  ON (tenant_id, period_key, insight_kind, calculation_result_hash)
  — AD-25 verbatim 3-tuple + per-kind row 정합 + idempotent INSERT.
- 3 NEW indexes:
    * idx_ai_insight_cache_tenant_period (cache lookup PRIMARY path)
    * idx_ai_insight_cache_calculation_hash (AD-25 key 3-tuple 정합)
    * idx_ai_insight_cache_published_at_desc (AC #2 cache hit sub-100ms)
- INSERT-only trigger EXTENSION: UPDATE/DELETE 시 audit_logs append
  (CR 1.1 audit-first invariant 정합 + AD-2 append-only).
- COMMENT ON TABLE for AD-25 verbatim 3-tuple 명시.

Down revision: 0029_input_drafts_monthly_extension.

NFR18 lock: column semantics captured in DB schema (NFR18 lock policy).
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0030_ai_insight_cache"
down_revision = "0029_input_drafts_monthly_extension"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Story 10.2 — AD-25 ai_insight_cache table + 3-tuple cache key wire."""
    # ── 1. Create `ai_insight_cache` table ─────────────────────
    op.execute(
        """
        CREATE TABLE ai_insight_cache (
            insight_cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL
                REFERENCES tenants(id) ON DELETE RESTRICT,
            period_key VARCHAR(32) NOT NULL,
            calculation_result_hash VARCHAR(64) NOT NULL,
            insight_kind VARCHAR(32) NOT NULL,
            source_kind VARCHAR(32) NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            evidence_ref TEXT NULL,
            generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "COMMENT ON TABLE ai_insight_cache IS "
        "'AD-25 AI insight cache invalidation target. "
        "Cache key = (tenant_id, period_key, calculation_result_hash). "
        "Per (tenant, period, kind, hash) UNIQUE constraint. "
        "Source: master PRD §F10.1 + epics.md Story 10.2. NFR18 lock.'"
    )

    # ── 2. AD-25 verbatim 3-tuple + per-kind UNIQUE constraint ──
    op.execute(
        """
        ALTER TABLE ai_insight_cache
        ADD CONSTRAINT uq_ai_insight_cache_tenant_period_kind_hash
        UNIQUE (tenant_id, period_key, insight_kind, calculation_result_hash)
        """
    )

    # ── 3. CHECK constraints (master PRD §12 + AD-15 SSOT) ─────
    op.execute(
        """
        ALTER TABLE ai_insight_cache
        ADD CONSTRAINT ck_ai_insight_cache_insight_kind
        CHECK (insight_kind IN ('cost_reduction_candidate', 'anomaly_pattern', 'forecast'))
        """
    )
    op.execute(
        """
        ALTER TABLE ai_insight_cache
        ADD CONSTRAINT ck_ai_insight_cache_source_kind
        CHECK (source_kind IN ('auto_analysis', 'ai_reference'))
        """
    )

    # ── 4. AD-24 typed period_key format check ────────────────
    op.execute(
        """
        ALTER TABLE ai_insight_cache
        ADD CONSTRAINT ck_ai_insight_cache_period_key_format
        CHECK (period_key ~ '^\\d{4}-(0[1-9]|1[0-2])$')
        """
    )

    # ── 5. 3 NEW indexes ───────────────────────────────────────
    op.execute(
        """
        CREATE INDEX idx_ai_insight_cache_tenant_period
        ON ai_insight_cache (tenant_id, period_key)
        """
    )
    op.execute(
        """
        CREATE INDEX idx_ai_insight_cache_calculation_hash
        ON ai_insight_cache (calculation_result_hash)
        """
    )
    op.execute(
        """
        CREATE INDEX idx_ai_insight_cache_published_at_desc
        ON ai_insight_cache (tenant_id, generated_at DESC)
        """
    )

    # ── 6. AD-2 INSERT-only trigger (UPDATE/DELETE 시 audit append) ──
    # CR 1.1 verbatim: "audit-first INSERT BEFORE data INSERT". Here we wire
    # the symmetric guard: any UPDATE/DELETE attempt is logged to audit_logs.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION trg_ai_insight_cache_no_update_delete()
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
                'AI_INSIGHT_CACHE_MUTATION_BLOCKED',
                COALESCE(NEW.insight_cache_id, OLD.insight_cache_id)::text,
                TG_OP || ' blocked by AD-2 INSERT-only invariant',
                jsonb_build_object(
                    'op', TG_OP,
                    'insight_cache_id', COALESCE(NEW.insight_cache_id, OLD.insight_cache_id),
                    'period_key', COALESCE(NEW.period_key, OLD.period_key),
                    'insight_kind', COALESCE(NEW.insight_kind, OLD.insight_kind)
                ),
                NOW()
            );
            RAISE EXCEPTION 'ai_insight_cache is INSERT-only (AD-2) — % blocked', TG_OP
                USING ERRCODE = '40006';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_ai_insight_cache_update_block
        BEFORE UPDATE ON ai_insight_cache
        FOR EACH ROW
        EXECUTE FUNCTION trg_ai_insight_cache_no_update_delete()
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_ai_insight_cache_delete_block
        BEFORE DELETE ON ai_insight_cache
        FOR EACH ROW
        EXECUTE FUNCTION trg_ai_insight_cache_no_update_delete()
        """
    )


def downgrade() -> None:
    """Story 10.2 — drop ai_insight_cache table + triggers."""
    op.execute("DROP TRIGGER IF EXISTS trg_ai_insight_cache_update_block ON ai_insight_cache")
    op.execute("DROP TRIGGER IF EXISTS trg_ai_insight_cache_delete_block ON ai_insight_cache")
    op.execute("DROP FUNCTION IF EXISTS trg_ai_insight_cache_no_update_delete()")
    op.execute("DROP TABLE IF EXISTS ai_insight_cache")
