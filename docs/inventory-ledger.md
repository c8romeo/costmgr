# Inventory Ledger Append-Only Events (Story 5.2)

> Epic 5 — PRD §F4.2 재고 이력 (Inventory Ledger)

## 1. 목적 (Why)

PRD §F4.2: "모든 재고 변동(inbound / outbound / carry / adjustment)은
append-only 재고 원장에 기록되며, UPDATE/DELETE 가 차단된다."

Story 5.1 (Opening Inventory Auto-Carry Chain) 이 전월 기말을 다음
달 기초로 자동 이월하는 hook을 wire 했다면, Story 5.2 는 그 hook이
발동될 때마다 `inventory_ledger` 테이블에 append-only 행을 남겨,
**재고 변동의 전체 이력(누가·언제·왜·얼마나)** 을 추적 가능하게 만든다.

Story 5.2 의 핵심:

1. **Append-only invariant (AD-2)** — PostgreSQL `BEFORE UPDATE OR
   DELETE` row-level trigger (`Alembic 0015`) 가 production gate.
2. **3중 방어 (defense-in-depth)** — DB trigger + service-layer AST
   guard + audit log.
3. **11-value event_type enum** — opening_carried /
   purchase_inbound / sales_outbound / production_output_inbound /
   reversal_corrected 등 11가지 변동 사유를 self-describing payload로
   강제한다.
