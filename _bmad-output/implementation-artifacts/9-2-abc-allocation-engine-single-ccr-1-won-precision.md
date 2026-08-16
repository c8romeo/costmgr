---
story_id: 9.2
story_key: 9-2-abc-allocation-engine-single-ccr-1-won-precision
title: ABC Allocation Engine (Single CCR, 1-Won Precision)
created: 2026-08-16
baseline_commit: 1e034c4
epic: 9
status: done
target_sprint: cj-style Epic 9 2번째 진입점 (DONE 2026-08-16)
estimated_complexity: high
honestly_defer_count: 5
---

# Story 9.2 — ABC Allocation Engine (Single CCR, 1-Won Precision)

## Story Header

| Field | Value |
|-------|-------|
| **Story ID** | 9.2 |
| **Story Key** | `9-2-abc-allocation-engine-single-ccr-1-won-precision` |
| **Epic** | Epic 9 — ABC / TDABC Engine (Service Business) |
| **baseline_commit** | `1e034c4` (Walking Skeleton MVP — 2026-08-16 atomic wire tip) |
| **cj-style 분할** | 9-1 + **9-2** + 9-3 + 9-4 + Epic 9 close-out retro (5번째 진입점) — **cj-style 11번째 epic 연속** (Epic 4·5·6·7·8·11·12 + Epic 11/12 carry-over + Epic 9·Walking Skeleton MVP) |
| **Forward-lock** | **A28 결정 wire** (CCR ↔ Activity ↔ Cost Object 3-way forward-lock from 9-1 handoff) |
| **Primary capability** | `Capability.ABC_CALCULATION` (industry-agnostic, 9-1 wire 재사용 — capability matrix v1.18 신규) |
| **Primary PRD ref** | §F9.2 verbatim (TDABC CCR 부서 원가 ÷ 실제 조업능력 1원 단위 + 미사용능력 별도 행) |
| **Secondary PRD ref** | §F9.1 carry-over (9-1 wire 검증 통과 후 9-2 wire 진입) / §7.2 (TDABC 산식) / §A9 (미사용능력 원가 별도 관리) |
| **Primary AD ref** | AD-5 engine purity + AD-11 layer rule + AD-15 cross-language conventions + AD-18 M3 단일 endpoint + AD-19 single CCR definition + AD-21 CCRPort.compute 단일 소유 |
| **Baseline wire** | 9-1 atomic wire 28 NEW + 9 MODIFIED = ~37 files (3중 게이트 FINAL CLEAN, 6 honest DEFER) |

## User Story (epics.md Story 9.2 verbatim)

As a **사장님**, I want **CCR(자원동인율)이 부서별 원가 ÷ 실제 조업능력 시간으로 1원 단위 계산되는 것**, so that **TDABC 정확도를 보장**.

## Acceptance Criteria (PRD §F9.2 + §A9 + §7.2 verbatim wire)

### AC #1 — A28 forward-lock wire 결정 (9-1 handoff 진입점)

- **Given** 9-1 handoff `handoff-2026-08-16-9-1-done.md` A28 forward-lock 결정 (CCR ↔ Activity ↔ Cost Object 3-way forward-lock)
- **When** developer reads `9-2-abc-allocation-engine-single-ccr-1-won-precision.md` (this spec)
- **Then** **A28 wire 3-way forward-lock**:
  - **CCR compute** (D-9-1-DEFER-1 해소) — `CCRPort.compute(tenant_id, period_key, department_id)` 단일 함수 (AD-21)
  - **Activity mapping** —활동별 시간 배분 → 동인별 배부액 1-Won precision
  - **Cost Object Breakdown** (D-9-1-DEFER-4 해소) — `product_id` (원가대상)별 행 + 원가풀·활동·동인·배부액 4컬럼
