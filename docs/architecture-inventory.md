# Architecture: M4 Inventory Module (Epic 5)

> Story 5.1 — Opening Inventory Auto-Carry Chain

## 모듈 구조

```
apps/api/modules/m4_inventory/
├── __init__.py          # router export
├── handlers.py          # POST /api/v1/inventory/opening-carry/{period_id}
└── services/
    ├── __init__.py
    └── opening_carry_service.py   # OpeningCarryService (5 operations, 4 exceptions)
```

## 레이어 규칙 (AD-11)

```
Pure kernel (packages/services/m2_input/opening_carry.py)
   ↓ import
Service layer (apps/api/modules/m4_inventory/services/opening_carry_service.py)
   ↓ import
HTTP layer (apps/api/modules/m4_inventory/handlers.py)
   ↓ import
FastAPI app (apps/api/main.py — include_router(m4_inventory_router))
```

Pure kernel 은 stdlib-only (no DB, no clock, no random). Service
layer 는 SQLAlchemy AsyncSession + audit-first emit (CR 1.1 lesson).
HTTP layer 는 FastAPI + Pydantic + get_tenant_context dependency.

## 데이터 흐름 (PRD §6.2 수불부 + PRD §F4.1 자동 이월)

```
[월 입력 페이지 mount]
   ↓
GET /api/v2/monthly-input/{period_key}/state
   ↓
MonthlyInputService.get_state(period_key)
   ↓ (Story 5.1 silent hook)
OpeningCarryService.auto_carry_on_get_state(period)
   ↓
  prev period 조회 (chain walk, depth ≤ 12)
   ↓
  build_inventory_projection(rows) → closing[product_id]
   ↓
  compute_carry_chain(prev_closing, current_state) → decisions
   ↓
  resolve_opening_balance(decisions) → final dict[UUID, Decimal]
   ↓
  emit_audit_typed(action="monthly_input_period_opening_carried")
   ↓ (AD-2 audit-first BEFORE UPDATE)
  UPDATE monthly_input_periods.opening_inventory JSONB
   ↓
warning aggregate dispatch (PRD §V3 fire signal — NEGATIVE_CLOSING_INVENTORY)
   ↓
MonthlyInputStateResponse {opening_inventory, opening_inventory_locked, ...}

[첫 행 INSERT]
POST /api/v2/monthly-input/{period_key}/rows
   ↓
MonthlyInputService.save_row(period_key, payload)
   ↓ (INSERT 성공 후)
OpeningCarryService.lock_opening_after_first_row(period)
   ↓
  add _locked=True, _lock_reason_ko="전월 기말 자동 이월" to JSONB
   ↓
  emit_audit_typed(action="monthly_input_period_opening_locked")
   ↓
  UPDATE monthly_input_periods.opening_inventory JSONB

[수동 트리거 (운영자)]
POST /api/v1/inventory/opening-carry/{period_id}
   ↓
OpeningCarryService.trigger_carry_chain_for_period(period_id)
   ↓
  SELECT FOR UPDATE period row
  load prev period (chain walk, depth ≤ 12)
  compute_carry_chain + resolve_opening_balance
  emit_audit_typed(action="monthly_input_period_opening_carried")
  UPDATE monthly_input_periods.opening_inventory JSONB
   ↓
CarryChainResultResponse {decisions, opening_inventory, chain_depth}
```

## AD 바인딩

- **AD-2** (audit-first): 모든 carry/lock write 가 audit_logs INSERT
  먼저 (CR 1.1 lesson).
- **AD-4** (REPEATABLE READ): manual trigger 는 SELECT FOR UPDATE 로
  동시성 보장.
- **AD-11** (layer rule): pure kernel ← service ← HTTP 단방향.
- **AD-15** (cross-language parity): JSONB key snake_case,
  Decimal → str 직렬화로 TS 측 drift 방지.
- **AD-22** (reversal entrypoint): locked opening 해제는 Epic 11
  reversal_log 도입 후 별도 entrypoint.
