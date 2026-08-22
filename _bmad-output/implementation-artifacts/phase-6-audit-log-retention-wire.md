---
baseline_commit: e84a281
epic_number: phase-6
status: ready-for-dev
wire_target: phase-6-audit-log-retention-wire
created: 2026-08-22
cj_style_entry_point: 86
---

# Story: Phase 6 — Audit Log Retention Policy Wire (cj-style 86번째 epic 연속 정직 회복 atomic docs-only wire)

## Story

**As a** operations team / compliance officer
**I want** audit log retention policy enforcement + automatic purge job + archive storage with immutable SHA-256 hash chain + GDPR Article 17 right to erasure
**so that** we satisfy NFR4 PII minimization EXTENSION + regulatory retention requirements (5년 audit_logs per Epic 12 close-out retro) + cross-region archive carry-over (Phase 5 wire `f093f8c`의 `phase_5_replication_lag` table) + GDPR Article 17 right to erasure endpoint

## Context (Phase 6 territory verbatim)

Phase 6 (Audit Log Retention Policy territory)는 Epic 17 T2+T3 UI frontend atomic wire `bb92879` (cj-style 83번째)의 backend audit log query API + Epic 12 close-out retro `a63646c`의 NFR4 5년 audit_logs + Epic 12-3 account deletion retention (30일 hard delete) + Phase 5 wire `f093f8c` cross-region archive carry-over chain의 natural next 진입 territory.

**Phase 6 PRD entry commit**: `e84a281` (master PRD v3.6 → v3.7 atomic edit + capability matrix v1.30 → v1.31 EXTENSION AUDIT_LOG_RETENTION 1 NEW row)

**Phase 6 territory 결정 wire** = Audit Log Retention Policy + automatic purge job + archive storage + GDPR Article 17 right to erasure + NFR4 PII minimization EXTENSION + 5 NEW AuditAction Literal values + capability matrix v1.31 EXTENSION

---

## Acceptance Criteria (7 ACs PRD §F22.1~§F22.7 verbatim)

### §F22.1 Retention policy DSL (12 ACs)
1. `apps/api/modules/audit/retention/retention_dsl.py` NEW (~120 LOC) defines `RetentionPolicy` TypedDict + `RetentionClass` Literal["admin"|"auth"|"data"|"security"] 결정 wire
2. Per-tenant retention DSL `retain(action_class, days, archive, mask_pii)` builder function 결정 wire
3. `DEFAULT_RETENTION_DAYS` module-level constants: admin=1825일 (5년), auth=1095일 (3년), data=1825일 (5년), security=2555일 (7년) 결정 wire (Epic 12 close-out retro §6 NFR4 5년 audit_logs verbatim carry-over)
4. `parse_retention_policy(tenant_id: str, payload: dict) -> RetentionPolicy` function 결정 wire (validation + RLS 자동 적용 CR 0-2 verbatim)
5. `AuditLogRetentionPolicyInvalidError(400)` 1 NEW error class CR 12-5 D-14 envelope 결정 wire
6. Unit tests: tenant-scoped retention isolation + DSL parsing 7 cases 결정 wire
7. `parse_retention_policy` accepts per-action override (e.g. `audit_log_purged` 30일 hard delete) 결정 wire
8. Default policy applies when tenant has no explicit retention configuration 결정 wire
9. `RetentionPolicy` validation rejects negative days + archive=False mask_pii=True contradiction + non-numeric values 결정 wire
10. `RetentionPolicy` immutability: after initial parse, policy changes require explicit `update_retention_policy()` mutation function 결정 wire
11. RLS isolation: tenant can only read/write own RetentionPolicy row CR 0-2 verbatim 결정 wire
12. `RetentionPolicy` TypedDict mirror parity with TypeScript frontend `audit-log-retention-client.ts` interface CR 12-5 D-PARITY-01 inversion 결정 wire

