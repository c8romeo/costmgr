# FinOps Budget Planning Router (Phase 24)

> **Phase 24 wire** — FinOps Budget Planning territory.
> **Layer 3 P2 docs backfill (cj-style 189번째)** — Phase 21~26 carry-over sprint.

## §1. Introduction

This runbook covers the FinOps Budget Planning router. It is the plan-and-approve
layer of the FinOps chain: budget plan CRUD, dimension allocation, a multi-step
approval workflow, budget-vs-actual variance, and threshold alerts.

7 distinct paths (9 operations) are mounted at `/finops/budget-planning/`.

Drift detector: `tests/api/modules/finops/test_phase_24_budget_planning_router.py`
(8 pytest cases).

## §2. Capability Gate

`Capability.FINOPS_BUDGET_PLANNING` (`finops_budget_planning`) is granted to all
4 industries per CR 12-1 L4 industry-agnostic precedent.

Dependency helper: `require_finops_budget_planning` in
`apps/api/dependencies/capability.py`.

AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory + NFR4 PII minimization ✅ PRESERVED.

## §3. Endpoint Inventory

| Method | Path | Purpose |
|---|---|---|
| POST  | `/plans` | Create a budget plan |
| GET   | `/plans` | List budget plans for the tenant (RLS) |
| GET   | `/plans/{plan_id}` | Read one plan |
| PATCH | `/plans/{plan_id}` | Partial update of a plan |
| POST  | `/plans/{plan_id}/allocate` | Allocate the plan across dimensions |
| POST  | `/plans/{plan_id}/submit-approval` | Submit the plan into the approval chain |
| POST  | `/plans/{plan_id}/approve-step` | Approve one step of the chain |
| POST  | `/plans/{plan_id}/vs-actual` | Compute budget-vs-actual variance |
| POST  | `/plans/{plan_id}/alerts/trigger` | Trigger threshold alerts |

The plan detail path is a **PATCH** (partial update), not a PUT — the drift
detector asserts the absence of PUT so a semantics change is explicit.

Note the prefix has no `/api/v1` segment: it is `/finops/budget-planning`,
unlike Phase 22/23 (`/api/v1/finops/...`) and Phase 21 (`/api/v1/admin/finops/...`).
This is existing, pinned behaviour; normalizing prefixes would be a separate
routing sprint.

## §4. Request Model Contract

Phase 24 endpoints accept **dict payloads** with query parameters via
`fastapi.Query`; validation and lifecycle transitions live in
`budget_plan_engine.py`, `budget_allocation.py`,
`budget_approval_workflow.py`, `budget_vs_actual.py`, and `budget_alert.py`.

## §5. Budget Bands and Caps

Defined in `apps/api/modules/finops/budget_planning/serializers.py`:

| Constant | Value | Meaning |
|---|---|---|
| `BUDGET_PLANNING_ENGINE_MODEL_VERSION` | `1.0.0` | Engine model version |
| `BUDGET_WARNING_THRESHOLD_PCT` | `10.0` | ≥10% over → warning |
| `BUDGET_CRITICAL_THRESHOLD_PCT` | `25.0` | ≥25% over → critical + escalation |
| `MAX_BUDGET_PLANS_PER_TENANT` | `1,000` | Tenant scale cap |
| `MAX_ALLOCATIONS_PER_PLAN` | `100,000` | Allocation line ceiling |
| `MAX_BUDGET_OVERRIDE_KRW` | `10,000,000` | Override requires owner 2FA |
| `TOTAL_VERIFICATION_TOLERANCE_KRW` | `0.01` | Allocation-sum tolerance (±0.01 KRW) |

Enum frozensets — `ALL_BUDGET_PLAN_PERIOD_TYPES`, `ALL_BUDGET_PLAN_LIFECYCLES`,
`ALL_BUDGET_PLAN_DRY_RUN_MODES`, `ALL_BUDGET_APPROVAL_STEP_STATUSES`,
`ALL_BUDGET_ALERT_SEVERITIES`, `ALL_BUDGET_PLAN_DIMENSIONS` — back the
lifecycle and alert-severity validation, each with a `*_VALUES` alias.

## §6. Audit Action Layer

Audit-first INSERT auto-activates on plan creation, allocation, both approval
endpoints, variance computation, and alert triggering (CR 1-1). The approval
chain writes one audit row per step so a partially-approved plan is fully
reconstructible.

## §7. Router Include

Mounted in `apps/api/main.py` via `app.include_router(budget_planning_router)`,
ordered AFTER `unit_economics_router` (Phase 23) — Phase 24 derives from unit
economics — and BEFORE `vendor_management_router` (Phase 25).

Include smoke test: `tests/api/modules/finops/test_phase_21_26_router_include.py`.

## §8. Cross-References

- Phase 23 unit economics — per-unit input to plan-vs-actual
- Phase 25 vendor management — contract `budget_ceiling_krw` checked against plans
- Phase 26 capability matrix v1.52 EXTENSION — `FINOPS_BUDGET_PLANNING` grant preserved
- Typed exception `apps/api/core/errors.py:3153` — raised by `get_budget_plan_endpoint()`
