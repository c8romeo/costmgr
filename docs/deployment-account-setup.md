# Costmgr Production Account Setup & Day-1 Deploy Runbook

> **cj-305 production deploy day-1 wire (cj-style 254번째, 2026-09-08 KST)** — Pilot W1 launch prep. 4-service minimal viable scope, 6-day D-day countdown. **Why:** cj-304 prod deploy prep wire 결정 wire 4 critical gaps 의 env var/CLI scaffolding 활용, D-6 (2026-09-14 KST) launch 까지 smoke-testable production stack 구성. **How to apply:** Signup 4 services in parallel → capture tokens → wire Railway env vars → alembic migrate Supabase → deploy → smoke test → onboard 1 pilot tenant.

## 1. Goal & Timeline

| Milestone | Date | Target |
|---|---|---|
| **D-6 Today** | 2026-09-08 (KST) | 4-service signup + token capture (이 문서) |
| D-5 | 2026-09-09 (KST) | Railway env vars + alembic migrate Supabase + API deploy |
| D-4 | 2026-09-10 (KST) | Vercel web deploy + end-to-end smoke test |
| D-3 | 2026-09-11 (KST) | Pilot tenant onboarding (CLI dry-run → real) |
| D-2 | 2026-09-12 (KST) | Pilot candidate outreach (B-1) 발송 |
| D-1 | 2026-09-13 (KST) | Pilot user self-test |
| **D-0 Pilot W1 launch** | **2026-09-14 (KST)** | **5-10 SaaS 제조 스타트업 8-week 무료 pilot 시작** |

## 2. 4-Service Minimal Viable Scope (cj-305 결정 wire)

**선정 rationale** (cj-304 wire 의 6-service scope 에서 2개 defer):

| # | Service | Tier | W1 필수? | Rationale |
|---|---|---|---|---|
| 1 | **Postmark** | Sandbox (free, 100 emails/mo) | ✅ HARD | cj-299 OQ 결정 wire 신규 active (transactional email HTTP API) |
| 2 | **Supabase** | Pro (~$25/mo) | ✅ HARD | Postgres for API runtime + alembic migrations |
| 3 | **Railway** | Hobby (~$5/mo) | ✅ HARD | API backend deploy target, cj-303 uvicorn boot verified |
| 4 | **Vercel** | Pro (~$20/mo) | ✅ HARD | Web frontend deploy target |
| 5 | ~~Sentry~~ | ~~Team (~$26/mo)~~ | ⏸️ **DEFER post-W1** | optional observability, W1+1 부 추가 가능 |
| 6 | ~~Cloudflare DNS~~ | ~~~$1/mo~~ | ⏸️ **DEFER post-W1** | `*.vercel.app` + `*.up.railway.app` default subdomain 으로 W1 기능 완결, custom domain 은 pilot 검증 후 부여 |

**월 burn 합계**: **~$50/mo** (vs 6-service full $77/mo, 35% 절감).
**Pilot 8-week 예상 burn**: ~$100 (B-2 budget guardrail 준수).

**Defer 사유**: 5-10 SaaS 제조 스타트업 대상 = technical credibility > brand credibility. `*.vercel.app` 으로 충분히 신뢰감 확보. Sentry 는 launch 안정화 후 추가.

## 3. Signup Order (의존성 순)

```
[Postmark]            ← ① instant (free), 1차 blocker
[Supabase]            ← ② DB, 이후 모든 deploy 의 의존
[Railway] → wire env  ← ③ env vars fill (Supabase URL, Postmark token)
[Vercel]              ← ④ web deploy (Railway URL 필요)
[Pilot tenant CLI]    ← ⑤ dry-run first, then real (Supabase URL 의존)
```

**병렬 가능**: Postmark + Cloudflare DNS (defer) + Supabase 는 독립. Railway 는 Supabase 끝나야 시작. Vercel 은 Railway 끝나야 시작.

## 4. Per-Service Signup Steps

### 4.1 Postmark (cj-299 OQ 결정 wire 보존)

**Signup URL**: https://postmarkapp.com/sign-up (또는 https://postmarkapp.com → Start free trial)

**Tier**: Sandbox (free, 100 emails/month) — Pilot W1 에 충분.

**Steps**:
1. Email + password signup (browser, 5분)
2. Email verification link 클릭
3. Dashboard 진입 → Servers → "Create Server" → server name: `costmgr-pilot`
4. Servers → costmgr-pilot → "API Tokens" tab → copy **Server Token**
5. (Optional, post-W1) "Sender Signatures" → add `noreply@a-costmgr.com` → DNS verification

