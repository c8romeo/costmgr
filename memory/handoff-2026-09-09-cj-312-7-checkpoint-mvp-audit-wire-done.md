# cj-312 7-Checkpoint MVP Audit Wire — Handoff

> **Sprint**: cj-312 7-Checkpoint MVP Audit Wire (cj-style 269번째)
> **Date**: 2026-09-09 KST (D-5)
> **Status**: ✅ **CLOSED ✅ HONEST** (wire form, sprint-status v4.85 → v4.86 EXTENSION)
> **Next**: cj-313 pytest rootdir 정정 (HIGH) 또는 cj-312 close-out retro (cj-style 269th follow-up)

---

## §1 Sprint Overview

cj-312 wire sprint 는 **MVP hardening 7-checkpoint audit 실행 + gap list + fix sprint 결정 wire** 입니다.
- **cj-311 entry** (`69d7d72`) 의 audit methodology 결정 wire 의 후속 wire
- **사용자 결정 wire** (2026-09-09): 비용 $0 + MVP hardening 우선
- **결과**: 19 findings 종합 (3 HIGH + 4 MEDIUM + 3 LOW + 9 PASS) + 3 HIGH severity fix sprint 결정 wire

---

## §2 Sprint Scope (5 files)

| File | Type | LOC | Description |
|---|---|---|---|
| `phase-30-mvp-7-checkpoint-audit-wire-2026-09-09.md` | NEW content | ~480 | 13-section §1~§13 audit 결과 sprint doc |
| `commit-msg-cj-312.txt` | NEW meta | ~95 | commit message |
| `handoff-2026-09-09-cj-312-7-checkpoint-mvp-audit-wire-done.md` | NEW meta | ~180 | 본 handoff (8-section) |
| `sprint-status.yaml` | MODIFIED meta | +A730 +last_updated_note_v4_86 | v4.85 → v4.86 EXTENSION |
| `memory/MEMORY.md` | MODIFIED meta | +cj-312 hook +active sprint state EXTENSION | hook EXTENSION |

---

## §3 7 Checkpoint Audit 결과 종합 (19 findings)

### Severity 별 count
| Severity | Count | Action |
|---|---|---|
| **HIGH** | **3** | 즉시 fix sprint 결정 (cj-313 + cj-314 + cj-316) |
| **MEDIUM** | **4** | honestly DEFER (cj-303 carryover 보존) 또는 batch fix |
| **LOW** | **3** | honestly DEFER (post-W1) |
| **PASS** | **9** | 결정 wire 보존 |
| **TOTAL** | **19** findings | |

### Checkpoint 별 결과
| # | Checkpoint | Result | Severity | 결정 wire |
|---|---|---|---|---|
| 1 | PRD AC coverage | PASS ✅ | 7 PASS + 2 MEDIUM honestly DEFER | 결정 wire 보존 |
| 2 | Test coverage | **PARTIAL ⚠️** | 1 HIGH + 1 HIGH + 1 MEDIUM + 2 LOW | **cj-313 + cj-314** 결정 wire |
| 3 | Error envelope | PASS ✅ | 4 PASS | 결정 wire 보존 |
| 4 | Audit & observability | PASS+1HIGH | 3 PASS + 1 HIGH | **cj-316** 결정 wire |
| 5 | Security | PASS ✅ | 5 PASS | 결정 wire 보존 |
| 6 | Performance & reliability | PASS+MED/LOW | 4 PASS + 1 MEDIUM + 1 LOW | honestly DEFER |
| 7 | Documentation | PASS ✅ | 5 PASS + 1 MEDIUM | 결정 wire 보존 |

---

## §4 3 HIGH Severity Fix Sprint 결정 wire

### cj-313 pytest rootdir 정정 (cj-style 270번째, ~30min)
- **finding 2.1**: `apps/api/tests/` 부재의 root cause 정직 회복
- **fix**: `apps/api/pyproject.toml` 또는 project root `pyproject.toml` 의 `[tool.pytest.ini_options]` testpaths = `["tests", "apps/api"]` EXTENSION
- **source code 변경**: 1 line (pyproject.toml EXTENSION)
- **ci.yml 변경**: 0건
- **runtime 영향**: pytest collect 명령이 404 tests/ files + apps/api/ 모두 collect 가능

### cj-314 cj-307 carryover fix (cj-style 271번째, ~2h)
- **finding 2.2**: cj-307 fix 가 auth-callback aal1 만 fix, 기존 32 failures + 22 errors + 3 collection errors 정직 회복 안 됨
- **fix**: pytest 에러 triage + fix (severity 재평가 후 fix 또는 honestly DEFER)
- **source code 변경**: TBD per triage
- **결정 wire 보존**: cj-307 aal1 MFA listFactors verified=[] skip 그대로

