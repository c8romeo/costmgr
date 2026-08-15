---
title: 'Epic 7 Story 1 — BEP Slider with 1-Second Recompute (CVP 시뮬레이션 + 순수 엔진 함수 + 슬라이더 디바운스)'
status: ready-for-dev
priority: HIGH
epic: 7
story_num: 1
story_key: 7-1-bep-slider-1-second-recompute
baseline_commit: a63646c
created: 2026-08-15
updated: 2026-08-15
---

> **2026-08-15 — bmad-create-story spec 진입 done** (7-1: backlog → ready-for-dev). **Epic 7 진입 첫 스토리** (cj-style 3-story 분할 6번째 epic 연속 검증 — Epic 4·5·6·11·12 + Epic 11/12 carry-over). 7-1 (BEP slider) / 7-2 (차월 추정 4종 파라미터) / 7-3 (Epic 7 close-out retro §7 신규 결정 시).
>
> **baseline_commit = `a63646c`** (Story 12.3 T7 follow-up sprint + Epic 12 진짜 close-out tip — current HEAD).
>
> **A19 carry-over sprint DONE** (2026-08-15) — Epic 6 retro §7 A8 inline projection deprecate 완료 + `packages/services/m2_input/inventory_math.py` math surface 마이그레이션 완료. **Epic 7 진입 gate clear**.
>
> **Three user decisions locked** (2026-08-15):
> 1. **순수 엔진 함수 surface = `packages/cost_engine/cvp.py`** (stdlib-only AD-5 purity) — `compute_bep(*, fixed_cost, unit_variable_cost, unit_price) -> BEPResult` + `compute_target_profit(*, target_profit, fixed_cost, unit_variable_cost, unit_price) -> TargetProfitResult` + `simulate_cvp(*, baseline_cvp, delta: CVPDelta) -> CVPResult` (3 NEW pure functions, A19 math surface 패턴 미러). **DB / clock / random / I/O 일체 없음** (AD-5 + AD-11 layer rule + import-linter 2 KEPT contracts 유지).
> 2. **Frontend 디바운싱 + Web Worker offload (optional)** — 1초 이내 응답 보장을 위해 슬라이더 onChange 이벤트에 100~200ms `lodash.debounce` (or React `useDeferredValue`) 적용 + 계산은 메인 스레드 동기 함수 (cost가 충분히 작음). **Web Worker optional** (Epic 5 A4 carry-over 패턴 — over-engineering 회피, MVP는 메인 스레드).
> 3. **Capability gate = 신규 `Capability.CVP_SIMULATION`** — manufacturing 3종 ✅ / service-only ✅ (전 industry 공통, AD-21 단일 CCR 패턴 + 12-1 L4 industry-agnostic precedent). `apps/api/core/capability.py` 추가 + `apps/api/modules/m7_simulation/` module authority 신규.
>
> **cj-style 3-story 분할 6번째 epic 연속 검증** + **CR 11-3 honest-DEFER discipline 9번째 epic 연속** (atomic wire만, partial wire 0).
>
> **A19 lessons carry-over**: math surface migration pattern (CR A19 NEW) + `packages/services/m2_input/inventory_math.py` 신규 math surface home post-deprecate. 7-1은 **`packages/cost_engine/cvp.py`** (cost_engine surface — Epic 4 pure calc engine과 동일 layer), `packages/services/m7_simulation/` 는 service layer (orchestration 없이 thin wrappers).
>
> **CR 11-4 lessons carry-over**: D-001 (page.tsx mount MUST actually mount) + D-002 (단일 `apps/web/messages/ko-KR.json` only) + D-005 (TS mirror unknown state fall-through → reject) + P-015 (ko-KR.json SSOT drift detector test).
>
> **CR 12-1 lessons continue applied**: L1 (PyJWT `verify_exp=False` deterministic testability — N/A for 7-1, no token) + L2 (AES-256-GCM lazy wrapper — N/A for 7-1, no PII) + L3 (`_to_cvp_state(...)` ORM→kernel boundary conversion, 7-1은 baseline fetch 후 pure kernel call) + L4 (CVP_SIMULATION capability industry-agnostic precedent).
>
> **CR 12-5 lessons continue applied**: D-13 (cross-language drift detector pattern) + L4 (honest-DEFER discipline).
>
> **Honestly DEFER (per CR 11-3, partial wire 아님)**:
> - **Web Worker offload** (1초 응답 미달 시 추가 최적화) — 현재 메인 스레드 디바운싱으로 충분.
> - **Monte Carlo sensitivity 분석** — 단일 변수 슬라이더만, multi-variate는 Epic 7 close-out retro §7 신규 결정 시 (7-3).
> - **AI 추천 가격 제안** — Epic 10 carry-over, F10.1 input_drafts 우회 필수.
> - **차월 추정 4종 파라미터** — Story 7-2.
> - **TS mirror cross-language drift detector test** — sprint-scale (parity test 5~10 cases로 atomic wire).
> - **Playwright E2E** — sprint-scale (12-5 T6 패턴, follow-up sprint).

# Story 7.1 — BEP Slider with 1-Second Recompute

## Epic 7 context

**Epic 7 (CVP/BEP Simulation)** cj-style 3-story 분할 진입 (Epic 4·5·6·11·12 검증 패턴 6번째 epic):

- **7-1** = BEP Slider with 1-Second Recompute (PRD §F7.1 + NFR9 1초 응답 + AD-5 engine purity) ← **이 스토리** (backlog → ready-for-dev)
- **7-2** = Next-Month Projection with 4 Required Parameters (PRD §F7.2)
- **7-3** = Epic 7 close-out retro §7 (cj-style A14 권장안 (a) — 신규 결정 시)

**Epic 7 모듈 authority**: `apps/api/modules/m7_simulation/` (신설, 12-1 m12_account / Epic 11 m11_close / Epic 4 m3_calculate 패턴 미러). 본 스토리 = 1 GET endpoint + 1 POST endpoint (snapshot dispatch).

**Epic 7 capability matrix wire**: v1.16 `CVP_SIMULATION` 신규 (manufacturing 3종 ✅ + service-only ✅ = industry-agnostic, 12-1 L4 precedent — "CVP는 tenant-level 재무 시뮬레이션 baseline").

**Epic 7 NFR coverage**: NFR9 (P95 ≤ 5초 — 단일 계산 기준; 7-1은 더 엄격한 1초 이내 — 슬라이더 응답성) + NFR16 (엔진 순수성 — AD-5) + NFR17 (monetary types — AD-8).

## Why this story (atomic wire 결정 근거)

**PRD §F7.1 verbatim**: "슬라이더 변경 시 BEP 수량·목표이익을 1초 이내 재계산."

