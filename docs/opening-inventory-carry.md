# Opening Inventory Auto-Carry Chain (Story 5.1)

> Epic 5 — PRD §F4.1 자동 기초재고 이월

## 1. 목적 (Why)

PRD §F4.1: "기초재고는 자동으로 전월 기말에서 이월되며, 매월 기초재고를
다시 입력하지 않아도 된다. 첫 행 입력 이후 수동 입력은 차단된다."

이전 Story 3.3 (Negative Inventory & Overcapacity Warning) 에서는
`monthly_input_periods.opening_inventory` JSONB 컬럼이 정적 입력
(MVP 기본값 0) 으로 작동했습니다. Story 5.1 부터는:

1. **자동 이월**: GET `/state` 호출 시 (silent hook) 또는 POST
   `/opening-carry/{period_id}` 호출 시 (manual trigger) 전월
   `monthly_input_rows` 의 closing balance 가 다음 달 opening 으로
   자동 전파됩니다.
2. **수동 잠금**: 첫 row INSERT 직후 `opening_inventory._locked = true`
   마커가 추가되며, 이후 `stream='opening_inventory'` POST 는
   `400 MONTHLY_INPUT_OPENING_MANUAL_EDIT` 으로 거부됩니다.
3. **체인 깊이 한도**: 12-period (1년) 이상 자동 체인은
   `422 MONTHLY_INPUT_CARRY_CHAIN_LIMIT` 으로 거부되며, 운영자가
   period 별로 수동 트리거해야 합니다.

## 2. 아키텍처 (AD-1 / AD-11 레이어)

```
Pure kernel (stdlib-only, deterministic, no DB):
  packages/services/m2_input/opening_carry.py
    - INVENTORY_PERIOD_CHAIN_LIMIT = 12
    - compute_carry_chain() — prev closing + current state → decisions
    - resolve_opening_balance() — decisions → final dict[UUID, Decimal]
    - lock_opening_after_first_row() — JSONB sub-key lock marker
    - validate_opening_lock_consistency() — shape guard

Service layer (SQLAlchemy AsyncSession + audit-first):
  apps/api/modules/m4_inventory/services/opening_carry_service.py
    - OpeningCarryService (5 operations)
      · trigger_carry_chain_for_period (manual trigger)
      · auto_carry_on_get_state (silent hook, idempotent)
      · lock_opening_after_first_row (first-row hook)
      · recompute_opening_on_prev_change (prev mutation hook)
      · validate_opening_lock_consistency (defense-in-depth)
    - 4 typed exceptions (AD-15 §4 envelope):
      · MonthlyInputOpeningManualEditError (400)
      · MonthlyInputOpeningLockViolationError (500)
      · MonthlyInputCarryChainLimitError (422)
      · MonthlyInputCarryPrevPeriodNotFoundError (422)

HTTP layer (FastAPI):
  apps/api/modules/m4_inventory/handlers.py
    - POST /api/v1/inventory/opening-carry/{period_id}
      → Manual trigger for opening inventory carry chain
      → Returns CarryChainResultResponse

TS mirror (deferred to Story 5.3 + Story 0.5 plumbing):
  apps/web/lib/l2-input-opening-carry.ts (not yet created)
```

## 3. PRD §6.2 수불부 (PRD §6.2 inventory equation)

PRD §6.2 수불 공식 (carry-applied form):

```
opening[product] = closing[product]_from_prev_period
inbound[product] = sum(purchases.qty) + sum(production_output.qty)
outbound[product] = sum(sales.qty)
closing[product] = opening[product] + inbound - outbound
```

QTY_QUANTUM = `Decimal("0.0001")` (NUMERIC(18,4)). ROUND_HALF_EVEN
적용 (CR 0-4 lesson — TS/Python ROUND_HALF_EVEN parity).

Story 5.1 는 opening[product] 자동 전파만 wire. inbound/outbound
합산은 Story 3.3 의 `build_inventory_projection` 으로 처리되며,
closing → 다음 opening 연결이 본 story 의 신규 기능입니다.

## 4. Wire 시퀀스

