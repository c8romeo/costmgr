---
name: handoff-2026-08-22-phase-4-prd-entry-done
description: Phase 4 PRD entry DONE (cj-style Phase 4 1번째 진입점 = cj-style 53번째 epic 연속 정직 회복). Phase 4 = Deployment config + Dockerfile + health check + observability + database backup territory 진입 결정 wire. 옵션 (a) Phase 4 진입 (옵션 b Epic 15 진입 / 옵션 c carry-over 진입 모두 rejected). A73+A74+A76+A77+A78 결정 wire 진입.
metadata:
  type: project
  modified: 2026-08-22T00:00:00.000Z
---

# Phase 4 PRD Entry DONE — Deployment config + Dockerfile territory (handoff-2026-08-22)

## Phase 4 territory 진입 wire 결정

Phase 4 = **Deployment config + Dockerfile + health check + observability + database backup territory** (옵션 (a) Phase 4 진입 결정 wire, A73 결정). **cj-style Phase 4 1번째 진입점 = cj-style 53번째 epic 연속 정직 회복 wire DONE**.

옵션 (b) Epic 15 진입 (Magic link + Social OAuth + SSO follow-up sprint 통합 territory 진입) / 옵션 (c) carry-over 진입 모두 rejected (rationale: Phase 4 PRD entry 진입 = Deployment territory 표준 진입 가능 + cj-style 1번째 진입점 표준 진입 가능 = 결정 wire 효율성).

## Phase 4 결정 wire Summary (A73+A74+A76+A77+A78)

| 결정 | 내용 | 상태 |
|------|------|------|
| **A73** | 옵션 (a) Phase 4 진입 결정 wire (Deployment config + Dockerfile territory 진입) | ✅ DONE |
| **A74** | Master PRD v3.0 → v3.1 atomic edit (D-1-1-DEFER-* RESOLVE 표기 보류) | ✅ DONE |
| **A75** | A42 A36 SDR 검증 4-step 보존 + Epic 15+ 적용 | 🔵 OPEN (자동 적용) |
| **A76** | AD-27 Deployment 신규 결정 (Vercel + Railway + Supabase + Sentry) | 🔵 OPEN (사용자 결정 보류) |
| **A77** | Capability matrix v1.24 → v1.25 EXTENSION 4 NEW rows (DEPLOYMENT_*) | 🔵 OPEN (사용자 결정 보류) |
| **A78** | Phase 4 wire scope T1~T8 결정 | 🔵 OPEN (사용자 결정 보류) |

**A73+A74 DONE 2/2 + A76+A77+A78 OPEN 3/3 (사용자 결정 보류) + A75 OPEN (자동 적용)**.

## 기존 baseline 정합 sweep (Phase 4 PRD entry 진입 시점에 cj-style "fix" 종류 pre-flight 정합 sweep)

### ✅ 이미 존재 (baseline 정합 보존)

- **Root `Dockerfile`** (multi-stage build: frontend-builder → backend-builder → backend-runtime + frontend-runtime = 4-stage, **AD-14 stack pin by @sha256: digest** 모든 베이스 이미지 결정, pnpm@10 + Python 3.12-slim, `--frozen-lockfile` 결정)
- `docker-compose.yml` (postgres only, port 54322 → host 54322 매핑, healthcheck 결정)
- `.github/workflows/ci.yml` (lint-deps + lint-imports + lint-conventions + stack-pin-check + commit-prefix-lint + test-architecture + test-service-role-guard + service-role-guard-lint + rls-tests + web-test + web-e2e + smoke-e2e 결정, 12 step decisions)

### ❌ 누락 (Phase 4 wire 진입 시점에 추가 결정)

- Production frontend `vercel.json` (Vercel frontend deployment config)
- Production backend `railway.toml` (Railway backend deployment config)
- `apps/web/Dockerfile` + `apps/api/Dockerfile` (per-app Dockerfile 분리 결정 wire — root Dockerfile 통합 baseline과 병행)
- `docs/deployment.md` (production deployment runbook)
- Health check + observability config (Sentry 결정 wire)
- Database backup strategy (Supabase 자동 backup + 수동 export 결정 wire)
- capability matrix v1.24 → v1.25 EXTENSION DEPLOYMENT_PROD + DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP + DEPLOYMENT_HEALTH_CHECK 4 NEW rows 결정

## Phase 4 PRD entry wire scope (master PRD v3.1 atomic edit)