**Capture (1Password 또는 secure store, git 부 커밋)**:
```
POSTMARK_SERVER_TOKEN=<token-from-step-4>
POSTMARK_FROM_EMAIL=noreply@postmarkapp.com  # sandbox default (custom domain post-W1)
```

**Target env var location**: `apps/api/.env.production` + Railway service Variables tab.

**cj-304 wire EXTENSION 보존**: cj-304 wire 의 env.example + docs/deployment.md §5 의 POSTMARK_SERVER_TOKEN + POSTMARK_FROM_EMAIL row 매핑 그대로.

### 4.2 Cloudflare DNS + 도메인 (DEFER to post-W1)

**Status**: ⏸️ **DEFER post-W1** — `*.vercel.app` + `*.up.railway.app` default subdomain 으로 W1 launch.

**Post-W1 task** (cj-305 wire scope 외):
- Cloudflare Registrar (~$1/mo + ICANN fee ~$10/year)
- 도메인 `a-costmgr.com` 등록
- Postmark sender signature DNS 검증: SPF + DKIM + Return-Path CNAME

### 4.3 Supabase Pro

**Signup URL**: https://supabase.com/dashboard/sign-up (또는 supabase.com → Start)

**Tier**: Pro (~$25/mo, 8GB Postgres + 250GB bandwidth)

**Steps**:
1. GitHub OAuth signup (browser, 3분)
2. "New Project" 클릭 → Organization 선택 (or create new)
3. Project name: `costmgr-prod` / Database password: 32자 strong (1Password generate)
4. Region: **ap-northeast-2 (Seoul)** — pilot 사용자 위치 최적
5. Plan: Pro (~$25/mo, 14-day trial then paid)
6. Project 생성 완료 (~2분)

**Capture (secure store)**:
```
SUPABASE_PROJECT_URL=https://<project-ref>.supabase.co
SUPABASE_ANON_KEY=<anon-key>           # web frontend용, security-checked
SUPABASE_SERVICE_ROLE_KEY=<service-key> # backend 전용, 절대 web 부 노출 금지
DATABASE_URL=postgresql+asyncpg://postgres.<project-ref>:<password>@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres  # POOLED (port 6543, runtime 용)
DATABASE_URL_DIRECT=postgresql+asyncpg://postgres.<project-ref>:<password>@aws-0-ap-northeast-2.pooler.supabase.com:5432/postgres  # DIRECT (port 5432, alembic migration 용)
```

**Setting > Database > Connection string** 에서 두 URL 모두 copy.

**Target env var location**:
- `DATABASE_URL` (pooled, port 6543) → Railway service Variables
- `DATABASE_URL_DIRECT` (direct, port 5432) → alembic migrations 로컬 실행 시

**Supabase PITR 활성화**: Settings > Database > Point-in-time Recovery → Enable (production 안전망).

### 4.4 Railway Hobby

**Signup URL**: https://railway.app/new (또는 railway.app → Start free trial)

**Tier**: Hobby ($5/mo flat, $5 credit trial → 그 후 $5/mo credit card 부터 청구)

**Steps**:
1. GitHub OAuth signup (browser, 3분)
2. "New Project" → "Deploy from GitHub Repo" → `c8romeo/costmgr` 선택
3. Service 생성 → Settings:
   - **Root Directory**: `apps/api`
   - **Watch Paths**: `apps/api/**` (기본값 그대로)
4. Variables 탭 → 다음 env vars 추가:

| Env Var | Value | Source |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres.<ref>:<password>@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres` | Supabase pooled URL |
| `POSTMARK_SERVER_TOKEN` | `<token from 4.1>` | Postmark |
| `POSTMARK_FROM_EMAIL` | `noreply@postmarkapp.com` | Postmark sandbox default |
| `TZ` | `Asia/Seoul` | cj-304 wire EXTENSION (APScheduler cron Railway 기본 UTC → 24h 오프셋 방지) |
| `RETRY_BACKOFF_MINUTES` | `1,5,30` | cj-304 wire EXTENSION (cj-300 APScheduler retry policy) |
| `APP_ENV` | `production` | runtime flag |
| `SECRET_KEY` | `<64-char-random>` | 1Password generate |
| `JWT_SECRET` | `<64-char-random>` | 1Password generate |
| `CORS_ORIGINS` | `https://costmgr-pilot.vercel.app` | Vercel URL (4.5 완료 후 update) |

5. Deploy trigger → Build logs 확인
6. **Generate Domain** → `<service-name>.up.railway.app` 자동 생성 → copy
7. Smoke test: `curl https://<service-name>.up.railway.app/health` → 200 OK

