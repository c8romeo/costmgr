# FinOps Chargeback Settlement Router (Phase 22)

> **Phase 22 (cj-style 160번째 wire)** — FinOps Chargeback Settlement territory.
> **Layer 3 P2 docs backfill (cj-style 189번째)** — Phase 21~26 carry-over sprint.

## §1. Introduction

This runbook covers the FinOps Chargeback Settlement router introduced in
Phase 22 (cj-style 160번째 wire). It is the settlement layer of the FinOps
chain: settlement rule CRUD, cost allocation, invoice generation, variance
reconciliation, and scheduled dispatch.

8 distinct paths (9 operations) are mounted at
`/api/v1/finops/chargeback-settlement/`.

Drift detector: `tests/api/modules/finops/test_phase_22_chargeback_settlement_router.py`
(8 pytest cases).

## §2. Capability Gate

`Capability.FINOPS_CHARGEBACK_SETTLEMENT` (`finops_chargeback_settlement`) is
granted to all 4 industries per CR 12-1 L4 industry-agnostic precedent.

Dependency helper: `require_finops_chargeback_settlement` in
`apps/api/dependencies/capability.py`.

AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory + NFR4 PII minimization ✅ PRESERVED.

## §3. Endpoint Inventory

| Method | Path | Purpose |
|---|---|---|
| GET  | `/healthcheck` | Router liveness + capability echo |
| POST | `/settlement-rules` | Create a settlement rule |
| GET  | `/settlement-rules` | List settlement rules for the tenant (RLS) |
| PUT  | `/settlement-rules/{settlement_id}` | Idempotent full update of a rule |
| POST | `/allocation` | Run cost allocation across departments |
| POST | `/invoice` | Generate a settlement invoice |
| POST | `/reconciliation` | Reconcile allocated vs invoiced amounts |
| POST | `/dispatch` | Schedule / trigger settlement dispatch |
| GET  | `/cadence-preview` | Preview upcoming dispatch cadence |

Note the collection path `/settlement-rules` carries both POST and GET; the
update operates on `/settlement-rules/{settlement_id}` and is a **PUT**
(idempotent full replace), not a PATCH.

## §4. Request Model Contract

Phase 22 endpoints accept **dict payloads** validated inside the engine layer
rather than dedicated Pydantic request models. Validation and typed-error
mapping live in `settlement_rules.py`, `allocation_engine.py`,
`invoice_generator.py`, and `reconciliation.py`.

## §5. Reconciliation Invariants

Defined in `apps/api/modules/finops/chargeback_settlement/serializers.py`:

| Constant | Value | Meaning |
|---|---|---|
| `CHARGEBACK_SETTLEMENT_ENGINE_MODEL_VERSION` | `1.0.0` | Engine model version |
| `RECONCILIATION_TOLERANCE_PCT` | `1.0` | Accepted variance band (±1.0%) |
| `RECONCILIATION_MAX_RETRIES` | `3` | Retry ceiling before escalation |
| `RECONCILIATION_AMOUNT_TOLERANCE_KRW` | `0.01` | Banker's-rounding round-off tolerance |
| `MAX_INVOICE_BYTES` | `10 MB` | Invoice artifact size ceiling |
| `MAX_ALLOCATION_LINES` | `10,000` | Allocation line-item ceiling |
| `HIGH_VALUE_THRESHOLD_KRW_PER_YEAR` | `10,000,000` | Owner-only + 2FA escalation threshold |

## §6. Audit Action Layer

Audit-first INSERT auto-activates on `/allocation`, `/invoice`,
`/reconciliation`, `/dispatch`, and both settlement-rule mutations (CR 1-1).

## §7. Router Include

Mounted in `apps/api/main.py` via
`app.include_router(chargeback_settlement_router)`, ordered AFTER
`reserved_capacity_router` (Phase 21) and BEFORE `unit_economics_router`
(Phase 23) — Phase 23 derives its per-unit costs from settlement output.

Include smoke test: `tests/api/modules/finops/test_phase_21_26_router_include.py`.

## §8. Cross-References

- Phase 21 reserved capacity — commitment amortization input to allocation
- Phase 23 unit economics — consumes `phase_22_settlement_tags` for cost-per-transaction
- Phase 26 capability matrix v1.52 EXTENSION — `FINOPS_CHARGEBACK_SETTLEMENT` grant preserved
