# ABC Calculation Routed via M3 Endpoint (Story 9.3, Epic 9)

> PRD §F9.3 verbatim: **"POST /api/v1/calc 단일 진입점 + Industry.SERVICE dispatch to M9"**.
> Epic 9 (ABC / TDABC Engine — Service Business) 3번째 진입점.
>
> **baseline_commit:** `515efc4` (Story 9.2 T8 close-out tip — 2026-08-16)
> **cj-style:** Epic 9 3번째 진입점 (cj-style 4-story 분할: 9-1 + 9-2 + **9-3** + 9-4 + Epic 9 close-out retro 5번째 진입점)
> **A29 forward-lock dual-route:** POST /api/v1/calc is the SINGLE public endpoint. M3
> orchestrator dispatches via `_resolve_engine_type(industry)` to M9 ABC path
> (service-only) or M3 trad path (mfg 3종). Discriminated union response envelope.

## What is dual-route dispatch?

PRD §F9.3 mandates a SINGLE public endpoint (`POST /api/v1/calc`) for
all industries. The orchestrator decides at runtime which compute path
to invoke based on `tenant.industry`:

| tenant.industry | resolved engine_type | compute path |
|---|---|---|
| `manufacturing` | `"trad"` | M3 traditional path (PRD §F0.2 3종 allocation) |
| `manufacturing_service` | `"trad"` | M3 traditional path |
| `manufacturing_service_other` | `"trad"` | M3 traditional path |
| `service` | `"abc"` | M9 ABC path (`AbcAllocationService.compute_and_persist`) |

The response envelope is a **discriminated union**:

```python
# apps/api/modules/m3_calculate/schemas.py
class CalcResponse(BaseModel):           # trad path
    material_cost: float
    labor_cost: float
    # ...

class CalcAbcResponse(BaseModel):        # abc path (engine_type tag)
    engine_type: Literal["abc"] = "abc"  # discriminator
    allocation_outcome: AllocationOutcomeABC
    snapshot_id: uuid.UUID
    result_hash: str
    state: Literal["verified"] = "verified"
    # ...
```

The TypeScript narrow uses the `engine_type` tag:
```ts
function isCalcAbcResponse(outcome: CalcOutcomeResponse): outcome is CalcAbcResponse {
  return "engine_type" in outcome && outcome.engine_type === "abc";
}
```

## Capability dual-route gate

Per AD-19 dual-route, the `POST /api/v1/calc` route uses
`require_any_capability(COST_CALCULATION, ABC_CALCULATION)`:

- `COST_CALCULATION` — mfg-only (mfg 3종 ✅), service-only ❌
- `ABC_CALCULATION` — industry-agnostic (all 4 industries ✅)
- `require_any_capability` ANY-OF semantics: passes if at least one is unlocked
- Net effect: ALL 4 industries can call POST /api/v1/calc
  (CR 12-5 D-14 envelope handler pattern + CR 6-2 V4 3-source contract)

## 11-step pipeline (compute_and_persist)

`AbcAllocationService.compute_and_persist` (M9 service layer) executes
an 11-step pipeline for the ABC path:

1. **load departments** — fetch active cost pools + activities + drivers
2. **validate count** — `validate_department_count(1-50 guard)`
3. **per-dept CCR** — `CCRPort.compute(tenant_id, period_key, department_id)`
4. **multi-dept CCR** — `compute_multi_dept_ccr` aggregation
5. **per-dept allocation + V7** — `compute_allocation` + `validate_v7_balance`
6. **cost_object_breakdown JSON** — serialize per (dept × product × activity × driver)
7. **unused_capacity JSON** — serialize per-dept unused sub-rows
8. **V8 hash** — `compute_abc_allocation_hash` (sha256:64-hex)
9. **idempotency + audit-first INSERT** — check existing snapshot; INSERT
   `calc_log` + `verification_log` BEFORE `fiscal_period_snapshots` INSERT
   (AD-22 ledger append-only)
10. **fiscal_period_snapshots INSERT** — write `cost_object_breakdown` +
    `unused_capacity_breakdown` JSONB columns
11. **COMMIT** — single tx boundary

## V7 balance invariant (1-Won precision)

Per PRD §V7 verbatim, the ABC allocation MUST satisfy:

```
Σ cost_object_breakdown.allocated_krw
  + Σ unused_capacity_breakdown.unused_cost_krw
  = Σ department_cost  (within 1원 단위 tolerance)
```

The kernel validates this with `validate_v7_balance(breakdown_sum,
unused_cost, expected_sum)` using `Decimal` arithmetic at 1-Won precision
(AD-8 cross-language parity with TS BigInt helper).

## Pure kernel EXTENSION (A28 forward-lock 3-way wire 해소)