**Target file location**: `apps/api/railway.toml` (cj-304 wire EXTENSION 보존) + Railway dashboard Variables.

### 4.5 Vercel Pro

**Signup URL**: https://vercel.com/signup (또는 vercel.com → Start)

**Tier**: Pro (~$20/mo per member)

**Steps**:
1. GitHub OAuth signup (browser, 3분)
2. "Add New Project" → "Import" `c8romeo/costmgr`
3. Framework Preset: Next.js (auto-detect)
4. **Root Directory**: `apps/web` (Edit → 설정)
5. Build/Output settings:
   - Build Command: `pnpm build` (또는 자동 감지)
   - Output Directory: `.next` (Next.js default)
   - Install Command: `pnpm install --frozen-lockfile`
6. Environment Variables:
   | Env Var | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | `https://<service-name>.up.railway.app` |
   | `NEXT_PUBLIC_APP_URL` | `https://costmgr-pilot.vercel.app` (Vercel 자동 부여 후 update) |
7. Deploy → Build logs 확인
8. 자동 부여 도메인: `costmgr-pilot.vercel.app` → copy

**CORS update 후속**: Railway `CORS_ORIGINS` env var 에 Vercel URL 추가 → Railway auto-redeploy.

## 5. 일자별 실행 계획

### Day 1 (2026-09-08, today, D-6) — Signup phase (2-3h)

- [ ] **Postmark** signup → POSTMARK_SERVER_TOKEN capture
- [ ] **Supabase** signup → DATABASE_URL (pooled + direct) capture
- [ ] **Cloudflare DNS** ⏸️ DEFER
- [ ] 위 token 들 1Password secure note 에 저장

### Day 2 (2026-09-09, D-5) — Deploy phase (2-3h)

- [ ] **Railway** signup + repo connect + env vars fill + deploy
- [ ] `curl https://<service>.up.railway.app/health` → 200 확인
- [ ] 로컬 alembic migrate: `uv run alembic -c apps/api/alembic.ini upgrade head` (DATABASE_URL_DIRECT 사용)
- [ ] smoke test: `/auth/login`, `/admin/tenants` (anon 거부 확인)

### Day 3 (2026-09-10, D-4) — Frontend deploy + E2E (1-2h)

- [ ] **Vercel** signup + deploy
- [ ] CORS env var update (Railway)
- [ ] Browser smoke test: `https://costmgr-pilot.vercel.app` 로그인 → dashboard
- [ ] Postmark test email: `uv run python apps/api/scripts/test_postmark_send.py` (or manual API call)

### Day 4 (2026-09-11, D-3) — Pilot tenant onboarding (1h)

- [ ] Pilot tenant CLI dry-run: `uv run python apps/api/scripts/cli/pilot_tenant_provision.py --dry-run --tenant-id=tenant_001 --tenant-name="Pilot Co 1" --admin-email=admin@pilot1.com`
- [ ] Real onboarding: same command without `--dry-run`
- [ ] audit_log INSERT 확인 (Supabase dashboard → audit_logs table)

### Day 5 (2026-09-12, D-2) — Outreach (1h)

- [ ] Pilot candidate list 작성 (B-1, 운영자 결정)
- [ ] 초대 이메일 발송 (Postmark transactional template, cj-299 결정 wire 사용)
- [ ] onboarding guide URL 전달

### Day 6 (2026-09-13, D-1) — Final verify (30min)

- [ ] Pilot user self-test (운영자 직접 login → dashboard load → action 1개 실행)
- [ ] Slack/Discord support channel open (Pilot W1 communication)

### Day 7 (2026-09-14, D-0) — Pilot W1 KICKOFF 🚀

- [ ] 5-10 SaaS 제조 스타트업 8-week 무료 pilot 시작
- [ ] Daily check-in (post-pilot cadence, cj-301 결정 wire 보존)

## 6. 결정 wire 적용 확인 (cj-305 wire EXTENSION 보존)

- **cj-304 wire 4 critical gaps 결정 wire 보존**:
  - ① POSTMARK_SERVER_TOKEN + POSTMARK_FROM_EMAIL (cj-299 Postmark 결정 wire 신규 active) → Railway env fill
  - ② TZ=Asia/Seoul + RETRY_BACKOFF_MINUTES (cj-300 APScheduler 결정 wire 신규 active) → Railway env fill
  - ③ Pilot tenant onboarding CLI dry-run-first (capability matrix v1.54 EXTENSION preserved) → Day 4 dry-run → real
  - ④ Production seed plan (docs/deployment.md §4 Step 6 EXTENSION 보존) → alembic head 으로 일원화

