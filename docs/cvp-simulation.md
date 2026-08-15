# CVP/BEP Simulation (Story 7.1)

> **Single source of truth** for the CVP (Cost-Volume-Profit) / BEP
> (Break-Even Point) simulation feature — Epic 7 Story 7.1.

## 1. Overview

Story 7.1 implements a real-time BEP slider that recomputes Break-Even
Point and target-profit metrics in **under 1 second** (NFR9 stricter
than 5초 P95 general limit). Users drag 4 sliders (단가 / 단위변동비 /
고정비 / 조업도) and see the impact on BEP 수량, BEP 매출, 목표 이익
수량, and 공헌이익률 — all reconciled against the baseline extracted
from the latest committed `fiscal_period_snapshots`.

This story is the **first entry** into Epic 7 (cj-style 3-story 분할
6번째 epic 연속 검증 — Epic 4·5·6·11·12 + Epic 11/12 carry-over).

## 2. PRD anchors

- **PRD §F7.1 verbatim**: "슬라이더 변경 시 BEP 수량·목표이익을 1초
  이내 재계산."
- **PRD §6.1 engine**: 엔진은 분리 — "엔진은 I/O 일체 없음"
- **NFR9**: P95 ≤ 5초 (general limit) → 7-1 stricter ≤ 1초
- **NFR16**: 100회 동일 입력 → 100회 byte-identical result (V8 determinism)
- **NFR17**: KRW BIGINT monetary types (AD-8)
- **AD-5**: 엔진 순수성 (stdlib-only, no I/O)
- **AD-11**: Layer rule (UI → API → services → ports → engine)
- **AD-3**: RLS multi-tenancy (tenant_id filter)
- **AD-15**: Cross-language conventions (snake_case DB/Python, kebab-case routes, PascalCase TS)

## 3. Architecture (AD-11 layer rule)

```
apps/web (RSC + client component)
  └─ apps/web/components/m7-simulation/CVPSimulationClient.tsx
       ├─ GET /api/v1/simulation/cvp/baseline?period_key=YYYY-MM
       └─ POST /api/v1/simulation/cvp/compute (debounced 150ms)
            ↓
apps/api/main.py (FastAPI envelope)
  └─ apps/api/modules/m7_simulation/handlers.py (2 routes)
       ├─ POST /api/v1/simulation/cvp/compute → service.compute()
       └─ GET  /api/v1/simulation/cvp/baseline → service.fetch_cvp_baseline()
            ↓
apps/api/modules/m7_simulation/services/cvp_simulation_service.py
  ├─ fetch_cvp_baseline() — SELECT fiscal_period_snapshots + products
  └─ simulate_cvp()       — delegate to pure kernel (no DB writes)
            ↓
packages/services/m7_simulation/ (thin wrappers)
  ├─ serializers.py  — Decimal-as-string JSON-safe
  └─ delta_helpers.py — clamp_delta + validate_delta_bounds
            ↓
packages/cost_engine/cvp.py (PURE KERNEL — stdlib-only)
  ├─ compute_bep()         — pure math
  ├─ compute_target_profit() — pure math
  ├─ apply_delta()         — pure math (immutable)
  ├─ simulate_cvp()        — full orchestration
  └─ compute_bep_hash()    — V8 determinism digest
```

## 4. Pure kernel surface (`packages/cost_engine/cvp.py`)

**5 NEW pure functions** (stdlib-only: `hashlib`, `dataclasses`,
`decimal`, `typing`):

| Function | Purpose | Edge cases |
|----------|---------|------------|
| `compute_bep(*, fixed_cost, unit_variable_cost, unit_price)` | BEP 수량·매출·공헌이익·공헌이익률 | unit_price ≤ unit_variable_cost → ValueError; fixed_cost < 0 → ValueError; fixed_cost == 0 → trivially 0 |
| `compute_target_profit(*, target_profit, fixed_cost, ...)` | 목표이익 달성 수량·매출 | unit_price ≤ variable_cost → ValueError; target_profit < 0 → ValueError; fixed_cost < 0 → ValueError |
| `apply_delta(baseline, delta)` | 4-variable delta → new immutable `CVPBaseline` | operating_rate out of bounds → ValueError |
| `simulate_cvp(*, baseline, delta)` | Full orchestration (baseline + simulated BEP/target) | baseline not mutated (frozen=True) |
| `compute_bep_hash(result)` | sha256(repr(result)) digest (V8 determinism) | non-BEP/CVP/TargetProfit result → ValueError |

**5 NEW frozen dataclasses** (with `slots=True`):

| Dataclass | Fields | Purpose |
|-----------|--------|---------|
| `BEPResult` | bep_quantity, bep_revenue, contribution_margin_per_unit, contribution_margin_ratio | BEP output |
| `TargetProfitResult` | target_quantity, target_revenue | 목표이익 output |
| `CVPBaseline` | fixed_cost, unit_variable_cost, unit_price, operating_rate, target_profit | baseline CVP state |
| `CVPDelta` | unit_price_delta_pct, unit_variable_cost_delta_pct, fixed_cost_delta_pct, operating_rate_delta_pct | 4 percentage deltas |
| `CVPResult` | simulated_bep, simulated_target_profit, baseline_bep, baseline_target_profit, delta_summary | full simulation output |

**1 NEW typed exception**: `CVPInvalidInputError` with `code` attribute
for typed HTTP envelope (CR 12-5 D-14).

