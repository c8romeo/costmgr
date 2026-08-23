---
baseline_commit: 344c7eb
status: ready-for-dev
cj_style_entry_point: 110
story_key: phase-12-finops-anomaly-budget-alert-wire
---

# Phase 12 FinOps Cost Anomaly Detection & Budget Alerting wire spec (cj-style 110번째 epic 연속 정직 회복)

## Story

**As a** finance team / FinOps analyst / department cost center owner / tenant admin / enterprise onboarding lead / compliance officer
**I want** FinOps Cost Anomaly Detection & Budget Alerting territory 결정 wire (anomaly detection DSL `AnomalyDefinition` TypedDict 8 fields + 4 detection methods z-score + IQR + EWMA + isolation forest + multi-method voting consensus + budget definition DSL `BudgetDefinition` TypedDict 12 fields + budget_period monthly/quarterly/yearly + budget_scope tenant/department/cost_center/product_line + budget_alert real-time consumption tracking + 3 thresholds 80% warning + 90% critical + 100% exceeded + Slack + PagerDuty + Email alert routing + forecast accuracy tracking MAE + MAPE + RMSE + capability matrix v1.37 EXTENSION FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT)
**so that** Phase 11 wire `e020ad0` FinOps Showback/Chargeback territory 의 natural backend DETECTION & ALERTING LAYER EXTENSION 결정 wire 진입 (showback baseline 대비 deviation 감지 = cost anomaly detection + chargeback 한도 초과 알림 = budget alert + statistical + ML hybrid detection methods + alert routing/escalation + AD-39 Cost Anomaly Detection & Budget Alerting 신규 + Phase 8 wire `60d4ea1` 의 cost-engine 12-period benchmark 의 자연스러운 carry-over chain = historical baseline last 30d + last 90d + YTD + statistical model training + forecast deviation tracking EXTENSION + Epic 12 2FA 챌린지 보존 + AD-22 owner-only RBAC 보존 + D-FINOPS-2 honestly DEFER 보존 진입 결정 wire + Phase 11 close-out retro `80df15b` §12 verbatim 해소 결정 wire 보존).

## Context

cj-style Phase 12 2번째 진입점 (cj-style 110번째) 진입 결정 wire 진입 완료:
- Phase 12 PRD entry `344c7eb` (cj-style 109번째) DONE 진입 정합 보존
- Phase 11 close-out retro `80df15b` (cj-style 108번째) + Phase 11 atomic wire T1~T8 `e020ad0` (cj-style 107번째) + Phase 11 spec entry `82c93a8` (cj-style 106번째) + Phase 11 PRD entry `16d7698` (cj-style 105번째) + Phase 10 close-out retro `733d428` (cj-style 104번째) + Phase 10 atomic wire T1~T8 `ac5d6c5` (cj-style 103번째) 결정 wire 모두 DONE 진입 정합 보존
- D-FINOPS-2 honestly DEFER 보존 진입 결정 wire (Phase 11 close-out retro §12 verbatim 해소 + Phase 12 PRD entry 진입 시점에 1 NEW 결정 wire)
- D-FINOPS-1 ✅ RESOLVED 보존 진입 결정 wire
- D-SLO-1 ✅ RESOLVED 보존 진입 결정 wire
- D-CHAOS-1 ✅ RESOLVED 보존 진입 결정 wire
- D-PERFORMANCE-1 ✅ RESOLVED 보존 진입 결정 wire
- D-OBSERVABILITY-1 ✅ RESOLVED 보존 진입 결정 wire
- Phase 12 PRD entry 의 8 ACs §F28.1~§F28.8 verbatim 결정 wire 보존
- Capability matrix v1.36 → v1.37 EXTENSION FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT 2 NEW rows 결정 wire (industry-agnostic 4-industry grants ✅/✅/✅/✅ CR 12-1 L4 precedent 미러)
- AD-39 Cost Anomaly Detection & Budget Alerting 신규 결정 wire 진입 (a)~(g) 7 sub-decisions

## 8 ACs (PRD §F28.1~§F28.8 verbatim) → 96 detailed sub-ACs

### §F28.1 anomaly detection DSL (12 sub-ACs)
- F28.1-1 `apps/api/modules/finops/anomaly_detection.py` NEW (~+150 LOC + `detect_anomaly(tenant_id, period_key, dimension, threshold_method)` builder + AST 5 levels + parser 검증 3 layer 결정 wire)
- F28.1-2 4 detection methods 결정 wire (z_score + IQR + EWMA + isolation_forest + multi-method voting consensus 3 of 4 agree = anomaly confirmed + sklearn==1.4.0 AD-14 stack pin 결정 wire)
- F28.1-3 5 dimension 옵션 결정 wire (department + cost_center + product_line + service + tenant_total + per-tenant override EXTENSION)
- F28.1-4 3 baseline windows 결정 wire (last 30d + last 90d + YTD + calendar arithmetic 결정 + leap year/month boundary 안전)
- F28.1-5 `ANOMALY_THRESHOLD_DEFAULTS` constants 결정 wire (z_score threshold default 3.0 + IQR k default 1.5 + EWMA λ default 0.3 + isolation_forest contamination default 0.1)
- F28.1-6 4 industries baseline industry-agnostic 결정 wire (manufacturing + service + manufacturing_service + manufacturing_service_other 모두 anomaly detection 가능 + per-tenant override EXTENSION + Phase 11 wire `e020ad0` FINOPS_SHOWBACK + FINOPS_CHARGEBACK 4-industry grants ✅/✅/✅/✅ pattern verbatim 미러)
- F28.1-7 anomaly detection pure validator CR 11-4 P-015 verbatim 결정 wire (`parse_anomaly_definition(tenant_id, payload) -> AnomalyDefinition` + 6 validation rules + `AnomalyDefinitionInvalidError(400)` CR 12-5 D-14 envelope)
- F28.1-8 audit-first INSERT `anomaly_detected` 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_ANOMALY 신규 정의 + emit_audit_typed BEFORE anomaly detection + per-tenant RLS 자동 적용 + multi-tenant isolation test)
- F28.1-9 typed exception envelope CR 12-5 D-14 verbatim 결정 wire (3 NEW typed exception classes: `AnomalyDefinitionInvalidError(400)` + `AnomalyDetectionError(500)` + `AnomalyBaselineUnavailableError(404)`)
- F28.1-10 RLS 자동 적용 CR 0-2 verbatim 결정 wire (phase_12_finops_anomaly + phase_12_finops_anomaly_baseline + phase_12_finops_anomaly_preview 3 tables 모두 RLS + tenant_id selector + cross-tenant isolation 검증)
- F28.1-11 dry-run mode `--finops-anomaly-dry-run` CLI flag 결정 wire (dry-run 시 actual anomaly detection skip + anomaly preview phase_12_finops_anomaly_preview table alembic 0044 신규 + audit-first INSERT `anomaly_dry_run_executed` CR 1-1 verbatim)
- F28.1-12 V8 determinism byte-identical 테스트 결정 wire (Phase 8 wire `60d4ea1` cost-engine V8 골든 fixture pattern verbatim 미러 + tenant-scoped result_hash + golden_diff detector EXTENSION)

