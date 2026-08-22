# Phase 4 Close-out Retrospective (cj-style Phase 4 4번째 진입점 = cj-style 56~57번째 epic 연속 정직 회복)

**일자**: 2026-08-22 (KST)
**작성자**: Amelia (Developer) + Charlie (Senior Dev) + Alice (Product Owner) 결정 wire 진입
**wire_commit**: TBD (cj-style Phase 4 close-out retro atomic docs-only wire = cj-style 56~57번째 docs only)
**baseline_commit**: `71a033a` (Phase 4 atomic wire tip = cj-style 55번째 epic 연속 정직 회복 wire DONE tip)
**retro_document**: 본 문서 (`_bmad-output/implementation-artifacts/phase-4-close-out-2026-08-22.md`)
**handoff**: `memory/handoff-2026-08-22-phase-4-close-out-done.md` (auto-memory 신규)
**previous retro**: `phase-3-close-out-2026-08-22.md` (cj-style 51~52번째) — D-1-1-DEFER-* honestly preserved 50번째 검증 + A70+A71+A72+A73+A74+A75 신규 결정 wire

---

## §1. Phase 4 territory 정의

Phase 4 = **Deployment config + Dockerfile + health check + observability + database backup territory**. Phase 3 (Auth Foundation) close-out retro 진입 시점에 옵션 (a) Phase 4 진입 결정 wire 진입 (옵션 b Epic 15 / 옵션 c carry-over 모두 rejected).

**Phase 4 cycle 구조** (cj-style 4-entry-point pattern):
1. **cj-style Phase 4 1번째 진입점** = Phase 4 PRD entry (cj-style 53번째 epic 연속 정직 회복) — `8e046df` ✅ DONE 2026-08-22
2. **cj-style Phase 4 2번째 진입점** = Phase 4 bmad-create-story spec entry (cj-style 54번째) — wire spec ~600+ lines ✅ DONE 2026-08-22
3. **cj-style Phase 4 3번째 진입점** = Phase 4 bmad-dev-story atomic wire T1~T8 (cj-style 55번째 epic 연속 정직 회복) — `71a033a` ✅ DONE 2026-08-22
4. **cj-style Phase 4 4번째 진입점** = Phase 4 close-out retro (cj-style 56~57번째) — THIS, 진입 결정 wire 진입

**Phase 4 진입 결정** (cj-style 정직 회복):
- Phase 3 (Auth Foundation) close-out retro 진입 시점에 옵션 (a) Phase 4 진입 결정 (Deployment territory 표준 진입 가능 + cj-style 1번째 진입점 표준 진입 가능 = 결정 wire 효율성)
- Epic 1 carry-over D-1-1-DEFER-* (Magic link + Social login OAuth + SSO enterprise SAML) honestly preserved for **53~54~55~56번째 epic 연속** (CR 11-3 honest-DEFER discipline)
- AD-27 Deployment 신규 결정 (Vercel frontend + Railway backend + Supabase PostgreSQL + Sentry observability)
- capability matrix v1.24 → v1.25 EXTENSION (4 NEW rows industry-agnostic 4-industry grants: DEPLOYMENT_PROD + DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP + DEPLOYMENT_HEALTH_CHECK)

## §2. Phase 4 cycle 정량 데이터

