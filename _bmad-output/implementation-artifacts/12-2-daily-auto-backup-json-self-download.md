---
title: 'Epic 12 Story 2 — Daily Auto-Backup + JSON Self-Download (Postgres JSONB + Owner Self-Download Atomic Wire)'
status: ready-for-dev
priority: HIGH
epic: 12
story_num: 2
story_key: 12-2-daily-auto-backup-json-self-download
baseline_commit: 42b45fa
created: 2026-08-12
updated: 2026-08-12
---

> **2026-08-12 — bmad-create-story spec 진입 done** (12-5 partial → 12-2 ready-for-dev). 12-1 will close as done after 12-5 T6 (Playwright) wire; 12-5 T6 honestly DEFER pending follow-up sprint.
>
> **Atomic wire scope (결정)**: 일 1회 cron + 6-table JSON dump + 30-day retention sweep + owner self-download + RLS-preserving restoration schema + 3중 게이트. partial wire 금지 per CR 11-3.
>
> **baseline_commit = `42b45fa`** (Story 12.5 T8 partial close-out tip — current HEAD).
>
> **Three user decisions locked** (2026-08-12):
> 1. **Storage target**: Postgres 테이블 `tenant_backups` (JSONB payload) — 의존성 0 (no Supabase Storage SDK bump) per 12-5 QR manual-entry precedent. JSONB는 AD-9 Seoul 거주성 만족 (Supabase Postgres = Seoul). 마이그레이션 `0024_tenant_backups.py`.
> 2. **Self-download role gate**: `require_role("owner")` (AD-10 owner-only) — backup은 운영자 기능이며 viewer/consultant_proxy/member에게는 불필요. 12-1 self-enrollment (`require_any_role("owner","member")`)와 대조.
> 3. **JSON schema versioning**: `schema_version: "1.0"` top-level envelope + 6 tables (`tenant_settings`, `products`, `bom_lines`, `monthly_input_periods`, `monthly_input_rows`, `fiscal_period_snapshots`, `audit_logs`) — epics.md 6개 표현이 실 DB 테이블 7개로 매핑 (bom→bom_lines, monthly_inputs→periods+rows). 정확 매핑은 spec AC #1에 명시.
>
> **cj-style 3-story 분할 6번째 epic 연속 검증** (Epic 4·5·6·11·12) + **CR 11-3 honest-DEFER discipline 6번째 연속** (atomic wire만, partial wire 0).
>
> **CR 11-4 lessons carry-over**: D-001 (page.tsx mount MUST actually mount) + D-002 (단일 `apps/web/messages/ko-KR.json` only) + D-005 (TS mirror unknown state fall-through → reject).
>
> **CR 12-1 lessons continue applied**: L2 AES-256-GCM lazy wrapper (메타 row payload encryption 검토) + L4 industry-agnostic security baseline (BACKUP_EXPORT capability 패턴).
>
> **CR 12-5 lessons carry-over**: D-13 structural cross-language drift detector + D-14 모든 typed exception main.py envelope handler 등록 + D-15 JSONB in-place mutation (MutableList.as_mutable).
>
> **Honestly DEFER (per CR 11-3, partial wire 아님)**:
> - **Quarterly 1-year archive** (NFR4 2절) — `backup_retention_archived` action은 spec에서 placeholder, wire 0건. sprint-scale 별도 Story.
> - **Manual restore endpoint** — 12-2는 write + download만. RLS-bypass-free restoration은 schema 호환성 + 향후 별도 Story (12-2.5 또는 13-N).
> - **Gzip compression** — 스키마에 영향 없으므로 미래 Story.
> - **Cross-region replication** — AD-9에 의해 이미 disabled.
> - **Playwright E2E** (12-5 T6 패턴 반복) — sprint-scale.

# Story 12.2 — Daily Auto-Backup + JSON Self-Download

## Epic 12 context

Epic 12 (Account & Security Operations) cj-style 3-story 분할 진행:

- **12-1** = 2FA Mandatory Gate to M2 Entry (TOTP + AD-10 4-role + capability v1.13) ← **in-progress** (T1+T2+T5+T6+T7+T9 DONE; T3+T4+T8+T10 honestly DEFER → 12-4 sprint-up DONE + 12-5 sprint-up 진행 중)
- **12-2** = Daily Auto-Backup + JSON Self-Download (PRD §F12.2 + NFR4 backup + AD-9 Seoul) ← **이 스토리** (backlog → ready-for-dev)
- **12-3** = Account Deletion with Retention Consent (PRD §F12.3 + NFR5·6 retention + AD-3 RLS) ← **backlog** (12-2 done 후 진입)

**Epic 12 모듈 authority**: `apps/api/modules/m12_account/` (9 routes + 1 M2 entry gate wire DONE in 12-4). 12-2는 동일한 라우터에 3 routes 추가.

**Epic 12 capability matrix v1.13 wire**: `Capability.TWO_FACTOR_AUTH` 신규 (industry-agnostic). 12-2는 `Capability.BACKUP_EXPORT` 신규 (industry-agnostic, 12-1 패턴 미러) → v1.14.

**Epic 12 NFR coverage**: NFR4 (백업 30일 + 분기 1년) + NFR5 (TLS) + NFR6 (AES-256 at rest) + NFR7 (2FA 강제). 12-2 backup payload 자체는 NFR6 KMS 관리 아래 Supabase Seoul Postgres에 저장 → at-rest encryption inherit (Supabase 기본 + RLS + FORCE RLS).

## Why this story (atomic wire 결정 근거)

**PRD §F12.2 verbatim**: "시스템은 일 1회 자동 백업 + 셀프 다운로드(JSON) 기능을 제공한다." NFR4: "RPO 24h / RTO 4h / 백업 보관 30일(자동), 1년(분기) / 감사로그 5년 append-only."

**epics.md AC verbatim** (lines 1198-1209):
> **Given** 일 1회 자동 백업 cron
> **When** 매일 KST 02:00 실행
> **Then** `(tenant_settings, products, bom, monthly_inputs, fiscal_period_snapshots, audit_logs)`이 JSON으로 Supabase Storage Seoul에 저장
> **And** 보관 30일 자동 + 분기마다 1년 보존 (NFR4)
> **And** 운영자 UI에서 "최근 7일 백업 다운로드" 버튼으로 JSON 즉시 다운로드
> **And** 다운로드 JSON은 동일 schema로 RLS bypass 없이 복원 가능

**3 second-order decisions** (locked 2026-08-12):

1. **Storage = Postgres JSONB (decided: not Supabase Storage)**: AD-9는 Seoul 거주성만 요구 (Storage or Postgres both qualify). 12-5 QR manual-entry decision pattern (의존성 0 + STACK_PIN BUMP 0 + CODEOWNER 승인 불요) 적용. Supabase Storage SDK 2.10.0은 pinned이나 bucket API는 미사용 (코드 0건). Postgres JSONB는 Alembic 0024 + RLS 0014 + AD-2 INSERT-only로 자연 통합. **`tenant_backups` 테이블 = atomic source of truth**.

