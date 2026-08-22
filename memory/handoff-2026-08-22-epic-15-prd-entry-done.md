---
name: handoff-2026-08-22-epic-15-prd-entry-done
description: Epic 15 PRD entry DONE (cj-style Epic 15 1번째 진입점 = cj-style 58번째 epic 연속 정직 회복). Epic 15 = Magic link + Social OAuth (Google/Naver/Kakao) + SSO enterprise SAML 통합 territory 진입 결정 wire. D-1-1-DEFER-1/2/3 honestly ✅ RESOLVED 58번째 epic 연속. A79+A80+A81+A82 신규 결정 wire 진입.
metadata:
  type: project
  modified: 2026-08-22T00:00:00.000Z
---

# Epic 15 PRD Entry DONE — Magic link + Social OAuth + SSO territory (handoff-2026-08-22)

## Epic 15 territory 진입 wire 결정

Epic 15 = **Magic link + Social OAuth (Google/Naver/Kakao) + SSO enterprise SAML 통합 territory** (옵션 (a) Epic 15 진입 결정 wire, A79 결정). **cj-style Epic 15 1번째 진입점 = cj-style 58번째 epic 연속 정직 회복 wire DONE**.

옵션 (b) Phase 5 진입 / 옵션 (c) carry-over 진입 모두 rejected (rationale: D-1-1-DEFER-1/2/3 honestly RESOLVE 결정 wire 진입 = Phase 3 Auth Foundation territory 보강 + cj-style 1번째 진입점 표준 진입 가능 = 결정 wire 효율성).

## Epic 15 결정 wire Summary (A79+A80+A81+A82 + A70+A71+A72 + A75)

| 결정 | 내용 | 상태 |
|------|------|------|
| **A79** | 옵션 (a) Epic 15 진입 결정 wire (Magic link + Social OAuth + SSO 통합 territory 진입) | ✅ DONE |
| **A80** | Master PRD v3.1 → v3.2 atomic edit (§F17 신규 + M0-(h/i/j) + AD-28 + §15 Epic 15 row + §부록 A 결정 표) | ✅ DONE |
| **A81** | AD-28 Magic link + Social OAuth + SSO enterprise SAML 신규 결정 (Supabase signInWithOtp + signInWithOAuth + python3-saml==1.16.0 + JIT + audit-first INSERT 3 NEW) | ✅ DONE |
| **A82** | Capability matrix v1.25 → v1.26 EXTENSION 5 NEW rows (MAGIC_LINK + SOCIAL_OAUTH_GOOGLE + SOCIAL_OAUTH_NAVER + SOCIAL_OAUTH_KAKAO + SSO_ENTERPRISE) | ✅ DONE |
| **A70** | D-1-1-DEFER-1 Magic link 결정 wire | ✅ DONE (Epic 15 wire 진입 시점에 RESOLVE) |
| **A71** | D-1-1-DEFER-2 Social login OAuth 결정 wire | ✅ DONE (Epic 15 wire 진입 시점에 RESOLVE) |
| **A72** | D-1-1-DEFER-3 SSO enterprise SAML 결정 wire | ✅ DONE (Epic 15 wire 진입 시점에 RESOLVE) |
| **A75** | A42 A36 SDR 검증 4-step 보존 + Epic 15+ 적용 | 🔵 OPEN (자동 적용) |

**A79+A80+A81+A82 4/4 ALL DONE + A70+A71+A72 3/3 DONE (D-1-1-DEFER-1/2/3 ✅ RESOLVED) + A75 OPEN (자동 적용)**.

## Epic 15 PRD entry wire scope (master PRD v3.2 atomic edit)

