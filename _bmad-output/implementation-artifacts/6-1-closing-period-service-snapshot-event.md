---
baseline_commit: 74f3a30
target_key: 6-1-closing-period-service-snapshot-event
epic: 6
story_id: 6.1
title: Closing Period Service + closing_snapshot Ledger Event Wire
status: ready-for-dev
---

# Story 6.1: Closing Period Service + closing_snapshot Ledger Event Wire

Status: ready-for-dev

> Epic 6 첫 스토리. Epic 5 5-1 (opening auto-carry chain) + 5-2 (inventory_ledger append-only events, `closing_snapshot` 11번째 event_type) + 5-3 (closing_guard + V3 verification + frontend banner) 위에 additive: ① PRD §F4.3 (월 마감 E2E — closing_period 서비스로 closing 시점 ledger aggregate 영구화) + §F5 (마감 보고서 입력 source = closing_snapshot ledger events) + §V4 (closing period verification = closing snapshot 일관성 + invariant 양쪽 검증) wire contract ② Story 0.5 plumbing + 5-3 frontend close-time guard 진입점 위에 additive (ClosingGuardBanner → ClosingPeriodConfirmationPanel 확장) ③ 5-1/5-2/5-3 backend carry-over (closing_guard pure kernel + closing_guard_service + V3 verifier + ledger aggregate + A5 forward-lock + A7 wire) 그대로 보존 + 6-1 wire contract 추가.
>
> **baseline_commit = 74f3a30** (A12 close-out tip + Epic 5 close-out 완료). Epic 5 close-out retro §6 결정 (cj-style 6-1/6-2/6-3 분할) + Epic 5 retro §7 A8 (Epic 6 close-out 시점에 Epic 3.3 inline projection 제거 — 5-2 commit + 1 epic maintenance window 종료) + A10 (MONTHLY_CLOSING_REPORT capability 신규 — manufacturing 3종 ✅ / service-only ❌, `docs/capability-matrix.md` v1.3 동반) spec 본문에 반영. **Epic 6 진입점**: closing_period service = AD-2 append-only ledger write 진입 + AD-4 atomicity close-time hook 위에 additive + AD-6 fiscal-period close lock (5-3 wire와 동일 lock semantics 보존) + AD-22 reversal entrypoint (closing_snapshot은 Epic 11 reversal module의 wire contract 진입점 — `reversal_negating` + `reversal_corrected` event type fill).

<!-- dev-context: Epic 5 close-out retro (2026-08-07) — Epic 5 셋 다 done (5-1 + 5-2 + 5-3 + 0.5 plumbing + A5 + A7). 3-story 분할 패턴 (cj-style) Epic 4 close-out A3 결정 정합 검증 완료. A12 T12.2 test file deferred close-out done (closing invariant TS mirror parity, commit 74f3a30). Epic 5 회고 §6 명시: 6-1 = Closing Period Service + closing_snapshot ledger event wire. 6-2 = Monthly Closing Report (capability gate MONTHLY_CLOSING_REPORT 신규 — A10 결정). 6-3 = Closing PDF Export + ko-KR labels.

Epic 4 close-out retro (2026-08-03) A3 cj-style — 3-story 분할 유지 (5-1 → 5-2 → 5-3) + inline projection deprecation = 5-2 commit 완료 + Epic 6 close-out 시점에 legacy path 제거 (Epic 5 retro §7 A8 결정, 6-1 spec 본문 §A8 명시). Epic 4 close-out retro A4 — frontend toast = 0.5 plumbing 별도 Story (5-3 진입 전 완료). ✅ done.
Epic 4 close-out retro A5 — A5 Full Phase 1+2+4 done. Epic 5 5-1 + 5-3 audit log 일관성 보장 + A5 forward-lock + drift detector pattern 정착. 6-1 wire 동일 패턴 적용.
Epic 4 close-out retro A6 — 0.5 plumbing = 5-3 spec 진입 전 dep. ✅ done 2026-08-05 (commit ead1974) — shadcn Tabs / sonner / vitest / Playwright 4종 wire. 6-1 frontend ClosingPeriodConfirmationPanel 진입점 가능.
Epic 4 close-out retro A7 — Epic 4 carry (async test pattern + SDR overclaim) Epic 5 wire. 6-1 동일 적용.

Story 0.5 (2026-08-05) — frontend plumbing wire ✅ done. shadcn Tabs / sonner / vitest + RTL + MSW / Playwright + next-intl + INDUSTRY_ICON fill + 10 ACs all green. **6-1 frontend 진입 전 dep satisfied**. docs/frontend-toolchain.md v1.0 SSOT.

Story 0-2 (2026-07-29) — RLS 인프라 + audit_logs INSERT-only with `BEFORE UPDATE OR DELETE` trigger 패턴이 Epic 0에서 wire됨. AD-2 + AD-3 SSOT. 6-1 wire는 RLS 위에서 동작.

Story 1.1 (2026-07-29) — Industry enum SSOT (manufacturing / manufacturing_service / service / manufacturing_service_other) + capability matrix v1.0. 6-1 capability gate = 신규 정의 `MONTHLY_CLOSING_REPORT` (A10 결정 — manufacturing 3종 ✅ / service-only ❌). `docs/capability-matrix.md` v1.2 → v1.3 동반.

Story 2.2 (2026-08-01) — BOM matrix 100% validation + sonner toast swap. 6-1 BOM data 활용 (5-3 W1 BOM-aware reconciliation 결과 — production_output_inbound + production_material_consumption ledger events는 closing_period snapshot 산출 시점에 BOM matrix join 활용).

Story 3.1 (2026-08-01) — monthly_input_periods + monthly_input_rows 테이블 (Alembic 0009). 6-1 close-time hook 진입점 (`monthly_input_periods.status='closing'` 시 closing_snapshot emit).

Story 3.3 (2026-08-01) — `monthly_input_periods.opening_inventory` JSONB column (Alembic 0011) + `MonthlyInputStateResponse.warnings` + `is_blocked` + `top_n_severity` 4 fields + F2.3 음수재고 입력 시 즉시 경고. **Epic 5 retro §7 A8 — Epic 3.3 inline projection deprecation timeline 명시: 6-1 spec 본문에서 5-2 commit + 1 epic maintenance window 종료 시점 = Epic 6 close-out 시점에 inline projection 제거 결정**.

Story 4.1 (2026-08-02) — engine returns state='draft' (AD-22 boundary strengthening). 6-1 closing period service = service layer ownership (engine은 closing_period 의미 모름).

Story 4.2 (2026-08-03) — REPEATABLE READ + audit-first (CR 1.1) + calc_log + AD-22 state transition + is_blocked close-time hook (Epic 3 A4). **6-1 wire는 4-2 close-time hook 위에 additive**: closing_period snapshot 시점 ledger emit.

Story 4.3 (2026-08-03) — V1·V4·V7·V8 verification + verdict + A5 forward-lock + Industry enum SSOT. **6-1 wire는 V3 (5-3 wire) + V4 (6-1 wire 신규 = closing snapshot 일관성 verification) verification surface 위에 additive**.

Story 4.4 (2026-08-03, commit 80f4494) — A5 forward-lock (verify_v8_golden_match + Alembic 0014 verification_log CHECK 4-value expansion) + 12 fixture matrix. V4 placeholder가 4-4 골든 fill 시점에 포함 (closing snapshot 일관성).

Story 5.1 (2026-08-04, commit b4b84da) — opening_carry_chain wire + 4 hooks into monthly_input_service + 2 audit actions under ActionClass.MONTHLY_INPUT_PERIOD + INVENTORY_LEDGER class placeholder 전가 + 4 hooks. **5-1 carry-over to 6-1**: opening_inventory JSONB → closing_period snapshot 시점 read-only aggregate.

Story 5.2 (2026-08-04, commit 7a13eb9) — inventory_ledger append-only events + 4 routes + 11 values event_type CHECK + PostgreSQL BEFORE UPDATE OR DELETE row-level trigger + AD-22 reversal entrypoint forward-fill + A5 6 values fill. **5-2 carry-over to 6-1**: (a) `closing_snapshot` 11번째 event_type = 6-1 wire 진입점, (b) `reverses_event_id` UNIQUE 보존 = closing_snapshot correction 시 Epic 11 reversal module wire contract, (c) `idempotency partial UNIQUE` 보존 = closing_period snapshot 멱등성.

Story 5.3 (2026-08-06, commit 079f6a7) — closing_guard pure kernel + closing_guard_service + 3 routes + MonthlyInputStateResponse 5 NEW fields + 6 NEW frontend files + 3 vitest scenarios + 32 patches P1-P32 (3 sweeps). **5-3 carry-over to 6-1**: (a) closing_guard pure kernel (compute_closing_balance_per_product + classify_closing_invariant + is_close_blocked) = closing_period snapshot 산출 시점에 pure kernel #1 호출, (b) closing_guard_service.evaluate_closing_guard = closing_period snapshot 검증 진입점, (c) V3 verification verifier = closing_period verification surface 진입점, (d) `closing_guard_audit_trail` field (MonthlyInputStateResponse 5 NEW fields 중 1개) = closing_period audit log emission trace, (e) ClosingGuardBanner frontend = ClosingPeriodConfirmationPanel 확장 진입점.

A12 (2026-08-07, commit 74f3a30) — T12.2 test file deferred close-out done. `tests/api/m2_input/test_monthly_input_state_extension.py` (9 cases CI-shim) + `apps/web/__tests__/closing-guard-banner.test.tsx` Case 6 TS/Python SSOT parity. Epic 5 close-out retro §7 A12 close-out 완료.

A8 (Epic 5 retro §7 결정, 2026-08-07) — Epic 3.3 inline projection deprecation timeline: Epic 6 close-out 시점에 inline projection 제거 (5-2 commit + 1 epic maintenance window 종료 시점). 6-1 spec 본문 §A8 timeline 명시. Epic 6 6-1 wire는 inline projection 보존 상태로 wire (1 epic maintenance window 진행 중), Epic 6 close-out 시점에 fold-in 결정.

