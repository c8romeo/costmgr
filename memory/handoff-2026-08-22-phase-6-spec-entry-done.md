---
name: handoff-2026-08-22-phase-6-spec-entry-done
description: Phase 6 bmad-create-story spec entry DONE (cj-style 86번째) — Audit Log Retention Policy territory spec wire. baseline_commit: e84a281. 7 ACs PRD §F22.1~§F22.7 verbatim + 8 tasks T1~T8 + 66 subtasks + ~34 files estimated wire scope. A198~A202 5/5 ALL DONE 결정 wire.
metadata:
  type: project
---

# Phase 6 bmad-create-story spec entry DONE (cj-style 86번째)

**결정 wire 일자**: 2026-08-22 (KST)
**Phase 6 territory**: Audit Log Retention Policy (retention DSL + automatic purge job + archive storage + GDPR Article 17 erasure)
**cj-style 진입점**: 86번째 epic 연속 정직 회복 atomic docs-only wire

## A198~A202 5/5 ALL DONE 결정 wire

- **A198**: 옵션 (a) Phase 6 bmad-create-story spec entry 진입 결정 wire (cj-style 86번째 epic 연속 정직 회복)
- **A199**: spec 파일 생성 결정 wire = `_bmad-output/implementation-artifacts/phase-6-audit-log-retention-wire.md` (~600 lines, 7 ACs PRD §F22.1~§F22.7 verbatim + 8 tasks T1~T8 + 66 subtasks + Dev Notes + CR lessons applied 14종)
- **A200**: handoff memory 신규 + MEMORY.md hook index EXTENSION
- **A201**: sprint-status 업데이트 + atomic commit
- **A202**: commit-msg file 신규 + `git commit -F <file>` (CR 9-6 D5 prevention)

## Wire scope 결정 wire

5 files atomic single sprint (cj-style 86번째 docs-only wire):
- 1 NEW `_bmad-output/implementation-artifacts/phase-6-audit-log-retention-wire.md` (~600 lines, 7 ACs PRD §F22.1~§F22.7 verbatim + 8 tasks T1~T8 + 66 subtasks)
- 1 NEW `memory/handoff-2026-08-22-phase-6-spec-entry-done.md` (handoff memory 결정 wire)
- 1 MODIFIED `_bmad-output/implementation-artifacts/sprint-status.yaml` (`phase-6-spec-entry: backlog → done` 신규 entry + A198~A202 action_items + last_updated_note prepend)
- 1 MODIFIED `memory/MEMORY.md` (handoff hook index EXTENSION)
- 1 NEW `_bmad-output/implementation-artifacts/commit-msg-phase-6-spec-entry.txt` (CR 9-6 commit message discipline 결정 wire)

= 3 NEW + 2 MODIFIED = 5 files atomic docs-only wire.

## Spec structure 결정 wire (~600 lines)

- YAML frontmatter with `baseline_commit: e84a281` (Phase 6 PRD entry commit)
- Story (As a/I want/so that) with Phase 6 territory verbatim from §F22
- 7 ACs PRD §F22.1~§F22.7 verbatim:
  - §F22.1 retention policy DSL (12 ACs — `RetentionPolicy` TypedDict + `RetentionClass` Literal + `retain()` builder + `parse_retention_policy()` + RLS + 1 NEW error class + unit tests)
  - §F22.2 automatic purge job (10 ACs — KST cron 02:00 daily + APScheduler lifespan + idempotent DELETE batch=1000 + audit-first INSERT `audit_log_purged` + dry-run mode)
  - §F22.3 archive storage with SHA-256 hash chain (12 ACs — audit_log_archive table + phase_6_audit_purge_log table + immutable append-only trigger + SHA-256 hash chain + `verify_archive_hash_chain()` + cold-archive action)
  - §F22.4 GDPR Article 17 right to erasure (10 ACs — POST /api/v1/audit-log/erase + owner-only RBAC + PII masking via AES-256-GCM NFR6 + archive preservation)
  - §F22.5 audit-first INSERT 5 NEW actions (8 ACs — `audit_log_purged` + `audit_log_archived` + `audit_log_pii_masked` + `audit_log_cold_archived` + `audit_log_personal_data_erased`)
  - §F22.6 Capability gate AUDIT_LOG_RETENTION (8 ACs — capability.py enum + 4-industry grants + require_capability + capability matrix v1.31 EXTENSION + drift detector)
  - §F22.7 tests + wire scope T1~T8 (16 ACs — pytest 6 files ~57 cases + vitest 3 files ~15 cases + 3중 게이트 + atomic commit)
- 8 tasks T1~T8 (retention DSL + automatic purge job + archive storage + GDPR/NFR4 erasure + 5 NEW AuditAction Literal values + Capability v1.31 EXTENSION + Tests + atomic commit)
- 66 subtasks (T1:13 + T2:8 + T3:14 + T4:9 + T5:5 + T6:6 + T7:8 + T8:3)
- Dev Notes with 14종 CR lessons applied
- A19 cohesion pattern 9 surface EXTENSION PASS 결정 (audit log retention surface NEW = F22.1~F22.7 audit log retention policy territory)