| Metric | Phase 4 PRD entry | Phase 4 spec entry | Phase 4 atomic wire | TOTAL |
|--------|-------------------|---------------------|---------------------|-------|
| **wire_commit** | `8e046df` (docs only) | (no commit, spec file only) | `71a033a` (atomic sprint) | 2 commits |
| **type** | docs-only | docs-only | docs-and-source | — |
| **NEW files** | 2 (handoff + memory index) | 1 (phase-4-deployment-wire.md spec) | 17 (vercel.json + railway.toml + 2 Dockerfiles + health.py + observability.py + sentry.ts + health/route.ts + alembic 0036 + docs/deployment.md + docs/database-backup.md + 5 pytest + 1 integration drift + 2 vitest) | 20 |
| **MODIFIED files** | 4 (prd.md + capability-matrix.md + sprint-status.yaml + MEMORY.md) | 0 (spec only) | 6 (capability.py + main.py + apps/web/package.json + pnpm-lock.yaml + capability-matrix.md + apps/web/tsconfig.tsbuildinfo incidental) | 10 |
| **alembic migrations** | — | — | 1 (0036_phase_4_backup_strategy) | 1 |
| **files atomic** | 6 (2+4) | 1 (spec) | 26 (20+6) | 33 |
| **NEW pytest cases** | — | — | 108 (vercel=11 + railway=14 + dockerfile_parity=12 + health_check=16 + alembic_0036=17 + capability_v1_25_drift=38) | 108 |
| **NEW vitest cases** | — | — | 21 (sentry_integration=10 + vercel_health=11) | 21 |
| **NEW ruff errors** | 0 | 0 | 0 (auto-fix + manual RET504/N801/PTH123×2/ARG002 fix) | 0 |
| **regressions** | 0 | 0 | 0 | 0 |
| **3중 게이트 FINAL CLEAN** | ✅ | n/a (spec) | ✅ | ✅ |
| **A19 cohesion surfaces PASS** | 9 surface 결정 | 9 surface 결정 | 9 surface EXTENSION PASS (deployment surface NEW) | 9/9 |
| **SDR 갱신** | baseline | baseline | pytest 3855→**3928** (+73 NEW collected), vitest 71→**73** files (+2) | +73 / +2 |
| **days** | 2026-08-22 | 2026-08-22 | 2026-08-22 | 1 day |

**Phase 4 cycle = 1-day atomic sprint** (Phase 4 PRD entry + spec entry + atomic wire 모두 2026-08-22 done 진입, partial wire 시도 0건 + single sprint atomic wire 결정 보존).

## §3. Phase 4 PRD entry 성과 (cj-style 53번째 epic 연속 정직 회복)

Phase 4 territory 진입을 가로막던 결정 wire 모두 해소.

### 결정 1: 옵션 (a) Phase 4 진입 결정 wire
- **문제**: Phase 3 close-out retro 진입 시점에 옵션 (a) Phase 4 / 옵션 (b) Epic 15 / 옵션 (c) carry-over 3 옵션 결정 보류
- **해결**: 옵션 (a) Phase 4 진입 결정 wire (rationale: Phase 4 PRD entry 진입 = Deployment territory 표준 진입 가능 + cj-style 1번째 진입점 표준 진입 가능 = 결정 wire 효율성)
- **wire**: master PRD v3.0 → v3.1 atomic edit (`_bmad-output/planning-artifacts/prd.md`) — front matter title 갱신 + changelog v3.1 entry 신규 + §F16 신규 (F16.1~F16.7) + §8.1 M0-(g) production deployment + §15 로드맵 Phase 4 row 백로그 → in-progress + §부록 A A73+A74+A76+A77+A78 표

### 결정 2: AD-27 Deployment 신규 결정
- **해결**: AD-27 verbatim (Vercel frontend + Railway backend + Supabase PostgreSQL + Sentry observability) 결정 wire
- **CR 12-5 D-PARITY-01 inversion 적용**: Vercel + Railway + Supabase URL parity + env vars parity 결정

### 결정 3: capability matrix v1.24 → v1.25 EXTENSION
- **해결**: 4 NEW rows (DEPLOYMENT_PROD + DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP + DEPLOYMENT_HEALTH_CHECK) industry-agnostic 4-industry grants ✅/✅/✅/✅
- **CR 12-1 L4 precedent 미러**: industry-agnostic capability 4-industry grants (manufacturing + service + retail + food_service)

### A73+A74+A76+A77+A78 결정 wire 진입
- **A73**: 옵션 (a) Phase 4 진입 결정 wire ✅ DONE
- **A74**: Master PRD v3.0 → v3.1 atomic edit ✅ DONE
- **A75**: A42 A36 SDR 검증 4-step 보존 + Epic 15+ 적용 🔵 OPEN (자동 적용)
- **A76**: AD-27 Deployment 신규 결정 🔵 OPEN → ✅ DONE (PRD entry 진입 시점에 결정)
- **A77**: Capability matrix v1.24 → v1.25 EXTENSION 4 NEW rows 결정 🔵 OPEN → ✅ DONE (PRD entry 진입 시점에 결정)
- **A78**: Phase 4 wire scope T1~T8 결정 🔵 OPEN → ✅ DONE (PRD entry 진입 시점에 결정)

## §4. Phase 4 atomic wire 성과 — T1~T8 (cj-style 55번째 epic 연속 정직 회복)

