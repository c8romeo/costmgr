---
baseline_commit: 8eb7dca
---

# Story 3.2: FTE Conversion & Daily Labor Precision

Status: ready-for-dev

> Epic 3 두 번째 — 일용직 FTE 환산을 정밀 계산 + pay_type 분기 + 인건비 breakdown까지 확장.
> Story 3.1의 read-only display hook (`fte_display`)을 **정규 계산** 결과로 채우고,
> `tenant_settings.payroll.*` JSONB override 패턴을 도입하여 테넌트별 payroll 정책을 반영.
> **모듈**: 기존 `m2_input/` 확장 + 신규 `packages/services/m2_input/labor_conversion.py`

<!-- dev-context: Epic 1 retro W6 (company_subblock JSONB 승격) — 본 스펙은 `tenant_settings.payroll` JSONB sub-block 도입.
                    Epic 2 retro W4 (TS mirror regex 검증) — TS mirror parity test 적용.
                    Story 3.1 read-only display hook을 정밀 계산으로 승격 (additive).
                    CR 1.1 audit-first + idempotent no-op은 monthly_input_rows mutation 시 동일 적용.
                    PRD §6.1 인건비 구성 (기본급/시간외/복리후생/상여/퇴직충당금) + pay_type 분기.
                    Action Item A2 (shadcn Tabs 확인) — Story 3.1 close-out에서 defer 결정 완료. -->

## Story

As a **사장님** (small/medium business owner),
I want **"2026-07" [인원] 탭에서 일용직 인원·일수·일급을 입력하면 FTE 환산 인원·환산 임금이 자동 계산되어 비활성 필드로 표시되고, 월급제/일급제 구분과 기본급·시간외·복리후생·상여·퇴직충당금 breakdown까지 한 페이지에서 관리되는 것**,
so that **인건비를 월 기준으로 정규화하는 수고를 덜고, 4대 보험·퇴직충당금·회사부담 임률을 일관 적용하여 인건비 원가 계산의 정확도를 높인다** — PRD §6.1 (인건비 구성) · F2.2 (일용직 FTE 자동 환산) · NFR9 (입력 응답성).

## Acceptance Criteria

1. **Given** I am on the [인원] tab for `period_key="2026-07"` and the tenant is `manufacturing` (제조)
   **When** I save a row with `pay_type="daily"`, `workers=3`, `days_per_worker=8`, `daily_wage_krw=150_000`
   **Then** the state response's `fte_display` (added by Story 3.1, populated by this story) includes:
     - `fte_headcount = 1.09명` (= `3 × 8 / 22`, ROUND_HALF_EVEN, AD-8 Decimal precision)
     - `fte_wage_krw = 2,725,000원` (= `1.09 × 2_500_000`, ROUND_HALF_EVEN)
     - `pay_type = "daily"` echoed back
   **And** these two fields are returned in the response but NEVER written to `monthly_input_rows` (FTE는 derived on read, AD-13 — `MonthInputAdapter` normalizes, not the row)
   **And** the row body in `monthly_input_rows` carries ONLY the inputs: `workers=3, days_per_worker=8, daily_wage_krw=150_000` — no fte_* columns
   **And** `tests/services/test_m2_input_completion.py` `test_format_fte_3_workers_8_days_22_workdays` already passes with `Decimal("1.09")` — Story 3.2 verifies the integration wiring (service + handler) extends this without breaking the pure function

2. **Given** I am on the [인원] tab for the same period
   **When** I save a row with `pay_type="monthly"`, `workers=2`, `monthly_salary_basis_krw_override=3_000_000`, `bonus_krw=500_000`, `overtime_krw=200_000`, `welfare_krw=100_000`, `retirement_reserve_krw=150_000`, `company_burden_rate=0.115` (4대보험·퇴직 회사부담분 비율)
   **Then** `fte_headcount = 2.00명` (월급제는 이미 정규화 — 일용직 환산 미적용)
   **And** `fte_wage_krw = 2 × (3_000_000 + 200_000 + 100_000 + 500_000) + 150_000 × 0.115` rounded to integer KRW
     = `2 × 3_800_000 + 17_250` = `7_600_000 + 17_250` = `7_617_250원`
   **And** the breakdown fields (monthly_salary_basis / bonus / overtime / welfare / retirement_reserve / company_burden_rate) are persisted on `monthly_input_rows` (new columns, see Task 2.1 Alembic) so the breakdown is recoverable on read
   **And** `pay_type="monthly"` + `days_per_worker=0` is the canonical form (days_per_worker is daily-only input; service validates this in `_validate_labor_shape`)

