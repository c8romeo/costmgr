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

## Story 12.3 AD bindings (Account Deletion + Retention Consent)

- **AD-2** (audit-first + INSERT-only invariant) — Story 12.3 wire:
  `deletion_consents` table has `deletion_consents_insert_only` trigger
  that BLOCKS UPDATE and DELETE (RLS 0015 policy + DB trigger).
  Pattern mirrors 12-2 `tenant_backups` INSERT-only. AD-2 invariant
  보존: audit_logs INSERT-only + deletion_consents INSERT-only = 5-year
  audit 보존 (NFR4 2절) + forensic integrity.
- **AD-9** (Seoul region) — Story 12.3 wire: `deletion_consents` table
  stored in Supabase Postgres Seoul (`ap-northeast-2`) region, mirroring
  12-2 `tenant_backups` table location. Cross-region replication BLOCKED
  (D-12-3-DEFER-5 honestly documented in `docs/deferred-work.md`).
- **AD-10** (4-role + NFR7 destructive endpoint) — `POST
  /api/v1/account/deletion/request` is `require_role("owner")` ONLY +
  2FA challenge token (CR 12-5 L3 3-layer defense — route layer
  `require_role` + service layer `verify_totp_challenge` + handler layer
  audit-first BEFORE raise).

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

## §6.3 Closing PDF Export Architecture (Story 6.3)

Epic 6 cj-style 3-story 분할 3번째 (마지막). 6-1 + 6-2 wire 위에 PDF
export + ko-KR labels SSOT + A8 timeline guard 추가.

### 신규 모듈

- **Pure kernel** `packages/services/m4_inventory/closing_pdf_export.py`
  - `validate_closing_pdf_section_order` + `build_closing_pdf_metadata` +
    `render_closing_pdf_byte_stream` (stdlib-only PDF 1.4 generation)
  - NamedTuples: `ClosingPdfTextBlock`, `ClosingPdfSection`, `ClosingPdfPage`,
    `ClosingPdfDocument`
  - Constants: A4_WIDTH_PT=595, A4_HEIGHT_PT=842, MAX_PDF_SIZE_BYTES=5*1024*1024,
    CLOSING_PDF_EXPORT_TITLE_KO, CLOSING_PDF_EXPORT_EMPTY_KO,
    CLOSING_PDF_INDUSTRY_VALUES (4 canonical)
- **Service layer** `apps/api/modules/m4_inventory/services/closing_pdf_export_service.py`
  - `ClosingPdfExportService.export_closing_pdf`
  - 5-step pipeline: industry guard → 4-source read-only join →
    audit-first emit → PDF render → Response
  - 3 typed exceptions: `ClosingPdfExportInvalidIndustryError` (422),
    `ClosingPdfExportSizeExceededError` (409),
    `ClosingPdfExportAuditEmitError` (500)

### 신규 routes (1 NEW)

- `POST /monthly-closing-report/export-pdf` — PDF 다운로드
  (4-source read-only join + audit-first emit + size cap guard)

### Capability gate

- `Capability.MONTHLY_CLOSING_REPORT` (manufacturing 3종 ✅ / service-only ❌)
- 6-2 wire 완료 — 6-3 reuse (no new capability wire)

### AD-15 envelope mapping (apps/api/main.py)

- 422 `CLOSING_PDF_EXPORT_INVALID_INDUSTRY` → ko-KR `"업종 미지원: ..."`
- 409 `CLOSING_PDF_EXPORT_SIZE_EXCEEDED` → ko-KR `"PDF 크기 초과: 5MB cap"`
- 500 `CLOSING_PDF_EXPORT_AUDIT_EMIT_ERROR` → ko-KR `"PDF 저장 audit emit 실패: ..."`

### Hook chain 통합 (CR 1.1 audit-first)

- `audit-first emit` → `monthly_closing_report_viewed` action
- action_class = `ActionClass.MONTHLY_CLOSING_REPORT`
- Audit 실패 시 PDF render skip (5-step pipeline invariant)

### Drift detectors (T5+T6)

- Inline projection timeline guard:
  `tests/integration/test_inline_projection_deprecation_timeline.py`
  (7 scenarios — 5-2/5-3/6-1/6-2/6-3 wire invariants)
- A5+A7+A11+A12 preservation:
  `tests/integration/test_6_3_action_inventory_preservation.py`
  (6 scenarios — A5 forward-lock + A7 wire + A11 V8 + A12 T12.2)