### cj-316 FastAPI on_event → lifespan migration (cj-style 272번째, ~1-2h)
- **finding 4.3**: `apps/api/main.py` 의 `@app.on_event("startup")` + `@app.on_event("shutdown")` → FastAPI lifespan handler
- **fix**: FastAPI 0.109+ deprecation 정직 회복
- **source code 변경**: apps/api/main.py (lifespan context manager EXTENSION)
- **결정 wire 보존**: cj-307 fix 의 carryover 정직 회복

---

## §5 결정 wire 보존 (cj-309~cj-311 wire 결정 wire 그대로)

### 결정 wire 보존 항목
- **Pilot W1 launch D-day = 2026-09-14 KST** 보존
- **cj-309b B-1 Pilot candidate outreach** 결정 wire 보존 (Tier 1 5 + Tier 2 3 = 8, D-2 발송 honestly DEFER)
- **Resend (OQ-EPIC30+-2 v2)** swap 결정 wire 보존 (Postmark blocker 정직 회복)
- **cj-307 aal1 minimum fix** 결정 wire 보존 (cj-313/cj-314/cj-316 결정 wire 와 양립)
- **cj-304 4 critical gaps fix** 결정 wire 보존 (env vars + TZ + Pilot tenant CLI + Production seed)
- **cj-300 APScheduler KST** 결정 wire 보존 (TZ=Asia/Seoul, 34 references)
- **cj-303 EXTENSION** (37 pins match) 보존 (AD-14 stack pin)
- **capability matrix v1.54 EXTENSION** 보존
- **audit_action EXTENSION** 보존

### cj-311 entry 의 새 우선순위 EXTENSION (reframe)
- **비용 $0** = Railway/Vercel/Resend/Supabase 모두 launch day 까지 honestly DEFER
- **MVP hardening 우선** = cj-313 + cj-314 + cj-316 결정 wire → MVP 완결성 확보 → launch day

---

## §6 Honestly DEFER 결정 wire 보존

### 비용 발생 항목 honestly DEFER (사용자 결정 wire)
- ❌ Railway Hobby plan ($5/mo) — launch day 결정 wire
- ❌ Vercel Pro plan ($20/mo) — launch day 결정 wire
- ❌ Resend Pro plan ($20/mo) — launch day 결정 wire
- ❌ Supabase Pro plan ($25/mo) — launch day 결정 wire
- ❌ Custom DNS (Cloudflare) — launch day 결정 wire
- ❌ Sentry Pro plan — launch day 결정 wire

### cj-style 결정 wire honestly DEFER
- ❌ Pilot candidate outreach 발송 (D-2 2026-09-12 honestly DEFER)
- ❌ W1~W8 weekly tracking (launch day 부터 결정 wire)
- ❌ Railway project 생성 + Vercel project 생성 (Trial workspace, 0 projects 정직 회복)
- ❌ Resend API key 캡처 + dashboard 설정
- ❌ Supabase project production env 설정

### cj-303 carryover 4건 honestly DEFER (cj-312 audit 결과 MEDIUM)
- D-FINOPS-13 (multi-currency + budget forecast + ZBB + envelope + reconciliation)
- Phase 11~20 + 22 + 23 emit_audit_typed signature mismatch retroactive correction
- Layer 2 P1 pytest test backfill (cj-314 결정 wire 로 일부 해소)
- Layer 3 P2 docs backfill

### PRE-EXISTING honestly DEFER 6건 (cj-style 보존)
1. web-e2e Playwright 23 skip (cj-282a 6 closing-guard + cj-282b 17 bulk e2e)
2. test-suite-measure 잔여 (cj-282a)
3. web-test 잔여 (cj-282a)
4. lint-conventions (apps/web)
5. Sentry (post-W1, cj-305 wire)
6. custom DNS (post-W1, cj-305 wire)

---

## §7 CR 11-3 honest-DEFER 269번째

### 결정 wire chain (cj-style 220번째~269번째)
- **cj-282 (220번째)** → cj-282a (221+222) → cj-282b (223~238) → cj-297 (237th) → cj-298 (238th)
- **cj-299 (239~242)** → cj-300 (243+244) → cj-301 (245) → cj-302 (246+247)
- **cj-303 (248+249+250)** → cj-304 (251+252+253) → cj-305 (254+255)
- **cj-305b (256+257)** → cj-306 (259) → cj-307 (261) → cj-308 (263)
- **cj-309 (264)** → cj-309b (265) → cj-310 (266) → cj-310 retroactive correction (267)
- **cj-311 entry (268)** → **cj-312 wire (269)** ← **본 sprint**

