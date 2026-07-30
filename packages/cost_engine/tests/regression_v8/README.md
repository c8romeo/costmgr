# V8 Regression Suite

> Placeholder for the V8 cost-engine regression fixtures (Story 4.4 will fill
> this directory).

---

## What is V8?

V8 is the **8th verification layer** in the costmgr verification chain
(see ARCHITECTURE-SPINE.md §Verification). It captures the
**1원 reconciliation contract** — for any input that has a published
expected output, the cost engine must produce that output exactly, in KRW
integer units, across all 8 verification layers (V1–V8).

V8 fixtures are **golden output snapshots** that encode:
- Input: a normalized monthly state (M1 + M2 input streams)
- Expected: the computed cost breakdown, unit-cost, and BOM result
- Tolerance: 0 KRW (exact match — no rounding tolerance)

---

## When V8 must run

**Any pinned-version bump** requires running the V8 suite. See
[`docs/STACK_PIN.md`](../../../../docs/STACK_PIN.md) for the full policy.

| Trigger                                | V8 required? |
| -------------------------------------- | ------------ |
| Patch update of unpinned transitive   | No           |
| Bump pinned package (`[STACK BUMP]`)  | **Yes**      |
| Change to cost_engine core/            | **Yes**      |
| Change to cost_engine adapters/        | **Yes**      |
| Change to V8 fixture itself            | **Yes**      |
| Refactor only (no version change)      | Recommended  |

---

## How to run (when implemented)

```bash
# Full suite
uv run pytest packages/cost_engine/tests/regression_v8 -v

# Update golden output after an intentional change
uv run pytest packages/cost_engine/tests/regression_v8 -v --update-golden
```

---

## Status

**Story 0.3** documents the policy and creates the directory.

**Story 4.4** will:
- Add the first batch of golden fixtures (food-service BOM, 3-product matrix).
- Wire `packages/cost_engine/tests/regression_v8/` into CI as a required
  gate on `stack-pin`-labelled PRs.
- Add `--update-golden` CLI flag to the pytest plugin.

Until then, this directory contains only this README. Running the test
path returns `no tests ran`.