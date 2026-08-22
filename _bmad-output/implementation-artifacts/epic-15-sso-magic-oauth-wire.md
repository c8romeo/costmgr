---
baseline_commit: dd218fa
---

# Story epic-15.1: SSO + Magic Link + Social OAuth Wire (Epic 15 cj-style 2번째 진입점)

Status: in-progress

<!-- Epic 15 cj-style 2번째 진입점 = cj-style 59번째 epic 연속 정직 회복 bmad-create-story spec.
     Epic 15 PRD entry (`epic-15-prd-entry: done`, 2026-08-22, commit `dd218fa`) 직후.
     master PRD v3.2 §F17 verbatim + AD-28 verbatim + A79+A80+A81+A82 결정 wire.
     T1~T8 wire scope (Magic link + Social OAuth Google/Naver/Kakao + SSO enterprise SAML territory) + D-1-1-DEFER-1/2/3 honestly ✅ RESOLVED (58번째 epic 연속 정직 회복). -->

## Story

As a **costmgr product owner**,
I want the **Magic link + Social OAuth (Google/Naver/Kakao) + SSO enterprise SAML 통합 territory fully wired end-to-end with Supabase `signInWithOtp` + `signInWithOAuth` + `python3-saml==1.16.0` AD-14 stack pin + multi-tenant isolation (CR 0-2 RLS) + Epic 12 2FA 게이트 보존**,
so that **Epic 15 territory 가 wire 되어 email-only 매직 링크 + 3 provider 소셜 OAuth + 엔터프라이즈 SSO SAML 로그인이 production-grade 로 동작 + 2FA 미설정 사용자 자동 redirect + capability matrix v1.26 EXTENSION 5 NEW rows industry-agnostic 4-industry grants 모두 production-grade 로 동작 + D-1-1-DEFER-1/2/3 모두 honestly RESOLVE 59번째 epic 연속 정직 회복**합니다.

## Acceptance Criteria

PRD §F17.1 ~ §F17.6 verbatim + AD-28 verbatim + Epic 15 PRD entry (commit `dd218fa`) §F17.6 wire scope T1~T8 결정 verbatim.

### F17.1 Magic link login (D-1-1-DEFER-1 ✅ RESOLVE 진입 wire, A70 결정)

- [ ] **AC1.1** `apps/web/lib/auth/magic-link.ts` NEW (~+40 LOC, atomic) — Supabase `signInWithOtp({ email, options: { emailRedirectTo: \`${SITE_URL}/[locale]/auth-callback\` } })` wrapper 결정 wire (AD-28 verbatim). 5회 cool-down (sessionStorage 30s, Phase 3-1 T2 wire `d3e7454` sessionStorage 패턴 미러 결정). Email 존재 여부 노출 방지 (security invariant try/catch/finally, Phase 3-1 T6 forgot-password 정합) — Supabase `signInWithOtp` 가 throw 해도 항상 generic success envelope 반환. ko-KR envelope `MAGIC_LINK_RATE_LIMITED_KO` / `MAGIC_LINK_SENT_KO` / `MAGIC_LINK_NETWORK_ERROR_KO` 결정 (CR 12-5 D-14 envelope `{code, message_ko, details, trace_id}` 정합).
- [ ] **AC1.2** `apps/web/components/auth/MagicLinkForm.tsx` NEW (~+30 LOC, atomic) — 이메일 단일 필드 UI + `sendMagicLink(email)` 호출 + ko-KR SSOT 사용 (`auth.magic_link.email_label` + `auth.magic_link.send_button`). **D-001 page.tsx mount MUST actual mount** `<MagicLinkForm>` 결정 wire (CR 11-4 D-001 lesson carry, no `<>TODO</>` stubs).
- [ ] **AC1.3** `apps/web/app/[locale]/(auth)/magic-link/page.tsx` NEW (~+30 LOC, atomic) — `(auth)` route group 공개 (Phase 3-1 T4 wire `d3e7454` auth middleware EXTENSION 정합). ko-KR SSOT: `auth.magic_link.title` + `auth.magic_link.subtitle` + `auth.magic_link.email_label` + `auth.magic_link.send_button` + `auth.magic_link.alt_text` ("비밀번호 로그인으로 돌아가기"). capability gate `MAGIC_LINK` (capability matrix v1.26, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러).
- [ ] **AC1.4** `apps/web/app/[locale]/(auth)/magic-link-sent/page.tsx` NEW (~+20 LOC, atomic) — generic success message + ko-KR envelope `MAGIC_LINK_SENT_KO` ("메일함을 확인해 주세요. 로그인 링크가 전송되었습니다."). **Email 존재 여부 노출 방지 강제** — 항상 동일 message 표시 (security invariant preserve).
- [ ] **AC1.5** audit-first INSERT `magic_link_sent` 결정 wire (CR 1-1 verbatim, `audit_logs` table INSERT, action_class='AUTH' + action='magic_link_sent' + actor_id + target_email + trace_id). Phase 3-0 wire `1db21d2` audit_logs table + RLS policy 정합.
- [ ] **AC1.6** Epic 12 2FA 게이트 보존 결정 wire (CR 12-5 D-GATE-01 inversion 적용) — Magic link 성공 후 Epic 12 미설정 사용자 (`users.totp_secret IS NULL`) 는 `/auth/2fa` 로 redirect 결정 wire. Epic 12 wire `a63646c` 정합 sweep.
- [ ] **AC1.7** Magic link callback 시 `supabase.auth.exchangeCodeForSession(code)` + `sb-access-token` cookie session 자동 설정 (Phase 3-1 T1 wire 정합) + `router.push('/dashboard')` 결정 wire (D-001 actual mount validate).

### F17.2 Social OAuth (Google/Naver/Kakao) login (D-1-1-DEFER-2 ✅ RESOLVE 진입 wire, A71 결정)

- [ ] **AC2.1** `apps/web/lib/auth/social.ts` NEW (~+60 LOC, atomic) — Supabase `signInWithOAuth({ provider, options: { redirectTo: \`${SITE_URL}/[locale]/auth-callback\` } })` wrapper 결정 wire (AD-28 verbatim). **Provider whitelist** 결정 wire (`ALLOWED_SOCIAL_PROVIDERS = frozenset({'google', 'naver', 'kakao'})` — strict reject + counter increment 외 value, AD-7 verbatim 정합). Supabase `signInWithOAuth` 가 throw 시 try/catch/finally 결정. ko-KR envelope `SOCIAL_OAUTH_RATE_LIMITED_KO` / `SOCIAL_OAUTH_PROVIDER_DISABLED_KO` / `SOCIAL_OAUTH_NETWORK_ERROR_KO` 결정 (CR 12-5 D-14 envelope 정합).
- [ ] **AC2.2** `apps/web/components/auth/SocialAuthButtons.tsx` NEW (~+60 LOC, atomic) — 3 provider buttons (Google + Naver + Kakao) 결정 wire. 각 button 별 `signInWithSocialOAuth(provider)` 호출 + provider-specific branding (Google: G logo + "구글로 계속하기" / Naver: N logo + "네이버로 계속하기" / Kakao: K logo + "카카오로 계속하기"). `SocialAuthRateLimiter` 결정 (3회 cool-down 60s, magic link 와 분리 sessionStorage 60s 결정).
- [ ] **AC2.3** **Naver OAuth Option A/B 결정 wire 보존** (2026-08-22 KST, 한국 시장 정합) — Supabase `signInWithOAuth` 가 Naver 공식 지원 여부 결정. Option A: Supabase Naver 지원 시 그대로 사용 / Option B: Supabase 미지원 시 custom Naver OAuth flow wire (`apps/web/app/api/auth/social/naver/route.ts` + Naver OAuth API integration). Epic 15-1 bmad-dev-story 진입 시점에 Option A vs B 결정. 본 Epic 15 PRD entry 진입 시점에 **Option A 우선 시도 + Option B fallback 결정 wire 보존**.
- [ ] **AC2.4** OAuth callback handler `apps/web/app/[locale]/(auth)/auth-callback/page.tsx` NEW (~+50 LOC, atomic) — magic link callback + social OAuth callback 통합 handler 결정. `supabase.auth.exchangeCodeForSession(code)` + `sb-access-token` cookie session 자동 설정 (Phase 3-1 T1 wire 정합) + `router.push('/dashboard')` 결정. **D-001 actual mount validate** (CR 11-4 D-001).
- [ ] **AC2.5** audit-first INSERT `social_oauth_initiated` 결정 wire (CR 1-1 verbatim, `audit_logs` table INSERT, action_class='AUTH' + action='social_oauth_initiated' + actor_id + provider + trace_id).
- [ ] **AC2.6** Epic 12 2FA 게이트 보존 (CR 12-5 D-GATE-01 inversion) — Social OAuth 성공 후 Epic 12 미설정 사용자 `/auth/2fa` redirect 결정 wire.
- [ ] **AC2.7** capability gates `SOCIAL_OAUTH_GOOGLE` + `SOCIAL_OAUTH_NAVER` + `SOCIAL_OAUTH_KAKAO` 3 NEW (capability matrix v1.26, industry-agnostic 4-industry grants ✅/✅/✅/✅). 미허용 tenant 진입 차단 결정 wire (SSOT RED→GREEN EXTENSION).

