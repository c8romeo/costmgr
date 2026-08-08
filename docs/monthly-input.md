# 월 입력 (Monthly Input Capture) — Story 3.1 운영자 가이드

> M2 모듈 (`apps/api/modules/m2_input/`)이 어떻게 동작하고,
> 6종 입력(주문·생산·판매·구매·경비·인원)을 어떻게 캡처하는지 설명한다.

## 한 줄 요약

테넌트가 기간(예: `2026-07`)을 선택하면 **M2 월 입력** 모듈이 5~6개 탭을
가로로 보여주고, 사용자가 row를 저장할 때마다 노란 점이 사라진다.
모든 탭의 노란 점이 사라지면 [계산] 버튼이 활성화된다. 한 번에 한
row라도 저장 = 해당 stream의 노란 점 해제.

## 동작 흐름

```
[Web m2-input 페이지]
   ↓ GET /api/v2/monthly-input/{period_key}/state
[m2_input.handlers.get_monthly_input_state]
   ↓ compute_stream_completion (pure, packages.services.m2_input)
   → MonthlyInputStateResponse {rows, completion, is_complete, missing,
                                 capability_mask, fte_display}

[사용자 row 입력 → POST /rows]
   ↓ SELECT FOR UPDATE monthly_input_rows natural key
   ↓ idempotent no-op?  → 200 + no audit (CR 1.1)
   ↓ emit_audit(action='monthly_input_row_saved', flush=True)
   ↓ INSERT or UPDATE monthly_input_rows
   → MonthlyInputStateResponse (yellow dot + [계산] 즉시 갱신)
```

## 6 stream 정의 (PRD §8.M2(b))

| Stream | Backend enum | 한글 라벨 | product_id | 비고 |
|---|---|---|---|---|
| `orders` | `Stream.ORDERS` | 주문 | 필수 | PRD §6.1 주문 입력 |
| `production` | `Stream.PRODUCTION` | 생산 | 필수 | **제조 업종만** (Capability gate) |
| `sales` | `Stream.SALES` | 판매 | 필수 | PRD §6.1 판매 입력 |
| `purchases` | `Stream.PURCHASES` | 구매 | 필수 | PRD §6.1 매입 입력 |
| `expenses` | `Stream.EXPENSES` | 경비 | NULL | 일반 경비 (GL 코드 미정) |
| `labor` | `Stream.LABOR` | 인원 | NULL | `workers`/`days_per_worker`/`daily_wage_krw` 입력 → FTE 환산 |

탭 순서: **주문 → 생산 → 판매 → 구매 → 경비 → 인원** (PRD §8.M2(b) sequence).

## Capability Matrix (PRD §8.M2(b))

[Capability Matrix](./capability-matrix.md) 참조. 핵심 매트릭스:

| Industry | 주문 | 생산 | 판매 | 구매 | 경비 | 인원 |
|---|---|---|---|---|---|---|
| `manufacturing` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `service` | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `manufacturing_service` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `manufacturing_service_other` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

서비스 업종에서 `[생산]` 탭은 hidden. 다른 5 stream은 모든 업종에서 입력 가능.

## 노란 점 / [계산] 게이트 동작

| Stream 행 수 | 노란 점 | [계산] 상태 |
|---|---|---|
| 0 | 🟡 노랑 | disabled (해당 stream이 missing에 포함) |
| ≥1 | ⚪ 없음 | (다른 stream이 모두 채워지면 enabled) |

`is_complete = 모든 visible stream에 ≥1 row` → `true`일 때 [계산] 활성화.

missing list의 한국어 라벨 순서 (PRD §8.M2(b)):
```
제조: 주문 → 생산 → 판매 → 구매 → 경비 → 인원
서비스: 주문 → 판매 → 구매 → 경비 → 인원
```

## 일자별/월합계 모드 (PRD F2.1)

`mode` 필드는 period 단위 (한 period에 1 mode):
- `month_total` (default) — 1 row per (product, stream). `day_no=NULL`
- `daily` — 1 row per (product, stream, day_no=1..31)

전환:
```
POST /api/v2/monthly-input/{period_key}/mode?mode=daily
```

