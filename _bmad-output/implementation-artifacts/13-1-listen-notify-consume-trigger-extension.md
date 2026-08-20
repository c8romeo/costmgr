---
title: LISTEN/NOTIFY Consume Trigger EXTENSION (D-10-2-DEFER-3 해소 — A39/A51 결정 wire 진입점)
status: ready-for-dev
priority: HIGH
epic: 13
story_num: 1
story_key: 13-1-listen-notify-consume-trigger-extension
baseline_commit: 3e398b9
created: 2026-08-20
updated: 2026-08-20
---

> **A39 + A51 결정 wire** (Epic 10 close-out retro 2026-08-19 §7 A39 신규 결정 + 사용자 옵션 (a) wire 진입 결정 = "Epic 13 = LISTEN/NOTIFY 전용 epic 진입" + 2026-08-20 A51 Epic 13 PRD entry 결정 wire 완료 + master PRD v2.1 → v2.2 atomic edit). 본 스토리는 D-10-2-DEFER-3 (LISTEN/NOTIFY consume 별도 epic territory 결정) ✅ RESOLVED 진입 + AD-25 cache invalidation trigger EXTENSION for close/reopen의 wire 진입점.
>
> **baseline_commit = `3e398b9`** (Epic 13 PRD entry atomic wire tip = cj-style Epic 13 1번째 진입점 docs only).
>
> **Epic 10 close-out retro** (cj-style 5번째 진입점, 2026-08-19) 완료. **A39** = LISTEN/NOTIFY consume 별도 epic territory 결정.
> **Epic 11 close-out retro 2nd** (cj-style 5번째 진입점, 2026-08-20) 완료. **A45/A46 preserved** 결정 (Epic 13 후속 story 진입).
> **A39 handoff wire** (2026-08-20) 완료. 사용자 옵션 (a) = Epic 13 = LISTEN/NOTIFY 전용 epic 진입.
> **Epic 13 PRD entry** (cj-style Epic 13 1번째 진입점, 2026-08-20) 완료. **A51** = Epic 13 PRD entry 결정 wire.
> **A52** = Story 13-1 atomic wire T1~TN 결정 wire (cj-style Epic 13 2번째 진입점 = 본 스토리).
> **PRD §F13** 신규 (LISTEN/NOTIFY Consume Trigger EXTENSION 명세) wire 완료.
> **AD-25 verbatim** cache invalidation trigger EXTENSION for close/reopen wire 진입 결정 verbatim bind.

# Story 13.1 — LISTEN/NOTIFY Consume Trigger EXTENSION

## Epic context

**Epic 13 = LISTEN/NOTIFY 전용 epic** (cj-style Epic 13 1번째 진입점 = cj-style 41번째 epic 연속 정직 회복 진입 결정 verbatim bind).

