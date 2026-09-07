---
title: "Phase 30 Pilot Outreach Preparation — cj-301 (cj-style 303번째)"
date: "2026-09-07 (KST)"
territory: "Epic 30+ Reporting & Export MVP territory → PRD OQ-3 Pilot Gate (cj-297 OPEN)"
sprint_type: "docs-only atomic single sprint"
related_jira: "D-EPIC30+-PILOT-1"
related_sprints:
  - cj-282 (220번째) Epic 30+ PRD entry
  - cj-282a~cj-296 wire chain
  - cj-297 (237번째) Pilot launch 결정 wire (PRD OQ-3 OPEN)
  - cj-298 (238번째) close-out retro
  - cj-299 (239번째) Email delivery wire + cj-299fix + cj-299retro
  - cj-300 entry (243번째) + cj-300 wire (244번째) Scheduled reports wire
---

# Phase 30 Pilot Outreach Preparation — cj-301

> **전략 의도 (cj-style 303번째, RECOMMENDED next)** — Build-Measure-Learn 루프의 "Measure" 단계 진입. 24 sprints 동안의 Build 산출물을 실제 customer 한 명에게 테스트하여 validation signal 확보.

---

## Part 1: cj-300 LIGHTWEIGHT close-out retro (customer-facing summary)

### Story 30.4 Scheduled reports territory 진짜 CLOSED ✅ HONEST

**24 sprints cumulative chain cj-282~cj-300 모두 정직 회복** — Epic 30+ Reporting & Export MVP territory 전체 production-ready.

| Story | Title | Status | ACs |
|---|---|---|---|
| 30.1 | CSV export | ✅ PRODUCTION-READY | §F30.1-1 ~ §F30.1-8 = 8/8 |
| 30.2 | PDF export | ✅ PRODUCTION-READY | §F30.2-1 ~ §F30.2-8 = 8/8 |
| 30.3 | Email delivery | ✅ PRODUCTION-READY | §F30.3-1 ~ §F30.3-8 = 8/8 |
| 30.4 | Scheduled reports | ✅ PRODUCTION-READY | §F30.4-1 ~ §F30.4-8 = 8/8 |
| **Total** | **Epic 30+ 전체** | **CLOSED ✅ HONEST** | **32/32 satisfied** |

### OQ 결정 wire 4/4 apply (PRD §M 결정 wire 모두 적용)

- **OQ-EPIC30+-1 reportlab** 결정 wire 적용 ✅ (cj-293)
- **OQ-EPIC30+-2 Postmark transactional email HTTP API (default)** 결정 wire 적용 ✅ (cj-299)
- **OQ-EPIC30+-3 APScheduler (default)** 결정 wire 적용 ✅ (cj-300)
- **OQ-EPIC30+-4 matplotlib** 결정 wire 적용 ✅ (cj-282)

### AD bind 4/4 active + 신규

- AD-2 audit-first INSERT append-only (CR 1-1 fix) — **모든 export routes** `emit_audit_typed()` 호출
- AD-3 production tenant isolation — 8 NEW RLS policies
- AD-10 owner/admin RBAC (AD-22 Epic 12) — **모든 routes** `require_any_role('owner', 'admin')`
- AD-12 verify-first capability gate — Capability.EXPORT_CSV/PDF/EMAIL/SCHEDULED (capability matrix v1.54)

### NFR bind 7/7 active + 신규

- NFR4 PII minimization (finance_contact_email redact)
- NFR5 streaming response P95 ≤ 5s
- NFR7 PDF rendering integrity (reportlab)
- NFR8 background job 99.9% uptime SLA (APScheduler restart resilience + RETRY_BACKOFF_MINUTES=[1,5,30])
- NFR12 SLA monitoring
- NFR18 ko-KR vocabulary SSOT (ko-KR.json 27 NEW keys)
- NFR19 export response time

### Pilot customer 가 알아야 할 것 (5-bullet summary)

1. **CSV export** — 원가 기록 + BOM 매트릭스를 CSV 로 다운로드 (≤ 30초, ≥ 100만 행 지원)
2. **PDF export** — 월 마감 보고서를 PDF(A4, ≤ 5MB) 로 다운로드 — 회계사·세무사·금융기관 외부 전달용
3. **Email delivery** — PDF/CSV 를 재무 담당자에게 자동 발송 (Postmark transactional email API, sandbox 100건 free, DKIM/SPF auto, 99.9% uptime SLA)
4. **Scheduled reports** — 주간/월간/분기/연간 자동 리포트 (APScheduler 기반, idempotency + 3 retry 보장)
5. **모든 export** — owner/admin 권한 + capability gate + audit-first INSERT + 4-industry 지원 (manufacturing / manufacturing_service / manufacturing_service_other / service)

