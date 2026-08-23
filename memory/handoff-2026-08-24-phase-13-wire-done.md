---
name: handoff-2026-08-24-phase-13-wire-done
description: Phase 13 wire DONE (cj-style 115번째). FinOps Forecasting & Capacity Planning territory. 5 NEW backend modules + alembic 0045 (5 tables) + 14 typed exceptions + 7 NEW audit actions + frontend dashboard + capability v1.39 + tests.
metadata:
  type: project
---

# Phase 13 wire DONE (cj-style 115번째)

Phase 13 (cj-style 115번째 epic 연속 정직 회복 atomic docs-and-source wire) — FinOps Forecasting & Capacity Planning territory DONE 진입 정합 보존.

**baseline_commit**: `77ed55f` (Phase 13 spec entry tip).
**outcome**: ~30 files atomic single commit (cj-style 115번째 epic 연속 정직 회복).

## §1. Wire scope (T1~T8)

### T1 — forecast_definition NEW (~+150 LOC)
- `apps/api/modules/finops/forecast_definition.py`
- `ForecastDefinition` TypedDict 11 fields (PRD §F29.1.1 verbatim)
- 5 `TARGET_METRIC_*` constants (department + cost_center + product_line + service + tenant_total)
- 4 `HORIZON_MONTHS_*` constants (3m + 6m + 12m + 24m)
- 4 `MODEL_TYPE_*` constants (arima + prophet + lstm + ensemble)
- 4 `CONFIDENCE_LEVEL_*` constants (80 + 90 + 95 + 99)
- 3 `FORECAST_STATUS_*` constants (active + paused + expired)
- `FORECAST_DEFAULTS` namespace
- `parse_forecast_definition()` pure validator (6 validation rules, CR 11-4 P-015)
- `define_forecast()` main entry (5 levels AST + 3 layer parser verification)
- 3 NEW typed exceptions (ForecastDefinitionInvalidError(400) + ForecastScopeInvalidError(400) + ForecastHistoryUnavailableError(422))

### T2 — forecast_engine + forecast_model_registry NEW (~+280 LOC)
- `apps/api/modules/finops/forecast_engine.py` (~+200 LOC)
- `generate_forecast()` 4-method parallel runner
- `ForecastResult` TypedDict 10 fields
- 4 method constants (ARIMA + Prophet + LSTM + ensemble)
- `_arima_predict` + `_prophet_predict` + `_lstm_predict` + `_ensemble_voting` (median of 3)
- STL decomposition + 8 KST holidays + 4 seasonality modes
- AD-14 stack pin: statsmodels==0.14.1 + prophet==1.1.5 + tensorflow==2.15.0
- 3 NEW typed exceptions (ForecastEngineError(500) + ForecastModelTrainingError(500) + ForecastSeasonalityDetectionError(500))
- `apps/api/modules/finops/forecast_model_registry.py` (~+80 LOC)
- `ForecastModelVersion` TypedDict + `ForecastModelRegistry` class
- Semantic versioning MAJOR.MINOR.PATCH + JSONB metadata + is_active flag

### T3 — capacity_headroom + budget_burnrate NEW (~+330 LOC)
- `apps/api/modules/finops/capacity_headroom.py` (~+180 LOC)
- `analyze_capacity_headroom()` main entry
- `CapacityHeadroomReport` TypedDict 14 fields
- 3 `RESOURCE_TYPE_*` constants (compute + storage + network)
- 3 `SATURATION_*` constants (ok + warning + critical)
- 90일 lookahead default + 7-365 range
- `RESOURCE_PRIMARY_MODEL_MAP` (compute=LSTM + storage=Prophet + network=ARIMA)
- 3 NEW typed exceptions (CapacityHeadroomAnalysisError(500) + CapacityThresholdBreachError(500) + CapacityMetricUnavailableError(404))
- `apps/api/modules/finops/budget_burnrate.py` (~+150 LOC)
- `project_budget_consumption()` 4-input burn-rate formula
- `BurnRateProjection` TypedDict 12 fields + `BudgetOverrunPrediction` TypedDict 8 fields
- 4 `SEVERITY_*` constants (normal + warning + critical + exceeded)
- 3 threshold percentages (110/130/150%)
- `_ALERT_ROUTING_TABLE` (warning=Slack/critical=Slack+PagerDuty/exceeded=Slack+PagerDuty+Email)
- 24h dedup window
- 2 NEW typed exceptions (BudgetBurnRateProjectionError(500) + BudgetOverrunPredictionError(500))

