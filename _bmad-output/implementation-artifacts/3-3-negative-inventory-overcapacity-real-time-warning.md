---
baseline_commit: d5d7da9
---

# Story 3.3: Negative Inventory & Overcapacity Real-Time Warning

Status: ready-for-dev

> Epic 3 세 번째 — 입력 중 음수재고·조업도 초과 발생 시 즉시 빨강 경고 + 마감 진입 차단.
> Story 3.1의 6-stream 입력 + Story 3.2의 FTE 정밀 환산 위에 **실시간 이상 신호 감지 레이어** (PRD §3.A11) 추가.
> **모듈**: 기존 `m2_input/` 확장 + 신규 `packages/services/m2_input/` (inventory_projection + operating_rate + warnings)

<!-- dev-context: Epic 1 retro W4 (audit-first + idempotent no-op) — 매 warning 트리거 mutation마다 audit-first 패턴 적용.
                    Epic 2 retro W3 (bulk-replace PUT atomic) — warning aggregate는 bulk-replace 일관성으로 재계산.
                    Epic 2 retro W4 (TS mirror regex 검증) — TS mirror parity test 적용.
                    Story 3.1 read-only state hook + Story 3.2 FTE precision 위에 additive.
                    5 deferrals from Story 3.1 중 (d) 음수재고·조업도 경고 = 본 스펙.
                    AD-22 append-only-leaning — monthly_input_rows는 user-input (DELETE 허용), inventory_ledger (Epic 5)는 append-only.
                    AD-13 MonthInputAdapter — Epic 4 first_calc 시점에 entered; 본 스펙은 inline projection.
                    Epic 5 ledger stub marker — inventory_projection.py에 `TODO(epic-5)` 마커 (5-1/5-2 진입점).
                    A11 운영 원칙: 입력 시 경고(진행 허용) → 마감 시 임계 위반 차단 (Epic 4 first_calc hook).
                    Action Item A1 (capability-matrix.md) — Story 3.3는 capability 변경 없음, footnote만 추가. -->

## Story

As a **사장님** (small/medium business owner),
I want **"2026-07" [판매]·[구매]·[생산] 탭에서 출고/매출/생산 row를 저장하거나 수정할 때, 음수재고나 조업도 초과가 발생하면 입력 즉시 빨강 토스트로 경고가 뜨고 [마감] 버튼이 disabled로 잠기며, 해당 수치를 정상 범위로 되돌리면 경고가 자동으로 사라지고 [마감]이 다시 활성화되는 것**,
so that **"티브이 시트에서 3개월을 방치한 달걀 -7,500개" 같은 데이터 오류가 음수 기말 그대로 [계산]까지 흘러가서 invalid 월마감을 만드는 사고를 시스템적으로 차단** — PRD §3 A11 (오류의 가시화) · F2.3 (음수재고/조업도 초과 입력 즉시 경고) · F4.2 (음수 기말 감지 즉시 경고 + 마감 차단) · §11 V3 (음수재고) · §11 V5 (조업도) · 운영 원칙 (입력 시 경고 → 마감 시 차단).

## Acceptance Criteria

1. **Given** 기초재고 100개, PRD-0001 (material) row가 monthly_input_periods `2026-07`에 존재
   **When** 사용자 [판매] 탭에서 PRD-0001 출고 130개를 저장
   **Then** `POST /api/v2/monthly-input/2026-07/rows` 응답이 **200** + `state.warnings: [...]` 배열에 1건 포함:
     - `{code: "NEGATIVE_CLOSING_INVENTORY", severity: "error", message_ko: "PRD-0001(달걀) 기말재고 -30 → 음수 경고", details: {product_id, product_code, opening_qty: 100, inbound_qty: 0, outbound_qty: 130, closing_qty: -30, period_key: "2026-07", stream: "sales"}, stream: "sales", trace_id, timestamp}`
   **And** `state.is_blocked: true` (PRD §A11 close-time rule — Epic 4 first_calc hook; Story 3.3는 입력 시점 게이트만)
   **And** **PRD §A11 입력 시 경고(진행 허용)** 정책: row 저장은 성공 (200 OK + audit row). 마감이 blocked.
   **And** `tests/services/test_m2_input_inventory_projection.py` `test_negative_closing_inventory_red_alert` (PRD §V3 fire) passes with `closing_qty = -30`
   **And** `tests/integration/test_m2_input_label_consistency.py` `test_warning_codes_match_python` verifies TS mirror has identical code list

2. **Given** PRD-0001 (material) 기초재고 100개, 출고 100개 저장 → 정상 (closing_qty = 0)
   **When** 사용자가 동일 row를 출고 100개 → 130개로 **수정 (PATCH)**
   **Then** `state.warnings`는 즉시 `{NEGATIVE_CLOSING_INVENTORY: PRD-0001}`로 전환 (200 OK + audit row 1개)
   **And** 출고 130개 → 80개로 다시 수정 시 `state.warnings`는 **빈 배열**로 전환 (closing_qty = 20)
   **And** `is_blocked` flag는 `len(warnings) == 0` → false, else true
   **And** `tests/services/test_m2_input_warnings.py` `test_warning_aggregate_immediate_disappear` passes

3. **Given** PRD-0001 (material) 기초재고 100개, 출고 0개, 인원 FTE 환산 1.09명 (`tenant_settings.payroll.standard_monthly_hours=228`)
   **When** 사용자가 [생산] 탭에서 PRD-0001 생산수량 250개를 저장 (unit_time_hours=1.0 기본값, Epic 7 unit_time 정밀화 후속)
   **Then** `state.warnings`에 1건 추가:
     - `{code: "OVERCAPACITY_OPERATING_RATE", severity: "error", message_ko: "총작업가능시간 248.5h(1.09 × 228) < 생산요구시간 250h → 100.6% (한도 초과)", details: {total_fte_headcount: "1.09", standard_monthly_hours: 228, total_available_hours: "248.5", production_required_hours: "250", operating_rate_pct: "100.6", limit_pct: 100, period_key: "2026-07"}, stream: "production", trace_id, timestamp}`
   **And** `is_blocked: true` (마감 차단)
   **And** `tests/services/test_m2_input_operating_rate.py` `test_overcapacity_110_percent_triggers_warning` (PRD §V5 fire) passes with `operating_rate_pct = Decimal("100.6")`

4. **Given** 인원 FTE 환산 1.09명, production 100개 (100h, 43.9%) → 정상 (no warning)
   **When** production 100개 → 250개로 **수정**
   **Then** `state.warnings`는 즉시 `[OVERCAPACITY_OPERATING_RATE]`로 전환 (PRD §V5 fire)
   **And** production 250개 → 50개로 다시 수정 시 `state.warnings`는 빈 배열로 전환
   **And** `tests/services/test_m2_input_operating_rate.py` `test_under_capacity_no_warning` + `test_overcapacity_immediate_clear` passes

