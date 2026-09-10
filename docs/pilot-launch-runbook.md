# Pilot Launch Master Runbook (costmgr SaaS manufacturing)

- **일자**: 2026-09-10 (KST) — cj-315 wire 의 D-4 → D-0 timeline refresh
- **D-day**: 2026-09-14 KST (Pilot W1 launch) = **4일 카운트다운**
- **대상 운영자**: kjw
- **Pilot scope**: 5-10 SaaS 제조 스타트업, 8 weeks (2026-09-14 ~ 2026-11-09 KST), 무료
- **소스 결정 wire 보존**: cj-297 (PRD OQ-3 Pilot Gate OPEN) + cj-301 (pilot prep) + cj-304 (4 critical gaps fix + Pilot tenant CLI) + cj-305b (Postmark → Resend swap, OQ-EPIC30+-2 v2) + cj-307 (aal1 minimum fix) + cj-309b (B-1 candidate list) + cj-315 (B-2 outreach exec prep, 본 wire)

---

## §1 Pilot Launch Critical Path (D-4 → D-0 4일 카운트다운, cj-315 wire refresh)

cj-315 wire (`2026-09-10` KST) 기준 **D-4 = 2026-09-10 ~ D-0 = 2026-09-14**. cj-297 + cj-304 + cj-305b 결정 wire 보존. **cj-305b swap** 으로 Postmark → **Resend** 변경 (OQ-EPIC30+-2 v2 결정 wire 보존).

```
D-4 today (2026-09-10 Thu)   — cj-309b B-1 candidate list 의 Tier 1 5곳 + Tier 2 2곳 contact 확보 + cj-315 B-2 outreach exec prep wire DONE
D-3 (2026-09-11 Fri)         — Tier 2 마지막 1곳 contact 확보 + outreach email 1차 작성 8건 + Resend API key 캡처 (deploy-blocking)
D-2 (2026-09-12 Sat AM 10:00) — 1차 outreach 8곳 동시 발송 (ko-KR AM 10:00 KST) + tracking 시작
D-2 PM ~ D-1 (2026-09-12 PM ~ 2026-09-13 Sun) — 1차 회신 확인 + 2차 follow-up 준비 (D+3) + W1 onboarding 일정 조율
D-1 (2026-09-13 Sun)         — 2차 follow-up (D+3) 발송 (회신 없는 곳만) + 회신 온 곳 콜 스케줄링
D-0 (2026-09-14 Mon W1)      — Pilot launch 🚀 + W1 1:1 onboarding 미팅 (회신 온 곳부터, 30분/slot)
```

**Critical path 의 longest pole**:
1. **DNS propagation** (24-48h, Vercel + Railway custom domain) — D-4 ~ D-2 진행 필수
2. **Resend 발신 도메인 인증** (cj-305b swap, 즉시 verify 가능, Postmark 의 1-3 영업일보다 훨씬 빠름)
3. **Supabase region latency** (Northeast Asia Tokyo, 한국 ~50ms) — D-3 ~ D-2 verify
4. **Tier 1 5곳 + Tier 2 3곳 contact 확보** (D-4 ~ D-3, cj-315 의 discovery protocol 결정 wire 보존)

**cj-305b swap 결정 wire 보존**: Postmark 의 Gmail public-domain 차단 + sandbox 100/mo 한계 → **Resend HTTP API + Bearer auth** 로 swap. W1 free tier 3,000/mo (Postmark 대비 30×) + 100/day. `docs/deployment-account-setup.md` §6.2 Resend signup 결정 wire 보존.

---

## §2 Account Setup Checklist

### 2.1 Vercel Pro ($20/월)

```
□ https://vercel.com/signup → GitHub 계정으로 가입
□ Pro plan upgrade (Hobby 무료 tier 는 custom domain 제한)
□ Domain 추가: costmgr.bizup.io (Vercel DNS 또는 external DNS)
□ Vercel DNS records 추가 (대상 도메인 registrar 에서):
  - CNAME @ → cname.vercel-dns.com
  - CNAME www → cname.vercel-dns.com
□ Environment variables 설정:
  - NEXT_PUBLIC_API_BASE_URL=https://api.costmgr.bizup.io
  - NEXT_PUBLIC_TENANT_ID=<pilot_tenant_uuid>
□ Production build 설정:
  - Build command: cd ../.. && pnpm install && pnpm --filter web build
  - Output directory: apps/web/.next
  - Install command: cd ../.. && pnpm install --frozen-lockfile
```