## 7 ACs PRD §F22.1~§F22.7 verbatim

- **§F22.1** retention policy DSL (12 ACs verbatim)
- **§F22.2** automatic purge job (10 ACs verbatim, KST cron + dry-run mode)
- **§F22.3** archive storage + SHA-256 hash chain (12 ACs verbatim, alembic 0040 + immutable append-only)
- **§F22.4** GDPR Article 17 erasure (10 ACs verbatim, NFR4 PII minimization + AES-256-GCM NFR6)
- **§F22.5** audit-first INSERT 5 NEW actions (8 ACs verbatim)
- **§F22.6** Capability gate AUDIT_LOG_RETENTION (8 ACs verbatim, capability matrix v1.31 EXTENSION)
- **§F22.7** tests + wire scope T1~T8 (16 ACs verbatim)

## Phase 6 wire scope T1~T8 결정

- **T1** retention DSL pure kernel = `apps/api/modules/audit/retention/retention_dsl.py` NEW ~120 LOC + `RetentionPolicy` TypedDict + `retain()` builder + `parse_retention_policy()` + RLS + 1 NEW error class + TS mirror interface
- **T2** automatic purge job KST cron = `apps/api/jobs/audit_log_purge.py` NEW ~180 LOC + APScheduler lifespan + idempotent DELETE batch=1000 + audit-first INSERT `audit_log_purged` + dry-run mode
- **T3** archive storage alembic 0040 + SHA-256 hash chain = `apps/api/db/migrations/versions/0040_phase_6_audit_retention.py` NEW + `audit_log_archive` table + immutable append-only trigger + `verify_archive_hash_chain()` + cold-archive action
- **T4** GDPR/NFR4 erasure endpoint = `apps/api/modules/audit/retention/erasure.py` NEW ~150 LOC + POST /api/v1/audit-log/erase + owner-only RBAC + PII masking via AES-256-GCM NFR6
- **T5** 5 NEW AuditAction Literal values + ActionClass.AUDIT EXTENSION = apps/api/core/audit_action.py MODIFIED + AuditAction Union EXTENSION + _ActionRegistry EXTENSION
- **T6** Capability v1.31 EXTENSION + drift detector = apps/api/core/capability.py MODIFIED + apps/api/dependencies/capability.py MODIFIED + tests/integration/test_capability_matrix_v1_31_drift.py NEW 8 NEW pytest cases
- **T7** Tests (~57 NEW pytest + ~15 NEW vitest + 0 NEW ruff + 0 regressions)
- **T8** atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention) + 3중 게이트 FINAL CLEAN atomic commit

## Estimated wire scope 결정 wire (cj-style 87번째 wire 진입 시점)

- ~26 NEW files (4 Python retention + 1 Python job + 1 alembic migration + 1 TS frontend client + 1 page.tsx + 4 components + 6 pytest + 3 vitest + 1 handoff + 1 commit-msg = ~26 files)
- ~8 MODIFIED files (1 backend main.py + 1 audit_action + 1 capability + 1 dependencies/capability + 1 capability-matrix.md + 1 ko-KR.json + 1 sprint-status + 1 MEMORY.md = ~8 files)
- ~57 NEW pytest cases (12 retention_dsl + 10 purge job + 12 archive storage + 10 GDPR erasure + 5 audit_action + 8 capability matrix v1.31 drift = 57)
- ~15 NEW vitest cases (5 retention config page + 5 purge job trigger + 5 GDPR erasure confirmation modal = 15)

## A19 cohesion pattern 9 surface EXTENSION PASS 결정

audit log retention surface NEW = F22.1~F22.7 audit log retention policy territory 결정 wire.

## CR lessons applied (cj-style 86번째)

- CR 0-2 RLS ✅ APPLIED (retention_dsl.py + audit_log_archive RLS 자동 적용 + multi-tenant isolation test)
- CR 1-1 audit-first INSERT ✅ APPLIED (5 NEW audit log entries + ActionClass.AUDIT EXTENSION + emit_audit_typed BEFORE destructive operation)
- CR 9-6 commit message discipline ✅ APPLIED (git commit -F <file>)
- CR 11-3 honest-DEFER discipline ✅ APPLIED (86번째 epic 연속 정직 회복, D-RETENTION-1 honestly RESOLVED)
- CR 11-4 D-001~D-005 + P-015 lessons carry ✅ APPLIED (dry-run mode UI 진입 시 frontend territory 정합 sweep)
- CR 12-1 L4 industry-agnostic capability ✅ APPLIED (AUDIT_LOG_RETENTION industry-agnostic 4-industry grants)
- CR 12-5 D-14 typed exception envelope ✅ APPLIED (7 NEW error classes)
- CR 12-5 D-PARITY-01 inversion ✅ APPLIED (Python TypedDict ↔ TS interface parity)
- CR 12-5 D-GATE-01 inversion ✅ APPLIED (AUDIT_LOG_RETENTION per-tenant on/off + owner-only RBAC AD-22)
- AD-14 stack pin ✅ APPLIED (no new deps)
- AD-22 owner-only RBAC ✅ APPLIED (GDPR erasure endpoint `require_role("owner")`)
- NFR4 PII minimization ✅ PRESERVED (GDPR Article 17 right to erasure EXTENSION + AES-256-GCM NFR6)