### §F28.2 budget definition DSL (12 sub-ACs)
- F28.2-1 `apps/api/modules/finops/budget_definition.py` NEW (~+150 LOC + `define_budget(tenant_id, period_key, scope, scope_id, amount)` builder + AST 6 levels + parser 검증 3 layer 결정 wire)
- F28.2-2 budget_period enum 결정 wire (monthly + quarterly + yearly + per-tenant override EXTENSION + tenant_settings.budget_period JSONB column)
- F28.2-3 budget_scope enum 결정 wire (tenant + department + cost_center + product_line + scope_id validation CR 0-2 RLS verbatim)
- F28.2-4 budget_amount NUMERIC(20, 2) + currency KRW default 결정 wire (Phase 11 wire `e020ad0` chargeback_amount format verbatim 미러 + ISO 4217 currency code + per-tenant currency_code EXTENSION)
- F28.2-5 alert_thresholds TypedDict 결정 wire (warning 80% + critical 90% + exceeded 100% + per-tenant override EXTENSION + tenant_settings.alert_thresholds JSONB column)
- F28.2-6 `apps/api/modules/finops/budget_definition.py` decision wire (`parse_budget_definition(tenant_id, payload) -> BudgetDefinition` + 6 validation rules + `BudgetDefinitionInvalidError(400)` CR 12-5 D-14 envelope + `BudgetScopeInvalidError(404)` + `BudgetAmountInvalidError(400)`)
- F28.2-7 audit-first INSERT `budget_definition_updated` 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_BUDGET 신규 정의 + emit_audit_typed BEFORE budget definition update + per-tenant RLS 자동 적용 + multi-tenant isolation test)
- F28.2-8 typed exception envelope CR 12-5 D-14 verbatim 결정 wire (3 NEW typed exception classes: `BudgetDefinitionInvalidError(400)` + `BudgetScopeInvalidError(404)` + `BudgetAmountInvalidError(400)`)
- F28.2-9 4 industries baseline industry-agnostic 결정 wire (Phase 11 wire `e020ad0` FINOPS_SHOWBACK + FINOPS_CHARGEBACK 4-industry grants ✅/✅/✅/✅ pattern verbatim 미러)
- F28.2-10 RLS 자동 적용 CR 0-2 verbatim + UNIQUE constraint 결정 wire (phase_12_finops_budget + phase_12_finops_budget_consumption + phase_12_finops_budget_preview 3 tables 모두 RLS + UNIQUE constraint `(tenant_id, period_key, scope, scope_id)`)
- F28.2-11 budget_period 만료 처리 auto-expire 결정 wire (cron KST 매시간 00분 UTC 15:00 + status enum active/paused/expired + auto status transition active → expired at period end + audit-first INSERT `budget_period_expired` CR 1-1 verbatim)
- F28.2-12 dry-run mode `--finops-budget-dry-run` CLI flag 결정 wire (dry-run 시 actual budget definition skip + budget preview phase_12_finops_budget_preview table alembic 0044 신규 + audit-first INSERT `budget_dry_run_executed` CR 1-1 verbatim)

### §F28.3 anomaly detection engine + alert routing (12 sub-ACs)
- F28.3-1 `apps/api/modules/finops/anomaly_detection_engine.py` NEW (~+180 LOC + `detect_anomalies(tenant_id, period_key, dimension) -> List[AnomalyResult]` + 4 detection methods parallel run + multi-method voting consensus 결정 wire + CR 12-5 D-PARITY-01 verbatim)
- F28.3-2 `AnomalyResult` TypedDict 14 fields 결정 wire (anomaly_id + tenant_id + period_key + dimension + dimension_value + observed_value + expected_value + deviation_pct + z_score + severity enum warning/critical + detection_method enum z_score/iqr/ewma/isolation_forest + detected_at + trace_id + confirmed_by_consensus)
- F28.3-3 false positive suppression 결정 wire (require 3 consecutive periods 동일 anomaly + consecutive_periods_required default 3 + per-tenant override EXTENSION)
- F28.3-4 Slack webhook integration `#bizup-finops-alerts` channel 결정 wire (AD-14 slack-sdk==3.23.0 stack pin + audit-first INSERT `alert_sent` CR 1-1 verbatim)
- F28.3-5 PagerDuty integration `pd_anomaly_critical` service 결정 wire (AD-14 pdpyras==5.2.0 stack pin + audit-first INSERT `alert_sent` CR 1-1 verbatim)
- F28.3-6 alert routing 결정 wire (warning → Slack only / critical → Slack + PagerDuty / exceeded → Slack + PagerDuty + Email)
- F28.3-7 audit-first INSERT `alert_sent` 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_ANOMALY + emit_audit_typed BEFORE alert send + per-tenant RLS 자동 적용)
- F28.3-8 alert deduplication 결정 wire (1시간 이내 중복 skip + alert_dedup_window_seconds default 3600 + per-tenant override EXTENSION)
- F28.3-9 isolation_forest model 결정 wire (sklearn==1.4.0 AD-14 stack pin + per-tenant isolation_forest model pickle storage + retraining cron KST 매주 일요일 03:00 UTC 18:00 + MAPE > 20% for 3 consecutive periods trigger retraining)
- F28.3-10 EWMA 모델 λ 0.3 default 결정 wire (EWMA λ default 0.3 + per-tenant override EXTENSION + tenant_settings.ewma_lambda JSONB column)
- F28.3-11 z-score + IQR 모델 결정 wire (z_score threshold default 3.0 + IQR k default 1.5 + 4 layer defense 결정 wire: syntax + semantic + tenant-scope RLS + baseline data availability)
- F28.3-12 typed exception envelope CR 12-5 D-14 verbatim 결정 wire (4 NEW typed exception classes: `AlertRoutingError(500)` + `AlertChannelUnavailableError(503)` + `SlackAPIError(502)` + `PagerDutyAPIError(502)`)

### §F28.4 budget overrun alerts (12 sub-ACs)
- F28.4-1 `apps/api/modules/finops/budget_alert.py` NEW (~+150 LOC + `check_budget_alerts(tenant_id, period_key) -> List[BudgetAlertResult]` 결정 wire + CR 12-5 D-PARITY-01 verbatim)
- F28.4-2 `BudgetAlertResult` TypedDict 11 fields 결정 wire (alert_id + tenant_id + period_key + budget_id + budget_amount + actual_amount + consumption_pct + severity enum warning/critical/exceeded + alert_channels + sent_at + trace_id)
- F28.4-3 real-time consumption tracking + 5초 lag 결정 wire (per-chargeback INSERT trigger + Phase 11 wire `e020ad0` phase_11_finops_chargeback table EXTENSION + consumption_update_lag default 5s)
- F28.4-4 threshold-based alerting 결정 wire (80% warning + 90% critical + 100% exceeded + threshold_validation Phase 11 wire `e020ad0` FINOPS_CHARGEBACK 패턴 verbatim)
- F28.4-5 audit-first INSERT `budget_threshold_exceeded` 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_BUDGET + emit_audit_typed BEFORE budget alert + per-tenant RLS 자동 적용)
- F28.4-6 audit-first INSERT `budget_alert_sent` 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_BUDGET + emit_audit_typed BEFORE alert send + per-tenant RLS 자동 적용)
- F28.4-7 alert deduplication 결정 wire (24시간 이내 중복 skip + alert_dedup_window_seconds default 86400 + per-tenant override EXTENSION)
- F28.4-8 budget overrun prediction 결정 wire (linear extrapolation + predicted_overrun_pct > 110% trigger warning alert + audit-first INSERT `budget_overrun_predicted` CR 1-1 verbatim)
- F28.4-9 Slack webhook `#bizup-finops-budget-alerts` channel 결정 wire (AD-14 slack-sdk==3.23.0 stack pin + Phase 11 wire `e020ad0` Phase 7 wire `59b56cd` Slack channel 결정 wire verbatim 미러)
- F28.4-10 PagerDuty integration `pd_budget_exceeded` service 결정 wire (AD-14 pdpyras==5.2.0 stack pin + audit-first INSERT `alert_sent` CR 1-1 verbatim)
- F28.4-11 email notification sendgrid==6.11.0 AD-14 stack pin 결정 wire (NFR4 PII minimization ✅ PRESERVED + tenant owner email + ko-KR.json `finops_budget_email_subject` EXTENSION 결정 wire)
- F28.4-12 typed exception envelope CR 12-5 D-14 verbatim 결정 wire (2 NEW typed exception classes: `BudgetAlertError(500)` + `BudgetConsumptionUpdateError(500)`)