### 2.2 Railway Hobby ($5/월 + usage)

```toml
# railway.toml (cj-304 wire EXTENSION 결정 wire 적용)
[build]
builder = "DOCKERFILE"
dockerfilePath = "apps/api/Dockerfile"

[deploy]
startCommand = "uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

# env vars (cj-304 결정 wire 신규 active)
POSTMARK_SERVER_TOKEN = "${POSTMARK_SERVER_TOKEN}"
POSTMARK_FROM_EMAIL = "${POSTMARK_FROM_EMAIL}"
TZ = "${TZ}"                                          # Asia/Seoul (cj-300)
RETRY_BACKOFF_MINUTES = "${RETRY_BACKOFF_MINUTES}"     # 1,5,30 (cj-300)
DATABASE_URL = "${DATABASE_URL}"                       # Supabase Postgres URL
SECRET_KEY = "${SECRET_KEY}"
ENVIRONMENT = "production"
```

```
□ https://railway.app → GitHub 계정으로 가입
□ New Project → Deploy from GitHub repo → costmgr repo 선택
□ apps/api 디렉토리 지정 (Root Directory 설정)
□ PostgreSQL addon 추가 (또는 Supabase 외부 연결)
□ 환경변수 설정 (위 7개 + DATABASE_URL)
□ Custom domain: api.costmgr.bizup.io
□ Health check endpoint: /health → 200 OK verify
```

### 2.3 Supabase Pro ($25/월)

```
□ https://supabase.com → GitHub 계정으로 가입
□ New project: costmgr-pilot
  - Region: Northeast Asia (Tokyo) - 한국 사용자 latency 최소화
  - Database password: strong random 32+ chars (1Password 저장)
□ Migration apply:
  - Railway 에서 alembic upgrade head 실행
  - 또는 Supabase SQL editor 에서 직접 alembic versions/*.sql 순차 실행
□ Connection pooling: Supavisor transaction mode (port 6543)
□ RLS policies verify:
  - 8 NEW RLS policies cj-290 EXTENSION 모두 적용 확인
  - tenants + users + capability_grants + audit_logs RLS enabled
□ Connection string 복사 → Railway DATABASE_URL env var 설정
```

### 2.4 Sentry Team ($26/월, 26+ users 시) — **cj-305 wire 결정: honestly DEFER post-W1**

cj-305 wire 의 4-service minimal viable 결정 (`b732153`, 2026-09-08) 에 따라 **Sentry 는 post-W1 honestly DEFER**. Pilot launch 비용 $0 EXTENSION 정책 + W1 에는 5-10 tenant only 이므로 custom monitoring 불필요. Railway + Vercel 기본 monitoring 으로 충분.

**post-W1 결정 wire 보존**:
- W4 evaluation 시점에서 tenant 5-10 → 10-20 확장 시 Sentry Team 결정
- 월 $26 burn 결정 = launch day 결정 wire 보류 (cj-305 4-service minimal viable 의 cost deferral)

### 2.5 Resend (cj-305b swap 결정 wire 신규 active)

cj-305b wire (`53b8bbf`, 2026-09-08) **OQ-EPIC30+-2 결정 wire v1 Postmark → v2 Resend swap** 적용. Postmark 의 Gmail public-domain 가입 차단 + sandbox 100/mo 한계 → **Resend HTTP API + Bearer auth** 로 swap. W1 free tier **3,000/mo** (Postmark 100/mo 대비 30×) + 100/day.

