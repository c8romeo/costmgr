# Pilot Candidate Discovery & Outreach Protocol (B-2)

- **일자**: 2026-09-10 (KST, **D-4 = D-day 2026-09-14 까지 4일**)
- **소스 결정 wire**: cj-301 (Pilot prep) + cj-309b B-1 candidate list wire (3c9bdbf, cj-style 265번째)
- **본 protocol**: cj-315 B-2 outreach execution prep wire (cj-style 278번째)
- **대상 운영자**: kjw
- **Pilot scope**: 5-10 SaaS 제조 스타트업, 8 weeks (2026-09-14 ~ 2026-11-09 KST), 무료

---

## §1 의도 + D-4 즉시 실행 항목

cj-309b B-1 candidate list wire (`3c9bdbf`) 의 8개 샘플 슬롯 (Tier 1 5 + Tier 2 3) 이 모두 `(operator network)` placeholder 상태. **D-2 (2026-09-12 Sat AM 10:00 KST) 1차 outreach 발송까지 2일**.

**D-4 ~ D-2 즉시 실행 5-step**:

| Step | 일자 | 액션 | 산출물 |
|---|---|---|---|
| **1** | **D-4 today (2026-09-10)** | Tier 1 슬롯 #1~#3 회사명 + contact 3건 확보 | candidate table §2 3행 채움 |
| **2** | **D-4 today (2026-09-10)** | Tier 1 슬롯 #4~#5 + Tier 2 슬롯 #6~#7 회사명 + contact 4건 확보 | candidate table §2 5행 + §3 2행 채움 |
| **3** | **D-3 (2026-09-11 Fri)** | Tier 2 슬롯 #8 회사명 + contact 1건 확보 + outreach email 1차 작성 8건 | candidate table §3 3행 채움 + email drafts 8건 |
| **4** | **D-2 AM (2026-09-12 Sat)** | **1차 outreach 8곳 동시 발송** (ko-KR AM 10:00 KST) + tracking 시작 | outreach tracker §4 update |
| **5** | **D-2 PM ~ D-0** | 1차 회신 확인 + 2차/3차 follow-up + W1 onboarding 일정 조율 | outreach tracker §4 update |

---

## §2 Tier 1 Ideal (5곳 목표) — D-4 contact 확보 protocol

각 슬롯별로 **구체적 discovery channel + 의사결정자 contact path** 가이드.

### Slot #1: 스마트팩토리 SaaS (Series A+, MRR >$100k)

**Discovery channels** (D-4 오전, 1시간):
1. **LinkedIn Sales Navigator** filter:
   - Title: "CFO" OR "VP Finance" OR "Head of Finance"
   - Industry: "Industrial Automation" OR "Smart Manufacturing" OR "SaaS"
   - Company size: 50-200
   - Geography: Seoul / Busan / Pangyo
   - Sort: 최근 30일 activity
2. **Crunchbase** filter:
   - Categories: SaaS, Manufacturing, Industrial Automation
   - Funding: Series A, last 12 months
   - Region: South Korea
3. **VC portfolio list**:
   - **SparkLabs** (한국 Series A+B heavy): https://sparklabs.co.kr/portfolio
   - **Primer** (한국 SaaS 특화): https://primer.saca.ai/portfolio
   - **Mashup Ventures** (SaaS + Manufacturing): https://mashupventures.kr/portfolio
   - **카운터포인트파트너스**: https://counterpoint.co.kr (한국 제조 vertical specialist)

**Decision-maker contact path**:
- 1차: LinkedIn connection request (300자 이내, vertical 매칭 1문장 + Pilot 멘션)
- 2차: connection 수락 후 DM (3문장, 15분 콜 제안)
- 3차: 콜 수락 → 15분 데모 + Pilot 참여 의사 확인
- 4차: 회신 시 → email follow-up with `docs/pilot-candidate-template.md` §5.1 cold outreach template

