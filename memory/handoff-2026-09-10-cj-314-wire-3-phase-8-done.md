---
name: cj-314-wire-3-phase-8-done
description: cj-314 wire 3 Phase 8 ESLint/SLO/SLI 8 fixes (cj-style 276번째) — Phase B item 2 closed, 8 stale test path bug → 8 passed (test-only fix, 0 source 변경, 5 files)
metadata:
  type: project
---

# cj-314 wire 3 Phase 8 ESLint/SLO/SLI 8 fixes — Handoff

> **Sprint**: cj-314 wire 3 Phase 8 ESLint/SLO/SLI 8 fixes (cj-style 276번째)
> **Date**: 2026-09-10 KST (D-4, Pilot W1 launch D-day 2026-09-14 KST)
> **Territory**: Phase 30 — MVP hardening 7-checkpoint audit 의 Checkpoint 2 (Test coverage) cj-307 carryover fix scope 의 Phase B item 2 CLOSED
> **Author**: Claude (operator = kjw)
> **Sprint form**: wire (cj-314 entry `3e2ed73` 의 risk-prioritized triage Phase B item 2 진입)
> **직전 sprint**: cj-314 wire 2 (`4435e2d`, sprint-status v4.91 → v4.92 EXTENSION — Phase B 6 fixes)

---

## §1 의도 분석 — cj-314 wire 2 결정 wire 의 옵션 (a) verbatim mirror 진입

### 사용자 결정 wire (2026-09-10 KST)
- cj-314 wire 2 결정 wire 의 옵션 (a) verbatim mirror: **cj-314 wire 3 (Phase B item 2) 진입**
- cj-style feedback `prioritize-mvp-hardening-before-deploy` (2026-09-07) verbatim mirror
- 비용 $0 + MVP hardening 우선 (2026-09-10 결정 wire)
- ~1h 소요 — Pilot W1 D-4 안에 충분히 fix + verify 가능

### cj-314 entry 의 claim (cj-style 271번째)
- **C. Phase 8 ESLint/SLO/SLI — 9 failures** (cj-314 entry §4 verbatim mirror)
- p99_budget (5) + slo_sli (4)
- Root cause (추정): apps/web/ ESLint rule 파일 부재 + docs/slo-sli.md 부재

### 실제 verification 결과 — ✅ root cause 의 정직 회복 필요
- **cj-314 entry 추정 9 fixes 의 정직 회복**: actual **8 fixes** (4+4)
- cj-314 entry 의 "p99_budget (5)" 추정 slightly off — actual `test_phase_8_p99_budget.py` has **4 pytest cases** (cj-style 270th + 273rd 정직 회복 패턴)
- **실제 root cause**: 테스트 path 계산 버그 — `parent.parent.parent` 3-level path 가 `tests/` 까지만 올라가고 project root 까지 못 올라감 (test 위치 `tests/api/core/` = 3-level depth → project root 까지 4-level 필요)
- ESLint rule (`apps/api/eslint/latency-budget-rule.js`) + latency_budget.py + slo-sli.md 모두 이미 정확한 content 보유 (변경 0건)

---

## §2 cj-314 wire 3 의 8 fixes (verbatim mirror)

### Files (2 MODIFIED tests)
- `tests/api/core/test_phase_8_p99_budget.py` — 2 lines (ESLINT_RULE_PATH + DEFAULT_BUDGETS_PATH)
- `tests/api/core/test_phase_8_slo_sli.py` — 1 line (SLO_SLI_DOC_PATH)

### Fix detail
- **Before**: `Path(__file__).parent.parent.parent / "apps" / "api" / ...` (3-level up = `tests/`)
- **After**: `Path(__file__).parent.parent.parent.parent / "apps" / "api" / ...` (4-level up = project root)

### Root cause analysis
- `__file__` = `costmgr/tests/api/core/test_phase_8_*.py`
- `.parent` = `costmgr/tests/api/core/`
- `.parent.parent` = `costmgr/tests/api/`
- `.parent.parent.parent` = `costmgr/tests/` ❌ (resolved to `tests/apps/api/eslint/...` and `tests/docs/...`)
- `.parent.parent.parent.parent` = `costmgr/` ✅

### Why this is test bug, not SSOT bug
- `apps/api/eslint/latency-budget-rule.js` EXISTS with 7 KNOWN_ENDPOINTS + `unmappedEndpoint` + `DEFAULT_LATENCY_BUDGETS`
- `apps/api/core/latency_budget.py` EXISTS with `dry_run` + "Synthetic fallback" comment
- `docs/slo-sli.md` EXISTS with SLA-1~SLA-4 + 30d rolling + 1.5h/month + owner-only + 2FA
- 모든 SSOT files 가 content 정합 — only test 의 path 계산만 forward