**epics.md Story 7.1 AC verbatim** (lines 935-939):
> **Given** 나는 [시뮬레이션] 화면에서 "단가" 슬라이더를 10,000원 → 12,000원으로 드래그
> **When** 마우스 떼는 순간
> **Then** 1초 이내에 "BEP 수량: 1,500개 → 1,250개" "예상 이익: 500만원 → 800만원" 카드 갱신
> **And** 시뮬레이션은 DB를 건드리지 않음 — 순수 엔진 함수(`simulate_cvp` 등)만 호출
> **And** Recharts 막대 차트가 실시간으로 변동 (현재 시나리오 vs 베이스라인)

**3 second-order decisions** (locked 2026-08-15):

1. **Pure kernel = `packages/cost_engine/cvp.py`** (Epic 4 cost_engine surface 패턴 미러): AD-5 (엔진 순수성) + AD-11 layer rule + A19 math surface migration 패턴. **`packages/cost_engine/` 가 SSOT** (Story 4-1 spec 확정). `packages/services/m7_simulation/` 는 thin orchestration wrappers (CR 11-3 D-2 ALLOWED_SERVICE_SUBMODULES sweep 즉시 + CR 11-1 RSC boundary / FastAPI ContextVar / BigInteger / JSONB lessons carry). **stdlib-only**: `import decimal, dataclasses, math` only (no sqlalchemy, no datetime.now, no random).

2. **Frontend 디바운싱 100~200ms** (CR 11-4 lessons carry + Epic 5 W2 deprecation 패턴): 슬라이더 onChange 이벤트는 `useDeferredValue` (React 19) 또는 `lodash.debounce` 150ms 적용. 계산 자체는 메인 스레드 동기 (cost_engine pure function은 충분히 빠름 — input 5개 변수 + 곱셈 나눗셈 수준, V8 byte-identical 보장 + Epic 4 V8 regression 패턴과 동일). **Web Worker offload는 honestly DEFER** — over-engineering 회피.

3. **Capability gate = `Capability.CVP_SIMULATION` industry-agnostic** (12-1 L4 precedent — "모든 tenant에 적용되는 재무 baseline"): `manufacturing` / `manufacturing_with_trading` / `manufacturing_with_service` / `service_only` 모두 ✅ grant. `apps/api/core/capability.py` 추가 + `apps/api/modules/m7_simulation/handlers.py` `@require_capability(CVP_SIMULATION)` decorator.

**+ Epic 7 close-out path**: 7-1 done 진입 후 7-2 spec 진입 (cj-style 2번째) → 7-3 close-out retro.

## User Story

As a **사장님**,
I want **단가·원가·조업도 슬라이더를 흔들면 BEP 수량과 목표이익이 1초 안에 갱신되고 베이스라인과 비교되는 것**,
so that **F7.1 (가격 인상 전 미리 손익분기점 확인) + NFR9 (1초 이내 응답성) + AD-5 (엔진 순수성으로 V8 회귀 가능) + AD-11 (의존 방향 일관성) 모두 만족**.

(PRD §F7.1 + epics.md Story 7.1 verbatim + NFR9·16·17 + AD-5·8·11·18 + Epic 7 cj-style 진입점)

## Acceptance Criteria

### AC #1 — 순수 엔진 함수 surface `packages/cost_engine/cvp.py` (epics.md AC #2 verbatim + AD-5 + NFR16)

- **Given** AD-5 엔진 순수성 + AD-11 layer rule + NFR16 V8 회귀 가능
- **When** `packages/cost_engine/cvp.py` 신규 작성
- **Then** `compute_bep(*, fixed_cost: Decimal, unit_variable_cost: Decimal, unit_price: Decimal) -> BEPResult`:
  - `BEPResult = dataclass(frozen=True)` with `bep_quantity: Decimal`, `bep_revenue: Decimal`, `contribution_margin_per_unit: Decimal`, `contribution_margin_ratio: Decimal`
  - 공식: `bep_quantity = fixed_cost / (unit_price - unit_variable_cost)` (정상범위 — `unit_price > unit_variable_cost`)
  - `bep_revenue = bep_quantity * unit_price`
  - `contribution_margin_per_unit = unit_price - unit_variable_cost`
  - `contribution_margin_ratio = (unit_price - unit_variable_cost) / unit_price` (Decimal 분수, ROUND_HALF_EVEN)
  - **Edge cases**:
    - `unit_price <= unit_variable_cost` → `ValueError("unit_price must exceed unit_variable_cost")` raise (정상범위 외)
    - `fixed_cost == 0` → `bep_quantity = 0`, `bep_revenue = 0` (trivially break-even)
    - `fixed_cost < 0` → `ValueError("fixed_cost must be non-negative")`
  - **Determinism**: 100회 동일 입력 호출 → 100회 모두 byte-identical `BEPResult` (V8 회귀 가능)
  - **Purity**: `import decimal, dataclasses, math` only (AD-5 + import-linter + ruff custom rule)
- **And** `compute_target_profit(*, target_profit: Decimal, fixed_cost: Decimal, unit_variable_cost: Decimal, unit_price: Decimal) -> TargetProfitResult`:
  - `TargetProfitResult = dataclass(frozen=True)` with `target_quantity: Decimal`, `target_revenue: Decimal`
  - 공식: `target_quantity = (fixed_cost + target_profit) / (unit_price - unit_variable_cost)`
  - **Edge cases** (동일):
    - `unit_price <= unit_variable_cost` → `ValueError`
    - `target_profit < 0` → `ValueError("target_profit must be non-negative")`
- **And** `simulate_cvp(*, baseline: CVPBaseline, delta: CVPDelta) -> CVPResult`:
  - `CVPBaseline = dataclass(frozen=True)` with `fixed_cost: Decimal`, `unit_variable_cost: Decimal`, `unit_price: Decimal`, `operating_rate: Decimal` (0.0 ~ 1.5, default 1.0)
  - `CVPDelta = dataclass(frozen=True)` with `unit_price_delta_pct: Decimal = Decimal("0")`, `unit_variable_cost_delta_pct: Decimal = Decimal("0")`, `fixed_cost_delta_pct: Decimal = Decimal("0")`, `operating_rate_delta_pct: Decimal = Decimal("0")`
  - `CVPResult = dataclass(frozen=True)` with `simulated_bep: BEPResult`, `simulated_target_profit: TargetProfitResult`, `baseline_bep: BEPResult`, `baseline_target_profit: TargetProfitResult`, `delta_summary: dict[str, Decimal]` (4 NEW delta percentages computed)
  - 내부적으로 `apply_delta(baseline, delta)` → `simulated = CVPBaseline(...)` → `compute_bep(simulated)` + `compute_target_profit(simulated, target_profit=baseline.target_profit)`
  - **`baseline`은 NOT mutated** (frozen=True + copy semantics)
- **And** **stdlib-only import 검증**:
  - `tests/cost_engine/test_cvp_no_io_imports.py` (NEW) — AST parser로 `cost_engine/cvp.py` 의 import whitelist 검증 (`decimal`, `dataclasses`, `math` 만 허용, `os, time, random, requests, sqlalchemy, datetime` 모두 차단)
  - ruff custom rule: `packages/cost_engine/` 내 `import os|time|random|requests|sqlalchemy` → lint error
  - import-linter 2 KEPT contracts 유지 (Epic 0 + 12-1 wire pattern)

