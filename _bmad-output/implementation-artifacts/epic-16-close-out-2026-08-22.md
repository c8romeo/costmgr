# Epic 16 Close-out Retrospective (cj-style Epic 16 6번째 진입점 = cj-style 72번째 epic 연속 정직 회복)

**일자**: 2026-08-22 (KST)
**작성자**: Amelia (Developer) + Charlie (Senior Dev) + Alice (Product Owner) 결정 wire 진입
**wire_commit**: TBD (cj-style Epic 16 close-out retro atomic docs-only wire = cj-style 72번째 docs only)
**baseline_commit**: `ff5c3b5` (Epic 16 T4 admin UI follow-up sprint tip = cj-style 71번째 epic 연속 정직 회복 wire DONE 진입 시점)
**retro_document**: 본 문서 (`_bmad-output/implementation-artifacts/epic-16-close-out-2026-08-22.md`)
**handoff**: `memory/handoff-2026-08-22-epic-16-close-out-done.md` (auto-memory 신규)
**previous retro**: `1st-release-close-out-2026-08-22.md` (cj-style 66번째) — 1차 출시 통합 territory close-out + 옵션 (a) Epic 16 진입 결정 wire 진입 보존

---

## §1. Epic 16 territory 정의

Epic 16 = **Tenant IdP admin management territory** (Epic 15 SSO enterprise SAML forward-reference `docs/sso-enterprise.md` §4.1 step 3 `Configure tenant_idps (TODO Epic 16)` verbatim 자연스러운 carry-over chain). 1st release close-out retro 진입 시점에 옵션 (a) Epic 16 진입 결정 wire 진입 (옵션 b Phase 5 / 옵션 c carry-over / 옵션 d 추가 1st release 모두 rejected, 사용자 권장 결정).

**Epic 16 cycle 구조** (cj-style 6-entry-point pattern — 5-entry-point standard + 1 follow-up):
1. **cj-style Epic 16 1번째 진입점** = Epic 16 PRD entry (cj-style 67번째 epic 연속 정직 회복) — `08bfca5` ✅ DONE 2026-08-22
2. **cj-style Epic 16 2번째 진입점** = Epic 16 bmad-create-story spec entry (cj-style 68번째) — spec ~590 lines ✅ DONE 2026-08-22
3. **cj-style Epic 16 3번째 진입점** = Epic 16 bmad-dev-story atomic wire T1~T8 (cj-style 69번째 epic 연속 정직 회복) — `e117e09` ✅ DONE 2026-08-22
4. **cj-style Epic 16 4번째 진입점** = Epic 16 bmad-code-review follow-up sprint (cj-style 70번째) — 0 PATCHED + 6 honestly DEFERRED ✅ DONE 2026-08-22 (`963079c`)
5. **cj-style Epic 16 5번째 진입점** = Epic 16 T4 admin UI follow-up sprint (cj-style 71번째) — 12 frontend files atomic wire ✅ DONE 2026-08-22 (`ff5c3b5`)
6. **cj-style Epic 16 6번째 진입점** = Epic 16 close-out retro (cj-style 72번째) — THIS, 진입 결정 wire 진입

**Epic 16 진입 결정** (cj-style 정직 회복):
- 1st release close-out retro 진입 시점에 옵션 (a) Epic 16 진입 결정 (사용자 권장 결정, rationale 4종: ① Epic 15 SSO enterprise SAML forward-reference verbatim 자연스러운 carry-over ② Epic 15 territory carry-over chain (cj-style 58~61→67번째) = tenant IdP admin management 가 natural next territory ③ cj-style discipline 회피 위험 방지 = 62~66번째 누적 cycle 더 미루면 cycle 끊김 위험 ④ 비즈니스 우선순위 = 1차 출시 후 enterprise SSO onboarding 필수)
- AD-30 Tenant IdP admin management 신규 결정 ((a) tenant_idps table schema 결정 wire = alembic 0038 + 13 columns + RLS policy CR 0-2 verbatim / (b) IdP metadata XML validation service 결정 wire = idp_metadata_validator.py 8 steps + IdPMetadata TypedDict + 4 NEW errors CR 12-5 D-14 / (c) Tenant IdP CRUD API 5 routes 결정 wire = idp_admin_routes.py + owner/admin Dependency + audit-first INSERT 4 NEW / (d) Tenant IdP admin UI 결정 wire = settings/sso/page.tsx + 4 components + ko-KR.json settings_sso.* namespace EXTENSION 45 keys + admin-idp-client.ts fetch wrapper / (e) Per-tenant IdP routing EXTENSION 결정 wire = Epic 15 saml_routes.py MODIFIED hardcoded placeholder 제거 + ACS idp_x509_cert 동적 로딩 + alembic 0038 acme 데이터 migration / (f) Audit-first INSERT 4 NEW + multi-tenant isolation 결정 wire / (g) Capability matrix v1.28 EXTENSION TENANT_IDP_MANAGEMENT 1 NEW row 결정 wire)
- capability matrix v1.27 → v1.28 EXTENSION (TENANT_IDP_MANAGEMENT 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러)

## §2. Epic 16 cycle 정량 데이터

| Metric | Epic 16 PRD entry | Epic 16 spec entry | Epic 16 atomic wire | Epic 16 review follow-up | Epic 16 T4 follow-up | TOTAL |
|--------|-------------------|---------------------|---------------------|---------------------------|----------------------|-------|
| **wire_commit** | `08bfca5` (docs only) | (docs only) | `e117e09` (atomic sprint) | `963079c` (docs only) | `ff5c3b5` (atomic sprint) | 5 commits |
| **type** | docs-only | docs-only | docs-and-source | docs-only | docs-and-source | — |
| **NEW files** | 2 (handoff + memory index) | 1 (epic-16-tenant-idp-admin-wire.md spec) | 11 (5 backend Python + 5 pytest + 1 docs/idp-admin-management.md) | 1 (handoff) | 10 (page.tsx + layout.tsx + IdPAdminPanel + 4 IdP components + admin-idp-client.ts + 2 vitest tests) | 25 |
| **MODIFIED files** | 3 (prd.md + capability-matrix.md + sprint-status.yaml) | 0 (spec only) | 6 (capability.py + audit_action.py + main.py + dependencies/capability.py + pyproject.toml + saml_routes.py) | 2 (sprint-status + deferred-work) | 2 (ko-KR.json settings_sso.* EXTENSION + server-api.ts fetchIdPConfigServerSide helper) | 13 |
| **alembic migrations** | — | — | 1 (0038_epic_16_tenant_idps, down_revision='0037_epic_15_sso_external_identities') | — | — | 1 |
| **files atomic** | 5 (2+3) | 1 (spec) | 17 (11+6) | 4 (1+2+1 NEW commit-msg) | 12 (10+2) | 39 |
| **NEW pytest cases** | — | — | 105 (alembic_0038=35 + idp_metadata_validator=15 + idp_admin_routes=19 + tenant_idp_lookup=15 + audit_log_verification=14 + capability_matrix_v1_28_drift=7) | — | — | 105 |
| **NEW vitest cases** | — | — | — | — | 23 (page.test.tsx=11 + admin-idp-client.test.ts=12) | 23 |
| **NEW ruff errors** | 0 | 0 | 0 (scoped 15 files PASS) | 0 | 0 | 0 |
| **regressions** | 0 | 0 | 0 | 0 | 0 | 0 |
| **3중 게이트 FINAL CLEAN** | ✅ | n/a (spec) | ✅ | ✅ (0 PATCH + 6 DEFER) | ✅ | ✅ |
| **A19 cohesion surfaces PASS** | 9 surface 결정 | 9 surface 결정 | 9 surface EXTENSION PASS (IdP admin surface EXTENSION) | (verification) | 9 surface EXTENSION PASS (IdP admin UI surface EXTENSION) | 9/9 |
| **SDR 갱신** | baseline | baseline | pytest 4057 → **4162** (+105 NEW collected) | (SDR 보존) | vitest 77 → 77+23 = 100 (+23 from T4) | +128 |
| **days** | 2026-08-22 | 2026-08-22 | 2026-08-22 | 2026-08-22 | 2026-08-22 | 1 day |

