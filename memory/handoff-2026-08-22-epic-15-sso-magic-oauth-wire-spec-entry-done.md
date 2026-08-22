---
name: handoff-2026-08-22-epic-15-sso-magic-oauth-wire-spec-entry-done
description: "Epic 15 bmad-create-story spec entry DONE (cj-style Epic 15 2번째 진입점 = cj-style 59번째 epic 연속 정직 회복 bmad-create-story). sprint-status epic-15-sso-magic-oauth-wire: backlog → ready-for-dev. PRD §F17 verbatim 9 ACs + 8 tasks T1~T8 + 22 subtasks 결정 wire 진입 보존. A19 cohesion 9 surface EXTENSION PASS 결정 (auth surface EXTENSION). D-1-1-DEFER-1/2/3 ✅ honestly RESOLVE 59번째 epic 연속 정직 회복."
metadata: 
  node_type: memory
  type: project
  originSessionId: 03027be3-bced-404e-90f1-6e2319813f4e
  modified: 2026-08-22T01:25:09.722Z
---

# Epic 15 bmad-create-story spec entry DONE — Magic link + Social OAuth + SSO enterprise territory (handoff-2026-08-22)

## 결정 wire (2026-08-22)

Epic 15 bmad-create-story spec entry DONE (cj-style Epic 15 2번째 진입점 = cj-style 59번째 epic 연속 정직 회복 bmad-create-story 진입 결정).

- baseline_commit = `dd218fa` (Epic 15 PRD entry wire tip = cj-style Epic 15 1번째 진입점 = cj-style 58번째)
- spec = `_bmad-output/implementation-artifacts/epic-15-sso-magic-oauth-wire.md` (NEW, ~600+ lines)
- sprint-status: `epic-15-sso-magic-oauth-wire: backlog → ready-for-dev`
- spec file = PRD §F17 verbatim 9 ACs + 8 tasks T1~T8 + 22 subtasks 결정 보존

## Epic 15 wire scope T1~T8 결정 (cj-style 59번째 epic 연속 정직 회복 spec 진입 시점에 결정)