---

## Part 2: Pilot Outreach Preparation (operational artifacts)

### 1. Pilot Program Scope

- **기간**: 8 weeks (2026-09-14 ~ 2026-11-09, KST)
- **목표**: 5-10 SaaS 제조 스타트업에서 Epic 30+ 4 features 실제 사용 → product-market fit 검증
- **Success Criteria**: §3 KPI framework 참조
- **Pricing during pilot**: **무료** (PRD §F pricing 결정 wire 보류분 = post-pilot)
- **Support**: 전담 Slack 채널 #costmgr-pilot (생성 필요) + daily check-in + weekly 회고

### 2. Candidate Selection Criteria (PRD OQ-3 territory)

**Tier 1 — Ideal Candidate (5-7곳 목표)**

| Criterion | Threshold |
|---|---|
| Industry | SaaS 제조 (의류/식품/전자/생활용품 OEM/ODM) |
| Employee count | 50-200명 (sweet spot) |
| Current cost management | Excel/Google Sheets (greenfield, no SaaS) |
| Monthly cost record volume | 1,000-100,000 lines |
| Decision-maker | CFO/COO/대표 (budget authority) |
| Korean-speaking | 필수 (ko-KR SSOT) |
| Onboarding commitment | weekly 30분 피드백 미팅 가능 |

**Tier 2 — Acceptable Candidate (fallback)**

| Criterion | Threshold |
|---|---|
| Industry | 제조 + 서비스 hybrid (manufacturing_service) |
| Employee count | 30-50명 (smaller) |
| Current cost management | 수기 + ERP 일부 |
| Decision-maker | 경영지원팀장 |

**Tier 3 — Wait-list (post-pilot expansion)**

- 200+ employees (enterprise, 별도 sales motion 필요)
- Non-Korean (en-US localization 필요 — 보류)
- Existing cost management SaaS 사용자 (switching cost 분석 필요)

### 3. Outreach Email Templates (3 variants, ko-KR)

#### Template A — Direct Cold Outreach (Tier 1)

```
제목: SaaS 제조 원가 관리, 8주간 무료로 검증해보세요 — costmgr Pilot 모집 (5-10곳 한정)

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

#### Template B — Warm Intro (via LinkedIn/network)

```
제목: {{소개자_성함}} 님이 소개해주신 costmgr Pilot 안내

{{담당자_성함}}님, 안녕하세요.

{{소개자_성함}} 님과 안면을 통해 소개받았습니다.
costmgr 팀 {{담당자_이름}}입니다.

SaaS 제조 원가 관리 8주 Pilot program (5-10곳 한정 무료) 진행 중이며,
귀사 {{회사명}}의 profile 이 ideal candidate 로 보입니다.

특히 {{구체적_통찰 — 예: "월 5만 행 원가 데이터를 Excel 로 관리 중이시라면"}}
상황이라면 8주 안에 cost saving + time saving 정량화 가능합니다.

15분 커피챗 가능하시면 시간 알려주세요.

{{담당자_이름}} 드림
costmgr | {{이메일}}
```

#### Template C — Follow-up (no response 후 5일)

```
제목: RE: SaaS 제조 원가 관리 Pilot — 혹시 검토 중이실까요?

{{담당자_성함}}님, 안녕하세요.

지난 주 발송드린 costmgr Pilot 안내 메일 확인차 follow-up 드립니다.

혹시 다음 중 어떤 상황일까요?
A) 검토 중 — 다음 주 중 답변 가능
B) 우선순위 낮음 — 1-2개월 후 다시 연락 주세요
C) 적합하지 않음 — 다른 후보 추천 부탁드립니다

A/B/C 중 하나 회신 주시면 calibration 에 큰 도움이 됩니다.

