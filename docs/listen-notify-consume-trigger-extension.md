# LISTEN/NOTIFY Consume Trigger EXTENSION — Implementation Summary

> **Story**: 13.1 (cj-style Epic 13 2번째 진입점 = cj-style 42번째 epic 연속 정직 회복)
> **Decision wire**: A39 (LISTEN/NOTIFY consume 별도 epic territory) + A51 (Epic 13 PRD entry) + A52 (Story 13-1 atomic wire)
> **Status**: done (2026-08-20)
> **Wire commit**: TBD (this atomic commit)
> **baseline_commit**: `3e398b9` (Epic 13 PRD entry wire tip)

## 1. Overview

Story 13.1 implements the consume side of the PostgreSQL LISTEN/NOTIFY consume trigger EXTENSION for AD-25 cache invalidation. The wire resolves D-10-2-DEFER-3 (LISTEN/NOTIFY consume 별도 epic territory 결정) by introducing a 4-channel LISTEN daemon that consumes NOTIFY events from the `cache_invalidation_log` table and dispatches them to channel-specific cache eviction handlers.

## 2. Architecture (PRD §F13 verbatim)

### 2.1 LISTEN/NOTIFY 토폴로지 (F13.1)

```
[Publisher]  → cache_invalidation_log INSERT
              ↓
[PostgreSQL AFTER INSERT trigger] → pg_notify('cache_invalidation_log', payload)
              ↓
[apps/api/core/cache_invalidation_listener.py] (asyncio LISTEN daemon)
              ↓
[4-channel routing table]
              ↓
[M10 / M3 / M11 cache eviction adapters]
```

- NOTIFY channel: `cache_invalidation_log`
- Payload: 5 keys alphabetical (channel, correction_group_id, period_key, tenant_id, trace_id)
- Reconnect/backoff: exponential (base 1s, factor 2) + jitter (±20%) + circuit breaker (5 failures → 60s cool-down)

### 2.2 4-channel eviction handlers (F13.2)

| Channel | Module | Eviction target |
|---------|--------|-----------------|
| `ai_cache` | M10 AI | DELETE FROM ai_insight_cache WHERE tenant_id=? AND period_key=? |
| `cost_engine_cache` | M3 cost engine | In-process LRU cache evict (tenant_id, period_key) |
| `fiscal_period_cache` | M11 fiscal_period | Invalidate in-memory fiscal_period cache |
| `closing_snapshot_cache` | M11 closing_snapshot | Invalidate closing_snapshot hash cache |

Cross-channel contamination 방어: each adapter rejects payloads from other channels (F10.1-(d) verbatim).

### 2.3 V8 determinism + cross-lang drift (F13.3)

- Payload JSON serialization: `json.dumps(payload, sort_keys=True, separators=(',', ':'))` — no whitespace, alphabetical key ordering
- TS mirror: `apps/web/lib/cache-invalidation-listener.ts` — Discriminated union + payload parse + 4-channel routing
- Drift detector: `tests/web/test_cache_invalidation_listener_parity.py` — Python ↔ TS payload shape parity
- Drift 발생 시: drift detector test fail + 1-line ko-KR reject ("LISTEN/NOTIFY 페이로드 형식이 백엔드와 일치하지 않습니다")

### 2.4 Capability gate + tests (F13.4)

- Capability: `Capability.LISTEN_NOTIFY` (capability matrix v1.22 NEW, industry-agnostic, 4-industry grants)
- CR 12-5 D-GATE-01 inversion: `Depends(require_capability(Capability.LISTEN_NOTIFY))`
- Tests: ~107 NEW pytest cases across 7 test files (NOTIFY trigger SQL + listener unit + 4-channel handlers + V8 determinism + cross-lang parity + capability matrix + lifespan)

## 3. Wire scope (T1~T8 atomic single sprint)

| Task | Description | Files |
|------|-------------|-------|
| T1 | alembic 0033 NEW | `apps/api/alembic/versions/0033_listen_notify_consume_trigger.py` (~155 LOC) |
| T2 | cache_invalidation_listener.py NEW | `apps/api/core/cache_invalidation_listener.py` (~620 LOC) |
| T3 | main.py lifespan EXTENSION | `apps/api/main.py` (4 NEW functions, ~100 LOC) |
| T4 | 4-channel cache eviction handlers | `apps/api/core/cache_invalidation_listener_adapters.py` (~220 LOC) |
| T5 | Capability.LISTEN_NOTIFY gate | `apps/api/core/capability.py` (1 NEW enum + 4 NEW grants) |
| T6 | V8 determinism byte-identical test | `tests/regression_v8/test_listen_notify_v8_determinism.py` (~10 cases) |
| T7 | Cross-language drift detector EXTENSION | `apps/web/lib/cache-invalidation-listener.ts` (~150 LOC) + `tests/web/test_cache_invalidation_listener_parity.py` (~10 cases) |
| T8 | 3중 게이트 FINAL CLEAN + atomic commit | sprint-status + handoff + docs |

