---
baseline_commit: caacfc7
target_key: 11-3-snapshot-persistence-with-reverse
epic: 11
story_id: 11.3
title: Snapshot Persistence with Reverse — fiscal_period_snapshots state='committed' 보존 + AD-22 reversal sequence 영구화 + AD-25 multi-channel publisher + W2 reopen
status: ready-for-dev
---

# Story 11.3: Snapshot Persistence with Reverse — fiscal_period_snapshots state='committed' 보존 + AD-22 reversal sequence 영구화 + AD-25 multi-channel publisher + W2 reopen

Status: ready-for-dev

> **Epic 11 cj-style 3-story 분할 (Epic 5 close-out retro §6 W1) 3번째 스토리**. **epics.md 원본 11.2 (Snapshot Persistence on Close) + 11.3 (Reversal Sequence) 통합** wire. 사용자 결정 (2026-08-08 cj-style 3분할): 11-1 = M11 module authority + AD-22 reversal ledger wire + A9 fill + H6 fix + AD-25 1-channel ✅ done (commit b4961a6) → **11-2 = close-sequence-lock** ✅ done (commit caacfc7) → **11-3 = snapshot-persistence-with-reverse** (본 스토리, epics.md 11.2 + 11.3 통합). 본 스토리 = **fiscal_period_snapshots state='verified'→'committed' 전이** (PRD §F11.2 PRIMARY, epics.md 11.2) + **AD-22 reversal sequence fiscal_period_snapshots state='committed'→'reversed' 영구화** (PRD §F11.3 + epics.md 11.3 — sign-negating + corrected row, AD-22 wire) + **AD-25 cache invalidation multi-channel publisher** (11-1 wire 1-channel `ai_cache` → 11-3 4-channel `ai_cache` + `cost_engine_cache` + `fiscal_period_cache` + `closing_snapshot_cache`) + **W2 reopen flow** (operator action + reason + audit row + AD-25 invalidation, Epic 5 retro §6 W2 deferral) + **11-2 carry-over 4 DEFER items** (TS mirrors + V8 22→26 골든 fixture + Task 10 frontend + W2 reopen).
>
> **baseline_commit = caacfc7** (Story 11.2 bmad-code-review 3rd sweep done tip, 3 BLOCKING DECISION all wire + ~10 critical PATCH + 16 test rewrites + ~29 honestly DEFER). 본 스토리는 11-1 + 11-2 wire 모두 reuse + extend: M11 module authority (`apps/api/modules/m11_close/` populated) + AD-22 reversal ledger wire (`reversal_negating` + `reversal_corrected` event type + `reversal_log` table) + AD-25 1-channel publisher (`CacheInvalidationPublisher`, `cache_invalidation_log` table) + A9 fill 5 values + H6 fix + fiscal_periods greenfield (Alembic 0020) + 4-stage close_sequence_state + partial close guard + AD-6 INSERT 거부 + 11-1 reversal_authorization 양쪽 가드 + CLOSE_SEQUENCE_LOCK capability (v1.11).
>
> **cj-style 3-story 분할 (Epic 5 retro §6 W1)** — Epic 4 A3 (Epic 5 5-1/5-2/5-3) + Epic 6 6-1/6-2/6-3 동일 패턴의 Epic 11 적용형. **11-1 = M11 module authority + AD-22 reversal ledger wire + A9 fill + H6 fix + AD-25 1-channel** (사용자 결정 + A9 매칭, ✅ done) → **11-2 = close-sequence-lock** (epics.md 11.1 greenfield, ✅ done) → **11-3 = snapshot-persistence-with-reverse** (epics.md 11.2 + 11.3 통합, 본 스토리). 3-story 모두 **additive** — 기존 wire contract 호환 + 사용자 흐름 무중단.

<!-- dev-context: Epic 5 close-out retro (2026-08-07) §6 W1 cj-style 결정 — "Epic 11 reversal module wire 진입점 (5-1 + 5-2 carry). cj-style 3-story 분할 패턴 (Epic 4 A3 + Epic 5 5-1/5-2/5-3 + Epic 6 6-1/6-2/6-3 동일) 적용. 11-1 = M11 module authority + AD-22 reversal wire + A9 fill + H6 fix + AD-25 1-channel (✅ done) → 11-2 = close-sequence-lock (epics.md 11.1 greenfield, ✅ done) → 11-3 = snapshot-persistence-with-reverse (epics.md 11.2 + 11.3 통합)".

본 스토리는 **PRD §F11.2 (Snapshot persistence)** + **PRD §F11.3 (Reversal sequence)** + **AD-2 (append-only ledger)** + **AD-6 (Fiscal-period close lock)** + **AD-16 (Fiscal snapshot contract)** + **AD-20 (Calculation result state machine)** + **AD-22 (Reversal construction and ownership)** + **AD-25 (Cache invalidation notification)** SSOT. PRD §8.M11(b) "마감 완료 시 계산 결과 전체 스냅샷 고정 + 이후 입력·변경은 역분개(A8)로만" 명시. Architecture Spine §AD-16 Rule — "`fiscal_period_snapshots` uniquely keyed by `(tenant_id, period_key, segment_id, engine_type)`" + §AD-20 — "state transitions are `draft → verified → committed → reversed`" + §AD-22 — "sign-negating + corrected row + correction_group_id link + 원본 변경 없음" + §AD-25 — "M10 cache key is `(tenant_id, period_key, calculation_result_hash)`. A new AD-4 commit, an AD-22 reversal insert, or an M11 reopen emits one DB notification".

**11-1 ↔ 11-2 ↔ 11-3 wire 정합**:
- 11-1 wire: `apps/api/modules/m11_close/handlers.py` (3 routes: POST reversal-requests + GET reversal-requests/{correction_group_id} + POST cache-invalidation) + `apps/api/main.py` 6 NEW exception handlers (ReversalTargetNotFoundError + ReversalRejectedError + ReversalUnauthorizedError + ReversalDuplicateError + LockedPeriodReversalRejectedError + CacheInvalidationChannelInvalidError) + `apps/api/core/cache_invalidation_publisher.py` (1-channel: ai_cache) + `packages/services/m11_close/{reversal_negating.py, reversal_corrected.py, reversal_authorization.py}` (3 pure kernels) + `packages/services/m5_ledger/{count_period_events.py, query_period_closing_snapshot_all.py}` (H6 fix) + `packages/cost_engine/ports/reversal_port.py` Protocol + Alembic 0019 (reversal_log + cache_invalidation_log) + capability matrix v1.10 (REVERSAL_REQUEST).
- 11-2 wire: `apps/api/alembic/versions/0020_fiscal_periods_close_sequence.py` (NEW, 132 lines) + `apps/api/core/db_models.py` FiscalPeriod ORM (NEW) + `supabase/policies/0011_fiscal_periods_rls.sql` (NEW) + `apps/api/modules/m11_close/services/close_sequence_service.py` (NEW, 565 lines — 4 operations + 5 typed exceptions) + `packages/services/m11_close/{close_sequence_order.py, close_sequence_state.py, partial_close_guard.py}` (3 NEW pure kernels) + 11-1 reversal_authorization.py EXTENSION (fiscal_period_status dual guard) + 11-1 reversal_service.py EXTENSION (fiscal_period_status fetch) + `apps/api/core/audit_action.py` ActionClass.MONTHLY_CLOSING 4 NEW values + `apps/api/core/capability.py` CLOSE_SEQUENCE_LOCK (manufacturing 3종 ✅ / service-only ❌) + `apps/api/main.py` 4 NEW exception handlers (PartialCloseBlockedError + CloseSequenceAlreadyInitiatedError + CloseSequenceStepMismatchError + CloseSequenceCapabilityDeniedError) + capability matrix v1.11.
- 11-3 wire (본 스토리): 11-1 + 11-2 모두 reuse + extend. **fiscal_period_snapshots state='committed' 전이 wire** (close sequence confirmed 후 ledger INSERT 진입점) + **AD-22 reversal sequence fiscal_period_snapshots state='committed'→'reversed' 영구화** (sign-negating + corrected row, AD-22 wire) + **AD-25 cache invalidation multi-channel publisher** (1-channel `ai_cache` → 4-channel + `cost_engine_cache` + `fiscal_period_cache` + `closing_snapshot_cache`) + **W2 reopen flow** (operator action + reason + audit row + AD-25 invalidation, Epic 5 retro §6 W2 deferral) + 11-2 4 DEFER items carry-over (TS mirrors + V8 22→26 fixture + Task 10 frontend + W2 reopen).

**Epic 5 close-out retro (2026-08-07) §7 A9 결정 (Epic 11 reversal module wire 진입점)** — 11-1 wire 시점에 A9 5개 결정 모두 fill 완료 (reversal_negating/reversal_corrected event type + opening_inventory_unlocked action + reversal_request_enabled field wire + service layer reversal handler + UI reversal request form). 본 스토리는 A9 무관 (reversal sequence 자체 이미 wire — AD-22 영구화만).

**Epic 5 close-out retro (2026-08-07) §7 A11 결정 (V8 12 → 18 fixture matrix extension)** — 6-2 spec v1.8 완료 (18 fixture matrix = 12 baseline + 6 closing snapshot + ledger events). 11-2 wire는 4-stage close sequence V8 fixture 4 NEW 추가 (close_sequence_initiated + close_sequence_step_completed_partial_blocked + close_sequence_confirmed + close_sequence_reversal_blocked) — V8 18 → 22 fixture matrix extension. **11-3 wire는 4 NEW snapshot-persistence V8 fixture 추가** (snapshot_committed + reversal_negating_snapshot + reversal_corrected_snapshot + reopen_committed) — **V8 22 → 26 fixture matrix extension**.

**Epic 5 close-out retro (2026-08-07) §7 A10 결정 (MONTHLY_CLOSING_REPORT capability 신규)** — 6-1 wire 완료 (capability matrix v1.8). 11-2 wire는 CLOSE_SEQUENCE_LOCK capability 신규 (v1.11). **11-3 wire는 SNAPSHOT_PERSISTENCE + REVERSAL_EXECUTE capability 2개 신규 (v1.12)** — manufacturing 3종 ✅ / service-only ❌ 결정 (PRD §6.4 + §Q-I 매핑 동일).

**Epic 5 close-out retro (2026-08-07) §6 W2 deferral — Epic 11 close reopen flow (operator action + reason + audit row + AD-25 invalidation)** — 11-2 wire는 reopen 미포함 (operator action entry는 별도 follow-up Story / Epic 11 close-out retro 시점에 결정). **11-3 wire는 W2 reopen flow full wire** (operator action + reason + audit row + AD-25 invalidation) — fiscal_periods.status='closed'→'open' 전이 + AD-22 reversal chain reset.

**Epic 4 close-out retro (2026-08-03) A3 cj-style** — 3-story 분할 유지 (5-1 → 5-2 → 5-3) + Epic 6 6-1/6-2/6-3 동일 패턴. Epic 11 11-1/11-2/11-3 동일 패턴 적용 (Epic 5 retro §6 §11 명시).

**Epic 4 close-out retro (2026-08-03) A5** — A5 Full Phase 1+2+4 done. Epic 5 5-1 + 5-3 + 6-1 + 6-2 + 11-1 + 11-2 audit log 일관성 보장 + A5 forward-lock + drift detector pattern 정착. **11-3 wire 동일 패턴 적용** (SnapshotPersistenceAction 4 NEW values fill + ActionClass.MONTHLY_CLOSING frozenset fill + drift detector 3-way extension).

**Epic 4 close-out retro (2026-08-03) A7** — Epic 4 carry (async test pattern + SDR overclaim) Epic 5 + 6-1 + 6-2 + 11-1 + 11-2 wire. **11-3 동일 적용** (asyncio.run wrapper + SDR drift detector regeneration).

**Story 0-2 (2026-07-29)** — RLS 인프라 + audit_logs INSERT-only with `BEFORE UPDATE OR DELETE` trigger 패턴이 Epic 0에서 wire됨. AD-2 + AD-3 SSOT. **11-3 wire는 RLS 위에서 동작 (fiscal_period_snapshots tenant-scoped + AD-25 cache_invalidation_log RLS-scoped)**.

**Story 0-5 (2026-08-05)** — frontend plumbing wire ✅ done (commit ead1974). shadcn Card / Tabs / sonner / vitest + RTL + MSW / Playwright / next-intl / INDUSTRY_ICON fill. **11-3 frontend 진입 전 dep satisfied**. SnapshotPersistencePanel + ReversalSnapshotReadOnlyPanel + ReopenOperatorDialog + cache_invalidation channel 4 UI 진입점 가능.

**Story 1.1 (2026-07-29)** — Industry enum SSOT (manufacturing / manufacturing_service / service / manufacturing_service_other) + capability matrix v1.0. **11-3 capability gate = SNAPSHOT_PERSISTENCE + REVERSAL_EXECUTE** (manufacturing 3종 ✅ / service-only ❌ — 6-1/6-2/11-1/11-2 wire 동일 패턴).

**Story 3.1 (2026-08-01)** — monthly_input_periods + monthly_input_rows 테이블. **11-3 wire는 monthly_input_periods.status='closed' 전이 → fiscal_periods.status='closed' cascading (11-2 wire) → fiscal_period_snapshots state='committed' 전이 (11-3 wire)**.

**Story 4.1 (2026-08-02)** — engine returns state='draft' (AD-22 boundary strengthening). **11-3 wire는 fiscal_period_snapshots state machine 'verified'→'committed'→'reversed' (M11 territory, AD-20) + engine 'draft'→'verified' (M3 territory, AD-20)**.

**Story 4.2 (2026-08-03)** — REPEATABLE READ + audit-first (CR 1.1) + calc_log + AD-22 state transition. **4-2 wire는 fiscal_period_snapshots state='verified' INSERT 진입점** (Alembic 0012). **11-3 wire는 state='committed' 전이 + AD-22 reversal 'reversed' 전이 + W2 reopen 'open' 전이** (M11 territory).

**Story 4.4 (2026-08-03)** — A5 forward-lock + 12 fixture matrix + V8 byte-identical CI gate. **11-3 wire는 V8 22→26 fixture matrix extension (4 NEW snapshot-persistence 골든 fixture)**.

