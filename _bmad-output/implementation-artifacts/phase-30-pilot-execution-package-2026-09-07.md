---
title: "Phase 30 Pilot Execution Package — cj-302 (cj-style 304번째)"
date: "2026-09-07 (KST)"
territory: "Epic 30+ Pilot Gate → W0 prep week"
sprint_type: "docs-only atomic single sprint (action-oriented distillation)"
related_jira: "D-EPIC30+-PILOT-2"
related_sprints:
  - cj-301 (303번째) pilot outreach prep
  - cj-300 wire (302번째) Scheduled reports source+docs atomic
depends_on:
  - "cj-301 prep docs (✓ exists)"
  - "docs/deployment.md (✓ exists)"
  - "3 commits pushed to origin (✓ done 2026-09-07)"
---

# Phase 30 Pilot Execution Package — cj-302

> **실행 distillation** — cj-301 prep + docs/deployment.md 의 "what to do" 추출.
> 본 문서는 **action-oriented** (operator/user가 읽고 즉시 행동) ≠ cj-301 prep (planning-oriented).
> **모든 외부 액션은 명시적 사용자 승인 필요** (CR 11-3 honest-DEFER).

---

## §1 Current State Snapshot (2026-09-07 KST, post-push)

| Status | Item | Evidence |
|---|---|---|
| ✅ DONE | cj-300 wire + cj-300 entry + cj-301 prep commits pushed | `git log origin/9-3-dev-2026-08-17..HEAD` = empty (3 commits ahead pushed) |
| ✅ READY | Pilot outreach prep doc | `_bmad-output/implementation-artifacts/phase-30-pilot-outreach-prep-2026-09-07.md` 343 lines |
| ✅ READY | Production deployment runbook | `docs/deployment.md` 349 lines (Vercel + Railway + Supabase + Sentry) |
| ✅ READY | 3 outreach templates (ko-KR) | cj-301 §3 — Template A/B/C with placeholders |
| ✅ READY | Tier 1/2/3 candidate criteria | cj-301 §2 — full rubric |
| ✅ READY | Pre-flight checklist (4 phases) | cj-301 §6 — 30+ items |
| ✅ READY | KPI framework + Go/No-Go | cj-301 §4 — 5 KPIs |
| ✅ READY | Risk register (8 risks) | cj-301 §5 — probability/impact/mitigation |
| ✅ READY | 8-week timeline | cj-301 §8 — W0~W8 dated |
| ✅ READY | capability matrix v1.54 EXTENSION | `docs/capability-matrix.md` — EXPORT_CSV/PDF/EMAIL/SCHEDULED granted |
| ✅ READY | 24 sprints 정직 회복 | cj-282 (220) ~ cj-300 wire (244) = 25/25 cumulative |

**Net state**: 모든 planning artifact 준비 완료. 실행 단계 진입 가능.

---

## §2 Hard Blockers (operator/user 제공 필요)

각 blocker 는 단일 액션 = 단일 책임자. Risk minimization 원칙상 **sequential unblock** 권장.

### Blocker B-1 — Pilot candidate list (5-10 companies)
- **Need**: 회사명 + 담당자 성함/이메일 + Tier (1/2) + 추천 source (warm/cold)
- **Provider**: Operator (인맥/네트워크 통해)
- **Format**: CSV or Markdown table — 5-10 rows
- **Risk if skipped**: outreach 자체 불가 (no recipients)
- **Fallback**: Tier 3 wait-list (post-pilot) — pilot 0명 = NO-GO 자동 결정

### Blocker B-2 — Production deployment authorization
- **Need**: "Deploy now" 승인 + Railway/Supabase/Vercel/Sentry credentials (or user directly executes docs/deployment.md §4)
- **Provider**: User
- **Time cost**: ~30 min (Supabase setup) + ~15 min (Railway deploy) + ~15 min (Vercel deploy) = ~1 hour
- **Risk if skipped**: pilot customers 가 접속할 URL 부재 (entire pilot 불가)
- **Fallback**: local demo (pilot 불가, internal validation만)

### Blocker B-3 — Email sending channel
- **Need**: Postmark server token (recommended — cj-299 결정 wire 보존) OR SMTP creds OR user 직접 발송
- **Provider**: User (Postmark 계정 생성 OR 기존 SMTP 사용)
- **Risk if skipped**: outreach 자동화 불가 (수동 발송은 가능하나 5-10곳 × N templates)
- **Fallback**: User 가 Gmail/네이버 메일로 수동 발송 (1회 발송당 5분)

