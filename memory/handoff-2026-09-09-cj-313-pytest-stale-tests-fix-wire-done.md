# cj-313 pytest rootdir 정정 — Handoff

> **Sprint**: cj-313 pytest rootdir 정정 (cj-style 270번째)
> **Date**: 2026-09-09 KST (D-5)
> **Status**: ✅ **CLOSED ✅ HONEST** (compressed entry+wire, sprint-status v4.86 → v4.87 EXTENSION)
> **Next**: cj-314 cj-307 carryover fix (HIGH severity) 또는 cj-316 FastAPI on_event → lifespan migration (HIGH severity)

---

## §1 Sprint Overview

cj-313 sprint 는 **cj-312 audit finding 2.1 의 정직 회복** + **7 stale tests 정정** + **pytest invocation docs** 입니다.
- **cj-312 audit finding 2.1** ("apps/api/tests/ 부재 → testpaths EXTENSION") 가 **WRONG** 정직 인정
- **실제 root cause**: 7 stale tests (cj-305b Resend swap 정직 회복 안 됨 + capability matrix drift + SLO test + audit_action test + scheduled_reports syntax error)
- **결과**: 5418 tests + 7 errors → **5554 tests + 0 errors** (+136 tests recovered)

---

## §2 Sprint Scope (13 files)

| File | Type | LOC | Description |
|---|---|---|---|
| `phase-30-cj-313-pytest-stale-tests-fix-wire-2026-09-09.md` | NEW content | ~350 | 9-section §1~§9 sprint doc |
| `commit-msg-cj-313.txt` | NEW meta | ~85 | commit message |
| `handoff-2026-09-09-cj-313-pytest-stale-tests-fix-wire-done.md` | NEW meta | ~150 | 본 handoff (7-section) |
| `pyproject.toml` | MODIFIED project | +12 LOC comment | canonical pytest invocation docs |
| `tests/integration/test_phase_30_exports_email.py` | MODIFIED tests | Resend swap test 정직 회복 | cj-305b test swap 정직 회복 |
| `tests/api/core/test_phase_10_audit_action.py` | MODIFIED tests | stale imports 제거 | is_valid_audit_action + normalize_audit_action |
| `tests/api/core/test_phase_10_slo_burn_rate_evaluator.py` | MODIFIED tests | stale imports 제거 | BURN_RATE_THRESHOLDS |
| `tests/api/core/test_phase_10_slo_dsl.py` | MODIFIED tests | multiple stale imports 제거 | BadRequest/Conflict/UnprocessableEntity + VALID_* prefix + build_slo_definition |
| `tests/integration/test_phase_30_scheduled_reports.py` | MODIFIED tests | syntax error + stale import | DISPATCH_CRON_EXPRESSIONS + ALL_REPORT_TYPES |
| `tests/integration/test_capability_matrix_v1_32_drift.py` | MODIFIED tests | Industry enum rename | MANUFACTURING_SERVICE + MANUFACTURING_SERVICE_OTHER |
| `tests/integration/test_capability_matrix_v1_35_drift.py` | MODIFIED tests | underscore prefix | _INDUSTRY_CAPABILITIES |
| `sprint-status.yaml` | MODIFIED meta | +A731 +last_updated_note_v4_87 | v4.86 → v4.87 EXTENSION |
| `memory/MEMORY.md` | MODIFIED meta | +cj-313 hook +active sprint state EXTENSION | hook EXTENSION |

---

## §3 cj-312 audit finding 2.1 의 정직 회복

### cj-312 audit 의 claim (WRONG)
> "apps/api/tests/ 부재의 root cause 정직 회복, testpaths=["tests","apps/api"] EXTENSION"

### 실제 verification 결과 (CORRECT)
- pytest config (`testpaths=["tests"]`) 가 CORRECT — 변경 불필요
- `apps/api/tests/` 부재는 사실이지만 pytest config 와 무관
- pytest 는 project root 의 `tests/` (404 files) 를 정상적으로 scan
- 실제 root cause = **7 stale tests 의 import errors**

