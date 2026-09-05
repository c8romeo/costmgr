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

## 8. Story 11.2 EXTENSION — `ActionClass.MONTHLY_CLOSING` 4 NEW values

Epic 11 cj-style 3-story 분할 2번째 (Epic 5 retro §6 W1) — 11-2 wire는 별도
`ActionClass.MONTHLY_CLOSING` frozenset에 4 NEW values fill:

| Action | Value | Use case |
|---|---|---|
| `MONTHLY_CLOSING_INITIATED` | `"closing_sequence_initiated"` | `initiate_close_sequence` succeeded — `fiscal_periods` INSERT + `close_sequence_state='divisions'` |
| `MONTHLY_CLOSING_STEP_COMPLETED` | `"closing_sequence_step_completed"` | `step_complete` 호출 시 단계별 완료 (divisions / manufacturing / abc / common) |
| `MONTHLY_CLOSING_BLOCKED` | `"closing_sequence_blocked"` | partial close guard 거부 — 4단계 미완료 → 409 `PARTIAL_CLOSE_BLOCKED` |
| `MONTHLY_CLOSING_CONFIRMED` | `"closing_sequence_confirmed"` | `confirm_close_sequence` succeeded — 4단계 모두 완료 + `fiscal_periods.status='closed'` |

Wire contract: `apps/api/core/audit_action.py` `ActionClass.MONTHLY_CLOSING`
frozenset extension + 11-1 `ActionClass.REVERSAL_LOG` 5 values + 11-1
`ActionClass.MONTHLY_INPUT_PERIOD` `opening_inventory_unlocked` 1 value 보존.

`ActionClass.CLOSING_PERIOD` (6-1 wire, 3 values: `closing_period_confirmed` /
`closing_period_blocked` / `closing_period_snapshot_inconsistency`) 별도
frozenset — 11-2 본문 SSOT. 11-2 wire = monthly_input_periods.status 차원
확장이며, fiscal_periods.status 차원의 close sequence event는
`ActionClass.MONTHLY_CLOSING` 별도.

Drift: 3-way detector (`tests/integration/test_audit_action_consistency.py`)
4 NEW cases (initiated / step_completed / blocked / confirmed) — registry ↔ DB
CHECK (Alembic 0020 fiscal_periods 5 CHECK + audit_logs CHECK via 5-1 wire) ↔
call sites 4 NEW (close_sequence_service.emit_audit_typed()). **Task 7.3 / 7.4
EXTENSION** 은 bmad-code-review carry-over sweep 대상.

## 9. Epic 30+ EXTENSION — `ActionClass.REPORTS` 4 NEW values

Epic 30+ (cj-style 285+ EXTENSION wire sprint — cj-282 PRD entry `0c7524e`
Epic 30+ 결정 wire follow-up — cj-282a close-out retro `7403920` 결정 wire
보류분 5종 중 4 audit actions EXTENSION 결정 wire apply) — 별도
`ActionClass.REPORTS` frozenset에 4 NEW values fill:

| Action | Value | Use case |
|---|---|---|
| `REPORTS_EXPORT_CSV` | `"export_csv"` | `GET /api/v1/exports/csv` succeeded — StreamingResponse + UTF-8 BOM for Excel ko-KR + audit-first INSERT |
| `REPORTS_EXPORT_PDF` | `"export_pdf"` | `GET /api/v1/exports/pdf` succeeded — weasyprint HTML→PDF + Jinja2 ko-KR + matplotlib 3 charts + audit-first INSERT |
| `REPORTS_EXPORT_EMAIL` | `"export_email"` | `POST /api/v1/exports/email` succeeded — SMTP retry 3회 + PII redaction + audit-first INSERT |
| `REPORTS_EXPORT_SCHEDULED` | `"export_scheduled"` | APScheduler dispatch succeeded — `tenants.finance_contact_email` lookup + 99.9% uptime + audit-first INSERT |

Wire contract: `apps/api/core/audit_action.py` `ActionClass.REPORTS`
frozenset EXTENSION + `ReportsAction` Literal 4 NEW values +
`_ActionRegistry._REGISTRY[ActionClass.REPORTS]` entry +
`ReportsAction` added to `AuditAction` union type + `__all__` export
addition 결정.

Why 별도 `ActionClass.REPORTS` (NOT re-use `ActionClass.AUDIT`):

- Epic 17 `ActionClass.AUDIT` = audit log viewer CSV export (운영자 감사
  로그 viewer) territory — `audit_logs` 테이블 export 의미.
- Epic 30+ `ActionClass.REPORTS` = financial / cost / closing report export
  (사업 운영 보고서) territory — `fiscal_period_snapshots` / `cost_*` /
  `monthly_closing_reports` 등 business table 기반 export 의미.
- 2가지 export 는 (a) source table, (b) RBAC, (c) PII 민감도, (d) wire
  endpoint (Epic 17 = `GET /api/v1/audit/logs` + Epic 30+ = `GET/POST
  /api/v1/exports/*`) 가 본질적으로 다름.
- Precedent: 각 Epic 는 own ActionClass 보유 (ActionClass.MONTHLY_CLOSING_REPORT,
  ActionClass.CLOSING_PERIOD, ActionClass.MONTHLY_CLOSING, ActionClass.SNAPSHOT_PERSISTENCE,
  ActionClass.REOPEN_OPERATOR etc). 30+ reports territory 도 own ActionClass.
- Mixing "audit log viewer export" + "financial report export" 는 CR 1.1
  verbatim "free-form string drift is forbidden" lesson 보존 측면 위험.

AD bind 결정 wire (cj-282 Epic 30+ PRD entry `0c7524e` 3/25 AD-2 + AD-10 +
AD-12 + AD-22 verbatim):
- **AD-2 audit-first INSERT append-only** — 4 NEW audit actions 모두 audit
  INSERT 패턴 (CR 1-1 verbatim + ActionClass.MONTHLY_CLOSING_REPORT 6-1
  wire `eb5a8f9` verbatim precedent).
- **AD-10 identity/2FA via owner-only RBAC** — high-value export operation
  (CSV/PDF bulk download + Email delivery + Scheduled dispatch) 은 모두
  Epic 12 2FA 챌린지 mandatory 결정 wire.
- **AD-12 verify-first capability** — capability gate
  `Capability.EXPORT_CSV` / `EXPORT_PDF` / `EXPORT_EMAIL` / `EXPORT_SCHEDULED`
  prevent bypass at FastAPI route boundary (cj-style 285+ companion
  capability matrix v1.54 EXTENSION 결정 wire 결정).

NFR bind 결정 wire (cj-282 Epic 30+ PRD entry 7/20 active NFRs):
- **NFR5 streaming P95 ≤ 5s** — CSV export StreamingResponse 적용.
- **NFR18 ko-KR vocabulary SSOT** — 4 NEW audit actions 모두
  `ko-KR.json` keys consistent across UI.

Drift: 3-way detector (`tests/integration/test_audit_action_consistency.py`)
4 NEW cases (export_csv / export_pdf / export_email / export_scheduled) —
registry ↔ DB CHECK (audit_logs CHECK) ↔ call sites 4 NEW (csv_routes /
pdf_routes / email_routes / scheduler_dispatch service-layer writers).

**3 결정 wire 보류** (cj-286 territory): dev_seed report_fixtures +
ci.yml csv-export.spec.ts + AD-56 Epic 30+ 결정 wire.