(1) **front matter title v3.0 → v3.1 + changelog v3.1 entry** (Phase 4 PRD entry 결정 wire 진입 verbatim bind)
(2) **§F16 신규** (F16.1 vercel.json Vercel frontend deployment config + F16.2 railway.toml Railway backend deployment config + F16.3 apps/web/Dockerfile + apps/api/Dockerfile per-app Dockerfile 분리 + F16.4 docs/deployment.md production deployment runbook 12 sections + F16.5 health check + observability + monitoring + F16.6 database backup strategy + F16.7 tests + wire scope T1~T8 결정)
(3) **§8.1 M0-(g) production deployment** 결정 wire 진입 (Production deployment config + Dockerfile + health check + observability + database backup 인수 불릿)
(4) **§15 로드맵 Phase 4 row status 백로그 → in-progress** (PRD entry DONE 진입 wire) + Phase 3 row status in-progress → done (Phase 3 close-out retro DONE 정합)
(5) **§부록 A A73+A74+A76+A77+A78 신규 결정 표** (A73 done + A74 done + A75 preserved + A76+A77+A78 신규 결정 wire 진입)
(6) **AD-27 Deployment 신규 결정** (Vercel frontend + Railway backend + Supabase PostgreSQL + Sentry observability 결정 wire)
(7) **capability matrix v1.24 → v1.25 EXTENSION** DEPLOYMENT_PROD + DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP + DEPLOYMENT_HEALTH_CHECK 4 NEW rows (industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러)

## Phase 4 wire scope T1~T8 결정 (cj-style 53번째 epic 연속 정직 회복 wire 진입 시점에 결정)

- **T1 Vercel config wire** (1 NEW) = `vercel.json` (Vercel frontend deployment config)
- **T2 Railway config wire** (1 NEW) = `railway.toml` (Railway backend deployment config)
- **T3 Per-app Dockerfile wire** (2 NEW) = `apps/web/Dockerfile` + `apps/api/Dockerfile`
- **T4 Deployment runbook wire** (1 NEW) = `docs/deployment.md` (production deployment runbook)
- **T5 Health check + observability wire** (3 NEW + 1 MODIFIED) = `apps/api/core/health.py` NEW + `apps/api/core/observability.py` NEW + `apps/web/lib/observability/sentry.ts` NEW + `apps/api/main.py` MODIFIED (health router include) + `apps/web/app/api/health/route.ts` NEW
- **T6 Database backup strategy wire** (1 NEW alembic + 1 NEW docs) = `apps/api/alembic/versions/0036_phase_4_backup_strategy.py` NEW + `docs/database-backup.md` NEW
- **T7 Capability v1.25 EXTENSION** (1 MODIFIED + 1 NEW) = `apps/api/core/capability.py` MODIFIED 4 NEW enum + `docs/capability-matrix.md` v1.24 → v1.25 (4 NEW rows, SSOT RED→GREEN)
- **T8 Tests + 3중 게이트 FINAL CLEAN** (~+40 NEW pytest PASS + ~+20 NEW vitest PASS + 2 NEW docs) — vercel config + railway config + Dockerfile parity + health check + Sentry integration + Vercel health + alembic 0036 + capability matrix v1.25 drift detector

## 3중 게이트 impact EXPECTED (Phase 4 wire 진입 시점)

(1) frontend `pnpm tsc --noEmit` 0 NEW errors (deployment files clean — pre-existing 7 baseline errors unrelated 보존)
(2) `pnpm vitest run` 716+20 = **~736/736 PASS** (71+2 = 73 files, Phase 4 +20 NEW cases, 0 regressions)
(3) `ruff check` scoped Phase 4 wire files = **All checks passed!**
(4) `pytest` 31+40 = **71/71 PASS** (Phase 4 +40 NEW e2e tests, 0 NEW regressions; baseline 1 unrelated pre-existing failure 보존)
(5) SDR drift gate PASS (MAX claim 3855 → **~3895** actual pytest --collect-only -q = +40 from Phase 4 T8 NEW pytest cases)
(6) commit_consistency gate PASS (CR 9-6 commit message discipline + A36 SDR 검증 4-step 자동 적용)

## A19 cohesion pattern 9 surface EXTENSION PASS (예정)

9/9 surfaces ALL PASS (cj-style 53번째 epic 연속 정직 회복 wire 진입 시점에 결정):