### §F22.2 Automatic purge job (10 ACs)
1. `apps/api/jobs/audit_log_purge.py` NEW (~180 LOC) KST cron job 결정 wire
2. Cron schedule: KST 02:00 매일 (UTC 17:00) 결정 wire (avoiding Phase 5 DR drill cron conflict at KST 1st Sunday 03:00 UTC 18:00)
3. Iterates all tenants → resolves RetentionPolicy → DELETEs expired audit_log entries WHERE created_at < now() - retention_days 결정 wire (idempotent: no-op if no expired entries)
4. Audit-first INSERT `audit_log_purged` CR 1-1 verbatim BEFORE actual DELETE (BEFORE byte stream flush) 결정 wire
5. ActionClass.AUDIT EXTENSION 1 NEW enum value 결정 wire (Phase 5 wire `f093f8c` ActionClass.INFRA pattern 미러)
6. `AuditLogPurgePolicyMissingError(404)` 1 NEW error class 결정 wire (when tenant has no RetentionPolicy + no default applied)
7. `AuditLogPurgeFailedError(500)` 1 NEW error class 결정 wire (when DELETE fails mid-purge)
8. APScheduler lifespan hook integration 결정 wire (Phase 5 wire `f093f8c` dr_drill cron pattern 미러)
9. Pagination: process expired entries in batches of 1000 to avoid long-running transaction lock 결정 wire
10. Dry-run mode: `dry_run=True` parameter returns count of entries that would be purged WITHOUT actual DELETE 결정 wire (operational safety per NFR4 PII minimization)

### §F22.3 Archive storage with immutable append-only + SHA-256 hash chain (12 ACs)
1. `apps/api/db/migrations/versions/0040_phase_6_audit_retention.py` NEW alembic migration 결정 wire
2. New table `audit_log_archive` 결정 wire: columns (`archive_id UUID PK` + `tenant_id UUID NOT NULL` + `audit_log_id UUID NOT NULL` + `payload_snapshot JSONB NOT NULL` + `archived_at TIMESTAMPTZ NOT NULL` + `sha256_hash TEXT NOT NULL` + `previous_hash TEXT` + `region TEXT NOT NULL DEFAULT 'primary'`) 결정 wire
3. New table `phase_6_audit_purge_log` 결정 wire: columns (`purge_log_id UUID PK` + `tenant_id UUID NOT NULL` + `purged_at TIMESTAMPTZ NOT NULL` + `purged_count INTEGER NOT NULL` + `dry_run BOOLEAN NOT NULL DEFAULT FALSE` + `trace_id TEXT`) 결정 wire
4. ALTER TABLE audit_log ADD COLUMN `archived_at TIMESTAMPTZ` 결정 wire (NULL until archived)
5. Immutable append-only trigger on `audit_log_archive`: BEFORE UPDATE/DELETE raise `AuditLogArchiveImmutableError` 결정 wire
6. SHA-256 hash chain linkage: each new `audit_log_archive` row's `sha256_hash` = SHA-256(audit_log_id + payload_snapshot + previous_hash) 결정 wire
7. `verify_archive_hash_chain(tenant_id) -> bool` function 결정 wire (re-computes chain + raises `AuditLogArchiveHashChainMismatchError(500)` on mismatch)
8. `audit_log_archive` is system-only table: RLS disabled (system-managed) CR 0-2 verbatim (Phase 5 wire `f093f8c` `phase_5_replication_lag` table pattern 미러)
9. `audit_log_archive` is replicated to secondary Tokyo region via Phase 5 Supabase multi-region replication 결정 wire (carry-over from `phase_5_replication_lag` table)
10. Trigger `archive_expired_audit_logs` AFTER DELETE on audit_log fires when archive=True in RetentionPolicy → inserts row into `audit_log_archive` BEFORE actual DELETE 결정 wire
11. Audit-first INSERT `audit_log_archived` CR 1-1 verbatim 결정 wire (ActionClass.AUDIT EXTENSION)
12. Cold-archive action `audit_log_cold_archived`: when archive_age > 90일, move to cold archive storage (separate from `audit_log_archive`) + audit-first INSERT 결정 wire

### §F22.4 GDPR Article 17 right to erasure + NFR4 PII minimization (10 ACs)
1. `apps/api/modules/audit/retention/erasure.py` NEW (~150 LOC) GDPR Article 17 erasure endpoint 결정 wire
2. `POST /api/v1/audit-log/erase` endpoint 결정 wire: payload `{actor_id: str, scope: "all"|"actor"|"tenant", reason: str}` 결정 wire
3. `require_role("owner")` permission gate CR 12-5 D-GATE-01 inversion 결정 wire (AD-22 owner-only RBAC verbatim)
4. `audit_log_personal_data_erased` 1 NEW audit action CR 1-1 verbatim 결정 wire (BEFORE actual PII masking)
5. PII masking via AES-256-GCM NFR6 encryption: `mask_pii_fields(payload, fields=["actor_email", "actor_phone", "payload_json.user_data"])` 결정 wire
6. UPDATE audit_log SET actor_email=NULL, actor_phone=NULL, payload_json=mask_pii(payload_json) WHERE scope filter 적용 결정 wire
7. Archive copy preservation: original `audit_log_archive` rows retain pre-erasure snapshot (cannot be erased per immutable append-only) 결정 wire
8. `AuditLogPiiErasureNotFoundError(404)` 1 NEW error class 결정 wire (when actor_id not found)
9. `AuditLogPiiErasureForbiddenError(403)` 1 NEW error class 결정 wire (when actor_id in different tenant)
10. Trace ID propagation: every erasure call generates UUID trace_id + logs to Sentry breadcrumb 결정 wire (Phase 5 wire `f093f8c` observability pattern 미러)

