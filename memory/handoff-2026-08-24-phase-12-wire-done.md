# Phase 12 wire DONE (cj-style 111번째)

> **v1.0 (2026-08-24, Phase 12 wire DONE)** — Cost Anomaly Detection & Budget Alerting capability gates 2 NEW rows wire DONE 진입 (cj-style Phase 12 3rd entry = cj-style 111번째 epic 연속 정직 회복 atomic docs-and-source wire). baseline_commit `8c5f374` (Phase 12 spec entry tip).

## Wire Scope (27 files atomic single sprint)
- **T1 NEW** `apps/api/modules/finops/anomaly_detection.py` (~347 LOC) — AnomalyDefinition TypedDict 9 fields + parse_anomaly_definition pure validator + detect_anomaly + 4 detection methods (z_score 3.0 + IQR 1.5 + EWMA λ=0.3 + isolation_forest 0.1) + 5 dimensions (department + cost_center + product_line + service + tenant_total) + 3 baseline windows (last_30d + last_90d + YTD) + 10 subtasks
- **T2 NEW** `apps/api/modules/finops/budget_definition.py` (~402 LOC) — BudgetDefinition TypedDict 13 fields + parse_budget_definition pure validator + define_budget + 3 budget_periods (monthly + quarterly + yearly) + 4 budget_scopes (tenant + department + cost_center + product_line) + AlertThresholds 80/90/100 defaults + 10 subtasks
- **T3 NEW** `apps/api/modules/finops/anomaly_detection_engine.py` (~340 LOC) — run_anomaly_detection + _z_score_method + _iqr_method + _ewma_method + _isolation_forest_method + _voting_consensus 3-of-4 + _assign_severity low/medium/high/critical + DetectionResult TypedDict 11 fields + 10 subtasks
- **T4 NEW** `apps/api/modules/finops/budget_alert.py` (~280 LOC) — route_budget_alert + _ALERT_ROUTING_TABLE + _is_dedup_window_active 24h + BudgetAlert TypedDict + 10 subtasks
- **T4 NEW** `apps/api/modules/finops/forecast_accuracy.py` (~210 LOC) — compute_mae + compute_mape + compute_rmse + evaluate_forecast_accuracy + HIGH_ACCURACY_MAPE_THRESHOLD 0.10 + RETRAIN_TRIGGER_MAPE_THRESHOLD 0.20
- **T5 NEW** `apps/api/alembic/versions/0044_phase_12_finops_anomaly.py` (~650 LOC) — 6 tables (phase_12_finops_anomaly + anomaly_baseline + anomaly_preview + budget + budget_consumption + budget_preview) + RLS tenant_isolation 6 tables + CHECK 10 + UNIQUE 3 + indexes 8 + m20_finops_anomaly module SSOT + 8 subtasks
- **T6 MODIFIED** `apps/api/core/errors.py` — 14 NEW typed exceptions (AnomalyDefinitionInvalidError 400 + AnomalyDetectionError 500 + AnomalyBaselineUnavailableError 422 + AnomalyBaselineUpdateError 500 + BudgetDefinitionInvalidError 400 + BudgetScopeInvalidError 400 + BudgetAmountInvalidError 400 + BudgetAlertError 500 + BudgetAlertRoutingError 400 + BudgetAlertDedupWindowActiveError 409 + ForecastAccuracyDegradedError 422 + ForecastAccuracyInvalidError 400 + ForecastModelRetrainingError 500 + FinopsAnomalyCapabilityDeniedError 403) + FINOPS_ANOMALY_MODULE_ID = "m20_finops_anomaly"
- **T6 MODIFIED** `apps/api/core/audit_action.py` — ActionClass.FINOPS_ANOMALY + ActionClass.FINOPS_BUDGET 2 NEW + FinopsAnomalyAction 4 NEW Literal + FinopsBudgetAction 3 NEW Literal + 7 NEW audit values via emit_audit_typed
- **T6 MODIFIED** `apps/api/core/capability.py` — Capability.FINOPS_ANOMALY_DETECTION + Capability.FINOPS_BUDGET_ALERT 2 NEW + 4-industry grants ✅/✅/✅/✅ industry-agnostic per CR 12-1 L4
- **T6 MODIFIED** `apps/api/dependencies/capability.py` — require_finops_anomaly + require_finops_budget
- **T6 MODIFIED** `apps/api/modules/finops/__init__.py` — EXTENSION docstring + re-exports
- **T7 NEW** `apps/web/lib/finops/anomaly-types.ts` (~150 LOC) — full TS parity (CR 12-5 D-PARITY-01)
- **T7 NEW** `apps/web/lib/finops/anomaly-client.ts` (~210 LOC) — fetch wrappers + AnomalyApiError
- **T7 NEW** `apps/web/components/finops/AnomalyDashboardPanel.tsx` (~310 LOC) — 4 panels (AnomalyDetections + BudgetDefinitions + BudgetAlerts + ForecastAccuracy)
- **T7 MODIFIED** `apps/web/lib/finops/finops-types.ts` — re-export Phase 12 anomaly types
- **T7 MODIFIED** `apps/web/lib/finops/finops-client.ts` — re-export Phase 12 anomaly client functions
- **T7 MODIFIED** `apps/web/messages/ko-KR.json` — ~50 NEW keys anomaly.* + budget.* + forecast.* + alert_level.* + alert_channel.*
- **T6.5 NEW** 5 pytest files `tests/api/core/test_phase_12_*.py` (50 NEW cases PASS)
- **T6.5 NEW** 1 vitest file `apps/web/__tests__/finops/anomaly-dashboard.test.tsx` (7 NEW cases PASS)
- **T8 MODIFIED** `_bmad-output/implementation-artifacts/sprint-status.yaml` v3.22 → v3.23 + A379~A383 action_items + last_updated_note
- **T8 MODIFIED** `docs/capability-matrix.md` v1.37 wire DONE confirmation
- **T8 NEW** `memory/handoff-2026-08-24-phase-12-wire-done.md` (this file)