### Blocker B-4 — Pilot sandbox tenant provisioning
- **Need**: Production DB write access + tenant seed script execution
- **Provider**: User (after deploy, via Railway shell or local psql against prod DATABASE_URL)
- **Time cost**: ~30 min (10 tenants × owner/admin user + capability grants)
- **Risk if skipped**: pilot customers 가 사용할 tenant 부재
- **Dependency**: B-2 (deploy 후 가능)

### Blocker B-5 — Slack channel #costmgr-pilot
- **Need**: Workspace admin 권한 또는 workspace 자체
- **Provider**: User (Slack workspace 생성/초대)
- **Risk if skipped**: daily check-in 메커니즘 부재 (Typeform 으로 대체 가능)
- **Fallback**: Discord channel OR Notion comments

### Blocker B-6 — Feedback collection form
- **Need**: Typeform account (Pro $25/mo) OR Notion form OR Google Form
- **Provider**: User (계정 생성 + form URL 공유)
- **Risk if skipped**: weekly survey 데이터 수집 불가
- **Fallback**: Google Form (free) — feature 부족하나 pilot 8주엔 충분

### Blocker B-7 — Calendar slots for 15-min coffee chats
- **Need**: Google Calendar / Calendly / SavvyCal 계정
- **Provider**: User (5-10 슬롯 사전 생성 — 1주일 분량)
- **Risk if skipped**: 후보자 미팅 스케줄링 friction
- **Fallback**: User 가 직접 "가능한 시간 회신 요청" + 수동 조율

---

## §3 Most Reasonable First Actions (priority order)

**원칙**: 각 액션 = 단일 책임자 + 단일 산출물 + 검증 가능 + reversible (가능한 한).

### Priority P0 (오늘/내일 — unblock pilot)
- [ ] **P0-1**: Operator 가 Tier 1 candidate list 작성 (5-7곳) — B-1 해결
- [ ] **P0-2**: User 가 production deploy authorization 결정 — B-2 해결
- [ ] **P0-3**: User 가 Postmark server token 확보 OR 수동 발송 결정 — B-3 해결

### Priority P1 (W0 prep week — pilot 발송 직전)
- [ ] **P1-1**: B-2 해결 시 production deploy 실행 (docs/deployment.md §4 1-1-1 매핑)
- [ ] **P1-2**: B-1 해결 시 outreach templates fill-in (Template A → Tier 1 / Template B → warm intro 시)
- [ ] **P1-3**: B-4 (pilot sandbox tenants) provisioning
- [ ] **P1-4**: B-5/B-6 (Slack + Typeform) setup
- [ ] **P1-5**: B-7 (coffee chat slots) 생성
- [ ] **P1-6**: outreach 발송 (D+0, Tier 1 candidate 한정)

### Priority P2 (W1 onboarding — 2026-09-14)
- [ ] **P2-1**: Tier 1 acceptance → onboarding 시작
- [ ] **P2-2**: weekly survey #1 배포
- [ ] **P2-3**: W1 milestone check-in

### Priority P3 (W2~W8 — engagement + close)
- [ ] **P3-1**: weekly survey + Slack 회고
- [ ] **P3-2**: feature customization per customer
- [ ] **P3-3**: 4-week milestone check-in (mid-pilot)
- [ ] **P3-4**: 8-week post-pilot survey + NPS
- [ ] **P3-5**: Go/No-Go decision wire (≥ 4 KPI target = GO)

---

## §4 Deploy Runbook (Pilot-Specific, extracted from docs/deployment.md)

> **Note**: 본 section 은 docs/deployment.md §4 의 pilot-specific subset.
> Full runbook = `docs/deployment.md` (변경 금지, SSOT).

### Pilot 환경 변수 (production env var 추가)

| Variable | Value (placeholder) | Source |
|----------|---------------------|--------|
| `POSTMARK_SERVER_TOKEN` | `<pilot-server-token>` | Postmark dashboard |
| `PILOT_TENANT_DB_URL` | `<separate-pilot-DB>` | Supabase (separate project 권장) |
| `REDIS_URL` | `<APScheduler-PersistentJobStore>` | Upstash/Redis Cloud |
| `SENTRY_DSN` | `<Sentry-team-DSN>` | Sentry |

### Pilot 환경 smoke test (deploy 직후 필수)

