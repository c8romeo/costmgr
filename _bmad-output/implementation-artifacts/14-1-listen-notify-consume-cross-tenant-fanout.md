---
title: LISTEN/NOTIFY Consume 2nd Batch (Cross-Tenant Invalidation Fan-Out + Multi-Process Coordination)
status: ready-for-dev
priority: HIGH
epic: 14
story_num: 1
story_key: 14-1-listen-notify-consume-cross-tenant-fanout
baseline_commit: 9c69fa1879302928430f1f2da2d7a45f712d5c2e
created: 2026-08-20
updated: 2026-08-20
---

> **A53 + A57 + A58 + A59 결정 wire** (Epic 13 close-out retro 2026-08-20 §7 A53 + 사용자 옵션 (a) Epic 14 진입 결정 = cj-style Epic 14 1~3번째 진입점 결정 보존 + A57 Epic 14 PRD entry 결정 wire 완료 + A58 AD-25 EXTENSION 5+ channels 결정 wire + A59 capability matrix v1.23 EXTENSION 2 NEW rows 결정 wire + master PRD v2.4 → v2.5 atomic edit). 본 스토리는 **D-13-1-DEFER-3 ✅ RESOLVED 진입** (separate epic LISTEN/NOTIFY consume 2nd batch territory 진입 = Epic 14 = cross-tenant invalidation fan-out + multi-process coordination). **Story 14-1 = cj-style Epic 14 2번째 진입점 = cj-style 46번째 epic 연속 정직 회복 진입 결정**.
>
> **PRD §F14 신규** (LISTEN/NOTIFY Consume 2nd Batch EXTENSION 명세) wire 완료. AD-25 cache invalidation trigger EXTENSION 4-channel → 5+ channels 결정 wire 진입 verbatim bind. capability matrix v1.22 → v1.23 EXTENSION 2 NEW rows 결정 wire 진입 verbatim bind.
>
> **Epic 13 PRD entry** (cj-style Epic 13 1번째 진입점 = cj-style 41번째) 완료. **Story 13.1 atomic wire** (cj-style Epic 13 2번째 진입점 = cj-style 42번째) 완료 (commit `f2ea2f6`, 17 files, ~107 NEW pytest PASS). **Epic 13 close-out retro** (cj-style Epic 13 4번째 진입점 = cj-style 43번째) 완료. **A57/A58/A59 결정 wire** (cj-style Epic 13 5번째 진입점 = cj-style Epic 13 carry-over 17번째 docs only) 완료. master PRD v2.4 → v2.5 atomic edit (Epic 14 PRD entry).

# Story 14.1 — LISTEN/NOTIFY Consume 2nd Batch (Cross-Tenant Invalidation Fan-Out + Multi-Process Coordination)

## Epic context

**Epic 14 = LISTEN/NOTIFY Consume 2nd Batch** (cj-style Epic 14 1번째 진입점 = cj-style 45번째 epic 연속 정직 회복 진입 결정 verbatim bind).

**Epic 13 PRD entry + 13-1 wire + Epic 13 close-out retro** 모두 done 진입 확인. A39/A51/A52 + A53+A54+A55+A56 결정 wire:
- **A39** ✅ done (D-10-2-DEFER-3 LISTEN/NOTIFY consume 별도 epic territory 결정)
- **A51** ✅ done (Epic 13 PRD entry 결정 wire, master PRD v2.1 → v2.2)
- **A52** ✅ done (Story 13-1 atomic wire, commit `f2ea2f6`)
- **A53** ✅ done (D-13-1-DEFER-3 separate epic LISTEN/NOTIFY consume 2nd batch = Epic 14 진입 결정, 옵션 (a) Epic 14 진입 결정 wire, master PRD v2.2 → v2.3)
- **A54** ✅ done (master PRD v2.2 → v2.3 atomic edit, D-13-1-DEFER-1 ✅ RESOLVE)
- **A55** ✅ done (LISTEN/NOTIFY 실측 evidence 정합 sweep, D-13-1-DEFER-2 ✅ RESOLVE)
- **A56** ✅ done + preserved (A42 A36 SDR 검증 4-step 보존 + Epic 14+ 적용 결정)
- **A45/A46 preserved** (옵션 (a) Epic 14 follow-up sprint 진입 결정, bundled into ONE Epic 14 carry-over sprint = cj-style Epic 14 3번째 진입점 진입 시점)

**Epic 14 PRD entry** (cj-style Epic 14 1번째 진입점 = cj-style 45번째) 완료. **A57/A58/A59 결정 wire**:
- **A57** ✅ done (master PRD v2.4 → v2.5 atomic edit, §F14 신규 + §15 로드맵 Epic 14 row in-progress + §부록 A A57+A58+A59 결정)
- **A58** ✅ done (AD-25 EXTENSION 4-channel → 5+ channels 결정 wire, `cross_tenant_fanout` 1 channel 추가 + 7-key alphabetical payload EXTENSION + Multi-process coordination Option 1 결정: PostgreSQL LISTEN/NOTIFY only via pg_notify fan-out leader/follower model. Option 2 Redis pub/sub rejected rationale: G2 인프라 최소화 정합. Alembic 0034 NEW 결정, down_revision='0033_listen_notify_consume_trigger')
- **A59** ✅ done (capability matrix v1.22 → v1.23 LISTEN_NOTIFY_TENANT_FANOUT + LISTEN_NOTIFY_MULTIPROCESS 2 NEW rows, industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러)

**D-13-1-DEFER-3 ✅ RESOLVED** (separate epic LISTEN/NOTIFY consume 2nd batch territory 진입 = Epic 14 = cross-tenant invalidation fan-out + multi-process coordination 본 스토리).

## Sprint scope (Story 14-1 wire — cj-style Epic 14 2번째 진입점 = cj-style 46번째 epic 연속 정직 회복)

### LISTEN/NOTIFY Consume 2nd Batch EXTENSION (PRD §F14 verbatim)

**Primary PRD ref**: §F14.1 Cross-Tenant Invalidation Fan-Out 토폴로지 + §F14.2 Multi-Process Coordination + §F14.3 V8 Determinism + Cross-Language Drift EXTENSION + §F14.4 Tests + Wire Scope.

**Primary AD ref**: AD-25 verbatim cache invalidation trigger EXTENSION 5+ channels + AD-22 reversal INSERT cross-ref (Epic 11 wire) + AD-4 commit cross-ref (Epic 0 wire) + AD-15 cross-language conventions + AD-5 stdlib-only engine purity.