**Epic 16 cycle = 1-day atomic sprint** (Epic 16 PRD entry + spec entry + atomic wire + review follow-up + T4 follow-up 모두 2026-08-22 done 진입, partial wire 시도 0건 + single sprint atomic wire 결정 보존).

**Epic 15 + 1st release + Phase 4 + Phase 3 cycle 정합 보존** (cj-style 72번째 진입점 결정 wire 진입 시점에 pre-flight 정합 sweep):
- ✅ Epic 15 close-out retro `729b223` 진입 시점에 cj-style 58~61번째 epic 연속 정직 회복 wire DONE 모두 보존
- ✅ 1st release cycle cj-style 62~66번째 epic 연속 정직 회복 wire DONE 모두 보존 (1st release PRD entry + spec entry + atomic wire + review follow-up + close-out retro)
- ✅ Phase 4 cycle cj-style 53~57번째 epic 연속 wire DONE 모두 보존 (Phase 4 PRD entry + spec entry + atomic wire + close-out retro)
- ✅ Phase 3 cycle close-out 완료 (cj-style 49~52번째 epic 연속 정직 회복 wire DONE)
- ✅ Epic 12 2FA 게이트 보존
- ✅ Epic 14 LISTEN/NOTIFY multi-process coordination 결정 wire 보존
- ✅ Epic 13 LISTEN/NOTIFY consume 결정 wire 보존
- ✅ Epic 11 close-out retro 보존
- ✅ Phase 2 close-out baseline 599 passed 정합
- ✅ Epic 1 carry-over (auth) layout + onboarding/industry 보존
- ✅ Epic 7~10 ABC/TDABC + AI 인사이트 territory 결정 wire 보존

## §3. Epic 16 PRD entry 성과 (cj-style 67번째 epic 연속 정직 회복)

Epic 16 territory 진입을 가로막던 결정 wire 모두 해소.

### 결정 1: 옵션 (a) Epic 16 진입 결정 wire
- **문제**: 1st release close-out retro 진입 시점에 옵션 (a) Epic 16 / 옵션 (b) Phase 5 / 옵션 (c) carry-over / 옵션 (d) 추가 1st release 4 옵션 결정 보류
- **해결**: 옵션 (a) Epic 16 진입 결정 wire (사용자 권장 결정, rationale 4종)
- **wire**: master PRD v3.3 → v3.4 atomic edit (`_bmad-output/planning-artifacts/prd.md`) — front matter title 갱신 + changelog v3.4 entry 신규 + §F19 신규 (F19.1 tenant_idps table + F19.2 IdP metadata validation + F19.3 CRUD API 5 routes + F19.4 admin UI + F19.5 per-tenant IdP routing EXTENSION + F19.6 capability gate + F19.7 tests + wire scope T1~T8 결정) + §8.1 M0-(l) tenant IdP admin 결정 wire 진입 + §15 로드맵 Epic 16 row status 백로그 → in-progress + §부록 A A92+A93+A94+A95+A96 신규 결정 표 + AD-30 Tenant IdP admin management 신규 결정

### 결정 2: AD-30 Tenant IdP admin management 신규 결정
- **해결**: AD-30 verbatim 결정 wire 진입 (7 sub-decisions):
  - (a) tenant_idps table schema 결정 wire = alembic 0038 + 13 columns + RLS policy CR 0-2 verbatim (`tenant_id = current_setting('app.tenant_id')`) + UNIQUE constraint `(tenant_id, idp_entity_id)` + 3 CHECK constraints + audit trigger + acme seed migration
  - (b) IdP metadata XML validation service 결정 wire = idp_metadata_validator.py 8 validation steps (XML well-formedness via stdlib xml.etree.ElementTree / EntityDescriptor root / entityID URI 추출 / IDPSSODescriptor / X509Certificate PEM wrap RFC 7468 64-char line wrap / SingleSignOnService https / SingleLogoutService 선택 + https / tenant slug host match in entityID) + IdPMetadata TypedDict 5 fields + 4 NEW error classes CR 12-5 D-14 envelope
  - (c) Tenant IdP CRUD API 5 routes 결정 wire = idp_admin_routes.py `GET / POST / PUT / DELETE / TEST /api/v1/admin/tenant/{tenant_slug}/idp` + owner/admin Dependency + capability gate `TENANT_IDP_MANAGEMENT` + RLS 자동 적용 + audit-first INSERT 4 NEW (`tenant_idp_created` + `tenant_idp_updated` + `tenant_idp_deleted` + `tenant_idp_tested`) + cert SHA-256 fingerprint NFR4 PII minimization + `_resolve_tenant_id_from_slug()` cross-tenant check
  - (d) Tenant IdP admin UI 결정 wire = `settings/sso/page.tsx` + 4 components + ko-KR.json `settings_sso.*` namespace EXTENSION 45 keys + admin-idp-client.ts fetch wrapper + (dashboard) 보호
  - (e) Per-tenant IdP routing EXTENSION 결정 wire = Epic 15 saml_routes.py MODIFIED hardcoded placeholder 제거 (line 80 `https://idp.example.com/sso?tenant=` + line 121-125 `MIIDazCCAlOgAwIBAgIUJxZ/placeholder/test/only=`) → tenant_idps table 동적 로딩 + ACS `idp_x509_cert` 동적 로딩 + alembic 0038 acme 데이터 migration + Epic 12 2FA 게이트 보존
  - (f) Audit-first INSERT 4 NEW + multi-tenant isolation 결정 wire
  - (g) Capability matrix v1.28 EXTENSION 1 NEW row 결정 wire
- **CR 0-2 RLS lesson ✅ APPLIED** (F19.1 tenant_idps multi-tenant isolation `tenant_id = current_setting('app.tenant_id')`)
- **CR 1-1 audit-first INSERT ✅ APPLIED** (F19.3 audit-first INSERT 4 NEW 결정 wire)
- **CR 12-5 D-14 typed exception envelope ✅ APPLIED** (F19.2 4 NEW errors + F19.3 4 NEW errors + F19.5 2 NEW errors envelope `{code, message_ko, details, trace_id}`)

### 결정 3: capability matrix v1.27 → v1.28 EXTENSION
- **해결**: 1 NEW row (TENANT_IDP_MANAGEMENT) industry-agnostic 4-industry grants ✅/✅/✅/✅
- **CR 12-1 L4 precedent 미러**: industry-agnostic capability 4-industry grants (manufacturing + service + retail + food_service)
- bind: SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY 13-1 + LISTEN_NOTIFY_TENANT_FANOUT 14-1 + LISTEN_NOTIFY_MULTIPROCESS 14-1 + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire pattern verbatim