`packages/cost_engine/abc_engine.py` (9-3 EXTENSION over 9-2):

- **D-9-1-DEFER-1 해소**: per-department CCR computation
- **D-9-1-DEFER-2 해소**: Activity standard hour 자동 추출 (via CCRPort)
- **D-9-1-DEFER-4 해소**: Cost Object Breakdown aggregation
- 5 NEW frozen dataclasses (A28 forward-lock 3-way wire):
  - `DispatchState` (engine_type tag discriminator + V8 hash)
  - `V7Verdict` (Σ breakdown + unused = Σ department, 1-Won precision)
  - `MultiDepartmentCcrResult` (CCR aggregation summary)
  - `DepartmentAllocation` (per-dept allocation summary)
  - `UnusedCapacitySubRow` (per-dept 미사용능력 sub-row)
- 2 NEW typed exceptions: `EmptyDepartmentsError`, `TooManyDepartmentsError`
- 5 NEW pure functions: `validate_department_count` + `dispatch_abc_path` +
  `compute_abc_allocation_hash` + `validate_v7_balance` + `compute_multi_dept_ccr`
- 3 NEW constants: `ABC_HASH_PREFIX = "sha256:"` +
  `V7_BALANCE_TOLERANCE_KRW = Decimal("0.01")` + `MAX_DEPARTMENT_COUNT = 50`

## Alembic 0028 NEW

`apps/api/alembic/versions/0028_abc_fiscal_period_breakdown.py`:

- `down_revision = '0027_budget_pre_standard'` (8-3 wire tip)
- ADD COLUMN `cost_object_breakdown JSONB` + GIN index `jsonb_path_ops`
- ADD COLUMN `unused_capacity_breakdown JSONB` + GIN index `jsonb_path_ops`
- 2 NEW `COMMENT ON COLUMN` documentation (NFR18 lock)

## Wire envelope parity

The discriminated union is wired at 3 layers:

1. **Backend (FastAPI)**: `Union[CalcResponse, CalcAbcResponse]` in handlers.py
   response_model — Pydantic v2 tag discriminator.
2. **Backend (orchestrator)**: `CalcOutcome | CalcOutcomeABC` frozen dataclass
   union — returned by `calc_orchestrator.compute()`.
3. **Frontend (TS)**: `CalcOutcomeResponse = CalcResponse | CalcAbcResponse` —
   narrowed at React boundary via `isCalcAbcResponse` type guard.

The `engine_type` Literal tag is the single source of truth for the
dispatch decision; both TS mirror and Pydantic schema use
`Literal["trad", "abc"]`.

## 422 envelope errors

Per CR 12-5 D-14 envelope handler pattern, 2 NEW typed exceptions map to
422 envelopes:

| Error code | Korean SSOT | Cause |
|---|---|---|
| `ABC_EMPTY_DEPARTMENTS` | "ABC 부서가 등록되지 않았습니다" | 0 departments registered |
| `ABC_TOO_MANY_DEPARTMENTS` | "ABC 부서 수가 한도를 초과했습니다" | > 50 departments (PRD §F9.3 cap) |

Wired by `_m9_abc_empty_departments_error_handler` and
`_m9_abc_too_many_departments_error_handler` in `apps/api/main.py`.

## Cross-references

- `packages/cost_engine/abc_engine.py` — pure kernel 9-3 EXTENSION
- `apps/api/modules/m3_calculate/handlers.py` — capability dual-route gate
- `apps/api/modules/m3_calculate/schemas.py` — `CalcAbcResponse` discriminated union
- `apps/api/modules/m3_calculate/services/calc_orchestrator.py` — dispatch logic
- `apps/api/modules/m9_abc/services/abc_allocation_service.py` — 11-step pipeline
- `apps/api/alembic/versions/0028_abc_fiscal_period_breakdown.py` — Alembic migration
- `apps/web/components/m9-abc/AbcDispatchPanel.tsx` — main Client Component
- `apps/web/lib/m9-abc-dispatch.ts` — TS discriminated union mirror
- `docs/capability-matrix.md` — v1.19 EXTENSION (no NEW capability row)
- `docs/architecture-inventory.md` §9.3 — module structure

## Next steps (A30 forward-lock)

Story 9.4 (cj-style Epic 9 4번째 진입점) will extend the 9-3 wire to:
- Full Report #21 PDF export (D-9-3-DEFER-1 해소)
- Activity standard hour 자동 추출 Epic 9 close-out follow-up
  (D-9-3-DEFER-2 해소)
- Unused capacity full breakdown (D-9-3-DEFER-3 해소)
- Playwright E2E for the dual-route UI (D-9-3-DEFER-4 해소)
- A30 forward-lock 결정 일정: 9-4 spec 진입 시점