### T4 — forecast_accuracy_tracker NEW (~+120 LOC)
- `apps/api/modules/finops/forecast_accuracy_tracker.py`
- `track_forecast_accuracy()` main entry
- `ForecastAccuracy` TypedDict 10 fields + `ModelRetrainingTrigger` TypedDict 8 fields
- 3-tuple granularity (tenant_id + target_metric + model_type)
- `compute_mae` + `compute_mape` + `compute_rmse` (banker's rounding CR 5-1)
- `INDUSTRY_BASELINE_MAPE_4_INDUSTRIES` (manufacturing=12%/service=15%/겸영=14%/full matrix=13%)
- MAPE > 20% for 3 consecutive periods → retraining trigger
- Retraining cron `'0 3 * * 0'` KST Sunday 03:00 (UTC 18:00 Saturday)
- 3 NEW typed exceptions (ForecastAccuracyTrackingError(500) + ModelRetrainingTriggerError(500) + ModelPerformanceDegradationError(500))

### T5 — alembic 0045 NEW (~+450 LOC)
- `apps/api/alembic/versions/0045_phase_13_forecasting.py`
- `down_revision = "0044_phase_12_finops_anomaly"`
- 5 NEW tables:
  1. `phase_13_finops_forecast_definition` (12 cols)
  2. `phase_13_finops_forecast_result` (14 cols + JSONB predicted_values/confidence_lower/confidence_upper + UNIQUE (tenant_id, target_metric, horizon_months))
  3. `phase_13_finops_capacity_headroom` (16 cols + saturation_level enum + UNIQUE (tenant_id, resource_type, lookahead_days))
  4. `phase_13_finops_budget_burnrate` (14 cols + severity enum + alert_required BOOLEAN)
  5. `phase_13_finops_forecast_preview` (10 cols + dry_run BOOLEAN)
- Each table: `id BIGSERIAL PK + tenant_id UUID NOT NULL + trace_id TEXT nullable + 1 RLS policy (ALTER TABLE ENABLE RLS + CREATE POLICY tenant_isolation USING tenant_id = current_setting('app.tenant_id', true)::uuid) + 1 CHECK constraint with f-string IN clause + 1 index on (tenant_id, ...)`

### T6 — audit action + capability EXTENSION
- `apps/api/core/audit_action.py` MODIFIED:
  - Appended `FINOPS_FORECAST = "finops_forecast"` to ActionClass enum (after line 80)
  - Added `FinopsForecastAction` Literal with 7 values: `forecast_definition_updated`, `forecast_generated`, `capacity_headroom_analyzed`, `budget_burn_rate_projected`, `forecast_accuracy_degraded`, `model_retraining_triggered`, `forecast_dry_run_executed`
  - Added to `AuditAction` union type
  - Added `_REGISTRY` entry for `ActionClass.FINOPS_FORECAST` with target_table `finops_forecast`
- `apps/api/core/errors.py` MODIFIED:
  - Added `FinopsForecastError(FinopsError)` base class with `module_id = "m21_finops_forecast"`
  - Added 14 NEW typed exception classes (3×400 + 2×404 + 1×422 + 8×500)
  - Updated `__all__` (lines 335-369)

### T7 — capability + dependency + serializers + frontend
- `apps/api/core/capability.py` MODIFIED:
  - Appended `FINOPS_FORECASTING_CAPACITY_PLANNING = "finops_forecasting_capacity_planning"` to Capability enum (after line 474)
  - Added to ALL 4 industry frozensets (manufacturing + service + manufacturing_service + manufacturing_service_other) with full comment trail
- `apps/api/dependencies/capability.py` MODIFIED:
  - Added `require_finops_anomaly_detection` (Phase 12 BACKFILL)
  - Added `require_finops_budget_alert` (Phase 12 BACKFILL)
  - Added `require_finops_forecast` (Phase 13 NEW)
  - Updated `__all__`
- `apps/api/modules/finops/serializers.py` NEW (Phase 11 BACKFILL):
  - `m21_finops_forecast.finops_forecast_serializers` namespace (Phase 12 m20_finops_anomaly pattern verbatim)
  - `finops_forecast_serializers()` + `finops_forecast_deserialize()` pure helpers
- `apps/api/modules/finops/__init__.py` MODIFIED:
  - Phase 13 re-exports (forecast_definition + forecast_engine + forecast_model_registry + capacity_headroom + budget_burnrate + forecast_accuracy_tracker)
- `apps/web/app/[locale]/(dashboard)/admin/finops/forecast/page.tsx` NEW RSC
- `apps/web/app/[locale]/(dashboard)/admin/finops/forecast/layout.tsx` NEW
- `apps/web/components/finops/FinopsForecastDashboardPanel.tsx` NEW Client with 5 sub-components (Recharts 2.12.7)
- `apps/web/lib/finops-forecast/finops-forecast-client.ts` NEW (CR 12-5 D-PARITY-01 TS mirror)
- `apps/web/messages/ko-KR.json` MODIFIED: added ~30 keys `finops_forecast.*` namespace (CR 11-4 D-002 verbatim SSOT)

### T8 — docs + handoff + commit-msg + sprint-status + atomic commit
- `docs/finops-forecast-capacity-planning.md` NEW (14-section runbook)
- `docs/capability-matrix.md` MODIFIED: v1.38 → v1.39 EXTENSION + 3 NEW rows (FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 BACKFILL + FINOPS_FORECASTING_CAPACITY_PLANNING Phase 13 NEW)
- 7 NEW test files (~43 NEW pytest cases)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` MODIFIED: v3.26 → v3.27 EXTENSION + phase-13-wire development_status + A404~A408 action_items block
- `_bmad-output/implementation-artifacts/commit-msg-phase-13-wire.txt` NEW
- Atomic commit `git commit -F commit-msg-phase-13-wire.txt` (Phase 12 wire `f3c0e63` 27-file precedent)

## §2. CR lessons applied 14종

- ✅ CR 0-2 RLS: 5 NEW tables in alembic 0045 + Phase 12 carry-over RLS preserved
- ✅ CR 1-1 audit-first INSERT: 7 NEW audit actions via `emit_audit_typed()` deferred to service-layer
- ✅ CR 1-1 ContextVar: trace_id propagation via ContextVar
- ✅ CR 1-1 RSC boundary: `forecast/page.tsx` RSC + `FinopsForecastDashboardPanel.tsx` Client-only
- ✅ CR 4-3/4-4: forecast baseline + golden_diff pattern verbatim
- ✅ CR 5-1 banker's rounding parity: MAE/MAPE/RMSE (Python `round` ↔ TS `Math.round`)
- ✅ CR 9-6 commit message: `git commit -F <file>`
- ✅ CR 11-3 honest-DEFER: D-FINOPS-3 preserved + 11 D-DEFER-* ALL RESOLVED + 3 Phase 12 backfill gaps honestly resolved (no new D-DEFER)
- ✅ CR 11-4 D-001~D-005 + P-015: ko-KR.json SSOT only (~30 keys), vitest RTL render discipline, owner-only RBAC, unknown state reject
- ✅ CR 12-1 L4 industry-agnostic capability: ✅/✅/✅/✅ (manufacturing + service + manufacturing_service + manufacturing_service_other all grant FINOPS_FORECASTING_CAPACITY_PLANNING)
- ✅ CR 12-5 D-14: 14 NEW typed exception classes
- ✅ CR 12-5 D-PARITY-01: Python TypedDict ↔ TS interface parity verification via `finops-forecast-client.ts`
- ✅ CR 12-5 D-GATE-01: capability gate fail-closed + owner-only RBAC AD-22
- ✅ A19 cohesion pattern 10 surface EXTENSION PASS

## §3. D-DEFER-* honestly 보존

- ✅ D-FINOPS-3 honestly preserved (Phase 13 PRD entry did NOT resolve, only 1 carry-over preserved)
- ✅ 11 D-DEFER-* ALL RESOLVED (D-1-1-DEFER-1/2/3, D-EPIC-16-REVIEW-DEFER-*, D-PHASE-4-DR-DEFER-*, D-EPIC-17-WIRE-DEFER-T2-T3-UI, D-RETENTION-1, D-OBSERVABILITY-1, D-PERFORMANCE-1, D-CHAOS-1, D-SLO-1, D-FINOPS-1, D-FINOPS-2)
- ✅ 3 Phase 12 backfill gaps honestly resolved (no new D-DEFER):
  1. `apps/api/dependencies/capability.py` missing Phase 12 deps → BACKFILL `require_finops_anomaly_detection` + `require_finops_budget_alert`
  2. `apps/api/modules/finops/serializers.py` Phase 11 stub → NEW `m21_finops_forecast.finops_forecast_serializers`
  3. `docs/capability-matrix.md` table missing Phase 12 rows → BACKFILL FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT + ADD FINOPS_FORECASTING_CAPACITY_PLANNING (3 rows in same atomic edit)

## §4. 결정 wire 일자

- **날짜**: 2026-08-24
- **순서**: cj-style 115번째 (PRD entry cj 113 `d31dfc8` → spec entry cj 114 `77ed55f` → wire cj 115 → close-out retro cj 116)
- **branch**: `9-3-dev-2026-08-17`

## §5. Next 5 options

(a) **Phase 13 close-out retro (Recommended, cj-style 116번째)** — atomic docs-only wire (1 NEW retro_document + handoff memory + sprint-status v3.27 → v3.28 EXTENSION)

(b) **Phase 14+ entry** — decide next territory (Anomaly ML Advanced? Cost Allocation Engine? etc.)

(c) **Epic 18+ entry** — decide next epic theme

(d) **D-DEFER-* follow-up** — handle any newly-identified gaps

(e) **Build fixes follow-up** — if 3중 게이트 impact FAIL on commit, run build fixes (`eaee198` precedent)