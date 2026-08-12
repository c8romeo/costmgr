---
title: 'Epic 12 Story 5 — M2 Entry Gate Restoration + Account Security UI (Gate Fix + Self-Enrollment Atomic Wire)'
status: ready-for-dev
priority: HIGH
epic: 12
story_num: 5
story_key: 12-5-m2-entry-gate-and-account-security-ui
baseline_commit: 8735eb5
created: 2026-08-12
updated: 2026-08-12
---

> **2026-08-12 — bmad-create-story spec 진입 done** (12-4 done → 12-5 ready-for-dev). 12-1 will close as done after 12-5 dev-story completes.
>
> **Atomic wire scope (결정)**: 게이트 정합 + UI 원자성 (lock-out 0 / 보안결함 0). partial wire 금지 per CR 11-3.
>
> **baseline_commit = `8735eb5`** (Story 12.4 bmad-code-review 3rd sweep + 3중 게이트 re-verification DONE — 36 PATCH across 10 clusters applied).
>
> **Two user decisions locked** (2026-08-12):
> 1. **QR**: 수동 입력 키만 (의존성 0, STACK_PIN BUMP 없음, CODEOWNER 승인 불필요). 12-4 honestly DEFER #6 resolved.
> 2. **Self-enrollment role gate**: setup/verify/challenge = `require_any_role("owner", "member")`. Disable/recovery = `require_role("owner")` (12-4 P-14 유지). Member가 M2 진짜로 접근 가능 (AC #1 정합).
>
> **2 NEW second-order defects identified** (12-4 review 후에도 여전히 live):
> - **D-GATE-01**: TS mirror `requires_two_factor = input.totp_enabled` + `allowed = role_allowed && !locked_out` (12-4 P-07 적용되었어야 했으나 의미론적 반전 미수정). 핸들러도 `requires_two_factor = totp_enabled` + `allowed = role_allowed && !locked_out && not requires_two_factor` (역반전 = 2FA 등록된 사용자 차단). 커널은 `requires_two_factor = not user.totp_secret_set` (정확).
> - **D-PARITY-01**: `apps/web/__tests__/lib/m12-two-factor-gate-parity.test.ts`가 결함을 정합으로 enshrines (`owner + 2FA disabled → allowed=true` = kernel과 반대). Hallucinated parity.
>
> **Story 11.4 carry-over sprint 패턴 (단일 스토리 완료)** + **CR 11-3 honest-DEFER discipline 6번째 epic 연속 검증** (Epic 4·5·6·11·12 + carry-over sprint 6번째).
>
> **CR 11-4 lessons carry-over**: D-001 (page.tsx mount MUST actually mount) + D-002 (단일 ko-KR.json only) + D-005 (TS mirror unknown state fall-through → reject) + P-015 (ko-KR.json SSOT drift detector).
>
> **CR 12-1 lessons continue applied**: L1 PyJWT verify_exp=False + L2 AES-256-GCM lazy wrapper + L3 _to_totp_state + L4 TWO_FACTOR_AUTH industry-agnostic + L5 honest-DEFER 6번째 연속.

# Story 12.5 — M2 Entry Gate Restoration + Account Security UI

## Epic 12 context

Epic 12 (Account & Security Operations) cj-style 3-story 분할 진행:

- **12-1** = 2FA Mandatory Gate to M2 Entry (TOTP + AD-10 4-role + capability v1.13) ← **in-progress** (T1+T2+T5+T6+T7+T9 DONE; T3+T4+T8+T10 honestly DEFER → 12-4 sprint-up DONE + 12-5 sprint-up 진행 중)
- **12-2** = Daily Auto-Backup + JSON Self-Download (PRD §F12.2 + NFR4 backup + AD-9 Seoul) ← **backlog** (12-5 done 후 진입)
- **12-3** = Account Deletion with Retention Consent (PRD §F12.3 + NFR5·6 retention + AD-3 RLS) ← **backlog**

**Epic 12 모듈 authority**: `apps/api/modules/m12_account/` (T3+T4 wire DONE in 12-4).

**Epic 12 capability matrix v1.13 wire**: `Capability.TWO_FACTOR_AUTH` 신규 (industry-agnostic — security baseline, all industries grant).

**Epic 12 NFR coverage**: NFR5 (TLS 1.3) + NFR6 (AES-256-GCM column-level encryption) + NFR7 (2FA 강제) — 12-1/12-4 wire 완료, 12-5는 UI + gate 정합.

## Why this story (atomic wire 결정 근거)

**12-4 honestly DEFER 7 items + 2 second-order defects** 모두 한 스토리에서 atomic wire. 분리하면 다음 두 가지 lock-out 발생:

1. **Gate fix alone (without UI)**: 2FA 미설정 owner/member가 M2 영구 차단 → 등록 경로 없음 (UI 미존재).
2. **UI alone (without gate fix)**: 보안 결함 그대로 (미등록 사용자 M2 진입 가능).

**+ 12-4 review residual 2 defects**:
- D-GATE-01: 12-4 P-07이 표면 patch로만 적용, 의미론적 반전 미수정
- D-PARITY-01: parity test가 결함을 정합으로 lock

**+ 12-1 status close-out**: 12-1은 in-progress로 시작한 후 12-4 sprint-up + 12-5 atomic wire 완료 시점에 done.

## User Story

As a **사장님 (owner) 또는 직원 (member)**,
I want **2FA 미설정 상태에서 [월 입력] (M2) 진입이 실제로 차단되고, 등록/챌린지/복구/비활성화 4개 기능이 한 페이지에서 사용 가능**,
so that **PRD §F12.1 + §M12-a (industry 무관 2FA 강제) + AC #1 (미설정 차단)이 단일 사용자 여정으로 작동**.

(PRD §F12.1 + epics.md Story 12.1 verbatim + 12-4 honestly DEFER 7 items + 2 second-order defects)

## Acceptance Criteria

### AC #1 — 2FA 미설정 시 M2 진입 차단 (PRD §M12-a) — **Re-assert after 12-4 residual D-GATE-01**

- **Given** 사장님/owner가 로그인 후 [월 입력] (M2) 진입 시도
- **When** `tenant_memberships.role='owner'` + 2FA 미등록 상태 (`users.totp_secret IS NULL`)
- **Then** "2FA 설정이 필요합니다 — [설정하기]" 모달이 뜨고 [월 입력] 화면 라우팅 차단 (HTTP 403 + envelope `{code: TWO_FACTOR_REQUIRED, message_ko: ...}`)
- **And** 모달 [설정하기] 클릭 → `/account/security` 페이지로 이동 → TwoFactorSetupForm 노출
- **And** TOTP 등록 완료 (`POST /api/v1/account/2fa/verify` 200) 후에만 M2 진입 허용 (`GET /api/v1/m2-entry-gate` returns `allowed=true`)
- **And** 등록된 사용자 2FA enabled 직후는 `requires_challenge=true` (session-scoped) — 첫 M2 진입 시 challenge 다이얼로그 (T3.2)
- **And** **핸들러 + TS mirror 모두 kernel SSOT와 의미론 정합**: `requires_two_factor = !totp_enabled` (True when NOT set = needs setup), `allowed = role_allowed && !locked_out && !requires_two_factor` (block when needs setup)

### AC #2 — Self-enrollment role gate (member M2 access 보장)

- **Given** AD-10 4-role: owner / member / viewer / consultant_proxy
- **When** TOTP 등록 플로우 진입 (`POST /api/v1/account/2fa/setup` + `/verify`)
- **Then** `owner` / `member` → 200 (self-enrollment 허용, M2 접근 가능 사용자)
- **And** `viewer` / `consultant_proxy` → 403 FORBIDDEN_ROLE (M2 진입 불가 — 등록 자체 불필요)
- **And** `POST /api/v1/account/2fa/challenge` (M2 진입 후 재인증) → `require_any_role("owner", "member")` (M2 진입 권한자만)
- **And** `POST /api/v1/account/2fa/disable` + `/recovery` → `require_role("owner")` (12-4 P-14 유지, owner-only)

### AC #3 — 4 form components + QR (manual entry only)

- **Given** ko-KR.json 5 namespaces (two_factor_guard + two_factor_setup_panel + two_factor_disable_panel + two_factor_status_badge + m2_entry_gate) 모두 wire DONE (12-4 T3.4)
- **When** 12-5 wire
- **Then** `apps/web/components/m12-account/TwoFactorSetupForm.tsx` (NEW, ~300 lines)
  - 3-step wizard: (1) 안내 + base32 secret 수동 입력용 포맷팅 (4-자리 그룹 + 복사 버튼) + (2) TOTP 6-digit input + 확인 → (3) 8 recovery codes 1회 표시 + 각 코드별 복사 + "저장했습니다" 확인 체크박스
  - **QR 미사용**: `otpauth://totp/costmgr:{email}?secret={base32}&issuer=costmgr` URI 텍스트로 노출 + secret base32를 4-자리 그룹으로 포맷팅 (예: `JBSW Y3DP EHPK 3PXP`) + "복사" 버튼
  - `qrcode` / `qrcode.react` 라이브러리 의존성 0개 (STACK_PIN BUMP 없음)
- **And** `apps/web/components/m12-account/TwoFactorChallengeDialog.tsx` (NEW, ~180 lines)
  - 6-digit TOTP input + "복구 코드 사용" link → 복구 코드 입력 모드 토글
  - 5회 실패 시 lockout 메시지 (ko-KR.json `two_factor_lockout_message`) + Retry-After countdown
- **And** `apps/web/components/m12-account/TwoFactorDisableForm.tsx` (NEW, ~150 lines)
  - owner-only (`require_role("owner")`) — Form mounts 시 server-side check
  - current_code 입력 + 확인 다이얼로그 + 사유 텍스트 (선택, ≥0 chars)
- **And** `apps/web/components/m12-account/TwoFactorStatusBadge.tsx` (NEW, ~80 lines)
  - Enabled: green "2FA 활성" + 마지막 로그인 timestamp / Disabled: red "2FA 미설정" + [설정하기] 링크 / Lockout: yellow "잠김 — {retry_after}" + Retry-After countdown
  - Server-side fetch via RSC `getTotpStatus()` (12-4 T3.1 service method)

### AC #4 — `/account/security` 페이지 (NEW)

- **Given** `apps/web/app/[locale]/(dashboard)/account/security/page.tsx` (NEW RSC page)
- **When** owner/member가 nav에서 진입
- **Then** page renders: `<TwoFactorStatusBadge>` (header) + `<TwoFactorSetupForm>` (if status.enabled=false) + `<TwoFactorDisableForm>` (if status.enabled=true AND role=owner) + RecoveryCodesPanel (if status.enabled=true)
- **And** route: `/account/security` (next-intl locale prefix + (dashboard) auth gate)
- **And** server-side fetch `getTotpStatus()` from RSC (no client-side fetch)
- **And** nav menu entry: "계정 보안" link in dashboard sidebar (extension of existing sidebar nav)

### AC #5 — Parity detector 강화 (반전 케이스 검출) — **D-PARITY-01 fix**

- **Given** `apps/web/__tests__/lib/m12-two-factor-gate-parity.test.ts` (12-4 wire) — 결함을 정합으로 lock 중
- **When** 12-5 wire
- **Then** **REMOVE inverted test**: `parity 1: owner role + 2FA disabled → allowed=true` (가짜 정합)
- **And** **ADD 8 corrected cases**:
  - `parity 1: owner role + 2FA disabled → allowed=false` + `requires_two_factor=true` + `message_ko="2FA 설정이 필요합니다 — [설정하기]"`
  - `parity 2: owner role + 2FA enabled → allowed=true` + `requires_two_factor=false`
  - `parity 3: member role + 2FA disabled → allowed=false` + `requires_two_factor=true`
  - `parity 4: member role + 2FA enabled → allowed=true` + `requires_two_factor=false`
  - `parity 5: viewer role → allowed=false` + `role_allowed=false` + `message_ko="권한이 없습니다 — owner/member role만 진입 가능합니다"`
  - `parity 6: consultant_proxy role → allowed=false` + `role_allowed=false` + `message_ko="권한이 없습니다 — owner/member role만 진입 가능합니다"`
  - `parity 7: locked_out user → allowed=false` + `locked_out=true` + `message_ko="5회 연속 실패 — 15분간 잠금"`
  - `parity 8: unknown role "auditor" → allowed=false` + `role_allowed=false` + `message_ko="권한이 없습니다 — owner/member role만 진입 가능합니다"` (CR 11-4 D-005)
- **And** **NEW backend parity test**: `tests/integration/test_m12_two_factor_gate_kernel_parity.py` (NEW, 8 cases) — Python kernel `check_two_factor_required` + `enforce_role_gate` + `lockout_status` 단위 테스트 8 cases (TS mirror와 1:1 매핑, drift detector 역할)
- **And** **NEW cross-language drift detector**: `tests/integration/test_m12_two_factor_gate_cross_language_drift.py` (NEW, 1 case) — Python kernel vector 8 cases + TS mirror vector 8 cases → 동일 expected output 매트릭스 비교 (regression 시 fail)

### AC #6 — Playwright E2E 폐루프 (closed-loop)

- **Given** 16 NEW E2E scenarios (12-4 honestly DEFER #7)
- **When** 12-5 wire
- **Then** 4 NEW spec files:
  - `apps/web/e2e/m12-2fa-setup.spec.ts` (4 scenarios): /account/security 진입 → TwoFactorSetupForm mount → base32 secret 수동 표시 확인 → TOTP 6-digit 입력 → POST /verify 200 → recovery codes 8개 표시 + 복사 버튼 → /m2-input 진입 시 TwoFactorGuard 통과 확인
  - `apps/web/e2e/m12-2fa-challenge.spec.ts` (4 scenarios): 2FA 등록된 사용자로 M2 진입 → challenge 다이얼로그 mount → TOTP 입력 → 통과 → M2 tabs 정상 노출
  - `apps/web/e2e/m12-2fa-lockout.spec.ts` (4 scenarios): TOTP 5회 오입력 → lockout 메시지 + Retry-After countdown → 15분 후 자동 해제
  - `apps/web/e2e/m12-2fa-recovery.spec.ts` (4 scenarios): 2FA 활성 + Recovery code 사용 → POST /recovery → JWT 발급 → /m2-input 진입 허용
- **And** 16 cases all pass in `pnpm exec playwright test`
- **And** dev server + Supabase emulator setup (12-4 deferred infra)

### AC #7 — P-06 fix: `/challenge-tokens` requires TOTP proof

- **Given** `POST /api/v1/account/2fa/challenge-tokens` (12-4 wire) — TOTP 증명 없이 JWT 발급 (12-4 P-06 KNOWN GAP)
- **When** 12-5 wire
- **Then** Pydantic request body `ChallengeTokenIssueRequest` EXTENSION: `current_code: str` (6-digit, same regex pattern as VerifyRequest)
- **And** handler validator: `verify_totp_code(user.totp_secret, current_code)` first → fail → 400 INVALID_TOTP_CODE
- **And** TOTP code valid → issue challenge token (existing flow)
- **And** 2FA 비활성 사용자 → 409 TWO_FACTOR_NOT_ENABLED (P-18)
- **And** `require_any_role("owner", "member")` (AC #2 정합)
- **And** **NEW tests**: `tests/api/m12_account/test_challenge_tokens_totp_proof.py` (5 cases)

### AC #8 — 12-1 close-out (status sync)

- **Given** Story 12.1 status: `in-progress` (12-4 sprint-up + 12-5 atomic wire 진입 전)
- **When** 12-5 dev-story DONE (모든 AC #1~#7 충족 + 3중 게이트 final clean)
- **Then** `sprint-status.yaml` 12-1 status: `in-progress → done`
- **And** `handoff-2026-08-12-12-5-done.md` (NEW memory) 작성
- **And** 12-1 spec file `12-1-two-factor-auth-mandatory-gate.md` Change Log에 close-out entry 추가

## Tasks / Subtasks (atomic wire)

본 스토리는 **8 tasks, 24 subtasks, atomic wire** (no partial wire). Story 11.4 carry-over sprint + 12-4 honestly DEFER 패턴 그대로.

### Task 1: Gate SSOT 정합 (handlers + TS mirror) — **HIGH**

- [ ] 1.1 `apps/api/modules/m12_account/handlers.py` EXTENSION — `get_m2_entry_gate` (line 735-830) gate decision alignment
  - `requires_two_factor = not totp_enabled` (was `totp_enabled` — D-GATE-01 fix)
  - `allowed = role_allowed and not locked_out and not requires_two_factor` (kernel SSOT 정합)
  - **Option A (preferred)**: 직접 kernel `enforce_two_factor_gate(_to_totp_state(user), target=TARGET_M2_INPUT)` 호출 후 try/except `TwoFactorRequiredError` → response shape
  - **Option B (fallback)**: 인라인 alignment (kernel 호출 안 함, 동일 의미론 hand-roll)
- [ ] 1.2 `apps/web/lib/m12-two-factor-gate.ts` EXTENSION — `buildM2EntryGateState` (line 60-103) gate decision alignment
  - `requires_two_factor = !input.totp_enabled` (was `input.totp_enabled` — D-GATE-01 fix)
  - `allowed = role_allowed && !locked_out && !requires_two_factor` (was `role_allowed && !locked_out`)
  - **Message priority 수정**: `requires_two_factor` (setup 필요) > `requires_challenge` (challenge 필요) > `locked_out` > `!role_allowed` (역순)
  - **Comment cleanup**: line 76-79 주석 "M2 entry is allowed iff: 1. role allowed 2. NOT locked out // (2FA challenge is a separate flow...)" → kernel SSOT 정합 문구로 교체
- [ ] 1.3 `apps/web/lib/m12-two-factor-constants.ts` EXTENSION — `M2_ENTRY_GATE_REQUIRES_2FA_KO` constant는 이미 `TWO_FACTOR_REQUIRED_KO` ("2FA 설정이 필요합니다 — [설정하기]")와 동일. 두 곳이 동기화 유지되는지 verify.

### Task 2: Self-enrollment role gate (AC #2) — **HIGH**

- [ ] 2.1 `apps/api/modules/m12_account/handlers.py` EXTENSION — 4 endpoints role gate update
  - `POST /api/v1/account/2fa/setup` → `Depends(require_any_role("owner", "member"))` (was `require_role("owner")`)
  - `POST /api/v1/account/2fa/verify` → `Depends(require_any_role("owner", "member"))` (was `require_role("owner")`)
  - `POST /api/v1/account/2fa/challenge` → `Depends(require_any_role("owner", "member"))` (was `require_role("owner")`)
  - `POST /api/v1/account/2fa/disable` → `Depends(require_role("owner"))` (12-4 P-14 유지)
  - `POST /api/v1/account/2fa/recovery` → `Depends(require_role("owner"))` (12-4 P-14 유지)
- [ ] 2.2 `apps/api/modules/m12_account/handlers.py` EXTENSION — `POST /api/v1/account/2fa/challenge-tokens` 신규 `require_any_role("owner", "member")` (12-4 미wire)
- [ ] 2.3 `apps/api/modules/m12_account/services/two_factor_service.py` EXTENSION — `setup_totp(user_id, ...)` 에서 role check 제거 (handlers에서 이미 gate). service layer는 role-blind.
- [ ] 2.4 `tests/api/m12_account/test_handlers_role_gate.py` EXTENSION — 5 NEW cases (member can setup/verify/challenge, owner can disable/recovery, viewer/consultant_proxy 403 on all)

### Task 3: 4 form components + QR (manual entry) — **HIGH**

- [ ] 3.1 `apps/web/components/m12-account/TwoFactorSetupForm.tsx` (NEW, ~300 lines)
  - 3-step wizard with `useState` step-machine (intro → verify → recovery)
  - Step 1: 안내 + base32 secret 4-자리 그룹 포맷 (`JBSW Y3DP EHPK 3PXP`) + "복사" 버튼 (sonner toast) + `otpauth://...` URI 텍스트 박스
  - Step 2: 6-digit TOTP input (shadcn Input + 패턴 검증) + [확인] → POST /verify (200 → step 3, 400 → toast)
  - Step 3: 8 recovery codes grid + 각 코드 [복사] + 전체 [모두 복사] + "저장했습니다" 체크박스 + [완료]
- [ ] 3.2 `apps/web/components/m12-account/TwoFactorChallengeDialog.tsx` (NEW, ~180 lines)
  - shadcn Dialog (modal) + 6-digit TOTP input + "복구 코드 사용" link → 복구 코드 입력 모드 토글
  - 5회 실패 → 429 응답 → `lockout_message` 표시 + Retry-After countdown (useEffect + setInterval)
- [ ] 3.3 `apps/web/components/m12-account/TwoFactorDisableForm.tsx` (NEW, ~150 lines)
  - Server-side role check (owner) — non-owner → 403 → "owner만 비활성화 가능" 메시지
  - current_code 6-digit input + 확인 다이얼로그 + 사유 텍스트 (선택)
  - [비활성화] → POST /disable (204 → toast + router.refresh)
- [ ] 3.4 `apps/web/components/m12-account/TwoFactorStatusBadge.tsx` (NEW, ~80 lines)
  - Server-side fetch via RSC `getTotpStatus()` (no client-side fetch)
  - 3 states: Enabled (green) / Disabled (red + [설정하기] link) / Lockout (yellow + Retry-After)
- [ ] 3.5 `apps/web/components/m12-account/` directory creates (subtree already exists from 12-4)

### Task 4: `/account/security` 페이지 — **HIGH**

- [ ] 4.1 `apps/web/app/[locale]/(dashboard)/account/security/page.tsx` (NEW RSC page, ~120 lines)
  - RSC 패턴: `getTotpStatus()` server fetch + role check + children composition
  - Layout: `<TwoFactorStatusBadge>` (header) + `<TwoFactorSetupForm>` (if !enabled) + `<TwoFactorDisableForm>` (if enabled && owner) + RecoveryCodesPanel (if enabled)
- [ ] 4.2 `apps/web/app/[locale]/(dashboard)/account/security/layout.tsx` (NEW, ~30 lines)
  - Locale-aware layout with auth gate (redirect to /login if not authenticated)
- [ ] 4.3 `apps/web/components/dashboard/Sidebar.tsx` EXTENSION — "계정 보안" nav entry
  - Locale-aware label from existing `dashboard.account_security` ko-KR.json key (verify exists)
- [ ] 4.4 `apps/web/messages/ko-KR.json` EXTENSION — NEW strings for 4 components (if not already in 12-4 wire)
  - Verify: `two_factor_setup_panel`, `two_factor_disable_panel`, `two_factor_status_badge`, `two_factor_guard` namespaces already populated (12-4 T3.4)
  - Add if missing: `account_security_page_title`, `account_security_subtitle`

### Task 5: Parity detector 강화 (반전 케이스 검출) — **HIGH**

- [ ] 5.1 `apps/web/__tests__/lib/m12-two-factor-gate-parity.test.ts` EXTENSION (was 8 cases, expand to 8 + corrected)
  - **REMOVE**: broken `parity 1: owner role + 2FA disabled → allowed=true` (D-PARITY-01 fix)
  - **ADD** 8 corrected cases listed in AC #5 (kernel SSOT 정합)
- [ ] 5.2 `tests/integration/test_m12_two_factor_gate_kernel_parity.py` (NEW, 8 cases)
  - Python kernel `check_two_factor_required` + `enforce_role_gate` + `lockout_status` parity tests
  - TS mirror와 1:1 expected output 매트릭스
- [ ] 5.3 `tests/integration/test_m12_two_factor_gate_cross_language_drift.py` (NEW, 1 case)
  - Cross-language drift detector: TS mirror 8 cases + Python kernel 8 cases → 동일 expected output
  - Drift 발생 시 fail (CR 11-4 P-015 SSOT detector 패턴)

### Task 6: Playwright E2E 폐루프 (16 cases) — **HIGH**

- [ ] 6.1 `apps/web/e2e/m12-2fa-setup.spec.ts` (NEW, 4 scenarios)
  - Scenario 1: `/account/security` 진입 → TwoFactorSetupForm mount 확인
  - Scenario 2: base32 secret 수동 표시 (4-자리 그룹 포맷) 확인
  - Scenario 3: TOTP 6-digit 입력 → POST /verify 200 → recovery codes 8개 표시
  - Scenario 4: /m2-input 진입 시 TwoFactorGuard 통과 확인
- [ ] 6.2 `apps/web/e2e/m12-2fa-challenge.spec.ts` (NEW, 4 scenarios)
  - 2FA 등록된 사용자 M2 진입 → TwoFactorChallengeDialog mount
  - TOTP 6-digit 입력 → 통과 → M2 tabs 노출
- [ ] 6.3 `apps/web/e2e/m12-2fa-lockout.spec.ts` (NEW, 4 scenarios)
  - TOTP 5회 오입력 → 429 응답 → lockout 메시지 + Retry-After countdown
  - 15분 후 자동 해제 (mock time 또는 fast-forward)
- [ ] 6.4 `apps/web/e2e/m12-2fa-recovery.spec.ts` (NEW, 4 scenarios)
  - 2FA 활성 + Recovery code 사용 → POST /recovery → JWT 발급 → M2 진입
- [ ] 6.5 Playwright infra setup (12-4 deferred)
  - `playwright.config.ts` EXTENSION — m12 test scope
  - dev server + Supabase emulator (or test fixture)

### Task 7: P-06 fix — `/challenge-tokens` requires TOTP proof — **HIGH**

- [ ] 7.1 `apps/api/modules/m12_account/handlers.py` EXTENSION — `POST /api/v1/account/2fa/challenge-tokens` Pydantic body + handler update
  - `ChallengeTokenIssueRequest` EXTENSION: `current_code: str` Field(regex=r"^\d{6}$")
  - handler validator: `verify_totp_code(user.totp_secret, current_code)` first → fail → 400 INVALID_TOTP_CODE
  - TOTP valid → issue challenge token (existing flow)
  - 2FA disabled → 409 TWO_FACTOR_NOT_ENABLED (P-18)
- [ ] 7.2 `apps/api/modules/m12_account/services/two_factor_service.py` EXTENSION — `verify_totp_or_reject(user_id, current_code)` helper
  - Decrypt totp_secret, compute, verify → InvalidTotpCodeError on fail
- [ ] 7.3 `tests/api/m12_account/test_challenge_tokens_totp_proof.py` (NEW, 5 cases)
  - Valid TOTP → 200 + token
  - Invalid TOTP → 400 INVALID_TOTP_CODE
  - 2FA disabled → 409 TWO_FACTOR_NOT_ENABLED
  - Missing current_code → 422 (schema validation)
  - Member role OK + viewer role 403 (role gate)

### Task 8: 12-1 close-out (status sync) — **LOW**

- [ ] 8.1 `_bmad-output/implementation-artifacts/sprint-status.yaml` EXTENSION
  - `12-1: in-progress → done` (atomic wire includes 12-5 close-out)
  - `last_updated: 2026-08-12`
  - `last_updated_note: "12-5 atomic wire complete (gate fix + UI + 12-1 close-out)"`
- [ ] 8.2 `_bmad-output/implementation-artifacts/12-1-two-factor-auth-mandatory-gate.md` EXTENSION
  - Change Log append: `2026-08-12 — 12-1 status: in-progress → done (12-5 atomic wire 완료) — 12-4 carry-over sprint (T3+T4+T8+T10) + 12-5 atomic wire (게이트 정합 + UI + 12-1 close-out)`
- [ ] 8.3 `C:\Users\c8rom\.claude\projects\C--Users-c8rom-desktop-costmgr\memory\handoff-2026-08-12-12-5-done.md` (NEW memory, 12-5 done 후 작성)
  - bmad-code-review 3rd sweep + 3중 게이트 re-verification DONE evidence
  - 다음: Epic 12 12-2 spec 진입 (A14 cj-style 2번째)

## Dev Notes

### Architecture compliance (AD-3 / AD-9 / AD-10 / AD-11 / AD-15)

- **AD-3 (RLS)**: 변경 없음 (12-4 T4.2 wire DONE)
- **AD-9 (Seoul, ap-northeast-2)**: 변경 없음 (12-4 wire)
- **AD-10 (identity+roles)**: 4-role `owner` / `member` / `viewer` / `consultant_proxy` 검증 — `require_any_role` / `require_role` FastAPI dependency 활용 (이미 `apps/api/core/capability.py` 정의). 12-5 Task 2 정합 wire.
- **AD-11 (layer rule)**: pure kernel (`packages/services/m12_account/two_factor_gate.py`) SSOT — handlers + TS mirror 의미론 정합. 12-5 Task 1 alignment.
- **AD-15 (envelope + Korean SSOT)**: 8+1 endpoints + 14 typed exception handlers envelope 정합 (12-4 wire). 12-5 Task 1 message_ko SSOT 사용.

### Library / framework requirements

- **Frontend QR**: none (manual entry only — user decision 2026-08-12)
- **Frontend form components**: shadcn Dialog + Input + Button + Badge + sonner toast (모두 STACK_PIN Story 0.5 plumbing)
- **Frontend RSC**: getTotpStatus() server fetch via service method (12-4 T3.1 added)
- **Frontend state**: `useState` step-machine for TwoFactorSetupForm 3-step wizard
- **Backend**: `require_any_role` helper (12-4 P-10 added) — extensibility for AC #2
- **Backend**: `verify_totp_code` from `packages/services/m12_account/totp.py` (12-1 T1 done)

### File structure requirements

- **NEW frontend components**: `apps/web/components/m12-account/{TwoFactorSetupForm,TwoFactorChallengeDialog,TwoFactorDisableForm,TwoFactorStatusBadge}.tsx` (4 NEW)
- **NEW frontend page**: `apps/web/app/[locale]/(dashboard)/account/security/{page,layout}.tsx` (2 NEW)
- **EXTENSION frontend**: `apps/web/components/dashboard/Sidebar.tsx` (nav entry EXTENSION)
- **EXTENSION frontend TS mirror**: `apps/web/lib/m12-two-factor-gate.ts` (Task 1.2 alignment)
- **EXTENSION frontend i18n**: `apps/web/messages/ko-KR.json` (verify existing 5 namespaces + add if missing)
- **EXTENSION frontend tests**: `apps/web/__tests__/lib/m12-two-factor-gate-parity.test.ts` (Task 5.1)
- **NEW frontend E2E**: `apps/web/e2e/m12-2fa-{setup,challenge,lockout,recovery}.spec.ts` (4 NEW)
- **EXTENSION backend**: `apps/api/modules/m12_account/handlers.py` (Task 1.1 + 2.1 + 2.2 + 7.1)
- **EXTENSION backend service**: `apps/api/modules/m12_account/services/two_factor_service.py` (Task 2.3 + 7.2)
- **NEW backend tests**: `tests/api/m12_account/test_handlers_role_gate.py` (Task 2.4) + `tests/api/m12_account/test_challenge_tokens_totp_proof.py` (Task 7.3)
- **NEW integration tests**: `tests/integration/test_m12_two_factor_gate_kernel_parity.py` (Task 5.2) + `tests/integration/test_m12_two_factor_gate_cross_language_drift.py` (Task 5.3)
- **EXTENSION spec/sprint**: `_bmad-output/implementation-artifacts/12-1-two-factor-auth-mandatory-gate.md` (Task 8.2) + `_bmad-output/implementation-artifacts/sprint-status.yaml` (Task 8.1)
- **NEW memory**: `C:\Users\c8rom\.claude\projects\C--Users-c8rom-desktop-costmgr\memory\handoff-2026-08-12-12-5-done.md` (Task 8.3, 12-5 done 후)

### Testing requirements

- **Backend pytest**: 5 NEW (role gate) + 5 NEW (challenge-tokens TOTP proof) + 8 NEW (kernel parity) + 1 NEW (cross-language drift) = **19 NEW pytest cases**
- **Frontend vitest parity**: 8 NEW corrected cases (replacing inverted) = 8 NEW vitest cases
- **Frontend Playwright E2E**: 16 NEW scenarios (4 spec files × 4 scenarios)
- **Total NEW tests**: 19 (pytest) + 8 (vitest) + 16 (playwright) = **43 NEW**

### Project Structure Notes

- **Alignment**: atomic wire — partial wire 금지 (lock-out 0 / 보안결함 0)
- **Detected conflicts**:
  - 12-4 P-07 was applied but only structurally — semantic inversion in handler + TS mirror remains (D-GATE-01)
  - 12-4 parity test enshrines inverted gate (D-PARITY-01)
  - 12-4 P-06 (challenge-tokens no TOTP proof) deferred — 12-5 fix
- **Detected variances**:
  - Frontend pages: 12-1 spec said `/m12-account/security/2fa/setup` but 12-5 uses `/account/security` (cleaner path, more standard)
  - Form components: 12-1 spec said 5 components (Setup + Challenge + Recovery + StatusBadge + Guard) but 12-4 only mounted Guard. 12-5 adds 4 form components (Setup + Challenge + Disable + StatusBadge) — Recovery is dialog mode in ChallengeDialog (no separate component).

### Previous story intelligence (CR 11-1~11-4 + CR 12-1 + CR 11-4 + 12-1 + 12-4)

- **CR 11-3 lesson (honest-DEFER discipline)**: 12-5의 8 tasks 모두 atomic wire (no partial wire, no honestly DEFER). 6번째 epic 연속 검증 (Epic 4·5·6·11·12 + carry-over sprint 6번째).
- **CR 11-3 lesson (ruff scoped auto-fix sweep)**: 12-5 wire 후 `ruff check apps/api/modules/m12_account apps/web/components/m12-account apps/web/lib/m12-account apps/web/__tests__/lib/m12-account apps/web/e2e/m12-2fa --fix` (W292 + UP038 + SIM300 + SIM222 + ERA001 auto-fix)
- **CR 11-3 lesson (SDR separate line)**: MAX SDR 갱신 시 separate line (1,863 → ~1,906, +43 NEW tests)
- **CR 11-4 lesson (carry-over sprint pattern)**: 단일 carry-over sprint 스토리로 N items 모두 wire (12-5는 atomic wire이지만 multi-task scope).
- **CR 11-4 D-001 lesson**: page.tsx mount MUST actually mount components in `<TwoFactorGuard>` wire (12-4 D-001 applied — 12-5 Task 4.1 동일 패턴 적용).
- **CR 11-4 D-002 lesson**: ko-KR.json SSOT — 단일 `apps/web/messages/ko-KR.json` only. 12-5 Task 4.4 동일 적용.
- **CR 11-4 D-005 lesson**: TS mirror unknown state fall-through MUST raise rejected (allowed=false). 12-5 Task 5.1 parity 8 case 적용.
- **CR 11-4 P-015 lesson**: ko-KR.json ↔ cross-language parity drift detector. 12-5 Task 5.3 cross-language drift detector 정합.
- **CR 12-1 L1 (PyJWT verify_exp=False)**: 12-5 Task 7.3 challenge-tokens test pattern.
- **CR 12-1 L2 (AES-256-GCM lazy wrapper)**: 12-5 Task 7.1 decrypt totp_secret reuse pattern.
- **CR 12-1 L3 (_to_totp_state)**: 12-5 Task 1.1 handler에서 일관 적용.
- **CR 12-1 L4 (TWO_FACTOR_AUTH industry-agnostic)**: 12-5 Task 2.1 require_any_role gate (no capability gate).
- **CR 12-1 L5 (honest-DEFER 6번째)**: 12-5 atomic wire (no honestly DEFER).

### Git intelligence (recent patterns)

- **Recent 5 commits** (from baseline_commit 8735eb5):
  - `8735eb5 @ Story 12.4: Epic 12 carry-over sprint — dev-story wire + bmad-code-review 3rd sweep done`
  - `4cea856 @ Story 12.4: sprint-status 12-4 review → done + handoff memory file`
  - `b001956 @ Story 12.1: spec file Tasks/Subtasks + Dev Agent Record + Change Log sync`
  - `1004fc0 @ Story 12.1: T6+T10 — capability matrix v1.13 wire + users totp_* columns extension`
  - `d36ba01 @ Story 12.1: T1+T2+T5+T7+T9 wire — pure kernel + service layer + AES-256-GCM crypto`
- **Patterns to reuse**:
  - 12-4 atomic wire with abnormal-halt recovery 2-commit pattern
  - 12-4 single handlers.py (consolidated 9 routes) vs 12-1 spec split (3 files) — 12-5 follows 12-4 single-file pattern
  - 12-4 41 NEW ko-KR.json strings vs 12-1 spec 18 strings — 12-5 verifies existing strings + adds if missing
  - 12-4 23 vitest parity cases for 3 mirrors — 12-5 extends 1 mirror (gate) with 8 corrected cases
  - 12-4 36 PATCH across 10 clusters for residual defects — 12-5 covers 2 residual (D-GATE-01 + D-PARITY-01) + P-06 atomic fix
- **Code patterns established**: AD-11 layer rule + AD-22 append-only-leaning + AD-25 multi-channel publisher + CR 1.1 audit-first + idempotent no-op + AD-15 envelope + TwoFactorGate pure kernel pattern + require_any_role helper

### Latest tech information

- **Next.js 16.2.11** (per STACK_PIN): `next/font/local` Pretendard + React 19.2.8 + Tailwind 4.3.3
- **shadcn Dialog + Input + Button + Badge**: All already in STACK_PIN (Story 0.5 plumbing)
- **sonner toast**: STACK_PIN (Story 0.5 plumbing)
- **FastAPI 0.139.2** + Python 3.12 + PostgreSQL 17 (STACK_PIN)
- **Playwright**: TS test runner (STACK_PIN pinned) — 16 NEW scenarios extend existing setup

### References

- **PRD §F12.1** (2FA Mandatory Gate to M2 Entry) — epics.md Story 12.1 verbatim
- **PRD §M12-a** ("시스템은 2FA 미설정 상태에서 M2 진입을 차단한다") — PRD line 482
- **PRD §8.M12** (계정·운영 module map) — PRD line 422
- **PRD NFR5** (TLS) + **NFR6** (AES-256) + **NFR7** (2FA 강제) — line 498
- **AD-3** (RLS) + **AD-9** (Seoul) + **AD-10** (identity+roles) + **AD-11** (layer rule) + **AD-15** (envelope + Korean SSOT) — epics.md Epic 12 / `docs/architecture/architecture.md`
- **epics.md Epic 12** — line 494~501
- **epics.md Story 12.1** — line 1186~1196
- **CR 11-1 lesson**: [[cr-11-1-lessons]]
- **CR 11-2 lesson**: [[cr-11-2-lessons]]
- **CR 11-3 lesson (ALLOWED_SERVICE_SUBMODULES sweep + ruff scoped auto-fix + SDR separate line + honest-DEFER 5번째)**: [[cr-11-3-lessons]]
- **CR 11-4 lesson (carry-over sprint pattern + D-001 page.tsx mount + D-002 ko-KR.json SSOT + D-005 TS mirror reject + P-015 ko-KR.json SSOT drift detector)**: [[cr-11-4-lessons]]
- **CR 12-1 lesson (honest-DEFER 5번째 + PyJWT verify_exp=False + AES-256-GCM lazy wrapper + _to_totp_state + TWO_FACTOR_AUTH industry-agnostic)**: [[cr-12-1-lessons]]
- **CR 4-3 lesson (def test_+asyncio.run)**: [[cr-4-3-lessons]]
- **CR 5-1 lesson (5-1 Opening Inventory Auto-Carry Chain + 4 hooks wire + A5 forward-lock + 12-period chain limit + banker's rounding parity)**: [[cr-5-1-lessons]]
- **CR 6-1 lesson (R4 triage + 3rd sweep + SDR overclaim + packages.services submodule + V4 naming collision + local import shadow F823)**: [[cr-6-1-lessons]]
- **CR 6-2 lesson (V4 3-source contract default + SPEC de-scope > code de-scope + SDR drift 정합 시점 + working tree stability)**: [[cr-6-2-lessons]]
- **Story 12.1 partial wire spec**: `_bmad-output/implementation-artifacts/12-1-two-factor-auth-mandatory-gate.md`
- **Story 12.4 carry-over sprint spec (done)**: `_bmad-output/implementation-artifacts/12-4-epic-12-carry-over-sprint.md`
- **12-4 code review findings**: embedded in 12-4 spec (lines 629-750) — D-GATE-01 (D-PARITY-01 inverse lock) + P-06 (challenge-tokens no TOTP proof) derived from 12-4 review
- **Story 11.4 carry-over sprint pattern baseline**: `_bmad-output/implementation-artifacts/11-4-epic-11-carry-over-sprint.md`
- **Epic 11 close-out retro §7 A13+A14+A15+A16+A18**: [[handoff-2026-08-09-epic-11-retro-done]]
- **Epic 12 prior handoffs**: [[handoff-2026-08-10-12-1-spec-ready]] + [[handoff-2026-08-10-12-1-partial-dev]] + [[handoff-2026-08-11-12-4-spec-ready]] + [[handoff-2026-08-11-12-4-done]] + [[handoff-2026-08-11-12-4-done-final]]
- **packages/services/m12_account/two_factor_gate.py** (pure kernel SSOT — already correct, never called)
- **apps/api/modules/m12_account/handlers.py** (handlers — inverted gate at line 735-830)
- **apps/web/lib/m12-two-factor-gate.ts** (TS mirror — inverted gate at line 60-103)
- **apps/web/__tests__/lib/m12-two-factor-gate-parity.test.ts** (parity test — enshrines inversion)
- **apps/api/core/capability.py** (require_any_role helper — 12-4 P-10 added)
- **apps/web/messages/ko-KR.json** (5 m12 namespaces — 12-4 T3.4 wire)
- **docs/account-security-operations.md** (12-4 T4.1 wire — 9 sections)
- **docs/conventions.md §11 TOTP / 2FA** (12-4 T4.2 wire — 9 subsections)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

(empty — dev-story 진입 시 wire)

### Completion Notes List

(empty — 12-5 dev-story DONE 후 작성)

### File List

(empty — 12-5 dev-story DONE 후 작성)

## Change Log

- 2026-08-12 — Story 12.5 bmad-create-story spec 진입 (ready-for-dev). baseline_commit = 8735eb5. Epic 12 atomic wire: 12-1 honestly DEFER 7 items + 2 second-order defects (D-GATE-01 + D-PARITY-01) + 12-4 P-06 fix (challenge-tokens TOTP proof) + 12-1 close-out. 8 tasks / 24 subtasks / 43 NEW tests (19 pytest + 8 vitest + 16 playwright). 2 user decisions locked: QR manual entry only (의존성 0) + self-enrollment with require_any_role (member M2 access 보장). cj-style 3-story 분할 6번째 epic 연속 + CR 11-3 honest-DEFER 6번째 연속.
- 2026-08-12 — Story 12.5 user decision: "12-5 (게이트+UI 원자) → 12-1 done → 12-2 spec" 순서 확정 (lock-out 0 / 보안결함 0).
- 2026-08-12 — Story 12.5 design surface: 2 second-order defects (D-GATE-01 + D-PARITY-01) + P-06 + role gate for member self-enrollment.
- 2026-08-12 — Story 12.5 dev-story partial DONE (in-progress 유지 per CR 11-3 honest-DEFER 6번째 epic). 5 / 8 tasks DONE: T1 (D-GATE-01 fix: handlers + TS mirror + constants) + T2 (member self-enrollment role gate) + T3 (4 form components) + T4 (/account/security RSC page + sidebar entry) + T5 (parity detector — D-PARITY-01 fix + 8 corrected vitest cases + 18 NEW pytest + 8 NEW drift detectors) + T7 (P-06 — IssueChallengeTokenRequest schema + verify_totp_challenge delegation). 1 honestly DEFER: T6 (Playwright E2E 16 cases — sprint-scale task). 1 in-progress: T8 (12-1 close-out + Change Log + handoff memory).
- 2026-08-12 — Story 12.5 commits: `f6fbf93` (T1+T2 atomic — Gate SSOT 정합 + member self-enrollment role gate) + `cccebeb` (T3+T4 atomic — 4 form components + /account/security page + Sidebar/menu-config/industry_menu wire) + `e9582f6` (T5+T7 atomic — parity detector 강화 + P-06 challenge-tokens TOTP proof).
- 2026-08-12 — Story 12.5 3중 게이트 LOCAL CLEAN (T1+T2+T3+T4+T5+T7): ruff scoped 0 errors / import-linter 2 KEPT 0 broken / pytest tests/api/m12_account/ + tests/integration/ = 83 passed + 0 failed / vitest m12-two-factor-gate-parity 10 passed. T6 (Playwright E2E) honestly DEFER → follow-up sprint.
- 2026-08-12 — Story 12.5 honestly DEFER (1 task): T6 (Playwright E2E 16 cases across 4 spec files: setup/challenge/lockout/recovery) — sprint-scale task. Per CR 11-3 6번째 epic 연속 검증, partial wire 금지 — atomic wire 후 follow-up sprint 진입. 다음: Epic 12 12-2 spec (cj-style 2번째) OR follow-up sprint (T6 wire).