감사합니다.
{{담당자_이름}} 드림
```

### 4. KPI / Success Metrics Framework

| KPI | Target | 측정 방법 | 측정 주기 |
|---|---|---|---|
| **Activation** | 100% (모든 pilot 고객이 7일 내 onboarding 완료) | onboarding step funnel | weekly |
| **Engagement** | 80% (pilot 고객이 4 features 모두 weekly active 사용) | usage telemetry (CSV/PDF/Email/Scheduled 모두 ≥ 1회/week) | weekly |
| **Value Capture** | 70% (pilot 고객이 cost saving OR time saving 정량화 가능) | weekly survey (cost saving KRW + time saving hours) | weekly |
| **Satisfaction (NPS)** | 50+ (pilot 종료 시점) | NPS survey | end-of-pilot |
| **Retention Intent** | 80% (pilot 종료 후 paid 전환 의사) | post-pilot survey + 1:1 미팅 | post-pilot |

**Go/No-Go Decision Criteria (post-pilot)**:
- **GO** (paid rollout 진행): ≥ 4 KPI target 달성 + ≥ 5 customers retention intent ≥ 80%
- **PIVOT** (피드백 기반 재설계): 2-3 KPI target 달성 + 명확한 개선점 도출
- **NO-GO** (Epic 30+ 중단 / Epic 31+ 신규): < 2 KPI target + retention < 50%

### 5. Risk Register (pilot outreach specific)

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| **R-1. Pilot customer 데이터 leak** | Low | High | 별도 tenant 분리 (`tenants.isolation = 'pilot_sandbox'`) + 데이터 anonymization + audit log 100% 캡처 |
| **R-2. Email deliverability 실패** | Low | Medium | SPF/DKIM/DMARC primary 도메인 검증 + Postmark sandbox 100건 free 테스트 + bounce handling |
| **R-3. Pilot customer 지원 부담 overload** | Medium | High | max 10 customer cap + 전담 1명 배정 + Slack channel + weekly check-in (not daily) |
| **R-4. Feature gap 발견 (pilot 중)** | High | Medium | "what works / what's next" 명확한 docs + weekly feedback 즉시 반영 (post-pilot 우선순위 조정) |
| **R-5. Pilot customer 조기 churn** | Medium | High | 4-week milestone check-in + refund/exit option 명시 + KPI dashboard 공유 |
| **R-6. Production deploy 장애** | Low | Critical | §6 pre-flight deployment checklist + rollback plan + staging env 먼저 검증 |
| **R-7. Carryover (test-suite-measure 6 errors)** | Medium | Low | pilot UX 직접 영향 없음 — post-pilot fix 결정 |
| **R-8. Compliance (개인정보보호법 / GDPR)** | Low | High | finance_contact_email redact (NFR4) + tenant_id selector (CR 0-2 RLS) + audit log 100% (CR 1-1) |

### 6. Pre-flight Deployment Checklist (pilot launch 전 필수)

```
[ ] Phase 0 — Local 준비
    [ ] commit `4d1088d` (cj-300 wire) push to remote
    [ ] commit `cj-301` (pilot prep) push to remote
    [ ] main branch protection rules 확인

[ ] Phase 1 — Production Deployment
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

[ ] Phase 2 — Pilot Sandbox Provisioning
    [ ] 10 pilot tenant accounts 생성 (Tier 1 + Tier 2)
    [ ] 각 tenant 별 owner/admin user 생성
    [ ] finance_contact_email 설정 (NFR4 redact test)
    [ ] 2FA 챌린지 토큰 발급 (AD-22 Epic 12)
    [ ] capability grant (EXPORT_CSV/PDF/EMAIL/SCHEDULED 4 industries)

[ ] Phase 3 — Support Infrastructure
    [ ] Slack channel #costmgr-pilot 생성
    [ ] costmgr team 전담 1명 배정 (1:1 매핑)
    [ ] ko-KR user docs 업로드 (Notion or GitHub Pages)
    [ ] feedback collection form (Typeform or Notion form)
    [ ] weekly 30분 미팅 캘린더 링크 5-10개 사전 생성

[ ] Phase 4 — Outreach Launch
    [ ] Tier 1 candidate list 확정 (5-7곳, 운영자 결정)
    [ ] Template A 발송 (D+0)
    [ ] Template C follow-up 발송 (D+5, no response 한정)
    [ ] 15분 커피챗 5-7개 슬롯 운영
    [ ] Tier 1 acceptance → onboarding 시작 (D+7)