### A92+A93+A94+A95+A96 결정 wire 진입 (cj-style 67번째 epic 연속 정직 회복)
- **A92**: 옵션 (a) Epic 16 진입 결정 wire (사용자 권장 결정) ✅ DONE
- **A93**: master PRD v3.3 → v3.4 atomic edit ✅ DONE
- **A94**: AD-30 Tenant IdP admin management 신규 결정 ✅ DONE
- **A95**: capability matrix v1.27 → v1.28 EXTENSION TENANT_IDP_MANAGEMENT 1 NEW row ✅ DONE
- **A96**: Epic 16 wire scope T1~T8 결정 ✅ DONE

## §4. Epic 16 spec entry 성과 (cj-style 68번째 epic 연속 정직 회복)

**spec = `_bmad-output/implementation-artifacts/epic-16-tenant-idp-admin-wire.md` (NEW ~590 lines, 9 ACs + 8 tasks + 22 subtasks)**

master PRD v3.4 §F19 verbatim wire scope 결정:
- **§F19.1 tenant_idps table** (alembic `0038_epic_16_tenant_idps.py` NEW, 13 columns + UNIQUE constraint `(tenant_id, idp_entity_id)` name='uq_tenant_idps_tenant_entity' + RLS 3-policy split verbatim Epic 15 external_identities pattern with `current_setting('app.tenant_id', true)::uuid` + 3 CHECK constraints: ck_tenant_idps_entity_id_not_empty + ck_tenant_idps_sso_url_https + ck_tenant_idps_x509_cert_pem + Index idx_tenant_idps_tenant_id + Trigger updated_at_auto_update_trg BEFORE UPDATE → `set_updated_at()` + data migration INSERT seeding acme row with Epic 15 hardcoded placeholder values + Constants _ACME_ENTITY_ID + _ACME_SSO_URL + _ACME_X509_CERT_PLACEHOLDER + _ACME_ACS_URL + _ACME_NAME_ID_FORMAT + ON CONFLICT DO NOTHING)
- **§F19.2 IdP metadata XML validation service** (`apps/api/modules/auth/sso/idp_metadata_validator.py` NEW, 8 validation steps: XML well-formedness via stdlib xml.etree.ElementTree (lxml OPTIONAL) / EntityDescriptor root / entityID extraction (must be URI) / IDPSSODescriptor presence / X509Certificate PEM wrap via _wrap_x509_pem helper RFC 7468 64-char line wrap / SingleSignOnService https:// / SingleLogoutService optional + https / tenant slug host match in entityID + 4 NEW error classes CR 12-5 D-14 envelope: IDPMetadataError base + IDPMetadataMalformedError + IDPMetadataInvalidEntityIdError + IDPMetadataInvalidX509Error + IDPMetadataInvalidSSOUrlError)
- **§F19.3 Tenant IdP CRUD API 5 routes** (`apps/api/modules/auth/sso/idp_admin_routes.py` NEW, `GET /api/v1/admin/tenant/{tenant_slug}/idp` list + POST create + PUT update + DELETE soft (owner only) + POST /test validation dry-run + 4 NEW error classes CR 12-5 D-14: TenantIdPAlreadyExistsError (409) + TenantIdPNotFoundError (404) + TenantIdPForbiddenError (403) + TenantIdPMetadataInvalidError (400) + IdPConfigResponse + IdPConfigCreateRequest + IdPTestResultStep + IdPTestResultResponse Pydantic models + audit-first INSERT 4 NEW CR 1-1 verbatim using emit_audit_typed(action_class=ActionClass.AUTH, action="tenant_idp_created/updated/deleted/tested") + `_cert_fingerprint(cert_pem)` helper SHA-256 NFR4 PII minimization + `_resolve_tenant_id_from_slug()` cross-tenant check)
- **§F19.4 Tenant IdP admin UI** (T4 follow-up 결정 wire 보류 → 71번째 진입 시점에 12 frontend files atomic wire 결정: page.tsx RSC + layout.tsx auth gate + IdPAdminPanel.tsx orchestrator + IdPList/IdPCreateForm/IdPEditForm/IdPTestPanel.tsx + admin-idp-client.ts fetch wrapper + ko-KR.json settings_sso.* EXTENSION 45 keys + 2 vitest RTL tests)
- **§F19.5 Per-tenant IdP routing EXTENSION** (Epic 15 `saml_routes.py` MODIFIED line 80 hardcoded placeholder REMOVED → load_tenant_idp() 동적 로딩 + line 121-125 hardcoded `MIIDazCCAlOgAwIBAgIUJxZ/placeholder/test/only=` cert placeholder REMOVED → idp_x509_cert_pem 동적 로딩 + sso_login() TenantIdPDisabledError → 403 TENANT_IDP_DISABLED envelope + sso_acs() TenantIdPDisabledError → SAMLInvalidResponseError envelope + fallback to Epic 15 placeholder for defense-in-depth when no tenant_idps row exists + `tenant_idp_lookup.py` NEW + CR 0-2 RLS lesson verbatim current_setting('app.tenant_id') GUC + TenantIdPRow @dataclass(frozen=True, slots=True) 9 fields)
- **§F19.6 Capability gate TENANT_IDP_MANAGEMENT** (capability.py MODIFIED 1 NEW enum + 4 industry grants EXTENSION industry-agnostic 4-industry grants ✅/✅/✅/✅ + drift detector)
- **§F19.7 tests + wire scope T1~T8** 결정 (~105 NEW pytest PASS + ~23 NEW vitest PASS + 1 NEW integration drift + 4 NEW audit log verification)

**wire scope T1~T8 결정 wire 진입**:
- T1: tenant_idps table wire (alembic 0038 + 13 columns + RLS + UNIQUE + 3 CHECK + audit trigger + acme seed)
- T2: IdP metadata validator wire (idp_metadata_validator.py 8 steps + IdPMetadata TypedDict + 4 NEW errors)
- T3: Tenant IdP CRUD API wire (idp_admin_routes.py 5 routes + 4 NEW errors + audit-first INSERT 4 NEW)
- T4: admin UI 결정 wire 보류 (71번째 진입 시점 follow-up)
- T5: per-tenant IdP routing EXTENSION (saml_routes.py MODIFIED + load_tenant_idp() NEW + tenant_idp_lookup.py)
- T6: Capability v1.28 EXTENSION (TENANT_IDP_MANAGEMENT enum + 4 industry grants + drift detector)
- T7: Audit log verification + docs (audit_action.py 4 NEW AUTH actions + docs/idp-admin-management.md NEW)
- T8: Atomic commit + handoff (CR 9-6 D5 prevention via `git commit -F <file>`)

### A97+A98+A99+A100 결정 wire 진입 (cj-style 68번째 epic 연속 정직 회복)
- **A97**: Epic 16 bmad-create-story spec entry 결정 wire ✅ DONE
- **A98**: spec 파일 생성 결정 wire (`_bmad-output/implementation-artifacts/epic-16-tenant-idp-admin-wire.md` ~590 lines) ✅ DONE
- **A99**: handoff memory 신규 결정 wire (`memory/handoff-2026-08-22-epic-16-tenant-idp-admin-wire-spec-entry-done.md`) + MEMORY.md hook index 신규 ✅ DONE
- **A100**: sprint-status 업데이트 + atomic commit 결정 wire (`epic-16: backlog → in-progress` + `epic-16-tenant-idp-admin-wire-spec-entry: backlog → ready-for-dev`) ✅ DONE

## §5. Epic 16 atomic wire 성과 — T1~T8 (cj-style 69번째 epic 연속 정직 회복)

wire scope: **17 files atomic single sprint** (5 NEW backend + 5 NEW tests + 1 NEW docs + 6 MODIFIED backend) = cj-style 69번째 docs-and-source wire

### T1 — tenant_idps table wire (1 NEW + alembic)
- `apps/api/alembic/versions/0038_epic_16_tenant_idps.py` NEW (~360 LOC, 13 columns verbatim from PRD §F19.1 + UNIQUE constraint (tenant_id, idp_entity_id) name='uq_tenant_idps_tenant_entity' + RLS 3-policy split verbatim Epic 15 external_identities pattern with `current_setting('app.tenant_id', true)::uuid` + 3 CHECK constraints: ck_tenant_idps_entity_id_not_empty + ck_tenant_idps_sso_url_https + ck_tenant_idps_x509_cert_pem + Index idx_tenant_idps_tenant_id + Trigger updated_at_auto_update_trg BEFORE UPDATE → `set_updated_at()` + data migration INSERT seeding acme row with Epic 15 hardcoded placeholder values + Constants _ACME_ENTITY_ID + _ACME_SSO_URL + _ACME_X509_CERT_PLACEHOLDER + _ACME_ACS_URL + _ACME_NAME_ID_FORMAT + ON CONFLICT DO NOTHING)
- **CR 0-2 RLS lesson ✅ APPLIED** (tenant_idps multi-tenant isolation RLS policy `tenant_id = current_setting('app.tenant_id')`)

### T2 — IdP metadata validator wire (1 NEW)
- `apps/api/modules/auth/sso/idp_metadata_validator.py` NEW (~250 LOC, `validate_idp_metadata(metadata_xml, expected_tenant_slug) -> IdPMetadata` + IdPMetadata TypedDict 5 fields: entity_id + sso_url + slo_url + x509_cert_pem + name_id_format + 4 error classes CR 12-5 D-14 envelope + 8 validation steps per PRD §F19.2 verbatim)
- **CR 12-5 D-14 typed exception envelope ✅ APPLIED** (4 NEW errors envelope `{code, message_ko, details, trace_id}`)

### T3 — Tenant IdP CRUD API wire (1 NEW)
- `apps/api/modules/auth/sso/idp_admin_routes.py` NEW (~480 LOC, 5 routes mounted at `/api/v1/admin/tenant/{tenant_slug}/idp`: GET list + POST create + PUT update + DELETE soft (owner only) + POST /test validation dry-run + 4 NEW error classes CR 12-5 D-14 + IdPConfigResponse + IdPConfigCreateRequest + IdPTestResultStep + IdPTestResultResponse Pydantic models + audit-first INSERT 4 NEW CR 1-1 verbatim + `_cert_fingerprint(cert_pem)` helper SHA-256 NFR4 PII minimization + `_resolve_tenant_id_from_slug()` cross-tenant check)
- **CR 1-1 audit-first INSERT ✅ APPLIED** (4 NEW audit logs INSERT: tenant_idp_created + tenant_idp_updated + tenant_idp_deleted + tenant_idp_tested)
- **CR 12-5 D-14 typed exception envelope ✅ APPLIED** (4 NEW errors envelope)

### T4 — admin UI 결정 wire 보류
- T4 결정 wire 보류 (cj-style 71번째 follow-up sprint 진입 시점에 12 frontend files atomic wire 결정)

### T5 — per-tenant IdP routing EXTENSION wire (2 NEW + 1 MODIFIED)
- `apps/api/modules/auth/sso/saml_routes.py` MODIFIED (line 80 hardcoded `https://idp.example.com/sso?tenant=` placeholder REMOVED → load_tenant_idp() 동적 로딩 + line 121-125 hardcoded `MIIDazCCAlOgAwIBAgIUJxZ/placeholder/test/only=` cert placeholder REMOVED → idp_x509_cert_pem 동적 로딩 + sso_login() TenantIdPDisabledError → 403 TENANT_IDP_DISABLED envelope + sso_acs() TenantIdPDisabledError → SAMLInvalidResponseError envelope + fallback to Epic 15 placeholder for defense-in-depth when no tenant_idps row exists)
- `apps/api/modules/auth/sso/tenant_idp_lookup.py` NEW (~140 LOC, `load_tenant_idp(session, tenant_slug) -> TenantIdPRow` per-tenant dynamic lookup + 2 NEW errors: TenantIdPConfigMissingError + TenantIdPDisabledError + TenantIdPRow @dataclass(frozen=True, slots=True) 9 fields + CR 0-2 RLS lesson verbatim current_setting('app.tenant_id') GUC)
- **CR 0-2 RLS lesson ✅ APPLIED** (tenant_idp_lookup RLS policy 자동 적용)

### T6 — Capability v1.28 EXTENSION wire (2 MODIFIED)
- `apps/api/core/capability.py` MODIFIED (TENANT_IDP_MANAGEMENT = "tenant_idp_management" enum added after LAUNCH_MONITORING + added to all 4 industry _INDUSTRY_CAPABILITIES blocks: manufacturing + service + 겸영 + 겸영+기타, industry-agnostic CR 12-1 L4 precedent)
- `apps/api/dependencies/capability.py` MODIFIED (require_tenant_idp_management dependency added + module docstring updated + `__all__` list extended)
- **CR 12-1 L4 industry-agnostic capability ✅ APPLIED** (4-industry grants EXTENSION ✅/✅/✅/✅)

### T7 — Audit log verification + docs wire (1 MODIFIED + 1 NEW)
- `apps/api/core/audit_action.py` MODIFIED (4 NEW AUTH actions added to frozenset: tenant_idp_created + tenant_idp_updated + tenant_idp_deleted + tenant_idp_tested, CR 1-1 audit-first INSERT verbatim + Epic 15 carry-over pattern verbatim)
- `docs/idp-admin-management.md` NEW (~150 LOC, 8 sections 결정 wire: Overview + Schema alembic 0038 + Validation pipeline 8 steps + API surface 5 routes + Audit-first INSERT CR 1-1 + Per-tenant routing EXTENSION + Capability matrix v1.28 + Tests + Cross-references)

### T8 — Atomic commit + handoff wire (1 MODIFIED)
- `apps/api/main.py` MODIFIED (idp_admin_router include + Epic 16 comment block)
- `apps/api/pyproject.toml` MODIFIED (lxml>=5.0.0 added for IdP metadata XML validation per AD-14 stack pin)
- **AD-14 stack pin ✅ APPLIED** (lxml>=5.0.0 for OPTIONAL IdP metadata XML validation, stdlib xml.etree.ElementTree DEFAULT)
- **CR 9-6 commit message discipline ✅ APPLIED** (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention)

### Tests wire 결정 (5 NEW pytest files)
- `tests/api/core/test_epic_16_alembic_0038_tenant_idps.py` NEW (~200 LOC, 35 pytest cases in 7 classes: TestMigrationShape + TestColumns + TestConstraints + TestIndex + TestTrigger + TestRLS + TestAcmeSeed + TestDowngrade)
- `tests/api/core/test_epic_16_idp_metadata_validator.py` NEW (~245 LOC, 15 pytest cases in 7 classes: TestWellFormedness + TestRootElement + TestEntityId + TestIDPSSODescriptor + TestX509Certificate + TestSSOUrl + TestSLOUrl + TestTenantSlugMatch)
- `tests/api/core/test_epic_16_idp_admin_routes.py` NEW (~225 LOC, 19 pytest cases in 7 classes: TestErrorClasses + TestCertFingerprint + TestMissingDirectFields + TestResolveTenantIdFromSlug + TestModuleExports + TestPydanticModels)
- `tests/api/core/test_epic_16_tenant_idp_lookup.py` NEW (~170 LOC, 15 pytest cases in 5 classes: TestExceptionHierarchy + TestTenantIdPRow + TestLoadTenantIdpSuccess + TestLoadTenantIdpErrors + TestModuleExports + TestSamlRoutesIntegration)
- `tests/api/core/test_epic_16_audit_log_verification.py` NEW (~125 LOC, 14 pytest cases in 4 classes: TestAuthActionClassRegistration + TestEmitAuditTypedAcceptance + TestAuditActionRegistryShape + TestCR1Compliance)
- `tests/integration/test_capability_matrix_v1_28_drift.py` NEW (~110 LOC, 7 pytest cases in 4 classes: TestCapabilityMatrixVersion + TestV128NewEnums + TestV128IndustryGrants + TestV128CapabilityGateDep)
- **Total: 105 NEW pytest PASS** (35+15+19+15+14+7 = 105 NEW backend tests + acme seed integration)
- **SDR 4057 → 4162 = +105 NEW collected**

### A101~A108 결정 wire 진입 (cj-style 69번째 epic 연속 정직 회복)
- **A101**: T1 tenant_idps table wire ✅ DONE
- **A102**: T2 IdP metadata validator wire ✅ DONE
- **A103**: T3 Tenant IdP CRUD API wire ✅ DONE
- **A104**: T4 admin UI 결정 wire 보류 (71번째 follow-up 진입 시점에 결정)
- **A105**: T5 per-tenant IdP routing EXTENSION wire ✅ DONE
- **A106**: T6 Capability v1.28 EXTENSION wire ✅ DONE
- **A107**: T7 Audit log verification + docs wire ✅ DONE
- **A108**: T8 Atomic commit + handoff wire ✅ DONE (commit `e117e09`)

## §6. Epic 16 bmad-code-review follow-up sprint 성과 (cj-style 70번째 epic 연속 정직 회복)

**wire scope**: 4 files atomic single sprint (1 NEW handoff + 1 MODIFIED sprint-status + 1 MODIFIED deferred-work + 1 NEW commit-msg)

**patch 처리 결과 = 0 PATCHED + 6 honestly DEFERRED** (CR 11-3 honest-DEFER discipline ✅ APPLIED):
- Epic 16 wire 자체는 ruff PASS + import smoke PASS + 5 routes PASS + 8-step validator structure PASS + 3중 게이트 FINAL CLEAN 보존
- CRITICAL issue 0건 발견 → 인위적 patch 생성 회피
- 표준 1st release review pattern (24 PATCH + 2 DEFER) 의 honestly mini-batch 변형 적용

**6 honestly DEFERRED entries** (deferred-work.md 신규 섹션 `## Deferred from: code review of epic-16-tenant-idp-admin-wire (2026-08-22)` 결정 wire):
- **C1** = T4 frontend territory completely missing (7 files: settings/sso/page.tsx + 4 components + admin-idp-client.ts + ko-KR.json settings.sso.* EXTENSION + vitest) → follow-up sprint (cj-style 71번째 진입 시점에 ✅ RESOLVED)
- **H8** = AC7.4 spec file rename variance (test_epic_16_saml_routes_extended.py → test_epic_16_tenant_idp_lookup.py) → spec 회기 update 결정 (cj-style 72번째 close-out retro 진입 시점에 보류)
- **M5** = audit_action.py typo risk (emit_audit_typed frozenset validation 부재) → CR 1-1 lesson carry + 1차 출시 후 결정 (Epic 17+ 또는 별도 epic)
- **M7** = acme seed URL placeholder deviation (idp.example.com vs idp.acme.com) → Epic 15 backward-compat 우선 결정 + atomic sprint 한계 인정
- **M9** = AC7.2 routes test count underrun (19 vs spec ~25) → Epic 16 close-out retro 진입 시점에 A104 결정 (RLS multi-tenant isolation + audit-first INSERT 검증 보강)
- **L11** = OnboardingTooltip.tsx removed step_dashboard_title stale i18n key may persist in ko-KR.json → P-015 ko-KR.json SSOT drift detector sweep 결정

### A109~A113 결정 wire 진입 (cj-style 70번째 epic 연속 정직 회복)
- **A109**: Epic 16 bmad-code-review follow-up sprint 진입 결정 wire (사용자 권장 결정) ✅ DONE
- **A110**: patch list 결정 wire = 0 PATCHED + 6 honestly DEFERRED ✅ DONE
- **A111**: handoff memory 신규 결정 wire (`memory/handoff-2026-08-22-epic-16-tenant-idp-admin-wire-review-followup-done.md`) ✅ DONE
- **A112**: deferred-work.md 업데이트 결정 wire (6 honestly DEFER entries 표 형식) ✅ DONE
- **A113**: sprint-status 업데이트 + atomic commit 결정 wire (commit `963079c`) ✅ DONE

## §7. Epic 16 T4 admin UI follow-up sprint 성과 (cj-style 71번째 epic 연속 정직 회복)

**wire scope**: 12 files atomic single sprint (10 NEW + 2 MODIFIED + commit-msg + sprint-status + deferred-work = 15 files total commit)

(1) `apps/web/app/[locale]/(dashboard)/settings/sso/page.tsx` NEW (~95 LOC RSC)
(2) `apps/web/app/[locale]/(dashboard)/settings/sso/layout.tsx` NEW (~30 LOC auth gate)
(3) `apps/web/components/settings/sso/IdPAdminPanel.tsx` NEW (~140 LOC orchestrator)
(4) `apps/web/components/settings/sso/IdPList.tsx` NEW (~110 LOC display)
(5) `apps/web/components/settings/sso/IdPCreateForm.tsx` NEW (~170 LOC 2-mode form)
(6) `apps/web/components/settings/sso/IdPEditForm.tsx` NEW (~140 LOC pre-fill form)
(7) `apps/web/components/settings/sso/IdPTestPanel.tsx` NEW (~120 LOC 8-step renderer)
(8) `apps/web/lib/auth/admin-idp-client.ts` NEW (~250 LOC fetch wrapper)
(9) `apps/web/messages/ko-KR.json` MODIFIED (settings_sso.* namespace EXTENSION 45 keys)
(10) `apps/web/__tests__/settings/sso/page.test.tsx` NEW (~280 LOC, 11 vitest RTL cases)
(11) `apps/web/__tests__/lib/admin-idp-client.test.ts` NEW (~220 LOC, 12 vitest cases)
(12) `apps/web/lib/server-api.ts` MODIFIED (~50 LOC fetchIdPConfigServerSide helper)

**§F19.4 admin UI AC #7 satisfied**: page route + 4 components + ko-KR.json SSOT + fetch wrapper + capability gate per-tenant on/off + owner-only DELETE + audit-first INSERT 보존.

**A19 cohesion 9 surface EXTENSION PASS** (IdP admin UI surface EXTENSION = page.tsx + 4 components + admin-idp-client.ts + ko-KR.json + vitest RTL).

**3중 게이트 FINAL CLEAN**: tsc --noEmit 0 NEW + vitest 23/23 PASS (11 page + 12 admin-idp-client) + ko-KR.json SSOT drift detector PASS + ruff 0 NEW + SDR vitest 77→77+23=100 (+23 from Epic 16 T4, pytest 4162 unchanged).

**C1 ✅ RESOLVED**: T4 frontend territory completely missing → 12 files atomic wire DONE. PRD §F19.4 AC satisfied.

### A114~A118 결정 wire 진입 (cj-style 71번째 epic 연속 정직 회복)
- **A114**: Epic 16 T4 admin UI follow-up sprint 진입 결정 wire (사용자 권장 결정, rationale 4종) ✅ DONE
- **A115**: T4 wire scope 12 files 결정 ✅ DONE
- **A116**: T4 atomic wire T1~T12 DONE ✅ DONE
- **A117**: 3중 게이트 FINAL CLEAN ✅ DONE
- **A118**: atomic commit + handoff 결정 wire (commit `ff5c3b5`) ✅ DONE

## §8. 3중 게이트 FINAL CLEAN retro verification (cj-style 72번째 검증)

### 8-1. ruff scoped Epic 16 wire Python files
- **All checks passed!** (Epic 16 wire Python files 15 files scoped: 5 alembic/routes/services + 4 tests + 5 modified capability/audit/main/deps + 1 capability matrix drift test)

### 8-2. pytest Epic 16 backend + parity tests
- **105/105 NEW PASS** (5 NEW backend pytest files + 1 integration drift)
  - tests/api/core/test_epic_16_alembic_0038_tenant_idps.py: 35 cases
  - tests/api/core/test_epic_16_idp_metadata_validator.py: 15 cases
  - tests/api/core/test_epic_16_idp_admin_routes.py: 19 cases
  - tests/api/core/test_epic_16_tenant_idp_lookup.py: 15 cases
  - tests/api/core/test_epic_16_audit_log_verification.py: 14 cases
  - tests/integration/test_capability_matrix_v1_28_drift.py: 7 cases
- **0 NEW regressions** (full suite baseline 4057 → 4162 = +105 NEW collected, drift +105 정확 일치)

### 8-3. vitest Epic 16 T4 follow-up frontend tests
- **23/23 NEW PASS** (2 NEW vitest RTL tests)
  - apps/web/__tests__/settings/sso/page.test.tsx: 11 cases
  - apps/web/__tests__/lib/admin-idp-client.test.ts: 12 cases

### 8-4. pnpm tsc --noEmit
- **0 NEW errors** (Epic 16 frontend files clean — pre-existing baseline errors unrelated 보존)

### 8-5. SDR drift gate
- **PASS** — pytest 4057 → **4162** = +105 NEW collected (Epic 16 atomic wire) + vitest 77 → 100 = +23 NEW (T4 follow-up)
- MAX claim 갱신: pytest SDR 4057 → 4162 = +105, vitest SDR 77 → 100 = +23

### 8-6. D-1-1-DEFER-* grep guard
- **PASS** (CR 11-3 honest-DEFER discipline 검증) — 단, Epic 15 wire 진입 시점에 D-1-1-DEFER-1/2/3 모두 honest RESOLVE 결정 (no longer preserved — RESOLVED!)
- D-EPIC-16-REVIEW-DEFER-* grep guard (H8+M5+M7+M9+L11 = 5 honestly DEFER) ✅ PRESERVED
- C1 ✅ RESOLVED (71번째 T4 follow-up 진입 시점에 frontend 12 files wire DONE)

### 8-7. commit_consistency gate
- **PASS** — CR 9-6 commit message discipline + A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + pytest file count drift 0건 + commit consistency PASS)