- ko-KR cross-surface coherence:
  `tests/integration/test_closing_pdf_export_ko_kr_comprehensive.py`
  (8 scenarios — Python kernel + TS mirror + ko-KR.json +
  API envelope + Vitest mock + service exception mapping)
- V8 runner E2E:
  `packages/cost_engine/tests/regression_v8/test_v8_runner_e2e.py`
  (6 scenarios — fixture load + lock verify + publish flow)
- Service submodule allowlist:
  `tests/architecture/test_api_calls_only_ports.py::ALLOWED_SERVICE_SUBMODULES`
  includes `"packages.services.m4_inventory.closing_pdf_export"`

### ko-KR SSOT surface (4 surfaces)

1. Python kernel constants (CLOSING_PDF_EXPORT_TITLE_KO + EMPTY_KO)
2. TS mirror constants (CLOSING_PDF_EXPORT_TITLE_KO + EMPTY_KO)
3. ko-KR.json `closing_pdf_export` namespace (10 keys)
4. API envelope `message_ko` Korean (3 typed exceptions)

Total cases: 84 (T1-T6 close-out 합산).

## Story 11.2 EXTENSION — M11 모듈 권한 본문 + fiscal_periods + 4-stage close_sequence_state

Epic 11 cj-style 3-story 분할 2번째 (Epic 5 retro §6 W1) — 11-2 wire는 M11
모듈 authority (11-1 wire) 위에 fiscal_periods 테이블 + 4-stage
close_sequence_state 추가:

### 모듈 권한 (apps/api/modules/m11_close/)

- `apps/api/modules/m11_close/__init__.py` — 11-1 populated
- `apps/api/modules/m11_close/handlers.py` — 11-1 3 routes + **11-2 3 NEW routes EXTENSION**
  (POST /api/v1/close/sequence/initiate + POST /api/v1/close/sequence/step-complete +
  GET /api/v1/close/sequence/state)
- `apps/api/modules/m11_close/services/__init__.py` — 11-1 reversal_service +
  reversal_kernel_adapter + **11-2 close_sequence_service EXTENSION**
- `apps/api/modules/m11_close/services/reversal_service.py` — 11-1 wire
  EXTENSION (`execute_reversal` 양쪽 status dispatch)
- `apps/api/modules/m11_close/services/close_sequence_service.py` — **11-2
  NEW** (565 lines, 4 operations + 5 typed exceptions + REPEATABLE READ +
  audit-first + idempotent no-op skip)

### 데이터 (apps/api/alembic/versions/0020_fiscal_periods_close_sequence.py)

`fiscal_periods` 테이블 greenfield:

- `id` (UUID PK)
- `tenant_id` (FK → tenants)
- `period_key` (TEXT, AD-24 pattern `^\d{4}-(0[1-9]|1[0-2])$`)
- `status` (TEXT, CHECK ∈ `('open', 'closing', 'closed', 'reversed')`)
- `close_sequence_state` (TEXT, CHECK ∈
  `('divisions', 'manufacturing', 'abc', 'common', 'confirmed')`)
- `divisions_completed_at` / `manufacturing_completed_at` /
  `abc_completed_at` / `common_completed_at` (TIMESTAMPTZ, NULL)
- `closed_at` (TIMESTAMPTZ, NULL)
- `closed_by` (UUID, NULL)
- 5 CHECK + 1 UNIQUE (`(tenant_id, period_key)`) + 2 INDEX (period_key, status)

`down_revision='0019_m11_reversal_ledger'` — 11-1 wire tip 그대로.

### Pure kernels (packages/services/m11_close/)

| Kernel | File | Role |
| --- | --- | --- |
| `close_sequence_order.validate_close_sequence_order` | `close_sequence_order.py` | 4-stage 순서 + chronological invariant |
| `close_sequence_state.compute_close_sequence_state` | `close_sequence_state.py` | state machine |
| `close_sequence_state.check_ad6_insert_allowed` | `close_sequence_state.py` | AD-6 INSERT 거부 |
| `partial_close_guard.check_partial_close_attempt` | `partial_close_guard.py` | 부분 마감 거부 |
| `reversal_authorization.authorize_reversal` (양쪽 가드) | `reversal_authorization.py` | 11-1 wire EXTENSION |

### RLS (supabase/policies/0011_fiscal_periods_rls.sql)

ENABLE + FORCE RLS + 4-policy split (`tenant_select_own` +
`tenant_insert_own` + `tenant_update_own_blocked_status` +
`tenant_delete_blocked`) — 5-2/6-1 RLS 패턴 동일.

### Capability matrix v1.11

