---
title: 'Epic 8 Story 3 — Budget Pre-Standard Cost Preview (예산 사전 표준원가 자동 계산 + §9 #20 PDF export 8-2 DEFER 해소)'
status: ready-for-dev
priority: HIGH
epic: 8
story_num: 3
story_key: 8-3-budget-pre-standard-cost-preview
baseline_commit: 091026f
created: 2026-08-16
updated: 2026-08-16
---

> **2026-08-16 — bmad-create-story spec 진입 done** (8-3: backlog → ready-for-dev). **Epic 8 cj-style 3-story 분할 3번째 진입점** (Epic 7 retro §7 A20 결정 wire + Epic 8 8-1·8-2 done 후 진입, cj-style 9번째 epic 연속). 8-1 (Virtual Budget Period Key + Scenario Lock to One) done `e12bea9` + 8-2 (Budget vs Actual Variance Table with ABCD Gray Badge) done `091026f` + 7-2 follow-up sprint done `2911162`.
>
> **baseline_commit = `091026f`** (Story 8.2 DONE tip — current HEAD).
>
> **Three user decisions locked** (2026-08-16):
> 1. **순수 엔진 함수 surface = `packages/cost_engine/budget_pre_standard.py`** (NEW 분리 surface, AD-5 stdlib-only) — `compute_pre_standard_cost(*, material_unit_cost: Decimal, labor_unit_cost: Decimal, overhead_rate: Decimal, material_qty: Decimal, labor_hours: Decimal) -> PreStandardCost` (1 NEW pure function) + `compute_pre_standard_hash(*, pre_standard_cost: PreStandardCost) -> str` (V8 determinism hash) + **2 NEW frozen dataclasses** (`PreStandardCost` with `material_cost: Decimal` + `labor_cost: Decimal` + `overhead_cost: Decimal` + `manufacturing_cost: Decimal` + `period_key: str` + `scenario_index: int` + `engine_type: Literal["budget"]`). **`packages/cost_engine/budget_pre_standard.py` 가 SSOT** (A19 math surface migration pattern 미러 — 8-1 budget_period_key.py + 8-2 budget_variance.py + 7-1 cvp.py + 7-2 projection.py 5번째 surface 분리, A19 cohesion pattern 5번째 검증).
> 2. **Pre-Standard Cost Preview primary scope = epics.md SSOT verbatim** — `fiscal_period_snapshots.engine_type` EXTENSION = `'budget'` 추가 (Alembic 0027 + CHECK EXTENSION) + `state='verified'` 초기 저장 + `UNIQUE(tenant_id, period_key, baseline_revision, engine_type)` 기존 제약 reuse (idempotency 보존, Story 4.2 wire) + `result_hash` = `compute_pre_standard_hash` 결과 (V8 determinism). **§9 #20 PDF export secondary scope = 8-2 honestly DEFER 해소** — `apps/api/modules/m8_budget/handlers.py:12` `/variance/{period_key}/pdf` placeholder wire + `VariancePdfButton.tsx` disabled → enabled + Epic 6 M5 PDF generator reuse (READ-ONLY envelope, ko-KR only).
> 3. **Capability gate 재사용 = 기존 `Capability.BUDGET_SCENARIO`** (8-1 wire 그대로, 12-1 L4 + 8-1/8-2 L4 동일 적용 — manufacturing 3종 ✅ + service-only ✅ = industry-agnostic, 8-2 + 8-3 reuse). **신규 capability 0건 추가** (CR 11-3 즉시 sweep 회피).
>
> **cj-style 3-story 분할 9번째 epic 연속 검증** + **CR 11-3 honest-DEFER discipline 15번째 epic 연속** (atomic wire만, partial wire 0).
>
> **CR 11-3 lessons carry-over**: D-2 (ALLOWED_SERVICE_SUBMODULES 즉시 sweep — `packages.services.m8_budget.budget_pre_standard_serializers` 추가) + ruff auto-fix sweep (CR 11-3 D-3) + SDR separate line parser (CR 11-2 lesson) + `def test_+asyncio.run` project convention (CR 4-3).
>
> **CR 11-4 lessons carry-over**: D-001 (page.tsx mount MUST actually mount `<BudgetPreStandardPreview>` JSX) + D-002 (단일 `apps/web/messages/ko-KR.json` only) + D-005 (TS mirror unknown state fall-through → reject) + P-015 (ko-KR.json SSOT drift detector test).
>
> **CR 12-1 lessons continue applied**: L3 (`_to_pre_standard_cost_state(orm_row)` ORM→kernel boundary conversion, 8-1 `_to_budget_scenario_state` + 8-2 `_to_budget_variance_row` precedent) + L4 (BUDGET_SCENARIO capability 8-1/8-2/8-3 industry-agnostic 동일 적용).
>
> **CR 12-5 lessons continue applied**: D-13 (cross-language drift detector pattern) + D-14 (typed exception main.py envelope handler 등록 — `InvalidPreStandardInputError` 422 + `PreStandardSnapshotNotFoundError` 404 + `PreStandardAlreadyExistsError` 409 + `BudgetVariancePdfNotReadyError` 425 — 8-3 wire 4 NEW typed exceptions envelope main.py handler 등록) + L3 (3-layer defense — route `@require_capability(BUDGET_SCENARIO)` + service `validate_pre_standard_inputs` + audit-first emit, 8-3은 engine_type='budget' snapshot INSERT로 destructive-write) + L4 (honest-DEFER discipline).
>
> **A19 lessons carry-over**: math surface migration pattern (CR A19 NEW) + `packages/services/m2_input/inventory_math.py` precedent. 8-3은 **`packages/cost_engine/budget_pre_standard.py`** (cost_engine surface — 8-1 budget_period_key.py + 8-2 budget_variance.py + 7-1 cvp.py + 7-2 projection.py 동일 layer, A19 cohesion pattern 5번째).
>
> **Honestly DEFER (per CR 11-3 15번째 epic 연속, partial wire 아님)**:
> - **Multi-scenario B2/B3 pre-standard cost preview** — 1차 MVP NON-GOAL #2 §15 verbatim (≥5 테넌트 요청 시 trigger). `Epic 8 close-out retro §7` honestly DEFER (cj-style 4번째 진입점).
> - **A×B×C×D 편성 엔진** — 1차 MVP NON-GOAL #1 §15 verbatim. 8-2 회색 배지 placeholder 명시 (PRD §F8.2 verbatim + epics.md Story 8.2 AC), 8-3은 pre-standard cost preview만 wire.
> - **AI 추천 예산 시나리오** — Epic 10 carry-over, 8-3 scope OUTSIDE (F10.1 input_drafts 우회 필수).
> - **Pre-standard cost ↔ Projection 통합** — 7-2 honestly DEFER (b) 결정 ("2026-08#P1" virtual projection key) + 8-3 honestly DEFER (차월 추정은 별도 surface, A8 inline projection deprecate 후 fold-in 결정).
> - **Year-over-year pre-standard cost comparison** — 1차 MVP N/A (epics.md 8-3 verbatim + 2차 PRD).
> - **Multi-currency pre-standard cost (USD 환산)** — Epic 6 6-2 wire 결정 보존, 8-3 scope OUTSIDE.
> - **Playwright E2E** — 12-5 T6 패턴, follow-up sprint (8-1/8-2 honestly DEFER mirror).
> - **Web Worker for large previews** — 1000+ products 가능, 1차 MVP 단일 scenario 한도 내 (over-engineering 회피, 7-1/8-1/8-2 honestly DEFER mirror).

# Story 8.3 — Budget Pre-Standard Cost Preview + §9 #20 PDF Export

## Epic 8 context

**Epic 8 (Budget vs Actual)** cj-style 3-story 분할 3번째 진입점 (Epic 4·5·6·11·12 + Epic 11/12 carry-over + Epic 7·8 9번째 epic):

