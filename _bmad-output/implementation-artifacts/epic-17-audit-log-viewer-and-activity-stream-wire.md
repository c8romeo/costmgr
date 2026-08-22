---
baseline_commit: 40a9c41
---

# Story epic-17.1: Audit Log Viewer & Activity Stream wire (Epic 17 cj-style 2번째 진입점)

Status: ready-for-dev

<!-- Epic 17 cj-style 2번째 진입점 = cj-style 81번째 epic 연속 정직 회복 bmad-create-story spec.
     Epic 17 PRD entry (`epic-17-prd-entry: done`, 2026-08-22, commit `40a9c41`) 직후.
     master PRD v3.6 §F21 verbatim + AD-32 verbatim + A153+A154+A155+A156+A157 결정 wire.
     T1~T8 wire scope (Audit Log Viewer & Activity Stream territory = audit log query API + audit log viewer UI + activity stream UI + cross-region audit log visibility + CSV export + Capability v1.30 EXTENSION AUDIT_LOG_VIEW 1 NEW row + tests + 3중 게이트 FINAL CLEAN 결정).
     Epic 17 PRD entry 진입 시점에 audit-first INSERT CR 1-1 의 누적된 audit_log table 에 대한 audit log viewer territory 의 natural next 진입 + Phase 5 multi-region wire `f093f8c` 의 cross-region audit log visibility 자연스러운 carry-over chain 결정 wire 진입 (Phase 5 PRD §F20.4 verbatim cross-region audit metadata decision + Epic 17 §F21.4 결정 wire 정합).
     D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존 (cj-style Epic 15 wire 60~61번째 honest-DEFER discipline 검증 — Epic 17 spec entry 진입 시점에 grep guard INVERSION 또는 test rename 결정 wire 보존).
     D-EPIC-16-REVIEW-DEFER-1 (C1) ✅ RESOLVED (cj-style 71번째 T4 follow-up wire DONE 진입 시점 frontend 12 files 결정 wire).
     D-EPIC-16-REVIEW-DEFER-2~6 (H8+M5+M7+M9+L11) ✅ RESOLVED (cj-style 78번째 결정 wire 완료, sprint DONE 진입 시점에 모두 정직 회복 결정 wire 완료).
     D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED 보존 (cj-style 73~76번째 epic 연속 정직 회복 결정 wire 완료).
     A19 cohesion pattern 9 surface EXTENSION PASS 결정 (audit log viewer surface EXTENSION = F21.1~F21.6 audit log viewer & activity stream territory).
     CR lessons applied (cj-style 81번째 epic 연속 정직 회복 docs only wire 진입 시점에 결정): CR 0-2 RLS + CR 1-1 audit-first INSERT + CR 9-6 commit message discipline + CR 11-3 honest-DEFER discipline + CR 11-4 D-001~D-005 + P-015 + CR 12-1 L4 industry-agnostic capability + CR 12-5 D-14 typed exception envelope + D-PARITY-01 inversion + D-GATE-01 inversion + A19 cohesion pattern + A36 SDR 검증 4-step 자동 적용 + AD-14 stack pin + AD-22 owner-only RBAC + NFR4 PII minimization. -->

## Story

As a **costmgr product owner**,
I want the **Epic 17 Audit Log Viewer & Activity Stream territory fully wired end-to-end with audit log query API (`apps/api/modules/audit/audit_log_query.py` NEW ~180 LOC + 4 functions: `query_audit_log` + `count_audit_log` + `get_audit_log_entry` + `query_activity_stream` + AuditLogQueryFilters + AuditLogEntry + AuditLogPage + ActivityStreamGroup TypedDict + RLS 자동 적용 CR 0-2 verbatim + owner/admin role required + capability gate AUDIT_LOG_VIEW) + audit log viewer UI (`apps/web/app/[locale]/(dashboard)/audit-log/page.tsx` NEW ~200 LOC + 5 components: `AuditLogFilterPanel` + `AuditLogTable` + `AuditLogPagination` + `AuditLogExportButton` + `AuditLogDetailModal` + ko-KR.json `audit_log.*` namespace EXTENSION 14 keys + `(dashboard)` route group 보호 Phase 3-1 T4 wire 정합 + `apps/web/lib/audit/audit-log-client.ts` NEW + vitest RTL render discipline CR 11-4 D-003 verbatim) + activity stream UI (`apps/web/app/[locale]/(dashboard)/activity/page.tsx` NEW ~150 LOC + 3 components: `ActivityStreamTimeline` + `ActivityStreamEntry` + `ActivityStreamWindowSelector` + ko-KR.json `activity.*` namespace EXTENSION 8 keys + all tenant members 권한 `require_role('owner', 'admin', 'member', 'viewer')`) + cross-region audit log visibility (Phase 5 wire `f093f8c` 의 `phase_5_replication_lag` table EXTENSION + Supabase multi-region primary Seoul + secondary Tokyo replica + read-only routing + lag_bytes ≤ 100MB + lag_seconds ≤ 30s threshold 정합 + Sentry breadcrumb) + CSV export (`apps/api/modules/audit/audit_log_export.py` NEW ~120 LOC + `export_audit_log_csv(tenant_id, filters, actor_id) -> StreamingResponse` + Excel-compatible UTF-8 BOM + comma-separated + double-quote escape for payload_json + streaming response + audit-first INSERT `audit_log_exported` CR 1-1 verbatim + CR 12-5 D-14 error envelope `AUDIT_LOG_EXPORT_FORBIDDEN_KO` + `AUDIT_LOG_EXPORT_TOO_LARGE_KO`) + capability gates AUDIT_LOG_VIEW (capability matrix v1.29 → v1.30 EXTENSION 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅ CR 12-1 L4 precedent 미러 + drift detector `tests/integration/test_capability_matrix_v1_30_drift.py` NEW)**,
so that **Epic 17 territory 가 wire 되어 audit-first INSERT CR 1-1 의 누적된 audit_log table 에 대한 audit log viewer territory 의 natural next 진입 완료 + Phase 5 multi-region wire `f093f8c` 의 cross-region audit log visibility 자연스러운 carry-over chain 정합 + 1차 출시 후 enterprise 고객 유치 시 audit log audit & compliance (SOC2/GDPR) 인프라 정합 + activity stream 을 통한 tenant member 실시간 활동 추적 + CSV export 으로 audit log 외부 retention 시스템 연동 + capability matrix v1.30 EXTENSION 1 NEW gate industry-agnostic 4-industry grants 모두 production-grade 로 동작 + D-1-1-DEFER-* ✅ RESOLVED + D-EPIC-16-REVIEW-DEFER-1 ✅ RESOLVED + D-EPIC-16-REVIEW-DEFER-2~6 ✅ RESOLVED + D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED 결정 wire + Epic 1 ~ Epic 16 + Phase 3 + Phase 4 + Phase 5 + 1st release cycle 정합 보존**합니다.

## Acceptance Criteria

PRD §F21.1 ~ §F21.7 verbatim + AD-32 verbatim + Epic 17 PRD entry (commit `40a9c41`) §F21.7 wire scope T1~T8 결정 verbatim.

### F21.1 audit log query API (A155 결정, AD-32 (a) verbatim)

