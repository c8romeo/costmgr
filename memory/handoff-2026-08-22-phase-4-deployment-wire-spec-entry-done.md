---
name: handoff-2026-08-22-phase-4-deployment-wire-spec-entry-done
description: Phase 4 bmad-create-story spec entry DONE (cj-style Phase 4 2번째 진입점 = cj-style 54번째 epic 연속 정직 회복 bmad-create-story). sprint-status phase-4-deployment-wire: open → ready-for-dev. PRD §F16 verbatim 9 ACs + 8 tasks T1~T8 결정 wire 진입 보존. A19 cohesion 9 surface EXTENSION PASS 결정 (deployment surface NEW).
metadata:
  type: project
---

# Phase 4 bmad-create-story spec entry DONE — Deployment config + Dockerfile territory (handoff-2026-08-22)

## 결정 wire (2026-08-22)

Phase 4 bmad-create-story spec entry DONE (cj-style Phase 4 2번째 진입점 = cj-style 54번째 epic 연속 정직 회복 bmad-create-story 진입 결정).

- baseline_commit = `8e046df` (Phase 4 PRD entry wire tip = cj-style Phase 4 1번째 진입점 = cj-style 53번째)
- spec = `_bmad-output/implementation-artifacts/phase-4-deployment-wire.md` (NEW, ~600+ lines)
- sprint-status: `phase-4-deployment-wire: open → ready-for-dev`
- spec file = PRD §F16 verbatim 9 ACs + 8 tasks T1~T8 결정 보존

## Phase 4 wire scope T1~T8 결정 (cj-style 54번째 epic 연속 정직 회복 spec 진입 시점에 결정)

- **T1 Vercel config wire** (1 NEW) = `vercel.json` (Vercel frontend deployment config ~+80 LOC, framework=nextjs + regions=[icn1] Seoul + buildCommand=`pnpm --filter web build` + installCommand=`pnpm install --frozen-lockfile` + outputDirectory=`apps/web/.next` + env NEXT_PUBLIC_SUPABASE_URL/ANON_KEY/API_BASE_URL + CSP/X-Frame-Options/HSTS headers + legacy `/ko-KR/*` → `/ko/*` redirects)
- **T2 Railway config wire** (1 NEW) = `railway.toml` (Railway backend deployment config ~+60 LOC, builder=DOCKERFILE + dockerfilePath=`apps/api/Dockerfile` + healthcheckPath=`/api/v1/health` + healthcheckTimeout=300 + restartPolicyType=ON_FAILURE + restartPolicyMaxRetries=3 + env DATABASE_URL/SUPABASE_JWT_SECRET/URL/ANON_KEY/SERVICE_ROLE_KEY/SENTRY_DSN/ENVIRONMENT=production)
- **T3 Per-app Dockerfile wire** (2 NEW) = `apps/web/Dockerfile` (~+40 LOC, node:20-bookworm-slim + Next.js standalone output build + pnpm install --frozen-lockfile + pnpm --filter web build + CMD ["node", "apps/web/server.js"]) + `apps/api/Dockerfile` (~+50 LOC, python:3.12-slim + FastAPI production server + pip install --no-cache-dir + uvicorn + 멀티 stage build) — **AD-14 stack pin by @sha256: digest**
- **T4 Deployment runbook wire** (1 NEW) = `docs/deployment.md` (12 sections: purpose + architecture + prerequisites + step-by-step deployment guide + env vars SSOT + health check + monitoring + database backup + restore + rollback strategy + smoke test + troubleshooting + security + cost estimation)
- **T5 Health check + observability wire** (3 NEW + 1 MODIFIED) = `apps/api/core/health.py` NEW (~+60 LOC, GET /api/v1/health + DB connectivity check + Supabase connection check + JWT verification + liveness/readiness 분리) + `apps/api/core/observability.py` NEW (~+40 LOC, Sentry FastAPI integration + FastAPI middleware + SQLAlchemy integration) + `apps/web/lib/observability/sentry.ts` NEW (~+40 LOC, Sentry browser integration + SSR-safe initialization + session replay) + `apps/api/main.py` MODIFIED (health router include) + `apps/web/app/api/health/route.ts` NEW (~+30 LOC, Next.js health check route handler)
- **T6 Database backup strategy wire** (1 NEW alembic + 1 NEW docs) = `apps/api/alembic/versions/0036_phase_4_backup_strategy.py` NEW (~+80 LOC, phase_4_backup_strategy table + id + backup_type + started_at + completed_at + size_bytes + checksum_sha256 + storage_url + status + created_at + down_revision=`0035_custom_access_token_hook`) + `docs/database-backup.md` NEW (~+200 LOC, RPO=5분 + RTO=1시간 + daily 자동 + weekly 수동 검증 + retention policy)
- **T7 Capability v1.25 EXTENSION** (1 MODIFIED + 1 NEW) = `apps/api/core/capability.py` MODIFIED (4 NEW enum: `DEPLOYMENT_PROD` + `DEPLOYMENT_STAGING` + `DEPLOYMENT_DATABASE_BACKUP` + `DEPLOYMENT_HEALTH_CHECK`, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러) + `docs/capability-matrix.md` v1.24 → v1.25 (4 NEW rows 이미 추가됨, capability.py enum 만 wire) + `tests/integration/test_capability_matrix_v1_25_drift.py` NEW (drift detector — SSOT 정합 sweep)
- **T8 Tests + 3중 게이트 FINAL CLEAN** (~+40 NEW pytest PASS + ~+20 NEW vitest PASS + 2 NEW docs): `tests/api/core/test_phase_4_vercel_config.py` 10 + `tests/api/core/test_phase_4_railway_config.py` 8 + `tests/api/core/test_phase_4_dockerfile_parity.py` 12 + `tests/api/core/test_phase_4_health_check.py` 10 + `tests/web/test_phase_4_sentry_integration.test.ts` 10 + `tests/web/test_phase_4_vercel_health.test.ts` 10 + `tests/api/core/test_phase_4_alembic_0036_backup.py` 10 + `tests/integration/test_capability_matrix_v1_25_drift.py` drift detector = ~70 NEW test cases

