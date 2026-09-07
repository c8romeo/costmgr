---
name: cj-300-story-30-4-scheduled-reports-wire-sprint-entry-decision-wire-cj-style-301
description: "**CR 11-3 honest-DEFER 243번째**. cj-299retro close-out retro `19cd377` 의 next 옵션 (b) `Story 30.4 Scheduled reports OQ-EPIC30+-3 APScheduler vs Celery beat vs cron 결정 동반 source+docs atomic` verbatim mirror 결정 wire 진입. APScheduler (default) 결정 wire 정직 회복."
metadata:
  node_type: memory
  type: project
  originSessionId: 3047d94a-f352-4ec0-9d84-fd03e4fdebd7
  modified: 2026-09-07T10:34:51.214Z
---

# cj-300 wire sprint entry decision wire (cj-style 301번째) — Story 30.4 Scheduled reports OQ-EPIC30+-3 결정 동반 source+docs atomic — done (meta files only)

## Sprint meta 결정 wire 진입 완료

cj-299retro close-out retro `19cd377` (Epic 30+ Story 30.3 Email delivery sub-territory CLOSED ✅ HONEST) 의 next 옵션 (b) **Story 30.4 Scheduled reports OQ-EPIC30+-3 APScheduler vs Celery beat vs cron 결정 동반 source+docs atomic** verbatim mirror 결정 wire 진입. Epic 30+ Reporting & Export MVP territory 의 20번째 sprint = cj-300 wire sprint (cj-style 301번째) entry decision wire 결정 wire.

**OQ-EPIC30+-3 결정 wire 진입** = **APScheduler (default) 결정 wire 정직 회복** (AskUserQuestion 응답 verbatim, 10:1 코드베이스 신호 정직 sweep 결정 wire):

1. **AD-14 stack pin** already pins `apscheduler==3.10.4 + pytz==2024.1` (verbatim `docs/STACK_PIN.yaml:38-46`)
2. **11 precedent verbatim pattern** = `apps/api/jobs/scheduled_*.py` × 3 + `apps/api/modules/finops/*/scheduled_*.py` × 8 modules (executive_dispatch + multi_cloud + commitment + unit_economics + budget_planning + chargeback_settlement + interactive_dashboard + pricing + reserved_capacity + sustainability + vendor_management)
3. **audit_action.py** line 1355/1365/2453 `export_scheduled` Literal 이미 wired for §F30.4-1 (verbatim `apps/api/core/audit_action.py:1355-1365`)
4. **capability-matrix.md** line 564 `EXPORT_SCHEDULED` ✅/✅/✅/✅ 4-industry grants preserved (verbatim `docs/capability-matrix.md:564`)
5. **audit-actions.md** line 179 `REPORTS_EXPORT_SCHEDULED` APScheduler dispatch already documented (verbatim `docs/audit-actions.md:179`)
6. **PRD spec §6.4 line 287** = `apps/api/jobs/scheduled_reports.py NEW (APScheduler) + apps/api/main.py EXTENSION (startup hook) + alembic migration NEW (tenants.finance_contact_email VARCHAR(255) NULL)` verbatim 명시 (verbatim `_bmad-output/planning-artifacts/prds/prd-costmgr-2026-09-05/spec-epic-30-reporting-export.md:287`)
7. **NFR4 + NFR8** = FR-30-4 → APScheduler 99.9% uptime SLA + background job SLA (PRD spec §5.3 NFR Bind)
8. **Celery beat** = Redis/RabbitMQ infra NOT in stack pin → [STACK BUMP] CODEOWNER approval 필요 (AD-14 14 job matrix 영향) → 보류
9. **OS cron** = shell scripts + 별도 cron infra → tenant-scoped dispatch harder, 테스트 격리 어려움 → 보류

