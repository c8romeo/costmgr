---
title: "cj-315 Pilot outreach execution prep (B-2) wire entry — cj-style 278번째"
type: sprint-entry
date: 2026-09-10
sprint_key: phase-30-pilot-outreach-exec-prep-wire
status: in_progress
cj_style_entry_point: 278
baseline_commit: 6756d1e
territory: Phase 30 Pilot W1 B-2 Outreach Execution Prep
sprint_type: wire (docs-only atomic)
CR: 11-3 honest-DEFER 278번째
---

# cj-315 Pilot outreach execution prep (B-2) wire entry (cj-style 278번째)

**일자**: 2026-09-10 (KST, **D-4 = D-day 2026-09-14 까지 4일**)
**territory**: Phase 30 Pilot W1 B-2 Outreach Execution Prep
**sprint type**: wire (docs-only atomic, cj-309b B-1 wire 결정 wire 보존)
**CR 11-3 honest-DEFER 278번째**

---

## §1 의도 + 진입 결정 wire

운전자 옵션 (a) **cj-309b B-1 Pilot candidate outreach** 진입 (c8rom, 2026-09-10 KST, D-4). cj-309b B-1 candidate list wire (`3c9bdbf`, cj-style 265번째) 의 8개 샘플 슬롯 (Tier 1 5 + Tier 2 3) 이 모두 `(operator network)` placeholder 상태. **D-2 (2026-09-12 Sat AM 10:00 KST) 1차 outreach 발송까지 2일**.

본 entry 는 **B-2 outreach execution prep wire 결정 wire 진입** = operator (kjw) 가 즉시 활용 가능한 operator-facing 자료를 보강하여 D-4 ~ D-2 5-step protocol 을 실행 가능하게 함.

### 사용자 결정 wire (2026-09-10 KST)
- 옵션 (a, RECOMMENDED next) **cj-309b B-1 Pilot candidate outreach 진입**
- cj-style feedback `prioritize-mvp-hardening-before-deploy` (2026-09-07) verbatim mirror
- 비용 $0 + MVP hardening 우선 (2026-09-10 결정 wire) — B-2 outreach prep 은 docs-only 이므로 비용 $0
- 4-day countdown → operator 즉시 활용 가능한 실행 가능한 protocol 필요

### cj-309b B-1 wire 의 honestly DEFER 보존 verbatim mirror
- **honest DEFER 보존**: 실제 candidate 8개 회사명 = **운전자 B-1 결정 영역** (operator network 기반). 본 sprint 는 **B-2 execution prep** (= 샘플 placeholder → operator 가 즉시 채울 수 있는 discovery protocol + outreach execution checklist + refreshed launch runbook 결정 wire only)
- **honest DEFER 보존**: outreach 발송 = D-2 (2026-09-12 KST) 결정 wire 보류 (operator work hours)
- **honest DEFER 보존**: 회신 추적 + 2차/3차 follow-up = post-D-2 결정 wire 보류

---

## §2 cj-315 wire scope = 5-step protocol + 3 신규 docs

### cj-309b 의 8개 샘플 슬롯 → operator 가 즉시 채울 수 있는 B-2 execution prep 결정 wire

**Tier 1 Ideal 5곳**: 스마트팩토리 SaaS / MES SaaS / ERP SaaS (제조) / SCM/물류 SaaS / QMS/품질 SaaS
**Tier 2 Fallback 3곳**: HR-Tech (제조) / Fintech (제조 B2B) / InsurTech (제조)

**B-2 execution prep 결정 wire (operator-facing) = 4 신규 + 1 MODIFIED**:

