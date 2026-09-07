# Phase 30 — Production deployment prep entry (cj-style 309번째)

**일자**: 2026-09-07 (KST)
**territory**: Epic 30+ Pilot Gate (cj-297 PRD OQ-3 OPEN) → production deployment prep for pilot W1 launch 2026-09-14 KST (7일 카운트다운)
**sprint type**: docs-only decision wire (cj-style atomic entry)

---

## §1 의도 분석

cj-303 close-out retro 종료 후 운전자 결정 사항 **option (a) production deployment + pilot outreach 즉시 시작** 승인. production deployment 의 첫 단계 = **deployment artifacts currency verification + gap analysis**. docs/deployment.md (Phase 4 / cj-style 55번째 wire, 2026-08-22 era) 가 cj-299 (Postmark) + cj-300 (APScheduler) + cj-303 (uvicorn boot fix + AD-14 stack pin EXTENSION) 의 변경을 반영하지 못함 → **production deployment 가 critical env var 없이 진행될 위험** 정직 회복.

### 본 sprint 의 의도
1. **currency check** — Phase 4 의 deployment.md / .env.example / railway.toml / vercel.json / Dockerfile 5개 파일이 cj-299/300/303 EXTENSION 반영 여부 verify
2. **gap analysis** — production deployment 차단 위험 gap 식별
3. **fix scope** — gap 별 fix 결정 wire 진입
4. **risk profile** — fix 의 LOW/MEDIUM/HIGH risk 평가
5. **verification plan** — 4-step 로컬 verify + CI verify
6. **결정 보류 정리** — operator 결정 사항 (계정/DNS/도메인/prod secrets) 결정 wire 보존

## §2 Currency check (Phase 4 vs cj-299/300/303 EXTENSION)

### 2.1 docs/deployment.md (Phase 4 / cj-style 55번째, 2026-08-22)

**확인 결과** (2026-09-07):

| Section | Phase 4 | cj-299/300/303 EXTENSION 반영 |
|---|---|---|
| §1 Purpose | Vercel + Railway + Supabase + Sentry 4-tier architecture | 보존 |
| §2 Architecture | 동일 | 보존 |
| §3 Prerequisites | Vercel + Railway + Supabase + Sentry 4 accounts | 보존 |
| §4 Step-by-Step | Supabase → Railway → Vercel → DNS 4-step | 보존 |
| §5 Env Vars SSOT | DATABASE_URL + SUPABASE_* + SENTRY_DSN + ENVIRONMENT | **❌ POSTMARK_SERVER_TOKEN 부재 (cj-299 부 반영)** + **❌ APScheduler env vars 부재 (cj-300 부 반영)** + **❌ TZ=Asia/Seoul 부재 (cj-300 부 반영)** |
| §6 Health Check | /api/v1/health + /api/v1/health/live + /api/v1/health/ready | 보존 |
| §7 Backup/Restore | Supabase PITR 7-day | 보존 |
| §8 Rollback | Vercel + Railway + Supabase 3-tier | 보존 |
| §9 Smoke Test | 4 critical user flow | **❌ pilot-specific tenant onboarding flow 부재** |
| §10 Troubleshooting | 5 common issues | 보존 |
| §11 Security | CSP + HSTS + JWT + 2FA | 보존 |
| §12 Cost | ~$76-96/month | 보존 |

**Currency verdict**: **5개 section 갱신 필요** (§5 Env Vars + §9 Smoke Test + NEW §5.b Pilot tenant provisioning + NEW §5.c Scheduling + §3 Prerequisites prod secrets manager 강화).

### 2.2 apps/api/.env.example

**확인 결과**:
```bash
$ cat apps/api/.env.example
SERVICE_NAME=costmgr-api
SERVICE_VERSION=0.1.0
ENVIRONMENT=development
REGION=ap-northeast-2
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_JWT_SECRET=
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:54322/postgres
LOG_LEVEL=INFO
```

**Currency verdict**: **EXTENSION 필요** (POSTMARK_SERVER_TOKEN + APScheduler env vars + TZ).

### 2.3 railway.toml

**확인 결과**:
```toml
[env]
DATABASE_URL = "${DATABASE_URL}"
SUPABASE_URL = "${SUPABASE_URL}"
SUPABASE_ANON_KEY = "${SUPABASE_ANON_KEY}"
SUPABASE_SERVICE_ROLE_KEY = "${SUPABASE_SERVICE_ROLE_KEY}"
SUPABASE_JWT_SECRET = "${SUPABASE_JWT_SECRET}"
SENTRY_DSN = "${SENTRY_DSN}"
ENVIRONMENT = "production"
PYTHONUNBUFFERED = "1"
PYTHONDONTWRITEBYTECODE = "1"
PORT = "8000"
```

