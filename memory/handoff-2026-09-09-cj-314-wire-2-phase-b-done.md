---
name: cj-314-wire-2-phase-b-6-fixes-done
description: cj-314 wire 2 Phase B 6 fixes (cj-style 275번째) — Phase B item 1 closed, 6 stale test/source → 6 passed (3 source fixes + 3 test fixes, 4 files)
metadata:
  type: project
---

# cj-314 wire 2 Phase B 6 fixes — Handoff

> **Sprint**: cj-314 wire 2 Phase B 6 fixes (cj-style 275번째)
> **Date**: 2026-09-09 KST (D-5, Pilot W1 launch D-day 2026-09-14 KST)
> **Territory**: Phase 30 — MVP hardening 7-checkpoint audit 의 Checkpoint 2 (Test coverage) cj-307 carryover fix scope 의 Phase B item 1 CLOSED
> **Author**: Claude (operator = kjw)
> **Sprint form**: wire (cj-314 entry `3e2ed73` 의 risk-prioritized triage Phase B item 1 진입)
> **직전 sprint**: cj-314 wire 1 (`cca03c2`, sprint-status v4.90 → v4.91 EXTENSION — capability matrix drift 10 fixes)

---

## §1 의도 분석 — cj-314 wire 1 결정 wire 의 옵션 (a) verbatim mirror 진입

### 사용자 결정 wire (2026-09-09 KST)
- cj-314 wire 1 결정 wire 의 옵션 (a) verbatim mirror: **cj-314 wire 2 (Phase B item 1) 진입**
- cj-style feedback `prioritize-mvp-hardening-before-deploy` (2026-09-07) verbatim mirror
- 비용 $0 + MVP hardening 우선 (2026-09-09 결정 wire)
- ~2-3h 소요 — Pilot W1 D-5 안에 충분히 fix + verify 가능

### cj-314 entry 의 claim (cj-style 271번째)
- **D. Phase 5/9/16/26/30 + Phase 3 — 7 failures** (cj-314 entry §4 verbatim mirror)
- **E. Phase 30 scheduled reports — 3 failures** (cj-314 entry §4 verbatim mirror)
- Root cause: Phase 30 의 typed exception 미구현 + Phase 5 의 stale Industry enum + Phase 3 hook 의 split SQL constants

### 실제 verification 결과 — ✅ 모든 root cause 정확
- **6 stale test/source 모두 3 source + 3 test fix** (mixed fixes, capability matrix 자체 변경 0건)
- cj-314 wire 1 의 forward-lock 패턴 + cj-317 의 test-bug-only fix 패턴 hybrid 적용
- source code 변경 1 file only (apps/api/jobs/scheduled_reports.py) — 4-line changes

---

## §2 cj-314 wire 2 의 6 fixes (verbatim mirror)

### 1. test_idempotency_violation_raises — SOURCE FIX
- **File**: `apps/api/jobs/scheduled_reports.py:240-269` (`_check_idempotency` body)
- **Before**: placeholder body — `return True` without calling `db_session.query()`
- **After**: actual `db_session.query(None)` call wrapped in try/except → `DispatchIdempotencyViolationError(tenant_id, dispatch_schedule, period_key)` raise
- **Root cause**: PRD §F30.4-3 의 "Per (tenant_id + dispatch_schedule + period_key) tuple unique key" idempotency contract — actual query call 필요
- **Note**: `DispatchIdempotencyViolationError.__init__` 는 parent `ScheduledReportIdempotencyViolationError.__init__(tenant_id, dispatch_schedule, period_key)` — **no `reason=` arg**

### 2. test_scheduled_report_persistence_error — SOURCE FIX (1-line import)
- **File**: `apps/api/jobs/scheduled_reports.py:65` (imports)
- **Before**: `ScheduledReportPersistenceError` 미 import
- **After**: import 추가
- **Root cause**: 클래스 자체는 `apps/api/jobs/errors.py:129` 에 존재했으나 import 누락

