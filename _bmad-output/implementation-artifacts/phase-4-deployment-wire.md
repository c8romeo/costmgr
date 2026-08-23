---
baseline_commit: 8e046df
---

# Story phase-4.1: Deployment Config Wire (Phase 4 cj-style 2번째 진입점)

Status: in-progress

<!-- Phase 4 cj-style 2번째 진입점 = cj-style 54번째 epic 연속 정직 회복 bmad-create-story spec.
     Phase 4 PRD entry (`phase-4-prd-entry: done`, 2026-08-22, commit `8e046df`) 직후.
     master PRD v3.1 §F16 verbatim + AD-27 verbatim + A73+A74+A76+A77+A78 결정 wire.
     T1~T8 wire scope (Deployment config + Dockerfile + health check + observability + database backup territory) + D-1-1-DEFER-1/2/3 honestly DEFER preserved (53번째 epic 연속). -->

## Story

As a **costmgr product owner**,
I want the **Deployment config + Dockerfile + health check + observability + database backup territory fully wired end-to-end with Vercel frontend + Railway backend + Supabase PostgreSQL production + Sentry observability**,
so that **Phase 4 territory 가 wire 되어 production deployment 가능 + health check 응답 envelope 정합 + database backup 자동화 + capability matrix v1.25 EXTENSION 4 NEW rows industry-agnostic 4-industry grants 가 production-grade 로 동작**합니다.

## Acceptance Criteria

PRD §F16.1 ~ §F16.6 verbatim + §F16.7 T1~T8 wire scope verbatim.

### F16.1 Vercel frontend deployment config

- [ ] **AC1.1** Root `vercel.json` NEW (~+80 LOC, atomic) — Vercel frontend deployment config: `framework = "nextjs"` + `buildCommand = "pnpm --filter web build"` + `installCommand = "pnpm install --frozen-lockfile"` + `outputDirectory = "apps/web/.next"` (monorepo 경로 정합) + `regions = ["icn1"]` (Seoul region 결정 wire, NFR16 latency 요구사항 정합). Vercel project = `costmgr` (단일 monorepo) 결정.
- [ ] **AC1.2** `env` 매핑 결정 (`NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY` + `NEXT_PUBLIC_API_BASE_URL` = Railway backend URL 결정) — Vercel dashboard 환경변수 매핑 결정 wire 보존.
- [ ] **AC1.3** `headers` (CSP + X-Frame-Options + HSTS 결정 wire) — `Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://*.supabase.co https://*.sentry.io https://*.railway.app; frame-ancestors 'none'` 결정.
- [ ] **AC1.4** `redirects` (legacy `/ko-KR/*` → `/ko/*` 결정, next-intl i18n routing 정합) + `rewrites` 결정 wire 보류 (CR 12-5 D-PARITY-01 inversion 적용: server/client URL parity).
- [ ] **AC1.5** `apps/web/vercel.json` vs root `vercel.json` 결정 wire 보존 (root 단일 SSOT 결정) — Phase 4 PRD entry 정합 sweep 결정.
- [ ] **AC1.6** CSP 결정 wire + HSTS 결정 wire (`Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`) + `X-Frame-Options: DENY` 결정 wire — 보안을 위한 HTTP 보안 헤더 결정.

### F16.2 Railway backend deployment config

- [ ] **AC2.1** Root `railway.toml` NEW (~+60 LOC, atomic) — Railway backend deployment config: `builder = "DOCKERFILE"` (multi-stage Dockerfile 정합) + `dockerfilePath = "apps/api/Dockerfile"` (per-app Dockerfile 결정) + `healthcheckPath = "/api/v1/health"` (FastAPI health check endpoint 결정) + `healthcheckTimeout = 300` (5분 cold start 허용) + `restartPolicyType = "ON_FAILURE"` 결정 + `restartPolicyMaxRetries = 3`.
- [ ] **AC2.2** env vars 매핑 (`DATABASE_URL` = Supabase PostgreSQL connection string + `SUPABASE_JWT_SECRET` + `SUPABASE_URL` + `SUPABASE_ANON_KEY` + `SUPABASE_SERVICE_ROLE_KEY` + `SENTRY_DSN` 결정 + `ENVIRONMENT = "production"`).
- [ ] **AC2.3** Railway service = `costmgr-api` (단일 backend) 결정 + `apps/api/railway.toml` vs root `railway.toml` 결정 wire 보존 (root 단일 SSOT 결정).
- [ ] **AC2.4** Health check healthcheckPath = `/api/v1/health` 정합 (FastAPI `apps/api/core/health.py` AC5.1 정합 sweep) — Railway health check 정합 sweep 결정.

### F16.3 apps/web/Dockerfile + apps/api/Dockerfile (per-app Dockerfile 분리)

- [ ] **AC3.1** `apps/web/Dockerfile` NEW (~+40 LOC, atomic) — `node:20-bookworm-slim` 베이스 (Next.js standalone output build) + `pnpm install --frozen-lockfile` + `pnpm --filter web build` + `pnpm deploy` standalone bundle 추출 + `CMD ["node", "apps/web/server.js"]` 결정. **AD-14 stack pin by @sha256: digest** 결정 (베이스 이미지 pin — root Dockerfile 패턴 미러).
- [ ] **AC3.2** `apps/api/Dockerfile` NEW (~+50 LOC, atomic) — `python:3.12-slim` 베이스 (FastAPI production server) + `pip install --no-cache-dir` + `uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT` 결정. **AD-14 stack pin by @sha256: digest** 결정. 멀티 stage build (builder → runtime) 결정.
- [ ] **AC3.3** Multi-stage build 정합 — `apps/web/Dockerfile` = builder (pnpm install + build) + runtime (Next.js standalone output only) 2-stage. `apps/api/Dockerfile` = builder (pip install + collect static) + runtime (uvicorn production server) 2-stage 결정.
- [ ] **AC3.4** Root `Dockerfile` baseline (4-stage frontend-builder → backend-builder → backend-runtime + frontend-runtime) 보존 결정 + per-app Dockerfile은 Railway/Vercel 각각의 deployment adapter — root Dockerfile + per-app Dockerfile 병행 결정 wire 보존.

