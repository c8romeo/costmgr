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

## §5.3 Negative Closing Inventory Guard Architecture (Story 5.3)

### 신규 모듈

```
apps/api/modules/m4_inventory/
  ├── services/closing_guard_service.py (4 operations, 5 typed exceptions)
  │     ├── evaluate_closing_guard — AC #1 read-only invariant computation
  │     ├── request_close_attempt — AC #2 block-on-negative (409)
  │     ├── emit_production_ledger_events — AC #3 BOM-aware reconciliation
  │     └── validate_closing_invariant_against_active_products — calc orchestrator pre-load
  ├── schemas.py (+5 Pydantic types, extra='forbid')
  └── handlers.py (+2 routes POST /api/v1/inventory/closing-guard/{evaluate,close-attempt})
```

### 신규 pure kernel

```
packages/services/m4_inventory/
  ├── closing_guard.py
  │     ├── compute_closing_balance_per_product — SIGN-NEUTRAL aggregate
  │     ├── classify_closing_invariant — 3 codes (CLOSING_OK / NEGATIVE_CLOSING / EMPTY_PERIOD)
  │     ├── is_close_blocked — single source of truth
  │     ├── format_negative_closing_banner_ko — Korean message SSOT
  │     └── ClosingInvariant NamedTuple
  └── production_consumption.py
        ├── compute_production_consumption_events — BOM-aware emit
        ├── EVENT_TYPE_PRODUCTION_OUTPUT_INBOUND (+ consumption + adjustment_positive)
        └── BomChild / BomMatrixLike / ProductionRowLike

packages/cost_engine/
  └── closing_invariant_check.py
        ├── verify_closing_invariant — V3 kernel (pure per AD-5)
        ├── V3Verdict TypedDict envelope
        └── Status enum: passed / failed / skipped
```

### Rule kernel 통합 (AD-12 slot 3 of 5)

```
V1CompleteAllocationRule (slot 1)
V4CostIncomeReconciliationRule (slot 2)
V3ClosingInvariantRule (slot 3) ← NEW
V7AbcIntegrityRule (slot 4)
V8RegressionRule (slot 5)
```

V3 는 calc orchestrator 가 ClosingInvariantVerifier.verify_v3_closing_invariant
를 pre-load 후 RuleInput.closing_invariant_verdict 로 주입 — rule kernel
은 pure 유지 (AD-5).

### Capability gate

`Capability.INVENTORY_CLOSING_GUARD` — manufacturing-kind 3종 ✅,
service ❌. Service-only tenant 가 POST 시도 → 403 INDUSTRY_NOT_SUPPORTED.

### AD-15 envelope mapping

| Exception | Status | envelope.error.code |
|---|---|---|
| ClosingGuardNegativeInventoryError | 409 | NEGATIVE_CLOSING_INVENTORY |
| ClosingGuardInvalidPeriodKeyError | 422 | CLOSING_GUARD_INVALID_PERIOD_KEY |
| ClosingGuardServiceOnlyTenantError | 403 | CLOSING_GUARD_SERVICE_ONLY_TENANT |
| ClosingGuardProductionConsumptionError | 500 | PRODUCTION_CONSUMPTION_INVALID |
| ClosingGuardAuditEmitError | 500 | CLOSING_GUARD_AUDIT_EMIT_FAILED |

### Audit action wire (A5 forward-lock + A7 wire)

`ActionClass.CLOSING_GUARD` 등록 — registry → audit_log INSERT:
- `closing_guard.evaluated` (read-only invariant computation)
- `closing_guard.close_attempted` (block-on-negative)
- `closing_guard.production_emitted` (BOM-aware ledger write)

### Alembic migration

- `0016_verification_log_v3_audit.py` — verification_log CHECK constraint
  확장 (4 → 5 value, `verify_v3_closing_invariant` 추가)
- `3-way drift detector` — UNION of ActionClass.VERIFICATION_LOG (4) +
  ActionClass.VERIFICATION (1) = DB CHECK (5)

### Drift detectors (T10)

- `tests/cost_engine/test_closing_invariant_check.py` (14 cases) V3 kernel
- `tests/services/test_closing_guard.py` (18 cases) closing_guard pure kernel
- `tests/services/test_production_consumption.py` (12 cases) BOM reconciliation
- `tests/cost_engine/test_v3_closing_invariant_rule.py` V3 rule kernel
- `tests/integration/test_closing_guard_label_consistency.py`
  (5 cases, AD-15 §11) Korean message parity Python ↔ TS
- `tests/integration/test_production_consumption_label_consistency.py`
  AD-15 §11 event_type parity
- `tests/services/test_closing_guard_service.py` (6+ cases) service-layer async
- `tests/services/test_closing_invariant_verifier.py` verifier bridge
- `tests/e2e/test_closing_guard_e2e.py` full flow smoke

