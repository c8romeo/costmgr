---
baseline_commit: d31dfc8
status: ready-for-dev
cj_style_entry_point: 114
story_key: phase-13-finops-forecasting-capacity-planning-wire
---

# Phase 13 FinOps Forecasting & Capacity Planning wire spec (cj-style 114번째 epic 연속 정직 회복)

## Story

**As a** finance team / FinOps analyst / department cost center owner / capacity planner / tenant admin / enterprise onboarding lead / compliance officer
**I want** FinOps Forecasting & Capacity Planning territory 결정 wire (forecast definition DSL `ForecastDefinition` TypedDict 11 fields + 5 target_metrics department/cost_center/product_line/service/tenant_total + forecast engine 4 methods ARIMA + Prophet + LSTM + ensemble + capacity headroom analyzer 3 resource types compute/storage/network + 90일 lookahead + budget burn-rate projection 4-input formula + forecast accuracy tracker MAE + MAPE + RMSE + model retraining trigger + capability matrix v1.38 EXTENSION FINOPS_FORECASTING_CAPACITY_PLANNING)
**so that** Phase 12 wire `f3c0e63` Cost Anomaly Detection & Budget Alerting territory 의 natural backend FORECASTING & PLANNING LAYER EXTENSION 결정 wire 진입 (anomaly detection baseline last 30d/90d/YTD → forward forecast EXTENSION 12-month prediction with 95% CI + budget overrun linear extrapolation → ARIMA/Prophet/LSTM time series forecast + forecast accuracy 의 MAE/MAPE/RMSE → forward-looking forecasting engine + capacity planning 의 compute/storage/network saturation 90일 lookahead + budget burn-rate projection territory 의 natural next + Phase 11 wire `e020ad0` showback period selector (current/previous/last 3/6 months/YTD) + Phase 8 wire `60d4ea1` cost-engine 12-period benchmark 의 자연스러운 carry-over chain + Epic 12 2FA 챌린지 보존 + AD-22 owner-only RBAC 보존 + D-FINOPS-3 honestly DEFER 보존 진입 결정 wire + Phase 12 close-out retro `3354e83` §13 verbatim 해소 결정 wire 보존).

## Context

cj-style Phase 13 2번째 진입점 (cj-style 114번째) 진입 결정 wire 진입 완료:
- Phase 13 PRD entry `d31dfc8` (cj-style 113번째) DONE 진입 정합 보존
- Phase 12 close-out retro `3354e83` (cj-style 112번째) + Phase 12 atomic wire T1~T8 `f3c0e63` (cj-style 111번째) + Phase 12 spec entry `8c5f374` (cj-style 110번째) + Phase 12 PRD entry `344c7eb` (cj-style 109번째) + Phase 11 close-out retro `80df15b` (cj-style 108번째) + Phase 11 atomic wire T1~T8 `e020ad0` (cj-style 107번째) + Phase 11 spec entry `82c93a8` (cj-style 106번째) + Phase 11 PRD entry `16d7698` (cj-style 105번째) + Phase 10 close-out retro `733d428` (cj-style 104번째) + Phase 10 atomic wire T1~T8 `ac5d6c5` (cj-style 103번째) 결정 wire 모두 DONE 진입 정합 보존
- D-FINOPS-3 honestly DEFER 보존 진입 결정 wire (Phase 12 close-out retro §13 + Phase 11 close-out retro §12 + Phase 10 close-out retro §10 + Phase 9 close-out retro §10 + Phase 8 close-out retro §10 + Phase 7 close-out retro §10 + Phase 6 close-out retro §13 + Epic 17 close-out retro §11 "FinOps Forecasting & Capacity Planning 결정 wire 보류, Phase 13+ 진입 시점" verbatim 해소 + Phase 13 PRD entry 진입 시점에 1 NEW 결정 wire)
- D-FINOPS-2 ✅ RESOLVED 보존 진입 결정 wire
- D-FINOPS-1 ✅ RESOLVED 보존 진입 결정 wire
- D-SLO-1 ✅ RESOLVED 보존 진입 결정 wire
- D-CHAOS-1 ✅ RESOLVED 보존 진입 결정 wire
- D-PERFORMANCE-1 ✅ RESOLVED 보존 진입 결정 wire
- D-OBSERVABILITY-1 ✅ RESOLVED 보존 진입 결정 wire
- Phase 13 PRD entry 의 8 ACs §F29.1~§F29.8 verbatim 결정 wire 보존
- Capability matrix v1.37 → v1.38 EXTENSION FINOPS_FORECASTING_CAPACITY_PLANNING 1 NEW row 결정 wire (industry-agnostic 4-industry grants ✅/✅/✅/✅ CR 12-1 L4 precedent 미러)
- AD-40 FinOps Forecasting & Capacity Planning 신규 결정 wire 진입 (a)~(g) 7 sub-decisions

## 8 ACs (PRD §F29.1~§F29.8 verbatim) → 92 detailed sub-ACs

### §F29.1 forecast definition DSL (12 sub-ACs)
- F29.1-1 `apps/api/modules/finops/forecast_definition.py` NEW (~+150 LOC + `define_forecast(tenant_id, target_metric, dimension_value, horizon_months, model_type, confidence_level)` builder + AST 5 levels + parser 검증 3 layer 결정 wire + 4 industries baseline industry-agnostic + per-tenant override EXTENSION)
- F29.1-2 `ForecastDefinition` TypedDict 11 fields 결정 wire (forecast_id UUID PK + tenant_id UUID + target_metric enum department/cost_center/product_line/service/tenant_total + dimension_value TEXT + horizon_months enum 3m/6m/12m/24m + model_type enum arima/prophet/lstm/ensemble + confidence_level enum 80/90/95/99 + retraining_cron TEXT + status enum active/paused/expired + created_at TIMESTAMPTZ + updated_at TIMESTAMPTZ)
- F29.1-3 5 target_metrics 옵션 결정 wire (department + cost_center + product_line + service + tenant_total + per-tenant override EXTENSION + tenant_settings.target_metric JSONB column)
- F29.1-4 4 horizon_months 옵션 결정 wire (3m + 6m + 12m + 24m + FORECAST_DEFAULTS `horizon_months=12` default + per-tenant override EXTENSION)
- F29.1-5 `FORECAST_DEFAULTS` constants 결정 wire (horizon_months default 12 + model_type default ensemble + confidence_level default 95 + retraining_cron default '0 3 * * 0' KST 일요일 03:00)
- F29.1-6 4 industries baseline industry-agnostic 결정 wire (manufacturing + service + manufacturing_service + manufacturing_service_other 모두 forecast 가능 + per-tenant override EXTENSION + Phase 11 wire `e020ad0` FINOPS_SHOWBACK + FINOPS_CHARGEBACK 4-industry grants ✅/✅/✅/✅ pattern verbatim 미러 + Phase 12 wire `f3c0e63` FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT 4-industry grants ✅/✅/✅/✅ pattern verbatim 미러)
- F29.1-7 forecast definition pure validator CR 11-4 P-015 verbatim 결정 wire (`parse_forecast_definition(tenant_id, payload) -> ForecastDefinition` + 6 validation rules + `ForecastDefinitionInvalidError(400)` CR 12-5 D-14 envelope)
- F29.1-8 audit-first INSERT `forecast_definition_updated` 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_FORECAST 신규 정의 + emit_audit_typed BEFORE forecast definition update + per-tenant RLS 자동 적용 + multi-tenant isolation test)
- F29.1-9 typed exception envelope CR 12-5 D-14 verbatim 결정 wire (3 NEW typed exception classes: `ForecastDefinitionInvalidError(400)` + `ForecastScopeInvalidError(400)` + `ForecastHistoryUnavailableError(422)`)
- F29.1-10 RLS 자동 적용 CR 0-2 verbatim 결정 wire (phase_13_finops_forecast_definition + phase_13_finops_forecast_preview 2 tables 모두 RLS + tenant_id selector + cross-tenant isolation 검증)
- F29.1-11 dry-run mode `--finops-forecast-dry-run` CLI flag 결정 wire (dry-run 시 actual forecast generation skip + forecast preview phase_13_finops_forecast_preview table alembic 0045 신규 + audit-first INSERT `forecast_dry_run_executed` CR 1-1 verbatim)
- F29.1-12 V8 determinism byte-identical 테스트 결정 wire (Phase 8 wire `60d4ea1` cost-engine V8 골든 fixture pattern verbatim 미러 + tenant-scoped result_hash + golden_diff detector EXTENSION)