```
□ https://resend.com → GitHub 계정으로 가입 (Gmail 가능)
□ API key 발급: API Keys → Create API Key
  - Production: re_xxxxxxxxxxxxxxxx (Bearer auth)
  - Pilot W1: free tier (3,000/mo + 100/day) 으로 충분
□ 발신 도메인 verify: Domains → Add Domain → costmgr.bizup.io
  - SPF record: v=spf1 include:resend.com ~all
  - DKIM record: Resend 에서 제공한 public key TXT record
  - DMARC record (선택): v=DMARC1; p=none; rua=mailto:admin@costmgr.bizup.io
□ DNS records 검증 (Resend dashboard 에서 자동 verify)
  - **Domain verification 시간: 즉시 ~ 수 시간** (Postmark 1-3 영업일보다 훨씬 빠름)
  - Sender: noreply@costmgr.bizup.io
□ Token 을 Railway env var RESEND_API_KEY + Web `.env.local` 에 설정
  - Railway API: production + preview environment 둘 다 설정 필수
  - Web .env.local: NEXT_PUBLIC_RESEND_FROM_EMAIL=noreply@costmgr.bizup.io
```

**cj-305b retroactive correction**: 본 §2.5 는 cj-305b swap 결정 wire 적용. Postmark 관련 모든 reference (POSTMARK_SERVER_TOKEN env var, postmark_send_pilot_invitation.py script) 는 **deprecated**. `apps/api/services/email_provider.py` 의 `PostmarkProvider` → `ResendProvider` swap 결정 wire 보존.

### 2.6 DNS Records (도메인 registrar 에서)

| Type | Host | Value | TTL |
|---|---|---|---|
| CNAME | @ | cname.vercel-dns.com | 300 |
| CNAME | www | cname.vercel-dns.com | 300 |
| CNAME | api | <Railway-provided>.up.railway.app | 300 |
| TXT | @ | v=spf1 include:spf.messagingengine.com ~all | 300 |
| TXT | pm._domainkey | (Postmark DKIM public key) | 300 |
| TXT | _dmarc | v=DMARC1; p=none; rua=mailto:admin@costmgr.bizup.io | 300 |

**DNS propagation 시간**: 24-48h (TTL 300 설정 시 빠르게 전파). `dig +short costmgr.bizup.io CNAME` 명령으로 verify.

---

## §3 Pilot Tenant Provisioning (cj-304 CLI 결정 wire)

### 3.1 CLI dry-run (필수)

```bash
# Railway 환경변수 DATABASE_URL 설정 후 또는 로컬에서 production DATABASE_URL 사용
export DATABASE_URL="postgresql+asyncpg://postgres:<password>@db.costmgr-pilot.supabase.co:6543/postgres"

uv run python apps/api/scripts/cli/pilot_tenant_provision.py \
  --dry-run \
  --tenant-id="00000000-0000-0000-0000-000000000001" \
  --industry="saas_manufacturing" \
  --admin-email="cfo@<candidate-domain>.com" \
  --admin-display-name="<CFO Name>" \
  --finance-contact-email="finance@<candidate-domain>.com"
```

기대 출력 (structured JSON):
```json
{
  "dry_run": true,
  "planned_actions": [
    "UPSERT tenants (id=..., industry=saas_manufacturing)",
    "UPSERT users (email=cfo@..., role=owner, two_factor_required=true)",
    "UPSERT 4 capability_grants (EXPORT_CSV, EXPORT_PDF, EXPORT_EMAIL, EXPORT_SCHEDULED)",
    "INSERT audit_logs (action_class=REPORTS, action=pilot_tenant_provisioned)"
  ]
}
```

### 3.2 CLI real run (dry-run 검증 후에만)

```bash
uv run python apps/api/scripts/cli/pilot_tenant_provision.py \
  --execute \
  --tenant-id="00000000-0000-0000-0000-000000000001" \
  --industry="saas_manufacturing" \
  --admin-email="cfo@<candidate-domain>.com" \
  --admin-display-name="<CFO Name>" \
  --finance-contact-email="finance@<candidate-domain>.com"
```

### 3.3 검증 (real run 후)

```sql
-- Supabase SQL editor
SELECT id, industry, finance_contact_email, created_at FROM tenants WHERE id = '...';
SELECT id, email, role, two_factor_required FROM users WHERE tenant_id = '...';
SELECT capability FROM capability_grants WHERE tenant_id = '...';
SELECT action_class, action, created_at FROM audit_logs WHERE tenant_id = '...' AND action = 'pilot_tenant_provisioned';
```