### F17.3 SSO enterprise SAML (D-1-1-DEFER-3 ✅ RESOLVE 진입 wire, A72 결정)

- [ ] **AC3.1** `apps/api/modules/auth/sso/saml_validator.py` NEW (~+150 LOC, atomic) — `python3-saml==1.16.0` library 사용 (AD-14 stack pin 결정, `requirements.txt` MODIFIED). SAML response XML schema validation + signature verification (IdP public key cert 검증) + `NotBefore` / `NotOnOrAfter` timestamp 검증 + `Audience` 검증 (ACS URL 매칭) + `Destination` 검증 + `InResponseTo` 검증 (CSRF 방어) + RelayState 검증 (base64 encode) 결정. ko-KR envelope `SSO_INVALID_RESPONSE_KO` / `SSO_EXPIRED_KO` / `SSO_SIGNATURE_FAILED_KO` 결정 (CR 12-5 D-14 envelope).
- [ ] **AC3.2** `apps/api/modules/auth/sso/saml_routes.py` NEW (~+100 LOC, atomic) — 4 SSO routes 결정 wire — (1) `GET /api/v1/auth/sso/login?tenant_slug=<slug>&relay_state=<url>` SAML AuthnRequest 생성 + IdP SSO URL redirect (HTTP 302) + SAMLRequest XML sign + RelayState base64 encode / (2) `POST /api/v1/auth/sso/acs` SAML ACS endpoint — SAML response POST 받음 + `saml_validator` 호출 + `jit_provisioning` 호출 + `sb-access-token` cookie set + 200 OK / (3) `GET /api/v1/auth/sso/metadata?tenant_slug=<slug>` SP metadata XML 반환 / (4) `GET /api/v1/auth/sso/sls` Single Logout Service endpoint.
- [ ] **AC3.3** `apps/api/modules/auth/sso/jit_provisioning.py` NEW (~+100 LOC, atomic) — JIT (Just-In-Time) user provisioning 결정 wire. SAML response 에서 `NameID` + email + displayName 추출 → 미존재 시 자동 atomic 5-step flow (Phase 3-0 `tenant_signup_completed` 정합 sweep 패턴 미러) — (1) `users` INSERT / (2) `audit_log` `signup_started` / (3) `tenants` INSERT (tenant_slug → tenant_id 매칭) / (4) `tenant_memberships` INSERT (role='member' 기본값, owner 가 별도 invite 결정) / (5) `external_identities` INSERT (alembic 0037). EPIC 12 Epic 12 wire 정합 sweep (2FA 챌린지 후 M2 진입).
- [ ] **AC3.4** `apps/api/alembic/versions/0037_epic_15_sso_external_identities.py` NEW (~+80 LOC, atomic) — `external_identities` table 신규 (id + provider TEXT enum `magic_link | google | naver | kakao | saml_okta | saml_azure_ad | saml_google_workspace | saml_custom` + provider_user_id TEXT + tenant_id UUID + user_id UUID + linked_at + last_used_at + metadata JSONB 결정). 4 indexes (provider+provider_user_id UNIQUE + user_id+provider + tenant_id+provider + last_used_at DESC) + 2 CHECK constraints (provider enum + provider_user_id NOT EMPTY) 결정. **Multi-tenant isolation** 결정 wire (CR 0-2 RLS lesson 적용, AD-22 verbatim): RLS policy `tenant_id = (SELECT current_setting('app.tenant_id'))::uuid` 결정. RLS 5-policy split (3 ALLOW + 2 BLOCK, AD-2 verbatim 보존). down_revision = `0036_phase_4_backup_strategy` 결정 wire (Phase 4 wire `71a033a` 정합).
- [ ] **AC3.5** `apps/web/app/api/auth/sso/callback/route.ts` NEW (~+30 LOC, atomic) — SAML ACS callback 후 `sb-access-token` cookie set 후 `/dashboard` redirect 결정 (Phase 3-1 T1 wire 정합). Sentry breadcrumb 추가 결정 (F4 observability EXTENSION, F16.5 wire 정합).
- [ ] **AC3.6** `apps/web/app/[locale]/sso/[tenant_slug]/login/page.tsx` NEW (~+40 LOC, atomic) — `/sso/<tenant_slug>/login` 진입 시 `GET /api/v1/auth/sso/login?tenant_slug=<slug>&relay_state=<original_path>` redirect 결정. Tenant slug 별로 다른 IdP metadata 사용 결정 (multi-tenant SSO routing). Epic 12 2FA 정합 — SSO 성공 후에도 2FA 미설정 시 `/auth/2fa` redirect 결정 wire.
- [ ] **AC3.7** audit-first INSERT `sso_identity_linked` 결정 wire (CR 1-1 verbatim, `audit_logs` table INSERT, action_class='AUTH' + action='sso_identity_linked' + actor_id + provider + provider_user_id + tenant_id).
- [ ] **AC3.8** Capability gate `SSO_ENTERPRISE` (capability matrix v1.26, industry-agnostic 4-industry grants ✅/✅/✅/✅). 미허용 tenant 의 SSO 진입 차단 결정 wire.

### F17.4 ko-KR SSOT EXTENSION (`apps/web/messages/ko-KR.json`)

- [ ] **AC4.1** **Magic link namespace EXTENSION 결정**: `auth.magic_link.title` ("매직 링크로 로그인") + `auth.magic_link.subtitle` ("이메일로 전송된 링크를 클릭하면 로그인됩니다") + `auth.magic_link.email_label` ("이메일 주소") + `auth.magic_link.send_button` ("매직 링크 전송") + `auth.magic_link.sent_message` ("메일함을 확인해 주세요. 로그인 링크가 전송되었습니다.") + `auth.magic_link.alt_text` ("비밀번호 로그인으로 돌아가기") + `auth.magic_link.error.rate_limited` ("너무 많은 요청이 있었습니다. 30초 후 다시 시도해 주세요.") + `auth.magic_link.error.network` ("네트워크 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.").
- [ ] **AC4.2** **Social OAuth namespace EXTENSION 결정**: `auth.social.divider_or` ("또는") + `auth.social.google_button` ("구글로 계속하기") + `auth.social.naver_button` ("네이버로 계속하기") + `auth.social.kakao_button` ("카카오로 계속하기") + `auth.social.error.rate_limited` ("너무 많은 요청이 있었습니다. 60초 후 다시 시도해 주세요.") + `auth.social.error.provider_disabled` ("이 로그인 방식은 현재 사용할 수 없습니다") + `auth.social.error.network` ("네트워크 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.").
- [ ] **AC4.3** **SSO namespace EXTENSION 결정**: `auth.sso.enterprise_button` ("엔터프라이즈 SSO 로그인") + `auth.sso.tenant_label` ("회사 도메인") + `auth.sso.continue_button` ("SSO 로그인 계속") + `auth.sso.error.invalid_tenant` ("유효하지 않은 회사 도메인입니다") + `auth.sso.error.redirecting` ("SSO 제공업체로 리다이렉트 중...") + `auth.sso.error.invalid_response` ("SSO 응답이 유효하지 않습니다") + `auth.sso.error.expired` ("SSO 세션이 만료되었습니다. 다시 로그인해 주세요.") + `auth.sso.error.signature_failed` ("SSO 서명 검증에 실패했습니다. 시스템 관리자에게 문의하세요.").
- [ ] **AC4.4** ko-KR.json SSOT EXTENSION 결정 wire (Phase 3-1 T2 wire `d3e7454` SSOT 패턴 verbatim bind). CR 12-5 D-14 typed exception envelope 정합. **D-002 ko-KR.json SSOT only** lesson carry (CR 11-4 D-002, no `lib/ko-KR.json` dual-file). **P-015 ko-KR.json SSOT drift detector** EXTENSION — epic-15 namespace 검출 추가 결정.

### F17.5 Capability matrix v1.25 → v1.26 EXTENSION 5 NEW rows 결정 (A81 결정)

- [ ] **AC5.1** `Capability.MAGIC_LINK = "magic_link"` 4-industry grants: manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ (industry-agnostic, CR 12-1 L4 precedent 미러, `LOGIN`/`SIGNUP`/`AUTH_MIDDLEWARE`/`FORGOT_PASSWORD`/`LOGOUT` Phase 3-1 wire pattern + `LISTEN_NOTIFY`/`LISTEN_NOTIFY_TENANT_FANOUT`/`LISTEN_NOTIFY_MULTIPROCESS` Epic 13/14 wire pattern + `DEPLOYMENT_PROD`/`DEPLOYMENT_STAGING`/`DEPLOYMENT_DATABASE_BACKUP`/`DEPLOYMENT_HEALTH_CHECK` Phase 4 wire pattern verbatim bind).
- [ ] **AC5.2** `Capability.SOCIAL_OAUTH_GOOGLE = "social_oauth_google"` 동일 industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정.
- [ ] **AC5.3** `Capability.SOCIAL_OAUTH_NAVER = "social_oauth_naver"` 동일 industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정.
- [ ] **AC5.4** `Capability.SOCIAL_OAUTH_KAKAO = "social_oauth_kakao"` 동일 industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정.
- [ ] **AC5.5** `Capability.SSO_ENTERPRISE = "sso_enterprise"` 동일 industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정.
- [ ] **AC5.6** 미허용 tenant 의 magic link / social OAuth / SSO enterprise 진입 차단 결정 wire (SSOT RED→GREEN EXTENSION, capability matrix v1.26 신규 5 rows + `require_capability()` Dependency 5개 신규 wire — `apps/api/dependencies/capability.py` EXTENSION 결정).
- [ ] **AC5.7** `docs/capability-matrix.md` v1.25 → v1.26 EXTENSION (5 NEW rows, SSOT RED→GREEN EXTENSION) 결정 wire — Epic 15 PRD entry commit `dd218fa` 진입 시점에 이미 5 NEW rows 추가됨, capability.py enum 만 wire 진입.

