---
name: cj-305b Resend migration wire
description: cj-style 256번째, Postmark → Resend swap (OQ-EPIC30+-2 v2) 결정 wire, 4 MODIFIED source + 1 MODIFIED docs + 2 NEW meta atomic
metadata:
  type: project
---

# cj-305b Resend migration wire sprint DONE

**cj-style**: 256번째
**날짜**: 2026-09-08 (KST)
**sprint-status**: v4.78 → v4.79 EXTENSION (A723)

## What was done

cj-305b Resend migration wire sprint 결정 wire — cj-305 production deploy day-1 wire 의 option (a) signup 진행 중 Postmark 의 public-domain-email (Gmail) 가입 차단 이슈 정직 회복 결정 wire. **OQ-EPIC30+-2 결정 wire v1 Postmark → v2 Resend swap** 결정 wire 진입. Pilot W1 D-day launch (D-0 = 2026-09-14 KST) 까지 **6일 카운트다운 시작** (cj-305 wire 의 6일 그대로 보존).

**핵심 결정 wire**:

1. **Postmark 의 결정적 blocker 정직 회복**: Postmark 의 signup 시 "Sorry, we don't allow email addresses on public domains such as Gmail and Yahoo. Please use your work email on a private domain." 메시지로 Pilot W1 운영자 (kjw) 의 Gmail 사용 정직 인정. Postmark 결정 wire 보류 결정 wire 진입 → Resend swap 결정 wire.

2. **Resend 의 우위 정직 회복**: public email (GitHub OAuth 또는 email signup) 허용 + W1 free tier **3,000 emails/month** (Postmark sandbox 100/mo 대비 30×) + 100/day rate limit + cleanest Bearer API (`Authorization: Bearer RESEND_API_KEY`) + httpx 와의 seamless integration.

3. **abstraction layer 의 swap 결정 wire**: `EmailProvider` ABC 의 `send(subject, body, recipients, sender) -> str` 인터페이스 보존 → `PostmarkProvider` → `ResendProvider` swap 만으로 email_service.py / email_routes.py 의 비즈니스 로직 변경 0건 결정 wire. **cj-299 wire 의 abstraction 설계 결정 wire 정직 회복** (cj-299 entry 의 "abstraction layer here allows future migration to SendGrid / SES / Gmail via env flag swap (no code change)" 결정 wire 그대로 적용).

## File scope (7 files = 4 MODIFIED source + 1 MODIFIED docs + 2 NEW meta)

1. `apps/api/core/email_provider.py` **MODIFIED** — PostmarkProvider → ResendProvider swap (HTTP API client 결정 wire)
2. `apps/api/modules/reports/email_routes.py` **MODIFIED** — 5 comments EXTENSION (Postmark → Resend 정직 회복)
3. `apps/api/main.py` **MODIFIED** — 1 comment block EXTENSION (email router mount 결정 wire)
4. `apps/api/.env.example` **MODIFIED** — Email delivery section 6 lines EXTENSION (POSTMARK_* → RESEND_* swap 결정 wire)
5. `docs/deployment-account-setup.md` **MODIFIED** — ~12 Postmark references → Resend references 정직 회복
6. `_bmad-output/implementation-artifacts/commit-msg-cj-305bresend.txt` **NEW** (본 commit 메시지)
7. `_bmad-output/implementation-artifacts/handoff-2026-09-08-cj-305b-resend-migration-done.md` **NEW** (본 handoff)

meta — `_bmad-output/implementation-artifacts/sprint-status.yaml` v4.78 → **v4.79 EXTENSION** (A723 cj-305bresend + last_updated_note_v4_79 신규 paragraph) + `memory/MEMORY.md` hook EXTENSION (cj-305b hook 1-line + Active sprint state post cj-305b EXTENSION).

## 결정 wire 보존 확인

- **OQ 결정 wire v1 Postmark → v2 Resend swap 결정 wire** (cj-299 의 Postmark 결정 wire 정직 회복 + cj-305b 의 Resend 결정 wire 신규 active)
- **AD bind 4/4 active 보존** (email_provider.py 의 factory 결정 wire swap 만, AD bind 직접 변경 없음)
- **NFR bind 7/7 active 보존** (email_provider.py 의 ResendProvider 는 NFR bind 직접 변경 없음 — NFR4 PII minimization 은 upstream email_service.redact_pii() 그대로 EXTENSION preserved)
- **capability matrix v1.54 EXTENSION preserved** (cj-305b capability 직접 변경 없음, EXPORT_EMAIL 그대로)
- **audit actions EXTENSION preserved** (cj-305b audit action 직접 변경 없음, `export_email` 그대로)
- **35/35 cumulative 결정 wire 보존**
- **CR 11-3 honest-DEFER 256번째**

## Runtime 동작 변화