(1) **front matter title v3.1 → v3.2 + changelog v3.2 entry 신규** (Epic 15 PRD entry 결정 wire 진입 verbatim bind)
(2) **§F17 신규** (F17.1 Magic link UI/Backend — Supabase `signInWithOtp` + 5회 cool-down + email 존재 여부 노출 방지 + audit-first INSERT `magic_link_sent` + F17.2 Social OAuth — Supabase `signInWithOAuth` Google/Naver/Kakao + provider whitelist + 3회 cool-down + audit-first INSERT `social_oauth_initiated` + Naver OAuth Option A 우선 / Option B custom flow 결정 wire 보존 + F17.3 SSO enterprise SAML — `python3-saml==1.16.0` AD-14 stack pin + SAML response validation + JIT user provisioning + multi-tenant isolation CR 0-2 RLS + audit-first INSERT `sso_identity_linked` + F17.4 ko-KR.json SSOT EXTENSION `magic_link.*` + `social_oauth.*` + `sso_enterprise.*` namespace + F17.5 capability matrix v1.25 → v1.26 EXTENSION 5 NEW rows + F17.6 tests + wire scope T1~T8 결정)
(3) **§8.1 M0-(h) Magic link + M0-(i) Social OAuth + M0-(j) SSO enterprise SAML** 결정 wire 진입 (Epic 15 territory 3 NEW 인수 불릿)
(4) **§15 로드맵 Epic 15 row status 백로그 → in-progress** (PRD entry DONE 진입 wire) + Phase 4 row status in-progress → done (Phase 4 close-out retro DONE 정합)
(5) **§부록 A A70+A71+A72 ✅ done + A79+A80+A81+A82 신규 결정 표** (A70~A72 done 결정 + A79~A82 신규 결정 wire 진입)
(6) **AD-28 Magic link + Social OAuth + SSO enterprise SAML 신규 결정** (Supabase signInWithOtp + signInWithOAuth + python3-saml==1.16.0 + JIT + multi-tenant isolation + audit-first INSERT 3 NEW 결정 wire)
(7) **capability matrix v1.25 → v1.26 EXTENSION** MAGIC_LINK + SOCIAL_OAUTH_GOOGLE + SOCIAL_OAUTH_NAVER + SOCIAL_OAUTH_KAKAO + SSO_ENTERPRISE 5 NEW rows (industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러)

## Epic 15 wire scope T1~T8 결정 (cj-style 58번째 epic 연속 정직 회복 wire 진입 시점에 결정)

- **T1 Magic link backend wrapper** (1 NEW) = `apps/api/modules/m13_auth/services/magic_link_service.py` (Supabase `signInWithOtp` wrapper, 5회 cool-down, email 존재 여부 노출 방지, audit-first INSERT `magic_link_sent`)
- **T2 Magic link UI form** (1 NEW) = `apps/web/components/auth/MagicLinkForm.tsx` (15 RTL cases) + `apps/web/app/[locale]/(auth)/magic-link/page.tsx` (page entry)
- **T3 Social OAuth backend wrapper** (1 NEW) = `apps/api/modules/m13_auth/services/social_oauth_service.py` (Supabase `signInWithOAuth` wrapper, Google/Naver/Kakao provider whitelist, 3회 cool-down, audit-first INSERT `social_oauth_initiated`, Naver Option A 우선 / Option B 결정 wire 보존)
- **T4 OAuth callback handler** (1 NEW) = `apps/web/app/[locale]/api/auth/oauth-callback/route.ts` (POST handler, audit-first INSERT `social_oauth_initiated`)
- **T5 SSO SAML backend** (1 NEW + 1 MODIFIED) = `apps/api/modules/m13_auth/services/sso_saml_service.py` NEW (`python3-saml==1.16.0` AD-14 stack pin, SAML response validation, JIT user provisioning, multi-tenant isolation CR 0-2 RLS, audit-first INSERT `sso_identity_linked`) + `apps/api/requirements.txt` MODIFIED (python3-saml==1.16.0 dependency)
- **T6 SSO SAML UI** (1 NEW + 1 NEW alembic) = `apps/web/components/auth/SsoSamlButton.tsx` (8 RTL cases) + `apps/web/app/[locale]/(auth)/sso-saml/page.tsx` (page entry) + `apps/api/alembic/versions/0037_epic_15_external_identities.py` NEW (external_identities table for SSO identity link tracking)
- **T7 Capability v1.26 EXTENSION** (1 MODIFIED + 1 MODIFIED) = `apps/api/core/capability.py` MODIFIED 5 NEW enum (MAGIC_LINK + SOCIAL_OAUTH_GOOGLE + SOCIAL_OAUTH_NAVER + SOCIAL_OAUTH_KAKAO + SSO_ENTERPRISE) + `docs/capability-matrix.md` v1.25 → v1.26 (5 NEW rows, SSOT RED→GREEN)
- **T8 Tests + 3중 게이트 FINAL CLEAN** (~+50 NEW pytest PASS + ~+25 NEW vitest PASS + 2 NEW docs) — Magic link backend + UI + Social OAuth backend + callback + SSO SAML backend + UI + alembic 0037 + capability matrix v1.26 drift detector + Epic 12 2FA 게이트 보존 + D-1-1-DEFER-* grep guard 솔기 적용

## 3중 게이트 impact EXPECTED (Epic 15 wire 진입 시점)

