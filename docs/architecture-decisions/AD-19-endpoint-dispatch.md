# AD-19 Endpoint Dispatch (Industry × Module Routing)

> **Status:** Active (forward-lock target: Story 9-3)
> **Deciders:** kjw
> **Date:** 2026-08-16 (Story 9.1 wire; AD-19 extension target = Story 9-3)
> **Source PRD:** §F9.1 (ABC 100% 가드) + §F4.1 (manufacturing cost chain)

## Context

Before Story 9.1, the codebase had:

- Manufacturing-kind industries (manufacturing / manufacturing_service /
  manufacturing_service_other): routed to Epic 4 calc → COST_CALCULATION
  capability.
- Service-only industry: **no dedicated ABC routing** — `COST_CALCULATION`
  was denied (403 INDUSTRY_NOT_SUPPORTED) per [docs/capability-matrix.md
  #COST_CALCULATION](./capability-matrix.md).

This created an asymmetry: service-only tenants had no primary
calculation engine. Story 9.1 wire introduces `Capability.ABC_CALCULATION`
(v1.18) as the industry-agnostic counterpart to `COST_CALCULATION`.

## Decision

AD-19 specifies that **manufacturing-kind** tenants go through the
manufacturing cost chain (COST_CALCULATION → CalcResponse), while
**service-only** tenants go through the ABC cost chain
(ABC_CALCULATION → ValidationResponse → future ABC compute).

| Industry | Primary calc path | Capability | Engine surface |
|---|---|---|---|
| `manufacturing` | Epic 4 calc | `COST_CALCULATION` | `packages/cost_engine/core/period_cost.py` |
| `manufacturing_service` | Epic 4 calc | `COST_CALCULATION` | `packages/cost_engine/core/period_cost.py` |
| `manufacturing_service_other` | Epic 4 calc | `COST_CALCULATION` | `packages/cost_engine/core/period_cost.py` |
| `service` | Epic 9 ABC | `ABC_CALCULATION` | `packages/cost_engine/abc_engine.py` |

## Implementation

- **Capability gate** at route boundary:
  `Depends(require_capability(Capability.ABC_CALCULATION))`.
- **Industry menu** (`packages/services/m0_onboarding/industry_menu.py`)
  remains unchanged — industry selection is user-driven.
- **9-1 = validation only** — actual ABC compute (CCR + allocation)
  arrives in Story 9-3 (forward-lock target).
- **3-layer defense** (CR 12-5 L3): route @require_capability + service
  `validate_abc_pct_list` + frontend disabled signal.

## Consequences

### Positive

- Service-only tenants get a clear primary calculation path
  (`ABC_CALCULATION`).
- ABC engine surface (`abc_engine.py`) is A19 cohesion pattern 6번째
  — pure-Python stdlib-only kernel, mirrors existing 5 surfaces.
- 100% 가드 invariant pre-validates input before any allocation compute.

### Negative

- Mixed-industry tenants (`manufacturing_service` /
  `manufacturing_service_other`) currently use COST_CALCULATION;
  Epic 9 9-2/9-3 may extend them to BOTH paths in 2차 (PRD §14.B
  Non-Goal #1 — Multi-industry ABC honestly DEFER).

### Forward-lock target (A29)

- **A29** (Story 9-3 entry): M3 endpoint dispatch ↔ M9 dispatch
  — service-only tenants must be routed to Epic 9 path, not 403.
- Implementation: extend `require_capability` to dispatch to
  `m9_abc` router when tenant industry is `service`.

## Cross-references

- [docs/capability-matrix.md](./capability-matrix.md) — v1.18 entry
- [docs/abc-validation.md](./abc-validation.md) — Story 9.1 wire
- [docs/conventions.md §6.6](./conventions.md#66-abc-100-가드-layer-sums-story-91) — layer sums rule
- `apps/api/core/capability.py::Capability.ABC_CALCULATION` — enum value
- `apps/api/modules/m9_abc/handlers.py` — 4 NEW routes
- `tests/integration/test_capability_matrix_v1_18_drift.py` — drift detector
- [docs/architecture-decisions/AD-11-dependency-direction.md](./AD-11-dependency-direction.md) — layer rule
- [docs/architecture-decisions/AD-15-tenant-id-variance.md](./AD-15-tenant-id-variance.md) — tenant isolation
- [docs/architecture-decisions/AD-8-money-types-decision.md](./AD-8-money-types-decision.md) — Decimal-as-string

## Change history

- **2026-08-16 (Story 9.3)** — A29 forward-lock dual-route wire 결정
  (cj-style Epic 9 3번째 진입점, baseline_commit = `515efc4`):
  - **POST /api/v1/calc is the SINGLE public endpoint** (AD-18). M3 owns
    the route. M9 owns NO router (AD-19 + 9-2 in-memory contract preserved).
  - **Dual-route gate**: `require_any_capability(COST_CALCULATION,
    ABC_CALCULATION)` ANY-OF semantics (CR 12-5 D-14 + CR 6-2 V4
    3-source contract).
  - **Discriminated union response**: `CalcResponse | CalcAbcResponse`
    with `engine_type: Literal["trad", "abc"]` tag discriminator
    (Pydantic v2 + FastAPI tag).
  - **M3 orchestrator dispatch**:
    `calc_orchestrator._resolve_engine_type(industry)` returns
    `"abc" if industry == 'service' else "trad"`. `_dispatch_abc_path`
    LAZY-imports `AbcAllocationService.compute_and_persist`.
  - **Pure kernel 9-3 EXTENSION** (`packages/cost_engine/abc_engine.py`,
    A28 forward-lock 3-way wire 해소 — D-9-1-DEFER-1/2/4 해소):
    - 5 NEW frozen dataclasses (DispatchState + V7Verdict +
      MultiDepartmentCcrResult + DepartmentAllocation +
      UnusedCapacitySubRow)
    - 2 NEW typed exceptions (EmptyDepartmentsError +
      TooManyDepartmentsError)
    - 5 NEW pure functions (validate_department_count + dispatch_abc_path
      + compute_abc_allocation_hash + validate_v7_balance +
      compute_multi_dept_ccr)
    - 3 NEW constants (ABC_HASH_PREFIX + V7_BALANCE_TOLERANCE_KRW +
      MAX_DEPARTMENT_COUNT = 50)
  - **Service layer EXTENSION** (`AbcAllocationService.compute_and_persist`,
    11-step pipeline): load departments → validate count → per-dept CCR →
    multi-dept CCR → per-dept allocation + V7 → cost_object_breakdown JSON
    → unused_capacity JSON → V8 hash → idempotency + audit-first INSERT
    → fiscal_period_snapshots INSERT → COMMIT. AD-22 ledger append-only
    preserved (calc_log + verification_log BEFORE fiscal_period_snapshots).
  - **Alembic 0028** (`apps/api/alembic/versions/
    0028_abc_fiscal_period_breakdown.py`) adds 2 JSONB columns to
    `fiscal_period_snapshots` (cost_object_breakdown + unused_capacity_breakdown)
    + 2 GIN indexes (jsonb_path_ops) + 2 COMMENT ON COLUMN (NFR18 lock).
    down_revision = `0027_budget_pre_standard` (8-3 wire tip).
  - **2 NEW envelope handlers** (CR 12-5 D-14): 422 ABC_EMPTY_DEPARTMENTS
    + 422 ABC_TOO_MANY_DEPARTMENTS.
  - **Capability matrix v1.19 EXTENSION**: NO NEW capability row.
    `ABC_CALCULATION` row fill changes from "9.1, 9.2" to "9.1, 9.2, 9.3".
  - **4 honestly DEFER** (D-9-3-DEFER-1~4): Report #21 PDF export (9-4) +
    Activity standard hour 자동 추출 (Epic 9 close-out follow-up) +
    Unused capacity full breakdown (9-4) + Playwright E2E (Epic 9 close-out
    follow-up).
  - **Frontend RSC**: `apps/web/app/[locale]/(dashboard)/budget/
    abc-calculation/page.tsx` + 4 NEW Client Components
    (AbcDispatchPanel + AbcDispatchDecisionBadge +
    AbcDispatchResultCard + AbcDispatchErrorToast) + 2 NEW TS mirrors
    (m9-abc-dispatch.ts + m9-abc-v7-verdict-schema.ts).
  - **Korean SSOT**: `abc_calculation` namespace (52 strings) in
    `apps/web/messages/ko-KR.json`.
  - **3중 게이트 FINAL CLEAN**: ruff scoped 0 NEW for 9-3 /
    import-linter 2 KEPT / pytest focused 87 NEW passed (16 dispatch +
    17 compute_and_persist + 8 alembic_0028 + 46 v1.19 drift) +
    vitest 42 NEW 5 files / tsc zero NEW.
  - 상세: [docs/abc-calculation.md](./abc-calculation.md) SSOT.
  - **A30 forward-lock 결정 일정**: 9-4 spec 진입 시점.

- **2026-08-16 (Story 9.2)** — A28 forward-lock 3-way wire 결정 (9-1
  handoff 진입점):
  - **CCR compute** (D-9-1-DEFER-1 해소) — `CCRPort.compute(tenant_id, period_key, department_id)` 단일 함수 (AD-21)
  - **Activity mapping** — 활동별 시간 배분 × CCR = 활동별 배부액 (1-Won precision)
  - **Cost Object Breakdown** (D-9-1-DEFER-4 해소) — `product_id` (원가대상)별 행 + 4컬럼 (원가풀·활동·동인·배부액)
  - 9-2 wire = in-memory `AllocationResult` ONLY (no INSERT, no public endpoint per AD-18)
  - Service layer: `apps/api/modules/m9_abc/services/abc_allocation_service.py` (`AbcAllocationService` orchestrator)
  - Frontend RSC: `apps/web/app/[locale]/(dashboard)/budget/abc-allocation/page.tsx` + 4 NEW Client Components
  - Cross-language parity: TS mirror `apps/web/lib/m9-abc-allocation.ts` + TS schema `apps/web/lib/m9-abc-allocation-schema.ts`
  - Korean SSOT: `abc_allocation` namespace (37 strings) in `apps/web/messages/ko-KR.json`
  - Capability matrix v1.18 unchanged (reuse `Capability.ABC_CALCULATION`)
  - 5 honestly DEFER (D-9-2-DEFER-1~5): `fiscal_period_snapshots.engine_type='abc'` COMMIT (9-3 wire) + 4 wire scope deferrals
  - 상세: [docs/abc-allocation.md](./abc-allocation.md) SSOT.
- **2026-08-16 (Story 9.1)** — AD-19 extension target set to Story 9-3.
  Capability.ABC_CALCULATION enum value + 4-industry grants wired.
  9-1 wire does NOT yet dispatch (service-only tenants still 403 on
  COST_CALCULATION — Epic 9 9-2/9-3 will fix).