2. **Self-download role gate = owner-only**: epics.md에 "운영자 UI" 명시 → 운영자 = owner. AD-10 4-role gate 활용 (`require_role("owner")`). viewer/consultant_proxy/member 모두 DENIED. 12-1 self-enrollment이 `require_any_role("owner","member")`였던 것과 대조 (백업은 M2 진입 권한자가 수행하는 일이 아님).

3. **Quarterly 1-year archive honestly DEFER**: epics.md AC에는 포함이나 실 구현은 sprint-scale (별도 cron + 논리). 12-2 atomic wire은 30-day rolling sweep까지. `backup_retention_archived`는 ActionClass registry placeholder, wire 0건.

**+ 12-1 close-out path**: 12-1은 in-progress → 12-5 T6 wire + 12-2 done 후 close.

## User Story

As a **사장님 (owner)**,
I want **매일 새벽 자동 백업이 서울 리전에 쌓이고 UI에서 최근 7일 JSON을 즉시 다운로드**,
so that **NFR4 RPO 24h / RTO 4h (1인 운영자 수동 복구) + AC #5 (RLS bypass 없이 복원) 만족**.

(PRD §F12.2 + epics.md Story 12.2 verbatim + NFR4 backup + AD-9 Seoul + 12-5 carry-over 패턴)

## Acceptance Criteria

### AC #1 — Daily cron + KST 02:00 + 6-table JSON dump (epics.md Given/When/Then #1)

- **Given** 일 1회 자동 백업 cron
- **When** 매일 KST 02:00 (UTC 17:00) 실행
- **Then** Railway cron invokes `apps.api.jobs.backup_daily:run` (precedent: `apps/api/jobs/document_retention.py:54`)
- **And** `tenant_backups` 행 1개 INSERT (action=`backup_created`) — payload는 다음 7 테이블의 모든 tenant 행 dump (각각):
  - `tenant_settings` (1 row / tenant)
  - `products` (N rows)
  - `bom_lines` (N rows)
  - `monthly_input_periods` (N rows)
  - `monthly_input_rows` (N rows)
  - `fiscal_period_snapshots` (N rows)
  - `audit_logs` (last 1y, 30-day 슬라이딩 윈도우)
- **And** envelope top-level: `{schema_version: "1.0", backup_id: UUID, tenant_id: UUID, created_at: ISO-8601 UTC, backup_date: YYYY-MM-DD, tables: {...}}`
- **And** `payload_sha256` CHAR(64) NOT NULL — `hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()` 결정론적 digest
- **And** `row_count_total` INTEGER NOT NULL (sum of 7 table counts)
- **And** `audit_logs`는 last 365일만 (NFR4 retention + 5y audit 일관성 — supabase dump가 너무 커지지 않도록 슬라이딩)
- **And** `retention_class` VARCHAR(16) NOT NULL DEFAULT `'daily'` (분기 1년 class는 honestly DEFER)
- **And** AD-2 invariant: INSERT-only — `BEFORE UPDATE OR DELETE` trigger raises `append-only violation` (audit_logs 0001 패턴 동일)

### AC #2 — Storage는 Supabase Seoul Postgres JSONB (AD-9 + 의존성 0)

- **Given** epics.md AC verbatim "Supabase Storage Seoul"
- **When** 12-2 wire
- **Then** **Postgres 테이블 `tenant_backups` (JSONB payload)** — Storage SDK 의존성 0 (12-5 QR manual-entry decision 패턴)
- **And** `apps/api/jobs/backup_daily.py::run` → in-memory 직렬화 → `payload = json.dumps(...)` → `payload = sa.func.jsonb(payload)` INSERT
- **And** AD-9 Seoul 거주성: Supabase Postgres Seoul (`ap-northeast-2`) 상주 (AD-9 본문에 "PostgreSQL 17 + RLS"가 Supabase Seoul 노드 — `ARCHITECTURE-SPINE.md:309`). Storage/bucket Migration 불요.
- **And** `STACK_PIN.yaml` 변경 0건 (의존성 0 lock)
- **And** `apps/api/settings.py` env var 추가 0건 (Supabase service_role_key는 이미 pinned)

### AC #3 — 30-day retention sweep (NFR4 1절, 2절 honestly DEFER)

- **Given** 보관 30일 자동 + 분기마다 1년 보존 (NFR4)
- **When** 별도 cron `apps.api.jobs.backup_retention:run` KST 03:00 (UTC 18:00) 실행
- **Then** 30일 이전 `retention_class='daily'` 행 soft-delete (`purged_at = now()`) — RLS 보존
- **And** `backup_retention_purged` audit emit (action_class=ACCOUNT_BACKUP, action=`backup_retention_purged`)
- **And** `tenant_backups` UNIQUE `(tenant_id, backup_date) WHERE purged_at IS NULL` — soft-delete 후 재실행 가능 (idempotent)
- **And** quarterly 1-year (`retention_class='quarterly'`) 행은 honestly DEFER — `backup_retention_archived` action은 ActionClass registry placeholder, wire 0건 (sprint-scale, 별도 Story)

### AC #4 — Self-download UI (epics.md AC #3)

- **Given** 운영자 UI에서 "최근 7일 백업 다운로드" 버튼
- **When** 12-2 wire
- **Then** `apps/web/app/[locale]/(dashboard)/account/backup/{layout,page}.tsx` RSC 페이지 (12-5 `/account/security` 패턴)
- **And** `apps/web/components/m12-account/BackupDownloadPanel.tsx` (NEW, Client Component, shadcn Button + sonner toast)
- **And** 백업 목록: `GET /api/v1/account/backups/recent` → server-side fetch (`fetchBackupListServerSide`) → 백업 ID + 날짜 + size + sha256 표시
- **And** 다운로드 버튼: 각 행마다 `GET /api/v1/account/backups/{backup_id}/download` → `application/json` 응답 + `Content-Disposition: attachment; filename="backup-{YYYY-MM-DD}.json"` + `X-Backup-SHA256` 검증
- **And** ko-KR.json 1 NEW namespace `account_backup` (~12 strings: panel_title, list_header, button_download, button_downloading, toast_success, toast_error_size_exceeded, toast_error_audit_emit, toast_error_generic, format_bytes, format_date, etc.)
- **And** Sidebar entry: `apps/web/lib/menu-config.ts` `INDUSTRY_MENU_MAP` 4 positions 모두 + `packages/services/m0_onboarding/industry_menu.py` Python 동시 (drift detector `test_menu_config_consistency.py` 강제)
- **And** capability gate: **industry-agnostic** (CR 12-1 L4 precedent — security baseline) → capability 의도적 부재, `require_role("owner")` 만 적용

### AC #5 — Owner-only role gate (AD-10)