- [ ] **AC1.1** `apps/api/modules/audit/audit_log_query.py` NEW (~+180 LOC, atomic) — audit log query API 결정 wire (PRD §F21.1 verbatim).
- [ ] **AC1.2** **`query_audit_log(tenant_id, filters, page, page_size) -> AuditLogPage`** 결정 wire (PRD §F21.1 verbatim): `tenant_id: str` + `filters: AuditLogQueryFilters` + `page: int = 1` + `page_size: int = 50` 결정 + returns `AuditLogPage` TypedDict (`entries: list[AuditLogEntry]` + `total: int` + `page: int` + `page_size: int` + `has_next: bool`).
- [ ] **AC1.3** **`count_audit_log(tenant_id, filters) -> int`** 결정 wire (PRD §F21.1 verbatim): total count without pagination 결정.
- [ ] **AC1.4** **`get_audit_log_entry(tenant_id, entry_id) -> AuditLogEntry`** 결정 wire (PRD §F21.1 verbatim): single audit log entry 조회 + RLS 자동 적용.
- [ ] **AC1.5** **`query_activity_stream(tenant_id, window_days) -> list[ActivityStreamGroup]`** 결정 wire (PRD §F21.1 verbatim): `window_days: Literal[1, 7, 30, 90]` 결정 + returns grouped activity stream (`timestamp_bucket: str` + `entry_count: int` + `top_actions: list[str]` + `top_actors: list[str]`).
- [ ] **AC1.6** **`AuditLogQueryFilters` TypedDict** 결정 wire (PRD §F21.1 verbatim): `actor_id: Optional[str]` + `action: Optional[str]` + `action_class: Optional[ActionClass]` + `resource_type: Optional[str]` + `resource_id: Optional[str]` + `start_date: Optional[datetime]` + `end_date: Optional[datetime]` + `trace_id: Optional[str]` + `tenant_id: str` (REQUIRED for RLS).
- [ ] **AC1.7** **`AuditLogEntry` TypedDict** 결정 wire (PRD §F21.1 verbatim): `id: int` + `tenant_id: str` + `actor_id: str` + `action: str` + `action_class: str` + `resource_type: Optional[str]` + `resource_id: Optional[str]` + `payload: dict[str, Any]` + `ip_address: Optional[str]` + `user_agent: Optional[str]` + `trace_id: str` + `created_at: datetime`.
- [ ] **AC1.8** **`ActivityStreamGroup` TypedDict** 결정 wire (PRD §F21.1 verbatim): `timestamp_bucket: str` + `entry_count: int` + `top_actions: list[str]` + `top_actors: list[str]`.
- [ ] **AC1.9** **RLS 자동 적용 (CR 0-2 RLS lesson verbatim)** 결정 wire (PRD §F21.1 verbatim): audit_log table 의 SELECT 는 tenant_id 기반으로 자동 isolation 결정 wire + tenant_id 가 다른 row 는 자동으로 invisible (Postgres RLS policy 결정 wire) + 모든 query 함수가 `tenant_id` parameter 를 필수로 받아 자동 RLS 검증.
- [ ] **AC1.10** **owner/admin role required (AD-22 owner-only RBAC + audit log viewer 보호)** 결정 wire (PRD §F21.1 verbatim): `query_audit_log` + `count_audit_log` + `get_audit_log_entry` 는 `Depends(require_role("owner", "admin"))` 결정 wire (audit log 는 owner + admin 만 조회 가능, member + viewer 차단). `query_activity_stream` 는 `Depends(require_role("owner", "admin", "member", "viewer"))` 결정 wire (activity stream 은 all tenant members 권한).
- [ ] **AC1.11** **capability gate AUDIT_LOG_VIEW (CR 12-5 D-GATE-01 inversion verbatim)** 결정 wire (PRD §F21.1 verbatim): `Depends(require_capability(Capability.AUDIT_LOG_VIEW))` 결정 wire + per-tenant on/off 결정 wire (capability matrix v1.30 EXTENSION 정합).
- [ ] **AC1.12** **error envelope (CR 12-5 D-14 typed exception envelope verbatim)** 결정 wire (PRD §F21.1 verbatim): `AuditLogQueryInvalidFilterError` (`code='AUDIT_LOG_QUERY_INVALID_FILTER_KO'` + `message_ko='잘못된 audit log filter 입니다'` + 400) + `AuditLogEntryNotFoundError` (`code='AUDIT_LOG_ENTRY_NOT_FOUND_KO'` + `message_ko='audit log entry 를 찾을 수 없습니다'` + 404).
- [ ] **AC1.13** **`GET /api/v1/audit-log` route** 결정 wire (PRD §F21.1 verbatim): query param `filters` + `page` + `page_size` 결정 + response `AuditLogPage` 결정.
- [ ] **AC1.14** **`GET /api/v1/audit-log/{entry_id}` route** 결정 wire (PRD §F21.1 verbatim): single entry 조회 + 404 envelope 결정.
- [ ] **AC1.15** **`GET /api/v1/audit-log/count` route** 결정 wire (PRD §F21.1 verbatim): count 조회 + filter 동일 결정.
- [ ] **AC1.16** **`GET /api/v1/activity` route** 결정 wire (PRD §F21.1 verbatim): activity stream 조회 + window_days param 결정.

### F21.2 audit log viewer UI (A155 결정, AD-32 (b) verbatim)

- [ ] **AC2.1** `apps/web/app/[locale]/(dashboard)/audit-log/page.tsx` NEW (~+200 LOC, atomic) — audit log viewer UI 결정 wire (PRD §F21.2 verbatim, Server Component 결정 + Client Component 분리 결정).
- [ ] **AC2.2** **`AuditLogFilterPanel` component** 결정 wire (PRD §F21.2 verbatim): actor_id filter + action filter + action_class filter + resource_type filter + start_date filter + end_date filter + trace_id filter 결정 + URL query param sync 결정 wire (refresh-friendly 결정).
- [ ] **AC2.3** **`AuditLogTable` component** 결정 wire (PRD §F21.2 verbatim): columns = created_at (timestamp) + actor_id + action_class + action + resource_type + resource_id + trace_id (link to detail modal) 결정 + virtualization 결정 wire 보류 (page_size=50 기본값 결정).
- [ ] **AC2.4** **`AuditLogPagination` component** 결정 wire (PRD §F21.2 verbatim): prev/next page + page number + total entries 결정 + URL query param sync.
- [ ] **AC2.5** **`AuditLogExportButton` component** 결정 wire (PRD §F21.2 verbatim): "Export CSV" button 결정 + filter snapshot 적용 결정 (현재 filter 그대로 export) + owner/admin 만 노출 결정 (member + viewer 차단) + 클릭 시 backend `GET /api/v1/audit-log/export` 호출 결정 wire.
- [ ] **AC2.6** **`AuditLogDetailModal` component** 결정 wire (PRD §F21.2 verbatim): entry_id 클릭 시 modal open 결정 + payload 전체 + actor_id + ip_address + user_agent + trace_id 결정 + "copy trace_id" button 결정 wire.
- [ ] **AC2.7** **`(dashboard)` route group 보호** 결정 wire (PRD §F21.2 verbatim, Phase 3-1 T4 wire 정합): `apps/web/app/[locale]/(dashboard)/audit-log/page.tsx` 가 `(dashboard)` route group 안에 위치 결정 wire + layout.tsx 가 auth check + role check 자동 적용 결정.
- [ ] **AC2.8** **`apps/web/lib/audit/audit-log-client.ts` NEW** 결정 wire (PRD §F21.2 verbatim, ~+80 LOC, fetch wrapper 결정): `fetchAuditLog(filters, page, pageSize) -> Promise<AuditLogPage>` + `fetchAuditLogEntry(entryId) -> Promise<AuditLogEntry>` + `fetchAuditLogCount(filters) -> Promise<number>` + `exportAuditLogCsv(filters, actorId) -> Promise<Blob>` 결정 + CR 12-5 D-14 envelope parsing 결정 wire + Bearer token forwarding 결정 wire + 401/403/404 error envelope 정합 결정.
- [ ] **AC2.9** **`apps/web/messages/ko-KR.json` EXTENSION** 결정 wire (PRD §F21.2 verbatim, CR 11-4 D-002 ko-KR.json SSOT only + P-015 SSOT discipline): `audit_log.*` namespace 14 keys 신규 결정 (e.g. `audit_log.title='감사 로그'` + `audit_log.filter.actor='실행자'` + `audit_log.filter.action='액션'` + `audit_log.filter.action_class='액션 분류'` + `audit_log.filter.resource_type='리소스 유형'` + `audit_log.filter.start_date='시작일'` + `audit_log.filter.end_date='종료일'` + `audit_log.filter.trace_id='추적 ID'` + `audit_log.column.created_at='시각'` + `audit_log.column.action='액션'` + `audit_log.column.actor='실행자'` + `audit_log.export='CSV 내보내기'` + `audit_log.detail='상세 보기'` + `audit_log.no_entries='감사 로그가 없습니다'`).
- [ ] **AC2.10** **vitest RTL render discipline (CR 11-4 D-003 verbatim)** 결정 wire (PRD §F21.2 verbatim): `apps/web/__tests__/audit-log/page.test.tsx` NEW (~+10 vitest cases) — AuditLogFilterPanel + AuditLogTable + AuditLogPagination + AuditLogExportButton + AuditLogDetailModal mount + empty state + error envelope render 검증 결정 wire.
- [ ] **AC2.11** **Owner/admin visibility (AD-22 owner-only RBAC verbatim)** 결정 wire (PRD §F21.2 verbatim): page.tsx 에서 `useSession()` hook 으로 user role 확인 결정 + owner/admin 만 audit log viewer 진입 가능 결정 wire (member + viewer 는 /audit-log 진입 시 403 redirect 결정 wire).
- [ ] **AC2.12** **TypeScript mirror parity (CR 12-5 D-PARITY-01 inversion verbatim)** 결정 wire (PRD §F21.2 verbatim): Python backend `AuditLogEntry` TypedDict ↔ TypeScript frontend `AuditLogEntry` interface 결정 wire (verbatim bind 결정 wire + AuditLogQueryFilters ↔ AuditLogQueryFilters interface 결정 wire).