### §F28.5 forecast accuracy tracking (10 sub-ACs)
- F28.5-1 `apps/api/modules/finops/forecast_accuracy.py` NEW (~+120 LOC + `track_forecast_deviation(tenant_id, period_key) -> ForecastAccuracyReport` 결정 wire)
- F28.5-2 `ForecastAccuracyReport` TypedDict 9 fields 결정 wire (tenant_id + period_key + predicted_amount + actual_amount + deviation_pct + MAE + MAPE + RMSE + model_version + JSONB metadata)
- F28.5-3 MAE (Mean Absolute Error) 결정 wire (MAE = mean(|actual - predicted|) + banker's rounding 적용 CR 5-1 verbatim)
- F28.5-4 MAPE (Mean Absolute Percentage Error) < 10% high accuracy 결정 wire (MAPE = mean(|actual - predicted| / actual) * 100 + accuracy threshold 10%)
- F28.5-5 RMSE (Root Mean Squared Error) 결정 wire (RMSE = sqrt(mean((actual - predicted)^2)) + banker's rounding 적용 CR 5-1 verbatim)
- F28.5-6 model performance degradation detection 결정 wire (MAPE > 20% for 3 consecutive periods → trigger retraining + audit-first INSERT `model_retraining_triggered` CR 1-1 verbatim)
- F28.5-7 audit-first INSERT `forecast_deviation` 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_ANOMALY + emit_audit_typed BEFORE forecast tracking + per-tenant RLS 자동 적용)
- F28.5-8 predicted_amount source 결정 wire (phase_11_finops_showback.showback_generated event Phase 11 wire `e020ad0` EXTENSION + LISTEN/NOTIFY Phase 11 wire `cost_engine_cache` channel EXTENSION)
- F28.5-9 model_version tracking 결정 wire (semantic versioning + JSONB metadata + phase_12_finops_anomaly.model_version column EXTENSION)
- F28.5-10 typed exception envelope CR 12-5 D-14 verbatim 결정 wire (2 NEW typed exception classes: `ForecastAccuracyError(500)` + `ModelVersionInvalidError(400)`)

### §F28.6 anomaly detection dashboard UI (10 sub-ACs)
- F28.6-1 `apps/web/app/[locale]/(dashboard)/admin/finops/anomaly/page.tsx` NEW (~+150 LOC + 4 components 결정 wire: AnomalyDetectionChart + AnomalyDetectionMethodSelector + AnomalyDetectionThresholdSlider + BudgetAlertPanel + owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 보존)
- F28.6-2 `AnomalyDetectionChart` component 결정 wire (Recharts 2.12.7 AD-14 stack pin + LineChart anomaly 시점 visualization + observed_value + expected_value 2 lines + deviation_pct tooltip 결정 + tenant currency_code 적용 + ko-KR.json `finops_anomaly_chart_label` EXTENSION + RTL render discipline)
- F28.6-3 `AnomalyDetectionMethodSelector` component 결정 wire (4 detection methods radio button 결정 wire: z_score + IQR + EWMA + isolation_forest + onChange handler + ko-KR.json `finops_anomaly_method_label` EXTENSION)
- F28.6-4 `AnomalyDetectionThresholdSlider` component 결정 wire (4 sliders 결정 wire: z_score threshold + IQR k + EWMA λ + isolation_forest contamination + onChange handler + ko-KR.json `finops_anomaly_threshold_label` EXTENSION)
- F28.6-5 `BudgetAlertPanel` component 결정 wire (CRUD + 실시간 consumption 시각화 + 80% warning yellow + 90% critical orange + 100% exceeded red 결정 wire + ko-KR.json `finops_budget_alert_label` EXTENSION)
- F28.6-6 ko-KR.json `finops_anomaly.*` namespace EXTENSION 결정 wire (~25 keys CR 11-4 D-002 verbatim SSOT 결정 wire: finops_anomaly_dashboard_title + finops_anomaly_method_label + finops_anomaly_threshold_label + finops_anomaly_chart_label + finops_anomaly_severity_label + finops_anomaly_alert_sent_label + finops_anomaly_budget_alert_label + finops_anomaly_warning_label + finops_anomaly_critical_label + finops_anomaly_exceeded_label + finops_anomaly_detection_method_zscore + finops_anomaly_detection_method_iqr + finops_anomaly_detection_method_ewma + finops_anomaly_detection_method_isoforest + finops_anomaly_budget_period_monthly + finops_anomaly_budget_period_quarterly + finops_anomaly_budget_period_yearly + finops_anomaly_budget_scope_tenant + finops_anomaly_budget_scope_department + finops_anomaly_budget_scope_cost_center + finops_anomaly_budget_scope_product_line + loading_finops_anomaly + error_finops_anomaly_failed + empty_state + owner_only_label)
- F28.6-7 ARIA labels WCAG 2.1 AA + Epic 12 2FA 챌린지 보존 결정 wire (ko-KR inline ARIA + i18n SSOT + keyboard navigation Tab + Enter + Arrow keys + screen reader 지원 + Phase 12 Epic 1 UX v1.0 locked decision Dark MVP / WCAG AA / Professional / ko-KR verbatim 보존)
- F28.6-8 toast notification 결정 wire (warning yellow / critical red / exceeded purple + duration 5s default + ko-KR toast EXTENSION + ARIA live region polite)
- F28.6-9 Vitest RTL render discipline CR 11-4 D-003 verbatim 적용 결정 wire (Phase 11 wire `e020ad0` finops-dashboard.test.tsx pattern verbatim 미러)
- F28.6-10 FinOps anomaly dashboard parity CR 12-5 D-PARITY-01 결정 wire (Python FastAPI backend anomaly_detection.py TypedDict ↔ TypeScript Next.js frontend finops-anomaly-client.ts interface parity + vitest 검증)

### §F28.7 Capability matrix v1.37 EXTENSION (12 sub-ACs)
- F28.7-1 Capability matrix v1.36 → v1.37 EXTENSION 결정 wire (2 NEW rows FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT industry-agnostic 4-industry grants ✅/✅/✅/✅ CR 12-1 L4 precedent 미러)
- F28.7-2 `apps/api/core/capability.py` MODIFIED 결정 wire (Capability.FINOPS_ANOMALY_DETECTION = "finops_anomaly_detection" + Capability.FINOPS_BUDGET_ALERT = "finops_budget_alert" 2 NEW enum + 4 `_INDUSTRY_CAPABILITIES` blocks EXTENSION industry-agnostic ✅/✅/✅/✅)
- F28.7-3 `apps/api/dependencies/capability.py` MODIFIED 결정 wire (require_finops_anomaly_detection + require_finops_budget_alert 2 NEW dep + `__all__` EXTENSION)
- F28.7-4 `docs/capability-matrix.md` MODIFIED 결정 wire (capability matrix v1.36 → v1.37 EXTENSION + 2 NEW rows FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT industry-agnostic 4-industry grants ✅/✅/✅/✅ + FINOPS_ANOMALY + FINOPS_BUDGET section 신규 추가)
- F28.7-5 `apps/api/modules/finops/__init__.py` MODIFIED 결정 wire (Phase 11 wire `e020ad0` m19_finops EXTENSION + m20_finops_anomaly 신규 module 결정 wire + finops_serializers EXTENSION + m20_finops_anomaly.finops_anomaly_serializers NEW 결정 wire)
- F28.7-6 미허용 tenant 의 anomaly detection 진입 차단 결정 wire (require_finops_anomaly_detection dep + capability gate per-tenant on/off + 403 Forbidden + FORBIDDEN_KO message 결정 wire ("FinOps Anomaly Detection capability 미허용 tenant") + Epic 12 2FA 챌린지 보존 + AD-22 owner-only RBAC 정합)
- F28.7-7 미허용 tenant 의 budget alert 진입 차단 결정 wire (require_finops_budget_alert dep + capability gate per-tenant on/off + 403 Forbidden + FORBIDDEN_KO message 결정 wire ("FinOps Budget Alert capability 미허용 tenant") + Epic 12 2FA 챌린지 보존 + AD-22 owner-only RBAC 정합)
- F28.7-8 drift detector 10 NEW pytest cases 결정 wire (`tests/integration/test_capability_matrix_v1_37_drift.py` NEW + Phase 11 wire `e020ad0` `test_capability_matrix_v1_36_drift.py` 패턴 verbatim 미러)
- F28.7-9 m20_finops_anomaly module 결정 wire (apps/api/modules/finops/__init__.py EXTENSION + m20_finops_anomaly.finops_anomaly_serializers NEW 결정 wire + Phase 11 wire `e020ad0` m19_finops.finops_serializers EXTENSION pattern verbatim 미러)
- F28.7-10 SSOT RED→GREEN EXTENSION + A36 SDR 검증 4-step 자동 적용 결정 wire (capability matrix v1.37 신규 2 rows + capability.py EXTENSION 2 NEW enum + require_finops_anomaly_detection + require_finops_budget_alert 2 NEW deps 결정 wire + drift detector EXTENSION)
- F28.7-11 CR 12-1 L4 industry-agnostic capability 결정 wire (FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT 모두 industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire manufacturing + service + manufacturing_service + manufacturing_service_other 모두 허용)
- F28.7-12 capability gate 의 fail-closed 결정 wire (미허용 tenant 의 anomaly detection 진입 차단 + capability matrix v1.37 row 부재 시 fail-closed + Capability enum 부재 시 fail-closed + AD-22 owner-only RBAC 정합 + Epic 12 2FA 챌린지 보존 + NFR4 PII minimization 정합 보존)

### §F28.8 dry-run + Tests + wire scope T1~T8 (12 sub-ACs)
- F28.8-1 dry-run mode 결정 wire (`--finops-anomaly-dry-run` + `--finops-budget-dry-run` CLI flag + anomaly detection dry-run parameter + budget alert dry-run parameter + dry-run 시 actual anomaly detection skip + dry-run 시 actual budget alert skip + dry-run 시 actual budget_definition_updated INSERT skip)
- F28.8-2 dry-run 의 preview 결과 결정 wire (phase_12_finops_anomaly_preview + phase_12_finops_budget_preview 2 tables alembic 0044 신규 + preview 결과 ko-KR.json `finops_anomaly_preview_label` + `finops_budget_preview_label` EXTENSION 결정 wire)
- F28.8-3 dry-run 의 CLI flag 결정 wire (`--finops-anomaly-dry-run` + `--finops-budget-dry-run` 2 NEW CLI flag + Phase 11 wire `e020ad0` `--finops-chargeback-dry-run` 패턴 verbatim 미러)
- F28.8-4 tests ~+50 NEW pytest PASS 결정 wire (anomaly_detection_dsl 6 + budget_definition 6 + anomaly_detection_engine 8 + budget_alert 7 + forecast_accuracy 6 + audit_action 7 + capability matrix v1.37 10 = ~50 NEW pytest PASS)
- F28.8-5 vitest tests ~+5 NEW vitest PASS 결정 wire (AnomalyDetectionChart 1 + AnomalyDetectionMethodSelector 1 + AnomalyDetectionThresholdSlider 1 + BudgetAlertPanel 1 + ko-KR SSOT 1 = ~5 NEW vitest PASS)
- F28.8-6 ruff + tsc 0 NEW + SDR drift gate 결정 wire (0 NEW ruff + 0 NEW tsc + 0 regressions + SDR drift gate PASS 결정 wire + A36 SDR 검증 4-step 자동 적용)
- F28.8-7 wire scope T1~T8 결정 wire (~+30-35 files estimate = ~20 NEW + ~12 MODIFIED atomic single sprint)
- F28.8-8 A19 cohesion pattern 9 surface EXTENSION PASS 결정 wire (FinOps anomaly + budget alert surface NEW = F28.1~F28.8 + spec surface EXTENSION + test surface EXTENSION + docs surface EXTENSION)
- F28.8-9 CR lessons applied 14종 결정 wire (CR 0-2 + CR 1-1 + CR 4-3/4-4 + CR 1-1 ContextVar + CR 1-1 RSC boundary + CR 9-6 + CR 11-3 + CR 11-4 + CR 12-1 + CR 12-5 D-14 + CR 12-5 D-PARITY-01 + CR 12-5 D-GATE-01 + A19 cohesion + A36 SDR 검증)
- F28.8-10 D-DEFER-* honestly 결정 wire (D-FINOPS-2 honestly preserved → Phase 12 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire + D-FINOPS-1 ✅ RESOLVED + D-SLO-1 ✅ RESOLVED + D-CHAOS-1 ✅ RESOLVED + D-PERFORMANCE-1 ✅ RESOLVED + D-OBSERVABILITY-1 ✅ RESOLVED + D-RETENTION-1 ✅ RESOLVED + D-EPIC-17-WIRE-DEFER-T2-T3-UI ✅ RESOLVED + D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED + D-EPIC-16-REVIEW-DEFER-2~6 ✅ RESOLVED + D-1-1-DEFER-1/2/3 ✅ RESOLVED 모두 보존)
- F28.8-11 Epic 1 ~ Epic 17 + Phase 3 ~ Phase 11 + 1st release cycle 정합 보존 결정 wire (cj-style 109번째 wire entry 모두 DONE 진입 정합 보존 + Phase 11 close-out retro `80df15b` + Phase 11 atomic wire T1~T8 `e020ad0` + Phase 11 spec entry `82c93a8` + Phase 11 PRD entry `16d7698` 모두 정합)
- F28.8-12 partial wire 시도 0건 + single sprint atomic docs-and-source wire 1 진입점 결정 wire (cj-style 110번째 epic 연속 정직 회복 Phase 12 spec entry atomic docs-only wire 5 files atomic single sprint 결정 wire)

## 8 tasks (T1~T8) + 68 subtasks

### T1: anomaly_detection + anomaly_detection_dsl module (10 subtasks)
- T1.1: `apps/api/modules/finops/anomaly_detection.py` NEW (~+150 LOC + detect_anomaly builder + AST 5 levels + parser 검증 3 layer + 4 industries baseline + per-tenant override EXTENSION + ANOMALY_THRESHOLD_DEFAULTS constants 결정 wire)
- T1.2: 4 detection methods 결정 wire (z_score + IQR + EWMA + isolation_forest + multi-method voting consensus 3 of 4 agree + sklearn==1.4.0 AD-14 stack pin)
- T1.3: 5 dimension 옵션 결정 wire (department + cost_center + product_line + service + tenant_total + per-tenant override EXTENSION)
- T1.4: 3 baseline windows 결정 wire (last 30d + last 90d + YTD + calendar arithmetic 결정)
- T1.5: anomaly detection pure validator CR 11-4 P-015 verbatim 적용 결정 wire (parse_anomaly_definition 함수 + 6 validation rules + AnomalyDefinitionInvalidError(400) CR 12-5 D-14 envelope)
- T1.6: 6 NEW pytest cases 결정 wire (TypedDict validation + 4 detection methods + 5 dimension 옵션 + 3 baseline windows + audit-first INSERT + owner-only RBAC + dry_run default)
- T1.7: anomaly_detection DSL audit-first INSERT `anomaly_detected` 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_ANOMALY + emit_audit_typed BEFORE anomaly detection + per-tenant RLS 자동 적용)
- T1.8: anomaly_detection owner-only RBAC AD-22 결정 wire (anomaly detection 모두 owner-only + Epic 12 2FA 챌린지 + governance_required=True mandatory)
- T1.9: anomaly_detection dry-run mode default 결정 wire (dry_run=True flag + audit-first INSERT `anomaly_dryrun` + no actual anomaly detection)
- T1.10: anomaly_detection CR 0-2 RLS verbatim 적용 결정 wire + tenant_id selector + cross-tenant isolation 검증 + phase_12_finops_anomaly_baseline table 결정 wire

