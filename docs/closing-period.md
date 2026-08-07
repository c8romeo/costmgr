# Closing Period Service — Operator/Dev Guide (Story 6.1, Epic 6)

> Closing period service는 월 마감을 확정하는 시점에 ledger aggregate 를
> 영구 보존하기 위한 append-only wire 입니다. Story 6.1 에서
> `closing_period_service.confirm_closing_period` 진입점이 wire 되었으며,
> ClosingGuardBanner (5-3) 위에 additive 한 ClosingPeriodConfirmationPanel
> 으로 UI 진입점이 노출됩니다. 본 문서는 operator/dev 양쪽을 위한 운영
> 매뉴얼입니다.

## 1. 개요 (Operator)

### 1.1 무엇이 달라지는가

월 마감을 확정하면:

1. **closing_snapshot ledger event 가 emit** 됩니다 (per product 1 row).
   `inventory_ledger.event_type='closing_snapshot'` 의 11번째 wire.
   `append-only` 보존 (PostgreSQL `BEFORE UPDATE OR DELETE` trigger) →
   회계사·세무사에게 전달하는 immutable snapshot 역할.
2. **monthly_input_periods.status='closed'** 가 됩니다 (AD-6 fiscal-period
   close lock). 한 번 closed 가 되면 reopen 은 operator action +
   reason + audit row 만 허용 (AD-25 invalidation 정책).
3. **audit log** 에 `closing_period_confirmed` 가 INSERT 됩니다.
   `ActionClass.CLOSING_PERIOD` 신규 3 values 의 첫 wire.
   payload: `{period_key, closing_snapshot_count, finalized_at, actor_id,
   tenant_id, trace_id}` (CR 1.1 self-describing).

### 1.2 누가 사용할 수 있는가

| Industry | Capability | 결과 |
|---|---|---|
| `manufacturing` | ✅ | confirm 가능 |
| `manufacturing_service` | ✅ | confirm 가능 |
| `manufacturing_service_other` | ✅ | confirm 가능 |
| `service` | ❌ | 403 INDUSTRY_NOT_SUPPORTED — UI panel 자체가 비노출 |

Capability matrix: `docs/capability-matrix.md` v1.8 (Story 6.1 wire).

### 1.3 상태 코드 (4 values)

PRD §F4.3 + §V4 + §A11 wire contract:

| Status | 의미 | UI 동작 | Backend 동작 |
|---|---|---|---|
| `CLOSING_READY` | invariant OK + ledger events ≥ 1 | [마감 확정] 버튼 enabled | POST `/closing-period/confirm` 200 OK |
| `CLOSING_BLOCKED` | invariant NEGATIVE_CLOSING | [마감 확정] 버튼 disabled | 409 CLOSING_PERIOD_BLOCKED |
| `ALREADY_CLOSED` | `monthly_input_periods.status='closed'` | 버튼 비노출 (AD-6 close lock) | 409 ALREADY_CLOSED (idempotent no-op) |
| `EMPTY_PERIOD` | ledger events 0건 | 버튼 disabled | 409 EMPTY_PERIOD |

## 2. Wire Contract (Dev)

### 2.1 Backend 진입점

```
POST /api/v1/inventory/closing-period/confirm
Body: { "period_key": "2026-07" }
Auth: Bearer JWT (tenant_id, actor_id decode)
Capability: MONTHLY_CLOSING_REPORT (A10)
```

**Response 200 OK envelope:**
```json
{
  "confirmed": true,
  "closing_snapshot_count": 12,
  "period_key": "2026-07",
  "finalized_at": "2026-08-07T12:34:56.789Z",
  "trace_id": "019200a0-..."
}
```

**409 typed envelopes (AD-15 §4):**
- `CLOSING_PERIOD_BLOCKED` — invariant NEGATIVE_CLOSING
- `ALREADY_CLOSED` — idempotent re-confirm 시 멱등성 보장 (no INSERT, no UPDATE, no audit)
- `EMPTY_PERIOD` — 수불 event 0건

**403 typed envelope:**
- `INDUSTRY_NOT_SUPPORTED` — service-only tenant

### 2.2 Read-only 진입점

```
GET /api/v1/inventory/closing-period/status?period_key=...
→ ClosingPeriodResponse (status + closing_per_product + counts)

GET /api/v1/inventory/closing-period/audit-trail?period_key=...
→ ClosingPeriodAuditTrailResponse (last 10 closing_period_* audit entries)
```

### 2.3 V4 verification surface (Story 6.1 V4 slot fill)

`VerificationRunner.run_all(monthly_input, baseline, calc_result, *, industry)`
에서:

```
V1 → V4 (closing snapshot 일관성 — NEW) → V3 → V7 → V8
```

**V4 PASS 골든:** `ledger_aggregate == closing_snapshot_aggregate` per product
→ `verdict.status='passed'` + audit `closing_period_confirmed`.