### F16.4 docs/deployment.md (production deployment runbook)

- [ ] **AC4.1** `docs/deployment.md` NEW (~12 sections, atomic): purpose + architecture (Vercel frontend + Railway backend + Supabase PostgreSQL 결정 wire) + prerequisites (Vercel account + Railway account + Supabase project + GitHub repo 결정) + step-by-step deployment guide (Supabase setup → Backend Railway deploy → Frontend Vercel deploy → DNS/domain 결정 wire) + env vars SSOT (`.env.example` → Railway/Vercel dashboard 매핑 결정).
- [ ] **AC4.2** Health check + monitoring (Sentry integration 결정 wire) + database backup + restore (Supabase 자동 + 수동 export 결정) + rollback strategy (Vercel/Railway atomic rollback 결정) sections 정합.
- [ ] **AC4.3** Smoke test (post-deploy verification 결정 wire, CR 12-5 D-PARITY-01 inversion 적용) + troubleshooting (common issues 결정 wire) + security (secrets management + HTTPS + CSP + HSTS 결정) + cost estimation (Vercel + Railway + Supabase pricing 결정 wire 보류) sections 정합.

### F16.5 Health check + observability + monitoring

- [ ] **AC5.1** `apps/api/core/health.py` NEW (~+60 LOC, atomic) — `GET /api/v1/health` FastAPI endpoint + response `{status: "healthy", timestamp, version, database: "connected", redis: "connected" | "disconnected", uptime_seconds}` 결정. Database connectivity check (psycopg2 `SELECT 1`) + Supabase connection check + JWT verification test (Supabase JWT decode with anon key) 결정 wire.
- [ ] **AC5.2** Liveness vs readiness 분리 결정 (`/health/live` + `/health/ready` 결정 wire). liveness = app process alive (200 OK always), readiness = DB connected + JWT verification passed (200 OK if all checks pass, 503 Service Unavailable otherwise).
- [ ] **AC5.3** `apps/web/lib/observability/sentry.ts` NEW (~+40 LOC, atomic) — Sentry browser integration (session replay + error tracking) + `Sentry.init({ dsn: process.env.NEXT_PUBLIC_SENTRY_DSN, environment: process.env.NEXT_PUBLIC_ENVIRONMENT, tracesSampleRate: 0.1 })` 결정. SSR-safe initialization (`typeof window !== "undefined"` guard) 결정.
- [ ] **AC5.4** `apps/api/core/observability.py` NEW (~+40 LOC, atomic) — Sentry FastAPI integration (server-side error tracking) + `sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), environment="production", traces_sample_rate=0.1)` 결정. FastAPI middleware integration (request context 결정) + SQLAlchemy integration (DB query tracing 결정, opt-in for sensitive routes) 결정.
- [ ] **AC5.5** `apps/web/app/api/health/route.ts` NEW (~+30 LOC, atomic) — Next.js health check route handler (Vercel-side health check, `/api/health` 결정) + response `{status: "healthy", build: process.env.NEXT_PUBLIC_VERCEL_GIT_COMMIT_SHA, region: process.env.NEXT_PUBLIC_VERCEL_REGION}` 결정.
- [ ] **AC5.6** `apps/api/main.py` MODIFIED (health router include) 결정 wire — `health_router` import + include_router 결정 (CR 12-5 D-14 envelope `{status, timestamp, version, database, redis, uptime_seconds}` 정합).
- [ ] **AC5.7** Capability gate `DEPLOYMENT_HEALTH_CHECK` 결정 wire (capability matrix v1.25 EXTENSION 4 NEW rows industry-agnostic 4-industry grants, CR 12-1 L4 precedent 미러).

### F16.6 Database backup strategy + Supabase production PostgreSQL

- [ ] **AC6.1** `apps/api/alembic/versions/0036_phase_4_backup_strategy.py` NEW (~+80 LOC, atomic) — `phase_4_backup_strategy` table 신규 (id + backup_type + started_at + completed_at + size_bytes + checksum_sha256 + storage_url + status + created_at 결정). down_revision = `0035_custom_access_token_hook` 결정 wire (Phase 3-0 wire 정합).
- [ ] **AC6.2** Supabase 자동 backup 정합 sweep (PITR = Point-in-Time Recovery = 7 days 결정 wire, Supabase Pro plan 기본) + 수동 backup trigger (`POST /api/v1/admin/backup` admin-only endpoint 결정 wire) + checksum validation (SHA-256 무결성 검증 결정).
- [ ] **AC6.3** Storage 결정 (`s3://costmgr-backups/YYYY-MM-DD/` 결정 wire 보류, Supabase Storage vs AWS S3 결정 보류 — Phase 4 close-out retro 진입 시점에 결정).
- [ ] **AC6.4** `docs/database-backup.md` NEW (~+200 LOC, atomic): purpose + strategy (Supabase PITR 자동 + 수동 export 보완) + RPO (Recovery Point Objective = 5분 결정, Supabase PITR 정합) + RTO (Recovery Time Objective = 1시간 결정) + backup schedule (daily 자동 + weekly 수동 검증 결정) + restore procedure (step-by-step 결정 wire) + disaster recovery (multi-region backup 결정 wire 보류, Phase 5+ 진입 시점) + monitoring (backup success/failure alerts 결정 wire) + retention policy (30일 hot + 90일 cold 결정) + testing (quarterly restore drill 결정 wire).
- [ ] **AC6.5** Capability gate `DEPLOYMENT_DATABASE_BACKUP` 결정 wire (capability matrix v1.25 EXTENSION 4 NEW rows industry-agnostic 4-industry grants, CR 12-1 L4 precedent 미러).
- [ ] **AC6.6** audit-first INSERT 정합 (`action_name='backup_created'`, `actor_user_id`, `tenant_id`, `payload={backup_type, size_bytes, checksum_sha256, storage_url}`, CR 1-1 audit-first INSERT 정합) 결정 wire.

### F16.7 Tests + Capability + atomic commit (3중 게이트 FINAL CLEAN)