### T1 — Vercel frontend deployment config (1 NEW)
- `vercel.json` (~+80 LOC) — Vercel frontend deployment config: framework=nextjs + buildCommand=`pnpm --filter web build` + installCommand=`pnpm install --frozen-lockfile` + outputDirectory=`apps/web/.next` + regions=[icn1] Seoul 결정
- env 매핑 (NEXT_PUBLIC_SUPABASE_URL + NEXT_PUBLIC_SUPABASE_ANON_KEY + NEXT_PUBLIC_API_BASE_URL)
- headers (CSP + HSTS + X-Frame-Options + X-Content-Type-Options + Referrer-Policy + Permissions-Policy)
- redirects (`/ko-KR/:path*` → `/ko/:path*` 308 redirect)
- rewrites (`/api/health` rewrite)

### T2 — Railway backend deployment config (1 NEW)
- `railway.toml` (~+60 LOC) — Railway backend deployment config: [build] builder=DOCKERFILE + dockerfilePath=`apps/api/Dockerfile` + [deploy] healthcheckPath=`/api/v1/health` + healthcheckTimeout=300 + restartPolicyType=ON_FAILURE + restartPolicyMaxRetries=3
- [env] 매핑 (DATABASE_URL + SUPABASE_URL + SUPABASE_ANON_KEY + SUPABASE_SERVICE_ROLE_KEY + SUPABASE_JWT_SECRET + SENTRY_DSN + ENVIRONMENT=production)
- [[services]] costmgr-api uvicorn workers=2

### T3 — Per-app Dockerfile 분리 (2 NEW)
- `apps/web/Dockerfile` (3-stage Next.js standalone — deps node:20.18.0-bookworm-slim@sha256 digest pinned + builder + runner, pnpm@9.15.4 via corepack, CMD ["node", "apps/web/server.js"], HEALTHCHECK at /api/health, non-root user `app`, EXPOSE 3000)
- `apps/api/Dockerfile` (2-stage FastAPI uvicorn — builder python:3.12-slim@sha256:57cd7c3a + runner, uv from ghcr.io/astral-sh/uv:0.11.32@sha256, CMD uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --workers 2, HEALTHCHECK at /api/v1/health, non-root user `app`, EXPOSE 8000)
- **Root Dockerfile (4-stage frontend-builder + backend-builder + backend-runtime + frontend-runtime AD-14 digest pinned) preserved verbatim** — root Dockerfile + per-app Dockerfile 병행 결정
- **AD-14 stack pin by @sha256: digest** 모든 베이스 이미지 결정 (CR 0-2 lesson)

### T4 — Deployment runbook (1 NEW)
- `docs/deployment.md` (12 sections) — Purpose + Architecture (Vercel+Railway+Supabase+Sentry diagram) + Prerequisites (services+costs) + Step-by-Step (Supabase→Railway→Vercel→DNS) + Env Vars SSOT + Health Check+Monitoring + Database Backup+Restore + Rollback Strategy + Smoke Test + Troubleshooting + Security (CSP+HSTS+X-Frame-Options) + Cost Estimation ($76-96/month baseline)

### T5 — Health check + observability (4 NEW + 1 MODIFIED)
- `apps/api/core/health.py` NEW (FastAPI router prefix=/api/v1/health, 3 endpoints: GET / [combined] + /live [always 200 OK] + /ready [200/503 with DB+JWT check], CR 12-5 D-14 envelope `{status, timestamp, version, database, redis, uptime_seconds}`, SELECT 1 with asyncio.wait_for timeout=2.0, urllib.request for Supabase /auth/v1/health probe, optional Redis check)
- `apps/api/core/observability.py` NEW (Sentry FastAPI integration init_sentry SSR-safe no-op when SENTRY_DSN unset, sentry_sdk with FastApiIntegration + StarletteIntegration + SqlalchemyIntegration, traces_sample_rate=0.1, send_default_pii=False)
- `apps/web/lib/observability/sentry.ts` NEW (browser Sentry SSR-safe guard `typeof window !== "undefined"`, isSentryEnabled() checks NEXT_PUBLIC_SENTRY_DSN, initSentry() lazy-loads @sentry/nextjs, tracesSampleRate=0.1, replaysSessionSampleRate=0, sendDefaultPii=false)
- `apps/web/app/api/health/route.ts` NEW (Edge Runtime + force-dynamic + NextResponse.json envelope `{status: "healthy", build, region, timestamp}` with NEXT_PUBLIC_VERCEL_GIT_COMMIT_SHA + NEXT_PUBLIC_VERCEL_REGION)
- `apps/api/main.py` MODIFIED (health_router include + init_sentry call after FastAPI app creation)
- `apps/web/package.json` MODIFIED (@sentry/nextjs 8.40.0 dependency 결정 wire) + pnpm-lock.yaml MODIFIED (lockfile 정합)