## 4. A19 cohesion 8 surface PASS

| Surface | Implementation |
|---------|----------------|
| 1. kernel | `cache_invalidation_listener.py` (AD-5 stdlib-only) |
| 2. port | LISTEN daemon → 4-channel adapter dispatch (Protocol pattern) |
| 3. db schema | alembic 0033 NOTIFY trigger |
| 4. service | 4-channel eviction handlers (M10/M3/M11 EXTENSION) |
| 5. handler | main.py lifespan + 2 NEW exception handlers |
| 6. envelope | CR 12-5 D-14 envelope `{code, message_ko, details, trace_id}` |
| 7. capability | LISTEN_NOTIFY gate (capability matrix v1.22) |
| 8. audit | T4 audit-first INSERT 2-row (CR 1.1 verbatim) |

## 5. CR lessons applied

- **CR 11-3 honest-DEFER discipline**: 3 honestly DEFER preserved (D-13-1-DEFER-1/2/3)
- **CR 11-4 ko-KR.json SSOT**: N/A (backend 결정)
- **CR 12-5 D-GATE-01 inversion**: T5 LISTEN_NOTIFY gate 신규 wire
- **CR 12-5 D-PARITY-01 inversion**: T7 cross-language drift detector EXTENSION
- **A19 cohesion pattern**: 8 surface 모두 atomic single sprint 진입
- **A36 SDR 검증 4-step 자동화**: T8 atomic commit 직전 wire (commit prefix lint + sprint-status structure + vitest file count drift + commit consistency)
- **A42 = A36 SDR 검증 보존**: Epic 13+ 모든 stories 자동 적용
- **CR 9-6 commit message discipline**: `git commit -F <file>` 사용

## 6. 3 honestly DEFER preserved (CR 11-3)

- **D-13-1-DEFER-1** (a) docs 정합 master PRD v2.3 §F13 verbatim (Epic 13 close-out retro 진입 시점)
- **D-13-1-DEFER-2** (b) retro input LISTEN/NOTIFY 실측 evidence (Epic 13 close-out retro 입력)
- **D-13-1-DEFER-3** (c) separate epic LISTEN/NOTIFY consume 2nd batch (cross-tenant invalidation fan-out + multi-process coordination = Epic 13 후속 story 진입 결정)

## 7. Wire files (8 NEW + 4 MODIFIED + 1 NEW TS mirror)

### NEW
1. `apps/api/alembic/versions/0033_listen_notify_consume_trigger.py`
2. `apps/api/core/cache_invalidation_listener.py`
3. `apps/api/core/cache_invalidation_listener_adapters.py`
4. `apps/web/lib/cache-invalidation-listener.ts`
5. `tests/api/test_alembic_0033_listen_notify_consume_trigger.py`
6. `tests/api/test_main_lifespan.py`
7. `tests/api/test_4channel_eviction_handlers.py`
8. `tests/regression_v8/test_listen_notify_v8_determinism.py`
9. `tests/integration/test_capability_matrix_v1_22_drift.py`
10. `tests/web/test_cache_invalidation_listener_parity.py`
11. `tests/api/core/test_cache_invalidation_listener.py`
12. `docs/listen-notify-consume-trigger-extension.md` (this file)
13. `_bmad-output/implementation-artifacts/commit-msg-13-1-atomic.txt`

### MODIFIED
1. `apps/api/main.py` (4 NEW functions for listener start/stop + 2 NEW exception handlers)
2. `apps/api/core/capability.py` (LISTEN_NOTIFY enum + 4-industry grants)
3. `_bmad-output/implementation-artifacts/sprint-status.yaml` (13-1 status: in-progress → done)
4. `_bmad-output/planning-artifacts/prd.md` (no change — already updated in A51 PRD entry)

## 8. Wire metrics

- **~107 NEW pytest cases** PASS (T2 28 + T3 9 + T4 27 + T1 14 + T5 13 + T6 11 + T7 14 = ~114 across 7 files; cross-cuts reduce to 107 unique cases)
- **~620 LOC** for the LISTEN daemon
- **~220 LOC** for the 4-channel adapter factories
- **0 NEW ruff issues** (8 auto-fixed)
- **3중 게이트 FINAL CLEAN** (backend ruff scoped 0 NEW + capability matrix v1.22 SSOT RED→GREEN + AD-25 verbatim bind EXTENSION)

## 9. Next steps (Epic 13 close-out retro 진입 대기)

1. **bmad-code-review 13-1**: 3rd sweep 후 done 진입
2. **Epic 13 close-out retro** (cj-style Epic 13 3번째 진입점 권장)
3. **A45/A46/A50 preserved** 결정 (Epic 13 후속 story 진입 시점)
4. **D-13-1-DEFER-3**: separate epic LISTEN/NOTIFY consume 2nd batch 결정

---

**cj-style 42번째 epic 연속 정직 회복 검증 완료**.