### §F22.5 Audit-first INSERT 5 NEW actions (8 ACs)
1. `audit_log_purged` 1 NEW AuditAction Literal value 결정 wire (Phase 6 §F22.2)
2. `audit_log_archived` 1 NEW AuditAction Literal value 결정 wire (Phase 6 §F22.3)
3. `audit_log_pii_masked` 1 NEW AuditAction Literal value 결정 wire (Phase 6 §F22.4)
4. `audit_log_cold_archived` 1 NEW AuditAction Literal value 결정 wire (Phase 6 §F22.3)
5. `audit_log_personal_data_erased` 1 NEW AuditAction Literal value 결정 wire (Phase 6 §F22.4)
6. ActionClass.AUDIT EXTENSION 5 NEW enum values 결정 wire (Phase 5 wire `f093f8c` ActionClass.INFRA pattern 미러)
7. `AuditAction` Union EXTENSION 5 NEW Literal values + `_ActionRegistry` EXTENSION 5 NEW entries + `__all__` EXTENSION 5 NEW names 결정 wire
8. Each new action emits audit log BEFORE actual destructive operation (CR 1-1 verbatim) 결정 wire

### §F22.6 Capability gate AUDIT_LOG_RETENTION (8 ACs)
1. `apps/api/core/capability.py` MODIFIED + `Capability.AUDIT_LOG_RETENTION = "audit_log_retention"` 1 NEW enum 결정 wire
2. `_INDUSTRY_CAPABILITIES` blocks EXTENSION 4 industries: manufacturing + service + 겸영 + 겸영+기타 → 모두 grants AUDIT_LOG_RETENTION ✅ 결정 wire (industry-agnostic CR 12-1 L4 precedent 미러)
3. `apps/api/dependencies/capability.py` EXTENSION `require_audit_log_retention = require_capability(Capability.AUDIT_LOG_RETENTION)` 1 NEW dep 결정 wire
4. `require_audit_log_retention` applied to: POST /api/v1/audit-log/erase + purge job trigger endpoint + dry-run endpoint + retention policy update endpoint 결정 wire
5. Capability matrix v1.30 → v1.31 EXTENSION 1 NEW row `AUDIT_LOG_RETENTION` industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire (Phase 5 v1.29 MULTI_REGION_BACKUP pattern verbatim)
6. Drift detector `tests/integration/test_capability_matrix_v1_31_drift.py` NEW 8 NEW pytest cases 결정 wire (Phase 5 v1.29 + Epic 16 v1.28 + Epic 17 v1.30 pattern verbatim)
7. 미허용 tenant의 audit log retention 진입 차단 결정 wire CR 12-5 D-GATE-01 inversion 결정 wire
8. Capability matrix `__all__` EXTENSION + Capability matrix v1.31 changelog entry 결정 wire