- **4 MODIFIED source EXTENSION 결정 wire** = email_provider.py ResendProvider 결정 wire + email_routes.py comments 결정 wire + main.py comments 결정 wire + .env.example 결정 wire
- **1 MODIFIED docs EXTENSION 결정 wire** = deployment-account-setup.md ~12 Postmark references → Resend references 정직 회복 (historical context 보존)
- dev_seed 변경 0건
- ci.yml 변경 0건
- alembic 변경 0건
- **37 pins unchanged** (cj-303 EXTENSION 보존, cj-305b 신규 EXTENSION 0건 — Resend 는 stdlib httpx 사용, AD-14 stack pin 신규 EXTENSION 불필요)
- **14 job matrix unchanged**

## PRE-EXISTING honestly DEFER carryover

- 4건 그대로 보존: web-e2e Playwright + test-suite-measure 잔여 + web-test + lint-conventions
- 2건 추가 defer (cj-305 wire 의 4-service minimal viable 결정 wire 그대로 보존): Sentry + custom DNS → post-W1

## 결정 보류 (운전자)

① **옵션 (a, RECOMMENDED next)**: cj-305b sprint commit 즉시 + Resend + Supabase signup 즉시 시작 (D-6 오늘 2026-09-08 KST, 병렬, ~2-3h, Resend 의 public email 허용으로 blocker 해소)
② 옵션 (b): Pilot candidate list (B-1) 먼저 작성 (cj-305 task #10, D-2 2026-09-12 KST 까지 발송 필수)
③ 옵션 (c): cj-303 carryover 4건 fix (post-pilot 또는 별도 sprint)
④ 옵션 (d): PRD v2 EXTENSION / Epic 29+ spec impl (pilot feedback 후)

## 다음 세션 resume path

1. **cj-305b sprint commit** (atomic, 7 files)
2. **옵션 (a) 즉시 실행**:
   - Resend signup: https://resend.com/signup (GitHub OAuth, 2분)
   - Dashboard → API Keys → Create API Key → `costmgr-pilot-production` → copy `re_<token>` → 1Password secure note
   - Supabase Pro signup: https://supabase.com/dashboard/sign-up (GitHub OAuth, 3분)
   - "New Project" → `costmgr-prod` / ap-northeast-2 Seoul / Pro plan
   - Settings > Database > Connection string → 두 URL (pooled + direct) 모두 copy → 1Password secure note
3. **Day 2 (D-5, 2026-09-09)**: Railway signup + repo connect + env vars fill (DATABASE_URL pooled + RESEND_API_KEY + RESEND_FROM_EMAIL + TZ=Asia/Seoul + RETRY_BACKOFF_MINUTES) + deploy → `curl https://<service>.up.railway.app/health` → 200 verify
4. **Day 3 (D-4, 2026-09-10)**: Vercel signup + deploy + CORS update → browser smoke test + **Resend test email** 발송 (Postmark test script → Resend test script swap 결정 wire, cj-305b sprint scope 외)
5. **Day 4 (D-3, 2026-09-11)**: Pilot tenant CLI dry-run → real (Supabase URL 의존)
6. **Day 5 (D-2, 2026-09-12)**: Pilot candidate outreach (B-1) 발송 (**cj-305 task #10 critical path**)
7. **Day 7 (D-0, 2026-09-14)**: **Pilot W1 KICKOFF 🚀**

## Resend HTTP API quick reference (cj-305b 결정 wire)

```bash
# Resend HTTP API endpoint
POST https://api.resend.com/emails

# Headers
Authorization: Bearer <RESEND_API_KEY>
Content-Type: application/json

# Body
{
  "from": "onboarding@resend.dev",  # sandbox default (custom domain post-W1)
  "to": ["recipient@example.com"],  # JSON array (Postmark 와 다름)
  "subject": "...",
  "text": "..."  # Postmark 의 TextBody → Resend 의 text
}

# Response (200 OK)
{"id": "<email_id>"}

# Error response (4xx)
{"statusCode": <int>, "name": "...", "message": "..."}
```

## Cross-references

- **cj-305 production deploy day-1 wire** (`b732153` + follow-up `0044799`): 4-service minimal viable scope + Pilot W1 D-6→D-0 runbook + compressed entry+wire
- **cj-304 prod deploy prep wire** (`1fdb67d`): 4 critical gaps fix + Pilot tenant CLI (~280 LOC) + env.example + railway.toml + Dockerfile ENV TZ + docs/deployment.md EXTENSION
- **cj-304 prod deploy prep retro** (`e7fb753`): 결정 wire 적용 확인, 33/33 cumulative 보존
- **cj-303 uvicorn boot fix wire** (`ad7b91b`): AD-14 stack pin EXTENSION (apscheduler==3.10.4 + pytz==2024.1)
- **cj-299 email delivery wire** (Postmark 결정 wire v1, cj-305b 에서 Resend 로 swap): `apps/api/core/email_provider.py` ResendProvider 결정 wire + ActionClass.REPORTS `export_email`
- **cj-300 scheduled reports wire**: APScheduler 4 cron + pytz KST + RETRY_BACKOFF_MINUTES=[1,5,30]
- **cj-301 pilot outreach prep**: 5-10 SaaS 제조 스타트업 8-week 무료 pilot, 2026-09-14~11-09 KST

## 결정 wire 일자

2026-09-08 (KST) — 본 cj-305b Resend migration wire sprint 의 실제 commit 일자.
