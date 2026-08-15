---
title: 'Epic 12 Story 3 — Account Deletion with Retention Consent (Tenants Status FSM + 2FA Challenge + Audit-First Retention)'
status: ready-for-dev
priority: HIGH
epic: 12
story_num: 3
story_key: 12-3-account-deletion-retention-consent
baseline_commit: 78b2e73
created: 2026-08-15
updated: 2026-08-15
---

> **2026-08-15 — bmad-create-story spec 진입 done** (12-3: backlog → ready-for-dev). Epic 12 cj-style 3-story 분할 (A14 권장안 a) 마지막 진입점 — 7번째 epic 연속 검증 (Epic 4·5·6·11·12 + Epic 11 carry-over + Epic 12 carry-over). 12-1 + 12-2 done 진입 확인 후 진입. 5 honestly DEFER per CR 11-3 honest-DEFER discipline 8번째 epic 연속 검증.
>
> **Atomic wire scope (결정)**: 해지 동의 모달 + tenants.status FSM (active→pending_deletion→deleted) + 30-day retention sweep + 2FA challenge gate (CR 12-5 L3 destructive endpoint 3-layer defense) + audit-first invariant (CR 1.1) + 5-year audit_logs 보존 (NFR4 2절) + 3중 게이트. partial wire 금지.
>
> **baseline_commit = `78b2e73`** (Story 12.5 T6 follow-up sprint + Epic 12 close-out tip — current HEAD).
>
> **Three user decisions locked** (2026-08-15):
> 1. **Storage target = `tenants.status` enum + `deletion_consents` table + Alembic 0025 + RLS 0015** — 의존성 0 (no STACK_PIN BUMP, no SDK bump, no Supabase Storage). AD-9 Seoul 거주성 만족 (Supabase Postgres = Seoul `ap-northeast-2`). 12-2 Postgres JSONB decision pattern 미러.
> 2. **Role gate = `require_role("owner")` + 2FA challenge token (CR 12-5 L3 destructive endpoint 3-layer defense)** — 해지 = destructive action (CR 12-5 L3 applicable). 12-1 self-enrollment `require_any_role("owner","member")` / 12-2 backup `require_role("owner")` / 12-5 2FA setup `require_any_role("owner","member")` 모두와 대조 — **owner-only + 2FA challenge 2중 가드** (sensitive token minting 3-layer: route layer require_role + service layer verify_totp_challenge + handler layer audit-first emit).
> 3. **Schema versioning = `schema_version: "1.0"` deletion envelope + 8 audit_actions (ACCOUNT_DELETION class) + retention_days=30 fixed** — epics.md AC verbatim "30일 / 30일 후 완전 삭제" → fixed 30일 (MVP, configurable 보류). quarterly 5-year audit append-only 보존 (NFR4 2절) — `audit_logs`는 `tenants` hard-delete 대상 외 (AD-2 INSERT-only invariant 보존).
>
> **cj-style 3-story 분할 7번째 epic 연속 검증** (Epic 4·5·6·11·12 + Epic 11 carry-over) + **CR 11-3 honest-DEFER discipline 8번째 연속** (atomic wire만, partial wire 0).
>
> **CR 11-4 lessons carry-over**: D-001 (page.tsx mount MUST actually mount) + D-002 (단일 `apps/web/messages/ko-KR.json` only) + D-005 (TS mirror unknown state fall-through → reject).
>
> **CR 12-1 lessons continue applied**: L1 (PyJWT `verify_exp=False` for 2FA deterministic testability) + L2 (AES-256-GCM lazy wrapper for `deletion_consent_id` encryption) + L3 (`_to_deletion_state(tenant)` ORM→kernel boundary conversion) + L4 (ACCOUNT_DELETION capability industry-agnostic precedent, 12-1 TWO_FACTOR_AUTH + 12-2 BACKUP_EXPORT 미러).
>
> **CR 12-5 lessons carry-over** (CRITICAL for destructive endpoint): D-13 (structural cross-language drift detector) + D-14 (모든 typed exception main.py envelope handler 등록) + **L3 (3-layer TOTP defense for sensitive token minting)** — CRITICAL: `POST /api/v1/account/deletion/request`는 destructive endpoint이므로 (a) require_role('owner') route layer + (b) verify_totp_challenge service layer + (c) audit-first emit handler layer 3중 defense 적용.
>
> **Honestly DEFER (per CR 11-3, partial wire 아님)**:
> - **Playwright E2E** (12-5 T6 패턴) — sprint-scale (atomic wire는 backend-only + Vitest parity).
> - **Quarterly 5-year audit aggregate** (NFR4 2절) — `deletion_audit_archived` action은 registry placeholder, wire 0건.
> - **Configurable retention_days** — MVP fixed 30일 (epics.md verbatim). 향후 settings aggregate (AD-23) extension으로 configurable.
> - **Cross-region replica** — AD-9에 의해 disabled.
> - **NFR7 2FA 진입 gate** (모든 account mutation 2FA 강제) — 현재 12-1 M2 entry 2FA만 적용. 12-3 destructive endpoint만 2FA 강제 (route layer).

# Story 12.3 — Account Deletion with Retention Consent

## Epic 12 context

Epic 12 (Account & Security Operations) cj-style 3-story 분할 완료 진행:

- **12-1** = 2FA Mandatory Gate to M2 Entry (TOTP + AD-10 4-role + capability v1.13) ← **done** (12-5 T6 wire + 12-5 follow-up sprint)
- **12-2** = Daily Auto-Backup + JSON Self-Download (Postgres JSONB + owner-only + capability v1.14) ← **done** (commit 5fced3b + bmad-code-review 3rd sweep chunk 1 commit b7a2522)
- **12-3** = Account Deletion with Retention Consent (PRD §F12.3 + NFR4·5·6 retention + AD-3·9·10) ← **이 스토리** (backlog → ready-for-dev)

**Epic 12 모듈 authority**: `apps/api/modules/m12_account/` (12 routes + 1 M2 entry gate wire DONE in 12-4 + 12-2 3 routes ADDED). 12-3은 동일한 라우터에 3 routes 추가 (request_deletion + cancel_deletion + deletion_status).

**Epic 12 capability matrix wire 누적**: v1.13 `TWO_FACTOR_AUTH` (industry-agnostic) → v1.14 `BACKUP_EXPORT` (industry-agnostic) → v1.15 `ACCOUNT_DELETION` (industry-agnostic, **owner-only**, 12-3 NEW).

**Epic 12 NFR coverage 누적**: NFR4 (백업 30일 + 분기 1년 + 감사로그 5년 append-only) + NFR5 (TLS 1.3) + NFR6 (AES-256 at rest + KMS 관리) + NFR7 (2FA 강제 — destructive endpoint 확장).

## Why this story (atomic wire 결정 근거)

**PRD §F12.3 verbatim**: "해지 요청 시 보관일수 + 삭제 동의 문구 강제 표시."

**epics.md AC verbatim** (lines 1217-1222):
> **Given** 나는 [설정] → [계정 해지] 클릭
> **When** 해지 진행
> **Then** "데이터 보관일수: 30일 / 30일 후 완전 삭제 / 동의 체크 필수" 모달 표시
> **And** 동의 체크 없이 [해지] 비활성
> **And** 해지 요청 시 `tenants.status='pending_deletion'`, 30일 후 완전 삭제 (NFR5 감사로그는 5년 별도 보존)
> **And** 동의 체크, 해지 요청 ts가 `audit_logs`에 append

**3 second-order decisions** (locked 2026-08-15):

1. **Storage = `tenants.status` FSM + `deletion_consents` table + audit_logs append-only** (decided: not Supabase Storage, not separate config table): AD-9는 Seoul 거주성만 요구 (Postgres native). 12-2 Postgres JSONB decision pattern (의존성 0 + STACK_PIN BUMP 0 + CODEOWNER 승인 불요) 적용. `tenants.status` 3-value enum (active / pending_deletion / deleted) + `deletion_consents` 별도 table (consent 추적 + AES-256-GCM 암호화) + `audit_logs` row에 동의 체크박스 ts 기록. **`tenants` + `deletion_consents` + `audit_logs` 3 tables = atomic source of truth**. Alembic 0025 + RLS 0015 + AD-2 INSERT-only natural 통합.

2. **Role gate = owner-only + 2FA challenge** (CR 12-5 L3 destructive endpoint 3-layer defense): epics.md AC verbatim "사장님" → owner. AD-10 4-role gate 활용 (`require_role("owner")`) + NFR7 2FA challenge token minting (12-1 P-06 `IssueChallengeTokenRequest` schema + `verify_totp_challenge` delegation pattern). viewer/consultant_proxy/member 모두 DENIED. 12-1 self-enrollment `require_any_role("owner","member")` / 12-2 backup `require_role("owner")`와 대조 — **해지는 destructive + sensitive 2중 가드** (12-5 L3 applicable, account deletion = destructive endpoint).

3. **Quarterly 5-year audit + configurable retention honestly DEFER**: epics.md AC에는 "5년 별도 보존" 명시하나 실 구현은 sprint-scale (별도 cron + 논리). 12-3 atomic wire는 30-day rolling sweep + audit_logs INSERT-only invariant 보존까지. `deletion_audit_archived`는 ActionClass registry placeholder, wire 0건. Configurable retention_days (settings aggregate extension)도 honestly DEFER — MVP fixed 30일.

**+ Epic 12 close-out path**: 12-3 done 진입 후 Epic 12 진짜 close-out (5/7 epic done + 12-3 done → 6/7 epic done Epic 12 done 유지).

## User Story

As a **사장님 (owner)**,
I want **계정 해지 요청 시 30일 보관 + 동의 체크 + 2FA 인증 후에만 진행되며, 30일 후 hard-delete (단 audit_logs는 5년 별도 보존)**,
so that **F12.3 (개인정보 보호 의무 준수 + 데이터 복구 시점 명확화) + NFR4 (감사로그 5년) + NFR6 (AES-256-GCM consent encryption) + NFR7 (destructive endpoint 2FA challenge) + AD-2 (audit_logs INSERT-only invariant) 모두 만족**.