| # | File | 종류 | 변경량 | 역할 |
|---|---|---|---|---|
| 1 | `docs/pilot-candidate-discovery-protocol.md` | NEW | ~285 LOC | §1 D-4 즉시 실행 5-step / §2 Tier 1 5곳 discovery channels (LinkedIn Sales Navigator + Crunchbase + VC portfolio + accelerator alumni) / §3 Tier 2 3곳 discovery / §4 contact verification / §5 outreach email 작성 / §6 outreach tracker / §7 D-2 AM 발송 execution checklist / §8 risk / §9 cross-ref / §10 결정 wire 일자 |
| 2 | `docs/pilot-launch-runbook.md` | MODIFIED | +30 LOC | (1) Postmark → **Resend swap** retroactive correction (cj-305b 결정 wire 신규 active) (2) Day 0-7 timeline → **D-4 to D-0 4일 카운트다운** refresh (3) Sentry post-W1 honestly DEFER (cj-305 4-service minimal viable 결정 wire) (4) §6.5 **W4 evaluation + W8 close-out meeting agenda** 신규 EXTENSION (5) §7 Risk #9 Tier 1/2 contact 확보 부재 risk 신규 추가 (6) §10 cross-references 확장 (7) §12 결정 wire 일자 update |
| 3 | `_bmad-output/implementation-artifacts/commit-msg-cj-315.txt` | NEW | ~80 LOC | 본 wire commit message (rationale 5종 + verify gate + 결정 wire 보존 + honestly DEFER + 결정 보류) |
| 4 | `memory/handoff-2026-09-10-cj-315-pilot-outreach-exec-prep-wire-done.md` | NEW | ~220 LOC | 8-section handoff (§1 의도 / §2 5-step protocol / §3 verify gate / §4 결정 wire 보존 / §5 CR 11-3 278번째 / §6 honestly DEFER / §7 결정 보류 / §8 cross-ref) |
| 5 | `_bmad-output/implementation-artifacts/sprint-status.yaml` | MODIFIED | +8/-0 | v4.94 → **v4.95 EXTENSION** (A739 + last_updated_note_v4_95) |
| 6 | `memory/MEMORY.md` | MODIFIED | +16/-1 | cj-315 hook + Active sprint state EXTENSION (575 → 591 lines) |

= **2 NEW content + 1 MODIFIED content + 2 NEW meta + 2 MODIFIED meta = 7 files docs-only atomic single sprint**

---

## §3 cj-315 5-step protocol (operator D-4 ~ D-2 즉시 실행)

### Step 1: D-4 today (2026-09-10) Tier 1 #1~#3 contact 확보
- LinkedIn Sales Navigator filter: "CFO" OR "VP Finance" + Industry "Industrial Automation" + Seoul/Busan/Pangyo
- Crunchbase filter: SaaS + Manufacturing + Series A last 12 months + South Korea
- VC portfolio list: SparkLabs / Primer / Mashup Ventures / 카운터포인트파트너스
- 의사결정자 contact path: LinkedIn connection → DM → 15분 콜 → email follow-up
- 산출물: candidate table §2 3행 채움 (회사명 + 의사결정자 + Email + LinkedIn URL + 컨택 경로 + TAM 시그널 + Fit score)

### Step 2: D-4 today (2026-09-10) Tier 1 #4~#5 + Tier 2 #6~#7 contact 확보
- Tier 1 #4 SCM/물류 SaaS: CJ Logistics Ventures + 롯데벤처스 + 한진 ICT 자회사
- Tier 1 #5 QMS/품질 SaaS: KS 표준원 인증 list + 한국품질경영협회 + TIPA + 한국산업지능화협회
- Tier 2 #6 HR-Tech (제조): 사람인 startup 채용 SaaS partnerships + 원티드 + LinkedIn Title filter
- Tier 2 #7 Fintech (제조 B2B): 핀테크센터 + 토스 developer partners + 카카오페이 B2B
- 산출물: candidate table §2 5행 + §3 2행 채움

### Step 3: D-3 (2026-09-11 Fri) Tier 2 #8 + outreach email 작성
- Tier 2 #8 InsurTech (제조): KB인베스트먼트 + 삼성화재 C-Lab + 현대해상 Innovation Lab + DB손해보험 핀테크 인큐베이팅
- outreach email 1차 작성 8건: `docs/pilot-candidate-template.md` §5.1 cold outreach template 기반 personalization 4-fields ([회사명] [의사결정자명] [Vertical] [TAM 시그널])
- 산출물: candidate table §3 3행 채움 + email drafts 8건

### Step 4: D-2 AM (2026-09-12 Sat 10:00 KST) 1차 outreach 8곳 동시 발송
- 09:30 KST: operator (kjw) 최종 email 8건 review (오타 + personalization 정확성)
- 09:45 KST: 발송 tooling 선택 = **Resend API (Bearer auth)** 결정 wire (cj-305b swap 신규 active)
- 09:50 KST: Resend API key verify (D-2 deploy-blocking operator action §6.2)
- 10:00 KST: 8곳 동시 발송
- 10:05 KST: 발송 audit log verify (Resend dashboard → 8 messages → delivery queued)
- 10:15 KST: outreach tracker §4 8행 update (1차 발송 일시 = 2026-09-12 10:00 KST)
- 10:30 KST: 회신 monitor 시작 (Gmail inbox / Resend inbound webhook)

### Step 5: D-2 PM ~ D-0 (2026-09-12 PM ~ 2026-09-14 Mon) follow-up + W1 onboarding 일정 조율
- 1차 회신 확인 (회신 온 곳 → 15분 콜 스케줄링)
- 2차 follow-up 준비 (D+3, 회신 없는 곳만, `docs/pilot-candidate-template.md` §5.2 verbatim)
- 3차 follow-up 준비 (D+7, warm intro 우선, `docs/pilot-candidate-template.md` §5.3 verbatim)
- W1 onboarding 일정 조율 (회신 온 곳부터, `docs/pilot-launch-runbook.md` §6 W1 onboarding run-of-show)

