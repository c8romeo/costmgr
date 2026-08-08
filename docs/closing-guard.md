# Closing Guard — Closing ≥ 0 Invariant + V3 Sync (Story 5.3)

> Epic 5 — PRD §F4.2 음수 기말 차단 + PRD §V3 연결성 검증

## 1. 개요 (Overview)

PRD §F4.2: "월 마감 진입 시 모든 제품의 기말재고가 0 이상이어야
[마감] 버튼이 활성화되고, 기말재고가 음수인 제품이 하나라도 있으면
즉시 빨간 배너 + sonner toast 경고가 뜨며 [마감]이 disabled로 유지된다."

PRD §V3: 연결성 verification = closing ≥ 0 invariant.

**Story 5.3** wire contract:

1. **Closing ≥ 0 invariant guard** — 5-2 `inventory_ledger` aggregate
   SUM(qty) per product → `classify_closing_invariant` →
   `CLOSING_OK` / `NEGATIVE_CLOSING` / `EMPTY_PERIOD`.
2. **PRD §F4.2 frontend block** — `ClosingGuardBanner` (shadcn Alert
   destructive + red `bg-red-50`/`border-red-300` per UX v1.0) +
   `shouldDisableCloseButton` mirror + sonner toast.warning.
3. **PRD §V3 verification sync** — `closing_invariant_check` pure kernel
   (`verify_closing_invariant`) feeds VerificationRunner V3 slot
   (V1 → V4 → **V3** → V7 → V8 ordering, AD-12 invariant).
4. **5-1/5-2 carry-over close** — L8 SQL CHECK constraint on
   `monthly_input_rows` (chk_opening_inventory_manual_reject) + W1
   BOM-aware production reconciliation + W3 vitest activation + W4
   isolated unit tests.

## 2. Wire Contract

### Backend (service-layer + pure kernel)

```
Pure kernel (stdlib-only):
  packages/services/m4_inventory/closing_guard.py (T1)
    - compute_closing_balance_per_product(events) -> dict[UUID, Decimal]
    - classify_closing_invariant(closing) -> ClosingInvariant
    - is_close_blocked(invariant) -> bool
    - format_negative_closing_banner_ko(invariant, *, product_name_lookup) -> str
    - NEGATIVE_CLOSING_INVENTORY_KO = "기말재고 음수: 마감 불가"
    - 1 typed exception: ClosingGuardError

  packages/cost_engine/closing_invariant_check.py (T2)
    - verify_closing_invariant(*, ledger_aggregate, product_whitelist) -> V3Verdict
    - V3 verdict status: "passed" / "failed" / "skipped"
    - V3 failures: list[V3Failure] (product_id, closing_qty, message_ko)
    - industry='service' → status='skipped' (4-3 service-only ❌ skip)
    - 1 typed exception: ClosingInvariantViolationError

  packages/services/m4_inventory/production_consumption.py (T3, W1 5-2 carry)
    - compute_production_consumption_events(production_row, bom) -> list[ComputedLedgerEvent]
    - bom.children non-empty → production_output_inbound + production_material_consumption
    - bom None / empty → production_output_inbound + adjustment_positive (incomplete BOM)
    - banker's rounding via QTY_QUANTUM

Service layer (SQLAlchemy AsyncSession + audit-first):
  apps/api/modules/m4_inventory/services/closing_guard_service.py (T4)
    - ClosingGuardService (4 operations):
      · evaluate_closing_guard(period_key) -> ClosingInvariant (read-only)
      · request_close_attempt(period_key, actor_id) -> {allowed, closing_per_product, ...}
      · emit_production_ledger_events(production_row, bom) -> list[event_id]
      · validate_closing_invariant_against_active_products(period_key) -> V3Verdict
    - 5 typed exceptions:
      · ClosingGuardNegativeInventoryError (409 NEGATIVE_CLOSING_INVENTORY)
      · ClosingGuardInvalidPeriodKeyError (422)
      · ClosingGuardServiceOnlyTenantError (403 INDUSTRY_NOT_SUPPORTED)
      · ClosingGuardProductionConsumptionError (500)
      · ClosingGuardAuditEmitError (500)
    - A5 forward-lock: emit_audit_typed (raw emit_audit( forbidden)

  apps/api/modules/m3_calculate/services/closing_invariant_verifier.py (T5)
    - ClosingInvariantVerifier.verify_v3_closing_invariant(...)
    - V3 slot fill in VerificationRunner V1 → V4 → V3 → V7 → V8
```

### Pydantic schemas