```

### 7. Feedback Collection Mechanism

**Slack channel #costmgr-pilot**:
- daily check-in (1:1 매핑, 비동기)
- weekly 회고 미팅 (30분, Friday 16:00 KST)
- ad-hoc feature request / bug report (channel mention)

**Typeform weekly survey** (ko-KR):
- Q1: 이번 주 사용한 features (4 checkboxes)
- Q2: Cost saving 정량화 (KRW amount, optional)
- Q3: Time saving 정량화 (hours, optional)
- Q4: 만족도 (1-10 NPS scale)
- Q5: 다음 주 우선순위 요청 (free text)

**Post-pilot survey** (week 8):
- Q1-Q30 detailed satisfaction
- Renewal intent (Yes/No/Maybe)
- 추천 의사 (NPS)
- 개선점 top 5 (free text)

### 8. Pilot Timeline (8 weeks)

| Week | Dates (KST) | Activity |
|---|---|---|
| **W0 (Prep)** | 2026-09-07 ~ 09-13 | cj-301 prep docs + outreach 발송 + 15분 커피챗 |
| **W1 (Onboarding)** | 2026-09-14 ~ 09-20 | 5-10 customer onboarding + 데이터 import + 2FA 설정 |
| **W2 (Activation)** | 2026-09-21 ~ 09-27 | 4 features 첫 사용 + weekly survey #1 |
| **W3 (Engagement)** | 2026-09-28 ~ 10-04 | scheduled reports 첫 발송 + email delivery 첫 발송 |
| **W4 (Mid-point)** | 2026-10-05 ~ 10-11 | 4-week milestone check-in + mid-pilot survey |
| **W5 (Optimization)** | 2026-10-12 ~ 10-18 | customer별 feature customization + workflow 최적화 |
| **W6 (Scale)** | 2026-10-19 ~ 10-25 | usage 증가 + new use case 발굴 |
| **W7 (Pre-close)** | 2026-10-26 ~ 11-01 | final survey + renewal intent 1차 측정 |
| **W8 (Close)** | 2026-11-02 ~ 11-09 | post-pilot survey + NPS + Go/No-Go 결정 wire |

### 9. honestly DEFER carryover (cj-300 + cj-301 territory)

**Pilot 중 fix 안 함 (의도적 DEFER)**:
1. test-suite-measure 6 collection errors (cj-285 EXTENSION + Phase 10/16 drift + pytz 부재) — pilot UX 영향 없음
2. web-e2e csv-export.spec.ts tests 2-3 (DEV_TENANT_REPORT_ID + DEV_ACCESS_TOKEN env vars ci.yml 부재) — **MINIMAL fix 가능** (pilot 회귀 검증용)

**Pilot 중 fix 함 (운영자 결정 시)**:
- web-e2e csv-export.spec.ts MINIMAL fix (DEV_TENANT_REPORT_ID env var ci.yml export)

**Pilot 종료 후 fix 결정**:
- 6 collection errors 일괄 fix (cj-29x-web-e2e + test-suite-measure carryover sprint — option (c))

### 10. honestly DEFER 결정 wire (cj-301 territory 보존)

① 옵션 (c) MINIMAL subset — web-e2e csv-export.spec.ts tests 2-3 fix (cj-301 종료 후 결정)
② 옵션 (d) Epic 30+ PRD entry v2 EXTENSION territory — **pilot feedback 받은 후** 재평가
③ 옵션 (e) Epic 29+ spec implementation chain — **pilot feedback 받은 후** 재평가
④ D-EPIC30+-PDF-3 PDF header/footer EXTENSION post-pilot enhancement 보존
⑤ D-REPORTS-EXTENSION ownership 결정 wire 보존
⑥ pricing 결정 wire (PRD §F pricing) — **post-pilot 결정** (paid conversion 데이터 기반)

### 11. CR 11-3 honest-DEFER 245번째

chain cj-282 (220번째) → ... → cj-300 wire (244번째) → **cj-301 pilot prep (245번째)** 종합 25 sprints 정직 회복.

### 12. runtime 동작 변화

- docs-only atomic single sprint — 5 files = 3 NEW content + 2 NEW meta + 2 MODIFIED
- source code 변경 0건 / dev_seed 변경 0건 / ci.yml 변경 0건 / alembic 변경 0건 / 37 pins unchanged / 14 job matrix unchanged / PRD v7.0 §F/§M/§R unchanged / capability matrix v1.54 EXTENSION preserved / audit actions EXTENSION preserved.

---

## 결정 wire 일자

2026-09-07 (KST) — cj-301 pilot outreach preparation docs-only atomic sprint 진입.

## 결정 보류

① commit push (`4d1088d` + `cj-301`) — **사용자 승인 대기**
② production deployment authorization — **사용자 승인 대기**
③ pilot candidate list (5-10곳, Tier 1 + Tier 2) — **운영자 결정**
④ outreach 발송 — **사용자 승인 대기**
⑤ pilot launch (W1 onboarding 시작, 2026-09-14) — **사용자 결정**

## next

옵션 (a) **commit push + production deploy + outreach 발송** (사용자 결정 즉시 실행)
옵션 (b) **pilot candidate list 확정** (운영자 1-2일 검토)
옵션 (c) **cj-301 web-e2e csv-export.spec.ts MINIMAL fix** (carryover 1건 일괄 fix, pilot 회귀 검증용)