### §F22.7 Tests + wire scope T1~T8 (16 ACs)
1. ~50 NEW pytest cases 결정 wire (12 retention_dsl + 10 purge job + 12 archive storage + 10 GDPR erasure + 5 audit_action + 8 capability matrix v1.31 drift = 57 cases total)
2. ~15 NEW vitest cases 결정 wire (5 retention config page + 5 purge job trigger + 5 GDPR erasure confirmation modal)
3. 0 NEW ruff + 0 regressions + 3중 게이트 FINAL CLEAN 보존 결정 wire
4. T1 retention DSL pure kernel + T2 automatic purge job KST cron + T3 archive storage alembic 0040 + SHA-256 hash chain + T4 GDPR/NFR4 erasure endpoint + T5 5 NEW AuditAction Literal values + ActionClass.AUDIT EXTENSION + T6 Capability v1.31 EXTENSION + drift detector + T7 Tests + T8 atomic commit via `git commit -F <file>` CR 9-6 D5 prevention
5. Alembic 0040 migration reversible + idempotent 결정 wire
6. Test cases include RLS isolation tests CR 0-2 verbatim (multi-tenant isolation)
7. Test cases include audit-first INSERT verification CR 1-1 verbatim (audit log emitted BEFORE destructive operation)
8. Test cases include SHA-256 hash chain tamper detection (modify payload → re-verify chain → expect AuditLogArchiveHashChainMismatchError)
9. Test cases include GDPR erasure PII masking (assert actor_email=NULL + payload_json.user_data masked)
10. Test cases include capability matrix drift detector (modify enum → expect drift detector FAIL)
11. Test cases include dry-run mode (purge with dry_run=True → no actual DELETE + count returned)
12. Test cases include pagination batch=1000 (insert 5000 expired entries → expect 5 DELETE batches)
13. Test cases include immutable archive trigger (UPDATE audit_log_archive → expect AuditLogArchiveImmutableError)
14. Test cases include cross-region archive (verify Tokyo replica has audit_log_archive rows)
15. Test cases include cold archive action (90+일 entries → audit_log_cold_archived)
16. Atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention) + A36 SDR 검증 4-step 자동 적용 결정 wire

---

## Tasks (T1~T8)

### T1. Retention DSL pure kernel (13 subtasks)
1.1. Create `apps/api/modules/audit/retention/__init__.py` module docstring
1.2. Create `apps/api/modules/audit/retention/retention_dsl.py` (~120 LOC) with RetentionPolicy TypedDict
1.3. Define RetentionClass Literal["admin"|"auth"|"data"|"security"]
1.4. Implement DEFAULT_RETENTION_DAYS module-level constants
1.5. Implement `retain(action_class, days, archive, mask_pii)` builder function
1.6. Implement `parse_retention_policy(tenant_id, payload) -> RetentionPolicy`
1.7. Add RLS auto-isolation CR 0-2 verbatim
1.8. Add AuditLogRetentionPolicyInvalidError(400) CR 12-5 D-14 envelope
1.9. Add `update_retention_policy()` mutation function with audit-first INSERT
1.10. Add tenant-scoped query: `get_retention_policy(tenant_id) -> RetentionPolicy`
1.11. Add TS mirror interface in `apps/web/lib/audit/audit-log-retention-client.ts`
1.12. Add `apps/api/modules/audit/retention/retention_routes.py` with POST /api/v1/audit-log/retention/policy + GET /api/v1/audit-log/retention/policy
1.13. Add 12 NEW pytest cases in `tests/api/modules/audit/test_retention_dsl.py`

### T2. Automatic purge job KST cron (8 subtasks)
2.1. Create `apps/api/jobs/__init__.py` package marker
2.2. Create `apps/api/jobs/audit_log_purge.py` (~180 LOC) KST cron job
2.3. Configure APScheduler: KST 02:00 daily schedule (UTC 17:00)
2.4. Implement `purge_expired_audit_logs(tenant_id, dry_run=False) -> int` function
2.5. Add idempotent DELETE batch=1000 pagination
2.6. Add audit-first INSERT `audit_log_purged` CR 1-1 verbatim
2.7. Add AuditLogPurgePolicyMissingError(404) + AuditLogPurgeFailedError(500)
2.8. Wire APScheduler lifespan hook in `apps/api/main.py` (Phase 5 dr_drill pattern 미러)

### T3. Archive storage alembic 0040 + SHA-256 hash chain (14 subtasks)
3.1. Create `apps/api/db/migrations/versions/0040_phase_6_audit_retention.py` alembic migration
3.2. Define `audit_log_archive` table (8 columns)
3.3. Define `phase_6_audit_purge_log` table (6 columns)
3.4. ALTER TABLE audit_log ADD COLUMN archived_at TIMESTAMPTZ
3.5. Add immutable append-only trigger on audit_log_archive (BEFORE UPDATE/DELETE raise)
3.6. Implement SHA-256 hash chain linkage
3.7. Add `verify_archive_hash_chain(tenant_id) -> bool` function
3.8. Add AuditLogArchiveHashChainMismatchError(500)
3.9. Add AuditLogArchiveImmutableError(403)
3.10. Add `archive_expired_audit_logs` AFTER DELETE trigger
3.11. Add audit-first INSERT `audit_log_archived` CR 1-1 verbatim
3.12. Add cold-archive function `move_to_cold_archive(tenant_id, older_than_days=90)` + audit-first INSERT `audit_log_cold_archived`
3.13. Disable RLS on `audit_log_archive` + `phase_6_audit_purge_log` (system-only tables) CR 0-2 verbatim
3.14. Add 12 NEW pytest cases in `tests/api/db/test_audit_log_archive.py`