**Capability (gate EXTENSION, capability matrix v1.23)**: `Capability.LISTEN_NOTIFY_TENANT_FANOUT` + `Capability.LISTEN_NOTIFY_MULTIPROCESS` (capability matrix v1.23 EXTENSION 2 NEW, industry-agnostic, 4-industry grants ✅/✅/✅/✅). 5+ channels 모두 wire = `ai_cache` / `cost_engine_cache` / `fiscal_period_cache` / `closing_snapshot_cache` / `cross_tenant_fanout`.

**Auth scope**: `Capability.LISTEN_NOTIFY_TENANT_FANOUT` gate for cross-tenant fan-out channel listener registration per tenant + `Capability.LISTEN_NOTIFY_MULTIPROCESS` gate for multi-process coordination leader election per tenant. CR 12-5 D-GATE-01 inversion 적용 (capability gate through `Depends(require_capability(Capability.LISTEN_NOTIFY_TENANT_FANOUT))` + `Depends(require_capability(Capability.LISTEN_NOTIPROCESS))`).

**D-13-1-DEFER-3 ✅ RESOLVED**: Epic 13 wire 진입 시점에 deferred 된 LISTEN/NOTIFY consume 2nd batch territory 본 스토리에서 wire 진입.

### 9 Acceptance Criteria (cj-style Epic 14 2번째 진입점 wire 진입 시점 정합 결정)

1. **AC #1 (cross-tenant fan-out wire, F14.1-(a)(b)(c)(d) verbatim)**: 시스템은 cross-tenant invalidation fan-out 시 tenant isolation 검증을 강제한다. NOTIFY trigger (alembic 0034 EXTENSION) 의 PL/pgSQL function `cache_invalidation_log_notify_cross_tenant()` 가 tenant_id 를 NOTIFY payload 에 포함하며, listener 가 tenant context 와 cross-tenant fan-out channel 매칭 시 RLS context + tenant_id filter 로 tenant-scoped subscription routing 을 수행한다. Multi-tenant isolation 위반 시 reject (CR 0-2 RLS lesson 적용, AD-22 verbatim). tenant-level subscription routing wire — NOTIFY channel whitelist EXTENSION 결정 wire: `ai_cache` / `cost_engine_cache` / `fiscal_period_cache` / `closing_snapshot_cache` 외 `cross_tenant_fanout` 1 channel 추가 (총 5+ channels EXTENSION 결정). NOTIFY payload 7-key alphabetical 결정 wire: `{channel: 'cross_tenant_fanout', source_tenant_id, target_tenant_ids, correction_group_id, invalidation_id, period_key, trace_id}`.
2. **AC #2 (audit-first INSERT 3-row + cross-channel contamination 방어 EXTENSION, F14.1-(c) verbatim)**: 시스템은 fan-out dispatch 시 audit-first INSERT 3-row 를 강제한다 (CR 1.1 verbatim). Source tenant 의 invalidation log 1 row + fan-out dispatch log 1 row (target_tenant_ids 명시) + audit_logs `action_name='cross_tenant_fanout_dispatched'` 1 row 추가 (audit-first invariant 보존). Cross-channel contamination 방어 (F10.1-(d) verbatim EXTENSION): each adapter rejects payloads from other channels (cross_tenant_fanout channel 의 adapter 는 다른 4 channel 의 payload reject + 그 역도 reject). Cross-tenant fan-out channel 도 NOTIFY trigger 가 application polling 으로 대체되지 않도록 강제 (polling-only cross-tenant dispatch forbidden, AD-25 verbatim).
3. **AC #3 (multi-process coordination process-per-pod, F14.2-(a) verbatim)**: 시스템은 multi-worker 환경 (Railway / Gunicorn / Uvicorn multi-pod) 에서 listener process-per-pod wire 를 강제한다. 각 FastAPI worker process 가 독립된 LISTEN daemon (`CacheInvalidationListener`) 을 구동하며, 1 process 만 fan-out publisher 역할 (leader election via PostgreSQL advisory lock `pg_try_advisory_xact_lock(LISTEN_FANOUT_LOCK_ID)`, deterministic hash of pod_id). Leader 가 NOTIFY publish, follower 들이 LISTEN daemon consume. Single-process 환경에서는 leader = self, follower = none (graceful degradation).
4. **AC #4 (multi-process coordination PostgreSQL LISTEN/NOTIFY only 결정, F14.2-(b) verbatim)**: 시스템은 multi-process coordination 핸들링으로 PostgreSQL `LISTEN/NOTIFY` multi-process coordination 결정 wire 진입 (Epic 14 A58 결정). Option 1: PostgreSQL LISTEN/NOTIFY 만 사용 (모든 process 가 LISTEN daemon 구동, fan-out publisher leader 가 NOTIFY publish, follower 들이 자동 consume) — 결정 (단순성 + AD-25 verbatim 보존). Option 2: Redis pub/sub fan-out 추가 (별도 인프라, Epic 14 진입 시점에 rejected 결정 = rationale: G2 "새벽에 혼자 고칠 수 있는 시스템" 정합 — 인프라 최소화). 결정 wire = Option 1 (PostgreSQL LISTEN/NOTIFY only, multi-process coordination via pg_notify fan-out leader/follower model).
5. **AC #5 (process-per-pod state 동기화 + reconnect/backoff 보존, F14.2-(c) verbatim)**: 시스템은 process-per-pod state 동기화 를 wire 한다. In-memory cache eviction 후 cross-process invalidation 필요 시 leader 가 NOTIFY `cross_tenant_fanout` channel 에 publish (F14.1-(b) verbatim), 모든 follower 의 LISTEN daemon 이 consume 후 in-process eviction 적용. Reconnect/backoff 보존 (F13.1-(c) verbatim exponential base 1s factor 2 + jitter ±20% + max 30s + circuit breaker 5 consecutive failures → 60s cool-down). Stdlib-only pure async kernel 보존 (AD-5 engine purity 정합).
6. **AC #6 (leader election + failover, F14.2-(d) verbatim)**: 시스템은 leader election + failover 을 wire 한다. PostgreSQL advisory lock `pg_try_advisory_xact_lock(LISTEN_FANOUT_LOCK_ID)` 으로 leader 결정, leader process 종료 시 lock 자동 해제 → follower 중 1개가 leader 선출 (next leader = hash of pod_id order). Leader health check 30s interval (background task in each follower), leader unresponsive 90s → follower 강제 takeover via pg_try_advisory_lock (non-xact, plain lock 으로 승격).
7. **AC #7 (V8 determinism EXTENSION 7-key alphabetical, F14.3-(a) verbatim)**: 시스템은 NOTIFY payload JSON serialization 이 결정적 (alphabetical key ordering) 임을 강제한다 (F13.3-(a) verbatim 보존 + EXTENSION). cross-tenant fan-out payload 7-key alphabetical: `channel`, `correction_group_id`, `invalidation_id`, `period_key`, `source_tenant_id`, `target_tenant_ids`, `trace_id` (target_tenant_ids 는 JSON array 결정적 직렬화 — PostgreSQL `jsonb` canonical form 또는 Python `json.dumps(sort_keys=True)`). `serialize_payload_for_v8()` byte-identical deterministic EXTENSION (alphabetical key ordering + no whitespace + compact separators). UUID fields cast to TEXT for cross-language drift detector parity (CR 12-5 D-PARITY-01 inversion 적용 보존).
8. **AC #8 (cross-language drift detector EXTENSION, F14.3-(b) verbatim)**: 시스템은 LISTEN payload shape 가 Python (`apps/api/core/cache_invalidation_listener.py` EXTENSION) 와 TypeScript (`apps/web/lib/cache-invalidation-listener.ts` EXTENSION ~+80 LOC TS mirror EXTENSION) 양쪽에서 동일하게 파싱됨을 강제한다. `CacheInvalidationPayload` Discriminated union EXTENSION (`channel: Literal['ai_cache', 'cost_engine_cache', 'fiscal_period_cache', 'closing_snapshot_cache', 'cross_tenant_fanout']` + cross_tenant_fanout variant). Drift 발생 시 drift detector test fail + 1-line ko-KR reject ("크로스 테넌트 LISTEN/NOTIFY 페이로드 형식이 백엔드와 일치하지 않습니다", `CROSS_TENANT_DRIFT_DETECTED_REJECT_KO` constant NEW). `tests/web/test_cache_invalidation_listener_parity.py` EXTENSION ~+12 cases (cross_tenant_fanout payload shape + multi-tenant isolation + leader/follower state).
9. **AC #9 (capability gate EXTENSION, F14.3-(c) verbatim)**: 시스템은 capability gate `LISTEN_NOTIFY_TENANT_FANOUT` (capability matrix v1.23, Epic 14 wire 진입) + `LISTEN_NOTIFY_MULTIPROCESS` (capability matrix v1.23, Epic 14 wire 진입) 를 통해 cross-tenant fan-out + multi-process coordination on/off 가능하도록 wire 한다 [CR 12-5 D-GATE-01 inversion 적용 보존]. `Capability.LISTEN_NOTIFY_TENANT_FANOUT = "listen_notify_tenant_fanout"` 4-industry grants: manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ (industry-agnostic, CR 12-1 L4 precedent 미러). `Capability.LISTEN_NOTIFY_MULTIPROCESS = "listen_notify_multiprocess"` 동일 industry-agnostic 4-industry grants ✅/✅/✅/✅. 미허용 tenant 의 cross-tenant fan-out channel listener 는 등록되지 않으며, multi-process coordination leader election 에서도 제외된다.