### F21.3 activity stream UI (A155 결정, AD-32 (c) verbatim)

- [ ] **AC3.1** `apps/web/app/[locale]/(dashboard)/activity/page.tsx` NEW (~+150 LOC, atomic) — activity stream UI 결정 wire (PRD §F21.3 verbatim, Server Component 결정 + Client Component 분리 결정).
- [ ] **AC3.2** **`ActivityStreamTimeline` component** 결정 wire (PRD §F21.3 verbatim): grouped activity entries by timestamp bucket 결정 wire (1일 window → hourly buckets, 7일 window → daily buckets, 30일 window → daily buckets, 90일 window → weekly buckets 결정) + entry count per bucket + top actions + top actors 표시 결정.
- [ ] **AC3.3** **`ActivityStreamEntry` component** 결정 wire (PRD §F21.3 verbatim): single activity entry 표시 결정 (timestamp + actor_id + action + resource_type + resource_id) 결정 + click 시 해당 audit-log entry 로 이동 결정 wire (deep link 결정).
- [ ] **AC3.4** **`ActivityStreamWindowSelector` component** 결정 wire (PRD §F21.3 verbatim): window selector UI 결정 (1일 / 7일 / 30일 / 90일) 결정 + URL query param sync 결정 wire + default 7일 결정 wire.
- [ ] **AC3.5** **`apps/web/messages/ko-KR.json` EXTENSION** 결정 wire (PRD §F21.3 verbatim, CR 11-4 D-002 ko-KR.json SSOT only + P-015 SSOT discipline): `activity.*` namespace 8 keys 신규 결정 (e.g. `activity.title='활동 스트림'` + `activity.window.day_1='최근 1일'` + `activity.window.day_7='최근 7일'` + `activity.window.day_30='최근 30일'` + `activity.window.day_90='최근 90일'` + `activity.bucket.entries='건'` + `activity.bucket.top_actions='주요 액션'` + `activity.bucket.top_actors='주요 실행자'`).
- [ ] **AC3.6** **all tenant members 권한 (PRD §F21.3 verbatim, AD-22 owner-only RBAC 보존)** 결정 wire: `useSession()` hook 으로 user role 확인 결정 + owner/admin/member/viewer 모두 activity stream 진입 가능 결정 wire (require_role 4종 모두 허용 결정).
- [ ] **AC3.7** **vitest RTL render discipline (CR 11-4 D-003 verbatim)** 결정 wire (PRD §F21.3 verbatim): `apps/web/__tests__/activity/page.test.tsx` NEW (~+10 vitest cases) — ActivityStreamTimeline + ActivityStreamEntry + ActivityStreamWindowSelector mount + window change + empty state 검증 결정 wire.
- [ ] **AC3.8** **TypeScript mirror parity (CR 12-5 D-PARITY-01 inversion verbatim)** 결정 wire (PRD §F21.3 verbatim): Python backend `ActivityStreamGroup` TypedDict ↔ TypeScript frontend `ActivityStreamGroup` interface 결정 wire.

### F21.4 cross-region audit log visibility (A155 결정, AD-32 (d) verbatim, Phase 5 carry-over)

- [ ] **AC4.1** **Phase 5 wire `f093f8c` 의 `phase_5_replication_lag` table EXTENSION** 결정 wire (PRD §F21.4 verbatim, Phase 5 carry-over chain 결정 wire): audit_log query 시 secondary region 의 read replica 에서 query 가능 결정 wire.
- [ ] **AC4.2** **Supabase multi-region primary Seoul + secondary Tokyo replica** 결정 wire (PRD §F21.4 verbatim, AD-9 Seoul region 정합 + Phase 5 wire `f093f8c` EXTENSION 결정 wire): audit_log table 의 read replica 를 Tokyo region 에 유지 결정 wire + primary region (Seoul) write + secondary region (Tokyo) read 결정.
- [ ] **AC4.3** **Read-only routing 결정** 결정 wire (PRD §F21.4 verbatim): `apps/api/modules/audit/audit_log_query.py` 의 SELECT query 가 secondary region (Tokyo) 의 read replica 로 routing 결정 wire + Supabase client 가 read-only endpoint 사용 결정 + 자동 retry on replica failure 결정.
- [ ] **AC4.4** **읽기 일관성 lag_bytes ≤ 100MB + lag_seconds ≤ 30s threshold 정합 (Phase 5 wire 정합)** 결정 wire (PRD §F21.4 verbatim): `phase_5_replication_lag` table 의 `lag_bytes` + `lag_seconds` 가 threshold 초과 시 primary region 으로 fallback 결정 wire + audit log query 가 lag threshold 자동 검증 결정 wire.
- [ ] **AC4.5** **Sentry breadcrumb 결정** 결정 wire (PRD §F21.4 verbatim): lag 초과 시 `apps/api/core/observability.py` EXTENSION + `sentry_sdk.capture_message(f"Audit log read replica lag exceeded: lag_bytes={lag_bytes}, lag_seconds={lag_seconds}", level="warning")` 결정 wire + Sentry alert routing 결정.
- [ ] **AC4.6** **Multi-region audit log visibility (PRD §F21.4 verbatim)** 결정 wire: audit log viewer UI 가 secondary region read replica 에서 query 가능 결정 wire + 동일 결과 보장 결정 (read-after-write consistency 는 eventual 정합 결정 wire).
- [ ] **AC4.7** **`tests/api/modules/audit/test_audit_log_cross_region.py` NEW (~+5 pytest cases)** 결정 wire (PRD §F21.4 verbatim): cross-region audit log visibility 검증 결정 wire (1) read replica routing / (2) lag threshold 검증 / (3) primary fallback / (4) Sentry breadcrumb 발송 / (5) multi-region RLS isolation 유지.

### F21.5 CSV export (A155 결정, AD-32 (e) verbatim)

- [ ] **AC5.1** `apps/api/modules/audit/audit_log_export.py` NEW (~+120 LOC, atomic) — CSV export 결정 wire (PRD §F21.5 verbatim).
- [ ] **AC5.2** **`export_audit_log_csv(tenant_id, filters, actor_id) -> StreamingResponse`** 결정 wire (PRD §F21.5 verbatim): streaming response 결정 + UTF-8 BOM (`﻿` prefix) 결정 + comma-separated 결정 + Excel-compatible 결정 (CRLF line ending 결정 wire).
- [ ] **AC5.3** **Double-quote escape for payload_json** 결정 wire (PRD §F21.5 verbatim): payload_json field 가 comma/newline 포함 시 double-quote 로 wrap + internal `"` 를 `""` 로 replace (Excel CSV escape rule 결정 wire).
- [ ] **AC5.4** **`GET /api/v1/audit-log/export` route** 결정 wire (PRD §F21.5 verbatim): query param `filters` 결정 + response `StreamingResponse(media_type='text/csv', headers={'Content-Disposition': 'attachment; filename="audit-log-{tenant_id}-{timestamp}.csv"'})` 결정.
- [ ] **AC5.5** **audit-first INSERT `audit_log_exported` (CR 1-1 verbatim)** 결정 wire (PRD §F21.5 verbatim): `audit_logs` table INSERT per export trigger: `action_class='AUDIT'` (신규 ActionClass 결정 wire, AD-32 (f) verbatim) + `action='audit_log_exported'` + `actor_id` (export trigger user) + `tenant_id` + `filters_json` (export 시점 filter) + `row_count` (exported row count) + `trace_id` 결정 — 누가 언제 어떤 filter 로 export 했는지 추적.
- [ ] **AC5.6** **size limit protection** 결정 wire (PRD §F21.5 verbatim): `MAX_EXPORT_ROWS = 100_000` 결정 wire (RO 크기 export 방지) + size limit 초과 시 error envelope 결정.
- [ ] **AC5.7** **error envelope (CR 12-5 D-14 typed exception envelope verbatim)** 결정 wire (PRD §F21.5 verbatim): 2 NEW error classes: `AuditLogExportForbiddenError` (`code='AUDIT_LOG_EXPORT_FORBIDDEN_KO'` + `message_ko='audit log export 권한이 없습니다'` + 403, member/viewer 차단) + `AuditLogExportTooLargeError` (`code='AUDIT_LOG_EXPORT_TOO_LARGE_KO'` + `message_ko='export 행 수가 너무 많습니다 (최대 100,000건)'` + 413).
- [ ] **AC5.8** **`tests/api/modules/audit/test_audit_log_export.py` NEW (~+8 pytest cases)** 결정 wire (PRD §F21.5 verbatim): CSV export 검증 결정 wire (1) UTF-8 BOM / (2) comma-separated / (3) double-quote escape / (4) CRLF line ending / (5) audit-first INSERT `audit_log_exported` / (6) size limit exceeded error envelope / (7) forbidden error envelope (member/viewer 차단) / (8) streaming response media_type.

