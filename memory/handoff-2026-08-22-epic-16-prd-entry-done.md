---
name: handoff-2026-08-22-epic-16-prd-entry-done
description: Epic 16 PRD entry DONE (cj-style Epic 16 1번째 진입점 = cj-style 67번째 epic 연속 정직 회복 atomic docs-only wire). 옵션 (a) Epic 16 진입 결정.
metadata:
  type: project
---

# Epic 16 PRD entry DONE — cj-style 67번째 epic 연속 정직 회복

**Date:** 2026-08-22 (KST)
**Cycle:** Epic 16 PRD entry (cj-style Epic 16 1번째 진입점 = cj-style 67번째)
**Wire scope:** 7 files atomic (4 MODIFIED + 3 NEW = docs only, no code/test)

## 1. 결정 wire 요약

- **옵션 (a) Epic 16 진입 결정** — 1st release close-out retro `25dccaf` §12 "Next unblocked 결정 wire 보류" 의 4 options 중 사용자 권장 결정.
- **rationale 4종**:
  1. Epic 15 SSO enterprise SAML forward-reference `docs/sso-enterprise.md` §4.1 step 3 `Configure tenant_idps (TODO Epic 16)` verbatim 자연스러운 carry-over chain 결정 wire.
  2. Epic 15 territory carry-over chain (cj-style 58~61→67번째) = tenant IdP admin management 가 natural next territory 결정 wire.
  3. cj-style discipline 회피 위험 방지 = 62~66번째 누적 cycle 더 미루면 cycle 끊김 위험.
  4. 비즈니스 우선순위 = 1차 출시 후 enterprise SSO onboarding 필수 (Epic 15 SSO enterprise SAML 은 response validation + JIT provisioning 까지 wire, tenant IdP config admin UI/API 가 Epic 16 territory 결정 wire 진입).
- **rejected**: 옵션 (b) Phase 5 / 옵션 (c) carry-over / 옵션 (d) 추가 1st release 모두 rejected.

## 2. territory 정의 (PRD §F19 verbatim)

- **§F19.1 `tenant_idps` table** — alembic `0038_epic_16_tenant_idps.py` NEW, 13 columns + RLS policy `tenant_id = current_setting('app.tenant_id')::uuid` 결정 (CR 0-2 RLS lesson 적용) + UNIQUE constraint `(tenant_id, idp_entity_id)` + audit trigger.
- **§F19.2 IdP metadata XML validation service** — `apps/api/modules/auth/sso/idp_metadata_validator.py` NEW ~120 LOC, 8 validation steps (XML well-formedness + EntityDescriptor root + entityID 추출 + IDPSSODescriptor + X509Certificate PEM wrap + SingleSignOnService HTTPS + SingleLogoutService + tenant slug 매칭) + `IdPMetadata` TypedDict 6 fields.
- **§F19.3 Tenant IdP CRUD API 5 routes** — `apps/api/modules/auth/sso/idp_admin_routes.py` NEW ~150 LOC (`GET / POST / PUT / DELETE / TEST /api/v1/admin/tenant/{tenant_slug}/idp`) + owner/admin Dependency + audit-first INSERT 4 NEW (`tenant_idp_created` + `tenant_idp_updated` + `tenant_idp_deleted` + `tenant_idp_tested`).
- **§F19.4 Tenant IdP admin UI** — `apps/web/app/[locale]/(dashboard)/settings/sso/page.tsx` NEW ~150 LOC + 4 components (`TenantIdPConfigForm` + `TenantIdPStatusBadge` + `TenantIdPTestResultModal` + `TenantIdPDeleteConfirmDialog`) + ko-KR.json `settings.sso.*` namespace EXTENSION 12 keys + `apps/web/lib/auth/admin-idp-client.ts` NEW.
- **§F19.5 Per-tenant IdP routing EXTENSION** — Epic 15 `apps/api/modules/auth/sso/saml_routes.py` MODIFIED (acme backward compatibility 보존 + ACS `idp_x509_cert` 동적 로딩) + alembic 0038 acme 데이터 migration + capability gate per-tenant on/off.
- **§F19.6 Capability gate `TENANT_IDP_MANAGEMENT`** — capability.py MODIFIED + capability-matrix.md v1.27 → v1.28 EXTENSION 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅ + drift detector.
- **§F19.7 Tests + wire scope T1~T8** — T1 tenant_idps table wire + T2 IdP metadata validator wire + T3 Tenant IdP CRUD API wire + T4 admin UI wire + T5 per-tenant IdP routing EXTENSION wire + T6 Capability v1.28 EXTENSION wire + T7 Tests + 3중 게이트 FINAL CLEAN + T8 atomic commit.

## 3. A92+A93+A94+A95+A96 결정 wire (5/5 ALL DONE)

| 결정 | 내용 | Status |
|------|------|--------|
| **A92** | 옵션 (a) Epic 16 진입 결정 | ✅ done 2026-08-22 |
| **A93** | Master PRD v3.3 → v3.4 atomic edit | ✅ done 2026-08-22 |
| **A94** | AD-30 Tenant IdP admin management 신규 (7 sub-decisions) | ✅ done 2026-08-22 |
| **A95** | Capability matrix v1.27 → v1.28 EXTENSION TENANT_IDP_MANAGEMENT 1 NEW row | ✅ done 2026-08-22 |
| **A96** | Epic 16 wire scope T1~T8 결정 | ✅ done 2026-08-22 |

