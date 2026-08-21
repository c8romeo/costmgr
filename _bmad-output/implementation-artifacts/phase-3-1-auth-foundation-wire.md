---
baseline_commit: 7c6aaa9f7f465be52ebeb522c6ce716696171874
---

# Story phase-3.1: Auth Foundation Wire (Phase 3 cj-style 2번째 진입점)

Status: in-progress

<!-- Phase 3 cj-style 2번째 진입점 = cj-style 50번째 epic 연속 정직 회복.
     Phase 3 PRD entry (`phase-3-prd-entry: done`, 2026-08-20) + Phase 3-0 auth contract slice (`phase-3-0-auth-contract-slice: done`, 2026-08-21) 직후.
     master PRD v3.0 §F15 verbatim + AD-26 verbatim + A65~A69 결정 wire.
     T1~T8 wire scope (frontend-focused, Docker 없이 가능) + D-1-1-DEFER-1/2/3 honestly DEFER preserved. -->

## Story

As a **costmgr product owner**,
I want the **Auth Foundation (login / signup / logout / forgot-password UI + auth middleware EXTENSION) fully wired end-to-end with Supabase SSR + sb-access-token cookie session + Edge Runtime middleware + (dashboard) route group protection**,
so that **Phase 3 = Epic 1 완성 territory (Epic 1 carry-over 정직 회복) 가 wire 되어 모든 dashboard 진입 시점에 login redirect + 2FA challenge flow + tenant creation atomic transaction + audit-first INSERT 가 production-grade 로 동작**합니다.

## Acceptance Criteria

PRD §F15.1 ~ §F15.5 verbatim + §F15.6 T1~T8 wire scope verbatim.

### F15.1 Login UI + Supabase SSR Auth Client (M0-(d))

- [ ] **AC1.1** `/[locale]/login` Server Component route 가 `next/headers.cookies()` 로 `sb-access-token` 쿠키를 읽고 `apps/web/lib/supabase/server.ts` 의 `supabase.auth.getUser()` 로 세션 검증. 유효 세션 → `/[locale]/(dashboard)/` redirect (`?redirect=` 쿼리 보존), 무세션 → `<LoginForm>` Client Component 렌더.
- [ ] **AC1.2** `<LoginForm>` (`apps/web/components/auth/LoginForm.tsx` NEW) — 이메일 + 비밀번호 2 필드 + [로그인] + [회원가입] / [비밀번호 찾기] 링크. 이메일 RFC 5322 검증, 비밀번호 `type="password"` + [보기/숨기기] 토글 (WCAG AA contrast). `supabase.auth.signInWithPassword({ email, password })` 호출, 성공 시 `router.push(redirect ?? '/[locale]/(dashboard)/')` + `router.refresh()`.
- [ ] **AC1.3** ko-KR 에러 메시지 — `LOGIN_INVALID_CREDENTIALS_KO` (401) + `LOGIN_NETWORK_ERROR_KO` (네트워크 실패) + `LOGIN_RATE_LIMITED_KO` (429, 5회 연속 실패 30초 cool-down). 5회 cool-down 로직은 `apps/web/lib/auth/login.ts` 에서 처리.
- [ ] **AC1.4** 2FA 정합 (Epic 12 wire) — `supabase.auth.getSession()` 의 `session.access_token` payload 에 `aal = 'aal2'` 면 2FA 인증 완료 (dashboard 진입), `aal = 'aal1'` 면 `/[locale]/auth/2fa` 챌린지 redirect.
- [ ] **AC1.5** Supabase SSR client invariant — `sb-access-token` 쿠키 = `httpOnly` + `secure` + `sameSite=lax` + `path=/` + `maxAge=3600`. `supabase.auth.getUser()` 가 `sb-access-token` 만 읽음, `sb-refresh-token` 는 server-only. CSRF 방어 = Supabase PKCE flow + sameSite=lax cookie (별도 CSRF token 미사용).
- [ ] **AC1.6** SSR + browser 양쪽 client 인스턴스 분리 — server = `createServerClient()` (cookie-based, Next.js cookies API), browser = `createBrowserClient()` (localStorage-based). URL + anon key (`NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY`) 가 server/client 양쪽에서 동일하게 resolve.

### F15.2 Signup UI + Tenant Creation Flow (M0-(e))

- [ ] **AC2.1** `/[locale]/signup` Server Component route 가 Supabase SSR client 로 세션 검증 후 세션 있으면 dashboard redirect, 없으면 `<SignupForm>` Client Component 렌더.
- [ ] **AC2.2** `<SignupForm>` (`apps/web/components/auth/SignupForm.tsx` NEW) — 이메일 + 비밀번호 + 비밀번호 확인 + 회사명 4 필드 + [가입하기] + [로그인] 링크. 검증 invariant: 이메일 RFC 5322 + 중복 (서버 측), 비밀번호 `^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]).{10,}$`, 비밀번호 확인 일치, 회사명 1~100자 trim 후 비어있지 않음.
- [ ] **AC2.3** 가입 성공 시 atomic transaction — `supabase.auth.signUp({ email, password, options: { data: { company_name } } })` → `useUser()` 가 pre-onboarding JWT 로 `POST /api/v1/onboarding/complete-signup` 호출 → `SignupService.complete_signup()` atomic 5-step (users + tenants + tenant_memberships + tenant_settings + audit_logs) → `supabase.auth.refreshSession()` → 두 번째 mint 에서 `custom_access_token_hook` (alembic 0035) 가 `app_metadata.tenant_id`/`role`/`industry` 주입.
- [ ] **AC2.4** 이메일 인증 완료 후 `/[locale]/(auth)/onboarding/industry` 자동 redirect (Epic 1 partial scaffold 의 IndustrySelector 진입). 미완료 시 `/[locale]/(auth)/email-verification-pending` + 재발송 버튼.
- [ ] **AC2.5** ko-KR 에러 메시지 — `SIGNUP_DUPLICATE_EMAIL_KO` (409) + `SIGNUP_WEAK_PASSWORD_KO` (422) + `SIGNUP_INVALID_EMAIL_KO` (422) + `SIGNUP_NETWORK_ERROR_KO` (네트워크 실패) + `SIGNUP_PASSWORD_MISMATCH_KO` (client-side) + `ALREADY_HAS_TENANT_KO` (409, `SignupService.complete_signup()` `AlreadyHasTenantError`).

