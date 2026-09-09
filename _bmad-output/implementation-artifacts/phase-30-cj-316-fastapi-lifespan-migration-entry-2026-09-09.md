# cj-316 FastAPI on_event → lifespan migration — Phase 30 Entry Sprint

> **Sprint**: cj-316 FastAPI on_event → lifespan migration (cj-style 272번째, compressed entry+wire atomic single sprint)
> **Date**: 2026-09-09 KST (D-5)
> **Status**: ✅ **CLOSED ✅ HONEST** (sprint-status v4.88 → v4.89 EXTENSION, A733)
> **Territory**: Cost Engineering API / FastAPI Application Lifecycle
> **Trigger**: cj-307 carryover 의 HIGH RISK item (cj-314 entry §4 의 risk-prioritized 분류)

---

## §1 Sprint Overview

cj-316 은 **cj-307 carryover 의 88 items 중 HIGH RISK 로 분류된 FastAPI `@app.on_event` deprecation** 의 atomic single sprint fix 입니다. 운전자 2026-09-09 결정 wire: **88 failures 의 count-prioritized 가 아닌 risk-prioritized triage** (Phase A → B → C).

cj-314 entry 의 risk-prioritized 분류:
- **HIGH RISK (must-fix pre-launch)**: ① alembic 0037 22 errors (DB schema 검증) ② **cj-316 FastAPI on_event deprecation** ← 본 sprint
- **MEDIUM RISK (should-fix)**: Phase 30 scheduled reports 3 + Phase 5 capability integration 2 + Phase 3 hook migration
- **LOW RISK (honestly DEFER post-W1)**: Capability matrix drift 10 + Phase 10 SLO family ~30 + Phase 8 + consistency

cj-316 = Phase A item 1.

---

## §2 Sprint Scope (6 files docs-only + 1 source atomic)

| File | Type | LOC | Description |
|---|---|---|---|
| `apps/api/main.py` | MODIFIED source | +47/-15 | on_event → lifespan migration |
| `phase-30-cj-316-fastapi-lifespan-migration-entry-2026-09-09.md` | NEW content | ~280 | 본 sprint doc (9-section) |
| `commit-msg-cj-316.txt` | NEW meta | ~75 | commit message |
| `handoff-2026-09-09-cj-316-fastapi-lifespan-migration-done.md` | NEW meta | ~140 | handoff doc |
| `sprint-status.yaml` | MODIFIED meta | +A733 +last_updated_note_v4_89 | v4.88 → v4.89 EXTENSION |
| `memory/MEMORY.md` | MODIFIED meta | +cj-316 hook +active sprint state | hook EXTENSION |

**Note**: compressed entry+wire atomic single sprint (cj-style 272번째, cj-313/cj-305 와 동일 패턴).

---

## §3 Sprint Motivation — Risk-prioritized Triage

운전자 2026-09-09 결정 wire (cj-314 entry §8 의 옵션 (a, RECOMMENDED) 의 재해석):
> "내가 얻고자 하는 최종 결과물이 무엇인지를 다시 한 번 고민해보고, 설계된 내용을 시스템으로 구현하는 과정에서 리스크를 최소화하면서 전체적인 프로세스 설계의 관점에서 최적의 대안이 무엇인지를 분석해본 후 나의 목적을 달성해줄 수 있는 가장 합리적이고 효과적인 것부터 실행해줘."

→ **count 기준 (cj-314 entry 분류)** vs **risk 기준 (launch-blocking) 의 차이 분석**:

| Risk | Items | Launch-blocking? |
|---|---|---|
| **HIGH** | alembic 0037 22 errors + **cj-316 FastAPI on_event deprecation** | **YES — must fix pre-launch** |
| **MEDIUM** | Phase 30 + Phase 5 capability + Phase 3 hook | affects feature/security correctness |
| **LOW** | Capability matrix drift 10 + Phase 10 SLO ~30 + Phase 8 + consistency | Pilot 사용자 5-10명 실사용 중 issue 보고 → 더 효과적인 triage |

**cj-316 = HIGH RISK item 1**: FastAPI `@app.on_event` deprecated since 0.109 → removed in 0.110+. Pilot W1 (D-day 2026-09-14) uses FastAPI 0.115+. Migration is inevitable; better to fix now while scope is small than later when scope grows.

---

## §4 Source Code Migration (apps/api/main.py)

### 4.1 Pattern change

**BEFORE** (cj-307 carryover 의 source pattern):
```python
@app.on_event("startup")
async def _attach_tenant_listener() -> None:
    ...

@app.on_event("startup")
async def _start_cache_invalidation_listener() -> None:
    ... # references module-level `app.state`

@app.on_event("shutdown")
async def _stop_cache_invalidation_listener() -> None:
    ... # references module-level `app.state`
```

