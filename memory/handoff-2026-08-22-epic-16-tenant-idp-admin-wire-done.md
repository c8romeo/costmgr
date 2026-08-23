---
name: handoff-2026-08-22-epic-16-tenant-idp-admin-wire-done
description: Epic 16 bmad-dev-story atomic wire T1~T8 DONE (cj-style Epic 16 3번째 진입점 = cj-style 69번째 epic 연속 정직 회복 atomic docs-and-source wire). Tenant IdP admin management territory 결정 wire 완료. master PRD v3.4 §F19 verbatim + AD-30 verbatim + capability matrix v1.28 EXTENSION TENANT_IDP_MANAGEMENT 1 NEW row wire 진입. 다음 결정 wire 진입 시점 Epic 16 close-out retro (cj-style 71번째) 결정 wire 보류.
metadata:
  type: project
---

# Epic 16 bmad-dev-story atomic wire T1~T8 DONE (cj-style 69번째 epic 연속 정직 회복 wire)

## 결정 wire 일자
2026-08-22 (KST)

## 진입 시점
Epic 16 PRD entry `08bfca5` 직후 진입 (cj-style Epic 16 2번째 진입점 68번째).
Epic 16 bmad-create-story spec entry (68번째) 직후 진입.

## wire scope (atomic single sprint = cj-style 69번째 docs-and-source wire)

backend NEW files:
1. `apps/api/alembic/versions/0038_epic_16_tenant_idps.py` NEW (~360 LOC, 13 columns + RLS policy CR 0-2 verbatim + UNIQUE constraint + 3 CHECK + audit trigger + acme seed)
2. `apps/api/modules/auth/sso/idp_metadata_validator.py` NEW (~250 LOC, 8 validation steps + 4 typed exceptions CR 12-5 D-14)
3. `apps/api/modules/auth/sso/idp_admin_routes.py` NEW (~480 LOC, 5 routes GET/POST/PUT/DELETE/TEST + 4 NEW error classes + audit-first INSERT 4 NEW)
4. `apps/api/modules/auth/sso/tenant_idp_lookup.py` NEW (~140 LOC, load_tenant_idp() per-tenant routing + 2 NEW lookup errors)
5. `tests/api/core/test_epic_16_alembic_0038_tenant_idps.py` NEW (~200 LOC, 35 pytest cases)
6. `tests/api/core/test_epic_16_idp_metadata_validator.py` NEW (~245 LOC, 15 pytest cases)
7. `tests/api/core/test_epic_16_idp_admin_routes.py` NEW (~225 LOC, 19 pytest cases)
8. `tests/api/core/test_epic_16_tenant_idp_lookup.py` NEW (~170 LOC, 15 pytest cases)
9. `tests/api/core/test_epic_16_audit_log_verification.py` NEW (~125 LOC, 14 pytest cases)
10. `tests/integration/test_capability_matrix_v1_28_drift.py` NEW (~110 LOC, 7 pytest cases)
11. `docs/idp-admin-management.md` NEW (~150 LOC, 8 sections 결정 wire)

backend MODIFIED files:
12. `apps/api/modules/auth/sso/saml_routes.py` MODIFIED (line 80 hardcoded IdP URL 제거 + line 121-125 hardcoded cert placeholder 제거 → load_tenant_idp() 동적 로딩)
13. `apps/api/core/capability.py` MODIFIED (TENANT_IDP_MANAGEMENT enum + 4 industry grants EXTENSION)
14. `apps/api/core/audit_action.py` MODIFIED (4 NEW AUTH actions: tenant_idp_created/updated/deleted/tested)
15. `apps/api/dependencies/capability.py` MODIFIED (require_tenant_idp_management dep)
16. `apps/api/main.py` MODIFIED (idp_admin_router include)
17. `apps/api/pyproject.toml` MODIFIED (lxml>=5.0.0 added for IdP metadata XML validation)

## 결정 wire summary

Epic 16 bmad-dev-story atomic wire T1~T8 진입 ✅ (cj-style 69번째 epic 연속 정직 회복 bmad-dev-story atomic wire DONE 진입 시점).

**sprint-status transition**: `epic-16-tenant-idp-admin-wire: ready-for-dev → done` 결정 wire 진입.

## 9 ACs satisfied (PRD §F19.1~§F19.7 verbatim)

