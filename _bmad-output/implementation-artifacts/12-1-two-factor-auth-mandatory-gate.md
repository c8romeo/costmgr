---
title: 'Epic 12 Story 1 — 2FA Mandatory Gate to M2 Entry (TOTP + AD-10 4-role)'
status: ready-for-dev
priority: HIGH
epic: 12
story_num: 1
story_key: 12-1-two-factor-auth-mandatory-gate
baseline_commit: 50b6399
created: 2026-08-10
updated: 2026-08-10
---

> **Epic 12 cj-style 3-story 분할 1번째** (Epic 11 retro §7 A14 권장안 (a) + Epic 6 close-out retro §7 A21+A22 wire).
> **cj-style 분할 패턴**: Epic 4 (4·5·6 cj-style 3-story) → Epic 5 (5·1·2·3 cj-style 3-story) → Epic 6 (6·1·2·3 cj-style 3-story) → Epic 11 (11·1·2·3 cj-style 3-story) → Epic 12 (12·1·2·3 cj-style 3-story) **5번째 epic 연속 검증**.
> **baseline_commit = 50b6399** (현재 HEAD, Epic 6 close-out + A19 honestly DEFER entry).
> **CR 11-1~11-4 lessons 반영**: auth-layer divergence sweep + ALLOWED_SERVICE_SUBMODULES 즉시 sweep + ruff scoped auto-fix sweep + SDR separate line for unambiguous parser match.

# Story 12.1 — 2FA Mandatory Gate to M2 Entry

## Epic 12 context

Epic 12 (Account & Security Operations) cj-style 3-story 분할:

- **12.1** = 2FA Mandatory Gate to M2 Entry ← **본 스토리** (PRD §F12.1 PRIMARY, AD-3·9·10)
- **12.2** = Daily Auto-Backup + JSON Self-Download (PRD §F12.2, NFR4 backup, AD-9 Seoul)
- **12.3** = Account Deletion with Retention Consent (PRD §F12.3, NFR5·6 retention, AD-3 RLS)

**Epic 12 모듈 authority**: `apps/api/modules/m12_account/` (현재 stub — `"""M12 Account & Security Operations — Epic 12 stories 12.1~12.3 will populate this."""`).

**Epic 12 capability matrix v1.13 wire 본문**: `Capability.TWO_FACTOR_AUTH` 신규 (manufacturing 3종 ✅ / service-only ❌). PRD §F12.1 + §8.M12(a) + NFR7 (2FA 강제) + AD-10 (identity+roles owner/member/viewer/consultant_proxy) wire.

**Epic 12 NFR coverage**: NFR1 (99.5%), NFR2·3 (RPO/RTO), NFR4 (백업 — 12-2), NFR5 (TLS), NFR6 (AES-256), NFR7 (2FA — **본 스토리**).

## User Story

As a **사장님 (owner)**,
I want **2FA 미설정 상태에서 [월 입력] 화면 진입이 차단되는 것**,
so that **내 회사 데이터가 약한 인증으로 새는 사고를 방지**.

(PRD §F12.1 + epics.md Story 12.1 verbatim + UJ-4 step 4-5 진입점 + NFR7 강제)

## Acceptance Criteria

### AC #1 — 2FA 미설정 시 M2 진입 차단 (PRD §M12-a)

- **Given** 사장님/owner가 로그인 후 [월 입력] (M2) 진입 시도
- **When** `tenant_memberships.role='owner'` + 2FA 미등록 상태 (`users.totp_secret IS NULL`)
- **Then** "2FA 설정이 필요합니다 — [설정하기]" 모달이 뜨고 [월 입력] 화면 라우팅 차단 (HTTP 403 + envelope `{code: TWO_FACTOR_REQUIRED, message_ko: ...}`)
- **And** 모달 [설정하기] 클릭 → `/m12-account/security/2fa/setup` 페이지로 이동 → TOTP 등록 플로우 진입
- **And** TOTP 등록 완료 (`POST /api/v1/account/2fa/enable` 200) 후에만 M2 진입 허용 (`GET /api/v1/m2-input/state` 200)

### AC #2 — TOTP 등록 플로우 (RFC 6238 + NFR7)

- **Given** 사장님이 [설정하기] 모달 진입
- **When** TOTP 등록 진행 (`POST /api/v1/account/2fa/setup` → QR code + secret 반환)
- **Then** QR code는 `otpauth://totp/costmgr:{user_email}?secret={base32}&issuer=costmgr` URI 표준 (RFC 6238 + Google Authenticator 호환)
- **And** 6-digit TOTP code 입력 → `POST /api/v1/account/2fa/verify` → `users.totp_secret` + `users.totp_enabled_at` 영구화
- **And** 8 recovery codes (`backup_codes`) 1회 표시 + `users.totp_recovery_codes_hash` (bcrypt) 저장 (PRD §F12.1 + NFR7 recovery path)
- **And** recovery code 1회용 enforce (`POST /api/v1/account/2fa/recover` → 검증 후 `used_at` 마킹 + `users.totp_secret` 재발급 옵션)