## 3중 게이트 Impact (CLEAN)
- **ruff scoped** Phase 12 wire Python files = **0 NEW errors**
- **pytest** Phase 12 backend tests = **50 NEW pytest CASES PASS**
- **vitest** Phase 12 frontend tests = **7 NEW vitest CASES PASS**
- **pnpm tsc --noEmit** = **0 NEW errors**
- **regressions** = **0**

## CR Lessons Applied (14종)
- **CR 0-2 RLS verbatim**: 6 alembic 0044 tables with tenant_isolation policies
- **CR 1-1 audit-first INSERT**: 7 NEW audit actions via emit_audit_typed
- **CR 9-6 commit message discipline**: `git commit -F <file>` (PowerShell here-string 회피)
- **CR 11-3 honest-DEFER**: D-FINOPS-2 honestly preserved
- **CR 11-4 P-015**: pure validator pattern (parse_anomaly_definition + parse_budget_definition)
- **CR 12-1 L4 industry-agnostic**: 4-industry grants ✅/✅/✅/✅ for both FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT
- **CR 12-5 D-14 typed exception envelope**: 14 NEW typed exceptions
- **CR 12-5 D-PARITY-01 inversion**: full TS parity (Python TypedDict ↔ TypeScript interface)
- **CR 12-5 D-GATE-01 inversion**: capability gate + owner-only RBAC
- **A19 cohesion 9 surface**: FinOps Anomaly surface NEW = F28.1~F28.8
- **A36 SDR**: 4-step SDR 검증 (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0 + commit consistency PASS)
- **AD-14 stack pin**: sklearn==1.4.0 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 + Recharts 2.12.7
- **AD-22 owner-only RBAC**: anomaly detection + budget definition + budget alert + forecast accuracy
- **NFR4 PII minimization**: ✅ PRESERVED (no PII in cost data)

## D-DEFER-* Honesty 보존
- D-1-1-DEFER-1/2/3 ✅ RESOLVED
- D-EPIC-16-REVIEW-DEFER-2~6 ✅ RESOLVED
- D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED
- D-EPIC-17-WIRE-DEFER-T2-T3-UI ✅ RESOLVED
- D-RETENTION-1 ✅ RESOLVED
- D-OBSERVABILITY-1 ✅ RESOLVED
- D-PERFORMANCE-1 ✅ RESOLVED
- D-CHAOS-1 ✅ RESOLVED
- D-SLO-1 ✅ RESOLVED
- D-FINOPS-1 ✅ RESOLVED
- **D-FINOPS-2 honestly DEFER preserved** (1 NEW 결정 wire 진입 완료 보존)

## 결정 wire 일자
2026-08-24 (KST)

## Next
- 옵션 (a) Phase 12 close-out retro 진입 (cj-style 112번째)
- 옵션 (b) Phase 13+ 진입
- 옵션 (c) Epic 18+ 진입
- 옵션 (d) carry-over 진입
- 옵션 (e) 1st release follow-up
- 옵션 (f) D-DEFER-* follow-up 결정 wire 보류