**V4 FAIL 골든:** `ledger_aggregate != closing_snapshot_aggregate` (per-product
qty 불일치) → `verdict.status='failed'` + audit
`closing_period_snapshot_inconsistency` + `top_failure.code='V4'` +
Korean message `"마감 snapshot 불일치: 기말재고 ledger vs closing_snapshot 갱신 필요"`.

**industry='service' → V4 SKIP:** inventory 의미 없음 + A10
MONTHLY_CLOSING_REPORT capability gate 동등 발동.

## 3. UI 진입점

### 3.1 ClosingGuardBanner 위에 additive panel

`apps/web/components/m2-input/MonthlyInputTabs.tsx` 의 [마감] tab 안에
vertical stack 으로 노출:

1. `M2ClosingGuardBanner` (5-3 wire) — invariant NEGATIVE_CLOSING 시
   red banner + 음수 product list (top 5)
2. `ClosingPeriodConfirmationPanel` (6-1 T8.3) — status 4 codes 별
   conditional Alert + [마감 확정] trigger button
3. `MonthlyInputRowForm` (5-3 wire) — close-time form (fieldset gate)
4. audit-trail list (5-3 P6 wire)

### 3.2 [마감 확정] 클릭 시 Dialog

shadcn `<Dialog>` (`apps/web/components/m2-input/ClosingPeriodConfirmDialog.tsx`):

1. snapshot preview 표시 (closing_per_product top 5 + period_key + status + counts)
2. [확정] 클릭 → POST `/closing-period/confirm`
3. sonner `toast.success('월 마감 확정 완료: closing_snapshot {N}건 저장')` (200 OK 시)
4. sonner `toast.error('마감 차단: 음수 기말재고')` (409 CLOSING_PERIOD_BLOCKED 시)
5. sonner `toast.error('이미 마감됨')` (409 ALREADY_CLOSED 시)

### 3.3 Capability gate UI

`tenant_settings.industry === 'service'` → `MONTHLY_CLOSING_REPORT`
capability 미보유 → ClosingPeriodConfirmationPanel 비노출 + 403
INDUSTRY_NOT_SUPPORTED 시 sonner `toast.error('업종 미지원...')`.

## 4. V4 Sync

V4 (closing snapshot 일관성) verification � ledger aggregate ↔
closing_snapshot ledger events 양방향 동기화:

1. **Backend:** ledger aggregate (`LedgerService.query_period_closing`) +
   closing_snapshot aggregate (per period event_type='closing_snapshot'
   filter) + product whitelist (현재 tenant 활성 product UUID set) →
   `verify_closing_period_consistency` pure kernel dispatch.
2. **V4 골든 fixture:** `packages/cost_engine/tests/regression_v8/fixtures/`
   의 `v4_closing_period_pass_manufacturing.json` +
   `v4_closing_period_fail_manufacturing.json` 2 NEW 골든 (Story 4-4
   골든 매트릭스 14 → 16 extension).
3. **byte-identical CI gate:** `tests/regression_v8/test_regression_v8_fixtures.py`
   의 16 fixture matrix × 3 (lock_sha256 / byte-identical / 100x determinism)
   + 2 industry skip matrix = 50+ cases.
4. **Audit emit:** V4 pass → `closing_period_confirmed` (ActionClass.CLOSING_PERIOD).
   V4 fail → `closing_period_snapshot_inconsistency` (ActionClass.CLOSING_PERIOD).

## 5. Carry-over close (5-1 + 5-2 + 5-3 + 0.5)

### 5.1 Story 5.1 — Opening Inventory Auto-Carry Chain
- `closing_per_product` 계산 시 5-1 `opening_inventory` JSONB → ledger
  aggregate 의 starting point.
- `opening_inventory_locked` flag 보존 (carry chain applied 시 자동 lock).

### 5.2 Story 5.2 — Inventory Ledger Append-Only Events
- `closing_snapshot` event_type = 11번째 wire (5-2 의 10 values +
  6-1 의 11번째 = 11 values whitelist).
- `reverses_event_id` UNIQUE 보존 → Epic 11 reversal module wire
  contract 진입점 (closing snapshot correction).
- `idempotency partial UNIQUE` 보존 → closing_period snapshot 멱등성.