### F17.6 OAuth callback + auth middleware EXTENSION + tests (T1~T8 wire scope 결정)

- [ ] **AC6.1** `apps/web/middleware.ts` MODIFIED — auth-callback route 추가 (magic link callback + OAuth callback 통합 handler 결정). Phase 3-1 T4 wire `d3e7454` middleware.ts EXTENSION 정합.
- [ ] **AC6.2** `apps/web/app/[locale]/(auth)/login/page.tsx` MODIFIED — 3 NEW auth method entry points 진입: magic link (`/magic-link`) + social OAuth (`SocialAuthButtons` component inline render) + SSO enterprise (`/sso/<tenant_slug>/login` 진입 link) 결정. Phase 3-1 T2 wire `d3e7454` `LoginForm.tsx` EXTENSION 정합.
- [ ] **AC6.3** `apps/api/main.py` MODIFIED — `sso_router` include 결정 (`apps/api/modules/auth/sso/saml_routes.py` router prefix `/api/v1/auth/sso`). `auth_router` EXTENSION 결정 wire 보존.
- [ ] **AC6.4** `requirements.txt` MODIFIED — `python3-saml==1.16.0` AD-14 stack pin 결정 wire. STACK_PIN.md EXTENSION 결정 wire 보존.
- [ ] **AC6.5** `apps/web/package.json` MODIFIED — `@supabase/supabase-js` `signInWithOAuth` EXTENSION 결정 (Phase 3-1 T1 wire `d3e7454` 에서 이미 `^2.112.3` 결정 wire 진입, magic link + OAuth EXTENSION 결정 wire 보존).

### F17.7 Tests + atomic commit + 3중 게이트 FINAL CLEAN

- [ ] **AC7.1** `tests/web/test_epic_15_magic_link_parity.test.ts` NEW (~+15 vitest cases) — `MagicLinkForm` 15 RTL cases (D-003 vitest RTL render discipline, CR 11-4 D-003) + `signInWithOtp` 5회 cool-down + email 존재 여부 노출 방지 (try/catch/finally invariant) + audit-first INSERT `magic_link_sent` + Epic 12 2FA redirect.
- [ ] **AC7.2** `tests/web/test_epic_15_social_oauth_parity.test.ts` NEW (~+15 vitest cases) — `SocialAuthButtons` 3 provider buttons + provider whitelist strict reject (`ALLOWED_SOCIAL_PROVIDERS` frozenset 외 value REJECT) + 3회 cool-down + audit-first INSERT `social_oauth_initiated` + `exchangeCodeForSession` callback handler.
- [ ] **AC7.3** `tests/api/core/test_epic_15_sso_validator.py` NEW (~+15 pytest cases) — `python3-saml` SAML response validation + signature + timestamp (`NotBefore` / `NotOnOrAfter`) + Audience + Destination + InResponseTo + RelayState + expired handling + signature failure. ko-KR envelope 정합.
- [ ] **AC7.4** `tests/api/core/test_epic_15_sso_jit_provisioning.py` NEW (~+10 pytest cases) — JIT user provisioning 5-step atomic flow + `external_identities` INSERT + multi-tenant isolation RLS policy (CR 0-2 RLS lesson) + audit-first INSERT `sso_identity_linked`.
- [ ] **AC7.5** `tests/api/core/test_epic_15_sso_routes.py` NEW (~+15 pytest cases) — 4 routes 검증 — (1) `/api/v1/auth/sso/login` SAML AuthnRequest 생성 + IdP redirect (HTTP 302) / (2) `/api/v1/auth/sso/acs` SAML ACS endpoint response 검증 / (3) `/api/v1/auth/sso/metadata` SP metadata XML 반환 검증 / (4) `/api/v1/auth/sso/sls` logout response 검증 + tenant slug routing multi-tenant SSO.
- [ ] **AC7.6** `tests/api/core/test_epic_15_alembic_0037_external_identities.py` NEW (~+10 pytest cases) — alembic 0037 migration code-shape 검증 (Story 9-7 T9 패턴 미러) + `external_identities` table schema + RLS policy + indexes + CHECK constraints + down_revision=`0036_phase_4_backup_strategy` 정합.
- [ ] **AC7.7** `tests/integration/test_capability_matrix_v1_26_drift.py` NEW (drift detector — 5 NEW rows SSOT 정합 sweep) — `MAGIC_LINK` + `SOCIAL_OAUTH_GOOGLE` + `SOCIAL_OAUTH_NAVER` + `SOCIAL_OAUTH_KAKAO` + `SSO_ENTERPRISE` SSOT 정합 sweep (P-015 ko-KR.json SSOT drift detector 패턴 미러).
- [ ] **AC7.8** `docs/sso-enterprise.md` NEW (~+150 LOC, 10 sections) — purpose + SAML 2.0 spec overview + IdP metadata + SP metadata + AuthnRequest flow + Assertion Consumer Service + JIT user provisioning + multi-tenant routing + audit log + security best practices + troubleshooting 결정 wire (AD-28 verbatim 정합).
- [ ] **AC7.9** 3중 게이트 FINAL CLEAN — (1) `pnpm tsc --noEmit` 0 NEW errors (Epic 15 auth files clean — pre-existing 7 baseline errors unrelated 보존) / (2) `pnpm vitest run` 716+50 = **~766/766 PASS** (71+5 = 76 files, Epic 15 +50 NEW vitest cases, 0 regressions) / (3) `ruff check` scoped Epic 15 wire files = **All checks passed!** (scoped to Epic 15 NEW Python files only) / (4) `pytest` 31+50 = **~81/81 PASS** (Epic 15 +50 NEW pytest e2e tests, 0 NEW regressions; baseline 1 unrelated pre-existing failure `test_generate_report_pdf_report15_payload_not_required` 보존) / (5) SDR drift gate PASS (MAX claim 3928 → **~3978** actual pytest --collect-only -q = +50 from Epic 15 T7~T8 NEW pytest cases).
- [ ] **AC7.10** **A36 SDR 검증 4-step 자동 적용 PASS** — (1) commit prefix lint (CR 9-6 D5 prevention) / (2) sprint-status structure 정합 (D4 fix 보존) / (3) vitest file count drift 0건 (D2 fix 보존) / (4) commit consistency 정합 (D1 fix 보존).
- [ ] **AC7.11** atomic commit + sprint-status `epic-15-sso-magic-oauth-wire: in-progress → done` + handoff memory 신규 + `docs/sso-enterprise.md` NEW + `apps/web/messages/ko-KR.json` 3 NEW namespace EXTENSION (`auth.magic_link.*` + `auth.social.*` + `auth.sso.*`).

## Tasks / Subtasks