**Currency verdict**: **EXTENSION 필요** (POSTMARK_SERVER_TOKEN + TZ=Asia/Seoul + RETRY_BACKOFF_MINUTES).

### 2.4 apps/web/.env.example

**확인 결과**:
```bash
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_SUPPORT_EMAIL=support@bizup.kr
NEXT_PUBLIC_SENTRY_DSN=
NEXT_PUBLIC_SENTRY_ENVIRONMENT=development
SENTRY_AUTH_TOKEN=
```

**Currency verdict**: **보존** (cj-299/300/303 의 frontend-side env vars 없음 — Postmark server-side only, APScheduler server-side only, pytz server-side only).

### 2.5 vercel.json + apps/api/Dockerfile

**확인 결과**: 보존 (build/runtime config 변경 없음, cj-299/300/303 의 EXTENSION 은 모두 runtime code + env vars 영역).

### 2.6 uv lockfile (cj-303 EXTENSION)

**확인 결과**: `apscheduler==3.10.4` + `pytz==2024.1` EXTENSION 완료 (cj-303 wire `537d17d` 후 uv.lock regen 107 packages resolved). Production `uv sync --frozen --no-dev --no-install-project` 가 정상 작동 예상.

## §3 Gap analysis (production deployment critical blockers)

### Gap 1 — POSTMARK_SERVER_TOKEN missing (cj-299 결정 wire 부 반영) ⚠️ CRITICAL

**증상**: `apps/api/main.py:625` 의 email provider factory 가 `POSTMARK_SERVER_TOKEN → SMTP_HOST → LoggingProvider (dev default)` 우선순위로 email provider 선택. Production env 에 POSTMARK_SERVER_TOKEN 미설정 시:
- POSTMARK 부재 → SMTP_HOST 부재 (Railway 에서 SMTP 미설정 가정) → **LoggingProvider fallback** → **모든 production email 발송이 stdout 로그로만 출력 (실제 발송 안 됨)**.
- cj-299 wire 의 OQ-EPIC30+-2 결정 wire (Postmark HTTP API) 가 production 에서 무력화.

**영향 범위**: Story 30.3 Email delivery 의 모든 production 동작 (CSV/PDF export email 발송, scheduled report dispatch). pilot customer 의 email 미수신 → pilot W1 자체가 무효.

**Fix**: 3 files EXTENSION:
- `apps/api/.env.example` — POSTMARK_SERVER_TOKEN= (commented)
- `railway.toml` — POSTMARK_SERVER_TOKEN = "${POSTMARK_SERVER_TOKEN}"
- `docs/deployment.md` §5 — Backend env vars EXTENSION + NEW subsection "Email (cj-299 Postmark 결정 wire)"

### Gap 2 — APScheduler cron env vars + TZ missing (cj-300 결정 wire 부 반영) ⚠️ CRITICAL

**증상**: `apps/api/jobs/scheduled_reports.py` 가 `KST` (`Asia/Seoul`) timezone + `SCHEDULED_REPORTS_CRON_EXPRESSIONS` (4 cron) + `RETRY_BACKOFF_MINUTES=[1,5,30]` 으로 동작. Railway 의 기본 timezone 은 `UTC` → **scheduled report 의 cron 표현식이 KST 04:00 의도 시 UTC 19:00 으로 잘못 해석** → pilot customer 의 monthly report 가 의도하지 않은 시각에 발송.

**영향 범위**: Story 30.4 Scheduled reports 의 모든 production 동작. pilot W1 의 첫 weekly report 가 KST 월요일 04:00 의도 시 UTC 19:00 (한국 시각 화요일 04:00) 으로 발송 → 24시간 오프셋.

**Fix**: 3 files EXTENSION:
- `apps/api/.env.example` — `TZ=Asia/Seoul` + `RETRY_BACKOFF_MINUTES=1,5,30` EXTENSION
- `railway.toml` — `TZ = "${TZ}"` + `RETRY_BACKOFF_MINUTES = "${RETRY_BACKOFF_MINUTES}"` EXTENSION
- `apps/api/Dockerfile` — runtime stage 에 `ENV TZ=Asia/Seoul` 추가 (Railway env var fallback)
- `docs/deployment.md` §5 — Backend env vars EXTENSION + NEW subsection "Scheduling (cj-300 APScheduler 결정 wire)" + §4 Step-by-Step EXTENSION (KST timezone setup 강조)