**Contact capture form**:
```
Slot #1 | 스마트팩토리 SaaS | 50-200명
회사명: ___________________
의사결정자: ___________________
Title: ____ (CFO / VP Finance / CEO)
Email: ____ (LinkedIn profile 에서 확인, public email 우선)
LinkedIn URL: ___________________
컨택 경로: □ warm intro (VC/accelerator) / □ LinkedIn / □ cold email
TAM 시그널: Series ___ MRR $___
Fit score: 1-5 (______)
상태: 🟡 D-4 contact 확보 중
```

### Slot #2: MES SaaS (Series A, MRR $50-100k)

**Discovery channels**:
1. **KOTRA** (한국贸易振興公社) startup 디렉토리: https://www.kotra.or.kr
2. **창업보육센터** alumni network: 판교/강남/부산 BI center
3. **D-Camp** (디캠프) alumni: https://www.dcamp.kr
4. **Google "MES SaaS Korea Series A"** 검색 → TechCrunch Korea / 블로터 기사 → 기사 언급 회사

**Decision-maker contact path**: Slot #1 동일

### Slot #3: ERP SaaS (제조) (Seed, MRR $20-50k)

**Discovery channels**:
1. **AWS SaaS Factory** Korea alumni: https://aws.amazon.com/ko/saas-factory
2. **NHN Cloud** SaaS 파트너 디렉토리
3. **더존 ERP marketplace** integrations: https://marketplace.doji.com
4. **경리나라** SaaS integrations: https://www.greennara.com

**Decision-maker contact path**: Slot #1 동일, 단 의사결정자 = **CEO** 우선 (Seed 단계는 CFO 없을 가능성)

### Slot #4: SCM/물류 SaaS (Series B+, MRR >$200k)

**Discovery channels**:
1. **CJ Logistics Ventures** portfolio: https://cjlventures.com
2. **롯데벤처스** portfolio (B2B logistics focus)
3. **한진** ICT 자회사 / 계열사 벤처 디렉토리
4. **SBS / KBS 스타트업 쇼** 출연 기업 list

**Decision-maker contact path**: Slot #1 동일

### Slot #5: QMS/품질 SaaS (Seed, MRR $20-50k)

**Discovery channels**:
1. **KS 표준원** 인증 SaaS list: https://www.ksa.or.kr
2. **한국품질경영협회** member directory
3. **TIPA** (대한민국정부발명진흥회) startup 디렉토리
4. **한국산업지능화협회** member companies

**Decision-maker contact path**: 의사결정자 = **COO** (Seed 단계, CFO 없을 가능성)

---

## §3 Tier 2 Fallback (3곳) — D-3~D-4 contact 확보 protocol

### Slot #6: HR-Tech (제조) (Bootstrap, MRR $10-20k)

**Discovery channels**:
1. **사람인** startup 채용 SaaS partnerships
2. **원티드** startup 디렉토리
3. **LinkedIn** Title filter: "People Operations" OR "HR Director" in Manufacturing
4. **원티드라이크** community: https://www.wanted.co.kr/community

**Decision-maker**: CEO (Bootstrap 단계)

### Slot #7: Fintech (제조 B2B) (Series A, MRR $30-50k)

**Discovery channels**:
1. **핀테크센터** (한국핀테크지원센터) alumni: https://www.kifc.kr
2. **토스** developer partners
3. **카카오페이** B2B partners
4. **뱅크샐러드** for Startups

**Decision-maker**: CFO

### Slot #8: InsurTech (제조) (Seed, MRR $15-30k)

**Discovery channels**:
1. **KB인베스트먼트** InsurTech portfolio
2. **삼성화재** C-Lab alumni
3. **현대해상** Innovation Lab
4. **DB손해보험** 핀테크 인큐베이팅 alumni

**Decision-maker**: VP Finance

---

## §4 Contact Verification Protocol (D-4 ~ D-2)

각 contact 확보 후 **verification 3-check**:

1. **Email verification**: `validate_email` 라이브러리 또는 Hunter.io / Apollo.io 로 email deliverability verify
   - Bounce rate < 5% 권장
   - Catch-all 도메인은 회신율 낮으므로 Tier 1 5곳에 우선 배치