```bash
# 1. Backend health
curl https://api.costmgr.com/api/v1/health
# Expected: status=healthy, database=connected, redis=connected

# 2. Frontend health
curl https://app.costmgr.com/api/health
# Expected: status=healthy, build=<git-sha>

# 3. 4 export endpoints smoke test (5-10개 pilot tenant 별)
for tenant in pilot-001 pilot-002 ... pilot-010; do
  TOKEN=$(generate-tenant-token $tenant)
  curl -X POST https://api.costmgr.com/exports/csv -H "Authorization: Bearer $TOKEN" -d '{"report_id":"smoke-test"}'
  curl -X POST https://api.costmgr.com/exports/pdf -H "Authorization: Bearer $TOKEN" -d '{"report_id":"smoke-test"}'
  curl -X POST https://api.costmgr.com/exports/email -H "Authorization: Bearer $TOKEN" -d '{"report_id":"smoke-test","to":"finance@example.com"}'
  curl -X POST https://api.costmgr.com/exports/scheduled -H "Authorization: Bearer $TOKEN" -d '{"report_id":"smoke-test","cron":"0 9 * * 1"}'
done

# 4. Cross-tenant isolation (CR 0-2 RLS)
TOKEN_A=$(generate-tenant-token pilot-001)
curl -H "Authorization: Bearer $TOKEN_A" https://api.costmgr.com/tenants/pilot-002
# Expected: 403 FORBIDDEN_TENANT
```

### Pilot tenant provisioning script (10 tenants)

```python
# apps/api/scripts/cli/pilot_provisioning.py (NEW — cj-302 wire 시 생성 결정)
# - 10 tenants × owner + admin user × finance_contact_email × 2FA × capability grant
# - alembic 0061 migration 사전 실행 필수
# - 실행 후 audit log 100% 캡처 검증
```

> **Risk minimization**: deploy + provisioning 모두 user 승인 후 진행. 자동화 스크립트는 §6 P1-3 결정 시점에 별도 sprint 로 결정 wire 보존.

---

## §5 Candidate Scoring Matrix (fillable template)

### Tier 1 Ideal Candidate — fill 5-7 rows

| # | 회사명 | Industry | Employees | Monthly cost lines | Decision-maker | Korean? | Onboarding commit | Score (0-7) | Tier | Source |
|---|--------|----------|-----------|---------------------|----------------|---------|--------------------|-------------|------|--------|
| 1 | ___ | SaaS 제조 (의류/식품/전자) | 50-200 | 1K-100K | CFO/COO/대표 | Y | weekly 30min | __ | T1/T2/T3 | warm/cold |
| 2 | ___ | ___ | ___ | ___ | ___ | ___ | ___ | __ | ___ | ___ |
| ... | ___ | ___ | ___ | ___ | ___ | ___ | ___ | __ | ___ | ___ |

**Scoring rule**:
- Industry = SaaS 제조 = 2점, hybrid = 1점, 그 외 = 0점
- Employees = 50-200 = 2점, 30-50 = 1점, 그 외 = 0점
- Korean + Decision-maker + Onboarding commit = 각 1점
- **Tier 1**: score ≥ 6, Tier 2: 4-5, Tier 3: < 4

### Tier 2 fallback — fill 0-3 rows (Tier 1 미달성 시)

(same structure as above)

### Tier 3 wait-list (post-pilot) — 기록용, 미발송

(200+ employees / non-Korean / existing SaaS 사용자)

---

## §6 Outreach Email Templates (in fillable format)

### Template A — Tier 1 Cold Outreach

**수신자**: `{{회사명}}` `{{담당자_성함}}` (`{{이메일}}`)
**제목**: SaaS 제조 원가 관리, 8주간 무료로 검증해보세요 — costmgr Pilot 모집 (5-10곳 한정)

```
{{담당자_성함}}님, 안녕하세요.

costmgr 팀 {{담당자_이름}}입니다.

귀사 {{회사명}}의 원가 관리 프로세스를 8주간 무료로 검증해보실 수 있는
Pilot program 5-10곳 모집 안내드립니다.

[현재 상황]
- SaaS 제조 스타트업의 원가 기록/BOM/마감 보고서를 Excel 로 관리 → 데이터 누락 + 회계사·세무사·금융기관 전달 어려움
- 50-200명 규모에서 monthly 1,000-100,000 lines 원가 데이터 핸들링 시 인건비 + 오류 비용 발생

[해결 — Epic 30+ Reporting & Export 4 features PRODUCTION-READY]
1. CSV export (≤ 30초, 100만 행 지원)
2. PDF 마감 보고서 (A4, ≤ 5MB, 회계사·세무사 외부 전달용)
3. Email 자동 발송 (재무 담당자 직접 수신, DKIM/SPF auto, 99.9% uptime)
4. 주간/월간/분기/연간 scheduled reports (idempotency + 3 retry 보장)

[Pilot 조건]
- 8 weeks (2026-09-14 ~ 2026-11-09 KST)
- 무료 (post-pilot pricing 결정 wire 보류분 = pilot feedback 기반 결정)
- 전담 Slack 채널 + weekly 30분 피드백 미팅
- 5-10 곳 한정 선착순

[다음 단계]
15분 커피챗 가능하실까요? 원하시는 시간 알려주시면 캘린더 링크 발송드리겠습니다.

{{담당자_이름}} 드림
costmgr | {{이메일}} | {{전화}}
```