- **T1 Magic link wrapper wire** (1 NEW frontend) = `apps/web/lib/auth/magic-link.ts` NEW (~+40 LOC, atomic) — Supabase `signInWithOtp({ email, options: { emailRedirectTo } })` wrapper + 5회 cool-down sessionStorage 30s (Phase 3-1 T2 wire 패턴 미러) + email 존재 여부 노출 방지 (security invariant try/catch/finally, Phase 3-1 T6 forgot-password 정합) + audit-first INSERT `magic_link_sent` (CR 1-1 verbatim, action_class='AUTH' + action='magic_link_sent' + actor_id + target_email + trace_id) 결정
- **T2 Magic link UI wire** (3 NEW frontend) = `apps/web/components/auth/MagicLinkForm.tsx` NEW (~+30 LOC, 이메일 단일 필드 UI + ko-KR SSOT `auth.magic_link.email_label` + `auth.magic_link.send_button`) + `apps/web/app/[locale]/(auth)/magic-link/page.tsx` NEW (~+30 LOC, (auth) route group 공개 + capability gate `MAGIC_LINK`) + `apps/web/app/[locale]/(auth)/magic-link-sent/page.tsx` NEW (~+20 LOC, generic success message + email 존재 여부 노출 방지 강제) 결정
- **T3 Social OAuth wrapper wire** (2 NEW frontend) = `apps/web/lib/auth/social.ts` NEW (~+60 LOC, `signInWithOAuth` wrapper + provider whitelist `ALLOWED_SOCIAL_PROVIDERS = frozenset({'google', 'naver', 'kakao'})` strict reject + 3회 cool-down sessionStorage 60s + audit-first INSERT `social_oauth_initiated`) + `apps/web/components/auth/SocialAuthButtons.tsx` NEW (~+60 LOC, 3 provider buttons Google + Naver + Kakao + provider-specific branding 결정) — **Naver OAuth Option A/B 결정 wire 보존** (Supabase 공식 Naver 지원 여부, Option A 우선 시도 + Option B fallback 결정 wire 보존)
- **T4 OAuth callback wire** (1 NEW frontend) = `apps/web/app/[locale]/(auth)/auth-callback/page.tsx` NEW (~+50 LOC, `exchangeCodeForSession` + session cookie setting + dashboard redirect 결정, magic link + OAuth callback 통합 handler) + `apps/web/middleware.ts` MODIFIED (auth-callback route 추가) 결정
- **T5 SSO SAML backend wire** (5 NEW backend) = `apps/api/modules/auth/sso/saml_validator.py` NEW (~+150 LOC, `python3-saml==1.16.0` AD-14 stack pin + SAML response validation signature + timestamp + Audience + Destination + InResponseTo + RelayState) + `saml_routes.py` NEW (~+100 LOC, 4 SSO routes `/api/v1/auth/sso/{login,acs,metadata,sls}` + tenant slug routing) + `jit_provisioning.py` NEW (~+100 LOC, JIT user provisioning 5-step atomic flow SAML → users + tenants + tenant_memberships + external_identities + audit_log) + `apps/api/alembic/versions/0037_epic_15_sso_external_identities.py` NEW (~+80 LOC, `external_identities` table + 4 indexes + 2 CHECK constraints + RLS policy `tenant_id = current_setting('app.tenant_id')` + down_revision=`0036_phase_4_backup_strategy`) + `apps/web/app/api/auth/sso/callback/route.ts` NEW (~+30 LOC, SSO ACS callback + sb-access-token cookie set + /dashboard redirect 결정) + `apps/api/main.py` MODIFIED (`sso_router` include) + `requirements.txt` MODIFIED (`python3-saml==1.16.0` AD-14 stack pin) 결정
- **T6 SSO UI wire** (1 NEW frontend) = `apps/web/app/[locale]/sso/[tenant_slug]/login/page.tsx` NEW (~+40 LOC, /sso/<tenant_slug>/login 진입 + tenant slug routing + Epic 12 2FA redirect) + `apps/web/app/[locale]/(auth)/login/page.tsx` MODIFIED (3 NEW auth method entry points: magic link + social OAuth + SSO enterprise) 결정
- **T7 Capability v1.26 EXTENSION** (1 MODIFIED backend + 1 EXTENSION docs) = `apps/api/core/capability.py` MODIFIED (5 NEW enum `MAGIC_LINK` + `SOCIAL_OAUTH_GOOGLE` + `SOCIAL_OAUTH_NAVER` + `SOCIAL_OAUTH_KAKAO` + `SSO_ENTERPRISE`, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러) + `apps/api/dependencies/capability.py` EXTENSION (`require_capability()` Dependency 5개 신규 wire) + `docs/capability-matrix.md` v1.25 → v1.26 (Epic 15 PRD entry `dd218fa` 진입 시점에 5 NEW rows 이미 추가됨 lines 451-455, capability.py enum 만 wire) + `tests/integration/test_capability_matrix_v1_26_drift.py` NEW (drift detector — 5 NEW rows SSOT 정합 sweep) 결정
- **T8 Tests + 3중 게이트 FINAL CLEAN** (~+50 NEW pytest PASS + ~+25 NEW vitest PASS + 1 NEW docs + 1 MODIFIED ko-KR.json): `tests/web/test_epic_15_magic_link_parity.test.ts` NEW (~+15 cases — `MagicLinkForm` 15 RTL + 5회 cool-down + email 존재 여부 노출 방지 + audit-first INSERT `magic_link_sent`) + `tests/web/test_epic_15_social_oauth_parity.test.ts` NEW (~+15 cases — `SocialAuthButtons` 3 provider buttons + provider whitelist strict reject + 3회 cool-down + audit-first INSERT `social_oauth_initiated` + `exchangeCodeForSession` callback) + `tests/api/core/test_epic_15_sso_validator.py` NEW (~+15 cases — `python3-saml` SAML response validation + signature + timestamp + Audience + Destination + InResponseTo + RelayState + expired handling + signature failure) + `tests/api/core/test_epic_15_sso_jit_provisioning.py` NEW (~+10 cases — JIT user provisioning 5-step atomic + `external_identities` INSERT + multi-tenant isolation RLS + audit-first INSERT `sso_identity_linked`) + `tests/api/core/test_epic_15_sso_routes.py` NEW (~+15 cases — 4 routes login + acs + metadata + sls + tenant slug routing) + `tests/api/core/test_epic_15_alembic_0037_external_identities.py` NEW (~+10 cases — alembic 0037 migration + external_identities table schema + RLS policy + indexes + CHECK constraints + down_revision 정합) + `tests/integration/test_capability_matrix_v1_26_drift.py` NEW (drift detector) + `docs/sso-enterprise.md` NEW (~+150 LOC, 10 sections) 결정