---

## §4 rationale 5종 (cj-style 278번째 결정 wire 진입)

1. **D-4 즉시 실행 필요**: 1차 outreach D-2 AM 발송까지 2일. operator 가 B-2 execution prep 없이 샘플 placeholder 상태로 들어가면 **contact 확보 + email 작성 시간 부족**. 본 protocol 은 5-step 으로 시간 분할 → **각 step 별 명확한 산출물 + decision-maker contact path 결정 wire**.
2. **cj-309b B-1 wire 결정 wire 보존 verbatim mirror**: B-1 candidate list wire 의 8개 샘플 슬롯이 `(operator network)` placeholder 인 상태에서, B-2 execution prep 이 없으면 operator 가 8개 슬롯을 어떤 channel 로 확보해야 하는지 모호. 본 protocol 은 §2 + §3 에서 각 슬롯별로 **LinkedIn Sales Navigator filter + Crunchbase filter + VC portfolio list + accelerator alumni** 4-channel 결정 wire.
3. **cj-305b Postmark → Resend swap retroactive correction**: 기존 `docs/pilot-launch-runbook.md` 의 Postmark reference (Postmark sandbox 100/mo + sender verification 1-3 영업일) 가 cj-305b swap 결정 wire 와 정합하지 않음. 본 wire 의 §2.5 / §5.2 / §6 / §7 모두 **Resend HTTP API (Bearer auth, 3,000/mo + 100/day, 즉시 verify)** 로 refresh → 결정 wire 일관성 회복.
4. **cj-305 4-service minimal viable 결정 wire 보존**: 기존 runbook 의 Sentry Team ($26/월) 은 cj-305 결정 wire 에 따라 **post-W1 honestly DEFER**. 본 wire 의 §2.4 + §9 결정 wire 정합 → 비용 $0 EXTENSION 정책 보존.
5. **Pilot W1 launch D-day readiness (D-4)**: D-2 outreach 발송 = **deploy-blocking critical path**. contact 확보 부재 시 Tier 1 5곳 회신 0 → W1 onboarding tenant 0건 → Pilot launch 의 의미 상실. 본 protocol + tracking sheet + risk #9 = **risk-prioritized triage** 결정 wire.

---

## §5 verify gate 결과 (cj-315 wire 의 본질)