### AC #2 — 1초 이내 응답 (epics.md AC #1 verbatim + NFR9 + AD-11)

- **Given** 슬라이더 드래그 시 1초 이내 BEP 카드 + Recharts 갱신
- **When** 사용자가 "단가" 슬라이더 10,000원 → 12,000원으로 드래그
- **Then** 마우스 떼는 순간 **150ms 이내** (debounce) + **10ms 이내 계산** (pure kernel) + **50ms 이내 React re-render** = **총 210ms P95** (1초 한도 대비 5배 여유)
- **And** BEP 카드 갱신:
  - "BEP 수량: 1,500개 → 1,250개" (단가 인상 → 손익분기점 낮아짐)
  - "예상 이익: 500만원 → 800만원" (현재 조업도 기준)
- **And** Recharts 막대 차트 실시간 변동:
  - X축: ["단가", "단위변동비", "고정비", "조업도"]
  - Y축: BEP 수량 (왼쪽 막대 baseline, 오른쪽 막대 simulated)
  - 4 variables 동시 비교 (color-coded: baseline=slate-500, simulated=blue-500)
- **And** **순수 엔진 함수만 호출** — DB 호출 0건 (network panel verification, MSW intercept 0 호출)
- **And** **응답 시간 측정**:
  - `apps/web/lib/m7-simulation-bench.ts` (NEW) — `performance.now()` before/after, P95 ≤ 200ms assertion
  - vitest `tests/web/lib/m7-simulation-bench.test.ts` (NEW) — 100회 측정 P95 ≤ 200ms

### AC #3 — Capability gate + industry-agnostic + RLS (AD-3·10·21 + 12-1 L4 precedent)

- **Given** AD-3 RLS multi-tenancy + AD-10 4-role + AD-21 단일 CCR + 12-1 L4 industry-agnostic
- **When** `Capability.CVP_SIMULATION` wire
- **Then** `apps/api/core/capability.py` EXTENSION:
  - `CVP_SIMULATION = "cvp_simulation"` 신규 추가 (Industry enum 4종 모두 ✅ grant: `manufacturing` / `manufacturing_with_trading` / `manufacturing_with_service` / `service_only`)
  - 12-1 L4 precedent: "CVP는 tenant-level 재무 baseline — 모든 industry에 동일 적용"
- **And** `apps/api/modules/m7_simulation/handlers.py` EXTENSION:
  - `POST /api/v1/simulation/cvp/compute` — `@require_capability(CVP_SIMULATION)` decorator
  - `GET /api/v1/simulation/cvp/baseline?period_key=YYYY-MM` — same decorator
  - `require_role("owner", "member", "viewer", "consultant_proxy")` 모두 허용 (AD-10 4-role 모두 — CVP는 read-only 시뮬레이션)
- **And** **CVP baseline data source**:
  - `fiscal_period_snapshots` (`state='committed'` 또는 `state='verified'`) + `monthly_input_periods` JOIN으로 baseline CVP 추출 (latest `period_key`)
  - **`monthly_input_periods` + `products` + `tenant_settings` aggregation** (pure read query, NO mutation)
  - baseline 추출 후 `packages/cost_engine/cvp.py` pure function 호출 (AD-5)
- **And** **RLS same-tenant filter**:
  - `tenant_id` JWT claim → `WHERE tenant_id = :tenant_id` (AD-3 standard pattern)
  - 다른 테넌트 baseline 0건 노출 (Epic 0 RLS verification pattern)
- **And** `docs/capability-matrix.md` v1.16 — `Capability.CVP_SIMULATION` row 신규 + 4 industries ✅ 마킹

### AC #4 — Frontend `/simulation/cvp` RSC + 슬라이더 + Recharts + ko-KR SSOT (epics.md AC #1·3 + CR 11-4 D-001·D-002)

- **Given** [시뮬레이션] 화면 + 슬라이더 + Recharts + ko-KR.json SSOT
- **When** `apps/web/app/[locale]/(dashboard)/simulation/cvp/{layout,page}.tsx` NEW RSC
- **Then** **RSC page** (`page.tsx`):
  - `apps/web/components/m7-simulation/CVPSimulationClient.tsx` (NEW client component) mount
  - **CR 11-4 D-001 actual mount MUST**: `<CVPSimulationClient>` JSX return (NOT just create file)
- **And** **CVPSimulationClient** (client component, 4 NEW):
  - **CVPSimulationClient.tsx** — main client orchestrator
    - state: `{ baseline: CVPBaseline, delta: CVPDelta, result: CVPResult | null, isComputing: boolean }`
    - onMount: `GET /api/v1/simulation/cvp/baseline?period_key=2026-07` → baseline set
    - onSliderChange → `setDelta(new_delta)` → debounced (150ms) → `simulate_cvp(baseline, delta)` 호출
    - 4 cards: BEP 수량 / BEP 매출 / 목표 이익 / 기여이익률
    - 1 Recharts `BarChart` (current vs baseline)
    - 4 sliders: 단가 (±50%), 단위변동비 (±50%), 고정비 (±30%), 조업도 (50%~150%)
  - **CVPSlider.tsx** (NEW) — shadcn Slider + decimal-aware
    - props: `{ label: string, min: number, max: number, step: number, value: number, onChange: (v: number) => void, suffix: string }`
    - ko-KR: "단가 (원)" / "단위변동비 (원)" / "고정비 (원)" / "조업도 (%)"
  - **CVPResultCard.tsx** (NEW) — 단일 결과 카드
    - props: `{ title: string, beforeValue: string, afterValue: string, isImproved: boolean }`
    - 화살표 표시 (↑ 개선 / ↓ 악화 / = 동일)
  - **CVPComparisonChart.tsx** (NEW) — Recharts BarChart
    - baseline vs simulated 4 variables 비교
- **And** **ko-KR.json** SSOT (CR 11-4 D-002 단일 `apps/web/messages/ko-KR.json` only):
  - 1 NEW namespace `cvp_simulation` (~15 strings: page_title, slider_unit_price, slider_unit_variable_cost, slider_fixed_cost, slider_operating_rate, card_bep_quantity, card_bep_revenue, card_target_profit, card_contribution_margin_ratio, label_baseline, label_simulated, label_delta_pct, button_reset, button_compare_baseline, toast_error_no_baseline, etc.)
- **And** **TS mirror** (`apps/web/lib/m7-simulation-cvp.ts`):
  - `CVPBaseline`, `CVPDelta`, `CVPResult`, `BEPResult`, `TargetProfitResult` TS interfaces
  - `simulateCvpTS(baseline, delta): CVPResult` — TypeScript re-implementation (V8 cross-language parity)
  - `apps/web/lib/cvp.ts` 또는 `apps/web/lib/m7-simulation-cvp.ts` 단일 SSOT (CR 11-4 D-002 — `lib/` 디렉터리는 ko-KR.json SSOT 안 됨, ko-KR.json only)