(PRD §F12.3 + epics.md Story 12.3 verbatim + NFR4·5·6·7 + AD-2·3·9·10 + 12-5 carry-over pattern)

## Acceptance Criteria

### AC #1 — 해지 동의 모달 (epics.md Given/When/Then #1)

- **Given** 나는 [설정] → [계정 해지] 클릭
- **When** 해지 진행
- **Then** `AccountDeletionModal` 모달 표시 (shadcn Dialog, 12-5 TwoFactorChallengeDialog 패턴)
- **And** 모달 내용 (ko-KR.json namespace `account_deletion`):
  - "데이터 보관일수: **30일**" (bold)
  - "**30일 후 완전 삭제** (audit_logs 별도 5년 보존)" (bold, NFR4 2절 명시)
  - 동의 체크박스: "본인은 데이터 보존 기간 및 삭제 시점을 이해했으며 동의합니다" (model_config forbid extra)
  - [해지 요청] 버튼: 동의 체크 전 `disabled={!is_consent_checked}` (D-001 actual mount + 12-1 TwoFactorSetupForm 체크박스 패턴)
  - [취소] 버튼: 모달 close (no state change)
- **And** `apps/web/app/[locale]/(dashboard)/account/settings/{layout,page}.tsx` (NEW RSC, 12-5 `/account/security` 패턴)
- **And** ko-KR.json 1 NEW namespace `account_deletion` (~10 strings: modal_title, modal_description, consent_checkbox_label, retention_days_label, retention_after_label, button_request, button_cancel, button_requesting, toast_success, toast_error_required_2fa, toast_error_forbidden)
- **And** [해지 요청] 클릭 시 2FA challenge dialog 자동 open (CR 12-5 L3 3-layer trigger)

### AC #2 — 동의 체크 + 2FA challenge 강제 (epics.md AC #2 + NFR7 + CR 12-5 L3)

- **Given** 동의 체크박스 + 2FA TOTP code 동시 필요
- **When** [해지 요청] 클릭
- **Then** 동의 체크박스 unchecked → [해지 요청] 비활성 (disabled state)
- **And** 동의 체크 후 [해지 요청] 클릭 → `POST /api/v1/account/deletion/challenge-token` 호출 → response body의 `challenge_token`을 `TwoFactorChallengeDialog`에 전달 → TOTP 6-digit 입력 → `POST /api/v1/account/deletion/request` 호출 (Bearer + challenge_token)
- **And** 2FA 미설정 사용자 → `M12TwoFactorRequiredError` 403 envelope (12-1 handler pattern) — [2FA 설정으로 이동] CTA 표시
- **And** TOTP code invalid → `M12TwoFactorInvalidError` 401 envelope (5회 실패 시 lockout, 12-1 pattern)
- **And** `deletion_2fa_failed` audit emit (CR 12-5 L3 audit-first BEFORE raise, CR 1.1 invariant)
- **And** `deletion_requested` audit emit (CR 1.1 invariant) AFTER successful state transition
- **And** CR 12-5 L3 3-layer defense:
  - Layer 1 (route): `require_role("owner")` + 2FA TOTP 검증을 route handler 진입 시 enforce
  - Layer 2 (service): `verify_totp_challenge(token, totp_code)` delegation (12-1 P-06 pattern) — service layer 진입 시 re-verify (no trust boundary)
  - Layer 3 (handler): `audit-first emit BEFORE raise` (CR 1.1 invariant) — 모든 예외 경로에 audit row 보장

### AC #3 — tenants.status='pending_deletion' 전이 + 30일 후 완전 삭제 (epics.md AC #3 + NFR4 2절)

- **Given** 해지 요청 시 tenants.status FSM 전이
- **When** `POST /api/v1/account/deletion/request` 성공
- **Then** `tenants.status='active'` → `'pending_deletion'` 즉시 전이 (AD-3 RLS same-tenant UPDATE)
- **And** `tenants.deletion_requested_at TIMESTAMPTZ NOT NULL` (request ts 기록)
- **And** `tenants.deletion_requested_by_user_id UUID NOT NULL FK→users.id` (owner 추적)
- **And** `tenants.deletion_consent_id UUID NOT NULL FK→deletion_consents.consent_id` (consent link)
- **And** `tenants.deletion_scheduled_for TIMESTAMPTZ NOT NULL` (= deletion_requested_at + 30일)
- **And** 별도 cron `apps.api.jobs.tenant_hard_delete:run` KST 04:00 (UTC 19:00) 일 1회 실행
  - `SELECT * FROM tenants WHERE status='pending_deletion' AND deletion_scheduled_for <= now()`
  - HARD DELETE tenant + related rows (cascade FK chain — products, bom_lines, monthly_input_periods, monthly_input_rows, fiscal_period_snapshots, fiscal_periods, tenant_backups, deletion_consents, ai_documents, input_drafts, m2_user_invitations)
  - `audit_logs`는 HARD DELETE 대상 외 (AD-2 INSERT-only invariant 보존 — 5년 별도 보존 NFR4 2절)
  - `tenant_hard_deleted` audit emit BEFORE DELETE (CR 1.1 invariant — `target_id=tenant_id` 보존)
- **And** `deletion_consents` row AES-256-GCM 암호화 (CR 12-1 L2 lazy wrapper pattern, `key_id=DEFAULT_KEY_ID, aad=b"deletion_consent"`) — `consent_id` UUID + `tenant_id` UUID + `consent_text_hash` CHAR(64) + `encrypted_consent_text BYTEA` + `consent_checked_at TIMESTAMPTZ` + `consent_ip INET NULL` (audit trace)

### AC #4 — 동의 체크 + 해지 요청 ts audit_logs append (epics.md AC #4 + CR 1.1)

- **Given** 동의 체크, 해지 요청 ts audit_logs append
- **When** `POST /api/v1/account/deletion/request` 성공
- **Then** `audit_logs` 2 row append:
  - Row 1: `action_class='ACCOUNT_DELETION'`, `action='deletion_requested'`, `target_id=tenant_id`, `actor_id=user_id`, `trace_id=request_trace_id`
  - Row 2: `action_class='ACCOUNT_DELETION'`, `action='deletion_consent_given'`, `target_id=consent_id`, `actor_id=user_id`, `trace_id=request_trace_id`
- **And** `deletion_cancelled` action (cancel_deletion route 시) + `deletion_anonymized` action (cron anonymization 시) + `tenant_hard_deleted` action + `deletion_failed` action + `deletion_2fa_failed` action + `two_factor_verified` action (CR 12-5 L3 audit trace) = **8 audit actions 신규**
- **And** AD-2 invariant: `audit_logs` INSERT-only preserved — Alembic 0025 trigger 0 신규 (기존 0001 trigger 적용)
- **And** 3-way drift detector: `tests/integration/test_audit_action_consistency.py` extension — `ACCOUNT_DELETION` 8 values 정합 (registry ↔ DB CHECK (no-op for audit_logs) ↔ call sites)
- **And** 5-year retention 보존: `audit_logs.deleted_at TIMESTAMPTZ NULL` + 5-year job (현재 honestly DEFER) — 12-3 atomic wire는 `audit_logs` row hard-delete 0건 보장

### AC #5 — Owner-only role gate (AD-10)

- **Given** AD-10 4-role: owner / member / viewer / consultant_proxy
- **When** `POST /api/v1/account/deletion/request` + `POST /api/v1/account/deletion/cancel` + `POST /api/v1/account/deletion/challenge-token` + `GET /api/v1/account/deletion/status` 호출
- **Then** `owner` → 200 (challenge-token 발급 / 요청 / 취소 / 상태 조회 허용)
- **And** `member` / `viewer` / `consultant_proxy` → 403 FORBIDDEN_ROLE (M2 진입 권한 ≠ 계정 해지 권한)
- **And** `tenants.status='pending_deletion'` 상태에서 신규 2FA setup/disable 요청 → `AccountDeletionInProgressError` 409 envelope (해지 진행 중 mutation 거부)
- **And** `tenants.status='deleted'` 상태에서 모든 호출 → `AccountAlreadyDeletedError` 410 envelope (gone)
- **And** 12-1 self-enrollment `require_any_role("owner","member")` / 12-2 backup `require_role("owner")`와 대조 — **owner-only 일관 + NFR7 2FA 추가 가드**

### AC #6 — 2FA challenge token + verify_totp_challenge 3-layer defense (CR 12-5 L3 + NFR7)

- **Given** 해지 = destructive endpoint, sensitive token minting
- **When** `POST /api/v1/account/deletion/challenge-token` → `POST /api/v1/account/deletion/request` 2-step
- **Then** `POST /api/v1/account/deletion/challenge-token`:
  - Request: `DeletionChallengeTokenRequest(current_code: str)` — TOTP 6-digit (12-1 P-06 pattern)
  - Response: `DeletionChallengeTokenResponse(challenge_token: str, expires_at: datetime)` — short-lived JWT
  - PyJWT `verify_exp=False` (CR 12-1 L1 deterministic testability, expires_at 명시적 check)
  - Layer 1: `require_role("owner")` + 2FA setup verified check
  - Layer 2: `verify_totp_code(user, current_code)` + lockout check (5회 실패 시 429, 12-1 pattern)
  - Layer 3: `two_factor_verified` audit emit (CR 1.1 BEFORE challenge_token mint)
- **And** `POST /api/v1/account/deletion/request`:
  - Request: `DeletionRequestRequest(challenge_token: str, consent_checked: bool, consent_text: str)`
  - Layer 1: `require_role("owner")` + Bearer auth + challenge_token decode (PyJWT verify_exp=False + expires_at check)
  - Layer 2: `verify_totp_challenge(token, user)` delegation (12-1 P-06 verify_totp_challenge service reuse)
  - Layer 3: `deletion_requested` audit emit BEFORE state transition (CR 1.1 invariant)