5. **Given** PRD-0001 (material) 출고 130개로 NEGATIVE warning 발동 중 (+ 동시에 production 250개로 OVERCAPACITY warning도 발동)
   **When** 사용자가 출고 130개 → 50개로 수정 (PRD-0001 closing_qty = 50 정상화)
   **Then** `state.warnings`는 NEGATIVE 가 사라지고 OVERCAPACITY 만 남음 (= 1건)
   **And** `is_blocked: true` 유지 (OVERCAPACITY still active)
   **And** production 250개 → 50개로도 수정하면 `state.warnings = []` + `is_blocked: false`
   **And** `tests/services/test_m2_input_warnings.py` `test_independent_warning_resolution` passes

6. **Given** 테넌트가 `product_type='service'` (예: PRD-0005 컨설팅)만 보유 — 재고 추적 대상 0
   **When** 기간 입력 시작
   **Then** `state.warnings = []` (음수재고 대상 product 0건)
   **And** `[운영률]` warning은 production stream rows가 0이어도 인원 FTE > 0인 경우 발동 (production_required_hours = 0 → operating_rate = 0% → no warning, 단 production_required_hours > 0 일 때만 분모 검사로 발동)
   **And** `tests/services/test_m2_input_warnings.py` `test_service_only_tenant_no_inventory_warning` passes (regression: Story 2.1의 service product_type과 일관)

