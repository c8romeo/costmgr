---
baseline_commit: b4961a6
target_key: 11-2-close-sequence-lock
epic: 11
story_id: 11.2
title: Close Sequence Lock — fiscal_periods 테이블 신설 + 4단계 순서 강제 + 부분 마감 불허 + AD-6 INSERT 거부
status: in-progress
---

# Story 11.2: Close Sequence Lock — fiscal_periods 테이블 신설 + 4단계 순서 강제 + 부분 마감 불허 + AD-6 INSERT 거부

Status: ready-for-dev

> **Epic 11 cj-style 3-story 분할 (Epic 5 close-out retro §6 W1 — Epic 4 A3 결정 + Epic 5 5-1/5-2/5-3 + Epic 6 6-1/6-2/6-3 동일 3-story 분할 패턴) 2번째 스토리**. **epics.md 원본 11.1 (Close Sequence Lock) greenfield** 그대로 wire. 사용자 결정 (2026-08-08 cj-style 3분할): 11-1 = M11 module authority + AD-22 reversal ledger wire + A9 fill + H6 fix + AD-25 1-channel ✅ done (commit b4961a6) → **11-2 = close-sequence-lock** (본 스토리) → 11-3 = snapshot-persistence-with-reverse (epics.md 11.2 + 11.3 통합). 본 스토리 = **fiscal_periods 테이블 greenfield** + **4단계 divisions → manufacturing → ABC → common 순서 강제** (PRD §F11.1 PRIMARY) + **부분 마감 불허** (한 단계만 완료 후 마감 진입 시도 → 409 PARTIAL_CLOSE_BLOCKED typed envelope) + **AD-6 INSERT 거부** (`fiscal_periods.status='closed'` 후 모든 business-data INSERT 거부, AD-22 reversal/correction events만 허용 — Architecture Spine §AD-6 Rule 그대로) + **11-1 reversal_authorization.py 확장** (`monthly_input_periods.status` 단일 가드 → `monthly_input_periods.status` + `fiscal_periods.status` 양쪽 가드).
>
> **baseline_commit = b4961a6** (Story 11.1 bmad-code-review 3rd sweep done tip, 25+ patches sweeping applied + 4 user decisions). 본 스토리는 11-1 wire 모두 reuse + extend: M11 module authority (`apps/api/modules/m11_close/` populated) + AD-22 reversal ledger wire (`reversal_negating` + `reversal_corrected` event type) + A9 fill 5 values (`reversal_logged` + `reversal_rejected` + `reversal_authorized` + `reversal_unauthorized` + `cache_invalidated`) + H6 fix (`LedgerService.count_period_events` + `query_period_closing_snapshot_all` 정의) + AD-25 1-channel publisher (`CacheInvalidationPublisher`).
>
> **cj-style 3-story 분할 (Epic 5 retro §6 W1)** — Epic 4 A3 (Epic 5 5-1/5-2/5-3) + Epic 6 6-1/6-2/6-3 동일 패턴의 Epic 11 적용형. **11-1 = M11 module authority + AD-22 reversal ledger wire + A9 fill + H6 fix + AD-25 1-channel** (사용자 결정 + A9 매칭, ✅ done) → **11-2 = close-sequence-lock** (본 스토리, epics.md 11.1 greenfield) → **11-3 = snapshot-persistence-with-reverse** (epics.md 11.2 + 11.3 snapshot state machine + AD-25 publisher full wire). 3-story 모두 **additive** — 기존 wire contract 호환 + 사용자 흐름 무중단.
>
> **carry-over from 11-1 done**:
> - `apps/api/modules/m11_close/` populated (`__init__.py` + `handlers.py` + `services/{reversal_service.py, reversal_kernel_adapter.py}` + tests)
> - `apps/api/modules/m11_close/handlers.py` 3 routes: `POST /api/v1/close/reversal-requests` + `GET /api/v1/close/reversal-requests/{correction_group_id}` + `POST /api/v1/close/cache-invalidation`
> - `apps/api/main.py` 6 NEW exception handlers (ReversalTargetNotFoundError + ReversalRejectedError + ReversalUnauthorizedError + ReversalDuplicateError + LockedPeriodReversalRejectedError + CacheInvalidationChannelInvalidError)
> - `apps/api/core/audit_action.py:170-173` `ActionClass.REVERSAL_LOG` 5 values fill (D3 결정)
> - `apps/api/core/audit_action.py:223-227` `ActionClass.MONTHLY_INPUT_PERIOD` 1 NEW value extension (`opening_inventory_unlocked`)
> - `apps/api/core/capability.py` `Capability.REVERSAL_REQUEST` (manufacturing 3종 ✅ / service-only ❌)
> - `apps/api/core/cache_invalidation_publisher.py` (NEW, AD-25 1-channel)
> - `packages/services/m5_ledger/count_period_events.py` + `query_period_closing_snapshot_all.py` (H6 fix pure kernels)
> - `packages/services/m11_close/{reversal_negating.py, reversal_corrected.py, reversal_authorization.py}` (3 pure kernels)
> - `packages/cost_engine/ports/reversal_port.py` Protocol
> - `apps/web/lib/{m11-reversal.ts, m11-reversal-parity.ts}` (TS mirrors + banker's rounding parity)
> - `apps/web/components/m11-close/ReversalRequestDialog.tsx` + `ReversalRequestForm.tsx` (shadcn Dialog + sonner toast pattern)
> - `apps/web/ko-KR.json` 9 NEW strings
> - Alembic 0019_m11_reversal_ledger.py (reversal_log table + RLS + unique indexes)
> - Capability matrix v1.10
> - docs/reversal-sequence.md (NEW) + docs/audit-actions.md (NEW)

<!-- dev-context: Epic 5 close-out retro (2026-08-07) §6 W1 cj-style 결정 — "Epic 11 reversal module wire 진입점 (5-1 + 5-2 carry). cj-style 3-story 분할 패턴 (Epic 4 A3 + Epic 5 5-1/5-2/5-3 + Epic 6 6-1/6-2/6-3 동일) 적용. 11-1 = M11 module authority + AD-22 reversal wire + A9 fill + H6 fix + AD-25 1-channel (✅ done) → 11-2 = close-sequence-lock (epics.md 11.1 greenfield) → 11-3 = snapshot-persistence-with-reverse (epics.md 11.2 + 11.3 통합)".

본 스토리는 **PRD §F11.1 (Close sequence lock)** + **AD-6 (Fiscal-period close lock)** + **AD-22 (Reversal construction and ownership)** SSOT. PRD §8.M11(a) "시스템은 부문분할 → 제조 → ABC → 공동 순서를 강제하고, 부분 마감을 허용하지 않는다" 명시. Architecture Spine §AD-6 Rule 그대로 — "rows bounded by `fiscal_periods.status='closed'` reject business-data INSERTs except AD-22 reversal/correction events".

**11-1 ↔ 11-2 wire 정합 (CR 11-1 H6 + TODO marker)**:
- `packages/services/m11_close/reversal_authorization.py:8` 코멘트 — "11-2 wire 시점에 fiscal_periods.status 추가 가드 예정"
- `packages/services/m11_close/reversal_authorization.py:32` 코멘트 — "11-2 wire will introduce fiscal_periods.status='locked' guard"
- 본 스토리 wire 후 reversal_authorization.py 확장: `monthly_input_periods.status` + `fiscal_periods.status` 양쪽 가드 + `LockedPeriodReversalRejectedError` (11-1 6 NEW exception handlers 중 1개) → fiscal_periods.status='closed' 추가 dispatch.

**Epic 5 close-out retro (2026-08-07) §7 A9 결정 (Epic 11 reversal module wire 진입점)** — 11-1 wire 시점에 A9 5개 결정 모두 fill 완료 (reversal_negating/reversal_corrected event type + opening_inventory_unlocked action + reversal_request_enabled field wire + service layer reversal handler + UI reversal request form). 본 스토리는 A9 무관 (reversal sequence 자체 무변경, 가드 확장만).

**Epic 5 close-out retro (2026-08-07) §7 A11 결정 (V8 12 → 18 fixture matrix extension)** — 6-2 spec v1.8 완료 (18 fixture matrix = 12 baseline + 6 closing snapshot + ledger events). 11-2 wire는 4-stage close sequence V8 fixture 4 NEW 추가 (close_sequence_initiated + close_sequence_step_completed_partial_blocked + close_sequence_confirmed + close_sequence_reversal_blocked) — V8 18 → 22 fixture matrix extension. 본 스토리 wire 시점에 11-3 carry-over 결정 후 spec 진입.

**Epic 5 close-out retro (2026-08-07) §7 A10 결정 (MONTHLY_CLOSING_REPORT capability 신규)** — 6-1 wire 완료 (capability matrix v1.8). 11-2 wire는 CLOSE_SEQUENCE_LOCK capability 신규 (manufacturing 3종 ✅ / service-only ❌ 결정 + 11-2 capability matrix v1.11 wire).

**Epic 5 close-out retro (2026-08-07) §6 W2 deferral — Epic 11 close reopen flow (operator action + reason + audit row + AD-25 invalidation)** — 11-2 wire는 reopen 미포함 (operator action entry는 별도 follow-up Story / Epic 11 close-out retro 시점에 결정). 11-3 carry-over 검토 (snapshot-persistence-with-reverse state machine 통합 시 reopen dispatch 결정).

**Epic 4 close-out retro (2026-08-03) A3 cj-style** — 3-story 분할 유지 (5-1 → 5-2 → 5-3) + Epic 6 6-1/6-2/6-3 동일 패턴. Epic 11 11-1/11-2/11-3 동일 패턴 적용 (Epic 5 retro §6 §11 명시).

**Epic 4 close-out retro (2026-08-03) A5** — A5 Full Phase 1+2+4 done. Epic 5 5-1 + 5-3 + 6-1 + 6-2 audit log 일관성 보장 + A5 forward-lock + drift detector pattern 정착. 11-2 wire 동일 패턴 적용 (ClosingSequenceAction 4 values fill + ActionClass.MONTHLY_CLOSING frozenset fill + drift detector 3-way extension).

**Epic 4 close-out retro (2026-08-03) A7** — Epic 4 carry (async test pattern + SDR overclaim) Epic 5 + 6-1 + 6-2 + 11-1 wire. 11-2 동일 적용 (asyncio.run wrapper + SDR drift detector regeneration).

**Story 0-2 (2026-07-29)** — RLS 인프라 + audit_logs INSERT-only with `BEFORE UPDATE OR DELETE` trigger 패턴이 Epic 0에서 wire됨. AD-2 + AD-3 SSOT. 11-2 wire는 RLS 위에서 동작 (fiscal_periods tenant-scoped + 4-stage close_sequence_state 모두 RLS-scoped).

**Story 0-5 (2026-08-05)** — frontend plumbing wire ✅ done (commit ead1974). shadcn Card / Tabs / sonner / vitest + RTL + MSW / Playwright / next-intl / INDUSTRY_ICON fill. **11-2 frontend 진입 전 dep satisfied**. CloseSequencePanel (shadcn Card + StepIndicator + sonner toast pattern) 진입점 가능.

**Story 1.1 (2026-07-29)** — Industry enum SSOT (manufacturing / manufacturing_service / service / manufacturing_service_other) + capability matrix v1.0. 11-2 capability gate = `CLOSE_SEQUENCE_LOCK` (manufacturing 3종 ✅ / service-only ❌ — 6-1/6-2 closing_period_capability + A10 MONTHLY_CLOSING_REPORT wire 동일 패턴).

**Story 3.1 (2026-08-01)** — monthly_input_periods + monthly_input_rows 테이블. 11-2 wire는 monthly_input_periods.status='closed' 전이 → fiscal_periods.status='closed' cascading (idempotent no-op skip, CR 1.1).

**Story 3.3 (2026-08-01)** — `monthly_input_periods.opening_inventory` JSONB column (Alembic 0011) + F2.3 음수재고 입력 시 즉시 경고. **11-2 wire는 3.3 inline projection 보존 (Epic 6 close-out 시점에 fold-in 결정, Epic 5 retro §7 A8 timeline)**.

**Story 4.1 (2026-08-02)** — engine returns state='draft' (AD-22 boundary strengthening). 11-2 wire는 fiscal_periods status machine + 4-stage 순서 강제 — engine 무관 (engine은 close sequence 의미 모름).

**Story 4.2 (2026-08-03)** — REPEATABLE READ + audit-first (CR 1.1) + calc_log + AD-22 state transition. **11-2 wire는 4-2 calc result + 5-2 ledger aggregate + 6-1 closing_snapshot + 4-stage close sequence 순서 검증 atomic transaction (CR 4-2 1-shot INSERT 패턴 보존)**.

**Story 4.4 (2026-08-03)** — A5 forward-lock + 12 fixture matrix + V8 byte-identical CI gate. **11-2 wire는 V8 18→22 fixture matrix extension (4 NEW close sequence fixtures)**.

**Story 5.1 (2026-08-04, commit b4b84da)** — opening_carry_chain wire + 4 hooks into monthly_input_service. **5-1 carry-over to 11-2**: opening_inventory JSONB → fiscal_periods.divisions 단계 첫 검증 항목.

**Story 5.2 (2026-08-04, commit 7a13eb9)** — inventory_ledger append-only events + 4 routes + 11 values event_type CHECK + PostgreSQL BEFORE UPDATE OR DELETE row-level trigger + AD-22 reversal entrypoint forward-fill. **5-2 carry-over to 11-2**: 
  (a) `reversal_negating` + `reversal_corrected` 11-value event_type (Alembic 0015 lines 92-110) 이미 wire — 11-2 wire와 호환.
  (b) `reverses_event_id` + `correction_group_id` 컬럼 (nullable UUID, no FK) 이미 wire — 11-2 wire 호환.
  (c) `uq_inventory_ledger_reverses_event_id` UNIQUE `(tenant_id, reverses_event_id) WHERE reverses_event_id IS NOT NULL` (Alembic 0015 lines 197-201) 이미 wire — AD-6 INSERT 거부 후 reversal은 UNIQUE 통과.
  (d) `inventory_ledger_reversal_coherence` CHECK (Alembic 0015 lines 162-175) 이미 wire.
  (e) `inventory_ledger_qty_signed_coherence` CHECK (Alembic 0015 lines 125-142) — reversal_negating 음수 qty 허용.
  (f) append-only trigger `trg_inventory_ledger_append_only` (Alembic 0015 lines 228-253) — 11-2 AD-6 INSERT 거부 후에도 reversal INSERT은 통과.

**Story 5.3 (2026-08-06, commit 079f6a7)** — closing_guard pure kernel + closing_guard_service + 3 routes + MonthlyInputStateResponse 5 NEW fields + 6 NEW frontend files + 32 patches P1-P32. **5-3 carry-over to 11-2**: `closing_period_service.py:528/531` H6 호출 위치 (production bug — `LedgerService.count_period_events` + `query_period_closing_snapshot_all` 정의 부재 → runtime AttributeError 가능) — 11-1 wire 시점에 H6 fix done (commit b4961a6). 11-2 wire는 H6 fix 활용 + fiscal_periods 차원 확장.

**Story 6.1 (2026-08-08, commit 418ca2d)** — closing_period service + closing_snapshot ledger event wire + V4 verification. **6-1 carry-over to 11-2**: 
  (a) `closing_period_service.py:506-535` `_query_closing_via_ledger` 가 `LedgerService` 의 두 부재 메서드 호출 — H6 fix 11-1에서 done.
  (b) `closing_period_service.py:307-312` SELECT FOR UPDATE 패턴 (4-2 wire) — 11-2 close sequence 1-shot INSERT 동일 패턴.
  (c) `MonthlyInputStateResponse.reversal_request_enabled` field — Capability.REVERSAL_REQUEST capability_granted mirror (11-1 wire).
  (d) `MonthlyInputStateResponse.inventory_ledger_enabled` field — Capability.INVENTORY_LEDGER capability_granted mirror.
  (e) `ActionClass.CLOSING_PERIOD` 3 values (`closing_period_confirmed` / `closing_period_blocked` / `closing_period_snapshot_inconsistency`) — 11-2 wire 시점에 4 NEW values fill (`closing_sequence_initiated` + `closing_sequence_step_completed` + `closing_sequence_blocked` + `closing_sequence_confirmed`).
  (f) `MonthlyInputStateResponse.closing_period_state` field — 11-2 wire 시점에 4 NEW fields extension (`close_sequence_state` + `close_sequence_step_completed` + `close_sequence_blocked_reason_ko` + `close_sequence_capability_granted`).
  (g) `closing_period_service.py:259` `confirm_closing_period` — 11-2 wire는 `confirm_close_sequence` (4-stage 검증 추가) + 6-1 `confirm_closing_period` (per-monthly_input_periods status UPDATE) 위에 additive.

**Story 6.2 (2026-08-08, commit 30d6455)** — monthly closing report + V8 18-fixture matrix extension. **6-2 carry-over to 11-2**: 11-2 wire 시점에 4-stage close V8 fixture matrix extension (4 NEW 골든 fixture: close_sequence_initiated + close_sequence_step_completed_partial_blocked + close_sequence_confirmed + close_sequence_reversal_blocked). V8 18 → 22 fixture matrix. byte-identical CI gate 동일 패턴.

**Story 11.1 (2026-08-08, commit b4961a6)** — M11 module authority + AD-22 reversal ledger wire + A9 fill + H6 fix + AD-25 1-channel. **11-1 carry-over to 11-2**: 
  (a) `apps/api/modules/m11_close/` populated — 본 스토리에서 close sequence service layer 추가.
  (b) `packages/services/m11_close/reversal_authorization.py` `monthly_input_periods.status` 단일 가드 → 본 스토리에서 `fiscal_periods.status` 추가 가드.
  (c) `ActionClass.REVERSAL_LOG` 5 values fill — 본 스토리 wire와 무관.
  (d) `ActionClass.MONTHLY_INPUT_PERIOD` 1 NEW value extension (`opening_inventory_unlocked`) — 본 스토리 wire와 무관.
  (e) `Capability.REVERSAL_REQUEST` (manufacturing 3종 ✅ / service-only ❌) — 본 스토리 wire와 무관.
  (f) `apps/api/core/cache_invalidation_publisher.py` (NEW, AD-25 1-channel) — 11-2 wire는 close_sequence_confirmed 시 cache_invalidation 발행 (M10 AI cache invalidation trigger). 11-3 entry 시점에 publisher full wire (multi-channel 확장).
  (g) `apps/api/main.py` 6 NEW exception handlers — 본 스토리 wire 시점에 4 NEW extension (PartialCloseBlockedError + CloseSequenceAlreadyInitiatedError + CloseSequenceStepMismatchError + CloseSequenceCapabilityDeniedError).
  (h) `LockedPeriodReversalRejectedError` (422 LOCKED_PERIOD_REVERSAL_REJECTED) — 본 스토리 wire에서 `fiscal_periods.status='closed'` dispatch 추가 (11-1 wire는 monthly_input_periods.status='closed'만 dispatch).

**A9 (Epic 5 retro §7 결정, 2026-08-07)** — Epic 11 reversal module wire 진입점. 11-1 spec 진입 시점에 결정. 본 스토리는 A9 무관 (reversal sequence 가드 확장만).

**A11 (Epic 5 retro §7 결정, 2026-08-07)** — V8 12 → 18 fixture matrix extension (closing snapshot + ledger events). 6-2 spec v1.8 완료 (18 fixture matrix). 11-2 wire는 V8 18 → 22 fixture matrix extension (4 NEW close sequence 골든 fixture).

**AD-1 (modular monolith + hexagonal core)** — 11-2 wire는 engine port + service layer + handlers 표준 3-tier 패턴 (5-1/5-2/5-3/6-1/6-2/11-1 동일). `packages/services/m11_close/` 3 NEW pure kernels + `apps/api/modules/m11_close/services/close_sequence_service.py` (NEW) + `apps/api/modules/m11_close/handlers.py` EXTENSION.

**AD-2 (append-only ledger)** — 11-2 wire 호환. 5-2 inventory_ledger SSOT + PostgreSQL `BEFORE UPDATE OR DELETE` trigger 보존. fiscal_periods.status='closed' 후 business-data INSERT 거부 시 reversal INSERT은 통과.

**AD-3 (multi-tenant RLS)** — 11-2 wire는 RLS 위에서 동작. `tenant_id` 자동 derive from JWT (AD-3 SSOT). fiscal_periods RLS policy + 4-stage close_sequence_state 모두 RLS-scoped.

**AD-6 (close lock)** — 11-2 wire PRIMARY AC. `fiscal_periods.status='closed'` 후 모든 business-data INSERT 거부 (Architecture Spine §AD-6 Rule 그대로). AD-22 reversal/correction events만 허용. Reopen requires operator action + reason + audit row + AD-25 invalidation (Epic 5 retro §6 W2 deferral — 11-3 carry).

**AD-11 (dependency direction / layer rule)** — pure helpers = `packages/services/m11_close/` 3 NEW pure kernels. service layer = `apps/api/modules/m11_close/services/close_sequence_service.py` (NEW). handlers = `apps/api/modules/m11_close/handlers.py` EXTENSION (3 NEW routes). engine layer (`packages/cost_engine/`) 무변경 (engine은 close sequence 의미 모름 — 4-2 wire 패턴).

**AD-15 (cross-language parity)** — TS mirror `apps/web/lib/m11-close-sequence.ts` (NEW) + Decimal serialization parity (close sequence state = 'divisions' | 'manufacturing' | 'abc' | 'common' | 'confirmed', banker's rounding to int for 4-stage progress indicator).

**AD-22 (reversal construction)** — 11-2 wire 호환. AD-22 reversal sequence = (1) sign-negating row INSERT (reverses_event_id link + reversal_of_period_key) + (2) optional corrected row INSERT (correction_group_id share). Original never changes. fiscal_periods.status='closed' 후 reversal INSERT만 허용 (AD-6 exception).

**AD-25 (cache invalidation notification)** — 11-2 wire는 `close_sequence_confirmed` 시 cache_invalidation 1-channel 발행 (11-1 CacheInvalidationPublisher reuse). 11-3 entry 시점에 publisher full wire (multi-channel 확장).

**AD-23 (4-namespace pattern)** — monthly_input_periods + monthly_input_rows + inventory_ledger + audit_logs + fiscal_period_snapshots + fiscal_periods (NEW namespace, 11-2 wire) + reversal_log (11-1 wire) = 7 namespace.

**AD-24 (typed period-key)** — 'YYYY-MM' 형식 SSOT. fiscal_periods.period_key = AD-24 typed. monthly_input_periods.period_key 동일.

**PRD §F11.1 (Close sequence lock)** — 11-2 PRIMARY AC. "부문분할→제조→ABC→공동 순서 + 부분 마감 없음" 명시. 4-stage close sequence order 강제.

**PRD §8.M11(a)** — "시스템은 부문분할 → 제조 → ABC → 공동 순서를 강제하고, 부분 마감을 허용하지 않는다" 명시. 11-2 PRIMARY AC.

**PRD §6.4 (industry × engine mapping)** — "제조 부문 → 전통 개별원가 엔진 / 서비스 부문 → ABC 엔진(classic + TDABC)". 4-stage 순서의 divisions → manufacturing → ABC → common 매핑.

**PRD §Q-I (industry × engine 고정 매핑)** — "제조 ABC는 3차 로드맵". 11-2 wire 시점에 manufacturing 단계 = 전통 개별원가 엔진 + ABC 단계 = service-only tenant 전용 분기.

**PRD §8.0 (A2 audit-first + idempotent no-op)** — CR 1.1 SSOT. 11-2 wire 모두 audit-first + idempotent no-op (fiscal_periods.status='closed' 후 re-confirm 시도 → no-op skip).

**PRD §A11 (3-layer defense)** — "입력 시 경고 + 마감 시 차단". 11-2 wire는 마감 시 차단 (Layer 2 = 5-3 closing_guard + 4-stage close sequence 4 검증) + 마감 확정 시 snapshot (Layer 3 = 6-1 confirm_closing_period + 11-2 confirm_close_sequence).

**PRD §F11.2 (마감 후 입력 수정은 역분개로만)** — 11-1 wire (`monthly_input_periods.status='closed'` reversal 허용) + 11-2 wire (`fiscal_periods.status='closed'` 추가 가드).

**PRD §F11.3 (마감 후 원본 변경 금지)** — 11-1 wire (AD-22 reversal sequence INSERT만 허용) + 11-2 wire (fiscal_periods.status='closed' 후 business-data INSERT 거부).

## Story

As a **사장님**,
I want **마감 순서가 부문분할→제조→ABC→공동 순서로 강제되고 부분 마감이 안 되는 것**,
so that **한 단계만 잠그는 사고를 방지 + 마감 후 임의 변경이 불가능하여 손익·재고가 마감 시점에 영구 보존**.

## Acceptance Criteria

1. **fiscal_periods 테이블 greenfield 신설 + RLS + 4-stage close_sequence_state (AD-6/AD-22 wire)**
   - (a) `apps/api/alembic/versions/0020_fiscal_periods_close_sequence.py` (NEW) — `fiscal_periods` 테이블 생성:
     - `id` (UUID v7, PK), `tenant_id` (ULID, FK tenants.id), `period_key` (TEXT, AD-24 typed 'YYYY-MM')
     - `status` (TEXT NOT NULL DEFAULT 'open' — 'open' | 'closing' | 'closed' | 'reversed', 1-way state machine AD-6)
     - `divisions_completed_at` (TIMESTAMPTZ NULLABLE — 부문분할 단계 완료 시각)
     - `manufacturing_completed_at` (TIMESTAMPTZ NULLABLE — 제조 단계 완료 시각)
     - `abc_completed_at` (TIMESTAMPTZ NULLABLE — ABC 단계 완료 시각)
     - `common_completed_at` (TIMESTAMPTZ NULLABLE — 공동 단계 완료 시각)
     - `close_sequence_state` (TEXT NOT NULL DEFAULT 'divisions' — 'divisions' | 'manufacturing' | 'abc' | 'common' | 'confirmed', 1-way state machine)
     - `close_sequence_blocked_reason_ko` (TEXT NULLABLE — 부분 마감 거부 사유 한국어, AD-15 §11 SSOT)
     - `closed_at` (TIMESTAMPTZ NULLABLE — status='closed' 전이 시각)
     - `closed_by_actor_id` (UUID v7, FK users.id NULLABLE — confirm_close_sequence initiator)
     - `created_at` + `updated_at` (TIMESTAMPTZ NOT NULL)
     - `UNIQUE (tenant_id, period_key)` — 1 fiscal_period per tenant per period
     - `CHECK status IN ('open', 'closing', 'closed', 'reversed')`
     - `CHECK close_sequence_state IN ('divisions', 'manufacturing', 'abc', 'common', 'confirmed')`
     - `CHECK divisions_completed_at IS NOT NULL OR manufacturing_completed_at IS NULL` — 단계 순서 검증 CHECK (defense-in-depth)
     - `CHECK manufacturing_completed_at IS NOT NULL OR abc_completed_at IS NULL`
     - `CHECK abc_completed_at IS NOT NULL OR common_completed_at IS NULL`
     - `CHECK status = 'closed' OR close_sequence_state != 'confirmed'` — confirmed → status='closed' 일관성
     - `CHECK status != 'closed' OR closed_at IS NOT NULL` — closed 시 closed_at 필수
     - `INDEX idx_fiscal_periods_tenant_period (tenant_id, period_key)` — RLS + close_sequence_state lookup
     - `INDEX idx_fiscal_periods_close_sequence_state (tenant_id, close_sequence_state)` — partial close detection
   - (b) `apps/api/alembic/versions/0020` mirror extension: `apps/api/core/db_models.py` `FiscalPeriod` (NEW, SQLAlchemy 2.x `Mapped[T]` 패턴, 5-1/5-2/6-1 동일 패턴) + Alembic 0020에 `__table_args__` mirror
   - (c) `supabase/policies/0011_fiscal_periods_rls.sql` (NEW) — `ALTER TABLE fiscal_periods ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY` + 4-policy split (tenant_select_own + tenant_insert_own + tenant_update_own_blocked_status + tenant_delete_blocked) — 5-2/6-1 RLS 패턴 동일
   - (d) 11-1 wire 정합: `packages/services/m11_close/reversal_authorization.py:8-32` 코멘트 — "fiscal_periods.status 추가 가드" 본 스토리 wire 후 update. line 32 `# 11-2 wire will introduce fiscal_periods.status='locked' guard` → line 32+ NEW comment block: "fiscal_periods.status 가드는 AD-6 close lock PRIMARY, monthly_input_periods.status='closed' dispatch는 11-1 wire 호환"

2. **4단계 divisions → manufacturing → ABC → common 순서 강제 (PRD §F11.1 PRIMARY)**
   - (a) `packages/services/m11_close/close_sequence_order.py` (NEW pure kernel) — `validate_close_sequence_order(divisions_completed_at, manufacturing_completed_at, abc_completed_at, common_completed_at) -> CloseSequenceOrderResult` (stdlib-only, AD-11 layer rule)
     - 검증 규칙: `divisions_completed_at IS NOT NULL AND manufacturing_completed_at IS NULL OR manufacturing_completed_at > divisions_completed_at` (defense-in-depth CHECK 동등)
     - 검증 규칙: `abc_completed_at IS NULL OR abc_completed_at > manufacturing_completed_at`
     - 검증 규칙: `common_completed_at IS NULL OR common_completed_at > abc_completed_at`
     - `CloseSequenceOrderResult` NamedTuple: `valid: bool`, `violations: tuple[str, ...]`, `next_step: str` ('divisions' | 'manufacturing' | 'abc' | 'common' | 'confirmed')
     - `CLOSE_SEQUENCE_ORDER_VIOLATIONS_KO` Korean constants: "divisions 단계 미완료" + "manufacturing 단계 미완료" + "abc 단계 미완료" + "common 단계 미완료"
   - (b) `packages/services/m11_close/close_sequence_order.py` ~20 pure tests (close sequence order all 4 patterns + chronological 순서 검증 + violation cases + next_step transition 4 stages)
   - (c) `apps/web/lib/m11-close-sequence.ts` (NEW TS mirror) — `validateCloseSequenceOrder()` 함수 + `CLOSE_SEQUENCE_ORDER_VIOLATIONS_KO` constants verbatim + Decimal 직렬화 parity (banker's rounding)
   - (d) `apps/web/lib/m11-close-sequence-parity.ts` (NEW TS parity test) — Python pure kernel ↔ TS mirror 5 cases (validate parity, edge cases, ordering invariants) — 6-1/6-2/11-1 TS parity 패턴 동일

3. **부분 마감 불허 (한 단계만 완료 후 마감 진입 시도 → 409 PARTIAL_CLOSE_BLOCKED typed envelope)**
   - (a) `packages/services/m11_close/partial_close_guard.py` (NEW pure kernel) — `check_partial_close_attempt(close_sequence_state, divisions_completed_at, manufacturing_completed_at, abc_completed_at, common_completed_at) -> PartialCloseGuardResult` (stdlib-only)
     - 검증 규칙: `confirm_close_sequence` 진입 시 `close_sequence_state='confirmed'` 도달을 위해서는 4단계 모두 완료 필수
     - 4단계 모두 미완료 시 → `PartialCloseGuardResult(blocked=True, missing_step='divisions', reject_reason_ko=PARTIAL_CLOSE_BLOCKED_KO)`
     - 3단계만 완료 시 → `block_reason='4단계 모두 완료 후 마감 가능'` + `missing_step='common'`
     - 검증 통과 시 → `PartialCloseGuardResult(blocked=False, missing_step=None, reject_reason_ko=None)`
   - (b) `packages/services/m11_close/partial_close_guard.py` ~15 pure tests (4단계 모두 완료 + 3단계만 완료 + 2단계만 완료 + 1단계만 완료 + 0단계 + chronological invariant)
   - (c) `apps/api/modules/m11_close/services/close_sequence_service.py` (NEW service layer) — `confirm_close_sequence(period_key, *, actor_id) -> dict[str, Any]`
     - SELECT FOR UPDATE on `fiscal_periods` (6-1 wire 패턴 동일)
     - `evaluate_close_sequence_state` (read-only status check via `query_fiscal_period_by_id` + `compute_close_sequence_progress`)
     - `check_partial_close_attempt` (partial close guard) → `PartialCloseBlockedError` raise (409 PARTIAL_CLOSE_BLOCKED typed envelope)
     - 4단계 모두 완료 시 → ledger INSERT (closing_snapshot event_type per product — 6-1 wire 진입점 동일) + `monthly_input_periods.status='closed'` UPDATE (6-1 wire 진입점 동일) + `fiscal_periods.status='closed'` + `close_sequence_state='confirmed'` UPDATE + audit-first emit (closing_sequence_confirmed, AD-15 §11 Korean message)
   - (d) `apps/api/modules/m11_close/services/close_sequence_service.py` 4 typed exceptions (AD-15 §4 envelope mapping):
     - `PartialCloseBlockedError` (409 PARTIAL_CLOSE_BLOCKED) — 4단계 미완료 시 confirm_close_sequence 거부
     - `CloseSequenceAlreadyInitiatedError` (409 CLOSE_SEQUENCE_ALREADY_INITIATED) — initiate_close_sequence 중복 호출 거부
     - `CloseSequenceStepMismatchError` (409 CLOSE_SEQUENCE_STEP_MISMATCH) — 단계 순서 mismatch 시 거부 (예: divisions 단계 완료 전 manufacturing step_complete 호출)
     - `CloseSequenceCapabilityDeniedError` (403 CLOSE_SEQUENCE_CAPABILITY_DENIED) — service-only tenant capability_granted=False

4. **AD-6 INSERT 거부 (`fiscal_periods.status='closed'` 후 모든 business-data INSERT 거부, AD-22 reversal/correction events만 허용)**
   - (a) `packages/services/m11_close/close_sequence_state.py` (NEW pure kernel) — `compute_close_sequence_state(divisions_completed_at, manufacturing_completed_at, abc_completed_at, common_completed_at, closed_at) -> str` ('divisions' | 'manufacturing' | 'abc' | 'common' | 'confirmed')
     - 0단계 → 'divisions', 1단계 → 'manufacturing', 2단계 → 'abc', 3단계 → 'common', 4단계 + closed_at → 'confirmed'
     - `check_ad6_insert_allowed(close_sequence_state, target_table, target_event_type) -> bool` — AD-6 Rule 검증
     - 허용: `target_table='inventory_ledger' AND target_event_type IN ('reversal_negating', 'reversal_corrected')` (AD-22 exception)
     - 거부: `close_sequence_state='confirmed' AND target_table IN ('monthly_input_periods', 'monthly_input_rows', 'inventory_ledger', 'fiscal_period_snapshots') AND target_event_type NOT IN ('reversal_negating', 'reversal_corrected')`
   - (b) `apps/api/modules/m11_close/services/close_sequence_service.py` — `confirm_close_sequence` flow:
     - step (3.5) AD-6 INSERT 거부 guard: `compute_close_sequence_state` + `check_ad6_insert_allowed` 호출 — `fiscal_periods.status='closed'` 후 business-data INSERT 거부
     - inventory_ledger INSERT (closing_snapshot event_type) — AD-6 close 직전이라 허용
     - monthly_input_periods.status='closed' UPDATE — AD-6 close 동시 dispatch
     - fiscal_periods.status='closed' + close_sequence_state='confirmed' UPDATE
     - audit-first emit (closing_sequence_confirmed)
   - (c) `packages/services/m11_close/close_sequence_state.py` ~20 pure tests (0/1/2/3/4단계 + AD-6 allow/reject matrix 6 cases + AD-22 reversal/correction event allow)
   - (d) `apps/web/lib/m11-close-sequence.ts` (NEW TS mirror) — `computeCloseSequenceState` + `checkAd6InsertAllowed` 함수 + Korean SSOT constants

5. **monthly_input_periods.status='closed' → fiscal_periods.status='closed' cascading (idempotent no-op skip, CR 1.1)**
   - (a) `apps/api/modules/m11_close/services/close_sequence_service.py` — `confirm_close_sequence` flow:
     - step (0.5) 기존 `confirm_closing_period` (6-1 wire) 호출 → monthly_input_periods.status='closed' UPDATE
     - step (1) SELECT FOR UPDATE on `fiscal_periods` (idempotent no-op skip on already 'confirmed')
     - step (2) partial close guard (AC #3)
     - step (3) AD-6 INSERT 거부 guard (AC #4)
     - step (4) inventory_ledger INSERT (closing_snapshot event_type per product)
     - step (5) V4 verifier dispatch (6-1 wire 진입점)
     - step (6) `fiscal_periods.status='closed'` + `close_sequence_state='confirmed'` UPDATE + closed_at=now()
     - step (7) audit-first emit (closing_sequence_confirmed, AD-15 §11 Korean)
   - (b) `apps/api/modules/m11_close/services/close_sequence_service.py` 4 typed exceptions (AC #3 (d) + AC #4 (d) 위 정의) + `ClosingSequenceAuditEmitError` (500) — audit-first emit failure
   - (c) CR 1.1 audit-first ordering 보존: ledger INSERT (step 4) → fiscal_periods UPDATE (step 6) → audit log INSERT (step 7) 순서 atomic transaction (6-1 wire 패턴 동일)
   - (d) Idempotent no-op skip: `fiscal_periods.status='closed'` 후 re-confirm 시도 → `ClosingSequenceAlreadyConfirmedError` (409 ALREADY_CONFIRMED) typed envelope + audit emit skip

6. **11-1 reversal_authorization.py 확장 (monthly_input_periods.status + fiscal_periods.status 양쪽 가드)**
   - (a) `packages/services/m11_close/reversal_authorization.py` (11-1 wire EXTENSION) — `authorize_reversal()` 함수 시그니처 확장:
     - 기존: `period_status: str` (monthly_input_periods.status 단일)
     - 신규: `period_status: str` + `fiscal_period_status: str` (fiscal_periods.status 추가)
     - 검증 규칙: `fiscal_period_status='closed' AND period_status='closed'` 모두 통과 시 reversal 허용 (11-1 호환)
     - 검증 규칙: `fiscal_period_status='closed' AND period_status='closed' AND target_event_type IN REVERSIBLE_TARGET_EVENT_TYPES` → reversal_allowed
     - 검증 규칙: `fiscal_period_status IN ('open', 'closing')` → reversal 거부 (마감 진행 중 = 422 LOCKED_PERIOD_REVERSAL_REJECTED)
   - (b) `LockedPeriodReversalRejectedError` (11-1 wire 6 NEW exception handlers 중 1개) — fiscal_periods.status='closed' 추가 dispatch (11-1 wire는 monthly_input_periods.status='closed'만 dispatch)
   - (c) `packages/services/m11_close/reversal_authorization.py` ~10 NEW tests (fiscal_period_status='closed' + monthly_input_periods.status='closed' dual guard matrix 6 cases + 'open'/'closing'/'closed' status별 3 cases + REVERSIBLE_TARGET_EVENT_TYPES cross-product)
   - (d) `apps/api/modules/m11_close/services/reversal_service.py` (11-1 wire EXTENSION) — `execute_reversal()` 함수:
     - `period_status` (monthly_input_periods.status) + `fiscal_period_status` (fiscal_periods.status) 양쪽 fetch
     - `authorize_reversal` 호출 시 두 status 모두 전달
     - `LockedPeriodReversalRejectedError` raise 시 fiscal_periods.status dispatch 추가

7. **A5 forward-lock (ActionClass.MONTHLY_CLOSING 4 values fill + drift detector 3-way extension)**
   - (a) `apps/api/core/audit_action.py` (EXTENSION) — `ActionClass.MONTHLY_CLOSING` 4 NEW values fill:
     - `closing_sequence_initiated` — initiate_close_sequence succeeded (fiscal_periods 생성 + close_sequence_state='divisions')
     - `closing_sequence_step_completed` — step_complete 호출 시 단계별 완료 (divisions/manufacturing/abc/common)
     - `closing_sequence_blocked` — partial_close_guard 거부 (4단계 미완료 → 409 PARTIAL_CLOSE_BLOCKED)
     - `closing_sequence_confirmed` — confirm_close_sequence succeeded (4단계 모두 완료 + fiscal_periods.status='closed')
   - (b) `apps/api/core/audit_action.py:223-227` `ActionClass.CLOSING_PERIOD` 보존 (6-1 wire) + `ActionClass.MONTHLY_CLOSING` 별도 frozenset (M11 전용)
   - (c) `tests/services/test_audit_action_centralization.py` (EXTENSION) — `ActionClass.MONTHLY_CLOSING` 4 NEW values registered verification (AST-grep `emit_audit_typed` hits = 0 유지)
   - (d) `tests/integration/test_audit_action_consistency.py` (EXTENSION) — 3-way drift detector (registry ↔ DB CHECK ↔ call sites) — 4 NEW cases (initiated + step_completed + blocked + confirmed)

8. **capability matrix v1.11 (CLOSE_SEQUENCE_LOCK 신규 — manufacturing 3종 ✅ / service-only ❌)**
   - (a) `apps/api/core/capability.py` (EXTENSION) — `Capability.CLOSE_SEQUENCE_LOCK` 신규:
     - `manufacturing` ✅ (제조 부문 마감 진입 가능)
     - `manufacturing_service` ✅ (겸영 제조 부문)
     - `service` ❌ (서비스 부문 단독 = service-only tenant)
     - `manufacturing_service_other` ✅ (3-engine 겸영)
     - rationale: PRD §6.4 + §Q-I (industry × engine 고정 매핑 — 제조 ABC는 3차 로드맵)
   - (b) `apps/api/modules/m11_close/handlers.py` (EXTENSION) — 3 NEW routes 진입 시 capability gate:
     - `POST /api/v1/close/sequence/initiate` — initiate_close_sequence (CLOSE_SEQUENCE_LOCK capability gate)
     - `POST /api/v1/close/sequence/step-complete` — step_complete (CLOSE_SEQUENCE_LOCK capability gate)
     - `GET /api/v1/close/sequence/state` — get_close_sequence_state (CLOSE_SEQUENCE_LOCK capability gate, read-only)
   - (c) `apps/api/main.py` 4 NEW exception handlers wire (AC #3 (d) 4 typed exceptions + AC #4 dispatch):
     - `PartialCloseBlockedError` (409 PARTIAL_CLOSE_BLOCKED)
     - `CloseSequenceAlreadyInitiatedError` (409 CLOSE_SEQUENCE_ALREADY_INITIATED)
     - `CloseSequenceStepMismatchError` (409 CLOSE_SEQUENCE_STEP_MISMATCH)
     - `CloseSequenceCapabilityDeniedError` (403 CLOSE_SEQUENCE_CAPABILITY_DENIED)
   - (d) `docs/capability-matrix.md` v1.11 (EXTENSION) — CLOSE_SEQUENCE_LOCK 신규 capability 행 추가 + 6-1 CLOSING_GUARD + 6-2 MONTHLY_CLOSING_REPORT + 11-1 REVERSAL_REQUEST 보존
   - (e) Capability matrix drift detector (`tests/services/test_capability_matrix_drift.py` NEW) — Capability enum ↔ capability-matrix.md 행 cross-check 3 cases (CLOSE_SEQUENCE_LOCK 등록 + 4-industry × 4-capability 매트릭스 + AD-15 §11 SSOT consistency)

9. **Alembic 0020 NEW (fiscal_periods + 4-stage sections + close_sequence_state + RLS) + 11-1 wire 정합**
   - (a) `apps/api/alembic/versions/0020_fiscal_periods_close_sequence.py` (NEW migration) — `down_revision='0019_m11_reversal_ledger'` (11-1 wire tip) + `revision='0020_fiscal_periods_close_sequence'`
   - (b) 11-1 wire 정합 검증 — Alembic 0019 reversal_ledger migration + Alembic 0020 fiscal_periods migration 호환성:
     - Alembic 0019 reversal_log 테이블 + RLS + unique indexes 보존
     - Alembic 0020 fiscal_periods 테이블 + RLS + close_sequence_state CHECK 보존
     - migration 순서: 0001 → ... → 0019 → 0020 (sequential)
   - (c) `alembic upgrade head` dry-run 검증 + CI shim 통과 (db-backed CI-only, Story 0-5 plumbing)
   - (d) `tests/api/test_alembic_0020_fiscal_periods.py` (NEW) — 8 cases (upgrade head 시 fiscal_periods 생성 + RLS 정책 4-policy split + CHECK constraints 5개 + UNIQUE constraint + INDEX 2개 + 4-namespace pattern 검증)
   - (e) `tests/api/test_db_models_fiscal_period.py` (NEW) — 6 cases (FiscalPeriod ORM 모델 — status state machine + close_sequence_state transition + closed_at trigger + CHECK constraints)
   - (f) `tests/integration/test_fiscal_periods_rls.py` (NEW) — 12 cases (RLS 4-policy split + tenant isolation + INSERT blocked on status='closed' + reversal INSERT allowed on status='closed' — AD-6 exception)

10. **closing_period_service 확장: confirm_close_sequence + get_close_sequence_state + initiate_close_sequence (4-stage verification wire)**
    - (a) `apps/api/modules/m11_close/services/close_sequence_service.py` (NEW) — 3 operations:
      - `initiate_close_sequence(period_key, *, actor_id) -> dict[str, Any]` — fiscal_periods INSERT (close_sequence_state='divisions') + audit emit (closing_sequence_initiated)
      - `step_complete(period_key, step_name, *, actor_id) -> dict[str, Any]` — 4단계 순서 검증 + fiscal_periods step column UPDATE (divisions_completed_at / manufacturing_completed_at / abc_completed_at / common_completed_at) + audit emit (closing_sequence_step_completed)
      - `confirm_close_sequence(period_key, *, actor_id) -> dict[str, Any]` — 4단계 모두 완료 검증 + ledger INSERT (closing_snapshot event_type) + monthly_input_periods.status='closed' UPDATE (6-1 wire 진입점) + fiscal_periods.status='closed' + close_sequence_state='confirmed' UPDATE + V4 verifier dispatch (6-1 wire 진입점) + audit emit (closing_sequence_confirmed)
      - `get_close_sequence_state(period_key) -> dict[str, Any]` — read-only status check (fiscal_periods row + 4-stage progress + missing step)
    - (b) `apps/api/modules/m11_close/services/close_sequence_service.py` SQLAlchemy 2.x AsyncSession + 11-1 wire 동일 패턴 (REPEATABLE READ + audit-first + idempotent no-op skip + SELECT FOR UPDATE)
    - (c) `apps/api/modules/m11_close/services/close_sequence_service.py` 4 typed exceptions (AC #3 (d) + AC #4 (d) + ClosingSequenceAlreadyConfirmedError 409 ALREADY_CONFIRMED + ClosingSequenceAuditEmitError 500)
    - (d) `apps/api/modules/m11_close/services/__init__.py` (EXTENSION) — `close_sequence_service` re-export
    - (e) `apps/api/modules/m11_close/handlers.py` (EXTENSION) — 3 NEW routes + capability gate (CLOSE_SEQUENCE_LOCK) + request/response schema + error mapping
    - (f) `apps/api/modules/m11_close/services/close_sequence_service.py` 6 NEW tests (initiate success + initiate idempotent + step_complete divisions + step_complete manufacturing + confirm partial_blocked + confirm success + already_confirmed idempotent)

## Tasks / Subtasks

- [ ] **Task 1: Alembic 0020 + fiscal_periods ORM + RLS + 4-stage close_sequence_state** (AC: #1, #9)
  - [ ] Subtask 1.1: `apps/api/alembic/versions/0020_fiscal_periods_close_sequence.py` (NEW) — fiscal_periods 테이블 + 5 CHECK constraints + UNIQUE + INDEX 2개 + close_sequence_state 1-way state machine
  - [ ] Subtask 1.2: `apps/api/core/db_models.py` (EXTENSION) — `FiscalPeriod` ORM (Mapped[T] 패턴 + __table_args__ mirror + 5-1/5-2/6-1/11-1 동일 SQLAlchemy 2.x)
  - [ ] Subtask 1.3: `supabase/policies/0011_fiscal_periods_rls.sql` (NEW) — ENABLE + FORCE RLS + 4-policy split (tenant_select_own + tenant_insert_own + tenant_update_own_blocked_status + tenant_delete_blocked) — 5-2/6-1 RLS 패턴 동일
  - [ ] Subtask 1.4: 11-1 wire 정합 — `packages/services/m11_close/reversal_authorization.py:8-32` 코멘트 업데이트 ("fiscal_periods.status 추가 가드" 본 스토리 wire 후 update)
  - [ ] Subtask 1.5: `tests/api/test_alembic_0020_fiscal_periods.py` (NEW) — 8 cases
  - [ ] Subtask 1.6: `tests/api/test_db_models_fiscal_period.py` (NEW) — 6 cases
  - [ ] Subtask 1.7: `tests/integration/test_fiscal_periods_rls.py` (NEW) — 12 cases (RLS 4-policy split + tenant isolation + INSERT blocked on status='closed' + reversal INSERT allowed on status='closed')
- [ ] **Task 2: 4-stage close_sequence_order pure kernel + TS mirror + parity** (AC: #2)
  - [ ] Subtask 2.1: `packages/services/m11_close/close_sequence_order.py` (NEW pure kernel) — `validate_close_sequence_order()` + `CloseSequenceOrderResult` NamedTuple + Korean constants
  - [ ] Subtask 2.2: `tests/services/test_close_sequence_order.py` (NEW) — ~20 pure tests (close sequence order all 4 patterns + chronological 순서 + violation + next_step transition 4 stages)
  - [ ] Subtask 2.3: `apps/web/lib/m11-close-sequence.ts` (NEW TS mirror) — `validateCloseSequenceOrder()` + `CLOSE_SEQUENCE_ORDER_VIOLATIONS_KO` constants verbatim + Decimal 직렬화 parity
  - [ ] Subtask 2.4: `apps/web/lib/m11-close-sequence-parity.ts` (NEW TS parity test) — Python ↔ TS 5 cases
- [ ] **Task 3: partial_close_guard pure kernel + 4 typed exceptions + service layer** (AC: #3)
  - [ ] Subtask 3.1: `packages/services/m11_close/partial_close_guard.py` (NEW pure kernel) — `check_partial_close_attempt()` + `PartialCloseGuardResult` NamedTuple + Korean constants (PARTIAL_CLOSE_BLOCKED_KO + MISSING_STEP_*_KO)
  - [ ] Subtask 3.2: `tests/services/test_partial_close_guard.py` (NEW) — ~15 pure tests (4단계 모두 + 3단계 + 2단계 + 1단계 + 0단계 + chronological invariant)
  - [ ] Subtask 3.3: `apps/api/modules/m11_close/services/close_sequence_service.py` (NEW) — `confirm_close_sequence()` + 4 typed exceptions (PartialCloseBlockedError + CloseSequenceAlreadyInitiatedError + CloseSequenceStepMismatchError + CloseSequenceCapabilityDeniedError)
  - [ ] Subtask 3.4: `apps/api/modules/m11_close/services/__init__.py` (EXTENSION) — `close_sequence_service` re-export
- [ ] **Task 4: AD-6 INSERT 거부 + close_sequence_state pure kernel + service layer wire** (AC: #4)
  - [ ] Subtask 4.1: `packages/services/m11_close/close_sequence_state.py` (NEW pure kernel) — `compute_close_sequence_state()` + `check_ad6_insert_allowed()` + Korean constants
  - [ ] Subtask 4.2: `tests/services/test_close_sequence_state.py` (NEW) — ~20 pure tests (0/1/2/3/4단계 + AD-6 allow/reject matrix 6 cases + AD-22 reversal/correction event allow)
  - [ ] Subtask 4.3: `apps/web/lib/m11-close-sequence.ts` (EXTENSION) — `computeCloseSequenceState` + `checkAd6InsertAllowed` 함수 + Korean SSOT
  - [ ] Subtask 4.4: `apps/api/modules/m11_close/services/close_sequence_service.py` (EXTENSION) — AD-6 INSERT 거부 guard (step 3.5) + closing_snapshot event_type INSERT (step 4) + fiscal_periods.status='closed' + close_sequence_state='confirmed' UPDATE (step 6)
- [ ] **Task 5: monthly_input_periods.status='closed' → fiscal_periods.status='closed' cascading (CR 1.1)** (AC: #5)
  - [ ] Subtask 5.1: `apps/api/modules/m11_close/services/close_sequence_service.py` (EXTENSION) — `confirm_close_sequence()` 7-step flow (6-1 wire + AD-6 guard + 4-stage verification)
  - [ ] Subtask 5.2: `tests/api/test_close_sequence_service.py` (NEW) — 6 cases (initiate success + idempotent + step_complete divisions + manufacturing + confirm partial_blocked + confirm success + already_confirmed idempotent)
  - [ ] Subtask 5.3: CR 1.1 audit-first ordering 검증 (ledger INSERT → fiscal_periods UPDATE → audit log INSERT 순서 atomic)
  - [ ] Subtask 5.4: Idempotent no-op skip 검증 (`fiscal_periods.status='closed'` 후 re-confirm 시도 → ALREADY_CONFIRMED + audit emit skip)
- [ ] **Task 6: 11-1 reversal_authorization.py 확장 (fiscal_periods.status 추가 가드)** (AC: #6)
  - [ ] Subtask 6.1: `packages/services/m11_close/reversal_authorization.py` (11-1 wire EXTENSION) — `authorize_reversal()` 시그니처 확장 (period_status + fiscal_period_status 양쪽 입력)
  - [ ] Subtask 6.2: `tests/services/test_reversal_authorization_fiscal_period_extension.py` (NEW) — ~10 cases (dual guard matrix 6 + status별 3 + REVERSIBLE_TARGET_EVENT_TYPES cross-product)
  - [ ] Subtask 6.3: `apps/api/modules/m11_close/services/reversal_service.py` (11-1 wire EXTENSION) — `execute_reversal()` fiscal_period_status fetch + authorize_reversal 호출 dispatch
  - [ ] Subtask 6.4: `LockedPeriodReversalRejectedError` (11-1 6 NEW exception handlers) fiscal_periods.status='closed' dispatch 추가
- [ ] **Task 7: A5 forward-lock (ActionClass.MONTHLY_CLOSING 4 values fill + drift detector 3-way extension)** (AC: #7)
  - [ ] Subtask 7.1: `apps/api/core/audit_action.py` (EXTENSION) — `ActionClass.MONTHLY_CLOSING` 4 NEW values fill (`closing_sequence_initiated` + `closing_sequence_step_completed` + `closing_sequence_blocked` + `closing_sequence_confirmed`)
  - [ ] Subtask 7.2: `apps/api/core/audit_action.py` (EXTENSION) — `ActionClass.MONTHLY_CLOSING: ("monthly_closing", frozenset({"closing_sequence_initiated", "closing_sequence_step_completed", "closing_sequence_blocked", "closing_sequence_confirmed"}))` frozenset fill
  - [ ] Subtask 7.3: `tests/services/test_audit_action_centralization.py` (EXTENSION) — `ActionClass.MONTHLY_CLOSING` 4 NEW values registered verification (AST-grep `emit_audit_typed` hits = 0 유지)
  - [ ] Subtask 7.4: `tests/integration/test_audit_action_consistency.py` (EXTENSION) — 3-way drift detector 4 NEW cases (initiated + step_completed + blocked + confirmed)
- [ ] **Task 8: capability matrix v1.11 (CLOSE_SEQUENCE_LOCK 신규) + 4 NEW exception handlers** (AC: #8)
  - [ ] Subtask 8.1: `apps/api/core/capability.py` (EXTENSION) — `Capability.CLOSE_SEQUENCE_LOCK` 신규 (manufacturing 3종 ✅ / service-only ❌)
  - [ ] Subtask 8.2: `apps/api/modules/m11_close/handlers.py` (EXTENSION) — 3 NEW routes + capability gate (`POST /api/v1/close/sequence/initiate` + `POST /api/v1/close/sequence/step-complete` + `GET /api/v1/close/sequence/state`)
  - [ ] Subtask 8.3: `apps/api/main.py` 4 NEW exception handlers wire (PartialCloseBlockedError + CloseSequenceAlreadyInitiatedError + CloseSequenceStepMismatchError + CloseSequenceCapabilityDeniedError)
  - [ ] Subtask 8.4: `docs/capability-matrix.md` v1.11 (EXTENSION) — CLOSE_SEQUENCE_LOCK capability 행 추가
  - [ ] Subtask 8.5: `tests/services/test_capability_matrix_drift.py` (NEW) — Capability enum ↔ capability-matrix.md cross-check 3 cases
- [ ] **Task 9: Alembic 0020 NEW + 11-1 wire 정합 검증 + RLS + 4-stage close_sequence_state** (AC: #9)
  - [ ] Subtask 9.1: `apps/api/alembic/versions/0020_fiscal_periods_close_sequence.py` (NEW migration) — `down_revision='0019_m11_reversal_ledger'` (11-1 wire tip)
  - [ ] Subtask 9.2: 11-1 wire 정합 검증 — Alembic 0019 reversal_ledger migration 호환성 (reversal_log 테이블 + RLS + unique indexes 보존)
  - [ ] Subtask 9.3: `alembic upgrade head` dry-run 검증 + CI shim 통과 (db-backed CI-only)
  - [ ] Subtask 9.4: `tests/api/test_alembic_0020_fiscal_periods.py` (NEW) — 8 cases (Task 1 Subtask 1.5와 동일)
- [ ] **Task 10: Frontend close sequence panel + step indicators + 4-stage progress UI + Playwright E2E** (AC: #2, #3, #4, #8)
  - [ ] Subtask 10.1: `apps/web/components/m11-close/CloseSequencePanel.tsx` (NEW shadcn Card + StepIndicator + progress bar) — 4-stage divisions → manufacturing → ABC → common 시각화
  - [ ] Subtask 10.2: `apps/web/components/m11-close/CloseSequenceStepCompleteButton.tsx` (NEW shadcn Button + sonner toast) — step_complete 호출 + partial close 거부 toast
  - [ ] Subtask 10.3: `apps/web/components/m11-close/CloseSequenceConfirmButton.tsx` (NEW shadcn Button + shadcn Dialog confirmation + sonner toast) — confirm_close_sequence 호출 + 4단계 검증
  - [ ] Subtask 10.4: `apps/web/lib/closing-period.ts` (EXTENSION) — `CloseSequenceState` + `CloseSequenceProgress` TS types + `partialCloseBlockedMessageKo` + `confirmCloseSequenceBlockedMessageKo` 추가
  - [ ] Subtask 10.5: `apps/web/ko-KR.json` (EXTENSION) — 7 NEW strings (`close_sequence_panel_title` + `step_complete_button_label_divisions` + `step_complete_button_label_manufacturing` + `step_complete_button_label_abc` + `step_complete_button_label_common` + `confirm_close_sequence_button_label` + `partial_close_blocked_toast_message`)
  - [ ] Subtask 10.6: `apps/web/app/(authenticated)/m2-input/period/[periodKey]/page.tsx` (EXTENSION) — CloseSequencePanel 진입점 (5-3 MonthlyInputTabs.tsx 마감 탭 진입점 동일)
  - [ ] Subtask 10.7: `apps/web/components/m11-close/__tests__/CloseSequencePanel.test.tsx` (NEW vitest) — 5 cases (4-stage progress rendering + step_complete trigger + partial close guard + confirm dispatch + ALREADY_CONFIRMED idempotent)
  - [ ] Subtask 10.8: `apps/web/components/m11-close/__tests__/m11-close-sequence.test.ts` (NEW vitest) — TS mirror parity 5 cases (Python ↔ TS validate parity + Decimal serialization + 4-stage state transitions)
  - [ ] Subtask 10.9: `e2e/m11-close-sequence.spec.ts` (NEW Playwright) — 4 scenarios (initiate → step_complete divisions → step_complete manufacturing → partial close block → step_complete common → confirm success)
- [ ] **Task 11: docs + 3중 게이트 final clean + SDR drift detector regeneration** (AC: #all)
  - [ ] Subtask 11.1: `docs/close-sequence-lock.md` (NEW) — 4-stage close sequence order + partial close guard + AD-6 INSERT 거부 + 11-1 reversal_authorization 양쪽 가드 + closing_period_service 확장 + capability matrix v1.11 + A5 forward-lock + V8 18→22 fixture matrix extension
  - [ ] Subtask 11.2: `docs/architecture-inventory.md` (EXTENSION) — M11 모듈 권한 본문 + fiscal_periods 테이블 + 4-stage close_sequence_state 추가
  - [ ] Subtask 11.3: `docs/monthly-input.md` (EXTENSION) — Story 11.2 section + close sequence panel 진입점 + 4-stage UI flow + partial close 거부 UX
  - [ ] Subtask 11.4: `docs/closing-period.md` (EXTENSION) — Story 11.2 close_sequence_state + fiscal_periods.status 차원 확장
  - [ ] Subtask 11.5: `docs/audit-actions.md` (11-1 wire EXTENSION) — `ActionClass.MONTHLY_CLOSING` 4 NEW values 추가 + closing_sequence_initiated/step_completed/blocked/confirmed wire contract
  - [ ] Subtask 11.6: `docs/conventions.md` §10 Audit Actions SSOT EXTENSION — 11-1 5 values 보존 + 11-2 4 NEW values 추가
  - [ ] Subtask 11.7: `docs/closing-guard.md` (EXTENSION) — 11-2 wire 4-stage close sequence guard + AD-6 close lock + AD-22 reversal/correction exception
  - [ ] Subtask 11.8: `tests/regression_v8/test_regression_v8_fixtures.py` (EXTENSION) — 4 NEW 골든 fixture (close_sequence_initiated + close_sequence_step_completed_partial_blocked + close_sequence_confirmed + close_sequence_reversal_blocked) — V8 18 → 22 fixture matrix extension + byte-identical CI gate
  - [ ] Subtask 11.9: `packages/cost_engine/tests/regression_v8/fixtures/close_sequence_initiated.json` (NEW) + 3 NEW 골든 fixture JSON
  - [ ] Subtask 11.10: `packages/cost_engine/tests/regression_v8/README.md` (EXTENSION) — 4 NEW 골든 fixture 명세 + byte-identical CI gate
  - [ ] Subtask 11.11: 3중 게이트 final clean — ruff scoped 0 errors / import-linter 2 KEPT 0 broken (ALLOWED_SERVICE_SUBMODULES m11_close 추가) / pytest 1,327 + ~110 = ~1,437 passed + 127 skipped + 0 failed / vitest 12 NEW + 14 carry / Playwright E2E 4 NEW scenarios
  - [ ] Subtask 11.12: SDR drift detector regeneration — MAX SDR claim 갱신 (1,454 → ~1,564, +110 NEW tests from 11-2 sweep patches + 4 NEW exception handler tests + 6 test rewrite delta)

## Dev Notes

### Project Structure Notes

- **Alignment with unified project structure**: 본 스토리는 11-1 wire (`apps/api/modules/m11_close/` populated + `packages/services/m11_close/` 3 pure kernels + `packages/services/m5_ledger/` H6 fix + `apps/api/core/audit_action.py` 6 values fill + `apps/api/core/capability.py` REVERSAL_REQUEST + `apps/api/core/cache_invalidation_publisher.py` AD-25 1-channel + `apps/api/main.py` 6 NEW exception handlers + Alembic 0019 reversal_ledger) 모두 reuse + extend. Epic 11 cj-style 3-story 분할 2번째.
- **Detected conflicts or variances**: fiscal_periods 테이블은 **greenfield** (현재 부재 — monthly_input_periods.status 만 존재). 11-1 wire는 `packages/services/m11_close/reversal_authorization.py:8/32` 코멘트에 "11-2 wire 시점에 fiscal_periods.status 추가 가드 예정" + "11-2 wire will introduce fiscal_periods.status='locked' guard" 명시 TODO marker 보유. 본 스토리 wire 후 update.
- **4-stage close_sequence_state** = divisions → manufacturing → abc → common → confirmed 1-way state machine. PRD §8.M11(a) "부문분할 → 제조 → ABC → 공동 순서 강제 + 부분 마감 불허" 명시.
- **Capability matrix v1.11**: CLOSE_SEQUENCE_LOCK 신규 (manufacturing 3종 ✅ / service-only ❌ — PRD §6.4 + §Q-I 매핑).
- **ALLOWED_SERVICE_SUBMODULES m11_close 추가** — 6-1/11-1 wire 시점에 이미 추가됨, 본 스토리는 추가 변경 불요요 (Task 11 Subtask 11.11 검증만).
- **A5 forward-lock**: ActionClass.MONTHLY_CLOSING 4 NEW values fill (ActionClass.CLOSING_PERIOD 6-1 wire 별도). 11-1 ActionClass.REVERSAL_LOG 5 values + MonthlyInputPeriodAction 1 value 보존.

### Source Tree Components to Touch

**Backend NEW (5 files)**:
1. `apps/api/alembic/versions/0020_fiscal_periods_close_sequence.py` — Alembic 0020 migration (fiscal_periods + RLS + close_sequence_state)
2. `apps/api/modules/m11_close/services/close_sequence_service.py` — close sequence service layer (4 operations + 5 typed exceptions)
3. `packages/services/m11_close/close_sequence_order.py` — close sequence order pure kernel
4. `packages/services/m11_close/close_sequence_state.py` — close sequence state + AD-6 insert allowed pure kernel
5. `packages/services/m11_close/partial_close_guard.py` — partial close guard pure kernel

**Backend NEW (3 files - tests)**:
6. `tests/services/test_close_sequence_order.py` — ~20 pure tests
7. `tests/services/test_close_sequence_state.py` — ~20 pure tests
8. `tests/services/test_partial_close_guard.py` — ~15 pure tests
9. `tests/services/test_reversal_authorization_fiscal_period_extension.py` — ~10 tests
10. `tests/api/test_close_sequence_service.py` — 6 tests
11. `tests/api/test_alembic_0020_fiscal_periods.py` — 8 tests
12. `tests/api/test_db_models_fiscal_period.py` — 6 tests
13. `tests/integration/test_fiscal_periods_rls.py` — 12 tests
14. `tests/services/test_capability_matrix_drift.py` — 3 tests

**Backend EXTENSION (10 files)**:
15. `apps/api/core/db_models.py` — `FiscalPeriod` ORM (Mapped[T] + __table_args__ mirror)
16. `apps/api/core/audit_action.py` — ActionClass.MONTHLY_CLOSING 4 NEW values fill + frozenset fill
17. `apps/api/core/capability.py` — Capability.CLOSE_SEQUENCE_LOCK 신규
18. `apps/api/main.py` — 4 NEW exception handlers wire (PartialCloseBlockedError + CloseSequenceAlreadyInitiatedError + CloseSequenceStepMismatchError + CloseSequenceCapabilityDeniedError)
19. `apps/api/modules/m11_close/handlers.py` — 3 NEW routes + capability gate
20. `apps/api/modules/m11_close/services/__init__.py` — close_sequence_service re-export
21. `apps/api/modules/m11_close/services/reversal_service.py` — execute_reversal fiscal_period_status fetch + authorize_reversal dispatch
22. `packages/services/m11_close/reversal_authorization.py` — 11-1 wire EXTENSION (period_status + fiscal_period_status 양쪽 입력)
23. `tests/services/test_audit_action_centralization.py` — ActionClass.MONTHLY_CLOSING 4 NEW values registered verification
24. `tests/integration/test_audit_action_consistency.py` — 3-way drift detector 4 NEW cases

**Frontend NEW (4 files)**:
25. `apps/web/lib/m11-close-sequence.ts` — TS mirror (validateCloseSequenceOrder + computeCloseSequenceState + checkAd6InsertAllowed + Korean SSOT constants)
26. `apps/web/lib/m11-close-sequence-parity.ts` — TS parity test (Python ↔ TS 5 cases)
27. `apps/web/components/m11-close/CloseSequencePanel.tsx` — 4-stage progress UI (shadcn Card + StepIndicator)
28. `apps/web/components/m11-close/CloseSequenceStepCompleteButton.tsx` — step_complete trigger + sonner toast
29. `apps/web/components/m11-close/CloseSequenceConfirmButton.tsx` — confirm_close_sequence trigger + shadcn Dialog + sonner toast
30. `apps/web/components/m11-close/__tests__/CloseSequencePanel.test.tsx` — vitest 5 cases
31. `apps/web/components/m11-close/__tests__/m11-close-sequence.test.ts` — vitest 5 cases
32. `e2e/m11-close-sequence.spec.ts` — Playwright 4 scenarios

**Frontend EXTENSION (4 files)**:
33. `apps/web/lib/closing-period.ts` — CloseSequenceState + CloseSequenceProgress TS types
34. `apps/web/ko-KR.json` — 7 NEW strings
35. `apps/web/app/(authenticated)/m2-input/period/[periodKey]/page.tsx` — CloseSequencePanel 진입점
36. `apps/web/components/m11-close/index.ts` (NEW) — CloseSequencePanel + CloseSequenceStepCompleteButton + CloseSequenceConfirmButton re-export

**V8 골든 fixture (5 NEW files)**:
37. `packages/cost_engine/tests/regression_v8/fixtures/close_sequence_initiated.json` (NEW)
38. `packages/cost_engine/tests/regression_v8/fixtures/close_sequence_step_completed_partial_blocked.json` (NEW)
39. `packages/cost_engine/tests/regression_v8/fixtures/close_sequence_confirmed.json` (NEW)
40. `packages/cost_engine/tests/regression_v8/fixtures/close_sequence_reversal_blocked.json` (NEW)
41. `tests/regression_v8/test_regression_v8_fixtures.py` (EXTENSION) — V8 18 → 22 fixture matrix

**Supabase RLS (1 NEW file)**:
42. `supabase/policies/0011_fiscal_periods_rls.sql` (NEW) — ENABLE + FORCE RLS + 4-policy split

**Docs (8 files)**:
43. `docs/close-sequence-lock.md` (NEW) — 4-stage close sequence order + partial close guard + AD-6 INSERT 거부 + 11-1 reversal_authorization 양쪽 가드 + closing_period_service 확장 + capability matrix v1.11 + A5 forward-lock + V8 18→22 fixture matrix extension
44. `docs/architecture-inventory.md` (EXTENSION) — M11 모듈 권한 본문 + fiscal_periods 테이블 + 4-stage close_sequence_state 추가
45. `docs/monthly-input.md` (EXTENSION) — Story 11.2 section + close sequence panel 진입점 + 4-stage UI flow + partial close 거부 UX
46. `docs/closing-period.md` (EXTENSION) — Story 11.2 close_sequence_state + fiscal_periods.status 차원 확장
47. `docs/audit-actions.md` (11-1 wire EXTENSION) — `ActionClass.MONTHLY_CLOSING` 4 NEW values 추가
48. `docs/conventions.md` §10 Audit Actions SSOT EXTENSION — 11-1 5 values + 11-2 4 NEW values 추가
49. `docs/closing-guard.md` (EXTENSION) — 11-2 wire 4-stage close sequence guard + AD-6 close lock + AD-22 reversal/correction exception
50. `docs/capability-matrix.md` v1.11 (EXTENSION) — CLOSE_SEQUENCE_LOCK 신규 capability 행 추가
51. `packages/cost_engine/tests/regression_v8/README.md` (EXTENSION) — 4 NEW 골든 fixture 명세

**Total**: ~50 NEW + EXTENSION files (backend 19 NEW + 10 EXTENSION + frontend 4 NEW + 4 EXTENSION + 4 V8 fixture + 1 RLS + 8 docs)

### Testing Standards Summary

- **3중 게이트 mandatory CI**:
  - ruff scoped 0 errors (close_sequence_service + close_sequence_order + close_sequence_state + partial_close_guard + FiscalPeriod + 11-1 reversal_authorization EXTENSION + audit_action.py EXTENSION + capability.py EXTENSION + main.py 4 NEW handlers)
  - import-linter 2 KEPT 0 broken (`cost_engine_forbidden_io` + `engine_core_to_adapters_forbidden`, ALLOWED_SERVICE_SUBMODULES m11_close 추가)
  - pytest **1,327 + ~110 = ~1,437 passed + 127 skipped + 0 failed** 목표 (1,327 = 11-1 baseline + ~110 NEW from 11-2 sweep patches + 4 NEW exception handler tests + 6 test rewrite delta + 4 NEW V8 골든 fixture tests)
- **TS tsc --noEmit** — `apps/web/lib/m11-close-sequence.ts` + EXTENSION files clean
- **vitest** — ~12 NEW (CloseSequencePanel + CloseSequenceStepCompleteButton + CloseSequenceConfirmButton + TS parity) + 14 carry from 11-1
- **Playwright E2E** — 4 NEW scenarios (initiate → step_complete divisions → step_complete manufacturing → partial close block → step_complete common → confirm success)
- **A5 drift detector** — `tests/integration/test_audit_action_consistency.py` 3-way (registry ↔ DB CHECK ↔ call sites) 4 NEW cases (initiated + step_completed + blocked + confirmed) — registry 4 NEW values ↔ DB CHECK constraint (Alembic 0020 fiscal_periods 5 CHECK + audit_logs CHECK via 5-1 wire) ↔ call sites 4 NEW (close_sequence_service.emit_audit_typed())
- **V8 byte-identical CI gate** — 4 NEW 골든 fixture (close_sequence_initiated + close_sequence_step_completed_partial_blocked + close_sequence_confirmed + close_sequence_reversal_blocked) — V8 18 → 22 fixture matrix extension
- **SDR drift detector** — MAX SDR claim 갱신 (1,454 → ~1,564, +110 NEW tests from 11-2 sweep patches + 4 NEW exception handler tests + 6 test rewrite delta + 4 NEW V8 골든 fixture tests)
- **A7 wire** (Epic 4 close-out retro A7) — Epic 4 carry (async test pattern + SDR overclaim) Epic 5 + 6-1 + 6-2 + 11-1 wire. 11-2 동일 적용 (asyncio.run wrapper + SDR drift detector regeneration).

### Critical Path Before 11-2 dev-story

```
Epic 11 11-1 done (commit b4961a6) ✅
  ↓
[Story 11.2 dev-story T1~T10 진입] — 본 스토리 spec 진입 가능
  ↓
[Story 11.2 bmad-code-review 진입] — 5-3 R2 / 6-1 R4 / 6-2 R4 / 11-1 R4 triage + carry-over + 3rd sweep 패턴
  ↓
[Story 11.3 close-sequence-lock-with-reverse spec 진입] — epics.md 11.2 + 11.3 통합
```

### Previous Story Intelligence (11-1 done)

- **11-1 baseline_commit = b4961a6** — bmad-code-review 3rd sweep done tip. 25+ PATCH sweeping applied + 4 user decisions (D1+D2+D3+D4) + 12 W-class DEFER items.
- **11-1 carry-over reuse**: M11 module authority + AD-22 reversal ledger wire + A9 fill 5 values + H6 fix + AD-25 1-channel publisher.
- **11-1 EXTENSION 파일 (Task 6 Subtask 6.1-6.4)** — `packages/services/m11_close/reversal_authorization.py` + `apps/api/modules/m11_close/services/reversal_service.py` + 11-1 6 NEW exception handlers (`LockedPeriodReversalRejectedError` fiscal_periods.status='closed' dispatch 추가) + `apps/api/core/audit_action.py` ActionClass.REVERSAL_LOG 5 values 보존.
- **11-1 carry-over deferred items** (12 W-class DEFER) — 본 스토리는 11-1 DEFER 항목 변경 없음 (모두 보존).
- **11-1 CR lesson** — EXTENSION files missing은 R4 triage + carry-over massive 패턴. 6 NEW exception handlers는 main.py wire extension 작업 시 필수 점검. 본 스토리는 4 NEW exception handlers 추가 wire (PartialCloseBlockedError + CloseSequenceAlreadyInitiatedError + CloseSequenceStepMismatchError + CloseSequenceCapabilityDeniedError).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 11.1: Close Sequence Lock (Divisions → Manufacturing → ABC → Common)] — 4단계 순서 강제 + 부분 마감 불허 + fiscal_periods.status='closed' 전이 + AD-6 INSERT 거부 (epics.md 원본 11.1 greenfield)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-6 Fiscal-period close lock] — fiscal_periods.status='closed' 후 business-data INSERT 거부 + AD-22 reversal/correction events만 허용
- [Source: _bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-22 Reversal construction and ownership] — sign-negating + corrected row INSERT + correction_group_id link + 원본 변경 없음
- [Source: _bmad-output/planning-artifacts/prd.md#PRD §F11.1 (Close sequence lock)] — 부문분할→제조→ABC→공동 순서 + 부분 마감 없음
- [Source: _bmad-output/planning-artifacts/prd.md#PRD §8.M11(a)] — 시스템은 부문분할 → 제조 → ABC → 공동 순서를 강제하고, 부분 마감을 허용하지 않는다
- [Source: _bmad-output/planning-artifacts/prd.md#PRD §6.4 (industry × engine mapping)] — 제조 부문 → 전통 개별원가 엔진 / 서비스 부문 → ABC 엔진
- [Source: _bmad-output/planning-artifacts/prd.md#PRD §Q-I (industry × engine 고정 매핑)] — 제조 ABC는 3차 로드맵
- [Source: _bmad-output/implementation-artifacts/11-1-m11-reversal-ledger.md] — 11-1 wire baseline + 4 user decisions + 25+ patches + 12 W-class DEFER
- [Source: _bmad-output/implementation-artifacts/sprint-status.yaml#11-2-close-sequence-lock] — current status backlog → ready-for-dev
- [Source: packages/services/m11_close/reversal_authorization.py:8-32] — 11-1 wire TODO marker ("fiscal_periods.status 추가 가드 예정" + "11-2 wire will introduce fiscal_periods.status='locked' guard")
- [Source: apps/api/modules/m4_inventory/services/closing_period_service.py:259] — 6-1 confirm_closing_period dispatch (11-2 wire 위에 additive)
- [Source: apps/api/core/db_models.py:418-449] — 6-1 monthly_input_periods.status state machine (open → closing → closed) — 11-2 wire fiscal_periods.status와 별도
- [Source: apps/api/alembic/versions/0012_fiscal_period_snapshots.py] — AD-16 fiscal_period_snapshots 패턴 (11-2 fiscal_periods와 별도)
- [Source: apps/api/alembic/versions/0015_inventory_ledger.py:92-110] — 11-value event_type CHECK (reversal_negating + reversal_corrected 포함) — 11-2 AD-6 INSERT 거부 후 reversal INSERT은 통과
- [Source: apps/api/alembic/versions/0019_m11_reversal_ledger.py] — 11-1 wire tip (down_revision for 0020)

## Dev Agent Record

### Agent Model Used

Claude Sonnet 5 (claude-sonnet-5)

### Debug Log References

TBD (will be populated by dev-story agent)

### Completion Notes List

TBD (will be populated by dev-story agent)

### File List

TBD (will be populated by dev-story agent)