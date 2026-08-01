# 월 입력 — FTE 정밀 계산 + 일용직 가이드 (Story 3.2)

PRD F2.2 / §6.1 — 인건비 구성 (5개 항목 + pay_type 분기) + 테넌트별
payroll 정책 override.

이 문서는 [docs/monthly-input.md](./monthly-input.md)의 후속편이다.
Story 3.1에서 다룬 6-stream 입력 + 일자별 토글 + 완료 게이트 위에
**인건비 정밀 계산 레이어** (PRD §6.1)를 추가한다.

## 한 줄 요약

> `pay_type='monthly'`: FTE = workers (정규직은 이미 정규화됨)
> `pay_type='daily'`:  FTE = workers × days_per_worker / workdays_in_month (환산)
> 인건비 5개 항목: 기본급 + 시간외 + 복리후생 + 상여 + 퇴직충당금 × 회사부담임률

---

## 데이터 모델 (Story 3.2 §Task 2)

`monthly_input_rows` 테이블에 7개 신규 컬럼 (Alembic 0010):

| 컬럼 | 타입 | nullable | 의미 |
|---|---|---|---|
| `pay_type` | TEXT | O | `'monthly'` \| `'daily'` discriminator — labor stream 전용 |
| `monthly_salary_basis_krw` | BIGINT | O | 기본급 (= FTE 환산 basis). monthly 전용 |
| `overtime_krw` | BIGINT | O | 시간외 수당 |
| `welfare_krw` | BIGINT | O | 복리후생비 |
| `bonus_krw` | BIGINT | O | 상여금 |
| `retirement_reserve_krw` | BIGINT | O | 퇴직충당금 (사용자 입력값) |
| `company_burden_rate` | NUMERIC(5,4) | O | 회사부담임률 (4대보험 + 퇴직) ∈ [0, 1] |

모든 컬럼은 NULLABLE — labor 외 5 stream 행은 그대로 둔다.

`tenant_settings.payroll` (JSONB sub-block) — per-tenant override
(Alembic 0010). 빈 dict `{}`은 PRD default 사용:

```jsonc
{
  "monthly_salary_basis_krw": 2500000,   // default = 2,500,000
  "workdays_in_month": 22,                // default = 22
  "standard_monthly_hours": 228,          // default = 228 (22 × 8h + 4h weekly휴게)
  "company_burden_rate": 0.115            // default = 0.115 (4대보험 + 퇴직 회사부담 평균)
}
```

---

## 서비스 가드 (Task 3.1)

`MonthlyInputService._validate_labor_shape()` — service layer에서
`stream='labor'` 행을 저장할 때 다음 검사를 한다:

| pay_type | 필수 | 금지 |
|---|---|---|
| `'daily'` | `workers>0`, `days_per_worker>0`, `daily_wage_krw>0` | `monthly_salary_basis_krw` |
| `'monthly'` | `workers>0`, `monthly_salary_basis_krw>0` | `days_per_worker>0` |
| `None` | — | — (400 INVALID_LABOR_SHAPE) |

`company_burden_rate`는 [0, 1] 범위 — Pydantic Field가 schema 단계에서
거부 (`extra='forbid'`), service-side 재검증으로 bypass 차단.

## 5개 Typed Errors (Task 3.2)