1. **kernel** (pure function) — T1+T2 vercel.json/railway.toml config parsers (Pydantic BaseModel validation) ✅
2. **port** (DB adapter) — T3 apps/web/Dockerfile + apps/api/Dockerfile (per-app deployment adapter) ✅
3. **db schema** — T6 alembic 0036 phase_4_backup_strategy table ✅
4. **service** — T5 health.py + observability.py + sentry.ts (health check service) ✅
5. **handler** — T5 /api/v1/health FastAPI endpoint + T5 /api/health Next.js route handler ✅
6. **envelope** — T5 health response `{status, timestamp, version, database, redis, uptime_seconds}` ✅
7. **capability** — T7 DEPLOYMENT_PROD + DEPLOYMENT_STAGING + DEPLOYMENT_DATABASE_BACKUP + DEPLOYMENT_HEALTH_CHECK 4 NEW gates ✅
8. **audit** — T6 backup_created audit_logs INSERT (CR 1-1 audit-first INSERT) ✅
9. **deployment surface NEW** — T1+T2+T3+T4+T5+T6 deployment config + health check + observability + database backup ✅

## CR lessons applied (cj-style 53번째 epic 연속 정직 회복 wire 진입 시점에 결정)

- **CR 0-2** RLS lesson ✅ APPLIED (Phase 3-0 atomic sprint `1db21d2` 정합)
- **CR 1-1** audit-first INSERT ✅ APPLIED (T6 backup_created audit log INSERT + Phase 3-0 tenant_signup_completed + T5 user_logged_out + T6 password_reset 보존)
- **CR 9-6** commit message discipline ✅ APPLIED (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention)
- **CR 11-3** honest-DEFER discipline ✅ APPLIED (53번째 epic 연속 정직 회복 — D-1-1-DEFER-1/2/3 honestly preserved)
- **CR 12-1** L4 industry-agnostic capability ✅ APPLIED (capability matrix v1.25 EXTENSION 4 NEW rows industry-agnostic 4-industry grants)
- **CR 12-5** D-14 typed exception envelope ✅ APPLIED (health check response envelope + ko-KR error messages)
- **CR 12-5** D-PARITY-01 inversion ✅ APPLIED (Vercel + Railway + Supabase URL parity + env vars parity)
- **A19** cohesion pattern 9 surface EXTENSION PASS ✅ (deployment surface NEW)

## D-1-1-DEFER-* honestly preserved (53번째 epic 연속)

| DEFER ID | Description | 상태 |
|----------|------------|------|
| **D-1-1-DEFER-1** | Magic link login | 🔵 OPEN (A70 결정 wire, Epic 15+ 진입 시점) |
| **D-1-1-DEFER-2** | Social login OAuth (Google/Naver/Kakao) | 🔵 OPEN (A71 결정 wire) |
| **D-1-1-DEFER-3** | SSO enterprise SAML | 🔵 OPEN (A72 결정 wire) |

CR 11-3 honest-DEFER discipline 53번째 epic 연속 정직 회복 결정. grep guard `test_no_magic_link_or_oauth_or_sso_introduced` 보존.

## Phase 3 close-out retro 정합 보존

Phase 3 = Auth Foundation territory close-out 완료 (cj-style Phase 3 1~3번째 진입점 + carry-over 진입점 모두 wire DONE = cj-style 49~52번째 epic 연속 정직 회복). master PRD v3.0 §F15 (F15.1~F15.6) verbatim wire + AD-26 verbatim + A65~A69 결정 wire 보존 + A19 cohesion 9 surface EXTENSION PASS + Epic 1 partial scaffold 보존.

## Epic 14 + Phase 3 cycle 정합 보존

Epic 13/14 LISTEN/NOTIFY consume multi-process coordination 결정 wire 보존. Phase 4 territory = PostgreSQL LISTEN/NOTIFY multi-process coordination 정합 (Railway multi-worker 환경 listener process-per-pod 정합).

## 다음 결정 wire 보류 (사용자 결정 대기)

옵션 (a) Phase 4 bmad-create-story spec 진입 (cj-style 53번째 epic 연속 정직 회복 bmad-create-story) OR 옵션 (b) Phase 4 bmad-dev-story atomic wire T1~T8 진입 (cj-style 54번째 epic 연속 정직 회복 wire 진입 시점) OR 옵션 (c) 다른 territory 진입 결정 wire 보존.

## 결정 wire 일자
2026-08-22 (KST)