### T2: budget_definition + budget_definition_dsl module (10 subtasks)
- T2.1: `apps/api/modules/finops/budget_definition.py` NEW (~+150 LOC + define_budget builder + AST 6 levels + parser 검증 3 layer + budget_period monthly/quarterly/yearly + budget_scope tenant/department/cost_center/product_line + BUDGET_THRESHOLD_DEFAULTS constants 결정 wire)
- T2.2: budget_period enum 결정 wire (monthly + quarterly + yearly + per-tenant override EXTENSION + tenant_settings.budget_period JSONB column)
- T2.3: budget_scope enum 결정 wire (tenant + department + cost_center + product_line + scope_id validation CR 0-2 RLS verbatim + UNIQUE constraint)
- T2.4: budget_amount NUMERIC(20, 2) + currency KRW default 결정 wire (Phase 11 wire `e020ad0` chargeback_amount format verbatim 미러)
- T2.5: alert_thresholds TypedDict 결정 wire (warning 80% + critical 90% + exceeded 100% + per-tenant override EXTENSION + tenant_settings.alert_thresholds JSONB column)
- T2.6: budget_definition pure validator CR 11-4 P-015 verbatim 적용 결정 wire (parse_budget_definition 함수 + 6 validation rules + BudgetDefinitionInvalidError(400) + BudgetScopeInvalidError(404) + BudgetAmountInvalidError(400) CR 12-5 D-14 envelope)
- T2.7: budget_definition audit-first INSERT `budget_definition_updated` 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_BUDGET + emit_audit_typed BEFORE budget definition update + per-tenant RLS 자동 적용)
- T2.8: budget_period 만료 처리 auto-expire 결정 wire (cron KST 매시간 00분 UTC 15:00 + status enum active/paused/expired + auto status transition active → expired at period end)
- T2.9: budget_definition dry-run mode default 결정 wire (dry_run=True flag + audit-first INSERT `budget_dryrun` + no actual budget definition)
- T2.10: 6 NEW pytest cases 결정 wire (TypedDict validation + budget_period enum + budget_scope enum + alert_thresholds + audit-first INSERT + owner-only RBAC + dry_run default)