| 검증 범위 | 결과 |
|---|---|
| `docs/pilot-candidate-discovery-protocol.md` NEW | 285 LOC, 10-section §1~§10 |
| `docs/pilot-launch-runbook.md` MODIFIED | 7-section refresh (header + §1 + §2.4 + §2.5 + §5.2 + §6 + §6.5 + §7 + §9 + §10 + §12) |
| Postmark reference count | BEFORE: 12회 / AFTER: 0회 (전량 Resend 로 swap) |
| Day 0-7 timeline reference | BEFORE: 7일 카운트다운 / AFTER: **D-4 to D-0 4일 카운트다운** |
| Sentry reference | BEFORE: 결정 wire / AFTER: **post-W1 honestly DEFER (cj-305 결정 wire 보존)** |
| W4 + W8 meeting agenda | BEFORE: 부재 / AFTER: **§6.5 신규 EXTENSION** (W4 45분 + W8 60분) |
| Risk register | BEFORE: 8 risks / AFTER: **9 risks (Risk #9 Tier 1/2 contact 확보 부재 신규 추가)** |
| sprint-status.yaml A739 + last_updated_note_v4_95 | append only |
| MEMORY.md hook + Active sprint state EXTENSION | 575 → 591 lines |

**runtime**: source code 변경 0건 / dev_seed 변경 0건 / ci.yml 변경 0건 / alembic 변경 0건 / 37 pins unchanged / 14 job matrix unchanged / PRD v7.0 §F/§M/§R unchanged / capability matrix v1.54 EXTENSION preserved / audit actions EXTENSION preserved.

---

## §6 결정 wire 보존 (cj-301~cj-314 wire 결정 wire 그대로)

- Pilot W1 D-day 2026-09-14 KST / cj-309b B-1 / **cj-315 B-2 (본 sprint)** / Resend (OQ-EPIC30+-2 v2 cj-305b swap) / cj-307 aal1 / cj-305 4-service minimal viable / cj-304 4 critical gaps / cj-300 APScheduler KST / capability matrix v1.54 EXTENSION / audit_action EXTENSION / AD-14 stack pin EXTENSION

**51/51 cumulative 결정 wire 보존** = 50 (cj-282~cj-314 wire 4) + **NEW 51번째 cj-315 B-2 outreach exec prep** 결정 wire 진입.

---

## §7 honestly DEFER 결정 wire 보존

- **실제 candidate 8개 회사명 + contact** = 운전자 B-1 결정 영역 (cj-309b 보존 verbatim)
- **outreach 발송** = D-2 (2026-09-12 KST) 결정 wire 보류 (operator work hours)
- **2차/3차 follow-up** = post-D-2 결정 wire 보류
- **회신 추적 + W1 onboarding 일정 조율** = post-D-1 결정 wire 보류
- **W4 evaluation + W8 close-out 미팅** = 회신 + onboarding 후 결정 wire 보류 (cj-315 §6.5 framework 만 제공)
- **Tier 3 wait-list 확장** = post-pilot expansion 결정 wire 보존 (cj-301)
- **PRD v2 EXTENSION** = W8 close-out 후 결정 wire 보존 (cj-301)
- **Epic 29+ spec implementation chain** = pilot feedback 후 결정 wire 보존 (cj-301)
- **정식 pricing 결정** = pilot 종료 후 결정 wire 보존 (cj-301)
- **Sentry Team + Custom DNS + 비용 발생 항목 모두** = launch day 결정 wire 보류 (cj-305 결정)
- **cj-312 close-out retro + cj-313 close-out retro** = 결정 wire 보존
- **`epics.md` 미커밋 대형 변경 triage** = 별도 sprint
- **운영자 액션 4건 OPEN (deploy-blocking)** = RESEND_API_KEY 캡처 + SUPABASE_JWT_SECRET 캡처 + Supabase Auth dashboard live verify + live signup smoke test (cj-309 결정 wire 보존)

---

## §8 결정 보류 (cj-315 종료 후, 운전자 결정)

① 옵션 (a, RECOMMENDED next) **operator 즉시 실행** — D-4 today 의 Step 1~2 (Tier 1 5곳 + Tier 2 2곳 contact 확보)
② 옵션 (b) **cj-309b B-1 retroactive correction** — cj-309b 의 "(operator network)" 8개 placeholder 를 Tier 1/2 슬롯별로 actual company name 입력 (운전자 network 결정)
③ 옵션 (c) **운영자 액션 4건 실행** — RESEND_API_KEY + SUPABASE_JWT_SECRET 캡처 + Supabase Auth live verify + signup smoke test (deploy-blocking)
④ 옵션 (d) **cj-313 close-out retro** (~30min, docs-only)
⑤ 옵션 (e) **cj-312 close-out retro** (~30min, docs-only)
⑥ 옵션 (f) **PRD v2 EXTENSION** (W8 close-out 후)
⑦ 옵션 (g) **`epics.md` 미커밋 대형 변경 triage** (별도 sprint)
⑧ 옵션 (h) **cj-314 wire 5 (Phase C 진입)** — `test_phase_10_*` 32건, ~2-3h, post-W1 honestly DEFER 권장 (LOW RISK)

**결정 wire 일자**: 2026-09-10 (KST, D-4, Pilot W1 launch D-day 2026-09-14 KST)

---

## §9 Cross-references

- cj-314 wire 4 (`aacb12c`, cj-style 277번째) — Phase B item 3 5 fixes CLOSED
- cj-314 wire 4 meta close (`6756d1e`, 2026-09-10) — sprint-status v4.94 + MEMORY.md wire 4 hook + handoff
- cj-309b B-1 candidate list (`3c9bdbf`, cj-style 265번째)
- cj-305b Resend migration (`53b8bbf`, cj-style 256번째) — Postmark → Resend swap
- cj-305 production deploy day-1 wire (`b732153`, cj-style 254번째) — 4-service minimal viable
- cj-307 auth-callback aal1 fix (`a1cb7ad`, cj-style 261번째)
- cj-304 prod deploy prep (`1fdb67d`, cj-style 252번째) — 4 critical gaps fix + Pilot tenant CLI
- cj-301 pilot prep (`23ee783`, cj-style 303번째 — outdated counter, cj-style chain reset)
- `docs/pilot-candidate-template.md` (184 LOC) — 8 slot templates + §5 outreach email 3종 + §4 tracker
- `docs/pilot-launch-runbook.md` (refreshed, 2026-09-10)
- `docs/deployment-account-setup.md` (cj-305 wire, 4-service minimal viable + Resend §6.2)

---

## §10 결정 wire 일자

2026-09-10 (KST, D-4, Pilot W1 launch D-day 2026-09-14 KST).