### 3.4 5-10 SaaS 제조 스타트업 tier list

- **Tier 1 ideal** (50-200명 SaaS 제조): 5곳 목표
  - 예: VC-funded SaaS 제조 + B2B SaaS + ERP/CRM 도메인
  - decision-maker: CFO 또는 VP Finance
- **Tier 2 fallback** (30-50명 SaaS 제조): 3곳 추가
  - bootstrap SaaS 제조 + Seed-funded SaaS
  - decision-maker: CEO 또는 COO (CFO 없을 수 있음)
- **Tier 3 wait-list**: 5-10곳 (post-pilot expansion)

---

## §4 Production Smoke Test

Railway deploy 완료 후 다음 7개 항목 verify:

```bash
# 1. Health check
curl -fsS https://api.costmgr.bizup.io/health
# Expected: {"status":"ok"}

# 2. Auth endpoint
curl -fsS -X POST https://api.costmgr.bizup.io/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"cfo@<domain>.com","password":"<test-password>"}'
# Expected: {"access_token":"...","refresh_token":"..."}

# 3. Tenant context
curl -fsS https://api.costmgr.bizup.io/api/v1/me \
  -H "Authorization: Bearer <access_token>"
# Expected: {"tenant_id":"...","role":"owner","capabilities":[...]}

# 4. CSV export
curl -fsS -X POST https://api.costmgr.bizup.io/api/v1/reports/csv \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"report_type":"monthly_cost","period":"2026-08"}' \
  --output /tmp/cost-report.csv
# Expected: 200 OK + valid CSV file

# 5. Email delivery (Postmark verify)
curl -fsS -X POST https://api.costmgr.bizup.io/api/v1/reports/email \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"report_type":"monthly_cost","period":"2026-08","to_email":"kjw@bizup.io"}'
# Expected: 200 OK + Postmark Message ID (cj-299 결정 wire 신규 active)

# 6. Timezone verification (APScheduler)
# Railway shell 에서:
date  # Current KST time
# Expected: Asia/Seoul (TZ=Asia/Seoul EXTENSION cj-300 신규 active)

# 7. Pilot tenant CLI dry-run (final sanity)
uv run python apps/api/scripts/cli/pilot_tenant_provision.py --dry-run --tenant-id="..." --industry="saas_manufacturing" --admin-email="..." --admin-display-name="..." --finance-contact-email="..."
# Expected: 4 planned actions JSON output
```

---

## §5 Pilot Invitation Email Template (Postmark transactional)

### 5.1 ko-KR subject + body (HTML for Postmark)