### T3: anomaly_detection_engine + alert routing (10 subtasks)
- T3.1: `apps/api/modules/finops/anomaly_detection_engine.py` NEW (~+180 LOC + detect_anomalies 함수 + 4 detection methods parallel run + multi-method voting consensus + CR 12-5 D-PARITY-01 verbatim)
- T3.2: AnomalyResult TypedDict 14 fields 결정 wire (anomaly_id + tenant_id + period_key + dimension + dimension_value + observed_value + expected_value + deviation_pct + z_score + severity enum + detection_method enum + detected_at + trace_id + confirmed_by_consensus)
- T3.3: false positive suppression 결정 wire (require 3 consecutive periods 동일 anomaly + consecutive_periods_required default 3 + per-tenant override EXTENSION)
- T3.4: Slack webhook integration `#bizup-finops-alerts` channel 결정 wire (AD-14 slack-sdk==3.23.0 stack pin + audit-first INSERT `alert_sent`)
- T3.5: PagerDuty integration `pd_anomaly_critical` service 결정 wire (AD-14 pdpyras==5.2.0 stack pin + audit-first INSERT `alert_sent`)
- T3.6: alert routing 결정 wire (warning → Slack only / critical → Slack + PagerDuty / exceeded → Slack + PagerDuty + Email)
- T3.7: alert deduplication 결정 wire (1시간 이내 중복 skip + alert_dedup_window_seconds default 3600 + per-tenant override EXTENSION)
- T3.8: isolation_forest model 결정 wire (sklearn==1.4.0 AD-14 stack pin + per-tenant isolation_forest model pickle storage + retraining cron KST 매주 일요일 03:00)
- T3.9: typed exception envelope CR 12-5 D-14 verbatim 결정 wire (4 NEW typed exception classes: AlertRoutingError + AlertChannelUnavailableError + SlackAPIError + PagerDutyAPIError)
- T3.10: 8 NEW pytest cases 결정 wire (4 detection methods + multi-method voting consensus + false positive suppression + alert routing + alert deduplication + isolation_forest retraining + audit-first INSERT + typed exception envelope)

### T4: budget_alert + forecast_accuracy module (10 subtasks)
- T4.1: `apps/api/modules/finops/budget_alert.py` NEW (~+150 LOC + check_budget_alerts 함수 + CR 12-5 D-PARITY-01 verbatim)
- T4.2: BudgetAlertResult TypedDict 11 fields 결정 wire (alert_id + tenant_id + period_key + budget_id + budget_amount + actual_amount + consumption_pct + severity enum + alert_channels + sent_at + trace_id)
- T4.3: real-time consumption tracking + 5초 lag 결정 wire (per-chargeback INSERT trigger + Phase 11 wire `e020ad0` phase_11_finops_chargeback table EXTENSION + consumption_update_lag default 5s)
- T4.4: threshold-based alerting 결정 wire (80% warning + 90% critical + 100% exceeded)
- T4.5: audit-first INSERT `budget_threshold_exceeded` + `budget_alert_sent` 결정 wire (CR 1-1 verbatim + ActionClass.FINOPS_BUDGET + emit_audit_typed BEFORE/AFTER budget alert)
- T4.6: alert deduplication 결정 wire (24시간 이내 중복 skip + alert_dedup_window_seconds default 86400 + per-tenant override EXTENSION)
- T4.7: budget overrun prediction 결정 wire (linear extrapolation + predicted_overrun_pct > 110% trigger warning alert)
- T4.8: `apps/api/modules/finops/forecast_accuracy.py` NEW (~+120 LOC + track_forecast_deviation 함수 + MAE + MAPE + RMSE metrics + model_version tracking)
- T4.9: model performance degradation detection 결정 wire (MAPE > 20% for 3 consecutive periods → trigger retraining + audit-first INSERT `model_retraining_triggered`)
- T4.10: 7 NEW pytest cases 결정 wire (real-time consumption tracking + threshold-based alerting + alert deduplication + budget overrun prediction + forecast accuracy MAE/MAPE/RMSE + model_version tracking + audit-first INSERT)

### T5: alembic 0044 phase_12_finops_anomaly (8 subtasks)
- T5.1: `apps/api/alembic/versions/0044_phase_12_finops_anomaly.py` NEW (~+250 LOC + 6 tables CREATE + indexes + RLS policies + down_revision "0043_phase_11_finops" 결정 wire)
- T5.2: phase_12_finops_anomaly table 14 columns 결정 wire (anomaly_id UUID PK + tenant_id UUID + period_key TEXT + dimension TEXT enum + dimension_value TEXT + observed_value NUMERIC(20, 2) + expected_value NUMERIC(20, 2) + deviation_pct NUMERIC(8, 4) + z_score NUMERIC(8, 4) + severity TEXT enum warning/critical + detection_method TEXT enum + detected_at TIMESTAMPTZ + trace_id TEXT + confirmed_by_consensus BOOLEAN DEFAULT FALSE)
- T5.3: phase_12_finops_anomaly_baseline table 8 columns 결정 wire (baseline_id UUID PK + tenant_id UUID + period_window TEXT enum last_30d/last_90d/YTD + dimension TEXT + dimension_value TEXT + mean_value NUMERIC(20, 2) + std_dev NUMERIC(20, 2) + sample_count INTEGER)
- T5.4: phase_12_finops_budget table 14 columns 결정 wire (budget_id UUID PK + tenant_id UUID + period_key TEXT + budget_period TEXT enum monthly/quarterly/yearly + scope TEXT enum + scope_id TEXT + amount NUMERIC(20, 2) + currency_code TEXT default 'KRW' + alert_thresholds JSONB + status TEXT enum active/paused/expired + created_at TIMESTAMPTZ + updated_at TIMESTAMPTZ + trace_id TEXT + tenant_id_period_key_scope_scope_id UNIQUE constraint)
- T5.5: phase_12_finops_budget_consumption table 8 columns 결정 wire (consumption_id UUID PK + tenant_id UUID + budget_id UUID + period_key TEXT + actual_amount NUMERIC(20, 2) + consumption_pct NUMERIC(8, 4) + recorded_at TIMESTAMPTZ + trace_id TEXT)
- T5.6: 6 tables RLS policies 결정 wire (CR 0-2 verbatim + tenant_id = current_setting('app.tenant_id')::uuid + Phase 11 wire `e020ad0` phase_11_finops_* table 정합 + Phase 10 wire `ac5d6c5` phase_10_slo_* table 정합)
- T5.7: 6 indexes 결정 wire (idx_phase_12_finops_anomaly_tenant_id_period_key + idx_phase_12_finops_anomaly_dimension + idx_phase_12_finops_anomaly_baseline_tenant_id_period_window + idx_phase_12_finops_budget_tenant_id_period_key + idx_phase_12_finops_budget_scope_scope_id + idx_phase_12_finops_budget_consumption_budget_id)
- T5.8: alembic migration 4 NEW pytest cases + multi-tenant isolation test 결정 wire (`tests/integration/test_finops_anomaly_tenant_isolation.py` NEW + Phase 11 wire `e020ad0` `test_finops_tenant_isolation.py` 패턴 verbatim 미러)