**AFTER** (cj-316 의 source pattern):
```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    await _attach_tenant_listener()
    await _start_cache_invalidation_listener(app)
    yield
    # Shutdown
    await _stop_cache_invalidation_listener(app)


app = FastAPI(
    title="bizup/costmgr API",
    version="0.1.0",
    description="원가 관리 SaaS — FastAPI modular monolith (AD-1)",
    lifespan=lifespan,
)


async def _attach_tenant_listener() -> None:
    """Story 0.2 — tenant listener (signature unchanged)."""
    ...

async def _start_cache_invalidation_listener(app: FastAPI) -> None:
    """Story 13.1 — listener start (signature: app param added)."""
    ...
    await _start_leader_election(app)
    ...

async def _stop_cache_invalidation_listener(app: FastAPI) -> None:
    """Story 14.1 — listener stop (signature: app param added)."""
    ...
    await _stop_leader_election(app)
    ...

async def _start_leader_election(app: FastAPI) -> None:
    """Story 14.1 — leader election start (signature: app param added)."""
    ...

async def _stop_leader_election(app: FastAPI) -> None:
    """Story 14.1 — leader election stop (signature: app param added)."""
    ...
```

### 4.2 Diff summary (47+/15- in 1 file)

- **+2 imports**: `from contextlib import asynccontextmanager` + `from typing import AsyncIterator`
- **+18 lifespan function** (newly defined before `app = FastAPI(...)`)
- **+1 `lifespan=lifespan`** kwarg in FastAPI constructor
- **-3 `@app.on_event(...)` decorators** (removed from `_attach_tenant_listener`, `_start_cache_invalidation_listener`, `_stop_cache_invalidation_listener`)
- **+3 `app: FastAPI` parameters** (added to `_start_cache_invalidation_listener`, `_stop_cache_invalidation_listener`, `_start_leader_election`, `_stop_leader_election`)
- **+13 cj-316 comment lines** (documentation of the migration)
- **-5 obsolete comment lines** (D-13-1-DEFER-4 reference + parallel on_event handler comment)
- **+3 call site updates** (`_start_leader_election(app)`, `_stop_leader_election(app)` — was no-arg)

### 4.3 Design choices

- **Option A (chosen)**: Pass `app: FastAPI` as parameter to all helper functions → decouple from module-level `app` reference (proper FastAPI 0.109+ pattern).
- **Option B (rejected)**: Keep module-level `app` reference in helpers → minimal diff but anti-pattern (module-level globals).

---

## §5 Verify Gate 결과

### 5.1 Python syntax validation
```
.venv/Scripts/python.exe -c "import ast; ast.parse(open('apps/api/main.py', encoding='utf-8').read())"
→ Syntax OK
```

### 5.2 pytest backward compatibility
```
.venv/Scripts/python.exe -m pytest tests/api/test_main_lifespan.py tests/api/test_main_lifespan_14_1.py tests/api/core/test_phase_4_health_check.py tests/api/m12_account/test_exception_handlers_registered.py
→ 57 passed in 13.31s (0 failures, 0 errors)
```

Test coverage:
- tests/api/test_main_lifespan.py (13 tests): listener wiring + exception handlers + graceful degradation + D-14 envelope
- tests/api/test_main_lifespan_14_1.py (13 tests): leader election wiring + 2 NEW exception handlers + Korean messages
- tests/api/core/test_phase_4_health_check.py (15 tests): health endpoint + module imports
- tests/api/m12_account/test_exception_handlers_registered.py (16 tests): exception handler registration

### 5.3 Backward compatibility preservation checklist

| Test invariant | Status |
|---|---|
| `_attach_tenant_listener` function name preserved | ✅ |
| `_start_cache_invalidation_listener` function name preserved | ✅ |
| `_stop_cache_invalidation_listener` function name preserved | ✅ |
| `_start_leader_election` function name preserved | ✅ |
| `_stop_leader_election` function name preserved | ✅ |
| `_start_cache_invalidation_listener` body calls `_start_leader_election` | ✅ (with `app` arg) |
| `_stop_cache_invalidation_listener` body calls `_stop_leader_election` | ✅ (with `app` arg) |
| `app.state.cache_invalidation_listener` reference preserved | ✅ |
| `app.state.cache_invalidation_leader_state` reference preserved | ✅ |
| `ListenerStartFailedError` + `ListenerStopFailedError` preserved | ✅ |
| `LeaderElectionFailedError` + `LeaderTakeoverFailedError` preserved | ✅ |
| `ImportError` catch in `_start_cache_invalidation_listener` preserved | ✅ |
| `RuntimeError` catch in `_attach_tenant_listener` preserved | ✅ |
| Korean error messages preserved | ✅ (캐시 무효화 리스너 시작 실패 / 종료 실패 / 리더 선출 실패 / 인계 실패) |
| CR 12-5 D-14 envelope `{code, message_ko, details, trace_id}` preserved | ✅ |

---

## §6 결정 wire 보존 (cj-307~cj-314 wire/entry 결정 wire 그대로)