3. **Given** the tenant has `tenant_settings.payroll.*` JSONB sub-block set:
     - `monthly_salary_basis_krw: 3_500_000`
     - `workdays_in_month: 20`
     - `standard_monthly_hours: 176`
     - `company_burden_rate: 0.115`
   **When** the [인원] tab computes FTE
   **Then** the override values are used in lieu of PRD defaults (2_500_000 / 22 / 228 / 0.115)
   **And** `tests/services/test_m2_input_fte.py` includes a new case `test_tenant_settings_override_takes_precedence` verifying the override path
   **And** if any of the four payroll.* keys is missing, the PRD default is used **per-field** (not all-or-nothing) — partial override semantics
   **And** the override is loaded **once per request** in `_load_payroll_settings(tenant_id)` and memoized within the request scope — no per-row DB hit

4. **Given** I am on the [인원] tab in 일자별 mode (`mode='daily'`)
   **When** I save `day_no=1..31` rows each carrying `(workers, days_per_worker, daily_wage_krw)` per-day labor cells
   **Then** the rolled-up month-total `fte_display` is the **sum** (not average) of the per-day FTE values:
     - `fte_headcount_total = Σ(day_no=1..31) format_fte_headcount(workers_day, days_per_worker_day, 22)`
     - `fte_wage_krw_total = Σ fte_wage_krw_day`
   **And** if `mode='month_total'` (Story 3.1 default), `fte_display` is computed from the single month-total row directly (one read, no rollup)
   **And** the API contract: `MonthlyInputStateResponse.fte_display` shape is `{pay_type, fte_headcount, fte_wage_krw, breakdown?: {...}, source_rows: int}` — `source_rows` makes the daily-rollup vs month-total-mode visible to the frontend (and to Epic 4 calc engine consumers)

5. **Given** I am on the [인원] tab and a row has been saved
   **When** the UI renders the FTE fields
   **Then** `fte_headcount` and `fte_wage_krw` are displayed in **disabled** inputs with `tabindex="-1"` and the visual cue (greyed-out background, `readonly` attribute) — per Story 3.1 AC #5
   **And** a `data-testid="fte-readonly"` attribute is set for frontend test selectors (Story 0.5 plumbing gate)
   **And** manual edit attempts via `PATCH /rows/{row_id}` with non-null `fte_headcount` or `fte_wage_krw` fields are rejected with **400 INVALID_PAYLOAD** + `details={field: "fte_headcount", reason: "computed field; not user-editable"}` (server-side defense-in-depth — UI already prevents UI-side edit, but API contract enforces)

6. **Given** the [인원] tab has saved `pay_type="daily"` rows totaling `fte_headcount >= 1.0` AND the tenant is `service` industry (no manufacturing capability — production tab hidden)
   **When** `POST /api/v2/monthly-input/{period_key}/state` returns
   **Then** `MonthlyInputStateResponse.fte_display` is populated the same way as for `manufacturing` tenants — FTE is **industry-agnostic** (PRD §6.1 applies to both)
   **And** no new `Capability` entry is needed — `MONTHLY_INPUT_LABOR` (existing from Story 3.1) gates the labor stream for all 4 industries; FTE precision is part of that gate, not a new one
   **And** `tests/integration/test_capability_consistency.py` is **NOT** extended (capability matrix unchanged — payroll precision is a calculation, not a capability)
   **And** `docs/capability-matrix.md` adds a footnote: "FTE precision (Story 3.2) is part of `MONTHLY_INPUT_LABOR`, not a separate capability"

## Tasks / Subtasks