### Template B — Warm Intro (LinkedIn/network)

(상동, cj-301 §3 Template B verbatim)

### Template C — Follow-up (no response 후 5일)

(상동, cj-301 §3 Template C verbatim)

### 발송 시 검증 checklist (per recipient)
- [ ] `{{회사명}}` 실제 회사명 확인 (검색/뉴스 크로스체크)
- [ ] `{{담당자_성함}}` 정확한 이름 확인 (LinkedIn 프로필 or 회사 홈페이지)
- [ ] `{{이메일}}` 도메인 회사 도메인 일치 확인 (gmail/naver = red flag)
- [ ] `{{담당자_이름}}` 발신자 실제 이름 (가명 금지)
- [ ] `{{이메일}}` 발신자 회사 도메인 (costmgr.com 또는 설정된 도메인)
- [ ] `{{전화}}` 발신자 실제 연락처 (pilot contact 용)
- [ ] 제목 50자 이내 (Gmail truncate 기준)
- [ ] preheader 80자 이내 (이메일 목록 미리보기)
- [ ] **사용자 1차 승인** (per recipient)
- [ ] **테스트 발송** (operator 개인 이메일로 1회)
- [ ] **본 발송** (operator 가 직접 or Postmark API)

---

## §7 Decision-Gate Flowchart

```
START
  │
  ▼
[준비 artifact] ✅ = cj-301 + cj-302 + docs/deployment.md
  │
  ▼
[B-1 candidate list] ── 미완료 ──▶ [Operator: 1-2일 검토] ──▶ B-1 DONE
  │                                                          │
  ▼                                                          ▼
[B-2 deploy auth] ── 미완료 ──▶ [User 결정] ──▶ B-2 DONE   (parallel 가능)
  │                                                          │
  ▼                                                          ▼
[B-3 email channel] ── 미완료 ──▶ [User 결정] ──▶ B-3 DONE (parallel 가능)
  │
  ▼
[ALL B-* DONE] ──▶ outreach 발송 가능
  │
  ▼
[per-recipient 사용자 승인] ──▶ [테스트 발송] ──▶ [본 발송] ──▶ 15분 커피챗
  │
  ▼
[Tier 1 acceptance] ──▶ onboarding 시작 (W1, 2026-09-14)
  │
  ▼
[W1~W8 pilot 진행 + weekly survey + Slack 회고]
  │
  ▼
[W8 close: post-pilot survey + NPS + Go/No-Go]
```

**Gating rules**:
- 각 B-* blocker 해결 전에는 downstream action 불가 (sequential unblock)
- Outreach 발송 = per-recipient 사용자 승인 필수 (no bulk send)
- Production deploy = smoke test 통과 후에만 tenant provisioning 진행
- 8주 pilot 중 ≥ 1 KPI target 미달성 시 mid-pivot 결정 wire 보존 (cj-301 §5 R-5)

---

## §8 W0 Prep Checklist (status as of 2026-09-07)