A10 (Epic 5 retro §7 결정, 2026-08-07) — Epic 6 reporting capability 신규 정의: `MONTHLY_CLOSING_REPORT` capability 신규 (manufacturing / manufacturing_service / manufacturing_service_other ✅ / service-only ❌). `docs/capability-matrix.md` v1.3 동반. 6-1 spec 본문 §A10 capability matrix 변경 명시.

AD-1 (modular monolith + hexagonal core) — 6-1 wire는 engine pure helper + service layer + handlers 표준 3-tier 패턴 (5-1/5-2/5-3 동일).

AD-2 (append-only ledger) — 6-1 wire는 closing_snapshot ledger event emit (5-2 wire 위에 additive). 5-2 inventory_ledger SSOT + RLS 4-policy 그대로 활용.

AD-3 (RLS) — 6-1 wire는 RLS 위에서 동작 (5-2 wire와 동일 predicate). service_role bypass 시 audit row INSERT-first (Epic 0 0-2 wire 패턴).

AD-4 (atomicity) — 6-1 closing_period close transaction = REPEATABLE READ + SELECT FOR UPDATE on monthly_input_periods (5-3 wire와 동일 transaction). audit-first + idempotent no-op skip (CR 1.1 lesson).

AD-6 (close lock) — 6-1 wire는 fiscal-period close lock 진입점. `monthly_input_periods.status='closed'` 시 closing_period snapshot 완료 + reopen 불가. reopen은 operator action + reason + audit row (AD-25 invalidation).

AD-11 (layer rule) — pure helpers = `packages/services/m4_inventory/closing_period.py` (NEW) + `packages/cost_engine/closing_period_snapshot.py` (NEW). service layer = `apps/api/modules/m4_inventory/services/closing_period_service.py` (NEW). engine은 closing_period 의미 모름 (service-layer ownership — 4-1 wire 패턴 동일).

AD-12 (verification ordering) — V4 wire = closing snapshot 일관성 verification (5-3 V3 wire 위에 additive). V1 → V4 → V3 → V7 → V8 ordering 보존. V4 fail 시 V3 SKIP.