```
apps/api/modules/m4_inventory/schemas.py (T5.3)
  - ClosingGuardResponse (Pydantic + extra='forbid'):
    { invariant: ClosingInvariant, closing_guard_blocked: bool, ... }
  - ClosingAttemptRequest (period_key)
  - ClosingAuditTrailResponse (list[AuditLogEntry])
```

### HTTP layer

```
apps/api/modules/m4_inventory/handlers.py (T6)
  - GET  /api/v1/inventory/closing-guard?period_key=...     (read-only)
  - POST /api/v1/inventory/closing-guard/attempt-close      (close-time gate)
  - GET  /api/v1/inventory/closing-guard/audit-trail        (audit query)
  Capability gate: Capability.INVENTORY_CLOSING_GUARD + MONTHLY_INPUT_PRODUCTION
  Service-only tenant → 403 INDUSTRY_NOT_SUPPORTED
```

### Audit actions (A5 forward-lock, ActionClass.CLOSING_GUARD + VERIFICATION)

| Action literal | ActionClass | Meaning |
|---|---|---|
| `closing_guard_violated` | CLOSING_GUARD | invariant violation (NEGATIVE_CLOSING) |
| `closing_guard_passed` | CLOSING_GUARD | invariant pass (CLOSING_OK / EMPTY_PERIOD) |
| `v3_closing_invariant_verified` | CLOSING_GUARD | V3 verdict audit |
| `verify_v3_closing_invariant` | VERIFICATION | V3 rule audit (Story 4-3 V3 slot fill) |

`ActionClass.CLOSING_GUARD` is a NEW class (3 values). `ActionClass.VERIFICATION`
is a NEW class (1 value, V3-only — distinct from existing
`ActionClass.VERIFICATION_LOG` which has 5 values including V8 골든).

## 3. UI (shadcn Tabs + Alert + sonner)

```
apps/web/components/m2-input/ClosingGuardBanner.tsx (or m4-inventory/)
  - shadcn <Alert variant="destructive"> (UX v1.0 red palette locked)
  - Top 5 offenders list (severity ASC sort, slice(0, 5))
  - Hidden when invariant is CLOSING_OK / EMPTY_PERIOD

MonthlyInputTabs (extension of Story 0.5 AC #7 shadcn Tabs)
  - 3 tabs: [기초재고] [입력] [경고/마감]
  - "경고/마감" tab = closing guard + V3 sync UI
  - reactive (re-fetch on save_row success → closing invariant recompute)

ClosingGuardGate (wraps [마감] button + manual edit reject):
  - invariant.code='NEGATIVE_CLOSING' → <fieldset disabled>
  - pointer-events-none + aria-disabled (legacy fallback for older browsers)

sonner toast pattern (Story 0.5 AC #3 BOMEditorClient precedent):
  toast.warning("기말재고 음수가 발생했습니다: 원자재 X -5개", {
    duration: 5000, position: "top-right",
  });
  + toast.error("기초재고는 자동 이월 체인에 의해 잠겼습니다");
```

## 4. V3 Sync (closing ≥ 0 invariant ↔ verification rule)

### V3 골든 fixture (NEW 5-3)

```
packages/cost_engine/tests/regression_v8/fixtures/
  - v3_closing_pass_manufacturing.json   (closing ≥ 0 → V3 verdict passed)
  - v3_closing_fail_manufacturing.json   (closing < 0 → V3 verdict failed)

V8_FIXTURE_COUNT 12 → 14 (Story 4-4 baseline + 2 V3 신규)
tests/regression_v8/test_regression_v8_fixtures.py extension:
  - 14 lock_sha256 + 14 byte-identical + 14 100× determinism
  - 2 V3 FAIL shape cases + 2 V3 PASS shape cases + 2 industry skip matrix
```

### V3 verdict envelope wire (AD-12 ordering invariant)

```
VerificationRunner.run_all(monthly_input, baseline, calc_result, *, industry)
  1. V1 (완전배부) — Story 4-3 wire
  2. V4 (4요소 분해) — Story 4-3 wire
  3. V3 (closing ≥ 0 invariant) — 5-3 wire (ClosingInvariantVerifier)
     - industry='service' → status='skipped' (4-3 service-only ❌ skip)
     - V3 fail → top_failure.code='V3' + action='verify_v3_closing_invariant'
     - V3 pass → audit 'closing_guard_passed'
  4. V7 (ABC 무결성) — Story 4-3 wire (service-only ❌ skip)
  5. V8 (1원 단위 회귀) — Story 4-4 wire (14 fixture matrix)
```

### Industry skip matrix (4-3 wire pattern)