- [ ] **Task 1 — Pure-Python labor conversion helpers** (AC: #1, #2, #3, #4)
  - [ ] 1.1 — Create `packages/services/m2_input/labor_conversion.py` (stdlib-only, AD-1/AD-5):
    - `PayType: str = Enum("monthly", "daily")` (AD-15 snake_case)
    - `class PayrollSettings(NamedTuple)`: `monthly_salary_basis_krw`, `workdays_in_month`, `standard_monthly_hours`, `company_burden_rate`. Defaults from PRD §6.1.
    - `DEFAULT_PAYROLL: Final[PayrollSettings]` = `PayrollSettings(2_500_000, 22, 228, Decimal("0.115"))`
    - `merge_payroll_settings(override: dict | None, base: PayrollSettings = DEFAULT_PAYROLL) -> PayrollSettings` — partial override semantics, per-field fallback
    - `compute_pay_type_breakdown(...)` — pure aggregator: returns `{base_krw, overtime_krw, welfare_krw, bonus_krw, retirement_burden_krw, total_krw}`. `total_krw = base + overtime + welfare + bonus + retirement_reserve × company_burden_rate`.
    - `compute_fte_for_daily(workers, days_per_worker, payroll) -> Decimal` — wraps `format_fte_headcount` with `payroll.workdays_in_month` injected
    - `compute_fte_for_monthly(workers, payroll) -> Decimal` — returns `Decimal(workers).quantize("0.01", ROUND_HALF_EVEN)` (no 환산)
    - `compute_fte_wage_for_daily(fte, daily_wage_krw, workers, days_per_worker, payroll) -> int` — `(daily_wage × workers × days_per_worker)` direct KRW sum (NOT multiplied by `monthly_salary_basis` — that's only for monthly mode 환산). **CRITICAL: This is different from Story 3.1's `compute_fte_wage_krw`.** Story 3.1 only knew about `monthly_salary_basis_krw` 환산; Story 3.2 adds the direct daily-wage path.
    - `rollup_daily_fte(per_day_fte: list[Decimal], per_day_wage: list[int]) -> tuple[Decimal, int]` — Σ fte + Σ wage for mode='daily'
    - `build_fte_display(pay_type, workers, days_per_worker, daily_wage_krw, monthly_breakdown, payroll, mode, source_rows) -> FteDisplay` — single composition function called by service
  - [ ] 1.2 — Update `packages/services/m2_input/__init__.py` — re-export public API (DRY between stream_completion + labor_conversion)
  - [ ] 1.3 — Tests `tests/services/test_m2_input_labor_conversion.py` (16+ cases):
    - `test_pay_type_monthly_no_conversion`: workers=2, payroll=default → Decimal("2.00")
    - `test_pay_type_daily_with_workers_and_days`: 3×8/22 → Decimal("1.09")
    - `test_pay_type_daily_wage_direct_sum_not_basis_multiplied`: 3명 × 8일 × 150_000 = 3_600_000원 (NOT 1.09 × 2_500_000)
    - `test_pay_type_monthly_breakdown_with_burden_rate`: AC #2 fixture (7_617_250)
    - `test_pay_type_monthly_no_breakdown_uses_basis_only`: 단순 workers=1, monthly_basis=2_500_000 → 2_500_000
    - `test_payroll_override_partial_per_field`: monthly_salary_basis override only → workdays_in_month stays 22
    - `test_payroll_override_all_fields`: 4 keys all set → all used
    - `test_payroll_override_none_uses_defaults`: None → DEFAULT_PAYROLL identity
    - `test_payroll_override_decimal_burden_rate`: company_burden_rate as Decimal("0.115") (TS mirror Decimal)
    - `test_rollup_daily_fte_sum_not_average`: 31 days, sum check
    - `test_build_fte_display_monthly_with_breakdown`: AC #2 shape
    - `test_build_fte_display_daily_with_direct_wage`: AC #1 shape
    - `test_round_half_even_precision_3_27_workers`: workers=3, days=24 → Decimal("3.27") not "3.28"
    - `test_zero_workers_returns_zero_fte`: workers=0 → Decimal("0.00")
    - `test_negative_workers_raises`: -1 → ValueError
    - `test_compute_fte_for_daily_uses_override_workdays`: payroll.workdays_in_month=20 → 3×8/20

- [ ] **Task 2 — DB schema: pay_type + breakdown columns on monthly_input_rows** (AC: #2, #4)
  - [ ] 2.1 — Create `apps/api/alembic/versions/0010_monthly_input_labor_breakdown.py` (revision `0010_...`, down_revision = `0009_monthly_input`):
    - ALTER TABLE monthly_input_rows ADD COLUMN:
      - `pay_type TEXT NULL CHECK (pay_type IS NULL OR pay_type IN ('monthly', 'daily'))` — service-level enforcement; column nullable so non-labor rows unaffected
      - `monthly_salary_basis_krw BIGINT NULL CHECK (monthly_salary_basis_krw IS NULL OR monthly_salary_basis_krw >= 0)` — breakdown input (per-row override)
      - `overtime_krw BIGINT NULL`
      - `welfare_krw BIGINT NULL`
      - `bonus_krw BIGINT NULL`
      - `retirement_reserve_krw BIGINT NULL`
      - `company_burden_rate NUMERIC(5,4) NULL CHECK (company_burden_rate IS NULL OR (company_burden_rate >= 0 AND company_burden_rate <= 1))`
    - No new indexes — existing `idx_monthly_input_rows_tenant_period_stream` covers query patterns
    - No UNIQUE change — natural key (Task 2.3 from Story 3.1) unchanged
  - [ ] 2.2 — Update `apps/api/core/db_models.py` — add the 7 new `Mapped[...]` columns on `MonthlyInputRow`:
    - `Mapped[str | None]` for `pay_type`
    - `Mapped[int | None]` for KRW breakdown (AD-8 BIGINT)
    - `Mapped[Decimal | None]` for `company_burden_rate`
  - [ ] 2.3 — Update `apps/api/modules/m2_input/schemas.py`:
    - `MonthlyInputRowCreate`: add `pay_type: PayType | None`, `monthly_salary_basis_krw: int | None`, `overtime_krw: int | None`, `welfare_krw: int | None`, `bonus_krw: int | None`, `retirement_reserve_krw: int | None`, `company_burden_rate: Decimal | None` (Field ge=0, le=1)
    - `MonthlyInputRowUpdate`: all optional (PATCH semantics preserved)
    - `MonthlyInputRowResponse`: same fields + `source_rows: int` (mode-aware: 1 for month_total, 31 for daily)
    - `FteDisplay` (rename from Story 3.1 stub): `pay_type`, `fte_headcount: Decimal`, `fte_wage_krw: int`, `breakdown: dict[str, int] | None`, `source_rows: int`
    - `PayrollSettingsResponse`: `monthly_salary_basis_krw`, `workdays_in_month`, `standard_monthly_hours`, `company_burden_rate` — exposed in state response so the frontend can echo the override back to the user

- [ ] **Task 3 — Service layer: payroll settings load + fte precision** (AC: #1, #2, #3, #4, #5)
  - [ ] 3.1 — Update `apps/api/modules/m2_input/services/monthly_input_service.py`:
    - Inject `SettingsService` (from `m1_baseline/services/settings_service.py`) for `tenant_settings.payroll.*` lookup
    - Add `_load_payroll_settings(tenant_id: UUID) -> PayrollSettings` — read `tenant_settings.payroll.*` JSONB, merge with `DEFAULT_PAYROLL` (Task 1.1 `merge_payroll_settings`)
    - Replace `_compute_fte_display` (Story 3.1 stub) with `_compute_fte_for_state(rows, payroll, mode) -> FteDisplay`:
      - mode='month_total' → read single labor row, dispatch by `pay_type` (monthly → breakdown path; daily → direct wage path)
      - mode='daily' → read all `day_no=1..31` labor rows, sum
    - `_validate_labor_shape(row: MonthlyInputRowCreate) -> None`:
      - `pay_type='daily'` ⇒ requires `workers>0, days_per_worker>0, daily_wage_krw>0`; `monthly_salary_basis_krw` MUST be None
      - `pay_type='monthly'` ⇒ requires `workers>0, monthly_salary_basis_krw>0`; `days_per_worker` MUST be None (or 0)
      - `pay_type=None` on labor stream ⇒ **400 INVALID_PAYLOAD** (Story 3.1 allowed implicit None; Story 3.2 makes pay_type explicit on labor stream because the computation branches on it)
    - `save_row`: extend payload validation to call `_validate_labor_shape` when `stream='labor'`
    - Idempotent no-op (CR 1.1) — compare full breakdown tuple `(workers, days_per_worker, daily_wage_krw, monthly_salary_basis_krw, overtime_krw, welfare_krw, bonus_krw, retirement_reserve_krw, company_burden_rate, pay_type, memo)` for equality
    - Add `validate_payroll_override(o: dict) -> dict` — public helper for future Story 0.5 plumbing (settings UI)
  - [ ] 3.2 — Add 5 typed exceptions to `apps/api/modules/m2_input/services/__init__.py`:
    - `MonthlyInputInvalidLaborShapeError` (400) — `_validate_labor_shape` violation
    - `MonthlyInputFteReadOnlyError` (400) — direct PATCH attempt on `fte_headcount`/`fte_wage_krw` (AC #5)
    - `MonthlyInputPayrollSettingsInvalidError` (400) — `tenant_settings.payroll.*` value out of range (e.g., `company_burden_rate=1.5`)
    - `MonthlyInputCompanyBurdenRateError` (422) — Schema-level failure (Pydantic validates first; this is the service-side re-check)
    - `MonthlyInputPayTypeMismatchError` (400) — `pay_type='daily'` + `monthly_salary_basis_krw` both set
  - [ ] 3.3 — Update `MonthlyInputStateResponse` to include `payroll_settings: PayrollSettingsResponse` — surfaced to frontend so the user sees what values are in effect (override + defaults merged)
  - [ ] 3.4 — Update handler `apps/api/modules/m2_input/handlers.py`:
    - Add exception handlers for the 5 new typed errors → AD-15 envelope
    - All 5 existing routes unchanged (POST/PATCH/DELETE/POST mode/GET state) — backward compatible
    - PATCH /rows payload schema rejects `fte_headcount` / `fte_wage_krw` fields at Pydantic level (model_config `extra='forbid'` already present from Story 3.1; just verify the two field names are not in the model)

- [ ] **Task 4 — TS mirror parity (Epic 2 W4 회귀)** (AC: #1, #3)
  - [ ] 4.1 — Create `apps/web/lib/l2-input-fte.ts`:
    - Export `PAY_TYPE_VALUES: readonly ["monthly", "daily"]`
    - Export `DEFAULT_PAYROLL: {monthly_salary_basis_krw: 2_500_000, workdays_in_month: 22, standard_monthly_hours: 228, company_burden_rate: 0.115}`
    - Export `mergePayrollSettings(override: Partial<typeof DEFAULT_PAYROLL> | null): typeof DEFAULT_PAYROLL` — partial override, per-field fallback
    - Export `computeFteForDaily(workers, daysPerWorker, workdaysInMonth): string` — banker's rounding (Math.round is half-away-from-zero; implement `roundHalfEven` explicitly) — Story 3.1 already has this pattern in `format_fte_headcount` mirror
    - Export `computeFteWageForDaily(dailyWageKrw, workers, daysPerWorker): number` — direct sum (NOT multiplied by monthly_salary_basis_krw)
    - Export `computeFteForMonthly(workers): string` — `workers.toFixed(2)` with half-even
    - Export `rollupDailyFte(perDay: Array<{fte: string, wage: number}>): {fte: string, wage: number}` — Σ sum
    - Export `buildFteDisplay(...)` — composition function matching Python `build_fte_display`
  - [ ] 4.2 — Extend `tests/integration/test_m2_input_label_consistency.py` with 5 new cases:
    - `test_pay_type_values_match_python`: TS `PAY_TYPE_VALUES` ↔ Python `PayType` enum
    - `test_default_payroll_matches_python`: 4-field equality (banker's rounding tolerance on `company_burden_rate`)
    - `test_compute_fte_for_daily_matches_python`: 3×8/22 → "1.09" (string, not Decimal)
    - `test_compute_fte_wage_for_daily_direct_sum`: 3×8×150_000 → 3_600_000 (NOT 1.09 × 2_500_000)
    - `test_merge_payroll_settings_partial_override`: TS partial override semantics
  - [ ] 4.3 — Update `apps/web/lib/menu-config.ts` — no enum changes (pay_type is not in the stream set); verify no drift

- [ ] **Task 5 — Capability matrix documentation update** (AC: #6)
  - [ ] 5.1 — Update `docs/capability-matrix.md` (Epic 1+2 회고 A4 통합 매트릭스) with footnote:
    - "FTE 정밀 계산 (Story 3.2) — `MONTHLY_INPUT_LABOR` capability의 일부. 추가 capability 부재. PRD §6.1 인건비 구성 (기본급·시간외·복리후생·상여·퇴직충당금) + pay_type 분기."
    - "테넌트별 payroll 정책은 `tenant_settings.payroll.*` JSONB sub-block으로 override (Story 3.2 신규 도입)."
  - [ ] 5.2 — `tests/integration/test_capability_consistency.py` — **확장 없음** (capability set unchanged — AC #6 명시)

- [ ] **Task 6 — Tests (service + integration + cross-language)** (AC: #1, #2, #3, #4, #5)
  - [ ] 6.1 — `tests/services/test_m2_input_labor_conversion.py` (Task 1.3 위 16 cases)
  - [ ] 6.2 — Extend `tests/services/test_m2_input_completion.py` with 3 cases:
    - `test_fte_display_pay_type_monthly_uses_basis`: 1명 × 2_500_000 = 2_500_000
    - `test_fte_display_pay_type_daily_uses_direct_wage`: 3명 × 8일 × 150_000 = 3_600_000
    - `test_fte_display_zero_workers_all_zeros`: workers=0 → fte=Decimal("0.00"), wage=0
  - [ ] 6.3 — Extend `tests/services/test_m2_input_fte.py` with 4 cases:
    - `test_tenant_settings_override_takes_precedence` (AC #3)
    - `test_tenant_settings_override_partial_per_field` (AC #3)
    - `test_payroll_settings_invalid_company_burden_rate`: company_burden_rate=1.5 → 422
    - `test_payroll_settings_decimal_company_burden_rate`: company_burden_rate=Decimal("0.115") (TS mirror)
  - [ ] 6.4 — Extend `tests/integration/test_m2_input_label_consistency.py` (Task 4.2 5 cases)
  - [ ] 6.5 — Extend `tests/api/test_monthly_input.py` (DB-backed skipif + 6 new reference tests):
    - `test_save_row_labor_pay_type_daily_201_with_fte_display`
    - `test_save_row_labor_pay_type_monthly_with_breakdown_201`
    - `test_save_row_labor_pay_type_none_rejected_400` (Story 3.2 변경점)
    - `test_save_row_labor_daily_with_monthly_basis_rejected_400` (AC #1 `pay_type='daily'` ⇒ monthly_basis MUST None)
    - `test_patch_row_fte_headcount_rejected_400` (AC #5 server-side defense)
    - `test_state_response_includes_payroll_settings_echo` (AC #3 task 3.3)
  - [ ] 6.6 — Extend `tests/rls/test_monthly_input_isolation.py` (no RLS change; add 2 reference tests):
    - `test_cross_tenant_labor_breakdown_not_visible`
    - `test_cross_tenant_payroll_settings_not_visible`
  - [ ] 6.7 — Verify zero regression on Story 3.1 tests: `pytest tests/services/test_m2_input_completion.py tests/services/test_m2_input_fte.py tests/integration/test_m2_input_label_consistency.py -v` — all green post-Story-3.2 changes

- [ ] **Task 7 — Docs** (AC: 전체 운영자/개발자 onboarding)
  - [ ] 7.1 — Create `docs/monthly-input-fte.md` — FTE 정밀 계산 operator/dev guide:
    - pay_type='daily' vs 'monthly' 분기 + breakdown 5 field 의미
    - `tenant_settings.payroll.*` JSONB sub-block 구조 + per-field override 의미
    - 730h 시나리오 (총작업시간 / standard_monthly_hours = 3.2명 환산 예시)
    - read-only 표시 가이드 (UI disabled + server-side validation defense-in-depth)
    - Epic 4 MonthInputAdapter 진입점에서 본 모듈의 pure 함수를 호출하는 흐름
    - Deferral: ABC labor pool 배분 (Epic 9 Story 9-2), 4대 보험 자동 계산 (MVP 외), 일자별 labor 시각 입력 (Story 3.1 mode toggle + 후속)
  - [ ] 7.2 — Update `docs/capability-matrix.md` (Task 5.1 footnote)
  - [ ] 7.3 — Update `docs/monthly-input.md` (Story 3.1) — §FTE 환산 단락 확장 (pay_type 분기 + breakdown 표)
  - [ ] 7.4 — Update `docs/conventions.md` — §0.7 cross-language parity: `bankerRounding` for FTE (already documented; add reference to Story 3.2 partial override semantics)

## Dev Notes

### Architecture binds

- **AD-1 (헥사고날)** — `packages/services/m2_input/labor_conversion.py` = pure (no DB, no clock, AD-5). `apps/api/modules/m2_input/services/monthly_input_service.py` = service layer (existing, extended). handlers unchanged (5 routes backward compatible).
- **AD-5 (purity)** — `labor_conversion.py` 는 stdlib + Decimal only. NO DB, NO clock, NO random.
- **AD-8 (monetary)** — All KRW breakdown fields = `BIGINT` (5 new columns). `company_burden_rate` = `NUMERIC(5,4)` for decimal precision. FTE headcount = `Decimal` (2 dp, ROUND_HALF_EVEN).
- **AD-13 (MonthInputAdapter)** — FTE conversion is **one of the adapter's three responsibilities** (alongside six-stream normalization and conditional machine-time exposure). The pure `build_fte_display` is the adapter's calculation kernel; Epic 4 Story 4-1 (pure cost engine) will wrap it. **Story 3.2 ships the kernel; Story 4-1 wraps it.**
- **AD-15 (cross-language)** — snake_case Python ↔ camelCase TS; `PayType` enum = `"monthly" | "daily"`; banker's rounding in BOTH languages (TS implements `roundHalfEven` explicitly — Story 3.1 mirror pattern); KRW amounts as integers; `Decimal` ↔ `string` at the API boundary (TS parses, not float).
- **AD-22 (append-only-leaning)** — `monthly_input_rows` BREAKDOWN columns are user-input (mutable). DELETE still allowed on the row (PRD §8.M2 diverges from AD-2). Audit-first + idempotent no-op preserved (CR 1.1).
- **AD-23 (4-namespace)** — natural key unchanged. New columns are payload-only (no namespace change).

### Story 3.1 → 3.2 의존성

| Story 3.1 산출물 | Story 3.2 사용처 |
|---|---|
| `monthly_input_rows.workers/days_per_worker/daily_wage_krw` | 그대로 보존. Story 3.2는 monthly 분기 시 추가 breakdown 컬럼 5개 + `pay_type` 추가 |
| `MonthlyInputStateResponse.fte_display: dict` (read-only stub) | 확장: `FteDisplay` typed object (pay_type + breakdown + source_rows) |
| `format_fte_headcount` (pure) | 재사용. `compute_fte_for_daily`는 workdays_in_month 주입만 추가 |
| `compute_fte_wage_krw` (Story 3.1의 basis 환산) | **deprecated for daily mode**. Story 3.2가 `compute_fte_wage_for_daily`(direct sum) 추가. 월급제는 basis 환산 그대로 |
| `Capability.MONTHLY_INPUT_PRODUCTION` | 변경 없음 (AC #6) |
| `docs/capability-matrix.md` | footnote 추가 (Task 5.1) |
| `tests/integration/test_m2_input_label_consistency.py` | 5 cases 추가 (Task 4.2) |

### Epic 의존성 (Epic 1+2+3 자산)

| 자산 | 출처 | 본 스펙 사용처 |
|---|---|---|
| `tenant_settings.*` JSONB pattern | Story 1.2 (M1 settings wizard) | `tenant_settings.payroll.*` JSONB sub-block 신설 |
| `SettingsService.get_tenant_settings()` | Story 1.2 | `_load_payroll_settings` (Task 3.1) |
| `MonthlyInputRowResponse` (Story 3.1) | Story 3.1 | 확장: 5 breakdown 필드 + pay_type + source_rows |
| CR 1.1 lesson (audit-first + idempotent no-op) | Story 1.1 회고 | `save_row` breakdown tuple equality check |
| Epic 2 W4 (TS mirror regex 검증) | Epic 2 회고 | Task 4.2 5 cases 추가 |
| `docs/capability-matrix.md` | Epic 1+2 회고 A4 | footnote 추가 (Task 5.1) |
| `format_fte_headcount` (Story 3.1) | Story 3.1 | 재사용 — `compute_fte_for_daily` wrapper |
| ABC ABC labor pool structure | Epic 9 Story 9-2 (deferred) | Epic 9 진입점에서 본 모듈의 breakdown 활용 |

### Capability matrix (변경 없음)

| Capability | manufacturing | service | manufacturing_service | manufacturing_service_other |
|---|---|---|---|---|
| `MONTHLY_INPUT_LABOR` | ✅ | ✅ | ✅ | ✅ |

(FTE 정밀 계산 = `MONTHLY_INPUT_LABOR`의 일부; 별도 capability 없음. AC #6 명시.)

### 데이터 흐름 (Story 3.2 추가)

```
[Web m2-input [인원] 탭]
   ↓ GET /api/v2/monthly-input/{period}/state
[m2_input.handlers.get_state]
   ↓ service: get_or_create_period → list rows
   ↓ _load_payroll_settings(tenant_id) — 1회 (memoized per request)
       └─ SettingsService.get_tenant_settings(tenant_id)
       └─ tenant_settings.payroll JSONB → merge_payroll_settings
   ↓ _compute_fte_for_state(rows, payroll, mode)
       ├─ mode='month_total' → read single labor row → dispatch by pay_type
       │   ├─ pay_type='daily' → compute_fte_for_daily + compute_fte_wage_for_daily (direct sum)
       │   └─ pay_type='monthly' → compute_fte_for_monthly + compute_pay_type_breakdown
       └─ mode='daily' → read 31 rows → rollup_daily_fte (Σ sum)
   → MonthlyInputStateResponse {completion, is_complete, missing, capability_mask,
                                fte_display: FteDisplay, payroll_settings: PayrollSettingsResponse}

[사용자 labor row 저장]
   ↓ POST /api/v2/monthly-input/{period}/rows
[m2_input.handlers.save_row]
   ↓ _validate_labor_shape(payload) ← AC #1, #2 분기 검증
   ↓ SELECT FOR UPDATE monthly_input_rows natural key
   ↓ idempotent no-op? (full breakdown tuple equality) → 200 + no audit (CR 1.1)
   ↓ emit_audit(action='monthly_input_row_saved', payload={..., full breakdown, trace_id})
   ↓ INSERT/UPDATE row (new 5 breakdown columns + pay_type)
   ↓ recompute completion + fte_display → return updated state
```

### `tenant_settings.payroll.*` JSONB schema (Story 3.2 신규)

```jsonc
{
  "payroll": {
    "monthly_salary_basis_krw": 3500000,    // 정수 KRW
    "workdays_in_month": 20,                // 정수 (1-31)
    "standard_monthly_hours": 176,          // 정수 (PRD §6.1 기본 228)
    "company_burden_rate": 0.115            // Decimal(5,4) — 0.0 ~ 1.0
  }
}
```

Override semantics: **per-field fallback to PRD default**. Story 1.2의 wizard 가 이미 `tenant_settings.*` JSONB로 저장하므로 본 스펙은 새 sub-key만 추가. UI는 Story 0.5 plumbing 후속에서 노출.

### PIPA / PII / Logging

- 인건비(`daily_wage_krw`, `monthly_salary_basis_krw`, `bonus_krw`, `overtime_krw`, `welfare_krw`, `retirement_reserve_krw`, `fte_wage_krw`, `company_burden_rate`)는 **모두 PII** — `redact_processor` 미설치 상태 (Epic 1 회고 C1 defer #3). 운영 전 필수 후속.
- breakdown 5 필드는 PII이므로 structlog 도입 시 redaction 대상. 본 스펙은 `docs/monthly-input-fte.md`에 경고 추가.

### Anti-patterns to avoid (CR lessons)

- **Float for KRW** — AD-8 위반. 모든 KRW = `int` 또는 `Decimal` (headcount).
- **TS Math.round for FTE** — half-away-from-zero ≠ ROUND_HALF_EVEN. TS mirror must implement `roundHalfEven` explicitly.
- **Service-layer direct Decimal arithmetic without rounding** — AD-15 cross-language parity 깨짐. `compute_fte_wage_for_daily`는 explicit quantize to Decimal("1") with ROUND_HALF_EVEN.
- **All-or-nothing override** — partial override (per-field fallback) 명시. One-size-fits-all은 tenant flexibility 깨짐.
- **Storing fte_* in DB** — AD-13 위반. FTE is derived on read only.
- **Mutable breakdown columns without idempotent no-op** — CR 1.1 lesson. breakdown tuple equality check 필수.

## Open Questions (cj-style defaults)

| # | 질문 | 디폴트 | 변경 시 영향 |
|---|---|---|---|
| OQ1 | pay_type='daily' 시 환산 임금 = `workers × days × daily_wage` (direct sum) vs `fte_headcount × monthly_salary_basis_krw` (basis 환산)? | **direct sum** — 일용직은 일급 × 일수 직접 누적. basis 환산은 정규직(=월급제)용. PRD §6.1 "총작업시간 기준 환산인원·환산임금" 정합 | basis 환산 선호 시 Story 3.1 spec 회귀 (Story 3.1은 basis 환산만 구현) |
| OQ2 | breakdown 컬럼 nullable vs NOT NULL with default 0? | **nullable** — non-labor rows (orders, production, ...) 무관. Story 3.1의 다른 breakdown 필드 패턴 일관 | NOT NULL 선호 시 schema migration 추가 |
| OQ3 | `tenant_settings.payroll.*` override UI 노출 시점? | **Story 0.5 plumbing 후속** — 본 스펙은 backend support만. M1 settings wizard에 통합 (Story 1.2 패턴) | 본 스펙에 UI 포함 시 scope +2주 |
| OQ4 | monthly_salary_basis_krw = per-row override vs tenant_settings only? | **per-row override 우선, 미설정 시 tenant_settings.payroll.monthly_salary_basis_krw, 최종 PRD default** — 3-level fallback | tenant-only 선호 시 breakdown 컬럼 1개 제거 (단순화) |
| OQ5 | 730h 시나리오 (PRD §6.1 원본 hr 로직)를 UI에 노출? | **미노출 — backend 계산에만 사용**. UI는 단순 `workers × days × daily_wage` + `monthly_basis` 입력만 받음. 730h 환산은 `standard_monthly_hours=228`일 때 자동으로 동작 | UI 노출 시 PRD §6.1 그래픽 필요 (Phase 4) |
| OQ6 | `pay_type=None` on labor stream → Story 3.1은 implicit 허용, Story 3.2는 명시 거부 — breaking change? | **breaking change 인정** — Story 3.1은 ship 후 1일 만에 close-out. 기존 labor row 없음 (테넌트 데이터 없음). 마이그레이션 무필요 | 호환성 필요 시 pay_type=None → default='daily' (silent fallback) |

## Definition of Done

- [ ] AC #1~#6 모두 pass (backend test + cross-language parity)
- [ ] Task 1~7 모든 subtask check
- [ ] `tests/services/test_m2_input_labor_conversion.py` 16+ cases green
- [ ] `tests/integration/test_m2_input_label_consistency.py` +5 cases green (TS mirror parity)
- [ ] Story 3.1 회귀 테스트 (40 + 5 + 18) 모두 green — 0 regression
- [ ] `docs/monthly-input-fte.md` + `docs/monthly-input.md` §FTE 확장 + `docs/capability-matrix.md` footnote 추가
- [ ] Alembic 0010 적용 (down_revision=0009)
- [ ] 5 typed exceptions → AD-15 envelope 매핑
- [ ] 4 deferral 명시: (a) `tenant_settings.payroll.*` UI 노출 (Story 0.5), (b) ABC labor pool (Epic 9 Story 9-2), (c) 4대 보험 자동 계산 (MVP 외), (d) PII redaction (Epic 1 회고 C1 #3)
- [ ] sprint-status.yaml: `3-2-fte-conversion-daily-labor` → ready-for-dev → done

## References

- Epic 3: Monthly Input Capture — `_bmad-output/planning-artifacts/epics.md` lines 707-756
- F2.2 일용직 FTE 자동 환산 — PRD §6 (인건비) · PRD §6.1 (산식)
- 인건비 breakdown 5 field — PRD §6.1 (인건비 구성)
- AD-13 MonthInputAdapter — `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md` lines 118-122
- Story 3.1 read-only display hook surface — `_bmad-output/implementation-artifacts/3-1-six-stream-monthly-input-ui-month-total-default.md`
- Epic 1 retro C1 #3 PII redaction defer — `_bmad-output/implementation-artifacts/epic-1-retro-2026-08-01.md` §C1
- Epic 2 retro W4 TS mirror regex — `_bmad-output/implementation-artifacts/epic-2-retro-2026-08-01.md` §W4
- CR 1.1 lesson (audit-first + idempotent no-op) — `_bmad-output/implementation-artifacts/.review/story-1-1.diff` + memory `cr-1-1-lessons`
- 4-namespace (AD-23) — `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md` lines 145-150
- Epic 1 settings wizard (tenant_settings JSONB pattern) — `_bmad-output/implementation-artifacts/1-2-settings-wizard-calculation-block.md`