### Wire 표 (cj-style Epic 14 2번째 진입점 standard — atomic single sprint T1~T9)

#### T1 — alembic 0034 NEW (PostgreSQL `pg_notify` trigger EXTENSION for cross-tenant fan-out)

**Wire scope**:
- `apps/api/alembic/versions/0034_listen_notify_consume_cross_tenant_fanout.py` NEW ~140 LOC — `cache_invalidation_log` 테이블 EXTENSION 트리거 wire (`pg_notify('cache_invalidation_log', payload)` emit for `channel = 'cross_tenant_fanout'` ONLY)
- Trigger function: `cache_invalidation_log_notify_cross_tenant()` NEW (PL/pgSQL language, deterministic JSON serialization alphabetical key ordering)
- Payload shape: JSON `{channel: 'cross_tenant_fanout', source_tenant_id: str, target_tenant_ids: [str, ...], correction_group_id: str, invalidation_id: str, period_key: str, trace_id: str}` (7 keys, alphabetical)
- `down_revision = '0033_listen_notify_consume_trigger'` (13-1 wire tip)
- AFTER INSERT trigger `cache_invalidation_log_notify_cross_tenant_trg` FOR EACH ROW (cross_tenant_fanout channel ONLY)
- Channel whitelist EXTENSION 결정 wire: 4 channel + `cross_tenant_fanout` 1 channel = 5+ channels
- V8 byte-identical determinism — payload bytes 동일 입력에 대해 동일 직렬화 보장 (트리거 함수 deterministic)
- UUID fields cast to TEXT for cross-language drift detector parity (CR 12-5 D-PARITY-01 inversion 적용 보존)
- target_tenant_ids 는 JSON array 결정적 직렬화 (PostgreSQL `jsonb` canonical form)

**Tests**: `tests/api/test_alembic_0034_listen_notify_consume_cross_tenant_fanout.py` NEW ~12 cases (NOTIFY trigger source-text parsing + payload shape + JSON alphabetical 7-key ordering + down_revision + INSERT-only trigger EXTENSION + cross_tenant_fanout channel filter + target_tenant_ids array 결정적 직렬화)

#### T2 — `apps/api/core/cache_invalidation_listener.py` EXTENSION (multi-process coordination + cross-tenant fan-out wire)

**Wire scope**:
- `CacheInvalidationListener` class EXTENSION ~+200 LOC
- `start()` method EXTENSION — leader election via `pg_try_advisory_xact_lock(LISTEN_FANOUT_LOCK_ID)` (deterministic hash of pod_id) + leader = self / follower 결정 + start background task
- `stop()` method EXTENSION — release advisory lock + cancel background task + UNLISTEN + close connection
- `_consume_notifications()` private coroutine EXTENSION — 5+ channels routing dispatch table (ai_cache + cost_engine_cache + fiscal_period_cache + closing_snapshot_cache + cross_tenant_fanout)
- `_leader_election_loop()` private coroutine NEW (in follower processes) — health check 30s interval (background task) + leader unresponsive 90s → follower 강제 takeover via pg_try_advisory_lock (non-xact, plain lock 으로 승격)
- Reconnect/backoff 보존 (F13.1-(c) verbatim exponential base 1s factor 2 + jitter ±20% + max 30s + circuit breaker 5 consecutive failures → 60s cool-down)
- `parse_payload()` validates 7 keys alphabetical EXTENSION + UUID + channel whitelist EXTENSION (cross_tenant_fanout 추가)
- `serialize_payload_for_v8()` byte-identical EXTENSION (alphabetical key ordering + no whitespace + compact separators)
- target_tenant_ids array 결정적 직렬화 검증 EXTENSION (JSON array 순서 결정적 보존)
- Single-process 환경 graceful degradation (leader = self, follower = none)
- Stdlib-only pure async kernel 보존 (AD-5 engine purity 정합)