2. **LinkedIn activity check**: 최근 30일 내 1회 이상 activity (post, comment, like) — inactive profile 은 outreach 응답률 5% 미만
3. **Decision-maker 권한 check**:
   - LinkedIn "Reports to" 또는 "Team size" 정보
   - 회사 website About / Leadership 페이지 cross-check
   - Recent funding announcement 에 CFO/VP Finance 언급 여부

**Verification 실패 시**: 즉시 Tier 3 wait-list (cj-301 보존, `docs/pilot-candidate-template.md` §3) 에서 차순위 후보로 교체.

---

## §5 Outreach Email 작성 protocol (D-3)

8개 contact 확보 완료 후, 각 슬롯별로 **`docs/pilot-candidate-template.md` §5.1 cold outreach template** 기반 personalized 작성:

### Personalization 4-fields (각 email 마다 필수):
```
[회사명]: 슬롯의 실제 회사명
[의사결정자명]: LinkedIn profile 의 실명
[Vertical]: 슬롯의 vertical (스마트팩토리 / MES / ERP / SCM / QMS / HR-Tech / Fintech / InsurTech)
[TAM 시그널]: 슬롯의 Series 단계 + MRR
```

### 예시 (Slot #1 placeholder → 실회사명 입력):
```
Subject: [Pilot] SaaS 제조 회계 AI 비용 분석 8주 무료 체험 - [회사명] [이름]님께

안녕하세요, [이름]님.

costmgr 팀의 kjw 입니다. 귀사 [회사명]에서 진행하시는 [스마트팩토리] 사업을 응원합니다.

귀사는 [Series A 단계의 MRR $100k+ SaaS 제조 솔루션]으로 빠른 성장 중이라 알고 있으며, 이 과정에서 회계 비용 분석의 자동화 니즈가 클 것으로 판단됩니다.

저희 costmgr 는 SaaS 제조 회사를 위한 AI 비용 분석 도구로, 다음 기능을 8주간 무료로 체험하실 수 있는 Pilot 프로그램을 운영합니다:

- CSV/PDF/Email 비용 분석 리포트 자동 생성
- 월별/분기별/연간 비용 추세 분석
- 예산 대비 실적 분석 (Budget vs Actual)
- Multi-tenant 격리 + 2FA + Audit log

Pilot 참여 시:
- 기간: 2026-09-14 ~ 2026-11-09 KST (8주)
- 비용: 무료
- W1 1:1 onboarding 미팅 (30분)
- W4 evaluation 미팅 (KPI 검증)
- W8 close-out 미팅

관심 있으시면 회신 부탁드립니다. 간단한 15분 콜로 상세 설명 드리겠습니다.

감사합니다.
kjw
costmgr | Pilot Program Lead
kjw@bizup.io
```

### 2차/3차 follow-up (회신 없을 시):
- **2차**: `docs/pilot-candidate-template.md` §5.2 verbatim (D+3)
- **3차**: `docs/pilot-candidate-template.md` §5.3 verbatim (D+7, warm intro 우선)

---

## §6 Outreach Tracker (D-2 ~ D-0)

`docs/pilot-candidate-template.md` §4 tracker 의 각 슬롯에 다음 컬럼 추가:

| 컬럼 | 설명 | D-2 | D-1 | D-0 |
|---|---|---|---|---|
| 1차 발송 | email 발송 일시 (ko-KR AM 10:00) | ○ | ○ | ○ |
| 1차 회신 | 회신 수신 일시 | pending | pending / ✓ | ✓ |
| 2차 follow-up | D+3 follow-up 발송 일시 | — | ○ | ○ |
| 3차 follow-up | D+7 follow-up 발송 일시 | — | — | ○ |
| 15분 콜 | 콜 일시 + 참석자 | — | — | ✓ |
| W1 onboarding | onboarding 미팅 일시 | — | — | ✓ |
| 상태 코드 | ⚪ / 🟡 / 🟢 / ✅ / ❌ / 🔵 | 🟡 | 🟡 / 🟢 | 🟢 / ✅ |

