# Story 30.4 Scheduled reports — Wire Sprint Spec (cj-300 entry decision wire)

> **Status:** ready-for-dev
> **Sprint key:** phase-30-story-30-4-scheduled-reports-wire
> **cj-style entry point:** 301st
> **Baseline commit:** cj-299retro `19cd377` (Epic 30+ Story 30.3 Email delivery sub-territory CLOSED ✅ HONEST)
> **Story + Context:** cj-299retro next 옵션 (b) `Story 30.4 Scheduled reports OQ-EPIC30+-3 APScheduler vs Celery beat vs cron 결정 동반 source+docs atomic` verbatim mirror 결정 wire 진입. Epic 30+ Reporting & Export MVP territory 의 20번째 sprint. 11 precedent verbatim pattern (executive_dispatch + multi_cloud + commitment + unit_economics + budget_planning + chargeback_settlement + interactive_dashboard + pricing + reserved_capacity + sustainability + vendor_management) 모두 APScheduler 3.10.4 AsyncIOScheduler + PersistentJobStore 보존. **OQ-EPIC30+-3 결정 wire 진입** = **APScheduler (default) 결정 wire 정직 회복** 결정 wire (AskUserQuestion 응답 verbatim, 10:1 코드베이스 신호 정직 sweep).

## 8 ACs §F30.4-1~§F30.4-8 verbatim → ~88 detailed sub-ACs

### §F30.4-1 APScheduler AsyncIOScheduler + PersistentJobStore (5 sub-ACs)

1. **AD-14 stack pin verbatim 보존** — `apscheduler==3.10.4 + pytz==2024.1` 이미 pinned (`docs/STACK_PIN.yaml:38-46`). [STACK BUMP] tag 불필요 결정 wire.
2. **AsyncIOScheduler + PersistentJobStore verbatim pattern** — `apps/api/jobs/scheduled_reports.py` NEW ~260 LOC. 11 precedent verbatim pattern 미러 (`scheduled_executive_dispatch.py:9` "apscheduler==3.10.4 AsyncIOScheduler + PersistentJobStore" + `scheduled_unit_economics_calculation_job.py:9` + `scheduled_multi_cloud_dispatch_job.py:9` + `scheduled_commitment_dispatch.py:9` + 8 modules `apps/api/modules/finops/*/scheduled_*.py`).
3. **4 cron schedules 결정 wire 보존** — cj-285 의 capability matrix v1.54 EXTENSION EXPORT_SCHEDULED row ✅/✅/✅/✅ 4-industry grants 결정 wire 보존 (verbatim `docs/capability-matrix.md:564`).
4. **Audit-first INSERT action="export_scheduled" 신규 active** — `apps/api/core/audit_action.py:1355-1365` `export_scheduled` Literal 이미 wired 보존 + cj-300 wire atomic 진입 시 emit_audit_typed() 호출 신규 결정 wire 진입. ActionClass.REPORTS cj-285 EXTENSION preserved.
5. **Lifecycle state machine verbatim pattern** — scheduled → running → completed/failed/cancelled. 11 precedent verbatim pattern 미러.

### §F30.4-2 finance_contact_email column EXTENSION (5 sub-ACs)

1. **alembic migration NEW `tenants.finance_contact_email VARCHAR(255) NULL`** — `apps/api/alembic/versions/0061_phase_30_story_30_4_finance_contact_email.py` NEW ~120 LOC. PRD spec §6.4 line 287 verbatim 명시.
2. **RLS policy EXTENSION** — tenant_id selector verbatim + finance_contact_email PII minimization CR 0-2 RLS + tenant 격리 NFR4.
3. **CR 0-2 RLS verbatim** — tenant_id selector + multi-tenant isolation. `apps/api/modules/reports/` RLS pattern verbatim.
4. **Null fallback 결정 wire** — finance_contact_email = NULL 인 tenant 의 경우 default admin email 발송 (audit log INSERT path `admin_fallback_dispatched`).
5. **Migration upgrade/downgrade round-trip** — alembic upgrade head + alembic downgrade base PASS 결정 wire.

### §F30.4-3 main.py startup hook EXTENSION (5 sub-ACs)

