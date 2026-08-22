---
baseline_commit: 93d852b
---

# Story phase-5.1: Multi-Region Backup & Disaster Recovery wire (Phase 5 cj-style 2번째 진입점)

Status: ready-for-dev

<!-- Phase 5 cj-style 2번째 진입점 = cj-style 74번째 epic 연속 정직 회복 bmad-create-story spec.
     Phase 5 PRD entry (`phase-5-prd-entry: done`, 2026-08-22, commit `93d852b`) 직후.
     master PRD v3.5 §F20 verbatim + AD-31 verbatim + A124+A125+A126+A127+A128 결정 wire.
     T1~T8 wire scope (Multi-Region Backup & Disaster Recovery territory = phase_5_replication_lag table + phase_5_dr_drill_results table + failover_orchestrator + dr_drill + cross-region backup strategy docs EXTENSION + multi-region health observability + Capability v1.29 EXTENSION 2 NEW rows + tests + 3중 게이트 FINAL CLEAN 결정).
     Phase 4 close-out retro §6 disaster recovery "multi-region backup 결정 wire 보류, Phase 5+ 진입 시점" verbatim 자연스러운 carry-over chain 결정 wire 진입 (D-PHASE-4-DR-DEFER-1/2 honestly RESOLVE 진입 결정 wire 진입).
     D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존 (cj-style Epic 15 wire 60~61번째 honest-DEFER discipline 검증 — Phase 5 spec entry 진입 시점에 grep guard INVERSION 또는 test rename 결정 wire 보존).
     D-EPIC-16-REVIEW-DEFER-2~6 (H8+M5+M7+M9+L11) honestly DEFERRED 5 OPEN 보존 (cj-style 70~73번째 epic 연속 정직 회복 검증).
     A19 cohesion pattern 9 surface EXTENSION PASS 결정 (multi-region surface EXTENSION = F20.1~F20.5 multi-region backup & DR territory).
     CR lessons applied (cj-style 74번째 epic 연속 정직 회복 docs only wire 진입 시점에 결정): CR 0-2 RLS + CR 1-1 audit-first INSERT + CR 9-6 commit message discipline + CR 11-3 honest-DEFER discipline + CR 12-1 L4 industry-agnostic capability + CR 12-5 D-14 typed exception envelope + D-PARITY-01 inversion + D-GATE-01 inversion + A19 cohesion pattern + A36 SDR 검증 4-step 자동 적용. -->

## Story

As a **costmgr product owner**,
I want the **Phase 5 Multi-Region Backup & Disaster Recovery territory fully wired end-to-end with `phase_5_replication_lag` table + `phase_5_dr_drill_results` table (alembic 0039) + Cross-region read replica + WAL archiving (Supabase managed PITR cross-region extension) + Cross-region failover automation (failover_orchestrator + primary → secondary health probe + automatic promotion + DNS update via Supabase custom domain redirect + RTO 30s target + manual trigger owner-only AD-22 RBAC + 2FA 챌린지 Epic 12 정합) + DR drill + automated quarterly test (dr_drill cron KST 1st Sunday 03:00 + 6 drill steps + RPO/RTO measurement + Q1/Q2/Q3/Q4 quarterly schedule) + Cross-region backup strategy (docs/database-backup.md EXTENSION 12 sections + cross-region PITR primary Seoul + secondary Tokyo + 30일 hot + 90일 cold + 365일 archive regional + RPO 1h / RTO 4h SLA) + Multi-region health observability (apps/api/core/health.py EXTENSION `/api/v1/health/multi-region` endpoint + apps/api/core/observability.py EXTENSION Sentry breadcrumb failover + Grafana multi-region dashboard + apps/web/app/api/health/multi-region/route.ts NEW Next.js Edge Runtime) + capability gates MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER (capability matrix v1.28 → v1.29 EXTENSION) + audit-first INSERT 4 NEW (`replica_status_changed` + `failover_initiated` + `failover_completed` + `dr_drill_completed`, CR 1-1 verbatim, ActionClass.INFRA 신규) + multi-tenant isolation (CR 0-2 RLS lesson — system-only tables replication metadata)**,
so that **Phase 5 territory 가 wire 되어 Phase 4 close-out retro §6 disaster recovery honestly-deferred "multi-region backup 결정 wire 보류, Phase 5+ 진입 시점" verbatim 가 정직 해소되고, 1차 출시 후 enterprise 고객 유치 시 RPO 1h / RTO 4h SLA 정합 + Seoul region disaster 시 backup restoration 불가 (Phase 4 single-region honest-extreme risk) verbatim 해소 + multi-region 자동 failover 으로 production availability 보강 + capability matrix v1.29 EXTENSION 2 NEW gates industry-agnostic 4-industry grants 모두 production-grade 로 동작 + D-PHASE-4-DR-DEFER-1/2 honestly RESOLVE 결정 wire + Epic 1 ~ Epic 16 + Phase 3 + Phase 4 + 1st release cycle 정합 보존**합니다.

## Acceptance Criteria

PRD §F20.1 ~ §F20.7 verbatim + AD-31 verbatim + Phase 5 PRD entry (commit `93d852b`) §F20.7 wire scope T1~T8 결정 verbatim.

### F20.1 Cross-region read replica + WAL archiving (A126 결정, AD-31 (a) verbatim)