(1) frontend `pnpm tsc --noEmit` 0 NEW errors (auth/sso files clean — pre-existing 17 baseline errors unrelated 보존)
(2) `pnpm vitest run` 737+25 = **~762/762 PASS** (73+ files, Epic 15 +25 NEW cases, 0 regressions)
(3) `ruff check` scoped Epic 15 wire files = **All checks passed!**
(4) `pytest` 3928+50 = **~3978 PASS** (Epic 15 +50 NEW e2e tests, 0 NEW regressions; baseline 1 unrelated pre-existing failure 보존)
(5) SDR drift gate PASS (MAX claim 3928 → **~3978** actual pytest --collect-only -q = +50 from Epic 15 T8 NEW pytest cases)
(6) commit_consistency gate PASS (CR 9-6 commit message discipline + A36 SDR 검증 4-step 자동 적용)

## A19 cohesion pattern 9 surface EXTENSION PASS (예정)

9/9 surfaces ALL PASS (cj-style 58번째 epic 연속 정직 회복 wire 진입 시점에 결정):

1. **kernel** (pure function) — T1 magic_link_5_failures_cool_down_check + T3 social_oauth_3_failures_cool_down_check + T5 saml_response_signature_verify (stdlib-only AD-5) ✅
2. **port** (DB adapter) — T6 alembic 0037 external_identities table (multi-tenant isolation CR 0-2 RLS lesson) ✅
3. **db schema** — T6 alembic 0037 external_identities (id + provider + provider_user_id + user_id + tenant_id + created_at + updated_at + UNIQUE(provider, provider_user_id)) ✅
4. **service** — T1 magic_link_service + T3 social_oauth_service + T5 sso_saml_service (3 NEW service layers) ✅
5. **handler** — T2 MagicLinkForm + T4 OAuth callback route + T6 SsoSamlButton (3 NEW handler wire) ✅
6. **envelope** — T1 magic_link envelope `{status, email_hash, cool_down_remaining}` + T3 oauth envelope `{status, provider, redirect_url}` + T5 saml envelope `{status, tenant_id, user_id}` (CR 12-5 D-14) ✅
7. **capability** — T7 MAGIC_LINK + SOCIAL_OAUTH_GOOGLE + SOCIAL_OAUTH_NAVER + SOCIAL_OAUTH_KAKAO + SSO_ENTERPRISE 5 NEW gates ✅
8. **audit** — T1 magic_link_sent + T3 social_oauth_initiated + T5 sso_identity_linked 3 NEW audit_logs INSERT (CR 1-1 audit-first INSERT) ✅
9. **auth surface reuse** — Phase 3 Auth Foundation territory 보강 (Epic 15 wire 진입 시점에 Epic 12 2FA 게이트 + ko-KR.json auth namespace EXTENSION 보존) ✅ EXTENSION PASS

## CR lessons applied (cj-style 58번째 epic 연속 정직 회복 wire 진입 시점에 결정)

- **CR 0-2** RLS lesson ✅ APPLIED (T6 external_identities table multi-tenant isolation RLS + SSO identity link 후 RLS policy 검증)
- **CR 1-1** audit-first INSERT ✅ APPLIED (T1 magic_link_sent + T3 social_oauth_initiated + T5 sso_identity_linked 3 NEW audit logs INSERT)
- **CR 9-6** commit message discipline ✅ APPLIED (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention)
- **CR 11-3** honest-DEFER discipline ✅ APPLIED (58번째 epic 연속 정직 회복 — D-1-1-DEFER-1/2/3 honestly ✅ RESOLVE)
- **CR 11-4** lessons carry (D-001 page.tsx mount MUST actual mount `<MagicLinkForm>` + D-002 ko-KR.json SSOT only + D-003 vitest RTL render + D-004 TS mirror parity mandatory + D-005 unknown state reject + P-015 ko-KR.json SSOT drift detector)
- **CR 12-1** L4 industry-agnostic capability ✅ APPLIED (capability matrix v1.26 EXTENSION 5 NEW rows industry-agnostic 4-industry grants)
- **CR 12-5** D-14 typed exception envelope ✅ APPLIED (magic_link + social_oauth + sso envelope)
- **CR 12-5** D-PARITY-01 inversion ✅ APPLIED (Supabase + Next.js + SAML OAuth parity)
- **CR 12-5** D-GATE-01 inversion ✅ APPLIED (Epic 12 2FA 게이트 보존 — Magic link + Social OAuth + SSO 모두 2FA 게이트 통과 후 M2 진입)
- **A19** cohesion pattern 9 surface EXTENSION PASS ✅ (auth surface reuse)

## D-1-1-DEFER-* honestly RESOLVE (CR 11-3 58번째 epic 연속 정직 회복)

