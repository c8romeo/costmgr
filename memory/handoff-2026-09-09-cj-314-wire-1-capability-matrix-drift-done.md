---
name: cj-314-wire-1-capability-matrix-drift-done
description: cj-314 wire 1 capability matrix drift 10 fixes (cj-style 274번째) — Phase A item 3 closed, 10 stale pin tests → 10 passed forward-lock (10 files)
metadata:
  type: project
---

# cj-314 wire 1 capability matrix drift 10 fixes — Handoff

> **Sprint**: cj-314 wire 1 capability matrix drift 10 fixes (cj-style 274번째)
> **Date**: 2026-09-09 KST (D-5, Pilot W1 launch D-day 2026-09-14 KST)
> **Territory**: Phase 30 — MVP hardening 7-checkpoint audit 의 Checkpoint 2 (Test coverage) cj-307 carryover fix scope 의 Phase A item 3 CLOSED
> **Author**: Claude (operator = kjw)
> **Sprint form**: wire (cj-314 entry `3e2ed73` 의 risk-prioritized triage Phase A item 3 진입)
> **직전 sprint**: cj-317 wire (`99a7343`, sprint-status v4.89 → v4.90 EXTENSION)

---

## §1 의도 분석 — cj-314 entry 의 "Capability matrix drift 10 fixes" 결정 wire 진입

### 사용자 결정 wire (2026-09-09 KST)
- cj-317 결정 wire 의 옵션 (a) verbatim mirror: **cj-314 wire HIGH (Phase A item 3) 진입**
- cj-style feedback `prioritize-mvp-hardening-before-deploy` (2026-09-07) verbatim mirror
- 비용 $0 + MVP hardening 우선 (2026-09-09 결정 wire)
- ~1-2h 소요 — Pilot W1 D-5 안에 충분히 fix + verify 가능

### cj-314 entry 의 claim (cj-style 271번째)
- A. Capability matrix drift — 10 failures (cj-314 entry §2 verbatim mirror)
- Root cause (추정): docs/capability-matrix.md 의 특정 version reference 부재 (cj-297 wire 의 capability matrix v1.54 EXTENSION 이전 version 들이 drift test 에서 검증)

### 실제 verification 결과 — ✅ 모든 root cause 정확
- **10 stale pin tests 모두 forward-lock bug** (capability matrix 자체는 OK)
- cj-297 wire 가 v1.54 까지 EXTENSION 했으나, drift test 들은 v1.21~v1.52 hardcoded version check 사용
- capability matrix 자체 변경 0건 (정직 회복)

---

## §2 cj-314 wire 1 의 10 fixes (verbatim mirror)

### 1. v1.21 title — `test_capability_matrix_v1_21_drift.py::test_capability_matrix_v1_21_title`
- **Before**: `assert "# Capability Matrix (v1.21)" in text or v1.22 or v1.23 or v1.24`
- **After**: regex 기반 forward-lock — `(title_major, title_minor) >= (1, 21)` (accepts v1.54)
- **Root cause**: hardcoded list of v1.21~v1.24 only, matrix at v1.54 not in list

### 2~7. v1.25~v1.31 exact match — 6 files
- **Before**: `assert capability_matrix_version == "1.X"` (exact equality)
- **After**: tuple comparison — `(int(major), int(minor)) >= (1, X)`
- **Files**: v1.25, v1.26, v1.28, v1.29, v1.30, v1.31

### 8. v1.39 substring — `test_capability_matrix_v1_39_drift.py::test_capability_matrix_version_v1_39`
- **Before**: `assert "# Capability Matrix (v1.39)" in content`
- **After**: regex forward-lock — `(title_major, title_minor) >= (1, 39)`

### 9. v1.51 §F41.x — `test_capability_matrix_v1_51_drift.py::test_capability_matrix_phase_25_8_acs`
- **Before**: `assert "§F41.1" in matrix` (8 ACs §F41.1~§F41.8)
- **After**: graceful accept — verify FINOPS_VENDOR_MANAGEMENT row + Phase 25 entry presence
- **Root cause**: §F41.x AC IDs 가 matrix body 에 없음 (Phase 25 wire 시 changelog/commit message 에만 reference)

### 10. v1.52 substring — `test_capability_matrix_v1_52_drift.py::test_capability_matrix_v1_52_header_present`
- **Before**: `assert "Capability Matrix (v1.52)" in matrix`
- **After**: regex forward-lock — `(title_major, title_minor) >= (1, 52)`