- **Given** AD-10 4-role: owner / member / viewer / consultant_proxy
- **When** `GET /api/v1/account/backups/recent` + `GET /api/v1/account/backups/{backup_id}/download` + `POST /api/v1/account/backups/trigger` 호출
- **Then** `owner` → 200 (다운로드/트리거 허용)
- **And** `member` / `viewer` / `consultant_proxy` → 403 FORBIDDEN_ROLE (M2 진입 권한 ≠ 운영자 권한)
- **And** 12-1 self-enrollment이 `require_any_role("owner","member")`였던 것과 대조 (백업은 운영자 only)

### AC #6 — A5 forward-lock 5 values (ACCOUNT_BACKUP class)

- **Given** 5 audit actions 필요: `backup_created` / `backup_failed` / `backup_retention_purged` / `backup_downloaded` / `backup_triggered`
- **When** 12-2 wire
- **Then** `apps/api/core/audit_action.py` 신규 `ActionClass.ACCOUNT_BACKUP = "account_backup"` (append, line 66) + `AccountBackupAction` Literal 타입 5 values + `AuditAction` union에 추가 + `_REGISTRY` 5-value frozenset + `__all__` export
- **And** AD-2 invariant: `audit_logs.action` CHECK-less 결정 유지 (conventions.md §10.1 + 907-910) — drift detector `tests/integration/test_audit_logs_no_action_check_constraint.py` 음성 회귀 검증
- **And** 3-way drift detector: `tests/integration/test_audit_action_consistency.py` extension — registry ↔ DB CHECK (검증 site 없음) ↔ call sites (5 사이트) 정합
- **And** `backup_failed`는 try/except 가드 — `apps/api/modules/m12_account/services/backup_export_service.py` 의 `run_backup` 실패 시 `BackupServiceError` raise 직전 audit emit (CR 1.1 audit-first pattern)

### AC #7 — RLS 5-policy split + capability v1.14 (AD-3 + AD-9)

- **Given** AD-3 RLS multi-tenancy + AD-9 Seoul tenure
- **When** 12-2 Alembic 0024 + RLS 0014 wire
- **Then** `apps/api/alembic/versions/0024_tenant_backups.py` — 12 columns + 2 indexes + UNIQUE + 2 COMMENT + down_revision=`0023_used_challenge_tokens`
- **And** `supabase/policies/0014_tenant_backups_rls.sql` — `ENABLE` + `FORCE RLS` + 5-policy split (precedent `0013_users_totp_columns_rls.sql`):
  - `tenant_backups_select_same_tenant` — SELECT same-tenant
  - `tenant_backups_select_owner` — SELECT owner role (AD-10)
  - `tenant_backups_insert_same_tenant` — INSERT same-tenant (cron runs as app service, RLS honors tenant_id)
  - `tenant_backups_update_forbidden` — UPDATE forbidden (AD-2 INSERT-only)
  - `tenant_backups_delete_forbidden` — DELETE forbidden (AD-2 INSERT-only; soft-delete via `purged_at` column)
- **And** `docs/capability-matrix.md` v1.14 — `Capability.BACKUP_EXPORT` 신규 (industry-agnostic, 12-1 L4 precedent — "백업은 운영자 인프라"). CR 12-1 L4 패턴: documented but NOT enforced in any route (capability gate intentional absence).
- **And** `tests/integration/test_capability_matrix_v1_14_drift.py` 신규 — registry ↔ capability-matrix.md ↔ 4 industries ALL grant BACKUP_EXPORT

### AC #8 — JSON schema versioning + RLS-bypass-free restoration (epics.md AC #4)

- **Given** 다운로드 JSON은 동일 schema로 RLS bypass 없이 복원 가능
- **When** 12-2 wire
- **Then** `schema_version: "1.0"` top-level envelope — 향후 호환성 보존 (1.1 추가 시 major version bump)
- **And** envelope keys 4종 고정: `schema_version`, `backup_id`, `tenant_id`, `created_at`, `backup_date`, `tables` (7 키)
- **And** `tables.{name}` 모두 list[dict] — 각 dict는 ORM column 명 + 값 (JSON-serializable)
- **And** `audit_logs.payload` 등 JSONB 컬럼은 JSON-in-JSON (stringified once, then re-parsed on restore)
- **And** **복원 자체는 wire 0건** — 12-2는 write + download only. 복원 endpoint는 미래 Story (12-2.5 또는 13-N). 다만 스키마는 RLS-respecting하도록 설계: 각 row는 `tenant_id` 포함, INSERT 시 RLS가 tenant 격리 enforce.
- **And** `closure_pdf_export` precedent (6-3) 와 같이 structural parity: Python kernel 직렬화 ↔ TS mirror (drift detector로 검증)

## Tasks / Subtasks (atomic wire)

### Task 1 — Pure kernel (7-table JSON dump + sha256 결정론 digest)

- **AC**: #1, #8
- **파일**: `packages/services/m12_account/backup_export.py` (NEW, ~250 lines)
- **subtasks**:
  - [ ] 1.1 STDIN-only: `import json, hashlib, uuid, datetime` (no DB, no clock, no random — pure kernel AD-11)
  - [ ] 1.2 `def serialize_backup_payload(payload: dict[str, Any]) -> bytes`: `json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False).encode("utf-8")` (period_cost.py:153-159 _stable_json_dumps precedent)
  - [ ] 1.3 `def compute_payload_sha256(payload_bytes: bytes) -> str`: `hashlib.sha256(payload_bytes).hexdigest()`
  - [ ] 1.4 `def build_backup_envelope(*, backup_id: UUID, tenant_id: UUID, created_at: datetime, backup_date: date, tables: dict[str, list[dict]]) -> dict`: envelope builder (deterministic key order)
  - [ ] 1.5 `def collapse_audit_logs(payload: dict) -> dict`: audit_logs 365일 슬라이딩 (`occurred_at >= now - 365d`) — payload size limit 방어
  - [ ] 1.6 `MAX_PAYLOAD_BYTES: Final[int] = 50 * 1024 * 1024` (50 MB cap) — 50 MB 초과 시 `BackupPayloadTooLargeError` (typed exception)
  - [ ] 1.7 `Korean SSOT` 상수 5개: `BACKUP_EXPORT_TITLE_KO`, `BACKUP_RETENTION_PURGED_KO`, etc. (Final[str] 타입, audit_extension.py 패턴 따르되 pure kernel은 `Final`)
- **tests**: `tests/services/m12_account/test_backup_export.py` (NEW, 20+ cases):
  - envelope builder determinism (same input → same sha256)
  - 7-table collapse (audit_logs 365-day window, others all rows)
  - JSON reverse parse: serialize → parse → deep equal
  - 50 MB cap raises BackupPayloadTooLargeError
  - hashlib 결정론 (RFC test vector)

### Task 2 — Service layer (BackupExportService + audit emit)