- [ ] **AC1.1** `apps/api/alembic/versions/0039_phase_5_multi_region_backup.py` NEW (~+120 LOC, atomic) — `phase_5_replication_lag` table 신규 (PRD §F20.1 verbatim): 8 columns = `id` (BIGSERIAL PK) + `replica_region` (TEXT NOT NULL, replica_region enum: seoul/tokyo/singapore/frankfurt/virginia/oregon/sao_paulo) + `primary_region` (TEXT NOT NULL) + `lag_bytes` (BIGINT NOT NULL) + `lag_seconds` (INTEGER NOT NULL) + `last_synced_lsn` (TEXT, PG_LSN) + `last_synced_at` (TIMESTAMPTZ NOT NULL DEFAULT NOW()) + `replication_status` (TEXT NOT NULL, replication_status enum: syncing/replicating/lagged/disconnected/failed).
- [ ] **AC1.2** **`phase_5_dr_drill_results` table** 신규 (PRD §F20.3 verbatim) = `id` (BIGSERIAL PK) + `drill_date` (DATE NOT NULL) + `rto_actual_seconds` (INTEGER NOT NULL) + `rpo_actual_bytes` (BIGINT NOT NULL) + `status` (TEXT NOT NULL, status enum: pass/fail) + `notes` (TEXT nullable) + `created_at` (TIMESTAMPTZ NOT NULL DEFAULT NOW()).
- [ ] **AC1.3** **3 indexes** 결정 wire: (a) `idx_phase_5_replication_lag_status` on `(replication_status)` 결정 (b) `idx_phase_5_replication_lag_region_status_time` on `(replica_region, replication_status, last_synced_at DESC)` 결정 (c) `idx_phase_5_replication_lag_created_at` on `(created_at)` 결정. **`phase_5_dr_drill_results` index** = `idx_phase_5_dr_drill_results_drill_date` on `(drill_date DESC)` 결정.
- [ ] **AC1.4** **2 CHECK constraints** (defense-in-depth) = (a) `ck_phase_5_replication_lag_status` (`replication_status IN ('syncing', 'replicating', 'lagged', 'disconnected', 'failed')`) + (b) `ck_phase_5_replication_lag_region` (`replica_region IN ('seoul', 'tokyo', 'singapore', 'frankfurt', 'virginia', 'oregon', 'sao_paulo')`) 결정 wire. **`phase_5_dr_drill_results` CHECK** = `ck_phase_5_dr_drill_results_status` (`status IN ('pass', 'fail')`) 결정.
- [ ] **AC1.5** **down_revision** = `'0038_epic_16_tenant_idps'` 결정 wire (Epic 16 wire `e117e09` alembic 0038 down_revision chain 정합). revision = `'0039_phase_5_multi_region_backup'`.
- [ ] **AC1.6** **system-only tables (CR 0-2 RLS lesson 적용 — replication metadata)** = `phase_5_replication_lag` + `phase_5_dr_drill_results` 모두 RLS 미적용 결정 wire (system-only tables, Epic 13/14 LISTEN/NOTIFY system table pattern 미러). Service role 만 INSERT/UPDATE/SELECT 가능 결정 wire (anon + authenticated 차단).
- [ ] **AC1.7** **audit-first INSERT `replica_status_changed` (CR 1-1 verbatim)** = `audit_logs` table INSERT per replication status change: `action_class='INFRA'` (신규 ActionClass 결정 wire, AD-31 (a) verbatim) + `action='replica_status_changed'` + `actor_id='system'` + `region` (replica_region) + `previous_status` + `new_status` + `trace_id` 결정. Alembic 0039 trigger 자동 호출 결정 wire.
- [ ] **AC1.8** **WAL archiving 결정** (PRD §F20.1 verbatim, Supabase managed 결정 wire) = `postgresql.conf` `archive_mode = on` + `archive_command = 'pgbackrest --stanza=costmgr archive-push %p'` + `wal_level = replica` 결정 wire 보류 (Supabase managed 결정 wire, bmad-dev-story 진입 시점에 결정).
- [ ] **AC1.9** `docs/cross-region-replication.md` NEW (~+120 LOC, atomic) — purpose + Supabase multi-region setup 결정 + replica region 선택 (Tokyo 결정 wire 1st choice: latency Seoul-Tokyo ~50ms vs Singapore ~70ms vs Frankfurt ~250ms, AD-9 Seoul region 정합) + replication lag monitoring 결정 (lag_bytes threshold 100MB + lag_seconds threshold 30s → alert 결정) + WAL archiving setup 결정 + Supabase pgbackrest 또는 barman 결정 wire 보류.

### F20.2 Cross-region failover automation (A126 결정, AD-31 (b) verbatim)

- [ ] **AC2.1** `apps/api/jobs/failover_orchestrator.py` NEW (~+200 LOC, atomic) — primary → secondary health probe + automatic promotion 결정 wire.
- [ ] **AC2.2** **Health probe** 결정 wire (PRD §F20.2 verbatim): primary region 의 `/api/v1/health/ready` endpoint + secondary region 의 `/api/v1/health/ready` endpoint 5-second interval 확인, **3 consecutive failures → failover candidate** 결정. Health probe 결과 log 결정 wire (`phase_5_replication_lag` table INSERT 결정 + `last_synced_at` 갱신 결정).
- [ ] **AC2.3** **Automatic promotion** 결정 wire (PRD §F20.2 verbatim): secondary region 의 PostgreSQL promote decision via Supabase API `POST /v1/projects/{ref}/database/promote` 결정 wire 보류 (Phase 5 atomic wire 진입 시점에 결정) + read-only mode 해제 + connection pool redirect 결정.
- [ ] **AC2.4** **DNS update via Supabase API** 결정 wire (PRD §F20.2 verbatim): failover 결정 wire 진입 시점에 Supabase project URL 의 custom domain redirect 결정 wire (Supabase custom domain 결정 wire 보류, bmad-dev-story 진입 시점에 결정).
- [ ] **AC2.5** **RTO 30-second target** 결정 wire (PRD §F20.2 verbatim) — manual failover 5min → automatic failover 30s 결정 wire (single-region RTO 1h → multi-region 30s RTO 결정 wire, Phase 4 honest-extreme risk 해소).
- [ ] **AC2.6** **failover trigger 3종** 결정 wire (PRD §F20.2 verbatim): (a) health probe 3 consecutive failures OR (b) manual trigger via `POST /api/v1/admin/failover` (owner-only, AD-22 RBAC 결정 wire + 2FA 챌린지 Epic 12 정합) OR (c) scheduled drill via `apps/api/jobs/dr_drill.py` cron 결정 wire.
- [ ] **AC2.7** **audit-first INSERT 2 NEW (CR 1-1 verbatim)** 결정 wire (PRD §F20.2 verbatim): `audit_logs` table INSERT per failover: `action_class='INFRA'` + `action='failover_initiated'` + `actor_id` + `from_region` + `to_region` + `trace_id` (failover_initiated) + `action='failover_completed'` + `actor_id` + `from_region` + `to_region` + `rto_actual_seconds` + `trace_id` (failover_completed).
- [ ] **AC2.8** **`apps/api/main.py` EXTENSION** (PRD §F20.2 verbatim, FastAPI lifespan hook 결정): FastAPI startup 에서 failover_orchestrator 백그라운드 task 시작 + shutdown 에서 task cancel 결정 wire. **GRACEFUL_SHUTDOWN_TIMEOUT=30s** 결정 wire (in-flight requests 30s 대기 결정).
- [ ] **AC2.9** **`POST /api/v1/admin/failover` route** (PRD §F20.2 verbatim, owner-only manual trigger) = `apps/api/modules/admin/failover_routes.py` NEW (~+80 LOC, atomic) — `Depends(require_role("owner"))` + `Depends(require_capability(Capability.MULTI_REGION_FAILOVER))` + 2FA 챌린지 Epic 12 정합 (`require_totp_verified()` Dependency) + body schema `{target_region: str, drill: bool = False}` + audit-first INSERT `failover_initiated` 결정.
- [ ] **AC2.10** **error envelope (CR 12-5 D-14 typed exception envelope verbatim)** 결정 wire — 3 NEW error classes: `FailoverInProgressError` (`code='FAILOVER_IN_PROGRESS_KO'` + `message_ko='이미 failover 가 진행 중입니다'` + 409) + `FailoverTargetUnhealthyError` (`code='FAILOVER_TARGET_UNHEALTHY_KO'` + `message_ko='대상 region 이 healthy 하지 않습니다'` + 503) + `FailoverTimeoutError` (`code='FAILOVER_TIMEOUT_KO'` + `message_ko='failover 가 30초 이내 완료되지 않았습니다'` + 504).

### F20.3 DR drill + automated quarterly test (A126 결정, AD-31 (c) verbatim)