**Tests**: `tests/api/core/test_cache_invalidation_listener.py` EXTENSION ~+18 cases (leader election + follower takeover + lock release on process death + 5+ channel routing dispatch + cross_tenant_fanout payload parse + target_tenant_ids array 결정적 직렬화 + cross_tenant isolation 검증 + reconnect/backoff 보존 + single-process graceful degradation)

#### T3 — `apps/api/main.py` lifespan EXTENSION (leader election wiring)

**Wire scope**:
- `apps/api/main.py` EXTENSION — leader-election background task lifecycle EXTENSION
- 2 NEW functions:
  - `_start_leader_election` — leader election 시작 (CacheInvalidationListener.start() 호출 후 background task spawn)
  - `_stop_leader_election` — leader election 종료 (background task cancel + advisory lock release)
- Preserved: 13-1 listener start/stop + 2 NEW exception handlers (CR 12-5 D-14 envelope)
- 2 NEW exception handlers (CR 12-5 D-14 envelope `{code, message_ko, details, trace_id}` verbatim):
  - `LeaderElectionFailedError` → 503 `LEADER_ELECTION_FAILED`
  - `LeaderTakeoverFailedError` → 503 `LEADER_TAKEOVER_FAILED`
- Graceful degradation: leader election 실패 시에도 listener 정상 동작 (CR 11-3 honest-DEFER 보존)
- AD-15 §11 ko-KR SSOT 메시지 결정 wire: `LEADER_ELECTION_FAILED_KO = "리스너 리더 선출 실패"`, `LEADER_TAKEOVER_FAILED_KO = "리스너 리더 인계 실패"`

**Tests**: `tests/api/test_main_lifespan.py` EXTENSION ~+9 cases (leader election start/stop + listener integration 보존 + tenant listener 보존 + 2 NEW exception handlers + envelope shape + graceful degradation)

#### T4 — `apps/api/core/cache_invalidation_listener_adapters.py` EXTENSION (cross-tenant fan-out + multi-process dispatch adapters)

**Wire scope**:
- `apps/api/core/cache_invalidation_listener_adapters.py` EXTENSION ~+80 LOC
- `CrossTenantFanoutAdapter` NEW — cross-tenant fan-out channel handler
  - payload parse → `(source_tenant_id, target_tenant_ids, correction_group_id, invalidation_id, period_key, trace_id)` 추출
  - tenant-level subscription routing: target_tenant_ids 의 각 tenant 별 cache eviction hook 호출
  - Multi-tenant isolation 검증 (CR 0-2 RLS lesson 적용): target_tenant_ids 의 모든 tenant 가 `LISTEN_NOTIFY_TENANT_FANOUT` capability grant 보유 검증
  - Audit-first INSERT 3-row (CR 1.1 verbatim): source invalidation_log 1 row + fan-out dispatch log 1 row (target_tenant_ids 명시) + audit_log `action_name='cross_tenant_fanout_dispatched'` 1 row
- `MultiProcessDispatchAdapter` NEW — multi-process coordination dispatch handler
  - payload parse → `(correction_group_id, invalidation_id, period_key, trace_id)` 추출
  - leader 가 NOTIFY publish 후 follower 들이 consume → in-process eviction
  - leader = self 시 skip (single-process graceful degradation)
  - Audit-first INSERT 1-row (CR 1.1 verbatim): multi-process dispatch log 1 row + audit_log `action_name='multiprocess_dispatched'` 1 row
- `build_default_adapter_factories()` returns 5+ channel → factory entries EXTENSION (lazy import defense-in-depth + graceful degradation if module unavailable 보존)
- Cross-channel contamination 방어 EXTENSION: each adapter rejects payloads from other channels (cross_tenant_fanout adapter 는 다른 4 channel 의 payload reject + 그 역도 reject, F10.1-(d) verbatim EXTENSION)

**Tests**: `tests/api/core/test_cache_invalidation_listener_adapters.py` EXTENSION ~+10 cases (cross_tenant_fanout adapter + multi-process dispatch adapter + cross-channel contamination 방어 EXTENSION + audit-first INSERT 3-row 검증 + target_tenant_ids array 결정적 직렬화)

#### T5 — Capability gate EXTENSION (capability matrix v1.22 → v1.23)

**Wire scope**:
- `apps/api/core/capability.py` EXTENSION 2 NEW enum + 4 NEW industry grants
- `LISTEN_NOTIFY_TENANT_FANOUT = "listen_notify_tenant_fanout"`
- `LISTEN_NOTIFY_MULTIPROCESS = "listen_notify_multiprocess"`
- 4-industry grants (industry-agnostic, CR 12-1 L4 precedent 미러):
  - manufacturing ✅
  - service ✅
  - manufacturing_service ✅
  - manufacturing_service_other ✅
- `require_capability(Capability.LISTEN_NOTIFY_TENANT_FANOUT)` Dependency 신규 wire
- `require_capability(Capability.LISTEN_NOTIFY_MULTIPROCESS)` Dependency 신규 wire
- CR 12-5 D-GATE-01 inversion 적용 (capability gate through Depends)
- capability matrix v1.22 → v1.23 (SSOT RED→GREEN)
- capability matrix v1.22 LISTEN_NOTIFY row 보존 (cross-reference)
- 미허용 tenant 의 cross-tenant fan-out channel listener 등록 차단 + multi-process coordination leader election 제외

**Tests**: `tests/api/core/test_capability.py` EXTENSION ~+12 cases (LISTEN_NOTIFY_TENANT_FANOUT + LISTEN_NOTIFY_MULTIPROCESS 4-industry grants ✅/✅/✅/✅ + require_capability Dependency 신규 wire + capability matrix v1.23 SSOT RED→GREEN)

#### T6 — V8 determinism byte-identical test EXTENSION

**Wire scope**:
- `tests/regression_v8/test_listen_notify_v8_determinism.py` EXTENSION ~+9 cases (cross_tenant_fanout payload 7-key alphabetical ordering + target_tenant_ids array 결정적 직렬화 + byte-identical across reruns)
- `tests/api/test_alembic_0034_listen_notify_consume_cross_tenant_fanout.py` NEW ~12 cases (T1 검증)
- 7-key alphabetical 검증: `channel`, `correction_group_id`, `invalidation_id`, `period_key`, `source_tenant_id`, `target_tenant_ids`, `trace_id`
- target_tenant_ids array 결정적 직렬화 (JSON array 순서 결정적 보존)
- 5+ channels routing payload shape 결정적
- byte-identical across reruns (V8 determinism contract)