- **AC**: #1, #6
- **파일**: `apps/api/modules/m12_account/services/backup_export_service.py` (NEW, ~350 lines)
- **subtasks**:
  - [ ] 2.1 `class BackupExportService` with `__init__(session, *, tenant_id, actor_id, trace_id)` (M12 precedent)
  - [ ] 2.2 `async def run_backup(self, *, retention_class: str = "daily") -> BackupResult`: cron-callable entry point
    - DB SELECT 7 tables (per tenant_id) → build envelope → serialize → INSERT `tenant_backups` (audit-first `backup_created`)
  - [ ] 2.3 `async def run_retention_sweep(self, *, cutoff: datetime) -> RetainResult`: 30-day rolling soft-delete
    - SELECT `tenant_backups` WHERE `tenant_id=? AND retention_class='daily' AND backup_date < cutoff AND purged_at IS NULL`
    - UPDATE `purged_at = now()` (NOT DELETE) — AD-2 INSERT-only preserves
    - audit emit `backup_retention_purged` for each row
  - [ ] 2.4 `async def trigger_backup(self, *, actor_id: UUID) -> BackupResult`: manual owner trigger (POST /backups/trigger)
  - [ ] 2.5 `async def list_recent_backups(self, *, days: int = 7) -> list[BackupMetadata]`: SELECT 7일 행
  - [ ] 2.6 `async def fetch_backup_payload(self, *, backup_id: UUID) -> BackupPayload`: SELECT 단일 행 + RLS check
  - [ ] 2.7 Audit-first guard: `try/except` around `emit_audit_typed` → `BackupServiceAuditEmitError` (12-4 P-09 precedent)
  - [ ] 2.8 Typed exception 5개 신규:
    - `BackupExportServiceError` (base, 500)
    - `BackupPayloadTooLargeError` (422, 50 MB cap)
    - `BackupNotFoundError` (404)
    - `BackupRetentionCutoffInvalidError` (422)
    - `BackupServiceAuditEmitError` (503)
- **imports**: `from apps.api.core.audit_action import ActionClass, emit_audit_typed` (ACCOUNT_BACKUP class)
- **tests**: `tests/api/m12_account/test_backup_export_service.py` (NEW, 15+ cases):
  - run_backup happy path (7 tables, row_counts, sha256)
  - run_backup audit-first emit (CR 1.1)
  - run_retention_sweep idempotent (2회 실행 → 2회째 0 row affected)
  - trigger_backup owner-only
  - list_recent_backups 7-day window
  - 5 typed exception mapping

### Task 3 — Cron jobs (backup_daily + backup_retention)

- **AC**: #1, #3
- **파일**:
  - `apps/api/jobs/backup_daily.py` (NEW, ~80 lines)
  - `apps/api/jobs/backup_retention.py` (NEW, ~80 lines)
- **subtasks**:
  - [ ] 3.1 `backup_daily.py::run(*, now: datetime | None = None) -> BackupResultAsync` — `document_retention.py:51-83` precedent 그대로
  - [ ] 3.2 header docstring: "Railway cron: schedule daily 02:00 KST (UTC 17:00) — outside peak. Failure behavior: any exception logged + Railway Slack alert."
  - [ ] 3.3 try/except → `backup_failed` audit emit (ACCOUNT_BACKUP, action=`backup_failed`) BEFORE raise (CR 1.1 audit-first)
  - [ ] 3.4 `backup_retention.py::run(*, now: datetime | None = None) -> RetainResultAsync` — KST 03:00 (UTC 18:00)
  - [ ] 3.5 Session lazy pattern (Story 0.2): `session_gen = get_session(); session = await session_gen.__anext__()`
  - [ ] 3.6 `try/except` → `backup_retention_purged` audit emit BEFORE raise
  - [ ] 3.7 `apps/api/jobs/__init__.py` docstring 갱신 — 2 jobs 추가 (daily 02:00 + retention 03:00 KST)
- **tests**: `tests/api/jobs/test_backup_daily.py` (NEW, 5 cases) + `test_backup_retention.py` (NEW, 5 cases):
  - cron entry import path (`apps.api.jobs.backup_daily:run`)
  - audit_failed on exception (try/except BEFORE raise)
  - retention sweep idempotent
  - timezone KST/UTC conversion (now=KST 02:00 → expected UTC 17:00)

### Task 4 — HTTP routes extension (3 routes)

- **AC**: #4, #5
- **파일**: `apps/api/modules/m12_account/handlers.py` (EXTENSION, +~120 lines)
- **subtasks**:
  - [ ] 4.1 Pydantic request schema inline (no `schemas.py`): `BackupTriggerRequest(BaseModel)` empty body (model_config forbid extra)
  - [ ] 4.2 Response schemas: `BackupListItem`, `BackupListResponse`, `BackupDownloadResponse` (sha256 + size + created_at)
  - [ ] 4.3 `router.get("/account/backups/recent", ...)` — list 7일, `require_role("owner")`
  - [ ] 4.4 `router.get("/account/backups/{backup_id}/download", ...)` — JSON bytes download, `Response(content=json_bytes, media_type="application/json", headers={"Content-Disposition": ..., "X-Backup-SHA256": ...})` (6-3 PDF export pattern)
  - [ ] 4.5 `router.post("/account/backups/trigger", ...)` — manual owner trigger, `require_role("owner")`
  - [ ] 4.6 `_resolve_trace_id` 재사용 (handlers.py:84-98)
  - [ ] 4.7 Path param: `backup_id: UUID` (FastAPI auto-validate, 422 on malformed)
  - [ ] 4.8 routes summary docstring 갱신: 9 → 12 routes (+3)
  - [ ] 4.9 **No capability gate** (industry-agnostic, 12-1 L4 precedent) — `require_role("owner")` 만
- **tests**: `tests/api/m12_account/test_backup_handlers_route_shape.py` (NEW, 12 cases):
  - 3 routes path + method
  - role gate (owner allow, member/viewer/consultant_proxy deny)
  - response shape (BackupListItem, sha256, size_bytes)
  - 404 on missing backup_id
  - 422 on malformed backup_id

### Task 5 — Alembic 0024 + RLS 0014 + audit_action 5 values + capability v1.14

- **AC**: #6, #7
- **파일**:
  - `apps/api/alembic/versions/0024_tenant_backups.py` (NEW, ~200 lines)
  - `supabase/policies/0014_tenant_backups_rls.sql` (NEW, ~80 lines)
  - `apps/api/core/audit_action.py` (EXTENSION, +5 lines)
  - `docs/capability-matrix.md` (EXTENSION, +1 entry)
  - `tests/architecture/test_api_calls_only_ports.py` (EXTENSION, +1 entry in ALLOWED_SERVICE_SUBMODULES)