- [ ] **AC3.1** `apps/api/jobs/dr_drill.py` NEW (~+150 LOC, atomic) — cron KST 1st Sunday 03:00 = UTC 18:00 결정 wire (PRD §F20.3 verbatim). **Actual failover drill test in staging** 결정 wire (production 환경 직접 failover 위험 회피, staging 환경에서 drill 결정).
- [ ] **AC3.2** **6 drill steps** 결정 wire (PRD §F20.3 verbatim): (1) staging primary health check + (2) staging secondary promote trigger + (3) staging database connection write test + (4) staging application health check + (5) staging DNS update test + (6) staging primary restore trigger (drill complete marker). 결과 `phase_5_dr_drill_results` table INSERT 결정 wire.
- [ ] **AC3.3** **RPO/RTO measurement** 결정 wire (PRD §F20.3 verbatim): drill 시작 시점 → drill 완료 시점 시간 측정 = **RTO actual** 결정. drill 시작 전 마지막 transaction LSN → drill 후 secondary LSN 측정 = **RPO actual** 결정. 결과 `rto_actual_seconds` + `rpo_actual_bytes` 결정.
- [ ] **AC3.4** **Quarterly drill schedule** 결정 wire (PRD §F20.3 verbatim) — Q1 (January) + Q2 (April) + Q3 (July) + Q4 (October) 결정. `docs/database-backup.md` §9 quarterly drill pattern verbatim preserve 결정. cron 표현식 = `0 18 1 1,4,7,10 *` (UTC 18:00, 1st day of January/April/July/October) 결정.
- [ ] **AC3.5** **audit-first INSERT `dr_drill_completed` (CR 1-1 verbatim)** 결정 wire (PRD §F20.3 verbatim): `audit_logs` table INSERT per drill: `action_class='INFRA'` + `action='dr_drill_completed'` + `actor_id='system'` + `rto_actual_seconds` + `rpo_actual_bytes` + `status` (pass/fail) + `drill_date` + `trace_id` 결정.
- [ ] **AC3.6** **dr_drill lifespan hook** 결정 wire — `apps/api/main.py` EXTENSION: FastAPI startup 에서 dr_drill background scheduler 시작 (APScheduler 사용, AD-14 stack pin `apscheduler>=3.10.0`) + shutdown 에서 scheduler shutdown 결정 wire.
- [ ] **AC3.7** **drill failure handling** 결정 wire (PRD §F20.3 verbatim) — drill 실패 시 (status='fail'): (a) Sentry alert 결정 (`sentry_sdk.capture_message(f"DR drill failed: rto_actual={rto_actual_seconds}s, rpo_actual={rpo_actual_bytes} bytes", level="error")`) + (b) Grafana alert routing 결정 + (c) ops oncall notification 결정 (email + Slack webhook 결정 wire 보류).

### F20.4 Cross-region backup strategy (A126 결정, AD-31 (d) verbatim)

- [ ] **AC4.1** `docs/database-backup.md` EXTENSION (PRD §F20.4 verbatim, 10 sections → 12 sections 결정 wire) = (existing 10 sections: purpose + PITR strategy + RPO/RTO + restore procedure + disaster recovery + monitoring + retention + quarterly drill testing) + (NEW) §11 cross-region backup strategy + (NEW) §12 cross-region failover runbook.
- [ ] **AC4.2** **§11 cross-region backup strategy section** 결정 wire (PRD §F20.4 verbatim): Supabase PITR primary (Seoul) + Supabase PITR secondary (Tokyo) 결정 + 30일 hot (primary) + 90일 cold (secondary) + 365일 archive (regional) retention decision.
- [ ] **AC4.3** **RPO 1h / RTO 4h SLA** 결정 (PRD §F20.4 verbatim, post-multi-region wire DONE 진입) — Phase 4 single-region RPO 5min/RTO 1h 의 honest-extreme risk = Seoul region disaster 시 backup restoration 불가 verbatim 해소 결정 wire. Multi-region 자동 failover 적용 후: RTO 30s (failover_orchestrator) → RTO 4h SLA (전체 DR scenario, multi-region drill 포함) 결정.
- [ ] **AC4.4** **Cross-region backup vs single-region** 결정 wire (PRD §F20.4 verbatim) — Phase 4 single-region (Supabase Seoul primary + PITR 7일 자동) 의 honest-extreme risk 의 multi-region 해소 결정. Phase 5 multi-region 결정 = primary Seoul + secondary Tokyo 자동 failover + cross-region backup 결정.
- [ ] **AC4.5** **§12 cross-region failover runbook section** 결정 wire — failover_orchestrator trigger 3종 + manual failover owner-only 절차 + Epic 12 2FA 챌린지 보존 + audit log 검증 절차 + Sentry alert routing + Grafana dashboard URL + Slack oncall notification channel 결정.
- [ ] **AC4.6** **`apps/api/jobs/cross_region_backup.py`** 결정 wire 보류 (PRD §F20.4 verbatim, bmad-dev-story 진입 시점에 결정) — Supabase Storage cross-region replication vs AWS S3 cross-region replication 결정 wire 보류. 3 options: Option A Supabase Storage 결정 wire vs Option B AWS S3 결정 wire vs Option C 직접 S3 cross-region replication 결정 wire.
- [ ] **AC4.7** **Encryption at rest + TLS cross-region** 결정 wire (NFR4 PII minimization + AD-14 verbatim) — Supabase managed encryption at rest (AES-256) 결정 + TLS 1.3 cross-region replication 결정 (Supabase managed) + WAL archiving pgbackrest AES-256 encryption 결정 (보류, bmad-dev-story 진입 시점에 결정).

### F20.5 Multi-region health observability (A126 결정, AD-31 (e) verbatim)

- [ ] **AC5.1** `apps/api/core/health.py` EXTENSION (PRD §F20.5 verbatim, multi-region endpoint 결정 wire) — NEW endpoint `GET /api/v1/health/multi-region` returns primary + secondary status array 결정 (CR 12-5 D-14 envelope `{status, primary: {region, status, lag_bytes, lag_seconds, last_synced_at}, secondary: {region, status, lag_bytes, lag_seconds, last_synced_at}, timestamp}`).
- [ ] **AC5.2** **JWT verification probe** 결정 wire (PRD §F20.5 verbatim) — Supabase Auth health probe per-region 결정 (`/auth/v1/health` endpoint 결정 + per-region access token 검증) + multi-region health endpoint에 JWT 검증 추가 결정.
- [ ] **AC5.3** `apps/api/core/observability.py` EXTENSION (PRD §F20.5 verbatim, Sentry breadcrumb failover 결정 wire) — failover_initiated 시 Sentry breadcrumb + alert 결정 wire (`sentry_sdk.capture_message(f"Failover initiated from {from_region} to {to_region}", level="warning")` + Sentry alert routing 결정).
- [ ] **AC5.4** **Grafana multi-region dashboard EXTENSION** 결정 wire (PRD §F20.5 verbatim) — primary + secondary region metrics + replication lag graph 결정 + failover event log 결정. `apps/api/jobs/multi_region_dashboard.py` NEW 결정 wire 보류 (Grafana JSON dashboard export + provisioning).
- [ ] **AC5.5** **`apps/web/app/api/health/multi-region/route.ts`** NEW 결정 wire (~+30 LOC, atomic, PRD §F20.5 verbatim) — Next.js Edge Runtime + force-dynamic + Vercel region 결정 + NextResponse.json envelope 결정 (`{status, primary, secondary, build, region, timestamp}` 결정).
- [ ] **AC5.6** **error envelope (CR 12-5 D-14 typed exception envelope verbatim)** 결정 wire (PRD §F20.5 verbatim) — 2 NEW error classes: `MultiRegionUnavailableError` (`code='MULTI_REGION_UNAVAILABLE_KO'` + `message_ko='multi-region endpoint 가 일시적으로 사용 불가합니다'` + 503) + `MultiRegionDataStaleError` (`code='MULTI_REGION_DATA_STALE_KO'` + `message_ko='replication lag 가 임계치를 초과했습니다'` + 503).

