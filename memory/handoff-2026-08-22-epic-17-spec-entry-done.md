---
name: handoff-2026-08-22-epic-17-spec-entry-done
description: **Epic 17 bmad-create-story spec entry DONE** (cj-style Epic 17 2번째 진입점 = cj-style 81번째 epic 연속 정직 회복 atomic docs-only wire). Audit Log Viewer & Activity Stream territory spec.
metadata:
  type: project
---

# Epic 17 bmad-create-story spec entry DONE (cj-style 81번째)

**결정 wire 일자**: 2026-08-22 (KST)
**Epic 17 territory**: Audit Log Viewer & Activity Stream
**cj-style 진입점**: Epic 17 2번째 진입점 = cj-style 81번째 epic 연속 정직 회복 atomic docs-only wire

## A158~A162 5/5 ALL DONE 결정 wire

- **A158**: 옵션 (a) Epic 17 bmad-create-story spec entry 진입 결정 wire (cj-style Epic 17 2번째 진입점)
- **A159**: spec 파일 생성 결정 wire = `_bmad-output/implementation-artifacts/epic-17-audit-log-viewer-and-activity-stream-wire.md` (~+600 lines, 7 ACs PRD §F21.1~§F21.7 verbatim + 8 tasks T1~T8 + 22 subtasks + Dev Notes + CR lessons applied 14종)
- **A160**: handoff memory 신규 + MEMORY.md hook index EXTENSION
- **A161**: sprint-status 업데이트 + atomic commit
- **A162**: commit-msg file 신규 + `git commit -F <file>` (CR 9-6 D5 prevention)

## Wire scope 결정 wire

5 files atomic single sprint (cj-style 81번째 docs-only wire):
- 1 NEW `_bmad-output/implementation-artifacts/epic-17-audit-log-viewer-and-activity-stream-wire.md` (~+600 lines, 7 ACs PRD §F21.1~§F21.7 verbatim + 8 tasks T1~T8 + 22 subtasks)
- 1 NEW `memory/handoff-2026-08-22-epic-17-spec-entry-done.md` (handoff memory 결정 wire)
- 1 MODIFIED `_bmad-output/implementation-artifacts/sprint-status.yaml` (`epic-17-spec-entry: backlog → done` 신규 entry + A158~A162 action_items + last_updated_note prepend)
- 1 MODIFIED `memory/MEMORY.md` (handoff hook index EXTENSION)
- 1 NEW `_bmad-output/implementation-artifacts/commit-msg-epic-17-spec-entry.txt` (CR 9-6 commit message discipline 결정 wire)

= 3 NEW + 2 MODIFIED = 5 files atomic docs-only wire.

## Spec structure 결정 wire (~600 lines)

- YAML frontmatter with `baseline_commit: 40a9c41` (Epic 17 PRD entry commit)
- Story (As a/I want/so that) with Epic 17 territory verbatim from §F21
- 7 ACs PRD §F21.1~§F21.7 verbatim:
  - §F21.1 audit log query API (16 ACs — query_audit_log + count_audit_log + get_audit_log_entry + query_activity_stream + TypedDict 4 + RLS + owner/admin role + capability gate + error envelope 2 + 4 routes)
  - §F21.2 audit log viewer UI (12 ACs — page.tsx + 5 components + (dashboard) route group 보호 + audit-log-client.ts + ko-KR.json 14 keys + vitest RTL + owner/admin visibility + TS mirror parity)
  - §F21.3 activity stream UI (8 ACs — page.tsx + 3 components + ko-KR.json 8 keys + all tenant members 권한 + vitest RTL + TS mirror parity)
  - §F21.4 cross-region audit log visibility (7 ACs — Phase 5 carry-over chain + Supabase multi-region + read-only routing + lag threshold + Sentry breadcrumb + multi-region RLS isolation)
  - §F21.5 CSV export (8 ACs — export_audit_log_csv + UTF-8 BOM + double-quote escape + route + audit-first INSERT `audit_log_exported` + size limit + 2 error envelope + tests)
  - §F21.6 Capability gate AUDIT_LOG_VIEW (6 ACs — capability.py enum + 4-industry grants + require_capability + capability matrix v1.30 EXTENSION + drift detector + 미허용 tenant 차단)
  - §F21.7 tests + wire scope T1~T8 (16 ACs — pytest 5 files + vitest 5 files + ko-KR.json SSOT 2 + audit_action + audit directory + 3중 게이트 + A36 + atomic commit)