### Gap 3 — Pilot tenant provisioning strategy 부재 ⚠️ MEDIUM

**증상**: `docs/deployment.md` 가 single-tenant 가정. Pilot program 은 5-10 SaaS 제조 스타트업 → **각 tenant 별 isolated DB context + admin user + capability grants** 필요. 현재 `dev_seed.py` 가 단일 tenant dev 용으로만 존재 (cj-302 MINIMAL fix 의 DEV_TENANT_REPORT_ID + DEV_ACCESS_TOKEN env vars 는 web-e2e test 용, production tenant provisioning 아님).

**영향 범위**: Pilot W1 onboarding 시 각 tenant 의:
- Industry vertical (SaaS 제조 4 옵션 중 1)
- Admin user (owner role + 2FA 강제)
- Capability grants (EXPORT_SCHEDULED + EXPORT_EMAIL + EXPORT_PDF + EXPORT_CSV)
- finance_contact_email (scheduled report recipient)

**Fix**:
- NEW `apps/api/scripts/cli/pilot_tenant_provision.py` (interactive CLI: tenant_id + industry + admin_email + finance_contact_email 입력 → admin user 생성 + capability grant + audit log INSERT)
- `docs/deployment.md` §4 EXTENSION — NEW Step 5 "Pilot tenant provisioning (5-10 SaaS 제조 스타트업)" + §5 EXTENSION + §9 Smoke Test EXTENSION

### Gap 4 — Production seed plan 부재 ⚠️ LOW

**증상**: dev 환경의 dev_seed 는 dev tenant 1개로 충분. production 첫 deploy 시:
- Initial owner user (platform admin)
- Default capabilities (EXPORT_SCHEDULED, EXPORT_EMAIL, EXPORT_PDF, EXPORT_CSV capability matrix v1.54 EXTENSION)
- Default scheduled reports cron (cj-300 의 4 cron)

**Fix**: `docs/deployment.md` §4 EXTENSION — NEW Step 6 "Production initial seed (platform admin + capability matrix + default cron)". 옵션: (a) 운영자가 수동 SQL, (b) NEW `apps/api/scripts/cli/prod_seed.py` CLI. (a) 권장 (1회용, audit log 의 admin action 으로 추적).

## §4 Fix scope 결정 wire 진입

### 4.1 Sprint 2 (cj-304 wire) scope

| File | Type | Change | 이유 |
|---|---|---|---|
| `apps/api/.env.example` | MODIFIED | EXTENSION 5 env vars: POSTMARK_SERVER_TOKEN + TZ + RETRY_BACKOFF_MINUTES + SCHEDULED_REPORTS_CRON_EXPRESSIONS + EMAIL_FROM_ADDRESS | cj-299/300 의 env vars + TZ |
| `railway.toml` | MODIFIED | EXTENSION 5 env vars + comment block (cj-303 EXTENSION 결정 wire 보존) | cj-299/300/303 반영 |
| `apps/api/Dockerfile` | MODIFIED | runtime stage ENV TZ=Asia/Seoul EXTENSION (line 65-69 부근) | cj-300 KST 결정 wire |
| `docs/deployment.md` | MODIFIED | §3 + §4 + §5 + §9 EXTENSION (env vars table EXTENSION + Pilot tenant provisioning Step 5 + Production initial seed Step 6 + Smoke test EXTENSION) | cj-299/300/303 반영 |
| `apps/api/scripts/cli/pilot_tenant_provision.py` | NEW | ~150 LOC CLI: interactive tenant onboarding (tenant_id + industry + admin_email + finance_contact_email) | Pilot Gap 3 fix |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | MODIFIED | v4.74 → v4.75 EXTENSION (cj-304 wire entry + last_updated_note_v4_75) | sprint accounting |
| `memory/MEMORY.md` | MODIFIED | cj-304 wire hook 1-line + Active sprint state EXTENSION | memory index |
| `uv.lock` | auto-regen | 변경 없음 (cj-303 EXTENSION 그대로) | — |

**총 6-7 files** 결정 wire 진입 (cj-303 wire 의 5 files 와 유사한 규모).

### 4.2 결정 보류 (cj-304 wire 후 operator 결정)