```html
Subject: [Pilot] SaaS 제조 회계 AI 비용 분석 8주 무료 체험 제안

<body style="font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">

<div style="text-align: center; margin-bottom: 30px;">
  <h1 style="color: #2563eb; font-size: 24px;">costmgr</h1>
  <p style="color: #64748b; font-size: 14px;">SaaS 제조 회계 AI 비용 분석</p>
</div>

<p>안녕하세요, <strong>{{admin_display_name}}</strong>님.</p>

<p>저는 costmgr 팀의 kjw 입니다. 귀사 {{company_name}}에서 진행하시는 SaaS 제조 사업을 응원하며, 8주 무료 Pilot 프로그램에 정식 초대드립니다.</p>

<h2 style="color: #1e293b; font-size: 18px; margin-top: 30px;">Pilot 프로그램 개요</h2>

<ul style="line-height: 1.8;">
  <li><strong>기간</strong>: 2026-09-14 ~ 2026-11-09 KST (8주)</li>
  <li><strong>대상</strong>: SaaS 제조 스타트업 5-10곳 (Tier 1 우선)</li>
  <li><strong>비용</strong>: 무료 (Pilot 종료 후 정식 과금 결정)</li>
  <li><strong>핵심 기능</strong>:
    <ul>
      <li>CSV/PDF/Email 비용 분석 리포트 자동 생성</li>
      <li>월별/분기별/연간 비용 추세 분석</li>
      <li>예산 대비 실적 분석 (Budget vs Actual)</li>
      <li>Multi-tenant 격리 + 2FA + Audit log</li>
    </ul>
  </li>
</ul>

<h2 style="color: #1e293b; font-size: 18px; margin-top: 30px;">W1 onboarding (2026-09-14 Mon)</h2>

<p>Pilot 시작일에 1:1 화상 미팅 (30분) 으로 초기 설정 도와드리겠습니다:</p>
<ol style="line-height: 1.8;">
  <li>테넌트 계정 활성화 + 2FA 설정</li>
  <li>회계 데이터 업로드 가이드 (CSV/Excel)</li>
  <li>첫 리포트 생성 + 워크플로우 데모</li>
  <li>W1~W8 KPI 측정 framework 설정</li>
</ol>

<h2 style="color: #1e293b; font-size: 18px; margin-top: 30px;">관심 있으시면 회신 부탁드립니다</h2>

<p>회신 시 다음 정보 공유 부탁드립니다:</p>
<ul style="line-height: 1.8;">
  <li>현재 회계 도구 (더존, 경리나라, Xero, QuickBooks 등)</li>
  <li>월 평균 거래 건수 (estimate)</li>
  <li>Pilot 참여 가능 시간대 (W1 onboarding)</li>
</ul>

<p style="margin-top: 30px;">
  감사합니다.<br/>
  <strong>kjw</strong><br/>
  costmgr | Pilot Program Lead<br/>
  kjw@bizup.io
</p>

<hr style="margin-top: 40px; border: none; border-top: 1px solid #e2e8f0;"/>
<p style="font-size: 12px; color: #94a3b8; text-align: center; margin-top: 20px;">
  이 이메일은 costmgr Pilot Program 초대 이메일입니다.<br/>
  <a href="{{unsubscribe_url}}" style="color: #64748b;">수신 거부</a> |
  <a href="https://costmgr.bizup.io" style="color: #64748b;">costmgr</a>
</p>

</body>
```

### 5.2 발송 절차 (Resend HTTP API, cj-305b swap 결정 wire 신규 active)

**cj-305b swap 결정 wire 보존**: Postmark → Resend. `apps/api/services/email_provider.py` 의 `ResendProvider` 사용.

```bash
# 1. dry-run verify (email body + recipients)
#    Resend API 호출 직전 preview via Django shell 또는 FastAPI endpoint
curl -fsS -X POST https://api.costmgr.bizup.io/api/v1/reports/email \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "pilot_invitation",
    "to_email": "cfo@<candidate-domain>.com",
    "params": {
      "admin_display_name": "<CFO Name>",
      "company_name": "<Company Name>"
    }
  }'
# Expected: 200 OK + Resend Message ID (EmailProvider ABC abstraction)

# 2. real send (dry-run 검증 후, Resend API 직접 호출 via Bearer auth)
curl -fsS -X POST https://api.resend.com/emails \
  -H "Authorization: Bearer ${RESEND_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "noreply@costmgr.bizup.io",
    "to": ["cfo@<candidate-domain>.com"],
    "subject": "[Pilot] SaaS 제조 회계 AI 비용 분석 8주 무료 체험 제안",
    "html": "<body>...</body>"
  }'
# Expected: {"id":"<resend_message_id>"}
```

**cj-305b swap rationale 보존**:
- Postmark = "Sorry, we don't allow email addresses on public domains such as Gmail and Yahoo" → **Resend 는 public email 허용**
- Postmark sandbox 100/mo → **Resend free 3,000/mo + 100/day (30×)**
- Postmark sender verification 1-3 영업일 → **Resend 즉시 ~ 수 시간**
- `EmailProvider` ABC abstraction swap 으로 code change 최소

---

## §6 W1 Onboarding Run-of-Show (2026-09-14 Mon)

```
09:00~09:15 KST  — Pilot W1 launch Slack #costmgr-pilot announcement
09:15~09:30 KST  — Pilot candidate 1:1 onboarding meeting #1 (first 5 tenants)
09:30~10:00 KST  — Tenant #1 onboarding (CFO + 2FA setup + first report)
10:00~10:30 KST  — Tenant #2 onboarding
... (각 30분 slots)
17:00 KST       — W1 day-1 close + audit log verify + cross-tenant isolation verify
17:30 KST       — Slack #costmgr-pilot day-1 retrospective + W2 plan
```