### 4.1 자동 (silent hook)

```
GET /api/v2/monthly-input/{period_key}/state
  ↓
MonthlyInputService.get_state(period_key)
  ↓
OpeningCarryService.auto_carry_on_get_state(period)
  ↓ (idempotent)
  · opening_inventory 비어있고 prev_period 존재 → compute_carry_chain
  · opening_inventory 이미 locked or populated → no-op
  ↓
  audit_logs INSERT (action: monthly_input_period_opening_carried)
  ↓
  monthly_input_periods.opening_inventory JSONB UPDATE
  ↓
warning aggregate dispatch (PRD §V3 fire signal)
```

### 4.2 수동 (operator trigger)

```
POST /api/v1/inventory/opening-carry/{period_id}
  ↓
trigger_opening_carry (handler)
  ↓
OpeningCarryService.trigger_carry_chain_for_period(period_id)
  ↓
  · SELECT FOR UPDATE period row
  · load prev period (chain walk, depth ≤ 12)
  · build prev period's closing balance
  · compute_carry_chain → decisions
  · audit_logs INSERT BEFORE UPDATE (AD-2)
  · monthly_input_periods.opening_inventory JSONB UPDATE
  ↓
  CarryChainResultResponse (decisions, opening_inventory, chain_depth)
```

## 5. Audit trail (CR 1.1 lesson — append-only + idempotent)

5-1 에서 emit 하는 audit 액션:

| Action literal | ActionClass | 의미 |
|---|---|---|
| `monthly_input_period_opening_carried` | MONTHLY_INPUT_PERIOD | auto/manual carry chain 적용 |
| `monthly_input_period_opening_locked` | MONTHLY_INPUT_PERIOD | 첫 row INSERT 후 lock 마커 추가 |

audit_log 페이로드에는 다음이 포함됩니다:
- `tenant_id`, `period_key`, `trigger_source` (`auto_get_state` / `manual`)
- `prev_period_key` (carry 출처)
- `decisions_count` + `decisions[]` (carry chain 결정 목록, stale/recompute 플래그 포함)
- `trace_id` (요청 trace)

## 6. Edge case 정책

### 6.1 Stale value 자동 overwrite

`current_period_state` 에 사용자 입력값이 있는데 prev period 의
projection 과 일치하지 않으면 silently overwrite 됩니다 (cj-style
default). 단, audit log 의 before/after 스냅샷에 prev_old 값이
캡처되어 사후 추적 가능합니다 (CR 1.1 lesson).

### 6.2 Locked opening

`opening_inventory._locked = true` 이면 `auto_carry_on_get_state` 와
`recompute_opening_on_prev_change` 모두 silent no-op. 운영자가
수동으로 lock 해제하려면 Epic 11 reversal entrypoint (별도 story)
필요.

### 6.3 Chain depth > 12

자동 trigger (`auto_carry_on_get_state`) 는 무한 루프 방지를 위해
12-period 제한 내에서만 작동. Manual trigger 는 422
`MONTHLY_INPUT_CARRY_CHAIN_LIMIT` 으로 거부되며, 운영자가
period 별로 수동 호출해 점진적으로 확장 가능.

## 7. Capability gate

`Capability.OPENING_INVENTORY` 는 모든 manufacturing-kind industry
(manufacturing, manufacturing_service, manufacturing_service_other)
에 wired. Service industry 는 자동 no-op (carry chain returns empty
decisions — inventory-bearing products 없음).

## 8. 3중 게이트 (CR 4-3 F-1 lesson)

- **ruff**: `packages/services/m2_input/opening_carry.py`,
  `apps/api/modules/m4_inventory/`,
  `apps/api/modules/m2_input/services/monthly_input_service.py`,
  `tests/services/test_opening_carry.py` 모두 clean.
- **import-linter**: `cost_engine_forbidden_io` + 
  `engine_core_to_adapters_forbidden` KEPT.