### F20.6 Capability matrix v1.29 EXTENSION 2 NEW rows (A127 결정, AD-31 (f) verbatim)

- [ ] **AC6.1** `apps/api/core/capability.py` MODIFIED — `Capability.MULTI_REGION_BACKUP = "multi_region_backup"` 1 NEW enum 결정 wire + `Capability.MULTI_REGION_FAILOVER = "multi_region_failover"` 1 NEW enum 결정 wire (PRD §F20.6 verbatim, Phase 5 wire 2 NEW rows).
- [ ] **AC6.2** **4-industry grants industry-agnostic ✅/✅/✅/✅** 결정 wire (PRD §F20.6 verbatim + CR 12-1 L4 precedent 미러): manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ (industry-agnostic, DEPLOYMENT_PROD + DEPLOYMENT_DATABASE_BACKUP Phase 4 wire + SSO_ENTERPRISE Epic 15 wire + TENANT_IDP_MANAGEMENT Epic 16 wire + LAUNCH_* 1st release wire + LISTEN_NOTIFY 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire pattern verbatim bind). 4 industry 블록 모두에 `Capability.MULTI_REGION_BACKUP,` + `Capability.MULTI_REGION_FAILOVER,` 추가 결정 wire.
- [ ] **AC6.3** `apps/api/dependencies/capability.py` EXTENSION 결정 wire — `require_capability(MULTI_REGION_BACKUP)` + `require_capability(MULTI_REGION_FAILOVER)` Dependency 2개 신규 (기존 `require_capability()` factory pattern verbatim reuse).
- [ ] **AC6.4** `docs/capability-matrix.md` v1.28 → v1.29 EXTENSION 2 NEW rows 결정 wire (Phase 5 PRD entry `93d852b` 진입 시점에 이미 row 추가됨 보존, capability.py enum 만 wire 진입). `MULTI_REGION_BACKUP` + `MULTI_REGION_FAILOVER` rows industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정.
- [ ] **AC6.5** `tests/integration/test_capability_matrix_v1_29_drift.py` NEW (drift detector, Epic 16 `test_capability_matrix_v1_28_drift.py` + Phase 4 `test_capability_matrix_v1_25_drift.py` 패턴 verbatim bind) — `MULTI_REGION_BACKUP` + `MULTI_REGION_FAILOVER` 2 NEW rows SSOT 정합 sweep (~+10 NEW pytest cases 결정).

### F20.7 tests + wire scope T1~T8 결정 (cj-style 73번째 결정 wire 진입 시점에 적용)

- [ ] **AC7.1** `tests/api/core/test_phase_5_alembic_0039_multi_region_backup.py` NEW (~+12 pytest cases) — alembic 0039 migration code-shape 검증 (Story 9-7 T9 precedent 미러, `re.compile` against migration source) + `phase_5_replication_lag` table schema + 8 columns + 3 indexes + 2 CHECK constraints + `phase_5_dr_drill_results` table schema + 7 columns + 1 index + 1 CHECK constraint + down_revision=`'0038_epic_16_tenant_idps'` 정합 + system-only tables RLS 미적용 검증.
- [ ] **AC7.2** `tests/api/jobs/test_phase_5_failover_orchestrator.py` NEW (~+18 pytest cases) — failover_orchestrator: (1) primary health probe 5-second interval / (2) 3 consecutive failures trigger failover / (3) secondary promotion via Supabase API / (4) DNS update via Supabase custom domain / (5) RTO 30-second target enforcement / (6) audit-first INSERT `failover_initiated` / (7) audit-first INSERT `failover_completed` / (8) GRACEFUL_SHUTDOWN_TIMEOUT=30s / (9) FastAPI lifespan hook startup/shutdown / (10) manual trigger `POST /api/v1/admin/failover` owner-only AD-22 / (11) 2FA 챌린지 Epic 12 보존 / (12) FailoverInProgressError 409 / (13) FailoverTargetUnhealthyError 503 / (14) FailoverTimeoutError 504.
- [ ] **AC7.3** `tests/api/jobs/test_phase_5_dr_drill.py` NEW (~+15 pytest cases) — dr_drill: (1) cron KST 1st Sunday 03:00 = UTC 18:00 expression / (2) 6 drill steps sequence / (3) RPO/RTO measurement / (4) `phase_5_dr_drill_results` table INSERT / (5) Q1/Q2/Q3/Q4 quarterly schedule / (6) audit-first INSERT `dr_drill_completed` / (7) APScheduler lifespan hook / (8) drill failure Sentry alert / (9) production 환경 직접 failover 위험 회피 (staging only).
- [ ] **AC7.4** `tests/api/core/test_phase_5_multi_region_health.py` NEW (~+10 pytest cases) — `apps/api/core/health.py` EXTENSION `/api/v1/health/multi-region` endpoint: (1) primary + secondary status array / (2) CR 12-5 D-14 envelope `{status, primary, secondary, timestamp}` / (3) JWT verification probe per-region / (4) replication lag threshold check / (5) MultiRegionUnavailableError 503 / (6) MultiRegionDataStaleError 503.
- [ ] **AC7.5** `tests/api/core/test_phase_5_audit_log_verification.py` NEW (~+10 pytest cases) — audit-first INSERT 4 NEW 검증: (1) `replica_status_changed` audit row 검증 / (2) `failover_initiated` audit row 검증 / (3) `failover_completed` audit row 검증 / (4) `dr_drill_completed` audit row 검증 / (5) audit actor_id 정확성 (`system` for replica + drill, `actor_user_id` for manual failover) / (6) `from_region` + `to_region` + `rto_actual_seconds` 정확성.
- [ ] **AC7.6** `tests/integration/test_capability_matrix_v1_29_drift.py` NEW (drift detector, P-015 SSOT drift detector + Epic 16 v1.28 precedent verbatim) — `MULTI_REGION_BACKUP` + `MULTI_REGION_FAILOVER` 2 NEW rows SSOT 정합 sweep (industry-agnostic 4-industry grants ✅/✅/✅/✅).
- [ ] **AC7.7** `tests/web/test_phase_5_multi_region_health_parity.test.ts` NEW (~+10 vitest cases) — `apps/web/app/api/health/multi-region/route.ts` Edge Runtime RTL render: (1) NextResponse.json envelope parity / (2) force-dynamic + Vercel region / (3) primary + secondary status array / (4) CR 12-5 D-14 envelope parsing / (5) build + region + timestamp fields.
- [ ] **AC7.8** `docs/multi-region-backup.md` NEW (~+150 LOC, 8 sections) — purpose + Supabase multi-region setup + cross-region replication + failover_orchestrator architecture + dr_drill cron + RPO/RTO SLA + multi-region health observability + capability matrix v1.29 + audit-first INSERT 4 NEW + Epic 4 carry-over 참고.
- [ ] **AC7.9** `docs/cross-region-replication.md` NEW (~+120 LOC, atomic) — purpose + Supabase multi-region setup + replica region 선택 Tokyo 1st choice + replication lag monitoring lag_bytes 100MB / lag_seconds 30s + WAL archiving setup + Supabase pgbackrest 결정 wire 보류.
- [ ] **AC7.10** `docs/database-backup.md` EXTENSION (10 sections → 12 sections) — §11 cross-region backup strategy + §12 cross-region failover runbook 결정.
- [ ] **AC7.11** `apps/api/core/audit_action.py` MODIFIED — `ActionClass.INFRA = "infra"` 1 NEW enum 결정 wire (F20.1~F20.3 audit-first INSERT 4 NEW 의 action_class 결정, AD-31 (a)~(c) verbatim) + registry entry frozenset 4 actions: `replica_status_changed` + `failover_initiated` + `failover_completed` + `dr_drill_completed` 결정.
- [ ] **AC7.12** `apps/api/main.py` MODIFIED — failover_orchestrator lifespan hook + dr_drill APScheduler lifespan hook EXTENSION 결정 wire.
- [ ] **AC7.13** `apps/api/pyproject.toml` MODIFIED — `apscheduler>=3.10.0` AD-14 stack pin 결정 wire (dr_drill cron job 용).
- [ ] **AC7.14** **3중 게이트 FINAL CLEAN** 결정 wire — (1) `pnpm tsc --noEmit` 0 NEW errors (Phase 5 frontend files clean — pre-existing 19 baseline errors unrelated 보존) / (2) `pnpm vitest run` 100+10 = **~110/110 PASS** (Phase 5 +10 NEW vitest cases, 0 regressions) / (3) `ruff check` scoped Phase 5 wire files = **All checks passed!** (scoped to Phase 5 NEW Python files only) / (4) `pytest` 4162+50 = **~4212/4212 PASS** (Phase 5 +50 NEW pytest e2e tests, 0 NEW regressions; baseline 1 unrelated pre-existing failure 보존) / (5) SDR drift gate PASS (MAX claim 4162 → **~4212** actual pytest --collect-only -q = +50 from Phase 5 T7~T8 NEW pytest cases).
- [ ] **AC7.15** **A36 SDR 검증 4-step 자동 적용 PASS** 결정 wire — (1) commit prefix lint (CR 9-6 D5 prevention, `git commit -F <file>`) / (2) sprint-status structure 정합 (D4 fix 보존) / (3) vitest file count drift 0건 (D2 fix 보존) / (4) commit consistency 정합 (D1 fix 보존).
- [ ] **AC7.16** atomic commit + sprint-status `phase-5-multi-region-backup-wire: backlog → done` + handoff memory 신규 + `docs/multi-region-backup.md` NEW + `docs/cross-region-replication.md` NEW + `docs/database-backup.md` EXTENSION + `apps/web/app/api/health/multi-region/route.ts` NEW + atomic 12-15 files 결정 wire 진입.

