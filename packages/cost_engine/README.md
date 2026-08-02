# packages/cost_engine — bizup pure cost engine

> **Story 4.1 (2026-08-02)**: `compute_period_cost(monthly_input, baseline)` introduction.

The hexagonal core: pure Python, no I/O, no clock, no random (AD-5).
Subpackages: `core/`, `ports/`, `adapters/`.

This package is the source of truth for the **1원 reconciliation** (V8
regression, verified by Story 4.4 fixtures).

## Public API

```python
from packages.cost_engine import (
    # Pure kernel
    compute_period_cost,
    Baseline,
    # I/O dataclasses (typed contracts)
    MonthlyInput,
    CalcResult,
    # Monetary primitives
    KRW,
    USD,
)
```

## File layout

```
packages/cost_engine/
├── __init__.py                                 # public API re-exports
├── pyproject.toml                              # dependencies=[] (stdlib-only)
├── core/
│   ├── money.py                                # KRW / USD NewType (AD-8)
│   └── period_cost.py                          # §6.1 8-stage 산식 체인 (Story 4.1)
├── ports/
│   ├── calc_port.py                            # CalcPort + MonthlyInput / CalcResult
│   ├── ccr_port.py                             # AD-21 CCR (consumption coefficient ratio)
│   └── reversal_port.py                        # AD-22 reversal authorization (M11 owns)
├── adapters/                                   # DB-bound, deferred
│   └── (Story 4-2 populates)
└── tests/
    └── regression_v8/                          # V8 1원 단위 골든 파일 (Story 4.4)
        ├── __init__.py                         # placeholder contract (Story 4.1)
        └── README.md                           # policy
```

## Architecture invariants

| AD | Invariant | How enforced |
|---|---|---|
| AD-1 | Hexagonal core. Ports for inbound; adapters at boundary. | import-linter contract `engine_core_to_adapters_forbidden` |
| AD-5 | Pure: no I/O, no DB, no clock, no random, no global state. | `tests/cost_engine/test_no_io_imports.py` (AST guard) |
| AD-8 | KRW = `int` (BIGINT in DB); USD = `Decimal(2dp)`; `float` forbidden. | `tests/cost_engine/test_money_purity.py` + `test_period_cost_purity.py::test_krw_types_are_int` |
| AD-11 | `core` MUST NOT import `adapters`. | import-linter contract `engine_core_to_adapters_forbidden` |
| AD-15 | snake_case; ROUND_HALF_EVEN banker's rounding. | `test_period_cost_purity.py::test_round_half_even_bankers_rounding` |
| AD-16 | `result_hash = sha256(stable_json_dumps(snapshot))` | `test_period_cost_purity.py::test_result_hash_is_64char_hex` |
| AD-22 | Engine returns `state="draft"` ONLY. Transitions owned by service layer. | `test_period_cost_purity.py::test_state_always_draft` + `test_no_io_imports.py::test_engine_state_transitions_only_draft` |

## How to add a new computation step

1. Add a new `_stageN_<name>` helper in `core/period_cost.py`.
2. Wire it in `compute_period_cost()`.
3. Add 1+ test in `tests/cost_engine/test_period_cost_purity.py`.
4. The test must be deterministic (same input → same hash).
5. Run `uv run pytest tests/cost_engine/` and `uv run ruff check packages/cost_engine/`.

## How to add a new V8 fixture (Story 4.4)

1. Drop a JSON file under `packages/cost_engine/tests/regression_v8/fixtures/`.
2. Use `V8_INPUT_SCHEMA` / `V8_GOLDEN_OUTPUT_STRUCTURE` from the placeholder.
3. Compute goldens with `banker_round_krw()` or `compute_period_cost()`.
4. Bump `V8_FIXTURE_COUNT` in `regression_v8/__init__.py`.
5. Story 4.4 will write `tests/regression_v8/test_regression_v8_fixtures.py`.

## Engine → API contract

The engine is consumed via `CalcPort` (defined in `ports/calc_port.py`).
Apps at the API boundary MUST NOT import `packages.cost_engine.core`
or `packages.cost_engine.adapters` directly — they go through the port.

```python
# ✅ Correct (port consumption)
from packages.cost_engine.ports.calc_port import CalcPort, MonthlyInput, Baseline

# ❌ Wrong (skipping the port)
from packages.cost_engine.core.period_cost import compute_period_cost
```

The single API endpoint (POST /api/v1/calc, Story 4-2) wires the port
in `apps/api/modules/m3_calculate/services/calc_orchestrator.py`.

## Capability gate

The engine itself is industry-agnostic. Industry gating is enforced at
the API boundary via `Capability.COST_CALCULATION` (granted to
manufacturing / mfg+service / mfg+service+other; service-only tenants
use Epic 9 ABC instead).

See `docs/capability-matrix.md` v1.1 for the full matrix.