| Industry | V3 wire? |
|---|---|
| manufacturing | ✅ RUN |
| manufacturing_service | ✅ RUN |
| manufacturing_service_other | ✅ RUN |
| service | ❌ SKIP (inventory 의미 없음) |

## 5. Carry-over Close (5-1 / 5-2 → 5-3)

### 5-1 (opening carry chain) carry-over

- **M14 (TS mirror `apps/web/lib/l2-input-opening-carry.ts`)** — closed in 5-3.
- **L8 (SQL CHECK `chk_opening_inventory_manual_reject`)** — wire in Alembic 0016.
- **L10 (service-only ❌ capability test)** — closed by `tests/integration/test_closing_guard_capability.py` (4 cases).
- **5-1 4 hooks + 5-3 manual edit reject UI 통합** — AC #5 wire.

### 5-2 (inventory_ledger append-only) carry-over

- **W1 (production_material_consumption BOM-aware)** — closed by `production_consumption.py` + T4.3 wire.
- **W2 (TS mirror `apps/web/lib/l2-input-inventory-ledger.ts`)** — closed.
- **W3 (TS mirror parity tests 6 unskip)** — closed by `tests/integration/test_inventory_ledger_label_consistency.py` (9 cases: 6 unskip + 3 NEW 5-3).
- **W4 (`_emit_inventory_ledger_event_for_row` isolated unit tests)** — closed by `tests/services/m4_inventory/test_emit_inventory_ledger_event_for_row.py` (8 cases).

## 6. 3중 Defense (Service-layer + SQL CHECK + Frontend)

Manual edit reject (`stream='opening_inventory'` reject) is enforced by 3 axes:

| 축 | 위치 | 역할 |
|---|---|---|
| 1. Service-layer validation | `OpeningCarryService.manual_edit_reject` | 400 `MONTHLY_INPUT_OPENING_MANUAL_EDIT` envelope (5-1 wire) |
| 2. SQL CHECK constraint | `monthly_input_rows.chk_opening_inventory_manual_reject` (Alembic 0016) | DB-level guard against bulk import bypass |
| 3. Frontend form reject | `apps/web/components/m2-input/MonthlyInputRowForm.tsx` | `<Form>` + `<Input disabled>` + sonner `toast.error` + helper text |

Drift detector: `tests/integration/test_opening_inventory_sql_check.py` (4 cases).

Closing guard (음수 기말 차단) is similarly enforced by 3 axes:

| 축 | 위치 | 역할 |
|---|---|---|
| 1. Service-layer close-time hook | `ClosingGuardService.request_close_attempt` + 4-2 `is_blocked` | 409 `NEGATIVE_CLOSING_INVENTORY` envelope |
| 2. SQL CHECK constraint | (none — invariant computed dynamically) | N/A |
| 3. Frontend [마감] button | `shouldDisableCloseButton` + `<fieldset disabled>` | UX reactivity |

PRD §A11 2-layer 정책 보존: 입력 시 경고 (Story 3.3 inline + 5-3 ledger aggregate) + 마감 시 차단 (5-3 closing_guard_service + 4-2 close-time hook).

## 7. 운영 가이드 (Operator Guide)

### 7.1. 운영자가 가장 자주 만나는 케이스 — Top 5 offenders

`ClosingGuardBanner` + `format_negative_closing_banner_ko` 가
severity ASC sort 로 top 1 (가장 음수 큰 제품) 를 banner head에 표시.
Top 5 까지 list 형식으로 동시 노출.

예시 메시지:
```
기말재고 음수: 마감 불가: 원자재 MAT-0001 -5.0000개, 반제품 SEM-0002 -3.0000개 → 마감 불가
```

### 7.2. 운영자가 출고/입고 수정 후 [마감] 활성화

1. [판매] 탭에서 출고량 130 → 80 으로 수정
2. backend `save_row` hook → ledger event emit → closing invariant 재계산
3. frontend reactive: `invariant.code` transitions
   `NEGATIVE_CLOSING` → `CLOSING_OK`
4. `<fieldset disabled>` 해제 + [마감] 버튼 enabled
5. sonner toast.warning 자동 dismiss (transient)

### 7.3. service-only tenant

`Capability.INVENTORY_CLOSING_GUARD` ❌ → 403 INDUSTRY_NOT_SUPPORTED.
[경고/마감] 탭 자체가 hidden (capability-gated UI).

### 7.4. Epic 6/11 진입 시점