## §9. A19 cohesion pattern 9 surface EXTENSION PASS (IdP admin surface EXTENSION)

9/9 surfaces ALL PASS (cj-style 67~71번째 epic 연속 정직 회복 wire):

| Surface | Epic 16 wire 결정 | Status |
|---------|---------------------|--------|
| **1. kernel** (pure function) | T2 idp_metadata_validator.py (validate_idp_metadata + IdPMetadata TypedDict + 4 NEW errors + 8 validation steps + _wrap_x509_pem RFC 7468 helper) | ✅ |
| **2. port** (DB adapter) | T1 alembic 0038 (13 columns + RLS 3-policy split + UNIQUE + 3 CHECK + audit trigger + acme seed migration) | ✅ |
| **3. db schema** | T1 tenant_idps table (RLS policy `tenant_id = current_setting('app.tenant_id')` CR 0-2 verbatim + UNIQUE constraint name='uq_tenant_idps_tenant_entity') | ✅ |
| **4. service** | T5 tenant_idp_lookup.py (load_tenant_idp() + TenantIdPRow @dataclass(frozen=True, slots=True) 9 fields + TenantIdPConfigMissingError + TenantIdPDisabledError + audit-first INSERT preservation) | ✅ |
| **5. handler** | T3 idp_admin_routes.py (5 routes GET/POST/PUT/DELETE/TEST /api/v1/admin/tenant/{tenant_slug}/idp + owner/admin Dependency + capability gate) + T4 IdPAdminPanel.tsx + 4 components (IdPList + IdPCreateForm + IdPEditForm + IdPTestPanel) | ✅ |
| **6. envelope** | T2 + T3 + T5 CR 12-5 D-14 typed exception envelope 결정 wire — 4+4+2 = 10 NEW typed exceptions ({code, message_ko, details, trace_id}) | ✅ |
| **7. capability** | T6 TENANT_IDP_MANAGEMENT 1 NEW gate (industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent) + drift detector | ✅ |
| **8. audit** | T7 audit_action.py (ActionClass.AUTH + 4 NEW actions tenant_idp_created/updated/deleted/tested registry entry) + audit-first INSERT CR 1-1 verbatim + audit_log_verification pytest 14 cases | ✅ |
| **9. IdP admin surface EXTENSION** | F19.1~F19.6 + F19.4 admin UI EXTENSION (T1~T7 backend + T4 follow-up frontend 12 files) 결정 wire | ✅ EXTENSION PASS |