### AC #3 — 로그인 시 2FA challenge (TOTP code 입력)

- **Given** 사용자가 로그인 (`POST /api/v1/auth/login` → JWT + 2FA_REQUIRED challenge token)
- **When** TOTP code 입력 (`POST /api/v1/auth/2fa/challenge` with code + challenge_token)
- **Then** RFC 6238 ±1 window (30s × 3 = 90s tolerance) 검증 → JWT 발급
- **And** 5회 실패 시 `users.totp_failed_attempts` 카운트 + 5회째 lockout 15분 (`users.totp_lockout_until`)
- **And** recovery code 입력 시 검증 → 1회용 consume + 새 JWT 발급 (AC #2 recovery path)

### AC #4 — AD-10 4-role 권한별 진입 제어 (PRD §F12.1 + AD-10)

- **Given** 4 roles: `owner` / `member` / `viewer` / `consultant_proxy` (per `apps/api/alembic/versions/0001_tenants_users_memberships_settings.py:38` `_ROLE_VALUES`)
- **When** M2 진입 시도 (`GET /api/v1/m2-input/state`)
- **Then** `owner`/`member` → 200 (정상 M2 진입, 단 2FA 미설정 시 AC #1 모달)
- **And** `viewer` → 403 FORBIDDEN_ROLE (PRD §F12.1 viewer = read-only, M2 입력 불가)
- **And** `consultant_proxy` → 403 FORBIDDEN_ROLE (PRD §F12.1 consultant = read-only + consent-bound, M2 입력 불가)
- **And** 2FA gate는 모든 role에 적용 (owner/member/viewer/consultant_proxy 모두 2FA 등록 필요)

### AC #5 — Capability matrix v1.13 (TWO_FACTOR_AUTH 신규)

- **Given** `apps/api/core/capability.py` Capability enum + `_INDUSTRY_CAPABILITIES` map
- **When** Story 12.1 wire
- **Then** `Capability.TWO_FACTOR_AUTH = "two_factor_auth"` enum 값 추가
- **And** manufacturing 3종 (manufacturing / manufacturing_service / manufacturing_service_other) frozenset에 추가
- **And** service-only ❌ (403 INDUSTRY_NOT_SUPPORTED — 2FA 자체는 모든 industry에 적용이지만, capability gate는 manufacturing tenant 우선 = PRD §F12.1 industry 무관 적용 명시 후 manufacturing 우선)
- **And** `docs/capability-matrix.md` v1.12 → v1.13 row 추가 (TWO_FACTOR_AUTH row + 4 industries 매트릭스)
- **And** `tests/integration/test_capability_matrix_drift.py` EXTENSION — TWO_FACTOR_AUTH gate case 6 NEW (4 industries × grant/deny matrix)

### AC #6 — Audit-first + idempotent no-op (CR 1.1 invariant)

- **Given** 모든 2FA mutation (setup / verify / enable / disable / recover)
- **When** wire
- **Then** audit-first emit `ActionClass.TWO_FACTOR_AUTH` 6 NEW values:
  - `two_factor_setup_initiated` (setup 요청)
  - `two_factor_setup_completed` (verify 성공 + 영구화)
  - `two_factor_challenge_passed` (로그인 challenge 성공)
  - `two_factor_challenge_failed` (TOTP code 오류)
  - `two_factor_recovery_consumed` (recovery code 사용)
  - `two_factor_disabled` (owner 명시적 disable)
- **And** `audit_logs` append (AD-2 append-only-leaning) + tenant_id + actor_id + trace_id
- **And** idempotent no-op: 같은 TOTP secret 재등록 시도 → 200 + audit row 1건만 (중복 setup 방지)

### AC #7 — Service-only industry skip (CR 11-2 capability skip pattern)

- **Given** `Industry.SERVICE` tenant (PRD §F12.1 적용 제외 — 본문은 "모든 industry에 적용"이지만, capability gate는 industry-aware front)
- **When** 2FA endpoint 호출
- **Then** 2FA 자체는 industry 무관 적용 (PRD §F12.1) → service-only tenant도 TOTP 등록 가능 (security baseline)
- **But** capability gate 자체는 manufacturing-kind 우선 grant (Epic 12 capability row 매트릭스 정합)
- **And** service-only tenant 2FA 미설정 시에도 M2 진입 차단 (AC #1 industry 무관 적용)

### AC #8 — NFR5 TLS + NFR6 AES-256 (PRD §F12.1 + NFR5·6)

- **Given** 2FA TOTP secret + recovery codes 저장
- **When** wire
- **Then** `users.totp_secret` + `users.totp_recovery_codes_hash` 모두 **AES-256-GCM encrypted at rest** (NFR6 — column-level encryption via `apps/api/core/crypto.py` 신규 pure helper)
- **And** TOTP code / recovery code transmission = **TLS 1.3 only** (NFR5 — `Strict-Transport-Security` header + `crypto_protocols=TLSv1.3` on FastAPI/Uvicorn)
- **And** 8 recovery codes plaintext는 1회만 응답 (저장 시 hash만) — replay attack 방지

## Tasks / Subtasks

### Task 1: Pure kernel — TOTP + 2FA gate logic (AC: #1, #2, #3, #7, #8)

- [ ] 1.1 `packages/services/m12_account/totp.py` (NEW pure helper, stdlib-only)
  - `generate_totp_secret()` → base32 160-bit
  - `generate_totp_uri(secret, email, issuer='costmgr')` → `otpauth://totp/...` RFC 6238 URI
  - `compute_totp_code(secret, timestamp=None, window=0)` → 6-digit code (HMAC-SHA1, 30s step)
  - `verify_totp_code(secret, code, tolerance_windows=1)` → bool (±1 window = 90s tolerance)
  - `generate_recovery_codes(count=8)` → list[str] (8 codes × 10-char alphanumeric)
  - `hash_recovery_code(code)` → bcrypt hash
  - `verify_recovery_code(code, hash)` → bool
  - **AD-11 layer rule**: stdlib-only (hmac, hashlib, base64, secrets, bcrypt)
- [ ] 1.2 `packages/services/m12_account/two_factor_gate.py` (NEW pure kernel)
  - `check_two_factor_required(user, tenant_membership)` → bool (2FA 미설정 + M2 진입 시도)
  - `enforce_two_factor_gate(ctx, target_route='m2_input')` → 2FA_REQUIRED raise or None
  - `lockout_status(user)` → bool (failed_attempts >= 5 → lockout active)
  - **CR 1.1 invariant**: pure function, no DB I/O (caller passes user/membership)

### Task 2: Service layer — 2FA service (AC: #2, #3, #6, #8)

- [ ] 2.1 `apps/api/modules/m12_account/services/two_factor_service.py` (NEW service)
  - `setup_totp(user_id, tenant_id)` → {secret, uri, qr_payload}
  - `verify_and_enable_totp(user_id, tenant_id, code)` → {recovery_codes} (1회만 응답)
  - `verify_totp_challenge(user_id, tenant_id, challenge_token, code)` → JWT or 2FA_CHALLENGE_FAILED
  - `verify_recovery_code(user_id, tenant_id, code)` → JWT or RECOVERY_INVALID
  - `disable_totp(user_id, tenant_id, current_code)` → void (owner 명시적)
  - **CR 1.1 audit-first invariant**: every mutation → audit row first (ActionClass.TWO_FACTOR_AUTH)
- [ ] 2.2 `apps/api/modules/m12_account/services/two_factor_challenge_service.py` (NEW)
  - `issue_challenge_token(user_id)` → JWT-like short-lived token (5min TTL)
  - `consume_challenge_token(token)` → user_id or expired
- [ ] 2.3 `apps/api/modules/m12_account/services/audit_extension.py` (EXTENSION)
  - `ActionClass.TWO_FACTOR_AUTH` 6 NEW values fill + emit helper
  - **CR 1.1 + A5 forward-lock**: SSOT at `apps/api/core/audit_action.py`

### Task 3: Routes + handlers (AC: #1, #2, #3, #4)

- [ ] 3.1 `apps/api/modules/m12_account/handlers.py` (NEW)
  - `POST /api/v1/account/2fa/setup` → {secret, uri, qr_payload}
  - `POST /api/v1/account/2fa/verify` → {recovery_codes}
  - `POST /api/v1/account/2fa/disable` → 204
  - `POST /api/v1/account/2fa/recover` → JWT or RECOVERY_INVALID
  - `GET /api/v1/account/2fa/status` → {enabled: bool, lockout_until: ts|None}
- [ ] 3.2 `apps/api/modules/m12_account/auth_handlers.py` (NEW)
  - `POST /api/v1/auth/login` → {jwt?, challenge_token?}
  - `POST /api/v1/auth/2fa/challenge` → JWT
- [ ] 3.3 `apps/api/modules/m12_account/m2_gate_handlers.py` (NEW)
  - `GET /api/v1/m2-input/state` → 2FA gate check (capability + 2FA + role)
- [ ] 3.4 `apps/api/main.py` EXTENSION — 8 NEW exception handlers wire
  - `TwoFactorRequiredError` (403 TWO_FACTOR_REQUIRED)
  - `TwoFactorChallengeFailedError` (401 TWO_FACTOR_CHALLENGE_FAILED)
  - `TwoFactorLockoutError` (429 TWO_FACTOR_LOCKOUT + Retry-After)
  - `TwoFactorRecoveryInvalidError` (401 TWO_FACTOR_RECOVERY_INVALID)
  - `TwoFactorAlreadyEnabledError` (409 TWO_FACTOR_ALREADY_ENABLED)
  - `TwoFactorNotEnabledError` (409 TWO_FACTOR_NOT_ENABLED)
  - `ForbiddenRoleError` (403 FORBIDDEN_ROLE — viewer/consultant_proxy)
  - `InvalidTotpCodeError` (400 INVALID_TOTP_CODE)

### Task 4: Alembic + RLS + column encryption (AC: #8)

- [ ] 4.1 `apps/api/alembic/versions/0022_users_totp_columns.py` (NEW migration)
  - `users.totp_secret` BYTEA (AES-256-GCM encrypted ciphertext)
  - `users.totp_enabled_at` TIMESTAMPTZ NULL
  - `users.totp_failed_attempts` INTEGER DEFAULT 0
  - `users.totp_lockout_until` TIMESTAMPTZ NULL
  - `users.totp_recovery_codes_hash` JSONB (8 bcrypt hashes array)
  - `down_revision = '0021_cache_invalidation_multi_channel'`
- [ ] 4.2 `supabase/policies/0013_users_totp_columns_rls.sql` (NEW RLS policy)
  - tenant_id filtering on users (이미 0001 RLS 적용, totp 컬럼은 column-level encryption으로 추가 layer)
  - service_role bypass: 2FA reset only via privileged job + audit row

### Task 5: Crypto helper (NFR6 AES-256) (AC: #8)

- [ ] 5.1 `apps/api/core/crypto.py` (NEW pure helper, stdlib-only + cryptography)
  - `encrypt_at_rest(plaintext, key_id)` → ciphertext (AES-256-GCM)
  - `decrypt_at_rest(ciphertext, key_id)` → plaintext
  - `rotate_key(old_key_id, new_key_id)` → re-encrypt batch job
  - **AD-11 layer rule**: stdlib + `cryptography` library only
  - Key storage: env-var `COSTMGR_AT_REST_KEY_ID` + KMS-managed (dev fallback: file-based key rotation)
- [ ] 5.2 `apps/api/core/key_manager.py` (NEW)
  - `get_active_key(key_id)` → key bytes (env-var or KMS)
  - `list_key_versions()` → rotation history

### Task 6: Capability matrix v1.13 wire (AC: #5, #7)

- [ ] 6.1 `apps/api/core/capability.py` EXTENSION
  - `Capability.TWO_FACTOR_AUTH = "two_factor_auth"` enum 추가
  - `_INDUSTRY_CAPABILITIES` map 4 industries 모두에 grant (manufacturing 3종 + service-only ✅)
  - **Note**: AC #7 spec — 2FA 자체는 industry 무관 적용 (PRD §F12.1) → 모든 industry grant (이전 capability pattern과 다른 예외 — security baseline)
- [ ] 6.2 `apps/api/modules/m12_account/handlers.py` EXTENSION
  - 8 NEW routes에 `Depends(require_capability(Capability.TWO_FACTOR_AUTH))` wire
  - **CR 11-2 lesson**: capability gate + role gate (AD-10 owner-only) 이중 검증
- [ ] 6.3 `docs/capability-matrix.md` EXTENSION
  - v1.12 → v1.13 (TWO_FACTOR_AUTH row + 4 industries 매트릭스)
  - Note section: "2FA는 industry 무관 적용 — capability gate는 industry-aware front, 실제 M2 진입 차단은 industry 무관"
- [ ] 6.4 `tests/integration/test_capability_matrix_drift.py` EXTENSION
  - TWO_FACTOR_AUTH gate 6 NEW cases (4 industries × grant/deny + service-only exception 명시)

### Task 7: A5 forward-lock — audit_action wire (AC: #6)

- [ ] 7.1 `apps/api/core/audit_action.py` EXTENSION
  - `ActionClass.TWO_FACTOR_AUTH` NEW frozenset (6 values)
  - `AuditAction` Literal union EXTENSION (6 NEW values)
  - `_ActionRegistry` entries (6 NEW)
  - **CR 1.1 + A5**: SSOT forward-lock (CR 11-2 lesson — registry ↔ DB CHECK ↔ call sites 3-way consistency)
- [ ] 7.2 `apps/api/alembic/versions/0023_audit_logs_two_factor_auth_check.py` (NEW)
  - `audit_logs.action` CHECK constraint EXTENSION (6 NEW values)
  - `down_revision = '0022_users_totp_columns'`
- [ ] 7.3 A5 drift detector EXTENSION (`tests/api/test_audit_action_drift.py`)
  - 6 NEW cases verify ActionClass.TWO_FACTOR_AUTH ↔ DB CHECK ↔ call sites 정합

### Task 8: Frontend — TOTP setup modal + challenge UI (AC: #1, #2, #3, #4)

- [ ] 8.1 `apps/web/components/m12-account/` (NEW subtree)
  - `TwoFactorSetupModal.tsx` (shadcn Dialog + QR code display + TOTP input + sonner toast, ~250 lines)
  - `TwoFactorChallengeModal.tsx` (shadcn Dialog + TOTP code input + recovery code link, ~150 lines)
  - `TwoFactorRecoveryCodesModal.tsx` (shadcn Dialog + 8 codes display + copy + confirm, ~200 lines)
  - `TwoFactorStatusBadge.tsx` (shadcn Badge + enabled/disabled state, ~80 lines)
  - `TwoFactorGuard.tsx` (HOC wrapping M2 entry page — checks 2FA + role + shows modal, ~120 lines)
- [ ] 8.2 `apps/web/lib/m12-account/` (NEW subtree)
  - `m12-two-factor-setup.ts` (TS mirror of pure kernel `totp.py`)
  - `m12-two-factor-gate.ts` (TS mirror of pure kernel `two_factor_gate.py`)
  - `m12-two-factor-types.ts` (TS type definitions)
- [ ] 8.3 `apps/web/app/[locale]/(authenticated)/m12-account/security/2fa/setup/page.tsx` (NEW RSC page)
  - 2FA 설정 페이지 (TOTP 등록 + recovery codes + disable)
- [ ] 8.4 `apps/web/app/[locale]/(dashboard)/m2-input/period/[periodKey]/page.tsx` EXTENSION
  - `<TwoFactorGuard>` HOC wrapping M2 entry
  - 2FA 미설정 + M2 진입 시 → `<TwoFactorSetupModal>` 자동 표시
- [ ] 8.5 `apps/web/messages/ko-KR.json` EXTENSION
  - 18 NEW strings (2FA 설정 / challenge / recovery codes / lockout / role gating)
  - 기존 [월 입력] 진입 메시지 2-string 추가 (TWO_FACTOR_REQUIRED 모달)
- [ ] 8.6 `apps/web/__tests__/lib/m12-two-factor-*.test.ts` (NEW vitest files)
  - TS mirror parity tests (Python pure kernel ↔ TS mirror 6 cases)
  - TOTP code generation/verification parity (RFC 6238 ±1 window)
- [ ] 8.7 `apps/web/e2e/m12-2fa-*.spec.ts` (NEW Playwright files)
  - 4 NEW E2E scenarios (setup / verify / challenge / recovery)
  - M2 entry gate (2FA 미설정 시 모달 + 차단)

### Task 9: ALLOWED_SERVICE_SUBMODULES sweep + 3중 게이트 (CR 11-2/11-3 lesson)

- [ ] 9.1 `apps/api/import_linter.ini` (or equivalent) EXTENSION
  - `apps.api.modules.m12_account` allowlist 추가
  - **CR 11-2/11-3 lesson**: ALLOWED_SERVICE_SUBMODULES 즉시 sweep (Story 12-1 wire 시점에 m12_account service submodule 보존)
- [ ] 9.2 ruff scoped auto-fix sweep (CR 11-3 lesson)
  - `ruff check apps/api/modules/m12_account packages/services/m12_account` → 0 errors
  - W292 trailing newline + UP038 PEP 604 union + SIM300 Yoda + SIM222 or True + ERA001 disable comments auto-fix
- [ ] 9.3 import-linter verify (CR 11-2 lesson)
  - `import-linter` 2 KEPT 0 broken (ALLOWED_SERVICE_SUBMODULES m12_account 추가 후)
- [ ] 9.4 pytest run (CR 4-3 lesson: `def test_*` + `asyncio.run(_impl())` project convention)
  - `pytest` 1,714 baseline + ~80 NEW = ~1,800 passed + 127 skipped + 0 failed
  - **MAX SDR 갱신**: 1,758 → ~1,838 (+80 NEW, separate line for unambiguous parser match per CR 11-2 lesson)
- [ ] 9.5 vitest + Playwright run (Story 0.5 plumbing 정합)
  - vitest 18 NEW cases pass + 6 NEW parity cases
  - Playwright 4 NEW E2E scenarios pass

### Task 10: Docs + finalization (AC: 전체)

- [ ] 10.1 `docs/account-security-operations.md` (NEW, ~200 lines)
  - Epic 12 overview + 3-story cj-style 분할
  - 12-1 2FA Mandatory Gate 운영 매뉴얼
  - TOTP 등록 플로우 + recovery codes + lockout 정책
  - AD-3·9·10·NFR5·6·7 wire 가이드
- [ ] 10.2 `docs/conventions.md` EXTENSION
  - §10 "Audit Actions" SSOT EXTENSION (ActionClass.TWO_FACTOR_AUTH 6 NEW values)
  - §N (NEW) "TOTP & 2FA" �션 (RFC 6238 + AES-256-GCM + bcrypt recovery codes)
- [ ] 10.3 `docs/capability-matrix.md` EXTENSION (Task 6.3과 중복 — 동일 본문)
- [ ] 10.4 `docs/architecture-inventory.md` EXTENSION
  - `m12_account/` module entry 추가
  - 13 module → 13 module (m12_account 진입) 정합
- [ ] 10.5 `deferred-work.md` EXTENSION
  - 본 스토리 honestly DEFER items (T8 frontend 일부 + T10 docs 일부는 carry-over 시 정리)
- [ ] 10.6 `sprint-status.yaml` EXTENSION
  - `12-1: ready-for-dev` → `12-1: in-progress` (dev-story 시작 시점에 자동 갱신)
  - `epic-12: backlog` → `epic-12: in-progress` (첫 스토리 진입)

## Dev Notes

### Architecture compliance (AD-3 / AD-9 / AD-10)

- **AD-3 (RLS)**: `users.totp_*` 컬럼은 이미 RLS policy 적용 (`apps/api/alembic/versions/0001_*` + `supabase/policies/0001_users_rls.sql`). 컬럼 추가는 0022 migration에서 처리, RLS policy는 0013에서 명시적으로 재확인.
- **AD-9 (Seoul, ap-northeast-2)**: 2FA cron job (lockout cleanup)도 KST 02:00 daily 실행 (Epic 12 12-2 backup cron과 동일 시간대).
- **AD-10 (identity+roles)**: 4-role `owner`/`member`/`viewer`/`consultant_proxy` 검증은 `require_role()` FastAPI dependency 활용 (이미 `apps/api/core/capability.py:362` 정의). M2 진입 시 `role ∈ {owner, member}` + 2FA gate 이중 검증.

### Library / framework requirements

- **TOTP library**: `pyotp` (PyPI, MIT, RFC 6238 호환, base32 + HMAC-SHA1) — Story 0.3 stack pin table에 등록 필요 (or stdlib 직접 구현 — Task 1.1 stdlib-only 결정)
- **AES-256-GCM**: `cryptography` library (PyPI, Apache 2.0) — `apps/api/core/crypto.py` 신규 모듈
- **bcrypt for recovery codes**: `bcrypt` (PyPI, Apache 2.0) — `packages/services/m12_account/totp.py` Task 1.1
- **Frontend QR code**: `qrcode` (PyPI) for `qr_payload` 생성 + `qrcode.react` (npm) for TS mirror
- **Frontend TOTP input**: shadcn Input + 6-digit numeric pattern

### File structure requirements

- **Pure kernel**: `packages/services/m12_account/` (NEW subtree)
  - `totp.py` (Task 1.1)
  - `two_factor_gate.py` (Task 1.2)
- **Service layer**: `apps/api/modules/m12_account/` (NEW populated)
  - `__init__.py` (capability matrix SSOT)
  - `services/{two_factor_service,two_factor_challenge_service,audit_extension}.py`
  - `handlers.py` + `auth_handlers.py` + `m2_gate_handlers.py`
- **Crypto**: `apps/api/core/crypto.py` + `key_manager.py` (NEW)
- **Alembic**: `0022_users_totp_columns.py` + `0023_audit_logs_two_factor_auth_check.py`
- **RLS**: `supabase/policies/0013_users_totp_columns_rls.sql`
- **Frontend**: `apps/web/components/m12-account/` + `apps/web/lib/m12-account/` + `apps/web/app/[locale]/(authenticated)/m12-account/security/2fa/setup/page.tsx`
- **ALLOWED_SERVICE_SUBMODULES sweep**: m12_account 추가 (Task 9.1)

### Testing requirements

- **Pure kernel tests**: `tests/services/m12_account/test_totp.py` (15+ cases) + `test_two_factor_gate.py` (10+ cases)
  - RFC 6238 ±1 window tolerance test (90s)
  - Recovery code 1회용 consume test
  - Lockout 5회 실패 + 15분 정책 test
- **Service layer tests**: `tests/api/m12_account/test_two_factor_service.py` (15+ cases) + `test_two_factor_challenge_service.py` (8+ cases)
  - **CR 4-3 lesson**: `def test_*` + `asyncio.run(_impl())` project convention (NOT async def test_*)
  - audit-first invariant test (CR 1.1)
  - idempotent no-op test (AC #6)
- **Handler tests**: `tests/api/m12_account/test_handlers.py` (12+ cases) + `test_auth_handlers.py` (8+ cases)
  - 8 NEW exception envelope tests (per handler)
  - role gating test (AC #4 — viewer/consultant_proxy → 403)
- **Capability drift**: `tests/integration/test_capability_matrix_drift.py` EXTENSION (6 NEW)
- **Audit drift**: `tests/api/test_audit_action_drift.py` EXTENSION (6 NEW)
- **Frontend vitest**: `apps/web/__tests__/lib/m12-*.test.ts` (6 NEW files, parity + components)
- **Playwright E2E**: `apps/web/e2e/m12-*.spec.ts` (4 NEW scenarios)
- **V8 골든 fixture (optional)**: 2FA는 deterministic 계산이 아니므로 V8 fixture 적용 불가 — capability matrix drift로 대체

### Project Structure Notes

- **Alignment with unified project structure**: `apps/api/modules/m12_account/` (13 module convention) + `packages/services/m12_account/` (pure kernel subtree)
- **Detected conflicts or variances**:
  - `packages/services/m12_account/` — Epic 12 cj-style 분할 결정 시점에 신규 subtree 생성 (Epic 11의 `packages/services/m11_close/` 패턴 동일)
  - `apps/api/core/crypto.py` — Epic 12 이전에 column-level encryption helper 없음 → 12-1 wire 시점에 신규 (Epic 0 이후 첫 crypto helper)
  - **Conflict check**: `apps/api/core/audit_action.py` ActionClass 12개 → 13개 (TWO_FACTOR_AUTH 추가) — drift detector 3-way 일관성 검증 필수 (CR 1.1 + A5)

### Previous story intelligence (from 11-1~11-4 + 6-1~6-3)

- **CR 11-2/11-3 lesson (auth-layer divergence + ALLOWED_SERVICE_SUBMODULES sweep)**: Story 11-2/11-3 sweep 패턴 그대로 적용 — `apps/api/import_linter.ini` ALLOWED_SERVICE_SUBMODULES m12_account 추가 즉시
- **CR 11-3 lesson (ruff scoped auto-fix sweep)**: 12-1 wire 후 `ruff check apps/api/modules/m12_account packages/services/m12_account` → 0 errors
- **CR 11-3 lesson (SDR separate line for unambiguous parser match)**: MAX SDR 갱신 시 separate line (1,758 → ~1,838, +80 NEW tests)
- **CR 4-3 lesson (async test → def test_+asyncio.run)**: 모든 service layer test는 project convention 준수
- **CR 1.1 lesson (audit-first + idempotent no-op)**: 6 NEW ActionClass.TWO_FACTOR_AUTH values — SSOT forward-lock
- **CR 6-2/6-3 lesson (cross-language parity drift detector)**: `apps/web/lib/m12-account/` TS mirror parity test 6+ cases
- **CR 11-2/11-3 lesson (REOPEN_CHANNELS / exception HTTP refactor)**: 8 NEW exception handlers 일관 envelope (status code 매핑 정합)
- **A5 forward-lock**: audit_action.py ActionClass + DB CHECK + call sites 3-way 정합 — drift detector 6 NEW cases
- **capability matrix v1.13 wire**: TWO_FACTOR_AUTH row + 4 industries 매트릭스 정합
- **cj-style 3-story 분할 5번째 epic 연속**: Epic 4·5·6·11과 동일 패턴 — 12-1 (2FA) → 12-2 (backup) → 12-3 (deletion)

### Git intelligence (recent patterns)

- **Recent 5 commits** (from baseline_commit 50b6399):
  - `50b6399 @ Epic 6 close-out retro: A19 honestly DEFER entry`
  - `dda7283 @ Epic 6 close-out: retro complete`
  - `ae3f26e @ Story 11.4: Epic 11 carry-over sprint wire-final`
  - `0ca41e6 @ Story 6.3: bmad-code-review 3rd sweep patches`
  - `4c2c8da @ Story 6.3: T4~T6 close-out`
- **Patterns to reuse**:
  - 11-4 frontend wire 패턴 (5 TS mirrors + 4 components + ko-KR.json + vitest + Playwright)
  - 11-3 exception HTTP refactor 패턴 (5 exception handlers + AD-15 §4 envelope)
  - 11-3 service convention 패턴 (`def test_*` + `asyncio.run(_impl())`)
  - 11-3 audit_action rename sweep 패턴 (5 Literal × 5 _ActionRegistry × 5 files)
- **Code patterns established**: AD-11 layer rule + AD-22 append-only-leaning + AD-25 multi-channel publisher + CR 1.1 audit-first + idempotent no-op + AD-15 envelope

### Latest tech information

- **TOTP RFC 6238**: `pyotp` 2.9.0 stable (2024-Q4) — HMAC-SHA1 default + base32 + 30s step + 6-digit
- **AES-256-GCM**: `cryptography` 43.0.1 (2024-Q4) — FIPS 140-2 validated + column-level encryption 패턴
- **bcrypt**: 4.2.0 (2024-Q4) — cost factor 12 default + recovery code hashing 표준
- **Next.js 16.2.11** (per STACK_PIN): `next/font/local` Pretendard + React 19.2.8 + Tailwind 4.3.3
- **FastAPI 0.139.2** + Python 3.12 + PostgreSQL 17 (STACK_PIN)

### References

- PRD §F12.1 (2FA Mandatory Gate to M2 Entry) — epics.md Story 12.1 verbatim
- PRD §M12-a ("시스템은 2FA 미설정 상태에서 M2 진입을 차단한다") — PRD line 482
- PRD §8.M12 (계정·운영 module map) — PRD line 422
- PRD §F0.1~F0.3 (Epic 1 onboarding) — tenant_memberships + role 정의 출처
- PRD NFR7 (2FA 강제) — line 498
- PRD NFR5 (TLS) + NFR6 (AES-256) — line 498
- AD-3 (RLS) + AD-9 (Seoul) + AD-10 (identity+roles) — epics.md Epic 12 line 499
- epics.md Epic 12 — line 494~501
- epics.md Story 12.1 — line 1186~1196
- epics.md Story 12.2 + 12.3 (12-1 cj-style 분할 2-3번째 follow-up)
- Epic 11 close-out retro §7 A14 권장안 (cj-style 3-story 분할) — handoff 2026-08-09-epic-11-retro-done
- Epic 6 close-out retro §7 A21+A22 (Epic 12 진입 결정 + capability matrix v1.13) — handoff 2026-08-09-6-3-spec-ready
- `apps/api/core/capability.py` (CR 11-2 lesson 적용 baseline)
- `apps/api/alembic/versions/0001_tenants_users_memberships_settings.py:38` (4-role `_ROLE_VALUES`)
- `apps/api/alembic/versions/0021_cache_invalidation_multi_channel.py` (down_revision baseline for 0022)
- `apps/web/components/m11-close/` (Story 11-4 frontend wire 패턴 baseline)
- `docs/capability-matrix.md` (v1.12 → v1.13 wire)
- `docs/conventions.md` §10 "Audit Actions" SSOT
- docs/account-security-operations.md (NEW, Task 10.1)
- CR 11-1~11-4 lessons applied (auth-layer divergence + ALLOWED_SERVICE_SUBMODULES + ruff scoped sweep + SDR separate line)
- CR 1.1 + CR 4-3 + CR 6-2/6-3 lessons applied

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

<!-- Dev agent will append debug log entries here -->

### Completion Notes List

<!-- Dev agent will append completion notes here -->

### File List

<!-- Dev agent will append file list here. Expected new files:
- packages/services/m12_account/__init__.py
- packages/services/m12_account/totp.py
- packages/services/m12_account/two_factor_gate.py
- apps/api/modules/m12_account/__init__.py
- apps/api/modules/m12_account/handlers.py
- apps/api/modules/m12_account/auth_handlers.py
- apps/api/modules/m12_account/m2_gate_handlers.py
- apps/api/modules/m12_account/services/__init__.py
- apps/api/modules/m12_account/services/two_factor_service.py
- apps/api/modules/m12_account/services/two_factor_challenge_service.py
- apps/api/modules/m12_account/services/audit_extension.py
- apps/api/core/crypto.py
- apps/api/core/key_manager.py
- apps/api/alembic/versions/0022_users_totp_columns.py
- apps/api/alembic/versions/0023_audit_logs_two_factor_auth_check.py
- supabase/policies/0013_users_totp_columns_rls.sql
- apps/web/components/m12-account/TwoFactorSetupModal.tsx
- apps/web/components/m12-account/TwoFactorChallengeModal.tsx
- apps/web/components/m12-account/TwoFactorRecoveryCodesModal.tsx
- apps/web/components/m12-account/TwoFactorStatusBadge.tsx
- apps/web/components/m12-account/TwoFactorGuard.tsx
- apps/web/lib/m12-account/m12-two-factor-setup.ts
- apps/web/lib/m12-account/m12-two-factor-gate.ts
- apps/web/lib/m12-account/m12-two-factor-types.ts
- apps/web/app/[locale]/(authenticated)/m12-account/security/2fa/setup/page.tsx
- tests/services/m12_account/test_totp.py
- tests/services/m12_account/test_two_factor_gate.py
- tests/api/m12_account/test_two_factor_service.py
- tests/api/m12_account/test_two_factor_challenge_service.py
- tests/api/m12_account/test_handlers.py
- tests/api/m12_account/test_auth_handlers.py
- tests/web/__tests__/lib/m12-two-factor-setup.test.ts
- tests/web/__tests__/lib/m12-two-factor-gate.test.ts
- tests/web/__tests__/components/m12-two-factor-setup-modal.test.tsx
- tests/web/__tests__/components/m12-two-factor-challenge-modal.test.tsx
- tests/web/e2e/m12-2fa-setup.spec.ts
- tests/web/e2e/m12-2fa-verify.spec.ts
- tests/web/e2e/m12-2fa-challenge.spec.ts
- tests/web/e2e/m12-2fa-recovery.spec.ts
- docs/account-security-operations.md

Modified files (EXTENSION):
- apps/api/core/capability.py (TWO_FACTOR_AUTH enum + industry map)
- apps/api/core/audit_action.py (ActionClass.TWO_FACTOR_AUTH 6 NEW values)
- apps/api/core/audit_action.py (AuditAction Literal union EXTENSION)
- apps/api/core/db_models.py (users model EXTENSION with totp_* columns)
- apps/api/main.py (8 NEW exception handlers)
- apps/web/app/[locale]/(dashboard)/m2-input/period/[periodKey]/page.tsx (TwoFactorGuard wrapper)
- apps/web/messages/ko-KR.json (18 NEW strings)
- docs/capability-matrix.md (v1.12 → v1.13)
- docs/conventions.md (Audit Actions SSOT EXTENSION + §N TOTP)
- docs/architecture-inventory.md (m12_account module entry)
- tests/integration/test_capability_matrix_drift.py (6 NEW cases)
- tests/api/test_audit_action_drift.py (6 NEW cases)
- deferred-work.md (12-1 honestly DEFER items)
- sprint-status.yaml (12-1 status + epic-12 status)
-->