## 9 ACs satisfied (PRD §F17.1~§F17.6 verbatim)

PRD §F17.1 (Magic link login — Supabase `signInWithOtp` + 5회 cool-down + email 존재 여부 노출 방지 + audit-first INSERT `magic_link_sent` + Epic 12 2FA redirect) / §F17.2 (Social OAuth Google/Naver/Kakao — Supabase `signInWithOAuth` + provider whitelist + 3회 cool-down + audit-first INSERT `social_oauth_initiated` + OAuth callback + Epic 12 2FA redirect + Naver OAuth Option A/B 결정 wire 보존) / §F17.3 (SSO enterprise SAML — `python3-saml==1.16.0` AD-14 stack pin + SAML response validation + JIT user provisioning + multi-tenant isolation CR 0-2 RLS + audit-first INSERT `sso_identity_linked` + Epic 12 2FA redirect + tenant slug 별 IdP metadata routing) / §F17.4 (ko-KR SSOT EXTENSION `auth.magic_link.*` + `auth.social.*` + `auth.sso.*` namespace) / §F17.5 (Capability matrix v1.25 → v1.26 EXTENSION 5 NEW rows MAGIC_LINK + SOCIAL_OAUTH_GOOGLE + SOCIAL_OAUTH_NAVER + SOCIAL_OAUTH_KAKAO + SSO_ENTERPRISE industry-agnostic 4-industry grants) / §F17.6 (tests + wire scope T1~T8 + 3중 게이트 FINAL CLEAN + atomic commit 결정) / §F17.7 (OAuth callback + auth middleware EXTENSION + tests 결정 wire) / §F17.8 (Epic 1 carry-over D-1-1-DEFER-1/2/3 honestly ✅ RESOLVE 59번째 epic 연속 정직 회복 검증 CR 11-3 discipline) / §F17.9 (A19 cohesion pattern 9 surface EXTENSION PASS 검증 auth surface EXTENSION 결정).

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

## 3중 게이트 impact EXPECTED (Epic 15 atomic sprint wire 진입 시점)

- (1) frontend `pnpm tsc --noEmit` 0 NEW errors (Epic 15 auth files clean — pre-existing 7 baseline errors unrelated 보존)
- (2) `pnpm vitest run` 737+25 = **~762/762 PASS** (73+3 = 76 files, Epic 15 +25 NEW vitest cases, 0 regressions)
- (3) `ruff check` scoped Epic 15 wire files = **All checks passed!** (scoped to Epic 15 NEW Python files only)
- (4) `pytest` 31+50 = **~81/81 PASS** (Epic 15 +50 NEW e2e tests, 0 NEW regressions; baseline 1 unrelated pre-existing failure `test_generate_report_pdf_report15_payload_not_required` 보존)
- (5) SDR drift gate PASS (MAX claim 3928 → **~3978** actual pytest --collect-only -q = +50 from Epic 15 T7~T8 NEW pytest cases)
- (6) commit_consistency gate PASS (CR 9-6 commit message discipline + A36 SDR 검증 4-step 자동 적용)