## D-DEFER-* honestly 결정 (CR 11-3 86번째 epic 연속 정직 회복 결정 wire 보존)

- D-1-1-DEFER-1 Magic link + D-1-1-DEFER-2 Social login OAuth + D-1-1-DEFER-3 SSO enterprise SAML 모두 ✅ RESOLVED (Epic 15 wire `5f9e37f`)
- D-EPIC-16-REVIEW-DEFER-1 (C1) ✅ RESOLVED (71번째 T4 follow-up)
- D-EPIC-16-REVIEW-DEFER-2~6 (H8+M5+M7+M9+L11) 모두 ✅ RESOLVED (78번째 cj-style 결정 wire 완료)
- D-PHASE-4-DR-DEFER-1/2 모두 ✅ RESOLVED (73~76번째 cj-style 결정 wire 완료)
- D-EPIC-17-WIRE-DEFER-T2-T3-UI ✅ RESOLVED (83번째 T2+T3 UI wire 진입 시점에 frontend 22 files wire DONE)
- **D-RETENTION-1** ✅ honestly RESOLVED (85번째 Phase 6 PRD entry 진입 시점에 1st release close-out retro §6 + Epic 17 close-out retro §11 verbatim 해소)

## Epic 1 ~ Epic 17 + Phase 3 ~ Phase 5 + 1st release cycle 정합 보존

✅ Phase 6 PRD entry `e84a281` (cj-style 85번째) 보존
✅ Epic 17 close-out retro `f1ead9a` (cj-style 84번째) 보존
✅ Epic 17 T2+T3 UI frontend atomic wire `bb92879` (cj-style 83번째) 보존
✅ Epic 17 bmad-dev-story atomic wire T1~T8 backend `2ada2ec` (cj-style 82번째) 보존
✅ Epic 17 bmad-create-story spec entry `f4b2b58` (cj-style 81번째) 보존
✅ Epic 17 PRD entry `40a9c41` (cj-style 80번째) 보존
✅ Sidebar/MenuProvider hot-fix `01a06e4` (cj-style 79번째) 보존
✅ D-EPIC-16-REVIEW-DEFER-2~6 RESOLVE sprint `512ed6a` (cj-style 78번째) 보존
✅ Phase 5 close-out retro `b843565` (cj-style 76~77번째) 보존
✅ Phase 5 atomic wire `f093f8c` (cj-style 75번째) 보존
✅ Phase 5 spec entry (cj-style 74번째) 보존
✅ Phase 5 PRD entry `93d852b` (cj-style 73번째) 보존
✅ Epic 16 cycle cj-style 67~72번째 모두 wire DONE 진입
✅ 1st release cycle cj-style 62~66번째 모두 wire DONE 진입
✅ Epic 15 cycle cj-style 58~61번째 모두 wire DONE 진입
✅ Phase 4 cycle cj-style 53~57번째 모두 wire DONE 진입
✅ Phase 3 cycle cj-style 49~52번째 모두 wire DONE 진입
✅ Epic 14 LISTEN/NOTIFY multi-process coordination `7835463` 보존
✅ Epic 13 LISTEN/NOTIFY consume `f2ea2f6` 보존
✅ Epic 12 2FA 게이트 `a63646c` 보존
✅ Epic 11 close-out retro + Phase 2 close-out baseline 599 passed 정합 보존
✅ Epic 1 carry-over (auth) layout + onboarding/industry 보존
✅ Epic 7~10 ABC/TDABC + AI 인사이트 territory 결정 wire 보존

## Next (옵션 보류)

- 옵션 (a) Phase 6 bmad-dev-story atomic wire T1~T8 진입 (cj-style 87번째 wire 진입 시점) — user 권장

## Related

- [[handoff-2026-08-22-phase-6-prd-entry-done]]
- [[handoff-2026-08-22-epic-17-close-out-done]]
- [[handoff-2026-08-22-epic-17-t2-t3-ui-wire-done]]
- [[handoff-2026-08-22-epic-17-wire-done]]
- [[handoff-2026-08-22-epic-17-spec-entry-done]]
- [[handoff-2026-08-22-epic-17-prd-entry-done]]
- [[handoff-2026-08-22-phase-5-close-out-done]]
- [[handoff-2026-08-22-phase-5-multi-region-backup-wire-done]]
- [[handoff-2026-08-22-phase-5-spec-entry-done]]
- [[handoff-2026-08-22-defer-2-6-resolve-done]]
- [[cr-11-3-lessons]]
- [[cr-11-4-lessons]]
- [[cr-12-1-lessons]]
- [[cr-12-5-lessons]]