전환 동작:
- `month_total` → `daily`: 기존 row들은 그대로 (`day_no=NULL`). UI에서
  31행 placeholder가 펼쳐짐 (DB row는 신규 생성 X, render-only).
- `daily` → `month_total`: 31행 day별 row들의 합산 표시 (sum, not avg).
  Epic 3.3 음수재고 검증과 일관.

`mode` 토글은 `baseline_revision`을 증가시키지 않음 (UI preference).
`baseline_revision`은 Epic 4 first_calc에서만 bump (Story 3.4 후속).

## FTE 환산 ([인원] 탭 read-only display) — Story 3.2 hook surface

`workers × days_per_worker / 22` (PRD default `workdays_in_month=22`)
→ `format_fte_headcount` (ROUND_HALF_EVEN, 2dp).

`fte_headcount × 2,500,000원` (PRD default `monthly_salary_basis_krw`)
→ `compute_fte_wage_krw` → `2,725,000원` (3명×8일 예시).

Story 3.1은 read-only display만 노출. 정밀 FTE 계산은 Story 3.2.

## Audit log

모든 mutation은 AD-2 audit-first 패턴:
1. SELECT FOR UPDATE row
2. `emit_audit(action=..., flush=True)`
3. INSERT/UPDATE/DELETE

`action` 값:
- `monthly_input_row_created` (POST /rows 새 row)
- `monthly_input_row_updated` (PATCH 또는 값 변경)
- `monthly_input_row_deleted` (DELETE)
- `monthly_input_mode_changed` (POST /mode)

CR 1.1 lesson: 동일 값 재저장 → audit row 없음, version 미증가.

## 자연키 + Unique

`monthly_input_rows`는 partial unique index로 자연키 보호:
```sql
UNIQUE (tenant_id, period_id, stream,
        COALESCE(product_id, '00000000-0000-0000-0000-000000000000'),
        COALESCE(day_no, 0))
```

- `labor`/`expenses` row → `product_id=NULL` → COALESCE sentinel
- `month_total` row → `day_no=NULL` → COALESCE 0

같은 (tenant, period, stream, product, day)에 row 2개 insert 시
IntegrityError → 400 INVALID_PAYLOAD `natural_key_collision`.

## RLS

`supabase/policies/0009_monthly_input_rls.sql`:
- `monthly_input_periods` + `monthly_input_rows` 모두 ENABLE + FORCE RLS
- 4-policy split (SELECT all roles / INSERT owner / UPDATE owner / DELETE owner)
- `DELETE` 허용 (PRD §8.M2 user-input data, NOT ledger)

cross-tenant → RLS predicate 거부 → 404 / 0 rows affected.

## 환경 / 환경 변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `MONTHLY_SALARY_BASIS_KRW` | `2_500_000` | PRD default — [인원] 탭 FTE 환산 임금 |
| `WORKDAYS_IN_MONTH` | `22` | PRD default — FTE 계산 분모 |

상수 위치: `apps/api/modules/m2_input/services/monthly_input_service.py`.
Story 3.2에서 `tenant_settings.payroll.*` JSONB override 추가 예정.

## PIPA / PII / Logging