- **And** **디바운싱 + Web Worker honestly DEFER**:
  - React `useDeferredValue` 또는 `lodash.debounce` 150ms (CR 11-4 patterns carry)
  - Web Worker offload honestly DEFER (1초 한도 대비 5배 여유 — over-engineering 회피)

### AC #5 — Cross-language drift detector (CR 12-5 D-13 + 12-1 P-015 ko-KR.json drift)

- **Given** AD-15 cross-language conventions + CR 12-5 D-13 structural drift detector
- **When** 7-1 wire
- **Then** **`tests/integration/test_m7_simulation_cross_language_drift.py`** (NEW):
  - **Python ↔ TS parity test**: `simulate_cvp` Python vs `simulateCvpTS` TypeScript 10+ vectors
    - 동일 baseline + delta → 동일 result (`bep_quantity`, `bep_revenue`, `target_quantity`, `target_revenue`, `contribution_margin_ratio`)
    - Decimal 정밀도 round-trip (TS `decimal.js` ↔ Python `decimal.Decimal`)
    - Edge cases: `unit_price = unit_variable_cost` → 동일 `ValueError`
  - **ko-KR.json SSOT drift detector** (CR 12-5 L4 + 12-1 P-015):
    - `tests/integration/test_ko_kr_json_ssot.py` EXTENSION — `cvp_simulation` namespace 정합
    - frontend i18n key가 `apps/web/messages/ko-KR.json` 에만 존재 (NOT `apps/web/lib/ko-KR.json`)
- **And** **no external state mutation**:
  - `tests/integration/test_m7_simulation_no_db_writes.py` (NEW) — 시뮬레이션 호출 후 `audit_logs` row 0건 (CR 1.1 invariant — simulation = read-only)
- **And** **V8 byte-identical CI gate 패턴** (Epic 4 회귀 — Epic 4 baseline extension):
  - `tests/cost_engine/test_cvp_determinism.py` (NEW) — 100회 동일 입력 byte-identical `result_hash` (`hashlib.sha256` over `repr(result)`)

### AC #6 — AD-11 layer rule + ALLOWED_SERVICE_SUBMODULES sweep + AD-2 audit-first (epics.md AC #2 + AD-2·5·11 + CR 11-3 D-2)

- **Given** AD-11 layer rule (`ui → api → services → ports → engine`) + AD-2 append-only + CR 11-3 D-2 ALLOWED_SERVICE_SUBMODULES
- **When** 7-1 wire
- **Then** **AD-11 layer rule 검증**:
  - `apps/api/modules/m7_simulation/services/cvp_simulation_service.py` (NEW service layer)
  - `packages/services/m7_simulation/` (NEW thin wrappers — `apply_delta`, `serialize_baseline`, `serialize_result`)
  - `packages/cost_engine/cvp.py` (pure kernel, stdlib-only)
  - **의존 방향**: `apps/api → packages/services/m7_simulation/ → packages/cost_engine/cvp.py` (단방향, AD-11)
  - **import-linter contracts**: 2 KEPT 0 broken (Epic 0 + 12-1 wire pattern)
- **And** **ALLOWED_SERVICE_SUBMODULES sweep** (CR 11-3 D-2 즉시):
  - `tests/architecture/test_api_calls_only_ports.py` EXTENSION — `packages.services.m7_simulation` 추가
- **And** **AD-2 audit-first invariant** (CR 1.1):
  - `simulation_cvp_computed` audit emit (선택적 — read-only operation은 audit skip 가능, 단 옵트인 telemetry)
  - **AC #5 test_m7_simulation_no_db_writes로 보장** — audit_logs row 0건 (read-only operation 명시)
- **And** **frontend telemetry**:
  - `cvp_simulation_viewed` analytics event (PostHog or similar — Epic 10 carry-over, honestly DEFER 시 mock)
  - 본 스토리 범위 외 (honestly DEFER)

## Tasks / Subtasks (atomic wire)

### Task 1 — Pure kernel (CVP math surface)

- **AC**: #1
- **파일**: `packages/cost_engine/cvp.py` (NEW, ~200 lines)
- **subtasks**:
  - [ ] 1.1 STDIN-only: `import decimal, dataclasses, math` only (AD-5 purity + import-linter)
  - [ ] 1.2 `class BEPResult(frozen=True)` with 4 fields: `bep_quantity: Decimal`, `bep_revenue: Decimal`, `contribution_margin_per_unit: Decimal`, `contribution_margin_ratio: Decimal`
  - [ ] 1.3 `class TargetProfitResult(frozen=True)` with 2 fields: `target_quantity: Decimal`, `target_revenue: Decimal`
  - [ ] 1.4 `class CVPBaseline(frozen=True)` with 5 fields: `fixed_cost`, `unit_variable_cost`, `unit_price`, `operating_rate`, `target_profit`
  - [ ] 1.5 `class CVPDelta(frozen=True)` with 4 fields + defaults (Decimal("0"))
  - [ ] 1.6 `class CVPResult(frozen=True)` with 4 fields: `simulated_bep`, `simulated_target_profit`, `baseline_bep`, `baseline_target_profit`, `delta_summary`
  - [ ] 1.7 `def compute_bep(*, fixed_cost: Decimal, unit_variable_cost: Decimal, unit_price: Decimal) -> BEPResult` — 공식 + edge cases
  - [ ] 1.8 `def compute_target_profit(*, target_profit: Decimal, fixed_cost: Decimal, unit_variable_cost: Decimal, unit_price: Decimal) -> TargetProfitResult` — 공식 + edge cases
  - [ ] 1.9 `def apply_delta(baseline: CVPBaseline, delta: CVPDelta) -> CVPBaseline` — 4 variables delta 적용 (immutable, return new instance)
  - [ ] 1.10 `def simulate_cvp(*, baseline: CVPBaseline, delta: CVPDelta) -> CVPResult` — `apply_delta` + `compute_bep` + `compute_target_profit` orchestration
  - [ ] 1.11 `def compute_bep_hash(result: BEPResult | CVPResult) -> str` — `hashlib.sha256(repr(result).encode()).hexdigest()` 결정론 digest (V8 회귀용)
- **tests**: `tests/cost_engine/test_cvp.py` (NEW, 30+ cases):
  - `compute_bep` 정상범위 + edge cases (3종 ValueError)
  - `compute_target_profit` 정상범위 + edge cases (3종 ValueError)
  - `apply_delta` immutable (baseline not mutated)
  - `simulate_cvp` 4 variables delta 적용 + delta_summary 정확성
  - `compute_bep_hash` 결정론 (RFC test vector)
  - `frozen=True` enforcement (mutation 시도 → FrozenInstanceError)
  - Decimal precision: ROUND_HALF_EVEN parity (TS decimal.js 동일)
  - 100회 determinism test (byte-identical hash)

### Task 2 — Engine purity gate (AD-5 + import-linter + ruff custom rule)