- **pytest**: `tests/services/test_opening_carry.py` 23 passed
  (determinism + banker's rounding parity pinned).

## 9. 향후 story (deferral)

- **Story 5.2** (inventory_ledger table): append-only ledger.
  5-1 의 opening carry + 5-2 의 ledger 가 결합되면
  `inventory_ledger.action` enum 에 OPENING_CARRY_AUTO,
  OPENING_CARRY_STALE_OVERWRITE, OPENING_CARRY_FIRST_ROW_LOCK
  추가 후 alembic migration 으로 DB CHECK 제약 도입.
- **Story 5.3** (frontend toast sonner): TS mirror
  (`apps/web/lib/l2-input-opening-carry.ts`) 추가.
- **Story 0.5 plumbing**: vitest·Playwright·CI shim 으로 DB-backed
  async 테스트 자동화.
- **Epic 11** (reversal entrypoint): locked opening 수동 해제 +
  reversal_log INSERT.

## §5.2 Carry Decision → Ledger Event Hook (Story 5.2)

`OpeningCarryService._persist_opening` 가 carry decision 마다
`_emit_ledger_events_for_decisions` 를 호출하여 `inventory_ledger`
테이블에 append-only 행을 emit 합니다.

### Decision → event_type 매핑

| `OpeningCarryDecision.recompute` | `event_type` |
|---|---|
| `False` (정상 자동 이월) | `opening_carried` |
| `True` (이전 결정 silently overwrite) | `opening_carried_stale_overwrite` |

### emit 시점

- Manual trigger: `POST /api/v1/inventory/opening-carry/{period_id}`
  → 5-1 `_persist_opening` 호출 → 5-2 `_emit_ledger_events_for_decisions`
  가 같은 transaction 안에서 ledger 행 INSERT.
- Silent trigger: `MonthlyInputService.get_state` 호출 시
  `auto_carry_on_get_state` (idempotent no-op check) → 5-1 carry
  applied → 5-2 ledger emit. 이미 opening 이 lock 된 상태에서는
  silent no-op (carry 적용 X → ledger emit X).

### metadata 캡처

각 ledger 행의 metadata JSONB:
- `prev_period_key`: carry source period (예: `2026-06`)
- `is_stale`: `OpeningCarryDecision.is_stale` (True if prev projection
  과 current opening 불일치)
- `trigger_source`: `"manual"` (POST /opening-carry) or `"silent"`
  (GET /state hook)

### Audit-first wire (A5 forward-lock)

`_emit_ledger_events_for_decisions` 는 `LedgerService.append_event` 를
호출 → `_write_inventory_ledger_audit(action="inventory_ledger_event_appended", ...)`
가 audit 행을 **먼저** emit → 그 다음 ledger INSERT. Drift detector:
`tests/integration/test_audit_action_consistency.py` (ActionClass
INVENTORY_LEDGER ↔ DB CHECK ↔ call sites 3-way).

## Story 5.3 — Closing Guard (2026-08-06)

M14 TS mirror wire (apps/web/lib/l2-input-opening-carry.ts) — Story 5.1 carry-over close-out:
- `OpeningCarryState` type + `isOpeningLocked()` + `canEditOpening()` + `formatCarryChainReason()` helpers
- banker's rounding parity + Decimal serialization (AD-15 §11)

L8 SQL CHECK constraint (`chk_opening_inventory_manual_reject`):
- monthly_input_rows table guard: `stream != 'opening_inventory' OR (stream = 'opening_inventory' AND created_via = 'auto_carry')`
- Alembic 0016 wire: column + CHECK + index
- defense-in-depth: bulk import / direct INSERT path 우회 시에도 service-layer reject와 동등 enforcement

Manual edit reject UI (frontend):
- `apps/web/components/m2-input/MonthlyInputRowForm.tsx` — for `stream='opening_inventory'` rows
- When `opening_inventory_locked=true` → form field disabled + helper text + sonner toast.error
- shadcn `<Form>` primitive + `<Input disabled>` + `<Tooltip>`

3중 defense-in-depth (manual edit reject):
- 5-1 service-layer `manual_edit_reject` validation
- L8 SQL CHECK constraint (chk_opening_inventory_manual_reject)
- 5-3 frontend form disabled + sonner toast.error
