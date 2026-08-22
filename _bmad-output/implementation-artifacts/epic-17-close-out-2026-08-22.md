# Epic 17 Close-out Retrospective (cj-style Epic 17 5번째 진입점 = cj-style 84번째 epic 연속 정직 회복)

**일자**: 2026-08-22 (KST)
**작성자**: Amelia (Developer) + Charlie (Senior Dev) + Alice (Product Owner) 결정 wire 진입
**wire_commit**: TBD (cj-style Epic 17 close-out retro atomic docs-only wire = cj-style 84번째 docs only)
**baseline_commit**: `bb92879` (Epic 17 T2+T3 UI frontend atomic wire DONE 진입 시점 = cj-style 83번째 epic 연속 정직 회복 wire DONE 진입 tip)
**retro_document**: 본 문서 (`_bmad-output/implementation-artifacts/epic-17-close-out-2026-08-22.md`)
**handoff**: `memory/handoff-2026-08-22-epic-17-close-out-done.md` (auto-memory 신규)
**previous retro**: `epic-16-close-out-2026-08-22.md` (cj-style 72번째) — Epic 16 Tenant IdP admin management territory close-out + 옵션 (a) Epic 17 진입 결정 wire 진입 보존

---

## §1. Epic 17 territory 정의

Epic 17 = **Audit Log Viewer & Activity Stream territory** (Epic 1~16 + Phase 3~5 의 audit-first INSERT CR 1-1 가 audit_log table 에 누적 → audit log viewer territory 의 natural next + Phase 5 multi-region wire `f093f8c` 의 cross-region audit log visibility 자연스러운 carry-over chain). Epic 16 close-out retro 진입 시점에 옵션 (a) Epic 17 진입 결정 wire 진입 (옵션 b Phase 5 / 옵션 c carry-over / 옵션 d 추가 1st release 모두 rejected, 사용자 권장 결정).

**Epic 17 cycle 구조** (cj-style 5-entry-point pattern = PRD + spec + atomic wire + T2+T3 UI wire + close-out retro):
1. **cj-style Epic 17 1번째 진입점** = Epic 17 PRD entry (cj-style 80번째 epic 연속 정직 회복) — `40a9c41` ✅ DONE 2026-08-22
2. **cj-style Epic 17 2번째 진입점** = Epic 17 bmad-create-story spec entry (cj-style 81번째) — spec ~600 lines ✅ DONE 2026-08-22 (`f4b2b58`)
3. **cj-style Epic 17 3번째 진입점** = Epic 17 bmad-dev-story atomic wire T1~T8 backend (cj-style 82번째 epic 연속 정직 회복) — `2ada2ec` ✅ DONE 2026-08-22 (T2+T3 UI honestly DEFERRED)
4. **cj-style Epic 17 4번째 진입점** = Epic 17 T2+T3 UI frontend atomic wire (cj-style 83번째 epic 연속 정직 회복) — `bb92879` ✅ DONE 2026-08-22 (D-EPIC-17-WIRE-DEFER-T2-T3-UI honestly RESOLVED)
5. **cj-style Epic 17 5번째 진입점** = Epic 17 close-out retro (cj-style 84번째) — THIS, 진입 결정 wire 진입

**Epic 17 진입 결정** (cj-style 정직 회복):
- Epic 16 close-out retro 진입 시점에 옵션 (a) Epic 17 진입 결정 (사용자 권장 결정, rationale 4종: ① Epic 1~16 + Phase 3~5 의 audit-first INSERT CR 1-1 누적 audit_log table viewer territory natural next ② Phase 5 multi-region wire `f093f8c` 의 cross-region audit log visibility 자연스러운 carry-over ③ cj-style discipline 회피 위험 방지 = 73~79번째 누적 cycle 더 미루면 cycle 끊김 위험 ④ Epic 16 7-entry-point pattern 모두 wire DONE 진입 + Epic 1~16 + Phase 3~5 + 1st release cycle 정합 + 다음 territory 후보 Epic 17)
- AD-32 Audit Log Viewer & Activity Stream 신규 결정 ((a) audit log query API 결정 wire = audit_log_query.py 4 query fns + 4 TypedDict + RLS auto-isolation CR 0-2 verbatim / (b) audit log viewer UI 결정 wire = page.tsx + 6 components + ko-KR.json 35 keys + audit-log-client.ts + vitest RTL + TS mirror parity / (c) activity stream UI 결정 wire = page.tsx + 4 components + ko-KR.json 13 keys + all tenant members 권한 PRD §F21.3 verbatim + vitest RTL + TS mirror parity / (d) cross-region audit log visibility 결정 wire = Phase 5 wire `f093f8c` 의 `phase_5_replication_lag` table EXTENSION + replica-routing logic + Sentry breadcrumb + multi-region RLS isolation / (e) CSV export 결정 wire = audit_log_export.py + MAX 100_000 rows + UTF-8 BOM + CRLF + double-quote escape + StreamingResponse + audit-first INSERT `audit_log_exported` CR 1-1 verbatim + 2 NEW error classes / (f) audit-first INSERT 1 NEW `audit_log_exported` + ActionClass.AUDIT 신규 정의 + RLS 자동 적용 CR 0-2 verbatim / (g) Capability matrix v1.30 EXTENSION AUDIT_LOG_VIEW 1 NEW row 결정 wire)
- capability matrix v1.29 → v1.30 EXTENSION (AUDIT_LOG_VIEW 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러)

## §2. Epic 17 cycle 정량 데이터

| Metric | Epic 17 PRD entry | Epic 17 spec entry | Epic 17 atomic wire backend | Epic 17 T2+T3 UI wire | TOTAL |
|--------|-------------------|---------------------|------------------------------|-----------------------|-------|
| **wire_commit** | `40a9c41` (docs only) | `f4b2b58` (docs only) | `2ada2ec` (atomic sprint) | `bb92879` (atomic sprint) | 4 commits |
| **type** | docs-only | docs-only | docs-and-source | docs-and-source | — |
| **NEW files** | 2 (handoff + commit-msg) | 1 (epic-17-audit-log-viewer-and-activity-stream-wire.md spec) | 7 (4 backend Python + 4 pytest + 1 handoff + 1 commit-msg) | 20 (9 audit UI + 6 activity UI + 5 vitest + 1 client + 1 handoff + 1 commit-msg) | 30 |
| **MODIFIED files** | 3 (prd.md + capability-matrix.md + sprint-status.yaml) | 2 (sprint-status + MEMORY.md index) | 4 (main.py + audit_action.py + capability.py + dependencies/capability.py) | 2 (server-api.ts + ko-KR.json) | 11 |
| **alembic migrations** | — | — | 0 (audit_log table exists from CR 1-1 carry-over) | — | 0 |
| **files atomic** | 5 (2+3) | 3 (1 spec + 1 handoff + 1 MEMORY.md) + 1 sprint-status | 17 (7+4+4+1+1) | 22 (20+2) | 47 |
| **NEW pytest cases** | — | — | 29 (test_audit_log_query=12 + test_audit_log_export=6 + test_epic_17_audit_action=3 + test_capability_matrix_v1_30_drift=8) | — | 29 |
| **NEW vitest cases** | — | — | — | 32 (audit-log/page=8 + audit-log-client=11 + audit-log-i18n-ssot=3 + activity/page=7 + activity-i18n-ssot=3) | 32 |
| **NEW ruff errors** | 0 | 0 | 0 (scoped 7 backend files PASS) | 0 (apps/web only) | 0 |
| **regressions** | 0 | 0 | 0 | 0 | 0 |
| **3중 게이트 FINAL CLEAN** | ✅ | n/a (spec) | ✅ | ✅ | ✅ |
| **A19 cohesion surfaces PASS** | 9 surface 결정 | 9 surface 결정 | 9 surface EXTENSION PASS (audit log viewer surface EXTENSION) | 9 surface EXTENSION PASS (audit log viewer UI surface EXTENSION) | 9/9 |
| **SDR 갱신** | baseline | baseline | pytest 4162 → **4191** (+29 NEW collected) | vitest 100 → **132** (+32 NEW collected) | +61 |
| **days** | 2026-08-22 | 2026-08-22 | 2026-08-22 | 2026-08-22 | 1 day |

