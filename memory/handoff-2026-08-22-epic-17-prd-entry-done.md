---
name: handoff-2026-08-22-epic-17-prd-entry-done
description: **Epic 17 PRD entry DONE** (cj-style Epic 17 1번째 진입점 = cj-style 80번째 epic 연속 정직 회복 atomic docs-only wire). Audit Log Viewer & Activity Stream territory.
metadata:
  type: project
---

# Epic 17 PRD entry DONE (cj-style 80번째)

**결정 wire 일자**: 2026-08-22 (KST)
**Epic 17 territory**: Audit Log Viewer & Activity Stream
**cj-style 진입점**: Epic 17 1번째 진입점 = cj-style 80번째 epic 연속 정직 회복 atomic docs-only wire

## A153~A157 5/5 ALL DONE 결정 wire

- **A153**: 옵션 (a) Epic 17 진입 결정 wire (cj-style Epic 17 1번째 진입점)
- **A154**: master PRD v3.5 → v3.6 atomic edit (front matter + changelog + §F21 + §8.1 M0-(n) + §15 Epic 17 row + §부록 A A153-A157 + AD-32 신규 row)
- **A155**: AD-32 Audit Log Viewer & Activity Stream 신규 결정 (7 sub-decisions: a-g)
- **A156**: Capability matrix v1.29 → v1.30 EXTENSION AUDIT_LOG_VIEW 1 NEW row (industry-agnostic 4-industry grants ✅/✅/✅/✅)
- **A157**: Epic 17 wire scope T1~T8 결정

## Wire scope 결정 wire

5 files atomic single sprint (cj-style 80번째 docs-only wire):
- 1 MODIFIED `_bmad-output/planning-artifacts/prd.md` (v3.5 → v3.6 atomic edit)
- 1 MODIFIED `docs/capability-matrix.md` (v1.29 → v1.30 EXTENSION + AUDIT_LOG_VIEW 1 NEW row)
- 1 MODIFIED `_bmad-output/implementation-artifacts/sprint-status.yaml` (`epic-17-prd-entry: backlog → done` + A153-A157 action_items + last_updated_note prepend)
- 1 NEW `memory/handoff-2026-08-22-epic-17-prd-entry-done.md` (handoff memory 결정 wire)
- 1 NEW `_bmad-output/implementation-artifacts/commit-msg-epic-17-prd-entry.txt` (CR 9-6 commit message discipline 결정 wire)

= 2 NEW + 3 MODIFIED = 5 files atomic docs-only wire.

## Epic 17 territory (AD-32 7 sub-decisions)

(a) **audit log query API** = `apps/api/modules/audit/audit_log_query.py` NEW ~180 LOC + 4 functions + TypedDict + RLS 자동 적용 + owner/admin role required
(b) **audit log viewer UI** = `apps/web/app/[locale]/(dashboard)/audit-log/page.tsx` NEW ~200 LOC + 5 components + ko-KR.json `audit_log.*` 14 keys
(c) **activity stream UI** = `apps/web/app/[locale]/(dashboard)/activity/page.tsx` NEW ~150 LOC + 3 components + ko-KR.json `activity.*` 8 keys
(d) **cross-region audit log visibility** = Phase 5 wire `f093f8c` 의 `phase_5_replication_lag` table EXTENSION (multi-region read replica + lag_bytes ≤ 100MB + lag_seconds ≤ 30s threshold)
(e) **CSV export** = `apps/api/modules/audit/audit_log_export.py` NEW ~120 LOC + streaming + UTF-8 BOM + audit-first INSERT `audit_log_exported`
(f) **audit-first INSERT 1 NEW + RLS 자동 적용** = CR 1-1 verbatim + CR 0-2 RLS verbatim
(g) **Capability matrix v1.30 EXTENSION** + 1 NEW row + drift detector

## 7 ACs PRD §F21.1~§F21.7 verbatim

- **§F21.1** audit log query API
- **§F21.2** audit log viewer UI
- **§F21.3** activity stream UI
- **§F21.4** cross-region audit log visibility (Phase 5 carry-over)
- **§F21.5** CSV export (audit-first INSERT)
- **§F21.6** Capability gate AUDIT_LOG_VIEW (capability matrix v1.30 EXTENSION)
- **§F21.7** tests + wire scope T1~T8

## A19 cohesion pattern 9 surface EXTENSION PASS