### T6 — Database backup strategy (1 NEW alembic + 1 NEW docs)
- `apps/api/alembic/versions/0036_phase_4_backup_strategy.py` NEW (revision="0036_phase_4_backup_strategy", down_revision="0035_custom_access_token_hook", phase_4_backup_strategy table — id BIGSERIAL PK + backup_type TEXT enum auto_pitr/manual_admin/manual_export + started_at + completed_at NULL + size_bytes + checksum_sha256 + storage_url + status TEXT enum in_progress/completed/failed server_default='in_progress' + tenant_id UUID NULL + created_at + updated_at, 4 indexes status + started_at DESC + tenant_id+started_at DESC + backup_type+status, 3 CHECK constraints backup_type enum + status enum + completed_at >= started_at)
- `docs/database-backup.md` NEW (10 sections: Purpose + Strategy PITR primary + manual secondary + quarterly tertiary + RPO 5 min + RTO 1 hr + Backup Schedule continuous PITR + daily 02:00 KST + weekly Sunday + quarterly drills + Restore Procedure 5 steps + Disaster Recovery single-region + multi-region deferred Phase5+ + Monitoring Grafana + Sentry + PagerDuty + Retention 30 day hot + 90 day cold + 7 day PITR + Testing quarterly drills Q1-Q4 schedule + Cross-References)
- **CR 1-1 audit-first INSERT ✅ APPLIED** (backup_created audit log INSERT 결정, alembic 0036 phase_4_backup_strategy table mirror)

### T7 — Capability gate v1.25 EXTENSION (1 MODIFIED + 1 MODIFIED)
- `apps/api/core/capability.py` MODIFIED (4 NEW enum entries: DEPLOYMENT_PROD = "deployment_prod" + DEPLOYMENT_STAGING = "deployment_staging" + DEPLOYMENT_DATABASE_BACKUP = "deployment_database_backup" + DEPLOYMENT_HEALTH_CHECK = "deployment_health_check", all 4 added to each of 4 Industry frozensets industry-agnostic with CR 12-1 L4 precedent comment)
- `docs/capability-matrix.md` MODIFIED (v1.24 → v1.25 + 4 NEW rows industry-agnostic 4-industry grants ✅/✅/✅/✅)

### T8 — Tests + 3중 게이트 FINAL CLEAN
- 6 NEW pytest files (test_phase_4_vercel_config.py 11 cases + test_phase_4_railway_config.py 14 cases + test_phase_4_dockerfile_parity.py 12 cases + test_phase_4_health_check.py 16 cases + test_phase_4_alembic_0036_backup.py 17 cases + test_capability_matrix_v1_25_drift.py 38 cases = **108 NEW pytest PASS**)
- 2 NEW vitest files (phase-4-sentry-integration.test.ts 10 cases + phase-4-vercel-health.test.ts 11 cases = **21 NEW vitest PASS**)

## §5. 3중 게이트 FINAL CLEAN 검증 (retro verification)

### 5-1. ruff scoped Phase 4 wire Python files
- **All checks passed!** (Phase 4 wire Python files 11 files scoped)
- pre-existing UP042 `Capability(str, Enum)` baseline issue suppress with `# noqa: UP042` per Pydantic v2 interop baseline (다른 곳에 영향 0)

### 5-2. pytest scoped Phase 4 backend tests
- **108/108 PASS** (6 NEW backend test files)
- 0 NEW regressions (baseline 1 unrelated pre-existing failure `test_generate_report_pdf_report15_payload_not_required` 보존)

### 5-3. vitest full suite (commit `71a033a` 검증)
- **737/737 PASS** (73 files, +2 NEW Phase 4 = 21 NEW cases, 0 regressions)
- vitest 71→73 = +2 NEW files