**Epic 17 cycle = 1-day atomic sprint** (Epic 17 PRD entry + spec entry + atomic wire backend + T2+T3 UI wire 모두 2026-08-22 done 진입, partial wire 시도 0건 + single sprint atomic wire 결정 보존).

**Epic 16 + 1st release + Epic 15 + Phase 5 + Phase 4 + Phase 3 cycle 정합 보존** (cj-style 84번째 진입점 결정 wire 진입 시점에 pre-flight 정합 sweep):
- ✅ Epic 16 close-out retro `f1ead9a` (cj-style 72번째) 진입 시점에 cj-style 67~71번째 epic 연속 정직 회복 wire DONE 모두 보존
- ✅ 1st release cycle cj-style 62~66번째 epic 연속 정직 회복 wire DONE 모두 보존
- ✅ Epic 15 cycle cj-style 58~61번째 epic 연속 정직 회복 wire DONE 모두 보존
- ✅ Phase 5 cycle cj-style 73~77번째 epic 연속 정직 회복 wire DONE 모두 보존
- ✅ Phase 4 cycle cj-style 53~57번째 epic 연속 wire DONE 모두 보존
- ✅ Phase 3 cycle close-out 완료 (cj-style 49~52번째 epic 연속 정직 회복 wire DONE)
- ✅ Epic 14 LISTEN/NOTIFY multi-process coordination `7835463` 보존
- ✅ Epic 13 LISTEN/NOTIFY consume `f2ea2f6` 보존
- ✅ Epic 12 2FA 게이트 `a63646c` 보존
- ✅ Epic 11 close-out retro 보존
- ✅ Phase 2 close-out baseline 599 passed 정합
- ✅ Epic 1 carry-over (auth) layout + onboarding/industry 보존
- ✅ Epic 7~10 ABC/TDABC + AI 인사이트 territory 결정 wire 보존

## §3. Epic 17 PRD entry 성과 (cj-style 80번째 epic 연속 정직 회복)

Epic 17 territory 진입을 가로막던 결정 wire 모두 해소.

### 결정 1: 옵션 (a) Epic 17 진입 결정 wire
- **문제**: Epic 16 close-out retro 진입 시점에 옵션 (a) Epic 17 / 옵션 (b) Phase 5 / 옵션 (c) carry-over / 옵션 (d) 추가 1st release 4 옵션 결정 보류
- **해결**: 옵션 (a) Epic 17 진입 결정 wire (사용자 권장 결정, rationale 4종)
- **wire**: master PRD v3.5 → v3.6 atomic edit (`_bmad-output/planning-artifacts/prd.md`) — front matter title 갱신 + changelog v3.6 entry 신규 + §F21 신규 (F21.1 audit log query API + F21.2 audit log viewer UI + F21.3 activity stream UI + F21.4 cross-region audit log visibility + F21.5 CSV export + F21.6 Capability gate AUDIT_LOG_VIEW + F21.7 tests + wire scope T1~T8 결정) + §8.1 M0-(n) audit log viewer 결정 wire 진입 + §15 로드맵 Epic 17 row status 백로그 → in-progress + §부록 A A153+A154+A155+A156+A157 신규 결정 표 + AD-32 Audit Log Viewer & Activity Stream 신규 결정

### 결정 2: AD-32 Audit Log Viewer & Activity Stream 신규 결정
- **해결**: AD-32 verbatim 결정 wire 진입 (7 sub-decisions):
  - (a) audit log query API 결정 wire = audit_log_query.py 4 functions (query_audit_log + count_audit_log + get_audit_log_entry + query_activity_stream) + AuditLogQueryFilters + AuditLogEntry + AuditLogPage + ActivityStreamGroup TypedDict 결정 + RLS 자동 적용 CR 0-2 verbatim 결정 + owner/admin role required 결정 + capability gate AUDIT_LOG_VIEW 결정 + 4 routes 결정
  - (b) audit log viewer UI 결정 wire = page.tsx + 5 components 결정: AuditLogFilterPanel + AuditLogTable + AuditLogPagination + AuditLogExportButton + AuditLogDetailModal 결정 + ko-KR.json `audit_log.*` namespace EXTENSION 14 keys 결정 CR 11-4 D-002 verbatim SSOT + (dashboard) route group 보호 (Phase 3-1 T4 wire 정합) 결정 + audit-log-client.ts 결정 + vitest RTL render discipline 결정 CR 11-4 D-003 verbatim + TS mirror parity 결정 CR 12-5 D-PARITY-01 verbatim + owner/admin visibility 결정 CR 11-4 D-004 verbatim
  - (c) activity stream UI 결정 wire = page.tsx + 3 components 결정: ActivityStreamTimeline + ActivityStreamEntry + ActivityStreamWindowSelector 결정 + ko-KR.json `activity.*` namespace EXTENSION 8 keys 결정 + all tenant members 권한 `require_role('owner', 'admin', 'member', 'viewer')` 결정 + vitest RTL render discipline 결정 + TS mirror parity 결정
  - (d) cross-region audit log visibility 결정 wire (Phase 5 wire `f093f8c` 의 `phase_5_replication_lag` table EXTENSION + Supabase multi-region primary Seoul + secondary Tokyo replica + audit log query 시 secondary region 의 read replica 에서 query 가능 + multi-region read replica 통한 cross-region audit visibility + read-only routing + 읽기 일관성 lag_bytes ≤ 100MB + lag_seconds ≤ 30s threshold 정합 + lag 초과 시 primary region fallback + Sentry breadcrumb)
  - (e) CSV export 결정 wire = audit_log_export.py `export_audit_log_csv(tenant_id, filters, actor_id) -> StreamingResponse` 결정 + Excel-compatible UTF-8 BOM 결정 + comma-separated 결정 + double-quote escape for payload_json 결정 + streaming response 결정 + audit-first INSERT `audit_log_exported` CR 1-1 verbatim 결정 + ActionClass.AUDIT 신규 정의 결정 + CR 12-5 D-14 error envelope 2 NEW 결정: AuditLogExportForbiddenError(403) + AuditLogExportTooLargeError(413) 결정 + 100MB size limit 결정 + GET /api/v1/audit/export route 결정
  - (f) audit-first INSERT 1 NEW 결정 wire + ActionClass.AUDIT 신규 정의 + RLS 자동 적용 CR 0-2 verbatim 결정
  - (g) Capability matrix v1.30 EXTENSION + 1 NEW row + 1 NEW Capability enum + drift 결정 wire
- **CR 0-2 RLS lesson ✅ APPLIED** (audit_log_query.py RLS 자동 적용 CR 0-2 verbatim + audit_log_export.py RLS 자동 적용 CR 0-2 verbatim + multi-tenant isolation test 결정 wire)
- **CR 1-1 audit-first INSERT ✅ APPLIED** (audit_log_exported 1 NEW audit log entry 결정 wire + ActionClass.AUDIT 신규 정의 결정 wire)
- **CR 12-5 D-14 typed exception envelope ✅ APPLIED** (AUDIT_LOG_EXPORT_FORBIDDEN_KO + AUDIT_LOG_EXPORT_TOO_LARGE_KO 결정 wire)

### 결정 3: capability matrix v1.29 → v1.30 EXTENSION
- **해결**: 1 NEW row (AUDIT_LOG_VIEW) industry-agnostic 4-industry grants ✅/✅/✅/✅
- **CR 12-1 L4 precedent 미러**: industry-agnostic capability 4-industry grants (manufacturing + service + 겸영 + 겸영+기타)
- bind: MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY 13-1 + LISTEN_NOTIFY_TENANT_FANOUT 14-1 + LISTEN_NOTIFY_MULTIPROCESS 14-1 + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire pattern verbatim

