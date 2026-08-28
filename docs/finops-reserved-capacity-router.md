# FinOps Reserved Capacity Router (Phase 21)

> **Phase 21 (cj-style 151번째 wire)** — FinOps Reserved Capacity Planning territory.
> **Layer 3 P2 docs backfill (cj-style 189번째)** — Phase 21~26 carry-over sprint.

## §1. Introduction

This runbook covers the FinOps Reserved Capacity router introduced in
Phase 21 (cj-style 151번째 wire). It is the commitment-planning layer of the
FinOps chain: 5-module cross-join demand forecast, 6-tier capacity plan
selection, commitment recommendation with break-even analysis, orchestration
across the scope chain, and scheduled dispatch.

8 routes are mounted at `/api/v1/admin/finops/reserved-capacity/`.

Drift detector: `tests/api/modules/finops/test_phase_21_reserved_capacity_router.py`
(8 pytest cases).

## §2. Capability Gate

`Capability.FINOPS_RESERVED_CAPACITY_PLANNING` (`finops_reserved_capacity_planning`)
is granted to all 4 industries per CR 12-1 L4 industry-agnostic precedent.

Dependency helper: `require_finops_reserved_capacity` in
`apps/api/dependencies/capability.py`.

The router resolves the gate lazily via `_require_finops_reserved_capacity_dep()`
so it imports cleanly even before the capability matrix EXTENSION lands
(CR 12-5 D-GATE-01 inversion pattern).

Capability matrix drift detector: `tests/integration/test_capability_matrix_v1_47_drift.py`.

AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory + NFR4 PII minimization ✅ PRESERVED.

## §3. Endpoint Inventory

| Method | Path | Purpose |
|---|---|---|
| GET  | `/health` | Healthcheck — router liveness + capability echo |
| POST | `/demand-forecast` | 5-module cross-join demand forecast |
| POST | `/capacity-plan` | 6-tier capacity plan selection |
| POST | `/commitment-recommendation` | Commitment recommendation + break-even |
| POST | `/orchestrate` | Orchestrate the full scope chain for a period |
| POST | `/dispatches` | Schedule dispatch (weekly/monthly/quarterly) |
| GET  | `/cadence-preview` | Preview upcoming dispatch cadence |
| POST | `/dry-run` | Dry-run preview (no persistence) |

## §4. Request Model Contract

All 5 request models declare `ConfigDict(extra="forbid")` per CR 12-5 D-14:

- `DemandForecastRequest` — `period_key`, `industry` (default `manufacturing`),
  `five_module_inputs`, `confidence_pct` (default `80.0`), `previous_demand_krw`, `dry_run`
- `CapacityPlanRequest` — adds `demand_forecast_id`, `forecasted_demand_krw`, `override_tier`
- `CommitmentRecommendationRequest` — adds `recommended_tier` (default `1y_no_upfront`),
  `utilization_stability`, `historical_accuracy`, `savings_pct`, `commitment_term`,
  `commitment_flexibility`, `estimated_annual_savings_krw`
- `OrchestrateRequest` — `period_key`, `cadence` (default `weekly`), `scope_chain`, `dry_run`
- `ScheduleDispatchRequest` — `dispatch_schedule`, `recipient_strategy` (default
  `owner_only`), `recipient_list`

## §5. Economics Invariants

Defined in `apps/api/modules/finops/reserved_capacity/serializers.py`:

| Constant | Value | Meaning |
|---|---|---|
| `RESERVED_CAPACITY_ENGINE_MODEL_VERSION` | `1.0.0` | Engine model version stamped on every response |
| `MINIMUM_SAVINGS_PCT` | `5.0` | Recommendation floor — below this, no commitment is proposed |
| `MINIMUM_SAVINGS_KRW` | `1,000,000` | Absolute savings floor (1M KRW) |
| `MINIMUM_BREAK_EVEN_UTILIZATION_PCT` | `70.0` | Break-even utilization gate |
| `CAPACITY_HEADROOM_MIN_PCT` / `MAX_PCT` | `10.0` / `20.0` | Headroom band for tier selection |
| `HIGH_VALUE_THRESHOLD_KRW_PER_YEAR` | `10,000,000` | Owner-only + 2FA escalation threshold |

## §6. Audit Action Layer

Audit-first INSERT auto-activates on every POST endpoint (CR 1-1) — the audit
row is written before the mutation, so a failed commit still leaves the attempt
on record.

## §7. Router Include

Mounted in `apps/api/main.py` via `app.include_router(reserved_capacity_router)`,
ordered AFTER `multi_cloud_router` (Phase 20) and BEFORE
`chargeback_settlement_router` (Phase 22), matching the derivation chain.

Include smoke test: `tests/api/modules/finops/test_phase_21_26_router_include.py`.

## §8. Cross-References

- Phase 20 multi-cloud router — upstream cost reconciliation input
- Phase 22 chargeback settlement — consumes reserved capacity commitments
- Phase 26 capability matrix v1.52 EXTENSION — `FINOPS_RESERVED_CAPACITY_PLANNING` grant preserved