4. **Epic 3.3 inline projection swap (AC #5)** —
   `MonthlyInputService` 가 더 이상 `build_inventory_projection` 의
   자체 집계 결과를 쓰지 않고, `LedgerService.query_period_closing_all`
   을 통해 원장의 SUM(qty) 를 canonical source 로 사용한다.

## 2. 아키텍처 (AD-1 / AD-11 레이어)

```
Pure kernel (stdlib-only, deterministic, no DB):
  packages/services/m4_inventory/ledger.py (T1)
    - INVENTORY_LEDGER_EVENT_TYPES (11-value frozenset)
    - INVENTORY_LEDGER_QTY_QUANTUM = Decimal("0.0001")
    - SOURCE_CARRY_CHAIN / SOURCE_MONTHLY_INPUT / SOURCE_REVERSAL_REQUEST / ...
    - validate_event_type(event_type)
    - validate_event_shape(event_id, product_id, period_key, qty, ...)
    - build_event_payload(...) -> dict (self-describing)
    - AppendOnlyLedgerError (kernel exception)

  packages/services/m4_inventory/ledger_query.py (T2)
    - build_period_closing_query() -> LedgerQuery (SUM(qty) per product)
    - build_carry_chain_query() -> LedgerQuery (recursive CTE ≤ 12 periods)
    - assert_tenant_guarded(query) — AD-4 RLS predicate check

Service layer (SQLAlchemy AsyncSession + audit-first):
  apps/api/modules/m4_inventory/services/ledger_service.py
    - LedgerService (5 operations)
      · append_event (AC #4 primary INSERT)
      · query_period_closing (AC #1 SUM(qty) 단일 product)
      · query_period_closing_all (AC #5 multi-product aggregation)
      · query_carry_chain (AC #1 recursive walk)
      · request_reversal (AC #6 forward-fill — Epic 11 owns INSERT)
      · get_event (AC #1 단일 event lookup)
    - 4 typed exceptions (AD-15 §4 envelope):
      · AppendOnlyLedgerViolationError (500)
      · InventoryLedgerInvalidEventTypeError (422)
      · InventoryLedgerPeriodKeyFormatError (422)
      · InventoryLedgerReversalNotYetWiredError (501)
    - _assert_not_modifying AST guard (AC #3 2축)
    - _write_inventory_ledger_audit writer (A5 forward-lock)

Pydantic schemas (FastAPI-coupled):
  apps/api/modules/m4_inventory/schemas.py (T5.3)
    - LedgerEventCreateRequest (extra='forbid')
    - PeriodClosingResponse (dict[str, str])
    - CarryChainEntry / CarryChainResponse (list with depth)
    - ReversalRequestCreate (event_id + reason max_length=500)

HTTP layer (FastAPI):
  apps/api/modules/m4_inventory/handlers.py (T4.1)
    - POST /api/v1/inventory/ledger/events
    - GET /api/v1/inventory/ledger/period-closing
    - GET /api/v1/inventory/ledger/carry-chain
    - POST /api/v1/inventory/ledger/reversal-requests

Capability gate:
  apps/api/core/capability.py::Capability.INVENTORY_LEDGER
    - manufacturing / manufacturing_service / manufacturing_service_other ✅
    - service ❌ (403 INDUSTRY_NOT_SUPPORTED)

AD-15 envelope mapping (apps/api/main.py T4.4):
  - AppendOnlyLedgerViolationError → 500 APPEND_ONLY_LEDGER_VIOLATION
  - InventoryLedgerInvalidEventTypeError → 422 INVENTORY_LEDGER_INVALID_EVENT_TYPE
  - InventoryLedgerPeriodKeyFormatError → 422 INVENTORY_LEDGER_PERIOD_KEY_FORMAT
  - InventoryLedgerReversalNotYetWiredError → 501 INVENTORY_LEDGER_REVERSAL_NOT_YET_WIRED

TS mirror (deferred to Story 5.3 + Story 0.5 plumbing):
  apps/web/lib/l2-inventory-ledger.ts (not yet created)

Hook chain (T4.2 + T4.3):
  monthly_input_service.save_row INSERT path
    → _emit_inventory_ledger_event_for_row (stream → event_type mapping)
    → LedgerService.append_event
  opening_carry_service._persist_opening (5-1)
    → _emit_ledger_events_for_decisions (opening_carried / _stale_overwrite)
    → LedgerService.append_event

Epic 3.3 inline projection swap (T8):
  monthly_input_service._compute_warnings_aggregate_for_state
    → _compute_inventory_projection_for_state
    → LedgerService.query_period_closing_all
    (replaces direct build_inventory_projection call)
```

## 3. Append-only 3중 방어 (AD-2 / AC #3)

| 축 | 위치 | 역할 |
|---|---|---|
| 1. DB trigger | `Alembic 0015 inventory_ledger_append_only` | PostgreSQL row-level `BEFORE UPDATE OR DELETE` trigger 가 `SQLSTATE P0001` (custom) 로 raise. Production gate. |
| 2. Service-layer AST guard | `LedgerService._assert_not_modifying` | UPDATE/DELETE/TRUNCATE/DROP TABLE 키워드 감지 → 즉시 `AppendOnlyLedgerViolationError` raise. Early fail. |
| 3. Audit log | `_write_inventory_ledger_audit` | 모든 rejection 은 `inventory_ledger_event_rejected` audit 행으로 남김 (관측성). |

3개 축 중 어느 하나가 fail 해도 invariant 유지. Drift detector:
- `tests/architecture/test_inventory_ledger_no_mutate.py` (T9.1)
  AST guard 자체의 존재 + 키워드 4종 + 예외 클래스 pin.
- `tests/integration/test_inventory_ledger_event_type_drift.py`
  11-value enum SSOT 와 DB CHECK constraint 의 hash 일치 검증.

## 4. 11-value event_type enum (AC #2)

```python
INVENTORY_LEDGER_EVENT_TYPES = frozenset({
    # Carry chain (5-1 wire)
    "opening_carried",
    "opening_carried_stale_overwrite",
    # Streams (3.1 wire, 5-2 부터 ledger 로 라우팅)
    "purchase_inbound",
    "sales_outbound",
    "production_output_inbound",
    "production_material_consumption",
    # Manual adjustments
    "adjustment_positive",
    "adjustment_negative",
    # Reversal sequence (Epic 11 forward-fill)
    "reversal_negating",
    "reversal_corrected",
    # Closing snapshot (materialized balance, NOT a flow event)
    "closing_snapshot",
})
```

`query_period_closing` / `query_period_closing_all` 은
`closing_snapshot` 을 집계에서 제외 (PRD §6.2: closing_snapshot 은
materialized balance, not a flow event).

## 5. Period key AD-24 typed pattern

`period_key` MUST match `^\d{4}-(0[1-9]|1[0-2])$` — 예: `2026-07`.
- Pydantic 필드 validator (`LedgerEventCreateRequest._validate_period_key_format`)
- Service-layer re-validation (`InventoryLedgerPeriodKeyFormatError`)
- Pure kernel `validate_event_shape`
- DB CHECK constraint (마지막 gate)

Virtual budget keys (`2026-07#B1`) 는 Epic 8 §M8 scope — 명시적으로 제외.

## 6. Capability gate (AC #2)

`Capability.INVENTORY_LEDGER` 는 manufacturing-kind industry 3종에만 부여:

| Industry | `INVENTORY_LEDGER` |
|---|---|
| manufacturing | ✅ |
| service | ❌ (403 INDUSTRY_NOT_SUPPORTED — BOM 없음 → 원장 의미 없음) |
| manufacturing_service | ✅ |
| manufacturing_service_other | ✅ |

Drift protection: `tests/integration/test_inventory_ledger_capability.py`
(T9.2) 가 matrix 일관성을 검증.

## 7. Epic 3.3 inline projection swap (AC #5)

Story 3.3 `build_inventory_projection` 의 inline 집계는 Story 5.2 부터
deprecated:

- Before: `MonthlyInputService._compute_warnings_aggregate_for_state`
  → `build_inventory_projection(rows, opening_balance)` (legacy inline)
- After: → `_compute_inventory_projection_for_state` (T8 wrapper)
  → `LedgerService.query_period_closing_all(period_key=...)` (canonical)

Epic 5 maintenance window 동안 `build_inventory_projection` 자체는
정의만 유지되며 (Story 5-1 carry-chain path 에서 여전히 사용),
Epic 6 close-out retro 에서 둘 다 제거 예정.

Drift detector: `tests/integration/test_inventory_projection_ledger_swap.py`
(T9.5) 가 5개 검증 케이스로 swap 무결성을 강제.

## 8. AD-22 reversal entrypoint forward-fill (AC #6)

`POST /api/v1/inventory/ledger/reversal-requests` 는:

1. `target event_id` 가 (a) 존재하고 (b) 호출자 tenant 에 속하는지 검증.
2. `inventory_ledger_reversal_requested` audit marker emit.
3. `InventoryLedgerReversalNotYetWiredError` (501) raise.

Epic 11 M11 모듈 authority 가 실제 reversal sequence INSERT
(`reversal_negating` + `reversal_corrected` 두 행) 를 담당할 때까지
이 entrypoint 는 request 만 acknowledge 하고 DB write 는 하지 않는다.
Epic 11 wire 시점에 501 → 200 + reversal sequence 반환으로 변경.

## 9. Audit-first wire (A5 forward-lock, CR 1.1)

모든 state-changing operation 은 audit 행을 **먼저** 쓴다:

```python
async def append_event(...) -> InventoryLedger:
    # (1) pure-kernel payload build (validates event_type / period_key / qty)
    # (2) audit-first emit (BEFORE INSERT)
    await self._write_inventory_ledger_audit(action="inventory_ledger_event_appended", ...)
    # (3) INSERT
    self.session.add(row); await self.session.flush()
    # (4) on IntegrityError: emit inventory_ledger_event_rejected audit
```

Audit destination: `_ActionRegistry.validate(action_class=INVENTORY_LEDGER, action=...)`
이 registry-routed destination 으로 emit. Drift detector:
- `tests/integration/test_audit_action_consistency.py`
- `tests/integration/test_inventory_ledger_event_type_drift.py`

## 10. 운영 시나리오 (Operator guide)

### 10.1. Carry chain 자동 발동 시 ledger 행 생성

POST `/api/v1/inventory/opening-carry/{period_id}` → 5-1 carry
service 가 opening_decided → `_emit_ledger_events_for_decisions`
호출 → `opening_carried` 또는 `opening_carried_stale_overwrite` 행
INSERT (qty = opening_qty, source = "carry_chain", metadata에
prev_period_key + is_stale + trigger_source 포함).

### 10.2. 월별 입력 저장 시 ledger 행 생성

POST `/api/v1/monthly-input/rows` 의 INSERT path 에서
`stream ∈ {"purchases", "sales", "production"}` AND
`product_id IS NOT NULL` AND `qty IS NOT NULL` 조건 만족 시:

| stream | event_type | direction |
|---|---|---|
| purchases | `purchase_inbound` | + qty |
| sales | `sales_outbound` | − qty |
| production | `production_output_inbound` | + qty (output product_qty) |

Material consumption (input side of production) 은 Epic 6 wire.

### 10.3. Reversal 요청 시

POST `/api/v1/inventory/ledger/reversal-requests` body:
```json
{ "event_id": "<uuid>", "reason": "<한글 가능, ≤ 500자>" }
```

501 응답 + audit marker (`inventory_ledger_reversal_requested`).
실제 reversal sequence INSERT 는 Epic 11 이후.

### 10.4. 운영자가 직접 backfill 행 생성 (recovery)

POST `/api/v1/inventory/ledger/events` body:
```json
{
  "product_id": "<uuid>",
  "period_key": "2026-07",
  "event_type": "adjustment_positive",
  "qty": "10.0000",
  "trace_id": "<optional uuid>",
  "metadata": { "reason": "operator recovery" }
}
```

Pure kernel 이 event_type (11-value whitelist) + period_key
(`YYYY-MM`) + qty (Decimal, nullable) 검증 후 INSERT.

### 10.5. Closing balance 조회

GET `/api/v1/inventory/ledger/period-closing?period_key=2026-07`
→ `{ "period_key": "...", "closing": { "<product_id>": "<qty>", ... }, "trace_id": "..." }`

`closing_snapshot` 행 제외. Multi-product aggregation 은
`LedgerService.query_period_closing_all` 단일 SQL query.

### 10.6. Carry chain walk 조회

GET `/api/v1/inventory/ledger/carry-chain?product_id=...&period_key=2026-07&depth=12`
→ product 의 opening_carried 이벤트를 12-period 까지 recursive walk.

## 11. Layered failures (어디서 잡히나)

| 입력/상태 | 검증 단계 | 에러 envelope |
|---|---|---|
| event_type not in 11-value | pure kernel → service re-raise | 422 INVENTORY_LEDGER_INVALID_EVENT_TYPE |
| period_key not YYYY-MM | pure kernel → service re-raise | 422 INVENTORY_LEDGER_PERIOD_KEY_FORMAT |
| DB trigger fires (UPDATE/DELETE) | Alembic 0015 trigger | 500 APPEND_ONLY_LEDGER_VIOLATION |
| service-layer UPDATE/DELETE issued | AST guard | 500 APPEND_ONLY_LEDGER_VIOLATION (early fail) |
| DB CHECK constraint violation | PostgreSQL | 500 (with IntegrityError → audit `event_rejected`) |
| service tenant POST | capability gate | 403 INDUSTRY_NOT_SUPPORTED |
| reversal INSERT requested | M4 entrypoint | 501 INVENTORY_LEDGER_REVERSAL_NOT_YET_WIRED |

## 12. Changelog

- 2026-08-04 — Story 5.2: ledger append-only events wire. 11-value
  event_type + 6-value action + 5 service operations + 4 HTTP routes
  + 4 Pydantic schemas + 3중 방어 + Epic 3.3 inline projection swap
  + AC #6 reversal forward-fill (Epic 11 owner).

## Story 5.3 — Closing Guard + V3 Sync (2026-08-06)

W2 TS mirror wire (apps/web/lib/l2-input-inventory-ledger.ts) — Story 5.2 carry-over close-out:
- `LedgerEventType` 11 values + `LedgerEvent` interface + `ClosingBalance` + `ClosingInvariant` + `ClosingInvariantCode`
- `classifyClosingInvariant()` + `isCloseBlocked()` + `formatNegativeClosingBannerKo()` helpers
- banker's rounding parity + Decimal serialization (AD-15 §11)

W3 vitest activation (8 cases) — Story 5.2 carry-over close-out:
- 6 unskip + 3 NEW 5-3 cases (negative_closing_invariant_ko, v3_verdict_envelope_ko, closing_guard_audit_payload_ko)
- pytest.skip markers removed (Story 0.5 vitest activation done)

W4 isolated unit tests (8 cases) — Story 5.2 carry-over close-out:
- `tests/services/m4_inventory/test_emit_inventory_ledger_event_for_row.py` NEW
- W4: test_emit_event_for_purchase_inbound_row, _sales_outbound_row, _production_output_inbound_row, _production_with_bom_consumption, _idempotent_skip, _invalid_event_type_rejected, _qty_decimal_quantization, _audit_first_ordering

W1 BOM-aware reconciliation (production_output + production_material_consumption 동시 emit):
- `production_consumption.py` pure kernel (BOM matrix 비율 → consumption qty calculation)
- `closing_guard_service.emit_production_ledger_events()` dispatch
- 5-2 deferral #9 resolved

## Story 6.2 — Monthly Closing Report Aggregator + V4 4-source extension (2026-08-08)

### §5.2 Story 6.2 Closing Report Aggregator

Story 6.2 의 monthly closing report 는 **5-2 ledger 의 read-only consumer** 이다.
**Append-only invariant (AD-2) 가 closing report 에서도 보존** — closing report 는
ledger 의 row 를 read 만 하고 절대 write 하지 않는다.

3-source read-only join (closing snapshot × ledger events × fiscal period snapshot):

```python
# packages/services/m4_inventory/monthly_closing_report.py
class MonthlyClosingReportAggregate(NamedTuple):
    period_key: str
    closing_snapshot_count: int     # 5-1 + 6-1 wire count
    ledger_event_count: int         # 5-2 wire count
    fiscal_period_snapshot_count: int  # 6-1 wire count
    closing_per_product: dict[UUID, Decimal]  # ledger_aggregate SUM(qty) per product
    view_mode: Literal["READY", "PARTIAL", "EMPTY"]
    v4_status: Literal["passed", "failed", "skipped"]
```

View mode 분류 (3-state classifier):
- **READY** — 3 sources 모두 populated + V4 PASS → green Alert + 4 KPI 카드
- **PARTIAL** — 일부 source 만 populated OR V4 FAIL but non-blocking → amber Alert + toast.info
- **EMPTY** — 3 sources 모두 count=0 → 409 `MonthlyClosingReportEmptyError` + muted Alert + toast.warning

V4 closing-period consistency 4-source extension:
- **Story 6.1**: V4 2-source wire (closing snapshot × fiscal period snapshot)
- **Story 6.2**: V4 4-source extension (ledger + closing snapshot + fiscal period
  snapshot + product whitelist) → `verify_monthly_closing_report_consistency`
- **AD-12 ordering**: V1 → **V4** → V3 → V7 → V8 (5-rule ordering, V4 slot 2)
- **V4 source_count invariant**: 4 sources ALWAYS present in verdict envelope

Wire contract (5-2 ledger READ-ONLY):
- `closing_snapshot_count` = `SELECT COUNT(*) FROM inventory_ledger WHERE event_type='closing_snapshot' AND tenant_id=:tenant_id AND period_key=:period_key` (read-only)
- `ledger_event_count` = `SELECT COUNT(*) FROM inventory_ledger WHERE tenant_id=:tenant_id AND period_key=:period_key` (read-only)
- `fiscal_period_snapshot_count` = `SELECT COUNT(*) FROM monthly_input_periods WHERE tenant_id=:tenant_id AND period_key=:period_key AND status='closed'` (read-only)

CR 1.1 audit-first wire + idempotent no-op skip on re-view:
- 1st GET → `monthly_closing_report_viewed` audit emit
- 2nd+ GET → idempotent no-op skip (audit_action='viewed' 가 이미 존재하면
  audit emit skip)

### §5.2.1 KRW/USD Dual Display (PRD §F5.2)

PRD §F5.2 — KRW/USD 동시 표시. 한국은행 USD/KRW 매매기준율 기준.

```python
# packages/services/m4_inventory/monthly_closing_report.py
USD_QUANTUM = Decimal("0.01")  # NUMERIC(18,2) AD-8 SSOT

def compute_usd_from_krw(
    amount_krw: Decimal,
    exchange_rate: Decimal,
) -> Decimal:
    """KRW → USD conversion (ROUND_HALF_EVEN banker's rounding).
    CR 0-4 lesson: USD 1.005 → 1.00 (banker's rounding precision).
    """
    return (amount_krw / exchange_rate).quantize(USD_QUANTUM, rounding=ROUND_HALF_EVEN)

def format_period_closing_krw_usd(
    amount_krw: Decimal,
    currency_pair: CurrencyPair,
) -> PeriodClosingDisplay:
    """PRD §F5.2 dual display envelope.
    Returns: PeriodClosingDisplay(amount_krw, amount_usd, currency_pair_display_ko)
    """
```

TS mirror (`apps/web/lib/monthly-closing-report-parity.ts`):
- `Decimal.set({ rounding: Decimal.ROUND_HALF_EVEN })` on module load
- `parityQuantizeUSD` + `parityComputeUsdFromKrw` + `parityFormatPeriodClosingKrwUsd`
  helpers
- Drift detector: `tests/integration/test_monthly_closing_report_label_consistency.py`
  (9 cases, T9.7)

### §5.2.2 V8 18-fixture matrix extension (A11 PRIMARY)

V8 골든 fixture count 16 → **18**:
- `closing-period-b-small.json` (V4 PASS)
- `closing-period-b-standard.json` (V4 FAIL)
- `fiscal-period-snapshot-b-small.json` (PASS)
- `fiscal-period-snapshot-b-standard.json` (FAIL)

Drift detectors:
- `tests/regression_v8/test_regression_v8_fixtures.py::test_v8_fixture_count_is_18`
- `tests/cost_engine/test_regression_v8_placeholder.py::test_v8_fixture_count_now_18_in_story_6_2`
- `tests/architecture/test_api_calls_only_ports.py::ALLOWED_SERVICE_SUBMODULES`
  includes `"packages.services.m4_inventory.monthly_closing_report"`

### §5.2.3 Carry-over close

- 5-1 (Opening Auto-Carry) + 5-2 (Inventory Ledger) + 5-3 (Closing Guard) +
  0.5 (Frontend Plumbing) + A12 (T12.2 deferred test file close-out) +
  6-1 R4 triage 9 DEFER items (frontend + capability matrix v1.8 + 51 NEW tests
  + 1 NEW doc) + 6-1 T10.5 deferred V4 골든 fixture fill (6-2 carry-over close
  integrated) 모두 6-2 spec 진입 시점에 close.