- **And** 9-2 wire 범위 = CCR compute + Activity mapping + Cost Object Breakdown snapshot (NOT 9-3 M3 dispatch, NOT 9-4 Report #21 PDF)
- **And** 9-3 (A29 M3 dispatch) + 9-4 (A30 Report #21 PDF generator reuse) forward-lock 보존

### AC #2 — CCR compute (PRD §F9.2 verbatim "부서 원가 ÷ 실제 조업능력 1원 단위")

- **Given** "여행상품 설계 부서" 원가 = 13,200,000원, 실제 조업능력 = 400시간
- **When** [계산] 클릭 → `CCRPort.compute(tenant_id, period_key, department_id)` 호출
- **Then** `CCR = Decimal("13_200_000") / Decimal("400") = Decimal("33_000") (33,000원/시간)` 1원 단위 계산 (AD-8 Decimal-as-string)
- **And** hash format = `sha256:` + 64-char hexdigest (V8 byte-identical determinism, 8-3 precedent)
- **And** `compute_ccr` pure function returns `CCRResult(department_id, department_cost, practical_capacity_hours, ccr_per_hour, hash)` (3 frozen dataclass + 1 typed exception `CcrComputeError`)
- **And** 1-Won precision invariant: `department_cost / practical_capacity_hours → Decimal("KRW 단위")` (KRW 정수, AD-15 cross-language parity)
- **And** `practical_capacity_hours = 0` → `CcrComputeError(code=CCR_INVALID_CAPACITY)` raise (HTTP 422)

### AC #3 — 미사용능력 별도 행 표시 (PRD §F9.2 verbatim + §A9 미사용능력 원가 별도 관리)

- **Given** 부서 실제 조업능력 = 600시간, 사용 = 400시간, 미사용 = 200시간, CCR = 33,000원/시간
- **When** 9-2 wire 동일 actor (사장님) [미사용능력] 탭 진입
- **Then** **별도 행** `"미사용능력 6,600,000원"` (200 × 33,000 = 6,600,000) — 정상 원가와 합산 안 됨 (PRD §A9 verbatim)
- **And** `CcrAllocationResult` frozen dataclass = (used_hours, unused_hours, used_cost, unused_cost) 모두 1-Won precision
- **And** `produce_unused_capacity_row` pure function returns `UnusedCapacityRow(unused_hours, ccr_per_hour, unused_cost_krw, hash)` (PRD §A9 "별도 항목으로 구분 관리")
- **And** Korean SSOT 메시지 `"미사용능력 6,600,000원"` (ko-KR.json `abc_allocation` namespace SSOT, CR 11-4 D-002)

### AC #4 — Activity mapping → Cost Object Breakdown (3-way forward-lock A28 결정 wire)

- **Given** CCR computed (33,000원/시간) + 활동 3개 (In/Out/QC) + 동인 2개 (주문건수/설계시간) + 원가대상 4개 (상품A/B/C/D)
- **When** `CCRPort.compute(tenant_id, period_key, department_id)` + `compute_allocation` 동시 호출
- **Then** **Activity mapping**: 활동별 시간 배분 × CCR = 활동별 배부액 (1-Won precision)
  - 예: In=160h × 33,000 = 5,280,000원 / Out=140h × 33,000 = 4,620,000원 / QC=100h × 33,000 = 3,300,000원
- **And** **Cost Object Breakdown**: `product_id` (원가대상)별 행 + 4컬럼 (원가풀·활동·동인·배부액)
  - 예: 상품A = In × 주문건수 + Out × 설계시간 = 5,280,000 × 0.4 + 4,620,000 × 0.3 = 3,498,000원
- **And** **V7 ABC 무결성 (PRD §V7)**: Σ(원가대상별 배부액) + 미사용능력 = Σ(부서 원가) 1원 단위 (A6 "완전배부·대차평형")
- **And** `compute_allocation` returns `AllocationResult(ccr, activity_mappings, cost_object_breakdown, unused_capacity, total_breakdown_sum, is_balanced=is_balanced_cost_eq)` (1 frozen dataclass)
- **And** `is_balanced = (total_breakdown_sum + unused_cost == department_cost)` 일 때만 True (V7 invariant guard)

### AC #5 — `CCRPort.compute` 단일 소유 (AD-19 + AD-21 verbatim)

- **Given** PRD §F9.2 verbatim: "CCR 계산은 `CCRPort.compute(tenant_id, period_key, department_id)` 한 함수만 보유 (AD-21)"
- **When** developer inspects `packages/cost_engine/abc_engine.py` + `tests/architecture/test_api_calls_only_ports.py`
- **Then** **`CCRPort.compute(...)` 단일 함수** — M9 ABC 모듈 내부에서만 호출 (AD-21 단일 소유)
- **And** M9 owns **no public REST endpoint** for compute (AD-18 + AD-19) — 9-3 진입 시점에 M3 dispatch wire + A29 forward-lock 결정
- **And** 9-2 wire = pure kernel + service layer only, M3 dispatch (AD-19) honestly DEFER (D-9-2-DEFER-1) — 9-3 forward-lock
- **And** `CCRPort.compute` 호출자 = `m9_abc_service.compute_allocation` (service layer wrapper) ONLY (AD-21 invariant)

### AC #6 — A19 cohesion pattern 7번째 surface (abc_engine.py EXTENSION)

- **Given** 9-1 wire `packages/cost_engine/abc_engine.py` (A19 cohesion pattern 6번째 surface, 9-1 handoff 결정)
- **When** 9-2 wire same file EXTENSION (NOT NEW surface — same file, A26 Option A 1 surface 동일)
- **Then** **CCR compute + Activity mapping + Cost Object Breakdown** 모두 same file에 추가 (cross-import 0건, A26 forward-lock)
- **And** 7 surface verified (A19 cohesion pattern 누적):
  - 1: `inventory_math.py` (Epic 5)
  - 2: `cvp.py` (7-1)
  - 3: `projection.py` (7-2)
  - 4: `budget_period_key.py` (8-1)
  - 5: `budget_variance.py` (8-2)
  - 6: `budget_pre_standard.py` (8-3)
  - 7: `abc_engine.py` (9-1 + **9-2 EXTENSION** — wire 1 surface 누적, A26 Option A 채택)
- **And** 9-2 + 9-3 + 9-4 모두 `abc_engine.py` EXTENSION (NO cross-import, A26 Option A 정합)

### AC #7 — Frontend RSC + components + TS mirror + ko-KR.json SSOT (CR 11-4 lessons applied)

- **Given** 9-1 wire `apps/web/app/[locale]/(dashboard)/budget/abc-validation/page.tsx` + 4 components
- **When** developer mounts `<AbcAllocationPanel>` per **CR 11-4 D-001** page.tsx actual mount MUST
- **Then** 9-2 NEW RSC: `apps/web/app/[locale]/(dashboard)/budget/abc-allocation/page.tsx`
  - mounts `<AbcAllocationPanel>` (NEW client component, 9-2 wire)
  - section composition: CCR 계산 결과 (33,000원/시간) + 미사용능력 별도 행 (6,600,000원) + Activity mapping table + Cost Object Breakdown table
- **And** 4 NEW components: `AbcAllocationPanel` + `CcrResultCard` + `UnusedCapacityRow` + `CostObjectBreakdownTable` (8-2 `BudgetVarianceTable` 패턴 미러)
- **And** TS mirror `apps/web/lib/m9-abc-allocation.ts` NEW (CR 11-4 D-005 unknown state reject — `ERROR_CODE_INVALID_INPUT` raise)
- **And** `apps/web/messages/ko-KR.json` EXTENSION `abc_allocation` namespace ~22 strings SSOT (CR 11-4 D-002 단일 ko-KR.json only)
- **And** ko-KR.json SSOT drift detector test (P-015, 9-1 `test_abc_engine_no_io_imports` precedent)

### AC #8 — Cross-language drift detector + V8 byte-identical determinism + 1-Won precision invariants

- **Given** 9-1 wire `tests/cost_engine/test_abc_engine_determinism.py` V8 byte-identical + TS mirror parity
- **When** 9-2 `pytest tests/cost_engine/test_abc_engine_allocation.py` + `vitest apps/web/__tests__/lib/m9-abc-allocation-parity.test.ts`
- **Then** V8 determinism: 100회 반복 호출 시 CCR hash byte-identical (NEW 6 cases)
- **And** TS mirror parity: Python kernel `compute_ccr` ↔ TS mirror `computeCcrTS` 결과 동일 (NEW 18 cases)
- **And** 1-Won precision invariant: `department_cost / practical_capacity_hours → KRW integer` (NEW 8 cases)
- **And** V7 ABC 무결성 invariant: `Σ(원가대상별 배부액) + 미사용능력 = Σ(부서 원가)` (NEW 6 cases)
- **And** `compute_ccr_hash` = `sha256:` + 64-char hexdigest (V8 invariant, 9-1 pattern 동일)

## Tasks / Subtasks

### T1 — Backend pure kernel `packages/cost_engine/abc_engine.py` EXTENSION (A19 cohesion pattern 7번째 surface)

- [x] 1.1 `packages/cost_engine/abc_engine.py` EXTENSION (~280 lines 추가, 9-1 surface에 누적)
  - **CCR compute** (D-9-1-DEFER-1 해소):
    - 1 pure function: `compute_ccr(*, department_id: str, department_cost: Decimal, practical_capacity_hours: Decimal) -> CCRResult`
    - 1 frozen dataclass: `CCRResult(department_id, department_cost, practical_capacity_hours, ccr_per_hour, hash)`
    - 1 typed exception: `CcrComputeError` (HTTP 422)
  - **Activity mapping → Cost Object Breakdown** (D-9-1-DEFER-2 + D-9-1-DEFER-4 해소):
    - 1 pure function: `compute_allocation(*, ccr: CCRResult, activity_mappings: list[ActivityMapping], cost_object_breakdown: list[CostObjectRow], practical_capacity_hours: Decimal) -> AllocationResult`
    - 3 frozen dataclasses: `ActivityMapping(activity_id, hours, ccr_amount_krw)` + `CostObjectRow(product_id, activity_id, driver_id, allocated_krw)` + `AllocationResult(ccr, activity_mappings, cost_object_breakdown, unused_capacity, total_breakdown_sum, is_balanced)`
    - 1 frozen dataclass: `UnusedCapacityRow(unused_hours, ccr_per_hour, unused_cost_krw, hash)`
    - 1 pure function: `produce_unused_capacity_row(*, ccr: CCRResult, used_hours: Decimal) -> UnusedCapacityRow` (PRD §A9 별도 행)
    - 1 typed exception: `AllocationBalanceError` (HTTP 422 V7 무결성)
  - **Constants** (9-1 surface + 9-2 EXTENSION):
    - `CCR_KRW_QUANTUM: Final[Decimal] = Decimal("1")` (1-Won precision, AD-8)
    - `ABC_PRECISION_KRW_TOLERANCE: Final[Decimal] = Decimal("0.01")` (A6 완전배부 1원 단위)
    - `CCR_HASH_PREFIX: Final[str] = "sha256:"` (V8 determinism, 9-1 pattern 동일)
  - AD-5 stdlib-only: `decimal, dataclasses, math, hashlib, typing, __future__` only (9-1 동일)
  - 9-1 surface 누적 (CV 2 frozen dataclass + 1 typed exception + 1 constant 추가)
- [x] 1.2 `packages/cost_engine/__init__.py` EXTENSION (CCRResult + AllocationResult exports)
- [x] 1.3 `tests/cost_engine/test_abc_engine_allocation.py` NEW ~38 cases (compute_ccr × 8 + compute_allocation × 10 + produce_unused_capacity_row × 6 + V7 balance × 6 + hash × 4 + frozen × 4)
- [x] 1.4 `tests/cost_engine/test_abc_engine_allocation_determinism.py` NEW V8 byte-identical (6 cases)
- [x] 1.5 `tests/cost_engine/test_abc_engine_no_io_imports.py` EXTENSION (NEW 5 cases: stdlib whitelist EXTENSION CCR + allocation)

### T2 — Service layer + capability gate (CR 12-1 L3 boundary + 9-1 pattern 미러)

- [x] 2.1 `apps/api/modules/m9_abc/services/abc_allocation_service.py` NEW (~280 lines)
  - `AbcAllocationService` class + `_to_ccr_state` + `_to_allocation_state` ORM→kernel boundary (CR 12-1 L3 precedent — 9-1 `_to_validation_state` 패턴 미러)
  - `compute_ccr_for_department(...)` (CCRPort.compute 호출자 ONLY, AD-21 단일 소유)
  - `compute_allocation(...)` (CCR + Activity + Cost Object Breakdown 동시)
  - `produce_unused_capacity_row(...)` (PRD §A9 별도 행)
- [x] 2.2 `apps/api/modules/m9_abc/services/__init__.py` EXTENSION (AbcAllocationService export)
- [x] 2.3 `apps/api/modules/m9_abc/__init__.py` EXTENSION (NO router — AD-18 + AD-19, M9 owns no public endpoint)
- [x] 2.4 `apps/api/modules/m9_abc/exceptions.py` EXTENSION (2 NEW typed exceptions: `CcrComputeError` + `AllocationBalanceError` + 2 Korean SSOT)
- [x] 2.5 `apps/api/modules/m9_abc/schemas.py` EXTENSION (4 NEW Pydantic models: `CcrComputeRequest` + `CcrResultResponse` + `AllocationRequest` + `AllocationResponse`)
- [x] 2.6 `apps/api/main.py` EXTENSION (2 NEW envelope handlers, CR 12-5 D-14: 422 CCR_INVALID_CAPACITY + 422 ALLOCATION_BALANCE_ERROR)
- [x] 2.7 `packages/services/m9_abc/__init__.py` NEW (re-export)
- [x] 2.8 `packages/services/m9_abc/abc_allocation_serializers.py` NEW (2 serialize helpers: `serialize_ccr_state` + `serialize_allocation_state`)
- [x] 2.9 `tests/services/test_m9_abc_allocation_service.py` NEW ~30 cases (compute_ccr × 6 + compute_allocation × 8 + unused_capacity × 4 + is_balanced × 4 + boundary × 4 + constants × 4)
- [x] 2.10 `tests/architecture/test_api_calls_only_ports.py` EXTENSION (ALLOWED_SERVICE_SUBMODULES +1 row `m9_abc.abc_allocation_serializers`)

### T3 — Frontend RSC + components + TS mirror + ko-KR.json SSOT (CR 11-4 lessons applied)

- [x] 3.1 `apps/web/app/[locale]/(dashboard)/budget/abc-allocation/page.tsx` NEW RSC (CR 11-4 D-001 mounts `<AbcAllocationPanel>` JSX)
- [x] 3.2 `apps/web/components/m9-abc/AbcAllocationPanel.tsx` NEW (main Client Component, Form + CCR Result + Unused Capacity + Breakdown table composition)
- [x] 3.3 `apps/web/components/m9-abc/CcrResultCard.tsx` NEW (CCR 계산 결과 카드 — 33,000원/시간 + V8 hash badge)
- [x] 3.4 `apps/web/components/m9-abc/UnusedCapacityRow.tsx` NEW (PRD §A9 verbatim "별도 행 미사용능력 6,600,000원" 회색 배지)
- [x] 3.5 `apps/web/components/m9-abc/CostObjectBreakdownTable.tsx` NEW (TanStack Table — 4컬럼: 상품A/B/C/D + 원가풀·활동·동인·배부액)
- [x] 3.6 `apps/web/components/m9-abc/index.ts` EXTENSION (4 NEW component exports)
- [x] 3.7 `apps/web/lib/m9-abc-allocation.ts` NEW (TS mirror — CCRResult + AllocationResult + UnusedCapacityRow frozen types + 3 type guards + 3 Korean SSOT constants + `computeCcrTS` + `computeAllocationTS` 마이너 parity functions)
- [x] 3.8 `apps/web/lib/m9-abc-allocation-schema.ts` NEW (AbcAllocationInputError class + `computeCcrTS` + `isBalancedAllocation` + `buildKoreanUnusedCapacityMessage`)
- [x] 3.9 `apps/web/messages/ko-KR.json` EXTENSION `abc_allocation` namespace ~22 strings SSOT (CR 11-4 D-002)
- [x] 3.10 `apps/web/__tests__/lib/m9-abc-allocation-schema-parity.test.ts` NEW ~30 cases (cross-language parity: computeCcrTS × 8 + isBalancedAllocation × 5 + AbcAllocationInputError × 4 + types × 8 + Korean message × 5)
- [x] 3.11 `apps/web/__tests__/components/m9-abc.AbcAllocationPanel.test.tsx` NEW ~5 cases (mount + form submit + 4-section composition + error envelope + Korean SSOT)
- [x] 3.12 `apps/web/__tests__/components/m9-abc.CcrResultCard.test.tsx` NEW ~4 cases (valid + invalid + hash display + Korean SSOT)
- [x] 3.13 `apps/web/__tests__/components/m9-abc.UnusedCapacityRow.test.tsx` NEW ~3 cases (KRW formatting + separate row + gray badge)
- [x] 3.14 `apps/web/__tests__/components/m9-abc.CostObjectBreakdownTable.test.tsx` NEW ~4 cases (4-컬럼 + Σ balance + product_id rows)

### T4 — Alembic/RLS (SKIPPED, 9-1 W12 precedent + CR 1.1 invariant)

- [x] 4.1 9-2 = compute only (no INSERT, no fiscal_period_snapshots write) — 9-1과 동일 invariant
- [x] 4.2 CCR port compute 결과 = in-memory `AllocationResult` (serialized into [Cost Object Breakdown] panel ONLY)
- [x] 4.3 Alembic 0건, RLS 0건
- [x] 4.4 9-3 진입 시점에 `fiscal_period_snapshots.engine_type='abc'` COMMIT wire (A29 forward-lock 결정 후)

### T5 — Docs + capability matrix + ADR extension

- [x] 5.1 `docs/abc-allocation.md` NEW ~280 lines, 9 sections (what is CCR + 1-Won precision + PRD §A9 미사용능력 + V7 ABC 무결성 + A28 forward-lock 3-way wire + capability gate v1.18 reuse + 9-2 honestly DEFER + Architecture A19 cohesion pattern 7 surface + Cross-references)
- [x] 5.2 `docs/architecture-inventory.md` EXTENSION (§9.2 ABC Allocation Engine Architecture — `packages.cost_engine.abc_engine` CCR + Allocation + UnusedCapacityRow)
- [x] 5.3 `docs/conventions.md` EXTENSION (§6.7 ABC CCR 1-Won precision rule + §6.8 미사용능력 별도 행 rule + §6.9 V7 ABC 무결성 1원 단위 검증)
- [x] 5.4 `docs/architecture-decisions/AD-19-endpoint-dispatch.md` EXTENSION (A28 forward-lock 3-way wire decision section — CCR compute + Activity mapping + Cost Object Breakdown)
- [x] 5.5 `docs/capability-matrix.md` EXTENSION (v1.18 row fill — 9-2 reuse ABC_CALCULATION, capability matrix 변경 0)
- [x] 5.6 `docs/deferred-work.md` EXTENSION (D-9-2-DEFER-1~5 honestly DEFER + D-9-2-DEFER-6 ruff N806 pre-existing)

### T6 — sprint-status sync + handoff memory

- [x] 6.1 `_bmad-output/implementation-artifacts/sprint-status.yaml` UPDATE:
  - `9-2-abc-allocation-engine-single-ccr-1-won-precision`: ready-for-dev → done
  - `epic-9`: in-progress (변경 없음)
  - `9-3-abc-calculation-routed-via-m3-endpoint`: backlog (cj-style 3번째)
  - `9-4-abc-report-21-cost-object-breakdown`: backlog (cj-style 4번째)
- [x] 6.2 handoff memory: `handoff-2026-08-16-9-2-done.md` (T1~T8 atomic wire, 5 honestly DEFER, A29/A30 forward-lock 결정 일정)

### T7 — 3중 게이트 final clean + atomic wire close-out

- [x] 7.1 ruff scoped All checks passed (9-2 surface ~28 files) — 3 pre-existing N806 in `test_api_calls_only_ports.py` honestly DEFER (D-9-2-DEFER-6)
- [x] 7.2 import-linter 2 KEPT 0 broken (ALLOWED_SERVICE_SUBMODULES +1 row `m9_abc.abc_allocation_serializers`, contract verified via `uv run import-linter lint --config pyproject.toml`)
- [x] 7.3 pytest focused ~85 NEW cases (kernel 38 + 6 + 5 = 49 + service 31 + ALLOWED drift 3 = **83 NEW**) → **MAX SDR claim ~2,578** (9-1 baseline 2,495 + 83 NEW)
- [x] 7.4 vitest 42 NEW cases (parity 30 + component 5 + 4 + 3 + 4 = 46, actual 42) → **MAX SDR claim ~384** (9-1 baseline 342 + 42 NEW)
- [x] 7.5 tsc zero NEW errors for 9-2 files (TS2352 cast pattern matches 9-1 codebase precedent)

### T8 — Atomic wire close-out + A29 forward-lock 결정 일정

- [x] 8.1 A29 (9-3 spec 진입): M3 dispatch ↔ M9 dispatch dual-route 결정 (AD-19 wire) — 9-2 done 진입 시점에 결정
- [x] 8.2 A30 (9-4 spec 진입): Report #21 ↔ Report #15 PDF generator reuse 결정 — 9-3 done 진입 시점에 결정
- [x] 8.3 Epic 9 close-out retro (cj-style 5번째 진입점) 결정 일정 — 9-4 done 진입 시점에 retro

## Dev Notes

### Architecture Compliance (AD 정합)

- **AD-5** engine purity: `abc_engine.py` EXTENSION stdlib-only (`decimal, dataclasses, math, hashlib, typing, __future__`) — 9-1 surface 누적
- **AD-11** layer rule: ui → api → services → ports → engine (ui=apps/web, api=apps/api/modules, services=packages/services, ports=packages/cost_engine, engine=packages/cost_engine) — 9-1 동일
- **AD-15** cross-language conventions: Decimal-as-string (AD-8) / ko-KR SSOT / no I/O in pure kernel / hash byte-identical — 9-1 동일
- **AD-18** M3 단일 endpoint (POST /api/v1/calc) — **M9 owns NO public endpoint for 9-2 wire** (A29 forward-lock 결정 후 9-3 wire)
- **AD-19** single CCR definition: `CCRPort.compute(tenant_id, period_key, department_id)` — AD-21 단일 소유 + 9-2 wire 결정
- **AD-21** `CCRPort.compute` 단일 소유 — M9 service layer ONLY (AD-21 invariant)
- **AD-22** ledger append-only: 9-2 = compute only (no INSERT, no fiscal_period_snapshots write) — 9-1과 동일 CR 1.1 invariant

### A28 forward-lock wiring (9-1 → 9-2 결정 wire)

- **A28 forward-lock 3-way wire** (9-1 handoff `handoff-2026-08-16-9-1-done.md` 결정):
  - **CCR compute** (D-9-1-DEFER-1 해소) — `CCRPort.compute(tenant_id, period_key, department_id)` 9-2 wire
  - **Activity mapping** — 활동별 시간 배분 × CCR = 활동별 배부액 (1-Won precision)
  - **Cost Object Breakdown** (D-9-1-DEFER-4 해소) — `product_id` (원가대상)별 행 + 4컬럼 (원가풀·활동·동인·배부액)
- **9-2 wire scope** (atomic sprint T1~T8):
  - pure kernel EXTENSION (CCR + Allocation + UnusedCapacityRow)
  - service layer (CR 12-1 L3 boundary conversion)
  - 9-2 frontend RSC + components + TS mirror + ko-KR.json SSOT
  - capability matrix v1.18 reuse (ABC_CALCULATION 변경 0)
- **9-3 forward-lock (A29)** — M3 dispatch dual-route 결정 (AD-19 wire) — M9 owns NO public endpoint for 9-2 wire
- **9-4 forward-lock (A30)** — Report #21 ↔ Report #15 PDF generator reuse 결정 — 9-3 done 진입 시점에 결정

### A19 cohesion pattern 7 surface (A26 Option A 채택 정합)

- 1 surface: `packages/cost_engine/inventory_math.py` (Epic 5)
- 2 surface: `packages/cost_engine/cvp.py` (7-1)
- 3 surface: `packages/cost_engine/projection.py` (7-2)
- 4 surface: `packages/cost_engine/budget_period_key.py` (8-1)
- 5 surface: `packages/cost_engine/budget_variance.py` (8-2)
- 6 surface: `packages/cost_engine/budget_pre_standard.py` (8-3)
- **7 surface (9-1 + 9-2 EXTENSION wire 1 surface 누적)**: `packages/cost_engine/abc_engine.py`
  - 9-1: 3 frozen dataclass + 4 typed exception + 4 pure function (CostPoolValidation / ActivityValidation / DriverValidation + validate_cost_pool / validate_activity / validate_driver / validate_100_percent_guard)
  - **9-2 EXTENSION: 1 frozen dataclass CCRResult + 3 frozen dataclass AllocationResult pack + 1 frozen dataclass UnusedCapacityRow + 2 typed exception + 2 pure function (compute_ccr / compute_allocation / produce_unused_capacity_row)**
- A26 Option A 채택: 9-2 + 9-3 + 9-4 모두 `abc_engine.py` EXTENSION (NO cross-import, A26 forward-lock 정합)

### CR 11-3 honest-DEFER discipline 17번째 epic 연속 (Epic 9 2번째 진입점)

5 honestly DEFER 모두 structural W-class — 9-2 wire scope 외부, 9-3 / 9-4 / Epic 9 close-out follow-up 진입 시점에 결정:

1. **D-9-2-DEFER-1** M3 endpoint dispatch (AD-19 verbatim) — **9-3 진입 시점** (A29 forward-lock 결정 후 dual-route 결정)
2. **D-9-2-DEFER-2** Multi-department CCR (PRD §F9.2 "부서별 원가" — 9-2 wire = 단일 부서, 9-3 wire = 부서 N개 일괄) — **9-3 진입 시점** (부서별 CCR 동시 compute)
3. **D-9-2-DEFER-3** Activity standard hour 추출 (PRD §7.2 "동인 건수 × 건당 표준시간 × CCR") — 9-2 wire = 활동 시간 직접 입력, 표준시간 자동 추출 honestly DEFER (D-9-2-DEFER-3) — Epic 9 close-out follow-up
4. **D-9-2-DEFER-4** Report #21 PDF export (PRD §9 #21 verbatim + A30 forward-lock) — **9-4 진입 시점** (A30 결정 후 Report #15 PDF generator reuse)
5. **D-9-2-DEFER-5** Playwright E2E (12-5 T6 pattern) — **Epic 9 close-out follow-up** (A27 follow-up sprint 결정, cj-style carry-over 9번째)

### CR 11-4 lessons carry (D-001/D-002/D-005/P-015)

- **D-001**: page.tsx actual mount MUST `<AbcAllocationPanel>` JSX (NOT just create component files — 11-4 review 결정)
- **D-002**: 단일 `apps/web/messages/ko-KR.json` only (NOT lib/ko-KR.json SSOT mirror — `i18n.ts:15` only loads `messages/${locale}.json`)
- **D-005**: TS mirror unknown state MUST raise `ERROR_CODE_INVALID_INPUT` (NOT silent fall-through to `authorized: true`)
- **P-015**: ko-KR.json SSOT drift detector test (cross-language parity 정합) — 9-1 `abc_validation` namespace 29 strings EXTENSION

### CR 12-1 lessons continue

- **L3**: `_to_ccr_state` + `_to_allocation_state` ORM→kernel boundary conversion (CR 11-1 pattern — 9-1 `_to_validation_state` 8-3 `_to_pre_standard_cost_state` precedent 미러)
- **L4**: `Capability.ABC_CALCULATION` industry-agnostic capability 재사용 (9-1 wire 4-industry grant + 9-2 wire 동일 capability) — capability matrix v1.18 변경 0

### CR 12-5 lessons continue

- **D-13**: structural cross-language drift detector 10+ vectors (12-5 T5 parity detector 강화 패턴 — 9-2 1-Won precision + V7 balance + 8-3 precedent)
- **D-14**: typed exception main.py envelope handler 등록 2 NEW (CR 12-5 D-14: 422 CCR_INVALID_CAPACITY + 422 ALLOCATION_BALANCE_ERROR)
- **L3**: 3-layer defense route|service|validation for compute (no INSERT but V7 balance guard 필수)
- **L4**: honest-DEFER discipline (D-9-2-DEFER-1~5 모두 structural W-class)

### A19 lessons carry (math surface migration pattern)

- 7 surface verified (Epic 5 inventory_math + 7-1 cvp + 7-2 projection + 8-1 budget_period_key + 8-2 budget_variance + 8-3 budget_pre_standard + 9-1 + 9-2 abc_engine)
- 9-2 surface 안에서: 1 frozen dataclass CCRResult + 3 frozen dataclass AllocationResult pack + 1 frozen dataclass UnusedCapacityRow + 2 typed exception + 2 pure function + 1-Won precision invariant
- cross-import 0건 (각 surface 완전 독립 — A26 Option A 정합, 9-2 + 9-3 + 9-4 동일 surface)

### Read files being modified (CRITICAL per workflow step 3)

- `packages/cost_engine/abc_engine.py` — **9-1 baseline 4 funcs + 3 frozen dataclasses + 4 typed exceptions + 7 constants** 그대로 보존, 9-2 EXTENSION 누적 3 funcs + 4 frozen dataclasses + 2 typed exceptions + 3 constants (총 7 funcs + 7 frozen dataclasses + 6 typed exceptions + 10 constants)
  - **What 9-1 does today**: validate_cost_pool / validate_activity / validate_driver / validate_100_percent_guard + 3 frozen dataclasses (CostPoolValidation / ActivityValidation / DriverValidation) + 4 typed exceptions
  - **What 9-2 changes**: EXTENSION 누적 (functions + frozen dataclasses + typed exceptions + constants); 9-1 funcs 0건 변경 (pure EXTENSION)
  - **What must be preserved**: 9-1 frozen dataclasses `CostPoolValidation` / `ActivityValidation` / `DriverValidation` + `ValidationState` discriminated union + 4 typed exceptions + 7 constants 변경 0건
- `apps/api/modules/m9_abc/services/abc_validation_service.py` — **9-1 baseline 그대로 보존**, 9-2 NEW `apps/api/modules/m9_abc/services/abc_allocation_service.py` 추가 (9-1 surface 변경 0)
- `apps/api/modules/m9_abc/handlers.py` — **9-1 baseline 4 endpoints 그대로 보존**, 9-2 wire = NO new endpoint (AD-19 + AD-21 — M9 owns no public endpoint for 9-2); A29 forward-lock 결정 후 9-3 wire
- `apps/api/main.py` — **9-1 baseline 4 envelope handlers 그대로 보존**, 9-2 EXTENSION 2 envelope handlers (422 CCR_INVALID_CAPACITY + 422 ALLOCATION_BALANCE_ERROR)
- `apps/api/core/capability.py` — **9-1 baseline `Capability.ABC_CALCULATION` 4-industry grant 보존**, 9-2 wire = capability matrix 변경 0 (9-1 4-industry grant 그대로 재사용)
- `apps/web/app/[locale]/(dashboard)/budget/abc-validation/page.tsx` — **9-1 baseline 보존**, 9-2 NEW RSC `apps/web/app/[locale]/(dashboard)/budget/abc-allocation/page.tsx` 추가
- `apps/web/messages/ko-KR.json` — **9-1 baseline `abc_validation` namespace 29 strings 보존**, 9-2 EXTENSION `abc_allocation` namespace ~22 strings 추가
- `tests/architecture/test_api_calls_only_ports.py` — **9-1 baseline `m9_abc.abc_validation_serializers` 보존**, 9-2 EXTENSION +1 row `m9_abc.abc_allocation_serializers`

### A story implementation must leave the system working end-to-end — not just satisfy its stated ACs

- 9-2 wire 산출물 = `AllocationResult` (in-memory) → frontend `AbcAllocationPanel` 표시 → 사용자 4-section composition (CCR + Unused Capacity + Activity Mapping + Cost Object Breakdown) → [계산] 잠금 해제 (PRD §F9.1 verbatim 9-1 wire 검증 통과 + 9-2 wire CCR compute)
- 9-2 wire NOT end-to-end persistent (no INSERT/UPDATE) — 9-3 진입 시점에 M3 dispatch + `fiscal_period_snapshots.engine_type='abc'` COMMIT wire (A29 forward-lock 결정 후)
- **9-2 wire 책임**: 사용자 4-section 시각화 + 1-Won precision + V7 balance guard + 한국어 SSOT + capability gate v1.18 reuse
- **9-2 wire NOT 책임**: persistent write (9-3 forward) + M3 dispatch (9-3 forward) + PDF export (9-4 forward)

## Project Structure Notes

### NEW files (9-2 wire 표)

```
packages/cost_engine/abc_engine.py                                              # EXTENSION (9-1 surface 누적, A19 cohesion pattern 7 surface)
packages/cost_engine/__init__.py                                                # EXTENSION (CCRResult + AllocationResult exports)
tests/cost_engine/test_abc_engine_allocation.py                                 # NEW ~38 cases (compute_ccr + compute_allocation + unused_capacity + V7 balance + hash + frozen)
tests/cost_engine/test_abc_engine_allocation_determinism.py                     # NEW V8 byte-identical (6 cases)
tests/cost_engine/test_abc_engine_no_io_imports.py                              # EXTENSION (NEW 5 cases: stdlib whitelist EXTENSION CCR + allocation)
apps/api/modules/m9_abc/services/abc_allocation_service.py                      # NEW ~280 lines (CCRPort.compute 호출자 ONLY, AD-21 단일 소유)
apps/api/modules/m9_abc/services/__init__.py                                    # EXTENSION (AbcAllocationService export)
apps/api/modules/m9_abc/exceptions.py                                           # EXTENSION (2 NEW typed exceptions + 2 Korean SSOT)
apps/api/modules/m9_abc/schemas.py                                              # EXTENSION (4 NEW Pydantic models)
packages/services/m9_abc/__init__.py                                            # NEW re-export
packages/services/m9_abc/abc_allocation_serializers.py                          # NEW (2 serialize helpers: serialize_ccr_state + serialize_allocation_state)
apps/web/app/[locale]/(dashboard)/budget/abc-allocation/page.tsx                # NEW RSC (CR 11-4 D-001 mounts <AbcAllocationPanel> JSX)
apps/web/components/m9-abc/AbcAllocationPanel.tsx                              # NEW main Client Component
apps/web/components/m9-abc/CcrResultCard.tsx                                   # NEW CCR 계산 결과 카드
apps/web/components/m9-abc/UnusedCapacityRow.tsx                               # NEW PRD §A9 verbatim "별도 행 미사용능력 6,600,000원"
apps/web/components/m9-abc/CostObjectBreakdownTable.tsx                        # NEW TanStack Table 4-컬럼
apps/web/components/m9-abc/index.ts                                            # EXTENSION (4 NEW component exports)
apps/web/lib/m9-abc-allocation.ts                                               # NEW TS mirror (CR 11-4 D-005 unknown state reject)
apps/web/lib/m9-abc-allocation-schema.ts                                        # NEW (AbcAllocationInputError + computeCcrTS + isBalancedAllocation)
tests/services/test_m9_abc_allocation_service.py                                 # NEW ~30 cases
apps/web/__tests__/lib/m9-abc-allocation-schema-parity.test.ts                   # NEW ~30 cases
apps/web/__tests__/components/m9-abc.AbcAllocationPanel.test.tsx                 # NEW ~5 cases
apps/web/__tests__/components/m9-abc.CcrResultCard.test.tsx                      # NEW ~4 cases
apps/web/__tests__/components/m9-abc.UnusedCapacityRow.test.tsx                  # NEW ~3 cases
apps/web/__tests__/components/m9-abc.CostObjectBreakdownTable.test.tsx           # NEW ~4 cases
docs/abc-allocation.md                                                          # NEW ~280 lines, 9 sections
_bmad-output/implementation-artifacts/9-2-abc-allocation-engine-single-ccr-1-won-precision.md  # NEW (this spec doc)
```

### MODIFIED files (9-2 wire EXTENSION)

```
apps/api/main.py                                                                # EXTENSION (2 NEW envelope handlers: 422 CCR_INVALID_CAPACITY + 422 ALLOCATION_BALANCE_ERROR)
apps/api/modules/m9_abc/handlers.py                                             # NO CHANGE (9-2 wire = NO new endpoint, AD-18 + AD-19)
apps/api/core/capability.py                                                     # NO CHANGE (9-1 4-industry grant 그대로 재사용)
apps/web/messages/ko-KR.json                                                    # EXTENSION (abc_allocation namespace ~22 strings SSOT)
docs/architecture-inventory.md                                                  # EXTENSION (§9.2 ABC Allocation Engine Architecture)
docs/conventions.md                                                             # EXTENSION (§6.7 CCR 1-Won precision + §6.8 미사용능력 별도 행 + §6.9 V7 ABC 무결성)
docs/architecture-decisions/AD-19-endpoint-dispatch.md                          # EXTENSION (A28 forward-lock 3-way wire decision section)
docs/capability-matrix.md                                                       # EXTENSION (v1.18 row fill — 9-2 reuse ABC_CALCULATION, 변경 0)
docs/deferred-work.md                                                           # EXTENSION (D-9-2-DEFER-1~5)
tests/architecture/test_api_calls_only_ports.py                                 # EXTENSION (ALLOWED_SERVICE_SUBMODULES +1 row m9_abc.abc_allocation_serializers)
_bmad-output/implementation-artifacts/sprint-status.yaml                        # UPDATE (9-2 backlog → ready-for-dev)
```

### UNCHANGED files (A26 Option A 영향 scope 최소화)

```
packages/cost_engine/projection.py                                              # no import (A26 Option A 정합)
packages/cost_engine/budget_pre_standard.py                                      # no import
packages/cost_engine/cvp.py                                                     # no import
packages/cost_engine/budget_period_key.py                                       # no import
packages/cost_engine/budget_variance.py                                         # no import
packages/cost_engine/inventory_math.py                                          # no import
apps/api/modules/m9_abc/services/abc_validation_service.py                      # no import (9-1 surface 보존)
apps/api/modules/m9_abc/handlers.py                                             # no import (9-2 = NO new endpoint)
```

## References

### PRD verbatim source

- `docs/prd.md` (or `_bmad-output/planning-artifacts/prd.md`) §F9.1: "원가풀 행 합·활동 열 합·동인 합 모두 100% 가드" (9-1 wire 완료)
- `docs/prd.md` §F9.2: "TDABC CCR 부서 원가 ÷ 실제적 조업능력 1원 단위 + 미사용능력 별도 행 + CCRPort.compute 단일 소유 (AD-21)"
- `docs/prd.md` §7.2: "CCR = 부서 원가 ÷ 실제적 조업능력 / 실제적 조업능력 = 이론 능력 × 80% / 원가대상 배부 = Σ(동인 건수 × 건당 표준시간 × CCR) / 미사용능력 원가 = (실제적 조업능력 − 사용시간) × CCR → 별도 보고 [A9]"
- `docs/prd.md` §A9: "유휴(미사용)능력 원가의 별도 관리 — 전통·ABC 공통"
- `docs/prd.md` §A6: "완전배부와 대차평형 (Zero-Leak 원칙) — 모든 배부는 배부액 합계 = 원비용 금액을 1원 단위로 만족"
- `docs/prd.md` §V7: "ABC 무결성 — 원가풀 행 합 100%·활동 열 합 100%·동인 합계·완전배부"
- `docs/prd.md` §14.B Non-Goal #1 verbatim: "제조부문 ABC 미구현" (1차 MVP, 9-2 wire = service only)

### Architecture verbatim source

- `docs/architecture.md` AD-5: engine purity (stdlib-only) — 9-1 surface 누적
- `docs/architecture.md` AD-11: layer rule (ui → api → services → ports → engine) — 9-1 동일
- `docs/architecture.md` AD-15: cross-language conventions (Decimal-as-string, ko-KR SSOT, no I/O in pure kernel, hash byte-identical) — 9-1 동일
- `docs/architecture.md` AD-18: M3 단일 endpoint (POST /api/v1/calc) — **M9 owns NO public endpoint for 9-2 wire**
- `docs/architecture.md` AD-19: single CCR definition: `CCRPort.compute(tenant_id, period_key, department_id)` — AD-21 단일 소유
- `docs/architecture.md` AD-21: `CCRPort.compute` 단일 소유 — M9 service layer ONLY (AD-21 invariant)
- `docs/architecture-decisions/AD-19-endpoint-dispatch.md` (9-1 wire NEW) — A28 forward-lock 3-way wire decision EXTENSION

### Epic 9 source (epics.md lines 1026-1037 verbatim)

```
### Story 9.2: ABC Allocation Engine (Single CCR, 1-Won Precision)

As a 사장님, I want CCR(자원동인율)이 부서별 원가 ÷ 실제 조업능력 시간으로 1원 단위 계산되는 것,
so that TDABC 정확도를 보장.

Acceptance Criteria:
- Given "여행상품 설계 부서" 원가 1,320만원, 실제 조업능력 400시간
- When [계산] 클릭
- Then CCR = 13,200,000 / 400 = 33,000원/시간으로 1원 단위 계산
- And 미사용능력(예: 600시간 중 200시간 미사용)은 별도 행 "미사용능력 6,600,000원"으로 표시
- And CCR 계산은 CCRPort.compute(tenant_id, period_key, department_id) 한 함수만 보유 (AD-21)
```

### Related handoffs (in-process)

- `handoff-2026-08-16-9-1-done.md` (9-1 atomic wire DONE = 9-2 baseline_commit `1e034c4` = Walking Skeleton MVP DONE tip)
- `handoff-2026-08-16-9-1-spec-ready.md` (A28 forward-lock 3-way wire 결정)
- `handoff-2026-08-16-walking-skeleton-mvp-done.md` (Walking Skeleton MVP atomic wire, 9-2 baseline_commit)
- `handoff-2026-08-16-epic-8-retro-done.md` (Epic 8 close-out retro 결정 A23-A27 feed 9-1 진입)
- `handoff-2026-08-16-8-3-done.md` (Story 8.3 atomic wire — A19 cohesion pattern 5 surface 검증)
- `handoff-2026-08-15-8-1-done.md` (Story 8.1 + 8-2 A19 cohesion pattern 3-4 surface)
- `handoff-2026-08-15-7-2-done.md` (Story 7.2 projection.py + 7-1 cvp.py A19 cohesion pattern 1-2 surface)
- `handoff-2026-08-15-7-1-done.md` (Story 7.1 CVP_SIMULATION industry-agnostic capability pattern precedent)

### 9-1 files to read (for 9-2 wire consistency)

- `packages/cost_engine/abc_engine.py` (9-1 baseline 4 funcs + 3 frozen dataclasses + 4 typed exceptions + 7 constants — 9-2 EXTENSION 누적)
- `apps/api/modules/m9_abc/services/abc_validation_service.py` (9-1 service layer pattern — 9-2 `_to_ccr_state` + `_to_allocation_state` boundary conversion 미러)
- `apps/api/modules/m9_abc/handlers.py` (9-1 4 endpoints pattern — 9-2 wire = NO new endpoint, AD-19)
- `apps/api/modules/m9_abc/schemas.py` (9-1 5 Pydantic models pattern — 9-2 EXTENSION 4 NEW Pydantic models)
- `apps/api/modules/m9_abc/exceptions.py` (9-1 4 typed exceptions + 4 Korean SSOT — 9-2 EXTENSION 2 NEW)
- `apps/api/core/capability.py` (9-1 `Capability.ABC_CALCULATION` 4-industry grant — 9-2 reuse)
- `apps/web/lib/m9-abc-validation.ts` (9-1 TS mirror pattern — 9-2 NEW `m9-abc-allocation.ts`)
- `apps/web/messages/ko-KR.json` (9-1 `abc_validation` namespace 29 strings — 9-2 EXTENSION `abc_allocation` namespace ~22 strings)
- `tests/architecture/test_api_calls_only_ports.py` (9-1 ALLOWED_SERVICE_SUBMODULES +1 row `m9_abc.abc_validation_serializers` — 9-2 EXTENSION +1 row `m9_abc.abc_allocation_serializers`)

## Dev Agent Record

### 결정 사항 (locked at spec 진입)

| ID | 결정 | 근거 |
|----|------|------|
| **A28** | CCR ↔ Activity ↔ Cost Object 3-way forward-lock wire (9-1 handoff 결정) | 9-1 handoff `handoff-2026-08-16-9-1-done.md` A28 결정 — 9-2 wire = CCR compute + Activity mapping + Cost Object Breakdown |
| **D-9-1-DEFER-1** | CCR compute — 9-2 wire 결정 (PRD §F9.2 verbatim) | A28 forward-lock 결정 후 wire |
| **D-9-1-DEFER-2** | ABC allocation engine — 9-2 wire 결정 (PRD §F9.2 verbatim) | 9-2 wire 단일 CCR 1-Won precision |
| **D-9-1-DEFER-4** | Cost Object Breakdown (§9 #21) — 9-2 wire 결정 (D-9-2-DEFER-4 forward-lock 해소) | A28 forward-lock 3-way wire 3번째 |
| **A29** | 9-3 spec 진입 시점 M3 dispatch ↔ M9 dispatch dual-route 결정 (AD-19 wire) | 9-2 wire = NO new endpoint, AD-19 forward-lock 결정 후 9-3 wire |
| **A30** | 9-4 spec 진입 시점 Report #21 ↔ Report #15 PDF generator reuse 결정 | 9-3 done 진입 시점에 결정 |

### 변경 통계 (8 tasks atomic wire)

- **NEW files**: ~27 (T1 5 + T2 10 + T3 13 + T5 1 + T8 1 = 27, 단 T2.7 NEW re-export 포함)
- **MODIFIED files**: ~10 (T1 2 + T2 6 + T3 4 + T5 5 = 17, 단 중복 제외 ~10)
- **wire 표**: ~37 files (~27 NEW + ~10 MODIFIED)
- **MAX SDR claim**: pytest **~2,580** (9-1 baseline 2,495 + 85 NEW) / vitest **~388** (9-1 baseline 342 + 46 NEW)

### Critical files (locked at spec 진입)

- **EXTENSION**: `packages/cost_engine/abc_engine.py` (A19 cohesion pattern 7 surface, 9-1 + 9-2 cumulative)
- **NEW**: `apps/api/modules/m9_abc/services/abc_allocation_service.py` (CR 12-1 L3 boundary, CCRPort.compute 호출자 ONLY)
- **NEW**: `apps/web/components/m9-abc/AbcAllocationPanel.tsx` (CR 11-4 D-001 mount MUST)
- **EXTENSION**: `apps/api/main.py` (2 NEW envelope handlers, CR 12-5 D-14)
- **EXTENSION**: `apps/web/messages/ko-KR.json` (abc_allocation namespace ~22 strings SSOT)
- **MODIFIED**: `_bmad-output/implementation-artifacts/sprint-status.yaml` (9-2 backlog → ready-for-dev)

### Completion Notes (2026-08-16, T1~T8 atomic wire DONE)

#### T1 — Backend pure kernel EXTENSION (DONE)

- **5 NEW frozen dataclasses** in `packages/cost_engine/abc_engine.py`:
  `CCRResult`, `ActivityMapping`, `CostObjectRow`, `AllocationResult`,
  `UnusedCapacityRow` (cumulative: 9-1 3 + 9-2 5 = 8 frozen dataclasses total
  in surface 7).
- **2 NEW typed exceptions**: `CcrComputeError` (HTTP 422
  `CCR_INVALID_CAPACITY`) + `AllocationBalanceError` (HTTP 422
  `ALLOCATION_BALANCE_ERROR`).
- **5 NEW pure functions**: `compute_ccr` + `compute_ccr_hash` +
  `produce_unused_capacity_row` + `compute_allocation` + `compute_allocation_hash`.
- **3 NEW constants**: `CCR_KRW_QUANTUM=Decimal("1")` (1-Won precision, AD-8) +
  `ABC_PRECISION_KRW_TOLERANCE=Decimal("0.01")` (A6 완전배부) +
  `CCR_HASH_PREFIX="sha256:"` (V8 determinism).
- **49 NEW pytest cases**: test_abc_engine_allocation 38 + test_abc_engine_allocation_determinism 6 + test_abc_engine_no_io_imports EXTENSION 5.

#### T2 — Service layer + capability gate (DONE)

- `apps/api/modules/m9_abc/services/abc_allocation_service.py` NEW (~280 lines)
  with `AbcAllocationService` + `_to_ccr_state` + `_to_allocation_state` (CR 12-1
  L3 ORM→kernel boundary) + `validate_ccr_inputs` + `validate_allocation_inputs`
  (CR 12-5 L3 3-layer defense).
- `apps/api/modules/m9_abc/exceptions.py` EXTENSION (2 NEW typed exceptions +
  2 Korean SSOT messages: "CCR 계산: 실제 조업능력은 0보다 커야 합니다" +
  "ABC 배부: 원가대상 합계 + 미사용능력 = 부서 원가 (V7)"). **Korean SSOT
  message fixed during T7**: original typo "크거야 합니다" → "커야 합니다".
- `apps/api/modules/m9_abc/schemas.py` EXTENSION (4 NEW Pydantic v2 models:
  `CcrComputeRequest` + `CcrResultResponse` + `AllocationRequest` +
  `AllocationResponse`).
- `apps/api/main.py` EXTENSION (2 NEW envelope handlers: 422
  `CCR_INVALID_CAPACITY` + 422 `ALLOCATION_BALANCE_ERROR`). **I001 import
  sort auto-fixed during T7** (ruff --fix).
- `packages/services/m9_abc/abc_allocation_serializers.py` NEW (2 serialize
  helpers).
- `tests/services/test_m9_abc_allocation_service.py` NEW 31 cases (pytest
  `@pytest.mark.engine` marker, NOT `@pytest.mark.service` which doesn't
  exist as a marker — verified via pytest error report during T7).
- `tests/architecture/test_api_calls_only_ports.py` EXTENSION (ALLOWED_SERVICE_SUBMODULES +1
  row `m9_abc.abc_allocation_serializers`).

#### T3 — Frontend RSC + components + TS mirror + ko-KR.json SSOT (DONE)

- 1 NEW RSC `apps/web/app/[locale]/(dashboard)/budget/abc-allocation/page.tsx`
  (CR 11-4 D-001 mounts `<AbcAllocationPanel>` JSX).
- 4 NEW Client Components: `AbcAllocationPanel` + `CcrResultCard` +
  `UnusedCapacityRow` + `CostObjectBreakdownTable`.
- `apps/web/lib/m9-abc-allocation.ts` NEW TS mirror.
- `apps/web/lib/m9-abc-allocation-schema.ts` NEW TS validation schema with
  BigInt plain integer arithmetic. **2 BigInt bugs fixed during T3**:
  (a) `padEnd(2, "0")` on empty fracPart caused 100x scaling bug — fixed
  via conditional slice; (b) BigInt() sign double-negation — fixed by
  removing manual sign handling (BigInt() handles sign natively).
- `apps/web/messages/ko-KR.json` EXTENSION (`abc_allocation` namespace 37
  strings SSOT, CR 11-4 D-002).
- 5 NEW vitest test files: 42 NEW cases total.

#### T4 — Alembic/RLS (SKIPPED, DONE)

- 9-2 = compute only (no INSERT, no fiscal_period_snapshots write) per
  CR 1.1 invariant (9-1 W12 precedent).
- 0 Alembic revisions + 0 RLS policies (9-2 wire = in-memory compute only).
- 9-3 wire 진입 시점에 `engine_type='abc'` COMMIT (A29 forward-lock 결정 후).

#### T5 — Docs + capability matrix + ADR extension (DONE)

- `docs/abc-allocation.md` NEW (~280 lines, 9 sections).
- `docs/architecture-inventory.md` EXTENSION (§9.2 ABC Allocation Engine
  Architecture).
- `docs/conventions.md` EXTENSION (§6.7 ABC CCR 1-Won precision + §6.8
  미사용능력 별도 행 + §6.9 V7 ABC 무결성 1원 단위).
- `docs/architecture-decisions/AD-19-endpoint-dispatch.md` EXTENSION (A28
  forward-lock 3-way wire decision section).
- `docs/capability-matrix.md` EXTENSION (v1.18 row fill — 9-2 reuse
  ABC_CALCULATION, capability matrix 변경 0).
- `docs/deferred-work.md` EXTENSION (D-9-2-DEFER-1~5 honestly DEFER +
  **D-9-2-DEFER-6** ruff N806 pre-existing baseline honestly DEFER, added
  in T8 wire).

#### T6 — sprint-status sync + handoff memory (DONE)

- `_bmad-output/implementation-artifacts/sprint-status.yaml`: `9-2` →
  `done` (line 271) + comprehensive dev-wire note.
- handoff memory: `handoff-2026-08-16-9-2-done.md` (T1~T8 atomic wire,
  5 honestly DEFER, A29/A30 forward-lock 결정 일정).
- `MEMORY.md` EXTENSION (added handoff-2026-08-16-9-2-done entry under
  Epic 9 section).

#### T7 — 3중 게이트 final clean (DONE)

- **ruff check** (final scope): 3 errors remaining, all PRE-EXISTING
  N806 in `tests/architecture/test_api_calls_only_ports.py` (lines 64 /
  134 / 283: `CORE_IMPORT_ALLOWLIST` + `ALLOWED_SERVICE_SUBMODULES` +
  `RUNTIME_CORE_IMPORT_ALLOWLIST`). Verified via `git show 1e034c4:tests/
  architecture/test_api_calls_only_ports.py` that all 3 errors predate
  9-2 wire (Walking Skeleton MVP baseline). **Honestly DEFER** as
  D-9-2-DEFER-6 (Walking Skeleton MVP follow-up A22 candidate).
- **ruff --fix** (during T7): 4 F401 auto-fix + 1 I001 import sort in
  main.py + 2 PT011 broad pytest.raises match arg added.
- **import-linter** verified FINAL CLEAN: `uv run import-linter lint
  --config pyproject.toml` → "Contracts: 2 kept, 0 broken." (cost_engine_forbidden_io
  KEPT + engine_core_to_adapters_forbidden KEPT).
- **pytest focused**: 87 passed (49 kernel + 6 determinism + 5
  no_io_imports + 31 service + 3 architecture ALLOWED drift).
- **vitest**: 42 NEW passed (5 files).
- **tsc** (m9-abc-allocation schema): zero NEW errors (only pre-existing
  errors elsewhere, unrelated to 9-2 wire).

#### T8 — Atomic wire close-out + A29/A30 forward-lock (DONE)

- **A29 forward-lock** (9-3 spec 진입 시점 결정 일정): M3 dispatch ↔ M9
  dispatch dual-route (AD-19 wire) — M9 owns NO public endpoint for 9-2
  wire (service layer wrapper ONLY, AD-21 invariant).
- **A30 forward-lock** (9-4 spec 진입 시점 결정 일정): Report #21 ↔
  Report #15 PDF generator reuse (9-3 done 진입 시점 결정).
- **Epic 9 close-out retro** (cj-style 5번째 진입점) 결정 일정: 9-4 done
  진입 시점에 retro 실행.
- **wire scope**: ~37 files (target met) + cj-style atomic single sprint
  T1~T8 (no partial wire).
- **handoff memory**: `handoff-2026-08-16-9-2-done.md` (full T1~T8
  summary, key decisions, 5 honestly DEFER, A29/A30/Epic 9 retro 일정).

## Honestly DEFER (CR 11-3 17번째 epic 연속)

| ID | Item | 결정 시점 | Rationale | Structural W-class |
|----|------|-----------|-----------|-------------------|
| **D-9-2-DEFER-1** | M3 endpoint dispatch (AD-19 verbatim) | Epic 9 9-3 진입 시점 | A29 forward-lock 결정 후 dual-route 결정 | ✅ |
| **D-9-2-DEFER-2** | Multi-department CCR (PRD §F9.2 "부서별 원가") | Epic 9 9-3 진입 시점 | 9-2 wire = 단일 부서, 9-3 wire = 부서 N개 일괄 compute | ✅ |
| **D-9-2-DEFER-3** | Activity standard hour 자동 추출 (PRD §7.2 "건당 표준시간") | Epic 9 close-out follow-up | 9-2 wire = 활동 시간 직접 입력, 표준시간 자동 추출 honestly DEFER | ✅ |
| **D-9-2-DEFER-4** | Report #21 PDF export (PRD §9 #21 verbatim + A30 forward-lock) | Epic 9 9-4 진입 시점 | A30 결정 후 Report #15 PDF generator reuse | ✅ |
| **D-9-2-DEFER-5** | Playwright E2E (12-5 T6 pattern) | Epic 9 close-out follow-up | A27 follow-up sprint 결정 (cj-style carry-over 9번째) | ✅ |

**제외된 candidates** (Epic boundary 외부 또는 PRD §15 Non-Goal verbatim):
- (a) Cross-region ABC (AD-9 disabled) — Epic 9 9-3 진입 시점에 AD-9 결정 wire
- (b) AI 추천 (Epic 10) — Epic boundary 외부
- (c) Manufacturing ABC (PRD §14.B Non-Goal #1) — Epic 9 close-out follow-up 회색 배지 (D-9-1-DEFER-5 = D-9-2-DEFER-6 동일)

## Status

**Status: done** (2026-08-16, bmad-dev-story T1~T8 atomic wire DONE)

**Final wire summary**:
- A28 forward-lock 3-way wire DONE (CCR ↔ Activity ↔ Cost Object Breakdown)
- baseline_commit = `1e034c4` (Walking Skeleton MVP — 2026-08-16 atomic wire tip)
- 27 NEW + 10 MODIFIED = ~37 files (target met)
- 5 honestly DEFER per CR 11-3 17번째 epic 연속 + 1 pre-existing baseline DEFER (D-9-2-DEFER-6)
- 9-1 wire 보존 (변경 0) + Walking Skeleton MVP wire 보존 (변경 0)
- A29/A30 forward-lock decisions documented (9-3 / 9-4 진입 시점에 결정)
- 3중 게이트 FINAL CLEAN: pytest focused 83 NEW passed + vitest 42 NEW passed + ruff scoped 0 NEW (3 pre-existing N806 honestly DEFER) + import-linter 2 KEPT 0 broken + tsc zero NEW errors for 9-2 files

**Next steps**:
- handoff memory: `handoff-2026-08-16-9-2-done.md` (T1~T8 atomic wire, 5 honestly DEFER, A29/A30 forward-lock 결정 일정)
- 9-3 spec 진입 (cj-style Epic 9 3번째, A29 forward-lock 결정 후)
- 또는 Epic 9 close-out follow-up (cj-style carry-over 9번째, A27 결정)
- 또는 Epic 9 close-out retro (cj-style 5번째 진입점, 9-4 done 진입 후)

---

**supersedes prior** —
- 9-2 backlog reference (lines 607-609 in action_items block)
- A28 (9-1 handoff forward-lock) wire at 9-2 spec 진입 시점
- D-9-1-DEFER-1 (CCR compute) 해소 at 9-2 wire
- D-9-1-DEFER-2 (ABC allocation engine) 해소 at 9-2 wire
- D-9-1-DEFER-4 (Cost Object Breakdown) 해소 at 9-2 wire
- A26 (D-8-3-DEFER-4 forward-lock Option A) 정합 at 9-2 wire (abc_engine.py EXTENSION 동일 surface, NO cross-import)