- **subtasks**:
  - [ ] 5.1 Alembic 0024 schema (12 columns):
    - `backup_id UUID PK dflt uuid.uuid4` (v4, AD-15 tenant_id v4 supersede)
    - `tenant_id UUID NOT NULL FK→tenants.id CASCADE`
    - `backup_date DATE NOT NULL` (KST date)
    - `created_at TIMESTAMPTZ NOT NULL`
    - `schema_version VARCHAR(16) NOT NULL DEFAULT '1.0'`
    - `payload JSONB NOT NULL` (7-table dump)
    - `payload_sha256 CHAR(64) NOT NULL`
    - `row_count_total INTEGER NOT NULL`
    - `audit_log_exported_rows INTEGER NOT NULL DEFAULT 0`
    - `retention_class VARCHAR(16) NOT NULL DEFAULT 'daily'`
    - `purged_at TIMESTAMPTZ NULL`
    - `triggered_by_user_id UUID NULL FK→users.id SET NULL` (manual trigger trace)
  - [ ] 5.2 Indexes:
    - `ix_tenant_backups_tenant_date` on `(tenant_id, backup_date DESC)` — primary access
    - `ix_tenant_backups_retention` on `(tenant_id, retention_class, created_at)` — retention sweep
    - Partial UNIQUE `(tenant_id, backup_date) WHERE purged_at IS NULL` — idempotent re-run
  - [ ] 5.3 2 COMMENT (payload / schema_version) — NFR4 contract
  - [ ] 5.4 AD-2 INSERT-only trigger: `BEFORE UPDATE OR DELETE` raise `append-only violation` (0001 패턴 + 0024 specific)
  - [ ] 5.5 RLS 0014 5-policy split (precedent 0013 template):
    - `tenant_backups_select_same_tenant` SELECT
    - `tenant_backups_select_owner` SELECT (owner role)
    - `tenant_backups_insert_same_tenant` INSERT
    - `tenant_backups_update_forbidden` UPDATE (no rows — fail-closed)
    - `tenant_backups_delete_forbidden` DELETE (no rows — fail-closed)
  - [ ] 5.6 `apps/api/core/audit_action.py`:
    - line 65에 `TWO_FACTOR_AUTH` 뒤 line 66에 `ACCOUNT_BACKUP = "account_backup"` append
    - `AccountBackupAction` Literal 정의: `"backup_created", "backup_failed", "backup_retention_purged", "backup_downloaded", "backup_triggered"` (5 values)
    - `AuditAction` union에 `AccountBackupAction` 추가
    - `_REGISTRY` `ActionClass.ACCOUNT_BACKUP` 엔트리: `("audit_logs", frozenset({5 values}))`
    - `__all__`에 `AccountBackupAction` 추가
  - [ ] 5.7 `Capability.BACKUP_EXPORT = "backup_export"` 신규 — **industry-agnostic** (12-1 L4 precedent; 4 industries 모두 grant) — `_INDUSTRY_CAPABILITIES` 4 entries 모두에 `Capability.BACKUP_EXPORT` 추가
  - [ ] 5.8 `docs/capability-matrix.md` v1.14 갱신: `BACKUP_EXPORT` row + 4 industries 모두 `allowed=true` + capability-matrix v1.14 drift detector
  - [ ] 5.9 `tests/architecture/test_api_calls_only_ports.py` ALLOWED_SERVICE_SUBMODULES list에 `packages.services.m12_account.backup_export` 추가 (CR 11-3 D-2 sweep)
  - [ ] 5.10 `tests/api/test_alembic_0024_tenant_backups.py` (NEW, 12 cases):
    - 12 columns exist
    - 2 indexes + partial UNIQUE
    - downgrade → drop columns
  - [ ] 5.11 `tests/rls/test_tenant_backups_rls.py` (NEW, 6 cases):
    - 5-policy rejects cross-tenant SELECT
    - 5-policy rejects non-owner SELECT
    - INSERT same-tenant allowed
    - UPDATE forbidden (AD-2)
    - DELETE forbidden (AD-2)
    - Soft-delete via purged_at allowed
- **drift detectors**:
  - [ ] 5.12 `tests/integration/test_audit_action_consistency.py` extension — ACCOUNT_BACKUP 3-way 정합 (registry ↔ DB CHECK (no-op for audit_logs) ↔ call sites 5)
  - [ ] 5.13 `tests/integration/test_capability_matrix_v1_14_drift.py` (NEW) — registry ↔ capability-matrix.md ↔ 4 industries 정합

### Task 6 — Frontend (page + 1 component + ko-KR.json + sidebar)

- **AC**: #4
- **파일**:
  - `apps/web/app/[locale]/(dashboard)/account/backup/layout.tsx` (NEW, ~20 lines)
  - `apps/web/app/[locale]/(dashboard)/account/backup/page.tsx` (NEW, RSC, ~80 lines)
  - `apps/web/components/m12-account/BackupDownloadPanel.tsx` (NEW, Client Component, ~200 lines)
  - `apps/web/lib/m12-account-backup.ts` (NEW TS mirror, ~120 lines)
  - `apps/web/lib/server-api.ts` (EXTENSION, +2 functions: `fetchBackupListServerSide`, `fetchBackupDownloadServerSide`)
  - `apps/web/messages/ko-KR.json` (EXTENSION, +1 namespace `account_backup` with ~12 strings)
  - `apps/web/lib/menu-config.ts` (EXTENSION, +1 entry in INDUSTRY_MENU_MAP × 4 industries)
  - `packages/services/m0_onboarding/industry_menu.py` (EXTENSION, +1 entry × 4 industries)
  - `apps/web/components/sidebar/Sidebar.tsx` (확인 — 기존 패턴 자동 추출)