audit log viewer surface NEW = F21.1~F21.6 audit log viewer & activity stream territory 결정 wire.

## CR lessons applied (cj-style 80번째)

- CR 0-2 RLS ✅ APPLIED (audit_log_query.py + audit_log_export.py RLS 자동 적용)
- CR 1-1 audit-first INSERT ✅ APPLIED (audit_log_exported 1 NEW + ActionClass.AUDIT)
- CR 9-6 commit message discipline ✅ APPLIED (git commit -F <file>)
- CR 11-3 honest-DEFER discipline ✅ APPLIED (80번째 epic 연속 정직 회복)
- CR 11-4 D-001~D-005 + P-015 lessons carry ✅ PRESERVED
- CR 12-1 L4 industry-agnostic capability ✅ APPLIED (AUDIT_LOG_VIEW industry-agnostic 4-industry grants)
- CR 12-5 D-14 typed exception envelope ✅ APPLIED (AUDIT_LOG_EXPORT_FORBIDDEN_KO + AUDIT_LOG_EXPORT_TOO_LARGE_KO)
- CR 12-5 D-PARITY-01 inversion ✅ APPLIED
- CR 12-5 D-GATE-01 inversion ✅ APPLIED (AUDIT_LOG_VIEW per-tenant on/off + owner-only RBAC AD-22)
- AD-14 stack pin ✅ APPLIED (no new deps)
- AD-22 owner-only RBAC ✅ APPLIED
- NFR4 PII minimization ✅ PRESERVED

## D-DEFER-* honestly 결정 (CR 11-3 80번째 epic 연속 정직 회복 결정 wire 보존)

- D-1-1-DEFER-1 Magic link + D-1-1-DEFER-2 Social login OAuth + D-1-1-DEFER-3 SSO enterprise SAML 모두 ✅ RESOLVED (Epic 15 wire `5f9e37f`)
- D-EPIC-16-REVIEW-DEFER-1 (C1) ✅ RESOLVED (71번째 T4 follow-up)
- D-EPIC-16-REVIEW-DEFER-2~6 (H8+M5+M7+M9+L11) 모두 ✅ RESOLVED (78번째 cj-style 결정 wire 완료)
- D-PHASE-4-DR-DEFER-1/2 모두 ✅ RESOLVED (73~76번째 cj-style 결정 wire 완료)

## Epic 1 ~ Epic 16 + Phase 3 ~ Phase 5 + 1st release cycle 정합 보존

✅ Sidebar/MenuProvider hot-fix `01a06e4` (cj-style 79번째) 보존
✅ D-EPIC-16-REVIEW-DEFER-2~6 RESOLVE sprint `512ed6a` (cj-style 78번째) 보존
✅ Phase 5 close-out retro `b843565` (cj-style 76~77번째) 보존
✅ Phase 5 atomic wire `f093f8c` (cj-style 75번째) 보존
✅ Epic 16 cycle cj-style 67~72번째 모두 wire DONE 진입
✅ 1st release cycle cj-style 62~66번째 모두 wire DONE 진입
✅ Epic 15 cycle cj-style 58~61번째 모두 wire DONE 진입
✅ Phase 4 cycle cj-style 53~57번째 모두 wire DONE 진입
✅ Phase 3 cycle cj-style 49~52번째 모두 wire DONE 진입
✅ Epic 14 LISTEN/NOTIFY multi-process coordination `7835463` 보존
✅ Epic 13 LISTEN/NOTIFY consume `f2ea2f6` 보존
✅ Epic 12 2FA 게이트 `a63646c` 보존

## Next (옵션 보류)

- 옵션 (a) Epic 17 bmad-create-story spec entry 진입 (cj-style 81번째 epic 연속 정직 회복 진입 대기)
- 옵션 (b) Epic 17 bmad-dev-story atomic wire T1~T8 진입 (cj-style 82번째 wire 진입 시점)

## Related

- [[handoff-2026-08-22-defer-2-6-resolve-done]]
- [[handoff-2026-08-22-phase-5-close-out-done]]
- [[handoff-2026-08-22-phase-5-multi-region-backup-wire-done]]
- [[handoff-2026-08-22-epic-16-close-out-done]]
- [[handoff-2026-08-18-smoke-fix-sprint-done]]
- [[cr-11-3-lessons]]
- [[cr-12-1-lessons]]
- [[cr-12-5-lessons]]