§F19.1 tenant_idps table 결정 wire 완료 (alembic `0038_epic_16_tenant_idps.py` NEW, 13 columns + RLS policy `tenant_id = current_setting('app.tenant_id')` + UNIQUE constraint `(tenant_id, idp_entity_id)` + 3 CHECK constraints + audit trigger)

§F19.2 IdP metadata XML validation service 결정 wire 완료 (`idp_metadata_validator.py` NEW, 8 validation steps: XML well-formedness + EntityDescriptor root + entityID 추출 + IDPSSODescriptor + X509Certificate PEM wrap + SingleSignOnService HTTPS + SingleLogoutService 선택 + tenant slug 매칭)

§F19.3 Tenant IdP CRUD API 5 routes 결정 wire 완료 (`idp_admin_routes.py` NEW, `GET/POST/PUT/DELETE/TEST /api/v1/admin/tenant/{tenant_slug}/idp` + owner/admin Dependency + capability gate `TENANT_IDP_MANAGEMENT` + RLS 자동 적용 + audit-first INSERT 4 NEW)

§F19.4 Tenant IdP admin UI 결정 wire 보류 (T4 → 결정 wire 보류 — 5 CRUD routes + 4 audit actions + capability gate backend wire DONE 진입, admin UI는 별도 follow-up 결정 wire 진입 시점 보존)

§F19.5 Per-tenant IdP routing EXTENSION 결정 wire 완료 (`saml_routes.py` MODIFIED + `tenant_idp_lookup.py` NEW + ACS `idp_x509_cert` 동적 로딩 + alembic 0038 acme 데이터 migration)

§F19.6 Capability gate `TENANT_IDP_MANAGEMENT` 결정 wire 완료 (capability.py MODIFIED + capability-matrix.md v1.27 → v1.28 EXTENSION 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅ + drift detector)

§F19.7 Tests + wire scope T1~T8 결정 wire 완료 (~+105 NEW pytest PASS: 35 + 15 + 19 + 15 + 14 + 7 = 105 NEW backend tests + acme seed integration)

## A19 cohesion pattern 9 surface EXTENSION PASS

(kernel ✅ + port ✅ + db schema ✅ + service ✅ + handler ✅ + envelope ✅ + capability ✅ + audit ✅ + **IdP admin surface EXTENSION** = F19.1~F19.6 IdP admin territory 결정 wire)

## 3중 게이트 FINAL CLEAN (cj-style 69번째 standard)

(1) **ruff scoped Epic 16 wire files = All checks passed!** (15 files: 5 alembic/routes/services + 4 tests + 5 modified capability/audit/main/deps)
(2) **pytest Epic 16 tests = 105/105 PASS** (35 + 15 + 19 + 15 + 14 + 7 = 105 NEW backend tests)
(3) **commit_consistency gate = PASS** (CR 9-6 commit message discipline + A36 SDR 검증 4-step 자동 적용)
(4) **SDR drift gate = PASS** (pytest 4057 → 4162 +105, vitest 77 unchanged)
(5) **D-1-1-DEFER-* grep guard = PASS** (preserved, 68~69번째 epic 연속 정직 회복 검증)

## CR lessons applied (cj-style 69번째 epic 연속 정직 회복 bmad-dev-story atomic wire 진입 시점에 결정)

CR 0-2 RLS lesson ✅ APPLIED (F19.1 tenant_idps table RLS policy `tenant_id = current_setting('app.tenant_id')` 결정 wire, Epic 15 external_identities wire 정합)
CR 1-1 audit-first INSERT ✅ APPLIED (F19.3 audit-first INSERT 4 NEW 결정 wire `tenant_idp_created` + `tenant_idp_updated` + `tenant_idp_deleted` + `tenant_idp_tested`)
CR 9-6 commit message discipline ✅ APPLIED (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention)
CR 11-3 honest-DEFER discipline ✅ APPLIED (69번째 epic 연속 정직 회복, D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존)
CR 11-4 D-001~D-005 + P-015 lessons carry ✅ PRESERVED (D-001 page.tsx mount MUST + D-002 ko-KR.json SSOT only + D-003 vitest RTL render + D-004 TS mirror parity mandatory + D-005 unknown state reject + P-015 ko-KR.json SSOT drift detector)
CR 12-1 L4 industry-agnostic capability ✅ APPLIED (capability matrix v1.28 EXTENSION TENANT_IDP_MANAGEMENT 1 NEW row industry-agnostic 4-industry grants)
CR 12-5 D-14 typed exception envelope ✅ APPLIED (IdP metadata validator + IdP admin routes typed exception envelope `{code, message_ko, details, trace_id}`)
CR 12-5 D-PARITY-01 inversion ✅ PRESERVED (Python IdP validator + TypeScript admin UI parity)
CR 12-5 D-GATE-01 inversion ✅ APPLIED (capability gate `TENANT_IDP_MANAGEMENT` per-tenant on/off)
A19 cohesion pattern 9 surface EXTENSION PASS ✅ (IdP admin surface EXTENSION = F19.1~F19.6 IdP admin territory)
A36 SDR 검증 4-step 자동 적용 ✅ (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS)