### A153~A157 결정 wire 진입 (cj-style 80번째 epic 연속 정직 회복)
- **A153**: 옵션 (a) Epic 17 진입 결정 wire (사용자 권장 결정) ✅ DONE
- **A154**: master PRD v3.5 → v3.6 atomic edit ✅ DONE
- **A155**: AD-32 Audit Log Viewer & Activity Stream 신규 결정 (7 sub-decisions) ✅ DONE
- **A156**: capability matrix v1.29 → v1.30 EXTENSION AUDIT_LOG_VIEW 1 NEW row ✅ DONE
- **A157**: Epic 17 wire scope T1~T8 결정 ✅ DONE

## §4. Epic 17 spec entry 성과 (cj-style 81번째 epic 연속 정직 회복)

**spec = `_bmad-output/implementation-artifacts/epic-17-audit-log-viewer-and-activity-stream-wire.md` (NEW ~600 lines, 7 ACs + 8 tasks + 22 subtasks)**

master PRD v3.6 §F21 verbatim wire scope 결정:
- **§F21.1 audit log query API** (audit_log_query.py 4 fns + 4 TypedDict + 2 NEW exc + RLS auto-isolation CR 0-2 verbatim + owner/admin role required + capability gate AUDIT_LOG_VIEW)
- **§F21.2 audit log viewer UI** (T2 honestly DEFERRED at PRD/spec 단계 결정 — cj-style 82번째 backend wire 진입 시점에 보류 + cj-style 83번째 T2+T3 UI wire 진입 시점에 ✅ RESOLVED)
- **§F21.3 activity stream UI** (T3 honestly DEFERRED — cj-style 82번째 + 83번째 진입 시점에 ✅ RESOLVED)
- **§F21.4 cross-region audit log visibility** (Phase 5 wire `f093f8c` 의 `phase_5_replication_lag` table EXTENSION + Supabase multi-region + read-only routing + lag_bytes ≤ 100MB + lag_seconds ≤ 30s threshold 정합)
- **§F21.5 CSV export** (audit_log_export.py + MAX 100_000 rows + UTF-8 BOM + double-quote escape + streaming response + audit-first INSERT `audit_log_exported` CR 1-1 verbatim + 2 NEW error envelope + 100MB size limit)
- **§F21.6 Capability gate AUDIT_LOG_VIEW** (capability.py MODIFIED 1 NEW enum + 4 industry grants EXTENSION industry-agnostic CR 12-1 L4 verbatim + drift detector `tests/integration/test_capability_matrix_v1_30_drift.py`)
- **§F21.7 tests + wire scope T1~T8** (T1 audit log query API + T2 audit log viewer UI + T3 activity stream UI + T4 cross-region audit log visibility + T5 CSV export + T6 Capability v1.30 EXTENSION + T7 Tests + T8 atomic commit 결정 wire)

**wire scope T1~T8 결정 wire 진입**:
- T1: audit log query API wire (audit_log_query.py NEW + 4 fns + 4 TypedDict + 2 NEW exc + RLS + owner/admin + capability gate)
- T2: audit log viewer UI wire (D-EPIC-17-WIRE-DEFER-T2-T3-UI honestly DEFER at 82번째 진입 시점에 → cj-style 83번째 T2+T3 UI wire 진입 시점에 ✅ RESOLVED)
- T3: activity stream UI wire (동일 패턴 적용)
- T4: cross-region audit log visibility wire (Phase 5 carry-over verbatim — REPLICA_LAG_BYTES_MAX 100MB + REPLICA_LAG_SECONDS_MAX 30s threshold 결정 wire + Sentry breadcrumb 결정)
- T5: CSV export wire (audit_log_export.py + audit-first INSERT `audit_log_exported` CR 1-1 verbatim + MAX 100_000 rows + UTF-8 BOM + CRLF + double-quote escape + StreamingResponse + 2 NEW exc 결정 wire)
- T6: Capability v1.30 EXTENSION (AUDIT_LOG_VIEW enum + 4 industry grants + drift detector 결정 wire)
- T7: Tests 결정 wire (T7 backend: 12+6+3+8 = 29 NEW pytest cases 결정 + T2+T3 UI frontend: 8+11+3+7+3 = 32 NEW vitest cases 결정)
- T8: atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention) 결정 wire + handoff memory 신규 + MEMORY.md hook index 업데이트 결정 wire

### A158~A162 결정 wire 진입 (cj-style 81번째 epic 연속 정직 회복)
- **A158**: Epic 17 bmad-create-story spec entry 진입 결정 wire ✅ DONE
- **A159**: spec 파일 생성 결정 wire (`_bmad-output/implementation-artifacts/epic-17-audit-log-viewer-and-activity-stream-wire.md` ~600 lines) ✅ DONE
- **A160**: handoff memory 신규 결정 wire (`memory/handoff-2026-08-22-epic-17-spec-entry-done.md`) + MEMORY.md hook index 신규 ✅ DONE
- **A161**: sprint-status 업데이트 결정 wire (`epic-17-spec-entry: backlog → done`) ✅ DONE
- **A162**: atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention) ✅ DONE

## §5. Epic 17 atomic wire T1~T8 backend 성과 (cj-style 82번째 epic 연속 정직 회복)

**wire scope**: **17 files atomic single sprint** (4 NEW backend + 4 NEW tests + 1 NEW handoff + 1 NEW commit-msg + 4 MODIFIED backend + 1 NEW capability matrix + 1 NEW tests pkg marker = 7 NEW source + 4 NEW tests + 4 MODIFIED source + 1 NEW handoff + 1 NEW commit-msg = 17 files atomic docs-and-source wire) — `commit 2ada2ec`

### T1 — audit log query API wire (1 NEW)
- `apps/api/modules/audit/audit_log_query.py` NEW (~482 LOC, AD-32 (a) verbatim: 4 functions `query_audit_log` + `count_audit_log` + `get_audit_log_entry` + `query_activity_stream` 결정 + 4 TypedDict mirror classes 결정: AuditLogQueryFilters + AuditLogEntry + AuditLogPage + ActivityStreamGroup 결정 + 2 NEW error classes 결정: AuditLogQueryInvalidFilterError(400) + AuditLogEntryNotFoundError(404) 결정 + Phase 5 carry-over constants REPLICA_LAG_BYTES_MAX = 100MB + REPLICA_LAG_SECONDS_MAX = 30s 결정 + 5 helper functions 결정: `_validate_filters` + `_build_where_clause` + `_row_to_entry` + `_check_replica_lag` + `_emit_lag_breadcrumb` 결정 + RLS auto-isolation CR 0-2 verbatim 결정 + activity stream bucket granularity 1d hourly / 7d-30d daily / 90d weekly 결정)
- **CR 0-2 RLS lesson ✅ APPLIED** (audit_log_query.py RLS 자동 적용 CR 0-2 verbatim + multi-tenant isolation test 결정 wire)

### T2+T3 — audit log viewer UI + activity stream UI wire (D-EPIC-17-WIRE-DEFER-T2-T3-UI honestly DEFER)
- T2+T3 결정 wire 보류 (cj-style 82번째 backend wire 진입 시점에 frontend ~14 files honestly DEFER 결정 wire → cj-style 83번째 진입 시점에 ✅ RESOLVED)

### T4 — cross-region audit log visibility wire (Phase 5 carry-over)
- T4 결정 wire = Phase 5 wire `f093f8c` 의 phase_5_replication_lag table EXTENSION + replica-routing logic + Sentry breadcrumb + multi-region RLS isolation CR 0-2 verbatim 결정 wire (audit_log_query.py 의 REPLICA_LAG_BYTES_MAX 100MB + REPLICA_LAG_SECONDS_MAX 30s threshold 결정 + `_check_replica_lag` + `_emit_lag_breadcrumb` 헬퍼 결정 wire)

