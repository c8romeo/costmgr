# Audit Actions — A9/A5 fill + 3-way consistency SSOT

> Story 11.1 (Epic 5 close-out retro §7 A9 결정 wire) + Story 5-1 (A5
> forward-lock) + drift detector 3-way consistency SSOT.
>
> **대상 독자**: Backend 개발자 (action registry extension) + Frontend
> 개발자 (action enum mirror) + Audit 검증자 (drift detector).
>
> **상태**: A9 5개 fill done (reversal_negating/reversal_corrected event
> type + opening_inventory_unlocked action + reversal_request_enabled
> field + service layer reversal handler + UI reversal request form).

## 1. Audit Action Architecture

`apps/api/core/audit_action.py` — Korean SSOT Literal 기반 5-class
partition:

- `AuditAction` — top-level Literal (1 row per audit_log).
- `MonthlyInputPeriodAction` — `monthly_input_periods` 도메인 4 values
  (open / close / lock / **opening_inventory_unlocked**).
- `InventoryLedgerAction` — `inventory_ledger` 도메인 11+ values including
  `reversal_negating_inserted` + `reversal_corrected_inserted` + A5
  `forward_lock_violated`.
- `CostCalculationAction` — `cost_calculation` 도메인 (Epic 4 wire).
- `AIAction` — AI doc-extraction (Epic 0/2 wire).

drift detection:
- backend: `tests/api/test_audit_action_m11_extension.py` (capability +
  11-value event_type registry).
- frontend: `__tests__/audit-action-mirror.test.ts` (TS mirror strip).
- A5 forward-lock: `tests/api/test_audit_action_forward_lock.py`.

## 2. A9 결정 5개 fill (Story 11.1 wire)

Epic 5 close-out retro (2026-08-07) §7 A9 결정 wire:

1. **`reversal_negating` + `reversal_corrected` event type fill** —
   Alembic 0015 11-value CHECK (`event_type IN ('opening_carry_inbound',
   'opening_carry_outbound', 'production_output_inbound',
   'production_material_consumption', 'sales_outbound', 'purchase_inbound',
   'adjustment_inbound', 'adjustment_outbound', 'transfer_inbound',
   'transfer_outbound', 'reversal_negating', 'reversal_corrected')`)
   lines 92-110 wire. 11-1 wire = actual INSERT (T1.1 + T1.2 pure kernel)
   + `ReversalService.execute_reversal` 9-step orchestrator.
2. **`opening_inventory_unlocked` action** — `MonthlyInputPeriodAction`
   Literal extension — `opening_inventory_unlocked` 1 value fill.
   `_ActionRegistry._REGISTRY[ActionClass.MONTHLY_INPUT_PERIOD]` accepted
   frozenset 3 → 4 values.
3. **`reversal_request_enabled` field wire** — `Capability.REVERSAL_REQUEST`
   신규 정의 (manufacturing 3종 ✅ / service-only ❌).
   `MonthlyInputStateResponse.reversal_request_enabled` mirror.
4. **service layer reversal handler** — `apps/api/modules/m11_close/services/reversal_service.py`
   (NEW) — ReversalService class 4 operations.
5. **UI reversal request form** — `apps/web/components/m4-inventory/ReversalRequestDialog.tsx`
   (NEW) + ReversalRequestForm + ReversalRequestButton.

## 3. A5 forward-lock (Story 5-1 wire)

`apps/api/modules/m5_ledger/services/forward_lock_service.py`:39-78
(`ForwardLockService.assert_forward_lock`):

- decision: `monthly_input_periods.status='locked'` 이면 forward emission
  거부. period_status='closed'이면 forward emission 허용 (마감 확정 이전).
- audit: `inventory_ledger_forward_lock_violated` action emit
  (CR 4-4 A5 forward-lock partial).
- carry chain: 5-1 opening carry A5 forward-lock 가드는 12-period chain
  limit + banker's rounding parity.

drift consistency: `tests/api/test_audit_action_forward_lock.py` (A5
drift detector 3-way: backend registry + Alembic 0015 CHECK + TS mirror).

## 4. 3-way consistency SSOT