### cumulative 결정 wire 보존
- **41/41** (cj-282~cj-311) → **+1 NEW = 42/42 cumulative** (cj-312 wire 신규)
- 결정 wire 보존: cj-309~cj-310 wire 결정 wire 그대로
- sprint-status v4.85 → **v4.86 EXTENSION** 결정 wire (A730 cj-312 wire + last_updated_note_v4_86)

### 정직 회복
- source code 변경 0건 (cj-312 wire docs-only sprint)
- 37 pins unchanged (cj-303 EXTENSION 보존)
- PRD v7.0 §F/§M/§R unchanged
- capability matrix v1.54 EXTENSION preserved
- audit actions EXTENSION preserved

---

## §8 Next unblocked 결정 wire 보류 + 결정 wire 일자

### 결정 보류 6개 옵션 (cj-312 wire 직후)
| 옵션 | 내용 | 예상 effort |
|---|---|---|
| **(a) cj-313 pytest rootdir 정정** | HIGH severity fix sprint (cj-style 270번째) | ~30min (docs-only + pyproject.toml testpaths EXTENSION) |
| **(b) cj-314 cj-307 carryover fix** | HIGH severity fix sprint (cj-style 271번째) | ~2h (32+22+3 pytest 에러 triage + fix) |
| **(c) cj-316 FastAPI on_event → lifespan** | HIGH severity fix sprint (cj-style 272번째) | ~1-2h (source code migration) |
| **(d) cj-312 close-out retro 진입** | cj-312 wire 결정 wire 종합 (cj-style 269th follow-up) | ~30min (docs-only) |
| **(e) PRD v2 EXTENSION 진입** | audit 결과 gap 의 우선순위 결정 후 PRD v2 작성 | TBD |
| **(f) carryover honestly DEFER 유지** | cj-303 carryover 4건 + PRE-EXISTING 6건 그대로 honestly DEFER | 0 effort |

### 결정 wire 일자
- **2026-09-09 KST (D-5)**

### Honestly DEFER 결정 wire (cj-312 close-out 후)
- ① Pilot launch D-day (2026-09-14) → 비용 발생 결정 wire 보류
- ② W1~W8 weekly follow-up 결정 wire (launch day 부터)
- ③ PRD v2 EXTENSION 결정 wire (cj-313/cj-314/cj-316 fix 후)
- ④ 비용 발생 항목 모두 (사용자 결정 wire, launch day 까지 honestly DEFER)

---

## §9 Cross-references + CR 11-3 정직 회복

### Cross-references
- **cj-style feedback** `prioritize-mvp-hardening-before-deploy` (2026-09-07) — 본 sprint 의 trigger
- **cj-style feedback** `count-remaining-before-start` (2026-09-07) — 매 주요 업무 진입 직전 잔여 주요 업무 개수 안내
- **cj-306 audit findings** (2026-09-08) — MVP deployment-ready audit, cj-307 fix 의 선행
- **cj-307 wire** (`a1cb7ad`) — auth-callback aal1 minimum fix (cj-312 audit 의 Checkpoint 2 carryover source)
- **cj-308 entry** (`07f06d0`) — Pilot W1 D-5 critical path 결정 wire entry
- **cj-309 wire** (`73766af`) — Resend + Supabase signup live verify wire
- **cj-309b wire** (`3c9bdbf`) — Pilot candidate list B-1 작성 wire
- **cj-310 entry** (`ce05e05`) — cj-309 close-out retro entry
- **cj-310 retroactive correction** (`6972571`) — headline 정직 회복
- **cj-311 entry** (`69d7d72`) — 7-Checkpoint MVP Audit Entry (cj-style 268번째)
- **cj-312 wire** (본 sprint) — 7-Checkpoint Audit 실행 결과 + gap list + fix sprint 결정 wire (cj-style 269번째)

### 결정 wire 정직 회복
- 7 checkpoint 종합 = 6 PASS section + 1 PARTIAL (Checkpoint 2 Test coverage)
- 19 findings = 3 HIGH (cj-313 + cj-314 + cj-316 결정 wire) + 4 MEDIUM (honestly DEFER) + 3 LOW (honestly DEFER) + 9 PASS (결정 wire 보존)
- 결정 wire 정직 회복: cj-309~cj-311 wire 결정 wire 그대로 보존 + MVP hardening 우선순위 EXTENSION
- cj-307 carryover 정직 회복: cj-312 audit 결과 cj-313 + cj-314 + cj-316 결정 wire 로 해소 결정

---

**CJ-312 WIRE 결정 wire 보존 완료**

**CR 11-3 honest-DEFER 269번째 결정 wire chain: cj-282 (220번째) → ... → cj-311 entry (268번째) → cj-312 wire (269번째, 본 sprint)**

**Next**: cj-313 pytest rootdir 정정 (HIGH severity) 진입 또는 cj-312 close-out retro 진입 (옵션 (d))