### F21.6 Capability gate AUDIT_LOG_VIEW (A155+A156 결정, AD-32 (g) verbatim)

- [ ] **AC6.1** `apps/api/core/capability.py` MODIFIED — `Capability.AUDIT_LOG_VIEW = "audit_log_view"` 1 NEW enum 결정 wire (PRD §F21.6 verbatim, Epic 17 wire 1 NEW row).
- [ ] **AC6.2** **4-industry grants industry-agnostic ✅/✅/✅/✅** 결정 wire (PRD §F21.6 verbatim + CR 12-1 L4 precedent 미러): manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ (industry-agnostic, MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern verbatim bind). 4 industry 블록 모두에 `Capability.AUDIT_LOG_VIEW,` 추가 결정 wire.
- [ ] **AC6.3** `apps/api/dependencies/capability.py` EXTENSION 결정 wire — `require_capability(AUDIT_LOG_VIEW)` Dependency 1개 신규 (기존 `require_capability()` factory pattern verbatim reuse).
- [ ] **AC6.4** `docs/capability-matrix.md` v1.29 → v1.30 EXTENSION 1 NEW row 결정 wire (Epic 17 PRD entry `40a9c41` 진입 시점에 이미 row 추가됨 보존, capability.py enum 만 wire 진입). `AUDIT_LOG_VIEW` row industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정.
- [ ] **AC6.5** `tests/integration/test_capability_matrix_v1_30_drift.py` NEW (drift detector, Epic 16 `test_capability_matrix_v1_28_drift.py` + Phase 5 `test_capability_matrix_v1_29_drift.py` 패턴 verbatim bind) — `AUDIT_LOG_VIEW` 1 NEW row SSOT 정합 sweep (~+7 NEW pytest cases 결정).
- [ ] **AC6.6** **미허용 tenant 의 audit log viewer 진입 차단** 결정 wire (PRD §F21.6 verbatim, CR 12-5 D-GATE-01 inversion): capability gate `AUDIT_LOG_VIEW` 가 off 인 tenant 의 audit log query 시 403 envelope 결정 wire + `audit_log_viewer_disabled` envelope code 결정.

### F21.7 tests + wire scope T1~T8 결정 (cj-style 80번째 결정 wire 진입 시점에 적용)

- [ ] **AC7.1** `tests/api/modules/audit/test_audit_log_query.py` NEW (~+15 pytest cases) — audit log query API 검증 결정 wire: (1) query_audit_log filter 조합 / (2) count_audit_log filter 동일 / (3) get_audit_log_entry 404 envelope / (4) query_activity_stream window_days 4종 / (5) RLS 자동 적용 tenant_id isolation / (6) AuditLogQueryInvalidFilterError 400 envelope / (7) AuditLogEntryNotFoundError 404 envelope / (8) owner/admin role required / (9) member/viewer 차단 / (10) capability gate AUDIT_LOG_VIEW per-tenant on/off / (11) page_size validation / (12) has_next computation / (13) audit_first INSERT `audit_log_exported` 검증 / (14) timestamp sorting / (15) trace_id filter.
- [ ] **AC7.2** `tests/api/modules/audit/test_audit_log_export.py` NEW (~+8 pytest cases) — CSV export 검증 결정 wire (AC5.8 verbatim).
- [ ] **AC7.3** `tests/api/modules/audit/test_audit_log_cross_region.py` NEW (~+5 pytest cases) — cross-region audit log visibility 검증 결정 wire (AC4.7 verbatim).
- [ ] **AC7.4** `tests/integration/test_capability_matrix_v1_30_drift.py` NEW (drift detector, P-015 SSOT drift detector + Phase 5 v1.29 + Epic 16 v1.28 precedent verbatim) — `AUDIT_LOG_VIEW` 1 NEW row SSOT 정합 sweep (industry-agnostic 4-industry grants ✅/✅/✅/✅).
- [ ] **AC7.5** `tests/api/modules/audit/test_audit_log_audit_first.py` NEW (~+5 pytest cases) — audit-first INSERT `audit_log_exported` 검증 결정 wire (CR 1-1 verbatim, ActionClass.AUDIT 신규 + actor_id + tenant_id + filters_json + row_count + trace_id).
- [ ] **AC7.6** `apps/web/__tests__/audit-log/page.test.tsx` NEW (~+10 vitest cases) — `apps/web/app/[locale]/(dashboard)/audit-log/page.tsx` RTL render 결정 wire: (1) page mount / (2) AuditLogFilterPanel render / (3) AuditLogTable render / (4) AuditLogPagination render / (5) AuditLogExportButton owner/admin 만 노출 / (6) AuditLogExportButton member/viewer 차단 / (7) AuditLogDetailModal open + close / (8) empty state render / (9) error envelope render / (10) 403 redirect for member/viewer.
- [ ] **AC7.7** `apps/web/__tests__/audit-log/audit-log-client.test.ts` NEW (~+10 vitest cases) — `apps/web/lib/audit/audit-log-client.ts` fetch wrapper 검증 결정 wire: (1) fetchAuditLog API call / (2) fetchAuditLogEntry API call / (3) fetchAuditLogCount API call / (4) exportAuditLogCsv Blob response / (5) CR 12-5 D-14 envelope parsing / (6) Bearer token forwarding / (7) 401 error envelope / (8) 403 error envelope / (9) 404 error envelope / (10) 413 AUDIT_LOG_EXPORT_TOO_LARGE_KO envelope.
- [ ] **AC7.8** `apps/web/__tests__/activity/page.test.tsx` NEW (~+10 vitest cases) — `apps/web/app/[locale]/(dashboard)/activity/page.tsx` RTL render 결정 wire: (1) page mount / (2) ActivityStreamTimeline render / (3) ActivityStreamEntry render / (4) ActivityStreamWindowSelector render / (5) window change / (6) empty state render / (7) error envelope render / (8) all tenant members visibility / (9) entry deep link to audit-log detail / (10) timestamp bucket grouping.
- [ ] **AC7.9** `apps/web/__tests__/audit-log/page.test.tsx` AC3.2 + AC3.5 ko-KR.json SSOT parity test 결정 wire (PRD §F21.2 verbatim, CR 11-4 D-002 + P-015 verbatim): `audit_log.*` namespace 14 keys 검증 + hardcoded Korean literal 검증 제거 결정 wire + 1 NEW file = `apps/web/__tests__/i18n/audit-log-i18n-ssot.test.ts`.
- [ ] **AC7.10** `apps/web/__tests__/activity/page.test.tsx` AC3.5 ko-KR.json SSOT parity test 결정 wire (PRD §F21.3 verbatim): `activity.*` namespace 8 keys 검증 결정 wire + 1 NEW file = `apps/web/__tests__/i18n/activity-i18n-ssot.test.ts`.
- [ ] **AC7.11** `apps/api/core/audit_action.py` MODIFIED — `ActionClass.AUDIT = "audit"` 1 NEW enum 결정 wire (F21.5 audit-first INSERT `audit_log_exported` 의 action_class 결정, AD-32 (f) verbatim) + registry entry frozenset 1 action: `audit_log_exported` 결정.
- [ ] **AC7.12** `apps/api/modules/audit/__init__.py` NEW (empty marker 결정 wire) + `apps/api/modules/audit/` directory 신규 결정 wire (audit log viewer + activity stream + CSV export modules 통합 결정).
- [ ] **AC7.13** `apps/web/lib/audit/__init__.py` NEW (empty marker 결정 wire) + `apps/web/lib/audit/audit-log-client.ts` NEW (frontend fetch wrapper 결정 wire).
- [ ] **AC7.14** **3중 게이트 FINAL CLEAN** 결정 wire — (1) `pnpm tsc --noEmit` 0 NEW errors (Epic 17 frontend files clean — pre-existing 19 baseline errors unrelated 보존) / (2) `pnpm vitest run` 102+10 = **~112/112 PASS** (Epic 17 +10 NEW vitest cases, 0 regressions) / (3) `ruff check` scoped Epic 17 wire Python files = **All checks passed!** (scoped to Epic 17 NEW Python files only) / (4) `pytest` 4176+30 = **~4206/4206 PASS** (Epic 17 +30 NEW pytest cases, 0 NEW regressions; baseline 1 unrelated pre-existing failure 보존) / (5) SDR drift gate PASS (MAX claim 4176 → **~4206** actual pytest --collect-only -q = +30 from Epic 17 T1~T7 NEW pytest cases) / (6) commit_consistency gate PASS (CR 9-6 + A36).
- [ ] **AC7.15** **A36 SDR 검증 4-step 자동 적용 PASS** 결정 wire — (1) commit prefix lint (CR 9-6 D5 prevention, `git commit -F <file>`) / (2) sprint-status structure 정합 (D4 fix 보존) / (3) vitest file count drift 0건 (D2 fix 보존) / (4) commit consistency 정합 (D1 fix 보존).
- [ ] **AC7.16** atomic commit + sprint-status `epic-17-audit-log-viewer-and-activity-stream-wire: backlog → done` + handoff memory 신규 + atomic 11-14 files 결정 wire 진입.