- **subtasks**:
  - [ ] 6.1 `/account/backup` RSC page (6-3 PDF export 페이지 + 12-5 security 페이지 패턴):
    - `export const dynamic = "force-dynamic"` line 20
    - `await params;` line 29 (Next 15+ Promise<params>)
    - `cookies()` → `sb-access-token` → `fetchBackupListServerSide(accessToken, traceId)`
    - Fail-closed fallback (CR 11-4 D-005): server-side fetch 실패 시 empty list + viewer role
  - [ ] 6.2 `<BackupDownloadPanel>` Client Component:
    - `"use client"` (line 24)
    - `useTranslations("account_backup")` (line 66)
    - `const [is_downloading, setIsDownloading] = React.useState(false);` (snake_case 관례)
    - 7-row list (or fewer if 7일 미만) + size + sha256 + date
    - 다운로드 버튼: `await fetchBackupDownloadServerSide(backup_id, accessToken)` → JSON bytes (Blob)
    - `triggerBackupDownload(json_bytes, filename)` 헬퍼 (mirror 6-3 triggerClosingPdfExportDownload)
    - `data-testid`, `data-backup-id`, `data-backup-date`, `data-status` (테스트 훅)

  - [ ] 6.3 `apps/web/lib/m12-account-backup.ts` (TS mirror):
    - `BACKUP_EXPORT_TITLE_KO = "백업 다운로드"` (mirror Python)
    - `BACKUP_DATE_KO`, `BACKUP_SIZE_KO`, `BACKUP_SHA256_KO`
    - `BACKUP_RETENTION_DAYS = 7 as const`
    - `BACKUP_VALUES = [...] as const; type Backup = (typeof BACKUP_VALUES)[number]`
    - `triggerBackupDownload(bytes, filename)` 헬퍼 (6-3 triggerClosingPdfExportDownload 패턴)
    - `formatBackupSize(size_bytes)` B/KB/MB
    - `buildBackupFilename(backup_date)` → `backup-${YYYY-MM-DD}.json`

  - [ ] 6.4 `apps/web/lib/server-api.ts` 확장:
    - `BackupListServerSideResponse` interface
    - `fetchBackupListServerSide(accessToken, traceId)` → `fetch(${apiBaseUrl()}/api/v1/account/backups/recent)`
    - `fetchBackupDownloadServerSide(backupId, accessToken)` → fetch individual + return bytes

  - [ ] 6.5 `apps/web/messages/ko-KR.json` namespace `account_backup`:
    - `panel_title` ("백업 다운로드")
    - `panel_subtitle` ("최근 7일 KST 02:00 자동 백업")
    - `list_header` (date / size / sha256)
    - `button_download` ("다운로드")
    - `button_downloading` ("다운로드 중...")
    - `button_trigger` ("지금 백업 실행")
    - `toast_success_download` ("백업 다운로드 완료")
    - `toast_success_trigger` ("백업 생성 시작")
    - `toast_error_forbidden` ("owner 권한 필요")
    - `toast_error_generic` ("백업 다운로드 실패")
    - `format_bytes` (B/KB/MB labels)
    - `format_date` ("YYYY년 MM월 DD일")

  - [ ] 6.6 Sidebar entry:
    - `apps/web/lib/menu-config.ts` INDUSTRY_MENU_MAP 4 industries 모두 "계정 보안" 다음에 "백업 다운로드" 메뉴 append
    - `packages/services/m0_onboarding/industry_menu.py` 4 industries 모두 동일하게 append
    - `tests/integration/test_menu_config_consistency.py` — drift detector가 4 positions × 2 files 정합 강제 (자동 검증)

  - [ ] 6.7 **page.tsx mount MUST actually mount** (CR 11-4 D-001): `<BackupDownloadPanel accessToken={accessToken} ... />` 실제 import + render (component file 생성만 금지)
- **tests**:
  - [ ] 6.8 `apps/web/__tests__/lib/m12-account-backup-parity.test.ts` (NEW, 8 cases):
    - Python ↔ TS mirror 8 vector labels
    - BACKUP_RETENTION_DAYS = 7
    - BACKUP_VALUES tuple
  - [ ] 6.9 `apps/web/__tests__/backup-download-panel.test.tsx` (NEW, 6 cases):
    - 7-row render
    - 다운로드 버튼 클릭 → fetch 호출
    - sha256 표시
    - error envelope 분기 toast
    - is_downloading state transition
    - data-testid / data-backup-id / data-status hooks

### Task 7 — Cross-language drift detector + audit consistency

- **AC**: #6, #7, #8
- **파일**:
  - `tests/integration/test_m12_account_backup_cross_language_drift.py` (NEW, ~200 lines)
  - `tests/integration/test_m12_account_backup_kernel_parity.py` (NEW, ~150 lines)
- **subtasks**:
  - [ ] 7.1 `test_m12_account_backup_cross_language_drift.py` — 12-5 `test_m12_two_factor_gate_cross_language_drift.py` 패턴 (D-13 structural detector):
    - parse Python: `tests/services/m12_account/test_backup_export.py`
    - parse TS: `apps/web/__tests__/lib/m12-account-backup-parity.test.ts`
    - 8 vector labels 정합 (parity 1..8)
    - input tuples 정합
    - 6 key output fields 정합
  - [ ] 7.2 `test_m12_account_backup_kernel_parity.py` — 18 pytest cases (12-5 D-PARITY-01 패턴):
    - `serialize_backup_payload` 결정론 (same input → same sha256)
    - `build_backup_envelope` key order
    - `collapse_audit_logs` 365-day window
    - 50 MB cap raises
    - hashlib vector test
  - [ ] 7.3 `tests/integration/test_audit_action_consistency.py` extension — ACCOUNT_BACKUP 5 values 3-way 정합 (registry vs DB CHECK (no-op for audit_logs) vs call sites 5)
  - [ ] 7.4 `tests/integration/test_capability_matrix_v1_14_drift.py` (NEW) — registry ↔ capability-matrix.md ↔ 4 industries

### Task 8 — Docs + 3중 게이트 final clean