### 5.3 Story 5.3 — Negative Closing Inventory Guard
- `compute_closing_balance_per_product` (5-3 pure kernel) →
  `closing_per_product` 입력으로 `compute_closing_snapshot` (6-1
  pure kernel #1) dispatch.
- `closing_guard_service.request_close_attempt` → `closing_period_service.confirm_closing_period`
  위 additive.
- 5-3 의 6 frontend files + 3 vitest scenarios 그대로 보존 +
  6-1 의 4 frontend files + 9 scenarios additive.

### 5.4 Story 0.5 — Frontend Plumbing
- shadcn Alert + Dialog + sonner toast 활용 (Story 0.5 AC #4 #5).
- vitest + RTL + jsdom + MSW wire (Story 0.5 AC #4) → 6-1 frontend
  vitest 9 scenarios unskip.

## 6. 3-layer Defense (PRD §A11)

PRD §A11 정책의 3-layer 가 6-1 wire 로 정확히 closed:

```
Layer 1 (입력 시 경고) — Story 3.3 inline projection + 5-2 ledger aggregate 동시 활용.
  음수 기초재고 / 출고 > 기초재고 입력 시 sonner toast.warning (5-3 wire).
  ↓
Layer 2 (마감 시 차단) — Story 5.3 closing_guard_service.request_close_attempt
  + 4-2 is_blocked 위 additive. 음수 기말재고 발생 시 409 NEGATIVE_CLOSING_INVENTORY
  typed envelope + ClosingGuardBanner red Alert (5-3 wire).
  ↓
Layer 3 (마감 확정 시 snapshot) — Story 6.1 closing_period_service.confirm_closing_period
  dispatch. CLOSING_READY 시 ledger INSERT (closing_snapshot event_type)
  + monthly_input_periods.status='closed' UPDATE + audit INSERT
  (atomic transaction). 409 ALREADY_CLOSED 시 멱등성 보장 (idempotent no-op skip).
```

## 7. 운영 가이드 (Operator)

### 7.1 정상 흐름 (Happy Path)

1. 사장님이 [월 입력] 페이지에서 모든 6 stream 입력 완료.
2. [마감] tab 클릭.
3. ClosingGuardBanner 가 hidden (invariant OK).
4. ClosingPeriodConfirmationPanel 에 "월 마감 확정 가능" Alert 표시.
5. [마감 확정] 버튼 클릭 → Dialog 열림 → snapshot preview 확인.
6. [확정] 클릭 → sonner `toast.success('월 마감 확정 완료: closing_snapshot {N}건 저장')`.
7. monthly_input_periods.status='closed' 가 되어 reopen 불가.

### 7.2 비정상 흐름 (Edge Case)

#### 음수 기말재고 (CLOSING_BLOCKED)

1. 출고 > 기말 입력 → ClosingGuardBanner 표시 + ClosingPeriodConfirmationPanel
   "마감 차단: 음수 기말재고" Alert + [마감 확정] 버튼 disabled.
2. 출고량 줄이거나 입고량 늘려 0 이상으로 맞춘 후 다시 시도.

#### 수불 event 0건 (EMPTY_PERIOD)

1. 입출력 0건 → ClosingPeriodConfirmationPanel "수불 event 0건: 마감 불가" Alert.
2. 먼저 입출고 입력 후 다시 시도.

#### 이미 마감됨 (ALREADY_CLOSED)

1. monthly_input_periods.status='closed' → "이미 마감됨" Alert + 버튼 비노출.
2. finalized_at 표시. Reopen 은 operator action + reason + audit row 만 가능.

### 7.3 Capability 거부 (service-only tenant)

1. `tenant_settings.industry === 'service'` → ClosingPeriodConfirmationPanel 자체가 비노출.
2. POST 시도 시 403 INDUSTRY_NOT_SUPPORTED typed envelope.
3. Epic 9 ABC costing path 사용 (COST_POOL / ACTIVITY / DRIVER capability).

### 7.4 Audit Log 조회

```
GET /api/v1/inventory/closing-period/audit-trail?period_key=2026-07
→ audit_logs entries filtered by action='closing_period_*'
```

UI 에서는 ClosingPeriodConfirmationPanel + audit-trail-list 가 통합 표시.

## 8. A8 Inline Projection Deprecation Timeline (Epic 5 retro §7 A8)

**5-2 commit + 1 epic maintenance window 종료 시점 = Epic 6 close-out 시점.**

- 6-1 wire 시점 (Epic 6 진입점): inline projection 보존 (1 epic
  maintenance window 진행 중) + closing_period snapshot 은 ledger
  aggregate (5-2 wire) 사용.
- 6-2 / 6-3 wire: inline projection 보존 상태로 wire.
- **Epic 6 close-out 시점에 fold-in vs deprecate 결정** (Epic 11
  reversal 진입 시 inline projection 완전 제거).

## 9. Cross-Reference

- PRD: §F4.3 (월 마감 E2E) + §F5 (마감 보고서 입력 source) + §V4
  (closing snapshot 일관성 verification) + §A11 (입력 시 경고 + 마감
  시 차단 + 마감 확정 시 snapshot 3-layer)
- AD: AD-2 (append-only ledger) + AD-4 (atomicity) + AD-6 (close lock)
  + AD-11 (layer rule) + AD-12 (verification ordering) + AD-15
  (cross-language parity) + AD-22 (reversal entrypoint)
- A8: Epic 3.3 inline projection deprecation timeline (Epic 6 close-out
  시점 fold-in)
- A10: MONTHLY_CLOSING_REPORT capability 신규 (manufacturing 3종 ✅ /
  service-only ❌)
- Carry-over: 5-1 (opening auto-carry) + 5-2 (inventory_ledger) + 5-3
  (closing_guard) + 0.5 (frontend plumbing) + A12 (T12.2 test file
  deferred close-out)
