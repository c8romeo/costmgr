# FinOps Unit Economics Router (Phase 23)

> **Phase 23 (cj-style 164번째 wire)** — FinOps Unit Economics territory.
> **Layer 3 P2 docs backfill (cj-style 189번째)** — Phase 21~26 carry-over sprint.

## §1. Introduction

This runbook covers the FinOps Unit Economics router introduced in
Phase 23 (cj-style 164번째 wire). It converts allocated cost into per-unit
economics: cost per business unit, cost per transaction, margin analysis, and
trend tracking.

9 routes are mounted at `/api/v1/finops/unit-economics/`.

Drift detector: `tests/api/modules/finops/test_phase_23_unit_economics_router.py`
(8 pytest cases).

## §2. Capability Gate

`Capability.FINOPS_UNIT_ECONOMICS` (`finops_unit_economics`) is granted to all
4 industries per CR 12-1 L4 industry-agnostic precedent.

Dependency helper: `require_finops_unit_economics` in
`apps/api/dependencies/capability.py`.

AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory + NFR4 PII minimization ✅ PRESERVED.

## §3. Endpoint Inventory

| Method | Path | Purpose |
|---|---|---|
| GET  | `/healthcheck` | Router liveness + capability echo |
| POST | `/compute` | Compute the full unit-economics bundle for a period |
| POST | `/cost-per-business-unit` | Cost per business unit |
| POST | `/cost-per-transaction` | Cost per transaction (uses `phase_22_settlement_tags`) |
| POST | `/margin-analysis` | Margin band classification |
| POST | `/dry-run` | Dry-run preview (no persistence) |
| GET  | `/trend` | Historical unit-economics trend |
| POST | `/calculation` | Trigger a scheduled calculation run |
| GET  | `/cadence-preview` | Preview upcoming calculation cadence |

All routes declare `response_model=None` — responses are typed dicts assembled
by the serializer layer rather than Pydantic response models.

## §4. Request Model Contract

Phase 23 endpoints accept **dict payloads**; validation lives in
`unit_economics_engine.py`, `cost_per_business_unit.py`,
`cost_per_transaction.py`, and `margin_analysis.py`.

`/cost-per-transaction` reads `phase_22_settlement_tags` from the payload,
which is the explicit hand-off point from the Phase 22 settlement layer.

## §5. Margin Bands and Caps

Defined in `apps/api/modules/finops/unit_economics/serializers.py`:

| Constant | Value | Meaning |
|---|---|---|
| `UNIT_ECONOMICS_ENGINE_MODEL_VERSION` | `1.0.0` | Engine model version |
| `MARGIN_HEALTHY_THRESHOLD_PCT` | `30.0` | ≥30% → healthy |
| `MARGIN_WARNING_THRESHOLD_PCT` | `15.0` | 15~30% → warning |
| `MARGIN_CRITICAL_THRESHOLD_PCT` | `15.0` | <15% → critical |
| `MARGIN_NEGATIVE_PCT` | `0.0` | <0% → negative (alert + Epic 12 2FA) |
| `MAX_BUSINESS_UNITS_PER_TENANT` | `1,000` | Tenant scale cap |
| `MAX_TRANSACTIONS_PER_PERIOD` | `100,000` | Per-period transaction cap |
| `MAX_COST_PER_X_OVERRIDE_KRW` | `10,000,000` | Override requires owner 2FA |

The band ordering `healthy > warning ≥ critical > negative` is pinned by the
drift detector so a threshold edit cannot silently invert the classification.

## §6. Audit Action Layer

Audit-first INSERT auto-activates on every POST endpoint (CR 1-1).

## §7. Router Include

Mounted in `apps/api/main.py` via `app.include_router(unit_economics_router)`,
ordered AFTER `chargeback_settlement_router` (Phase 22) — Phase 23 derives from
settlement output — and BEFORE `budget_planning_router` (Phase 24).

Include smoke test: `tests/api/modules/finops/test_phase_21_26_router_include.py`.

## §8. Cross-References

- Phase 19 pricing router — rate-card input to per-unit cost
- Phase 22 chargeback settlement — `phase_22_settlement_tags` hand-off
- Phase 24 budget planning — consumes unit economics for plan-vs-actual
- Phase 26 capability matrix v1.52 EXTENSION — `FINOPS_UNIT_ECONOMICS` grant preserved
