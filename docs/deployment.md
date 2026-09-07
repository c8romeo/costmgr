# Costmgr Production Deployment Runbook

> **Phase 4 (cj-style 55번째 epic 연속 정직 회복 wire)** — Production deployment guide for Vercel (frontend) + Railway (backend) + Supabase (PostgreSQL) + Sentry (observability). 12 sections covering architecture, prerequisites, step-by-step deployment, env vars, health check, monitoring, backup, rollback, smoke test, troubleshooting, security, cost estimation.

## Table of Contents

1. [Purpose](#1-purpose)
2. [Architecture](#2-architecture)
3. [Prerequisites](#3-prerequisites)
4. [Step-by-Step Deployment Guide](#4-step-by-step-deployment-guide)
5. [Environment Variables SSOT](#5-environment-variables-ssot)
6. [Health Check + Monitoring](#6-health-check--monitoring)
7. [Database Backup + Restore](#7-database-backup--restore)
8. [Rollback Strategy](#8-rollback-strategy)
9. [Smoke Test](#9-smoke-test)
10. [Troubleshooting](#10-troubleshooting)
11. [Security](#11-security)
12. [Cost Estimation](#12-cost-estimation)

---

## 1. Purpose

This runbook describes how to deploy `costmgr` to a production environment with:

- **Frontend** (Next.js 15 monorepo web app) on **Vercel**
- **Backend** (FastAPI modular monolith) on **Railway** (Dockerfile-based)
- **PostgreSQL database** on **Supabase** (managed Postgres with PITR)
- **Observability** via **Sentry** (browser + server)
- **Backup strategy** via Supabase PITR + manual exports (alembic 0036)

Target audience: DevOps engineer + product owner performing the initial deployment or a rollback.

## 2. Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vercel Edge   │───▶│  Railway (API)  │───▶│ Supabase (DB)   │
│  Next.js 15     │    │   FastAPI       │    │  PostgreSQL 15  │
│  apps/web/      │    │   apps/api/     │    │                 │
│  Standalone     │    │   Dockerfile    │    │  + PITR 7 days  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                      │                       │
        └──────────────────────┼───────────────────────┘
                               ▼
                       ┌─────────────────┐
                       │ Sentry (DSN)    │
                       │  traces 10%     │
                       │  errors 100%    │
                       └─────────────────┘
```

- **Vercel** serves the Next.js frontend from a single monorepo (root `vercel.json` SSOT).
- **Railway** runs the FastAPI backend from a per-app Dockerfile (`apps/api/Dockerfile`).
- **Supabase** provides managed PostgreSQL with PITR (Point-in-Time Recovery, 7-day retention on Pro plan).
- **Sentry** collects errors and traces from both browser (Next.js) and server (FastAPI) tiers.

### Deployment Config SSOT

| File | Purpose | Owner |
|------|---------|-------|
| `vercel.json` (root) | Vercel frontend build + headers + redirects | Frontend |
| `railway.toml` (root) | Railway backend deployment + health check | Backend |
| `apps/web/Dockerfile` | Vercel per-app frontend container (preserved + extended) | Frontend |
| `apps/api/Dockerfile` | Railway per-app backend container | Backend |
| `Dockerfile` (root) | CI/local development stack (4-stage, AD-14 pinned) | CI |
| `docker-compose.yml` | Local Postgres (port 54322, AD-14 pinned) | Dev |
| `.github/workflows/ci.yml` | CI workflow (12 step decisions) | CI |

## 3. Prerequisites

Before deploying, ensure you have:

- [ ] **Vercel account** (Pro plan recommended for production traffic + team seats)
- [ ] **Railway account** (Hobby plan $5/month + usage, Pro plan for teams)
- [ ] **Supabase project** (Pro plan for PITR 7-day retention + daily backups)
- [ ] **Sentry project** (Free tier supports 5K errors/month; Team tier for production)
- [ ] **GitHub repository** with push access to `main` branch
- [ ] **DNS provider** access (if custom domain — Vercel + Railway both support)
- [ ] **Secrets manager** (1Password / Vault) for env var storage

### Required Services

| Service | Tier | Estimated Monthly Cost (USD) |
|---------|------|------------------------------|
| Vercel Pro | $20/seat/month | $20+ |
| Railway Hobby | $5 + usage | $5–25 |
| Supabase Pro | $25/month | $25+ |
| Sentry Team | $26/month | $26+ |
| **Total estimated** | | **~$76–96/month** |

## 4. Step-by-Step Deployment Guide

### Step 1 — Supabase Setup

1. Create a new Supabase project at <https://supabase.com/dashboard>.
2. Choose region `ap-northeast-2` (Seoul) to match Vercel `icn1` for low latency.
3. Save the following values to your secrets manager:
   - `SUPABASE_URL` — Project URL (e.g., `https://abcxyz.supabase.co`)
   - `SUPABASE_ANON_KEY` — Public anon key
   - `SUPABASE_SERVICE_ROLE_KEY` — Service role key (admin)
   - `SUPABASE_JWT_SECRET` — JWT secret (Settings → API → JWT Settings)
   - `DATABASE_URL` — Direct connection string (Settings → Database → Connection string)

4. Run Alembic migrations:

```bash
DATABASE_URL=postgresql://postgres:...@db.abcxyz.supabase.co:5432/postgres \
  uv run alembic upgrade head
```

5. Enable the `custom_access_token_hook` (Phase 3-0 wire):

```toml
# supabase/config.toml
[auth.hook.custom_access_token]
enabled = true
uri = "pg-functions://postgres/public/custom_access_token_hook"
```

6. Configure PITR (Settings → Database → Point in Time Recovery → Enable).

### Step 2 — Backend Deployment (Railway)

1. Create a new Railway project at <https://railway.app/new>.
2. Connect the GitHub repository (`costmgr` monorepo).
3. Railway auto-detects `railway.toml` (Phase 4 wire) and uses `apps/api/Dockerfile`.
4. Configure environment variables (see §5 below).
5. Deploy and verify the health check:

```bash
curl https://<your-api>.railway.app/api/v1/health
# Expected: {"status":"healthy","timestamp":"...","version":"0.1.0","database":"connected","redis":"disconnected","uptime_seconds":42}
```

### Step 3 — Frontend Deployment (Vercel)

1. Import the GitHub repository at <https://vercel.com/new>.
2. Vercel auto-detects `vercel.json` (Phase 4 wire) and configures:
   - Framework: Next.js
   - Build command: `pnpm --filter web build`
   - Output directory: `apps/web/.next`
   - Region: `icn1` (Seoul)
3. Configure environment variables (see §5 below).
4. Deploy and verify:

```bash
curl https://<your-app>.vercel.app/api/health
# Expected: {"status":"healthy","build":"<git-sha>","region":"icn1"}
```

### Step 4 — DNS / Custom Domain

1. In Vercel, add a custom domain (e.g., `app.costmgr.com`).
2. In Railway, add a custom domain for the API (e.g., `api.costmgr.com`).
3. Update `NEXT_PUBLIC_API_BASE_URL` in Vercel to point to the Railway domain.
4. Configure SSL via Vercel's automatic Let's Encrypt integration.

### Step 5 — Pilot tenant provisioning (cj-304 wire 결정 wire)

For the 8-week pilot program (2026-09-14 ~ 2026-11-09 KST, 5-10 SaaS 제조 스타트업), each customer tenant must be onboarded with isolated context + admin user + capability grants. Use the CLI script:

```bash
# Dry-run (mandatory default for safety):
uv run python apps/api/scripts/cli/pilot_tenant_provision.py \
  --tenant-id="$(uuidgen)" \
  --industry="saas_manufacturing" \
  --admin-email="cfo@customer.com" \
  --admin-display-name="Customer Admin" \
  --finance-contact-email="finance@customer.com" \
  --dry-run

# Apply (only after dry-run output reviewed):
uv run python apps/api/scripts/cli/pilot_tenant_provision.py \
  --tenant-id="$(uuidgen)" \
  --industry="saas_manufacturing" \
  --admin-email="cfo@customer.com" \
  --admin-display-name="Customer Admin" \
  --finance-contact-email="finance@customer.com"
```

The CLI:
1. Creates a `tenants` row (idempotent — re-runs are safe).
2. Creates an owner user with `TWO_FACTOR_AUTH` capability (AD-22 verbatim).
3. Grants 4 capabilities: `EXPORT_CSV` + `EXPORT_PDF` + `EXPORT_EMAIL` + `EXPORT_SCHEDULED`.
4. Inserts an audit log row `pilot_tenant_provisioned` (AD-2 verbatim + ActionClass.REPORTS).

### Step 6 — Production initial seed (platform admin + default cron)

After Step 5 (or before, depending on operator preference), initialize the platform:

```sql
-- 1. Insert platform owner user (manual — only once)
INSERT INTO users (id, email, role, two_factor_enabled, ...)
VALUES ('<platform-admin-uuid>', 'admin@costmgr.com', 'owner', true, ...);

-- 2. Insert capability grants (EXPORT_*) — already handled by alembic 0061
-- Verify: SELECT * FROM capability_grants WHERE industry IN ('saas_manufacturing', ...);

-- 3. Verify scheduled reports cron expressions — apps/api/jobs/scheduled_reports.py SCHEDULED_REPORTS_CRON_EXPRESSIONS
-- No DB seed needed — cron expressions are hardcoded in source code.
```

**Note**: For production, prefer operating via the pilot CLI (Step 5) per-tenant over a global seed script — this keeps the audit log per-action attributable to a specific operator.

## 5. Environment Variables SSOT

### Backend (Railway)

| Variable | Required | Source | Notes |
|----------|----------|--------|-------|
| `DATABASE_URL` | ✅ | Supabase | Direct connection string (port 5432) |
| `SUPABASE_URL` | ✅ | Supabase | Project URL |
| `SUPABASE_ANON_KEY` | ✅ | Supabase | Public anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ | Supabase | Service role key (admin) |
| `SUPABASE_JWT_SECRET` | ✅ | Supabase | JWT secret (Settings → API) |
| `SENTRY_DSN` | ✅ | Sentry | Server-side DSN |
| `POSTMARK_SERVER_TOKEN` | ✅ | Postmark | **cj-299 OQ-EPIC30+-2 결정 wire** — Story 30.3 Email delivery. Production REQUIRES (없으면 LoggingProvider fallback → stdout 로그만). Postmark Sandbox: 100건/month free at <https://postmarkapp.com>. |
| `POSTMARK_FROM_EMAIL` | ❌ | Manual | Default `noreply@costmgr.bizup.io`. 운영자 override 가능. |
| `TZ` | ✅ | Manual | **cj-300 OQ-EPIC30+-3 결정 wire** — `Asia/Seoul` mandatory. Railway 기본 UTC → 24h cron 오프셋 방지. |
| `RETRY_BACKOFF_MINUTES` | ❌ | Manual | Default `1,5,30`. Exponential backoff for scheduled report failures. |
| `ENVIRONMENT` | ✅ | Manual | `production` |
| `PORT` | ❌ | Default | Railway auto-provides |

### Frontend (Vercel)

| Variable | Required | Source | Notes |
|----------|----------|--------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | ✅ | Supabase | Same as backend `SUPABASE_URL` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | ✅ | Supabase | Same as backend `SUPABASE_ANON_KEY` |
| `NEXT_PUBLIC_API_BASE_URL` | ✅ | Railway | Backend URL (e.g., `https://api.costmgr.com`) |
| `NEXT_PUBLIC_SENTRY_DSN` | ✅ | Sentry | Browser DSN (separate from server DSN) |
| `NEXT_PUBLIC_ENVIRONMENT` | ✅ | Manual | `production` |

### SSOT mapping rule (CR 12-5 D-PARITY-01 inversion)

Frontend `NEXT_PUBLIC_SUPABASE_URL` MUST equal backend `SUPABASE_URL`. Frontend `NEXT_PUBLIC_SUPABASE_ANON_KEY` MUST equal backend `SUPABASE_ANON_KEY`. This ensures that Supabase session validation (browser-side `createServerClient`) and FastAPI JWT decoding (server-side) refer to the same authority.

## 6. Health Check + Monitoring

### Endpoints

| Endpoint | Purpose | Used by |
|----------|---------|---------|
| `GET /api/v1/health` | FastAPI backend health (DB + JWT verification) | Railway healthcheck, ops dashboard |
| `GET /api/v1/health/live` | Liveness — process alive (200 OK always) | Kubernetes / load balancer |
| `GET /api/v1/health/ready` | Readiness — DB + JWT verification (503 if any fails) | Kubernetes / load balancer |
| `GET /api/health` | Next.js frontend health (build SHA + region) | Vercel, smoke tests |

### Response Envelope (CR 12-5 D-14 verbatim)

```json
{
  "status": "healthy",
  "timestamp": "2026-08-22T12:34:56.789Z",
  "version": "0.1.0",
  "database": "connected",
  "redis": "disconnected",
  "uptime_seconds": 42
}
```

The `database` field reflects a real `SELECT 1` against Supabase PostgreSQL. The `redis` field reflects an opt-in Redis ping (defaults to `disconnected` when no Redis is configured).

### Sentry Observability

- **Browser** (`apps/web/lib/observability/sentry.ts`): session replay + error tracking, `tracesSampleRate=0.1`.
- **Server** (`apps/api/core/observability.py`): FastAPI middleware + SQLAlchemy query tracing, `traces_sample_rate=0.1`.
- DSNs are stored in Vercel/Railway env vars (NOT in source code).

## 7. Database Backup + Restore

See [`docs/database-backup.md`](./database-backup.md) for full details.

**Summary**:
- **Automatic**: Supabase PITR (7-day retention on Pro plan) — point-in-time recovery to any second within the last 7 days.
- **Manual**: `POST /api/v1/admin/backup` admin-only endpoint (Phase 4 T6 wire) creates a `phase_4_backup_strategy` row with SHA-256 checksum + storage URL.
- **RPO**: 5 minutes (Supabase PITR window)
- **RTO**: 1 hour (manual restore from PITR)

## 8. Rollback Strategy

### Vercel (Frontend)

1. Go to Vercel dashboard → Deployments.
2. Find the last known good deployment.
3. Click "Promote to Production" — atomic rollback, no rebuild.

### Railway (Backend)

1. Go to Railway dashboard → Deployments.
2. Find the last known good deployment.
3. Click "Rollback" — atomic container restart, no rebuild.

### Database

1. Use Supabase PITR (Settings → Database → Point in Time Recovery).
2. Select a timestamp before the incident.
3. Confirm the restore (creates a new branch; manual merge required).

### Frontend ↔ Backend Compatibility

Vercel + Railway should be rolled back INDEPENDENTLY. The `version` field in the health check envelope helps confirm which backend is serving which frontend request.

## 9. Smoke Test

After every deployment, run a smoke test:

```bash
# 1. Backend health
curl -fsSL https://api.costmgr.com/api/v1/health
# Expected: 200 OK + JSON envelope with status=healthy

# 2. Frontend health
curl -fsSL https://app.costmgr.com/api/health
# Expected: 200 OK + JSON with build SHA + region

# 3. Cross-tenant isolation check (Task #5 from Phase 3 close-out retro)
# Issue a JWT for tenant A, GET /api/v1/tenants/{tenantB_id}
# Expected: 403 FORBIDDEN_TENANT (CR 0-2 RLS lesson)

# 4. Critical user flow: signup → industry select → login
# Verify the 2-mint sequence (Phase 3-0 wire) works end-to-end

# 5. Email delivery verification (cj-304 wire EXTENSION — cj-299 Postmark 결정 wire)
# Create a test tenant via pilot CLI, then trigger a CSV export email:
curl -fsSL -X POST https://api.costmgr.com/api/v1/exports/email \
  -H "Authorization: Bearer $TEST_JWT" \
  -H "Content-Type: application/json" \
  -d '{"report_type": "cost-records", "period_key": "2026-09", "recipients": ["verify@costmgr.com"]}'
# Expected: 200 OK + { "message_id": "<postmark-message-id>", "status": "queued" }
# Verify in Postmark dashboard (https://postmarkapp.com) that the email was sent.

# 6. Scheduled reports timezone verification (cj-304 wire EXTENSION — cj-300 APScheduler 결정 wire)
# Verify TZ env var is set to Asia/Seoul:
curl -fsSL https://api.costmgr.com/api/v1/health | jq '.timezone'
# Expected: "Asia/Seoul"
# Verify cron expressions are loaded:
uv run python -c "from apps.api.jobs.scheduled_reports import SCHEDULED_REPORTS_CRON_EXPRESSIONS; print(SCHEDULED_REPORTS_CRON_EXPRESSIONS)"
# Expected: { "weekly": "0 9 * * 1", "monthly": "0 9 1 * *", ... }

# 7. Pilot tenant provisioning verification (cj-304 wire EXTENSION)
# Run the pilot CLI in dry-run mode for a new test tenant:
uv run python apps/api/scripts/cli/pilot_tenant_provision.py \
  --tenant-id="00000000-0000-0000-0000-000000000001" \
  --industry="saas_manufacturing" \
  --admin-email="smoke-test@costmgr.com" \
  --admin-display-name="Smoke Test" \
  --finance-contact-email="finance-smoke@costmgr.com" \
  --dry-run
# Expected: prints planned SQL + capability grants + audit log action, no DB mutation
```

CR 12-5 D-PARITY-01 inversion: the smoke test must use the same `NEXT_PUBLIC_API_BASE_URL` that the frontend uses, NOT a different staging URL. This catches parity bugs early.

## 10. Troubleshooting

### Common Issues

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| Railway healthcheck 503 | DB connection pool exhausted | Increase `POOL_SIZE` env var; restart container |
| Vercel 500 on `/api/*` | Backend URL misconfigured | Check `NEXT_PUBLIC_API_BASE_URL` env var |
| Sentry not capturing errors | DSN mismatch | Verify `SENTRY_DSN` (backend) + `NEXT_PUBLIC_SENTRY_DSN` (frontend) |
| Migration fails | Alembic head out of sync | Run `alembic upgrade head` against staging DB first |
| CORS errors | CSP `connect-src` too restrictive | Add origin to CSP `connect-src` in `vercel.json` headers |

### Diagnostic Commands

```bash
# Backend logs (Railway)
railway logs --service costmgr-api --tail 100

# Frontend logs (Vercel)
vercel logs <deployment-url> --prod

# Database connection test
psql $DATABASE_URL -c "SELECT 1"

# Sentry event test (server)
python -c "import sentry_sdk; sentry_sdk.capture_message('test')"
```

## 11. Security

- **Secrets**: All secrets stored in Vercel/Railway env vars, NEVER in source code.
- **HTTPS**: Enforced via Vercel (automatic Let's Encrypt) + Railway (automatic).
- **CSP**: `Content-Security-Policy` set in `vercel.json` headers (Phase 4 T1 wire).
- **HSTS**: `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload` (Phase 4 T1 wire).
- **X-Frame-Options**: `DENY` to prevent clickjacking (Phase 4 T1 wire).
- **Permissions-Policy**: Camera, microphone, geolocation disabled by default.
- **JWT verification**: Backend verifies Supabase JWT using `SUPABASE_JWT_SECRET` (Phase 3-0 wire).
- **2FA**: Required for all `owner` accounts (Phase 12 wire, `TWO_FACTOR_AUTH` capability).

## 12. Cost Estimation

### Monthly Cost Breakdown (1K MAU baseline)

| Service | Tier | Cost |
|---------|------|------|
| Vercel Pro | Pro | $20/seat/month |
| Railway Hobby | Hobby + usage | $5–25/month |
| Supabase Pro | Pro | $25/month |
| Sentry Team | Team | $26/month |
| **Total** | | **~$76–96/month** |

### Scaling Considerations

- **10K MAU**: ~$200–400/month (Railway scales workers, Supabase adds storage)
- **100K MAU**: ~$2K–4K/month (Railway Pro, Supabase Team, Vercel Enterprise)

### Cost Optimization Tips

- Vercel: Use ISR + edge caching for read-heavy pages (report dashboards).
- Railway: Reduce `--workers` from 2 to 1 if traffic <100 req/min.
- Supabase: PITR retention is the most expensive feature — drop to 3-day retention if budget-constrained.
- Sentry: Adjust `tracesSampleRate` from 0.1 to 0.01 for high-volume endpoints.

---

## Cross-References

- [Master PRD §F16](../_bmad-output/planning-artifacts/prd.md#F16) — Deployment territory
- [Master PRD AD-27](../_bmad-output/planning-artifacts/prd.md#AD-27) — Deployment 신규 결정
- [Database backup runbook](./database-backup.md) — RPO/RTO + backup strategy
- [Auth foundation runbook](./auth-foundation.md) — Phase 3-1 wire (auth + 2FA + session)
- [Capability matrix v1.25](./capability-matrix.md#v1.25) — DEPLOYMENT_PROD/STAGING/DATABASE_BACKUP/HEALTH_CHECK capability gates

## Known Limitations

- Disaster recovery multi-region backup is deferred to Phase 5+ (single-region only).
- Sentry session replay is opt-in (defaults to 0% capture rate; can be bumped via env var).
- CDN cache invalidation is manual (no automatic purge on deployment).