- [ ] **Task 1 — T1: Magic link wrapper + rate limiter wire** (AC: #1.1, #1.5)
  - [ ] Subtask 1.1 — `apps/web/lib/auth/magic-link.ts` NEW (~+40 LOC): Supabase `signInWithOtp({ email, options: { emailRedirectTo } })` wrapper + 5회 cool-down sessionStorage 30s + email 존재 여부 노출 방지 (try/catch/finally) 결정
  - [ ] Subtask 1.2 — `magic-link.ts` audit-first INSERT `magic_link_sent` (CR 1-1 verbatim, action_class='AUTH' + action='magic_link_sent' + actor_id + target_email + trace_id) 결정

- [ ] **Task 2 — T2: Magic link UI wire** (AC: #1.2, #1.3, #1.4, #1.6, #1.7, #6.1, #6.2)
  - [ ] Subtask 2.1 — `apps/web/components/auth/MagicLinkForm.tsx` NEW (~+30 LOC): 이메일 단일 필드 UI + ko-KR SSOT 사용 + `sendMagicLink()` 호출 + D-001 actual mount validate 결정
  - [ ] Subtask 2.2 — `apps/web/app/[locale]/(auth)/magic-link/page.tsx` NEW (~+30 LOC): `(auth)` route group 공개 + capability gate `MAGIC_LINK` 정합 결정
  - [ ] Subtask 2.3 — `apps/web/app/[locale]/(auth)/magic-link-sent/page.tsx` NEW (~+20 LOC): generic success message + email 존재 여부 노출 방지 강제 결정
  - [ ] Subtask 2.4 — `apps/web/app/[locale]/(auth)/auth-callback/page.tsx` NEW (~+50 LOC): magic link callback + `exchangeCodeForSession` + session cookie setting + Epic 12 2FA redirect 결정

- [ ] **Task 3 — T3: Social OAuth wrapper + buttons wire** (AC: #2.1, #2.2, #2.3, #2.5, #2.6, #2.7)
  - [ ] Subtask 3.1 — `apps/web/lib/auth/social.ts` NEW (~+60 LOC): `signInWithSocialOAuth(provider)` wrapper + provider whitelist (`ALLOWED_SOCIAL_PROVIDERS` frozenset) + 3회 cool-down sessionStorage 60s + audit-first INSERT `social_oauth_initiated` 결정
  - [ ] Subtask 3.2 — `apps/web/components/auth/SocialAuthButtons.tsx` NEW (~+60 LOC): 3 provider buttons (Google + Naver + Kakao) + provider-specific branding + 60s cool-down 결정
  - [ ] Subtask 3.3 — Naver OAuth Option A/B 결정: Supabase Naver 공식 지원 확인 (Option A 우선) / 미지원 시 Option B custom Naver OAuth flow 결정 wire 보존 (Epic 15-1 bmad-dev-story 진입 시점에 결정)

- [ ] **Task 4 — T4: SSO SAML backend wire** (AC: #3.1, #3.2, #3.3, #3.4, #3.7, #3.8, #6.3, #6.4)
  - [ ] Subtask 4.1 — `apps/api/modules/auth/sso/saml_validator.py` NEW (~+150 LOC): `python3-saml==1.16.0` (AD-14 stack pin) + SAML response validation (signature + timestamp + Audience + Destination + InResponseTo + RelayState) 결정
  - [ ] Subtask 4.2 — `apps/api/modules/auth/sso/saml_routes.py` NEW (~+100 LOC): 4 SSO routes (`/api/v1/auth/sso/{login,acs,metadata,sls}`) + tenant slug routing + ko-KR envelope 결정
  - [ ] Subtask 4.3 — `apps/api/modules/auth/sso/jit_provisioning.py` NEW (~+100 LOC): JIT user provisioning 5-step atomic flow (SAML → users + tenants + tenant_memberships + external_identities + audit_log) 결정
  - [ ] Subtask 4.4 — `apps/api/alembic/versions/0037_epic_15_sso_external_identities.py` NEW (~+80 LOC): `external_identities` table + RLS policy (`tenant_id = current_setting('app.tenant_id')`) + 4 indexes + 2 CHECK constraints + down_revision=`0036_phase_4_backup_strategy` 결정
  - [ ] Subtask 4.5 — `apps/api/main.py` MODIFIED: `sso_router` include + Epic 15 audit-first INSERT `sso_identity_linked` 결정
  - [ ] Subtask 4.6 — `requirements.txt` MODIFIED: `python3-saml==1.16.0` AD-14 stack pin 결정

- [ ] **Task 5 — T5: SSO SAML UI wire** (AC: #3.5, #3.6, #6.2, #3.7)
  - [ ] Subtask 5.1 — `apps/web/app/api/auth/sso/callback/route.ts` NEW (~+30 LOC): SAML ACS callback + `sb-access-token` cookie set + `/dashboard` redirect 결정
  - [ ] Subtask 5.2 — `apps/web/app/[locale]/sso/[tenant_slug]/login/page.tsx` NEW (~+40 LOC): `/sso/<tenant_slug>/login` 진입 + tenant slug routing + Epic 12 2FA redirect 결정
  - [ ] Subtask 5.3 — `apps/web/app/[locale]/(auth)/login/page.tsx` MODIFIED: 3 NEW auth method entry points (magic link + social OAuth + SSO enterprise) 결정

- [ ] **Task 6 — T6: Capability v1.26 EXTENSION wire** (AC: #5.1~#5.6)
  - [ ] Subtask 6.1 — `apps/api/core/capability.py` MODIFIED: 5 NEW enum `MAGIC_LINK` + `SOCIAL_OAUTH_GOOGLE` + `SOCIAL_OAUTH_NAVER` + `SOCIAL_OAUTH_KAKAO` + `SSO_ENTERPRISE` (CR 12-1 L4 precedent — industry-agnostic) 결정
  - [ ] Subtask 6.2 — `apps/api/core/capability.py` 4-industry grants industry-agnostic ✅/✅/✅/✅ (manufacturing + service + retail + food_service) 결정
  - [ ] Subtask 6.3 — `docs/capability-matrix.md` 확인 (Epic 15 PRD entry `dd218fa` 진입 시점에 5 NEW rows 이미 추가됨, lines 451-455) — capability.py enum 만 wire 진입 결정
  - [ ] Subtask 6.4 — `apps/api/dependencies/capability.py` EXTENSION: `require_capability()` Dependency 5개 신규 wire (미허용 tenant 진입 차단) 결정

- [ ] **Task 7 — T7: ko-KR.json SSOT EXTENSION + middleware EXTENSION wire** (AC: #4.1, #4.2, #4.3, #4.4, #6.1, #6.5)
  - [ ] Subtask 7.1 — `apps/web/messages/ko-KR.json` MODIFIED: 3 NEW namespace EXTENSION — `auth.magic_link.*` (8 keys) + `auth.social.*` (7 keys) + `auth.sso.*` (8 keys) 결정 wire
  - [ ] Subtask 7.2 — `apps/web/middleware.ts` MODIFIED: auth-callback route 추가 (magic link callback + OAuth callback 통합) + Phase 3-1 T4 wire EXTENSION 정합 결정

- [ ] **Task 8 — T8: Tests + docs + atomic commit + 3중 게이트 FINAL CLEAN** (AC: #7.1~#7.11)
  - [ ] Subtask 8.1 — `tests/web/test_epic_15_magic_link_parity.test.ts` NEW (~+15 vitest cases — `MagicLinkForm` 15 RTL + 5회 cool-down + email 존재 여부 노출 방지 + audit-first INSERT)
  - [ ] Subtask 8.2 — `tests/web/test_epic_15_social_oauth_parity.test.ts` NEW (~+15 vitest cases — `SocialAuthButtons` + provider whitelist + 3회 cool-down + audit-first INSERT)
  - [ ] Subtask 8.3 — `tests/api/core/test_epic_15_sso_validator.py` NEW (~+15 pytest cases — SAML response validation)
  - [ ] Subtask 8.4 — `tests/api/core/test_epic_15_sso_jit_provisioning.py` NEW (~+10 pytest cases — JIT 5-step + RLS + audit-first INSERT)
  - [ ] Subtask 8.5 — `tests/api/core/test_epic_15_sso_routes.py` NEW (~+15 pytest cases — 4 routes + tenant slug routing)
  - [ ] Subtask 8.6 — `tests/api/core/test_epic_15_alembic_0037_external_identities.py` NEW (~+10 pytest cases — alembic 0037 + RLS + indexes)
  - [ ] Subtask 8.7 — `tests/integration/test_capability_matrix_v1_26_drift.py` NEW (drift detector — 5 NEW rows SSOT 정합 sweep)
  - [ ] Subtask 8.8 — `docs/sso-enterprise.md` NEW (~+150 LOC, 10 sections: SAML 2.0 spec + IdP metadata + SP metadata + AuthnRequest + ACS + JIT + multi-tenant + audit + security + troubleshooting) 결정 wire
  - [ ] Subtask 8.9 — sprint-status `epic-15-sso-magic-oauth-wire: in-progress → done` + `last_updated: 2026-08-22 (KST)` line 갱신
  - [ ] Subtask 8.10 — handoff memory 신규 `C:\Users\c8rom\.claude\projects\C--Users-c8rom-desktop-costmgr\memory\handoff-2026-08-22-epic-15-sso-magic-oauth-wire-done.md` + `C:\Users\c8rom\.claude\projects\C--Users-c8rom-desktop-costmgr\memory\handoff-2026-08-22-epic-15-sso-magic-oauth-wire-spec-entry-done.md`
  - [ ] Subtask 8.11 — 3중 게이트 FINAL CLEAN verification: (1) `pnpm tsc --noEmit` 0 NEW / (2) `pnpm vitest run` 716+50 = ~766 NEW PASS + 0 regressions / (3) `ruff check` scoped Epic 15 wire files = All checks passed! / (4) `pytest` 31+50 = ~81 NEW PASS. **A36 SDR 검증 4-step 자동 적용**: (a) commit prefix lint / (b) sprint-status structure / (c) vitest file count drift / (d) commit consistency
  - [ ] Subtask 8.12 — atomic commit via `git commit -F <commit-msg-file>` (CR 9-6 D5 prevention — PowerShell here-string 회피)
  - [ ] Subtask 8.13 — D-1-1-DEFER-1/2/3 grep guard UPDATE 결정 — test `test_no_magic_link_or_oauth_or_sso_introduced` INVERSION 결정 (D-1-1-DEFER-1/2/3 RESOLVED 진입 후, 이 test 는 Magic link + Social OAuth + SSO 모두 wire 됨 검증으로 INVERT 결정) 또는 test rename (`test_epic_15_magic_link_and_oauth_and_sso_introduced`) 결정 wire 보존 — Epic 15-1 bmad-dev-story 진입 시점에 결정.

## Dev Notes

### Source tree components to touch

**NEW files (~17)**
- `apps/web/lib/auth/magic-link.ts` (T1.1+T1.2)
- `apps/web/components/auth/MagicLinkForm.tsx` (T2.1)
- `apps/web/app/[locale]/(auth)/magic-link/page.tsx` (T2.2)
- `apps/web/app/[locale]/(auth)/magic-link-sent/page.tsx` (T2.3)
- `apps/web/app/[locale]/(auth)/auth-callback/page.tsx` (T2.4)
- `apps/web/lib/auth/social.ts` (T3.1)
- `apps/web/components/auth/SocialAuthButtons.tsx` (T3.2)
- `apps/api/modules/auth/sso/saml_validator.py` (T4.1)
- `apps/api/modules/auth/sso/saml_routes.py` (T4.2)
- `apps/api/modules/auth/sso/jit_provisioning.py` (T4.3)
- `apps/api/alembic/versions/0037_epic_15_sso_external_identities.py` (T4.4)
- `apps/web/app/api/auth/sso/callback/route.ts` (T5.1)
- `apps/web/app/[locale]/sso/[tenant_slug]/login/page.tsx` (T5.2)
- `docs/sso-enterprise.md` (T8.8)
- `tests/web/test_epic_15_magic_link_parity.test.ts` (T8.1)
- `tests/web/test_epic_15_social_oauth_parity.test.ts` (T8.2)
- `tests/api/core/test_epic_15_sso_validator.py` (T8.3)
- `tests/api/core/test_epic_15_sso_jit_provisioning.py` (T8.4)
- `tests/api/core/test_epic_15_sso_routes.py` (T8.5)
- `tests/api/core/test_epic_15_alembic_0037_external_identities.py` (T8.6)
- `tests/integration/test_capability_matrix_v1_26_drift.py` (T8.7)

**MODIFIED files (~7)**
- `apps/api/main.py` (T4.5) — sso_router include
- `apps/api/core/capability.py` (T6.1+T6.2) — 5 NEW enum + 4-industry grants
- `apps/api/dependencies/capability.py` (T6.4) — `require_capability()` Dependency 5개 신규
- `apps/web/middleware.ts` (T7.2) — auth-callback route 추가
- `apps/web/app/[locale]/(auth)/login/page.tsx` (T5.3) — 3 NEW auth method entry points
- `apps/web/messages/ko-KR.json` (T7.1) — 3 NEW namespace EXTENSION
- `requirements.txt` (T4.6) — `python3-saml==1.16.0` AD-14 stack pin
- `apps/web/package.json` (F17.6 AC6.5) — `@supabase/supabase-js` `signInWithOAuth` EXTENSION (이미 결정 wire, EXTENSION 결정 wire 보존)

### Existing files to PRESERVE (Epic 15 PRD entry baseline sweep)

- **Phase 3-1 wire `d3e7454` (cj-style 50번째 epic 연속 정직 회복) — 33 files atomic**:
  - `apps/web/lib/supabase/{server,client,env,types,middleware}.ts` (Supabase SSR 5 NEW, F17.1/F17.2/F17.3 결정 wire 보존) — **PRESERVE VERBATIM**
  - `apps/web/lib/auth/{login,signup,forgot-password,reset-password,logout}.ts` (Phase 3-1 T2+T3+T6+T5 wire) — **EXTENSION ONLY** (not rewrite)
  - `apps/web/app/[locale]/(auth)/{login,signup,forgot-password,reset-password}/page.tsx` — **PRESERVE** (Epic 15 entry points 추가 EXTENSION 만)
  - `apps/web/components/auth/{LoginForm,SignupForm,ForgotPasswordForm,ResetPasswordForm,LogoutButton}.tsx` — **PRESERVE VERBATIM**
  - `apps/web/middleware.ts` (Phase 3-1 T4 EXTENSION, Edge Runtime + AAL branching) — **EXTENSION ONLY** (MODIFIED, auth-callback route 추가)
  - `apps/web/messages/ko-KR.json` (auth.login.* + auth.common namespace SSOT) — **EXTENSION ONLY** (3 NEW namespace EXTENSION)
  - `apps/api/modules/auth/sso/` — **PRESERVE** (신규 디렉토리, 없음)
  - `apps/api/alembic/versions/0035_custom_access_token_hook.py` (Phase 3-0 wire `1db21d2`) — **PRESERVE VERBATIM**
  - `tenant_memberships` + `audit_logs` tables (Phase 3-0 wire) — **PRESERVE VERBATIM**

- **Phase 4 wire `71a033a` (cj-style 55번째 epic 연속 정직 회복) — 26 files atomic**:
  - Vercel + Railway + per-app Dockerfile + health check + observability + database backup — **PRESERVE VERBATIM**
  - `apps/api/alembic/versions/0036_phase_4_backup_strategy.py` (down_revision chain) — **PRESERVE VERBATIM** (Epic 15 T4.4 `0037_epic_15_sso_external_identities.py` 의 down_revision = `0036_phase_4_backup_strategy` 결정 wire 정합)

- **Epic 12 wire `a63646c` (cj-style Epic 12 final close-out) — 2FA 게이트 보존**:
  - `apps/api/modules/auth/twofa/` + `users.totp_secret` 컬럼 + AAL branching (aal1 → /auth/2fa, aal2 → /dashboard) — **PRESERVE VERBATIM** (Epic 15 AC1.6 + AC2.6 + AC3.6 결정 wire 정합 sweep)

- **Epic 13/14 wire (`f2ea2f6` + `7835463`)** — LISTEN/NOTIFY consume multi-process coordination — **PRESERVE VERBATIM** (Epic 15 territory 미접촉)

- **Epic 11 wire `8735eb5` + Story 11.6 wire `1060360`** — M0 Auth Foundation territory — **PRESERVE VERBATIM**

- **Epic 1 partial scaffold** — (auth) layout + onboarding/industry + IndustrySelector + IndustryCard + middleware.ts next-intl EXTENSION — **PRESERVE VERBATIM**

### Test environment invariants (CRITICAL)

- **Magic link wrapper tests**: All `tests/web/test_epic_15_magic_link_parity.test.ts` tests MUST mock Supabase `signInWithOtp` (test fixture = `supabase.auth.signInWithOtp = vi.fn(async () => ({ data: null, error: null }))`). Email 존재 여부 노출 방지 try/catch/finally invariant MUST be tested (security invariant enforcement).
- **Social OAuth wrapper tests**: All `tests/web/test_epic_15_social_oauth_parity.test.ts` tests MUST mock Supabase `signInWithOAuth` (test fixture = mock per-provider response). **Provider whitelist strict reject MUST be tested** (e.g. `signInWithSocialOAuth('facebook')` MUST throw `PROVIDER_DISABLED` envelope, AD-7 verbatim 정합).
- **SSO validator tests**: All `tests/api/core/test_epic_15_sso_validator.py` tests MUST use mocked SAML response XML (test fixture = `tests/fixtures/saml/response_ok.xml` + `response_expired.xml` + `response_invalid_signature.xml`). `python3-saml==1.16.0` pinned version MUST be used.
- **SSO JIT provisioning tests**: All `tests/api/core/test_epic_15_sso_jit_provisioning.py` tests MUST mock 5-step atomic flow (test fixture = mock SAML response → user extraction → 5-step INSERT). RLS policy 검증 MUST be tested (CR 0-2 RLS lesson).
- **alembic 0037 tests**: All `tests/api/core/test_epic_15_alembic_0037_external_identities.py` tests MUST use `re.compile` against migration source for code-shape verification (Story 9-7 T9 precedent 미러).
- **D-003 vitest RTL render**: All frontend component tests MUST use `@testing-library/react` with `render(<Component />)` (no shallow rendering, full DOM tree).
- **D-005 unknown state reject**: All TS mirror components MUST handle `state === 'unknown'` by rejecting (render fallback UI, never crash).
- **No live Supabase**: All tests run in `pnpm vitest` / `pytest` without actual Supabase connection. Magic link + OAuth 모두 mock 결정.

### Existing patterns to mirror (CR 11-4 lessons carry)

- **CR 11-4 D-001**: `page.tsx` actual mount `<Component>` JSX MUST (no `<>TODO</>` stubs) — Epic 15 T2+T5 page.tsx actual mount 결정 wire
- **CR 11-4 D-002**: `apps/web/messages/ko-KR.json` SSOT only (no `lib/ko-KR.json` dual-file) — Epic 15 ko-KR.json EXTENSION 결정 wire
- **CR 11-4 D-003**: vitest RTL render discipline — Epic 15 frontend tests 결정
- **CR 11-4 D-004**: TS mirror parity mandatory (TS ↔ Python envelope consistency) — Epic 15 magic_link + social_oauth + sso envelope 결정
- **CR 11-4 D-005**: TS mirror unknown state reject — Epic 15 callback handler 결정
- **CR 11-4 P-015**: ko-KR.json SSOT drift detector — Epic 15 namespace 검출 EXTENSION 결정

### Backend integration points

- **Phase 3-0 wire `1db21d2` 정합** — tenant_memberships + audit_logs + custom_access_token_hook + 5-step atomic flow (JIT provisioning 의 tenant_memberships INSERT 패턴 verbatim reuse)
- **Phase 3-1 wire `d3e7454` 정합** — Supabase SSR + sb-access-token cookie + auth route group (auth) + dashboard route group (dashboard) + auth middleware EXTENSION (Epic 15 entry points EXTENSION)
- **Phase 4 wire `71a033a` 정합** — alembic 0036 phase_4_backup_strategy (Epic 15 T4.4 `0037_epic_15_sso_external_identities.py` 의 down_revision chain 정합)
- **Epic 12 wire `a63646c` 정합** — 2FA 게이트 + Epic 12 AAL branching (Magic link + Social OAuth + SSO 성공 후 2FA 미설정 시 `/auth/2fa` redirect)
- **Epic 14 wire `7835463` 정합** — LISTEN/NOTIFY multi-process coordination (Epic 15 territory 미접촉, 보존 결정)
- **`audit_logs` table** — Phase 3-0 wire (CR 1-1 audit-first INSERT — Epic 15 `magic_link_sent` + `social_oauth_initiated` + `sso_identity_linked` 3 NEW audit log INSERT 결정 wire)
- **`tenants` + `tenant_memberships` tables** — Phase 3-0 wire + Epic 11 wire `1060360` (JIT provisioning 의 5-step atomic flow 정합)

### Architecture patterns to follow

- **AD-28 Magic link + Social OAuth + SSO enterprise SAML 신규** (Epic 15 PRD entry 결정 wire):
  - Magic link: Supabase `signInWithOtp` + 5회 cool-down + email 존재 여부 노출 방지 + audit-first INSERT
  - Social OAuth: Supabase `signInWithOAuth` + provider whitelist + 3회 cool-down + audit-first INSERT + OAuth callback
  - SSO enterprise SAML: `python3-saml==1.16.0` AD-14 stack pin + SAML response validation + JIT user provisioning + multi-tenant isolation RLS + audit-first INSERT
- **CR 0-2 RLS lesson**: T4.4 `external_identities` table RLS policy `tenant_id = current_setting('app.tenant_id')` 결정 wire (CR 0-2 verbatim 정합)
- **CR 1-1 audit-first INSERT**: T1+T3+T5 audit-first INSERT 3 NEW 결정 wire (magic_link_sent + social_oauth_initiated + sso_identity_linked)
- **CR 9-6 commit message discipline**: `git commit -F <file>` (NOT PowerShell here-string) 결정 wire
- **CR 11-3 honest-DEFER 58~59번째 epic 연속**: D-1-1-DEFER-1/2/3 honestly ✅ RESOLVE (Epic 15 PRD entry 진입 wire), grep guard INVERSION 또는 test rename 결정
- **CR 11-4 D-001~D-005 + P-015**: 5 lessons carry 결정
- **CR 12-1 L4 precedent**: capability matrix v1.26 EXTENSION 5 NEW rows industry-agnostic 4-industry grants (MAGIC_LINK + SOCIAL_OAUTH_GOOGLE + SOCIAL_OAUTH_NAVER + SOCIAL_OAUTH_KAKAO + SSO_ENTERPRISE)
- **CR 12-5 D-14 envelope**: magic_link + social_oauth + sso envelope 결정 wire (CR 12-5 verbatim 정합)
- **CR 12-5 D-PARITY-01 inversion**: Supabase + Next.js + SAML OAuth parity 결정 wire
- **CR 12-5 D-GATE-01 inversion**: Epic 12 2FA 게이트 보존 결정 wire (Magic link + Social OAuth + SSO 모두 2FA 게이트 통과 후 M2 진입)
- **A19 cohesion pattern 9 surface EXTENSION PASS 결정**: auth surface EXTENSION = F17.1~F17.3 magic link + social OAuth + SSO enterprise territory (Epic 1 partial scaffold + Phase 3-1 wire + Epic 12 2FA 게이트 + capability matrix v1.26 EXTENSION 결정 wire)

### Project Structure Notes

- **Auth services frontend**: `apps/web/lib/auth/` (Phase 3-1 T1~T6 wire EXTENSION) + `apps/web/components/auth/` (Phase 3-1 component EXTENSION)
- **Auth services backend**: `apps/api/modules/auth/sso/` (Epic 15 NEW directory, submodule EXTENSION 결정을 추후에 결정, ALLOWED_SERVICE_SUBMODULES sweep 결정 wire)
- **Alembic migration**: `apps/api/alembic/versions/0037_epic_15_sso_external_identities.py` (Phase 4 `0036_phase_4_backup_strategy` down_revision 정합)
- **Capability gate**: `apps/api/core/capability.py` (Phase 3-1 + Phase 4 wire pattern verbatim EXTENSION)
- **SSO UI**: `apps/web/app/[locale]/sso/[tenant_slug]/login/page.tsx` + `apps/web/app/api/auth/sso/callback/route.ts`
- **Auth middleware**: `apps/web/middleware.ts` EXTENSION (Phase 3-1 T4 + Epic 15 auth-callback route 추가)
- **Docs**: `docs/sso-enterprise.md` + `apps/web/messages/ko-KR.json` 3 NEW namespace EXTENSION
- **Test structure**: `tests/web/test_epic_15_*.test.ts` (vitest frontend tests) + `tests/api/core/test_epic_15_*.py` (pytest backend tests) + `tests/integration/test_capability_matrix_v1_26_drift.py` (drift detector) — 기존 pattern 미러 (`test_capability_matrix_v1_24_drift.py` + `test_phase_3_1_*.py` + `test_phase_4_*.py`)

### Detected conflicts or variances

- **Naver OAuth Option A vs B 결정**: Supabase `signInWithOAuth` 공식 Naver 지원 여부 결정 보류 (Supabase Provider docs 확인 필요). Option A 우선 시도 + Option B fallback 결정 wire 보존. Epic 15-1 bmad-dev-story 진입 시점에 결정.
- **D-1-1-DEFER-* grep guard INVERSION**: Phase 3-1 wire `d3e7454` 에서 추가된 `test_no_magic_link_or_oauth_or_sso_introduced` 테스트는 Epic 15 wire DONE 진입 시점에 INVERT 또는 rename (`test_epic_15_magic_link_and_oauth_and_sso_introduced`) 결정. 결정 wire 진입 시점에 결정 (Epic 15-1 bmad-dev-story 진입 시점에 결정).
- **SAML IdP metadata storage**: tenant slug 별 IdP metadata 저장 방식 결정 (DB vs config file vs Supabase Storage). 결정 wire 진입 시점에 결정 (Epic 15-1 bmad-dev-story 진입 시점에 결정).
- **SAML Signature verification test**: `python3-saml` library 의 signature verification 는 실제 IdP metadata 가 필요. test fixture 로 signed SAML response XML 사용 결정 (테스트 신뢰성 sweep).
- **SSO SLO 구현 범위**: Single Logout Service endpoint 의 SAML logout response 처리 범위 결정 (full logout vs basic logout) 결정 wire 보존.

## Previous Story Intelligence

### Epic 15 PRD entry (`epic-15-prd-entry: done`, 2026-08-22, commit `dd218fa`)
- master PRD v3.1 → v3.2 atomic edit
- §F17 신규 (F17.1~F17.6 verbatim)
- AD-28 Magic link + Social OAuth + SSO enterprise SAML 신규 결정
- capability matrix v1.25 → v1.26 EXTENSION 5 NEW rows 결정
- A79+A80+A81+A82 신규 결정 wire
- D-1-1-DEFER-1/2/3 honestly ✅ RESOLVE 58번째 epic 연속 정직 회복
- handoff: `memory/handoff-2026-08-22-epic-15-prd-entry-done.md`

### Phase 4 close-out retro (`phase-4-close-out: done`, 2026-08-22, commit `934b35e`)
- Phase 4 = Deployment config + Dockerfile + health check + observability + database backup territory close-out 완료
- Phase 4 wire `71a033a` (cj-style 55번째) 정합 — alembic 0036 down_revision chain 결정
- A79 결정 wire 진입 = 옵션 (a) Epic 15 진입
- handoff: `memory/handoff-2026-08-22-phase-4-close-out-done.md`

### Phase 4 atomic wire (`phase-4-deployment-wire: done`, 2026-08-22, commit `71a033a`)
- 26 files atomic (20 NEW + 6 MODIFIED)
- 108 NEW pytest PASS + 21 NEW vitest PASS
- 3중 게이트 FINAL CLEAN
- alembic 0036 phase_4_backup_strategy table 결정 (Epic 15 T4.4 down_revision = 0036 결정 wire 정합)
- handoff: `memory/handoff-2026-08-22-phase-4-deployment-wire-done.md`

### Phase 4-1 spec entry (`phase-4-deployment-wire-spec-entry: done`, 2026-08-22)
- 9 ACs + 8 tasks + 22 subtasks (cj-style 54번째 epic 연속 정직 회복 bmad-create-story)
- sprint-status: `phase-4-deployment-wire: open → ready-for-dev`
- spec = `_bmad-output/implementation-artifacts/phase-4-deployment-wire.md`
- handoff: `memory/handoff-2026-08-22-phase-4-deployment-wire-spec-entry-done.md`

### Phase 3 close-out retro (`phase-3-close-out-retrospective: done`, 2026-08-22)
- Phase 3 = Auth Foundation territory close-out 완료
- A70+A71+A72+A73+A74+A75 신규 결정 wire 진입
- Epic 15 = 옵션 (a) 진입 결정 wire (cj-style 58번째 epic 연속 정직 회복)
- handoff: `memory/handoff-2026-08-22-phase-3-close-out-done.md`

### Phase 3-1 auth foundation wire (`phase-3-1-auth-foundation-wire: done`, 2026-08-21, commit `d3e7454`)
- 33 files atomic (5+4+5+2+3+5+2+7)
- 97 NEW test cases (66 vitest + 31 pytest)
- 3중 게이트 FINAL CLEAN
- Supabase SSR + sb-access-token cookie + auth route group + dashboard route group + auth middleware EXTENSION + Epic 12 2FA 게이트 보존
- handoff: `memory/handoff-2026-08-21-phase-3-1-auth-foundation-wire-done.md`

### Phase 3-0 auth contract slice (`phase-3-0-auth-contract-slice: done`, 2026-08-21, commit `1db21d2`)
- P0 3종 ALL RESOLVED: GUC name split + custom_access_token_hook + signup path
- 15 files atomic
- 43 NEW pytest PASS
- 3중 게이트 FINAL CLEAN
- handoff: `memory/handoff-2026-08-21-phase-3-0-auth-contract-slice-done.md`

### Epic 12 wire (cj-style Epic 12 final close-out, commit `a63646c`)
- 2FA 게이트 + AAL branching (aal1 → /auth/2fa, aal2 → /dashboard)
- 16 E2E scenarios
- TOTP RFC 6238 + NFR6 AES-256-GCM + ActionClass.TWO_FACTOR_AUTH 6 NEW 결정 wire
- Epic 15 AC1.6 + AC2.6 + AC3.6 결정 wire 정합 (2FA 게이트 보존)

### Epic 14 wire (`14-1-listen-notify-consume-cross-tenant-fanout: done`, commit `7835463`)
- 14 NEW + 8 MODIFIED
- ~140 NEW pytest PASS
- A19 cohesion 8 surface EXTENSION PASS
- Epic 15 territory 미접촉, 보존 결정 wire

### Epic 13 wire (`13-1-listen-notify-consume-trigger-extension: done`, commit `f2ea2f6`)
- 17 files atomic T1~T8
- A19 cohesion 8 surface PASS + D-10-2-DEFER-3 ✅ RESOLVED
- Epic 15 territory 미접촉, 보존 결정 wire

### Phase 2 close-out baseline
- baseline 42 failed → 0 failed + 599 passed + 8 skipped in 212s
- 11 gates + 6 functional fixes ALL PASS
- handoff: `memory/handoff-2026-08-20-phase-2-close-out-done.md`

## Git Intelligence Summary

### Last 5 commit titles (analysis)

1. `dd218fa` — Epic 15 PRD entry DONE (cj-style Epic 15 1번째 진입점 = cj-style 58번째 epic 연속 정직 회복, master PRD v3.1 → v3.2 atomic edit)
2. `934b35e` — Phase 4 close-out retro DONE (cj-style Phase 4 4번째 진입점 = cj-style 56~57번째 epic 연속 정직 회복, 12-section cj-style retro)
3. `71a033a` — Phase 4 atomic wire DONE (cj-style Phase 4 3번째 진입점 = cj-style 55번째 epic 연속 정직 회복, 26 files atomic)
4. `phase-4-deployment-wire-spec-entry` — Phase 4 spec entry DONE (cj-style Phase 4 2번째 진입점 = cj-style 54번째 epic 연속 정직 회복 bmad-create-story)
5. `8e046df` — Phase 4 PRD entry DONE (cj-style Phase 4 1번째 진입점 = cj-style 53번째 epic 연속 정직 회복)

### Patterns established (apply to current story)

- **Single atomic commit** per sprint (T1~T8 in single atomic commit, CR 11-3 discipline)
- **2 atomic commits** if frontend + backend + docs must be separated (rare)
- **3중 게이트 FINAL CLEAN** mandatory before commit
- **A36 SDR 검증 4-step 자동 적용** (commit prefix lint + sprint-status structure + vitest file count drift + commit consistency)
- **CR 9-6 D5 prevention**: `git commit -F <file>` (NOT PowerShell here-string)
- **cj-style "fix" 종류 pre-flight 정합 sweep**: 결정 wire 진입 시점에 baseline 정합 sweep 결정 (Epic 15 PRD entry 진입 시점에 cj-style 53~58번째 epic 연속 정직 회복 모두 보존 검증 결정)

### Files created/modified in last sprint (relevant to Epic 15)

**Phase 4 atomic wire `71a033a` 결정:**
- `vercel.json` + `railway.toml` + `apps/web/Dockerfile` + `apps/api/Dockerfile` + `docs/deployment.md` + `apps/api/core/health.py` + `apps/api/core/observability.py` + `apps/web/lib/observability/sentry.ts` + `apps/web/app/api/health/route.ts` + `apps/api/alembic/versions/0036_phase_4_backup_strategy.py` + `docs/database-backup.md` + `apps/api/main.py` (health router) + `apps/api/core/capability.py` (4 NEW DEPLOYMENT_* enum) — **PRESERVE VERBATIM**

**Phase 3-1 auth foundation wire `d3e7454` 결정:**
- `apps/web/lib/supabase/{server,client,env,types,middleware}.ts` (5 NEW) — **PRESERVE VERBATIM**
- `apps/web/lib/auth/{login,signup,forgot-password,reset-password,logout}.ts` — **EXTENSION ONLY**
- `apps/web/components/auth/{LoginForm,SignupForm,ForgotPasswordForm,ResetPasswordForm,LogoutButton}.tsx` — **PRESERVE VERBATIM**
- `apps/web/app/[locale]/(auth)/{login,signup,forgot-password,reset-password}/page.tsx` — **EXTENSION ONLY**
- `apps/web/app/[locale]/(auth)/signup/email-verification-pending/page.tsx` — **PRESERVE VERBATIM**
- `apps/web/middleware.ts` (Phase 3-1 T4 EXTENSION, auth middleware) — **EXTENSION ONLY** (Epic 15 auth-callback route 추가 결정)
- `apps/web/messages/ko-KR.json` (auth.login + auth.common + auth.signup namespace) — **EXTENSION ONLY** (3 NEW namespace EXTENSION 결정)
- `apps/api/core/capability.py` (5 NEW enum: LOGIN + SIGNUP + AUTH_MIDDLEWARE + FORGOT_PASSWORD + LOGOUT) — **EXTENSION ONLY** (Epic 15 T6 5 NEW enum EXTENSION)

## References

- [Source: _bmad-output/planning-artifacts/prd.md#F17] — master PRD §F17 (Magic link + Social OAuth + SSO enterprise territory) verbatim
- [Source: _bmad-output/planning-artifacts/prd.md#F17.1] — Magic link login
- [Source: _bmad-output/planning-artifacts/prd.md#F17.2] — Social OAuth (Google/Naver/Kakao) login
- [Source: _bmad-output/planning-artifacts/prd.md#F17.3] — SSO enterprise SAML
- [Source: _bmad-output/planning-artifacts/prd.md#F17.4] — ko-KR SSOT EXTENSION
- [Source: _bmad-output/planning-artifacts/prd.md#F17.5] — Capability matrix v1.25 → v1.26 EXTENSION 5 NEW rows
- [Source: _bmad-output/planning-artifacts/prd.md#F17.6] — tests + wire scope T1~T8 결정
- [Source: _bmad-output/planning-artifacts/prd.md#AD-28] — Magic link + Social OAuth + SSO enterprise SAML 신규 결정
- [Source: _bmad-output/planning-artifacts/prd.md#M0-(h)] — §8.1 M0-(h) Magic link 인수 불릿
- [Source: _bmad-output/planning-artifacts/prd.md#M0-(i)] — §8.1 M0-(i) Social OAuth 인수 불릿
- [Source: _bmad-output/planning-artifacts/prd.md#M0-(j)] — §8.1 M0-(j) SSO enterprise SAML 인수 불릿
- [Source: docs/capability-matrix.md#v1.26] — capability matrix v1.26 EXTENSION (5 NEW rows already added at lines 451-455)
- [Source: docs/architecture-decisions/] — AD 인벤토리 (AD-28 신규 추가 시)
- [Source: docs/conventions.md] — §13.1 ko-KR SSOT 1권 강제 + ESLint rule forbid-non-ko-KR-keys
- [Source: docs/STACK_PIN.yaml] — frontend + backend 의존성 pin 검증 (`python3-saml==1.16.0` 결정)
- [Source: _bmad-output/implementation-artifacts/handoff-2026-08-22-epic-15-prd-entry-done.md] — A79+A80+A81+A82 결정
- [Source: _bmad-output/implementation-artifacts/handoff-2026-08-22-phase-4-close-out-done.md] — Phase 4 close-out retro
- [Source: _bmad-output/implementation-artifacts/handoff-2026-08-22-phase-4-deployment-wire-done.md] — Phase 4 atomic wire
- [Source: _bmad-output/implementation-artifacts/handoff-2026-08-22-phase-3-close-out-done.md] — Phase 3 close-out retro + A70~A75 결정
- [Source: _bmad-output/implementation-artifacts/handoff-2026-08-21-phase-3-1-auth-foundation-wire-done.md] — Phase 3-1 wire 33 files
- [Source: _bmad-output/implementation-artifacts/handoff-2026-08-21-phase-3-0-auth-contract-slice-done.md] — Phase 3-0 wire
- [Source: apps/api/core/capability.py] — Capability enum (5 NEW entries wire 진입)
- [Source: docs/sso-enterprise.md] — SSO enterprise runbook (NEW, T8.8)

## Open Questions

- **OQ-1**: Naver OAuth Option A vs B 결정 — Supabase `signInWithOAuth` 공식 Naver 지원 여부. 결정 wire 진입 시점: Epic 15-1 bmad-dev-story 진입 시점 (Option A 우선 시도 + Option B fallback 결정).
- **OQ-2**: D-1-1-DEFER-* grep guard INVERSION — `test_no_magic_link_or_oauth_or_sso_introduced` test 의 INVERT 또는 rename 결정. 결정 wire 진입 시점: Epic 15-1 bmad-dev-story 진입 시점.
- **OQ-3**: SAML IdP metadata storage — tenant slug 별 IdP metadata 저장 방식 (DB vs config file vs Supabase Storage). 결정 wire 진입 시점: Epic 15-1 bmad-dev-story 진입 시점.
- **OQ-4**: SSO SLO 구현 범위 — Single Logout Service endpoint 의 SAML logout response 처리 범위 (full logout vs basic logout). 결정 wire 진입 시점: Epic 15-1 bmad-dev-story 진입 시점.
- **OQ-5**: SAML Signature verification test fixture — `python3-saml` library 의 signature verification 를 테스트하기 위한 signed SAML response XML test fixture 작성. 결정 wire 진입 시점: Epic 15-1 bmad-dev-story 진입 시점.

## Dev Agent Record

### Agent Model Used

claude-opus-4 (cj-style Epic 15 2번째 진입점 = cj-style 59번째 epic 연속 정직 회복 bmad-create-story)

### Debug Log References

### Completion Notes List

### File List

- [ ] `apps/web/lib/auth/magic-link.ts` (NEW, T1.1+T1.2)
- [ ] `apps/web/components/auth/MagicLinkForm.tsx` (NEW, T2.1)
- [ ] `apps/web/app/[locale]/(auth)/magic-link/page.tsx` (NEW, T2.2)
- [ ] `apps/web/app/[locale]/(auth)/magic-link-sent/page.tsx` (NEW, T2.3)
- [ ] `apps/web/app/[locale]/(auth)/auth-callback/page.tsx` (NEW, T2.4)
- [ ] `apps/web/lib/auth/social.ts` (NEW, T3.1)
- [ ] `apps/web/components/auth/SocialAuthButtons.tsx` (NEW, T3.2)
- [ ] `apps/api/modules/auth/sso/saml_validator.py` (NEW, T4.1)
- [ ] `apps/api/modules/auth/sso/saml_routes.py` (NEW, T4.2)
- [ ] `apps/api/modules/auth/sso/jit_provisioning.py` (NEW, T4.3)
- [ ] `apps/api/alembic/versions/0037_epic_15_sso_external_identities.py` (NEW, T4.4)
- [ ] `apps/web/app/api/auth/sso/callback/route.ts` (NEW, T5.1)
- [ ] `apps/web/app/[locale]/sso/[tenant_slug]/login/page.tsx` (NEW, T5.2)
- [ ] `apps/api/main.py` (MODIFIED, T4.5)
- [ ] `apps/api/core/capability.py` (MODIFIED, T6.1+T6.2)
- [ ] `apps/api/dependencies/capability.py` (MODIFIED, T6.4)
- [ ] `apps/web/middleware.ts` (MODIFIED, T7.2)
- [ ] `apps/web/app/[locale]/(auth)/login/page.tsx` (MODIFIED, T5.3)
- [ ] `apps/web/messages/ko-KR.json` (MODIFIED, T7.1)
- [ ] `requirements.txt` (MODIFIED, T4.6)
- [ ] `apps/web/package.json` (MODIFIED, F17.6 AC6.5)
- [ ] `tests/web/test_epic_15_magic_link_parity.test.ts` (NEW, T8.1)
- [ ] `tests/web/test_epic_15_social_oauth_parity.test.ts` (NEW, T8.2)
- [ ] `tests/api/core/test_epic_15_sso_validator.py` (NEW, T8.3)
- [ ] `tests/api/core/test_epic_15_sso_jit_provisioning.py` (NEW, T8.4)
- [ ] `tests/api/core/test_epic_15_sso_routes.py` (NEW, T8.5)
- [ ] `tests/api/core/test_epic_15_alembic_0037_external_identities.py` (NEW, T8.6)
- [ ] `tests/integration/test_capability_matrix_v1_26_drift.py` (NEW, T8.7)
- [ ] `docs/sso-enterprise.md` (NEW, T8.8)
- [ ] `memory/handoff-2026-08-22-epic-15-sso-magic-oauth-wire-spec-entry-done.md` (NEW, T8.10)
- [ ] `memory/handoff-2026-08-22-epic-15-sso-magic-oauth-wire-done.md` (NEW, T8.10)
- [ ] `_bmad-output/implementation-artifacts/sprint-status.yaml` (MODIFIED, T8.9)

---

## A19 cohesion pattern 9 surface EXTENSION PASS 결정

- **Surface 1 (kernel)** = T1+T3+T4 `magic-link.ts` + `social.ts` + `saml_validator.py` + `jit_provisioning.py` (pure service kernels, Supabase wrapper + SAML 2.0 spec validation + JIT 5-step flow)
- **Surface 2 (port)** = T2+T3+T5 page.tsx + components + middleware.ts EXTENSION (Next.js App Router port adapter, (auth) route group 공개)
- **Surface 3 (db schema)** = T4.4 alembic 0037 `external_identities` table (id + provider enum `magic_link | google | naver | kakao | saml_*` + provider_user_id + tenant_id + user_id + linked_at + last_used_at + metadata JSONB + 4 indexes + 2 CHECK constraints + RLS policy)
- **Surface 4 (service)** = T1+T3+T4 service wrappers (Supabase `signInWithOtp` + `signInWithOAuth` + `python3-saml` SAML 2.0 + JIT provisioning)
- **Surface 5 (handler)** = T2.4 `/auth-callback` Next.js page + T4.2 `/api/v1/auth/sso/{login,acs,metadata,sls}` FastAPI routes
- **Surface 6 (envelope)** = Magic link + Social OAuth + SSO ko-KR envelope (`{code, message_ko, details, trace_id}` CR 12-5 D-14 verbatim 정합)
- **Surface 7 (capability)** = T6 5 NEW gates (`MAGIC_LINK` + `SOCIAL_OAUTH_GOOGLE` + `SOCIAL_OAUTH_NAVER` + `SOCIAL_OAUTH_KAKAO` + `SSO_ENTERPRISE`, industry-agnostic 4-industry grants ✅/✅/✅/✅)
- **Surface 8 (audit)** = T1+T3+T4 audit-first INSERT 3 NEW (`magic_link_sent` + `social_oauth_initiated` + `sso_identity_linked`, CR 1-1 audit-first INSERT 정합)
- **Surface 9 (auth) EXTENSION** = T1~T7 Magic link + Social OAuth + SSO enterprise territory 결정 wire (Epic 15 = auth surface EXTENSION 결정 wire)

## D-1-1-DEFER-* honestly ✅ RESOLVED 58번째 epic 연속 정직 회복 (CR 11-3 discipline)

Epic 15 PRD entry (`epic-15-prd-entry: done`, 2026-08-22, commit `dd218fa`) 진입 시점에 모두 ✅ RESOLVE 결정 wire 완료.

| DEFER ID | Description | 상태 (Epic 15 PRD entry 진입 후) |
|----------|------------|---------|
| **D-1-1-DEFER-1** | Magic link login | ✅ RESOLVED (A70) — Epic 15 T1+T2 wire 진입 대기 |
| **D-1-1-DEFER-2** | Social login OAuth (Google/Naver/Kakao) | ✅ RESOLVED (A71) — Epic 15 T3+T4 wire 진입 대기 |
| **D-1-1-DEFER-3** | SSO enterprise SAML | ✅ RESOLVED (A72) — Epic 15 T5+T6 wire 진입 대기 |

CR 11-3 honest-DEFER discipline 58번째 epic 연속 정직 회복 결정 wire. 59번째 진입 시점에 grep guard INVERSION 또는 test rename 결정 wire 보존 (OQ-2).

## CR 11-3 honest-DEFER discipline 59번째 epic 연속

A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS) + CR 12-5 D-GATE-01 (Epic 12 2FA 게이트) + D-PARITY-01 inversion (Supabase + Next.js + SAML OAuth parity) 적용 보존 + A19 cohesion 9 surface EXTENSION PASS (auth surface EXTENSION) + CR 0-2 RLS lesson (`external_identities` multi-tenant isolation) + CR 1-1 audit-first INSERT (3 NEW audit logs INSERT) + CR 9-6 commit message discipline (`git commit -F <file>`) + CR 11-4 D-001~D-005 + P-015 lessons carry 모두 적용 보존.

## 결정 wire 일자

2026-08-22 (KST)

## next

Epic 15 cj-style 2번째 진입점 (본 스토리) = cj-style 59번째 epic 연속 정직 회복 bmad-create-story spec 진입 → `bmad-dev-story epic-15-sso-magic-oauth-wire` T1~T8 atomic wire 진입 (cj-style Epic 15 3번째 진입점 = cj-style 60번째 epic 연속 정직 회복 wire 진입 시점).

Epic 15 close-out retro 진입 결정 wire 보존 (cj-style Epic 15 4번째 진입점 = cj-style 61~62번째 epic 연속 정직 회복 진입 시점) — A70+A71+A72 honestly RESOLVE 검증 + A19 cohesion 9 surface EXTENSION PASS 검증 (auth surface EXTENSION) + D-1-1-DEFER-1/2/3 grep guard 58~61~62번째 epic 연속 정직 회복 검증 결정 wire 보존.