### 정직 회복 rationale
- CR 11-3 honest-DEFER retroactive correction discipline (cj-style 257th + 267th 의 cj-305b/cj-310retro 패턴 verbatim mirror)
- 결정 wire 보존: cj-309~cj-312 wire 결정 wire 그대로
- **compressed entry+wire 결정 wire** (cj-style 270번째) — cj-312 audit 정직 회복을 본 sprint 의 본질로 삼음

---

## §4 7 Stale Tests 정정 내역

### Fix #1: test_phase_30_exports_email.py (cj-305b swap 정직 회복)
- PostmarkProvider → ResendProvider (4 test methods + env var + error code + URL + header)
- **결과**: 0 tests → 32 tests recovered

### Fix #2: test_phase_10_audit_action.py
- is_valid_audit_action + normalize_audit_action import 제거
- **결과**: 1 error → 0 errors

### Fix #3: test_phase_10_slo_burn_rate_evaluator.py
- BURN_RATE_THRESHOLDS import 제거
- **결과**: 1 error → 0 errors

### Fix #4: test_phase_10_slo_dsl.py
- BadRequest → BadRequestError, Conflict → ConflictError, UnprocessableEntity → UnprocessableEntityError
- SLI_TYPES → VALID_SLI_TYPES, WINDOWS → VALID_WINDOWS, BUDGET_POLICIES → VALID_BUDGET_POLICIES, REGIONS → VALID_REGIONS
- build_slo_definition import 제거
- **결과**: 1 error → 0 errors

### Fix #5: test_phase_30_scheduled_reports.py
- DISPATCH_CRON_EXPRESSIONS syntax error (walrus operator) → 분리 import
- ALL_REPORT_TYPES import path 정정 (scheduled_reports → scheduled_serializers)
- **결과**: 2 errors → 0 errors

### Fix #6: test_capability_matrix_v1_32_drift.py
- Industry.MFG_AND_SERVICE → MANUFACTURING_SERVICE (2 occurrences)
- Industry.MFG_AND_SERVICE_AND_OTHER → MANUFACTURING_SERVICE_OTHER
- **결과**: 1 error → 0 errors

### Fix #7: test_capability_matrix_v1_35_drift.py
- INDUSTRY_CAPABILITIES → _INDUSTRY_CAPABILITIES (import + body usage)
- **결과**: 1 error → 0 errors

---

## §5 pyproject.toml [tool.pytest.ini_options] canonical invocation EXTENSION

### 추가 변경
```toml
# Canonical invocation (cj-313 wire 결정 wire, 2026-09-09):
#   `.venv\Scripts\python.exe -m pytest`  (project root)
#
# Why not `uv run pytest`? — uv trampoline on Windows env occasionally
# returns "uv trampoline failed to canonicalize script path" for pytest.
#
# Why not `python -m pytest`? — bare `python` resolves to system Python
# (3.14 on this dev box) which lacks asyncpg and surfaces false errors.
```

### 정직 회복
- cj-312 audit 의 "uv trampoline" issue 가 **uv bug 가 아니라 invocation pattern 문제** 정직 회복
- 결정 wire 보존: pyproject.toml 의 testpaths=["tests"] 그대로

---

## §6 CR 11-3 honest-DEFER 270번째

### 결정 wire chain (cj-style 220번째~270번째)
- cj-282 (220번째) → cj-282a (221+222) → cj-282b (223~238) → cj-297 (237th) → cj-298 (238th)
- cj-299 (239~242) → cj-300 (243+244) → cj-301 (245) → cj-302 (246+247)
- cj-303 (248+249+250) → cj-304 (251+252+253) → cj-305 (254+255)
- cj-305b (256+257) → cj-306 (259) → cj-307 (261) → cj-308 (263)
- cj-309 (264) → cj-309b (265) → cj-310 (266) → cj-310 retroactive correction (267)
- cj-311 entry (268) → cj-312 wire (269)
- **cj-313 (270)** ← **본 sprint**