- **Epic 6 (reports)** — closing invariant column을 21 보고서 wire에 추가.
- **Story 6.2 (월 마감 보고서)** — closing invariant 가 MonthlyClosingReportPanel
  의 4 KPI 카드 중 v4_verdict KPI 로 wire. **closing ≥ 0 invariant (V3) +
  closing-period consistency (V4 4-source) + ledger aggregate consistency
  동시 검증**. V3 fail 시 PARTIAL view mode dispatch (amber Alert +
  toast.info), V4 fail 시 PARTIAL view mode + KPI 빨강 + failures list.
  MonthlyClosingReportPanel 이 ClosingGuardBanner 아래 additive.
- **Epic 11 (reversal)** — `closing_guard_violated` reversal sequence wire.
  sign-negating reversal row + corrected row emit.

---

**Cross-references**:

- [`docs/inventory-ledger.md`](./inventory-ledger.md) §Story 5.2 base ledger wire contract.
- [`docs/opening-inventory-carry.md`](./opening-inventory-carry.md) §Story 5.1 carry chain.
- [`docs/cost-engine.md`](./cost-engine.md) §V3 closing invariant + §V4 closing-period consistency.
- [`docs/capability-matrix.md`](./capability-matrix.md) v1.9 (CLOSING_GUARD + MONTHLY_CLOSING_REPORT capability wire).
- [`docs/conventions.md`](./conventions.md) §10.7 closing guard invariant policy + §10.8 monthly closing report audit policy.
- [`docs/frontend-toolchain.md`](./frontend-toolchain.md) §Story 5.3 sonner + Alert + Form pattern.
- [`docs/monthly-closing-report.md`](./monthly-closing-report.md) §Story 6.2 monthly closing report wire contract.

## Story 11.2 EXTENSION — 4-stage close sequence guard + AD-6 close lock + AD-22 reversal/correction exception

Epic 11 cj-style 3-story 분할 2번째 (Epic 5 retro §6 W1) — 11-2 wire는 본
closing-guard (5-3 wire, closing ≥ 0 invariant) 위에 **4-stage close sequence
guard** 추가:

### Guard layering (Story 11.2)

1. **Layer 1 — closing ≥ 0 invariant** (5-3 wire) — V3 verdict PASS 시에만
   close sequence 진입 가능.
2. **Layer 2 — 4-stage close_sequence_state** (11-2 NEW) — divisions →
   manufacturing → abc → common → confirmed 1-way state machine.
3. **Layer 3 — partial close guard** (11-2 NEW) — 4단계 모두 완료 후에만
   confirm 가능. 미완료 시 `PartialCloseBlockedError` (409
   `PARTIAL_CLOSE_BLOCKED`).
4. **Layer 4 — AD-6 close lock** (11-2 NEW) — `fiscal_periods.status='closed'`
   후 모든 business-data INSERT 거부 (AD-22 reversal/correction events만 허용).
5. **Layer 5 — 11-1 reversal authorization 양쪽 가드** (11-2 EXTENSION) —
   `period_status` (monthly_input_periods.status) + `fiscal_period_status`
   (fiscal_periods.status) 양쪽 dispatch.

### AD-22 reversal/correction exception

`fiscal_periods.status='closed'` 후에도 `inventory_ledger.event_type IN
('reversal_negating', 'reversal_corrected')` 는 INSERT 허용 (AD-22 reversal
wire contract). `check_ad6_insert_allowed` pure kernel이 matrix 검증:

```python
allowed = (
    target_table == 'inventory_ledger'
    and target_event_type in ('reversal_negating', 'reversal_corrected')
)
```

### Capability matrix v1.11

- `Capability.CLOSE_SEQUENCE_LOCK` 신규 (manufacturing 3종 ✅ / service-only ❌)
- service-only tenant 진입 시 panel 자체 disabled + early-return 403
  `INDUSTRY_NOT_SUPPORTED` (CR 1.1 lesson — silent skip 금지)

### Audit trail

| Trigger | audit action | ActionClass |
|---|---|---|
| 4단계 미완료 → confirm 거부 | `closing_sequence_blocked` | `MONTHLY_CLOSING` |
| 4단계 모두 완료 → confirm 성공 | `closing_sequence_confirmed` | `MONTHLY_CLOSING` |
| step advance | `closing_sequence_step_completed` | `MONTHLY_CLOSING` |
| initiate | `closing_sequence_initiated` | `MONTHLY_CLOSING` |

### Carry-over

- **Frontend panel** (Task 10) — bmad-code-review carry-over sweep.
- **TS mirror + parity test** (Task 2.3 / 2.4 / 4.3) — bmad-code-review
  carry-over sweep.

상세: [docs/close-sequence-lock.md](./close-sequence-lock.md) SSOT.