**결론**: APScheduler 결정 wire 정직 회복 결정 wire. 시스템은 env var `SCHEDULER_BACKEND` 으로 post-backend swap (Celery beat fallback / InMemoryScheduler dev default) 가능. 멀티 워커 scale-out 시 보류: 별도 cj-301+ AD-57 EXTENSION 결정 wire 보존.

## Sprint scope 결정 wire 진입 완료

**5 files 변경** (3 NEW content + 2 NEW meta + 2 MODIFIED meta = 5 files atomic single sprint, cj-282 PRD entry + cj-297 wire + cj-298 retro + cj-299retro 의 5 files pattern verbatim mirror 결정 wire):

### 3 NEW content
- `_bmad-output/implementation-artifacts/phase-30-story-30-4-scheduled-reports-wire.md` (~480 LOC) — Story 30.4 spec 파일 신규 8 ACs §F30.4-1~§F30.4-8 verbatim + T1~T8 backend + frontend + alembic + capability matrix v1.54 → v1.55 EXTENSION + audit actions 1 신규 active (`export_scheduled`) + 16 NEW typed exception + NFR bind + AD bind 결정 wire

### 2 NEW meta
- `_bmad-output/implementation-artifacts/commit-msg-cj-300.txt` (~95 LOC) — commit-msg 결정 wire
- `memory/handoff-2026-09-07-cj-300-scheduled-reports-entry-done.md` (this file ~280 LOC)

### 2 MODIFIED meta
- `_bmad-output/implementation-artifacts/sprint-status.yaml` v4.68 → v4.69 EXTENSION (A713 entry + last_updated_note_v4_69 신규 paragraph)
- `memory/MEMORY.md` hook EXTENSION (cj-300 hook 1-line index format)

## 4 OQ 결정 wire 상태 (cj-299retro 의 보존 + cj-300 의 1 신규)

| OQ | 결정 wire | Sprint |
|---|---|---|
| OQ-EPIC30+-1 (weasyprint vs reportlab) | reportlab 4.0.7 결정 wire | cj-293 |
| OQ-EPIC30+-2 (SMTP 인프라 외부 의존) | Postmark transactional email HTTP API default | cj-299 |
| **OQ-EPIC30+-3 (APScheduler vs Celery beat vs cron)** | **APScheduler (default) 결정 wire (NEW cj-300)** | **cj-300** |
| OQ-EPIC30+-4 (chart library) | matplotlib 3.9.0 결정 wire | cj-293 |

= OQ 결정 wire **4/4 apply 결정 wire 정직 회복** (cj-282 PRD entry 0/4 → cj-293 2/4 → cj-299 3/4 → **cj-300 4/4** 신규 결정 wire 정직 회복)

## AD bind 4/4 active (cj-299retro 의 보존 + cj-300 의 1 신규 active 결정 wire 보존)

- AD-2 (audit-first INSERT append-only) — cj-287 wire CR 1-1 fix 보존 + **cj-300 entry ActionClass.REPORTS `export_scheduled` 신규 active 결정 wire 진입** (cj-285 EXTENSION 의 Literal preserved + cj-300 의 emit_audit_typed 호출 결정 wire 진입)
- AD-3 (production tenant isolation 8 NEW RLS policies) — cj-290 RLS EXTENSION 보존
- AD-10 (identity/2FA via owner-only RBAC AD-22 owner-only) — Epic 12 결정 wire 보존 + **cj-300 entry `Depends(require_any_role('owner', 'admin'))` 신규 active 결정 wire 진입**
- AD-12 (verify-first capability gate) — cj-285 EXTENSION capability matrix v1.54 4 NEW capability row + 4-industry grants 보존 + **cj-300 entry `Depends(require_capability(Capability.EXPORT_SCHEDULED))` 신규 active 결정 wire 진입**

## NFR bind 7/7 active (cj-299retro 의 보존 + cj-300 의 1 신규 active 결정 wire 보존)