AD-15 (cross-language parity) — TS mirror drift detector `tests/integration/test_closing_period_label_consistency.py` (NEW) + vitest wire (Story 0.5 AC #4 done). Decimal serialization parity.

AD-18 (single product identity) — `inventory_ledger.product_id` (UUID v7) = PRODUCT(product_id) SSOT. closing_period snapshot per-product aggregation = product_id SSOT.

AD-22 (append-only-leaning + reversal) — closing_period snapshot = append-only ledger event (5-2 wire). correction = Epic 11 reversal module ships 후 부호 반전 row + corrected row emit. `closing_snapshot` event type은 reversal 가능.

AD-23 (4-namespace pattern) — monthly_input_periods + monthly_input_rows + inventory_ledger + audit_logs 4 namespace SSOT. 6-1 wire는 4 namespace 모두 read-only aggregate + monthly_input_periods update + inventory_ledger INSERT + audit_logs INSERT.

AD-24 (typed period-key) — 'YYYY-MM' 형식 SSOT. closing_period per period_key. closing_period service는 `monthly_input_periods.period_key` AD-24 typed.

PRD §F4.3 (월 마감 E2E) — 6-1 primary AC: closing_period service로 closing 시점 ledger aggregate 영구화 + closing snapshot ledger event emit.

PRD §F5 (마감 보고서) — 6-2 spec 진입 시점 wire. 6-1 wire는 closing snapshot = 6-2 보고서 입력 source.

PRD §V4 (closing period verification) — 6-1 V4 wire 신규: closing snapshot 일관성 verification (closing_guard invariant + ledger aggregate 일치 + closing snapshot qty 합계 = product active closing balance).

PRD §6.2 (수불부) — 5-3 wire와 동일 (PRD §6.2 normalized). 6-1 wire는 수불부 read-only aggregate.

PRD §A11 (오류의 가시화) — 입력 시 경고 (5-3 wire) + 마감 시 차단 (5-3 wire) + 마감 확정 시 snapshot (6-1 wire) 3-layer. PRD §A11 정책 정확히 closed.

PRD §12 (AI) — 6-1은 AI 무관. 6-2/6-3에서 AI commentary 활용 가능.

0.5 plumbing — 6-1 frontend ClosingPeriodConfirmationPanel 진입 시점 frontend toolchain 완비 (shadcn Tabs / sonner / vitest / Playwright / next-intl). ClosingPeriodConfirmationPanel = ClosingGuardBanner (5-3 wire) 위에 additive panel. -->

## Story

As a **사장님**,

I want **월 마감을 확정하면 (1) 그 시점의 모든 제품 기말재고가 영구 보존된 closing_snapshot ledger event로 기록되고 (2) ClosingGuardBanner에 "마감 확정" 패널이 추가되며 (3) V4 verification이 ledger aggregate와 closing snapshot의 일관성을 검증하고 (4) service-only 업종은 월 마감 진입 자체가 거부되는 것**,

so that **회계사·세무사에게 전달할 마감 snapshot이 시스템적으로 immutable하게 보존되고, Epic 11 reversal module의 진입점이 wire되며, PRD §F4.3 + §F5 + §V4 wire contract가 정확히 closed됨** — AD-2 (append-only ledger closing_snapshot event) · AD-4 (atomicity close-time hook) · AD-6 (fiscal-period close lock) · AD-11 (layer rule) · AD-12 (verification ordering V1 → V4 → V3 → V7 → V8) · AD-15 (cross-language parity) · AD-18 (single product identity) · AD-22 (reversal entrypoint) · PRD §F4.3 (월 마감 E2E) · PRD §F5 (마감 보고서 입력 source) · PRD §V4 (closing snapshot 일관성 verification) · PRD §A11 (입력 시 경고 + 마감 시 차단 + 마감 확정 시 snapshot 3-layer) · A8 (Epic 6 close-out 시점에 inline projection 제거) · A10 (MONTHLY_CLOSING_REPORT capability 신규) · Story 0.5 frontend plumbing · Epic 5 5-3 (closing_guard + V3 verification + ClosingGuardBanner) carry-over.

## Acceptance Criteria

1. **Given** Epic 5 5-1 (opening auto-carry chain) + 5-2 (inventory_ledger append-only events, `closing_snapshot` 11번째 event_type) + 5-3 (closing_guard + V3 verification + ClosingGuardBanner) backend wire 완료 + Story 3.3 (음수재고 입력 시 즉시 경고) + Story 4-2 (close-time hook) + Story 4-3 (verification surface V1/V4/V7/V8) + Story 4-4 (V8 골든 fixture) + Story 0.5 frontend plumbing ✅ done (shadcn Tabs / sonner / vitest / Playwright / next-intl) + A12 (T12.2 test file deferred close-out done)
   **When** 본 스토리 dev-story 진입 시
   **Then** 다음 책임 분리 + wire contract 정렬이 유지된다:
     - **Pure kernel #1 (NEW `packages/services/m4_inventory/closing_period.py`)** — `compute_closing_snapshot(closing_per_product: dict[UUID, Decimal], period_key: str, tenant_id: UUID, finalized_at: str) -> list[ClosingSnapshotEntry]` (5-3 `compute_closing_balance_per_product` 결과 = closing per product → per-product ClosingSnapshotEntry 변환). + `classify_closing_period_status(closing_per_product: dict[UUID, Decimal], ledger_event_count: int) -> ClosingPeriodStatus` (CLOSING_READY / CLOSING_BLOCKED / ALREADY_CLOSED / EMPTY_PERIOD — CLOSING_READY = invariant OK + ledger events ≥ 1; CLOSING_BLOCKED = invariant NEGATIVE_CLOSING; ALREADY_CLOSED = monthly_input_periods.status='closed'; EMPTY_PERIOD = ledger events 0건). + `is_closing_period_allowed(status: ClosingPeriodStatus) -> bool` (= status == CLOSING_READY). + `CLOSING_PERIOD_CONFIRMATION_KO: Final[str] = "월 마감 확정: 기말재고 snapshot 저장"` (Korean confirmation message constant — AD-15 §11 SSOT). stdlib-only (no DB, no clock, no random). banker's rounding via `QTY_QUANTUM` from `inventory_projection` (CR 0-4 lesson + AD-15 parity). 1 typed exception (`ClosingPeriodError`, NO HTTP mapping — pure helper owns domain semantics).
     - **Pure kernel #2 (NEW `packages/cost_engine/closing_period_snapshot.py`)** — `verify_closing_period_consistency(*, ledger_aggregate: dict[UUID, Decimal], closing_snapshot_aggregate: dict[UUID, Decimal], product_whitelist: set[UUID]) -> V4Verdict` (V4 rule pure kernel — closing snapshot 일관성 verification; ledger aggregate = 5-2 `query_period_closing` 결과 vs closing_snapshot_aggregate = inventory_ledger `event_type='closing_snapshot'` aggregate 일치 검증; verdict = PASS / FAIL / SKIP). **AD-11 layer rule**: cost_engine pure helper는 stdlib-only (no sqlalchemy import) — service layer가 ledger aggregate + closing snapshot aggregate + product whitelist를 인자로 전달. **AD-12 ordering**: V4 rule의 `previous_status='failed'` 시 SKIP 발동 = Story 4-3 ordering invariant 보존. stdlib-only. 1 typed exception (`ClosingPeriodSnapshotInconsistencyError`).
     - **Service layer #1 (NEW `apps/api/modules/m4_inventory/services/closing_period_service.py`)** — `ClosingPeriodService` class with 3 operations:
       - `evaluate_closing_period(session, *, tenant_id, period_key) -> ClosingPeriodResult` (read-only aggregate via 5-2 `LedgerService.query_period_closing` + 5-3 `ClosingGuardService.evaluate_closing_guard` dispatch + T1 pure kernel `classify_closing_period_status` + `is_closing_period_allowed`).
       - `confirm_closing_period(session, *, tenant_id, period_key, actor_id) -> ClosingPeriodConfirmationResult` (close-time hook — 4-2 is_blocked + 5-3 closing_guard 위 additive: T1 pure kernel dispatch → ledger aggregate 검증 → T2 pure kernel V4 verification dispatch → closing_snapshot ledger event emit (5-2 `LedgerService.append_event` 호출) + `monthly_input_periods.status='closed'` UPDATE (AD-6 fiscal-period close lock) + audit log emission (CR 1.1 audit-first)).
       - `get_closing_period_audit_trail(session, *, tenant_id, period_key) -> list[AuditLogEntry]` (CR 1.1 observability — closing_period_confirmed + closing_period_blocked + closing_period_snapshot_inconsistency audit entries, time DESC).
     - **Wire trigger (extension `apps/api/modules/m4_inventory/handlers.py`)** — 3 NEW routes:
       - `POST /api/v1/inventory/closing-period/confirm` — close-time confirmation wire. Body = `{ period_key: str }`. Returns 200 OK `{ confirmed: true, closing_snapshot_count: int, period_key: str, finalized_at: str }` or 409 CLOSING_PERIOD_BLOCKED typed envelope (5-3 NEGATIVE_CLOSING_INVENTORY envelope와 동등) or 409 ALREADY_CLOSED typed envelope. Capability gate `MONTHLY_CLOSING_REPORT` (A10 신규 — manufacturing 3종 ✅ / service-only ❌ INDUSTRY_NOT_SUPPORTED).
       - `GET /api/v1/inventory/closing-period/status?period_key=...` — read-only closing period status check. Returns `ClosingPeriodResponse` (`{ status: "CLOSING_READY"|"CLOSING_BLOCKED"|"ALREADY_CLOSED"|"EMPTY_PERIOD", allowed: bool, closing_per_product: dict[str, str], closing_snapshot_count: int, ledger_event_count: int, period_key: str }`). AD-15 envelope + capability gate.
       - `GET /api/v1/inventory/closing-period/audit-trail?period_key=...` — closing period audit log emission trace (CR 1.1 observability). Returns audit_logs entries filtered by `action='closing_period_*'`. Capability gate.
     - **V4 verification wire (extension `apps/api/modules/m6_verification/services/verification_runner.py`)** — V4 slot fill in `run_all(monthly_input, baseline, calc_result, *, industry)`:
       1. V1 (완전배부) → wire from Story 4-3.
       2. **V4 (closing snapshot 일관성) — NEW wire** (`ClosingPeriodSnapshotVerifier.verify_v4_closing_period_consistency` dispatch).
       3. V3 (연결성 = closing ≥ 0 invariant) → wire from Story 5.3.
       4. V7 (ABC 무결성) → wire from Story 4-3 (service-only ❌ skip).
       5. V8 (1원 단위 회귀) → wire from Story 4-4.
     - **A5 forward-lock (`apps/api/core/audit_action.py` extension)** — `ClosingPeriodAction` Literal 3 values 신규 채움: `closing_period_confirmed` (closing period 확정 audit), `closing_period_blocked` (closing period 차단 audit), `closing_period_snapshot_inconsistency` (V4 verification fail audit). + `VerificationAction` Literal 1 value 신규 채움: `verify_v4_closing_period_consistency` (Story 4-3 V4 placeholder fill audit). A5 drift detector 동시 통과.

2. **Given** AC #1 pure kernel + service layer + wire trigger + V4 verification + A5 forward-lock
   **When** 본 스토리 dev-story 진입 시
   **Then** 다음 frontend wire 발동 (AC #2 — ClosingPeriodConfirmationPanel + shadcn Dialog + sonner toast wire):
     - **TS mirror helper #1 (NEW `apps/web/lib/closing-period.ts`)** — 6-1 frontend logic (wire path mirror). Exports:
       ```typescript
       export type ClosingPeriodStatus = "CLOSING_READY" | "CLOSING_BLOCKED" | "ALREADY_CLOSED" | "EMPTY_PERIOD";
       export interface ClosingPeriodState {
         status: ClosingPeriodStatus;
         allowed: boolean;
         closing_per_product: Record<string, string>;
         closing_snapshot_count: number;
         ledger_event_count: number;
         period_key: string;
       }
       export interface ClosingPeriodConfirmationResult {
         confirmed: boolean;
         closing_snapshot_count: number;
         period_key: string;
         finalized_at: string;
       }
       export function buildClosingPeriodState(response: ClosingPeriodResponse): ClosingPeriodState;
       export function isClosingPeriodAllowed(state: ClosingPeriodState): boolean;
       export function formatClosingPeriodConfirmationKo(state: ClosingPeriodState): string;  // "월 마감 확정: 기말재고 snapshot 저장"
       export function formatClosingPeriodBlockedKo(state: ClosingPeriodState): string;  // "마감 차단: 기말재고 음수"
       ```
     - **TS mirror helper #2 (extension `apps/web/lib/l2-input-inventory-ledger.ts`)** — 5-2 W2 carry-over extension. Add `ClosingSnapshotEvent` interface export:
       ```typescript
       export interface ClosingSnapshotEvent {
         event_id: string; product_id: string; period_key: string;
         event_type: "closing_snapshot"; qty: string;  // closing qty per product
         trace_id: string; reverses_event_id: string | null;
         correction_group_id: string | null;
         finalized_at: string;  // ISO-8601 UTC
       }
       ```
     - **ClosingPeriodConfirmationPanel (NEW `apps/web/components/m2-input/ClosingPeriodConfirmationPanel.tsx`)** — ClosingGuardBanner (5-3 wire) 위에 additive panel. shadcn `<Alert>` + `<Dialog>` pattern:
       - When `closing_period.status=CLOSING_READY` → "마감 확정 가능" Alert 표시 + [마감 확정] 버튼 (sonner `toast.info` on click).
       - When `closing_period.status=CLOSING_BLOCKED` → "마감 차단: 음수 기말재고" Alert 표시 + [마감 확정] 버튼 disabled (ClosingGuardBanner 와 동일 wire).
       - When `closing_period.status=ALREADY_CLOSED` → "이미 마감됨 (finalized_at: ...)" Alert 표시 + [마감 확정] 버튼 비노출 (AD-6 close lock).
       - When `closing_period.status=EMPTY_PERIOD` → "수불 event 0건: 마감 불가" Alert 표시 + [마감 확정] 버튼 disabled.
     - **ClosingPeriodConfirmDialog (NEW `apps/web/components/m2-input/ClosingPeriodConfirmDialog.tsx`)** — shadcn `<Dialog>` + sonner `toast.success` + `toast.error` pattern:
       - [마감 확정] 버튼 클릭 → Dialog 열림 (closing_period snapshot 산출 preview 표시).
       - Dialog [확정] 클릭 → `POST /api/v1/inventory/closing-period/confirm` 호출 → 200 OK → sonner `toast.success('월 마감 확정 완료: closing_snapshot {N}건 저장')` + 페이지 reactive (ClosingGuardBanner → "마감 확정됨" 표시).
       - 409 CLOSING_PERIOD_BLOCKED / 409 ALREADY_CLOSED → sonner `toast.error(...)` + Dialog 닫힘 + ClosingGuardBanner re-display.
     - **MonthlyInputTabs extension** — `apps/web/components/m2-input/MonthlyInputTabs.tsx` (5-3 wire) extension. 마감 tab (5-3 3-tab 구조) 안에 ClosingPeriodConfirmationPanel wire. ClosingGuardBanner + ClosingPeriodConfirmationPanel = vertical stack (5-3 AC #2 wire 그대로).
     - **Capability-gated UI** — service-only tenant (`tenant_settings.industry === 'service'`) → ClosingPeriodConfirmationPanel 비노출 + 403 INDUSTRY_NOT_SUPPORTED 시 sonner `toast.error` 표시. Capability matrix v1.3 (A10 결정) `MONTHLY_CLOSING_REPORT` capability SSOT.

3. **Given** AC #2 TS mirror + ClosingPeriodConfirmationPanel + ClosingPeriodConfirmDialog + capability gate
   **When** 본 스토리 dev-story 진입 시
   **Then** 다음 wire contract 발동 (AC #3 — closing snapshot signal source = ledger aggregate + closing_snapshot event + monthly_input_periods status update):
     - **`MonthlyInputStateResponse` extension (NEW 4 fields)**:
       - `closing_period_status: ClosingPeriodState` (closing period status result — 5-3 closing_guard_invariant와 별도 필드)
       - `closing_snapshot_count: int` (현재 시점 closing_snapshot ledger event count — AC #1 wire trigger)
       - `closing_period_audit_trail: list[AuditLogEntry]` (last 10 closing_period_* audit entries, time DESC)
       - `closing_period_finalized_at: str | None` (ISO-8601 UTC, monthly_input_periods.status='closed' 시 finalized_at; None = 미마감)
     - **5-1 + 5-2 + 5-3 carry fields 보존**: 12 fields = `opening_inventory` + `opening_inventory_locked` + `opening_inventory_lock_reason_ko` (5-1) + `ledger_events_count` + `ledger_period_closing` + `inventory_ledger_enabled` + `reversal_request_enabled` (5-2) + `closing_guard_invariant` + `closing_guard_blocked` + `closing_guard_audit_trail` + `production_consumption_events` + `v3_verdict` (5-3) 그대로. 6-1 = 4 fields 신규 추가. 합계 16 fields.
     - **`MonthlyInputService.get_state` extension** — wire `closing_period_service.evaluate_closing_period(session, tenant_id, period_key)` 호출 결과 + audit_trail query → 4 NEW fields populate.
     - **`MonthlyInputService.confirm_closing_period` NEW method (extension `apps/api/modules/m2_input/services/monthly_input_service.py`)** — close-time confirmation hook:
       1. `closing_period_service.confirm_closing_period(session, tenant_id, period_key, actor_id)` dispatch (AC #1 wire trigger).
       2. confirm 성공 → `monthly_input_periods.status='closed'` UPDATE (AD-6 fiscal-period close lock) + `closed_at=func.now()` + `closed_by_actor_id=actor_id` + `closing_snapshot_event_count=N`.
       3. CR 1.1 audit-first ordering: ledger INSERT before monthly_input_periods UPDATE before audit log INSERT (atomicity guarantee).
       4. idempotent no-op skip: monthly_input_periods.status='closed' 이미 → 409 ALREADY_CLOSED typed envelope (no INSERT + no UPDATE + no audit).
     - **Close-time hook integration (extension `MonthlyInputService.attempt_close` 4-2 is_blocked + 5-3 closing_guard 위 additive)**:
       1. 4-2 `is_blocked=true` → 409 MONTHLY_INPUT_BLOCKED typed envelope (기존).
       2. 5-3 `closing_guard_service.request_close_attempt` → 409 NEGATIVE_CLOSING_INVENTORY typed envelope (5-3 wire).
       3. **6-1 `closing_period_service.confirm_closing_period` dispatch** → CLOSING_READY 시 200 OK `{ confirmed: true, closing_snapshot_count: int, period_key: str, finalized_at: str }` + ALREADY_CLOSED 시 409 ALREADY_CLOSED + CLOSING_BLOCKED 시 409 CLOSING_PERIOD_BLOCKED.
       4. Audit log emission (CR 1.1 audit-first) — `audit_logs.action='closing_period_confirmed'` (ActionClass.CLOSING_PERIOD NEW) payload: `{period_key, closing_snapshot_count, finalized_at, actor_id, tenant_id, trace_id}`.
     - **V4 verification wire (extension VerificationRunner 4-3 + 5-3 wire)** — `run_all(monthly_input, baseline, calc_result, *, industry)`:
       1. V1 → **V4 (closing snapshot 일관성)** → V3 → V7 → V8 ordering 보존 (AD-12 invariant).
       2. V4 wire: `ClosingPeriodSnapshotVerifier.verify_v4_closing_period_consistency(session, monthly_input, baseline, calc_result)` dispatch. industry=='service' → V4 SKIP (service-only tenant은 inventory 의미 없음 — 4-3 service-only ❌ skip pattern + A10 MONTHLY_CLOSING_REPORT capability gate 동등).
       3. V4 fail → `top_failure.code='V4'` + audit `action='closing_period_snapshot_inconsistency'` (ActionClass.CLOSING_PERIOD NEW) + 4-3 verdict envelope verbatim.
       4. V4 pass → audit `action='closing_period_confirmed'` (ActionClass.CLOSING_PERIOD NEW) payload `{period_key, closing_snapshot_count, verified_at, actor_id, tenant_id, trace_id}`.

4. **Given** AC #1~#3 backend wire + AC #2 frontend wire + 5-1/5-2/5-3/0.5/A12 carry-over
   **When** 본 스토리 commit 안에서 5-3 carry-over close + A10 capability matrix v1.3 wire
   **Then** 다음 defense-in-depth + carry-over wire 발동 (AC #4 — A10 capability matrix + A8 inline projection timeline + closing_period audit):
     - **A10 capability matrix v1.3 (extension `docs/capability-matrix.md`)** — Epic 5 retro §7 A10 결정:
       ```markdown
       | Capability | manufacturing | mfg+service | mfg+service+other | service-only |
       |------------|---------------|-------------|--------------------|--------------|
       | ... 기존 11+ capabilities ... |
       | MONTHLY_CLOSING_REPORT (NEW 6-1) | ✅ | ✅ | ✅ | ❌ INDUSTRY_NOT_SUPPORTED |
       ```
       Changelog v1.3: 6-1 spec 진입 시 `MONTHLY_CLOSING_REPORT` capability wire.
     - **A8 inline projection deprecation timeline (Epic 5 retro §7 A8 결정)** — `docs/closing-period.md` §timeline 섹션 명시:
       ```markdown
       ### A8 — Epic 3.3 inline projection deprecation timeline
       - **5-2 commit + 1 epic maintenance window 종료 시점 = Epic 6 close-out 시점**
       - 6-1 wire 시점 (Epic 6 진입점): inline projection 보존 (1 epic maintenance window 진행 중) + closing_period snapshot은 ledger aggregate (5-2 wire) 사용
       - 6-2 / 6-3 wire: inline projection 보존 상태로 wire
       - Epic 6 close-out 시점에 fold-in vs deprecate 결정 (Epic 11 reversal 진입 시 inline projection 완전 제거)
       ```
     - **ClosingPeriod audit log wire (AC #3 #4)** — `audit_logs.action='closing_period_confirmed'` / `closing_period_blocked` / `closing_period_snapshot_inconsistency` 3 values 신규 (ActionClass.CLOSING_PERIOD). INSERT to audit_logs (immutable, AD-2). payload = self-describing (CR 1.1 lesson).
     - **SQL CHECK constraint (extension `apps/api/alembic/versions/0017_closing_period.py` NEW)**:
       ```sql
       ALTER TABLE monthly_input_periods ADD CONSTRAINT chk_closing_period_status
         CHECK (
           status IN ('open', 'closing', 'closed')
         );
       ALTER TABLE monthly_input_periods ADD COLUMN closing_snapshot_event_count INTEGER DEFAULT 0
         CHECK (closing_snapshot_event_count >= 0);
       ALTER TABLE monthly_input_periods ADD COLUMN finalized_at TIMESTAMPTZ;
       ALTER TABLE monthly_input_periods ADD COLUMN closed_by_actor_id UUID;
       ```
       SQL-level guard: monthly_input_periods.status lifecycle = `open` → `closing` → `closed` (1-way state machine). 5-3 wire와 동일 defense-in-depth 패턴.
     - **W4 vitest activation (Story 5-2 + 5-3 carry-over close)** — `tests/integration/test_inventory_ledger_label_consistency.py` extension. 3 NEW 6-1 cases 추가 (closing_period_status_label_ko_parity, closing_snapshot_event_type_ko_parity, closing_period_blocked_envelope_ko_parity). vitest infra (Story 0.5 AC #4 done) 활용. pytest.skip markers removed.
     - **W5 isolated service layer tests (Story 5-2 + 5-3 carry-over close)** — `tests/api/m4_inventory/test_closing_period_service.py` (NEW) — 12 cases: evaluate_closing_period (3), confirm_closing_period CLOSING_READY success (2), confirm_closing_period CLOSING_BLOCKED 409 (2), confirm_closing_period ALREADY_CLOSED 409 (1), confirm_closing_period audit-first ordering (2), closing_period_audit_trail query (2).
     - **6-1 AC #2 wire trigger frontend tests (Story 0.5 vitest + RTL wire)** — `apps/web/__tests__/closing-period-confirmation-panel.test.tsx` (NEW) — 5 scenarios:
       1. `test_closing_period_panel_shows_when_ready` — status=CLOSING_READY → Alert 표시 + [마감 확정] 버튼 enabled.
       2. `test_closing_period_panel_shows_blocked` — status=CLOSING_BLOCKED → Alert 표시 + [마감 확정] 버튼 disabled.
       3. `test_closing_period_dialog_open_on_click` — [마감 확정] 클릭 → Dialog 열림 + snapshot preview 표시.
       4. `test_closing_period_confirm_success` — Dialog [확정] 클릭 → POST 호출 + sonner toast.success + 페이지 reactive.
       5. `test_closing_period_already_closed` — status=ALREADY_CLOSED → Alert 표시 + [마감 확정] 버튼 비노출.
     - **MonthlyInputTabs extension tests (vitest + RTL)** — `apps/web/__tests__/monthly-input-tabs.test.tsx` (5-3 wire) extension. 4 NEW 6-1 scenarios 추가 (ClosingPeriodConfirmationPanel render, confirm dialog flow, audit trail list extension, service-only tenant hide).

5. **Given** AC #1~#4 backend wire + frontend wire + carry-over close + capability matrix v1.3
   **When** 본 스토리 dev-story 진입 시 5-3 ClosingGuardBanner 위에 additive + 6-1 frontend ClosingPeriodConfirmationPanel
   **Then** 다음 3-layer defense wire 발동 (AC #5 — PRD §A11 입력 시 경고 + 마감 시 차단 + 마감 확정 시 snapshot 3-layer):
     - **Layer 1 (입력 시 경고)** — Story 3.3 inline projection + 5-2 ledger aggregate 동시 활용. 음수 기초재고 / 출고 > 기초재고 입력 시 sonner `toast.warning` (5-3 wire 그대로).
     - **Layer 2 (마감 시 차단)** — Story 5.3 `closing_guard_service.request_close_attempt` + 4-2 `is_blocked` 위 additive. 음수 기말재고 발생 시 409 NEGATIVE_CLOSING_INVENTORY typed envelope + ClosingGuardBanner red Alert (5-3 wire 그대로).
     - **Layer 3 (마감 확정 시 snapshot)** — **6-1 `closing_period_service.confirm_closing_period`** dispatch. CLOSING_READY 시 ledger INSERT (closing_snapshot event_type) + monthly_input_periods.status='closed' UPDATE + audit INSERT (atomic transaction). 409 ALREADY_CLOSED 시 멱등성 보장 (idempotent no-op skip).
     - **Capability gate** — `Capability.MONTHLY_CLOSING_REPORT` (6-1 v1.3 wire) + `Capability.INVENTORY_LEDGER` (5-2 wire) + `Capability.MONTHLY_INPUT_PRODUCTION` (3-1 wire) 3 capabilities 모두 CLOSING_PERIOD 진입점에서 검증. service-only tenant → 403 INDUSTRY_NOT_SUPPORTED typed envelope (A10 결정).

6. **Given** AC #1~#5 backend + frontend + ClosingGuardBanner 위에 additive + capability gate
   **When** 본 스토리 dev-story 진입 시 V4 verification wire
   **Then** 다음 verification sync 발동 (AC #6 — V4 (closing snapshot 일관성) verification ↔ ledger aggregate ↔ closing_snapshot ledger events 양방향 동기화):
     - **V4 verdict wire** — Story 4-3 V4 placeholder + Story 4-4 V8 골든 fixture fill 진입점 (V4 fixture = closing snapshot 일관성 PASS / FAIL 2 시나리오 골든):
       1. **V4 PASS 골든** — ledger aggregate == closing_snapshot aggregate per product + V4 verdict = `passed` + audit `closing_period_confirmed`.
       2. **V4 FAIL 골든** — ledger aggregate != closing_snapshot aggregate (per-product qty 불일치) + V4 verdict = `failed` + audit `closing_period_snapshot_inconsistency` + top_failure.code='V4' + Korean message "마감 snapshot 불일치: 기말재고 ledger vs closing_snapshot 갱신 필요".
     - **V4 골든 fixture wire (extension `packages/cost_engine/tests/regression_v8/fixtures/`)** — `v4_closing_period_pass_manufacturing.json` + `v4_closing_period_fail_manufacturing.json` 2 신규 골든. V8_FIXTURE_COUNT 14 → 16. 4-4 `fixture_publisher` CLI `--industry manufacturing --include-closing-period-snapshot` 추가.
     - **V8 byte-identical 골든 확장** — Story 4-4 14 fixture matrix × V4 closing period snapshot 2 신규 = 16 fixture matrix. `tests/regression_v8/test_regression_v8_fixtures.py` extension — 16 lock_sha256 + 16 byte-identical + 16 100x determinism + 2 V4 FAIL shape + 2 V4 PASS shape cases. V8 mandatory CI gate 보존.
     - **Verification ordering invariant (AD-12)** — V1 fail 시 V4 SKIP. V4 fail 시 V3 SKIP. V3 fail 시 V7 SKIP. V7 fail 시 V8 SKIP. abort-on-fail 패턴 그대로 (Story 4-3 + 5-3 wire).
     - **4-2 calc endpoint close-time hook (Epic 3 A4 wire) 위에 additive** — `POST /api/v1/calc` 응답 시 verdict field:
       - V4 fail → `top_failure.code='V4'` + `top_failure.message_ko='마감 snapshot 불일치: 기말재고 ledger vs closing_snapshot 갱신 필요'` + block_reason='CLOSING_PERIOD_SNAPSHOT_INCONSISTENCY'.
       - V4 pass → verdict.status='verified' + closing period snapshot OK.
     - **Industry skip matrix (4-3 wire 패턴)** — manufacturing / manufacturing_service / manufacturing_service_other → V4 RUN. service-only → V4 SKIP (inventory 의미 없음 + A10 MONTHLY_CLOSING_REPORT capability gate 동등 발동).

7. **Given** AC #1~#6 backend + frontend + V4 sync + 골든 fixture + verification ordering
   **When** 본 스토리 dev-story 진입 시 audit-first + idempotent no-op + A5 forward-lock + A7 wire + A8 inline projection timeline
   **Then** 다음 audit + drift + A7 wire 발동 (AC #7 — A5 forward-lock + A7 wire + A8 timeline + A10 capability):
     - **`apps/api/core/audit_action.py` extension** — `ClosingPeriodAction = Literal["closing_period_confirmed", "closing_period_blocked", "closing_period_snapshot_inconsistency"]` 3 values 신규 + `VerificationAction` Literal 1 value 신규 채움: `verify_v4_closing_period_consistency` (Story 4-3 V4 placeholder fill audit). **A5 forward-lock**: `_ActionRegistry._REGISTRY[ActionClass.CLOSING_PERIOD]` accepted frozenset 3 values fill + `_REGISTRY[ActionClass.VERIFICATION]` accepted frozenset extension 1 value add (Story 4-3 wire 4 values + 5-3 wire 1 value + 6-1 wire 1 value = 6 values).
     - **A5 drift detector (`tests/services/test_audit_action_centralization.py` extension)** — ActionClass.CLOSING_PERIOD + ActionClass.VERIFICATION 4 new actions 검증 pass. drift count = 0 유지.
     - **3-way consistency drift detector (`tests/integration/test_audit_action_consistency.py` extension)** — A5 forward-lock:
       - registry ↔ DB CHECK: ActionClass.CLOSING_PERIOD 3 values (registry SSOT) + ActionClass.VERIFICATION 6 values (registry SSOT + Story 4-3 wire 4 values + 5-3 V3 1 value + 6-1 V4 1 value).
       - call sites AST-grep: `emit_audit(` raw in `apps/api/modules/m4_inventory/` + `apps/api/modules/m6_verification/` = 0 (5-1 + 5-2 + 5-3 + 6-1 모두 typed).
       - verified DB constraint contents match published alembic migration files (Alembic 0013 + 0014 + 0015 + 0016 + 0017 모두 일치).
     - **A7 wire (Epic 4 close-out retro A7 — async test pattern + SDR overclaim)** — Story 5-2 + 5-3 wire pattern 그대로:
       - Async test pattern (CR 4-3 F-1) — 모든 service-layer test `def test_x(): asyncio.run(_impl())` wrapper (pytest-asyncio 금지).
       - SDR overclaim detector — `tests/integration/test_sdr_test_count_drift.py` 2 cases (5-1 + 5-2 + 5-3 wire pattern 그대로 6-1 확장).
     - **`MonthlyInputService.confirm_closing_period` CR 1.1 audit-first + idempotent no-op wire**:
       1. `monthly_input_periods.status='closed'` check (idempotent no-op guard) → 이미 closed 시 409 ALREADY_CLOSED typed envelope (no INSERT + no UPDATE + no audit).
       2. `closing_period_service.evaluate_closing_period` 호출 → status == CLOSING_READY 검증.
       3. **5-2 `LedgerService.append_event(event_type='closing_snapshot', ...)`** INSERT to inventory_ledger (per-product closing qty) — per product 1 row. CR 1.1 audit-first ordering.
       4. **`monthly_input_periods.status='closed'` UPDATE** + `closed_at=func.now()` + `closed_by_actor_id=actor_id` + `closing_snapshot_event_count=N`.
       5. **`emit_audit_typed(action_class=ActionClass.CLOSING_PERIOD, action='closing_period_confirmed', ..., payload={period_key, closing_snapshot_count, finalized_at, actor_id, tenant_id, trace_id})`** INSERT to audit_logs.
       6. CR 1.1 idempotent re-confirm 시 audit skip + no DB write (CLOSING_PERIOD wire).
     - **PR 일관성 guard** — Alembic 0017 migration 후 Alembic 0015 + 0016 + 0017 cross-check (`tests/integration/test_alembic_migration_chain.py` extension — V4 closing period snapshot guard wire에 필수).

8. **Given** AC #1~#7 backend + frontend + V4 + audit + drift + A7 + A8 timeline + A10 capability
   **When** 본 스토리 10 task (T1-T10) 실행
   **Then** 다음 tests wire 발동 (AC #8 — 3중 게이트 + drift detector + A5 + A7 + frontend vitest + Playwright):
     - **Pure kernel (2 NEW files — ~30 cases)**:
       - `tests/services/m4_inventory/test_closing_period.py` (NEW) — 18 cases: compute_closing_snapshot (5), classify_closing_period_status (5 CLOSING_READY/CLOSING_BLOCKED/ALREADY_CLOSED/EMPTY_PERIOD/edge), is_closing_period_allowed (2), CLOSING_PERIOD_CONFIRMATION_KO constant (2), append-only interaction (2), banker's rounding (2 — CR 0-4 lesson).
       - `tests/cost_engine/test_closing_period_snapshot.py` (NEW) — 12 cases: V4 verdict PASS/FAIL/SKIP (3), ledger aggregate vs closing_snapshot aggregate 일치 검증 (3), product whitelist mismatch (2), industry='service' skip (2), ordering invariant (V4 fail 후 abort, 2), banker's rounding (2).
     - **Service layer (3 NEW files — ~28 cases)**:
       - `tests/api/m4_inventory/test_closing_period_service.py` (NEW) — 12 cases (AC #4 wire spec).
       - `tests/api/m6_verification/test_closing_period_snapshot_verifier.py` (NEW) — 8 cases: verify_v4_closing_period_consistency PASS/FAIL (2), industry skip (1), product whitelist mismatch (1), ordering invariant (1), audit emission (1), idempotent (1), empty period (1).
       - `tests/api/m2_input/test_monthly_input_confirm_closing_period.py` (NEW) — 8 cases: confirm_closing_period CLOSING_READY success (2), ALREADY_CLOSED 409 (2), audit-first ordering (2), idempotent re-confirm skip (2).
     - **3-way consistency drift detector (extension A5)** — `tests/integration/test_audit_action_consistency.py` extension — 4 NEW cases:
       - ActionClass.CLOSING_PERIOD registry ↔ DB CHECK consistency (2 cases).
       - ActionClass.VERIFICATION 6-1 extension ↔ Story 4-3 wire 4 values + 5-3 wire 1 value + 6-1 wire 1 value consistency (2 cases).
     - **SQL CHECK constraint test (AC #4)** — `tests/integration/test_closing_period_sql_check.py` NEW — 4 cases:
       1. `test_closing_period_status_state_machine_valid` — status lifecycle `open → closing → closed` 검증.
       2. `test_closing_period_status_invalid_rejected` — invalid status 값 INSERT 시 CHECK constraint violation.
       3. `test_closing_snapshot_event_count_non_negative` — `closing_snapshot_event_count < 0` 시 CHECK constraint violation.
       4. `test_closing_period_sql_check_constraint_exists` — alembic migration 후 introspection.
     - **V8 fixture extension (AC #6 wire)** — `tests/regression_v8/test_regression_v8_fixtures.py` extension — 16 fixture matrix + 2 V4 PASS/FAIL shape cases + 2 industry skip matrix = 20 NEW cases (총 V8 골든 = 16 = 14 existing + 2 V4 신규).
     - **Capability gate (1 NEW + 1 extension)**:
       - `tests/integration/test_closing_period_capability.py` (NEW) — 4 cases: manufacturing 3종 ✅ / service-only ❌ INDUSTRY_NOT_SUPPORTED (A10 MONTHLY_CLOSING_REPORT capability).
       - `tests/integration/test_inventory_ledger_capability.py` (extension) — `evaluate_closing_period` capability wire test 2 cases.
     - **TS mirror parity (1 extension)** — `tests/integration/test_closing_period_label_consistency.py` (NEW) — 6 cases (AC #2 wire spec):
       1. `test_closing_period_status_label_ko_parity` — TS `ClosingPeriodStatus` literal 4 values ↔ Python `ClosingPeriodStatus` literal 4 values.
       2. `test_closing_snapshot_event_type_ko_parity` — TS `ClosingSnapshotEvent` ↔ Python `closing_snapshot` ledger event.
       3. `test_closing_period_blocked_envelope_ko_parity` — TS `CLOSING_PERIOD_BLOCKED` envelope ↔ Python `ClosingPeriodBlockedError` envelope.
       4. `test_already_closed_envelope_ko_parity` — TS `ALREADY_CLOSED` envelope ↔ Python `AlreadyClosedError` envelope.
       5. `test_closing_period_confirmation_ko` — TS `formatClosingPeriodConfirmationKo` � Python `CLOSING_PERIOD_CONFIRMATION_KO`.
       6. `test_closing_period_blocked_ko` — TS `formatClosingPeriodBlockedKo` ↔ Python `CLOSING_PERIOD_BLOCKED_KO`.
     - **Frontend vitest tests (2 NEW files — 9 scenarios)**:
       - `apps/web/__tests__/closing-period-confirmation-panel.test.tsx` (NEW) — 5 scenarios (AC #4 spec).
       - `apps/web/__tests__/monthly-input-tabs.test.tsx` (extension) — 4 NEW 6-1 scenarios (ClosingPeriodConfirmationPanel render, confirm dialog flow, audit trail list extension, service-only tenant hide).
     - **Playwright E2E (1 NEW file — 4 scenarios)**:
       - `apps/web/e2e/closing-period.spec.ts` (NEW) — 4 scenarios:
         1. `test_closing_period_confirm_full_flow` — 기초재고 + 입고 + 출고 입력 → [마감] 클릭 → ClosingGuardBanner 표시 → [마감 확정] 클릭 → Dialog → [확정] → sonner toast.success + monthly_input_periods.status='closed' 검증.
         2. `test_closing_period_blocked_on_negative` — 출고 > 기말 → [마감] 차단 → ClosingPeriodConfirmationPanel disabled.
         3. `test_closing_period_already_closed_idempotent` — [마감 확정] 1회 → 2회 클릭 시 409 ALREADY_CLOSED typed envelope.
         4. `test_service_only_tenant_hides_closing_period` — service-only tenant → ClosingPeriodConfirmationPanel 비노출.
     - **3중 게이트 (mandatory CI)**:
       - `uv run ruff check packages/services/m4_inventory/closing_period.py packages/cost_engine/closing_period_snapshot.py apps/api/modules/m4_inventory/services/closing_period_service.py apps/api/modules/m6_verification/services/closing_period_snapshot_verifier.py apps/api/core/audit_action.py 0 errors`
       - `uv run import-linter lint` — closing_period.py + closing_period_snapshot.py pure helper = `packages/` allowed. m4_inventory + m6_verification service layer = `apps/api/modules/{m4_inventory,m6_verification}/` allowed (no `packages.cost_engine` import for service layer — AD-11).
       - `uv run pytest` (full) — 30+ pure + 28+ service + 4 drift + 4 SQL CHECK + 20 V8 골든 + 6 capability + 6 TS parity + 9 frontend vitest + 4 Playwright = 110+ NEW tests pass + Story 5-1 + 5-2 + 5-3 + 0-5 + A12 누적 회귀 0건. A7 SDR overclaim detector pass (test count = 110+ 매칭 필수).
       - `pnpm test` (Story 0.5 AC #4 wire + 6-1 frontend vitest) — 9 scenarios pass + 5-3 wire 14 scenarios regression 0건.
       - `pnpm playwright test --project=chromium apps/web/e2e/closing-period.spec.ts` (Story 0.5 AC #5 wire + 6-1 E2E) — 4 scenarios pass.

9. **Given** AC #1~#8 backend + frontend + V4 + tests + 3중 게이트
   **When** 본 스토리 10 task (T1-T10) 실행
   **Then** 다음 docs wire 발동 (AC #9 — operator/dev 가이드 + Epic 6 6-2 spec 진입점 + A8 timeline + A10 capability matrix):
     - `docs/closing-period.md` (NEW): operator/dev guide — closing_period service wire contract + closing_snapshot ledger event emit + V4 verification sync + 4-2 close-time hook + 5-3 closing guard + 5-2 ledger aggregate + shadcn Dialog + sonner toast + ClosingPeriodConfirmationPanel + ClosingPeriodConfirmDialog + idempotent no-op skip. 7-section 운영 매뉴얼 (개요 / wire contract / UI / V4 sync / carry-over close / 3-layer defense / 운영 가이드) + **A8 inline projection deprecation timeline 섹션** 명시 (Epic 6 close-out 시점 fold-in).
     - `docs/monthly-input.md` §Story 6.1 추가: closing period service wire contract (`closing_period_status` 4 values + `closing_snapshot_count` flag + `closing_period_finalized_at` envelope + `closing_period_audit_trail` list) + 6-1 4 NEW fields populate + ClosingPeriodConfirmationPanel UI + sonner toast pattern + [마감 확정] button gate.
     - `docs/inventory-ledger.md` §Story 6.1 추가: closing_snapshot ledger event wire (5-2 11 values event_type whitelist 11번째 값 wire 진입점) + ledger INSERT pattern + monthly_input_periods.status='closed' UPDATE + audit-first ordering.
     - `docs/cost-engine.md` §V4 closing period snapshot 추가: 4-3 V4 placeholder + 4-4 V8 골든 + 6-1 V4 wire — closing snapshot 일관성 PASS / FAIL 골든 2 fixture + V8 골든 14 → 16 matrix + byte-identical CI gate.
     - `docs/capability-matrix.md` v1.3 (2026-08-XX) — Changelog:
       - v1.3 (Story 6.1) — `MONTHLY_CLOSING_REPORT` capability wire (manufacturing 3종 ✅ / service-only ❌) + `ActionClass.CLOSING_PERIOD` 3 values 채움 + `ActionClass.VERIFICATION` V4 value add (5 → 6) + `inventory_ledger.event_type` 11 values 그대로 (closing_snapshot은 5-2 commit 안에서 wire 완료 — 6-1 spec 본문에서 명시 보존) + V4 verification surface wire + Alembic 0017 SQL CHECK constraint + 6-1 spec 진입 시 A8 inline projection deprecation timeline 명시.
     - `docs/conventions.md` §10.8 (NEW) closing period service policy: "closing period snapshot = AD-2 ledger append-only closing_snapshot event + AD-4 atomicity close-time hook + AD-6 fiscal-period close lock + AD-12 V4 verification ordering (V1 → V4 → V3 → V7 → V8). 입력 시 경고 (Story 3.3 inline + 5-3 ledger aggregate) + 마감 시 차단 (5-3 closing_guard_service + 4-2 close-time hook) + 마감 확정 시 snapshot (6-1 closing_period_service) 3-layer. V4 fail 시 4-3 verdict envelope + 4-2 close-time block_reason 동등 발동. 6-1 spec에서 3중 게이트 와이어됨. A8 timeline: Epic 6 close-out 시점에 inline projection 제거."
     - `docs/conventions.md` §10.7 �신 (5-3 closing guard invariant policy): "M14 TS mirror wire + L8 SQL CHECK + 5-3 frontend manual edit reject UI + 6-1 closing_period wire = 4중 defense-in-depth 보존."
     - `docs/frontend-toolchain.md` §Story 6.1 추가 (Story 0.5 v1.0 SSOT extension): ClosingPeriodConfirmationPanel pattern (ClosingGuardBanner 위에 additive) + shadcn Dialog pattern (`<Dialog>` + `<DialogTrigger>` + `<DialogContent>` + `<DialogAction>`) + ClosingPeriodConfirmDialog pattern + sonner `toast.success` + `toast.error` + `toast.info` pattern.

10. **Given** AC #1~#9 wire + docs + 3중 게이트
    **When** 본 스토리 commit 완료 후
    **Then** 다음 Epic 6 6-2 spec 진입점 발동 (AC #10 — Epic 6 close-out 결정 가이드):
    - **Epic 6 6-2 spec 진입점** — 6-1 commit 후 Epic 6 6-2 (Monthly Closing Report — closing snapshot + ledger events + capability gate) spec 진입 가능:
      1. **3-story 분할 결론** — Epic 5 retro §6 결정 (cj-style 6-1/6-2/6-3 분할) 그대로 적용. 6-1 closing period service + closing_snapshot ledger event wire 완료 → 6-2 Monthly Closing Report 진입점.
      2. **A10 carry (Epic 5 close-out retro A10)** — MONTHLY_CLOSING_REPORT capability 신규 wire 완료 → Epic 6/Epic 11 reporting capability 일관성 보장.
      3. **A8 carry (Epic 5 close-out retro A8)** — Epic 3.3 inline projection deprecation timeline 명시 완료 → Epic 6 close-out 회고 시점에 fold-in vs deprecate 결정 필수.
      4. **A11 carry (Epic 5 close-out retro A11)** — Epic 6 V8 fixture 확장 (closing snapshot + ledger events) 진입점. 6-1 wire 시점에 V4 골든 2 fixture 신규 + V8 골든 14 → 16 matrix 확장. 6-2 spec 진입 시 추가 fixture 확장 (월 마감 보고서 input shape).
      5. **A9 carry (Epic 5 close-out retro A9)** — Epic 11 reversal module wire 진입점 (5-1 + 5-2 + 6-1 carry). `closing_snapshot` ledger event = Epic 11 reversal module의 wire contract 진입점 (reversal_negating + reversal_corrected event type fill로 closing_snapshot correction 가능). Epic 11 spec 진입 시 결정.

## Tasks / Subtasks

### T1. Pure kernel #1 — `packages/services/m4_inventory/closing_period.py` (NEW)
- T1.1 `compute_closing_snapshot(closing_per_product: dict[UUID, Decimal], period_key: str, tenant_id: UUID, finalized_at: str) -> list[ClosingSnapshotEntry]` — 5-3 `compute_closing_balance_per_product` 결과 → per-product ClosingSnapshotEntry 변환. per product 1 ClosingSnapshotEntry = `{product_id, closing_qty: Decimal, finalized_at}`. banker's rounding via `QTY_QUANTUM` from `inventory_projection`.
- T1.2 `classify_closing_period_status(closing_per_product: dict[UUID, Decimal], ledger_event_count: int) -> ClosingPeriodStatus` — CLOSING_READY / CLOSING_BLOCKED / ALREADY_CLOSED / EMPTY_PERIOD 4 values classification. NamedTuple OR TypedDict.
- T1.3 `is_closing_period_allowed(status: ClosingPeriodStatus) -> bool` (= status == CLOSING_READY).
- T1.4 `CLOSING_PERIOD_CONFIRMATION_KO: Final[str] = "월 마감 확정: 기말재고 snapshot 저장"` — Korean confirmation message constant SSOT (AD-15 §11).
- T1.5 `ClosingPeriodError(Exception)` typed exception — pure helper domain semantics. NO HTTP envelope (service layer wraps).
- T1.6 stdlib-only import set: `uuid`, `decimal`, `re`, `datetime`, `enum`. NO `sqlalchemy`, NO `fastapi`, NO `pydantic`, NO DB client.

### T2. Pure kernel #2 — `packages/cost_engine/closing_period_snapshot.py` (NEW)
- T2.1 `V4Verdict` TypedDict — `{status: Literal["passed","failed","skipped"], failures: list[V4Failure], verified_at: str, product_whitelist_size: int}`. CR 4-3 lesson TypedDict pattern.
- T2.2 `V4Failure` TypedDict — `{product_id: UUID, ledger_qty: Decimal, closing_snapshot_qty: Decimal, message_ko: str}`. AD-15 snake_case.
- T2.3 `verify_closing_period_consistency(*, ledger_aggregate: dict[UUID, Decimal], closing_snapshot_aggregate: dict[UUID, Decimal], product_whitelist: set[UUID]) -> V4Verdict` — V4 rule pure kernel:
  1. product whitelist intersection check: aggregate key not in whitelist → log + ignore (defense-in-depth).
  2. ledger_aggregate vs closing_snapshot_aggregate per-product 일치 검증. 불일치 시 V4Failure append.
  3. failures empty → status='passed'. failures non-empty → status='failed'. ledger aggregate empty → status='skipped'.
- T2.4 `verify_v4_in_verification_runner` flag — industry='service' → status='skipped' + reason_ko='service-only tenant은 inventory 의미 없음' (Story 4-3 service-only ❌ skip pattern + A10 MONTHLY_CLOSING_REPORT capability gate 동등).
- T2.5 stdlib-only (no sqlalchemy). AD-11 layer rule preserved.

### T3. Service layer #1 — `apps/api/modules/m4_inventory/services/closing_period_service.py` (NEW)
- T3.1 `ClosingPeriodService.evaluate_closing_period(session, *, tenant_id, period_key) -> ClosingPeriodResult`:
  - 5-2 `LedgerService.query_period_closing(session, period_key)` 호출 → dict[UUID, Decimal].
  - 5-3 `ClosingGuardService.evaluate_closing_guard(session, tenant_id, period_key)` 호출 → closing_guard_invariant.
  - T1 pure kernel `classify_closing_period_status` + `is_closing_period_allowed` dispatch.
  - Audit log emission (CR 1.1) — `closing_period_blocked` (CLOSING_BLOCKED) emit (CLOSING_READY / ALREADY_CLOSED / EMPTY_PERIOD 시 audit skip).
  - return `ClosingPeriodResult` TypedDict `{status, allowed, closing_per_product, closing_snapshot_count, ledger_event_count, period_key}`.
- T3.2 `ClosingPeriodService.confirm_closing_period(session, *, tenant_id, period_key, actor_id) -> ClosingPeriodConfirmationResult`:
  - 1. `monthly_input_periods.status='closed'` check (idempotent no-op guard) — 이미 closed 시 409 ALREADY_CLOSED typed envelope (no INSERT + no UPDATE + no audit).
  - 2. T3.1 `evaluate_closing_period` 호출 → CLOSING_READY 검증 (CLOSING_BLOCKED / EMPTY_PERIOD / ALREADY_CLOSED 시 409 typed envelope).
  - 3. T1 pure kernel `compute_closing_snapshot` dispatch.
  - 4. 5-2 `LedgerService.append_event(event_type='closing_snapshot', ...)` 호출 per product (per product 1 row INSERT).
  - 5. CR 1.1 audit-first ordering: ledger INSERT before monthly_input_periods UPDATE before audit log INSERT (atomicity guarantee).
  - 6. `monthly_input_periods.status='closed'` UPDATE + `closed_at=func.now()` + `closed_by_actor_id=actor_id` + `closing_snapshot_event_count=N`.
  - 7. `emit_audit_typed(action_class=ActionClass.CLOSING_PERIOD, action='closing_period_confirmed', ..., payload={period_key, closing_snapshot_count, finalized_at, actor_id, tenant_id, trace_id})` INSERT to audit_logs.
  - return `ClosingPeriodConfirmationResult` TypedDict `{confirmed: true, closing_snapshot_count: int, period_key: str, finalized_at: str}`.
- T3.3 `ClosingPeriodService.get_closing_period_audit_trail(session, *, tenant_id, period_key) -> list[AuditLogEntry]`:
  - 5-3 `ClosingGuardService.get_closing_guard_audit_trail` 패턴 그대로 (CR 1.1 observability).
  - audit_logs query filtered by `action_class='closing_period'` for the current period_key.
  - return list[AuditLogEntry] (capped at 10, time DESC).
- T3.4 SQLAlchemy AsyncSession + `emit_audit_typed` wire (raw `emit_audit(` 0건). 5-1 + 5-2 + 5-3 pattern 동일 적용.
- T3.5 4 typed exceptions (`ClosingPeriodError` 409 / `ClosingPeriodBlockedError` 409 / `AlreadyClosedError` 409 / `ClosingPeriodSnapshotInconsistencyError` 409 AD-15 envelope mapping in main.py — distinct from pure helper type for layer boundary).

### T4. Service layer #2 — `apps/api/modules/m6_verification/services/closing_period_snapshot_verifier.py` (NEW, V4 slot fill)
- T4.1 `ClosingPeriodSnapshotVerifier.verify_v4_closing_period_consistency(session, *, monthly_input, baseline, calc_result) -> V4RuleResult`:
  - 5-2 ledger aggregate + 5-3 closing_guard_invariant + 6-1 closing_snapshot ledger events aggregate dispatch.
  - T2 `verify_closing_period_consistency` pure kernel 호출 (ledger_aggregate vs closing_snapshot_aggregate 일치 검증, product whitelist from session).
  - industry='service' → status='skipped' (4-3 service-only skip pattern + A10 MONTHLY_CLOSING_REPORT capability gate 동등).
  - return `V4RuleResult` TypedDict `{status, code: "V4", failures: list[V4Failure], verified_at, message_ko}`.
- T4.2 `VerificationRunner.run_all` extension — V4 slot fill:
  ```python
  # Story 4-3 + 4-4 + 5-3 wire 그대로
  v1 = v1_completeness.run(monthly_input, baseline)
  if v1.status == "failed":
      return Verdict(top_failure=v1)
  # Story 6.1 V4 slot fill (NEW)
  v4 = ClosingPeriodSnapshotVerifier.verify_v4_closing_period_consistency(session, monthly_input, baseline, calc_result)
  if v4.status == "failed":
      return Verdict(top_failure=v4)
  v3 = ClosingInvariantVerifier.verify_v3_closing_invariant(session, monthly_input, baseline, calc_result)
  if v3.status == "failed":
      return Verdict(top_failure=v3)
  v7 = v7_abc_integrity.run(...)  # service-only skip
  if v7.status == "failed":
      return Verdict(top_failure=v7)
  v8 = v8_regression.run(...)  # V8 16 fixture matrix
  ```
- T4.3 A5 audit wire — `verify_v4_closing_period_consistency` action emit (ActionClass.VERIFICATION NEW value).
- T4.4 V4 fail 시 top_failure.code='V4' + message_ko=closing period snapshot inconsistency message (Korean SSOT).

### T5. Wire trigger — `apps/api/modules/m4_inventory/handlers.py` extension
- T5.1 `POST /api/v1/inventory/closing-period/confirm` (NEW) — close-time confirmation wire. Body = `{period_key: str}`. Returns 200 OK or 409 CLOSING_PERIOD_BLOCKED / 409 ALREADY_CLOSED typed envelope. AD-15 envelope + capability gate `MONTHLY_CLOSING_REPORT` (A10 신규).
- T5.2 `GET /api/v1/inventory/closing-period/status?period_key=...` (NEW) — read-only closing period status check. Returns `ClosingPeriodResponse`. AD-15 envelope + capability gate.
- T5.3 `GET /api/v1/inventory/closing-period/audit-trail?period_key=...` (NEW) — audit log query filtered by closing_period actions. AD-15 envelope + capability gate.
- T5.4 `apps/api/modules/m2_input/services/monthly_input_service.py` extension:
  - `MonthlyInputStateResponse` 4 NEW fields (AC #3 wire spec) + 12 existing fields (5-1 + 5-2 + 5-3) 보존.
  - `get_state` extension — `closing_period_service.evaluate_closing_period` + audit_trail query dispatch → 4 NEW fields populate.
  - `confirm_closing_period` NEW method — `closing_period_service.confirm_closing_period` dispatch (T3.2).
  - `attempt_close` 4-2 is_blocked + 5-3 closing_guard 위 additive — `closing_period_service.confirm_closing_period` dispatch (T3.2).
- T5.5 `apps/api/main.py` route 등록 (3 NEW routes) + AD-15 envelope exception handlers (T3.5 4 typed exceptions).
- T5.6 `apps/api/core/audit_action.py` extension — `ClosingPeriodAction` + `VerificationAction` Literal 신규 (AC #7 wire spec).
- T5.7 `apps/api/core/capability.py` extension — `MONTHLY_CLOSING_REPORT` capability SSOT 신규 채움 (manufacturing 3종 ✅ / service-only ❌). `_INDUSTRY_CAPABILITIES` SSOT 동시 갱신.

### T6. Schema — Alembic migration + db_models + response schemas (NEW + extension)
- T6.1 `apps/api/alembic/versions/0017_closing_period.py` (NEW):
  - `down_revision: 0016_closing_guard_invariant`.
  - `op.execute("ALTER TABLE monthly_input_periods ADD CONSTRAINT chk_closing_period_status CHECK (...)")` — AC #4 SQL CHECK.
  - `op.add_column('monthly_input_periods', sa.Column('closing_snapshot_event_count', sa.Integer, server_default='0'))` + `op.create_check_constraint(...)`.
  - `op.add_column('monthly_input_periods', sa.Column('finalized_at', sa.TIMESTAMP(timezone=True), nullable=True))`.
  - `op.add_column('monthly_input_periods', sa.Column('closed_by_actor_id', postgresql.UUID, nullable=True))`.
  - `op.create_index('idx_closing_period_audit', 'audit_logs', ['tenant_id', 'period_key', 'created_at'], postgresql_using='btree')` — closing period audit trail query 지원.
  - Downgrade: drop index + drop columns + drop CHECK constraint.
- T6.2 `apps/api/core/db_models.py` extension — `monthly_input_periods.closing_snapshot_event_count` + `finalized_at` + `closed_by_actor_id` + status CHECK constraint ORM 매핑.
- T6.3 `apps/api/modules/m4_inventory/schemas.py` extension — `ClosingPeriodResponse` (Pydantic + extra='forbid') + `ClosingPeriodConfirmRequest` (period_key) + `ClosingPeriodConfirmationResult` (response) + `ClosingPeriodAuditTrailResponse` (list[AuditLogEntry]). CR 2.3 lesson `extra='forbid'` 보존.
- T6.4 `apps/api/modules/m2_input/services/monthly_input_service.py` extension — `MonthlyInputStateResponse` 4 NEW fields (T5.4 spec).

### T7. Audit-action wire (A5 forward-lock + A7 wire + A8 timeline + A10 capability)
- T7.1 `apps/api/core/audit_action.py` — `ClosingPeriodAction = Literal["closing_period_confirmed", "closing_period_blocked", "closing_period_snapshot_inconsistency"]` 3 values 신규 + `VerificationAction` Literal 1 value 신규 채움: `verify_v4_closing_period_consistency` (extension).
- T7.2 `_ActionRegistry._REGISTRY[ActionClass.CLOSING_PERIOD] = ("closing_period", frozenset({...3 values...}))` — NEW class accepted set.
- T7.3 `_ActionRegistry._REGISTRY[ActionClass.VERIFICATION]` extension — Story 4-3 wire 4 values + 5-3 wire 1 value + 6-1 wire 1 value = 6 values.
- T7.4 `AuditAction` Union type auto-sync (registry guard 시 검증됨).
- T7.5 `apps/api/core/capability.py` extension — `MONTHLY_CLOSING_REPORT = "monthly_closing_report"` Literal 신규 + `_INDUSTRY_CAPABILITIES[MANUFACTURING] |= {MONTHLY_CLOSING_REPORT}` + `_INDUSTRY_CAPABILITIES[MANUFACTURING_SERVICE] |= {MONTHLY_CLOSING_REPORT}` + `_INDUSTORY_CAPABILITIES[MANUFACTURING_SERVICE_OTHER] |= {MONTHLY_CLOSING_REPORT}` (A10 결정 — manufacturing 3종 ✅ / service-only ❌).
- T7.6 `tests/integration/test_audit_action_consistency.py` extension — A5 3-way drift detector (AC #7 spec).
- T7.7 `tests/services/test_audit_action_centralization.py` extension — 6-1 actions 4개 (CLOSING_PERIOD 3 + VERIFICATION 1) 모두 registry set 포함 검증. drift count = 0 유지.
- T7.8 `tests/integration/test_sdr_test_count_drift.py` extension — A7 wire SDR overclaim detector 2 cases (6-1 claim 110+ 매칭).

### T8. Frontend wire — TS mirror + ClosingPeriodConfirmationPanel + ClosingPeriodConfirmDialog (NEW)
- T8.1 `apps/web/lib/closing-period.ts` (NEW) — TS mirror helper #1 (AC #2 spec).
- T8.2 `apps/web/lib/l2-input-inventory-ledger.ts` (extension) — `ClosingSnapshotEvent` interface export (AC #2 spec).
- T8.3 `apps/web/components/m2-input/ClosingPeriodConfirmationPanel.tsx` (NEW) — ClosingGuardBanner (5-3 wire) 위에 additive panel. shadcn `<Alert>` + status 별 conditional rendering (CLOSING_READY / CLOSING_BLOCKED / ALREADY_CLOSED / EMPTY_PERIOD). Korean message SSOT.
- T8.4 `apps/web/components/m2-input/ClosingPeriodConfirmDialog.tsx` (NEW) — shadcn `<Dialog>` + sonner `toast.success` + `toast.error` pattern. POST /closing-period/confirm 호출 + reactive update.
- T8.5 `apps/web/components/m2-input/MonthlyInputTabs.tsx` (extension, 5-3 wire) — 마감 tab 안에 ClosingPeriodConfirmationPanel wire (ClosingGuardBanner + ClosingPeriodConfirmationPanel = vertical stack).
- T8.6 `apps/web/app/[locale]/(dashboard)/m2-input/period/[periodKey]/page.tsx` extension — `<MonthlyInputTabs>` wire + closing period integration + ClosingPeriodConfirmDialog mount.
- T8.7 `apps/web/messages/ko-KR.json` extension — 6-1 신규 ko-KR strings:
  - `closing_period.panel_ready` = "월 마감 확정 가능"
  - `closing_period.panel_blocked` = "마감 차단: 음수 기말재고"
  - `closing_period.panel_already_closed` = "이미 마감됨"
  - `closing_period.panel_empty_period` = "수불 event 0건: 마감 불가"
  - `closing_period.confirm_button` = "마감 확정"
  - `closing_period.dialog_title` = "월 마감 확정"
  - `closing_period.dialog_description` = "기말재고 snapshot 저장 후 reopen 불가. 확정하시겠습니까?"
  - `closing_period.dialog_confirm` = "확정"
  - `closing_period.toast_success` = "월 마감 확정 완료: closing_snapshot {N}건 저장"
  - `closing_period.toast_error_blocked` = "마감 차단: 음수 기말재고"
  - `closing_period.toast_error_already_closed` = "이미 마감됨"

### T9. Capability gate wire + A10 capability matrix v1.3 + A8 inline projection timeline
- T9.1 `apps/api/core/capability.py` extension — `MONTHLY_CLOSING_REPORT` capability 신규 (T7.5 spec). `_INDUSTRY_CAPABILITIES` 4 industries × 12+ capabilities 정합성 자동 검증 (Epic 3 정착 패턴 그대로).
- T9.2 `docs/capability-matrix.md` v1.3 — Changelog v1.3: 6-1 spec 진입 시 `MONTHLY_CLOSING_REPORT` capability wire (A10 결정 — manufacturing 3종 ✅ / service-only ❌).
- T9.3 `docs/closing-period.md` §A8 timeline 섹션 — Epic 3.3 inline projection deprecation timeline 명시 (Epic 6 close-out 시점 fold-in). 6-1 wire 시점 inline projection 보존 상태로 wire (1 epic maintenance window 진행 중).
- T9.4 `tests/integration/test_capability_consistency.py` extension — 6-1 capability wire 1 NEW case (MONTHLY_CLOSING_REPORT 4 industries 검증).

### T10. Tests + docs + 3중 게이트 (T1-T9 동반 + T10 commit-msg finalize)
- T10.1 Pure kernel tests 2 NEW files (T1+T2 spec 본문) — ~30 cases.
- T10.2 Service layer tests 3 NEW files (T3+T4 spec 본문) — ~28 cases.
- T10.3 Drift detector extension 1 NEW file (AC #7 spec) — 4 cases.
- T10.4 SQL CHECK test 1 NEW file (AC #4 spec) — 4 cases.
- T10.5 V8 fixture extension (AC #6 wire spec) — 20 cases (16 existing + 2 V4 + 2 byte-identical + 2 industry skip).
- T10.6 Capability gate 1 NEW + 2 extension — 6 cases.
- T10.7 TS mirror parity 1 NEW file (AC #2 spec) — 6 cases.
- T10.8 Frontend vitest tests 2 NEW files (1 extension) — 9 scenarios.
- T10.9 Playwright E2E 1 NEW file — 4 scenarios.
- T10.10 docs 5 NEW + 5 EXTENSION (AC #9 spec):
  - `docs/closing-period.md` (NEW)
  - `docs/monthly-input.md` §Story 6.1 추가
  - `docs/inventory-ledger.md` §Story 6.1 추가
  - `docs/cost-engine.md` §V4 closing period snapshot 추가
  - `docs/capability-matrix.md` v1.3
  - `docs/conventions.md` §10.8 (NEW) + §10.7 갱신
  - `docs/frontend-toolchain.md` §Story 6.1 추가
- T10.11 3중 게이트 (mandatory CI) — ruff 0 errors / import-linter 2 KEPT / pytest full (skip 옵션 없음) — Epic 5 5-1 (35) + 5-2 (50+) + 5-3 (150+) + A12 (9 CI-shim) + 6-1 (110+) + Story 0-5 (7) + Epic 1-4 누적 회귀 0건. A7 SDR overclaim detector pass (test count = 110+ 매칭 필수). `pnpm test` 9 frontend vitest scenarios pass. `pnpm playwright test --project=chromium apps/web/e2e/closing-period.spec.ts` 4 E2E scenarios pass.
- T10.12 Deferred-work.md close-out:
  - 5-3 3rd sweep deferral T12.2 test file → closed (A12 close-out, commit 74f3a30)
  - 6-1 W1 closing_snapshot ledger event emit → closed (T3.2 wire)
  - 6-1 W2 TS mirror `apps/web/lib/closing-period.ts` → closed (T8.1 wire)
  - 6-1 W3 vitest activation 9 scenarios → closed (T8 + T10.8 wire)
  - 6-1 W4 isolated unit tests 12 cases → closed (T10.1 wire)
  - 6-1 W5 service layer tests 28 cases → closed (T10.2 wire)