- **And** `verify_totp_challenge` service 12-1 P-06 pattern reuse — `packages/services/m12_account/two_factor_gate.py` extension (NOT new service module — kernel SSOT reference per CR 12-5 L1)
- **And** `M12TwoFactorRequiredError` + `M12TwoFactorInvalidError` + `M12TwoFactorLockoutError` 3 envelope handlers reuse (12-1 wire)

### AC #7 — NFR6 AES-256-GCM consent_text encryption + tenants.status RLS 0015 + capability v1.15 (AD-2·3·9·10 + NFR6 + CR 12-1 L2)

- **Given** AD-3 RLS multi-tenancy + AD-9 Seoul tenure + AD-10 4-role + NFR6 AES-256-GCM
- **When** 12-3 Alembic 0025 + RLS 0015 wire
- **Then** `apps/api/alembic/versions/0025_tenants_deletion_status.py` — `tenants` table EXTENSION:
  - `status VARCHAR(16) NOT NULL DEFAULT 'active'` + CHECK `status IN ('active', 'pending_deletion', 'deleted')`
  - `deletion_requested_at TIMESTAMPTZ NULL`
  - `deletion_requested_by_user_id UUID NULL FK→users.id SET NULL`
  - `deletion_consent_id UUID NULL FK→deletion_consents.consent_id SET NULL`
  - `deletion_scheduled_for TIMESTAMPTZ NULL` (= deletion_requested_at + 30일)
  - Index: `ix_tenants_status_pending` on `(status, deletion_scheduled_for) WHERE status='pending_deletion'`
- **And** `apps/api/alembic/versions/0025_tenants_deletion_status.py` — `deletion_consents` table NEW:
  - `consent_id UUID PK dflt uuid.uuid4` (v4, AD-15 tenant_id v4 supersede)
  - `tenant_id UUID NOT NULL FK→tenants.id CASCADE`
  - `consent_text_hash CHAR(64) NOT NULL` (sha256 of consent text — plaintext NEVER stored)
  - `encrypted_consent_text BYTEA NOT NULL` (AES-256-GCM ciphertext, CR 12-1 L2 lazy wrapper)
  - `consent_checked_at TIMESTAMPTZ NOT NULL`
  - `consent_checked_by_user_id UUID NOT NULL FK→users.id`
  - `consent_ip INET NULL` (audit trace, NULL if RSC server-side)
  - `consent_user_agent VARCHAR(512) NULL`
  - Index: `ix_deletion_consents_tenant` on `(tenant_id, consent_checked_at DESC)`
- **And** `supabase/policies/0015_tenants_deletion_rls.sql` — 6-policy split:
  - `tenants_select_same_tenant` SELECT
  - `tenants_select_owner` SELECT (owner role, AD-10)
  - `tenants_update_forbidden_owner_only` UPDATE (owner only, status='active' → 'pending_deletion' 만 허용)
  - `tenants_update_pending_to_active` UPDATE (cancel_deletion route 시 pending_deletion → active 복귀)
  - `tenants_delete_forbidden` DELETE (no rows — fail-closed; cron bypass via service_role)
  - `deletion_consents_select_owner` SELECT (owner only)
  - `deletion_consents_insert_owner` INSERT (owner only)
  - `deletion_consents_update_forbidden` UPDATE
  - `deletion_consents_delete_forbidden` DELETE
- **And** `docs/capability-matrix.md` v1.15 — `Capability.ACCOUNT_DELETION` 신규 (industry-agnostic, 12-1 L4 precedent — "계정 해지는 tenant-level security baseline"). CR 12-1 L4 패턴: documented but **enforced in 1 route** (request_deletion only). cancel_deletion + challenge-token + status는 `require_role("owner")` 만 적용.
- **And** `tests/integration/test_capability_matrix_v1_15_drift.py` 신규 — registry ↔ capability-matrix.md ↔ 4 industries 정합

### AC #8 — JSON schema versioning + AD-2 audit-first invariant + cross-language parity (epics.md + AD-2 + CR 12-5 L4)

- **Given** 다운로드 envelope + audit-first invariant + cross-language parity (12-5 D-13 pattern)
- **When** 12-3 wire
- **Then** `deletion_envelope` schema versioning:
  - top-level: `{schema_version: "1.0", envelope_type: "account_deletion", tenant_id: UUID, status: "pending_deletion", deletion_requested_at: ISO-8601 UTC, deletion_scheduled_for: ISO-8601 UTC, retention_days: 30, consent_id: UUID}`
  - `audit_logs.payload` JSONB envelope (CR 12-5 D-15 in-place mutation NOT applicable — INSERT-only)
  - envelope keys 9종 고정