### T4. GDPR/NFR4 erasure endpoint (9 subtasks)
4.1. Create `apps/api/modules/audit/retention/erasure.py` (~150 LOC)
4.2. Implement `POST /api/v1/audit-log/erase` endpoint with payload validation
4.3. Add `require_role("owner")` + `require_audit_log_retention` gate CR 12-5 D-GATE-01 inversion
4.4. Implement PII masking via AES-256-GCM NFR6: `mask_pii_fields(payload, fields)`
4.5. Add audit-first INSERT `audit_log_personal_data_erased` CR 1-1 verbatim
4.6. Add archive copy preservation logic (cannot erase archived rows)
4.7. Add AuditLogPiiErasureNotFoundError(404) + AuditLogPiiErasureForbiddenError(403)
4.8. Add trace_id generation + Sentry breadcrumb (Phase 5 observability pattern 미러)
4.9. Add 10 NEW pytest cases in `tests/api/modules/audit/test_gdpr_erasure.py`

### T5. 5 NEW AuditAction Literal values + ActionClass.AUDIT EXTENSION (5 subtasks)
5.1. Modify `apps/api/core/audit_action.py` EXTENSION ActionClass.AUDIT enum (no new enum, reuse AUDIT)
5.2. Add 5 NEW AuditAction Literal values: `audit_log_purged` + `audit_log_archived` + `audit_log_pii_masked` + `audit_log_cold_archived` + `audit_log_personal_data_erased`
5.3. Add AuditAction Union EXTENSION 5 NEW Literal values
5.4. Add _ActionRegistry EXTENSION 5 NEW entries + __all__ EXTENSION 5 NEW names
5.5. Add 5 NEW pytest cases in `tests/api/core/test_phase_6_audit_action.py`

### T6. Capability v1.31 EXTENSION + drift detector (6 subtasks)
6.1. Modify `apps/api/core/capability.py` EXTENSION Capability.AUDIT_LOG_RETENTION = "audit_log_retention"
6.2. EXTENSION 4 _INDUSTRY_CAPABILITIES blocks (manufacturing + service + 겸영 + 겸영+기타) with AUDIT_LOG_RETENTION grants ✅
6.3. Modify `apps/api/dependencies/capability.py` EXTENSION `require_audit_log_retention = require_capability(Capability.AUDIT_LOG_RETENTION)`
6.4. Modify `docs/capability-matrix.md` v1.30 → v1.31 EXTENSION 1 NEW row AUDIT_LOG_RETENTION
6.5. Add v1.31 changelog entry
6.6. Create `tests/integration/test_capability_matrix_v1_31_drift.py` NEW 8 NEW pytest cases

### T7. Tests (~65 NEW pytest + ~15 NEW vitest cases) (8 subtasks)
7.1. 12 NEW pytest cases for retention_dsl (T1.13)
7.2. 10 NEW pytest cases for purge job (new file `tests/api/jobs/test_audit_log_purge.py`)
7.3. 12 NEW pytest cases for archive storage (T3.14)
7.4. 10 NEW pytest cases for GDPR erasure (T4.9)
7.5. 5 NEW pytest cases for audit_action (T5.5)
7.6. 8 NEW pytest cases for capability matrix v1.31 drift (T6.6)
7.7. 15 NEW vitest cases (5 retention config page + 5 purge job trigger + 5 GDPR erasure confirmation modal)
7.8. 3중 게이트 FINAL CLEAN verification (ruff scoped + pytest focused + vitest focused)

### T8. Atomic commit via `git commit -F <file>` (4 subtasks)
8.1. Create `_bmad-output/implementation-artifacts/commit-msg-phase-6-audit-log-retention-wire.txt` commit message file
8.2. Create `memory/handoff-2026-08-22-phase-6-spec-entry-done.md` handoff memory
8.3. Update `_bmad-output/implementation-artifacts/sprint-status.yaml`: phase-6-spec-entry: backlog → done + A198~A202 action_items + last_updated_note v3.7 Phase 6 spec entry prepend
8.4. Update `memory/MEMORY.md` hook index EXTENSION + atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention)

---

## Dev Notes

### CR Lessons Applied (14종 결정 wire)