`Capability.CLOSE_SEQUENCE_LOCK` 신규 (manufacturing 3종 ✅ / service-only ❌).
상세: [docs/capability-matrix.md](./capability-matrix.md) + [docs/close-sequence-lock.md](./close-sequence-lock.md) SSOT.

---

# Architecture: M12 Account Module (Epic 12) — 2FA / M2 Entry Gate

> Story 12.1 (initial wire) + Story 12.4 (carry-over sprint) — 5번째 epic 연속 검증

## 모듈 구조

```
apps/api/modules/m12_account/
├── __init__.py          # router re-export (CR 11-2 lessons)
├── handlers.py          # 8 routes + 1 M2 entry gate route (Story 12.4 wire)
├── exceptions.py        # 8 typed exceptions (TwoFactorNotEnabledError 등)
├── services/
│   ├── __init__.py
│   ├── two_factor_service.py             # TwoFactorService (get_totp_status + disable_totp 등)
│   ├── two_factor_challenge_service.py   # PyJWT HS256 challenge tokens (5-min TTL)
│   └── audit_extension.py                # 19 *_KO + 11 ERROR_CODE_* constants (AD-15 §11 SSOT)
```

## 레이어 규칙 (AD-11)

```
Pure kernel (packages/services/m12_account/)
   ├── totp.py                  # RFC 6238 + lockout + recovery code PBKDF2
   └── two_factor_gate.py       # AD-10 role gate + M2 entry state machine
   ↓ import
Service layer (apps/api/modules/m12_account/services/two_factor_service.py)
   ↓ import
HTTP layer (apps/api/modules/m12_account/handlers.py)
   ↓ import
FastAPI app (apps/api/main.py — include_router(m12_account_router))
```

Pure kernel 은 stdlib-only (no DB, no clock injection, no random). Service
layer 는 SQLAlchemy AsyncSession + NFR6 AES-256-GCM encrypt-at-rest + AD-15
§11 audit-first emit (CR 1.1 lesson). HTTP layer 는 FastAPI + Pydantic
+ `require_role("owner")` dependency (AD-10 4-role gate).

## 데이터 흐름 (PRD §F12.1 + §M12-a)

```
[User navigates to /m2-input/period/[periodKey]]
   ↓
Server Component: <TwoFactorGuard role={session.role}
                              totp_enabled={...}
                              locked_out={...}
                              lockout_until={...}>
   ↓
TS mirror buildM2EntryGateState(input) → state.allowed
   ↓ (Story 12.4: minimal viable wire — stub props, TODO replace with session resolution)
If state.allowed === false:
  Render yellow-bordered panel (ko-KR.json: two_factor_guard + m2_entry_gate)
   ↓
[User clicks "인증 진행" — DEFERRED to Story 12.5: TwoFactorChallengeDialog]
   ↓
POST /api/v1/account/2fa/challenge → HS256 challenge token (5-min TTL)
   ↓
POST /api/v1/account/2fa/challenge-tokens/consume → verify TOTP code
   ↓
on success: M2 entry permitted
on lockout (429): display Retry-After timer
```

## Pure kernels (packages/services/m12_account/)

| Kernel | File | Role |
| --- | --- | --- |
| `totp.verify_totp_code` | `totp.py` | RFC 6238 HMAC-SHA1 base32 + ±1 window |
| `totp.verify_recovery_code` | `totp.py` | PBKDF2-HMAC-SHA256 200k iters + Crockford base32 |
| `totp.compute_lockout_state` | `totp.py` | 5-fail → 15-min LOCKOUT_DURATION_SECONDS=900 |
| `two_factor_gate.enforce_role_gate` | `two_factor_gate.py` | AD-10 owner/member allowlist |
| `two_factor_gate.enforce_two_factor_gate` | `two_factor_gate.py` | 2FA enrollment + lockout gate |
| `two_factor_gate.lockout_status` | `two_factor_gate.py` | bool derivation from totp_lockout_until |

## RLS (supabase/policies/0013_users_totp_columns_rls.sql)

ENABLE + FORCE RLS + 5-policy split on `users.totp_*` columns:

| Policy | Operation | Rule |
| --- | --- | --- |
| `users_totp_select_same_tenant` | SELECT | `tenant_id = current_setting('app.tenant_id', true)::uuid` |
| `users_totp_select_consultant_proxy` | SELECT | EXISTS check on `memberships.role='consultant_proxy'` |
| `users_totp_insert_same_tenant` | INSERT | same-tenant check |
| `users_totp_update_self` | UPDATE | `id = current_setting('app.user_id', true)::uuid` |
| `users_totp_update_owner` | UPDATE | EXISTS check on `memberships.role='owner'` |