1. **apps/api/main.py EXTENSION startup hook** — `@app.on_event("startup")` AsyncIOScheduler.start() verbatim. 11 precedent verbatim pattern 미러 (`scheduled_executive_dispatch.py` lifecycle state machine).
2. **CR 1-1 audit-first INSERT ContextVar** — trace_id propagation verbatim (`scheduled_executive_dispatch.py:9` "CR 1-1 ContextVar — trace_id propagation").
3. **Idempotency per (tenant_id + dispatch_schedule + period_key) tuple** — `scheduled_executive_dispatch.py:9` "Idempotency per (tenant_id + dispatch_schedule + period_key) tuple" verbatim pattern.
4. **Retry policy: exponential backoff 1min → 5min → 30min, 3 retries** — `scheduled_executive_dispatch.py:9` verbatim pattern.
5. **main.py line ~700 EXTENSION** — email_export_router (cj-299) 다음 scheduled_reports_router include 결정 wire.

### §F30.4-4 Recipient resolver dispatch (5 sub-ACs)

1. **Recipient resolver dispatch** — finance_contact_email lookup + admin email fallback (NFR4 PII minimization).
2. **CSV + PDF + Email 통합 dispatch** — cj-282a (CSV) + cj-293 (PDF) + cj-299 (Email) 의 기존 export service 통합 dispatch.
3. **Recipient masking NFR19** — recipient email masking in audit log INSERT path 결정 wire 보존.
4. **NFR4 PII minimization verbatim** — finance_contact_email redact 패턴 + recipient masking 11 precedent verbatim pattern.
5. **Slack DM notification (optional EXTENSION)** — 11 precedent 의 Slack DM notification verbatim pattern 보존 결정 wire 보존 (cj-285 의 capability matrix v1.54 EXTENSION 의 NFR4 + NFR19 보존).

### §F30.4-5 UI list page + ScheduledJobsList component (8 sub-ACs)