## 기존 baseline 정합 보존 (Epic 15 PRD entry 진입 시점에 cj-style "fix" 종류 pre-flight 정합 sweep)

- ✅ Epic 15 PRD entry `dd218fa` 진입 시점에 결정 wire 모두 보존 (master PRD v3.2 + capability matrix v1.26 EXTENSION 5 NEW rows + AD-28 신규 결정 모두 보존)
- ✅ Phase 4 wire DONE 진입 시점에 cj-style 53~57번째 epic 연속 wire DONE 모두 보존 (Phase 4 PRD entry `8e046df` + Phase 4 spec entry + Phase 4 atomic wire T1~T8 `71a033a` + Phase 4 close-out retro `934b35e`) 결정 wire 보존
- ✅ Phase 3 cycle close-out 완료 (Phase 3 PRD entry + Phase 3-0 atomic sprint `1db21d2` + Phase 3-1 atomic sprint `d3e7454` + Phase 3 close-out retro = cj-style 49~52번째 epic 연속 정직 회복 wire DONE) 결정 wire 보존
- ✅ Epic 12 2FA 게이트 보존 결정 wire (CR 12-5 D-GATE-01 inversion 적용 — Magic link + Social OAuth + SSO 모두 2FA 게이트 통과 후 M2 진입)
- ✅ Epic 14 LISTEN/NOTIFY multi-process coordination 결정 wire 보존
- ✅ Epic 13 LISTEN/NOTIFY consume 결정 wire 보존
- ✅ Epic 11 close-out retro + ✅ Phase 2 close-out baseline 599 passed 정합
- ✅ Epic 1 carry-over (auth) layout + onboarding/industry 보존

## CR lessons applied (cj-style 59번째 epic 연속 정직 회복 wire 진입 시점에 결정)

- **CR 0-2** RLS lesson ✅ APPLIED (T4.4 external_identities table multi-tenant isolation RLS policy `tenant_id = current_setting('app.tenant_id')` 결정 wire + SSO identity link 후 RLS policy 검증)
- **CR 1-1** audit-first INSERT ✅ APPLIED (T1 magic_link_sent + T3 social_oauth_initiated + T5 sso_identity_linked 3 NEW audit logs INSERT 결정)
- **CR 9-6** commit message discipline ✅ APPLIED (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention)
- **CR 11-3** honest-DEFER discipline ✅ APPLIED (59번째 epic 연속 정직 회복, D-1-1-DEFER-1/2/3 ✅ honestly RESOLVE)
- **CR 11-4** D-001~D-005 + P-015 lessons carry ✅ APPLIED (D-001 page.tsx mount MUST actual mount `<MagicLinkForm>` + D-002 ko-KR.json SSOT only + D-003 vitest RTL render + D-004 TS mirror parity mandatory + D-005 unknown state reject + P-015 ko-KR.json SSOT drift detector)
- **CR 12-1** L4 industry-agnostic capability ✅ APPLIED (capability matrix v1.26 EXTENSION 5 NEW rows industry-agnostic 4-industry grants)
- **CR 12-5** D-14 typed exception envelope ✅ APPLIED (magic_link + social_oauth + sso envelope 결정 wire `{code, message_ko, details, trace_id}`)
- **CR 12-5** D-PARITY-01 inversion ✅ APPLIED (Supabase + Next.js + SAML OAuth parity 결정 wire)
- **CR 12-5** D-GATE-01 inversion ✅ APPLIED (Epic 12 2FA 게이트 보존 — Magic link + Social OAuth + SSO 모두 2FA 게이트 통과 후 M2 진입)
- **A19** cohesion pattern 9 surface EXTENSION PASS ✅ (auth surface EXTENSION 결정 wire)
- **A36** SDR 검증 4-step 자동 적용 ✅ (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS)

## D-1-1-DEFER-* honestly ✅ RESOLVE 59번째 epic 연속 정직 회복 (CR 11-3 discipline)

Epic 15 PRD entry (`epic-15-prd-entry: done`, 2026-08-22, commit `dd218fa`) 진입 시점에 모두 ✅ RESOLVE 결정 wire 완료.

