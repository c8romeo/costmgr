# cj-316 FastAPI on_event → lifespan migration — Handoff

> **Sprint**: cj-316 FastAPI on_event → lifespan migration (cj-style 272번째)
> **Date**: 2026-09-09 KST (D-5)
> **Status**: ✅ **CLOSED ✅ HONEST** (compressed entry+wire atomic single sprint, sprint-status v4.88 → v4.89 EXTENSION)
> **Source code change**: apps/api/main.py (47 insertions, 15 deletions)
> **Test verification**: 57 tests passed, 0 regressions

---

## §1 Sprint Overview

cj-316 은 **cj-307 carryover 의 HIGH RISK item** 중 첫 번째 (Phase A item 1). 운전자 2026-09-09 결정 wire: 88 failures 의 risk-prioritized triage (count-prioritized 가 아닌).

cj-314 entry 의 risk 분류에서 HIGH RISK 는 2개:
1. **alembic 0037 22 errors** (DB schema 검증) — Phase A item 2
2. **cj-316 FastAPI on_event deprecation** — Phase A item 1 ← 본 sprint

---

## §2 Sprint Scope (6 files = 1 MODIFIED source + 5 meta atomic)

| File | Type | LOC | Description |
|---|---|---|---|
| `apps/api/main.py` | MODIFIED source | +47/-15 | on_event → lifespan migration |
| `phase-30-cj-316-fastapi-lifespan-migration-entry-2026-09-09.md` | NEW content | ~280 | sprint doc 9-section §1~§9 |
| `commit-msg-cj-316.txt` | NEW meta | ~75 | commit message |
| `handoff-2026-09-09-cj-316-fastapi-lifespan-migration-done.md` | NEW meta | ~140 | 본 handoff |
| `sprint-status.yaml` | MODIFIED meta | +A733 +last_updated_note_v4_89 | v4.88 → v4.89 EXTENSION |
| `memory/MEMORY.md` | MODIFIED meta | +cj-316 hook +active sprint state | hook EXTENSION |

---

## §3 Source Code Migration — 3 on_event → lifespan

### 3.1 Pattern change (apps/api/main.py)

**BEFORE**:
```python
@app.on_event("startup")
async def _attach_tenant_listener() -> None: ...

@app.on_event("startup")
async def _start_cache_invalidation_listener() -> None: ...

@app.on_event("shutdown")
async def _stop_cache_invalidation_listener() -> None: ...
```

**AFTER**:
```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await _attach_tenant_listener()
    await _start_cache_invalidation_listener(app)
    yield
    await _stop_cache_invalidation_listener(app)

app = FastAPI(..., lifespan=lifespan)

async def _start_cache_invalidation_listener(app: FastAPI) -> None: ...
async def _stop_cache_invalidation_listener(app: FastAPI) -> None: ...
async def _start_leader_election(app: FastAPI) -> None: ...
async def _stop_leader_election(app: FastAPI) -> None: ...
```

### 3.2 Helper function signature changes
- `_attach_tenant_listener()` — signature unchanged (no `app.state` reference)
- `_start_cache_invalidation_listener(app: FastAPI)` — added `app` parameter
- `_stop_cache_invalidation_listener(app: FastAPI)` — added `app` parameter
- `_start_leader_election(app: FastAPI)` — added `app` parameter
- `_stop_leader_election(app: FastAPI)` — added `app` parameter

### 3.3 Imports added
```python
from contextlib import asynccontextmanager
from typing import AsyncIterator
```

---

## §4 Verify Gate 결과

### 4.1 Python syntax
- `python ast.parse` → Syntax OK ✅

### 4.2 pytest backward compatibility (57 tests, 0 regressions)
- tests/api/test_main_lifespan.py: 13 passed ✅
- tests/api/test_main_lifespan_14_1.py: 13 passed ✅
- tests/api/core/test_phase_4_health_check.py: 15 passed ✅
- tests/api/m12_account/test_exception_handlers_registered.py: 16 passed ✅
- **Total**: 57 passed in 13.31s

### 4.3 Backward compatibility invariants preserved
- ✅ Function names: `_attach_tenant_listener`, `_start_cache_invalidation_listener`, `_stop_cache_invalidation_listener`, `_start_leader_election`, `_stop_leader_election`
- ✅ Call site relationships: `_start_cache_invalidation_listener` body calls `_start_leader_election`, `_stop_cache_invalidation_listener` body calls `_stop_leader_election`
- ✅ app.state bindings: `app.state.cache_invalidation_listener` + `app.state.cache_invalidation_leader_state`
- ✅ Exception handlers: `ListenerStartFailedError`, `ListenerStopFailedError`, `LeaderElectionFailedError`, `LeaderTakeoverFailedError`
- ✅ Error catches: `ImportError` in listener start, `RuntimeError` in tenant listener
- ✅ Korean error messages: 캐시 무효화 리스너 시작 실패 / 종료 실패 / 리스너 리더 선출 실패 / 인계 실패
- ✅ CR 12-5 D-14 envelope: `{code, message_ko, details, trace_id}`