### T6: audit action EXTENSION 7 NEW (8 subtasks)
- T6.1: `apps/api/core/audit_action.py` MODIFIED 결정 wire (ActionClass.FINOPS_ANOMALY + ActionClass.FINOPS_BUDGET 2 NEW class 신규 정의 + FinopsAnomalyAction Literal 4 NEW values + FinopsBudgetAction Literal 4 NEW values + _ActionRegistry FINOPS_ANOMALY + FINOPS_BUDGET entry 신규 7개 등록 + __all__ EXTENSION + AuditAction Union EXTENSION)
- T6.2: ActionClass.FINOPS_ANOMALY = 'finops_anomaly' + ActionClass.FINOPS_BUDGET = 'finops_budget' 신규 정의 결정 wire (CR 12-1 L4 precedent 미러 FINOPS Phase 11 wire + SLO_ENGINEERING Phase 10 wire + CHAOS_ENGINEERING Phase 9 wire + PERFORMANCE_TESTING Phase 8 wire + OBSERVABILITY_TRACES + OBSERVABILITY_METRICS Phase 7 wire pattern verbatim bind)
- T6.3: FinopsAnomalyAction Literal 4 NEW values 결정 wire = `anomaly_detected` + `alert_sent` + `forecast_deviation` + `model_retraining_triggered` (CR 1-1 verbatim 적용)
- T6.4: FinopsBudgetAction Literal 4 NEW values 결정 wire = `budget_definition_updated` + `budget_threshold_exceeded` + `budget_alert_sent` + `budget_period_expired` (CR 1-1 verbatim 적용)
- T6.5: _ActionRegistry FINOPS_ANOMALY + FINOPS_BUDGET entry 신규 7개 등록 결정 wire (resource_table "phase_12_finops_*" + action_class=FINOPS_ANOMALY/FINOPS_BUDGET + 7 NEW actions acceptance + reject)
- T6.6: emit_audit_typed BEFORE/AFTER FinOps Anomaly + Budget event CR 1-1 verbatim 적용 결정 wire (anomaly_detected 의 audit_first INSERT 가 anomaly detection 직전에 실행 + budget_definition_updated AFTER definition 변경 + alert_sent AFTER Slack/PagerDuty send + trace_id propagation + actor_id capture + tenant_id capture)
- T6.7: multi-tenant isolation 결정 wire (7 NEW action 의 tenant_id 가 RLS 와 정합 + cross-tenant audit log leak 방지 결정 wire)
- T6.8: 7 NEW pytest cases 결정 wire (AuditAction Literal 값 검증 + ActionClass.FINOPS_ANOMALY + ActionClass.FINOPS_BUDGET enum value + resource_table + emit_audit_typed BEFORE/AFTER FinOps Anomaly + Budget event CR 1-1 verbatim 적용 + multi-tenant isolation + trace_id propagation + typed exception envelope + dry-run default)

### T7: capability v1.37 EXTENSION + frontend finops anomaly dashboard (8 subtasks)
- T7.1: `apps/api/core/capability.py` MODIFIED 결정 wire (Capability.FINOPS_ANOMALY_DETECTION + Capability.FINOPS_BUDGET_ALERT 2 NEW enum + 4 `_INDUSTRY_CAPABILITIES` blocks EXTENSION industry-agnostic ✅/✅/✅/✅ CR 12-1 L4 precedent 미러)
- T7.2: `apps/api/dependencies/capability.py` MODIFIED 결정 wire (require_finops_anomaly_detection + require_finops_budget_alert 2 NEW dep + __all__ EXTENSION 결정 wire)
- T7.3: capability matrix v1.36 → v1.37 EXTENSION title update + v1.37 changelog entry prepend + 2 NEW rows FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire
- T7.4: `tests/integration/test_capability_matrix_v1_37_drift.py` NEW 10 NEW pytest cases 결정 wire (Capability.FINOPS_ANOMALY_DETECTION + Capability.FINOPS_BUDGET_ALERT enum + 4 industries grants + v1.36 + v1.35 + v1.34 + v1.33 + v1.32 + v1.31 + v1.30 + v1.29 preservation + Phase 5 v1.29 + Epic 16 v1.28 + Epic 17 v1.30 + Phase 6 v1.31 + Phase 7 v1.32 + Phase 8 v1.33 + Phase 9 v1.34 + Phase 10 v1.35 + Phase 11 v1.36 pattern verbatim)
- T7.5: `docs/capability-matrix.md` MODIFIED v1.36 → v1.37 EXTENSION 결정 wire (2 NEW rows FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT industry-agnostic 4-industry grants + FINOPS_ANOMALY + FINOPS_BUDGET section 신규 추가)
- T7.6: 미허용 tenant 의 FinOps Anomaly + Budget 진입 차단 결정 wire (require_finops_anomaly_detection + require_finops_budget_alert dep + capability gate per-tenant on/off)
- T7.7: `apps/web/app/[locale]/(dashboard)/admin/finops/anomaly/page.tsx` NEW (~+150 LOC + 4 components 결정 wire: AnomalyDetectionChart + AnomalyDetectionMethodSelector + AnomalyDetectionThresholdSlider + BudgetAlertPanel + owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 보존)
- T7.8: SSOT RED→GREEN EXTENSION 결정 wire (capability matrix v1.37 신규 2 rows + capability.py EXTENSION 2 NEW enum + require_finops_anomaly_detection + require_finops_budget_alert 2 NEW deps wire + drift detector EXTENSION + frontend finops anomaly dashboard wire)

### T8: atomic commit (4 subtasks)
- T8.1: 3중 게이트 impact NONE 결정 wire (ruff scoped 0 NEW + pytest 0 NEW failures + vitest 0 NEW failures + tsc 0 NEW errors)
- T8.2: A19 cohesion pattern 9 surface EXTENSION PASS 결정 wire (FinOps Anomaly + Budget Alert surface NEW = F28.1~F28.8)
- T8.3: atomic commit via `git commit -F <file>` 결정 wire (CR 9-6 D5 prevention + PowerShell here-string 회피)
- T8.4: sprint-status.yaml `phase-12-spec-entry: backlog → done` transition 결정 wire

## Dev Notes (CR lessons applied 14종)