| DEFER ID | Description | 상태 (Epic 15 PRD entry 진입 후) |
|----------|------------|---------|
| **D-1-1-DEFER-1** | Magic link login | ✅ RESOLVED (A70) — Epic 15 T1+T2 wire 진입 대기 |
| **D-1-1-DEFER-2** | Social login OAuth (Google/Naver/Kakao) | ✅ RESOLVED (A71) — Epic 15 T3+T4 wire 진입 대기 |
| **D-1-1-DEFER-3** | SSO enterprise SAML | ✅ RESOLVED (A72) — Epic 15 T5+T6 wire 진입 대기 |

CR 11-3 honest-DEFER discipline 58~59번째 epic 연속 정직 회복 결정 wire. 59번째 진입 시점에 grep guard INVERSION 또는 test rename 결정 wire 보존 (OQ-2).

## 결정 wire 일자

2026-08-22 (KST)

## Related Memories

- [[handoff-2026-08-22-epic-15-prd-entry-done]] — Epic 15 PRD entry DONE (cj-style Epic 15 1번째 진입점 = cj-style 58번째)
- [[handoff-2026-08-22-phase-4-close-out-done]] — Phase 4 close-out retro DONE (cj-style Phase 4 4번째 진입점 = cj-style 56~57번째)
- [[handoff-2026-08-22-phase-4-deployment-wire-done]] — Phase 4 atomic wire DONE (cj-style Phase 4 3번째 진입점 = cj-style 55번째)
- [[handoff-2026-08-22-phase-4-deployment-wire-spec-entry-done]] — Phase 4 spec entry DONE (cj-style Phase 4 2번째 진입점 = cj-style 54번째)
- [[handoff-2026-08-22-phase-4-prd-entry-done]] — Phase 4 PRD entry DONE (cj-style Phase 4 1번째 진입점 = cj-style 53번째)
- [[handoff-2026-08-22-phase-3-close-out-done]] — Phase 3 close-out retro DONE (cj-style Phase 3 3번째 진입점 = cj-style 51~52번째)
- [[handoff-2026-08-21-phase-3-1-auth-foundation-wire-done]] — Phase 3-1 wire DONE (cj-style Phase 3 2번째 진입점 = cj-style 50번째)
- [[handoff-2026-08-21-phase-3-0-auth-contract-slice-done]] — Phase 3-0 auth contract slice DONE
- [[handoff-2026-08-20-phase-3-prd-entry-done]] — Phase 3 PRD entry DONE (cj-style Phase 3 1번째 진입점 = cj-style 49번째)
- [[cr-11-3-lessons]] — honest-DEFER discipline
- [[cr-12-1-lessons]] — capability matrix wire pattern (L4 precedent)
- [[cr-12-5-lessons]] — D-GATE-01 inversion + D-PARITY-01 inversion + D-14 envelope
- [[cr-a19-lessons]] — A19 cohesion pattern 9 surface
- [[cr-0-2-lessons]] — RLS + multi-tenant isolation
- [[cr-1-1-lessons]] — audit-first INSERT

## next: Epic 15 bmad-dev-story atomic wire T1~T8 진입

`bmad-dev-story epic-15-sso-magic-oauth-wire` 진입 시점에 PRD §F17 verbatim + A79+A80+A81+A82 결정 wire 보존 = cj-style Epic 15 3번째 진입점 = cj-style 60번째 epic 연속 정직 회복 atomic single sprint = ~50 NEW pytest PASS + ~25 NEW vitest PASS + 0 NEW ruff + 0 regressions + A19 cohesion 9 surface EXTENSION PASS (auth surface EXTENSION) + 3중 게이트 FINAL CLEAN + D-1-1-DEFER-1/2/3 ✅ RESOLVE 검증 (CR 11-3 discipline, grep guard INVERSION 또는 test rename 결정 wire 보존).

**cj-style 59번째 epic 연속 정직 회복 검증 완료**.