1. **apps/web/app/[locale]/(dashboard)/reports/scheduled/page.tsx NEW** — RSC page + scheduled jobs list view.
2. **apps/web/components/reports/ScheduledJobsList.tsx NEW** — table component (job_id + dispatch_schedule + last_run_at + next_run_at + status + tenant_name).
3. **3 NEW data-testid** — `scheduled-jobs-list-table` + `scheduled-job-row` + `scheduled-job-cancel-button`.
4. **ActionClass.REPORTS export_scheduled 결정 wire 보존** — UI cancel button click → `POST /api/v1/exports/scheduled/{job_id}/cancel` 결정 wire 진입.
5. **NFR18 ko-KR vocabulary SSOT** — ko-KR inline labels (`ko-KR.json` EXTENSION ~5 NEW keys) + ScheduledJobsList inline strings SSOT.
6. **Capability.EXPORT_SCHEDULED require_capability dependency gate** — `Depends(require_capability(Capability.EXPORT_SCHEDULED))` 결정 wire 진입.
7. **Owner/admin only RBAC AD-22** — `Depends(require_any_role('owner', 'admin'))` 결정 wire 진입.
8. **Tab nav EXTENSION** — ReportsTabNav.tsx 3-tab → 4-tab UX EXTENSION (cj-295 follow-up #1 의 2-tab→3-tab 패턴 verbatim 미러).

### §F30.4-6 Capability matrix v1.55 EXTENSION EXPORT_SCHEDULED (6 sub-ACs)

1. **Capability.EXPORT_SCHEDULED enum value** — cj-285 의 enum value line 564 preserved + 4-industry grants 결정 wire 보존.
2. **verify_first_export_scheduled gate** — cj-285 의 Capability v1.54 EXTENSION preserved.
3. **Role.BUDGET_PLANNING_OPERATOR-style operator/viewer roles** — Epic 12 owner/admin RBAC preserved.
5. **CR 12-1 L4 industry-agnostic capability** — 4-industry grants ✅/✅/✅/✅ industry-agnostic CR 12-1 L4 verbatim.
6. **Capability matrix v1.54 EXTENSION preserved** — cj-285 EXTENSION 그대로 보존.

### §F30.4-7 Audit action EXTENSION export_scheduled + 16 NEW typed exceptions (4 sub-ACs)

1. **ActionClass.REPORTS + Literal "export_scheduled"** — `apps/api/core/audit_action.py:1355-1365` verbatim preserved + emit_audit_typed() 호출 신규 active.
2. **CR 1-1 audit-first INSERT append-only** — 8 NEW actions EXTENSION cj-285 preserved + cj-300 의 1 신규 active.
3. **16 NEW typed exception classes CR 12-5 D-14 envelope** — ScheduledReportCronInvalidError 400 + ScheduledReportTenantNotFoundError 404 + ScheduledReportFinanceEmailNotFoundError 400 + ScheduledReportLifecycleError 400 + ScheduledReportRetryExhaustedError 500 + ScheduledReportPersistenceError 500 + ScheduledReportIdempotencyViolationError 409 + ScheduledReportPermissionError 403 + ScheduledReportFinanceContactEmailError 400 + ScheduledReportAlembicMigrationError 500 + ScheduledReportAsyncIOError 500 + ScheduledReportPersistentJobStoreError 500 + ScheduledReportTimezoneError 400 + ScheduledReportPeriodKeyError 400 + ScheduledReportDispatchError 500 + ScheduledReportRecipientResolverError 500 = 16 NEW typed exception classes.
4. **errors.py EXTENSION** — `apps/api/core/errors.py` ScheduledReportError base class NEW + 16 NEW typed exceptions.

### §F30.4-8 dry-run + Tests + wire scope T1~T8 verified (10 sub-ACs)

1. **dry-run CLI flag** — `--scheduled-reports-dry-run` + `--scheduled-reports-finance-contact-email-dry-run` 2 NEW CLI flags (`apps/api/scripts/cli/scheduled_reports_dry_run.py` + `apps/api/scripts/cli/scheduled_reports_finance_contact_email_dry_run.py` 2 NEW CLI scripts).
2. **apps/api/jobs/scheduled_reports.py NEW ~260 LOC** — main scheduler job.
3. **apps/api/modules/reports/scheduled_routes.py NEW ~280 LOC** — FastAPI router 4 NEW endpoints (POST /api/v1/exports/scheduled/cancel + GET /api/v1/exports/scheduled/jobs + GET /api/v1/exports/scheduled/history + POST /api/v1/exports/scheduled/dispatch-now).
4. **apps/api/modules/reports/scheduled_serializers.py NEW ~205 LOC** — Pydantic schemas + 3 field_validator NFR18 ko-KR.
5. **alembic migration NEW ~120 LOC** — `0061_phase_30_story_30_4_finance_contact_email.py`.
6. **apps/api/main.py EXTENSION startup hook** — line ~700+ `scheduled_reports_router include` + `@app.on_event("startup")` AsyncIOScheduler.start().
7. **apps/web/app/[locale]/(dashboard)/reports/scheduled/page.tsx NEW** — RSC page + scheduled jobs list.
8. **apps/web/components/reports/ScheduledJobsList.tsx NEW** — table component.
9. **apps/web/components/reports/ReportsTabNav.tsx EXTENSION** — 3-tab → 4-tab UX (cj-295 follow-up #1 의 2-tab→3-tab 패턴 verbatim 미러).
10. **Tests** — `tests/integration/test_phase_30_scheduled_reports.py` NEW ~360 LOC (60+ tests: scheduler + cron + finance_email + retry + idempotency + lifecycle + alembic + capability + audit_action + errors + dry-run CLI + history) + `apps/web/__tests__/components/ScheduledJobsList.test.tsx` NEW ~125 LOC (6 frontend tests vitest + @testing-library/react).

= 8 ACs + ~88 detailed sub-ACs pre-flight 정합 sweep 만족 결정 wire.

## AD-52 (a)~(g) 7 sub-decisions verbatim cross-reference

- (a) territory decision = Epic 30+ Reporting & Export MVP territory preserved (cj-282 PRD entry `0c7524e`).
- (b) capability matrix v1.54 EXTENSION preserved (cj-285) + cj-300 의 Capability.EXPORT_SCHEDULED 신규 active.
- (c) audit actions EXTENSION preserved (cj-285) + cj-300 의 export_scheduled 신규 active.
- (d) dev_seed.py EXTENSION 보존 (cj-286) + cj-300 의 finance_contact_email column EXTENSION.
- (e) ci.yml web-e2e csv-export.spec.ts EXTENSION 보존 (cj-286, PRE-EXISTING DEFER cj-299retro).
- (f) AD-56 Epic 30+ 7 sub-decisions 보존 (cj-286) + cj-300 의 OQ-EPIC30+-3 결정 wire 진입.
- (g) 10M KRW threshold EXTENSION 결정 wire 보존 (cj-286 + AD-56 (g) rationale).

## T1~T8 wire scope + ~38 subtasks

### T1 backend scheduler (5 subtasks)
- T1.1 `apps/api/jobs/scheduled_reports.py` NEW ~260 LOC AsyncIOScheduler + PersistentJobStore
- T1.2 `apps/api/main.py` EXTENSION startup hook + scheduled_reports_router include
- T1.3 4 cron schedules 결정 wire (weekly Mon 09:00 + monthly 1st-day 09:00 + quarterly 1st-day 09:00 + annual Jan-1 09:00)
- T1.4 Lifecycle state machine (scheduled → running → completed/failed/cancelled)
- T1.5 Idempotency per (tenant_id + dispatch_schedule + period_key) tuple + retry 3회

### T2 alembic migration (4 subtasks)
- T2.1 `apps/api/alembic/versions/0061_phase_30_story_30_4_finance_contact_email.py` NEW ~120 LOC
- T2.2 `tenants.finance_contact_email VARCHAR(255) NULL` column ADD
- T2.3 RLS policy EXTENSION + tenant_id selector verbatim
- T2.4 Upgrade/downgrade round-trip PASS

### T3 FastAPI router (5 subtasks)
- T3.1 `apps/api/modules/reports/scheduled_routes.py` NEW ~280 LOC
- T3.2 POST /api/v1/exports/scheduled/{job_id}/cancel
- T3.3 GET /api/v1/exports/scheduled/jobs
- T3.4 GET /api/v1/exports/scheduled/history
- T3.5 POST /api/v1/exports/scheduled/dispatch-now

### T4 serializers (4 subtasks)
- T4.1 `apps/api/modules/reports/scheduled_serializers.py` NEW ~205 LOC
- T4.2 ScheduledJobCreate + ScheduledJobResponse + ScheduledJobCancel + ScheduledJobHistory Pydantic schemas
- T4.3 3 field_validator NFR18 ko-KR
- T4.4 DispatchSchedule + PeriodKey Literal 결정 wire

### T5 typed exceptions (3 subtasks)
- T5.1 `apps/api/core/errors.py` EXTENSION ScheduledReportError base class + 16 NEW typed exception classes
- T5.2 16 NEW exception envelope CR 12-5 D-14 verbatim
- T5.3 Capability gate 의 exception path 결정 wire

### T6 UI list page (4 subtasks)
- T6.1 `apps/web/app/[locale]/(dashboard)/reports/scheduled/page.tsx` NEW
- T6.2 `apps/web/components/reports/ScheduledJobsList.tsx` NEW ~280 LOC
- T6.3 3 NEW data-testid (scheduled-jobs-list-table + scheduled-job-row + scheduled-job-cancel-button)
- T6.4 NFR18 ko-KR inline labels + ko-KR.json EXTENSION ~5 NEW keys

### T7 Tab nav EXTENSION (3 subtasks)
- T7.1 `apps/web/components/reports/ReportsTabNav.tsx` EXTENSION 3-tab → 4-tab UX
- T7.2 ScheduledJobsList import + scheduled tab UX
- T7.3 Capability.EXPORT_SCHEDULED require_capability gate

### T9 tests + dry-run (10 subtasks)
- T9.1 `tests/integration/test_phase_30_scheduled_reports.py` NEW ~360 LOC 60+ tests (scheduler + cron + finance_email + retry + idempotency + lifecycle + alembic + capability + audit_action + errors + dry-run CLI + history)
- T9.2 `apps/web/__tests__/components/ScheduledJobsList.test.tsx` NEW ~125 LOC 6 frontend tests vitest
- T9.3 `apps/api/scripts/cli/scheduled_reports_dry_run.py` NEW + `--scheduled-reports-dry-run` flag
- T9.4 `apps/api/scripts/cli/scheduled_reports_finance_contact_email_dry_run.py` NEW + `--scheduled-reports-finance-contact-email-dry-run` flag
- T9.5 vitest mocks verbatim (cj-299 의 AsyncMock pattern 미러)
- T9.6 alembic upgrade/downgrade round-trip PASS 결정 wire
- T9.7 capability gate `Depends(require_capability(Capability.EXPORT_SCHEDULED))` 결정 wire
- T9.8 RBAC `Depends(require_any_role('owner', 'admin'))` 결정 wire
- T9.9 audit-first INSERT emit_audit_typed() 호출 결정 wire
- T9.10 3중 게이트 FINAL CLEAN 검증 (ruff + pytest + vitest + tsc)

= T1~T8 + ~38 subtasks 결정 wire 진입.

## Dev Notes 19종

1. **CR 0-2 RLS** — tenant_id selector + multi-tenant isolation
2. **CR 1-1 audit-first INSERT append-only** — emit_audit_typed() 호출 verbatim
3. **CR 1-1 ContextVar** — trace_id propagation verbatim
4. **CR 1-1 RSC boundary** — RSC page ↔ Client component boundary verbatim
5. **CR 4-3/4-4** — Decimal precision + banker's rounding verbatim
6. **CR 5-1 Decimal precision banker's rounding** — finance_contact_email INSERT path
7. **CR 9-6 commit message discipline** — `git commit -F <file>` verbatim
8. **CR 11-3 ALLOWED_SERVICE_SUBMODULES 즉시 sweep EXTENSION** — `m30_reports_scheduled` 신규 EXTENSION
9. **CR 11-3 honest-DEFER 243번째** — cj-299retro 의 242번째 + cj-300 의 243번째
10. **CR 11-3 honest-DEFER post-commit retroactive correction 보존** — Phase 22/23/24 retroactive correction 패턴 verbatim 미러
11. **CR 11-4 P-015 pure validator pattern** — DispatchSchedule validator + PeriodKey validator + finance_email format validator
12. **CR 12-1 L4 industry-agnostic capability** — 4-industry grants ✅/✅/✅/✅
13. **CR 12-5 D-14 typed exception envelope verbatim** — 16 NEW typed exception classes
14. **CR 12-5 D-PARITY-01 inversion** — TypeScript mirror + ko-KR.json EXTENSION
15. **CR 12-5 D-GATE-01 inversion** — Capability gate path
16. **A19 cohesion 9 surface EXTENSION PASS preserved** — Surface 1~9 EXTENSION 결정 wire 진입
17. **A36 SDR 검증 4-step** — sanity determination review 4-step verbatim
18. **AD-14 stack pin** — apscheduler 3.10.4 + pytz 2024.1 already pinned, [STACK BUMP] 불필요
19. **AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory** — `Depends(require_any_role('owner', 'admin'))`

## Architecture Alignment ALLOWED sweep

- ALLOWED_SERVICE_SUBMODULES EXTENSION `m30_reports_scheduled` 신규 EXTENSION 결정 wire
- ALLOWED_MODULES_LIST EXTENSION `apps/api/jobs/scheduled_reports.py` + `apps/api/modules/reports/scheduled_*.py` EXTENSION
- ALLOWED_ROUTER_LIST EXTENSION `scheduled_reports_router` include 결정 wire
- ALLOWED_AUDIT_ACTIONS EXTENSION `export_scheduled` Literal preserved (cj-285)
- ALLOWED_CAPABILITIES EXTENSION `Capability.EXPORT_SCHEDULED` preserved (cj-285)
- ALLOWED_STACK_PINS EXTENSION `apscheduler 3.10.4 + pytz 2024.1` already pinned

## Files Affected ~15 files estimate (cj-300 wire atomic sprint cj-style 302nd)

- 1 NEW `apps/api/jobs/scheduled_reports.py` (~260 LOC)
- 1 NEW `apps/api/alembic/versions/0061_phase_30_story_30_4_finance_contact_email.py` (~120 LOC)
- 1 NEW `apps/api/modules/reports/scheduled_routes.py` (~280 LOC)
- 1 NEW `apps/api/modules/reports/scheduled_serializers.py` (~205 LOC)
- 1 MODIFIED `apps/api/core/errors.py` (16 NEW typed exception EXTENSION)
- 1 MODIFIED `apps/api/main.py` (line ~700+ EXTENSION startup hook + scheduled_reports_router include)
- 1 NEW `apps/web/app/[locale]/(dashboard)/reports/scheduled/page.tsx`
- 1 NEW `apps/web/components/reports/ScheduledJobsList.tsx` (~280 LOC)
- 1 MODIFIED `apps/web/components/reports/ReportsTabNav.tsx` (3-tab → 4-tab UX EXTENSION)
- 1 NEW `tests/integration/test_phase_30_scheduled_reports.py` (~360 LOC, 60+ tests)
- 1 NEW `apps/web/__tests__/components/ScheduledJobsList.test.tsx` (~125 LOC, 6 tests)
- 1 NEW `apps/api/scripts/cli/scheduled_reports_dry_run.py` + `--scheduled-reports-dry-run` flag
- 1 NEW `apps/api/scripts/cli/scheduled_reports_finance_contact_email_dry_run.py` + `--scheduled-reports-finance-contact-email-dry-run` flag
- = **15 files atomic single sprint estimate** (cj-style 302번째 wire atomic sprint)

## 3중 게이트 impact

- **cj-300 entry** (현재 sprint) = 0 NEW source / docs-only atomic single sprint (5 files 결정 wire)
- **cj-300 wire atomic (cj-style 302nd)** = ~+60 NEW pytest cases (60+ tests in test_phase_30_scheduled_reports.py) / ~+6 NEW vitest cases (6 tests in ScheduledJobsList.test.tsx) / 0 NEW tsc (TypeScript mirror) / 0 NEW ruff (verbatim pattern + banker's rounding + ALLOWED sweep)
- **cj-300 close-out retro (cj-style 303rd)** = 0 NEW (docs-only atomic single sprint, 14-section §1~§14 retro document)

## 결정 wire 일자

2026-09-07 (KST) — cj-300 entry decision wire 진입 시점