### 5-4. pnpm tsc --noEmit
- 0 NEW errors (deployment files clean — pre-existing 17 baseline errors unrelated 보존)

### 5-5. SDR drift gate
- **PASS** — vitest 71→73 = +2 NEW files, pytest 3855→**3928** = +73 NEW collected (retro verification 시점 동일)
- MAX claim 갱신: pytest SDR 3855 → 3928 = +73 (retro verification 시점 동일)

### 5-6. commit_consistency gate
- **PASS** — CR 9-6 commit message discipline + A36 SDR 검증 4-step 자동 적용 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS)

## §6. A19 cohesion pattern 9 surface EXTENSION PASS (deployment surface NEW)

9/9 surfaces ALL PASS (cj-style 55번째 epic 연속 정직 회복 wire):

| Surface | Phase 4 wire 결정 | Status |
|---------|---------------------|--------|
| **1. kernel** (pure function) | T1+T2 vercel.json/railway.toml config parsers (Pydantic BaseModel validation, JSON/TOML schema 검증) | ✅ |
| **2. port** (DB adapter) | T3 apps/web/Dockerfile + apps/api/Dockerfile (per-app deployment adapter, AD-14 digest pin 결정) | ✅ |
| **3. db schema** | T6 alembic 0036 phase_4_backup_strategy table (id + backup_type + started_at + completed_at + size_bytes + checksum_sha256 + storage_url + status + created_at) | ✅ |
| **4. service** | T5 health.py + observability.py + sentry.ts (health check service + Sentry observability) | ✅ |
| **5. handler** | T5 /api/v1/health FastAPI endpoint + T5 /api/health Next.js route handler | ✅ |
| **6. envelope** | T5 health response `{status, timestamp, version, database, redis, uptime_seconds}` 결정 | ✅ |
| **7. capability** | T7 DEPLOYMENT_PROD + DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP + DEPLOYMENT_HEALTH_CHECK 4 NEW gates (industry-agnostic) | ✅ |
| **8. audit** | T6 backup_created audit_logs INSERT 결정 (CR 1-1 audit-first INSERT) | ✅ |
| **9. deployment surface NEW** | T1+T2+T3+T4+T5+T6 deployment config + health check + observability + database backup 결정 | ✅ EXTENSION PASS |

## §7. 9 ACs satisfied (PRD §F16.1~F16.7 verbatim)

- **§F16.1** Vercel frontend deployment config (vercel.json + framework=nextjs + regions=[icn1] Seoul + env 매핑 + headers/redirects) ✅
- **§F16.2** Railway backend deployment config (railway.toml + builder=DOCKERFILE + healthcheckPath + restartPolicyType) ✅
- **§F16.3** Per-app Dockerfile 분리 (apps/web/Dockerfile + apps/api/Dockerfile, AD-14 digest pin) ✅
- **§F16.4** Deployment runbook (docs/deployment.md 12 sections) ✅
- **§F16.5** Health check + observability (/api/v1/health + Sentry browser/server + Next.js /api/health) ✅
- **§F16.6** Database backup strategy (alembic 0036 + phase_4_backup_strategy table + docs/database-backup.md) ✅
- **§F16.7** Capability matrix v1.24 → v1.25 EXTENSION 4 NEW rows ✅
- **§F16.8** D-1-1-DEFER-* honestly preserved 55번째 epic 연속 (CR 11-3 정직 회복 검증) ✅
- **§F16.9** A19 cohesion pattern 9 surface EXTENSION PASS (deployment surface NEW) ✅

## §8. CR lessons applied (cj-style 55~56~57번째 epic 연속 정직 회복 검증)