| 코드 | HTTP | 발생 조건 |
|---|---|---|
| `MONTHLY_INPUT_INVALID_LABOR_SHAPE` | 400 | `_validate_labor_shape` 위반 |
| `MONTHLY_INPUT_FTE_READ_ONLY` | 400 | 직접 `fte_headcount`/`fte_wage_krw` PATCH 시도 (AC #5) |
| `MONTHLY_INPUT_PAY_TYPE_MISMATCH` | 400 | pay_type별 forbidden 필드 사용 (예: daily + monthly_salary_basis_krw) |
| `MONTHLY_INPUT_PAYROLL_SETTINGS_INVALID` | 400 | `tenant_settings.payroll.*` 값이 범위 밖 |
| `MONTHLY_INPUT_COMPANY_BURDEN_RATE` | 422 | `company_burden_rate` 범위 밖 (service 재검증) |

모두 AD-15 §4 envelope `{code, message_ko, details, trace_id}`로 응답.

---

## FTE 계산식 (Task 1 — pure helper)

PRD §6.1 인건비 구성:

```
total_krw = base_krw + overtime_krw + welfare_krw + bonus_krw
          + retirement_reserve_krw × company_burden_rate
```

FTE 환산:

| mode | pay_type | fte_headcount | fte_wage_krw |
|---|---|---|---|
| month_total | `'monthly'` | `workers` (as-is, 2dp) | `workers × breakdown.total_krw` |
| month_total | `'daily'` | `workers × days_per_worker / workdays_in_month` (2dp ROUND_HALF_EVEN) | `daily_wage_krw × workers × days_per_worker` (direct sum) |
| daily | `'daily'` | (per-day 환산, 31일 Σ sum) | (per-day 직접 합산) |

Critical distinction:
- **monthly mode**: FTE 환산 시 `monthly_salary_basis_krw`를 곱한다 (basis 환산).
- **daily mode**: `daily_wage_krw`를 `workers × days_per_worker`만큼 직접 더한다.
  basis 환산을 사용하지 않는다 — 일용직은 실제 급여 × 일수의 합산.

730h 시나리오 (PRD §6.1):
- `standard_monthly_hours=228` → `100 hours worked = 100/228 = 0.439 FTE` (정규직 환산)
- 일용직 3명 × 8일 × `daily_wage_krw=150_000` = `3_600_000 원` (basis 환산 X)

---

## 라운딩 정책 — ROUND_HALF_EVEN (Banker's Rounding)

`packages.services.m2_input.labor_conversion.compute_pay_type_breakdown`,
`compute_fte_for_daily` 모두 `Decimal.quantize(..., rounding=ROUND_HALF_EVEN)`
사용.

TS mirror (`apps/web/lib/l2-input-fte.ts`) — `Decimal.ROUND_HALF_EVEN`을
`money.ts`에서 전역 설정 (`Decimal.set({ rounding: ... })`). `Math.round`은
half-AWAY-FROM-ZERO라 cross-language drift를 일으키므로 `roundHalfEven2`
helper 사용.

테스트:
- `tests/services/test_m2_input_labor_conversion.py` — 36 cases (pure)
- `tests/services/test_m2_input_completion.py` — `fie_display_pay_type_*` 3 cases
- `tests/services/test_m2_input_fte.py` — `payroll_settings_*` 4 cases
- `tests/integration/test_m2_input_label_consistency.py` — 5 cross-lang cases
- `tests/api/test_monthly_input.py` — 8 DB-backed skipif cases (CI shim)

---

## API 변경 요약 (Task 3.3)

`MonthlyInputStateResponse` (`GET .../state` 응답)에 추가:
- `rows[].pay_type` · 5개 breakdown 필드 · `company_burden_rate`
- `fte_display.pay_type` · `fte_display.breakdown` · `fte_display.source_rows`
- `fte_display.payroll_settings` (resolved merge 결과)
- (Story 3.1 호환) `fte_display.{total_workers, total_days_per_worker, total_daily_wage_krw, fte_headcount, fte_wage_krw, monthly_salary_basis_krw}` 그대로 유지

기존 5개 라우트 (POST/PATCH/DELETE/POST mode/GET state)는 **그대로** —
Schema level `extra='forbid'`로 미인가 필드 거부 (AC #5).

---

## TS mirror parity (Task 4)

`apps/web/lib/l2-input-fte.ts` — Python `labor_conversion.py`의 TS mirror.
Drift는 `tests/integration/test_m2_input_label_consistency.py`의 5개
cross-language test로 자동 검출.

| Python | TypeScript |
|---|---|
| `PayType.MONTHLY` | `'monthly'` |
| `PayType.DAILY` | `'daily'` |
| `PayrollSettings` (NamedTuple) | `PayrollSettings` (interface) |
| `merge_payroll_settings(override)` | `mergePayrollSettings(override)` |
| `compute_fte_for_daily(w, d, payroll)` | `computeFteForDaily(w, d, workdaysInMonth)` |
| `compute_fte_wage_for_daily(...)` | `computeFteWageForDaily(...)` |
| `compute_pay_type_breakdown(...)` | `computePayTypeBreakdown(...)` |
| `build_fte_display(...)` | `buildFteDisplay(...)` |
| `rollup_daily_fte(...)` | `rollupDailyFte(...)` |

---

## 디버깅 + 관측 가능성

- `trace_id`는 모든 mutation에 부여. 응답 `X-Trace-Id` 헤더 + `audit_logs.payload.trace_id`.
- `audit_logs.action`:
  - Story 3.1 — `monthly_input_row_created` / `updated` / `deleted` / `mode_changed`
  - Story 3.2 — 동일한 audit action 사용 (새 필드들은 row payload의 일부로 직렬화)
- 빌드 후속: `redact_processor` (defer #2) — payroll JSONB에는 PII 없음
  (금액·비율만 있으므로 redact 불필요).

## 알려진 한계 + 후속 (defer 위주)

- **일별 31행 mode='daily'** 표시 UX (per-day 입력 폼) — Story 3.3+ UI plumbing
- **인건비 음수재고 경고** — Story 3.3 (defer #4)
- **MonthInputAdapter 본체** — Epic 4 `first_calc`에서 작성 (defer #5)
- **테넌트 UI에서 payroll override 편집** — Story 0.5 (settings wizard integration)

## 참조

- 스펙: `_bmad-output/implementation-artifacts/3-2-fte-conversion-daily-labor.md`
- Architecture: AD-8 (KRW 통화) · AD-13 (MonthInputAdapter) · AD-15 (snake_case)
  · AD-23 (4-namespace) · docs/capability-matrix.md
- 이전 가이드: [docs/monthly-input.md](./monthly-input.md) (Story 3.1)
- 다음 가이드: Story 3.3 — 음수재고 경고 + 일별 31행 UX
- Engine reference: `packages/services/m2_input/labor_conversion.py`
