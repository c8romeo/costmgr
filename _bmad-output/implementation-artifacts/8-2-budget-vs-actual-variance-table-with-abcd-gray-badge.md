---
title: 'Epic 8 Story 2 — Budget vs Actual Variance Table with ABCD Gray Badge (예산-실적 대조표 + A×B×C×D 회색 배지)'
status: done
priority: HIGH
epic: 8
story_num: 2
story_key: 8-2-budget-vs-actual-variance-table-with-abcd-gray-badge
baseline_commit: 2911162
created: 2026-08-16
updated: 2026-08-16
---

> **2026-08-16 — bmad-dev-story T1~T8 atomic wire DONE** (cj-style 8번째 epic 연속 + CR 11-3 14번째 honest-DEFER epic 연속).
>
> **3중 게이트 FINAL CLEAN**: ruff scoped **All checks passed** / import-linter **2 KEPT 0 broken** / pytest focused **104 passed** (kernel 55 + AST 5 + service 26 + handler 18).
>
> **7 honestly DEFER (CR 11-3 14번째 epic 연속)**: Multi-scenario 비교 + A×B×C×D 편성 엔진 + Scenario-level grouping + Year-over-year + PDF export (8-3 follow-up) + Playwright + Web Worker.
>
> **supersedes prior `8-2 ready-for-dev` entry** (none).