## 9 ACs satisfied (PRD §F16.1~F16.7 verbatim)

PRD §F16.1 (Vercel frontend deployment config — vercel.json + framework=nextjs + regions=[icn1] + env 매핑 + headers/redirects 결정) / §F16.2 (Railway backend deployment config — railway.toml + builder=DOCKERFILE + healthcheckPath + restartPolicyType 결정) / §F16.3 (Per-app Dockerfile 분리 — apps/web/Dockerfile + apps/api/Dockerfile, AD-14 digest pin 결정) / §F16.4 (Deployment runbook — docs/deployment.md 12 sections 결정) / §F16.5 (Health check + observability — /api/v1/health + Sentry browser/server + Next.js /api/health 결정) / §F16.6 (Database backup strategy — alembic 0036 + phase_4_backup_strategy table + docs/database-backup.md 결정) / §F16.7 (Capability matrix v1.24 → v1.25 EXTENSION 4 NEW rows 결정) / §F16.8 (D-1-1-DEFER-* honestly preserved 53번째 epic 연속 CR 11-3 정직 회복 검증) / §F16.9 (A19 cohesion pattern 9 surface EXTENSION PASS deployment surface NEW).

## A19 cohesion pattern 9 surface EXTENSION PASS 결정

- **Surface 1 (kernel)** = T1+T2 vercel.json/railway.toml config parsers (Pydantic BaseModel validation, JSON/TOML schema 검증)
- **Surface 2 (port)** = T3 apps/web/Dockerfile + apps/api/Dockerfile (per-app deployment adapter, AD-14 digest pin 결정)
- **Surface 3 (db schema)** = T6 alembic 0036 phase_4_backup_strategy table (id + backup_type + started_at + completed_at + size_bytes + checksum_sha256 + storage_url + status + created_at)
- **Surface 4 (service)** = T5 health.py + observability.py + sentry.ts (health check service + Sentry observability)
- **Surface 5 (handler)** = T5 /api/v1/health FastAPI endpoint + T5 /api/health Next.js route handler
- **Surface 6 (envelope)** = T5 health response `{status, timestamp, version, database, redis, uptime_seconds}` 결정
- **Surface 7 (capability)** = T7 DEPLOYMENT_PROD + DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP + DEPLOYMENT_HEALTH_CHECK 4 NEW gates (industry-agnostic)
- **Surface 8 (audit)** = T6 backup_created audit_logs INSERT 결정 (CR 1-1 audit-first INSERT)
- **Surface 9 (deployment) NEW** = T1+T2+T3+T4+T5+T6 deployment config + health check + observability + database backup 결정

## 3중 게이트 impact EXPECTED (Phase 4 atomic sprint wire 진입 시점)