- **CR 1.1** (idempotent no-op): `auto_carry_on_get_state` 가
  populated/locked 상태에서 silent no-op.

## 향후 (deferral)

- **Story 5.2** (inventory_ledger table): append-only ledger 도입.
  carry chain 결정이 ledger row 가 됨. 현재 audit_logs 에 기록되던
  액션이 inventory_ledger 로 라우팅 전환.
- **Story 5.3** (frontend toast sonner): TS mirror
  `apps/web/lib/l2-input-opening-carry.ts` 추가. 현재 hook 이 silent
  이지만 carry chain 결정 후 toast 노출로 UX 개선.
- **Story 0.5 plumbing**: vitest·Playwright·CI shim 으로 DB-backed
  async 테스트 자동화 (현재 `tests/api/test_opening_carry.py` 의
  9개 stub 활성화).
- **Epic 11** (reversal): locked opening 수동 해제 + reversal_log
  INSERT entrypoint.

## §5.2 Inventory Ledger Architecture (Story 5.2)

### 신규 모듈

```
apps/api/modules/m4_inventory/
  ├── services/ledger_service.py (5 operations)
  │     ├── append_event — AC #4 primary INSERT
  │     ├── query_period_closing — AC #1 SUM(qty) 단일
  │     ├── query_period_closing_all — AC #5 multi-product
  │     ├── query_carry_chain — AC #1 recursive walk ≤ 12
  │     ├── request_reversal — AC #6 Epic 11 forward-fill (501)
  │     ├── get_event — AC #1 단일 event lookup
  │     ├── _assert_not_modifying — AC #3 2축 AST guard
  │     └── _write_inventory_ledger_audit — A5 forward-lock writer
  ├── schemas.py (4 Pydantic types, extra='forbid')
  └── handlers.py (4 routes + Capability.INVENTORY_LEDGER gate)
```

### Capability gate

`Capability.INVENTORY_LEDGER` — manufacturing-kind 3종 ✅, service ❌.
Service-only tenant 가 POST 시도 → 403 INDUSTRY_NOT_SUPPORTED.

### AD-15 envelope mapping (apps/api/main.py)

| Exception | Status | envelope.error.code |
|---|---|---|
| AppendOnlyLedgerViolationError | 500 | APPEND_ONLY_LEDGER_VIOLATION |
| InventoryLedgerInvalidEventTypeError | 422 | INVENTORY_LEDGER_INVALID_EVENT_TYPE |
| InventoryLedgerPeriodKeyFormatError | 422 | INVENTORY_LEDGER_PERIOD_KEY_FORMAT |
| InventoryLedgerReversalNotYetWiredError | 501 | INVENTORY_LEDGER_REVERSAL_NOT_YET_WIRED |

### Hook chain 통합

5-1 `_persist_opening` (carry decisions)
  → 5-2 `_emit_ledger_events_for_decisions` (carry → ledger hook)
  → `LedgerService.append_event` (3중 방어 자동 적용)

5-2 `_emit_inventory_ledger_event_for_row` (monthly input save_row)
  → `LedgerService.append_event`

5-2 `_compute_warnings_aggregate_for_state`
  → `_compute_inventory_projection_for_state` (T8 swap)
  → `LedgerService.query_period_closing_all` (Epic 3.3 AC #5)

### Drift detectors (T9.1+T9.2+T9.5)

- `tests/integration/test_inventory_projection_ledger_swap.py` (T9.5)
  AC #5 swap 무결성 — `TODO(epic-5-5-2) CLOSED` marker + 5개 검증.
- `tests/architecture/test_inventory_ledger_no_mutate.py` (T9.1)
  AST guard 자체 검증 + mutation 금지.
- `tests/integration/test_inventory_ledger_capability.py` (T9.2)
  capability matrix consistency.
- `tests/integration/test_inventory_ledger_event_type_drift.py`
  11-value enum SSOT vs DB CHECK vs call sites.