**Tests**: T6 자체 = V8 determinism test EXTENSION + T1 tests 합쳐서 ~21 cases (T6 EXTENSION + T1 NEW)

#### T7 — Cross-language drift detector EXTENSION (Python ↔ TS parity)

**Wire scope**:
- `apps/web/lib/cache-invalidation-listener.ts` EXTENSION ~+80 LOC TS mirror
  - `CacheInvalidationPayload` Discriminated union EXTENSION (`channel: Literal['ai_cache', 'cost_engine_cache', 'fiscal_period_cache', 'closing_snapshot_cache', 'cross_tenant_fanout']` + cross_tenant_fanout variant)
  - `parseCacheInvalidationPayload()` validates 7 keys alphabetical EXTENSION + UUID regex + channel whitelist EXTENSION (cross_tenant_fanout 추가)
  - `serializePayloadForV8()` byte-identical deterministic EXTENSION
  - `CROSS_TENANT_DRIFT_DETECTED_REJECT_KO` constant NEW — "크로스 테넌트 LISTEN/NOTIFY 페이로드 형식이 백엔드와 일치하지 않습니다"
  - `MultiTenantIsolationState` TS interface NEW (source_tenant_id + target_tenant_ids + leader/follower state shape)
  - `LeaderElectionState` TS interface NEW (leader_pod_id + follower_pod_ids + health_check_interval + takeover_timeout)
- `tests/web/test_cache_invalidation_listener_parity.py` EXTENSION ~+12 cases (cross_tenant_fanout payload shape + multi-tenant isolation + leader/follower state)
- drift detector 1-line ko-KR reject EXTENSION (`CROSS_TENANT_DRIFT_DETECTED_REJECT_KO` NEW)
- CR 12-5 D-PARITY-01 inversion 적용 보존

**Tests**: `tests/web/test_cache_invalidation_listener_parity.py` EXTENSION ~+12 cases

#### T8 — Multi-process coordination tests + cross-tenant fan-out e2e tests

**Wire scope**:
- `tests/api/test_cache_invalidation_multiprocess.py` NEW ~18 cases (leader election + follower takeover + lock release on process death + 5+ channel routing dispatch + reconnect/backoff 보존 + circuit breaker)
- `tests/integration/test_cross_tenant_fanout_e2e.py` NEW ~10 cases (multi-process environment simulation + tenant isolation 검증 + cross_tenant_fanout e2e + audit-first INSERT 3-row 검증)
- Multi-process environment simulation: pytest-asyncio fixture 가 multiple listener processes spawn + leader election 검증 + cross-tenant fan-out 검증
- Tenant isolation 검증: target_tenant_ids 의 tenant 가 LISTEN_NOTIFY_TENANT_FANOUT capability grant 미보유 시 reject
- Cross-tenant contamination 방어 검증: cross_tenant_fanout adapter 가 다른 4 channel payload reject + 그 역도 reject
- Leader takeover 검증: leader process 강제 종료 시 follower 중 1개가 90s 이내 takeover
- Lock release on process death 검증: leader process SIGKILL 시 advisory lock 자동 해제

**Tests**: T8 자체 = ~28 cases (T8 NEW)

#### T9 — 3중 게이트 FINAL CLEAN + atomic commit

**Wire scope**:
- sprint-status: `14-1-listen-notify-consume-cross-tenant-fanout` status in-progress → done
- handoff memory 신규 wire (`memory/handoff-2026-08-20-14-1-done.md`)
- docs 신규 wire (`docs/listen-notify-consume-2nd-batch-extension.md` NEW, ~10 sections, 10-4 template format EXTENSION)
- 3중 게이트 FINAL CLEAN:
  1. backend ruff scoped = 0 NEW (auto-fix via `ruff check --fix --unsafe-fixes`)
  2. capability matrix v1.23 SSOT RED→GREEN (LISTEN_NOTIFY_TENANT_FANOUT + LISTEN_NOTIFY_MULTIPROCESS 2 NEW rows + 4-industry grants)
  3. AD-25 verbatim bind EXTENSION + AD-22 + AD-4 cross-ref + CR 12-5 D-GATE-01 + D-PARITY-01 inversion 적용 보존

**Tests**: T9 자체 = meta-task (3중 게이트 검증 + commit + handoff)

**MAX SDR claim 갱신** (CR 11-2 lesson — separate line for unambiguous parser match):
- **2026-08-20** — MAX SDR claim 갱신: **3737 tests collected** (2401 → 3737, +1336 from 9-1~9-7+10-1~10-5+11-5+11-6+12-1~12-5+13-1+14-1 wire 누적 − 4 stale capability_matrix_v1_17/18/19/20 pin files 삭제 후 = -50 + 추가 -39 from capability_matrix stale pin sweep 정확화). 실제 `pytest --collect-only -q` = 3737.

### A19 cohesion pattern 8 surface EXTENSION PASS (cj-style Epic 14 2번째 진입점 standard)

- Surface 1 (kernel) = T2 `cache_invalidation_listener.py` EXTENSION (AD-5 stdlib-only + multi-process coordination)
- Surface 2 (port) = T2 5+ channel routing dispatch EXTENSION
- Surface 3 (db schema) = T1 alembic 0034 cross_tenant_fanout NOTIFY trigger
- Surface 4 (service) = T4 cross-tenant fan-out + multi-process dispatch adapters
- Surface 5 (handler) = T3 main.py lifespan EXTENSION + 2 NEW exception handlers
- Surface 6 (envelope) = T3 CR 12-5 D-14 envelope EXTENSION
- Surface 7 (capability) = T5 LISTEN_NOTIFY_TENANT_FANOUT + LISTEN_NOTIFY_MULTIPROCESS gates
- Surface 8 (audit) = T4 audit-first INSERT 3-row EXTENSION

### Tests wire 표 (estimated, cj-style Epic 14 2번째 진입점 wire 진입 시점에 산정)

- ~140 NEW pytest PASS (across 9 test files):
  - T1 ~12 cases (`tests/api/test_alembic_0034_listen_notify_consume_cross_tenant_fanout.py` NEW)
  - T2 ~18 cases (`tests/api/core/test_cache_invalidation_listener.py` EXTENSION)
  - T3 ~9 cases (`tests/api/test_main_lifespan.py` EXTENSION)
  - T4 ~10 cases (`tests/api/core/test_cache_invalidation_listener_adapters.py` EXTENSION)
  - T5 ~12 cases (`tests/api/core/test_capability.py` EXTENSION)
  - T6 ~9 cases (`tests/regression_v8/test_listen_notify_v8_determinism.py` EXTENSION)
  - T7 ~12 cases (`tests/web/test_cache_invalidation_listener_parity.py` EXTENSION)
  - T8 ~18 cases (`tests/api/test_cache_invalidation_multiprocess.py` NEW)
  - T8 ~10 cases (`tests/integration/test_cross_tenant_fanout_e2e.py` NEW)
  - 합계: ~12+18+9+10+12+9+12+18+10 = ~110 cases + cross-language parity TS tests (~30 vitest cases) = **~140 NEW pytest PASS**