### cumulative 결정 wire 보존
- **42/42** (cj-282~cj-312) → **+1 NEW = 43/43 cumulative** (cj-313 wire 신규)
- 결정 wire 보존: cj-309~cj-312 wire 결정 wire 그대로
- sprint-status v4.86 → **v4.87 EXTENSION** 결정 wire (A731 cj-313 + last_updated_note_v4_87)

### 정직 회복
- source code 변경 0건 (cj-313 wire 는 tests only sprint)
- 37 pins unchanged (cj-303 EXTENSION 보존)
- PRD v7.0 §F/§M/§R unchanged
- capability matrix v1.54 EXTENSION preserved
- audit actions EXTENSION preserved

---

## §7 Next unblocked 결정 wire 보류 + 결정 wire 일자

### 결정 보류 5개 옵션
| 옵션 | 내용 | 예상 effort |
|---|---|---|
| **(a) cj-314 cj-307 carryover fix** | HIGH severity (cj-style 271번째) — pytest 0 errors 회복 후 32+22+3 failures triage | ~2h |
| **(b) cj-316 FastAPI on_event → lifespan** | HIGH severity (cj-style 272번째) — source code migration | ~1-2h |
| **(c) cj-313 close-out retro** | docs-only (cj-style 270th follow-up) | ~30min |
| **(d) PRD v2 EXTENSION** | audit 결과 gap 의 우선순위 결정 후 | TBD |
| **(e) carryover honestly DEFER 유지** | cj-303 4건 + PRE-EXISTING 6건 | 0 effort |

### 결정 wire 일자
- **2026-09-09 KST (D-5)**

### Honestly DEFER 결정 wire
- ① Pilot launch D-day (2026-09-14) → 비용 발생 결정 wire 보류
- ② W1~W8 weekly follow-up (launch day 부터)
- ③ PRD v2 EXTENSION (cj-314/cj-316 fix 후)
- ④ 비용 발생 항목 모두 (사용자 결정 wire, launch day 까지 honestly DEFER)

---

## §8 Cross-references + CR 11-3 정직 회복

### Cross-references
- **cj-style feedback** `prioritize-mvp-hardening-before-deploy` (2026-09-07) — 본 sprint 의 trigger
- **cj-style feedback** `count-remaining-before-start` (2026-09-07) — 매 주요 업무 진입 직전 잔여 주요 업무 개수 안내
- **cj-305b wire** (`53b8bbf`) — Postmark → Resend swap (Fix #1 의 결정 wire 출처)
- **cj-303 wire** — ALL_REPORT_TYPES stale import path 정정 pattern (Fix #5 의 패턴 보존)
- **cj-307 wire** (`a1cb7ad`) — auth-callback aal1 minimum fix (cj-314 결정 wire 의 source)
- **cj-310 retroactive correction** (`6972571`) — headline 정직 회복 (cj-313 의 정직 회복 패턴 출처)
- **cj-311 entry** (`69d7d72`) — 7-Checkpoint MVP Audit Entry
- **cj-312 wire** (`a0a27d1`) — 7-Checkpoint Audit Wire (본 sprint 의 retroactive correction 대상)
- **cj-313 wire** (본 sprint) — 7 stale tests 정정 + pytest invocation docs (cj-style 270번째)

### 결정 wire 정직 회복
- 7 stale tests 모두 정정: 5418 + 7 errors → 5554 + 0 errors (+136 tests recovered)
- 결정 wire 보존: cj-309~cj-312 wire 결정 wire 그대로 + 0 source code 변경
- CR 11-3 honest-DEFER 270번째 정직 회복 (compressed entry+wire 패턴)

---

**CJ-313 WIRE 결정 wire 보존 완료**

**CR 11-3 honest-DEFER 270번째 결정 wire chain: cj-282 (220번째) → ... → cj-312 wire (269번째) → cj-313 (270번째, 본 sprint)**

**Next**: cj-314 cj-307 carryover fix (HIGH severity) 또는 cj-316 FastAPI on_event → lifespan migration (HIGH severity)