### §F29.2 forecast engine 4 methods ARIMA + Prophet + LSTM + ensemble (12 sub-ACs)
- F29.2-1 `apps/api/modules/finops/forecast_engine.py` NEW (~+200 LOC + `generate_forecast(tenant_id, target_metric, horizon_months) -> ForecastResult` + 4 time series models parallel run + multi-method voting consensus 4 methods decide)
- F29.2-2 4 forecast methods 결정 wire (ARIMA p=2 d=1 q=2 + Prophet seasonality_mode='multiplicative' + LSTM hidden_layers=50 + ensemble voting consensus 4 methods + statsmodels==0.14.1 + prophet==1.1.5 + tensorflow==2.15.0 AD-14 stack pin 결정 wire)
- F29.2-3 `ForecastResult` TypedDict 10 fields 결정 wire (forecast_id + tenant_id + target_metric + horizon_months + predicted_values List[float] + confidence_lower List[float] + confidence_upper List[float] + model_type + model_version + generated_at)
- F29.2-4 historical baseline source 결정 wire (last 12-month historical baseline data source = phase_11_finops_showback table Phase 11 wire `e020ad0` EXTENSION + phase_12_finops_anomaly_detection table Phase 12 wire `f3c0e63` EXTENSION + LISTEN/NOTIFY Phase 11 wire `cost_engine_cache` channel EXTENSION)
- F29.2-5 seasonality detection 결정 wire (weekly + monthly + quarterly + yearly 4 seasonality modes + STL trend decomposition + holiday calendar KST 8 holidays 신정 + 설날 + 삼일절 + 어린이날 + 현충일 + 광복절 + 개천절 + 크리스마스 for Prophet seasonality EXTENSION)
- F29.2-6 ARIMA model 결정 wire (statsmodels==0.14.1 AD-14 stack pin + ARIMA p=2 d=1 q=2 default + auto_arima per-tenant override EXTENSION + tenant_settings.arima_order JSONB column)
- F29.2-7 Prophet model 결정 wire (prophet==1.1.5 AD-14 stack pin + Prophet seasonality_mode='multiplicative' default + 8 KST holidays for Prophet seasonality + per-tenant override EXTENSION)
- F29.2-8 LSTM model 결정 wire (tensorflow==2.15.0 AD-14 stack pin + LSTM hidden_layers=50 default + epochs=100 default + batch_size=32 default + per-tenant override EXTENSION)
- F29.2-9 ensemble voting consensus 결정 wire (4 methods 4-way voting + majority 3-of-4 agree + per-tenant override EXTENSION + ensemble_weight JSONB column)
- F29.2-10 model_version tracking 결정 wire (semantic versioning MAJOR.MINOR.PATCH + JSONB metadata + model_registry `apps/api/modules/finops/forecast_model_registry.py` NEW 결정 wire + Phase 12 wire `f3c0e63` forecast_accuracy.py model_version tracking 정합)
- F29.2-11 typed exception envelope CR 12-5 D-14 verbatim 결정 wire (3 NEW typed exception classes: `ForecastEngineError(500)` + `ForecastModelTrainingError(500)` + `ForecastSeasonalityDetectionError(500)`)
- F29.2-12 dry-run mode `--finops-forecast-dry-run` CLI flag 결정 wire (dry-run 시 actual model training skip + actual forecast generation skip + forecast preview phase_13_finops_forecast_preview table alembic 0045 신규 EXTENSION)

### §F29.3 capacity headroom analyzer 3 resource types + 90일 lookahead (12 sub-ACs)
- F29.3-1 `apps/api/modules/finops/capacity_headroom.py` NEW (~+180 LOC + `analyze_capacity_headroom(tenant_id, resource_type) -> CapacityHeadroomReport` + 3 resource type (compute + storage + network) + 90일 lookahead window 결정 wire)
- F29.3-2 `CapacityHeadroomReport` TypedDict 14 fields 결정 wire (tenant_id + resource_type enum compute/storage/network + current_saturation_pct + predicted_saturation_pct List[float] + headroom_pct = (1 - saturation_pct) × 100 + lookahead_days enum 30/60/90 default 90 + critical_threshold headroom < 20% → Slack + PagerDuty + warning_threshold headroom < 40% → Slack + forecast_method enum lstm_primary/prophet_primary/arima_primary/ensemble + confidence_level + analyzed_at + trace_id + tenant_id resource_type lookahead_days UNIQUE constraint)
- F29.3-3 compute resource type 결정 wire (CPU utilization + memory utilization + instance_count 3 metrics + 90일 lookahead LSTM primary + Phase 8 wire `60d4ea1` k6 부하 테스트 EXTENSION + Phase 7 wire `59b56cd` Prometheus EXTENSION 정합)
- F29.3-4 storage resource type 결정 wire (DB size + backup storage 2 metrics + 90일 lookahead Prophet primary + Phase 5 wire `f093f8c` cross-region replica EXTENSION 정합)
- F29.3-5 network resource type 결정 wire (egress bandwidth + ingress bandwidth 2 metrics + 90일 lookahead ARIMA primary + Phase 7 wire `59b56cd` observability metrics EXTENSION 정합)
- F29.3-6 3 saturation levels 결정 wire (OK headroom > 40% + WARNING 20% < headroom < 40% + CRITICAL headroom < 20% + saturation level enum decision)
- F29.3-7 critical threshold alerting 결정 wire (headroom < 20% → Slack + PagerDuty + audit-first INSERT `capacity_threshold_breach` CR 1-1 verbatim + alert_dedup_window 1h default + per-tenant override EXTENSION)
- F29.3-8 warning threshold alerting 결정 wire (headroom < 40% → Slack only + audit-first INSERT `capacity_warning_sent` CR 1-1 verbatim + alert_dedup_window 24h default + per-tenant override EXTENSION)
- F29.3-9 capacity metrics source 결정 wire (Prometheus custom metrics Phase 7 wire `59b56cd` EXTENSION + LISTEN/NOTIFY capacity_metrics channel EXTENSION + per-tenant capacity_metrics table RLS CR 0-2 verbatim)
- F29.3-10 audit-first INSERT `capacity_headroom_analyzed` 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_FORECAST + emit_audit_typed BEFORE capacity analysis + per-tenant RLS 자동 적용)
- F29.3-11 typed exception envelope CR 12-5 D-14 verbatim 결정 wire (3 NEW typed exception classes: `CapacityHeadroomAnalysisError(500)` + `CapacityThresholdBreachError(500)` + `CapacityMetricUnavailableError(404)`)
- F29.3-12 dry-run mode `--finops-capacity-dry-run` CLI flag 결정 wire (dry-run 시 actual capacity analysis skip + capacity preview phase_13_finops_forecast_preview table alembic 0045 신규 EXTENSION)

### §F29.4 budget burn-rate projection (12 sub-ACs)
- F29.4-1 `apps/api/modules/finops/budget_burnrate.py` NEW (~+150 LOC + `project_budget_consumption(tenant_id, period_key) -> BurnRateProjection` + 4-input formula 결정 wire)
- F29.4-2 4-input formula 결정 wire (current_consumption + period_elapsed_days + period_total_days + historical_consumption_rate 4 inputs + linear extrapolation + ARIMA-based projection 7/30-day rolling projection)
- F29.4-3 `BurnRateProjection` TypedDict 12 fields 결정 wire (tenant_id + period_key + budget_id + current_consumption NUMERIC + period_elapsed_days + period_total_days + historical_consumption_rate NUMERIC + projected_consumption NUMERIC + predicted_overrun_pct NUMERIC + severity enum warning/critical/exceeded + alert_required BOOLEAN + projected_at TIMESTAMPTZ + trace_id)
- F29.4-4 `BudgetOverrunPrediction` TypedDict 8 fields 결정 wire (tenant_id + period_key + predicted_overrun_pct + predicted_overrun_at TIMESTAMPTZ + confidence_level + severity enum warning/critical + forecast_method + generated_at)
- F29.4-5 predicted_overrun_pct threshold 결정 wire (> 110% warning alert + > 130% critical alert + > 150% exceeded alert + 3-level severity routing)
- F29.4-6 Phase 12 wire `f3c0e63` budget_alert linear extrapolation EXTENSION 결정 wire (Phase 12 budget_alert.py 의 linear_extrapolation 함수 carry-over chain verbatim + Phase 11 wire `e020ad0` chargeback_amount format verbatim)
- F29.4-7 ARIMA-based projection 결정 wire (statsmodels==0.14.1 AD-14 stack pin + ARIMA p=2 d=1 q=2 7-day/30-day rolling window + per-tenant override EXTENSION)
- F29.4-8 alert routing 결정 wire (warning → Slack only / critical → Slack + PagerDuty / exceeded → Slack + PagerDuty + Email + audit-first INSERT `budget_burn_rate_projected` CR 1-1 verbatim)
- F29.4-9 alert deduplication 결정 wire (24시간 이내 중복 skip + alert_dedup_window_seconds default 86400 + per-tenant override EXTENSION + Phase 12 wire `f3c0e63` budget_alert dedup pattern verbatim 미러)
- F29.4-10 audit-first INSERT `budget_burn_rate_projected` 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_FORECAST + emit_audit_typed BEFORE budget burn-rate projection + per-tenant RLS 자동 적용)
- F29.4-11 typed exception envelope CR 12-5 D-14 verbatim 결정 wire (2 NEW typed exception classes: `BudgetBurnRateProjectionError(500)` + `BudgetOverrunPredictionError(500)`)
- F29.4-12 dry-run mode `--finops-burnrate-dry-run` CLI flag 결정 wire (dry-run 시 actual budget burn-rate projection skip + budget burn-rate preview phase_13_finops_forecast_preview table alembic 0045 신규 EXTENSION)

