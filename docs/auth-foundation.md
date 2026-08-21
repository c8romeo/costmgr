# Auth Foundation (Phase 3-1)

> Status: **Active** (Phase 3-1 wire DONE 2026-08-21, cj-style Phase 3 2번째 = 50번째 epic 연속 정직 회복)
> Owner: Frontend (apps/web) + Backend (apps/api) cross-team
> Source spec: `docs/capability-matrix.md` v1.24 + `prd.md` §F15 + AD-26

## 1. 목적 (Purpose)

이 문서는 Phase 3-1 에서 wire 한 **Auth Foundation** (로그인 / 회원가입 / 로그아웃 / 비밀번호 재설정 + middleware) 의
구현 contract 를 single source 로 정리한다. PRD §F15 + master PRD §F15.1~§F15.6 + capability matrix v1.24 의 5 NEW rows
(LOGIN, SIGNUP, AUTH_MIDDLEWARE, FORGOT_PASSWORD, LOGOUT) 가 모두 이 문서 한 곳에서 map 된다.

## 2. 아키텍처 (Architecture)

Auth Foundation 은 다음 3 layer 의 결합이다:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 1 — Browser (Client Components)                              │
│  apps/web/components/auth/                                           │
│    ├── LoginForm          (5-failure cool-down + AAL 분기)          │
│    ├── SignupForm         (3-step flow call)                        │
│    ├── LogoutButton       (POST /api/auth/logout)                   │
│    ├── ForgotPasswordForm (always-success security invariant)        │
│    └── ResetPasswordForm  (password strength + mismatch check)      │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 2 — Edge Runtime (Next.js middleware)                        │
│  apps/web/middleware.ts + apps/web/lib/auth/middleware.ts            │
│    ├── Supabase SSR Edge session refresh (sb-access-token cookie)    │
│    ├── routeGuard: (dashboard)/* protected, (auth)/* public,        │
│    │                /api/v1/* bypass, 2FA gate (aal1 → security)    │
│    └── Edge Runtime export (CR 11-4 LLM default 바꾸기 방지)         │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 3 — Backend (FastAPI + Supabase)                              │
│  apps/api/modules/m0_onboarding/ + alembic 0035 + supabase/config   │
│    ├── custom_access_token_hook (alembic 0035)                       │
│    │   → mint 시점에 tenant_id/role/industry 를 app_metadata merge   │
│    ├── POST /api/v1/onboarding/complete-signup (Phase 3-0)           │
│    │   → 5-step atomic transaction (users + tenants + memberships + │
│    │                                  tenant_settings + audit)      │
│    └── get_pre_onboarding_user + decode_jwt(require_tenant=False)    │
│        → tenant_id 가 비어있는 pre-onboarding JWT 도 수용             │
└─────────────────────────────────────────────────────────────────────┘
```

## 3. 세션 / 쿠키 (Session / Cookie)

| 항목 | 값 | 비고 |
|------|------|------|
| Cookie name | `sb-access-token` | Supabase SSR default |
| httpOnly | `true` | XSS 차단 |
| secure | `true` | production |
| sameSite | `lax` | OAuth callback 호환 |
| maxAge | 3600 (1 hour) | Supabase SSR default |
| refresh | middleware 가 매 요청마다 refresh | Layer 2 |

## 4. AAL 분기 (Authenticator Assurance Level)

PRD §F15.3 + Story 12.1 + Epic 12 mandatory 2FA gate 와의 정합.

| Login result | next URL | 이유 |
|--------------|----------|------|
| `aal2` (TOTP 완료) | `/<locale>/dashboard` (또는 `?redirect=`) | 2FA 완료된 session |
| `aal1` (password only) | `/<locale>/account/security?reason=2fa_required` | Epic 12 2FA 미설정 redirect |
| `/dashboard/*` with `aal1` | `/<locale>/account/security?reason=2fa_required` | Edge middleware 2FA gate |

## 5. capability matrix v1.24 EXTENSION

CR 12-1 L4 precedent (industry-agnostic) — 5 NEW enum + 4-industry grants.

```python
# apps/api/core/capability.py
class Capability(str, enum.Enum):
    # ... (21 prior entries + 5 NEW Phase 3-1)
    LOGIN = "login"               # NEW — Phase 3-1
    SIGNUP = "signup"             # NEW — Phase 3-1
    AUTH_MIDDLEWARE = "auth_middleware"  # NEW — Phase 3-1
    FORGOT_PASSWORD = "forgot_password"  # NEW — Phase 3-1
    LOGOUT = "logout"             # NEW — Phase 3-1

# Industry grants — 모두 ✅/✅/✅/✅ (industry-agnostic)
INDUSTRY_CAPABILITIES = {
    Industry.MANUFACTURING: frozenset({
        Capability.LOGIN, Capability.SIGNUP,
        Capability.AUTH_MIDDLEWARE, Capability.FORGOT_PASSWORD, Capability.LOGOUT,
        # ... existing
    }),
    # SERVICE / MANUFACTURING_SERVICE / OTHER 모두 동일
}
```

`docs/capability-matrix.md` v1.24 title + 5 NEW rows.

## 6. ko-KR.json SSOT

CR 11-4 D-002 lesson — i18n key 가 single source of truth (ko-KR.json).

```jsonc
// apps/web/messages/ko-KR.json
{
  "auth": {
    "login": { "email": "이메일", "password": "비밀번호", "submit": "로그인", ... },
    "signup": { "email": "이메일", "password": "비밀번호", "tenantName": "회사/사업장 이름", ... },
    "logout": { "submit": "로그아웃", ... },
    "forgot_password": { "email": "이메일", "submit": "재설정 링크 발송", ... },
    "reset_password": { "newPassword": "새 비밀번호", "confirmPassword": "새 비밀번호 확인", ... }
  }
}
```

## 7. audit-first INSERT (CR 1-1 lesson)

| 액션 | ActionClass | AuditAction | audit-first row |
|------|-------------|-------------|-----------------|
| signup 완료 | `TENANT` | `tenant_signup_completed` | Phase 3-0 |
| logout | (Phase 3-2 deferred) | — | — |
| password_reset | (Phase 3-2 deferred) | — | — |

> Note: Phase 3-1 wire 는 frontend-only wire 이므로 logout / password_reset backend audit endpoint 는
> Phase 3-2 진입 시점에 honestly DEFER preserved wire scope.

## 8. D-1-1-DEFER-* honestly preserved (50번째 epic 연속)

CR 11-3 honest-DEFER discipline 50번째 epic 연속 보존:

- **D-1-1-DEFER-1**: Magic link (passwordless) — 1차 출시 후 진입 시점
- **D-1-1-DEFER-2**: Social login OAuth (Google / Kakao / Naver) — 1차 출시 후 진입 시점
- **D-1-1-DEFER-3**: SSO enterprise SAML — 1차 출시 후 진입 시점

`tests/api/core/test_phase_3_1_auth_wire.py::test_no_magic_link_or_oauth_or_sso_introduced` grep guard 가
이 3 가지 substring (`magic_link` / `magicLink` / `oauth_signin` / `saml_acs` 등) 의 wire 도입을
**명시적으로 차단**한다.

## 9. 보너스 invariant (Security)

1. **5-failure cool-down** (login.ts) — sessionStorage 기반 30초 잠금 (CR 11-4 노하우)
2. **Always-success on forgot-password** (forgot-password.ts) — email 존재 여부 노출 방지
3. **Password strength regex** (login.ts / signup.ts / reset-password.ts) —
   `(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]).{10,}`
4. **AAL branch transparency** — AAL 결정은 middleware 가 `x-user-aal` header 로 express,
   client component 는 단순히 분기만 한다.
5. **Edge runtime explicit** — `middleware.ts` 안에 `export const runtime = 'edge'`
   (CR 11-4 LLM default 바꾸기 방지 — Supabase SSR Edge variant 가 Node runtime 에서 동작 X)

## 10. wire 산출물 (Wire artifacts)

| Task | 상태 | 산출물 |
|------|------|--------|
| T1 (Supabase SSR client) | ✅ | `apps/web/lib/supabase/{server,client,middleware,env,types}.ts` (5 NEW) |
| T2 (Login page) | ✅ | `apps/web/app/[locale]/(auth)/login/page.tsx` + `LoginForm.tsx` + `lib/auth/login.ts` + ko-KR.json EXTENSION |
| T3 (Signup page) | ✅ | `apps/web/app/[locale]/(auth)/signup/page.tsx` + `SignupForm.tsx` + `lib/auth/signup.ts` + email-verification-pending page + ResendVerificationButton |
| T4 (Auth middleware) | ✅ | `apps/web/middleware.ts` EXTENSION + `lib/auth/middleware.ts` NEW |
| T5 (Logout) | ✅ | `apps/web/app/[locale]/api/auth/logout/route.ts` + `LogoutButton.tsx` + `lib/auth/logout.ts` |
| T6 (Forgot/Reset) | ✅ | `app/[locale]/(auth)/forgot-password/page.tsx` + `ForgotPasswordForm.tsx` + `lib/auth/forgot-password.ts` + reset-password equivalent (5 NEW) |
| T7 (Capability v1.24) | ✅ | `apps/api/core/capability.py` EXTENSION (5 NEW enum + 20 grants) + `tests/integration/test_capability_matrix_v1_24_drift.py` |
| T8 (Tests + 3중 게이트) | ✅ | 5 vitest + 1 pytest + docs/auth-foundation.md + handoff memory + sprint-status |

## 11. 결정 wire (Decisions wire)

| ID | 결정 | 근거 |
|----|------|------|
| A65 | Phase 3 PRD entry 진입 (master PRD v2.5 → v3.0 + §F15 신규) | Epic 1 carry-over 정직 회복 |
| A66 | AD-26 Auth Foundation 신규 결정 | Supabase SSR + sb-access-token + next-intl middleware |
| A67 | Capability matrix v1.23 → v1.24 EXTENSION (5 NEW rows) | 1차 출시 wire scope |
| A68 | D-1-1-DEFER-1/2/3 honestly preserved | 50번째 epic 연속 정직 |
| A69 | Phase 3 wire scope T1~T8 결정 + Epic 1 partial scaffold 보존 | 입력 부족 시 wire scope 결정 |

## 12. Cross-references

- PRD: `prd.md` §F15.1~§F15.6 (Phase 3 진입 결정 v3.0)
- Capability matrix: `docs/capability-matrix.md` v1.24
- Spec: `_bmad-output/implementation-artifacts/phase-3-1-auth-foundation-wire.md`
- Handoff: `handoff-2026-08-21-phase-3-1-auth-foundation-wire-done.md`
- Phase 3-0 handoff: `handoff-2026-08-21-phase-3-0-auth-contract-slice-done.md` (custom_access_token_hook)
- AD-26: §부록 A (Auth Foundation)

## 13. Known limitations / Future work

1. **Logout / password-reset backend endpoints** — Phase 3-1 wire 는 frontend-only 이므로
   `POST /api/v1/auth/logout` + `POST /api/v1/auth/password-reset` backend 핸들러는 Phase 3-2 진입 시점에
   honestly DEFER preserved. frontend stub 은 `body = { ok: true, redirect: ... }` 형태로 호출
2. **Audit action types** — `user_logged_out` + `password_reset` ActionClass 등록은 Phase 3-2 진입 결정
3. **D-1-1-DEFER-1/2/3** — 1차 출시 후 진입 결정 wire 보존
4. **Email verification enforcement** — 현재 signup 시 email-verification-pending page 가 표시되지만
   2FA + industry selection 의 gate 진입은 backend 의 `tenant_status` enum 정착 후 결정