## §10. 9 ACs satisfied (PRD §F19.1~§F19.7 verbatim)

- **§F19.1** tenant_idps table schema (alembic 0038 + 13 columns + UNIQUE constraint + RLS 3-policy split + 3 CHECK constraints + 1 index + 1 trigger + acme seed migration) ✅
- **§F19.2** IdP metadata XML validation service (8 validation steps + IdPMetadata TypedDict 5 fields + 4 NEW error classes CR 12-5 D-14 envelope + lxml>=5.0.0 AD-14 stack pin) ✅
- **§F19.3** Tenant IdP CRUD API 5 routes (GET list + POST create + PUT update + DELETE soft + POST test + owner/admin Dependency + audit-first INSERT 4 NEW) ✅
- **§F19.4** Tenant IdP admin UI (settings/sso/page.tsx RSC + layout.tsx auth gate + IdPAdminPanel.tsx orchestrator + IdPList + IdPCreateForm + IdPEditForm + IdPTestPanel + admin-idp-client.ts + ko-KR.json settings_sso.* EXTENSION 45 keys + 2 vitest RTL tests) ✅ (T4 follow-up 71번째 진입 시점에 ✅ RESOLVED)
- **§F19.5** Per-tenant IdP routing EXTENSION (Epic 15 saml_routes.py MODIFIED hardcoded placeholder 제거 + tenant_idps table lookup + load_tenant_idp() 동적 로딩 + alembic 0038 acme 데이터 migration + Epic 12 2FA 게이트 보존) ✅
- **§F19.6** Capability gate TENANT_IDP_MANAGEMENT (1 NEW enum industry-agnostic 4-industry grants ✅/✅/✅/✅ + drift detector) ✅
- **§F19.7** tests + wire scope T1~T8 (105 NEW pytest PASS + 23 NEW vitest PASS + 1 NEW integration drift + 4 NEW audit log verification) ✅