**Constants** (PRD §F7.1 slider bounds):
- `OPERATING_RATE_MIN = 0.5`, `OPERATING_RATE_MAX = 1.5`
- `DEFAULT_OPERATING_RATE = 1.0`, `DEFAULT_TARGET_PROFIT = 0`
- Delta bounds:
  - `PRICE_DELTA_PCT_BOUNDS = (-0.5, 0.5)` (단가·단위변동비 ±50%)
  - `FIXED_COST_DELTA_PCT_BOUNDS = (-0.3, 0.3)` (고정비 ±30%)
  - `OPERATING_RATE_DELTA_PCT_BOUNDS = (-0.5, 0.5)` (조업도 ±50%)

## 5. Service layer

`apps/api/modules/m7_simulation/services/cvp_simulation_service.py`:

```python
class CVPSimulationService:
    async def fetch_cvp_baseline(self, *, period_key: str) -> tuple[CVPBaseline, str, str]:
        """SELECT fiscal_period_snapshots (state='committed', latest)
           + products (avg unit_cost_krw) → derive CVPBaseline.

           Returns (baseline, source_period_key, fiscal_period_state).
           Raises CVPBaselineNotFoundError if no committed snapshot.

        async def simulate_cvp(self, *, baseline, delta) -> CVPResult:
            \"\"\"Delegate to pure kernel — no DB writes.\"\"\"

        async def compute(self, *, period_key, delta) -> tuple[CVPBaseline, CVPResult, str]:
            \"\"\"End-to-end: fetch + simulate.\"\"\"
```

**Data source**:
- `fiscal_period_snapshots` (latest committed for the period):
  - `fixed_cost` = `overhead_cost + material_cost` (KRW)
  - `period_key` and `state` returned for audit
- `products` (active, unit_cost_krw NOT NULL):
  - `unit_price` = `AVG(unit_cost_krw)` (round to KRW)
  - `unit_variable_cost` = `unit_price * 0.6` (PRD §F7.1 단순화)
- `operating_rate` = `DEFAULT_OPERATING_RATE` (1.0)
- `target_profit` = `DEFAULT_TARGET_PROFIT` (0)

## 6. HTTP routes

| Method | Path | Capability | Roles | Status |
|--------|------|------------|-------|--------|
| POST | `/api/v1/simulation/cvp/compute` | `CVP_SIMULATION` | owner+member+viewer+consultant_proxy | 200 / 404 / 422 / 403 |
| GET | `/api/v1/simulation/cvp/baseline` | `CVP_SIMULATION` | owner+member+viewer+consultant_proxy | 200 / 404 / 422 / 403 |

**2 NEW typed exceptions** (CR 12-5 D-14 main.py envelope handlers):
- `CVPBaselineNotFoundError` → `404 CVP_BASELINE_NOT_FOUND`
- `CVPInvalidDeltaError` → `422 CVP_INVALID_DELTA`

**Response shape** (AD-15 §1 + Decimal-as-string):
```json
{
  "baseline": {
    "fixed_cost": "8000000",
    "unit_variable_cost": "6000.0",
    "unit_price": "10000",
    "operating_rate": "1.0",
    "target_profit": "0"
  },
  "delta": {
    "unit_price_delta_pct": "0.1",
    "unit_variable_cost_delta_pct": "0",
    "fixed_cost_delta_pct": "0",
    "operating_rate_delta_pct": "0"
  },
  "result": {
    "simulated_bep": {"bep_quantity": "...", "bep_revenue": "...", ...},
    "simulated_target_profit": {"target_quantity": "...", "target_revenue": "..."},
    "baseline_bep": {...},
    "baseline_target_profit": {...},
    "delta_summary": {"unit_price_delta_pct": "0.1", ...}
  },
  "latency_ms": 12,
  "trace_id": "uuid"
}
```

## 7. Frontend (TS mirror parity)

`apps/web/lib/m7-simulation-cvp.ts` — TS re-implementation of pure kernel
math. `computeBepTS`, `applyDeltaTS`, `simulateCvpTS` produce identical
output to Python (modulo `decimal.js` rounding for displayed values).

**CR 11-4 D-001** — page.tsx `<CVPSimulationClient>` JSX actual mount MUST.
**CR 11-4 D-002** — ko-KR.json SSOT only (`apps/web/messages/ko-KR.json`,
NOT `apps/web/lib/ko-KR.json`).
**CR 11-4 D-005** — invalid delta → reject (NOT silent fall-through).
**CR 11-4 P-015** — ko-KR.json `cvp_simulation` namespace drift detector
verified by `tests/integration/test_m7_simulation_cross_language_drift.py`.

**Debouncing**: React `setTimeout` 150ms (NFR9 P95 ≤ 1초 대비 5배 여유).
Web Worker offload **honestly DEFER** (over-engineering 회피).

**Layout structure**:
```
apps/web/app/[locale]/(dashboard)/simulation/cvp/
  ├─ layout.tsx  (auth gate)
  └─ page.tsx    (RSC mounts <CVPSimulationClient>)

apps/web/components/m7-simulation/
  ├─ CVPSimulationClient.tsx (main client component)
  └─ index.ts (barrel export)
```

## 8. Performance & observability

- **Latency budget**: 150ms debounce + 10ms pure calc + 50ms React
  re-render = 210ms P95 (1초 한도 대비 5배 여유).
- **latency_ms** field in response envelope for server-side timing.
- **No audit emit** (CR 1.1 honest-DEFER — simulation is read-only).
- **NFR16 V8 determinism**: `compute_bep_hash()` for byte-identical CI
  gate; 100회 동일 입력 → 100회 동일 sha256 digest.