### F15.3 Auth Middleware EXTENSION — Supabase Session Check + (dashboard) 보호 (M0-(f))

- [ ] **AC3.1** `apps/web/middleware.ts` 의 next-intl middleware EXTENSION — 모든 `/[locale]/(dashboard)/*` 요청에 Supabase session 검사 강제. `createMiddleware(...)` 호출 후 추가 핸들러 등록.
- [ ] **AC3.2** 세션 없거나 만료 시 `/[locale]/login?redirect=<original-path>` redirect. `original-path` = `req.nextUrl.pathname` + `req.nextUrl.search` 보존.
- [ ] **AC3.3** `/[locale]/(auth)/*` 공개 route group 미들웨어 bypass. `/api/v1/*` bypass (백엔드 FastAPI `get_tenant_context` 가 자체적으로 Supabase JWT verification + tenant context resolution). Static assets (`_next/*`, `*.png`, `*.svg`, ...) matcher 제외.
- [ ] **AC3.4** Epic 12 2FA 게이트 EXTENSION — `supabase.auth.getSession()` `session.access_token` payload `aal = 'aal1'` 인 사용자 (2FA 미설정) 가 `/[locale]/(dashboard)/*` 진입 시 `/[locale]/account/security?reason=2fa_required` redirect. 단 `/[locale]/account/security` 자체는 dashboard 진입 가능.
- [ ] **AC3.5** Edge Runtime — middleware = `export const runtime = 'edge'`. Edge Runtime 제약: Node.js API 미사용, Supabase SSR client Edge-compatible variant (`createServerClient` 의 cookie-based Edge variant).
- [ ] **AC3.6** `apps/web/lib/auth/middleware.ts` NEW — middleware helper (Supabase SSR Edge variant + session extraction + 2FA gate logic).

### F15.4 Logout Flow + Korean SSOT

- [ ] **AC4.1** `/[locale]/api/auth/logout` Route Handler (`apps/web/app/[locale]/api/auth/logout/route.ts` NEW) — POST 요청 시 `supabase.auth.signOut()` + `sb-access-token` + `sb-refresh-token` 쿠키 만료 + `router.push('/[locale]/login')` + `router.refresh()`.
- [ ] **AC4.2** `<LogoutButton>` (`apps/web/components/auth/LogoutButton.tsx` NEW) — sidebar 또는 dashboard 헤더 [로그아웃] 버튼, logout Server Action 호출. 2FA 미설정 사용자 정상 동작 (Epic 12 2FA gate 우회).
- [ ] **AC4.3** logout 후 `audit_logs` row 1개 (`action_name='user_logged_out'`, actor_user_id, tenant_id, payload={session_duration_seconds, logout_method='manual'|'session_expired'}) atomic append (CR 1-1 audit-first INSERT 정합).
- [ ] **AC4.4** ko-KR 에러 메시지 — `LOGOUT_FAILED_KO` (500) + `LOGOUT_NETWORK_ERROR_KO` (네트워크 실패). CR 12-5 D-14 envelope `{code, message_ko, details, trace_id}` 정합.

### F15.5 Forgot-Password UI + Supabase resetPasswordForEmail

- [ ] **AC5.1** `/[locale]/(auth)/forgot-password` Server Component — 세션 있으면 dashboard redirect, 없으면 `<ForgotPasswordForm>` Client Component.
- [ ] **AC5.2** `<ForgotPasswordForm>` (`apps/web/components/auth/ForgotPasswordForm.tsx` NEW) — 이메일 1 필드 + [재설정 링크 보내기] + [로그인으로 돌아가기]. 제출 시 `supabase.auth.resetPasswordForEmail(email, { redirectTo: '<origin>/[locale]/(auth)/reset-password' })`.
- [ ] **AC5.3** `/[locale]/(auth)/reset-password` Server Component — URL 의 `code` 쿼리 파라미터 (Supabase recovery session) 검증 후 `<ResetPasswordForm>` Client Component. 새 비밀번호 + 비밀번호 확인 (F15.2-(b) 동일 strength) + `supabase.auth.updateUser({ password })` → 성공 시 `/[locale]/login?reset=success` redirect.
- [ ] **AC5.4** password reset 성공 시 모든 기존 세션 무효화 + `audit_logs` row 1개 (`action_name='password_reset'`, actor_user_id, tenant_id, payload={reset_method='email_link', session_invalidated=true}) append (CR 1-1 audit-first INSERT 정합).
- [ ] **AC5.5** ko-KR 에러 메시지 — `FORGOT_PASSWORD_EMAIL_SENT_KO` (보안: 항상 200 반환, 이메일 존재 여부 노출 방지) + `RESET_PASSWORD_INVALID_TOKEN_KO` (401) + `RESET_PASSWORD_WEAK_PASSWORD_KO` (422). Capability gate `FORGOT_PASSWORD` (capability matrix v1.24, industry-agnostic 4-industry grants ✅/✅/✅/✅).

### F15.6 Tests + Capability + atomic commit (3중 게이트 FINAL CLEAN)

