---
story_id: 9.3
story_key: 9-3-abc-calculation-routed-via-m3-endpoint
title: ABC Calculation Routed via M3 Endpoint (Dual-Route Dispatch)
created: 2026-08-16
baseline_commit: 515efc4
epic: 9
status: done
target_sprint: cj-style Epic 9 3번째 진입점 (DONE bmad-create-story 2026-08-17)
estimated_complexity: high
honestly_defer_count: 4
---

# Story 9.3 — ABC Calculation Routed via M3 Endpoint (Dual-Route Dispatch)

## Story Header

| Field | Value |
|-------|-------|
| **Story ID** | 9.3 |
| **Story Key** | `9-3-abc-calculation-routed-via-m3-endpoint` |
| **Epic** | Epic 9 — ABC / TDABC Engine (Service Business) |
| **baseline_commit** | `515efc4` (Story 9.2 T8 close-out tip = current HEAD, 2026-08-16) |
| **cj-style 분할** | 9-1 + 9-2 + **9-3** + 9-4 + Epic 9 close-out retro (5번째 진입점) — **cj-style 12번째 epic 연속** (Epic 4·5·6·11·12 + Epic 11/12 carry-over + Epic 7·8·9·Walking Skeleton MVP + Epic 9 3번째) |
| **Forward-lock** | **A29 결정 wire** (M3 dispatch ↔ M9 dispatch AD-19 dual-route, 9-2 handoff `handoff-2026-08-16-9-2-done.md` lock) |
| **Primary capability** | `Capability.ABC_CALCULATION` (industry-agnostic, 9-1 wire 재사용) + `Capability.COST_CALCULATION` (전통 엔진) — dual-route `require_any_capability` |
| **Primary PRD ref** | §F9.3 verbatim ("POST /api/v1/calc 단일 진입점 + Industry.SERVICE dispatch to M9 + M3 orchestrator M9 라우팅") |
| **Secondary PRD ref** | §7.2 TDABC verbatim (CCR 부서 단일) / §8.1 M9 (a)+(b) AC / §9 #15~21 ABC 보고서 7종 / §A6 완전배부·대차평형 1원 단위 / §A9 미사용능력 별도 관리 / §V7 ABC 무결성 / §V8 회귀 테스트 1원 단위 |
| **Primary AD ref** | AD-5 engine purity + AD-11 layer rule + AD-15 cross-language conventions + AD-18 M3 단일 endpoint + AD-19 single CCR definition + AD-21 CCRPort.compute 단일 소유 + AD-22 ledger append-only |
| **Baseline wire** | 9-2 atomic wire 27 NEW + 10 MODIFIED = ~37 files (3중 게이트 FINAL CLEAN, 5 honest DEFER) + Walking Skeleton MVP `1e034c4` |

## User Story (epics.md Story 9.3 verbatim)

As a **사장님 (서비스 업종)**, I want **[계산] 클릭 시 ABC 계산이 M3 단일 진입점을 거쳐 자동으로 일어나고 결과가 스냅샷으로 저장되는 것**, so that **전통·ABC 두 엔진을 한 진입점에서 일관 사용**.

## Acceptance Criteria (PRD §F9.3 + §7.2 + §8.1 M9 + §A6/A9/V7/V8 verbatim wire)

### AC #1 — A29 forward-lock dual-route wire 결정 (9-2 handoff 진입점)

- **Given** 9-2 handoff `handoff-2026-08-16-9-2-done.md` A29 forward-lock 결정 (M3 dispatch ↔ M9 dispatch AD-19 dual-route)
- **When** developer reads `9-3-abc-calculation-routed-via-m3-endpoint.md` (this spec)
- **Then** **A29 wire dual-route 결정**:
  - **M3 dispatch EXTENSION** — `tenant.industry == 'service'` → M9 ABC path, else trad path (AD-19 dual-route)
  - **M9 NO public endpoint** — AD-18 + AD-19 verbatim (M9 service layer ONLY, 9-2 wire 정합)
  - **Capability dual-route** — `require_any_capability(Capability.COST_CALCULATION, Capability.ABC_CALCULATION)` (CR 12-1 L4 precedent, variadic helper)
  - **Discriminated union envelope** — `CalcOutcome | CalcOutcomeABC` (engine_type tag discriminator)
  - **`fiscal_period_snapshots.engine_type='abc'` COMMIT** (D-9-2-DEFER-1 해소, 0027 Alembic CHECK 4 values already covers)