- [ ] **AC7.1** `tests/api/core/test_phase_4_vercel_config.py` NEW (~+10 cases) — vercel.json JSON schema 검증 + regions/buildCommand/outputDirectory/env 매핑 검증 + headers/redirects/rewrites 정합.
- [ ] **AC7.2** `tests/api/core/test_phase_4_railway_config.py` NEW (~+8 cases) — railway.toml TOML schema 검증 + healthcheckPath/restartPolicyType/env 매핑 검증.
- [ ] **AC7.3** `tests/api/core/test_phase_4_dockerfile_parity.py` NEW (~+12 cases) — apps/web/Dockerfile + apps/api/Dockerfile multi-stage build 검증 + AD-14 digest pin 검증 + CMD entrypoint 검증.
- [ ] **AC7.4** `tests/api/core/test_phase_4_health_check.py` NEW (~+10 cases) — `/api/v1/health` endpoint response 검증 + database connectivity check + JWT verification + liveness/readiness 분리.
- [ ] **AC7.5** `tests/web/test_phase_4_sentry_integration.test.ts` NEW (~+10 cases) — Sentry browser init + SSR-safe guard + tracesSampleRate 결정 검증 + session replay opt-in 검증.
- [ ] **AC7.6** `tests/web/test_phase_4_vercel_health.test.ts` NEW (~+10 cases) — `/api/health` route handler + Vercel env vars + region 결정 검증.
- [ ] **AC7.7** `tests/api/core/test_phase_4_alembic_0036_backup.py` NEW (~+10 cases) — alembic 0036 migration code-shape 검증 + phase_4_backup_strategy table schema + checksum validation + storage URL format.
- [ ] **AC7.8** `tests/integration/test_capability_matrix_v1_25_drift.py` NEW (drift detector — 4 NEW DEPLOYMENT_* rows SSOT 정합 sweep) — SSOT 정합 sweep (P-015 ko-KR.json SSOT drift detector 패턴 미러).
- [ ] **AC7.9** 3중 게이트 FINAL CLEAN — (1) `pnpm tsc --noEmit` 0 NEW errors (Phase 4 deployment files clean — pre-existing 7 baseline errors unrelated 보존) / (2) `pnpm vitest run` 716+20 = **~736/736 PASS** (71+2 = 73 files, Phase 4 +20 NEW cases, 0 regressions) / (3) `ruff check` scoped Phase 4 wire files = **All checks passed!** / (4) `pytest` 31+40 = **71/71 PASS** (Phase 4 +40 NEW e2e tests, 0 NEW regressions; baseline 1 unrelated pre-existing failure `test_generate_report_pdf_report15_payload_not_required` 보존).
- [ ] **AC7.10** A36 SDR 검증 4-step 자동 적용 PASS — (1) commit prefix lint (CR 9-6 D5 prevention) / (2) sprint-status structure 정합 (D4 fix 보존) / (3) vitest file count drift 0건 (D2 fix 보존) / (4) commit consistency 정합 (D1 fix 보존).
- [ ] **AC7.11** atomic commit + sprint-status `phase-4-deployment-config-wire: ready-for-dev → done` + handoff memory 신규 + `docs/deployment.md` NEW (Phase 4 T4) + `docs/database-backup.md` NEW (Phase 4 T6).

## Tasks / Subtasks