---

## §7 1차 outreach 발송 execution checklist (D-2 Sat AM 09:30 ~ 10:30 KST)

```
09:30 KST — operator (kjw) 최종 email 8건 review (오타, personalization 정확성)
09:45 KST — 발송 tooling 선택:
         A) Gmail SMTP (대량 발송 100/day, 스팸 분류 위험)
         B) Resend API (Bearer auth, 100/day 무료 tier, 권장) — cj-305b swap
         C) Postmark (100/mo sandbox, 부적합)
09:50 KST — Resend API key verify (D-2 deploy-blocking operator action §6.2)
10:00 KST — 8곳 동시 발송 (개별 수신자명 정확성 확인)
10:05 KST — 발송 audit log verify (Resend dashboard → 8 messages → delivery queued)
10:15 KST — outreach tracker §4 8행 update (1차 발송 일시 = 2026-09-12 10:00 KST)
10:30 KST — 회신 monitor 시작 (Gmail inbox / Resend inbound webhook)
```

---

## §8 risk profile + honestly DEFER 보존

**risk profile: HIGH** — 2일 안에 8 contact 확보 + 8 email 작성 + 1차 발송. 동시 진행.

**Mitigation**:
- **Tier 1 5곳 우선** 확보 (오늘 D-4 ~ D-3) — Tier 2 3곳은 D-3 ~ D-2 sliding 가능
- **Tier 3 wait-list** fallback 즉시 가능 (`docs/pilot-candidate-template.md` §3)
- **2차/3차 follow-up** = D+3, D+7 → 본 outreach prep scope 외, honestly DEFER

**honestly DEFER 결정 wire 보존**:
- 2차/3차 follow-up 발송 = post-D-2 honestly DEFER (cj-301 결정 wire 보존)
- 회신 추적 + W1 onboarding 일정 조율 = post-D-1 honestly DEFER
- W4 evaluation 미팅 agenda + W8 close-out 미팅 agenda = cj-315 follow-up sprint (or post-W1)
- Tier 3 wait-list 확장 candidate = post-pilot expansion 결정 wire 보존 (cj-301)

---

## §9 Cross-references

- `docs/pilot-candidate-template.md` — 8 slot templates + §5 outreach email 3종 + §4 tracker
- `docs/pilot-launch-runbook.md` — D-4 → D-0 timeline (cj-315 wire 신규 EXTENSION) + Resend migration (cj-305b swap retroactive correction)
- `_bmad-output/implementation-artifacts/phase-30-pilot-candidate-list-b1-wire-2026-09-09.md` — cj-309b B-1 결정 wire (cj-style 265번째)
- `_bmad-output/implementation-artifacts/phase-30-pilot-outreach-prep-2026-09-07.md` — cj-301 pilot prep (3 outreach templates + KPI framework)
- `memory/handoff-2026-09-10-cj-315-pilot-outreach-exec-prep-wire-done.md` — 본 sprint handoff

---

## §10 결정 wire 일자 + 다음 단계

**결정 wire 일자**: 2026-09-10 (KST, **D-4 = 4일 카운트다운 시작**)

**다음 옵션 (운전자 결정)**:
- **즉시 실행**: §1 Step 1~2 (Tier 1 5곳 + Tier 2 2곳 contact 확보, D-4 today)
- **D-3 (Fri)**: §1 Step 3 (Tier 2 마지막 1곳 + outreach email 8건 작성)
- **D-2 (Sat AM 10:00)**: §1 Step 4 (1차 outreach 발송)
- **D-2 PM ~ D-0**: §1 Step 5 (회신 추적 + follow-up + W1 onboarding 일정 조율)

**cj-style 278번째 정직 회복 보존**: 본 protocol 은 cj-309b 의 샘플 슬롯 placeholder 를 operator network 기반 실데이터로 채우는 **B-2 execution prep 결정 wire**. 실제 회사명 + 실제 contact = **운전자 B-1 결정 영역** (cj-309b honestly DEFER 보존 verbatim mirror).
