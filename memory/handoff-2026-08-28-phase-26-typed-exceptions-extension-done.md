# Phase 26 typed exceptions EXTENSION sprint handoff (cj-style 184번째 결정 wire 진입 완료)

**Date**: 2026-08-28 (KST)
**Sprint ID**: cj-style 184번째
**Sprint Type**: source-and-test wire (CR 12-5 D-14 typed exception envelope EXTENSION)
**Baseline commit**: `725acde` (Phase 26 audit_action EXTENSION cj-style 183번째 tip)

## Sprint Scope Summary

Phase 26 typed exceptions EXTENSION DONE — 16 NEW typed exception classes CR 12-5 D-14 envelope
applied to Phase 26 ML-driven pre-detection layer (FINOPS_COST_ANOMALY_ML_PREDICTION territory),
complementary to Phase 12 rule-based 사후 detection (FINOPS_ANOMALY_DETECTION territory).

## Files Changed (6 files = 3 NEW + 3 MODIFIED atomic single sprint)

| # | File | Action | LOC |
|---|------|--------|-----|
| 1 | `apps/api/core/errors.py` | MODIFIED | +260 |
| 2 | `tests/api/core/test_phase_26_cost_anomaly_ml_prediction_typed_exceptions.py` | NEW | +370 |
| 3 | `_bmad-output/implementation-artifacts/sprint-status.yaml` | MODIFIED | +12 entries |
| 4 | `_bmad-output/implementation-artifacts/commit-msg-cj-184.txt` | NEW | (this file's parent) |
| 5 | `memory/handoff-2026-08-28-phase-26-typed-exceptions-extension-done.md` | NEW | (this file) |
| 6 | `memory/MEMORY.md` | MODIFIED | (hook EXTENSION) |

## 16 NEW Typed Exception Classes

### Group 1: Cost Anomaly ML Prediction core (3 NEW)
- `AnomalyMLPredictionNotFoundError` (HTTP 404) — PRD §F42.4 lifecycle
- `AnomalyMLPredictionStatusTransitionError` (HTTP 400) — lifecycle invariants
- `AnomalyMLPredictionComplianceViolationError` (HTTP 403) — AD-55 (g) Epic 12 2FA 챌린지

### Group 2: Model Registry (4 NEW)
- `ModelRegistryEntryNotFoundError` (HTTP 404) — semver 0.1.0, AD-55 (b)
- `ModelArtifactChecksumMismatchError` (HTTP 422) — artifact integrity, AD-55 (b)
- `ModelStatusTransitionError` (HTTP 400) — 5 lifecycle states, AD-55 (b)
- `ModelArtifactSizeError` (HTTP 413) — 100 MB max, AD-55 (b)

### Group 3: Model Training Pipeline (4 NEW)
- `ModelTrainingJobNotFoundError` (HTTP 404) — AD-55 (c)
- `ModelTrainingFailedError` (HTTP 500) — 5 model types ensemble, AD-55 (c)
- `ModelTrainingDataInsufficientError` (HTTP 422) — 8 features × 300 days, AD-55 (c)
- `ModelTrainingTimeoutError` (HTTP 504) — 3600s timeout, AD-55 (c)

### Group 4: Anomaly ML Scoring (5 NEW)
- `AnomalyMLScoringError` (HTTP 500) — 3-attempt retry, AD-55 (d)
- `AnomalyMLInferenceTimeoutError` (HTTP 504) — 200ms P95, AD-55 (d)
- `AnomalyMLFeatureExtractionError` (HTTP 422) — 8 features, AD-55 (c)
- `AnomalyMLComparisonError` (HTTP 500) — AnomalyScoreComparison 12 fields, AD-55 (d)
- `AnomalyMLEnsembleConsensusError` (HTTP 500) — 5 model types ensemble, AD-55 (a)

## Module Identifier

`FINOPS_COST_ANOMALY_ML_PREDICTION_MODULE_ID = "m34_finops_cost_anomaly_ml_prediction"`

Inheritance chain: `BaseError` → `FinopsError` → `FinopsCostAnomalyMLPredictionError` → 16 NEW subclasses.

## 3중 게이트 (3-level gate) Result

| Gate | Status |
|------|--------|
| ruff scoped | ✅ All checks passed! (after I001 auto-fix + PT017 pytest.raises refactor) |
| pytest | ✅ 26/26 NEW PASS + 12/12 Phase 26 audit_action regression + 24/24 Phase 26 universal = 62/62 PASS |
| vitest | N/A (backend only) |
| tsc | N/A (backend only) |

**3중 게이트 pytest PASS + ruff PASS** 결정 wire + A19 cohesion 9 surface EXTENSION PARTIAL preserved
(Phase 26 typed exceptions EXTENSION sprint 는 Surface 4 typed exceptions EXTENSION 만, 나머지 8 surface NO 변경).

## Honest Deviations (3건 보존)

1. **capability matrix v1.52 EXTENSION honestly DEFER** — FINOPS_COST_ANOMALY_ML_PREDICTION capability wiring 변경은 다음 sprint honestly DEFER
2. **dashboard UI 5 sub-components honestly DEFER** — frontend Layer 변경은 별도 sprint honestly DEFER
3. **vitest 28 frontend tests honestly DEFER** — backend pytest 26/26 PASS 보존

## A741~A745 결정 wire

- A741: 옵션 (a) Phase 26 typed exceptions EXTENSION sprint 진입 결정 wire (rationale 5종)
- A742: 6 files = 3 NEW + 3 MODIFIED atomic single sprint
- A743: 26 NEW pytest cases verbatim 결정 wire + 16 NEW typed exception classes
- A744: CR 11-3 honest-DEFER 75번째 + CR lessons applied 19종 + D-FINOPS-15 honestly DEFER 보존
- A745: sprint-status v3.91 → v3.92 + atomic commit via `git commit -F <file>`

## Phase 26 Wire Cycle (5-entry-point chain ALL DONE)

| Sprint | cj-style | Commit | Scope |
|--------|----------|--------|-------|
| PRD entry | 179 | `b95ebc3` | 7 files = 3 NEW + 4 MODIFIED (docs only) |
| spec entry | 180 | `36efc71` | 5 files = 3 NEW + 2 MODIFIED (docs only) |
| atomic wire | 181 | `0cf2547` | 16 files = 13 NEW + 3 MODIFIED (source/test) |
| close-out retro | 182 | `ca78862` | 5 files = 3 NEW + 2 MODIFIED (docs only) |
| audit_action EXTENSION | 183 | `725acde` | 6 files = 3 NEW + 3 MODIFIED (source/test) |
| **typed exceptions EXTENSION** | **184** | **pending** | **6 files = 3 NEW + 3 MODIFIED (source/test)** |

## Next unblocked 결정 wire 보류

- 옵션 (a) Phase 26 capability matrix v1.52 EXTENSION sprint 진입 결정 wire (cj-style 185번째)
- 옵션 (b) Phase 26 dashboard UI sprint 진입 결정 wire (cj-style 185번째)
- 옵션 (c) Phase 26 vitest frontend test sprint 진입 결정 wire (cj-style 185번째)
- 옵션 (d) Layer 2 P1 + Layer 3 P2 carry-over sprint 진입
- 옵션 (e) Epic 27+ 진입 결정 wire
- 옵션 (f) D-DEFER-* follow-up 결정 wire 보류

## Cross-References

- Phase 26 PRD entry handoff: `memory/handoff-2026-08-28-phase-26-prd-entry-done.md`
- Phase 26 spec entry handoff: `memory/handoff-2026-08-28-phase-26-spec-entry-done.md`
- Phase 26 atomic wire handoff: `memory/handoff-2026-08-28-phase-26-wire-cycle-end.md`
- Phase 26 close-out retro handoff: `memory/handoff-2026-08-28-phase-26-close-out-retro-done.md`
- Phase 26 audit_action EXTENSION handoff: `memory/handoff-2026-08-28-phase-26-audit-action-extension-done.md`
- AD-55: `docs/architecture-decisions/AD-55-phase-26-finops-cost-anomaly-ml-prediction.md`

결정 wire 일자: 2026-08-28 (KST)