```
┌─────────────────────────────────────────────────────────────┐
│  Backend (Python) — apps/api/core/audit_action.py          │
│  ─ SSOT Literal types (Korean SSOT) — Literal="..."        │
│  ─ _ActionRegistry._REGISTRY[ActionClass] accepted frozenset│
└────────────────────────┬────────────────────────────────────┘
                         │ 1-way (TS dict strip)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend (TypeScript) — apps/web/lib/audit-action.ts      │
│  ─ const FROZEN: readonly audit action keys + Korean labels │
│  ─ Generated from Python SSOT via bmad-bump-audit-action    │
└────────────────────────┬────────────────────────────────────┘
                         │ 1-way (Alembic 0015 CHECK)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Database (PostgreSQL) — Alembic 0015                      │
│  ─ CHECK (event_type IN ('...', 'reversal_negating', ...)) │
│  ─ CHECK (audit_action IN ('...', 'opening_inventory_...))│
└─────────────────────────────────────────────────────────────┘
```

3-way consistency tests:
- `tests/api/test_audit_action_drift.py` — Python enum vs DB CHECK.
- `apps/web/__tests__/audit-action-mirror.test.ts` — TS dict strip
  parity (CR 1-1 lesson).
- `tests/api/test_audit_action_m11_extension.py` — A9 reversal fill
  parity.

## 5. Cap-mapped audit enforcement

| Capability | Audit action whitelist | Critical-event enum |
|---|---|---|
| `INVENTORY_LEDGER` (5-2) | 11+ event_type values | `reversal_negating` / `reversal_corrected` |
| `MONTHLY_INPUT_PRODUCTION` (3-1) | 4 monthly_input_periods values | `opening_inventory_unlocked` |
| `REVERSAL_REQUEST` (11-1) | 2 critical-event values | `reversal_negating_inserted` / `reversal_corrected_inserted` |
| `MONTHLY_CLOSING_REPORT` (6-1) | 1 critical-event value | `monthly_closing_report_emitted` |
| `COST_CALCULATION` (4.1) | 1 critical-event value | `cost_calculation_emitted` |

Drift: PRD §F11.3 + AD-22 + AD-25 모두 capability gate ⇒ audit action
whitelist가 capability 매트릭스 변경 시 자동 재계산.

## 6. 11-1 wire 시점 추가 fill

| Action | Value | Use case |
|---|---|---|
| `MonthlyInputPeriodAction.OPENING_INVENTORY_UNLOCKED` | `"opening_inventory_unlocked"` | 5-1 opening carry unlock 후 audit. |
| `InventoryLedgerAction.REVERSAL_NEGATING_INSERTED` | `"reversal_negating_inserted"` | AD-22 sign-negating row INSERT 후 audit. |
| `InventoryLedgerAction.REVERSAL_CORRECTED_INSERTED` | `"reversal_corrected_inserted"` | AD-22 corrected row INSERT 후 audit. |
| `InventoryLedgerAction.INVENTORY_LEDGER_REVERSAL_LOGGED` | `"inventory_ledger_reversal_logged"` | INVENTORY_LEDGER 도메인 reversal_log link. |
| `AIAction.M11_REVERSAL_HANDLER_INVOKED` | `"m11_reversal_handler_invoked"` | 핸들러 진입점 audit (5-3 P21 패턴). |

5 values 모두 11-1 wire 시점에 추가 완료.

## 7. Defers (11-1 wire 시점)

1. Alembic 0018 reversal_log namespace 추가 — 11-1 wire는 reversal_log
   audit INSERT를 inventory_ledger audit_logs 테이블에 동시 emit.
2. A5 forward-lock failure payload schema 강제 (5-1 partial) — Epic 11
   11-2 + 11-3 진입 시 payment.
3. AI dashboard action_label strips — Epic 14 AI dashboard wire 진입 시.
4. cost_engine_cache / fiscal_period_cache / closing_snapshot_cache channel
   audit action fill — AD-25 11-3 entry 시점에 channel registry 확장.
5. capability gate 4-tier → 5-tier (PRD §F11.3 capability matrix v1.11) — Epic 11 close-out retro 결정.