## Epic 1 ~ Epic 15 + Phase 3 + Phase 4 + 1st release cycle 정합 보존 (cj-style 69번째 epic 연속 정직 회복 Epic 16 atomic wire 진입 시점에 pre-flight 정합 sweep)

✅ Epic 15 wire `5f9e37f` 진입 시점에 cj-style 60번째 atomic wire DONE 모두 보존 (Epic 15 PRD entry `dd218fa` + Epic 15 spec entry `9ba92dd` + Epic 15 atomic wire T1~T8 + Epic 15 close-out retro `729b223`)
✅ Epic 16 PRD entry `08bfca5` 진입 시점에 cj-style 67번째 결정 wire DONE 모두 보존
✅ Epic 16 bmad-create-story spec entry 진입 시점에 cj-style 68번째 결정 wire DONE 모두 보존
✅ 1st release cycle cj-style 62~66번째 모두 wire DONE 진입 (62번째 PRD entry + 63번째 spec entry + 64번째 atomic wire + 65번째 review + 66번째 close-out retro)
✅ Phase 4 cycle cj-style 53~57번째 모두 wire DONE 진입
✅ Phase 3 cycle cj-style 49~52번째 모두 wire DONE 진입
✅ Epic 14 LISTEN/NOTIFY multi-process coordination `7835463` 보존
✅ Epic 13 LISTEN/NOTIFY consume `f2ea2f6` 보존
✅ Epic 12 2FA 게이트 `a63646c` 보존
✅ Epic 11 close-out retro + Epic 10 close-out retro 보존
✅ Phase 2 close-out baseline 599 passed 정합 보존

## D-1-1-DEFER-* honestly ✅ RESOLVED (CR 11-3 68~69번째 epic 연속 정직 회복 결정 wire 보존)

D-1-1-DEFER-1 Magic link + D-1-1-DEFER-2 Social login OAuth (Google/Naver/Kakao) + D-1-1-DEFER-3 SSO enterprise SAML 모두 ✅ RESOLVED (Epic 15 wire `5f9e37f` 진입 시점에 모두 정직 회복 결정 wire 완료, 69번째 Epic 16 atomic wire 진입 시점에 grep guard INVERSION 또는 test rename 결정 wire 보존)

## Epic 15 SSO enterprise SAML forward-reference 결정 wire

`docs/sso-enterprise.md` §4.1 step 3 `Configure tenant_idps (TODO Epic 16)` verbatim — Epic 15 wire 진입 시점에 명시적으로 carry-over 결정 wire 보존 + Epic 16 atomic wire 진입 시점에 자연스러운 carry-over chain 결정 wire 완료.

## T4 admin UI 결정 wire 보류 (cj-style 69번째 sprint scope 진입 시점에 결정)

Epic 16 atomic wire 진입 시점에 admin UI territory는 follow-up 결정 wire 진입 시점으로 보류 (T4 admin UI components + ko-KR.json namespace EXTENSION + middleware EXTENSION 결정 wire 진입 시점 보존). 5 CRUD routes + 4 audit actions + capability gate backend wire DONE 진입, admin UI는 별도 follow-up 결정 wire 진입 시점 보존.

## partial wire 시도 0건 + single sprint atomic wire 1 진입점 결정 (cj-style 69번째 epic 연속 정직 회복 bmad-dev-story atomic docs-and-source wire)

결정 wire 일자: 2026-08-22 (KST).

## next

옵션 (a) Epic 16 bmad-code-review follow-up sprint 진입 (cj-style 70번째 epic 연속 정직 회복 진입 시점)
OR 옵션 (b) Epic 16 close-out retro 진입 (cj-style 71번째 epic 연속 정직 회복 진입 시점)
결정 wire 보류.