- **8-1** = Virtual Budget Period Key + Scenario Lock to One (PRD §F8.1 + AD-24 period key + 1차 시나리오 1개 잠금) ← **done** `e12bea9`
- **8-2** = Budget vs Actual Variance Table with ABCD Gray Badge (PRD §F8.2 + 차이율 ±5% yellow / ±10% red + A×B×C×D 회색 배지) ← **done** `091026f`
- **8-3** = Budget Pre-Standard Cost Preview (PRD §F8.3 + AD-5 engine purity + fiscal_period_snapshots.engine_type='budget' + §9 #20 PDF export 8-2 DEFER 해소) ← **이 스토리** (backlog → ready-for-dev)

**Epic 8 모듈 authority**: `apps/api/modules/m8_budget/` (8-1 + 8-2 wire populate 완료, 본 스토리에서 EXTENSION). 11-1 m11_close / 12-1 m12_account / 7-1 m7_simulation 패턴 미러.

**Epic 8 capability matrix wire**: v1.17 `BUDGET_SCENARIO` 8-1 wire 그대로 재사용 (manufacturing 3종 ✅ + service-only ✅ = industry-agnostic, 12-1 L4 precedent + 8-1/8-2/8-3 동일 적용). **신규 capability 추가 0건** (CR 11-3 즉시 sweep 회피).

**Epic 8 NFR coverage**: NFR16 (엔진 순수성 — AD-5) + NFR17 (monetary types — AD-8) + NFR18 (ko-KR MVP lock).

**NON-GOAL for MVP 명시** (§15 PRD verbatim):
- 복수 예산 시나리오 (1차 = 1개, 2차 = 복수 예정, trigger: ≥5 테넌트 요청 시) — `8-3 honestly DEFER (multi-scenario B2/B3)`
- A×B×C×D 차이 분석 (1차 = 회색 배지 placeholder, 2차 = 산식 보존) — 8-2 회색 배지 명시, 8-3 pre-standard cost preview는 A×B×C×D engine 미사용

## Why this story (atomic wire 결정 근거)

**PRD §F8.3 verbatim (epics.md lines 990-1000)**:
> **Given** 가상 기간 "2026-07#B1"에 예산 입력 완료
> **When** [예측] 클릭
> **Then** 사전 표준원가표(직접재료·직접노무·제조경비)가 표시되고 `fiscal_period_snapshots`에 `engine_type='budget'`로 저장
> **And** 동일 입력 시 동일한 hash (엔진 순수성)
> **And** 예산 시점과 실적 시점의 차이는 §9 #20 "예산-실적 차이 명세서"로 출력

**8-1 sprint-up 결정 verbatim**: "Pre-standard cost preview `engine_type='budget'` (Story 8-3 결정, cj-style 3번째)" — 8-1 wire 시점에 8-3 scope 확정.

**PRD §10 M8 verbatim** (line 465-467):
> - **M8 (예산 시나리오)**
>   - (a) 시스템은 1차에서 시나리오 1개만 허용하고, 2개 이상 생성 시도를 차단한다(2차에서 해제).
>   - (b) 시스템은 예산 실적 대조 시 모든 차이 행을 표시하고, A×B×C×D 편성 엔진이 미구현이면 회색 배지로 "2차 예정"을 표시한다.

**8-2 handlers.py placeholder** (lines 8-12 verbatim):
```python
Story 8.2 (2 NEW endpoints):
  - GET /api/v1/budget/variance/{period_key} — budget vs actual variance
    (4-role read, BUDGET_SCENARIO capability reuse — AC #2 + AD-22)
  - GET /api/v1/budget/variance/{period_key}/pdf — variance PDF envelope
    (8-3 honestly DEFER — placeholder response shape)
```

8-3 wire 시 `/variance/{period_key}/pdf` placeholder 활성화 + Epic 6 M5 PDF generator reuse.

**AD-22 ledger append-only** + **AD-5 engine purity** + **AD-11 layer rule** + **AD-24 period key typed**:
- `fiscal_period_snapshots` 테이블 (Story 4.2 wire 완료) — `engine_type='trad'` default + `state IN ('verified','committed','reversed')` CHECK + `UNIQUE(tenant_id, period_key, baseline_revision, engine_type)` idempotency constraint 보존
- `engine_type` EXTENSION = `'budget'` 추가 (Alembic 0027 + CHECK EXTENSION) — 8-3 wire 시 enum EXTENSION, free text → 4-value enum 변환 (`'trad' | 'abc' | 'tdabc' | 'budget'`)
- `tenant_id` JWT claim → `WHERE tenant_id = :tenant_id` (AD-3 standard pattern)
- `period_key` 검증: `real_period_key = "YYYY-MM"` (예: `2026-07`) + `scenario_index = 1` (8-1 lock) — virtual budget period key `2026-07#B1`

**3 second-order decisions** (locked 2026-08-16):

1. **Pure kernel = `packages/cost_engine/budget_pre_standard.py`** (NEW 분리 surface, AD-5 stdlib-only + AD-11 layer rule + A19 math surface migration pattern 5번째 분리 surface — pre-standard cost concern 별도): `compute_pre_standard_cost(*, material_unit_cost: Decimal, labor_unit_cost: Decimal, overhead_rate: Decimal, material_qty: Decimal, labor_hours: Decimal) -> PreStandardCost` (5 frozen dataclass fields: `material_cost: Decimal` (= material_unit_cost × material_qty), `labor_cost: Decimal` (= labor_unit_cost × labor_hours), `overhead_cost: Decimal` (= labor_cost × overhead_rate, AD-8 monetary BigInteger parity), `manufacturing_cost: Decimal` (= material_cost + labor_cost + overhead_cost), `period_key: str`, `scenario_index: int`, `engine_type: Literal["budget"]`) + `compute_pre_standard_hash(*, pre_standard_cost: PreStandardCost) -> str` (V8 determinism hash, sha256). **`packages/cost_engine/` 가 SSOT** (Story 4-1 spec 확정). `packages/services/m8_budget/` 는 thin wrappers (CR 11-3 D-2 ALLOWED_SERVICE_SUBMODULES sweep 즉시). **stdlib-only**: `import decimal, dataclasses, math, hashlib, typing` only (no sqlalchemy, no datetime.now, no random, no emoji).

2. **Pre-Standard Cost Preview primary scope + §9 #20 PDF export secondary scope**:
   - **Primary** = epics.md SSOT verbatim: `fiscal_period_snapshots` row INSERT (or UPSERT with idempotency guard) `engine_type='budget'` + `state='verified'` 초기 저장 + `result_hash` = `compute_pre_standard_hash` 결과 + `material_cost + labor_cost + overhead_cost + manufacturing_cost` 4-column reuse + `inventory_adjustment = 0` (default).
   - **Secondary** = 8-2 honestly DEFER 해소: `/variance/{period_key}/pdf` endpoint wire + `VariancePdfButton.tsx` disabled → enabled + Epic 6 M5 PDF generator reuse (READ-ONLY envelope, ko-KR only per NFR18).
   - **Alembic 0027** (NEW — 0026 budget_scenarios 후속): `fiscal_period_snapshots.engine_type` CHECK EXTENSION 1→4 values (`'trad' | 'abc' | 'tdabc' | 'budget'`) + `idx_fiscal_period_snapshots_engine_type` (engine_type 별도 index) + `down_revision = '0026_budget_scenarios'`.

3. **Capability gate 재사용 = `Capability.BUDGET_SCENARIO`** (8-1 wire 그대로, industry-agnostic): manufacturing 3종 ✅ + service-only ✅ (전 industry 공통, 12-1 L4 precedent — "pre-standard cost preview는 budget scenario의 projection 변형, 모든 industry 동일 적용"). **신규 capability 0건** (CR 11-3 즉시 sweep 회피).

**+ Epic 8 close-out path**: 8-3 done 진입 후 Epic 8 close-out retro (cj-style 4번째 진입점) → Epic 9 spec 진입 또는 Epic 8 follow-up sprint (cj-style 8번째 carry-over).

## User Story

As a **사장님**,
I want **예산 입력 완료 시 [예측] 클릭으로 사전 표준원가(pre-standard cost)표 (직접재료·직접노무·제조경비)가 자동 계산되어 보이고 `fiscal_period_snapshots`에 `engine_type='budget'`로 저장되며, 8-2에서 표시된 [PDF 다운로드] 버튼이 활성화되어 §9 #20 예산-실적 차이 명세서를 PDF로 출력**,
so that **PRD §F8.3 (예산 시점의 단가 기준 미리 잠금) + §10 M8 (예산 시나리오) + §15 NON-GOAL 명시 + NFR16 (엔진 순수성 — 동일 입력 시 동일 hash) + AD-22 (fiscal_period_snapshots ledger append-only) + AD-24 (period key typed) + 12-1 L4 (capability industry-agnostic) + Epic 6 M5 (PDF generator reuse) 모두 만족**.

(epics.md Story 8.3 verbatim + PRD §F8.3 + §10 + §15 + NFR16·17·18 + AD-5·8·11·15·22·24 + Epic 8 cj-style 3번째 진입점 + 8-1 sprint-up 결정 verbatim + 8-2 honestly DEFER #5 해소)

## Acceptance Criteria

### AC #1 — 순수 엔진 함수 surface `packages/cost_engine/budget_pre_standard.py` (epics.md AC #3 verbatim + AD-5 + AD-11 + NFR16 + A19 5번째 분리 surface)

- **Given** AD-5 엔진 순수성 + AD-11 layer rule + NFR16 V8 회귀 가능 + 8-1 budget_period_key.py + 8-2 budget_variance.py와 surface 분리 (A19 cohesion pattern 5번째)
- **When** `packages/cost_engine/budget_pre_standard.py` NEW 파일 작성 (8-1 budget_period_key.py + 8-2 budget_variance.py EXTENSION이 아님 — 분리 surface)
- **Then** **`compute_pre_standard_cost(*, material_unit_cost: Decimal, labor_unit_cost: Decimal, overhead_rate: Decimal, material_qty: Decimal, labor_hours: Decimal, period_key: str = "2026-07", scenario_index: int = 1) -> PreStandardCost`**:
  - 공식:
    - `material_cost = material_unit_cost * material_qty` (ROUND_HALF_EVEN, AD-8)
    - `labor_cost = labor_unit_cost * labor_hours` (ROUND_HALF_EVEN, AD-8)
    - `overhead_cost = labor_cost * overhead_rate / 100` (overhead_rate는 % 단위, ROUND_HALF_EVEN, AD-8)
    - `manufacturing_cost = material_cost + labor_cost + overhead_cost` (합계)
    - `period_key = period_key` (AD-24 `YYYY-MM#B1` 검증 — `parse_virtual_budget_period_key` 8-1 reuse)
    - `scenario_index = 1` (8-1 lock, 1차 MVP는 1개 only)
    - `engine_type = "budget"` (literal, 8-3 wire 시점 유일)
  - **Edge cases**:
    - `material_unit_cost < 0` → `ValueError("material_unit_cost must be non-negative")` raise
    - `labor_unit_cost < 0` → `ValueError("labor_unit_cost must be non-negative")` raise
    - `overhead_rate < 0` → `ValueError("overhead_rate must be non-negative")` raise
    - `overhead_rate > 100` → `ValueError("overhead_rate must be <= 100")` raise
    - `material_qty < 0` → `ValueError("material_qty must be non-negative")` raise
    - `labor_hours < 0` → `ValueError("labor_hours must be non-negative")` raise
    - `period_key` invalid virtual pattern → `ValueError("period_key must match YYYY-MM#B<n>")` raise (8-1 reuse `parse_virtual_budget_period_key`)
    - `scenario_index != 1` → `ValueError("MVP supports scenario_index=1 only; 2차 예정")` raise (8-1 lock)
  - **Determinism**: 100회 동일 입력 호출 → 100회 모두 byte-identical `PreStandardCost` (V8 회귀 가능)
  - **Purity**: `import decimal, dataclasses, math, hashlib, typing` only (AD-5 + import-linter + ruff custom rule)
- **And** **`compute_pre_standard_hash(*, pre_standard_cost: PreStandardCost) -> str`**:
  - `hashlib.sha256(repr(pre_standard_cost).encode()).hexdigest()` 결정론 digest (V8 회귀용, 8-1 `compute_budget_scenario_hash` + 8-2 `compute_variance_hash` 패턴)
- **And` **stdlib-only import 검증**:
  - `tests/cost_engine/test_budget_pre_standard_no_io_imports.py` (NEW) — AST parser로 `budget_pre_standard.py` 의 import whitelist 검증 (`decimal`, `dataclasses`, `math`, `hashlib`, `typing` 만 허용, `os, time, random, requests, sqlalchemy, datetime` 모두 차단)
  - 8-1 `test_budget_period_key_no_io_imports.py` + 8-2 `test_budget_variance_no_io_imports.py` 패턴 미러 (5+ AST cases)
  - ruff custom rule (8-1 + 8-2 wire): `packages/cost_engine/*.py` 에서 forbidden imports → lint error (이미 wire, 8-3은 신규 surface 추가지만 동일 rule 적용)

### AC #2 — Pre-Standard Cost Preview + fiscal_period_snapshots.engine_type='budget' 저장 (epics.md AC #3 verbatim + AD-8 + NFR16 + 4-2 wire reuse)

- **Given** PRD §F8.3 verbatim + AD-8 monetary types + NFR16 V8 determinism + Story 4-2 fiscal_period_snapshots wire reuse
- **When** pre-standard cost 계산 + `fiscal_period_snapshots` INSERT (or UPSERT with idempotency guard)
- **Then` **Pre-Standard Cost Preview row** (PRD §F8.3 verbatim + 4-2 wire reuse):
  - `fiscal_period_snapshots` row INSERT (or UPSERT):
    - `tenant_id` = JWT claim
    - `period_key` = `"2026-07#B1"` (8-1 virtual period key)
    - `baseline_revision` = 1 (default, 첫 preview)
    - `engine_type` = `"budget"` (8-3 wire 시점 유일)
    - `material_cost` = `compute_pre_standard_cost` 의 `material_cost` (KRW BigInteger, AD-8)
    - `labor_cost` = `compute_pre_standard_cost` 의 `labor_cost` (KRW BigInteger, AD-8)
    - `overhead_cost` = `compute_pre_standard_cost` 의 `overhead_cost` (KRW BigInteger, AD-8)
    - `manufacturing_cost` = `compute_pre_standard_cost` 의 `manufacturing_cost` (KRW BigInteger, AD-8)
    - `inventory_adjustment` = 0 (default, pre-standard cost preview에서는 N/A — actual snapshot 시점 보정)
    - `result_hash` = `compute_pre_standard_hash(pre_standard_cost)` 결과 (V8 determinism, 64-char hex SHA-256)
    - `state` = `'verified'` (초기 저장, M11 close에서 `'committed'`로 전이, AD-22 + Epic 11 11-3 reverse 가드 동일 적용)
    - `created_at` = NOW() (AD-9 Seoul TZ-aware)
  - **Idempotency**: `UNIQUE(tenant_id, period_key, baseline_revision, engine_type)` 기존 제약 (4-2 wire) reuse — `engine_type='budget'` row 1개 per (tenant, period, baseline) 보장
  - **재호출 시**: 같은 hash → idempotent skip (CR 1.1 wire, 4-2 wire), 다른 hash → 기존 row UPSERT (PostgreSQL ON CONFLICT)
- **And` **Decimal precision ROUND_HALF_EVEN** (banker's rounding, AD-8):
  - `material_cost` = `round_half_even(material_unit_cost * material_qty, 0)` (KRW 정수, AD-8 BigInteger parity)
  - `labor_cost` = `round_half_even(labor_unit_cost * labor_hours, 0)` (KRW 정수)
  - `overhead_cost` = `round_half_even(labor_cost * overhead_rate / 100, 0)` (KRW 정수)
  - `manufacturing_cost` = `material_cost + labor_cost + overhead_cost` (KRW 정수 합산)
  - parity with TS decimal.js (8-1 + 8-2 pattern)
- **And` **Edge cases**:
  - `material_qty == 0 AND labor_hours == 0` → `manufacturing_cost = 0` (모두 0)
  - `overhead_rate == 0` → `overhead_cost = 0` (overhead 미적용)
  - `overhead_rate == 100` → `overhead_cost = labor_cost` (overhead 100%, edge case)
  - **테스트**: `tests/cost_engine/test_budget_pre_standard.py` (NEW, 35+ cases):
    - `compute_pre_standard_cost` 정상범위 + 6종 edge cases (ValueError + 0 budget + 100% overhead)
    - `compute_pre_standard_hash` 결정론 (RFC test vector)
    - `frozen=True` enforcement (mutation 시도 → FrozenInstanceError)
    - Decimal precision: ROUND_HALF_EVEN parity (TS decimal.js 동일, 8-1 + 8-2 패턴)
    - 100회 determinism test (byte-identical hash)
    - Pre-Standard Cost Preview idempotency (same input → same hash → skip; different input → UPSERT)

### AC #3 — Capability gate + RLS + 4-role + Alembic 0027 engine_type EXTENSION (8-1 BUDGET_SCENARIO reuse + 12-1 L4 + AD-3·10 + NFR18)

- **Given** AD-3 RLS multi-tenancy + AD-10 4-role + 12-1 L4 industry-agnostic + 8-1 BUDGET_SCENARIO capability reuse + AD-22 ledger append-only
- **When** `Capability.BUDGET_SCENARIO` 재사용 + 1 NEW POST endpoint (preview 생성) + 1 NEW GET endpoint (preview 조회) + 1 NEW GET endpoint (PDF 다운로드) wire
- **Then` **`apps/api/modules/m8_budget/handlers.py` EXTENSION**:
  - **`POST /api/v1/budget/pre-standard` (NEW)**:
    - Request: `BudgetPreStandardRequest(period_key: str, scenario_index: int = 1, material_unit_cost: Decimal, labor_unit_cost: Decimal, overhead_rate: Decimal, material_qty: Decimal, labor_hours: Decimal)` (Pydantic v2, AD-24 regex 검증)
    - `@require_capability(BUDGET_SCENARIO)` decorator (8-1 reuse)
    - `require_role("owner", "member")` (생성 권한, AD-10 — preview 생성은 destructive-write)
    - Service: `compute_pre_standard_cost` → `compute_pre_standard_hash` → `upsert_fiscal_period_snapshot(engine_type='budget')`
    - Response: `BudgetPreStandardResponse(period_key, scenario_index, material_cost, labor_cost, overhead_cost, manufacturing_cost, inventory_adjustment, engine_type, result_hash, created_at_kst, state)` + `X-PreStandard-Hash` header
    - 200 OK + Decimal-as-string (JSON-safe, AD-15) + idempotency ACK (409 if exists with different hash → `PreStandardAlreadyExistsError` envelope)
  - **`GET /api/v1/budget/pre-standard?period_key=YYYY-MM#B1` (NEW)**:
    - `@require_capability(BUDGET_SCENARIO)` decorator (8-1 reuse)
    - `require_role("owner", "member", "viewer", "consultant_proxy")` 모두 허용 (AD-10 4-role 모두 — preview는 read-only)
    - Service: `fetch_pre_standard_snapshot(period_key, engine_type='budget')` → `fiscal_period_snapshots` row 조회
    - Response: `BudgetPreStandardResponse(...)` + 200 OK + `X-PreStandard-Hash` header
    - 404 if not exists → `PreStandardSnapshotNotFoundError` envelope
  - **`GET /api/v1/budget/variance/{period_key}/pdf` (EXTENSION — 8-2 placeholder 활성화)**:
    - `@require_capability(BUDGET_SCENARIO)` decorator (8-1 + 8-2 reuse)
    - `require_role("owner", "member", "viewer", "consultant_proxy")` 모두 허용 (AD-10 4-role 모두 — PDF는 read-only)
    - Service: `generate_budget_variance_pdf(period_key)` (8-2 placeholder wire) → Epic 6 M5 PDF generator reuse (READ-ONLY envelope)
    - Response: `application/pdf` (binary) + `Content-Disposition: attachment; filename="budget_variance_{period_key}.pdf"`
    - 425 if pre-standard snapshot not ready → `BudgetVariancePdfNotReadyError` envelope (Too Early)
    - 404 if scenario not found → `BudgetScenarioNotFoundError` envelope
- **And` **Alembic 0027** (NEW — 0026 budget_scenarios 후속):
  - `apps/api/alembic/versions/0027_budget_pre_standard.py` (NEW)
  - **`fiscal_period_snapshots.engine_type` CHECK EXTENSION** 1→4 values:
    - 기존: `engine_type TEXT NOT NULL DEFAULT 'trad'` (free text, 4-2 wire)
    - 신규: `engine_type TEXT NOT NULL DEFAULT 'trad' CHECK (engine_type IN ('trad','abc','tdabc','budget'))`
    - `down_revision = '0026_budget_scenarios'`
    - 기존 row migration: `UPDATE fiscal_period_snapshots SET engine_type = 'trad' WHERE engine_type NOT IN ('trad','abc','tdabc','budget')` (idempotency guard, 기존 row 영향 없음 — 모두 'trad')
  - **`idx_fiscal_period_snapshots_engine_type`** (NEW): engine_type 별도 index (pre-standard cost preview 조회 최적화)
- **And` **RLS = 기존 fiscal_period_snapshots RLS reuse** (4-2 wire `0012_fiscal_period_snapshots_rls.sql`):
  - `tenant_id = current_setting('app.tenant_id')::UUID` filter (AD-3 standard pattern)
  - 다른 테넌트 pre-standard snapshot 0건 노출 (Epic 0 RLS verification pattern)
  - 신규 RLS 정책 불요 (8-1 + 8-2 + 7-1 + 7-2와 동일 패턴)
- **And` **NFR9 1초 이내 응답** (8-1 baseline 200ms P95 + 8-2 추가 100ms + 8-3 추가 100ms):
  - **목표**: 100ms budget_scenarios fetch + 30ms monthly_input_periods aggregation + 30ms pre_standard_cost pure calc + 20ms fiscal_period_snapshots INSERT/UPSERT + 20ms React re-render = **200ms P95** (1초 한도 대비 5배 여유)
  - vitest `apps/web/lib/m8-budget-pre-standard-bench.ts` (NEW) — `performance.now()` before/after, P95 ≤ 200ms assertion
- **And` **AD-22 ledger append-only** (CR 1.1 invariant):
  - `audit_first=False` 명시 (8-3은 destructive-write이지만 INSERT-only operation, M11 close 시점에 committed audit emit)
  - **테스트**: `tests/integration/test_m8_budget_pre_standard_no_db_writes_to_other_tables.py` (NEW) — pre-standard 호출 후 `audit_logs` row 0건 + `budget_scenarios` 변경 0건 + `monthly_input_periods` 변경 0건 (fiscal_period_snaphots INSERT만 허용, 다른 table 변경 0건)
- **And` **PDF envelope** (Epic 6 M5 PDF generator reuse, §9 #20 8-2 DEFER 해소):
  - `packages/services/m8_budget/budget_pre_standard_pdf_helpers.py` (NEW thin wrapper, 8-2 `budget_variance_pdf_helpers.py` pattern 미러):
    - `serialize_budget_pre_standard_pdf_envelope(*, period_key, scenario_index, pre_standard_cost, fiscal_period_snapshot, generated_at_kst) -> dict`
    - envelope 형식: `{ report_code: "BUDGET_PRE_STANDARD", title: "예산 사전 표준원가 명세서", period_key, scenario_index, material_cost, labor_cost, overhead_cost, manufacturing_cost, engine_type, result_hash, generated_at_kst }` (Epic 6 §9 #20 형식)
    - PDF 형식: A4 portrait + KRW 정수 + ko-KR only (NFR18)
  - `apps/api/modules/m8_budget/services/budget_pre_standard_service.py` `generate_budget_pre_standard_pdf()` (NEW):
    - delegate to `packages/services/m6_reports/pdf_helpers.py:generate_pdf_from_envelope` (Epic 6 M5 reuse, READ-ONLY)
    - return PDF bytes (A4 portrait, KRW integer, ko-KR) + ABCD gray badge PDF 미터
    - **425 BudgetVariancePdfNotReadyError** if pre-standard snapshot NOT yet inserted (race condition 방지, 8-2 PDF placeholder race와 동일 패턴)

### AC #4 — Frontend `/budget/pre-standard` RSC + form + preview table + PDF button enabled + ko-KR SSOT (epics.md AC #1~#5 + CR 11-4 D-001·D-002 + 8-2 wire EXTENSION)

- **Given** [예산] → [예측] 클릭 + 직접재료·직접노무·제조경비 3-component preview + PDF 다운로드 enabled
- **When** `apps/web/app/[locale]/(dashboard)/budget/pre-standard/{layout,page}.tsx` NEW RSC + 8-2 `VariancePdfButton` enabled EXTENSION
- **Then` **RSC page** (`page.tsx`):
  - `apps/web/components/m8-budget/BudgetPreStandardPreview.tsx` (NEW client component) mount
  - **CR 11-4 D-001 actual mount MUST**: `<BudgetPreStandardPreview>` JSX return (NOT just create file)
  - 8-2 wire EXTENSION: `/budget/variance/{period_key}` 페이지에서 `VariancePdfButton` enabled (8-2 wire의 disabled → enabled)
- **And` **BudgetPreStandardPreview** (client component, 4 NEW):
  - **BudgetPreStandardPreview.tsx** — main client orchestrator (~250 lines)
    - state: `{ preStandardCost: PreStandardCost | null, isLoading: boolean, error: AD-15 envelope | null }`
    - onMount: `GET /api/v1/budget/pre-standard?period_key=2026-07#B1` → pre_standard_cost set (if exists)
    - 폼 필드 5개 (Pydantic v2 schema 정합):
      - **직접재료 단가 (material_unit_cost)**: KRW 정수, default = 0
      - **직접노무 단가 (labor_unit_cost)**: KRW 정수, default = 0
      - **제조경비율 (overhead_rate)**: % 단위, 0~100, default = 0
      - **직접재료 수량 (material_qty)**: KRW 정수, default = 0
      - **직접노무 시간 (labor_hours)**: 시간 단위, default = 0
    - submit: `POST /api/v1/budget/pre-standard` with 5 fields + period_key + scenario_index
    - **에러 처리**:
      - 409 PRE_STANDARD_ALREADY_EXISTS → toast error + 기존 snapshot 조회 안내
      - 422 INVALID_PRE_STANDARD_INPUT → toast error + 폼 유지
      - 403 CAPABILITY_NOT_GRANTED → toast error + 폼 닫기
      - 404 PRE_STANDARD_SNAPSHOT_NOT_FOUND (GET only) → empty state 안내
  - **PreStandardCostTable.tsx** (NEW, ~80 lines) — 사전 표준원가표 (직접재료·직접노무·제조경비)
    - props: `{ preStandardCost: PreStandardCost }`
    - 4컬럼 표시: 항목명 / 금액 (KRW 정수) / 비중 (%) / 비고
    - 합계 행: 굵은 글씨 + 제조원가 합계 강조
  - **PreStandardPdfButton.tsx** (NEW, ~80 lines) — §9 #20 PDF 다운로드 버튼 (8-2 `VariancePdfButton` 패턴 미러)
    - 8-2 wire의 disabled `VariancePdfButton`은 별도 유지 (variance PDF)
    - 8-3 wire의 `PreStandardPdfButton`은 enabled — pre-standard snapshot이 INSERT되어야 활성화 (425 if not ready)
    - click: `GET /api/v1/budget/variance/{period_key}/pdf` → binary download
    - **disabled 조건**: pre-standard snapshot 미저장 시 disabled + tooltip "예측을 먼저 실행하세요"
    - **enabled 조건**: pre-standard snapshot 저장 완료 시 enabled + tooltip "§9 #20 예산-실적 차이 명세서 PDF 다운로드"
  - **PreStandardHashBadge.tsx** (NEW, ~60 lines) — V8 determinism hash 표시
    - props: `{ resultHash: string }`
    - hash 앞 8자만 표시 + "[전체 보기]" hover tooltip
    - copy-to-clipboard 버튼 (전체 hash 복사)
- **And` **8-2 wire EXTENSION** (`VariancePdfButton.tsx` enabled):
  - 8-2 wire의 `VariancePdfButton.tsx`는 disabled 상태 + "PDF export는 8-3 follow-up sprint에서 wire" tooltip (8-2 spec line 211)
  - 8-3 wire 시점: `disabled = false` + tooltip "§9 #20 예산-실적 차이 명세서 PDF 다운로드" + Epic 6 M5 reuse wire
- **And` **ko-KR.json** SSOT (CR 11-4 D-002 단일 `apps/web/messages/ko-KR.json` only):
  - 1 NEW namespace `budget_pre_standard` (~18 strings: page_title, form_label_material_unit_cost, form_label_labor_unit_cost, form_label_overhead_rate, form_label_material_qty, form_label_labor_hours, form_submit_label, form_clear_label, preview_table_label_material, preview_table_label_labor, preview_table_label_overhead, preview_table_label_manufacturing, preview_table_label_share, preview_table_total_label, pdf_button_label, pdf_button_tooltip_ready, pdf_button_tooltip_disabled, hash_badge_label, etc.)
  - **8-1 budget_scenario + 8-2 budget_variance namespace와 분리** (pre_standard 독립 namespace)
- **And` **TS mirror** (`apps/web/lib/m8-budget-pre-standard.ts`):
  - `PreStandardCost` TS interface (8-1 BudgetScenario + 8-2 VarianceRow 패턴 미러)
  - `computePreStandardCostTS(material_unit_cost, labor_unit_cost, overhead_rate, material_qty, labor_hours): PreStandardCost` — TypeScript re-implementation (V8 cross-language parity)
  - `computePreStandardHashTS(pre_standard_cost): string` — hash TS re-implementation (8-1 + 8-2 pattern)
  - **CR 11-4 D-005**: unknown state fall-through → reject (`computePreStandardCostTS` invalid input → throw `ERROR_CODE_INVALID_INPUT`)
- **And` **`apps/web/lib/menu-config.ts` EXTENSION**:
  - `/budget/pre-standard` sidebar nav entry (8-1 `/budget/scenarios` + 8-2 `/budget/variance` sibling)
  - 조건부 렌더: `industry in (manufacturing, manufacturing_with_trading, manufacturing_with_service, service_only)` 모두 표시 (12-1 L4 industry-agnostic)
- **And` **디바운싱 + Web Worker honestly DEFER** (8-1 + 8-2 + 7-1 + 7-2 동일):
  - React `useDeferredValue` 또는 `lodash.debounce` 100ms (CR 11-4 patterns carry)
  - Web Worker offload honestly DEFER (1초 한도 대비 5배 여유 — over-engineering 회피)

### AC #5 — Cross-language drift detector + no DB writes to other tables + V8 byte-identical (CR 12-5 D-13 + 12-1 P-015 + AD-2 audit-first)

- **Given** AD-15 cross-language conventions + CR 12-5 D-13 structural drift detector + 8-1 + 8-2 cross-language drift 패턴
- **When** 8-3 wire
- **Then` **`tests/integration/test_m8_budget_pre_standard_cross_language_drift.py`** (NEW):
  - **Python ↔ TS parity test**: `compute_pre_standard_cost` Python vs `computePreStandardCostTS` TypeScript 10+ vectors
    - 동일 5개 입력 (material_unit_cost + labor_unit_cost + overhead_rate + material_qty + labor_hours) → 동일 result (`material_cost`, `labor_cost`, `overhead_cost`, `manufacturing_cost`)
    - Decimal 정밀도 round-trip (TS `decimal.js` ↔ Python `decimal.Decimal`)
    - Edge cases: `material_qty == 0 AND labor_hours == 0` → `manufacturing_cost = 0`
    - Edge cases: `overhead_rate == 100` → `overhead_cost = labor_cost` (overhead 100%)
    - Edge cases: `overhead_rate > 100` → `ERROR_CODE_INVALID_INPUT` (TS) / `ValueError` (Python)
    - Edge cases: `period_key = "invalid"` → 동일 거부 (8-1 reuse `parse_virtual_budget_period_key`)
  - **ko-KR.json SSOT drift detector** (CR 12-5 L4 + 12-1 P-015):
    - `tests/integration/test_ko_kr_json_ssot.py` EXTENSION — `budget_pre_standard` namespace 정합
    - frontend i18n key가 `apps/web/messages/ko-KR.json` 에만 존재 (NOT `apps/web/lib/ko-KR.json`)
- **And` **no external state mutation to other tables**:
  - `tests/integration/test_m8_budget_pre_standard_no_db_writes_to_other_tables.py` (NEW) — pre-standard 호출 후 다른 table 변경 0건 (CR 1.1 invariant + AD-22 ledger append-only):
    - **`audit_logs` row 0건** (CR 1.1 invariant — pre-standard INSERT는 audit-first emit N/A, M11 close 시점 emit)
    - **`budget_scenarios` 변경 0건** (8-1 wire 미변경)
    - **`monthly_input_periods` 변경 0건** (input data 미변경)
    - **`fiscal_period_snapshots.engine_type='trad'` 변경 0건** (snapshot 'trad' row 미변경)
    - **허용**: `fiscal_period_snapshots.engine_type='budget'` INSERT/UPSERT 1건 (8-3 wire의 primary scope)
- **And` **V8 byte-identical CI gate** (8-1 + 8-2 pattern):
  - `tests/cost_engine/test_budget_pre_standard_determinism.py` (NEW) — 100회 동일 입력 byte-identical `pre_standard_hash` (`hashlib.sha256` over `repr(pre_standard_cost)`)
  - 8-1 `test_budget_scenario_determinism.py` + 8-2 `test_budget_variance_determinism.py` 패턴 미러 (5+ cases)

### AC #6 — AD-11 layer rule + ALLOWED_SERVICE_SUBMODULES sweep + 8-2 wire EXTENSION (epics.md AC #4 + AD-2·5·11·22 + CR 11-3 D-2 + Epic 6 §9 #20+)

- **Given** AD-11 layer rule (`ui → api → services → ports → engine`) + AD-2 append-only + CR 11-3 D-2 ALLOWED_SERVICE_SUBMODULES + Epic 6 M5 PDF report reuse + PRD §F8.3 verbatim + 8-2 wire EXTENSION (VariancePdfButton enabled + `/variance/{period_key}/pdf` placeholder wire)
- **When** 8-3 wire
- **Then` **AD-11 layer rule 검증**:
  - `apps/api/modules/m8_budget/services/budget_pre_standard_service.py` (NEW service layer, ~200 lines)
  - `packages/services/m8_budget/` EXTENSION (NEW: `budget_pre_standard_serializers.py` + `budget_pre_standard_pdf_helpers.py`)
  - `packages/cost_engine/budget_pre_standard.py` (pure kernel, stdlib-only, 8-1 budget_period_key.py + 8-2 budget_variance.py와 surface 분리)
  - **의존 방향**: `apps/api → packages/services/m8_budget/ → packages/cost_engine/budget_pre_standard.py` (단방향, AD-11)
  - **import-linter contracts**: 2 KEPT 0 broken (8-1 + 8-2 wire pattern 그대로 유지)
- **And` **ALLOWED_SERVICE_SUBMODULES sweep** (CR 11-3 D-2 즉시, 8-1 + 8-2 wire 패턴 그대로):
  - `tests/architecture/test_api_calls_only_ports.py` EXTENSION — `packages.services.m8_budget.budget_pre_standard_serializers` + `packages.services.m8_budget.budget_pre_standard_pdf_helpers` 추가
- **And` **AD-2 audit-first invariant** (CR 1.1):
  - `pre_standard_snapshot_inserted` audit emit (M11 close 시점에 committed audit emit, 8-3 INSERT 자체는 audit-first 미적용 — `audit_first=False` 명시, Epic 11 11-1 + 11-3 precedent)
  - **AC #5 test_m8_budget_pre_standard_no_db_writes_to_other_tables로 보장** — 다른 table 변경 0건
- **And` **8-2 wire EXTENSION** (`VariancePdfButton` enabled + `/variance/{period_key}/pdf` placeholder wire):
  - **`apps/api/modules/m8_budget/services/budget_variance_service.py`** EXTENSION:
    - `generate_budget_variance_pdf()` placeholder `pass` → real wire (8-2 spec line 273 placeholder)
    - delegate to `packages/services/m8_budget/budget_pre_standard_pdf_helpers.py:serialize_budget_pre_standard_pdf_envelope`
    - delegate to `packages/services/m6_reports/pdf_helpers.py:generate_pdf_from_envelope` (Epic 6 M5 reuse, READ-ONLY)
    - return PDF bytes (A4 portrait, KRW integer, ko-KR) + ABCD gray badge PDF 미터
    - **425 BudgetVariancePdfNotReadyError** if pre-standard snapshot NOT yet inserted
  - **`apps/api/modules/m8_budget/handlers.py`** EXTENSION:
    - `GET /api/v1/budget/variance/{period_key}/pdf` placeholder → real wire (8-2 handlers.py line 12 placeholder)
    - Response: `application/pdf` (binary) + `Content-Disposition: attachment; filename="budget_variance_{period_key}.pdf"`
  - **`apps/web/components/m8-budget/VariancePdfButton.tsx`** EXTENSION:
    - `disabled = true` → `disabled = false` (8-2 wire의 disabled 상태 해소)
    - tooltip: "PDF export는 8-3 follow-up sprint에서 wire (8-2 범위 외)" → "§9 #20 예산-실적 차이 명세서 PDF 다운로드"
- **And` **PDF 보고서 wire** (Epic 6 M5 PDF generator reuse, §9 #20 verbatim):
  - **`packages/services/m8_budget/budget_pre_standard_pdf_helpers.py`** (NEW thin wrapper):
    - `serialize_budget_pre_standard_pdf_envelope(*, period_key, scenario_index, pre_standard_cost, fiscal_period_snapshot, generated_at_kst) -> dict` — Epic 6 M5 PDF envelope (§9 #20 형식)
    - `: pd_envelope["abcd_disabled_badge"] = compute_abcd_disabled_badge().to_dict()` (회색 배지 PDF 미터, 8-2 wire reuse)
  - **`apps/api/modules/m8_budget/services/budget_pre_standard_service.py` `generate_budget_pre_standard_pdf()`** (NEW):
    - delegate to `packages/services/m6_reports/pdf_helpers.py:generate_pdf_from_envelope` (Epic 6 M5 reuse, READ-ONLY 패턴)
    - PDF 형식: A4 portrait + KRW 정수 (AD-17 BigInteger parity) + ko-KR only (NFR18)
- **And` **frontend telemetry**:
  - `pre_standard_preview_computed` + `pre_standard_pdf_downloaded` + `pre_standard_hash_copied` analytics event (PostHog or similar — Epic 10 carry-over, honestly DEFER 시 mock)
  - 본 스토리 범위 외 (honestly DEFER)

## Tasks / Subtasks (atomic wire)

### Task 1 — Pure kernel (Budget pre-standard cost math surface)

- **AC**: #1
- **파일**: `packages/cost_engine/budget_pre_standard.py` (NEW, ~280 lines) + `packages/cost_engine/__init__.py` EXTENSION (export 2 NEW pure functions)
- **subtasks**:
  - [ ] 1.1 STDIN-only: `import decimal, dataclasses, math, hashlib, typing` only (AD-5 purity + import-linter, 8-1 + 8-2 + 7-1 + 7-2 패턴 동일)
  - [ ] 1.2 `class PreStandardCost(frozen=True, slots=True)` with 7 fields: `material_cost: Decimal`, `labor_cost: Decimal`, `overhead_cost: Decimal`, `manufacturing_cost: Decimal`, `period_key: str`, `scenario_index: int`, `engine_type: Literal["budget"]`
  - [ ] 1.3 `def compute_pre_standard_cost(*, material_unit_cost: Decimal, labor_unit_cost: Decimal, overhead_rate: Decimal, material_qty: Decimal, labor_hours: Decimal, period_key: str = "2026-07", scenario_index: int = 1) -> PreStandardCost` — 공식 + 7종 edge cases (ValueError + 0 budget + 100% overhead)
  - [ ] 1.4 `def compute_pre_standard_hash(*, pre_standard_cost: PreStandardCost) -> str` — `hashlib.sha256(repr(pre_standard_cost).encode()).hexdigest()` 결정론 digest
  - [ ] 1.5 8-1 `parse_virtual_budget_period_key` reuse (period_key 검증 delegate)
- **tests**: `tests/cost_engine/test_budget_pre_standard.py` (NEW, 35+ cases):
  - `compute_pre_standard_cost` 정상범위 + 7종 edge cases (ValueError + 0 budget + 100% overhead)
  - `compute_pre_standard_hash` 결정론 (RFC test vector)
  - `frozen=True` enforcement (mutation 시도 → FrozenInstanceError)
  - Decimal precision: ROUND_HALF_EVEN parity (TS decimal.js 동일, 8-1 + 8-2 패턴)
  - 100회 determinism test (byte-identical hash)
  - period_key 검증 (8-1 reuse — invalid virtual pattern + scenario_index != 1 거부)

### Task 2 — Engine purity gate (AD-5 + import-linter + ruff custom rule)

- **AC**: #1
- **파일**: `tests/cost_engine/test_budget_pre_standard_no_io_imports.py` (NEW), 8-1 + 8-2 ruff custom rule reuse
- **subtasks**:
  - [ ] 2.1 `test_budget_pre_standard_no_io_imports.py` AST parser 검증 (8-1 `test_budget_period_key_no_io_imports.py` + 8-2 `test_budget_variance_no_io_imports.py` 패턴 미러):
    - `cost_engine/budget_pre_standard.py` 의 import whitelist: `decimal, dataclasses, math, hashlib, typing` (8-1 + 8-2와 동일 whitelist)
    - forbidden: `os, time, random, requests, sqlalchemy, datetime, json, urllib` 모두 차단 (5+ cases)
  - [ ] 2.2 ruff custom rule (8-1 + 8-2 wire 그대로 — `packages/cost_engine/*.py` 전체 적용):
    - `import os | import time | import random | import requests | import sqlalchemy | import datetime` → lint error
    - 8-3은 신규 surface 추가이지만 동일 rule 적용 (8-1 + 8-2 wire 재사용)
  - [ ] 2.3 `import-linter` contracts 유지:
    - `cost_engine_forbidden_io` (Epic 0 wire) — 1 KEPT 0 broken (8-1 + 8-2 + 7-1 + 7-2 + 8-3 모두 검증)
    - `engine_core_to_adapters_forbidden` (Epic 0 wire) — 1 KEPT 0 broken

### Task 3 — Service layer (thin wrappers + pre-standard snapshot UPSERT + PDF envelope + 8-2 wire EXTENSION)

- **AC**: #3, #6
- **파일**: `apps/api/modules/m8_budget/services/budget_pre_standard_service.py` (NEW, ~250 lines)
- **subtasks**:
  - [ ] 3.1 `class BudgetPreStandardService` with `__init__(session, *, tenant_id, actor_id, trace_id)` (8-1 BudgetScenarioService + 8-2 BudgetVarianceService precedent)
  - [ ] 3.2 `async def compute_pre_standard_snapshot(self, *, period_key: str, scenario_index: int = 1, material_unit_cost: Decimal, labor_unit_cost: Decimal, overhead_rate: Decimal, material_qty: Decimal, labor_hours: Decimal) -> PreStandardCost`:
    - delegate to `packages/cost_engine/budget_pre_standard.py:compute_pre_standard_cost` (pure kernel)
    - `upsert_fiscal_period_snapshot(period_key, baseline_revision=1, engine_type='budget', material_cost, labor_cost, overhead_cost, manufacturing_cost, inventory_adjustment=0, result_hash, state='verified')` (AD-22 + 4-2 wire reuse, idempotency via UNIQUE constraint)
    - RLS same-tenant filter (`tenant_id = :tenant_id`)
    - return `PreStandardCost` + `fiscal_period_snapshot_row`
  - [ ] 3.3 `async def fetch_pre_standard_snapshot(self, *, period_key: str, scenario_index: int = 1) -> FiscalPeriodSnapshot`:
    - SELECT `fiscal_period_snapshots` WHERE `engine_type='budget'` AND `tenant_id = :tenant_id` AND `period_key = :period_key`
    - 404 if not found → `PreStandardSnapshotNotFoundError` raise
    - return `FiscalPeriodSnapshot` ORM row + `_to_pre_standard_cost_state(orm_row)` ORM→kernel boundary conversion (CR 12-1 L3 precedent)
  - [ ] 3.4 `async def generate_budget_pre_standard_pdf(self, *, period_key: str, scenario_index: int = 1) -> bytes`:
    - `serialize_budget_pre_standard_pdf_envelope(...)` → `generate_pdf_from_envelope(...)` (Epic 6 M5 reuse, READ-ONLY)
    - 425 if pre-standard snapshot NOT yet inserted → `BudgetVariancePdfNotReadyError` raise
    - return PDF bytes (A4 portrait, KRW integer, ko-KR) + ABCD gray badge PDF 미터
  - [ ] 3.5 `async def generate_budget_variance_pdf(self, *, period_key: str, scenario_index: int = 1) -> bytes` (**8-2 placeholder wire**):
    - delegate to `BudgetPreStandardService.generate_budget_pre_standard_pdf` (pre-standard snapshot reuse)
    - PDF envelope에 variance data merge (8-2 `budget_variance_pdf_helpers.py` pattern)
- **파일**: `packages/services/m8_budget/` EXTENSION (NEW thin wrappers):
  - [ ] 3.6 `budget_pre_standard_serializers.py` — `serialize_pre_standard_cost`, `serialize_fiscal_period_snapshot`, `serialize_pre_standard_pdf_metadata` (dataclass → dict, JSON-safe Decimal)
  - [ ] 3.7 `budget_pre_standard_pdf_helpers.py` — `serialize_budget_pre_standard_pdf_envelope` (Epic 6 §9 #20 형식) + ABCD disabled badge PDF 미터
- **파일**: `apps/api/modules/m8_budget/services/budget_variance_service.py` EXTENSION (8-2 placeholder wire):
  - [ ] 3.8 `generate_budget_variance_pdf()` placeholder `pass` → real wire (8-2 spec line 273)
  - [ ] 3.9 `serialize_budget_variance_pdf_envelope` EXTENSION (8-2 placeholder wire — pre-standard cost data merge)
- **tests**: `tests/services/m8_budget/test_budget_pre_standard_service.py` (NEW, 20+ cases):
  - `compute_pre_standard_snapshot` UPSERT 정확성 (fiscal_period_snapshots.engine_type='budget' row 생성)
  - `compute_pre_standard_snapshot` idempotency (same hash → skip; different hash → UPSERT)
  - `fetch_pre_standard_snapshot` no scenario → `PreStandardSnapshotNotFoundError` raise
  - `fetch_pre_standard_snapshot` invalid period_key → `InvalidPreStandardInputError` raise (AD-24 검증)
  - `fetch_pre_standard_snapshot` RLS same-tenant (다른 tenant_id 0건)
  - `generate_budget_pre_standard_pdf` envelope 정확성 (Epic 6 §9 #20 형식)
  - `generate_budget_pre_standard_pdf` not ready → `BudgetVariancePdfNotReadyError` raise
  - `serializers` JSON-safe Decimal
  - `pdf_helpers` envelope 정확성 (Epic 6 §9 #20 형식 + ABCD disabled badge)
  - `generate_budget_variance_pdf` (8-2 wire EXTENSION) — 8-2 placeholder wire 정합

### Task 4 — HTTP routes + main.py wire + 8-2 wire EXTENSION + Alembic 0027

- **AC**: #3, #6
- **파일**: `apps/api/modules/m8_budget/handlers.py` EXTENSION (~+200 lines)
- **subtasks**:
  - [ ] 4.1 `POST /api/v1/budget/pre-standard`:
    - Request: `BudgetPreStandardRequest(period_key: str, scenario_index: int = 1, material_unit_cost: Decimal, labor_unit_cost: Decimal, overhead_rate: Decimal, material_qty: Decimal, labor_hours: Decimal)` (Pydantic v2, AD-24 regex 검증)
    - `@require_capability(BUDGET_SCENARIO)` decorator (8-1 + 8-2 reuse)
    - `require_role("owner", "member")` (생성 권한, AD-10)
    - Service: `compute_pre_standard_snapshot(period_key, scenario_index, ...)` → UPSERT
    - Response: `BudgetPreStandardResponse(period_key, scenario_index, material_cost, labor_cost, overhead_cost, manufacturing_cost, inventory_adjustment, engine_type, result_hash, created_at_kst, state)` + `X-PreStandard-Hash` header
    - 200 OK + Decimal-as-string (JSON-safe, AD-15) + idempotency ACK (409 if exists with different hash → `PreStandardAlreadyExistsError` envelope)
  - [ ] 4.2 `GET /api/v1/budget/pre-standard?period_key=YYYY-MM#B1`:
    - `@require_capability(BUDGET_SCENARIO)` decorator (8-1 + 8-2 reuse)
    - `require_role("owner", "member", "viewer", "consultant_proxy")` 모두 허용 (AD-10 4-role 모두 — preview는 read-only)
    - Service: `fetch_pre_standard_snapshot(period_key)` → response
    - 404 if not found → `PreStandardSnapshotNotFoundError` envelope
  - [ ] 4.3 `GET /api/v1/budget/variance/{period_key}/pdf` (**8-2 placeholder wire 활성화**):
    - `@require_capability(BUDGET_SCENARIO)` decorator (8-1 + 8-2 reuse)
    - `require_role("owner", "member", "viewer", "consultant_proxy")` 모두 허용
    - Service: `generate_budget_variance_pdf(period_key)` → PDF bytes
    - Response: `application/pdf` (binary) + `Content-Disposition: attachment; filename="budget_variance_{period_key}.pdf"`
    - 425 if pre-standard snapshot not ready → `BudgetVariancePdfNotReadyError` envelope
    - 404 if scenario not found → `BudgetScenarioNotFoundError` envelope
- **파일**: `apps/api/main.py` EXTENSION:
  - [ ] 4.4 4 NEW typed exception handlers wire (CR 12-5 D-14 envelope):
    - `InvalidPreStandardInputError` → HTTP 422 INVALID_PRE_STANDARD_INPUT envelope
    - `PreStandardSnapshotNotFoundError` → HTTP 404 PRE_STANDARD_SNAPSHOT_NOT_FOUND envelope
    - `PreStandardAlreadyExistsError` → HTTP 409 PRE_STANDARD_ALREADY_EXISTS envelope
    - `BudgetVariancePdfNotReadyError` → HTTP 425 BUDGET_VARIANCE_PDF_NOT_READY envelope
- **파일**: `apps/api/modules/m8_budget/exceptions.py` EXTENSION:
  - [ ] 4.5 `InvalidPreStandardInputError` typed exception (D-14 envelope, 422)
  - [ ] 4.6 `PreStandardSnapshotNotFoundError` typed exception (D-14 envelope, 404)
  - [ ] 4.7 `PreStandardAlreadyExistsError` typed exception (D-14 envelope, 409)
  - [ ] 4.8 `BudgetVariancePdfNotReadyError` typed exception (D-14 envelope, 425)
- **파일**: `apps/api/alembic/versions/0027_budget_pre_standard.py` (NEW):
  - [ ] 4.9 `fiscal_period_snapshots.engine_type` CHECK EXTENSION 1→4 values (`'trad' | 'abc' | 'tdabc' | 'budget'`)
  - [ ] 4.10 `idx_fiscal_period_snapshots_engine_type` (engine_type 별도 index)
  - [ ] 4.11 `down_revision = '0026_budget_scenarios'`
  - [ ] 4.12 기존 row migration: `UPDATE fiscal_period_snapshots SET engine_type = 'trad' WHERE engine_type NOT IN (...)` (idempotency guard)
- **tests**: `tests/api/test_m8_budget_pre_standard_handlers.py` (NEW, 18+ cases):
  - `POST /api/v1/budget/pre-standard` 정상 (200 + Decimal-as-string + X-PreStandard-Hash 헤더)
  - `POST /api/v1/budget/pre-standard` no capability → 403 CAPABILITY_NOT_GRANTED
  - `POST /api/v1/budget/pre-standard` invalid period_key → 422 INVALID_PRE_STANDARD_INPUT
  - `POST /api/v1/budget/pre-standard` existing different hash → 409 PRE_STANDARD_ALREADY_EXISTS
  - `POST /api/v1/budget/pre-standard` existing same hash → 200 (idempotent skip)
  - `POST /api/v1/budget/pre-standard` invalid input (negative cost) → 422
  - `GET /api/v1/budget/pre-standard?period_key=2026-07#B1` 정상 (200)
  - `GET /api/v1/budget/pre-standard?period_key=2026-07#B1` not found → 404
  - `GET /api/v1/budget/pre-standard?period_key=2026-07#B1` RLS other tenant → 404 (RLS same-tenant filter)
  - `GET /api/v1/budget/variance/2026-07#B1/pdf` 정상 (200 application/pdf)
  - `GET /api/v1/budget/variance/2026-07#B1/pdf` not ready → 425 BUDGET_VARIANCE_PDF_NOT_READY
  - `GET /api/v1/budget/variance/2026-07#B1/pdf` scenario not found → 404 BUDGET_SCENARIO_NOT_FOUND
  - ABCD disabled badge PDF 미터 검증 (8-2 wire reuse)
  - latency measurement: 200ms P95 assertion (pre-standard만, PDF 제외)
  - AD-15 envelope contract (4 fields: code, message_ko, details, trace_id)
- **tests**: `tests/alembic/test_0027_budget_pre_standard.py` (NEW, 8+ cases):
  - migration up/down idempotency
  - CHECK constraint enforcement (engine_type='budget' allowed, 'invalid' rejected)
  - 기존 row migration 검증 (모두 'trad' → 'trad' 보존)

### Task 5 — Alembic + RLS (0027 EXTENSION)

- **AC**: #3
- **파일**: `apps/api/alembic/versions/0027_budget_pre_standard.py` (NEW, ~80 lines) + `supabase/policies/` (N/A — 기존 fiscal_period_snapshots RLS 0012 reuse)
- **note**: 8-3은 **fiscal_period_snapshots 기존 테이블 reuse + engine_type CHECK EXTENSION** — Alembic migration 1개 (0027), RLS 신규 정책 불요 (기존 `fiscal_period_snapshots` RLS 0012 reuse, 4-2 + 8-1 + 8-2와 동일 패턴)
- **subtasks**:
  - [ ] 5.1 `fiscal_period_snapshots.engine_type` CHECK EXTENSION 1→4 values
  - [ ] 5.2 `idx_fiscal_period_snapshots_engine_type` (engine_type 별도 index)
  - [ ] 5.3 기존 row migration idempotency guard (UPDATE WHERE NOT IN 보존)
  - [ ] 5.4 (verify) 기존 `fiscal_period_snapshots` RLS policy `0012_fiscal_period_snapshots_rls.sql` 활용 확인 (4-2 wire + Epic 0 verification pattern)

### Task 6 — Frontend (RSC + form + preview table + PDF button enabled + ko-KR.json + 8-2 wire EXTENSION)

- **AC**: #2, #4
- **파일**:
  - [ ] 6.1 `apps/web/app/[locale]/(dashboard)/budget/pre-standard/layout.tsx` (NEW RSC layout)
  - [ ] 6.2 `apps/web/app/[locale]/(dashboard)/budget/pre-standard/page.tsx` (NEW RSC page — `<BudgetPreStandardPreview>` actual mount MUST per CR 11-4 D-001)
  - [ ] 6.3 `apps/web/components/m8-budget/BudgetPreStandardPreview.tsx` (NEW client component, ~250 lines)
  - [ ] 6.4 `apps/web/components/m8-budget/PreStandardCostTable.tsx` (NEW, ~80 lines) — 사전 표준원가표 (직접재료·직접노무·제조경비)
  - [ ] 6.5 `apps/web/components/m8-budget/PreStandardPdfButton.tsx` (NEW, ~80 lines) — §9 #20 PDF 다운로드 버튼
  - [ ] 6.6 `apps/web/components/m8-budget/PreStandardHashBadge.tsx` (NEW, ~60 lines) — V8 determinism hash 표시
  - [ ] 6.7 `apps/web/components/m8-budget/VariancePdfButton.tsx` EXTENSION (8-2 wire EXTENSION — disabled → enabled)
  - [ ] 6.8 `apps/web/lib/m8-budget-pre-standard.ts` (NEW, ~160 lines) — TS mirror + `computePreStandardCostTS` + `computePreStandardHashTS` + Zod schema
  - [ ] 6.9 `apps/web/lib/m8-budget-pre-standard-schema.ts` (NEW, ~60 lines) — Zod schema (pre_standard + result_hash)
  - [ ] 6.10 `apps/web/messages/ko-KR.json` EXTENSION — `budget_pre_standard` namespace (~18 strings, 8-1 budget_scenario + 8-2 budget_variance namespace와 분리)
  - [ ] 6.11 `apps/web/lib/m8-budget-pre-standard-bench.ts` (NEW, ~30 lines) — perf benchmark
  - [ ] 6.12 `apps/web/components/m8-budget/index.ts` EXTENSION — barrel export + PreStandardCost
  - [ ] 6.13 `apps/web/lib/menu-config.ts` EXTENSION — `/budget/pre-standard` sidebar nav entry (8-1 `/budget/scenarios` + 8-2 `/budget/variance` sibling)
  - [ ] 6.14 디바운싱: React `useDeferredValue` 또는 `lodash.debounce` 100ms (CR 11-4 patterns carry, 8-1 + 8-2 + 7-1 + 7-2와 동일)
- **tests**:
  - [ ] 6.15 `apps/web/components/m8-budget/BudgetPreStandardPreview.test.tsx` (NEW, 12+ cases) — fetch + 5필드 form submit + pre_standard_cost display
  - [ ] 6.16 `apps/web/components/m8-budget/PreStandardCostTable.test.tsx` (NEW, 8+ cases) — 4컬럼 표시 + 합계 행
  - [ ] 6.17 `apps/web/components/m8-budget/PreStandardPdfButton.test.tsx` (NEW, 5+ cases) — enabled/disabled + tooltip + click → PDF download
  - [ ] 6.18 `apps/web/components/m8-budget/PreStandardHashBadge.test.tsx` (NEW, 4+ cases) — hash 8자 표시 + copy-to-clipboard
  - [ ] 6.19 `apps/web/components/m8-budget/VariancePdfButton.test.tsx` EXTENSION (8-2 wire EXTENSION — enabled 상태 검증)
  - [ ] 6.20 `apps/web/lib/m8-budget-pre-standard-bench.test.ts` (NEW) — 100회 P95 ≤ 200ms (pre-standard만, PDF 제외)
  - [ ] 6.21 `apps/web/lib/m8-budget-pre-standard.test.ts` (NEW, 10+ cases) — TS mirror parity Python

### Task 7 — Tests + docs + 3중 게이트 final clean

- **AC**: #1, #2, #3, #4, #5, #6
- **subtasks**:
  - [ ] 7.1 Backend tests aggregate:
    - `tests/cost_engine/test_budget_pre_standard.py` (35+ pure kernel)
    - `tests/cost_engine/test_budget_pre_standard_no_io_imports.py` (5+ AST, 8-1 + 8-2 패턴 미러)
    - `tests/cost_engine/test_budget_pre_standard_determinism.py` (5+ V8 byte-identical, 8-1 + 8-2 패턴 미러)
    - `tests/services/m8_budget/test_budget_pre_standard_service.py` (20+)
    - `tests/api/test_m8_budget_pre_standard_handlers.py` (18+)
    - `tests/alembic/test_0027_budget_pre_standard.py` (8+)
    - `tests/integration/test_m8_budget_pre_standard_cross_language_drift.py` (10+ Python↔TS, 8-1 + 8-2 패턴 미러)
    - `tests/integration/test_m8_budget_pre_standard_no_db_writes_to_other_tables.py` (5+ audit_logs 0건 + budget_scenarios 변경 0건 + monthly_input_periods 변경 0건 + fiscal_period_snapshots.engine_type='trad' 변경 0건 + fiscal_period_snapshots.engine_type='budget' INSERT/UPSERT 1건)
    - `tests/architecture/test_api_calls_only_ports.py` EXTENSION (ALLOWED_SERVICE_SUBMODULES m8_budget.budget_pre_standard_serializers + budget_pre_standard_pdf_helpers sweep, CR 11-3 D-2)
  - [ ] 7.2 Frontend tests:
    - `apps/web/components/m8-budget/BudgetPreStandardPreview.test.tsx` (12+)
    - `apps/web/components/m8-budget/PreStandardCostTable.test.tsx` (8+)
    - `apps/web/components/m8-budget/PreStandardPdfButton.test.tsx` (5+)
    - `apps/web/components/m8-budget/PreStandardHashBadge.test.tsx` (4+)
    - `apps/web/components/m8-budget/VariancePdfButton.test.tsx` EXTENSION (8-2 wire EXTENSION — enabled)
    - `apps/web/lib/m8-budget-pre-standard-bench.test.ts` (perf benchmark)
    - `apps/web/lib/m8-budget-pre-standard.test.ts` (10+ TS mirror)
  - [ ] 7.3 Docs:
    - `docs/budget-pre-standard-cost-preview.md` (NEW, ~280 lines, 10 sections — 8-1 docs/virtual-budget-period-key.md + 8-2 docs/budget-variance-table.md 패턴 + §9 #20 PDF export 명시 + fiscal_period_snapshots.engine_type='budget' lifecycle)
    - `docs/capability-matrix.md` v1.17 EXTENSION (8-1 BUDGET_SCENARIO row reuse 명시, 신규 row 0)
    - `docs/conventions.md` §AD-11 layer rule EXTENSION (m8_budget pre_standard service layer 명시, 8-1 + 8-2 + 8-3)
    - `docs/architecture-inventory.md` EXTENSION (m8_budget pre_standard module entry)
    - `docs/deferred-work.md` EXTENSION (8 honestly DEFER items 명시)
    - `docs/sprint-status.md` sync (8-3: ready-for-dev → in-progress)
  - [ ] 7.4 3중 게이트 mandatory CI (cj-style 9번째 epic + carry-over 9번째 연속):
    - **ruff scoped** (8-3 surface: `packages/cost_engine/budget_pre_standard.py` + `apps/api/modules/m8_budget/` + `packages/services/m8_budget/` + `apps/web/components/m8-budget/`): All checks passed
    - **import-linter 2 KEPT 0 broken** (ALLOWED_SERVICE_SUBMODULES `m8_budget.budget_pre_standard_serializers` + `budget_pre_standard_pdf_helpers` 추가, AD-11 + AD-22 + cost_engine_forbidden_io + engine_core_to_adapters_forbidden 모두 유지)
    - **pytest baseline + ~50 NEW = 2351 + ~50 = ~2401 passed + 127 skipped + 0 failed** (3 pre-existing failures honestly DEFER per A19 carry-over T0 결정, 8-3 추가 회귀 0)
    - **vitest 246 baseline + ~40 NEW = ~286 passed** (8-1 budget_scenario 20 + 8-2 budget_variance 49 + 8-3 budget_pre_standard 40 추가)
    - **3 pre-existing failures** (test_alembic_0022_does_not_exist + test_sdr_test_count_drift + test_tenant_backups_0024_migration) honestly DEFER per A19 carry-over T0 결정 (8-3 scope OUTSIDE)
  - [ ] 7.5 MAX SDR claim 갱신 (CR 11-2 lesson — separate line for unambiguous parser match):
    - `2351 → ~2401` (+50 NEW pytest cases)
    - `246 → ~286` (+40 NEW vitest cases)
    - `2597 → ~2687` total

### Task 8 — Atomic wire close-out (handoff + sprint-status)

- **AC**: all
- **subtasks**:
  - [ ] 8.1 Commit message: `Story 8.3: T1~T8 atomic wire — Budget Pre-Standard Cost Preview + fiscal_period_snapshots.engine_type='budget' Alembic 0027 + 4 NEW typed exceptions + §9 #20 PDF export (8-2 DEFER 해소) + VariancePdfButton enabled + 3중 게이트`
  - [ ] 8.2 sprint-status.yaml EXTENSION — `8-3-budget-pre-standard-cost-preview: backlog → ready-for-dev → in-progress → review → done`
  - [ ] 8.3 handoff memory file: `handoff-2026-08-16-8-3-done.md` (8 honestly DEFER 명시)
  - [ ] 8.4 Epic 8 진입 시점 baseline_commit = `091026f` (Story 8.2 DONE tip) 명시
  - [ ] 8.5 다음 단계 명시: `Epic 8 close-out retro 진입 (cj-style 4번째) OR Epic 8 follow-up sprint (cj-style carry-over 9번째) OR Epic 9 spec 진입 (cj-style Epic 9 1번째) OR 8-3 follow-up sprint for 8 honestly DEFER`

## Dev Notes

### Architecture patterns & constraints

**AD-5 engine purity (CRITICAL)**:
- `packages/cost_engine/budget_pre_standard.py` 는 **stdlib-only** (decimal, dataclasses, math, hashlib, typing) — NO sqlalchemy, NO datetime.now(), NO random, NO I/O
- **8-1 budget_period_key.py + 8-2 budget_variance.py 와 surface 분리** — A19 math surface migration pattern (cohesion 강화, pre-standard cost는 별도 concern)
- import-linter contracts 2 KEPT 0 broken (Epic 0 wire pattern, 12-1 + Epic 5 reinforcement + 8-1 + 8-2 + 8-3)
- ruff custom rule: `packages/cost_engine/*.py` 에서 forbidden imports → lint error (8-1 + 8-2 wire 그대로, 8-3은 신규 surface 추가지만 동일 rule 적용)

**AD-11 layer rule**:
- 의존 방향: `apps/web → apps/api → packages/services/m8_budget/ → packages/cost_engine/budget_pre_standard.py`
- 단방향 strict (Epic 0 wire pattern, 12-1 reinforcement + 8-1 + 8-2 + 8-3)
- engine은 services / adapters / UI import 불가 (AD-11 reverse-direction 명시)
- **packages/cost_engine/budget_pre_standard.py → packages/cost_engine/budget_period_key.py** 1방향 호출 (8-3은 8-1 budget scenario를 input으로 받음, reverse 호출 없음)
- **packages/cost_engine/budget_pre_standard.py → packages/cost_engine/budget_variance.py** 호출 없음 (concern 별도 분리, A19 cohesion)

**AD-3 RLS multi-tenancy**:
- pre-standard snapshot fetch 시 `tenant_id = :tenant_id` 필터 (JWT claim, 8-1 + 8-2 패턴 동일)
- 다른 테넌트 pre-standard snapshot 0건 노출 (Epic 0 fixture test pattern)

**AD-15 cross-language conventions**:
- DB/Python `snake_case`; Next.js routes `kebab-case` (`/budget/pre-standard`); React/TS types `PascalCase`
- Decimal 정밀도: ROUND_HALF_EVEN (Python `decimal.Decimal` ↔ TS `decimal.js`, 8-1 + 8-2 + 7-1 + 7-2 패턴 동일)
- Period keys follow AD-24 (`YYYY-MM#B1` for budget_scenarios, 8-1 wire)
- Errors: `{code, message_ko, details, trace_id}` (AD-15 §4 envelope, 8-1 + 8-2 + 8-3 typed exception main.py handler 등록)

**NFR9 (P95 ≤ 5초) → 8-3 (P95 ≤ 1초, pre-standard만)**:
- 100ms budget_scenarios fetch + 30ms monthly_input_periods aggregation + 30ms pre_standard_cost pure calc + 20ms fiscal_period_snapshots UPSERT + 20ms React re-render = 200ms P95
- **PDF 생성은 별도 endpoint** (1초 한도 비대상, 8-2 wire의 placeholder 활성화)
- Web Worker offload honestly DEFER (over-engineering 회피, 8-1 + 8-2 + 7-1 + 7-2와 동일)

**NFR16 determinism**:
- V8 byte-identical CI gate: 100회 동일 입력 → 100회 동일 `compute_pre_standard_hash(pre_standard_cost)` (Epic 4 baseline extension + 8-1 + 8-2 + 7-1 + 7-2 패턴)
- `hashlib.sha256(repr(pre_standard_cost).encode()).hexdigest()` 결정론 digest

**NFR17 monetary types (AD-8)**:
- BIGINT (KRW integer, `material_cost` + `labor_cost` + `overhead_cost` + `manufacturing_cost`) / NUMERIC(18,4) (오버헤드율 — Decimal 4자리 정밀도)
- Python `decimal.Decimal`; TS `decimal.js`
- 8-3은 KRW only (USD 환산은 Epic 6 6-2 wire, 본 스토리 범위 외)

**PRD §F8.3 verbatim (pre-standard cost preview)**:
- `material_cost = material_unit_cost * material_qty` (KRW 정수)
- `labor_cost = labor_unit_cost * labor_hours` (KRW 정수)
- `overhead_cost = labor_cost * overhead_rate / 100` (KRW 정수)
- `manufacturing_cost = material_cost + labor_cost + overhead_cost` (KRW 정수 합산)
- `engine_type = 'budget'` (fiscal_period_snapshots.engine_type 신규 값)
- `state = 'verified'` (초기 저장, M11 close에서 'committed'로 전이)

**PRD §10 M8 verbatim (예산 시나리오)**:
- 1차 시나리오 1개 only (8-1 lock)
- A×B×C×D 회색 배지 placeholder (8-2 wire)

**PRD §15 NON-GOAL #1·2 verbatim**:
- A×B×C×D 예산 편성 엔진 1차 비구현 (산식 보존, §부록 B)
- 복수 예산 시나리오 1차 = 1개 (≥5 테넌트 요청 시 2차 trigger)

**PDF 보고서 envelope (Epic 6 §9 #20, §9 #20 8-2 DEFER 해소)**:
- Epic 6 M5 PDF generator reuse (READ-ONLY, no audit emit)
- envelope 형식: `{ report_code: "BUDGET_PRE_STANDARD", title: "예산 사전 표준원가 명세서", period_key, scenario_index, material_cost, labor_cost, overhead_cost, manufacturing_cost, engine_type, result_hash, generated_at_kst }`
- PDF 형식: A4 portrait + KRW 정수 + ko-KR only (NFR18)
- 8-2 wire의 `/variance/{period_key}/pdf` placeholder 활성화 + `VariancePdfButton` enabled

**Epic 8 capability reuse (8-1 + 8-2 + 8-3)**:
- `Capability.BUDGET_SCENARIO` 단일 capability로 8-1 + 8-2 + 8-3 dispatch (산업 agnostic 동일 적용)
- 신규 capability 추가 0건 (CR 11-3 즉시 sweep 회피)

**CR 11-4 lessons carry**:
- D-001 (page.tsx mount MUST actually mount `<BudgetPreStandardPreview>` JSX)
- D-002 (단일 `apps/web/messages/ko-KR.json` only — NOT `apps/web/lib/ko-KR.json`)
- D-005 (TS mirror unknown state MUST raise — `computePreStandardCostTS` invalid input → throw `ERROR_CODE_INVALID_INPUT`, NOT silent fall-through)
- P-015 (ko-KR.json SSOT drift detector test — `budget_pre_standard` namespace 정합)

**CR 12-1 lessons continue**:
- L3 (`_to_pre_standard_cost_state(orm_row)` ORM→kernel boundary conversion, 8-1 `_to_budget_scenario_state` + 8-2 `_to_budget_variance_row` precedent)
- L4 (BUDGET_SCENARIO capability 재사용 — 8-1 + 8-2 + 8-3 industry-agnostic 동일 적용)

**CR 12-5 lessons continue**:
- D-13 (structural cross-language drift detector — `test_m8_budget_pre_standard_cross_language_drift.py` Python↔TS 10+ vectors, 8-1 + 8-2 패턴)
- D-14 (typed exception main.py envelope handler 등록 — 4 NEW: `InvalidPreStandardInputError` 422 + `PreStandardSnapshotNotFoundError` 404 + `PreStandardAlreadyExistsError` 409 + `BudgetVariancePdfNotReadyError` 425)
- L3 (3-layer defense — route `@require_role` + service `validate_pre_standard_inputs` + audit-first emit, 8-3은 destructive-write이지만 INSERT-only operation, M11 close 시점에 committed audit emit)
- L4 (honest-DEFER discipline — 8 honestly DEFER)

**A19 lessons carry**:
- math surface migration pattern (`packages/services/m2_input/inventory_math.py` precedent — math surface는 `packages/cost_engine/` 또는 `packages/services/<module>/<math>.py`)
- 8-1은 `packages/cost_engine/budget_period_key.py` / 8-2는 `packages/cost_engine/budget_variance.py` / 8-3은 `packages/cost_engine/budget_pre_standard.py` (분리 surface, A19 cohesion pattern 5번째)

### Source tree components to touch

**NEW files**:
1. `packages/cost_engine/budget_pre_standard.py` (~280 lines)
2. `tests/cost_engine/test_budget_pre_standard.py` (~35+ cases)
3. `tests/cost_engine/test_budget_pre_standard_no_io_imports.py` (~5 cases, 8-1 + 8-2 패턴 미러)
4. `tests/cost_engine/test_budget_pre_standard_determinism.py` (~5 cases, 8-1 + 8-2 패턴 미러)
5. `packages/services/m8_budget/budget_pre_standard_serializers.py` (~80 lines)
6. `packages/services/m8_budget/budget_pre_standard_pdf_helpers.py` (~100 lines)
7. `tests/services/m8_budget/test_budget_pre_standard_service.py` (~20 cases)
8. `apps/api/modules/m8_budget/services/budget_pre_standard_service.py` (~250 lines)
9. `apps/api/modules/m8_budget/schemas_pre_standard.py` (~120 lines — Pydantic v2)
10. `tests/api/test_m8_budget_pre_standard_handlers.py` (~18 cases)
11. `tests/alembic/test_0027_budget_pre_standard.py` (~8 cases)
12. `tests/integration/test_m8_budget_pre_standard_cross_language_drift.py` (~10 cases, 8-1 + 8-2 패턴 미러)
13. `tests/integration/test_m8_budget_pre_standard_no_db_writes_to_other_tables.py` (~5 cases)
14. `apps/api/alembic/versions/0027_budget_pre_standard.py` (~80 lines)
15. `apps/web/app/[locale]/(dashboard)/budget/pre-standard/layout.tsx` (NEW RSC layout)
16. `apps/web/app/[locale]/(dashboard)/budget/pre-standard/page.tsx` (NEW RSC page)
17. `apps/web/components/m8-budget/BudgetPreStandardPreview.tsx` (~250 lines)
18. `apps/web/components/m8-budget/PreStandardCostTable.tsx` (~80 lines)
19. `apps/web/components/m8-budget/PreStandardPdfButton.tsx` (~80 lines)
20. `apps/web/components/m8-budget/PreStandardHashBadge.tsx` (~60 lines)
21. `apps/web/components/m8-budget/BudgetPreStandardPreview.test.tsx` (~12 cases)
22. `apps/web/components/m8-budget/PreStandardCostTable.test.tsx` (~8 cases)
23. `apps/web/components/m8-budget/PreStandardPdfButton.test.tsx` (~5 cases)
24. `apps/web/components/m8-budget/PreStandardHashBadge.test.tsx` (~4 cases)
25. `apps/web/lib/m8-budget-pre-standard.ts` (~160 lines TS mirror)
26. `apps/web/lib/m8-budget-pre-standard-schema.ts` (~60 lines Zod schema)
27. `apps/web/lib/m8-budget-pre-standard.test.ts` (~10 cases)
28. `apps/web/lib/m8-budget-pre-standard-bench.ts` (~30 lines perf benchmark)
29. `apps/web/lib/m8-budget-pre-standard-bench.test.ts` (~3 cases)
30. `docs/budget-pre-standard-cost-preview.md` (~280 lines, 10 sections)

**MODIFIED files**:
1. `packages/cost_engine/__init__.py` — export 2 NEW pure functions (`compute_pre_standard_cost`, `compute_pre_standard_hash`) + `PreStandardCost` (5 lines)
2. `apps/api/main.py` — 4 NEW typed exception handlers (4 lines, 8-1 + 8-2 + 8-3 envelope handlers 누적)
3. `apps/api/modules/m8_budget/exceptions.py` EXTENSION — 4 NEW typed exceptions (`InvalidPreStandardInputError` + `PreStandardSnapshotNotFoundError` + `PreStandardAlreadyExistsError` + `BudgetVariancePdfNotReadyError`)
4. `apps/api/modules/m8_budget/handlers.py` EXTENSION — 2 NEW endpoints (POST `/api/v1/budget/pre-standard` + GET `/api/v1/budget/pre-standard`) + 1 EXTENSION endpoint (GET `/api/v1/budget/variance/{period_key}/pdf` placeholder wire 활성화) (~+200 lines)
5. `apps/api/modules/m8_budget/services/budget_variance_service.py` EXTENSION — `generate_budget_variance_pdf()` placeholder wire (8-2 line 273)
6. `apps/api/modules/m8_budget/services/__init__.py` EXTENSION — `BudgetPreStandardService` re-export
7. `apps/api/modules/m8_budget/__init__.py` EXTENSION — pre_standard module export (이미 module authority populate 완료)
8. `apps/web/messages/ko-KR.json` — `budget_pre_standard` namespace EXTENSION (~18 strings, 8-1 budget_scenario + 8-2 budget_variance namespace와 분리)
9. `apps/web/lib/menu-config.ts` — `/budget/pre-standard` sidebar nav EXTENSION (1 entry)
10. `apps/web/components/m8-budget/VariancePdfButton.tsx` EXTENSION (8-2 wire EXTENSION — disabled → enabled + tooltip 변경)
11. `apps/web/components/m8-budget/index.ts` EXTENSION — PreStandardCost barrel export
12. `docs/capability-matrix.md` v1.17 EXTENSION (8-1 BUDGET_SCENARIO row reuse 명시, 신규 row 0)
13. `docs/conventions.md` §AD-11 EXTENSION (m8_budget pre_standard service 명시, 8-1 + 8-2 + 8-3)
14. `docs/architecture-inventory.md` EXTENSION (m8_budget pre_standard module entry)
15. `docs/deferred-work.md` EXTENSION (8 honestly DEFER items)
16. `_bmad-output/implementation-artifacts/sprint-status.yaml` — 8-3 status sync + last_updated_note
17. `tests/architecture/test_api_calls_only_ports.py` — ALLOWED_SERVICE_SUBMODULES sweep EXTENSION (m8_budget.budget_pre_standard_serializers + budget_pre_standard_pdf_helpers 추가, CR 11-3 D-2)
18. `tests/integration/test_ko_kr_json_ssot.py` — `budget_pre_standard` namespace 정합 EXTENSION (CR 12-1 P-015)

**Total**: 30 NEW + 18 MODIFIED = 48 files (~3,200 lines code + ~900 lines tests + ~400 lines docs)

### Testing standards summary

**Backend (pytest)**:
- **Pure kernel** (35+ cases): edge cases 7종 ValueError + 0 budget + 100% overhead + Decimal precision ROUND_HALF_EVEN parity + frozen=True enforcement + 100회 determinism (8-1 + 8-2 + 7-1 + 7-2 패턴)
- **Service layer** (20+ cases): pre-standard snapshot UPSERT + idempotency (same hash skip, different hash UPSERT) + AD-24 period_key 검증 + RLS same-tenant + 0 DB writes to other tables + ABCD disabled badge JSON-safe + PDF envelope 정확성 + 8-2 wire EXTENSION
- **Handlers** (18+ cases): 200 OK + 403 CAPABILITY_NOT_GRANTED + 409 PRE_STANDARD_ALREADY_EXISTS + 422 INVALID_PRE_STANDARD_INPUT + 404 PRE_STANDARD_SNAPSHOT_NOT_FOUND + 425 BUDGET_VARIANCE_PDF_NOT_READY + ABCD disabled badge response + latency 200ms P95 (pre-standard만)
- **Alembic 0027** (8+ cases): migration up/down idempotency + CHECK constraint enforcement + 기존 row migration 검증
- **Cross-language drift** (10+ cases): Python ↔ TS parity 10 vectors + edge cases 동일 (8-1 + 8-2 + 7-1 + 7-2 패턴 미러)
- **Audit no-write to other tables** (5+ cases): `audit_logs` row 0건 + `budget_scenarios` 변경 0건 + `monthly_input_periods` 변경 0건 + `fiscal_period_snapshots.engine_type='trad'` 변경 0건 + `fiscal_period_snapshots.engine_type='budget'` INSERT/UPSERT 1건

**Frontend (vitest)**:
- **BudgetPreStandardPreview** (12+ cases): fetch + 5필드 form submit + pre_standard_cost display + state machine
- **PreStandardCostTable** (8+ cases): 4컬럼 표시 + 합계 행 + 비중 계산
- **PreStandardPdfButton** (5+ cases): enabled/disabled + tooltip + click → PDF download
- **PreStandardHashBadge** (4+ cases): hash 8자 표시 + copy-to-clipboard
- **VariancePdfButton EXTENSION** (8-2 wire EXTENSION): enabled 상태 검증 (8-2 wire의 disabled → enabled)
- **TS mirror parity** (10+ cases): Python `compute_pre_standard_cost` vs TS `computePreStandardCostTS` 동일 결과 (8-1 + 8-2 + 7-1 + 7-2 패턴)
- **Performance benchmark** (3+ cases): 100회 P95 ≤ 200ms (pre-standard만, PDF 제외)

**Architecture tests**:
- **ALLOWED_SERVICE_SUBMODULES sweep** (1 case): `m8_budget.budget_pre_standard_serializers` + `budget_pre_standard_pdf_helpers` 추가 검증 (CR 11-3 D-2)
- **Engine purity** (5+ cases): AST parser로 forbidden imports 차단 검증 (8-1 + 8-2 + 7-1 + 7-2 패턴 미러)

### Project Structure Notes

**Alignment with unified project structure** (cj-style 9번째 epic 검증):
- `apps/api/modules/m8_budget/` (Epic 8 wire + 8-1 + 8-2 + 8-3 패턴)
- `packages/services/m8_budget/` (thin wrappers, A19 math surface 패턴 + 8-1 + 8-2 + 8-3 EXTENSION)
- `packages/cost_engine/budget_pre_standard.py` (pure kernel, 8-1 budget_period_key.py + 8-2 budget_variance.py와 surface 분리, A19 cohesion pattern 5번째)
- `apps/web/components/m8-budget/` (8-1 BudgetScenarioList + 8-2 BudgetVarianceTable + 8-3 BudgetPreStandardPreview 패턴)
- `apps/web/app/[locale]/(dashboard)/budget/pre-standard/` (8-1 /budget/scenarios + 8-2 /budget/variance + 8-3 /budget/pre-standard 패턴)

**Detected conflicts or variances**:
- None — 8-3은 8-1 + 8-2 wire pattern 그대로 미러 (BUDGET_SCENARIO capability reuse + cost_engine surface 분리는 A19 cohesion 강화)
- **packages/cost_engine/budget_pre_standard.py** → **packages/cost_engine/budget_period_key.py** 1방향 import (8-3은 8-1 budget scenario를 input으로 받기 위함, reverse 호출 없음)
- **packages/cost_engine/budget_pre_standard.py** → **packages/cost_engine/budget_variance.py** 호출 없음 (concern 별도, A19 cohesion)

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story-8.3-Budget-Pre-Standard-Cost-Preview`] — Epic 8 + Story 8.3 verbatim (lines 990-1000)
- [Source: `_bmad-output/planning-artifacts/prd.md#§10-M8`] — PRD §10 M8 (a, b) — 예산 시나리오 1차 1개 only + 회색 배지
- [Source: `_bmad-output/planning-artifacts/prd.md#§15-NON-GOAL-MVP-1`] — PRD §15 NON-GOAL #1 (A×B×C×D 엔진 1차 비구현)
- [Source: `_bmad-output/planning-artifacts/prd.md#§15-NON-GOAL-MVP-2`] — PRD §15 NON-GOAL #2 (복수 시나리오 1차 = 1개)
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-5`] — engine purity
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-11`] — layer rule
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-15`] — cross-language conventions
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-3`] — RLS multi-tenancy
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-22`] — reversal ledger (fiscal_period_snapshots append-only)
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md#AD-24`] — period key typed
- [Source: `_bmad-output/implementation-artifacts/8-1-virtual-budget-period-key-scenario-lock-to-one.md`] — Story 8.1 spec 진입 패턴 (cj-style 8번째 epic + BUDGET_SCENARIO capability wire + 8-3 sprint-up 결정 verbatim)
- [Source: `_bmad-output/implementation-artifacts/8-2-budget-vs-actual-variance-table-with-abcd-gray-badge.md`] — Story 8.2 wire (cj-style 8번째 epic + cost_engine surface 분리 + VariancePdfButton placeholder + /variance/{period_key}/pdf placeholder)
- [Source: `_bmad-output/implementation-artifacts/handoff-2026-08-16-7-2-follow-up-sprint.md`] — 7-2 follow-up sprint DONE (cj-style 7-2 + 8-1 + 8-2 + 8-3 sequence)
- [Source: `_bmad-output/implementation-artifacts/handoff-2026-08-15-a19-inventory-projection-deprecate-done.md`] — A19 carry-over DONE (math surface migration 패턴)
- [Source: `_bmad-output/implementation-artifacts/4-2-fiscal-period-snapshots-persistence.md`] — Story 4.2 fiscal_period_snapshots wire (engine_type='trad' default + state machine + UNIQUE constraint + 4-2 wire)
- [Source: `_bmad-output/implementation-artifacts/6-3-closing-pdf-export.md`] — Story 6.3 closing PDF export (M5 PDF generator reuse pattern + READ-ONLY envelope + ko-KR labels)
- [Source: `_bmad-output/implementation-artifacts/12-1-two-factor-auth-mandatory-gate.md`] — Story 12.1 L4 industry-agnostic capability precedent
- [Source: `_bmad-output/implementation-artifacts/12-3-account-deletion-retention-consent.md#AC-7`] — CR 12-1 L3 _to_<state> ORM→kernel boundary conversion pattern
- [Source: `apps/api/modules/m8_budget/handlers.py:12`] — 8-2 wire의 `/variance/{period_key}/pdf` placeholder verbatim (8-3 wire 활성화)
- [Source: `apps/api/core/db_models.py:673-728`] — fiscal_period_snapshots ORM (engine_type free text + state CHECK + UNIQUE constraint + idempotency)
- [Source: `docs/capability-matrix.md`] — capability matrix v1.17 (8-1 BUDGET_SCENARIO row reuse, 8-2 + 8-3 신규 row 0)
- [Source: `docs/conventions.md#AD-11-layer-rule`] — 의존 방향 명시
- [Source: `docs/virtual-budget-period-key.md`] (NEW per 8-1) — 8-1 도큐먼트
- [Source: `docs/budget-variance-table.md`] (NEW per 8-2) — 8-2 도큐먼트
- [Source: `docs/budget-pre-standard-cost-preview.md`] (will be NEW) — 8-3 도큐먼트

## Dev Agent Record

### Agent Model Used

Claude Opus 5 (claude-opus-5)

### Debug Log References

N/A (spec 진입 단계 — bmad-dev-story 진입 시 작성)

### Completion Notes List

(To be filled by bmad-dev-story T1~T8 execution — see handoff at `_bmad-output/implementation-artifacts/handoff-2026-08-16-8-3-done.md`)

### File List

(To be filled by bmad-dev-story T1~T8 execution — see handoff at `_bmad-output/implementation-artifacts/handoff-2026-08-16-8-3-done.md`)

## Honestly DEFER (per CR 11-3 15번째 epic 연속 검증)

| # | Item | Rationale | Where |
|---|------|-----------|-------|
| 1 | Multi-scenario B2/B3 pre-standard cost preview | 1차 MVP NON-GOAL #2 §15 verbatim (≥5 테넌트 요청 시 trigger) — Epic 8 close-out retro §7 honestly DEFER (cj-style 4번째 진입점) | specs/deferred-work.md ## Deferred from: 8-3 |
| 2 | A×B×C×D 편성 엔진 | 1차 MVP NON-GOAL #1 §15 verbatim — 8-2 회색 배지 placeholder 명시, 8-3은 pre-standard cost preview만 wire | specs/deferred-work.md ## Deferred from: 8-3 |
| 3 | AI 추천 예산 시나리오 (F10.1 input_drafts) | Epic 10 carry-over, 8-3 scope OUTSIDE (F10.1 input_drafts 우회 필수) | specs/deferred-work.md ## Deferred from: 8-3 |
| 4 | Pre-standard cost ↔ Projection 통합 | 7-2 honestly DEFER (b) 결정 ("2026-08#P1" virtual projection key) + 8-3 honestly DEFER (차월 추정은 별도 surface, A8 inline projection deprecate 후 fold-in 결정) | specs/deferred-work.md ## Deferred from: 8-3 |
| 5 | Year-over-year pre-standard cost comparison | 1차 MVP N/A (epics.md 8-3 verbatim + 2차 PRD) | specs/deferred-work.md ## Deferred from: 8-3 |
| 6 | Multi-currency pre-standard cost (USD 환산) | Epic 6 6-2 wire 결정 보존, 8-3 scope OUTSIDE | specs/deferred-work.md ## Deferred from: 8-3 |
| 7 | Playwright E2E | sprint-scale (12-5 T6 패턴, follow-up sprint) — 8-1 honestly DEFER #6 + 8-2 honestly DEFER #6 mirror | specs/deferred-work.md ## Deferred from: 8-3 |
| 8 | Web Worker for large previews | 1000+ products 가능, 1차 MVP 단일 scenario 한도 내 (over-engineering 회피, 7-1 honestly DEFER #1 + 8-1/8-2 mirror) | specs/deferred-work.md ## Deferred from: 8-3 |

---

**Status**: ready-for-dev (cj-style 3-story Epic 8 3번째 진입점, 9번째 epic 연속 검증)
**baseline_commit**: `091026f`
**다음 단계**: `bmad-dev-story 8-3 T1~T8 실행` OR `Epic 8 close-out retro 진입 (cj-style 4번째)` OR `Epic 8 follow-up sprint (cj-style carry-over 9번째)` OR `Epic 9 spec 진입 (cj-style Epic 9 1번째)`