- **AC**: #1
- **파일**: `tests/cost_engine/test_cvp_no_io_imports.py` (NEW), `pyproject.toml` EXTENSION (ruff custom rule)
- **subtasks**:
  - [ ] 2.1 `test_cvp_no_io_imports.py` AST parser 검증:
    - `cost_engine/cvp.py` 의 import whitelist: `decimal, dataclasses, math, hashlib, typing` (CR 12-1 L1 pattern)
    - forbidden: `os, time, random, requests, sqlalchemy, datetime, json, urllib` 모두 차단
  - [ ] 2.2 ruff custom rule (or pre-commit hook):
    - `packages/cost_engine/*.py` 에서 `import os | import time | import random | import requests | import sqlalchemy | import datetime` → lint error
  - [ ] 2.3 `import-linter` contracts 유지:
    - `cost_engine_forbidden_io` (Epic 0 wire) — 1 KEPT 0 broken
    - `engine_core_to_adapters_forbidden` (Epic 0 wire) — 1 KEPT 0 broken

### Task 3 — Service layer (thin wrappers + baseline fetch)

- **AC**: #3, #6
- **파일**: `apps/api/modules/m7_simulation/services/cvp_simulation_service.py` (NEW, ~150 lines)
- **subtasks**:
  - [ ] 3.1 `class CVPSimulationService` with `__init__(session, *, tenant_id, actor_id, trace_id)` (12-2 BackupExportService precedent)
  - [ ] 3.2 `async def fetch_cvp_baseline(self, *, period_key: str) -> CVPBaseline`:
    - SELECT `monthly_input_periods` + `fiscal_period_snapshots` JOIN (latest `period_key`, `state IN ('committed', 'verified')`)
    - aggregate: `fixed_cost = SUM(overhead_cost)`, `unit_variable_cost = AVG(unit_variable_cost)`, `unit_price = AVG(unit_price)`, `operating_rate = AVG(operating_rate)`, `target_profit = fiscal_period_snapshots.target_profit`
    - RLS same-tenant filter (`tenant_id = :tenant_id`)
    - Return `CVPBaseline`
  - [ ] 3.3 `async def simulate_cvp(self, *, baseline: CVPBaseline, delta: CVPDelta) -> CVPResult`:
    - delegate to `packages/cost_engine/cvp.py:simulate_cvp` (pure kernel)
    - no DB writes, no audit emit (read-only operation, AC #5 보장)
    - Return `CVPResult`
- **파일**: `packages/services/m7_simulation/` (NEW thin wrappers):
  - [ ] 3.4 `__init__.py` — module init
  - [ ] 3.5 `serializers.py` — `serialize_cvp_baseline`, `serialize_cvp_result` (dataclass → dict, JSON-safe Decimal)
  - [ ] 3.6 `delta_helpers.py` — `clamp_delta(delta)`, `validate_delta_bounds(delta)` (sliders min/max enforcement)
- **tests**: `tests/services/m7_simulation/test_cvp_simulation_service.py` (NEW, 15+ cases):
  - `fetch_cvp_baseline` baseline extraction 정확성 (latest period_key 우선)
  - `fetch_cvp_baseline` no baseline → `CVPBaselineNotFoundError` raise
  - `fetch_cvp_baseline` RLS same-tenant (다른 tenant_id 0건)
  - `simulate_cvp` pure kernel delegation
  - `serializers` JSON-safe Decimal
  - `delta_helpers` clamp + validate

### Task 4 — HTTP routes + capability gate + main.py wire

- **AC**: #3, #6
- **파일**: `apps/api/modules/m7_simulation/handlers.py` (NEW, ~120 lines)
- **subtasks**:
  - [ ] 4.1 `POST /api/v1/simulation/cvp/compute`:
    - Request: `CVPSimulationRequest(period_key: str, delta: CVPDeltaRequest)`
    - `@require_capability(CVP_SIMULATION)` decorator
    - `require_role("owner", "member", "viewer", "consultant_proxy")` 모두 허용
    - Service: `fetch_cvp_baseline(period_key)` → `simulate_cvp(baseline, delta)`
    - Response: `CVPSimulationResponse(baseline, delta, result, latency_ms: int)`
    - 200 OK + Decimal-as-string (JSON-safe, AD-15)
  - [ ] 4.2 `GET /api/v1/simulation/cvp/baseline?period_key=YYYY-MM`:
    - `@require_capability(CVP_SIMULATION)` decorator
    - Service: `fetch_cvp_baseline(period_key)` only
    - Response: `CVPBaselineResponse(baseline, period_key, source_period_key, fiscal_period_state)`
- **파일**: `apps/api/main.py` EXTENSION:
  - [ ] 4.3 `m7_simulation` router include (Epic 11 m11_close + 12-1 m12_account wire pattern)
- **파일**: `apps/api/core/capability.py` EXTENSION:
  - [ ] 4.4 `CVP_SIMULATION = "cvp_simulation"` 신규 + 4 industries grant (industry-agnostic, 12-1 L4 precedent)
- **파일**: `apps/api/core/audit_action.py` EXTENSION:
  - [ ] 4.5 (선택) `simulation_cvp_computed` audit action 추가 — ActionClass.SIMULATION 신규 1 value fill (CR 11-3 D-2 sweep)
- **파일**: `docs/capability-matrix.md` EXTENSION:
  - [ ] 4.6 v1.16 — `Capability.CVP_SIMULATION` row 신규 + 4 industries ✅ 마킹
- **tests**: `tests/api/test_m7_simulation_handlers.py` (NEW, 12+ cases):
  - `POST /api/v1/simulation/cvp/compute` 정상 (200 + Decimal-as-string)
  - `POST /api/v1/simulation/cvp/compute` no capability → 403 CAPABILITY_NOT_GRANTED
  - `POST /api/v1/simulation/cvp/compute` no baseline → 404 CVP_BASELINE_NOT_FOUND
  - `GET /api/v1/simulation/cvp/baseline?period_key=invalid` → 422 INVALID_PERIOD_KEY
  - latency measurement: 200ms P95 assertion (성능 검증)
  - AD-15 envelope contract (4 fields: code, message_ko, details, trace_id)

### Task 5 — Alembic + RLS (N/A — no schema 변경)

- **AC**: N/A (no schema 변경)
- **note**: 7-1은 **순수 read + pure kernel** — Alembic migration 불요, RLS 신규 정책 불요 (기존 `fiscal_period_snapshots` + `monthly_input_periods` RLS reuse, AD-3 same-tenant filter 적용)
- **subtasks**:
  - [ ] 5.1 (skip) No new tables, no new columns, no new RLS policies
  - [ ] 5.2 (verify) 기존 `fiscal_period_snapshots` RLS policy `supabase/policies/0003_fiscal_period_snapshots_rls.sql` 활용 확인 (Epic 0 wire)

### Task 6 — Frontend (RSC + sliders + Recharts + TS mirror + ko-KR.json)

- **AC**: #2, #4
- **파일**:
  - [ ] 6.1 `apps/web/app/[locale]/(dashboard)/simulation/cvp/layout.tsx` (NEW RSC layout)
  - [ ] 6.2 `apps/web/app/[locale]/(dashboard)/simulation/cvp/page.tsx` (NEW RSC page — `<CVPSimulationClient>` actual mount MUST per CR 11-4 D-001)
  - [ ] 6.3 `apps/web/components/m7-simulation/CVPSimulationClient.tsx` (NEW client component, ~250 lines)
  - [ ] 6.4 `apps/web/components/m7-simulation/CVPSlider.tsx` (NEW, ~80 lines) — shadcn Slider + decimal-aware
  - [ ] 6.5 `apps/web/components/m7-simulation/CVPResultCard.tsx` (NEW, ~60 lines) — 결과 카드
  - [ ] 6.6 `apps/web/components/m7-simulation/CVPComparisonChart.tsx` (NEW, ~150 lines) — Recharts BarChart
  - [ ] 6.7 `apps/web/lib/m7-simulation-cvp.ts` (NEW, ~120 lines) — TS mirror + `simulateCvpTS`
  - [ ] 6.8 `apps/web/messages/ko-KR.json` EXTENSION — `cvp_simulation` namespace (~15 strings)
  - [ ] 6.9 `apps/web/components/m7-simulation/index.ts` (NEW barrel export)
  - [ ] 6.10 `apps/web/lib/menu-config.ts` EXTENSION — `/simulation/cvp` sidebar nav entry
  - [ ] 6.11 디바운싱: React `useDeferredValue` 또는 `lodash.debounce` 150ms (CR 11-4 patterns)
- **tests**:
  - [ ] 6.12 `apps/web/components/m7-simulation/CVPSimulationClient.test.tsx` (NEW, 10+ cases) — slider onChange → debounce → recompute
  - [ ] 6.13 `apps/web/lib/m7-simulation-bench.test.ts` (NEW) — 100회 P95 ≤ 200ms
  - [ ] 6.14 `apps/web/lib/m7-simulation-cvp.test.ts` (NEW, 8+ cases) — TS mirror parity Python

### Task 7 — Tests + docs + 3중 게이트 final clean

- **AC**: #1, #2, #3, #4, #5, #6
- **subtasks**:
  - [ ] 7.1 Backend tests aggregate:
    - `tests/cost_engine/test_cvp.py` (30+ pure kernel)
    - `tests/cost_engine/test_cvp_no_io_imports.py` (5+ AST)
    - `tests/cost_engine/test_cvp_determinism.py` (5+ V8 byte-identical)
    - `tests/services/m7_simulation/test_cvp_simulation_service.py` (15+)
    - `tests/api/test_m7_simulation_handlers.py` (12+)
    - `tests/integration/test_m7_simulation_cross_language_drift.py` (10+ Python↔TS)
    - `tests/integration/test_m7_simulation_no_db_writes.py` (3+ audit_logs 0건)
    - `tests/architecture/test_api_calls_only_ports.py` EXTENSION (ALLOWED_SERVICE_SUBMODULES m7_simulation sweep)
  - [ ] 7.2 Frontend tests:
    - `apps/web/components/m7-simulation/CVPSimulationClient.test.tsx` (10+)
    - `apps/web/lib/m7-simulation-bench.test.ts` (perf benchmark)
    - `apps/web/lib/m7-simulation-cvp.test.ts` (8+ TS mirror)
  - [ ] 7.3 Docs:
    - `docs/cvp-simulation.md` (NEW, ~200 lines, 8 sections)
    - `docs/capability-matrix.md` v1.16 EXTENSION
    - `docs/conventions.md` §AD-11 layer rule EXTENSION (m7_simulation service layer 명시)
    - `docs/architecture-inventory.md` EXTENSION (m7_simulation module entry)
    - `docs/deferred-work.md` EXTENSION (honest DEFER items)
    - `docs/sprint-status.md` sync (7-1: ready-for-dev → in-progress)
  - [ ] 7.4 3중 게이트 mandatory CI (cj-style 6번째 epic + carry-over 6번째 연속):
    - **ruff scoped** (7-1 surface: `packages/cost_engine/cvp.py` + `apps/api/modules/m7_simulation/` + `packages/services/m7_simulation/` + `apps/web/components/m7-simulation/`): All checks passed
    - **import-linter 2 KEPT 0 broken** (ALLOWED_SERVICE_SUBMODULES `m7_simulation` 추가, AD-11 + AD-22 + cost_engine_forbidden_io + engine_core_to_adapters_forbidden 모두 유지)
    - **pytest baseline + ~70 NEW = 2106 + ~70 = ~2176 passed + 127 skipped + 0 failed** (3 pre-existing failures honestly DEFER per T0)
    - **vitest 158 baseline + ~26 NEW = ~184 passed**
    - **3 pre-existing failures** (test_alembic_0022_does_not_exist + test_sdr_test_count_drift + test_tenant_backups_0024_migration) honestly DEFER per A19 carry-over T0 결정
  - [ ] 7.5 MAX SDR claim 갱신 (CR 11-2 lesson — separate line for unambiguous parser match):
    - `2176 → ~2246` (+70 NEW pytest cases)
    - `184 → ~210` (+26 NEW vitest cases)
    - `2410 → ~2456` total

### Task 8 — Atomic wire close-out (handoff + sprint-status)

- **AC**: all
- **subtasks**:
  - [ ] 8.1 Commit message: `Story 7.1: T1~T7 atomic wire — BEP slider 1-second recompute + pure kernel + service layer + handlers + frontend + cross-language drift detector + 3중 게이트`
  - [ ] 8.2 sprint-status.yaml EXTENSION — `7-1-bep-slider-1-second-recompute: ready-for-dev → in-progress → review → done`
  - [ ] 8.3 handoff memory file: `handoff-2026-08-15-7-1-spec-ready.md` (5 honestly DEFER 명시)
  - [ ] 8.4 Epic 7 진입 시점 baseline_commit = `a63646c` (Story 12.3 T7 follow-up tip) 명시
  - [ ] 8.5 다음 단계 명시: `bmad-dev-story 7-1 T1~T8 실행 OR follow-up sprint for 5 honestly DEFER OR Epic 7 7-2 spec 진입 (cj-style 2번째)`

## Dev Notes

### Architecture patterns & constraints

**AD-5 engine purity (CRITICAL)**:
- `packages/cost_engine/cvp.py` 는 **stdlib-only** (decimal, dataclasses, math, hashlib, typing) — NO sqlalchemy, NO datetime.now(), NO random, NO I/O
- import-linter contracts 2 KEPT 0 broken (Epic 0 wire pattern, 12-1 + Epic 5 reinforcement)
- ruff custom rule: `packages/cost_engine/*.py` 에서 forbidden imports → lint error

**AD-11 layer rule**:
- 의존 방향: `apps/web → apps/api → packages/services/m7_simulation/ → packages/cost_engine/cvp.py`
- 단방향 strict (Epic 0 wire pattern, 12-1 reinforcement)
- engine은 services / adapters / UI import 불가 (AD-11 reverse-direction 명시)

**AD-3 RLS multi-tenancy**:
- baseline fetch 시 `tenant_id = :tenant_id` 필터 (JWT claim)
- 다른 테넌트 baseline 0건 노출 (Epic 0 fixture test pattern)

**AD-15 cross-language conventions**:
- DB/Python `snake_case`; Next.js routes `kebab-case` (`/simulation/cvp`); React/TS types `PascalCase`
- Decimal 정밀도: ROUND_HALF_EVEN (Python `decimal.Decimal` ↔ TS `decimal.js`)
- Period keys follow AD-24 (`YYYY-MM`)
- Errors: `{code, message_ko, details, trace_id}` (AD-15 §4 envelope)

**NFR9 (P95 ≤ 5초) → 7-1 (P95 ≤ 1초)**:
- 150ms debounce + 10ms pure calc + 50ms React re-render = 210ms P95
- Web Worker offload honestly DEFER (over-engineering 회피)
- Epic 4 cost engine + Epic 5 ledger aggregate 패턴 동일 (pure kernel + service layer thin wrapper)

**NFR16 determinism**:
- V8 byte-identical CI gate: 100회 동일 입력 → 100회 동일 `compute_bep_hash(result)` (Epic 4 baseline extension)
- `hashlib.sha256(repr(result).encode()).hexdigest()` 결정론 digest

**NFR17 monetary types (AD-8)**:
- BIGINT (KRW integer) / NUMERIC(18,2) (USD) — 7-1은 KRW only (USD 환산은 Epic 6 6-2 wire, 본 스토리 범위 외)
- Python `decimal.Decimal`; TS `decimal.js`

**CR 11-4 lessons carry**:
- D-001 (page.tsx mount MUST actually mount `<CVPSimulationClient>` JSX)
- D-002 (단일 `apps/web/messages/ko-KR.json` only — NOT `apps/web/lib/ko-KR.json`)
- D-005 (TS mirror unknown state MUST raise — `simulateCvpTS` baseline null → throw `ERROR_CODE_INVALID_INPUT`, NOT silent fall-through)
- P-015 (ko-KR.json SSOT drift detector test — `cvp_simulation` namespace 정합)

**CR 12-1 lessons continue**:
- L3 (`_to_cvp_baseline(snapshot, monthly_input_period)` ORM→kernel boundary conversion, Epic 12-1 _to_totp_state precedent)
- L4 (CVP_SIMULATION industry-agnostic capability — 12-1 TWO_FACTOR_AUTH + 12-2 BACKUP_EXPORT + 12-3 ACCOUNT_DELETION 미러)

**CR 12-5 lessons continue**:
- D-13 (structural cross-language drift detector — `test_m7_simulation_cross_language_drift.py` Python↔TS 10+ vectors)
- D-14 (typed exception main.py envelope handler 등록 — `CVPBaselineNotFoundError` 404 + `CVPInvalidDeltaError` 422)
- L4 (honest-DEFER discipline — Web Worker / sensitivity / AI 추천 / 7-2 / Playwright)

**A19 lessons carry**:
- math surface migration pattern (`packages/services/m2_input/inventory_math.py` precedent — math surface는 `packages/cost_engine/` 또는 `packages/services/<module>/<math>.py`)
- 7-1은 cost_engine surface (calc engine과 동일 layer) → `packages/cost_engine/cvp.py` SSOT
- build_inventory_projection runtime migration 패턴 (5-2 commit 안에 swap + Epic 6 close-out 시점에 완전 제거) — 7-1은 runtime migration 불요 (신규 surface)

### Source tree components to touch

**NEW files**:
1. `packages/cost_engine/cvp.py` (~200 lines)
2. `packages/cost_engine/__init__.py` EXTENSION (export `compute_bep`, `compute_target_profit`, `simulate_cvp`)
3. `tests/cost_engine/test_cvp.py` (~30+ cases)
4. `tests/cost_engine/test_cvp_no_io_imports.py` (~5 cases)
5. `tests/cost_engine/test_cvp_determinism.py` (~5 cases)
6. `packages/services/m7_simulation/__init__.py` (NEW)
7. `packages/services/m7_simulation/serializers.py` (~50 lines)
8. `packages/services/m7_simulation/delta_helpers.py` (~40 lines)
9. `tests/services/m7_simulation/test_cvp_simulation_service.py` (~15 cases)
10. `apps/api/modules/m7_simulation/__init__.py` (NEW)
11. `apps/api/modules/m7_simulation/handlers.py` (~120 lines)
12. `apps/api/modules/m7_simulation/services/cvp_simulation_service.py` (~150 lines)
13. `apps/api/modules/m7_simulation/schemas.py` (~80 lines — Pydantic v2)
14. `apps/api/modules/m7_simulation/exceptions.py` (~30 lines)
15. `tests/api/test_m7_simulation_handlers.py` (~12 cases)
16. `tests/integration/test_m7_simulation_cross_language_drift.py` (~10 cases)
17. `tests/integration/test_m7_simulation_no_db_writes.py` (~3 cases)
18. `apps/web/app/[locale]/(dashboard)/simulation/cvp/layout.tsx` (NEW RSC layout)
19. `apps/web/app/[locale]/(dashboard)/simulation/cvp/page.tsx` (NEW RSC page)
20. `apps/web/components/m7-simulation/CVPSimulationClient.tsx` (~250 lines)
21. `apps/web/components/m7-simulation/CVPSlider.tsx` (~80 lines)
22. `apps/web/components/m7-simulation/CVPResultCard.tsx` (~60 lines)
23. `apps/web/components/m7-simulation/CVPComparisonChart.tsx` (~150 lines)
24. `apps/web/components/m7-simulation/index.ts` (NEW barrel)
25. `apps/web/components/m7-simulation/CVPSimulationClient.test.tsx` (~10 cases)
26. `apps/web/lib/m7-simulation-cvp.ts` (~120 lines TS mirror)
27. `apps/web/lib/m7-simulation-cvp.test.ts` (~8 cases)
28. `apps/web/lib/m7-simulation-bench.ts` (~30 lines perf benchmark)
29. `apps/web/lib/m7-simulation-bench.test.ts` (~3 cases)
30. `docs/cvp-simulation.md` (~200 lines)

**MODIFIED files**:
1. `apps/api/main.py` — m7_simulation router include (1 line)
2. `apps/api/core/capability.py` — `CVP_SIMULATION = "cvp_simulation"` EXTENSION (5 lines)
3. `apps/api/core/audit_action.py` — `simulation_cvp_computed` EXTENSION (선택적)
4. `apps/web/messages/ko-KR.json` — `cvp_simulation` namespace EXTENSION (~15 strings)
5. `apps/web/lib/menu-config.ts` — `/simulation/cvp` sidebar nav EXTENSION (1 entry)
6. `docs/capability-matrix.md` v1.16 EXTENSION (1 row)
7. `docs/conventions.md` §AD-11 EXTENSION (m7_simulation 명시)
8. `docs/architecture-inventory.md` EXTENSION (m7_simulation module entry)
9. `docs/deferred-work.md` EXTENSION (5 honestly DEFER items)
10. `_bmad-output/implementation-artifacts/sprint-status.yaml` — 7-1 status sync + last_updated_note
11. `tests/architecture/test_api_calls_only_ports.py` — ALLOWED_SERVICE_SUBMODULES sweep (CR 11-3 D-2)
12. `tests/integration/test_ko_kr_json_ssot.py` — `cvp_simulation` namespace 정합 (CR 12-1 P-015)

**Total**: 30 NEW + 12 MODIFIED = 42 files (~2,500 lines code + ~700 lines tests + ~300 lines docs)

### Testing standards summary

**Backend (pytest)**:
- **Pure kernel** (30+ cases): edge cases 3종 ValueError + Decimal precision ROUND_HALF_EVEN parity + frozen=True enforcement + 100회 determinism
- **Service layer** (15+ cases): baseline extraction + RLS same-tenant + 0 DB writes verification
- **Handlers** (12+ cases): 200 OK + 403 CAPABILITY_NOT_GRANTED + 404 CVP_BASELINE_NOT_FOUND + 422 INVALID_PERIOD_KEY + latency 200ms P95
- **Cross-language drift** (10+ cases): Python ↔ TS parity 10 vectors + edge cases 동일
- **Audit no-write** (3+ cases): `audit_logs` row 0건 검증

**Frontend (vitest)**:
- **CVPSimulationClient** (10+ cases): slider onChange → debounce → recompute → result card 갱신
- **TS mirror parity** (8+ cases): Python `simulate_cvp` vs TS `simulateCvpTS` 동일 결과
- **Performance benchmark** (3+ cases): 100회 P95 ≤ 200ms

**Architecture tests**:
- **ALLOWED_SERVICE_SUBMODULES sweep** (1 case): `m7_simulation` 추가 검증 (CR 11-3 D-2)
- **Engine purity** (5+ cases): AST parser로 forbidden imports 차단 검증

### Project Structure Notes

**Alignment with unified project structure** (cj-style 6번째 epic 검증):
- `apps/api/modules/m7_simulation/` (Epic 11 m11_close + 12-1 m12_account 패턴)
- `packages/services/m7_simulation/` (thin wrappers, A19 math surface 패턴)
- `packages/cost_engine/cvp.py` (pure kernel, Epic 4 cost_engine surface)
- `apps/web/components/m7-simulation/` (12-1 m12-account 패턴)
- `apps/web/app/[locale]/(dashboard)/simulation/cvp/` (12-1 /account/security 패턴)

**Detected conflicts or variances**:
- None — 7-1은 신규 surface (Epic 4 + Epic 5 + Epic 11 + Epic 12 wire 패턴 그대로 미러)

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Epic-7-CVP/BEP-Simulation`] — Epic 7 + Story 7.1 verbatim
- [Source: `_bmad-output/planning-artifacts/prd.md#§F7.1`] — PRD §F7.1 (슬라이더 변경 시 1초 이내 재계산)
- [Source: `_bmad-output/planning-artifacts/prd.md#§6.1-engine`] — 산식 체인 (Epic 4 cost_engine precedent)
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-5`] — engine purity
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-11`] — layer rule
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-15`] — cross-language conventions
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-3`] — RLS multi-tenancy
- [Source: `_bmad-output/implementation-artifacts/12-3-account-deletion-retention-consent.md`] — Story 12.3 spec 진입 패턴 (cj-style 7번째 epic)
- [Source: `_bmad-output/implementation-artifacts/handoff-2026-08-15-a19-inventory-projection-deprecate-done.md`] — A19 carry-over DONE (math surface migration 패턴)
- [Source: `_bmad-output/implementation-artifacts/epic-6-retro-2026-08-09.md`] — Epic 6 close-out retro §7 A8 inline projection deprecate 결정
- [Source: `_bmad-output/implementation-artifacts/epic-11-retro-2026-08-09.md`] — Epic 11 close-out retro §7 A14 cj-style 3-story 분할 권장
- [Source: `_bmad-output/implementation-artifacts/4-1-pure-cost-engine-no-i-o-no-clock.md`] — Story 4.1 cost_engine pure kernel spec (precedent)
- [Source: `_bmad-output/implementation-artifacts/12-1-two-factor-auth-mandatory-gate.md`] — Story 12.1 L4 industry-agnostic capability precedent
- [Source: `_bmad-output/implementation-artifacts/12-3-account-deletion-retention-consent.md#AC-7`] — CR 12-1 L3 _to_<state> ORM→kernel boundary conversion pattern
- [Source: `docs/capability-matrix.md`] — capability matrix v1.13 → v1.16 (5 NEW: TWO_FACTOR_AUTH + BACKUP_EXPORT + ACCOUNT_DELETION + MONTHLY_CLOSING_REPORT + CVP_SIMULATION)
- [Source: `docs/conventions.md#AD-11-layer-rule`] — 의존 방향 명시
- [Source: `docs/cvp-simulation.md`] (will be NEW) — 7-1 도큐먼트