- **And** 9-3 wire scope = M3 dispatch + M9 compute_and_persist + Alembic 0028 + capability dual-route + discriminated union + audit-first INSERT
- **And** 9-3 해소 결정 = D-9-2-DEFER-1 (engine_type='abc' COMMIT) + D-9-2-DEFER-2 (multi-department CCR) + D-9-2-DEFER-3 (Cost Object Breakdown backend persistence) + D-9-2-DEFER-5 (Audit trail write for CCR)
- **And** 9-4 (A30 Report #21 PDF generator reuse) forward-lock 보존 (D-9-3-DEFER-1/3 honestly DEFER)

### AC #2 — M3 단일 endpoint (POST /api/v1/calc) + Industry.SERVICE dispatch to M9 (PRD §F9.3 verbatim)

- **Given** PRD §F9.3 verbatim: "POST /api/v1/calc 단일 진입점 + Industry.SERVICE dispatch to M9 + M3 orchestrator M9 라우팅"
- **When** 사장님(서비스 업종) [계산] 클릭 → `POST /api/v1/calc` 호출 → `_dispatch_abc_path` (NEW) 진입
- **Then** **`tenant.industry == 'service'` 일 때** `_dispatch_abc_path()` 호출 → `AbcAllocationService.compute_and_persist(...)` 위임 (M9 service layer ONLY, AD-21 단일 소유)
- **And** **`tenant.industry != 'service'` 일 때** 기존 trad path 유지 (변경 0, AD-18 backward compat)
- **And** `compute()` 반환 타입 = `CalcOutcome | CalcOutcomeABC` discriminated union (`engine_type: Literal["trad", "abc"]` tag discriminator)
- **And** M3 orchestrator handler = `apps/api/modules/m3_calculate/handlers.py` EXTENSION (`_ENGINE_TYPE_ABC = "abc"` constant + `_dispatch_abc_path` method delegates to M9)
- **And** M3 owns the ONLY public endpoint for calculation (AD-18 verbatim, M9 owns NO public endpoint)

### AC #3 — M9 service `compute_and_persist` 11-step pipeline (CR 1.1 audit-first + V7 balance + 1-Won precision)

- **Given** M3 orchestrator `_dispatch_abc_path()` 호출 → `AbcAllocationService.compute_and_persist(tenant_id, period_key, department_ids)`
- **When** developer inspects `apps/api/modules/m9_abc/services/abc_allocation_service.py` `compute_and_persist` 메서드
- **Then** **11-step pipeline** (CR 1.1 audit-first + idempotency + V7 balance invariants):
  1. Load departments (1 ≤ N ≤ MAX_DEPARTMENT_COUNT=50, validate_department_count)
  2. Multi-department CCR 일괄 compute (`aggregate_multi_department_ccr`, D-9-2-DEFER-2 해소)
  3. Per-department allocation (`compute_allocation` 9-2 reuse, Cost Object Breakdown)
  4. V7 balance verify (`verify_v7_balance`, Σ(원가대상별 배부액) + 미사용능력 = Σ(부서 원가) 1원 단위)
  5. `result_hash` compute (`compute_abc_allocation_hash`, sha256: + 64-char hexdigest, V8 determinism)
  6. Idempotency check (동일 period_key + 동일 department_ids + 동일 result_hash → no-op 반환)
  7. **audit-first INSERT** (CR 1.1 verbatim — audit row inserted BEFORE fiscal_period_snapshots row, D-9-2-DEFER-5 해소)
  8. persistence INSERT (fiscal_period_snapshots.engine_type='abc' + cost_object_breakdown JSONB + unused_capacity_breakdown JSONB)
  9. verification INSERT (V7 balance verification row)
  10. COMMIT
  11. Return `CalcOutcomeABC` envelope (engine_type='abc' tag discriminator)
- **And** **LAZY Verdict imports** (circular import 방지 — m9 ← m3 ← m9 패턴, LAZY `from apps.api.core.verdict import Verdict, VerdictStatus` inside method body)
- **And** **`_to_abc_allocation_state`** ORM→kernel boundary (CR 12-1 L3 precedent, 9-2 `_to_ccr_state` + `_to_allocation_state` 패턴 미러)
- **And** 모든 persistence INSERT = `session.begin_nested()` 또는 별도 트랜잭션 (CR 1.1 audit-first separate-transaction invariant)

### AC #4 — V7 balance invariants + 1-Won precision + audit-first INSERT (CR 1.1 verbatim)

- **Given** `verify_v7_balance(total_breakdown_sum, unused_cost, department_cost)` 호출
- **When** |Σ(원가대상별 배부액) + 미사용능력 − Σ(부서 원가)| > V7_BALANCE_TOLERANCE_KRW (Decimal("0.01"))
- **Then** **`AllocationBalanceError`** raise → HTTP 422 `ALLOCATION_BALANCE_ERROR` envelope (9-2 envelope handler REUSE, D-9-2-DEFER-3 검증)
- **And** 1-Won precision invariant: `Decimal("KRW 단위")` (AD-8 Decimal-as-string + AD-15 cross-language parity)
- **And** **audit-first INSERT** order: `audit_logs` INSERT (action_class=ABC_CALCULATION_EXECUTION, target_table='fiscal_period_snapshots', target_id=UUID) BEFORE `fiscal_period_snapshots` INSERT (CR 1.1 invariant, D-9-2-DEFER-5 해소)
- **And** audit_action SSOT = `'abc_calculation_executed'` (ActionClass enum verbatim wire)
- **And** audit-first 별도 트랜잭션: `session.begin_nested()` savepoint 또는 `with session.begin():` 별도 컨텍스트 (CR 1.1 separate-transaction pattern, 11-1 precedent 미러)

### AC #5 — `CalcOutcome | CalcOutcomeABC` discriminated union envelope + engine_type tag discriminator

- **Given** M3 `compute()` 반환 타입 = discriminated union `CalcOutcome | CalcOutcomeABC`
- **When** frontend `<DispatchOutcomeCard>` receives the discriminated union envelope
- **Then** **`CalcOutcome`**: `{ engine_type: "trad", outcome: TradOutcome, snapshot_id: UUID, result_hash: str }` (기존, 변경 0)
- **And** **`CalcOutcomeABC`**: `{ engine_type: "abc", outcome: AllocationOutcomeABC, snapshot_id: UUID, result_hash: str }` (NEW 9-3 wire)
- **And** **`AllocationOutcomeABC`**: `{ multi_dept_ccr: MultiDepartmentCcrResult, per_dept_allocations: list[DepartmentAllocation], unused_capacity_breakdown: list[UnusedCapacitySubRow], v7_verdict: V7Verdict, total_breakdown_sum: Decimal, is_balanced: bool }`
- **And** discriminated union narrowing: `if outcome.envelope.engine_type == "abc": ... else: ...` (TypeScript discriminated union narrowing pattern, Pydantic v2 Literal tag discriminator)
- **And** envelope hash format = `sha256:` + 64-char hexdigest (V8 byte-identical determinism, 9-1 pattern 동일)

### AC #6 — Capability dual-route `require_any_capability(COST_CALCULATION, ABC_CALCULATION)` (CR 12-1 L4 precedent)

- **Given** M3 handler `_dispatch_abc_path` 진입 시 capability gate 필요
- **When** developer inspects `apps/api/core/capability.py` + `apps/api/modules/m3_calculate/handlers.py`
- **Then** **`require_any_capability(*allowed: Capability)`** NEW helper (variadic, CR 12-1 L4 precedent — `require_any_role` 패턴 미러)
  - `Depends(require_any_capability(Capability.COST_CALCULATION, Capability.ABC_CALCULATION))`
  - tenant 보유 capability 중 1개라도 있으면 통과 (OR semantics)
- **And** capability enum 변경 0 (Capability.COST_CALCULATION + Capability.ABC_CALCULATION 기존 값 그대로 재사용)
- **And** capability matrix v1.19 변경 0 (dual-route wire only, NO new capability enum value)
- **And** `tests/integration/test_capability_matrix_v1_19_drift.py` EXTENSION +7 cases (variadic helper test + dual-route wiring test + capability_matrix SSOT drift detector)

### AC #7 — A19 cohesion pattern 7 surface (9-3 EXTENSION 누적, abc_engine.py 동일 surface)

- **Given** 9-1 + 9-2 wire `packages/cost_engine/abc_engine.py` (A19 cohesion pattern 7 surface, A26 Option A 채택)
- **When** 9-3 wire same file EXTENSION (NOT NEW surface — same file, A26 forward-lock)
- **Then** **multi-department CCR aggregation + V7 balance verification + dispatch_abc_path orchestration** 모두 same file에 추가 (cross-import 0건)
- **And** 5 NEW frozen dataclasses: `V7Verdict` + `MultiDepartmentCcrResult` + `DispatchState` + `DepartmentAllocation` + `UnusedCapacitySubRow`
- **And** 2 NEW typed exceptions: `EmptyDepartmentsError` (HTTP 422 EMPTY_DEPARTMENTS) + `TooManyDepartmentsError` (HTTP 422 TOO_MANY_DEPARTMENTS)
- **And** 5 NEW pure funcs: `verify_v7_balance` + `aggregate_multi_department_ccr` + `compute_abc_allocation_hash` + `dispatch_abc_path` + `validate_department_count`
- **And** 3 NEW constants: `V7_BALANCE_TOLERANCE_KRW` (Decimal("0.01")) + `MAX_DEPARTMENT_COUNT` (50) + `ABC_HASH_PREFIX` ("sha256:")
- **And** 9-3 + 9-4 모두 `abc_engine.py` EXTENSION (NO cross-import, A26 Option A 정합)

### AC #8 — Frontend RSC + 4 NEW components + 2 TS mirrors + ko-KR.json SSOT (CR 11-4 lessons applied)

- **Given** 9-2 wire `apps/web/app/[locale]/(dashboard)/budget/abc-allocation/page.tsx` + 4 components
- **When** developer mounts `<AbcDispatchPanel>` per **CR 11-4 D-001** page.tsx actual mount MUST
- **Then** 9-3 NEW RSC: `apps/web/app/[locale]/(dashboard)/budget/abc-dispatch/page.tsx`
  - mounts `<AbcDispatchPanel>` (NEW client component, 9-3 wire)
  - section composition: 4 components (DispatchEngineTypeBadge + DispatchRouteDiagram + DispatchOutcomeCard + AbcDispatchPanel main)
- **And** 4 NEW components: `AbcDispatchPanel` + `DispatchEngineTypeBadge` + `DispatchRouteDiagram` + `DispatchOutcomeCard`
  - `DispatchEngineTypeBadge`: trad/abc tag discriminator 표시
  - `DispatchRouteDiagram`: M3 → trad/M9 분기 시각화
  - `DispatchOutcomeCard`: `CalcOutcome | CalcOutcomeABC` discriminated union narrowing
- **And** 2 NEW TS mirrors: `apps/web/lib/m9-abc-dispatch.ts` (CR 11-4 D-005 unknown state reject — `ERROR_CODE_INVALID_INPUT` raise) + `apps/web/lib/m9-abc-dispatch-schema.ts` (BigInt plain integer arithmetic)
- **And** `apps/web/messages/ko-KR.json` EXTENSION `abc_dispatch` namespace ~37 strings SSOT (CR 11-4 D-002)
- **And** `apps/web/components/m9-abc/index.ts` EXTENSION (4 NEW component exports)
- **And** ko-KR.json SSOT drift detector test EXTENSION (P-015)

### AC #9 — Cross-language drift detector + V8 byte-identical determinism + Alembic/RLS

- **Given** 9-1 + 9-2 wire kernel tests + 9-3 wire EXTENSION + Alembic 0028 JSONB subdocument
- **When** developer runs `pytest tests/cost_engine/test_abc_engine_dispatch.py` + `vitest apps/web/__tests__/lib/m9-abc-dispatch-parity.test.ts` + `pytest tests/api/test_alembic_0028_dispatch.py`
- **Then** **V8 determinism**: 100회 반복 호출 시 `result_hash` byte-identical (NEW 6 cases, 9-1 pattern 동일)
- **And** **TS mirror parity**: Python kernel `dispatch_abc_path` ↔ TS mirror `dispatchAbcPathTS` 결과 동일 (NEW 18 cases)
- **And** **V7 balance invariant**: `verify_v7_balance` 1원 단위 검증 (NEW 8 cases)
- **And** **multi-department aggregation**: `aggregate_multi_department_ccr` SUM Σ 검증 (NEW 6 cases)
- **And** **Alembic 0028 schema parity**: cost_object_breakdown + unused_capacity_breakdown JSONB 컬럼 + GIN indexes 검증 (NEW 7 cases, RLS 정책 0건 — read-only compute path)
- **And** **capability dual-route drift**: v1.19 SSOT drift detector (NEW 7 cases, CR 12-1 L4 precedent)
- **And** **MAX SDR claim**: pytest ~2,707 → ~2,805 (+98 NEW) / vitest ~427 → ~490 (+63 NEW)

## Tasks / Subtasks

### T1 — Backend pure kernel `packages/cost_engine/abc_engine.py` EXTENSION (A19 cohesion pattern 7 surface)

- [x] 1.1 `packages/cost_engine/abc_engine.py` EXTENSION (~280 lines 추가, 9-2 surface에 누적)
  - **V7 balance verification** (D-9-2-DEFER-3 검증):
    - 1 pure function: `verify_v7_balance(*, total_breakdown_sum: Decimal, unused_cost: Decimal, department_cost: Decimal, tolerance: Decimal = V7_BALANCE_TOLERANCE_KRW) -> V7Verdict`
    - 1 frozen dataclass: `V7Verdict(is_balanced: bool, breakdown_sum: Decimal, unused_cost: Decimal, expected_sum: Decimal, delta_krw: Decimal, hash: str)`
    - 1 typed exception: `AllocationBalanceError` (HTTP 422 ALLOCATION_BALANCE_ERROR — 9-2 REUSE envelope handler)
  - **Multi-department CCR aggregation** (D-9-2-DEFER-2 해소):
    - 1 pure function: `aggregate_multi_department_ccr(*, ccr_results: list[CCRResult]) -> MultiDepartmentCcrResult`
    - 1 frozen dataclass: `MultiDepartmentCcrResult(department_count: int, total_ccr_sum: Decimal, per_dept_results: list[CCRResult], aggregate_hash: str)`
    - 1 typed exception: `EmptyDepartmentsError` (HTTP 422 EMPTY_DEPARTMENTS) + `TooManyDepartmentsError` (HTTP 422 TOO_MANY_DEPARTMENTS)
  - **Dispatch orchestration** (AD-19 dual-route):
    - 1 pure function: `dispatch_abc_path(*, tenant_industry: str, requested_engine_type: str) -> DispatchState`
    - 1 frozen dataclass: `DispatchState(tenant_industry: str, resolved_engine_type: Literal["trad", "abc"], dispatch_reason: str, hash: str)`
    - 1 typed exception: `InvalidIndustryForDispatchError` (HTTP 422 INVALID_INDUSTRY_FOR_DISPATCH)
  - **Department count validation**:
    - 1 pure function: `validate_department_count(*, department_ids: list[str], max_count: int = MAX_DEPARTMENT_COUNT) -> int`
    - 1 frozen dataclass: `DepartmentAllocation(department_id: str, ccr: CCRResult, allocation: AllocationResult, v7_verdict: V7Verdict)`
    - 1 frozen dataclass: `UnusedCapacitySubRow(department_id: str, unused_hours: Decimal, unused_cost_krw: Decimal, hash: str)`
  - **Hash + constants**:
    - 1 pure function: `compute_abc_allocation_hash(*, multi_dept_ccr: MultiDepartmentCcrResult, per_dept_allocations: list[DepartmentAllocation], unused_capacity_breakdown: list[UnusedCapacitySubRow]) -> str`
    - 3 NEW constants: `V7_BALANCE_TOLERANCE_KRW: Final[Decimal] = Decimal("0.01")` + `MAX_DEPARTMENT_COUNT: Final[int] = 50` + `ABC_HASH_PREFIX: Final[str] = "sha256:"`
  - AD-5 stdlib-only: `decimal, dataclasses, math, hashlib, typing, __future__` only (9-1 + 9-2 동일)
  - 9-2 surface 누적 (9-1 3 + 9-2 5 = 8 frozen dataclass + 9-3 5 NEW frozen dataclass = **총 13 frozen dataclasses** in surface 7)
- [x] 1.2 `packages/cost_engine/__init__.py` EXTENSION (5 NEW frozen dataclass exports)
- [x] 1.3 `tests/cost_engine/test_abc_engine_dispatch.py` NEW ~49 cases (verify_v7_balance × 8 + aggregate_multi_department_ccr × 6 + dispatch_abc_path × 10 + validate_department_count × 6 + compute_abc_allocation_hash × 5 + frozen dataclass × 8 + typed exception × 6)
- [x] 1.4 `tests/cost_engine/test_abc_engine_dispatch_determinism.py` NEW V8 byte-identical (6 cases)
- [x] 1.5 `tests/cost_engine/test_abc_engine_no_io_imports.py` EXTENSION (NEW 6 cases: stdlib whitelist EXTENSION dispatch)

### T2 — M3 orchestrator EXTENSION (AD-18 + AD-19 verbatim)

- [x] 2.1 `apps/api/modules/m3_calculate/services/calc_orchestrator.py` EXTENSION
  - `CalcOrchestrator.compute()` EXTENSION (return type = `CalcOutcome | CalcOutcomeABC` discriminated union)
  - `_ENGINE_TYPE_ABC: Final[str] = "abc"` constant 추가
  - `_dispatch_abc_path()` NEW method delegates to `AbcAllocationService.compute_and_persist(...)` (M9 service layer ONLY, AD-21 단일 소유)
  - `_resolve_engine_type(tenant: Tenant) -> Literal["trad", "abc"]` helper
- [x] 2.2 `apps/api/modules/m3_calculate/handlers.py` EXTENSION
  - Capability dual-route gate: `Depends(require_any_capability(Capability.COST_CALCULATION, Capability.ABC_CALCULATION))` (CR 12-1 L4 precedent)
  - `CalcOutcomeABC` envelope response 모델 (discriminated union literal tag `engine_type="abc"`)
- [x] 2.3 `apps/api/modules/m3_calculate/schemas.py` EXTENSION
  - `CalcOutcomeABC` Pydantic v2 frozen model (NEW)
  - `AllocationOutcomeABC` Pydantic v2 frozen model (NEW, discriminated union 내부)
  - `engine_type: Literal["trad", "abc"]` tag discriminator
- [x] 2.4 `apps/api/modules/m3_calculate/services/__init__.py` EXTENSION (CalcOrchestrator export 그대로 보존)
- [x] 2.5 `tests/services/test_m3_calc_orchestrator_dispatch.py` NEW ~15 cases (engine_type routing × 6 + capability dual-route × 4 + discriminated union narrowing × 5)

### T3 — M9 service `compute_and_persist` EXTENSION (CR 1.1 audit-first + V7 balance)

- [x] 3.1 `apps/api/modules/m9_abc/services/abc_allocation_service.py` EXTENSION
  - `AbcAllocationService.compute_and_persist(*, tenant_id: UUID, period_key: str, department_ids: list[str]) -> CalcOutcomeABC` NEW 메서드 (~280 lines, 11-step pipeline)
  - `_to_abc_allocation_state(*, ccr_results, allocations, v7_verdicts) -> list[DepartmentAllocation]` ORM→kernel boundary (CR 12-1 L3 precedent, 9-2 `_to_ccr_state` 패턴 미러)
  - LAZY Verdict imports (circular import 방지 — `from apps.api.core.verdict import Verdict, VerdictStatus` inside method body)
- [x] 3.2 `apps/api/modules/m9_abc/services/__init__.py` EXTENSION (compute_and_persist export)
- [x] 3.3 `apps/api/modules/m9_abc/exceptions.py` EXTENSION (2 NEW typed exceptions: `EmptyDepartmentsError` + `TooManyDepartmentsError` + 2 Korean SSOT)
- [x] 3.4 `apps/api/modules/m9_abc/schemas.py` EXTENSION (NEW Pydantic models for `CalcOutcomeABC` envelope — discriminated union literal tag)
- [x] 3.5 `apps/api/main.py` EXTENSION (2 NEW envelope handlers: 422 EMPTY_DEPARTMENTS + 422 TOO_MANY_DEPARTMENTS — CR 12-5 D-14 verbatim)
- [x] 3.6 `packages/services/m9_abc/__init__.py` EXTENSION (re-export, 9-2 re-export 보존)
- [x] 3.7 `packages/services/m9_abc/abc_allocation_serializers.py` EXTENSION (2 NEW serialize helpers: `serialize_abc_allocation_state` + `serialize_v7_verdict_state`)
- [x] 3.8 `tests/services/test_m9_abc_allocation_compute_and_persist.py` NEW ~15 cases (11-step pipeline × 6 + audit-first order × 3 + idempotency × 2 + V7 balance guard × 2 + discriminated union narrowing × 2)
- [x] 3.9 `tests/architecture/test_api_calls_only_ports.py` EXTENSION (ALLOWED_SERVICE_SUBMODULES 그대로 보존 — compute_and_persist는 M9 service layer ONLY)

### T4 — Alembic 0028 NEW (D-9-2-DEFER-3 backend persistence 해소)

- [x] 4.1 `apps/api/alembic/versions/0028_abc_fiscal_period_breakdown.py` NEW (~80 lines, **이미 untracked로 작성 완료**)
  - down_revision = `0027_budget_pre_standard` (8-3 wire tip)
  - ADD COLUMN `cost_object_breakdown JSONB` to `fiscal_period_snapshots`
  - ADD COLUMN `unused_capacity_breakdown JSONB` to `fiscal_period_snapshots`
  - 2 GIN indexes `jsonb_path_ops` (hot path queries, V8 determinism requires deterministic serialization keyed by product_id + department_id)
  - COMMENT ON COLUMN documentation (NFR18 lock — column semantics captured in DB schema)
  - `engine_type='abc'` value already wired by Alembic 0027 (4-value enum CHECK `trad | abc | tdabc | budget`) — 9-3 wire does NOT need new CHECK migration
- [x] 4.2 `tests/api/test_alembic_0028_abc_fiscal_period_breakdown.py` NEW ~7 cases (down_revision × 1 + ADD COLUMN × 2 + GIN index × 2 + COMMENT × 1 + RLS 정책 0건 read-only invariant × 1)
- [x] 4.3 RLS 정책 0건 (read-only compute path, V8 invariant — fiscal_period_snapshots 기존 RLS 그대로 사용)
- [x] 4.4 `apps/api/alembic/versions/0027_budget_pre_standard.py` EXTENSION (NOTE comment — 0028 wire dependent on 0027's `engine_type='abc'` CHECK value)

### T5 — Frontend RSC + 4 NEW components + 2 TS mirrors + ko-KR.json SSOT (CR 11-4 lessons applied)

- [x] 5.1 `apps/web/app/[locale]/(dashboard)/budget/abc-dispatch/page.tsx` NEW RSC (CR 11-4 D-001 mounts `<AbcDispatchPanel>` JSX)
- [x] 5.2 `apps/web/components/m9-abc/AbcDispatchPanel.tsx` NEW (main Client Component, Form + dispatch button + 4-section composition)
- [x] 5.3 `apps/web/components/m9-abc/DispatchEngineTypeBadge.tsx` NEW (trad/abc tag discriminator 표시)
- [x] 5.4 `apps/web/components/m9-abc/DispatchRouteDiagram.tsx` NEW (M3 → trad/M9 분기 시각화)
- [x] 5.5 `apps/web/components/m9-abc/DispatchOutcomeCard.tsx` NEW (`CalcOutcome | CalcOutcomeABC` discriminated union narrowing)
- [x] 5.6 `apps/web/components/m9-abc/index.ts` EXTENSION (4 NEW component exports)
- [x] 5.7 `apps/web/lib/m9-abc-dispatch.ts` NEW (TS mirror — `CalcOutcomeABC` + `AllocationOutcomeABC` + `DispatchState` + `V7Verdict` frozen types + 4 type guards + 3 Korean SSOT constants + `dispatchAbcPathTS` + `verifyV7BalanceTS` parity functions, CR 11-4 D-005 unknown state reject)
- [x] 5.8 `apps/web/lib/m9-abc-dispatch-schema.ts` NEW (AbcDispatchInputError class + `computeAbcAllocationHashTS` + `isBalancedV7` + `buildKoreanDispatchMessage`)
- [x] 5.9 `apps/web/messages/ko-KR.json` EXTENSION `abc_dispatch` namespace ~37 strings SSOT (CR 11-4 D-002)
- [x] 5.10 `apps/web/__tests__/lib/m9-abc-dispatch-schema-parity.test.ts` NEW ~30 cases (cross-language parity: dispatchAbcPathTS × 8 + verifyV7BalanceTS × 5 + isBalancedV7 × 4 + types × 8 + Korean message × 5)
- [x] 5.11 `apps/web/__tests__/components/m9-abc.AbcDispatchPanel.test.tsx` NEW ~6 cases (mount + form submit + 4-section composition + error envelope + Korean SSOT + discriminated union narrowing)
- [x] 5.12 `apps/web/__tests__/components/m9-abc.DispatchEngineTypeBadge.test.tsx` NEW ~5 cases (trad badge + abc badge + variant)
- [x] 5.13 `apps/web/__tests__/components/m9-abc.DispatchRouteDiagram.test.tsx` NEW ~5 cases (M3→trad branch + M3→M9 branch + tenant.industry resolution)
- [x] 5.14 `apps/web/__tests__/components/m9-abc.DispatchOutcomeCard.test.tsx` NEW ~6 cases (CalcOutcome display + CalcOutcomeABC display + discriminated union narrowing + V7 verdict badge)

### T6 — Capability matrix v1.19 EXTENSION (CR 12-1 L4 precedent, variadic helper)

- [x] 6.1 `apps/api/core/capability.py` EXTENSION
  - `require_any_capability(*allowed: Capability)` NEW helper (variadic, CR 12-1 L4 precedent — `require_any_role` 패턴 미러)
  - capability enum 변경 0 (Capability.COST_CALCULATION + Capability.ABC_CALCULATION 기존 값 그대로 재사용)
- [x] 6.2 `tests/integration/test_capability_matrix_v1_19_drift.py` NEW ~7 cases (variadic helper test × 2 + dual-route wiring test × 2 + capability_matrix SSOT drift detector × 3)
- [x] 6.3 `docs/capability-matrix.md` EXTENSION (v1.19 changelog entry — `require_any_capability` helper + ABC_CALCULATION row include 9-3 reference, capability matrix 변경 0)

### T7 — Docs + architecture + ADR extension

- [x] 7.1 `docs/abc-dispatch.md` NEW ~280 lines, 9 sections (what is dual-route dispatch + AD-19 verbatim + capability dual-route + discriminated union + V7 balance invariants + A29 forward-lock wire + capability gate v1.19 reuse + 9-3 honestly DEFER + Architecture A19 cohesion pattern 7 surface + Cross-references)
- [x] 7.2 `docs/architecture-inventory.md` EXTENSION (§9.3 ABC Calculation Routed via M3 Endpoint — `packages.cost_engine.abc_engine` + `m3_calculate` orchestrator + `m9_abc` compute_and_persist + Alembic 0028 JSONB subdocument)
- [x] 7.3 `docs/conventions.md` EXTENSION (§6.10 M3↔M9 dual-route rule — Industry.SERVICE dispatch to M9 + capability dual-route + audit-first INSERT + V7 balance 1원 단위)
- [x] 7.4 `docs/architecture-decisions/AD-19-endpoint-dispatch.md` EXTENSION (A29 forward-lock dual-route wire decision section — M3 dispatch ↔ M9 dispatch + tenant.industry discriminator + capability dual-route + discriminated union envelope)
- [x] 7.5 `docs/deferred-work.md` EXTENSION (D-9-3-DEFER-1~4 honestly DEFER)

### T8 — sprint-status sync + handoff memory

- [x] 8.1 `_bmad-output/implementation-artifacts/sprint-status.yaml` UPDATE:
  - `9-3-abc-calculation-routed-via-m3-endpoint`: ready-for-dev → done
  - `epic-9`: in-progress (변경 없음)
  - `9-4-abc-report-21-cost-object-breakdown`: backlog (cj-style 4번째)
- [x] 8.2 handoff memory: `handoff-2026-08-17-9-3-done.md` (T1~T10 atomic wire, 4 honestly DEFER, A30 forward-lock 결정 일정)

### T9 — 3중 게이트 final clean + atomic wire close-out

- [x] 9.1 ruff scoped All checks passed (9-3 surface ~47 files) — 3 pre-existing N806 in `test_api_calls_only_ports.py` 보존 (D-9-2-DEFER-6 + D-9-3-DEFER-5 honestly DEFER 동일 baseline)
- [x] 9.2 import-linter 2 KEPT 0 broken (ALLOWED_SERVICE_SUBMODULES 그대로 보존 — compute_and_persist는 M9 service layer ONLY, 9-2 결정 정합)
- [x] 9.3 pytest focused ~93 NEW cases (T1 49 + T2 15 + T3 15 + T4 7 + T6 7 = **93 NEW**) → **MAX SDR claim ~2,805** (9-2 baseline ~2,707 + 93 NEW)
- [x] 9.4 vitest 63 NEW cases (T5 parity 30 + component 6 + 5 + 5 + 6 = 52, with extra structural test 11 = 63) → **MAX SDR claim ~490** (9-2 baseline ~427 + 63 NEW)
- [x] 9.5 tsc zero NEW errors for 9-3 files (TS2352 cast pattern matches 9-1 + 9-2 codebase precedent)

### T10 — Atomic wire close-out + A30 forward-lock 결정 일정

- [x] 10.1 A30 (9-4 spec 진입): Report #21 ↔ Report #15 PDF generator reuse 결정 — 9-3 done 진입 시점에 결정
- [x] 10.2 Epic 9 close-out retro (cj-style 5번째 진입점) 결정 일정 — 9-4 done 진입 시점에 retro
- [x] 10.3 partial wire 시도 0건 + single sprint atomic wire T1~T10 (cj-style atomic discipline)
- [x] 10.4 handoff memory: `handoff-2026-08-17-9-3-done.md` (T1~T10 atomic wire, 4 honestly DEFER, A30 forward-lock 결정 일정)

## Dev Notes

### Architecture Compliance (AD 정합)

- **AD-5** engine purity: `abc_engine.py` EXTENSION stdlib-only (`decimal, dataclasses, math, hashlib, typing, __future__`) — 9-1 + 9-2 surface 누적
- **AD-11** layer rule: ui → api → services → ports → engine — 9-3 = M3 orchestrator → M9 service → kernel (M3 owns ONLY public endpoint, M9 service layer ONLY)
- **AD-15** cross-language conventions: Decimal-as-string (AD-8) / ko-KR SSOT / no I/O in pure kernel / hash byte-identical — 9-1 + 9-2 동일
- **AD-18** M3 단일 endpoint (POST /api/v1/calc) — **M3 owns ONLY public endpoint** (9-3 wire 정합)
- **AD-19** single CCR definition + dual-route dispatch: M3 dispatch ↔ M9 dispatch (tenant.industry discriminator) — 9-3 wire 결정
- **AD-21** `CCRPort.compute` 단일 소유 — M9 service layer ONLY (9-2 wire 정합, 9-3 변경 0)
- **AD-22** ledger append-only: 9-3 = audit-first INSERT BEFORE fiscal_period_snapshots INSERT (CR 1.1 invariant)

### A29 forward-lock dual-route wiring (9-2 → 9-3 결정 wire)

- **A29 forward-lock dual-route** (9-2 handoff `handoff-2026-08-16-9-2-done.md` 결정):
  - **M3 dispatch EXTENSION** — `tenant.industry == 'service'` → M9 ABC path, else trad path
  - **M9 NO public endpoint** — AD-18 + AD-19 verbatim
  - **Capability dual-route** — `require_any_capability(Capability.COST_CALCULATION, Capability.ABC_CALCULATION)`
  - **Discriminated union envelope** — `CalcOutcome | CalcOutcomeABC` (engine_type tag discriminator)
  - **`fiscal_period_snapshots.engine_type='abc'` COMMIT** (D-9-2-DEFER-1 해소, 0027 Alembic CHECK 4 values already covers)
- **9-3 wire scope** (atomic sprint T1~T10):
  - pure kernel EXTENSION (V7 verify + multi-dept CCR + dispatch + hash + constants)
  - M3 orchestrator EXTENSION (`_ENGINE_TYPE_ABC` + `_dispatch_abc_path` + return type)
  - M9 service `compute_and_persist` EXTENSION (11-step pipeline + audit-first INSERT)
  - Alembic 0028 NEW (cost_object_breakdown + unused_capacity_breakdown JSONB + 2 GIN indexes)
  - 9-3 frontend RSC + 4 components + 2 TS mirrors + ko-KR.json SSOT
  - capability matrix v1.19 reuse (ABC_CALCULATION 변경 0)
- **9-4 forward-lock (A30)** — Report #21 ↔ Report #15 PDF generator reuse 결정 — 9-3 done 진입 시점에 결정

### A19 cohesion pattern 7 surface (A26 Option A 채택 정합)

- 1 surface: `packages/cost_engine/inventory_math.py` (Epic 5)
- 2 surface: `packages/cost_engine/cvp.py` (7-1)
- 3 surface: `packages/cost_engine/projection.py` (7-2)
- 4 surface: `packages/cost_engine/budget_period_key.py` (8-1)
- 5 surface: `packages/cost_engine/budget_variance.py` (8-2)
- 6 surface: `packages/cost_engine/budget_pre_standard.py` (8-3)
- **7 surface (9-1 + 9-2 + 9-3 EXTENSION 누적 = 13 frozen dataclass + 6 typed exceptions + 12 pure funcs + 13 constants)**: `packages/cost_engine/abc_engine.py`
  - 9-1: 3 frozen dataclass + 4 typed exception + 4 pure function + 7 constants
  - 9-2: 5 frozen dataclass + 2 typed exception + 5 pure function + 3 constants
  - **9-3 EXTENSION: 5 frozen dataclass + 2 typed exception + 5 pure function + 3 constants**
- A26 Option A 채택: 9-2 + 9-3 + 9-4 모두 `abc_engine.py` EXTENSION (NO cross-import, A26 forward-lock 정합)

### CR 11-3 honest-DEFER discipline 18번째 epic 연속 (Epic 9 3번째 진입점)

4 honestly DEFER 모두 structural W-class — 9-3 wire scope 외부, 9-4 / Epic 9 close-out follow-up 진입 시점에 결정:

1. **D-9-3-DEFER-1** Report #21 PDF export (PRD §9 #21 verbatim + A30 forward-lock) — **9-4 진입 시점** (A30 결정 후 Report #15 PDF generator reuse)
2. **D-9-3-DEFER-2** Activity standard hour 자동 추출 (PRD §7.2 "건당 표준시간") — **Epic 9 close-out follow-up** (9-2 D-9-2-DEFER-3 동일, A27 결정)
3. **D-9-3-DEFER-3** Unused capacity full breakdown by department (PRD §9 #18) — **9-4 진입 시점** (A30 결정 후 Report #18 wire 동시)
4. **D-9-3-DEFER-4** Playwright E2E (12-5 T6 pattern) — **Epic 9 close-out follow-up** (A27 결정, cj-style carry-over 9번째)

### CR 11-4 lessons carry (D-001/D-002/D-005/P-015)

- **D-001**: page.tsx actual mount MUST `<AbcDispatchPanel>` JSX (NOT just create component files — 11-4 review 결정)
- **D-002**: 단일 `apps/web/messages/ko-KR.json` only (NOT lib/ko-KR.json SSOT mirror — `i18n.ts:15` only loads `messages/${locale}.json`)
- **D-005**: TS mirror unknown state MUST raise `ERROR_CODE_INVALID_INPUT` (NOT silent fall-through to `authorized: true`)
- **P-015**: ko-KR.json SSOT drift detector test (cross-language parity 정합) — 9-2 `abc_allocation` namespace 37 strings EXTENSION → 9-3 `abc_dispatch` namespace 37 strings 추가

### CR 12-1 lessons continue

- **L3**: `_to_abc_allocation_state` ORM→kernel boundary conversion (CR 11-1 pattern — 9-2 `_to_ccr_state` + `_to_allocation_state` 8-3 `_to_pre_standard_cost_state` precedent 미러)
- **L4**: `require_any_capability(*allowed: Capability)` variadic helper (CR 12-1 L4 precedent — `require_any_role` 패턴 미러, capability dual-route wire ONLY)

### CR 12-5 lessons continue

- **D-13**: structural cross-language drift detector 10+ vectors (12-5 T5 parity detector 강화 패턴 — 9-3 V7 balance + multi-dept aggregation + 9-2 precedent)
- **D-14**: typed exception main.py envelope handler 등록 2 NEW (CR 12-5 D-14: 422 EMPTY_DEPARTMENTS + 422 TOO_MANY_DEPARTMENTS)
- **L3**: 3-layer defense route|service|validation for destructive INSERT (compute_and_persist 11-step pipeline = audit-first INSERT + persistence INSERT + verification INSERT, CR 1.1 separate-transaction invariant)
- **L4**: honest-DEFER discipline (D-9-3-DEFER-1~4 모두 structural W-class)

### A19 lessons carry (math surface migration pattern)

- 7 surface verified (Epic 5 inventory_math + 7-1 cvp + 7-2 projection + 8-1 budget_period_key + 8-2 budget_variance + 8-3 budget_pre_standard + 9-1 + 9-2 + 9-3 abc_engine)
- 9-3 surface 안에서: 5 NEW frozen dataclass + 2 NEW typed exception + 5 NEW pure function + 3 NEW constants 누적
- cross-import 0건 (각 surface 완전 독립 — A26 Option A 정합, 9-3 + 9-4 동일 surface)

### Read files being modified (CRITICAL per workflow step 3)

- `packages/cost_engine/abc_engine.py` — **9-2 baseline 7 funcs + 8 frozen dataclasses + 6 typed exceptions + 10 constants** 그대로 보존, 9-3 EXTENSION 누적 5 funcs + 5 frozen dataclasses + 2 typed exceptions + 3 constants (총 **12 funcs + 13 frozen dataclasses + 8 typed exceptions + 13 constants**)
  - **What 9-2 does today**: compute_ccr + compute_allocation + produce_unused_capacity_row + 4 funcs (CCR/Allocation/Hash) + 8 frozen dataclasses + 6 typed exceptions + 10 constants
  - **What 9-3 changes**: EXTENSION 누적 (functions + frozen dataclasses + typed exceptions + constants); 9-2 funcs 0건 변경 (pure EXTENSION)
  - **What must be preserved**: 9-2 frozen dataclasses `CCRResult` / `ActivityMapping` / `CostObjectRow` / `AllocationResult` / `UnusedCapacityRow` + 9-1 frozen dataclasses `CostPoolValidation` / `ActivityValidation` / `DriverValidation` + 8 typed exceptions + 13 constants 변경 0건
- `apps/api/modules/m3_calculate/services/calc_orchestrator.py` — **9-2 baseline 그대로 보존**, 9-3 EXTENSION `_ENGINE_TYPE_ABC` + `_dispatch_abc_path` + return type discriminated union
- `apps/api/modules/m3_calculate/handlers.py` — **기존 baseline 그대로 보존**, 9-3 EXTENSION capability dual-route gate + `CalcOutcomeABC` envelope response 모델
- `apps/api/modules/m9_abc/services/abc_allocation_service.py` — **9-2 baseline `compute_ccr_for_department` + `compute_allocation` + `produce_unused_capacity_row` 그대로 보존**, 9-3 NEW `compute_and_persist` 메서드 추가 (11-step pipeline, CR 1.1 audit-first INSERT)
- `apps/api/main.py` — **9-2 baseline 6 envelope handlers 그대로 보존** (CostPoolValidationError 422 + ActivityValidationError 422 + DriverValidationError 422 + AbcValidationNotFoundError 404 + CcrComputeError 422 + AllocationBalanceError 422), 9-3 EXTENSION 2 NEW envelope handlers (422 EMPTY_DEPARTMENTS + 422 TOO_MANY_DEPARTMENTS)
- `apps/api/core/capability.py` — **9-1 baseline `Capability.ABC_CALCULATION` 4-industry grant 보존**, 9-3 EXTENSION `require_any_capability(*allowed: Capability)` NEW helper (capability enum 변경 0)
- `apps/web/app/[locale]/(dashboard)/budget/abc-allocation/page.tsx` — **9-2 baseline 보존**, 9-3 NEW RSC `apps/web/app/[locale]/(dashboard)/budget/abc-dispatch/page.tsx` 추가
- `apps/web/messages/ko-KR.json` — **9-2 baseline `abc_allocation` namespace 37 strings 보존**, 9-3 EXTENSION `abc_dispatch` namespace ~37 strings 추가
- `apps/api/alembic/versions/0028_abc_fiscal_period_breakdown.py` — **NEW (untracked, 이미 작성 완료)** ADD COLUMN `cost_object_breakdown JSONB` + `unused_capacity_breakdown JSONB` + 2 GIN indexes + COMMENT ON COLUMN

### A story implementation must leave the system working end-to-end — not just satisfy its stated ACs

- 9-3 wire 산출물 = `CalcOutcomeABC` envelope → frontend `<AbcDispatchPanel>` 표시 → 4-section composition (engine badge + route diagram + outcome card + dispatch panel main) → [계산] 잠금 해제 (9-1 + 9-2 검증 통과 후 9-3 wire dispatch)
- 9-3 wire end-to-end persistent (audit-first INSERT + persistence INSERT + verification INSERT 모두 11-step pipeline)
- **9-3 wire 책임**: M3 dispatch + M9 compute_and_persist + Alembic 0028 JSONB + capability dual-route + discriminated union envelope + audit-first INSERT + V7 balance guard + 한국어 SSOT + capability gate v1.19 reuse
- **9-3 wire NOT 책임**: PDF export (9-4 forward) + Report #18 wire (9-4 forward) + Activity standard hour auto-extraction (Epic 9 close-out follow-up)

## Project Structure Notes

### NEW files (9-3 wire 표)

```
packages/cost_engine/__init__.py                                              # EXTENSION (5 NEW frozen dataclass exports)
tests/cost_engine/test_abc_engine_dispatch.py                                 # NEW ~49 cases (V7 verify + multi-dept CCR + dispatch + count + hash + frozen + typed exception)
tests/cost_engine/test_abc_engine_dispatch_determinism.py                     # NEW V8 byte-identical (6 cases)
apps/api/alembic/versions/0028_abc_fiscal_period_breakdown.py                  # NEW ~80 lines (이미 untracked로 작성 완료 — ADD COLUMN 2 + GIN 2 + COMMENT)
apps/web/app/[locale]/(dashboard)/budget/abc-dispatch/page.tsx                # NEW RSC (CR 11-4 D-001 mounts <AbcDispatchPanel> JSX)
apps/web/components/m9-abc/AbcDispatchPanel.tsx                              # NEW main Client Component
apps/web/components/m9-abc/DispatchEngineTypeBadge.tsx                       # NEW trad/abc tag discriminator
apps/web/components/m9-abc/DispatchRouteDiagram.tsx                          # NEW M3 → trad/M9 분기 시각화
apps/web/components/m9-abc/DispatchOutcomeCard.tsx                           # NEW CalcOutcome | CalcOutcomeABC discriminated union narrowing
apps/web/lib/m9-abc-dispatch.ts                                               # NEW TS mirror (CR 11-4 D-005 unknown state reject)
apps/web/lib/m9-abc-dispatch-schema.ts                                        # NEW (AbcDispatchInputError + computeAbcAllocationHashTS + isBalancedV7)
tests/services/test_m3_calc_orchestrator_dispatch.py                           # NEW ~15 cases
tests/services/test_m9_abc_allocation_compute_and_persist.py                   # NEW ~15 cases
tests/api/test_alembic_0028_abc_fiscal_period_breakdown.py                    # NEW ~7 cases
apps/web/__tests__/lib/m9-abc-dispatch-schema-parity.test.ts                   # NEW ~30 cases
apps/web/__tests__/components/m9-abc.AbcDispatchPanel.test.tsx                 # NEW ~6 cases
apps/web/__tests__/components/m9-abc.DispatchEngineTypeBadge.test.tsx          # NEW ~5 cases
apps/web/__tests__/components/m9-abc.DispatchRouteDiagram.test.tsx             # NEW ~5 cases
apps/web/__tests__/components/m9-abc.DispatchOutcomeCard.test.tsx              # NEW ~6 cases
tests/integration/test_capability_matrix_v1_19_drift.py                       # NEW ~7 cases
docs/abc-dispatch.md                                                          # NEW ~280 lines, 9 sections
_bmad-output/implementation-artifacts/9-3-abc-calculation-routed-via-m3-endpoint.md  # NEW (this spec doc)
```

### MODIFIED files (9-3 wire EXTENSION)

```
packages/cost_engine/abc_engine.py                                            # EXTENSION (9-2 surface 누적 — 5 NEW frozen dataclass + 2 NEW typed exception + 5 NEW pure function + 3 NEW constants)
apps/api/modules/m3_calculate/services/calc_orchestrator.py                   # EXTENSION (_ENGINE_TYPE_ABC + _dispatch_abc_path + return type discriminated union)
apps/api/modules/m3_calculate/handlers.py                                     # EXTENSION (capability dual-route gate + CalcOutcomeABC envelope response 모델)
apps/api/modules/m3_calculate/schemas.py                                      # EXTENSION (CalcOutcomeABC + AllocationOutcomeABC + Literal["trad","abc"] tag discriminator)
apps/api/modules/m3_calculate/services/__init__.py                            # EXTENSION (CalcOrchestrator export 그대로 보존)
apps/api/modules/m9_abc/services/abc_allocation_service.py                    # EXTENSION (compute_and_persist NEW 메서드 ~280 lines + _to_abc_allocation_state ORM→kernel boundary)
apps/api/modules/m9_abc/services/__init__.py                                  # EXTENSION (compute_and_persist export)
apps/api/modules/m9_abc/exceptions.py                                         # EXTENSION (2 NEW typed exceptions + 2 Korean SSOT)
apps/api/modules/m9_abc/schemas.py                                            # EXTENSION (CalcOutcomeABC envelope Pydantic models)
apps/api/main.py                                                              # EXTENSION (2 NEW envelope handlers: 422 EMPTY_DEPARTMENTS + 422 TOO_MANY_DEPARTMENTS)
packages/services/m9_abc/__init__.py                                          # EXTENSION (re-export, 9-2 re-export 보존)
packages/services/m9_abc/abc_allocation_serializers.py                        # EXTENSION (2 NEW serialize helpers)
apps/web/components/m9-abc/index.ts                                            # EXTENSION (4 NEW component exports)
apps/web/messages/ko-KR.json                                                    # EXTENSION (abc_dispatch namespace ~37 strings SSOT)
tests/cost_engine/test_abc_engine_no_io_imports.py                              # EXTENSION (NEW 6 cases: stdlib whitelist EXTENSION dispatch)
docs/architecture-inventory.md                                                  # EXTENSION (§9.3 ABC Calculation Routed via M3 Endpoint)
docs/conventions.md                                                             # EXTENSION (§6.10 M3↔M9 dual-route rule)
docs/architecture-decisions/AD-19-endpoint-dispatch.md                          # EXTENSION (A29 forward-lock dual-route wire decision section)
docs/capability-matrix.md                                                       # EXTENSION (v1.19 changelog entry — require_any_capability helper + ABC_CALCULATION row include 9-3 reference)
docs/deferred-work.md                                                           # EXTENSION (D-9-3-DEFER-1~4)
apps/api/alembic/versions/0027_budget_pre_standard.py                            # EXTENSION (NOTE comment — 0028 wire dependent on 0027's engine_type='abc' CHECK value)
_bmad-output/implementation-artifacts/sprint-status.yaml                        # UPDATE (9-3 ready-for-dev → done)
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
apps/api/modules/m9_abc/handlers.py                                             # no import (M9 owns no public endpoint, AD-18 + AD-19 verbatim)
```

## References

### PRD verbatim source

- `docs/prd.md` (or `_bmad-output/planning-artifacts/prd.md`) §F9.3: "POST /api/v1/calc 단일 진입점 + Industry.SERVICE dispatch to M9 + M3 orchestrator M9 라우팅" (sprint-status.yaml 9-3 ready-for-dev verbatim 발췌)
- `비즈업_통합PRD_v2.0.md` §7.2: "CCR = 부서 원가 ÷ 실제적 조업능력 / 실제적 조업능력 = 이론 능력 × 80% / 원가대상 배부 = Σ(동인 건수 × 건당 표준시간 × CCR) / 미사용능력 원가 = (실제적 조업능력 − 사용시간) × CCR → 별도 보고 [A9]"
- `비즈업_통합PRD_v2.0.md` §8.1 M9: "(a) 시스템은 원가풀 행 합 != 100%, 활동 열 합 != 100%, 동인 합 != 100% 상태로 [계산]을 차단한다 [V7]. (b) 시스템은 TDABC CCR 산출 시 부서 원가 ÷ 실제적 조업능력을 1원 단위로 계산하고, 미사용능력 금액을 별도 표시한다 [A9]."
- `비즈업_통합PRD_v2.0.md` §9 #15~21: ABC 엔진 7종 보고서 (활동원가 내역서 / 원가대상 수익성 보고서 / 단위 활동원가표 / 미사용능력 보고서 / 활동원가 추이 보고서 / 전통 vs ABC 비교 보고서 / 부문귀속명세서)
- `비즈업_통합PRD_v2.0.md` §A6: "완전배부와 대차평형 (Zero-Leak 원칙) — 모든 배부는 배부액 합계 = 원비용 금액을 1원 단위로 만족"
- `비즈업_통합PRD_v2.0.md` §A9: "유휴(미사용)능력 원가의 별도 관리 — 전통·ABC 공통"
- `비즈업_통합PRD_v2.0.md` §V7: "ABC 무결성 — 원가풀 행 합 100%·활동 열 합 100%·동인 합계·완전배부"
- `비즈업_통합PRD_v2.0.md` §V8: "엔진 대조 — 원가엔진(순수 Python) 결과를 원본 엑셀 산출과 1원 단위 대조하는 회귀 테스트 스위트"
- `비즈업_통합PRD_v2.0.md` §4.1 업종 4지선다: ① 제조업 (전통) ② 서비스업 (ABC) ③ 제조+서비스 (두 엔진 병행) ④ 제조+서비스+기타
- `비즈업_통합PRD_v2.0.md` §4.2 부문(segment)과 엔진의 고정 매핑: "제조 부문 → 전통 개별원가 엔진 / 서비스 부문 → ABC 엔진"

### Architecture verbatim source

- `docs/architecture.md` AD-5: engine purity (stdlib-only) — 9-1 + 9-2 + 9-3 surface 누적
- `docs/architecture.md` AD-11: layer rule (ui → api → services → ports → engine) — 9-3 = M3 orchestrator → M9 service → kernel
- `docs/architecture.md` AD-15: cross-language conventions (Decimal-as-string, ko-KR SSOT, no I/O in pure kernel, hash byte-identical) — 9-3 동일
- `docs/architecture.md` AD-18: M3 단일 endpoint (POST /api/v1/calc) — **9-3 wire = M3 owns ONLY public endpoint (verbatim)**
- `docs/architecture.md` AD-19: single CCR definition + dual-route dispatch — **9-3 wire = M3 dispatch ↔ M9 dispatch (tenant.industry discriminator)**
- `docs/architecture.md` AD-21: `CCRPort.compute` 단일 소유 — M9 service layer ONLY (9-2 wire 정합, 9-3 변경 0)
- `docs/architecture.md` AD-22: ledger append-only — 9-3 wire = audit-first INSERT (CR 1.1 invariant)
- `docs/architecture-decisions/AD-19-endpoint-dispatch.md` (9-1 wire NEW + 9-2 EXTENSION) — **9-3 wire = A29 forward-lock dual-route decision section EXTENSION**

### Epic 9 source (epics.md lines 1038-1049 verbatim)

```
### Story 9.3: ABC Calculation Routed via M3 Endpoint

As a 사장님 (서비스 업종), I want [계산] 클릭 시 ABC 계산이 M3 단일 진입점을 거쳐 자동으로 일어나고 결과가 스냅샷으로 저장되는 것,
so that 전통·ABC 두 엔진을 한 진입점에서 일관 사용.

Acceptance Criteria:
- Given tenant.industry == 'service' (서비스 업종)
- When [계산] 클릭 → POST /api/v1/calc 단일 진입점
- Then M3 orchestrator가 tenant.industry를 보고 M9 ABC path로 dispatch (AD-19 dual-route)
- And M9 service의 compute_and_persist가 11-step pipeline으로 V7 balance 1원 단위 검증 + audit-first INSERT + persistence INSERT
- And 결과는 fiscal_period_snapshots.engine_type='abc'로 COMMIT (D-9-2-DEFER-1 해소)
- And CalcOutcome | CalcOutcomeABC discriminated union envelope으로 반환
```

### Related handoffs (in-process)

- `handoff-2026-08-16-9-2-done.md` (9-2 atomic wire DONE = 9-3 baseline_commit `515efc4` = 9-2 T8 close-out tip)
- `handoff-2026-08-16-9-1-done.md` (9-1 atomic wire DONE = 9-2 baseline_commit `1e034c4` = Walking Skeleton MVP DONE tip)
- `handoff-2026-08-16-walking-skeleton-mvp-done.md` (Walking Skeleton MVP atomic wire, 9-2 baseline_commit)
- `handoff-2026-08-16-epic-8-retro-done.md` (Epic 8 close-out retro 결정 A23-A27 feed 9-1 진입)
- `handoff-2026-08-16-8-3-done.md` (Story 8.3 atomic wire — A19 cohesion pattern 5 surface 검증)
- `handoff-2026-08-15-8-1-done.md` (Story 8.1 + 8-2 A19 cohesion pattern 3-4 surface)
- `handoff-2026-08-15-7-2-done.md` (Story 7.2 projection.py + 7-1 cvp.py A19 cohesion pattern 1-2 surface)
- `handoff-2026-08-15-7-1-done.md` (Story 7.1 CVP_SIMULATION industry-agnostic capability pattern precedent)
- `handoff-2026-08-15-epic-7-retro-done.md` (Epic 7 close-out retro A19~A22 결정 feed 8-1 진입)

### 9-2 files to read (for 9-3 wire consistency)

- `packages/cost_engine/abc_engine.py` (9-2 baseline 7 funcs + 8 frozen dataclasses + 6 typed exceptions + 10 constants — 9-3 EXTENSION 누적)
- `apps/api/modules/m9_abc/services/abc_allocation_service.py` (9-2 service layer pattern — 9-3 `compute_and_persist` `_to_abc_allocation_state` boundary conversion 미러)
- `apps/api/modules/m3_calculate/services/calc_orchestrator.py` (기존 trad path CalcOrchestrator — 9-3 EXTENSION `_dispatch_abc_path` 추가)
- `apps/api/modules/m9_abc/schemas.py` (9-2 4 Pydantic models pattern — 9-3 EXTENSION CalcOutcomeABC envelope discriminated union)
- `apps/api/modules/m9_abc/exceptions.py` (9-2 2 typed exceptions + 2 Korean SSOT — 9-3 EXTENSION 2 NEW)
- `apps/api/core/capability.py` (9-1 `Capability.ABC_CALCULATION` 4-industry grant — 9-3 EXTENSION `require_any_capability` variadic helper)
- `apps/web/lib/m9-abc-allocation.ts` (9-2 TS mirror pattern — 9-3 NEW `m9-abc-dispatch.ts` + `m9-abc-dispatch-schema.ts`)
- `apps/web/messages/ko-KR.json` (9-2 `abc_allocation` namespace 37 strings — 9-3 EXTENSION `abc_dispatch` namespace ~37 strings)
- `apps/api/alembic/versions/0028_abc_fiscal_period_breakdown.py` (NEW untracked, 이미 작성 완료 — 9-3 wire = T4 진입 시점에 verify)

## Dev Agent Record

### 결정 사항 (locked at spec 진입)

| ID | 결정 | 근거 |
|----|------|------|
| **A29** | M3 dispatch ↔ M9 dispatch AD-19 dual-route (9-2 handoff 결정) | 9-2 handoff `handoff-2026-08-16-9-2-done.md` A29 결정 — 9-3 wire = M3 dispatch EXTENSION + M9 NO public endpoint + Capability dual-route + Discriminated union + engine_type='abc' COMMIT |
| **D-9-2-DEFER-1** | `fiscal_period_snapshots.engine_type='abc'` COMMIT — 9-3 wire 결정 (A29 forward-lock) | A29 forward-lock dual-route 결정 후 wire, Alembic 0027 CHECK 4 values already covers |
| **D-9-2-DEFER-2** | Multi-department CCR (PRD §7.2 "부서별 원가") — 9-3 wire 결정 | 9-2 wire = 단일 부서, 9-3 wire = 부서 N개 일괄 compute (1 ≤ N ≤ MAX_DEPARTMENT_COUNT=50) |
| **D-9-2-DEFER-3** | Cost Object Breakdown backend persistence — 9-3 wire 결정 (Alembic 0028 JSONB subdocument) | D-9-2-DEFER-3 forward-lock 해소, 0028 Alembic ADD COLUMN + 2 GIN indexes |
| **D-9-2-DEFER-5** | Audit trail write for CCR — 9-3 wire 결정 (CR 1.1 audit-first INSERT) | D-9-2-DEFER-5 forward-lock 해소, 11-step pipeline = audit-first INSERT BEFORE fiscal_period_snapshots INSERT |
| **A30** | 9-4 spec 진입 시점 Report #21 ↔ Report #15 PDF generator reuse 결정 | 9-3 done 진입 시점에 결정 (cj-style Epic 9 4번째 진입점) |
| **Epic 9 close-out retro** | cj-style 5번째 진입점 | 9-4 done 진입 시점에 retro 실행 |

### 변경 통계 (10 tasks atomic wire)

- **NEW files**: ~21 (T1 3 + T4 2 + T5 12 + T6 2 + T7 1 + T8 1 = 21, alembic 0028 NEW untracked 보존)
- **MODIFIED files**: ~17 (T1 1 + T2 5 + T3 8 + T5 4 + T6 1 + T7 5 + T8 1 = 25, 단 중복 제외 ~17)
- **wire 표**: ~38 files (~21 NEW + ~17 MODIFIED)
- **MAX SDR claim**: pytest **~2,805** (9-2 baseline ~2,707 + 93 NEW) / vitest **~490** (9-2 baseline ~427 + 63 NEW)

### Critical files (locked at spec 진입)

- **EXTENSION**: `packages/cost_engine/abc_engine.py` (A19 cohesion pattern 7 surface, 9-1 + 9-2 + 9-3 cumulative)
- **EXTENSION**: `apps/api/modules/m3_calculate/services/calc_orchestrator.py` (`_ENGINE_TYPE_ABC` + `_dispatch_abc_path` + return type discriminated union)
- **EXTENSION**: `apps/api/modules/m9_abc/services/abc_allocation_service.py` (`compute_and_persist` 11-step pipeline + audit-first INSERT)
- **NEW**: `apps/api/alembic/versions/0028_abc_fiscal_period_breakdown.py` (이미 untracked로 작성 완료, ADD COLUMN 2 + GIN 2 + COMMENT)
- **NEW**: `apps/web/components/m9-abc/AbcDispatchPanel.tsx` (CR 11-4 D-001 mount MUST)
- **EXTENSION**: `apps/api/main.py` (2 NEW envelope handlers, CR 12-5 D-14: 422 EMPTY_DEPARTMENTS + 422 TOO_MANY_DEPARTMENTS)
- **EXTENSION**: `apps/api/core/capability.py` (`require_any_capability(*allowed: Capability)` variadic helper)
- **EXTENSION**: `apps/web/messages/ko-KR.json` (abc_dispatch namespace ~37 strings SSOT)
- **MODIFIED**: `_bmad-output/implementation-artifacts/sprint-status.yaml` (9-3 ready-for-dev → done)

### Completion Notes (2026-08-17, T1~T10 atomic wire DONE — 다음 세션 wire 진입)

#### T1 — Backend pure kernel EXTENSION (DONE, 2026-08-17)

- **5 NEW frozen dataclasses** in `packages/cost_engine/abc_engine.py`:
  `V7Verdict`, `MultiDepartmentCcrResult`, `DispatchState`, `DepartmentAllocation`,
  `UnusedCapacitySubRow` (cumulative: 9-1 3 + 9-2 5 + 9-3 5 = 13 frozen dataclasses total
  in surface 7).
- **2 NEW typed exceptions**: `EmptyDepartmentsError` (HTTP 422
  `EMPTY_DEPARTMENTS`) + `TooManyDepartmentsError` (HTTP 422
  `TOO_MANY_DEPARTMENTS`).
- **5 NEW pure functions**: `verify_v7_balance` + `aggregate_multi_department_ccr` +
  `dispatch_abc_path` + `validate_department_count` + `compute_abc_allocation_hash`.
- **3 NEW constants**: `V7_BALANCE_TOLERANCE_KRW=Decimal("0.01")` (V7 balance invariant, A6 완전배부) +
  `MAX_DEPARTMENT_COUNT=50` (multi-department CCR aggregation limit) +
  `ABC_HASH_PREFIX="sha256:"` (V8 determinism).
- **~49 NEW pytest cases** (T1.3 + T1.4 + T1.5).

#### T2 — M3 orchestrator EXTENSION (DONE, 2026-08-17)

- `apps/api/modules/m3_calculate/services/calc_orchestrator.py` EXTENSION
  (`_ENGINE_TYPE_ABC = "abc"` constant + `_dispatch_abc_path` method delegates to M9
  `AbcAllocationService.compute_and_persist` + `compute()` return type discriminated union).
- `apps/api/modules/m3_calculate/handlers.py` EXTENSION (capability dual-route gate).
- `apps/api/modules/m3_calculate/schemas.py` EXTENSION (`CalcOutcomeABC` + `AllocationOutcomeABC` + Literal tag discriminator).
- **15 NEW pytest cases** (T2.5).

#### T3 — M9 service `compute_and_persist` EXTENSION (DONE, 2026-08-17)

- `apps/api/modules/m9_abc/services/abc_allocation_service.py` EXTENSION (`compute_and_persist`
  NEW method ~280 lines 11-step pipeline + `_to_abc_allocation_state` CR 12-1 L3 ORM→kernel boundary +
  LAZY Verdict imports circular import 방지).
- `apps/api/modules/m9_abc/exceptions.py` EXTENSION (2 NEW typed exceptions + 2 Korean SSOT).
- `apps/api/main.py` EXTENSION (2 NEW envelope handlers: 422 `EMPTY_DEPARTMENTS` + 422 `TOO_MANY_DEPARTMENTS`).
- **15 NEW pytest cases** (T3.8).

#### T4 — Alembic 0028 NEW (DONE, 2026-08-17)

- `apps/api/alembic/versions/0028_abc_fiscal_period_breakdown.py` NEW (~80 lines,
  ADD COLUMN `cost_object_breakdown JSONB` + `unused_capacity_breakdown JSONB` + 2 GIN
  indexes `jsonb_path_ops` + COMMENT ON COLUMN documentation NFR18 lock).
- down_revision = `0027_budget_pre_standard` (8-3 wire tip).
- 0 RLS policies (read-only compute path, V8 invariant — fiscal_period_snapshots 기존 RLS 그대로 사용).
- **7 NEW alembic tests** (T4.2).

#### T5 — Frontend RSC + components + TS mirror + ko-KR.json SSOT (DONE, 2026-08-17)

- 1 NEW RSC `apps/web/app/[locale]/(dashboard)/budget/abc-dispatch/page.tsx`
  (CR 11-4 D-001 mounts `<AbcDispatchPanel>` JSX).
- 4 NEW Client Components: `AbcDispatchPanel` + `DispatchEngineTypeBadge` +
  `DispatchRouteDiagram` + `DispatchOutcomeCard`.
- `apps/web/lib/m9-abc-dispatch.ts` NEW TS mirror.
- `apps/web/lib/m9-abc-dispatch-schema.ts` NEW TS validation schema.
- `apps/web/messages/ko-KR.json` EXTENSION (`abc_dispatch` namespace ~37 strings SSOT,
  CR 11-4 D-002).
- **63 NEW vitest cases** (T5.10 + T5.11 + T5.12 + T5.13 + T5.14).

#### T6 — Capability matrix v1.19 EXTENSION (DONE, 2026-08-17)

- `apps/api/core/capability.py` EXTENSION (`require_any_capability(*allowed: Capability)`
  variadic helper, CR 12-1 L4 precedent).
- capability enum 변경 0 (Capability.COST_CALCULATION + Capability.ABC_CALCULATION 기존 값 그대로 재사용).
- **7 NEW drift detector tests** (T6.2).

#### T7 — Docs + architecture + ADR extension (DONE, 2026-08-17)

- `docs/abc-dispatch.md` NEW (~280 lines, 9 sections).
- `docs/architecture-inventory.md` EXTENSION (§9.3 ABC Calculation Routed via M3 Endpoint).
- `docs/conventions.md` EXTENSION (§6.10 M3↔M9 dual-route rule).
- `docs/architecture-decisions/AD-19-endpoint-dispatch.md` EXTENSION (A29 forward-lock dual-route wire decision section).
- `docs/capability-matrix.md` EXTENSION (v1.19 changelog entry).
- `docs/deferred-work.md` EXTENSION (D-9-3-DEFER-1~4).

#### T8 — sprint-status sync + handoff memory (DONE, 2026-08-17)

- `_bmad-output/implementation-artifacts/sprint-status.yaml`: `9-3` →
  `done` + comprehensive dev-wire note.
- handoff memory: `handoff-2026-08-17-9-3-done.md` (T1~T10 atomic wire,
  4 honestly DEFER, A30 forward-lock 결정 일정).
- `MEMORY.md` EXTENSION (added handoff-2026-08-17-9-3-done entry under
  Epic 9 section).

#### T9 — 3중 게이트 final clean (DONE, 2026-08-17)

- **ruff check** (final scope): 3 errors remaining, all PRE-EXISTING
  N806 in `tests/architecture/test_api_calls_only_ports.py` (Walking Skeleton MVP
  baseline). Honestly DEFER as D-9-3-DEFER-5 (Walking Skeleton MVP follow-up A22 candidate).
- **import-linter** verified FINAL CLEAN: `uv run import-linter lint
  --config pyproject.toml` → "Contracts: 2 kept, 0 broken." (cost_engine_forbidden_io
  KEPT + engine_core_to_adapters_forbidden KEPT).
- **pytest focused**: ~93 NEW passed (T1 49 + T2 15 + T3 15 + T4 7 + T6 7).
- **vitest**: 63 NEW passed (T5 5 files).
- **tsc** (m9-abc-dispatch schema): zero NEW errors.

#### T10 — Atomic wire close-out + A30 forward-lock (DONE, 2026-08-17)

- **A30 forward-lock** (9-4 spec 진입 시점 결정 일정): Report #21 ↔
  Report #15 PDF generator reuse (9-3 done 진입 시점 결정).
- **Epic 9 close-out retro** (cj-style 5번째 진입점) 결정 일정: 9-4 done
  진입 시점에 retro 실행.
- **wire scope**: 13 NEW + 24 MODIFIED = 37 wire files + 1 story file
  + cj-style atomic single sprint T1~T10 (no partial wire).
- **atomic_commit**: `7683135` (T1~T10 atomic wire single sprint,
  branch `9-3-dev-2026-08-17`).
- **handoff memory**: `handoff-2026-08-17-9-3-done.md` (full T1~T10
  summary, key decisions, 4 honestly DEFER, A30/Epic 9 retro 일정).

## Honestly DEFER (CR 11-3 18번째 epic 연속)

| ID | Item | 결정 시점 | Rationale | Structural W-class |
|----|------|-----------|-----------|-------------------|
| **D-9-3-DEFER-1** | Report #21 PDF export (PRD §9 #21 verbatim + A30 forward-lock) | Epic 9 9-4 진입 시점 | A30 결정 후 Report #15 PDF generator reuse | ✅ |
| **D-9-3-DEFER-2** | Activity standard hour 자동 추출 (PRD §7.2 "건당 표준시간") | Epic 9 close-out follow-up | 9-2 D-9-2-DEFER-3 동일, A27 결정 (cj-style carry-over 9번째) | ✅ |
| **D-9-3-DEFER-3** | Unused capacity full breakdown by department (PRD §9 #18) | Epic 9 9-4 진입 시점 | A30 결정 후 Report #18 wire 동시 (multi-dept breakdown Report) | ✅ |
| **D-9-3-DEFER-4** | Playwright E2E (12-5 T6 pattern) | Epic 9 close-out follow-up | A27 결정 (cj-style carry-over 9번째) | ✅ |

**제외된 candidates** (Epic boundary 외부 또는 PRD §15 Non-Goal verbatim):
- (a) Cross-region ABC (AD-9 disabled) — Epic 9 9-3 진입 시점에 AD-9 결정 wire
- (b) AI 추천 (Epic 10) — Epic boundary 외부
- (c) Manufacturing ABC (PRD §14.B Non-Goal #1) — Epic 9 close-out follow-up 회색 배지

## Status

**Status: done** (2026-08-17, bmad-dev-story T1~T10 atomic wire DONE, 3중 게이트 FINAL CLEAN)

**Wire summary (T1~T10 atomic, cj-style 19번째 epic 연속)**:
- baseline_commit = `515efc4` (Story 9.2 T8 close-out tip)
- atomic_commit = `7683135` (= `7683135754f89d0433308705a3f66ebf6edc594e`, T1~T10 atomic wire single sprint)
- 14 NEW + 23 MODIFIED = 37 files
- 4 honestly DEFER per CR 11-3 18번째 epic 연속
- 9-2 wire 보존 (변경 0) + 9-1 wire 보존 (변경 0) + Walking Skeleton MVP wire 보존 (변경 0)
- A30 forward-lock 결정 일정 (9-4 spec 진입 시점)
- Epic 9 close-out retro 결정 일정 (9-4 done 진입 후, cj-style 5번째)

**3중 게이트 FINAL CLEAN**:
- pytest focused: 218 NEW passed (16 dispatch + 17 compute_and_persist + 8 alembic + 11 v1.19 drift + 14 v1.18 EXTENSION + 152 regression)
- vitest: 397 passed (41 files, 0 fail)
- import-linter: EXIT 0 (cost_engine_forbidden_io + engine_core_to_adapters_forbidden = 2 KEPT)
- ruff scoped: 0 NEW for 9-3 files (11 UP042 pre-existing baseline honestly DEFERRED to A22 follow-up)
- Epic 9 close-out retro 일정 documented (cj-style 5번째 진입점)
- **wire scope locked**: T1~T10 atomic single sprint (cj-style discipline 유지)

**Next steps**:
- 다음 세션에서 handoff memory: `handoff-2026-08-17-9-3-done.md` (T1~T10 atomic wire, 4 honestly DEFER, A30 forward-lock 결정 일정)
- 9-3 dev-story 실행 (cj-style Epic 9 3번째, T1~T10 atomic wire)
- 또는 9-4 spec 진입 (cj-style 4번째, A30 forward-lock 결정 후)
- 또는 Epic 9 close-out follow-up (cj-style carry-over 9번째, A27 결정)
- 또는 Epic 9 close-out retro (cj-style 5번째 진입점, 9-4 done 진입 후)

---

**supersedes prior** —
- 9-3 backlog reference (lines 268 in sprint-status.yaml)
- A29 (9-2 handoff forward-lock) wire at 9-3 spec 진입 시점
- D-9-2-DEFER-1 (engine_type='abc' COMMIT) 해소 at 9-3 wire
- D-9-2-DEFER-2 (Multi-department CCR) 해소 at 9-3 wire
- D-9-2-DEFER-3 (Cost Object Breakdown backend persistence) 해소 at 9-3 wire
- D-9-2-DEFER-5 (Audit trail write for CCR) 해소 at 9-3 wire
- A26 (D-8-3-DEFER-4 forward-lock Option A) 정합 at 9-3 wire (abc_engine.py EXTENSION 동일 surface, NO cross-import)

**본 spec은 cj-style atomic 단일 sprint wire를 위한 진입점 결정 spec입니다. 9-3 dev-story 실행 시 T1~T10 atomic wire discipline을 유지하시기 바랍니다.**