- (1) frontend `pnpm tsc --noEmit` 0 NEW errors (deployment files clean — pre-existing 7 baseline errors unrelated 보존)
- (2) `pnpm vitest run` 716+20 = **~736/736 PASS** (71+2 = 73 files, Phase 4 +20 NEW cases, 0 regressions)
- (3) `ruff check` scoped Phase 4 wire files = **All checks passed!**
- (4) `pytest` 31+40 = **~71/71 PASS** (Phase 4 +40 NEW e2e tests, 0 NEW regressions; baseline 1 unrelated pre-existing failure `test_generate_report_pdf_report15_payload_not_required` 보존)
- (5) SDR drift gate PASS (MAX claim 3855 → **~3895** actual pytest --collect-only -q = +40 from Phase 4 T8 NEW pytest cases)
- (6) commit_consistency gate PASS (CR 9-6 commit message discipline + A36 SDR 검증 4-step 자동 적용)

## 기존 baseline 정합 보존 (Phase 4 PRD entry 진입 시점에 cj-style "fix" 종류 pre-flight 정합 sweep)

- **Root `Dockerfile`** (multi-stage 4-stage: frontend-builder → backend-builder → backend-runtime + frontend-runtime, AD-14 stack pin by @sha256: digest 모든 베이스 이미지 결정, pnpm@10 + Python 3.12-slim, `--frozen-lockfile` 결정)
- `docker-compose.yml` (postgres only, port 54322 → host 54322 매핑, healthcheck 결정)
- `.github/workflows/ci.yml` (lint-deps + lint-imports + lint-conventions + stack-pin-check + commit-prefix-lint + test-architecture + test-service-role-guard + service-role-guard-lint + rls-tests + web-test + web-e2e + smoke-e2e 결정, 12 step decisions)

## CR lessons applied (cj-style 54번째 epic 연속 정직 회복 wire 진입 시점에 결정)

- **CR 0-2** RLS lesson ✅ APPLIED (Phase 3-0 atomic sprint `1db21d2` 정합)
- **CR 1-1** audit-first INSERT ✅ APPLIED (T6 backup_created audit log INSERT + Phase 3-0 tenant_signup_completed + T5 user_logged_out + T6 password_reset 보존)
- **CR 9-6** commit message discipline ✅ APPLIED (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention)
- **CR 11-3** honest-DEFER discipline ✅ APPLIED (54번째 epic 연속 정직 회복 — D-1-1-DEFER-1/2/3 honestly preserved)
- **CR 12-1** L4 industry-agnostic capability ✅ APPLIED (capability matrix v1.25 EXTENSION 4 NEW rows industry-agnostic 4-industry grants)
- **CR 12-5** D-14 typed exception envelope ✅ APPLIED (health check response envelope + ko-KR error messages)
- **CR 12-5** D-PARITY-01 inversion ✅ APPLIED (Vercel + Railway + Supabase URL parity + env vars parity)
- **A19** cohesion pattern 9 surface EXTENSION PASS ✅ (deployment surface NEW)
- **A36** SDR 검증 4-step 자동 적용 ✅ (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS)

## D-1-1-DEFER-* honestly preserved (CR 11-3 54번째 epic 연속)

| DEFER ID | Description | 상태 |
|----------|------------|------|
| **D-1-1-DEFER-1** | Magic link login | 🔵 OPEN (A70 결정 wire, Epic 15+ 진입 시점) |
| **D-1-1-DEFER-2** | Social login OAuth (Google/Naver/Kakao) | 🔵 OPEN (A71 결정 wire) |
| **D-1-1-DEFER-3** | SSO enterprise SAML | 🔵 OPEN (A72 결정 wire) |

CR 11-3 honest-DEFER discipline 54번째 epic 연속 정직 회복 결정. grep guard `test_no_magic_link_or_oauth_or_sso_introduced` 보존.

## 결정 wire 일자

2026-08-22 (KST)

## Related Memories

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

## next: Phase 4 bmad-dev-story atomic wire T1~T8 진입

`bmad-dev-story phase-4-deployment-wire` 진입 시점에 PRD §F16 verbatim + A73+A74+A76+A77+A78 결정 wire 보존 = cj-style Phase 4 3번째 진입점 = cj-style 55번째 epic 연속 정직 회복 atomic single sprint = ~40 NEW pytest PASS + ~20 NEW vitest PASS + 0 NEW ruff + 0 regressions + A19 cohesion 9 surface EXTENSION PASS + 3중 게이트 FINAL CLEAN.

**cj-style 54번째 epic 연속 정직 회복 검증 완료**.