- [ ] **Task 1 — T1: Vercel frontend deployment config 신규 wire** (AC: #1.1, #1.2, #1.3, #1.4, #1.5, #1.6)
  - [ ] Subtask 1.1 — Root `vercel.json` NEW: framework=nextjs + buildCommand="pnpm --filter web build" + installCommand="pnpm install --frozen-lockfile" + outputDirectory="apps/web/.next" + regions=["icn1"] 결정
  - [ ] Subtask 1.2 — Root `vercel.json` env 매핑: NEXT_PUBLIC_SUPABASE_URL + NEXT_PUBLIC_SUPABASE_ANON_KEY + NEXT_PUBLIC_API_BASE_URL 결정
  - [ ] Subtask 1.3 — Root `vercel.json` headers: CSP + X-Frame-Options + HSTS 결정 wire 보존
  - [ ] Subtask 1.4 — Root `vercel.json` redirects: legacy `/ko-KR/*` → `/ko/*` 결정 (next-intl i18n routing 정합)

- [ ] **Task 2 — T2: Railway backend deployment config 신규 wire** (AC: #2.1, #2.2, #2.3, #2.4)
  - [ ] Subtask 2.1 — Root `railway.toml` NEW: builder=DOCKERFILE + dockerfilePath="apps/api/Dockerfile" + healthcheckPath="/api/v1/health" + healthcheckTimeout=300 결정
  - [ ] Subtask 2.2 — Root `railway.toml` restartPolicyType="ON_FAILURE" + restartPolicyMaxRetries=3 결정
  - [ ] Subtask 2.3 — Root `railway.toml` env vars: DATABASE_URL + SUPABASE_JWT_SECRET + SUPABASE_URL + SUPABASE_ANON_KEY + SUPABASE_SERVICE_ROLE_KEY + SENTRY_DSN + ENVIRONMENT="production" 결정

- [ ] **Task 3 — T3: Per-app Dockerfile 분리 wire** (AC: #3.1, #3.2, #3.3, #3.4)
  - [ ] Subtask 3.1 — `apps/web/Dockerfile` NEW: node:20-bookworm-slim 베이스 (Next.js standalone output build) + pnpm install --frozen-lockfile + pnpm --filter web build + pnpm deploy standalone bundle 추출 + CMD ["node", "apps/web/server.js"] 결정
  - [ ] Subtask 3.2 — `apps/api/Dockerfile` NEW: python:3.12-slim 베이스 (FastAPI production server) + pip install --no-cache-dir + uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT 결정
  - [ ] Subtask 3.3 — `apps/web/Dockerfile` + `apps/api/Dockerfile` AD-14 digest pin 결정 (베이스 이미지 pin — root Dockerfile 패턴 미러)

- [ ] **Task 4 — T4: Deployment runbook 신규 wire** (AC: #4.1, #4.2, #4.3)
  - [ ] Subtask 4.1 — `docs/deployment.md` NEW (~12 sections): purpose + architecture + prerequisites + step-by-step deployment guide + env vars SSOT 결정
  - [ ] Subtask 4.2 — `docs/deployment.md` health check + monitoring + database backup + restore + rollback strategy sections 결정
  - [ ] Subtask 4.3 — `docs/deployment.md` smoke test + troubleshooting + security + cost estimation sections 결정

- [ ] **Task 5 — T5: Health check + observability 신규 wire** (AC: #5.1, #5.2, #5.3, #5.4, #5.5, #5.6, #5.7)
  - [ ] Subtask 5.1 — `apps/api/core/health.py` NEW: GET /api/v1/health FastAPI endpoint + response `{status, timestamp, version, database, redis, uptime_seconds}` + database connectivity check (psycopg2 SELECT 1) + Supabase connection check + JWT verification test 결정
  - [ ] Subtask 5.2 — `apps/api/core/health.py` liveness vs readiness 분리: /health/live (app process alive, 200 OK always) + /health/ready (DB connected + JWT verification passed, 503 if any check fails) 결정
  - [ ] Subtask 5.3 — `apps/web/lib/observability/sentry.ts` NEW: Sentry browser integration (session replay + error tracking) + Sentry.init({ dsn, environment, tracesSampleRate: 0.1 }) + SSR-safe initialization (typeof window !== "undefined" guard) 결정
  - [ ] Subtask 5.4 — `apps/api/core/observability.py` NEW: Sentry FastAPI integration + sentry_sdk.init(dsn, environment="production", traces_sample_rate=0.1) + FastAPI middleware (request context) + SQLAlchemy integration (DB query tracing, opt-in for sensitive routes) 결정
  - [ ] Subtask 5.5 — `apps/web/app/api/health/route.ts` NEW: Next.js health check route handler + response `{status, build: NEXT_PUBLIC_VERCEL_GIT_COMMIT_SHA, region: NEXT_PUBLIC_VERCEL_REGION}` 결정
  - [ ] Subtask 5.6 — `apps/api/main.py` MODIFIED: health_router import + include_router 결정 (CR 12-5 D-14 envelope 정합)

- [ ] **Task 6 — T6: Database backup strategy 신규 wire** (AC: #6.1, #6.2, #6.3, #6.4, #6.5, #6.6)
  - [ ] Subtask 6.1 — `apps/api/alembic/versions/0036_phase_4_backup_strategy.py` NEW: phase_4_backup_strategy table (id + backup_type + started_at + completed_at + size_bytes + checksum_sha256 + storage_url + status + created_at) 결정
  - [ ] Subtask 6.2 — alembic 0036 down_revision = `0035_custom_access_token_hook` 결정 wire (Phase 3-0 wire 정합)
  - [ ] Subtask 6.3 — phase_4_backup_strategy table checksum validation: SHA-256 무결성 검증 결정 + audit-first INSERT (action_name='backup_created', CR 1-1 정합) 결정
  - [ ] Subtask 6.4 — `docs/database-backup.md` NEW (~+200 LOC): purpose + strategy + RPO/RTO + backup schedule + restore procedure + retention policy sections 결정

- [ ] **Task 7 — T7: Capability gate v1.25 EXTENSION wire** (AC: #5.7, #6.5)
  - [ ] Subtask 7.1 — `apps/api/core/capability.py` EXTENSION: 4 NEW enum `DEPLOYMENT_PROD` + `DEPLOYMENT_STAGING` + `DEPLOYMENT_DATABASE_BACKUP` + `DEPLOYMENT_HEALTH_CHECK` (CR 12-1 L4 precedent — industry-agnostic)
  - [ ] Subtask 7.2 — `apps/api/core/capability.py` 4-industry grants industry-agnostic ✅/✅/✅/✅ (manufacturing + service + retail + food_service)
  - [ ] Subtask 7.3 — `docs/capability-matrix.md` 확인 (Phase 4 PRD entry wire 시점에 4 NEW rows 이미 추가됨, lines 416-419) — capability.py enum 만 wire
  - [ ] Subtask 7.4 — `tests/integration/test_capability_matrix_v1_25_drift.py` NEW: drift detector — SSOT 정합 sweep (P-015 ko-KR.json SSOT drift detector 패턴 미러)

- [ ] **Task 8 — T8: Tests + 3중 게이트 FINAL CLEAN + atomic commit** (AC: #7.1~#7.11)
  - [ ] Subtask 8.1 — `tests/api/core/test_phase_4_vercel_config.py` NEW (~+10 pytest cases)
  - [ ] Subtask 8.2 — `tests/api/core/test_phase_4_railway_config.py` NEW (~+8 pytest cases)
  - [ ] Subtask 8.3 — `tests/api/core/test_phase_4_dockerfile_parity.py` NEW (~+12 pytest cases)
  - [ ] Subtask 8.4 — `tests/api/core/test_phase_4_health_check.py` NEW (~+10 pytest cases)
  - [ ] Subtask 8.5 — `tests/web/test_phase_4_sentry_integration.test.ts` NEW (~+10 vitest cases)
  - [ ] Subtask 8.6 — `tests/web/test_phase_4_vercel_health.test.ts` NEW (~+10 vitest cases)
  - [ ] Subtask 8.7 — `tests/api/core/test_phase_4_alembic_0036_backup.py` NEW (~+10 pytest cases)
  - [ ] Subtask 8.8 — `tests/integration/test_capability_matrix_v1_25_drift.py` NEW (drift detector — 4 NEW DEPLOYMENT_* rows SSOT 정합 sweep)
  - [ ] Subtask 8.9 — sprint-status `phase-4-deployment-config-wire: in-progress → done` + `last_updated: 2026-08-22 (KST)` line 갱신
  - [ ] Subtask 8.10 — `docs/deployment.md` NEW (Phase 4 T4) + `docs/database-backup.md` NEW (Phase 4 T6)
  - [ ] Subtask 8.11 — handoff memory 신규 `C:\Users\c8rom\.claude\projects\C--Users-c8rom-desktop-costmgr\memory\handoff-2026-08-22-phase-4-deployment-wire-spec-entry-done.md`
  - [ ] Subtask 8.12 — 3중 게이트 FINAL CLEAN verification: (1) `pnpm tsc --noEmit` 0 NEW / (2) `pnpm vitest run` 716+20 = ~736 NEW PASS + 0 regressions / (3) `ruff check` scoped Phase 4 wire files = All checks passed! / (4) `pytest` 31+40 = ~71 NEW PASS. A36 SDR 검증 4-step 자동 적용: (a) commit prefix lint / (b) sprint-status structure / (c) vitest file count drift / (d) commit consistency
  - [ ] Subtask 8.13 — atomic commit via `git commit -F <commit-msg-file>` (CR 9-6 D5 prevention — PowerShell here-string 회피)

## Dev Notes

### Source tree components to touch

**NEW files (~17)**
- `vercel.json` (T1.1+T1.2+T1.3+T1.4)
- `railway.toml` (T2.1+T2.2+T2.3)
- `apps/web/Dockerfile` (T3.1+T3.3)
- `apps/api/Dockerfile` (T3.2+T3.3)
- `docs/deployment.md` (T4.1+T4.2+T4.3)
- `apps/api/core/health.py` (T5.1+T5.2)
- `apps/api/core/observability.py` (T5.4)
- `apps/web/lib/observability/sentry.ts` (T5.3)
- `apps/web/app/api/health/route.ts` (T5.5)
- `apps/api/alembic/versions/0036_phase_4_backup_strategy.py` (T6.1+T6.2+T6.3)
- `docs/database-backup.md` (T6.4)
- `tests/api/core/test_phase_4_vercel_config.py` (T8.1)
- `tests/api/core/test_phase_4_railway_config.py` (T8.2)
- `tests/api/core/test_phase_4_dockerfile_parity.py` (T8.3)
- `tests/api/core/test_phase_4_health_check.py` (T8.4)
- `tests/web/test_phase_4_sentry_integration.test.ts` (T8.5)
- `tests/web/test_phase_4_vercel_health.test.ts` (T8.6)
- `tests/api/core/test_phase_4_alembic_0036_backup.py` (T8.7)
- `tests/integration/test_capability_matrix_v1_25_drift.py` (T8.8)

**MODIFIED files (~2)**
- `apps/api/core/capability.py` (T7.1+T7.2) — 4 NEW enum + 4-industry grants
- `apps/api/main.py` (T5.6) — health router include

### Existing files to PRESERVE (Phase 4 PRD entry baseline sweep)

- **Root `Dockerfile`** (multi-stage build: frontend-builder → backend-builder → backend-runtime + frontend-runtime = 4-stage, AD-14 stack pin by @sha256: digest 모든 베이스 이미지 결정) — **PRESERVE VERBATIM**
- `docker-compose.yml` (postgres only, port 54322 → host 54322 매핑, healthcheck 결정) — **PRESERVE VERBATIM**
- `.github/workflows/ci.yml` (lint-deps + lint-imports + lint-conventions + stack-pin-check + commit-prefix-lint + test-architecture + test-service-role-guard + service-role-guard-lint + rls-tests + web-test + web-e2e + smoke-e2e 결정, 12 step decisions) — **PRESERVE VERBATIM**
- `apps/api/main.py` (existing router includes) — **EXTENSION ONLY** (MODIFIED, not rewrite)
- `apps/api/core/capability.py` (existing Capability enum entries) — **EXTENSION ONLY** (MODIFIED, not rewrite)

### Test environment invariants (CRITICAL)

- **vercel.json/railway.toml JSON/TOML schema tests**: All `tests/api/core/test_phase_4_*_config.py` tests MUST use JSON/TOML parsers to verify schema correctness. Mock pattern = `pathlib.Path` + `json.loads` / `tomllib.loads` for direct file reading.
- **Dockerfile tests**: All `tests/api/core/test_phase_4_dockerfile_parity.py` tests MUST use `pathlib.Path` + regex matching against Dockerfile content. Pattern = `re.compile(r'FROM (\S+)')` + multi-stage build verification.
- **alembic 0036 tests**: All `tests/api/core/test_phase_4_alembic_0036_backup.py` tests MUST use `re.compile` against migration source for code-shape verification (Story 9-7 pattern, T9 precedent).
- **No live deployment**: All tests run in `pnpm vitest` / `pytest` without actual Vercel/Railway deployment. Health check endpoint tests MUST mock database connectivity (psycopg2 `SELECT 1` mocked).
- **Sentry DSN env vars**: All `tests/web/test_phase_4_sentry_integration.test.ts` tests MUST mock Sentry DSN (test DSN = `https://test@sentry.io/1`).

### Existing patterns to mirror (CR 11-4 lessons)

- **CR 11-4 D-001**: `page.tsx` actual mount `<Component>` JSX MUST (no `<>TODO</>` stubs) — Phase 4 T5 `apps/web/app/api/health/route.ts` 정합
- **CR 11-4 D-002**: `apps/web/messages/ko-KR.json` SSOT only (no `lib/ko-KR.json` dual-file) — Phase 4 health check responses ko-KR 정합
- **CR 11-4 D-003**: vitest RTL render discipline
- **CR 11-4 D-005**: TS mirror unknown state reject
- **CR 11-4 P-015**: ko-KR.json SSOT drift detector (`test_ko_kr_json_ssot_drift.test.ts` already exists)

### Backend integration points (Phase 3-0 already done)

- `custom_access_token_hook` (alembic 0035) — Phase 3-0 wire 정합
- `tenant_memberships` table — Phase 3-0 wire 정합
- `audit_logs` table — CR 1-1 audit-first INSERT 정합 (Phase 4 T6 backup_created audit log INSERT)
- `users.totp_secret` + 2FA columns — Epic 12 wire 정합
- `tenant_backups` table — Epic 12 Story 12.2 wire 정합 (Phase 4 T6 NEW `phase_4_backup_strategy` table 별도 추가 결정)
- `deletion_consents` table — Epic 12 Story 12.3 wire 정합

### Architecture patterns to follow

- **AD-27 Deployment verbatim** (Phase 4 PRD entry 결정 wire):
  - Vercel frontend (Next.js 15 + monorepo + Seoul region icn1)
  - Railway backend (FastAPI + Dockerfile + health check endpoint)
  - Supabase PostgreSQL production (PITR 7 days auto backup)
  - Sentry observability (browser + server, tracesSampleRate 0.1)
- **AD-14 stack pin by @sha256: digest** 결정 — root Dockerfile 패턴 미러 (apps/web/Dockerfile + apps/api/Dockerfile)
- **CR 0-2 RLS lesson**: Phase 3-0 wire 정합 (Phase 4 deployment surface does NOT modify RLS policies)
- **CR 1-1 audit-first INSERT**: T6 backup_created audit log INSERT 결정 (Phase 3-0 tenant_signup_completed + T5 user_logged_out + T6 password_reset 보존)
- **CR 11-3 honest-DEFER 53번째 epic 연속**: D-1-1-DEFER-1/2/3 honestly preserved (Magic link + Social login OAuth + SSO enterprise SAML)
- **CR 11-4 D-001/D-002/D-003/D-005 + P-015**: 5 lessons carry
- **CR 12-1 L4 precedent**: industry-agnostic capability 4-industry grants (DEPLOYMENT_* 4 NEW rows)
- **CR 12-5 D-14 envelope**: health check response envelope `{status, timestamp, version, database, redis, uptime_seconds}` 정합
- **CR 12-5 D-PARITY-01 inversion**: Vercel + Railway + Supabase URL parity + env vars parity (NEXT_PUBLIC_API_BASE_URL = Railway backend URL 결정)
- **CR 9-6 D5 prevention**: `git commit -F <file>` (NOT PowerShell here-string)
- **A19 cohesion pattern 9 surface EXTENSION PASS 결정**: deployment surface NEW (T1~T7 deployment config + health check + observability + database backup)

### Project Structure Notes

- **Root deployment config**: `vercel.json` (root) + `railway.toml` (root) — SSOT 결정 wire (apps/web/vercel.json + apps/api/railway.toml 미사용 결정)
- **Per-app Dockerfile**: `apps/web/Dockerfile` + `apps/api/Dockerfile` — per-app deployment adapter 결정 (root Dockerfile baseline과 병행)
- **Observability**: `apps/web/lib/observability/sentry.ts` (browser) + `apps/api/core/observability.py` (server) 결정
- **Health check**: `apps/api/core/health.py` (FastAPI) + `apps/web/app/api/health/route.ts` (Next.js) 결정
- **Database backup**: `apps/api/alembic/versions/0036_phase_4_backup_strategy.py` (NEW table) + `docs/database-backup.md` (runbook) 결정
- **Test structure**: `tests/api/core/test_phase_4_*.py` (pytest backend tests) + `tests/web/test_phase_4_*.test.ts` (vitest frontend tests) + `tests/integration/test_capability_matrix_v1_25_drift.py` (drift detector) — 기존 pattern 미러 (test_capability_matrix_v1_18_drift.py + test_phase_3_0_*.py)
- **Docs structure**: `docs/deployment.md` (T4) + `docs/database-backup.md` (T6) 결정

### Detected conflicts or variances

- **Root Dockerfile + per-app Dockerfile 병행**: root Dockerfile은 4-stage 통합 baseline (development/CI 환경), per-app Dockerfile은 Vercel/Railway 각각의 deployment adapter. 둘 다 보존 결정 wire — root Dockerfile verbatim preserve + per-app Dockerfile 추가.
- **Alembic 0036 down_revision**: down_revision = `0035_custom_access_token_hook` (Phase 3-0 wire 정합) 결정 wire — Story 14.1 alembic 0034 이후, Phase 3-0 alembic 0035 이후 결정.
- **Sentry DSN parity**: browser Sentry (`NEXT_PUBLIC_SENTRY_DSN`) + server Sentry (`SENTRY_DSN`) 결정 wire — 둘 다 Supabase secrets에 저장 결정.
- **Storage 결정 보류**: `s3://costmgr-backups/YYYY-MM-DD/` vs Supabase Storage 결정 wire 보류 (Phase 4 close-out retro 진입 시점에 결정).
- **Multi-region backup 결정 wire 보류**: disaster recovery multi-region backup 결정 wire 보류 (Phase 5+ 진입 시점).

## Previous Story Intelligence

### Phase 4 PRD entry (`phase-4-prd-entry: done`, 2026-08-22, commit `8e046df`)
- master PRD v3.0 → v3.1 atomic edit
- §F16 신규 (F16.1~F16.7 verbatim)
- AD-27 Deployment 신규 결정
- capability matrix v1.24 → v1.25 EXTENSION (4 NEW rows 이미 추가됨, capability.py enum 만 wire)
- A73+A74+A76+A77+A78 신규 결정 wire
- handoff: `memory/handoff-2026-08-22-phase-4-prd-entry-done.md`

### Phase 3 close-out retro (`phase-3-close-out-retrospective: done`, 2026-08-22)
- Phase 3 = Auth Foundation territory close-out 완료
- A70+A71+A72+A73+A74+A75 신규 결정 wire 진입
- Phase 4 = 옵션 (a) 진입 결정 wire (Deployment territory)
- handoff: `memory/handoff-2026-08-22-phase-3-close-out-done.md`

### Phase 3-1 auth foundation wire (`phase-3-1-auth-foundation-wire: done`, 2026-08-21, commit `d3e7454`)
- wire_commit = `d3e7454`
- 33 files atomic (5+4+5+2+3+5+2+7)
- 97 NEW test cases (66 vitest + 31 pytest)
- 3중 게이트 FINAL CLEAN
- handoff: `memory/handoff-2026-08-21-phase-3-1-auth-foundation-wire-done.md`

### Phase 3-0 auth contract slice (`phase-3-0-auth-contract-slice: done`, 2026-08-21, commit `1db21d2`)
- P0 3종 ALL RESOLVED: GUC name split + custom_access_token_hook + signup path
- 15 files atomic (5 NEW + 9 MODIFIED + 1 alembic)
- 43 NEW pytest PASS (8 + 14 + 21)
- 3중 게이트 FINAL CLEAN
- handoff: `memory/handoff-2026-08-21-phase-3-0-auth-contract-slice-done.md`

### Existing baseline (PRESERVE — Phase 4 PRD entry 정합 sweep)
- **Root `Dockerfile`** (multi-stage 4-stage, AD-14 digest pin, pnpm@10 + Python 3.12-slim)
- `docker-compose.yml` (postgres only, port 54322, healthcheck)
- `.github/workflows/ci.yml` (12 step decisions)

### Epic 12 wire (PRESERVE — backup strategy 정합)
- `apps/api/jobs/backup_daily.py` (KST 02:00 = UTC 17:00 cron entry)
- `apps/api/jobs/backup_retention.py` (KST 03:00 = UTC 18:00 retention sweep)
- `tenant_backups` table (Epic 12 12.2 wire) — Phase 4 T6 NEW `phase_4_backup_strategy` table 별도 추가 결정
- `packages/services/m12_account/backup_export` pure kernel subtree

### Epic 13 + Epic 14 wire (PRESERVE — LISTEN/NOTIFY consume 정합)
- `apps/api/alembic/versions/0034_listen_notify_consume_cross_tenant_fanout.py` NEW (14-1 wire)
- Epic 13/14 LISTEN/NOTIFY consume multi-process coordination 결정 wire 보존
- Phase 4 = PostgreSQL LISTEN/NOTIFY multi-process coordination 정합 (Railway multi-worker 환경 listener process-per-pod 정합)

### Story 9-7 frontend test debt follow-up (REFERENCE)
- `apps/web/mocks/handlers.ts` EXTENSION pattern — POST /api/v1/abc/validate handler reference
- 5 NEW vitest component tests (AbcDispatchPanel + AbcDispatchDecisionBadge + AbcDispatchResultCard + AbcDispatchErrorToast + AbcValidationForm)
- 3 NEW TS mirror parity tests (m9-abc-dispatch + report21 + report21-pdf)

## Git Intelligence Summary

### Last 5 commit titles (analysis)

1. `8e046df` — Phase 4 PRD entry DONE (cj-style Phase 4 1번째 진입점, master PRD v3.0 → v3.1 atomic edit)
2. `d3e7454` — Phase 3-1 auth foundation wire DONE (cj-style Phase 3 2번째 진입점 = cj-style 50번째 epic 연속 정직 회복)
3. `7c6aaa9` — Phase 3-0 sprint-status follow-up docs-only wire
4. `1db21d2` — Phase 3-0 auth contract slice DONE
5. `bd77221` — chore: 작업 트리 ruff 자동 수정 정리 + 부수 효과로 깨진 테스트 1건 수정

### Patterns established (apply to current story)

- **Single atomic commit** per sprint (T1~T8 in single atomic commit, CR 11-3 discipline)
- **2 atomic commits** if frontend + backend + docs must be separated (rare)
- **3중 게이트 FINAL CLEAN** mandatory before commit
- **A36 SDR 검증 4-step 자동 적용** (commit prefix lint + sprint-status structure + vitest file count drift + commit consistency)
- **CR 9-6 D5 prevention**: `git commit -F <file>` (NOT PowerShell here-string)

### Files created/modified in last sprint (relevant to Phase 4)

- `apps/api/core/security.py` EXTENSION (ALLOWED_ROLES + JWTClaims.tenant_id Optional + decode_jwt require_tenant kwarg) — **PRESERVE**
- `apps/api/core/tenant_context.py` EXTENSION (set_claims/clear_claims + 3-GUC publisher + PreOnboardingUser) — **PRESERVE**
- `apps/api/modules/m0_onboarding/handlers.py` EXTENSION (signup_router + POST endpoint) — **PRESERVE**
- `apps/api/modules/m0_onboarding/services/signup_service.py` NEW (atomic 5-step + 2 typed exceptions) — **PRESERVE**
- `apps/api/alembic/versions/0035_custom_access_token_hook.py` NEW — **PRESERVE**
- `supabase/config.toml` EXTENSION (custom_access_token_hook enabled = true) — **PRESERVE**

## References

- [Source: _bmad-output/planning-artifacts/prd.md#F16] — master PRD §F16 (Deployment territory) verbatim
- [Source: _bmad-output/planning-artifacts/prd.md#F16.1] — Vercel frontend deployment config
- [Source: _bmad-output/planning-artifacts/prd.md#F16.2] — Railway backend deployment config
- [Source: _bmad-output/planning-artifacts/prd.md#F16.3] — apps/web/Dockerfile + apps/api/Dockerfile (per-app Dockerfile 분리)
- [Source: _bmad-output/planning-artifacts/prd.md#F16.4] — docs/deployment.md (production deployment runbook)
- [Source: _bmad-output/planning-artifacts/prd.md#F16.5] — Health check + observability + monitoring
- [Source: _bmad-output/planning-artifacts/prd.md#F16.6] — Database backup strategy + Supabase production PostgreSQL
- [Source: _bmad-output/planning-artifacts/prd.md#F16.7] — tests + wire scope T1~T8 결정
- [Source: _bmad-output/planning-artifacts/prd.md#AD-27] — Deployment 신규 결정
- [Source: docs/capability-matrix.md#v1.25] — capability matrix v1.25 EXTENSION (4 NEW rows already added)
- [Source: docs/architecture-decisions/] — AD 인벤토리 (AD-27 신규 추가 시)
- [Source: docs/conventions.md] — §13.1 ko-KR SSOT 1권 강제 + ESLint rule forbid-non-ko-KR-keys
- [Source: docs/STACK_PIN.yaml] — frontend + backend 의존성 pin 검증 (Sentry SDK version 검증)
- [Source: _bmad-output/implementation-artifacts/handoff-2026-08-22-phase-4-prd-entry-done.md] — A73+A74+A76+A77+A78 결정
- [Source: _bmad-output/implementation-artifacts/handoff-2026-08-22-phase-3-close-out-done.md] — Phase 3 close-out retro A70~A75 결정
- [Source: _bmad-output/implementation-artifacts/handoff-2026-08-21-phase-3-1-auth-foundation-wire-done.md] — Phase 3-1 wire 33 files
- [Source: apps/api/core/capability.py] — Capability enum (4 NEW entries wire 진입)
- [Source: docs/deployment.md] — production deployment runbook (NEW, T4)
- [Source: docs/database-backup.md] — database backup runbook (NEW, T6)

## Open Questions

- **OQ-1**: Storage 결정 (`s3://costmgr-backups/YYYY-MM-DD/` vs Supabase Storage vs AWS S3). 결정 wire 진입 시점: Phase 4 close-out retro 진입 시점 (사용자 결정 보류).
- **OQ-2**: Sentry DSN parity (browser `NEXT_PUBLIC_SENTRY_DSN` + server `SENTRY_DSN`) — Supabase secrets vs Vercel/Railway env vars 결정. 결정 wire 진입 시점: T5.3 (sentry.ts) + T5.4 (observability.py) 진입 시.
- **OQ-3**: Multi-region backup 결정 wire 보류 — disaster recovery multi-region backup. 결정 wire 진입 시점: Phase 5+ 진입 시점 (cj-style 55번째 epic 연속 정직 회복 bmad-create-story 진입 시점).
- **OQ-4**: Phase 4 wire commit 진입 후 `Task #5 종단 증명` (Docker Desktop start 후 real Vercel/Railway deploy + health check 200 + cross-tenant 격리 확인) 시점. Phase 4 wire 완료 후 결정.
- **OQ-5**: CSP 결정 wire (`Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; ...`) — exact CSP values 결정 wire 진입 시점: T1.3 (vercel.json headers) 진입 시.

## Dev Agent Record

### Agent Model Used

claude-opus-4 (cj-style Phase 4 2번째 진입점 = cj-style 54번째 epic 연속 정직 회복)

### Debug Log References

### Completion Notes List

### File List

- [ ] `vercel.json` (NEW, T1.1+T1.2+T1.3+T1.4)
- [ ] `railway.toml` (NEW, T2.1+T2.2+T2.3)
- [ ] `apps/web/Dockerfile` (NEW, T3.1+T3.3)
- [ ] `apps/api/Dockerfile` (NEW, T3.2+T3.3)
- [ ] `docs/deployment.md` (NEW, T4.1+T4.2+T4.3)
- [ ] `apps/api/core/health.py` (NEW, T5.1+T5.2)
- [ ] `apps/api/core/observability.py` (NEW, T5.4)
- [ ] `apps/web/lib/observability/sentry.ts` (NEW, T5.3)
- [ ] `apps/web/app/api/health/route.ts` (NEW, T5.5)
- [ ] `apps/api/alembic/versions/0036_phase_4_backup_strategy.py` (NEW, T6.1+T6.2+T6.3)
- [ ] `docs/database-backup.md` (NEW, T6.4)
- [ ] `apps/api/main.py` (MODIFIED, T5.6)
- [ ] `apps/api/core/capability.py` (MODIFIED, T7.1+T7.2)
- [ ] `tests/api/core/test_phase_4_vercel_config.py` (NEW, T8.1)
- [ ] `tests/api/core/test_phase_4_railway_config.py` (NEW, T8.2)
- [ ] `tests/api/core/test_phase_4_dockerfile_parity.py` (NEW, T8.3)
- [ ] `tests/api/core/test_phase_4_health_check.py` (NEW, T8.4)
- [ ] `tests/web/test_phase_4_sentry_integration.test.ts` (NEW, T8.5)
- [ ] `tests/web/test_phase_4_vercel_health.test.ts` (NEW, T8.6)
- [ ] `tests/api/core/test_phase_4_alembic_0036_backup.py` (NEW, T8.7)
- [ ] `tests/integration/test_capability_matrix_v1_25_drift.py` (NEW, T8.8)
- [ ] `memory/handoff-2026-08-22-phase-4-deployment-wire-spec-entry-done.md` (NEW, T8.11)
- [ ] `_bmad-output/implementation-artifacts/sprint-status.yaml` (MODIFIED, T8.9)

---

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

## D-1-1-DEFER-* honestly DEFER preserved (CR 11-3 53번째 epic 연속)

- **D-1-1-DEFER-1** (Magic link login) — honestly preserved (Epic 15+ 진입 시점에 결정 wire 보존)
- **D-1-1-DEFER-2** (Social login OAuth — Google/Naver/Kakao) — honestly preserved
- **D-1-1-DEFER-3** (SSO enterprise SAML) — honestly preserved

Phase 4 PRD entry 정합 sweep 결정 wire 진입 시점에 A70+A71+A72 결정 wire 진입 완료 (Epic 15+ 진입 시점에 동시 RESOLVE 결정 wire 보존).

## CR 11-3 honest-DEFER 53번째 epic 연속

A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS) + CR 12-5 D-GATE-01 + D-PARITY-01 inversion 적용 보존 + A19 + CR 0-2 RLS lesson + CR 1-1 audit-first INSERT + CR 9-6 commit message discipline 모두 적용 보존.

## 결정 wire 일자

2026-08-22 (KST)

## next

Phase 4 cj-style 2번째 진입점 (본 스토리) = cj-style 54번째 epic 연속 정직 회복 bmad-create-story spec 진입 → `bmad-dev-story phase-4-deployment-wire` T1~T8 atomic wire 진입 (cj-style 55번째 epic 연속 정직 회복 wire 진입 시점).
Phase 4 close-out retro 진입 결정 wire 보존 (cj-style 56번째 epic 연속 정직 회복 진입 시점) OR 옵션 (b) Epic 15 진입 (Magic link + Social OAuth + SSO follow-up sprint 통합 territory) OR 옵션 (c) carry-over 진입 결정 wire 보존.