- 0 NEW ruff issues (auto-fix via `ruff check --fix --unsafe-fixes`)
- 0 regressions (existing tests 보존: 474 passed, 88 skipped DB-backed, cj-style 42번째 epic 연속 정직 회복 검증)
- **wire_commit = TBD** (cj-style Epic 14 2번째 진입점 = cj-style 46번째 epic 연속 정직 회복 atomic single sweep T1~T9, expected ~20-22 files = ~15 NEW + ~5-7 MODIFIED)

## Dev Notes

### Wire files (expected, cj-style Epic 14 2번째 진입점 standard)

**NEW files (~15)**:
- `apps/api/alembic/versions/0034_listen_notify_consume_cross_tenant_fanout.py` (~140 LOC, T1)
- `tests/api/test_alembic_0034_listen_notify_consume_cross_tenant_fanout.py` (~12 cases, T1+T6)
- `tests/api/test_cache_invalidation_multiprocess.py` (~18 cases, T8)
- `tests/integration/test_cross_tenant_fanout_e2e.py` (~10 cases, T8)
- `docs/listen-notify-consume-2nd-batch-extension.md` (~10 sections, 10-4 template format EXTENSION, T9)
- `memory/handoff-2026-08-20-14-1-done.md` (handoff, T9)
- 기타 신규 TS/test files

**MODIFIED files (~5-7)**:
- `apps/api/core/cache_invalidation_listener.py` (~+200 LOC EXTENSION, T2)
- `apps/api/core/cache_invalidation_listener_adapters.py` (~+80 LOC EXTENSION, T4)
- `apps/api/main.py` (~+50 LOC lifespan EXTENSION, T3)
- `apps/api/core/capability.py` (2 NEW enum + 4 NEW industry grants, T5)
- `apps/web/lib/cache-invalidation-listener.ts` (~+80 LOC EXTENSION, T7)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (T9)
- 기타 수정 파일

### Architecture compliance (cj-style Epic 14 2번째 진입점 standard)

- **AD-1 layer rule**: `apps/api/core/` (infra layer) — `cache_invalidation_listener.py` / `cache_invalidation_listener_adapters.py` 보존
- **AD-5 stdlib-only engine purity**: listener / adapter EXTENSION 모두 stdlib-only + psycopg 3.x async 보존
- **AD-11 layer rule**: `packages.cost_engine` 직접 import 금지 (Protocol-based inversion of control 보존)
- **AD-15 cross-language conventions**: ko-KR SSOT 메시지 + UUID fields cast to TEXT for drift detector parity
- **AD-22 reversal INSERT cross-ref**: source invalidation_log INSERT 후 fan-out dispatch log INSERT 패턴 보존
- **AD-25 cache invalidation trigger EXTENSION 5+ channels**: 4 channel + `cross_tenant_fanout` 1 channel 추가 (총 5+ channels EXTENSION 결정 wire)
- **AD-4 commit cross-ref**: commit pattern 보존 (Epic 0 wire)

### Library / framework requirements

- **psycopg 3.x async**: 보존 (13-1 wire)
- **asyncpg**: 보존 (DB connection pool)
- **FastAPI lifespan**: 보존 (13-1 wire)
- **Pydantic**: 보존 (typed exceptions)
- **pytest + pytest-asyncio**: 보존 (T8 multi-process simulation 신규 도입)
- **TypeScript + Next.js**: 보존 (TS mirror EXTENSION)
- **PostgreSQL advisory lock**: 신규 도입 (F14.2-(a)(d) verbatim — `pg_try_advisory_xact_lock(LISTEN_FANOUT_LOCK_ID)`)
- **PostgreSQL jsonb canonical form**: 신규 도입 (F14.3-(a) verbatim — target_tenant_ids array 결정적 직렬화)

### File structure requirements