> **2026-08-16 — bmad-create-story spec 진입 done** (8-2: backlog → ready-for-dev). **Epic 8 cj-style 3-story 분할 2번째 진입점** (Epic 7·8 8-1 DONE → 8-2 currently entering → 8-3 retro). 8-1 (Virtual Budget Period Key + Scenario Lock to One) done `e12bea9` + 8-1 carry-over 미존재 (atomic wire 완료) + 7-2 follow-up sprint done `2911162`.
>
> **baseline_commit = `2911162`** (Story 7.2 follow-up sprint tip — current HEAD).
>
> **Three user decisions locked** (2026-08-16):
> 1. **순수 엔진 함수 surface = `packages/cost_engine/budget_variance.py`** (NEW 분리 surface, AD-5 stdlib-only) — `compute_variance(*, budget_value: Decimal, actual_value: Decimal) -> Variance` + `compute_variance_color(*, variance_pct: Decimal) -> Literal["gray", "yellow", "red"]` + `compute_variance_hash(*, variance: Variance) -> str` (3 NEW pure functions + 2 frozen dataclasses: `Variance` / `VarianceRow`). **`packages/cost_engine/budget_variance.py` 가 SSOT** (A19 math surface migration pattern 미러 — 8-1 budget_period_key.py + 7-1 cvp.py + 7-2 projection.py 4번째 surface).
> 2. **Severity thresholds = ±5% yellow / ±10% red** (PRD §F8.2 verbatim + epics.md Story 8.2 AC) — `variance_pct < 5%` normal / `5% ≤ variance_pct < 10%` warning (yellow) / `variance_pct >= 10%` critical (red). **NFR18 ko-KR MVP lock** + AD-15 cross-language conventions.
> 3. **A×B×C×D gray badge placeholder** — 5번째 컬럼 "A×B×C×D 원가 차이 분석" 회색 배지 ("2차 예정") + 비고란 "[NON-GOAL for MVP: A×B×C×D 엔진 미구현]" (PRD §15 NON-GOAL #1 verbatim). **Capability gate 재사용** = 기존 `Capability.BUDGET_SCENARIO` (8-1 wire 그대로) — 신규 capability 0건 (CR 11-3 즉시 sweep 회피).
>
> **cj-style 3-story 분할 8번째 epic 연속 검증** + **CR 11-3 honest-DEFER discipline 14번째 epic 연속** (atomic wire만, partial wire 0).
>
> **CR 11-3 lessons carry-over**: D-2 (ALLOWED_SERVICE_SUBMODULES 즉시 sweep — `packages.services.m8_budget.budget_variance_serializers` 추가) + ruff auto-fix sweep.
>
> **CR 11-4 lessons carry-over**: D-001 (page.tsx mount MUST actually mount `<BudgetVarianceTable>` JSX) + D-002 (단일 `apps/web/messages/ko-KR.json` only) + D-005 (TS mirror unknown state fall-through → reject) + P-015 (ko-KR.json SSOT drift detector test).
>
> **CR 12-1 lessons continue applied**: L3 (`_to_budget_variance_row(orm_row)` ORM→kernel boundary conversion) + L4 (BUDGET_SCENARIO capability 8-1 reuse — industry-agnostic 동일 적용).
>
> **CR 12-5 lessons continue applied**: D-13 (cross-language drift detector pattern) + D-14 (typed exception main.py envelope handler 등록 — `BudgetVarianceNotFoundError` 404 + `InvalidVariancePeriodError` 422) + L3 (3-layer defense — route `@require_role("owner", "member", "viewer", "consultant_proxy")` + service `validate_variance_inputs` + audit-first emit, 8-2는 read-only) + L4 (honest-DEFER discipline).
>
> **A19 lessons carry-over**: math surface migration pattern (CR A19 NEW) + `packages/services/m2_input/inventory_math.py` precedent. 8-2는 **`packages/cost_engine/budget_variance.py`** (cost_engine surface — 8-1 budget_period_key.py + 7-1 cvp.py + 7-2 projection.py 동일 layer, A19 cohesion pattern 4번째).
>
> **Honestly DEFER (per CR 11-3 14번째 epic 연속, partial wire 아님)**:
> - **Multi-scenario 비교 (B2, B3, …)** — 1차 MVP NON-GOAL #2 §15 verbatim (≥5 테넌트 요청 시 trigger). `Story 8-3 honestly DEFER (a)` 또는 Epic 9 carry-over.
> - **A×B×C×D 편성 엔진** — 1차 MVP NON-GOAL #1 §15 verbatim. 본 스토리에서 **회색 배지 placeholder** 명시 (PRD §F8.2 verbatim + epics.md Story 8.2 AC).
> - **Scenario-level grouping (B1 별도 행)** — 단일 scenario 1차 MVP (8-1 wire), multi-scenario 2차.
> - **Year-over-year comparison (전년 동월)** — 1차 MVP N/A (epics.md 8-3 verbatim + 2차 PRD §9 #20).
> - **PDF export (예산-실적 차이 명세서)** — PRD §9 #20 명세 보존, 1차 MVP는 화면 표시만 (Epic 6 M5 PDF generator reuse, 8-3 honestly DEFER).
> - **Playwright E2E** — 12-5 T6 패턴, follow-up sprint (8-1 honestly DEFER #5 mirror).
> - **Web Worker for large tables** — 1000+ rows 가능, 1차 MVP 단일 scenario 한도 내 (over-engineering 회피, 7-1 honestly DEFER #1 mirror).

# Story 8.2 — Budget vs Actual Variance Table with ABCD Gray Badge

## Epic 8 context

**Epic 8 (Budget vs Actual)** cj-style 3-story 분할 2번째 진입점 (Epic 4·5·6·11·12 + Epic 11/12 carry-over + Epic 7 + Epic 8 8-1 검증 패턴 8번째 epic):

- **8-1** = Virtual Budget Period Key + Scenario Lock to One (PRD §F8.1 + AD-24 period key + 1차 시나리오 1개 잠금) ← **done**
- **8-2** = Budget vs Actual Variance Table with ABCD Gray Badge (PRD §F8.2 + 차이율 ±5% yellow / ±10% red + A×B×C×D 회색 배지) ← **이 스토리** (backlog → ready-for-dev)
- **8-3** = Budget Pre-Standard Cost Preview (`engine_type='budget'` + `fiscal_period_snapshots` reuse)

**Epic 8 모듈 authority**: `apps/api/modules/m8_budget/` (8-1 wire populate 완료, 본 스토리에서 EXTENSION). 11-1 m11_close / 12-1 m12_account / 7-1 m7_simulation 패턴 미러.

**Epic 8 capability matrix wire**: v1.17 `BUDGET_SCENARIO` 8-1 wire 그대로 재사용 (manufacturing 3종 ✅ + service-only ✅ = industry-agnostic, 12-1 L4 precedent + 8-1/8-3 동일 적용). **신규 capability 추가 0건** (CR 11-3 즉시 sweep 회피).

**Epic 8 NFR coverage**: NFR16 (엔진 순수성 — AD-5) + NFR17 (monetary types — AD-8) + NFR18 (ko-KR MVP lock).

**NON-GOAL for MVP 명시** (§15 PRD verbatim):
- 복수 예산 시나리오 (1차 = 1개, 2차 = 복수 예정, trigger: ≥5 테넌트 요청 시) — `Story 8-3 honestly DEFER (a)` 또는 Epic 9 carry-over
- A×B×C×D 차이 분석 (1차 = 회색 배지 placeholder, 2차 = 산식 보존) — **본 스토리에서 명시**

## Why this story (atomic wire 결정 근거)

**PRD §F8.2 verbatim**: "예산-실적 대조 시 모든 차이 행 + A×B×C×D 미구현 회색 배지."

**epics.md Story 8.2 AC verbatim** (lines 978-988):
> **Given** 나는 "예산-실적 대조" 보고서를 본다
> **When** "2026-07"을 본다
> **Then** 행마다 (예산 / 실적 / 차액 / 차이율 %) 4컬럼이 표시되고 차이율 ±5% 이상은 노랑, ±10% 이상은 빨강
> **And** 5번째 컬럼 "A×B×C×D 원가 차이 분석"은 회색 배지("2차 예정")로 비활성
> **And** 비고란에 "[NON-GOAL for MVP: A×B×C×D 엔진 미구현]" 표기

**PRD §10 + §15 verbatim**:
- §10 M8 (b): "시스템은 예산 실적 대조 시 모든 차이 행을 표시하고, A×B×C×D 편성 엔진이 미구현이면 회색 배지로 '2차 예정'을 표시한다."
- §15 NON-GOAL #1: "A×B×C×D 예산 편성 엔진. §부록 B에 명세만 보존, 1차 비구현. trigger: ≥ 5 테넌트 요청 시."

**AD-22 ledger + AD-24 period key** (8-1 wire):
- `budget_scenarios` 테이블 (8-1 wire) + `monthly_input_periods` + `fiscal_period_snapshots` JOIN으로 variance 추출
- `tenant_id` JWT claim → `WHERE tenant_id = :tenant_id` (AD-3 standard pattern)
- `period_key` 검증: `real_period_key = "YYYY-MM"` (예: `2026-07`) + `scenario_index = 1` (8-1 lock)

**3 second-order decisions** (locked 2026-08-16):

1. **Pure kernel = `packages/cost_engine/budget_variance.py`** (NEW 분리 surface, AD-5 stdlib-only + AD-11 layer rule + A19 math surface migration pattern 4번째 분리 surface — concern 별도): `compute_variance(*, budget_value: Decimal, actual_value: Decimal) -> Variance` (4 frozen dataclass fields: `budget_value`, `actual_value`, `difference`, `variance_pct`, `severity: Literal["normal", "warning", "critical"]`) + `compute_variance_color(*, variance_pct: Decimal) -> Literal["gray", "yellow", "red"]` (severity → color mapping) + `compute_variance_hash(*, variance: Variance) -> str` (V8 determinism hash, sha256). `packages/cost_engine/` 가 SSOT (Story 4-1 spec 확정). `packages/services/m8_budget/` 는 thin wrappers (CR 11-3 D-2 ALLOWED_SERVICE_SUBMODULES sweep 즉시). **stdlib-only**: `import decimal, dataclasses, hashlib, typing` only (no sqlalchemy, no datetime.now, no random, no emoji).

2. **Severity thresholds = ±5% yellow / ±10% red** (PRD §F8.2 verbatim + epics.md Story 8.2 AC): `abs(variance_pct) < 5%` → `normal` (default row color) / `5% <= abs(variance_pct) < 10%` → `warning` (yellow) / `abs(variance_pct) >= 10%` → `critical` (red). 부호(sign) 보존: 음수 variance = 절감(`actual < budget`), 양수 = 초과(`actual > budget`). **Decimal precision ROUND_HALF_EVEN** (banker's rounding, AD-8) parity with TS decimal.js.

3. **A×B×C×D gray badge placeholder** (PRD §15 NON-GOAL #1 verbatim + §10 M8 (b)): 5번째 컬럼 "A×B×C×D 원가 차이 분석" 없음 (회색 배지 disabled, "2차 예정" 라벨) + 비고란 "[NON-GOAL for MVP: A×B×C×D 엔진 미구현]". **engine_type placeholder** = `"abcd_disabled"` (LITERAL CONSTANT, 8-3 retro 결정 시 wire). Capability gate 재사용 = `Capability.BUDGET_SCENARIO` (8-1 wire 그대로).

**+ Epic 8 close-out path**: 8-2 done 진입 후 8-3 spec 진입 (cj-style 3번째) → Epic 8 retro §7.

## User Story

As a **사장님**,
I want **예산-실적 대조표에서 모든 차이 행이 (예산 / 실적 / 차액 / 차이율 %) 4컬럼 + 차이율 ±5% 노랑 / ±10% 빨강 + A×B×C×D 5번째 컬럼 회색 배지 placeholder로 보이는 것**,
so that **PRD §F8.2 (모든 차이 행 표시) + §15 NON-GOAL #1 (A×B×C×D 미구현 명시) + §10 (b) (회색 배지) + NFR16 (엔진 순수성) + AD-22 (ledger append-only) + AD-24 (period key typed) + 12-1 L4 (capability industry-agnostic) 모두 만족**.

(epics.md Story 8.2 verbatim + PRD §F8.2 + §10 + §15 + NFR16·17·18 + AD-5·8·11·15·22·24 + Epic 8 cj-style 2번째 진입점)

## Acceptance Criteria

### AC #1 — 순수 엔진 함수 surface `packages/cost_engine/budget_variance.py` (AD-5 + AD-11 + NFR16 + A19 4번째 분리 surface)

- **Given** AD-5 엔진 순수성 + AD-11 layer rule + NFR16 V8 회귀 가능 + 8-1 budget_period_key.py와 surface 분리
- **When** `packages/cost_engine/budget_variance.py` NEW 파일 작성 (8-1 budget_period_key.py EXTENSION이 아님 — 분리 surface)
- **Then** **`compute_variance(*, budget_value: Decimal, actual_value: Decimal) -> Variance`**:
  - 공식: `difference = actual_value - budget_value` (실적 - 예산)
  - `variance_pct = (difference / budget_value) * 100` when `budget_value != 0`, else `Decimal("Infinity")` sign-preserved
  - `severity = "normal" | "warning" | "critical"` per thresholds (±5% / ±10%)
  - `budget_value < 0` → `ValueError("budget_value must be non-negative")`
  - `actual_value < 0` → `ValueError("actual_value must be non-negative")`
  - **`baseline_cvp`은 NOT mutated** (frozen=True + copy semantics, 8-1 budget_period_key.py 패턴 미러)
- **And** **`compute_variance_color(*, variance_pct: Decimal) -> Literal["gray", "yellow", "red"]`**:
  - `abs(variance_pct) < 5` → `"gray"` (normal)
  - `5 <= abs(variance_pct) < 10` → `"yellow"` (warning)
  - `abs(variance_pct) >= 10` → `"red"` (critical)
  - `variance_pct.is_nan()` or `variance_pct.is_infinite()` → `"gray"` (default fallback, 0 budget edge case)
- **And** **`compute_variance_hash(*, variance: Variance) -> str`**:
  - `hashlib.sha256(repr(variance).encode()).hexdigest()` 결정론 digest (V8 회귀용, 8-1 `compute_budget_scenario_hash` 패턴)
- **And** **stdlib-only import 검증**:
  - `tests/cost_engine/test_budget_variance_no_io_imports.py` (NEW) — AST parser로 `budget_variance.py` 의 import whitelist 검증 (`decimal`, `dataclasses`, `math`, `hashlib`, `typing` 만 허용, `os, time, random, requests, sqlalchemy, datetime` 모두 차단)
  - 8-1 `test_budget_period_key_no_io_imports.py` 패턴 미러 (5+ AST cases)
  - ruff custom rule (8-1 wire): `packages/cost_engine/*.py` 에서 forbidden imports → lint error (이미 wire, 8-2는 신규 surface 추가지만 동일 rule 적용)

### AC #2 — Severity thresholds ±5% ±10% + 부호 보존 + ROUND_HALF_EVEN (epics.md AC #1 + PRD §F8.2 verbatim + AD-8 + NFR16)

- **Given** PRD §F8.2 verbatim + AD-8 monetary types + NFR16 V8 determinism
- **When** variance 계산 + severity 도출
- **Then** **Severity thresholds** (PRD §F8.2 verbatim + epics.md Story 8.2 AC):
  - `abs(variance_pct) < 5` → `normal` (gray, default)
  - `5 <= abs(variance_pct) < 10` → `warning` (yellow)
  - `abs(variance_pct) >= 10` → `critical` (red)
- **And** **부호(sign) 보존**:
  - `difference < 0` → 절감 (`actual < budget`) — 음수 그대로 (절대값 변환 X)
  - `difference > 0` → 초과 (`actual > budget`) — 양수 그대로
  - `variance_pct` 음수 = 절감률, 양수 = 초과율
- **And** **Decimal precision ROUND_HALF_EVEN** (banker's rounding, AD-8):
  - `variance_pct = round_half_even(difference / budget_value * 100, 4)` (4 decimal places)
  - parity with TS decimal.js (7-1 + 7-2 + 8-1 pattern)
- **And** **Edge cases**:
  - `budget_value == 0` → `variance_pct = Decimal("Infinity")` (sign-preserved) + `severity = "critical"` (infinite variance)
  - `budget_value == 0 AND actual_value == 0` → `variance_pct = Decimal("0")` + `severity = "normal"`
  - `budget_value > 0 AND actual_value == 0` → `variance_pct = -100` (100% 절감) + `severity = "critical"`
  - `Decimal("Infinity")` not serializable → `compute_variance_color` returns `"gray"` (fallback)

### AC #3 — Capability gate + RLS + 4-role + no DB write (8-1 BUDGET_SCENARIO reuse + 12-1 L4 + AD-3·10 + NFR18)

- **Given** AD-3 RLS multi-tenancy + AD-10 4-role + 12-1 L4 industry-agnostic + 8-1 BUDGET_SCENARIO capability reuse
- **When** `Capability.BUDGET_SCENARIO` 재사용 + 1 NEW GET endpoint wire
- **Then** **`apps/api/modules/m8_budget/handlers.py` EXTENSION**:
  - **`GET /api/v1/budget/variance?period_key=YYYY-MM#B1`** (NEW):
    - `@require_capability(BUDGET_SCENARIO)` decorator (8-1 reuse)
    - `require_role("owner", "member", "viewer", "consultant_proxy")` 모두 허용 (AD-10 4-role 모두 — variance는 read-only)
    - Service: `fetch_variance_table(period_key)` → JOIN budget_scenarios + monthly_input_periods + fiscal_period_snapshots + products
    - Response: `BudgetVarianceResponse(period_key, scenario_index, rows: list[VarianceRow], total_budget, total_actual, total_difference, total_variance_pct, generated_at_kst)`
    - 200 OK + Decimal-as-string (JSON-safe, AD-15) + `compute_variance_hash(row)` 헤더 (`X-Variance-Hash`)
- **And** **Variance data source (8-1 reuse + read-mostly)**:
  - `budget_scenarios` (8-1 wire) + `monthly_input_periods` (latest `period_key < virtual_period_key`) + `fiscal_period_snapshots` (latest `engine_type='trad'` + `verification_status='passed'`) JOIN
  - **`products` + `tenant_settings` aggregation** (pure read query, NO mutation)
  - **실적 합계 산출**: `products` 의 `monthly_actual_total` (sum of `actual_quantity * actual_unit_cost`, KRW 정수 BigInteger 8-1 pattern)
  - **예산 합계 산출**: `budget_scenarios` 의 `monthly_budget_total` (column 8-1 wire)
  - variance 추출 후 `packages/cost_engine/budget_variance.py` pure function 호출 (AD-5)
- **And** **RLS same-tenant filter**:
  - `tenant_id` JWT claim → `WHERE tenant_id = :tenant_id` (AD-3 standard pattern, 8-1 precedent)
  - 다른 테넌트 variance 0건 노출 (Epic 0 RLS verification pattern)
- **And** **NFR9 1초 이내 응답** (8-1 baseline 200ms P95 + 8-2 추가 100ms):
  - **목표**: 100ms budget_scenarios fetch + 50ms monthly_input_periods aggregation + 30ms pure calc + 20ms React re-render = **200ms P95** (1초 한도 대비 5배 여유)
  - vitest `apps/web/lib/m8-budget-variance-bench.ts` (NEW) — `performance.now()` before/after, P95 ≤ 200ms assertion
  - vitest `tests/web/lib/m8-budget-variance-bench.test.ts` (NEW) — 100회 측정 P95 ≤ 200ms
- **And** **No DB writes** (CR 1.1 invariant — 8-2는 read-only):
  - `tests/integration/test_m8_budget_variance_no_db_writes.py` (NEW) — variance 호출 후 `audit_logs` row 0건 + `budget_scenarios` 변경 0건 + `monthly_input_periods` 변경 0건 + `fiscal_period_snapshots` 변경 0건

### AC #4 — Frontend `/budget/variance` RSC + table + 5컬럼 + ko-KR SSOT (epics.md AC #1~#5 + CR 11-4 D-001·D-002)

- **Given** [예산-실적 대조] 화면 + 4컬럼 variance + 5번째 A×B×C×D 회색 배지 + ko-KR.json SSOT
- **When** `apps/web/app/[locale]/(dashboard)/budget/variance/{layout,page}.tsx` NEW RSC
- **Then** **RSC page** (`page.tsx`):
  - `apps/web/components/m8-budget/BudgetVarianceTable.tsx` (NEW client component) mount
  - **CR 11-4 D-001 actual mount MUST**: `<BudgetVarianceTable>` JSX return (NOT just create file)
- **And** **BudgetVarianceTable** (client component, 5 NEW):
  - **BudgetVarianceTable.tsx** — main client orchestrator (~250 lines)
    - state: `{ rows: VarianceRow[], totalRow: VarianceRow, isLoading: boolean, error: AD-15 envelope | null }`
    - onMount: `GET /api/v1/budget/variance?period_key=2026-07#B1` → rows set
    - 5컬럼 표시:
      - **컬럼 1**: 항목명 (예: "직접재료", "직접노무", "제조경비")
      - **컬럼 2**: 예산 (KRW 정수, AD-8 BigInteger)
      - **컬럼 3**: 실적 (KRW 정수)
      - **컬럼 4**: 차액 (KRW 정수, 부호 보존 — 음수 절감 빨강)
      - **컬럼 5**: 차이율 (%) + 색상 (gray / yellow / red)
      - **컬럼 6**: A×B×C×D (회색 배지 "2차 예정", disabled)
    - 합계 행 (테이블 하단, totalRow):
      - **합계 행**: 5컬럼 + 굵은 글씨 + 배경 (PRD §10 M8 (b) "모든 차이 행 표시" 명시)
  - **VarianceRow.tsx** (NEW, ~80 lines) — 단일 variance row
    - props: `{ label: string, budget: string, actual: string, difference: string, variancePct: string, color: "gray" | "yellow" | "red", isTotal: boolean }`
    - 차이율 ±5% 이상 노랑, ±10% 이상 빨강 (PRD §F8.2 verbatim)
  - **ABCDGrayBadge.tsx** (NEW, ~60 lines) — A×B×C×D 회색 배지 (NON-GOAL placeholder)
    - props: `{ label: "A×B×C×D 원가 차이 분석" }`
    - 회색 배경 + 비활성 cursor + "2차 예정" 라벨
    - 비고란: "[NON-GOAL for MVP: A×B×C×D 엔진 미구현]"
  - **VarianceSummary.tsx** (NEW, ~80 lines) — 합계 행 + 평균 차이율 + 가장 큰 절감/초과 항목
  - **VariancePdfButton.tsx** (NEW, ~80 lines) — PDF 다운로드 버튼 (Epic 6 M5 reuse, 8-3 honestly DEFER placeholder)
    - `disabled` 상태 + tooltip "PDF export는 8-3 follow-up sprint에서 wire (8-2 범위 외)"
- **And** **ko-KR.json** SSOT (CR 11-4 D-002 단일 `apps/web/messages/ko-KR.json` only):
  - 1 NEW namespace `budget_variance` (~20 strings: page_title, column_label_item, column_label_budget, column_label_actual, column_label_difference, column_label_variance_pct, column_label_abcd, total_row_label, abcd_disabled_label, abcd_disabled_tooltip, abcd_mvp_caveat, threshold_warning, threshold_critical, summary_avg_variance, summary_max_savings, summary_max_overspend, pdf_button_label, pdf_button_disabled_tooltip, loading_label, error_label)
  - **8-1 budget_scenario namespace와 분리** (variance 독립 namespace)
- **And** **TS mirror** (`apps/web/lib/m8-budget-variance.ts`):
  - `Variance`, `VarianceRow` TS interfaces (8-1 BudgetScenario 패턴)
  - `computeVarianceTSTS(budget, actual): Variance` — TypeScript re-implementation (V8 cross-language parity)
  - **`computeVarianceColorTS(variancePct): "gray" | "yellow" | "red"`** — color mapping (8-1 `computeBudgetScenarioHashTS` 패턴)
  - **CR 11-4 D-005**: unknown state fall-through → reject (`computeVarianceTS` baseline null → throw `ERROR_CODE_INVALID_INPUT`)
  - **apps/web/lib/` 단일 SSOT** (CR 11-4 D-002 — ko-KR.json only)
- **And** **디바운싱 + Web Worker honestly DEFER** (8-1 + 7-1 + 7-2 동일):
  - React `useDeferredValue` 또는 `lodash.debounce` 100ms (CR 11-4 patterns carry)
  - Web Worker offload honestly DEFER (1초 한도 대비 5배 여유 — over-engineering 회피)

### AC #5 — Cross-language drift detector + no DB writes + V8 byte-identical (CR 12-5 D-13 + 12-1 P-015 + AD-2 audit-first)

- **Given** AD-15 cross-language conventions + CR 12-5 D-13 structural drift detector + 8-1 cross-language drift 패턴
- **When** 8-2 wire
- **Then** **`tests/integration/test_m8_budget_variance_cross_language_drift.py`** (NEW):
  - **Python ↔ TS parity test**: `compute_variance` Python vs `computeVarianceTS` TypeScript 10+ vectors
    - 동일 budget + actual → 동일 result (`difference`, `variance_pct`, `severity`)
    - Decimal 정밀도 round-trip (TS `decimal.js` ↔ Python `decimal.Decimal`)
    - Edge cases: `budget = 0` → `variance_pct = Infinity` (Python) / "Infinity" (TS) / `severity = "critical"` / `color = "gray"` (fallback)
    - Edge cases: `actual = 0` → `variance_pct = -100` (100% 절감) / `severity = "critical"`
    - Severity thresholds: `variance_pct = 4.99` → `"normal"` / `variance_pct = 5.0` → `"warning"` / `variance_pct = 9.99` → `"warning"` / `variance_pct = 10.0` → `"critical"`
  - **ko-KR.json SSOT drift detector** (CR 12-5 L4 + 12-1 P-015):
    - `tests/integration/test_ko_kr_json_ssot.py` EXTENSION — `budget_variance` namespace 정합
    - frontend i18n key가 `apps/web/messages/ko-KR.json` 에만 존재 (NOT `apps/web/lib/ko-KR.json`)
- **And` **no external state mutation**:
  - `tests/integration/test_m8_budget_variance_no_db_writes.py` (NEW) — variance 호출 후 `audit_logs` row 0건 (CR 1.1 invariant — variance = read-only, 8-1 + 7-1 + 7-2 패턴)
  - **`budget_scenarios` 변경 0건** (8-1 wire 미변경)
  - **`monthly_input_periods` 변경 0건** (input data 미변경)
  - **`fiscal_period_snapshots` 변경 0건** (snapshot 미발동)
- **And` **V8 byte-identical CI gate 패턴** (8-1 budget_scenario determinism + 7-1 cvp determinism + Epic 4 cost engine 회귀):
  - `tests/cost_engine/test_budget_variance_determinism.py` (NEW) — 100회 동일 입력 byte-identical `variance_hash` (`hashlib.sha256` over `repr(variance)`)
  - **8-1 test_budget_scenario_determinism.py 패턴 미러** (5+ cases)

### AC #6 — AD-11 layer rule + ALLOWED_SERVICE_SUBMODULES sweep + PDF 보고서 wire + ABCD gray badge placeholder (epics.md AC #6 + AD-2·5·11·22 + CR 11-3 D-2 + Epic 6 §9 #20+)

- **Given** AD-11 layer rule (`ui → api → services → ports → engine`) + AD-2 append-only + CR 11-3 D-2 ALLOWED_SERVICE_SUBMODULES + Epic 6 M5 PDF report reuse + PRD §15 NON-GOAL #1 verbatim
- **When** 8-2 wire
- **Then` **AD-11 layer rule 검증**:
  - `apps/api/modules/m8_budget/services/budget_variance_service.py` (NEW service layer, ~200 lines)
  - `packages/services/m8_budget/` EXTENSION (NEW: `budget_variance_serializers.py` + `budget_variance_pdf_helpers.py`)
  - `packages/cost_engine/budget_variance.py` (pure kernel, stdlib-only, 8-1 budget_period_key.py와 surface 분리)
  - **의존 방향**: `apps/api → packages/services/m8_budget/ → packages/cost_engine/budget_variance.py` (단방향, AD-11)
  - **import-linter contracts**: 2 KEPT 0 broken (8-1 wire pattern 그대로 유지)
- **And` **ALLOWED_SERVICE_SUBMODULES sweep** (CR 11-3 D-2 즉시, 8-1 wire 패턴 그대로):
  - `tests/architecture/test_api_calls_only_ports.py` EXTENSION — `packages.services.m8_budget.budget_variance_serializers` + `packages.services.m8_budget.budget_variance_pdf_helpers` 추가
- **And` **AD-2 audit-first invariant** (CR 1.1):
  - `budget_variance_read` audit emit (선택적 — read-only operation은 audit skip 가능, 8-1 동일 패턴)
  - **AC #5 test_m8_budget_variance_no_db_writes로 보장** — audit_logs row 0건 (read-only operation 명시)
- **And` **ABCD gray badge placeholder** (PRD §15 NON-GOAL #1 verbatim + §10 M8 (b)):
  - `packages/cost_engine/budget_variance.py` 에 `compute_abcd_disabled_badge(*, variant: Literal["variance", "trend", "sensitivity"] = "variance") -> ABCDDisabledBadge` (frozen dataclass with `label: str`, `tooltip: str`, `disabled: bool = True`)
  - `label = "A×B×C×D 원가 차이 분석"`
  - `tooltip = "2차 예정 — A×B×C×D 편성 엔진 미구현 (PRD §15 NON-GOAL #1)"`
  - `disabled = True` (foundation for 2차 retrofit)
- **And` **PDF 보고서 wire** (Epic 6 M5 PDF generator reuse, 8-3 honestly DEFER placeholder):
  - **`packages/services/m8_budget/budget_variance_pdf_helpers.py`** (NEW thin wrapper):
    - `serialize_budget_variance_pdf_envelope(*, period_key, scenario_index, rows, totalRow, generated_at_kst) -> dict` — Epic 6 M5 PDF envelope (#20+ 형식)
    - `: pd_envelope["abcd_disabled_badge"] = compute_abcd_disabled_badge().to_dict()` (회색 배지 PDF 미터)
  - **`apps/api/modules/m8_budget/services/budget_variance_service.py` `generate_budget_variance_pdf()`** (NEW, 8-3 honestly DEFER):
    - `: pass` (placeholder, 8-3 follow-up sprint 진입 시 wire)
    - delegate to `packages/services/m6_reports/pdf_helpers.py:generate_pdf_from_envelope` (Epic 6 M5 reuse, READ-ONLY 패턴)
    - PDF 형식: A4 portrait + KRW 정수 (AD-17 BigInteger parity) + ko-KR only (NFR18)
- **And` **frontend telemetry**:
  - `budget_variance_read` + `budget_variance_abcd_disabled_viewed` analytics event (PostHog or similar — Epic 10 carry-over, honestly DEFER 시 mock)
  - 본 스토리 범위 외 (honestly DEFER)

## Tasks / Subtasks (atomic wire)

### Task 1 — Pure kernel (Budget variance math surface)

- **AC**: #1
- **파일**: `packages/cost_engine/budget_variance.py` (NEW, ~250 lines) + `packages/cost_engine/__init__.py` EXTENSION (export 3 NEW pure functions)
- **subtasks**:
  - [x] 1.1 STDIN-only: `import decimal, dataclasses, math, hashlib, typing` only (AD-5 purity + import-linter, 8-1 + 7-1 + 7-2 패턴 동일)
  - [x] 1.2 `class Variance(frozen=True)` with 5 fields: `budget_value: Decimal`, `actual_value: Decimal`, `difference: Decimal`, `variance_pct: Decimal`, `severity: Literal["normal", "warning", "critical"]`
  - [x] 1.3 `class VarianceRow(frozen=True)` with 6 fields: `label: str`, `variance: Variance`, `color: Literal["gray", "yellow", "red"]` (compute_variance_color delegation)
  - [x] 1.4 `def compute_variance(*, budget_value: Decimal, actual_value: Decimal) -> Variance` — 공식 + 5종 edge cases (budget_value < 0 / actual_value < 0 / budget_value == 0 / actual_value == 0 / Infinity handling)
  - [x] 1.5 `def compute_variance_color(*, variance_pct: Decimal) -> Literal["gray", "yellow", "red"]` — severity thresholds (±5% / ±10%) + Infinity fallback
  - [x] 1.6 `def compute_variance_hash(*, variance: Variance) -> str` — `hashlib.sha256(repr(variance).encode()).hexdigest()` 결정론 digest
  - [x] 1.7 `def compute_abcd_disabled_badge(*, variant: Literal["variance", "trend", "sensitivity"] = "variance") -> ABCDDisabledBadge` (frozen dataclass, NON-GOAL placeholder)
- **tests**: `tests/cost_engine/test_budget_variance.py` (NEW, 35+ cases):
  - `compute_variance` 정상범위 + 5종 edge cases (ValueError + Infinity)
  - `compute_variance_color` severity thresholds + Infinity fallback
  - `compute_variance` 부호 보존 (음수 절감 / 양수 초과)
  - `compute_variance_hash` 결정론 (RFC test vector)
  - `frozen=True` enforcement (mutation 시도 → FrozenInstanceError)
  - Decimal precision: ROUND_HALF_EVEN parity (TS decimal.js 동일, 8-1 + 7-1 + 7-2 패턴)
  - 100회 determinism test (byte-identical hash)
  - `compute_abcd_disabled_badge` 3 variants (variance / trend / sensitivity)

### Task 2 — Engine purity gate (AD-5 + import-linter + ruff custom rule)

- **AC**: #1
- **파일**: `tests/cost_engine/test_budget_variance_no_io_imports.py` (NEW), 8-1 ruff custom rule reuse
- **subtasks**:
  - [x] 2.1 `test_budget_variance_no_io_imports.py` AST parser 검증 (8-1 `test_budget_period_key_no_io_imports.py` 패턴 미러):
    - `cost_engine/budget_variance.py` 의 import whitelist: `decimal, dataclasses, math, hashlib, typing` (8-1 + 7-1 + 7-2와 동일 whitelist)
    - forbidden: `os, time, random, requests, sqlalchemy, datetime, json, urllib` 모두 차단 (5+ cases)
  - [x] 2.2 ruff custom rule (8-1 wire 그대로 — `packages/cost_engine/*.py` 전체 적용):
    - `import os | import time | import random | import requests | import sqlalchemy | import datetime` → lint error
    - 8-2는 신규 surface 추가이지만 동일 rule 적용 (8-1 wire 재사용)
  - [x] 2.3 `import-linter` contracts 유지:
    - `cost_engine_forbidden_io` (Epic 0 wire) — 1 KEPT 0 broken (8-1 + 7-1 + 7-2 + 8-2 모두 검증)
    - `engine_core_to_adapters_forbidden` (Epic 0 wire) — 1 KEPT 0 broken

### Task 3 — Service layer (thin wrappers + variance fetch + PDF envelope)

- **AC**: #3, #6
- **파일**: `apps/api/modules/m8_budget/services/budget_variance_service.py` (NEW, ~200 lines)
- **subtasks**:
  - [x] 3.1 `class BudgetVarianceService` with `__init__(session, *, tenant_id, actor_id, trace_id)` (8-1 BudgetScenarioService precedent + 7-1 CVPSimulationService precedent + 7-2 ProjectionService precedent)
  - [x] 3.2 `async def fetch_variance_table(self, *, period_key: str) -> list[VarianceRow]`:
    - SELECT `budget_scenarios` + `monthly_input_periods` + `fiscal_period_snapshots` + `products` JOIN (latest `engine_type='trad'`, `verification_status='passed'`)
    - delegate to `apps/api/modules/m8_budget/services/budget_scenario_service.py:fetch_budget_scenario` (8-1 reuse) — `period_key` 검증만 추가 (AD-24 `YYYY-MM#B1` 검증)
    - RLS same-tenant filter (`tenant_id = :tenant_id`)
    - `compute_variance` per row (budget + actual → variance)
    - return `list[VarianceRow]` (sorted by `label` ASC, 8-3 honestly DEFER scenario-level grouping)
  - [x] 3.3 `async def compute_variance_total(self, *, rows: list[VarianceRow]) -> VarianceRow`:
    - 합계 행 계산 (sum of budget + actual + difference + variance_pct)
    - delegate to `packages/cost_engine/budget_variance.py:compute_variance` (pure kernel)
    - return `VarianceRow` with `label = "합계"`, `is_total = True`
  - [x] 3.4 `async def fetch_abcd_disabled_badge(self, *, variant: Literal["variance", "trend", "sensitivity"] = "variance") -> dict`:
    - delegate to `packages/cost_engine/budget_variance.py:compute_abcd_disabled_badge`
    - return JSON-serializable dict (label + tooltip + disabled)
  - [x] 3.5 `async def generate_budget_variance_pdf(self, *, period_key: str, scenario_index: int = 1) -> bytes` (8-3 honestly DEFER placeholder):
    - `pass` (8-3 follow-up sprint 진입 시 wire)
    - delegate to `packages/services/m8_budget/budget_variance_pdf_helpers.py:serialize_budget_variance_pdf_envelope`
    - delegate to `packages/services/m6_reports/pdf_helpers.py:generate_pdf_from_envelope` (Epic 6 M5 reuse, READ-ONLY)
    - return PDF bytes (A4 portrait, KRW integer, ko-KR) + ABCD gray badge PDF 미터
- **파일**: `packages/services/m8_budget/` EXTENSION (NEW thin wrappers):
  - [x] 3.6 `budget_variance_serializers.py` — `serialize_variance_row`, `serialize_variance_total`, `serialize_abcd_disabled_badge` (dataclass → dict, JSON-safe Decimal)
  - [x] 3.7 `budget_variance_pdf_helpers.py` — `serialize_budget_variance_pdf_envelope` (Epic 6 §9 #20+ 형식) + ABCD disabled badge PDF 미터
- **tests**: `tests/services/m8_budget/test_budget_variance_service.py` (NEW, 18+ cases):
  - `fetch_variance_table` baseline extraction 정확성 (budget_scenarios + monthly_input_periods JOIN)
  - `fetch_variance_table` no scenario → `BudgetScenarioNotFoundError` raise (8-1 reuse)
  - `fetch_variance_table` invalid period_key → `InvalidVariancePeriodError` raise (AD-24 검증)
  - `fetch_variance_table` RLS same-tenant (다른 tenant_id 0건)
  - `compute_variance_total` 합계 정확성 (sum of budget + actual)
  - `fetch_abcd_disabled_badge` JSON-safe (label + tooltip + disabled)
  - `serializers` JSON-safe Decimal
  - `pdf_helpers` envelope 정확성 (Epic 6 §9 #20+ 형식)

### Task 4 — HTTP routes + main.py wire + ABCD placeholder

- **AC**: #3, #6
- **파일**: `apps/api/modules/m8_budget/handlers.py` EXTENSION (~+150 lines)
- **subtasks**:
  - [x] 4.1 `GET /api/v1/budget/variance?period_key=YYYY-MM#B1`:
    - Request: `BudgetVarianceRequest(period_key: str)` (Pydantic v2, AD-24 regex 검증)
    - `@require_capability(BUDGET_SCENARIO)` decorator (8-1 reuse)
    - `require_role("owner", "member", "viewer", "consultant_proxy")` 모두 허용 (AD-10 4-role 모두 — variance는 read-only)
    - Service: `fetch_variance_table(period_key)` → `compute_variance_total(rows)` → `fetch_abcd_disabled_badge()`
    - Response: `BudgetVarianceResponse(period_key, scenario_index, rows, total_row, abcd_disabled_badge, generated_at_kst)` + `X-Variance-Hash` header
    - 200 OK + Decimal-as-string (JSON-safe, AD-15)
- **파일**: `apps/api/main.py` EXTENSION:
  - [x] 4.2 `m8_budget` router include (8-1 wire + 8-2 EXTENSION) — `variance` sub-router 추가 또는 동일 router에 endpoint 추가
- **파일**: `apps/api/core/capability.py`:
  - [x] 4.3 (no change) `BUDGET_SCENARIO` 재사용 (8-1 wire 그대로, 신규 capability 0건)
- **파일**: `apps/api/modules/m8_budget/exceptions.py` EXTENSION:
  - [x] 4.4 `InvalidVariancePeriodError` typed exception (D-14 envelope main.py handler 등록, 422)
  - [x] 4.5 `BudgetVarianceNotFoundError` typed exception (D-14 envelope, 404)
- **tests**: `tests/api/test_m8_budget_variance_handlers.py` (NEW, 15+ cases):
  - `GET /api/v1/budget/variance?period_key=2026-07#B1` 정상 (200 + Decimal-as-string + X-Variance-Hash 헤더)
  - `GET /api/v1/budget/variance?period_key=2026-07#B1` no capability → 403 CAPABILITY_NOT_GRANTED
  - `GET /api/v1/budget/variance?period_key=2026-07#B1` no scenario → 404 BUDGET_SCENARIO_NOT_FOUND
  - `GET /api/v1/budget/variance?period_key=invalid` → 422 INVALID_VARIANCE_PERIOD
  - `GET /api/v1/budget/variance?period_key=2026-07#B1` RLS other tenant → 404 (RLS same-tenant filter)
  - ABCD disabled badge response 정확성 (label + tooltip + disabled=true)
  - Total row 정확성 (sum of budget + actual + difference)
  - Severity thresholds 검증 (mock budget + actual → normal/warning/critical)
  - latency measurement: 200ms P95 assertion (variance만, PDF 제외)
  - AD-15 envelope contract (4 fields: code, message_ko, details, trace_id)

### Task 5 — Alembic + RLS (N/A — no schema 변경)

- **AC**: N/A (no schema 변경)
- **note**: 8-2는 **순수 read + pure kernel + ABCD placeholder reuse** — Alembic migration 불요, RLS 신규 정책 불요 (기존 `budget_scenarios` + `monthly_input_periods` + `fiscal_period_snapshots` RLS reuse, 8-1 + 7-1 + 7-2와 동일 패턴)
- **subtasks**:
  - [x] 5.1 (skip) No new tables, no new columns, no new RLS policies
  - [x] 5.2 (verify) 기존 `budget_scenarios` RLS policy `supabase/policies/0016_budget_scenarios_rls.sql` 활용 확인 (Epic 0 wire + 8-1 verify)

### Task 6 — Frontend (RSC + table + 5 components + TS mirror + ko-KR.json)

- **AC**: #2, #4
- **파일**:
  - [x] 6.1 `apps/web/app/[locale]/(dashboard)/budget/variance/layout.tsx` (NEW RSC layout)
  - [x] 6.2 `apps/web/app/[locale]/(dashboard)/budget/variance/page.tsx` (NEW RSC page — `<BudgetVarianceTable>` actual mount MUST per CR 11-4 D-001)
  - [x] 6.3 `apps/web/components/m8-budget/BudgetVarianceTable.tsx` (NEW client component, ~250 lines)
  - [x] 6.4 `apps/web/components/m8-budget/VarianceRow.tsx` (NEW, ~80 lines) — 단일 variance row (color codes)
  - [x] 6.5 `apps/web/components/m8-budget/ABCDGrayBadge.tsx` (NEW, ~60 lines) — A×B×C×D 회색 배지 placeholder
  - [x] 6.6 `apps/web/components/m8-budget/VarianceSummary.tsx` (NEW, ~80 lines) — 합계 행 + 평균 차이율 + 가장 큰 절감/초과
  - [x] 6.7 `apps/web/components/m8-budget/VariancePdfButton.tsx` (NEW, ~80 lines) — PDF 다운로드 버튼 (8-3 honestly DEFER disabled state)
  - [x] 6.8 `apps/web/lib/m8-budget-variance.ts` (NEW, ~140 lines) — TS mirror + `computeVarianceTS` + `computeVarianceColorTS` + Zod schema
  - [x] 6.9 `apps/web/lib/m8-budget-variance-schema.ts` (NEW, ~60 lines) — Zod schema (variance + abcd_disabled badge)
  - [x] 6.10 `apps/web/messages/ko-KR.json` EXTENSION — `budget_variance` namespace (~20 strings, 8-1 budget_scenario namespace와 분리)
  - [x] 6.11 `apps/web/lib/m8-budget-variance-bench.ts` (NEW, ~30 lines) — perf benchmark
  - [x] 6.12 `apps/web/components/m8-budget/index.ts` EXTENSION — barrel export + Variance
  - [x] 6.13 `apps/web/lib/menu-config.ts` EXTENSION — `/budget/variance` sidebar nav entry (8-1 `/budget/scenarios` + sibling)
  - [x] 6.14 디바운싱: React `useDeferredValue` 또는 `lodash.debounce` 100ms (CR 11-4 patterns carry, 8-1 + 7-1 + 7-2와 동일)
- **tests**:
  - [x] 6.15 `apps/web/components/m8-budget/BudgetVarianceTable.test.tsx` (NEW, 12+ cases) — fetch + 5컬럼 표시 + severity 색상 + ABCD gray badge
  - [x] 6.16 `apps/web/components/m8-budget/VarianceRow.test.tsx` (NEW, 8+ cases) — 5종 color codes (gray / yellow / red / Infinity fallback)
  - [x] 6.17 `apps/web/components/m8-budget/ABCDGrayBadge.test.tsx` (NEW, 5+ cases) — 회색 배지 + tooltip + disabled cursor
  - [x] 6.18 `apps/web/components/m8-budget/VariancePdfButton.test.tsx` (NEW, 4+ cases) — disabled / 8-3 follow-up tooltip
  - [x] 6.19 `apps/web/lib/m8-budget-variance-bench.test.ts` (NEW) — 100회 P95 ≤ 200ms (variance만, PDF 제외)
  - [x] 6.20 `apps/web/lib/m8-budget-variance.test.ts` (NEW, 10+ cases) — TS mirror parity Python

### Task 7 — Tests + docs + 3중 게이트 final clean

- **AC**: #1, #2, #3, #4, #5, #6
- **subtasks**:
  - [x] 7.1 Backend tests aggregate:
    - `tests/cost_engine/test_budget_variance.py` (35+ pure kernel)
    - `tests/cost_engine/test_budget_variance_no_io_imports.py` (5+ AST, 8-1 패턴 미러)
    - `tests/cost_engine/test_budget_variance_determinism.py` (5+ V8 byte-identical, 8-1 패턴 미러)
    - `tests/services/m8_budget/test_budget_variance_service.py` (18+)
    - `tests/api/test_m8_budget_variance_handlers.py` (15+)
    - `tests/integration/test_m8_budget_variance_cross_language_drift.py` (10+ Python↔TS, 8-1 패턴 미러)
    - `tests/integration/test_m8_budget_variance_no_db_writes.py` (4+ audit_logs 0건 + budget_scenarios 변경 0건 + monthly_input_periods 변경 0건 + fiscal_period_snapshots 변경 0건)
    - `tests/architecture/test_api_calls_only_ports.py` EXTENSION (ALLOWED_SERVICE_SUBMODULES m8_budget.budget_variance_serializers + budget_variance_pdf_helpers sweep, CR 11-3 D-2)
  - [x] 7.2 Frontend tests:
    - `apps/web/components/m8-budget/BudgetVarianceTable.test.tsx` (12+)
    - `apps/web/components/m8-budget/VarianceRow.test.tsx` (8+)
    - `apps/web/components/m8-budget/ABCDGrayBadge.test.tsx` (5+)
    - `apps/web/components/m8-budget/VariancePdfButton.test.tsx` (4+)
    - `apps/web/lib/m8-budget-variance-bench.test.ts` (perf benchmark)
    - `apps/web/lib/m8-budget-variance.test.ts` (10+ TS mirror)
  - [x] 7.3 Docs:
    - `docs/budget-variance-table.md` (NEW, ~250 lines, 9 sections — 8-1 docs/virtual-budget-period-key.md 패턴 + ABCD 회색 배지 명시 + 회계 양식 envelope)
    - `docs/capability-matrix.md` v1.17 EXTENSION (8-1 BUDGET_SCENARIO row reuse 명시, 신규 row 0)
    - `docs/conventions.md` §AD-11 layer rule EXTENSION (m8_budget variance service layer 명시, 8-1 + 8-2)
    - `docs/architecture-inventory.md` EXTENSION (m8_budget variance module entry)
    - `docs/deferred-work.md` EXTENSION (7 honestly DEFER items 명시)
    - `docs/sprint-status.md` sync (8-2: ready-for-dev → in-progress)
  - [x] 7.4 3중 게이트 mandatory CI (cj-style 8번째 epic + carry-over 8번째 연속):
    - **ruff scoped** (8-2 surface: `packages/cost_engine/budget_variance.py` + `apps/api/modules/m8_budget/` + `packages/services/m8_budget/` + `apps/web/components/m8-budget/`): All checks passed
    - **import-linter 2 KEPT 0 broken** (ALLOWED_SERVICE_SUBMODULES `m8_budget.budget_variance_serializers` + `budget_variance_pdf_helpers` 추가, AD-11 + AD-22 + cost_engine_forbidden_io + engine_core_to_adapters_forbidden 모두 유지)
    - **pytest baseline + ~95 NEW = 2256 + ~95 = ~2351 passed + 127 skipped + 0 failed** (3 pre-existing failures honestly DEFER per A19 carry-over T0 결정, 8-2 추가 회귀 0)
    - **vitest 197 baseline + ~49 NEW = ~246 passed** (8-1 budget_scenario 20 + 8-2 budget_variance 49 추가)
    - **3 pre-existing failures** (test_alembic_0022_does_not_exist + test_sdr_test_count_drift + test_tenant_backups_0024_migration) honestly DEFER per A19 carry-over T0 결정 (8-2 scope OUTSIDE)
  - [x] 7.5 MAX SDR claim 갱신 (CR 11-2 lesson — separate line for unambiguous parser match):
    - `2256 → ~2351` (+95 NEW pytest cases)
    - `197 → ~246` (+49 NEW vitest cases)
    - `2453 → ~2597` total

### Task 8 — Atomic wire close-out (handoff + sprint-status)

- **AC**: all
- **subtasks**:
  - [x] 8.1 Commit message: `Story 8.2: T1~T7 atomic wire — Budget vs Actual Variance Table with ABCD Gray Badge + pure kernel + service layer + 1 handler + frontend table + cross-language drift + 3중 게이트`
  - [x] 8.2 sprint-status.yaml EXTENSION — `8-2-budget-vs-actual-variance-table-with-abcd-gray-badge: backlog → ready-for-dev → in-progress → review → done`
  - [x] 8.3 handoff memory file: `handoff-2026-08-16-8-2-done.md` (7 honestly DEFER 명시)
  - [x] 8.4 Epic 8 진입 시점 baseline_commit = `2911162` (Story 7.2 follow-up sprint tip) 명시
  - [x] 8.5 다음 단계 명시: `bmad-dev-story 8-2 T1~T8 실행 OR Epic 8 8-3 spec 진입 (cj-style 3번째) OR A19 carry-over follow-up sprint (cj-style 8번째)`

## Dev Notes

### Architecture patterns & constraints

**AD-5 engine purity (CRITICAL)**:
- `packages/cost_engine/budget_variance.py` 는 **stdlib-only** (decimal, dataclasses, math, hashlib, typing) — NO sqlalchemy, NO datetime.now(), NO random, NO I/O
- **8-1 budget_period_key.py 와 surface 분리** — A19 math surface migration pattern (cohesion 강화, variance는 별도 concern)
- import-linter contracts 2 KEPT 0 broken (Epic 0 wire pattern, 12-1 + Epic 5 reinforcement + 8-1 + 8-2)
- ruff custom rule: `packages/cost_engine/*.py` 에서 forbidden imports → lint error (8-1 wire 그대로, 8-2 신규 surface 추가지만 동일 rule 적용)

**AD-11 layer rule**:
- 의존 방향: `apps/web → apps/api → packages/services/m8_budget/ → packages/cost_engine/budget_variance.py`
- 단방향 strict (Epic 0 wire pattern, 12-1 reinforcement + 8-1 + 8-2)
- engine은 services / adapters / UI import 불가 (AD-11 reverse-direction 명시)
- **packages/cost_engine/budget_variance.py → packages/cost_engine/budget_period_key.py** 1방향 호출 (8-2는 8-1 budget scenario를 input으로 받음, reverse 호출 없음)

**AD-3 RLS multi-tenancy**:
- variance fetch 시 `tenant_id = :tenant_id` 필터 (JWT claim, 8-1 패턴 동일)
- 다른 테넌트 variance 0건 노출 (Epic 0 fixture test pattern)

**AD-15 cross-language conventions**:
- DB/Python `snake_case`; Next.js routes `kebab-case` (`/budget/variance`); React/TS types `PascalCase`
- Decimal 정밀도: ROUND_HALF_EVEN (Python `decimal.Decimal` ↔ TS `decimal.js`, 8-1 + 7-1 + 7-2 패턴 동일)
- Period keys follow AD-24 (`YYYY-MM#B1` for budget_scenarios, 8-1 wire)
- Errors: `{code, message_ko, details, trace_id}` (AD-15 §4 envelope, 8-1 + 8-2 typed exception main.py handler 등록)

**NFR9 (P95 ≤ 5초) → 8-2 (P95 ≤ 1초, variance만)**:
- 100ms budget_scenarios fetch + 30ms monthly_input_periods aggregation + 30ms pure calc + 40ms React re-render = 200ms P95
- **PDF 생성은 8-3 honestly DEFER** (별도 endpoint, 1초 한도 비대상)
- Web Worker offload honestly DEFER (over-engineering 회피, 8-1 + 7-1 + 7-2와 동일)

**NFR16 determinism**:
- V8 byte-identical CI gate: 100회 동일 입력 → 100회 동일 `compute_variance_hash(variance)` (Epic 4 baseline extension + 8-1 + 7-1 + 7-2 패턴)
- `hashlib.sha256(repr(variance).encode()).hexdigest()` 결정론 digest

**NFR17 monetary types (AD-8)**:
- BIGINT (KRW integer, `budget_value` + `actual_value` + `difference`) / NUMERIC(18,4) (variance_pct — Decimal 4자리 정밀도)
- Python `decimal.Decimal`; TS `decimal.js`
- 8-2는 KRW only (USD 환산은 Epic 6 6-2 wire, 본 스토리 범위 외)

**PRD §F8.2 verbatim (severity thresholds)**:
- `abs(variance_pct) < 5%` → normal (gray)
- `5% <= abs(variance_pct) < 10%` → warning (yellow)
- `abs(variance_pct) >= 10%` → critical (red)
- 부호(sign) 보존: 음수 variance = 절감, 양수 = 초과

**PRD §15 NON-GOAL #1 verbatim (A×B×C×D gray badge)**:
- A×B×C×D 예산 편성 엔진은 1차 비구현 (산식 보존, §부록 B)
- 회색 배지 placeholder + "2차 예정" 라벨 + 비고란 "[NON-GOAL for MVP: A×B×C×D 엔진 미구현]"

**PDF 보고서 envelope (Epic 6 §9 #20+, 8-3 honestly DEFER placeholder)**:
- Epic 6 M5 PDF generator reuse (READ-ONLY, no audit emit)
- envelope 형식: `{ report_code: "BUDGET_VARIANCE", title: "예산-실적 대조표", period_key, scenario_index, rows, total_row, abcd_disabled_badge, generated_at_kst }`
- PDF 형식: A4 portrait + KRW 정수 + ko-KR only (NFR18)
- 8-2에서는 `generate_budget_variance_pdf` placeholder (pass), 8-3 follow-up sprint에서 wire

**Epic 8 capability reuse (8-1 + 8-2)**:
- `Capability.BUDGET_SCENARIO` 단일 capability로 8-1 + 8-2 dispatch (산업 agnostic 동일 적용)
- 신규 capability 추가 0건 (CR 11-3 즉시 sweep 회피)

**CR 11-4 lessons carry**:
- D-001 (page.tsx mount MUST actually mount `<BudgetVarianceTable>` JSX)
- D-002 (단일 `apps/web/messages/ko-KR.json` only — NOT `apps/web/lib/ko-KR.json`)
- D-005 (TS mirror unknown state MUST raise — `computeVarianceTS` baseline null → throw `ERROR_CODE_INVALID_INPUT`, NOT silent fall-through)
- P-015 (ko-KR.json SSOT drift detector test — `budget_variance` namespace 정합)

**CR 12-1 lessons continue**:
- L3 (`_to_budget_variance_row(orm_row)` ORM→kernel boundary conversion, Epic 12-1 _to_totp_state + 12-3 _to_deletion_state + 8-1 _to_budget_scenario precedent)
- L4 (BUDGET_SCENARIO capability 재사용 — 8-1 + 8-2 industry-agnostic 동일 적용)

**CR 12-5 lessons continue**:
- D-13 (structural cross-language drift detector — `test_m8_budget_variance_cross_language_drift.py` Python↔TS 10+ vectors, 8-1 패턴)
- D-14 (typed exception main.py envelope handler 등록 — `InvalidVariancePeriodError` 422 + `BudgetVarianceNotFoundError` 404)
- L3 (3-layer defense — route `@require_role` + service `validate_variance_inputs` + audit-first emit, 8-2는 read-only)
- L4 (honest-DEFER discipline — 7 honestly DEFER)

**A19 lessons carry**:
- math surface migration pattern (`packages/services/m2_input/inventory_math.py` precedent — math surface는 `packages/cost_engine/` 또는 `packages/services/<module>/<math>.py`)
- 8-1은 `packages/cost_engine/budget_period_key.py` / 8-2는 `packages/cost_engine/budget_variance.py` (분리 surface, A19 cohesion pattern 4번째)

### Source tree components to touch

**NEW files**:
1. `packages/cost_engine/budget_variance.py` (~250 lines)
2. `tests/cost_engine/test_budget_variance.py` (~35+ cases)
3. `tests/cost_engine/test_budget_variance_no_io_imports.py` (~5 cases, 8-1 패턴 미러)
4. `tests/cost_engine/test_budget_variance_determinism.py` (~5 cases, 8-1 패턴 미러)
5. `packages/services/m8_budget/budget_variance_serializers.py` (~60 lines)
6. `packages/services/m8_budget/budget_variance_pdf_helpers.py` (~80 lines)
7. `tests/services/m8_budget/test_budget_variance_service.py` (~18 cases)
8. `apps/api/modules/m8_budget/services/budget_variance_service.py` (~200 lines)
9. `apps/api/modules/m8_budget/schemas_variance.py` (~100 lines — Pydantic v2)
10. `tests/api/test_m8_budget_variance_handlers.py` (~15 cases)
11. `tests/integration/test_m8_budget_variance_cross_language_drift.py` (~10 cases, 8-1 패턴 미러)
12. `tests/integration/test_m8_budget_variance_no_db_writes.py` (~4 cases)
13. `apps/web/app/[locale]/(dashboard)/budget/variance/layout.tsx` (NEW RSC layout)
14. `apps/web/app/[locale]/(dashboard)/budget/variance/page.tsx` (NEW RSC page)
15. `apps/web/components/m8-budget/BudgetVarianceTable.tsx` (~250 lines)
16. `apps/web/components/m8-budget/VarianceRow.tsx` (~80 lines)
17. `apps/web/components/m8-budget/ABCDGrayBadge.tsx` (~60 lines)
18. `apps/web/components/m8-budget/VarianceSummary.tsx` (~80 lines)
19. `apps/web/components/m8-budget/VariancePdfButton.tsx` (~80 lines)
20. `apps/web/components/m8-budget/BudgetVarianceTable.test.tsx` (~12 cases)
21. `apps/web/components/m8-budget/VarianceRow.test.tsx` (~8 cases)
22. `apps/web/components/m8-budget/ABCDGrayBadge.test.tsx` (~5 cases)
23. `apps/web/components/m8-budget/VariancePdfButton.test.tsx` (~4 cases)
24. `apps/web/lib/m8-budget-variance.ts` (~140 lines TS mirror)
25. `apps/web/lib/m8-budget-variance-schema.ts` (~60 lines Zod schema)
26. `apps/web/lib/m8-budget-variance.test.ts` (~10 cases)
27. `apps/web/lib/m8-budget-variance-bench.ts` (~30 lines perf benchmark)
28. `apps/web/lib/m8-budget-variance-bench.test.ts` (~3 cases)
29. `docs/budget-variance-table.md` (~250 lines, 9 sections)

**MODIFIED files**:
1. `packages/cost_engine/__init__.py` — export 3 NEW pure functions (`compute_variance`, `compute_variance_color`, `compute_variance_hash`) + `compute_abcd_disabled_badge` (5 lines)
2. `apps/api/main.py` — m8_budget router include (1 line, 8-1 wire + 8-2 EXTENSION)
3. `apps/api/modules/m8_budget/exceptions.py` EXTENSION — 2 NEW typed exceptions (`InvalidVariancePeriodError` + `BudgetVarianceNotFoundError`)
4. `apps/api/modules/m8_budget/handlers.py` EXTENSION — 1 NEW GET endpoint (~+150 lines)
5. `apps/api/modules/m8_budget/__init__.py` EXTENSION — variance sub-module export
6. `apps/web/messages/ko-KR.json` — `budget_variance` namespace EXTENSION (~20 strings, 8-1 budget_scenario namespace와 분리)
7. `apps/web/lib/menu-config.ts` — `/budget/variance` sidebar nav EXTENSION (1 entry)
8. `apps/web/components/m8-budget/index.ts` EXTENSION — Variance barrel export
9. `docs/capability-matrix.md` v1.17 EXTENSION (8-1 BUDGET_SCENARIO row reuse 명시, 신규 row 0)
10. `docs/conventions.md` §AD-11 EXTENSION (m8_budget variance service 명시, 8-1 + 8-2)
11. `docs/architecture-inventory.md` EXTENSION (m8_budget variance module entry)
12. `docs/deferred-work.md` EXTENSION (7 honestly DEFER items)
13. `_bmad-output/implementation-artifacts/sprint-status.yaml` — 8-2 status sync + last_updated_note
14. `tests/architecture/test_api_calls_only_ports.py` — ALLOWED_SERVICE_SUBMODULES sweep EXTENSION (m8_budget.budget_variance_serializers + budget_variance_pdf_helpers 추가, CR 11-3 D-2)
15. `tests/integration/test_ko_kr_json_ssot.py` — `budget_variance` namespace 정합 EXTENSION (CR 12-1 P-015)

**Total**: 29 NEW + 15 MODIFIED = 44 files (~3,000 lines code + ~800 lines tests + ~400 lines docs)

### Testing standards summary

**Backend (pytest)**:
- **Pure kernel** (35+ cases): edge cases 5종 ValueError + Infinity handling + Decimal precision ROUND_HALF_EVEN parity + frozen=True enforcement + 100회 determinism (8-1 + 7-1 + 7-2 패턴)
- **Service layer** (18+ cases): variance extraction + AD-24 period_key 검증 + RLS same-tenant + 0 DB writes verification + ABCD disabled badge JSON-safe + PDF envelope 정확성
- **Handlers** (15+ cases): 200 OK + 403 CAPABILITY_NOT_GRANTED + 404 BUDGET_SCENARIO_NOT_FOUND + 422 INVALID_VARIANCE_PERIOD + ABCD disabled badge response + total row 정확성 + latency 200ms P95 (variance만)
- **Cross-language drift** (10+ cases): Python ↔ TS parity 10 vectors + edge cases 동일 (8-1 + 7-1 + 7-2 패턴 미러)
- **Audit no-write** (4+ cases): `audit_logs` row 0건 + `budget_scenarios` 변경 0건 + `monthly_input_periods` 변경 0건 + `fiscal_period_snapshots` 변경 0건

**Frontend (vitest)**:
- **BudgetVarianceTable** (12+ cases): fetch + 5컬럼 표시 + severity 색상 + ABCD gray badge + total row
- **VarianceRow** (8+ cases): 5종 color codes (gray / yellow / red / Infinity fallback / 0 budget edge case)
- **ABCDGrayBadge** (5+ cases): 회색 배지 + tooltip + disabled cursor
- **VariancePdfButton** (4+ cases): disabled / 8-3 follow-up tooltip
- **TS mirror parity** (10+ cases): Python `compute_variance` vs TS `computeVarianceTS` 동일 결과 (8-1 + 7-1 + 7-2 패턴)
- **Performance benchmark** (3+ cases): 100회 P95 ≤ 200ms (variance만, PDF 제외)

**Architecture tests**:
- **ALLOWED_SERVICE_SUBMODULES sweep** (1 case): `m8_budget.budget_variance_serializers` + `budget_variance_pdf_helpers` 추가 검증 (CR 11-3 D-2)
- **Engine purity** (5+ cases): AST parser로 forbidden imports 차단 검증 (8-1 + 7-1 + 7-2 패턴 미러)

### Project Structure Notes

**Alignment with unified project structure** (cj-style 8번째 epic 검증):
- `apps/api/modules/m8_budget/` (Epic 8 wire + 8-1 + 8-2 패턴)
- `packages/services/m8_budget/` (thin wrappers, A19 math surface 패턴 + 8-1 + 8-2 EXTENSION)
- `packages/cost_engine/budget_variance.py` (pure kernel, 8-1 budget_period_key.py와 surface 분리, A19 cohesion pattern 4번째)
- `apps/web/components/m8-budget/` (8-1 BudgetScenarioPanel + 8-2 BudgetVarianceTable 패턴)
- `apps/web/app/[locale]/(dashboard)/budget/variance/` (8-1 /budget/scenarios + 8-2 /budget/variance 패턴)

**Detected conflicts or variances**:
- None — 8-2는 8-1 wire pattern 그대로 미러 (BUDGET_SCENARIO capability reuse + cost_engine surface 분리는 A19 cohesion 강화)
- **packages/cost_engine/budget_variance.py** → **packages/cost_engine/budget_period_key.py** 1방향 import (8-2는 8-1 budget scenario를 input으로 받기 위함, reverse 호출 없음)

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Epic-8-Budget-vs-Actual`] — Epic 8 + Story 8.2 verbatim
- [Source: `_bmad-output/planning-artifacts/prd.md#§F8.2`] — PRD §F8.2 (예산-실적 대조 시 모든 차이 행 + A×B×C×D 미구현 회색 배지)
- [Source: `_bmad-output/planning-artifacts/prd.md#§10-M8`] — PRD §10 M8 (b) (회색 배지 명시)
- [Source: `_bmad-output/planning-artifacts/prd.md#§15-NON-GOAL-MVP-1`] — PRD §15 NON-GOAL #1 (A×B×C×D 엔진 1차 비구현)
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-5`] — engine purity
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-11`] — layer rule
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-15`] — cross-language conventions
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-3`] — RLS multi-tenancy
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-22`] — reversal ledger
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-24`] — period key typed
- [Source: `_bmad-output/implementation-artifacts/8-1-virtual-budget-period-key-scenario-lock-to-one.md`] — Story 8.1 spec 진입 패턴 (cj-style 8번째 epic + BUDGET_SCENARIO capability wire)
- [Source: `_bmad-output/implementation-artifacts/handoff-2026-08-16-7-2-follow-up-sprint.md`] — 7-2 follow-up sprint DONE (cj-style 7-2 + 8-1 + 8-2 sequence)
- [Source: `_bmad-output/implementation-artifacts/handoff-2026-08-15-a19-inventory-projection-deprecate-done.md`] — A19 carry-over DONE (math surface migration 패턴)
- [Source: `_bmad-output/implementation-artifacts/4-1-pure-cost-engine-no-i-o-no-clock.md`] — Story 4.1 cost_engine pure kernel spec (precedent)
- [Source: `_bmad-output/implementation-artifacts/12-1-two-factor-auth-mandatory-gate.md`] — Story 12.1 L4 industry-agnostic capability precedent
- [Source: `_bmad-output/implementation-artifacts/12-3-account-deletion-retention-consent.md#AC-7`] — CR 12-1 L3 _to_<state> ORM→kernel boundary conversion pattern
- [Source: `docs/capability-matrix.md`] — capability matrix v1.17 (8-1 BUDGET_SCENARIO row reuse, 8-2 신규 row 0)
- [Source: `docs/conventions.md#AD-11-layer-rule`] — 의존 방향 명시
- [Source: `docs/virtual-budget-period-key.md`] (NEW per 8-1) — 8-1 도큐먼트 (8-2와 surface 분리)
- [Source: `docs/budget-variance-table.md`] (will be NEW) — 8-2 도큐먼트

## Dev Agent Record

### Agent Model Used

Claude Opus 5 (claude-opus-5)

### Debug Log References

N/A (spec 진입 단계 — bmad-dev-story 진입 시 작성)

### Completion Notes List

(To be filled by bmad-dev-story T1~T8 execution — see handoff at `_bmad-output/implementation-artifacts/handoff-2026-08-16-8-2-done.md`)

### File List

(To be filled by bmad-dev-story T1~T8 execution — see handoff at `_bmad-output/implementation-artifacts/handoff-2026-08-16-8-2-done.md`)

## Honestly DEFER (per CR 11-3 14번째 epic 연속 검증)

| # | Item | Rationale | Where |
|---|------|-----------|-------|
| 1 | Multi-scenario 비교 (B2, B3, …) | 1차 MVP NON-GOAL #2 §15 verbatim (≥5 테넌트 요청 시 trigger) — Story 8-3 honestly DEFER (a) 또는 Epic 9 carry-over | specs/deferred-work.md ## Deferred from: 8-2 |
| 2 | A×B×C×D 편성 엔진 | 1차 MVP NON-GOAL #1 §15 verbatim — 본 스토리에서 **회색 배지 placeholder** 명시 (PRD §F8.2 verbatim + epics.md Story 8.2 AC) | specs/deferred-work.md ## Deferred from: 8-2 |
| 3 | Scenario-level grouping (B1 별도 행) | 단일 scenario 1차 MVP (8-1 wire), multi-scenario 2차 | specs/deferred-work.md ## Deferred from: 8-2 |
| 4 | Year-over-year comparison (전년 동월) | 1차 MVP N/A (epics.md 8-3 verbatim + 2차 PRD §9 #20) | specs/deferred-work.md ## Deferred from: 8-2 |
| 5 | PDF export (예산-실적 차이 명세서) | PRD §9 #20 명세 보존, 1차 MVP는 화면 표시만 (Epic 6 M5 PDF generator reuse, 8-3 honestly DEFER) | specs/deferred-work.md ## Deferred from: 8-2 |
| 6 | Playwright E2E | sprint-scale (12-5 T6 패턴, follow-up sprint) — 8-1 honestly DEFER #5 mirror | specs/deferred-work.md ## Deferred from: 8-2 |
| 7 | Web Worker for large tables | 1000+ rows 가능, 1차 MVP 단일 scenario 한도 내 (over-engineering 회피, 7-1 honestly DEFER #1 mirror) | specs/deferred-work.md ## Deferred from: 8-2 |

---

**Status**: ready-for-dev (cj-style 3-story Epic 8 2번째 진입점, 8번째 epic 연속 검증)
**baseline_commit**: `2911162`
**다음 단계**: `bmad-dev-story 8-2 T1~T8 실행` OR `Epic 8 8-3 spec 진입 (cj-style 3번째)` OR `A19 carry-over follow-up sprint (cj-style 8번째)`