## §6.2 Monthly Closing Report Architecture (Story 6.2)

### 신규 모듈

- **Pure kernel #1** `packages/services/m4_inventory/monthly_closing_report.py`
  - 3-source read-only join (closing snapshot + ledger events + fiscal period
    snapshot) — `classify_report_view_mode` (READY/PARTIAL/EMPTY 3-state)
    + `compute_usd_from_krw` (banker's rounding ROUND_HALF_EVEN) +
    `format_period_closing_krw_usd` (PRD §F5.2 dual display)
- **Pure kernel #2** `packages/cost_engine/monthly_closing_report_aggregator.py`
  - V4 closing-period consistency 4-source verification
    (`verify_monthly_closing_report_consistency`) — AD-12 V4 slot 2 of 5

### 신규 service layer

- `apps/api/modules/m4_inventory/services/monthly_closing_report_service.py`
  - `MonthlyClosingReportService` (3 routes — get_report / get_audit_trail /
    verify_v4) + typed exceptions
    (`MonthlyClosingReportEmptyError` /
    `MonthlyClosingReportKrwUsdRateMissingError` /
    `MonthlyClosingReportAuditEmitError`)

### 신규 routes (3 NEW)

- `GET /monthly-closing-report` — 월 마감 보고서 (3-source read-only join, D1 결정 2026-08-08)
- `GET /monthly-closing-report/audit-trail` — audit log
  (action_class='monthly_closing_report' filter)
- `GET /monthly-closing-report/v4-verdict` — V4 closing-period consistency
  verdict (3-source verification, D1 결정)

### Capability gate

- `Capability.MONTHLY_CLOSING_REPORT` (manufacturing 3종 ✅ / service-only ❌)
- A10 wire (manufacturing-kind 3종 200 OK + service-only 403
  INDUSTRY_NOT_SUPPORTED)
- 6-1 R4 triage 후 capability matrix v1.8 + 6-2 v1.9 changelog 등록

### AD-15 envelope mapping (apps/api/main.py)

- `MonthlyClosingReportResponse` Pydantic envelope (period_key, view_mode,
  closing_snapshot_count, ledger_event_count, fiscal_period_snapshot_count,
  v4_verdict, opening_inventory[], closing_per_product[], aggregate)
- `V4Verdict` TypedDict (status / code / failures / source_count / skip_reason_ko)

### Hook chain 통합

- 6-1 closing_period_service.confirm_closing_period dispatch → 6-2
  monthly_closing_report_service.get_monthly_closing_report GET → 4 KPI
  카드 (closing_snapshot_count + ledger_event_count +
  fiscal_period_snapshot_count + v4_verdict)
- V4 verdict dispatcher: 6-2 service.verify_v4 → 6-1 V4 slot fill in
  VerificationRunner (V1 → V4 → V3 → V7 → V8 ordering, AD-12 invariant)

### Drift detectors (T9)

- `tests/services/m4_inventory/test_monthly_closing_report.py` (18 cases)
  pure kernel #1
- `tests/cost_engine/test_monthly_closing_report_aggregator.py` (12 cases)
  pure kernel #2 V4 (4-source extension invariant + source_count=4)
- `tests/api/m4_inventory/test_monthly_closing_report_service.py` (12 cases)
  service layer (CR 1.1 audit-first + typed exceptions)
- `tests/api/m4_inventory/test_monthly_closing_report_krw_usd.py` (6 cases)
  KRW/USD dual display (PRD §F5.2 banker's rounding precision)
- `tests/integration/test_monthly_closing_report_label_consistency.py`
  (9 cases, AD-15 §11) Korean SSOT parity Python ↔ TS + view mode codes
- `tests/integration/test_monthly_closing_report_v4_verdict.py` (4 cases)
  V4 wire envelope shape + AD-12 ordering slot 2

### V8 18-fixture matrix extension (A11 PRIMARY)

- 16 → 18 골든 fixture count extension:
  - `closing-period-b-small.json` (V4 PASS, 4-source 일치)
  - `closing-period-b-standard.json` (V4 FAIL, 1개 product 4-source 불일치)
  - `fiscal-period-snapshot-b-small.json` (fiscal_period_snapshot PASS)
  - `fiscal-period-snapshot-b-standard.json` (fiscal_period_snapshot FAIL)
- Drift detector:
  `tests/regression_v8/test_regression_v8_fixtures.py::test_v8_fixture_count_is_18`
- Service submodule allowlist:
  `tests/architecture/test_api_calls_only_ports.py::ALLOWED_SERVICE_SUBMODULES`
  includes `"packages.services.m4_inventory.monthly_closing_report"`

총 ~70+ cases 추가 (3-way drift + parity + service + e2e).
