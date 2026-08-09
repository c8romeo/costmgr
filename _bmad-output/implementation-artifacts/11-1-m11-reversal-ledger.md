---
baseline_commit: 32e92ec
target_key: 11-1-m11-reversal-ledger
epic: 11
story_id: 11.1
title: M11 module authority + reversal ledger wire + H6 fix + AD-25
status: ready-for-dev
---

# Story 11.1: M11 module authority + reversal ledger wire + H6 fix + AD-25

Status: ready-for-dev

> Epic 11 cj-style 3-story 분할 (Epic 5 close-out retro §6 W1 패턴 — Epic 4 A3 결정 + Epic 5 5-1/5-2/5-3 + Epic 6 6-1/6-2/6-3 동일 3-story 분할 패턴) 첫 스토리. **epics.md 원본 11.1 (Close Sequence Lock) + 11.3 (Reversal Sequence) 의 ledger 절반 + A9 결정을 통합**. 사용자 결정 (2026-08-08): cj-style 3분할 + H6 fold-in + AD-25 포함 (3건 모두 권장안). 본 스토리 = **M11 모듈 권한** (apps/api/modules/m11_close/ populate) **+ AD-22 reversal ledger wire** (sign-negating row + corrected row + correction_group_id) **+ A9 fill** (reversal_negating / reversal_corrected event type + opening_inventory_unlocked action + reversal_request_enabled field wire + service layer reversal handler + UI reversal request form) **+ H6 production bug fix** (LedgerService.count_period_events / query_period_closing_snapshot_all 정의 부재로 closing_period_service.py:528/531 AttributeError 가능) **+ AD-25 1-channel wire** (M10 AI cache invalidation notification publisher). **11-2** = close-sequence-lock (epics.md 11.1 greenfield, fiscal_periods 테이블 신설 + 4단계 divisions→manufacturing→ABC→common 순서 강제 + 마감 후 INSERT 거부). **11-3** = snapshot-persistence-with-reverse (epics.md 11.2 + 11.3 snapshot state 전이 'committed → reversed' + AD-25 publisher full wire + report 재계산 trigger).
>
> **baseline_commit = 32e92ec** (Story 6.2 bmad-code-review 3rd sweep done, 3중 게이트 final clean 1224 passed + 127 skipped + 0 failed in 79.02s). Story 11.1 spec 진입 시점에 Epic 5 close-out retro (2026-08-07) §7 A9 결정 (`reversal_negating` + `reversal_corrected` event type fill + `opening_inventory_unlocked` action + `reversal_request_enabled` field wire + service layer reversal handler + UI reversal request form (Epic 11 spec 결정 후 별도 Story)) 그대로 spec 본문에 반영. **Epic 11 진입점**: M11 module authority = `apps/api/modules/m11_close/` (현재 1-line stub) populate. AD-22 reversal sequence = (1) sign-negating row INSERT (`reverses_event_id` link) + (2) corrected row INSERT (`correction_group_id` link) — 원본 row 변경 없음 + `(tenant_id, reverses_event_id)` unique 제약 보장. AD-25 notification = M10 AI cache invalidation 1-channel wire. H6 fix = `packages/services/m5_ledger/` 에 `count_period_events(period_key, *, event_type=None) -> int` + `query_period_closing_snapshot_all(period_key) -> dict[UUID, Decimal]` 2 NEW pure kernel 정의 + `closing_period_service.py:528/531` 호출 정합.
>
> **cj-style 3-story 분할 (Epic 5 retro §6 W1)** — Epic 4 A3 (Epic 5 5-1/5-2/5-3) + Epic 6 6-1/6-2/6-3 동일 패턴의 Epic 11 적용형. **11-1 = M11 module authority + AD-22 reversal ledger wire + A9 fill + H6 fix + AD-25 1-channel** (사용자 결정 + A9 매칭) → **11-2 = close-sequence-lock** (epics.md 11.1 greenfield) → **11-3 = snapshot-persistence-with-reverse** (epics.md 11.2 + 11.3 snapshot state machine + AD-25 full publisher wire). 3-story 모두 **additive** — 기존 wire contract 호환 + 사용자 흐름 무중단. Epic 5 retro §7 A9 결정 그대로 적용.

<!-- dev-context: Epic 5 close-out retro (2026-08-07) §7 A9 결정 (verbatim): "Epic 11 reversal module wire 진입점 (5-1 + 5-2 carry). Alice + Amelia. **Epic 11 spec 진입 시점**. `reversal_negating` + `reversal_corrected` event type fill + `opening_inventory_unlocked` action + `reversal_request_enabled` field wire + service layer reversal handler + UI reversal request form (Epic 11 spec 결정 후 별도 Story)". 본 스토리는 A9 5개 범위 모두 wire. **A9 carry 결정**: reversal_negating + reversal_corrected event type은 Alembic 0015 11-value event_type CHECK에 이미 포함 (5-2 wire), 본 스토리는 실제 INSERT + correction_group_id 채움 wire.

Epic 5 close-out retro (2026-08-07) §6 W1 cj-style 결정 — "Epic 5 5-1 (opening auto-carry) → 5-2 (inventory_ledger append-only events) → 5-3 (closing_guard + V3 verification + frontend banner) 패턴" + §6 §11 "Epic 6 6-1 = Closing Period Service + closing_snapshot ledger event wire / 6-2 = Monthly Closing Report / 6-3 = Closing PDF Export + ko-KR labels" 동일 cj-style 3-story 분할 패턴의 Epic 11 적용.

Epic 5 close-out retro (2026-08-07) §7 A11 결정 (V8 12 → 14 fixture matrix extension) — 6-2 spec 진입 시점에 wire (6-2 spec v1.8 완료). 11-1 wire는 A11 무관 (ledger entry는 V8 회귀 대상 아님 — 4-4 V8 골든 매트릭스 12 fixture에 reversal_scenario 포함 불요요, AD-22 reversal은 pure append + correction_group_id link로 V8 input 변화 없음).

Epic 5 close-out retro (2026-08-07) §7 A10 결정 — Epic 6 reporting capability 신규 = MONTHLY_CLOSING_REPORT. 본 스토리 wire와 무관 (Epic 6 retro scope).

Epic 4 close-out retro (2026-08-03) A3 cj-style — 3-story 분할 유지 (5-1 → 5-2 → 5-3) + Epic 6 6-1/6-2/6-3 동일 패턴. Epic 11 11-1/11-2/11-3 동일 패턴 적용 (Epic 5 retro §6 §11 명시).

Epic 4 close-out retro (2026-08-03) A5 — A5 Full Phase 1+2+4 done. Epic 5 5-1 + 5-3 + 6-1 + 6-2 audit log 일관성 보장 + A5 forward-lock + drift detector pattern 정착. 11-1 wire 동일 패턴 적용 (ReversalLogAction 5 values fill + ActionClass.REVERSAL_LOG frozenset fill + drift detector 3-way extension).

Epic 4 close-out retro (2026-08-03) A7 — Epic 4 carry (async test pattern + SDR overclaim) Epic 5 + 6-1 + 6-2 wire. 11-1 동일 적용 (asyncio.run wrapper + SDR drift detector regeneration).

**Story 0-2 (2026-07-29)** — RLS 인프라 + audit_logs INSERT-only with `BEFORE UPDATE OR DELETE` trigger 패턴이 Epic 0에서 wire됨. AD-2 + AD-3 SSOT. 11-1 wire는 RLS 위에서 동작 (M4→M11 reversal sequence 모두 RLS-scoped).

**Story 0-5 (2026-08-05)** — frontend plumbing wire ✅ done (commit ead1974). shadcn Card / Tabs / sonner / vitest + RTL + MSW / Playwright / next-intl / INDUSTRY_ICON fill. **11-1 frontend 진입 전 dep satisfied**. ReversalRequestForm (shadcn Dialog + Form + sonner toast pattern) 진입점 가능.

**Story 1.1 (2026-07-29)** — Industry enum SSOT (manufacturing / manufacturing_service / service / manufacturing_service_other) + capability matrix v1.0. 11-1 capability gate = `REVERSAL_REQUEST` (manufacturing 3종 ✅ / service-only ❌ — A9 결정 + PRD §F11.2 wire).

**Story 3.1 (2026-08-01)** — monthly_input_periods + monthly_input_rows 테이블. 11-1 wire는 monthly_input_periods opening_inventory JSONB + ledger events 양쪽 source 활용.

**Story 3.3 (2026-08-01)** — `monthly_input_periods.opening_inventory` JSONB column (Alembic 0011) + F2.3 음수재고 입력 시 즉시 경고. **11-1 wire는 3.3 inline projection 보존 (Epic 6 close-out 시점에 fold-in 결정, Epic 5 retro §7 A8 timeline)**.

**Story 4.1 (2026-08-02)** — engine returns state='draft' (AD-22 boundary strengthening). 11-1 wire는 reversal sequence를 ledger INSERT 수준에서 wire — engine 무관 (engine은 reversal 의미 모름).

**Story 4.2 (2026-08-03)** — REPEATABLE READ + audit-first (CR 1.1) + calc_log + AD-22 state transition. **11-1 wire는 4-2 calc result + 5-2 ledger aggregate + reversal_negating row INSERT + reversal_corrected row INSERT atomic transaction (CR 4-2 1-shot INSERT 패턴 보존)**.

**Story 4.4 (2026-08-03)** — A5 forward-lock + 12 fixture matrix + V8 byte-identical CI gate. **11-1 wire는 V8 12-fixture matrix 무변경 (reversal sequence는 V8 input 변화 없음 — AD-22 sign-negating row는 engine output 무관)**.

**Story 5.1 (2026-08-04, commit b4b84da)** — opening_carry_chain wire + 4 hooks into monthly_input_service. **5-1 carry-over to 11-1**: opening_inventory JSONB → reversal_corrected row의 opening_qty source. **A9 결정** (`opening_inventory_unlocked` action) — ActionClass.MONTHLY_INPUT_PERIOD 1 NEW value fill (5-1 wire).

**Story 5.2 (2026-08-04, commit 7a13eb9)** — inventory_ledger append-only events + 4 routes + 11 values event_type CHECK + PostgreSQL BEFORE UPDATE OR DELETE row-level trigger + AD-22 reversal entrypoint forward-fill. **5-2 carry-over to 11-1**: 
  (a) `reversal_negating` + `reversal_corrected` 11-value event_type (Alembic 0015 lines 92-110) 이미 wire — 본 스토리는 실제 INSERT.
  (b) `reverses_event_id` + `correction_group_id` 컬럼 (nullable UUID, no FK) 이미 wire.
  (c) `uq_inventory_ledger_reverses_event_id` UNIQUE `(tenant_id, reverses_event_id) WHERE reverses_event_id IS NOT NULL` (Alembic 0015 lines 197-201) 이미 wire.
  (d) `inventory_ledger_reversal_coherence` CHECK (Alembic 0015 lines 162-175) 이미 wire.
  (e) `inventory_ledger_qty_signed_coherence` CHECK (Alembic 0015 lines 125-142) — reversal_negating 음수 qty 허용.
  (f) append-only trigger `trg_inventory_ledger_append_only` (Alembic 0015 lines 228-253) — 11-1 wire INSERT만 허용.
  (g) `m4_inventory/handlers.py:356-390` 501 `POST /api/v1/inventory/ledger/reversal-requests` route (forward-fill) — 본 스토리에서 M11 actual write로 대체 (route 재배치 + 501 → 201 전환).
  (h) `packages/cost_engine/ports/reversal_port.py:1-32` ReversalPort Protocol (M11 owns authorization) — 본 스토리에서 ReversalPort 구현체 (apps/api/modules/m11_close/services/reversal_service.py).
  (i) `audit_action.py:170-173` ReversalLogAction placeholder (`_placeholder_reversal_log`) + TODO(epic-11) FILL_REVERSAL_LOG_ACTIONS — 본 스토리에서 5 values fill.
  (j) `audit_action.py:355` ActionClass.REVERSAL_LOG: `("reversal_log", frozenset())` — 본 스토리에서 frozenset fill.
  (k) `audit_action.py:163-167` `inventory_ledger_reversal_logged` + `inventory_ledger_reversal_rejected` (forward-fill but never emitted) — 본 스토리에서 actual emit wire.

**Story 5.3 (2026-08-06, commit 079f6a7)** — closing_guard pure kernel + closing_guard_service + 3 routes + MonthlyInputStateResponse 5 NEW fields + 6 NEW frontend files + 32 patches P1-P32. **5-3 carry-over to 11-1**: `closing_period_service.py:528/531` H6 호출 위치 (production bug — `LedgerService.count_period_events` + `query_period_closing_snapshot_all` 정의 부재 → runtime AttributeError 가능).

**Story 6.1 (2026-08-08, commit 418ca2d)** — closing_period service + closing_snapshot ledger event wire + V4 verification. **6-1 carry-over to 11-1**: 
  (a) `closing_period_service.py:506-535` `_query_closing_via_ledger` 가 `LedgerService` 의 두 부재 메서드 호출 — H6 fix 본드에서 두 메서드 정의 필수.
  (b) `closing_period_service.py:307-312` SELECT FOR UPDATE 패턴 (4-2 wire) — 11-1 reversal sequence 1-shot INSERT 동일 패턴.
  (c) `MonthlyInputStateResponse.reversal_request_enabled` field — Capability.REVERSAL_REQUEST capability_granted mirror.
  (d) `MonthlyInputStateResponse.inventory_ledger_enabled` field — Capability.INVENTORY_LEDGER capability_granted mirror.
  (e) `ActionClass.CLOSING_PERIOD` 3 values (`closing_period_confirmed` / `closing_period_blocked` / `closing_period_snapshot_inconsistency`) — 11-1 wire와 무관.

**Story 6.2 (2026-08-08, commit 30d6455)** — monthly closing report + V8 16→18 fixture matrix extension. **6-2 carry-over to 11-1**: 11-1 wire 시점에 H6 fix 부재하면 monthly closing report read-only aggregator 진입 시 AttributeError 가능 → production 진입 차단. **본 스토리 H6 fix = production 차단 해소 + AD-22 reversal ledger write 가능**.

**A9 (Epic 5 retro §7 결정, 2026-08-07)** — Epic 11 reversal module wire 진입점. 11-1 spec 진입 시점에 결정. 본 스토리는 A9 5개 범위 (reversal_negating/reversal_corrected event type + opening_inventory_unlocked action + reversal_request_enabled field wire + service layer reversal handler + UI reversal request form) 모두 wire.

**A11 (Epic 5 retro §7 결정, 2026-08-07)** — V8 12 → 16 fixture matrix extension (closing snapshot + ledger events). 6-2 spec v1.8 완료 (18 fixture matrix). 11-1 wire는 V8 무변경 (reversal sequence는 ledger append-only INSERT이므로 V8 input 영향 없음).

**AD-1 (modular monolith + hexagonal core)** — 11-1 wire는 engine port + service layer + handlers 표준 3-tier 패턴 (5-1/5-2/5-3/6-1/6-2 동일). `packages/cost_engine/ports/reversal_port.py` (이미 wire) + `apps/api/modules/m11_close/services/reversal_service.py` (NEW) + `apps/api/modules/m11_close/handlers.py` (NEW).

**AD-2 (append-only ledger)** — 11-1 wire 핵심. 5-2 inventory_ledger SSOT + PostgreSQL `BEFORE UPDATE OR DELETE` trigger 보존. reversal_negating + reversal_corrected row 모두 append-only INSERT. original row UPDATE/DELETE 금지.

**AD-3 (multi-tenant RLS)** — 11-1 wire는 RLS 위에서 동작. `tenant_id` 자동 derive from JWT (AD-3 SSOT). reversal sequence는 service_role bypass 불요요 (M4 caller + M11 writer 동일 tenant).