- **CR 0-2 RLS lesson ✅ APPLIED**: Phase 12 wire 시점에 phase_12_finops_anomaly + phase_12_finops_anomaly_baseline + phase_12_finops_anomaly_preview + phase_12_finops_budget + phase_12_finops_budget_consumption + phase_12_finops_budget_preview 6 tables 모두 RLS 자동 적용 + multi-tenant isolation test 결정 wire + tenant-scoped result_hash 결정 wire + Phase 11 wire `e020ad0` phase_11_finops_* table 정합 + Phase 10 wire `ac5d6c5` phase_10_slo_* table 정합 + Phase 5 wire `f093f8c` phase_5_replication_lag table 정합
- **CR 1-1 audit-first INSERT ✅ APPLIED**: ActionClass.FINOPS_ANOMALY + ActionClass.FINOPS_BUDGET 신규 정의 + 7 NEW audit log entries (`anomaly_detected` + `alert_sent` + `forecast_deviation` + `model_retraining_triggered` + `budget_definition_updated` + `budget_threshold_exceeded` + `budget_alert_sent` + `budget_period_expired`) 결정 wire + emit_audit_typed BEFORE/AFTER FinOps Anomaly + Budget event CR 1-1 verbatim 적용
- **CR 4-3/4-4 lessons carry ✅ APPLIED**: anomaly baseline + budget consumption 30d rolling + golden_diff pattern verbatim 미러 + tenant-scoped result_hash 결정 wire + Epic 8 wire `e117e09` capability drift detector 정합 패턴 + Phase 11 wire `e020ad0` showback baseline result_hash 패턴 verbatim
- **CR 1-1 ContextVar lesson ✅ APPLIED**: trace_id request-scoped ContextVar 바인딩 + 비동기 trace context 보존 CR 1-1 verbatim 적용 + FinOps Anomaly + Budget event 의 trace_id propagation 결정 wire
- **CR 1-1 RSC boundary lesson ✅ APPLIED**: `apps/web/app/[locale]/(dashboard)/admin/finops/anomaly/page.tsx` Client-only + finops anomaly dashboard server-only delegation 결정 wire + CR 1-1 verbatim 적용
- **CR 9-6 commit message discipline ✅ APPLIED**: `git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention 결정 wire
- **CR 11-3 honest-DEFER discipline ✅ APPLIED**: 110번째 epic 연속 정직 회복 결정 wire (D-1-1-DEFER-* + D-EPIC-16-REVIEW-DEFER-* + D-PHASE-4-DR-DEFER-* + D-EPIC-17-WIRE-DEFER-T2-T3-UI + D-RETENTION-1 + D-OBSERVABILITY-1 + D-PERFORMANCE-1 + D-CHAOS-1 + D-SLO-1 + D-FINOPS-1 모두 ✅ ALL RESOLVED 보존 + D-FINOPS-2 honestly ✅ DEFER 보존 진입 결정 wire)
- **CR 11-4 D-001~D-005 + P-015 lessons carry ✅ APPLIED**: dry-run mode UI 진입 시 frontend territory 정합 sweep 결정 wire + ko-KR.json SSOT only + vitest RTL render discipline + owner-only RBAC + unknown state reject + ko-KR.json SSOT drift detector 결정 wire
- **CR 12-1 L4 industry-agnostic capability ✅ APPLIED**: FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire + capability matrix v1.37 EXTENSION 결정 wire
- **CR 12-5 D-14 typed exception envelope ✅ APPLIED**: 14 NEW typed exception classes (AnomalyDefinitionInvalidError(400) + AnomalyDetectionError(500) + AnomalyBaselineUnavailableError(404) + AlertRoutingError(500) + AlertChannelUnavailableError(503) + SlackAPIError(502) + PagerDutyAPIError(502) + BudgetDefinitionInvalidError(400) + BudgetScopeInvalidError(404) + BudgetAmountInvalidError(400) + BudgetAlertError(500) + BudgetConsumptionUpdateError(500) + ForecastAccuracyError(500) + ModelVersionInvalidError(400)) 결정 wire + apps/api/main.py EXTENSION 결정 wire
- **CR 12-5 D-PARITY-01 inversion ✅ APPLIED**: Python FastAPI backend anomaly_detection.py + budget_definition.py TypedDict ↔ TypeScript Next.js frontend finops-anomaly-client.ts interface parity 결정 wire + vitest CR 12-5 D-PARITY-01 검증 결정 wire
- **CR 12-5 D-GATE-01 inversion ✅ APPLIED**: FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT capability gate per-tenant on/off + owner-only RBAC AD-22 결정 wire + gate 적용 대상 명시 결정 wire
- **A19 cohesion pattern 9 surface EXTENSION PASS ✅**: FinOps Anomaly + Budget Alert surface NEW = F28.1~F28.8 Cost Anomaly Detection & Budget Alerting territory 결정 wire + spec surface EXTENSION + test surface EXTENSION + docs surface EXTENSION 결정 wire
- **A36 SDR 검증 4-step 자동 적용 ✅**: commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS 결정 wire
- **AD-14 stack pin ✅ APPLIED**: sklearn==1.4.0 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 + Recharts 2.12.7 (Phase 11 wire pandas + reportlab + jinja2 + openpyxl + pdfkit + weasyprint + python-magic EXTENSION 결정 wire)
- **AD-22 owner-only RBAC ✅ APPLIED**: anomaly detection + budget definition + budget alert + forecast accuracy tracking 모두 owner-only RBAC AD-22 + Epic 12 2FA 챌린지 보존 결정 wire
- **NFR4 PII minimization ✅ PRESERVED**: anomaly/budget data 는 사업 metric + cost amount 만 포함, PII 미포함 결정 wire

## Architecture Alignment (cj-style ALLOWED sweep — Phase 11 wire 정합)

**ALLOWED_SERVICE_SUBMODULES sweep CR 11-3 D-2 verbatim** (Phase 5 wire `f093f8c` + Phase 7 wire `59b56cd` + Phase 8 wire `60d4ea1` + Phase 9 wire `e7670e1` + Phase 10 wire `ac5d6c5` + Phase 11 wire `e020ad0` 정합):

### Backend (FastAPI, Python 3.12)
- ✅ `apps/api/modules/finops/` (MODIFIED EXTENSION): `anomaly_detection.py` + `anomaly_detection_engine.py` + `budget_definition.py` + `budget_alert.py` + `forecast_accuracy.py` + `__init__.py` EXTENSION + `serializers.py` EXTENSION
- ✅ `apps/api/core/capability.py` (MODIFIED): Capability.FINOPS_ANOMALY_DETECTION + Capability.FINOPS_BUDGET_ALERT enum EXTENSION + 4 INDUSTRY_CAPABILITIES EXTENSION
- ✅ `apps/api/dependencies/capability.py` (MODIFIED): require_finops_anomaly_detection + require_finops_budget_alert EXTENSION
- ✅ `apps/api/core/audit_action.py` (MODIFIED): ActionClass.FINOPS_ANOMALY + ActionClass.FINOPS_BUDGET + FinopsAnomalyAction Literal 4 NEW + FinopsBudgetAction Literal 4 NEW + _ActionRegistry FINOPS_ANOMALY + FINOPS_BUDGET entry 7 신규 등록 + __all__ EXTENSION
- ✅ `apps/api/core/errors.py` (MODIFIED): 14 NEW typed exception classes CR 12-5 D-14 verbatim
- ✅ `apps/api/alembic/versions/0044_phase_12_finops_anomaly.py` (NEW): 6 tables + indexes + RLS policies
- ✅ `apps/api/main.py` (MODIFIED): /admin/finops/anomaly/* endpoints EXTENSION (CR 1-1 RSC boundary 적용)

### Frontend (Next.js 15.x, TypeScript 5.x)
- ✅ `apps/web/app/[locale]/(dashboard)/admin/finops/anomaly/page.tsx` (NEW): RSC + finops anomaly dashboard
- ✅ `apps/web/app/[locale]/(dashboard)/admin/finops/anomaly/layout.tsx` (NEW): RTL section wrapper
- ✅ `apps/web/components/finops/FinopsAnomalyDashboardPanel.tsx` (NEW): 4 components (AnomalyDetectionChart + AnomalyDetectionMethodSelector + AnomalyDetectionThresholdSlider + BudgetAlertPanel)
- ✅ `apps/web/lib/finops-anomaly/finops-anomaly-client.ts` (NEW): AnomalyDefinition + AnomalyResult + BudgetDefinition + BudgetAlertResult TypedDict CR 12-5 D-PARITY-01 verbatim + 4 fetch wrappers + FinopsAnomalyApiError class
- ✅ `apps/web/messages/ko-KR.json` (MODIFIED): EXTENSION `finops_anomaly.*` namespace ~25 keys 결정 wire

### Tests
- ✅ `tests/api/core/test_phase_12_finops_anomaly*.py` (NEW): ~40 NEW pytest
- ✅ `tests/integration/test_finops_anomaly_tenant_isolation.py` (NEW): multi-tenant isolation CR 0-2 verbatim
- ✅ `tests/integration/test_capability_matrix_v1_37_drift.py` (NEW): 10 NEW pytest cases
- ✅ `apps/web/__tests__/finops-anomaly/finops-anomaly-dashboard.test.tsx` (NEW): ~4 NEW vitest
- ✅ `apps/web/__tests__/i18n/finops-anomaly-i18n-ssot.test.ts` (NEW): SSOT drift NFR18 ko-KR 정합

### Docs
- ✅ `docs/finops-anomaly-budget-alert.md` (NEW): ~+200 LOC 14 sections runbook 결정 wire
- ✅ `docs/capability-matrix.md` (MODIFIED): v1.36 → v1.37 EXTENSION

## Files Affected (estimate)

- **~20 NEW**: `apps/api/modules/finops/{anomaly_detection,anomaly_detection_engine,budget_definition,budget_alert,forecast_accuracy}.py` (5 files) + `apps/api/alembic/versions/0044_phase_12_finops_anomaly.py` + `apps/web/app/[locale]/(dashboard)/admin/finops/anomaly/{page,layout}.tsx` (2 files) + `apps/web/components/finops/FinopsAnomalyDashboardPanel.tsx` + `apps/web/lib/finops-anomaly/finops-anomaly-client.ts` + tests (5 files) + `docs/finops-anomaly-budget-alert.md`
- **~12 MODIFIED**: `apps/api/core/capability.py` + `apps/api/dependencies/capability.py` + `apps/api/core/audit_action.py` + `apps/api/core/errors.py` + `apps/api/main.py` + `apps/api/modules/finops/__init__.py` + `apps/api/modules/finops/serializers.py` + `apps/web/messages/ko-KR.json` + `docs/capability-matrix.md` + `_bmad-output/implementation-artifacts/sprint-status.yaml` + `tests/integration/conftest.py` + `apps/api/alembic/versions/script.py.mako`
- **Total**: ~32 files atomic single sprint

## Test Coverage

- **~50 NEW pytest PASS 결정 wire**:
  - `tests/api/core/test_phase_12_anomaly_detection.py` (6 cases): TypedDict validation + 4 detection methods + 5 dimension 옵션 + 3 baseline windows + audit-first INSERT + owner-only RBAC + dry_run default
  - `tests/api/core/test_phase_12_budget_definition.py` (6 cases): TypedDict validation + budget_period enum + budget_scope enum + alert_thresholds + audit-first INSERT + owner-only RBAC + dry_run default
  - `tests/api/core/test_phase_12_anomaly_detection_engine.py` (8 cases): 4 detection methods + multi-method voting consensus + false positive suppression + alert routing + alert deduplication + isolation_forest retraining + audit-first INSERT + typed exception envelope
  - `tests/api/core/test_phase_12_budget_alert.py` (7 cases): real-time consumption tracking + threshold-based alerting + alert deduplication + budget overrun prediction + forecast accuracy MAE/MAPE/RMSE + model_version tracking + audit-first INSERT
  - `tests/api/core/test_phase_12_forecast_accuracy.py` (6 cases): MAE + MAPE + RMSE + model_version tracking + audit-first INSERT + multi-tenant isolation + typed exception envelope
  - `tests/api/core/test_phase_12_audit_action.py` (7 cases): 7 NEW audit log entries + ActionClass.FINOPS_ANOMALY + ActionClass.FINOPS_BUDGET + emit_audit_typed CR 1-1
  - `tests/integration/test_finops_anomaly_tenant_isolation.py` (4 cases): cross-tenant isolation + anomaly baseline isolation + budget consumption isolation
  - `tests/integration/test_capability_matrix_v1_37_drift.py` (10 cases): FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT enum + 4-industry grants + v1.36 + v1.35 + ... preservation
  - **Subtotal**: ~50 NEW pytest PASS

- **~5 NEW vitest PASS 결정 wire**:
  - `apps/web/__tests__/finops-anomaly/finops-anomaly-dashboard.test.tsx` (4 cases): AnomalyDetectionChart + AnomalyDetectionMethodSelector + AnomalyDetectionThresholdSlider + BudgetAlertPanel
  - `apps/web/__tests__/i18n/finops-anomaly-i18n-ssot.test.ts` (1 cases): ko-KR SSOT drift detection + CR 12-5 D-PARITY-01 verification
  - **Subtotal**: ~5 NEW vitest PASS

- **0 NEW ruff 결정 wire** (apps/api backend 결정 wire + 기존 ruff scoped 0 NEW 정합 보존)
- **0 NEW tsc 결정 wire** (apps/web frontend 결정 wire + 기존 tsc 0 NEW 정합 보존)
- **0 regressions 결정 wire** (3중 게이트 FINAL CLEAN + ruff scoped 0 NEW + pytest 0 NEW failures + vitest 0 NEW failures + tsc 0 NEW errors)

## Notes

- `apps/api/main.py` EXTENSION 시 /admin/finops/anomaly/* endpoints EXTENSION + require_finops_anomaly_detection + require_finops_budget_alert dep 적용
- `apps/api/core/errors.py` EXTENSION 시 14 NEW typed exception classes + envelope CR 11-4 P-015 적용
- `apps/api/core/audit_action.py` EXTENSION 시 ActionClass.FINOPS_ANOMALY + ActionClass.FINOPS_BUDGET + FinopsAnomalyAction Literal 4 NEW values + FinopsBudgetAction Literal 4 NEW values + _ActionRegistry FINOPS_ANOMALY + FINOPS_BUDGET entry 7 신규 등록
- m20_finops_anomaly.finops_anomaly_serializers NEW Phase 12 EXTENSION 결정 wire (Phase 11 wire `e020ad0` m19_finops.finops_serializers EXTENSION pattern verbatim 미러, wire 시점에 sprint-status.yaml action_items EXTENSION)
- Phase 11 wire `e020ad0` 의 showback baseline 대비 deviation 감지 = cost anomaly detection + chargeback 한도 초과 알림 = budget alert territory 자연스러운 EXTENSION 결정 wire
- Phase 8 wire `60d4ea1` 의 cost-engine V8 골든 fixture + 12-period benchmark 의 자연스러운 carry-over chain (historical baseline last 30d + last 90d + YTD + statistical model training + forecast deviation tracking EXTENSION) 결정 wire
- Phase 10 wire `ac5d6c5` 의 4 SLIs 자연스러운 EXTENSION 결정 wire + Phase 9 wire `e7670e1` chaos_experiment baseline EXTENSION 결정 wire
- Phase 7 wire `59b56cd` observability 의 Prometheus custom metrics + Slack channel EXTENSION 결정 wire + alert routing 정합
- Epic 12 2FA 챌린지 mandatory 결정 wire (anomaly detection + budget definition + budget alert + forecast accuracy tracking 모두 Epic 12 2FA 챌린지 mandatory)
- AD-22 owner-only RBAC 보존 결정 wire (anomaly detection + budget definition + budget alert + forecast accuracy tracking 모두 owner-only)
- AD-14 stack pin 결정 wire (sklearn==1.4.0 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 + Recharts 2.12.7)
- NFR4 PII minimization PRESERVED (anomaly/budget data 는 사업 metric + cost amount 만 포함, PII 미포함)
- 3중 게이트 impact NONE (cj-style 110번째 spec entry 진입 표준 = docs only 변경): ruff scoped 0 NEW + pytest 0 NEW + vitest 0 NEW + tsc 0 NEW
- 8 ACs PRD §F28.1~§F28.8 verbatim → 96 sub-ACs (12+12+12+12+10+10+12+12 = 96 sub-ACs) satisfied pre-flight 정합 sweep 결정 wire

## Cross-References

- Phase 12 PRD entry `344c7eb` (cj-style 109번째) — Cost Anomaly Detection & Budget Alerting territory 정합
- Phase 11 close-out retro `80df15b` (cj-style 108번째) — D-FINOPS-2 honestly DEFER 보존 해소
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
- AD-14 stack pin — sklearn==1.4.0 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 + Recharts 2.12.7
- AD-22 owner-only RBAC — anomaly detection + budget definition + budget alert + forecast accuracy tracking
- AD-39 Cost Anomaly Detection & Budget Alerting 신규
- NFR18 ko-KR — SSOT only invariant
- NFR4 PII minimization — anomaly/budget data PII 미포함
- CR 0-2 RLS lesson, CR 1-1 audit-first INSERT, CR 4-3/4-4 lessons carry, CR 1-1 ContextVar, CR 1-1 RSC boundary, CR 9-6 commit message, CR 11-3 honest-DEFER, CR 11-4 D-001~D-005 + P-015, CR 12-1 L4 industry-agnostic capability, CR 12-5 D-14 envelope, CR 12-5 D-PARITY-01, CR 12-5 D-GATE-01, A19 cohesion 9 surface EXTENSION PASS, A36 SDR 검증 4-step 자동 적용
- m20_finops_anomaly.finops_anomaly_serializers NEW Phase 12 EXTENSION 결정 wire (wire 시점에)

## 결정 wire 일자

2026-08-24 (KST)

## next (wire 진입 시)

옵션 (a) Phase 12 bmad-dev-story atomic wire T1~T8 진입 (cj-style 111번째 wire 진입 시점) 결정 wire 진입 / 옵션 (b) Phase 12 close-out retro 진입 (cj-style 112번째) / 옵션 (c) Phase 13+ 진입 / 옵션 (d) Epic 18+ 진입 / 옵션 (e) D-DEFER-* follow-up 진입 결정 wire 보류.