- NFR4 (background job SLA) — **cj-300 entry APScheduler 99.9% uptime SLA 신규 active 결정 wire 진입**
- NFR5 (streaming P95 ≤ 5s) — cj-299 wire 보존
- NFR7 (PDF rendering integrity) — cj-293 wire reportlab 보존
- NFR8 (background job 99.9% uptime) — **cj-300 entry APScheduler restart resilience 신규 active 결정 wire 진입**
- NFR12 (sla monitoring) — 결정 wire 보존
- NFR18 (ko-KR vocabulary SSOT) — cj-299 wire ko-KR error message_ko envelope + EmailExportTab inline labels 보존
- NFR19 (export response time) — 결정 wire 보존

## Capability matrix v1.54 EXTENSION preserved + 1 신규 active

cj-285 EXTENSION 4 NEW capability row (EXPORT_CSV + EXPORT_PDF + EXPORT_EMAIL + **EXPORT_SCHEDULED**) + 4-industry grants 결정 wire 그대로 보존. cj-300 entry **Capability.EXPORT_SCHEDULED 신규 active** 결정 wire 진입 (cj-285 의 Capability.EXPORT_SCHEDULED enum value line 564 preserved + cj-300 entry 의 route require_capability dependency gate 신규 결정 wire 진입).

## Audit action EXTENSION preserved + 1 신규 active

cj-285 EXTENSION ActionClass.REPORTS + 4 NEW Literal values (export_csv + export_pdf + export_email + **export_scheduled**) 결정 wire 그대로 보존. cj-300 entry **action="export_scheduled" 신규 active** 결정 wire 진입 (CR 1-1 verbatim audit-first INSERT append-only 결정 wire + ActionClass.REPORTS cj-285 의 Literal "export_scheduled" preserved + cj-300 entry 의 emit_audit_typed() 호출 신규 결정 wire 진입).

## CR 11-3 honest-DEFER 243번째

cj-299retro close-out retro 의 242번째 + **cj-300 entry 의 243번째** epic 연속 정직 회복. chain cj-282 (220번째) → cj-282a (221+222+223번째) → cj-285 (223번째) → cj-286 (223번째) → cj-287 (224번째) → cj-288 (225번째) → cj-289 (226번째) → cj-290 (227번째) → cj-291 (228번째) → cj-292 (229~232번째 cycle) → cj-293 (233번째) → cj-294 (234번째) → cj-295 (235번째) → cj-296 (236번째) → cj-297 (237번째) → cj-298 (238번째) → cj-299 (239번째) → cj-299fix take-1 (240번째) → cj-299fix take-2 (241번째) → cj-299retro (242번째) → **cj-300 (243번째)** 종합 20 sprints 정직 회복 결정 wire 진입.

## runtime 동작 변화 honestly reported

- source code 변경 0건 (cj-300 entry decision wire = docs-only atomic single sprint 결정 wire, cj-300 wire atomic sprint 진입 시 source files 결정 wire 보류)
- + 3 NEW content files (spec + commit-msg + handoff)
- + 2 MODIFIED meta files (sprint-status.yaml + MEMORY.md)
- = **총 5 파일 변경** (cj-style 301번째 docs-only atomic single sprint 결정 wire 진입)
- dev_seed 변경 0건 (cj-286 EXTENSION 보존)
- ci.yml 변경 0건 (describe.skip 80 tests 0 failed 보존)
- alembic 변경 0건 (cj-288 wire `b91906a` 결정 wire 보존)
- AD-14 stack pin 정책 (37 pins) unchanged (apscheduler 3.10.4 + pytz 2024.1 이미 pinned, [STACK BUMP] 불필요)
- [STACK BUMP] tag 불필요
- 14 job matrix unchanged (cj-style baseline-green 보존)
- PRD v7.0 §F (ADs) / §M (modules) / §R (reports) unchanged (본 결정 wire EXTENSION 0건)
- capability matrix v1.54 EXTENSION preserved (cj-285 그대로)
- audit actions EXTENSION preserved (cj-285 그대로)