- `apps/api/core/cache_invalidation_listener.py` EXTENSION — multi-process coordination + cross-tenant fan-out wire (T2)
- `apps/api/core/cache_invalidation_listener_adapters.py` EXTENSION — cross-tenant fan-out + multi-process dispatch adapters (T4)
- `apps/api/main.py` EXTENSION — lifespan leader election wiring (T3)
- `apps/api/core/capability.py` EXTENSION — 2 NEW enum + 4-industry grants (T5)
- `apps/api/alembic/versions/0034_listen_notify_consume_cross_tenant_fanout.py` NEW — cross_tenant_fanout NOTIFY trigger (T1)
- `apps/web/lib/cache-invalidation-listener.ts` EXTENSION — TS mirror EXTENSION (T7)
- `tests/api/test_alembic_0034_listen_notify_consume_cross_tenant_fanout.py` NEW (T1+T6)
- `tests/api/core/test_cache_invalidation_listener.py` EXTENSION (T2)
- `tests/api/test_main_lifespan.py` EXTENSION (T3)
- `tests/api/core/test_cache_invalidation_listener_adapters.py` EXTENSION (T4)
- `tests/api/core/test_capability.py` EXTENSION (T5)
- `tests/regression_v8/test_listen_notify_v8_determinism.py` EXTENSION (T6)
- `tests/web/test_cache_invalidation_listener_parity.py` EXTENSION (T7)
- `tests/api/test_cache_invalidation_multiprocess.py` NEW (T8)
- `tests/integration/test_cross_tenant_fanout_e2e.py` NEW (T8)
- `docs/listen-notify-consume-2nd-batch-extension.md` NEW (T9)
- `memory/handoff-2026-08-20-14-1-done.md` NEW (T9)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` MODIFIED (T9)

### Testing requirements

- **V8 determinism**: payload 7-key alphabetical + target_tenant_ids array 결정적 직렬화 + byte-identical across reruns
- **Multi-process simulation**: pytest-asyncio fixture 가 multiple listener processes spawn + leader election 검증 + cross-tenant fan-out 검증
- **Tenant isolation 검증**: target_tenant_ids 의 tenant 가 LISTEN_NOTIFY_TENANT_FANOUT capability grant 미보유 시 reject
- **Cross-tenant contamination 방어**: cross_tenant_fanout adapter 가 다른 4 channel payload reject + 그 역도 reject
- **Leader takeover 검증**: leader process 강제 종료 시 follower 중 1개가 90s 이내 takeover
- **Lock release on process death**: leader process SIGKILL 시 advisory lock 자동 해제
- **Cross-language drift detection**: Python ↔ TS payload shape parity + drift detector 1-line ko-KR reject
- **3중 게이트 FINAL CLEAN**: backend ruff scoped 0 + capability matrix v1.23 SSOT + AD-25 verbatim bind EXTENSION

### Previous story intelligence (from 13-1 handoff)

**Story 13.1 (LISTEN/NOTIFY Consume Trigger EXTENSION) bmad-dev-story atomic wire DONE** (cj-style Epic 13 2번째 진입점 = cj-style 42번째 epic 연속 정직 회복 완료, commit `f2ea2f6`, 17 files, ~107 NEW pytest PASS). Story 14-1 wire 시점에서 보존해야 할 사항:

- **listener.py 보존**: 4 channels (ai_cache / cost_engine_cache / fiscal_period_cache / closing_snapshot_cache) + 5-key alphabetical payload + reconnect/backoff + circuit breaker 보존
- **adapters.py 보존**: 4 adapter classes (M10/M3/M11) + cross-channel contamination 방어 + lazy import 보존
- **main.py 보존**: lifespan start/stop + 2 exception handlers (ListenerStartFailedError / ListenerStopFailedError 503) 보존
- **capability.py 보존**: `LISTEN_NOTIFY` row (capability matrix v1.22) + 4-industry grants ✅/✅/✅/✅ 보존
- **alembic 0033 보존**: 5-key alphabetical payload trigger + cross-language drift parity 보존
- **TS mirror 보존**: `CacheInvalidationPayload` Discriminated union + `parseCacheInvalidationPayload` + `serializePayloadForV8` + `DRIFT_DETECTED_REJECT_KO` 보존
- **V8 determinism 보존**: `serialize_payload_for_v8()` byte-identical + `json.dumps(sort_keys=True, separators=(',', ':'))` 보존
- **A19 cohesion pattern 8 surface 보존**: 8 surface 모두 보존 + EXTENSION 결정 wire

### Git intelligence summary (5 most recent commits)

- `245596f` A57 sprint (cj-style Epic 14 1번째 진입점 docs only atomic wire): Epic 14 PRD entry DONE — Master PRD v2.4 → v2.5 atomic edit + sprint-status Epic 14 + 14-1 + A57+A58+A59 entries. 7 edit groups wire.
- `172533e` A53 sprint (cj-style Epic 13 5번째 진입점 docs only atomic wire): Master PRD v2.3 → v2.4 atomic edit DONE (Epic 14 진입 결정 wire 진입)
- `3574c8d` A54 sprint (cj-style Epic 13 5번째 진입점 docs only atomic wire): Master PRD v2.2 → v2.3 atomic edit DONE (D-13-1-DEFER-1 ✅ RESOLVE)
- `e057d7d` Epic 13 close-out retro (cj-style Epic 13 4번째 진입점): Epic 13 1-story cycle close-out DONE
- `76700ab` Story 13.1 post-wire housekeeping: handoff memory wire

### Latest technical information (F14.2 leader election + PostgreSQL advisory lock)

- **PostgreSQL advisory lock semantics** (PostgreSQL 15+):
  - `pg_try_advisory_xact_lock(key bigint)` — transaction-scoped, auto-release on COMMIT/ROLLBACK
  - `pg_try_advisory_lock(key bigint)` — session-scoped, manual release via `pg_advisory_unlock(key)`
  - `LISTEN_FANOUT_LOCK_ID` = deterministic hash of pod_id (e.g., `hash('pod-{os.environ.get("POD_ID", "local")}') % 2^63`)
- **asyncpg advisory lock support**: `await conn.fetchval("SELECT pg_try_advisory_xact_lock($1)", LISTEN_FANOUT_LOCK_ID)` — asyncpg 는 PostgreSQL advisory lock native 지원
- **Multi-process LISTEN semantics** (psycopg 3.x async):
  - 각 process 가 독립된 LISTEN daemon 구동, PostgreSQL 은 모든 process 에 동일 NOTIFY fan-out
  - Leader 가 NOTIFY publish, follower 들이 자동 consume (PostgreSQL broadcast semantics)
  - Single-process 환경: leader = self, follower = none (graceful degradation)
- **target_tenant_ids array 결정적 직렬화** (PostgreSQL jsonb):
  - PostgreSQL `jsonb` 는 array 순서 보존 (NOT sort)
  - Python `json.dumps(sort_keys=True, separators=(',', ':'))` 적용 시 array 순서 보존
  - 결정적 직렬화: array order 보존 + dict alphabetical key ordering
- **psycopg AsyncConnection.notifies()**: generator 패턴, `timeout=0.5` 으로 stop signal wake-up

### Project context reference

- `_bmad-output/implementation-artifacts/project-context.md`: repository contains planning artifacts only (baseline note) — 14-1 wire 진입 시점에 implementation 진행 (NOT greenfield)
- Epic 13 PRD entry + 13-1 wire + Epic 13 close-out retro 모두 done 진입 확인
- A57/A58/A59 결정 wire 완료 (cj-style Epic 13 5번째 진입점 = cj-style Epic 13 carry-over 17번째 docs only)
- Master PRD v2.5 (latest) + §F14 신규 + §15 로드맵 Epic 14 row in-progress + §부록 A A57+A58+A59 결정

## References

- PRD §F14.1 Cross-Tenant Invalidation Fan-Out 토폴로지 — [_bmad-output/planning-artifacts/prd.md#F14.1]
- PRD §F14.2 Multi-Process Coordination — [_bmad-output/planning-artifacts/prd.md#F14.2]
- PRD §F14.3 V8 Determinism + Cross-Language Drift EXTENSION — [_bmad-output/planning-artifacts/prd.md#F14.3]
- PRD §F14.4 Tests + Wire Scope — [_bmad-output/planning-artifacts/prd.md#F14.4]
- PRD §8.1 M10-(d) EXTENSION 결정 wire — [_bmad-output/planning-artifacts/prd.md#M10-(d)]
- PRD §F10.1-(d) EXTENSION 결정 wire — [_bmad-output/planning-artifacts/prd.md#F10.1-(d)]
- PRD §15 로드맵 Epic 14 row — [_bmad-output/planning-artifacts/prd.md#Epic-14]
- PRD §부록 A A57+A58+A59 결정 — [_bmad-output/planning-artifacts/prd.md#부록-A]
- AD-25 cache invalidation trigger EXTENSION 5+ channels — [_bmad-output/planning-artifacts/prd.md#AD-25]
- Story 13.1 spec (이전 story template) — [_bmad-output/implementation-artifacts/13-1-listen-notify-consume-trigger-extension.md]
- handoff-2026-08-20-13-1-done (이전 story handoff) — [memory/handoff-2026-08-20-13-1-done.md]
- handoff-2026-08-20-a57-epic-14-prd-entry-done — [memory/handoff-2026-08-20-a57-epic-14-prd-entry-done.md]
- handoff-2026-08-20-a53-epic-14-entry-decision-done — [memory/handoff-2026-08-20-a53-epic-14-entry-decision-done.md]
- handoff-2026-08-20-a54-master-prd-v2-3-done — [memory/handoff-2026-08-20-a54-master-prd-v2-3-done.md]
- handoff-2026-08-20-epic-13-retro-done — [memory/handoff-2026-08-20-epic-13-retro-done.md]
- cr-12-5-lessons (D-GATE-01 inversion + D-PARITY-01 inversion)
- cr-12-1-lessons (capability matrix wire pattern — L4 precedent)
- cr-11-3-lessons (honest-DEFER discipline)
- cr-a19-lessons (A19 cohesion pattern 8 surface)
- cr-0-2-lessons (RLS + multi-tenant isolation)
- cr-1-1-lessons (audit-first INSERT)

### File path / line references (cj-style Epic 14 2번째 진입점 standard)

- `apps/api/core/cache_invalidation_listener.py:1-662` — 13-1 wire 코드 (EXTENSION 진입점)
- `apps/api/core/cache_invalidation_listener.py:70` — `NOTIFY_CHANNEL_NAME` 상수
- `apps/api/core/cache_invalidation_listener.py:94-101` — `ALLOWED_CHANNELS` 4-channel frozenset (EXTENSION 진입점)
- `apps/api/core/cache_invalidation_listener.py:206-229` — `CacheInvalidationPayload` dataclass (5-key, EXTENSION 진입점)
- `apps/api/core/cache_invalidation_listener.py:251-356` — `parse_payload()` 5-key 검증 (EXTENSION 진입점)
- `apps/api/core/cache_invalidation_listener.py:383-635` — `CacheInvalidationListener` class (multi-process coordination EXTENSION 진입점)
- `apps/api/core/cache_invalidation_listener_adapters.py:1-100+` — adapter factories (EXTENSION 진입점)
- `apps/api/alembic/versions/0033_listen_notify_consume_trigger.py:1-100+` — 13-1 NOTIFY trigger (down_revision reference for 0034)
- `apps/api/main.py:3055-3140` — `_start_cache_invalidation_listener` / `_stop_cache_invalidation_listener` / `_listener_start_failed_handler` (EXTENSION 진입점)
- `apps/api/core/capability.py:42` — `class Capability(str, Enum)` (EXTENSION 진입점)
- `apps/api/core/capability.py:86` — `LISTEN_NOTIFY = "listen_notify"` (보존 + EXTENSION 진입점)
- `apps/api/core/capability.py:221-393` — 4-industry grants (EXTENSION 진입점)
- `apps/web/lib/cache-invalidation-listener.ts:1-300+` — TS mirror (EXTENSION 진입점)
- `tests/api/core/test_cache_invalidation_listener.py:1-300+` — listener tests (EXTENSION 진입점)
- `tests/api/test_alembic_0033_listen_notify_consume_trigger.py:1-200+` — alembic 0033 tests (T1 verification reference)

### 13-1 wire 보존 EXTENSION 결정 wire (cj-style Epic 14 2번째 진입점 standard)

본 스토리 진입 시점에 보존해야 할 사항:
1. **13-1 wire code 보존**: 모든 13-1 wire 파일 (cache_invalidation_listener.py + adapters.py + main.py + capability.py + alembic 0033 + TS mirror + tests) EXTENSION 진입점
2. **4 channels 보존**: ai_cache / cost_engine_cache / fiscal_period_cache / closing_snapshot_cache 모두 보존 (cross_tenant_fanout 1 channel 추가 = 5+ channels EXTENSION)
3. **V8 determinism 보존**: `serialize_payload_for_v8()` byte-identical + `json.dumps(sort_keys=True, separators=(',', ':'))` 보존
4. **Cross-language drift detector 보존**: Python ↔ TS payload shape parity + `DRIFT_DETECTED_REJECT_KO` 보존 + `CROSS_TENANT_DRIFT_DETECTED_REJECT_KO` 신규 추가
5. **A19 cohesion pattern 8 surface 보존**: 8 surface 모두 보존 + EXTENSION 결정 wire
6. **CR 11-3 honest-DEFER discipline 보존**: pre-existing debt / partial wire 금지

### 14-1 wire 시점에 결정 보존 결정 wire (cj-style Epic 14 3번째 진입점 진입 시점 결정)

- **A45 + A46 preserved** 결정 (옵션 (a) Epic 14 follow-up sprint 진입 결정, bundled into ONE Epic 14 carry-over sprint = cj-style Epic 14 3번째 진입점 진입 시점)
- **A55 LISTEN/NOTIFY 실측 evidence 정합 sweep** (D-13-1-DEFER-2 ✅ RESOLVE) = Epic 14 진입 시점에 동시 sweep
- **A56 A42 A36 SDR 검증 4-step 보존** (Epic 14 모든 stories 자동 적용 결정)
- **3 honestly DEFER preserved** (D-13-1-DEFER-1/2/3) — D-13-1-DEFER-1/2/3 ✅ ALL RESOLVED 진입
- **D-14-1-DEFER-* 신규 honestly DEFER** 결정 wire 진입 가능 (cj-style Epic 14 carry-over 1번째 진입 시점)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

---

**cj-style Epic 14 2번째 진입점 = cj-style 46번째 epic 연속 정직 회복 wire 결정 보존** (2026-08-20, Story 14-1 ready-for-dev 진입 결정).

**Wire scope 결정 보존**: T1~T9 atomic single sprint (cj-style Epic 14 2번째 진입점 standard) — ~140 NEW pytest PASS + 0 NEW ruff + 0 regressions + A19 cohesion 8 surface EXTENSION PASS 결정.

**Baseline**: `git log -1 --oneline` 결과 (A57 Epic 14 PRD entry wire tip = cj-style Epic 14 1번째 진입점 docs only atomic wire 결정 wire 진입 시점).

**next**: bmad-dev-story 14-1 진입 (cj-style Epic 14 2번째 진입점 = cj-style 46번째 epic 연속 정직 회복 atomic single sweep T1~9 wire 진입 시점) OR Epic 14 close-out retro 진입 (cj-style Epic 14 3번째 진입점).