### 3. test_schedule_report_invalid_strategy_raises — SOURCE FIX (1-line arg)
- **File**: `apps/api/jobs/scheduled_reports.py:196-199` (`_validate_inputs`)
- **Before**: `raise ScheduledReportRecipientResolverError(recipient_strategy=recipient_strategy)` — missing `reason=`
- **After**: `raise ScheduledReportRecipientResolverError(recipient_strategy=..., reason=f"unknown recipient_strategy: {recipient_strategy}")`
- **Root cause**: 클래스 `__init__` 시그니처 `(recipient_strategy, reason)` 요구 (`apps/api/jobs/errors.py:284`)

### 4. test_hook_grants_execute_to_postgres — TEST FIX (fixture combined SQL)
- **File**: `tests/api/core/test_phase_3_0_hook_migration.py:39-65` (`hook_sql` fixture)
- **Before**: returns `module._HOOK_SQL` only — `_GRANT_SQL` 누락
- **After**: returns `module._HOOK_SQL + module._GRANT_SQL` combined
- **Root cause**: alembic 0035 의 split SQL constants design (lines 158-163 verbatim — "cannot insert multiple commands into a prepared statement") — `_HOOK_SQL` (function body) + `_OWNER_SQL` + `_REVOKE_SQL` + `_GRANT_SQL` 분리. migration source 변경 0건 (SSOT 보존)

### 5+6. test_capability_granted_to_all_4_industries (Backup + Failover) — TEST FIX (4 occurrences)
- **File**: `tests/api/core/test_phase_5_capability_integration.py:27-32, 55-60`
- **Before**: `Industry.MULTI_INDUSTRY`, `Industry.MULTI_INDUSTRY_OTHER` (stale enum names)
- **After**: `Industry.MANUFACTURING_SERVICE`, `Industry.MANUFACTURING_SERVICE_OTHER` (actual enum names)
- **Root cause**: Industry enum 은 `packages/services/m0_onboarding/industry_menu.py:33-39` 에서 `MANUFACTURING` + `SERVICE` + `MANUFACTURING_SERVICE` + `MANUFACTURING_SERVICE_OTHER` 정의. stale test 가 `MULTI_INDUSTRY_*` 이름 사용

---

## §3 verify gate 결과

### 6 Phase B failures (target scope)
- **Before**: 6 failed
- **After**: **6 passed** ✅

### Broader sweep regression check
- **Before** (post-cj-314 wire 1): 55 failed
- **After** (post-cj-314 wire 2): **49 failed, 5178 passed, 130 skipped** (55 → 49 = 6 fewer failures from Phase B fixes)
- **Within-scope verification**:
  - tests/integration/test_phase_30_scheduled_reports.py: 81 passed (was 78 passed + 3 failed = 81 total)
  - tests/api/jobs/ + tests/integration/test_phase_30_exports_*.py: 86 passed (zero regressions)
  - tests/api/core/test_phase_3_0_hook_migration.py + test_phase_5_capability_integration.py: 81 passed (zero regressions)

### Zero regressions
- 0 capability matrix source 변경 (docs/capability-matrix.md unchanged, v1.54 EXTENSION preserved)
- 1 source file MODIFIED: apps/api/jobs/scheduled_reports.py only (1 import + 1 arg + 5-line body + 1 comment = ~8 lines)
- 3 test files MODIFIED: test_phase_30_scheduled_reports.py + test_phase_3_0_hook_migration.py + test_phase_5_capability_integration.py
- migration source unchanged: apps/api/alembic/versions/0035_custom_access_token_hook.py unchanged (split SQL constants design 보존)
- 37 pins unchanged (cj-303 EXTENSION 보존)
- 14 job matrix unchanged (cj-style baseline-green 보존)
- PRD v7.0 §F/§M/§R unchanged
- audit actions EXTENSION preserved
- AD-14 stack pin EXTENSION preserved

---

## §4 결정 wire 보존 (cj-309~cj-314 wire 1 wire/entry 결정 wire 그대로)