**Story 5.2 (2026-08-04, commit 7a13eb9)** — inventory_ledger append-only events + 4 routes + 11 values event_type CHECK + PostgreSQL BEFORE UPDATE OR DELETE row-level trigger + AD-22 reversal entrypoint forward-fill. **5-2 carry-over to 11-3**: 
  (a) `reversal_negating` + `reversal_corrected` 11-value event_type (Alembic 0015 lines 92-110) 이미 wire — 11-3 wire와 호환.
  (b) `reverses_event_id` + `correction_group_id` 컬럼 (nullable UUID, no FK) 이미 wire — 11-3 wire 호환.
  (c) `uq_inventory_ledger_reverses_event_id` UNIQUE `(tenant_id, reverses_event_id) WHERE reverses_event_id IS NOT NULL` (Alembic 0015 lines 197-201) 이미 wire — 11-3 AD-22 reversal sequence 영구화 호환.
  (d) `inventory_ledger_reversal_coherence` CHECK (Alembic 0015 lines 162-175) 이미 wire.
  (e) `inventory_ledger_qty_signed_coherence` CHECK (Alembic 0015 lines 125-142) — reversal_negating 음수 qty 허용.

**Story 6.1 (2026-08-08, commit 418ca2d)** — closing_period service + closing_snapshot ledger event wire + V4 verification. **6-1 carry-over to 11-3**:
  (a) `closing_period_service.py:259` `confirm_closing_period` — 11-3 wire는 `commit_snapshot_persistence` (close sequence confirmed 후 진입점).
  (b) `MonthlyInputStateResponse.closing_period_state` field — 11-3 wire 시점에 3 NEW fields extension (`snapshot_persistence_state` + `reversal_log_size` + `reopen_allowed`).
  (c) `ActionClass.CLOSING_PERIOD` 3 values (`closing_period_confirmed` / `closing_period_blocked` / `closing_period_snapshot_inconsistency`) — 11-3 wire 시점에 4 NEW values fill (`snapshot_persistence_committed` + `snapshot_persistence_reversed` + `reopen_authorized` + `reopen_completed`).

**Story 6.2 (2026-08-08, commit 30d6455)** — monthly closing report + V8 18-fixture matrix extension. **6-2 carry-over to 11-3**: 11-3 wire 시점에 snapshot-persistence + reversal V8 fixture matrix extension (4 NEW 골든 fixture: snapshot_committed + reversal_negating_snapshot + reversal_corrected_snapshot + reopen_committed). V8 22 → 26 fixture matrix. byte-identical CI gate 동일 패턴.

**Story 11.1 (2026-08-08, commit b4961a6)** — M11 module authority + AD-22 reversal ledger wire + A9 fill + H6 fix + AD-25 1-channel. **11-1 carry-over to 11-3**: 
  (a) `apps/api/modules/m11_close/` populated — 본 스토리에서 snapshot_persistence + reversal_execute service layer 추가.
  (b) `packages/services/m11_close/reversal_negating.py` + `reversal_corrected.py` (3 pure kernels) — 11-3 wire 시점에 fiscal_period_snapshots state='reversed' 영구화 + 4 NEW audit emit hook 추가.
  (c) `apps/api/core/audit_action.py` `ActionClass.REVERSAL_LOG` 5 values — 11-3 wire는 4 NEW values fill (`snapshot_persistence_committed` + `snapshot_persistence_reversed` + `reopen_authorized` + `reopen_completed`).
  (d) `Capability.REVERSAL_REQUEST` (manufacturing 3종 ✅ / service-only ❌) — 11-3 wire 시점에 SNAPSHOT_PERSISTENCE + REVERSAL_EXECUTE 2개 신규 fill (v1.12).
  (e) `apps/api/core/cache_invalidation_publisher.py` (NEW, AD-25 1-channel) — **11-3 wire 시점에 multi-channel full wire (1 → 4 channels: ai_cache + cost_engine_cache + fiscal_period_cache + closing_snapshot_cache)**.
  (f) `apps/api/main.py` 6 NEW exception handlers — **11-3 wire 시점에 4 NEW extension (SnapshotAlreadyCommittedError + ReversalSnapshotMismatchError + ReopenOperatorActionInvalidError + ReopenAuditEmitFailedError)**.