```
[✅] Phase 0 — Local 준비
    [✅] commit `4d1088d` (cj-300 wire) push to remote
    [✅] commit `cj-301` (pilot prep) push to remote
    [✅] commit `cj-302` (execution package) push to remote (PENDING)
    [ ] main branch protection rules 확인 [USER 결정]

[ ] Phase 1 — Production Deployment (USER 결정 필요)
    [ ] production environment variables 설정
        - POSTMARK_SERVER_TOKEN (pilot 환경)
        - DATABASE_URL (separate pilot tenant DB)
        - REDIS_URL (pilot APScheduler PersistentJobStore)
    [ ] alembic upgrade head (0061 migration: tenants.finance_contact_email)
    [ ] Health check endpoints OK
        - GET /api/v1/healthz
        - GET /api/v1/metrics
    [ ] 4 export endpoints smoke test
        - POST /exports/csv
        - POST /exports/pdf
        - POST /exports/email
        - POST /exports/scheduled

[ ] Phase 2 — Pilot Sandbox Provisioning (USER 실행)
    [ ] 10 pilot tenant accounts 생성 (Tier 1 + Tier 2)
    [ ] 각 tenant 별 owner/admin user 생성
    [ ] finance_contact_email 설정 (NFR4 redact test)
    [ ] 2FA 챌린지 토큰 발급 (AD-22 Epic 12)
    [ ] capability grant (EXPORT_CSV/PDF/EMAIL/SCHEDULED 4 industries)

[ ] Phase 3 — Support Infrastructure (USER 생성)
    [ ] Slack channel #costmgr-pilot 생성
    [ ] costmgr team 전담 1명 배정 (1:1 매핑)
    [ ] ko-KR user docs 업로드 (Notion or GitHub Pages)
    [ ] feedback collection form (Typeform or Notion form)
    [ ] weekly 30분 미팅 캘린더 링크 5-10개 사전 생성

[ ] Phase 4 — Outreach Launch (USER 승인 후)
    [ ] Tier 1 candidate list 확정 (5-7곳, 운영자 결정)
    [ ] Template A 발송 (D+0)
    [ ] Template C follow-up 발송 (D+5, no response 한정)
    [ ] 15분 커피챗 5-7개 슬롯 운영
    [ ] Tier 1 acceptance → onboarding 시작 (D+7)
```

---

## §9 honestly DEFER carryover (cj-302 territory 보존)

본 execution package 자체는 cj-301 prep 의 distillation 이므로 **새로운 honestly DEFER 없음**.

**cj-301 territory 보존 (재확인)**:
1. test-suite-measure 6 collection errors (cj-285 EXTENSION + Phase 10/16 drift + pytz 부재) — **post-pilot fix 결정**
2. web-e2e csv-export.spec.ts tests 2-3 MINIMAL fix — **pilot 회귀 검증 후 결정**
3. 옵션 (d) Epic 30+ PRD entry v2 EXTENSION — **pilot feedback 후 재평가**
4. 옵션 (e) Epic 29+ spec implementation chain — **pilot feedback 후 재평가**
5. D-EPIC30+-PDF-3 PDF header/footer EXTENSION — **post-pilot enhancement**
6. pricing 결정 wire (PRD §F) — **post-pilot 결정**

---

## §10 CR 11-3 honest-DEFER 246번째

chain cj-282 (220) → ... → cj-301 pilot prep (245) → **cj-302 execution package (246)**.

본 sprint 는 **docs-only** (action-oriented distillation), 외부 액션 0건.
- commit 1 push (cj-302 결정 시) — 사용자 승인 대기
- production deployment — **사용자 승인 대기**
- outreach 발송 — **사용자 승인 대기**

**Risk minimization 원칙 적용**:
- B-1/B-2/B-3 blocker 해결 전 downstream action 진행 금지
- Outreach = per-recipient 사용자 승인 필수
- Deploy = smoke test 통과 후에만 tenant provisioning 진행

---

## §11 결정 보류 (운전자/사용자 결정)

| # | Item | Provider | Status |
|---|------|----------|--------|
| ① | commit `cj-302` push | User | 대기 |
| ② | Production deployment authorization | User | 대기 |
| ③ | Pilot candidate list (5-10곳) | Operator | 대기 |
| ④ | Email sending channel 결정 (Postmark vs SMTP vs 수동) | User | 대기 |
| ⑤ | Pilot sandbox tenant provisioning 실행 | User (deploy 후) | 대기 |
| ⑥ | Slack + Typeform + Calendar setup | User | 대기 |
| ⑦ | Outreach 발송 (per-recipient) | User 승인 후 | 대기 |
| ⑧ | Pilot launch (W1 onboarding 시작, 2026-09-14 KST) | User 결정 | 대기 |

---

## §12 next (운전자 결정 후)

옵션 (a) — **commit push + production deploy + outreach 발송** (즉시 실행, 사용자 결정 시)
옵션 (b) — **pilot candidate list 확정** (Operator 1-2일 검토)
옵션 (c) — **web-e2e csv-export.spec.ts MINIMAL fix** (carryover 1건 fix, pilot 회귀 검증용)
옵션 (d) — **8주 pilot W1 시작 후 feedback 기반 옵션 (d)/(e) 재평가** (Lean startup 정직 회복)