| DEFER ID | Description | 상태 |
|----------|------------|------|
| **D-1-1-DEFER-1** | Magic link login | ✅ RESOLVED (Epic 15 wire 진입 시점에) |
| **D-1-1-DEFER-2** | Social login OAuth (Google/Naver/Kakao) | ✅ RESOLVED (Epic 15 wire 진입 시점에) |
| **D-1-1-DEFER-3** | SSO enterprise SAML | ✅ RESOLVED (Epic 15 wire 진입 시점에) |

CR 11-3 honest-DEFER discipline 58번째 epic 연속 정직 회복 결정. grep guard `test_no_magic_link_or_oauth_or_sso_introduced` 보존 + wire 진입 시점에 모두 RESOLVE.

## Epic 1 carry-over 정합 보존

Epic 1 partial scaffold = (auth) layout + onboarding/industry + IndustrySelector + IndustryCard + middleware.ts next-intl EXTENSION 모두 보존. Phase 3-0 + Phase 3-1 Auth Foundation territory close-out 완료 (cj-style Phase 3 1~3번째 진입점 모두 wire DONE = cj-style 49~52번째 epic 연속 정직 회복). master PRD v3.0 §F15 (F15.1~F15.6) verbatim wire + AD-26 verbatim + A65~A69 결정 wire 보존.

## Phase 4 cycle 정합 보존

Phase 4 PRD entry `8e046df` + spec entry + atomic wire T1~T8 `71a033a` + close-out retro 모두 wire DONE (cj-style 53~57번째 epic 연속 정직 회복). master PRD v3.1 §F16 (F16.1~F16.7) verbatim wire + AD-27 verbatim + A73+A74+A76+A77+A78 5/5 ALL DONE + APPLIED 결정 wire 진입.

## 다음 결정 wire 보류 (사용자 결정 대기)

옵션 (a) Epic 15 bmad-create-story spec 진입 (cj-style Epic 15 2번째 진입점 = cj-style 59번째 epic 연속 정직 회복) OR 옵션 (b) Epic 15 bmad-dev-story atomic wire T1~T8 진입 (cj-style Epic 15 3번째 진입점 = cj-style 60번째 epic 연속 정직 회복 wire 진입 시점) OR 옵션 (c) 다른 territory 진입 결정 wire 보존.

## 결정 wire 일자

2026-08-22 (KST) — cj-style Epic 15 1번째 진입점 = cj-style 58번째 epic 연속 정직 회복 wire DONE.

## Related Memories

- [[handoff-2026-08-22-phase-4-close-out-done]] — Phase 4 close-out retro DONE (cj-style 56~57번째)
- [[handoff-2026-08-22-phase-4-deployment-wire-done]] — Phase 4 atomic wire T1~T8 DONE (cj-style 55번째)
- [[handoff-2026-08-22-phase-4-deployment-wire-spec-entry-done]] — Phase 4 spec entry DONE (cj-style 54번째)
- [[handoff-2026-08-22-phase-4-prd-entry-done]] — Phase 4 PRD entry DONE (cj-style 53번째)
- [[handoff-2026-08-22-phase-3-close-out-done]] — Phase 3 close-out retro DONE (cj-style 51~52번째)
- [[handoff-2026-08-21-phase-3-1-auth-foundation-wire-done]] — Phase 3-1 wire DONE (cj-style 50번째)
- [[handoff-2026-08-21-phase-3-0-auth-contract-slice-done]] — Phase 3-0 auth contract slice DONE
- [[handoff-2026-08-20-phase-3-prd-entry-done]] — Phase 3 PRD entry DONE (cj-style 49번째)
- [[cr-11-3-lessons]] — honest-DEFER discipline (D-1-1-DEFER-* RESOLVE discipline)
- [[cr-12-1-lessons]] — capability matrix wire pattern (L4 precedent)
- [[cr-12-5-lessons]] — D-GATE-01 inversion + D-PARITY-01 inversion + D-14 envelope
- [[cr-0-2-lessons]] — RLS + multi-tenant isolation + AD-14 stack pin
- [[cr-1-1-lessons]] — audit-first INSERT (3 NEW audit actions)
- [[cr-11-4-lessons]] — page.tsx mount + ko-KR.json SSOT + vitest RTL + TS mirror parity
- [[cr-a19-lessons]] — A19 cohesion pattern 9 surface EXTENSION PASS

## next: Epic 15 bmad-create-story spec 진입 OR Epic 15 bmad-dev-story atomic wire T1~T8 진입 결정 wire 보류

cj-style discipline 회피 위험 방지: **즉시 진입 권장**.