7. **Given** server-side defense (AC #5 Story 3.2와 동일 패턴):
     - `PATCH /api/v2/monthly-input/{period_key}/rows/{row_id}` body에 `warnings: [...]` 또는 `is_blocked: bool` 필드 PATCH 시도
   **When** 사용자가 URL-poking
   **Then** Pydantic `extra='forbid'` (Story 3.1 base) + Story 3.3 schema extension이 미인가 필드 거부 → **400 INVALID_PAYLOAD** + `details: {field: "warnings", reason: "computed field; not user-editable"}`
   **And** `tests/api/test_monthly_input.py` `test_patch_warnings_field_rejected_400_read_only` (DB-backed skipif)
   **And** server-side 계산된 `state.warnings[]`는 read-only — UI는 단순 렌더 + `[마감]` enable/disable

8. **Given** 한 period에 multiple products with negative inventory (PRD-0001 -30 + PRD-0002 -50 + PRD-0003 -10)
   **When** `state.warnings` 계산
   **Then** `state.warnings` 배열은 **severity 내림차순** (모두 error) → `closing_qty` **오름차순** (가장 음수 큰 순 = PRD-0002 -50 먼저)
   **And** `state.warnings_count: 3` (TS mirror 정렬 검증)
   **And** `top_n_severity: 1` (UI에서 "1건" 표시 시 가장 심각한 1건 우선 노출)
   **And** `tests/services/test_m2_input_warnings.py` `test_warnings_sorted_by_severity_and_closing_qty` passes

9. **Given** AC #1-8 모든 backend wiring
   **When** 비교 가능한 warning state를 Python/TS 양쪽에서 계산
   **Then** `apps/web/lib/l2-input-warnings.ts`가 `packages/services/m2_input/warnings.py`의 pure helpers (build_inventory_projection, compute_operating_rate, aggregate_warnings)와 **동일한 출력** 보장
   **And** `tests/integration/test_m2_input_label_consistency.py` 5 cases 추가:
     - `test_warning_codes_match_python` (AC #1 fire)
     - `test_warning_severity_order_matches_python` (AC #8 sort)
     - `test_inventory_projection_opening_inbound_outbound_matches_python` (Epic 5 ledger stub 호환)
     - `test_operating_rate_110_percent_matches_python` (AC #3, ROUND_HALF_EVEN)
     - `test_aggregate_warnings_independent_resolution_matches_python` (AC #5)
   **And** Node v24 `--input-type=module` 실행으로 cross-language numeric parity (Story 3.2의 검증 패턴, Epic 2 W4)

## Tasks / Subtasks

- [ ] **Task 1 — Pure-Python inventory projection + operating rate + warnings aggregate** (AC: #1, #3, #5, #6, #8)
  - [ ] 1.1 — Create `packages/services/m2_input/inventory_projection.py` (stdlib-only, AD-1/AD-5):
    - `InventoryMovement: NamedTuple` = `product_id, opening_qty, inbound_qty, outbound_qty` (AD-15 snake_case)
    - `INVENTORY_PRODUCT_TYPES: Final[frozenset[str]]` = `{"material", "semi_product", "product"}` (service/merchandise 제외, PRD §6.2)
    - `compute_opening_inventory(prev_period_projection: dict | None, product_id: UUID) -> Decimal` — cj-style default: 이전 period 데이터 없으면 0 (Epic 5 ledger later)
    - `compute_closing_inventory(opening: Decimal, inbound: Decimal, outbound: Decimal) -> Decimal` — `opening + inbound - outbound` (PRD §6.2 수불 공식)
    - `build_inventory_projection(rows: list[MonthlyInputRowLike], opening_balance: dict[UUID, Decimal] | None) -> list[InventoryMovement]` — per-product aggregation
      - `sales` rows → outbound (qty)
      - `purchases` rows → inbound (qty) — material/merchandise 한정
      - `production` rows → inbound (qty) — material→product 변환 (PRD §6.1); output product_qty 만 카운트 (input material 소모는 Epic 5 ledger 진입점)
    - **TODO(epic-5) marker**: `LEDGER_REFERENCE_QUERY_STUB: Final[str] = ""` — Epic 5 Story 5-1 (auto-carry) + 5-2 (append-only ledger) 진입점. Inline projection은 Epic 5 이전 source-of-truth (Story 3.3 코드 내 명시 코멘트)
  - [ ] 1.2 — Create `packages/services/m2_input/operating_rate.py` (stdlib-only, AD-5):
    - `DEFAULT_UNIT_TIME_HOURS: Final[Decimal] = Decimal("1.0")` — MVP default (PRD §6.1 "단위공수: 제품별 정의 우선 → 생산유형 상속" — Story 2.1 schema에 컬럼 부재, Epic 7 BEP unit_time 정밀화 후속)
    - `compute_total_available_hours(total_fte_headcount: Decimal, standard_monthly_hours: int) -> Decimal` — `total_fte × standard_monthly_hours` (Story 3.2 fte_display 활용)
    - `compute_production_required_hours(production_rows: list, unit_time_hours: Decimal = DEFAULT_UNIT_TIME_HOURS) -> Decimal` — `Σ(qty × unit_time)`
    - `compute_operating_rate(available_hours: Decimal, required_hours: Decimal) -> Decimal` — `required / available × 100` (PRD §6.1 (2)) → 2dp ROUND_HALF_EVEN
    - `OperatingRateLimit = Decimal("100")` — 100% 초과 시 OVERCAPACITY 발동
  - [ ] 1.3 — Create `packages/services/m2_input/warnings.py` (stdlib-only, AD-5):
    - `WarningCode: str = Enum("NEGATIVE_CLOSING_INVENTORY", "OVERCAPACITY_OPERATING_RATE")` — 2 codes (Story 3.3 범위)
    - `class Warning(NamedTuple)` = `code, severity, message_ko, details: dict, stream, trace_id, timestamp`
    - `SEVERITY_ORDER: Final[dict[str, int]] = {"error": 0, "warning": 1, "info": 2}` (PRD §A11 error > warning > info)
    - `build_inventory_warnings(projection: list[InventoryMovement]) -> list[Warning]` — closing_qty < 0 → 1건 (per product)
    - `build_operating_rate_warning(...)` — operating_rate > 100% → 1건 (per period)
    - `aggregate_warnings(inventory_warnings, operating_rate_warning) -> list[Warning]` — sort by (severity ASC, closing_qty ASC for inventory, descending for operating_rate)
    - `Korean_message_builders`: `_format_inventory_warning_ko(product, projection)` + `_format_operating_rate_ko(fte, hours, required, rate)` — handlers/UI 공통 (AD-11 cross-language pattern)
  - [ ] 1.4 — Update `packages/services/m2_input/__init__.py` — re-export public API (inventory_projection, operating_rate, warnings)
  - [ ] 1.5 — Tests `tests/services/test_m2_input_inventory_projection.py` (16+ cases):
    - `test_opening_inventory_zero_for_new_tenant`: prev_period=None → 0
    - `test_opening_inventory_from_prev_period`: prev_period={product_id: 100} → 100
    - `test_closing_inventory_basic_positive`: opening=100, inbound=0, outbound=30 → 70
    - `test_closing_inventory_negative_basic`: opening=100, outbound=130 → -30 (AC #1 fire)
    - `test_closing_inventory_exact_zero`: opening=100, outbound=100 → 0 (no warning)
    - `test_inventory_projection_sales_only_outbound`: sales row → outbound
    - `test_inventory_projection_purchases_inbound`: purchases row → inbound
    - `test_inventory_production_outbound_material_consumption`: production output product_qty → inbound for product
    - `test_inventory_projection_excludes_service_products`: product_type='service' → not in projection
    - `test_inventory_projection_multiple_products`: 3 products → 3 movements
    - `test_inventory_projection_zero_qty_excluded`: qty=0 → skip
    - `test_inventory_projection_round_half_even_decimal`: qty=Decimal("0.005") → 0.01 (ROUND_HALF_EVEN)
    - `test_inventory_projection_unknown_product_in_prev_period`: prev had product A, current doesn't → opening=0 (not stale)
    - `test_inventory_projection_closing_qty_negative_for_labor_no_product`: labor stream → ignored (no product_id)
    - `test_inventory_projection_empty_rows`: empty rows → empty projection
    - `test_inventory_projection_aggregate_by_product`: 3 sales rows of same product → sum outbound
  - [ ] 1.6 — Tests `tests/services/test_m2_input_operating_rate.py` (12+ cases):
    - `test_total_available_hours_basic`: fte=Decimal("1.09"), hours=228 → Decimal("248.52")
    - `test_total_available_hours_zero_fte`: fte=0 → 0
    - `test_production_required_hours_basic`: 1 row qty=100 → 100
    - `test_production_required_hours_unit_time_override`: unit_time=2.5, qty=10 → 25
    - `test_production_required_hours_multiple_rows`: 100+50+30 → 180
    - `test_operating_rate_50_percent`: 100h / 200h → Decimal("50.00")
    - `test_operating_rate_100_percent`: 200/200 → Decimal("100.00") (boundary, no warning)
    - `test_operating_rate_110_percent_triggers_overcapacity`: 220/200 → Decimal("110.00") (AC #3 fire)
    - `test_operating_rate_round_half_even`: 1.005 → 1.00 (banker's rounding)
    - `test_operating_rate_zero_available_no_division_error`: required=0, available=0 → 0 (no warning)
    - `test_operating_rate_required_zero_no_warning`: required=0 → 0% (no warning even if available=0)
    - `test_operating_rate_default_unit_time_1_hours`: 250 / 248.5 → Decimal("100.60") (AC #3 example)
  - [ ] 1.7 — Tests `tests/services/test_m2_input_warnings.py` (8+ cases):
    - `test_warning_codes_python_enum`: 2 codes exposed
    - `test_build_inventory_warnings_single_negative`: 1 product closing=-30 → 1 warning
    - `test_build_inventory_warnings_multiple_products_sorted`: 3 products → sorted by closing_qty ASC
    - `test_build_operating_rate_warning_under_limit`: rate=80% → no warning
    - `test_build_operating_rate_warning_over_limit`: rate=110% → 1 warning
    - `test_aggregate_warnings_independent_resolution`: items 1+2 → clear 1 → item 2 remains (AC #5)
    - `test_aggregate_warnings_empty`: empty inventory + no overcapacity → []
    - `test_warning_aggregate_immediate_disappear`: clear warning → state.warnings = [] (AC #2)
    - `test_korean_message_format_inventory`: "PRD-0001(달걀) 기말재고 -30 → 음수 경고" (PRD §V3 friendly)
    - `test_korean_message_format_operating_rate`: "총작업가능시간 248.5h(1.09 × 228) < 생산요구시간 250h → 100.6% (한도 초과)" (AC #3)
    - `test_service_only_tenant_no_inventory_warning`: product_type='service' products → 0 warnings (AC #6)
    - `test_warnings_sorted_by_severity_and_closing_qty`: severity ASC + closing_qty ASC (AC #8)

- [ ] **Task 2 — DB schema: opening inventory column on monthly_input_periods** (AC: #6, future Epic 5)
  - [ ] 2.1 — Create `apps/api/alembic/versions/0011_monthly_input_periods_opening_inventory.py` (revision `0011_...`, down_revision = `0010_monthly_input_labor_breakdown`):
    - `ALTER TABLE monthly_input_periods ADD COLUMN opening_inventory JSONB NOT NULL DEFAULT '{}'::jsonb` — per-period per-product opening balance
    - Index: `CREATE INDEX idx_monthly_input_periods_tenant_period_opening_inventory ON monthly_input_periods USING GIN (tenant_id, opening_inventory)` (GIN on JSONB for fast product lookup) — 단, MVP에서는 서비스 레이어에서만 사용 (Epic 5 ledger 진입 시 활성화)
    - COMMENT: 'Story 3.3 placeholder for Epic 5 Story 5-1 (opening inventory auto-carry chain)'
  - [ ] 2.2 — Update `apps/api/core/db_models.py`:
    - `MonthlyInputPeriod.opening_inventory: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)`
  - [ ] 2.3 — Update `apps/api/modules/m2_input/schemas.py`:
    - `MonthlyInputStateResponse`: add `warnings: list[WarningResponse]`, `is_blocked: bool`, `warnings_count: int`, `top_n_severity: int`
    - `MonthlyInputRowUpdate`: schema-level `extra='forbid'` (Story 3.1 base) — `warnings`, `is_blocked` 미정의 → PATCH 시 400 (AC #7)
    - `WarningResponse`: `code: str`, `severity: str`, `message_ko: str`, `details: dict`, `stream: str`, `trace_id: str`, `timestamp: datetime` (ISO-8601 UTC, AD-15)
    - `InventoryProjectionResponse` (optional): `product_id: UUID`, `product_code: str`, `opening_qty: Decimal`, `inbound_qty: Decimal`, `outbound_qty: Decimal`, `closing_qty: Decimal` (frontend echo 용)
  - [ ] 2.4 — No new RLS policy — `monthly_input_periods` already RLS-scoped (Story 3.1)

- [ ] **Task 3 — Service layer: warning aggregate wired into state** (AC: #1, #2, #3, #4, #5, #6, #8)
  - [ ] 3.1 — Update `apps/api/modules/m2_input/services/monthly_input_service.py`:
    - Inject `compute_inventory_projection(rows, opening_inventory)` call → `build_inventory_warnings(projection)` (Task 1.1 + 1.3)
    - Inject `compute_operating_rate(fte, standard_monthly_hours, production_rows)` call → `build_operating_rate_warning(rate)` (Task 1.2 + 1.3)
    - `aggregate_warnings(inventory_warnings, operating_rate_warning)` → mounted on `MonthlyInputStateResponse.warnings`
    - `is_blocked = len(warnings) > 0` (PRD §A11 close-time rule)
    - Opening inventory read: `monthly_input_periods.opening_inventory` (Task 2.1) → if empty, fetch from `previous_period_closing_inventory` (cj-style default = 0 for new tenants; Epic 5 5-1 entry point)
    - `_compute_inventory_projection_for_state` (private) — call ordering: build_inventory_projection → build_inventory_warnings → compute_operating_rate → build_operating_rate_warning → aggregate_warnings
  - [ ] 3.2 — Add 2 typed exceptions to `apps/api/modules/m2_input/services/__init__.py`:
    - `MonthlyInputWarningsReadOnlyError` (400) — direct PATCH attempt on `warnings`/`is_blocked` field (AC #7 server-side defense)
    - `MonthlyInputInventoryProjectionError` (422) — invalid qty / product_id in inventory projection (defensive, schema-level invalid)
  - [ ] 3.3 — Update `save_row` (CR 1.1 idempotent no-op):
    - `warnings` 필드는 save_row 응답에 포함 (재계산된 최신)
    - `is_blocked` 도 같이 갱신
    - 이미 발생한 row라서 no-op이어도 `warnings`는 항상 재계산 (다른 row가 만든 warning이 있을 수 있음)
  - [ ] 3.4 — Update `get_state` 응답: `warnings`, `is_blocked`, `warnings_count`, `top_n_severity` 4 fields 항상 포함 (AC #8 정렬 보장)

- [ ] **Task 4 — Handler layer: state response + 2 typed exceptions** (AC: #1, #2, #3, #4, #5, #7, #8)
  - [ ] 4.1 — Update `apps/api/modules/m2_input/handlers.py`:
    - `get_state` 응답: `MonthlyInputStateResponse` + `warnings`/`is_blocked`/`warnings_count`/`top_n_severity` (Task 2.3 schema)
    - `save_row` 응답: 동일 + 재계산된 `warnings` (CR 1.1 idempotent no-op은 `quantity/amount` 동일 시 200 OK + 최신 warnings)
    - `set_mode` 응답: warnings 재계산 (mode toggle 시 fte/projection 영향)
    - 2 new exception handlers → AD-15 envelope:
      - `MonthlyInputWarningsReadOnlyError` → 400 INVALID_PAYLOAD
      - `MonthlyInputInventoryProjectionError` → 422 INVENTORY_PROJECTION_INVALID
  - [ ] 4.2 — Update `apps/api/main.py` — register 2 new exception handlers
  - [ ] 4.3 — Korean message formatters: `_format_inventory_warning_ko` + `_format_operating_rate_ko` (Task 1.3 helpers) — handler에서 import하여 사용

- [ ] **Task 5 — TS mirror parity (Epic 2 W4 회귀)** (AC: #9)
  - [ ] 5.1 — Create `apps/web/lib/l2-input-warnings.ts`:
    - Export `WARNING_CODES: readonly ["NEGATIVE_CLOSING_INVENTORY", "OVERCAPACITY_OPERATING_RATE"]`
    - Export `INVENTORY_PRODUCT_TYPES: readonly ["material", "semi_product", "product"]`
    - Export `OPERATING_RATE_LIMIT_PCT: 100`
    - Export `DEFAULT_UNIT_TIME_HOURS: 1.0`
    - Export `SEVERITY_ORDER: {error: 0, warning: 1, info: 2}`
    - Export `buildInventoryProjection(rows, openingBalance): InventoryMovement[]` — TS mirror of `compute_inventory_projection`
    - Export `computeOperatingRate(available, required): Decimal` — ROUND_HALF_EVEN (`Decimal.ROUND_HALF_EVEN` from `decimal.js`)
    - Export `buildInventoryWarnings(projection): Warning[]`
    - Export `buildOperatingRateWarning(rate, ...): Warning | null`
    - Export `aggregateWarnings(invWarn, opWarn): Warning[]` — sort by (severity ASC, closing_qty ASC)
    - Export `formatInventoryWarningKo(product, projection): string` — Korean message
    - Export `formatOperatingRateKo(fte, hours, required, rate): string` — Korean message
  - [ ] 5.2 — Extend `tests/integration/test_m2_input_label_consistency.py` with 5 new cases (AC #9):
    - `test_warning_codes_match_python`: WARNING_CODES ↔ Python `WarningCode` enum
    - `test_warning_severity_order_matches_python`: SEVERITY_ORDER dict parity
    - `test_inventory_projection_opening_inbound_outbound_matches_python`: AC #1 fixtures (opening=100, outbound=130 → closing=-30)
    - `test_operating_rate_110_percent_matches_python`: AC #3 fixtures (110% → OVERCAPACITY warning)
    - `test_aggregate_warnings_independent_resolution_matches_python`: AC #5 step-by-step verification
  - [ ] 5.3 — Update `apps/web/lib/m2-input-completion.ts` (Story 3.1) — no enum changes (warnings are not in stream set); verify no drift in `STREAM_LABELS_KO`

- [ ] **Task 6 — Capability matrix documentation update** (AC: #6, 운전자 가이드)
  - [ ] 6.1 — Update `docs/capability-matrix.md` (Epic 1+2+3 통합 매트릭스) with footnote:
    - "재고 음수·조업도 초과 실시간 경고 (Story 3.3) — 기존 capability 일부 (`MONTHLY_INPUT_SALES`/`PURCHASES`/`PRODUCTION`/`LABOR`). 추가 capability 부재. PRD §A11 입력 시 경고 + Epic 4 first_calc close-time 차단."
    - "음수재고 detection은 M2 inline projection (Epic 5 ledger 진입 전). Epic 5 Story 5-1 (auto-carry) + 5-2 (append-only ledger) 진입 시 ledger-backed read로 승격."
  - [ ] 6.2 — `tests/integration/test_capability_consistency.py` — **확장 없음** (capability set unchanged)

- [ ] **Task 7 — Tests (service + integration + cross-language + API)** (AC: #1-9)
  - [ ] 7.1 — `tests/services/test_m2_input_inventory_projection.py` (Task 1.5 16+ cases)
  - [ ] 7.2 — `tests/services/test_m2_input_operating_rate.py` (Task 1.6 12+ cases)
  - [ ] 7.3 — `tests/services/test_m2_input_warnings.py` (Task 1.7 8+ cases)
  - [ ] 7.4 — Extend `tests/services/test_m2_input_completion.py` with 2 cases:
    - `test_state_warnings_empty_for_clean_period`: no negative, no overcapacity → 0
    - `test_state_warnings_count_reflects_aggregate`: 2 inventory + 1 overcapacity → 3
  - [ ] 7.5 — Extend `tests/services/test_m2_input_fte.py` with 2 cases:
    - `test_operating_rate_uses_fte_display_hours`: fte=1.09, hours=228 → available=248.5
    - `test_operating_rate_under_capacity_with_default_unit_time`: 100h / 248.5h → 40.2% (no warning)
  - [ ] 7.6 — Extend `tests/integration/test_m2_input_label_consistency.py` (Task 5.2 5 cases)
  - [ ] 7.7 — Extend `tests/api/test_monthly_input.py` (DB-backed skipif + 6 new reference tests):
    - `test_save_row_sales_triggers_negative_inventory_warning` (AC #1)
    - `test_save_row_sales_clear_warning_on_qty_decrease` (AC #2)
    - `test_save_row_production_triggers_overcapacity_warning` (AC #3)
    - `test_save_row_production_clear_warning_on_qty_decrease` (AC #4)
    - `test_save_row_independent_warning_resolution` (AC #5)
    - `test_patch_warnings_field_rejected_400_read_only` (AC #7 server-side defense)
  - [ ] 7.8 — Verify zero regression on Story 3.1 + 3.2 tests: `pytest tests/services/test_m2_input_completion.py tests/services/test_m2_input_fte.py tests/services/test_m2_input_labor_conversion.py tests/integration/test_m2_input_label_consistency.py -v` — all green post-Story-3.3 changes

- [ ] **Task 8 — Docs** (AC: 전체 운영자/개발자 onboarding)
  - [ ] 8.1 — Create `docs/monthly-input-warnings.md` — 경고 시스템 operator/dev guide:
    - 2 warning codes (NEGATIVE_CLOSING_INVENTORY + OVERCAPACITY_OPERATING_RATE) 의미 + PRD §V3·V5·A11 매핑
    - M2 inline projection 한계 (Epic 5 ledger 진입 전) + `TODO(epic-5)` marker 설명
    - 입력 시 warning (200 OK + 진행 허용) vs 마감 시 차단 (Epic 4 first_calc hook) — PRD §A11 정책
    - opening_inventory = 0 (MVP) / Epic 5 5-1로 auto-carry (다음 phase)
    - Korean message format 예시 (PRD §V3·V5 friendly)
    - top_n_severity 정렬 알고리즘 (severity ASC → closing_qty ASC)
  - [ ] 8.2 — Update `docs/monthly-input.md` (Story 3.1) — §재고/조업도 경고 단락 추가
  - [ ] 8.3 — Update `docs/monthly-input-fte.md` (Story 3.2) — §조업도 계산 (operating rate) 단락 추가
  - [ ] 8.4 — Update `docs/capability-matrix.md` (Task 6.1 footnote)
  - [ ] 8.5 — Update `docs/README.md` — Epic 3 navigation entry

## Dev Notes

### Architecture binds

- **AD-1 (헥사고날)** — `packages/services/m2_input/{inventory_projection,operating_rate,warnings}.py` = pure (no DB, no clock, AD-5). `apps/api/modules/m2_input/services/monthly_input_service.py` = service layer (existing, extended). handlers unchanged (5 routes backward compatible) + 2 new typed exception handlers.
- **AD-5 (purity)** — 모든 helper stdlib + Decimal only. NO DB, NO clock, NO random. `Decimal.ROUND_HALF_EVEN` 명시.
- **AD-8 (monetary)** — qty = `Decimal` (`NUMERIC(18,4)` PRD §6.1). KRW는 본 스펙 범위 외 (no new KRW columns).
- **AD-13 (Input-collection adapter)** — `MonthInputAdapter` (Epic 4 first_calc 호출) 진입점. Story 3.3 ships the warning kernel (inventory_projection + operating_rate + aggregate_warnings); Epic 4 Story 4-1 wraps it for V3·V5 verification.
- **AD-15 (cross-language)** — snake_case Python ↔ camelCase TS; `WarningCode` enum = `"NEGATIVE_CLOSING_INVENTORY" | "OVERCAPACITY_OPERATING_RATE"`; banker's rounding in BOTH languages (TS Decimal.js ROUND_HALF_EVEN — Story 3.1 format_fte_headcount 패턴); ISO-8601 UTC TIMESTAMPTZ for warning.timestamp; `{code, message_ko, details, trace_id}` envelope consistent.
- **AD-22 (append-only-leaning)** — `monthly_input_rows` IS user-input (mutable, DELETE 허용 — PRD §8.M2). `inventory_ledger` (Epic 5) WILL be append-only. 두 개념 혼동 주의: 본 스펙은 inline projection (`monthly_input_periods.opening_inventory JSONB`), NOT ledger.
- **AD-23 (4-namespace)** — `monthly_input_periods.opening_inventory` JSONB는 payload-only (no namespace change). Existing `monthly_input_rows` UNIQUE 제약 변경 없음.

### Story 3.1 → 3.2 → 3.3 의존성

| Story 산출물 | Story 3.3 사용처 |
|---|---|
| `monthly_input_rows` (qty, product_id, stream, day_no) | 그대로 보존. Story 3.3는 projection 계산 source |
| `monthly_input_periods` (period_key, mode, baseline_revision, locked_by_calculation) | `opening_inventory JSONB` 1 컬럼 추가 (Task 2.1) |
| `MonthlyInputStateResponse` (Story 3.1) | 확장: `warnings[]`, `is_blocked`, `warnings_count`, `top_n_severity` |
| `compute_labor_fte` (Story 3.1) + `compute_fte_wage_for_daily` (Story 3.2) | operating_rate 계산 시 `total_fte_headcount` source로 활용 |
| `format_fte_headcount` (Story 3.1) | ROUND_HALF_EVEN 검증 reference (Task 1.6 12 cases) |
| `tenant_settings.payroll.*` (Story 3.2) | `standard_monthly_hours` (default 228) → operating_rate divisor |
| `Completion` (Story 3.1) | 그대로. `is_complete` ≠ `is_blocked`. Completion = row 존재, Block = warning 존재 |
| `Capability.MONTHLY_INPUT_*` | 변경 없음 (AC #6) |

### Epic 의존성 (Epic 1+2+3 자산)

| 자산 | 출처 | 본 스펙 사용처 |
|---|---|---|
| `compute_completion()` pure function | Story 1.2 / 1.3 | 패턴: `aggregate_warnings` 동일 구조 |
| `audit-first + idempotent no-op` | CR 1.1 lesson | save_row 응답의 warnings는 항상 재계산 (다른 row 영향 받음) |
| `tenant_settings.payroll.*` JSONB | Story 3.2 | standard_monthly_hours source (이미 DONE) |
| `MonthlyInputRowResponse` (Story 3.1) | Story 3.1 | projection의 input (qty, product_id) |
| Epic 2 W4 (TS mirror regex 검증) | Epic 2 회고 | Task 5.2 5 cases 추가 |
| `docs/capability-matrix.md` | Epic 1+2+3 회고 A4 | footnote 추가 (Task 6.1) |
| `format_fte_headcount` (Story 3.1) | Story 3.1 | ROUND_HALF_EVEN reference (Task 1.6) |
| Epic 5 ledger stub marker (`TODO(epic-5)`) | Story 2.3 (product_references) | inventory_projection.py 동일 패턴 |

### Capability matrix (변경 없음)

| Capability | manufacturing | service | manufacturing_service | manufacturing_service_other |
|---|---|---|---|---|
| `MONTHLY_INPUT_SALES` | ✅ | ✅ | ✅ | ✅ |
| `MONTHLY_INPUT_PURCHASES` | ✅ | ✅ | ✅ | ✅ |
| `MONTHLY_INPUT_PRODUCTION` | ✅ | ❌ | ✅ | ✅ |
| `MONTHLY_INPUT_LABOR` | ✅ | ✅ | ✅ | ✅ |

(Warning 시스템 = 위 4 capability의 일부; 별도 capability 없음. AC #6 명시.)

### 데이터 흐름 (Story 3.3 추가)

```
[Web m2-input 페이지]
   ↓ GET /api/v2/monthly-input/{period}/state
[m2_input.handlers.get_state]
   ↓ service: get_or_create_period → list rows
   ↓ _load_payroll_settings (Story 3.2) ← standard_monthly_hours
   ↓ _compute_fte_display (Story 3.2) ← total_fte_headcount
   ↓ _compute_inventory_projection_for_state (NEW)
       ├─ build_inventory_projection(rows, opening_inventory) → InventoryMovement[]
       ├─ build_inventory_warnings(projection) → Warning[]
       ├─ compute_operating_rate(fte, hours, production_rows) → Decimal
       ├─ build_operating_rate_warning(rate) → Warning | null
       └─ aggregate_warnings(inv_warn, op_warn) → Warning[] (sorted)
   → MonthlyInputStateResponse {completion, is_complete, missing, capability_mask,
                                fte_display (Story 3.2), payroll_settings (Story 3.2),
                                warnings: Warning[], is_blocked: bool, warnings_count: int,
                                top_n_severity: int}

[사용자 row 저장]
   ↓ POST /api/v2/monthly-input/{period}/rows
[m2_input.handlers.save_row]
   ↓ _validate_labor_shape (Story 3.2) — labor stream
   ↓ SELECT FOR UPDATE monthly_input_rows natural key
   ↓ idempotent no-op? → 200 + no audit (row unchanged) BUT warnings 여전히 재계산
   ↓ emit_audit(action='monthly_input_row_saved', flush=True) [if not no-op]
   ↓ INSERT/UPDATE row
   ↓ _compute_inventory_projection_for_state (recompute warnings)
   ↓ return updated state with warnings
```

### `monthly_input_periods.opening_inventory` JSONB schema (Story 3.3 신규)

```jsonc
{
  "products": [
    {"product_id": "...uuid...", "product_code": "PRD-0001", "qty": 100.0},
    {"product_id": "...uuid...", "product_code": "PRD-0002", "qty": 50.0}
  ]
}
```

MVP: column exists, default `{}`. 시드 데이터 없음. 운영자가 첫 달 시작 시 수동 set (Story 0.5 plumbing 후속 — M1 settings wizard pattern). Epic 5 5-1 진입 시 auto-carry chain (`prev_period_closing_inventory → current_period_opening_inventory`).

### Inventory projection algorithm (Story 3.3 신규)

```python
# Per-product aggregation (service layer)
def compute_closing_inventory(opening, inbound, outbound):
    return (opening + inbound - outbound).quantize(Decimal("0.0001"), ROUND_HALF_EVEN)

# Stream mapping (PRD §6.2 수불 공식)
STREAM_TO_MOVEMENT = {
    "sales": "outbound",          # 판매 = 출고
    "purchases": "inbound",       # 구매 = 매입 (material/merchandise)
    "production": "inbound_product",  # 생산 = 제품 입고 (output product_qty만)
}

# Excluded from inventory projection
INVENTORY_PRODUCT_TYPES = {"material", "semi_product", "product"}
EXCLUDED_TYPES = {"service", "merchandise"}  # merchandise는 Epic 5에서 별도 처리
```

**MVP 한계 (Epic 5 진입 전)**:
- material consumption (production 시 원부재료 소모) 추적 안 함 — production output product_qty만 inbound
- cumulative stock across months: the same SIDE 계산 (current period closing - opening = net movement). 이전 period closing → current period opening은 `monthly_input_periods.opening_inventory`로 수동 set 또는 Epic 5 5-1 auto-carry.

### Operating rate calculation (Story 3.3 신규)

```python
# PRD §6.1 (2) 조업도 체인
total_available_hours = total_fte_headcount × standard_monthly_hours
production_required_hours = Σ(production_rows.qty × unit_time_hours)
operating_rate_pct = (production_required_hours / total_available_hours) × 100

# 한도 초과 (PRD §V5)
operating_rate_pct > 100 → OVERCAPACITY_OPERATING_RATE warning
```

**MVP default**: `unit_time_hours = 1.0` per product. Story 2.1 BOM schema에 컬럼 부재. Epic 7 BEP 슬라이더 (Story 7-2) 정밀화 후속.

### Korean message format (AD-11 cross-language)

```python
# inventory warning (PRD §V3 friendly)
"PRD-0001(달걀) 기말재고 -30 → 음수 경고"

# operating rate warning (PRD §V5 friendly)
"총작업가능시간 248.5h(1.09 × 228) < 생산요구시간 250h → 100.6% (한도 초과)"
```

PRD §A11 "오류의 가시화" 정책 — 사용자 친화적 한국어 메시지. 영어 fallback 없음 (ko-KR MVP, Epic 1 architecture).

### [마감] 버튼 게이트 (Epic 4 first_calc 진입점)

Story 3.3 ships:
- `state.is_blocked: bool` 필드 (= `len(warnings) > 0`)
- TS mirror for frontend `[마감]` button enable/disable
- Korean message in `state.warnings[].message_ko`

Epic 4 Story 4-1 (pure cost engine) 진입 시:
- `POST /api/v1/calc` first_calc 호출 전 server-side `validate_preview_state(state)` — `is_blocked=true` → **422 INPUT_BLOCKED** typed error
- UI는 사용자 친화 토스트: "음수재고/조업도 초과 3건 — 먼저 입력 값을 수정해주세요"
- 이 server-side enforcement는 Story 3.3 범위 외 (PRD §A11 close-time rule deliverable = Epic 4)

### PIPA / PII / Logging

- `daily_wage_krw` (Story 3.2), `warnings[].message_ko` (PII는 아니지만 사용자 데이터)는 structlog 도입 시 redaction 대상. 본 스펙은 `docs/monthly-input-warnings.md`에 경고 추가.
- `trace_id` (Story 1.1 pattern) — 모든 warning `details.trace_id` 자동 부여.

### Anti-patterns to avoid (CR lessons)

- **Float for qty** — AD-8 위반. 모든 qty = `Decimal` + `ROUND_HALF_EVEN`.
- **TS Math.round for operating_rate_pct** — half-away-from-zero ≠ ROUND_HALF_EVEN. TS mirror must implement `roundHalfEven` explicitly (Story 3.2 pattern).
- **Storing warnings in DB** — AD-13 위반. Warnings are derived on read only (computed on every state call).
- **Hard-fail on warning during save_row** — PRD §A11 위반. 입력 시 경고(진행 허용) 정책. save_row 항상 200 OK + warnings[]. Hard-fail only at Epic 4 first_calc.
- **Race between multiple row saves + warning recompute** — service layer는 single transaction 안에서 warnings 재계산 (CR 1.1 SELECT FOR UPDATE 동일 row 의존성만 격리, 다른 row는 다른 row의 PATCH 영향 반영). Multiple concurrent saves on different rows → 결과 일관성 OK (마지막 commit 시점의 state.warnings = 모든 visible row의 union).
- **Service-only 테넌트 production stream 0 rows** — 운영률 분모 = fte × hours (FTE 있으면 분모 > 0). 분자 = 0 (production rows 0). operating_rate = 0% → no warning. 정상.

## Open Questions (cj-style defaults)

| # | 질문 | 디폴트 | 변경 시 영향 |
|---|---|---|---|
| OQ1 | Inventory projection source — M2 inline vs Epic 5 ledger JOIN? | **M2 inline projection** (current) — Epic 5 5-1 (auto-carry) + 5-2 (append-only ledger) 진입 시 ledger-backed read로 승격. `TODO(epic-5)` 마커 명시 | 즉시 Epic 5 ledger 진입 시 inline projection 제거 + service layer 교체 |
| OQ2 | Opening inventory source — 자동 (이전 period) vs 수동 (테넌트 UI) vs 둘 다? | **MVP: `monthly_input_periods.opening_inventory` JSONB column + default `{}`** + service layer fallback 0. Epic 5 5-1 auto-carry chain 후속. 운영자 UI 노출 = Story 0.5 plumbing | 자동만 선호 시 service layer 단순화 + 5-1 즉시 필요 |
| OQ3 | Operating rate unit_time_hours — 제품별 단위공수 source? | **MVP default 1.0h per product** — Story 2.1 BOM schema에 컬럼 부재. Epic 7 BEP 슬라이더 후속 정밀화 | BOM/Product 스키마 확장 시 products.unit_time_hours 컬럼 추가 (Epic 7) |
| OQ4 | Top-N severity 노출 — 1건만 vs 3건 vs 전체? | **3건 (warnings list 전체) + top_n_severity: 1 (가장 심각한 1건)** — UI는 top_n_severity 1건 우선 노란 알림 + "전체 N건 보기" expander | 1건만 선호 시 UX 통제력 ↓ (사용자 모름) |
| OQ5 | 입고/출고 stream 매핑 — sales=outbound, purchases=inbound, production=inbound? | **service 입고 = (sales_view)**: sales + purchases + production 모두 적용. 단, production input material consumption 추적 = MVP 외 (Epic 5 ledger) | material consumption 추적 즉시 필요 시 Epic 5 5-2 우선 개발 |
| OQ6 | Inventory projection을 monthly_input 공유 캐시 vs 매번 재계산? | **매번 재계산 (pure function)** — NFR9 ≤ 5s 응답. 31 products × 6 streams = 186 rows worst case → < 100ms compute. 캐시 무필요 (row 변경 시 invalidation 복잡) | 캐시 선호 시 Story 0.5 plumbing + M2 shared cache layer 추가 |
| OQ7 | Warning 코드 확장성 — 2개로 한정 (NEGATIVE_INVENTORY + OVERCAPACITY) vs 4+ 확장? | **2개로 한정** (PRD §V3 + §V5). V4 (4요소 분해), V6 (합계 대사) 등은 Epic 4 calc engine 진입점으로 | 4+ 즉시 필요 시 enum 확장 + sort 알고리즘 복잡화 |
| OQ8 | Service-only 테넌트 (production rows 0) 의 operating_rate 검사? | **production_required_hours > 0 일 때만 분모 검사** (PRD §V5 fire 조건). production_required_hours=0 → 검사 skip (operating_rate=0% 무경고) | 모든 tenant 무조건 검사 선호 시 service tenant operating_rate=0% noise |

## Definition of Done

- [ ] AC #1-9 모두 pass (backend test + cross-language parity + AC #9 cross-language)
- [ ] Task 1-8 모든 subtask check
- [ ] `tests/services/test_m2_input_inventory_projection.py` 16+ cases green
- [ ] `tests/services/test_m2_input_operating_rate.py` 12+ cases green
- [ ] `tests/services/test_m2_input_warnings.py` 8+ cases green
- [ ] `tests/integration/test_m2_input_label_consistency.py` +5 cases green (TS mirror parity)
- [ ] Story 3.1 + 3.2 regression 0 (의존 pure functions unaffected)
- [ ] `docs/monthly-input-warnings.md` + `docs/monthly-input.md` §경고 + `docs/monthly-input-fte.md` §조업도 + `docs/capability-matrix.md` footnote + `docs/README.md` navigation
- [ ] Alembic 0011 적용 (down_revision=0010)
- [ ] 2 typed exceptions → AD-15 envelope 매핑
- [ ] 4 deferral 명시: (a) opening inventory auto-carry (Epic 5 5-1), (b) inventory ledger inline projection (Epic 5 5-2), (c) BOM/Product unit_time_hours 정밀화 (Epic 7 BEP), (d) Epic 4 first_calc close-time enforcement
- [ ] sprint-status.yaml: `3-3-negative-inventory-overcapacity-real-time-warning` → ready-for-dev
- [ ] Atomic commit (Story 3.2의 `d5d7da9` baseline에서)

## References

- Epic 3: Monthly Input Capture — `_bmad-output/planning-artifacts/epics.md` lines 707-756
- F2.3 (음수재고/조업도 초과 입력 즉시 경고) — PRD §6.2 + §8.M2
- F4.2 (음수 기말 감지 + 마감 진입 차단) — PRD §6.2 (4)
- §3 A11 (오류의 가시화) — PRD §3 lines 244-247
- §6.1 (2) (조업도 체인) — PRD §6.1 lines 305-316
- §6.2 (수불부) — PRD §6.2 lines 348-356
- §11 V3 (음수재고 검증) — PRD §11 lines 533
- §11 V5 (조업도 검증) — PRD §11 lines 535
- § 운영 원칙 (입력 시 경고 → 마감 시 차단) — PRD §11 line 540
- AD-13 MonthInputAdapter — `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md` lines 118-122
- AD-22 (append-only-leaning) — lines 172-177
- AD-23 (4-namespace) — lines 178-182
- Story 3.1 read-only state hook surface — `_bmad-output/implementation-artifacts/3-1-six-stream-monthly-input-ui-month-total-default.md`
- Story 3.2 FTE precision + payroll override — `_bmad-output/implementation-artifacts/3-2-fte-conversion-daily-labor.md`
- Epic 1 retro C1 #3 PII redaction defer — `_bmad-output/implementation-artifacts/epic-1-retro-2026-08-01.md` §C1
- Epic 2 retro W4 TS mirror regex — `_bmad-output/implementation-artifacts/epic-2-retro-2026-08-01.md` §W4
- CR 1.1 lesson (audit-first + idempotent no-op) — `_bmad-output/implementation-artifacts/.review/story-1-1.diff` + memory `cr-1-1-lessons`
- Epic 5 ledger stub marker pattern — `_bmad-output/implementation-artifacts/2-3-item-type-change-integrity-guard.md` (product_references.py `LEDGER_REFERENCE_QUERY_STUB`)

## Dev Agent Record

### Implementation Plan (draft)

Story 3.3 — Negative Inventory & Overcapacity Real-Time Warning. 8 tasks /
60+ subtasks. Backend-core priority (T1 → T2 → T3 → T4 → T5 → T6 → T7 →
T8). Frontend warning UI plumbing은 Story 0.5 진입 후속 (5 deferrals from
Story 3.1 carry over).

Layered architecture preserved (AD-1 / AD-11):
1. **Pure helpers** — `packages/services/m2_input/{inventory_projection,operating_rate,warnings}.py` (T1). stdlib-only, Decimal-based, ROUND_HALF_EVEN explicit. `TODO(epic-5)` marker 명시.
2. **DB schema** — Alembic 0011 + ORM (T2)
   - 1 JSONB column `monthly_input_periods.opening_inventory` (default `{}`)
   - `MonthlyInputStateResponse` 확장: `warnings[]`, `is_blocked`, `warnings_count`, `top_n_severity`
3. **Service layer** — `MonthlyInputService` extension (T3)
   - `_compute_inventory_projection_for_state` (warning aggregate dispatcher)
   - 2 new typed exceptions (AD-15 §4 envelope compatible)
   - `save_row`/`get_state`/`set_mode` 응답에 warnings 4 fields 노출
4. **Handler layer** — `apps/api/modules/m2_input/handlers.py` (T4)
   - 기존 5 routes 응답 warnings 포함 (backward compatible)
   - 2 new exception handlers in `main.py`
5. **TS mirror** — `apps/web/lib/l2-input-warnings.ts` (T5)
   - `decimal.js` ROUND_HALF_EVEN (matches Python `Decimal.quantize`)
   - camelCase ↔ snake_case boundary discipline
6. **Capability matrix** — `docs/capability-matrix.md` (T6) — footnote 추가 (capability unchanged)
7. **Tests** — pure + cross-lang + DB-skipif (T7)
   - 16 inventory_projection cases (T1.5)
   - 12 operating_rate cases (T1.6)
   - 8 warnings cases (T1.7)
   - 2 fte_completion cases (T7.4)
   - 2 fte_display cases (T7.5)
   - 5 cross-language cases via Node v24 (T7.6)
   - 6 DB-backed skipif cases (T7.7)
   - Story 3.1 + 3.2 0 regression (T7.8)
8. **Docs** — `docs/monthly-input-warnings.md` (new) + monthly-input.md §경고 + monthly-input-fte.md §조업도 + capability-matrix.md footnote + README.md (T8)

### Status

**READY-FOR-DEV 2026-08-01** — comprehensive spec with 9 ACs, 8 tasks
(60+ subtasks), 6 explicit deferrals (a) opening inventory auto-carry
(Epic 5 5-1), (b) inventory ledger inline projection (Epic 5 5-2),
(c) BOM/Product unit_time_hours 정밀화 (Epic 7 BEP), (d) Epic 4 first_calc
close-time enforcement, (e) 운영자 UI for opening inventory (Story 0.5
plumbing), (f) PII redaction (Epic 1 회고 C1 #3).