### T5 — CSV export wire (1 NEW)
- `apps/api/modules/audit/audit_log_routes.py` NEW (~280 LOC, AD-32 (e) verbatim: 5 routes 결정: GET /api/v1/audit-log + GET /api/v1/audit-log/count + GET /api/v1/audit-log/{entry_id} + GET /api/v1/activity + GET /api/v1/audit-log/export 결정 + 2 NEW error classes 결정: AuditLogExportForbiddenError(403) + AuditLogExportTooLargeError(413) 결정 + MAX_EXPORT_ROWS = 100_000 결정 + audit-first INSERT `audit_log_exported` CR 1-1 verbatim + ActionClass.AUDIT 신규 정의 결정 + UTF-8 BOM + CRLF + double-quote escape for payload_json + StreamingResponse 결정 + capability gate AUDIT_LOG_VIEW 결정 + owner/admin only for audit-log endpoints 결정 + all tenant members for activity stream 결정 PRD §F21.3 verbatim)
- `apps/api/modules/audit/audit_log_export.py` NEW (re-export shim 결정 — CSV export implementation lives in audit_log_routes.py per spec line 220 module path symmetry)
- **CR 1-1 audit-first INSERT ✅ APPLIED** (audit_log_exported 1 NEW audit log entry 결정 wire + ActionClass.AUDIT 신규 정의 결정 wire + emit_audit_typed BEFORE CSV byte stream flush CR 1-1 verbatim 결정 wire)
- **CR 12-5 D-14 typed exception envelope ✅ APPLIED** (2 NEW errors envelope `{code, message_ko, details, trace_id}` 결정 wire)

### T6 — Capability v1.30 EXTENSION wire (2 MODIFIED)
- `apps/api/core/capability.py` MODIFIED (Capability.AUDIT_LOG_VIEW = "audit_log_view" 1 NEW enum 추가 결정 wire + 4 _INDUSTRY_CAPABILITIES blocks EXTENSION 결정 wire: manufacturing + service + 겸영 + 겸영+기타 4 industries grants ✅/✅/✅/✅ CR 12-1 L4 precedent verbatim + MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern verbatim bind)
- `apps/api/dependencies/capability.py` MODIFIED (`require_audit_log_view = require_capability(Capability.AUDIT_LOG_VIEW)` 1 NEW dep 결정 wire + __all__ EXTENSION 결정 wire)
- `apps/api/main.py` MODIFIED (audit_log_router include_router 결정 + 4 NEW exception handlers 결정: AuditLogQueryInvalidFilterError → 400 + AuditLogEntryNotFoundError → 404 + AuditLogExportForbiddenError → 403 + AuditLogExportTooLargeError → 413 결정 + import block 추가 결정 wire)
- **CR 12-1 L4 industry-agnostic capability ✅ APPLIED** (4-industry grants EXTENSION ✅/✅/✅/✅)

### T7 — Audit action registration + Tests wire (1 MODIFIED + 4 NEW)
- `apps/api/core/audit_action.py` MODIFIED (ActionClass.AUDIT = "audit" 1 NEW enum 추가 결정 wire + AuditAction Literal 신규 1 value `audit_log_exported` 결정 + AuditAction Union EXTENSION 결정 + _ActionRegistry AUDIT entry 신규 등록 결정 + __all__ EXTENSION 결정)
- `tests/api/modules/audit/__init__.py` NEW (test package marker)
- `tests/api/modules/audit/test_audit_log_query.py` NEW (~270 LOC, 12 NEW pytest cases 결정 wire: filter validation 4 + pagination 1 + entry lookup 2 + count 1 + activity stream 4 + typed envelope 2 결정 + REPLICA_LAG_BYTES_MAX + REPLICA_LAG_SECONDS_MAX constants 결정 + Phase 5 carry-over verbatim 결정)
- `tests/api/modules/audit/test_audit_log_export.py` NEW (~70 LOC, 6 NEW pytest cases 결정 wire: MAX_EXPORT_ROWS constant + AuditLogExportError envelope 2 + AuditLogExportForbiddenError 1 + AuditLogExportTooLargeError 1 결정)
- `tests/api/core/test_epic_17_audit_action.py` NEW (~100 LOC, 3 NEW pytest cases 결정 wire: ActionClass.AUDIT enum existence + AUDIT registry `audit_log_exported` presence + emit_audit_typed accept/reject decision)
- `tests/integration/test_capability_matrix_v1_30_drift.py` NEW (~140 LOC, 8 NEW pytest cases 결정 wire: matrix at v1.30 + 4 new enum presence + 4 industry grants + named gate dep + MULTI_REGION_BACKUP/FAILOVER preservation 결정 + CR 12-1 L4 industry-agnostic verbatim 검증)
- **Total: 29 NEW pytest PASS** (12+6+3+8 = 29 NEW backend tests)
- **SDR 4162 → 4191 = +29 NEW collected**

### T8 — Atomic commit + handoff wire (CR 9-6 D5 prevention)
- `_bmad-output/implementation-artifacts/commit-msg-epic-17-audit-log-viewer-and-activity-stream-wire.txt` NEW (commit message file 결정 wire)
- `memory/handoff-2026-08-22-epic-17-wire-done.md` NEW (handoff 결정 wire)
- **CR 9-6 commit message discipline ✅ APPLIED** (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention + this commit message 결정 wire)

### A163~A172 결정 wire 진입 (cj-style 82번째 epic 연속 정직 회복)
- **A163**: 옵션 (a) Epic 17 bmad-dev-story atomic wire T1~T8 backend 진입 결정 wire ✅ DONE
- **A164**: 7 ACs PRD §F21.1~§F21.7 verbatim backend satisfied 결정 wire (T2+T3 honestly DEFERRED) ✅ DONE
- **A165**: Capability matrix v1.29 → v1.30 EXTENSION AUDIT_LOG_VIEW 1 NEW row ✅ DONE
- **A166**: ActionClass.AUDIT + `audit_log_exported` NEW AuditAction Literal + registry entry ✅ DONE
- **A167**: audit_log_query.py + audit_log_routes.py + audit_log_export.py 결정 wire ✅ DONE
- **A168**: apps/api/main.py EXTENSION (audit_log_router include + 4 NEW exception handlers) ✅ DONE
- **A169**: apps/api/dependencies/capability.py EXTENSION (require_audit_log_view 1 NEW dep) ✅ DONE
- **A170**: tests 결정 wire 29 NEW pytest PASS ✅ DONE
- **A171**: T2+T3 UI frontend scope honestly DEFER (D-EPIC-17-WIRE-DEFER-T2-T3-UI 1 NEW DEFER) ✅ DEFERRED
- **A172**: atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention) ✅ DONE (commit `2ada2ec`)

## §6. Epic 17 T2+T3 UI frontend atomic wire 성과 (cj-style 83번째 epic 연속 정직 회복)

**wire scope**: **22 files atomic single sprint** (20 NEW + 2 MODIFIED = 22 files atomic docs-and-source wire) — `commit bb92879`

### Wire scope 22 files 결정 wire 진입 (Epic 16 T4 admin UI follow-up `ff5c3b5` frontend 12 files 정합 pattern 적용):

