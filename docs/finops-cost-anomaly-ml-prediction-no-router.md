# FinOps Cost Anomaly ML Prediction — No-Router Territory (Phase 26)

> **Phase 26 (cj-style 179~187 wires)** — FinOps Cost Anomaly ML Prediction territory.
> **Layer 3 P2 docs backfill (cj-style 189번째)** — Phase 21~26 carry-over sprint.

## §1. Why this document exists

The Phase 21~26 Layer 3 docs backfill produces one router runbook per territory.
Phase 26 is the exception: **it ships no FastAPI router.** This document records
that absence deliberately, so a future reader does not mistake a missing
`docs/finops-cost-anomaly-ml-prediction-router.md` for an unfinished backfill.

Pinned by `test_phase_26_cost_anomaly_ml_prediction_has_no_router` in
`tests/api/modules/finops/test_phase_21_26_router_include.py`, which asserts
that no module under `apps/api/modules/finops/cost_anomaly_ml_prediction/`
constructs an `APIRouter` and that `apps/api/main.py` does not reference the
package.

## §2. What the territory does ship

`apps/api/modules/finops/cost_anomaly_ml_prediction/`:

| Module | Role |
|---|---|
| `anomaly_ml_prediction_engine.py` | Prediction orchestration |
| `anomaly_ml_model_registry.py` | Model registry + artifact checksums |
| `anomaly_ml_training_pipeline.py` | Training job lifecycle |
| `anomaly_ml_scoring.py` | Inference + feature extraction |
| `anomaly_ml_ensemble_consensus.py` | 5-model ensemble consensus |
| `scheduled_cost_anomaly_ml_prediction_jobs.py` | Scheduled dispatch |
| `serializers.py` | Typed serializers + constants |

The territory is consumed by the Next.js dashboard rather than by HTTP clients:
`apps/web/lib/finops/cost-anomaly-ml-prediction-{types,client}.ts` and the five
components under `apps/web/components/finops/cost-anomaly-ml-prediction/`.

## §3. Capability Gate

`Capability.FINOPS_COST_ANOMALY_ML_PREDICTION` (`finops_cost_anomaly_ml_prediction`)
is granted to all 4 industries (capability matrix v1.52).

Dependency helper `require_finops_cost_anomaly_ml_prediction` exists in
`apps/api/dependencies/capability.py` — it is wired ahead of any router, so a
future router wire needs no capability work.

Drift detector: `tests/integration/test_capability_matrix_v1_52_drift.py` (12 cases).

## §4. Typed Exceptions

16 typed exception subclasses under `FinopsCostAnomalyMLPredictionError`
(module id `m34_finops_cost_anomaly_ml_prediction`) in `apps/api/core/errors.py`,
in four groups: prediction core (3), model registry (4), training pipeline (4),
ML scoring (5).

Drift detector:
`tests/api/core/test_phase_26_cost_anomaly_ml_prediction_typed_exceptions.py` (26 cases).

## §5. Existing test coverage

| Layer | File | Cases |
|---|---|---|
| Typed exceptions | `tests/api/core/test_phase_26_cost_anomaly_ml_prediction_typed_exceptions.py` | 26 |
| Capability matrix | `tests/integration/test_capability_matrix_v1_52_drift.py` | 12 |
| Frontend | `apps/web/__tests__/finops/cost-anomaly-ml-prediction-dashboard.test.tsx` | 28 |
| No-router pin | `tests/api/modules/finops/test_phase_21_26_router_include.py` (Test 6) | 1 |

## §6. If a router is added later

A Phase 26 router wire would need, in order: the routes module, an
`app.include_router()` call in `apps/api/main.py` after
`vendor_management_router`, an update to Test 6 above (which will fail loudly —
by design), a router drift test mirroring Phase 21~25, and a replacement of this
document with a standard router runbook.

## §7. Cross-References

- Phase 12 anomaly detection — rule-based layer this territory pre-empts
- Phase 25 vendor management — last router in the Phase 21~25 include block
- Capability matrix v1.52 EXTENSION `7357139` (cj-style 185번째)
- Dashboard UI sprint `fbc6f42` (cj-style 186번째) + vitest sprint `2dd9744` (cj-style 187번째)