### 검증 사항 (W1 day-1 close 시)

```bash
# 1. audit log verify (Resend 발송 audit 포함, cj-305b swap 결정 wire 신규 active)
psql $DATABASE_URL -c "SELECT action_class, action, COUNT(*) FROM audit_logs WHERE created_at >= '2026-09-14 00:00:00+09' GROUP BY action_class, action ORDER BY 1, 2;"

# 2. cross-tenant isolation verify (cj-290 RLS policies)
psql $DATABASE_URL -c "
  SET app.current_tenant_id = 'tenant_1_uuid';
  SELECT COUNT(*) FROM cost_records;  -- tenant_1 건수만
  SET app.current_tenant_id = 'tenant_2_uuid';
  SELECT COUNT(*) FROM cost_records;  -- tenant_2 건수만
"

# 3. Error rate 확인 (cj-305 결정: Sentry post-W1 honestly DEFER, Railway + Vercel 기본 monitoring 사용)
# Railway dashboard → costmgr-api → Logs (error count < 1%)
# Vercel dashboard → costmgr-web → Runtime Logs

# 4. Resend delivery rate 확인 (cj-305b swap 신규 active)
# Resend dashboard → Logs → Delivery rate > 95%
```

---

## §6.5 W4 Evaluation + W8 Close-out Meeting Agendas (cj-315 wire 신규 EXTENSION)

cj-315 wire 의 **post-D-2 honestly DEFER 결정 wire 보존**: W4 evaluation 미팅 + W8 close-out 미팅 agenda 는 회신 + onboarding 후 결정. 본 §6.5 는 framework 만 제공, 실제 agenda 는 W1 onboarding 후 tenant 별 customize.

### W4 Evaluation Meeting (2026-10-12 Mon, 45분)

```
00:00~05:00 — Welcome + 8주 중반 KPI 검토
  - costmgr 사용 frequency (CSV/PDF/Email 리포트 생성 건수)
  - Budget vs Actual 분석 활용도 (월별 variance 추적)
  - Audit log 검토 (어떤 action 이 가장 많이 호출되었나)

05:00~20:00 — Tenant-side 정성 피드백
  - ① 회계 도구 호환성 (더존/경리나라/Xero/QuickBooks integration)
  - ② 데이터 보안 (2FA + RLS + Audit log 신뢰도)
  - ③ 비용 분석 workflow 효율성 (수동 작업 시간 절감)
  - ④ Pilot 의 overall satisfaction (1-5)
  - ⑤ Tier 1/2 candidate 추천 (추가 SaaS 제조 vertical)

20:00~35:00 — KPI 측정 결과 (cj-301 결정 wire 보존)
  - W4 KPI dashboard verify
  - 4주 누적 cost_records / audit_logs / capability_grants 활동
  - 회계 분석 자동화 coverage (manual → automated)

35:00~45:00 — W4~W8 plan + 추가 지원
  - W5~W8 동안 추가 지원 필요 사항
  - Pilot 종료 후 정식 과금 tier 결정 (cj-301 honestly DEFER 보존)
  - Reference call 동의 (W8 후 다른 SaaS 제조 startup 에 reference 제공)
```

### W8 Close-out Meeting (2026-11-09 Mon, 60분)

```
00:00~10:00 — 8주 종합 KPI dashboard review
  - Total cost_records ingested / variance analyses run
  - Total reports generated (CSV/PDF/Email)
  - Audit log completeness (all mutations recorded)
  - 2FA setup success rate (cj-307 aal1 minimum fix 검증)

10:00~30:00 — Tenant-side 정성 피드백 (W4 보다 deeper)
  - ① Pilot 기간 중 biggest win (가장 큰 ROI)
  - ② 가장 불편했던 점 + 개선 제안
  - ③ 정식 전환 의향 (yes/no/maybe + 이유)
  - ④ Reference 제공 의향 (다른 SaaS 제조 startup 에 추천)
  - ⑤ PRD v2 EXTENSION 제안 (cj-301 결정 wire 보존, W8 후 재평가)

30:00~50:00 — Pilot close-out 행정
  - 데이터 export (tenant 의 8주 cost_records 를 CSV/PDF 로 제공)
  - 계정 deactivate 정책 (Pilot 종료 후 30일 retention 후 삭제, GDPR/PIPA 준수)
  - 감사 추적 보존 (audit_logs 는 익명화 후 1년 retention, regulatory requirement)

50:00~60:00 — Next steps + thank you
  - Reference call 일정 조율 (다른 candidate 에 warm intro)
  - 정식 tier 결정 후 연락 (cj-301 honestly DEFER 보존)
  - Thank you gift (Pilot SaaS 제조 cohort swag or costmgr Pro 6개월 무료 등)
```