- 인건비(`daily_wage_krw`, `fte_wage_krw`)는 **PII** — MVP에서 logging
  마스킹은 미적용. **운영 전 `redact_processor` 후속 필수** (Epic 1 회고 C1 defer #3).
- `memo TEXT` (500자 제한) — 사용자 입력 그대로 저장.
  PIPA cross-border gate 적용 (Epic 1 m10_ai 패턴; `require_pipa_review`).

## Deferral / 후속 작업

이번 스토리에서 **의도적으로 미완성** 항목:

1. **Frontend 6-tab + 일자별 toggle UI** — Story 0.5 plumbing 의존
   (shadcn/ui Tabs 설치 후 진행). AC 검증은 backend tests로만 done.
2. **FTE 정밀 계산** — Story 3.2 (PRD §6.1). 본 스펙은 read-only
   display hook만 노출.
3. **음수재고/조업도 실시간 경고** — Story 3.3 (PRD §3.A4).
4. **MonthInputAdapter 본체** — Epic 4 first_calc 진입 시 작성 (AD-13).
5. **InputPromoter** — Story 3.4 (M10 AI drafts → monthly_input promotion).
6. **baseline_revision 발행 정책** — Epic 4 first_calc에서만 bump
   (현재는 단순 입력 수정 in-place).

## 실패 시나리오 매핑 (AD-15 envelope)

| 코드 | HTTP | 원인 |
|---|---|---|
| `INDUSTRY_NOT_SUPPORTED` | 403 | service 업종에서 production stream 작성 시도 |
| `FORBIDDEN_ROLE` | 403 | member/viewer가 mutation 시도 |
| `MONTHLY_INPUT_INVALID_PAYLOAD` | 400 | stream-conditional 요구사항 위반 (product_id 부재 등) |
| `MONTHLY_INPUT_NOT_FOUND` | 404 | row 또는 period 없음 |
| `MONTH_INPUT_PERIOD_LOCKED` | 409 | Epic 4 first_calc 후 lock된 period |
| `PIPA_CONSENT_MISSING` | 451 | memo 필드 cross-border 위반 (Story 3.1 memo는 PIPA gate 적용) |

## 디버깅

- 모든 mutation은 `trace_id` 부여 → 응답 `X-Trace-Id` 헤더 + `audit_logs.payload.trace_id`
- `audit_logs.action='monthly_input_row_created'` / `'updated'` / `'deleted'` / `'mode_changed'`로 행위 추적
- `monthly_input_rows.memo`는 500자 truncate + `redact_processor` 후속 (defer #3)

## FTE 정밀 (Story 3.2)

Story 3.1에서 도입한 read-only FTE hook 표시는 Story 3.2에서 PRD §6.1
인건비 정밀 계산으로 **승격**되었다 (`additive` 변경 — Story 3.1 호환).
자세한 내용은 [docs/monthly-input-fte.md](./monthly-input-fte.md) 참조.

핵심 변경:
- `monthly_input_rows`에 7개 신규 컬럼 (`pay_type` + 5 breakdown + `company_burden_rate`)
- `tenant_settings.payroll` JSONB sub-block (per-tenant override)
- `pay_type='monthly'` (정규직, basis 환산) ↔ `pay_type='daily'` (일용직, direct sum)
- `MonthlyInputService._validate_labor_shape()` — pay_type별 shape validation
- 5개 typed exceptions (Task 3.2): 모두 AD-15 §4 envelope으로 응답
- `FteDisplay` enriched: `pay_type` · `breakdown` · `source_rows` · `payroll_settings`
- TS mirror `apps/web/lib/l2-input-fte.ts` — cross-language drift sentinel

## 음수재고·조업도 실시간 경고 (Story 3.3)

Story 3.1/3.2가 캡처 + FTE 정밀 계산까지 다뤘다면, Story 3.3는
PRD §A11 (오류의 가시화) + §V3 (음수재고) + §V5 (조업도) 정책에 따라
**입력 시점의 경고(200 OK + 진행 허용)**를 추가한다. 마감 시 임계
위반 차단은 Epic 4 `MonthInputAdapter.first_calc` hook에서.

핵심 변경:
- `monthly_input_periods`에 신규 컬럼 `opening_inventory JSONB` (4-namespace AD-23)
  `{products: [{product_id, qty}]}`. Story 5-1에서 ledger-backed read로
  자동 carry-chain 진입 (`TODO(epic-5)` marker).
- `MonthlyInputStateResponse`에 4개 read-only 필드 추가:
  `warnings: list[WarningResponse]`, `is_blocked: bool`, `warnings_count: int`,
  `top_n_severity: int`. **클라이언트 write 시 400 `MONTHLY_INPUT_WARNINGS_READ_ONLY`**
  (서버 자동 계산 항목, AC #7 server-side defense).
- 2개 신규 typed exception (서버 응답 envelope):
  - `MONTHLY_INPUT_WARNINGS_READ_ONLY` (400) — 클라이언트가 `warnings` /
    `is_blocked` / `warnings_count` / `top_n_severity` 필드를 쓰려고 시도
  - `MONTHLY_INPUT_INVENTORY_PROJECTION` (422) — projection kernel 실패
    시 `details.reason` + `details.row_count` 동봉
- 2개 warning code (PRD §V3·§V5):
  - `NEGATIVE_CLOSING_INVENTORY` — 기말재고 < 0 (PRD §6.2: 기초+구입-생산출고)
  - `OVERCAPACITY_OPERATING_RATE` — 조업도 > 100% (PRD §6.1 (2): FTE × 월근무시간)
- `MonthlyInputService.get_state()` → `_compute_warnings_aggregate_for_state`
  → inventory projection kernel (PRD §6.2 수불부) + operating rate kernel
  → `aggregate_warnings` (severity ASC + closing_qty ASC) → 4 필드 response
- service-only 테넌트는 inventory-bearing product type 없음 → 0개 경고
  (예외 아님 — capability-ungated)
- TS mirror `apps/web/lib/l2-input-warnings.ts` — Decimal `ROUND_HALF_EVEN`
  banker's rounding cross-language parity (AD-8)
- 5 cross-language parity tests in
  `tests/integration/test_m2_input_label_consistency.py` (15/15 green)
- 18 service-layer pure helper tests in
  `tests/services/test_m2_input_warnings_service.py` (pure helpers only)
- 11 DB skipif handler integration tests in
  `tests/api/test_monthly_input_warnings.py` (Story 0.4 CI shim mode)

### SEVERITY_ORDER (PRD §A11)

```
error=0, warning=1, info=2
```

`top_n_severity` = min(SEVERITY_ORDER[w] for w in warnings). 빈 경고
리스트 → `0` (sentinel for "no warnings").

### 응답 예시

```json
{
  "warnings": [
    {
      "code": "NEGATIVE_CLOSING_INVENTORY",
      "severity": "error",
      "message_ko": "PRD-0001(달걀) 기말재고 -30 → 음수 경고",
      "details": {
        "product_id": "...",
        "product_code": "PRD-0001",
        "opening_qty": "10",
        "inbound_qty": "0",
        "outbound_qty": "40",
        "closing_qty": "-30",
        "stream": "sales"
      },
      "stream": "sales",
      "trace_id": "...",
      "timestamp": "2026-08-01T12:00:00Z"
    }
  ],
  "is_blocked": true,
  "warnings_count": 1,
  "top_n_severity": 0
}
```

`is_blocked = warnings_count > 0` (PRD §A11 입력 시점 진행 허용).
마감 시점 차단은 Epic 4 `first_calc` hook에서 임계 위반 시 422로 처리.

## 참조

- 스펙: `_bmad-output/implementation-artifacts/3-1-six-stream-monthly-input-ui-month-total-default.md`
- Story 3.3 스펙: `_bmad-output/implementation-artifacts/3-3-negative-inventory-overcapacity-real-time-warning.md`
- FTE 정밀 가이드: [docs/monthly-input-fte.md](./monthly-input-fte.md)
- Architecture: AD-13 (`MonthInputAdapter`) · AD-17 (`InputPromoter`)
- Architecture: AD-13 (`MonthInputAdapter`) · AD-17 (`InputPromoter`)
- Capability matrix: `docs/capability-matrix.md`
- 이전 Epic 가이드:
  - `docs/ai-document-extraction.md` (Story 1.3 — input_drafts 패턴)
  - `docs/architecture-decisions/AD-7-ai-extraction-table-naming.md`
- 다음 Epic: Epic 4 (Cost Calculation & Verification) — first_calc에서
  `monthly_input_periods.baseline_revision` bump + `locked_by_calculation=true`

## Story 5.1 — Opening Inventory Auto-Carry Chain

PRD §F4.1: 기초재고는 자동 이월되며, 매달 다시 입력하지 않아도 됨.
첫 행 입력 이후 `stream='opening_inventory'` POST는 400
`MONTHLY_INPUT_OPENING_MANUAL_EDIT` 으로 거부됩니다.

### 자동 wire

`GET /state` 호출 시 silent hook:
- `OpeningCarryService.auto_carry_on_get_state(period)` 가 opening_inventory JSONB 가
  비어있고 prev period 가 존재하면 carry chain 실행 (idempotent).
- opening_inventory 가 이미 locked or populated 이면 no-op.
- emit_audit(action=`monthly_input_period_opening_carried`) BEFORE UPDATE (AD-2).

### 첫 행 입력 시 lock

`POST /rows` (INSERT 경로) 가 성공하면:
- `OpeningCarryService.lock_opening_after_first_row(period)` 호출.
- `_locked=True, _lock_reason_ko="전월 기말 자동 이월"` 마커 추가.
- 이후 `stream='opening_inventory'` POST 는 400 reject.

### 수동 trigger

`POST /api/v1/inventory/opening-carry/{period_id}`:
- 운영자가 데이터 수정 후 강제로 carry chain 다시 실행 가능.
- 12-period 체인 깊이 초과 시 422 `MONTHLY_INPUT_CARRY_CHAIN_LIMIT`.
- prev period 없으면 422 `MONTHLY_INPUT_CARRY_PREV_PERIOD_NOT_FOUND`.

### 응답 스키마 추가 필드

`MonthlyInputStateResponse` (Story 5.1) 확장:
- `opening_inventory: dict[str, str]` — product_id_str → qty_str
- `opening_inventory_locked: bool`
- `opening_inventory_lock_reason_ko: str | None`

### 참조

- 운영자/dev 가이드: [docs/opening-inventory-carry.md](./opening-inventory-carry.md)
- Architecture: AD-2 (audit-first) · AD-22 (reversal entrypoint)
- 스펙: `_bmad-output/implementation-artifacts/5-1-opening-inventory-auto-carry-chain.md`

## §5.2 Inventory Ledger Stream Hook (Story 5.2)

`POST /api/v1/monthly-input/rows` 의 INSERT path 에서 inventory
streams (purchases / sales / production) 의 row 가 들어올 때마다
`inventory_ledger` 테이블에 append-only 행을 추가합니다.

### Stream → event_type 매핑

| monthly_input_rows.stream | inventory_ledger.event_type | direction |
|---|---|---|
| purchases | `purchase_inbound` | + qty |
| sales | `sales_outbound` | − qty |
| production | `production_output_inbound` | + qty (output product_qty) |

Material consumption (input side of production) 은 Epic 6 wire — 당분간
production row 가 추가되어도 ledger 행의 source 가 `monthly_input` 이고
event_type 이 `production_output_inbound` (output 만 추적).

### Hook 위치

`_emit_inventory_ledger_event_for_row(new_row, period, payload)`:
- `payload.stream ∈ {"purchases", "sales", "production"}` AND
  `payload.product_id IS NOT NULL` AND `payload.qty IS NOT NULL` 조건
  만족 시 호출.
- Service-layer helper 가 `LedgerService.append_event` 호출 → 3중 방어
  (DB trigger + AST guard + audit) 자동 적용.

### Epic 3.3 inline projection swap (AC #5)

5-2 이전: `_compute_warnings_aggregate_for_state` 가
`build_inventory_projection(rows, opening_balance)` 직접 호출.
5-2 이후: `_compute_inventory_projection_for_state` (T8 wrapper) 가
`LedgerService.query_period_closing_all(period_key=...)` 사용.
`build_inventory_projection` 자체는 Epic 6 close-out retro 까지
유지 (5-1 carry chain path 에서 여전히 사용).

## §5.3 Closing Guard Stream Hook (Story 5.3)

Story 5.3 은 음수 기말재고 (PRD §F4.2) 와 연결성 검증 (PRD §V3) 을
monthly_input 흐름에 결합합니다. `ClosingGuardService` 가 4 가지
operation 을 제공하고, `MonthlyInputStateResponse` 가 5 개의
closing-guard field 로 확장됩니다.

### ClosingGuardService — 4 operations

`apps/api/modules/m4_inventory/services/closing_guard_service.py` :

| Op | 호출 지점 | 책임 |
|---|---|---|
| `evaluate_closing_guard` | `GET /closing-guard/evaluate` handler + `get_state` extension | 5-2 ledger aggregate 종합 → `ClosingInvariant` (CLOSING_OK / NEGATIVE_CLOSING / EMPTY_PERIOD) + `negative_products` top-5 offenders + audit emit (`closing_guard_passed` or `closing_guard_violated`). |
| `request_close_attempt` | `POST /closing-guard/close-attempt` handler + 4-2 `attempt_close` additive | 4-2 `is_blocked` check 위 additive: invariant.code = NEGATIVE_CLOSING → 409 NEGATIVE_CLOSING_INVENTORY envelope (AD-15 §4). Audit-first ordering: 409 envelope BEFORE audit INSERT (CR 1.1 lesson). |
| `emit_production_ledger_events` | `save_row` BOM-aware emit hook (stream='production') | 5-2 `LedgerService.append_event` 호출 per event: 1 × `production_output_inbound` (output product qty) + N × `production_material_consumption` (per BOM child, 음수 qty). BOM=None or children empty → output event only (no `adjustment_positive`). |
| `validate_closing_invariant_against_active_products` | `verify_v3_closing_invariant` dispatch | product whitelist = `SELECT id FROM products WHERE tenant_id=:tenant_id AND is_active=true`. `verify_closing_invariant` pure-kernel 호출 → V3 verdict (status='passed'/'failed'/'skipped' + failures). V3 fail → audit `closing_guard_violated`. |

### 5 NEW fields on `MonthlyInputStateResponse` (AC #3 wire spec)

`apps/api/modules/m2_input/services/monthly_input_service.py::get_state`
는 closing-guard aggregate + V3 verdict + audit-trail 을 다음 5 field 로
project 합니다:

| Field | Type | Source | 비고 |
|---|---|---|---|
| `closing_guard_blocked` | `bool` | `ClosingGuardService.evaluate_closing_guard().invariant.code == 'NEGATIVE_CLOSING'` | Frontend [마감] button disabled gate. |
| `closing_guard_audit_trail` | `list[AuditLogEntry]` | `audit_logs WHERE action='closing_guard_passed' OR 'closing_guard_violated'` ORDER BY `created_at DESC` LIMIT 10 | Frontend [마감 검증 이력] tab render. |
| `production_consumption_events` | `list[InventoryLedgerEvent]` | `closing_guard_service.emit_production_ledger_events` 최근 호출 결과 (per period) | BOM-aware ledger event preview for [수불부] tab. |
| `v3_verdict` | `V3Verdict \| None` | `ClosingInvariantVerifier.verify_v3_closing_invariant` 4-3 V3 slot fill | Status='passed'/'failed'/'skipped' + failures + skip_reason_ko. |
| `closing_guard_invariant` | `ClosingInvariant` | `ClosingGuardService.evaluate_closing_guard().invariant` | Typed `code` + `message_ko` + `closing_per_product` dict. |

### Hook 위치 (Story 5.3 wire additive on 4-2 + 5-2)

1. **`save_row` BOM-aware emit** (`stream='production'`):
   - 기존 5-2 `_emit_inventory_ledger_event_for_row` 호출 직후,
     BOM (Story 2.2 schema) 존재 시
     `closing_guard_service.emit_production_ledger_events` dispatch.
   - BOM=None or `bom.children == []` → output event only
     (P15 patch: no `adjustment_positive` emit).
   - 모든 emit 는 audit-first + idempotent no-op skip (CR 1.1).

2. **`attempt_close` additive guard** (4-2 wire 위):
   - 기존 `is_blocked` check 통과 후,
     `closing_guard_service.request_close_attempt` dispatch.
   - invariant.code='NEGATIVE_CLOSING' → 409 NEGATIVE_CLOSING_INVENTORY
     envelope (AD-15 §4 Korean message).

3. **`get_state` extension** (5 NEW fields populate):
   - `closing_guard_blocked` + `closing_guard_invariant` →
     `evaluate_closing_guard` dispatch.
   - `closing_guard_audit_trail` →
     `audit_logs` query filtered by closing_guard actions.
   - `production_consumption_events` →
     `inventory_ledger` query filtered by stream='production' events.
   - `v3_verdict` →
     `ClosingInvariantVerifier.verify_v3_closing_invariant` dispatch.

### AD-15 §4 Typed envelope contract

`ClosingGuardService` raises 5 typed exceptions mapped in `apps/api/main.py`:

| Exception | HTTP | code | 비고 |
|---|---|---|---|
| `ClosingGuardNegativeInventoryError` | 409 | `NEGATIVE_CLOSING_INVENTORY` | banner_ko="기말재고 음수: 마감 불가" |
| `ClosingGuardInvalidPeriodKeyError` | 422 | `CLOSING_GUARD_INVALID_PERIOD_KEY` | AD-24 pattern check |
| `ClosingGuardServiceOnlyTenantError` | 403 | `INDUSTRY_NOT_SUPPORTED` | service-only tenant early-return |
| `ClosingGuardProductionConsumptionError` | 500 | `CLOSING_GUARD_PRODUCTION_CONSUMPTION_ERROR` | save_row emit failure |
| `ClosingGuardAuditEmitError` | 500 | `CLOSING_GUARD_AUDIT_EMIT_ERROR` | audit-first fail-closed (CR 1.1) |

### Capability gate

- `Capability.INVENTORY_CLOSING_GUARD` — manufacturing 3종 ✅ / service-only ❌
- `Capability.MONTHLY_INPUT_PRODUCTION` — manufacturing 3종 ✅ / service-only ❌

Service-only tenant: guard 자체 disabled (`skip_reason_ko='service-only tenant은 inventory 의미 없음'`),
v3_verdict.status='skipped', closing_guard_blocked=false.

### 참조

- 운영자/dev 가이드: [docs/closing-guard.md](./closing-guard.md)
- Architecture: AD-2 (audit-first) · AD-11 (layer rule) · AD-15 §4 (typed envelope)
- 스펙: `_bmad-output/implementation-artifacts/5-3-negative-closing-inventory-guard.md`
- V3 verification: [docs/cost-engine.md#v3](./cost-engine.md#v3)
- 5-1 carry-over: [docs/opening-inventory-carry.md](./opening-inventory-carry.md)
- 5-2 ledger append-only: [docs/inventory-ledger.md](./inventory-ledger.md)

## Story 11.2 EXTENSION — Close Sequence Panel 진입점 + 4-stage UI flow + partial close 거부 UX

Epic 11 cj-style 3-story 분할 2번째 (Epic 5 retro §6 W1) — 11-2 wire는 본
monthly-input 마감 탭 진입점 (5-3 MonthlyInputTabs.tsx 마감 �) 위에
**CloseSequencePanel + 4-stage progress UI** 추가:

### 진입점 흐름 (deferred to bmad-code-review sweep)

```
m2-input/period/[periodKey] (5-3 page.tsx)
  └─ MonthlyInputTabs (5-3)
      └─ 마감 � (5-3 ClosingGuardBanner)
          └─ CloseSequencePanel (11-2 NEW — shadcn Card + StepIndicator + progress bar)
              ├─ divisions  ─ step_complete → manufacturing
              ├─ manufacturing ─ step_complete → abc
              ├─ abc ─ step_complete → common
              └─ common ─ confirm → confirmed (CloseSequenceConfirmButton + shadcn Dialog)
```

### 4-stage UI 표시

- 4개의 step indicator (divisions → manufacturing → abc → common) 각각
  완료 / 진행중 / 미시작 3-state 시각화.
- partial close 거부 시 `partial_close_blocked_toast_message` (sonner
  toast error) — "전체 4단계 완료 후 마감 가능: {missing_step} 단계 미완료".
- ALREADY_CONFIRMED idempotent — confirm dispatch 후 success toast +
  panel read-only mode.

### Capability gate

- `Capability.CLOSE_SEQUENCE_LOCK` — manufacturing 3종 ✅ / service-only ❌
  (service tenant 진입 시 panel 자체 disabled + read-only 표시).

### 11-2 wire 정합

- 5-3 ClosingGuardBanner (closing ≥ 0 invariant) 위에 additive — banner는
  pre-requisite (V3 PASS 시에만 close sequence 진입 가능).
- 6-1 ClosingPeriodConfirmationPanel 위 additive — close sequence confirm
  후 `monthly_input_periods.status='closed'` + `fiscal_periods.status='closed'`
  동시 dispatch (CR 1.1 audit-first).

### Frontend deferred (Task 10)

- 11-2 spec 본문 §Task 10 frontend 9 subtasks — bmad-code-review
  carry-over sweep 대상. 본 스토리 checkpoint commit (1dbb01f) 은
  backend wire 만 커버.

상세: [docs/close-sequence-lock.md](./close-sequence-lock.md) SSOT + [docs/capability-matrix.md](./capability-matrix.md) v1.11.

## 참조

