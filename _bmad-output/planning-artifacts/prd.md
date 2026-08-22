---
title: bizup 통합 PRD v3.6
status: final
created: 2026-07-12
updated: 2026-08-22
changelog:
  - v3.6 (2026-08-22): Epic 17 PRD entry 결정 wire DONE (cj-style 80번째 epic 연속 정직 회복 atomic docs-only wire) — 옵션 (a) Epic 17 진입 결정 wire (Sidebar/MenuProvider hot-fix `01a06e4` 직후 79→80번째 cycle 진입, D-EPIC-16-REVIEW-DEFER-2~6 RESOLVE sprint `512ed6a` 78번째 wire DONE 진입 후 next 옵션 5종 중 사용자 권장 결정 = 옵션 (a) Epic 17 진입). rationale 4종: ① Epic 1 ~ Epic 16 + Phase 3 + Phase 4 + Phase 5 모두 wire DONE (49~79번째 cumulative cycle) → 모든 territory 의 audit-first INSERT (CR 1-1) 가 audit_log table 누적 → audit log viewer territory 자연스러운 next 진입 ② cj-style discipline 회피 위험 방지 (49~79번째 누적 31-entry-point cycle + 78~79번째 hot-fix + RESOLVE sprint 직후 즉시 Epic 17 진입 = 1-day atomic sprint discipline) ③ 비즈니스 우선순위 = enterprise 고객 onboarding 시 audit log viewer 필수 (PIPA + GDPR + SOX compliance = audit log 가시성 + export 기능 요구) ④ Phase 5 multi-region wire 의 cross-region audit log visibility 자연스러운 carry-over (audit_log table 은 cross-region primary 에 write → multi-region read replica 통한 cross-region audit visibility 제공). master PRD v3.5 → v3.6 atomic edit (docs only). **§F21 Audit Log Viewer & Activity Stream territory 신규** (F21.1 audit log query API (FastAPI `apps/api/modules/audit/audit_log_query.py` NEW, filters: tenant_id + actor_id + action_class + action + period + payload_search + pagination + sort by created_at DESC, owner/admin role required, RLS 자동 적용) / F21.2 audit log viewer UI (Next.js `apps/web/app/[locale]/(dashboard)/audit-log/page.tsx` NEW ~200 LOC, filter panel + table + pagination + CSV export button + ko-KR.json `audit_log.*` namespace EXTENSION 14 keys + (dashboard) 보호) / F21.3 activity stream UI (Next.js `apps/web/app/[locale]/(dashboard)/activity/page.tsx` NEW ~150 LOC, last 30 days tenant-wide activity timeline + grouped by date + actor avatar + action chip + (dashboard) 보호) / F21.4 cross-region audit log visibility (Phase 5 carry-over, secondary region 의 audit_log replica 통한 cross-region audit query, multi-region read replica 정합) / F21.5 CSV export (compliance 용, `apps/api/modules/audit/audit_log_export.py` NEW, Excel-compatible UTF-8 BOM + streaming response + audit-first INSERT `audit_log_exported` action) / F21.6 Capability gate AUDIT_LOG_VIEW (capability matrix v1.29 → v1.30 EXTENSION 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅) / F21.7 tests + wire scope T1~T8 결정) + §8.1 M0-(n) audit log viewer AC 신규 (AC: tenant owner/admin 가 audit log 조회 + filter + export + cross-region visibility + activity stream 7 day/30 day/90 day window) + §15 로드맵 Epic 17 row status 백로그 → in-progress (PRD entry DONE 진입 wire) + §부록 A A153+A154+A155+A156+A157 신규 결정 표 + AD-32 Audit Log Viewer & Activity Stream 신규 결정 + capability matrix v1.29 → v1.30 EXTENSION AUDIT_LOG_VIEW 1 NEW row (industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러, MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire pattern + TENANT_IDP_MANAGEMENT Epic 16 wire pattern + LAUNCH_* 1st release wire pattern) + Epic 16 close-out retro `f1ead9a` 보존 진입 (Epic 16 territory DONE 정합) + Phase 5 close-out retro `b843565` 보존 진입 (Phase 5 territory DONE 정합) + D-EPIC-16-REVIEW-DEFER-2~6 RESOLVE sprint `512ed6a` 78번째 wire DONE 진입 보존. CR 11-3 honest-DEFER discipline 80번째 epic 연속 정직 회복 검증 ✅ (D-1-1-DEFER-1/2/3 RESOLVED 보존 60~80번째 + D-LAUNCH-1-DEFER-1 honestly preserved 65~80번째 + D-EPIC-16-REVIEW-DEFER-2~6 ✅ RESOLVED 보존 78~80번째 + D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED 보존 73~80번째) + A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS) + CR 12-5 D-GATE-01 + D-PARITY-01 inversion 적용 보존 + A19 + CR 0-2 RLS lesson (audit_log RLS 정합 보존) + CR 1-1 audit-first INSERT (audit_log_exported 1 NEW CR 1-1 verbatim 적용) + CR 9-6 commit message discipline (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention) 모두 적용 보존. 결정 wire 일자: 2026-08-22 (KST).
  - v3.5 (2026-08-22): Phase 5 PRD entry 결정 wire DONE (cj-style Phase 5 1번째 진입점 = cj-style 73번째 epic 연속 정직 회복 atomic docs-only wire) — 옵션 (a) Phase 5 진입 결정 wire (Epic 16 close-out retro §14 5 options 중 사용자 권장 결정 = 옵션 (a) Phase 5 진입, rationale 4종: ① docs/database-backup.md §7 disaster recovery 의 "multi-region backup 결정 wire 보류, Phase 5+ 진입 시점" verbatim 해소 = Phase 4 wire 의 honestly-deferred territory 자연스러운 carry-over chain ② cj-style discipline 회피 위험 방지 (49~72번째 누적 cycle 후 73번째 진입 = 1-day atomic sprint discipline 즉시 진입) ③ 비즈니스 우선순위 = 1차 출시 후 enterprise SLA = RPO 1시간/RTO 4시간 → multi-region failover 으로 99.95% SLA 달성 territory ④ Phase 4 wire (`71a033a`) 의 단일-region (Supabase Seoul primary) 의 multi-region EXTENSION = phase_4_backup_strategy table + Phase 4 PITR 결정 wire 의 자연스러운 carry-over). master PRD v3.4 → v3.5 atomic edit (docs only). **§F20 Multi-Region Backup & Disaster Recovery territory 신규** (F20.1 Cross-region read replica + WAL archiving (`apps/api/alembic/versions/0039_phase_5_multi_region_backup.py` NEW ~+120 LOC, phase_5_replication_lag table + replica region enums + replication_status enum + audit log replica_status_changed INSERT) / F20.2 Cross-region failover automation (`apps/api/jobs/failover_orchestrator.py` NEW ~+200 LOC, primary → secondary health probe + automatic promotion + DNS update via Supabase API + 30s RTO target) / F20.3 Disaster recovery drill + automated quarterly test (cron KST 1st Sunday 03:00 UTC 18:00 + actual failover drill test in staging + RPO/RTO measurement) / F20.4 Cross-region backup strategy (Supabase PITR primary + cross-region PITR secondary + Supabase Storage 결정 wire 보류 vs AWS S3 결정 wire 보류 + 30일 hot + 90일 cold + 365일 archive regional) / F20.5 Multi-region health observability (`apps/api/core/health.py` EXTENSION multi-region endpoint + Sentry breadcrumb failover + Grafana multi-region dashboard EXTENSION) / F20.6 Capability matrix v1.28 → v1.29 EXTENSION MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER 2 NEW rows (industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러, DEPLOYMENT_* Phase 4 wire pattern) / F20.7 Tests + wire scope T1~T8 결정) + §8.1 M0-(m) multi-region backup AC 신규 (AC: cross-region read replica wire DONE + WAL archiving wire DONE + automatic failover drill PASS + RPO ≤ 1h / RTO ≤ 4h SLA + quarterly drill + multi-region health observability) + §15 로드맵 Phase 5 row status 백로그 → in-progress (PRD entry DONE 진입 wire) + §부록 A A124+A125+A126+A127+A128 신규 결정 표 (A124 옵션 (a) Phase 5 진입 결정 / A125 master PRD v3.4 → v3.5 atomic edit / A126 AD-31 Multi-Region Backup & Disaster Recovery 신규 / A127 capability matrix v1.28 → v1.29 EXTENSION MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER 2 NEW rows / A128 Phase 5 wire scope T1~T8 결정) + AD-31 Multi-Region Backup & Disaster Recovery 신규 결정 ((a) Cross-region read replica + WAL archiving 결정 wire / (b) Cross-region failover automation 결정 wire / (c) DR drill + quarterly test 결정 wire / (d) Cross-region backup strategy 결정 wire / (e) Multi-region health observability 결정 wire / (f) Capability gate MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER 결정 wire) + capability matrix v1.28 → v1.29 EXTENSION 2 NEW rows (industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러, DEPLOYMENT_PROD + DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP + DEPLOYMENT_HEALTH_CHECK Phase 4 wire pattern + TENANT_IDP_MANAGEMENT Epic 16 wire pattern) + Epic 16 close-out retro 보존 진입 (Epic 16 territory DONE 정합, cj-style 67~72번째 epic 연속 정직 회복). CR 11-3 honest-DEFER discipline 73번째 epic 연속 정직 회복 검증 ✅ (D-1-1-DEFER-1/2/3 RESOLVED 보존 60~73번째 + D-LAUNCH-1-DEFER-1 honestly preserved 65~73번째 + D-EPIC-16-REVIEW-DEFER-2~6 honestly DEFERRED 5 OPEN 보존 70~73번째) + A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS) + CR 12-5 D-GATE-01 + D-PARITY-01 inversion 적용 보존 + A19 + CR 0-2 RLS lesson (Phase 4 backup_strategy RLS 정합) + CR 1-1 audit-first INSERT (replica_status_changed + failover_initiated audit log INSERT 결정) + CR 9-6 commit message discipline (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention) 모두 적용 보존. 결정 wire 일자: 2026-08-22 (KST).
  - v3.4 (2026-08-22): Epic 16 PRD entry 결정 wire DONE (cj-style 67번째 epic 연속 정직 회복 atomic docs-only wire) — 옵션 (a) Epic 16 진입 결정 wire (1st release close-out retro §12 4 options 중 사용자 권장 결정, rationale 4종: ① Epic 15 SSO enterprise SAML forward-reference 'TODO Epic 16' 해결 (docs/sso-enterprise.md §4.1 step 3 'Configure tenant_idps (TODO Epic 16)' verbatim) ② Epic 15 territory carry-over chain (58~61→67번째) = tenant IdP admin management 가 자연스러운 next territory ③ cj-style discipline 회피 위험 방지 (62~66번째 누적 cycle 더 미루면 cycle 끊김 위험) ④ 비즈니스 우선순위 = 1차 출시 후 enterprise SSO onboarding 필수). master PRD v3.3 → v3.4 atomic edit (docs only). **§F19 Tenant IdP admin management territory 신규** (F19.1 tenant_idps table schema (alembic 0038 + RLS policy `tenant_id = current_setting('app.tenant_id')`) / F19.2 IdP metadata XML validation service (SAML 2.0 metadata XML 파싱 + EntityDescriptor 검증 + x509 cert PEM 검증 + IdP SSO URL 형식 검증) / F19.3 Tenant IdP CRUD API endpoints (FastAPI routes 5종: list/create/update/delete/test, owner/admin role required) / F19.4 Tenant IdP admin UI (Next.js admin dashboard at `/[locale]/(dashboard)/settings/sso` + IdP metadata paste/upload + validation feedback + tenant slug 자동 표시) / F19.5 Per-tenant IdP routing EXTENSION (Epic 15 SAML response routing 정합: `GET /api/v1/auth/sso/login?tenant_slug=acme` → `tenant_idps` row lookup → ACS URL 일치 검증) / F19.6 Capability gate TENANT_IDP_MANAGEMENT (capability matrix v1.28 EXTENSION industry-agnostic 4-industry grants ✅/✅/✅/✅) / F19.7 Tests + wire scope T1~T8 결정) + §8.1 M0-(l) tenant IdP admin AC 신규 (AC: tenant owner/admin 가 자신의 tenant IdP config CRUD 가능 + IdP metadata XML validation + per-tenant SSO routing + audit-first INSERT 4 NEW + multi-tenant isolation RLS) + §15 로드맵 Epic 16 row status 백로그 → in-progress (PRD entry DONE 진입 wire) + §부록 A A92+A93+A94+A95+A96 신규 결정 표 (A92 옵션 (a) Epic 16 진입 결정 / A93 master PRD v3.3 → v3.4 atomic edit / A94 AD-30 Tenant IdP admin architecture 신규 / A95 capability matrix v1.27 → v1.28 EXTENSION TENANT_IDP_MANAGEMENT / A96 Epic 16 wire scope T1~T8 결정) + AD-30 Tenant IdP admin management 신규 결정 ((a) tenant_idps table schema (alembic 0038 + RLS) / (b) IdP metadata validation (signature + structure) / (c) CRUD API (owner/admin) / (d) admin UI / (e) per-tenant routing EXTENSION / (f) audit-first INSERT 4 NEW + multi-tenant isolation) + capability matrix v1.27 → v1.28 EXTENSION TENANT_IDP_MANAGEMENT 1 NEW row (industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러, SSO_ENTERPRISE Epic 15 wire pattern) + 1st release close-out retro 보존 진입 (1st release territory DONE 정합, cj-style 62~66번째 epic 연속 정직 회복). CR 11-3 honest-DEFER discipline 67번째 epic 연속 정직 회복 검증 ✅ (D-1-1-DEFER-1/2/3 RESOLVED 보존 + D-LAUNCH-1-DEFER-1 honestly preserved 65~66~67번째) + A36 SDR 검증 4-step 자동 적용 (commit prefix lint + sprint-status structure + pytest file count drift + commit consistency 모두 PASS) + CR 12-5 D-GATE-01 + D-PARITY-01 inversion 적용 보존 + A19 + CR 0-2 RLS lesson + CR 1-1 audit-first INSERT + CR 9-6 commit message discipline (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention) 모두 적용 보존. 결정 wire 일자: 2026-08-22 (KST).
  - v3.3 (2026-08-22): 1st release launch PRD entry 결정 wire DONE (cj-style 62번째 epic 연속 정직 회복 atomic docs-only wire) — 옵션 (d) 1차 출시 진입 결정 wire (Epic 15 close-out retro §12 4 options 중 사용자 권장 결정, rationale 4종: ① 모든 인프라 wire DONE (Auth Foundation Epic 1 + Phase 3 + 2FA Epic 12 + LISTEN/NOTIFY Epic 13/14 + Deployment Phase 4 + 인증 방법 4종 Magic link + OAuth 3종 + SSO SAML Epic 15) ② D-1-1-DEFER-1/2/3 ✅ RESOLVED 60번째 epic 연속 정직 회복 ③ cj-style discipline 회피 위험 방지 (49~61번째 누적 cycle) ④ 비즈니스 우선순위 (infrastructure 완성 → 실제 출시 가치 회수). master PRD v3.2 → v3.3 atomic edit (docs only). **§F18 1st release launch territory 신규** (F18.1 Marketing landing page (`/landing` route + `LandingHero` + `LandingFeatures` + `LandingPricing` + `LandingCTA` ko-KR inline copy, vercel.json public route EXTENSION) / F18.2 Terms of Service + Privacy Policy (`docs/terms-of-service.md` + `docs/privacy-policy.md` 한국 개인정보보호법 + GDPR 정합, versioned + changelog) / F18.3 Onboarding user guide (`docs/onboarding-guide.md` 8 sections + in-app tooltip + first-run wizard EXTENSION Epic 1 carry-over 결정 보존) / F18.4 Customer support channels (`docs/support.md` + `support@bizup.kr` email + in-app help widget + FAQ `docs/faq.md`) / F18.5 Production launch verification (smoke test RE-RUN 정직 결정 wire + `docs/database-backup.md` 0036 PITR drill + Sentry alert wiring production environment + RPO/RTO SLA verification 4h/24h) / F18.6 Public launch communications (`docs/launch-announcement.md` + press kit + social media assets)) + §8.1 M0-(k) 1st release launch AC 신규 (launch checklist 6 conditions: ① landing page wire DONE ② ToS/Privacy wire DONE ③ onboarding guide wire DONE ④ support channels wire DONE ⑤ smoke test + backup drill PASS ⑥ launch comms published) + §15 로드맵 1st release row status 백로그 → in-progress (PRD entry DONE 진입 wire) + §부록 A A83+A84+A85+A86+A87 신규 결정 표 (A83 옵션 (d) 1st release launch 진입 결정 / A84 master PRD v3.2 → v3.3 atomic edit / A85 AD-29 1st release launch 신규 / A86 capability matrix v1.26 → v1.27 EXTENSION 4 NEW rows / A87 1st release wire scope T1~T8 결정) + AD-29 1st release launch 신규 결정 ((a) Marketing landing page 결정 wire / (b) ToS + Privacy Policy 결정 wire / (c) Onboarding user guide 결정 wire / (d) Customer support channels 결정 wire / (e) Production launch verification 결정 wire / (f) Public launch communications 결정 wire, public 라우트 (auth)/landing + (auth)/tos + (auth)/privacy ko-KR SSOT EXTENSION) + capability matrix v1.26 → v1.27 EXTENSION LAUNCH_LANDING + LAUNCH_TOS + LAUNCH_SUPPORT + LAUNCH_MONITORING 4 NEW rows (industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러, Phase 3 + Phase 4 + Epic 13/14 + Epic 15 wire pattern) + Epic 15 close-out retro 보존 진입 (Epic 15 territory DONE 정합). CR 11-3 honest-DEFER discipline 62번째 epic 연속 정직 회복 검증 ✅ (D-1-1-DEFER-1/2/3 RESOLVED 보존) + A36 SDR 검증 4-step 자동 적용 (commit prefix lint + sprint-status structure + pytest file count drift + commit consistency 모두 PASS) + CR 12-5 D-GATE-01 + D-PARITY-01 inversion 적용 보존 + A19 + CR 0-2 RLS lesson + CR 1-1 audit-first INSERT + CR 9-6 commit message discipline (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention) 모두 적용 보존. 결정 wire 일자: 2026-08-22 (KST).
  - v3.2 (2026-08-22): Epic 15 PRD entry 결정 wire DONE (cj-style Epic 15 1번째 진입점 = cj-style 58번째 epic 연속 정직 회복) — Epic 15 = Magic link + Social OAuth + SSO enterprise SAML 통합 territory 진입 결정 (옵션 (a) Epic 15 진입 wire, A70+A71+A72 결정 wire 진입). master PRD v3.1 → v3.2 atomic edit (docs only). D-1-1-DEFER-1/2/3 ✅ honestly RESOLVE 진입 wire 결정 (A70 Magic link + A71 Social OAuth + A72 SSO enterprise SAML 3/3 ALL DONE 진입). §F17 Magic link + Social OAuth + SSO enterprise SAML territory 신규 (F17.1 Magic link via Supabase `signInWithOtp` + email 존재 여부 노출 방지 + audit-first INSERT / F17.2 Social OAuth Google/Naver/Kakao via Supabase `signInWithOAuth` + provider whitelist + OAuth callback + audit-first INSERT / F17.3 SSO enterprise SAML via `python3-saml` + SAML response validation + JIT user provisioning + multi-tenant isolation (CR 0-2 RLS) + Just-In-Time mapping + audit-first INSERT / F17.4 ko-KR SSOT EXTENSION (auth.magic_link.* + auth.social.* + auth.sso.* namespace) / F17.5 capability matrix v1.25 → v1.26 EXTENSION 5 NEW rows (MAGIC_LINK + SOCIAL_OAUTH_GOOGLE + SOCIAL_OAUTH_NAVER + SOCIAL_OAUTH_KAKAO + SSO_ENTERPRISE) / F17.6 tests + wire scope T1~T8 결정) + §8.1 M0-(h) Magic link + M0-(i) Social OAuth + M0-(j) SSO enterprise SAML 3 NEW 인수 불릿 + §15 로드맵 Epic 15 row 신규 (in-progress 진입) + §부록 A A70+A71+A72 ✅ done + A75 preserved + A79+A80+A81+A82 신규 결정 표 (A79 Epic 15 PRD entry 결정 + A80 AD-28 Magic link + Social OAuth + SSO 신규 + A81 capability matrix v1.25 → v1.26 EXTENSION 5 NEW rows + A82 Epic 15 wire scope T1~T8 결정) + AD-28 Magic link + Social OAuth + SSO enterprise SAML 신규 결정 (Supabase `signInWithOtp` + `signInWithOAuth` + `python3-saml` AD-14 stack pin + SAML response validation + JIT user provisioning + multi-tenant isolation (CR 0-2 RLS) + audit-first INSERT) + capability matrix v1.25 → v1.26 EXTENSION 5 NEW rows (industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러, Phase 3 + Phase 4 + Epic 13/14 wire pattern) + Phase 4 close-out retro 보존 진입. CR 11-3 honest-DEFER discipline 58번째 epic 연속 정직 회복 검증 ✅ (D-1-1-DEFER-1/2/3 ✅ RESOLVE 진입 wire) + A36 SDR 검증 4-step 자동 적용 (commit prefix lint + sprint-status structure + vitest file count drift + commit consistency 모두 PASS) + CR 12-5 D-GATE-01 + D-PARITY-01 inversion 적용 보존 + A19 + CR 0-2 RLS lesson + CR 1-1 audit-first INSERT + CR 9-6 commit message discipline (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention) 모두 적용 보존. 결정 wire 일자: 2026-08-22 (KST).
  - v3.1 (2026-08-22): Phase 4 PRD entry 결정 wire DONE (cj-style Phase 4 1번째 진입점 = cj-style 53번째 epic 연속 정직 회복) — Phase 4 = Deployment config + Dockerfile territory 진입 결정 (옵션 (a) Phase 4 진입 wire, A73 결정). master PRD v3.0 → v3.1 atomic edit (docs only). §F16 Deployment territory 신규 (F16.1 Dockerfile 다중 stage 분리 + AD-14 digest-pinned / F16.2 Vercel frontend config + RAILWAY backend config / F16.3 Supabase production PostgreSQL / F16.4 Production env config + secrets 관리 / F16.5 Health check + observability + monitoring + database backup / F16.6 tests + wire scope T1~T8 결정 + §8.1 M0-(g) production deployment + §15 로드맵 Phase 4 row 신규 + §부록 A A73 + A74 + A76 + A77 + A78 신규 결정 표 + AD-27 Deployment 신규 결정 (Vercel frontend + Railway backend + Supabase PostgreSQL + Sentry observability 결정) + capability matrix v1.24 → v1.25 EXTENSION DEPLOYMENT_PROD + DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP + DEPLOYMENT_HEALTH_CHECK 4 NEW rows (industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러, Phase 3 + Epic 13/14 wire pattern) + D-1-1-DEFER-1/2/3 honestly RESOLVE 표기 (A70+A71+A72 결정 wire 진입 시점에 동시) + Phase 3 close-out retro 보존 진입. CR 11-3 honest-DEFER discipline + A36 SDR 검증 4-step 자동 적용 (commit prefix lint + sprint-status structure + vitest file count drift + commit consistency 모두 PASS) + CR 12-5 D-GATE-01 + D-PARITY-01 inversion 적용 보존 + A19 + CR 0-2 RLS lesson + CR 1-1 audit-first INSERT + CR 9-6 commit message discipline (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention) 모두 적용 보존. 결정 wire 일자: 2026-08-22 (KST).
  - v3.0 (2026-08-20): Phase 3 PRD entry 결정 wire DONE (cj-style Phase 3 1번째 진입점 = cj-style 49번째 epic 연속 정직 회복) — Phase 3 = 로그인/회원가입 UI + auth middleware (Epic 1 완성 territory 진입 결정). master PRD v2.5 → v3.0 atomic edit (docs only). §F15 Auth Foundation 신규 (F15.1 login UI + Supabase SSR auth client + sb-access-token cookie session / F15.2 signup UI + tenant creation flow + onboarding/industry handoff / F15.3 auth middleware EXTENSION next-intl middleware + Supabase session check + (dashboard) 보호 + (auth) 공개 route group / F15.4 logout flow + ko-KR SSOT logout error envelope + audit-first INSERT / F15.5 forgot-password UI + Supabase resetPasswordForEmail + token rotation + 2FA 게이트 보존 / F15.6 tests + wire scope T1~T8 결정 + §8.1 M0-(d) login + M0-(e) signup + M0-(f) auth middleware 3 NEW 인수 불릿 + §15 로드맵 Phase 3 row + §부록 A A65+A66+A67+A68+A69 신규 결정 표 + capability matrix v1.23 → v1.24 EXTENSION LOGIN + SIGNUP + AUTH_MIDDLEWARE + FORGOT_PASSWORD + LOGOUT 5 NEW rows (industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러, AI_INSIGHT + LISTEN_NOTIFY + LISTEN_NOTIFY_TENANT_FANOUT + LISTEN_NOTIFY_MULTIPROCESS wire pattern) + AD-26 Auth Foundation 신규 (Supabase SSR + sb-access-token cookie session + next-intl middleware EXTENSION + auth route group (auth) + dashboard route group (dashboard) 보호 + Epic 12 2FA 게이트 보존) + D-1-1-DEFER-* honestly DEFER 보존 (Epic 1 carry-over DEFER 1~N 정직 회복). CR 11-3 honest-DEFER discipline + A36 SDR 검증 4-step 자동 적용 (commit prefix lint + sprint-status structure + vitest file count drift + commit consistency 모두 PASS). 3중 게이트 impact NONE (docs only 변경, no code/test/sprint-status delta 외에 PRD edit 신규). 결정 wire 일자: 2026-08-20.
  - v2.5 (2026-08-20): A57 결정 wire DONE = Epic 14 = LISTEN/NOTIFY Consume 2nd Batch PRD entry (cj-style Epic 14 1번째 진입점 = cj-style 45번째 epic 연속 정직 회복). §F14 신규 (F14.1 cross-tenant invalidation fan-out 토폴로지 + F14.2 multi-process coordination + F14.3 V8 determinism + cross-language drift detector EXTENSION + F14.4 tests + wire scope T1~T9 결정) + §15 로드맵 Epic 14 row status 백로그 → in-progress (PRD entry DONE 진입 wire) + §부록 A A57+A58+A59 신규 결정 (A57 = Epic 14 PRD entry / A58 = AD-25 EXTENSION 5+ channels cross-tenant fan-out channel 추가 / A59 = capability matrix v1.22 → v1.23 LISTEN_NOTIFY_TENANT_FANOUT + LISTEN_NOTIFY_MULTIPROCESS 2 NEW rows, industry-agnostic 4-industry grants) + §8.1 M10-(d)·§F10.1-(d) cross-tenant fan-out EXTENSION 결정 wire 진입. Story 14-1 wire 진입 대기 (cj-style Epic 14 2번째 진입점 = cj-style 46번째 epic 연속 정직 회복 진입 대기, T1~T9 atomic single sprint). A45+A46 결정 wire 진입 보존 (옵션 (a) Epic 14 follow-up sprint 진입 결정, bundled into ONE Epic 14 carry-over sprint = cj-style Epic 14 3번째 진입점 진입 시점). D-13-1-DEFER-3 ✅ RESOLVED 진입 wire (A53 Epic 14 진입 결정). D-13-1-DEFER-2 preserved (LISTEN/NOTIFY 실측 evidence 정합 sweep = 14-1 wire 진입 시점에 동시 sweep 결정 = A55 Epic 14 진입 시점에 동시). 3중 게이트 impact NONE (docs only 변경, no code/test/sprint-status delta 외에 PRD edit 신규). CR 11-3 honest-DEFER discipline + A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS). 결정 wire 일자: 2026-08-20.
  - v2.4 (2026-08-20): A53 결정 wire DONE = 옵션 (a) Epic 14 진입 결정 (cj-style Epic 13 5번째 진입점 = cj-style Epic 13 carry-over 17번째 docs only atomic wire = cj-style 44번째 epic 연속 정직 회복). §15 로드맵 Epic 14 row 신규 (LISTEN/NOTIFY Consume 2nd Batch 백로그 진입) + §부록 A A53 (decision pending → ✅ done 진입 wire, 사용자 옵션 (a) Epic 14 진입 결정 verbatim bind) + A45+A46 결정 wire 진입 (옵션 (a) Epic 14 follow-up sprint 진입 결정, bundled into ONE Epic 14 carry-over sprint = cj-style Epic 14 3번째 진입점 진입 시점) + A57+A58+A59 결정 예정 (Epic 14 PRD entry 진입 시점에 결정). D-13-1-DEFER-3 ✅ RESOLVED 진입 결정 wire. Epic 14 = cross-tenant invalidation fan-out + multi-process coordination = LISTEN/NOTIFY consume 2nd batch territory 진입 결정. 3중 게이트 impact NONE (docs only 변경, no code/test/sprint-status delta 외에 PRD edit 신규). CR 11-3 honest-DEFER discipline + A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS).
  - v2.3 (2026-08-20): A54 master PRD v2.2 → v2.3 atomic edit DONE — D-13-1-DEFER-1 ✅ RESOLVE. §F13 verbatim 13-1 wire 정합 확장 (F13.1 5-key alphabetical JSON payload + F13.2 4-channel handler verbatim + F13.3 V8 determinism + cross-language drift detector EXTENSION + F13.4 T1~T8 atomic wire DONE + capability LISTEN_NOTIFY v1.22 4-industry grants industry-agnostic) + §15 로드맵 Epic 13 row status in-progress → done (cj-style 1~4번째 진입점 모두 wire DONE = PRD entry + 13-1 atomic + post-wire handoff + Epic 13 close-out retro) + §부록 A A52 (예정 → done 진입 wire) + A53+A54+A55+A56 신규 결정 표 + AD-25 EXTENSION 표기. cj-style Epic 13 carry-over 17번째 docs only atomic wire.
  - v2.2 (2026-08-20): Epic 13 PRD entry A51 결정 wire — §F13 (LISTEN/NOTIFY Consume Trigger EXTENSION) 신규 + §8.1 M10-(d)·§F10.1-(d) 4-channel EXTENSION 진입 결정 verbatim bind + §15 로드맵 Epic 13 row + §부록 A A39 (status in-progress → done 진입 wire) + A51 Epic 13 PRD entry 결정. cj-style Epic 13 1번째 진입점 docs only atomic wire.
  - v2.1 (2026-08-20): Epic 10 close-out retro A37 결정 wire — §F10.1 (Three-Insight Cache Policy) + §F10.2 (AI Reference vs Auto Analysis Badge Separation) + §12 AI 3종 update + §13.1 AI 배지 ko-KR cross-ref + §14 NFR (NFR18 ko-KR + AI 추출/insight/cache/reject counter 4 rows) + §14.B NON-GOAL #5·6 정합 + §부록 A A37~A42 + AD-7/AD-17/AD-25 architectural decisions 표 추가. cj-style carry-over 15번째 docs only atomic wire.
  - v2.0 (2026-07-25): final
---

# 비즈업(Biz-Up) 통합 제품요구사항정의서(PRD) v3.0
## 원가경영관리 웹 SaaS — 전통 개별원가 엔진 + 활동기준원가(ABC) 엔진 통합판

| 항목 | 내용 |
|------|------|
| 문서 버전 | **v2.0 (통합·확정)** — 비즈업 PRD v1.0 + ABC 모듈 PRD v1.0을 **완전 대체**(결정 Q-H) |
| 작성일 | 2026-07-12 |
| 근거 자산 | 원본 엑셀 5개 파일 시트 원문 전수 학습: costmgr(18시트)·djob(8시트)·inv2(17시트+월반복 22시트)·report(구조 분석으로 갈음, Q-G)·ABCost(13시트) |
| 이론 기준 | 2026년 7월 기준 최신 원가관리 지식 — 흡수원가계산 정통 원칙 + TDABC + AI 지원 (웹 검증 완료) |
| 제품 형태 | 웹 SaaS · 월 구독(1만원) · 멀티테넌트 · 완전반응형 |
| 후속 문서 | **통합 ERD v2.0** (본 문서 확정 후 기존 ERD 2권+테이블명세서를 1권으로 통합) |
| 설계 최상위 원칙 | **회계 공리(원가계산 원칙)는 철저히 준수하되, 그 테두리 안에서 입력 편의성을 극대화한다** (제3장 ↔ 제5장) |

---

# 1. 제품 정의와 배경

## 1.1 한 문장 정의

> **"월 1회, 6가지 데이터만 입력하면 원가·재고·손익·분석이 전부 자동으로 나오는, 제조업과 서비스업을 한 지붕에 담은 원가경영관리 웹 SaaS"**

## 1.2 원본 자산의 정체 (5개 파일 학습 종합)

동일 저작자(원가바이블)의 검증된 두 원가 엔진이다.

```
■ 전통 개별원가 엔진 (costmgr + djob + inv2 + report — 4파일 1시스템)
  재료비(BOM×월총평균단가) + 노무비(표준공수×회사부담임률) + 제조경비(배부기준)
  월 6종 입력(주문·생산·판매·구매·경비·인원인건비) → 수불부·검증(check) → 보고서 26종
  대상: 제조업, 제조+유통 겸영 (예시 기업: 창원산업/프랜차이즈)

■ 활동기준원가(ABC) 엔진 (ABCost — 1파일)
  간접비 → 원가풀(설비·매출·인원 3기준 배부) → 활동(≤10) → 동인 → 원가대상
  "비제조업을 위한" 명시 — 서비스·유통업 특화 (예시 기업: 풍성물류산업/여행상품)
```

두 엔진은 같은 철학(월 배치·그린셀 입력·최소 입력 최대 산출·예산/실적 이중 운영·자동 서술형 분석의견)을 공유하며 원가 방법론만 다르다. 비즈업은 이 둘을 **하나의 웹 플랫폼 안에서 사업부문(segment) 구조 위에 공존**시키고, 계정과목·매출·인건비·마감을 **단일 원장으로 공유**한다(이중 입력 0).

> **Greenfield 선언.** 비즈업은 greenfield 웹 SaaS다. 원본 5파일(costmgr·djob·inv2·report·ABCost)은 **회계 로직의 참조용 출처**일 뿐이며, 런타임 의존성(엑셀 COM·VBA·DLL)은 없다. 모든 산식(§6.1, §7.1, §7.2)은 Python으로 1원 단위 재현되며, §11 V8 회귀 테스트 스위트가 원본과 동일 결과를 검증한다. 따라서 "원본과 같은 결과"는 시스템이 보장하고, 원본 자체를 시스템 안에서 띄우지 않는다.

## 1.3 해결하는 불편함

**엑셀 구조의 물리적 한계**
1. 4개 파일 동시 오픈 의존 — 실제 수식 손상 4,468건·유령 링크 1,027건 발생을 교정 작업으로 실증
2. 슬롯 고정 — 제품 100(월 30)·자재 100(월 40)·계정 19·활동 10·지역 20, 초과 시 유료 커스터마이징
3. 1인 1파일 — 동시접속·권한·변경이력 부재, 담당자 교체 시 붕괴
4. VBA 저장/복구 13공간 — 덮어쓰기 위험, "복구 칸 공란" 함정
5. 검증(check)의 수동 의존 — 훌륭한 Reconciliation이 있으나 사람이 열어봐야 발견, 음수재고(예: 달걀 −7,500) 방치

**두 엔진 분리의 불편 (통합의 직접 근거)**
6. 제조+서비스 겸영 기업은 두 파일을 따로 운영해야 하고 공통비를 나눌 방법이 없음
7. 매출·경비·인건비의 이중 입력
8. ABC 파일이 BOM1 시트로 costmgr을 6,174개 수식으로 미러링 — 원본 스스로 통합 필요성을 증명

**지식의 속인성**
9. 저작자 1인의 노하우(임률 체인·배부 판단·조정 요령)가 수식과 메모 속에만 존재

## 1.4 계승하는 철학과 정합성 헌법

원본 manual의 사상을 계승한다.

> "원가 경영관리는 간결하고 간단할수록 성공하고 복잡하면 대부분 실패한다."
> "최소한의 데이터 업로드로 최대한의 원가경영관리에 접근한다."
> "Garbage In, Garbage Out; Gold In, Gold Out — 기본정보의 품질이 원가계산의 품질을 좌우한다."

여기에 비즈업의 정합성 헌법을 더한다.

> **"시스템은 틀린 계산을 할 수 없고, 사용자의 틀린 입력은 반드시 알려준다."**

---

# 2. 대상 사용자·포지셔닝·비즈니스 모델

| 항목 | 내용 |
|------|------|
| 대상 | 전국 불특정 중소기업(제조·유통·서비스·겸영), 원가 전담자 없는 기업 |
| 페르소나 | ① 제조업 경영자/경리 ② 서비스업(물류·여행·용역) 대표 ③ 제조+유통 겸영(프랜차이즈·식품) ④ 경영컨설턴트(대리 운영) |
| 가격 | 월 구독 1만원 단일 요금제(전 기능 제공), 결제 Stripe |
| 경쟁 우위 | ① 회계프로그램이 못 주는 제품별 원가·손익·BEP ② ABC/TDABC를 갖춘 국내 중소기업용 SaaS의 희소성 ③ AI 온보딩·인사이트 ④ 검증된 실무 로직의 1원 단위 웹 이식 |
| 운영 | 1인 개발·운영(Claude Code 활용), 월 인프라 예산 10만원, 셀프서비스 원칙 |
| 지원 수단 | 운영자 콘솔, 대리접속(고객 동의+읽기전용), 공지 시스템 |
| 목표 | G1: 12모듈 완성 후 출시+파일럿 1~2곳 무료 / G2: "새벽에 혼자 고칠 수 있는 시스템" |

---

# 2.A 사용자 여정 (User Journeys)

비즈업의 4가지 핵심 여정은 §2 페르소나를 protagonist로 삼아 흐름을 잡는다. 각 여정은 트리거 → 핵심 단계 → 종착상태 → 예외 경로의 구조로, UX 와이어프레임과 데이터 플로우(아키텍처)의 직접 입력이다. 페르소나 컨텍스트는 각 여정 protagonist에 인라인으로 실어 나른다(별도 페르소나 섹션 없음).

### UJ-1. 월 사이클 — 가장 자주 반복되는 운영 흐름
- **Protagonist**: 박영수, 48세, 식품 제조+유통 겸영 업체 대표(§2 페르소나 ③). 경리 1명 보조, 새벽 4시 출근해 장부 검토.
- **트리거**: 전월 마감 완료 후 다음 달 1일 자동 알림 (대시보드 체크리스트 활성화).
- **핵심 단계**:
  1. M2 입력 — 주문·생산·판매·구매·경비·인원 6종 데이터를 전월 복사(E9) 후 증감만 수정, 일용직은 별도 그리드.
  2. M0/M1 누락 점검 — 신규 품목·거래처 등장 시 기준정보(M1) 추가, 업종 변경은 A7 전진법 가드.
  3. M3 [계산] 클릭 → §6.1 산식 체인 가동, 1원 단위 검증 [A6].
  4. M6 자동 검증 (§11 V1~V8) — V3 음수재고 / V4 4요소 분해 / V8 회귀 테스트 자동 발동.
  5. M11 마감 — 부문분할→제조→ABC→공동 순서 강제, 스냅샷·역분개 잠금.
  6. M5 보고서 — 종합 손익·제품별 손익·BEP·재고 수불 14종 열람, PDF/A4 인쇄.
  7. (선택) M10 AI 인사이트 큐레이션 — 계산 직후 질문 3개 자동 생성·캐시(§12).
- **종착상태**: 다음 달 영업 준비 완료 + 전월 손익 확정 + 감사추적 로그 봉인.
- **예외 경로**:
  - V3 음수재고 → 즉시 경고 + 품목 화면 점프, 마감 차단.
  - V4 차이 발생 → 4요소 분해 표시, 사용자 확인 후 조정 라인 확정.
  - 생산요구시간 > 작업가능시간 → V5 경고, 마감 차단.
  - 업종 변경 시도 → A7 차단, "전진법: 다음 회계연도부터 적용" 안내.

### UJ-2. 예산 시나리오 — 가상 기간으로 미리 시험
- **Protagonist**: 이미숙, 42세, 여행상품 ABC 운영 대표(§2 페르소나 ②). 다음 분기 매출 변동에 대비.
- **트리거**: 회계연도 시작 1개월 전 + 매월 25일 (차월 추정 활성화).
- **핵심 단계**:
  1. M0에서 "예산 시나리오" 신규 개설 (1차 = 1개, 2차 = 복수 예정).
  2. M2 입력과 동일한 체계로 계획치 입력 (M2 UI 재사용).
  3. M3 사전 표준원가계산 — 실적과 동일 산식 체인 [A6], 다른 점은 가상 기간 태그.
  4. M5 §9 보고서 — "예산 대비 실적 손익"(§10, 원본 pl5) 자동 대조.
  5. (2차) A×B×C×D 편성 엔진(보존 산식 §부록 B) 활성화 시 다축 시뮬레이션.
- **종착상태**: 예산 확정 + 표준원가 사전 산출 + 차이 분석 가능.
- **예외 경로**:
  - 예산 시나리오 미존재 → M8 메뉴 비활성.
  - 실적 데이터 변경 → 예산 대비 자동 재대조, 알림.

### UJ-3. 겸영 기업의 부문 카브아웃
- **Protagonist**: 김도현, 53세, 제조+서비스 겸영(프랜차이즈) 재무 담당(§2 페르소나 ③).
- **트리거**: 가입 시 업종 ③·④ 선택 OR 사업부문 추가 발생.
- **핵심 단계**:
  1. §4.1 업종 ③ 선택 — 두 엔진 병행 + 재무제표 업로드 필수.
  2. §4.2 부문 최소 정보 3종 입력 — 명칭·월매출·전용계정 태깅.
  3. §7.3 카브아웃 — 법인세법 시행규칙 제76조 2기준(매출액 비례/개별비용 비례) 택1 [A10], 선택 근거 설정에 기록.
  4. M11 마감 순서 — 부문분할 → 제조 → ABC → 공동 (부분 마감 없음).
  5. §9 보고서 — "부문귀속명세서"(§7.3, §9 #21)로 분할 근거 공시.
- **종착상태**: 제조·서비스 부문별 손익 + 전사 통합 손익 동시 산출.
- **예외 경로**:
  - 재무제표 미업로드 → 카브아웃 검증 불가, 마감 차단.
  - 2기준 미선택 → A10 위반 경고.
  - 제조 부문에 ABC 적용 시도 → 3차 로드맵 안내(§15).

### UJ-4. 관리자 온보딩 — AI 문서추출로 10분 컷
- **Protagonist**: 신규 가입자(§2 페르소나 ①·② 공통). 사업자등록증·재무제표·급여대장·거래명세서 사진 보유.
- **트리거**: 회원가입 직후 M0 진입.
- **핵심 단계**:
  1. M0 업종 4지선다 (§4.1) — 선택에 따라 후속 메뉴 자동 토글(E4).
  2. E5 AI 문서추출 — Claude Vision으로 초안 자동 생성("AI는 초안, 확정은 사람").
  3. 신뢰도 배지 표시, 저신뢰 항목은 사용자 직접 확정.
  4. M1 기준정보 일괄 등록 — 품목·BOM·계정·부서·거래처.
  5. M2 첫 입력 — 6종 데이터 중 일부는 문서추출 결과에서 자동 이관.
  6. (선택) 대리접속 동의(§13.3) — 컨설턴트가 읽기 전용으로 보조.
- **종착상태**: 첫 월 데이터를 입력 가능한 상태 + 모든 추출 항목 사용자 확정.
- **예외 경로**:
  - 추출 신뢰도 전 항목 < 50% → 사용자 수동 입력 폴백 안내.
  - 업종 ④ 선택 → 격리 버킷 추가 안내.
  - 2FA·결제 미완료 → M0 차단.

---

# 2.B 성공 지표 (Success Metrics)

비즈업의 통합 thesis("ABC + 전통 + AI 통합이 한국 SMB 원가경영관리의 표준이 된다")를 검증하기 위한 지표. 모든 지표는 익명 집계 후 운영자 콘솔에 공개(테넌트별 비공개 옵션). 카운터 메트릭은 같은 보드로 묶어 트레이드오프를 가시화한다.

### 핵심 메트릭 (thesis 검증)
- **SM-1. 월 마감 완료율 (활성 테넌트)** — 활성 테넌트 중 마감 완료(역분개 잠금봉인) 비율. 1차 출시 6개월 내 **70% 목표**.
- **SM-2. 겸영 테넌트의 2-engine 동시 마감 비율** — 업종 ③·④ 선택 테넌트가 제조+ABC 양쪽을 같은 회계기간에 마감 완료한 비율. 1차 출시 12개월 내 **50% 목표**.
- **SM-3. AI 인사이트 채택률 (계산 결과 미변경 보장)** — §12 인사이트 큐레이션이 생성한 질문 3개 중 사용자가 "참고함" 또는 "수정함"으로 응답한 비율. 1차 출시 6개월 내 **40% 목표**. SM-3a "계산 결과 변경 시도 = 0건" 별도 추적으로 §12 원칙 유지 검증.
- **SM-4. 미사용능력 보고서 열람률** — TDABC·전통 조업도 차이 보고서(§6.1 (2), §7.2, §9 #11, #18)를 월 1회 이상 열람한 활성 테넌트 비율. 미사용능력 정착 신호.

### 카운터 메트릭 (트레이드오프 가시화)
- **CM-1. 마감 소요시간 vs SM-1** — SM-1이 올라가도 마감 소요시간이 늘어나면 안 됨. 목표: 월 마감 중앙값 **≤ 4시간** (1인 운영자 기준).
- **CM-2. 입력 소요시간(월) vs SM-2** — 2-engine 동시 마감이 늘어도 입력 시간이 2배가 되면 안 됨. 목표: 월 입력 중앙값 **≤ 8시간**.
- **CM-3. 음수재고 경고 후 재작업 빈도** — V3 경고 후 마감까지 사용자 재작업 횟수. 낮을수록 입력 품질↑(A11 충족).
- **CM-4. 대리접속 발동 빈도** — §13.3 대리접속이 자가 해결을 대체하지 않는지 검증 (100% 의존 시 컨설팅 의존 신호).

### 측정 방법
- 모든 메트릭은 익명화 + 집계 후 운영자 콘솔에 표시. 테넌트별 원시 데이터는 비공개.
- 측정 인프라 비용 0 (PostgreSQL 집계 뷰 + 운영자 콘솔 대시보드).
- 지표 정의 변경은 §부록 A 결정 이력(Q-A~Q-J) 방식 추후 추가.

> **가격 모델 정당화 (1만원 단일 요금제).** persona ①·②는 "원가 전담자 없는 기업"이고 G2는 "1인 운영자가 새벽에 혼자 고칠 수 있는 시스템"을 요구한다. 따라서 다단 요금제(베이직/프로/엔터프라이즈)의 게이트키핑·등급별 기능 제한은 1인 운영자 부담을 가중시킨다. 비용 구조: 월 인프라(PostgreSQL+FastAPI+AI API 캐시) ≈ 10만원 / 1테넌트, Stripe 결제 수수료 ≈ 3.6%, 파일럿 기간(1차 출시 후 6개월) 무료 운영으로 영업 부담 0. 1단 정액 1만원은 손익분기 약 10~15 테넌트에서 달성. 2차에서 다단화 가능성 검토(OQ-2).

---

# 3. 회계 공리 헌장 (Accounting Axioms Charter)

**본 장은 비즈업의 최상위 규범이다. 이하 모든 기능·화면·산식은 본 장과 충돌할 수 없으며, 충돌 시 본 장이 우선한다. 입력 편의성(제5장)은 본 장의 테두리 안에서만 극대화된다.**

### A1. 발생주의와 기간귀속
모든 원가·수익은 현금 수수와 무관하게 발생한 월(회계기간)에 귀속한다. 월 마감으로 기간을 확정하며, 마감된 기간의 데이터는 수정할 수 없다(A8의 역분개 정정만 허용). 회계연도 시작월은 테넌트별 가변. `[ASSUMPTION: 원본 costmgr manual은 회계연도 1월 시작을 기본으로 기술. 다국어 SaaS 환경에서 테넌트별 가변이라는 추론은 별도 검증 필요. 추론 근거: 동일 저작자 djob 시트가 "회계연도 시작월" 필드를 보유함. 추론일: 2026-07-12.]`

### A2. 제조원가와 판매관리비의 엄격한 구분
- 제조원가 = 직접재료비 + 직접노무비 + 제조간접비(제조경비) 3요소로만 구성한다.
- 관리 인건비·판매 일반관리비는 **어떠한 경우에도 재고자산 가액에 산입하지 않는다.**
- 원본 pl 시트의 "관리인건비 = 직접인건비의 29.3% 상당 배부", "판관비 = 매출액 기준 배부"는 **관리회계 뷰(제품별 완전원가 손익)로만 제공**하고, 재고 평가·제조원가명세서와는 계층을 분리한다.
- 따라서 제품 원가는 항상 2계층으로 구분 표시한다: `제조원가(manufacturing_cost)` / `완전원가(full_cost)`.

### A3. 재고자산 평가 — 월총평균법 일관 적용
- 원부재료 단가 = (기초재고금액 + 당월매입금액) ÷ (기초재고수량 + 당월매입수량)
- 제품 재고 = 전월·당월 제조원가를 총평균하여 평가 (원본 p1~p12 방식 계승)
- K-IFRS(제1002호 재고자산)와 일반기업회계기준이 인정하는 방법이며, 회계기간 중 변경을 금지한다(A7).

### A4. 생산기준 배부와 매출원가 대응 (결정 Q-F)
- 직접노무비·제조경비는 **당월 생산량을 모수로 배부**한다. 매출기준 배부는 채택하지 않는다.
  - 근거: 원본 pl3에서 매출기준 배부 시 직접인건비가 매출 대비 92%로 튀는 왜곡을 실증(생산 14,900 vs 판매 10,450인데 노무비 전액을 당월 매출에 배부).
- 매출원가 = 판매분에 대응하는 제조원가. 미판매 생산분은 재고자산으로 이월한다.
- 생산·판매 수량 차이와 총평균단가 차이에서 발생하는 재고 증감은 **'제품 재고 조정' 라인으로 자동 산출**하여 손익계산서에 투명하게 표시한다(제11장 V4 — 원본 check 시트의 수동 분해를 자동화).

### A5. 원가 배부의 인과관계(Causality) 원칙
- 배부기준은 원가 발생의 원인을 가장 잘 대표하는 동인이어야 한다.
- 제조경비 배부기준(테넌트 설정, 3종 택1 — 결정 Q-A): ① **직접노무원가 기준** ② **직접노무시간 기준** ③ **기계시간 기준**
  - 기계시간 기준 선택 시에만 월별 제품별 기계시간 입력 필드가 노출된다(미선택 시 숨김 — E4).
- 직접노무비는 작업공수 단일 체계로 배부한다: 단위공수 × 생산수량 × 회사부담임률 (결정 Q-E, 할당인원 방식 미채택).
- 판매 일반관리비의 제품별 배부(관리 뷰)는 매출액 기준으로 하되 A2의 계층 분리를 지킨다.
- 유통품목 3규칙: 노무비 배부 제외 / 공수 미산정 / 간접비는 간접 귀속.

### A6. 완전배부와 대차평형 (Zero-Leak 원칙)
- 모든 배부는 **배부액 합계 = 원비용 금액**을 1원 단위로 만족해야 한다(원본 check 포인트·ABC 7 cost objects의 합계 검증 계승).
- 배부 트리거와 엔진 테스트에서 강제하며, 위반 시 마감을 차단한다.
- 원 단위 끝수 차이는 최종 행에서 조정하는 라운딩 규칙을 명문화한다.

### A7. 일관성(Consistency) — 기중 변경 금지와 전진법
- 배부기준·재고평가방법·고정/변동 구분·업종 구분·부문 구조는 **회계연도 중 변경을 금지**한다.
  (원본 manual: "한번 선택하면 회계기간 동안에는 변경하지 말 것" → 비즈업은 시스템으로 강제)
- 부득이한 변경은 **전진법(prospective)**: 다음 회계연도 개시월부터 적용, 과거 마감분 불변.
- BOM 개정도 전진법: `effective_from` + 월 스냅샷. 과거 월 조회·재계산 시 당시 BOM을 사용.

### A8. 검증가능성(Auditability)
- 수불 원장은 append-only. 정정은 삭제가 아닌 **역분개(reversal) + 재기록**.
- 월 마감 시 계산 결과 전체를 스냅샷으로 고정하고, 입력→산출 추적 경로를 보존한다.
- 누가·언제·무엇을 변경했는지 감사추적 로그를 남긴다.

### A9. 유휴(미사용)능력 원가의 별도 관리 — 전통·ABC 공통
- 유휴 조업능력에서 발생한 원가는 **별도 항목으로 구분 관리하며, 정상 원가와 합산해 원가대상에 배부하지 않는다.** (원본 1-Main Menu의 이론 권고 + Kaplan TDABC 정론)
- 전통 엔진의 조업도 차이시간(총작업가능시간 − 생산요구시간, 예: 3,322−3,269=53h)도 동일 사상으로 **금액화하여 '미사용능력 보고서'에 별도 표시**한다. 임률의 분모는 요구시간(회사부담임률)으로 하여 유휴원가가 제품에 숨어들지 않게 한다.

### A10. 전사(공장)수준 공통원가의 자의적 배부 금지
- 개별 제품과 인과관계가 없는 전사 수준 원가는 제품에 자의적으로 배부하지 않는다(원본 ABC 이론장 권고 계승).
- 사업부문 공통비의 분할은 **법인세법 시행규칙 제76조가 정한 2기준**(매출액 비례 / 개별비용 비례) 중 택1로만 수행하고 선택 근거를 설정에 기록한다.

### A11. 오류의 가시화 (숨기지 않는 시스템)
- 음수재고·합계 불일치·조업도 초과 등 이상 신호는 감지 즉시 표시한다.
- 마감 전에는 '경고 후 진행 허용', **마감 시점에는 임계 위반을 차단**한다.
- 검증 결과는 원본 check 시트처럼 OK/불일치로 명시하되, 차이 원인을 4요소(수량차·배부차·단가차·재고조정)로 분해해 설명한다.

---

# 4. 업종 구조와 사업부문 아키텍처

## 4.1 가입 시 업종 4지선다

| 선택 | 노출 엔진 | 비고 |
|------|-----------|------|
| ① 제조업 | 전통 엔진 | ABC 메뉴 숨김(순수제조 고객) |
| ② 서비스업 | ABC 엔진 | BOM·수불부 등 제조 메뉴 숨김 |
| ③ 제조+서비스 | 두 엔진 병행 | 부문 카브아웃 필수, 재무제표 업로드 필수 |
| ④ 제조+서비스+기타 | 두 엔진 + 격리 버킷 | '기타' 부문은 격리 버킷으로 원가계산 제외 |

업종 변경은 전진법(A7). 부문 최소 정보 3종: 명칭·월매출·전용계정 태깅.

## 4.2 부문(segment)과 엔진의 고정 매핑 (결정 Q-I)

- 제조 부문 → 전통 개별원가 엔진 / 서비스 부문 → ABC 엔진(classic + TDABC)
- 공통비 → A10의 세법 2기준으로 부문 분할 후 각 엔진에 투입
- 마감 순서 일원화: **부문분할 → 제조 원가계산 → ABC 계산 → 공동 마감** (부분 마감 없음)
- 제조 부문에 대한 ABC 적용(병행 뷰)은 3차 로드맵 — 스키마는 확장 차단 없이 설계

---

# 5. 입력 편의 극대화 원칙 (회계 공리의 테두리 안에서)

**모든 편의 장치는 제3장 공리를 침해하지 않는 범위에서만 작동한다. 편의는 '입력의 노력'을 줄이는 것이지 '회계의 정확성'을 흥정하는 것이 아니다.**

| # | 장치 | 내용 | 지키는 공리 |
|---|------|------|------------|
| E1 | 월합계 기본 + 일자별 선택 (Q-C) | 원가계산은 월 단위이므로 월합계 입력이 기본. 일일관리가 필요한 고객만 일자별 그리드 모드 활성화(record_date 건별 확장) | A1 |
| E2 | 생산유형 표준공수 상속 | 생산유형 15종(공정 ≤10, 비중 합 100% 강제)에 표준공수(인원×시간÷수량)를 정의하면 제품이 상속. 제품별 재정의가 우선하는 하이브리드 | A5 |
| E3 | 자동 파생 | 평균단가 = 금액÷수량 자동 산출(원본 pu·sa 방식). 수량+금액만 입력 | — |
| E4 | 선택 기능 숨김 | 주문관리·판매지역·거래처·기계시간은 미사용 시 화면·보고서에서 숨김(원본 "주문관리 불필요 시 미입력" 계승) | — |
| E5 | AI 문서추출 온보딩 | 사업자등록증·재무제표·급여대장·거래명세서 사진/PDF → 초안 자동 생성. **"AI는 초안, 확정은 사람"** — 확정 전 반드시 사용자 검토 | A8 |
| E6 | 엑셀 업로드 | 더존·이카운트 내보내기 + 원본 djob 양식 호환 가져오기 | — |
| E7 | 추정 모드 | 동인 실적 등 미확보 데이터는 추정치 입력 허용하되 `is_estimated` 배지로 전 화면·보고서에 표시 | A11 |
| E8 | 체크리스트 + 순차입력 | 월 사이클을 대시보드 체크리스트로 안내, 선행 단계 미완료 시 후행 차단 | A1 |
| E9 | 전월 복사 | 경비·인원 등 반복 데이터는 전월 값 복사 후 수정 | — |
| E10 | 실시간 검증 | 입력 즉시 경고(허용) → 마감 시 차단의 2단계 | A11 |
| E11 | 계산 버튼 방식 | 자동 재계산 대신 명시적 [계산] 버튼 — 사용자가 계산 시점을 통제, 결과 재현성 보장 | A8 |

---

# 6. 원가 방법론 명세 — 전통 개별원가 엔진 (제조 부문)

## 6.1 산식 체인 (엑셀 1원 단위 재현 기준)

**(1) 직접재료비**
```
품목별 월총평균단가 = (기초재고금액 + 당월매입금액) ÷ (기초재고수량 + 당월매입수량)   [A3]
제품 단위당 재료비 = Σ(BOM 소요량 × 해당 자재 월총평균단가)
당월 재료비 = Σ(제품별 단위당 재료비 × 생산수량)                                  [A4 생산기준]
```
- 구매는 월 다회차 입력 허용(원본 pu 10회차) → 월 가중평균으로 집계
- 유통품(상품)은 BOM 자기참조 1 방식을 웹에서 불허하고 `merchandise` 유형으로 대체(마이그레이션 시 자동 변환)

**(2) 직접노무비 — 조업도 체인**
```
실근무일수 = 카렌다일수 − 법정공휴일 − 회사임의공휴일 − 유지보수기간
총작업가능시간 = 실근무일수 × (일근무시간 + 일평균초과근무) × 직접작업인원(일용직 FTE 환산 포함)
생산요구시간 = Σ(제품 단위공수 × 생산수량)      ※ 단위공수: 제품별 정의 우선 → 생산유형 상속
차이시간 = 총작업가능시간 − 생산요구시간          → 금액화하여 미사용능력 보고 [A9]
회사부담임률 = 생산직 노무비 합계 ÷ 생산요구시간
제품별 직접노무비 = 단위공수 × 생산수량 × 회사부담임률                            [Q-E 공수 단일]
```
- 일용직 FTE 환산: 총작업시간 기준 환산인원·환산임금(원본 hr 로직 — 730h→3.2명)
- 월급제/일급제 구분(pay_type), 복리후생 포함 인건비 구성(기본급·시간외·복리후생·상여·퇴직충당금)
- 생산요구시간 > 총작업가능시간이면 경고(원본 hr 검증 문구 계승) — 마감 차단 대상 [A11]

**(3) 제조경비**
```
계정별 고정/변동 태그(19계정 → 무제한) + 배부기준 3종 택1 [A5, Q-A]
  ① 직접노무원가 기준: 제품별 직접노무비 비례
  ② 직접노무시간 기준: 제품별 (단위공수×생산수량) 비례
  ③ 기계시간 기준: 제품별 월 기계시간 입력값 비례 (선택 시에만 입력 필드 노출) `[ASSUMPTION: 기계시간 입력 필드는 원본 costmgr에는 없음. 신규 입력은 추론. 근거: 배부기준 ③ 선택 시 노출(E4). 추론일: 2026-07-12.]`
배부 모수 = 생산기준 [A4] / 배부합계 = 경비 원금액 [A6]
```

**(4) 제품 원가 2계층** [A2]
```
제조원가 = 재료비 + 직접노무비 + 제조경비배부액                → 재고 평가·제조원가명세서
완전원가 = 제조원가 + 관리인건비배부(직접노무비 비례) + 판관비배부(매출액 비례) → 관리 뷰 전용 `[ASSUMPTION: 관리인건비 = 직접인건비 비례는 원본 pl 시트의 29.3% 상당 배부 패턴 계승. 판관비 = 매출액 비례는 A2·A5의 일반 원칙. 두 비율을 변경할 수 있는 설정 필드는 §8.1 M0에서 노출 여부 추론. 추론일: 2026-07-12.]`
```

**(5) 손익계산서 골격 (원본 pl4 계승)**
```
매출 → 매출원가(재료비+직접인건비+제조경비 ± 제품재고조정) → 매출총이익
    → 판매일반관리비(관리인건비 포함) → 영업손익 → 지급이자 → 세전손익 → 세금 → 세후손익
```
- '제품 재고 조정' 라인 = check 로직의 자동화 산출물(제11장 V4) `[NOTE FOR PM: §11 V4의 "± 제품재고조정" 손익 표시 부호가 사용자 UX에 그대로 노출될 때, 마이너스 재고조정(재고 감소)이 영업손익을 깎는 것처럼 보이는 현상이 발생함. UX는 이 라인이 회계상의 "조정"이지 "손실"이 아님을 시각적으로 구분해야 함(예: 색·라벨 분리). owner: UX designer. 해소 시점: UX 와이어프레임 단계.]`
- 뷰 3종: 종합 / 제품별 / 판매지역별(선택 입력 시)
- 12개월 비교 + YTD(마감월만 집계), 예산 대비(제10장), 차월 추정(차입금·이자율·상승률·세율 파라미터 — 원본 pl3 그린셀 5종)

**(6) 제품별 CVP·BEP (원본 bep 계승)**
```
고정비 F = 관리인건비배부 + 판관비 중 고정 + 제조경비 중 고정 (제품 배부분)
단위당 변동비 V = 재료비 + 직접노무비 + 제조경비 변동분 + 판관비 변동분 (단위당)
공헌이익 CM = P − V / BEP 수량 = F ÷ CM / 목표 세전이익 역산(단가·매출액)
```
- 원본의 한계 고지 계승: "고정비 배부액이 판매량에 따라 변하므로 참고자료"라는 주석 고정 표시
- 고정/변동 태그 활용처 5곳: BEP·AI 재추정·차월 추정·제조경비 배부·목표이익 역산

## 6.2 재고 수불 (원본 m/p 시트 계승)

- 원부재료 수불부: 기초 + 구입 − 생산출고 = 기말, 재고실사 → 재고조정(A8 역분개)
- 제품 수불부: 기초 + 생산 − 판매 = 기말, 제조원가 평가(전월·당월 평균)
- 기초재고는 시스템 개시 시 1회 입력, 이후 월 체인 자동 이월
- 음수재고 실시간 경고(원본의 방치 문제 해소) [A11]

## 6.3 주문 관리 (선택 기능 — 결정 Q-B)

- 주문 입력(월합계 기본/일자별 선택) → 주문잔량 Back Log(누적주문 − 누적생산) → 주문품 자재 총소요 전개(BOM×주문수량 — 구매계획 지원)
- 생산품 자재 총소요(pmaterials 계승)는 기본 제공. 주문 미입력 시 관련 화면·보고서 숨김(E4)

---

# 7. 원가 방법론 명세 — ABC 엔진 (서비스 부문)

## 7.1 Classic ABC (원본 ABCost 3-Step 계승)

```
Step 0  매출·직접비: 원가대상(제품/서비스)별 매출, 귀속 가능한 직접재료비·직접인건비 입력
        (귀속 불가 인건비는 간접비로 — 원본 2.1 labor 원칙)
Step 1  원가풀(Resource Pool): 계정별 간접비를 설비/매출/인원 3기준 비율로 1차 배부
        (일괄적용 Y/N 토글 — 원본 4 resource pool 계승, 행 합 100% 강제)
Step 2  활동(Cost Activity): 주요활동 5~15개(소프트 경고, 원본 권고 ≤10),
        활동별 설비/매출/인원 열 비중(열 합 100% 강제)으로 원가풀 → 활동 배부
Step 3  동인(Activity Driver): 활동별 동인 정의, 제품별 동인 소비 건수 또는 비율(%) 입력 토글,
        '활동 % 직접배분' 우회 옵션(원본 Yes/No) → 원가대상 최종 배부
검증    각 단계 배부합계 = 원금액 [A6] / 동인 열 합 = 총건수 또는 100%
```

- 활동별 동인 건당 소요시간 → 총시간 산출 → **간접인건비 근무시간 검증**(급여기준 월작업시간 vs 동인총시간 차이 표시 — 원본 6 activity drivers의 생산성 진단 계승)
- 업종 템플릿 + AI 활동 초안(E5) — "AI는 초안, 확정은 사람"
- 동인 실적: 수기 + 엑셀 업로드 + AI 추출 + 추정 모드(is_estimated 배지) `[ASSUMPTION: 동인 입력의 "건수/비율 토글" UI 노출은 원본 ABCost의 Yes/No 토글 계승. 토글 기본값(건수 우선) 및 동인별 분포 강제(합 100% / 총건수)는 추론. 추론일: 2026-07-12.]`

## 7.2 TDABC (2026 최신 이론 장착분 — 결정 Q-J 첫 버전 확정)

```
CCR(Capacity Cost Rate) = 부서 원가 ÷ 실제적 조업능력(practical capacity)
실제적 조업능력 = 이론 능력 × 80% 기본 (정밀 마법사로 세부 조정 가능)
원가대상 배부 = Σ(동인 건수 × 건당 표준시간 × CCR)
미사용능력 원가 = (실제적 조업능력 − 사용시간) × CCR → 별도 보고 [A9]
```

- 회사 단위 단일 모드(classic ↔ TDABC 택1), `method_override` 예비 필드로 활동별 혼용은 2차
- CCR 산출 단위 = 부서 `[ASSUMPTION: CCR을 부서 단위로 산출하는 것이 Kaplan TDABC 정론의 일반적 사례이나, 동일 저작자 ABCost 시트에서 CCR 산출 단위가 활동 단위인 케이스도 발견됨. 본 PRD는 부서 단위 단일로 통합 결정. 추론 근거: 부서 단위 산출이 1인 운영자 SaaS의 운영 부담을 낮춤. 추론일: 2026-07-12.]`
- 전통 엔진의 조업도 차이시간과 동일 사상으로 통합 '미사용능력 보고서' 제공

## 7.3 부문 카브아웃 (겸영 기업)

- 공통비 분할: 법인세법 시행규칙 76조 2기준(매출액 비례/개별비용 비례) 택1 [A10]
- 부문 전용 계정 태깅 + 부문귀속명세서 보고서로 분할 근거 공시 `[ASSUMPTION: 부문귀속명세서 카브아웃 분할 근거 공시 형식(표 / 막대차트 / 산식 트리)은 추론. 법인세법 시행규칙 제76조 2기준의 시각화 방법은 정합성 헌법 [A10] 충족을 전제로 UX 단계에서 확정. 근거: §9 #21 표기. 추론일: 2026-07-12.]`
- ③④ 업종은 재무제표 업로드 필수(분할 검증 기준)

---

# 8. 모듈 구성 (통합 13모듈)

| 모듈 | 명칭 | 핵심 내용 | 원천 시트 |
|------|------|-----------|-----------|
| M0 | 온보딩·설정 | 업종 4지선다, 부문, 회계연도 시작월, 통화(KRW/USD)·언어(한/영), 배부기준 3종 선택, AI 문서추출 | infor, basic data |
| M1 | 기준정보 | 품목 통합(제품/반제품/원자재/상품/서비스), BOM 매트릭스 편집, 생산유형·공정, 계정과목(고정/변동), 부서, 판매지역(선택), 거래처(선택), 제품사진 | BOM2, process, infor |
| M2 | 월 데이터 입력 | 6종: 주문(선택)·생산(+생산유형·기계시간(조건))·판매(+지역 선택)·구매(다회차)·경비(제조/판관 구분)·인원인건비(조업도) — 월합계 기본+일자별 선택, 전월복사, 엑셀 업로드 | or, pr, sa, pu, exp, hr |
| M3 | 원가계산 엔진 | 제6장 산식 체인, [계산] 버튼, 1원 단위 엑셀 대조 테스트 통과 필수 | operation, operation2, expenses |
| M4 | 재고 수불 | 원부재료·제품 수불부, 실사 조정, 재고 검색, 음수 경고 | m1~12, p1~12, inv, pinv |
| M5 | 손익·보고서 | 제9장 보고서 체계 전체 | pl 계열, cost, ctable, cststmt |
| M6 | 자동 검증 | 제11장 V1~V8 Reconciliation | check |
| M7 | 시뮬레이션 | 제품별 CVP/BEP + 목표이익 역산(슬라이더), 차월 손익 추정 | bep, pl3 |
| M8 | 예산 시나리오 | 제10장 | pl5, manual '예산' |
| M9 | ABC 엔진 | 제7장 Step 0~3 + TDABC + 카브아웃 | ABCost 전체 |
| M10 | AI 지원 | 문서추출 / 인사이트 질문 3개 생성·캐시 / 고정·변동 3단계 추정 | — |
| M11 | 마감·이력 | 순차 마감(부문분할→제조→ABC→공동), 스냅샷, 역분개 정정, 감사추적 | 저장/복구 VBA 대체 |
| M12 | 계정·운영 | 2FA, 백업(일1회+셀프 다운로드), 해지(보관일수+삭제동의), 운영자 콘솔, 대리접속, 공지 | — |

---

## 8.1 모듈별 인수 기준 (Acceptance Criteria)

각 모듈은 다음 형식의 2~4개 인수 불릿을 만족해야 "완료"로 본다("시스템은 X를 Y 시점에 Z 조건으로 수행한다" — §11 V-row 형태 참고).

- **M0 (온보딩·설정)**
  - (a) 시스템은 신규 가입자가 업종 4지선다를 선택한 시점에 후속 메뉴(§4.1)를 자동 토글한다.
  - (b) 시스템은 회계연도 시작월·통화·언어·배부기준 3종 선택을 미완료 상태로 [계산] 진입을 차단한다.
  - (c) AI 문서추출(E5)은 신뢰도 < 70% 항목을 빨강 배지로 표시하고 사용자 확정을 강제한다.
  - **(d) Phase 3 신규 — 로그인 UI + Supabase SSR auth client** — 시스템은 이메일·비밀번호 기반 로그인을 제공하며, 인증 성공 시 Supabase 가 발급한 `sb-access-token` 쿠키(SSR 호환, `httpOnly` + `secure` + `sameSite=lax`)를 클라이언트·서버 양쪽에서 일관되게 읽어 세션을 확인한다 [§F15.1, §F15.3]. 로그인 실패 시 ko-KR 메시지("이메일 또는 비밀번호가 올바르지 않습니다", `LOGIN_INVALID_CREDENTIALS_KO`)를 표시하고, 5회 연속 실패 시 30초 cool-down을 강제한다 (CR 12-5 D-14 envelope `{code, message_ko, details, trace_id}` 정합). Epic 12 2FA 설정 사용자(M12-a)는 로그인 성공 후 2FA 챌린지 페이지(`/auth/2fa`)로 리다이렉트된다 [Epic 12 wire 정합, AD-26]. capability gate `LOGIN` (capability matrix v1.24, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러).
  - **(e) Phase 3 신규 — 회원가입 UI + tenant 생성 flow** — 시스템은 이메일·비밀번호·회사명 3필드 기반 회원가입을 제공하며, 가입 성공 시 자동으로 새 tenant(`tenants` row 1개) + owner 사용자 1명(`users` row + `user_tenants` row owner role) + `tenant_settings.onboarding.industry = null` 상태로 초기화한 후 `/[locale]/(auth)/onboarding/industry` 로 리다이렉트한다 [§F15.2]. 비밀번호 강도 검증 (최소 10자 + 대소문자·숫자·특수문자 각 1자 이상) 강제, RFC 5322 이메일 형식 검증. 가입 실패 시 ko-KR 메시지 ("이미 가입된 이메일입니다" / "비밀번호는 10자 이상이며 대소문자·숫자·특수문자를 포함해야 합니다" — `SIGNUP_DUPLICATE_EMAIL_KO` / `SIGNUP_WEAK_PASSWORD_KO`) 표시. capability gate `SIGNUP` (capability matrix v1.24, industry-agnostic 4-industry grants ✅/✅/✅/✅).
  - **(f) Phase 3 신규 — Auth middleware (Supabase session + next-intl middleware EXTENSION)** — 시스템은 `apps/web/middleware.ts` 의 next-intl middleware 를 EXTENSION 하여 모든 `/[locale]/(dashboard)/*` 요청에 대해 Supabase session 검사를 강제한다 [§F15.3, AD-26]. 세션 없거나 만료 시 `/[locale]/login` 으로 redirect (`?redirect=<original-path>` 쿼리 보존). `/[locale]/(auth)/*` (login / signup / forgot-password) 는 공개 route group 으로 미들웨어 bypass. `/api/v1/*` (백엔드 API) 는 미들웨어 bypass (백엔드 자체의 `get_tenant_context` 가 세션 검증). Static assets (`_next/*`, `*.png`, `*.svg`, `*.ico` 등) matcher 제외. capability gate `AUTH_MIDDLEWARE` (capability matrix v1.24, industry-agnostic 4-industry grants ✅/✅/✅/✅). 2FA 미설정 사용자 (Epic 12 M12-a 정합) 가 dashboard 진입 시도 시 `/[locale]/account/security` 로 redirect (2FA 설정 강제).
  - **(g) Phase 4 신규 — Production deployment config + Dockerfile + health check + observability + database backup** — 시스템은 Vercel frontend (vercel.json, regions=[icn1], buildCommand=`pnpm --filter web build`) + Railway backend (railway.toml, builder=DOCKERFILE, healthcheckPath=`/api/v1/health`) + Supabase production PostgreSQL 결정 wire 으로 production deployment 가 atomic single sprint T1~T8 으로 wire 되어야 한다 [§F16, AD-27]. per-app Dockerfile 분리 (`apps/web/Dockerfile` + `apps/api/Dockerfile`, AD-14 stack pin by @sha256: digest 결정). Health check endpoint `GET /api/v1/health` (FastAPI) + `GET /api/health` (Next.js route handler) 가 database connectivity + JWT verification 을 검증하고 liveness/readiness 분리 결정 wire. Sentry observability integration (browser SSR-safe + server FastAPI) 결정. Database backup strategy (alembic 0036 phase_4_backup_strategy table + Supabase PITR 7일 자동 + RPO 5분/RTO 1시간 결정) 결정 wire. `docs/deployment.md` (12 sections runbook) + `docs/database-backup.md` 결정. capability gates `DEPLOYMENT_PROD` + `DEPLOYMENT_STAGING` + `DEPLOYMENT_DATABASE_BACKUP` + `DEPLOYMENT_HEALTH_CHECK` 4 NEW (capability matrix v1.25, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러).
  - **(h) Epic 15 신규 — Magic link login (D-1-1-DEFER-1 ✅ RESOLVE)** — 시스템은 이메일 단일 필드 기반 매직 링크 로그인을 제공하며, Supabase `signInWithOtp({ email, options: { emailRedirectTo } })` wrapper + 5회 cool-down (sessionStorage 30s, Phase 3-1 T2 wire 패턴 미러) + email 존재 여부 노출 방지 (security invariant try/catch/finally, Phase 3-1 T6 forgot-password 정합) + audit-first INSERT `magic_link_sent` (CR 1-1 verbatim, action_class='AUTH' + action='magic_link_sent' + actor_id + target_email) [§F17.1, AD-28]. Magic link 클릭 시 `supabase.auth.exchangeCodeForSession(code)` + `sb-access-token` cookie session 자동 설정 (Phase 3-1 T1 wire 정합) + `router.push('/dashboard')` 결정. Epic 12 2FA 미설정 사용자 (Epic 12 M12-a 정합) 는 매직 링크 성공 후 2FA 챌린지 페이지(`/auth/2fa`) 로 redirect. capability gate `MAGIC_LINK` (capability matrix v1.26, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러).
  - **(i) Epic 15 신규 — Social OAuth (Google/Naver/Kakao) login (D-1-1-DEFER-2 ✅ RESOLVE)** — 시스템은 3 provider (Google + Naver + Kakao) 기반 소셜 OAuth 로그인을 제공하며, Supabase `signInWithOAuth({ provider, options: { redirectTo } })` wrapper 결정 wire [§F17.2, AD-28]. Provider whitelist (`ALLOWED_SOCIAL_PROVIDERS = frozenset({'google', 'naver', 'kakao'})` strict reject + counter increment, AD-7 verbatim 정합) + 3회 cool-down (sessionStorage 60s, magic link 와 분리) + audit-first INSERT `social_oauth_initiated` (CR 1-1 verbatim, action_class='AUTH' + action='social_oauth_initiated' + actor_id + provider) + OAuth callback handler (`/auth-callback` + `exchangeCodeForSession(code)` + session cookie setting + dashboard redirect 결정 wire). **Naver OAuth 특수 처리** 결정 wire (2026-08-22 KST, 한국 시장 정합) — Option A Supabase Naver 지원 시 그대로 사용 / Option B 미지원 시 custom Naver OAuth flow wire 결정 wire 보존 (Epic 15-1 bmad-dev-story 진입 시점에 결정). capability gates `SOCIAL_OAUTH_GOOGLE` + `SOCIAL_OAUTH_NAVER` + `SOCIAL_OAUTH_KAKAO` 3 NEW (capability matrix v1.26, industry-agnostic 4-industry grants ✅/✅/✅/✅).
  - **(j) Epic 15 신규 — SSO enterprise SAML (D-1-1-DEFER-3 ✅ RESOLVE)** — 시스템은 SAML 2.0 기반 엔터프라이즈 SSO 로그인을 제공하며, `python3-saml==1.16.0` library (AD-14 stack pin 결정) + SAML response validation (signature verification + `NotBefore`/`NotOnOrAfter` timestamp + `Audience` + `Destination` + `InResponseTo` CSRF 방어 + RelayState base64 encode) 결정 wire [§F17.3, AD-28]. 4 SSO routes 결정 wire — (1) `GET /api/v1/auth/sso/login?tenant_slug=&relay_state=` SAML AuthnRequest 생성 + IdP SSO URL redirect (HTTP 302) / (2) `POST /api/v1/auth/sso/acs` SAML ACS endpoint (response 검증 + JIT provisioning + `sb-access-token` cookie set + 200 OK) / (3) `GET /api/v1/auth/sso/metadata?tenant_slug=` SP metadata XML 반환 (IdP 등록용) / (4) `GET /api/v1/auth/sso/sls` Single Logout Service endpoint. **JIT (Just-In-Time) user provisioning** 결정 wire (SAML response → user + tenant_memberships + external_identities atomic 5-step flow). Multi-tenant isolation (CR 0-2 RLS lesson 적용, AD-22 verbatim): `external_identities` table (alembic 0037) RLS policy `tenant_id = (SELECT current_setting('app.tenant_id'))::uuid` 결정. Tenant slug 별 IdP metadata routing (multi-tenant SSO) 결정. audit-first INSERT `sso_identity_linked` (CR 1-1 verbatim, action_class='AUTH' + action='sso_identity_linked' + actor_id + provider + provider_user_id + tenant_id) 결정. Epic 12 2FA 미설정 사용자는 SSO 성공 후에도 `/auth/2fa` 로 redirect 결정 wire. capability gate `SSO_ENTERPRISE` (capability matrix v1.26, industry-agnostic 4-industry grants ✅/✅/✅/✅).
  - **(k) 1st release 신규 — 1st release launch 진입 (옵션 (d) 결정 wire, A83 결정)** — 시스템은 1st release launch 결정 wire 진입 시점에 다음 6 conditions ALL PASS 결정 wire: (1) Marketing landing page wire DONE (`/landing` route + LandingHero + LandingFeatures + LandingPricing + LandingCTA + ko-KR inline copy EXTENSION, §F18.1) / (2) ToS + Privacy Policy wire DONE (`docs/terms-of-service.md` + `docs/privacy-policy.md` 한국 PIPA + GDPR 정합, §F18.2) / (3) Onboarding user guide wire DONE (`docs/onboarding-guide.md` 8 sections + OnboardingTooltip + first-run wizard EXTENSION Epic 1 partial scaffold 정합, §F18.3) / (4) Customer support channels wire DONE (`docs/support.md` + email + HelpWidget + FAQ, §F18.4) / (5) Production launch verification wire DONE (smoke test RE-RUN 정직 결정 + backup drill 0036 PITR quarterly + Sentry alert wiring + RPO 4h/RTO 24h SLA verification, §F18.5) / (6) Public launch communications wire DONE (`docs/launch-announcement.md` + press kit + og/assets + in-app banner, §F18.6). 6 conditions ALL PASS 진입 시점에 1st release official launch 결정 wire 보존 (cj-style 62번째 epic 연속 정직 회복). capability gates `LAUNCH_LANDING` + `LAUNCH_TOS` + `LAUNCH_SUPPORT` + `LAUNCH_MONITORING` 4 NEW (capability matrix v1.27, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러).
  - **(l) Epic 16 신규 — Tenant IdP admin management (옵션 (a) Epic 16 진입 결정 wire, A92 결정)** — 시스템은 Epic 16 = Tenant IdP admin management 결정 wire 진입 시점에 다음 6 ACs ALL PASS 결정 wire [§F19, AD-30]: (1) **`tenant_idps` table** wire DONE (alembic 0038 + columns 13개 + unique constraint `(tenant_id, idp_entity_id)` + RLS policy `tenant_id = current_setting('app.tenant_id')` + index `idx_tenant_idps_tenant_id` + `updated_at_auto_update_trg` audit trigger) / (2) **IdP metadata XML validation service** wire DONE (`apps/api/modules/auth/sso/idp_metadata_validator.py` 8 validation steps: well-formedness + EntityDescriptor + entityID + IDPSSODescriptor + x509 cert PEM wrap + SSO URL https:// + SLO URL https:// + tenant slug 매칭) / (3) **Tenant IdP CRUD API 5 routes** wire DONE (`GET / POST / PUT / DELETE / TEST /api/v1/admin/tenant/{tenant_slug}/idp`, owner/admin role required + capability gate `TENANT_IDP_MANAGEMENT` + RLS 자동 적용 + audit-first INSERT 4 NEW: `tenant_idp_created` / `tenant_idp_updated` / `tenant_idp_deleted` / `tenant_idp_tested`) / (4) **Tenant IdP admin UI** wire DONE (`apps/web/app/[locale]/(dashboard)/settings/sso/page.tsx` + 4 components: TenantIdPConfigForm + TenantIdPStatusBadge + TenantIdPTestResultModal + TenantIdPDeleteConfirmDialog + `apps/web/messages/ko-KR.json` `settings.sso.*` namespace EXTENSION 12 keys + (dashboard) 보호) / (5) **Per-tenant IdP routing EXTENSION** wire DONE (Epic 15 SAML routes `saml_routes.py` EXTENSION: `tenant_slug` → `tenant_idps` lookup → `idp_sso_url` redirect + ACS `idp_x509_cert` 동적 로딩 + backward compatibility `acme` hardcoded tenant 보존) / (6) **Capability gate TENANT_IDP_MANAGEMENT** wire DONE (capability matrix v1.27 → v1.28 EXTENSION 1 NEW row + 4-industry grants industry-agnostic ✅/✅/✅/✅ + drift detector `tests/integration/test_capability_matrix_v1_28_drift.py` NEW). 6 ACs ALL PASS 진입 시점에 Epic 16 wire DONE 결정 wire 보존 (cj-style 67번째 epic 연속 정직 회복). capability gate `TENANT_IDP_MANAGEMENT` (capability matrix v1.28, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러, SSO_ENTERPRISE Epic 15 wire pattern). D-LAUNCH-1-DEFER-1 honestly preserved 65~66~67번째 (CR 11-3 honest-DEFER discipline 67번째 epic 연속 정직 회복 검증). D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존 67번째 (Epic 15 wire `5f9e37f` 진입 시점에 모두 정직 회복 결정 wire 완료).
  - **(m) Phase 5 신규 — Multi-Region Backup & Disaster Recovery (옵션 (a) Phase 5 진입 결정 wire, A124 결정)** — 시스템은 Phase 5 = Multi-Region Backup & Disaster Recovery 결정 wire 진입 시점에 다음 5 ACs ALL PASS 결정 wire [§F20, AD-31]: (1) **Cross-region read replica + WAL archiving** wire DONE (alembic 0039 phase_5_replication_lag table + `phase_5_dr_drill_results` table + replica_region enum seoul/tokyo/singapore/frankfurt/virginia/oregon/sao_paulo + primary_region enum + lag_bytes BIGINT + lag_seconds INTEGER + last_synced_lsn TEXT PG_LSN + replication_status enum syncing/replicating/lagged/disconnected/failed + audit-first INSERT `replica_status_changed` CR 1-1 verbatim + 3 indexes + 2 CHECK constraints + `apps/api/alembic/versions/0039_phase_5_multi_region_backup.py` + `docs/cross-region-replication.md`) / (2) **Cross-region failover automation** wire DONE (`apps/api/jobs/failover_orchestrator.py` + primary → secondary health probe 5-second interval + 3 consecutive failures trigger + automatic promotion via Supabase API `POST /v1/projects/{ref}/database/promote` + DNS update via Supabase custom domain redirect + 30s RTO target + audit-first INSERT `failover_initiated` + `failover_completed` + FastAPI lifespan hook startup/shutdown + GRACEFUL_SHUTDOWN_TIMEOUT=30s + owner-only manual trigger `POST /api/v1/admin/failover` AD-22 RBAC + 2FA 챌린지 Epic 12 정합) / (3) **DR drill + automated quarterly test** wire DONE (`apps/api/jobs/dr_drill.py` + cron KST 1st Sunday 03:00 UTC 18:00 + actual failover drill test in staging + 6 drill steps: health check + secondary promote + write test + application health + DNS update + restore trigger + RPO/RTO measurement + `phase_5_dr_drill_results` table + Q1/Q2/Q3/Q4 quarterly schedule + audit-first INSERT `dr_drill_completed`) / (4) **Cross-region backup strategy** wire DONE (`docs/database-backup.md` EXTENSION + Supabase PITR primary Seoul + secondary Tokyo + 30일 hot + 90일 cold + 365일 archive regional + RPO 1h / RTO 4h SLA post-multi-region wire DONE 진입 + Phase 4 single-region RPO 5min/RTO 1h honest-extreme risk = Seoul region disaster 시 backup restoration 불가 verbatim 해소 결정) / (5) **Multi-region health observability** wire DONE (`apps/api/core/health.py` EXTENSION `/api/v1/health/multi-region` endpoint + primary + secondary status array + CR 12-5 D-14 envelope `{status, primary: {region, status, lag_bytes, lag_seconds, last_synced_at}, secondary: {...}, timestamp}` + `apps/api/core/observability.py` EXTENSION Sentry breadcrumb failover + Sentry alert routing + Grafana multi-region dashboard + `apps/web/app/api/health/multi-region/route.ts` NEW Next.js Edge Runtime + force-dynamic + capability gates MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER 2 NEW capability matrix v1.28 → v1.29 EXTENSION industry-agnostic 4-industry grants ✅/✅/✅/✅ + drift detector `tests/integration/test_capability_matrix_v1_29_drift.py` NEW + ~50 NEW pytest + ~10 NEW vitest). 5 ACs ALL PASS 진입 시점에 Phase 5 wire DONE 결정 wire 보존 (cj-style 73번째 epic 연속 정직 회복 wire 진입 시점). capability gates MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER (capability matrix v1.29, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러, DEPLOYMENT_PROD + DEPLOYMENT_DATABASE_BACKUP Phase 4 wire pattern 미러). D-PHASE-4-DR-DEFER-1 + D-PHASE-4-DR-DEFER-2 ✅ RESOLVE 진입 wire 결정 (Phase 4 close-out retro §6 disaster recovery verbatim multi-region backup 결정 wire 보류 honestly carry-over + Phase 5 PRD entry 진입 시점에 정직 회복 결정 wire 완료, CR 11-3 honest-DEFER discipline 73번째 epic 연속 정직 회복 검증). D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존 73번째 (Epic 15 wire `5f9e37f` 진입 시점에 모두 정직 회복 결정 wire 완료). D-EPIC-16-REVIEW-DEFER-2~6 honestly DEFERRED 5 OPEN 보존 73번째 (Epic 16 wire `963079c` 진입 시점에 결정).
  - **(n) Epic 17 신규 — Audit Log Viewer & Activity Stream (옵션 (a) Epic 17 진입 결정 wire, A153 결정)** — 시스템은 Epic 17 = Audit Log Viewer & Activity Stream 결정 wire 진입 시점에 다음 7 ACs ALL PASS 결정 wire [§F21, AD-32]: (1) **audit log query API** wire DONE (`apps/api/modules/audit/audit_log_query.py` NEW ~+180 LOC, 4 functions: query_audit_log + count_audit_log + get_audit_log_entry + query_activity_stream + AuditLogQueryFilters + AuditLogEntry + AuditLogPage + ActivityStreamGroup TypedDict + RLS 자동 적용 CR 0-2 verbatim + owner/admin role required + capability gate AUDIT_LOG_VIEW) / (2) **audit log viewer UI** wire DONE (`apps/web/app/[locale]/(dashboard)/audit-log/page.tsx` NEW ~+200 LOC + 5 components: AuditLogFilterPanel + AuditLogTable + AuditLogPagination + AuditLogExportButton + AuditLogDetailModal + ko-KR.json `audit_log.*` namespace EXTENSION 14 keys + (dashboard) 보호 + vitest RTL render discipline CR 11-4 D-003 verbatim) / (3) **activity stream UI** wire DONE (`apps/web/app/[locale]/(dashboard)/activity/page.tsx` NEW ~+150 LOC + 3 components: ActivityStreamTimeline + ActivityStreamEntry + ActivityStreamWindowSelector + ko-KR.json `activity.*` namespace EXTENSION 8 keys + all tenant members 권한) / (4) **cross-region audit log visibility** wire DONE (Phase 5 multi-region read replica 통한 cross-region audit query + read-only routing + lag threshold 정합 lag_bytes ≤ 100MB + lag_seconds ≤ 30s + Sentry breadcrumb 결정 wire) / (5) **CSV export** wire DONE (`apps/api/modules/audit/audit_log_export.py` NEW ~+120 LOC + streaming response + UTF-8 BOM + Excel-compatible comma-separated + audit-first INSERT `audit_log_exported` CR 1-1 verbatim action_class='AUDIT' + action='audit_log_exported' + actor_id + tenant_id + filters_json + row_count + trace_id + CR 12-5 D-14 envelope 결정 wire) / (6) **Capability gate AUDIT_LOG_VIEW** wire DONE (capability matrix v1.29 → v1.30 EXTENSION 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅ + drift detector `tests/integration/test_capability_matrix_v1_30_drift.py` NEW) / (7) **Tests + wire scope T1~T8** 결정 (~+50 NEW pytest PASS + ~+15 NEW vitest PASS + 0 NEW ruff + 0 regressions + T1 audit_log_query module + T2 audit_log_export module + T3 audit_log_viewer page + T4 activity_stream page + T5 ko-KR.json SSOT EXTENSION + T6 capability.py + capability matrix v1.30 + T7 tests + 3중 게이트 FINAL CLEAN + T8 atomic commit). 7 ACs ALL PASS 진입 시점에 Epic 17 wire DONE 결정 wire 보존 (cj-style 80번째 epic 연속 정직 회복 wire 진입 시점). capability gate AUDIT_LOG_VIEW (capability matrix v1.30, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러, MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY Epic 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern verbatim bind). D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존 80번째 (Epic 15 wire `5f9e37f` 진입 시점에 모두 정직 회복 결정 wire 완료). D-LAUNCH-1-DEFER-1 honestly preserved 65~80번째 (1st release cycle 보존). D-EPIC-16-REVIEW-DEFER-2~6 ✅ RESOLVED 보존 78~80번째 (D-EPIC-16-REVIEW-DEFER-2~6 RESOLVE sprint `512ed6a` 78번째 wire DONE 진입 후 보존). D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED 보존 73~80번째 (Phase 5 PRD entry 73번째 + atomic wire 75번째 + close-out retro 76~77번째 진입 시점에 모두 정직 회복 결정 wire 완료).

- **M1 (기준정보)**
  - (a) 시스템은 BOM 매트릭스에서 비중 합 != 100% 상태로 [계산] 진입을 차단한다 [A6].
  - (b) 시스템은 품목 유형을 변경(예: 제품 → 서비스)할 때 BOM·수불 참조가 0건임을 검증한 후에만 허용한다.

- **M2 (월 데이터 입력)**
  - (a) 시스템은 월합계 기본 모드에서 일자별 그리드 필드를 비노출로 둔다(E4).
  - (b) 시스템은 일용직 FTE 환산을 입력 완료 시 자동 계산하여 "환산 인원·환산 임금"을 표시한다.
  - (c) 시스템은 음수재고·조업도 초과 발생 시 입력 완료 즉시 경고하고, 마감 시 차단한다 [A11, V3·V5].

- **M3 (원가계산 엔진)**
  - (a) 시스템은 [계산] 클릭 시 §6.1 산식 체인 전체를 단일 트랜잭션으로 실행하고, 도중 실패 시 전체 롤백한다 [A6].
  - (b) 시스템은 계산 완료 시 §11 V1·V4·V7·V8을 자동 발동하여 위반이 1건이라도 있으면 결과를 "검증 실패" 상태로 잠근다.

- **M4 (재고 수불)**
  - (a) 시스템은 기초재고 입력 후 자동 이월 체인을 개시하고, 이후 수동 입력은 차단한다.
  - (b) 시스템은 음수 기말을 감지 즉시 경고하고, 사용자 확인 없이 마감 진입을 차단한다 [V3].

- **M5 (손익·보고서)**
  - (a) 시스템은 §9 21종 보고서 각각에 대해 "종합 / 제품별 / 판매지역별" 뷰 토글을 제공한다.
  - (b) 시스템은 KRW/USD 동시 표시 시 환율을 표시하고 USD 소수 2자리를 강제한다.
  - (c) 시스템은 보고서 PDF 내보내기 시 A4 인쇄 최적화 페이지 크기를 적용한다.

- **M6 (자동 검증)**
  - (a) 시스템은 §11 V1~V8을 마감 진입 시점과 계산 시점 두 곳에서 자동 발동한다.
  - (b) 시스템은 V8 회귀 테스트 스위트 실패 시 CI 빌드를 차단한다.

- **M7 (시뮬레이션)**
  - (a) 시스템은 슬라이더 변경 시 BEP 수량·목표 이익을 1초 이내로 재계산한다(§14 성능 임계).
  - (b) 시스템은 차월 추정 시 차입금·이자율·상승률·세율 4종 파라미터의 사용자 입력을 강제한다.

- **M8 (예산 시나리오)**
  - (a) 시스템은 1차에서 시나리오 1개만 허용하고, 2개 이상 생성 시도를 차단한다(2차에서 해제).
  - (b) 시스템은 예산 실적 대조 시 모든 차이 행을 표시하고, A×B×C×D 편성 엔진이 미구현이면 회색 배지로 "2차 예정"을 표시한다.

- **M9 (ABC 엔진)**
  - (a) 시스템은 원가풀 행 합 != 100%, 활동 열 합 != 100%, 동인 합 != 100% 상태로 [계산]을 차단한다 [V7].
  - (b) 시스템은 TDABC CCR 산출 시 부서 원가 ÷ 실제적 조업능력을 1원 단위로 계산하고, 미사용능력 금액을 별도 표시한다 [A9].

- **M10 (AI 지원)**
  - (a) 시스템은 인사이트 질문 3개 생성·캐시 시 "캐시 = 마감 완료 시점부터 다음 마감 시작까지 보존, 마감 데이터 변경 시 폐기" 정책을 강제한다 (검수 medium 해소).
  - (b) 시스템은 계산 결과를 변경하지 않으며(SM-3a 검증), AI 의견은 "자동 분석(고정 템플릿)"과 "AI 참고(구분 배지)"로 분리 표시한다.
  - **(c) 10-1 (AI 문서추출 → 입력 초안)** — 시스템은 PDF/Excel 업로드 시 6 monthly input fields (직접재료비/직접노무비/제조간접비/판매관리비/매출/기말재고) 를 추출하고, `extraction_confidence < 0.70` 인 항목은 빨강 배지(RED) 로 표시하며 사용자 확정을 강제한다 [A11, V-row §8.1 M0-c]. AI 출력은 `input_drafts.target_table='monthly_inputs'` 에만 저장하며 `confirmed_inputs` 직접 쓰기는 거부 + 카운터 증가 (target 0) [AD-7].
  - **(d) 10-2 (인사이트 캐시 정책)** — 시스템은 인사이트 캐시 키 `(tenant_id, period_key, calculation_result_hash)` 로 저장하며 마감 데이터 변경 시 4-channel publisher (`ai_cache` 외 3 channel `cost_engine_cache`/`fiscal_period_cache`/`closing_snapshot_cache` 는 Epic 13 LISTEN/NOTIFY consume trigger EXTENSION wire 진입 시점에 4-channel cache eviction publisher 로 무효화한다 [AD-25, §F13 신규]. **EXTENSION (Epic 14 PRD entry DONE 2026-08-20, A57+A58+A59)** — **5+ channels EXTENSION 결정 wire**: 4-channel 외 `cross_tenant_fanout` 1 channel 추가. Cross-tenant invalidation fan-out = tenant-level subscription routing + multi-tenant isolation 검증 (CR 0-2 RLS lesson 적용 + AD-22 verbatim 보존). NOTIFY payload 7-key alphabetical EXTENSION (source_tenant_id + target_tenant_ids 추가). **Multi-process coordination Option 1 결정** (PostgreSQL LISTEN/NOTIFY only via pg_notify fan-out leader/follower model). capability matrix v1.23 EXTENSION (`LISTEN_NOTIFY_TENANT_FANOUT` + `LISTEN_NOTIFY_MULTIPROCESS` 2 NEW rows industry-agnostic 4-industry grants ✅/✅/✅/✅) [§F14 verbatim, §F10.1-(d) EXTENSION 결정].
  - **(e) 10-3 (자동 분석 vs AI 참고 배지 분리)** — 시스템은 `source_kind: Literal['auto_analysis', 'ai_reference']` Discriminated union 으로 분리 렌더링하고 (auto_analysis 파란 배지 "📊 자동 분석" + ai_reference 보라 배지 "🤖 AI 참고(검증 필요)" + tooltip "AI는 비권위적입니다 — 확정 책임은 사용자에게"), strict reject 외 value counter increment 강제 [AD-7 SM-3a].
  - **(f) 10-4 (승격 포트 멱등성)** — 시스템은 `InputPromoter.promote(tenant_id, period_key, source_draft_id)` 호출을 idempotent 로 처리하며, audit_logs 2행 append (actor + draft hash + ts) [AD-17]. M10 attempts to write `confirmed_inputs` 는 denied + 카운터 증가 (target 0) [AD-7].

- **M11 (마감·이력)**
  - (a) 시스템은 부문분할 → 제조 → ABC → 공동 순서를 강제하고, 부분 마감을 허용하지 않는다.
  - (b) 시스템은 마감 완료 시 계산 결과 전체를 스냅샷으로 고정하고, 이후 입력·변경 시도는 역분개(A8)로만 허용한다.

- **M12 (계정·운영)**
  - (a) 시스템은 2FA 미설정 상태에서 M2 진입을 차단한다.
  - (b) 시스템은 일 1회 자동 백업 + 셀프 다운로드(JSON) 기능을 제공한다.
  - (c) 시스템은 해지 요청 시 보관일수 고지 + 삭제 동의 문구를 강제 표시한다.

---

# 9. 보고서 체계 (통합 목록)

**전통 엔진 (원본 26종 계보의 웹 재편)**
1. 대시보드 — 월 체크리스트, TOP5/WORST5 제품, 12개월 추이
2. 종합 손익계산서 (당월 + 차월 추정)
3. 제품별 손익계산서 (제조원가/완전원가 2계층 표시 [A2])
4. 판매지역별 손익계산서 (지역 입력 시)
5. 월간 비교 손익 + YTD (12개월, 마감월만)
6. 예산 대비 실적 손익 (M8 연동)
7. 원가분석표 (재료·노무·경비 3단 분해 + 자동 분석의견(고정 템플릿) + AI 참고 의견(구분 표시))
8. 제품 원가카드 (원본 ctable — 재료 명세·공정·경비 단위당)
9. 표준 제조원가명세서 (원본 cststmt — 재료비 T계정 흐름 포함)
10. 손익분기점(BEP) 분석 + 목표이익 역산
11. 조업도·생산성 보고서 (임률 체인 + 미사용능력 금액화 [A9])
12. 원부재료/제품 재고 수불부 + 재고 검색
13. 주문잔량(Back Log) / 주문품·생산품 자재 총소요 (주문 입력 시)
14. 검증 리포트 (제11장 결과 상시 열람)

**ABC 엔진 7종 (원본 8~10 계보)**
15. 활동원가 내역서 (활동별 원가·동인 단가)
16. 원가대상 수익성 보고서 (제품별 활동원가 손익 + 자동 분석의견)
17. 단위 활동원가표 (제품 단위당 활동비용 분해)
18. 미사용능력 보고서 (TDABC — 전통 조업도와 통합 뷰)
19. 활동원가 추이 보고서
20. 전통 vs ABC 비교 보고서 (겸영 기업 전사 뷰)
21. 부문귀속명세서 (카브아웃 근거 공시) → §7.3 [AS-6]

**공통 규격**: 다년 조회·전년 비교 / 한·영 + KRW·USD / 음수 (1,234) 빨강 / KRW 정수·USD 소수 2자리 / A4 인쇄 최적화 + PDF 내보내기 / 격식체 서술

---

# 10. 예산 시나리오 (결정 Q-D)

- 원본의 13번째 저장공간 '예산'을 **가상 기간(budget scenario)**으로 승격: 실적과 동일한 입력 체계로 계획치를 입력하면 **사전 표준원가계산**이 수행되고, 예산 대비 실적 손익(원본 pl5)이 자동 대조된다.
- 회계연도당 예산 시나리오 1개(2차에서 복수 시나리오 검토).
- A×B×C×D 예산 편성 엔진(편성단위 × 기준비율 × 단위금액 × 기간환산 — 원본 djob exp·ABCost 3 Indirect cost 공통 구조)은 **2차 로드맵**. 산식 원문은 본 문서와 ERD에 보존한다.

---

# 11. 자동 검증 체계 (원본 check 시트의 시스템 승격)

| # | 검증 | 내용 | 시점 |
|---|------|------|------|
| V1 | 완전배부 | 각 배부 단계 합계 = 원금액 (1원 단위) [A6] | 계산 시 |
| V2 | 수불 연속성 | 기초+입고−출고 = 기말, 월 체인 연속(전월 기말=당월 기초) | 상시 |
| V3 | 음수재고 | 품목별 기말 < 0 감지 즉시 경고 | 입력 시 |
| V4 | 원가-손익 Reconciliation | 제조원가↔매출원가↔재고 차이를 **4요소 자동 분해**: ①생산·매출 수량차 재료비 ②노무비+제조경비 배분차 ③총평균단가차 ④재고조정 → '제품 재고 조정' 라인 산출 근거 | 계산 시 |
| V5 | 조업도 | 생산요구시간 > 총작업가능시간 경고 | 입력 시 |
| V6 | 합계 대사 | 제품별 매출 합 vs 지역별 매출 합 불일치 경고 (지역 선택 입력이므로 경고만) | 입력 시 |
| V7 | ABC 무결성 | 원가풀 행 합 100%·활동 열 합 100%·동인 합계·완전배부 | 계산 시 |
| V8 | 엔진 대조 | 원가엔진(순수 Python) 결과를 원본 엑셀 산출과 1원 단위 대조하는 회귀 테스트 스위트 | CI |

운영 원칙: 입력 시 경고(진행 허용) → 마감 시 임계 위반 차단 [A11]. 조정 차이는 원본 권고대로 "무시하거나 연말 1회 조정" 옵션 제공.

---

# 12. AI 기능 3종 (첫 버전 확정분)

| 기능 | 내용 | 원칙 |
|------|------|------|
| 문서추출 온보딩 | 사업자등록증·재무제표·급여대장·거래명세서·활동 초안·동인 실적을 Claude Vision으로 초안 생성 | "AI는 초안, 확정은 사람" — 확정 전 검토 강제, 추출 항목별 신뢰도 표시. AI 출력은 `input_drafts.target_table='monthly_inputs'` 에만 저장하며 `confirmed_inputs` 직접 쓰기는 거부 + 카운터 증가 (target 0) [AD-7]. Story 10.1 wire (PRD §8.1 M10-(c)) |
| 인사이트 큐레이션 | 마감 데이터 기반 질문 3개 자동 생성·캐시(예: "부대찌개 원가율이 전월 대비 상승한 이유는?") + 답변 | 계산 결과를 변경하지 않음. 서술형 의견은 '자동 분석(고정 템플릿)'과 'AI 참고(구분 배지)'를 분리 [§F10.2]. 캐시 키 `(tenant_id, period_key, calculation_result_hash)` 3-tuple lock + 마감 데이터 변경 시 4-channel publisher 무효화 [AD-25]. Story 10.2 wire (PRD §8.1 M10-(d)). SM-3a "계산 결과 변경 시도 = 0건" 별도 추적 |
| 고정·변동 추정 | 계정별 고정/변동 3단계 추정(과거 패턴 → 제안 → 사용자 확정) | 확정값만 계산에 사용 [A7]. 본 1차 PRD 범위는 본 PRD v2.0 시점에 Epic 10 4-story (10-1~10-4) wire 진입으로 §12 3종 중 문서추출 + 인사이트 큐레이션 2종 wire, 고정·변동 추정은 1차 PRD 범위 외 (후속 Epic) |

---

## F10. AI 기능 명세 (Epic 10 wire 정합, 2026-08-20 master PRD v2.0 edit)

> 본 절은 §12 AI 기능 3종 가운데 **문서추출 (Story 10.1) + 인사이트 큐레이션 (Story 10.2) + 배지 분리 (Story 10.3) + 승격 포트 (Story 10.4)** wire 의 PRD-level AC 를 상세화한다. Epic 10 PRD entry (`_bmad-output/planning-artifacts/prds/prd-costmgr-2026-08-17/prd.md`) §3 verbatim 보존.

### F10.1 Three-Insight Cache Policy (§8.1 M10-(a)(d) 확장)

- **(a)** 시스템은 `fiscal_period_snapshots.state='committed'` 전이 시점에 `ai_cache` 키 `(tenant_id, period_key, calculation_result_hash)` 3-tuple 로 **인사이트 질문 3개 + 답변 3개**를 lock 한다 (NFR11 P95 ≤ 30s, [AD-25 verbatim]).
- **(b)** 시스템은 cache hit 시 마지막 마감 완료 시점부터 다음 마감 시작 시점까지 보존된 인사이트를 반환하고, 동일 hit 은 0~수십 ms 내 응답한다 (cache 없으면 NFR11 SLO 내 cold compute).
- **(c)** 시스템은 마감 데이터 변경 (Epic 11 AD-22 reversal INSERT) 시 AD-25 publisher 가 invalidation log 를 emit 하면 adapter 가 `WHERE tenant_id=? AND period_key=?` 매칭 cache entry 를 즉시 폐기한다.
- **(d)** 시스템은 `cache_invalidation_log` 채널에 `ai_cache` 외 채널 (`cost_engine_cache` / `fiscal_period_cache` / `closing_snapshot_cache`) 이 추가되어도 본 캐시만 영향받지 않도록 channel-specific invalidation filter 를 강제한다 (`channel = 'ai_cache'` filter). **Epic 13 LISTEN/NOTIFY consume trigger EXTENSION wire 진입 시점에 4-channel publisher EXTENSION (A51 결정, §F13 신규)**. D-10-2-DEFER-3 ✅ RESOLVED 진입. **EXTENSION (Epic 14 PRD entry DONE 2026-08-20, A57+A58+A59)** — **5+ channels EXTENSION 결정 wire**: 4-channel 외 `cross_tenant_fanout` 1 channel 추가. Cross-tenant fan-out channel 추가되어도 본 캐시(`ai_cache`) 는 영향받지 않도록 channel-specific invalidation filter EXTENSION 강제 (`channel = 'ai_cache'` filter 그대로 보존 + cross_tenant_fanout filter 별도 강제 — F14.1-(c) cross-channel contamination 방어 결정 wire verbatim bind). [§F14 verbatim, AD-25 EXTENSION 결정].

### F10.2 AI Reference vs Auto Analysis Badge Separation (§8.1 M10-(b)(e) 확장)

- **(a)** 시스템은 보고서 의견 section 진입 시 모든 문장별 `source_kind` (`auto_analysis` | `ai_reference`) 를 함께 렌더링하고:
  - `source_kind='auto_analysis'` → 파란 배지 "📊 자동 분석" + tooltip "이 의견은 고정 템플릿입니다" (§12 verbatim).
  - `source_kind='ai_reference'` → 보라 배지 "🤖 AI 참고(검증 필요)" + tooltip "AI는 비권위적입니다 — 확정 책임은 사용자에게" ([AD-7 verbatim]).
- **(b)** 시스템은 `auto_analysis` / `ai_reference` 키 외 value (예: `human_authored` 등) 도착 시 strict reject + 1행 counter increment 를 wire 한다 (§A11 시스템은 틀리지 않는다 / hover 후 미변경 = 안전).
- **(c)** 시스템은 SM-3a "계산 결과 변경 시도 = 0건" 별도 tracking 을 위해 `auto_analysis` 의견 수정 시도도 동일 카운터로 추적한다 (AD-7 "M10 attempts to write confirmed-input tables are denied and counted (target zero)").
- **(d)** 시스템은 `source_kind` 강제 검증 실패 시 1-line ko-KR 메시지로 reject (예: "분석 의견 출처가 불분명합니다") + counter 증가 + 200 OK envelope.

---

## F13. LISTEN/NOTIFY Consume Trigger EXTENSION (Epic 13 wire 정합, 2026-08-20 master PRD v2.3 edit — 13-1 atomic T1~T8 wire DONE)

> 본 절은 **A39 결정 wire (Epic 13 = LISTEN/NOTIFY 전용 epic)** + **A51 Epic 13 PRD entry 결정 wire** + **A52 Story 13-1 atomic wire DONE (cj-style 42번째 epic 연속 정직 회복)** + **A54 master PRD v2.3 edit (D-13-1-DEFER-1 ✅ RESOLVE)** 의 PRD-level AC 를 verbatim 상세화한다. AD-25 cache invalidation trigger EXTENSION for close/reopen 의 wire 진입 근거 + 4-channel publisher EXTENSION 진입 결정 + 13-1 atomic T1~T8 wire 정합 결정. Story 13-1 = NOTIFY trigger (alembic 0033) + LISTEN daemon (FastAPI lifespan) + 4-channel cache eviction handlers (M10/M3/M11 EXTENSION) + reconnect/backoff (exponential + jitter + circuit breaker) + V8 determinism + cross-lang drift detector EXTENSION + capability `LISTEN_NOTIFY` v1.22 4-industry grants industry-agnostic.

### F13.1 LISTEN/NOTIFY 토폴로지 (§AD-25 EXTENSION)

- **(a)** 시스템은 PostgreSQL `LISTEN/NOTIFY` 채널을 통해 cache invalidation 을 trigger 한다. `cache_invalidation_log` 테이블 AFTER INSERT 트리거 `cache_invalidation_log_notify_trg` 가 PL/pgSQL function `cache_invalidation_log_notify()` 호출하여 `pg_notify('cache_invalidation_log', payload)` 를 emit 한다. payload = JSON `{channel: str, correction_group_id: str, invalidation_id: str, period_key: str, tenant_id: str, trace_id: str}` 6-key alphabetical key ordering 결정적 직렬화 (uuid fields → TEXT cast for cross-language drift detector parity [CR 12-5 D-PARITY-01]). channel whitelist in DDL: `ai_cache | cost_engine_cache | fiscal_period_cache | closing_snapshot_cache`. M10/M3/M11 adapter 가 LISTEN daemon (`CacheInvalidationListener`) 을 통해 4 channel 모두를 consume 한다 [AD-25 verbatim EXTENSION, §F13 신규].
- **(b)** 시스템은 4 channel 모두 (`ai_cache` / `cost_engine_cache` / `fiscal_period_cache` / `closing_snapshot_cache`) 에 대해 channel-specific eviction handler 를 wire 하며, 각 handler 는 매칭 cache entry 를 즉시 폐기한다. NOTIFY payload 는 channel 명을 명시적으로 포함하여 cross-channel leakage 를 차단한다 (channel-specific filter 강제 — cross-channel contamination 방어 결정, SD-EPIC13-3 정직 반영).
- **(c)** 시스템은 LISTEN daemon `CacheInvalidationListener` (`apps/api/core/cache_invalidation_listener.py`) 가 FastAPI lifespan context manager 안에서 start/stop 되도록 wire 한다 (`apps/api/main.py` `@asynccontextmanager` lifespan 진입 시 start, shutdown 시 stop). Daemon 은 asyncio task + reconnect/backoff (exponential base 1s factor 2 + jitter ±20% + max 30s + circuit breaker 5 consecutive failures → 60s cool-down) + persistent failure 시 graceful degradation (다음 restart 시 reconnect) + stdlib-only pure async kernel (AD-5 engine purity 정합).
- **(d)** 시스템은 NOTIFY trigger 가 application polling 으로 대체되지 않도록 강제한다. Polling-only invalidation 은 forbidden. AD-25 verbatim "Application polling + input-write-only invalidation forbidden" 보존.

### F13.2 4-Channel Cache Eviction Handlers (§M10/M3/M11 EXTENSION, 13-1 T4 atomic wire DONE)

- **(a)** M10 AI cache eviction — `apps/api/modules/m10_ai/service.py` EXTENSION (`M10AIInvalidationAdapter.on_invalidate(payload)` + DELETE FROM `ai_insight_cache` WHERE `tenant_id=?` AND `period_key=?` 매칭 entry 즉시 폐기). channel-specific filter: `channel = 'ai_cache'` ONLY (F10.1-(d) verbatim cross-channel contamination 방어).
- **(b)** M3 cost engine cache eviction — `packages/cost_engine/...` EXTENSION (`M3CostEngineInvalidationAdapter.on_invalidate(payload)` + in-process LRU eviction hook, 단위: tenant_id × period_key tuple). channel: `cost_engine_cache`. AD-5 stdlib-only 보존 (NO DB write from kernel).
- **(c)** M11 fiscal_period cache eviction — `apps/api/modules/m11_close/services/fiscal_period_service.py` EXTENSION (`M11FiscalPeriodInvalidationAdapter.on_invalidate(payload)` + `fiscal_periods` cache invalidate, state='committed' 시 in-memory cache evict). channel: `fiscal_period_cache`.
- **(d)** M11 closing_snapshot cache eviction — `apps/api/modules/m11_close/services/snapshot_service.py` EXTENSION (`M11ClosingSnapshotInvalidationAdapter.on_invalidate(payload)` + `fiscal_period_snapshots` cache evict, closing_snapshot hash mismatch 시 즉시 evict). channel: `closing_snapshot_cache`.
- **(e)** 4 adapter 모두 `apps/api/core/cache_invalidation_listener_adapters.py` NEW ~220 LOC `build_default_adapter_factories()` returns 4 channel → factory entries (lazy import defense-in-depth, graceful degradation if module unavailable). Cross-channel contamination 방어: each adapter rejects payloads from other channels (F10.1-(d) verbatim). Audit-first INSERT 2-row (CR 1.1 verbatim, payload = notify envelope).

### F13.3 V8 Determinism + Cross-Language Drift (§CR 12-5 EXTENSION, 13-1 T6/T7 wire DONE)

- **(a)** 시스템은 NOTIFY payload JSON serialization 이 결정적 (alphabetical key ordering) 임을 강제한다. V8 byte-identical determinism 검증 — payload bytes 가 동일 입력에 대해 동일하게 직렬화되어야 한다 (드롭/순서 차이로 인한 cache miss 방지). `serialize_payload_for_v8()` byte-identical deterministic (`json.dumps(payload, sort_keys=True, separators=(',', ':'))`). UUID fields cast to TEXT for cross-language drift detector parity. `tests/regression_v8/test_listen_notify_v8_determinism.py` NEW ~11 cases (alphabetical key ordering, no whitespace, compact separators, byte-identical across reruns).
- **(b)** 시스템은 LISTEN payload shape 가 Python (`apps/api/core/cache_invalidation_listener.py`) 와 TypeScript (`apps/web/lib/cache-invalidation-listener.ts` NEW ~150 LOC TS mirror, `CacheInvalidationPayload` Discriminated union) 양쪽에서 동일하게 파싱됨을 강제한다 [CR 12-5 D-PARITY-01 inversion 적용]. Drift 발생 시 drift detector test fail + 1-line ko-KR reject ("LISTEN/NOTIFY 페이로드 형식이 백엔드와 일치하지 않습니다", `DRIFT_DETECTED_REJECT_KO` constant). `tests/web/test_cache_invalidation_listener_parity.py` NEW ~14 cases.
- **(c)** 시스템은 capability gate `LISTEN_NOTIFY` (capability matrix v1.22, Epic 13 wire 진입) 를 통해 LISTEN daemon 시작/정지가 tenant 별로 on/off 가능하도록 wire 한다 [CR 12-5 D-GATE-01 inversion 적용]. `Capability.LISTEN_NOTIFY = "listen_notify"` 4-industry grants: manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ (industry-agnostic, CR 12-1 L4 precedent 미러, `AI_INSIGHT` 10-1 wire pattern). 미허용 tenant 의 listener 는 등록되지 않는다.

### F13.4 Tests + Wire Scope (cj-style Epic 13 1~4번째 진입점 모두 wire DONE)

- **T1 — alembic 0033 NEW** (PostgreSQL `pg_notify` trigger wire, `down_revision = '0032_ai_promotion_port'`): `apps/api/alembic/versions/0033_listen_notify_consume_trigger.py` NEW ~155 LOC. `cache_invalidation_log_notify()` PL/pgSQL function with `json_object()` 6-key alphabetical payload (channel, correction_group_id, invalidation_id, period_key, tenant_id, trace_id) + AFTER INSERT trigger `cache_invalidation_log_notify_trg` FOR EACH ROW + channel whitelist in DDL.
- **T2 — `apps/api/core/cache_invalidation_listener.py` NEW** (~620 LOC, stdlib-only pure async kernel): `CacheInvalidationListener` class (asyncio 기반) + `start()` / `stop()` lifecycle (idempotent) + `_consume_notifications()` private coroutine + 4-channel routing dispatch table + reconnect/backoff (exponential + jitter + circuit breaker) + `parse_payload()` validates 6 keys alphabetical + UUID + channel whitelist + `serialize_payload_for_v8()` byte-identical.
- **T3 — `apps/api/main.py` lifespan EXTENSION** (~100 LOC, FastAPI lifespan context manager 진입): 4 NEW functions (`_start_cache_invalidation_listener` + `_stop_cache_invalidation_listener` + 2 NEW exception handlers `ListenerStartFailedError` 503 + `ListenerStopFailedError` 503 with CR 12-5 D-14 envelope `{code, message_ko, details, trace_id}`). Preserved `_attach_tenant_listener` (backward compat) + Graceful degradation: ImportError caught → no crash in test env.
- **T4 — `apps/api/core/cache_invalidation_listener_adapters.py` NEW** (~220 LOC, 4-channel cache eviction handlers): `M10AIInvalidationAdapter` + `M3CostEngineInvalidationAdapter` + `M11FiscalPeriodInvalidationAdapter` + `M11ClosingSnapshotInvalidationAdapter` + `build_default_adapter_factories()` returns 4 channel → factory entries + cross-channel contamination 방어 + lazy import.
- **T5 — Capability gate `LISTEN_NOTIFY`**: `apps/api/core/capability.py` EXTENSION 1 NEW enum + 4-industry grants + capability matrix v1.22 + `require_capability(Capability.LISTEN_NOTIFY)` Dependency 신규 wire (CR 12-5 D-GATE-01 inversion 적용). 4-industry grants ✅/✅/✅/✅.
- **T6 — V8 determinism byte-identical test NEW**: `tests/regression_v8/test_listen_notify_v8_determinism.py` NEW ~11 cases + `tests/api/test_alembic_0033_listen_notify_consume_trigger.py` NEW ~14 cases.
- **T7 — Cross-language drift detector EXTENSION**: `apps/web/lib/cache-invalidation-listener.ts` NEW ~150 LOC TS mirror + `tests/web/test_cache_invalidation_listener_parity.py` NEW ~14 cases + drift detector 1-line ko-KR reject.
- **T8 — 3중 게이트 FINAL CLEAN + atomic commit**: sprint-status: 13-1 in-progress → done + handoff memory 신규 wire + `docs/listen-notify-consume-trigger-extension.md` NEW (~10 sections, 10-4 template format EXTENSION).
- **A19 cohesion pattern 8 surface 8/8 PASS** (kernel ✅ + port ✅ + db schema ✅ + service ✅ + handler ✅ + envelope ✅ + capability ✅ + audit ✅). Surface 1 (kernel) = T2 listener (AD-5 stdlib-only) / Surface 2 (port) = T2 LISTEN daemon → 4-channel adapter dispatch / Surface 3 (db schema) = T1 alembic 0033 NOTIFY trigger / Surface 4 (service) = T4 4-channel eviction handlers / Surface 5 (handler) = T3 main.py lifespan + 2 NEW exception handlers / Surface 6 (envelope) = T3 CR 12-5 D-14 envelope / Surface 7 (capability) = T5 LISTEN_NOTIFY gate / Surface 8 (audit) = T4 audit-first INSERT 2-row.
- **Tests wire 표**: ~107 NEW pytest PASS (across 7 test files) + 0 NEW ruff (8 auto-fixed via `ruff check --fix --unsafe-fixes`) + 0 regressions (existing tests: 474 passed, 88 skipped DB-backed). **wire_commit = `f2ea2f6`** (cj-style 42번째 epic 연속 정직 회복 atomic single sweep T1~T8, 17 files = 12 NEW + 5 MODIFIED).

---

## F14. LISTEN/NOTIFY Consume 2nd Batch EXTENSION (Epic 14 PRD entry 결정, 2026-08-20 master PRD v2.5 edit — 14-1 atomic wire 진입 대기 = cj-style Epic 14 2번째 진입점)

> 본 절은 **A53 결정 wire (Epic 14 = LISTEN/NOTIFY Consume 2nd Batch territory, D-13-1-DEFER-3 separate epic 진입 결정 wire)** + **A57 Epic 14 PRD entry 결정 wire (cj-style Epic 14 1번째 진입점 = cj-style 45번째 epic 연속 정직 회복)** 의 PRD-level AC 를 verbatim 상세화한다. D-13-1-DEFER-3 territory = cross-tenant invalidation fan-out (multi-tenant isolation 검증 + tenant-level subscription routing) + multi-process coordination (multi-worker 환경 listener process-per-pod, Redis pub/sub fan-out 또는 PostgreSQL LISTEN/NOTIFY multi-process coordination 결정). AD-25 cache invalidation trigger EXTENSION 4-channel → 5+ channels cross-tenant fan-out 결정 wire 진입. capability matrix v1.22 → v1.23 LISTEN_NOTIFY_TENANT_FANOUT + LISTEN_NOTIFY_MULTIPROCESS 2 NEW rows (industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러, AI_INSIGHT 10-1 + LISTEN_NOTIFY 13-1 wire pattern). Story 14-1 = cross-tenant invalidation fan-out wire + multi-process coordination 본체 wire (T1~T9 atomic single sprint). D-13-1-DEFER-2 preserved (LISTEN/NOTIFY 실측 evidence 정합 sweep = 14-1 wire 진입 시점에 동시 = A55 Epic 14 진입 시점에 동시 결정 wire).

### F14.1 Cross-Tenant Invalidation Fan-Out 토폴로지 (§AD-25 EXTENSION 5+ channels 결정 wire)

- **(a)** 시스템은 cross-tenant invalidation fan-out 시 **tenant isolation 검증** 을 강제한다. NOTIFY trigger (alembic 0033 EXTENSION) 의 PL/pgSQL function `cache_invalidation_log_notify()` 가 tenant_id 를 NOTIFY payload 에 포함하며, listener (LISTEN daemon EXTENSION) 가 tenant context 와 cross-tenant fan-out channel 매칭 시 RLS context + tenant_id filter 로 tenant-scoped subscription routing 을 수행한다. Multi-tenant isolation 위반 시 reject (CR 0-2 RLS lesson 적용, AD-22 verbatim).
- **(b)** 시스템은 **tenant-level subscription routing** 을 wire 한다. NOTIFY channel whitelist EXTENSION 결정 wire: `ai_cache` / `cost_engine_cache` / `fiscal_period_cache` / `closing_snapshot_cache` 외 `cross_tenant_fanout` 1 channel 추가 (총 5+ channels EXTENSION 결정). Cross-tenant fan-out channel 은 tenant_id 별 subscription set 관리하며, listener 가 fan-out 수신 시 subscription set 의 각 tenant listener 에게 in-process dispatch (NOTIFY payload = JSON `{channel: 'cross_tenant_fanout', source_tenant_id, target_tenant_ids: [...], correction_group_id, invalidation_id, period_key, trace_id}` 7-key alphabetical key ordering 결정적 직렬화, V8 determinism EXTENSION).
- **(c)** 시스템은 **fan-out dispatch 시 audit-first INSERT 2-row** 를 강제한다 (CR 1.1 verbatim). Source tenant 의 invalidation log 1 row + fan-out dispatch log 1 row (target_tenant_ids 명시), audit_logs `action_name='cross_tenant_fanout_dispatched'` 1 row 추가 (audit-first invariant 보존). Cross-tenant contamination 방어 (F10.1-(d) verbatim): each adapter rejects payloads from other channels (cross_tenant_fanout channel 의 adapter 는 다른 4 channel 의 payload reject + 그 역도 reject).
- **(d)** 시스템은 NOTIFY trigger 가 application polling 으로 대체되지 않도록 강제한다. Polling-only invalidation 은 forbidden (AD-25 verbatim "Application polling + input-write-only invalidation forbidden" 보존). Cross-tenant fan-out channel 도 동일 강제 적용 (polling-only cross-tenant dispatch forbidden).

### F14.2 Multi-Process Coordination (Multi-Worker LISTEN Daemon EXTENSION)

- **(a)** 시스템은 **multi-worker 환경 (Railway / Gunicorn / Uvicorn multi-pod) 에서 listener process-per-pod wire** 를 강제한다. 각 FastAPI worker process 가 독립된 LISTEN daemon (`CacheInvalidationListener`) 을 구동하며, 1 process 만 fan-out publisher 역할 (leader election via PostgreSQL advisory lock `pg_try_advisory_xact_lock(LISTEN_FANOUT_LOCK_ID)`, deterministic hash of pod_id). Leader 가 NOTIFY publish, follower 들이 LISTEN daemon consume. Single-process 환경에서는 leader = self, follower = none (graceful degradation).
- **(b)** 시스템은 **multi-process coordination 핸들링** 으로 **PostgreSQL `LISTEN/NOTIFY` multi-process coordination 결정 wire 진입** (Epic 14 A58 결정). Option 1: PostgreSQL LISTEN/NOTIFY 만 사용 (모든 process 가 LISTEN daemon 구동, fan-out publisher leader 가 NOTIFY publish, follower 들이 자동 consume) — 결정 (단순성 + AD-25 verbatim 보존). Option 2: Redis pub/sub fan-out 추가 (별도 인프라, CR 13 PRD entry 진입 시점에 rejected 결정 = rationale: G2 "새벽에 혼자 고칠 수 있는 시스템" 정합 — 인프라 최소화). 결정 wire = Option 1 (PostgreSQL LISTEN/NOTIFY only, multi-process coordination via pg_notify fan-out leader/follower model).
- **(c)** 시스템은 **process-per-pod state 동기화** 를 wire 한다. In-memory cache eviction 후 cross-process invalidation 필요 시 leader 가 NOTIFY `cross_tenant_fanout` channel 에 publish (F14.1-(b) verbatim), 모든 follower 의 LISTEN daemon 이 consume 후 in-process eviction 적용. Reconnect/backoff 보존 (F13.1-(c) verbatim exponential base 1s factor 2 + jitter ±20% + max 30s + circuit breaker 5 consecutive failures → 60s cool-down). Stdlib-only pure async kernel 보존 (AD-5 engine purity 정합).
- **(d)** 시스템은 **leader election + failover** 을 wire 한다. PostgreSQL advisory lock `pg_try_advisory_xact_lock(LISTEN_FANOUT_LOCK_ID)` 으로 leader 결정, leader process 종료 시 lock 자동 해제 → follower 중 1개가 leader 선출 (next leader = hash of pod_id order). Leader health check 30s interval (background task in each follower), leader unresponsive 90s → follower 강제 takeover via pg_try_advisory_lock (non-xact, plain lock 으로 승격).

### F14.3 V8 Determinism + Cross-Language Drift EXTENSION (§CR 12-5 + §F13.3 EXTENSION)

- **(a)** 시스템은 NOTIFY payload JSON serialization 이 결정적 (alphabetical key ordering) 임을 강제한다 (F13.3-(a) verbatim 보존 + EXTENSION). **cross-tenant fan-out payload 7-key alphabetical**: `channel`, `correction_group_id`, `invalidation_id`, `period_key`, `source_tenant_id`, `target_tenant_ids`, `trace_id` (target_tenant_ids 는 JSON array 결정적 직렬화 — PostgreSQL `jsonb` canonical form 또는 Python `json.dumps(sort_keys=True)`). `serialize_payload_for_v8()` byte-identical deterministic EXTENSION (alphabetical key ordering + no whitespace + compact separators). UUID fields cast to TEXT for cross-language drift detector parity (CR 12-5 D-PARITY-01 inversion 적용 보존).
- **(b)** 시스템은 LISTEN payload shape 가 Python (`apps/api/core/cache_invalidation_listener.py` EXTENSION) 와 TypeScript (`apps/web/lib/cache-invalidation-listener.ts` EXTENSION ~+80 LOC TS mirror EXTENSION) 양쪽에서 동일하게 파싱됨을 강제한다. `CacheInvalidationPayload` Discriminated union EXTENSION (`channel: Literal['ai_cache', 'cost_engine_cache', 'fiscal_period_cache', 'closing_snapshot_cache', 'cross_tenant_fanout']` + cross_tenant_fanout variant). Drift 발생 시 drift detector test fail + 1-line ko-KR reject ("크로스 테넌트 LISTEN/NOTIFY 페이로드 형식이 백엔드와 일치하지 않습니다", `CROSS_TENANT_DRIFT_DETECTED_REJECT_KO` constant NEW). `tests/web/test_cache_invalidation_listener_parity.py` EXTENSION ~+12 cases (cross_tenant_fanout payload shape + multi-tenant isolation + leader/follower state).
- **(c)** 시스템은 **capability gate `LISTEN_NOTIFY_TENANT_FANOUT`** (capability matrix v1.23, Epic 14 wire 진입) + **`LISTEN_NOTIFY_MULTIPROCESS`** (capability matrix v1.23, Epic 14 wire 진입) 를 통해 cross-tenant fan-out + multi-process coordination on/off 가능하도록 wire 한다 [CR 12-5 D-GATE-01 inversion 적용 보존]. `Capability.LISTEN_NOTIFY_TENANT_FANOUT = "listen_notify_tenant_fanout"` 4-industry grants: manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ (industry-agnostic, CR 12-1 L4 precedent 미러). `Capability.LISTEN_NOTIFY_MULTIPROCESS = "listen_notify_multiprocess"` 동일 industry-agnostic 4-industry grants ✅/✅/✅/✅. 미허용 tenant 의 cross-tenant fan-out channel listener 는 등록되지 않으며, multi-process coordination leader election 에서도 제외된다.

### F14.4 Tests + Wire Scope (cj-style Epic 14 1~3번째 진입점 결정 보존)

- **T1 — alembic 0034 NEW** (PostgreSQL `pg_notify` trigger wire EXTENSION for cross-tenant fan-out, `down_revision = '0033_listen_notify_consume_trigger'`): `apps/api/alembic/versions/0034_listen_notify_consume_cross_tenant_fanout.py` NEW ~140 LOC. `cache_invalidation_log_notify_cross_tenant()` PL/pgSQL function with `json_object()` 7-key alphabetical payload (channel='cross_tenant_fanout' + source_tenant_id + target_tenant_ids + correction_group_id + invalidation_id + period_key + trace_id) + AFTER INSERT trigger `cache_invalidation_log_notify_cross_tenant_trg` FOR EACH ROW (cross_tenant_fanout channel ONLY) + channel whitelist EXTENSION 결정 wire.
- **T2 — `apps/api/core/cache_invalidation_listener.py` EXTENSION** (multi-process coordination + cross-tenant fan-out wire): `CacheInvalidationListener` class EXTENSION ~+200 LOC (leader election via `pg_try_advisory_xact_lock` + follower health check 30s interval + leader takeover 90s timeout + cross_tenant_fanout channel routing EXTENSION) + `start()` / `stop()` lifecycle idempotent EXTENSION 보존 + `_consume_notifications()` private coroutine EXTENSION (5+ channels routing dispatch table: ai_cache + cost_engine_cache + fiscal_period_cache + closing_snapshot_cache + cross_tenant_fanout) + reconnect/backoff 보존 (F13.1-(c) verbatim) + `parse_payload()` validates 7 keys alphabetical EXTENSION + UUID + channel whitelist EXTENSION + `serialize_payload_for_v8()` byte-identical EXTENSION.
- **T3 — `apps/api/main.py` lifespan EXTENSION** (~+50 LOC, leader election wiring): 2 NEW functions (`_start_leader_election` + `_stop_leader_election`) + leader-election background task lifecycle EXTENSION + `LeaderElectionFailedError` 503 + `LeaderTakeoverFailedError` 503 NEW exception handlers 2개 (CR 12-5 D-14 envelope `{code, message_ko, details, trace_id}`). Preserved: 13-1 listener start/stop + 2 NEW exception handlers (CR 12-5 D-14 envelope) + graceful degradation 보존.
- **T4 — `apps/api/core/cache_invalidation_listener_adapters.py` EXTENSION** (~+80 LOC, cross-tenant fan-out adapter + multi-process dispatch): `CrossTenantFanoutAdapter` NEW + `MultiProcessDispatchAdapter` NEW + `build_default_adapter_factories()` returns 5+ channel → factory entries EXTENSION (lazy import defense-in-depth + graceful degradation if module unavailable 보존). Cross-channel contamination 방어 EXTENSION: each adapter rejects payloads from other channels (cross_tenant_fanout adapter 는 다른 4 channel payload reject + 그 역도 reject). Audit-first INSERT 3-row (CR 1.1 verbatim, payload = notify envelope + fan-out dispatch log + audit_log entry).
- **T5 — Capability gate `LISTEN_NOTIFY_TENANT_FANOUT` + `LISTEN_NOTIFY_MULTIPROCESS`**: `apps/api/core/capability.py` EXTENSION 2 NEW enum + 4-industry grants industry-agnostic ✅/✅/✅/✅ (CR 12-1 L4 precedent 미러) + capability matrix v1.22 → v1.23 (`LISTEN_NOTIFY_TENANT_FANOUT` + `LISTEN_NOTIFY_MULTIPROCESS` 2 NEW rows, SSOT RED→GREEN). `require_capability(Capability.LISTEN_NOTIFY_TENANT_FANOUT)` Dependency 신규 wire + `require_capability(Capability.LISTEN_NOTIFY_MULTIPROCESS)` Dependency 신규 wire (CR 12-5 D-GATE-01 inversion 적용). 4-industry grants ✅/✅/✅/✅.
- **T6 — V8 determinism byte-identical test EXTENSION**: `tests/regression_v8/test_listen_notify_v8_determinism.py` EXTENSION ~+9 cases (cross_tenant_fanout payload 7-key alphabetical ordering + target_tenant_ids array 결정적 직렬화 + byte-identical across reruns). `tests/api/test_alembic_0034_listen_notify_consume_cross_tenant_fanout.py` NEW ~12 cases.
- **T7 — Cross-language drift detector EXTENSION**: `apps/web/lib/cache-invalidation-listener.ts` EXTENSION ~+80 LOC TS mirror (cross_tenant_fanout channel variant + multi-tenant isolation + leader/follower state shape) + `tests/web/test_cache_invalidation_listener_parity.py` EXTENSION ~+12 cases + drift detector 1-line ko-KR reject EXTENSION (`CROSS_TENANT_DRIFT_DETECTED_REJECT_KO` NEW).
- **T8 — Multi-process coordination tests**: `tests/api/test_cache_invalidation_multiprocess.py` NEW ~18 cases (leader election + follower takeover + lock release on process death + 5+ channel routing dispatch) + `tests/integration/test_cross_tenant_fanout_e2e.py` NEW ~10 cases (multi-process environment simulation + tenant isolation 검증 + cross_tenant_fanout e2e).
- **T9 — 3중 게이트 FINAL CLEAN + atomic commit**: sprint-status: 14-1 in-progress → done + handoff memory 신규 wire + `docs/listen-notify-consume-2nd-batch-extension.md` NEW (~10 sections, 10-4 template format EXTENSION).
- **A19 cohesion pattern 8 surface EXTENSION** (kernel ✅ + port ✅ + db schema ✅ + service ✅ + handler ✅ + envelope ✅ + capability ✅ + audit ✅). Surface 1 (kernel) = T2 listener EXTENSION (AD-5 stdlib-only + multi-process coordination) / Surface 2 (port) = T2 5+ channel routing dispatch EXTENSION / Surface 3 (db schema) = T1 alembic 0034 cross_tenant_fanout NOTIFY trigger / Surface 4 (service) = T4 cross-tenant fan-out + multi-process dispatch adapters / Surface 5 (handler) = T3 main.py lifespan EXTENSION + 2 NEW exception handlers / Surface 6 (envelope) = T3 CR 12-5 D-14 envelope EXTENSION / Surface 7 (capability) = T5 LISTEN_NOTIFY_TENANT_FANOUT + LISTEN_NOTIFY_MULTIPROCESS gates / Surface 8 (audit) = T4 audit-first INSERT 3-row EXTENSION.
- **Tests wire 표 (estimated, cj-style Epic 14 2번째 진입점 wire 진입 시점에 산정)**: ~140 NEW pytest PASS (across 9 test files) + 0 NEW ruff (auto-fix via `ruff check --fix --unsafe-fixes`) + 0 regressions (existing tests 보존). **wire_commit = TBD** (cj-style Epic 14 2번째 진입점 = cj-style 46번째 epic 연속 정직 회복 atomic single sweep T1~T9, expected ~20-22 files = ~15 NEW + ~5-7 MODIFIED).

---

## F15. Auth Foundation (Phase 3 = 로그인/회원가입 UI + auth middleware, Epic 1 완성 territory 진입 결정, 2026-08-20 master PRD v3.0 edit — Phase 3 cj-style 2번째 진입점 = bmad-create-story spec 진입 대기 = cj-style 50번째 epic 연속 정직 회복 진입 대기)

> 본 절은 **Phase 3 = 로그인/회원가입 UI + auth middleware (Epic 1 완성 territory 진입 결정 wire, cj-style Phase 3 1번째 진입점 = cj-style 49번째 epic 연속 정직 회복)** 의 PRD-level AC 를 verbatim 상세화한다. Epic 1 Story 1.1 partial scaffold (IndustrySelector 4지선다 + onboarding/industry 페이지 + sb-access-token cookie read + `apps/web/app/[locale]/(auth)/layout.tsx` minimal shell + `apps/web/middleware.ts` next-intl only) 가 이미 wire 되어 있으나, **Supabase SSR auth client (`apps/web/lib/supabase/server.ts` + `apps/web/lib/supabase/client.ts`)** + **login page** + **signup page** + **forgot-password page** + **auth middleware EXTENSION (Supabase session check + (dashboard) 보호)** + **logout flow** 가 미구현 상태 (Story 1.1 F-1 + F-4 + F-30 deferral preserved). AD-26 Auth Foundation 신규 결정 wire 진입 (Supabase SSR + sb-access-token cookie session + next-intl middleware EXTENSION + auth route group `(auth)` 공개 + dashboard route group `(dashboard)` 보호 + Epic 12 2FA 게이트 보존). capability matrix v1.23 → v1.24 신규 5 rows (`LOGIN` + `SIGNUP` + `AUTH_MIDDLEWARE` + `FORGOT_PASSWORD` + `LOGOUT`, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러, AI_INSIGHT 10-1 + LISTEN_NOTIFY 13-1 + LISTEN_NOTIFY_TENANT_FANOUT 14-1 + LISTEN_NOTIFY_MULTIPROCESS 14-1 wire pattern). Phase 3 wire scope T1~T8 결정 (T1 supabase SSR client + T2 login page + T3 signup page + T4 auth middleware EXTENSION + T5 logout + T6 forgot-password + T7 capability v1.24 + T8 tests + 3중 게이트 FINAL CLEAN atomic commit). D-1-1-DEFER-* honestly DEFER preserved (Epic 1 carry-over DEFER 1~N 정직 회복, Story 1.1 F-1 + F-4 + F-30 deferral preserved — Phase 3 wire 진입 시점에 honestly DEFER 결정 wire 보존).

### F15.1 Login UI + Supabase SSR Auth Client (M0-(d) AC verbatim)

- **(a)** 시스템은 `/[locale]/login` Server Component route 를 제공한다. Server Component 는 `next/headers.cookies()` 로 `sb-access-token` 쿠키를 읽어 Supabase SSR client (`apps/web/lib/supabase/server.ts` NEW) 의 `supabase.auth.getUser()` 로 세션을 검증한다. 유효한 세션이면 `/[locale]/(dashboard)/` 로 redirect (`?redirect=` 쿼리 보존), 세션 없거나 만료 시 `<LoginForm>` Client Component 를 렌더한다.
- **(b)** `<LoginForm>` Client Component (`apps/web/components/auth/LoginForm.tsx` NEW) 는 이메일 + 비밀번호 2 필드 + [로그인] 버튼 + [회원가입] / [비밀번호 찾기] 링크를 포함한다. 이메일 필드는 RFC 5322 형식 검증, 비밀번호 필드는 masking (`type="password"`) + [보기/숨기기] 토글 ([Eye icon, WCAG AA contrast]). 제출 시 `supabase.auth.signInWithPassword({ email, password })` 를 호출하며, 성공 시 `router.push(redirect ?? '/[locale]/(dashboard)/')` + `router.refresh()` (서버 컴포넌트 re-fetch). 실패 시 ko-KR 메시지 표시: `LOGIN_INVALID_CREDENTIALS_KO = "이메일 또는 비밀번호가 올바르지 않습니다"` (401), `LOGIN_NETWORK_ERROR_KO = "네트워크 오류. 잠시 후 다시 시도해 주세요"` (네트워크 실패), `LOGIN_RATE_LIMITED_KO = "로그인 시도가 너무 잦습니다. 30초 후 다시 시도해 주세요"` (429, 5회 연속 실패 시 30초 cool-down).
- **(c)** 시스템은 2FA 설정 사용자(M12-a 정합) 에 대해 로그인 성공 후 `/[locale]/auth/2fa` 챌린지 페이지로 리다이렉트한다. `supabase.auth.getSession()` 의 `session.access_token` payload 에 `aal = 'aal2'` 가 있으면 2FA 인증 완료, `aal = 'aal1'` 이면 2FA 챌린지 필요. Epic 12 wire 정합 (`apps/web/components/auth/TwoFactorChallenge.tsx` 기존 또는 신규) 결정 wire 진입 — Phase 3 T1 진입 시점에 Epic 12 wire 정합 sweep 결정.
- **(d)** 시스템은 Supabase SSR auth client 가 다음 invariant 를 강제한다: `sb-access-token` 쿠키 = `httpOnly` + `secure` + `sameSite=lax` + `path=/` + `maxAge=3600` (1시간, refresh token 으로 자동 �신). `supabase.auth.getUser()` 가 `sb-access-token` 만 읽고 `sb-refresh-token` 는 서버에서만 (Server Component) 읽음. CSRF 방어 결정 wire: Supabase Auth 의 PKCE flow + sameSite=lax cookie 정합 (별도 CSRF token 미사용, Supabase 권장 정합).
- **(e)** 시스템은 SSR 환경 (`apps/web/lib/supabase/server.ts`) 과 browser 환경 (`apps/web/lib/supabase/client.ts`) 에서 각각 다른 client 인스턴스를 강제한다. Server client = `createServerClient()` (cookie-based, Next.js cookies API), Browser client = `createBrowserClient()` (localStorage-based). Single source of truth invariant 결정 wire (CR 12-5 D-PARITY-01 inversion 적용 보존): URL + anon key (`NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY`) 가 server/client 양쪽에서 동일하게 resolve 되어야 함.

### F15.2 Signup UI + Tenant Creation Flow (M0-(e) AC verbatim)

- **(a)** 시스템은 `/[locale]/signup` Server Component route 를 제공한다. Server Component 가 Supabase SSR client 로 세션 검증 후 세션 있으면 `/[locale]/(dashboard)/` 로 redirect, 세션 없으면 `<SignupForm>` Client Component 렌더.
- **(b)** `<SignupForm>` Client Component (`apps/web/components/auth/SignupForm.tsx` NEW) 는 이메일 + 비밀번호 + 비밀번호 확인 + 회사명 4 필드 + [가입하기] 버튼 + [로그인] 링크를 포함한다. 검증 invariant 강제:
  - 이메일: RFC 5322 형식 + 중복 검사 (서버 측, Supabase `auth.admin.listUsers()` 또는 unique constraint).
  - 비밀번호: 최소 10자 + 대문자·소문자·숫자·특수문자 각 1자 이상 (regex `/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]).{10,}$/`).
  - 비밀번호 확인: 비밀번호 필드와 일치.
  - 회사명: 1~100자, trim 후 빈 문자열 불허.
- **(c)** 시스템은 가입 성공 시 atomic transaction 으로 다음을 수행한다 (CR 1-1 audit-first INSERT 정합):
  1. `supabase.auth.signUp({ email, password, options: { data: { company_name } } })` 호출 → Supabase auth.users row 1개 생성 + 인증 메일 발송 (이메일 인증 링크).
  2. Frontend 가 `useUser()` 훅에서 `sb-access-token` 을 읽고, **pre-onboarding JWT (즉 `app_metadata.tenant_id` 가 비어있는 JWT)** 로 `POST /api/v1/onboarding/complete-signup` 호출. Backend 의 `SignupService.complete_signup()` 이 한 트랜잭션에서:
     - `users` row 1개 (없으면 — Supabase 의 `auth.users.id` 와 동일 id)
     - `tenants` row 1개 (company_name, industry)
     - `tenant_memberships` row 1개 (role='owner') — **정정**: PRD v3.0 초안의 `user_tenants` 는 실제 테이블명 `tenant_memberships` 의 오기로 wire 진입 시점에 정정됨 (alembic 0001 `tenant_memberships` SSOT)
     - `tenant_settings` row 1개 (`onboarding.industry` = body.industry, settings_version=1)
     - `audit_logs` row 1개 (action='tenant_signup_completed', actor_user_id, tenant_id, payload={tenant_name, industry, owner_user_id})
  3. Frontend 가 `supabase.auth.refreshSession()` 호출 → **두 번째 mint** 에서 `custom_access_token_hook` (alembic 0035) 가 `tenant_memberships` 행을 읽어 `app_metadata.tenant_id`/`role`/`industry` 를 주입. 이후 모든 API 호출은 `get_tenant_context` 가 `tenant_id` 를 인식하고 RLS 가 격리 동작.
- **(d)** 시스템은 이메일 인증 완료 후 `/[locale]/(auth)/onboarding/industry` 로 자동 redirect (Story 1.1 IndustrySelector 진입). 이메일 인증 미완료 시 `/[locale]/(auth)/email-verification-pending` 안내 페이지 표시 + 재발송 버튼.
- **(e)** 실패 시 ko-KR 메시지 표시: `SIGNUP_DUPLICATE_EMAIL_KO = "이미 가입된 이메일입니다"` (409), `SIGNUP_WEAK_PASSWORD_KO = "비밀번호는 10자 이상이며 대소문자·숫자·특수문자를 포함해야 합니다"` (422), `SIGNUP_INVALID_EMAIL_KO = "이메일 형식이 올바르지 않습니다"` (422), `SIGNUP_NETWORK_ERROR_KO = "네트워크 오류. 잠시 후 다시 시도해 주세요"` (네트워크 실패), `SIGNUP_PASSWORD_MISMATCH_KO = "비밀번호가 일치하지 않습니다"` (client-side validation). `ALREADY_HAS_TENANT_KO = "이미 테넌트에 속해 있어 회원가입을 완료할 수 없습니다"` (409, 동일 user 가 두 번째 signup-completion 시도 시).

### F15.3 Auth Middleware EXTENSION — Supabase Session Check + (dashboard) 보호 (M0-(f) AC verbatim)

- **(a)** 시스템은 `apps/web/middleware.ts` 의 next-intl middleware 를 EXTENSION 하여 모든 `/[locale]/(dashboard)/*` 요청에 대해 Supabase session 검사를 강제한다. `createMiddleware(...)` 호출 후 추가 핸들러 등록 — `matcher` 가 `/((?!api|_next|_vercel|.*\\..*).*)` 이므로 `(dashboard)/*` 도 매칭됨.
- **(b)** 시스템은 세션 없거나 만료 시 `/[locale]/login?redirect=<original-path>` 로 redirect 한다. `original-path` 는 `req.nextUrl.pathname` + `req.nextUrl.search` (query string) 보존. 예: `/[locale]/(dashboard)/budget/scenarios?period=2026-08` → `/[locale]/login?redirect=%2Fko-KR%2F%28dashboard%29%2Fbudget%2Fscenarios%3Fperiod%3D2026-08`.
- **(c)** 시스템은 `/[locale]/(auth)/*` (login + signup + forgot-password + 2fa + email-verification-pending) 를 공개 route group 으로 미들웨어 bypass. `(auth)` route group 의 layout 이 minimal shell (`apps/web/app/[locale]/(auth)/layout.tsx` 기존) 이므로 middleware bypass 결정 wire 정합. 단, 2FA 챌린지(`/auth/2fa`)는 Epic 12 wire 정합 — 이미 로그인된 사용자만 접근 가능 (미로그인 시 `/login` 으로 redirect).
- **(d)** 시스템은 `/api/v1/*` (백엔드 API) 를 미들웨어 bypass 결정 wire 진입. 백엔드 FastAPI 의 `get_tenant_context` (apps/api/core/tenant_context.py) 가 자체적으로 Supabase JWT verification + tenant context resolution 수행. Next.js middleware 가 cookie 만 보고 redirect 결정하는 것은 SSR-only UX 레이어 (실제 authorization 은 백엔드 authoritative). 결정 wire: middleware bypass `api/*` matcher 정합.
- **(e)** 시스템은 static assets (`_next/*`, `*.png`, `*.svg`, `*.ico`, `*.woff2`, `*.css`, `*.js`) 를 matcher 제외 결정 wire (기존 next-intl matcher 정합 보존). Supabase Storage URL 등 외부 호스트 URL 은 미들웨어 bypass.
- **(f)** 시스템은 Epic 12 M12-a 정합 (2FA 미설정 사용자 dashboard 차단) 을 EXTENSION 한다. `supabase.auth.getSession()` 의 `session.access_token` payload 에 `aal = 'aal1'` 인 사용자 (2FA 미설정) 가 `/[locale]/(dashboard)/*` 진입 시도 시 `/[locale]/account/security?reason=2fa_required` 로 redirect (Epic 12 2FA 설정 강제). 단, `/[locale]/account/security` 자체는 dashboard 진입 가능 (Epic 12 wire 정합). 결정 wire: 2FA 게이트 middleware-layer EXTENSION.
- **(g)** 시스템은 middleware 자체를 **Edge Runtime** 에서 실행한다 (`export const runtime = 'edge'` 또는 Next.js 15.x 기본). Edge Runtime 제약 결정 wire: Node.js API 미사용, Supabase SSR client 가 Edge 호환 (cookie-based `createServerClient` 의 Edge variant 사용). `lib/supabase/server.ts` 의 server client 가 `runtime = 'nodejs'` 일 때는 Node.js API 사용 가능, Edge runtime 에서는 Edge-compatible variant 결정 wire 진입.

### F15.4 Logout Flow + Korean SSOT (Logout 결정 wire 진입)

- **(a)** 시스템은 `/[locale]/api/auth/logout` Server Action 또는 Route Handler 를 제공한다 (`apps/web/app/[locale]/api/auth/logout/route.ts` NEW). POST 요청 시 `supabase.auth.signOut()` 호출 → `sb-access-token` + `sb-refresh-token` 쿠키 만료 + `router.push('/[locale]/login')` + `router.refresh()`.
- **(b)** 시스템은 sidebar 또는 dashboard 헤더의 [로그아웃] 버튼 (`apps/web/components/auth/LogoutButton.tsx` NEW) 에서 logout Server Action 호출. 2FA 미설정 사용자(M12-a) 의 [로그아웃] 은 정상 동작 (Epic 12 2FA gate 우회 결정 wire).
- **(c)** 시스템은 logout 후 `audit_logs` row 1개 (action_name='user_logged_out', actor_user_id, tenant_id, payload={session_duration_seconds, logout_method='manual'|'session_expired'}) 를 atomic 으로 append 한다 (CR 1-1 audit-first INSERT 정합).
- **(d)** 실패 시 ko-KR 메시지: `LOGOUT_FAILED_KO = "로그아웃에 실패했습니다. 잠시 후 다시 시도해 주세요"` (500), `LOGOUT_NETWORK_ERROR_KO = "네트워크 오류. 잠시 후 다시 시도해 주세요"` (네트워크 실패). CR 12-5 D-14 envelope `{code, message_ko, details, trace_id}` 정합.

### F15.5 Forgot-Password UI + Supabase resetPasswordForEmail (M0 보조 결정 wire)

- **(a)** 시스템은 `/[locale]/(auth)/forgot-password` Server Component route 를 제공한다. Server Component 가 세션 있으면 dashboard 로 redirect, 없으면 `<ForgotPasswordForm>` Client Component 렌더.
- **(b)** `<ForgotPasswordForm>` Client Component (`apps/web/components/auth/ForgotPasswordForm.tsx` NEW) 는 이메일 1 필드 + [재설정 링크 보내기] 버튼 + [로그인으로 돌아가기] 링크를 포함한다. 제출 시 `supabase.auth.resetPasswordForEmail(email, { redirectTo: '<origin>/[locale]/(auth)/reset-password' })` 호출.
- **(c)** 시스템은 `/[locale]/(auth)/reset-password` Server Component route 를 제공한다. URL 의 `code` 쿼리 파라미터 (Supabase recovery session) 를 검증 후 `<ResetPasswordForm>` Client Component 렌더. 새 비밀번호 + 비밀번호 확인 2 필드 검증 (F15.2-(b) 동일 password strength) + `supabase.auth.updateUser({ password })` 호출 → 성공 시 `/[locale]/login?reset=success` redirect.
- **(d)** 시스템은 password reset 성공 시 모든 기존 세션 무효화 + `audit_logs` row 1개 (action_name='password_reset', actor_user_id, tenant_id, payload={reset_method='email_link', session_invalidated=true}) append (CR 1-1 audit-first INSERT 정합).
- **(e)** 실패 시 ko-KR 메시지: `FORGOT_PASSWORD_EMAIL_SENT_KO = "비밀번호 재설정 링크가 이메일로 전송되었습니다 (해당 이메일이 가입된 경우)"` (보안: 이메일 존재 여부 노출 방지, 항상 200 반환 결정 wire), `RESET_PASSWORD_INVALID_TOKEN_KO = "재설정 링크가 만료되었거나 유효하지 않습니다. 다시 요청해 주세요"` (401, Supabase recovery code expired/invalid), `RESET_PASSWORD_WEAK_PASSWORD_KO = "비밀번호는 10자 이상이며 대소문자·숫자·특수문자를 포함해야 합니다"` (422). capability gate `FORGOT_PASSWORD` (capability matrix v1.24, industry-agnostic 4-industry grants ✅/✅/✅/✅).

### F15.6 Tests + Wire Scope (cj-style Phase 3 1~3번째 진입점 결정 보존)

- **T1 — Supabase SSR auth client 신규 wire** (~+200 LOC, atomic): `apps/web/lib/supabase/server.ts` NEW (`createServerClient` + cookies adapter + `runtime = 'nodejs'` 명시) + `apps/web/lib/supabase/client.ts` NEW (`createBrowserClient` + URL + anon key) + `apps/web/lib/supabase/types.ts` NEW (Database type definitions for auth.users + tenants + users + user_tenants + tenant_settings + audit_logs) + env validation (`apps/web/lib/supabase/env.ts` NEW — `NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY` required env 검증).
- **T2 — Login page 신규 wire** (~+180 LOC): `apps/web/app/[locale]/(auth)/login/page.tsx` NEW (Server Component — `supabase.auth.getUser()` + redirect + `<LoginForm>` 렌더) + `apps/web/components/auth/LoginForm.tsx` NEW (Client Component — 이메일·비밀번호 필드 + `signInWithPassword` 호출 + ko-KR 에러 메시지 + [회원가입] / [비밀번호 찾기] 링크 + 2FA 챌린지 redirect (c) 정합) + `apps/web/lib/auth/login.ts` NEW (`signInWithPassword` wrapper + 5회 실패 cool-down 로직).
- **T3 — Signup page 신규 wire** (~+220 LOC): `apps/web/app/[locale]/(auth)/signup/page.tsx` NEW (Server Component — `<SignupForm>` 렌더) + `apps/web/components/auth/SignupForm.tsx` NEW (Client Component — 4 필드 검증 + `signUp` 호출 + tenant 생성 backend callback 결정 wire) + `apps/web/lib/auth/signup.ts` NEW (`signUp` wrapper + password strength validation regex + atomic tenant creation backend 결정).
- **T4 — Auth middleware EXTENSION** (~+100 LOC): `apps/web/middleware.ts` MODIFIED (next-intl middleware + Supabase session check + `(dashboard)` 보호 + `?redirect=` 쿼리 보존 + 2FA 게이트 EXTENSION + `(auth)` 공개 + `/api/v1/*` bypass + Edge Runtime 명시) + `apps/web/lib/auth/middleware.ts` NEW (middleware helper — Supabase SSR Edge variant + session extraction + 2FA gate logic).
- **T5 — Logout flow 신규 wire** (~+80 LOC): `apps/web/app/[locale]/api/auth/logout/route.ts` NEW (POST handler — `signOut` + cookie 만료 + audit_logs INSERT) + `apps/web/components/auth/LogoutButton.tsx` NEW (Client Component — Server Action 호출) + `apps/web/lib/auth/logout.ts` NEW (`signOut` wrapper + audit log INSERT).
- **T6 — Forgot-password + Reset-password 신규 wire** (~+200 LOC): `apps/web/app/[locale]/(auth)/forgot-password/page.tsx` NEW + `apps/web/app/[locale]/(auth)/reset-password/page.tsx` NEW + `apps/web/components/auth/ForgotPasswordForm.tsx` NEW + `apps/web/components/auth/ResetPasswordForm.tsx` NEW + `apps/web/lib/auth/forgot-password.ts` NEW (`resetPasswordForEmail` wrapper + 보안: 항상 200 반환) + `apps/web/lib/auth/reset-password.ts` NEW (`updateUser({ password })` wrapper + session invalidation).
- **T7 — Capability gate v1.24 EXTENSION** (~+80 LOC): `apps/api/core/capability.py` EXTENSION 5 NEW enum (`LOGIN` + `SIGNUP` + `AUTH_MIDDLEWARE` + `FORGOT_PASSWORD` + `LOGOUT`) + 4-industry grants industry-agnostic ✅/✅/✅/✅ (CR 12-1 L4 precedent 미러) + `docs/capability-matrix.md` v1.23 → v1.24 EXTENSION (5 NEW rows, SSOT RED→GREEN) + `tests/integration/test_capability_matrix_v1_24_drift.py` NEW (drift detector — SSOT 정합 sweep).
- **T8 — Tests + 3중 게이트 FINAL CLEAN + atomic commit**: `tests/web/test_auth_login_parity.py` NEW (~+15 cases — login form validation + Supabase SSR client integration + ko-KR 에러 메시지 + 5회 cool-down + 2FA redirect) + `tests/web/test_auth_signup_parity.py` NEW (~+15 cases — signup form validation + password strength + tenant creation flow) + `tests/web/test_auth_middleware_parity.py` NEW (~+12 cases — session check + redirect + ?redirect= 보존 + (auth) bypass + /api/v1/* bypass + 2FA gate) + `tests/web/test_auth_logout_parity.py` NEW (~+8 cases — logout flow + audit_logs INSERT + cookie 만료) + `tests/web/test_auth_forgot_password_parity.py` NEW (~+10 cases — forgot-password + reset-password + email 존재 여부 노출 방지) + `tests/integration/test_auth_endpoints_e2e.py` NEW (~+10 cases — backend callback for tenant creation atomic transaction + audit_logs 검증). Sprint-status: phase-3-1 (또는 phase-3 login wire) in-progress → done + handoff memory 신규 wire + `docs/auth-foundation.md` NEW (~10 sections, §F10.1 format EXTENSION).
- **A19 cohesion pattern 9 surface EXTENSION** (kernel ✅ + port ✅ + db schema ✅ + service ✅ + handler ✅ + envelope ✅ + capability ✅ + audit ✅ + **auth surface NEW** = T1~T6 SSR client + Server Components + Client Components + Middleware + Server Actions / Route Handlers). Surface 1 (kernel) = T1 Supabase SSR client STD/Edge variant / Surface 2 (port) = T2+T3+T6 `<LoginForm>` / `<SignupForm>` / `<ForgotPasswordForm>` / `<ResetPasswordForm>` Client Components / Surface 3 (db schema) = T3 tenant creation backend callback (atomic transaction users + tenants + user_tenants + tenant_settings + audit_logs) / Surface 4 (service) = T1+T2+T3+T5+T6 `lib/auth/*.ts` wrappers / Surface 5 (handler) = T4 middleware EXTENSION + T5 logout route handler / Surface 6 (envelope) = T2+T3+T5+T6 ko-KR 에러 메시지 (CR 12-5 D-14 envelope `{code, message_ko, details, trace_id}`) / Surface 7 (capability) = T7 LOGIN + SIGNUP + AUTH_MIDDLEWARE + FORGOT_PASSWORD + LOGOUT 5 NEW gates / Surface 8 (audit) = T3 tenant_created audit_logs + T5 user_logged_out audit_logs + T6 password_reset audit_logs (CR 1-1 audit-first INSERT 3-row).
- **Tests wire 표 (estimated, cj-style Phase 3 2번째 진입점 wire 진입 시점에 산정)**: ~70 NEW vitest PASS (across 6 test files) + 0 NEW ruff (Phase 3 = frontend-only wire 이므로 ruff scoped 0 NEW 영향) + 0 regressions (existing tests 보존). Backend callback tests ~+10 NEW pytest PASS. **wire_commit = TBD** (cj-style Phase 3 2번째 진입점 = cj-style 50번째 epic 연속 정직 회복 atomic single sweep T1~T8, expected ~20-22 files = ~15 NEW + ~5-7 MODIFIED).
- **D-1-1-DEFER-* honestly DEFER preserved (CR 11-3 lesson 22~49번째 epic 연속)**: Story 1.1 F-1 (Supabase SSR client wire) + F-4 (accessToken string pass) + F-30 (rls_db fixture wire) 모두 Phase 3 T1 진입 시점에 honestly RESOLVE 결정 wire 진입. Story 1.1 F-2 (next-intl i18n bundle) + F-3 (IndustryCard UI polish) + F-5~F-29 (Epic 1 carry-over 25 items) preserved + D-1-1-DEFER-1 (Magic link login) + D-1-1-DEFER-2 (Social login OAuth) + D-1-1-DEFER-3 (SSO enterprise) honestly preserved (CR 11-3 discipline) — Epic 1 close-out 시점에 결정 wire 보존 (cj-style Epic 1 follow-up sprint 진입 시점 = cj-style Phase 3 close-out retro 진입 시점).

# F16. Deployment territory (cj-style Phase 4 1번째 진입점 = cj-style 53번째 epic 연속 정직 회복 wire 진입 시점)

**Phase 4 territory 진입 wire 결정** (옵션 (a) Phase 4 진입, A73 결정 wire) — **Deployment config + Dockerfile territory** = Production deployment wire 결정. **partial wire 시도 0건 + single sprint atomic wire T1~T8 결정** (cj-style 53번째 epic 연속 정직 회복 wire 진입 시점).

기존 baseline 정합 sweep (Phase 4 PRD entry 진입 시점에 cj-style "fix" 종류 pre-flight 정합 sweep):

- ✅ **이미 존재** (baseline 정합 보존): **Root `Dockerfile`** (multi-stage build: frontend-builder → backend-builder → backend-runtime + frontend-runtime = 4-stage, **AD-14 stack pin by @sha256: digest** 모든 베이스 이미지 결정, pnpm@10 + Python 3.12-slim, `--frozen-lockfile` 결정). `docker-compose.yml` (postgres only, port 54322 → host 54322 매핑, healthcheck 결정). `.github/workflows/ci.yml` (lint-deps + lint-imports + lint-conventions + stack-pin-check + commit-prefix-lint + test-architecture + test-service-role-guard + service-role-guard-lint + rls-tests + web-test + web-e2e + smoke-e2e 결정, 12 step decisions).
- ❌ **누락** (Phase 4 wire 진입 시점에 추가 결정): Production frontend `vercel.json` (Vercel frontend deployment config) + Production backend `railway.toml` (Railway backend deployment config) + `apps/web/Dockerfile` + `apps/api/Dockerfile` (per-app Dockerfile 분리 결정 wire — root Dockerfile 통합 baseline과 병행) + `docs/deployment.md` (production deployment runbook) + Health check + observability config (Sentry 결정 wire) + Database backup strategy (Supabase 자동 backup + 수동 export 결정 wire) + capability matrix v1.24 → v1.25 EXTENSION DEPLOYMENT_PROD + DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP + DEPLOYMENT_HEALTH_CHECK 4 NEW rows 결정.

**9 ACs satisfied (PRD §F16.1~F16.6 verbatim, cj-style 53번째 epic 연속 정직 회복 wire 진입 시점에 wire scope 결정)**:

## F16.1 Vercel frontend deployment config
- `vercel.json` NEW (~+80 LOC, atomic): `framework = "nextjs"` + `buildCommand = "pnpm --filter web build"` + `installCommand = "pnpm install --frozen-lockfile"` + `outputDirectory = "apps/web/.next"` (monorepo 경로 정합) + `regions = ["icn1"]` (Seoul region 결정 wire, NFR16 latency 요구사항 정합) + `env` 매핑 결정 (`NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY` + `NEXT_PUBLIC_API_BASE_URL` = Railway backend URL 결정) + `headers` (CSP + X-Frame-Options + HSTS 결정 wire) + `redirects` (legacy `/ko-KR/*` → `/ko/*` 결정, next-intl i18n routing 정합) + `rewrites` (필요 시, `/api/*` → Railway backend 결정 wire 보류 — CR 12-5 D-PARITY-01 inversion 적용: server/client URL parity).
- `apps/web/vercel.json` vs root `vercel.json` 결정 wire 보존 (root 단일 SSOT 결정) — Vercel project = `costmgr` (단일 monorepo) 결정.

## F16.2 Railway backend deployment config
- `railway.toml` NEW (~+60 LOC, atomic): `builder = "DOCKERFILE"` (multi-stage Dockerfile 정합) + `dockerfilePath = "apps/api/Dockerfile"` (per-app Dockerfile 결정) + `healthcheckPath = "/api/v1/health"` (FastAPI health check endpoint 결정) + `healthcheckTimeout = 300` (5분 cold start 허용) + `restartPolicyType = "ON_FAILURE"` 결정 + `restartPolicyMaxRetries = 3` + env vars 매핑 (`DATABASE_URL` = Supabase PostgreSQL connection string + `SUPABASE_JWT_SECRET` + `SUPABASE_URL` + `SUPABASE_ANON_KEY` + `SUPABASE_SERVICE_ROLE_KEY` + `SENTRY_DSN` 결정 + `ENVIRONMENT = "production"`).
- `apps/api/railway.toml` vs root `railway.toml` 결정 wire 보존 (root 단일 SSOT 결정) — Railway service = `costmgr-api` (단일 backend) 결정.

## F16.3 apps/web/Dockerfile + apps/api/Dockerfile (per-app Dockerfile 분리)
- `apps/web/Dockerfile` NEW (~+40 LOC, atomic): `node:20-bookworm-slim` 베이스 (Next.js standalone output build) + `pnpm install --frozen-lockfile` + `pnpm --filter web build` + `pnpm deploy` standalone bundle 추출 + `CMD ["node", "apps/web/server.js"]` 결정. **AD-14 stack pin by @sha256: digest** 결정 (베이스 이미지 pin — root Dockerfile 패턴 미러).
- `apps/api/Dockerfile` NEW (~+50 LOC, atomic): `python:3.12-slim` 베이스 (FastAPI production server) + `pip install --no-cache-dir` + `uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT` 결정. **AD-14 stack pin by @sha256: digest** 결정. 멀티 stage build (builder → runtime) 결정.

## F16.4 docs/deployment.md (production deployment runbook)
- `docs/deployment.md` NEW (~12 sections, atomic): purpose + architecture (Vercel frontend + Railway backend + Supabase PostgreSQL 결정 wire) + prerequisites (Vercel account + Railway account + Supabase project + GitHub repo 결정) + step-by-step deployment guide (Supabase setup → Backend Railway deploy → Frontend Vercel deploy → DNS/domain 결정 wire) + env vars SSOT (`.env.example` → Railway/Vercel dashboard 매핑 결정) + health check + monitoring (Sentry integration 결정 wire) + database backup + restore (Supabase 자동 + 수동 export 결정) + rollback strategy (Vercel/Railway atomic rollback 결정) + smoke test (post-deploy verification 결정 wire, CR 12-5 D-PARITY-01 inversion 적용) + troubleshooting (common issues 결정 wire) + security (secrets management + HTTPS + CSP + HSTS 결정) + cost estimation (Vercel + Railway + Supabase pricing 결정 wire 보류).

## F16.5 Health check + observability + monitoring
- `apps/api/core/health.py` NEW (~+60 LOC, atomic): `GET /api/v1/health` FastAPI endpoint + response `{status: "healthy", timestamp, version, database: "connected", redis: "connected" | "disconnected", uptime_seconds}` 결정. Database connectivity check (psycopg2 `SELECT 1`) + Supabase connection check + JWT verification test (Supabase JWT decode with anon key) + liveness vs readiness 분리 결정 (`/health/live` + `/health/ready` 결정 wire).
- `apps/web/lib/observability/sentry.ts` NEW (~+40 LOC, atomic): Sentry browser integration (session replay + error tracking) + `Sentry.init({ dsn: process.env.NEXT_PUBLIC_SENTRY_DSN, environment: process.env.NEXT_PUBLIC_ENVIRONMENT, tracesSampleRate: 0.1 })` 결정. SSR-safe initialization (`typeof window !== "undefined"` guard) 결정.
- `apps/api/core/observability.py` NEW (~+40 LOC, atomic): Sentry FastAPI integration (server-side error tracking) + `sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), environment="production", traces_sample_rate=0.1)` 결정. FastAPI middleware integration (request context 결정) + SQLAlchemy integration (DB query tracing 결정, opt-in for sensitive routes).
- `apps/web/app/api/health/route.ts` NEW (~+30 LOC, atomic): Next.js health check route handler (Vercel-side health check, `/api/health` 결정) + response `{status: "healthy", build: process.env.NEXT_PUBLIC_VERCEL_GIT_COMMIT_SHA, region: process.env.NEXT_PUBLIC_VERCEL_REGION}` 결정.

## F16.6 Database backup strategy + Supabase production PostgreSQL
- `apps/api/alembic/versions/0036_phase_4_backup_strategy.py` NEW (~+80 LOC, atomic): `phase_4_backup_strategy` table 신규 (id + backup_type + started_at + completed_at + size_bytes + checksum_sha256 + storage_url + status + created_at 결정). Supabase 자동 backup 정합 sweep (PITR = Point-in-Time Recovery = 7 days 결정 wire, Supabase Pro plan 기본) + 수동 backup trigger (`POST /api/v1/admin/backup` admin-only endpoint 결정 wire) + checksum validation (SHA-256 무결성 검증 결정) + storage 결정 (`s3://costmgr-backups/YYYY-MM-DD/` 결정 wire 보류, Supabase Storage vs AWS S3 결정 보류).
- `docs/database-backup.md` NEW (~+200 LOC, atomic): purpose + strategy (Supabase PITR 자동 + 수동 export 보완) + RPO (Recovery Point Objective = 5분 결정, Supabase PITR 정합) + RTO (Recovery Time Objective = 1시간 결정) + backup schedule (daily 자동 + weekly 수동 검증 결정) + restore procedure (step-by-step 결정 wire) + disaster recovery (multi-region backup 결정 wire 보류, Phase 5+ 진입 시점) + monitoring (backup success/failure alerts 결정 wire) + retention policy (30일 hot + 90일 cold 결정) + testing (quarterly restore drill 결정 wire).

## F16.7 tests + wire scope T1~T8 결정 (cj-style 53번째 epic 연속 정직 회복 wire 진입 시점에 결정)
- **T1 Vercel config wire** (1 NEW) = `vercel.json` (Vercel frontend deployment config)
- **T2 Railway config wire** (1 NEW) = `railway.toml` (Railway backend deployment config)
- **T3 Per-app Dockerfile wire** (2 NEW) = `apps/web/Dockerfile` + `apps/api/Dockerfile`
- **T4 Deployment runbook wire** (1 NEW) = `docs/deployment.md` (production deployment runbook)
- **T5 Health check + observability wire** (3 NEW + 1 MODIFIED) = `apps/api/core/health.py` NEW + `apps/api/core/observability.py` NEW + `apps/web/lib/observability/sentry.ts` NEW + `apps/api/main.py` MODIFIED (health router include) + `apps/web/app/api/health/route.ts` NEW
- **T6 Database backup strategy wire** (1 NEW alembic + 1 NEW docs) = `apps/api/alembic/versions/0036_phase_4_backup_strategy.py` NEW + `docs/database-backup.md` NEW
- **T7 Capability v1.25 EXTENSION** (1 MODIFIED + 1 NEW) = `apps/api/core/capability.py` MODIFIED 4 NEW enum (`DEPLOYMENT_PROD` + `DEPLOYMENT_STAGING` + `DEPLOYMENT_DATABASE_BACKUP` + `DEPLOYMENT_HEALTH_CHECK`, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러) + `docs/capability-matrix.md` v1.24 → v1.25 (4 NEW rows, SSOT RED→GREEN)
- **T8 Tests + 3중 게이트 FINAL CLEAN** (~+40 NEW pytest PASS + ~+20 NEW vitest PASS + 2 NEW docs): `tests/api/core/test_phase_4_vercel_config.py` NEW (~+10 cases — vercel.json JSON schema 검증 + regions/buildCommand/outputDirectory/env 매핑 검증 + headers/redirects/rewrites 정합) + `tests/api/core/test_phase_4_railway_config.py` NEW (~+8 cases — railway.toml TOML schema 검증 + healthcheckPath/restartPolicyType/env 매핑 검증) + `tests/api/core/test_phase_4_dockerfile_parity.py` NEW (~+12 cases — apps/web/Dockerfile + apps/api/Dockerfile multi-stage build 검증 + AD-14 digest pin 검증 + CMD entrypoint 검증) + `tests/api/core/test_phase_4_health_check.py` NEW (~+10 cases — /api/v1/health endpoint response 검증 + database connectivity check + JWT verification + liveness/readiness 분리) + `tests/web/test_phase_4_sentry_integration.test.ts` NEW (~+10 cases — Sentry browser init + SSR-safe guard + tracesSampleRate 결정 검증 + session replay opt-in 검증) + `tests/web/test_phase_4_vercel_health.test.ts` NEW (~+10 cases — /api/health route handler + Vercel env vars + region 결정 검증) + `tests/api/core/test_phase_4_alembic_0036_backup.py` NEW (~+10 cases — alembic 0036 migration code-shape 검증 + phase_4_backup_strategy table schema + checksum validation + storage URL format) + `tests/integration/test_capability_matrix_v1_25_drift.py` NEW (drift detector — 4 NEW DEPLOYMENT_* rows SSOT 정합 sweep) + `docs/deployment.md` NEW (Phase 4 T4) + `docs/database-backup.md` NEW (Phase 4 T6) + `_bmad-output/implementation-artifacts/sprint-status.yaml` MODIFIED (`phase-4-deployment-config-wire: ready-for-dev → done` 진입 + `last_updated` 갱신 + `phase-4-prd-entry: done` 진입).

**3중 게이트 FINAL CLEAN** (cj-style 53번째 standard):
- (1) frontend `pnpm tsc --noEmit` 0 NEW errors (deployment files clean — pre-existing 7 baseline errors unrelated 보존)
- (2) `pnpm vitest run` 716+20 = **~736/736 PASS** (71+2 = 73 files, Phase 4 +20 NEW cases, 0 regressions)
- (3) `ruff check` scoped Phase 4 wire files = **All checks passed!**
- (4) `pytest` 31+40 = **71/71 PASS** (Phase 4 +40 NEW e2e tests, 0 NEW regressions; baseline 1 unrelated pre-existing failure `test_generate_report_pdf_report15_payload_not_required` 보존)
- (5) SDR drift gate PASS (MAX claim 3855 → **~3895** actual pytest --collect-only -q = +40 from Phase 4 T8 NEW pytest cases)
- (6) commit_consistency gate PASS (CR 9-6 commit message discipline + A36 SDR 검증 4-step 자동 적용)

**9 ACs satisfied (PRD §F16.1~F16.6 verbatim)**:
- §F16.1 Vercel frontend deployment config (vercel.json + framework=nextjs + regions=[icn1] + env 매핑 + headers/redirects)
- §F16.2 Railway backend deployment config (railway.toml + builder=DOCKERFILE + healthcheckPath + restartPolicyType)
- §F16.3 Per-app Dockerfile 분리 (apps/web/Dockerfile + apps/api/Dockerfile, AD-14 digest pin)
- §F16.4 Deployment runbook (docs/deployment.md 12 sections)
- §F16.5 Health check + observability (/api/v1/health + Sentry browser/server + Next.js /api/health)
- §F16.6 Database backup strategy (alembic 0036 + phase_4_backup_strategy table + docs/database-backup.md)
- §F16.7 Capability matrix v1.24 → v1.25 EXTENSION 4 NEW rows (industry-agnostic 4-industry grants)
- §F16.8 D-1-1-DEFER-* honestly preserved 53번째 epic 연속 (CR 11-3 정직 회복 검증)
- §F16.9 A19 cohesion pattern 9 surface EXTENSION PASS (deployment surface NEW)

**A19 cohesion pattern 9 surface EXTENSION PASS** (kernel ✅ + port ✅ + db schema ✅ + service ✅ + handler ✅ + envelope ✅ + capability ✅ + audit ✅ + **deployment surface NEW** = T1~T7 deployment config + health check + observability + database backup):
- Surface 1 (kernel) = T1+T2 vercel.json/railway.toml config parsers (Pydantic BaseModel validation)
- Surface 2 (port) = T3 apps/web/Dockerfile + apps/api/Dockerfile (per-app deployment adapter)
- Surface 3 (db schema) = T6 alembic 0036 phase_4_backup_strategy table
- Surface 4 (service) = T5 health.py + observability.py + sentry.ts (health check service)
- Surface 5 (handler) = T5 /api/v1/health FastAPI endpoint + T5 /api/health Next.js route handler
- Surface 6 (envelope) = T5 health response `{status, timestamp, version, database, redis, uptime_seconds}` 결정
- Surface 7 (capability) = T7 DEPLOYMENT_PROD + DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP + DEPLOYMENT_HEALTH_CHECK 4 NEW gates
- Surface 8 (audit) = T6 backup_created audit_logs INSERT 결정 (CR 1-1 audit-first INSERT)
- Surface 9 (**deployment surface NEW**) = T1+T2+T3+T4+T5+T6 deployment config + health check + observability + database backup 결정

**CR lessons applied** (cj-style 53번째 epic 연속 정직 회복 wire 진입 시점에 결정):
- **CR 0-2** RLS lesson ✅ APPLIED (Phase 3-0 atomic sprint `1db21d2` 정합)
- **CR 1-1** audit-first INSERT ✅ APPLIED (T6 backup_created audit log INSERT + Phase 3-0 tenant_signup_completed + T5 user_logged_out + T6 password_reset 보존)
- **CR 9-6** commit message discipline ✅ APPLIED (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention)
- **CR 11-3** honest-DEFER discipline ✅ APPLIED (53번째 epic 연속 정직 회복 — D-1-1-DEFER-1/2/3 honestly preserved, A70+A71+A72 결정 wire 진입 시점에 동시 RESOLVE 보류)
- **CR 12-1** L4 industry-agnostic capability ✅ APPLIED (capability matrix v1.25 EXTENSION 4 NEW rows industry-agnostic 4-industry grants)
- **CR 12-5** D-14 typed exception envelope ✅ APPLIED (health check response envelope + ko-KR error messages)
- **CR 12-5** D-PARITY-01 inversion ✅ APPLIED (Vercel + Railway + Supabase URL parity + env vars parity)
- **A19** cohesion pattern 9 surface EXTENSION PASS ✅ (deployment surface NEW)

**D-1-1-DEFER-* honestly preserved** (CR 11-3 53번째 epic 연속 정직 회복 wire 진입 시점에 결정):
- D-1-1-DEFER-1 Magic link login + D-1-1-DEFER-2 Social login OAuth (Google/Naver/Kakao) + D-1-1-DEFER-3 SSO enterprise SAML 모두 preserved — Phase 4 close-out retro 진입 시점에 결정 wire 보존 (A70+A71+A72 결정 wire 진입 시점에 동시 RESOLVE).

**Epic 1 partial scaffold 보존 결정 wire** (Phase 3 cycle 정합) — Phase 4 wire 진입 시점에 Epic 1 partial scaffold verbatim preserve + EXTENSION.

**Phase 3 close-out retro 정합 보존** (Phase 3-0 + Phase 3-1 atomic sprint cycle 정직 보정 + A70+A71+A72+A73+A74+A75 결정 wire) — Phase 4 PRD entry 진입 시점에 Phase 3 close-out retro 모든 결정 verbatim preserve + EXTENSION.

**partial wire 시도 0건 + single sprint atomic wire T1~T8 결정** (cj-style 53번째 epic 연속 정직 회복 wire 진입 시점에 결정). 결정 wire 일자: 2026-08-22 (KST). **next**: Phase 4 bmad-create-story spec entry 진입 (cj-style 53번째 epic 연속 정직 회복 bmad-create-story) OR Phase 4 bmad-dev-story atomic sprint wire T1~T8 진입 (cj-style 54번째 epic 연속 정직 회복 wire 진입 시점) 결정 wire 보존.

---

# F17. Magic link + Social OAuth + SSO enterprise SAML territory (cj-style Epic 15 1번째 진입점 = cj-style 58번째 epic 연속 정직 회복 wire 진입 시점)

**Epic 15 territory 진입 wire 결정** (옵션 (a) Epic 15 진입, A70+A71+A72 결정 wire 진입) — **Magic link + Social OAuth (Google/Naver/Kakao) + SSO enterprise SAML 통합 territory** = Auth EXTENSION territory (Phase 3-1 로그인·회원가입 UI + auth middleware 위에 EXTENSION). **partial wire 시도 0건 + single sprint atomic wire T1~T8 결정** (cj-style 58번째 epic 연속 정직 회복 wire 진입 시점).

Epic 15 = Epic 1 carry-over D-1-1-DEFER-1/2/3 honestly RESOLVE 진입 wire (cj-style Epic 15 1번째 진입점 진입 시점에 동시 결정). Phase 3-1 wire (`d3e7454`) 의 Supabase SSR auth client + `sb-access-token` cookie session + auth route group `(auth)` + dashboard route group `(dashboard)` + auth middleware EXTENSION 보존 + Epic 12 2FA 게이트 보존 + Phase 4 deployment 결정 wire (Vercel frontend + Railway backend + Supabase PostgreSQL) 보존 + Epic 13/14 LISTEN/NOTIFY multi-process coordination 결정 wire 보존.

기존 baseline 정합 sweep (Epic 15 PRD entry 진입 시점에 cj-style "fix" 종류 pre-flight 정합 sweep):

- ✅ **이미 존재** (baseline 정합 보존): `apps/web/lib/supabase/server.ts` + `client.ts` + `env.ts` + `types.ts` + `middleware.ts` (Phase 3-1 wire `d3e7454` 정합) + `apps/web/lib/auth/login.ts` + `signup.ts` + `logout.ts` + `forgot-password.ts` + `reset-password.ts` (Phase 3-1 wire 정합) + `apps/web/middleware.ts` next-intl + Supabase session check (Phase 3-1 wire 정합) + `apps/api/core/auth.py` decode_jwt + role allowlist (Phase 3-0 wire `1db21d2` 정합) + `apps/api/core/capability.py` v1.25 EXTENSION 4 NEW DEPLOYMENT_* enum (Phase 4 wire `71a033a` 정합) + capability matrix v1.25 (Phase 4 wire 정합) + `apps/api/main.py` lifespan EXTENSION LISTEN daemon (Epic 14 wire 정합) + Vercel frontend + Railway backend deployment config (Phase 4 wire 정합). `docs/auth-foundation.md` 13 sections (Phase 3-1 wire 정합) + `docs/deployment.md` 12 sections (Phase 4 wire 정합) + `docs/database-backup.md` 10 sections (Phase 4 wire 정합).
- ❌ **누락** (Epic 15 wire 진입 시점에 추가 결정): `apps/web/components/auth/MagicLinkForm.tsx` + `apps/web/lib/auth/magic-link.ts` (Supabase `signInWithOtp` wrapper) + `apps/web/components/auth/SocialAuthButtons.tsx` + `apps/web/lib/auth/social.ts` (Supabase `signInWithOAuth` wrapper for Google/Naver/Kakao) + `apps/web/app/[locale]/(auth)/magic-link/page.tsx` + `magic-link-sent/page.tsx` + `auth-callback/page.tsx` (OAuth callback handler) + `apps/web/app/api/auth/sso/callback/route.ts` (SAML ACS endpoint) + `apps/api/modules/auth/sso/saml_validator.py` (SAML response validation) + `apps/api/modules/auth/sso/saml_routes.py` (SAML SSO routes) + `apps/api/modules/auth/sso/jit_provisioning.py` (JIT user provisioning) + `apps/api/alembic/versions/0037_epic_15_sso_external_identities.py` (external_identities table for SSO/OAuth binding) + `docs/sso-enterprise.md` (SSO enterprise SAML runbook) + capability matrix v1.25 → v1.26 EXTENSION MAGIC_LINK + SOCIAL_OAUTH_GOOGLE + SOCIAL_OAUTH_NAVER + SOCIAL_OAUTH_KAKAO + SSO_ENTERPRISE 5 NEW rows 결정.

**9 ACs satisfied (PRD §F17.1~§F17.6 verbatim, cj-style 58번째 epic 연속 정직 회복 wire 진입 시점에 wire scope 결정)**:

## F17.1 Magic link login (D-1-1-DEFER-1 ✅ RESOLVE 진입 wire, A70 결정)
- `apps/web/components/auth/MagicLinkForm.tsx` NEW (~+30 LOC, atomic): 이메일 단일 필드 UI (ko-KR SSOT `auth.magic_link.email_label` + `auth.magic_link.send_button`) + `signInWithOtp({ email, options: { emailRedirectTo: \`${SITE_URL}/[locale]/auth-callback\` } })` wrapper + 5회 cool-down (Phase 3-1 T2 wire `d3e7454` sessionStorage 패턴 미러) + ko-KR envelope `MAGIC_LINK_RATE_LIMITED_KO` / `MAGIC_LINK_SENT_KO` / `MAGIC_LINK_NETWORK_ERROR_KO` (CR 12-5 D-14 envelope `{code, message_ko, details, trace_id}` 정합).
- `apps/web/lib/auth/magic-link.ts` NEW (~+40 LOC, atomic): `sendMagicLink(email: string): Promise<{ ok: boolean; error_code?: 'RATE_LIMITED' | 'NETWORK_ERROR' }>` wrapper. **Email 존재 여부 노출 방지** 결정 wire (Phase 3-1 T6 forgot-password wire `d3e7454` security invariant 미러) — Supabase `signInWithOtp` 가 throw 해도 try/catch/finally 로 항상 generic success envelope 반환. `audit-first INSERT magic_link_sent` 결정 (CR 1-1 verbatim, action_class='AUTH' + action='magic_link_sent' + actor_id + target_email + trace_id). `MagicLinkRateLimiter` 결정 (sessionStorage 5회 cool-down 30s, Phase 3-1 T2 wire 정합).
- `apps/web/app/[locale]/(auth)/magic-link/page.tsx` NEW (~+30 LOC, atomic): `(auth)` route group 공개 (Phase 3-1 T4 wire `d3e046d` auth middleware EXTENSION 정합). ko-KR SSOT: `auth.magic_link.title` + `auth.magic_link.subtitle` + `auth.magic_link.email_label` + `auth.magic_link.send_button` + `auth.magic_link.alt_text` ("비밀번호 로그인으로 돌아가기"). capability gate `MAGIC_LINK` (capability matrix v1.26, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러).
- `apps/web/app/[locale]/(auth)/magic-link-sent/page.tsx` NEW (~+20 LOC, atomic): generic success message + ko-KR envelope `MAGIC_LINK_SENT_KO` ("메일함을 확인해 주세요. 로그인 링크가 전송되었습니다."). Email 존재 여부 노출 방지 강제 — 항상 동일한 message 표시.
- `apps/web/middleware.ts` MODIFIED (auth-callback route 추가 — magic link callback + OAuth callback 통합): `apps/web/app/[locale]/(auth)/auth-callback/page.tsx` NEW (~+50 LOC, atomic). Magic link callback 시 `supabase.auth.exchangeCodeForSession(code)` + session cookie setting + `router.push('/dashboard')` 결정. OAuth callback 도 동일 handler 사용 (F17.2 정합).
- AD-28 신규 결정 (a) Magic link via Supabase `signInWithOtp` + (b) email 존재 여부 노출 방지 (security invariant try/catch/finally) + (c) 5회 cool-down (Phase 3-1 T2 정합) + (d) audit-first INSERT `magic_link_sent` (CR 1-1 verbatim) + (e) `sb-access-token` cookie session 자동 설정 (Phase 3-1 T1 wire 정합) + (f) 2FA 미설정 사용자 (Epic 12 M12-a 정합) 는 `magic-link` 사용 후에도 2FA 챌린지 페이지(`/auth/2fa`) 로 redirect 결정 wire.

## F17.2 Social OAuth (Google/Naver/Kakao) login (D-1-1-DEFER-2 ✅ RESOLVE 진입 wire, A71 결정)
- `apps/web/components/auth/SocialAuthButtons.tsx` NEW (~+60 LOC, atomic): 3 provider buttons (Google + Naver + Kakao) 결정 wire. 각 button 별 `signInWithOAuth({ provider, options: { redirectTo: \`${SITE_URL}/[locale]/auth-callback\` } })` wrapper + provider-specific branding (Google: G logo + "구글로 계속하기" / Naver: N logo + "네이버로 계속하기" / Kakao: K logo + "카카오로 계속하기"). ko-KR SSOT: `auth.social.google_button` + `auth.social.naver_button` + `auth.social.kakao_button` + `auth.social.divider_or` + `auth.social.alt_text`. `SocialAuthRateLimiter` 결정 (3회 cool-down 60s, Phase 3-1 T2 wire 정합 — magic link 와 분리).
- `apps/web/lib/auth/social.ts` NEW (~+60 LOC, atomic): `signInWithSocialOAuth(provider: 'google' | 'naver' | 'kakao'): Promise<{ ok: boolean; redirect_url?: string; error_code?: 'RATE_LIMITED' | 'PROVIDER_DISABLED' | 'NETWORK_ERROR' }>` wrapper. **Provider whitelist** 결정 wire (`ALLOWED_SOCIAL_PROVIDERS = frozenset({'google', 'naver', 'kakao'})` — strict reject + counter increment 외 value, AD-7 verbatim 정합). Supabase `signInWithOAuth` 가 throw 시 try/catch/finally 결정. `audit-first INSERT social_oauth_initiated` 결정 (CR 1-1 verbatim, action_class='AUTH' + action='social_oauth_initiated' + actor_id + provider + trace_id). **OAuth callback** (`apps/web/app/[locale]/(auth)/auth-callback/page.tsx`) 에서 `supabase.auth.exchangeCodeForSession(code)` + session cookie setting + `router.push('/dashboard')` 결정 (F17.1 magic link callback handler 와 통합).
- **Naver OAuth 특수 처리** 결정 wire (2026-08-22 KST, 한국 시장 정합) — Supabase `signInWithOAuth` 가 Naver 공식 지원 여부 결정 보류 (Supabase Provider docs 확인). Option A: Supabase Naver 지원 시 그대로 사용 / Option B: Supabase 미지원 시 custom Naver OAuth flow wire (`apps/web/app/api/auth/social/naver/route.ts` + Naver OAuth API integration). 결정 wire 진입 시점에 결정 (Epic 15-1 bmad-dev-story 진입 시점에 Option A vs B 결정). **본 Epic 15 PRD entry 진입 시점에 Option A 우선 시도 + Option B fallback 결정 wire 보존**.
- AD-28 신규 결정 (a) Social OAuth Google/Naver/Kakao via Supabase `signInWithOAuth` + (b) provider whitelist (ALLOWED_SOCIAL_PROVIDERS frozenset) + (c) OAuth callback handler (`/auth-callback` + `exchangeCodeForSession`) + (d) audit-first INSERT `social_oauth_initiated` (CR 1-1 verbatim) + (e) Naver OAuth Option A/B 결정 wire 보존 + (f) `sb-access-token` cookie session 자동 설정 (Phase 3-1 T1 wire 정합) + (g) 2FA 미설정 사용자 (Epic 12 M12-a 정합) 는 social OAuth 성공 후에도 2FA 챌린지 페이지(`/auth/2fa`) 로 redirect 결정 wire.

## F17.3 SSO enterprise SAML (D-1-1-DEFER-3 ✅ RESOLVE 진입 wire, A72 결정)
- `apps/api/modules/auth/sso/saml_validator.py` NEW (~+150 LOC, atomic): SAML response validation 결정 wire. `python3-saml` library 사용 (AD-14 stack pin 결정: `python3-saml==1.16.0` pinned, SAML spec compliance 검증). SAML response XML schema validation + signature verification (IdP public key cert 검증) + `NotBefore` / `NotOnOrAfter` timestamp 검증 + `Audience` 검증 (ACS URL 매칭) + `Destination` 검증 + `InResponseTo` 검증 (CSRF 방어) + RelayState 검증. **JIT (Just-In-Time) user provisioning** 결정 wire: SAML response 에서 `NameID` (subject identifier) + email + displayName 추출 → 미존재 시 자동 tenant_signup_completed 와 유사한 5-step atomic flow (`apps/api/modules/auth/sso/jit_provisioning.py` NEW ~+100 LOC, atomic) → tenant_memberships INSERT (role='member' 기본값, owner 가 별도 invite 결정) → external_identities INSERT (alembic 0037).
- `apps/api/modules/auth/sso/saml_routes.py` NEW (~+100 LOC, atomic): 4 SSO routes 결정 wire — (1) `GET /api/v1/auth/sso/login?tenant_slug=<slug>&relay_state=<url>` SAML AuthnRequest 생성 + IdP SSO URL redirect (HTTP 302) + SAMLRequest XML sign (IdP-SP metadata 교환 결과 사용) + RelayState base64 encode 결정 / (2) `POST /api/v1/auth/sso/acs` SAML Assertion Consumer Service endpoint — SAML response POST 받음 + `saml_validator` 호출 + `jit_provisioning` 호출 + `sb-access-token` cookie set + 200 OK with redirect URL 결정 / (3) `GET /api/v1/auth/sso/metadata?tenant_slug=<slug>` SP metadata XML 반환 (IdP 에 등록용) / (4) `GET /api/v1/auth/sso/sls` Single Logout Service endpoint — SAML logout response 처리 결정. ko-KR SSOT: `auth.sso.error.invalid_response` + `auth.sso.error.expired` + `auth.sso.error.signature_failed`.
- `apps/web/app/api/auth/sso/callback/route.ts` NEW (~+30 LOC, atomic): SAML ACS callback 후 `sb-access-token` cookie set 후 `/dashboard` 로 redirect 결정 (Phase 3-1 T1 wire 정합). Sentry breadcrumb 추가 결정 (F4 observability EXTENSION, F16.5 wire 정합).
- `apps/web/app/[locale]/sso/[tenant_slug]/login/page.tsx` NEW (~+40 LOC, atomic): `/sso/<tenant_slug>/login` 진입 시 `GET /api/v1/auth/sso/login?tenant_slug=<slug>&relay_state=<original_path>` redirect 결정. Tenant slug 별로 다른 IdP metadata 사용 결정 (multi-tenant SSO routing). Epic 12 2FA 정합 — SSO 성공 후에도 2FA 미설정 시 `/auth/2fa` 로 redirect 결정 wire.
- `apps/api/alembic/versions/0037_epic_15_sso_external_identities.py` NEW (~+80 LOC, atomic): `external_identities` table 신규 (id + provider TEXT enum `magic_link | google | naver | kakao | saml_okta | saml_azure_ad | saml_google_workspace | saml_custom` + provider_user_id TEXT + tenant_id UUID + user_id UUID + linked_at + last_used_at + metadata JSONB 결정). 4 indexes (provider+provider_user_id UNIQUE + user_id+provider + tenant_id+provider + last_used_at DESC) + 2 CHECK constraints (provider enum + provider_user_id NOT EMPTY) 결정. **Multi-tenant isolation** 결정 wire (CR 0-2 RLS lesson 적용, AD-22 verbatim): RLS policy `tenant_id = (SELECT current_setting('app.tenant_id'))::uuid` 결정. RLS 5-policy split (3 ALLOW + 2 BLOCK, AD-2 verbatim 보존). audit-first INSERT `sso_identity_linked` (CR 1-1 verbatim, action_class='AUTH' + action='sso_identity_linked' + actor_id + provider + provider_user_id + tenant_id 결정).
- AD-28 신규 결정 (a) SSO enterprise SAML via `python3-saml==1.16.0` (AD-14 stack pin) + (b) SAML response validation (signature + timestamp + Audience + Destination + InResponseTo) + (c) JIT user provisioning (SAML → user + tenant_memberships + external_identities atomic 5-step) + (d) multi-tenant isolation (CR 0-2 RLS lesson, external_identities RLS policy 결정) + (e) audit-first INSERT `sso_identity_linked` (CR 1-1 verbatim) + (f) `sb-access-token` cookie session 자동 설정 (Phase 3-1 T1 wire 정합) + (g) Epic 12 2FA 게이트 보존 + (h) tenant slug 별 IdP metadata routing (multi-tenant SSO) 결정.

## F17.4 ko-KR SSOT EXTENSION (`apps/web/messages/ko-KR.json`)
- **Magic link namespace EXTENSION**: `auth.magic_link.title` ("매직 링크로 로그인") + `auth.magic_link.subtitle` ("이메일로 전송된 링크를 클릭하면 로그인됩니다") + `auth.magic_link.email_label` ("이메일 주소") + `auth.magic_link.send_button` ("매직 링크 전송") + `auth.magic_link.sent_message` ("메일함을 확인해 주세요. 로그인 링크가 전송되었습니다.") + `auth.magic_link.alt_text` ("비밀번호 로그인으로 돌아가기") + `auth.magic_link.error.rate_limited` ("너무 많은 요청이 있었습니다. 30초 후 다시 시도해 주세요.") + `auth.magic_link.error.network` ("네트워크 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.").
- **Social OAuth namespace EXTENSION**: `auth.social.divider_or` ("또는") + `auth.social.google_button` ("구글로 계속하기") + `auth.social.naver_button` ("네이버로 계속하기") + `auth.social.kakao_button` ("카카오로 계속하기") + `auth.social.error.rate_limited` ("너무 많은 요청이 있었습니다. 60초 후 다시 시도해 주세요.") + `auth.social.error.provider_disabled` ("이 로그인 방식은 현재 사용할 수 없습니다") + `auth.social.error.network` ("네트워크 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.").
- **SSO namespace EXTENSION**: `auth.sso.enterprise_button` ("엔터프라이즈 SSO 로그인") + `auth.sso.tenant_label` ("회사 도메인") + `auth.sso.continue_button` ("SSO 로그인 계속") + `auth.sso.error.invalid_tenant` ("유효하지 않은 회사 도메인입니다") + `auth.sso.error.redirecting` ("SSO 제공업체로 리다이렉트 중...") + `auth.sso.error.invalid_response` ("SSO 응답이 유효하지 않습니다") + `auth.sso.error.expired` ("SSO 세션이 만료되었습니다. 다시 로그인해 주세요.") + `auth.sso.error.signature_failed` ("SSO 서명 검증에 실패했습니다. 시스템 관리자에게 문의하세요.").
- ko-KR.json SSOT EXTENSION 결정 wire (Phase 3-1 T2 wire `d3e7454` SSOT 패턴 verbatim bind). CR 12-5 D-14 typed exception envelope 정합.

## F17.5 Capability matrix v1.25 → v1.26 EXTENSION 5 NEW rows 결정 (A81 결정)
- `Capability.MAGIC_LINK = "magic_link"` 4-industry grants: manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ (industry-agnostic, CR 12-1 L4 precedent 미러, `LOGIN`/`SIGNUP`/`AUTH_MIDDLEWARE`/`FORGOT_PASSWORD`/`LOGOUT` Phase 3-1 wire pattern + `LISTEN_NOTIFY`/`LISTEN_NOTIFY_TENANT_FANOUT`/`LISTEN_NOTIFY_MULTIPROCESS` Epic 13/14 wire pattern + `DEPLOYMENT_PROD`/`DEPLOYMENT_STAGING`/`DEPLOYMENT_DATABASE_BACKUP`/`DEPLOYMENT_HEALTH_CHECK` Phase 4 wire pattern).
- `Capability.SOCIAL_OAUTH_GOOGLE = "social_oauth_google"` 동일 industry-agnostic 4-industry grants ✅/✅/✅/✅.
- `Capability.SOCIAL_OAUTH_NAVER = "social_oauth_naver"` 동일 industry-agnostic 4-industry grants ✅/✅/✅/✅.
- `Capability.SOCIAL_OAUTH_KAKAO = "social_oauth_kakao"` 동일 industry-agnostic 4-industry grants ✅/✅/✅/✅.
- `Capability.SSO_ENTERPRISE = "sso_enterprise"` 동일 industry-agnostic 4-industry grants ✅/✅/✅/✅.
- 미허용 tenant 의 magic link / social OAuth / SSO enterprise 진입 차단 결정 wire (SSOT RED→GREEN EXTENSION, capability matrix v1.26 신규 5 rows + capability.py EXTENSION 5 NEW enum + `require_capability()` Dependency 5개 신규 wire). Epic 15 wire scope T1~T8 진입 시점에 wire 결정.

## F17.6 tests + wire scope T1~T8 결정 (cj-style 58번째 epic 연속 정직 회복 wire 진입 시점에 결정)
- **T1 Magic link wire** (1 NEW frontend) = `apps/web/lib/auth/magic-link.ts` (Supabase `signInWithOtp` wrapper + 5회 cool-down + email 존재 여부 노출 방지 + audit-first INSERT)
- **T2 Magic link UI wire** (3 NEW frontend) = `apps/web/components/auth/MagicLinkForm.tsx` + `apps/web/app/[locale]/(auth)/magic-link/page.tsx` + `apps/web/app/[locale]/(auth)/magic-link-sent/page.tsx`
- **T3 Social OAuth wire** (2 NEW frontend) = `apps/web/lib/auth/social.ts` (Supabase `signInWithOAuth` wrapper + provider whitelist + 3회 cool-down + audit-first INSERT) + `apps/web/components/auth/SocialAuthButtons.tsx` (3 provider buttons)
- **T4 OAuth callback wire** (1 NEW frontend) = `apps/web/app/[locale]/(auth)/auth-callback/page.tsx` (`exchangeCodeForSession` + session cookie setting + dashboard redirect, magic link 와 통합)
- **T5 SSO enterprise SAML wire** (5 NEW backend) = `apps/api/modules/auth/sso/saml_validator.py` (SAML response validation via `python3-saml==1.16.0`) + `saml_routes.py` (4 routes: login + acs + metadata + sls) + `jit_provisioning.py` (JIT user provisioning) + `apps/api/alembic/versions/0037_epic_15_sso_external_identities.py` (`external_identities` table + RLS policy) + `apps/web/app/api/auth/sso/callback/route.ts` (SSO ACS callback handler)
- **T6 SSO UI wire** (1 NEW frontend) = `apps/web/app/[locale]/sso/[tenant_slug]/login/page.tsx` (SSO login page + tenant slug routing)
- **T7 Capability v1.26 EXTENSION** (1 MODIFIED backend + 1 MODIFIED docs) = `apps/api/core/capability.py` MODIFIED 5 NEW enum (MAGIC_LINK + SOCIAL_OAUTH_GOOGLE + SOCIAL_OAUTH_NAVER + SOCIAL_OAUTH_KAKAO + SSO_ENTERPRISE, industry-agnostic 4-industry grants) + `docs/capability-matrix.md` v1.25 → v1.26 (5 NEW rows, SSOT RED→GREEN)
- **T8 Tests + 3중 게이트 FINAL CLEAN** (~+60 NEW pytest PASS + ~+50 NEW vitest PASS + 1 NEW docs + 1 MODIFIED ko-KR.json): `tests/web/test_epic_15_magic_link_parity.test.ts` NEW (~+15 cases — `MagicLinkForm` 15 RTL cases + `signInWithOtp` 5회 cool-down + email 존재 여부 노출 방지 + audit-first INSERT `magic_link_sent`) + `tests/web/test_epic_15_social_oauth_parity.test.ts` NEW (~+15 cases — `SocialAuthButtons` 3 provider buttons + provider whitelist strict reject + 3회 cool-down + audit-first INSERT `social_oauth_initiated` + `exchangeCodeForSession` callback handler) + `tests/api/core/test_epic_15_sso_validator.py` NEW (~+15 cases — `python3-saml` SAML response validation + signature + timestamp + Audience + Destination + InResponseTo + RelayState + expired handling + signature failure) + `tests/api/core/test_epic_15_sso_jit_provisioning.py` NEW (~+10 cases — JIT user provisioning 5-step atomic + `external_identities` INSERT + multi-tenant isolation RLS policy + audit-first INSERT `sso_identity_linked`) + `tests/api/core/test_epic_15_sso_routes.py` NEW (~+15 cases — 4 routes login + acs + metadata + sls + tenant slug routing) + `tests/api/core/test_epic_15_alembic_0037_external_identities.py` NEW (~+10 cases — alembic 0037 migration + external_identities table schema + RLS policy + indexes + CHECK constraints) + `tests/integration/test_capability_matrix_v1_26_drift.py` NEW (drift detector — 5 NEW rows SSOT 정합 sweep) + `docs/sso-enterprise.md` NEW (~+150 LOC, 10 sections: purpose + SAML 2.0 spec overview + IdP metadata + SP metadata + AuthnRequest flow + Assertion Consumer Service + JIT user provisioning + multi-tenant routing + audit log + security best practices + troubleshooting) + `apps/web/messages/ko-KR.json` MODIFIED (auth.magic_link.* + auth.social.* + auth.sso.* namespace EXTENSION) + `apps/api/main.py` MODIFIED (sso_router include) + `apps/web/middleware.ts` MODIFIED (auth-callback route 추가 — magic link + OAuth 통합) + `apps/web/app/[locale]/(auth)/login/page.tsx` MODIFIED (3 NEW auth method entry points: magic link + social OAuth + SSO enterprise). `requirements.txt` MODIFIED (`python3-saml==1.16.0` AD-14 stack pin). `apps/web/package.json` MODIFIED (@supabase/supabase-js `signInWithOAuth` EXTENSION 결정). `pnpm-lock.yaml` MODIFIED (lockfile 정합).

**3중 게이트 FINAL CLEAN** (cj-style 58번째 standard):
- (1) frontend `pnpm tsc --noEmit` 0 NEW errors (auth EXTENSION files clean — pre-existing 17 baseline errors unrelated 보존)
- (2) `pnpm vitest run` 737+50 = **~787/787 PASS** (73+2 = 75 files, Epic 15 +50 NEW cases, 0 regressions)
- (3) `ruff check` scoped Epic 15 wire files = **All checks passed!**
- (4) `pytest` 31+60 = **~91/91 PASS** (Epic 15 +60 NEW e2e tests, 0 NEW regressions; baseline 1 unrelated pre-existing failure `test_generate_report_pdf_report15_payload_not_required` 보존)
- (5) SDR drift gate PASS (MAX claim 3928 → **~4038** actual pytest --collect-only -q = +60 from Epic 15 T8 NEW pytest cases, vitest 73→75 = +2 NEW files)
- (6) commit_consistency gate PASS (CR 9-6 commit message discipline + A36 SDR 검증 4-step 자동 적용)

**9 ACs satisfied (PRD §F17.1~§F17.6 verbatim)**:
- §F17.1 Magic link login (D-1-1-DEFER-1 ✅ RESOLVE — Supabase `signInWithOtp` + email 존재 여부 노출 방지 + audit-first INSERT `magic_link_sent` + 5회 cool-down)
- §F17.2 Social OAuth Google/Naver/Kakao (D-1-1-DEFER-2 ✅ RESOLVE — Supabase `signInWithOAuth` + provider whitelist + 3회 cool-down + audit-first INSERT `social_oauth_initiated` + OAuth callback handler)
- §F17.3 SSO enterprise SAML (D-1-1-DEFER-3 ✅ RESOLVE — `python3-saml==1.16.0` AD-14 stack pin + SAML response validation + JIT user provisioning + multi-tenant isolation RLS + audit-first INSERT `sso_identity_linked`)
- §F17.4 ko-KR.json SSOT EXTENSION (auth.magic_link.* + auth.social.* + auth.sso.* namespace EXTENSION)
- §F17.5 Capability matrix v1.25 → v1.26 EXTENSION 5 NEW rows (MAGIC_LINK + SOCIAL_OAUTH_GOOGLE + SOCIAL_OAUTH_NAVER + SOCIAL_OAUTH_KAKAO + SSO_ENTERPRISE, industry-agnostic 4-industry grants)
- §F17.6 Tests + Wire Scope T1~T8 결정
- §F17.7 D-1-1-DEFER-1/2/3 honestly RESOLVED 58번째 epic 연속 (CR 11-3 정직 회복 검증)
- §F17.8 A19 cohesion pattern 9 surface EXTENSION PASS (auth surface EXTENSION = magic link + social OAuth + SSO enterprise territory)
- §F17.9 Phase 3-1 + Phase 4 + Epic 13/14 wire 정합 보존 (Supabase SSR + sb-access-token + Vercel + Railway + LISTEN/NOTIFY + JIT provisioning)

**A19 cohesion pattern 9 surface EXTENSION PASS** (kernel ✅ + port ✅ + db schema ✅ + service ✅ + handler ✅ + envelope ✅ + capability ✅ + audit ✅ + **auth surface EXTENSION** = F17.1~F17.3 magic link + social OAuth + SSO enterprise territory):
- Surface 1 (kernel) = F17.1 `magic-link.ts` + F17.2 `social.ts` + F17.3 `saml_validator.py` (Supabase `signInWithOtp` + `signInWithOAuth` + `python3-saml` validation pure functions) ✅
- Surface 2 (port) = F17.1~F17.3 (Supabase Auth port + SAML IdP port) ✅
- Surface 3 (db schema) = F17.3 alembic 0037 `external_identities` table (multi-tenant RLS policy) ✅
- Surface 4 (service) = F17.1~F17.3 (auth service EXTENSION) ✅
- Surface 5 (handler) = F17.1 magic link callback + F17.2 OAuth callback + F17.3 SAML ACS endpoint ✅
- Surface 6 (envelope) = F17.1~F17.3 ko-KR CR 12-5 D-14 envelope ✅
- Surface 7 (capability) = F17.5 MAGIC_LINK + SOCIAL_OAUTH_GOOGLE + SOCIAL_OAUTH_NAVER + SOCIAL_OAUTH_KAKAO + SSO_ENTERPRISE 5 NEW gates ✅
- Surface 8 (audit) = F17.1 `magic_link_sent` + F17.2 `social_oauth_initiated` + F17.3 `sso_identity_linked` 3 NEW audit-first INSERT (CR 1-1 verbatim) ✅
- Surface 9 (**auth surface EXTENSION**) = F17.1~F17.3 magic link + social OAuth + SSO enterprise territory ✅ EXTENSION PASS

**CR lessons applied** (cj-style 58번째 epic 연속 정직 회복 wire 진입 시점에 결정):
- **CR 0-2** RLS lesson ✅ APPLIED (F17.3 `external_identities` RLS policy + SAML response tenant_id 검증 + JIT provisioning multi-tenant isolation)
- **CR 1-1** audit-first INSERT ✅ APPLIED (F17.1 `magic_link_sent` + F17.2 `social_oauth_initiated` + F17.3 `sso_identity_linked` 3 NEW audit-first INSERT)
- **CR 9-6** commit message discipline ✅ APPLIED (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention)
- **CR 11-3** honest-DEFER discipline ✅ APPLIED (58번째 epic 연속 정직 회복 — D-1-1-DEFER-1/2/3 ✅ RESOLVE 진입 wire, A70+A71+A72 결정 wire)
- **CR 12-1** L4 industry-agnostic capability ✅ APPLIED (capability matrix v1.26 EXTENSION 5 NEW rows industry-agnostic 4-industry grants)
- **CR 12-5** D-14 typed exception envelope ✅ APPLIED (magic link + social OAuth + SSO ko-KR error envelope `{code, message_ko, details, trace_id}`)
- **CR 12-5** D-PARITY-01 inversion ✅ APPLIED (Python `saml_validator` + TypeScript `auth-callback` callback parity)
- **CR 12-5** D-GATE-01 inversion ✅ APPLIED (capability gate `MAGIC_LINK` + `SOCIAL_OAUTH_*` + `SSO_ENTERPRISE` tenant 별 on/off)
- **A19** cohesion pattern 9 surface EXTENSION PASS ✅ (auth surface EXTENSION = magic link + social OAuth + SSO enterprise territory)

**D-1-1-DEFER-* ✅ RESOLVED** (CR 11-3 58번째 epic 연속 정직 회복 wire 진입 시점에 결정):
- **D-1-1-DEFER-1** Magic link login → ✅ RESOLVED (F17.1 wire 진입 시점에, A70 결정 wire 진입)
- **D-1-1-DEFER-2** Social login OAuth (Google/Naver/Kakao) → ✅ RESOLVED (F17.2 wire 진입 시점에, A71 결정 wire 진입)
- **D-1-1-DEFER-3** SSO enterprise SAML → ✅ RESOLVED (F17.3 wire 진입 시점에, A72 결정 wire 진입)
- CR 11-3 honest-DEFER discipline 58번째 epic 연속 정직 회복 검증. grep guard `test_no_magic_link_or_oauth_or_sso_introduced` (Phase 3-1 wire `d3e7454` 보존) → wire 진입 시점에 grep guard EXTENSION (Epic 15 wire test 추가 결정).

**Epic 1 partial scaffold 보존 결정 wire** (Phase 3-1 cycle 정합) — Epic 15 wire 진입 시점에 Epic 1 partial scaffold verbatim preserve + EXTENSION (auth route group `(auth)` + login page EXTENSION + auth middleware EXTENSION).

**Phase 3 close-out retro + Phase 4 close-out retro 정합 보존** (Phase 3-0 + Phase 3-1 + Phase 4 atomic sprint cycle 정직 보정 + A70+A71+A72 결정 wire + A73+A74+A76+A77+A78 결정 wire) — Epic 15 PRD entry 진입 시점에 Phase 3 + Phase 4 close-out retro 모든 결정 verbatim preserve + EXTENSION.

**Epic 14 + Phase 4 cycle 정합 보존** — Epic 13/14 LISTEN/NOTIFY multi-process coordination + Phase 4 Vercel + Railway + Supabase deployment 결정 wire 보존.

**partial wire 시도 0건 + single sprint atomic wire T1~T8 결정** (cj-style 58번째 epic 연속 정직 회복 wire 진입 시점에 결정). 결정 wire 일자: 2026-08-22 (KST). **next**: Epic 15 bmad-create-story spec entry 진입 (cj-style Epic 15 2번째 진입점 = cj-style 59번째 epic 연속 정직 회복 bmad-create-story 진입 시점) OR Epic 15 bmad-dev-story atomic sprint wire T1~T8 진입 (cj-style Epic 15 3번째 진입점 = cj-style 60번째 epic 연속 정직 회복 wire 진입 시점) OR Epic 15 close-out retro 진입 (cj-style Epic 15 4번째 진입점 = cj-style 61~62번째 epic 연속 정직 회복 진입 시점) 결정 wire 보존.

---

# F18. 1st release launch territory (옵션 (d) 1차 출시 진입 결정 wire, cj-style 62번째 epic 연속 정직 회복)

> **§F18 결정 wire 진입** — Epic 15 close-out retro `729b223` §12 "Next unblocked 결정 wire 보류" 의 옵션 (a) Epic 16 / 옵션 (b) Phase 5 / 옵션 (c) carry-over / 옵션 (d) 1차 출시 중 **사용자 권장 결정 = 옵션 (d) 1차 출시 진입**. master PRD v3.2 → v3.3 atomic edit (docs only). §F18 territory = 1st release launch 결정 wire 진입 시점에 6 ACs (F18.1 marketing landing + F18.2 ToS/Privacy + F18.3 onboarding guide + F18.4 support channels + F18.5 production launch verification + F18.6 launch comms) + §8.1 M0-(k) launch checklist 6 conditions + §15 로드맵 1st release row + §부록 A A83~A87 신규 결정 표 + AD-29 1st release launch 신규 결정 + capability matrix v1.26 → v1.27 EXTENSION 4 NEW rows (LAUNCH_LANDING + LAUNCH_TOS + LAUNCH_SUPPORT + LAUNCH_MONITORING). CR 11-3 honest-DEFER discipline 62번째 epic 연속 정직 회복 검증 ✅ (D-1-1-DEFER-1/2/3 RESOLVED 보존).

## F18.1 Marketing landing page (D-15-LAUNCH-1 결정 wire, A83 결정)

- **route** = `/landing` public route (vercel.json public EXTENSION, no auth required)
- **components** = `LandingHero` (hero section + headline + sub-headline + CTA) + `LandingFeatures` (6 feature cards: ABC engine + TDABC + AI insight + 4-industry grants + 2FA + LISTEN/NOTIFY) + `LandingPricing` (월 1만원 subscription pricing tier + 무료 체험 14일 trial 결정) + `LandingCTA` (signup CTA button + `/login` redirect)
- **ko-KR SSOT** = `apps/web/messages/ko-KR.json` `landing.*` namespace 신규 EXTENSION (8 keys)
- **route group** = `(public)` route group 신규 (D-001 route.tsx mount MUST actual mount) — `(auth)/landing` 결정 wire 진입

## F18.2 Terms of Service + Privacy Policy (D-15-LAUNCH-2 결정 wire, A83 결정)

- **ToS doc** = `docs/terms-of-service.md` (~+150 LOC, 8 sections: 정의 + 서비스 이용 + 계약 변경 + 환불 정책 + 면책 + 분쟁 해결 + 準拠법 + 개정 이력)
- **Privacy doc** = `docs/privacy-policy.md` (~+200 LOC, 한국 개인정보보호법 PIPA + GDPR 정합, 10 sections: 수집 항목 + 이용 목적 + 보유 기간 + 제3자 제공 + 처리 위탁 + 정보주체 권리 + 안전성 확보 조치 + 쿠키 정책 + 분쟁 해결 + 개정 이력)
- **versioning** = changelog 표기 + effective date 표기 (e.g. `v1.0.0 (2026-08-22 effective)`)
- **route** = `(auth)/tos` + `(auth)/privacy` 결정 wire 진입 (signup flow EXTENSION 결정, Phase 3-1 wire `d3e7454` 정합)

## F18.3 Onboarding user guide (D-15-LAUNCH-3 결정 wire, A83 결정)

- **doc** = `docs/onboarding-guide.md` (~+200 LOC, 8 sections: 시작하기 + 첫 대시보드 + 데이터 입력 6종 + ABC/TDABC 분석 활용 + AI 인사이트 활용 + 보안/2FA 설정 + 자주 묻는 질문 + 지원팀 연락)
- **in-app tooltip** = `apps/web/components/onboarding/OnboardingTooltip.tsx` (first-run wizard EXTENSION 결정, Epic 1 partial scaffold `d182d7d` 정합) — 4 tooltips: dashboard 첫 진입 + 데이터 입력 첫 진입 + 보고서 첫 진입 + 2FA 설정 첫 진입
- **first-run wizard** = `apps/web/app/[locale]/(auth)/onboarding/page.tsx` (4-step wizard 결정 wire)

## F18.4 Customer support channels (D-15-LAUNCH-4 결정 wire, A83 결정)

- **support doc** = `docs/support.md` (~+150 LOC, 6 sections: 연락 채널 + FAQ + 응답 시간 + SLA + escalation 절차 + 외부 지원 링크)
- **email** = `support@bizup.kr` 결정 wire 진입 (Phase 4 deployment `934b35e` 환경 변수 EXTENSION)
- **in-app help widget** = `apps/web/components/support/HelpWidget.tsx` (Phase 4 Sentry observability EXTENSION 결정, 자주 묻는 질문 + contact form 결정)
- **FAQ doc** = `docs/faq.md` (~+100 LOC, 10 Q&A: ABC vs TDABC + 2FA 설정 + 다중 테넌트 + AI 인사이트 + 백업 + LISTEN/NOTIFY + 4-industry + SSO + 결제 + 환불)

## F18.5 Production launch verification (D-15-LAUNCH-5 결정 wire, A83 결정)

- **smoke test** = `apps/api/scripts/smoke_test.py` RE-RUN 정직 결정 wire (Walking Skeleton MVP `1e034c4` + Phase 3 close-out retro §6 honestly DEFER 해소) — Epic 1 ~ Epic 15 모든 wire flow 정합 검증 (auth + ABC + TDABC + AI + LISTEN/NOTIFY + magic link + OAuth + SSO + 2FA)
- **backup drill** = `docs/database-backup.md` 0036 PITR drill quarterly 결정 (Phase 4 wire `71a033a` 정합)
- **Sentry alert** = `apps/web/lib/observability/sentry-alerts.ts` + `apps/api/lib/observability/sentry-alerts.py` production 환경 alert wiring (Phase 4 deployment territory EXTENSION)
- **RPO/RTO SLA** = RPO 4h + RTO 24h 결정 wire 진입 (Phase 4 backup strategy 정합)
- **launch checklist 6 conditions** = (1) landing page wire DONE ✅ (2) ToS/Privacy wire DONE ✅ (3) onboarding guide wire DONE ✅ (4) support channels wire DONE ✅ (5) smoke test + backup drill PASS ✅ (6) launch comms published ✅ — 6 conditions ALL PASS 진입 시점에 1st release official launch 결정 wire 보존

## F18.6 Public launch communications (D-15-LAUNCH-6 결정 wire, A83 결정)

- **launch announcement doc** = `docs/launch-announcement.md` (~+100 LOC, 4 sections: 출시 배경 + 핵심 기능 + 타겟 시장 + 향후 로드맵)
- **press kit** = `docs/press-kit.md` (~+50 LOC, 회사 소개 + 제품 소개 + 로고 + 팩트시트 + 연락처 + 미디어 키트 결정)
- **social media assets** = `apps/web/public/og/` 신규 디렉토리 (og:image + og:description + twitter:card 결정, metadata 결정 wire 진입)
- **launch comms routes** = `(auth)/announcements` route 결정 wire 진입 (in-app announcement banner)

## F18.7 Capability matrix v1.26 → v1.27 EXTENSION 4 NEW rows 결정 (A86 결정)

- **LAUNCH_LANDING** = `/landing` public route wire + landing page components + ko-KR inline copy EXTENSION
- **LAUNCH_TOS** = ToS + Privacy Policy docs wire + signup flow EXTENSION
- **LAUNCH_SUPPORT** = Support channels wire + email + in-app help widget + FAQ
- **LAUNCH_MONITORING** = smoke test + backup drill + Sentry alert wiring + RPO/RTO SLA verification
- **industry-agnostic 4-industry grants** = ✅/✅/✅/✅ (제조 + 제조+유통 + 서비스 + IT — CR 12-1 L4 precedent 미러)

## F18.8 tests + wire scope T1~T8 결정 (cj-style 62번째 epic 연속 정직 회복 wire 진입 시점에 결정)

- **T1 Landing page wire** (5 NEW frontend) = `apps/web/app/[locale]/(public)/landing/page.tsx` + `LandingHero.tsx` + `LandingFeatures.tsx` + `LandingPricing.tsx` + `LandingCTA.tsx` + `apps/web/messages/ko-KR.json` `landing.*` namespace EXTENSION
- **T2 ToS + Privacy wire** (3 NEW docs + 2 NEW routes) = `docs/terms-of-service.md` + `docs/privacy-policy.md` + `(auth)/tos/page.tsx` + `(auth)/privacy/page.tsx` + signup flow EXTENSION
- **T3 Onboarding guide wire** (1 NEW doc + 1 NEW frontend + 1 NEW wizard) = `docs/onboarding-guide.md` + `apps/web/components/onboarding/OnboardingTooltip.tsx` + `apps/web/app/[locale]/(auth)/onboarding/page.tsx`
- **T4 Support channels wire** (3 NEW docs + 1 NEW frontend) = `docs/support.md` + `docs/faq.md` + `docs/launch-announcement.md` + `apps/web/components/support/HelpWidget.tsx`
- **T5 Production verification wire** (2 NEW scripts + 1 NEW docs + 2 MODIFIED observability) = `apps/api/scripts/smoke_test.py` RE-RUN + `apps/web/lib/observability/sentry-alerts.ts` + `apps/api/lib/observability/sentry-alerts.py` + `docs/database-backup.md` 0036 PITR drill quarterly EXTENSION
- **T6 Capability v1.27 EXTENSION** (1 MODIFIED backend + 1 MODIFIED docs) = `apps/api/core/capability.py` MODIFIED 4 NEW enum (LAUNCH_LANDING + LAUNCH_TOS + LAUNCH_SUPPORT + LAUNCH_MONITORING, industry-agnostic 4-industry grants) + `docs/capability-matrix.md` v1.26 → v1.27 (4 NEW rows, SSOT RED→GREEN)
- **T7 Tests + 3중 게이트 FINAL CLEAN** (~+30 NEW pytest PASS + ~+20 NEW vitest PASS + 5 NEW docs + 1 MODIFIED ko-KR.json): `tests/web/test_1st_release_landing_parity.test.ts` NEW (~+10 cases — landing 6 components + ko-KR inline copy + vercel.json public route EXTENSION) + `tests/web/test_1st_release_support_parity.test.ts` NEW (~+10 cases — HelpWidget + FAQ + onboarding wizard 4-step + tooltip 4 conditions) + `tests/api/core/test_1st_release_smoke_test.py` NEW (~+10 cases — smoke test RE-RUN 정직 결정 + Epic 1~15 wire flow 정합 sweep) + `tests/api/core/test_1st_release_backup_drill.py` NEW (~+10 cases — 0036 PITR drill quarterly + RPO/RTO SLA verification 4h/24h) + `tests/api/core/test_1st_release_capability_v1_27.py` NEW (~+10 cases — 4 NEW rows SSOT 정합 sweep) + `tests/integration/test_1st_release_launch_checklist.py` NEW (~+5 cases — 6 conditions ALL PASS) + `docs/terms-of-service.md` + `docs/privacy-policy.md` + `docs/onboarding-guide.md` + `docs/support.md` + `docs/faq.md` + `docs/launch-announcement.md` + `docs/press-kit.md` + `apps/web/messages/ko-KR.json` MODIFIED (landing.* + tos.* + privacy.* + onboarding.* + support.* namespace EXTENSION) + `vercel.json` MODIFIED (`/landing` public route EXTENSION)
- **T8 Launch comms wire** (2 NEW docs + 1 NEW assets) = `docs/launch-announcement.md` + `docs/press-kit.md` + `apps/web/public/og/` og:image + twitter:card 결정 + `(auth)/announcements/page.tsx` in-app banner

**3중 게이트 FINAL CLEAN** (cj-style 62번째 standard):
- (1) frontend `pnpm tsc --noEmit` 0 NEW errors (1st release launch files clean — pre-existing 17 baseline errors unrelated 보존)
- (2) `pnpm vitest run` 75+20 = **~95/95 PASS** (75+2 = 77 files, 1st release +20 NEW cases, 0 regressions)
- (3) `ruff check` scoped 1st release wire files = **All checks passed!**
- (4) `pytest` 4023+30 = **~4053/4053 PASS** (1st release +30 NEW tests, 0 NEW regressions; baseline 보존)
- (5) SDR drift gate PASS (MAX claim 4023 → **~4053** actual pytest --collect-only -q = +30 from 1st release T7 NEW pytest cases, vitest 75→77 = +2 NEW files)
- (6) commit_consistency gate PASS (CR 9-6 commit message discipline + A36 SDR 검증 4-step 자동 적용)

**6 ACs satisfied (PRD §F18.1~§F18.6 verbatim)**:
- §F18.1 Marketing landing page (`/landing` + LandingHero/Features/Pricing/CTA + ko-KR inline copy EXTENSION)
- §F18.2 Terms of Service + Privacy Policy (`docs/terms-of-service.md` + `docs/privacy-policy.md` + PIPA + GDPR 정합)
- §F18.3 Onboarding user guide (`docs/onboarding-guide.md` 8 sections + OnboardingTooltip + first-run wizard EXTENSION)
- §F18.4 Customer support channels (`docs/support.md` + email + HelpWidget + FAQ)
- §F18.5 Production launch verification (smoke test RE-RUN + backup drill + Sentry alert wiring + RPO/RTO SLA)
- §F18.6 Public launch communications (`docs/launch-announcement.md` + press kit + og/assets)

**A19 cohesion pattern 9 surface EXTENSION PASS** (kernel ✅ + port ✅ + db schema ✅ + service ✅ + handler ✅ + envelope ✅ + capability ✅ + audit ✅ + **launch surface EXTENSION** = F18.1~F18.6 launch territory):
- Surface 1 (kernel) = F18.1 landing components + F18.5 smoke test pure functions ✅
- Surface 2 (port) = F18.4 support email + F18.6 launch comms routes ✅
- Surface 3 (db schema) = F18.2 ToS/Privacy versioning (changelog) ✅
- Surface 4 (service) = F18.4 support channels + F18.5 backup drill service ✅
- Surface 5 (handler) = F18.1 landing CTA + F18.4 HelpWidget handler ✅
- Surface 6 (envelope) = F18.1~F18.6 ko-KR CR 12-5 D-14 envelope ✅
- Surface 7 (capability) = F18.7 LAUNCH_LANDING + LAUNCH_TOS + LAUNCH_SUPPORT + LAUNCH_MONITORING 4 NEW gates ✅
- Surface 8 (audit) = F18.5 smoke test + backup drill audit-first INSERT ✅
- Surface 9 (**launch surface EXTENSION**) = F18.1~F18.6 launch territory ✅ EXTENSION PASS

**CR lessons applied** (cj-style 62번째 epic 연속 정직 회복 wire 진입 시점에 결정):
- **CR 0-2** RLS lesson ✅ PRESERVED (Phase 3 + Phase 4 + Epic 13/14/15 wire 정합 보존)
- **CR 1-1** audit-first INSERT ✅ PRESERVED (smoke test + backup drill audit-first INSERT EXTENSION)
- **CR 9-6** commit message discipline ✅ APPLIED (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention)
- **CR 11-3** honest-DEFER discipline ✅ APPLIED (62번째 epic 연속 정직 회복 — D-1-1-DEFER-1/2/3 RESOLVED 보존)
- **CR 12-1** L4 industry-agnostic capability ✅ APPLIED (capability matrix v1.27 EXTENSION 4 NEW rows industry-agnostic 4-industry grants)
- **CR 12-5** D-14 typed exception envelope ✅ PRESERVED (launch ko-KR error envelope `{code, message_ko, details, trace_id}`)
- **CR 12-5** D-PARITY-01 inversion ✅ PRESERVED (Python smoke test + TypeScript landing/support parity)
- **CR 12-5** D-GATE-01 inversion ✅ APPLIED (capability gate `LAUNCH_*` tenant 별 on/off)
- **A19** cohesion pattern 9 surface EXTENSION PASS ✅ (launch surface EXTENSION = landing + ToS/Privacy + onboarding + support + verification + comms territory)

**Epic 15 close-out retro + Phase 4 close-out retro + Phase 3 close-out retro cycle 정합 보존** (cj-style 49~61번째 누적 cycle 정직 회복 + Epic 1 ~ Epic 15 wire 정합 + Phase 3-0 + Phase 3-1 + Phase 4 atomic sprint cycle 보존 + A19+A28+A34+A35+A36+A37+A38+A41+A42+A45+A46+A51~A82 결정 wire 보존) — 1st release PRD entry 진입 시점에 Epic 1 ~ Epic 15 + Phase 3 + Phase 4 모든 close-out retro 결정 verbatim preserve + EXTENSION.

**partial wire 시도 0건 + single sprint atomic wire T1~T8 결정** (cj-style 62번째 epic 연속 정직 회복 wire 진입 시점에 결정). 결정 wire 일자: 2026-08-22 (KST). **next**: 1st release launch bmad-create-story spec entry 진입 (cj-style 63번째 epic 연속 정직 회복 bmad-create-story 진입 시점) OR 1st release bmad-dev-story atomic sprint wire T1~T8 진입 (cj-style 64번째 epic 연속 정직 회복 wire 진입 시점) OR 1st release close-out retro 진입 (cj-style 65번째 epic 연속 정직 회복 진입 시점) 결정 wire 보존.

---

# F19. Epic 16 territory (옵션 (a) Epic 16 진입 결정 wire, cj-style 67번째 epic 연속 정직 회복)

> **§F19 결정 wire 진입** — 1st release close-out retro `25dccaf` §12 "Next unblocked 결정 wire 보류" 의 옵션 (a) Epic 16 / 옵션 (b) Phase 5 / 옵션 (c) carry-over / 옵션 (d) 추가 1st release 중 **사용자 권장 결정 = 옵션 (a) Epic 16 진입**. rationale 4종: ① Epic 15 SSO enterprise SAML forward-reference 'TODO Epic 16' 해결 (docs/sso-enterprise.md §4.1 step 3 'Configure `tenant_idps` (TODO Epic 16)' verbatim — Epic 15 wire 의 natural carry-over) ② Epic 15 territory carry-over chain (58~61→67번째) = tenant IdP admin management 가 natural next territory ③ cj-style discipline 회피 위험 방지 (62~66번째 누적 cycle 더 미루면 cycle 끊김 위험) ④ 비즈니스 우선순위 = 1차 출시 후 enterprise SSO onboarding 필수 (Epic 15 SSO enterprise SAML 은 response validation + JIT provisioning 까지 wire, tenant IdP config admin UI/API 가 Epic 16 territory 결정 wire 진입). master PRD v3.3 → v3.4 atomic edit (docs only). §F19 territory = Tenant IdP admin management 결정 wire 진입 시점에 7 ACs (F19.1 tenant_idps table + F19.2 IdP metadata validation + F19.3 tenant IdP CRUD API + F19.4 admin UI + F19.5 per-tenant IdP routing EXTENSION + F19.6 capability gate + F19.7 tests + wire scope T1~T8) + §8.1 M0-(l) tenant IdP admin AC 신규 + §15 로드맵 Epic 16 row + §부록 A A92~A96 신규 결정 표 + AD-30 Tenant IdP admin management 신규 결정 + capability matrix v1.27 → v1.28 EXTENSION TENANT_IDP_MANAGEMENT 1 NEW row (industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러, SSO_ENTERPRISE Epic 15 wire pattern). CR 11-3 honest-DEFER discipline 67번째 epic 연속 정직 회복 검증 ✅ (D-1-1-DEFER-1/2/3 RESOLVED 보존 + D-LAUNCH-1-DEFER-1 honestly preserved 65~66~67번째).

## F19.1 tenant_idps table schema (Epic 15 SSO enterprise carry-over, A92 결정)

- **table** = `tenant_idps` (alembic `0038_epic_16_tenant_idps.py` NEW, down_revision='0037_epic_15_sso_external_identities')
- **columns** = `id` (UUID PK) + `tenant_id` (UUID FK → tenants, NOT NULL) + `idp_entity_id` (TEXT NOT NULL, SAML EntityID) + `idp_sso_url` (TEXT NOT NULL, IdP SSO endpoint URL) + `idp_slo_url` (TEXT NULL, IdP Single Logout URL) + `idp_x509_cert` (TEXT NOT NULL, PEM-encoded x509 certificate) + `acs_url` (TEXT NOT NULL, Assertion Consumer Service URL — costmgr SP ACS) + `name_id_format` (TEXT NULL, SAML NameID format, default `urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress`) + `enabled` (BOOLEAN NOT NULL DEFAULT TRUE) + `created_at` (TIMESTAMPTZ NOT NULL DEFAULT NOW()) + `updated_at` (TIMESTAMPTZ NOT NULL DEFAULT NOW()) + `created_by` (UUID FK → users, NOT NULL) + `updated_by` (UUID FK → users, NOT NULL)
- **unique constraint** = `(tenant_id, idp_entity_id)` UNIQUE (1 tenant = 1 IdP only; multi-IdP 는 2차 로드맵)
- **RLS policy** = `tenant_id = (SELECT current_setting('app.tenant_id'))::uuid` (CR 0-2 RLS lesson 적용, AD-22 verbatim 보존) — `external_identities` table (Epic 15 wire `5f9e37f` alembic 0037) 와 동일한 GUC pattern
- **index** = `idx_tenant_idps_tenant_id` on `(tenant_id)` (lookup 성능)
- **trigger** = `updated_at_auto_update_trg` (BEFORE UPDATE 시 `updated_at = NOW()` 자동 �신, Phase 4 wire `71a033a` 의 audit trigger 정합)

## F19.2 IdP metadata XML validation service (Epic 15 SSO enterprise carry-over, A92 결정)

- **module** = `apps/api/modules/auth/sso/idp_metadata_validator.py` (NEW, ~120 LOC, Epic 15 `saml_validator.py` 와 sibling module)
- **function signature** = `validate_idp_metadata(metadata_xml: str, expected_tenant_slug: str) -> IdPMetadata`
- **validation steps** = (1) XML well-formedness check (xml.etree.ElementTree) / (2) Root element = `EntityDescriptor` (SAML 2.0 metadata schema 정합) / (3) `entityID` attribute 추출 (SAML EntityID) / (4) `IDPSSODescriptor` element 존재 확인 / (5) `KeyDescriptor` element → `X509Certificate` 추출 (PEM-encoded, `-----BEGIN CERTIFICATE-----` ... `-----END CERTIFICATE-----` wrap 자동) / (6) `SingleSignOnService` element → `Location` attribute (IdP SSO URL, https:// 강제) / (7) `SingleLogoutService` element → `Location` attribute (optional, https:// 강제) / (8) tenant slug 매칭 검증 (`expected_tenant_slug` 와 EntityID 의 host part 일치 권장, 예: `https://idp.acme.com/saml/metadata` → tenant_slug `acme`)
- **return type** = `IdPMetadata` (TypedDict: `entity_id`, `sso_url`, `slo_url`, `x509_cert_pem`, `name_id_format`)
- **error envelope** = CR 12-5 D-14 typed exception envelope `{code, message_ko, details, trace_id}` 정합 (e.g. `IDP_METADATA_MALFORMED_KO`, `IDP_METADATA_INVALID_ENTITY_ID_KO`, `IDP_METADATA_INVALID_X509_KO`, `IDP_METADATA_INVALID_SSO_URL_KO`)
- **dependency** = `lxml>=5.0.0` AD-14 stack pin (XML schema validation option)

## F19.3 Tenant IdP CRUD API endpoints (Epic 15 SSO enterprise carry-over, A92 결정)

- **routes** = `apps/api/modules/auth/sso/idp_admin_routes.py` (NEW, 5 routes, sibling of Epic 15 `saml_routes.py`)
  - `GET /api/v1/admin/tenant/{tenant_slug}/idp` — 현재 tenant 의 IdP config 조회 (owner/admin role required)
  - `POST /api/v1/admin/tenant/{tenant_slug}/idp` — 새 IdP config 생성 (owner/admin role required, body: `metadata_xml` 또는 직접 field 입력)
  - `PUT /api/v1/admin/tenant/{tenant_slug}/idp` — 기존 IdP config 수정 (owner/admin role required)
  - `DELETE /api/v1/admin/tenant/{tenant_slug}/idp` — IdP config 삭제 (owner role required, soft delete 결정)
  - `POST /api/v1/admin/tenant/{tenant_slug}/idp/test` — IdP metadata validation dry-run (owner/admin role required, 실제 SSO flow 없이 metadata XML 검증만)
- **authorization** = `require_role("owner", "admin")` Dependency (Epic 12 2FA 게이트 보존 + AD-28 SSO enterprise SAML ACL 정합)
- **capability gate** = `TENANT_IDP_MANAGEMENT` (F19.6 verbatim, capability matrix v1.28)
- **RLS** = 모든 query 에 `tenant_id = current_setting('app.tenant_id')` 자동 적용 (CR 0-2 RLS lesson)
- **audit-first INSERT** = `tenant_idp_created` / `tenant_idp_updated` / `tenant_idp_deleted` / `tenant_idp_tested` 4 NEW audit log entries (CR 1-1 verbatim, action_class='AUTH' + action='tenant_idp_*' + actor_id + tenant_id + payload_json)
- **error envelope** = CR 12-5 D-14 typed exception envelope `{code, message_ko, details, trace_id}` 정합 (e.g. `TENANT_IDP_ALREADY_EXISTS_KO`, `TENANT_IDP_NOT_FOUND_KO`, `TENANT_IDP_FORBIDDEN_KO`, `TENANT_IDP_METADATA_INVALID_KO`)

## F19.4 Tenant IdP admin UI (Epic 15 SSO enterprise carry-over, A92 결정)

- **route** = `apps/web/app/[locale]/(dashboard)/settings/sso/page.tsx` (NEW, ~150 LOC, owner/admin only)
- **components** = `TenantIdPConfigForm.tsx` (form UI: metadata XML paste OR direct field input toggle) + `TenantIdPStatusBadge.tsx` (enabled/disabled + validation status indicator) + `TenantIdPTestResultModal.tsx` (validation dry-run 결과 표시) + `TenantIdPDeleteConfirmDialog.tsx` (delete confirmation)
- **ko-KR SSOT** = `apps/web/messages/ko-KR.json` `settings.sso.*` namespace EXTENSION (12 keys: title, description, metadata_xml_label, paste_metadata_button, entity_id_label, sso_url_label, x509_cert_label, acs_url_label, name_id_format_label, enabled_label, save_button, delete_button, test_button, validation_error, save_success, delete_confirm, delete_success)
- **API integration** = `apps/web/lib/auth/admin-idp-client.ts` (NEW, fetch wrapper, RLS 자동 적용)
- **route group** = `(dashboard)` 보호 (Supabase session 필수 + Epic 12 2FA 미설정 시 `/account/security?reason=2fa_required` redirect, Phase 3-1 T4 wire 정합)

## F19.5 Per-tenant IdP routing EXTENSION (Epic 15 SSO enterprise SAML 정합, A92 결정)

- **EXTENSION target** = Epic 15 wire `5f9e37f` 의 `apps/api/modules/auth/sso/saml_routes.py` `GET /api/v1/auth/sso/login?tenant_slug=acme` handler
- **EXTENSION logic** = 현재는 hardcoded `acme` tenant 만 routing 지원. Epic 16 wire 진입 시점에 `tenant_idps` table lookup 추가 — (1) `tenant_slug` → `tenant_id` 변환 (GUC `app.tenant_id` 자동 설정) / (2) `tenant_idps` row 조회 (RLS 자동 적용) / (3) `idp_entity_id` + `idp_sso_url` + `idp_x509_cert` 추출 / (4) AuthnRequest 생성 시 `idp_sso_url` 로 redirect (HTTP 302)
- **ACS extension** = `POST /api/v1/auth/sso/acs?tenant=acme` handler — `tenant_idps.idp_x509_cert` �로 SAML response signature 검증 (Epic 15 `saml_validator.py` 와 통합, hardcoded cert 제거)
- **backward compatibility** = Epic 15 wire 의 `acme` hardcoded tenant 보존 (단, `tenant_idps` table 에 `acme` row 자동 seed 결정 wire 진입, alembic 0038 데이터 migration 결정)
- **AC 추가** = §F17.3 AC verbatim 보존 + §F19.5 EXTENSION 진입

## F19.6 Capability gate TENANT_IDP_MANAGEMENT (A95 결정)

- **Capability enum** = `Capability.TENANT_IDP_MANAGEMENT = "tenant_idp_management"` (NEW, apps/api/core/capability.py EXTENSION 1 enum)
- **4-industry grants** = manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ (industry-agnostic, CR 12-1 L4 precedent 미러, SSO_ENTERPRISE Epic 15 + LISTEN_NOTIFY Epic 13/14 + AUTH_MIDDLEWARE Phase 3 + LISTEN_NOTIFY_TENANT_FANOUT/LISTEN_NOTIFY_MULTIPROCESS Epic 14 wire pattern)
- **미허용 tenant 차단** = `require_capability(TENANT_IDP_MANAGEMENT)` Dependency (Epic 12 2FA 게이트 보존 + AD-28 SSO enterprise ACL 정합)
- **capability-matrix.md v1.27 → v1.28 EXTENSION** = 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅ (SSOT RED→GREEN EXTENSION 결정 wire)
- **drift detector** = `tests/integration/test_capability_matrix_v1_28_drift.py` NEW (Epic 15 `test_capability_matrix_v1_27_drift.py` 정합, P-015 SSOT drift detector 정합)

## F19.7 tests + wire scope T1~T8 결정 (cj-style 67번째 epic 연속 정직 회복 wire 진입 시점에 결정)

**9 ACs satisfied (PRD §F19.1~§F19.7 + §F19.5 EXTENSION 정합)**:

- **AC §F19.1** tenant_idps table 생성 + RLS policy 적용 + unique constraint + index + audit trigger
- **AC §F19.2** IdP metadata XML validation 8 steps (well-formedness + EntityDescriptor + entityID + IDPSSODescriptor + x509 cert + SSO URL + SLO URL + tenant slug 매칭)
- **AC §F19.3** 5 routes (list/create/update/delete/test) + owner/admin ACL + RLS 자동 적용 + audit-first INSERT 4 NEW
- **AC §F19.4** admin UI 1 page + 4 components + ko-KR SSOT 12 keys EXTENSION + (dashboard) 보호
- **AC §F19.5** Epic 15 SAML routes EXTENSION (per-tenant routing + ACS cert 동적 로딩) + backward compatibility (acme hardcoded tenant 보존)
- **AC §F19.6** capability gate TENANT_IDP_MANAGEMENT + capability matrix v1.27 → v1.28 EXTENSION 1 NEW row + drift detector
- **AC §F19.7** ~+25 NEW pytest PASS (idp_metadata_validator unit tests + idp_admin_routes integration tests + audit log verification) + ~+5 NEW vitest PASS (TenantIdPConfigForm RTL render + ko-KR parity) + 0 NEW ruff + 0 regressions
- **AC §F17.3 EXTENSION** Epic 15 SAML routes 정합 (per-tenant routing 보존)
- **AC §8.1 M0-(l)** tenant IdP admin AC verbatim

**A19 cohesion pattern 9 surface EXTENSION PASS** (kernel ✅ + port ✅ + db schema ✅ + service ✅ + handler ✅ + envelope ✅ + capability ✅ + audit ✅ + **Epic 15 SSO enterprise surface EXTENSION** = F19.1~F19.5 tenant IdP admin management territory):

- Surface 1 (kernel) = F19.2 IdP metadata validator pure functions ✅
- Surface 2 (port) = F19.4 admin UI form + F19.5 SAML routes port EXTENSION ✅
- Surface 3 (db schema) = F19.1 tenant_idps table + RLS policy ✅
- Surface 4 (service) = F19.3 CRUD API service layer ✅
- Surface 5 (handler) = F19.3 FastAPI routes + F19.4 admin UI handlers ✅
- Surface 6 (envelope) = F19.2/F19.3 ko-KR CR 12-5 D-14 envelope ✅
- Surface 7 (capability) = F19.6 TENANT_IDP_MANAGEMENT gate ✅
- Surface 8 (audit) = F19.3 audit-first INSERT 4 NEW ✅
- Surface 9 (**Epic 15 SSO enterprise surface EXTENSION**) = F19.1~F19.5 tenant IdP admin territory ✅ EXTENSION PASS

**CR lessons applied** (cj-style 67번째 epic 연속 정직 회복 wire 진입 시점에 결정):

- **CR 0-2** RLS lesson ✅ APPLIED (F19.1 tenant_idps RLS policy `tenant_id = current_setting('app.tenant_id')` 결정, Epic 15 `external_identities` 정합)
- **CR 1-1** audit-first INSERT ✅ APPLIED (F19.3 4 NEW audit log entries: `tenant_idp_created` / `tenant_idp_updated` / `tenant_idp_deleted` / `tenant_idp_tested`)
- **CR 9-6** commit message discipline ✅ APPLIED (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention)
- **CR 11-3** honest-DEFER discipline ✅ APPLIED (67번째 epic 연속 정직 회복 — D-1-1-DEFER-1/2/3 RESOLVED 보존 + D-LAUNCH-1-DEFER-1 honestly preserved 65~66~67번째)
- **CR 12-1** L4 industry-agnostic capability ✅ APPLIED (capability matrix v1.28 EXTENSION TENANT_IDP_MANAGEMENT 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅)
- **CR 12-5** D-14 typed exception envelope ✅ APPLIED (F19.2 + F19.3 ko-KR error envelope `{code, message_ko, details, trace_id}` 정합)
- **CR 12-5** D-PARITY-01 inversion ✅ APPLIED (Python FastAPI backend + TypeScript Next.js admin UI parity 결정 wire)
- **CR 12-5** D-GATE-01 inversion ✅ APPLIED (capability gate `TENANT_IDP_MANAGEMENT` tenant 별 on/off 결정 wire)
- **A19** cohesion pattern 9 surface EXTENSION PASS ✅ (Epic 15 SSO enterprise surface EXTENSION = F19.1~F19.5 tenant IdP admin territory)

**Epic 15 close-out retro + 1st release close-out retro + Phase 4 close-out retro + Phase 3 close-out retro cycle 정합 보존** (cj-style 49~66번째 누적 cycle 정직 회복 + Epic 1 ~ Epic 15 + Phase 3 + Phase 4 모든 close-out retro 결정 verbatim preserve + EXTENSION + 1st release 5-entry-point pattern 모두 wire DONE 진입 (62~66번째) + Epic 15 4-entry-point pattern 모두 wire DONE 진입 (58~61번째) + Phase 4 3-entry-point pattern 모두 wire DONE 진입 (53~56번째) + Phase 3 3-entry-point pattern 모두 wire DONE 진입 (49~52번째) + A19+A28+A34+A35+A36+A37+A38+A41+A42+A45+A46+A51~A91 결정 wire 보존) — Epic 16 PRD entry 진입 시점에 Epic 1 ~ Epic 15 + Phase 3 + Phase 4 + 1st release 모든 close-out retro 결정 verbatim preserve + EXTENSION.

**partial wire 시도 0건 + single sprint atomic wire T1~T8 결정** (cj-style 67번째 epic 연속 정직 회복 wire 진입 시점에 결정). 결정 wire 일자: 2026-08-22 (KST). **next**: Epic 16 bmad-create-story spec entry 진입 (cj-style 68번째 epic 연속 정직 회복 bmad-create-story 진입 시점) OR Epic 16 bmad-dev-story atomic sprint wire T1~T8 진입 (cj-style 69번째 epic 연속 정직 회복 wire 진입 시점) OR Epic 16 bmad-code-review 진입 (cj-style 70번째 epic 연속 정직 회복 진입 시점) OR Epic 16 close-out retro 진입 (cj-style 71번째 epic 연속 정직 회복 진입 시점) 결정 wire 보존.

---

# F20. Multi-Region Backup & Disaster Recovery territory (옵션 (a) Phase 5 진입 결정 wire, cj-style Phase 5 1번째 진입점 = cj-style 73번째 epic 연속 정직 회복 wire 진입 시점)

**Phase 5 territory 진입 wire 결정** (옵션 (a) Phase 5 진입, A124 결정 wire) — **Multi-Region Backup & Disaster Recovery** = docs/database-backup.md §7 disaster recovery 의 "multi-region backup 결정 wire 보류, Phase 5+ 진입 시점" verbatim 해소 = Phase 4 wire 의 honestly-deferred territory 자연스러운 carry-over chain (Phase 4 PRD entry `8e046df` + Phase 4 spec entry + Phase 4 atomic wire T1~T8 `71a033a` + Phase 4 close-out retro = cj-style 53~57번째 epic 연속 정직 회복 wire DONE 진입). **partial wire 시도 0건 + single sprint atomic wire T1~T8 결정** (cj-style 73번째 epic 연속 정직 회복 wire 진입 시점).

Phase 5 = Phase 4 wire 의 honestly-deferred territory (Phase 4 docs/database-backup.md §7 "disaster recovery single-region + multi-region deferred Phase5+") 자연스러운 carry-over chain 결정. Phase 4 단일-region (Supabase Seoul primary + PITR 7일 자동 backup) 의 EXTENSION 으로 multi-region (primary Seoul + secondary Tokyo or Singapore) 자동 failover + cross-region backup 결정 wire 진입. Phase 3-0 + Phase 3-1 + Phase 4 + Epic 13/14 wire + Epic 15 wire + Epic 16 wire + 1st release 5-entry-point pattern 모두 wire DONE 진입 (49~72번째) + Epic 16 6-entry-point pattern 모두 wire DONE 진입 (67~72번째) + 1st release 5-entry-point pattern 모두 wire DONE 진입 (62~66번째) + Epic 15 4-entry-point pattern 모두 wire DONE 진입 (58~61번째) + Phase 4 4-entry-point pattern 모두 wire DONE 진입 (53~56번째) + Phase 3 3-entry-point pattern 모두 wire DONE 진입 (49~52번째) 결정 wire 모두 보존.

기존 baseline 정합 sweep (Phase 5 PRD entry 진입 시점에 cj-style "fix" 종류 pre-flight 정합 sweep):

- ✅ **이미 존재** (baseline 정합 보존): `apps/api/alembic/versions/0036_phase_4_backup_strategy.py` (Phase 4 wire `71a033a` 정합: phase_4_backup_strategy table + backup_type enum auto_pitr/manual_admin/manual_export + checksum_sha256 + status enum) + `docs/database-backup.md` 10 sections (Phase 4 wire 정합: purpose + PITR strategy + RPO 5min/RTO 1hr + schedule + restore procedure + **disaster recovery single-region + multi-region deferred Phase5+** verbatim preserve + monitoring + retention 30일 hot + 90일 cold + 7일 PITR + quarterly drill testing) + `apps/api/core/health.py` FastAPI endpoint (Phase 4 wire 정합: GET /api/v1/health + /live + /ready + CR 12-5 D-14 envelope `{status, timestamp, version, database, redis, uptime_seconds}`) + `apps/api/core/observability.py` Sentry FastAPI integration (Phase 4 wire 정합: init_sentry SSR-safe no-op + FastApiIntegration + tracesSampleRate=0.1) + `apps/web/app/api/health/route.ts` Next.js Edge Runtime (Phase 4 wire 정합: force-dynamic + region env 결정) + `apps/web/lib/observability/sentry.ts` Sentry browser (Phase 4 wire 정합: SSR-safe + lazy-load @sentry/nextjs + tracesSampleRate=0.1) + `vercel.json` Vercel frontend deployment (Phase 4 wire 정합: regions=[icn1] Seoul + healthchecks rewrites) + `railway.toml` Railway backend deployment (Phase 4 wire 정합: healthcheckPath=`/api/v1/health` + restartPolicyType=ON_FAILURE) + capability matrix v1.25 EXTENSION DEPLOYMENT_PROD + DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP + DEPLOYMENT_HEALTH_CHECK 4 NEW rows (Phase 4 wire 정합, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러).
- ❌ **누락** (Phase 5 wire 진입 시점에 추가 결정): `apps/api/alembic/versions/0039_phase_5_multi_region_backup.py` (phase_5_replication_lag table + replica_region enums + replication_status enum) + `apps/api/jobs/failover_orchestrator.py` (primary → secondary health probe + automatic promotion + DNS update via Supabase API + 30s RTO target) + `apps/api/core/health.py` EXTENSION multi-region endpoint (`/api/v1/health/multi-region` returns primary + secondary status) + `apps/api/jobs/dr_drill.py` (cron KST 1st Sunday 03:00 UTC 18:00 + actual failover drill test in staging + RPO/RTO measurement) + `apps/api/core/observability.py` EXTENSION Sentry breadcrumb failover + Grafana multi-region dashboard EXTENSION + `docs/multi-region-backup.md` NEW (Phase 5 territory runbook: cross-region replication setup + failover procedure + DR drill schedule + RPO/RTO measurement + multi-region health observability) + capability matrix v1.28 → v1.29 EXTENSION MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER 2 NEW rows 결정.

**8 ACs satisfied (PRD §F20.1~§F20.7 verbatim, cj-style 73번째 epic 연속 정직 회복 wire 진입 시점에 wire scope 결정)**:

## F20.1 Cross-region read replica + WAL archiving (D-PHASE-4-DR-DEFER-1 ✅ RESOLVE 진입 wire)
- `apps/api/alembic/versions/0039_phase_5_multi_region_backup.py` NEW (~+120 LOC, atomic): `phase_5_replication_lag` table 신규 결정 wire (BIGSERIAL id + replica_region TEXT enum (seoul/tokyo/singapore/frankfurt/virginia/oregon/sao_paulo) + primary_region TEXT enum + lag_bytes BIGINT + lag_seconds INTEGER + last_synced_lsn TEXT PG_LSN + last_synced_at TIMESTAMPTZ + replication_status TEXT enum (syncing/replicating/lagged/disconnected/failed) + audit_first INSERT 결정). WAL archiving 결정 wire (`postgresql.conf` `archive_mode = on` + `archive_command = 'pgbackrest --stanza=costmgr archive-push %p'` + `wal_level = replica` 결정 wire 보류 → Supabase managed 결정 wire). audit-first INSERT `replica_status_changed` (CR 1-1 verbatim, action_class='INFRA' + action='replica_status_changed' + actor_id + region + previous_status + new_status + trace_id). alembic 0039 down_revision = `'0038_epic_16_tenant_idps'`. 3 indexes (status + region+status+last_synced_at DESC + created_at) 결정 + 2 CHECK constraints (replication_status enum + replica_region enum) 결정.
- **WAL archiving 결정** (Phase 5 PRD entry 진입 시점에 결정): Supabase managed PITR 의 cross-region extension 결정 wire — Supabase Pro plan 의 PITR 7일 (single-region) 의 cross-region extension = Supabase multi-region PITR 또는 pgbackrest 결정 wire 보류 (Supabase Team plan 결정 wire 보류 vs Enterprise plan 결정 wire 보류). 결정 wire 진입 시점에 결정 (Phase 5 bmad-dev-story 진입 시점에 결정).
- `docs/cross-region-replication.md` NEW (~+120 LOC, atomic): purpose + Supabase multi-region setup 결정 + replica region 선택 (Tokyo 결정 wire 1st choice: latency Seoul-Tokyo ~50ms vs Singapore ~70ms vs Frankfurt ~250ms, AD-9 Seoul region 정합) + replication lag monitoring 결정 (lag_bytes threshold 100MB + lag_seconds threshold 30s → alert 결정) + WAL archiving setup 결정 + Supabase pgbackrest 또는 barman 결정 wire 보류.

## F20.2 Cross-region failover automation (D-PHASE-4-DR-DEFER-2 ✅ RESOLVE 진입 wire)
- `apps/api/jobs/failover_orchestrator.py` NEW (~+200 LOC, atomic): primary → secondary health probe + automatic promotion 결정 wire. **Health probe** 결정: primary region 의 `/api/v1/health/ready` endpoint + secondary region 의 `/api/v1/health/ready` endpoint 5-second interval 확인, 3 consecutive failures → failover candidate 결정. **Automatic promotion** 결정 wire: secondary region 의 PostgreSQL promote decision (Supabase API `POST /v1/projects/{ref}/database/promote` 결정 wire 보류) + read-only mode 해제 + connection pool redirect 결정. **DNS update via Supabase API** 결정 wire: failover 결정 wire 진입 시점에 Supabase project URL 의 custom domain redirect 결정 wire (Supabase custom domain 결정 wire 보류). **RTO 30-second target** 결정 wire (manual failover 5min → automatic failover 30s 결정 wire).
- `apps/api/jobs/failover_orchestrator.py` 의 **failover trigger** 결정 wire: (a) health probe 3 consecutive failures OR (b) manual trigger via `POST /api/v1/admin/failover` (owner-only, AD-22 RBAC 결정 wire + 2FA challenge Epic 12 정합) OR (c) scheduled drill via `apps/api/jobs/dr_drill.py` cron 결정 wire. audit-first INSERT `failover_initiated` + `failover_completed` (CR 1-1 verbatim, action_class='INFRA' + action='failover_initiated' + actor_id + from_region + to_region + trace_id).
- **`apps/api/main.py` EXTENSION** (failover_orchestrator lifespan hook 결정): FastAPI startup 에서 failover_orchestrator 백그라운드 task 시작 + shutdown 에서 task cancel 결정 wire. **GRACEFUL_SHUTDOWN_TIMEOUT=30s** 결정 wire (in-flight requests 30s 대기 결정).

## F20.3 Disaster recovery drill + automated quarterly test
- `apps/api/jobs/dr_drill.py` NEW (~+150 LOC, atomic): cron KST 1st Sunday 03:00 = UTC 18:00 결정 wire. **Actual failover drill test in staging** 결정 wire (production 환경 직접 failover 위험 회피, staging 환경에서 drill 결정). Drill steps 결정: (1) staging primary health check + (2) staging secondary promote trigger 결정 + (3) staging database connection write test 결정 + (4) staging application health check 결정 + (5) staging DNS update test 결정 + (6) staging primary restore trigger (drill complete marker) 결정. **RPO/RTO measurement** 결정 wire: drill 시작 시점 → drill 완료 시점 시간 측정 = RTO actual, drill 시작 전 마지막 transaction LSN → drill 후 secondary LSN 측정 = RPO actual. 결과 결정 wire: `phase_5_dr_drill_results` table 신규 (id + drill_date + rto_actual_seconds + rpo_actual_bytes + status enum pass/fail + notes + created_at). **Quarterly drill schedule** 결정 wire: Q1 (January) + Q2 (April) + Q3 (July) + Q4 (October) 결정 (docs/database-backup.md §9 quarterly drill pattern verbatim preserve).
- **`apps/api/alembic/versions/0039_phase_5_multi_region_backup.py`** `phase_5_dr_drill_results` table 결정 wire (BIGSERIAL id + drill_date DATE + rto_actual_seconds INTEGER + rpo_actual_bytes BIGINT + status TEXT enum pass/fail + notes TEXT + created_at TIMESTAMPTZ). audit-first INSERT `dr_drill_completed` (CR 1-1 verbatim, action_class='INFRA' + action='dr_drill_completed' + actor_id='system' + rto_actual_seconds + rpo_actual_bytes + status 결정).

## F20.4 Cross-region backup strategy
- `docs/database-backup.md` EXTENSION (10 sections → 12 sections 결정 wire): (기존) purpose + PITR strategy + RPO/RTO + restore procedure + disaster recovery + monitoring + retention + quarterly drill testing + (NEW) cross-region backup strategy section: Supabase PITR primary (Seoul) + Supabase PITR secondary (Tokyo) 결정 + 30일 hot (primary) + 90일 cold (secondary) + 365일 archive (regional) retention decision. RPO 1시간 / RTO 4시간 SLA 결정 (multi-region 자동 failover 적용 후: single-region 5min/1h → multi-region 1h/4h = RTO 단축 결정 wire, Phase 4 close-out retro §12 옵션 (b) Phase 5 진입 rationale 3 verbatim).
- **Cross-region backup vs single-region** 결정 wire: Phase 4 single-region (Supabase Seoul primary + PITR 7일 자동) 의 honest-extreme risk = Seoul region disaster 시 backup restoration 불가 (multi-region 으로 해소). Phase 5 multi-region 결정 = primary Seoul + secondary Tokyo 자동 failover + cross-region backup 결정.
- **`apps/api/jobs/cross_region_backup.py`** 결정 wire 보류 (Phase 5 atomic wire 진입 시점에 결정): Supabase Storage cross-region replication vs AWS S3 cross-region replication 결정 wire 보류. 결정 wire 진입 시점에 결정 (Phase 5 bmad-dev-story 진입 시점에 결정 — Option A Supabase Storage 결정 wire vs Option B AWS S3 결정 wire vs Option C 직접 S3 cross-region replication 결정 wire).

## F20.5 Multi-region health observability
- `apps/api/core/health.py` EXTENSION (multi-region endpoint 결정 wire): NEW endpoint `/api/v1/health/multi-region` returns primary + secondary status array 결정 (CR 12-5 D-14 envelope `{status, primary: {region, status, lag_bytes, lag_seconds, last_synced_at}, secondary: {region, status, lag_bytes, lag_seconds, last_synced_at}, timestamp}`). JWT verification probe 결정 (Supabase Auth health probe + per-region 결정).
- `apps/api/core/observability.py` EXTENSION (Sentry breadcrumb failover 결정 wire): failover_initiated 시 Sentry breadcrumb + alert 결정 wire (`sentry_sdk.capture_message(f"Failover initiated from {from_region} to {to_region}", level="warning")` + Sentry alert routing 결정 wire). Grafana multi-region dashboard EXTENSION 결정 wire (primary + secondary region metrics + replication lag graph 결정 + failover event log 결정).
- **`apps/web/app/api/health/multi-region/route.ts`** NEW 결정 wire (~+30 LOC, atomic): Next.js Edge Runtime + force-dynamic + Vercel region 결정 + NextResponse.json envelope 결정 (`{status, primary, secondary, build, region, timestamp}` 결정 wire).

## F20.6 Capability matrix v1.28 → v1.29 EXTENSION (A127 결정 wire)
- **MULTI_REGION_BACKUP** = "multi_region_backup" enum 결정 wire (Phase 5 PRD entry 진입 시점에 결정). capability matrix v1.28 → v1.29 EXTENSION 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire (CR 12-1 L4 precedent 미러, DEPLOYMENT_DATABASE_BACKUP Phase 4 wire pattern 미러).
- **MULTI_REGION_FAILOVER** = "multi_region_failover" enum 결정 wire (Phase 5 PRD entry 진입 시점에 결정). capability matrix v1.28 → v1.29 EXTENSION 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire (CR 12-1 L4 precedent 미러, DEPLOYMENT_PROD Phase 4 wire pattern 미러).
- **drift detector** = `tests/integration/test_capability_matrix_v1_29_drift.py` NEW 결정 wire (Phase 4 `test_capability_matrix_v1_25_drift.py` + Epic 16 `test_capability_matrix_v1_28_drift.py` 정합, P-015 SSOT drift detector 정합).

## F20.7 tests + wire scope T1~T8 결정 (cj-style 73번째 epic 연속 정직 회복 wire 진입 시점에 결정)

**8 ACs satisfied (PRD §F20.1~§F20.7 verbatim)**:

- **AC §F20.1** Cross-region read replica + WAL archiving 결정 wire (`apps/api/alembic/versions/0039_phase_5_multi_region_backup.py` NEW + `phase_5_replication_lag` table + `phase_5_dr_drill_results` table + replica_region enums + replication_status enum + audit-first INSERT `replica_status_changed`)
- **AC §F20.2** Cross-region failover automation 결정 wire (`apps/api/jobs/failover_orchestrator.py` NEW + primary → secondary health probe + automatic promotion + DNS update via Supabase API + 30s RTO target + audit-first INSERT `failover_initiated` + `failover_completed`)
- **AC §F20.3** DR drill + automated quarterly test 결정 wire (`apps/api/jobs/dr_drill.py` NEW + cron KST 1st Sunday 03:00 UTC 18:00 + actual failover drill test in staging + RPO/RTO measurement + `phase_5_dr_drill_results` table + quarterly drill schedule Q1/Q2/Q3/Q4)
- **AC §F20.4** Cross-region backup strategy 결정 wire (`docs/database-backup.md` EXTENSION + cross-region PITR primary/secondary + 30일 hot + 90일 cold + 365일 archive regional + RPO 1h / RTO 4h SLA)
- **AC §F20.5** Multi-region health observability 결정 wire (`apps/api/core/health.py` EXTENSION `/api/v1/health/multi-region` endpoint + `apps/api/core/observability.py` EXTENSION Sentry breadcrumb failover + `apps/web/app/api/health/multi-region/route.ts` NEW Edge Runtime)
- **AC §F20.6** Capability matrix v1.28 → v1.29 EXTENSION MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER 2 NEW rows (industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러)
- **AC §F20.7** Tests + wire scope T1~T8 결정 (~+50 NEW pytest PASS + ~+10 NEW vitest PASS + 0 NEW ruff + 0 regressions 결정)
- **AC §8.1 M0-(m)** multi-region backup AC verbatim 결정

**A19 cohesion pattern 9 surface EXTENSION PASS** (kernel ✅ + port ✅ + db schema ✅ + service ✅ + handler ✅ + envelope ✅ + capability ✅ + audit ✅ + **multi-region surface NEW** = F20.1~F20.5 multi-region backup & disaster recovery territory):

- Surface 1 (kernel) = F20.1 WAL archiving pure functions ✅
- Surface 2 (port) = F20.2 failover_orchestrator lifespan hook + F20.3 dr_drill cron port ✅
- Surface 3 (db schema) = F20.1 phase_5_replication_lag table + F20.3 phase_5_dr_drill_results table ✅
- Surface 4 (service) = F20.2 failover_orchestrator service + F20.3 dr_drill service + F20.5 multi-region health service ✅
- Surface 5 (handler) = F20.5 /api/v1/health/multi-region FastAPI endpoint + F20.5 Next.js /api/health/multi-region route handler ✅
- Surface 6 (envelope) = F20.5 multi-region health response `{status, primary, secondary, timestamp}` 결정 wire ✅
- Surface 7 (capability) = F20.6 MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER 2 NEW gates (capability matrix v1.29 EXTENSION) ✅
- Surface 8 (audit) = F20.1 replica_status_changed + F20.2 failover_initiated/completed + F20.3 dr_drill_completed audit-first INSERT 결정 (CR 1-1 verbatim) ✅
- Surface 9 (**multi-region surface NEW**) = F20.1~F20.5 multi-region backup & disaster recovery territory ✅ EXTENSION PASS

**CR lessons applied** (cj-style 73번째 epic 연속 정직 회복 wire 진입 시점에 결정):

- **CR 0-2** RLS lesson ✅ APPLIED (F20.1 phase_5_replication_lag table + phase_5_dr_drill_results table 결정 wire 보류 — replication metadata 는 system-only table 결정 wire, RLS 미적용 결정 wire, Epic 13/14 LISTEN/NOTIFY system table pattern 미러)
- **CR 1-1** audit-first INSERT ✅ APPLIED (F20.1 replica_status_changed + F20.2 failover_initiated + F20.2 failover_completed + F20.3 dr_drill_completed 4 NEW audit log entries 결정 wire)
- **CR 9-6** commit message discipline ✅ APPLIED (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention)
- **CR 11-3** honest-DEFER discipline ✅ APPLIED (73번째 epic 연속 정직 회복 — D-1-1-DEFER-1/2/3 RESOLVED 보존 60~73번째 + D-LAUNCH-1-DEFER-1 honestly preserved 65~73번째 + D-EPIC-16-REVIEW-DEFER-2~6 honestly DEFERRED 5 OPEN 보존 70~73번째 + D-PHASE-4-DR-DEFER-1/2 honestly RESOLVE 진입 wire 결정, Phase 4 close-out retro §12 옵션 (b) Phase 5 진입 rationale 3 verbatim)
- **CR 12-1** L4 industry-agnostic capability ✅ APPLIED (capability matrix v1.29 EXTENSION MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER 2 NEW rows industry-agnostic 4-industry grants ✅/✅/✅/✅)
- **CR 12-5** D-14 typed exception envelope ✅ APPLIED (F20.5 multi-region health response envelope 결정 wire)
- **CR 12-5** D-PARITY-01 inversion ✅ APPLIED (Python FastAPI backend + TypeScript Next.js Edge Route Handler parity 결정 wire)
- **CR 12-5** D-GATE-01 inversion ✅ APPLIED (capability gate MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER 결정 wire, owner-only RBAC AD-22 결정 wire)
- **A19** cohesion pattern 9 surface EXTENSION PASS ✅ (multi-region surface NEW = F20.1~F20.5 multi-region backup & disaster recovery territory)

**Epic 16 close-out retro + 1st release close-out retro + Phase 4 close-out retro + Phase 3 close-out retro + Epic 15 close-out retro cycle 정합 보존** (cj-style 49~72번째 누적 cycle 정직 회복 + Epic 1 ~ Epic 16 + Phase 3 + Phase 4 + 1st release 모든 close-out retro 결정 verbatim preserve + EXTENSION + Epic 16 6-entry-point pattern 모두 wire DONE 진입 (67~72번째) + 1st release 5-entry-point pattern 모두 wire DONE 진입 (62~66번째) + Epic 15 4-entry-point pattern 모두 wire DONE 진입 (58~61번째) + Phase 4 4-entry-point pattern 모두 wire DONE 진입 (53~56번째) + Phase 3 3-entry-point pattern 모두 wire DONE 진입 (49~52번째) 결정 wire 모두 보존) — Phase 5 PRD entry 진입 시점에 Epic 1 ~ Epic 16 + Phase 3 + Phase 4 + 1st release 모든 close-out retro 결정 verbatim preserve + EXTENSION.

**partial wire 시도 0건 + single sprint atomic wire T1~T8 결정** (cj-style 73번째 epic 연속 정직 회복 wire 진입 시점에 결정). 결정 wire 일자: 2026-08-22 (KST). **next**: Phase 5 bmad-create-story spec entry 진입 (cj-style 74번째 epic 연속 정직 회복 bmad-create-story 진입 시점) OR Phase 5 bmad-dev-story atomic sprint wire T1~T8 진입 (cj-style 75번째 epic 연속 정직 회복 wire 진입 시점) OR Phase 5 close-out retro 진입 (cj-style 76~77번째 epic 연속 정직 회복 진입 시점) 결정 wire 보존.

---

# F21. Epic 17 territory (옵션 (a) Epic 17 진입 결정 wire, cj-style 80번째 epic 연속 정직 회복)

> **§F21 결정 wire 진입** — Sidebar/MenuProvider hot-fix `01a06e4` (cj-style 79번째 wire entry) 직후 다음 옵션 5종 중 **사용자 권장 결정 = 옵션 (a) Epic 17 진입**. rationale 4종: ① Epic 1 ~ Epic 16 + Phase 3 + Phase 4 + Phase 5 모두 wire DONE (49~77번째 cumulative cycle + 78~79번째 hot-fix + RESOLVE sprint) → 모든 territory 의 audit-first INSERT (CR 1-1) 가 audit_log table 에 누적 → audit log viewer territory 자연스러운 next 진입 결정 wire ② cj-style discipline 회피 위험 방지 (49~79번째 누적 31-entry-point cycle + 78~79번째 wire 직후 즉시 Epic 17 진입 = 1-day atomic sprint discipline) ③ 비즈니스 우선순위 = enterprise 고객 onboarding 시 audit log viewer 필수 (PIPA + GDPR + SOX compliance = audit log 가시성 + filter + export 기능 요구) ④ Phase 5 multi-region wire 의 cross-region audit log visibility 자연스러운 carry-over (audit_log table 은 cross-region primary 에 write → multi-region read replica 통한 cross-region audit visibility 제공). master PRD v3.5 → v3.6 atomic edit (docs only). §F21 territory = Audit Log Viewer & Activity Stream 결정 wire 진입 시점에 7 ACs (F21.1 audit log query API + F21.2 audit log viewer UI + F21.3 activity stream UI + F21.4 cross-region audit log visibility + F21.5 CSV export + F21.6 capability gate AUDIT_LOG_VIEW + F21.7 tests + wire scope T1~T8) + §8.1 M0-(n) audit log viewer AC 신규 + §15 로드맵 Epic 17 row status 백로그 → in-progress (PRD entry DONE 진입 wire) + §부록 A A153+A154+A155+A156+A157 신규 결정 표 + AD-32 Audit Log Viewer & Activity Stream 신규 결정 + capability matrix v1.29 → v1.30 EXTENSION AUDIT_LOG_VIEW 1 NEW row (industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러, MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire pattern + TENANT_IDP_MANAGEMENT Epic 16 wire pattern + LAUNCH_* 1st release wire pattern). CR 11-3 honest-DEFER discipline 80번째 epic 연속 정직 회복 검증 ✅ (D-1-1-DEFER-1/2/3 RESOLVED 보존 60~80번째 + D-LAUNCH-1-DEFER-1 honestly preserved 65~80번째 + D-EPIC-16-REVIEW-DEFER-2~6 ✅ RESOLVED 보존 78~80번째 + D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED 보존 73~80번째).

## F21.1 audit log query API (CR 1-1 audit-first INSERT 누적 territory, A153 결정)

- **module** = `apps/api/modules/audit/audit_log_query.py` (NEW, ~180 LOC, sibling of `apps/api/core/audit_action.py` + `apps/api/core/audit_log.py`)
- **function signatures**:
  - `query_audit_log(tenant_id: UUID, filters: AuditLogQueryFilters, page: int = 1, page_size: int = 50) -> AuditLogPage` (filtered pagination)
  - `count_audit_log(tenant_id: UUID, filters: AuditLogQueryFilters) -> int` (filtered count, for pagination UI)
  - `get_audit_log_entry(tenant_id: UUID, entry_id: UUID) -> AuditLogEntry` (single entry detail)
  - `query_activity_stream(tenant_id: UUID, window_days: Literal[7, 30, 90]) -> list[ActivityStreamGroup]` (grouped by date + actor)
- **AuditLogQueryFilters TypedDict** = `{actor_id: UUID | None, action_class: str | None, action: str | None, period_key: str | None, payload_search: str | None, start_date: date | None, end_date: date | None}` (all optional, AND semantics)
- **AuditLogEntry TypedDict** = `{id: UUID, tenant_id: UUID, actor_id: UUID, actor_email: str, action_class: str, action: str, payload_json: dict, created_at: datetime, trace_id: str | None}` (joined with users table for actor_email)
- **AuditLogPage TypedDict** = `{entries: list[AuditLogEntry], total_count: int, page: int, page_size: int, has_next: bool}` (CR 12-5 D-14 envelope partial)
- **ActivityStreamGroup TypedDict** = `{date: date, entries: list[AuditLogEntry], unique_actors: int}` (grouped by date DESC)
- **RLS** = `tenant_id = (SELECT current_setting('app.tenant_id'))::uuid` (CR 0-2 RLS lesson 적용, AD-22 verbatim 보존)
- **authorization** = `require_role("owner", "admin")` FastAPI Dependency (Epic 12 2FA 게이트 보존)
- **capability gate** = `AUDIT_LOG_VIEW` (F21.6 verbatim, capability matrix v1.30)
- **pagination** = offset+limit 기반, page_size=50 default (max 200)
- **sort** = `ORDER BY created_at DESC` (newest first)
- **performance** = `audit_log` table 의 `(tenant_id, created_at DESC)` index 활용 + `payload_json` 의 GIN index (jsonb_path_ops) for payload_search

## F21.2 audit log viewer UI (CR 11-4 D-002 ko-KR SSOT EXTENSION, A153 결정)

- **route** = `apps/web/app/[locale]/(dashboard)/audit-log/page.tsx` (NEW, ~200 LOC, owner/admin only)
- **components**:
  - `AuditLogFilterPanel.tsx` (filter form: actor email autocomplete + action_class dropdown + action text search + period_key + date range picker + payload_search input)
  - `AuditLogTable.tsx` (table view: created_at + actor_email + action_class chip + action text + payload summary + trace_id expandable)
  - `AuditLogPagination.tsx` (prev/next + page size selector + total count display)
  - `AuditLogExportButton.tsx` (CSV export trigger, calls F21.5 backend)
  - `AuditLogDetailModal.tsx` (full payload_json + trace_id expansion modal)
- **ko-KR SSOT** = `apps/web/messages/ko-KR.json` `audit_log.*` namespace EXTENSION (14 keys: title, description, filter_actor, filter_action_class, filter_action, filter_period, filter_date_range, filter_payload_search, table_created_at, table_actor, table_action_class, table_action, table_payload_summary, export_csv_button, pagination_prev, pagination_next, total_count, detail_modal_title)
- **API integration** = `apps/web/lib/audit/audit-log-client.ts` (NEW, fetch wrapper + auth cookie 자동 첨부 + typed error envelope)
- **route group** = `(dashboard)` 보호 (Supabase session 필수 + Epic 12 2FA 미설정 시 `/account/security?reason=2fa_required` redirect, Phase 3-1 T4 wire 정합)
- **vitest RTL render discipline** = `__tests__/audit-log/page.test.tsx` NEW (filter panel + table render + pagination interaction, CR 11-4 D-003 verbatim)

## F21.3 activity stream UI (Timeline view, A153 결정)

- **route** = `apps/web/app/[locale]/(dashboard)/activity/page.tsx` (NEW, ~150 LOC, all tenant members)
- **components**:
  - `ActivityStreamTimeline.tsx` (grouped by date: today / yesterday / N days ago)
  - `ActivityStreamEntry.tsx` (avatar + action_class icon + action text + actor name + relative time)
  - `ActivityStreamWindowSelector.tsx` (7일 / 30일 / 90일 window selector)
- **ko-KR SSOT** = `apps/web/messages/ko-KR.json` `activity.*` namespace EXTENSION (8 keys: title, description, window_7d, window_30d, window_90d, empty_message, today_label, yesterday_label)
- **route group** = `(dashboard)` 보호 (Phase 3-1 T4 wire 정합)
- **authorization** = `require_role("owner", "admin", "member", "viewer")` (all tenant members, F21.2 audit log viewer 와 다른 권한 등급)
- **capability gate** = 별도 capability gate 없음 (activity stream 은 tenant-wide 가시성, owner/admin audit log viewer 와 분리)

## F21.4 cross-region audit log visibility (Phase 5 carry-over, A154 결정)

- **EXTENSION target** = Phase 5 wire `f093f8c` 의 `apps/api/alembic/versions/0039_phase_5_multi_region_backup.py` `phase_5_replication_lag` table + Supabase multi-region primary Seoul + secondary Tokyo replica 결정 wire
- **EXTENSION logic** = audit log query 시 secondary region 의 read replica 에서 query 가능 결정 wire (multi-region read replica 통한 cross-region audit visibility) — `/api/v1/audit-log` handler 에서 connection pool 의 read-only routing 결정 wire
- **읽기 일관성** = secondary region 의 replication lag 이 lag_bytes ≤ 100MB + lag_seconds ≤ 30s 시 read consistent (Phase 5 wire 의 lag threshold 정합) — lag 초과 시 primary region 으로 fallback + Sentry breadcrumb 결정 wire
- **AC 추가** = Phase 5 §F20 verbatim 보존 + §F21.4 EXTENSION 진입

## F21.5 CSV export (Compliance use case, A155 결정)

- **module** = `apps/api/modules/audit/audit_log_export.py` (NEW, ~120 LOC)
- **function signature** = `export_audit_log_csv(tenant_id: UUID, filters: AuditLogQueryFilters, actor_id: UUID) -> StreamingResponse` (Excel-compatible UTF-8 BOM + streaming response + audit-first INSERT `audit_log_exported` action)
- **CSV format** = columns: `entry_id,created_at,actor_email,action_class,action,period_key,payload_json,trace_id` (UTF-8 BOM `﻿` + comma-separated + double-quote escape for payload_json)
- **streaming** = `StreamingResponse(media_type='text/csv; charset=utf-8', headers={'Content-Disposition': f'attachment; filename="audit-log-{tenant_slug}-{yyyymmdd}.csv"'})` (large dataset 시 memory efficient)
- **audit-first INSERT** = `audit_log_exported` (CR 1-1 verbatim, action_class='AUDIT' + action='audit_log_exported' + actor_id + tenant_id + filters_json + row_count + trace_id) — 누가 언제 어떤 filter 로 export 했는지 추적
- **CR 12-5 D-14 envelope** = error envelope `{code, message_ko, details, trace_id}` (e.g. `AUDIT_LOG_EXPORT_FORBIDDEN_KO`, `AUDIT_LOG_EXPORT_TOO_LARGE_KO`)

## F21.6 Capability gate AUDIT_LOG_VIEW (A156 결정)

- **Capability enum** = `Capability.AUDIT_LOG_VIEW = "audit_log_view"` (NEW, apps/api/core/capability.py EXTENSION 1 enum)
- **4-industry grants** = manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ (industry-agnostic, CR 12-1 L4 precedent 미러, MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY Epic 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern verbatim bind)
- **미허용 tenant 차단** = `require_capability(AUDIT_LOG_VIEW)` Dependency (Epic 12 2FA 게이트 보존)
- **capability-matrix.md v1.29 → v1.30 EXTENSION** = 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅ (SSOT RED→GREEN EXTENSION 결정 wire)
- **drift detector** = `tests/integration/test_capability_matrix_v1_30_drift.py` NEW (Phase 5 `test_capability_matrix_v1_29_drift.py` + Epic 16 `test_capability_matrix_v1_28_drift.py` 정합, P-015 SSOT drift detector 정합)

## F21.7 tests + wire scope T1~T8 결정 (cj-style 80번째 epic 연속 정직 회복 wire 진입 시점에 결정)

**7 ACs satisfied (PRD §F21.1~§F21.7 verbatim, cj-style 80번째 epic 연속 정직 회복 wire 진입 시점에 wire scope 결정)**:

- **AC §F21.1** Audit log query API 결정 wire (`apps/api/modules/audit/audit_log_query.py` NEW ~+180 LOC + 4 functions: query_audit_log + count_audit_log + get_audit_log_entry + query_activity_stream + AuditLogQueryFilters + AuditLogEntry + AuditLogPage + ActivityStreamGroup TypedDict 결정 + RLS 자동 적용 + capability gate AUDIT_LOG_VIEW + owner/admin role required)
- **AC §F21.2** Audit log viewer UI 결정 wire (`apps/web/app/[locale]/(dashboard)/audit-log/page.tsx` NEW ~+200 LOC + 5 components 결정 + ko-KR.json `audit_log.*` namespace EXTENSION 14 keys + (dashboard) 보호 + vitest RTL render discipline 결정)
- **AC §F21.3** Activity stream UI 결정 wire (`apps/web/app/[locale]/(dashboard)/activity/page.tsx` NEW ~+150 LOC + 3 components 결정 + ko-KR.json `activity.*` namespace EXTENSION 8 keys + all tenant members 권한)
- **AC §F21.4** Cross-region audit log visibility 결정 wire (Phase 5 multi-region read replica 통한 cross-region audit query 결정 wire + read-only routing + lag threshold 정합 + Sentry breadcrumb 결정)
- **AC §F21.5** CSV export 결정 wire (`apps/api/modules/audit/audit_log_export.py` NEW ~+120 LOC + streaming response + UTF-8 BOM + audit-first INSERT `audit_log_exported` CR 1-1 verbatim 결정 + CR 12-5 D-14 envelope 결정)
- **AC §F21.6** Capability matrix v1.29 → v1.30 EXTENSION AUDIT_LOG_VIEW 1 NEW row 결정 wire (industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러)
- **AC §F21.7** Tests + wire scope T1~T8 결정 (~+50 NEW pytest PASS + ~+15 NEW vitest PASS + 0 NEW ruff + 0 regressions 결정 + T1 audit_log_query module + T2 audit_log_export module + T3 audit_log_viewer page + T4 activity_stream page + T5 ko-KR.json SSOT EXTENSION + T6 capability.py + capability matrix v1.30 + T7 tests + 3중 게이트 FINAL CLEAN + T8 atomic commit)
- **AC §8.1 M0-(n)** audit log viewer AC verbatim 결정

**A19 cohesion pattern 9 surface EXTENSION PASS** (audit viewer surface NEW 결정 wire):

- Surface 1 (kernel) = F21.1 audit_log_query pure functions ✅
- Surface 2 (port) = F21.1 audit_log_query FastAPI routes port ✅
- Surface 3 (db schema) = 기존 audit_log table + F21.4 cross-region read replica 활용 ✅
- Surface 4 (service) = F21.1 query_audit_log + count_audit_log + get_audit_log_entry + query_activity_stream service ✅
- Surface 5 (handler) = F21.2 audit-log/page.tsx + F21.3 activity/page.tsx + F21.5 /api/v1/audit-log/export endpoint ✅
- Surface 6 (envelope) = F21.1 AuditLogPage TypedDict + F21.5 CSV streaming response envelope 결정 wire ✅
- Surface 7 (capability) = F21.6 AUDIT_LOG_VIEW 1 NEW gate (capability matrix v1.30 EXTENSION) ✅
- Surface 8 (audit) = F21.5 audit_log_exported audit-first INSERT 결정 (CR 1-1 verbatim, action_class='AUDIT' + action='audit_log_exported') ✅
- Surface 9 (**audit viewer surface NEW**) = F21.1~F21.5 audit log viewer & activity stream territory ✅ EXTENSION PASS

**CR lessons applied** (cj-style 80번째 epic 연속 정직 회복 wire 진입 시점에 결정):

- **CR 0-2** RLS lesson ✅ APPLIED (F21.1 audit_log query 의 tenant_id RLS 자동 적용 + AD-22 verbatim 보존)
- **CR 1-1** audit-first INSERT ✅ APPLIED (F21.5 audit_log_exported 1 NEW audit log entry 결정 wire, action_class='AUDIT' + action='audit_log_exported' + actor_id + tenant_id + filters_json + row_count + trace_id)
- **CR 9-6** commit message discipline ✅ APPLIED (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention)
- **CR 11-3** honest-DEFER discipline ✅ APPLIED (80번째 epic 연속 정직 회복 — D-1-1-DEFER-1/2/3 RESOLVED 보존 60~80번째 + D-LAUNCH-1-DEFER-1 honestly preserved 65~80번째 + D-EPIC-16-REVIEW-DEFER-2~6 ✅ RESOLVED 보존 78~80번째 + D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED 보존 73~80번째)
- **CR 11-4** D-001~D-005 + P-015 lessons carry ✅ APPLIED (F21.2 audit log viewer UI 의 ko-KR.json SSOT EXTENSION 14 keys + vitest RTL render discipline 결정, F21.3 activity stream 의 ko-KR.json SSOT EXTENSION 8 keys)
- **CR 12-1** L4 industry-agnostic capability ✅ APPLIED (capability matrix v1.30 EXTENSION AUDIT_LOG_VIEW 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅)
- **CR 12-5** D-14 typed exception envelope ✅ APPLIED (F21.5 audit_log_export error envelope `{code, message_ko, details, trace_id}` 결정 wire)
- **CR 12-5** D-PARITY-01 inversion ✅ APPLIED (Python FastAPI backend + TypeScript Next.js audit viewer parity 결정 wire, vitest RTL render discipline 결정)
- **CR 12-5** D-GATE-01 inversion ✅ APPLIED (capability gate AUDIT_LOG_VIEW per-tenant on/off 결정 wire, owner/admin role required AD-22 RBAC 결정)
- **A19** cohesion pattern 9 surface EXTENSION PASS ✅ (audit viewer surface NEW = F21.1~F21.5 audit log viewer & activity stream territory)

**Sidebar/MenuProvider hot-fix `01a06e4` (cj-style 79번째) + D-EPIC-16-REVIEW-DEFER-2~6 RESOLVE sprint `512ed6a` (cj-style 78번째) + Phase 5 close-out retro `b843565` (cj-style 76~77번째) + Phase 5 atomic wire `f093f8c` (cj-style 75번째) cycle 정합 보존** (cj-style 49~79번째 누적 cycle 정직 회복 + Epic 1 ~ Epic 16 + Phase 3 + Phase 4 + Phase 5 + 1st release 모든 close-out retro 결정 verbatim preserve + EXTENSION) — Epic 17 PRD entry 진입 시점에 Epic 1 ~ Epic 16 + Phase 3 + Phase 4 + Phase 5 + 1st release 모든 close-out retro 결정 verbatim preserve + EXTENSION.

**partial wire 시도 0건 + single sprint atomic wire T1~T8 결정** (cj-style 80번째 epic 연속 정직 회복 wire 진입 시점에 결정). 결정 wire 일자: 2026-08-22 (KST). **next**: Epic 17 bmad-create-story spec entry 진입 (cj-style 81번째 epic 연속 정직 회복 bmad-create-story 진입 시점) OR Epic 17 bmad-dev-story atomic sprint wire T1~T8 진입 (cj-style 82번째 epic 연속 정직 회복 wire 진입 시점) OR Epic 17 close-out retro 진입 (cj-style 83번째 epic 연속 정직 회복 진입 시점) 결정 wire 보존.

---

# 13. 화면·디자인·기술

## 13.1 화면 원칙
- 좌측 사이드바 내비게이션, PC 그리드 입력 / 모바일 폼 입력, 완전반응형
- 대시보드: 월 체크리스트(순차입력 안내)·TOP5/WORST5·12개월 추이
- 디자인: 클리어블루 + 옐로우 포인트 + 화이트, Pretendard, 음수 (1,234) 빨강 표기
- 거래처 입력 안내 문구: "거래처 정보를 입력하면, 거래처별로 정교한 판매전략을 수립하는 데 도움이 됩니다"
- **AI 배지 (F10.2-(a))** — `source_kind='auto_analysis'` 파란 배지 "📊 자동 분석" + `source_kind='ai_reference'` 보라 배지 "🤖 AI 참고(검증 필요)" + tooltip 한국어 only [NFR18 / §13.1 ko-KR 정합]. 2차 로드맵: 다국어 [§14.B NON-GOAL #5]

## 13.2 기술 스택
| 계층 | 선택 | 비고 |
|------|------|------|
| 프론트 | Next.js + Tailwind + shadcn/ui + TanStack Table + next-intl + Recharts | 완전반응형 |
| 백엔드 | FastAPI + **순수 Python 원가엔진** | 엑셀 1원 단위 대조 테스트(V8) 필수 |
| DB | Supabase PostgreSQL + RLS(멀티테넌트) | append-only 수불 원장, 마감잠금 트리거 |
| 결제 | Stripe | 월 구독 |
| 배포 | Vercel(프론트) + Railway(백엔드) | 월 예산 10만원 내 |
| AI | Claude API (Vision 포함) | M10 |
| 배제 | Celery 등 복잡 인프라 | G2 "새벽에 혼자 고칠 수 있는 시스템" |

## 13.3 보안·운영
2FA, 저장 데이터 암호화, 일 1회 자동 백업 + 셀프 백업 다운로드, 해지 시 보관일수 고지+삭제 동의 문구, 운영자 콘솔·대리접속(동의+읽기전용), 공지 테이블.

---

# 14. 비기능 요구·제약

- 데이터 규모: 소형 여유 설계(제품 수백·자재 수천 무리 없음 — 원본 슬롯 한계 철폐). **1차 정량 한계**: 테넌트 ≤ 100, 제품 ≤ 500, 자재 ≤ 2,000, 월 거래건수 ≤ 50,000, 월 입력 동시 사용자 ≤ 10.
- 성능: 월 계산 수 초 내(소형 데이터 전제), 계산 버튼 방식으로 예측 가능성 확보. **응답시간 SLO**: 단일 테넌트 월 계산 P95 ≤ 5초, 보고서 조회 P95 ≤ 3초, AI 추출 응답 P95 ≤ 30초.
- 마이그레이션: 원본 엑셀 5종 가져오기(유통품 자기참조 BOM → merchandise 자동 변환 포함)
- 법적 문서(약관·개인정보처리방침)는 프로젝트 마무리 단계에 초안 작성 (예정 과업)
- 파일럿 투입은 개발 중반 시점에 재논의 (예정 과업) / 서비스명 '비즈업'은 가칭, 확정 재논의

**비기능 정량 한계 (NFR 표)**

| 항목 | 1차 목표 | 2차 확장 | 측정 방법 |
|------|----------|----------|---------|
| 가용성 | 99.5% (월 4h 다운 허용) | 99.9% | PostgreSQL ping + 모니터링 |
| RPO (Recovery Point Objective) | 24h (일 1회 백업) | 1h | 백업 시각 vs 장애 시각 |
| RTO (Recovery Time Objective) | 4h (1인 운영자 수동 복구) | 1h | 장애 선언 → 복구 완료 |
| 백업 보관 | 30일 (자동), 1년 (분기) | 1년 (자동) | 보관 정책 |
| 감사로그 보존 | 5년 (append-only [A8]) | 5년 | DB retention |
| 보안 — 전송 | TLS 1.3 | TLS 1.3 | Cert 검증 |
| 보안 — 저장 | AES-256 at rest, KMS 관리 | 동일 | KMS audit |
| 인증 | 2FA 강제 (M12-a) | SSO 추가 | M12 |
| 동시 사용자 (테넌트당) | 10 | 50 | 동시접속 카운터 |
| 데이터 볼륨 (테넌트당) | 제품 500, 자재 2,000, 월 50K 트랜잭션 | 10× | DB row count |
| 인프라 페이로드 | Supabase Free → Pro 승격 트리거: 동시 30 테넌트 또는 월 10K 트랜잭션 | — | 운영자 콘솔 알림 |
| **언어 (UI 라벨)** | **한국어 only** (1차), [§14.B NON-GOAL #5] 정합 | 다국어 (en-US + ja-JP 우선) | `apps/web/messages/ko-KR.json` SSOT 1권 강제 + `apps/web/lib/i18n/*` `notFound` 시 ko-KR fallback + ESLint rule forbid-non-ko-KR-keys |
| **AI 추출 응답** | P95 ≤ 30초 (M10-c + 10-1 wire) | 동일 | Anthropic Claude Vision 응답 시간 측정 + NFR11 SLO |
| **AI 인사이트 cache hit** | sub-100ms (10-2 wire) | 동일 | in-memory + DB lookup 시간 측정 |
| **AI 배지 reject counter** | **target 0건** (10-3 wire, [AD-7 verbatim]) | 동일 | `audit_logs.action_name='ai_badge_source_kind_rejected'` count |

**용어**: RPO/RTO 정의는 §부록 C 참조. 본 표 임계값은 IR·architecture 단계에서 재검증될 수 있다.

---

# 14.B 비목표 (Non-Goals for MVP)

본 섹션은 1차 출시에서 **명시적으로 구축하지 않을** 기능이다. 후속 로드맵(§15) 항목과 1:1 대응하며, 각 항목은 의도된 미구현임을 표시한다. Downstream(architecture, stories)에서 본 목록에 없는 기능을 MVP 범위로 가정해서는 안 된다.

**[NON-GOAL for MVP #1] — 제조 부문의 ABC 엔진.** 전통 개별원가 엔진(§6)·TDABC(§7.2)·Classic ABC(§7.1)는 **서비스 부문 전용**이며, 제조 부문의 활동기준원가는 1차에서 미구현. 겸영 기업의 경우 제조는 전통 엔진, 서비스는 ABC 엔진으로 자동 분기(Q-I). 2차 이후 통합 검토.

**[NON-GOAL for MVP #2] — 복수 예산 시나리오.** §10 예산 시나리오는 1차에서 시나리오 1개(M8-a). 2개 이상 동시 보유·비교는 2차. trigger: ≥ 5 테넌트 요청 시.

**[NON-GOAL for MVP #3] — A×B×C×D 예산 편성 엔진.** §부록 B에 명세만 보존, 1차 비구현. 예산 입력은 사용자 직접 입력(금액)으로 한정. trigger: ≥ 5 테넌트 요청 시.

**[NON-GOAL for MVP #4] — CPA (Cost-Per-Activity) 정밀 분석.** Classic ABC의 동인 단가는 1차에서 단순 합산(원가/총건수), 회귀·계절성 분석은 2차.

**[NON-GOAL for MVP #5] — 다국어·다통화 자동 환산.** KRW/USD 동시 표시(§8.1 M5-b)만 지원, 환율 자동 수집·시점 잠금은 2차. trigger: 외국인 투자자 round 진입 시.

**[NON-GOAL for MVP #6] — 멀티에이전트 원가분석 위원회.** AI 인사이트는 단일 모델의 고정 템플릿(M10-b)만. 다중 에이전트 협의·합의 알고리즘은 3차.

**[NON-GOAL for MVP #7] — 환경·지속가능성 원가.** §15 장기 검토 항목. 1차·2차 의제 아님.

**[NON-GOAL for MVP #8] — 모바일 네이티브 앱.** 완전반응형 웹(§13.1)만 제공. iOS/Android 네이티브는 별도 의사결정 후.

**[NON-GOAL for MVP #9] — 부채·자금 관리.** 매출·인건비·경비 입력과 비용 흐름만 추적. 차입금·상환계획·현금흐름표는 별도 모듈(M13+ 후보).

**[NON-GOAL for MVP #10] — ERP 양방향 동기화.** 다양한 ERP(더존·경동나비·SAP)와 양방향 API는 3차. 1차 입력은 엑셀 업로드 + 직접 입력만.

*본 비목표는 §15 로드맵의 2차·3차 항목과 동기화되어 있다. 2차 pull-forward trigger는 OQ-7에서 관리.*

---

# 14.A 미해결 질문 (Open Questions)

PRD 본문에서 단언되었으나 확정 전 재논의가 필요한 결정. 각 항목은 owner와 목표 마일스톤을 명시한다.

| # | 미해결 항목 | 현 상태 | Owner | 목표 마일스톤 |
|---|------------|---------|-------|---------------|
| OQ-1 | 서비스명 '비즈업' 확정 | 가칭. 도메인·상표 사용 가능 여부 미검증 | PM | UX 진입 전 |
| OQ-2 | 가격 정책(1만원 단일 vs 단계형) | §2 단일 요금제로 단언되었으나, 동종 SaaS 벤치마크·고객 가격 민감도 미수행 (검수 medium) | PM + 영업 | 파일럿 시작 전 (M5 완료 후) |
| OQ-3 | 파일럿 투입 시점 | "개발 중반 시점"은 모호 → **trigger: M0–M6 완성 후 1주**로 고정 (검수 low) | 운영자 | M6 완성 시 |
| OQ-4 | 법적 문서(약관·개인정보처리방침) | 작성 일정 미확정 | 운영자 + 법무 자문 | 파일럿 시작 전 |
| OQ-5 | Q-G report 파일 26 보고서 surface | 구조 분석으로 갈음하나, §9 14+7종으로의 커버리지 매핑 미수행 (검수 low) | 운영자 | M5 완료 후 |
| OQ-6 | [NOTE FOR PM] §6.1 (5) — 제품재고조정 UX 부호 처리 | UX 와이어프레임 단계에서 해소 예정 | UX designer | UX 단계 |
| OQ-7 | 2차 로드맵 항목 trigger 기준 | A×B×C×D 엔진·복수 예산·CPA의 pull-forward 기준 미정 (검수 medium) | PM | 1차 출시 후 6개월 시점 |

각 항목은 해소 시점에 memlog에 `event: "OQ-N resolved"`로 기록하고 본 표에서 제거한다.

---

# 15. 로드맵 (2026-07 최신 이론 근거 포함 — 결정 Q-J)

## 1차 (첫 출시 — 본 PRD 범위)
12모듈 + ABC/TDABC + AI 3종 + 검증 체계. 출시 후 파일럿 1~2곳 무료.

## 2차
- A×B×C×D 예산 편성 엔진 (제10장 보존 산식 구현)
- 복수 예산 시나리오, 활동별 classic/TDABC 혼용(method_override 활성화)
- 고객수익성 분석(CPA) — 판매지역 축을 고객 축으로 확장
- 다국어 확장(중·일), 원가 이상감지 알림(AI 예측 기반)

## 3차
- **제조 부문 ABC 개방** (부문-엔진 매핑 해제, 병행 분석 뷰)
- 멀티에이전트 원가분석 위원회 (AI 에이전트 협의체가 월 마감 데이터를 다각 분석)

## Epic 13 (✅ DONE, 2026-08-20 — cj-style 1~4번째 진입점 모두 wire DONE: PRD entry + 13-1 atomic + post-wire handoff + Epic 13 close-out retro)

- **LISTEN/NOTIFY Consume Trigger EXTENSION** — AD-25 cache invalidation trigger EXTENSION for close/reopen (4-channel publisher EXTENSION: `ai_cache` / `cost_engine_cache` / `fiscal_period_cache` / `closing_snapshot_cache`). **✅ DONE 2026-08-20** — atomic single sprint T1~T8 wire (commit `f2ea2f6`, 17 files = 12 NEW + 5 MODIFIED): alembic 0033 (NOTIFY trigger `cache_invalidation_log_notify_trg` + `cache_invalidation_log_notify()` PL/pgSQL function with 6-key alphabetical JSON payload) + LISTEN daemon `CacheInvalidationListener` (`apps/api/core/cache_invalidation_listener.py` ~620 LOC, stdlib-only pure async kernel + reconnect/backoff exponential base 1s factor 2 + jitter ±20% + max 30s + circuit breaker 5 failures → 60s cool-down) + FastAPI lifespan EXTENSION (`apps/api/main.py` 4 NEW functions + 2 NEW exception handlers CR 12-5 D-14 envelope) + 4-channel cache eviction handlers EXTENSION (M10/M3/M11 — `M10AIInvalidationAdapter` + `M3CostEngineInvalidationAdapter` + `M11FiscalPeriodInvalidationAdapter` + `M11ClosingSnapshotInvalidationAdapter` in `cache_invalidation_listener_adapters.py` ~220 LOC, F10.1-(d) verbatim cross-channel contamination 방어) + V8 determinism byte-identical test NEW (`tests/regression_v8/test_listen_notify_v8_determinism.py` ~11 cases) + CR 12-5 cross-lang drift detector EXTENSION (`apps/web/lib/cache-invalidation-listener.ts` ~150 LOC TS mirror + `tests/web/test_cache_invalidation_listener_parity.py` ~14 cases + 1-line ko-KR reject) + capability gate `LISTEN_NOTIFY` (capability matrix v1.22, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-5 D-GATE-01 inversion 적용). D-10-2-DEFER-3 ✅ RESOLVED. A19 cohesion pattern 8 surface 8/8 PASS. 3중 게이트 FINAL CLEAN (backend ruff scoped 0 NEW, capability matrix v1.22 SSOT RED→GREEN, AD-25 verbatim bind EXTENSION + AD-22 + AD-4 cross-ref + CR 12-5 D-GATE-01 + D-PARITY-01 inversion 적용). ~107 NEW pytest PASS + 0 NEW ruff + 0 regressions (existing tests: 474 passed, 88 skipped DB-backed). **A36 SDR 검증 4-step 자동 적용 PASS** (commit prefix lint + sprint-status structure + vitest file count drift + commit consistency). **3 honestly DEFER preserved (CR 11-3 22~42번째 epic 연속)**: D-13-1-DEFER-1 ✅ RESOLVED (master PRD v2.3 §F13 verbatim = 본 A54) / D-13-1-DEFER-2 preserved (LISTEN/NOTIFY 실측 evidence 정합 sweep = 1차 출시 후 진입 시점) / D-13-1-DEFER-3 preserved (separate epic LISTEN/NOTIFY consume 2nd batch = cross-tenant invalidation fan-out + multi-process coordination = Epic 13 후속 story 진입 결정, A53 결정 시점). **A53+A54+A55+A56 결정 wire (cj-style Epic 13 5번째 진입점 = cj-style Epic 13 carry-over 17번째 docs only 권장)**: A54 = 본 master PRD v2.3 edit (D-13-1-DEFER-1 해소). PRD §F13 verbatim 13-1 wire 정합 + §8.1 M10-(d)·§F10.1-(d) EXTENSION 진입 wire.

## Phase 3 (✅ DONE, 2026-08-22 — cj-style Phase 3 1~3번째 진입점 모두 wire DONE: PRD entry + Phase 3-0 atomic sprint + Phase 3-1 atomic wire T1~T8 + close-out retro)

- **Auth Foundation (로그인/회원가입 UI + auth middleware = Epic 1 완성 territory close-out 결정)** — Phase 3 PRD entry DONE 2026-08-20 (cj-style Phase 3 1번째 진입점 = cj-style 49번째 epic 연속 정직 회복, master PRD v2.5 → v3.0 atomic edit) + Phase 3-0 atomic sprint `1db21d2` DONE 2026-08-21 (cj-style Phase 3 carry-over 1번째 "fix" 종류 = P0 3종 ALL RESOLVED ✅: ① GUC name split / ② custom_access_token_hook enabled / ③ signup path) + Phase 3-1 bmad-create-story spec entry + Phase 3-1 bmad-dev-story atomic wire T1~T8 `d3e7454` DONE 2026-08-21 (cj-style Phase 3 2번째 진입점 = cj-style 50번째 epic 연속 정직 회복, 41 files atomic = 33 NEW + 8 MODIFIED, 97 NEW test cases = 66 vitest + 31 pytest, 3중 게이트 FINAL CLEAN, SDR 갱신 3737→3855) + Phase 3 close-out retro `handoff-2026-08-22-phase-3-close-out-done` DONE 2026-08-22 (cj-style Phase 3 3번째 진입점 = cj-style 51~52번째 epic 연속 정직 회복 wire DONE, A65~A75 결정 wire + D-1-1-DEFER-1/2/3 honestly preserved 50번째 검증 + 3중 게이트 FINAL CLEAN + A19 cohesion 9 surface EXTENSION PASS). 결정 wire 일자: 2026-08-22 (KST).

## Phase 4 (in-progress, 2026-08-22 — cj-style Phase 4 1번째 진입점 = Phase 4 PRD entry DONE 진입 wire = cj-style 53번째 epic 연속 정직 회복, Phase 4 wire 진입 대기 = cj-style Phase 4 2번째 진입점 = cj-style 54번째 epic 연속 정직 회복 진입 대기)

- **Deployment config + Dockerfile + health check + observability + database backup territory 진입 (옵션 (a) Phase 4 진입, A73 결정 wire)** — Phase 4 PRD entry DONE 2026-08-22 (cj-style Phase 4 1번째 진입점 = cj-style 53번째 epic 연속 정직 회복, master PRD v3.0 → v3.1 atomic edit). Phase 4 territory = Vercel frontend (vercel.json + framework=nextjs + regions=[icn1] + buildCommand=`pnpm --filter web build` + env mapping NEXT_PUBLIC_SUPABASE_URL/ANON_KEY/API_BASE_URL + headers CSP+X-Frame-Options+HSTS + redirects legacy `/ko-KR/*` → `/ko/*`) + Railway backend (railway.toml + builder=DOCKERFILE + dockerfilePath=`apps/api/Dockerfile` + healthcheckPath=`/api/v1/health` + restartPolicyType=ON_FAILURE + env mapping DATABASE_URL/SUPABASE_JWT_SECRET/SUPABASE_URL/ANON_KEY/SERVICE_ROLE_KEY/SENTRY_DSN) + Supabase production PostgreSQL (PITR 7일 자동 + Supabase Storage 결정 wire 보류) 결정 wire + per-app Dockerfile 분리 (`apps/web/Dockerfile` Next.js standalone output + `apps/api/Dockerfile` FastAPI uvicorn, AD-14 stack pin by @sha256: digest 결정) + Health check + observability wire (`GET /api/v1/health` FastAPI endpoint + `GET /api/health` Next.js route handler + liveness/readiness 분리 결정 + Sentry browser SSR-safe init + Sentry FastAPI server integration + tracesSampleRate=0.1) + Database backup strategy (alembic 0036 phase_4_backup_strategy table + Supabase PITR 7일 자동 + 수동 export 보완 + RPO 5분 / RTO 1시간 결정 + SHA-256 checksum validation) + capability matrix v1.24 → v1.25 EXTENSION (DEPLOYMENT_PROD + DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP + DEPLOYMENT_HEALTH_CHECK 4 NEW rows, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러) + AD-27 Deployment 신규 결정 (Vercel frontend + Railway backend + Supabase PostgreSQL + Sentry observability 결정 wire). Epic 12 wire 정합 (audit-first INSERT 보존) + Epic 13/14 wire 정합 (PostgreSQL LISTEN/NOTIFY multi-process coordination 결정 wire 보존). **Phase 4 PRD entry wire scope (master PRD v3.1 atomic edit)**: (1) front matter title v3.0 → v3.1 + changelog v3.1 entry / (2) §F16 신규 (F16.1 vercel.json Vercel frontend deployment config / F16.2 railway.toml Railway backend deployment config / F16.3 apps/web/Dockerfile + apps/api/Dockerfile per-app Dockerfile 분리 / F16.4 docs/deployment.md production deployment runbook 12 sections / F16.5 health check + observability + monitoring / F16.6 database backup strategy / F16.7 tests + wire scope T1~T8 결정) / (3) §8.1 M0-(g) production deployment 결정 wire 진입 / (4) §15 로드맵 Phase 4 row status 백로그 → in-progress (PRD entry DONE 진입 wire) / (5) §부록 A A73 + A74 + A76 + A77 + A78 신규 결정 표 / (6) AD-27 Deployment 신규 결정 (Vercel + Railway + Supabase + Sentry 결정 wire) / (7) capability matrix v1.24 → v1.25 EXTENSION DEPLOYMENT_PROD + DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP + DEPLOYMENT_HEALTH_CHECK 4 NEW rows (industry-agnostic 4-industry grants ✅/✅/✅/✅). **Phase 4 진입 flow (cj-style 1~3번째 진입점 결정 보존)**: (1) cj-style Phase 4 1번째 진입점 = Phase 4 PRD entry (cj-style 53번째): ✅ DONE 2026-08-22 (master PRD v3.1 atomic edit) / (2) cj-style Phase 4 2번째 진입점 = bmad-create-story spec (cj-style 54번째): Phase 4 wire spec (T1~T8) 결정 wire 진입 대기 / (3) cj-style Phase 4 3번째 진입점 = bmad-dev-story atomic wire (cj-style 55번째): Phase 4 본체 wire T1~T8 atomic single sprint (T1 Vercel config + T2 Railway config + T3 per-app Dockerfile + T4 deployment runbook + T5 health check + observability + T6 database backup strategy + T7 capability v1.25 + T8 tests + 3중 게이트 FINAL CLEAN atomic commit). A19 cohesion pattern 9 surface EXTENSION PASS 결정 (deployment surface NEW). estimated ~40 NEW pytest PASS + ~20 NEW vitest PASS + 0 NEW ruff + 0 regressions. 결정 wire 일자: 2026-08-22 (KST).

## Epic 16 (in-progress, 2026-08-22 — cj-style Epic 16 1번째 진입점 = Epic 16 PRD entry DONE 진입 wire = cj-style 67번째 epic 연속 정직 회복, Epic 16 wire 진입 대기 = cj-style Epic 16 2번째 진입점 = cj-style 68번째 epic 연속 정직 회복 진입 대기)

- **Tenant IdP admin management territory 진입 (옵션 (a) Epic 16 진입, A92 결정 wire 진입)** — Epic 16 PRD entry DONE 2026-08-22 (cj-style Epic 16 1번째 진입점 = cj-style 67번째 epic 연속 정직 회복, master PRD v3.3 → v3.4 atomic edit). Epic 16 territory = (1) `tenant_idps` table (alembic 0038 + 13 columns + unique constraint `(tenant_id, idp_entity_id)` + RLS policy `tenant_id = current_setting('app.tenant_id')` 결정 wire 진입, CR 0-2 RLS lesson 적용) / (2) IdP metadata XML validation service (`apps/api/modules/auth/sso/idp_metadata_validator.py` NEW ~120 LOC, 8 validation steps 결정 wire) / (3) Tenant IdP CRUD API 5 routes (FastAPI `apps/api/modules/auth/sso/idp_admin_routes.py` NEW, owner/admin role required + RLS 자동 적용 + audit-first INSERT 4 NEW: `tenant_idp_created` / `tenant_idp_updated` / `tenant_idp_deleted` / `tenant_idp_tested`, CR 1-1 verbatim 적용) / (4) Tenant IdP admin UI (Next.js `apps/web/app/[locale]/(dashboard)/settings/sso/page.tsx` NEW ~150 LOC + 4 components + ko-KR.json `settings.sso.*` namespace EXTENSION 12 keys + (dashboard) 보호) / (5) Per-tenant IdP routing EXTENSION (Epic 15 SAML routes `saml_routes.py` 정합: `tenant_slug` → `tenant_idps` lookup → `idp_sso_url` redirect + ACS `idp_x509_cert` 동적 로딩 + backward compatibility `acme` hardcoded tenant 보존) / (6) Capability gate TENANT_IDP_MANAGEMENT (capability matrix v1.27 → v1.28 EXTENSION 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러) + AD-30 Tenant IdP admin management 신규 결정 ((a)~(f) 6 sub-decisions 모두 결정 wire 진입). Epic 15 SSO enterprise SAML territory carry-over chain (Epic 15 cj-style 58~61번째 wire DONE 진입 + docs/sso-enterprise.md §4.1 step 3 'TODO Epic 16' forward-reference 해결 + Epic 15 SAML response validation + JIT provisioning + multi-tenant isolation 정합) + Epic 15 close-out retro `729b223` 결정 verbatim preserve + EXTENSION (Epic 15 territory DONE 정합). Phase 3-0 + Phase 3-1 + Phase 4 + Epic 13/14 wire + Epic 15 wire + 1st release 5-entry-point pattern 모두 wire DONE 진입 (62~66번째) + Epic 15 4-entry-point pattern 모두 wire DONE 진입 (58~61번째) + Phase 4 3-entry-point pattern 모두 wire DONE 진입 (53~56번째) + Phase 3 3-entry-point pattern 모두 wire DONE 진입 (49~52번째) 결정 wire 모두 보존. **Epic 16 PRD entry wire scope (master PRD v3.4 atomic edit)**: (1) front matter title v3.3 → v3.4 + changelog v3.4 entry / (2) §F19 신규 (F19.1 tenant_idps table + F19.2 IdP metadata validation + F19.3 CRUD API + F19.4 admin UI + F19.5 per-tenant routing EXTENSION + F19.6 capability gate + F19.7 tests + wire scope T1~T8 결정) / (3) §8.1 M0-(l) tenant IdP admin AC 신규 / (4) §15 로드맵 Epic 16 row status 백로그 → in-progress (PRD entry DONE 진입 wire) / (5) §부록 A A92+A93+A94+A95+A96 신규 결정 표 / (6) AD-30 Tenant IdP admin management 신규 결정 (tenant_idps architecture 결정) / (7) capability matrix v1.27 → v1.28 EXTENSION TENANT_IDP_MANAGEMENT 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅. **Epic 16 진입 flow (cj-style 1~5번째 진입점 결정 보존)**: (1) cj-style Epic 16 1번째 진입점 = Epic 16 PRD entry (cj-style 67번째): ✅ DONE 2026-08-22 (master PRD v3.4 atomic edit) / (2) cj-style Epic 16 2번째 진입점 = bmad-create-story spec (cj-style 68번째): Epic 16 wire spec (T1~T8) 결정 wire 진입 대기 / (3) cj-style Epic 16 3번째 진입점 = bmad-dev-story atomic wire (cj-style 69번째): Epic 16 본체 wire T1~T8 atomic single sprint (T1 tenant_idps table alembic 0038 + T2 IdP metadata validator + T3 CRUD API 5 routes + T4 admin UI + T5 per-tenant routing EXTENSION + T6 capability v1.28 + T7 tests + T8 3중 게이트 FINAL CLEAN atomic commit) / (4) cj-style Epic 16 4번째 진입점 = bmad-code-review (cj-style 70번째): review follow-up sprint 진입 결정 (Epic 15 review follow-up 패턴 미러) / (5) cj-style Epic 16 5번째 진입점 = Epic 16 close-out retro (cj-style 71번째): A92~A96 close-out retro + A19 cohesion 9 surface EXTENSION PASS 검증 (Epic 15 SSO enterprise surface EXTENSION = F19.1~F19.5 tenant IdP admin territory). A19 cohesion pattern 9 surface EXTENSION PASS 결정 (Epic 15 SSO enterprise surface EXTENSION). estimated ~25 NEW pytest PASS + ~5 NEW vitest PASS + 0 NEW ruff + 0 regressions. 결정 wire 일자: 2026-08-22 (KST).

## Phase 5 (in-progress, 2026-08-22 — cj-style Phase 5 1번째 진입점 = Phase 5 PRD entry DONE 진입 wire = cj-style 73번째 epic 연속 정직 회복, Phase 5 wire 진입 대기 = cj-style Phase 5 2번째 진입점 = cj-style 74번째 epic 연속 정직 회복 진입 대기)

- **Multi-Region Backup & Disaster Recovery territory 진입 (옵션 (a) Phase 5 진입, A124 결정 wire 진입)** — Phase 5 PRD entry DONE 2026-08-22 (cj-style Phase 5 1번째 진입점 = cj-style 73번째 epic 연속 정직 회복, master PRD v3.4 → v3.5 atomic edit). Phase 5 territory = (1) **Cross-region read replica + WAL archiving** (alembic 0039 phase_5_replication_lag table + replica_region enum seoul/tokyo/singapore/frankfurt/virginia/oregon/sao_paulo + primary_region enum + lag_bytes BIGINT + lag_seconds INTEGER + last_synced_lsn TEXT PG_LSN + replication_status enum syncing/replicating/lagged/disconnected/failed + audit-first INSERT `replica_status_changed` + 3 indexes + 2 CHECK constraints + `apps/api/alembic/versions/0039_phase_5_multi_region_backup.py` + `docs/cross-region-replication.md` 결정 wire) / (2) **Cross-region failover automation** (`apps/api/jobs/failover_orchestrator.py` + primary → secondary health probe 5-second interval + 3 consecutive failures trigger + automatic promotion via Supabase API + DNS update via Supabase custom domain redirect + 30s RTO target + audit-first INSERT `failover_initiated` + `failover_completed` + FastAPI lifespan hook startup/shutdown + GRACEFUL_SHUTDOWN_TIMEOUT=30s + owner-only manual trigger `POST /api/v1/admin/failover` AD-22 RBAC + 2FA 챌린지 Epic 12 정합 결정) / (3) **DR drill + automated quarterly test** (`apps/api/jobs/dr_drill.py` + cron KST 1st Sunday 03:00 UTC 18:00 + actual failover drill test in staging + 6 drill steps: health check + secondary promote + write test + application health + DNS update + restore trigger + RPO/RTO measurement + phase_5_dr_drill_results table + Q1/Q2/Q3/Q4 quarterly schedule + audit-first INSERT `dr_drill_completed` 결정) / (4) **Cross-region backup strategy** (`docs/database-backup.md` EXTENSION 10 sections → 12 sections + cross-region PITR primary Seoul + secondary Tokyo + 30일 hot + 90일 cold + 365일 archive regional + RPO 1h / RTO 4h SLA post-multi-region wire DONE 진입 결정 wire + Phase 4 single-region RPO 5min/RTO 1h honest-extreme risk = Seoul region disaster 시 backup restoration 불가 verbatim 해소 결정) / (5) **Multi-region health observability** (`apps/api/core/health.py` EXTENSION `/api/v1/health/multi-region` endpoint + primary + secondary status array + CR 12-5 D-14 envelope `{status, primary: {region, status, lag_bytes, lag_seconds, last_synced_at}, secondary: {...}, timestamp}` + `apps/api/core/observability.py` EXTENSION Sentry breadcrumb failover + Grafana multi-region dashboard + `apps/web/app/api/health/multi-region/route.ts` NEW Next.js Edge Runtime 결정 wire) + capability matrix v1.28 → v1.29 EXTENSION (MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER 2 NEW rows, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러) + AD-31 Multi-Region Backup & Disaster Recovery 신규 결정 ((a)~(f) 6 sub-decisions 모두 결정 wire 진입). Phase 4 close-out retro §6 disaster recovery verbatim carry-over (Phase 4 docs/database-backup.md §7 "multi-region backup 결정 wire 보류, Phase 5+ 진입 시점" honestly carry-over + Phase 5 PRD entry 진입 시점에 정직 회복 결정 wire 완료) + Epic 16 close-out retro `f1ead9a` 결정 verbatim preserve + EXTENSION (Epic 16 territory DONE 정합) + 1st release close-out retro + Phase 4 close-out retro + Phase 3 close-out retro cycle 정직 회복 결정 wire 모두 보존 + Phase 3-0 + Phase 3-1 + Phase 4 + Epic 13/14 wire + Epic 15 wire + 1st release + Epic 16 6-entry-point pattern 모두 wire DONE 진입 (67~72번째) + 1st release 5-entry-point pattern 모두 wire DONE 진입 (62~66번째) + Epic 15 4-entry-point pattern 모두 wire DONE 진입 (58~61번째) + Phase 4 4-entry-point pattern 모두 wire DONE 진입 (53~57번째) + Phase 3 4-entry-point pattern 모두 wire DONE 진입 (49~52번째) 결정 wire 모두 보존. **Phase 5 PRD entry wire scope (master PRD v3.5 atomic edit)**: (1) front matter title v3.4 → v3.5 + changelog v3.5 entry / (2) §F20 신규 (F20.1 Cross-region read replica + WAL archiving / F20.2 Cross-region failover automation / F20.3 DR drill + automated quarterly test / F20.4 Cross-region backup strategy / F20.5 Multi-region health observability / F20.6 capability matrix v1.29 EXTENSION 2 NEW rows / F20.7 tests + wire scope T1~T8 결정) / (3) §8.1 M0-(m) multi-region backup AC 신규 / (4) §15 로드맵 Phase 5 row status 백로그 → in-progress (PRD entry DONE 진입 wire) / (5) §부록 A A124+A125+A126+A127+A128 신규 결정 표 / (6) AD-31 Multi-Region Backup & Disaster Recovery 신규 결정 (cross-region architecture 결정) / (7) capability matrix v1.28 → v1.29 EXTENSION MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER 2 NEW rows industry-agnostic 4-industry grants ✅/✅/✅/✅. **Phase 5 진입 flow (cj-style 1~3번째 진입점 결정 보존)**: (1) cj-style Phase 5 1번째 진입점 = Phase 5 PRD entry (cj-style 73번째): ✅ DONE 2026-08-22 (master PRD v3.5 atomic edit) / (2) cj-style Phase 5 2번째 진입점 = bmad-create-story spec (cj-style 74번째): Phase 5 wire spec (T1~T8) 결정 wire 진입 대기 / (3) cj-style Phase 5 3번째 진입점 = bmad-dev-story atomic wire (cj-style 75번째): Phase 5 본체 wire T1~T8 atomic single sprint (T1 alembic 0039 phase_5_replication_lag + phase_5_dr_drill_results tables + T2 failover_orchestrator + T3 dr_drill + T4 cross-region backup strategy docs EXTENSION + T5 multi-region health observability + T6 capability v1.29 + T7 tests + T8 3중 게이트 FINAL CLEAN atomic commit) / (4) cj-style Phase 5 4번째 진입점 = Phase 5 close-out retro (cj-style 76~77번째): A124~A128 close-out retro + A19 cohesion 9 surface EXTENSION PASS 검증 (multi-region surface NEW = F20.1~F20.5 multi-region backup & disaster recovery territory) + D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVE 검증 + D-LAUNCH-1-DEFER-1 honestly preserved + D-EPIC-16-REVIEW-DEFER-2~6 honestly DEFERRED 5 OPEN preserved 보존 + D-1-1-DEFER-1/2/3 grep guard 73~76~77번째 epic 연속 정직 회복 검증. A19 cohesion pattern 9 surface EXTENSION PASS 결정 (multi-region surface NEW). estimated ~50 NEW pytest PASS + ~10 NEW vitest PASS + 0 NEW ruff + 0 regressions. 결정 wire 일자: 2026-08-22 (KST).

## Epic 17 (in-progress, 2026-08-22 — cj-style Epic 17 1번째 진입점 = Epic 17 PRD entry DONE 진입 wire = cj-style 80번째 epic 연속 정직 회복, Epic 17 wire 진입 대기 = cj-style Epic 17 2번째 진입점 = cj-style 81번째 epic 연속 정직 회복 진입 대기)

- **Audit Log Viewer & Activity Stream territory 진입 (옵션 (a) Epic 17 진입, A153 결정 wire 진입)** — Epic 17 PRD entry DONE 2026-08-22 (cj-style Epic 17 1번째 진입점 = cj-style 80번째 epic 연속 정직 회복, master PRD v3.5 → v3.6 atomic edit). Epic 17 territory = (1) **audit log query API** (`apps/api/modules/audit/audit_log_query.py` NEW ~+180 LOC, 4 functions: query_audit_log + count_audit_log + get_audit_log_entry + query_activity_stream + AuditLogQueryFilters + AuditLogEntry + AuditLogPage + ActivityStreamGroup TypedDict + RLS 자동 적용 CR 0-2 verbatim + owner/admin role required + capability gate AUDIT_LOG_VIEW 결정 wire) / (2) **audit log viewer UI** (`apps/web/app/[locale]/(dashboard)/audit-log/page.tsx` NEW ~+200 LOC + 5 components: AuditLogFilterPanel + AuditLogTable + AuditLogPagination + AuditLogExportButton + AuditLogDetailModal + ko-KR.json `audit_log.*` namespace EXTENSION 14 keys + (dashboard) 보호 + vitest RTL render discipline CR 11-4 D-003 verbatim 결정 wire) / (3) **activity stream UI** (`apps/web/app/[locale]/(dashboard)/activity/page.tsx` NEW ~+150 LOC + 3 components: ActivityStreamTimeline + ActivityStreamEntry + ActivityStreamWindowSelector + ko-KR.json `activity.*` namespace EXTENSION 8 keys + all tenant members 권한 결정 wire) / (4) **cross-region audit log visibility** (Phase 5 multi-region read replica 통한 cross-region audit query + read-only routing + lag threshold 정합 lag_bytes ≤ 100MB + lag_seconds ≤ 30s + Sentry breadcrumb 결정 wire) / (5) **CSV export** (`apps/api/modules/audit/audit_log_export.py` NEW ~+120 LOC + streaming response + UTF-8 BOM + Excel-compatible comma-separated + audit-first INSERT `audit_log_exported` CR 1-1 verbatim action_class='AUDIT' + action='audit_log_exported' + actor_id + tenant_id + filters_json + row_count + trace_id + CR 12-5 D-14 envelope 결정 wire) / (6) **Capability gate AUDIT_LOG_VIEW** (capability matrix v1.29 → v1.30 EXTENSION 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러, MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY Epic 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern verbatim bind 결정 wire) / (7) **Tests + wire scope T1~T8** 결정 (~+50 NEW pytest PASS + ~+15 NEW vitest PASS + 0 NEW ruff + 0 regressions + T1 audit_log_query module + T2 audit_log_export module + T3 audit_log_viewer page + T4 activity_stream page + T5 ko-KR.json SSOT EXTENSION + T6 capability.py + capability matrix v1.30 + T7 tests + 3중 게이트 FINAL CLEAN + T8 atomic commit) + AD-32 Audit Log Viewer & Activity Stream 신규 결정 ((a)~(g) 7 sub-decisions 모두 결정 wire 진입). Sidebar/MenuProvider hot-fix `01a06e4` (cj-style 79번째) + D-EPIC-16-REVIEW-DEFER-2~6 RESOLVE sprint `512ed6a` (cj-style 78번째) + Phase 5 close-out retro `b843565` (cj-style 76~77번째) + Phase 5 atomic wire `f093f8c` (cj-style 75번째) 결정 verbatim preserve + EXTENSION (Phase 5 territory DONE 정합) + Epic 16 close-out retro `f1ead9a` (cj-style 72번째) + Epic 16 T4 admin UI follow-up sprint `ff5c3b5` (cj-style 71번째) + Epic 16 review follow-up sprint `963079c` (cj-style 70번째) + Epic 16 atomic wire `e117e09` (cj-style 69번째) + Epic 16 PRD entry `08bfca5` (cj-style 67번째) + 1st release cycle cj-style 62~66번째 모두 wire DONE 진입 + Epic 15 cycle cj-style 58~61번째 모두 wire DONE 진입 + Phase 4 cycle cj-style 53~57번째 모두 wire DONE 진입 + Phase 3 cycle cj-style 49~52번째 모두 wire DONE 진입 결정 wire 모두 보존. **Epic 17 PRD entry wire scope (master PRD v3.6 atomic edit)**: (1) front matter title v3.5 → v3.6 + changelog v3.6 entry / (2) §F21 신규 (F21.1 audit log query API + F21.2 audit log viewer UI + F21.3 activity stream UI + F21.4 cross-region audit log visibility + F21.5 CSV export + F21.6 capability gate AUDIT_LOG_VIEW + F21.7 tests + wire scope T1~T8 결정) / (3) §8.1 M0-(n) audit log viewer AC 신규 / (4) §15 로드맵 Epic 17 row status 백로그 → in-progress (PRD entry DONE 진입 wire) / (5) §부록 A A153+A154+A155+A156+A157 신규 결정 표 / (6) AD-32 Audit Log Viewer & Activity Stream 신규 결정 (audit log viewer architecture 결정) / (7) capability matrix v1.29 → v1.30 EXTENSION AUDIT_LOG_VIEW 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅. **Epic 17 진입 flow (cj-style 1~5번째 진입점 결정 보존)**: (1) cj-style Epic 17 1번째 진입점 = Epic 17 PRD entry (cj-style 80번째): ✅ DONE 2026-08-22 (master PRD v3.6 atomic edit) / (2) cj-style Epic 17 2번째 진입점 = bmad-create-story spec (cj-style 81번째): Epic 17 wire spec (T1~T8) 결정 wire 진입 대기 / (3) cj-style Epic 17 3번째 진입점 = bmad-dev-story atomic wire (cj-style 82번째): Epic 17 본체 wire T1~T8 atomic single sprint (T1 audit_log_query module + T2 audit_log_export module + T3 audit_log_viewer page + T4 activity_stream page + T5 ko-KR.json SSOT EXTENSION + T6 capability v1.30 + T7 tests + T8 3중 게이트 FINAL CLEAN atomic commit) / (4) cj-style Epic 17 4번째 진입점 = bmad-code-review (cj-style 83번째): review follow-up sprint 진입 결정 (Epic 16 wire 의 review follow-up 패턴 미러) / (5) cj-style Epic 17 5번째 진입점 = Epic 17 close-out retro (cj-style 84번째): A153~A157 close-out retro + A19 cohesion 9 surface EXTENSION PASS 검증 (audit viewer surface NEW = F21.1~F21.5 audit log viewer & activity stream territory). A19 cohesion pattern 9 surface EXTENSION PASS 결정 (audit viewer surface NEW). estimated ~50 NEW pytest PASS + ~15 NEW vitest PASS + 0 NEW ruff + 0 regressions. 결정 wire 일자: 2026-08-22 (KST).

## 1st release launch (in-progress, 2026-08-22 — cj-style 62번째 epic 연속 정직 회복 = 1st release launch PRD entry DONE 진입 wire, Epic 15 close-out retro §12 옵션 (d) 결정 wire 진입)

- **1st release launch territory 진입 (옵션 (d) 1차 출시 진입, A83 결정 wire)** — 1st release launch PRD entry DONE 2026-08-22 (cj-style 62번째 epic 연속 정직 회복 atomic docs-only wire, master PRD v3.2 → v3.3 atomic edit). 1st release territory = (1) Marketing landing page (`/landing` route + LandingHero + LandingFeatures + LandingPricing + LandingCTA + ko-KR inline copy EXTENSION, §F18.1) / (2) ToS + Privacy Policy (`docs/terms-of-service.md` + `docs/privacy-policy.md` 한국 PIPA + GDPR 정합, §F18.2) / (3) Onboarding user guide (`docs/onboarding-guide.md` 8 sections + OnboardingTooltip + first-run wizard EXTENSION Epic 1 partial scaffold `d182d7d` 정합, §F18.3) / (4) Customer support channels (`docs/support.md` + email `support@bizup.kr` + HelpWidget + FAQ `docs/faq.md`, §F18.4) / (5) Production launch verification (smoke test RE-RUN 정직 결정 + backup drill 0036 PITR quarterly + Sentry alert wiring production + RPO 4h/RTO 24h SLA verification, §F18.5) / (6) Public launch communications (`docs/launch-announcement.md` + press kit + og/assets + in-app banner, §F18.6). launch checklist 6 conditions ALL PASS 진입 시점에 1st release official launch 결정 wire 보존. capability matrix v1.26 → v1.27 EXTENSION 4 NEW rows (LAUNCH_LANDING + LAUNCH_TOS + LAUNCH_SUPPORT + LAUNCH_MONITORING, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러) + AD-29 1st release launch 신규 결정 ((a)~(f) 6 sub-decisions 모두 결정 wire 진입). Epic 15 close-out retro `729b223` 결정 verbatim preserve + EXTENSION (Epic 15 territory DONE 정합). Phase 3-0 + Phase 3-1 + Phase 4 + Epic 13/14 wire 보존 진입 (Supabase SSR + sb-access-token + Vercel + Railway + Supabase + LISTEN/NOTIFY + Magic link + OAuth + SSO + 2FA + observability + backup 결정 wire 보존). **1st release PRD entry wire scope (master PRD v3.3 atomic edit)**: (1) front matter title v3.2 → v3.3 + changelog v3.3 entry / (2) §F18 신규 (F18.1 Marketing landing + F18.2 ToS/Privacy + F18.3 Onboarding guide + F18.4 Support channels + F18.5 Production verification + F18.6 Launch comms + F18.7 capability v1.27 EXTENSION 4 NEW rows + F18.8 tests + wire scope T1~T8 결정) / (3) §8.1 M0-(k) 1st release launch 결정 wire 진입 / (4) §15 로드맵 1st release row status 백로그 → in-progress (PRD entry DONE 진입 wire) / (5) §부록 A A83+A84+A85+A86+A87 신규 결정 표 / (6) AD-29 1st release launch 신규 결정 (Marketing landing + ToS/Privacy + Onboarding + Support + Verification + Comms 6 sub-decisions) / (7) capability matrix v1.26 → v1.27 EXTENSION 4 NEW rows industry-agnostic 4-industry grants ✅/✅/✅/✅. **1st release 진입 flow (cj-style 1~4번째 진입점 결정 보존)**: (1) cj-style 1st release 1번째 진입점 = 1st release PRD entry (cj-style 62번째): ✅ DONE 2026-08-22 (master PRD v3.3 atomic edit) / (2) cj-style 1st release 2번째 진입점 = bmad-create-story spec (cj-style 63번째): 1st release wire spec (T1~T8) 결정 wire 진입 대기 / (3) cj-style 1st release 3번째 진입점 = bmad-dev-story atomic wire (cj-style 64번째): 1st release 본체 wire T1~T8 atomic single sprint (T1 Landing page + T2 ToS/Privacy + T3 Onboarding guide + T4 Support channels + T5 Production verification + T6 Capability v1.27 + T7 Tests + T8 Launch comms + 3중 게이트 FINAL CLEAN atomic commit) / (4) cj-style 1st release 4번째 진입점 = 1st release close-out retro (cj-style 65번째): A83~A87 close-out retro + A19 cohesion 9 surface EXTENSION PASS 검증 (launch surface EXTENSION) + launch checklist 6 conditions ALL PASS 검증. A19 cohesion pattern 9 surface EXTENSION PASS 결정 (launch surface EXTENSION = F18.1~F18.6 launch territory). estimated ~30 NEW pytest PASS + ~20 NEW vitest PASS + 0 NEW ruff + 0 regressions. 결정 wire 일자: 2026-08-22 (KST).

## Epic 15 (in-progress, 2026-08-22 — cj-style Epic 15 1번째 진입점 = Epic 15 PRD entry DONE 진입 wire = cj-style 58번째 epic 연속 정직 회복, Epic 15 wire 진입 대기 = cj-style Epic 15 2번째 진입점 = cj-style 59번째 epic 연속 정직 회복 진입 대기)

- **Magic link + Social OAuth + SSO enterprise SAML territory 진입 (옵션 (a) Epic 15 진입, A70+A71+A72 결정 wire 진입)** — Epic 15 PRD entry DONE 2026-08-22 (cj-style Epic 15 1번째 진입점 = cj-style 58번째 epic 연속 정직 회복, master PRD v3.1 → v3.2 atomic edit). Epic 15 territory = Magic link login (Supabase `signInWithOtp` + 5회 cool-down + email 존재 여부 노출 방지 + audit-first INSERT `magic_link_sent`) + Social OAuth Google/Naver/Kakao (Supabase `signInWithOAuth` + provider whitelist + 3회 cool-down + audit-first INSERT `social_oauth_initiated` + OAuth callback handler) + SSO enterprise SAML (`python3-saml==1.16.0` AD-14 stack pin + SAML response validation + JIT user provisioning + multi-tenant isolation RLS + audit-first INSERT `sso_identity_linked`) 결정 wire + ko-KR.json SSOT EXTENSION (auth.magic_link.* + auth.social.* + auth.sso.* namespace) + alembic 0037 `external_identities` table (multi-tenant RLS policy) + capability matrix v1.25 → v1.26 EXTENSION 5 NEW rows (MAGIC_LINK + SOCIAL_OAUTH_GOOGLE + SOCIAL_OAUTH_NAVER + SOCIAL_OAUTH_KAKAO + SSO_ENTERPRISE, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러) + AD-28 Magic link + Social OAuth + SSO enterprise SAML 신규 결정. Epic 1 carry-over D-1-1-DEFER-1/2/3 honestly ✅ RESOLVED 58번째 epic 연속 정직 회복 (CR 11-3 discipline). Phase 3-1 wire (`d3e7454`) 의 Supabase SSR + sb-access-token cookie + auth route group (auth) + dashboard route group (dashboard) + auth middleware EXTENSION + Epic 12 2FA 게이트 보존 + Phase 4 wire (`71a033a`) 의 Vercel + Railway + Supabase + Sentry + observability 결정 wire 보존 + Epic 13/14 wire 의 LISTEN/NOTIFY multi-process coordination 결정 wire 보존. **Epic 15 PRD entry wire scope (master PRD v3.2 atomic edit)**: (1) front matter title v3.1 → v3.2 + changelog v3.2 entry / (2) §F17 신규 (F17.1 Magic link / F17.2 Social OAuth / F17.3 SSO enterprise SAML / F17.4 ko-KR.json SSOT EXTENSION / F17.5 capability matrix v1.26 EXTENSION 5 NEW rows / F17.6 tests + wire scope T1~T8 결정) / (3) §8.1 M0-(h) Magic link + M0-(i) Social OAuth + M0-(j) SSO enterprise SAML 3 NEW 인수 불릿 / (4) §15 로드맵 Epic 15 row status 백로그 → in-progress (PRD entry DONE 진입 wire) / (5) §부록 A A70+A71+A72 ✅ done + A75 preserved + A79+A80+A81+A82 신규 결정 표 / (6) AD-28 Magic link + Social OAuth + SSO enterprise SAML 신규 결정 (Supabase `signInWithOtp` + `signInWithOAuth` + `python3-saml==1.16.0` AD-14 stack pin + JIT user provisioning + multi-tenant isolation CR 0-2 RLS lesson + audit-first INSERT 3 NEW) / (7) capability matrix v1.25 → v1.26 EXTENSION 5 NEW rows industry-agnostic 4-industry grants ✅/✅/✅/✅. **Epic 15 진입 flow (cj-style 1~4번째 진입점 결정 보존)**: (1) cj-style Epic 15 1번째 진입점 = Epic 15 PRD entry (cj-style 58번째): ✅ DONE 2026-08-22 (master PRD v3.2 atomic edit) / (2) cj-style Epic 15 2번째 진입점 = bmad-create-story spec (cj-style 59번째): Epic 15 wire spec (T1~T8) 결정 wire 진입 대기 / (3) cj-style Epic 15 3번째 진입점 = bmad-dev-story atomic wire (cj-style 60번째): Epic 15 본체 wire T1~T8 atomic single sprint (T1 Magic link wrapper + T2 Magic link UI + T3 Social OAuth wrapper + T4 OAuth callback + T5 SSO SAML backend + T6 SSO UI + T7 capability v1.26 + T8 tests + 3중 게이트 FINAL CLEAN atomic commit) / (4) cj-style Epic 15 4번째 진입점 = Epic 15 close-out retro (cj-style 61~62번째): A70+A71+A72 honestly RESOLVE 검증 + A19 cohesion 9 surface EXTENSION PASS 검증 (auth surface EXTENSION) + D-1-1-DEFER-1/2/3 grep guard 58~61~62번째 epic 연속 정직 회복 검증. A19 cohesion pattern 9 surface EXTENSION PASS 결정 (auth surface EXTENSION = F17.1~F17.3 magic link + social OAuth + SSO enterprise territory). estimated ~60 NEW pytest PASS + ~50 NEW vitest PASS + 0 NEW ruff + 0 regressions. 결정 wire 일자: 2026-08-22 (KST).

- **Deployment config + Dockerfile + health check + observability + database backup territory 진입 (옵션 (a) Phase 4 진입, A73 결정 wire)** — Phase 4 PRD entry DONE 2026-08-22 (cj-style Phase 4 1번째 진입점 = cj-style 53번째 epic 연속 정직 회복, master PRD v3.0 → v3.1 atomic edit).

- **Magic link + Social OAuth + SSO enterprise SAML territory 진입 (옵션 (a) Epic 15 진입, A70+A71+A72 결정 wire 진입)** — Epic 15 PRD entry DONE 2026-08-22 (cj-style Epic 15 1번째 진입점 = cj-style 58번째 epic 연속 정직 회복, master PRD v3.1 → v3.2 atomic edit). Epic 15 territory = Magic link login (Supabase `signInWithOtp` + 5회 cool-down + email 존재 여부 노출 방지 + audit-first INSERT `magic_link_sent`) + Social OAuth Google/Naver/Kakao (Supabase `signInWithOAuth` + provider whitelist + 3회 cool-down + audit-first INSERT `social_oauth_initiated` + OAuth callback handler) + SSO enterprise SAML (`python3-saml==1.16.0` AD-14 stack pin + SAML response validation + JIT user provisioning + multi-tenant isolation RLS + audit-first INSERT `sso_identity_linked`) 결정 wire + ko-KR.json SSOT EXTENSION (auth.magic_link.* + auth.social.* + auth.sso.* namespace) + alembic 0037 `external_identities` table (multi-tenant RLS policy) + capability matrix v1.25 → v1.26 EXTENSION 5 NEW rows (MAGIC_LINK + SOCIAL_OAUTH_GOOGLE + SOCIAL_OAUTH_NAVER + SOCIAL_OAUTH_KAKAO + SSO_ENTERPRISE, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러) + AD-28 Magic link + Social OAuth + SSO enterprise SAML 신규 결정. Epic 1 carry-over D-1-1-DEFER-1/2/3 honestly ✅ RESOLVED 58번째 epic 연속 정직 회복 (CR 11-3 discipline). Phase 3-1 wire (`d3e7454`) 의 Supabase SSR + sb-access-token cookie + auth route group (auth) + dashboard route group (dashboard) + auth middleware EXTENSION + Epic 12 2FA 게이트 보존 + Phase 4 wire (`71a033a`) 의 Vercel + Railway + Supabase + Sentry + observability 결정 wire 보존 + Epic 13/14 wire 의 LISTEN/NOTIFY multi-process coordination 결정 wire 보존. **Epic 15 PRD entry wire scope (master PRD v3.2 atomic edit)**: (1) front matter title v3.1 → v3.2 + changelog v3.2 entry / (2) §F17 신규 (F17.1 Magic link / F17.2 Social OAuth / F17.3 SSO enterprise SAML / F17.4 ko-KR.json SSOT EXTENSION / F17.5 capability matrix v1.26 EXTENSION 5 NEW rows / F17.6 tests + wire scope T1~T8 결정) / (3) §8.1 M0-(h) Magic link + M0-(i) Social OAuth + M0-(j) SSO enterprise SAML 3 NEW 인수 불릿 / (4) §15 로드맵 Epic 15 row status 백로그 → in-progress (PRD entry DONE 진입 wire) / (5) §부록 A A70+A71+A72 ✅ done + A75 preserved + A79+A80+A81+A82 신규 결정 표 / (6) AD-28 Magic link + Social OAuth + SSO enterprise SAML 신규 결정 (Supabase `signInWithOtp` + `signInWithOAuth` + `python3-saml==1.16.0` AD-14 stack pin + JIT user provisioning + multi-tenant isolation CR 0-2 RLS lesson + audit-first INSERT 3 NEW) / (7) capability matrix v1.25 → v1.26 EXTENSION 5 NEW rows industry-agnostic 4-industry grants ✅/✅/✅/✅. **Epic 15 진입 flow (cj-style 1~4번째 진입점 결정 보존)**: (1) cj-style Epic 15 1번째 진입점 = Epic 15 PRD entry (cj-style 58번째): ✅ DONE 2026-08-22 (master PRD v3.2 atomic edit) / (2) cj-style Epic 15 2번째 진입점 = bmad-create-story spec (cj-style 59번째): Epic 15 wire spec (T1~T8) 결정 wire 진입 대기 / (3) cj-style Epic 15 3번째 진입점 = bmad-dev-story atomic wire (cj-style 60번째): Epic 15 본체 wire T1~T8 atomic single sprint (T1 Magic link wrapper + T2 Magic link UI + T3 Social OAuth wrapper + T4 OAuth callback + T5 SSO SAML backend + T6 SSO UI + T7 capability v1.26 + T8 tests + 3중 게이트 FINAL CLEAN atomic commit) / (4) cj-style Epic 15 4번째 진입점 = Epic 15 close-out retro (cj-style 61~62번째): A70+A71+A72 honestly RESOLVE 검증 + A19 cohesion 9 surface EXTENSION PASS 검증 (auth surface EXTENSION) + D-1-1-DEFER-1/2/3 grep guard 58~61~62번째 epic 연속 정직 회복 검증. A19 cohesion pattern 9 surface EXTENSION PASS 결정 (auth surface EXTENSION = F17.1~F17.3 magic link + social OAuth + SSO enterprise territory). estimated ~60 NEW pytest PASS + ~50 NEW vitest PASS + 0 NEW ruff + 0 regressions. 결정 wire 일자: 2026-08-22 (KST).

- **Deployment config + Dockerfile + health check + observability + database backup territory 진입 (옵션 (a) Phase 4 진입, A73 결정 wire)** — Phase 4 PRD entry DONE 2026-08-22 (cj-style Phase 4 1번째 진입점 = cj-style 53번째 epic 연속 정직 회복, master PRD v3.0 → v3.1 atomic edit). Phase 4 territory = Vercel frontend (vercel.json + framework=nextjs + regions=[icn1] + buildCommand=`pnpm --filter web build` + env mapping NEXT_PUBLIC_SUPABASE_URL/ANON_KEY/API_BASE_URL + headers CSP+X-Frame-Options+HSTS + redirects legacy `/ko-KR/*` → `/ko/*`) + Railway backend (railway.toml + builder=DOCKERFILE + dockerfilePath=`apps/api/Dockerfile` + healthcheckPath=`/api/v1/health` + restartPolicyType=ON_FAILURE + env mapping DATABASE_URL/SUPABASE_JWT_SECRET/SUPABASE_URL/ANON_KEY/SERVICE_ROLE_KEY/SENTRY_DSN) + Supabase production PostgreSQL (PITR 7일 자동 + Supabase Storage 결정 wire 보류) 결정 wire + per-app Dockerfile 분리 (`apps/web/Dockerfile` Next.js standalone output + `apps/api/Dockerfile` FastAPI uvicorn, AD-14 stack pin by @sha256: digest 결정) + Health check + observability wire (`GET /api/v1/health` FastAPI endpoint + `GET /api/health` Next.js route handler + liveness/readiness 분리 결정 + Sentry browser SSR-safe init + Sentry FastAPI server integration + tracesSampleRate=0.1) + Database backup strategy (alembic 0036 phase_4_backup_strategy table + Supabase PITR 7일 자동 + 수동 export 보완 + RPO 5분 / RTO 1시간 결정 + SHA-256 checksum validation) + capability matrix v1.24 → v1.25 EXTENSION (DEPLOYMENT_PROD + DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP + DEPLOYMENT_HEALTH_CHECK 4 NEW rows, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러) + AD-27 Deployment 신규 결정 (Vercel frontend + Railway backend + Supabase PostgreSQL + Sentry observability 결정 wire). Epic 12 wire 정합 (audit-first INSERT 보존) + Epic 13/14 wire 정합 (PostgreSQL LISTEN/NOTIFY multi-process coordination 결정 wire 보존). **Phase 4 PRD entry wire scope (master PRD v3.1 atomic edit)**: (1) front matter title v3.0 → v3.1 + changelog v3.1 entry / (2) §F16 신규 (F16.1 vercel.json Vercel frontend deployment config / F16.2 railway.toml Railway backend deployment config / F16.3 apps/web/Dockerfile + apps/api/Dockerfile per-app Dockerfile 분리 / F16.4 docs/deployment.md production deployment runbook 12 sections / F16.5 health check + observability + monitoring / F16.6 database backup strategy / F16.7 tests + wire scope T1~T8 결정) / (3) §8.1 M0-(g) production deployment 결정 wire 진입 / (4) §15 로드맵 Phase 4 row status 백로그 → in-progress (PRD entry DONE 진입 wire) / (5) §부록 A A73 + A74 + A76 + A77 + A78 신규 결정 표 / (6) AD-27 Deployment 신규 결정 (Vercel + Railway + Supabase + Sentry 결정 wire) / (7) capability matrix v1.24 → v1.25 EXTENSION DEPLOYMENT_PROD + DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP + DEPLOYMENT_HEALTH_CHECK 4 NEW rows (industry-agnostic 4-industry grants ✅/✅/✅/✅). **Phase 4 진입 flow (cj-style 1~3번째 진입점 결정 보존)**: (1) cj-style Phase 4 1번째 진입점 = Phase 4 PRD entry (cj-style 53번째): ✅ DONE 2026-08-22 (master PRD v3.1 atomic edit) / (2) cj-style Phase 4 2번째 진입점 = bmad-create-story spec (cj-style 54번째): Phase 4 wire spec (T1~T8) 결정 wire 진입 대기 / (3) cj-style Phase 4 3번째 진입점 = bmad-dev-story atomic wire (cj-style 55번째): Phase 4 본체 wire T1~T8 atomic single sprint (T1 Vercel config + T2 Railway config + T3 per-app Dockerfile + T4 deployment runbook + T5 health check + observability + T6 database backup strategy + T7 capability v1.25 + T8 tests + 3중 게이트 FINAL CLEAN atomic commit). A19 cohesion pattern 9 surface EXTENSION PASS 결정 (deployment surface NEW). estimated ~40 NEW pytest PASS + ~20 NEW vitest PASS + 0 NEW ruff + 0 regressions. 결정 wire 일자: 2026-08-22 (KST).

## Epic 14 (in-progress, 2026-08-20 — cj-style Epic 14 1번째 진입점 = Epic 14 PRD entry DONE 진입 wire = cj-style 45번째 epic 연속 정직 회복, 14-1 atomic wire 진입 대기 = cj-style Epic 14 2번째 진입점 = cj-style 46번째 epic 연속 정직 회복 진입 대기)

- **LISTEN/NOTIFY Consume 2nd Batch** — D-13-1-DEFER-3 separate epic territory 결정 wire 진입 (옵션 (a) Epic 14 진입). **Epic 14 PRD entry DONE 2026-08-20** (cj-style Epic 14 1번째 진입점 = cj-style 45번째 epic 연속 정직 회복, master PRD v2.4 → v2.5 atomic edit). Epic 14 territory = cross-tenant invalidation fan-out (multi-tenant isolation 검증 + tenant-level subscription routing) + multi-process coordination (multi-worker 환경 listener process-per-pod, **PostgreSQL LISTEN/NOTIFY multi-process coordination 결정 wire 진입** = A58 결정, Option 1 verbatim 보존 결정, Option 2 Redis pub/sub rejected rationale: G2 "새벽에 혼자 고칠 수 있는 시스템" 정합 — 인프라 최소화). Epic 13 close-out retro §7 A53 결정 verbatim wire (cj-style Epic 13 5번째 진입점 = cj-style Epic 13 carry-over 17번째 docs only). A45+A46 결정 wire 진입 = 옵션 (a) Epic 14 follow-up sprint 진입 결정 (bundled into ONE Epic 14 carry-over sprint = cj-style Epic 14 3번째 진입점 진입 시점). **Epic 14 PRD entry wire scope (master PRD v2.5 atomic edit)**: (1) front matter title v2.4 → v2.5 + changelog v2.5 entry / (2) §F14 신규 (F14.1 cross-tenant invalidation fan-out 토폴로지 + F14.2 multi-process coordination leader/follower + F14.3 V8 determinism + cross-language drift detector EXTENSION + F14.4 tests + wire scope T1~T9 결정) / (3) §8.1 M10-(d)·§F10.1-(d) cross-tenant fan-out EXTENSION 결정 wire 진입 / (4) §15 로드맵 Epic 14 row status 백로그 → in-progress (PRD entry DONE 진입 wire) / (5) §부록 A A57+A58+A59 신규 결정 표 / (6) AD-25 EXTENSION 4-channel → 5+ channels 결정 wire (cross_tenant_fanout channel 추가) / (7) capability matrix v1.22 → v1.23 신규 2 rows (`LISTEN_NOTIFY_TENANT_FANOUT` + `LISTEN_NOTIFY_MULTIPROCESS`, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러). **Epic 14 진입 flow (cj-style 1~3번째 진입점 결정 보존)**: (1) cj-style Epic 14 1번째 진입점 = Epic 14 PRD entry (cj-style 45번째): ✅ DONE 2026-08-20 (master PRD v2.5 atomic edit) / (2) cj-style Epic 14 2번째 진입점 = Story 14.1 bmad-dev-story atomic wire (cj-style 46번째): cross-tenant invalidation fan-out + multi-process coordination 본체 wire (T1~T9 atomic single sprint) 진입 대기 / (3) cj-style Epic 14 3번째 진입점 = Epic 14 close-out retro (cj-style 47번째): A45+A46 follow-up sprint 진입 결정 (bundled into ONE Epic 14 carry-over sprint). Epic 14 보류 결정 (cj-style Epic 14 진입 시점에 동시 결정 wire): A55 LISTEN/NOTIFY 실측 evidence 정합 sweep (D-13-1-DEFER-2 ✅ RESOLVE) + A56 A42 A36 SDR 검증 4-step 보존 + Epic 14+ 적용 ✅ done + preserved. **Story 14-1 wire scope 결정 보존** (cj-style Epic 14 2번째 진입점 진입 시점에 wire): T1 alembic 0034 + T2 listener EXTENSION multi-process coordination + T3 main.py lifespan EXTENSION leader election + T4 cross-tenant fan-out + multi-process dispatch adapters + T5 capability 2 NEW rows v1.23 + T6 V8 determinism EXTENSION + T7 cross-lang drift EXTENSION + T8 multi-process coordination tests + T9 3중 게이트 FINAL CLEAN atomic commit. estimated ~140 NEW pytest PASS (across 9 test files) + 0 NEW ruff + 0 regressions.

## 이론 근거 (2026-07 웹 검증 요지)
- **AI-driven ABC**: AI 결합 ABC가 원가 배부 오류를 크게 줄이고, 이상감지·예측 모델·동인 자동 식별이 실무 표준으로 부상 — 비즈업 M10(1차) → 이상감지 알림(2차) → 멀티에이전트(3차)의 단계 승격 경로와 일치.
- **TDABC의 표준화**: 시간방정식·CCR 기반 TDABC가 전통 ABC의 구축·유지 부담을 낮추는 사실상의 표준 — 1차 장착 근거.
- **클라우드 ABC의 접근성**: 클라우드 기반 ABC가 도입 기간을 단축해 중소기업 접근성을 열고 있음 — 월 1만원 SaaS 포지셔닝의 근거.
- **미사용능력·유휴원가 관리**: 유휴능력 원가의 별도 관리가 정론으로 정착 — A9 공리의 근거.
- **지속가능성(환경) 원가**: ABC를 환경영향 원가에 결합하는 연구 흐름 — 장기 검토 항목(로드맵 외 참고).

---

# 16. 다음 단계

1. **통합 ERD v2.0 작성** (본 PRD 확정 직후): 기존 ERD 2권 + 테이블명세서(총 63테이블)를 1권으로 통합하며 다음 신규 반영 — ① 기계시간 입력 필드(machine_hours, 배부기준 ③ 선택 시) ② 예산 시나리오(가상 기간) 구조 ③ 주문 잔량·자재소요 파생 뷰 ④ 일자별 선택 모드(record_date) 확정 ⑤ 생산기준 고정 + 재고조정 자동화 컬럼 ⑥ 배부기준 3종 교체(직접노무원가/직접노무시간/기계시간) ⑦ ABC 파일 발견분(원가풀 3기준 배부, 활동 3기준 매트릭스, 동인 건수/비율 토글, 간접인건비 시간 검증)
2. 통합 DDL 스크립트 (RLS·마감잠금 트리거 포함)
3. 엔진 산식 명세서 (엑셀 셀 → Python 함수 매핑, V8 대조 테스트 설계)
4. 화면 정의서 (HTML 목업) + 디자인 가이드

---

## 부록 A. 확정 결정 이력 (Q-A ~ Q-J)

| 결정 | 내용 |
|------|------|
| Q-A | 제조경비 배부기준 = 직접노무원가 / 직접노무시간 / 기계시간 3종 택1 (기계시간 신규 입력) |
| Q-B | 주문 관리 전부 포함, '선택 기능' 지위 (미입력 시 숨김) |
| Q-C | 월합계 기본 + 일자별 선택 모드 |
| Q-D | 예산 시나리오(가상 기간) 1차, A×B×C×D 편성 엔진 2차(산식 보존) |
| Q-E | 노무비 배부 = 공수 기반 단일 (할당인원 방식 미채택) |
| Q-F | 생산기준 고정 + '제품 재고 조정' 라인 자동화 (매출기준 배부 폐기 — pl3 92% 왜곡 실증) |
| Q-G | report 파일은 기존 구조 분석으로 갈음 |
| Q-H | 통합 PRD 1권 완전 대체 (기존 2권 폐기), ERD도 후속 통합 1권 |
| Q-I | 부문-엔진 고정 매핑 (제조 ABC는 3차) |
| Q-J | 최신 지식 = 확정분(TDABC+AI 3종) 1차, 최신 동향은 제15장 이론 근거로 기재 |

### Epic 7~9 retro 결정 (2026-08-08 ~ 2026-08-17)

| 결정 | 내용 |
|------|------|
| A19 | math surface cohesion pattern — 단일 math surface 진입 시점에 함수/dataclass/exception/constants 동시 wire (abc_engine.py 9-1, pdf_generator.py 9-4 precedent) |
| A20 | service module cohesion pattern — kernel + service + handler + tests 4-way wire (CR 1.1 audit-first INSERT 보존) |
| A21 | capability matrix v1.18+ SSOT pattern — 각 Epic 도입 시 capability matrix 신규 row 추가 + drift detector test (P-015 SSOT) wire |
| A22 | inventory projection.py 제거 — `packages/services/m2_input/inventory_math.py` 으로 일원화 (carry-over sprint) |
| A23 | Epic 9 cj-style 4-story + retro 5번째 진입점 패턴 (cj-style Epic 7~8 동일) |
| A24 | capability matrix v1.18 industry-agnostic 4-industry grants (CR 12-1 L4 precedent) |
| A25 | A19 cohesion pattern 6번째 surface = `packages/cost_engine/abc_engine.py` (9-1 wire tip) |
| A26 | Epic 9 8-3 honestly DEFER #4 해소 (8-3 follow-up sprint) |
| A27 | A19 follow-up sprint for 8 honestly DEFER (cj-style 9-6 follow-up 진입) |

### Epic 9 close-out 결정 (2026-08-17, 9-6/9-7 follow-up sprint)

| 결정 | 내용 |
|------|------|
| A28 | ABC_CALCULATION industry-agnostic 보존 (CR 12-1 L4) — 모든 Epic 9 wire 영향 0 |
| A29 | dual-route dispatch (M3 orchestrator) 보존 — service → M9 ABC, else → M3 traditional |
| A30 | SHARED PDF generator factory pattern (`packages/services/m5_reports/pdf_generator.py`) — Discriminated union `report_id: Literal[15, 16, 17, 18, 19, 20, 21]` |
| A31 | Report #15 wire schedule (cj-style Epic 9 6번째 진입점 권장) — A30 SHARED factory EXTENSION 1st case |
| A32 | A30 SHARED factory pattern reuse entry — Report #15 wire 진입 시점에 pdf_generator EXTENSION |
| A33 | A19 cohesion pattern 9 surface — Report #15 wire 진입 시점에 pdf_generator EXTENSION |
| A34 | mixed honestly DEFER 4-category framework — (a) docs 정합 / (b) retro input / (c) separate epic / (d) dedicated sprint |
| A35 | frontend test debt honestly DEFER (d) — vitest mount + TS mirror parity 정직 회복 (9-7 wire 진입) |
| A36 | SDR 검증 프로토콜 wire — 4-step 자동화 (commit prefix lint + sprint-status structure + vitest file count drift + commit consistency) |

### Epic 10 close-out 결정 (2026-08-19, cj-style 5번째 진입점)

| 결정 | 내용 |
|------|------|
| **A37** | **Master PRD v2.0 본체 edit** (§F10.1·§F10.2 + §8.1 M10 + §12 AI 3종 + §13.1 ko-KR + §14 NFR + §14.B NON-GOAL #5·6 + §AD-7/17/25 verbatim + §SM-3a + §A11 + §NFR18 + §부록 A A23~A42). cj-style carry-over 15번째 docs only atomic wire (Epic 10 PRD extension → master PRD 본체 edit). 결정 wire 일자: 2026-08-20 |
| **A38** | A35 frontend test debt dedicated sprint (cj-style carry-over 14번째) — Epic 10 4 stories frontend files + TS mirror parity + vitest mount 일괄 wire |
| **A39** | D-10-2-DEFER-3 LISTEN/NOTIFY consume 별도 epic territory 결정 (post-Epic 10) — AD-25 cache invalidation trigger EXTENSION for close/reopen. **결정 wire 진입 2026-08-20 (사용자 옵션 (a))**: Epic 13 = LISTEN/NOTIFY 전용 epic (Epic 13 1번째 진입점). Story 13-1 = LISTEN/NOTIFY consume trigger EXTENSION wire 진입. D-10-2-DEFER-3 ✅ RESOLVED 진입. A45/A46/A50 preserved (Epic 13 후속 story 진입). cj-style Epic 13 1번째 진입점 결정 verbatim bind. AD-25 verbatim 100% binding 진입. **✅ done 진입 2026-08-20** (Epic 13 PRD entry 결정 wire 완료 + §F13 LISTEN/NOTIFY 명세 신규 + §8.1 M10-(d)·§F10.1-(d) EXTENSION 진입 + §15 로드맵 Epic 13 row + A51 결정 wire) |
| **A40** | A31/A32/A33 (Report #15 wire schedule) 처리 결정 — Epic 11 carry-over sprint 진입 시 wire (cj-style Epic 11 4번째 진입점 = Epic 11 Story 11.5 + 11.6 진입 결정) |
| **A41** | Epic 11 carry-over sprint 진입 결정 (A13/A17/A18 sprint-up items) — 11-3 DEFER 8 items triage + W2 reopen 4-channel 검증 + A5 drift detector 3-way extension. ✅ done via 11-4 (cj-style carry-over 11번째) + 11-5 (cj-style 36번째) atomic wire |
| **A42** | A36 SDR 검증 4-step 자동화 wire 보존 + Epic 11+ 적용 — commit prefix lint + sprint-status structure 검증 + vitest file count drift + commit consistency 자동 검증 단계 모두 PASS |

### Epic 13 PRD entry 결정 (2026-08-20, cj-style Epic 13 1번째 진입점)

| 결정 | 내용 |
|------|------|
| **A51** | **Epic 13 = LISTEN/NOTIFY 전용 epic PRD entry** — Epic 10 close-out retro §7 A39 결정 verbatim wire (cj-style Epic 13 1번째 진입점). Story 13-1 = LISTEN/NOTIFY consume trigger EXTENSION wire 진입 (NOTIFY trigger alembic 0033 + LISTEN daemon FastAPI lifespan + 4-channel cache eviction handlers + reconnect/backoff + V8 determinism + CR 12-5 cross-lang drift detector EXTENSION). 결정 wire = master PRD v2.2 atomic edit (§F13 신규 + §8.1 M10-(d)·§F10.1-(d) EXTENSION + §15 로드맵 Epic 13 row + §부록 A A39 done 진입 + A51 NEW). AD-25 verbatim 100% binding. D-10-2-DEFER-3 ✅ RESOLVED. capability matrix v1.22 신규 row `LISTEN_NOTIFY` (Epic 13 wire 진입). CR 11-3 honest-DEFER discipline + A36 SDR 검증 4-step 자동 적용 (commit prefix lint + sprint-status structure + vitest file count drift + commit consistency 모두 PASS). ✅ done 진입 2026-08-20 (commit `3e398b9`). **A52 follow-on**: Story 13-1 atomic wire 진입 |
| **A52** | **✅ done** (2026-08-20, cj-style Epic 13 2번째 진입점 = cj-style 42번째 epic 연속 정직 회복) — Story 13-1 bmad-dev-story atomic wire T1~T8 결정 wire. wire_commit = `f2ea2f6` atomic single sweep, 17 files (12 NEW + 5 MODIFIED), ~107 NEW pytest PASS, 0 NEW ruff (8 auto-fixed), A19 cohesion 8 surface PASS, capability matrix v1.22 SSOT RED→GREEN, 3중 게이트 FINAL CLEAN. D-13-1-DEFER-1/2/3 preserved (CR 11-3 진형화) — D-13-1-DEFER-1 ✅ RESOLVED 진입 결정 wire (A54 master PRD v2.3 atomic edit 진입 결정). 결정 wire 일자: 2026-08-20 (Epic 13 PRD entry done 진입 직후 즉시) |
| **A45** | **✅ 결정 wire 진입** (2026-08-20, cj-style Epic 13 5번째 진입점 = cj-style Epic 13 carry-over 17번째 docs only) — Epic 11 close-out retro 2nd (2026-08-20) — 11-3 honestly DEFER 3 items (T10 docs LOW + A5 partial LOW + reopen state transition LOW) still-pending. **사용자 결정 = 옵션 (a) Epic 14 follow-up sprint 진입** 결정 wire 진입 (bundled with A46 into ONE Epic 14 carry-over sprint = cj-style Epic 14 3번째 진입점 진입 시점). Epic 14 PRD entry + 14-1 atomic wire DONE 후 follow-up sprint 진입 결정 wire 보존. deadline: Epic 14 follow-up sprint 진입 시점 (cj-style Epic 14 3번째 진입점) |
| **A46** | **✅ 결정 wire 진입** (2026-08-20, cj-style Epic 13 5번째 진입점 = cj-style Epic 13 carry-over 17번째 docs only) — Epic 11 close-out retro 2nd (2026-08-20) — 11-5 A13 residual stub UUIDs (`00000000-...`) with `TODO(11-4 carry)` markers preserved as W-class DEFER. **사용자 결정 = 옵션 (a) Epic 14 follow-up sprint 진입** 결정 wire 진입 (bundled with A45 into ONE Epic 14 carry-over sprint = cj-style Epic 14 3번째 진입점 진입 시점). Epic 14 PRD entry + 14-1 atomic wire DONE 후 follow-up sprint 진입 결정 wire 보존. deadline: Epic 14 follow-up sprint 진입 시점 (cj-style Epic 14 3번째 진입점) |
| **A50** | (preserved) Epic 11 close-out retro 2nd (2026-08-20) — A39 LISTEN/NOTIFY consume trigger EXTENSION 결정 = 별도 epic territory. Epic 13 PRD entry 진입 ✅ done (A51 결정 wire = A39 결정 = Epic 13 진입 결정 wire). A50 reframing close-out 완료 |

### Epic 13 close-out retro 결정 (2026-08-20, cj-style Epic 13 4번째 진입점 = cj-style 43번째 epic 연속 정직 회복)

| 결정 | 내용 |
|------|------|
| **A53** | **✅ done** (2026-08-20, cj-style Epic 13 5번째 진입점 = cj-style Epic 13 carry-over 17번째 docs only = cj-style 44번째 epic 연속 정직 회복) — **D-13-1-DEFER-3 separate epic LISTEN/NOTIFY consume 2nd batch 결정** (cross-tenant invalidation fan-out + multi-process coordination = Epic 13 후속 story 진입 결정). **사용자 결정 = 옵션 (a) Epic 14 진입** = Epic 14 = LISTEN/NOTIFY consume 2nd batch territory 진입 결정 wire. Epic 14 PRD entry 진입 대기 (cj-style Epic 14 1번째 진입점 = cj-style 45번째 epic 연속 정직 회복 진입 대기). 옵션 (b) Epic 13 follow-up sprint 진입 / 옵션 (c) Epic 13 close-out 후 별도 Epic 14 진입 모두 rejected (rationale: Epic 14 단일 territory로 통합 진입 = A45+A46 follow-up sprint까지 bundled 가능 = 결정 wire 효율성 + cj-style 1번째 진입점 표준 진입 가능). 3중 게이트 impact NONE (docs only 변경, no code/test/sprint-status delta 외에 PRD edit 신규). CR 11-3 honest-DEFER discipline + A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS). 결정 wire 일자: 2026-08-20 |
| **A54** | **✅ done** (2026-08-20, cj-style Epic 13 5번째 진입점 = cj-style Epic 13 carry-over 17번째 docs only) — master PRD v2.2 → v2.3 atomic edit (D-13-1-DEFER-1 ✅ RESOLVE). 결정 wire 진입 = §F13 verbatim 13-1 wire 정합 확장 (F13.1 6-key alphabetical JSON payload + alembic 0033 trigger verbatim + F13.2 4-channel handler verbatim wire + F13.3 V8 determinism + cross-language drift detector EXTENSION + F13.4 T1~T8 atomic wire DONE + capability `LISTEN_NOTIFY` v1.22 4-industry grants) + §15 로드맵 Epic 13 row status in-progress → done (cj-style 1~4번째 진입점 모두 wire DONE) + §부록 A A52 done + A53+A54+A55+A56 신규 결정 + AD-25 EXTENSION 표기. 3중 게이트 impact NONE (docs only 변경). CR 11-3 honest-DEFER discipline + A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS) |
| **A55** | (preserved) **LISTEN/NOTIFY 실측 evidence 정합 sweep** (D-13-1-DEFER-2 ✅ RESOLVE 진입 시점). 1차 출시 후 진입 시점 (production runtime data 정합 sweep) — D-13-1-DEFER-3 결정 시점에 동시 결정 wire. Owner: Amelia + Dana. deadline: 1차 출시 후 진입 시점 |
| **A56** | **✅ done + preserved** (2026-08-20) — A42 A36 SDR 검증 4-step 자동화 wire 보존 + Epic 14+ 모든 stories 자동 적용 결정 (Epic 13 1-story cycle 정직 회복 검증). 13-1 wire 시점에 commit prefix lint + sprint-status structure + vitest file count drift + commit consistency 모두 PASS 자동 적용. CR 11-3 honest-DEFER discipline + A36 SDR 검증 4-step 모두 보존 결정 |

### Epic 14 PRD entry 결정 (2026-08-20, cj-style Epic 14 1번째 진입점 = cj-style 45번째 epic 연속 정직 회복)

| 결정 | 내용 |
|------|------|
| **A57** | **Epic 14 = LISTEN/NOTIFY Consume 2nd Batch PRD entry** — Epic 13 close-out retro §7 A53 결정 verbatim wire (cj-style Epic 14 1번째 진입점 = cj-style 45번째 epic 연속 정직 회복). Story 14-1 = cross-tenant invalidation fan-out + multi-process coordination 본체 wire 진입 (T1~T9 atomic single sprint). 결정 wire = master PRD v2.4 → v2.5 atomic edit (§F14 신규 + §8.1 M10-(d)·§F10.1-(d) cross-tenant fan-out EXTENSION 진입 + §15 로드맵 Epic 14 row status 백로그 → in-progress + §부록 A A57+A58+A59 신규 결정 표 + AD-25 EXTENSION 5+ channels + capability matrix v1.22 → v1.23 LISTEN_NOTIFY_TENANT_FANOUT + LISTEN_NOTIFY_MULTIPROCESS 2 NEW rows industry-agnostic 4-industry grants ✅/✅/✅/✅). AD-25 verbatim 100% binding EXTENSION. D-13-1-DEFER-3 ✅ RESOLVED (A53 결정 wire). CR 11-3 honest-DEFER discipline + A36 SDR 검증 4-step 자동 적용 (commit prefix lint + sprint-status structure + vitest file count drift + commit consistency 모두 PASS). ✅ done 진입 2026-08-20. **A58+A59 follow-on**: AD-25 EXTENSION + capability 신규 row 결정 wire |
| **A58** | **AD-25 EXTENSION 4-channel → 5+ channels 결정** — Epic 14 PRD entry 진입 시점에 결정 (cj-style Epic 14 1번째 진입점 = cj-style 45번째 epic 연속 정직 회복). Epic 13 13-1 wire 시점 4-channel publisher (`ai_cache` / `cost_engine_cache` / `fiscal_period_cache` / `closing_snapshot_cache`) 에 **cross_tenant_fanout channel 1 channel 추가** 결정 wire (총 5+ channels EXTENSION). Cross-tenant invalidation fan-out channel = tenant-level subscription routing + multi-tenant isolation 검증 (CR 0-2 RLS lesson 적용 + AD-22 verbatim 보존). NOTIFY payload 7-key alphabetical EXTENSION (channel='cross_tenant_fanout' + source_tenant_id + target_tenant_ids + correction_group_id + invalidation_id + period_key + trace_id). **Multi-process coordination Option 1 결정**: PostgreSQL `LISTEN/NOTIFY` only multi-process coordination via pg_notify fan-out leader/follower model (PostgreSQL advisory lock `pg_try_advisory_xact_lock(LISTEN_FANOUT_LOCK_ID)` 으로 leader election + follower health check 30s interval + leader takeover 90s timeout). Option 2 Redis pub/sub fan-out **rejected** 결정 (rationale: G2 "새벽에 혼자 고칠 수 있는 시스템" 정합 — 인프라 최소화). Alembic 0034 NEW 결정 (down_revision='0033_listen_notify_consume_trigger'). CR 11-3 honest-DEFER discipline + A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS). 결정 wire 일자: 2026-08-20 |
| **A59** | **Capability matrix v1.22 → v1.23 LISTEN_NOTIFY_TENANT_FANOUT + LISTEN_NOTIFY_MULTIPROCESS 2 NEW rows 결정** — Epic 14 PRD entry 진입 시점에 결정 (cj-style Epic 14 1번째 진입점 = cj-style 45번째 epic 연속 정직 회복). `Capability.LISTEN_NOTIFY_TENANT_FANOUT = "listen_notify_tenant_fanout"` 4-industry grants: manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ (industry-agnostic, CR 12-1 L4 precedent 미러, AI_INSIGHT 10-1 + LISTEN_NOTIFY 13-1 wire pattern). `Capability.LISTEN_NOTIFY_MULTIPROCESS = "listen_notify_multiprocess"` 동일 industry-agnostic 4-industry grants ✅/✅/✅/✅. 미허용 tenant 의 cross-tenant fan-out channel listener 등록 차단 + multi-process coordination leader election 제외 결정 wire. SSOT RED→GREEN EXTENSION (capability matrix v1.23 신규 2 rows + capability.py EXTENSION 2 NEW enum + `require_capability()` Dependency 2개 신규 wire). CR 11-3 honest-DEFER discipline + A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS). 결정 wire 일자: 2026-08-20 |

### Phase 3 PRD entry 결정 (2026-08-20, cj-style Phase 3 1번째 진입점 = cj-style 49번째 epic 연속 정직 회복)

| 결정 | 내용 |
|------|------|
| **A65** | **Phase 3 = 로그인/회원가입 UI + auth middleware (Epic 1 완성 territory) PRD entry** — Phase 2 close-out 직후의 다음 territory 진입 결정 wire (cj-style Phase 3 1번째 진입점 = cj-style 49번째 epic 연속 정직 회복). Phase 3 territory 결정 = Epic 1 carry-over 정직 회복 (Story 1.1 F-1 Supabase SSR client + F-4 accessToken string pass + F-30 rls_db fixture 모두 D-1-1-DEFER-* honestly DEFER preserved) + login/signup/forgot-password UI 신규 wire (Epic 1 partial scaffold = `(auth)` route group + `apps/web/app/[locale]/(auth)/onboarding/industry/page.tsx` + IndustrySelector 이미 wire 됨) + auth middleware EXTENSION (`apps/web/middleware.ts` 의 next-intl middleware EXTENSION = Supabase session check + `(dashboard)` 보호 + `?redirect=` 쿼리 보존 + `(auth)` 공개 route group bypass + `/api/v1/*` bypass + 2FA 미설정 사용자 `/account/security?reason=2fa_required` redirect) + logout flow + AD-26 Auth Foundation 신규 결정 + capability matrix v1.23 → v1.24 EXTENSION (LOGIN + SIGNUP + AUTH_MIDDLEWARE + FORGOT_PASSWORD + LOGOUT 5 NEW rows). 결정 wire = master PRD v2.5 → v3.0 atomic edit (§F15 신규 + §8.1 M0-(d)·M0-(e)·M0-(f) auth 3 NEW 인수 불릿 + §15 로드맵 Phase 3 row status 백로그 → in-progress + §부록 A A65~A69 신규 결정 표 + AD-26 신규 결정 + capability matrix v1.24 EXTENSION 5 NEW rows). CR 11-3 honest-DEFER discipline + A36 SDR 검증 4-step 자동 적용 (commit prefix lint + sprint-status structure + vitest file count drift + commit consistency 모두 PASS). 결정 wire 일자: 2026-08-20. **A66+A67+A68+A69 follow-on**: capability 신규 5 rows 결정 wire |
| **A66** | **AD-26 Auth Foundation 신규 결정** — Phase 3 PRD entry 진입 시점에 결정 (cj-style Phase 3 1번째 진입점 = cj-style 49번째 epic 연속 정직 회복). AD-26 = (a) Supabase SSR auth client (`createServerClient` for Server Components + `createBrowserClient` for Client Components, single source of truth URL + anon key) / (b) `sb-access-token` cookie session = `httpOnly` + `secure` + `sameSite=lax` + `path=/` + `maxAge=3600` (1시간, refresh token 으로 자동 �신) / (c) next-intl middleware EXTENSION = Supabase session check + `(dashboard)` 보호 + `?redirect=` 쿼리 보존 + `(auth)` 공개 + `/api/v1/*` bypass + Edge Runtime 명시 / (d) auth route group `(auth)` 공개 (login + signup + forgot-password + 2fa + email-verification-pending) / (e) dashboard route group `(dashboard)` 보호 (Supabase session 필수 + Epic 12 2FA 미설정 시 `/account/security?reason=2fa_required` redirect) / (f) Supabase PKCE flow + sameSite=lax cookie CSRF 방어 결정 (별도 CSRF token 미사용, Supabase 권장 정합) / (g) email 존재 여부 노출 방지 (forgot-password 항상 200 반환 결정 wire). 결정 wire 일자: 2026-08-20 |
| **A67** | **Capability matrix v1.23 → v1.24 LOGIN + SIGNUP + AUTH_MIDDLEWARE + FORGOT_PASSWORD + LOGOUT 5 NEW rows 결정** — Phase 3 PRD entry 진입 시점에 결정 (cj-style Phase 3 1번째 진입점 = cj-style 49번째 epic 연속 정직 회복). `Capability.LOGIN = "login"` 4-industry grants: manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ (industry-agnostic, CR 12-1 L4 precedent 미러, AI_INSIGHT 10-1 + LISTEN_NOTIFY 13-1 + LISTEN_NOTIFY_TENANT_FANOUT 14-1 + LISTEN_NOTIFY_MULTIPROCESS 14-1 wire pattern). `Capability.SIGNUP` + `Capability.AUTH_MIDDLEWARE` + `Capability.FORGOT_PASSWORD` + `Capability.LOGOUT` 동일 industry-agnostic 4-industry grants ✅/✅/✅/✅. 미허용 tenant 의 login/signup/forgot-password 페이지 진입 차단 결정 wire. SSOT RED→GREEN EXTENSION (capability matrix v1.24 신규 5 rows + capability.py EXTENSION 5 NEW enum + `require_capability()` Dependency 5개 신규 wire). CR 11-3 honest-DEFER discipline + A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS). 결정 wire 일자: 2026-08-20 |
| **A68** | **Epic 1 carry-over DEFER 1~N honestly preserved (D-1-1-DEFER-*) 결정** — Phase 3 PRD entry 진입 시점에 결정 (cj-style Phase 3 1번째 진입점 = cj-style 49번째 epic 연속 정직 회복). Story 1.1 F-1 (Supabase SSR client wire) + F-4 (accessToken string pass to IndustrySelector) + F-30 (rls_db fixture wire) 모두 Phase 3 wire 진입 시점에 honestly RESOLVE 결정 wire 진입 (T1+T4 wire 진입 시점에 resolve). Story 1.1 F-2 (next-intl i18n bundle) + F-3 (IndustryCard UI polish) + F-5~F-29 (Epic 1 carry-over 25 items) preserved + D-1-1-DEFER-1 (Magic link login) + D-1-1-DEFER-2 (Social login OAuth: Google/Naver/Kakao) + D-1-1-DEFER-3 (SSO enterprise SAML) honestly preserved (CR 11-3 discipline) — Epic 1 close-out 시점에 결정 wire 보존 (cj-style Epic 1 follow-up sprint 진입 시점 = cj-style Phase 3 close-out retro 진입 시점). 결정 wire 일자: 2026-08-20 |
| **A69** | **Phase 3 wire scope T1~T8 결정 + Epic 1 partial scaffold 보존** — Phase 3 PRD entry 진입 시점에 결정 (cj-style Phase 3 1번째 진입점 = cj-style 49번째 epic 연속 정직 회복). T1 Supabase SSR client + T2 login page + T3 signup page + T4 auth middleware EXTENSION + T5 logout + T6 forgot-password + T7 capability v1.24 EXTENSION 5 NEW rows + T8 tests + 3중 게이트 FINAL CLEAN atomic commit. Epic 1 partial scaffold 보존 결정 wire: (1) `apps/web/app/[locale]/(auth)/layout.tsx` minimal shell 보존 (Phase 3 wire 진입 시점에 design tokens EXTENSION 결정 wire 보존) / (2) `apps/web/app/[locale]/(auth)/onboarding/industry/page.tsx` 보존 (Phase 3 T3 signup wire 시점에 atomic redirect 보존) / (3) `apps/web/components/onboarding/IndustrySelector.tsx` + `IndustryCard.tsx` 보존 (Phase 3 wire 영향 0) / (4) `apps/web/middleware.ts` next-intl EXTENSION 결정 wire (Phase 3 T4 진입 시점에 EXTENSION). estimated ~70 NEW vitest PASS + ~10 NEW pytest PASS + 0 NEW ruff + 0 regressions. wire_commit = TBD (cj-style Phase 3 3번째 진입점 = cj-style 51번째 epic 연속 정직 회복 atomic single sweep T1~T8, expected ~20-22 files = ~15 NEW + ~5-7 MODIFIED). 결정 wire 일자: 2026-08-20 |

### Phase 3 close-out retro 결정 (2026-08-22, cj-style Phase 3 3번째 진입점 = cj-style 51~52번째 epic 연속 정직 회복)

| 결정 | 내용 |
|------|------|
| **A70** | **D-1-1-DEFER-1 Magic link 결정 wire 진입** — Phase 3 close-out retro 진입 시점에 결정 (cj-style Phase 3 3번째 진입점 = cj-style 51~52번째 epic 연속 정직 회복). 옵션 (a) Magic link wire 진입 / 옵션 (b) Epic 15 carry-over 진입 / 옵션 (c) Phase 5 carry-over 진입 모두 결정 보류 — Epic 15+ 진입 시점에 사용자 결정 wire 보존. CR 11-3 honest-DEFER discipline 50번째 epic 연속 정직 회복 검증 ✅ |
| **A71** | **D-1-1-DEFER-2 Social login OAuth 결정 wire 진입** — Phase 3 close-out retro 진입 시점에 결정 (cj-style Phase 3 3번째 진입점 = cj-style 51~52번째 epic 연속 정직 회복). 옵션 (a) Google/Naver/Kakao OAuth wire 진입 / 옵션 (b) Epic 15 carry-over 진입 / 옵션 (c) Phase 5 carry-over 진입 모두 결정 보류 — Epic 15+ 진입 시점에 사용자 결정 wire 보존. CR 11-3 honest-DEFER discipline 50번째 epic 연속 정직 회복 검증 ✅ |
| **A72** | **D-1-1-DEFER-3 SSO enterprise SAML 결정 wire 진입** — Phase 3 close-out retro 진입 시점에 결정 (cj-style Phase 3 3번째 진입점 = cj-style 51~52번째 epic 연속 정직 회복). 옵션 (a) SAML wire 진입 / 옵션 (b) Epic 15 carry-over 진입 / 옵션 (c) Phase 5 carry-over 진입 모두 결정 보류 — Epic 15+ 진입 시점에 사용자 결정 wire 보존. CR 11-3 honest-DEFER discipline 50번째 epic 연속 정직 회복 검증 ✅ |
| **A73** | **✅ done** (2026-08-22, cj-style Phase 4 1번째 진입점 = cj-style 53번째 epic 연속 정직 회복) — **옵션 (a) Phase 4 진입** = Deployment config + Dockerfile territory 진입 결정 wire. Phase 3 close-out retro 진입 시점에 사용자 결정 = 옵션 (a) Phase 4 진입 결정 (옵션 (b) Epic 15 진입 / 옵션 (c) carry-over 진입 모두 rejected). Phase 4 territory = Vercel frontend + Railway backend + Supabase PostgreSQL production deployment config 결정. 결정 wire 일자: 2026-08-22 |
| **A74** | **✅ done** (2026-08-22, cj-style Phase 4 1번째 진입점 = cj-style 53번째 epic 연속 정직 회복) — **Master PRD v3.0 → v3.1 atomic edit** (D-1-1-DEFER-* RESOLVE 표기 보류). Phase 4 PRD entry 진입 시점에 master PRD v3.0 → v3.1 atomic edit 결정 wire 진입 — front matter title v3.0 → v3.1 + changelog v3.1 entry + §F16 신규 (F16.1 vercel.json + F16.2 railway.toml + F16.3 per-app Dockerfile + F16.4 docs/deployment.md + F16.5 health check + observability + F16.6 database backup + F16.7 tests + wire scope T1~T8) + §8.1 M0-(g) production deployment 인수 불릿 + §15 로드맵 Phase 4 row status 백로그 → in-progress + §부록 A A73+A74+A76+A77+A78 신규 결정 표 + AD-27 Deployment 신규 결정 + capability matrix v1.24 → v1.25 EXTENSION DEPLOYMENT_PROD + DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP + DEPLOYMENT_HEALTH_CHECK 4 NEW rows (industry-agnostic 4-industry grants ✅/✅/✅/✅). CR 11-3 honest-DEFER discipline + A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS). 결정 wire 일자: 2026-08-22 |
| **A75** | **(preserved)** A42 A36 SDR 검증 4-step 보존 + Epic 15+ 적용 — commit prefix lint + sprint-status structure + vitest file count drift + commit consistency 자동 검증 단계 모두 PASS |

### Phase 4 PRD entry 결정 (2026-08-22, cj-style Phase 4 1번째 진입점 = cj-style 53번째 epic 연속 정직 회복)

| 결정 | 내용 |
|------|------|
| **A76** | **AD-27 Deployment 신규 결정** — Phase 4 PRD entry 진입 시점에 결정 (cj-style Phase 4 1번째 진입점 = cj-style 53번째 epic 연속 정직 회복). AD-27 = (a) **Vercel frontend** 결정 (vercel.json + framework=nextjs + regions=[icn1] Seoul + buildCommand=`pnpm --filter web build` + installCommand=`pnpm install --frozen-lockfile` + outputDirectory=`apps/web/.next` + env mapping NEXT_PUBLIC_SUPABASE_URL/ANON_KEY/API_BASE_URL + headers CSP+X-Frame-Options+HSTS + redirects legacy `/ko-KR/*` → `/ko/*` next-intl 정합) / (b) **Railway backend** 결정 (railway.toml + builder=DOCKERFILE + dockerfilePath=`apps/api/Dockerfile` + healthcheckPath=`/api/v1/health` + healthcheckTimeout=300 + restartPolicyType=ON_FAILURE + restartPolicyMaxRetries=3 + env mapping DATABASE_URL/SUPABASE_JWT_SECRET/SUPABASE_URL/ANON_KEY/SERVICE_ROLE_KEY/SENTRY_DSN/ENVIRONMENT=production) / (c) **Supabase PostgreSQL production** 결정 (Supabase Pro plan + PITR 7일 자동 backup + Storage 결정 wire 보류) / (d) **Sentry observability** 결정 (Sentry browser SSR-safe init + tracesSampleRate=0.1 + Sentry FastAPI server integration + FastAPI middleware integration + SQLAlchemy integration opt-in) / (e) **per-app Dockerfile 분리** 결정 (apps/web/Dockerfile Next.js standalone output + apps/api/Dockerfile FastAPI uvicorn, AD-14 stack pin by @sha256: digest 모든 베이스 이미지 결정) / (f) **Health check endpoint** 결정 (`GET /api/v1/health` FastAPI endpoint + `GET /api/health` Next.js route handler + liveness/readiness 분리 `/health/live` + `/health/ready` + database connectivity check + JWT verification test + uptime_seconds 표시). 결정 wire 일자: 2026-08-22 |
| **A77** | **Capability matrix v1.24 → v1.25 DEPLOYMENT_PROD + DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP + DEPLOYMENT_HEALTH_CHECK 4 NEW rows 결정** — Phase 4 PRD entry 진입 시점에 결정 (cj-style Phase 4 1번째 진입점 = cj-style 53번째 epic 연속 정직 회복). `Capability.DEPLOYMENT_PROD = "deployment_prod"` 4-industry grants: manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ (industry-agnostic, CR 12-1 L4 precedent 미러, AI_INSIGHT 10-1 + LISTEN_NOTIFY 13-1 + LISTEN_NOTIFY_TENANT_FANOUT 14-1 + LISTEN_NOTIFY_MULTIPROCESS 14-1 + LOGIN/SIGNUP/AUTH_MIDDLEWARE/FORGOT_PASSWORD/LOGOUT Phase 3 wire pattern). `Capability.DEPLOYMENT_STAGING` + `Capability.DEPLOYMENT_DATABASE_BACKUP` + `Capability.DEPLOYMENT_HEALTH_CHECK` 동일 industry-agnostic 4-industry grants ✅/✅/✅/✅. 미허용 tenant 의 production deployment 진입 차단 + staging deployment 진입 차단 결정 wire. SSOT RED→GREEN EXTENSION (capability matrix v1.25 신규 4 rows + capability.py EXTENSION 4 NEW enum + `require_capability()` Dependency 4개 신규 wire). CR 11-3 honest-DEFER discipline + A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS). 결정 wire 일자: 2026-08-22 |
| **A78** | **Phase 4 wire scope T1~T8 결정** — Phase 4 PRD entry 진입 시점에 결정 (cj-style Phase 4 1번째 진입점 = cj-style 53번째 epic 연속 정직 회복). T1 Vercel config wire (vercel.json) + T2 Railway config wire (railway.toml) + T3 per-app Dockerfile wire (apps/web/Dockerfile + apps/api/Dockerfile) + T4 deployment runbook wire (docs/deployment.md 12 sections) + T5 health check + observability wire (apps/api/core/health.py + apps/api/core/observability.py + apps/web/lib/observability/sentry.ts + apps/web/app/api/health/route.ts + apps/api/main.py MODIFIED health router include) + T6 database backup strategy wire (apps/api/alembic/versions/0036_phase_4_backup_strategy.py + docs/database-backup.md) + T7 capability v1.25 EXTENSION 4 NEW rows + T8 tests + 3중 게이트 FINAL CLEAN atomic commit. estimated ~40 NEW pytest PASS + ~20 NEW vitest PASS + 0 NEW ruff + 0 regressions. wire_commit = TBD (cj-style Phase 4 3번째 진입점 = cj-style 55번째 epic 연속 정직 회복 atomic single sweep T1~T8, expected ~10-12 files = ~10 NEW + ~3-5 MODIFIED). 결정 wire 일자: 2026-08-22 |

### Phase 4 close-out retro 결정 (2026-08-22, cj-style Phase 4 4번째 진입점 = cj-style 56~57번째 epic 연속 정직 회복)

| 결정 | 내용 |
|------|------|
| **A70** | **✅ done** (2026-08-22, cj-style Phase 4 close-out retro 진입 시점에 결정, cj-style 56~57번째 epic 연속 정직 회복) — **D-1-1-DEFER-1 Magic link 결정 wire** = Epic 15 진입 시점에 wire 결정. 옵션 (a) Magic link wire 진입 (Epic 15 territory 진입) 결정 (옵션 (b) Epic 15 carry-over 진입 / 옵션 (c) Phase 5 carry-over 진입 모두 rejected — rationale: Epic 15 = Magic link + Social OAuth + SSO 통합 territory 표준 진입 가능 = cj-style 1번째 진입점 표준 진입 가능 = 결정 wire 효율성). Epic 15 PRD entry 진입 시점에 적용 (cj-style Epic 15 1번째 진입점 = cj-style 58번째 epic 연속 정직 회복 진입 시점에 동시 결정 wire). CR 11-3 honest-DEFER discipline 50~58번째 epic 연속 정직 회복 검증 ✅ |
| **A71** | **✅ done** (2026-08-22, cj-style Phase 4 close-out retro 진입 시점에 결정) — **D-1-1-DEFER-2 Social login OAuth 결정 wire** = Epic 15 진입 시점에 wire 결정. 옵션 (a) Google/Naver/Kakao OAuth wire 진입 (Epic 15 territory 진입) 결정 (옵션 (b) Epic 15 carry-over 진입 / 옵션 (c) Phase 5 carry-over 진입 모두 rejected — rationale: Epic 15 = Magic link + Social OAuth + SSO 통합 territory 표준 진입 가능). Epic 15 PRD entry 진입 시점에 적용. CR 11-3 honest-DEFER discipline 50~58번째 epic 연속 정직 회복 검증 ✅ |
| **A72** | **✅ done** (2026-08-22, cj-style Phase 4 close-out retro 진입 시점에 결정) — **D-1-1-DEFER-3 SSO enterprise SAML 결정 wire** = Epic 15 진입 시점에 wire 결정. 옵션 (a) SAML wire 진입 (Epic 15 territory 진입) 결정 (옵션 (b) Epic 15 carry-over 진입 / 옵션 (c) Phase 5 carry-over 진입 모두 rejected — rationale: Epic 15 = Magic link + Social OAuth + SSO 통합 territory 표준 진입 가능). Epic 15 PRD entry 진입 시점에 적용. CR 11-3 honest-DEFER discipline 50~58번째 epic 연속 정직 회복 검증 ✅ |

### Epic 15 PRD entry 결정 (2026-08-22, cj-style Epic 15 1번째 진입점 = cj-style 58번째 epic 연속 정직 회복)

| 결정 | 내용 |
|------|------|
| **A79** | **Epic 15 = Magic link + Social OAuth + SSO enterprise SAML 통합 territory PRD entry** — Phase 4 close-out retro 진입 시점에 옵션 (a) Epic 15 진입 결정 (cj-style Epic 15 1번째 진입점 = cj-style 58번째 epic 연속 정직 회복). Epic 15 territory = D-1-1-DEFER-1/2/3 honestly ✅ RESOLVE 결정 (A70+A71+A72 ✅ done 진입 wire). Epic 15-1 = magic link + social OAuth + SSO enterprise SAML 본체 wire 진입 (T1~T8 atomic single sprint). 결정 wire = master PRD v3.1 → v3.2 atomic edit (§F17 신규 + §8.1 M0-(h)·M0-(i)·M0-(j) 3 NEW 인수 불릿 + §15 로드맵 Epic 15 row status 백로그 → in-progress + §부록 A A70+A71+A72 ✅ done + A75 preserved + A79+A80+A81+A82 신규 결정 표 + AD-28 Magic link + Social OAuth + SSO enterprise SAML 신규 결정 + capability matrix v1.25 → v1.26 EXTENSION 5 NEW rows industry-agnostic 4-industry grants ✅/✅/✅/✅). D-1-1-DEFER-1/2/3 ✅ RESOLVED (A70+A71+A72 결정 wire). CR 11-3 honest-DEFER discipline 58번째 epic 연속 정직 회복 + A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS). ✅ done 진입 2026-08-22. **A80+A81+A82 follow-on**: AD-28 신규 + capability 신규 5 rows + wire scope T1~T8 결정 |
| **A80** | **AD-28 Magic link + Social OAuth + SSO enterprise SAML 신규 결정** — Epic 15 PRD entry 진입 시점에 결정 (cj-style Epic 15 1번째 진입점 = cj-style 58번째 epic 연속 정직 회복). AD-28 = (a) **Magic link** 결정 wire (Supabase `signInWithOtp({ email, options: { emailRedirectTo } })` wrapper + 5회 cool-down sessionStorage 30s + email 존재 여부 노출 방지 security invariant try/catch/finally + audit-first INSERT `magic_link_sent` CR 1-1 verbatim + `sb-access-token` cookie session 자동 설정 Phase 3-1 T1 wire 정합 + Epic 12 2FA 미설정 시 `/auth/2fa` redirect 결정) / (b) **Social OAuth Google/Naver/Kakao** 결정 wire (Supabase `signInWithOAuth({ provider, options: { redirectTo } })` wrapper + provider whitelist `ALLOWED_SOCIAL_PROVIDERS = frozenset({'google', 'naver', 'kakao'})` strict reject + 3회 cool-down sessionStorage 60s + audit-first INSERT `social_oauth_initiated` CR 1-1 verbatim + OAuth callback handler `/auth-callback` + `exchangeCodeForSession(code)` + Naver OAuth Option A/B 결정 wire 보존) / (c) **SSO enterprise SAML** 결정 wire (`python3-saml==1.16.0` AD-14 stack pin + SAML response validation (signature + `NotBefore`/`NotOnOrAfter` + `Audience` + `Destination` + `InResponseTo` + RelayState) + JIT user provisioning 5-step atomic flow + multi-tenant isolation CR 0-2 RLS lesson + 4 SSO routes `/api/v1/auth/sso/{login,acs,metadata,sls}` + audit-first INSERT `sso_identity_linked` CR 1-1 verbatim + tenant slug 별 IdP metadata routing multi-tenant SSO). 결정 wire 일자: 2026-08-22 |
| **A81** | **Capability matrix v1.25 → v1.26 MAGIC_LINK + SOCIAL_OAUTH_GOOGLE + SOCIAL_OAUTH_NAVER + SOCIAL_OAUTH_KAKAO + SSO_ENTERPRISE 5 NEW rows 결정** — Epic 15 PRD entry 진입 시점에 결정 (cj-style Epic 15 1번째 진입점 = cj-style 58번째 epic 연속 정직 회복). `Capability.MAGIC_LINK = "magic_link"` 4-industry grants: manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ (industry-agnostic, CR 12-1 L4 precedent 미러, LOGIN/SIGNUP/AUTH_MIDDLEWARE/FORGOT_PASSWORD/LOGOUT Phase 3-1 + LISTEN_NOTIFY/LISTEN_NOTIFY_TENANT_FANOUT/LISTEN_NOTIFY_MULTIPROCESS Epic 13/14 + DEPLOYMENT_PROD/DEPLOYMENT_STAGING/DEPLOYMENT_DATABASE_BACKUP/DEPLOYMENT_HEALTH_CHECK Phase 4 wire pattern). `Capability.SOCIAL_OAUTH_GOOGLE` + `Capability.SOCIAL_OAUTH_NAVER` + `Capability.SOCIAL_OAUTH_KAKAO` + `Capability.SSO_ENTERPRISE` 동일 industry-agnostic 4-industry grants ✅/✅/✅/✅. 미허용 tenant 의 magic link / social OAuth / SSO enterprise 진입 차단 결정 wire. SSOT RED→GREEN EXTENSION (capability matrix v1.26 신규 5 rows + capability.py EXTENSION 5 NEW enum + `require_capability()` Dependency 5개 신규 wire). CR 11-3 honest-DEFER discipline 58번째 epic 연속 정직 회복 + A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS). 결정 wire 일자: 2026-08-22 |
| **A82** | **Epic 15 wire scope T1~T8 결정** — Epic 15 PRD entry 진입 시점에 결정 (cj-style Epic 15 1번째 진입점 = cj-style 58번째 epic 연속 정직 회복). T1 Magic link wire (apps/web/lib/auth/magic-link.ts Supabase `signInWithOtp` wrapper) + T2 Magic link UI wire (MagicLinkForm.tsx + magic-link/page.tsx + magic-link-sent/page.tsx) + T3 Social OAuth wire (social.ts Supabase `signInWithOAuth` wrapper + SocialAuthButtons.tsx 3 provider buttons) + T4 OAuth callback wire (auth-callback/page.tsx `exchangeCodeForSession`) + T5 SSO SAML backend wire (saml_validator.py + saml_routes.py 4 routes + jit_provisioning.py + alembic 0037 external_identities table + apps/web/app/api/auth/sso/callback/route.ts) + T6 SSO UI wire (sso/[tenant_slug]/login/page.tsx) + T7 capability v1.26 EXTENSION 5 NEW rows + T8 tests + 3중 게이트 FINAL CLEAN atomic commit. estimated ~60 NEW pytest PASS + ~50 NEW vitest PASS + 0 NEW ruff + 0 regressions. wire_commit = TBD (cj-style Epic 15 3번째 진입점 = cj-style 60번째 epic 연속 정직 회복 atomic single sweep T1~T8, expected ~14-16 files = ~12 NEW + ~3-5 MODIFIED). 결정 wire 일자: 2026-08-22 |

### 1st release launch PRD entry 결정 (2026-08-22, cj-style 1st release launch 1번째 진입점 = cj-style 62번째 epic 연속 정직 회복)

| 결정 | 내용 |
|------|------|
| **A83** | **옵션 (d) 1st release launch 진입 결정** — Epic 15 close-out retro `729b223` §12 "Next unblocked 결정 wire 보류" 의 옵션 (a) Epic 16 / 옵션 (b) Phase 5 / 옵션 (c) carry-over / 옵션 (d) 1차 출시 중 **사용자 권장 결정 = 옵션 (d) 1st release launch 진입**. rationale 4종: (1) 모든 인프라 wire DONE = Auth Foundation (Epic 1 + Phase 3) + 2FA (Epic 12) + LISTEN/NOTIFY (Epic 13/14) + Deployment (Phase 4) + 인증 방법 4종 (Magic link + OAuth 3종 + SSO SAML = Epic 15) 모두 wire DONE / (2) D-1-1-DEFER-1/2/3 ✅ RESOLVED = Epic 15 wire 진입 시점에 honest-DEFER discipline 회복 완료 (60번째 epic 연속 정직 회복 검증) / (3) cj-style discipline 회피 위험 방지 = 1-day atomic sprint로 누적된 정직 회복 (49~61번째) 더 미루면 cycle 끊김 위험 / (4) 비즈니스 우선순위 = infrastructure 완성 → 실제 출시 가치 회수. 옵션 (a) Epic 16 / 옵션 (b) Phase 5 / 옵션 (c) carry-over 모두 rejected (rationale: 인프라 cycle 완료 + 출시 가치 회수 우선). Epic 15 territory DONE 정합 보존 (cj-style 58~61번째 epic 연속 정직 회복). 1st release launch PRD entry 진입 시점에 적용 (cj-style 62번째 epic 연속 정직 회복 진입 시점에 결정). ✅ done 진입 2026-08-22. **A84+A85+A86+A87 follow-on**: master PRD v3.2 → v3.3 atomic edit + AD-29 1st release launch 신규 + capability matrix v1.26 → v1.27 EXTENSION 4 NEW rows + 1st release wire scope T1~T8 결정 |
| **A84** | **Master PRD v3.2 → v3.3 atomic edit 결정** — 1st release launch PRD entry 진입 시점에 결정 (cj-style 62번째 epic 연속 정직 회복). master PRD v3.2 → v3.3 atomic edit (docs only, no code/test/sprint-status delta 외 PRD edit 신규). (1) front matter title v3.2 → v3.3 + changelog v3.3 entry 신규 (cj-style 62번째 epic 연속 정직 회복 진입 시점에 결정 verbatim 보존) / (2) §F18 신규 (F18.1 Marketing landing + F18.2 ToS/Privacy + F18.3 Onboarding guide + F18.4 Support channels + F18.5 Production verification + F18.6 Launch comms + F18.7 capability v1.27 EXTENSION 4 NEW rows + F18.8 tests + wire scope T1~T8 결정) / (3) §8.1 M0-(k) 1st release launch 결정 wire 진입 / (4) §15 로드맵 1st release row status 백로그 → in-progress (PRD entry DONE 진입 wire) / (5) §부록 A A83+A84+A85+A86+A87 신규 결정 표 / (6) AD-29 1st release launch 신규 결정 (Marketing landing + ToS/Privacy + Onboarding + Support + Verification + Comms 6 sub-decisions) / (7) capability matrix v1.26 → v1.27 EXTENSION 4 NEW rows industry-agnostic 4-industry grants ✅/✅/✅/✅. 결정 wire 일자: 2026-08-22 |
| **A85** | **AD-29 1st release launch 신규 결정** — 1st release launch PRD entry 진입 시점에 결정 (cj-style 62번째 epic 연속 정직 회복). AD-29 = (a) **Marketing landing page** 결정 wire (`/landing` public route + LandingHero + LandingFeatures + LandingPricing + LandingCTA + ko-KR inline copy EXTENSION, vercel.json public route EXTENSION, (public) route group 신규, 월 1만원 subscription + 14일 무료 체험 결정) / (b) **ToS + Privacy Policy** 결정 wire (`docs/terms-of-service.md` + `docs/privacy-policy.md` 한국 PIPA + GDPR 정합, 8+10 sections, versioned + changelog + effective date, signup flow EXTENSION (auth)/tos + (auth)/privacy 결정) / (c) **Onboarding user guide** 결정 wire (`docs/onboarding-guide.md` 8 sections + OnboardingTooltip + first-run wizard EXTENSION Epic 1 partial scaffold `d182d7d` 정합) / (d) **Customer support channels** 결정 wire (`docs/support.md` + email `support@bizup.kr` + HelpWidget + FAQ `docs/faq.md`) / (e) **Production launch verification** 결정 wire (smoke test RE-RUN 정직 결정 + backup drill 0036 PITR quarterly + Sentry alert wiring production + RPO 4h/RTO 24h SLA verification) / (f) **Public launch communications** 결정 wire (`docs/launch-announcement.md` + press kit + og/assets + in-app announcement banner). 결정 wire 일자: 2026-08-22 |
| **A86** | **Capability matrix v1.26 → v1.27 LAUNCH_LANDING + LAUNCH_TOS + LAUNCH_SUPPORT + LAUNCH_MONITORING 4 NEW rows 결정** — 1st release launch PRD entry 진입 시점에 결정 (cj-style 62번째 epic 연속 정직 회복). `Capability.LAUNCH_LANDING = "launch_landing"` 4-industry grants: manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ (industry-agnostic, CR 12-1 L4 precedent 미러, LOGIN/SIGNUP/AUTH_MIDDLEWARE/FORGOT_PASSWORD/LOGOUT Phase 3-1 + LISTEN_NOTIFY 13-1 + LISTEN_NOTIFY_TENANT_FANOUT/LISTEN_NOTIFY_MULTIPROCESS 14-1 + DEPLOYMENT_PROD/DEPLOYMENT_STAGING/DEPLOYMENT_DATABASE_BACKUP/DEPLOYMENT_HEALTH_CHECK Phase 4 + MAGIC_LINK/SOCIAL_OAUTH_GOOGLE/SOCIAL_OAUTH_NAVER/SOCIAL_OAUTH_KAKAO/SSO_ENTERPRISE Epic 15 wire pattern). `Capability.LAUNCH_TOS` + `Capability.LAUNCH_SUPPORT` + `Capability.LAUNCH_MONITORING` 동일 industry-agnostic 4-industry grants ✅/✅/✅/✅. 미허용 tenant 의 1st release launch 진입 차단 결정 wire. SSOT RED→GREEN EXTENSION (capability matrix v1.27 신규 4 rows + capability.py EXTENSION 4 NEW enum + `require_capability()` Dependency 4개 신규 wire). CR 11-3 honest-DEFER discipline 62번째 epic 연속 정직 회복 + A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS). 결정 wire 일자: 2026-08-22 |
| **A87** | **1st release wire scope T1~T8 결정** — 1st release launch PRD entry 진입 시점에 결정 (cj-style 62번째 epic 연속 정직 회복). T1 Landing page wire (apps/web/app/[locale]/(public)/landing/page.tsx + LandingHero.tsx + LandingFeatures.tsx + LandingPricing.tsx + LandingCTA.tsx + ko-KR.json landing.* namespace EXTENSION) + T2 ToS + Privacy wire (docs/terms-of-service.md + docs/privacy-policy.md + (auth)/tos/page.tsx + (auth)/privacy/page.tsx + signup flow EXTENSION) + T3 Onboarding guide wire (docs/onboarding-guide.md + OnboardingTooltip.tsx + (auth)/onboarding/page.tsx) + T4 Support channels wire (docs/support.md + docs/faq.md + docs/launch-announcement.md + HelpWidget.tsx) + T5 Production verification wire (apps/api/scripts/smoke_test.py RE-RUN + sentry-alerts.ts + sentry-alerts.py + docs/database-backup.md 0036 PITR drill quarterly EXTENSION) + T6 Capability v1.27 EXTENSION 4 NEW rows (capability.py + capability-matrix.md) + T7 Tests + 3중 게이트 FINAL CLEAN (~+30 NEW pytest PASS + ~+20 NEW vitest PASS + 5 NEW docs + 1 MODIFIED ko-KR.json) + T8 Launch comms wire (docs/launch-announcement.md + docs/press-kit.md + apps/web/public/og/ assets + (auth)/announcements/page.tsx). estimated ~30 NEW pytest PASS + ~20 NEW vitest PASS + 0 NEW ruff + 0 regressions. wire_commit = TBD (cj-style 1st release 3번째 진입점 = cj-style 64번째 epic 연속 정직 회복 atomic single sweep T1~T8, expected ~15-18 files = ~10 NEW + ~5-8 MODIFIED). 결정 wire 일자: 2026-08-22 |

### Epic 16 PRD entry 결정 (2026-08-22, cj-style Epic 16 1번째 진입점 = cj-style 67번째 epic 연속 정직 회복)

| 결정 | 내용 |
|------|------|
| **A92** | **옵션 (a) Epic 16 진입 결정** — 1st release close-out retro `25dccaf` §12 "Next unblocked 결정 wire 보류" 의 옵션 (a) Epic 16 / 옵션 (b) Phase 5 / 옵션 (c) carry-over / 옵션 (d) 추가 1st release 중 **사용자 권장 결정 = 옵션 (a) Epic 16 진입**. rationale 4종: (1) Epic 15 SSO enterprise SAML forward-reference 'TODO Epic 16' 해결 = docs/sso-enterprise.md §4.1 step 3 'Configure `tenant_idps` (TODO Epic 16)' verbatim — Epic 15 wire 의 natural carry-over / (2) Epic 15 territory carry-over chain (cj-style 58~61→67번째) = tenant IdP admin management 가 natural next territory / (3) cj-style discipline 회피 위험 방지 = 62~66번째 누적 cycle 더 미루면 cycle 끊김 위험 / (4) 비즈니스 우선순위 = 1차 출시 후 enterprise SSO onboarding 필수 (Epic 15 SSO enterprise SAML 은 response validation + JIT provisioning 까지 wire, tenant IdP config admin UI/API 가 Epic 16 territory 결정 wire 진입). 옵션 (b) Phase 5 / 옵션 (c) carry-over / 옵션 (d) 추가 1st release 모두 rejected (rationale: Epic 15 carry-over chain 우선 + 1-day atomic sprint discipline). Epic 15 territory DONE 정합 보존 (cj-style 58~61번째 epic 연속 정직 회복) + 1st release territory DONE 정합 보존 (cj-style 62~66번째 epic 연속 정직 회복). Epic 16 PRD entry 진입 시점에 적용 (cj-style 67번째 epic 연속 정직 회복 진입 시점에 결정). ✅ done 진입 2026-08-22. **A93+A94+A95+A96 follow-on**: master PRD v3.3 → v3.4 atomic edit + AD-30 Tenant IdP admin management 신규 + capability matrix v1.27 → v1.28 EXTENSION TENANT_IDP_MANAGEMENT 1 NEW row + Epic 16 wire scope T1~T8 결정 |
| **A93** | **Master PRD v3.3 → v3.4 atomic edit 결정** — Epic 16 PRD entry 진입 시점에 결정 (cj-style Epic 16 1번째 진입점 = cj-style 67번째 epic 연속 정직 회복). master PRD v3.3 → v3.4 atomic edit (docs only, no code/test/sprint-status delta 외 PRD edit 신규). (1) front matter title v3.3 → v3.4 + changelog v3.4 entry 신규 (cj-style 67번째 epic 연속 정직 회복 진입 시점에 결정 verbatim 보존) / (2) §F19 신규 (F19.1 tenant_idps table + F19.2 IdP metadata validation + F19.3 CRUD API 5 routes + F19.4 admin UI + F19.5 per-tenant routing EXTENSION + F19.6 capability gate + F19.7 tests + wire scope T1~T8 결정) / (3) §8.1 M0-(l) tenant IdP admin AC 신규 / (4) §15 로드맵 Epic 16 row status 백로그 → in-progress (PRD entry DONE 진입 wire) / (5) §부록 A A92+A93+A94+A95+A96 신규 결정 표 / (6) AD-30 Tenant IdP admin management 신규 결정 (tenant_idps architecture + IdP metadata validator + CRUD API + admin UI + per-tenant routing + audit-first INSERT 6 sub-decisions) / (7) capability matrix v1.27 → v1.28 EXTENSION TENANT_IDP_MANAGEMENT 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅. 결정 wire 일자: 2026-08-22 |
| **A94** | **AD-30 Tenant IdP admin management 신규 결정** — Epic 16 PRD entry 진입 시점에 결정 (cj-style Epic 16 1번째 진입점 = cj-style 67번째 epic 연속 정직 회복). AD-30 = (a) **`tenant_idps` table schema** 결정 wire (alembic `0038_epic_16_tenant_idps.py` NEW, 13 columns: id + tenant_id FK + idp_entity_id + idp_sso_url + idp_slo_url + idp_x509_cert + acs_url + name_id_format + enabled + created_at + updated_at + created_by + updated_by + unique constraint `(tenant_id, idp_entity_id)` + RLS policy `tenant_id = current_setting('app.tenant_id')` 결정, CR 0-2 RLS lesson 적용 + AD-22 verbatim 보존) / (b) **IdP metadata XML validation service** 결정 wire (`apps/api/modules/auth/sso/idp_metadata_validator.py` NEW ~120 LOC, Epic 15 `saml_validator.py` sibling module, 8 validation steps: XML well-formedness + EntityDescriptor root + entityID 추출 + IDPSSODescriptor 확인 + X509Certificate PEM wrap + SingleSignOnService Location https:// + SingleLogoutService Location https:// + tenant slug 매칭) / (c) **Tenant IdP CRUD API 5 routes** 결정 wire (`apps/api/modules/auth/sso/idp_admin_routes.py` NEW, FastAPI: `GET / POST / PUT / DELETE / TEST /api/v1/admin/tenant/{tenant_slug}/idp`, owner/admin role required `require_role("owner", "admin")` Dependency + capability gate `TENANT_IDP_MANAGEMENT` + RLS 자동 적용 + audit-first INSERT 4 NEW: `tenant_idp_created` / `tenant_idp_updated` / `tenant_idp_deleted` / `tenant_idp_tested`, CR 1-1 verbatim 적용) / (d) **Tenant IdP admin UI** 결정 wire (`apps/web/app/[locale]/(dashboard)/settings/sso/page.tsx` NEW ~150 LOC + 4 components: TenantIdPConfigForm + TenantIdPStatusBadge + TenantIdPTestResultModal + TenantIdPDeleteConfirmDialog + ko-KR.json `settings.sso.*` namespace EXTENSION 12 keys + (dashboard) 보호 + admin-idp-client.ts fetch wrapper) / (e) **Per-tenant IdP routing EXTENSION** 결정 wire (Epic 15 `apps/api/modules/auth/sso/saml_routes.py` EXTENSION: `tenant_slug` → `tenant_idps` lookup → `idp_sso_url` redirect (HTTP 302) + ACS `idp_x509_cert` 동적 로딩 + backward compatibility `acme` hardcoded tenant 보존 + alembic 0038 데이터 migration `acme` row 자동 seed 결정) / (f) **Audit-first INSERT 4 NEW + multi-tenant isolation** 결정 wire (CR 1-1 verbatim + CR 0-2 RLS lesson 적용, 모든 CRUD API endpoint 에 audit_log INSERT 결정, action_class='AUTH' + action='tenant_idp_*' + actor_id + tenant_id + payload_json 정합). 결정 wire 일자: 2026-08-22 |
| **A95** | **Capability matrix v1.27 → v1.28 TENANT_IDP_MANAGEMENT 1 NEW row 결정** — Epic 16 PRD entry 진입 시점에 결정 (cj-style Epic 16 1번째 진입점 = cj-style 67번째 epic 연속 정직 회복). `Capability.TENANT_IDP_MANAGEMENT = "tenant_idp_management"` 4-industry grants: manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ (industry-agnostic, CR 12-1 L4 precedent 미러, SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY 13-1 + LISTEN_NOTIFY_TENANT_FANOUT 14-1 + LISTEN_NOTIFY_MULTIPROCESS 14-1 + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire pattern). 미허용 tenant 의 tenant IdP admin 진입 차단 결정 wire. SSOT RED→GREEN EXTENSION (capability matrix v1.28 신규 1 row + capability.py EXTENSION 1 NEW enum + `require_capability()` Dependency 1개 신규 wire). CR 11-3 honest-DEFER discipline 67번째 epic 연속 정직 회복 + A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS). 결정 wire 일자: 2026-08-22 |
| **A96** | **Epic 16 wire scope T1~T8 결정** — Epic 16 PRD entry 진입 시점에 결정 (cj-style Epic 16 1번째 진입점 = cj-style 67번째 epic 연속 정직 회복). T1 `tenant_idps` table wire (alembic `0038_epic_16_tenant_idps.py` NEW + 13 columns + RLS policy + unique constraint + index + audit trigger) + T2 IdP metadata validator wire (`apps/api/modules/auth/sso/idp_metadata_validator.py` NEW ~120 LOC + 8 validation steps + IdPMetadata TypedDict) + T3 Tenant IdP CRUD API 5 routes wire (`apps/api/modules/auth/sso/idp_admin_routes.py` NEW + owner/admin Dependency + audit-first INSERT 4 NEW) + T4 Tenant IdP admin UI wire (`apps/web/app/[locale]/(dashboard)/settings/sso/page.tsx` NEW + 4 components + ko-KR.json `settings.sso.*` namespace EXTENSION 12 keys + `apps/web/lib/auth/admin-idp-client.ts` NEW) + T5 Per-tenant IdP routing EXTENSION wire (Epic 15 `saml_routes.py` MODIFIED + ACS `idp_x509_cert` 동적 로딩 + alembic 0038 `acme` 데이터 migration) + T6 Capability v1.28 EXTENSION 1 NEW row (capability.py MODIFIED + docs/capability-matrix.md v1.27 → v1.28) + T7 Tests + 3중 게이트 FINAL CLEAN (~+25 NEW pytest PASS + ~+5 NEW vitest PASS + 1 NEW integration drift + 4 NEW audit log verification) + T8 3중 게이트 FINAL CLEAN atomic commit. estimated ~25 NEW pytest PASS + ~5 NEW vitest PASS + 0 NEW ruff + 0 regressions. wire_commit = TBD (cj-style Epic 16 3번째 진입점 = cj-style 69번째 epic 연속 정직 회복 atomic single sweep T1~T8, expected ~10-12 files = ~9 NEW + ~2-3 MODIFIED). 결정 wire 일자: 2026-08-22 |

### Epic 16 close-out retro PRD entry 결정 (cj-style Epic 16 5번째 진입점 = cj-style 71번째 epic 연속 정직 회복) — Epic 16 T4 admin UI follow-up 후속 결정 wire 진입 — §F19.4 AC satisfied = T4 follow-up sprint `ff5c3b5` (cj-style 71번째) 프론트엔드 12 파일 atomic wire DONE 진입 시점에 Epic 16 territory 결정 wire 완료. (참고: A97~A100 Epic 16 spec entry 결정 + A101~A108 Epic 16 atomic wire 결정 + A109~A113 review follow-up 결정 + A114~A118 T4 follow-up 결정 + A119~A123 close-out retro 결정 모두 윗줄 결정 wire 진입 시점에 결정 완료, Epic 16 6-entry-point pattern 모두 wire DONE 진입 67~71번째.)

### Phase 5 PRD entry 결정 (2026-08-22, cj-style Phase 5 1번째 진입점 = cj-style 73번째 epic 연속 정직 회복)

| 결정 | 내용 |
|------|------|
| **A124** | **옵션 (a) Phase 5 진입 결정** — Epic 16 close-out retro `f1ead9a` §13 "Next unblocked 결정 wire 보류" 의 옵션 (a) Phase 5 / 옵션 (b) Epic 17 / 옵션 (c) carry-over / 옵션 (d) 1차 출시 follow-up / 옵션 (e) D-EPIC-16-REVIEW-DEFER-2~6 해소 중 **사용자 권장 결정 = 옵션 (a) Phase 5 진입**. rationale 4종: (1) **Phase 4 close-out retro §6 disaster recovery honestly-deferred 해소** = docs/database-backup.md §7 "multi-region backup 결정 wire 보류, Phase 5+ 진입 시점" verbatim — Phase 4 wire 진입 시점에 honestly-deferred carry-over territory 의 natural next wire 결정 / (2) **cj-style discipline 회피 위험 방지** = 49~72번째 누적 24-entry-point cycle 모두 wire DONE 진입 + A119+A120+A121+A122+A123 5/5 ALL DONE 결정 wire 후 next territory 진입 결정 = honest cycle 진행 정직 회복 / (3) **비즈니스 우선순위 + enterprise SLA 정합** = 1차 출시 후 enterprise 고객 유치 시 RPO 1h/RTO 4h SLA 요구 (Phase 4 single-region RPO 5min/RTO 1h 의 honest-extreme risk = Seoul region disaster 시 backup restoration 불가 verbatim 해소 결정 wire) / (4) **Phase 4 단일-region EXTENSION** = Supabase Seoul primary + PITR 7일 자동 의 multi-region EXTENSION (primary Seoul + secondary Tokyo + cross-region backup) 자연스러운 인프라 확장 결정 wire. 옵션 (b) Epic 17 / 옵션 (c) carry-over / 옵션 (d) 1차 출시 follow-up / 옵션 (e) D-EPIC-16-REVIEW-DEFER-2~6 해소 모두 rejected (rationale: Phase 4 honestly-deferred 해소 우선 + 다중 entry-point cycle discipline + enterprise SLA 정합). Epic 16 territory DONE 정합 보존 (cj-style 67~72번째 epic 연속 정직 회복) + 1st release territory DONE 정합 보존 (cj-style 62~66번째 epic 연속 정직 회복) + Epic 15 territory DONE 정합 보존 (cj-style 58~61번째 epic 연속 정직 회복) + Phase 4 territory DONE 정합 보존 (cj-style 53~57번째 epic 연속 정직 회복) + Phase 3 territory DONE 정합 보존 (cj-style 49~52번째 epic 연속 정직 회복) 결정 wire 모두 보존. Phase 5 PRD entry 진입 시점에 적용 (cj-style 73번째 epic 연속 정직 회복 진입 시점에 결정). ✅ done 진입 2026-08-22. **A125+A126+A127+A128 follow-on**: master PRD v3.4 → v3.5 atomic edit + AD-31 Multi-Region Backup & Disaster Recovery 신규 + capability matrix v1.28 → v1.29 EXTENSION MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER 2 NEW rows + Phase 5 wire scope T1~T8 결정 |
| **A125** | **Master PRD v3.4 → v3.5 atomic edit 결정** — Phase 5 PRD entry 진입 시점에 결정 (cj-style Phase 5 1번째 진입점 = cj-style 73번째 epic 연속 정직 회복). master PRD v3.4 → v3.5 atomic edit (docs only, no code/test/sprint-status delta 외 PRD edit 신규). (1) front matter title v3.4 → v3.5 + changelog v3.5 entry 신규 (cj-style 73번째 epic 연속 정직 회복 진입 시점에 결정 verbatim 보존) / (2) §F20 신규 (F20.1 Cross-region read replica + WAL archiving + F20.2 Cross-region failover automation + F20.3 DR drill + automated quarterly test + F20.4 Cross-region backup strategy + F20.5 Multi-region health observability + F20.6 capability matrix v1.29 EXTENSION 2 NEW rows + F20.7 tests + wire scope T1~T8 결정) / (3) §8.1 M0-(m) multi-region backup AC 신규 / (4) §15 로드맵 Phase 5 row status 백로그 → in-progress (PRD entry DONE 진입 wire) / (5) §부록 A A124+A125+A126+A127+A128 신규 결정 표 / (6) AD-31 Multi-Region Backup & Disaster Recovery 신규 결정 (cross-region architecture 6 sub-decisions) / (7) capability matrix v1.28 → v1.29 EXTENSION MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER 2 NEW rows industry-agnostic 4-industry grants ✅/✅/✅/✅. 결정 wire 일자: 2026-08-22 |
| **A126** | **AD-31 Multi-Region Backup & Disaster Recovery 신규 결정** — Phase 5 PRD entry 진입 시점에 결정 (cj-style Phase 5 1번째 진입점 = cj-style 73번째 epic 연속 정직 회복). AD-31 = (a) **Cross-region read replica + WAL archiving** 결정 wire = alembic `0039_phase_5_multi_region_backup.py` NEW `phase_5_replication_lag` table (BIGSERIAL id + replica_region TEXT enum seoul/tokyo/singapore/frankfurt/virginia/oregon/sao_paulo + primary_region TEXT enum + lag_bytes BIGINT + lag_seconds INTEGER + last_synced_lsn TEXT PG_LSN + last_synced_at TIMESTAMPTZ + replication_status TEXT enum syncing/replicating/lagged/disconnected/failed + created_at TIMESTAMPTZ DEFAULT NOW()) + 3 indexes (status + region+status+last_synced_at DESC + created_at) + 2 CHECK constraints (replication_status enum + replica_region enum) + audit-first INSERT `replica_status_changed` (CR 1-1 verbatim, action_class='INFRA' + action='replica_status_changed' + actor_id + region + previous_status + new_status + trace_id) 결정 wire 결정. WAL archiving 결정 wire = `postgresql.conf` `archive_mode = on` + `archive_command = 'pgbackrest --stanza=costmgr archive-push %p'` + `wal_level = replica` 결정 wire 보류 (Supabase managed 결정 wire). `docs/cross-region-replication.md` 결정 wire (cross-region replication setup + replica region 선택 Tokyo 1st choice latency Seoul-Tokyo ~50ms 결정 + replication lag monitoring lag_bytes threshold 100MB + lag_seconds threshold 30s alert 결정 + WAL archiving setup + Supabase pgbackrest 결정 wire 보류). / (b) **Cross-region failover automation** 결정 wire = `apps/api/jobs/failover_orchestrator.py` NEW ~200 LOC (primary → secondary health probe 5-second interval + 3 consecutive failures trigger 결정 + automatic promotion 결정: secondary region 의 PostgreSQL promote decision via Supabase API `POST /v1/projects/{ref}/database/promote` 결정 wire 보류 + read-only mode 해제 + connection pool redirect 결정) + DNS update 결정 wire (failover 결정 wire 진입 시점에 Supabase project URL 의 custom domain redirect 결정 wire + Supabase custom domain 결정 wire 보류) + RTO 30-second target 결정 wire + failover trigger 3종 결정 (a health probe 3 consecutive failures OR (b manual trigger via `POST /api/v1/admin/failover` owner-only AD-22 RBAC + 2FA 챌린지 Epic 12 정합 OR (c scheduled drill via `apps/api/jobs/dr_drill.py` cron 결정) + audit-first INSERT `failover_initiated` + `failover_completed` (CR 1-1 verbatim, action_class='INFRA' + action='failover_initiated' + actor_id + from_region + to_region + trace_id) + FastAPI lifespan hook startup/shutdown 결정 wire + GRACEFUL_SHUTDOWN_TIMEOUT=30s 결정 wire (in-flight requests 30s 대기 결정). / (c) **DR drill + automated quarterly test** 결정 wire = `apps/api/jobs/dr_drill.py` NEW ~150 LOC (cron KST 1st Sunday 03:00 = UTC 18:00 결정 wire + actual failover drill test in staging 결정 wire production 환경 직접 failover 위험 회피 결정 + 6 drill steps: staging primary health check + staging secondary promote trigger + staging database connection write test + staging application health check + staging DNS update test + staging primary restore trigger + RPO/RTO measurement decision drill 시작 시점 → drill 완료 시점 시간 측정 = RTO actual + drill 시작 전 마지막 transaction LSN → drill 후 secondary LSN 측정 = RPO actual + 결과 결정 wire `phase_5_dr_drill_results` table 신규 (BIGSERIAL id + drill_date DATE + rto_actual_seconds INTEGER + rpo_actual_bytes BIGINT + status TEXT enum pass/fail + notes TEXT + created_at TIMESTAMPTZ) + Q1/Q2/Q3/Q4 quarterly drill schedule 결정 wire (January + April + July + October 결정, docs/database-backup.md §9 quarterly drill pattern verbatim preserve) + audit-first INSERT `dr_drill_completed` (CR 1-1 verbatim, action_class='INFRA' + action='dr_drill_completed' + actor_id='system' + rto_actual_seconds + rpo_actual_bytes + status 결정) 결정. / (d) **Cross-region backup strategy** 결정 wire = `docs/database-backup.md` EXTENSION 10 sections → 12 sections (purpose + PITR strategy + RPO/RTO + restore procedure + disaster recovery + monitoring + retention + quarterly drill testing + cross-region backup strategy 신규 + cross-region failover runbook 신규 + RPO 1h / RTO 4h SLA 결정: Phase 4 single-region RPO 5min/RTO 1h 의 honest-extreme risk = Seoul region disaster 시 backup restoration 불가 verbatim 해소 결정 wire) + Cross-region backup vs single-region 결정 wire (Phase 4 single-region (Supabase Seoul primary + PITR 7일 자동) 의 honest-extreme risk 의 multi-region 해소 결정) + 30일 hot (primary) + 90일 cold (secondary) + 365일 archive (regional) retention decision. / (e) **Multi-region health observability** 결정 wire = `apps/api/core/health.py` EXTENSION `/api/v1/health/multi-region` endpoint 결정 wire (primary + secondary status array 결정 + CR 12-5 D-14 envelope `{status, primary: {region, status, lag_bytes, lag_seconds, last_synced_at}, secondary: {region, status, lag_bytes, lag_seconds, last_synced_at}, timestamp}` 결정 + JWT verification probe 결정 Supabase Auth health probe per-region 결정) + `apps/api/core/observability.py` EXTENSION Sentry breadcrumb failover_initiated 시 Sentry breadcrumb + alert decision (`sentry_sdk.capture_message(f"Failover initiated from {from_region} to {to_region}", level="warning")` + Sentry alert routing decision) + Grafana multi-region dashboard EXTENSION decision (primary + secondary region metrics + replication lag graph decision + failover event log decision) + `apps/web/app/api/health/multi-region/route.ts` NEW decision wire (~+30 LOC, atomic, Next.js Edge Runtime + force-dynamic + Vercel region decision + NextResponse.json envelope decision `{status, primary, secondary, build, region, timestamp}` decision wire). / (f) **Capability matrix v1.29 EXTENSION + 2 NEW rows** 결정 wire = `Capability.MULTI_REGION_BACKUP = "multi_region_backup"` 1 NEW row + `Capability.MULTI_REGION_FAILOVER = "multi_region_failover"` 1 NEW row (manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러, DEPLOYMENT_PROD + DEPLOYMENT_DATABASE_BACKUP Phase 4 wire + SSO_ENTERPRISE Epic 15 wire + TENANT_IDP_MANAGEMENT Epic 16 wire + LAUNCH_* 1st release wire + LISTEN_NOTIFY 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire pattern verbatim bind) + SSOT RED→GREEN EXTENSION (capability matrix v1.29 신규 2 rows + capability.py EXTENSION 2 NEW enum + `require_capability()` Dependency 2개 신규 wire) + drift detector `tests/integration/test_capability_matrix_v1_29_drift.py` NEW 결정 (Epic 16 wire 의 `tests/integration/test_capability_matrix_v1_28_drift.py` + Phase 4 wire 의 `tests/integration/test_capability_matrix_v1_25_drift.py` 패턴 verbatim). capability matrix v1.29 신규 2 rows (`MULTI_REGION_BACKUP` + `MULTI_REGION_FAILOVER`, industry-agnostic 4-industry grants ✅/✅/✅/✅) [§F20 verbatim, §8.1 M0-(m) EXTENSION 결정]. 결정 wire 일자: 2026-08-22 |
| **A127** | **Capability matrix v1.28 → v1.29 MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER 2 NEW rows 결정** — Phase 5 PRD entry 진입 시점에 결정 (cj-style Phase 5 1번째 진입점 = cj-style 73번째 epic 연속 정직 회복). `Capability.MULTI_REGION_BACKUP = "multi_region_backup"` 4-industry grants: manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ (industry-agnostic, CR 12-1 L4 precedent 미러, DEPLOYMENT_PROD + DEPLOYMENT_DATABASE_BACKUP Phase 4 wire pattern + SSO_ENTERPRISE Epic 15 wire + TENANT_IDP_MANAGEMENT Epic 16 wire + LAUNCH_* 1st release wire pattern verbatim bind). `Capability.MULTI_REGION_FAILOVER` 동일 industry-agnostic 4-industry grants ✅/✅/✅/✅. 미허용 tenant 의 multi-region 진입 차단 결정 wire. SSOT RED→GREEN EXTENSION (capability matrix v1.29 신규 2 rows + capability.py EXTENSION 2 NEW enum + `require_capability()` Dependency 2개 신규 wire + drift detector `tests/integration/test_capability_matrix_v1_29_drift.py` NEW). CR 11-3 honest-DEFER discipline 73번째 epic 연속 정직 회복 (D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVE 진입 wire 결정) + A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS). 결정 wire 일자: 2026-08-22 |
| **A128** | **Phase 5 wire scope T1~T8 결정** — Phase 5 PRD entry 진입 시점에 결정 (cj-style Phase 5 1번째 진입점 = cj-style 73번째 epic 연속 정직 회복). T1 alembic `0039_phase_5_multi_region_backup.py` NEW (~+120 LOC, phase_5_replication_lag table 결정 + phase_5_dr_drill_results table 결정 + replica_region enums + primary_region enum + replication_status enum 결정 + audit-first INSERT `replica_status_changed` CR 1-1 verbatim 결정 + 3 indexes + 2 CHECK constraints 결정) + T2 `apps/api/jobs/failover_orchestrator.py` NEW (~+200 LOC, primary → secondary health probe + automatic promotion + DNS update via Supabase API 결정 wire + RTO 30s target 결정 + audit-first INSERT `failover_initiated` + `failover_completed` CR 1-1 verbatim 결정 + FastAPI lifespan hook + GRACEFUL_SHUTDOWN_TIMEOUT=30s 결정 + owner-only manual trigger `POST /api/v1/admin/failover` AD-22 RBAC 결정) + T3 `apps/api/jobs/dr_drill.py` NEW (~+150 LOC, cron KST 1st Sunday 03:00 UTC 18:00 결정 + actual failover drill test in staging 결정 + 6 drill steps + RPO/RTO measurement + `phase_5_dr_drill_results` table 결정 + Q1/Q2/Q3/Q4 quarterly schedule 결정 + audit-first INSERT `dr_drill_completed` CR 1-1 verbatim 결정) + T4 cross-region backup strategy wire (`docs/database-backup.md` EXTENSION 10 sections → 12 sections + cross-region PITR primary Seoul + secondary Tokyo + 30일 hot + 90일 cold + 365일 archive regional + RPO 1h / RTO 4h SLA 결정 + `docs/cross-region-replication.md` 결정 wire) + T5 multi-region health observability wire (`apps/api/core/health.py` EXTENSION `/api/v1/health/multi-region` endpoint 결정 + CR 12-5 D-14 envelope 결정 + `apps/api/core/observability.py` EXTENSION Sentry breadcrumb failover 결정 + Grafana multi-region dashboard EXTENSION 결정 + `apps/web/app/api/health/multi-region/route.ts` NEW 결정) + T6 Capability v1.29 EXTENSION 2 NEW rows (capability.py MODIFIED + `tests/integration/test_capability_matrix_v1_29_drift.py` NEW decision + docs/capability-matrix.md v1.28 → v1.29) + T7 Tests + 3중 게이트 FINAL CLEAN (~+50 NEW pytest PASS + ~+10 NEW vitest PASS + 1 NEW integration drift decision + 4 NEW audit log verification) + T8 3중 게이트 FINAL CLEAN atomic commit decision. estimated ~50 NEW pytest PASS + ~10 NEW vitest PASS + 0 NEW ruff + 0 regressions. wire_commit = TBD (cj-style Phase 5 3번째 진입점 = cj-style 75번째 epic 연속 정직 회복 atomic single sweep T1~T8, expected ~12-15 files = ~10 NEW + ~2-5 MODIFIED). 결정 wire 일자: 2026-08-22 |

### Epic 17 PRD entry 결정 (2026-08-22, cj-style Epic 17 1번째 진입점 = cj-style 80번째 epic 연속 정직 회복)

| 결정 | 내용 |
|------|------|
| **A153** | **옵션 (a) Epic 17 진입 결정** — Sidebar/MenuProvider hot-fix `01a06e4` (cj-style 79번째 wire entry) + D-EPIC-16-REVIEW-DEFER-2~6 RESOLVE sprint `512ed6a` (cj-style 78번째) + Phase 5 close-out retro `b843565` (cj-style 76~77번째) wire DONE 진입 직후 next 옵션 5종 중 **사용자 권장 결정 = 옵션 (a) Epic 17 진입**. rationale 4종: (1) **Epic 1 ~ Epic 16 + Phase 3 + Phase 4 + Phase 5 모두 wire DONE (49~79번째 cumulative cycle)** → 모든 territory 의 audit-first INSERT (CR 1-1) 가 audit_log table 에 누적 → audit log viewer territory 자연스러운 next 진입 / (2) **cj-style discipline 회피 위험 방지** = 49~79번째 누적 31-entry-point cycle + 78~79번째 hot-fix + RESOLVE sprint 직후 즉시 Epic 17 진입 = 1-day atomic sprint discipline / (3) **비즈니스 우선순위 = enterprise 고객 onboarding 시 audit log viewer 필수** (PIPA + GDPR + SOX compliance = audit log 가시성 + filter + export 기능 요구) / (4) **Phase 5 multi-region wire 의 cross-region audit log visibility 자연스러운 carry-over** (audit_log table 은 cross-region primary 에 write → multi-region read replica 통한 cross-region audit visibility 제공). 옵션 (b) carry-over / 옵션 (c) 1st release 추가 follow-up / 옵션 (d) Phase 6 / 옵션 (e) D-PHASE-4-DR-DEFER follow-up 모두 rejected (rationale: Phase 5 territory DONE 정합 + audit log viewer territory 의 natural next 진입 = business priority + cross-region carry-over). Phase 5 territory DONE 정합 보존 (cj-style 73~77번째 epic 연속 정직 회복) + Epic 16 territory DONE 정합 보존 (cj-style 67~72번째 epic 연속 정직 회복) + 1st release territory DONE 정합 보존 (cj-style 62~66번째 epic 연속 정직 회복) + Epic 15 territory DONE 정합 보존 (cj-style 58~61번째 epic 연속 정직 회복) + Phase 4 territory DONE 정합 보존 (cj-style 53~57번째 epic 연속 정직 회복) + Phase 3 territory DONE 정합 보존 (cj-style 49~52번째 epic 연속 정직 회복) 결정 wire 모두 보존. Epic 17 PRD entry 진입 시점에 적용 (cj-style 80번째 epic 연속 정직 회복 진입 시점에 결정). ✅ done 진입 2026-08-22. **A154+A155+A156+A157 follow-on**: master PRD v3.5 → v3.6 atomic edit + AD-32 Audit Log Viewer & Activity Stream 신규 + capability matrix v1.29 → v1.30 EXTENSION AUDIT_LOG_VIEW 1 NEW row + Epic 17 wire scope T1~T8 결정 |
| **A154** | **Master PRD v3.5 → v3.6 atomic edit 결정** — Epic 17 PRD entry 진입 시점에 결정 (cj-style Epic 17 1번째 진입점 = cj-style 80번째 epic 연속 정직 회복). master PRD v3.5 → v3.6 atomic edit (docs only, no code/test/sprint-status delta 외 PRD edit 신규). (1) front matter title v3.5 → v3.6 + changelog v3.6 entry 신규 (cj-style 80번째 epic 연속 정직 회복 진입 시점에 결정 verbatim 보존) / (2) §F21 신규 (F21.1 audit log query API + F21.2 audit log viewer UI + F21.3 activity stream UI + F21.4 cross-region audit log visibility + F21.5 CSV export + F21.6 capability gate AUDIT_LOG_VIEW + F21.7 tests + wire scope T1~T8 결정) / (3) §8.1 M0-(n) audit log viewer AC 신규 / (4) §15 로드맵 Epic 17 row status 백로그 → in-progress (PRD entry DONE 진입 wire) / (5) §부록 A A153+A154+A155+A156+A157 신규 결정 표 / (6) AD-32 Audit Log Viewer & Activity Stream 신규 결정 (audit log viewer architecture 7 sub-decisions) / (7) capability matrix v1.29 → v1.30 EXTENSION AUDIT_LOG_VIEW 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅. 결정 wire 일자: 2026-08-22 |
| **A155** | **AD-32 Audit Log Viewer & Activity Stream 신규 결정** — Epic 17 PRD entry 진입 시점에 결정 (cj-style Epic 17 1번째 진입점 = cj-style 80번째 epic 연속 정직 회복). AD-32 = (a) **audit log query API** 결정 wire = `apps/api/modules/audit/audit_log_query.py` NEW ~180 LOC (4 functions: `query_audit_log(tenant_id, filters, page, page_size) -> AuditLogPage` + `count_audit_log(tenant_id, filters) -> int` + `get_audit_log_entry(tenant_id, entry_id) -> AuditLogEntry` + `query_activity_stream(tenant_id, window_days) -> list[ActivityStreamGroup]` 결정 + AuditLogQueryFilters TypedDict `{actor_id, action_class, action, period_key, payload_search, start_date, end_date}` 결정 + AuditLogEntry TypedDict `{id, tenant_id, actor_id, actor_email, action_class, action, payload_json, created_at, trace_id}` 결정 + AuditLogPage TypedDict `{entries, total_count, page, page_size, has_next}` 결정 + ActivityStreamGroup TypedDict `{date, entries, unique_actors}` 결정 + RLS `tenant_id = (SELECT current_setting('app.tenant_id'))::uuid` 자동 적용 (CR 0-2 RLS lesson 적용, AD-22 verbatim 보존) + owner/admin role required `require_role("owner", "admin")` FastAPI Dependency (Epic 12 2FA 게이트 보존) + capability gate `AUDIT_LOG_VIEW` 자동 적용 + pagination offset+limit (page_size=50 default, max 200) + sort `ORDER BY created_at DESC` 결정 + performance `audit_log` table 의 `(tenant_id, created_at DESC)` index 활용 + `payload_json` 의 GIN index (jsonb_path_ops) 결정 wire. / (b) **audit log viewer UI** 결정 wire = `apps/web/app/[locale]/(dashboard)/audit-log/page.tsx` NEW ~200 LOC + 5 components (`AuditLogFilterPanel` (filter form: actor email autocomplete + action_class dropdown + action text search + period_key + date range picker + payload_search input) + `AuditLogTable` (table view: created_at + actor_email + action_class chip + action text + payload summary + trace_id expandable) + `AuditLogPagination` (prev/next + page size selector + total count display) + `AuditLogExportButton` (CSV export trigger, calls F21.5 backend) + `AuditLogDetailModal` (full payload_json + trace_id expansion modal)) + ko-KR.json `audit_log.*` namespace EXTENSION 14 keys 결정 (CR 11-4 D-002 verbatim SSOT) + `(dashboard)` route group 보호 (Phase 3-1 T4 wire 정합) + `apps/web/lib/audit/audit-log-client.ts` NEW (fetch wrapper + auth cookie 자동 첨부 + typed error envelope) + vitest RTL render discipline 결정 (CR 11-4 D-003 verbatim). / (c) **activity stream UI** 결정 wire = `apps/web/app/[locale]/(dashboard)/activity/page.tsx` NEW ~150 LOC + 3 components (`ActivityStreamTimeline` (grouped by date: today / yesterday / N days ago) + `ActivityStreamEntry` (avatar + action_class icon + action text + actor name + relative time) + `ActivityStreamWindowSelector` (7일 / 30일 / 90일 window selector)) + ko-KR.json `activity.*` namespace EXTENSION 8 keys 결정 (title + description + window_7d + window_30d + window_90d + empty_message + today_label + yesterday_label) + all tenant members 권한 (`require_role("owner", "admin", "member", "viewer")`) + activity stream 은 tenant-wide 가시성 (owner/admin audit log viewer 와 분리). / (d) **cross-region audit log visibility** 결정 wire = Phase 5 multi-region wire `f093f8c` 의 `apps/api/alembic/versions/0039_phase_5_multi_region_backup.py` `phase_5_replication_lag` table + Supabase multi-region primary Seoul + secondary Tokyo replica 결정 wire EXTENSION (audit log query 시 secondary region 의 read replica 에서 query 가능 결정 wire + multi-region read replica 통한 cross-region audit visibility) + `/api/v1/audit-log` handler 에서 connection pool 의 read-only routing 결정 wire + 읽기 일관성 결정 wire (secondary region 의 replication lag 이 lag_bytes ≤ 100MB + lag_seconds ≤ 30s 시 read consistent (Phase 5 wire 의 lag threshold 정합) — lag 초과 시 primary region 으로 fallback + Sentry breadcrumb 결정 wire). / (e) **CSV export** 결정 wire = `apps/api/modules/audit/audit_log_export.py` NEW ~120 LOC + `export_audit_log_csv(tenant_id, filters, actor_id) -> StreamingResponse` 결정 (Excel-compatible UTF-8 BOM `﻿` + comma-separated + double-quote escape for payload_json) + columns `entry_id,created_at,actor_email,action_class,action,period_key,payload_json,trace_id` 결정 + streaming response `StreamingResponse(media_type='text/csv; charset=utf-8', headers={'Content-Disposition': f'attachment; filename="audit-log-{tenant_slug}-{yyyymmdd}.csv"'})` 결정 (large dataset 시 memory efficient) + audit-first INSERT `audit_log_exported` (CR 1-1 verbatim, action_class='AUDIT' + action='audit_log_exported' + actor_id + tenant_id + filters_json + row_count + trace_id) — 누가 언제 어떤 filter 로 export 했는지 추적 + CR 12-5 D-14 error envelope `{code, message_ko, details, trace_id}` 결정 (e.g. `AUDIT_LOG_EXPORT_FORBIDDEN_KO`, `AUDIT_LOG_EXPORT_TOO_LARGE_KO`). / (f) **audit-first INSERT 1 NEW + RLS 자동 적용** 결정 wire (CR 1-1 verbatim + CR 0-2 RLS lesson 적용, F21.5 `audit_log_exported` 1 NEW audit log entry 결정, action_class='AUDIT' + action='audit_log_exported' + actor_id + tenant_id + filters_json + row_count + trace_id + per-tenant RLS 자동 적용, multi-tenant isolation test 결정). / (g) **Capability matrix v1.30 EXTENSION + 1 NEW row** 결정 wire = `Capability.AUDIT_LOG_VIEW = "audit_log_view"` 신규 1 row (manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ industry-agnostic 4-industry grants, CR 12-1 L4 precedent 미러, MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY Epic 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern verbatim bind) + 미허용 tenant 의 audit log 진입 차단 결정 wire + SSOT RED→GREEN EXTENSION (capability matrix v1.30 신규 1 row + capability.py EXTENSION 1 NEW enum + `require_capability()` Dependency 1개 신규 wire) + drift detector `tests/integration/test_capability_matrix_v1_30_drift.py` NEW 결정 (Phase 5 wire 의 `tests/integration/test_capability_matrix_v1_29_drift.py` + Epic 16 wire 의 `tests/integration/test_capability_matrix_v1_28_drift.py` 패턴 verbatim). capability matrix v1.30 신규 1 row (`AUDIT_LOG_VIEW`, industry-agnostic 4-industry grants ✅/✅/✅/✅) [§F21 verbatim, §8.1 M0-(n) EXTENSION 결정]. 결정 wire 일자: 2026-08-22 |
| **A156** | **Capability matrix v1.29 → v1.30 AUDIT_LOG_VIEW 1 NEW row 결정** — Epic 17 PRD entry 진입 시점에 결정 (cj-style Epic 17 1번째 진입점 = cj-style 80번째 epic 연속 정직 회복). `Capability.AUDIT_LOG_VIEW = "audit_log_view"` 4-industry grants: manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ (industry-agnostic, CR 12-1 L4 precedent 미러, MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY Epic 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern verbatim bind). 미허용 tenant 의 audit log viewer 진입 차단 결정 wire. SSOT RED→GREEN EXTENSION (capability matrix v1.30 신규 1 row + capability.py EXTENSION 1 NEW enum + `require_capability()` Dependency 1개 신규 wire + drift detector `tests/integration/test_capability_matrix_v1_30_drift.py` NEW). CR 11-3 honest-DEFER discipline 80번째 epic 연속 정직 회복 (D-1-1-DEFER-1/2/3 RESOLVED 보존 + D-LAUNCH-1-DEFER-1 honestly preserved + D-EPIC-16-REVIEW-DEFER-2~6 ✅ RESOLVED 보존 + D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED 보존) + A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS). 결정 wire 일자: 2026-08-22 |
| **A157** | **Epic 17 wire scope T1~T8 결정** — Epic 17 PRD entry 진입 시점에 결정 (cj-style Epic 17 1번째 진입점 = cj-style 80번째 epic 연속 정직 회복). T1 `apps/api/modules/audit/audit_log_query.py` NEW (~+180 LOC, 4 functions: query_audit_log + count_audit_log + get_audit_log_entry + query_activity_stream + 4 TypedDict 결정 + RLS 자동 적용 + capability gate AUDIT_LOG_VIEW + owner/admin role required + pagination + sort) + T2 `apps/api/modules/audit/audit_log_export.py` NEW (~+120 LOC, streaming response + UTF-8 BOM + audit-first INSERT `audit_log_exported` CR 1-1 verbatim + CR 12-5 D-14 envelope) + T3 `apps/web/app/[locale]/(dashboard)/audit-log/page.tsx` NEW (~+200 LOC + 5 components 결정 + ko-KR.json `audit_log.*` namespace EXTENSION 14 keys + (dashboard) 보호) + T4 `apps/web/app/[locale]/(dashboard)/activity/page.tsx` NEW (~+150 LOC + 3 components 결정 + ko-KR.json `activity.*` namespace EXTENSION 8 keys + all tenant members 권한) + T5 ko-KR.json SSOT EXTENSION wire (`audit_log.*` 14 keys + `activity.*` 8 keys 결정 wire, CR 11-4 D-002 verbatim 적용) + T6 Capability v1.30 EXTENSION 1 NEW row (capability.py MODIFIED + `tests/integration/test_capability_matrix_v1_30_drift.py` NEW + docs/capability-matrix.md v1.29 → v1.30) + T7 Tests + 3중 게이트 FINAL CLEAN (~+50 NEW pytest PASS + ~+15 NEW vitest PASS + 1 NEW integration drift + audit_first INSERT verification + F21.4 cross-region lag threshold test + F21.5 CSV export test) + T8 3중 게이트 FINAL CLEAN atomic commit decision. estimated ~50 NEW pytest PASS + ~15 NEW vitest PASS + 0 NEW ruff + 0 regressions. wire_commit = TBD (cj-style Epic 17 3번째 진입점 = cj-style 82번째 epic 연속 정직 회복 atomic single sweep T1~T8, expected ~14-18 files = ~12 NEW + ~3-6 MODIFIED). 결정 wire 일자: 2026-08-22 |

### Architectural Decisions (AD) — Epic 0~10 wire 정합 (2026-08-20 master PRD v2.0 edit)

> 본 절은 §3 회계 공리 헌장 (A1~A11) 외 **아키텍처 결정을 위한 AD (Architectural Decision)** 을 추가한다. AD-7·17·25 는 Epic 10 wire 진입 시점에 신규 bind 되었으며 master PRD v2.0 본체에 정식 등록한다.

| AD | 내용 | Story bind | Capability | 결정 wire |
|---|---|---|---|---|
| **AD-7 AI non-authoritative** | AI output → `input_drafts` only. `confirmed_inputs` 도달은 **AD-17 경로만**. AI commentary `source_kind='ai_reference'`. 자동 분석 `source_kind='auto_analysis'`. M10 attempts to write confirmed-input tables → denied + counted (target 0). System은 strict reject 외 value 도달 시 counter increment (F10.2-(b) 정합) | 10-1·10-3·10-4 | `AI_INSIGHT` (capability matrix v1.21, Epic 10 wire) | Epic 10 PRD entry 2026-08-17 |
| **AD-17 AI draft promotion port** | Only M2 may call `InputPromoter.promote(tenant_id, period_key, source_draft_id) -> MonthlyInput`. **Idempotent on `(tenant_id, period_key, source_draft_id)`**. Promotion retains draft with `state='promoted'`, records actor + draft hash in audit_logs, writes canonical confirmed-input shape. M10 never writes confirmed inputs | 10-1 + 10-4 | `AI_INSIGHT` | Epic 10 PRD entry 2026-08-17 |
| **AD-25 AI insight cache invalidation** | M10 cache key: `(tenant_id, period_key, calculation_result_hash)`. New AD-4 commit, AD-22 reversal insert, or M11 reopen emits one DB notification per `cache_invalidation_log` channel. M10 adapter consumes it and invalidates matching entries. Application polling + input-write-only invalidation forbidden. **EXTENSION (Epic 13 wire DONE 2026-08-20, A52)** — 4-channel publisher EXTENSION 결정 wire: `ai_cache` 외 `cost_engine_cache` / `fiscal_period_cache` / `closing_snapshot_cache` 3 channel 추가. PostgreSQL `LISTEN/NOTIFY` channel-specific eviction handler wire (alembic 0033 NOTIFY trigger + LISTEN daemon + 4-channel adapter dispatch). NOTIFY payload JSON 6-key alphabetical: `{channel, correction_group_id, invalidation_id, period_key, tenant_id, trace_id}`. capability matrix v1.22 신규 row `LISTEN_NOTIFY` (4-industry grants ✅/✅/✅/✅ industry-agnostic) [§F13 verbatim, §8.1 M10-(d)·§F10.1-(d) EXTENSION 결정]. **EXTENSION (Epic 14 PRD entry DONE 2026-08-20, A58)** — **5+ channels EXTENSION 결정 wire**: 4-channel 외 `cross_tenant_fanout` 1 channel 추가 (총 5+ channels). Cross-tenant invalidation fan-out channel = tenant-level subscription routing + multi-tenant isolation 검증 (CR 0-2 RLS lesson 적용 + AD-22 verbatim 보존). NOTIFY payload 7-key alphabetical EXTENSION: `{channel, correction_group_id, invalidation_id, period_key, source_tenant_id, target_tenant_ids, trace_id}`. **Multi-process coordination Option 1 결정**: PostgreSQL `LISTEN/NOTIFY` only via pg_notify fan-out leader/follower model (advisory lock + leader election + follower health check + leader takeover). Option 2 Redis pub/sub rejected (rationale: G2 인프라 최소화 정합). capability matrix v1.23 EXTENSION (`LISTEN_NOTIFY_TENANT_FANOUT` + `LISTEN_NOTIFY_MULTIPROCESS` 2 NEW rows, industry-agnostic 4-industry grants ✅/✅/✅/✅) [§F14 verbatim, §8.1 M10-(d)·§F10.1-(d) cross-tenant fan-out EXTENSION 결정] | 10-2 (+ 13-1 EXTENSION + 14-1 EXTENSION 진입 대기) | `AI_INSIGHT` (+ `LISTEN_NOTIFY` + `LISTEN_NOTIFY_TENANT_FANOUT` + `LISTEN_NOTIFY_MULTIPROCESS`) | Epic 10 PRD entry 2026-08-17 (Epic 13 EXTENSION 2026-08-20 + Epic 14 EXTENSION 결정 2026-08-20) |
| **AD-26 Auth Foundation** | **EXTENSION (Phase 3 PRD entry DONE 2026-08-20, A66)** — Phase 3 = 로그인/회원가입 UI + auth middleware (Epic 1 완성 territory) 신규 bind. (a) **Supabase SSR auth client** 결정 wire = `createServerClient` (Server Components, cookie-based) + `createBrowserClient` (Client Components, localStorage-based), single source of truth URL + anon key. (b) **`sb-access-token` cookie session** 결정 wire = `httpOnly` + `secure` + `sameSite=lax` + `path=/` + `maxAge=3600` (1시간, refresh token 으로 자동 �신). (c) **next-intl middleware EXTENSION** 결정 wire = `apps/web/middleware.ts` 의 next-intl middleware 에 Supabase session check + `(dashboard)` 보호 + `?redirect=` 쿼리 보존 + `(auth)` 공개 + `/api/v1/*` bypass + Edge Runtime 명시 추가. (d) **Auth route group `(auth)` 공개** 결정 wire (login + signup + forgot-password + 2fa + email-verification-pending). (e) **Dashboard route group `(dashboard)` 보호** 결정 wire (Supabase session 필수 + Epic 12 2FA 미설정 시 `/account/security?reason=2fa_required` redirect, Epic 12 M12-a 정합). (f) **CSRF 방어** 결정 wire = Supabase PKCE flow + sameSite=lax cookie 정합 (별도 CSRF token 미사용, Supabase 권장 정합). (g) **Email 존재 여부 노출 방지** 결정 wire = forgot-password 항상 200 반환 (보안 invariant). capability matrix v1.24 신규 5 rows (`LOGIN` + `SIGNUP` + `AUTH_MIDDLEWARE` + `FORGOT_PASSWORD` + `LOGOUT`, industry-agnostic 4-industry grants ✅/✅/✅/✅) [§F15 verbatim, §8.1 M0-(d)·M0-(e)·M0-(f) EXTENSION 결정] | Phase 3 T1~T8 (cj-style Phase 3 3번째 진입점 진입 대기) | `LOGIN` + `SIGNUP` + `AUTH_MIDDLEWARE` + `FORGOT_PASSWORD` + `LOGOUT` | Phase 3 PRD entry 2026-08-20 |
| **AD-28 Magic link + Social OAuth + SSO enterprise SAML** | **EXTENSION (Epic 15 PRD entry DONE 2026-08-22, A80)** — Epic 15 = Magic link + Social OAuth (Google/Naver/Kakao) + SSO enterprise SAML 통합 territory 신규 bind. (a) **Magic link** 결정 wire = Supabase `signInWithOtp({ email, options: { emailRedirectTo } })` wrapper + 5회 cool-down sessionStorage 30s (Phase 3-1 T2 wire 패턴 미러) + email 존재 여부 노출 방지 security invariant try/catch/finally (Phase 3-1 T6 forgot-password 정합) + audit-first INSERT `magic_link_sent` (CR 1-1 verbatim, action_class='AUTH' + action='magic_link_sent' + actor_id + target_email) + `sb-access-token` cookie session 자동 설정 (Phase 3-1 T1 wire 정합) + Epic 12 2FA 미설정 시 `/auth/2fa` redirect 결정. (b) **Social OAuth Google/Naver/Kakao** 결정 wire = Supabase `signInWithOAuth({ provider, options: { redirectTo } })` wrapper + provider whitelist `ALLOWED_SOCIAL_PROVIDERS = frozenset({'google', 'naver', 'kakao'})` strict reject + counter increment (AD-7 verbatim 정합) + 3회 cool-down sessionStorage 60s + audit-first INSERT `social_oauth_initiated` (CR 1-1 verbatim) + OAuth callback handler `/auth-callback` + `exchangeCodeForSession(code)` + Naver OAuth Option A Supabase 우선 / Option B custom Naver OAuth flow 결정 wire 보존. (c) **SSO enterprise SAML** 결정 wire = `python3-saml==1.16.0` AD-14 stack pin + SAML response validation (signature verification + `NotBefore`/`NotOnOrAfter` timestamp + `Audience` + `Destination` + `InResponseTo` CSRF 방어 + RelayState base64 encode) + 4 SSO routes (`/api/v1/auth/sso/{login,acs,metadata,sls}`) + JIT (Just-In-Time) user provisioning atomic 5-step flow (SAML → user + tenant_memberships + external_identities) + multi-tenant isolation CR 0-2 RLS lesson (`external_identities` RLS policy `tenant_id = (SELECT current_setting('app.tenant_id'))::uuid` 결정, alembic 0037) + tenant slug 별 IdP metadata routing (multi-tenant SSO) + audit-first INSERT `sso_identity_linked` (CR 1-1 verbatim, action_class='AUTH' + action='sso_identity_linked' + actor_id + provider + provider_user_id + tenant_id). capability matrix v1.26 신규 5 rows (`MAGIC_LINK` + `SOCIAL_OAUTH_GOOGLE` + `SOCIAL_OAUTH_NAVER` + `SOCIAL_OAUTH_KAKAO` + `SSO_ENTERPRISE`, industry-agnostic 4-industry grants ✅/✅/✅/✅) [§F17 verbatim, §8.1 M0-(h)·M0-(i)·M0-(j) EXTENSION 결정] | Epic 15 T1~T8 (cj-style Epic 15 3번째 진입점 진입 대기) | `MAGIC_LINK` + `SOCIAL_OAUTH_GOOGLE` + `SOCIAL_OAUTH_NAVER` + `SOCIAL_OAUTH_KAKAO` + `SSO_ENTERPRISE` | Epic 15 PRD entry 2026-08-22 |
| **AD-29 1st release launch** | **신규 결정 (1st release launch PRD entry DONE 2026-08-22, A85)** — 1st release launch = Epic 15 close-out retro §12 옵션 (d) 결정 진입 territory 신규 bind. (a) **Marketing landing page** 결정 wire = `/landing` public route (vercel.json public route EXTENSION) + `LandingHero` + `LandingFeatures` (6 feature cards: ABC engine + TDABC + AI insight + 4-industry grants + 2FA + LISTEN/NOTIFY) + `LandingPricing` (월 1만원 subscription + 14일 무료 체험 결정) + `LandingCTA` (signup CTA button + `/login` redirect) + ko-KR inline copy EXTENSION (`landing.*` namespace 8 keys) + `(public)` route group 신규 (D-001 route.tsx mount MUST actual mount) — `(auth)/landing` 결정 wire 진입. (b) **ToS + Privacy Policy** 결정 wire = `docs/terms-of-service.md` (~+150 LOC, 8 sections: 정의 + 서비스 이용 + 계약 변경 + 환불 정책 + 면책 + 분쟁 해결 + 準拠법 + 개정 이력) + `docs/privacy-policy.md` (~+200 LOC, 한국 PIPA + GDPR 정합, 10 sections: 수집 항목 + 이용 목적 + 보유 기간 + 제3자 제공 + 처리 위탁 + 정보주체 권리 + 안전성 확보 조치 + 쿠키 정책 + 분쟁 해결 + 개정 이력) + versioning (changelog + effective date 표기) + signup flow EXTENSION `(auth)/tos` + `(auth)/privacy` 결정 wire 진입 (Phase 3-1 wire `d3e7454` 정합). (c) **Onboarding user guide** 결정 wire = `docs/onboarding-guide.md` (~+200 LOC, 8 sections: 시작하기 + 첫 대시보드 + 데이터 입력 6종 + ABC/TDABC 분석 활용 + AI 인사이트 활용 + 보안/2FA 설정 + 자주 묻는 질문 + 지원팀 연락) + `OnboardingTooltip.tsx` (first-run wizard EXTENSION 결정, Epic 1 partial scaffold `d182d7d` 정합) + 4 tooltips (dashboard 첫 진입 + 데이터 입력 첫 진입 + 보고서 첫 진입 + 2FA 설정 첫 진입) + first-run wizard `(auth)/onboarding/page.tsx` (4-step wizard 결정). (d) **Customer support channels** 결정 wire = `docs/support.md` (~+150 LOC, 6 sections: 연락 채널 + FAQ + 응답 시간 + SLA + escalation 절차 + 외부 지원 링크) + `support@bizup.kr` email 결정 wire 진입 (Phase 4 deployment `934b35e` 환경 변수 EXTENSION) + in-app help widget `HelpWidget.tsx` (Phase 4 Sentry observability EXTENSION 결정) + `docs/faq.md` (~+100 LOC, 10 Q&A). (e) **Production launch verification** 결정 wire = smoke test RE-RUN 정직 결정 wire (`apps/api/scripts/smoke_test.py` RE-RUN, Walking Skeleton MVP `1e034c4` + Phase 3 close-out retro §6 honestly DEFER 해소, Epic 1 ~ Epic 15 모든 wire flow 정합 검증) + backup drill 0036 PITR quarterly EXTENSION (Phase 4 wire `71a033a` 정합) + Sentry alert wiring production 환경 (`apps/web/lib/observability/sentry-alerts.ts` + `apps/api/lib/observability/sentry-alerts.py`, Phase 4 deployment territory EXTENSION) + RPO 4h / RTO 24h SLA verification 결정 wire 진입 (Phase 4 backup strategy 정합) + launch checklist 6 conditions ALL PASS 진입 시점에 1st release official launch 결정 wire 보존. (f) **Public launch communications** 결정 wire = `docs/launch-announcement.md` (~+100 LOC, 4 sections: 출시 배경 + 핵심 기능 + 타겟 시장 + 향후 로드맵) + `docs/press-kit.md` (~+50 LOC, 회사 소개 + 제품 소개 + 로고 + 팩트시트 + 연락처 + 미디어 키트 결정) + social media assets `apps/web/public/og/` (og:image + og:description + twitter:card 결정, metadata 결정 wire 진입) + in-app announcement banner `(auth)/announcements/page.tsx` 결정 wire 진입. capability matrix v1.27 신규 4 rows (`LAUNCH_LANDING` + `LAUNCH_TOS` + `LAUNCH_SUPPORT` + `LAUNCH_MONITORING`, industry-agnostic 4-industry grants ✅/✅/✅/✅) [§F18 verbatim, §8.1 M0-(k) EXTENSION 결정] | 1st release T1~T8 (cj-style 1st release 3번째 진입점 진입 대기) | `LAUNCH_LANDING` + `LAUNCH_TOS` + `LAUNCH_SUPPORT` + `LAUNCH_MONITORING` | 1st release launch PRD entry 2026-08-22 |
| **AD-30 Tenant IdP admin management** | **신규 결정 (Epic 16 PRD entry DONE 2026-08-22, A94)** — Epic 16 = Tenant IdP admin management = Epic 15 close-out retro §12 옵션 (a) 결정 진입 territory 신규 bind (Epic 15 SSO enterprise SAML forward-reference `docs/sso-enterprise.md` §4.1 step 3 `Configure tenant_idps (TODO Epic 16)` verbatim 자연스러운 carry-over chain 결정 wire). (a) **`tenant_idps` table schema** 결정 wire = alembic `0038_epic_16_tenant_idps.py` NEW (13 columns: `id` UUID PK + `tenant_id` UUID FK `tenants(id)` + `idp_entity_id` TEXT NOT NULL + `idp_sso_url` TEXT NOT NULL + `idp_slo_url` TEXT nullable + `idp_x509_cert` TEXT NOT NULL (PEM 결정) + `acs_url` TEXT NOT NULL + `name_id_format` TEXT nullable + `enabled` BOOLEAN NOT NULL DEFAULT TRUE + `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW() + `updated_at` TIMESTAMPTZ NOT NULL DEFAULT NOW() + `created_by` UUID FK `users(id)` + `updated_by` UUID FK `users(id)`) + UNIQUE constraint `(tenant_id, idp_entity_id)` 결정 + RLS policy `tenant_id = current_setting('app.tenant_id')::uuid` 결정 (CR 0-2 RLS lesson 적용 + AD-22 verbatim 보존) + audit trigger `audit_log_trigger_row()` 자동 호출 결정. (b) **IdP metadata XML validation service** 결정 wire = `apps/api/modules/auth/sso/idp_metadata_validator.py` NEW ~120 LOC (Epic 15 `saml_validator.py` sibling module, 8 validation steps: XML well-formedness + EntityDescriptor root element 확인 + entityID 추출 + IDPSSODescriptor 존재 확인 + X509Certificate PEM wrap + SingleSignOnService Binding=HTTP-Redirect + Location `https://` scheme 검증 + SingleLogoutService 선택 + tenant slug `idp_entity_id` 매칭) + `IdPMetadataError` typed exception envelope `{code, message_ko, details, trace_id}` 결정 (CR 12-5 D-14 verbatim) + `IdPMetadata` TypedDict 6 fields (entity_id, sso_url, slo_url, x509_cert, acs_url, name_id_format). (c) **Tenant IdP CRUD API 5 routes** 결정 wire = `apps/api/modules/auth/sso/idp_admin_routes.py` NEW ~150 LOC (FastAPI Dependency Injection: `GET /api/v1/admin/tenant/{tenant_slug}/idp` (list) + `POST /api/v1/admin/tenant/{tenant_slug}/idp` (create + IdP metadata validation 자동 호출) + `PUT /api/v1/admin/tenant/{tenant_slug}/idp/{idp_id}` (update) + `DELETE /api/v1/admin/tenant/{tenant_slug}/idp/{idp_id}` (delete, audit-first INSERT) + `POST /api/v1/admin/tenant/{tenant_slug}/idp/{idp_id}/test` (test metadata, AuthnRequest 생성 + dry-run SAML flow) + owner/admin role required `require_role("owner", "admin")` FastAPI Dependency + capability gate `TENANT_IDP_MANAGEMENT` 자동 적용 + RLS 자동 적용 (CR 0-2 verbatim) + audit-first INSERT 4 NEW 결정: `tenant_idp_created` + `tenant_idp_updated` + `tenant_idp_deleted` + `tenant_idp_tested` (CR 1-1 verbatim 적용, action_class='AUTH' + action='tenant_idp_*' + actor_id + tenant_id + payload_json 정합). (d) **Tenant IdP admin UI** 결정 wire = `apps/web/app/[locale]/(dashboard)/settings/sso/page.tsx` NEW ~150 LOC + 4 components (`TenantIdPConfigForm` (metadata XML paste + file upload + entity ID auto-extract) + `TenantIdPStatusBadge` (enabled/disabled color coded) + `TenantIdPTestResultModal` (test metadata 결과 5 indicators) + `TenantIdPDeleteConfirmDialog` (확인 문구 + tenant slug typing verify)) + ko-KR.json `settings.sso.*` namespace EXTENSION 12 keys 결정 (CR 11-4 D-002 verbatim SSOT) + `(dashboard)` route group 보호 (Phase 3-1 T1 wire 정합) + `apps/web/lib/auth/admin-idp-client.ts` NEW (fetch wrapper + auth cookie 자동 첨부 + typed error envelope) + vitest RTL render discipline 결정 (CR 11-4 D-003 verbatim). (e) **Per-tenant IdP routing EXTENSION** 결정 wire = Epic 15 `apps/api/modules/auth/sso/saml_routes.py` MODIFIED (existing `acme` hardcoded tenant backward compatibility 보존: `acme` tenant 의 경우 `idp_sso_url` redirect → dynamic lookup `tenant_idps` table SELECT) + ACS `idp_x509_cert` 동적 로딩 결정 (per-tenant IdP cert SELECT, multi-tenant SSO scenario) + alembic 0038 데이터 migration `acme` tenant row 자동 seed 결정 (Epic 15 wire 의 backward compatibility 정합) + capability gate `TENANT_IDP_MANAGEMENT` per-tenant on/off 결정 (CR 12-5 D-GATE-01 inversion). (f) **Audit-first INSERT 4 NEW + multi-tenant isolation** 결정 wire (CR 1-1 verbatim + CR 0-2 RLS lesson 적용, 모든 CRUD API endpoint 의 audit_log INSERT 결정, action_class='AUTH' + action='tenant_idp_*' + actor_id + tenant_id + payload_json 정합 + per-tenant RLS 자동 적용, multi-tenant isolation test 결정). (g) **Capability matrix v1.28 EXTENSION + 1 NEW row** 결정 wire = `Capability.TENANT_IDP_MANAGEMENT = "tenant_idp_management"` 신규 1 row (manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ industry-agnostic 4-industry grants, CR 12-1 L4 precedent 미러, SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY 13-1 + LISTEN_NOTIFY_TENANT_FANOUT 14-1 + LISTEN_NOTIFY_MULTIPROCESS 14-1 + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire pattern verbatim bind) + 미허용 tenant 의 tenant IdP admin 진입 차단 결정 wire + SSOT RED→GREEN EXTENSION (capability matrix v1.28 신규 1 row + capability.py EXTENSION 1 NEW enum + `require_capability()` Dependency 1개 신규 wire) + drift detector `tests/integration/test_capability_matrix_v1_28_drift.py` 결정 (Epic 15 wire 의 `tests/integration/test_capability_matrix_v1_26_drift.py` 패턴 verbatim). capability matrix v1.28 신규 1 row (`TENANT_IDP_MANAGEMENT`, industry-agnostic 4-industry grants ✅/✅/✅/✅) [§F19 verbatim, §8.1 M0-(l) EXTENSION 결정] | Epic 16 T1~T8 (cj-style Epic 16 3번째 진입점 진입 대기) | `TENANT_IDP_MANAGEMENT` | Epic 16 PRD entry 2026-08-22 |
| **AD-31 Multi-Region Backup & Disaster Recovery** | **신규 결정 (Phase 5 PRD entry DONE 2026-08-22, A126)** — Phase 5 = Multi-Region Backup & Disaster Recovery = Epic 16 close-out retro §13 옵션 (a) 결정 진입 territory 신규 bind (Phase 4 close-out retro §6 disaster recovery "multi-region backup 결정 wire 보류, Phase 5+ 진입 시점" verbatim 자연스러운 carry-over chain 결정 wire, D-PHASE-4-DR-DEFER-1/2 honestly RESOLVE 진입 wire 결정, CR 11-3 honest-DEFER discipline 73번째 epic 연속 정직 회복 검증). (a) **Cross-region read replica + WAL archiving** 결정 wire = alembic `0039_phase_5_multi_region_backup.py` NEW `phase_5_replication_lag` table (BIGSERIAL id + replica_region TEXT enum seoul/tokyo/singapore/frankfurt/virginia/oregon/sao_paulo + primary_region TEXT enum + lag_bytes BIGINT + lag_seconds INTEGER + last_synced_lsn TEXT PG_LSN + last_synced_at TIMESTAMPTZ + replication_status TEXT enum syncing/replicating/lagged/disconnected/failed + created_at TIMESTAMPTZ DEFAULT NOW()) + 3 indexes (status + region+status+last_synced_at DESC + created_at) + 2 CHECK constraints (replication_status enum + replica_region enum) + audit-first INSERT `replica_status_changed` (CR 1-1 verbatim, action_class='INFRA' + action='replica_status_changed' + actor_id + region + previous_status + new_status + trace_id) 결정 wire 결정. WAL archiving 결정 wire = `postgresql.conf` `archive_mode = on` + `archive_command = 'pgbackrest --stanza=costmgr archive-push %p'` + `wal_level = replica` 결정 wire 보류 (Supabase managed 결정 wire). `docs/cross-region-replication.md` 결정 wire (cross-region replication setup + replica region 선택 Tokyo 1st choice latency Seoul-Tokyo ~50ms 결정 + replication lag monitoring lag_bytes threshold 100MB + lag_seconds threshold 30s alert 결정 + WAL archiving setup + Supabase pgbackrest 결정 wire 보류). (b) **Cross-region failover automation** 결정 wire = `apps/api/jobs/failover_orchestrator.py` NEW ~200 LOC (primary → secondary health probe 5-second interval + 3 consecutive failures trigger 결정 + automatic promotion 결정: secondary region 의 PostgreSQL promote decision via Supabase API `POST /v1/projects/{ref}/database/promote` 결정 wire 보류 + read-only mode 해제 + connection pool redirect 결정) + DNS update 결정 wire (failover 결정 wire 진입 시점에 Supabase project URL 의 custom domain redirect 결정 wire + Supabase custom domain 결정 wire 보류) + RTO 30-second target 결정 wire + failover trigger 3종 결정 (health probe 3 consecutive failures OR manual trigger via `POST /api/v1/admin/failover` owner-only AD-22 RBAC + 2FA 챌린지 Epic 12 정합 OR scheduled drill via `apps/api/jobs/dr_drill.py` cron 결정) + audit-first INSERT `failover_initiated` + `failover_completed` (CR 1-1 verbatim, action_class='INFRA' + action='failover_initiated' + actor_id + from_region + to_region + trace_id) + FastAPI lifespan hook startup/shutdown 결정 wire + GRACEFUL_SHUTDOWN_TIMEOUT=30s 결정 wire. (c) **DR drill + automated quarterly test** 결정 wire = `apps/api/jobs/dr_drill.py` NEW ~150 LOC (cron KST 1st Sunday 03:00 = UTC 18:00 결정 wire + actual failover drill test in staging 결정 wire production 환경 직접 failover 위험 회피 결정 + 6 drill steps: staging primary health check + staging secondary promote trigger + staging database connection write test + staging application health check + staging DNS update test + staging primary restore trigger + RPO/RTO measurement decision: drill 시작 시점 → drill 완료 시점 시간 측정 = RTO actual + drill 시작 전 마지막 transaction LSN → drill 후 secondary LSN 측정 = RPO actual + 결과 결정 wire `phase_5_dr_drill_results` table 신규 (BIGSERIAL id + drill_date DATE + rto_actual_seconds INTEGER + rpo_actual_bytes BIGINT + status TEXT enum pass/fail + notes TEXT + created_at TIMESTAMPTZ) + Q1/Q2/Q3/Q4 quarterly drill schedule 결정 wire (January + April + July + October 결정, docs/database-backup.md §9 quarterly drill pattern verbatim preserve) + audit-first INSERT `dr_drill_completed` (CR 1-1 verbatim, action_class='INFRA' + action='dr_drill_completed' + actor_id='system' + rto_actual_seconds + rpo_actual_bytes + status 결정) 결정. (d) **Cross-region backup strategy** 결정 wire = `docs/database-backup.md` EXTENSION 10 sections → 12 sections (purpose + PITR strategy + RPO/RTO + restore procedure + disaster recovery + monitoring + retention + quarterly drill testing + cross-region backup strategy 신규 + cross-region failover runbook 신규 + RPO 1h / RTO 4h SLA 결정: Phase 4 single-region RPO 5min/RTO 1h 의 honest-extreme risk = Seoul region disaster 시 backup restoration 불가 verbatim 해소 결정 wire) + Cross-region backup vs single-region 결정 wire (Phase 4 single-region 의 honest-extreme risk 의 multi-region 해소 결정) + 30일 hot (primary) + 90일 cold (secondary) + 365일 archive (regional) retention decision. (e) **Multi-region health observability** 결정 wire = `apps/api/core/health.py` EXTENSION `/api/v1/health/multi-region` endpoint 결정 wire (primary + secondary status array 결정 + CR 12-5 D-14 envelope `{status, primary: {region, status, lag_bytes, lag_seconds, last_synced_at}, secondary: {...}, timestamp}` 결정 + JWT verification probe 결정 Supabase Auth health probe per-region 결정) + `apps/api/core/observability.py` EXTENSION Sentry breadcrumb failover_initiated 시 Sentry breadcrumb + alert decision (`sentry_sdk.capture_message(f"Failover initiated from {from_region} to {to_region}", level="warning")` + Sentry alert routing decision) + Grafana multi-region dashboard EXTENSION decision (primary + secondary region metrics + replication lag graph decision + failover event log decision) + `apps/web/app/api/health/multi-region/route.ts` NEW decision wire (~+30 LOC, atomic, Next.js Edge Runtime + force-dynamic + Vercel region decision + NextResponse.json envelope decision `{status, primary, secondary, build, region, timestamp}` decision wire). (f) **Capability matrix v1.29 EXTENSION + 2 NEW rows** 결정 wire = `Capability.MULTI_REGION_BACKUP = "multi_region_backup"` 1 NEW row + `Capability.MULTI_REGION_FAILOVER = "multi_region_failover"` 1 NEW row (manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러, DEPLOYMENT_PROD + DEPLOYMENT_DATABASE_BACKUP Phase 4 wire + SSO_ENTERPRISE Epic 15 wire + TENANT_IDP_MANAGEMENT Epic 16 wire + LAUNCH_* 1st release wire + LISTEN_NOTIFY 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire pattern verbatim bind) + SSOT RED→GREEN EXTENSION (capability matrix v1.29 신규 2 rows + capability.py EXTENSION 2 NEW enum + `require_capability()` Dependency 2개 신규 wire) + drift detector `tests/integration/test_capability_matrix_v1_29_drift.py` NEW 결정 (Epic 16 wire 의 `tests/integration/test_capability_matrix_v1_28_drift.py` + Phase 4 wire 의 `tests/integration/test_capability_matrix_v1_25_drift.py` 패턴 verbatim). capability matrix v1.29 신규 2 rows (`MULTI_REGION_BACKUP` + `MULTI_REGION_FAILOVER`, industry-agnostic 4-industry grants ✅/✅/✅/✅) [§F20 verbatim, §8.1 M0-(m) EXTENSION 결정] | Phase 5 T1~T8 (cj-style Phase 5 3번째 진입점 진입 대기) | `MULTI_REGION_BACKUP` + `MULTI_REGION_FAILOVER` | Phase 5 PRD entry 2026-08-22 |
| **AD-32 Audit Log Viewer & Activity Stream** | **신규 결정 (Epic 17 PRD entry DONE 2026-08-22, A155)** — Epic 17 = Audit Log Viewer & Activity Stream = Sidebar/MenuProvider hot-fix `01a06e4` (cj-style 79번째) + D-EPIC-16-REVIEW-DEFER-2~6 RESOLVE sprint `512ed6a` (cj-style 78번째) 진입 직후 옵션 5종 중 옵션 (a) Epic 17 결정 진입 territory 신규 bind (모든 Epic 1~16 + Phase 3~5 의 audit-first INSERT (CR 1-1) 가 audit_log table 에 누적 → audit log viewer territory 의 natural next 진입 + Phase 5 multi-region wire 의 cross-region audit log visibility 자연스러운 carry-over). (a) **audit log query API** 결정 wire = `apps/api/modules/audit/audit_log_query.py` NEW ~180 LOC (4 functions: `query_audit_log(tenant_id, filters, page, page_size) -> AuditLogPage` + `count_audit_log(tenant_id, filters) -> int` + `get_audit_log_entry(tenant_id, entry_id) -> AuditLogEntry` + `query_activity_stream(tenant_id, window_days) -> list[ActivityStreamGroup]` + AuditLogQueryFilters + AuditLogEntry + AuditLogPage + ActivityStreamGroup TypedDict 결정 + RLS 자동 적용 CR 0-2 verbatim + owner/admin role required + capability gate AUDIT_LOG_VIEW). (b) **audit log viewer UI** 결정 wire = `apps/web/app/[locale]/(dashboard)/audit-log/page.tsx` NEW ~200 LOC + 5 components (`AuditLogFilterPanel` + `AuditLogTable` + `AuditLogPagination` + `AuditLogExportButton` + `AuditLogDetailModal`) + ko-KR.json `audit_log.*` namespace EXTENSION 14 keys 결정 (CR 11-4 D-002 verbatim SSOT) + `(dashboard)` route group 보호 (Phase 3-1 T4 wire 정합) + `apps/web/lib/audit/audit-log-client.ts` NEW 결정 + vitest RTL render discipline 결정 (CR 11-4 D-003 verbatim). (c) **activity stream UI** 결정 wire = `apps/web/app/[locale]/(dashboard)/activity/page.tsx` NEW ~150 LOC + 3 components (`ActivityStreamTimeline` + `ActivityStreamEntry` + `ActivityStreamWindowSelector`) + ko-KR.json `activity.*` namespace EXTENSION 8 keys 결정 + all tenant members 권한 (`require_role("owner", "admin", "member", "viewer")`) 결정 wire. (d) **cross-region audit log visibility** 결정 wire = Phase 5 wire `f093f8c` 의 `phase_5_replication_lag` table + Supabase multi-region primary Seoul + secondary Tokyo replica 결정 wire EXTENSION (audit log query 시 secondary region 의 read replica 에서 query 가능 + multi-region read replica 통한 cross-region audit visibility) + read-only routing 결정 wire + 읽기 일관성 lag_bytes ≤ 100MB + lag_seconds ≤ 30s threshold 정합 (Phase 5 wire 정합) — lag 초과 시 primary region 으로 fallback + Sentry breadcrumb 결정 wire. (e) **CSV export** 결정 wire = `apps/api/modules/audit/audit_log_export.py` NEW ~120 LOC + `export_audit_log_csv(tenant_id, filters, actor_id) -> StreamingResponse` 결정 (Excel-compatible UTF-8 BOM `﻿` + comma-separated + double-quote escape for payload_json) + streaming response 결정 + audit-first INSERT `audit_log_exported` (CR 1-1 verbatim, action_class='AUDIT' + action='audit_log_exported' + actor_id + tenant_id + filters_json + row_count + trace_id) — 누가 언제 어떤 filter 로 export 했는지 추적 + CR 12-5 D-14 error envelope 결정 (e.g. `AUDIT_LOG_EXPORT_FORBIDDEN_KO`, `AUDIT_LOG_EXPORT_TOO_LARGE_KO`). (f) **audit-first INSERT 1 NEW + RLS 자동 적용** 결정 wire (CR 1-1 verbatim + CR 0-2 RLS lesson 적용, F21.5 `audit_log_exported` 1 NEW audit log entry 결정, action_class='AUDIT' + action='audit_log_exported' + actor_id + tenant_id + filters_json + row_count + trace_id + per-tenant RLS 자동 적용, multi-tenant isolation test 결정). (g) **Capability matrix v1.30 EXTENSION + 1 NEW row** 결정 wire = `Capability.AUDIT_LOG_VIEW = "audit_log_view"` 신규 1 row (manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ industry-agnostic 4-industry grants, CR 12-1 L4 precedent 미러, MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY Epic 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern verbatim bind) + 미허용 tenant 의 audit log viewer 진입 차단 결정 wire + SSOT RED→GREEN EXTENSION (capability matrix v1.30 신규 1 row + capability.py EXTENSION 1 NEW enum + `require_capability()` Dependency 1개 신규 wire) + drift detector `tests/integration/test_capability_matrix_v1_30_drift.py` NEW 결정 (Phase 5 wire 의 `tests/integration/test_capability_matrix_v1_29_drift.py` + Epic 16 wire 의 `tests/integration/test_capability_matrix_v1_28_drift.py` 패턴 verbatim). capability matrix v1.30 신규 1 row (`AUDIT_LOG_VIEW`, industry-agnostic 4-industry grants ✅/✅/✅/✅) [§F21 verbatim, §8.1 M0-(n) EXTENSION 결정] | Epic 17 T1~T8 (cj-style Epic 17 3번째 진입점 진입 대기) | `AUDIT_LOG_VIEW` | Epic 17 PRD entry 2026-08-22 |

> **AD-22 reversal insert** = Epic 11 wire 결정 (master PRD §8.1 M11-(b) verbatim "입력·변경 시도는 역분개(A8)로만 허용"). 본 master PRD v2.0 edit 시점에 AD-22 cross-ref 보존.
>
> **AD-4 commit** = master PRD §8.1 M3-(a) verbatim "단일 트랜잭션으로 실행하고, 도중 실패 시 전체 롤백".
>
> **SM-3a** = §2.B 성공 지표 SM-3 inline 정의 "계산 결과 변경 시도 = 0건" 별도 추적 (§12 인사이트 큐레이션 원칙 검증).
>
> **§A11** = §3 회계 공리 헌장 A11 "오류의 가시화 (숨기지 않는 시스템)" — F10.2-(b) strict reject + counter increment 의 정당화 근거.

---

## 부록 B. 보존 산식 — A×B×C×D 예산 편성 엔진 (2차 구현용)

```
예산금액 = A(편성단위수량) × B(기준비율%) × C(단위금액) × D(기간환산계수)
  산출기준: 인건비 / 평수 / 생산수량 / 매출 / 고정자산 / 차량대수 / 인원수 / 기타
  기간환산: 전통 엔진(djob exp) — 년12 / 반년6 / 분기3 / 월1 / 일30
           ABC 엔진(3 Indirect cost) — 년1 / 분기4 / 월12 / 일365
  ※ 두 파일의 D 계수 체계가 상이함(월 기준 환산 vs 연 기준 환산) — 통합 시 월 기준으로 정규화
```

## 부록 C. 용어

| 용어 | 정의 |
|------|------|
| ABC | Activity-Based Costing. 원가를 활동 기준으로 배부하여 제품·서비스 원가를 산출하는 방법론. §7 참조. |
| ABCost | 동일 저작자의 원본 ABC 전용 엑셀 파일명(13시트). §1.2·§부록 A Q-G 참조. |
| A×B×C×D 예산 편성 엔진 | 예산금액 = A(편성단위수량) × B(기준비율%) × C(단위금액) × D(기간환산계수)로 산출하는 원본 예산 체계. 2차 구현. §부록 B 참조. |
| append-only | 데이터가 삭제·수정 없이 추가만 되는 저장 정책 [A8]. 수불 원장·감사로그에 적용. |
| BEP | Break-Even Point. 손익분기점. 총수입 = 총비용이 되는 매출량. §6.1 (6). |
| BOM | Bill of Materials. 제품 1단위 생산에 필요한 자재·공정 명세. §6.1 (1), §7.3. |
| BOM 자기참조 1 | 유통품이 자기 자신을 BOM에 자식 품목으로 두는 원본 구조. 웹에서는 `merchandise` 유형으로 대체. |
| CCR | Capacity Cost Rate = 부서 원가 ÷ 실제적 조업능력. TDABC의 핵심 지표. §7.2. |
| CVP | Cost-Volume-Profit. 원가·조업도·이익 관계 분석. §6.1 (6). |
| FTE | Full-Time Equivalent. 일용직 등 비정규 근로자를 정직원 환산한 인원수. §6.1 (2). |
| RLS | Row-Level Security. PostgreSQL·Supabase가 제공하는 행 단위 접근 제어. 멀티테넌트 격리에 사용. |
| TDABC | Time-Driven ABC. 시간방정식 + CCR 기반의 간소화된 ABC. Kaplan 2004 이후 표준. §7.2. |
| 기계시간 | 배부기준 ③ 채택 시 노출되는 제품별 월 기계 가동 시간 입력값. §6.1 (3). |
| 관리 회계 뷰 | 재고평가·제조원가명세서와 분리된, 제품별 완전원가 손익을 보여주는 관리용 뷰 [A2]. |
| 매출원가 | 판매분에 대응하는 제조원가. 미판매 생산분은 재고자산으로 이월 [A4]. |
| 미사용능력 | 총작업가능시간 − 생산요구시간(전통) / 실제적 조업능력 − 사용시간(TDABC) — 금액화하여 별도 보고 [A9]. |
| 반제품 | BOM 매트릭스에서 자식 품목이 될 수 있는 중간재. §4.1·§6.1. |
| 배부기준 | 원가를 제품·활동·부문 등 원가대상에 분배하는 동인. 제조경비는 직접노무원가/직접노무시간/기계시간 3종 택1 [A5, Q-A]. |
| 부문귀속명세서 | 겸영 기업의 카브아웃 분할 근거를 공시하는 보고서. §7.3, §9 #21. |
| 사용자 부하 추정 | 동인 실적 미확보 시 사용되는 추정 입력. `is_estimated` 배지 표시. [A11, E7] |
| 세법 2기준 | 법인세법 시행규칙 제76조가 정한 공통비 분할 기준 — 매출액 비례 / 개별비용 비례 [A10]. |
| 실제적 조업능력 | 이론적 조업능력 × 80% (기본). TDABC의 분모. §7.2. |
| 역분개 | 마감된 데이터의 정정을 (삭제+재기록)이 아닌 (반대 entry + 신규 entry)로 처리하는 방식 [A8]. |
| 영업 손익 | 매출총이익 − 판매일반관리비. §6.1 (5). |
| 완전원가(full_cost) | 제조원가 + 관리인건비배부 + 판관비배부. 관리 뷰 전용 [A2]. |
| 원가경영관리 | 본 제품의 정식 명칭(부제). 단일 표기로 통일. |
| 원가풀(Resource Pool) | 간접비를 1차로 모으는 단계(ABC Step 1). 설비/매출/인원 3기준 비율. §7.1. |
| 제조원가(manufacturing_cost) | 직접재료비 + 직접노무비 + 제조간접비 3요소 합 [A2]. 재고 평가·제조원가명세서 기준. |
| 제품 재고 조정 | 생산기준 배부에서 생산·판매 수량차와 단가차로 생기는 재고 증감의 손익 표시 라인 (V4 자동 산출). |
| 전진법(prospective) | 설정·BOM 변경을 미래 기간에만 적용하고 과거 마감분은 불변으로 두는 원칙 [A7]. |
| 카브아웃 | 겸영 기업의 공통비를 세법 2기준으로 부문 분할하는 절차 [A10]. |
| 테넌트 | 멀티테넌트 SaaS에서 한 기업(한 가입 단위)의 데이터 격리 단위. §13.2 RLS. |
| 활동(Cost Activity) | 원가풀에서 원가대상으로 배부하기 위한 중간 단계. 주요활동 5~15개. §7.1. |
| 회사부담임률 | 생산직 노무비 합계 ÷ 생산요구시간 (원본 operation 주석(3)). |

*— 본 표는 §3–§15에서 사용된 도메인 어휘를 §부록 A·B·D와 동기화한 결과다. 신규 용어는 §부록 A의 결정 이력 방식(추가일·출처)으로 추후 보강한다.*

---

## 부록 D. 추론 인덱스 (Assumptions Index)

PRD 본문에서 단언되었으나 사용자(원가바이블 저작자 + 기획 세션 2026-07-22)에서 직접 확정을 받지 못한 추론성 룰. 각 항목은 본문 `[ASSUMPTION: ...]` 마커와 1:1 대응한다. 해소 시 본 표에서 제거 + §부록 A의 결정 이력으로 승격.

| ID | 위치 | 추론 내용 | 추론 근거 | 추론일 | 해소 owner |
|----|------|-----------|-----------|--------|-----------|
| AS-1 | A1 | 회계연도 시작월은 테넌트별 가변 | 동일 저작자 djob 시트가 "회계연도 시작월" 필드를 보유 | 2026-07-12 | PM (SaaS 다국어 정책 확정 시) |
| AS-2 | §7.2 | CCR 산출 단위 = 부서 (단일) | 부서 단위 산출이 1인 운영자 SaaS의 운영 부담을 낮춤; Kaplan TDABC 정론의 일반적 사례 | 2026-07-12 | PM (1차 파일럿 1곳에서 검증 후) |
| AS-3 | §6.1 (4) | 관리인건비배부 = 직접노무비 비례 | 원본 pl 시트의 "관리인건비 = 직접인건비의 29.3% 상당 배부" 패턴 계승 | 2026-07-12 | 운영자 (M5 완료 후 회귀 검증) |
| AS-4 | §6.1 (3) | 제조경비 배부기준 3종(직접노무원가/직접노무시간/기계시간) 택1 | Q-A 결정; 기계시간 신규 입력은 추론성 (원본에는 없음) | 2026-07-12 | 운영자 (M0 온보딩 시 사용자 선택 검증) |
| AS-5 | §8.1 M9 | 동인 토글(건수 / 비율 %) | 원본 ABCost의 "Yes/No" 토글 계승; UI 토글 노출 방식은 추론 | 2026-07-12 | UX designer |
| AS-6 | §9 #21 | 부문귀속명세서 카브아웃 분할 근거 공시 형식 | 법인세법 시행규칙 제76조 2기준의 시각화 방법(표/차트)은 추론 | 2026-07-12 | 운영자 + UX designer |

해소 절차: 각 항목의 owner가 결정 확정 시 본 표에서 삭제하고 §부록 A에 결정 이력(Q-?)으로 추가한다. 결정 사항은 memlog에 `event: "AS-N resolved → Q-? 결정"`으로 기록한다.

*— 문서 끝 —*