## Tasks / Subtasks

- [ ] **Task 1 — T1: phase_5_replication_lag + phase_5_dr_drill_results tables + alembic 0039 wire** (AC: #1.1, #1.2, #1.3, #1.4, #1.5, #1.6, #1.7, #1.8, #1.9, #7.1, #7.11, #7.13)
  - [ ] Subtask 1.1 — `apps/api/alembic/versions/0039_phase_5_multi_region_backup.py` NEW (~+120 LOC): `phase_5_replication_lag` table 8 columns 결정 wire (id + replica_region + primary_region + lag_bytes + lag_seconds + last_synced_lsn + last_synced_at + replication_status)
  - [ ] Subtask 1.2 — `phase_5_dr_drill_results` table 7 columns 결정 wire (id + drill_date + rto_actual_seconds + rpo_actual_bytes + status + notes + created_at)
  - [ ] Subtask 1.3 — replica_region enum 7 regions (seoul/tokyo/singapore/frankfurt/virginia/oregon/sao_paulo) + replication_status enum 5 states (syncing/replicating/lagged/disconnected/failed) + status enum (pass/fail) 결정 wire
  - [ ] Subtask 1.4 — 3 indexes (status + region+status+last_synced_at DESC + created_at) + 1 index (drill_date DESC) + 2 CHECK constraints + 1 CHECK constraint 결정 wire (AC1.3+AC1.4 verbatim)
  - [ ] Subtask 1.5 — system-only tables RLS 미적용 결정 wire (CR 0-2 RLS lesson verbatim, Epic 13/14 LISTEN/NOTIFY system table pattern 미러) — service_role 만 INSERT/UPDATE/SELECT 가능
  - [ ] Subtask 1.6 — audit-first INSERT `replica_status_changed` trigger 자동 호출 결정 wire (CR 1-1 verbatim, ActionClass.INFRA 신규)
  - [ ] Subtask 1.7 — down_revision = `'0038_epic_16_tenant_idps'` 결정 wire (Epic 16 wire `e117e09` alembic 0038 chain 정합)
  - [ ] Subtask 1.8 — `apps/api/core/audit_action.py` MODIFIED: `ActionClass.INFRA = "infra"` 1 NEW enum + 4 NEW actions (replica_status_changed + failover_initiated + failover_completed + dr_drill_completed) 결정 wire
  - [ ] Subtask 1.9 — `apps/api/pyproject.toml` MODIFIED: WAL archiving 결정 wire 보류 (Supabase managed, bmad-dev-story 진입 시점에 결정)
  - [ ] Subtask 1.10 — `tests/api/core/test_phase_5_alembic_0039_multi_region_backup.py` NEW (~+12 pytest cases) — alembic 0039 code-shape 검증 결정 wire
  - [ ] Subtask 1.11 — `docs/cross-region-replication.md` NEW (~+120 LOC, atomic) — purpose + Supabase multi-region setup + replica region 선택 Tokyo 1st choice + replication lag monitoring 결정 wire

- [ ] **Task 2 — T2: Cross-region failover automation + failover_orchestrator wire** (AC: #2.1, #2.2, #2.3, #2.4, #2.5, #2.6, #2.7, #2.8, #2.9, #2.10, #7.2, #7.11, #7.12)
  - [ ] Subtask 2.1 — `apps/api/jobs/failover_orchestrator.py` NEW (~+200 LOC): primary → secondary health probe 5-second interval + 3 consecutive failures trigger 결정 wire
  - [ ] Subtask 2.2 — automatic promotion via Supabase API `POST /v1/projects/{ref}/database/promote` 결정 wire 보류 (Phase 5 atomic wire 진입 시점에 결정)
  - [ ] Subtask 2.3 — DNS update via Supabase project URL custom domain redirect 결정 wire 보류 (bmad-dev-story 진입 시점에 결정)
  - [ ] Subtask 2.4 — RTO 30-second target 결정 wire (manual failover 5min → automatic failover 30s, Phase 4 single-region RTO 1h → multi-region 30s RTO)
  - [ ] Subtask 2.5 — failover trigger 3종 결정 wire: (a) health probe 3 consecutive failures OR (b) manual trigger `POST /api/v1/admin/failover` owner-only AD-22 + 2FA 챌린지 Epic 12 정합 OR (c) scheduled drill via dr_drill cron
  - [ ] Subtask 2.6 — audit-first INSERT `failover_initiated` + `failover_completed` 2 NEW 결정 wire (CR 1-1 verbatim, ActionClass.INFRA)
  - [ ] Subtask 2.7 — `apps/api/main.py` EXTENSION: FastAPI lifespan hook startup/shutdown 결정 wire + GRACEFUL_SHUTDOWN_TIMEOUT=30s
  - [ ] Subtask 2.8 — `apps/api/modules/admin/failover_routes.py` NEW (~+80 LOC): `POST /api/v1/admin/failover` route — owner-only AD-22 + 2FA 챌린지 Epic 12 + `Depends(require_capability(Capability.MULTI_REGION_FAILOVER))` + body `{target_region, drill}` + audit-first INSERT
  - [ ] Subtask 2.9 — 3 NEW error classes (CR 12-5 D-14 envelope verbatim): FailoverInProgressError 409 + FailoverTargetUnhealthyError 503 + FailoverTimeoutError 504
  - [ ] Subtask 2.10 — `tests/api/jobs/test_phase_5_failover_orchestrator.py` NEW (~+18 pytest cases) — 14 verification steps + 3 error envelope tests 결정 wire

- [ ] **Task 3 — T3: DR drill + automated quarterly test + dr_drill wire** (AC: #3.1, #3.2, #3.3, #3.4, #3.5, #3.6, #3.7, #7.3, #7.11, #7.12, #7.13)
  - [ ] Subtask 3.1 — `apps/api/jobs/dr_drill.py` NEW (~+150 LOC): cron KST 1st Sunday 03:00 = UTC 18:00 결정 wire (`0 18 1 1,4,7,10 *` cron expression)
  - [ ] Subtask 3.2 — 6 drill steps 결정 wire: (1) staging primary health check + (2) staging secondary promote trigger + (3) staging database connection write test + (4) staging application health check + (5) staging DNS update test + (6) staging primary restore trigger
  - [ ] Subtask 3.3 — RPO/RTO measurement decision: drill 시작 시점 → drill 완료 시점 시간 측정 = RTO actual, drill 시작 전 마지막 transaction LSN → drill 후 secondary LSN 측정 = RPO actual
  - [ ] Subtask 3.4 — `phase_5_dr_drill_results` table INSERT 결정 wire (id + drill_date + rto_actual_seconds + rpo_actual_bytes + status + notes + created_at)
  - [ ] Subtask 3.5 — Q1/Q2/Q3/Q4 quarterly schedule 결정 wire (January + April + July + October, docs/database-backup.md §9 quarterly drill pattern verbatim preserve)
  - [ ] Subtask 3.6 — audit-first INSERT `dr_drill_completed` 결정 wire (CR 1-1 verbatim, ActionClass.INFRA, actor_id='system')
  - [ ] Subtask 3.7 — `apps/api/main.py` EXTENSION: dr_drill APScheduler background scheduler lifespan hook startup/shutdown 결정 wire
  - [ ] Subtask 3.8 — drill failure handling 결정 wire: Sentry alert + Grafana alert routing + ops oncall notification (Slack webhook 결정 wire 보류)
  - [ ] Subtask 3.9 — `apps/api/pyproject.toml` MODIFIED: `apscheduler>=3.10.0` AD-14 stack pin 결정 wire
  - [ ] Subtask 3.10 — `tests/api/jobs/test_phase_5_dr_drill.py` NEW (~+15 pytest cases) — 9 verification steps + 6 Sentry/Grafana/oncall failure handling tests 결정 wire

- [ ] **Task 4 — T4: Cross-region backup strategy + docs EXTENSION wire** (AC: #4.1, #4.2, #4.3, #4.4, #4.5, #4.6, #4.7, #7.8, #7.9, #7.10)
  - [ ] Subtask 4.1 — `docs/database-backup.md` EXTENSION (10 sections → 12 sections 결정 wire) — §11 cross-region backup strategy + §12 cross-region failover runbook 신규
  - [ ] Subtask 4.2 — §11 cross-region backup strategy section 결정 wire: Supabase PITR primary (Seoul) + Supabase PITR secondary (Tokyo) + 30일 hot (primary) + 90일 cold (secondary) + 365일 archive (regional) retention
  - [ ] Subtask 4.3 — RPO 1h / RTO 4h SLA 결정 wire (post-multi-region wire DONE 진입, Phase 4 single-region RPO 5min/RTO 1h honest-extreme risk verbatim 해소)
  - [ ] Subtask 4.4 — §12 cross-region failover runbook section 결정 wire: failover_orchestrator trigger 3종 + manual failover owner-only 절차 + Epic 12 2FA 챌린지 보존 + audit log 검증 + Sentry alert + Grafana dashboard + Slack oncall
  - [ ] Subtask 4.5 — `apps/api/jobs/cross_region_backup.py` 결정 wire 보류 (bmad-dev-story 진입 시점에 결정 — Option A Supabase Storage vs Option B AWS S3 vs Option C 직접 S3 cross-region replication)
  - [ ] Subtask 4.6 — Encryption at rest + TLS cross-region 결정 wire (NFR4 PII minimization + AD-14 verbatim): Supabase managed AES-256 + TLS 1.3 + WAL archiving pgbackrest AES-256 (보류)
  - [ ] Subtask 4.7 — `docs/multi-region-backup.md` NEW (~+150 LOC, 8 sections) — purpose + Supabase multi-region setup + cross-region replication + failover_orchestrator architecture + dr_drill cron + RPO/RTO SLA + multi-region health observability + capability matrix v1.29 + audit-first INSERT 4 NEW

- [ ] **Task 5 — T5: Multi-region health observability wire** (AC: #5.1, #5.2, #5.3, #5.4, #5.5, #5.6, #7.4, #7.5, #7.7)
  - [ ] Subtask 5.1 — `apps/api/core/health.py` EXTENSION: NEW endpoint `GET /api/v1/health/multi-region` returns primary + secondary status array (CR 12-5 D-14 envelope `{status, primary, secondary, timestamp}`)
  - [ ] Subtask 5.2 — JWT verification probe per-region 결정 wire (`/auth/v1/health` endpoint + per-region access token 검증)
  - [ ] Subtask 5.3 — `apps/api/core/observability.py` EXTENSION: Sentry breadcrumb failover (`sentry_sdk.capture_message(f"Failover initiated from {from_region} to {to_region}", level="warning")` + Sentry alert routing)
  - [ ] Subtask 5.4 — Grafana multi-region dashboard EXTENSION 결정 wire (primary + secondary region metrics + replication lag graph + failover event log) — `apps/api/jobs/multi_region_dashboard.py` NEW 결정 wire 보류
  - [ ] Subtask 5.5 — `apps/web/app/api/health/multi-region/route.ts` NEW (~+30 LOC, atomic, Next.js Edge Runtime + force-dynamic + Vercel region + NextResponse.json envelope)
  - [ ] Subtask 5.6 — 2 NEW error classes (CR 12-5 D-14 envelope verbatim): MultiRegionUnavailableError 503 + MultiRegionDataStaleError 503
  - [ ] Subtask 5.7 — `tests/api/core/test_phase_5_multi_region_health.py` NEW (~+10 pytest cases) — 6 verification steps
  - [ ] Subtask 5.8 — `tests/web/test_phase_5_multi_region_health_parity.test.ts` NEW (~+10 vitest cases) — NextResponse.json envelope parity + force-dynamic + Vercel region

- [ ] **Task 6 — T6: Capability matrix v1.28 → v1.29 EXTENSION 2 NEW rows wire** (AC: #6.1, #6.2, #6.3, #6.4, #6.5, #7.6)
  - [ ] Subtask 6.1 — `apps/api/core/capability.py` MODIFIED: `Capability.MULTI_REGION_BACKUP = "multi_region_backup"` + `Capability.MULTI_REGION_FAILOVER = "multi_region_failover"` 2 NEW enum 결정 wire
  - [ ] Subtask 6.2 — 4-industry grants industry-agnostic ✅/✅/✅/✅ (manufacturing + service + manufacturing_service + manufacturing_service_other, CR 12-1 L4 precedent 미러)
  - [ ] Subtask 6.3 — `apps/api/dependencies/capability.py` EXTENSION: `require_capability(MULTI_REGION_BACKUP)` + `require_capability(MULTI_REGION_FAILOVER)` Dependency 2개 신규
  - [ ] Subtask 6.4 — `docs/capability-matrix.md` v1.28 → v1.29 EXTENSION 2 NEW rows (Phase 5 PRD entry `93d852b` 진입 시점에 이미 row 추가됨 보존)
  - [ ] Subtask 6.5 — `tests/integration/test_capability_matrix_v1_29_drift.py` NEW (drift detector, P-015 SSOT drift detector, Epic 16 v1.28 + Phase 4 v1.25 패턴 verbatim bind) — 2 NEW rows SSOT 정합 sweep

- [ ] **Task 7 — T7: Tests + audit log verification + 3중 게이트** (AC: #7.1, #7.2, #7.3, #7.4, #7.5, #7.6, #7.7, #7.8, #7.9, #7.10, #7.11, #7.12, #7.13, #7.14, #7.15)
  - [ ] Subtask 7.1 — `tests/api/core/test_phase_5_audit_log_verification.py` NEW (~+10 pytest cases) — audit-first INSERT 4 NEW 검증: replica_status_changed + failover_initiated + failover_completed + dr_drill_completed
  - [ ] Subtask 7.2 — `tests/integration/test_phase_5_multi_region_integration.py` NEW (~+5 pytest cases) — end-to-end multi-region scenario
  - [ ] Subtask 7.3 — 3중 게이트 FINAL CLEAN verification: ruff scoped Phase 5 wire Python files = All checks passed! / pytest 50 NEW PASS / vitest 10 NEW PASS / pnpm tsc --noEmit 0 NEW errors / SDR drift gate PASS / commit_consistency PASS
  - [ ] Subtask 7.4 — A36 SDR 검증 4-step 자동 적용: commit prefix lint + sprint-status structure + vitest file count drift 0건 + commit consistency 정합

- [ ] **Task 8 — T8: 3중 게이트 FINAL CLEAN + atomic commit** (AC: #7.14, #7.15, #7.16)
  - [ ] Subtask 8.1 — Final wire scope 정합 sweep: T1 alembic 0039 + T2 failover_orchestrator + failover_routes + T3 dr_drill + T4 docs EXTENSION + T5 multi-region health + T6 Capability v1.29 EXTENSION + T7 Tests = 12-15 files atomic single sprint
  - [ ] Subtask 8.2 — `git commit -F <file>` (CR 9-6 D5 prevention, commit-msg file 신규 = `_bmad-output/implementation-artifacts/commit-msg-phase-5-multi-region-backup-wire.txt`)
  - [ ] Subtask 8.3 — handoff memory 신규 = `memory/handoff-2026-08-22-phase-5-multi-region-backup-wire-done.md`
  - [ ] Subtask 8.4 — sprint-status `phase-5-multi-region-backup-wire: backlog → done` + sprint-status structure 정합

## Dev Notes

### Source Tree Components to Touch

- **NEW (10 files)**:
  - `apps/api/alembic/versions/0039_phase_5_multi_region_backup.py` (~+120 LOC) — T1
  - `apps/api/jobs/failover_orchestrator.py` (~+200 LOC) — T2
  - `apps/api/jobs/dr_drill.py` (~+150 LOC) — T3
  - `apps/api/modules/admin/failover_routes.py` (~+80 LOC) — T2
  - `apps/web/app/api/health/multi-region/route.ts` (~+30 LOC) — T5
  - `docs/multi-region-backup.md` (~+150 LOC) — T4
  - `docs/cross-region-replication.md` (~+120 LOC) — T1
  - `tests/api/core/test_phase_5_alembic_0039_multi_region_backup.py` (~+12 pytest cases) — T1
  - `tests/api/jobs/test_phase_5_failover_orchestrator.py` (~+18 pytest cases) — T2
  - `tests/api/jobs/test_phase_5_dr_drill.py` (~+15 pytest cases) — T3
  - `tests/api/core/test_phase_5_multi_region_health.py` (~+10 pytest cases) — T5
  - `tests/api/core/test_phase_5_audit_log_verification.py` (~+10 pytest cases) — T7
  - `tests/integration/test_capability_matrix_v1_29_drift.py` (~+10 pytest cases) — T6
  - `tests/integration/test_phase_5_multi_region_integration.py` (~+5 pytest cases) — T7
  - `tests/web/test_phase_5_multi_region_health_parity.test.ts` (~+10 vitest cases) — T5
  - `memory/handoff-2026-08-22-phase-5-multi-region-backup-wire-done.md` (NEW handoff memory) — T8
  - `_bmad-output/implementation-artifacts/commit-msg-phase-5-multi-region-backup-wire.txt` (NEW commit-msg file) — T8

- **MODIFIED (5 files)**:
  - `apps/api/main.py` — failover_orchestrator + dr_drill lifespan hook EXTENSION
  - `apps/api/core/health.py` — multi-region endpoint EXTENSION
  - `apps/api/core/observability.py` — Sentry breadcrumb failover EXTENSION
  - `apps/api/core/audit_action.py` — ActionClass.INFRA + 4 NEW actions
  - `apps/api/core/capability.py` — MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER 2 NEW enum
  - `apps/api/dependencies/capability.py` — require_capability Dependency 2개 EXTENSION
  - `apps/api/pyproject.toml` — apscheduler>=3.10.0 AD-14 stack pin
  - `docs/database-backup.md` — EXTENSION 10 sections → 12 sections
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` — phase-5-multi-region-backup-wire: backlog → done + A129~A133 action_items
  - `MEMORY.md` — handoff index EXTENSION

**Total wire scope (cj-style 75번째 expected)**: ~12-15 NEW files + ~5-7 MODIFIED files = ~17-22 files atomic single sprint.

### Architecture Compliance

- **CR 0-2 RLS lesson** ✅ APPLIED (system-only tables replication metadata: phase_5_replication_lag + phase_5_dr_drill_results RLS 미적용 결정 wire, Epic 13/14 LISTEN/NOTIFY system table pattern 미러)
- **CR 1-1 audit-first INSERT** ✅ APPLIED (audit-first INSERT 4 NEW 결정 wire: replica_status_changed + failover_initiated + failover_completed + dr_drill_completed, CR 1-1 verbatim, ActionClass.INFRA 신규)
- **CR 9-6 commit message discipline** ✅ APPLIED (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention)
- **CR 11-3 honest-DEFER discipline** ✅ APPLIED (74번째 epic 연속 정직 회복, D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVE 진입 wire 결정 + D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존 60~74번째 + D-EPIC-16-REVIEW-DEFER-2~6 (H8+M5+M7+M9+L11) honestly DEFERRED 5 OPEN 보존 70~74번째)
- **CR 12-1 L4 industry-agnostic capability** ✅ APPLIED (capability matrix v1.29 EXTENSION 2 NEW rows MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER industry-agnostic 4-industry grants ✅/✅/✅/✅)
- **CR 12-5 D-14 typed exception envelope** ✅ APPLIED (5 NEW error classes 결정 wire: FailoverInProgressError + FailoverTargetUnhealthyError + FailoverTimeoutError + MultiRegionUnavailableError + MultiRegionDataStaleError)
- **CR 12-5 D-PARITY-01 inversion** ✅ APPLIED (Python FastAPI backend `/api/v1/health/multi-region` + TypeScript Next.js Edge Runtime `/api/health/multi-region` parity 결정 wire)
- **CR 12-5 D-GATE-01 inversion** ✅ APPLIED (capability gate MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER per-tenant on/off + manual failover trigger owner-only RBAC AD-22)
- **A19 cohesion pattern 9 surface EXTENSION PASS** ✅ (multi-region surface NEW = F20.1~F20.5 multi-region backup & disaster recovery territory)
- **A36 SDR 검증 4-step 자동 적용** ✅ (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS)
- **AD-14 stack pin** ✅ APPLIED (apscheduler>=3.10.0 + lxml>=5.0.0 + python3-saml==1.16.0 + Supabase managed 결정 wire)
- **AD-22 owner-only RBAC** ✅ APPLIED (manual failover `POST /api/v1/admin/failover` owner-only 결정 + Epic 12 2FA 챌린지 보존)
- **NFR4 PII minimization** ✅ APPLIED (audit_log cert SHA-256 fingerprint NOT raw cert, encryption at rest Supabase managed)

### Library / Framework Requirements

- **apscheduler>=3.10.0** (AD-14 stack pin) — dr_drill cron job background scheduler
- **lxml>=5.0.0** (carry-over from Epic 16 wire, AD-14 stack pin) — optional XML schema validation for cross-region replication metadata
- **python3-saml==1.16.0** (carry-over from Epic 15 wire, AD-14 stack pin)
- **httpx>=0.27.0** (carry-over) — Supabase API call for failover (POST /v1/projects/{ref}/database/promote)
- **sentry-sdk[fastapi]>=2.10.0** (carry-over from Phase 4 wire) — Sentry breadcrumb failover

### File Structure Requirements

- `apps/api/jobs/` (NEW directory sibling to `apps/api/modules/`, `apps/api/core/`) — for background jobs (failover_orchestrator + dr_drill)
- `apps/api/modules/admin/` (NEW directory) — for admin routes (failover_routes.py)
- `tests/api/jobs/` (NEW directory) — for background job tests
- `docs/multi-region-backup.md` + `docs/cross-region-replication.md` (NEW docs) — multi-region runbook + replication setup
- `docs/database-backup.md` EXTENSION — §11 + §12 신규 sections
- `apps/web/app/api/health/multi-region/route.ts` (NEW) — Next.js Edge Runtime multi-region health

### Testing Standards

- **3중 게이트 FINAL CLEAN** (cj-style 75번째 standard): (1) `pnpm tsc --noEmit` 0 NEW errors / (2) `pnpm vitest run` 100+10 = ~110/110 PASS / (3) `ruff check` scoped Phase 5 wire Python files = All checks passed! / (4) `pytest` 4162+50 = ~4212/4212 PASS / (5) `pytest --collect-only -q` SDR drift gate = MAX claim 4162 → ~4212 actual (no SDR overclaim) / (6) commit_consistency gate PASS (CR 9-6 + A36)
- **Test scope breakdown**: ~50 NEW pytest (12 alembic + 18 failover + 15 dr_drill + 10 health + 10 audit + 10 drift + 5 integration = 80 actual) + ~10 NEW vitest + 1 NEW integration drift + 4 NEW audit log verification
- **A19 cohesion pattern 9 surface EXTENSION PASS** — all 9 surfaces touched (kernel + port + db schema + service + handler + envelope + capability + audit + multi-region surface NEW)

### Project Structure Notes

- Alignment with unified project structure:
  - `apps/api/jobs/` follows `apps/api/modules/auth/sso/` pattern (Epic 15 wire 정합)
  - `apps/api/modules/admin/` follows `apps/api/modules/auth/sso/idp_admin_routes.py` pattern (Epic 16 wire 정합)
  - `tests/api/jobs/` follows `tests/api/core/` pattern (Phase 4 wire 정합)
- Detected conflicts or variances: None — Phase 5 territory fully aligned with existing patterns

### References

- master PRD v3.5 §F20 (Multi-Region Backup & Disaster Recovery territory) — `docs/planning-artifacts/prd.md` lines 1180-1261
- master PRD v3.5 §F20.1 (Cross-region read replica + WAL archiving) — lines 1193-1196
- master PRD v3.5 §F20.2 (Cross-region failover automation) — lines 1198-1201
- master PRD v3.5 §F20.3 (DR drill + automated quarterly test) — lines 1203-1205
- master PRD v3.5 §F20.4 (Cross-region backup strategy) — lines 1207-1210
- master PRD v3.5 §F20.5 (Multi-region health observability) — lines 1212-1215
- master PRD v3.5 §F20.6 (Capability matrix v1.28 → v1.29 EXTENSION) — lines 1217-1220
- master PRD v3.5 §F20.7 (tests + wire scope T1~T8) — lines 1222-1233
- master PRD v3.5 §8.1 M0-(m) (multi-region backup AC) — line 456
- master PRD v3.5 AD-31 (Multi-Region Backup & Disaster Recovery) — line 1611
- master PRD v3.5 §부록 A A124~A128 — lines 1592-1596
- master PRD v3.5 §15 (로드맵 Phase 5 row) — line 1399
- Phase 4 close-out retro §6 disaster recovery honestly-deferred — `docs/implementation-artifacts/phase-4-close-out-2026-08-22.md`
- capability matrix v1.29 — `docs/capability-matrix.md` line 1-7
- Phase 5 PRD entry commit `93d852b` — `git log` reference
- Phase 4 wire `71a033a` (deployment + health check + observability) — `git log` reference
- Phase 4 close-out retro `934b35e` — `git log` reference
- Epic 15 wire `5f9e37f` (sso_enterprise + audit-first INSERT pattern) — `git log` reference
- Epic 16 wire `e117e09` (idp_admin_management + audit-first INSERT 4 NEW pattern) — `git log` reference
- Epic 16 close-out retro `f1ead9a` — `git log` reference
- Epic 12 wire `a63646c` (2FA 게이트 + TOTP chain) — `git log` reference
- A36 SDR verification 4-step (commit prefix lint + sprint-status structure + vitest file count drift + commit consistency) — `memory/cr-a19-lessons.md` carry-over

## Dev Agent Record

### Agent Model Used

`MiniMax-M3` (cj-style 74번째 epic 연속 정직 회복 bmad-create-story spec entry 진입 시점에 결정)

### Debug Log References

N/A (docs only spec entry)

### Completion Notes List

- [x] Phase 5 PRD entry (cj-style 73번째) DONE
- [x] Phase 5 bmad-create-story spec entry (cj-style 74번째) DONE (this document)
- [ ] Phase 5 bmad-dev-story atomic wire T1~T8 (cj-style 75번째) — pending
- [ ] Phase 5 close-out retro (cj-style 76~77번째) — pending

### File List

(To be filled by dev agent during T1~T8 implementation)
