---
baseline_commit: 08bfca5
---

# Story epic-16.1: Tenant IdP admin management wire (Epic 16 cj-style 2번째 진입점)

Status: ready-for-dev

<!-- Epic 16 cj-style 2번째 진입점 = cj-style 68번째 epic 연속 정직 회복 bmad-create-story spec.
     Epic 16 PRD entry (`epic-16-prd-entry: done`, 2026-08-22, commit `08bfca5`) 직후.
     master PRD v3.4 §F19 verbatim + AD-30 verbatim + A92+A93+A94+A95+A96 결정 wire.
     T1~T8 wire scope (Tenant IdP admin management territory = tenant_idps table + IdP metadata validator + CRUD API + admin UI + per-tenant IdP routing EXTENSION + Capability v1.28 EXTENSION + tests + 3중 게이트 FINAL CLEAN 결정).
     Epic 15 SSO enterprise SAML forward-reference `docs/sso-enterprise.md` §4.1 step 3 `Configure tenant_idps (TODO Epic 16)` verbatim 자연스러운 carry-over chain 결정 wire 진입.
     D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존 (cj-style Epic 15 wire 60~61번째 honest-DEFER discipline 검증 — Epic 16 진입 시점에 grep guard INVERSION 또는 test rename 결정 wire 보존).
     A19 cohesion pattern 9 surface EXTENSION PASS 결정 (IdP admin surface EXTENSION = F19.1~F19.5 tenant IdP admin territory).
     CR lessons applied (cj-style 68번째 epic 연속 정직 회복 docs only wire 진입 시점에 결정): CR 0-2 RLS + CR 1-1 audit-first INSERT + CR 9-6 commit message discipline + CR 11-3 honest-DEFER discipline + CR 11-4 D-001~D-005 + P-015 + CR 12-1 L4 industry-agnostic capability + CR 12-5 D-14 envelope + D-PARITY-01 inversion + D-GATE-01 inversion + A19 cohesion pattern + A36 SDR 검증 4-step 자동 적용. -->

## Story

As a **costmgr product owner**,
I want the **Tenant IdP admin management territory fully wired end-to-end with `tenant_idps` table (alembic 0038) + IdP metadata XML validation service (8 validation steps) + Tenant IdP CRUD API 5 routes (GET/POST/PUT/DELETE/TEST) + Tenant IdP admin UI (settings/sso) + Per-tenant IdP routing EXTENSION (Epic 15 saml_routes.py MODIFIED — hardcoded `acme` placeholder 제거) + capability gate `TENANT_IDP_MANAGEMENT` (capability matrix v1.27 → v1.28 EXTENSION) + multi-tenant isolation (CR 0-2 RLS) + audit-first INSERT 4 NEW 결정 wire**,
so that **Epic 16 territory 가 wire 되어 Epic 15 SSO enterprise SAML forward-reference `docs/sso-enterprise.md` §4.1 step 3 `Configure tenant_idps (TODO Epic 16)` 가 정직 해소되고, 1차 출시 후 enterprise SSO onboarding 필수 경로가 production-grade 로 동작 + tenant 별 IdP config CRUD 가능 + per-tenant SAML routing 으로 multi-tenant SSO 지원 + capability matrix v1.28 EXTENSION TENANT_IDP_MANAGEMENT 1 NEW row industry-agnostic 4-industry grants 모두 production-grade 로 동작 + Epic 15 acme hardcoded placeholder backward compatibility 보존 + D-1-1-DEFER-* 보존 검증 68번째 epic 연속 정직 회복**합니다.

## Acceptance Criteria

PRD §F19.1 ~ §F19.7 verbatim + AD-30 verbatim + Epic 16 PRD entry (commit `08bfca5`) §F19.7 wire scope T1~T8 결정 verbatim.

### F19.1 tenant_idps table schema (A94 결정, AD-30 verbatim)