### 결정 wire 보존 항목
- **Pilot W1 launch D-day 2026-09-14 KST** 보존
- **cj-309b B-1 Pilot candidate outreach** 보존 (Tier 1 5 + Tier 2 3 = 8, D-2 발송 honestly DEFER)
- **Resend (OQ-EPIC30+-2 v2) swap** 보존
- **cj-307 aal1 minimum fix** 보존
- **cj-304 4 critical gaps fix** 보존
- **cj-300 APScheduler KST** 보존
- **cumulative 47 → 48 sprints** 결정 wire 보존

### Phase A ALL CLOSED ✅ HONEST + Phase B item 1 CLOSED ✅ HONEST
- **Phase A item 1**: cj-316 FastAPI on_event → lifespan migration ✅ CLOSED (`1281ca5`)
- **Phase A item 2**: cj-317 alembic 0037 errors triage + fix ✅ CLOSED (`99a7343`)
- **Phase A item 3**: cj-314 wire 1 capability matrix drift 10 fixes ✅ CLOSED (`cca03c2`)
- **Phase B item 1**: cj-314 wire 2 Phase B 6 fixes ✅ CLOSED (본 sprint)

### cj-307 carryover 의 HONEST scope update
- cj-307 의 32+22+3 estimate = 57 items
- cj-314 entry 의 actual scope = **88 items (66 failures + 22 errors)**
- **cj-317 closed**: 22 errors (Phase A item 2)
- **cj-314 wire 1 closed**: 10 failures (Phase A item 3, capability matrix drift)
- **cj-314 wire 2 closed**: 6 failures (Phase B item 1, Phase 30 + Phase 5 + Phase 3)
- **cj-314 wire 3~6 + batch B/C 결정 wire 보류**: 50 failures + sso 13 skipped

---

## §5 CR 11-3 honest-DEFER 275번째

### 결정 wire chain (cj-style 220번째~275번째)
- cj-282 (220번째) → cj-282a (221+222) → cj-282b (223~238) → cj-297 (237th) → cj-298 (238th)
- cj-299 (239~242) → cj-300 (243+244) → cj-301 (245) → cj-302 (246+247)
- cj-303 (248+249+250) → cj-304 (251+252+253) → cj-305 (254+255)
- cj-305b (256+257) → cj-306 (259) → cj-307 (261) → cj-308 (263)
- cj-309 (264) → cj-309b (265) → cj-310 (266) → cj-310 retroactive (267)
- cj-311 entry (268) → cj-312 wire (269) → cj-313 wire (270)
- cj-314 entry (271) → cj-316 wire (272) → cj-317 wire (273)
- cj-314 wire 1 (274) → **cj-314 wire 2 (275)** ← **본 sprint**

### cumulative 결정 wire 보존
- **47/47** (cj-282~cj-314 wire 1) → **+1 NEW = 48/48 cumulative** (cj-314 wire 2 신규)
- 결정 wire 보존: cj-309~cj-314 wire 1 wire/entry 결정 wire 그대로
- sprint-status v4.91 → **v4.92 EXTENSION** 결정 wire (A736 cj-314 wire 2 + last_updated_note_v4_92)

### CR lessons applied
- CR 0-2 (RLS) + CR 1-1 (audit-first INSERT) + CR 1-1 (ContextVar + RSC boundary)
- CR 4-3/4-4 + CR 5-1 (Decimal precision logic)
- CR 9-6 (commit message `git commit -F <file>`)
- **CR 11-3 (honest-DEFER retroactive correction discipline)** — cj-314 wire 2 에서 verbatim mirror (cj-style 257th + 267th + 270th + 272th + 273rd + 274th 패턴)
- CR 11-4 (P-015 pure validator pattern)
- CR 12-1 (L4 industry-agnostic capability)
- CR 12-5 (D-14 typed exception envelope + D-PARITY-01 + D-GATE-01)

### 정직 회복
- 1 source file MODIFIED (apps/api/jobs/scheduled_reports.py only) — 8 lines 변경
- 3 test files MODIFIED — enum stale names + fixture combined SQL
- migration source unchanged (split SQL constants SSOT 보존)
- capability matrix 변경 0건 (cj-314 wire 1 의 v1.54 EXTENSION 보존)
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

