# ABC Allocation Engine (Story 9.2, Epic 9)

> PRD §F9.2 verbatim: **"CCR = 부서 원가 ÷ 실제 조업능력 시간, 1원 단위 + 미사용능력 별도 행 관리"**.
> Epic 9 (ABC / TDABC Engine — Service Business) 2번째 진입점.
>
> **baseline_commit:** `1e034c4` (Walking Skeleton MVP — 2026-08-16 atomic wire tip)
> **cj-style:** Epic 9 2번째 진입점 (cj-style 4-story 분할: 9-1 + **9-2** + 9-3 + 9-4 + Epic 9 close-out retro 5번째 진입점)
> **A28 forward-lock:** CCR ↔ Activity ↔ Cost Object 3-way wire 결정 (9-1 handoff 진입점).

## What is CCR (자원동인율)?

CCR (Cost Center Rate / 자원동인율) is the **per-hour cost rate** for a
department, computed as:

```
CCR (KRW/시간) = 부서 원가 (KRW) ÷ 실제 조업능력 시간 (hours)
```

The result is **rounded to 1원 단위 (1-Won precision)** using `ROUND_HALF_EVEN`
(AD-8 Decimal-as-string parity with backend `Decimal`).

| Input | Example | CCR (1-Won precision) |
|---|---|---|
| department_cost = 13,200,000 KRW, capacity = 400h | `13,200,000 / 400` | **33,000원/시간** |
| department_cost = 19,800,000 KRW, capacity = 600h | `19,800,000 / 600` | **33,000원/시간** |
| department_cost = 1,000,000 KRW, capacity = 100h | `1,000,000 / 100` | **10,000원/시간** |

## 1-Won precision (CCR_KRW_QUANTUM)

`CCR_KRW_QUANTUM = Decimal("1")` enforces that all monetary values
(CCR per hour, allocated KRW, unused cost KRW) are quantized to whole
Won. The backend uses Python `Decimal.quantize(Decimal("1"),
rounding=ROUND_HALF_EVEN)` per AD-8 cross-language parity.

## PRD §A9 — 미사용능력 별도 행 관리

Per PRD §A9 verbatim, unused capacity must be tracked as a **separate
row** in the allocation output:

```
unused_hours    = practical_capacity_hours - used_hours
unused_cost_krw = unused_hours × CCR (KRW/시간)
```

For example: 600h capacity, 400h used, 33,000원/시간 CCR →
`unused_hours = 200h`, `unused_cost_krw = 6,600,000원`.

The frontend renders this as a **회색 배지 (gray badge)** in
`<UnusedCapacityRow>` to visually differentiate from activity breakdown
rows.

## V7 ABC 무결성 (1원 단위 검증)

Per PRD §V7, the ABC allocation must satisfy:

```
Σ (cost_object_breakdown.allocated_krw) + unused_cost_krw = department_cost
```

Tolerance: **0.01 KRW** (1원 단위 precision means integer arithmetic,
tolerance is for any non-integer rounding edge case).

When the equation holds → `is_balanced = True` → 균형 (balanced) badge.
When it fails → `is_balanced = False` → 불균형 (unbalanced) badge.

## A28 forward-lock 3-way wire

9-2 wire unlocks the **3-way forward-lock** from 9-1 handoff:

| Forward-lock target | 9-2 wire element | Frozen dataclass |
|---|---|---|
| **CCR compute** (D-9-1-DEFER-1 해소) | `CCRPort.compute(tenant_id, period_key, department_id)` | `CCRResult` |
| **Activity mapping** | 활동별 시간 배분 × CCR = 활동별 배부액 (1-Won) | `ActivityMapping` |
| **Cost Object Breakdown** (D-9-1-DEFER-4 해소) | `product_id` (원가대상)별 행 + 4컬럼 (원가풀·활동·동인·배부액) | `CostObjectRow` |

AD-21 invariant: `CCRPort.compute` is **single-owned** by the M9 service
layer. No other module may import the compute logic directly (only the
frozen dataclasses + serializers via `packages.cost_engine.abc_engine`).

## Capability gate (v1.18 reuse)

`Capability.ABC_CALCULATION` is **reused** from 9-1 — no new capability
matrix entry. 9-2 wire enforces the same capability gate at the service
layer (CR 12-5 L3).

## 9-2 honestly DEFER (5 items)

D-9-2-DEFER-1: `fiscal_period_snapshots.engine_type='abc'` COMMIT (9-3 wire).
D-9-2-DEFER-2: 9-2 wire does NOT expose public endpoint (AD-18 + AD-19).
  M9 service layer returns in-memory `AllocationResult` ONLY.
D-9-2-DEFER-3: Cost Object Breakdown 4-column UI table is rendered as
  CLIENT-SIDE TanStack Table; no backend persistence (9-3 wire).
D-9-2-DEFER-4: Unused capacity 별도 행 is **gray badge + accordion** in MVP;
  full breakdown by department planned for 9-4.
D-9-2-DEFER-5: 9-2 wire = in-memory compute only; no audit trail write
  (AD-22 ledger append-only invariant preserved).

## Architecture A19 cohesion pattern 7 surface

Per A26 decision, the abc_engine.py kernel surface is the **A19 cohesion
pattern 7 surface** — 9-1 + 9-2 EXTENSION share the same surface with
NO cross-import between sub-modules. Both stories call
`packages.cost_engine.abc_engine.compute_*` functions directly.

## Cross-references

- **Story 9.1** (100% 가드) — `docs/abc-validation.md`
- **Story 9.3** (M3 dispatch wire) — planned
- **Story 9.4** (Report #21 PDF generator reuse) — planned
- **PRD §F9.2** (CCR verbatim 산식)
- **PRD §A9** (미사용능력 별도 행 관리)
- **PRD §V7** (ABC 무결성)
- **AD-19** (single CCR definition) — `docs/architecture-decisions/AD-19-endpoint-dispatch.md`
- **AD-21** (CCRPort.compute 단일 소유)
- **Capability matrix v1.18** — `docs/capability-matrix.md`