## 4. 3중 게이트 FINAL CLEAN (cj-style 67번째 standard)

- (1) docs only 변경 (no code/test/sprint-status delta 외 PRD edit 신규)
- (2) capability matrix v1.27 → v1.28 EXTENSION 1 NEW row (industry-agnostic 4-industry grants)
- (3) commit_consistency gate PASS (CR 9-6 commit message discipline + A36 SDR 검증 4-step)
- (4) SDR drift gate PASS (MAX claim 4057 동일, no NEW test files introduced in PRD entry)
- (5) D-1-1-DEFER-* grep guard PASS (preserved, 60~67번째 검증)
- (6) sprint-status structure PASS (development_status + action_items block 정합)

## 5. CR lessons applied (cj-style 67번째 epic 연속 정직 회복)

- CR 0-2 RLS lesson ✅ APPLIED (tenant_idps RLS policy)
- CR 1-1 audit-first INSERT ✅ APPLIED (F19.3 audit-first INSERT 4 NEW)
- CR 9-6 commit message discipline ✅ APPLIED (`git commit -F <file>`, PowerShell here-string 회피)
- CR 11-3 honest-DEFER discipline ✅ APPLIED (67번째 epic 연속 정직 회복)
- CR 11-4 D-001~D-005 + P-015 lessons carry ✅ PRESERVED
- CR 12-1 L4 industry-agnostic capability ✅ APPLIED (capability matrix v1.28 EXTENSION)
- CR 12-5 D-14 typed exception envelope ✅ APPLIED (IdPMetadataError)
- CR 12-5 D-PARITY-01 inversion ✅ PRESERVED
- CR 12-5 D-GATE-01 inversion ✅ APPLIED (capability gate per-tenant on/off)
- A19 cohesion pattern 9 surface EXTENSION PASS ✅ (IdP admin surface NEW)
- A36 SDR 검증 4-step 자동 적용 ✅

## 6. Epic 1~15 + Phase 3 + Phase 4 + 1st release cycle 정합 보존

- ✅ Epic 15 close-out retro `729b223` (cj-style 58~61번째 모두 wire DONE)
- ✅ 1st release cycle (cj-style 62~66번째 모두 wire DONE — 1st release PRD entry `e48db06` 62번째 + spec entry 63번째 + atomic wire `be0cf97` 64번째 + review follow-up sprint 65번째 + close-out retro `25dccaf` 66번째)
- ✅ Phase 4 cycle (cj-style 53~57번째 모두 wire DONE — Phase 4 PRD entry `8e046df` + spec entry + atomic wire `71a033a` + close-out retro `934b35e`)
- ✅ Phase 3 cycle close-out 완료 (cj-style 49~52번째 모두 wire DONE)
- ✅ Epic 14 LISTEN/NOTIFY multi-process coordination `7835463` 보존
- ✅ Epic 13 LISTEN/NOTIFY consume `f2ea2f6` 보존
- ✅ Epic 12 2FA 게이트 `a63646c` 보존
- ✅ Epic 11 close-out retro 보존
- ✅ Phase 2 close-out baseline 599 passed 정합
- ✅ Epic 1 carry-over (auth) layout + onboarding/industry 보존
- ✅ Epic 7~10 ABC/TDABC + AI 인사이트 territory 결정 wire 보존

## 7. D-1-1-DEFER-* honestly ✅ RESOLVED (CR 11-3 67번째 검증)

- D-1-1-DEFER-1 Magic link ✅ RESOLVED
- D-1-1-DEFER-2 Social login OAuth (Google/Naver/Kakao) ✅ RESOLVED
- D-1-1-DEFER-3 SSO enterprise SAML ✅ RESOLVED

Epic 15 wire `5f9e37f` 진입 시점에 모두 정직 회복 결정 wire 완료 + Epic 16 PRD entry 진입 시점에 forward-reference `Configure tenant_idps (TODO Epic 16)` 자연스러운 carry-over chain 결정 wire 보존.

## 8. next 결정 wire 보류 (cj-style 68~71번째 진입점)

- 옵션 (a) Epic 16 bmad-create-story spec entry 진입 (cj-style 68번째) 결정 wire 보류
- 옵션 (b) Epic 16 bmad-dev-story atomic wire T1~T8 진입 (cj-style 69번째) 결정 wire 보류
- 옵션 (c) Epic 16 bmad-code-review follow-up sprint 진입 (cj-style 70번째) 결정 wire 보류
- 옵션 (d) Epic 16 close-out retro 진입 (cj-style 71번째) 결정 wire 보류

## 9. Cross-References

- master PRD v3.4 §F19 (Epic 16 territory)
- AD-30 Tenant IdP admin management
- capability matrix v1.28 (TENANT_IDP_MANAGEMENT row)
- Epic 15 SSO enterprise SAML forward-reference `docs/sso-enterprise.md` §4.1 step 3
- 1st release close-out retro `25dccaf` §12 (Next unblocked 결정 wire 보류)
- Related: [[handoff-2026-08-22-1st-release-close-out-done]] / [[handoff-2026-08-22-epic-15-close-out-done]] / [[handoff-2026-08-22-phase-4-deployment-wire-done]]