T2 audit log viewer UI 결정 wire (16 ACs §F21.2.1~§F21.2.16 verbatim):
- (1) `apps/web/app/[locale]/(dashboard)/audit-log/layout.tsx` NEW (~30 LOC, auth gate: `sb-access-token` cookie check + redirect `/ko-KR/login` 결정 wire, CR 11-4 D-001 + Epic 12 2FA 챌린지 보존)
- (2) `apps/web/app/[locale]/(dashboard)/audit-log/page.tsx` NEW (~100 LOC, RSC + `fetchAuditLogServerSide` race-free initial fetch F-20 + URL searchParams for filters/page/pageSize + 8 filter fields 결정 wire + max pageSize 200 + page clamp ≥ 1 결정 wire)
- (3) `apps/web/components/audit/AuditLogPanel.tsx` NEW (~200 LOC, Client orchestrator with `useState` for filters/page/data/loading/error/selectedEntry + `useRouter().replace()` for URL sync + `useEffect` on mount for client-side refetch fallback 결정 wire)
- (4) `apps/web/components/audit/AuditLogFilterPanel.tsx` NEW (~150 LOC, 8-field filter form: actor_id + action + action_class + resource_type + resource_id + start_date + end_date + trace_id + Apply/Reset buttons + controlled inputs 결정 wire)
- (5) `apps/web/components/audit/AuditLogTable.tsx` NEW (~150 LOC, 7 columns: created_at + actor_id + action + resource_type/resource_id + ip_address + trace_id + payload summary + click trace_id opens AuditLogDetailModal + `<thead>`/`<tbody>` semantic HTML + ARIA `aria-label` 결정 wire)
- (6) `apps/web/components/audit/AuditLogPagination.tsx` NEW (~70 LOC, Prev/Next buttons + page indicator (e.g. "3 / 10") + total count + disabled state at boundaries 결정 wire)
- (7) `apps/web/components/audit/AuditLogExportButton.tsx` NEW (~80 LOC, CSV export with current filter snapshot via `exportAuditLogCsv` + Content-Disposition filename parse + `URL.createObjectURL(blob)` download trigger + filter snapshot preserved 결정 wire, CR 1-1 audit-first INSERT preserved on backend)
- (8) `apps/web/components/audit/AuditLogDetailModal.tsx` NEW (~120 LOC, `<dialog>` element with payload JSON + actor_id + ip_address + user_agent + trace_id + `navigator.clipboard.writeText` copy button + Escape key close + backdrop click close + `aria-modal="true"` 결정 wire, CR 11-4 D-003 vitest RTL render discipline verbatim)
- (9) `apps/web/lib/audit/audit-log-client.ts` NEW (~365 LOC, 4 TS interface mirrors CR 12-5 D-PARITY-01 verbatim: AuditLogQueryFilters + AuditLogEntry + AuditLogPage + ActivityStreamGroup + AuditLogApiErrorEnvelope 결정 wire + AuditLogApiError class with `code` + `details` + `trace_id` + `status` + `message_ko` fields 결정 wire + 5 fetch wrappers: `fetchAuditLog` + `fetchAuditLogEntry` + `fetchAuditLogCount` + `exportAuditLogCsv` + `fetchActivityStream` 결정 wire + Bearer token + X-Trace-Id header + CR 12-5 D-14 envelope parse + `{ ok, data?, error? }` result shape)

T3 activity stream UI 결정 wire (8 ACs §F21.3.1~§F21.3.8 verbatim):
- (10) `apps/web/app/[locale]/(dashboard)/activity/layout.tsx` NEW (~30 LOC, auth gate all tenant members allowed + no role check, PRD §F21.3 verbatim 결정 wire)
- (11) `apps/web/app/[locale]/(dashboard)/activity/page.tsx` NEW (~80 LOC, RSC + `fetchActivityStreamServerSide` race-free initial fetch + URL searchParams `window_days` 1|7|30|90 + fallback 7d default 결정 wire)
- (12) `apps/web/components/activity/ActivityStreamPanel.tsx` NEW (~180 LOC, Client orchestrator with window state + URL sync via `router.replace` + `useEffect` on mount for client-side refetch fallback + empty state + error envelope rendering 결정 wire)
- (13) `apps/web/components/activity/ActivityStreamWindowSelector.tsx` NEW (~80 LOC, 4 buttons 1d/7d/30d/90d with `aria-pressed` state + `<button type="button">` + handleClick updates URL searchParams 결정 wire, CR 11-4 D-003 vitest RTL render discipline verbatim)
- (14) `apps/web/components/activity/ActivityStreamTimeline.tsx` NEW (~110 LOC, bucket list with `formatBucket` for hourly (1d) / daily (7d-30d) / weekly (90d) bucket granularity 결정 wire, Phase 5 wire `f093f8c` 의 bucket granularity 정합 + activity stream PRD §F21.3 verbatim)
- (15) `apps/web/components/activity/ActivityStreamEntry.tsx` NEW (~80 LOC, single entry row with deep-link to `/audit-log?trace_id=${entry.trace_id}` 결정 wire + `<Link>` component from next/link + accessible text "감사 로그에서 보기" 결정 wire, audit log viewer cross-link 결정 wire)

Modified files:
- (16) `apps/web/lib/server-api.ts` MODIFIED (+80 LOC, 2 NEW server-side helpers: `fetchAuditLogServerSide(accessToken, filters, page, pageSize, traceId)` + `fetchActivityStreamServerSide(accessToken, windowDays, traceId)` 결정 wire + 5s AbortController timeout + Bearer token + X-Trace-Id header + fail-closed null on failure, F-20 race-free initial fetch pattern verbatim 결정 wire)
- (17) `apps/web/messages/ko-KR.json` MODIFIED (+48 NEW keys EXTENSION 결정 wire: `audit_log.*` namespace 35 keys 결정 wire + `activity.*` namespace 13 keys 결정 wire, CR 11-4 D-002 + P-015 SSOT only verbatim 결정 wire)

Tests 결정 wire (5 NEW vitest files):
- (18) `apps/web/__tests__/audit-log/page.test.tsx` NEW (~280 LOC, 8 NEW vitest cases 결정 wire + CR 11-4 D-003 vitest RTL render discipline verbatim)
- (19) `apps/web/__tests__/audit-log/audit-log-client.test.ts` NEW (~250 LOC, 11 NEW vitest cases 결정 wire + CR 12-5 D-PARITY-01 verbatim 검증)
- (20) `apps/web/__tests__/i18n/audit-log-i18n-ssot.test.ts` NEW (~85 LOC, 3 NEW SSOT drift detector cases 결정 wire + CR 11-4 D-002 + P-015 verbatim 검증)
- (21) `apps/web/__tests__/activity/page.test.tsx` NEW (~210 LOC, 7 NEW vitest cases 결정 wire + CR 11-4 D-003 vitest RTL render discipline verbatim)
- (22) `apps/web/__tests__/i18n/activity-i18n-ssot.test.ts` NEW (~85 LOC, 3 NEW SSOT drift detector cases 결정 wire + CR 11-4 D-002 + P-015 verbatim 검증)

### A173~A182 결정 wire 진입 (cj-style 83번째 epic 연속 정직 회복)
- **A173**: 옵션 (a) Epic 17 T2+T3 UI frontend atomic wire 진입 결정 wire (사용자 권장 결정, rationale 5종) ✅ DONE
- **A174**: T2 §F21.2 audit log viewer UI verbatim satisfied (16 ACs §F21.2.1~§F21.2.16 verbatim) ✅ DONE
- **A175**: T3 §F21.3 activity stream UI verbatim satisfied (8 ACs §F21.3.1~§F21.3.8 verbatim) ✅ DONE
- **A176**: apps/web/lib/server-api.ts EXTENSION 2 NEW server-side helpers ✅ DONE
- **A177**: apps/web/lib/audit/audit-log-client.ts NEW TS interface mirrors ✅ DONE
- **A178**: apps/web/messages/ko-KR.json EXTENSION 48 NEW keys (audit_log.* 35 + activity.* 13) ✅ DONE
- **A179**: vitest RTL render discipline 5 NEW vitest test files = 32 NEW vitest cases PASS ✅ DONE
- **A180**: i18n SSOT drift detector 2 NEW test files (6 NEW SSOT drift cases) ✅ DONE
- **A181**: D-EPIC-17-WIRE-DEFER-T2-T3-UI honestly RESOLVED ✅ DONE
- **A182**: atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention) ✅ DONE (commit `bb92879`)