- **CR 0-2 RLS lesson** ✅ APPLIED: `retention_dsl.py` + `audit_log_archive` + `phase_6_audit_purge_log` RLS 자동 적용 (system-only tables RLS disabled) CR 0-2 verbatim + multi-tenant isolation test 결정 wire
- **CR 1-1 audit-first INSERT** ✅ APPLIED: 5 NEW audit log entries (`audit_log_purged` + `audit_log_archived` + `audit_log_pii_masked` + `audit_log_cold_archived` + `audit_log_personal_data_erased`) + ActionClass.AUDIT EXTENSION + emit_audit_typed BEFORE destructive operation CR 1-1 verbatim
- **CR 9-6 commit message discipline** ✅ APPLIED: `git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention + commit message file 결정 wire
- **CR 11-3 honest-DEFER discipline** ✅ APPLIED: 86번째 epic 연속 정직 회복, D-1-1-DEFER-* ✅ RESOLVED 보존 + D-EPIC-16-REVIEW-DEFER-* ✅ RESOLVED 보존 + D-PHASE-4-DR-DEFER-* ✅ RESOLVED 보존 + D-EPIC-17-WIRE-DEFER-T2-T3-UI ✅ RESOLVED 보존 + **D-RETENTION-1 honestly RESOLVED 진입 wire** (1st release close-out retro §6 + Epic 17 close-out retro §11 verbatim 해소)
- **CR 11-4 D-001~D-005 + P-015 lessons carry** ✅ APPLIED: dry-run mode UI 진입 시 frontend territory 정합 sweep 결정 wire (ko-KR.json `audit_log_retention.*` namespace EXTENSION 8 keys EXTENSION 예정)
- **CR 12-1 L4 industry-agnostic capability** ✅ APPLIED: AUDIT_LOG_RETENTION industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire (Phase 5 MULTI_REGION_BACKUP/FAILOVER + Epic 17 AUDIT_LOG_VIEW + Epic 16 TENANT_IDP_MANAGEMENT + Epic 15 SSO_ENTERPRISE + Epic 13/14 LISTEN_NOTIFY + Phase 3 AUTH_MIDDLEWARE + 1st release LAUNCH_* + Phase 4 DEPLOYMENT_* pattern verbatim bind)
- **CR 12-5 D-14 typed exception envelope** ✅ APPLIED: 6 NEW error classes (AuditLogRetentionPolicyInvalidError 400 + AuditLogPurgePolicyMissingError 404 + AuditLogPurgeFailedError 500 + AuditLogArchiveHashChainMismatchError 500 + AuditLogArchiveImmutableError 403 + AuditLogPiiErasureNotFoundError 404 + AuditLogPiiErasureForbiddenError 403) 결정 wire + apps/api/main.py 7 NEW exception handlers
- **CR 12-5 D-PARITY-01 inversion** ✅ APPLIED: Python FastAPI backend `retention_dsl.py` TypedDict ↔ TypeScript Next.js frontend `audit-log-retention-client.ts` interface parity 결정 wire + vitest CR 12-5 D-PARITY-01 검증
- **CR 12-5 D-GATE-01 inversion** ✅ APPLIED: AUDIT_LOG_RETENTION capability gate per-tenant on/off + owner-only RBAC AD-22 결정 wire + GDPR erasure endpoint `require_role("owner")` 결정 wire
- **A19 cohesion pattern 9 surface EXTENSION PASS** ✅ APPLIED: audit log retention surface NEW = F22.1~F22.7 audit log retention policy territory 결정 wire + spec surface EXTENSION + test surface EXTENSION
- **A36 SDR 검증 4-step 자동 적용** ✅ APPLIED: commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS 결정 wire
- **AD-14 stack pin** ✅ APPLIED: no new deps 결정 wire (APScheduler already in stack from Phase 5 wire `f093f8c`)
- **AD-22 owner-only RBAC** ✅ APPLIED: manual audit log retention owner-only RBAC 결정 wire + Epic 12 2FA 챌린지 보존 + GDPR erasure endpoint `require_role("owner")` 결정 wire
- **NFR4 PII minimization** ✅ PRESERVED: audit log retention 진입 시 NFR4 PII 데이터 minimization + GDPR Article 17 right to erasure EXTENSION 정합 보존 결정 wire + audit log payload encryption at rest 결정 wire + AES-256-GCM NFR6 PII data masking 결정 wire

### Architecture Alignment (cj-style architecture ALLOWED sweep)
- **kernel**: retention DSL pure functions + SHA-256 hash chain pure functions
- **port**: `apps/api/modules/audit/retention/` port (retention_dsl + erasure) 결정 wire
- **db schema**: audit_log_archive + phase_6_audit_purge_log + audit_log.archived_at column 결정 wire (Phase 5 phase_5_replication_lag pattern 미러)
- **service**: audit_log_purge service + gdpr_erasure service + archive_storage service 결정 wire
- **handler**: POST /api/v1/audit-log/erase + POST /api/v1/audit-log/retention/policy + GET /api/v1/audit-log/retention/policy + POST /api/v1/audit-log/purge (dry-run) 결정 wire
- **envelope**: CR 12-5 D-14 typed exception envelope 7 NEW error classes 결정 wire
- **capability**: AUDIT_LOG_RETENTION capability gate per-tenant on/off + owner-only RBAC AD-22 결정 wire
- **audit**: 5 NEW AuditAction Literal values + ActionClass.AUDIT EXTENSION + audit-first INSERT CR 1-1 verbatim
- **audit_log_retention surface NEW**: F22.1~F22.7 audit log retention policy territory 결정 wire EXTENSION PASS

### Files Affected (Estimated ~50 NEW + ~10 MODIFIED)
**NEW files (estimated)**:
- `apps/api/modules/audit/retention/__init__.py`
- `apps/api/modules/audit/retention/retention_dsl.py` (~120 LOC)
- `apps/api/modules/audit/retention/retention_routes.py` (~120 LOC)
- `apps/api/modules/audit/retention/erasure.py` (~150 LOC)
- `apps/api/jobs/__init__.py`
- `apps/api/jobs/audit_log_purge.py` (~180 LOC)
- `apps/api/db/migrations/versions/0040_phase_6_audit_retention.py` (alembic migration)
- `apps/web/lib/audit/audit-log-retention-client.ts` (~150 LOC, TS interface mirrors CR 12-5 D-PARITY-01)
- `apps/web/app/[locale]/(dashboard)/audit-log-retention/page.tsx` (~100 LOC, RSC)
- `apps/web/components/audit/RetentionPolicyPanel.tsx` (~150 LOC, Client orchestrator)
- `apps/web/components/audit/RetentionPolicyForm.tsx` (~120 LOC, 4 retention classes)
- `apps/web/components/audit/PurgeJobTrigger.tsx` (~100 LOC, dry-run mode UI)
- `apps/web/components/audit/GdprErasureModal.tsx` (~150 LOC, confirmation modal)
- 6 NEW pytest files (test_retention_dsl + test_audit_log_purge + test_audit_log_archive + test_gdpr_erasure + test_phase_6_audit_action + test_capability_matrix_v1_31_drift)
- 3 NEW vitest files (audit-log-retention/page + audit-log-retention-client + i18n/audit-log-retention-ssot)
- 1 NEW handoff memory (`memory/handoff-2026-08-22-phase-6-spec-entry-done.md`)
- 1 NEW commit-msg file (`_bmad-output/implementation-artifacts/commit-msg-phase-6-audit-log-retention-wire.txt`)

**MODIFIED files (estimated)**:
- `apps/api/main.py` (audit_log_retention_router include_router + 7 NEW exception handlers)
- `apps/api/core/audit_action.py` (ActionClass.AUDIT EXTENSION + 5 NEW AuditAction Literal values + _ActionRegistry EXTENSION + __all__ EXTENSION)
- `apps/api/core/capability.py` (Capability.AUDIT_LOG_RETENTION EXTENSION + 4 _INDUSTRY_CAPABILITIES blocks EXTENSION)
- `apps/api/dependencies/capability.py` (require_audit_log_retention EXTENSION + __all__ EXTENSION)
- `docs/capability-matrix.md` (v1.30 → v1.31 EXTENSION title + 1 NEW row + changelog)
- `apps/web/messages/ko-KR.json` (`audit_log_retention.*` namespace EXTENSION 8 keys EXTENSION)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (phase-6-spec-entry entry + A198~A202 action_items + last_updated_note prepend)
- `memory/MEMORY.md` (handoff hook index EXTENSION)

**Total**: ~26 NEW + ~8 MODIFIED = ~34 files atomic single sprint

### Test Coverage (cj-style 정합)
- pytest: ~50 NEW CASES (12 retention_dsl + 10 purge job + 12 archive storage + 10 GDPR erasure + 5 audit_action + 8 capability matrix v1.31 drift = 57 cases total)
- vitest: ~15 NEW CASES (5 retention config page + 5 purge job trigger + 5 GDPR erasure confirmation modal)
- ruff: 0 NEW errors
- regressions: 0 NEW
- 3중 게이트 FINAL CLEAN 보존 결정 wire

### References (16)
1. `_bmad-output/planning-artifacts/prd.md` §F22 (master PRD v3.7 §F22 territory)
2. `_bmad-output/planning-artifacts/prd.md` §8.1 M0-(o) Phase 6 AC
3. `_bmad-output/planning-artifacts/prd.md` §15 로드맵 Phase 6 row
4. `_bmad-output/planning-artifacts/prd.md` 부록 A AD-33 Audit Log Retention Policy
5. `docs/capability-matrix.md` v1.31 EXTENSION AUDIT_LOG_RETENTION row
6. Epic 17 bmad-dev-story atomic wire T1~T8 backend `2ada2ec` — audit_log_query.py carry-over chain
7. Phase 5 atomic wire `f093f8c` — `phase_5_replication_lag` table + Supabase multi-region primary Seoul + secondary Tokyo replica carry-over chain
8. Epic 12 close-out retro `a63646c` — NFR4 5년 audit_logs + Epic 12-3 account deletion retention (30일 hard delete) carry-over
9. 1st release close-out retro §6 verbatim D-RETENTION-1 honestly RESOLVED 진입 결정 wire
10. Epic 17 close-out retro §11 verbatim D-RETENTION-1 honestly RESOLVED 진입 결정 wire
11. Phase 5 spec entry `phase-5-multi-region-backup-wire.md` — APScheduler lifespan hook pattern 미러
12. Epic 17 spec entry `epic-17-audit-log-viewer-and-activity-stream-wire.md` — 7 ACs verbatim pattern
13. CR 0-2 RLS lesson (multi-tenant isolation)
14. CR 1-1 audit-first INSERT lesson (5 NEW actions)
15. CR 11-3 honest-DEFER discipline (86번째 epic 연속 정직 회복)
16. CR 12-1 L4 industry-agnostic capability precedent (capability matrix v1.31 EXTENSION)

### Story Header
- **Story ID**: phase-6
- **Story Title**: Audit Log Retention Policy Wire
- **Created**: 2026-08-22
- **cj-style entry point**: 86
- **baseline_commit**: e84a281 (Phase 6 PRD entry commit)
- **PRD section**: §F22 (master PRD v3.7)
- **AC count**: 7 ACs (PRD §F22.1~§F22.7 verbatim)
- **Sub-AC count**: 64 detailed sub-ACs
- **Task count**: 8 (T1~T8)
- **Subtask count**: 66 (T1:13 + T2:8 + T3:14 + T4:9 + T5:5 + T6:6 + T7:8 + T8:3)
- **Estimated wire scope**: ~26 NEW + ~8 MODIFIED = ~34 files atomic single sprint
- **Estimated pytest**: ~57 NEW CASES
- **Estimated vitest**: ~15 NEW CASES

### Dev Agent Record
- **Agent**: Amelia (Developer)
- **Wire target**: phase-6-audit-log-retention-wire
- **Wire commit**: pending (T8 atomic commit)
- **3중 게이트**: pending (T7 verification)
- **A19 cohesion**: pending (9 surface EXTENSION PASS)
- **CR lessons applied**: 14종 결정 wire
- **D-DEFER-* honestly 결정**: D-RETENTION-1 ✅ RESOLVED + D-1-1-DEFER-* ✅ RESOLVED + D-EPIC-16-REVIEW-DEFER-* ✅ RESOLVED + D-PHASE-4-DR-DEFER-* ✅ RESOLVED + D-EPIC-17-WIRE-DEFER-T2-T3-UI ✅ RESOLVED

---

**Why/How to apply**: cj-style discipline 회피 위험 방지 — Phase 6 spec entry 진입 시점에 4-entry-point pattern 두 번째 진입점 결정 (PRD 85 → spec 86 → atomic wire T1~T8 87 → close-out retro 88). D-RETENTION-1 honestly RESOLVED 결정 wire 보존. 7 ACs PRD §F22.1~§F22.7 verbatim + 8 tasks T1~T8 + 66 subtasks + ~34 files estimated wire scope + 14종 CR lessons applied. Epic 1~17 + Phase 3~5 + 1st release cycle 정합 보존 검증 결정 wire 보존.