**Intentionally NO DELETE policy** — 2FA state retention required for audit.

## Capability matrix v1.13

**2FA is industry-agnostic** (CR 12-1 L4) — capability gate intentionally
absent. Authorization is AD-10 role gate only. `Capability.TWO_FACTOR_AUTH`
is documented in [docs/capability-matrix.md](./capability-matrix.md) for
completeness but is NOT enforced in any route.

상세: [docs/capability-matrix.md](./capability-matrix.md) + [docs/account-security-operations.md](./account-security-operations.md) + [docs/conventions.md#11-totp-2fa-epic-12-story-121-124](./conventions.md#11-totp-2fa-epic-12-story-121-124) SSOT.

## Cross-references

- `apps/api/alembic/versions/0022_users_totp_columns.py` — 5 columns + 2 partial indexes + CHECK
- `tests/api/test_alembic_0022_users_totp_columns.py` — 12 migration tests
- `tests/api/m12_account/test_handlers_route_shape.py` — 12 route shape tests
- `tests/api/m12_account/test_exception_handlers_registered.py` — 14 exception handler tests
- `tests/integration/test_audit_logs_no_action_check_constraint.py` — invariant regression
- `apps/web/lib/m12-two-factor-{gate,setup,disable}.ts` — 3 TS mirrors + 23 vitest parity tests
- `apps/web/components/m12-account/TwoFactorGuard.tsx` — M2 entry guard UI
- `apps/web/messages/ko-KR.json` — 5 NEW sections (two_factor_guard, two_factor_setup_panel, two_factor_disable_panel, two_factor_status_badge, m2_entry_gate) — 41 NEW strings total

---

## §9.1 ABC 100% Validation Architecture (Story 9.1)

> PRD §F9.1 verbatim: "원가풀 행 합·활동 열 합·동인 합 모두 100% 가드".
> Epic 9 (ABC / TDABC Engine — Service Business) 1번째 진입점.

### 모듈 구조

```
apps/api/modules/m9_abc/
├── __init__.py
├── handlers.py             # 4 NEW endpoints (1.2 scaffold 2 routes + 9-1 4 routes)
├── schemas.py              # 5 NEW Pydantic v2 models
├── exceptions.py           # 4 NEW typed exceptions + 4 Korean SSOT constants
└── services/
    ├── __init__.py
    └── abc_validation_service.py   # AbcValidationService (orchestrator)

packages/cost_engine/abc_engine.py        # A19 cohesion pattern 6번째 surface
packages/services/m9_abc/abc_validation_serializers.py   # JSON-safe thin serializer
apps/web/components/m9-abc/                       # 4 NEW Client Components
apps/web/lib/m9-abc-validation.ts                # TS mirror
apps/web/lib/m9-abc-validation-schema.ts          # TS validation schema
```

### Pure kernel (A19 cohesion pattern 6번째 surface)

`packages/cost_engine/abc_engine.py`:
- 4 NEW pure functions: `validate_cost_pool`, `validate_activity`,
  `validate_driver`, `validate_100_percent_guard` (orchestrator),
  `compute_validation_hash` (V8 determinism sha256:64-hex)
- 3 NEW frozen dataclasses: `CostPoolValidation`, `ActivityValidation`,
  `DriverValidation` (+ `ValidationState` Union)
- 4 NEW typed exceptions: `CostPoolValidationError`,
  `ActivityValidationError`, `DriverValidationError`,
  `AbcValidationNotFoundError`
- 7 NEW constants: `ABC_VALIDATION_KRW_QUANTUM`, `ALLOCATION_PCT_MIN/MAX`,
  `VALIDATION_100_PCT_TARGET`, `VALIDATION_TOLERANCE_KRW`,
  `VALIDATION_HASH_PREFIX`, `VALIDATION_DEFAULT_INDUSTRY`
- AD-5 stdlib-only (no DB, no clock, no random) — verified via
  `tests/cost_engine/test_abc_engine_no_io_imports.py` (5 AST cases).

### Service layer

`AbcValidationService` (orchestrator):
- `validate_100_percent_guard(cost_pool, activities, drivers, ...)` →
  3-layer guard orchestrator (CR 12-5 L3 3-layer defense).
- `validate_cost_pool_only / validate_activity_only / validate_driver_only`
  single-layer endpoints.
- `_to_validation_state` ORM→kernel boundary conversion (CR 12-1 L3 precedent).
- `validate_abc_pct_list` pre-validation (type/range/empty).
- `fetch_tenant_abc_drivers` (Story 1.2 scaffold JSONB re-use).

### Capability gate

`Capability.ABC_CALCULATION` (NEW, v1.18):
- Industry-agnostic (manufacturing 3종 ✅ + service-only ✅).
- CR 12-1 L4 precedent: ABC is financial baseline infrastructure.
- 4 NEW endpoints gated: `Depends(require_capability(Capability.ABC_CALCULATION))`
  + `Depends(require_any_role("owner", "member"))`.
- Drift detector: `tests/integration/test_capability_matrix_v1_18_drift.py`.

### AD-15 envelope mapping (apps/api/main.py)

4 NEW typed exception envelopes (CR 12-5 D-14):
- `CostPoolValidationError` → 422 COST_POOL_INVALID_SUM
- `ActivityValidationError` → 422 ACTIVITY_INVALID_SUM
- `DriverValidationError` → 422 DRIVER_INVALID_SUM
- `AbcValidationNotFoundError` → 404 ABC_VALIDATION_NOT_FOUND

Korean SSOT constants:
- `ABC_COST_POOL_INVALID_SUM_KO = "원가풀 행 합이 100%가 아닙니다"`
- `ABC_ACTIVITY_INVALID_SUM_KO = "활동 열 합이 100%가 아닙니다"`
- `ABC_DRIVER_INVALID_SUM_KO = "동인 합이 100%가 아닙니다"`
- `ABC_VALIDATION_NOT_FOUND_KO = "ABC 검증 대상을 찾을 수 없습니다"`

### 9-1 honestly DEFER (A26 forward-lock)

9-1 = validation only, NO INSERT/UPDATE/DELETE on persistent storage.
- **D-9-1-DEFER-1** CCR compute (9-2 entry)
- **D-9-1-DEFER-2** ABC allocation engine (9-3 entry)
- **D-9-1-DEFER-3** M3 endpoint dispatch (9-3 entry, AD-19)
- **D-9-1-DEFER-4** Cost Object Breakdown (9-2 entry)
- **D-9-1-DEFER-5** Multi-industry ABC (§14.B Non-Goal #1)
- **D-9-1-DEFER-6** Playwright E2E

### Drift detectors (T9.7)

- `tests/cost_engine/test_abc_engine.py` — 36 pure kernel cases
- `tests/cost_engine/test_abc_engine_no_io_imports.py` — 5 AST stdlib whitelist cases
- `tests/cost_engine/test_abc_engine_determinism.py` — 6 V8 byte-identical cases
- `tests/services/test_m9_abc_validation_service.py` — 30 service-layer cases
- `tests/api/m9_abc/test_abc_validation_handlers.py` — 20 handler + schema cases
- `tests/integration/test_capability_matrix_v1_18_drift.py` — 12 capability pin cases
- `apps/web/__tests__/lib/m9-abc-validation-schema-parity.test.ts` — 33 TS parity cases
- `apps/web/__tests__/components/m9-abc.*.test.tsx` — 13 component cases

### Cross-references (9-1)

- `packages/cost_engine/abc_engine.py` — pure kernel (A19 cohesion pattern 6번째)
- `apps/api/modules/m9_abc/handlers.py` — 4 NEW routes + 1.2 scaffold preserved
- `apps/api/modules/m9_abc/services/abc_validation_service.py` — orchestrator
- `apps/api/modules/m9_abc/schemas.py` — 5 NEW Pydantic v2 models
- `apps/api/modules/m9_abc/exceptions.py` — 4 NEW typed exceptions + 4 Korean SSOT
- `apps/api/main.py` — 4 NEW @app.exception_handler decorators
- `apps/api/core/capability.py` — `Capability.ABC_CALCULATION` enum + 4-industry grants
- `packages/services/m9_abc/abc_validation_serializers.py` — JSON-safe thin serializer
- `apps/web/lib/m9-abc-validation.ts` — TS mirror (types + validators)
- `apps/web/lib/m9-abc-validation-schema.ts` — TS validation schema
- `apps/web/components/m9-abc/AbcValidationPanel.tsx` — main Client Component
- `apps/web/components/m9-abc/AbcValidationForm.tsx` — 3-input form
- `apps/web/components/m9-abc/AbcValidationStatus.tsx` — single-layer status
- `apps/web/components/m9-abc/AbcValidationGuardBadge.tsx` — 3-layer guard badge
- `apps/web/messages/ko-KR.json` — NEW `abc_validation` namespace (29 strings)
- `apps/web/app/[locale]/(dashboard)/budget/abc-validation/page.tsx` — RSC page