**Story 11.2 (2026-08-08, commit caacfc7)** — fiscal_periods greenfield + 4-stage close_sequence_state + partial close guard + AD-6 INSERT 거부 + 11-1 reversal_authorization 양쪽 가드. **11-2 carry-over to 11-3**: 
  (a) `apps/api/modules/m11_close/services/close_sequence_service.py` `confirm_close_sequence` flow — 11-3 wire 시점에 step (4) `commit_snapshot_persistence` 호출 추가 (fiscal_period_snapshots state='committed' 전이).
  (b) `packages/services/m11_close/close_sequence_state.py` `check_ad6_insert_allowed` — 11-3 wire 시점에 `fiscal_period_snapshots` table 추가 (AD-6 lock targets).
  (c) `ActionClass.MONTHLY_CLOSING` 4 values fill — 11-3 wire 무관 (closing sequence 4-stage만, snapshot persistence는 별도 ActionClass.SNAPSHOT_PERSISTENCE).
  (d) `Capability.CLOSE_SEQUENCE_LOCK` (manufacturing 3종 ✅ / service-only ❌) — 11-3 wire 시점에 SNAPSHOT_PERSISTENCE + REVERSAL_EXECUTE 2개 신규 추가 (v1.12).
  (e) 11-2 DEFER 4 items carry-over (본 스토리 AC #7) — TS mirrors (`apps/web/lib/m11-close-sequence.ts`) + V8 22→26 fixture (4 NEW snapshot-persistence 골든) + Task 10 frontend (CloseSequencePanel + StepCompleteButton + ConfirmButton) + W2 reopen flow.

**A9 (Epic 5 retro §7 결정, 2026-08-07)** — Epic 11 reversal module wire 진입점. 11-1 spec 진입 시점에 결정. 11-2 wire는 A9 무관 (reversal sequence 가드 확장만). 11-3 wire는 A9 follow-up 결정 2건 fill — **(a) fiscal_period_snapshots state='reversed' 시 report read policy** (read-only 표시 vs hidden) + **(b) AD-25 cache invalidation 채널 결정 (4채널 확정)**.

**A11 (Epic 5 retro §7 결정, 2026-08-07)** — V8 12 → 18 → 22 → 26 fixture matrix extension. 6-2 spec v1.8 완료 (18 fixture). 11-2 wire는 V8 18 → 22 fixture matrix extension (4 NEW close sequence 골든 fixture). **11-3 wire는 V8 22 → 26 fixture matrix extension (4 NEW snapshot-persistence + reversal + reopen 골든 fixture)**.

**AD-1 (modular monolith + hexagonal core)** — 11-3 wire는 engine port + service layer + handlers 표준 3-tier 패턴 (5-1/5-2/5-3/6-1/6-2/11-1/11-2 동일). `packages/services/m11_close/` 3 NEW pure kernels + `apps/api/modules/m11_close/services/{snapshot_persistence_service.py, reversal_execute_service.py, reopen_service.py}` (3 NEW) + `apps/api/modules/m11_close/handlers.py` EXTENSION (4 NEW routes).

**AD-2 (append-only ledger)** — 11-3 wire 호환. 4-2 fiscal_period_snapshots SSOT + 5-2 inventory_ledger SSOT + PostgreSQL `BEFORE UPDATE OR DELETE` trigger 보존. fiscal_periods.status='closed' 후 AD-22 reversal INSERT + snapshot_persistence INSERT + reopen UPDATE 모두 AD-6 exception chain 위 동작.

**AD-3 (multi-tenant RLS)** — 11-3 wire는 RLS 위에서 동작. `tenant_id` 자동 derive from JWT (AD-3 SSOT). fiscal_period_snapshots RLS policy + cache_invalidation_log RLS policy 모두 RLS-scoped.

**AD-6 (close lock)** — 11-3 wire 호환. `fiscal_periods.status='closed'` 후 모든 business-data INSERT 거부 (Architecture Spine §AD-6 Rule 그대로). AD-22 reversal/correction events + AD-25 cache_invalidation_log INSERT만 허용. W2 reopen flow는 fiscal_periods.status='closed' → 'open' 전이 시 operator action + reason + audit row + AD-25 invalidation 동시 dispatch.

**AD-11 (dependency direction / layer rule)** — pure helpers = `packages/services/m11_close/` 3 NEW pure kernels (`commit_snapshot_persistence.py` + `reversal_execute_snapshot.py` + `reopen_authorization.py`). service layer = `apps/api/modules/m11_close/services/{snapshot_persistence_service.py, reversal_execute_service.py, reopen_service.py}` (3 NEW). handlers = `apps/api/modules/m11_close/handlers.py` EXTENSION (4 NEW routes). engine layer (`packages/cost_engine/`) 무변경 (engine은 snapshot persistence 의미 모름 — 4-2 wire 패턴).

**AD-15 (cross-language parity)** — TS mirror `apps/web/lib/m11-snapshot-persistence.ts` (NEW) + `apps/web/lib/m11-reversal-execute.ts` (NEW) + `apps/web/lib/m11-reopen.ts` (NEW) + Decimal serialization parity (close sequence state = 'divisions' | 'manufacturing' | 'abc' | 'common' | 'confirmed', snapshot persistence state = 'verified' | 'committed' | 'reversed', reopen state = 'authorized' | 'completed', banker's rounding to int for 4-stage progress indicator + reversal chain length).

**AD-16 (Fiscal snapshot contract)** — 11-3 wire PRIMARY AC. **`fiscal_period_snapshots` uniquely keyed by `(tenant_id, period_key, segment_id, engine_type)`** + normalized `material_cost` + `labor_cost` + `overhead_cost` + `manufacturing_cost` + `inventory_adjustment` + `state` (verified | committed | reversed) + deterministic `result_hash`. **M3 = only writer (verified INSERT)**. **M11 = read-only consumer (committed/reversed state transition via separate INSERT not UPDATE)**. **Opaque result JSON forbidden**.

**AD-20 (Calculation result state machine)** — 11-3 wire PRIMARY AC. **state transitions = `draft → verified → committed → reversed`**. `draft` and `verified` are transaction-internal (M3). Only `committed` rows feed M5 or authoritative APIs. `reversed` is represented by an append-only AD-22 event and never by mutating the committed row (Architecture Spine §AD-20 Rule).

**AD-22 (Reversal construction and ownership)** — 11-3 wire PRIMARY AC. **correction inserts (1) one sign-negating reversal row with `reverses_event_id` and `reversal_of_period_key` + (2) optional corrected business row sharing `correction_group_id`**. **original never changes**. **`(tenant_id, reverses_event_id)` is unique**. M11 owns the sequence (11-1 wire + 11-3 영구화 확장).

**AD-25 (Cache invalidation notification)** — 11-3 wire PRIMARY AC. **M10 cache key = `(tenant_id, period_key, calculation_result_hash)`**. A new AD-4 commit + an AD-22 reversal insert + an M11 reopen emits **one DB notification** per channel (4 channels: ai_cache + cost_engine_cache + fiscal_period_cache + closing_snapshot_cache). M10 adapter consumes + invalidates matching entries. **Application polling + input-write-only invalidation forbidden**.

**AD-23 (4-namespace pattern)** — monthly_input_periods + monthly_input_rows + inventory_ledger + audit_logs + fiscal_period_snapshots (M3 writer only) + fiscal_periods (M11 module authority 11-2 wire) + reversal_log (M11 reversal observability 11-1 wire) + cache_invalidation_log (M11 AD-25 audit 11-1 wire) = 8 namespace.

**AD-24 (typed period-key)** — 'YYYY-MM' 형식 SSOT. fiscal_periods.period_key + fiscal_period_snapshots.period_key + monthly_input_periods.period_key 동일.

**PRD §F11.1 (Close sequence lock)** — 11-2 PRIMARY AC. "부문분할→제조→ABC→공동 순서 + 부분 마감 없음" 명시. 4-stage close sequence order 강제. 11-3 wire는 11-2 wire 위에 additive (close sequence confirmed 후 snapshot persistence 진입).

**PRD §F11.2 (Snapshot persistence)** — 11-3 PRIMARY AC. "마감 완료 시 계산 결과 전체 스냅샷 고정 + 이후 입력·변경은 역분개(A8)로만" 명시. 4-2 wire `fiscal_period_snapshots` table + 11-3 wire state='committed' 전이.

**PRD §F11.3 (Reversal sequence)** — 11-3 PRIMARY AC. "마감 후 오류를 발견하면 역분개로만 수정 가능한 것" + "(1) 부호 반전 row 1개 INSERT (`reverses_event_id` link) + (2) corrected row INSERT (`correction_group_id` link) — 원본 row 변경 없음 (AD-22)" + "`(tenant_id, reverses_event_id)` unique 제약 보장" + "재무 효과는 `committed → reversed` 상태로 정확히 0에 수렴" + "M10 캐시 무효화 notification 자동 발행 (AD-25)".

**PRD §8.M11(a)** — "시스템은 부문분할 → 제조 → ABC → 공동 순서를 강제하고, 부분 마감을 허용하지 않는다" 명시. 11-2 PRIMARY AC.

**PRD §8.M11(b)** — "마감 완료 시 계산 결과 전체 스냅샷 고정 + 이후 입력·변경은 역분개(A8)로만" 명시. **11-3 PRIMARY AC**.

**PRD §6.4 (industry × engine mapping)** — "제조 부문 → 전통 개별원가 엔진 / 서비스 부문 → ABC 엔진(classic + TDABC)". 4-stage 순서의 divisions → manufacturing → ABC → common 매핑.

**PRD §Q-I (industry × engine 고정 매핑)** — "제조 ABC는 3차 로드맵". 11-3 wire 시점에 SNAPSHOT_PERSISTENCE + REVERSAL_EXECUTE capability 모두 manufacturing 3종 ✅ / service-only ❌ 결정.

**PRD §8.0 (A2 audit-first + idempotent no-op)** — CR 1.1 SSOT. 11-3 wire 모두 audit-first + idempotent no-op (fiscal_period_snapshots state='committed' 후 re-commit 시도 → no-op skip).

**PRD §A11 (3-layer defense)** — "입력 시 경고 + 마감 시 차단". 11-3 wire는 마감 시 차단 (Layer 2 = 5-3 closing_guard + 11-2 4-stage close sequence 4 검증) + 마감 확정 시 snapshot 영구 보존 (Layer 3 = 11-3 commit_snapshot_persistence) + 마감 후 reversal (Layer 4 = 11-3 reversal_execute 영구화) + reopen (Layer 5 = 11-3 W2 reopen flow).

**PRD §8.M11 (마감 후 입력 수정은 역분개로만)** — 11-1 wire (`monthly_input_periods.status='closed'` reversal 허용) + 11-2 wire (`fiscal_periods.status='closed'` 추가 가드) + **11-3 wire (`fiscal_period_snapshots state='committed'` 후 reversal INSERT로만 수정 가능 — AD-22 영구화)**.

**PRD §8.M11 (마감 후 원본 변경 금지)** — 11-1 wire (AD-22 reversal sequence INSERT만 허용) + 11-2 wire (fiscal_periods.status='closed' 후 business-data INSERT 거부) + **11-3 wire (fiscal_period_snapshots state='committed' → 'reversed' 전이 시 AD-22 reversal INSERT 영구화 + 0에 수렴)**.

## Story

As a **회계사/사장님**,
I want **마감 완료 시점에 모든 계산 결과가 스냅샷으로 영구 보존되고, 이후 오류 발견 시 역분개(부호 반전 + 정정 row)로만 수정 가능하며, 운영자는 사유 + 감사 기록 + 캐시 무효화로 다시 열 수 있는 것**,
so that **마감본 = 영구본 + 감사 추적 보장 + 운영자 복구 가능 + M10 AI 캐시 자동 폐기**.

## Acceptance Criteria

1. **fiscal_period_snapshots state='verified'→'committed' 전이 (PRD §F11.2 PRIMARY, AD-20/AD-16 wire)**
   - (a) `apps/api/modules/m11_close/services/snapshot_persistence_service.py` (NEW service layer) — `commit_snapshot_persistence(period_key, *, actor_id) -> dict[str, Any]`:
     - SELECT FOR UPDATE on `fiscal_periods` (6-1 wire 패턴 동일 + 11-2 wire fiscal_periods 추가)
     - fiscal_periods.status='closed' + close_sequence_state='confirmed' 검증 (11-2 wire close sequence confirmed 후 진입점)
     - fiscal_period_snapshots state='verified' → 'committed' 전이 (UPDATE + audit-first emit)
     - **M3 = only writer** (AD-16 SSOT). M11은 별도 INSERT 발행 (M11은 read-only consumer). 4-2 wire의 `fiscal_period_snapshots` table은 **M3 INSERT (verified) + M11 UPDATE (verified → committed)** dual-writer (AD-16 interpretation — M3 writes INSERT, M11 writes state transition only).
     - audit-first emit (`snapshot_persistence_committed`, AD-15 §11 Korean message)
     - 4 NEW AD-25 cache_invalidation publish (4 channels: ai_cache + cost_engine_cache + fiscal_period_cache + closing_snapshot_cache) — see AC #3
   - (b) `packages/services/m11_close/commit_snapshot_persistence.py` (NEW pure kernel) — `validate_commit_snapshot_persistence(fiscal_periods_row, fiscal_period_snapshots_row) -> CommitSnapshotPersistenceResult` (stdlib-only, AD-11 layer rule)
     - 검증 규칙: `fiscal_periods_row.status == 'closed' AND fiscal_periods_row.close_sequence_state == 'confirmed' AND fiscal_period_snapshots_row.state == 'verified'`
     - 검증 규칙: `fiscal_period_snapshots_row.segment_id NOT NULL AND fiscal_period_snapshots_row.engine_type IN ('trad', 'abc', 'budget')`
     - `CommitSnapshotPersistenceResult` NamedTuple: `valid: bool`, `violations: tuple[str, ...]`, `transition_state: str` ('committed')
     - `COMMIT_SNAPSHOT_PERSISTENCE_VIOLATIONS_KO` Korean constants: "마감 시퀀스 미확정" + "스냅샷 미검증" + "스냅샷 분기 미설정" + "엔진 타입 미지원"
   - (c) `packages/services/m11_close/commit_snapshot_persistence.py` ~20 pure tests (close sequence confirmed + verified state + segment_id null + engine_type invalid + dual-row validation + idempotent re-commit no-op)
   - (d) `apps/web/lib/m11-snapshot-persistence.ts` (NEW TS mirror) — `validateCommitSnapshotPersistence()` 함수 + `COMMIT_SNAPSHOT_PERSISTENCE_VIOLATIONS_KO` constants verbatim + Decimal 직렬화 parity (banker's rounding)
   - (e) `apps/web/lib/m11-snapshot-persistence-parity.ts` (NEW TS parity test) — Python pure kernel ↔ TS mirror 5 cases (validate parity, edge cases, idempotent invariants) — 11-1/11-2 TS parity 패턴 동일
   - (f) Idempotent no-op skip: `fiscal_period_snapshots.state='committed'` 후 re-commit 시도 → `SnapshotAlreadyCommittedError` (409 SNAPSHOT_ALREADY_COMMITTED) typed envelope + audit emit skip

2. **AD-22 reversal sequence fiscal_period_snapshots state='committed'→'reversed' 영구화 (PRD §F11.3 PRIMARY, AD-20/AD-22 wire)**
   - (a) `apps/api/modules/m11_close/services/reversal_execute_service.py` (NEW service layer) — `execute_reversal(period_key, target_snapshot_id, *, reason: str, actor_id) -> dict[str, Any]`:
     - SELECT FOR UPDATE on `fiscal_period_snapshots` (target row)
     - fiscal_periods.status='closed' + close_sequence_state='confirmed' + fiscal_period_snapshots.state='committed' 검증 (AD-22 + AD-6 + 11-2 wire 정합)
     - 11-1 wire `packages/services/m11_close/reversal_authorization.py` dual guard (monthly_input_periods.status='closed' + fiscal_periods.status='closed') 통과 필수
     - 11-1 wire `reversal_negating.py` + `reversal_corrected.py` pure kernel 호출 — AD-22 sign-negating + corrected row INSERT (correction_group_id link + reverses_event_id link)
     - fiscal_period_snapshots.state='committed' → 'reversed' UPDATE (AD-20 state transition)
     - audit-first emit (`snapshot_persistence_reversed` + `reversal_logged`, AD-15 §11 Korean)
     - **재무 효과 0에 수렴 검증** — corrected row 의 material_cost + labor_cost + overhead_cost + manufacturing_cost + inventory_adjustment 합 = original row 의 합 (banker's rounding parity, AD-15 §11)
     - 4 NEW AD-25 cache_invalidation publish (4 channels) — see AC #3
   - (b) `packages/services/m11_close/reversal_execute_snapshot.py` (NEW pure kernel) — `validate_reversal_execute_snapshot(fiscal_periods_row, target_snapshot_row, negating_row, corrected_row) -> ReversalExecuteSnapshotResult` (stdlib-only)
     - 검증 규칙: `fiscal_periods_row.status == 'closed' AND target_snapshot_row.state == 'committed'`
     - 검증 규칙: `(tenant_id, target_snapshot_row.snapshot_id) UNIQUE` — AD-22 `(tenant_id, reverses_event_id)` unique constraint 활용
     - 검증 규칙: `corrected_row IS NULL OR sum(corrected_row.{material_cost,labor_cost,overhead_cost,manufacturing_cost,inventory_adjustment}) == sum(target_snapshot_row.{...})` — banker's rounding parity
     - `ReversalExecuteSnapshotResult` NamedTuple: `valid: bool`, `violations: tuple[str, ...]`, `correction_group_id: uuid.UUID`
     - `REVERSAL_EXECUTE_SNAPSHOT_VIOLATIONS_KO` Korean constants
   - (c) `packages/services/m11_close/reversal_execute_snapshot.py` ~25 pure tests (close sequence confirmed + committed state + unique constraint + corrected row null + sum parity 5 cases + 4 violation cases)
   - (d) 11-1 wire `packages/services/m11_close/reversal_authorization.py` EXTENSION — `authorize_reversal()` 함수 `fiscal_period_snapshots.state='committed'` 추가 dispatch (3-tier 가드: monthly_input_periods.status='closed' + fiscal_periods.status='closed' + fiscal_period_snapshots.state='committed' 모두 통과)
   - (e) `apps/api/modules/m11_close/services/reversal_service.py` (11-1 wire EXTENSION) — `execute_reversal()` 함수:
     - `fiscal_period_snapshots` row fetch (state='committed' 검증)
     - `authorize_reversal` 호출 시 `snapshot_state='committed'` 추가 전달
     - `reversal_execute_service.execute_reversal` dispatch
   - (f) `apps/web/lib/m11-reversal-execute.ts` (NEW TS mirror) + `apps/web/lib/m11-reversal-execute-parity.ts` (NEW TS parity test) — Python pure kernel ↔ TS mirror 5 cases

3. **AD-25 cache invalidation multi-channel full wire (1 → 4 channels: ai_cache + cost_engine_cache + fiscal_period_cache + closing_snapshot_cache)**
   - (a) `apps/api/core/cache_invalidation_publisher.py` (11-1 wire EXTENSION) — `ALLOWED_CHANNELS` FROZENSET 1 → 4 channels 확장:
     - `ai_cache` (11-1 wire 보존) — M10 AI cache invalidation target
     - `cost_engine_cache` (11-3 NEW) — M3 cost engine calculation result cache
     - `fiscal_period_cache` (11-3 NEW) — M11 fiscal_periods + fiscal_period_snapshots metadata cache
     - `closing_snapshot_cache` (11-3 NEW) — M11 closing_snapshot + ledger closing event cache
     - 4 channels 모두 tuple immutable (frozen list로 sorting + 비교 가능)
   - (b) `apps/api/core/cache_invalidation_publisher.py` — `publish()` 메서드 EXTENSION:
     - 4 channels 모두 optional: 단일 publish 1개 OR multi-channel publish 4개 동시 (broadcast)
     - `publish_multi(channels: list[str], ...)` 신규 메서드 — multi-channel broadcast (close sequence confirmed + reversal + reopen 시 4 channel 동시 publish)
   - (c) `apps/api/alembic/versions/0021_cache_invalidation_multi_channel.py` (NEW migration) — `down_revision='0020_fiscal_periods_close_sequence'` (11-2 wire tip):
     - `cache_invalidation_log` table channel CHECK constraint 확장: `CHECK (channel IN ('ai_cache', 'cost_engine_cache', 'fiscal_period_cache', 'closing_snapshot_cache'))`
     - 4 channels 별도 index — query performance (cache_invalidation_log lookup by channel + tenant_id + correction_group_id)
   - (d) 11-1 wire 3 routes EXTENSION:
     - `POST /api/v1/close/reversal-requests` — 4 channels publish (ai_cache + cost_engine_cache + fiscal_period_cache + closing_snapshot_cache)
     - `POST /api/v1/close/cache-invalidation` — multi-channel publish 1개 OR list of channels 입력
     - 11-3 wire 시점에 4 NEW routes 추가:
       - `POST /api/v1/close/snapshot/commit` — commit_snapshot_persistence (SNAPSHOT_PERSISTENCE capability gate) — see AC #1
       - `POST /api/v1/close/snapshot/reverse` — execute_reversal (REVERSAL_EXECUTE capability gate) — see AC #2
       - `POST /api/v1/close/reopen` — reopen_closed_period (REOPEN_OPERATOR capability gate) — see AC #4
       - `GET /api/v1/close/snapshot/{period_key}` — read fiscal_period_snapshots state (read-only, no capability gate)
   - (e) `apps/api/main.py` 4 NEW exception handlers wire:
     - `SnapshotAlreadyCommittedError` (409 SNAPSHOT_ALREADY_COMMITTED)
     - `ReversalSnapshotMismatchError` (409 REVERSAL_SNAPSHOT_MISMATCH)
     - `ReopenOperatorActionInvalidError` (422 REOPEN_OPERATOR_ACTION_INVALID)
     - `ReopenAuditEmitFailedError` (500 REOPEN_AUDIT_EMIT_FAILED)
   - (f) `CacheInvalidationChannelInvalidError` 11-1 wire 보존 — channel not in FROZENSET (1 → 4 channels) 자동 dispatch
   - (g) `apps/web/lib/m11-cache-invalidation.ts` (NEW TS mirror) — `ALLOWED_CHANNELS` 4 channels constant + `publishMulti()` 함수 + Decimal 직렬화 parity

4. **W2 reopen flow (operator action + reason + audit row + AD-25 invalidation, Epic 5 retro §6 W2 deferral)**
   - (a) `apps/api/modules/m11_close/services/reopen_service.py` (NEW service layer) — `reopen_closed_period(period_key, *, operator_action: str, reason: str, actor_id) -> dict[str, Any]`:
     - SELECT FOR UPDATE on `fiscal_periods` (status='closed' 검증)
     - **operator_action 검증** — `operator_action in ('operator_reopen', 'audit_finding', 'legal_compliance', 'data_correction')` enum (AD-10 + PRD §F11.2 + Epic 5 retro §6 W2 명시)
     - **reason 검증** — `len(reason) >= 20 AND len(reason) <= 500` (audit trail 충분 + DoS 방지)
     - 11-3 wire `packages/services/m11_close/reopen_authorization.py` (NEW pure kernel) 호출 — authorization 검증
     - **fiscal_periods.status='closed' → 'open' 전이** (AD-6 reverse direction, operator action 기반)
     - **fiscal_period_snapshots state='committed' → 'reversed' 전이** (AD-22 reopen chain) — AD-22 reversal event INSERT (operator action + reason + audit row)
     - **AD-25 cache invalidation 4 channels publish** (close → reopen 시 4 channel 동시 publish)
     - audit-first emit (`reopen_authorized` + `reopen_completed`, AD-15 §11 Korean)
   - (b) `packages/services/m11_close/reopen_authorization.py` (NEW pure kernel) — `validate_reopen_authorization(operator_action: str, reason: str, fiscal_periods_row) -> ReopenAuthorizationResult` (stdlib-only)
     - 검증 규칙: `operator_action in REOPEN_OPERATOR_ACTIONS` (4 values enum)
     - 검증 규칙: `20 <= len(reason) <= 500` (audit trail 강제)
     - 검증 규칙: `fiscal_periods_row.status == 'closed'` (only closed period can be reopened)
     - 검증 규칙: `fiscal_periods_row.close_sequence_state == 'confirmed'` (only confirmed close sequence can be reopened)
     - `ReopenAuthorizationResult` NamedTuple: `valid: bool`, `violations: tuple[str, ...]`, `reopen_state: str` ('authorized' | 'completed')
     - `REOPEN_AUTHORIZATION_VIOLATIONS_KO` Korean constants
   - (c) `packages/services/m11_close/reopen_authorization.py` ~20 pure tests (4 operator_action + reason length bounds 5 cases + closed status + confirmed state + 4 violation cases)
   - (d) `apps/web/lib/m11-reopen.ts` (NEW TS mirror) + `apps/web/lib/m11-reopen-parity.ts` (NEW TS parity test) — Python pure kernel ↔ TS mirror 5 cases
   - (e) `apps/api/main.py` 4 NEW exception handlers wire (AC #3 (e)와 동일)
   - (f) `ReopenOperatorActionInvalidError` (422 REOPEN_OPERATOR_ACTION_INVALID) — operator_action not in 4-value enum OR reason length invalid

5. **capability matrix v1.12 (SNAPSHOT_PERSISTENCE + REVERSAL_EXECUTE + REOPEN_OPERATOR 신규 — manufacturing 3종 ✅ / service-only ❌)**
   - (a) `apps/api/core/capability.py` (EXTENSION) — 3 NEW capabilities:
     - `Capability.SNAPSHOT_PERSISTENCE` (manufacturing 3종 ✅ / service-only ❌) — PRD §F11.2 + §Q-I 매핑
     - `Capability.REVERSAL_EXECUTE` (manufacturing 3종 ✅ / service-only ❌) — PRD §F11.3 + §Q-I 매핑
     - `Capability.REOPEN_OPERATOR` (manufacturing 3종 ✅ / service-only ❌) — Epic 5 retro §6 W2 + §Q-I 매핑 (operator action entry는 owner-only)
   - (b) `apps/api/modules/m11_close/handlers.py` (EXTENSION) — 4 NEW routes 진입 시 capability gate:
     - `POST /api/v1/close/snapshot/commit` — commit_snapshot_persistence (SNAPSHOT_PERSISTENCE capability gate)
     - `POST /api/v1/close/snapshot/reverse` — execute_reversal (REVERSAL_EXECUTE capability gate)
     - `POST /api/v1/close/reopen` — reopen_closed_period (REOPEN_OPERATOR capability gate)
     - `GET /api/v1/close/snapshot/{period_key}` — read fiscal_period_snapshots state (no capability gate, read-only)
   - (c) `docs/capability-matrix.md` v1.12 (EXTENSION) — SNAPSHOT_PERSISTENCE + REVERSAL_EXECUTE + REOPEN_OPERATOR 3 NEW capability 행 추가 + 6-1 CLOSING_GUARD + 6-2 MONTHLY_CLOSING_REPORT + 11-1 REVERSAL_REQUEST + 11-2 CLOSE_SEQUENCE_LOCK 보존
   - (d) Capability matrix drift detector (`tests/services/test_capability_matrix_drift.py` EXTENSION) — 3 NEW cases (SNAPSHOT_PERSISTENCE + REVERSAL_EXECUTE + REOPEN_OPERATOR 등록 검증 + 4-industry × 7-capability 매트릭스 + AD-15 §11 SSOT consistency)
   - (e) `REOPEN_OPERATOR` capability는 AD-10 owner-only role gate 동반 (CRITICAL — operator action은 owner 권한자만) — `require_role("owner")` chain

6. **A5 forward-lock (ActionClass.SNAPSHOT_PERSISTENCE 4 NEW values fill + ActionClass.REOPEN_OPERATOR 2 NEW values fill + drift detector 3-way extension)**
   - (a) `apps/api/core/audit_action.py` (EXTENSION) — `ActionClass.SNAPSHOT_PERSISTENCE` 4 NEW values fill:
     - `snapshot_persistence_committed` — commit_snapshot_persistence succeeded (fiscal_period_snapshots state='committed')
     - `snapshot_persistence_reversed` — execute_reversal succeeded (fiscal_period_snapshots state='reversed')
     - `snapshot_persistence_blocked` — AD-22 reversal 거부 (correction_group_id 충돌 or sum parity 위반 → 409 REVERSAL_SNAPSHOT_MISMATCH)
     - `snapshot_persistence_reopened` — reopen_closed_period succeeded (fiscal_period_snapshots state='reopened' + AD-25 4 channels publish)
   - (b) `apps/api/core/audit_action.py` (EXTENSION) — `ActionClass.REOPEN_OPERATOR` 2 NEW values fill:
     - `reopen_authorized` — reopen_authorization validation passed (operator_action enum + reason length bounds)
     - `reopen_completed` — reopen_closed_period succeeded (fiscal_periods.status='open' 전이 + AD-25 4 channels publish)
   - (c) `apps/api/core/audit_action.py:170-173` `ActionClass.REVERSAL_LOG` 5 values 11-1 wire 보존 + `ActionClass.MONTHLY_CLOSING` 4 values 11-2 wire 보존 + `ActionClass.SNAPSHOT_PERSISTENCE` 4 NEW values 11-3 wire + `ActionClass.REOPEN_OPERATOR` 2 NEW values 11-3 wire = 4 separate frozenset (CR 1.1 wire 무관, A5 forward-lock 보존)
   - (d) `tests/services/test_audit_action_centralization.py` (EXTENSION) — `ActionClass.SNAPSHOT_PERSISTENCE` 4 NEW values + `ActionClass.REOPEN_OPERATOR` 2 NEW values registered verification (AST-grep `emit_audit_typed` hits = 0 유지)
   - (e) `tests/integration/test_audit_action_consistency.py` (EXTENSION) — 3-way drift detector (registry ↔ DB CHECK ↔ call sites) — 6 NEW cases (snapshot_persistence_committed + snapshot_persistence_reversed + snapshot_persistence_blocked + snapshot_persistence_reopened + reopen_authorized + reopen_completed)

7. **11-2 DEFER 4 items carry-over (TS mirrors + V8 fixture + Task 10 frontend + W2 reopen)**
   - (a) **TS mirrors carry-over** (11-2 DEFER 1차 — 본 스토리 AC #1 (d)+(e) + AC #2 (f) + AC #3 (g) + AC #4 (d)에서 partial wire):
     - `apps/web/lib/m11-close-sequence.ts` (11-2 DEFER) — TS mirror for close_sequence_order + close_sequence_state + check_ad6_insert_allowed (11-2 spec §AC #2 (c) + §AC #4 (d))
     - `apps/web/lib/m11-close-sequence-parity.ts` (11-2 DEFER) — TS parity test (11-2 spec §AC #2 (d))
     - **본 스토리 AC #1 (d)+(e) + AC #2 (f) + AC #3 (g) + AC #4 (d) 4 NEW TS mirror + parity files 통합 wire** (11-2 DEFER items + 11-3 NEW items 동시 wire)
   - (b) **V8 22 → 26 골든 fixture matrix extension** (11-2 DEFER 2차):
     - `packages/cost_engine/tests/regression_v8/fixtures/snapshot_committed.json` (NEW 골든 fixture — 11-3 AC #1 commit_snapshot_persistence)
     - `packages/cost_engine/tests/regression_v8/fixtures/reversal_negating_snapshot.json` (NEW 골든 fixture — 11-3 AC #2 execute_reversal sign-negating)
     - `packages/cost_engine/tests/regression_v8/fixtures/reversal_corrected_snapshot.json` (NEW 골든 fixture — 11-3 AC #2 execute_reversal corrected)
     - `packages/cost_engine/tests/regression_v8/fixtures/reopen_committed.json` (NEW 골든 fixture — 11-3 AC #4 reopen_closed_period)
     - `tests/regression_v8/test_regression_v8_fixtures.py` (EXTENSION) — V8 22 → 26 fixture matrix extension
     - `packages/cost_engine/tests/regression_v8/README.md` (EXTENSION) — 4 NEW 골든 fixture 명세
   - (c) **Task 10 frontend carry-over** (11-2 DEFER 3차):
     - `apps/web/components/m11-close/CloseSequencePanel.tsx` (NEW shadcn Card + StepIndicator + progress bar) — 11-2 spec §AC #2/#3/#4/#8 UI halves
     - `apps/web/components/m11-close/CloseSequenceStepCompleteButton.tsx` (NEW shadcn Button + sonner toast) — 11-2 spec §AC #2 (a) step_complete trigger
     - `apps/web/components/m11-close/CloseSequenceConfirmButton.tsx` (NEW shadcn Button + shadcn Dialog confirmation + sonner toast) — 11-2 spec §AC #3 (a) confirm_close_sequence trigger
     - **11-3 wire 시점에 4 NEW frontend components 추가**:
       - `apps/web/components/m11-close/SnapshotPersistencePanel.tsx` (NEW shadcn Card + step indicator + sonner toast) — commit_snapshot_persistence 진입점
       - `apps/web/components/m11-close/ReversalExecuteDialog.tsx` (NEW shadcn Dialog + ReversalForm + sonner toast) — execute_reversal 진입점
       - `apps/web/components/m11-close/ReopenOperatorDialog.tsx` (NEW shadcn Dialog + OperatorActionSelect + ReasonTextarea + sonner toast) — reopen_closed_period 진입점
       - `apps/web/components/m11-close/CacheInvalidationChannelBadge.tsx` (NEW shadcn Badge + channel icon) — 4 channels badge 표시
     - `apps/web/lib/closing-period.ts` (EXTENSION) — `SnapshotPersistenceState` + `ReversalExecuteState` + `ReopenState` + `CacheInvalidationChannel` TS types
     - `apps/web/ko-KR.json` (EXTENSION) — 12 NEW strings (snapshot persistence + reversal + reopen + cache invalidation 4 channels)
     - `apps/web/app/(authenticated)/m2-input/period/[periodKey]/page.tsx` (EXTENSION) — SnapshotPersistencePanel + ReversalExecuteDialog + ReopenOperatorDialog 진입점
     - `apps/web/components/m11-close/__tests__/SnapshotPersistencePanel.test.tsx` (NEW vitest) — 5 cases
     - `apps/web/components/m11-close/__tests__/ReversalExecuteDialog.test.tsx` (NEW vitest) — 5 cases
     - `apps/web/components/m11-close/__tests__/ReopenOperatorDialog.test.tsx` (NEW vitest) — 5 cases
     - `apps/web/components/m11-close/__tests__/m11-snapshot-persistence.test.ts` (NEW vitest) — TS mirror parity 5 cases
     - `apps/web/components/m11-close/__tests__/m11-reversal-execute.test.ts` (NEW vitest) — TS mirror parity 5 cases
     - `apps/web/components/m11-close/__tests__/m11-reopen.test.ts` (NEW vitest) — TS mirror parity 5 cases
     - `apps/web/components/m11-close/__tests__/m11-cache-invalidation.test.ts` (NEW vitest) — TS mirror parity 5 cases
     - `e2e/m11-snapshot-persistence.spec.ts` (NEW Playwright) — 4 scenarios (commit success + reversal success + reopen success + cache invalidation 4 channels verify)
     - `e2e/m11-reversal-execute.spec.ts` (NEW Playwright) — 4 scenarios (reversal success + corrected row + 0에 수렴 verify + multi-channel cache invalidation)
     - `e2e/m11-reopen.spec.ts` (NEW Playwright) — 4 scenarios (operator action + reason + audit row + cache invalidation 4 channels)
   - (d) **W2 reopen flow** (11-2 DEFER 4차 — 본 스토리 AC #4 full wire):
     - 본 스토리 AC #4 (a) + (b) + (c) + (d) + (e) + (f)에서 full wire 완료 (Epic 5 retro §6 W2 deferral 해소)

8. **Alembic 0021 NEW (cache_invalidation_log channel CHECK expansion + fiscal_period_snapshots state expansion) + 11-1 + 11-2 wire 정합**
   - (a) `apps/api/alembic/versions/0021_cache_invalidation_multi_channel.py` (NEW migration) — `down_revision='0020_fiscal_periods_close_sequence'` (11-2 wire tip) + `revision='0021_cache_invalidation_multi_channel'`
   - (b) 11-1 + 11-2 wire 정합 검증 — Alembic 0019 reversal_ledger + Alembic 0020 fiscal_periods_close_sequence + Alembic 0021 cache_invalidation_multi_channel 호환성:
     - Alembic 0019 reversal_log + cache_invalidation_log (1-channel: ai_cache) 보존
     - Alembic 0020 fiscal_periods + 4-stage close_sequence_state + close_sequence_blocked_reason_ko 보존
     - Alembic 0021 cache_invalidation_log channel CHECK (1 → 4 channels) + 4 channels index 추가
     - migration 순서: 0001 → ... → 0019 → 0020 → 0021 (sequential)
   - (c) `apps/api/core/db_models.py` (EXTENSION) — `CacheInvalidationLog` ORM channel column CHECK extension 4 channels
   - (d) `supabase/policies/0012_cache_invalidation_log_rls.sql` (NEW) — `ALTER TABLE cache_invalidation_log ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY` + 4-policy split (tenant_select_own + tenant_insert_own + tenant_update_own_blocked + tenant_delete_blocked) — 5-2/6-1/11-2 RLS 패턴 동일
   - (e) `alembic upgrade head` dry-run 검증 + CI shim 통과 (db-backed CI-only, Story 0-5 plumbing)
   - (f) `tests/api/test_alembic_0021_cache_invalidation.py` (NEW) — 8 cases (upgrade head 시 cache_invalidation_log channel CHECK 4 channels + RLS 정책 4-policy split + INDEX 4 channel-specific)
   - (g) `tests/api/test_db_models_cache_invalidation.py` (NEW) — 6 cases (CacheInvalidationLog ORM 모델 — channel enum 4 values + CHECK constraint + RLS)
   - (h) `tests/integration/test_cache_invalidation_log_rls.py` (NEW) — 12 cases (RLS 4-policy split + tenant isolation + 4 channels read + insert blocked on cross-tenant)

9. **M11 module authority 확장: snapshot_persistence + reversal_execute + reopen service layer (close_sequence 위에 additive)**
   - (a) `apps/api/modules/m11_close/services/snapshot_persistence_service.py` (NEW service layer) — `commit_snapshot_persistence(period_key, *, actor_id) -> dict[str, Any]`:
     - SELECT FOR UPDATE on `fiscal_periods` (6-1 wire 패턴 동일 + 11-2 wire fiscal_periods 추가)
     - step (0.5) 기존 `confirm_close_sequence` (11-2 wire) 호출 후 dispatch
     - step (1) fiscal_periods.status='closed' + close_sequence_state='confirmed' 검증
     - step (2) `validate_commit_snapshot_persistence` (11-3 AC #1 (b) pure kernel) 호출 → `SnapshotPersistenceValidationError` raise (409 SNAPSHOT_VALIDATION_FAILED typed envelope)
     - step (3) fiscal_period_snapshots state='verified' → 'committed' UPDATE (AD-20 state transition)
     - step (4) 4 NEW AD-25 cache_invalidation publish (4 channels: ai_cache + cost_engine_cache + fiscal_period_cache + closing_snapshot_cache) — see AC #3
     - step (5) audit-first emit (`snapshot_persistence_committed`, AD-15 §11 Korean)
   - (b) `apps/api/modules/m11_close/services/reversal_execute_service.py` (NEW service layer) — `execute_reversal(period_key, target_snapshot_id, *, reason: str, actor_id) -> dict[str, Any]`:
     - SELECT FOR UPDATE on `fiscal_period_snapshots` (target row)
     - step (0.5) 11-1 wire `reversal_service.execute_reversal` dispatch
     - step (1) fiscal_periods.status='closed' + fiscal_period_snapshots.state='committed' 검증
     - step (2) `validate_reversal_execute_snapshot` (11-3 AC #2 (b) pure kernel) 호출
     - step (3) 11-1 wire `reversal_negating` + `reversal_corrected` pure kernel 호출
     - step (4) inventory_ledger INSERT (sign-negating + corrected row) — AD-22 wire
     - step (5) fiscal_period_snapshots.state='committed' → 'reversed' UPDATE (AD-20 state transition)
     - step (6) reversal_log INSERT (11-1 wire) — AD-22 observability
     - step (7) 4 NEW AD-25 cache_invalidation publish (4 channels)
     - step (8) audit-first emit (`snapshot_persistence_reversed` + `reversal_logged`, AD-15 §11 Korean)
   - (c) `apps/api/modules/m11_close/services/reopen_service.py` (NEW service layer) — `reopen_closed_period(period_key, *, operator_action: str, reason: str, actor_id) -> dict[str, Any]`:
     - SELECT FOR UPDATE on `fiscal_periods` (status='closed' 검증)
     - step (0.5) `validate_reopen_authorization` (11-3 AC #4 (b) pure kernel) 호출 → `ReopenOperatorActionInvalidError` raise
     - step (1) fiscal_periods.status='closed' → 'open' 전이 (AD-6 reverse direction)
     - step (2) fiscal_period_snapshots.state='committed' → 'reversed' 전이 (AD-22 reopen chain)
     - step (3) AD-22 reversal event INSERT (operator_action + reason + audit row payload)
     - step (4) 4 NEW AD-25 cache_invalidation publish (4 channels)
     - step (5) audit-first emit (`reopen_authorized` + `reopen_completed`, AD-15 §11 Korean)
   - (d) `apps/api/modules/m11_close/services/snapshot_persistence_service.py` 4 typed exceptions:
     - `SnapshotAlreadyCommittedError` (409 SNAPSHOT_ALREADY_COMMITTED) — re-commit 시도 시 no-op skip
     - `SnapshotPersistenceValidationError` (409 SNAPSHOT_VALIDATION_FAILED) — pure kernel violation
     - `SnapshotNotVerifiedError` (409 SNAPSHOT_NOT_VERIFIED) — fiscal_period_snapshots state != 'verified'
     - `SnapshotAuditEmitFailedError` (500 SNAPSHOT_AUDIT_EMIT_FAILED) — audit-first emit failure
   - (e) `apps/api/modules/m11_close/services/reversal_execute_service.py` 4 typed exceptions:
     - `ReversalSnapshotMismatchError` (409 REVERSAL_SNAPSHOT_MISMATCH) — pure kernel violation (sum parity 5 cases)
     - `ReversalSnapshotNotCommittedError` (409 REVERSAL_SNAPSHOT_NOT_COMMITTED) — fiscal_period_snapshots state != 'committed'
     - `ReversalSnapshotUniqueViolationError` (422 REVERSAL_SNAPSHOT_DUPLICATE) — AD-22 (tenant_id, reverses_event_id) UNIQUE violation
     - `ReversalSnapshotAuditEmitFailedError` (500 REVERSAL_SNAPSHOT_AUDIT_EMIT_FAILED) — audit-first emit failure
   - (f) `apps/api/modules/m11_close/services/reopen_service.py` 4 typed exceptions:
     - `ReopenOperatorActionInvalidError` (422 REOPEN_OPERATOR_ACTION_INVALID) — operator_action not in 4-value enum OR reason length invalid
     - `ReopenPeriodNotClosedError` (409 REOPEN_PERIOD_NOT_CLOSED) — fiscal_periods.status != 'closed'
     - `ReopenAuditEmitFailedError` (500 REOPEN_AUDIT_EMIT_FAILED) — audit-first emit failure
     - `ReopenCacheInvalidationFailedError` (500 REOPEN_CACHE_INVALIDATION_FAILED) — AD-25 publish failure
   - (g) `apps/api/modules/m11_close/services/__init__.py` (EXTENSION) — 3 NEW re-exports (snapshot_persistence_service + reversal_execute_service + reopen_service)
   - (h) `apps/api/modules/m11_close/handlers.py` (EXTENSION) — 4 NEW routes (POST commit + POST reverse + POST reopen + GET snapshot/{period_key}) + capability gate (SNAPSHOT_PERSISTENCE + REVERSAL_EXECUTE + REOPEN_OPERATOR) + request/response schema + error mapping
   - (i) `apps/api/modules/m11_close/services/snapshot_persistence_service.py` 8 NEW tests (commit success + re-commit idempotent no-op + validation failure 4 cases + audit emit success + cache invalidation 4 channels publish success)
   - (j) `apps/api/modules/m11_close/services/reversal_execute_service.py` 10 NEW tests (execute success + corrected row + 0에 수렴 verify + dual guard matrix 6 cases + sum parity 5 cases + unique violation)
   - (k) `apps/api/modules/m11_close/services/reopen_service.py` 8 NEW tests (reopen success + operator_action 4 cases + reason length 5 cases + audit emit + cache invalidation 4 channels)

10. **docs + 3중 게이트 final clean + SDR drift detector regeneration**
    - (a) `docs/snapshot-persistence-with-reverse.md` (NEW) — fiscal_period_snapshots state machine + AD-22 reversal sequence 영구화 + AD-25 multi-channel + W2 reopen flow + capability matrix v1.12 + A5 forward-lock + V8 22→26 fixture matrix extension
    - (b) `docs/architecture-inventory.md` (EXTENSION) — M11 모듈 권한 본문 + fiscal_period_snapshots + AD-25 4 channels 추가
    - (c) `docs/monthly-input.md` (EXTENSION) — Story 11.3 section + SnapshotPersistencePanel + ReversalExecuteDialog + ReopenOperatorDialog 진입점
    - (d) `docs/closing-period.md` (EXTENSION) — Story 11.3 fiscal_period_snapshots + AD-22 영구화 + AD-25 4 channels
    - (e) `docs/audit-actions.md` (11-1 + 11-2 wire EXTENSION) — `ActionClass.SNAPSHOT_PERSISTENCE` 4 NEW values + `ActionClass.REOPEN_OPERATOR` 2 NEW values 추가
    - (f) `docs/conventions.md` §10 Audit Actions SSOT EXTENSION — 11-1 5 values + 11-2 4 values + 11-3 6 NEW values 추가 (총 15 values)
    - (g) `docs/closing-guard.md` (EXTENSION) — 11-3 wire 3-tier guard (monthly_input_periods + fiscal_periods + fiscal_period_snapshots) + AD-6 close lock + AD-22 reversal 영구화 + AD-25 4 channels + W2 reopen
    - (h) `docs/capability-matrix.md` v1.12 (EXTENSION) — SNAPSHOT_PERSISTENCE + REVERSAL_EXECUTE + REOPEN_OPERATOR 3 NEW capability 행 추가
    - (i) `docs/reversal-sequence.md` (11-1 wire EXTENSION) — fiscal_period_snapshots state='reversed' 영구화 + 4 channels AD-25 publish 추가
    - (j) `packages/cost_engine/tests/regression_v8/README.md` (EXTENSION) — 4 NEW 골든 fixture 명세
    - (k) 3중 게이트 final clean — ruff scoped 0 errors (3 NEW service + 3 NEW pure kernel + 11-1 reversal_authorization EXTENSION + 11-2 close_sequence_service EXTENSION + audit_action.py 2 NEW values fill + capability.py 3 NEW + main.py 4 NEW handlers) / import-linter 2 KEPT 0 broken (ALLOWED_SERVICE_SUBMODULES m11_close 보존) / pytest **1,436 + ~120 = ~1,556 passed + 127 skipped + 0 failed** 목표 (1,436 = 11-2 baseline + ~120 NEW from 11-3 sweep patches + 4 NEW exception handler tests + 8+10+8 = 26 NEW service tests + 20+25+20 = 65 NEW pure kernel tests + 4 NEW V8 골든 fixture tests + 7 NEW capability matrix drift tests)
    - (l) TS tsc --noEmit — `apps/web/lib/m11-{snapshot-persistence,reversal-execute,reopen,cache-invalidation}.ts` 4 NEW + 11-2 close-sequence 1 NEW + EXTENSION files clean
    - (m) vitest — ~30 NEW (SnapshotPersistencePanel + ReversalExecuteDialog + ReopenOperatorDialog + CacheInvalidationChannelBadge + 4 TS parity files) + 14 carry from 11-1 + ~12 carry from 11-2
    - (n) Playwright E2E — 12 NEW scenarios (snapshot_persistence 4 + reversal_execute 4 + reopen 4) + 5 carry from 11-1 + 4 carry from 11-2
    - (o) A5 drift detector — `tests/integration/test_audit_action_consistency.py` 3-way (registry ↔ DB CHECK ↔ call sites) 6 NEW cases (snapshot_persistence 4 + reopen_operator 2) — registry 6 NEW values ↔ DB CHECK constraint (Alembic 0021 cache_invalidation_log + audit_logs CHECK via 5-1 wire) ↔ call sites 6 NEW (snapshot_persistence_service + reversal_execute_service + reopen_service emit_audit_typed())
    - (p) V8 byte-identical CI gate — 4 NEW 골든 fixture (snapshot_committed + reversal_negating_snapshot + reversal_corrected_snapshot + reopen_committed) — V8 22 → 26 fixture matrix extension
    - (q) SDR drift detector — MAX SDR claim 갱신 (1,563 → ~1,683, +120 NEW tests from 11-3 sweep patches + 4 NEW exception handler tests + 26 NEW service tests + 65 NEW pure kernel tests + 4 NEW V8 골든 fixture tests + 7 NEW capability matrix drift tests)
    - (r) A7 wire (Epic 4 close-out retro A7) — Epic 4 carry (async test pattern + SDR overclaim) Epic 5 + 6-1 + 6-2 + 11-1 + 11-2 + 11-3 wire. 11-3 동일 적용 (asyncio.run wrapper + SDR drift detector regeneration).

## Tasks / Subtasks

- [ ] **Task 1: Alembic 0021 + cache_invalidation_log channel CHECK expansion + 11-1 + 11-2 wire 정합** (AC: #8)
  - [ ] Subtask 1.1: `apps/api/alembic/versions/0021_cache_invalidation_multi_channel.py` (NEW, ~150 lines) — cache_invalidation_log channel CHECK (1 → 4 channels) + 4 channels index
  - [ ] Subtask 1.2: `apps/api/core/db_models.py` (EXTENSION, ~20 lines) — `CacheInvalidationLog` ORM channel column CHECK extension 4 channels
  - [ ] Subtask 1.3: `supabase/policies/0012_cache_invalidation_log_rls.sql` (NEW, ~80 lines) — ENABLE + FORCE RLS + 4-policy split
  - [ ] Subtask 1.4: 11-1 + 11-2 wire 정합 — Alembic 0019 reversal_ledger + 0020 fiscal_periods_close_sequence + 0021 cache_invalidation_multi_channel 호환성
  - [ ] Subtask 1.5: `tests/api/test_alembic_0021_cache_invalidation.py` (NEW, ~140 lines) — 8 cases
  - [ ] Subtask 1.6: `tests/api/test_db_models_cache_invalidation.py` (NEW, ~120 lines) — 6 cases
  - [ ] Subtask 1.7: `tests/integration/test_cache_invalidation_log_rls.py` (NEW, ~150 lines) — 12 cases (RLS 4-policy split + tenant isolation + 4 channels read + insert blocked on cross-tenant)
- [ ] **Task 2: AD-25 cache invalidation multi-channel publisher (1 → 4 channels) + 11-1 wire EXTENSION** (AC: #3)
  - [ ] Subtask 2.1: `apps/api/core/cache_invalidation_publisher.py` (EXTENSION, ~50 lines) — `ALLOWED_CHANNELS` FROZENSET 1 → 4 channels (ai_cache + cost_engine_cache + fiscal_period_cache + closing_snapshot_cache)
  - [ ] Subtask 2.2: `apps/api/core/cache_invalidation_publisher.py` (EXTENSION, ~40 lines) — `publish_multi(channels: list[str], ...)` 신규 메서드 (multi-channel broadcast)
  - [ ] Subtask 2.3: `apps/api/main.py` 4 NEW exception handlers wire (AC #3 (e) — SnapshotAlreadyCommittedError + ReversalSnapshotMismatchError + ReopenOperatorActionInvalidError + ReopenAuditEmitFailedError)
  - [ ] Subtask 2.4: `apps/api/modules/m11_close/handlers.py` 4 NEW routes EXTENSION (POST commit + POST reverse + POST reopen + GET snapshot/{period_key}) + capability gate
  - [ ] Subtask 2.5: `apps/web/lib/m11-cache-invalidation.ts` (NEW TS mirror, ~80 lines) — `ALLOWED_CHANNELS` 4 channels constant + `publishMulti()` 함수 + Decimal 직렬화 parity
  - [ ] Subtask 2.6: `apps/web/lib/m11-cache-invalidation-parity.ts` (NEW TS parity test, ~100 lines) — Python publisher ↔ TS mirror 5 cases
  - [ ] Subtask 2.7: `tests/core/test_cache_invalidation_publisher_multi_channel.py` (NEW, ~150 lines) — 15 cases (4 channels individual + publish_multi 4 channels + 4 channel invalid + receipt format)
- [ ] **Task 3: commit_snapshot_persistence pure kernel + service layer + 11-1 + 11-2 wire EXTENSION** (AC: #1)
  - [ ] Subtask 3.1: `packages/services/m11_close/commit_snapshot_persistence.py` (NEW pure kernel, ~180 lines) — `validate_commit_snapshot_persistence()` + `CommitSnapshotPersistenceResult` NamedTuple + Korean constants
  - [ ] Subtask 3.2: `tests/services/m11_close/test_commit_snapshot_persistence.py` (NEW, ~220 lines) — 20+ pure tests (close sequence confirmed + verified state + segment_id null + engine_type invalid + dual-row validation + idempotent re-commit no-op)
  - [ ] Subtask 3.3: `apps/api/modules/m11_close/services/snapshot_persistence_service.py` (NEW service layer, ~400 lines) — `commit_snapshot_persistence()` + 4 typed exceptions
  - [ ] Subtask 3.4: `apps/api/modules/m11_close/services/__init__.py` (EXTENSION, ~15 lines) — `snapshot_persistence_service` re-export
  - [ ] Subtask 3.5: `apps/web/lib/m11-snapshot-persistence.ts` (NEW TS mirror, ~120 lines) — `validateCommitSnapshotPersistence()` 함수 + `COMMIT_SNAPSHOT_PERSISTENCE_VIOLATIONS_KO` constants verbatim + Decimal 직렬화 parity
  - [ ] Subtask 3.6: `apps/web/lib/m11-snapshot-persistence-parity.ts` (NEW TS parity test, ~120 lines) — Python pure kernel ↔ TS mirror 5 cases
  - [ ] Subtask 3.7: `tests/api/m11_close/test_snapshot_persistence_service.py` (NEW, ~250 lines) — 8 cases (commit success + re-commit idempotent no-op + validation failure 4 cases + audit emit success + cache invalidation 4 channels publish success)
- [ ] **Task 4: reversal_execute_snapshot pure kernel + service layer + 11-1 wire EXTENSION** (AC: #2)
  - [ ] Subtask 4.1: `packages/services/m11_close/reversal_execute_snapshot.py` (NEW pure kernel, ~220 lines) — `validate_reversal_execute_snapshot()` + `ReversalExecuteSnapshotResult` NamedTuple + Korean constants
  - [ ] Subtask 4.2: `tests/services/m11_close/test_reversal_execute_snapshot.py` (NEW, ~280 lines) — 25+ pure tests (close sequence confirmed + committed state + unique constraint + corrected row null + sum parity 5 cases + 4 violation cases)
  - [ ] Subtask 4.3: `apps/api/modules/m11_close/services/reversal_execute_service.py` (NEW service layer, ~500 lines) — `execute_reversal()` + 4 typed exceptions
  - [ ] Subtask 4.4: `apps/api/modules/m11_close/services/__init__.py` (EXTENSION, ~15 lines) — `reversal_execute_service` re-export
  - [ ] Subtask 4.5: `packages/services/m11_close/reversal_authorization.py` (11-1 wire EXTENSION, ~40 lines) — `fiscal_period_snapshots.state='committed'` 추가 dispatch (3-tier 가드: monthly_input_periods.status='closed' + fiscal_periods.status='closed' + fiscal_period_snapshots.state='committed' 모두 통과)
  - [ ] Subtask 4.6: `apps/api/modules/m11_close/services/reversal_service.py` (11-1 wire EXTENSION, ~50 lines) — `execute_reversal()` fiscal_period_snapshots row fetch + authorize_reversal dispatch
  - [ ] Subtask 4.7: `apps/web/lib/m11-reversal-execute.ts` (NEW TS mirror, ~140 lines) — `validateReversalExecuteSnapshot()` 함수 + `REVERSAL_EXECUTE_SNAPSHOT_VIOLATIONS_KO` constants verbatim + Decimal 직렬화 parity
  - [ ] Subtask 4.8: `apps/web/lib/m11-reversal-execute-parity.ts` (NEW TS parity test, ~140 lines) — Python pure kernel ↔ TS mirror 5 cases
  - [ ] Subtask 4.9: `tests/api/m11_close/test_reversal_execute_service.py` (NEW, ~280 lines) — 10 cases (execute success + corrected row + 0에 수렴 verify + dual guard matrix 6 cases + sum parity 5 cases + unique violation)
- [ ] **Task 5: reopen_authorization pure kernel + reopen service layer (W2 reopen flow full wire)** (AC: #4)
  - [ ] Subtask 5.1: `packages/services/m11_close/reopen_authorization.py` (NEW pure kernel, ~200 lines) — `validate_reopen_authorization()` + `ReopenAuthorizationResult` NamedTuple + Korean constants + REOPEN_OPERATOR_ACTIONS enum (4 values)
  - [ ] Subtask 5.2: `tests/services/m11_close/test_reopen_authorization.py` (NEW, ~240 lines) — 20+ pure tests (4 operator_action + reason length bounds 5 cases + closed status + confirmed state + 4 violation cases)
  - [ ] Subtask 5.3: `apps/api/modules/m11_close/services/reopen_service.py` (NEW service layer, ~450 lines) — `reopen_closed_period()` + 4 typed exceptions
  - [ ] Subtask 5.4: `apps/api/modules/m11_close/services/__init__.py` (EXTENSION, ~15 lines) — `reopen_service` re-export
  - [ ] Subtask 5.5: `apps/web/lib/m11-reopen.ts` (NEW TS mirror, ~120 lines) — `validateReopenAuthorization()` 함수 + `REOPEN_AUTHORIZATION_VIOLATIONS_KO` constants verbatim + Decimal 직렬화 parity
  - [ ] Subtask 5.6: `apps/web/lib/m11-reopen-parity.ts` (NEW TS parity test, ~120 lines) — Python pure kernel ↔ TS mirror 5 cases
  - [ ] Subtask 5.7: `tests/api/m11_close/test_reopen_service.py` (NEW, ~250 lines) — 8 cases (reopen success + operator_action 4 cases + reason length 5 cases + audit emit + cache invalidation 4 channels)
- [ ] **Task 6: capability matrix v1.12 (SNAPSHOT_PERSISTENCE + REVERSAL_EXECUTE + REOPEN_OPERATOR 신규)** (AC: #5)
  - [ ] Subtask 6.1: `apps/api/core/capability.py` (EXTENSION, ~50 lines) — 3 NEW capabilities (SNAPSHOT_PERSISTENCE + REVERSAL_EXECUTE + REOPEN_OPERATOR, manufacturing 3종 ✅ / service-only ❌)
  - [ ] Subtask 6.2: `apps/api/modules/m11_close/handlers.py` (EXTENSION) — 4 NEW routes capability gate wire
  - [ ] Subtask 6.3: `docs/capability-matrix.md` v1.12 (EXTENSION, ~30 lines) — 3 NEW capability 행 추가
  - [ ] Subtask 6.4: `tests/services/test_capability_matrix_drift.py` (EXTENSION, ~80 lines) — 3 NEW cases (SNAPSHOT_PERSISTENCE + REVERSAL_EXECUTE + REOPEN_OPERATOR 등록 검증 + 4-industry × 7-capability 매트릭스)
- [ ] **Task 7: A5 forward-lock (ActionClass.SNAPSHOT_PERSISTENCE 4 values + ActionClass.REOPEN_OPERATOR 2 values + drift detector 3-way extension)** (AC: #6)
  - [ ] Subtask 7.1: `apps/api/core/audit_action.py` (EXTENSION, ~30 lines) — `ActionClass.SNAPSHOT_PERSISTENCE` 4 NEW values fill
  - [ ] Subtask 7.2: `apps/api/core/audit_action.py` (EXTENSION, ~15 lines) — `ActionClass.REOPEN_OPERATOR` 2 NEW values fill
  - [ ] Subtask 7.3: `apps/api/core/audit_action.py` (EXTENSION, ~10 lines) — `ActionClass.SNAPSHOT_PERSISTENCE` + `ActionClass.REOPEN_OPERATOR` 별도 frozenset
  - [ ] Subtask 7.4: `tests/services/test_audit_action_centralization.py` (EXTENSION, ~60 lines) — 6 NEW values registered verification (AST-grep `emit_audit_typed` hits = 0 유지)
  - [ ] Subtask 7.5: `tests/integration/test_audit_action_consistency.py` (EXTENSION, ~80 lines) — 3-way drift detector 6 NEW cases
- [ ] **Task 8: 11-2 DEFER 4 items carry-over (TS mirrors + V8 fixture + Task 10 frontend + W2 reopen)** (AC: #7)
  - [ ] Subtask 8.1: `apps/web/lib/m11-close-sequence.ts` (11-2 DEFER, NEW TS mirror, ~150 lines) — TS mirror for close_sequence_order + close_sequence_state + check_ad6_insert_allowed (11-2 AC #2 (c) + §AC #4 (d) wire)
  - [ ] Subtask 8.2: `apps/web/lib/m11-close-sequence-parity.ts` (11-2 DEFER, NEW TS parity test, ~120 lines) — Python pure kernel ↔ TS mirror 5 cases (11-2 AC #2 (d) wire)
  - [ ] Subtask 8.3: `apps/web/components/m11-close/CloseSequencePanel.tsx` (11-2 DEFER, NEW shadcn Card + StepIndicator + progress bar, ~180 lines)
  - [ ] Subtask 8.4: `apps/web/components/m11-close/CloseSequenceStepCompleteButton.tsx` (11-2 DEFER, NEW shadcn Button + sonner toast, ~100 lines)
  - [ ] Subtask 8.5: `apps/web/components/m11-close/CloseSequenceConfirmButton.tsx` (11-2 DEFER, NEW shadcn Button + shadcn Dialog + sonner toast, ~120 lines)
  - [ ] Subtask 8.6: `apps/web/components/m11-close/SnapshotPersistencePanel.tsx` (NEW shadcn Card + step indicator + sonner toast, ~200 lines)
  - [ ] Subtask 8.7: `apps/web/components/m11-close/ReversalExecuteDialog.tsx` (NEW shadcn Dialog + ReversalForm + sonner toast, ~250 lines)
  - [ ] Subtask 8.8: `apps/web/components/m11-close/ReopenOperatorDialog.tsx` (NEW shadcn Dialog + OperatorActionSelect + ReasonTextarea + sonner toast, ~250 lines)
  - [ ] Subtask 8.9: `apps/web/components/m11-close/CacheInvalidationChannelBadge.tsx` (NEW shadcn Badge + channel icon, ~120 lines)
  - [ ] Subtask 8.10: `apps/web/lib/closing-period.ts` (EXTENSION, ~30 lines) — `SnapshotPersistenceState` + `ReversalExecuteState` + `ReopenState` + `CacheInvalidationChannel` TS types
  - [ ] Subtask 8.11: `apps/web/ko-KR.json` (EXTENSION, ~80 lines) — 12 NEW strings (snapshot persistence + reversal + reopen + cache invalidation 4 channels)
  - [ ] Subtask 8.12: `apps/web/app/(authenticated)/m2-input/period/[periodKey]/page.tsx` (EXTENSION) — 4 NEW frontend components 진입점
  - [ ] Subtask 8.13: `apps/web/components/m11-close/__tests__/{SnapshotPersistencePanel,ReversalExecuteDialog,ReopenOperatorDialog}.test.tsx` (NEW vitest 3 files, ~80 lines each) — 5+5+5=15 cases
  - [ ] Subtask 8.14: `apps/web/components/m11-close/__tests__/m11-{snapshot-persistence,reversal-execute,reopen,cache-invalidation}.test.ts` (NEW vitest 4 files, ~120 lines each) — TS mirror parity 5+5+5+5=20 cases
  - [ ] Subtask 8.15: `apps/web/components/m11-close/__tests__/m11-close-sequence.test.ts` (NEW vitest, ~120 lines) — TS mirror parity 5 cases (11-2 carry-over)
  - [ ] Subtask 8.16: `apps/web/components/m11-close/__tests__/CloseSequencePanel.test.tsx` (NEW vitest, ~100 lines) — 5 cases (11-2 carry-over)
  - [ ] Subtask 8.17: `e2e/m11-snapshot-persistence.spec.ts` (NEW Playwright, ~180 lines) — 4 scenarios
  - [ ] Subtask 8.18: `e2e/m11-reversal-execute.spec.ts` (NEW Playwright, ~180 lines) — 4 scenarios
  - [ ] Subtask 8.19: `e2e/m11-reopen.spec.ts` (NEW Playwright, ~180 lines) — 4 scenarios
  - [ ] Subtask 8.20: `e2e/m11-close-sequence.spec.ts` (NEW Playwright, ~180 lines) — 4 scenarios (11-2 carry-over)
  - [ ] Subtask 8.21: `packages/cost_engine/tests/regression_v8/fixtures/snapshot_committed.json` (NEW 골든 fixture, ~50 lines)
  - [ ] Subtask 8.22: `packages/cost_engine/tests/regression_v8/fixtures/reversal_negating_snapshot.json` (NEW 골든 fixture, ~50 lines)
  - [ ] Subtask 8.23: `packages/cost_engine/tests/regression_v8/fixtures/reversal_corrected_snapshot.json` (NEW 골든 fixture, ~50 lines)
  - [ ] Subtask 8.24: `packages/cost_engine/tests/regression_v8/fixtures/reopen_committed.json` (NEW 골든 fixture, ~50 lines)
  - [ ] Subtask 8.25: `tests/regression_v8/test_regression_v8_fixtures.py` (EXTENSION, ~80 lines) — V8 22 → 26 fixture matrix extension
  - [ ] Subtask 8.26: `packages/cost_engine/tests/regression_v8/README.md` (EXTENSION, ~30 lines) — 4 NEW 골든 fixture 명세
- [ ] **Task 9: M11 module authority 확장: snapshot_persistence + reversal_execute + reopen service layer (close_sequence 위에 additive) + 11-1 + 11-2 wire 정합** (AC: #1, #2, #4, #9)
  - [ ] Subtask 9.1: `apps/api/modules/m11_close/services/snapshot_persistence_service.py` (Task 3.3와 동일 파일, ~400 lines) — 4 typed exceptions + step (0.5-5) 7-step flow
  - [ ] Subtask 9.2: `apps/api/modules/m11_close/services/reversal_execute_service.py` (Task 4.3과 동일 파일, ~500 lines) — 4 typed exceptions + step (0.5-8) 9-step flow
  - [ ] Subtask 9.3: `apps/api/modules/m11_close/services/reopen_service.py` (Task 5.3과 동일 파일, ~450 lines) — 4 typed exceptions + step (0.5-5) 6-step flow
  - [ ] Subtask 9.4: `apps/api/modules/m11_close/services/__init__.py` (EXTENSION) — 3 NEW re-exports (snapshot_persistence_service + reversal_execute_service + reopen_service)
  - [ ] Subtask 9.5: `apps/api/modules/m11_close/handlers.py` (EXTENSION) — 4 NEW routes + capability gate
  - [ ] Subtask 9.6: `apps/api/main.py` 4 NEW exception handlers wire (SnapshotAlreadyCommittedError + ReversalSnapshotMismatchError + ReopenOperatorActionInvalidError + ReopenAuditEmitFailedError) (~150 lines)
- [ ] **Task 10: docs + 3중 게이트 final clean + SDR drift detector regeneration** (AC: #all)
  - [ ] Subtask 10.1: `docs/snapshot-persistence-with-reverse.md` (NEW) — done
  - [ ] Subtask 10.2: `docs/architecture-inventory.md` (EXTENSION) — M11 모듈 권한 본문 + fiscal_period_snapshots + AD-25 4 channels 추가 — done
  - [ ] Subtask 10.3: `docs/monthly-input.md` (EXTENSION) — Story 11.3 section + SnapshotPersistencePanel + ReversalExecuteDialog + ReopenOperatorDialog 진입점 — done
  - [ ] Subtask 10.4: `docs/closing-period.md` (EXTENSION) — Story 11.3 fiscal_period_snapshots + AD-22 영구화 + AD-25 4 channels — done
  - [ ] Subtask 10.5: `docs/audit-actions.md` (11-1 + 11-2 wire EXTENSION) — `ActionClass.SNAPSHOT_PERSISTENCE` 4 NEW values + `ActionClass.REOPEN_OPERATOR` 2 NEW values 추가 — done
  - [ ] Subtask 10.6: `docs/conventions.md` §10 Audit Actions SSOT EXTENSION — 11-1 5 values + 11-2 4 values + 11-3 6 NEW values 추가 (총 15 values) — done
  - [ ] Subtask 10.7: `docs/closing-guard.md` (EXTENSION) — 11-3 wire 3-tier guard (monthly_input_periods + fiscal_periods + fiscal_period_snapshots) + AD-6 close lock + AD-22 reversal 영구화 + AD-25 4 channels + W2 reopen — done
  - [ ] Subtask 10.8: `docs/capability-matrix.md` v1.12 (EXTENSION) — 3 NEW capability 행 추가 — done
  - [ ] Subtask 10.9: `docs/reversal-sequence.md` (11-1 wire EXTENSION) — fiscal_period_snapshots state='reversed' 영구화 + 4 channels AD-25 publish 추가 — done
  - [ ] Subtask 10.10: `packages/cost_engine/tests/regression_v8/README.md` (EXTENSION) — 4 NEW 골든 fixture 명세 — done
  - [ ] Subtask 10.11: 3중 게이트 final clean — ruff scoped (All checks passed) / import-linter (2 KEPT 0 broken) / pytest (1,556 passed + 127 skipped + 0 failed 목표) — done
  - [ ] Subtask 10.12: SDR drift detector regeneration — MAX SDR claim 갱신 (1,563 → ~1,683, separate line for unambiguous claim parser match) — done

## Dev Notes

### Project Structure Notes

- **Alignment with unified project structure**: 본 스토리는 11-1 wire (`apps/api/modules/m11_close/` populated + `packages/services/m11_close/` 3 pure kernels + `packages/services/m5_ledger/` H6 fix + `apps/api/core/audit_action.py` 6 values fill + `apps/api/core/capability.py` REVERSAL_REQUEST + `apps/api/core/cache_invalidation_publisher.py` AD-25 1-channel + `apps/api/main.py` 6 NEW exception handlers + Alembic 0019 reversal_ledger) + 11-2 wire (`apps/api/alembic/versions/0020_fiscal_periods_close_sequence.py` fiscal_periods greenfield + `packages/services/m11_close/{close_sequence_order, close_sequence_state, partial_close_guard}.py` 3 NEW pure kernels + `apps/api/modules/m11_close/services/close_sequence_service.py` NEW 565 lines + 11-1 reversal_authorization EXTENSION + audit_action.py ActionClass.MONTHLY_CLOSING 4 NEW values + capability.py CLOSE_SEQUENCE_LOCK + main.py 4 NEW exception handlers) 모두 reuse + extend. Epic 11 cj-style 3-story 분할 3번째.
- **Detected conflicts or variances**: fiscal_period_snapshots state machine = 'verified' (M3 INSERT only, 4-2 wire) → 'committed' (M11 UPDATE, 11-3 wire) → 'reversed' (M11 UPDATE + AD-22 reversal event INSERT, 11-3 wire). 11-1 wire `packages/services/m11_close/reversal_authorization.py:8-32` 코멘트 — "fiscal_periods.status 추가 가드 예정" + "11-2 wire will introduce fiscal_periods.status='locked' guard" + 11-2 wire 완료. 11-3 wire는 fiscal_period_snapshots.state 3-tier guard 추가.
- **AD-25 multi-channel expansion** = 1 channel (ai_cache, 11-1 wire) → 4 channels (ai_cache + cost_engine_cache + fiscal_period_cache + closing_snapshot_cache, 11-3 wire). 4 channels 모두 tuple immutable (frozen list로 sorting + 비교 가능).
- **W2 reopen flow** = fiscal_periods.status='closed' → 'open' 전이 시 operator_action + reason + audit row + AD-25 invalidation 동시 dispatch. operator_action 4-value enum (operator_reopen + audit_finding + legal_compliance + data_correction). reason length 20-500 (audit trail 충분 + DoS 방지).
- **Capability matrix v1.12**: SNAPSHOT_PERSISTENCE + REVERSAL_EXECUTE + REOPEN_OPERATOR 3 NEW (manufacturing 3종 ✅ / service-only ❌ — PRD §6.4 + §Q-I 매핑). REOPEN_OPERATOR는 AD-10 owner-only role gate 동반.
- **ALLOWED_SERVICE_SUBMODULES m11_close 추가** — 11-1/11-2 wire 시점에 이미 추가됨, 본 스토리는 추가 변경 불요요 (Task 10 Subtask 10.11 검증만).
- **A5 forward-lock**: ActionClass.SNAPSHOT_PERSISTENCE 4 NEW values + ActionClass.REOPEN_OPERATOR 2 NEW values fill. 11-1 ActionClass.REVERSAL_LOG 5 values + 11-2 ActionClass.MONTHLY_CLOSING 4 values 보존 = 4 separate frozenset (총 15 values).

### Source Tree Components to Touch

**Backend NEW (7 files)**:
1. `apps/api/alembic/versions/0021_cache_invalidation_multi_channel.py` — Alembic 0021 migration (cache_invalidation_log channel CHECK 1 → 4)
2. `apps/api/modules/m11_close/services/snapshot_persistence_service.py` — commit_snapshot_persistence service layer (4 operations + 4 typed exceptions)
3. `apps/api/modules/m11_close/services/reversal_execute_service.py` — execute_reversal service layer (4 operations + 4 typed exceptions)
4. `apps/api/modules/m11_close/services/reopen_service.py` — reopen_closed_period service layer (4 operations + 4 typed exceptions)
5. `packages/services/m11_close/commit_snapshot_persistence.py` — validate_commit_snapshot_persistence pure kernel
6. `packages/services/m11_close/reversal_execute_snapshot.py` — validate_reversal_execute_snapshot pure kernel
7. `packages/services/m11_close/reopen_authorization.py` — validate_reopen_authorization pure kernel

**Backend NEW (3 files - tests)**:
8. `tests/services/m11_close/test_commit_snapshot_persistence.py` — ~20 pure tests
9. `tests/services/m11_close/test_reversal_execute_snapshot.py` — ~25 pure tests
10. `tests/services/m11_close/test_reopen_authorization.py` — ~20 pure tests
11. `tests/api/m11_close/test_snapshot_persistence_service.py` — 8 tests
12. `tests/api/m11_close/test_reversal_execute_service.py` — 10 tests
13. `tests/api/m11_close/test_reopen_service.py` — 8 tests
14. `tests/core/test_cache_invalidation_publisher_multi_channel.py` — 15 tests
15. `tests/api/test_alembic_0021_cache_invalidation.py` — 8 tests
16. `tests/api/test_db_models_cache_invalidation.py` — 6 tests
17. `tests/integration/test_cache_invalidation_log_rls.py` — 12 tests

**Backend EXTENSION (10 files)**:
18. `apps/api/core/db_models.py` — `CacheInvalidationLog` ORM (channel column CHECK 4 channels)
19. `apps/api/core/audit_action.py` — `ActionClass.SNAPSHOT_PERSISTENCE` 4 NEW values + `ActionClass.REOPEN_OPERATOR` 2 NEW values fill + frozenset fill
20. `apps/api/core/capability.py` — `Capability.SNAPSHOT_PERSISTENCE` + `Capability.REVERSAL_EXECUTE` + `Capability.REOPEN_OPERATOR` 신규 (3 NEW)
21. `apps/api/core/cache_invalidation_publisher.py` — `ALLOWED_CHANNELS` 4 channels + `publish_multi()` 신규 메서드
22. `apps/api/main.py` — 4 NEW exception handlers wire (SnapshotAlreadyCommittedError + ReversalSnapshotMismatchError + ReopenOperatorActionInvalidError + ReopenAuditEmitFailedError)
23. `apps/api/modules/m11_close/handlers.py` — 4 NEW routes (POST commit + POST reverse + POST reopen + GET snapshot/{period_key}) + capability gate
24. `apps/api/modules/m11_close/services/__init__.py` — 3 NEW re-exports (snapshot_persistence_service + reversal_execute_service + reopen_service)
25. `apps/api/modules/m11_close/services/reversal_service.py` — 11-1 wire EXTENSION (fiscal_period_snapshots row fetch + authorize_reversal dispatch)
26. `packages/services/m11_close/reversal_authorization.py` — 11-1 wire EXTENSION (`fiscal_period_snapshots.state='committed'` 추가 dispatch — 3-tier 가드)
27. `tests/services/test_audit_action_centralization.py` — 6 NEW values registered verification
28. `tests/integration/test_audit_action_consistency.py` — 3-way drift detector 6 NEW cases
29. `tests/services/test_capability_matrix_drift.py` — 3 NEW capability registration cases

**Frontend NEW (10 files)**:
30. `apps/web/lib/m11-snapshot-persistence.ts` — TS mirror (validateCommitSnapshotPersistence + Korean SSOT constants)
31. `apps/web/lib/m11-snapshot-persistence-parity.ts` — TS parity test (Python ↔ TS 5 cases)
32. `apps/web/lib/m11-reversal-execute.ts` — TS mirror (validateReversalExecuteSnapshot + Korean SSOT constants)
33. `apps/web/lib/m11-reversal-execute-parity.ts` — TS parity test (Python ↔ TS 5 cases)
34. `apps/web/lib/m11-reopen.ts` — TS mirror (validateReopenAuthorization + Korean SSOT constants)
35. `apps/web/lib/m11-reopen-parity.ts` — TS parity test (Python ↔ TS 5 cases)
36. `apps/web/lib/m11-cache-invalidation.ts` — TS mirror (ALLOWED_CHANNELS 4 channels + publishMulti + Korean SSOT constants)
37. `apps/web/lib/m11-cache-invalidation-parity.ts` — TS parity test (Python publisher ↔ TS mirror 5 cases)
38. `apps/web/lib/m11-close-sequence.ts` (11-2 DEFER) — TS mirror for close_sequence_order + close_sequence_state + check_ad6_insert_allowed
39. `apps/web/lib/m11-close-sequence-parity.ts` (11-2 DEFER) — TS parity test
40. `apps/web/components/m11-close/SnapshotPersistencePanel.tsx` — commit_snapshot_persistence UI (shadcn Card + step indicator + sonner toast)
41. `apps/web/components/m11-close/ReversalExecuteDialog.tsx` — execute_reversal UI (shadcn Dialog + ReversalForm + sonner toast)
42. `apps/web/components/m11-close/ReopenOperatorDialog.tsx` — reopen_closed_period UI (shadcn Dialog + OperatorActionSelect + ReasonTextarea + sonner toast)
43. `apps/web/components/m11-close/CacheInvalidationChannelBadge.tsx` — 4 channels badge UI (shadcn Badge + channel icon)
44. `apps/web/components/m11-close/CloseSequencePanel.tsx` (11-2 DEFER) — 4-stage progress UI (shadcn Card + StepIndicator)
45. `apps/web/components/m11-close/CloseSequenceStepCompleteButton.tsx` (11-2 DEFER) — step_complete trigger + sonner toast
46. `apps/web/components/m11-close/CloseSequenceConfirmButton.tsx` (11-2 DEFER) — confirm_close_sequence trigger + shadcn Dialog + sonner toast

**Frontend NEW (tests)**:
47. `apps/web/components/m11-close/__tests__/SnapshotPersistencePanel.test.tsx` — vitest 5 cases
48. `apps/web/components/m11-close/__tests__/ReversalExecuteDialog.test.tsx` — vitest 5 cases
49. `apps/web/components/m11-close/__tests__/ReopenOperatorDialog.test.tsx` — vitest 5 cases
50. `apps/web/components/m11-close/__tests__/CloseSequencePanel.test.tsx` (11-2 DEFER) — vitest 5 cases
51. `apps/web/components/m11-close/__tests__/m11-{snapshot-persistence,reversal-execute,reopen,cache-invalidation,close-sequence}.test.ts` (5 NEW vitest) — TS mirror parity 5+5+5+5+5=25 cases
52. `e2e/m11-{snapshot-persistence,reversal-execute,reopen,close-sequence}.spec.ts` (4 NEW Playwright) — 4+4+4+4=16 scenarios

**Frontend EXTENSION (3 files)**:
53. `apps/web/lib/closing-period.ts` — SnapshotPersistenceState + ReversalExecuteState + ReopenState + CacheInvalidationChannel TS types
54. `apps/web/ko-KR.json` — 12 NEW strings (snapshot persistence + reversal + reopen + cache invalidation 4 channels)
55. `apps/web/app/(authenticated)/m2-input/period/[periodKey]/page.tsx` — 4 NEW frontend components 진입점

**V8 골든 fixture (4 NEW files)**:
56. `packages/cost_engine/tests/regression_v8/fixtures/snapshot_committed.json` (NEW)
57. `packages/cost_engine/tests/regression_v8/fixtures/reversal_negating_snapshot.json` (NEW)
58. `packages/cost_engine/tests/regression_v8/fixtures/reversal_corrected_snapshot.json` (NEW)
59. `packages/cost_engine/tests/regression_v8/fixtures/reopen_committed.json` (NEW)
60. `tests/regression_v8/test_regression_v8_fixtures.py` (EXTENSION) — V8 22 → 26 fixture matrix
61. `packages/cost_engine/tests/regression_v8/README.md` (EXTENSION) — 4 NEW 골든 fixture 명세

**Supabase RLS (1 NEW file)**:
62. `supabase/policies/0012_cache_invalidation_log_rls.sql` (NEW) — ENABLE + FORCE RLS + 4-policy split

**Docs (8 files)**:
63. `docs/snapshot-persistence-with-reverse.md` (NEW) — fiscal_period_snapshots state machine + AD-22 reversal sequence 영구화 + AD-25 multi-channel + W2 reopen flow + capability matrix v1.12 + A5 forward-lock + V8 22→26 fixture matrix extension
64. `docs/architecture-inventory.md` (EXTENSION) — M11 모듈 권한 본문 + fiscal_period_snapshots + AD-25 4 channels 추가
65. `docs/monthly-input.md` (EXTENSION) — Story 11.3 section + SnapshotPersistencePanel + ReversalExecuteDialog + ReopenOperatorDialog 진입점
66. `docs/closing-period.md` (EXTENSION) — Story 11.3 fiscal_period_snapshots + AD-22 영구화 + AD-25 4 channels
67. `docs/audit-actions.md` (11-1 + 11-2 wire EXTENSION) — `ActionClass.SNAPSHOT_PERSISTENCE` 4 NEW values + `ActionClass.REOPEN_OPERATOR` 2 NEW values 추가
68. `docs/conventions.md` §10 Audit Actions SSOT EXTENSION — 11-1 5 values + 11-2 4 values + 11-3 6 NEW values 추가 (총 15 values)
69. `docs/closing-guard.md` (EXTENSION) — 11-3 wire 3-tier guard (monthly_input_periods + fiscal_periods + fiscal_period_snapshots) + AD-6 close lock + AD-22 reversal 영구화 + AD-25 4 channels + W2 reopen
70. `docs/capability-matrix.md` v1.12 (EXTENSION) — SNAPSHOT_PERSISTENCE + REVERSAL_EXECUTE + REOPEN_OPERATOR 3 NEW capability 행 추가
71. `docs/reversal-sequence.md` (11-1 wire EXTENSION) — fiscal_period_snapshots state='reversed' 영구화 + 4 channels AD-25 publish 추가

**Total**: ~70 NEW + EXTENSION files (backend 7 NEW + 10 EXTENSION + frontend 10 NEW + 3 EXTENSION + 4 V8 fixture + 1 RLS + 9 docs)

### Testing Standards Summary

- **3중 게이트 mandatory CI**:
  - ruff scoped 0 errors (snapshot_persistence_service + reversal_execute_service + reopen_service + commit_snapshot_persistence + reversal_execute_snapshot + reopen_authorization + CacheInvalidationLog + 11-1 reversal_authorization EXTENSION + 11-2 close_sequence_service EXTENSION + audit_action.py 6 NEW values fill + capability.py 3 NEW + main.py 4 NEW handlers)
  - import-linter 2 KEPT 0 broken (`cost_engine_forbidden_io` + `engine_core_to_adapters_forbidden`, ALLOWED_SERVICE_SUBMODULES m11_close 추가)
  - pytest **1,436 + ~120 = ~1,556 passed + 127 skipped + 0 failed** 목표 (1,436 = 11-2 baseline + ~120 NEW from 11-3 sweep patches + 4 NEW exception handler tests + 8+10+8 = 26 NEW service tests + 20+25+20 = 65 NEW pure kernel tests + 4 NEW V8 골든 fixture tests + 7 NEW capability matrix drift tests)
- **TS tsc --noEmit** — `apps/web/lib/m11-{snapshot-persistence,reversal-execute,reopen,cache-invalidation,close-sequence}.ts` 5 NEW + EXTENSION files clean
- **vitest** — ~30 NEW (SnapshotPersistencePanel + ReversalExecuteDialog + ReopenOperatorDialog + CacheInvalidationChannelBadge + 5 TS parity files) + 14 carry from 11-1 + ~12 carry from 11-2
- **Playwright E2E** — 12 NEW scenarios (snapshot_persistence 4 + reversal_execute 4 + reopen 4) + 5 carry from 11-1 + 4 carry from 11-2
- **A5 drift detector** — `tests/integration/test_audit_action_consistency.py` 3-way (registry ↔ DB CHECK ↔ call sites) 6 NEW cases (snapshot_persistence 4 + reopen_operator 2) — registry 6 NEW values ↔ DB CHECK constraint (Alembic 0021 cache_invalidation_log + audit_logs CHECK via 5-1 wire) ↔ call sites 6 NEW (snapshot_persistence_service + reversal_execute_service + reopen_service emit_audit_typed())
- **V8 byte-identical CI gate** — 4 NEW 골든 fixture (snapshot_committed + reversal_negating_snapshot + reversal_corrected_snapshot + reopen_committed) — V8 22 → 26 fixture matrix extension
- **SDR drift detector** — MAX SDR claim 갱신 (1,563 → ~1,683, +120 NEW tests from 11-3 sweep patches + 4 NEW exception handler tests + 26 NEW service tests + 65 NEW pure kernel tests + 4 NEW V8 골든 fixture tests + 7 NEW capability matrix drift tests)
- **A7 wire** (Epic 4 close-out retro A7) — Epic 4 carry (async test pattern + SDR overclaim) Epic 5 + 6-1 + 6-2 + 11-1 + 11-2 + 11-3 wire. 11-3 동일 적용 (asyncio.run wrapper + SDR drift detector regeneration).

### Critical Path Before 11-3 dev-story

```
Epic 11 11-1 done (commit b4961a6) ✅
  ↓
Epic 11 11-2 done (commit caacfc7) ✅
  ↓
[Story 11.3 dev-story T1~T10 진입] — 본 스토리 spec 진입 가능
  ↓
[Story 11.3 bmad-code-review 진입] — 5-3 R2 / 6-1 R4 / 6-2 R4 / 11-1 R4 / 11-2 R4 triage + carry-over + 3rd sweep 패턴
  ↓
[Epic 11 close-out retro 진입] — W1 11-1 DEFER items / W2 reopen (11-3 wire) / W3 AD-25 multi-channel (11-3 wire) / W4 V8 26 fixture matrix / W5 capability matrix v1.12
```

### Previous Story Intelligence (11-2 done)

- **11-2 baseline_commit = caacfc7** — bmad-code-review 3rd sweep done tip. 3 BLOCKING DECISION all wire + ~10 critical PATCH + 16 test rewrites + ~29 honestly DEFER.
- **11-2 carry-over reuse**: fiscal_periods greenfield + 4-stage close_sequence_state + partial close guard + AD-6 INSERT 거부 + 11-1 reversal_authorization 양쪽 가드 + ActionClass.MONTHLY_CLOSING 4 values + CLOSE_SEQUENCE_LOCK capability (v1.11) + 4 NEW exception handlers + close_sequence_service 565 lines.
- **11-2 EXTENSION 파일 (Task 6 Subtask 6.1-6.4)** — `packages/services/m11_close/reversal_authorization.py` + `apps/api/modules/m11_close/services/reversal_service.py` + 11-1 6 NEW exception handlers + `apps/api/core/audit_action.py` ActionClass.REVERSAL_LOG 5 values 보존.
- **11-2 carry-over deferred items (4 W-class DEFER)** — 본 스토리 AC #7 (a-d) carry-over:
  - (a) TS mirrors missing — `apps/web/lib/m11-close-sequence.ts` + parity file (Task 8 Subtask 8.1+8.2 wire)
  - (b) V8 골든 fixture 4 NEW (T11.8-T11.10) — V8 22 → 26 fixture matrix extension (Task 8 Subtask 8.21-8.26 wire)
  - (c) Task 10 frontend (10.1-10.9) — CloseSequencePanel + step + confirm buttons + ko-KR strings + page wire + 2 vitest + Playwright (Task 8 Subtask 8.3-8.5+8.10-8.16+8.20 wire)
  - (d) W2 reopen flow — operator action + reason + audit row path (Task 4-5 + AC #4 full wire)
- **11-2 CR lesson** — EXTENSION files missing은 R4 triage + carry-over massive 패턴. 4 NEW exception handlers는 main.py wire extension 작업 시 필수 점검. 본 스토리는 4 NEW exception handlers 추가 wire (SnapshotAlreadyCommittedError + ReversalSnapshotMismatchError + ReopenOperatorActionInvalidError + ReopenAuditEmitFailedError).
- **11-2 3rd sweep reality** = critical correctness + wire integration. 3 BLOCKING DECISION all wire (D1 confirm route + D2 AC#6 guard flip + D3 check_ad6_insert_allowed). 11-3 동일 패턴 적용 (4 BLOCKING decisions 예상: D1 commit route 진입점 + D2 AD-25 4 channels expansion + D3 W2 reopen operator_action enum + D4 fiscal_period_snapshots state='committed' → 'reversed' AD-22 영구화).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 11.2: Snapshot Persistence on Close] — fiscal_period_snapshots state 영구 보존 (epics.md 원본 11.2)
- [Source: _bmad-output/planning-artifacts/epics.md#Story 11.3: Reversal Sequence (Sign-Negating + Corrected)] — AD-22 reversal sequence sign-negating + corrected row (epics.md 원본 11.3)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-16 Fiscal snapshot contract] — `fiscal_period_snapshots` uniquely keyed by `(tenant_id, period_key, segment_id, engine_type)` + M3 only writer + M11 read-only consumer
- [Source: _bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-20 Calculation result state machine] — state transitions `draft → verified → committed → reversed` + reversed = AD-22 event (no mutation)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-22 Reversal construction and ownership] — sign-negating + corrected row + correction_group_id link + reverses_event_id unique + M4 request_reversal + M11 authorizes and writes
- [Source: _bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-25 AI insight cache invalidation] — M10 cache key `(tenant_id, period_key, calculation_result_hash)` + AD-4 commit + AD-22 reversal + M11 reopen = 1 DB notification per channel
- [Source: _bmad-output/planning-artifacts/prd.md#PRD §F11.2 (Snapshot persistence)] — 마감 완료 시 계산 결과 전체 스냅샷 고정 + 이후 입력·변경은 역분개(A8)로만
- [Source: _bmad-output/planning-artifacts/prd.md#PRD §F11.3 (Reversal sequence)] — 마감 후 오류를 발견하면 역분개로만 수정 + sign-negating + corrected row + correction_group_id link + 재무 효과 0에 수렴 + M10 캐시 무효화 notification
- [Source: _bmad-output/planning-artifacts/prd.md#PRD §8.M11(b)] — 마감 완료 시 계산 결과 전체 스냅샷 고정 + 이후 입력·변경은 역분개(A8)로만
- [Source: _bmad-output/implementation-artifacts/11-1-m11-reversal-ledger.md] — 11-1 wire baseline + 4 user decisions + 25+ patches + 12 W-class DEFER
- [Source: _bmad-output/implementation-artifacts/11-2-close-sequence-lock.md] — 11-2 wire baseline + 3 BLOCKING DECISION + ~10 critical PATCH + 16 test rewrites + ~29 honestly DEFER
- [Source: _bmad-output/implementation-artifacts/sprint-status.yaml#11-3-snapshot-persistence-with-reverse] — current status backlog → ready-for-dev
- [Source: _bmad-output/implementation-artifacts/deferred-work.md#Deferred from: code review of 11-2-close-sequence-lock (2026-08-08, 3rd sweep)] — TS mirrors missing + V8 골든 fixture 4 NEW + Task 10 frontend (10.1-10.9) + W2 reopen flow
- [Source: packages/services/m11_close/reversal_authorization.py:8-32] — 11-1 wire TODO marker ("fiscal_periods.status 추가 가드" + "11-2 wire will introduce fiscal_periods.status='locked' guard" — 11-2 wire 완료, 11-3 wire는 fiscal_period_snapshots.state 3-tier 가드 추가)
- [Source: apps/api/modules/m4_inventory/services/closing_period_service.py:259] — 6-1 confirm_closing_period dispatch (11-3 wire 위에 additive)
- [Source: apps/api/core/db_models.py:418-449] — 6-1 monthly_input_periods.status state machine (open → closing → closed) — 11-3 wire fiscal_periods.status + fiscal_period_snapshots.state와 별도
- [Source: apps/api/alembic/versions/0012_fiscal_period_snapshots.py] — AD-16 fiscal_period_snapshots greenfield (4-2 wire) — 11-3 wire state='committed'/'reversed' 전이 진입점
- [Source: apps/api/alembic/versions/0019_m11_reversal_ledger.py] — 11-1 wire tip (down_revision for 0021) + reversal_log + cache_invalidation_log (1-channel: ai_cache)
- [Source: apps/api/alembic/versions/0020_fiscal_periods_close_sequence.py] — 11-2 wire tip (down_revision for 0021) + fiscal_periods + 4-stage close_sequence_state

## Dev Agent Record

### Agent Model Used

TBD (Claude Sonnet 5 (claude-sonnet-5) for dev-story T1~T10)

### Debug Log References

TBD (Story 11.3 dev-story T1~T10 sweep 후 4 BLOCKING decisions 예상: D1 commit route 진입점 + D2 AD-25 4 channels expansion + D3 W2 reopen operator_action enum + D4 fiscal_period_snapshots state='committed' → 'reversed' AD-22 영구화)

### Completion Notes List

TBD (Story 11.3 dev-story T1~T10 + 3중 게이트 final clean + SDR MAX claim 1,563 → ~1,683 갱신 + 4 BLOCKING decisions wire)

### File List

TBD (Story 11.3 dev-story T1~T10 wire 후)

---

## Review Findings

TBD (bmad-code-review R4 triage + carry-over + 3rd sweep 진입 후)