| 결정 | 결정자 | 의존성 |
|---|---|---|
| Vercel account setup (Pro plan) | operator | pilot W1 launch 전 |
| Railway account setup (Hobby plan) | operator | pilot W1 launch 전 |
| Supabase project creation (ap-northeast-2 Seoul) | operator | pilot W1 launch 전 |
| Sentry project creation (Team tier) | operator | pilot W1 launch 전 |
| Custom domain 등록 (app.costmgr.com + api.costmgr.com) | operator | DNS provider 의존 |
| Production secrets (POSTMARK_SERVER_TOKEN 등) | operator | Postmark account 의존 |
| Pilot candidate list 5-10곳 (B-1) | operator | outreach 전 |
| Email channel 결정 (B-3) | operator | Postmark account 의존 |

cj-304 wire sprint 종료 후 위 8개 결정이 모두 완료되어야 pilot W1 launch 가능.

## §5 Risk profile

**LOW RISK** (cj-303 wire 와 동일):
- 0 NEW source code (apps/api/*.py 무변경, cj-304 wire scope 외)
- 0 MODIFIED runtime API surface
- alembic graph 보존 (0061 head 그대로)
- ci.yml 무변경
- runtime behavior 보존 (env vars 의 default 가 `LoggingProvider` + UTC + RETRY_BACKOFF_MINUTES=[1,5,30] 기본값)
- 단 4-6 files EXTENSION (cj-303 wire 의 5 files 와 유사한 규모)

**MEDIUM RISK** (cj-304 wire 의 Pilot tenant provisioning CLI 추가 시):
- `apps/api/scripts/cli/pilot_tenant_provision.py` NEW — interactive CLI 가 잘못된 input 받아도 idempotent 처리 + dry-run mode + audit log INSERT 보장 필요
- Risk mitigation: dry-run mode default + audit log INSERT mandatory + typo tolerance

## §6 Verification plan (4-step)

### Step 1: 로컬 verify (env var 무결성)
```bash
uv run python -c "
import os
os.environ['TZ'] = 'Asia/Seoul'
os.environ['POSTMARK_SERVER_TOKEN'] = 'test-token-not-real'
os.environ['RETRY_BACKOFF_MINUTES'] = '1,5,30'
os.environ['SCHEDULED_REPORTS_CRON_EXPRESSIONS'] = 'weekly:0 4 * * 1'
from apps.api.core.email_provider import get_email_provider
provider = get_email_provider()
print('OK email provider:', type(provider).__name__)
from apps.api.jobs.scheduled_reports import SCHEDULED_REPORTS_CRON_EXPRESSIONS, RETRY_BACKOFF_MINUTES
print('OK cron expressions:', SCHEDULED_REPORTS_CRON_EXPRESSIONS)
print('OK retry backoff:', RETRY_BACKOFF_MINUTES)
"
```
Expected: email provider = PostmarkProvider (POSTMARK_SERVER_TOKEN 부재 시 LoggingProvider fallback) + cron expressions 정상 로드 + retry backoff 정상 로드.

### Step 2: check_stack_pin.py verify
```bash
uv run python scripts/check_stack_pin.py
# Expected: OK all 39 pins match (cj-303 EXTENSION 보존)
```

### Step 3: stack-pin-check CI job verify
- `stack-pin-check` job 의 Python pin check step 이 exit 0 인지 확인
- 기존 통과 상태 (cj-303 wire baseline) 유지

### Step 4: Pilot tenant provisioning CLI dry-run verify
```bash
uv run python apps/api/scripts/cli/pilot_tenant_provision.py \
  --tenant-id="acme-corp" \
  --industry="saas_manufacturing" \
  --admin-email="cfo@acme.com" \
  --finance-contact-email="finance@acme.com" \
  --dry-run
# Expected: prints planned SQL + capability grants + audit log action, no DB mutation
```

## §7 결정 wire 보존

- **OQ 결정 wire 4/4 apply 보존** (cj-303 retro 의 보존 그대로, cj-304 wire 신규 EXTENSION 0건): reportlab + Postmark + APScheduler + matplotlib
- **AD bind 4/4 active 보존** (cj-304 wire 의 env vars EXTENSION 은 AD bind 직접 변경 없음): AD-2/AD-3/AD-10/AD-12/AD-22
- **NFR bind 7/7 active 보존** (cj-304 wire 의 env vars EXTENSION 은 NFR bind 직접 변경 없음): NFR4/NFR5/NFR7/NFR8/NFR12/NFR18/NFR19
- **capability matrix v1.54 EXTENSION preserved** (cj-304 wire 의 Pilot tenant provisioning CLI 가 capability grants EXTENSION 시 v1.55 EXTENSION 결정 wire 진입 결정 wire 보류 — cj-304 entry 에서는 v1.54 그대로 보존 결정)
- **audit actions EXTENSION preserved** (cj-304 wire 의 Pilot tenant provisioning CLI 가 audit log INSERT 시 ActionClass.REPORTS 의 신규 action 결정 wire 보류 — cj-304 entry 에서는 보존)
- **27/27 cumulative 결정 wire 보존** (cj-303 retro 의 보존 그대로, cj-304 entry 신규 EXTENSION 0건) + **NEW 28번째 cj-304 entry 결정 wire 진입**

## §8 결정 보류 (운전자)

### 8.1 cj-304 entry 종료 후 결정 wire 보존
| # | 옵션 | 결정자 | 의존성 |
|---|---|---|---|
| ① | **cj-304 wire sprint 즉시 진입** (cj-style 310번째, RECOMMENDED next) | 운전자 결정 | 본 entry 승인 |
| ② | Vercel/Railway/Supabase/Sentry account setup 병행 진행 (operator 결정 + execution) | operator | pilot W1 launch 전 |
| ③ | Pilot candidate list 작성 (B-1) 병행 | operator | outreach 전 |
| ④ | cj-303 의 4건 carryover fix (web-e2e Playwright + test-suite-measure + web-test + lint-conventions) | 기술 결정 | optional, post-pilot |

### 8.2 honestly DEFER 결정 wire
- 옵션 (a) cj-304 wire sprint 즉시 진입 (cj-style 310번째, RECOMMENDED)
- 옵션 (b) Pilot candidate list 작성 (B-1) 병행
- 옵션 (c) cj-303 carryover 4건 fix
- 옵션 (d) Epic 30+ PRD v2 EXTENSION (pilot feedback 후)
- 옵션 (e) Epic 29+ spec impl (pilot feedback 후)
- 옵션 (f) Pilot outreach 즉시

## §9 CR 11-3 honest-DEFER (cj-style 309번째)

```
cj-style chain (CR 11-3 honest-DEFER count):
cj-282 (220번째) → ... → cj-303 entry (248번째) → cj-303 wire (249번째) → cj-303 close-out retro (250번째) → **cj-304 prod deploy prep entry (251번째)**
```

종합 **31 sprints 정직 회복 결정 wire 진입**.

## §10 Cross-references

- Plan file: TBD (cj-304 plan 필요 시)
- Phase 4 deployment runbook: `docs/deployment.md` (cj-style 55번째)
- cj-299 Postmark 결정 wire: `memory/handoff-2026-09-06-cj-299-email-delivery-wire-done.md`
- cj-300 APScheduler 결정 wire: `memory/handoff-2026-09-07-cj-300-wire-done.md`
- cj-303 AD-14 stack pin EXTENSION: `memory/handoff-2026-09-07-cj-303-uvicorn-boot-fix-wire-done.md`
- Root cause (env vars): `apps/api/main.py:625` (POSTMARK_SERVER_TOKEN 부재) + `apps/api/jobs/scheduled_reports.py` (KST + RETRY_BACKOFF)
- Alembic head: `0061_phase_30_story_30_4_finance_contact_email.py` (cj-300 wire)
- Stack pin EXTENSION: `docs/STACK_PIN.yaml` (cj-303 EXTENSION 39 pins)

## §11 Why / How to apply

**Why**: cj-303 close-out retro 종료 후 production deployment 진입 직전, docs/deployment.md (Phase 4 / cj-style 55번째, 2026-08-22 era) 가 cj-299/300/303 EXTENSION 반영 안 됨을 확인. **4 critical gaps** 식별 — POSTMARK_SERVER_TOKEN 부재 (cj-299 부 반영), APScheduler cron env vars + TZ 부재 (cj-300 부 반영), Pilot tenant provisioning strategy 부재, Production seed plan 부재. 본 entry sprint 가 gap 정직 회복 + fix scope 결정 wire 진입.

**How to apply**:
- 다음 세션 시작 시: §결정 보류 8.1 (4 options) + §결정 보류 8.2 (6 honestly DEFER) 확인
- 우선순위: **옵션 ① cj-304 wire sprint 즉시 진입** (cj-style 310번째, 6-7 files EXTENSION 결정 wire) → ② Vercel/Railway/Supabase/Sentry account setup + ③ Pilot candidate list 작성 병행 → pilot W1 launch 2026-09-14 KST 7일 카운트다운

## §12 결정 wire 일자

2026-09-07 (KST) — cj-304 prod deploy prep entry sprint 결정 wire 진입 시점.

CR 11-3 honest-DEFER 251번째 (cj-303 close-out retro 의 250번째 → cj-304 prod deploy prep entry 의 251번째)