**honestly DEFER**: W4 + W8 미팅은 post-D-2 결정 wire 보존. 실제 미팅 일정은 회신 + onboarding 후 tenant 별 조율.

---

## §7 Risk Register (8 risks)

| # | Risk | Impact | Mitigation | Status |
|---|---|---|---|---|
| 1 | DNS propagation 지연 (24-48h) | High | D-4 즉시 DNS records 설정 (cj-315 wire refresh) | 결정 wire |
| 2 | ~~Postmark sender verification 지연 (1-3d)~~ → **Resend 즉시 verify** (cj-305b swap) | ~~High~~ → **Low** | Resend API key 캡처 + 발신 도메인 verify | 결정 wire (cj-305b swap 신규 active) |
| 3 | Supabase region latency (Tokyo 선택 시 한국 ~50ms) | Low | Region: Northeast Asia (Tokyo) 선택 | 결정 wire |
| 4 | Pilot tenant 데이터 잘못된 UPSERT | High | cj-304 CLI dry-run-first pattern + audit log INSERT | 결정 wire |
| 5 | Railway 첫 cold start (10-15s) | Medium | Health check + restart policy + keep-alive | 결정 wire |
| 6 | 2FA setup 미완료 (CFO 모바일 부재 시) | Medium | cj-307 aal1 minimum fix + cj-298 SMS fallback | 결정 wire |
| 7 | Pilot candidate 응답 부재 (cold outreach, MEDIUM 회신율 10-20%) | Medium | cj-301 3 outreach templates + cj-315 B-2 discovery protocol + Tier 3 wait-list fallback | 결정 wire (cj-315 wire refresh) |
| 8 | 데이터 누출 (cross-tenant RLS bypass) | Critical | cj-290 8 NEW RLS policies + W1 day-1 verify | 결정 wire |
| 9 | Tier 1/2 contact 확보 부재 (D-2 발송 전, cj-315 신규) | High | Tier 3 wait-list fallback + D-3~D-4 sliding + 2차/3차 follow-up | 결정 wire (cj-315 wire refresh) |

---

## §8 Honestly DEFER 결정 wire (post-pilot 또는 별도 sprint)

| 결정 | 사유 | 결정 wire |
|---|---|---|
| ① PDF header/footer EXTENSION | cj-293 wire 시점 보류, post-pilot enhancement | honestly DEFER |
| ② cj-300 stale docstring cleanup (slack-sdk + sendgrid) | 미사용 import, post-pilot cleanup | honestly DEFER |
| ③ cj-303 carryover 4건 fix (web-e2e Playwright + test-suite-measure + web-test + lint-conventions) | CI signal clarity 강화, post-pilot | honestly DEFER |
| ④ Epic 30+ PRD v2 EXTENSION | pilot feedback 후 재평가 | honestly DEFER (cj-301) |
| ⑤ Epic 29+ spec implementation chain | pilot feedback 후 재평가 | honestly DEFER (cj-301) |
| ⑥ 정식 pricing 결정 | pilot 종료 후 SaaS metrics 기반 결정 | honestly DEFER |

---

## §9 결정 wire 일자 + 운영자 결정 사항