---

## §5 결정 wire 보존

### 5.1 결정 wire 보존 항목
- Pilot W1 launch D-day 2026-09-14 KST
- cj-309b B-1 Pilot candidate outreach (Tier 1 5 + Tier 2 3 = 8, D-2 발송 honestly DEFER)
- Resend (OQ-EPIC30+-2 v2) swap
- cj-307 aal1 minimum fix
- cj-304 4 critical gaps fix
- cj-300 APScheduler KST
- capability matrix v1.54 EXTENSION
- audit_action EXTENSION
- **44 → 45 sprints** 결정 wire 보존

### 5.2 cj-316 의 결정 wire (Phase A item 1)
- 88 items 의 risk-prioritized triage 진입 (운전자 2026-09-09 결정 wire)
- Phase A item 1 (cj-316) ✅ CLOSED
- Phase A item 2 (alembic 0037 errors triage) — 다음 sprint
- Phase B (MEDIUM RISK items) — pre-launch
- Phase C (LOW RISK honestly DEFER post-W1)

---

## §6 CR 11-3 honest-DEFER 272번째

### 6.1 결정 wire chain
- cj-282 (220번째) → ... → cj-314 entry (271번째) → **cj-316 (272번째, 본 sprint)**
- **cumulative 44 → 45 sprints** 결정 wire 보존
- sprint-status v4.88 → **v4.89 EXTENSION** 결정 wire (A733 + last_updated_note_v4_89)

### 6.2 정직 회복
- 1 source code 변경 (apps/api/main.py 47+/15-)
- 37 pins unchanged (cj-303 EXTENSION 보존)
- 14 job matrix unchanged (cj-style baseline-green 보존)
- PRD v7.0 §F/§M/§R unchanged
- capability matrix v1.54 EXTENSION preserved
- audit actions EXTENSION preserved

---

## §7 결정 보류 + 결정 wire 일자

### 7.1 결정 보류 (운전자)
다음 옵션 (운전자 결정 wire 보류):
① **alembic 0037 errors triage** (Phase A item 2, ~1-2h, atomic single sprint, RECOMMENDED next)
② **cj-314 wire HIGH** (Phase B item, ~1-2h)
③ **cj-314 wire LOW** (Phase C honestly DEFER 유지) — post-W1
④ **cj-313 close-out retro** (~30min, docs-only)
⑤ **cj-312 close-out retro** (~30min, docs-only)
⑥ **cj-309b B-1 Pilot candidate outreach** (D-2 발송)
⑦ **PRD v2 EXTENSION** (cj-314 fix 후)

### 7.2 결정 wire 일자
- **2026-09-09 KST (D-5)**

### 7.3 Honestly DEFER 결정 wire 보존
- ① Pilot launch D-day (2026-09-14) → 비용 발생 결정 wire 보류
- ② W1~W8 weekly follow-up (launch day 부터)
- ③ PRD v2 EXTENSION (cj-314 fix 후)
- ④ 비용 발생 항목 모두 (사용자 결정 wire, launch day 까지 honestly DEFER)

---

## §8 Cross-references + CR 11-3 정직 회복

### Cross-references
- **cj-style feedback** `prioritize-mvp-hardening-before-deploy` (2026-09-07) — 본 sprint 의 trigger
- **cj-style feedback** `count-remaining-before-start` (2026-09-07) — 매 주요 업무 진입 직전 잔여 주요 업무 개수 안내
- **cj-314 entry** (`3e2ed73`) — 88 items 의 risk-prioritized 분류 출처
- **cj-307 wire** (`a1cb7ad`) — cj-316 의 carryover trigger
- **cj-303 wire** — AD-14 stack pin EXTENSION (cj-316 의 transitive 보존 영역)
- **cj-300 wire** — APScheduler KST (cj-316 의 source migration 보존 영역)
- **cj-316** (본 sprint) — FastAPI on_event → lifespan migration (cj-style 272번째)

### 결정 wire 정직 회복
- 1 source code 변경 (apps/api/main.py 47+/15-)
- 결정 wire 보존: cj-307~cj-314 wire/entry 결정 wire 그대로
- CR 11-3 honest-DEFER 272번째 정직 회복 (Phase A item 1 closed, Phase A item 2 + B + C 결정 wire 보존)

---

**CJ-316 결정 wire 보존 완료**

**CR 11-3 honest-DEFER 272번째 결정 wire chain: cj-282 (220번째) → ... → cj-314 entry (271번째) → cj-316 (272번째, 본 sprint)**

**Next**: alembic 0037 errors triage (Phase A item 2, RECOMMENDED next) 또는 cj-314 wire HIGH (Phase B)