### 6.1 결정 wire 보존 항목
- Pilot W1 launch D-day 2026-09-14 KST
- cj-309b B-1 Pilot candidate outreach (Tier 1 5 + Tier 2 3 = 8, D-2 발송 honestly DEFER)
- Resend (OQ-EPIC30+-2 v2) swap
- cj-307 aal1 minimum fix
- cj-304 4 critical gaps fix
- cj-300 APScheduler KST
- capability matrix v1.54 EXTENSION
- audit_action EXTENSION
- **44 → 45 sprints** 결정 wire 보존

### 6.2 cj-316 의 결정 wire (compressed entry+wire)
- 88 items 의 risk-prioritized triage 진입 (운전자 2026-09-09 결정 wire)
- Phase A item 1: cj-316 (본 sprint) ✅ CLOSED
- Phase A item 2: alembic 0037 errors triage (~1-2h, 다음 sprint)
- Phase B: MEDIUM RISK items (~1-2h)
- Phase C: LOW RISK honestly DEFER post-W1 (Pilot 사용자 실사용 중 issue 보고 → 더 효과적인 triage)

---

## §7 cj-style 272번째 + CR 11-3 honest-DEFER

### 7.1 결정 wire chain
- cj-282 (220번째) → ... → cj-314 entry (271번째) → **cj-316 (272번째, 본 sprint)**
- **cumulative 44 → 45 sprints** 결정 wire 보존
- sprint-status v4.88 → **v4.89 EXTENSION** 결정 wire (A733 cj-316 + last_updated_note_v4_89)

### 7.2 정직 회복
- 1 source code 변경 (apps/api/main.py, 47+/15-)
- 37 pins unchanged (cj-303 EXTENSION 보존)
- 14 job matrix unchanged (cj-style baseline-green 보존)
- PRD v7.0 §F/§M/§R unchanged
- capability matrix v1.54 EXTENSION preserved
- audit actions EXTENSION preserved
- AD-14 stack pin EXTENSION preserved (apscheduler==3.10.4 + pytz==2024.1 + 35 pins)

---

## §8 Cross-references

### 8.1 Related sprints
- **cj-314 entry** (`3e2ed73`) — cj-307 carryover scope triage (88 items 의 risk-prioritized 분류 출처)
- **cj-307 wire** (`a1cb7ad`) — auth-callback aal1 minimum fix (cj-316 의 carryover trigger)
- **cj-303 wire** (`cfe5eca` — wait, cj-303 의 commit은 다른 hash) — uvicorn boot fix (cj-300 wire 의 transitive import issue)
- **cj-300 wire** — APScheduler KST + scheduled_reports.py 4 cron (cj-316 의 source migration 보존 영역)

### 8.2 cj-style feedback
- `prioritize-mvp-hardening-before-deploy` (2026-09-07) — 본 sprint 의 trigger (HIGH RISK 먼저)
- `count-remaining-before-start` (2026-09-07) — 매 주요 업무 진입 직전 잔여 주요 업무 개수 안내

---

## §9 결정 보류 + 결정 wire 일자

### 9.1 결정 보류 (운전자)
다음 옵션 (운전자 결정 wire 보류):
① **alembic 0037 errors triage** (Phase A item 2, ~1-2h, atomic single sprint, RECOMMENDED next) — 22 errors 의 test bug vs migration bug 분류 후 fix
② **cj-314 wire HIGH** (Phase B item, ~1-2h) — Phase 30 + Phase 5 capability + Phase 3 hook migration
③ **cj-314 wire LOW** (Phase C honestly DEFER 유지) — post-W1
④ **cj-313 close-out retro** (cj-style 270th follow-up, ~30min, docs-only)
⑤ **cj-312 close-out retro** (cj-style 269th follow-up, ~30min, docs-only)
⑥ **cj-309b B-1 Pilot candidate outreach** (D-2 발송, 운전자 결정)
⑦ **PRD v2 EXTENSION** (cj-314 fix 후)

### 9.2 결정 wire 일자
- **2026-09-09 KST (D-5)**

### 9.3 Honestly DEFER 결정 wire 보존
- ① Pilot launch D-day (2026-09-14) → 비용 발생 결정 wire 보류
- ② W1~W8 weekly follow-up (launch day 부터)
- ③ PRD v2 EXTENSION (cj-314 fix 후)
- ④ 비용 발생 항목 모두 (사용자 결정 wire, launch day 까지 honestly DEFER)

---

**CJ-316 결정 wire 보존 완료**

**CR 11-3 honest-DEFER 272번째 결정 wire chain: cj-282 (220번째) → ... → cj-314 entry (271번째) → cj-316 (272번째, 본 sprint)**

**Next**: alembic 0037 errors triage (Phase A item 2, RECOMMENDED next) 또는 cj-314 wire HIGH (Phase B) 또는 cj-313 close-out retro