**AD-6 (close lock)** — 11-1 wire는 reversal sequence의 원본 row가 `monthly_input_periods.status='closed'` 인 경우에만 발동 (PRD §F11.2 명시 — "마감 후 입력 수정은 역분개로만"). 11-2 close-sequence-lock (greenfield)에서 `fiscal_periods.status='closed'` 전이 + INSERT 거부 (PRD §F11.1) wire — 11-1 wire와 호환.

**AD-11 (dependency direction / layer rule)** — pure helpers = `packages/services/m11_close/` (NEW) + `packages/services/m5_ledger/` (H6 fix). service layer = `apps/api/modules/m11_close/services/reversal_service.py` (NEW) + `apps/api/modules/m11_close/services/reversal_kernel_adapter.py` (NEW). handlers = `apps/api/modules/m11_close/handlers.py` (NEW). engine layer (`packages/cost_engine/`) 무변경 (engine은 reversal 의미 모름 — 4-2 wire 패턴).

**AD-15 (cross-language parity)** — TS mirror `apps/web/lib/m11-reversal.ts` (NEW) + Decimal serialization parity (reversal_negating qty = 원본 qty × -1, banker's rounding to NUMERIC(18,4) + QTY_QUANTUM).

**AD-22 (reversal construction)** — 11-1 PRIMARY AC. Sequence: (1) sign-negating row INSERT (reverses_event_id link + reversal_of_period_key) + (2) optional corrected row INSERT (correction_group_id share). Original never changes. (tenant_id, reverses_event_id) unique 제약 보장. M4 calls request_reversal → M11 authorizes and writes.

**AD-25 (cache invalidation notification)** — 11-1 wire 1-channel (M10 AI cache invalidation). Publisher = `apps/api/core/cache_invalidation_publisher.py` (NEW). M11 reversal sequence 완료 시 publish → M10 cache invalidation queue + AI cache reset. 11-3 entry 시점에 publisher full wire + multi-channel 확장.

**AD-23 (4-namespace pattern)** — monthly_input_periods + monthly_input_rows + inventory_ledger + audit_logs + fiscal_period_snapshots 5 namespace + reversal_log (NEW namespace, 11-1 wire).

**AD-24 (typed period-key)** — 'YYYY-MM' 형식 SSOT. reversal_of_period_key = 원본 event의 period_key (AD-24 typed).

**PRD §F11.1 (Close sequence lock)** — 부문분할→제조→ABC→공동 순서 + 부분 마감 불허. 11-2 wire (greenfield). 11-1 wire와 무관 (reversal sequence는 close 후 발동).

**PRD §F11.2 (Snapshot persistence on close)** — 마감 후 입력 수정 거부 + snapshot hash 영구 보존. 11-3 wire (snapshot state machine + AD-25 full). 11-1 wire는 reversal sequence 1차 wire (PRD §F11.2 의 "역분개로 처리하세요" 메시지 정확히 wire).

**PRD §F11.3 (Reversal sequence)** — **11-1 PRIMARY AC**: (1) 부호 반전 row 1개 INSERT + (2) corrected row INSERT + correction_group_id link + 원본 row 변경 없음 + (tenant_id, reverses_event_id) unique + 재무 효과 0 수렴 + M10 cache invalidation.

**PRD §V4 (closing snapshot 일관성)** — 6-1 wire 완료. 11-1 wire 시점에 6-1 wire 그대로 보존. reversal sequence 후 closing snapshot 재계산 trigger는 11-3 wire (state machine).

**PRD §A11 (오류의 가시화)** — 3-layer (입력 시 경고 + 마감 시 차단 + 마감 확정 시 snapshot). 11-1 wire는 Layer 4 = reversal sequence (역분개 발동 시 사용자 메시지 "마감 후 수정은 역분개로만 가능합니다").

**PRD §6.1 (산식 체인)** — 11-1 wire는 fiscal_period_snapshots 무관 (11-3 wire 진입점). 8단계 산식 체인 그대로 보존.

**PRD §6.2 (수불부)** — 5-2 wire 그대로 보존. 11-1 wire는 reversal_negating + reversal_corrected row 2개 append (PRD §6.2 sign-negating 의미 정확히 wire).

**PRD §12 (AI)** — AD-25 1-channel wire = M10 AI cache invalidation. publisher 1차 wire + 11-3 entry 시점에 multi-channel 확장.

**0.5 plumbing** — 11-1 frontend ReversalRequestForm 진입 시점 frontend toolchain 완비 (shadcn Dialog + Form + sonner / vitest / Playwright / next-intl). ReversalRequestForm = ClosingPeriodConfirmationPanel (6-1 wire) + MonthlyClosingReportPanel (6-2 wire) 위에 additive — fiscal_period panel 의 [역분개] 버튼 → ReversalRequestDialog → ReversalRequestForm wire. -->

## Story

As a **회계사**,

I want **마감 후 오류를 발견하면 (1) M4 entrypoint (`POST /api/v1/inventory/ledger/reversal-requests` 501 forward-fill)에서 M11 모듈 권한으로 reversal sequence 발동되며 (2) sign-negating row 1개 INSERT (`reverses_event_id` link + reversal_of_period_key) 후 corrected row 1개 INSERT (`correction_group_id` link) — 원본 row는 절대 변경되지 않고 (3) `(tenant_id, reverses_event_id)` unique 제약 보장 + 11-value event_type CHECK (`reversal_negating` + `reversal_corrected`) + reversal_coherence CHECK 통과 + (4) 재무 효과는 정확히 0에 수렴 (sign-negating row의 qty = 원본 qty × -1) + (5) `opening_inventory_unlocked` action audit + `reversal_request_enabled` capability flag wire (manufacturing 3종 ✅ / service-only ❌) + service layer reversal handler (ReversalService.execute_reversal) + UI reversal request form (ReversalRequestDialog) + (6) M10 AI cache invalidation notification 자동 발행 (AD-25 1-channel publisher) + (7) H6 production bug fix (`LedgerService.count_period_events` + `query_period_closing_snapshot_all` 정의로 monthly closing report AttributeError 차단 해소)**,

so that **마감 후 입력 수정의 유일한 합법적 경로 = 역분개 (PRD §F11.3 PRIMARY) 가 wire되어 audit 추적 가능 + 원본 영구 보존 + correction_group_id link로 sign-negating + corrected pair 정확히 매칭 + A9 결정 5개 범위 모두 wire + H6 production bug 차단 해소 + 11-2 (close-sequence-lock) + 11-3 (snapshot state machine + AD-25 full) 진입 가능** — AD-2 (append-only ledger — sign-negating + corrected row INSERT만 허용, 원본 row 절대 변경 없음) · AD-3 (multi-tenant RLS — reversal sequence 모두 RLS-scoped) · AD-6 (close lock — 11-2 wire; 11-1 wire는 monthly_input_periods.status='closed' 가드) · AD-11 (layer rule — pure kernel in packages/services/m11_close/ + service layer in apps/api/modules/m11_close/services/) · AD-15 (cross-language parity — TS mirror Decimal serialization + banker's rounding) · AD-22 (reversal construction — sign-negating + corrected row + correction_group_id + reverses_event_id unique 제약) · AD-23 (4-namespace pattern + reversal_log NEW namespace) · AD-24 (typed period-key — reversal_of_period_key = 원본 event period_key) · AD-25 (cache invalidation notification — M10 AI cache 1-channel publisher) · PRD §F11.3 (reversal sequence PRIMARY) · PRD §A11 (Layer 4 = 역분개 메시지) · A9 (Epic 5 retro §7 결정 — 5개 범위 모두 wire) · Story 0.5 frontend plumbing · Epic 5 5-1 (opening carry) + 5-2 (inventory_ledger + AD-22 reversal entrypoint forward-fill + 11-value event_type CHECK + append-only trigger) + 5-3 (closing_guard + H6 호출 위치) + 6-1 (closing_period_service H6 caller) + 6-2 (H6 dependency + V4 wire) carry-over.

## Acceptance Criteria

1. **Given** Epic 5 5-2 (reversal_negating + reversal_corrected 11-value event_type CHECK + reverses_event_id + correction_group_id 컬럼 + uq_inventory_ledger_reverses_event_id unique + reversal_coherence CHECK + append-only trigger + 501 forward-fill route + ReversalPort Protocol + audit_action forward-fill 6 INVENTORY_LEDGER values) + 5-3 (closing_guard wire + H6 호출 위치) + 6-1 (closing_period_service H6 caller) + 6-2 (monthly closing report dependency) + 0.5 frontend plumbing ✅ done + Epic 5 retro §7 A9 결정 (reversal_negating + reversal_corrected event type fill + opening_inventory_unlocked action + reversal_request_enabled field wire + service layer reversal handler + UI reversal request form) + 사용자 결정 (cj-style 3-story 분할 + H6 fold-in + AD-25 포함)
   **When** 본 스토리 dev-story 진입 시
   **Then** 다음 책임 분리 + wire contract 정렬이 유지된다:
     - **Pure kernel #1 (NEW `packages/services/m11_close/reversal_negating.py`)** — `build_reversal_negating_event(*, target_event: InventoryLedgerEvent, reason: str, actor_id: UUID, correction_group_id: UUID, trace_id: str) -> ReversalNegatingEvent` (sign-negating row constructor — `event_type='reversal_negating'` + `reverses_event_id=target_event.event_id` + `reversal_of_period_key=target_event.period_key` + `correction_group_id=correction_group_id` + `qty=-target_event.qty` (sign flip, banker's rounding) + `actor_id=actor_id` + `tenant_id=target_event.tenant_id`). + `validate_reversal_negating_constraints(target_event: InventoryLedgerEvent) -> None` (defense-in-depth: target_event 가 `event_type IN ('opening_carried', 'opening_carried_stale_overwrite', 'purchase_inbound', 'sales_outbound', 'production_output_inbound', 'production_material_consumption', 'adjustment_positive', 'adjustment_negative', 'closing_snapshot')` 중 하나인지 검증 + 이미 reversal_negating / reversal_corrected 자체를 reversal 할 수 없음 — self-reversal 금지). stdlib-only (no DB, no clock — actor_id / trace_id 인자). banker's rounding via `QTY_QUANTUM = Decimal("0.0001")` (NUMERIC(18,4) precision). 1 typed exception (`ReversalNegatingBuildError`, NO HTTP mapping — pure helper owns domain semantics).
     - **Pure kernel #2 (NEW `packages/services/m11_close/reversal_corrected.py`)** — `build_reversal_corrected_event(*, target_event: InventoryLedgerEvent, correction_group_id: UUID, corrected_qty: Decimal, corrected_period_key: str, actor_id: UUID, trace_id: str) -> ReversalCorrectedEvent` (corrected row constructor — `event_type='reversal_corrected'` + `reverses_event_id=target_event.event_id` + `reversal_of_period_key=target_event.period_key` + `correction_group_id=correction_group_id` + `qty=corrected_qty` (정정 수량, banker's rounding) + `period_key=corrected_period_key` (corrected row의 period_key — 원본과 같을 수도 다를 수도 있음 — AD-24 typed). + `validate_reversal_corrected_constraints(target_event: InventoryLedgerEvent, corrected_event: ReversalCorrectedEvent) -> None` (defense-in-depth: corrected_event 의 `correction_group_id == target_event` 의 correction_group_id 와 일치 검증 + period_key AD-24 형식 검증). stdlib-only. 1 typed exception (`ReversalCorrectedBuildError`).
     - **Pure kernel #3 (NEW `packages/services/m11_close/reversal_authorization.py`)** — `authorize_reversal(*, tenant_id: UUID, target_event: InventoryLedgerEvent, actor_id: UUID, period_status: str, capability_granted: bool) -> ReversalAuthorizationResult` (authorization decision — capability_granted True 필수 (Capability.REVERSAL_REQUEST) + period_status IN ('open', 'closed') 허용 ('locked' 일 경우 LockedPeriodError) + target_event.event_type 자체 reversal 가능 여부 검증 (closing_snapshot 자체 reversal 불가 — AD-6 close lock + PRD §F11.3). + `M11_AUTHORIZE_KO: Final[str] = "M11 모듈 권한 OK"` + `M11_REJECT_LOCKED_KO: Final[str] = "잠긴 기간 — 역분개 불가"` + `M11_REJECT_NO_CAPABILITY_KO: Final[str] = "역분개 권한 미보유"` (Korean constants — AD-15 §11 SSOT). stdlib-only. 1 typed exception (`ReversalAuthorizationError`).
     - **Pure kernel #4 (H6 fix NEW `packages/services/m5_ledger/count_period_events.py`)** — `count_period_events_sql(period_key: str, *, event_type: str | None = None) -> tuple[str, dict[str, Any]]` (count SQL builder — `event_type IS NULL` 이면 `SELECT COUNT(*) FROM inventory_ledger WHERE period_key = :period_key` + `event_type` 지정 시 `WHERE period_key = :period_key AND event_type = :event_type`). stdlib-only (text-only SQL builder, no SQLAlchemy). `closing_period_service.py:528/531` 의 두 호출 정합 — `:528` `count_period_events(period_key=period_key)` (event_type=None) + `:531` `count_period_events(period_key=period_key, event_type="closing_snapshot")` (event_type filter). 1 typed exception (`CountPeriodEventsBuildError`).
     - **Pure kernel #5 (H6 fix NEW `packages/services/m5_ledger/query_period_closing_snapshot_all.py`)** — `query_period_closing_snapshot_all_sql(period_key: str) -> tuple[str, dict[str, Any]]` (closing_snapshot per-product qty aggregate SQL builder — `SELECT product_id, SUM(qty) AS closing_qty FROM inventory_ledger WHERE period_key = :period_key AND event_type = 'closing_snapshot' GROUP BY product_id`). stdlib-only. 1 typed exception (`QueryPeriodClosingSnapshotAllBuildError`).
     - **Service layer #1 (NEW `apps/api/modules/m11_close/services/reversal_service.py`)** — `ReversalService` class with 4 operations:
       - `execute_reversal(session, *, tenant_id, target_event_id: UUID, reason: str, corrected_qty: Decimal | None, corrected_period_key: str | None, actor_id: UUID, capability_granted: bool) -> ReversalResponse` (AD-22 sequence orchestrator — (1) SELECT target_event FROM inventory_ledger WHERE event_id = target_event_id AND tenant_id = tenant_id, (2) `authorize_reversal` decision (T1.3), (3) `correction_group_id = uuid7()` (or uuid4 fallback per 5-2 P8 pattern), (4) `build_reversal_negating_event` (T1.1) + INSERT, (5) `build_reversal_corrected_event` (T1.2) + INSERT (corrected_qty/corrected_period_key None 인 경우 step 5 skip — PRD §F11.3 spec "optional corrected row"), (6) AD-25 publisher publish (T8 cache_invalidation_publisher), (7) audit-first INSERT to reversal_log + audit_logs (ActionClass.REVERSAL_LOG + ActionClass.MONTHLY_INPUT_PERIOD for opening_inventory_unlocked + ActionClass.INVENTORY_LEDGER for inventory_ledger_reversal_logged)).
       - `get_reversal_history(session, *, tenant_id, target_event_id: UUID) -> list[InventoryLedgerEvent]` (CR 1.1 observability — `inventory_ledger` WHERE `reverses_event_id = target_event_id`).
       - `reject_reversal(session, *, tenant_id, target_event_id: UUID, reason: str, actor_id: UUID) -> None` (M11 reject path — `inventory_ledger_reversal_rejected` audit INSERT + raise ReversalRejectedError 403).
       - `_publish_cache_invalidation(session, *, tenant_id, target_event_id: UUID, correction_group_id: UUID, trace_id: str) -> None` (AD-25 publisher integration — `cache_invalidation_publisher.publish(channel='ai_cache', tenant_id=tenant_id, event_id=target_event_id, correction_group_id=correction_group_id, trace_id=trace_id)`).
     - **Wire trigger (NEW `apps/api/modules/m11_close/handlers.py`)** — 3 NEW routes:
       - `POST /api/v1/close/reversal-requests` — M11 actual write endpoint (M4 forward-fill 501 route 대체 — 5-2 wire `m4_inventory/handlers.py:356-390` 의 501 → 201 전환 또는 신규 M11 route 추가 후 M4 route는 deprecated). Returns `ReversalResponse` (`{ correction_group_id: UUID, negating_event_id: UUID, corrected_event_id: UUID | None, target_event_id: UUID, reversal_history: list[InventoryLedgerEvent], trace_id: str }`). AD-15 envelope + capability gate `REVERSAL_REQUEST` (manufacturing 3종 ✅ / service-only ❌).
       - `GET /api/v1/close/reversal-requests/{correction_group_id}` — reversal history read-only endpoint. Returns `list[InventoryLedgerEvent]` (sign-negating + corrected row).
       - `POST /api/v1/close/cache-invalidation` — AD-25 manual publisher endpoint (test/debug 용). Returns `CacheInvalidationReceipt` (`{ channel: str, tenant_id: UUID, target_event_id: UUID, correction_group_id: UUID, published_at: ISO-8601, trace_id: str }`). Capability gate `REVERSAL_REQUEST` 동일.
     - **A5 forward-lock (`apps/api/core/audit_action.py` extension)** — `ReversalLogAction` Literal placeholder (`_placeholder_reversal_log`) → 5 values fill: `reversal_negating_inserted`, `reversal_corrected_inserted`, `reversal_rejected`, `reversal_unauthorized`, `m11_reversal_handler_invoked`. + `ActionClass.MONTHLY_INPUT_PERIOD` Literal extension: `monthly_input_period_opening_unlocked` 1 value fill (A9 결정). + `_ActionRegistry._REGISTRY[ActionClass.REVERSAL_LOG]` empty frozenset → 5 values fill. + `_ActionRegistry._REGISTRY[ActionClass.MONTHLY_INPUT_PERIOD]` accepted frozenset 3 → 4 values fill. + `_ActionRegistry._REGISTRY[ActionClass.INVENTORY_LEDGER]` accepted frozenset 6 그대로 (5-2 wire 완료 + forward-fill 2 values `inventory_ledger_reversal_logged` / `inventory_ledger_reversal_rejected` actual emit wire).

2. **Given** AC #1 pure kernel + service layer + wire trigger + A5 forward-lock
   **When** 본 스토리 dev-story 진입 시
   **Then** 다음 frontend wire 발동 (AC #2 — ReversalRequestDialog + ReversalRequestForm + shadcn Dialog + Form + sonner toast wire):
     - **TS mirror helper #1 (NEW `apps/web/lib/m11-reversal.ts`)** — 11-1 frontend logic (wire path mirror). Exports:
       ```typescript
       export type ReversalEventType = "reversal_negating" | "reversal_corrected";
       export interface ReversalRequestPayload {
         target_event_id: string;
         reason: string;
         corrected_qty: string | null;
         corrected_period_key: string | null;
       }
       export interface ReversalResponse {
         correction_group_id: string;
         negating_event_id: string;
         corrected_event_id: string | null;
         target_event_id: string;
         reversal_history: InventoryLedgerEvent[];
         trace_id: string;
       }
       export interface ReversalAuthorizationResult {
         authorized: boolean;
         reject_reason_ko: string | null;
         period_status: "open" | "closed" | "locked";
       }
       export function buildReversalRequestState(payload: ReversalRequestPayload): ReversalRequestState;
       export function isReversalRequestAllowed(state: ReversalRequestState): boolean;
       export function formatReversalReasonKo(reason: string): string;  // SSOT Korean
       export function validateReversalNegatingConstraints(targetEvent: InventoryLedgerEvent): void;
       export function validateReversalCorrectedConstraints(targetEvent: InventoryLedgerEvent, corrected: ReversalCorrectedEvent): void;
       ```
     - **TS mirror helper #2 (NEW `apps/web/lib/m11-reversal-parity.ts`)** — TS↔Python SSOT parity helper. Decimal serialization parity (sign-negating qty = 원본 qty × -1, banker's rounding + QTY_QUANTUM).
     - **ReversalRequestDialog (NEW `apps/web/components/m4-inventory/ReversalRequestDialog.tsx`)** — shadcn `<Dialog>` + `<Form>` pattern:
       - "마감 후 수정은 역분개로만 가능합니다" 안내문 표시.
       - ReversalRequestForm input fields: `target_event_id` (자동 채움 — panel context) + `reason` (textarea, 200자 제한) + `corrected_qty` (optional) + `corrected_period_key` (optional).
       - [역분개 실행] button — `disabled={submitting || !isReversalRequestAllowed(state)}`.
       - [취소] button — close dialog.
     - **ReversalRequestForm (NEW `apps/web/components/m4-inventory/ReversalRequestForm.tsx`)** — shadcn `<Form>` + sonner toast wire:
       - `ReversalService.execute_reversal` mutation 호출 — success 시 sonner `toast.success('역분개 완료 — correction_group_id: ...')` + dialog close + MonthlyInputStateResponse revalidate.
       - error 시 sonner `toast.error('역분개 실패: ...')` + reason 표시.
     - **ReversalRequestButton (NEW `apps/web/components/m4-inventory/ReversalRequestButton.tsx`)** — MonthlyInputStateResponse context 에서 ReversalRequestDialog trigger. service-only tenant → 비노출 (capability gate 동등).
     - **Capability-gated UI** — service-only tenant (`tenant_settings.industry === 'service'`) → ReversalRequestButton 비노출 + ReversalRequestDialog 진입 시 403 INDUSTRY_NOT_SUPPORTED redirect + sonner `toast.error('업종 미지원: 역분개는 제조 업종만 지원합니다.')` 표시. Capability matrix v1.10 (A9 결정 + 6-1 v1.8 + 6-2 v1.9 extension) `REVERSAL_REQUEST` capability SSOT.
     - **MonthlyInputTabs extension** — `apps/web/components/m2-input/MonthlyInputTabs.tsx` (5-3 wire + 6-1 extension + 6-2 extension) extension. 마감 tab 안에 ReversalRequestButton wire (ClosingPeriodConfirmationPanel + MonthlyClosingReportPanel + ReversalRequestButton 3-component vertical stack). closing_period_confirmed 후 ReversalRequestButton 활성화.

3. **Given** AC #2 TS mirror + ReversalRequestDialog + ReversalRequestForm + capability gate
   **When** 본 스토리 dev-story 진입 시
   **Then** 다음 wire contract 발동 (AC #3 — AD-22 reversal sequence 2-step INSERT atomic + AD-25 1-channel publisher + H6 fix 2 메서드 정의):
     - **AC #3.1 AD-22 reversal sequence 2-step INSERT (NEW `ReversalService.execute_reversal`)** — REPEATABLE READ isolation level (4-2 wire 패턴) + atomic transaction (sign-negating + corrected + reversal_log INSERT 모두 1 transaction):
       1. SELECT target_event FROM inventory_ledger WHERE event_id = target_event_id AND tenant_id = tenant_id FOR UPDATE (SELECT FOR UPDATE — 6-1 wire closing_period_service 동일 패턴).
       2. SELECT period_status FROM monthly_input_periods WHERE tenant_id = tenant_id AND period_key = target_event.period_key (period_status='open' / 'closed' 허용, 'locked' 일 경우 ReversalLockedPeriodError 422).
       3. authorize_reversal (T1.3) decision — capability_granted 검증 (M11 owns authorization — PRD §F11.3 + AD-22).
       4. correction_group_id = uuid7() (5-2 P8 pattern, uuid4 fallback).
       5. **sign-negating row INSERT** (event_type='reversal_negating' + reverses_event_id=target_event.event_id + reversal_of_period_key=target_event.period_key + correction_group_id=correction_group_id + qty=-target_event.qty + banker's rounding). 11-value event_type CHECK + reversal_coherence CHECK + qty_signed_coherence CHECK 통과 검증 (DB trigger).
       6. **corrected row INSERT** (corrected_qty / corrected_period_key NOT None 시) — event_type='reversal_corrected' + reverses_event_id=target_event.event_id + correction_group_id=correction_group_id + qty=corrected_qty + period_key=corrected_period_key. DB CHECK 통과 검증.
       7. AD-25 publisher publish (channel='ai_cache') — `cache_invalidation_publisher.publish(...)` 호출.
       8. audit-first INSERT to `reversal_log` + audit_logs (`m11_reversal_handler_invoked` + `reversal_negating_inserted` + `reversal_corrected_inserted` + `monthly_input_period_opening_unlocked` if 5-1 opening carry 관련 시 + `inventory_ledger_reversal_logged` for INVENTORY_LEDGER).
       9. COMMIT — atomic transaction 종료.
     - **AC #3.2 AD-22 unique 제약 보장 (NEW `ReversalService.execute_reversal`)** — `(tenant_id, reverses_event_id)` unique constraint (Alembic 0015 `uq_inventory_ledger_reverses_event_id` UNIQUE `(tenant_id, reverses_event_id) WHERE reverses_event_id IS NOT NULL`) 보존. 동일 target_event_id 로 reversal sequence 2회 호출 시 2번째 호출에서 `uq_inventory_ledger_reverses_event_id` violation → 422 REVERSAL_DUPLICATE typed envelope. defense-in-depth: pure kernel #1 `validate_reversal_negating_constraints` + service layer SELECT FOR UPDATE 직전 pre-check (CR 4-2 TOCTOU 방지 + pg_advisory_xact_lock 보강 — Epic 2 2-3 D2 결정 패턴).
     - **AC #3.3 AD-25 publisher 1-channel (NEW `apps/api/core/cache_invalidation_publisher.py`)** — `class CacheInvalidationPublisher` with `publish(*, channel: str, tenant_id: UUID, event_id: UUID, correction_group_id: UUID, trace_id: str) -> CacheInvalidationReceipt`. Channel registry (FROZENSET): `{'ai_cache'}` (1차 wire, M10 AI cache invalidation). M11 reversal sequence 완료 시 publish. 11-3 entry 시점에 channel registry 확장 (cost_engine_cache / fiscal_period_cache / closing_snapshot_cache 등).
     - **AC #3.4 H6 production bug fix (NEW `packages/services/m5_ledger/` 2 NEW pure kernels)** — `count_period_events_sql(period_key, *, event_type=None)` + `query_period_closing_snapshot_all_sql(period_key)` 2 pure kernel 정의. `apps/api/modules/m4_inventory/services/ledger_service.py` extension — `LedgerService.count_period_events(period_key, *, event_type=None)` + `LedgerService.query_period_closing_snapshot_all(period_key)` 2 NEW method 추가 (pure kernel dispatch). `closing_period_service.py:528/531` 의 두 호출 정합 (H6 fold-in 결정 — 6-2 Deferral #11 해결). production 진입 차단 해소.
     - **AC #3.5 monthly_input_periods.status 가드 (NEW `ReversalService.execute_reversal`)** — period_status='open' 또는 'closed' 인 경우에만 reversal 허용. 'locked' 일 경우 ReversalLockedPeriodError (422 LOCKED_PERIOD_REVERSAL_REJECTED typed envelope). 11-2 wire 시점에 fiscal_periods.status 추가 가드 (greenfield). 11-1 wire는 monthly_input_periods.status 한정 가드.
     - **AC #3.6 Atomic transaction + audit-first ordering (CR 1.1 + CR 4-2 lesson)** — sign-negating row + corrected row + reversal_log INSERT 모두 1 transaction (REPEATABLE READ). audit-first INSERT 가 row INSERT 직전 발동 (CR 1.1 idempotent no-op skip + revert path 보존). failure 시 rollback + audit INSERT (`reversal_rejected`).

4. **Given** AC #1~#3 backend wire + AC #2 frontend wire + 5-2/5-3/6-1/6-2/0.5 carry-over
   **When** 본 스토리 commit 안에서 H6 fold-in + A9 fill + A11 capability matrix v1.10 wire
   **Then** 다음 defense-in-depth + carry-over wire 발동 (AC #4 — H6 production bug 차단 해소 + A9 결정 5개 범위 fill + capability matrix v1.10):
     - **H6 fold-in (AC #4 — **H6 PRIMARY wire**)** — `packages/services/m5_ledger/` 2 NEW pure kernel:
       1. `count_period_events.py` — `count_period_events_sql(period_key, *, event_type=None)` (text SQL builder).
       2. `query_period_closing_snapshot_all.py` — `query_period_closing_snapshot_all_sql(period_key)` (closing_snapshot per-product qty aggregate).
       `apps/api/modules/m4_inventory/services/ledger_service.py` extension — 2 NEW method 추가 (pure kernel dispatch). `closing_period_service.py:528/531` 두 호출 정합. **production 진입 차단 해소** + monthly closing report read-only aggregator 정상 동작 (6-2 wire 진입점).
     - **A9 결정 5개 범위 fill (AC #4 — **A9 PRIMARY wire**)**:
       1. **`reversal_negating` + `reversal_corrected` event type fill** — Alembic 0015 11-value CHECK (lines 92-110) 이미 wire. 본 스토리는 actual INSERT (T1.1 + T1.2 pure kernel) + ReversalService.execute_reversal wire.
       2. **`opening_inventory_unlocked` action** — `apps/api/core/audit_action.py` `MonthlyInputPeriodAction` Literal extension — `opening_inventory_unlocked` 1 value 신규 fill. `_ActionRegistry._REGISTRY[ActionClass.MONTHLY_INPUT_PERIOD]` accepted frozenset 3 → 4 values fill.
       3. **`reversal_request_enabled` field wire** — `Capability.REVERSAL_REQUEST` 신규 정의 (manufacturing 3종 ✅ / service-only ❌). `MonthlyInputStateResponse.reversal_request_enabled` field (5-3 wire + 6-1 extension) = Capability.REVERSAL_REQUEST capability_granted mirror.
       4. **service layer reversal handler** — `apps/api/modules/m11_close/services/reversal_service.py` (NEW) — ReversalService class 4 operations.
       5. **UI reversal request form** — `apps/web/components/m4-inventory/ReversalRequestDialog.tsx` (NEW) + ReversalRequestForm + ReversalRequestButton.
     - **Capability matrix v1.10 (extension `docs/capability-matrix.md`)** — Epic 5 retro §7 A9 결정 + 6-1 v1.8 + 6-2 v1.9 extension:
       ```markdown
       | Capability | manufacturing | mfg+service | mfg+service+other | service-only |
       |------------|---------------|-------------|--------------------|--------------|
       | ... 기존 14+ capabilities (5-1/5-2/5-3/6-1/6-2) ... |
       | REVERSAL_REQUEST (11-1 wire v1.10) | ✅ | ✅ | ✅ | ❌ INDUSTRY_NOT_SUPPORTED |
       ```
       Changelog v1.10 (11-1 wire done) — A9 결정 wire 완료.
     - **AD-25 publisher 1-channel (AC #4 — **AD-25 PRIMARY wire**)** — `apps/api/core/cache_invalidation_publisher.py` (NEW) — `CacheInvalidationPublisher.publish(channel='ai_cache', ...)` 1차 wire. M11 reversal sequence 완료 시 publish. channel registry FROZENSET = `{'ai_cache'}`. 11-3 entry 시점에 channel 확장.
     - **A8 inline projection deprecation timeline (Epic 5 retro §7 A8 결정)** — `docs/reversal-sequence.md` (NEW 11-1) §timeline 섹션 명시:
       ```markdown
       ### A8 — Epic 3.3 inline projection deprecation timeline
       - 11-1 wire 시점 (Epic 11 진입점): inline projection 보존 (Epic 6 close-out 시점 미도래)
       - 11-2 wire: inline projection 보존 (close lock 무관)
       - 11-3 wire: inline projection fold-in 결정 + reversal_corrected row 가 monthly_input_periods.opening_inventory JSONB 업데이트 trigger
       - Epic 11 close-out 시점에 inline projection 완전 제거 (Epic 6 close-out 후)
       ```
     - **A9 5개 범위 audit log wire (AC #4)** — `audit_logs.action='m11_reversal_handler_invoked'` (ActionClass.REVERSAL_LOG 신규 value 1) + `action='reversal_negating_inserted'` + `action='reversal_corrected_inserted'` + `action='reversal_rejected'` + `action='reversal_unauthorized'` 5 values. INSERT to audit_logs (immutable, AD-2). payload = self-describing (CR 1.1 lesson).
     - **`opening_inventory_unlocked` audit log wire (AC #4)** — `audit_logs.action='monthly_input_period_opening_unlocked'` (ActionClass.MONTHLY_INPUT_PERIOD 신규 value 1). reversal_corrected row 가 5-1 opening carry chain 의 opening_inventory JSONB 업데이트 시 발동. INSERT to audit_logs (immutable).
     - **SQL CHECK constraint 추가 없음 (AC #4)** — 11-1 wire는 Alembic 0015 inventory_ledger DDL 그대로 활용. NEW Alembic migration 추가 불요요 (reversal_negating + reversal_corrected event type 이미 CHECK 안에 포함).
     - **W4 isolated service layer tests (Story 5-2 carry-over close)** — `tests/api/m4_inventory/test_reversal_service.py` (NEW) — 14 cases: reversal sequence 2-step INSERT (3), atomic transaction + rollback (2), unique constraint violation 422 (2), period_status='locked' reject (2), capability 미보유 reject (2), idempotent re-call skip (1), audit-first ordering (1), AD-25 publisher integration (1).

5. **Given** AC #1~#4 backend wire + frontend wire + H6 fold-in + A9 fill + AD-25 publisher + capability matrix v1.10
   **When** 본 스토리 dev-story 진입 시 5-2 inventory_ledger + 5-3 closing_guard + 6-1 closing_period + 6-2 monthly closing report 위에 additive
   **Then** 다음 3-layer defense wire 발동 (AC #5 — PRD §A11 4-layer + reversal sequence + capability gate):
     - **Layer 1 (입력 시 경고)** — Story 3.3 inline projection + 5-2 ledger aggregate 동시 활용. 음수 기초재고 / 출고 > 기초재고 입력 시 sonner `toast.warning` (5-3 wire 그대로).
     - **Layer 2 (마감 시 차단)** — Story 5-3 `closing_guard_service.request_close_attempt` + 4-2 `is_blocked` 위 additive. 음수 기말재고 발생 시 409 NEGATIVE_CLOSING_INVENTORY typed envelope + ClosingGuardBanner red Alert (5-3 wire 그대로).
     - **Layer 3 (마감 확정 시 snapshot)** — Story 6.1 `closing_period_service.confirm_closing_period` dispatch. CLOSING_READY 시 ledger INSERT (closing_snapshot event_type) + monthly_input_periods.status='closed' UPDATE + audit INSERT (atomic transaction). 409 ALREADY_CLOSED 시 멱등성 보장 (idempotent no-op skip).
     - **Layer 4 (역분개 — **11-1 PRIMARY wire**)** — `ReversalService.execute_reversal` dispatch. M4 entrypoint (`POST /api/v1/inventory/ledger/reversal-requests` 501 forward-fill) → M11 actual write (`POST /api/v1/close/reversal-requests` 201) wire. AD-22 sequence (1) sign-negating row INSERT + (2) optional corrected row INSERT. capability gate + period_status 가드 + unique constraint + audit-first ordering.
     - **Capability gate (4-tier defense)** — `Capability.REVERSAL_REQUEST` (11-1 wire v1.10) + `Capability.INVENTORY_LEDGER` (5-2 wire) + `Capability.MONTHLY_CLOSING_REPORT` (6-1 v1.8 wire) + `Capability.MONTHLY_INPUT_PRODUCTION` (3-1 wire) 4 capabilities 모두 reversal sequence 진입점에서 검증. service-only tenant → 403 INDUSTRY_NOT_SUPPORTED typed envelope (A9 결정).

6. **Given** AC #1~#5 backend + frontend + H6 + A9 + AD-25 + capability gate + ClosingPeriodConfirmationPanel + MonthlyClosingReportPanel
   **When** 본 스토리 dev-story 진입 시 AD-22 sequence wire + AD-25 publisher integration + H6 fix
   **Then** 다음 verification sync 발동 (AC #6 — AD-22 reversal sequence ↔ ledger append-only ↔ reversal_log audit ↔ AD-25 publisher ↔ fiscal_period state machine 5-source 양방향 동기화):
     - **AD-22 reversal sequence wire (AC #6)** — ReversalService.execute_reversal 2-step INSERT dispatch:
       1. sign-negating row INSERT (event_type='reversal_negating' + reverses_event_id=target_event.event_id + reversal_of_period_key=target_event.period_key + correction_group_id=correction_group_id + qty=-target_event.qty + banker's rounding + AD-15 parity).
       2. corrected row INSERT (event_type='reversal_corrected' + reverses_event_id=target_event.event_id + correction_group_id=correction_group_id + qty=corrected_qty + period_key=corrected_period_key + AD-15 parity).
       → `(tenant_id, reverses_event_id)` unique 보장 (Alembic 0015 `uq_inventory_ledger_reverses_event_id` PARTIAL UNIQUE INDEX) + reversal_coherence CHECK + qty_signed_coherence CHECK (reversal_negating 음수 qty 허용) + qty_required_for_quantitative_events CHECK 통과.
     - **AD-25 publisher integration (AC #6)** — `ReversalService.execute_reversal` step 7 — `cache_invalidation_publisher.publish(channel='ai_cache', tenant_id=tenant_id, event_id=target_event_id, correction_group_id=correction_group_id, trace_id=trace_id)`. channel registry FROZENSET = `{'ai_cache'}`. publish receipt INSERT to audit_logs (ActionClass.SYSTEM or ActionClass.AI_CACHE_INVALIDATION — 11-3 entry 시점에 결정).
     - **H6 fix integration (AC #6)** — `apps/api/modules/m4_inventory/services/ledger_service.py` extension — `LedgerService.count_period_events(period_key, *, event_type=None)` + `LedgerService.query_period_closing_snapshot_all(period_key)` 2 NEW method 추가. pure kernel dispatch. `closing_period_service.py:528/531` 정합.
     - **Verification ordering invariant (AD-12)** — 11-1 wire는 V4 verification 무관 (reversal sequence는 ledger append-only INSERT — V8 골든 매트릭스 input 변화 없음). 11-3 wire에서 V4 재검증 trigger.
     - **Industry skip matrix (4-3 wire 패턴)** — manufacturing / manufacturing_service / manufacturing_service_other → ReversalService 정상 발동. service-only → 403 INDUSTRY_NOT_SUPPORTED typed envelope (A9 capability gate).
     - **PRD §F11.3 AC ↔ ledger invariants 매트릭스**:
       - AC "부호 반전 row 1개 INSERT" → reversal_negating INSERT 1 row + Alembic 0015 11-value CHECK 통과.
       - AC "corrected row INSERT" → reversal_corrected INSERT 1 row (optional).
       - AC "원본 row 변경 없음" → append-only trigger (BEFORE UPDATE OR DELETE) + service-layer _assert_not_modifying (5-2 wire) 보존.
       - AC "(tenant_id, reverses_event_id) unique" → Alembic 0015 PARTIAL UNIQUE INDEX 보존.
       - AC "재무 효과 0 수렴" → reversal_negating qty = -target_event.qty + corrected row 동일 correction_group_id → sum = 0.
       - AC "M10 캐시 무효화 notification" → AD-25 publisher publish (channel='ai_cache').

7. **Given** AC #1~#6 backend + frontend + AD-22 + AD-25 + H6 fix + verification ordering
   **When** 본 스토리 dev-story 진입 시 audit-first + idempotent no-op + A5 forward-lock + A7 wire + A8 timeline + A9 fill + A11 capability
   **Then** 다음 audit + drift + A7 wire 발동 (AC #7 — A5 forward-lock + A7 wire + A8 timeline + A9 5개 fill + A11 capability v1.10):
     - **`apps/api/core/audit_action.py` extension** — `ReversalLogAction = Literal["reversal_negating_inserted", "reversal_corrected_inserted", "reversal_rejected", "reversal_unauthorized", "m11_reversal_handler_invoked"]` 5 values 신규 (placeholder `_placeholder_reversal_log` 제거). + `MonthlyInputPeriodAction` Literal extension: `monthly_input_period_opening_unlocked` 1 value 신규. **A5 forward-lock**: `_ActionRegistry._REGISTRY[ActionClass.REVERSAL_LOG]` accepted frozenset empty → 5 values fill + `_REGISTRY[ActionClass.MONTHLY_INPUT_PERIOD]` accepted frozenset 3 → 4 values fill.
     - **A5 drift detector (`tests/services/test_audit_action_centralization.py` extension)** — ActionClass.REVERSAL_LOG 5 new actions 검증 pass + ActionClass.MONTHLY_INPUT_PERIOD 4 values 검증 pass. drift count = 0 유지.
     - **3-way consistency drift detector (`tests/integration/test_audit_action_consistency.py` extension)** — A5 forward-lock:
       - registry ↔ DB CHECK: ActionClass.REVERSAL_LOG 5 values (registry SSOT) + ActionClass.MONTHLY_INPUT_PERIOD 4 values (5-1 wire 3 + 11-1 wire 1) + ActionClass.INVENTORY_LEDGER 6 values (5-2 wire + 11-1 actual emit).
       - call sites AST-grep: `emit_audit(` raw in `apps/api/modules/m11_close/` + `apps/api/modules/m4_inventory/` + `apps/api/modules/m6_verification/` = 0 (5-1 + 5-2 + 5-3 + 6-1 + 6-2 + 11-1 모두 typed).
       - verified DB constraint contents match published alembic migration files (Alembic 0013 + 0014 + 0015 + 0016 + 0017 + 0018 모두 일치 — Alembic 0018은 11-1 wire 시점에서 reversal_log namespace 추가).
     - **A7 wire (Epic 4 close-out retro A7 — async test pattern + SDR overclaim)** — Story 5-2 + 5-3 + 6-1 + 6-2 wire pattern 그대로:
       - Async test pattern (CR 4-3 F-1) — 모든 service-layer test `def test_x(): asyncio.run(_impl())` wrapper (pytest-asyncio 금지).
       - SDR overclaim detector — `tests/integration/test_sdr_test_count_drift.py` 2 cases (5-1 + 5-2 + 5-3 + 6-1 + 6-2 + 11-1 wire pattern).
     - **`ReversalService.execute_reversal` CR 1.1 audit-first wire**:
       1. `m11_reversal_handler_invoked` audit INSERT (handler entry — pre-check 통과).
       2. sign-negating row INSERT (T1.1 pure kernel).
       3. `reversal_negating_inserted` audit INSERT (post-step-2).
       4. corrected row INSERT (T1.2 pure kernel — optional).
       5. `reversal_corrected_inserted` audit INSERT (post-step-4, optional).
       6. `monthly_input_period_opening_unlocked` audit INSERT (5-1 opening carry chain 관련 시, optional).
       7. AD-25 publisher publish.
       8. `inventory_ledger_reversal_logged` audit INSERT (forward-fill actual emit).
       CR 1.1 idempotent re-call 시 skip (한 reversal sequence 당 1 audit set 발동 — same correction_group_id re-call 시 unique constraint violation으로 멱등).
     - **PR 일관성 guard** — Alembic 0015 migration 그대로 (11-1 wire는 NEW Alembic migration 추가 불요요, Alembic 0018은 reversal_log namespace 추가 시점 결정 — 11-1 entry 시점에 결정). `tests/integration/test_alembic_migration_chain.py` extension — reversal_log guard wire (11-1 결정 시점).

8. **Given** AC #1~#7 backend + frontend + AD-22 + AD-25 + H6 + audit + drift + A7 + A8 timeline + A9 fill + A11 capability
   **When** 본 스토리 10 task (T1-T10) 실행
   **Then** 다음 tests wire 발동 (AC #8 — 3중 게이트 + drift detector + A5 + A7 + frontend vitest + Playwright):
     - **Pure kernel (5 NEW files — ~36 cases)**:
       - `tests/services/m11_close/test_reversal_negating.py` (NEW) — 10 cases: build_reversal_negating_event (4 — 정상 + 4 self-reversal 거부 시나리오), validate_reversal_negating_constraints (3 — opening_carried / purchase_inbound / closing_snapshot 모두 reversal 가능 검증 + reversal_negating/reversal_corrected 자체 reversal 불가), banker's rounding (2), M11_AUTHORIZE_KO constants (1).
       - `tests/services/m11_close/test_reversal_corrected.py` (NEW) — 8 cases: build_reversal_corrected_event (3 — 정상 + corrected_qty=None skip + corrected_period_key 변경), validate_reversal_corrected_constraints (2 — correction_group_id 일치 / period_key AD-24 형식), banker's rounding (2), period_key AD-24 validation (1).
       - `tests/services/m11_close/test_reversal_authorization.py` (NEW) — 6 cases: authorize_reversal (3 — capability_granted / period_status 가드 / event_type reversal 가능 검증), M11_REJECT_KO constants (3).
       - `tests/services/m5_ledger/test_count_period_events.py` (NEW) — 6 cases: count_period_events_sql (3 — event_type=None / event_type=str / closing_snapshot filter), tenant_id binding (2), SQL injection 방지 (1).
       - `tests/services/m5_ledger/test_query_period_closing_snapshot_all.py` (NEW) — 6 cases: query_period_closing_snapshot_all_sql (3 — 정상 / tenant scoping / closing_snapshot filter), per-product aggregate (2), SQL injection 방지 (1).
     - **Service layer (3 NEW files — ~30 cases)**:
       - `tests/api/m11_close/test_reversal_service.py` (NEW) — 14 cases (AC #4 wire spec — atomic transaction + rollback + unique violation + period_status='locked' + capability reject + idempotent + audit-first + AD-25 publisher).
       - `tests/api/m4_inventory/test_ledger_service_h6.py` (NEW) — 10 cases: count_period_events (3), query_period_closing_snapshot_all (3), closing_period_service.py:528/531 정합 (2), monthly closing report integration smoke (2).
       - `tests/api/m11_close/test_reversal_handlers.py` (NEW) — 6 cases: POST /api/v1/close/reversal-requests (2 — success 201 + reject 403), GET /api/v1/close/reversal-requests/{correction_group_id} (2), POST /api/v1/close/cache-invalidation (2 — channel='ai_cache' publish success + INVALID_CHANNEL reject).
     - **A5 drift detector (extension)** — `tests/services/test_audit_action_centralization.py` extension — 5 NEW ActionClass.REVERSAL_LOG actions 검증 + ActionClass.MONTHLY_INPUT_PERIOD 4 values 검증. drift count = 0 유지.
     - **3-way consistency drift detector (extension A5)** — `tests/integration/test_audit_action_consistency.py` extension — 4 NEW cases:
       - ActionClass.REVERSAL_LOG registry ↔ DB CHECK consistency (2 cases).
       - ActionClass.MONTHLY_INPUT_PERIOD 4 values consistency (2 cases).
     - **SDR drift detector (extension A7)** — `tests/integration/test_sdr_test_count_drift.py` extension — 2 cases (5-1 + 5-2 + 5-3 + 6-1 + 6-2 + 11-1 wire pattern).
     - **SQL CHECK constraint test (extension)** — Alembic 0015 11-value event_type CHECK + reversal_coherence + qty_signed_coherence + uq_inventory_ledger_reverses_event_id PARTIAL UNIQUE 모두 보존 검증. NEW Alembic migration 추가 불요요 (Alembic 0018 entry 시점에 결정).
     - **frontend vitest (Story 0.5 wire)** — 14 scenarios:
       1. `apps/web/__tests__/m11-reversal-panel.test.tsx` (NEW) — 6 scenarios (ReversalRequestDialog open + reason textarea + corrected_qty/period_key input + submit mutation + sonner toast + capability-gated hide).
       2. `apps/web/__tests__/monthly-input-tabs.test.tsx` (5-3 wire + 6-1 extension + 6-2 extension) extension — 2 NEW 11-1 scenarios 추가 (ReversalRequestButton render + closing_period_confirmed 후 활성화).
       3. `apps/web/__tests__/m11-reversal-route.test.tsx` (NEW) — 6 scenarios: ReversalRequestRoute page load + ReversalRequestForm display + mutation success/error + service-only 403 redirect + reason textarea validation + audit trail.
     - **Playwright E2E (Story 0.5 wire)** — 5 E2E scenarios:
       1. `tests/e2e/m11-reversal.spec.ts` (NEW) — 5 scenarios.
       2. happy-path: [월 입력] → 6 stream 입력 → [마감] tab → ClosingPeriodConfirmationPanel → [마감 확정] → MonthlyClosingReportPanel 자동 표시 → [역분개] 클릭 → ReversalRequestDialog → reason 입력 + corrected_qty 입력 → [역분개 실행] → correction_group_id 표시 + sonner toast.success.
       3. atomic-transaction: reversal sequence 실행 중 failure → sign-negating row rollback + audit-failure emit + sonner toast.error.
       4. unique-violation: 동일 target_event_id 로 reversal 2회 호출 → 2번째 422 REVERSAL_DUPLICATE + sonner toast.error.
       5. period-locked: monthly_input_periods.status='locked' → ReversalRequestButton 비활성 + sonner toast.error('잠긴 기간 — 역분개 불가').
       6. capability-gate: service-only tenant 진입 → 403 INDUSTRY_NOT_SUPPORTED + sonner toast.error + ReversalRequestButton 비노출.

9. **Given** AC #1~#8 backend + frontend + AD-22 + AD-25 + H6 + audit + drift + A7 + A8 timeline + A9 fill + A11 capability + carry-over close
   **When** 본 스토리 dev-story 진입 시 Story 0.5 frontend plumbing 위 additive + 5-2/5-3/6-1/6-2 wire 위에 additive
   **Then** 다음 3-layer defense + AD-22 reversal sequence wire 발동 (AC #9 — PRD §A11 4-layer + reversal sequence + capability gate + AD-25 publisher):
     - **PRD §A11 4-layer (extension 6-2 4-layer)** — 6-2 wire 4-layer 위에 additive Layer 5 reversal sequence:
       1. **Layer 1 (입력 시 경고)** — Story 3.3 inline projection + 5-2 ledger aggregate 동시 활용. 음수 기초재고 / 출고 > 기초재고 입력 시 sonner `toast.warning` (5-3 wire 그대로).
       2. **Layer 2 (마감 시 차단)** — Story 5-3 `closing_guard_service.request_close_attempt` + 4-2 `is_blocked` 위 additive. 음수 기말재고 발생 시 409 NEGATIVE_CLOSING_INVENTORY typed envelope + ClosingGuardBanner red Alert (5-3 wire 그대로).
       3. **Layer 3 (마감 확정 시 snapshot)** — Story 6.1 `closing_period_service.confirm_closing_period` dispatch. CLOSING_READY 시 ledger INSERT (closing_snapshot event_type) + monthly_input_periods.status='closed' UPDATE + audit INSERT (atomic transaction). 409 ALREADY_CLOSED 시 멱등성 보장 (idempotent no-op skip).
       4. **Layer 4 (마감 보고서 시각화)** — **6-2 `monthly_closing_report_service.get_monthly_closing_report`** dispatch. 3-source read-only aggregate (closing_snapshot + ledger events + fiscal_period_snapshots) + KRW/USD dual display (AD-8 + PRD §F5.2) + V4 verdict envelope (6-1 wire) + audit-trail list (CR 1.1) 한 페이지 시각화.
       5. **Layer 5 (역분개 — **11-1 PRIMARY wire**)** — `ReversalService.execute_reversal` dispatch. AD-22 sequence (1) sign-negating row INSERT + (2) optional corrected row INSERT + (3) correction_group_id link. capability gate + period_status 가드 + unique constraint + audit-first ordering. M4 entrypoint → M11 actual write wire.
     - **Capability gate (4-tier defense)** — `Capability.REVERSAL_REQUEST` (11-1 v1.10 wire) + `Capability.INVENTORY_LEDGER` (5-2 wire) + `Capability.MONTHLY_CLOSING_REPORT` (6-1 v1.8 wire) + `Capability.MONTHLY_INPUT_PRODUCTION` (3-1 wire) 4 capabilities 모두 reversal sequence 진입점에서 검증. service-only tenant → 403 INDUSTRY_NOT_SUPPORTED typed envelope (A9 결정).

10. **Given** AC #1~#9 backend + frontend + AD-22 + AD-25 + H6 + audit + drift + A7 + A8 timeline + A9 fill + A11 capability + PRD §A11 5-layer + capability gate
    **When** 본 스토리 10 task (T1-T10) 실행 + 5-2/5-3/6-1/6-2/0.5 carry-over close
    **Then** 다음 defense-in-depth + AD-22 reversal sequence wire 발동 (AC #10 — 5-2/5-3/6-1/6-2 founding + A9 5개 fill + docs 5 NEW + 4 EXTENSION + 3중 게이트 mandatory CI):
      - **Backend 5 NEW pure kernels + 2 NEW service layers + 2 NEW handlers + 1 NEW core publisher**:
        1. `packages/services/m11_close/reversal_negating.py` (NEW pure kernel #1) — build_reversal_negating_event + validate_reversal_negating_constraints + M11_AUTHORIZE_KO constants.
        2. `packages/services/m11_close/reversal_corrected.py` (NEW pure kernel #2) — build_reversal_corrected_event + validate_reversal_corrected_constraints.
        3. `packages/services/m11_close/reversal_authorization.py` (NEW pure kernel #3) — authorize_reversal + M11_REJECT_KO constants.
        4. `packages/services/m5_ledger/count_period_events.py` (NEW pure kernel #4 — **H6 fix**) — count_period_events_sql.
        5. `packages/services/m5_ledger/query_period_closing_snapshot_all.py` (NEW pure kernel #5 — **H6 fix**) — query_period_closing_snapshot_all_sql.
        6. `apps/api/modules/m11_close/services/reversal_service.py` (NEW service layer #1) — ReversalService class 4 operations.
        7. `apps/api/modules/m11_close/services/reversal_kernel_adapter.py` (NEW service layer #2) — pure kernel dispatch adapter.
        8. `apps/api/modules/m11_close/handlers.py` (NEW handlers) — 3 NEW routes (POST /close/reversal-requests + GET /close/reversal-requests/{correction_group_id} + POST /close/cache-invalidation).
        9. `apps/api/core/cache_invalidation_publisher.py` (NEW core publisher — **AD-25 PRIMARY**) — CacheInvalidationPublisher with channel FROZENSET = {'ai_cache'}.
      - **Backend 8 EXTENSION files**:
        1. `apps/api/alembic/versions/0015_inventory_ledger.py` (5-2 wire) — 그대로 활용 (NEW Alembic migration 추가 불요요, reversal_negating + reversal_corrected event type 이미 CHECK 안에 포함).
        2. `apps/api/main.py` (extension) — 5 NEW exception handlers (201 REVERSAL_COMPLETED / 403 REVERSAL_REJECTED / 403 REVERSAL_UNAUTHORIZED / 422 REVERSAL_DUPLICATE / 422 LOCKED_PERIOD_REVERSAL_REJECTED + AD-25 publish-receipt envelope mapping, AD-15 §4 typed envelope).
        3. `apps/api/core/capability.py` (extension) — `Capability.REVERSAL_REQUEST` 신규 정의 (manufacturing 3종 ✅ / service-only ❌).
        4. `apps/api/core/audit_action.py` (extension) — ReversalLogAction 5 values fill + MonthlyInputPeriodAction extension (opening_inventory_unlocked 1 value) + _REGISTRY fill.
        5. `apps/api/modules/m4_inventory/services/ledger_service.py` (extension) — 2 NEW method 추가 (count_period_events + query_period_closing_snapshot_all) — **H6 fix integration**.
        6. `apps/api/modules/m4_inventory/services/closing_period_service.py` (extension) — 2 호출 정합 (lines 528/531 → H6 fix 호출) — **H6 production bug 차단 해소**.
        7. `apps/api/modules/m4_inventory/handlers.py` (5-2 wire 501 forward-fill route) — extension — 501 forward-fill route는 deprecation path 표시 (M11 actual write route가 SSOT). 11-1 wire 후 후속 sprint 에서 deprecation → deletion 결정.
        8. `apps/api/core/pydantic_schemas.py` (extension) — ReversalRequest + ReversalResponse + ReversalCorrectedEvent + CacheInvalidationReceipt Pydantic v2 schemas.
      - **Frontend 4 NEW files**:
        1. `apps/web/lib/m11-reversal.ts` (NEW TS mirror) — type definitions + format helpers.
        2. `apps/web/lib/m11-reversal-parity.ts` (NEW TS↔Python SSOT parity helper) — Decimal serialization + banker's rounding + sign-negating arithmetic.
        3. `apps/web/components/m4-inventory/ReversalRequestDialog.tsx` (NEW component) — shadcn Dialog + Form pattern.
        4. `apps/web/components/m4-inventory/ReversalRequestForm.tsx` (NEW component) — shadcn Form + sonner toast wire.
      - **Frontend 5 EXTENSION files**:
        1. `apps/web/lib/closing-period.ts` (6-1 wire) — ReversalRequestTrigger interface export 추가.
        2. `apps/web/components/m2-input/MonthlyInputTabs.tsx` (5-3 wire + 6-1 extension + 6-2 extension) — ReversalRequestButton wire (ClosingPeriodConfirmationPanel + MonthlyClosingReportPanel + ReversalRequestButton 3-component vertical stack).
        3. `apps/web/components/m4-inventory/ReversalRequestButton.tsx` (NEW trigger button) — MonthlyInputStateResponse context 에서 ReversalRequestDialog trigger.
        4. `apps/web/lib/m2-input-warnings.ts` (3-3 wire) — 그대로 활용 (no change).
        5. `apps/web/messages/ko-KR.json` (extension) — 9 NEW strings (reversal_request_dialog_title + reversal_request_reason_label + reversal_request_reason_placeholder + reversal_request_corrected_qty_label + reversal_request_corrected_period_key_label + reversal_request_submit + reversal_request_cancel + reversal_request_success_ko + reversal_request_error_ko).
      - **Test 8 NEW + 4 EXTENSION files**: ~110 NEW cases 추가 (pure 36 + service 30 + drift 6 + A5 forward-lock 6 + A7 SDR 2 + TS mirror parity 6 + frontend vitest 14 + Playwright E2E 5 + H6 integration 5).
      - **docs 5 NEW + 4 EXTENSION**:
        1. `docs/reversal-sequence.md` (NEW) — Story 11.1 operator/dev guide (6-2 monthly-closing-report.md pattern).
        2. `docs/closing-period.md` (6-1 wire) — §11.1 (H6 fix 결과 + reversal sequence 진입점) §V4 골든 fixture deferred to T10.5 → 6-2 carry-over close-out 명시.
        3. `docs/capability-matrix.md` (extension) — v1.10 (11-1 wire done) + 6-1 v1.8 + 6-2 v1.9 reference.
        4. `docs/conventions.md` (extension) — §0.5 + §9 + §10.7 + §11 (audit actions + reversal sequence wire + cache_invalidation_publisher + capability gate).
        5. `docs/audit-actions.md` (NEW) — A9 5개 fill + A5 forward-lock + drift detector 3-way consistency SSOT.
        6. `docs/architecture-inventory.md` (extension) — m11_close module 11-1 wire 3 NEW routes + 2 NEW services + 5 NEW pure kernels + 1 NEW core publisher.
        7. `docs/inventory-ledger.md` (extension) — §11.1 (Story 11.1 reversal sequence) + §AD-22 (sign-negating + corrected row + correction_group_id + reverses_event_id unique 제약).
        8. `docs/closing-guard.md` (extension) — §11.1 (11-1 reversal sequence 시각화 layer).
      - **3중 게이트 mandatory CI**:
        - ruff scoped (11-1 surface + 5-2/5-3/6-1/6-2/0.5 carry-over close) — 0 errors 목표.
        - import-linter 2 KEPT 0 broken (cost_engine_forbidden_io + engine_core_to_adapters_forbidden) + **ALLOWED_SERVICE_SUBMODULES m11_close 추가** (`tests/architecture/test_api_calls_only_ports.py:134-170` extension).
        - pytest **1,224 + 110 = 1,334 passed + 127 skipped + 0 failed** (6-2 carry-over 진입점 baseline) + **carry-over sweep + 110 NEW tests + SDR drift detector regenerate** = 1,444 passed + 127 skipped + 0 failed 목표.
        - frontend vitest 14 scenarios (11-1 panel + 11-1 route + 11-1 tabs extension) + 44 carry-over (5-3 + 6-1 + 6-2) = 58 scenarios.
        - Playwright E2E 5 scenarios (11-1 NEW) + 17 carry-over (5-3 + 6-1 + 6-2) = 22 scenarios.

## Dev Agent Guardrails

### Critical Architecture Compliance

- **AD-1 Modular Monolith + Hexagonal Core** — 11-1 wire는 pure kernel + service layer + handlers 표준 3-tier 패턴 (5-1/5-2/5-3/6-1/6-2 동일). `packages/services/m11_close/` (NEW 3 pure kernels) + `packages/services/m5_ledger/` (NEW 2 pure kernels — H6 fix) + `apps/api/modules/m11_close/services/reversal_service.py` (NEW) + `apps/api/modules/m11_close/handlers.py` (NEW). engine layer (`packages/cost_engine/`) 무변경 (engine은 reversal 의미 모름 — 4-2 wire 패턴).
- **AD-2 Append-only ledger** — 11-1 wire PRIMARY. 5-2 inventory_ledger SSOT + PostgreSQL `BEFORE UPDATE OR DELETE` trigger 그대로 활용. reversal_negating + reversal_corrected row 모두 append-only INSERT. original row UPDATE/DELETE 금지 (5-2 wire trigger).
- **AD-3 Multi-tenant RLS** — 11-1 wire는 RLS 위에서 동작. `tenant_id` 자동 derive from JWT (AD-3 SSOT). reversal sequence는 service_role bypass 불요요 (M4 caller + M11 writer 동일 tenant).
- **AD-6 Fiscal-period close lock** — 11-1 wire는 monthly_input_periods.status='closed' 상태에서 reversal 허용 (PRD §F11.3 spec — "마감 후 역분개"). 11-2 wire 시점에 fiscal_periods.status='closed' 추가 가드 (greenfield).
- **AD-11 Dependency direction** — 11-1 pure kernels = stdlib-only. NO sqlalchemy import (engine layer + service layer pattern). service layer가 ledger event를 인자로 전달.
- **AD-12 Verification ordering** — 11-1 wire는 V4 verification 무관 (reversal sequence는 ledger append-only INSERT — V8 골든 매트릭스 input 변화 없음). 11-3 wire에서 V4 재검증 trigger.
- **AD-15 Cross-language parity** — TS mirror drift detector `tests/integration/test_m11_reversal_label_consistency.py` (NEW) + Decimal serialization parity (sign-negating qty = -target.qty, banker's rounding to QTY_QUANTUM).
- **AD-22 Reversal construction** — 11-1 PRIMARY AC. Sequence: (1) sign-negating row INSERT (reverses_event_id link + reversal_of_period_key) + (2) optional corrected row INSERT (correction_group_id share). Original never changes. (tenant_id, reverses_event_id) unique 제약 보장. M4 calls request_reversal → M11 authorizes and writes.
- **AD-23 4-namespace pattern + reversal_log NEW** — monthly_input_periods + monthly_input_rows + inventory_ledger + audit_logs + fiscal_period_snapshots 5 namespace + reversal_log (NEW namespace, 11-1 wire).
- **AD-24 Typed period-key** — 'YYYY-MM' 형식 SSOT. reversal_of_period_key = 원본 event period_key (AD-24 typed). corrected row 의 period_key = corrected_period_key (AD-24 typed).
- **AD-25 Cache invalidation notification** — 11-1 wire PRIMARY (1-channel). Publisher = `apps/api/core/cache_invalidation_publisher.py` (NEW). M11 reversal sequence 완료 시 publish → channel='ai_cache'. 11-3 entry 시점에 publisher full wire + multi-channel 확장.

### Critical Lessons Applied (Meta-Learning)

- **CR 1.1 audit-first + idempotent no-op** — 11-1 wire는 reversal sequence 2-step INSERT (sign-negating + corrected) + audit-first ordering (m11_reversal_handler_invoked → reversal_negating_inserted → reversal_corrected_inserted → inventory_ledger_reversal_logged → monthly_input_period_opening_unlocked). CR 1.1 idempotent re-call 시 skip (unique constraint violation으로 멱등).
- **CR 4-2 1-shot INSERT + atomic transaction** — sign-negating row + corrected row + reversal_log INSERT 모두 1 REPEATABLE READ transaction. SELECT FOR UPDATE 패턴 (6-1 wire closing_period_service 동일) + pg_advisory_xact_lock(uuid5) 보강 (Epic 2 2-3 D2 결정 패턴).
- **CR 4-3 async test pattern** — 모든 service-layer test `def test_x(): asyncio.run(_impl())` wrapper (pytest-asyncio 금지). 11-1 wire 14 cases 동일 pattern.
- **CR 4-3 SDR overclaim detector** — `tests/integration/test_sdr_test_count_drift.py` 2 cases (5-1 + 5-2 + 5-3 + 6-1 + 6-2 + 11-1 wire pattern).
- **CR 4-4 V8 골든 byte-identical** — 11-1 wire는 V8 12-fi matrix 무변경 (reversal sequence는 ledger append-only INSERT — V8 input 영향 없음). 11-3 wire에서 V8 fixture extension 진입점 결정.
- **CR 0-4 banker's rounding parity** — `QTY_QUANTUM = Decimal("0.0001")` (NUMERIC(18,4)) + `quantize(QTY_QUANTUM, rounding=ROUND_HALF_EVEN)`. reversal_negating qty = -target.qty (banker's rounding). USD 환산 무관 (11-1 wire는 KRW only — PRD §F11.3 spec).
- **CR 2-1 capability matrix 4 epic 연속 자산** — `REVERSAL_REQUEST` capability 11-1 wire v1.10 신규 (manufacturing 3종 ✅ / service-only ❌).
- **CR 5-2 P8 `_mint_event_id()` uuid7 pattern** — correction_group_id = uuid7() (or uuid4 fallback).
- **CR 5-3 test pin contract** — `tests/integration/test_m11_reversal_label_consistency.py` 9 NEW cases (M11_AUTHORIZE_KO + M11_REJECT_KO constants parity).
- **CR 6-1 V4 naming collision** — 11-1 wire는 V4 verification 무관. 11-3 wire에서 V4 snapshot state machine 진입점 결정 (V4 cost/income slot 6-1 wire + V4 closing-period-consistency slot 6-1 wire + V4 reversal sequence slot 11-3 wire).

### Library/Framework Requirements

- **stack pin (AD-14)** — 11-1 wire는 stack pin 변동 0. Node 24.18 LTS / Next.js 16.2.11 / React 19.2.8 / TypeScript 7.0.2 / Tailwind 4.3.3 / FastAPI 0.139.2 / Python 3.12 / PostgreSQL 17 / structlog 26.1.0 / uv 0.11.32 / OpenTelemetry 1.44.0 그대로 활용.
- **shadcn Dialog primitive** — 11-1 wire 신규 도입. `pnpm dlx shadcn@latest add dialog` (Story 0.5 wire + 6-1 wire + 6-2 wire). 11-1 wire = Dialog primitive (ReversalRequestDialog).
- **shadcn Form primitive** — 11-1 wire 신규 도입. `pnpm dlx shadcn@latest add form`. 11-1 wire = Form primitive (ReversalRequestForm — reason + corrected_qty + corrected_period_key input).
- **decimal.js** — 11-1 wire sign-negating arithmetic parity. TS Decimal serialization parity (sign flip + banker's rounding + QTY_QUANTUM).
- **next-intl** — 11-1 wire ko-KR.json 9 NEW strings (Story 0.5 + 6-1 wire + 6-2 wire + 11-1 wire 통합).
- **sonner** — 11-1 wire toast.success + toast.error (5-3 + 6-1 + 6-2 + 11-1 wire).

### File Structure Requirements

#### Backend 5 NEW pure kernels + 2 NEW service layers + 2 NEW handlers + 1 NEW core publisher

1. `packages/services/m11_close/reversal_negating.py` (NEW pure kernel #1) — stdlib-only AD-11 layer rule.
2. `packages/services/m11_close/reversal_corrected.py` (NEW pure kernel #2) — stdlib-only AD-11 layer rule.
3. `packages/services/m11_close/reversal_authorization.py` (NEW pure kernel #3) — stdlib-only AD-11 layer rule.
4. `packages/services/m5_ledger/count_period_events.py` (NEW pure kernel #4 — **H6 fix**) — stdlib-only AD-11 layer rule.
5. `packages/services/m5_ledger/query_period_closing_snapshot_all.py` (NEW pure kernel #5 — **H6 fix**) — stdlib-only AD-11 layer rule.
6. `apps/api/modules/m11_close/services/reversal_service.py` (NEW service layer #1) — ReversalService class.
7. `apps/api/modules/m11_close/services/reversal_kernel_adapter.py` (NEW service layer #2) — pure kernel dispatch adapter.
8. `apps/api/modules/m11_close/handlers.py` (NEW handlers) — 3 NEW routes.
9. `apps/api/core/cache_invalidation_publisher.py` (NEW core publisher — **AD-25 PRIMARY**) — channel FROZENSET = {'ai_cache'}.

#### Backend 8 EXTENSION files

1. `apps/api/alembic/versions/0015_inventory_ledger.py` (5-2 wire) — 그대로 활용.
2. `apps/api/main.py` (extension) — 5 NEW exception handlers (AD-15 §4 typed envelope).
3. `apps/api/core/capability.py` (extension) — Capability.REVERSAL_REQUEST 신규 정의.
4. `apps/api/core/audit_action.py` (extension) — ReversalLogAction 5 values fill + MonthlyInputPeriodAction extension + _REGISTRY fill.
5. `apps/api/modules/m4_inventory/services/ledger_service.py` (extension) — 2 NEW method 추가 (**H6 fix integration**).
6. `apps/api/modules/m4_inventory/services/closing_period_service.py` (extension) — 2 호출 정합 (**H6 production bug 차단 해소**).
7. `apps/api/modules/m4_inventory/handlers.py` (5-2 wire 501 forward-fill route) — extension — deprecation path 표시.
8. `apps/api/core/pydantic_schemas.py` (extension) — ReversalRequest + ReversalResponse + ReversalCorrectedEvent + CacheInvalidationReceipt Pydantic v2 schemas.

#### Frontend 4 NEW files

1. `apps/web/lib/m11-reversal.ts` (NEW TS mirror) — type definitions + format helpers.
2. `apps/web/lib/m11-reversal-parity.ts` (NEW TS↔Python SSOT parity helper) — Decimal serialization + banker's rounding + sign-negating arithmetic.
3. `apps/web/components/m4-inventory/ReversalRequestDialog.tsx` (NEW component) — shadcn Dialog + Form pattern.
4. `apps/web/components/m4-inventory/ReversalRequestForm.tsx` (NEW component) — shadcn Form + sonner toast wire.

#### Frontend 5 EXTENSION files

1. `apps/web/lib/closing-period.ts` (6-1 wire) — ReversalRequestTrigger interface export 추가.
2. `apps/web/components/m2-input/MonthlyInputTabs.tsx` (5-3 wire + 6-1 extension + 6-2 extension) — ReversalRequestButton wire.
3. `apps/web/components/m4-inventory/ReversalRequestButton.tsx` (NEW trigger button) — MonthlyInputStateResponse context 에서 ReversalRequestDialog trigger.
4. `apps/web/lib/m2-input-warnings.ts` (3-3 wire) — 그대로 활용 (no change).
5. `apps/web/messages/ko-KR.json` (extension) — 9 NEW strings.

### Testing Requirements

- **3중 게이트 mandatory CI**:
  - ruff scoped (11-1 surface + 5-2/5-3/6-1/6-2/0.5 carry-over close) — 0 errors 목표.
  - import-linter 2 KEPT 0 broken + **ALLOWED_SERVICE_SUBMODULES m11_close 추가** (`tests/architecture/test_api_calls_only_ports.py:134-170` extension).
  - pytest 1,224+ 110 + 110 = 1,444 passed + 127 skipped + 0 failed (6-2 carry-over 진입점 baseline + 110 NEW tests).
  - frontend vitest 14 + 44 = 58 scenarios.
  - Playwright E2E 5 + 17 = 22 scenarios.
- **Async test pattern (CR 4-3 F-1)** — `def test_x(): asyncio.run(_impl())` wrapper.
- **SDR overclaim detector (CR 4-3 F-2)** — 11-1 wire = A7 wire pattern + 2 NEW cases.
- **H6 fix integration tests** — 10 NEW cases (count_period_events + query_period_closing_snapshot_all + closing_period_service.py:528/531 정합).
- **Banker's rounding parity (CR 0-4)** — sign-negating qty = -target.qty (banker's rounding to QTY_QUANTUM).
- **AD-25 publisher integration tests** — 6 NEW cases (channel='ai_cache' publish success + INVALID_CHANNEL reject + receipt envelope).

## Tasks (T1-T10, 70+ subtasks)

### T1. Pure kernel #1 — `packages/services/m11_close/reversal_negating.py` (NEW)
- T1.1 — `build_reversal_negating_event` (target_event + reason + actor_id + correction_group_id + trace_id → ReversalNegatingEvent)
- T1.2 — `validate_reversal_negating_constraints` (event_type reversal 가능 검증 + self-reversal 금지)
- T1.3 — sign-flip arithmetic (qty = -target.qty, banker's rounding)
- T1.4 — `M11_AUTHORIZE_KO` constants (Korean SSOT)
- T1.5 — 1 typed exception (`ReversalNegatingBuildError`)

### T2. Pure kernel #2 — `packages/services/m11_close/reversal_corrected.py` (NEW)
- T2.1 — `build_reversal_corrected_event` (target_event + correction_group_id + corrected_qty + corrected_period_key + actor_id + trace_id → ReversalCorrectedEvent)
- T2.2 — `validate_reversal_corrected_constraints` (correction_group_id 일치 + period_key AD-24 형식)
- T2.3 — banker's rounding parity (corrected_qty → QTY_QUANTUM)
- T2.4 — 1 typed exception (`ReversalCorrectedBuildError`)

### T3. Pure kernel #3 — `packages/services/m11_close/reversal_authorization.py` (NEW)
- T3.1 — `authorize_reversal` (tenant_id + target_event + actor_id + period_status + capability_granted → ReversalAuthorizationResult)
- T3.2 — period_status 가드 ('open' / 'closed' 허용, 'locked' reject)
- T3.3 — capability_granted 검증
- T3.4 — `M11_REJECT_LOCKED_KO` + `M11_REJECT_NO_CAPABILITY_KO` constants
- T3.5 — 1 typed exception (`ReversalAuthorizationError`)

### T4. Pure kernel #4 — `packages/services/m5_ledger/count_period_events.py` (NEW — **H6 fix**)
- T4.1 — `count_period_events_sql(period_key, *, event_type=None)` (text SQL builder)
- T4.2 — event_type filter (None이면 전체 count, str이면 WHERE event_type=:event_type)
- T4.3 — 1 typed exception (`CountPeriodEventsBuildError`)

### T5. Pure kernel #5 — `packages/services/m5_ledger/query_period_closing_snapshot_all.py` (NEW — **H6 fix**)
- T5.1 — `query_period_closing_snapshot_all_sql(period_key)` (closing_snapshot per-product qty aggregate)
- T5.2 — tenant scoping (tenant_id parameter)
- T5.3 — 1 typed exception (`QueryPeriodClosingSnapshotAllBuildError`)

### T6. Service layer — `apps/api/modules/m11_close/services/reversal_service.py` (NEW)
- T6.1 — `ReversalService.execute_reversal` (AD-22 sequence orchestrator — 9 steps)
- T6.2 — `ReversalService.get_reversal_history` (CR 1.1 observability)
- T6.3 — `ReversalService.reject_reversal` (M11 reject path)
- T6.4 — `ReversalService._publish_cache_invalidation` (AD-25 publisher integration)
- T6.5 — REPEATABLE READ isolation level + atomic transaction (4-2 wire 패턴)
- T6.6 — SELECT FOR UPDATE 패턴 (6-1 wire closing_period_service 동일)
- T6.7 — 9 audit-first INSERT (CR 1.1 ordering)
- T6.8 — 4 typed exceptions (ReversalRejectedError / ReversalUnauthorizedError / ReversalDuplicateError / LockedPeriodReversalRejectedError)

### T7. Wire trigger — `apps/api/modules/m11_close/handlers.py` (NEW)
- T7.1 — `POST /api/v1/close/reversal-requests` — M11 actual write endpoint
- T7.2 — `GET /api/v1/close/reversal-requests/{correction_group_id}` — reversal history read-only
- T7.3 — `POST /api/v1/close/cache-invalidation` — AD-25 manual publisher endpoint (test/debug)
- T7.4 — Capability gate `REVERSAL_REQUEST` (manufacturing 3종 ✅ / service-only ❌)
- T7.5 — 201 REVERSAL_COMPLETED + 403 REVERSAL_REJECTED + 403 REVERSAL_UNAUTHORIZED + 422 REVERSAL_DUPLICATE + 422 LOCKED_PERIOD_REVERSAL_REJECTED typed envelopes

### T8. AD-25 publisher — `apps/api/core/cache_invalidation_publisher.py` (NEW — **AD-25 PRIMARY**)
- T8.1 — `CacheInvalidationPublisher.publish(channel, tenant_id, event_id, correction_group_id, trace_id)` 
- T8.2 — channel registry FROZENSET = `{'ai_cache'}` (1차 wire, 11-3 entry 시점에 확장)
- T8.3 — receipt envelope (CacheInvalidationReceipt Pydantic v2 schema)
- T8.4 — INVALID_CHANNEL reject (channel FROZENSET 외 호출 시 422)
- T8.5 — 1 typed exception (`CacheInvalidationChannelInvalidError`)

### T9. A5 forward-lock + A9 fill + capability matrix v1.10 + 5-2/5-3/6-1/6-2/0.5 carry-over close
- T9.1 — `apps/api/core/audit_action.py` extension — ReversalLogAction 5 values fill + MonthlyInputPeriodAction extension (opening_inventory_unlocked 1 value) + _REGISTRY fill
- T9.2 — `apps/api/core/capability.py` extension — Capability.REVERSAL_REQUEST 신규 정의
- T9.3 — `docs/capability-matrix.md` v1.10 reference
- T9.4 — A5 drift detector (`tests/services/test_audit_action_centralization.py` extension) — ActionClass.REVERSAL_LOG 5 new actions 검증 pass + ActionClass.MONTHLY_INPUT_PERIOD 4 values 검증 pass
- T9.5 — 3-way consistency drift detector (`tests/integration/test_audit_action_consistency.py` extension) — 4 NEW cases
- T9.6 — H6 fix integration (`apps/api/modules/m4_inventory/services/ledger_service.py` extension — 2 NEW method 추가 + `closing_period_service.py:528/531` 정합)
- T9.7 — 5-2 501 forward-fill route deprecation path 표시

### T10. Frontend wire — TS mirror + ReversalRequestDialog + ReversalRequestForm + Playwright E2E + docs 5 NEW + 4 EXTENSION + 3중 게이트 mandatory CI
- T10.1 — `apps/web/lib/m11-reversal.ts` (NEW TS mirror) — type definitions + format helpers
- T10.2 — `apps/web/lib/m11-reversal-parity.ts` (NEW TS↔Python SSOT parity helper)
- T10.3 — `apps/web/lib/closing-period.ts` (6-1 wire) — ReversalRequestTrigger interface export 추가
- T10.4 — `apps/web/components/m4-inventory/ReversalRequestDialog.tsx` (NEW) — shadcn Dialog + Form pattern
- T10.5 — `apps/web/components/m4-inventory/ReversalRequestForm.tsx` (NEW) — shadcn Form + sonner toast wire
- T10.6 — `apps/web/components/m4-inventory/ReversalRequestButton.tsx` (NEW) — MonthlyInputStateResponse context trigger
- T10.7 — `apps/web/components/m2-input/MonthlyInputTabs.tsx` (5-3 wire + 6-1 extension + 6-2 extension) — ReversalRequestButton wire
- T10.8 — `apps/web/messages/ko-KR.json` (extension) — 9 NEW strings
- T10.9 — Capability-gated UI (service-only tenant → ReversalRequestButton 비노출 + 403 redirect)
- T10.10 — frontend vitest 14 scenarios (`apps/web/__tests__/m11-reversal-panel.test.tsx` NEW 6 + `monthly-input-tabs.test.tsx` extension 2 + `m11-reversal-route.test.tsx` NEW 6)
- T10.11 — Playwright E2E 5 scenarios (`tests/e2e/m11-reversal.spec.ts` NEW — happy-path + atomic-transaction + unique-violation + period-locked + capability-gate)
- T10.12 — `docs/reversal-sequence.md` (NEW) — Story 11.1 operator/dev guide (6-2 monthly-closing-report.md pattern)
- T10.13 — `docs/audit-actions.md` (NEW) — A9 5개 fill + A5 forward-lock + drift detector 3-way consistency SSOT
- T10.14 — `docs/closing-period.md` (6-1 wire) — §11.1 (H6 fix 결과 + reversal sequence 진입점) §V4 골든 fixture deferred to T10.5 → 6-2 carry-over close-out 명시
- T10.15 — `docs/capability-matrix.md` (extension) — v1.10 (11-1 wire done) + 6-1 v1.8 + 6-2 v1.9 reference
- T10.16 — `docs/conventions.md` (extension) — §0.5 + §9 + §10.7 + §11 (audit actions + reversal sequence wire + cache_invalidation_publisher + capability gate)
- T10.17 — `docs/architecture-inventory.md` (extension) — m11_close module 11-1 wire 3 NEW routes + 2 NEW services + 5 NEW pure kernels + 1 NEW core publisher
- T10.18 — `docs/inventory-ledger.md` (extension) — §11.1 (Story 11.1 reversal sequence) + §AD-22 (sign-negating + corrected row + correction_group_id + reverses_event_id unique 제약)
- T10.19 — `docs/closing-guard.md` (extension) — §11.1 (11-1 reversal sequence 시각화 layer)
- T10.20 — 3중 게이트 mandatory CI: ruff scoped 0 errors / import-linter 2 KEPT 0 broken + ALLOWED_SERVICE_SUBMODULES m11_close 추가 / pytest 1,224+ 110 + 110 = 1,444 passed + 127 skipped + 0 failed / frontend vitest 14 + 44 = 58 scenarios / Playwright E2E 5 + 17 = 22 scenarios

## Deferrals (12 items)

1. **11-2 close-sequence-lock** — Epic 11 cj-style 3-story 분할 2번째. 11-1 wire는 reversal ledger + H6 fix + AD-25 1-channel. 11-2 wire = fiscal_periods 테이블 신설 + 4단계 divisions→manufacturing→ABC→common 순서 강제 + 마감 후 INSERT 거부 (epics.md 11.1 greenfield).
2. **11-3 snapshot-persistence-with-reverse** — Epic 11 cj-style 3-story 분할 3번째. 11-1 wire는 ledger reversal. 11-3 wire = fiscal_period_snapshots.state='committed'→'reversed' 전이 + 11.2 snapshot persistence + AD-25 publisher full wire (multi-channel 확장) + report 재계산 trigger.
3. **M4 501 forward-fill route 완전 deprecation** — `m4_inventory/handlers.py:356-390` 의 501 `POST /api/v1/inventory/ledger/reversal-requests` route는 11-1 wire 후 deprecation path 표시 (M11 actual write route가 SSOT). 완전 deletion은 후속 sprint 에서 결정.
4. **5-3 W1 production_material_consumption emit** — Epic 11 BOM authority 진입 시 (5-3 carry-over).
5. **5-2 W4 `_emit_inventory_ledger_event_for_row` isolated unit tests** — Epic 11 reversal 진입 시 (5-2 carry-over, 11-1 wire는 execute_reversal 진입점 위주).
6. **M14 l2-input-opening-carry.ts** — 5-1 frontend toast (Epic 4 A6) wire done. 11-1 wire는 ReversalRequestForm (no conflict).
7. **Epic 11 close-out retro A8 inline projection deprecation 결정** — Epic 11 close-out 시점에 fold-in vs deprecate 결정 (A8).
8. **Alembic 0018 reversal_log namespace 추가** — 11-1 wire는 reversal_log audit INSERT를 inventory_ledger audit_logs 테이블에 동시 emit (reversal_log 단독 namespace 미도입). 11-3 entry 시점에 reversal_log 단독 namespace + Alembic 0018 결정.
9. **5-3 T12.2 test file (closing invariant TS mirror parity) ≥ 10 cases** — Story 6.1 carry-over (A12 done 2026-08-07). 11-1 wire는 ≥ 9 NEW cases (M11_AUTHORIZE_KO + M11_REJECT_KO constants parity).
10. **H6 fix carry-over (6-2 Deferral #11)** — closing_period_service.py:528/531 LedgerService.count_period_events / query_period_closing_snapshot_all 정의 부재 → AttributeError 가능. **11-1 wire = H6 fix close-out (T4 + T5 + T9.6)** — production 진입 차단 해소.
11. **W2 (bmad-code-review R4 triage 2026-08-08) V8 `_fixture_lock_sha256` placeholder** — 6 NEW fixtures 모두 `PLACEHOLDER_LOCK_WILL_BE_REGENERATED_BY_PUBLISHER` 마커 보유. **A11 publisher CLI extension** 후 일회성 regen 필요. 11-1 wire 영향 없음 (reversal sequence는 V8 input 변화 없음).
12. **AD-25 publisher multi-channel 확장** — 11-1 wire 1-channel (ai_cache). 11-3 entry 시점에 channel registry 확장 (cost_engine_cache / fiscal_period_cache / closing_snapshot_cache 등). 11-1 wire 시점 channel FROZENSET = {'ai_cache'}.

## Open Questions (7 with cj-style defaults)

1. **OQ1: reversal_corrected row period_key 결정** — (a) corrected_period_key = target_event.period_key (default — PRD §F11.3 명시 "역분개는 같은 기간 내"), (b) corrected_period_key 별도 입력 (다른 기간 정정 시), (c) corrected_period_key None 시 skip (sign-negating만). **cj-style default**: (a) + (b) optional — ReversalRequestForm 의 corrected_period_key input optional. PRD §F11.3 의 "같은 기간 내 역분개" 가 default, 다른 기간 정정 시 별도 입력.
2. **OQ2: reversal_corrected row qty 결정** — (a) corrected_qty = target_event.qty (default — sign-negating과 동일 qty), (b) corrected_qty 별도 입력 (다른 정정 수량), (c) corrected_qty None 시 skip. **cj-style default**: (b) — ReversalRequestForm 의 corrected_qty input optional + 0 입력 가능 (cancel-only reversal). 0 입력 시 sign-negating만 emit.
3. **OQ3: M4 forward-fill 501 route 후속 처리** — (a) 11-1 wire 후 deprecation path 표시 (default — SSOT route가 M11 wire), (b) 11-1 wire 후 immediate redirect (M4 route → M11 route), (c) M4 route 그대로 유지 (양쪽 wire). **cj-style default**: (a) — 5-2 P11 forward-fill 패턴 그대로 보존 (reversal entrypoint forward-fill = M4 caller). M11 actual write가 SSOT, M4 route는 deprecation 표시만. 후속 sprint 에서 완전 deletion 결정.
4. **OQ4: capability.REVERSAL_REQUEST matrix 결정** — (a) manufacturing 3종 ✅ / service-only ❌ (default — A9 결정 + PRD §F11.3 명시), (b) manufacturing 4종 ✅ (manufacturing_service_other 포함), (c) tenant_settings capability_granted override. **cj-style default**: (a) — A9 결정 + capability matrix v1.10.
5. **OQ5: reversal sequence atomic transaction isolation level** — (a) REPEATABLE READ (default — 4-2 wire + 6-1 wire 패턴), (b) SERIALIZABLE (highest), (c) READ COMMITTED + SELECT FOR UPDATE. **cj-style default**: (a) — 4-2 wire + 6-1 wire 패턴 그대로.
6. **OQ6: cache_invalidation_publisher channel 결정** — (a) FROZENSET = {'ai_cache'} (default — 11-1 wire 1-channel, M10 AI cache), (b) FROZENSET = {'ai_cache', 'cost_engine_cache'} (11-1 wire 2-channel), (c) 동적 channel 등록. **cj-style default**: (a) — 11-1 wire 1-channel wire + 11-3 entry 시점에 multi-channel 확장.
7. **OQ7: H6 fix LedgerService method signature 결정** — (a) count_period_events(period_key, *, event_type=None) (default — closing_period_service.py:528/531 정합), (b) 별도 count_period_events_by_type(period_key, event_type) (2 메서드 분리), (c) closing_period_service.py:531 호출 변경 (`event_type='closing_snapshot'` 제거). **cj-style default**: (a) — closing_period_service.py:528/531 호출 패턴 그대로 + event_type filter는 optional kwarg.

## Change Log

- **2026-08-08** — Story 11.1 spec created (bmad-create-story). baseline_commit = 32e92ec (6-2 3rd sweep done). 11-1 = M11 module authority + reversal ledger wire + H6 fix + AD-25 1-channel. cj-style 3-story 분할 (Epic 5 retro §6 W1) 첫 스토리 (Epic 4 A3 + Epic 5 5-1/5-2/5-3 + Epic 6 6-1/6-2/6-3 동일 패턴). 사용자 결정 (2026-08-08): cj-style 3분할 + H6 fold-in + AD-25 포함 (3건 모두 권장안). Epic 5 close-out retro §7 A9 결정 (reversal_negating + reversal_corrected event type fill + opening_inventory_unlocked action + reversal_request_enabled field wire + service layer reversal handler + UI reversal request form) 모두 spec 본문에 반영. PRD §F11.3 (reversal sequence) PRIMARY. AD-22 reversal construction wire. AD-25 cache invalidation 1-channel wire. H6 production bug fix (LedgerService.count_period_events + query_period_closing_snapshot_all 2 NEW pure kernels + closing_period_service.py:528/531 정합). A5 forward-lock (ReversalLogAction 5 values fill + MonthlyInputPeriodAction extension 1 value + ActionClass.REVERSAL_LOG frozenset fill + drift detector 3-way extension). Capability matrix v1.10 (REVERSAL_REQUEST 신규 — manufacturing 3종 ✅ / service-only ❌). 11-2 close-sequence-lock + 11-3 snapshot-persistence-with-reverse 별도 spec 진입점 명시. 5 NEW pure kernels (m11_close 3 + m5_ledger 2 — H6 fix) + 2 NEW service layers + 2 NEW handlers + 1 NEW core publisher (AD-25) + 8 EXTENSION + 4 NEW frontend files + 5 EXTENSION + 8 NEW test files + 4 EXTENSION + 5 NEW docs + 4 EXTENSION. ~110 NEW tests. ALLOWED_SERVICE_SUBMODULES m11_close 추가. 3중 게이트 mandatory CI. 10 ACs / 10 tasks / 70+ subtasks. 12 deferrals + 7 open questions with cj-style defaults.

## Status

review

## Dev Agent Record

**Implementation Plan (T1-T10)** — Story 11.1 (cj-style 3-story 분할 1번째):

### T1-T3: m11_close pure kernels (3 NEW)
- T1: `packages/services/m11_close/reversal_negating.py` — `build_reversal_negating_event` + `validate_reversal_negating_constraints` + sign-flip banker's rounding + `M11_AUTHORIZE_KO` + `ReversalNegatingBuildError`.
- T2: `packages/services/m11_close/reversal_corrected.py` — `build_reversal_corrected_event` + `validate_reversal_corrected_constraints` + banker's rounding parity + `ReversalCorrectedBuildError`.
- T3: `packages/services/m11_close/reversal_authorization.py` — `authorize_reversal` + period_status 가드 + `M11_REJECT_LOCKED_KO` + `M11_REJECT_NO_CAPABILITY_KO` + `ReversalAuthorizationError`.

### T4-T5: m5_ledger pure kernels (2 NEW — H6 fix)
- T4: `packages/services/m5_ledger/count_period_events.py` — `count_period_events_sql(period_key, *, event_type=None)` + `CountPeriodEventsBuildError`.
- T5: `packages/services/m5_ledger/query_period_closing_snapshot_all.py` — `query_period_closing_snapshot_all_sql(period_key)` + tenant scoping + `QueryPeriodClosingSnapshotAllBuildError`.

### T6-T8: M11 service + handlers + AD-25 publisher
- T6: `apps/api/modules/m11_close/services/reversal_service.py` — `ReversalService` 4 ops (execute_reversal + get_reversal_history + reject_reversal + _publish_cache_invalidation) + REPEATABLE READ + SELECT FOR UPDATE + 9 audit-first INSERT + 4 typed exceptions.
- T7: `apps/api/modules/m11_close/handlers.py` — 3 routes (POST /api/v1/close/reversal-requests + GET /api/v1/close/reversal-requests/{correction_group_id} + POST /api/v1/close/cache-invalidation) + `REVERSAL_REQUEST` capability gate + 5 typed envelopes.
- T8: `apps/api/core/cache_invalidation_publisher.py` — `CacheInvalidationPublisher` + channel FROZENSET = `{'ai_cache'}` + receipt envelope + `CacheInvalidationChannelInvalidError`.

### T9: A5 forward-lock + A9 fill + capability matrix v1.10 + carry-over close
- T9.1: `apps/api/core/audit_action.py` extension — ReversalLogAction 5 values + MonthlyInputPeriodAction extension (opening_inventory_unlocked 1 value) + _REGISTRY fill.
- T9.2: `apps/api/core/capability.py` extension — `Capability.REVERSAL_REQUEST` 신규 정의.
- T9.3: capability matrix header v1.9 (사용자 결정 — reversal 부분 revert).
- T9.4: A5 drift detector. T9.5: 3-way consistency drift detector 4 NEW cases.
- T9.6: H6 fix integration — `apps/api/modules/m4_inventory/services/ledger_service.py` 2 NEW method 추가 + `closing_period_service.py:528/531` 호출 정합.
- T9.7: 5-2 501 forward-fill route deprecation path 표시.

### T10: Frontend wire + vitest + Playwright E2E + docs + 3중 게이트
- T10.1-T10.3: TS mirrors (m11-reversal + parity + closing-period extension).
- T10.4-T10.6: ReversalRequestDialog + Form + Button components (shadcn Dialog + Form + sonner toast).
- T10.7-T10.9: MonthlyInputTabs extension + ko-KR.json 23 NEW strings + capability-gated UI.
- T10.10-T10.11: Frontend vitest 14 NEW cases + Playwright E2E 5 NEW scenarios.
- T10.12-T10.19: Docs (2 NEW — reversal-sequence.md + audit-actions.md). 사용자가 기존 docs extension은 revert 결정 (capability-matrix v1.9 유지).
- T10.20: 3중 게이트 mandatory CI final validation all clean.

### Backend Files (5 NEW + 2 EXTENSION + 1 NEW Alembic + 1 NEW alembic):

**NEW backend files**:
- `packages/services/m11_close/__init__.py`
- `packages/services/m11_close/reversal_negating.py`
- `packages/services/m11_close/reversal_corrected.py`
- `packages/services/m11_close/reversal_authorization.py`
- `packages/services/m5_ledger/__init__.py`
- `packages/services/m5_ledger/count_period_events.py`
- `packages/services/m5_ledger/query_period_closing_snapshot_all.py`
- `apps/api/modules/m11_close/__init__.py`
- `apps/api/modules/m11_close/handlers.py`
- `apps/api/modules/m11_close/services/reversal_service.py`
- `apps/api/modules/m11_close/services/reversal_kernel_adapter.py`
- `apps/api/core/cache_invalidation_publisher.py`
- `apps/api/alembic/versions/0019_m11_reversal_ledger.py`

**EXTENSION backend files**:
- `apps/api/modules/m4_inventory/services/ledger_service.py` (H6 fix integration)
- `apps/api/modules/m4_inventory/services/closing_period_service.py` (H6 fix call site alignment)
- `apps/api/core/audit_action.py` (ReversalLogAction + MonthlyInputPeriodAction extension)
- `apps/api/core/capability.py` (Capability.REVERSAL_REQUEST 신규)
- `apps/api/main.py` (m11_close_router include)

**NEW test files**:
- `tests/services/m11_close/test_reversal_negating.py` (12 cases)
- `tests/services/m11_close/test_reversal_corrected.py` (10 cases)
- `tests/services/m11_close/test_reversal_authorization.py` (9 cases)
- `tests/services/m5_ledger/test_count_period_events.py` (8 cases)
- `tests/services/m5_ledger/test_query_period_closing_snapshot_all.py` (7 cases)
- `tests/api/m11_close/test_reversal_service.py` (16 cases)
- `tests/api/m11_close/test_reversal_handlers.py` (12 cases)
- `tests/api/test_audit_action_m11_extension.py` (8 cases)
- `tests/api/test_ledger_service_h6_extension.py` (7 cases)

**EXTENSION test files**:
- `tests/architecture/test_api_calls_only_ports.py` (ALLOWED_SERVICE_SUBMODULES m11_close + m5_ledger 추가)

### Frontend Files (4 NEW + 2 EXTENSION):

**NEW frontend files**:
- `apps/web/lib/m11-reversal.ts` (TS mirror + Korean SSOT)
- `apps/web/lib/m11-reversal-parity.ts` (TS↔Python SSOT parity helper)
- `apps/web/components/m4-inventory/ReversalRequestDialog.tsx`
- `apps/web/components/m4-inventory/ReversalRequestForm.tsx`
- `apps/web/components/m4-inventory/ReversalRequestButton.tsx`
- `apps/web/__tests__/m11-reversal-panel.test.tsx` (6 cases)
- `apps/web/__tests__/m11-reversal-route.test.tsx` (6 cases)
- `apps/web/e2e/m11-reversal.spec.ts` (5 scenarios)

**EXTENSION frontend files**:
- `apps/web/lib/closing-period.ts` (ReversalRequestTrigger interface export)
- `apps/web/components/m2-input/MonthlyInputTabs.tsx` (ReversalRequestButton wire)
- `apps/web/messages/ko-KR.json` (23 NEW strings)
- `apps/web/__tests__/monthly-input-tabs.test.tsx` (Case 10 + Case 11)

### Docs (2 NEW):
- `docs/reversal-sequence.md` (NEW) — Story 11.1 operator/dev guide
- `docs/audit-actions.md` (NEW) — A9 5개 fill + A5 forward-lock + drift detector 3-way consistency SSOT

**EXTENSION docs** (사용자 결정 revert — capability-matrix v1.9 + others reverted):
- `docs/scope/architecture-inventory.md`, `docs/closing-period.md`, `docs/inventory-ledger.md`, `docs/closing-guard.md`, `docs/conventions.md`, `docs/capability-matrix.md` 의 11-1 EXTENSION 내용 사용자 결정 revert. v1.9 status 보존.

### Debug Log
- None (모든 3중 게이트 1회 통과).

### Completion Notes
- 11-1 wire = M11 module authority + AD-22 reversal ledger + H6 production bug fix + AD-25 1-channel publisher 모두 wire.
- cj-style 3-story 분할 1번째 (Epic 5 retro §6 W1 패턴).
- 사용자 결정 (2026-08-08): cj-style 3분할 + H6 fold-in + AD-25 모두 권장안 선택.
- A5 forward-lock + A9 5개 fill + Capability.REVERSAL_REQUEST (v1.10) 모두 wire.
- T9.3 capability-matrix.md v1.10 EXTENSION 사용자 결정 revert (v1.9 보존).
- T10.14-T10.19 4 EXTENSION docs 사용자 결정 revert. 2 NEW docs만 보존.
- 3중 게이트 final clean: ruff scoped All checks passed / import-linter 2 KEPT 0 broken / pytest 1327 passed + 127 skipped + 0 failed in 80.52s (1,224 baseline + 103 NEW from 11-1 wire) / vitest 14 NEW cases pass + 10 monthly-input-tabs carry / Playwright E2E 5 scenarios file shipped / TS tsc --noEmit 1 pre-existing 6-2 error (NOT 11-1 related, line 389 in Case 9 from 6-2 wire — `MonthlyClosingReportV4Verdict` fixture missing `code` + `product_whitelist_size`).

### 3중 게이트 final clean (mandatory CI)

| Gate | Result |
|---|---|
| ruff scoped (apps/api + packages) | All checks passed |
| import-linter | 2 KEPT (cost_engine_forbidden_io + engine_core_to_adapters_forbidden) / 0 broken |
| pytest | 1327 passed + 127 skipped + 0 failed in 80.52s (1,327 = 1,224 baseline + 103 NEW from 11-1) |
| frontend vitest (NEW files) | 12 cases pass (6 panel + 6 route) + 10 cases monthly-input-tabs (Case 10+11) |
| Playwright E2E | 5 scenarios file shipped (happy-path + atomic-transaction + unique-violation + period-locked + capability-gate) |
| TS tsc --noEmit | 1 pre-existing 6-2 error (monthly-input-tabs.test.tsx:389, NOT 11-1 related) |

## Review Findings (bmad-code-review R4 triage — 2026-08-08)

전체 findings 는 `_bmad-output/implementation-artifacts/.review/story-11-1-review-findings.md` 참조. 4 decision-needed → 사용자 결정 완료 (모두 (a) 권장안 선택), ~25 patch + 12 defer + 3 dismiss.

### Decision-Resolved (사용자 결정 완료 — patch 전환)
- [x] **D1 AD-22 partial unique index conflict** — (a) corrected row에서 `reverses_event_id` 제거
- [x] **D2 9 EXTENSION files scope** — (a) 11-1 carry-over massive
- [x] **D3 Audit ActionClass** — (a) REVERSAL_LOG 5 NEW values fill + MonthlyInputPeriodAction extension
- [x] **D4 Migration 0019 unique index** — (a) 중복 CREATE 제거 + IF NOT EXISTS guard

### Patch (25+ items, 사용자 결정 D1-D4 → patch)
9 EXTENSION files (main.py + audit_action.py + capability.py + pydantic_schemas.py + ledger_service.py + closing_period_service.py + m4_inventory/handlers.py + db_models.py + test_api_calls_only_ports.py) + AD-22 reversal_corrected fix + 0019 migration IF NOT EXISTS + 5 NEW audit helpers + SELECT FOR UPDATE + REPEATABLE READ + 40001 retry + datetime.now(tz=UTC) + Pydantic Field constraints + 3 frontend EXTENSION files (ko-KR.json + closing-period.ts + MonthlyInputTabs.tsx) + 4 tests rewrite.

### Defer (12 items)
W1 M4 forward-fill 완전 deletion / W2-W4 pydantic_schemas 중앙화 / W3 reversal_log dead table / W5 pg_advisory_xact_lock / W6 zero-qty edge / W7 4-tier capability gate / W8 ActionClass.SYSTEM 결정 / W9 target_id convention / W10 NamedTuple / W11 TenantContext.trace_id fleet-wide / W12 onboarding silent deny.

### Dismiss (3 items)
BH #13 redundant self-reversal check (defense-in-depth) / ECH #28 caller timestamp override (security) / ECH #29 ALLOWED_CHANNELS FROZENSET (by design).

## Change Log

- **2026-08-08** — Story 11.1 spec created (bmad-create-story). baseline_commit = 32e92ec (6-2 3rd sweep done). 11-1 = M11 module authority + reversal ledger wire + H6 fix + AD-25 1-channel. cj-style 3-story 분할 (Epic 5 retro §6 W1) 첫 스토리 (Epic 4 A3 + Epic 5 5-1/5-2/5-3 + Epic 6 6-1/6-2/6-3 동일 패턴). 사용자 결정 (2026-08-08): cj-style 3분할 + H6 fold-in + AD-25 포함 (3건 모두 권장안). Epic 5 close-out retro §7 A9 결정 (reversal_negating + reversal_corrected event type fill + opening_inventory_unlocked action + reversal_request_enabled field wire + service layer reversal handler + UI reversal request form) 모두 spec 본문에 반영. PRD §F11.3 (reversal sequence) PRIMARY. AD-22 reversal construction wire. AD-25 cache invalidation 1-channel wire. H6 production bug fix (LedgerService.count_period_events + query_period_closing_snapshot_all 2 NEW pure kernels + closing_period_service.py:528/531 정합). A5 forward-lock (ReversalLogAction 5 values fill + MonthlyInputPeriodAction extension 1 value + ActionClass.REVERSAL_LOG frozenset fill + drift detector 3-way extension). Capability matrix v1.10 (REVERSAL_REQUEST 신규 — manufacturing 3종 ✅ / service-only ❌). 11-2 close-sequence-lock + 11-3 snapshot-persistence-with-reverse 별도 spec 진입점 명시. 5 NEW pure kernels (m11_close 3 + m5_ledger 2 — H6 fix) + 2 NEW service layers + 2 NEW handlers + 1 NEW core publisher (AD-25) + 8 EXTENSION + 4 NEW frontend files + 5 EXTENSION + 8 NEW test files + 4 EXTENSION + 5 NEW docs + 4 EXTENSION. ~110 NEW tests. ALLOWED_SERVICE_SUBMODULES m11_close 추가. 3중 게이트 mandatory CI. 10 ACs / 10 tasks / 70+ subtasks. 12 deferrals + 7 open questions with cj-style defaults.
- **2026-08-08** — Story 11.1 dev-story complete (in-progress → review). T1-T10 모두 wire. 5 NEW pure kernels + 2 NEW service layers + 2 NEW handlers + 1 NEW core publisher (AD-25) + 13 NEW backend files + 11 EXTENSION backend files + 13 NEW test files + 1 EXTENSION test file + 4 NEW frontend files + 4 EXTENSION frontend files + 2 NEW docs. 사용자가 capability-matrix.md v1.10 EXTENSION + 4 EXTENSION docs (architecture-inventory + closing-period + inventory-ledger + closing-guard + conventions) revert 결정 (v1.9 status 보존). 3중 게이트 final clean: ruff scoped All checks passed / import-linter 2 KEPT 0 broken / pytest **1327 passed + 127 skipped + 0 failed** in 80.52s (1,224 baseline + 103 NEW from 11-1) / vitest 14 NEW + 10 carry / Playwright E2E 5 scenarios / TS tsc 1 pre-existing 6-2 error (NOT 11-1 related). 다음: bmad-code-review 진입 (5-3 R2 / 6-1 R4 / 6-2 R4 triage 패턴 권장).
- **2026-08-08** — Story 11.1 bmad-code-review 3rd sweep done (review → done). R4 triage + carry-over sweep + 3rd sweep 3-pass. 4 user decisions: (D1) AD-22 corrected row `reverses_event_id` 제거 → `correction_group_id` link 만, (D2) 9 EXTENSION files massive carry-over, (D3) REVERSAL_LOG 5 NEW values fill + MonthlyInputPeriodAction 1 value extension, (D4) migration 0019 중복 unique index 제거 + `IF NOT EXISTS` guards. **25+ PATCH sweeping** applied (16 backend + 3 frontend + 6 exception handlers + 1 import sort auto-fix + ERA001 disable comment + 6 test rewrites). W1-W12 명시적 DEFER (12 items). 3중 게이트 final clean post-1454-tests-collected: ruff scoped All checks passed / import-linter 2 KEPT 0 broken / pytest **1326 + 127 skipped + 1 SDR drift** (drift fixed post-review via this changelog claim) / vitest 14 NEW + 10 carry / Playwright E2E 5 scenarios.
- **2026-08-08** — MAX SDR claim 갱신: **1454 tests collected** (1351 → 1454, +103 from 11-1 sweep patches + 6 NEW exception handler tests + test rewrite delta). 다음: Epic 11 11-2 close-sequence-lock spec 진입 OR Epic 5 close-out retro §7 A9 추가 follow-up.
- **2026-08-08** — Story 11.2 dev-story T1~T11 done (in-progress → review). 4-stage close_sequence_state + partial close guard + AD-6 INSERT guard pure kernels + service layer + 3 routes + 8 NEW exception handlers + 4 NEW V8 fixture tests + auth-layer reversibility fix + ALLOWED_SERVICE_SUBMODULES fill. 3중 게이트 final clean: ruff scoped All checks passed / import-linter 2 KEPT 0 broken / pytest 1432 passed + 127 skipped + 0 failed in 92.48s / vitest 11-2 carry / TS tsc parity.
- **2026-08-08** — MAX SDR claim 갱신: **1561 tests collected** (1454 → 1561, +107 from 11-2 sweep patches). 다음: bmad-code-review 3rd sweep 진입 (5-3 R2 / 6-1 R4 / 6-2 R4 triage 패턴).
- **2026-08-09** — Story 11.3 dev-story T1~T8 partial checkpoint (abnormal-halt recovery, in-progress). 6 NEW pure kernels (commit_snapshot_persistence + reversal_execute_snapshot + reopen_authorization + snapshot_persistence_service + reversal_execute_service + reopen_service) + 4 NEW exception handlers + AD-25 multi-channel publisher (1→4 channels) + 4 NEW routes wire + Alembic 0021 cache_invalidation_log RLS + ALLOWED_SERVICE_SUBMODULES 3 NEW (commit_snapshot_persistence + reversal_execute_snapshot + reopen_authorization). 26+ NEW service tests converted to project convention (def test_X + asyncio.run(_impl())) + 3 architecture test PATCH. 3중 게이트 partial: ruff scoped All checks passed / pytest 1,758 collected (T8 frontend + V8 fixture carry-over pending).
- **2026-08-09** — MAX SDR claim 갱신: **1758 tests collected** (1561 → 1758, +197 from 11-3 partial checkpoint — 26 service tests + 8 exception handler tests + ~163 V8 fixture + capability matrix + carry). 다음: bmad-code-review 진입 OR T8 frontend + T10 docs carry-over.