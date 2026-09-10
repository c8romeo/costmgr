---
name: cj-315-pilot-outreach-exec-prep-wire-done
description: cj-315 Pilot outreach execution prep (B-2) wire (cj-style 278번째) — 5-step protocol + discovery channels + D-4→D-0 timeline refresh + Postmark→Resend swap (3 NEW + 1 MODIFIED + 2 NEW meta + 2 MODIFIED meta, 7 files)
metadata:
  type: project
---

# cj-315 Pilot outreach execution prep (B-2) wire — Handoff

> **Sprint**: cj-315 Pilot outreach execution prep (B-2) wire (cj-style 278번째)
> **Date**: 2026-09-10 KST (D-4, Pilot W1 launch D-day 2026-09-14 KST)
> **Territory**: Phase 30 Pilot W1 B-2 Outreach Execution Prep
> **Author**: Claude (operator = kjw)
> **Sprint form**: wire (cj-style 278th, post cj-314 wire 4 277th 결정 wire 진입)
> **commit**: 단일 sprint (예정 commit hash)

---

## §1 의도 분석 — 옵션 (a) cj-309b B-1 outreach 진입 결정 wire

### 사용자 결정 wire (2026-09-10 KST)
- 옵션 (a, RECOMMENDED next) **cj-309b B-1 Pilot candidate outreach** 진입 (운전자 결정)
- cj-style feedback `prioritize-mvp-hardening-before-deploy` (2026-09-07) verbatim mirror
- 비용 $0 + MVP hardening 우선 (2026-09-10 결정 wire) — B-2 outreach prep 은 docs-only 이므로 비용 $0
- 4-day countdown → operator 즉시 활용 가능한 실행 가능한 protocol 필요

### cj-309b B-1 wire 의 honestly DEFER 보존 verbatim mirror
- 실제 candidate 8개 회사명 = **운전자 B-1 결정 영역** (operator network 기반). cj-309b 가 8개 슬롯 placeholder 제공
- 본 sprint 는 **B-2 execution prep** (= 샘플 placeholder → operator 가 즉시 채울 수 있는 discovery protocol + outreach execution checklist + refreshed launch runbook 결정 wire only)

### cj-314 wire 4 meta close (`6756d1e`) 직후 즉시 진입
- Phase A 3/3 + Phase B 3/3 ALL CLOSED → **코드 사이드 병목 해소**
- **D-4 시점 병목 = 운영자 액션** (cj-309b B-1 outreach D-2 발송 + deploy-blocking 4건)

---

## §2 cj-315 wire scope = 5-step protocol + 3 신규 docs

### 파일 구성 (7 files, docs-only atomic single sprint)

| # | File | 종류 | 변경량 | 역할 |
|---|---|---|---|---|
| 1 | `docs/pilot-candidate-discovery-protocol.md` | NEW | ~285 LOC | D-4 즉시 실행 5-step protocol + Tier 1/2 discovery channels per slot + contact verification + outreach email 작성 + outreach tracker + D-2 AM 발송 execution checklist |
| 2 | `docs/pilot-launch-runbook.md` | MODIFIED | +30 LOC | Postmark → Resend swap retroactive correction + D-4 to D-0 timeline refresh + Sentry post-W1 honestly DEFER + §6.5 W4 evaluation + W8 close-out meeting agenda 신규 + Risk #9 Tier 1/2 contact 확보 부재 risk + §10 cross-references 확장 + §12 결정 wire 일자 update |
| 3 | `_bmad-output/implementation-artifacts/commit-msg-cj-315.txt` | NEW | ~80 LOC | 본 wire commit message |
| 4 | `memory/handoff-2026-09-10-cj-315-pilot-outreach-exec-prep-wire-done.md` | NEW | ~220 LOC | 본 handoff 8-section §1~§8 |
| 5 | `_bmad-output/implementation-artifacts/sprint-status.yaml` | MODIFIED | +8/-0 | v4.94 → **v4.95 EXTENSION** A739 + last_updated_note_v4_95 |
| 6 | `memory/MEMORY.md` | MODIFIED | +16/-1 | cj-315 hook + Active sprint state EXTENSION (575 → 591 lines) |

### cj-315 5-step protocol (operator D-4 ~ D-2 즉시 실행)