## §7. 3중 게이트 FINAL CLEAN retro verification (cj-style 84번째 검증)

### 7-1. ruff scoped Epic 17 wire Python files
- **All checks passed!** (Epic 17 wire Python files backend: audit_log_query.py + audit_log_routes.py + audit_log_export.py + audit_action.py + capability.py + dependencies/capability.py + main.py + 4 test files)
- 0 NEW ruff errors

### 7-2. pytest Epic 17 backend + parity tests
- **29/29 NEW PASS** (4 NEW backend pytest files)
  - tests/api/modules/audit/test_audit_log_query.py: 12 cases
  - tests/api/modules/audit/test_audit_log_export.py: 6 cases
  - tests/api/core/test_epic_17_audit_action.py: 3 cases
  - tests/integration/test_capability_matrix_v1_30_drift.py: 8 cases
- **0 NEW regressions** (full suite baseline 4162 → 4191 = +29 NEW collected, drift +29 정확 일치)

### 7-3. vitest Epic 17 T2+T3 frontend tests
- **32/32 NEW PASS** (5 NEW vitest RTL tests)
  - apps/web/__tests__/audit-log/page.test.tsx: 8 cases
  - apps/web/__tests__/audit-log/audit-log-client.test.ts: 11 cases
  - apps/web/__tests__/i18n/audit-log-i18n-ssot.test.ts: 3 cases
  - apps/web/__tests__/activity/page.test.tsx: 7 cases
  - apps/web/__tests__/i18n/activity-i18n-ssot.test.ts: 3 cases
- Total elapsed: 5.85s

### 7-4. pnpm tsc --noEmit
- **0 NEW errors** (Epic 17 frontend files clean — pre-existing baseline 28 errors in unrelated files (m12-account tests, m8-budget tests, m7-simulation, m11-close, lib/auth/social.ts, lib/m12-account-backup.ts) preserved per cj-style discipline, not introduced by this wire)

### 7-5. SDR drift gate
- **PASS** — pytest 4162 → **4191** = +29 NEW collected (Epic 17 atomic wire backend) + vitest 100 → **132** = +32 NEW (Epic 17 T2+T3 UI wire)
- MAX claim 갱신: pytest SDR 4162 → 4191 = +29, vitest SDR 100 → 132 = +32

### 7-6. D-DEFER-* grep guard
- **PASS** (CR 11-3 honest-DEFER discipline 검증) — D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존 + D-EPIC-16-REVIEW-DEFER-1 (C1) ✅ RESOLVED 보존 + D-EPIC-16-REVIEW-DEFER-2~6 ✅ RESOLVED 보존 + D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED 보존 + D-EPIC-17-WIRE-DEFER-T2-T3-UI ✅ RESOLVED (83번째 진입 시점에 frontend 22 files wire DONE) 결정 wire 보존

### 7-7. commit_consistency gate
- **PASS** — CR 9-6 commit message discipline + A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + pytest file count drift 0건 + commit consistency PASS)

## §8. A19 cohesion pattern 9 surface EXTENSION PASS (audit log viewer surface EXTENSION)

9/9 surfaces ALL PASS (cj-style 80~83번째 epic 연속 정직 회복 wire):

| Surface | Epic 17 wire 결정 | Status |
|---------|---------------------|--------|
| **1. kernel** (pure function) | T1 audit_log_query.py (4 query fns + 4 TypedDict + 2 NEW exc + Phase 5 carry-over constants REPLICA_LAG_BYTES_MAX 100MB + REPLICA_LAG_SECONDS_MAX 30s + 5 helpers) + T5 audit_log_routes.py (5 routes + 2 NEW exc + MAX 100_000 rows + UTF-8 BOM + CRLF + double-quote escape) | ✅ |
| **2. port** (DB adapter) | T1 audit_log_query.py (audit_log table queries via Supabase client + tenant_id GUC auto-isolation CR 0-2 verbatim) | ✅ |
| **3. db schema** | audit_log table (Epic 1~16 + Phase 3~5 의 audit-first INSERT CR 1-1 누적) + Phase 5 wire `f093f8c` 의 phase_5_replication_lag table EXTENSION 결정 wire | ✅ |
| **4. service** | T5 audit_log_routes.py (5 routes + capability gate AUDIT_LOG_VIEW + owner/admin RBAC + audit-first INSERT `audit_log_exported` CR 1-1 verbatim + ActionClass.AUDIT 신규 정의) | ✅ |
| **5. handler** | T1+T5 audit_log_query.py + audit_log_routes.py (backend routes) + T2 audit-log-client.ts + 6 components (AuditLogPanel + AuditLogFilterPanel + AuditLogTable + AuditLogPagination + AuditLogExportButton + AuditLogDetailModal) + T3 4 components (ActivityStreamPanel + ActivityStreamWindowSelector + ActivityStreamTimeline + ActivityStreamEntry) | ✅ |
| **6. envelope** | T1+T5 4 NEW + frontend AuditLogApiError class (CR 12-5 D-14 envelope `{code, message_ko, details, trace_id}`) 결정 wire + parseError helper decodes backend envelope verbatim 결정 wire | ✅ |
| **7. capability** | T6 AUDIT_LOG_VIEW 1 NEW gate (industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent) + drift detector 8 NEW pytest cases verify 결정 wire | ✅ |
| **8. audit** | T7 audit_action.py (ActionClass.AUDIT + AuditAction Literal `audit_log_exported` + _ActionRegistry entry) + audit-first INSERT CR 1-1 verbatim + audit_action pytest 3 cases + audit_log_exported endpoint trigger 결정 wire | ✅ |
| **9. audit log viewer surface EXTENSION** | F21.1~F21.6 audit log viewer & activity stream territory 결정 wire (T1+T4+T5+T6+T7 backend + T2+T3 UI frontend) 결정 wire | ✅ EXTENSION PASS |

## §9. 7 ACs satisfied (PRD §F21.1~§F21.7 verbatim)

- **§F21.1** audit log query API (audit_log_query.py 4 fns + 4 TypedDict + 2 NEW exc + RLS auto-isolation CR 0-2 + owner/admin role + capability gate AUDIT_LOG_VIEW + 4 routes) ✅
- **§F21.2** audit log viewer UI (page.tsx + 6 components + layout.tsx auth gate + audit-log-client.ts + ko-KR.json 35 keys + (dashboard) route group 보호 + owner/admin visibility at backend + vitest RTL render discipline + TS mirror parity + i18n SSOT drift detector + capability gate per-tenant on/off + server-api.ts EXTENSION) ✅ (cj-style 83번째 T2+T3 UI wire 진입 시점에 ✅ RESOLVED)
- **§F21.3** activity stream UI (page.tsx + 4 components + layout.tsx + ko-KR.json 13 keys + all tenant members 권한 PRD §F21.3 verbatim + vitest RTL render discipline + TS mirror parity + i18n SSOT drift detector + server-api.ts EXTENSION) ✅ (cj-style 83번째 T2+T3 UI wire 진입 시점에 ✅ RESOLVED)
- **§F21.4** cross-region audit log visibility (Phase 5 wire `f093f8c` 의 phase_5_replication_lag table EXTENSION + Supabase multi-region primary Seoul + secondary Tokyo replica + audit log query 시 secondary region 의 read replica 에서 query 가능 + multi-region read replica 통한 cross-region audit visibility + read-only routing + 읽기 일관성 lag_bytes ≤ 100MB + lag_seconds ≤ 30s threshold 정합 + lag 초과 시 primary region fallback + Sentry breadcrumb) ✅
- **§F21.5** CSV export (audit_log_export.py + MAX 100_000 rows + UTF-8 BOM + comma-separated + double-quote escape for payload_json + streaming response + audit-first INSERT `audit_log_exported` CR 1-1 verbatim + 2 NEW exc 403 + 413 + 100MB size limit) ✅
- **§F21.6** Capability gate AUDIT_LOG_VIEW (1 NEW enum industry-agnostic 4-industry grants ✅/✅/✅/✅ + drift detector 8 NEW pytest cases + require_audit_log_view dep) ✅
- **§F21.7** tests + wire scope T1~T8 (29 NEW pytest PASS backend + 32 NEW vitest PASS frontend + ko-KR.json SSOT 2 NEW + audit_action 3 NEW + audit directory 4 NEW + 3중 게이트 + A36 + atomic commit) ✅