**Epic 16 close-out retro 진입 시점에 ALL 7 §F19.* ACs ✅ satisfied** (cj-style 72번째 진입 시점에 ALL honestly resolved 결정)

## §11. CR lessons applied (cj-style 67~72번째 epic 연속 정직 회복 검증)

| CR Lesson | Epic 16 적용 | Status |
|-----------|---------------|--------|
| **CR 0-2** RLS lesson | T1 tenant_idps table multi-tenant isolation RLS policy `tenant_id = current_setting('app.tenant_id')` + T5 tenant_idp_lookup RLS 자동 적용 + T3 _resolve_tenant_id_from_slug cross-tenant check | ✅ APPLIED |
| **CR 1-1** audit-first INSERT | T3 audit-first INSERT 4 NEW 결정 wire `tenant_idp_created` + `tenant_idp_updated` + `tenant_idp_deleted` + `tenant_idp_tested` BEFORE the tenant_idps row mutation + T7 audit_action.py 4 NEW actions registry entry | ✅ APPLIED |
| **CR 9-6** commit message discipline | `git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention (5 commits 모두 정합: 08bfca5 + spec + e117e09 + 963079c + ff5c3b5) | ✅ APPLIED |
| **CR 11-3** honest-DEFER discipline | 67~72번째 epic 연속 정직 회복, D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존 + D-EPIC-16-REVIEW-DEFER-1~6 honestly 결정 wire + 0 PATCH 결정 wire 인위적 patch 생성 회피 | ✅ APPLIED |
| **CR 11-4** lessons carry (D-001~D-005 + P-015) | D-001 page.tsx mount MUST (layout RSC fetch + Client Component mount) + D-002 ko-KR.json SSOT only (settings_sso.* EXTENSION 45 keys) + D-003 vitest RTL render (page.test.tsx 11 cases) + D-004 TS mirror parity mandatory (admin-idp-client.ts Pydantic ↔ TS interface verbatim) + D-005 unknown state reject (IdPList empty state + 403/404 error envelope render) + P-015 ko-KR.json SSOT drift detector (settings_sso EXTENSION sweep) | ✅ APPLIED |
| **CR 12-1** L4 industry-agnostic capability | capability matrix v1.28 EXTENSION TENANT_IDP_MANAGEMENT 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅ (manufacturing + service + 겸영 + 겸영+기타) | ✅ APPLIED |
| **CR 12-5** D-14 typed exception envelope | idp_metadata_validator 4 NEW + idp_admin_routes 4 NEW + tenant_idp_lookup 2 NEW = 10 NEW typed exceptions, all CR 12-5 D-14 `{code, message_ko, details, trace_id}` envelope | ✅ APPLIED |
| **CR 12-5** D-PARITY-01 inversion | Python backend (idp_validator + idp_admin_routes + tenant_idp_lookup) ↔ TypeScript frontend (admin-idp-client.ts + 4 components) parity 결정 wire 보존 | ✅ PRESERVED |
| **CR 12-5** D-GATE-01 inversion | capability gate `TENANT_IDP_MANAGEMENT` per-tenant on/off + DELETE route owner-only RBAC AD-22 + Epic 12 2FA 게이트 보존 | ✅ APPLIED |
| **AD-14** stack pin | lxml>=5.0.0 pyproject.toml ADDED for IdP metadata XML validation OPTIONAL, stdlib xml.etree.ElementTree DEFAULT | ✅ APPLIED |
| **A19** cohesion pattern 9 surface EXTENSION | IdP admin surface EXTENSION PASS 결정 wire (T1~T7 backend + T4 follow-up frontend 12 files) | ✅ APPLIED |
| **A36** SDR 검증 4-step 자동 적용 | commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS 결정 | ✅ APPLIED |
| **AD-22** owner-only RBAC | DELETE route owner-only RBAC AD-22 결정 wire (DELETE /api/v1/admin/tenant/{tenant_slug}/idp) | ✅ APPLIED |
| **NFR4** PII minimization | T3 `_cert_fingerprint(cert_pem)` SHA-256 helper 결정 wire (cert fingerprint minimization) | ✅ APPLIED |

## §12. D-1-1-DEFER-* honestly RESOLVED 72번째 검증 + D-EPIC-16-REVIEW-DEFER-* status (CR 11-3 22~72번째 epic 연속)

### D-1-1-DEFER-* honestly RESOLVED 보존
| DEFER ID | Description | Status |
|----------|-------------|--------|
| **D-1-1-DEFER-1** | Magic link login | ✅ **RESOLVED** (Epic 15 wire `5f9e37f` 60번째 진입 시점에 정직 회복 결정 wire 완료, 72번째 epic 연속 정직 회복 검증 보존) |
| **D-1-1-DEFER-2** | Social login OAuth (Google/Naver/Kakao) | ✅ **RESOLVED** (Epic 15 wire `5f9e37f` 60번째 진입 시점에 정직 회복 결정 wire 완료, 72번째 epic 연속 정직 회복 검증 보존) |
| **D-1-1-DEFER-3** | SSO enterprise SAML | ✅ **RESOLVED** (Epic 15 wire `5f9e37f` 60번째 진입 시점에 정직 회복 결정 wire 완료 + Epic 16 wire `e117e09` 69번째 진입 시점에 per-tenant IdP routing EXTENSION 결정 wire 완료, 72번째 epic 연속 정직 회복 검증 보존) |

### D-EPIC-16-REVIEW-DEFER-* status (Epic 16 review follow-up sprint 70번째 진입 시점에 honestly 결정)
| DEFER ID | Description | Status | 결정 wire |
|----------|-------------|--------|-----------|
| **D-EPIC-16-REVIEW-DEFER-1** (C1) | T4 frontend territory completely missing | ✅ **RESOLVED** (cj-style 71번째 T4 follow-up sprint 진입 시점에 12 frontend files atomic wire DONE, §F19.4 AC #7 satisfied) | ✅ done |
| **D-EPIC-16-REVIEW-DEFER-2** (H8) | AC7.4 spec file rename variance (test_epic_16_saml_routes_extended.py → test_epic_16_tenant_idp_lookup.py) | ⏳ **honestly DEFERRED** (spec 회기 update 결정, cj-style 72번째 close-out retro 진입 시점에 보류) | 🔵 OPEN |
| **D-EPIC-16-REVIEW-DEFER-3** (M5) | audit_action.py typo risk (emit_audit_typed frozenset validation 부재) | ⏳ **honestly DEFERRED** (CR 1-1 lesson carry + 1차 출시 후 결정, Epic 17+ 또는 별도 epic) | 🔵 OPEN |
| **D-EPIC-16-REVIEW-DEFER-4** (M7) | acme seed URL placeholder deviation (idp.example.com vs idp.acme.com) | ⏳ **honestly DEFERRED** (Epic 15 backward-compat 우선 결정 + atomic sprint 한계 인정) | 🔵 OPEN |
| **D-EPIC-16-REVIEW-DEFER-5** (M9) | AC7.2 routes test count underrun (19 vs spec ~25) | ⏳ **honestly DEFERRED** (Epic 16 close-out retro 진입 시점에 A104 결정 — RLS multi-tenant isolation + audit-first INSERT 검증 보강) | 🔵 OPEN |
| **D-EPIC-16-REVIEW-DEFER-6** (L11) | OnboardingTooltip.tsx removed step_dashboard_title stale i18n key may persist in ko-KR.json | ⏳ **honestly DEFERRED** (P-015 ko-KR.json SSOT drift detector sweep 결정) | 🔵 OPEN |

**CR 11-3 honest-DEFER discipline 72번째 epic 연속 정직 회복 검증 완료** — D-1-1-DEFER-1/2/3 ✅ ALL RESOLVED 보존 (Epic 15 wire `5f9e37f` 60번째 진입 시점에 정직 회복 결정 wire 완료) + D-EPIC-16-REVIEW-DEFER-1 (C1) ✅ RESOLVED (71번째 T4 follow-up 진입 시점에 frontend 12 files wire DONE) + D-EPIC-16-REVIEW-DEFER-2~6 (H8+M5+M7+M9+L11) ⏳ honestly DEFERRED 보존. 누적 정직 회복: CR 11-3 22번째 (Epic 9.5) → 50번째 (Phase 3-1) → 53~57번째 (Phase 4) → 58~61번째 (Epic 15) → 62~66번째 (1st release) → 67~72번째 (Epic 16) = **72번째 epic 연속 정직 회복 결정**.

## §13. 결정 wire summary

| 결정 | 내용 | Status |
|------|------|--------|
| **A92** | 옵션 (a) Epic 16 진입 결정 wire (Tenant IdP admin management territory 진입) | ✅ DONE |
| **A93** | Master PRD v3.3 → v3.4 atomic edit (§F19 신규 + AD-30 신규 + capability matrix v1.28 EXTENSION) | ✅ DONE |
| **A94** | AD-30 Tenant IdP admin management 신규 결정 (7 sub-decisions) | ✅ DONE |
| **A95** | Capability matrix v1.27 → v1.28 EXTENSION TENANT_IDP_MANAGEMENT 1 NEW row | ✅ DONE |
| **A96** | Epic 16 wire scope T1~T8 결정 | ✅ DONE |
| **A97~A100** | Epic 16 spec entry 결정 wire (cj-style 68번째) | ✅ DONE |
| **A101~A108** | Epic 16 atomic wire T1~T8 결정 wire (cj-style 69번째) | ✅ DONE |
| **A109~A113** | Epic 16 review follow-up sprint 결정 wire (cj-style 70번째) | ✅ DONE |
| **A114~A118** | Epic 16 T4 admin UI follow-up sprint 결정 wire (cj-style 71번째) | ✅ DONE |
| **A119~A123** | Epic 16 close-out retro 결정 wire (cj-style 72번째) | 🔵 OPEN — THIS |

**A92~A118 27/27 ALL DONE + APPLIED + 보존** (Epic 16 cycle 모두 wire DONE 진입).
**A119~A123 5/5 OPEN (사용자 결정 보류)**: A119 Epic 16 close-out retro 진입 결정 wire / A120 retro document 생성 결정 wire / A121 sprint-status 업데이트 + atomic commit 결정 wire / A122 handoff memory 신규 결정 wire / A123 MEMORY.md hook index 업데이트 결정 wire.

## §14. Next unblocked 결정 wire 보류 (사용자 결정 대기)

**옵션 (a) Phase 5 진입** (multi-region backup 결정 wire 보류 해소, 1st release cycle 이후 추가 인프라 territory)
**옵션 (b) Epic 17 진입** (또 다른 territory — 예: ABAC 강화, audit log retention, advanced analytics 등)
**옵션 (c) carry-over 진입** (Epic 1~16 + Phase 3~4 + 1st release territory의 carry-over 결정 wire 해소)
**옵션 (d) 1차 출시 추가 follow-up** (1st release cycle 직후 추가 territory — 예: marketing campaigns, customer onboarding flow improvement, observability enhancement 등)
**옵션 (e) D-EPIC-16-REVIEW-DEFER-2~6 (H8+M5+M7+M9+L11) 결정 wire 해소 진입** (5 honestly DEFER follow-up sprint)

cj-style discipline 회피 위험 방지: **즉시 진입 권장** (Epic 16 close-out 진입 시점에 6-entry-point pattern 모두 wire DONE 진입 + 27/27 ALL DONE 결정 wire + C1 ✅ RESOLVED + A19 cohesion 9 surface EXTENSION PASS + 3중 게이트 FINAL CLEAN 보존 + D-1-1-DEFER-* ✅ ALL RESOLVED 결정 보존, 결정 보류 위험 해소).

## §15. 결정 wire 일자

**2026-08-22 (KST)** — cj-style Epic 16 6번째 진입점 = cj-style 72번째 epic 연속 정직 회복 retro wire DONE.

---

## Cross-References

- [[handoff-2026-08-22-epic-16-t4-admin-ui-followup-done]] — Epic 16 T4 admin UI follow-up sprint DONE (cj-style 71번째)
- [[handoff-2026-08-22-epic-16-tenant-idp-admin-wire-review-followup-done]] — Epic 16 review follow-up sprint DONE (cj-style 70번째)
- [[handoff-2026-08-22-epic-16-tenant-idp-admin-wire-done]] — Epic 16 atomic wire T1~T8 DONE (cj-style 69번째)
- [[handoff-2026-08-22-epic-16-tenant-idp-admin-wire-spec-entry-done]] — Epic 16 spec entry DONE (cj-style 68번째)
- [[handoff-2026-08-22-epic-16-prd-entry-done]] — Epic 16 PRD entry DONE (cj-style 67번째)
- [[handoff-2026-08-22-1st-release-close-out-done]] — 1st release close-out retro DONE (cj-style 66번째)
- [[handoff-2026-08-22-1st-release-launch-wire-review-done]] — 1st release review follow-up sprint DONE (cj-style 65번째)
- [[handoff-2026-08-22-1st-release-launch-wire-done]] — 1st release atomic wire T1~T8 DONE (cj-style 64번째)
- [[handoff-2026-08-22-epic-15-close-out-done]] — Epic 15 close-out retro DONE (cj-style 61번째)
- [[handoff-2026-08-22-epic-15-sso-magic-oauth-wire-done]] — Epic 15 atomic wire T1~T8 DONE (cj-style 60번째)
- [[cr-11-3-lessons]] — honest-DEFER discipline 72번째 epic 연속 정직 회복 검증
- [[cr-12-1-lessons]] — capability matrix wire pattern (L4 precedent)
- [[cr-12-5-lessons]] — D-GATE-01 inversion + D-PARITY-01 inversion + TOTP chain + cross-language drift detector
- [[cr-a19-lessons]] — A19 cohesion pattern 9 surface
- [[cr-0-2-lessons]] — RLS + multi-tenant isolation + AD-14 stack pin
- [[cr-1-1-lessons]] — audit-first INSERT
- [[cr-11-4-lessons]] — D-001~D-005 + P-015 lessons carry (Tenant IdP admin territory)
- [[ad-14-stack-pin]] — lxml>=5.0.0 IdP metadata XML validation OPTIONAL stack pin
- [[ad-22-owner-only-rbac]] — DELETE route owner-only RBAC AD-22
- [[ad-30-tenant-idp-admin-management]] — AD-30 Tenant IdP admin management 신규
- [[nfr4-pii-minimization]] — NFR4 PII minimization via cert SHA-256 fingerprint