- **본 runbook 작성 일자**: 2026-09-07 (KST, cj-304 wire 시점)
- **cj-315 wire refresh 일자**: 2026-09-10 (KST, D-4)
- **D-day**: 2026-09-14 KST
- **카운트다운**: **4일** (cj-315 wire refresh 기준)
- **운영자 결정 사항** (cj-305 4-service minimal viable 결정 wire + cj-305b Resend swap 적용):
  ① Vercel Pro 결제 ($20/월) — 신용카드 정보 입력
  ② Railway Hobby 결제 ($5/월) — 신용카드 정보 입력
  ③ Supabase Pro 결제 ($25/월) — 신용카드 정보 입력
  ④ ~~Sentry Team 결제 ($26/월)~~ → **cj-305 결정: post-W1 honestly DEFER**
  ⑤ 도메인 costmgr.bizup.io — registrar (Cloudflare/가비아/Namecheap) DNS 관리 권한
  ⑥ ~~Postmark prod 전환 시점~~ → **cj-305b 결정: Resend free tier (3,000/mo + 100/day) 으로 충분, prod 전환 시점 post-pilot 결정 wire 보류**

---

## §10 Cross-references

- **docs/deployment.md** — Phase 4 의 deployment runbook (cj-304 wire EXTENSION)
- **docs/pilot-candidate-discovery-protocol.md** — **cj-315 wire 신규** Tier 1/2 candidate discovery protocol + D-4 contact 확보 + outreach 발송 execution checklist
- **docs/pilot-candidate-template.md** — 8 slot templates + §5 outreach email 3종 + §4 tracker
- **_bmad-output/implementation-artifacts/phase-30-prod-deploy-prep-entry-2026-09-07.md** — cj-304 entry plan
- **_bmad-output/implementation-artifacts/phase-30-prod-deploy-prep-wire-2026-09-07.md** — cj-304 wire plan (4 critical gaps fix + Pilot CLI)
- **_bmad-output/implementation-artifacts/phase-30-prod-deploy-prep-retro-2026-09-07.md** — cj-304 close-out retro
- **_bmad-output/implementation-artifacts/phase-30-pilot-outreach-prep-2026-09-07.md** — cj-301 pilot prep (3 outreach templates + KPI framework)
- **_bmad-output/implementation-artifacts/phase-30-pilot-candidate-list-b1-wire-2026-09-09.md** — cj-309b B-1 candidate list wire (cj-style 265번째)
- **_bmad-output/implementation-artifacts/phase-30-pilot-outreach-exec-prep-entry-2026-09-10.md` — **cj-315 wire entry** (cj-style 278번째)
- **memory/handoff-2026-09-07-cj-304-prod-deploy-prep-wire-done.md** — wire handoff
- **memory/handoff-2026-09-07-cj-304-prod-deploy-prep-retro-done.md** — retro handoff
- **memory/handoff-2026-09-10-cj-315-pilot-outreach-exec-prep-wire-done.md** — **cj-315 wire handoff** (cj-style 278번째)

---

## §11 Why / How to apply

**Why**: cj-304 3 atomic sub-sprint chain CLOSED ✅ HONEST. 4 critical gaps 결정 wire 적용 완료 + Pilot tenant onboarding CLI dry-run-first 결정 wire 적용. production deployment 의 technical blocker 0건 → 운영자가 본 runbook 의 7일 카운트다운 절차 따로 execution 하면 pilot W1 launch 가능.

**How to apply**:
- **즉시 시작**: §1 의 Day 0-1 단계 (Vercel + Railway 계정 생성 + DNS records)
- **Day 2**: §2.3 + §2.5 (Supabase + Postmark sandbox)
- **Day 3-4**: §2.4 (Sentry) + DNS propagation verify + Postmark sender verification
- **Day 4**: §4 Production smoke test (7개 항목 verify)
- **Day 5**: §3 Pilot tenant CLI dry-run → real run
- **Day 6**: §5 Pilot invitation email 발송
- **Day 7 (W1)**: §6 W1 Onboarding run-of-show

## §12 결정 wire 일자

2026-09-07 (KST) — Pilot launch master runbook 작성 일자 (cj-304 wire 시점).
**2026-09-10 (KST) — cj-315 wire refresh**: D-4 → D-0 4일 카운트다운 + Postmark → Resend swap + W4/W8 meeting agenda 신규 EXTENSION + Risk #9 Tier 1/2 contact 확보 부재 risk 신규 추가. Pilot W1 launch 2026-09-14 KST = **4일 카운트다운**.