**Epic 10 PRD entry + 10-1 + 10-2 + 10-3 + 10-4 + retro** 모두 done 진입 확인 (Epic 10 close-out retro 2026-08-19). 6 NEW action items A37~A42 결정 wire:
- **A37** ✅ done (master PRD v2.1 atomic edit, commit `a4f4a08`)
- **A38** ✅ done (A35 frontend test debt dedicated sprint, commit `65b1bfb`)
- **A39** ✅ done (D-10-2-DEFER-3 LISTEN/NOTIFY consume 별도 epic territory 결정 + 사용자 옵션 (a) Epic 13 진입 결정 wire, Epic 13 PRD entry 결정 완료 2026-08-20, commit `3e398b9`)
- **A40** ✅ done (A31/A32/A33 Report #15 wire schedule = 11-6 Sprint wire, commit `197c96d`)
- **A41** ✅ done (Epic 11 carry-over sprint = 11-5 atomic wire, commit `1060360`)
- **A42** ✅ done (A36 SDR 검증 4-step 자동화 wire 보존 + Epic 11+ 적용)

**Epic 11 close-out retro 2nd** (cj-style 5번째 진입점, 2026-08-20) 완료. 6 NEW action items A43~A50 결정 wire:
- **A45/A46/A50 preserved** 결정 (Epic 13 후속 story 진입 시점에 결정)
- **A47/A48/A49 = obsolete** (정직 보정 후 done 진입)

**D-10-2-DEFER-3 ✅ RESOLVED** (LISTEN/NOTIFY consume trigger EXTENSION wire 진입 = 본 스토리).

## Sprint scope (Story 13-1 wire — cj-style Epic 13 2번째 진입점 = cj-style 42번째 epic 연속 정직 회복)

### LISTEN/NOTIFY Consume Trigger EXTENSION (PRD §F13 verbatim)

**Primary PRD ref**: §F13.1 LISTEN/NOTIFY 토폴로지 + §F13.2 4-channel eviction handlers + §F13.3 V8 determinism + cross-lang drift + §F13.4 tests + wire scope.

**Primary AD ref**: AD-25 verbatim cache invalidation trigger EXTENSION for close/reopen + AD-22 reversal INSERT cross-ref (Epic 11 wire) + AD-4 commit cross-ref (Epic 0 wire) + AD-15 cross-language conventions.

**Capability**: `Capability.LISTEN_NOTIFY` (capability matrix v1.22 NEW, industry-agnostic, 4-industry grants ✅/✅/✅/✅). 4 channels 모두 wire = `ai_cache` / `cost_engine_cache` / `fiscal_period_cache` / `closing_snapshot_cache`.

**Auth scope**: `Capability.LISTEN_NOTIFY` gate for LISTEN daemon registration per tenant. CR 12-5 D-GATE-01 inversion 적용 (capability gate through `Depends(require_capability(Capability.LISTEN_NOTIFY))`).

**D-10-2-DEFER-3 ✅ RESOLVED**: Epic 10 wire 진입 시점에 deferred 된 LISTEN/NOTIFY consume trigger EXTENSION for close/reopen 본 스토리에서 wire 진입.

### Wire 표 (cj-style Epic 13 2번째 진입점 standard — atomic single sprint T1~T8)

#### T1 — alembic 0033 NEW (PostgreSQL `pg_notify` trigger on `cache_invalidation_log` AFTER INSERT)

**Wire scope**:
- `apps/api/alembic/versions/0033_listen_notify_consume_trigger.py` NEW — `cache_invalidation_log` 테이블 AFTER INSERT 트리거 wire (`pg_notify('cache_invalidation_log', payload)` emit)
- Trigger function: `cache_invalidation_log_notify()` NEW (PL/pgSQL language, deterministic JSON serialization alphabetical key ordering)
- Payload shape: JSON `{channel: str, tenant_id: str, period_key: str, trace_id: str, correction_group_id: str}` (5 keys, alphabetical)
- `down_revision = '0032_ai_promotion_port'` (10-4 wire tip)
- V8 byte-identical determinism — payload bytes 동일 입력에 대해 동일 직렬화 보장 (트리거 함수 deterministic)

**Tests**: `tests/api/test_alembic_0033_listen_notify_consume_trigger.py` NEW ~10 cases (NOTIFY trigger source-text parsing + payload shape + JSON alphabetical ordering + down_revision + INSERT-only trigger EXTENSION + channel filter)

#### T2 — `apps/api/core/cache_invalidation_listener.py` NEW (asyncio LISTEN daemon)

**Wire scope**:
- `CacheInvalidationListener` class NEW (asyncio 기반, FastAPI lifespan 진입 시 start/shutdown 시 stop)
- `start()` method — `psycopg.AsyncConnection.listen('cache_invalidation_log')` + asyncio Task spawn
- `stop()` method — Task cancel + `unlisten('cache_invalidation_log')` + connection close
- `_consume_notifications()` private coroutine — NOTIFY 수신 → JSON payload parse → 4-channel routing → M10/M3/M11 adapter dispatch
- Reconnect/backoff: exponential (base 1s, factor 2) + jitter (±20%) + circuit breaker (5 consecutive failures → 60s cool-down) + persistent failure 시 graceful degradation (다음 restart 시 reconnect)
- `_route_to_handler(channel, payload)` — channel-specific dispatch table:
  - `ai_cache` → `M10Adapter.on_invalidate(payload)` (AI cache eviction handler)
  - `cost_engine_cache` → `M3CostEngineAdapter.on_invalidate(payload)` (cost engine in-process LRU eviction hook)
  - `fiscal_period_cache` → `M11FiscalPeriodAdapter.on_invalidate(payload)` (fiscal_period state='committed' cache invalidate)
  - `closing_snapshot_cache` → `M11ClosingSnapshotAdapter.on_invalidate(payload)` (closing_snapshot hash mismatch evict)
- Channel-specific filter 강제 — 알 수 없는 channel 도착 시 `CacheInvalidationChannelInvalidError` raise (CR 1.1 fail-fast)
- V8 determinism — payload JSON serialization `json.dumps(payload, sort_keys=True, separators=(',', ':'))` deterministic

**Tests**: `tests/api/core/test_cache_invalidation_listener.py` NEW ~12 cases (start/stop + reconnect exponential backoff + circuit breaker + 4-channel routing + channel-specific filter + payload parse + JSON determinism)

#### T3 — `apps/api/main.py` lifespan EXTENSION (FastAPI lifespan context manager 진입)

**Wire scope**:
- `apps/api/main.py` EXTENSION — `@asynccontextmanager` lifespan 진입 (`async def lifespan(app: FastAPI)`)
- lifespan 진입 시 `CacheInvalidationListener.start()` 호출 (현재 `@app.on_event("startup")` decorator 제거 + lifespan으로 통합)
- lifespan 종료 시 `CacheInvalidationListener.stop()` 호출
- `_attach_tenant_listener()` 호출 보존 (Epic 0 wire) — lifespan 진입 시 동일하게 실행
- Typed exception handler 2 NEW — `ListenerStartFailedError` → 503 `LISTENER_START_FAILED` / `ListenerStopFailedError` → 503 `LISTENER_STOP_FAILED`
- CR 12-5 D-14 envelope `{code, message_ko, details, trace_id}` verbatim

**Tests**: `tests/api/test_main_lifespan.py` NEW ~8 cases (lifespan start/stop + listener integration + tenant listener 보존 + exception handlers + envelope shape)

#### T4 — 4-channel cache eviction handlers EXTENSION (M10/M3/M11)

**Wire scope**:

**M10 AI cache eviction** (`apps/api/modules/m10_ai/service.py` EXTENSION):
- `M10Adapter.on_invalidate(payload)` method NEW
- payload parse → `(tenant_id, period_key)` 추출 → `DELETE FROM ai_insight_cache WHERE tenant_id=? AND period_key=?` 즉시 폐기
- Channel-specific filter: `channel = 'ai_cache'` ONLY (F10.1-(d) verbatim cross-channel contamination 방어)
- AD-25 verbatim 3-tuple cache key `(tenant_id, period_key, calculation_result_hash)` 보존

**M3 cost engine cache eviction** (`packages/cost_engine/...` EXTENSION):
- `M3CostEngineAdapter.on_invalidate(payload)` method NEW
- payload parse → `(tenant_id, period_key)` 추출 → in-process LRU cache eviction hook (단위: tenant_id × period_key tuple)
- Channel: `cost_engine_cache`
- AD-5 stdlib-only 보존 (NO DB write from kernel)

**M11 fiscal_period cache eviction** (`apps/api/modules/m11_close/services/fiscal_period_service.py` EXTENSION):
- `M11FiscalPeriodAdapter.on_invalidate(payload)` method NEW
- payload parse → `(tenant_id, period_key)` 추출 → `fiscal_periods` cache invalidate (state='committed' 시 in-memory cache evict)
- Channel: `fiscal_period_cache`

**M11 closing_snapshot cache eviction** (`apps/api/modules/m11_close/services/snapshot_service.py` EXTENSION):
- `M11ClosingSnapshotAdapter.on_invalidate(payload)` method NEW
- payload parse → `(tenant_id, period_key)` 추출 → `fiscal_period_snapshots` cache evict (closing_snapshot hash mismatch 시 즉시 evict)
- Channel: `closing_snapshot_cache`

**Tests**: `tests/api/test_4channel_eviction_handlers.py` NEW ~12 cases (M10/M3/M11 4 handler 모두 channel-specific filter + cross-channel contamination 거부 + payload parse + DB DELETE/in-process evict)

#### T5 — Capability gate `LISTEN_NOTIFY` 신규 row (capability matrix v1.22)

**Wire scope**:
- `apps/api/core/capability.py` EXTENSION — `Capability.LISTEN_NOTIFY` enum 1 NEW
- Industry-agnostic grants 4-industry: manufacturing ✅ + service ✅ (CR 12-1 L4 precedent — `AI_INSIGHT` 10-1 wire pattern 미러)
- `require_capability(Capability.LISTEN_NOTIFY)` Dependency 신규 wire (CR 12-5 D-GATE-01 inversion 적용)
- `docs/capability-matrix.md` EXTENSION — 1 NEW capability 행 추가 + 4-industry grants + 13-1 story reference
- `tests/integration/test_capability_matrix_v1_22_drift.py` NEW ~6 cases (LISTEN_NOTIFY row + 4-industry grants + 13-1 story coverage)
- `tests/integration/test_capability_matrix_drift.py` EXTENSION — LISTEN_NOTIFY SSOT drift detection

**Tests**: 통합 + capability matrix ~6 NEW cases

#### T6 — V8 determinism byte-identical test NEW

**Wire scope**:
- `packages/cost_engine/tests/regression_v8/fixtures/listen_notify_payload.json` NEW 골든 fixture (~30 lines)
- `tests/regression_v8/test_listen_notify_v8_determinism.py` NEW ~6 cases
  - payload bytes 동일 입력에 대해 동일하게 직렬화 (alphabetical key ordering 강제)
  - json.dumps(sort_keys=True, separators=(',', ':')) 1원 단위 byte-identical 보장
  - 4-channel routing payload shape 결정적

**Tests**: V8 determinism ~6 NEW cases

#### T7 — Cross-language drift detector EXTENSION (CR 12-5 D-PARITY-01 inversion)

**Wire scope**:
- `apps/web/lib/cache-invalidation-listener.ts` NEW TS mirror — `CacheInvalidationListenerPayload` Discriminated union + payload parse + 4-channel routing
- `tests/web/test_cache_invalidation_listener_parity.py` NEW ~8 cases (Python `cache_invalidation_listener.py` ↔ TS `cache-invalidation-listener.ts` payload shape parity)
- Drift 발생 시 drift detector test fail + 1-line ko-KR reject ("LISTEN/NOTIFY 페이로드 형식이 백엔드와 일치하지 않습니다")

**Tests**: Cross-lang parity ~8 NEW cases

#### T8 — `tests/integration/test_alembic_listen_notify_extends.py` + sprint-status sync + handoff memory

**Wire scope**:
- Sprint-status sync (`_bmad-output/implementation-artifacts/sprint-status.yaml`) — `13-1-listen-notify-consume-trigger-extension: backlog → ready-for-dev → in-progress → done` (T8 atomic commit 직전 wire)
- Handoff memory 신규 wire (`handoff-2026-08-20-13-1-done.md`)
- `docs/listen-notify-consume-trigger-extension.md` NEW (~10 sections, 10-4 template format EXTENSION)

### Expected wire 표 (cj-style Epic 13 2번째 진입점 standard)

- ~12 NEW files + ~6 MODIFIED + 1 NEW spec = ~19 files, ~800-1,200 NEW LOC
- **Tests planned**: ~30-40 NEW pytest (NOTIFY trigger SQL ~10 + listener unit ~12 + 4-channel handlers ~12 + V8 determinism ~6 + cross-lang parity ~8 + capability matrix ~6 = ~54 cases planned)
- **MAX SDR claim 갱신**: 직전 Epic 13 PRD entry wire (docs only, baseline 보존) → 13-1 wire 후 ~30-40 NEW pytest PASS 추가
- **3 honestly DEFER** (CR 11-3 17번째 epic 연속):
  - `D-13-1-DEFER-1` (a) docs 정합 master PRD v2.3 §F13 verbatim (Epic 13 close-out retro 진입 시점)
  - `D-13-1-DEFER-2` (b) retro input LISTEN/NOTIFY 실측 evidence (Epic 13 close-out retro 입력)
  - `D-13-1-DEFER-3` (c) separate epic LISTEN/NOTIFY consume 2nd batch (cross-tenant invalidation fan-out + multi-process coordination = Epic 13 후속 story 진입 결정)

### A19 cohesion pattern 8 surface EXPECTED PASS

cj-style Epic 13 2번째 진입점 standard (Epic 10 wire pattern 미러):
- Surface 1 (kernel) = T2 `cache_invalidation_listener.py` (AD-5 stdlib-only)
- Surface 2 (port) = T2 LISTEN daemon → 4-channel adapter dispatch (Protocol pattern)
- Surface 3 (db schema) = T1 alembic 0033 NOTIFY trigger
- Surface 4 (service) = T4 4-channel eviction handlers (M10/M3/M11 EXTENSION)
- Surface 5 (handler) = T3 main.py lifespan + 2 NEW exception handlers
- Surface 6 (envelope) = T3 CR 12-5 D-14 envelope `{code, message_ko, details, trace_id}` verbatim
- Surface 7 (capability) = T5 LISTEN_NOTIFY gate (capability matrix v1.22)
- Surface 8 (audit) = T4 audit-first INSERT 2-row (CR 1.1 verbatim, payload = notify envelope)

### 3중 게이트 impact EXPECTED

- (1) backend ruff scoped ~5-10 NEW (new listener + new alembic + new handlers)
- (2) capability matrix v1.22 SSOT RED→GREEN (LISTEN_NOTIFY row + 4-industry grants + 13-1 story coverage)
- (3) AD-25 verbatim bind EXTENSION (4-channel publisher EXTENSION wire 결정) + AD-22 + AD-4 cross-ref + CR 12-5 D-GATE-01 + D-PARITY-01 inversion 적용

### CR lessons applied (cj-style Epic 13 2번째 진입점 standard)

- **CR 11-3 honest-DEFER discipline** — 3 honestly DEFER preserved (D-13-1-DEFER-1/2/3)
- **CR 11-4 ko-KR.json SSOT** — N/A (backend 결정, ko-KR.json 변경 없음)
- **CR 12-5 D-GATE-01 inversion** — T5 LISTEN_NOTIFY gate 신규 wire (capability matrix v1.22)
- **CR 12-5 D-PARITY-01 inversion** — T7 cross-language drift detector EXTENSION
- **A19 cohesion pattern** — 8 surface 모두 atomic single sprint 진입 (cj-style Epic 10 wire pattern 미러)
- **A36 SDR 검증 4-step 자동화** — T8 atomic commit 직전 wire (commit prefix lint + sprint-status structure + vitest file count drift + commit consistency)
- **A42 = A36 SDR 검증 보존** — Epic 13+ 모든 stories 자동 적용 — Story 13-1 wire 시 자동 적용
- **CR 9-6 commit message discipline** — `git commit -F <file>` 사용 (PowerShell here-string 회피, D5 prevention)

## Tasks / Subtasks

본 스토리는 cj-style Epic 13 2번째 진입점 standard (atomic single sprint T1~T8):

- [ ] **Task 1: alembic 0033 NEW — PostgreSQL NOTIFY trigger wire** (AC: #1, #2)
  - [ ] Subtask 1.1: `cache_invalidation_log_notify()` trigger function NEW (PL/pgSQL, deterministic JSON serialization alphabetical)
  - [ ] Subtask 1.2: AFTER INSERT trigger on `cache_invalidation_log` NEW (`pg_notify('cache_invalidation_log', payload)`)
  - [ ] Subtask 1.3: Payload shape `{channel, tenant_id, period_key, trace_id, correction_group_id}` (5 keys, alphabetical ordering)
  - [ ] Subtask 1.4: `down_revision = '0032_ai_promotion_port'`
  - [ ] Subtask 1.5: tests/api/test_alembic_0033_listen_notify_consume_trigger.py NEW ~10 cases

- [ ] **Task 2: cache_invalidation_listener.py NEW — asyncio LISTEN daemon** (AC: #1, #2, #3)
  - [ ] Subtask 2.1: `CacheInvalidationListener` class NEW (asyncio 기반)
  - [ ] Subtask 2.2: `start()` method — `psycopg.AsyncConnection.listen()` + Task spawn
  - [ ] Subtask 2.3: `stop()` method — Task cancel + `unlisten()` + connection close
  - [ ] Subtask 2.4: `_consume_notifications()` private coroutine — NOTIFY 수신 → JSON parse → 4-channel routing
  - [ ] Subtask 2.5: Reconnect/backoff — exponential (base 1s, factor 2) + jitter (±20%) + circuit breaker (5 failures → 60s cool-down)
  - [ ] Subtask 2.6: 4-channel routing dispatch table (`ai_cache` / `cost_engine_cache` / `fiscal_period_cache` / `closing_snapshot_cache`)
  - [ ] Subtask 2.7: Channel-specific filter — unknown channel raise `CacheInvalidationChannelInvalidError`
  - [ ] Subtask 2.8: V8 determinism — `json.dumps(payload, sort_keys=True, separators=(',', ':'))` deterministic
  - [ ] Subtask 2.9: tests/api/core/test_cache_invalidation_listener.py NEW ~12 cases

- [ ] **Task 3: main.py lifespan EXTENSION — FastAPI lifespan context manager 진입** (AC: #4)
  - [ ] Subtask 3.1: `@asynccontextmanager` lifespan 진입 (`async def lifespan(app: FastAPI)`)
  - [ ] Subtask 3.2: lifespan 진입 시 `CacheInvalidationListener.start()` 호출
  - [ ] Subtask 3.3: lifespan 종료 시 `CacheInvalidationListener.stop()` 호출
  - [ ] Subtask 3.4: 기존 `@app.on_event("startup")` decorator 제거 + lifespan 통합
  - [ ] Subtask 3.5: `_attach_tenant_listener()` 보존 (lifespan 진입 시 동일 실행)
  - [ ] Subtask 3.6: 2 NEW exception handlers (`ListenerStartFailedError` 503 / `ListenerStopFailedError` 503) + CR 12-5 D-14 envelope
  - [ ] Subtask 3.7: tests/api/test_main_lifespan.py NEW ~8 cases

- [ ] **Task 4: 4-channel cache eviction handlers EXTENSION** (AC: #5, #6)
  - [ ] Subtask 4.1: M10 AI cache eviction — `apps/api/modules/m10_ai/service.py` EXTENSION (`M10Adapter.on_invalidate(payload)` + DELETE FROM ai_insight_cache)
  - [ ] Subtask 4.2: M3 cost engine cache eviction — `packages/cost_engine/...` EXTENSION (in-process LRU eviction hook)
  - [ ] Subtask 4.3: M11 fiscal_period cache eviction — `apps/api/modules/m11_close/services/fiscal_period_service.py` EXTENSION
  - [ ] Subtask 4.4: M11 closing_snapshot cache eviction — `apps/api/modules/m11_close/services/snapshot_service.py` EXTENSION
  - [ ] Subtask 4.5: tests/api/test_4channel_eviction_handlers.py NEW ~12 cases (4 handler 모두 channel-specific filter + cross-channel contamination 거부)

- [ ] **Task 5: Capability gate `LISTEN_NOTIFY` 신규 row (capability matrix v1.22)** (AC: #7)
  - [ ] Subtask 5.1: `apps/api/core/capability.py` EXTENSION — `Capability.LISTEN_NOTIFY` enum 1 NEW
  - [ ] Subtask 5.2: Industry-agnostic grants 4-industry (manufacturing ✅ + service ✅)
  - [ ] Subtask 5.3: `require_capability(Capability.LISTEN_NOTIFY)` Dependency 신규 wire (CR 12-5 D-GATE-01 inversion)
  - [ ] Subtask 5.4: `docs/capability-matrix.md` EXTENSION — 1 NEW capability 행 추가
  - [ ] Subtask 5.5: tests/integration/test_capability_matrix_v1_22_drift.py NEW ~6 cases
  - [ ] Subtask 5.6: tests/integration/test_capability_matrix_drift.py EXTENSION — LISTEN_NOTIFY SSOT drift detection

- [ ] **Task 6: V8 determinism byte-identical test NEW** (AC: #8)
  - [ ] Subtask 6.1: `packages/cost_engine/tests/regression_v8/fixtures/listen_notify_payload.json` NEW 골든 fixture
  - [ ] Subtask 6.2: tests/regression_v8/test_listen_notify_v8_determinism.py NEW ~6 cases (alphabetical ordering + 1원 단위 byte-identical + 4-channel routing payload shape 결정적)

- [ ] **Task 7: Cross-language drift detector EXTENSION (CR 12-5 D-PARITY-01 inversion)** (AC: #9)
  - [ ] Subtask 7.1: `apps/web/lib/cache-invalidation-listener.ts` NEW TS mirror (Discriminated union + payload parse + 4-channel routing)
  - [ ] Subtask 7.2: tests/web/test_cache_invalidation_listener_parity.py NEW ~8 cases (Python ↔ TS payload shape parity)
  - [ ] Subtask 7.3: Drift detector test fail + 1-line ko-KR reject ("LISTEN/NOTIFY 페이로드 형식이 백엔드와 일치하지 않습니다")

- [ ] **Task 8: 3중 게이트 FINAL CLEAN + atomic commit** (AC: ALL)
  - [ ] Subtask 8.1: backend ruff scoped 0 NEW (10-4 wire pattern 미러, automated `ruff check --fix`)
  - [ ] Subtask 8.2: capability matrix v1.22 SSOT RED→GREEN (LISTEN_NOTIFY row + 4-industry grants + 13-1 story coverage)
  - [ ] Subtask 8.3: AD-25 verbatim bind EXTENSION (4-channel publisher EXTENSION wire 결정) + AD-22 + AD-4 cross-ref
  - [ ] Subtask 8.4: A19 cohesion pattern 8 surface PASS (kernel + port + db schema + service + handler + envelope + capability + audit)
  - [ ] Subtask 8.5: A36 SDR 검증 4-step PASS (commit prefix lint + sprint-status structure + vitest file count drift + commit consistency)
  - [ ] Subtask 8.6: `git commit -F commit-msg-13-1-atomic.txt` (PowerShell here-string 회피, D5 prevention)
  - [ ] Subtask 8.7: sprint-status.yaml sync (`13-1-listen-notify-consume-trigger-extension: backlog → ready-for-dev → in-progress → done`)
  - [ ] Subtask 8.8: handoff memory 신규 wire (`handoff-2026-08-20-13-1-done.md`)
  - [ ] Subtask 8.9: docs/listen-notify-consume-trigger-extension.md NEW (~10 sections, 10-4 template format EXTENSION)

## Acceptance Criteria

- **AC #1**: NOTIFY trigger wire — PostgreSQL `cache_invalidation_log` AFTER INSERT trigger가 `pg_notify('cache_invalidation_log', payload)` emit (alembic 0033 wire). payload = `{channel, tenant_id, period_key, trace_id, correction_group_id}` (5 keys, alphabetical ordering).
- **AC #2**: LISTEN daemon wire — `apps/api/core/cache_invalidation_listener.py` asyncio 기반 start/stop (FastAPI lifespan 진입 시 start, shutdown 시 stop). reconnect/backoff exponential (base 1s, factor 2) + jitter (±20%) + circuit breaker (5 failures → 60s cool-down).
- **AC #3**: 4-channel routing wire — `ai_cache` / `cost_engine_cache` / `fiscal_period_cache` / `closing_snapshot_cache` 4 channel 모두 channel-specific eviction handler dispatch. unknown channel은 `CacheInvalidationChannelInvalidError` raise.
- **AC #4**: FastAPI lifespan wire — `@asynccontextmanager` lifespan 진입 시 `CacheInvalidationListener.start()`, 종료 시 `stop()`. 기존 `@app.on_event("startup")` decorator 제거 + 통합. 2 NEW exception handlers (`ListenerStartFailedError` 503 / `ListenerStopFailedError` 503) + CR 12-5 D-14 envelope `{code, message_ko, details, trace_id}` verbatim.
- **AC #5**: M10 AI cache eviction — `apps/api/modules/m10_ai/service.py` EXTENSION (`M10Adapter.on_invalidate(payload)` + DELETE FROM ai_insight_cache WHERE tenant_id=? AND period_key=?). F10.1-(d) verbatim `channel = 'ai_cache'` filter ONLY consume (cross-channel contamination 방어).
- **AC #6**: M3 + M11 3-channel cache eviction EXTENSION (M3 cost_engine_cache / M11 fiscal_period_cache / M11 closing_snapshot_cache) — 4 channel 모두 eviction handler wire.
- **AC #7**: Capability gate `LISTEN_NOTIFY` (capability matrix v1.22 NEW, industry-agnostic 4-industry grants ✅/✅/✅/✅). CR 12-5 D-GATE-01 inversion 적용 (`Depends(require_capability(Capability.LISTEN_NOTIFY))`).
- **AC #8**: V8 determinism byte-identical — payload JSON serialization deterministic (alphabetical key ordering + `json.dumps(sort_keys=True, separators=(',', ':'))`). 동일 입력에 대해 동일 payload bytes 보장.
- **AC #9**: Cross-language drift detector EXTENSION (CR 12-5 D-PARITY-01 inversion) — Python `cache_invalidation_listener.py` ↔ TS `cache-invalidation-listener.ts` payload shape parity. Drift 발생 시 drift detector test fail + 1-line ko-KR reject.

## Reference Documents (링크 only)

- **Master PRD v2.2** §F13 — LISTEN/NOTIFY Consume Trigger EXTENSION (verbatim)
- **Master PRD v2.2** §8.1 M10-(d) — 4-channel EXTENSION 결정 verbatim
- **Master PRD v2.2** §F10.1-(d) — 4-channel EXTENSION 결정 wire
- **Master PRD v2.2** §부록 A A39 done + A51 Epic 13 PRD entry 결정 wire + A52 Story 13-1 atomic wire 결정 wire
- **Master PRD v2.2** §15 로드맵 Epic 13 row
- **`apps/api/core/cache_invalidation_publisher.py`** — AD-25 publisher (4-channel 보존)
- **`apps/api/alembic/versions/0021_cache_invalidation_multi_channel.py`** — alembic 0021 4-channel CHECK EXTENSION
- **`apps/api/modules/m11_close/services/reopen_service.py`** — REOPEN_CHANNELS_ALL + REOPEN_CHANNELS_W2_SUBSET split (cj-style Epic 11 wire)
- **`apps/api/modules/m10_ai/service.py`** — AI cache eviction 진입점 (F10.1-(d) verbatim `channel = 'ai_cache'` filter)
- **handoff-2026-08-20-a39-listen-notify-decision-done.md** — Epic 13 진입 결정 wire
- **handoff-2026-08-20-epic-13-prd-entry-done.md** — Epic 13 PRD entry 결정 wire

## Previous Story Intelligence

본 스토리는 Epic 13 1번째 진입점 (cj-style Epic 13 1번째 진입점 = cj-style 41번째 epic 연속 정직 회복). 이전 epic story wire 패턴 (Epic 10 4 stories) 모두 done 진입 + Epic 11 6-story cycle 모두 done 진입 + Epic 12 5-story cycle 모두 done 진입. CR 11-3 honest-DEFER discipline + A36 SDR 검증 4-step 자동화 모두 보존.

cj-style Epic 13 2번째 진입점 standard = Epic 10 wire 진입 패턴 미러 (10-1/10-2/10-3/10-4 atomic single sprint T1~T8, ready-for-dev → done 단일 sprint).

## Git Intelligence

- **Latest commit**: `3e398b9` (A51 Epic 13 PRD entry atomic wire, cj-style Epic 13 1번째 진입점)
- **Patterns**: atomic single sprint T1~T8 (cj-style standard) + sprint-status + handoff memory + docs sync
- **CR 9-6**: commit message `git commit -F <file>` (PowerShell here-string 회피)

## Latest Tech Information

- **PostgreSQL LISTEN/NOTIFY**: PostgreSQL 15 (locked, walking skeleton MVP wire) — `pg_notify(channel, payload)` + `LISTEN channel` 비동기 알림 메커니즘
- **psycopg 3.x**: `AsyncConnection.listen(channel)` API for async LISTEN (psycopg2 → psycopg 3 async 마이그레이션 결정 보존, walking skeleton MVP wire 시점에 결정)
- **FastAPI lifespan**: `@asynccontextmanager` lifespan 진입 (deprecation `@app.on_event("startup")` 보존) — FastAPI 0.110+ 표준 패턴
- **asyncio Task**: `asyncio.create_task()` + `asyncio.CancelledError` 처리 + graceful shutdown

## Project Context Reference

- project-context.md: minimal (Story 1.3 implementation baseline only)
- user_skill_level: intermediate
- communication_language: korean
- document_output_language: korean

## Story Completion Status

- **Status**: ready-for-dev
- **Completion note**: Ultimate context engine analysis completed — comprehensive developer guide created (11-6 template format EXTENSION with PRD §F13 verbatim + A39/A51/A52 결정 wire + CR lessons applied)
- **다음**: bmad-dev-story 13-1 atomic wire T1~TN 진입 (cj-style Epic 13 2번째 진입점 = cj-style 42번째 epic 연속 정직 회복)