## Dev Agent Record

### Agent Model Used

Claude Opus 5 (claude-opus-5)

### Debug Log References

N/A (spec 진입 단계 — bmad-dev-story 진입 시 작성)

### Completion Notes List

(To be filled by bmad-dev-story T1~T8 execution)

### File List

(To be filled by bmad-dev-story T1~T8 execution)

## Honestly DEFER (per CR 11-3 9번째 epic 연속 검증)

| # | Item | Rationale | Where |
|---|------|-----------|-------|
| 1 | Web Worker offload | 1초 한도 대비 5배 여유 (210ms P95) — over-engineering 회피 | specs/deferred-work.md ## Deferred from: 7-1 |
| 2 | Monte Carlo sensitivity 분석 | 단일 변수 슬라이더만 — multi-variate는 7-3 close-out retro §7 신규 결정 시 | specs/deferred-work.md ## Deferred from: 7-1 |
| 3 | AI 추천 가격 제안 | Epic 10 carry-over (F10.1 input_drafts 우회 필수) | specs/deferred-work.md ## Deferred from: 7-1 |
| 4 | 차월 추정 4종 파라미터 | Story 7-2 (cj-style 2번째) | specs/deferred-work.md ## Deferred from: 7-1 |
| 5 | Playwright E2E | sprint-scale (12-5 T6 패턴, follow-up sprint) | specs/deferred-work.md ## Deferred from: 7-1 |

---

**Status**: ready-for-dev (cj-style 3-story Epic 7 진입점, 6번째 epic 연속 검증)
**baseline_commit**: `a63646c`
**다음 단계**: `bmad-dev-story 7-1 T1~T8 실행` OR `Epic 7 7-2 spec 진입 (cj-style 2번째)` OR `follow-up sprint for 5 honestly DEFER`