## Tasks / Subtasks

- [ ] **Task 1 — T1: audit log query API + 4 functions + TypedDict wire** (AC: #1.1, #1.2, #1.3, #1.4, #1.5, #1.6, #1.7, #1.8, #1.9, #1.10, #1.11, #1.12, #1.13, #1.14, #1.15, #1.16, #7.1, #7.11, #7.12)
  - [ ] Subtask 1.1 — `apps/api/modules/audit/__init__.py` NEW (empty marker 결정 wire, `apps/api/modules/audit/` directory 신규 결정 wire)
  - [ ] Subtask 1.2 — `apps/api/modules/audit/audit_log_query.py` NEW (~+180 LOC): `query_audit_log` + `count_audit_log` + `get_audit_log_entry` + `query_activity_stream` 4 functions 결정 wire
  - [ ] Subtask 1.3 — `AuditLogQueryFilters` + `AuditLogEntry` + `AuditLogPage` + `ActivityStreamGroup` TypedDict 4 결정 wire (AC1.6+AC1.7+AC1.8 verbatim)
  - [ ] Subtask 1.4 — RLS 자동 적용 (CR 0-2 RLS lesson verbatim) 결정 wire: audit_log table 의 SELECT 는 tenant_id 기반으로 자동 isolation 결정 wire + 모든 query 함수가 `tenant_id` parameter 필수 검증
  - [ ] Subtask 1.5 — owner/admin role required (AD-22 owner-only RBAC) 결정 wire: `Depends(require_role("owner", "admin"))` 적용 (audit log 는 owner + admin 만 조회 가능)
  - [ ] Subtask 1.6 — `query_activity_stream` 의 all tenant members 권한 결정 wire: `Depends(require_role("owner", "admin", "member", "viewer"))` 적용
  - [ ] Subtask 1.7 — capability gate `AUDIT_LOG_VIEW` (CR 12-5 D-GATE-01 inversion verbatim) 결정 wire: `Depends(require_capability(Capability.AUDIT_LOG_VIEW))` 적용 + per-tenant on/off 검증
  - [ ] Subtask 1.8 — 2 NEW error classes (CR 12-5 D-14 envelope verbatim): `AuditLogQueryInvalidFilterError` 400 + `AuditLogEntryNotFoundError` 404
  - [ ] Subtask 1.9 — `apps/api/modules/audit/audit_log_routes.py` NEW (~+80 LOC): 4 routes 결정 wire (`GET /api/v1/audit-log` + `GET /api/v1/audit-log/{entry_id}` + `GET /api/v1/audit-log/count` + `GET /api/v1/activity`)
  - [ ] Subtask 1.10 — `apps/api/main.py` EXTENSION: audit_log_routes 등록 + lifecycle hook 결정 wire
  - [ ] Subtask 1.11 — `apps/api/core/audit_action.py` MODIFIED: `ActionClass.AUDIT = "audit"` 1 NEW enum 결정 wire (F21.5 audit-first INSERT `audit_log_exported` 용) + registry entry frozenset 1 action `audit_log_exported` 결정 wire
  - [ ] Subtask 1.12 — `tests/api/modules/audit/test_audit_log_query.py` NEW (~+15 pytest cases) — 15 verification steps (AC7.1 verbatim)
  - [ ] Subtask 1.13 — `tests/api/modules/audit/test_audit_log_audit_first.py` NEW (~+5 pytest cases) — audit-first INSERT `audit_log_exported` 검증 (CR 1-1 verbatim)

- [ ] **Task 2 — T2: audit log viewer UI + 5 components + ko-KR.json EXTENSION wire** (AC: #2.1, #2.2, #2.3, #2.4, #2.5, #2.6, #2.7, #2.8, #2.9, #2.10, #2.11, #2.12, #7.6, #7.9)
  - [ ] Subtask 2.1 — `apps/web/app/[locale]/(dashboard)/audit-log/page.tsx` NEW (~+200 LOC, atomic, Server Component 결정 + Client Component 분리 결정)
  - [ ] Subtask 2.2 — `AuditLogFilterPanel` component 결정 wire (PRD §F21.2 verbatim): 7 filter fields + URL query param sync 결정
  - [ ] Subtask 2.3 — `AuditLogTable` component 결정 wire: columns = created_at + actor_id + action_class + action + resource_type + resource_id + trace_id 결정 + page_size=50 default
  - [ ] Subtask 2.4 — `AuditLogPagination` component 결정 wire: prev/next + page number + total entries + URL sync
  - [ ] Subtask 2.5 — `AuditLogExportButton` component 결정 wire: "Export CSV" button + filter snapshot + owner/admin 만 노출 + 클릭 시 backend `GET /api/v1/audit-log/export` 호출
  - [ ] Subtask 2.6 — `AuditLogDetailModal` component 결정 wire: entry_id 클릭 시 modal open + payload + actor_id + ip_address + user_agent + trace_id + "copy trace_id" button
  - [ ] Subtask 2.7 — `(dashboard)` route group 보호 (Phase 3-1 T4 wire 정합) 결정 wire: layout.tsx 가 auth check + role check 자동 적용
  - [ ] Subtask 2.8 — `apps/web/lib/audit/__init__.py` NEW + `apps/web/lib/audit/audit-log-client.ts` NEW (~+80 LOC): `fetchAuditLog` + `fetchAuditLogEntry` + `fetchAuditLogCount` + `exportAuditLogCsv` 결정 + CR 12-5 D-14 envelope parsing + Bearer token forwarding + 401/403/404 error envelope 정합
  - [ ] Subtask 2.9 — `apps/web/messages/ko-KR.json` EXTENSION: `audit_log.*` namespace 14 keys 신규 결정 (CR 11-4 D-002 ko-KR.json SSOT only + P-015 SSOT discipline)
  - [ ] Subtask 2.10 — `useSession()` hook 으로 user role 확인 결정 wire + owner/admin 만 audit log viewer 진입 가능 + member/viewer 는 403 redirect
  - [ ] Subtask 2.11 — TypeScript mirror parity (CR 12-5 D-PARITY-01 inversion verbatim): Python `AuditLogEntry` ↔ TypeScript `AuditLogEntry` interface verbatim bind + `AuditLogQueryFilters` ↔ `AuditLogQueryFilters` interface
  - [ ] Subtask 2.12 — `apps/web/__tests__/audit-log/page.test.tsx` NEW (~+10 vitest cases) — 10 verification steps (AC7.6 verbatim)
  - [ ] Subtask 2.13 — `apps/web/__tests__/audit-log/audit-log-client.test.ts` NEW (~+10 vitest cases) — 10 verification steps (AC7.7 verbatim)
  - [ ] Subtask 2.14 — `apps/web/__tests__/i18n/audit-log-i18n-ssot.test.ts` NEW — `audit_log.*` namespace 14 keys SSOT parity 검증 (CR 11-4 D-002 + P-015 verbatim)

- [ ] **Task 3 — T3: activity stream UI + 3 components + ko-KR.json EXTENSION wire** (AC: #3.1, #3.2, #3.3, #3.4, #3.5, #3.6, #3.7, #3.8, #7.8, #7.10)
  - [ ] Subtask 3.1 — `apps/web/app/[locale]/(dashboard)/activity/page.tsx` NEW (~+150 LOC, atomic, Server Component 결정 + Client Component 분리 결정)
  - [ ] Subtask 3.2 — `ActivityStreamTimeline` component 결정 wire: grouped by timestamp bucket (1d hourly / 7d daily / 30d daily / 90d weekly) + entry count + top actions + top actors
  - [ ] Subtask 3.3 — `ActivityStreamEntry` component 결정 wire: timestamp + actor_id + action + resource_type + resource_id + click → audit-log entry deep link
  - [ ] Subtask 3.4 — `ActivityStreamWindowSelector` component 결정 wire: 1d / 7d / 30d / 90d selector + URL query param sync + default 7d
  - [ ] Subtask 3.5 — `apps/web/messages/ko-KR.json` EXTENSION: `activity.*` namespace 8 keys 신규 결정 (CR 11-4 D-002 + P-015 SSOT discipline)
  - [ ] Subtask 3.6 — all tenant members 권한 결정 wire: `useSession()` hook 으로 user role 확인 + owner/admin/member/viewer 모두 진입 가능
  - [ ] Subtask 3.7 — TypeScript mirror parity (CR 12-5 D-PARITY-01 inversion verbatim): Python `ActivityStreamGroup` ↔ TypeScript `ActivityStreamGroup` interface verbatim bind
  - [ ] Subtask 3.8 — `apps/web/__tests__/activity/page.test.tsx` NEW (~+10 vitest cases) — 10 verification steps (AC7.8 verbatim)
  - [ ] Subtask 3.9 — `apps/web/__tests__/i18n/activity-i18n-ssot.test.ts` NEW — `activity.*` namespace 8 keys SSOT parity 검증 (CR 11-4 D-002 + P-015 verbatim)

- [ ] **Task 4 — T4: cross-region audit log visibility + Phase 5 carry-over wire** (AC: #4.1, #4.2, #4.3, #4.4, #4.5, #4.6, #4.7)
  - [ ] Subtask 4.1 — `apps/api/modules/audit/audit_log_query.py` EXTENSION: Supabase client 의 read-only endpoint 사용 결정 wire + secondary region (Tokyo) read replica routing 결정 wire + 자동 retry on replica failure 결정 wire
  - [ ] Subtask 4.2 — `phase_5_replication_lag` table 의 `lag_bytes` + `lag_seconds` threshold 검증 결정 wire (Phase 5 wire `f093f8c` EXTENSION): lag_bytes ≤ 100MB + lag_seconds ≤ 30s threshold 정합
  - [ ] Subtask 4.3 — lag threshold 초과 시 primary region 으로 fallback 결정 wire (PRD §F21.4 verbatim)
  - [ ] Subtask 4.4 — `apps/api/core/observability.py` EXTENSION: Sentry breadcrumb audit lag 결정 wire (`sentry_sdk.capture_message(f"Audit log read replica lag exceeded: lag_bytes={lag_bytes}, lag_seconds={lag_seconds}", level="warning")` + Sentry alert routing)
  - [ ] Subtask 4.5 — `tests/api/modules/audit/test_audit_log_cross_region.py` NEW (~+5 pytest cases) — 5 verification steps (AC4.7 verbatim)

- [ ] **Task 5 — T5: CSV export + audit_log_exported wire** (AC: #5.1, #5.2, #5.3, #5.4, #5.5, #5.6, #5.7, #5.8, #7.2)
  - [ ] Subtask 5.1 — `apps/api/modules/audit/audit_log_export.py` NEW (~+120 LOC): `export_audit_log_csv(tenant_id, filters, actor_id) -> StreamingResponse` 결정 wire
  - [ ] Subtask 5.2 — UTF-8 BOM (`﻿` prefix) + comma-separated + Excel-compatible CRLF 결정 wire (PRD §F21.5 verbatim)
  - [ ] Subtask 5.3 — Double-quote escape for payload_json 결정 wire: comma/newline 포함 시 double-quote wrap + internal `"` → `""` (Excel CSV escape rule)
  - [ ] Subtask 5.4 — `apps/api/modules/audit/audit_log_routes.py` EXTENSION: `GET /api/v1/audit-log/export` route 추가 결정 wire + response `StreamingResponse(media_type='text/csv', headers={'Content-Disposition': 'attachment; filename="audit-log-{tenant_id}-{timestamp}.csv"'})`
  - [ ] Subtask 5.5 — audit-first INSERT `audit_log_exported` 결정 wire (CR 1-1 verbatim, ActionClass.AUDIT 신규): `action_class='AUDIT'` + `action='audit_log_exported'` + `actor_id` + `tenant_id` + `filters_json` + `row_count` + `trace_id` — 누가 언제 어떤 filter 로 export 했는지 추적
  - [ ] Subtask 5.6 — size limit protection 결정 wire: `MAX_EXPORT_ROWS = 100_000` (RO 크기 export 방지) + size limit 초과 시 error envelope
  - [ ] Subtask 5.7 — 2 NEW error classes (CR 12-5 D-14 envelope verbatim): `AuditLogExportForbiddenError` 403 (member/viewer 차단) + `AuditLogExportTooLargeError` 413
  - [ ] Subtask 5.8 — `tests/api/modules/audit/test_audit_log_export.py` NEW (~+8 pytest cases) — 8 verification steps (AC5.8 verbatim)

- [ ] **Task 6 — T6: Capability matrix v1.29 → v1.30 EXTENSION 1 NEW row wire** (AC: #6.1, #6.2, #6.3, #6.4, #6.5, #6.6, #7.4)
  - [ ] Subtask 6.1 — `apps/api/core/capability.py` MODIFIED: `Capability.AUDIT_LOG_VIEW = "audit_log_view"` 1 NEW enum 결정 wire (PRD §F21.6 verbatim)
  - [ ] Subtask 6.2 — 4-industry grants industry-agnostic ✅/✅/✅/✅ (manufacturing + service + manufacturing_service + manufacturing_service_other, CR 12-1 L4 precedent 미러) + 4 industry 블록 모두에 `Capability.AUDIT_LOG_VIEW,` 추가 결정 wire
  - [ ] Subtask 6.3 — `apps/api/dependencies/capability.py` EXTENSION: `require_capability(AUDIT_LOG_VIEW)` Dependency 1개 신규 (기존 `require_capability()` factory pattern verbatim reuse)
  - [ ] Subtask 6.4 — `docs/capability-matrix.md` v1.29 → v1.30 EXTENSION 1 NEW row (Epic 17 PRD entry `40a9c41` 진입 시점에 이미 row 추가됨 보존)
  - [ ] Subtask 6.5 — `tests/integration/test_capability_matrix_v1_30_drift.py` NEW (drift detector, P-015 SSOT drift detector, Phase 5 v1.29 + Epic 16 v1.28 패턴 verbatim bind) — `AUDIT_LOG_VIEW` 1 NEW row SSOT 정합 sweep
  - [ ] Subtask 6.6 — 미허용 tenant 의 audit log query 시 403 envelope 결정 wire (PRD §F21.6 verbatim, CR 12-5 D-GATE-01 inversion)

- [ ] **Task 7 — T7: Tests + audit log verification + 3중 게이트** (AC: #7.1, #7.2, #7.3, #7.4, #7.5, #7.6, #7.7, #7.8, #7.9, #7.10, #7.11, #7.12, #7.13, #7.14, #7.15, #7.16)
  - [ ] Subtask 7.1 — `tests/api/modules/audit/test_audit_log_query.py` NEW (~+15 pytest cases) — 15 verification steps (AC7.1 verbatim)
  - [ ] Subtask 7.2 — `tests/api/modules/audit/test_audit_log_export.py` NEW (~+8 pytest cases) — 8 verification steps (AC5.8 verbatim)
  - [ ] Subtask 7.3 — `tests/api/modules/audit/test_audit_log_cross_region.py` NEW (~+5 pytest cases) — 5 verification steps (AC4.7 verbatim)
  - [ ] Subtask 7.4 — `tests/integration/test_capability_matrix_v1_30_drift.py` NEW (drift detector, P-015 SSOT + Phase 5 v1.29 + Epic 16 v1.28 패턴 verbatim) — `AUDIT_LOG_VIEW` 1 NEW row SSOT 정합 sweep (~+7 pytest cases)
  - [ ] Subtask 7.5 — `tests/api/modules/audit/test_audit_log_audit_first.py` NEW (~+5 pytest cases) — audit-first INSERT `audit_log_exported` 검증 (CR 1-1 verbatim)
  - [ ] Subtask 7.6 — `apps/web/__tests__/audit-log/page.test.tsx` NEW (~+10 vitest cases) — 10 verification steps
  - [ ] Subtask 7.7 — `apps/web/__tests__/audit-log/audit-log-client.test.ts` NEW (~+10 vitest cases) — 10 verification steps
  - [ ] Subtask 7.8 — `apps/web/__tests__/activity/page.test.tsx` NEW (~+10 vitest cases) — 10 verification steps
  - [ ] Subtask 7.9 — `apps/web/__tests__/i18n/audit-log-i18n-ssot.test.ts` + `apps/web/__tests__/i18n/activity-i18n-ssot.test.ts` NEW — ko-KR.json SSOT parity 검증 (CR 11-4 D-002 + P-015 verbatim)
  - [ ] Subtask 7.10 — 3중 게이트 FINAL CLEAN verification: ruff scoped Epic 17 wire Python files = All checks passed! / pytest 30 NEW PASS / vitest 10 NEW PASS / pnpm tsc --noEmit 0 NEW errors / SDR drift gate PASS / commit_consistency PASS
  - [ ] Subtask 7.11 — A36 SDR 검증 4-step 자동 적용: commit prefix lint + sprint-status structure + vitest file count drift 0건 + commit consistency 정합

- [ ] **Task 8 — T8: 3중 게이트 FINAL CLEAN + atomic commit** (AC: #7.14, #7.15, #7.16)
  - [ ] Subtask 8.1 — Final wire scope 정합 sweep: T1 audit log query API + audit_log_routes + T2 audit log viewer UI + ko-KR.json EXTENSION + T3 activity stream UI + ko-KR.json EXTENSION + T4 cross-region audit log visibility + T5 CSV export + T6 Capability v1.30 EXTENSION + T7 Tests = 11-14 files atomic single sprint
  - [ ] Subtask 8.2 — `git commit -F <file>` (CR 9-6 D5 prevention, commit-msg file 신규 = `_bmad-output/implementation-artifacts/commit-msg-epic-17-audit-log-viewer-and-activity-stream-wire.txt`)
  - [ ] Subtask 8.3 — handoff memory 신규 = `memory/handoff-2026-08-22-epic-17-audit-log-viewer-and-activity-stream-wire-done.md`
  - [ ] Subtask 8.4 — sprint-status `epic-17-audit-log-viewer-and-activity-stream-wire: backlog → done` + sprint-status structure 정합

## Dev Notes

### Source Tree Components to Touch

- **NEW (11 files)**:
  - `apps/api/modules/audit/__init__.py` (NEW, empty marker) — T1
  - `apps/api/modules/audit/audit_log_query.py` (~+180 LOC) — T1
  - `apps/api/modules/audit/audit_log_routes.py` (~+80 LOC) — T1
  - `apps/api/modules/audit/audit_log_export.py` (~+120 LOC) — T5
  - `apps/web/lib/audit/__init__.py` (NEW, empty marker) — T2
  - `apps/web/lib/audit/audit-log-client.ts` (~+80 LOC) — T2
  - `apps/web/app/[locale]/(dashboard)/audit-log/page.tsx` (~+200 LOC) — T2
  - `apps/web/app/[locale]/(dashboard)/activity/page.tsx` (~+150 LOC) — T3
  - `tests/api/modules/audit/test_audit_log_query.py` (~+15 pytest cases) — T1
  - `tests/api/modules/audit/test_audit_log_export.py` (~+8 pytest cases) — T5
  - `tests/api/modules/audit/test_audit_log_cross_region.py` (~+5 pytest cases) — T4
  - `tests/api/modules/audit/test_audit_log_audit_first.py` (~+5 pytest cases) — T1
  - `tests/integration/test_capability_matrix_v1_30_drift.py` (~+7 pytest cases) — T6
  - `apps/web/__tests__/audit-log/page.test.tsx` (~+10 vitest cases) — T2
  - `apps/web/__tests__/audit-log/audit-log-client.test.ts` (~+10 vitest cases) — T2
  - `apps/web/__tests__/activity/page.test.tsx` (~+10 vitest cases) — T3
  - `apps/web/__tests__/i18n/audit-log-i18n-ssot.test.ts` (NEW, ko-KR.json SSOT) — T2
  - `apps/web/__tests__/i18n/activity-i18n-ssot.test.ts` (NEW, ko-KR.json SSOT) — T3
  - `memory/handoff-2026-08-22-epic-17-audit-log-viewer-and-activity-stream-wire-done.md` (NEW handoff memory) — T8
  - `_bmad-output/implementation-artifacts/commit-msg-epic-17-audit-log-viewer-and-activity-stream-wire.txt` (NEW commit-msg file) — T8

- **MODIFIED (5 files)**:
  - `apps/api/main.py` — audit_log_routes 등록 + lifecycle hook EXTENSION
  - `apps/api/core/audit_action.py` — ActionClass.AUDIT + `audit_log_exported` 1 NEW action
  - `apps/api/core/capability.py` — `Capability.AUDIT_LOG_VIEW` 1 NEW enum
  - `apps/api/core/observability.py` — Sentry breadcrumb audit lag EXTENSION
  - `apps/api/dependencies/capability.py` — `require_capability(AUDIT_LOG_VIEW)` Dependency 1개 EXTENSION
  - `apps/web/messages/ko-KR.json` — `audit_log.*` 14 keys + `activity.*` 8 keys EXTENSION
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` — `epic-17-audit-log-viewer-and-activity-stream-wire: backlog → done` + A158~A162 action_items
  - `MEMORY.md` — handoff index EXTENSION

**Total wire scope (cj-style 82번째 expected)**: ~12-14 NEW files + ~6-8 MODIFIED files = ~18-22 files atomic single sprint.

### Architecture Compliance

- **CR 0-2 RLS lesson** ✅ APPLIED (audit_log_query.py + audit_log_export.py RLS 자동 적용 — tenant_id 기반 SELECT 자동 isolation 결정 wire, multi-tenant isolation test 결정 wire)
- **CR 1-1 audit-first INSERT** ✅ APPLIED (audit_log_exported 1 NEW audit log entry 결정 wire, action_class='AUDIT' + ActionClass.AUDIT 신규 정의, 누가 언제 어떤 filter 로 export 했는지 추적 결정)
- **CR 9-6 commit message discipline** ✅ APPLIED (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention)
- **CR 11-3 honest-DEFER discipline** ✅ APPLIED (81번째 epic 연속 정직 회복, D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존 + D-EPIC-16-REVIEW-DEFER-1 (C1) ✅ RESOLVED 보존 + D-EPIC-16-REVIEW-DEFER-2~6 (H8+M5+M7+M9+L11) ✅ RESOLVED 보존 78번째 + D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED 보존 73~76번째)
- **CR 11-4 D-001~D-005 + P-015 lessons carry** ✅ APPLIED (D-001 page.tsx mount MUST (layout RSC fetch + Client Component mount) + D-002 ko-KR.json SSOT only (`audit_log.*` 14 keys + `activity.*` 8 keys, drift detector 정합) + D-003 vitest RTL render (page.test.tsx ~10 cases + audit-log-client.test.ts ~10 cases + activity/page.test.tsx ~10 cases = ~30 NEW vitest cases) + D-004 TS mirror parity mandatory (audit-log-client.ts Python TypedDict ↔ TS interface verbatim bind 결정) + D-005 unknown state reject (AuditLogTable empty state + 403/404/413 error envelope render) + P-015 ko-KR.json SSOT drift detector (audit_log EXTENSION sweep + activity EXTENSION sweep))
- **CR 12-1 L4 industry-agnostic capability** ✅ APPLIED (capability matrix v1.30 EXTENSION 1 NEW row AUDIT_LOG_VIEW industry-agnostic 4-industry grants ✅/✅/✅/✅)
- **CR 12-5 D-14 typed exception envelope** ✅ APPLIED (4 NEW error classes 결정 wire: AuditLogQueryInvalidFilterError + AuditLogEntryNotFoundError + AuditLogExportForbiddenError + AuditLogExportTooLargeError)
- **CR 12-5 D-PARITY-01 inversion** ✅ APPLIED (Python FastAPI backend `AuditLogEntry` + `AuditLogQueryFilters` + `ActivityStreamGroup` TypedDict ↔ TypeScript Next.js frontend `AuditLogEntry` + `AuditLogQueryFilters` + `ActivityStreamGroup` interface parity 결정 wire)
- **CR 12-5 D-GATE-01 inversion** ✅ APPLIED (capability gate AUDIT_LOG_VIEW per-tenant on/off + owner-only RBAC AD-22 결정 wire + manual audit log query owner-only RBAC 결정 wire)
- **A19 cohesion pattern 9 surface EXTENSION PASS** ✅ (audit log viewer surface EXTENSION = F21.1~F21.6 audit log viewer & activity stream territory)
- **A36 SDR 검증 4-step 자동 적용** ✅ (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS)
- **AD-14 stack pin** ✅ APPLIED (no new deps 결정 wire, FastAPI + Supabase + Next.js + sentry-sdk[fastapi] carry-over)
- **AD-22 owner-only RBAC** ✅ APPLIED (manual audit log query owner-only RBAC 결정 wire + Epic 12 2FA 챌린지 보존)
- **NFR4 PII minimization** ✅ APPLIED (audit log query 시 PII 데이터 filter 가능 + masked display 결정 wire, audit log payload encryption at rest Supabase managed 결정 wire)

### Library / Framework Requirements

- **httpx>=0.27.0** (carry-over) — Supabase API call for read replica (GET /v1/projects/{ref}/read-replica)
- **sentry-sdk[fastapi]>=2.10.0** (carry-over from Phase 5 wire) — Sentry breadcrumb audit lag
- **csv** (Python stdlib, no new deps) — CSV writer for audit log export
- **next-intl>=3.0.0** (carry-over from Epic 16 wire) — `useTranslations("audit_log")` + `useTranslations("activity")` for i18n

### File Structure Requirements

- `apps/api/modules/audit/` (NEW directory) — for audit log modules (audit_log_query + audit_log_export + audit_log_routes)
- `apps/web/lib/audit/` (NEW directory) — for audit log client (audit-log-client.ts)
- `apps/web/app/[locale]/(dashboard)/audit-log/` (NEW route, protected by `(dashboard)` route group)
- `apps/web/app/[locale]/(dashboard)/activity/` (NEW route, protected by `(dashboard)` route group)
- `apps/web/__tests__/audit-log/` (NEW test directory)
- `apps/web/__tests__/activity/` (NEW test directory)
- `apps/web/__tests__/i18n/` (NEW test directory for ko-KR.json SSOT parity)
- `tests/api/modules/audit/` (NEW test directory)
- `tests/integration/test_capability_matrix_v1_30_drift.py` (NEW drift detector)

### Testing Standards

- **3중 게이트 FINAL CLEAN** (cj-style 82번째 standard): (1) `pnpm tsc --noEmit` 0 NEW errors / (2) `pnpm vitest run` 102+10 = ~112/112 PASS / (3) `ruff check` scoped Epic 17 wire Python files = All checks passed! / (4) `pytest` 4176+30 = ~4206/4206 PASS / (5) `pytest --collect-only -q` SDR drift gate = MAX claim 4176 → ~4206 actual (no SDR overclaim) / (6) commit_consistency gate PASS (CR 9-6 + A36)
- **Test scope breakdown**: ~30 NEW pytest (15 query + 8 export + 5 cross_region + 5 audit_first + 7 drift = 40 actual) + ~10 NEW vitest (page.test.tsx 10 + audit-log-client.test.ts 10 + activity/page.test.tsx 10 = 30 actual) + 1 NEW drift detector + 1 NEW integration test
- **A19 cohesion pattern 9 surface EXTENSION PASS** — all 9 surfaces touched (kernel + port + db schema + service + handler + envelope + capability + audit + audit log viewer surface NEW)

### Project Structure Notes

- Alignment with unified project structure:
  - `apps/api/modules/audit/` follows `apps/api/modules/auth/sso/` pattern (Epic 15/16 wire 정합)
  - `apps/web/lib/audit/` follows `apps/web/lib/tenant/` pattern (Epic 16 wire 정합)
  - `apps/web/app/[locale]/(dashboard)/audit-log/` follows `apps/web/app/[locale]/(dashboard)/admin/` pattern (Epic 16 T4 follow-up 정합)
  - `apps/web/__tests__/audit-log/` follows `apps/web/__tests__/api/` pattern (Phase 5 wire 정합)
- Detected conflicts or variances: None — Epic 17 territory fully aligned with existing patterns

### References

- master PRD v3.6 §F21 (Audit Log Viewer & Activity Stream territory) — `_bmad-output/planning-artifacts/prd.md` lines 1267-1380
- master PRD v3.6 §F21.1 (audit log query API) — lines 1295-1301
- master PRD v3.6 §F21.2 (audit log viewer UI) — lines 1303-1309
- master PRD v3.6 §F21.3 (activity stream UI) — lines 1311-1317
- master PRD v3.6 §F21.4 (cross-region audit log visibility) — lines 1319-1325
- master PRD v3.6 §F21.5 (CSV export) — lines 1327-1333
- master PRD v3.6 §F21.6 (Capability gate AUDIT_LOG_VIEW) — lines 1335-1341
- master PRD v3.6 §F21.7 (tests + wire scope T1~T8) — lines 1343-1370
- master PRD v3.6 §8.1 M0-(n) (audit log viewer AC) — line 458
- master PRD v3.6 §15 (로드맵 Epic 17 row) — line 1522
- master PRD v3.6 AD-32 (Audit Log Viewer & Activity Stream) — line 1745
- master PRD v3.6 §부록 A A153~A157 — lines 1721-1729
- Epic 17 PRD entry commit `40a9c41` — `git log` reference
- Phase 5 atomic wire `f093f8c` (multi-region backup & DR territory, cross-region audit log visibility carry-over) — `git log` reference
- Phase 5 PRD entry `93d852b` (PRD §F20 verbatim multi-region backup & DR territory) — `git log` reference
- Epic 16 atomic wire `e117e09` (idp_admin_management + audit-first INSERT 4 NEW pattern) — `git log` reference
- Epic 16 T4 follow-up sprint `ff5c3b5` (admin UI 12 files, CR 11-4 D-001~D-005 + P-015 lessons carry) — `git log` reference
- Epic 16 close-out retro `f1ead9a` — `git log` reference
- Epic 15 wire `5f9e37f` (sso_enterprise + audit-first INSERT pattern) — `git log` reference
- Epic 12 wire `a63646c` (2FA 게이트 + TOTP chain) — `git log` reference
- A36 SDR verification 4-step (commit prefix lint + sprint-status structure + vitest file count drift + commit consistency) — `memory/cr-a19-lessons.md` carry-over
- CR 11-4 D-001~D-005 lessons — `memory/cr-11-4-lessons.md` carry-over
- P-015 ko-KR.json SSOT discipline — `memory/cr-11-4-lessons.md` carry-over

## Dev Agent Record

### Agent Model Used

`MiniMax-M3` (cj-style 81번째 epic 연속 정직 회복 bmad-create-story spec entry 진입 시점에 결정)

### Debug Log References

N/A (docs only spec entry)

### Completion Notes List

- [x] Epic 17 PRD entry (cj-style 80번째) DONE
- [x] Epic 17 bmad-create-story spec entry (cj-style 81번째) DONE (this document)
- [ ] Epic 17 bmad-dev-story atomic wire T1~T8 (cj-style 82번째) — pending
- [ ] Epic 17 close-out retro (cj-style 83번째) — pending

### File List

(To be filled by dev agent during T1~T8 implementation)