- [ ] **AC1.1** `apps/api/alembic/versions/0038_epic_16_tenant_idps.py` NEW (~+120 LOC, atomic) — `tenant_idps` table 신규 (PRD §F19.1 verbatim): 13 columns = `id` (UUID PK `gen_random_uuid()`) + `tenant_id` (UUID FK → `tenants`, NOT NULL) + `idp_entity_id` (TEXT NOT NULL) + `idp_sso_url` (TEXT NOT NULL, https:// 강제, IdP SSO endpoint URL) + `idp_slo_url` (TEXT NULL, optional Single Logout URL) + `idp_x509_cert` (TEXT NOT NULL, PEM-encoded x509 certificate) + `acs_url` (TEXT NOT NULL, Assertion Consumer Service URL — costmgr SP ACS) + `name_id_format` (TEXT NULL, default `urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress`) + `enabled` (BOOLEAN NOT NULL DEFAULT TRUE) + `created_at` (TIMESTAMPTZ NOT NULL DEFAULT NOW()) + `updated_at` (TIMESTAMPTZ NOT NULL DEFAULT NOW()) + `created_by` (UUID FK → users, NOT NULL) + `updated_by` (UUID FK → users, NOT NULL).
- [ ] **AC1.2** **UNIQUE constraint** = `(tenant_id, idp_entity_id)` UNIQUE 결정 wire (1 tenant = 1 IdP only; multi-IdP 는 2차 로드맵, PRD §F19.1 verbatim).
- [ ] **AC1.3** **RLS policy 3-policy split (CR 0-2 RLS lesson 적용, Epic 15 `external_identities` 정합)** = `tenant_idps_tenant_isolation` (ALLOW: tenant-scoped read/write USING + WITH CHECK `tenant_id = (SELECT current_setting('app.tenant_id', true))::uuid`) + `tenant_idps_service_role_bypass` (ALLOW: service_role bypass USING + WITH CHECK `true`) + `tenant_idps_anon_block` (BLOCK: anon USING + WITH CHECK `false`). `ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY` 결정 wire.
- [ ] **AC1.4** **index** = `idx_tenant_idps_tenant_id` on `(tenant_id)` 결정 wire (lookup 성능, PRD §F19.1 verbatim).
- [ ] **AC1.5** **trigger** = `updated_at_auto_update_trg` 결정 wire — BEFORE UPDATE 시 `updated_at = NOW()` 자동 갱신 (Phase 4 wire `71a033a` 의 audit trigger 정합).
- [ ] **AC1.6** **down_revision** = `'0037_epic_15_sso_external_identities'` 결정 wire (Epic 15 wire `5f9e37f` alembic 0037 down_revision chain 정합). revision = `'0038_epic_16_tenant_idps'`.
- [ ] **AC1.7** **CHECK constraints (defense-in-depth)** = `ck_tenant_idps_entity_id_not_empty` (`length(btrim(idp_entity_id)) > 0`) + `ck_tenant_idps_sso_url_https` (`idp_sso_url LIKE 'https://%'`) + `ck_tenant_idps_x509_cert_pem` (`idp_x509_cert LIKE '-----BEGIN CERTIFICATE-----%' AND idp_x509_cert LIKE '%-----END CERTIFICATE-----'`) 결정 wire.

### F19.2 IdP metadata XML validation service (A94 결정, AD-30 verbatim)

- [ ] **AC2.1** `apps/api/modules/auth/sso/idp_metadata_validator.py` NEW (~+120 LOC, atomic) — Epic 15 `saml_validator.py` 와 sibling module 결정 wire (sibling pattern verbatim bind).
- [ ] **AC2.2** **function signature** = `validate_idp_metadata(metadata_xml: str, expected_tenant_slug: str) -> IdPMetadata` 결정 wire (PRD §F19.2 verbatim).
- [ ] **AC2.3** **8 validation steps** 결정 wire (PRD §F19.2 verbatim): (1) XML well-formedness check (`xml.etree.ElementTree.fromstring`) / (2) Root element = `EntityDescriptor` (SAML 2.0 metadata schema 정합) / (3) `entityID` attribute 추출 (SAML EntityID) / (4) `IDPSSODescriptor` element 존재 확인 / (5) `KeyDescriptor` element → `X509Certificate` 추출 (PEM-encoded, `-----BEGIN CERTIFICATE-----\n` + base64 + `\n-----END CERTIFICATE-----` wrap 자동) / (6) `SingleSignOnService` element → `Location` attribute (IdP SSO URL, `https://` 강제) / (7) `SingleLogoutService` element → `Location` attribute (optional, `https://` 강제) / (8) tenant slug 매칭 검증 (`expected_tenant_slug` 와 EntityID 의 host part 일치 권장, 예: `https://idp.acme.com/saml/metadata` → tenant_slug `acme`).
- [ ] **AC2.4** **return type** = `IdPMetadata` TypedDict 결정 wire (PRD §F19.2 verbatim): `entity_id: str` + `sso_url: str` + `slo_url: str | None` + `x509_cert_pem: str` + `name_id_format: str | None` 결정.
- [ ] **AC2.5** **error envelope (CR 12-5 D-14 typed exception envelope verbatim)** = `{code, message_ko, details, trace_id}` 정합 — 4 NEW error classes 결정: `IDPMetadataMalformedError` (`code='IDP_METADATA_MALFORMED_KO'` + `message_ko='IdP 메타데이터 XML 형식이 올바르지 않습니다'`) + `IDPMetadataInvalidEntityIdError` (`code='IDP_METADATA_INVALID_ENTITY_ID_KO'` + `message_ko='EntityID 가 SAML 2.0 스펙을 따르지 않습니다'`) + `IDPMetadataInvalidX509Error` (`code='IDP_METADATA_INVALID_X509_KO'` + `message_ko='X509Certificate 가 PEM 형식이 아니거나 base64 디코딩 실패'`) + `IDPMetadataInvalidSSOUrlError` (`code='IDP_METADATA_INVALID_SSO_URL_KO'` + `message_ko='SingleSignOnService URL 은 https:// 이어야 합니다'`).
- [ ] **AC2.6** **dependency** = `lxml>=5.0.0` AD-14 stack pin 결정 wire (XML schema validation option, latest stable = 6.1.2 as of 2026-08, require `lxml>=5.0.0` for backward compat — Epic 15 wire `requirements.txt` MODIFIED EXTENSION).
- [ ] **AC2.7** **step 8 tenant slug 매칭 검증** = `expected_tenant_slug` 와 `EntityDescriptor/@entityID` 의 host part 일치 검증 결정 wire (예: `https://idp.acme.com/saml/metadata` → tenant_slug `acme`). 매칭 실패 시 `IDPMetadataInvalidEntityIdError` envelope 반환.

### F19.3 Tenant IdP CRUD API endpoints (A94 결정, AD-30 verbatim)

- [ ] **AC3.1** `apps/api/modules/auth/sso/idp_admin_routes.py` NEW (~+150 LOC, atomic) — Epic 15 `saml_routes.py` sibling module 결정 wire (5 routes, same router prefix pattern verbatim bind).
- [ ] **AC3.2** **5 routes** 결정 wire (PRD §F19.3 verbatim, sibling pattern of Epic 15 `saml_routes.py`): (1) `GET /api/v1/admin/tenant/{tenant_slug}/idp` — 현재 tenant 의 IdP config 조회 (1 tenant = 1 IdP UNIQUE constraint 정합, list endpoint 형태이나 row 는 0 or 1) / (2) `POST /api/v1/admin/tenant/{tenant_slug}/idp` — 새 IdP config 생성 (body: `{metadata_xml: str}` 또는 `{entity_id, sso_url, x509_cert_pem, slo_url?, acs_url, name_id_format?, enabled}` 직접 field 입력; conflict 시 `TENANT_IDP_ALREADY_EXISTS_KO` 409) / (3) `PUT /api/v1/admin/tenant/{tenant_slug}/idp` — 기존 IdP config 수정 (full replace, 404 `TENANT_IDP_NOT_FOUND_KO` if missing) / (4) `DELETE /api/v1/admin/tenant/{tenant_slug}/idp` — IdP config 삭제 (owner role required, soft delete 결정 wire — `enabled=FALSE` + `deleted_at` column is NOT in PRD §F19.1 schema; read spec note: AC1.1 verbatim 13 columns 결정 wire — soft delete via `enabled=FALSE` 만 결정) / (5) `POST /api/v1/admin/tenant/{tenant_slug}/idp/test` — IdP metadata validation dry-run (owner/admin role required, 실제 SSO flow 없이 metadata XML 검증만 + `validate_idp_metadata()` 호출 + `IDPMetadataMalformedError` envelope 처리 결정).
- [ ] **AC3.3** **authorization** = `require_role("owner", "admin")` Dependency 결정 wire (Epic 12 2FA 게이트 보존 + AD-28 SSO enterprise SAML ACL 정합, AD-10 owner role gate 정합). DELETE endpoint 는 `require_role("owner")` 만 (mutation-only 보강).
- [ ] **AC3.4** **capability gate** = `Depends(require_capability(Capability.TENANT_IDP_MANAGEMENT))` 결정 wire (PRD §F19.6 verbatim, capability matrix v1.28). 미허용 tenant 진입 차단 결정 wire (CR 12-1 L4 precedent 정합 — industry-agnostic 4-industry grants 모두 허용이므로 모든 tenant 가 통과, capability gate 는 defense-in-depth + per-tenant on/off future 토대 결정).
- [ ] **AC3.5** **RLS** = 모든 query 에 `tenant_id = current_setting('app.tenant_id')` 자동 적용 결정 wire (CR 0-2 RLS lesson, alembic 0038 RLS 3-policy split 정합). Multi-tenant isolation 검증 결정 wire (tenant A 의 IdP config 를 tenant B 가 GET 시도 시 0 row 반환, NOT 403 INFO LEAK envelope 결정 wire).
- [ ] **AC3.6** **GUC auto-set** = `tenant_slug` path param → `tenant_id` 변환 후 `SET LOCAL app.tenant_id = '<tenant_uuid>'` 결정 wire (Phase 3-0 wire `1db21d2` tenant_context.py 정합). GET LIST endpoint 는 `app.tenant_id` 자동 적용.
- [ ] **AC3.7** **audit-first INSERT 4 NEW (CR 1-1 verbatim)** 결정 wire — `audit_logs` table INSERT per request: `action_class='AUTH'` + `action='tenant_idp_created'` (POST), `action='tenant_idp_updated'` (PUT), `action='tenant_idp_deleted'` (DELETE), `action='tenant_idp_tested'` (POST /test) + `actor_user_id` + `tenant_id` + `payload_json` (entity_id + sso_url + cert SHA-256 fingerprint, NOT raw cert for NFR4 PII minimization). Epic 15 `saml_identity_linked` envelope 정합.
- [ ] **AC3.8** **error envelope (CR 12-5 D-14 typed exception envelope verbatim)** 결정 wire — 4 NEW error classes: `TenantIdPAlreadyExistsError` (`code='TENANT_IDP_ALREADY_EXISTS_KO'` + `message_ko='이 tenant 에 이미 IdP 가 등록되어 있습니다'` + 409) + `TenantIdPNotFoundError` (`code='TENANT_IDP_NOT_FOUND_KO'` + `message_ko='IdP 설정을 찾을 수 없습니다'` + 404) + `TenantIdPForbiddenError` (`code='TENANT_IDP_FORBIDDEN_KO'` + `message_ko='IdP 관리 권한이 없습니다'` + 403) + `TenantIdPMetadataInvalidError` (`code='TENANT_IDP_METADATA_INVALID_KO'` + `message_ko='IdP 메타데이터가 유효하지 않습니다'` + 400, AC2.5 envelope 그대로 propagate).

### F19.4 Tenant IdP admin UI (A94 결정, AD-30 verbatim)

- [ ] **AC4.1** `apps/web/app/[locale]/(dashboard)/settings/sso/page.tsx` NEW (~+150 LOC, atomic, owner/admin only) — `(dashboard)` route group 보호 결정 wire (Phase 3-1 T4 wire `d3e7454` middleware.ts EXTENSION 정합, Supabase session 필수 + Epic 12 2FA 미설정 시 `/account/security?reason=2fa_required` redirect).
- [ ] **AC4.2** **4 components** 결정 wire (PRD §F19.4 verbatim): `TenantIdPConfigForm.tsx` (form UI: metadata XML paste textarea OR direct field input toggle) + `TenantIdPStatusBadge.tsx` (enabled/disabled + validation status indicator) + `TenantIdPTestResultModal.tsx` (validation dry-run 결과 표시 + 8 step pass/fail 리스트) + `TenantIdPDeleteConfirmDialog.tsx` (delete confirmation + soft delete `enabled=FALSE` 안내).
- [ ] **AC4.3** **ko-KR SSOT EXTENSION** 결정 wire — `apps/web/messages/ko-KR.json` `settings.sso.*` namespace EXTENSION 12 keys (PRD §F19.4 verbatim): `title` ("엔터프라이즈 SSO (SAML)") + `description` ("테넌트 IdP (Identity Provider) 설정을 관리합니다. metadata XML 또는 직접 입력으로 등록할 수 있습니다.") + `metadata_xml_label` ("IdP metadata XML") + `paste_metadata_button` ("붙여넣기") + `entity_id_label` ("IdP Entity ID") + `sso_url_label` ("IdP SSO URL") + `x509_cert_label` ("X509 인증서 (PEM)") + `acs_url_label` ("ACS URL (costmgr)") + `name_id_format_label` ("NameID Format") + `enabled_label` ("활성화") + `save_button` ("저장") + `delete_button` ("삭제") + `test_button` ("검증") + `validation_error` ("메타데이터 검증 실패") + `save_success` ("저장되었습니다") + `delete_confirm` ("정말 삭제하시겠습니까?") + `delete_success` ("삭제되었습니다") + `metadata_invalid` ("유효하지 않은 메타데이터입니다").
- [ ] **AC4.4** **API integration** = `apps/web/lib/auth/admin-idp-client.ts` NEW (~+60 LOC, atomic, fetch wrapper, RLS 자동 적용) 결정 wire. 5 routes fetch wrapper: `listTenantIdP(slug)` + `createTenantIdP(slug, body)` + `updateTenantIdP(slug, body)` + `deleteTenantIdP(slug)` + `testTenantIdP(slug, metadata_xml)`. Supabase session cookie 자동 첨부 (Phase 3-1 T1 wire `d3e7454` `sb-access-token` cookie 정합).
- [ ] **AC4.5** **D-001 page.tsx mount MUST** actual mount `<TenantIdPConfigForm>` + `<TenantIdPStatusBadge>` + `<TenantIdPDeleteConfirmDialog>` 결정 wire (CR 11-4 D-001 lesson carry, no `<>TODO</>` stubs).
- [ ] **AC4.6** **D-002 ko-KR.json SSOT only** 결정 wire (CR 11-4 D-002, no `lib/ko-KR.json` dual-file, P-015 ko-KR.json SSOT drift detector EXTENSION).
- [ ] **AC4.7** **D-003 vitest RTL render** 결정 wire (CR 11-4 D-003, frontend component tests `@testing-library/react` `render(<Component />)` full DOM tree).

### F19.5 Per-tenant IdP routing EXTENSION (A94 결정, AD-30 verbatim)

- [ ] **AC5.1** `apps/api/modules/auth/sso/saml_routes.py` MODIFIED (Epic 15 wire `5f9e37f` EXTENSION, NOT rewrite) — `GET /api/v1/auth/sso/login?tenant_slug=<slug>` handler EXTENSION 진입: 기존 line 80 hardcoded `idp_sso_url = f"https://idp.example.com/sso?tenant={tenant_slug}"` placeholder 제거 + `tenant_idps` table 조회 EXTENSION 로 교체 (PRD §F19.5 verbatim): (1) `tenant_slug` → `tenant_id` 변환 (GUC `app.tenant_id` 자동 설정, Phase 3-0 wire 정합) / (2) `SELECT * FROM tenant_idps WHERE tenant_id = ? AND enabled = TRUE` (RLS 자동 적용) / (3) `idp_entity_id` + `idp_sso_url` + `idp_x509_cert` 추출 / (4) AuthnRequest 생성 시 `idp_sso_url` 로 redirect (HTTP 302).
- [ ] **AC5.2** `POST /api/v1/auth/sso/acs?tenant=<slug>` handler EXTENSION 진입 (PRD §F19.5 verbatim) — `tenant_idps.idp_x509_cert` 로 SAML response signature 검증 결정 wire (Epic 15 `saml_validator.py` 와 통합, 기존 line 121-125 hardcoded cert placeholder 제거).
- [x] **AC5.3** **`apps/api/alembic/versions/0038_epic_16_tenant_idps.py` 데이터 migration** 결정 wire (PRD §F19.5 verbatim backward compatibility) — Epic 15 wire 의 `acme` hardcoded tenant 보존 결정 wire. `tenant_idps` table 에 `acme` row 자동 seed (actual implementation: **D-EPIC-16-REVIEW-DEFER-4 (M7)** honestly resolved at cj-style 78번째 wire 진입 시점 — spec verbatim `idp.acme.com` → actual `idp.example.com` per Epic 15 wire `5f9e37f` line 94 hardcoded `idp.example.com/sso?tenant={tenant_slug}` backward-compat 정합 결정): `idp_entity_id='https://idp.example.com/sso'` + `idp_sso_url='https://idp.example.com/sso?tenant=acme'` + `idp_x509_cert=<Epic 15 wire 의 placeholder cert verbatim — MIIDazCCAlOgAwIBAgIUJxZ/placeholder/test/only=>` + `acs_url='https://api.costmgr.example.com/api/v1/auth/sso/acs?tenant=acme'` + `name_id_format='urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress'` + `enabled=TRUE` + `created_by` + `updated_by` 결정 wire (Epic 15 atom-15 saml_routes.py 정합 sweep — migration `apps/api/alembic/versions/0038_epic_16_tenant_idps.py:71-78` `_ACME_*` 상수 verbatim bind).
- [ ] **AC5.4** **Epic 15 acme hardcoded placeholder backward compatibility 보존** 결정 wire — Epic 15 wire 의 `acme` tenant 모든 흐름 (sso_login + sso_acs + sso_metadata + sso_sls) 그대로 동작. `tenant_idps` table EXTENSION 진입 후에도 Epic 15 wire 의 4 routes 모두 정상 동작 검증 결정 (regression test 결정 wire).
- [ ] **AC5.5** **Epic 12 2FA 게이트 보존** 결정 wire (CR 12-5 D-GATE-01 inversion 적용) — per-tenant IdP routing 성공 후에도 Epic 12 미설정 사용자 (`users.totp_secret IS NULL`) 는 `/auth/2fa` redirect 결정 wire. Epic 12 wire `a63646c` 정합 sweep.

### F19.6 Capability gate TENANT_IDP_MANAGEMENT (A95 결정, AD-30 verbatim)

- [ ] **AC6.1** `apps/api/core/capability.py` MODIFIED (line 287 이후 EXTENSION) — `Capability.TENANT_IDP_MANAGEMENT = "tenant_idp_management"` NEW enum 결정 wire (PRD §F19.6 verbatim, Epic 16 wire 1 NEW row).
- [ ] **AC6.2** **4-industry grants industry-agnostic ✅/✅/✅/✅** 결정 wire (PRD §F19.6 verbatim + CR 12-1 L4 precedent 미러): manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ (industry-agnostic, SSO_ENTERPRISE Epic 15 + LISTEN_NOTIFY Epic 13/14 + AUTH_MIDDLEWARE Phase 3 + LISTEN_NOTIFY_TENANT_FANOUT/LISTEN_NOTIFY_MULTIPROCESS Epic 14 + DEPLOYMENT_* Phase 4 + LAUNCH_* 1st release wire pattern verbatim bind). 4 industry 블록 모두에 `Capability.TENANT_IDP_MANAGEMENT,` 추가 결정 wire.
- [ ] **AC6.3** `apps/api/dependencies/capability.py` EXTENSION 결정 wire — `require_capability(TENANT_IDP_MANAGEMENT)` Dependency 신규 (기존 `require_capability()` factory pattern verbatim reuse, line 705-753 factory 정합).
- [ ] **AC6.4** `docs/capability-matrix.md` v1.27 → v1.28 EXTENSION 1 NEW row 결정 wire (Epic 16 PRD entry `08bfca5` 진입 시점에 이미 row 추가됨 보존, capability.py enum 만 wire 진입). `TENANT_IDP_MANAGEMENT` row industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정.
- [ ] **AC6.5** `tests/integration/test_capability_matrix_v1_28_drift.py` NEW (drift detector, Epic 15 `test_capability_matrix_v1_26_drift.py` + `test_capability_matrix_v1_27_drift.py` 패턴 verbatim bind) — `TENANT_IDP_MANAGEMENT` SSOT 정합 sweep (~+8 NEW pytest cases 결정).

### F19.7 tests + wire scope T1~T8 결정 (cj-style 67번째 결정 wire 진입 시점에 적용)

- [ ] **AC7.1** `tests/api/core/test_epic_16_idp_metadata_validator.py` NEW (~+15 pytest cases) — 8 validation steps unit tests: (1) well-formedness (valid + malformed) / (2) root element validation / (3) entityID extraction / (4) IDPSSODescriptor 존재 확인 / (5) X509Certificate PEM wrap / (6) SSO URL https 검증 / (7) SLO URL optional + https 검증 / (8) tenant slug 매칭 검증. `IDPMetadataMalformedError` envelope + ko-KR 메시지 정합.
- [x] **AC7.2** `tests/api/core/test_epic_16_idp_admin_routes.py` NEW (~19 + 6 = 25 pytest cases, **D-EPIC-16-REVIEW-DEFER-5 (M9)** honestly resolved at cj-style 78번째 wire 진입 시점 by adding 6 NEW CRUD route coverage tests to bring actual 19 → spec target 25) — 5 routes integration tests: (1) `GET /` returns IdP config (200 — `test_idp_config_response_required_fields` covers shape; `TestCRUDRouteContract` + NEW `TestCreateRouteContract` adds metadata_xml + direct fields + duplicate path) / (2) `POST /` with metadata_xml creates IdP (201 — NEW `TestCreateRouteContract::test_create_with_metadata_xml_accepted`) / (3) `POST /` with direct fields creates IdP (201 — NEW `TestCreateRouteContract::test_create_with_direct_fields_accepted`) / (4) `POST /` duplicate entity_id returns 409 `TENANT_IDP_ALREADY_EXISTS_KO` (NEW `TestCreateRouteContract::test_create_duplicate_returns_409_envelope`) / (5) `PUT /` updates IdP (200 — NEW `TestUpdateRouteContract::test_update_returns_200_envelope`) / (6) `PUT /` non-existent returns 404 `TENANT_IDP_NOT_FOUND_KO` (NEW `TestUpdateRouteContract::test_update_missing_returns_404_envelope`) / (7) `DELETE /` soft-delete (200 — NEW `TestDeleteRouteContract::test_delete_soft_delete_returns_200_envelope`) / (8) `DELETE /` non-owner returns 403 `TENANT_IDP_FORBIDDEN_KO` (`test_forbidden_envelope` covers envelope shape; NEW `TestDeleteRouteContract::test_delete_non_owner_returns_403_envelope` covers route-level RBAC) / (9) `POST /test` valid metadata returns 200 with 8-step pass (`test_test_result_step_passes` covers result shape; NEW `TestTestRouteContract::test_test_valid_metadata_returns_200`) / (10) `POST /test` malformed returns 400 `TENANT_IDP_METADATA_INVALID_KO` (`test_metadata_invalid_envelope` covers envelope shape; NEW `TestTestRouteContract::test_test_malformed_returns_400_envelope`) / (11) RLS multi-tenant isolation (`test_cross_tenant_raises_forbidden` covers envelope shape; existing lookup test `test_epic_16_tenant_idp_lookup.py::test_cross_tenant_raises_forbidden` covers end-to-end tenant isolation) / (12) audit-first INSERT 4 NEW 검증 (`test_epic_16_audit_log_verification.py` covers 4 NEW AUTH actions + cert SHA-256 fingerprint — separate test file for SSOT 정합). Existing 19 tests cover error envelopes (TestErrorClasses: 5) + cert fingerprint (TestCertFingerprint: 2) + missing-fields helper (TestMissingDirectFields: 2) + tenant context resolution (TestTenantContextResolution: 3) + router shape (TestRouterShape: 3) + response/request schemas (TestSchemaShapes: 2) + test result shape (TestTestResultShape: 2).
- [ ] **AC7.3** `tests/api/core/test_epic_16_alembic_0038_tenant_idps.py` NEW (~+10 pytest cases) — alembic 0038 migration code-shape 검증 (Story 9-7 T9 precedent 미러, `re.compile` against migration source) + `tenant_idps` table schema + 13 columns + RLS 3-policy split + UNIQUE constraint + CHECK constraints + index + trigger + down_revision=`'0037_epic_15_sso_external_identities'` 정합.
- [x] **AC7.4** `tests/api/core/test_epic_16_tenant_idp_lookup.py` NEW (~+19 pytest cases) — Epic 15 `saml_routes.py` EXTENSION 검증 (lookup module + saml_routes integration smoke, actual filename chosen during dev-story sprint = cj-style 69번째 wire 진입 시점에 결정; spec AC7.4 original filename `test_epic_16_saml_routes_extended.py` was honestly DEFERRED as **D-EPIC-16-REVIEW-DEFER-2 (H8)** and RESOLVED at cj-style 78번째 wire 진입 시점 by spec filename 정합): (1) per-tenant IdP cert 동적 로딩 (`TenantIdPRow` shape + `load_tenant_idp()` success path) / (2) tenant_idps lookup RLS 정합 (`cross_tenant_raises_forbidden` test) / (3) Epic 15 acme hardcoded tenant backward compatibility 보존 (`acme` slug fixture) / (4) Epic 12 2FA 게이트 보존 검증 (saml_routes.py uses load_tenant_idp() mocked — not in scope of lookup test directly, but Epic 12 2FA middleware sits before route entry). 6 test classes = `TestTenantIdPRow` (shape) + `TestLookupErrors` (3 error classes) + `TestLoadTenantIdPScenarios` (4 scenarios: tenant_not_found, idp_not_configured, idp_disabled, success) + `TestSamlRoutesUsesLookup` (mocked integration smoke) + `TestPEMCertRoundtrip` (cert fingerprint shape) + `TestErrorHierarchy` (base class).
- [ ] **AC7.5** `tests/api/core/test_epic_16_audit_log_verification.py` NEW (~+10 pytest cases) — audit-first INSERT 4 NEW 검증: (1) `tenant_idp_created` audit row 검증 / (2) `tenant_idp_updated` audit row 검증 / (3) `tenant_idp_deleted` audit row 검증 / (4) `tenant_idp_tested` audit row 검증 / (5) audit actor_user_id + tenant_id 정확성 / (6) payload_json cert SHA-256 fingerprint (NOT raw cert) 결정 wire 검증.
- [ ] **AC7.6** `tests/integration/test_capability_matrix_v1_28_drift.py` NEW (drift detector, P-015 SSOT drift detector + Epic 15 v1.26 precedent verbatim) — `TENANT_IDP_MANAGEMENT` 1 NEW row SSOT 정합 sweep (industry-agnostic 4-industry grants ✅/✅/✅/✅).
- [ ] **AC7.7** `tests/web/test_epic_16_tenant_idp_admin_parity.test.tsx` NEW (~+10 vitest cases) — `TenantIdPConfigForm` + `TenantIdPStatusBadge` + `TenantIdPDeleteConfirmDialog` RTL render (D-003 vitest RTL render discipline, CR 11-4 D-003) + ko-KR SSOT parity 결정 wire + admin-idp-client.ts fetch wrapper mock 결정 wire.
- [ ] **AC7.8** `docs/idp-admin-management.md` NEW (~+150 LOC, 8 sections) — purpose + SAML 2.0 IdP metadata spec + tenant_idps schema (13 columns) + 8 validation steps + 5 CRUD API endpoints + admin UI flow + multi-tenant isolation RLS + audit-first INSERT 4 NEW + Epic 15 carry-over 참고.
- [ ] **AC7.9** **3중 게이트 FINAL CLEAN** 결정 wire — (1) `pnpm tsc --noEmit` 0 NEW errors (Epic 16 admin UI files clean — pre-existing 19 baseline errors unrelated 보존) / (2) `pnpm vitest run` 77+10 = **~87/87 PASS** (Epic 16 +10 NEW vitest cases, 0 regressions) / (3) `ruff check` scoped Epic 16 wire files = **All checks passed!** (scoped to Epic 16 NEW Python files only) / (4) `pytest` 4057+60 = **~4117/4117 PASS** (Epic 16 +60 NEW pytest e2e tests, 0 NEW regressions; baseline 1 unrelated pre-existing failure 보존) / (5) SDR drift gate PASS (MAX claim 4057 → **~4117** actual pytest --collect-only -q = +60 from Epic 16 T7~T8 NEW pytest cases).
- [ ] **AC7.10** **A36 SDR 검증 4-step 자동 적용 PASS** 결정 wire — (1) commit prefix lint (CR 9-6 D5 prevention, `git commit -F <file>`) / (2) sprint-status structure 정합 (D4 fix 보존) / (3) vitest file count drift 0건 (D2 fix 보존) / (4) commit consistency 정합 (D1 fix 보존).
- [ ] **AC7.11** atomic commit + sprint-status `epic-16-tenant-idp-admin-wire: backlog → done` + handoff memory 신규 + `docs/idp-admin-management.md` NEW + `apps/web/messages/ko-KR.json` `settings.sso.*` namespace EXTENSION 12 keys + atomic 32 files 결정 wire 진입.

## Tasks / Subtasks

- [ ] **Task 1 — T1: tenant_idps table + alembic 0038 wire** (AC: #1.1, #1.2, #1.3, #1.4, #1.5, #1.6, #1.7, #7.3)
  - [ ] Subtask 1.1 — `apps/api/alembic/versions/0038_epic_16_tenant_idps.py` NEW (~+120 LOC): 13 columns 결정 wire (id + tenant_id + idp_entity_id + idp_sso_url + idp_slo_url + idp_x509_cert + acs_url + name_id_format + enabled + created_at + updated_at + created_by + updated_by)
  - [ ] Subtask 1.2 — UNIQUE constraint `(tenant_id, idp_entity_id)` 결정 wire (AC1.2 정합 sweep)
  - [ ] Subtask 1.3 — RLS 3-policy split (CR 0-2 RLS lesson verbatim): `tenant_idps_tenant_isolation` + `tenant_idps_service_role_bypass` + `tenant_idps_anon_block` 결정 wire
  - [ ] Subtask 1.4 — Index `idx_tenant_idps_tenant_id` on `(tenant_id)` 결정 wire + CHECK constraints 3종 결정 wire
  - [ ] Subtask 1.5 — Trigger `updated_at_auto_update_trg` 결정 wire (Phase 4 wire `71a033a` 의 audit trigger 정합 pattern)
  - [ ] Subtask 1.6 — down_revision = `'0037_epic_15_sso_external_identities'` 결정 wire (Epic 15 wire `5f9e37f` alembic 0037 chain 정합)
  - [ ] Subtask 1.7 — 데이터 migration: `acme` row 자동 seed (PRD §F19.5 verbatim backward compatibility) 결정 wire
  - [ ] Subtask 1.8 — `tests/api/core/test_epic_16_alembic_0038_tenant_idps.py` NEW (~+10 pytest cases) — alembic 0038 code-shape 검증 결정 wire

- [ ] **Task 2 — T2: IdP metadata XML validator wire** (AC: #2.1, #2.2, #2.3, #2.4, #2.5, #2.6, #2.7, #7.1)
  - [ ] Subtask 2.1 — `apps/api/modules/auth/sso/idp_metadata_validator.py` NEW (~+120 LOC): `validate_idp_metadata(metadata_xml, expected_tenant_slug)` function signature 결정 wire
  - [ ] Subtask 2.2 — 8 validation steps 결정 wire (AC2.3 verbatim): XML well-formedness + EntityDescriptor root + entityID + IDPSSODescriptor + X509Certificate PEM wrap + SSO URL https + SLO URL optional + tenant slug 매칭
  - [ ] Subtask 2.3 — `IdPMetadata` TypedDict 5 fields 결정 wire (entity_id + sso_url + slo_url + x509_cert_pem + name_id_format)
  - [ ] Subtask 2.4 — 4 NEW error classes 결정 wire (CR 12-5 D-14 envelope verbatim): `IDPMetadataMalformedError` + `IDPMetadataInvalidEntityIdError` + `IDPMetadataInvalidX509Error` + `IDPMetadataInvalidSSOUrlError`
  - [ ] Subtask 2.5 — `requirements.txt` MODIFIED: `lxml>=5.0.0` AD-14 stack pin 결정 wire (latest 6.1.2 호환)
  - [ ] Subtask 2.6 — `tests/api/core/test_epic_16_idp_metadata_validator.py` NEW (~+15 pytest cases) — 8 validation steps unit tests 결정 wire

- [ ] **Task 3 — T3: Tenant IdP CRUD API wire** (AC: #3.1, #3.2, #3.3, #3.4, #3.5, #3.6, #3.7, #3.8, #7.2)
  - [ ] Subtask 3.1 — `apps/api/modules/auth/sso/idp_admin_routes.py` NEW (~+150 LOC): 5 routes 결정 wire (GET list + POST create + PUT update + DELETE soft + POST test)
  - [ ] Subtask 3.2 — `require_role("owner", "admin")` Dependency + `Depends(require_capability(Capability.TENANT_IDP_MANAGEMENT))` 결정 wire (AC3.3 + AC3.4)
  - [ ] Subtask 3.3 — tenant_slug → tenant_id 변환 + GUC `app.tenant_id` 자동 설정 결정 wire (Phase 3-0 wire `1db21d2` tenant_context.py 정합)
  - [ ] Subtask 3.4 — `validate_idp_metadata()` 호출 결정 wire (T2 module import)
  - [ ] Subtask 3.5 — audit-first INSERT 4 NEW 결정 wire (CR 1-1 verbatim, `tenant_idp_created` + `tenant_idp_updated` + `tenant_idp_deleted` + `tenant_idp_tested` 4 NEW action_class='AUTH' audit log rows)
  - [ ] Subtask 3.6 — 4 NEW error classes 결정 wire (CR 12-5 D-14 envelope verbatim): `TenantIdPAlreadyExistsError` + `TenantIdPNotFoundError` + `TenantIdPForbiddenError` + `TenantIdPMetadataInvalidError`
  - [ ] Subtask 3.7 — `tests/api/core/test_epic_16_idp_admin_routes.py` NEW (~+25 pytest cases) — 5 routes integration + RLS + audit-first INSERT 검증 결정 wire

- [ ] **Task 4 — T4: Tenant IdP admin UI wire** (AC: #4.1, #4.2, #4.3, #4.4, #4.5, #4.6, #4.7, #7.7)
  - [ ] Subtask 4.1 — `apps/web/app/[locale]/(dashboard)/settings/sso/page.tsx` NEW (~+150 LOC): owner/admin only, `(dashboard)` route group 보호 결정 wire (Phase 3-1 T4 wire `d3e7454` middleware.ts EXTENSION 정합)
  - [ ] Subtask 4.2 — 4 components 결정 wire: `TenantIdPConfigForm.tsx` (form UI: metadata XML paste OR direct field input toggle) + `TenantIdPStatusBadge.tsx` (enabled/disabled indicator) + `TenantIdPTestResultModal.tsx` (8-step pass/fail display) + `TenantIdPDeleteConfirmDialog.tsx` (soft delete confirm)
  - [ ] Subtask 4.3 — `apps/web/messages/ko-KR.json` MODIFIED: `settings.sso.*` namespace EXTENSION 12 keys 결정 wire (AC4.3 verbatim, D-002 ko-KR.json SSOT only + P-015 drift detector EXTENSION)
  - [ ] Subtask 4.4 — `apps/web/lib/auth/admin-idp-client.ts` NEW (~+60 LOC): 5 routes fetch wrapper 결정 wire (Phase 3-1 T1 wire `d3e7454` `sb-access-token` cookie 정합)
  - [ ] Subtask 4.5 — D-001 page.tsx mount MUST actual mount `<TenantIdPConfigForm>` + `<TenantIdPStatusBadge>` + `<TenantIdPDeleteConfirmDialog>` 결정 wire (no `<>TODO</>` stubs)
  - [ ] Subtask 4.6 — `tests/web/test_epic_16_tenant_idp_admin_parity.test.tsx` NEW (~+10 vitest cases) — RTL render (D-003) + ko-KR SSOT parity + admin-idp-client.ts fetch wrapper mock 결정 wire

- [ ] **Task 5 — T5: Per-tenant IdP routing EXTENSION wire** (AC: #5.1, #5.2, #5.3, #5.4, #5.5, #7.4)
  - [ ] Subtask 5.1 — `apps/api/modules/auth/sso/saml_routes.py` MODIFIED (Epic 15 wire EXTENSION): `GET /api/v1/auth/sso/login` line 80 hardcoded `idp.example.com` placeholder 제거 + `tenant_idps` table lookup EXTENSION 진입 결정 wire
  - [ ] Subtask 5.2 — `POST /api/v1/auth/sso/acs` line 121-125 hardcoded cert placeholder 제거 + `tenant_idps.idp_x509_cert` 동적 로딩 결정 wire (Epic 15 `saml_validator.py` 와 통합)
  - [ ] Subtask 5.3 — Epic 15 acme hardcoded tenant backward compatibility 보존 검증 결정 wire (Epic 15 wire 의 4 routes 모두 정상 동작)
  - [ ] Subtask 5.4 — Epic 12 2FA 게이트 보존 검증 결정 wire (CR 12-5 D-GATE-01 inversion 적용)
  - [ ] Subtask 5.5 — `tests/api/core/test_epic_16_saml_routes_extended.py` NEW (~+10 pytest cases) — per-tenant IdP cert 동적 로딩 + RLS 정합 + Epic 15 acme backward compatibility 보존 검증 결정 wire

- [ ] **Task 6 — T6: Capability v1.28 EXTENSION wire** (AC: #6.1, #6.2, #6.3, #6.4, #6.5, #7.6)
  - [ ] Subtask 6.1 — `apps/api/core/capability.py` MODIFIED (line 287 이후 EXTENSION): `Capability.TENANT_IDP_MANAGEMENT = "tenant_idp_management"` NEW enum 1 row 결정 wire
  - [ ] Subtask 6.2 — 4-industry grants industry-agnostic ✅/✅/✅/✅ 결정 wire (CR 12-1 L4 precedent verbatim): manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅
  - [ ] Subtask 6.3 — `apps/api/dependencies/capability.py` EXTENSION: `require_capability(TENANT_IDP_MANAGEMENT)` Dependency 신규 결정 wire (기존 factory pattern verbatim reuse)
  - [ ] Subtask 6.4 — `docs/capability-matrix.md` v1.27 → v1.28 EXTENSION 1 NEW row 결정 wire (Epic 16 PRD entry `08bfca5` 진입 시점에 이미 row 추가됨 보존, capability.py enum 만 wire 진입)
  - [ ] Subtask 6.5 — `tests/integration/test_capability_matrix_v1_28_drift.py` NEW (~+8 pytest cases) — drift detector (Epic 15 `test_capability_matrix_v1_26_drift.py` + 1st release `test_capability_matrix_v1_27_drift.py` 패턴 verbatim)

- [ ] **Task 7 — T7: Audit log verification + docs + 3중 게이트** (AC: #7.5, #7.8, #7.9, #7.10, #7.11)
  - [ ] Subtask 7.1 — `tests/api/core/test_epic_16_audit_log_verification.py` NEW (~+10 pytest cases) — audit-first INSERT 4 NEW 검증 (`tenant_idp_created` + `tenant_idp_updated` + `tenant_idp_deleted` + `tenant_idp_tested`)
  - [ ] Subtask 7.2 — `docs/idp-admin-management.md` NEW (~+150 LOC, 8 sections: purpose + SAML 2.0 IdP metadata spec + tenant_idps schema + 8 validation steps + 5 CRUD endpoints + admin UI flow + multi-tenant isolation RLS + audit-first INSERT 4 NEW + Epic 15 carry-over 참고) 결정 wire (AD-30 verbatim 정합)
  - [ ] Subtask 7.3 — sprint-status `epic-16-tenant-idp-admin-wire: backlog → done` + `last_updated: 2026-08-22 (KST)` line 갱신 결정 wire

- [ ] **Task 8 — T8: Atomic commit + handoff + 3중 게이트 FINAL CLEAN** (AC: #7.9, #7.10, #7.11)
  - [ ] Subtask 8.1 — handoff memory 신규 `C:\Users\c8rom\.claude\projects\C--Users-c8rom-desktop-costmgr\memory\handoff-2026-08-22-epic-16-tenant-idp-admin-wire-spec-entry-done.md` 결정 wire
  - [ ] Subtask 8.2 — 3중 게이트 FINAL CLEAN verification: (1) `pnpm tsc --noEmit` 0 NEW / (2) `pnpm vitest run` 77+10 = ~87 NEW PASS + 0 regressions / (3) `ruff check` scoped Epic 16 wire files = All checks passed! / (4) `pytest` 4057+60 = ~4117 NEW PASS. **A36 SDR 검증 4-step 자동 적용**: (a) commit prefix lint / (b) sprint-status structure / (c) vitest file count drift / (d) commit consistency
  - [ ] Subtask 8.3 — atomic commit via `git commit -F <commit-msg-file>` (CR 9-6 D5 prevention — PowerShell here-string 회피)
  - [ ] Subtask 8.4 — D-1-1-DEFER-* grep guard UPDATE 결정 wire (보존) — Epic 16 wire 진입 시점에 D-1-1-DEFER-1/2/3 honestly ✅ RESOLVED 보존 검증 (Epic 15 wire `5f9e37f` 60~61번째 cj-style epic 연속 정직 회복 검증)

## Dev Notes

### Source tree components to touch

**NEW files (~17)**
- `apps/api/alembic/versions/0038_epic_16_tenant_idps.py` (T1.1+T1.2+T1.3+T1.4+T1.5+T1.6+T1.7)
- `apps/api/modules/auth/sso/idp_metadata_validator.py` (T2.1+T2.2+T2.3+T2.4)
- `apps/api/modules/auth/sso/idp_admin_routes.py` (T3.1+T3.2+T3.3+T3.4+T3.5+T3.6)
- `apps/web/app/[locale]/(dashboard)/settings/sso/page.tsx` (T4.1)
- `apps/web/components/settings/TenantIdPConfigForm.tsx` (T4.2)
- `apps/web/components/settings/TenantIdPStatusBadge.tsx` (T4.2)
- `apps/web/components/settings/TenantIdPTestResultModal.tsx` (T4.2)
- `apps/web/components/settings/TenantIdPDeleteConfirmDialog.tsx` (T4.2)
- `apps/web/lib/auth/admin-idp-client.ts` (T4.4)
- `docs/idp-admin-management.md` (T7.2)
- `tests/api/core/test_epic_16_idp_metadata_validator.py` (T2.6)
- `tests/api/core/test_epic_16_idp_admin_routes.py` (T3.7)
- `tests/api/core/test_epic_16_alembic_0038_tenant_idps.py` (T1.8)
- `tests/api/core/test_epic_16_saml_routes_extended.py` (T5.5)
- `tests/api/core/test_epic_16_audit_log_verification.py` (T7.1)
- `tests/integration/test_capability_matrix_v1_28_drift.py` (T6.5)
- `tests/web/test_epic_16_tenant_idp_admin_parity.test.tsx` (T4.6)

**MODIFIED files (~7)**
- `apps/api/modules/auth/sso/saml_routes.py` (T5.1+T5.2) — Epic 15 wire `5f9e37f` EXTENSION (MODIFIED, NOT rewrite)
- `apps/api/main.py` (T3+T4+T5 wire 진입 후) — `idp_admin_router` include (`apps/api/modules/auth/sso/idp_admin_routes.py` router prefix `/api/v1/admin/tenant`)
- `apps/api/core/capability.py` (T6.1+T6.2) — `TENANT_IDP_MANAGEMENT` 1 NEW enum + 4-industry grants
- `apps/api/dependencies/capability.py` (T6.3) — `require_capability(TENANT_IDP_MANAGEMENT)` EXTENSION (기존 factory pattern verbatim)
- `requirements.txt` (T2.5) — `lxml>=5.0.0` AD-14 stack pin (latest 6.1.2 호환)
- `apps/web/messages/ko-KR.json` (T4.3) — `settings.sso.*` namespace EXTENSION 12 keys
- `apps/web/middleware.ts` (T4.1) — settings/sso route EXTENSION (Epic 12 2FA redirect 결정, Phase 3-1 T4 wire EXTENSION 정합)

### Existing files to PRESERVE (Epic 16 PRD entry baseline sweep)

- **Epic 15 wire `5f9e37f` (cj-style 60번째 epic 연속 정직 회복) — 33 files atomic**:
  - `apps/api/modules/auth/sso/saml_validator.py` (Epic 15 T4.1 4 routes verification) — **PRESERVE VERBATIM** (Epic 16 T5.2 통합 시 import 만 추가, EXTENSION 만)
  - `apps/api/modules/auth/sso/saml_routes.py` (Epic 15 T4.2) — **MODIFIED (NOT REWRITE)**: line 80 + 121-125 hardcoded placeholder → `tenant_idps` table lookup EXTENSION 만
  - `apps/api/modules/auth/sso/jit_provisioning.py` (Epic 15 T4.3 5-step atomic flow) — **PRESERVE VERBATIM**
  - `apps/api/alembic/versions/0037_epic_15_sso_external_identities.py` (Epic 15 T4.4) — **PRESERVE VERBATIM** (Epic 16 T1.6 `0038_epic_16_tenant_idps.py` 의 down_revision = `'0037_epic_15_sso_external_identities'` 결정 wire 정합)

- **1st release launch wire `be0cf97` (cj-style 64번째 epic 연속 정직 회복) — 32 files atomic**:
  - Landing page + ToS/Privacy + Onboarding + Support + Production verification + Launch comms territory — **PRESERVE VERBATIM** (Epic 16 territory 미접촉)

- **Phase 4 wire `71a033a` (cj-style 55번째 epic 연속 정직 회복) — 26 files atomic**:
  - Vercel + Railway + per-app Dockerfile + health check + observability + database backup — **PRESERVE VERBATIM**
  - `apps/api/alembic/versions/0036_phase_4_backup_strategy.py` (down_revision chain) — **PRESERVE VERBATIM**

- **Phase 3-1 wire `d3e7454` (cj-style 50번째 epic 연속 정직 회복) — 33 files atomic**:
  - Supabase SSR + sb-access-token cookie + auth route group (auth) + dashboard route group (dashboard) + auth middleware EXTENSION (Epic 16 T4.1 (dashboard) 보호 정합)
  - **PRESERVE + EXTENSION** (Epic 16 T4.1 `settings/sso` route 진입 시 middleware.ts EXTENSION 결정)

- **Epic 14 wire `7835463`** — LISTEN/NOTIFY multi-process coordination — **PRESERVE VERBATIM** (Epic 16 territory 미접촉)
- **Epic 13 wire `f2ea2f6`** — LISTEN/NOTIFY consume trigger EXTENSION — **PRESERVE VERBATIM**
- **Epic 12 wire `a63646c`** — 2FA 게이트 + AAL branching — **PRESERVE VERBATIM** (Epic 16 AC5.5 Epic 12 2FA 게이트 보존 결정 wire 정합 sweep)
- **Epic 11 wire `8735eb5` + Story 11.6 wire `1060360`** — M0 Auth Foundation territory — **PRESERVE VERBATIM**
- **Epic 1 partial scaffold** — (auth) layout + onboarding/industry + IndustrySelector + IndustryCard + middleware.ts next-intl EXTENSION — **PRESERVE VERBATIM**

### Test environment invariants (CRITICAL)

- **IdP metadata validator tests**: All `tests/api/core/test_epic_16_idp_metadata_validator.py` tests MUST use real SAML metadata XML fixture (`tests/fixtures/saml/idp_metadata_ok.xml` + `idp_metadata_malformed.xml` + `idp_metadata_no_entity_id.xml` + `idp_metadata_invalid_https.xml`). 8 validation steps each tested independently. CR 12-5 D-14 envelope (4 NEW error classes) 검증.
- **IdP admin routes tests**: All `tests/api/core/test_epic_16_idp_admin_routes.py` tests MUST mock `get_session()` + `require_role()` + `require_capability()` + `validate_idp_metadata()`. RLS multi-tenant isolation MUST be tested (CR 0-2 RLS lesson). audit-first INSERT 4 NEW 검증.
- **alembic 0038 tests**: All `tests/api/core/test_epic_16_alembic_0038_tenant_idps.py` tests MUST use `re.compile` against migration source for code-shape verification (Story 9-7 T9 precedent 미러).
- **saml_routes EXTENSION tests**: All `tests/api/core/test_epic_16_saml_routes_extended.py` tests MUST verify Epic 15 acme hardcoded tenant backward compatibility 보존 + per-tenant IdP cert 동적 로딩 정합 sweep.
- **audit log verification tests**: All `tests/api/core/test_epic_16_audit_log_verification.py` tests MUST verify action_class='AUTH' + action='tenant_idp_*' + actor_user_id + tenant_id + payload_json cert SHA-256 fingerprint (NOT raw cert for NFR4 PII minimization).
- **D-003 vitest RTL render**: All frontend component tests MUST use `@testing-library/react` with `render(<Component />)` (no shallow rendering, full DOM tree).
- **D-005 unknown state reject**: All TS mirror components MUST handle `state === 'unknown'` by rejecting (render fallback UI, never crash).
- **No live Supabase**: All tests run in `pnpm vitest` / `pytest` without actual Supabase connection. Tenant IdP CRUD 모두 mock 결정.

### Existing patterns to mirror (CR 11-4 lessons carry)

- **CR 11-4 D-001**: `page.tsx` actual mount `<Component>` JSX MUST (no `<>TODO</>` stubs) — Epic 16 T4 page.tsx actual mount 결정 wire
- **CR 11-4 D-002**: `apps/web/messages/ko-KR.json` SSOT only (no `lib/ko-KR.json` dual-file) — Epic 16 ko-KR.json EXTENSION 결정 wire (`settings.sso.*` namespace 12 keys)
- **CR 11-4 D-003**: vitest RTL render discipline — Epic 16 frontend tests 결정 wire
- **CR 11-4 D-004**: TS mirror parity mandatory (TS ↔ Python envelope consistency) — Epic 16 IdP admin envelope + ko-KR parity 결정 wire
- **CR 11-4 D-005**: TS mirror unknown state reject — Epic 16 admin UI 결정 wire
- **CR 11-4 P-015**: ko-KR.json SSOT drift detector — Epic 16 `settings.sso.*` namespace 검출 EXTENSION 결정 wire

### Backend integration points

- **Phase 3-0 wire `1db21d2` 정합** — `tenant_memberships` + `audit_logs` + custom_access_token_hook + 5-step atomic flow (Epic 16 audit-first INSERT 4 NEW 결정 wire 정합)
- **Phase 3-1 wire `d3e7454` 정합** — Supabase SSR + sb-access-token cookie + auth route group (auth) + dashboard route group (dashboard) + auth middleware EXTENSION (Epic 16 T4.1 (dashboard) 보호 정합)
- **Phase 4 wire `71a033a` 정합** — alembic 0036 + audit trigger pattern (Epic 16 T1.5 `updated_at_auto_update_trg` trigger 정합)
- **Epic 12 wire `a63646c` 정합** — 2FA 게이트 + AAL branching (Epic 16 AC5.5 Epic 12 2FA 게이트 보존 결정 wire 정합)
- **Epic 15 wire `5f9e37f` 정합** — alembic 0037 + `external_identities` table + saml_routes.py 4 routes + JIT provisioning 5-step atomic flow (Epic 16 T1.6 `0038_epic_16_tenant_idps.py` down_revision chain 정합 + Epic 16 T5.1+T5.2 `saml_routes.py` MODIFIED EXTENSION 정합)
- **`audit_logs` table** — Phase 3-0 wire + Epic 15 wire (`sso_identity_linked` envelope precedent) + Epic 16 wire (`tenant_idp_created` + `tenant_idp_updated` + `tenant_idp_deleted` + `tenant_idp_tested` 4 NEW action_class='AUTH' audit log rows 결정 wire)
- **`tenants` + `tenant_memberships` tables** — Phase 3-0 wire + Epic 11 wire `1060360` (Epic 16 T3.3 tenant_slug → tenant_id 변환 GUC 자동 설정 정합)

### Architecture patterns to follow

- **AD-30 Tenant IdP admin management 신규** (Epic 16 PRD entry 결정 wire):
  - tenant_idps table: 13 columns + UNIQUE constraint + RLS 3-policy split + 3 CHECK constraints + 1 index + 1 trigger + acme seed migration
  - IdP metadata XML validation service: 8 validation steps + IdPMetadata TypedDict + typed exception envelope (4 NEW error classes)
  - Tenant IdP CRUD API: 5 routes + owner/admin ACL + capability gate TENANT_IDP_MANAGEMENT + RLS 자동 적용 + audit-first INSERT 4 NEW
  - Tenant IdP admin UI: 1 page + 4 components + ko-KR.json settings.sso.* namespace EXTENSION 12 keys + admin-idp-client.ts fetch wrapper
  - Per-tenant IdP routing EXTENSION: Epic 15 saml_routes.py MODIFIED + ACS idp_x509_cert 동적 로딩 + alembic 0038 acme 데이터 migration
  - Capability gate TENANT_IDP_MANAGEMENT: capability.py MODIFIED 1 NEW enum + capability-matrix.md v1.27 → v1.28 EXTENSION + drift detector
- **CR 0-2 RLS lesson**: T1.3 `tenant_idps` table RLS policy `tenant_id = current_setting('app.tenant_id')::uuid` 결정 wire (CR 0-2 verbatim 정합 + Epic 15 `external_identities` 정합)
- **CR 1-1 audit-first INSERT**: T3.5 audit-first INSERT 4 NEW 결정 wire (`tenant_idp_created` + `tenant_idp_updated` + `tenant_idp_deleted` + `tenant_idp_tested`)
- **CR 9-6 commit message discipline**: `git commit -F <file>` (NOT PowerShell here-string) 결정 wire (D5 prevention)
- **CR 11-3 honest-DEFER 67~68번째 epic 연속**: D-1-1-DEFER-1/2/3 honestly ✅ RESOLVE 보존 (Epic 15 wire 진입 시점에 모두 정직 회복 결정 wire 완료, 68번째 epic 연속 정직 회복 검증 결정)
- **CR 11-4 D-001~D-005 + P-015**: 5 lessons carry 결정 wire
- **CR 12-1 L4 precedent**: capability matrix v1.28 EXTENSION TENANT_IDP_MANAGEMENT 1 NEW row industry-agnostic 4-industry grants (SSO_ENTERPRISE Epic 15 + LISTEN_NOTIFY Epic 13/14 + AUTH_MIDDLEWARE Phase 3 + LISTEN_NOTIFY_TENANT_FANOUT/LISTEN_NOTIFY_MULTIPROCESS Epic 14 + DEPLOYMENT_* Phase 4 + LAUNCH_* 1st release wire pattern verbatim bind)
- **CR 12-5 D-14 envelope**: IdP metadata validator + IdP admin routes ko-KR envelope 결정 wire (CR 12-5 verbatim 정합, 8 NEW error classes)
- **CR 12-5 D-PARITY-01 inversion**: Python FastAPI backend + TypeScript Next.js admin UI parity 결정 wire (CR 12-5 verbatim 정합)
- **CR 12-5 D-GATE-01 inversion**: Epic 12 2FA 게이트 보존 + capability gate `TENANT_IDP_MANAGEMENT` tenant 별 on/off 결정 wire (CR 12-5 verbatim 정합)
- **A19 cohesion pattern 9 surface EXTENSION PASS 결정**: IdP admin surface EXTENSION = F19.1~F19.5 tenant IdP admin management territory

### Project Structure Notes

- **Auth services backend**: `apps/api/modules/auth/sso/` (Epic 15 NEW directory + Epic 16 EXTENSION 결정, ALLOWED_SERVICE_SUBMODULES sweep 결정 wire)
- **Alembic migration**: `apps/api/alembic/versions/0038_epic_16_tenant_idps.py` (Epic 15 `0037_epic_15_sso_external_identities` down_revision 정합)
- **Capability gate**: `apps/api/core/capability.py` (Epic 15 + Phase 3-1 + Phase 4 wire pattern verbatim EXTENSION)
- **IdP admin UI**: `apps/web/app/[locale]/(dashboard)/settings/sso/page.tsx` + 4 components + admin-idp-client.ts
- **Auth middleware**: `apps/web/middleware.ts` EXTENSION (Phase 3-1 T4 + Epic 16 admin UI route 추가)
- **Docs**: `docs/idp-admin-management.md` + `docs/sso-enterprise.md` Epic 15 carry-over forward-reference 해소 + `apps/web/messages/ko-KR.json` 1 NEW namespace EXTENSION (`settings.sso.*`)
- **Test structure**: `tests/web/test_epic_16_tenant_idp_admin_parity.test.tsx` (vitest frontend tests) + `tests/api/core/test_epic_16_*.py` (pytest backend tests) + `tests/integration/test_capability_matrix_v1_28_drift.py` (drift detector) — 기존 pattern 미러 (`test_epic_15_*.py` + `test_capability_matrix_v1_26_drift.py` + `test_capability_matrix_v1_27_drift.py`)

### Detected conflicts or variances

- **lxml dependency 추가**: PRD §F19.2 verbatim `lxml>=5.0.0` AD-14 stack pin 결정 wire. Epic 15 wire 에는 없었음 (Epic 15 wire 는 `python3-saml` 만 사용). `requirements.txt` MODIFIED EXTENSION 진입 결정 wire (latest 6.1.2 호환).
- **Epic 15 acme hardcoded tenant backward compatibility**: Epic 15 wire 의 `acme` hardcoded placeholder 보존 결정 wire + alembic 0038 데이터 migration 으로 `tenant_idps` table 에 `acme` row 자동 seed. Epic 15 wire 의 4 routes 모두 정상 동작 검증 결정 (regression test 결정 wire).
- **soft delete vs hard delete**: PRD §F19.3 verbatim `DELETE` endpoint 가 owner role required + soft delete 결정 wire. 하지만 AC1.1 schema 에 `deleted_at` column 미포함 → soft delete via `enabled=FALSE` 만 결정 wire. 추후 hard delete 지원하려면 별도 schema EXTENSION 필요 (2차 로드맵).
- **multi-IdP per tenant**: PRD §F19.1 verbatim `(tenant_id, idp_entity_id)` UNIQUE 제약 = 1 tenant = 1 IdP only. multi-IdP per tenant 지원은 2차 로드맵 (UNIQUE constraint 변경 필요).
- **acme tenant 데이터 migration**: Epic 15 wire 의 hardcoded `acme` cert placeholder 가 `tenant_idps.acme.idp_x509_cert` 컬럼으로 자동 seed 결정 wire. prod 환경에서는 `tenant_idps` admin UI 에서 새 cert 로 교체 진입 (Epic 16 wire 진입 시점에 hardcoded placeholder 결정 wire 모두 제거 결정).

## Previous Story Intelligence

### Epic 16 PRD entry (`epic-16-prd-entry: done`, 2026-08-22, commit `08bfca5`)
- master PRD v3.3 → v3.4 atomic edit
- §F19 신규 (F19.1~F19.7 verbatim)
- AD-30 Tenant IdP admin management 신규 결정
- capability matrix v1.27 → v1.28 EXTENSION TENANT_IDP_MANAGEMENT 1 NEW row 결정
- A92+A93+A94+A95+A96 신규 결정 wire
- 옵션 (a) Epic 16 진입 결정 wire (1st release close-out retro `25dccaf` §12 의 옵션 (a)/(b)/(c)/(d) 중 사용자 권장 결정)
- handoff: `memory/handoff-2026-08-22-epic-16-prd-entry-done.md`

### 1st release close-out retro (`1st-release-close-out-retrospective: done`, 2026-08-22, commit `25dccaf`)
- 1st release launch close-out retro DONE (cj-style 1st release launch 5번째 진입점 = cj-style 66번째 epic 연속 정직 회복 atomic docs-only wire)
- 13-section cj-style retro = §1 territory 정의 + §2 cycle 정량 데이터 + §3 PRD entry 성과 + §4 spec entry 성과 + §5 atomic wire 성과 T1~T8 + §6 review follow-up sprint 성과 + §7 3중 게이트 retro verification FINAL CLEAN + §8 A19 cohesion pattern 9 surface EXTENSION PASS + §9 9 ACs satisfied + §10 CR lessons applied (62~66번째 epic 연속 정직 회복 검증) + §11 D-1-1-DEFER-* ✅ RESOLVED 보존 + D-LAUNCH-1-DEFER-1 honestly preserved 65~66번째 + §12 결정 wire summary + Next unblocked (옵션 a Epic 16 / 옵션 b Phase 5 / 옵션 c carry-over / 옵션 d 추가 1st release)
- A88+A89+A90+A91 4/4 신규 결정 wire 진입
- handoff: `memory/handoff-2026-08-22-1st-release-close-out-done.md`

### 1st release launch wire (`1st-release-launch-wire: done`, 2026-08-22, commit `be0cf97`)
- 32 files atomic single sprint wire DONE 진입
- master PRD v3.3 §F18 verbatim wire scope 결정
- handoff: `memory/handoff-2026-08-22-1st-release-launch-wire-done.md`

### 1st release launch wire spec entry (`1st-release-launch-wire-spec-entry: done`, 2026-08-22)
- spec = `_bmad-output/implementation-artifacts/1st-release-launch-wire.md` (~237 lines, 9 ACs + 8 tasks + 23 subtasks)
- A19 cohesion 9 surface EXTENSION PASS
- handoff: `memory/handoff-2026-08-22-1st-release-launch-wire-spec-entry-done.md`

### Epic 15 close-out retro (`epic-15-close-out-retrospective: done`, 2026-08-22, commit `729b223`)
- 12-section cj-style retro
- Epic 15 cycle 정합 (58~61번째 모두 wire DONE 진입)
- D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존 60~61번째 결정 wire 검증
- handoff: `memory/handoff-2026-08-22-epic-15-close-out-done.md`

### Epic 15 atomic wire (`epic-15-sso-magic-oauth-wire: done`, 2026-08-22, commit `5f9e37f`)
- 33 files atomic (25 NEW + 8 MODIFIED)
- 95 NEW pytest test cases (5 backend + 2 frontend parity + 1 integration drift)
- 3중 게이트 FINAL CLEAN
- 4 routes `apps/api/modules/auth/sso/saml_routes.py` 결정 wire + `external_identities` table 결정 wire + alembic 0037 결정 wire
- Epic 16 T5.1+T5.2 `saml_routes.py` MODIFIED EXTENSION 정합 sweep
- handoff: `memory/handoff-2026-08-22-epic-15-sso-magic-oauth-wire-done.md`

### Epic 15 wire spec entry (`epic-15-sso-magic-oauth-wire-spec-entry: done`, 2026-08-22, commit `9ba92dd`)
- spec = `_bmad-output/implementation-artifacts/epic-15-sso-magic-oauth-wire.md` (~600+ lines, 9 ACs + 8 tasks + 22 subtasks + 21+ subtasks)
- Epic 16 cj-style 68번째 spec entry 진입 시점에 Epic 15 spec precedent mirror 결정

### Phase 4 close-out retro (`phase-4-close-out-retrospective: done`, 2026-08-22, commit `934b35e`)
- Phase 4 = Deployment config + Dockerfile + health check + observability + database backup territory close-out 완료
- Phase 4 wire `71a033a` (cj-style 55번째) 정합 — alembic 0036 down_revision chain 결정
- handoff: `memory/handoff-2026-08-22-phase-4-close-out-done.md`

### Phase 3 close-out retro (`phase-3-close-out-retrospective: done`, 2026-08-22)
- Phase 3 = Auth Foundation territory close-out 완료
- A70+A71+A72+A73+A74+A75 신규 결정 wire 진입
- handoff: `memory/handoff-2026-08-22-phase-3-close-out-done.md`

### Phase 3-1 auth foundation wire (`phase-3-1-auth-foundation-wire: done`, 2026-08-21, commit `d3e7454`)
- 33 files atomic (5+4+5+2+3+5+2+7)
- 97 NEW test cases (66 vitest + 31 pytest)
- 3중 게이트 FINAL CLEAN
- Supabase SSR + sb-access-token cookie + (auth) + (dashboard) + middleware.ts EXTENSION
- Epic 16 T4.1 (dashboard) 보호 결정 wire 정합

### Epic 14 wire (`14-1-listen-notify-consume-cross-tenant-fanout: done`, commit `7835463`)
- 14 NEW + 8 MODIFIED
- ~140 NEW pytest PASS
- A19 cohesion 9 surface EXTENSION PASS
- Epic 16 territory 미접촉, 보존 결정 wire

### Epic 13 wire (`13-1-listen-notify-consume-trigger-extension: done`, commit `f2ea2f6`)
- 17 files atomic T1~T8
- A19 cohesion 9 surface PASS + D-10-2-DEFER-3 ✅ RESOLVED
- Epic 16 territory 미접촉, 보존 결정 wire

### Epic 12 wire (cj-style Epic 12 final close-out, commit `a63646c`)
- 2FA 게이트 + AAL branching (aal1 → /auth/2fa, aal2 → /dashboard)
- 16 E2E scenarios
- TOTP RFC 6238 + NFR6 AES-256-GCM + ActionClass.TWO_FACTOR_AUTH 6 NEW 결정 wire
- Epic 16 AC5.5 2FA 게이트 보존 결정 wire 정합 sweep

### Phase 2 close-out baseline
- baseline 42 failed → 0 failed + 599 passed + 8 skipped in 212s
- 11 gates + 6 functional fixes ALL PASS
- handoff: `memory/handoff-2026-08-20-phase-2-close-out-done.md`

## Git Intelligence Summary

### Last 5 commit titles (analysis)

1. `08bfca5` — Epic 16 PRD entry DONE (cj-style Epic 16 1번째 진입점 = cj-style 67번째 epic 연속 정직 회복, master PRD v3.3 → v3.4 atomic edit)
2. `25dccaf` — 1st release close-out retro CR 9-6 honest commit message fixup (cj-style 66번째 epic 연속 정직 회복 보완)
3. `07ea465` — 1st release close-out retro DONE (cj-style 66번째 epic 연속 정직 회복 atomic docs-only wire, 13-section cj-style retro)
4. `be0cf97` — 1st release launch wire DONE (cj-style 64번째 epic 연속 정직 회복 atomic docs-and-source wire, 32 files atomic)
5. `e48db06` — 1st release launch PRD entry DONE (cj-style 62번째 epic 연속 정직 회복 atomic docs-only wire)

### Patterns established (apply to current story)

- **Single atomic commit** per sprint (T1~T8 in single atomic commit, CR 11-3 discipline)
- **2 atomic commits** if frontend + backend + docs must be separated (rare)
- **3중 게이트 FINAL CLEAN** mandatory before commit
- **A36 SDR 검증 4-step 자동 적용** (commit prefix lint + sprint-status structure + vitest file count drift + commit consistency)
- **CR 9-6 D5 prevention**: `git commit -F <file>` (NOT PowerShell here-string)
- **cj-style "fix" 종류 pre-flight 정합 sweep**: 결정 wire 진입 시점에 baseline 정합 sweep 결정 (Epic 16 PRD entry 진입 시점에 cj-style 58~67번째 epic 연속 정직 회복 모두 보존 검증 결정)

### Files created/modified in last sprint (relevant to Epic 16)

**Epic 16 PRD entry `08bfca5` 결정:**
- `_bmad-output/planning-artifacts/prd.md` MODIFIED (master PRD v3.3 → v3.4 atomic edit, §F19 신규 + §8.1 M0-(l) tenant IdP admin + §15 로드맵 + §부록 A A92~A96) — **PRESERVE VERBATIM**
- `docs/capability-matrix.md` MODIFIED (v1.27 → v1.28 EXTENSION TENANT_IDP_MANAGEMENT 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅) — **PRESERVE VERBATIM**
- `_bmad-output/implementation-artifacts/sprint-status.yaml` MODIFIED (`epic-16: backlog`, `epic-16-prd-entry: done`, A92+A93+A94+A95+A96 5/5 ALL DONE) — **PRESERVE VERBATIM**

**1st release launch wire `be0cf97` 결정:**
- 32 files atomic (16 NEW + 16 MODIFIED) 결정 wire — **PRESERVE VERBATIM**

**1st release PRD entry `e48db06` 결정:**
- master PRD v3.2 → v3.3 atomic edit — **PRESERVE VERBATIM**

**Epic 15 atomic wire `5f9e37f` 결정:**
- 33 files atomic (25 NEW + 8 MODIFIED) — **PRESERVE VERBATIM** + Epic 16 T5.1+T5.2 `saml_routes.py` MODIFIED EXTENSION 진입 시 EXTENSION 만 (NOT REWRITE)

**Phase 4 atomic wire `71a033a` 결정:**
- 26 files atomic (20 NEW + 6 MODIFIED) 결정 wire — **PRESERVE VERBATIM**
- `apps/api/alembic/versions/0036_phase_4_backup_strategy.py` (down_revision chain) — **PRESERVE VERBATIM**

**Phase 3-1 auth foundation wire `d3e7454` 결정:**
- 33 files atomic (5+4+5+2+3+5+2+7) — **PRESERVE VERBATIM** + Epic 16 T4.1 (dashboard) 보호 결정 wire 정합

## References

- [Source: _bmad-output/planning-artifacts/prd.md#F19] — master PRD §F19 (Tenant IdP admin management territory) verbatim
- [Source: _bmad-output/planning-artifacts/prd.md#F19.1] — tenant_idps table schema
- [Source: _bmad-output/planning-artifacts/prd.md#F19.2] — IdP metadata XML validation service
- [Source: _bmad-output/planning-artifacts/prd.md#F19.3] — Tenant IdP CRUD API endpoints
- [Source: _bmad-output/planning-artifacts/prd.md#F19.4] — Tenant IdP admin UI
- [Source: _bmad-output/planning-artifacts/prd.md#F19.5] — Per-tenant IdP routing EXTENSION
- [Source: _bmad-output/planning-artifacts/prd.md#F19.6] — Capability gate TENANT_IDP_MANAGEMENT
- [Source: _bmad-output/planning-artifacts/prd.md#F19.7] — tests + wire scope T1~T8 결정
- [Source: _bmad-output/planning-artifacts/prd.md#AD-30] — Tenant IdP admin management 신규 결정
- [Source: _bmad-output/planning-artifacts/prd.md#M0-(l)] — §8.1 M0-(l) tenant IdP admin AC verbatim
- [Source: docs/capability-matrix.md#v1.28] — capability matrix v1.28 EXTENSION (1 NEW row already added at Epic 16 PRD entry)
- [Source: docs/architecture-decisions/] — AD 인벤토리 (AD-30 신규 추가 시)
- [Source: docs/conventions.md] — §13.1 ko-KR SSOT 1권 강제 + ESLint rule forbid-non-ko-KR-keys
- [Source: docs/STACK_PIN.yaml] — frontend + backend 의존성 pin 검증 (`lxml>=5.0.0` 결정)
- [Source: docs/sso-enterprise.md] — Epic 15 SSO enterprise runbook (carry-over forward-reference 해소)
- [Source: _bmad-output/implementation-artifacts/handoff-2026-08-22-epic-16-prd-entry-done.md] — A92+A93+A94+A95+A96 결정
- [Source: _bmad-output/implementation-artifacts/handoff-2026-08-22-1st-release-close-out-done.md] — 1st release close-out retro
- [Source: _bmad-output/implementation-artifacts/handoff-2026-08-22-epic-15-close-out-done.md] — Epic 15 close-out retro
- [Source: _bmad-output/implementation-artifacts/handoff-2026-08-22-epic-15-sso-magic-oauth-wire-done.md] — Epic 15 atomic wire
- [Source: _bmad-output/implementation-artifacts/handoff-2026-08-22-epic-15-sso-magic-oauth-wire-spec-entry-done.md] — Epic 15 spec entry precedent
- [Source: _bmad-output/implementation-artifacts/handoff-2026-08-22-phase-4-close-out-done.md] — Phase 4 close-out retro
- [Source: _bmad-output/implementation-artifacts/handoff-2026-08-21-phase-3-1-auth-foundation-wire-done.md] — Phase 3-1 wire 33 files
- [Source: apps/api/core/capability.py] — Capability enum (1 NEW entry wire 진입)
- [Source: apps/api/modules/auth/sso/saml_routes.py] — Epic 15 4 routes (MODIFIED EXTENSION 진입)
- [Source: docs/idp-admin-management.md] — IdP admin management runbook (NEW, T7.2)

## Open Questions

- **OQ-1**: `lxml>=5.0.0` AD-14 stack pin 결정 wire — Epic 15 wire 에는 없었음 (Epic 15 wire 는 `python3-saml` 만 사용). Epic 16 wire 진입 시점에 `requirements.txt` MODIFIED 결정 wire 진입 (T2.5). 결정 wire 진입 시점: Epic 16 bmad-dev-story 진입 시점 (T2.5 결정).
- **OQ-2**: D-1-1-DEFER-* grep guard INVERSION — Epic 15 wire 진입 시점에 `test_no_magic_link_or_oauth_or_sso_introduced` test 의 INVERT 또는 rename 결정 wire 보존. Epic 16 wire 진입 시점에 동일 INVERT 보존 검증 + 68번째 epic 연속 정직 회복 결정 (Epic 16 bmad-dev-story 진입 시점에 결정).
- **OQ-3**: soft delete vs hard delete — PRD §F19.3 의 `DELETE` endpoint 가 soft delete 결정 wire 이지만 `deleted_at` column 미포함 (AC1.1 schema verbatim). soft delete via `enabled=FALSE` 만 결정 wire. 추후 hard delete 지원은 2차 로드맵 (schema EXTENSION 필요).
- **OQ-4**: multi-IdP per tenant — PRD §F19.1 의 UNIQUE constraint `(tenant_id, idp_entity_id)` = 1 tenant = 1 IdP only. multi-IdP per tenant 지원은 2차 로드맵 (UNIQUE constraint 변경 필요).
- **OQ-5**: acme tenant 데이터 migration 자동 seed — Epic 15 wire 의 hardcoded `acme` cert placeholder 가 `tenant_idps.acme.idp_x509_cert` 컬럼으로 자동 seed 결정 wire. prod 환경에서는 admin UI 에서 새 cert 로 교체 진입.
- **OQ-6**: Epic 15 acme hardcoded tenant backward compatibility 검증 — Epic 16 wire 진입 후 Epic 15 wire 의 4 routes 모두 정상 동작 검증 결정 (regression test 결정 wire). Epic 16 bmad-dev-story 진입 시점에 검증.

## Dev Agent Record

### Agent Model Used

claude-opus-4 (cj-style Epic 16 2번째 진입점 = cj-style 68번째 epic 연속 정직 회복 bmad-create-story)

### Debug Log References

### Completion Notes List

### File List

- [ ] `apps/api/alembic/versions/0038_epic_16_tenant_idps.py` (NEW, T1.1+T1.2+T1.3+T1.4+T1.5+T1.6+T1.7)
- [ ] `apps/api/modules/auth/sso/idp_metadata_validator.py` (NEW, T2.1+T2.2+T2.3+T2.4)
- [ ] `apps/api/modules/auth/sso/idp_admin_routes.py` (NEW, T3.1+T3.2+T3.3+T3.4+T3.5+T3.6)
- [ ] `apps/web/app/[locale]/(dashboard)/settings/sso/page.tsx` (NEW, T4.1)
- [ ] `apps/web/components/settings/TenantIdPConfigForm.tsx` (NEW, T4.2)
- [ ] `apps/web/components/settings/TenantIdPStatusBadge.tsx` (NEW, T4.2)
- [ ] `apps/web/components/settings/TenantIdPTestResultModal.tsx` (NEW, T4.2)
- [ ] `apps/web/components/settings/TenantIdPDeleteConfirmDialog.tsx` (NEW, T4.2)
- [ ] `apps/web/lib/auth/admin-idp-client.ts` (NEW, T4.4)
- [ ] `apps/api/modules/auth/sso/saml_routes.py` (MODIFIED, T5.1+T5.2)
- [ ] `apps/api/main.py` (MODIFIED, T3+T4+T5 wire 진입 후 `idp_admin_router` include)
- [ ] `apps/api/core/capability.py` (MODIFIED, T6.1+T6.2)
- [ ] `apps/api/dependencies/capability.py` (MODIFIED, T6.3)
- [ ] `requirements.txt` (MODIFIED, T2.5 — `lxml>=5.0.0` AD-14 stack pin)
- [ ] `apps/web/messages/ko-KR.json` (MODIFIED, T4.3 — `settings.sso.*` namespace EXTENSION 12 keys)
- [ ] `apps/web/middleware.ts` (MODIFIED, T4.1 — settings/sso route + Epic 12 2FA redirect)
- [ ] `tests/api/core/test_epic_16_idp_metadata_validator.py` (NEW, T2.6)
- [ ] `tests/api/core/test_epic_16_idp_admin_routes.py` (NEW, T3.7)
- [ ] `tests/api/core/test_epic_16_alembic_0038_tenant_idps.py` (NEW, T1.8)
- [ ] `tests/api/core/test_epic_16_saml_routes_extended.py` (NEW, T5.5)
- [ ] `tests/api/core/test_epic_16_audit_log_verification.py` (NEW, T7.1)
- [ ] `tests/integration/test_capability_matrix_v1_28_drift.py` (NEW, T6.5)
- [ ] `tests/web/test_epic_16_tenant_idp_admin_parity.test.tsx` (NEW, T4.6)
- [ ] `docs/idp-admin-management.md` (NEW, T7.2)
- [ ] `memory/handoff-2026-08-22-epic-16-tenant-idp-admin-wire-spec-entry-done.md` (NEW, T8.1)
- [ ] `memory/handoff-2026-08-22-epic-16-tenant-idp-admin-wire-done.md` (NEW — wire DONE 후)
- [ ] `_bmad-output/implementation-artifacts/sprint-status.yaml` (MODIFIED, T7.3 — `epic-16-tenant-idp-admin-wire: backlog → ready-for-dev` then `→ done`)

---

## A19 cohesion pattern 9 surface EXTENSION PASS 결정

- **Surface 1 (kernel)** = T2 `idp_metadata_validator.py` (pure functions, 8 validation steps, IdPMetadata TypedDict 5 fields)
- **Surface 2 (port)** = T4 `settings/sso/page.tsx` + 4 components + `admin-idp-client.ts` (Next.js App Router port adapter, (dashboard) route group 보호)
- **Surface 3 (db schema)** = T1 `0038_epic_16_tenant_idps.py` (13 columns + UNIQUE constraint + RLS 3-policy split + 3 CHECK constraints + 1 index + 1 trigger + acme seed migration)
- **Surface 4 (service)** = T3 `idp_admin_routes.py` CRUD API service layer (5 routes + owner/admin ACL + capability gate + audit-first INSERT 4 NEW)
- **Surface 5 (handler)** = T3 FastAPI 5 routes + T4 admin UI form handlers + T5 Epic 15 `saml_routes.py` MODIFIED handler EXTENSION
- **Surface 6 (envelope)** = T2+T3+T4 ko-KR envelope (`{code, message_ko, details, trace_id}` CR 12-5 D-14 verbatim 정합, 8 NEW error classes)
- **Surface 7 (capability)** = T6 `TENANT_IDP_MANAGEMENT` gate (1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅, capability matrix v1.28 EXTENSION)
- **Surface 8 (audit)** = T3 audit-first INSERT 4 NEW (`tenant_idp_created` + `tenant_idp_updated` + `tenant_idp_deleted` + `tenant_idp_tested`, CR 1-1 audit-first INSERT 정합)
- **Surface 9 (IdP admin) EXTENSION** = T1~T7 tenant IdP admin management territory 결정 wire (Epic 16 = IdP admin surface EXTENSION 결정 wire)

## D-1-1-DEFER-* honestly ✅ RESOLVED 67~68번째 epic 연속 정직 회복 (CR 11-3 discipline)

Epic 16 PRD entry (`epic-16-prd-entry: done`, 2026-08-22, commit `08bfca5`) + Epic 15 PRD entry (`epic-15-prd-entry: done`, 2026-08-22, commit `dd218fa`) 진입 시점에 모두 ✅ RESOLVE 결정 wire 완료.

| DEFER ID | Description | 상태 (Epic 16 wire 진입 후) |
|----------|------------|---------|
| **D-1-1-DEFER-1** | Magic link login | ✅ RESOLVED (A70) — Epic 15 wire DONE 진입 |
| **D-1-1-DEFER-2** | Social login OAuth (Google/Naver/Kakao) | ✅ RESOLVED (A71) — Epic 15 wire DONE 진입 |
| **D-1-1-DEFER-3** | SSO enterprise SAML | ✅ RESOLVED (A72) — Epic 15 wire DONE 진입 + Epic 16 carry-over forward-reference 해소 |

CR 11-3 honest-DEFER discipline 67~68번째 epic 연속 정직 회복 결정 wire. 68번째 진입 시점에 grep guard INVERSION 또는 test rename 결정 wire 보존 (OQ-2).

## CR 11-3 honest-DEFER discipline 68번째 epic 연속

A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS) + CR 12-5 D-GATE-01 (Epic 12 2FA 게이트) + D-PARITY-01 inversion (Python FastAPI backend + TypeScript Next.js admin UI parity) 적용 보존 + A19 cohesion 9 surface EXTENSION PASS (IdP admin surface EXTENSION) + CR 0-2 RLS lesson (`tenant_idps` multi-tenant isolation) + CR 1-1 audit-first INSERT (4 NEW audit logs INSERT) + CR 9-6 commit message discipline (`git commit -F <file>`) + CR 11-4 D-001~D-005 + P-015 lessons carry 모두 적용 보존.

## 결정 wire 일자

2026-08-22 (KST)

## next

Epic 16 cj-style 2번째 진입점 (본 스토리) = cj-style 68번째 epic 연속 정직 회복 bmad-create-story spec → `bmad-dev-story epic-16-tenant-idp-admin-wire` T1~T8 atomic wire 진입 (cj-style Epic 16 3번째 진입점 = cj-style 69번째 epic 연속 정직 회복 wire 진입 시점).

Epic 16 close-out retro 진입 결정 wire 보존 (cj-style Epic 16 5번째 진입점 = cj-style 71번째 epic 연속 정직 회복 진입 시점) — A92+A93+A94+A95+A96 정직 검증 + A19 cohesion 9 surface EXTENSION PASS 검증 (IdP admin surface EXTENSION) + D-1-1-DEFER-1/2/3 grep guard 67~68~71번째 epic 연속 정직 회복 검증 결정 wire 보존.

Epic 16 bmad-code-review follow-up sprint 진입 결정 wire 보존 (cj-style Epic 16 4번째 진입점 = cj-style 70번째 epic 연속 정직 회복 진입 시점, 1st release review follow-up sprint precedent mirror).

---

## Review Findings (cj-style 69번째 epic 연속 정직 회복 bmad-code-review — 2026-08-22)

**Review mode**: full | **Diff**: 9 modified + 13 untracked Epic 16 files (~3,315 lines) | **Layers**: Blind Hunter + Edge Case Hunter + Acceptance Auditor (3/3 PASS) | **Total raw findings**: ~100 → **36 unique after dedup**

### patch (24) — to be applied during review follow-up sprint (cj-style 70번째 진입 시점)

- [ ] [Review][Patch] **C2**: sso_login/sso_cs GUC `app.tenant_id` 미설정 — `apps/api/modules/auth/sso/saml_routes.py:88,148` (RLS auto-apply 깨짐 → Epic 15 placeholder fallback → per-tenant routing functionally broken in production)
- [ ] [Review][Patch] **C3**: XXE / billion-laughs DoS — `apps/api/modules/auth/sso/idp_metadata_validator.py:154` (`ET.fromstring` stdlib vulnerable, use `defusedxml.ElementTree.fromstring`)
- [ ] [Review][Patch] **C4**: DELETE audit-first violation — `apps/api/modules/auth/sso/idp_admin_routes.py:555-583` (existence check should be BEFORE `emit_audit_typed`)
- [ ] [Review][Patch] **C5**: TOCTOU race in `create_tenant_idp` — `apps/api/modules/auth/sso/idp_admin_routes.py:708-721` (try/except IntegrityError → typed envelope)
- [ ] [Review][Patch] **H1**: PUT update UNIQUE pre-check missing — `apps/api/modules/auth/sso/idp_admin_routes.py:853-885`
- [ ] [Review][Patch] **H2**: `load_tenant_idp` cross-tenant guard missing — `apps/api/modules/auth/sso/tenant_idp_lookup.py`
- [ ] [Review][Patch] **H3**: DELETE soft-delete blocks re-POST via UNIQUE — `apps/api/modules/auth/sso/idp_admin_routes.py:909` + alembic 0038 (partial UNIQUE on enabled=TRUE)
- [ ] [Review][Patch] **H4**: Soft-delete `ON CONFLICT DO NOTHING` alembic — `apps/api/alembic/versions/0038_epic_16_tenant_idps.py:329` (add `DO UPDATE SET updated_at = NOW()` OR explicit comment)
- [ ] [Review][Patch] **H5**: `sso_login` fallback to real `idp.example.com` leaks tenant_slug — `apps/api/modules/auth/sso/saml_routes.py:94` (404 + typed envelope instead of fallback)
- [ ] [Review][Patch] **H6**: `sso_acs` cross-tenant SAML response bind — `apps/api/modules/auth/sso/tenant_idp_lookup.py:1472` (verify idp_row.tenant_slug == tenant_slug)
- [ ] [Review][Patch] **H7**: `lxml` dependency added but unused — `apps/api/pyproject.toml:247` (remove from `[project.dependencies]`)
- [ ] [Review][Patch] **M1**: Step 8 tenant_slug label-match spoofable — `apps/api/modules/auth/sso/idp_metadata_validator.py:229` (use `entity_host.split(".")[-2]` + case-insensitive)
- [ ] [Review][Patch] **M2**: `create_tenant_idp` returns empty `created_at`/`updated_at` — `apps/api/modules/auth/sso/idp_admin_routes.py:781-782` (add RETURNING)
- [ ] [Review][Patch] **M3**: `_placeholder_acs_host()` silent fallback masks missing ACS URL — `apps/api/modules/auth/sso/idp_admin_routes.py:691,705,821,834` (require acs_url when metadata_xml absent)
- [ ] [Review][Patch] **M4**: `POST /test` synthesized step list lies — `apps/api/modules/auth/sso/idp_admin_routes.py:644-657` (run each step independently with try/except)
- [ ] [Review][Patch] **M6**: Migration `idp_sso_url LIKE 'https://%'` accepts `https://` empty host — `apps/api/alembic/versions/0038_epic_16_tenant_idps.py:230` (add `~ '^https://[^/]+'`)
- [ ] [Review][Patch] **M10**: `OnboardingTooltip.tsx` 3-line removal unrelated to Epic 16 — `apps/web/components/onboarding/OnboardingTooltip.tsx:255-262` (revert, separate cleanup commit)
- [ ] [Review][Patch] **M11**: `middleware.ts` `/onboarding` removed from public routes — `apps/web/lib/auth/middleware.ts` (verify (auth)/onboarding/page.tsx OR revert)
- [ ] [Review][Patch] **M12**: drift detector incomplete — Python only, not markdown — `tests/integration/test_capability_matrix_v1_28_drift.py:2990-3000` (parse markdown table)
- [ ] [Review][Patch] **L1**: XML size unbounded DoS — `apps/api/modules/auth/sso/idp_metadata_validator.py:154` (add `len(metadata_xml) > 1_000_000` check)
- [ ] [Review][Patch] **L2**: X509 cert size unbounded — `apps/api/modules/auth/sso/idp_metadata_validator.py:1277` (base64 decode size check)
- [ ] [Review][Patch] **L3**: Step 5 encryption-only cert accepted — `apps/api/modules/auth/sso/idp_metadata_validator.py:1259` (skip non-signing keys)
- [ ] [Review][Patch] **L5**: Step 8 expected_tenant_slug=None short-circuit — `apps/api/modules/auth/sso/idp_metadata_validator.py:229` (require non-empty)
- [ ] [Review][Patch] **L6-L10**: Various small fixes (whitespace bypass, UUID typing, audit log 500 handling, __all__ pollution, lookup envelope violation)

### defer (7) — to be decided in follow-up sprint

- [x] [Review][Defer] **C1**: T4 frontend territory completely missing — 7 files (page + 4 components + admin-idp-client + ko-KR.json + vitest) — **deferred to T4 follow-up sprint (A104 결정 wire 진입 시점)** — user explicitly approved option (a) at review entry
- [x] [Review][Defer] **H8**: AC7.4 spec file rename — `test_epic_16_saml_routes_extended.py` → `test_epic_16_tenant_idp_lookup.py` — **deferred to spec 회기 update** (similar coverage exists)
- [x] [Review][Defer] **M5**: `audit_action.py` typo risk — **deferred** (CR 1-1 lesson carry, 1차 출시 후 결정)
- [x] [Review][Defer] **M7**: acme seed URL placeholder deviation (`idp.example.com` vs spec `idp.acme.com`) — **deferred** (Epic 15 backward-compat 우선, atomic sprint 한계 인정)
- [x] [Review][Defer] **M8**: `pyproject.toml` vs `requirements.txt` location variance — **deferred/dismissed** (현재 poetry 사용, pyproject.toml 정합)
- [x] [Review][Defer] **M9**: AC7.2 routes test count underrun (19 vs ~25) — **deferred to close-out retro** (A104 결정)
- [x] [Review][Defer] **L11**: `OnboardingTooltip` removed `step_dashboard_title` stale i18n key — **deferred** (P-015 detector sweep)

### dismiss (5) — false positive or handled elsewhere

- [Review][Dismiss] **L4**: Step 8 TLD-1 slug — duplicate of M1 (merged)
- [Review][Dismiss] **M8** partial: `pyproject.toml` not `requirements.txt` — 정합 (poetry 사용)
- [Review][Dismiss] (기타 false positives per step-03 best-effort parsing)