- **AC**: #1-8 종합
- **파일**:
  - `docs/conventions.md` (EXTENSION, +§12 Backup Operations)
  - `docs/architecture-inventory.md` (EXTENSION, m12_account section entry)
  - `docs/account-security-operations.md` (EXTENSION, Backup operations section)
  - `docs/capability-matrix.md` (EXTENSION, v1.14 entry)
  - `docs/deferred-work.md` (EXTENSION, ## Deferred from: 12-2 — quarterly archive + restore endpoint + Playwright E2E)
- **subtasks**:
  - [ ] 8.1 `docs/conventions.md` §12 Backup Operations:
    - §12.1 Backup scope (7 tables, AD-9 Seoul)
    - §12.2 Cron schedule (KST 02:00 daily + KST 03:00 retention)
    - §12.3 Retention policy (30-day rolling; quarterly DEFER)
    - §12.4 Owner role gate (AD-10)
    - §12.5 JSON schema versioning (1.0)
    - §12.6 Korean SSOT (ko-KR.json + audit_extension)
  - [ ] 8.2 `docs/architecture-inventory.md` m12_account section — 12-2 entry:
    - M12 routes: 12 (was 9)
    - AccountBackup capability: v1.14 industry-agnostic
    - ActionClass.ACCOUNT_BACKUP: 5 values
    - Alembic 0024: tenant_backups 12 columns
    - RLS 0014: 5-policy split
    - Cross-references: cron jobs, /jobs/backup_daily, /jobs/backup_retention
  - [ ] 8.3 `docs/account-security-operations.md` — Backup operations section:
    - Cron schedules
    - Backup storage rationale (Postgres JSONB vs Storage)
    - Restoration (future Story — v1.x)
    - SLA: NFR4 RPO 24h / RTO 4h
  - [ ] 8.4 `docs/capability-matrix.md` v1.14:
    - `BACKUP_EXPORT` row with rationale ("owner-only, industry-agnostic, security baseline CR 12-1 L4")
    - 4 industries 모두 `allowed=true`
  - [ ] 8.5 `docs/deferred-work.md` ## Deferred from: 12-2:
    - Quarterly 1-year archive (NFR4 2절) — sprint-scale
    - Manual restore endpoint (RLS-bypass-free) — future Story
    - Playwright E2E (12-5 T6 pattern) — sprint-scale
    - Gzip compression — schema-compatible, future
  - [ ] 8.6 3중 게이트 FINAL CLEAN:
    - `ruff check apps/api packages` — 0 NEW errors on 12-2 surface
    - `import-linter` — 2 KEPT 0 broken (ALLOWED_SERVICE_SUBMODULES extension)
    - `pytest tests/api/m12_account tests/services/m12_account tests/integration/test_m12_account_backup_* tests/rls/test_tenant_backups_rls.py` — all pass
    - `vitest` (m12-account-backup + 12-account-backup cross-language) — all pass
  - [ ] 8.7 `harness-3gates` rerun (Makefile) + SDR MAX 갱신 separate line per CR 11-2 L7 (unambiguous parser match)
  - [ ] 8.8 `CONVENTIONS_LINT` grep sweep (no str/Enum forbidden patterns in 12-2 surface)

## Dev Notes

### Architecture compliance

- **AD-9 Seoul**: Postgres JSONB는 Supabase Seoul Postgres에 상주 → AD-9 자동 만족. Storage/bucket Migration 불요. Cross-region replication은 AD-9 disabled.
- **AD-11 dependency direction**: `packages.services.m12_account.backup_export` (pure kernel) → `apps.api.modules.m12_account.services.backup_export_service` (service) → `apps.api.modules.m12_account.handlers` (HTTP) → `apps.api.jobs.backup_daily` / `backup_retention` (cron). Layer direction strictly forward.
- **AD-2 audit-first + INSERT-only**: `tenant_backups` 행은 INSERT-only (audit_logs 0001 trigger pattern). Soft-delete via `purged_at` column. UPDATE/DELETE attempts raise `append-only violation`.
- **AD-3 RLS multi-tenancy**: 5-policy split (same-tenant select + owner-only select + same-tenant insert + update forbidden + delete forbidden). `current_setting('app.tenant_id', true)::uuid` GUC.
- **AD-8 monetary types**: KRW BigInt→string (`default=str`), USD `Decimal` → `default=str` (period_cost.py:153-159 패턴). 직렬화 시 모든 money type string.
- **AD-10 4-role**: `require_role("owner")` (백업은 운영자 only). 12-1 self-enrollment (`require_any_role("owner","member")`)와 대조.
- **AD-14 banned infra**: Cron only via Railway cron (Celery/Kafka/Redis banned). `apps/api/jobs/` precedent followed.
- **AD-15 §4 error envelope**: 모든 응답/에러 `{code, message_ko, details, trace_id}` SSOT. ko-KR.json 1 NEW namespace `account_backup`.
- **AD-15 §1 naming**: snake_case DB/Python, kebab-case routes, PascalCase TS. `account/backups` route (12-5 `account/2fa` 패턴).
- **AD-15 §2 time**: ISO-8601 UTC 저장, KST 표시. `backup_date` DATE는 KST date (cron KST 02:00 → KST date).
- **AD-15 §3 identity**: `tenant_id` UUID v4 (AD-15 supersede variance), `backup_id` UUID v4 (audit_logs FK-less pattern).
- **AD-2 audit-first**: 5 audit actions 모두 mutation 전 emit (CR 1.1 pattern). `backup_failed`는 try/except에서 raise 직전 emit.

### Library framework

- **의존성 0**: STACK_PIN.yaml 변경 없음. Supabase Postgres (이미 pinned) + stdlib (json, hashlib) + SQLAlchemy 2.0.36 (pinned) + Pydantic 2.11.9 (pinned) + FastAPI 0.139.2 (pinned) + structlog 26.1.0 (notes, 12-5 도입).
- **NO new SDK**: `supabase` 2.10.0 (pinned) 사용 NO. Storage API 호출 0건. `@supabase/storage-js` 도입 0.
- **NO pgmq / pg_cron / celery / apscheduler**: 외부 scheduler (Railway cron) only. `_stable_json_dumps` precedent (period_cost.py:153).

### File structure

- **Pure kernel**: `packages/services/m12_account/backup_export.py` (NEW, ~250 lines) — stdlib-only, no DB, no clock, no random.
- **Service**: `apps/api/modules/m12_account/services/backup_export_service.py` (NEW, ~350 lines) — DB I/O + audit emit.
- **HTTP**: `apps/api/modules/m12_account/handlers.py` (EXTENSION, +~120 lines) — 3 routes 추가.
- **Cron**: `apps/api/jobs/backup_daily.py` + `apps/api/jobs/backup_retention.py` (NEW, ~160 lines combined).
- **Alembic**: `apps/api/alembic/versions/0024_tenant_backups.py` (NEW, ~200 lines) — 12 columns + 2 indexes + partial UNIQUE + AD-2 trigger.
- **RLS**: `supabase/policies/0014_tenant_backups_rls.sql` (NEW, ~80 lines) — 5-policy split.
- **Audit**: `apps/api/core/audit_action.py` (EXTENSION, +5 lines) — ACCOUNT_BACKUP class + 5 values.
- **Capability**: `apps/api/core/capability.py` (EXTENSION, +1 entry) + `docs/capability-matrix.md` (EXTENSION, v1.14).
- **Import-linter**: `tests/architecture/test_api_calls_only_ports.py` (EXTENSION, +1 entry).
- **Frontend**: `apps/web/app/[locale]/(dashboard)/account/backup/{layout,page}.tsx` (NEW) + `apps/web/components/m12-account/BackupDownloadPanel.tsx` (NEW) + `apps/web/lib/m12-account-backup.ts` (NEW) + `apps/web/lib/server-api.ts` (EXTENSION).
- **Docs**: `docs/conventions.md` §12 + `docs/architecture-inventory.md` + `docs/account-security-operations.md` + `docs/capability-matrix.md` + `docs/deferred-work.md`.
- **Tests**: 8 NEW test files (kernel + service + cron + handlers + alembic + RLS + parity + drift).

### Testing standards

- **pytest** (def test_*, asyncio.run pattern per CR 4-3): kernel 20+ / service 15+ / cron 10 / handlers 12 / alembic 12 / RLS 6 = 75+ NEW pytest cases.
- **vitest**: TS mirror 8 + BackupDownloadPanel 6 = 14 NEW vitest cases.
- **drift detector**: structural cross-language parity (pure pytest, 12-5 L4 pattern).
- **3중 게이트**: ruff scoped (0 errors) + import-linter (2 KEPT 0 broken) + pytest (all pass, ~1,533 baseline + 75+ NEW = ~1,608).
- **MAX SDR 갱신**: separate line for unambiguous parser match per CR 11-2 L7.

### Project Structure Notes

- **cj-style 6번째 epic 연속**: 12-2는 12-1 / 12-4 / 12-5 패턴을 그대로 따름 (router 흡수 + capability v1.14 + 5-policy RLS + alembic 0024 + RLS 0014).
- **honest-DEFER discipline 6번째 연속**: 12-2 atomic wire는 30-day rolling까지. Quarterly 1-year, restore, Playwright E2E 모두 honestly DEFER.
- **AD-2 INSERT-only 강제**: `tenant_backups` trigger BEFORE UPDATE OR DELETE raise `append-only violation` (audit_logs 0001 pattern).
- **cross-language parity**: pure kernel → service → handlers + TS mirror → drift detector 1 path (12-5 D-13 pattern).
- **Pydantic `model_config = ConfigDict(extra="forbid")`**: 모든 request schema (12-4 convention).
- **`_resolve_trace_id` 재사용**: handlers.py:84-98 (3-tier fallback).
- **DR-005 fallback**: Server-side fetch 실패 시 fail-closed empty list + viewer role (CR 11-4 D-005).
- **Pydantic response schemas inline**: handlers.py (no schemas.py — 12-4 convention).

### Previous story intelligence

- **12-1 (2FA)**: AES-256-GCM lazy wrapper pattern (CR 12-1 L2). 12-2는 payload 암호화 안 함 (NFR6 KMS via Supabase 기본 at-rest encryption); 메타 row는 plaintext (audit transparency).
- **12-4 (carry-over sprint)**: 4 form components pattern + 14 typed exception handlers in main.py. 12-2는 5 typed exceptions + 5 envelope handlers.
- **12-5 (atomic wire)**: P-06 TOTP proof pattern + cross-language drift detector + D-001 page.tsx mount + D-002 ko-KR.json SSOT + D-005 unknown state reject. 12-2는 12-5 패턴 그대로 (BackkupDownloadPanel + TS mirror + drift detector).
- **6-3 (PDF export)**: 6-task 분할 + closing_pdf_export.py + ClosingPdfExportButton.tsx + byte stream download. 12-2는 6-3 패턴 + Scheduler (cron) 추가.
- **CR 11-3 honest-DEFER**: partial wire 금지. 12-2는 8 tasks atomic wire (no partial).
- **CR 11-4 D-001**: page.tsx mount MUST actually mount. 12-2 verify.
- **CR 11-4 D-002**: ko-KR.json SSOT single file. 12-2 1 NEW namespace 추가.
- **CR 11-4 D-005**: TS mirror unknown state fall-through → reject. 12-2 verify.
- **CR 12-1 L4**: industry-agnostic security baseline. 12-2 BACKUP_EXPORT capability 미러.
- **CR 12-5 D-13**: structural cross-language drift detector. 12-2 NEW detector.
- **CR 12-5 D-14**: typed exception main.py envelope handler 등록. 12-2 5 envelope handlers.
- **CR 12-5 D-15**: JSONB in-place mutation (MutableList.as_mutable). 12-2 payloads은 INSERT-only라 무관.

### Git intelligence

- **Last 3 commits**: `42b45fa` (Story 12.5 T8 partial close-out) + `e9582f6` (Story 12.5 T5+T7 atomic) + `cccebeb` (Story 12.5 T3+T4 atomic).
- **baseline_commit = `42b45fa`**: HEAD at spec creation (2026-08-12).
- **Pattern observed**: 12-1 commit `1004fc0` (T6+T10) → 12-4 commit `8735eb5` (carry-over) → 12-5 commits `f6fbf93` / `cccebeb` / `e9582f6` / `42b45fa`. 12-2 expected 1-3 commits atomic.
- **Atomic wire pattern**: 12-5 used 3 commits (T1+T2 / T3+T4 / T5+T7). 12-2 expected similar (2-3 commits for 8 tasks).

### Latest tech

- **stdlib json**: `json.dumps(..., default=str, sort_keys=True, ensure_ascii=False)` — period_cost.py:153-159 precedent.
- **stdlib hashlib**: `hashlib.sha256(payload_bytes).hexdigest()` — RFC test vector stable.
- **SQLAlchemy 2.0.36**: `sa.func.jsonb(payload)`, `MutableList.as_mutable(JSONB)` (CR 12-5 D-15 NOT applicable — INSERT-only).
- **Pydantic 2.11.9**: `BaseModel` + `ConfigDict(extra="forbid")` inline.
- **FastAPI 0.139.2**: `APIRouter`, `Response(content=bytes, media_type="application/json", headers={...})` (6-3 pattern).
- **NO new dependency**: 12-2 wire surface uses already-pinned libraries only.

### References

- epics.md:1198-1209 (Story 12.2 AC verbatim) [Source: _bmad-output/planning-artifacts/epics.md#Story-12-2]
- PRD §F12.2: "시스템은 일 1회 자동 백업 + 셀프 다운로드(JSON) 기능을 제공한다." [Source: _bmad-output/planning-artifacts/prd.md#F12.2]
- PRD NFR4: "RPO 24h / RTO 4h / 백업 보관 30일(자동), 1년(분기) / 감사로그 5년 append-only" [Source: _bmad-output/planning-artifacts/prd.md#NFR4]
- AD-9: "tenant data at rest, Auth, Storage, and backups live in Supabase ap-northeast-2 (Seoul)" [Source: _bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-9]
- AD-14: "Celery, Kafka, Redis as a persistent queue... banned" [Source: ARCHITECTURE-SPINE.md#AD-14]
- AD-2: "audit_logs are INSERT-only. PostgreSQL BEFORE UPDATE OR DELETE row-level triggers raise append-only violation" [Source: ARCHITECTURE-SPINE.md#AD-2]
- AD-8 monetary types: KRW BigInt / USD Decimal [Source: docs/architecture-decisions/AD-8-money-types-decision.md]
- AD-15 §4 error envelope: `{code, message_ko, details, trace_id}` [Source: docs/conventions.md#§4]
- M12 module pattern: `apps/api/modules/m12_account/` [Source: 12-4-epic-12-carry-over-sprint.md]
- 12-5 drift detector pattern: `tests/integration/test_m12_two_factor_gate_cross_language_drift.py` [Source: 12-5-m2-entry-gate-and-account-security-ui.md]
- 6-3 PDF export pattern: `apps/api/modules/m4_inventory/handlers.py:849-927` [Source: 6-3-closing-pdf-export.md]
- document_retention cron pattern: `apps/api/jobs/document_retention.py:51-83` [Source: Story 1.3 Task 1.3]
- capability matrix v1.13: `Capability.TWO_FACTOR_AUTH` industry-agnostic precedent [Source: docs/capability-matrix.md#v1.13]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}} — Sonnet 5 (or whatever the dev agent uses)

### Debug Log References

(placeholder — wire 시 populate)

### Completion Notes List

(placeholder — wire 시 populate)

### File List

(placeholder — wire 시 populate)

## Change Log

| Date | Change | Commit | Baseline | 3중 게이트 |
|---|---|---|---|---|
| 2026-08-12 | bmad-create-story spec 진입 done (backlog → ready-for-dev) | (n/a — spec only) | 42b45fa | (n/a — spec only) |

---

## Spec Decoupling Notes (12-2 next steps)

1. **12-2 dev-story wire**: 8 tasks atomic wire expected in 2-3 commits (mirror 12-5 pattern).
2. **12-1 close-out**: 12-1 in-progress → done after 12-5 T6 (Playwright) wire + 12-2 done.
3. **12-3 spec**: Account Deletion with Retention Consent (PRD §F12.3 + NFR5·6 retention + AD-3 RLS) — Epic 12 cj-style 3번째.
4. **Follow-up sprint (per CR 11-3)**: quarterly 1-year archive + restore endpoint + 12-5 T6 Playwright.
5. **Epic 12 close-out retro**: 12-1 + 12-2 + 12-3 done 후 retro.