- 8 tasks T1~T8 (audit log query API + audit log viewer UI + activity stream UI + cross-region audit log visibility + CSV export + Capability v1.30 EXTENSION + Tests + atomic commit)
- 22 subtasks (T1 13 + T2 14 + T3 9 + T4 5 + T5 8 + T6 6 + T7 11 + T8 4)
- Dev Notes with 14종 CR lessons applied
- A19 cohesion pattern 9 surface EXTENSION PASS 결정 (audit log viewer surface NEW = F21.1~F21.6 audit log viewer & activity stream territory)

## 7 ACs PRD §F21.1~§F21.7 verbatim

- **§F21.1** audit log query API (16 ACs verbatim)
- **§F21.2** audit log viewer UI (12 ACs verbatim)
- **§F21.3** activity stream UI (8 ACs verbatim)
- **§F21.4** cross-region audit log visibility (7 ACs verbatim, Phase 5 carry-over)
- **§F21.5** CSV export (8 ACs verbatim, audit-first INSERT)
- **§F21.6** Capability gate AUDIT_LOG_VIEW (6 ACs verbatim, capability matrix v1.30 EXTENSION)
- **§F21.7** tests + wire scope T1~T8 (16 ACs verbatim)

## Epic 17 wire scope T1~T8 결정

- **T1** audit log query API wire = `apps/api/modules/audit/audit_log_query.py` NEW + 4 functions + TypedDict + RLS 자동 적용 + owner/admin role required + capability gate AUDIT_LOG_VIEW
- **T2** audit log viewer UI wire = `apps/web/app/[locale]/(dashboard)/audit-log/page.tsx` NEW + 5 components + ko-KR.json `audit_log.*` namespace EXTENSION 14 keys + audit-log-client.ts NEW + vitest RTL render
- **T3** activity stream UI wire = `apps/web/app/[locale]/(dashboard)/activity/page.tsx` NEW + 3 components + ko-KR.json `activity.*` namespace EXTENSION 8 keys
- **T4** cross-region audit log visibility wire = Phase 5 wire `f093f8c` 의 `phase_5_replication_lag` table EXTENSION + read-only routing + lag_bytes ≤ 100MB + lag_seconds ≤ 30s threshold 정합 + Sentry breadcrumb
- **T5** CSV export wire = `apps/api/modules/audit/audit_log_export.py` NEW ~120 LOC + `export_audit_log_csv` streaming + UTF-8 BOM + audit-first INSERT `audit_log_exported` + CR 12-5 D-14 error envelope
- **T6** Capability v1.30 EXTENSION wire + drift detector `tests/integration/test_capability_matrix_v1_30_drift.py` NEW
- **T7** Tests (~30 NEW pytest + ~10 NEW vitest + 0 NEW ruff + 0 regressions)
- **T8** atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention) + 3중 게이트 FINAL CLEAN atomic commit

## Estimated wire scope 결정 wire (cj-style 82번째 wire 진입 시점)

- ~12-14 NEW files (4 Python backend + 1 Python routes + 1 Python export + 1 TS frontend client + 2 page.tsx + 5 pytest + 3 vitest + 2 SSOT + 1 handoff + 1 commit-msg = 20-22 files expected)
- ~6-8 MODIFIED files (5 backend + 1 ko-KR.json + 1 sprint-status + 1 MEMORY.md)
- ~40 NEW pytest cases (15 query + 8 export + 5 cross_region + 5 audit_first + 7 drift = 40)
- ~30 NEW vitest cases (10 audit-log page + 10 audit-log-client + 10 activity page = 30)

## A19 cohesion pattern 9 surface EXTENSION PASS 결정

audit log viewer surface NEW = F21.1~F21.6 audit log viewer & activity stream territory 결정 wire.

## CR lessons applied (cj-style 81번째)