- **And** AD-2 INSERT-only invariant 강제 (AC #4에서 보장):
  - `tenants` UPDATE는 service role로만 (cron cancel + status FSM만)
  - `audit_logs` INSERT-only (0001 trigger, 12-3 신규 trigger 0)
  - `deletion_consents` INSERT-only (RLS UPDATE/DELETE forbidden)
- **And** cross-language parity 정합 (CR 12-5 L4):
  - `packages/services/m12_account/account_deletion.py` pure kernel (status FSM + consent envelope + retention_days constant)
  - `apps/web/lib/m12-account-deletion.ts` TS mirror (ko-KR.json SSOT + envelope constants)
  - `tests/integration/test_m12_account_deletion_cross_language_drift.py` (NEW, 12-5 D-13 pattern) — parse Python ↔ parse TS 8 vector labels + input tuples + output fields 정합
- **And** `_to_deletion_state(tenant)` ORM→kernel boundary conversion (CR 12-1 L3 pattern, 12-1 `_to_totp_state` precedent)

## Tasks / Subtasks (atomic wire)

### Task 1 — Pure kernel (status FSM + consent envelope + retention_days constant)

- **AC**: #3, #4, #8
- **파일**: `packages/services/m12_account/account_deletion.py` (NEW, ~250 lines)
- **subtasks**:
  - [ ] 1.1 STDIN-only: `import hashlib, uuid, datetime, enum` (no DB, no clock, no random — pure kernel AD-11)
  - [ ] 1.2 `class TenantDeletionStatus(str, Enum)`: `ACTIVE = "active"`, `PENDING_DELETION = "pending_deletion"`, `DELETED = "deleted"` (3-value)
  - [ ] 1.3 `RETENTION_DAYS: Final[int] = 30` (MVP fixed, configurable deferred)
  - [ ] 1.4 `def compute_deletion_scheduled_for(deletion_requested_at: datetime) -> datetime`: return `deletion_requested_at + timedelta(days=RETENTION_DAYS)`
  - [ ] 1.5 `def build_deletion_envelope(*, tenant_id: UUID, status: TenantDeletionStatus, deletion_requested_at: datetime, deletion_scheduled_for: datetime, consent_id: UUID) -> dict`: envelope builder (deterministic key order)
  - [ ] 1.6 `def compute_consent_hash(consent_text: str) -> str`: `hashlib.sha256(consent_text.encode("utf-8")).hexdigest()` 결정론 digest
  - [ ] 1.7 `def validate_consent_text(consent_text: str) -> bool`: length 20-500 + ko-KR regex pattern match (12-1 bcrypt recovery codes precedent)
  - [ ] 1.8 `def can_transition_status(current: TenantDeletionStatus, target: TenantDeletionStatus) -> bool`: FSM transitions (active → pending_deletion ✅, pending_deletion → active ✅, pending_deletion → deleted ✅, others ❌)
  - [ ] 1.9 `Korean SSOT` 상수 5개: `DELETION_MODAL_TITLE_KO`, `DELETION_RETENTION_DAYS_LABEL_KO`, `DELETION_CONSENT_LABEL_KO`, etc. (Final[str] 타입)
  - [ ] 1.10 `Typed exceptions` 5개 정의 (services layer에서 raise):
    - `AccountDeletionNotOwnerError` (403, require_role failed)
    - `AccountDeletionInProgressError` (409, status='pending_deletion' mutation 거부)
    - `AccountAlreadyDeletedError` (410, status='deleted' 호출)
    - `DeletionConsentRequiredError` (422, consent_checked=false)
    - `DeletionConsentTextInvalidError` (422, validate_consent_text failed)
- **tests**: `tests/services/m12_account/test_account_deletion.py` (NEW, 25+ cases):
  - `TenantDeletionStatus` enum 3 values
  - `RETENTION_DAYS = 30` constant
  - `compute_deletion_scheduled_for` +30 days 정확
  - `build_deletion_envelope` determinism (same input → same envelope)
  - `compute_consent_hash` 결정론 (RFC test vector)
  - `validate_consent_text` regex match
  - `can_transition_status` FSM 9 cases (3x3 grid)
  - 5 typed exception instances

### Task 2 — Service layer (DeletionService + 2FA challenge integration + audit emit)

- **AC**: #2, #3, #4, #6
- **파일**: `apps/api/modules/m12_account/services/account_deletion_service.py` (NEW, ~450 lines)
- **subtasks**:
  - [ ] 2.1 `class DeletionService` with `__init__(session, *, tenant_id, actor_id, trace_id)` (12-2 BackupExportService precedent)
  - [ ] 2.2 `async def issue_deletion_challenge_token(self, *, current_code: str) -> DeletionChallengeTokenResult`:
    - Layer 1: `require_role("owner")` (route layer, but service re-checks)
    - Layer 2: `verify_totp_code(user, current_code)` (12-1 `two_factor_gate.py:verify_totp_code` delegation)
    - Layer 2b: Lockout check (5회 실패 시 `M12TwoFactorLockoutError`, 12-1 pattern)
    - Layer 3: `two_factor_verified` audit emit BEFORE challenge_token mint (CR 1.1)
    - Mint JWT challenge_token (PyJWT `verify_exp=False`, expires_at = now + 5분, CR 12-1 L1)
  - [ ] 2.3 `async def request_deletion(self, *, challenge_token: str, consent_checked: bool, consent_text: str) -> DeletionResult`:
    - `consent_checked == False` → `DeletionConsentRequiredError` raise (Layer 3 audit-first)
    - `validate_consent_text(consent_text) == False` → `DeletionConsentTextInvalidError` raise (Layer 3 audit-first)
    - `verify_totp_challenge(token, user)` delegation (12-1 P-06 pattern, Layer 2 re-verify)
    - `can_transition_status(status, 'pending_deletion') == False` → `AccountDeletionInProgressError` raise
    - INSERT `deletion_consents` row (AES-256-GCM `encrypted_consent_text` via CR 12-1 L2 lazy wrapper)
    - UPDATE `tenants.status='pending_deletion'` + 4 NEW columns (RLS 0015 owner-only UPDATE)
    - `deletion_requested` audit emit + `deletion_consent_given` audit emit (CR 1.1)
    - Return DeletionResult
  - [ ] 2.4 `async def cancel_deletion(self) -> DeletionResult`:
    - `tenants.status='pending_deletion'`만 cancel 가능 (FSM can_transition_status)
    - UPDATE `tenants.status='active'` + NULL 4 columns (RLS 0015 pending_to_active)
    - `deletion_cancelled` audit emit (CR 1.1)
    - deletion_consents row UPDATE 0 (INSERT-only RLS)
  - [ ] 2.5 `async def get_deletion_status(self) -> DeletionStatusResponse`:
    - SELECT `tenants` + `deletion_consents` join (RLS same-tenant)
    - Return status + scheduled_for + days_remaining + consent_id
  - [ ] 2.6 `async def hard_delete_expired_tenants(self, *, cutoff: datetime) -> HardDeleteResult`:
    - SELECT `tenants WHERE status='pending_deletion' AND deletion_scheduled_for <= cutoff`
    - For each tenant: cascade DELETE products, bom_lines, monthly_input_periods, monthly_input_rows, fiscal_period_snapshots, fiscal_periods, tenant_backups, deletion_consents, ai_documents, input_drafts, m2_user_invitations
    - `audit_logs` row HARD DELETE 0 (AD-2 INSERT-only invariant, NFR4 5년 보존)
    - `tenant_hard_deleted` audit emit (target_id=tenant_id, CR 1.1)
    - Soft-fail: any exception → `deletion_failed` audit emit + continue to next tenant
  - [ ] 2.7 `async def run_hard_delete_cron(self, *, now: datetime | None = None) -> HardDeleteResultAsync`:
    - `hard_delete_expired_tenants(cutoff=now)` wrapper for cron entry point
  - [ ] 2.8 Audit-first guard: `try/except` around `emit_audit_typed` → `AccountDeletionAuditEmitError` (12-4 P-09 precedent)
  - [ ] 2.9 Typed exception 10개 신규 (Task 1.10 5 + 추가 5):
    - `M12TwoFactorRequiredError` (403, 12-1 reuse via import)
    - `M12TwoFactorInvalidError` (401, 12-1 reuse via import)
    - `M12TwoFactorLockoutError` (429, 12-1 reuse via import)
    - `DeletionChallengeTokenInvalidError` (401, PyJWT decode failed)
    - `DeletionChallengeTokenExpiredError` (401, expires_at < now)
    - `DeletionConsentEncryptionError` (500, AES-256-GCM failed)
    - `DeletionConsentDecryptionError` (500, AES-256-GCM failed)
    - `AccountDeletionAuditEmitError` (503, audit-first guard failed)
    - `AccountDeletionServiceError` (base, 500)
    - `AccountDeletionHardDeleteError` (500, cron hard-delete failed)
- **imports**: `from apps.api.core.audit_action import ActionClass, emit_audit_typed` (ACCOUNT_DELETION class), `from packages.services.m12_account.two_factor_gate import verify_totp_code, verify_totp_challenge` (12-1 SSOT kernel, CR 12-5 L1 reuse pattern)
- **tests**: `tests/api/m12_account/test_account_deletion_service.py` (NEW, 20+ cases):
  - issue_challenge_token happy path (TOTP verify → token mint)
  - issue_challenge_token invalid TOTP → audit-first emit BEFORE raise
  - request_deletion consent_checked=false → DeletionConsentRequiredError + audit
  - request_deletion status FSM 거부 → AccountDeletionInProgressError + audit
  - request_deletion happy path (status FSM transition + 2 audit rows)
  - cancel_deletion happy path (status FSM revert)
  - get_deletion_status days_remaining 정확
  - hard_delete_expired_tenants N tenants expired → cascade + tenant_hard_deleted N rows
  - hard_delete_expired_tenants audit_logs NOT deleted (AD-2 invariant)
  - 10 typed exception mapping

### Task 3 — Cron jobs (tenant_hard_delete)

- **AC**: #3
- **파일**: `apps/api/jobs/tenant_hard_delete.py` (NEW, ~100 lines)
- **subtasks**:
  - [ ] 3.1 `tenant_hard_delete.py::run(*, now: datetime | None = None) -> HardDeleteResultAsync` — `document_retention.py:51-83` precedent 그대로
  - [ ] 3.2 header docstring: "Railway cron: schedule daily 04:00 KST (UTC 19:00) — outside peak. Failure behavior: any exception logged + Railway Slack alert + `deletion_failed` audit emit."
  - [ ] 3.3 try/except → `deletion_failed` audit emit (ACCOUNT_DELETION, action=`deletion_failed`) BEFORE raise (CR 1.1 audit-first)
  - [ ] 3.4 Session lazy pattern (Story 0.2): `session_gen = get_session(); session = await session_gen.__anext__()`
  - [ ] 3.5 `try/except` per-tenant soft-fail (one tenant fail → continue next, audit emit for failed + tenant_hard_deleted for succeeded)
  - [ ] 3.6 `apps/api/jobs/__init__.py` docstring 갱신 — 3 jobs 추가 (backup_daily 02:00 + backup_retention 03:00 + tenant_hard_delete 04:00 KST)
- **tests**: `tests/api/jobs/test_tenant_hard_delete.py` (NEW, 8 cases):
  - cron entry import path (`apps.api.jobs.tenant_hard_delete:run`)
  - audit_failed on exception (try/except BEFORE raise)
  - per-tenant soft-fail (1 fail + 1 success → 1 deletion_failed + 1 tenant_hard_deleted audit rows)
  - audit_logs NOT deleted (cascade DELETE 명시적 exclude)
  - timezone KST/UTC conversion (now=KST 04:00 → expected UTC 19:00)
  - 30일 미만 tenants NOT deleted (deletion_scheduled_for > now → SKIP)

### Task 4 — HTTP routes extension (4 routes)

- **AC**: #2, #5, #6
- **파일**: `apps/api/modules/m12_account/handlers.py` (EXTENSION, +~200 lines)
- **subtasks**:
  - [ ] 4.1 Pydantic request schemas inline (no `schemas.py`, 12-4 convention): `DeletionChallengeTokenRequest(current_code: str)`, `DeletionRequestRequest(challenge_token: str, consent_checked: bool, consent_text: str)` (model_config forbid extra)
  - [ ] 4.2 Response schemas: `DeletionChallengeTokenResponse(challenge_token, expires_at)`, `DeletionResponse(tenant_id, status, deletion_requested_at, deletion_scheduled_for, consent_id, days_remaining)`, `DeletionStatusResponse(...)`
  - [ ] 4.3 `router.post("/account/deletion/challenge-token", ...)` — Layer 1 require_role("owner") + 2FA setup verified check
  - [ ] 4.4 `router.post("/account/deletion/request", ...)` — Layer 1 require_role("owner") + Bearer + challenge_token decode (PyJWT verify_exp=False + expires_at check)
  - [ ] 4.5 `router.post("/account/deletion/cancel", ...)` — Layer 1 require_role("owner")
  - [ ] 4.6 `router.get("/account/deletion/status", ...)` — Layer 1 require_role("owner")
  - [ ] 4.7 `_resolve_trace_id` 재사용 (handlers.py:84-98)
  - [ ] 4.8 routes summary docstring 갱신: 12 → 16 routes (+4)
  - [ ] 4.9 **Capability gate: ACCOUNT_DELETION (industry-agnostic) ONLY on `request_deletion`** route — cancel + challenge-token + status는 `require_role("owner")` 만 (CR 12-1 L4 precedent — 12-2 BACKUP_EXPORT capability 의도적 부재 패턴 + 12-1 TWO_FACTOR_AUTH capability 모든 route 적용 차이)
  - [ ] 4.10 TwoFactorSetupForm.tsx 검증: 2FA 미설정 시 request_deletion route 진입 시 403 (M12TwoFactorRequiredError envelope) → UI는 `/account/security`로 redirect CTA 표시
- **tests**: `tests/api/m12_account/test_deletion_handlers_route_shape.py` (NEW, 16 cases):
  - 4 routes path + method
  - role gate (owner allow, member/viewer/consultant_proxy deny)
  - 2FA 미설정 → M12TwoFactorRequiredError 403
  - 2FA invalid TOTP → M12TwoFactorInvalidError 401
  - 5회 실패 → M12TwoFactorLockoutError 429
  - consent_checked=false → DeletionConsentRequiredError 422
  - response shape (DeletionResponse, days_remaining calc)
  - 401 on missing/invalid challenge_token
  - 409 on status='pending_deletion' already (AccountDeletionInProgressError)
  - 410 on status='deleted' (AccountAlreadyDeletedError)

### Task 5 — Alembic 0025 + RLS 0015 + audit_action 8 values + capability v1.15

- **AC**: #4, #7
- **파일**:
  - `apps/api/alembic/versions/0025_tenants_deletion_status.py` (NEW, ~250 lines)
  - `supabase/policies/0015_tenants_deletion_rls.sql` (NEW, ~120 lines)
  - `apps/api/core/audit_action.py` (EXTENSION, +8 lines)
  - `apps/api/core/capability.py` (EXTENSION, +1 entry)
  - `docs/capability-matrix.md` (EXTENSION, +1 entry)
  - `tests/architecture/test_api_calls_only_ports.py` (EXTENSION, +1 entry in ALLOWED_SERVICE_SUBMODULES)
- **subtasks**:
  - [ ] 5.1 Alembic 0025 — `tenants` table EXTENSION (6 columns):
    - `status VARCHAR(16) NOT NULL DEFAULT 'active'` + CHECK `status IN ('active', 'pending_deletion', 'deleted')`
    - `deletion_requested_at TIMESTAMPTZ NULL`
    - `deletion_requested_by_user_id UUID NULL FK→users.id SET NULL`
    - `deletion_consent_id UUID NULL FK→deletion_consents.consent_id SET NULL`
    - `deletion_scheduled_for TIMESTAMPTZ NULL`
    - `tenants_deletion_consent_id_fkey` FK constraint name explicit
  - [ ] 5.2 Indexes:
    - `ix_tenants_status_pending` on `(status, deletion_scheduled_for) WHERE status='pending_deletion'` — cron lookup
  - [ ] 5.3 2 COMMENT (status / deletion_scheduled_for) — NFR4 contract
  - [ ] 5.4 Alembic 0025 — `deletion_consents` table NEW (9 columns):
    - `consent_id UUID PK dflt uuid.uuid4` (v4)
    - `tenant_id UUID NOT NULL FK→tenants.id CASCADE`
    - `consent_text_hash CHAR(64) NOT NULL` (sha256, plaintext NEVER stored)
    - `encrypted_consent_text BYTEA NOT NULL` (AES-256-GCM ciphertext, CR 12-1 L2)
    - `consent_checked_at TIMESTAMPTZ NOT NULL`
    - `consent_checked_by_user_id UUID NOT NULL FK→users.id`
    - `consent_ip INET NULL` (audit trace)
    - `consent_user_agent VARCHAR(512) NULL`
    - Index: `ix_deletion_consents_tenant` on `(tenant_id, consent_checked_at DESC)`
  - [ ] 5.5 RLS 0015 — 9-policy split (precedent 0013 template):
    - `tenants_select_same_tenant` SELECT
    - `tenants_select_owner` SELECT (owner role)
    - `tenants_update_forbidden_owner_only` UPDATE (owner only, status='active' → 'pending_deletion' 만 허용 via service role)
    - `tenants_update_pending_to_active` UPDATE (cancel_deletion route 시 pending_deletion → active 복귀)
    - `tenants_delete_forbidden` DELETE (no rows — fail-closed; cron bypass via service_role)
    - `deletion_consents_select_owner` SELECT (owner only)
    - `deletion_consents_insert_owner` INSERT (owner only)
    - `deletion_consents_update_forbidden` UPDATE (no rows)
    - `deletion_consents_delete_forbidden` DELETE (no rows)
  - [ ] 5.6 `apps/api/core/audit_action.py`:
    - line 66에 `ACCOUNT_BACKUP` 뒤 line 67에 `ACCOUNT_DELETION = "account_deletion"` append
    - `AccountDeletionAction` Literal 정의: `"deletion_requested", "deletion_consent_given", "deletion_cancelled", "deletion_anonymized", "tenant_hard_deleted", "deletion_failed", "deletion_2fa_failed", "two_factor_verified"` (8 values)
    - `AuditAction` union에 `AccountDeletionAction` 추가
    - `_REGISTRY` `ActionClass.ACCOUNT_DELETION` 엔트리: `("audit_logs", frozenset({8 values}))`
    - `__all__`에 `AccountDeletionAction` 추가
  - [ ] 5.7 `Capability.ACCOUNT_DELETION = "account_deletion"` 신규 — **industry-agnostic** (12-1 L4 precedent; 4 industries 모두 grant) — `_INDUSTRY_CAPABILITIES` 4 entries 모두에 `Capability.ACCOUNT_DELETION` 추가
  - [ ] 5.8 `docs/capability-matrix.md` v1.15 갱신: `ACCOUNT_DELETION` row + 4 industries 모두 `allowed=true` + rationale ("owner-only, industry-agnostic, destructive endpoint CR 12-5 L3 3-layer defense")
  - [ ] 5.9 `tests/architecture/test_api_calls_only_ports.py` ALLOWED_SERVICE_SUBMODULES list에 `packages.services.m12_account.account_deletion` 추가 (CR 11-3 D-2 sweep)
  - [ ] 5.10 `tests/api/test_alembic_0025_tenants_deletion.py` (NEW, 14 cases):
    - tenants 6 NEW columns exist
    - tenants CHECK constraint status 3-value
    - tenants index ix_tenants_status_pending
    - deletion_consents 9 columns exist
    - deletion_consents index ix_deletion_consents_tenant
    - downgrade → drop columns + drop table
  - [ ] 5.11 `tests/rls/test_tenants_deletion_rls.py` (NEW, 10 cases):
    - 9-policy rejects cross-tenant SELECT
    - 9-policy rejects non-owner SELECT
    - tenants UPDATE owner-only (active → pending_deletion allowed, other rejected)
    - tenants UPDATE pending_to_active (cancel) allowed
    - tenants DELETE forbidden (AD-3 + cron service_role bypass)
    - deletion_consents INSERT owner-only
    - deletion_consents UPDATE forbidden
    - deletion_consents DELETE forbidden
- **drift detectors**:
  - [ ] 5.12 `tests/integration/test_audit_action_consistency.py` extension — ACCOUNT_DELETION 3-way 정합 (registry ↔ DB CHECK (no-op for audit_logs) ↔ call sites 8)
  - [ ] 5.13 `tests/integration/test_capability_matrix_v1_15_drift.py` (NEW) — registry ↔ capability-matrix.md ↔ 4 industries 정합

### Task 6 — Frontend (page + 3 components + ko-KR.json + sidebar)

- **AC**: #1, #2
- **파일**:
  - `apps/web/app/[locale]/(dashboard)/account/settings/layout.tsx` (NEW, ~20 lines)
  - `apps/web/app/[locale]/(dashboard)/account/settings/page.tsx` (NEW, RSC, ~80 lines)
  - `apps/web/components/m12-account/AccountDeletionModal.tsx` (NEW, Client Component, ~250 lines)
  - `apps/web/components/m12-account/DeletionStatusPanel.tsx` (NEW, Client Component, ~150 lines)
  - `apps/web/components/m12-account/DeletionConsentCheckbox.tsx` (NEW, Client Component, ~80 lines)
  - `apps/web/lib/m12-account-deletion.ts` (NEW TS mirror, ~140 lines)
  - `apps/web/lib/server-api.ts` (EXTENSION, +3 functions: `fetchDeletionStatusServerSide`, `requestDeletionServerSide`, `cancelDeletionServerSide`)
  - `apps/web/messages/ko-KR.json` (EXTENSION, +1 namespace `account_deletion` with ~10 strings)
  - `apps/web/lib/menu-config.ts` (EXTENSION, +1 entry in INDUSTRY_MENU_MAP × 4 industries)
  - `packages/services/m0_onboarding/industry_menu.py` (EXTENSION, +1 entry × 4 industries)
- **subtasks**:
  - [ ] 6.1 `/account/settings` RSC page (12-5 `/account/security` + 12-2 `/account/backup` 패턴):
    - `export const dynamic = "force-dynamic"` line 20
    - `await params;` line 29 (Next 15+ Promise<params>)
    - `cookies()` → `sb-access-token` → `fetchDeletionStatusServerSide(accessToken, traceId)`
    - Fail-closed fallback (CR 11-4 D-005): server-side fetch 실패 시 empty status + viewer role
  - [ ] 6.2 `<AccountDeletionModal>` Client Component:
    - `"use client"` (line 24)
    - `useTranslations("account_deletion")` (line 66)
    - shadcn Dialog 패턴 (12-5 TwoFactorChallengeDialog precedent)
    - 동의 체크박스 + [해지 요청] 버튼 (`disabled={!is_consent_checked || is_requesting}`)
    - [해지 요청] 클릭 → 2FA challenge dialog 자동 open → TOTP code 입력 → `requestDeletionServerSide`
    - `data-testid`, `data-deletion-status`, `data-consent-checked`, `data-challenge-token` (테스트 훅)
  - [ ] 6.3 `<DeletionStatusPanel>` Client Component:
    - `"use client"` (line 24)
    - status='active' → [계정 해지] 버튼 (모달 open)
    - status='pending_deletion' → "30일 후 완전 삭제 (N일 남음)" + [해지 취소] 버튼 + audit_id 표시
    - status='deleted' → "삭제된 계정" + [복구 불가] 안내
    - 2FA 미설정 사용자 → status panel "2FA 설정 필요" 안내 + `/account/security` CTA
  - [ ] 6.4 `<DeletionConsentCheckbox>` Client Component:
    - 체크박스 + 라벨 (ko-KR.json `consent_checkbox_label`)
    - `onCheckedChange` callback (12-5 TwoFactorSetupForm 체크박스 패턴)
    - `data-consent-checked` testid
  - [ ] 6.5 `apps/web/lib/m12-account-deletion.ts` (TS mirror):
    - `DELETION_MODAL_TITLE_KO = "계정 해지"` (mirror Python)
    - `DELETION_RETENTION_DAYS_LABEL_KO = "데이터 보관일수"`
    - `DELETION_CONSENT_LABEL_KO = "본인은 데이터 보존 기간 및 삭제 시점을 이해했으며 동의합니다"`
    - `RETENTION_DAYS = 30 as const`
    - `TENANT_DELETION_STATUS_VALUES = ["active", "pending_deletion", "deleted"] as const`
    - `type TenantDeletionStatus = (typeof TENANT_DELETION_STATUS_VALUES)[number]`
    - `buildDeletionEnvelope(...)` envelope builder (mirror Python determinism)
    - `validateConsentText(consent_text)` regex match (mirror Python)
    - `formatDaysRemaining(days)` → "30일", "1일", "오늘"
  - [ ] 6.6 `apps/web/lib/server-api.ts` 확장:
    - `DeletionStatusServerSideResponse` interface
    - `fetchDeletionStatusServerSide(accessToken, traceId)` → `fetch(${apiBaseUrl()}/api/v1/account/deletion/status)`
    - `requestDeletionServerSide(accessToken, traceId, requestBody)` → fetch POST
    - `cancelDeletionServerSide(accessToken, traceId)` → fetch POST
  - [ ] 6.7 `apps/web/messages/ko-KR.json` namespace `account_deletion`:
    - `modal_title` ("계정 해지")
    - `modal_description` ("계정을 해지하면 30일 후 데이터가 완전히 삭제됩니다.")
    - `retention_days_label` ("데이터 보관일수")
    - `retention_days_value` ("30일")
    - `retention_after_label` ("30일 후 완전 삭제 (audit_logs 별도 5년 보존)")
    - `consent_checkbox_label` ("본인은 데이터 보존 기간 및 삭제 시점을 이해했으며 동의합니다")
    - `button_request` ("해지 요청")
    - `button_cancel` ("취소")
    - `button_cancel_deletion` ("해지 취소")
    - `button_requesting` ("해지 요청 중...")
    - `toast_success_requested` ("해지 요청 완료 — 30일 후 완전 삭제됩니다")
    - `toast_success_cancelled` ("해지 요청 취소 완료")
    - `toast_error_required_2fa` ("2FA 설정이 필요합니다. [설정으로 이동]")
    - `toast_error_forbidden` ("owner 권한 필요")
    - `toast_error_consent_required` ("동의 체크 필요")
    - `toast_error_generic` ("해지 요청 실패")
    - `status_active_label` ("활성")
    - `status_pending_deletion_label` ("해지 진행 중 (N일 남음)")
    - `status_deleted_label` ("삭제됨")
    - `format_days_remaining_30` ("30일 남음")
    - `format_days_remaining_today` ("오늘 삭제 예정")
  - [ ] 6.8 Sidebar entry:
    - `apps/web/lib/menu-config.ts` INDUSTRY_MENU_MAP 4 industries 모두 "계정 보안" + "백업 다운로드" 다음에 "계정 설정" 메뉴 append (또는 "계정 보안" submenu 통합 — 결정 spec 진입 시점에 owner-only 가드 우선)
    - `packages/services/m0_onboarding/industry_menu.py` 4 industries 모두 동일하게 append
    - `tests/integration/test_menu_config_consistency.py` — drift detector가 4 positions × 2 files 정합 강제 (자동 검증)
  - [ ] 6.9 **page.tsx mount MUST actually mount** (CR 11-4 D-001): `<DeletionStatusPanel accessToken={accessToken} ... />` + `<AccountDeletionModal>` 실제 import + render (component file 생성만 금지)
- **tests**:
  - [ ] 6.10 `apps/web/__tests__/lib/m12-account-deletion-parity.test.ts` (NEW, 10 cases):
    - Python ↔ TS mirror 10 vector labels
    - RETENTION_DAYS = 30
    - TENANT_DELETION_STATUS_VALUES tuple
    - buildDeletionEnvelope determinism
    - validateConsentText regex match
    - formatDaysRemaining edge cases (30, 1, 0)
  - [ ] 6.11 `apps/web/__tests__/account-deletion-modal.test.tsx` (NEW, 8 cases):
    - 모달 mount
    - 동의 체크박스 unchecked → [해지 요청] disabled
    - 동의 체크 → [해지 요청] enabled
    - [해지 요청] 클릭 → 2FA challenge dialog open
    - 2FA invalid → toast error
    - 2FA valid → request_deletion 호출 → toast success
    - data-testid / data-deletion-status / data-consent-checked hooks
    - ko-KR.json namespace 정확 일치
  - [ ] 6.12 `apps/web/__tests__/deletion-status-panel.test.tsx` (NEW, 6 cases):
    - status='active' → [계정 해지] 버튼 표시
    - status='pending_deletion' → days_remaining 표시 + [해지 취소] 버튼
    - status='deleted' → "삭제됨" + 복구 불가 안내
    - 2FA 미설정 → "/account/security" CTA 표시
    - [해지 취소] 클릭 → cancel_deletion 호출 → toast success
    - data-testid hooks

### Task 7 — Cross-language drift detector + audit consistency + capability matrix

- **AC**: #4, #7, #8
- **파일**:
  - `tests/integration/test_m12_account_deletion_cross_language_drift.py` (NEW, ~200 lines)
  - `tests/integration/test_m12_account_deletion_kernel_parity.py` (NEW, ~150 lines)
- **subtasks**:
  - [ ] 7.1 `test_m12_account_deletion_cross_language_drift.py` — 12-5 `test_m12_two_factor_gate_cross_language_drift.py` 패턴 (D-13 structural detector):
    - parse Python: `tests/services/m12_account/test_account_deletion.py`
    - parse TS: `apps/web/__tests__/lib/m12-account-deletion-parity.test.ts`
    - 10 vector labels 정합 (parity 1..10)
    - input tuples 정합 (RETENTION_DAYS, TenantDeletionStatus values, validate_consent_text regex, format_days_remaining)
    - 6 key output fields 정합 (envelope keys, status enum, days_remaining format)
  - [ ] 7.2 `test_m12_account_deletion_kernel_parity.py` — 20 pytest cases (12-5 D-PARITY-01 패턴):
    - `build_deletion_envelope` 결정론 (same input → same envelope)
    - `compute_deletion_scheduled_for` +30 days 정확
    - `compute_consent_hash` 결정론 (RFC test vector)
    - `validate_consent_text` regex match
    - `can_transition_status` FSM 9 cases (3x3 grid)
    - `RETENTION_DAYS = 30` constant
    - `_to_deletion_state(tenant)` ORM→kernel boundary conversion (CR 12-1 L3)
    - 5 typed exception instances (Task 1.10)
  - [ ] 7.3 `tests/integration/test_audit_action_consistency.py` extension — ACCOUNT_DELETION 8 values 3-way 정합 (registry vs DB CHECK (no-op for audit_logs) vs call sites 8)
  - [ ] 7.4 `tests/integration/test_capability_matrix_v1_15_drift.py` (NEW) — registry ↔ capability-matrix.md ↔ 4 industries

### Task 8 — Docs + 3중 게이트 final clean

- **AC**: #1-8 종합
- **파일**:
  - `docs/conventions.md` (EXTENSION, +§13 Account Deletion)
  - `docs/architecture-inventory.md` (EXTENSION, m12_account section entry)
  - `docs/account-security-operations.md` (EXTENSION, Account Deletion section)
  - `docs/capability-matrix.md` (EXTENSION, v1.15 entry)
  - `docs/deferred-work.md` (EXTENSION, ## Deferred from: 12-3 — quarterly 5-year audit + configurable retention + NFR7 2FA 진입 gate + Playwright E2E + cross-region replica)
- **subtasks**:
  - [ ] 8.1 `docs/conventions.md` §13 Account Deletion:
    - §13.1 Deletion scope (tenants.status FSM, 3-value enum)
    - §13.2 Cron schedule (KST 04:00 daily tenant_hard_delete)
    - §13.3 Retention policy (30-day fixed; configurable deferred)
    - §13.4 Owner role gate (AD-10) + 2FA challenge (NFR7 + CR 12-5 L3)
    - §13.5 audit_logs 5-year retention (NFR4 2절 + AD-2 INSERT-only)
    - §13.6 Korean SSOT (ko-KR.json + audit_extension)
    - §13.7 AES-256-GCM consent_text encryption (CR 12-1 L2 lazy wrapper)
    - §13.8 cross-language parity (12-5 D-13 pattern)
  - [ ] 8.2 `docs/architecture-inventory.md` m12_account section — 12-3 entry:
    - M12 routes: 16 (was 12)
    - AccountDeletion capability: v1.15 industry-agnostic + owner-only + 2FA challenge
    - ActionClass.ACCOUNT_DELETION: 8 values
    - Alembic 0025: tenants.status 6 NEW columns + deletion_consents 9 columns
    - RLS 0015: 9-policy split (tenants 5 + deletion_consents 4)
    - Cross-references: cron jobs, /jobs/tenant_hard_delete, /services/account_deletion_service
  - [ ] 8.3 `docs/account-security-operations.md` — Account Deletion section:
    - tenants.status FSM diagram (active → pending_deletion → deleted)
    - 30-day retention rationale (NFR4)
    - 5-year audit_logs retention (NFR4 2절)
    - 2FA challenge token minting flow (NFR7 + CR 12-5 L3)
    - AES-256-GCM consent encryption (NFR6 + CR 12-1 L2)
    - Hard-delete cascade chain (audit_logs 명시적 exclude)
  - [ ] 8.4 `docs/capability-matrix.md` v1.15:
    - `ACCOUNT_DELETION` row with rationale ("owner-only, industry-agnostic, destructive endpoint CR 12-5 L3 3-layer defense")
    - 4 industries 모두 `allowed=true`
    - `request_deletion` route ONLY (cancel + challenge-token + status는 `require_role("owner")` 만)
  - [ ] 8.5 `docs/deferred-work.md` ## Deferred from: 12-3:
    - Quarterly 5-year audit aggregate (NFR4 2절) — `deletion_audit_archived` action은 ActionClass registry placeholder, wire 0건
    - Configurable retention_days (settings aggregate extension) — MVP fixed 30일
    - NFR7 2FA 진입 gate (모든 account mutation 2FA 강제) — 현재 12-1 M2 entry + 12-3 destructive endpoint만 적용
    - Playwright E2E (12-5 T6 패턴) — sprint-scale
    - Cross-region replication — AD-9 disabled
  - [ ] 8.6 3중 게이트 FINAL CLEAN:
    - `ruff check apps/api packages` — 0 NEW errors on 12-3 surface
    - `import-linter` — 2 KEPT 0 broken (ALLOWED_SERVICE_SUBMODULES extension)
    - `pytest tests/api/m12_account tests/services/m12_account tests/integration/test_m12_account_deletion_* tests/rls/test_tenants_deletion_rls.py` — all pass
    - `vitest` (m12-account-deletion + 12-account-deletion cross-language) — all pass
  - [ ] 8.7 `harness-3gates` rerun (Makefile) + SDR MAX 갱신 separate line per CR 11-2 L7 (unambiguous parser match)
  - [ ] 8.8 `CONVENTIONS_LINT` grep sweep (no str/Enum forbidden patterns in 12-3 surface)

## Dev Notes

### Architecture compliance

- **AD-9 Seoul**: `tenants.status` + `deletion_consents` Postgres tables은 Supabase Seoul Postgres에 상주 → AD-9 자동 만족. Storage/bucket Migration 불요. Cross-region replication은 AD-9 disabled.
- **AD-11 dependency direction**: `packages.services.m12_account.account_deletion` (pure kernel) → `apps.api.modules.m12_account.services.account_deletion_service` (service) → `apps.api.modules.m12_account.handlers` (HTTP) → `apps.api.jobs.tenant_hard_delete` (cron). Layer direction strictly forward.
- **AD-2 audit-first + INSERT-only**: `tenants.status` UPDATE는 service role로만 (RLS UPDATE_FORBIDDEN_OWNER_ONLY + cancel_deletion). `deletion_consents` INSERT-only (RLS UPDATE/DELETE forbidden). `audit_logs` INSERT-only preserved (0001 trigger, 12-3 신규 trigger 0). NFR4 5년 audit_logs 보존 = `audit_logs` row hard-delete 0건 보장.
- **AD-3 RLS multi-tenancy**: 9-policy split (tenants 5 + deletion_consents 4). `current_setting('app.tenant_id', true)::uuid` GUC.
- **AD-8 monetary types**: KRW BigInt→string (`default=str`), USD `Decimal` → `default=str` (period_cost.py:153-159 패턴). consent_text는 평문 NEVER 저장 → sha256 hash + AES-256-GCM ciphertext만 저장.
- **AD-10 4-role**: `require_role("owner")` + 2FA challenge token (CR 12-5 L3 destructive endpoint 3-layer defense). viewer/consultant_proxy/member 모두 DENIED.
- **AD-14 banned infra**: Cron only via Railway cron (Celery/Kafka/Redis banned). `apps/api/jobs/` precedent followed.
- **AD-15 §4 error envelope**: 모든 응답/에러 `{code, message_ko, details, trace_id}` SSOT. ko-KR.json 1 NEW namespace `account_deletion`.
- **AD-15 §1 naming**: snake_case DB/Python, kebab-case routes, PascalCase TS. `account/deletion` route (12-5 `account/2fa` + 12-2 `account/backups` 패턴).
- **AD-15 §2 time**: ISO-8601 UTC 저장, KST 표시. `deletion_requested_at` + `deletion_scheduled_for` 모두 TIMESTAMPTZ UTC.
- **AD-15 §3 identity**: `tenant_id` UUID v4 (AD-15 supersede variance), `consent_id` UUID v4 (audit_logs FK-less pattern), `deletion_requested_by_user_id` UUID v4 FK→users.id.
- **AD-2 audit-first**: 8 audit actions 모두 mutation 전 emit (CR 1.1 pattern). `deletion_failed` + `deletion_2fa_failed` + `tenant_hard_deleted` 모두 try/except에서 raise 직전 emit.

### Library framework

- **의존성 0**: STACK_PIN.yaml 변경 없음. Supabase Postgres (이미 pinned) + stdlib (hashlib, datetime, enum) + SQLAlchemy 2.0.36 (pinned) + Pydantic 2.11.9 (pinned) + FastAPI 0.139.2 (pinned) + structlog 26.1.0 (notes, 12-5 도입) + PyJWT (12-1 도입, challenge_token minting).
- **NO new SDK**: `supabase` 2.10.0 (pinned) 사용 NO. Storage API 호출 0건. `@supabase/storage-js` 도입 0.
- **NO pgmq / pg_cron / celery / apscheduler**: 외부 scheduler (Railway cron) only. `document_retention.py:51-83` precedent.

### File structure

- **Pure kernel**: `packages/services/m12_account/account_deletion.py` (NEW, ~250 lines) — stdlib-only, no DB, no clock, no random.
- **Service**: `apps/api/modules/m12_account/services/account_deletion_service.py` (NEW, ~450 lines) — DB I/O + audit emit + 2FA challenge delegation.
- **HTTP**: `apps/api/modules/m12_account/handlers.py` (EXTENSION, +~200 lines) — 4 routes 추가.
- **Cron**: `apps/api/jobs/tenant_hard_delete.py` (NEW, ~100 lines).
- **Alembic**: `apps/api/alembic/versions/0025_tenants_deletion_status.py` (NEW, ~250 lines) — tenants 6 NEW columns + deletion_consents 9 columns.
- **RLS**: `supabase/policies/0015_tenants_deletion_rls.sql` (NEW, ~120 lines) — 9-policy split.
- **Audit**: `apps/api/core/audit_action.py` (EXTENSION, +8 lines) — ACCOUNT_DELETION class + 8 values.
- **Capability**: `apps/api/core/capability.py` (EXTENSION, +1 entry) + `docs/capability-matrix.md` (EXTENSION, v1.15).
- **Import-linter**: `tests/architecture/test_api_calls_only_ports.py` (EXTENSION, +1 entry).
- **Frontend**: `apps/web/app/[locale]/(dashboard)/account/settings/{layout,page}.tsx` (NEW) + `apps/web/components/m12-account/{AccountDeletionModal,DeletionStatusPanel,DeletionConsentCheckbox}.tsx` (NEW 3 components) + `apps/web/lib/m12-account-deletion.ts` (NEW TS mirror) + `apps/web/lib/server-api.ts` (EXTENSION, +3 functions).
- **Docs**: `docs/conventions.md` §13 + `docs/architecture-inventory.md` + `docs/account-security-operations.md` + `docs/capability-matrix.md` + `docs/deferred-work.md`.
- **Tests**: 8 NEW test files (kernel + service + cron + handlers + alembic + RLS + parity + drift).

### Testing standards

- **pytest** (def test_*, asyncio.run pattern per CR 4-3): kernel 25+ / service 20+ / cron 8 / handlers 16 / alembic 14 / RLS 10 = 93+ NEW pytest cases.
- **vitest**: TS mirror 10 + AccountDeletionModal 8 + DeletionStatusPanel 6 = 24 NEW vitest cases.
- **drift detector**: structural cross-language parity (pure pytest, 12-5 L4 pattern).
- **3중 게이트**: ruff scoped (0 errors) + import-linter (2 KEPT 0 broken) + pytest (all pass, ~1,648 baseline + 93+ NEW = ~1,741).
- **MAX SDR 갱신**: separate line for unambiguous parser match per CR 11-2 L7.

### Project Structure Notes

- **cj-style 7번째 epic 연속**: 12-3은 12-1 / 12-2 / 12-4 / 12-5 패턴을 그대로 따름 (router 흡수 + capability v1.15 + 9-policy RLS + alembic 0025 + RLS 0015).
- **honest-DEFER discipline 8번째 연속**: 12-3 atomic wire는 30-day rolling sweep까지. quarterly 5-year audit aggregate + configurable retention + NFR7 2FA 진입 gate + Playwright E2E 모두 honestly DEFER.
- **CR 12-5 L3 destructive endpoint 3-layer defense**: request_deletion route = (a) route layer require_role("owner") + 2FA setup verified + (b) service layer verify_totp_challenge delegation + (c) handler layer audit-first emit BEFORE raise.
- **AD-2 INSERT-only 강제**: `audit_logs` 0001 trigger preserved (12-3 신규 trigger 0). `deletion_consents` RLS UPDATE/DELETE forbidden. `tenants` RLS UPDATE owner-only + cancel-only.
- **cross-language parity**: pure kernel → service → handlers + TS mirror → drift detector 1 path (12-5 D-13 pattern).
- **Pydantic `model_config = ConfigDict(extra="forbid")`**: 모든 request schema (12-4 convention).
- **`_resolve_trace_id` 재사용**: handlers.py:84-98 (3-tier fallback).
- **DR-005 fallback**: Server-side fetch 실패 시 fail-closed empty status + viewer role (CR 11-4 D-005).
- **Pydantic response schemas inline**: handlers.py (no schemas.py — 12-4 convention).
- **AES-256-GCM lazy wrapper**: `deletion_consents.encrypted_consent_text` BYTEA column (CR 12-1 L2 pattern, 12-1 totp_secret 동일 wrapper 재사용).

### Previous story intelligence

- **12-1 (2FA)**: PyJWT `verify_exp=False` deterministic testability (CR 12-1 L1) + AES-256-GCM lazy wrapper (CR 12-1 L2) + `_to_totp_state(user)` ORM→kernel boundary conversion (CR 12-1 L3) + TWO_FACTOR_AUTH industry-agnostic (CR 12-1 L4). 12-3는 모두 reuse + extend.
- **12-2 (backup)**: Postgres JSONB storage pattern (AD-9 Seoul) + `tenant_backups` INSERT-only (AD-2) + RLS 5-policy split (0014) + capability matrix v1.14 (industry-agnostic, 12-1 L4 precedent) + atomic wire (8 tasks) + honest-DEFER discipline. 12-3은 `tenants.status` FSM + `deletion_consents` INSERT-only + RLS 9-policy split (0015) + capability matrix v1.15.
- **12-4 (carry-over sprint)**: 4 form components pattern + 14 typed exception handlers in main.py. 12-3은 10 typed exceptions + 10 envelope handlers.
- **12-5 (atomic wire + T6 follow-up)**: P-06 TOTP proof pattern (`verify_totp_challenge` delegation) + cross-language drift detector + D-001 page.tsx mount + D-002 ko-KR.json SSOT + D-005 unknown state reject + L3 3-layer TOTP defense (CRITICAL for destructive endpoint) + L4 cross-language drift detector. 12-3은 12-5 패턴 그대로 적용.
- **6-3 (PDF export)**: 6-task 분할 + closing_pdf_export.py + ClosingPdfExportButton.tsx + byte stream download. 12-3은 8-task 분할 + account_deletion.py + AccountDeletionModal.tsx + cascade DELETE.
- **CR 11-3 honest-DEFER**: partial wire 금지. 12-3은 8 tasks atomic wire (no partial).
- **CR 11-4 D-001**: page.tsx mount MUST actually mount. 12-3 verify.
- **CR 11-4 D-002**: ko-KR.json SSOT single file. 12-3 1 NEW namespace 추가.
- **CR 11-4 D-005**: TS mirror unknown state fall-through → reject. 12-3 verify.
- **CR 12-1 L1**: PyJWT verify_exp=False. 12-3 challenge_token mint 동일.
- **CR 12-1 L2**: AES-256-GCM lazy wrapper. 12-3 consent_text 암호화 동일 wrapper 재사용.
- **CR 12-1 L3**: ORM→kernel boundary conversion. 12-3 `_to_deletion_state(tenant)` 동일.
- **CR 12-1 L4**: industry-agnostic security baseline. 12-3 ACCOUNT_DELETION capability 미러.
- **CR 12-5 D-13**: structural cross-language drift detector. 12-3 NEW detector.
- **CR 12-5 D-14**: typed exception main.py envelope handler 등록. 12-3 10 envelope handlers.
- **CR 12-5 L3**: 3-layer TOTP defense for destructive endpoint. 12-3 CRITICAL 적용.
- **CR 12-5 L4**: cross-language drift detector. 12-3 NEW detector.

### Git intelligence

- **Last 3 commits**: `78b2e73` (Story 12.5 T6 follow-up sprint + Epic 12 close-out) + `b7a2522` (12.2 bmad-code-review 3rd sweep chunk 1) + `5fced3b` (12.2 T1~T8 atomic wire).
- **baseline_commit = `78b2e73`**: HEAD at spec creation (2026-08-15).
- **Pattern observed**: 12-1 commit `1004fc0` (T6+T10) → 12-2 commit `5fced3b` (T1~T8 atomic) → 12-4 commit `8735eb5` (carry-over) → 12-5 commits `f6fbf93` / `cccebeb` / `e9582f6` / `42b45fa` / `78b2e73` (T6 follow-up). 12-3 expected 2-3 commits atomic (mirror 12-5 pattern).
- **Atomic wire pattern**: 12-5 used 3 commits (T1+T2 / T3+T4 / T5+T7) + 1 follow-up sprint (T6 + Epic 12 close-out). 12-3 expected 2-3 commits for 8 tasks.

### Latest tech

- **stdlib hashlib**: `hashlib.sha256(consent_text.encode("utf-8")).hexdigest()` — RFC test vector stable.
- **stdlib datetime**: `datetime + timedelta(days=RETENTION_DAYS)` — 12-1 totp_datetime precedent.
- **stdlib enum**: `class TenantDeletionStatus(str, Enum)` — 12-5 TwoFactorSetupForm enum precedent.
- **SQLAlchemy 2.0.36**: `sa.func.inet(client_ip)`, `MutableList.as_mutable(JSONB)` (CR 12-5 D-15 NOT applicable — INSERT-only).
- **Pydantic 2.11.9**: `BaseModel` + `ConfigDict(extra="forbid")` inline.
- **FastAPI 0.139.2**: `APIRouter`, `Depends(require_role("owner"))`, `HTTPException` (12-1 handler pattern).
- **PyJWT**: `jwt.encode(payload, secret, algorithm="HS256")` + `verify_exp=False` (12-1 challenge_token pattern reuse).
- **AES-256-GCM lazy wrapper**: `crypto.encrypt_gcm(plaintext, key_id=DEFAULT_KEY_ID, aad=b"deletion_consent")` (CR 12-1 L2 pattern, 12-1 totp_secret 동일 wrapper 재사용).
- **NO new dependency**: 12-3 wire surface uses already-pinned libraries only.

### References

- epics.md:1211-1222 (Story 12.3 AC verbatim) [Source: _bmad-output/planning-artifacts/epics.md#Story-12.3]
- PRD §F12.3: "해지 요청 시 보관일수 + 삭제 동의 문구 강제 표시" [Source: _bmad-output/planning-artifacts/prd.md#F12.3]
- PRD NFR4: "RPO 24h / RTO 4h / 백업 보관 30일(자동), 1년(분기) / 감사로그 5년 append-only" [Source: _bmad-output/planning-artifacts/prd.md#NFR4]
- PRD NFR6: "저장 AES-256 at rest + KMS 관리" [Source: _bmad-output/planning-artifacts/prd.md#NFR6]
- PRD NFR7: "2FA 강제" [Source: _bmad-output/planning-artifacts/prd.md#NFR7]
- AD-2: "audit_logs are INSERT-only. PostgreSQL BEFORE UPDATE OR DELETE row-level triggers raise append-only violation" [Source: ARCHITECTURE-SPINE.md#AD-2]
- AD-3: "Multi-tenant isolation via Supabase RLS" [Source: ARCHITECTURE-SPINE.md#AD-3]
- AD-9: "tenant data at rest, Auth, Storage, and backups live in Supabase ap-northeast-2 (Seoul)" [Source: ARCHITECTURE-SPINE.md#AD-9]
- AD-10: "Identity & roles" [Source: ARCHITECTURE-SPINE.md#AD-10]
- AD-14: "Celery, Kafka, Redis as a persistent queue... banned" [Source: ARCHITECTURE-SPINE.md#AD-14]
- AD-15 §4 error envelope: `{code, message_ko, details, trace_id}` [Source: docs/conventions.md#§4]
- AD-15 §1 naming: snake_case / kebab-case / PascalCase [Source: docs/conventions.md#§1]
- M12 module pattern: `apps/api/modules/m12_account/` [Source: 12-4-epic-12-carry-over-sprint.md]
- 12-1 P-06 verify_totp_challenge pattern: `packages/services/m12_account/two_factor_gate.py:verify_totp_challenge` [Source: 12-1-two-factor-auth-mandatory-gate.md]
- 12-1 AES-256-GCM lazy wrapper: `apps/api/core/crypto.py` [Source: 12-1-two-factor-auth-mandatory-gate.md]
- 12-1 ORM→kernel boundary: `_to_totp_state(user)` [Source: 12-1-two-factor-auth-mandatory-gate.md]
- 12-2 Postgres JSONB pattern: `apps/api/alembic/versions/0024_tenant_backups.py` [Source: 12-2-daily-auto-backup-json-self-download.md]
- 12-2 RLS 5-policy split: `supabase/policies/0014_tenant_backups_rls.sql` [Source: 12-2-daily-auto-backup-json-self-download.md]
- 12-5 cross-language drift detector: `tests/integration/test_m12_two_factor_gate_cross_language_drift.py` [Source: 12-5-m2-entry-gate-and-account-security-ui.md]
- 12-5 L3 3-layer TOTP defense: destructive endpoint pattern [Source: cr-12-5-lessons.md]
- 12-5 page.tsx mount pattern: `/account/security` RSC [Source: 12-5-m2-entry-gate-and-account-security-ui.md]
- 6-3 PDF export pattern: `apps/api/modules/m4_inventory/handlers.py:849-927` [Source: 6-3-closing-pdf-export.md]
- document_retention cron pattern: `apps/api/jobs/document_retention.py:51-83` [Source: Story 1.3 Task 1.3]
- capability matrix v1.13/v1.14: `Capability.TWO_FACTOR_AUTH` + `Capability.BACKUP_EXPORT` industry-agnostic precedent [Source: docs/capability-matrix.md#v1.13-14]

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
| 2026-08-15 | bmad-create-story spec 진입 done (backlog → ready-for-dev) | (n/a — spec only) | 78b2e73 | (n/a — spec only) |

---

## Spec Decoupling Notes (12-3 next steps)

1. **12-3 dev-story wire**: 8 tasks atomic wire expected in 2-3 commits (mirror 12-5 pattern).
2. **Epic 12 close-out retro**: 12-1 + 12-2 + 12-3 done 후 retro → epic-12 status done 유지 확인 + Epic 12 cj-style 3-story 분할 검증 완료.
3. **Follow-up sprint (per CR 11-3)**: quarterly 5-year audit aggregate + configurable retention + NFR7 2FA 진입 gate + Playwright E2E + cross-region replica (모두 honestly DEFER).
4. **Next epic after 12-3**: Epic 7 진입 (A19 carried-over — inline projection deprecate 코드 제거) OR Epic 1 1-3 완료 (partial — frontend + real SDK + redaction deferred).
5. **CR 12-5 lessons L1-L5 final**: 12-3은 L1 (kernel SSOT reference in parity tests) + L2 (composition priority lock-down) + L3 (3-layer defense CRITICAL destructive endpoint) + L4 (cross-language drift detector NEW) + L5 (honest-DEFER discipline) 모두 적용.