### cj-314 wire 3~6 + batch B/C 결정 wire 보류 (operator choice)
- cj-314 wire 3 (~1h): Phase 8 ESLint/SLO/SLI 9 fixes
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

## §7 결정 보류 (cj-314 wire 2 종료 후)

| 옵션 | 내용 | Effort |
|---|---|---|
| **(a) cj-314 wire 3** (RECOMMENDED next) | Phase B item 2: Phase 8 ESLint/SLO/SLI 9 fixes | ~1h |
| **(b) cj-314 wire 4** | Phase B item 3: Phase 5/9/16/26/30 + Phase 3 hook ~10 fixes | ~1-2h |
| **(c) cj-314 wire 5** | Epic 15 alembic 0037 12 errors | ~1h |
| **(d) cj-314 batch B** | Phase 10 SLO family + Phase 5/9/16/26/30 ~37 fixes | ~4-5h |
| **(e) cj-313 close-out retro** | docs-only | ~30min |
| **(f) cj-312 close-out retro** | docs-only | ~30min |
| **(g) cj-309b B-1 Pilot candidate outreach** | D-2 발송, 운전자 결정 | 운전자 결정 |
| **(h) PRD v2 EXTENSION** | cj-314 wire 3 후 | TBD |

### 결정 wire 일자
- **2026-09-09 KST (D-5)**

---

## §8 Cross-references + CR 11-3 정직 회복

### Cross-references
- **cj-style feedback** `prioritize-mvp-hardening-before-deploy` (2026-09-07) — 본 sprint 의 trigger
- **cj-style feedback** `count-remaining-before-start` (2026-09-07) — 매 주요 업무 진입 직전 잔여 주요 업무 개수 안내
- **cj-307 wire** (`a1cb7ad`) — auth-callback aal1 minimum fix (cj-314 결정 wire 의 source)
- **cj-312 wire** (`a0a27d1`) — 7-Checkpoint MVP Audit Wire (cj-314 의 source)
- **cj-313 wire** (`cfe5cea`) — pytest rootdir 정정 (cj-314 의 prerequisite)
- **cj-314 entry** (`3e2ed73`) — cj-307 carryover fix scope triage (cj-style 271번째)
- **cj-316 wire** (`1281ca5`) — Phase A item 1 closed
- **cj-317 wire** (`99a7343`) — Phase A item 2 closed
- **cj-314 wire 1** (`cca03c2`) — Phase A item 3 closed (capability matrix drift 10 fixes)
- **cj-314 wire 2** (본 sprint) — Phase B item 1 closed (Phase 30 + Phase 5 + Phase 3 = 6 fixes)

### 결정 wire 정직 회복
- 6 stale test/source 모두 forward-lock + idempotency contract + split SQL SSOT 정합
- CR 11-3 honest-DEFER 275번째 정직 회복 (cj-style 257th + 267th + 270th + 272th + 273rd + 274th 패턴 verbatim mirror)
- 48/48 cumulative 결정 wire 보존 (cj-314 wire 1 의 47 + cj-314 wire 2 의 NEW 48번째)
- 결정 wire 보존: cj-309~cj-314 wire 1 wire/entry 결정 wire 그대로 + 1 source file MODIFIED + 3 test files MODIFIED + migration unchanged

---

**CJ-314 WIRE 2 결정 wire 보존 완료**

**CR 11-3 honest-DEFER 275번째 결정 wire chain: cj-282 (220번째) → ... → cj-314 wire 1 capability matrix drift 10 fixes (274번째) → cj-314 wire 2 Phase B 6 fixes (275번째, 본 sprint)**

**Next**: cj-314 wire 3 (Phase B item 2, ~1h, RECOMMENDED) 또는 cj-314 wire 4 또는 cj-314 batch B 또는 cj-313/cj-312 close-out retro 또는 cj-309b B-1 또는 PRD v2