- CR 0-2 RLS ✅ APPLIED (audit_log_query.py + audit_log_export.py RLS 자동 적용)
- CR 1-1 audit-first INSERT ✅ APPLIED (audit_log_exported 1 NEW + ActionClass.AUDIT)
- CR 9-6 commit message discipline ✅ APPLIED (git commit -F <file>)
- CR 11-3 honest-DEFER discipline ✅ APPLIED (81번째 epic 연속 정직 회복)
- CR 11-4 D-001~D-005 + P-015 lessons carry ✅ APPLIED (audit_log.* 14 keys + activity.* 8 keys SSOT + vitest RTL + TS mirror + unknown state reject + drift detector)
- CR 12-1 L4 industry-agnostic capability ✅ APPLIED (AUDIT_LOG_VIEW industry-agnostic 4-industry grants)
- CR 12-5 D-14 typed exception envelope ✅ APPLIED (4 NEW error classes)
- CR 12-5 D-PARITY-01 inversion ✅ APPLIED (Python TypedDict ↔ TS interface parity)
- CR 12-5 D-GATE-01 inversion ✅ APPLIED (AUDIT_LOG_VIEW per-tenant on/off + owner-only RBAC AD-22)
- AD-14 stack pin ✅ APPLIED (no new deps)
- AD-22 owner-only RBAC ✅ APPLIED
- NFR4 PII minimization ✅ PRESERVED (audit log payload encryption at rest)

## D-DEFER-* honestly 결정 (CR 11-3 81번째 epic 연속 정직 회복 결정 wire 보존)

- D-1-1-DEFER-1 Magic link + D-1-1-DEFER-2 Social login OAuth + D-1-1-DEFER-3 SSO enterprise SAML 모두 ✅ RESOLVED (Epic 15 wire `5f9e37f`)
- D-EPIC-16-REVIEW-DEFER-1 (C1) ✅ RESOLVED (71번째 T4 follow-up)
- D-EPIC-16-REVIEW-DEFER-2~6 (H8+M5+M7+M9+L11) 모두 ✅ RESOLVED (78번째 cj-style 결정 wire 완료)
- D-PHASE-4-DR-DEFER-1/2 모두 ✅ RESOLVED (73~76번째 cj-style 결정 wire 완료)

## Epic 1 ~ Epic 16 + Phase 3 ~ Phase 5 + 1st release cycle 정합 보존

✅ Sidebar/MenuProvider hot-fix `01a06e4` (cj-style 79번째) 보존
✅ D-EPIC-16-REVIEW-DEFER-2~6 RESOLVE sprint `512ed6a` (cj-style 78번째) 보존
✅ Phase 5 close-out retro `b843565` (cj-style 76~77번째) 보존
✅ Phase 5 atomic wire `f093f8c` (cj-style 75번째) 보존
✅ Epic 17 PRD entry `40a9c41` (cj-style 80번째) 보존
✅ Epic 16 cycle cj-style 67~72번째 모두 wire DONE 진입
✅ 1st release cycle cj-style 62~66번째 모두 wire DONE 진입
✅ Epic 15 cycle cj-style 58~61번째 모두 wire DONE 진입
✅ Phase 5 cycle cj-style 73~77번째 모두 wire DONE 진입
✅ Phase 4 cycle cj-style 53~57번째 모두 wire DONE 진입
✅ Phase 3 cycle cj-style 49~52번째 모두 wire DONE 진입
✅ Epic 14 LISTEN/NOTIFY multi-process coordination `7835463` 보존
✅ Epic 13 LISTEN/NOTIFY consume `f2ea2f6` 보존
✅ Epic 12 2FA 게이트 `a63646c` 보존

## Next (옵션 보류)

- 옵션 (a) Epic 17 bmad-dev-story atomic wire T1~T8 진입 (cj-style 82번째 wire 진입 시점)

## Related

- [[handoff-2026-08-22-epic-17-prd-entry-done]]
- [[handoff-2026-08-22-defer-2-6-resolve-done]]
- [[handoff-2026-08-22-phase-5-close-out-done]]
- [[handoff-2026-08-22-phase-5-multi-region-backup-wire-done]]
- [[handoff-2026-08-22-epic-16-close-out-done]]
- [[handoff-2026-08-18-smoke-fix-sprint-done]]
- [[cr-11-3-lessons]]
- [[cr-11-4-lessons]]
- [[cr-12-1-lessons]]
- [[cr-12-5-lessons]]