| Step | 일자 | Action | 산출물 |
|---|---|---|---|
| 1 | D-4 today (2026-09-10) | Tier 1 #1~#3 회사명 + contact 3건 확보 | candidate table §2 3행 채움 |
| 2 | D-4 today (2026-09-10) | Tier 1 #4~#5 + Tier 2 #6~#7 회사명 + contact 4건 확보 | candidate table §2 5행 + §3 2행 채움 |
| 3 | D-3 (2026-09-11 Fri) | Tier 2 #8 회사명 + contact 1건 확보 + outreach email 1차 작성 8건 | candidate table §3 3행 채움 + email drafts 8건 |
| 4 | D-2 AM (2026-09-12 Sat 10:00 KST) | **1차 outreach 8곳 동시 발송** (Resend API Bearer auth) | outreach tracker §4 update |
| 5 | D-2 PM ~ D-0 | 1차 회신 확인 + 2차/3차 follow-up + W1 onboarding 일정 조율 | outreach tracker §4 update |

---

## §3 verify gate 결과 (cj-315 wire 의 본질)

| 검증 범위 | 결과 |
|---|---|
| `docs/pilot-candidate-discovery-protocol.md` NEW | **285 LOC**, 10-section §1~§10 |
| `docs/pilot-launch-runbook.md` MODIFIED | **7-section refresh** (header + §1 + §2.4 + §2.5 + §5.2 + §6 + §6.5 + §7 + §9 + §10 + §12) |
| **Postmark reference count** | BEFORE 12회 → **AFTER 0회** (전량 Resend 로 swap, cj-305b 결정 wire 정합) |
| **Day 0-7 timeline** | BEFORE 7일 카운트다운 → **AFTER D-4 to D-0 4일 카운트다운** (cj-315 wire refresh) |
| **Sentry reference** | BEFORE 결정 wire → **AFTER post-W1 honestly DEFER** (cj-305 4-service minimal viable 결정 wire 보존) |
| **W4 + W8 meeting agenda** | BEFORE 부재 → **AFTER §6.5 신규 EXTENSION** (W4 45분 + W8 60분) |
| **Risk register** | BEFORE 8 risks → **AFTER 9 risks** (Risk #9 Tier 1/2 contact 확보 부재 risk 신규 추가) |
| **sprint-status.yaml** | append only A739 + last_updated_note_v4_95 |
| **MEMORY.md** | 575 → 591 lines (+16) |

**runtime**: source code 변경 0건 / dev_seed 변경 0건 / ci.yml 변경 0건 / alembic 변경 0건 / 37 pins unchanged / 14 job matrix unchanged / PRD v7.0 §F/§M/§R unchanged / capability matrix v1.54 EXTENSION preserved / audit actions EXTENSION preserved / AD-14 stack pin EXTENSION preserved.

---

## §4 결정 wire 보존 (cj-301~cj-314 wire 결정 wire 그대로)

- Pilot W1 D-day 2026-09-14 KST / cj-309b B-1 / **cj-315 B-2 (본 sprint)** / Resend (OQ-EPIC30+-2 v2 cj-305b swap) / cj-307 aal1 / cj-305 4-service minimal viable / cj-304 4 critical gaps / cj-300 APScheduler KST / capability matrix v1.54 EXTENSION / audit_action EXTENSION / AD-14 stack pin EXTENSION

**51/51 cumulative 결정 wire 보존** = 50 (cj-282~cj-314 wire 4) + **NEW 51번째 cj-315 B-2 outreach exec prep** 결정 wire 진입.

### cj-307 carryover risk-prioritized triage 진행 현황

| Phase | Item | Sprint | Commit | 상태 |
|---|---|---|---|---|
| A | item 1 | cj-316 FastAPI lifespan | `1281ca5` | ✅ CLOSED |
| A | item 2 | cj-317 alembic 0037 | `99a7343` | ✅ CLOSED |
| A | item 3 | cj-314 wire 1 capability matrix drift | `cca03c2` | ✅ CLOSED |
| B | item 1 | cj-314 wire 2 Phase 30 + Phase 5 + Phase 3 6 fixes | `4435e2d` | ✅ CLOSED |
| B | item 2 | cj-314 wire 3 Phase 8 ESLint/SLO/SLI 8 fixes | `34e92aa` | ✅ CLOSED |
| B | item 3 | cj-314 wire 4 Phase 5/9/16/26 5 fixes | `aacb12c` | ✅ CLOSED |
| C | — | `test_phase_10_*` SLO family 32건 | — | honestly DEFER post-W1 |

**Phase A ALL CLOSED (3/3) + Phase B ALL CLOSED (3/3) → Phase B 잔여 0건**

---

## §5 CR 11-3 honest-DEFER 278번째

- cj-315 B-2 outreach exec prep wire 는 **"operator 즉시 활용 가능한 5-step protocol + D-4 → D-0 timeline refresh + Postmark → Resend retroactive correction"** 을 본 sprint 의 본질로 삼음
- **정직 회복 (cj-style 257th + 267th + 270th + 273rd + 276th + 277th verbatim mirror)**:
  - ① **cj-309b honestly DEFER 보존 verbatim mirror**: 8개 슬롯 `(operator network)` placeholder → 본 sprint 는 execution prep 결정 wire only. 실제 회사명 = operator network 결정 영역
  - ② **cj-305b Postmark → Resend retroactive correction**: 기존 `docs/pilot-launch-runbook.md` 의 Postmark reference 12회를 전량 Resend 로 swap. 결정 wire 일관성 회복
  - ③ **cj-305 4-service minimal viable 결정 wire 보존**: Sentry Team post-W1 honestly DEFER. 비용 $0 EXTENSION 정책 정합
- chain: cj-282 (220번째) → ... → cj-314 wire 4 Phase B item 3 5 fixes (277번째) → **cj-315 B-2 outreach execution prep (278번째, 본 sprint)** 종합 51 sprints 정직 회복

---

## §6 Honestly DEFER 결정 wire 보존

- **실제 candidate 8개 회사명 + contact** = 운전자 B-1 결정 영역 (cj-309b 보존 verbatim)
- **outreach 발송** = D-2 (2026-09-12 KST) 결정 wire 보류 (operator work hours)
- **2차/3차 follow-up** = post-D-2 결정 wire 보류
- **회신 추적 + W1 onboarding 일정 조율** = post-D-1 결정 wire 보류
- **W4 evaluation + W8 close-out 미팅** = 회신 + onboarding 후 결정 wire 보류 (cj-315 §6.5 framework 만 제공)
- **Tier 3 wait-list 확장** = post-pilot expansion 결정 wire 보존 (cj-301)
- **PRD v2 EXTENSION** = W8 close-out 후 결정 wire 보존 (cj-301)
- **Epic 29+ spec implementation chain** = pilot feedback 후 결정 wire 보존 (cj-301)
- **정식 pricing 결정** = pilot 종료 후 결정 wire 보존 (cj-301)
- **Sentry Team + Custom DNS + 비용 발생 항목 모두** = launch day 결정 wire 보류 (cj-305)
- **cj-312 close-out retro + cj-313 close-out retro** = 결정 wire 보존
- **`epics.md` 미커밋 대형 변경 triage** = 별도 sprint
- **운영자 액션 4건 OPEN (deploy-blocking)** = RESEND_API_KEY 캡처 + SUPABASE_JWT_SECRET 캡처 + Supabase Auth dashboard live verify + live signup smoke test

---

## §7 결정 보류 (cj-315 종료 후, 운전자 결정)

**D-4 시점 최우선 = 옵션 (a) operator 즉시 실행**. 옵션 (a) 가 곧 cj-315 의 본질 실행.

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

## §8 Cross-references + CR 11-3 정직 회복

### Cross-references
- cj-314 wire 4 (`aacb12c`, cj-style 277번째) — Phase B item 3 5 fixes CLOSED
- cj-314 wire 4 meta close (`6756d1e`, 2026-09-10) — sprint-status v4.94 + MEMORY.md wire 4 hook + handoff
- cj-309b B-1 candidate list (`3c9bdbf`, cj-style 265번째)
- cj-305b Resend migration (`53b8bbf`, cj-style 256번째) — Postmark → Resend swap
- cj-305 production deploy day-1 wire (`b732153`, cj-style 254번째) — 4-service minimal viable
- cj-307 auth-callback aal1 fix (`a1cb7ad`, cj-style 261번째)
- cj-304 prod deploy prep (`1fdb67d`, cj-style 252번째) — 4 critical gaps fix + Pilot tenant CLI
- cj-301 pilot prep (`23ee783`, cj-style 303번째)
- `docs/pilot-candidate-template.md` (184 LOC) — 8 slot templates + §5 outreach email 3종 + §4 tracker
- `docs/pilot-launch-runbook.md` (refreshed 2026-09-10)
- `docs/pilot-candidate-discovery-protocol.md` (NEW 285 LOC) — 본 sprint 신규
- `docs/deployment-account-setup.md` (cj-305 wire, 4-service minimal viable + Resend §6.2)

### CR 11-3 정직 회복 요약
본 sprint 의 정직 회복은 **"operator 결정 wire 영역을 침범하지 않으면서 즉시 활용 가능한 protocol + 결정 wire 정합성 회복"** 이다. cj-309b 가 `(operator network)` placeholder 로 결정한 영역을 그대로 보존하면서, **discovery channels + verification protocol + outreach execution checklist** 의 5-step 으로 operator 가 2일 안에 실행 가능하도록 보강했다. 동시에 cj-305b 의 Postmark → Resend swap + cj-305 의 Sentry post-W1 honestly DEFER 결정 wire 가 기존 runbook 에 정합하지 않던 상태를 retroactive correction 으로 일관성 회복.