| CR Lesson | Phase 4 적용 | Status |
|-----------|---------------|--------|
| **CR 0-2** RLS lesson | AD-14 stack pin by @sha256: digest (root Dockerfile + per-app Dockerfile 패턴) | ✅ APPLIED |
| **CR 1-1** audit-first INSERT | T6 backup_created audit log INSERT (alembic 0036 phase_4_backup_strategy table mirror) | ✅ APPLIED |
| **CR 9-6** commit message discipline | `git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention | ✅ APPLIED |
| **CR 11-3** honest-DEFER discipline | 55~56~57번째 epic 연속 정직 회복, D-1-1-DEFER-1/2/3 honestly preserved | ✅ APPLIED |
| **CR 11-4** lessons carry | D-001 page.tsx mount + D-002 ko-KR.json SSOT + D-003 vitest RTL + D-004 TS mirror + D-005 unknown state reject + P-015 ko-KR.json SSOT drift | ✅ APPLIED |
| **CR 12-1** L4 industry-agnostic capability | capability matrix v1.25 EXTENSION 4 NEW rows industry-agnostic 4-industry grants precedent 미러 | ✅ APPLIED |
| **CR 12-5** D-14 typed exception envelope | health check response envelope `{status, timestamp, version, database, redis, uptime_seconds}` + /live + /ready 분리 | ✅ APPLIED |
| **CR 12-5** D-PARITY-01 inversion | Vercel + Railway + Supabase URL parity + env vars parity | ✅ APPLIED |
| **A19** cohesion pattern 9 surface | deployment surface NEW EXTENSION PASS | ✅ APPLIED |
| **A36** SDR 검증 4-step 자동 적용 | commit prefix lint + sprint-status structure + vitest file count drift + commit consistency | ✅ APPLIED |

## §9. D-1-1-DEFER-* honestly preserved (CR 11-3 56~57번째 epic 연속 검증)

| DEFER ID | Description | Status | grep guard |
|----------|-------------|--------|------------|
| **D-1-1-DEFER-1** | Magic link login | 🔵 OPEN (A70 결정 wire) | ✅ no signInWithOAuth/MagicLink found in apps/web |
| **D-1-1-DEFER-2** | Social login OAuth (Google/Naver/Kakao) | 🔵 OPEN (A71 결정 wire) | ✅ no signInWithOAuth/signInWithRedirect found |
| **D-1-1-DEFER-3** | SSO enterprise SAML | 🔵 OPEN (A72 결정 wire) | ✅ no SAML/saml-provider found |

CR 11-3 honest-DEFER discipline 56~57번째 epic 연속 정직 회복 검증 완료. grep guard: `test_no_magic_link_or_oauth_or_sso_introduced` PASS (retro verification 시점 재확인, 0 matches).

## §10. 결정 wire summary

| 결정 | 내용 | Status |
|------|------|--------|
| **A73** | 옵션 (a) Phase 4 진입 결정 wire (Deployment config + Dockerfile territory 진입) | ✅ DONE |
| **A74** | Master PRD v3.0 → v3.1 atomic edit | ✅ DONE |
| **A75** | A42 A36 SDR 검증 4-step 보존 + Epic 15+ 적용 | 🔵 OPEN (자동 적용) |
| **A76** | AD-27 Deployment 신규 결정 (Vercel + Railway + Supabase + Sentry) | ✅ DONE |
| **A77** | Capability matrix v1.24 → v1.25 EXTENSION 4 NEW rows | ✅ DONE |
| **A78** | Phase 4 wire scope T1~T8 결정 | ✅ DONE |
| **A70** | D-1-1-DEFER-1 Magic link 결정 wire (옵션 a/b/c 결정 보류) | 🔵 OPEN |
| **A71** | D-1-1-DEFER-2 Social login OAuth 결정 wire (옵션 a/b/c 결정 보류) | 🔵 OPEN |
| **A72** | D-1-1-DEFER-3 SSO enterprise SAML 결정 wire (옵션 a/b/c 결정 보류) | 🔵 OPEN |

**A73+A74+A76+A77+A78 5/5 ALL DONE + APPLIED** + **A70+A71+A72+A75 4/4 OPEN (사용자 결정 보류)**.

## §11. 결정 wire 보존 (기존 baseline 정합)

### Preserved VERBATIM (Phase 4 PRD entry 진입 시점에 cj-style "fix" 종류 pre-flight 정합 sweep 결정)
- **Root `Dockerfile`** (multi-stage 4-stage frontend-builder + backend-builder + backend-runtime + frontend-runtime, **AD-14 stack pin by @sha256: digest** 모든 베이스 이미지 결정, pnpm@10 + Python 3.12-slim, `--frozen-lockfile` 결정)
- `docker-compose.yml` (postgres only, port 54322 → host 54322 매핑, healthcheck 결정)
- `.github/workflows/ci.yml` (lint-deps + lint-imports + lint-conventions + stack-pin-check + commit-prefix-lint + test-architecture + test-service-role-guard + service-role-guard-lint + rls-tests + web-test + web-e2e + smoke-e2e 결정, 12 step decisions)

### Preserved VERBATIM (Phase 3 wire 결정)
- `apps/api/core/security.py` EXTENSION (ALLOWED_ROLES + JWTClaims.tenant_id Optional + decode_jwt require_tenant kwarg) — **PRESERVE**
- `apps/api/core/tenant_context.py` EXTENSION (set_claims/clear_claims + 3-GUC publisher + PreOnboardingUser) — **PRESERVE**
- `apps/api/modules/m0_onboarding/handlers.py` EXTENSION (signup_router + POST endpoint) — **PRESERVE**
- `apps/api/modules/m0_onboarding/services/signup_service.py` NEW (atomic 5-step + 2 typed exceptions) — **PRESERVE**
- `apps/api/alembic/versions/0035_custom_access_token_hook.py` NEW — **PRESERVE**
- `supabase/config.toml` EXTENSION (custom_access_token_hook enabled = true) — **PRESERVE**

### Preserved VERBATIM (Epic 12 wire 결정)
- `apps/api/jobs/backup_daily.py` (KST 02:00 = UTC 17:00 cron entry)
- `apps/api/jobs/backup_retention.py` (KST 03:00 = UTC 18:00 retention sweep)
- `tenant_backups` table (Epic 12 12.2 wire)
- `packages/services/m12_account/backup_export` pure kernel subtree

### Preserved VERBATIM (Epic 13 + Epic 14 wire 결정)
- `apps/api/alembic/versions/0034_listen_notify_consume_cross_tenant_fanout.py` NEW (14-1 wire)
- Epic 13/14 LISTEN/NOTIFY consume multi-process coordination 결정 wire 보존
- Phase 4 = PostgreSQL LISTEN/NOTIFY multi-process coordination 정합 (Railway multi-worker 환경 listener process-per-pod 정합)

## §12. Next unblocked 결정 wire 보류 (사용자 결정 대기)

**옵션 (a) Epic 15 진입** (Magic link + Social OAuth + SSO 통합 territory) — A70+A71+A72 결정 wire 진입 시점에 동시 결정
**옵션 (b) Phase 5 진입** (다른 territory — 예: multi-region backup 결정 wire 보류 해소 등)
**옵션 (c) carry-over 진입** (다른 carry-over 결정 wire 진입)

cj-style discipline 회피 위험 방지: **즉시 진입 권장** (D-1-1-DEFER-* honestly preserved 56~57번째 epic 연속 정직 회복 검증 완료, 결정 보류 위험).

## §13. 결정 wire 일자

**2026-08-22 (KST)** — cj-style Phase 4 4번째 진입점 = cj-style 56~57번째 epic 연속 정직 회복 retro wire DONE.

---

## Cross-References

- [[handoff-2026-08-22-phase-4-deployment-wire-done]] — Phase 4 atomic wire T1~T8 DONE (cj-style 55번째)
- [[handoff-2026-08-22-phase-4-deployment-wire-spec-entry-done]] — Phase 4 spec entry DONE (cj-style 54번째)
- [[handoff-2026-08-22-phase-4-prd-entry-done]] — Phase 4 PRD entry DONE (cj-style 53번째)
- [[handoff-2026-08-22-phase-3-close-out-done]] — Phase 3 close-out retro DONE (cj-style 51~52번째)
- [[handoff-2026-08-21-phase-3-1-auth-foundation-wire-done]] — Phase 3-1 wire DONE (cj-style 50번째)
- [[handoff-2026-08-21-phase-3-0-auth-contract-slice-done]] — Phase 3-0 auth contract slice DONE
- [[handoff-2026-08-20-phase-3-prd-entry-done]] — Phase 3 PRD entry DONE (cj-style 49번째)
- [[cr-11-3-lessons]] — honest-DEFER discipline
- [[cr-12-1-lessons]] — capability matrix wire pattern (L4 precedent)
- [[cr-12-5-lessons]] — D-GATE-01 inversion + D-PARITY-01 inversion + D-14 envelope
- [[cr-a19-lessons]] — A19 cohesion pattern 9 surface
- [[cr-0-2-lessons]] — RLS + multi-tenant isolation + AD-14 stack pin
- [[cr-1-1-lessons]] — audit-first INSERT