- **CR 11-3 honest-DEFER 254번째** cj-305 wire 진입 결정 wire (cj-304 close-out retro 의 253번째 → cj-305 wire 의 254번째)
- **OQ 결정 wire 4/4 apply 보존** (reportlab + Postmark + APScheduler + matplotlib, cj-304 wire 의 보존 그대로)
- **capability matrix v1.54 EXTENSION preserved** (Pilot CLI 의 capability_grants UPSERT 가 EXPORT_CSV/PDF/EMAIL/SCHEDULED 그대로)
- **audit actions EXTENSION preserved** + 1 신규 (`pilot_tenant_provisioned`, cj-304 wire 결정 wire)

## 7. Verifications (smoke-testable success criteria)

- [ ] **Smoke Test 1**: `curl https://<service>.up.railway.app/health` → 200 + `{"status":"healthy"}`
- [ ] **Smoke Test 2**: alembic migrate 성공 (Supabase `SELECT version FROM alembic_version` → latest revision)
- [ ] **Smoke Test 3**: Vercel `https://costmgr-pilot.vercel.app` → 200 + login page render
- [ ] **Smoke Test 4**: Postmark test email 발송 → 수신 확인 (sandbox sender OK)
- [ ] **Smoke Test 5**: Pilot tenant CLI dry-run → 4 planned actions JSON output
- [ ] **Smoke Test 6**: Pilot tenant real onboarding → audit_logs INSERT 확인
- [ ] **Smoke Test 7**: End-to-end browser test: Vercel login → Railway API call → Supabase query → response

## 8. Carryover honestly DEFER (cj-305 scope 외)

- ~~Sentry Team~~: launch 안정화 후 W1+1 ~ W1+2 추가
- ~~Cloudflare DNS + custom domain~~: pilot 검증 후 부여 (D+7 ~ D+14)
- **cj-303 carryover 4건**: web-e2e Playwright + test-suite-measure 잔여 + web-test + lint-conventions → post-pilot fix sprint
- **cj-300 stale docstring cleanup** (slack-sdk + sendgrid references) → post-pilot cleanup sprint

## 9. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| DNS propagation delay (post-W1 only) | low | W1 uses default subdomains |
| Supabase IP allowlist | low | Use pooled URL (port 6543) bypasses direct connection restrictions |
| Railway free trial → paid transition surprise | medium | Set billing alert in Railway dashboard, $5/mo Hobby budget |
| Postmark sandbox sender 100/mo limit | low | Pilot 5-10 users × ~5 emails = ~50/mo, fits comfortably |
| Pilot candidate outreach 늦음 | **HIGH** | cj-305 task #10 별도 트랙, D-2 (2026-09-12) 까지 발송 필수 |

## 10. Cross-references

- **cj-304 prod deploy prep wire** (`1fdb67d`): 4 critical gaps fix + Pilot tenant CLI (~280 LOC) + env.example + railway.toml + Dockerfile ENV TZ + docs/deployment.md EXTENSION
- **cj-304 prod deploy prep retro** (`e7fb753`): 결정 wire 적용 확인, 33/33 cumulative 보존
- **cj-303 uvicorn boot fix wire** (`ad7b91b`): AD-14 stack pin EXTENSION (apscheduler==3.10.4 + pytz==2024.1) + cj-300 wire 의 pytz unpinned 정직 회복
- **cj-299 email delivery wire**: Postmark HTTP API 결정 wire, `apps/api/integrations/postmark.py` + ActionClass.REPORTS `export_email`
- **cj-300 scheduled reports wire**: APScheduler 4 cron + pytz KST + RETRY_BACKOFF_MINUTES=[1,5,30], `apps/api/jobs/scheduled_reports.py`
- **cj-301 pilot outreach prep**: 5-10 SaaS 제조 스타트업 8-week 무료 pilot 결정 wire, 2026-09-14~11-09 KST

## 11. 결정 wire 일자

2026-09-08 (KST) — 본 cj-305 production deploy day-1 wire sprint 의 실제 commit 일자.

---

**다음 옵션** (운전자 결정 보류):
- (a) **Postmark + Supabase signup 즉시 시작** (D-6 오늘, 병렬)
- (b) cj-305 wire sprint commit 먼저 (본 runbook commit 후 signup 진행)
- (c) Pilot candidate list (B-1) 먼저 작성 (cj-305 task #10)
- (d) 다른 옵션

추천: **(b) cj-305 wire sprint commit 먼저** → 본 runbook 이 audit trail 로 commit 된 후 signup 진행 (Postmark sandbox instant 이므로 commit 후 30분 내 signup 가능).