---

## §3 verify gate 결과

### 8 Phase 8 failures (target scope)
- **Before**: 8 failed (test_phase_8_p99_budget.py 4 + test_phase_8_slo_sli.py 4)
- **After**: **8 passed** ✅

### Within-scope regression check (4 Phase 8 test files)
- tests/api/core/test_phase_8_p99_budget.py + test_phase_8_slo_sli.py + test_phase_8_latency_regression.py + test_phase_8_load_test_runner.py
- **Result**: **25 passed in 137.99s (0:02:17)**, exit code 0 (zero regressions)

### Broader sweep regression check (tests/api/core/)
- **Result**: 1166 passed, 37 failed, 16 skipped
- **37 residual failures**: cj-314 wire 4/5 scope (Phase 5/9/16/26/30 + Phase 10 SLO family) — cj-314 wire 3 scope 외
- **0 regressions in cj-314 wire 3 scope** ✅

### Zero regressions
- 0 source code 변경 (apps/api/* + apps/web/* unchanged)
- 2 test files MODIFIED: test_phase_8_p99_budget.py + test_phase_8_slo_sli.py only (3 lines total)
- ESLint rule unchanged: `apps/api/eslint/latency-budget-rule.js` unchanged
- latency_budget unchanged: `apps/api/core/latency_budget.py` unchanged
- slo-sli.md unchanged: `docs/slo-sli.md` unchanged (all SSOT content preserved)
- migration source unchanged: 0035/0037 unchanged
- 0 capability matrix source 변경 (docs/capability-matrix.md unchanged, v1.54 EXTENSION preserved)
- 37 pins unchanged (cj-303 EXTENSION 보존)
- 14 job matrix unchanged (cj-style baseline-green 보존)
- PRD v7.0 §F/§M/§R unchanged
- audit actions EXTENSION preserved
- AD-14 stack pin EXTENSION preserved

---

## §4 결정 wire 보존 (cj-309~cj-314 wire 2 wire/entry 결정 wire 그대로)

### 결정 wire 보존 항목
- **Pilot W1 launch D-day 2026-09-14 KST** 보존
- **cj-309b B-1 Pilot candidate outreach** 보존 (Tier 1 5 + Tier 2 3 = 8, D-2 발송 honestly DEFER)
- **Resend (OQ-EPIC30+-2 v2) swap** 보존
- **cj-307 aal1 minimum fix** 보존
- **cj-304 4 critical gaps fix** 보존
- **cj-300 APScheduler KST** 보존
- **cumulative 48 → 49 sprints** 결정 wire 보존

### Phase A ALL CLOSED ✅ HONEST + Phase B item 1, 2 CLOSED ✅ HONEST
- **Phase A item 1**: cj-316 FastAPI on_event → lifespan migration ✅ CLOSED (`1281ca5`)
- **Phase A item 2**: cj-317 alembic 0037 errors triage + fix ✅ CLOSED (`99a7343`)
- **Phase A item 3**: cj-314 wire 1 capability matrix drift 10 fixes ✅ CLOSED (`cca03c2`)
- **Phase B item 1**: cj-314 wire 2 Phase B 6 fixes ✅ CLOSED (`4435e2d`)
- **Phase B item 2**: cj-314 wire 3 Phase 8 ESLint/SLO/SLI 8 fixes ✅ CLOSED (본 sprint)

### cj-307 carryover 의 HONEST scope update
- cj-307 의 32+22+3 estimate = 57 items
- cj-314 entry 의 actual scope = **88 items (66 failures + 22 errors)**
- **cj-317 closed**: 22 errors (Phase A item 2)
- **cj-314 wire 1 closed**: 10 failures (Phase A item 3, capability matrix drift)
- **cj-314 wire 2 closed**: 6 failures (Phase B item 1, Phase 30 + Phase 5 + Phase 3)
- **cj-314 wire 3 closed**: 8 failures (Phase B item 2, Phase 8 ESLint/SLO/SLI)
- **cj-314 wire 4~6 + batch B/C 결정 wire 보류**: 42 failures + sso 13 skipped

---

## §5 CR 11-3 honest-DEFER 276번째

### 결정 wire chain (cj-style 220번째~276번째)
- cj-282 (220번째) → cj-282a (221+222) → cj-282b (223~238) → cj-297 (237th) → cj-298 (238th)
- cj-299 (239~242) → cj-300 (243+244) → cj-301 (245) → cj-302 (246+247)
- cj-303 (248+249+250) → cj-304 (251+252+253) → cj-305 (254+255)
- cj-305b (256+257) → cj-306 (259) → cj-307 (261) → cj-308 (263)
- cj-309 (264) → cj-309b (265) → cj-310 (266) → cj-310 retroactive (267)
- cj-311 entry (268) → cj-312 wire (269) → cj-313 wire (270)
- cj-314 entry (271) → cj-316 wire (272) → cj-317 wire (273)
- cj-314 wire 1 (274) → cj-314 wire 2 (275) → **cj-314 wire 3 (276)** ← **본 sprint**

### cumulative 결정 wire 보존
- **48/48** (cj-282~cj-314 wire 2) → **+1 NEW = 49/49 cumulative** (cj-314 wire 3 신규)
- 결정 wire 보존: cj-309~cj-314 wire 2 wire/entry 결정 wire 그대로
- sprint-status v4.92 → **v4.93 EXTENSION** 결정 wire (A737 cj-314 wire 3 + last_updated_note_v4_93)

### CR lessons applied
- CR 0-2 (RLS) + CR 1-1 (audit-first INSERT) + CR 1-1 (ContextVar + RSC boundary)
- CR 4-3/4-4 + CR 5-1 (Decimal precision logic)
- CR 9-6 (commit message `git commit -F <file>`)
- **CR 11-3 (honest-DEFER retroactive correction discipline)** — cj-314 wire 3 에서 verbatim mirror (cj-style 257th + 267th + 270th + 272th + 273rd + 274th + 275th 패턴)
- CR 11-4 (P-015 pure validator pattern)
- CR 12-1 (L4 industry-agnostic capability)
- CR 12-5 (D-14 typed exception envelope + D-PARITY-01 + D-GATE-01)

### 정직 회복
- 0 source code 변경 (cj-314 wire 3 은 tests only fix + meta sprint)
- capability matrix 변경 0건 (cj-297 wire v1.54 EXTENSION 보존)
- ESLint rule 변경 0건 (cj-314 entry 의 'apps/web ESLint rule 부재' 추정은 incorrect — 실제 ESLint rule 은 `apps/api/eslint/` 에 존재)
- latency_budget 변경 0건
- slo-sli.md 변경 0건
- 37 pins unchanged (cj-303 EXTENSION 보존)
- PRD v7.0 §F/§M/§R unchanged
- capability matrix v1.54 EXTENSION preserved
- audit actions EXTENSION preserved
- AD-14 stack pin EXTENSION preserved

---

## §6 Honestly DEFER 결정 wire 보존

### 비용 발생 항목 honestly DEFER (사용자 결정 wire 2026-09-10)
- ❌ Railway Hobby plan ($5/mo) — launch day 결정 wire
- ❌ Vercel Pro plan ($20/mo) — launch day 결정 wire
- ❌ Resend Pro plan ($20/mo) — launch day 결정 wire
- ❌ Supabase Pro plan ($25/mo) — launch day 결정 wire
- ❌ Custom DNS (Cloudflare) — launch day 결정 wire
- ❌ Sentry Pro plan — launch day 결정 wire

### cj-style 결정 wire honestly DEFER
- ❌ Pilot candidate outreach 발송 (D-2 2026-09-12 honestly DEFER)
- ❌ W1~W8 weekly tracking (launch day 부터 결정 wire)

### cj-314 wire 4~6 + batch B/C 결정 wire 보류 (operator choice)
- cj-314 wire 4 (~1-2h): Phase 5/9/16/26/30 + Phase 3 hook ~10 fixes
- cj-314 wire 5 (~1h): Epic 15 alembic 0037 12 errors
- cj-314 wire 6 (~1h): errors TBD 10 fixes
- cj-314 batch B (~4-5h): Phase 10 SLO family + Phase 5/9/16/26/30 ~37 fixes
- cj-314 batch C (~2h): Epic 15 alembic + errors TBD ~22 fixes

### PRE-EXISTING honestly DEFER 6건 (cj-style 보존)
1. web-e2e Playwright 23 skip (cj-282a/b)
2. test-suite-measure 잔여 (cj-282a)
3. web-test 잔여 (cj-282a)
4. lint-conventions (apps/web)
5. Sentry (post-W1, cj-305 wire)
6. custom DNS (post-W1, cj-305 wire)

### cj-303 carryover 4건 honestly DEFER 보존
- D-FINOPS-13 (multi-currency + budget forecast + ZBB + envelope + reconciliation)
- Phase 11~20 + 22 + 23 emit_audit_typed signature mismatch retroactive correction
- Layer 2 P1 pytest test backfill (cj-314 결정 wire 로 일부 해소)
- Layer 3 P2 docs backfill

---

## §7 결정 보류 (cj-314 wire 3 종료 후)

| 옵션 | 내용 | Effort |
|---|---|---|
| **(b) cj-314 wire 4** (RECOMMENDED next) | Phase B item 3: Phase 5/9/16/26/30 + Phase 3 hook ~10 fixes | ~1-2h |
| **(c) cj-314 wire 5** | Phase B item 4: Epic 15 alembic 0037 12 errors | ~1h |
| **(d) cj-314 batch B** | Phase 10 SLO family + Phase 5/9/16/26/30 ~37 fixes | ~4-5h |
| **(e) cj-313 close-out retro** | docs-only | ~30min |
| **(f) cj-312 close-out retro** | docs-only | ~30min |
| **(g) cj-309b B-1 Pilot candidate outreach** | D-2 발송, 운전자 결정 | 운전자 결정 |
| **(h) PRD v2 EXTENSION** | cj-314 wire 4 후 | TBD |

### 결정 wire 일자
- **2026-09-10 KST (D-4)**

---

## §8 Cross-references + CR 11-3 정직 회복

### Cross-references
- **cj-style feedback** `prioritize-mvp-hardening-before-deploy` (2026-09-07) — 본 sprint 의 trigger
- **cj-style feedback** `count-remaining-before-start` (2026-09-07) — 매 주요 업무 진입 직전 잔여 주요 업무 개수 안내
- **cj-307 wire** (`a1cb7ad`) — auth-callback aal1 minimum fix (cj-314 결정 wire 의 source)
- **cj-312 wire** (`a0a27d1`) — 7-Checkpoint MVP Audit Wire (cj-314 의 source)
- **cj-313 wire** (`cfe5eca`) — pytest rootdir 정정 (cj-314 의 prerequisite)
- **cj-314 entry** (`3e2ed73`) — cj-307 carryover fix scope triage (cj-style 271번째)
- **cj-316 wire** (`1281ca5`) — Phase A item 1 closed
- **cj-317 wire** (`99a7343`) — Phase A item 2 closed
- **cj-314 wire 1** (`cca03c2`) — Phase A item 3 closed (capability matrix drift 10 fixes)
- **cj-314 wire 2** (`4435e2d`) — Phase B item 1 closed (Phase 30 + Phase 5 + Phase 3 = 6 fixes)
- **cj-314 wire 3** (본 sprint) — Phase B item 2 closed (Phase 8 ESLint/SLO/SLI = 8 fixes)

### 결정 wire 정직 회복
- cj-314 entry 의 "p99_budget (5) + slo_sli (4) = 9 fixes" 추정 의 정직 회복 — actual 4+4 = 8 fixes
- cj-314 entry 의 "apps/web ESLint rule 부재 + docs/slo-sli.md 부재" root cause 추정 의 정직 회복 — 실제 ESLint rule은 `apps/api/eslint/` 에 존재, slo-sli.md 존재. 진짜 root cause = test path 계산 버그 (3-level → 4-level)
- CR 11-3 honest-DEFER 276번째 정직 회복 (cj-style 257th + 267th + 270th + 272th + 273rd + 274th + 275th 패턴 verbatim mirror)
- 49/49 cumulative 결정 wire 보존 (cj-314 wire 2 의 48 + cj-314 wire 3 의 NEW 49번째)
- 결정 wire 보존: cj-309~cj-314 wire 2 wire/entry 결정 wire 그대로 + 0 source code 변경 + 0 capability matrix 변경 + 0 ESLint rule 변경 + 0 latency_budget 변경 + 0 slo-sli.md 변경

---

**CJ-314 WIRE 3 결정 wire 보존 완료**

**CR 11-3 honest-DEFER 276번째 결정 wire chain: cj-282 (220번째) → ... → cj-314 wire 2 Phase B 6 fixes (275번째) → cj-314 wire 3 Phase 8 ESLint/SLO/SLI 8 fixes (276번째, 본 sprint)**

**Next**: cj-314 wire 4 (Phase B item 3, ~1-2h, RECOMMENDED) 또는 cj-314 wire 5 또는 cj-314 batch B 또는 cj-313/cj-312 close-out retro 또는 cj-309b B-1 또는 PRD v2