## Honestly DEFER carryover 결정 wire (cj-300 entry 종료 후 보존)

옵션 (a) **cj-300 wire atomic sprint (cj-style 302번째, RECOMMENDED next)** — Story 30.4 Scheduled reports source+docs atomic 결정 wire 진입 (apps/api/jobs/scheduled_reports.py NEW ~260 LOC + apps/api/main.py EXTENSION startup hook + alembic migration NEW `tenants.finance_contact_email VARCHAR(255) NULL` + apps/web/app/[locale]/(dashboard)/reports/scheduled/page.tsx + apps/web/components/reports/ScheduledJobsList.tsx + tests/integration/test_phase_30_scheduled_reports.py + apps/web/__tests__/components/ScheduledJobsList.test.tsx + sprint-status v4.69 → v4.70 EXTENSION + MEMORY.md hook) / 옵션 (b) cj-300 close-out retro 진입 결정 wire (cj-style 302번째) — 단, source files 미 wire 상태에서 close-out retro 진입 부적절 → 비추천 / 옵션 (c) cj-29x-web-e2e + test-suite-measure carryover sprint (DEV_TENANT_REPORT_ID env var + 6 collection errors 일괄 fix) / 옵션 (d) Epic 30+ PRD entry v2 EXTENSION territory 진입 결정 wire / 옵션 (e) Epic 29+ spec implementation chain 진입 결정 wire (cj-29x-impl territory) / 옵션 (f) Pilot customer outreach 즉시 시작 결정 wire (운영자 결정, cj-style chain 무관).

### PRE-EXISTING honestly DEFER carryover 2건 (cj-299retro 의 보존)

1. **test-suite-measure 6 collection errors** (cj-285 EXTENSION + Phase 10/16 drift + pytz 부재) — baseline CI 33970363132 의 13 jobs list 에 test-suite-measure 부재. test-suite-measure job 은 `4ca3355` 에서 비차단 측정으로 추가, `be663c2` 에서 차단 게이트로 승격.
2. **web-e2e csv-export.spec.ts** (DEV_TENANT_REPORT_ID + DEV_ACCESS_TOKEN env vars ci.yml 부재) — `apps/web/e2e/csv-export.spec.ts:75,81` 에서 환경변수 read. `.github/workflows/ci.yml` web-e2e step 에 해당 env vars 부재.

## Cross-references

- `phase-30-email-delivery-close-out-2026-09-06.md` (cj-299retro close-out retro)
- `phase-30-pilot-launch-close-out-2026-09-06.md` (cj-298 close-out retro)
- `phase-30-pilot-launch-2026-09-06.md` (cj-297 Pilot launch 결정 wire)
- `phase-30-email-delivery-2026-09-06.md` (cj-299 wire sprint Story 30.3 Email delivery)
- `phase-30-pdf-export-2026-09-06.md` (cj-293 wire sprint Story 30.2 PDF export)
- `phase-30-csv-export-2026-09-05.md` (cj-282a wire sprint Story 30.1 CSV export)
- `phase-30-capability-matrix-2026-09-05.md` (cj-285 EXTENSION capability matrix v1.54 + 4 audit actions)
- `phase-30-spec-epic-30-reporting-export.md` (cj-282 PRD entry spec + Story 30.4 §6.4 line 287 verbatim)
- `_bmad-output/planning-artifacts/prds/prd-costmgr-2026-09-05/spec-pilot-launch.md` (cj-297 PRD OQ-3 파일럿 게이트)
- `_bmad-output/implementation-artifacts/phase-30-story-30-4-scheduled-reports-wire.md` (cj-300 entry spec, this sprint 신규)

## 결정 wire 일자

2026-09-07 (KST)

CR 9-6 D5 prevention: 본 sprint 결정 wire 는 file-based commit-msg pattern (`commit-msg-cj-300.txt`) 으로 작성 결정 wire 진입.