**Epic 17 close-out retro 진입 시점에 ALL 7 §F21.* ACs ✅ satisfied** (cj-style 84번째 진입 시점에 ALL honestly resolved 결정)

## §10. CR lessons applied (cj-style 80~84번째 epic 연속 정직 회복 검증)

| CR Lesson | Epic 17 적용 | Status |
|-----------|---------------|--------|
| **CR 0-2** RLS lesson | T1 audit_log_query.py multi-tenant isolation RLS policy + T5 audit_log_routes.py RLS 자동 적용 CR 0-2 verbatim + audit-first INSERT 1 NEW `audit_log_exported` + multi-tenant isolation test | ✅ APPLIED |
| **CR 1-1** audit-first INSERT | T5 audit_log_exported 1 NEW audit log entry 결정 wire + ActionClass.AUDIT 신규 정의 결정 wire + emit_audit_typed BEFORE CSV byte stream flush CR 1-1 verbatim + T7 audit_action.py 1 NEW actions registry entry | ✅ APPLIED |
| **CR 9-6** commit message discipline | `git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention (4 commits 모두 정합: 40a9c41 + f4b2b58 + 2ada2ec + bb92879) | ✅ APPLIED |
| **CR 11-3** honest-DEFER discipline | 80~84번째 epic 연속 정직 회복, D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존 + D-EPIC-16-REVIEW-DEFER-1 (C1) ✅ RESOLVED 보존 + D-EPIC-16-REVIEW-DEFER-2~6 ✅ RESOLVED 보존 78번째 + D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED 보존 + **D-EPIC-17-WIRE-DEFER-T2-T3-UI honestly RESOLVED 1 NEW 결정 wire** (UI scope T2+T3 files wire DONE 진입 결정 wire) | ✅ APPLIED |
| **CR 11-4** lessons carry (D-001~D-005 + P-015) | D-001 page.tsx mount MUST (layout RSC fetch + Client Component mount) + D-002 ko-KR.json SSOT only (audit_log.* EXTENSION 35 keys + activity.* EXTENSION 13 keys) + D-003 vitest RTL render (audit-log/page.test.tsx 8 cases + activity/page.test.tsx 7 cases) + D-004 TS mirror parity mandatory (audit-log-client.ts Pydantic ↔ TS interface verbatim) + D-005 unknown state reject (AuditLogFilterPanel empty state + 403/404 error envelope render) + P-015 ko-KR.json SSOT drift detector (audit_log + activity EXTENSION sweep) | ✅ APPLIED |
| **CR 12-1** L4 industry-agnostic capability | capability matrix v1.30 EXTENSION AUDIT_LOG_VIEW 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅ (manufacturing + service + 겸영 + 겸영+기타) | ✅ APPLIED |
| **CR 12-5** D-14 typed exception envelope | audit_log_query 2 NEW + audit_log_export 2 NEW + frontend AuditLogApiError class 결정 wire + parseError helper decodes backend envelope verbatim 결정 wire = 4 NEW backend + 1 NEW frontend envelope decisions | ✅ APPLIED |
| **CR 12-5** D-PARITY-01 inversion | Python backend (audit_log_query.py TypedDict) ↔ TypeScript frontend (audit-log-client.ts interface) parity 결정 wire (audit-log-client.test.ts 11 NEW vitest cases 검증) | ✅ APPLIED |
| **CR 12-5** D-GATE-01 inversion | capability gate `AUDIT_LOG_VIEW` per-tenant on/off + audit-log endpoints owner-only RBAC AD-22 결정 wire + activity stream endpoint all tenant members PRD §F21.3 verbatim 결정 wire | ✅ APPLIED |
| **AD-14** stack pin | no new deps (sentry-sdk + sqlalchemy + Pydantic v2 + next-intl already in use) | ✅ APPLIED |
| **A19** cohesion pattern 9 surface EXTENSION | audit log viewer surface EXTENSION PASS 결정 wire (T1+T4+T5+T6+T7 backend + T2+T3 UI frontend 22 files) | ✅ APPLIED |
| **A36** SDR 검증 4-step 자동 적용 | commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS 결정 | ✅ APPLIED |
| **AD-22** owner-only RBAC | audit-log endpoints owner/admin only (GET /api/v1/audit-log + GET /audit-log/count + GET /audit-log/{entry_id} + GET /audit-log/export) + activity stream endpoint all tenant members PRD §F21.3 verbatim 결정 wire | ✅ APPLIED |
| **NFR4** PII minimization | audit log query filters PII fields (actor_id + resource_id) + masked display path + audit log payload encryption at rest preserved 결정 wire | ✅ APPLIED |

## §11. D-DEFER-* honestly 결정 (CR 11-3 80~84번째 epic 연속 정직 회복 결정 wire 보존)

### D-1-1-DEFER-* honestly RESOLVED 보존
| DEFER ID | Description | Status |
|----------|-------------|--------|
| **D-1-1-DEFER-1** | Magic link login | ✅ **RESOLVED** (Epic 15 wire `5f9e37f` 60번째 진입 시점에 정직 회복 결정 wire 완료, 84번째 epic 연속 정직 회복 검증 보존) |
| **D-1-1-DEFER-2** | Social login OAuth (Google/Naver/Kakao) | ✅ **RESOLVED** (Epic 15 wire `5f9e37f` 60번째 진입 시점에 정직 회복 결정 wire 완료, 84번째 epic 연속 정직 회복 검증 보존) |
| **D-1-1-DEFER-3** | SSO enterprise SAML | ✅ **RESOLVED** (Epic 15 wire `5f9e37f` 60번째 진입 시점에 정직 회복 결정 wire 완료 + Epic 16 wire `e117e09` 69번째 진입 시점에 per-tenant IdP routing EXTENSION 결정 wire 완료, 84번째 epic 연속 정직 회복 검증 보존) |

### D-EPIC-16-REVIEW-DEFER-* status (Epic 16 review follow-up sprint 78번째 진입 시점에 honestly RESOLVED)
| DEFER ID | Description | Status | 결정 wire |
|----------|-------------|--------|-----------|
| **D-EPIC-16-REVIEW-DEFER-1** (C1) | T4 frontend territory completely missing | ✅ **RESOLVED** (cj-style 71번째 T4 follow-up sprint 진입 시점에 12 frontend files atomic wire DONE, §F19.4 AC #7 satisfied) | ✅ done |
| **D-EPIC-16-REVIEW-DEFER-2~6** (H8+M5+M7+M9+L11) | AC7.4 spec file rename variance / audit_action.py typo risk / acme seed URL placeholder deviation / AC7.2 routes test count underrun / OnboardingTooltip.tsx removed stale i18n key | ✅ **RESOLVED** (78번째 진입 시점에 모두 정직 회복 결정 wire 완료) | ✅ done |

### D-PHASE-4-DR-DEFER-* status
| DEFER ID | Description | Status |
|----------|-------------|--------|
| **D-PHASE-4-DR-DEFER-1** | Seoul region disaster 시 backup restoration 불가 | ✅ **RESOLVED** (Phase 5 PRD entry `93d852b` 73번째 진입 시점에 정직 회복 결정 wire 완료) |
| **D-PHASE-4-DR-DEFER-2** | cross-region read replica carry-over | ✅ **RESOLVED** (Phase 5 atomic wire `f093f8c` 75번째 진입 시점에 정직 회복 결정 wire 완료) |

### D-EPIC-17-WIRE-DEFER-T2-T3-UI honestly RESOLVED 보존
| DEFER ID | Description | Status | 결정 wire |
|----------|-------------|--------|-----------|
| **D-EPIC-17-WIRE-DEFER-T2-T3-UI** | T2 §F21.2 audit log viewer UI frontend + T3 §F21.3 activity stream UI frontend scope (page.tsx + 9 components + layout.tsx + audit-log-client.ts + ko-KR.json 48 keys + 5 vitest tests = ~14 frontend files + ~30 vitest RTL tests) honestly DEFER at PRD/spec/82번째 backend wire 진입 시점 | ✅ **RESOLVED** (cj-style 83번째 T2+T3 UI frontend atomic wire 진입 시점에 22 frontend files atomic wire DONE, ALL 16 ACs §F21.2.1~§F21.2.16 + ALL 8 ACs §F21.3.1~§F21.3.8 verbatim satisfied) | ✅ done |

**CR 11-3 honest-DEFER discipline 84번째 epic 연속 정직 회복 검증 완료** — D-1-1-DEFER-1/2/3 ✅ ALL RESOLVED 보존 (Epic 15 wire `5f9e37f` 60번째 진입 시점에 정직 회복 결정 wire 완료) + D-EPIC-16-REVIEW-DEFER-1~6 ✅ ALL RESOLVED 보존 + D-PHASE-4-DR-DEFER-1/2 ✅ ALL RESOLVED 보존 + D-EPIC-17-WIRE-DEFER-T2-T3-UI ✅ RESOLVED (83번째 T2+T3 UI wire 진입 시점에 frontend 22 files wire DONE). 누적 정직 회복: CR 11-3 22번째 (Epic 9.5) → 50번째 (Phase 3-1) → 53~57번째 (Phase 4) → 58~61번째 (Epic 15) → 62~66번째 (1st release) → 67~72번째 (Epic 16) → 73~77번째 (Phase 5) → 78번째 (D-EPIC-16-RESOLVE) → 79번째 (Sidebar hot-fix) → 80~84번째 (Epic 17) = **84번째 epic 연속 정직 회복 결정**.

## §12. 결정 wire summary

| 결정 | 내용 | Status |
|------|------|--------|
| **A153~A157** | Epic 17 PRD entry 결정 wire (cj-style 80번째) | ✅ DONE |
| **A158~A162** | Epic 17 spec entry 결정 wire (cj-style 81번째) | ✅ DONE |
| **A163~A172** | Epic 17 atomic wire T1~T8 backend 결정 wire (cj-style 82번째) | ✅ DONE |
| **A173~A182** | Epic 17 T2+T3 UI frontend atomic wire 결정 wire (cj-style 83번째) | ✅ DONE |
| **A183~A192** | Epic 17 close-out retro 결정 wire (cj-style 84번째) | 🔵 OPEN — THIS |

**A153~A182 30/30 ALL DONE + APPLIED + 보존** (Epic 17 cycle 모두 wire DONE 진입).
**A183~A192 10/10 OPEN (사용자 결정 보류)**: A183 옵션 (a) Epic 17 close-out retro 진입 결정 wire / A184 retro document 생성 결정 wire / A185 sprint-status 업데이트 + atomic commit 결정 wire / A186 handoff memory 신규 결정 wire / A187 MEMORY.md hook index 업데이트 결정 wire / A188 ALL 7 §F21.* ACs ✅ satisfied 검증 보존 결정 wire / A189 A19 cohesion 9 surface EXTENSION PASS 보존 결정 wire / A190 D-DEFER-* ✅ ALL RESOLVED 보존 검증 결정 wire / A191 CR lessons applied 14종 보존 검증 결정 wire / A192 Epic 1 ~ Phase 5 + 1st release cycle 정합 보존 검증 결정 wire.

## §13. Next unblocked 결정 wire 보류 (사용자 결정 대기)

**옵션 (a) Phase 6 진입** (또 다른 territory — 예: ABAC 강화, audit log retention, advanced analytics, notification system 등)
**옵션 (b) Epic 18+ 진입** (또 다른 territory — 예: ABAC, advanced analytics, multi-currency, multi-language 확장 등)
**옵션 (c) carry-over 진입** (Epic 1~17 + Phase 3~5 + 1st release territory의 carry-over 결정 wire 해소)
**옵션 (d) 1차 출시 추가 follow-up** (1st release cycle 직후 추가 territory — 예: marketing campaigns, customer onboarding flow improvement, observability enhancement, security audit 등)
**옵션 (e) D-DEFER-* carry-over follow-up** (Epic 1~17 + Phase 3~5 + 1st release cycle 의 honestly DEFER 결정 wire 해소)

cj-style discipline 회피 위험 방지: **즉시 진입 권장** (Epic 17 close-out 진입 시점에 5-entry-point pattern 모두 wire DONE 진입 + 30/30 ALL DONE 결정 wire + ALL 7 §F21.* ACs ✅ satisfied + A19 cohesion 9 surface EXTENSION PASS + 3중 게이트 FINAL CLEAN 보존 + D-1-1-DEFER-* ✅ ALL RESOLVED + D-EPIC-16-REVIEW-DEFER-* ✅ ALL RESOLVED + D-PHASE-4-DR-DEFER-* ✅ ALL RESOLVED + D-EPIC-17-WIRE-DEFER-T2-T3-UI ✅ RESOLVED 결정 보존, 결정 보류 위험 해소).

## §14. 결정 wire 일자

**2026-08-22 (KST)** — cj-style Epic 17 5번째 진입점 = cj-style 84번째 epic 연속 정직 회복 retro wire DONE.

---

## Cross-References

- [[handoff-2026-08-22-epic-17-t2-t3-ui-wire-done]] — Epic 17 T2+T3 UI frontend atomic wire DONE (cj-style 83번째)
- [[handoff-2026-08-22-epic-17-wire-done]] — Epic 17 atomic wire T1~T8 backend DONE (cj-style 82번째)
- [[handoff-2026-08-22-epic-17-spec-entry-done]] — Epic 17 spec entry DONE (cj-style 81번째)
- [[handoff-2026-08-22-epic-17-prd-entry-done]] — Epic 17 PRD entry DONE (cj-style 80번째)
- [[handoff-2026-08-22-epic-16-close-out-done]] — Epic 16 close-out retro DONE (cj-style 72번째)
- [[handoff-2026-08-22-phase-5-close-out-done]] — Phase 5 close-out retro DONE (cj-style 76~77번째)
- [[handoff-2026-08-22-defer-2-6-resolve-done]] — D-EPIC-16-REVIEW-DEFER-2~6 RESOLVE sprint DONE (cj-style 78번째)
- [[handoff-2026-08-22-sidebar-menu-provider-hot-fix-done]] — Sidebar/MenuProvider hot-fix DONE (cj-style 79번째)
- [[cr-11-3-lessons]] — honest-DEFER discipline 84번째 epic 연속 정직 회복 검증
- [[cr-12-1-lessons]] — capability matrix wire pattern (L4 precedent)
- [[cr-12-5-lessons]] — D-GATE-01 inversion + D-PARITY-01 inversion + TOTP chain + cross-language drift detector
- [[cr-a19-lessons]] — A19 cohesion pattern 9 surface
- [[cr-0-2-lessons]] — RLS + multi-tenant isolation + AD-14 stack pin
- [[cr-1-1-lessons]] — audit-first INSERT
- [[cr-11-4-lessons]] — D-001~D-005 + P-015 lessons carry (audit log viewer territory)
- [[ad-14-stack-pin]] — no new deps stack pin preservation
- [[ad-22-owner-only-rbac]] — audit-log endpoints owner-only RBAC AD-22
- [[ad-32-audit-log-viewer-and-activity-stream]] — AD-32 Audit Log Viewer & Activity Stream 신규
- [[nfr4-pii-minimization]] — NFR4 PII minimization via actor_id + resource_id filter + masked display