- [ ] **AC6.1** `tests/web/test_auth_login_parity.py` NEW (~+15 cases) — login form validation + Supabase SSR client integration + ko-KR 에러 메시지 + 5회 cool-down + 2FA redirect.
- [ ] **AC6.2** `tests/web/test_auth_signup_parity.py` NEW (~+15 cases) — signup form validation + password strength + tenant creation flow.
- [ ] **AC6.3** `tests/web/test_auth_middleware_parity.py` NEW (~+12 cases) — session check + redirect + ?redirect= 보존 + (auth) bypass + /api/v1/* bypass + 2FA gate.
- [ ] **AC6.4** `tests/web/test_auth_logout_parity.py` NEW (~+8 cases) — logout flow + audit_logs INSERT + cookie 만료.
- [ ] **AC6.5** `tests/web/test_auth_forgot_password_parity.py` NEW (~+10 cases) — forgot-password + reset-password + email 존재 여부 노출 방지.
- [ ] **AC6.6** `tests/integration/test_auth_endpoints_e2e.py` NEW (~+10 cases) — backend callback for tenant creation atomic transaction + audit_logs 검증.
- [ ] **AC6.7** `apps/api/core/capability.py` EXTENSION 5 NEW enum (`LOGIN` + `SIGNUP` + `AUTH_MIDDLEWARE` + `FORGOT_PASSWORD` + `LOGOUT`) + 4-industry grants industry-agnostic ✅/✅/✅/✅ (CR 12-1 L4 precedent 미러). `docs/capability-matrix.md` v1.23 → v1.24 (이미 Phase 3 PRD entry wire 시점에 5 NEW rows 추가됨, capability.py enum 만 wire) + `tests/integration/test_capability_matrix_v1_24_drift.py` NEW (drift detector).
- [ ] **AC6.8** 3중 게이트 FINAL CLEAN — (1) `pnpm tsc --noEmit` 0 NEW errors (Phase 3 frontend-only wire) / (2) `pnpm vitest run` ~70 NEW PASS (across 6 test files) + 0 regressions / (3) `pnpm eslint . --max-warnings 0` 0 NEW (pre-existing 16 warnings preserved). Backend 회귀 — `pytest tests/ -q --no-header` baseline 보존 (Phase 3 frontend wire → 0 NEW pytest 영향, but `tests/integration/test_auth_endpoints_e2e.py` ~10 NEW pytest PASS).
- [ ] **AC6.9** A36 SDR 검증 4-step 자동 적용 PASS — (1) commit prefix lint (CR 9-6 D5 prevention) / (2) sprint-status structure 정합 (D4 fix 보존) / (3) vitest file count drift 0건 (D2 fix 보존) / (4) commit consistency 정합 (D1 fix 보존).
- [ ] **AC6.10** atomic commit + sprint-status `phase-3-1-auth-foundation-wire: in-progress → done` + handoff memory 신규 + `docs/auth-foundation.md` NEW (~10 sections, §F15 format EXTENSION).

## Tasks / Subtasks

- [ ] **Task 1 — T1: Supabase SSR client 신규 wire** (AC: #1.5, #1.6, #3.5)
  - [ ] Subtask 1.1 — `apps/web/lib/supabase/env.ts` NEW: `NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY` required env 검증 (Zod 또는 manual)
  - [ ] Subtask 1.2 — `apps/web/lib/supabase/server.ts` NEW: `createServerClient` + Next.js cookies API adapter + `runtime = 'nodejs'` 명시 (Server Component 전용)
  - [ ] Subtask 1.3 — `apps/web/lib/supabase/client.ts` NEW: `createBrowserClient` + URL + anon key
  - [ ] Subtask 1.4 — `apps/web/lib/supabase/types.ts` NEW: Database type definitions (auth.users + tenants + users + tenant_memberships + tenant_settings + audit_logs — **tenant_memberships 정정**, v2.5 PRD 오기 `user_tenants` 사용 금지)
  - [ ] Subtask 1.5 — `apps/web/lib/supabase/middleware.ts` NEW: Supabase SSR Edge variant (cookie-based) — middleware.ts 에서 사용

- [ ] **Task 2 — T2: Login page 신규 wire** (AC: #1.1, #1.2, #1.3, #1.4)
  - [ ] Subtask 2.1 — `apps/web/app/[locale]/(auth)/login/page.tsx` NEW: Server Component — `supabase.auth.getUser()` + redirect (세션 있음) + `<LoginForm>` 렌더 (세션 없음)
  - [ ] Subtask 2.2 — `apps/web/components/auth/LoginForm.tsx` NEW: Client Component — 이메일·비밀번호 2 필드 + `signInWithPassword` + ko-KR 에러 메시지 (LOGIN_INVALID_CREDENTIALS_KO + LOGIN_NETWORK_ERROR_KO + LOGIN_RATE_LIMITED_KO) + [회원가입] / [비밀번호 찾기] 링크 + 2FA 챌린지 redirect (aal='aal1' 일 때 `/auth/2fa`)
  - [ ] Subtask 2.3 — `apps/web/lib/auth/login.ts` NEW: `signInWithPassword` wrapper + 5회 실패 cool-down (in-memory counter or sessionStorage)
  - [ ] Subtask 2.4 — `apps/web/messages/ko-KR.json` EXTENSION: `auth.login` namespace 7+ strings (email_label, password_label, login_button, signup_link, forgot_password_link, error_messages)

- [ ] **Task 3 — T3: Signup page 신규 wire** (AC: #2.1, #2.2, #2.3, #2.4, #2.5)
  - [ ] Subtask 3.1 — `apps/web/app/[locale]/(auth)/signup/page.tsx` NEW: Server Component — `<SignupForm>` 렌더
  - [ ] Subtask 3.2 — `apps/web/components/auth/SignupForm.tsx` NEW: Client Component — 4 필드 검증 (이메일 RFC 5322 + 비밀번호 strength regex + 비밀번호 확인 + 회사명 1~100자) + `signUp` + tenant 생성 backend callback (`POST /api/v1/onboarding/complete-signup` Phase 3-0 wire 정합) + `supabase.auth.refreshSession()` 2nd mint + ko-KR 에러 메시지 (SIGNUP_DUPLICATE_EMAIL_KO + SIGNUP_WEAK_PASSWORD_KO + SIGNUP_INVALID_EMAIL_KO + SIGNUP_NETWORK_ERROR_KO + SIGNUP_PASSWORD_MISMATCH_KO + ALREADY_HAS_TENANT_KO)
  - [ ] Subtask 3.3 — `apps/web/lib/auth/signup.ts` NEW: `signUp` wrapper + password strength validation regex + atomic tenant creation backend callback 결정
  - [ ] Subtask 3.4 — `apps/web/app/[locale]/(auth)/email-verification-pending/page.tsx` NEW: 이메일 인증 미완료 안내 + 재발송 버튼
  - [ ] Subtask 3.5 — `apps/web/messages/ko-KR.json` EXTENSION: `auth.signup` namespace 10+ strings (이메일·비밀번호·비밀번호 확인·회사명 labels + 가입하기·로그인 buttons + error_messages)

- [ ] **Task 4 — T4: Auth middleware EXTENSION** (AC: #3.1, #3.2, #3.3, #3.4, #3.5, #3.6)
  - [ ] Subtask 4.1 — `apps/web/middleware.ts` MODIFIED: next-intl middleware + Supabase session check + `(dashboard)` 보호 + `?redirect=` 쿼리 보존 + 2FA 게이트 EXTENSION (aal='aal1' → `/account/security?reason=2fa_required`) + `(auth)` 공개 + `/api/v1/*` bypass + Edge Runtime 명시 (`export const runtime = 'edge'`)
  - [ ] Subtask 4.2 — `apps/web/lib/auth/middleware.ts` NEW: middleware helper — Supabase SSR Edge variant + session extraction + 2FA gate logic

- [ ] **Task 5 — T5: Logout flow 신규 wire** (AC: #4.1, #4.2, #4.3, #4.4)
  - [ ] Subtask 5.1 — `apps/web/app/[locale]/api/auth/logout/route.ts` NEW: POST handler — `signOut` + `sb-access-token` + `sb-refresh-token` 쿠키 만료 + audit_logs INSERT (`action_name='user_logged_out'`, CR 1-1 audit-first INSERT 정합)
  - [ ] Subtask 5.2 — `apps/web/components/auth/LogoutButton.tsx` NEW: Client Component — logout Server Action 호출
  - [ ] Subtask 5.3 — `apps/web/lib/auth/logout.ts` NEW: `signOut` wrapper + audit log INSERT
  - [ ] Subtask 5.4 — `apps/web/messages/ko-KR.json` EXTENSION: `auth.logout` namespace 3+ strings (logout_button, LOGOUT_FAILED_KO, LOGOUT_NETWORK_ERROR_KO)

- [ ] **Task 6 — T6: Forgot-password + Reset-password 신규 wire** (AC: #5.1, #5.2, #5.3, #5.4, #5.5)
  - [ ] Subtask 6.1 — `apps/web/app/[locale]/(auth)/forgot-password/page.tsx` NEW: Server Component — 세션 있으면 dashboard redirect, 없으면 `<ForgotPasswordForm>`
  - [ ] Subtask 6.2 — `apps/web/components/auth/ForgotPasswordForm.tsx` NEW: Client Component — 이메일 1 필드 + `resetPasswordForEmail` + ko-KR 메시지 (FORGOT_PASSWORD_EMAIL_SENT_KO, 항상 200 반환 = 이메일 존재 여부 노출 방지)
  - [ ] Subtask 6.3 — `apps/web/app/[locale]/(auth)/reset-password/page.tsx` NEW: Server Component — URL `code` 쿼리 파라미터 검증 후 `<ResetPasswordForm>`
  - [ ] Subtask 6.4 — `apps/web/components/auth/ResetPasswordForm.tsx` NEW: Client Component — 새 비밀번호 + 비밀번호 확인 2 필드 검증 (F15.2-(b) 동일 strength) + `updateUser({ password })` → `/[locale]/login?reset=success` redirect
  - [ ] Subtask 6.5 — `apps/web/lib/auth/forgot-password.ts` NEW: `resetPasswordForEmail` wrapper + 보안 (항상 200 반환)
  - [ ] Subtask 6.6 — `apps/web/lib/auth/reset-password.ts` NEW: `updateUser({ password })` wrapper + session invalidation + audit_logs INSERT (`action_name='password_reset'`)
  - [ ] Subtask 6.7 — `apps/web/messages/ko-KR.json` EXTENSION: `auth.forgot_password` namespace 5+ strings + `auth.reset_password` namespace 4+ strings

- [ ] **Task 7 — T7: Capability gate v1.24 EXTENSION** (AC: #6.7)
  - [ ] Subtask 7.1 — `apps/api/core/capability.py` EXTENSION: 5 NEW enum `LOGIN` + `SIGNUP` + `AUTH_MIDDLEWARE` + `FORGOT_PASSWORD` + `LOGOUT` (CR 12-1 L4 precedent — industry-agnostic)
  - [ ] Subtask 7.2 — `apps/api/core/capability.py` 4-industry grants industry-agnostic ✅/✅/✅/✅ (manufacturing + service + retail + food_service)
  - [ ] Subtask 7.3 — `docs/capability-matrix.md` 확인 (Phase 3 PRD entry wire 시점에 5 NEW rows 이미 추가됨, lines 390-394) — capability.py enum 만 wire
  - [ ] Subtask 7.4 — `tests/integration/test_capability_matrix_v1_24_drift.py` NEW: drift detector — SSOT 정합 sweep (P-015 ko-KR.json SSOT drift detector 패턴 미러)

- [ ] **Task 8 — T8: Tests + 3중 게이트 FINAL CLEAN + atomic commit** (AC: #6.1~#6.10)
  - [ ] Subtask 8.1 — `tests/web/test_auth_login_parity.py` NEW (~+15 vitest cases)
  - [ ] Subtask 8.2 — `tests/web/test_auth_signup_parity.py` NEW (~+15 vitest cases)
  - [ ] Subtask 8.3 — `tests/web/test_auth_middleware_parity.py` NEW (~+12 vitest cases)
  - [ ] Subtask 8.4 — `tests/web/test_auth_logout_parity.py` NEW (~+8 vitest cases)
  - [ ] Subtask 8.5 — `tests/web/test_auth_forgot_password_parity.py` NEW (~+10 vitest cases)
  - [ ] Subtask 8.6 — `tests/integration/test_auth_endpoints_e2e.py` NEW (~+10 pytest cases)
  - [ ] Subtask 8.7 — sprint-status `phase-3-1-auth-foundation-wire: in-progress → done` + `last_updated: 2026-08-21 (KST)` line 갱신
  - [ ] Subtask 8.8 — `docs/auth-foundation.md` NEW (~10 sections, §F15 format EXTENSION)
  - [ ] Subtask 8.9 — handoff memory 신규 `C:\Users\c8rom\.claude\projects\C--Users-c8rom-desktop-costmgr\memory\handoff-2026-08-21-phase-3-1-auth-foundation-wire-done.md`
  - [ ] Subtask 8.10 — 3중 게이트 FINAL CLEAN verification: (1) `pnpm tsc --noEmit` 0 NEW / (2) `pnpm vitest run` ~70 NEW PASS + 0 regressions / (3) `pnpm eslint . --max-warnings 0` 0 NEW. A36 SDR 검증 4-step 자동 적용: (a) commit prefix lint / (b) sprint-status structure / (c) vitest file count drift / (d) commit consistency
  - [ ] Subtask 8.11 — atomic commit via `git commit -F <commit-msg-file>` (CR 9-6 D5 prevention — PowerShell here-string 회피)

## Dev Notes

### Source tree components to touch

**NEW files (~15)**
- `apps/web/lib/supabase/env.ts` (T1.1)
- `apps/web/lib/supabase/server.ts` (T1.2)
- `apps/web/lib/supabase/client.ts` (T1.3)
- `apps/web/lib/supabase/types.ts` (T1.4)
- `apps/web/lib/supabase/middleware.ts` (T1.5)
- `apps/web/lib/auth/login.ts` (T2.3)
- `apps/web/lib/auth/signup.ts` (T3.3)
- `apps/web/lib/auth/middleware.ts` (T4.2)
- `apps/web/lib/auth/logout.ts` (T5.3)
- `apps/web/lib/auth/forgot-password.ts` (T6.5)
- `apps/web/lib/auth/reset-password.ts` (T6.6)
- `apps/web/app/[locale]/(auth)/login/page.tsx` (T2.1)
- `apps/web/app/[locale]/(auth)/signup/page.tsx` (T3.1)
- `apps/web/app/[locale]/(auth)/email-verification-pending/page.tsx` (T3.4)
- `apps/web/app/[locale]/(auth)/forgot-password/page.tsx` (T6.1)
- `apps/web/app/[locale]/(auth)/reset-password/page.tsx` (T6.3)
- `apps/web/app/[locale]/api/auth/logout/route.ts` (T5.1)
- `apps/web/components/auth/LoginForm.tsx` (T2.2)
- `apps/web/components/auth/SignupForm.tsx` (T3.2)
- `apps/web/components/auth/LogoutButton.tsx` (T5.2)
- `apps/web/components/auth/ForgotPasswordForm.tsx` (T6.2)
- `apps/web/components/auth/ResetPasswordForm.tsx` (T6.4)
- `tests/web/test_auth_login_parity.py` (T8.1)
- `tests/web/test_auth_signup_parity.py` (T8.2)
- `tests/web/test_auth_middleware_parity.py` (T8.3)
- `tests/web/test_auth_logout_parity.py` (T8.4)
- `tests/web/test_auth_forgot_password_parity.py` (T8.5)
- `tests/integration/test_auth_endpoints_e2e.py` (T8.6)
- `tests/integration/test_capability_matrix_v1_24_drift.py` (T7.4)
- `docs/auth-foundation.md` (T8.8)

**MODIFIED files (~6)**
- `apps/web/middleware.ts` (T4.1) — next-intl + Supabase session + 2FA gate + (dashboard) 보호 + Edge Runtime
- `apps/web/messages/ko-KR.json` (T2.4 + T3.5 + T5.4 + T6.7) — 4 NEW namespaces (auth.login + auth.signup + auth.logout + auth.forgot_password + auth.reset_password), ~30+ strings
- `apps/api/core/capability.py` (T7.1 + T7.2) — 5 NEW enum + 4-industry grants

### Existing files to PRESERVE (Epic 1 partial scaffold)

- `apps/web/app/[locale]/(auth)/layout.tsx` — Epic 1 partial scaffold (minimal shell), **PRESERVE VERBATIM**
- `apps/web/app/[locale]/(auth)/onboarding/industry/page.tsx` — Epic 1 partial scaffold, **PRESERVE VERBATIM**
- `apps/web/components/onboarding/IndustrySelector.tsx` — Epic 1 partial scaffold, **PRESERVE VERBATIM**
- `apps/web/components/onboarding/IndustryCard.tsx` — Epic 1 partial scaffold, **PRESERVE VERBATIM**
- `apps/web/middleware.ts` (Epic 1 partial scaffold next-intl) — **EXTENSION ONLY** (MODIFIED, not rewrite)

### Test environment invariants (CRITICAL)

- **Supabase client mock discipline**: All `tests/web/test_auth_*.py` tests MUST use `vi.mock('@/lib/supabase/client')` + `vi.mock('@/lib/supabase/server')` + `vi.mock('next/navigation')` to avoid requiring live Supabase. Mock pattern = `mocks/handlers.ts` (existing 9-7 wire pattern — POST /api/v1/abc/validate handler reference).
- **Cookie mock**: `next/headers.cookies()` mock via `vi.mock('next/headers', ...)` for Server Component tests
- **No live Supabase**: All tests run in `pnpm vitest` without `NEXT_PUBLIC_SUPABASE_URL` env. Env validation in `lib/supabase/env.ts` MUST throw clear error in test mode (not block tests).

### Existing patterns to mirror (CR 11-4 lessons)

- **CR 11-4 D-001**: `page.tsx` actual mount `<Component>` JSX MUST (no `<>TODO</>` stubs)
- **CR 11-4 D-002**: `apps/web/messages/ko-KR.json` SSOT only (no `lib/ko-KR.json` dual-file)
- **CR 11-4 D-003**: vitest RTL render discipline
- **CR 11-4 D-005**: TS mirror unknown state reject
- **CR 11-4 P-015**: ko-KR.json SSOT drift detector (`test_ko_kr_json_ssot_drift.test.ts` already exists)

### Backend integration points (Phase 3-0 already done)

- `POST /api/v1/onboarding/complete-signup` — Phase 3-0 wire (`1db21d2` commit), `SignupService.complete_signup()` atomic 5-step (users + tenants + tenant_memberships + tenant_settings + audit_logs)
- `get_pre_onboarding_user` FastAPI dep — pre-onboarding JWT (no `tenant_id` claim) 수용
- `decode_jwt(token, require_tenant=False)` — Phase 3-0 wire
- `custom_access_token_hook` (alembic 0035) — `app_metadata.tenant_id`/`role`/`industry` 주입

### Architecture patterns to follow

- **AD-26 Auth Foundation verbatim** (Phase 3 PRD entry §A65 결정):
  - Supabase SSR + sb-access-token cookie session httpOnly+secure+sameSite=lax+maxAge=3600
  - next-intl middleware EXTENSION Supabase session check
  - (dashboard) 보호 + ?redirect= 쿼리 보존
  - (auth) 공개 + /api/v1/* bypass
  - Edge Runtime 명시
  - Supabase PKCE flow + sameSite=lax cookie CSRF 방어
  - email 존재 여부 노출 방지 (FORGOT_PASSWORD_EMAIL_SENT_KO 항상 200 반환)
- **CR 0-2 RLS lesson**: 78+28 RLS policies 가 읽는 SSOT = `app.tenant_id` + `app.user_id` + `request.jwt.claims` (Phase 3-0 wire 정합)
- **CR 1-1 audit-first INSERT**: logout + password_reset 모두 atomic transaction with audit_logs INSERT
- **CR 11-3 honest-DEFER 49번째 epic 연속**: D-1-1-DEFER-1/2/3 honestly preserved (Magic link + Social login OAuth + SSO enterprise SAML)
- **CR 11-4 D-001/D-002/D-003/D-005 + P-015**: 5 lessons carry
- **CR 12-1 L4 precedent**: industry-agnostic capability 4-industry grants
- **CR 12-5 D-14 envelope**: `{code, message_ko, details, trace_id}` 정합
- **CR 9-6 D5 prevention**: `git commit -F <file>` (NOT PowerShell here-string)
- **A19 cohesion pattern 9 surface EXTENSION PASS 결정**: auth surface NEW (T1~T6 SSR client + Server Components + Client Components + Middleware + Server Actions / Route Handlers)

### Project Structure Notes

- **App router directory**: `apps/web/app/[locale]/(auth)/*` + `apps/web/app/[locale]/(dashboard)/*` route groups — Phase 3 T4 middleware 가 (auth) 공개 + (dashboard) 보호 결정 wire
- **Components barrel**: `apps/web/components/auth/` directory 신규 — `index.ts` barrel export (LoginForm + SignupForm + ForgotPasswordForm + ResetPasswordForm + LogoutButton)
- **Lib structure**: `apps/web/lib/supabase/` (Supabase client) + `apps/web/lib/auth/` (auth wrappers) — 분리 결정 (Phase 3-0 wire)
- **Test structure**: `tests/web/test_auth_*.py` (parity tests) + `tests/integration/test_auth_endpoints_e2e.py` (e2e backend callback) — 기존 pattern 미러 (test_ai_extract_parity + test_ai_extraction_endpoint)
- **ko-KR.json namespace**: `auth.login` + `auth.signup` + `auth.logout` + `auth.forgot_password` + `auth.reset_password` — 기존 `auth.*` namespace 가 있는지 확인 (없으면 신규)

### Detected conflicts or variances

- **`tenant_memberships` vs PRD v2.5 `user_tenants`**: master PRD v3.0 §F15.2 wire 진입 시점에 정정됨 (`user_tenants` 오기 → `tenant_memberships` 실제 테이블명) — Phase 3-0 wire 정합. **DO NOT use `user_tenants` in any NEW frontend code**.
- **AAL check**: `supabase.auth.getSession()` 의 `access_token` payload 의 `aal` claim 은 Phase 3 wire 진입 시점에 Supabase session payload 에 포함 여부 verify 필요. 미포함 시 fallback to `auth.getUser(jwt)` + `aal` claim read from `user.app_metadata.aal`. Epic 12 wire 정합 sweep 결정.
- **2FA gate middleware conflict**: middleware 에서 2FA gate 강제 시 미로그인 사용자가 `/login` → `/account/security?reason=2fa_required` 로 redirect 되는 무한 루프 회피. `?reason=2fa_required` query param 일 때 middleware bypass 결정 wire.

## Previous Story Intelligence

### Phase 3 PRD entry (`phase-3-prd-entry: done`, 2026-08-20)
- master PRD v2.5 → v3.0 atomic edit
- §F15 신규 (F15.1~F15.6 verbatim)
- AD-26 Auth Foundation 신규 결정
- capability matrix v1.23 → v1.24 EXTENSION (5 NEW rows 이미 추가됨, capability.py enum 만 wire)
- A65+A66+A67+A68+A69 신규 결정 wire
- handoff: `memory/handoff-2026-08-20-phase-3-prd-entry-done.md`

### Phase 3-0 auth contract slice (`phase-3-0-auth-contract-slice: done`, 2026-08-21)
- wire_commit = `1db21d2`
- P0 3종 ALL RESOLVED: GUC name split + custom_access_token_hook + signup path
- 15 files atomic (5 NEW + 9 MODIFIED + 1 alembic)
- 43 NEW pytest PASS (8 + 14 + 21)
- 3중 게이트 FINAL CLEAN
- handoff: `memory/handoff-2026-08-21-phase-3-0-auth-contract-slice-done.md`

### Epic 1 partial scaffold (PRESERVE)
- `apps/web/app/[locale]/(auth)/layout.tsx` minimal shell (existing)
- `apps/web/app/[locale]/(auth)/onboarding/industry/page.tsx` (existing)
- `apps/web/components/onboarding/IndustrySelector.tsx` (existing)
- `apps/web/components/onboarding/IndustryCard.tsx` (existing)
- `apps/web/middleware.ts` next-intl only (existing, EXTENSION 대상)

### Epic 12 wire (PRESERVE — 2FA gate EXTENSION 정합)
- `apps/web/components/auth/TwoFactorChallenge.tsx` (existing 또는 신규)
- `apps/web/components/auth/TwoFactorSetupForm.tsx` (existing, Epic 12 12-5 wire)
- `apps/web/app/[locale]/account/security/page.tsx` (existing, Epic 12 12-5 wire)
- `Capability.TWO_FACTOR_AUTH` industry-agnostic (Epic 12 12-1 wire)
- `ActionClass.TWO_FACTOR_AUTH` 6 NEW values (Epic 12 12-1 wire)

### Story 9-7 frontend test debt follow-up (REFERENCE)
- `apps/web/mocks/handlers.ts` EXTENSION pattern — POST /api/v1/abc/validate handler reference
- 5 NEW vitest component tests (AbcDispatchPanel + AbcDispatchDecisionBadge + AbcDispatchResultCard + AbcDispatchErrorToast + AbcValidationForm)
- 3 NEW TS mirror parity tests (m9-abc-dispatch + report21 + report21-pdf)

## Git Intelligence Summary

### Last 5 commit titles (analysis)

1. `1db21d2` — Phase 3-0 auth contract slice DONE (15 files atomic, 43 NEW pytest)
2. `7c6aaa9` — Phase 3-0 sprint-status follow-up docs-only wire
3. `9085a03` — Phase 3 PRD entry (master PRD v2.5 → v3.0)
4. `3020823` — Phase 2 close-out (baseline 42 failed → 0 failed)
5. `7835463` — Story 14.1 bmad-dev-story atomic wire DONE

### Patterns established (apply to current story)

- **Single atomic commit** per sprint (T1~T8 in single atomic commit, CR 11-3 discipline)
- **2 atomic commits** if frontend + backend + docs must be separated (rare)
- **3중 게이트 FINAL CLEAN** mandatory before commit
- **A36 SDR 검증 4-step 자동 적용** (commit prefix lint + sprint-status structure + vitest file count drift + commit consistency)
- **CR 9-6 D5 prevention**: `git commit -F <file>` (NOT PowerShell here-string)

### Files created/modified in last sprint (relevant to Phase 3)

- `apps/api/core/security.py` EXTENSION (ALLOWED_ROLES + JWTClaims.tenant_id Optional + decode_jwt require_tenant kwarg) — **PRESERVE**
- `apps/api/core/tenant_context.py` EXTENSION (set_claims/clear_claims + 3-GUC publisher + PreOnboardingUser) — **PRESERVE**
- `apps/api/modules/m0_onboarding/handlers.py` EXTENSION (signup_router + POST endpoint) — **PRESERVE**
- `apps/api/modules/m0_onboarding/services/signup_service.py` NEW (atomic 5-step + 2 typed exceptions) — **PRESERVE**
- `apps/api/alembic/versions/0035_custom_access_token_hook.py` NEW — **PRESERVE**
- `supabase/config.toml` EXTENSION (custom_access_token_hook enabled = true) — **PRESERVE**

## References

- [Source: _bmad-output/planning-artifacts/prd.md#F15] — master PRD §F15 (Auth Foundation) verbatim
- [Source: _bmad-output/planning-artifacts/prd.md#F15.1] — Login UI + Supabase SSR Auth Client
- [Source: _bmad-output/planning-artifacts/prd.md#F15.2] — Signup UI + Tenant Creation Flow
- [Source: _bmad-output/planning-artifacts/prd.md#F15.3] — Auth Middleware EXTENSION
- [Source: _bmad-output/planning-artifacts/prd.md#F15.4] — Logout Flow + Korean SSOT
- [Source: _bmad-output/planning-artifacts/prd.md#F15.5] — Forgot-Password UI + Supabase resetPasswordForEmail
- [Source: _bmad-output/planning-artifacts/prd.md#F15.6] — Tests + Wire Scope T1~T8
- [Source: _bmad-output/planning-artifacts/prd.md#AD-26] — Auth Foundation 신규 결정
- [Source: docs/capability-matrix.md#v1.24] — capability matrix v1.24 EXTENSION (5 NEW rows already added)
- [Source: docs/architecture-decisions/] — AD 인벤토리 (AD-26 신규 추가 시)
- [Source: docs/conventions.md] — §13.1 ko-KR SSOT 1권 강제 + ESLint rule forbid-non-ko-KR-keys
- [Source: docs/STACK_PIN.yaml] — frontend 의존성 pin 검증 (Supabase SSR 라이브러리 version 검증)
- [Source: _bmad-output/implementation-artifacts/handoff-2026-08-20-phase-3-prd-entry-done.md] — A65~A69 결정
- [Source: _bmad-output/implementation-artifacts/handoff-2026-08-21-phase-3-0-auth-contract-slice-done.md] — Phase 3-0 wire 15 files
- [Source: apps/web/middleware.ts] — Epic 1 partial scaffold next-intl only (EXTENSION 대상)
- [Source: apps/web/app/[locale]/(auth)/layout.tsx] — Epic 1 partial scaffold minimal shell (PRESERVE)
- [Source: apps/api/core/capability.py] — Capability enum (5 NEW entries wire 진입)
- [Source: apps/web/messages/ko-KR.json] — ko-KR SSOT 1권 (4 NEW namespaces)

## Open Questions

- **OQ-1**: `supabase.auth.getSession()` 의 `aal` claim read pattern — Supabase session payload 에 `aal` claim 직접 포함 vs `auth.getUser(jwt)` 의 `user.app_metadata.aal` read. 결정 wire 진입 시점: T2.2 (LoginForm 2FA redirect logic) 진입 시.
- **OQ-2**: 5회 cool-down 로직 storage — in-memory counter (server restart 시 reset) vs sessionStorage (browser-only) vs DB-backed (Supabase `auth.failed_login_attempts` table). 결정 wire 진입 시점: T2.3 (login.ts wrapper) 진입 시.
- **OQ-3**: Phase 3 wire commit 진입 후 `Task #5 종단 증명` (Docker Desktop start 후 real Supabase token → `/api/v1/*` 200 + cross-tenant 격리 확인) 시점. Phase 3 wire 완료 후 결정.

## Dev Agent Record

### Agent Model Used

claude-opus-4 (cj-style Phase 3 2번째 진입점 = cj-style 50번째 epic 연속 정직 회복)

### Debug Log References

### Completion Notes List

### File List

- [ ] `apps/web/lib/supabase/env.ts` (NEW, T1.1)
- [ ] `apps/web/lib/supabase/server.ts` (NEW, T1.2)
- [ ] `apps/web/lib/supabase/client.ts` (NEW, T1.3)
- [ ] `apps/web/lib/supabase/types.ts` (NEW, T1.4)
- [ ] `apps/web/lib/supabase/middleware.ts` (NEW, T1.5)
- [ ] `apps/web/lib/auth/login.ts` (NEW, T2.3)
- [ ] `apps/web/lib/auth/signup.ts` (NEW, T3.3)
- [ ] `apps/web/lib/auth/middleware.ts` (NEW, T4.2)
- [ ] `apps/web/lib/auth/logout.ts` (NEW, T5.3)
- [ ] `apps/web/lib/auth/forgot-password.ts` (NEW, T6.5)
- [ ] `apps/web/lib/auth/reset-password.ts` (NEW, T6.6)
- [ ] `apps/web/app/[locale]/(auth)/login/page.tsx` (NEW, T2.1)
- [ ] `apps/web/app/[locale]/(auth)/signup/page.tsx` (NEW, T3.1)
- [ ] `apps/web/app/[locale]/(auth)/email-verification-pending/page.tsx` (NEW, T3.4)
- [ ] `apps/web/app/[locale]/(auth)/forgot-password/page.tsx` (NEW, T6.1)
- [ ] `apps/web/app/[locale]/(auth)/reset-password/page.tsx` (NEW, T6.3)
- [ ] `apps/web/app/[locale]/api/auth/logout/route.ts` (NEW, T5.1)
- [ ] `apps/web/components/auth/LoginForm.tsx` (NEW, T2.2)
- [ ] `apps/web/components/auth/SignupForm.tsx` (NEW, T3.2)
- [ ] `apps/web/components/auth/LogoutButton.tsx` (NEW, T5.2)
- [ ] `apps/web/components/auth/ForgotPasswordForm.tsx` (NEW, T6.2)
- [ ] `apps/web/components/auth/ResetPasswordForm.tsx` (NEW, T6.4)
- [ ] `apps/web/middleware.ts` (MODIFIED, T4.1)
- [ ] `apps/web/messages/ko-KR.json` (MODIFIED, T2.4 + T3.5 + T5.4 + T6.7)
- [ ] `apps/api/core/capability.py` (MODIFIED, T7.1 + T7.2)
- [ ] `tests/web/test_auth_login_parity.py` (NEW, T8.1)
- [ ] `tests/web/test_auth_signup_parity.py` (NEW, T8.2)
- [ ] `tests/web/test_auth_middleware_parity.py` (NEW, T8.3)
- [ ] `tests/web/test_auth_logout_parity.py` (NEW, T8.4)
- [ ] `tests/web/test_auth_forgot_password_parity.py` (NEW, T8.5)
- [ ] `tests/integration/test_auth_endpoints_e2e.py` (NEW, T8.6)
- [ ] `tests/integration/test_capability_matrix_v1_24_drift.py` (NEW, T7.4)
- [ ] `docs/auth-foundation.md` (NEW, T8.8)
- [ ] `memory/handoff-2026-08-21-phase-3-1-auth-foundation-wire-done.md` (NEW, T8.9)
- [ ] `_bmad-output/implementation-artifacts/sprint-status.yaml` (MODIFIED, T8.7)

---

## A19 cohesion pattern 9 surface EXTENSION PASS 결정

- **Surface 1 (kernel)** = T1 Supabase SSR client STD/Edge variant (`apps/web/lib/supabase/server.ts` + `client.ts` + `middleware.ts`)
- **Surface 2 (port)** = T2+T3+T6 Client Components (`<LoginForm>` / `<SignupForm>` / `<ForgotPasswordForm>` / `<ResetPasswordForm>`)
- **Surface 3 (db schema)** = T3 tenant creation backend callback (Phase 3-0 wire `SignupService.complete_signup()` atomic 5-step)
- **Surface 4 (service)** = T1+T2+T3+T5+T6 `lib/auth/*.ts` wrappers (login + signup + middleware + logout + forgot-password + reset-password)
- **Surface 5 (handler)** = T4 middleware EXTENSION + T5 logout route handler (`/api/auth/logout`)
- **Surface 6 (envelope)** = T2+T3+T5+T6 ko-KR 에러 메시지 (CR 12-5 D-14 envelope `{code, message_ko, details, trace_id}`)
- **Surface 7 (capability)** = T7 LOGIN + SIGNUP + AUTH_MIDDLEWARE + FORGOT_PASSWORD + LOGOUT 5 NEW gates (industry-agnostic)
- **Surface 8 (audit)** = T3 tenant_signup_completed (Phase 3-0 wire) + T5 user_logged_out + T6 password_reset (CR 1-1 audit-first INSERT 3-row)
- **Surface 9 (auth) NEW** = T1~T6 SSR client + Server Components + Client Components + Middleware + Server Actions / Route Handlers

## D-1-1-DEFER-* honestly DEFER preserved (CR 11-3 49번째 epic 연속)

- **D-1-1-DEFER-1** (Magic link login) — honestly preserved (Phase 3 close-out retro 진입 시점에 결정 wire 보존)
- **D-1-1-DEFER-2** (Social login OAuth — Google/Naver/Kakao) — honestly preserved
- **D-1-1-DEFER-3** (SSO enterprise SAML) — honestly preserved

Story 1.1 F-1 (Supabase SSR client wire) + F-4 (accessToken string pass) + F-30 (rls_db fixture wire) 모두 Phase 3 T1 wire 진입 시점에 honestly RESOLVE 결정 wire 진입 ✅.
Story 1.1 F-2 (next-intl i18n bundle) + F-3 (IndustryCard UI polish) + F-5~F-29 (Epic 1 carry-over 25 items) preserved.

## CR 11-3 honest-DEFER 49번째 epic 연속

A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS) + CR 12-5 D-GATE-01 + D-PARITY-01 inversion 적용 보존 + A19 + CR 0-2 RLS lesson + CR 1-1 audit-first INSERT + CR 9-6 commit message discipline 모두 적용 보존.

## 결정 wire 일자

2026-08-21 (KST)

## next

Phase 3 cj-style 2번째 진입점 (본 스토리) = cj-style 50번째 epic 연속 정직 회복 wire 진입 대기 → `bmad-dev-story phase-3-1-auth-foundation-wire` T1~T8 atomic wire 진입.
Task #5 종단 증명 (Docker Desktop 기동 후) OR Phase 3 close-out retro 진입 결정 wire 보존.