### §F29.5 forecast accuracy tracker + model retraining trigger (10 sub-ACs)
- F29.5-1 `apps/api/modules/finops/forecast_accuracy_tracker.py` NEW (~+120 LOC + `track_forecast_accuracy(tenant_id, target_metric) -> ForecastAccuracyReport` + per-model accuracy tracking 결정 wire)
- F29.5-2 per-model accuracy tracking 결정 wire (per tenant_id + target_metric + model_type 3-tuple granularity + Phase 12 wire `f3c0e63` forecast_accuracy.py EXTENSION chain 정합 + MAE + MAPE + RMSE 3 metrics)
- F29.5-3 MAE (Mean Absolute Error) 결정 wire (MAE = mean(|actual - predicted|) + banker's rounding 적용 CR 5-1 verbatim)
- F29.5-4 MAPE (Mean Absolute Percentage Error) < 10% high accuracy 결정 wire (MAPE = mean(|actual - predicted| / actual) * 100 + HIGH_ACCURACY_THRESHOLD 0.10 default + accuracy threshold 10%)
- F29.5-5 RMSE (Root Mean Squared Error) 결정 wire (RMSE = sqrt(mean((actual - predicted)^2)) + banker's rounding 적용 CR 5-1 verbatim)
- F29.5-6 ensemble vs individual model comparison 결정 wire (ensemble accuracy vs ARIMA accuracy vs Prophet accuracy vs LSTM accuracy 4-way comparison + ensemble improvement_pct = (ensemble_MAPE - best_individual_MAPE) / best_individual_MAPE * 100)
- F29.5-7 model performance degradation detection 결정 wire (MAPE > 20% for 3 consecutive periods → trigger retraining + RETRAIN_TRIGGER_THRESHOLD 0.20 default + audit-first INSERT `forecast_accuracy_degraded` CR 1-1 verbatim)
- F29.5-8 model retraining trigger 결정 wire (MAPE > 20% for 3 consecutive periods → retraining cron KST 매주 일요일 03:00 UTC 18:00 + Phase 12 wire `f3c0e63` anomaly detection isolation_forest retraining cron EXTENSION 정합 + audit-first INSERT `model_retraining_triggered` CR 1-1 verbatim)
- F29.5-9 typed exception envelope CR 12-5 D-14 verbatim 결정 wire (3 NEW typed exception classes: `ForecastAccuracyTrackingError(500)` + `ModelRetrainingTriggerError(500)` + `ModelPerformanceDegradationError(500)`)
- F29.5-10 `ModelRetrainingTrigger` TypedDict 8 fields 결정 wire (tenant_id + target_metric + model_type + current_MAPE NUMERIC + trigger_threshold NUMERIC + consecutive_degraded_periods INTEGER + retraining_cron TEXT + triggered_at TIMESTAMPTZ)

### §F29.6 forecast dashboard UI (10 sub-ACs)
- F29.6-1 `apps/web/app/[locale]/(dashboard)/admin/finops/forecast/page.tsx` NEW (~+150 LOC + 5 components 결정 wire: ForecastHorizonSelector + ForecastChart + CapacityHeadroomGauge + BudgetBurnRatePanel + ForecastAccuracyPanel + owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 보존)
- F29.6-2 `ForecastHorizonSelector` component 결정 wire (4 horizon options radio button 결정 wire: 3m + 6m + 12m + 24m + onChange handler + ko-KR.json `finops_forecast_horizon_label` EXTENSION)
- F29.6-3 `ForecastChart` component 결정 wire (Recharts 2.12.7 AD-14 stack pin + LineChart predicted_values + confidence band confidence_lower + confidence_upper + 95% CI shading 결정 + tenant currency_code 적용 + ko-KR.json `finops_forecast_chart_label` EXTENSION + RTL render discipline)
- F29.6-4 `CapacityHeadroomGauge` component 결정 wire (Recharts 2.12.7 AD-14 stack pin + Gauge chart 0-100% headroom + 3 saturation levels (OK green + WARNING yellow + CRITICAL red) 결정 wire + ko-KR.json `finops_capacity_gauge_label` EXTENSION)
- F29.6-5 `BudgetBurnRatePanel` component 결정 wire (CRUD + 3-level severity visualization + 110% warning yellow + 130% critical orange + 150% exceeded red 결정 wire + ko-KR.json `finops_burn_rate_label` EXTENSION)
- F29.6-6 `ForecastAccuracyPanel` component 결정 wire (3 metrics visualization MAE + MAPE + RMSE + per-model accuracy table + ensemble vs individual model comparison 결정 wire + ko-KR.json `finops_forecast_accuracy_label` EXTENSION)
- F29.6-7 ko-KR.json `finops_forecast.*` namespace EXTENSION 결정 wire (~30 keys CR 11-4 D-002 verbatim SSOT 결정 wire: finops_forecast_dashboard_title + finops_forecast_horizon_label + finops_forecast_chart_label + finops_forecast_model_label + finops_forecast_confidence_label + finops_forecast_seasonality_label + finops_capacity_gauge_label + finops_capacity_ok_label + finops_capacity_warning_label + finops_capacity_critical_label + finops_capacity_compute_label + finops_capacity_storage_label + finops_capacity_network_label + finops_burn_rate_label + finops_burn_rate_warning_label + finops_burn_rate_critical_label + finops_burn_rate_exceeded_label + finops_forecast_accuracy_label + finops_forecast_accuracy_mae_label + finops_forecast_accuracy_mape_label + finops_forecast_accuracy_rmse_label + finops_forecast_model_arima_label + finops_forecast_model_prophet_label + finops_forecast_model_lstm_label + finops_forecast_model_ensemble_label + finops_forecast_retraining_label + loading_finops_forecast + error_finops_forecast_failed + empty_state + owner_only_label)
- F29.6-8 ARIA labels WCAG 2.1 AA + Epic 12 2FA 챌린지 보존 결정 wire (ko-KR inline ARIA + i18n SSOT + keyboard navigation Tab + Enter + Arrow keys + screen reader 지원 + Phase 13 Epic 1 UX v1.0 locked decision Dark MVP / WCAG AA / Professional / ko-KR verbatim 보존)
- F29.6-9 toast notification 결정 wire (warning yellow / critical red / exceeded purple + duration 5s default + ko-KR toast EXTENSION + ARIA live region polite)
- F29.6-10 Vitest RTL render discipline CR 11-4 D-003 verbatim 적용 결정 wire (Phase 12 wire `f3c0e63` anomaly-dashboard.test.tsx pattern verbatim 미러)

### §F29.7 Capability matrix v1.38 EXTENSION (12 sub-ACs)
- F29.7-1 Capability matrix v1.37 → v1.38 EXTENSION 결정 wire (1 NEW row FINOPS_FORECASTING_CAPACITY_PLANNING industry-agnostic 4-industry grants ✅/✅/✅/✅ CR 12-1 L4 precedent 미러)
- F29.7-2 `apps/api/core/capability.py` MODIFIED 결정 wire (Capability.FINOPS_FORECASTING_CAPACITY_PLANNING = "finops_forecasting_capacity_planning" 1 NEW enum + 4 `_INDUSTRY_CAPABILITIES` blocks EXTENSION industry-agnostic ✅/✅/✅/✅)
- F29.7-3 `apps/api/dependencies/capability.py` MODIFIED 결정 wire (require_finops_forecast 1 NEW dep + `__all__` EXTENSION)
- F29.7-4 `docs/capability-matrix.md` MODIFIED 결정 wire (capability matrix v1.37 → v1.38 EXTENSION + 1 NEW row FINOPS_FORECASTING_CAPACITY_PLANNING industry-agnostic 4-industry grants ✅/✅/✅/✅ + FINOPS_FORECAST section 신규 추가)
- F29.7-5 `apps/api/modules/finops/__init__.py` MODIFIED 결정 wire (Phase 12 wire `f3c0e63` m20_finops_anomaly EXTENSION + m21_finops_forecast 신규 module 결정 wire + finops_serializers EXTENSION + m21_finops_forecast.finops_forecast_serializers NEW 결정 wire)
- F29.7-6 미허용 tenant 의 forecast 진입 차단 결정 wire (require_finops_forecast dep + capability gate per-tenant on/off + 403 Forbidden + FORBIDDEN_KO message 결정 wire ("FinOps Forecasting & Capacity Planning capability 미허용 tenant") + Epic 12 2FA 챌린지 보존 + AD-22 owner-only RBAC 정합)
- F29.7-7 drift detector 10 NEW pytest cases 결정 wire (`tests/integration/test_capability_matrix_v1_38_drift.py` NEW + Phase 12 wire `f3c0e63` `test_capability_matrix_v1_37_drift.py` 패턴 verbatim 미러)
- F29.7-8 m21_finops_forecast module 결정 wire (apps/api/modules/finops/__init__.py EXTENSION + m21_finops_forecast.finops_forecast_serializers NEW 결정 wire + Phase 12 wire `f3c0e63` m20_finops_anomaly.finops_anomaly_serializers EXTENSION pattern verbatim 미러)
- F29.7-9 SSOT RED→GREEN EXTENSION + A36 SDR 검증 4-step 자동 적용 결정 wire (capability matrix v1.38 신규 1 row + capability.py EXTENSION 1 NEW enum + require_finops_forecast 1 NEW dep 결정 wire + drift detector EXTENSION)
- F29.7-10 CR 12-1 L4 industry-agnostic capability 결정 wire (FINOPS_FORECASTING_CAPACITY_PLANNING industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire manufacturing + service + manufacturing_service + manufacturing_service_other 모두 허용)
- F29.7-11 capability gate 의 fail-closed 결정 wire (미허용 tenant 의 forecast 진입 차단 + capability matrix v1.38 row 부재 시 fail-closed + Capability enum 부재 시 fail-closed + AD-22 owner-only RBAC 정합 + Epic 12 2FA 챌린지 보존 + NFR4 PII minimization 정합 보존)
- F29.7-12 capability matrix 의 version 결정 wire v1.37 → v1.38

### §F29.8 dry-run + Tests + wire scope T1~T8 (12 sub-ACs)
- F29.8-1 dry-run mode 결정 wire (`--finops-forecast-dry-run` + `--finops-capacity-dry-run` + `--finops-burnrate-dry-run` 3 CLI flag + forecast dry-run parameter + capacity dry-run parameter + budget burn-rate dry-run parameter + dry-run 시 actual forecast generation skip + dry-run 시 actual capacity analysis skip + dry-run 시 actual budget burn-rate projection skip + dry-run 시 actual forecast_definition_updated INSERT skip)
- F29.8-2 dry-run 의 preview 결과 결정 wire (phase_13_finops_forecast_preview table alembic 0045 신규 + preview 결과 ko-KR.json `finops_forecast_preview_label` + `finops_capacity_preview_label` + `finops_burn_rate_preview_label` EXTENSION 결정 wire)
- F29.8-3 dry-run 의 CLI flag 결정 wire (`--finops-forecast-dry-run` + `--finops-capacity-dry-run` + `--finops-burnrate-dry-run` 3 NEW CLI flag + Phase 12 wire `f3c0e63` `--finops-anomaly-dry-run` + `--finops-budget-dry-run` 패턴 verbatim 미러)
- F29.8-4 tests ~+50 NEW pytest PASS 결정 wire (forecast_definition_dsl 6 + forecast_engine 8 + capacity_headroom 8 + budget_burnrate 6 + forecast_accuracy_tracker 6 + audit_action 7 + capability matrix v1.38 10 = ~51 NEW pytest PASS)
- F29.8-5 vitest tests ~+5 NEW vitest PASS 결정 wire (ForecastChart 1 + CapacityHeadroomGauge 1 + ForecastAccuracyPanel 1 + ko-KR SSOT 1 + ForecastHorizonSelector 1 = ~5 NEW vitest PASS)
- F29.8-6 ruff + tsc 0 NEW + SDR drift gate 결정 wire (0 NEW ruff + 0 NEW tsc + 0 regressions + SDR drift gate PASS 결정 wire + A36 SDR 검증 4-step 자동 적용)
- F29.8-7 wire scope T1~T8 결정 wire (~+30 files estimate = ~18 NEW + ~12 MODIFIED atomic single sprint)
- F29.8-8 A19 cohesion pattern 9 surface EXTENSION PASS 결정 wire (FinOps Forecasting & Capacity Planning surface NEW = F29.1~F29.8 + spec surface EXTENSION + test surface EXTENSION + docs surface EXTENSION)
- F29.8-9 CR lessons applied 14종 결정 wire (CR 0-2 + CR 1-1 + CR 4-3/4-4 + CR 1-1 ContextVar + CR 1-1 RSC boundary + CR 9-6 + CR 11-3 + CR 11-4 + CR 12-1 + CR 12-5 D-14 + CR 12-5 D-PARITY-01 + CR 12-5 D-GATE-01 + A19 cohesion + A36 SDR 검증)
- F29.8-10 D-DEFER-* honestly 결정 wire (D-FINOPS-3 honestly preserved → Phase 13 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire + D-FINOPS-2 ✅ RESOLVED + D-FINOPS-1 ✅ RESOLVED + D-SLO-1 ✅ RESOLVED + D-CHAOS-1 ✅ RESOLVED + D-PERFORMANCE-1 ✅ RESOLVED + D-OBSERVABILITY-1 ✅ RESOLVED + D-RETENTION-1 ✅ RESOLVED + D-EPIC-17-WIRE-DEFER-T2-T3-UI ✅ RESOLVED + D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED + D-EPIC-16-REVIEW-DEFER-2~6 ✅ RESOLVED + D-1-1-DEFER-1/2/3 ✅ RESOLVED 모두 보존)
- F29.8-11 Epic 1 ~ Epic 17 + Phase 3 ~ Phase 12 + 1st release cycle 정합 보존 결정 wire (cj-style 113번째 wire entry 모두 DONE 진입 정합 보존 + Phase 12 close-out retro `3354e83` + Phase 12 atomic wire T1~T8 `f3c0e63` + Phase 12 spec entry `8c5f374` + Phase 12 PRD entry `344c7eb` 모두 정합)
- F29.8-12 partial wire 시도 0건 + single sprint atomic docs-and-source wire 1 진입점 결정 wire (cj-style 114번째 epic 연속 정직 회복 Phase 13 spec entry atomic docs-only wire 5 files atomic single sprint 결정 wire)

## 8 tasks (T1~T8) + 68 subtasks

### T1: forecast_definition + forecast_dsl module (10 subtasks)
- T1.1: `apps/api/modules/finops/forecast_definition.py` NEW (~+150 LOC + define_forecast builder + AST 5 levels + parser 검증 3 layer + 4 industries baseline + per-tenant override EXTENSION + FORECAST_DEFAULTS constants 결정 wire)
- T1.2: ForecastDefinition TypedDict 11 fields 결정 wire (forecast_id + tenant_id + target_metric enum + dimension_value + horizon_months enum + model_type enum + confidence_level enum + retraining_cron + status enum + created_at + updated_at)
- T1.3: 5 target_metrics 옵션 결정 wire (department + cost_center + product_line + service + tenant_total + per-tenant override EXTENSION)
- T1.4: 4 horizon_months 옵션 결정 wire (3m + 6m + 12m + 24m + FORECAST_DEFAULTS horizon_months=12 default)
- T1.5: forecast definition pure validator CR 11-4 P-015 verbatim 적용 결정 wire (parse_forecast_definition 함수 + 6 validation rules + ForecastDefinitionInvalidError(400) CR 12-5 D-14 envelope)
- T1.6: 6 NEW pytest cases 결정 wire (TypedDict validation + 5 target_metrics 옵션 + 4 horizon_months 옵션 + 4 industries baseline + audit-first INSERT + owner-only RBAC + dry_run default)
- T1.7: forecast_definition DSL audit-first INSERT `forecast_definition_updated` 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_FORECAST + emit_audit_typed BEFORE forecast definition update + per-tenant RLS 자동 적용)
- T1.8: forecast_definition owner-only RBAC AD-22 결정 wire (forecast definition 모두 owner-only + Epic 12 2FA 챌린지 + governance_required=True mandatory)
- T1.9: forecast_definition dry-run mode default 결정 wire (dry_run=True flag + audit-first INSERT `forecast_dryrun` + no actual forecast definition)
- T1.10: forecast_definition CR 0-2 RLS verbatim 적용 결정 wire + tenant_id selector + cross-tenant isolation 검증 + phase_13_finops_forecast_definition table 결정 wire

### T2: forecast_engine + 4 time series models (10 subtasks)
- T2.1: `apps/api/modules/finops/forecast_engine.py` NEW (~+200 LOC + generate_forecast 함수 + 4 time series models parallel run + multi-method voting consensus 4 methods decide + CR 12-5 D-PARITY-01 verbatim)
- T2.2: ForecastResult TypedDict 10 fields 결정 wire (forecast_id + tenant_id + target_metric + horizon_months + predicted_values List + confidence_lower List + confidence_upper List + model_type + model_version + generated_at)
- T2.3: 4 forecast methods 결정 wire (ARIMA p=2 d=1 q=2 + Prophet seasonality_mode='multiplicative' + LSTM hidden_layers=50 + ensemble voting consensus + statsmodels==0.14.1 + prophet==1.1.5 + tensorflow==2.15.0 AD-14 stack pin)
- T2.4: historical baseline source 결정 wire (last 12-month historical baseline data source = phase_11_finops_showback table Phase 11 wire `e020ad0` EXTENSION + phase_12_finops_anomaly_detection table Phase 12 wire `f3c0e63` EXTENSION + LISTEN/NOTIFY Phase 11 wire `cost_engine_cache` channel EXTENSION)
- T2.5: seasonality detection 결정 wire (weekly + monthly + quarterly + yearly 4 seasonality modes + STL trend decomposition + holiday calendar KST 8 holidays 신정 + 설날 + 삼일절 + 어린이날 + 현충일 + 광복절 + 개천절 + 크리스마스)
- T2.6: ARIMA + Prophet + LSTM individual model 결정 wire (statsmodels==0.14.1 + prophet==1.1.5 + tensorflow==2.15.0 AD-14 stack pin + per-tenant override EXTENSION)
- T2.7: ensemble voting consensus 결정 wire (4 methods 4-way voting + majority 3-of-4 agree + per-tenant override EXTENSION)
- T2.8: model_registry `apps/api/modules/finops/forecast_model_registry.py` NEW 결정 wire (model_version tracking + JSONB metadata + semantic versioning MAJOR.MINOR.PATCH)
- T2.9: typed exception envelope CR 12-5 D-14 verbatim 결정 wire (3 NEW typed exception classes: ForecastEngineError + ForecastModelTrainingError + ForecastSeasonalityDetectionError)
- T2.10: 8 NEW pytest cases 결정 wire (4 forecast methods + multi-method voting consensus + seasonality detection + STL decomposition + ensemble voting + model_version tracking + audit-first INSERT + typed exception envelope)

### T3: capacity_headroom + 3 resource types + budget_burnrate (10 subtasks)
- T3.1: `apps/api/modules/finops/capacity_headroom.py` NEW (~+180 LOC + analyze_capacity_headroom 함수 + 3 resource type (compute + storage + network) + 90일 lookahead window 결정 wire + CR 12-5 D-PARITY-01 verbatim)
- T3.2: CapacityHeadroomReport TypedDict 14 fields 결정 wire (tenant_id + resource_type enum + current_saturation_pct + predicted_saturation_pct List + headroom_pct + lookahead_days enum + critical_threshold + warning_threshold + forecast_method + confidence_level + analyzed_at + trace_id + tenant_id resource_type lookahead_days UNIQUE constraint)
- T3.3: compute + storage + network 3 resource type 결정 wire (compute: cpu_avg + memory_avg + instance_count 3 metrics + 90일 lookahead LSTM primary / storage: db_gb + backup_gb 2 metrics + 90일 lookahead Prophet primary / network: egress_gb + ingress_gb 2 metrics + 90일 lookahead ARIMA primary)
- T3.4: 3 saturation levels 결정 wire (OK headroom > 40% + WARNING 20% < headroom < 40% + CRITICAL headroom < 20% + saturation level enum decision)
- T3.5: critical + warning threshold alerting 결정 wire (headroom < 20% → Slack + PagerDuty + audit-first INSERT `capacity_threshold_breach` / headroom < 40% → Slack only + audit-first INSERT `capacity_warning_sent`)
- T3.6: capacity metrics source 결정 wire (Prometheus custom metrics Phase 7 wire `59b56cd` EXTENSION + LISTEN/NOTIFY capacity_metrics channel EXTENSION + per-tenant capacity_metrics table RLS CR 0-2 verbatim)
- T3.7: `apps/api/modules/finops/budget_burnrate.py` NEW (~+150 LOC + project_budget_consumption 함수 + 4-input formula + Phase 12 wire `f3c0e63` budget_alert linear extrapolation EXTENSION + ARIMA-based projection + 7/30-day rolling projection)
- T3.8: 4-input formula + 3-level severity routing 결정 wire (current_consumption + period_elapsed_days + period_total_days + historical_consumption_rate 4 inputs + linear extrapolation + ARIMA-based projection + > 110% warning + > 130% critical + > 150% exceeded)
- T3.9: typed exception envelope CR 12-5 D-14 verbatim 결정 wire (5 NEW typed exception classes: CapacityHeadroomAnalysisError + CapacityThresholdBreachError + CapacityMetricUnavailableError + BudgetBurnRateProjectionError + BudgetOverrunPredictionError)
- T3.10: 8 NEW pytest cases 결정 wire (3 resource types + 3 saturation levels + critical + warning threshold alerting + 4-input formula + 3-level severity routing + audit-first INSERT + typed exception envelope)

### T4: forecast_accuracy_tracker + Phase 12 forecast_accuracy.py EXTENSION (10 subtasks)
- T4.1: `apps/api/modules/finops/forecast_accuracy_tracker.py` NEW (~+120 LOC + track_forecast_accuracy 함수 + per-model accuracy tracking + Phase 12 wire `f3c0e63` forecast_accuracy.py EXTENSION chain 결정 wire)
- T4.2: per-model accuracy tracking 결정 wire (per tenant_id + target_metric + model_type 3-tuple granularity + MAE + MAPE + RMSE 3 metrics + ensemble vs individual model comparison)
- T4.3: MAE + MAPE + RMSE 3 metrics 결정 wire (MAE = mean(|actual - predicted|) + banker's rounding CR 5-1 verbatim / MAPE = mean(|actual - predicted| / actual) * 100 + HIGH_ACCURACY_THRESHOLD 0.10 default / RMSE = sqrt(mean((actual - predicted)^2)) + banker's rounding CR 5-1 verbatim)
- T4.4: ensemble vs individual model comparison 결정 wire (ensemble accuracy vs ARIMA accuracy vs Prophet accuracy vs LSTM accuracy 4-way comparison + ensemble improvement_pct = (ensemble_MAPE - best_individual_MAPE) / best_individual_MAPE * 100)
- T4.5: model performance degradation detection 결정 wire (MAPE > 20% for 3 consecutive periods → trigger retraining + RETRAIN_TRIGGER_THRESHOLD 0.20 default + audit-first INSERT `forecast_accuracy_degraded`)
- T4.6: model retraining trigger 결정 wire (MAPE > 20% for 3 consecutive periods → retraining cron KST 매주 일요일 03:00 UTC 18:00 + Phase 12 wire `f3c0e63` anomaly detection isolation_forest retraining cron EXTENSION 정합 + audit-first INSERT `model_retraining_triggered`)
- T4.7: ModelRetrainingTrigger TypedDict 8 fields 결정 wire (tenant_id + target_metric + model_type + current_MAPE + trigger_threshold + consecutive_degraded_periods + retraining_cron + triggered_at)
- T4.8: typed exception envelope CR 12-5 D-14 verbatim 결정 wire (3 NEW typed exception classes: ForecastAccuracyTrackingError + ModelRetrainingTriggerError + ModelPerformanceDegradationError)
- T4.9: 6 NEW pytest cases 결정 wire (MAE + MAPE + RMSE + ensemble vs individual model comparison + model performance degradation detection + model retraining trigger + audit-first INSERT + typed exception envelope)
- T4.10: Phase 12 wire `f3c0e63` forecast_accuracy.py EXTENSION chain 정합 (Phase 12 forecast_accuracy.py 의 MAE + MAPE + RMSE carry-over chain verbatim + banker's rounding 적용)

### T5: alembic 0045 phase_13_forecasting (8 subtasks)
- T5.1: `apps/api/alembic/versions/0045_phase_13_forecasting.py` NEW (~+250 LOC + 5 tables CREATE + indexes + RLS policies + down_revision "0044_phase_12_finops_anomaly" 결정 wire)
- T5.2: phase_13_finops_forecast_definition table 12 columns 결정 wire (forecast_id UUID PK + tenant_id UUID + target_metric TEXT enum + dimension_value TEXT + horizon_months TEXT enum + model_type TEXT enum + confidence_level TEXT enum + retraining_cron TEXT + status TEXT enum + created_at TIMESTAMPTZ + updated_at TIMESTAMPTZ + trace_id TEXT)
- T5.3: phase_13_finops_forecast_result table 14 columns 결정 wire (forecast_id UUID PK + tenant_id UUID + target_metric TEXT + horizon_months TEXT enum + predicted_values JSONB + confidence_lower JSONB + confidence_upper JSONB + model_type TEXT enum + model_version TEXT + generated_at TIMESTAMPTZ + tenant_id_target_metric_horizon_months UNIQUE constraint + trace_id TEXT + JSONB metadata + tenant_id column)
- T5.4: phase_13_finops_capacity_headroom table 16 columns 결정 wire (tenant_id + resource_type TEXT enum + current_saturation_pct NUMERIC + predicted_saturation_pct JSONB + headroom_pct NUMERIC + lookahead_days TEXT enum + critical_threshold NUMERIC + warning_threshold NUMERIC + forecast_method TEXT enum + confidence_level TEXT enum + saturation_level TEXT enum OK/WARNING/CRITICAL + analyzed_at TIMESTAMPTZ + trace_id TEXT + tenant_id resource_type lookahead_days UNIQUE constraint + JSONB metadata + created_at)
- T5.5: phase_13_finops_budget_burnrate table 14 columns 결정 wire (tenant_id + period_key TEXT + budget_id UUID + current_consumption NUMERIC(20, 2) + period_elapsed_days INTEGER + period_total_days INTEGER + historical_consumption_rate NUMERIC + projected_consumption NUMERIC + predicted_overrun_pct NUMERIC + severity TEXT enum + alert_required BOOLEAN + projected_at TIMESTAMPTZ + trace_id TEXT + JSONB metadata)
- T5.6: 5 tables RLS policies 결정 wire (CR 0-2 verbatim + tenant_id = current_setting('app.tenant_id')::uuid + Phase 12 wire `f3c0e63` phase_12_finops_* table 정합 + Phase 11 wire `e020ad0` phase_11_finops_* table 정합 + Phase 10 wire `ac5d6c5` phase_10_slo_* table 정합)
- T5.7: 5 indexes 결정 wire (idx_phase_13_finops_forecast_definition_tenant_id_target_metric + idx_phase_13_finops_forecast_result_tenant_id_target_metric + idx_phase_13_finops_capacity_headroom_tenant_id_resource_type + idx_phase_13_finops_budget_burnrate_tenant_id_period_key + idx_phase_13_finops_forecast_preview_tenant_id)
- T5.8: alembic migration 4 NEW pytest cases + multi-tenant isolation test 결정 wire (`tests/integration/test_finops_forecast_tenant_isolation.py` NEW + Phase 12 wire `f3c0e63` `test_finops_anomaly_tenant_isolation.py` 패턴 verbatim 미러)

### T6: audit action EXTENSION 7 NEW (8 subtasks)
- T6.1: `apps/api/core/audit_action.py` MODIFIED 결정 wire (ActionClass.FINOPS_FORECAST 1 NEW class 신규 정의 + FinopsForecastAction Literal 7 NEW values + _ActionRegistry FINOPS_FORECAST entry 신규 1개 등록 + __all__ EXTENSION + AuditAction Union EXTENSION)
- T6.2: ActionClass.FINOPS_FORECAST = 'finops_forecast' 신규 정의 결정 wire (CR 12-1 L4 precedent 미러 FINOPS Phase 12 wire + FINOPS_ANOMALY Phase 12 wire + FINOPS_BUDGET Phase 12 wire + FINOPS_SHOWBACK + FINOPS_CHARGEBACK Phase 11 wire + SLO_ENGINEERING Phase 10 wire + CHAOS_ENGINEERING Phase 9 wire + PERFORMANCE_TESTING Phase 8 wire + OBSERVABILITY_TRACES + OBSERVABILITY_METRICS Phase 7 wire pattern verbatim bind)
- T6.3: FinopsForecastAction Literal 7 NEW values 결정 wire = `forecast_definition_updated` + `forecast_generated` + `capacity_headroom_analyzed` + `budget_burn_rate_projected` + `forecast_accuracy_degraded` + `model_retraining_triggered` + `forecast_dry_run_executed` (CR 1-1 verbatim 적용)
- T6.4: _ActionRegistry FINOPS_FORECAST entry 신규 1개 등록 결정 wire (resource_table "phase_13_finops_*" + action_class=FINOPS_FORECAST + 7 NEW actions acceptance + reject)
- T6.5: emit_audit_typed BEFORE/AFTER FinOps Forecast event CR 1-1 verbatim 적용 결정 wire (forecast_definition_updated 의 audit_first INSERT 가 forecast definition 직전에 실행 + forecast_generated AFTER forecast generation + capacity_headroom_analyzed AFTER capacity analysis + budget_burn_rate_projected AFTER budget burn-rate projection + forecast_accuracy_degraded BEFORE model retraining trigger + model_retraining_triggered AFTER retraining trigger + trace_id propagation + actor_id capture + tenant_id capture)
- T6.6: multi-tenant isolation 결정 wire (7 NEW action 의 tenant_id 가 RLS 와 정합 + cross-tenant audit log leak 방지 결정 wire)
- T6.7: typed exception envelope CR 12-5 D-14 verbatim 결정 wire (14 NEW typed exception classes: ForecastDefinitionInvalidError(400) + ForecastScopeInvalidError(400) + ForecastHistoryUnavailableError(422) + ForecastEngineError(500) + ForecastModelTrainingError(500) + ForecastSeasonalityDetectionError(500) + CapacityHeadroomAnalysisError(500) + CapacityThresholdBreachError(500) + CapacityMetricUnavailableError(404) + BudgetBurnRateProjectionError(500) + BudgetOverrunPredictionError(500) + ForecastAccuracyTrackingError(500) + ModelRetrainingTriggerError(500) + ModelPerformanceDegradationError(500))
- T6.8: 7 NEW pytest cases 결정 wire (AuditAction Literal 값 검증 + ActionClass.FINOPS_FORECAST enum value + resource_table + emit_audit_typed BEFORE/AFTER FinOps Forecast event CR 1-1 verbatim 적용 + multi-tenant isolation + trace_id propagation + typed exception envelope + dry-run default)

### T7: capability v1.38 EXTENSION + frontend finops forecast dashboard (8 subtasks)
- T7.1: `apps/api/core/capability.py` MODIFIED 결정 wire (Capability.FINOPS_FORECASTING_CAPACITY_PLANNING 1 NEW enum + 4 `_INDUSTRY_CAPABILITIES` blocks EXTENSION industry-agnostic ✅/✅/✅/✅ CR 12-1 L4 precedent 미러)
- T7.2: `apps/api/dependencies/capability.py` MODIFIED 결정 wire (require_finops_forecast 1 NEW dep + __all__ EXTENSION 결정 wire)
- T7.3: capability matrix v1.37 → v1.38 EXTENSION title update + v1.38 changelog entry prepend + 1 NEW row FINOPS_FORECASTING_CAPACITY_PLANNING industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire
- T7.4: `tests/integration/test_capability_matrix_v1_38_drift.py` NEW 10 NEW pytest cases 결정 wire (Capability.FINOPS_FORECASTING_CAPACITY_PLANNING enum + 4 industries grants + v1.37 + v1.36 + v1.35 + v1.34 + v1.33 + v1.32 + v1.31 + v1.30 + v1.29 preservation + Phase 5 v1.29 + Epic 16 v1.28 + Epic 17 v1.30 + Phase 6 v1.31 + Phase 7 v1.32 + Phase 8 v1.33 + Phase 9 v1.34 + Phase 10 v1.35 + Phase 11 v1.36 + Phase 12 v1.37 pattern verbatim)
- T7.5: `docs/capability-matrix.md` MODIFIED v1.37 → v1.38 EXTENSION 결정 wire (1 NEW row FINOPS_FORECASTING_CAPACITY_PLANNING industry-agnostic 4-industry grants + FINOPS_FORECAST section 신규 추가)
- T7.6: 미허용 tenant 의 FinOps Forecast 진입 차단 결정 wire (require_finops_forecast dep + capability gate per-tenant on/off)
- T7.7: `apps/web/app/[locale]/(dashboard)/admin/finops/forecast/page.tsx` NEW (~+150 LOC + 5 components 결정 wire: ForecastHorizonSelector + ForecastChart + CapacityHeadroomGauge + BudgetBurnRatePanel + ForecastAccuracyPanel + owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 보존)
- T7.8: SSOT RED→GREEN EXTENSION 결정 wire (capability matrix v1.38 신규 1 row + capability.py EXTENSION 1 NEW enum + require_finops_forecast 1 NEW dep wire + drift detector EXTENSION + frontend finops forecast dashboard wire)

### T8: atomic commit (4 subtasks)
- T8.1: 3중 게이트 impact NONE 결정 wire (ruff scoped 0 NEW + pytest 0 NEW failures + vitest 0 NEW failures + tsc 0 NEW errors)
- T8.2: A19 cohesion pattern 9 surface EXTENSION PASS 결정 wire (FinOps Forecasting & Capacity Planning surface NEW = F29.1~F29.8)
- T8.3: atomic commit via `git commit -F <file>` 결정 wire (CR 9-6 D5 prevention + PowerShell here-string 회피)
- T8.4: sprint-status.yaml `phase-13-spec-entry: backlog → done` transition 결정 wire

## Dev Notes (CR lessons applied 14종)

- **CR 0-2 RLS lesson ✅ APPLIED**: Phase 13 wire 시점에 phase_13_finops_forecast_definition + phase_13_finops_forecast_result + phase_13_finops_capacity_headroom + phase_13_finops_budget_burnrate + phase_13_finops_forecast_preview 5 tables 모두 RLS 자동 적용 + multi-tenant isolation test 결정 wire + tenant-scoped result_hash 결정 wire + Phase 12 wire `f3c0e63` phase_12_finops_* table 정합 + Phase 11 wire `e020ad0` phase_11_finops_* table 정합 + Phase 10 wire `ac5d6c5` phase_10_slo_* table 정합 + Phase 5 wire `f093f8c` phase_5_replication_lag table 정합
- **CR 1-1 audit-first INSERT ✅ APPLIED**: ActionClass.FINOPS_FORECAST 신규 정의 + 7 NEW audit log entries (`forecast_definition_updated` + `forecast_generated` + `capacity_headroom_analyzed` + `budget_burn_rate_projected` + `forecast_accuracy_degraded` + `model_retraining_triggered` + `forecast_dry_run_executed`) 결정 wire + emit_audit_typed BEFORE/AFTER FinOps Forecast event CR 1-1 verbatim 적용
- **CR 4-3/4-4 lessons carry ✅ APPLIED**: forecast baseline + capacity baseline 30d rolling + golden_diff pattern verbatim 미러 + tenant-scoped result_hash 결정 wire + Epic 8 wire `e117e09` capability drift detector 정합 패턴 + Phase 12 wire `f3c0e63` forecast accuracy baseline result_hash 패턴 verbatim
- **CR 1-1 ContextVar lesson ✅ APPLIED**: trace_id request-scoped ContextVar 바인딩 + 비동기 trace context 보존 CR 1-1 verbatim 적용 + FinOps Forecast event 의 trace_id propagation 결정 wire
- **CR 1-1 RSC boundary lesson ✅ APPLIED**: `apps/web/app/[locale]/(dashboard)/admin/finops/forecast/page.tsx` Client-only + finops forecast dashboard server-only delegation 결정 wire + CR 1-1 verbatim 적용
- **CR 9-6 commit message discipline ✅ APPLIED**: `git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention 결정 wire
- **CR 11-3 honest-DEFER discipline ✅ APPLIED**: 114번째 epic 연속 정직 회복 결정 wire (D-1-1-DEFER-* + D-EPIC-16-REVIEW-DEFER-* + D-PHASE-4-DR-DEFER-* + D-EPIC-17-WIRE-DEFER-T2-T3-UI + D-RETENTION-1 + D-OBSERVABILITY-1 + D-PERFORMANCE-1 + D-CHAOS-1 + D-SLO-1 + D-FINOPS-1 + D-FINOPS-2 모두 ✅ ALL RESOLVED 보존 + D-FINOPS-3 honestly ✅ DEFER 보존 진입 결정 wire)
- **CR 11-4 D-001~D-005 + P-015 lessons carry ✅ APPLIED**: dry-run mode UI 진입 시 frontend territory 정합 sweep 결정 wire + ko-KR.json SSOT only + vitest RTL render discipline + owner-only RBAC + unknown state reject + ko-KR.json SSOT drift detector 결정 wire
- **CR 12-1 L4 industry-agnostic capability ✅ APPLIED**: FINOPS_FORECASTING_CAPACITY_PLANNING industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire + capability matrix v1.38 EXTENSION 결정 wire
- **CR 12-5 D-14 typed exception envelope ✅ APPLIED**: 14 NEW typed exception classes (ForecastDefinitionInvalidError(400) + ForecastScopeInvalidError(400) + ForecastHistoryUnavailableError(422) + ForecastEngineError(500) + ForecastModelTrainingError(500) + ForecastSeasonalityDetectionError(500) + CapacityHeadroomAnalysisError(500) + CapacityThresholdBreachError(500) + CapacityMetricUnavailableError(404) + BudgetBurnRateProjectionError(500) + BudgetOverrunPredictionError(500) + ForecastAccuracyTrackingError(500) + ModelRetrainingTriggerError(500) + ModelPerformanceDegradationError(500)) 결정 wire + apps/api/main.py EXTENSION 결정 wire
- **CR 12-5 D-PARITY-01 inversion ✅ APPLIED**: Python FastAPI backend forecast_definition.py + forecast_engine.py TypedDict ↔ TypeScript Next.js frontend finops-forecast-client.ts interface parity 결정 wire + vitest CR 12-5 D-PARITY-01 검증 결정 wire
- **CR 12-5 D-GATE-01 inversion ✅ APPLIED**: FINOPS_FORECASTING_CAPACITY_PLANNING capability gate per-tenant on/off + owner-only RBAC AD-22 결정 wire + gate 적용 대상 명시 결정 wire
- **A19 cohesion pattern 9 surface EXTENSION PASS ✅**: FinOps Forecasting & Capacity Planning surface NEW = F29.1~F29.8 FinOps Forecasting & Capacity Planning territory 결정 wire + spec surface EXTENSION + test surface EXTENSION + docs surface EXTENSION 결정 wire
- **A36 SDR 검증 4-step 자동 적용 ✅**: commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS 결정 wire
- **AD-14 stack pin ✅ APPLIED**: statsmodels==0.14.1 + prophet==1.1.5 + tensorflow==2.15.0 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 + Recharts 2.12.7 (Phase 12 wire sklearn==1.4.0 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 + Recharts 2.12.7 EXTENSION 결정 wire + Phase 11 wire pandas + reportlab + jinja2 + openpyxl + pdfkit + weasyprint + python-magic EXTENSION 결정 wire)
- **AD-22 owner-only RBAC ✅ APPLIED**: forecast definition update + forecast generation + capacity headroom analyze + budget burn-rate projection + model retraining trigger 모두 owner-only RBAC AD-22 + Epic 12 2FA 챌린지 보존 결정 wire
- **NFR4 PII minimization ✅ PRESERVED**: forecast/capacity data 는 사업 metric + cost amount 만 포함, PII 미포함 결정 wire

## Architecture Alignment (cj-style ALLOWED sweep — Phase 12 wire 정합)

**ALLOWED_SERVICE_SUBMODULES sweep CR 11-3 D-2 verbatim** (Phase 5 wire `f093f8c` + Phase 7 wire `59b56cd` + Phase 8 wire `60d4ea1` + Phase 9 wire `e7670e1` + Phase 10 wire `ac5d6c5` + Phase 11 wire `e020ad0` + Phase 12 wire `f3c0e63` 정합):

### Backend (FastAPI, Python 3.12)
- ✅ `apps/api/modules/finops/` (MODIFIED EXTENSION): `forecast_definition.py` + `forecast_engine.py` + `capacity_headroom.py` + `budget_burnrate.py` + `forecast_accuracy_tracker.py` + `forecast_model_registry.py` + `__init__.py` EXTENSION + `serializers.py` EXTENSION
- ✅ `apps/api/core/capability.py` (MODIFIED): Capability.FINOPS_FORECASTING_CAPACITY_PLANNING enum EXTENSION + 4 INDUSTRY_CAPABILITIES EXTENSION
- ✅ `apps/api/dependencies/capability.py` (MODIFIED): require_finops_forecast EXTENSION
- ✅ `apps/api/core/audit_action.py` (MODIFIED): ActionClass.FINOPS_FORECAST + FinopsForecastAction Literal 7 NEW + _ActionRegistry FINOPS_FORECAST entry 1 신규 등록 + __all__ EXTENSION
- ✅ `apps/api/core/errors.py` (MODIFIED): 14 NEW typed exception classes CR 12-5 D-14 verbatim
- ✅ `apps/api/alembic/versions/0045_phase_13_forecasting.py` (NEW): 5 tables + indexes + RLS policies
- ✅ `apps/api/main.py` (MODIFIED): /admin/finops/forecast/* endpoints EXTENSION (CR 1-1 RSC boundary 적용)

### Frontend (Next.js 15.x, TypeScript 5.x)
- ✅ `apps/web/app/[locale]/(dashboard)/admin/finops/forecast/page.tsx` (NEW): RSC + finops forecast dashboard
- ✅ `apps/web/app/[locale]/(dashboard)/admin/finops/forecast/layout.tsx` (NEW): RTL section wrapper
- ✅ `apps/web/components/finops/FinopsForecastDashboardPanel.tsx` (NEW): 5 components (ForecastHorizonSelector + ForecastChart + CapacityHeadroomGauge + BudgetBurnRatePanel + ForecastAccuracyPanel)
- ✅ `apps/web/lib/finops-forecast/finops-forecast-client.ts` (NEW): ForecastDefinition + ForecastResult + CapacityHeadroomReport + BurnRateProjection + ForecastAccuracyReport TypedDict CR 12-5 D-PARITY-01 verbatim + 5 fetch wrappers + FinopsForecastApiError class
- ✅ `apps/web/messages/ko-KR.json` (MODIFIED): EXTENSION `finops_forecast.*` namespace ~30 keys 결정 wire

### Tests
- ✅ `tests/api/core/test_phase_13_forecast_definition.py` (NEW): ~6 NEW pytest
- ✅ `tests/api/core/test_phase_13_forecast_engine.py` (NEW): ~8 NEW pytest
- ✅ `tests/api/core/test_phase_13_capacity_headroom.py` (NEW): ~8 NEW pytest
- ✅ `tests/api/core/test_phase_13_budget_burnrate.py` (NEW): ~6 NEW pytest
- ✅ `tests/api/core/test_phase_13_forecast_accuracy_tracker.py` (NEW): ~6 NEW pytest
- ✅ `tests/api/core/test_phase_13_audit_action.py` (NEW): ~7 NEW pytest
- ✅ `tests/integration/test_finops_forecast_tenant_isolation.py` (NEW): multi-tenant isolation CR 0-2 verbatim
- ✅ `tests/integration/test_capability_matrix_v1_38_drift.py` (NEW): 10 NEW pytest cases
- ✅ `apps/web/__tests__/finops-forecast/finops-forecast-dashboard.test.tsx` (NEW): ~4 NEW vitest
- ✅ `apps/web/__tests__/i18n/finops-forecast-i18n-ssot.test.ts` (NEW): SSOT drift NFR18 ko-KR 정합

### Docs
- ✅ `docs/finops-forecast-capacity-planning.md` (NEW): ~+200 LOC 14 sections runbook 결정 wire
- ✅ `docs/capability-matrix.md` (MODIFIED): v1.37 → v1.38 EXTENSION

## Files Affected (estimate)

- **~18 NEW**: `apps/api/modules/finops/{forecast_definition,forecast_engine,capacity_headroom,budget_burnrate,forecast_accuracy_tracker,forecast_model_registry}.py` (6 files) + `apps/api/alembic/versions/0045_phase_13_forecasting.py` + `apps/web/app/[locale]/(dashboard)/admin/finops/forecast/{page,layout}.tsx` (2 files) + `apps/web/components/finops/FinopsForecastDashboardPanel.tsx` + `apps/web/lib/finops-forecast/finops-forecast-client.ts` + tests (8 files) + `docs/finops-forecast-capacity-planning.md`
- **~12 MODIFIED**: `apps/api/core/capability.py` + `apps/api/dependencies/capability.py` + `apps/api/core/audit_action.py` + `apps/api/core/errors.py` + `apps/api/main.py` + `apps/api/modules/finops/__init__.py` + `apps/api/modules/finops/serializers.py` + `apps/web/messages/ko-KR.json` + `docs/capability-matrix.md` + `_bmad-output/implementation-artifacts/sprint-status.yaml` + `tests/integration/conftest.py` + `apps/api/alembic/versions/script.py.mako`
- **Total**: ~30 files atomic single sprint

## Test Coverage

- **~51 NEW pytest PASS 결정 wire**:
  - `tests/api/core/test_phase_13_forecast_definition.py` (6 cases): TypedDict validation + 5 target_metrics 옵션 + 4 horizon_months 옵션 + 4 industries baseline + audit-first INSERT + owner-only RBAC + dry_run default
  - `tests/api/core/test_phase_13_forecast_engine.py` (8 cases): 4 forecast methods + multi-method voting consensus + seasonality detection + STL decomposition + ensemble voting + model_version tracking + audit-first INSERT + typed exception envelope
  - `tests/api/core/test_phase_13_capacity_headroom.py` (8 cases): 3 resource types + 3 saturation levels + critical + warning threshold alerting + audit-first INSERT + typed exception envelope
  - `tests/api/core/test_phase_13_budget_burnrate.py` (6 cases): 4-input formula + 3-level severity routing + ARIMA-based projection + alert deduplication + audit-first INSERT + typed exception envelope
  - `tests/api/core/test_phase_13_forecast_accuracy_tracker.py` (6 cases): MAE + MAPE + RMSE + ensemble vs individual model comparison + model performance degradation detection + model retraining trigger + audit-first INSERT + typed exception envelope
  - `tests/api/core/test_phase_13_audit_action.py` (7 cases): 7 NEW audit log entries + ActionClass.FINOPS_FORECAST + emit_audit_typed CR 1-1
  - `tests/integration/test_finops_forecast_tenant_isolation.py` (4 cases): cross-tenant isolation + forecast definition isolation + capacity headroom isolation + budget burnrate isolation
  - `tests/integration/test_capability_matrix_v1_38_drift.py` (10 cases): FINOPS_FORECASTING_CAPACITY_PLANNING enum + 4-industry grants + v1.37 + v1.36 + ... preservation
  - **Subtotal**: ~55 NEW pytest PASS

- **~5 NEW vitest PASS 결정 wire**:
  - `apps/web/__tests__/finops-forecast/finops-forecast-dashboard.test.tsx` (4 cases): ForecastChart + CapacityHeadroomGauge + ForecastAccuracyPanel + ForecastHorizonSelector
  - `apps/web/__tests__/i18n/finops-forecast-i18n-ssot.test.ts` (1 cases): ko-KR SSOT drift detection + CR 12-5 D-PARITY-01 verification
  - **Subtotal**: ~5 NEW vitest PASS

- **0 NEW ruff 결정 wire** (apps/api backend 결정 wire + 기존 ruff scoped 0 NEW 정합 보존)
- **0 NEW tsc 결정 wire** (apps/web frontend 결정 wire + 기존 tsc 0 NEW 정합 보존)
- **0 regressions 결정 wire** (3중 게이트 FINAL CLEAN + ruff scoped 0 NEW + pytest 0 NEW failures + vitest 0 NEW failures + tsc 0 NEW errors)

## Notes

- `apps/api/main.py` EXTENSION 시 /admin/finops/forecast/* endpoints EXTENSION + require_finops_forecast dep 적용
- `apps/api/core/errors.py` EXTENSION 시 14 NEW typed exception classes + envelope CR 11-4 P-015 적용
- `apps/api/core/audit_action.py` EXTENSION 시 ActionClass.FINOPS_FORECAST + FinopsForecastAction Literal 7 NEW values + _ActionRegistry FINOPS_FORECAST entry 1 신규 등록
- m21_finops_forecast.finops_forecast_serializers NEW Phase 13 EXTENSION 결정 wire (Phase 12 wire `f3c0e63` m20_finops_anomaly.finops_anomaly_serializers EXTENSION pattern verbatim 미러, wire 시점에 sprint-status.yaml action_items EXTENSION)
- Phase 12 wire `f3c0e63` 의 anomaly detection baseline last 30d/90d/YTD → forward forecast EXTENSION territory 자연스러운 EXTENSION 결정 wire
- Phase 11 wire `e020ad0` 의 showback period selector (current/previous/last 3/6 months/YTD) 의 자연스러운 carry-over chain 결정 wire
- Phase 8 wire `60d4ea1` 의 cost-engine V8 골든 fixture + 12-period benchmark 의 자연스러운 carry-over chain (historical baseline ⇒ forward forecast EXTENSION 12-month prediction with 95% CI + capacity headroom 90일 lookahead + budget burn-rate EXTENSION) 결정 wire
- Phase 10 wire `ac5d6c5` 의 4 SLIs 자연스러운 EXTENSION 결정 wire + Phase 9 wire `e7670e1` chaos_experiment baseline EXTENSION 결정 wire
- Phase 7 wire `59b56cd` observability 의 Prometheus custom metrics + Slack channel EXTENSION 결정 wire + alert routing 정합
- Epic 12 2FA 챌린지 mandatory 결정 wire (forecast definition update + forecast generation + capacity headroom analyze + budget burn-rate projection + model retraining trigger 모두 Epic 12 2FA 챌린지 mandatory)
- AD-22 owner-only RBAC 보존 결정 wire (forecast definition update + forecast generation + capacity headroom analyze + budget burn-rate projection + model retraining trigger 모두 owner-only)
- AD-14 stack pin 결정 wire (statsmodels==0.14.1 + prophet==1.1.5 + tensorflow==2.15.0 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 + Recharts 2.12.7)
- NFR4 PII minimization PRESERVED (forecast/capacity data 는 사업 metric + cost amount 만 포함, PII 미포함)
- 3중 게이트 impact NONE (cj-style 114번째 spec entry 진입 표준 = docs only 변경): ruff scoped 0 NEW + pytest 0 NEW + vitest 0 NEW + tsc 0 NEW
- 8 ACs PRD §F29.1~§F29.8 verbatim → 92 sub-ACs (12+12+12+12+10+10+12+12 = 92 sub-ACs) satisfied pre-flight 정합 sweep 결정 wire

## Cross-References

- Phase 13 PRD entry `d31dfc8` (cj-style 113번째) — FinOps Forecasting & Capacity Planning territory 정합
- Phase 12 close-out retro `3354e83` (cj-style 112번째) — D-FINOPS-3 honestly DEFER 보존 해소
- Phase 12 atomic wire T1~T8 `f3c0e63` (cj-style 111번째) — Cost Anomaly Detection & Budget Alerting territory 정합
- Phase 12 spec entry `8c5f374` (cj-style 110번째)
- Phase 12 PRD entry `344c7eb` (cj-style 109번째)
- Phase 11 close-out retro `80df15b` (cj-style 108번째)
- Phase 11 atomic wire T1~T8 `e020ad0` (cj-style 107번째) — FinOps Showback / Chargeback territory 정합
- Phase 11 spec entry `82c93a8` (cj-style 106번째)
- Phase 11 PRD entry `16d7698` (cj-style 105번째)
- Phase 10 close-out retro `733d428` (cj-style 104번째)
- Phase 10 wire `ac5d6c5` (cj-style 103번째) — SLO Engineering / Error Budget Management territory 정합
- Phase 9 wire `e7670e1` (cj-style 99번째) — Chaos Engineering / Game Day territory 정합
- Phase 8 wire `60d4ea1` (cj-style 95번째) — cost-engine V8 골든 fixture + 12-period benchmark EXTENSION
- Phase 7 wire `59b56cd` (cj-style 91번째) — observability 정합
- Phase 5 wire `f093f8c` (cj-style 75번째) — multi-region failover + replication_lag 정합
- Epic 12 2FA 게이트 `a63646c` — Epic 12 2FA 챌린지 mandatory
- Epic 1 carry-over (auth) — onboarding/industry 보존
- AD-14 stack pin — statsmodels==0.14.1 + prophet==1.1.5 + tensorflow==2.15.0 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 + Recharts 2.12.7
- AD-22 owner-only RBAC — forecast definition update + forecast generation + capacity headroom analyze + budget burn-rate projection + model retraining trigger
- AD-40 FinOps Forecasting & Capacity Planning 신규
- NFR18 ko-KR — SSOT only invariant
- NFR4 PII minimization — forecast/capacity data PII 미포함
- CR 0-2 RLS lesson, CR 1-1 audit-first INSERT, CR 4-3/4-4 lessons carry, CR 1-1 ContextVar, CR 1-1 RSC boundary, CR 9-6 commit message, CR 11-3 honest-DEFER, CR 11-4 D-001~D-005 + P-015, CR 12-1 L4 industry-agnostic capability, CR 12-5 D-14 envelope, CR 12-5 D-PARITY-01, CR 12-5 D-GATE-01, A19 cohesion 9 surface EXTENSION PASS, A36 SDR 검증 4-step 자동 적용
- m21_finops_forecast.finops_forecast_serializers NEW Phase 13 EXTENSION 결정 wire (wire 시점에)

## 결정 wire 일자

2026-08-24 (KST)

## next (wire 진입 시)

옵션 (a) Phase 13 bmad-dev-story atomic wire T1~T8 진입 (cj-style 115번째 wire 진입 시점) 결정 wire 진입 / 옵션 (b) Phase 13 close-out retro 진입 (cj-style 116번째) / 옵션 (c) Phase 14+ 진입 / 옵션 (d) Epic 18+ 진입 / 옵션 (e) D-DEFER-* follow-up 진입 결정 wire 보류.