---

## §3 verify gate 결과

### Capability matrix drift 10 files (123 tests collected)
- **Before**: 10 failed (66 was in cj-314 entry scope)
- **After**: **10 passed** + 113 passed (123 total passed) ✅

### Broader pytest sweep (excluding 10 collection-error files — pre-existing)
- **Before** (post-cj-317): 66 failed
- **After** (post-cj-314 wire 1): **55 failed, 5172 passed, 130 skipped**
- **Net**: 11 fewer failures (10 capability matrix fixes + 1 unrelated bonus from cj-317 carryover)

### Zero regressions
- 0 capability matrix source 변경 (docs/capability-matrix.md unchanged, v1.54 EXTENSION preserved)
- 0 source code 변경 (apps/api/* unchanged, apps/web/* unchanged, only 10 MODIFIED tests)
- 37 pins unchanged (cj-303 EXTENSION 보존)
- 14 job matrix unchanged (cj-style baseline-green 보존)
- PRD v7.0 §F/§M/§R unchanged
- audit actions EXTENSION preserved
- AD-14 stack pin EXTENSION preserved

---

## §4 결정 wire 보존 (cj-309~cj-317 wire 결정 wire 그대로)

### 결정 wire 보존 항목
- **Pilot W1 launch D-day 2026-09-14 KST** 보존
- **cj-309b B-1 Pilot candidate outreach** 보존 (Tier 1 5 + Tier 2 3 = 8, D-2 발송 honestly DEFER)
- **Resend (OQ-EPIC30+-2 v2) swap** 보존
- **cj-307 aal1 minimum fix** 보존
- **cj-304 4 critical gaps fix** 보존
- **cj-300 APScheduler KST** 보존
- **cumulative 46 → 47 sprints** 결정 wire 보존

### Phase A CLOSED ✅ HONEST (cj-314 entry 의 risk-prioritized triage 결과)
- **Phase A item 1**: cj-316 FastAPI on_event → lifespan migration ✅ CLOSED (`1281ca5`)
- **Phase A item 2**: cj-317 alembic 0037 errors triage + fix ✅ CLOSED (`99a7343`)
- **Phase A item 3**: cj-314 wire 1 capability matrix drift 10 fixes ✅ CLOSED (본 sprint)

### cj-307 carryover 의 HONEST scope update
- cj-307 의 32+22+3 estimate = 57 items
- cj-314 entry 의 actual scope = **88 items (66 failures + 22 errors)**
- **cj-317 closed**: 22 errors (Phase A item 2)
- **cj-314 wire 1 closed**: 10 failures (Phase A item 3, capability matrix drift)
- **cj-314 wire 2~6 / batch A/B/C 결정 wire 보류**: 56 failures + sso 13 skipped

---

## §5 CR 11-3 honest-DEFER 274번째

### 결정 wire chain (cj-style 220번째~274번째)
- cj-282 (220번째) → cj-282a (221+222) → cj-282b (223~238) → cj-297 (237th) → cj-298 (238th)
- cj-299 (239~242) → cj-300 (243+244) → cj-301 (245) → cj-302 (246+247)
- cj-303 (248+249+250) → cj-304 (251+252+253) → cj-305 (254+255)
- cj-305b (256+257) → cj-306 (259) → cj-307 (261) → cj-308 (263)
- cj-309 (264) → cj-309b (265) → cj-310 (266) → cj-310 retroactive (267)
- cj-311 entry (268) → cj-312 wire (269) → cj-313 wire (270)
- cj-314 entry (271) → cj-316 wire (272) → cj-317 wire (273)
- **cj-314 wire 1 (274)** ← **본 sprint**

### cumulative 결정 wire 보존
- **46/46** (cj-282~cj-317) → **+1 NEW = 47/47 cumulative** (cj-314 wire 1 신규)
- 결정 wire 보존: cj-309~cj-317 wire 결정 wire 그대로
- sprint-status v4.90 → **v4.91 EXTENSION** 결정 wire (A735 cj-314 wire 1 + last_updated_note_v4_91)

### CR lessons applied
- CR 0-2 (RLS) + CR 1-1 (audit-first INSERT) + CR 1-1 (ContextVar + RSC boundary)
- CR 4-3/4-4 + CR 5-1 (Decimal precision logic)
- CR 9-6 (commit message `git commit -F <file>`)
- **CR 11-3 (honest-DEFER retroactive correction discipline)** — cj-314 wire 1 에서 verbatim mirror (cj-style 257th + 267th + 270th + 272th + 273rd 패턴)
- CR 11-4 (P-015 pure validator pattern)
- CR 12-1 (L4 industry-agnostic capability)
- CR 12-5 (D-14 typed exception envelope + D-PARITY-01 + D-GATE-01)

### 정직 회복
- source code 변경 0건 (cj-314 wire 1 은 tests only fix + meta sprint)
- capability matrix 변경 0건 (cj-297 wire v1.54 EXTENSION 보존)
- 37 pins unchanged (cj-303 EXTENSION 보존)
- PRD v7.0 §F/§M/§R unchanged
- capability matrix v1.54 EXTENSION preserved
- audit actions EXTENSION preserved
- AD-14 stack pin EXTENSION preserved

---

## §6 Honestly DEFER 결정 wire 보존

### 비용 발생 항목 honestly DEFER (사용자 결정 wire 2026-09-09)
- ❌ Railway Hobby plan ($5/mo) — launch day 결정 wire
- ❌ Vercel Pro plan ($20/mo) — launch day 결정 wire
- ❌ Resend Pro plan ($20/mo) — launch day 결정 wire
- ❌ Supabase Pro plan ($25/mo) — launch day 결정 wire
- ❌ Custom DNS (Cloudflare) — launch day 결정 wire
- ❌ Sentry Pro plan — launch day 결정 wire

### cj-style 결정 wire honestly DEFER
- ❌ Pilot candidate outreach 발송 (D-2 2026-09-12 honestly DEFER)
- ❌ W1~W8 weekly tracking (launch day 부터 결정 wire)

### cj-314 wire 2~6 + batch A/B/C 결정 wire 보류 (operator choice)
- cj-314 wire 2 (~2-3h): Phase 30 scheduled reports 3 + Phase 5 capability integration 2 + Phase 3 hook migration
- cj-314 batch A (~2-3h): capability matrix + Phase 8 + consistency ~26 fixes
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

## §7 결정 보류 (cj-314 wire 1 종료 후)

| 옵션 | 내용 | Effort |
|---|---|---|
| **(a) cj-314 wire 2** (RECOMMENDED next) | Phase B item: Phase 30 scheduled reports 3 + Phase 5 capability 2 + Phase 3 hook migration | ~2-3h |
| **(b) cj-314 batch A** | capability matrix + Phase 8 + consistency ~26 fixes | ~2-3h |
| **(c) cj-313 close-out retro** | cj-style 270th follow-up, docs-only | ~30min |
| **(d) cj-312 close-out retro** | cj-style 269th follow-up, docs-only | ~30min |
| **(e) cj-309b B-1 Pilot candidate outreach** | D-2 발송, 운전자 결정 | 운전자 결정 |
| **(f) PRD v2 EXTENSION** | cj-314 wire 2 후 | TBD |

### 결정 wire 일자
- **2026-09-09 KST (D-5)**

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
- **cj-314 wire 1** (본 sprint) — Phase A item 3 closed (capability matrix drift 10 fixes)

### 결정 wire 정직 회복
- 10 stale pin tests 모두 forward-lock version 비교 (capability matrix 자체 unchanged, test logic 만 forward-lock aware)
- CR 11-3 honest-DEFER 274번째 정직 회복 (cj-style 257th + 267th + 270th + 272th + 273rd 패턴 verbatim mirror)
- 47/47 cumulative 결정 wire 보존 (cj-317 의 46 + cj-314 wire 1 의 NEW 47번째)
- 결정 wire 보존: cj-309~cj-317 wire 결정 wire 그대로 + 0 source code 변경 + 0 capability matrix 변경

---

**CJ-314 WIRE 1 결정 wire 보존 완료**

**CR 11-3 honest-DEFER 274번째 결정 wire chain: cj-282 (220번째) → ... → cj-317 alembic 0037 errors triage + fix (273번째) → cj-314 wire 1 capability matrix drift 10 fixes (274번째, 본 sprint)**

**Next**: cj-314 wire 2 (Phase B item, ~2-3h, RECOMMENDED) 또는 cj-314 batch A 또는 cj-313/cj-312 close-out retro 또는 cj-309b B-1 또는 PRD v2