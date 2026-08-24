---
baseline_commit: 0e3f8d9
status: ready-for-dev
cj_style_entry_point: 118
story_key: phase-14-finops-optimization-rightsizing-wire
---

# Phase 14 FinOps Optimization & Rightsizing wire spec (cj-style 118번째 epic 연속 정직 회복)

## Story

**As a** finance team / FinOps analyst / department cost center owner / capacity planner / cloud architect / commitment manager / tenant admin / enterprise onboarding lead / compliance officer
**I want** FinOps Optimization & Rightsizing territory 결정 wire (optimization definition DSL `define_optimization` builder + AST 5 levels + 5 resource_type 옵션 compute/storage/database/network/container + 6 optimization_strategy 옵션 rightsize_down/rightsize_up/idle_terminate/commit_1y/commit_3y/storage_tier_down + 4 target_metric 옵션 cost_saving_pct/cost_saving_amount/utilization_target/commit_break_even_months + 5 baseline_period 옵션 last_7d/last_30d/last_90d/last_180d/last_365d + 4 industries baseline industry-agnostic + per-tenant override EXTENSION + OptimizationDefinition TypedDict 11 fields + rightsizing engine 5 resource types compute/storage/database/network/container + 80+ AWS EC2 instance type mapping + Phase 13 wire `8b98030` capacity_headroom_report 의 90일 lookahead forecast EXTENSION + RightsizingRecommendation TypedDict 14 fields + idle resource detector 5 resource_type idle 정의 + z-score < -2.0 based detection + Phase 12 wire `f3c0e63` anomaly_detection baseline EXTENSION + IdleResource TypedDict 13 fields + RI/SP commitment recommender commitment_type enum 6 ec2_ri/rds_ri/ec2_sp/s3_sp/redshift_sp/dynamodb_sp + commitment_term enum 1_year/3_year + break-even_months calculation + CommitmentRecommendation TypedDict 12 fields + Phase 13 wire `8b98030` forecast 12-month baseline EXTENSION + optimization accuracy tracker precision/recall/realized_savings + Phase 13 wire `8b98030` forecast_accuracy_tracker EXTENSION pattern + OptimizationAccuracyReport TypedDict 10 fields + Capability matrix v1.40 EXTENSION FINOPS_OPTIMIZATION + audit-first INSERT 8 NEW + ActionClass.FINOPS_OPTIMIZATION)
**so that** Phase 13 wire `8b98030` FinOps Forecasting & Capacity Planning territory (forecast definition DSL + 4 time series models ARIMA/Prophet/LSTM/ensemble + capacity headroom analysis compute/storage/network 90일 lookahead + budget burn-rate projection + forecast accuracy tracking MAE/MAPE/RMSE + Capability FINOPS_FORECASTING_CAPACITY_PLANNING 1 NEW + dry-run mode) 의 natural backend ACTIONABLE RECOMMENDATION LAYER EXTENSION 결정 wire 진입 (capacity headroom 의 compute/storage/network saturation 90일 lookahead forecast → forward-looking rightsizing recommendation + forecast accuracy 의 MAE/MAPE/RMSE → optimization accuracy precision/recall/realized_savings + budget burn-rate projection 의 projected_overrun_pct → projected_savings_pct + Phase 13 forecasting 의 historical baseline → utilization baseline for idle detection + Phase 11 wire `e020ad0` showback period selector 의 monthly granularity → monthly optimization cycle + Phase 12 wire `f3c0e63` anomaly detection 의 z-score baseline → idle detection z-score threshold < -2.0) = Phase 13 FinOps territory 의 ACTIONABLE RECOMMENDATION LAYER EXTENSION 결정 (forecast → action) + Phase 14 PRD entry `0e3f8d9` (cj-style 117번째) DONE 진입 정합 보존 + Epic 12 2FA 챌린지 보존 + AD-22 owner-only RBAC 보존 + D-FINOPS-4 honestly DEFER 보존 진입 결정 wire + Phase 13 close-out retro `850b4f8` §13 verbatim 해소 결정 wire 보존).

## Context

cj-style Phase 14 2번째 진입점 (cj-style 118번째) 진입 결정 wire 진입 완료:
- Phase 14 PRD entry `0e3f8d9` (cj-style 117번째) DONE 진입 정합 보존
- Phase 13 close-out retro `850b4f8` (cj-style 116번째) + Phase 13 atomic wire T1~T8 `8b98030` (cj-style 115번째) + Phase 13 spec entry `77ed55f` (cj-style 114번째) + Phase 13 PRD entry `d31dfc8` (cj-style 113번째) + Phase 12 close-out retro `3354e83` (cj-style 112번째) + Phase 12 atomic wire T1~T8 `f3c0e63` (cj-style 111번째) + Phase 12 spec entry `8c5f374` (cj-style 110번째) + Phase 12 PRD entry `344c7eb` (cj-style 109번째) + Phase 11 close-out retro `80df15b` (cj-style 108번째) + Phase 11 atomic wire T1~T8 `e020ad0` (cj-style 107번째) + Phase 11 spec entry `82c93a8` (cj-style 106번째) + Phase 11 PRD entry `16d7698` (cj-style 105번째) + Phase 10 close-out retro `733d428` (cj-style 104번째) + Phase 10 wire `ac5d6c5` (cj-style 103번째) 결정 wire 모두 DONE 진입 정합 보존
- D-FINOPS-4 honestly DEFER 보존 진입 결정 wire (Phase 14 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire + Phase 13 close-out retro `850b4f8` §13 + Phase 12 close-out retro `3354e83` §13 + Phase 11 close-out retro `80df15b` §12 + Phase 10 close-out retro `733d428` §10 + Phase 9 close-out retro `634427d` §10 + Phase 8 close-out retro `ab495a8` §10 + Phase 7 close-out retro `326fa9f` §10 + Phase 6 close-out retro `f9f006c` §13 + Epic 17 close-out retro `be8f3bd` §11 + 1st release close-out retro §6 "FinOps Optimization & Rightsizing 결정 wire 보류, Phase 14+ 진입 시점" verbatim 해소 + Phase 14 PRD entry 진입 시점에 1 NEW 결정 wire)
- D-FINOPS-3 ✅ RESOLVED 보존 진입 결정 wire
- D-FINOPS-2 ✅ RESOLVED 보존 진입 결정 wire
- D-FINOPS-1 ✅ RESOLVED 보존 진입 결정 wire
- D-SLO-1 ✅ RESOLVED 보존 진입 결정 wire
- D-CHAOS-1 ✅ RESOLVED 보존 진입 결정 wire
- D-PERFORMANCE-1 ✅ RESOLVED 보존 진입 결정 wire
- D-OBSERVABILITY-1 ✅ RESOLVED 보존 진입 결정 wire
- Phase 14 PRD entry 의 8 ACs §F30.1~§F30.8 verbatim 결정 wire 보존
- Capability matrix v1.39 → v1.40 EXTENSION FINOPS_OPTIMIZATION 1 NEW row 결정 wire (industry-agnostic 4-industry grants ✅/✅/✅/✅ CR 12-1 L4 precedent 미러)
- AD-41 FinOps Optimization & Rightsizing 신규 결정 wire 진입 (a)~(g) 7 sub-decisions

## 8 ACs (PRD §F30.1~§F30.8 verbatim) → 92 detailed sub-ACs

### §F30.1 optimization definition DSL (12 sub-ACs)
- F30.1-1 `apps/api/modules/finops/optimization_definition.py` NEW (~+150 LOC + `define_optimization(tenant_id, resource_type, optimization_strategy, target_metric, baseline_period)` builder + AST 5 levels + parser 검증 3 layer 결정 wire + 4 industries baseline industry-agnostic + per-tenant override EXTENSION)
- F30.1-2 `OptimizationDefinition` TypedDict 11 fields 결정 wire (optimization_id UUID PK + tenant_id UUID + resource_type enum compute/storage/database/network/container + optimization_strategy enum rightsize_down/rightsize_up/idle_terminate/commit_1y/commit_3y/storage_tier_down + target_metric enum cost_saving_pct/cost_saving_amount/utilization_target/commit_break_even_months + baseline_period enum last_7d/last_30d/last_90d/last_180d/last_365d + status enum active/paused/expired + created_at TIMESTAMPTZ + updated_at TIMESTAMPTZ + trace_id TEXT)
- F30.1-3 5 resource_type 옵션 결정 wire (compute EC2 instance / storage S3 EBS / database RDS / network EIP NAT LB / container EKS node group + resource_type validation + tenant_settings.resource_inventory JSONB 기반)
- F30.1-4 6 optimization_strategy 옵션 + 1 composite default 결정 wire (rightsize_down + rightsize_up + idle_terminate + commit_1y + commit_3y + storage_tier_down + composite default = 4 strategy 자동 선택)
- F30.1-5 4 target_metric 옵션 결정 wire (cost_saving_pct default 20% + cost_saving_amount KRW + utilization_target default 70% + commit_break_even_months default 1y=8mo 3y=18mo)
- F30.1-6 5 baseline_period 옵션 결정 wire (last_7d + last_30d default + last_90d + last_180d + last_365d)
- F30.1-7 `OPTIMIZATION_DEFAULTS` constants 결정 wire (`OPTIMIZATION_DEFAULTS = {'resource_type': 'compute', 'optimization_strategy': 'composite', 'target_metric': 'cost_saving_pct', 'baseline_period': 'last_30d', 'idle_cpu_threshold_pct': 5.0, 'idle_detection_window_days': 30, 'min_savings_amount_krw': 10000, 'commit_break_even_months_1y': 8, 'commit_break_even_months_3y': 18}` constants + `OPTIMIZATION_RESOURCE_TYPES = ['compute', 'storage', 'database', 'network', 'container']` constants + `OPTIMIZATION_STRATEGIES = ['rightsize_down', 'rightsize_up', 'idle_terminate', 'commit_1y', 'commit_3y', 'storage_tier_down', 'composite']` constants 결정 wire)
- F30.1-8 4 industries baseline industry-agnostic 결정 wire (manufacturing + service + manufacturing_service + manufacturing_service_other 모두 optimization 가능 + per-tenant override EXTENSION + Phase 13 wire `8b98030` FINOPS_FORECASTING_CAPACITY_PLANNING 4-industry grants ✅/✅/✅/✅ pattern verbatim 미러 + Phase 12 wire `f3c0e63` FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT 4-industry grants ✅/✅/✅/✅ pattern verbatim 미러 + policy evaluation precedence tenant override > industry baseline > system default)
- F30.1-9 optimization definition pure validator CR 11-4 P-015 verbatim 결정 wire (`parse_optimization_definition(tenant_id, payload) -> OptimizationDefinition` + 6 validation rules + 5 layer defense (syntax + semantic + tenant-scope RLS + resource_type validation + inventory data availability) + `OptimizationDefinitionInvalidError(400)` + `OptimizationScopeInvalidError(404)` + `OptimizationInventoryUnavailableError(422)` CR 12-5 D-14 envelope)
- F30.1-10 audit-first INSERT `optimization_definition_updated` 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_OPTIMIZATION 신규 정의 + emit_audit_typed BEFORE optimization definition update + per-tenant RLS 자동 적용 + multi-tenant isolation test)
- F30.1-11 typed exception envelope CR 12-5 D-14 verbatim 결정 wire (3 NEW typed exception classes: `OptimizationDefinitionInvalidError(400)` + `OptimizationScopeInvalidError(404)` + `OptimizationInventoryUnavailableError(422)`)
- F30.1-12 dry-run mode `--finops-optimization-dry-run` CLI flag 결정 wire (dry-run 시 actual optimization definition update skip + optimization preview phase_14_finops_optimization_preview table alembic 0046 신규 + audit-first INSERT `optimization_dry_run_executed` CR 1-1 verbatim)

### §F30.2 rightsizing engine (12 sub-ACs)
- F30.2-1 `apps/api/modules/finops/rightsizing_engine.py` NEW (~+200 LOC + `recommend_rightsizing(tenant_id, resource_type, baseline_period) -> List[RightsizingRecommendation]` + Phase 13 wire `8b98030` capacity_headroom_report 의 compute/storage/network saturation 90일 lookahead forecast EXTENSION + instance type 한 단계 downsize/upsize 권고 + per-resource savings calculation 결정 wire)
- F30.2-2 compute rightsizing 결정 wire (EC2 instance type 한 단계 downsize e.g. m5.2xlarge → m5.xlarge + upsize 성능 회피 목적 + Phase 13 wire `8b98030` LSTM model 의 CPU utilization 90일 lookahead forecast 기반 max expected utilization < 70% → downsize 권고 + max_expected_utilization_pct = max(forecast_p50, forecast_p99 × 1.1) + 4 instance family mapping (general_purpose + compute_optimized + memory_optimized + storage_optimized) 결정 wire)
- F30.2-3 storage rightsizing 결정 wire (S3 Standard → S3 Standard-IA 30일 access < 1회 or S3 Glacier 90일 access < 1회 tier downgrade 권고 + Phase 13 wire `8b98030` Prophet model 의 storage growth 90일 lookahead forecast EXTENSION + access_pattern enum frequent/infrequent/rare + 3 storage tier mapping Standard + Standard-IA + Glacier 결정 wire)
- F30.2-4 database rightsizing 결정 wire (RDS instance class 한 단계 downsize e.g. db.r5.2xlarge → db.r5.xlarge + connection_count_p95 + CPU utilization_p95 + memory utilization_p95 3 metric 기반 권고 + Phase 13 wire `8b98030` capacity_headroom_report database saturation EXTENSION 정합)
- F30.2-5 network rightsizing 결정 wire (EIP Elastic IP attached 여부 검증 + unattached EIP release 권고 + NAT gateway bandwidth 90일 max utilization < 10% → NAT gateway 제거 권고 + Load balancer request count_p95 < 100/일 → ALB 제거 권고 + Phase 13 wire `8b98030` network saturation forecast EXTENSION 정합)
- F30.2-6 container rightsizing 결정 wire (EKS node group desired instance count 조정 권고 + CPU request/limit 합리화 권고 Phase 7 wire `59b56cd` business_calculations_total EXTENSION + memory request/limit 합리화 권고 + per-pod resource utilization 분석 + Phase 13 wire `8b98030` capacity_headroom_report container dimension EXTENSION 정합)
- F30.2-7 `RightsizingRecommendation` TypedDict 14 fields 결정 wire (recommendation_id UUID PK + tenant_id UUID + resource_id TEXT resource ARN or ID + resource_type enum compute/storage/database/network/container + current_instance_type TEXT + recommended_instance_type TEXT + current_cost_krw NUMERIC(20, 2) per month + recommended_cost_krw NUMERIC(20, 2) per month + projected_savings_pct NUMERIC(8, 4) + projected_savings_amount_krw NUMERIC(20, 2) per month + confidence_score NUMERIC(8, 4) Phase 13 forecast accuracy EXTENSION + recommendation_severity enum low/medium/high + model_version TEXT + generated_at TIMESTAMPTZ + trace_id TEXT 결정 wire)
- F30.2-8 instance type mapping table 결정 wire (`INSTANCE_TYPE_DOWNGRADE_MAP` 80+ AWS EC2 instance type mapping m5.large → t3.large, m5.xlarge → m5.large, m5.2xlarge → m5.xlarge, etc. + `INSTANCE_TYPE_UPGRADE_MAP` reverse mapping + per-family mapping general_purpose + compute_optimized + memory_optimized + storage_optimized + GCP/Azure mapping JSONB 결정 wire)
- F30.2-9 projected_savings calculation 결정 wire (`projected_savings_krw_per_month = current_cost_krw - recommended_cost_krw` + annualized `projected_savings_krw_per_year = projected_savings_krw_per_month × 12` + Phase 11 wire `e020ad0` chargeback cost allocation EXTENSION + Phase 12 wire `f3c0e63` budget_definition EXTENSION 정합)
- F30.2-10 confidence_score calculation 결정 wire (Phase 13 wire `8b98030` forecast_accuracy 의 MAPE 기반 confidence_score + confidence_score = (1 - normalized_mape) × 100 + confidence_score < 70% → low severity + 70~90% → medium + ≥ 90% → high + Phase 13 model_retraining_triggered EXTENSION 정합)
- F30.2-11 audit-first INSERT `recommendation_generated` 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_OPTIMIZATION + emit_audit_typed BEFORE recommendation generation + per-tenant RLS 자동 적용 + multi-tenant isolation test)
- F30.2-12 typed exception envelope CR 12-5 D-14 verbatim 결정 wire (3 NEW typed exception classes: `RightsizingEngineError(500)` + `InstanceTypeMappingError(500)` + `RecommendationConfidenceLowError(422)`)

### §F30.3 idle resource detection (12 sub-ACs)
- F30.3-1 `apps/api/modules/finops/idle_resource_detector.py` NEW (~+180 LOC + `detect_idle_resources(tenant_id, idle_cpu_threshold_pct, idle_window_days) -> List[IdleResource]` + Phase 12 wire `f3c0e63` anomaly_detection 의 z-score < -2.0 EXTENSION + Phase 13 wire `8b98030` capacity_headroom_report 의 last 30d utilization EXTENSION 결정 wire)
- F30.3-2 compute idle detection 결정 wire (CPU utilization_p95 < idle_cpu_threshold_pct default 5% for idle_window_days default 30 일관된 → idle compute resource classify + network_in_bytes_p95 < 1MB/day for 30d → idle network classify + memory utilization_p95 < 10% for 30d → low utilization classify + Phase 12 wire `f3c0e63` anomaly_detection 의 z-score < -2.0 EXTENSION 정합)
- F30.3-3 storage idle detection 결정 wire (S3 bucket last_accessed_at > idle_window_days → idle storage classify + S3 bucket size < 1GB + last_accessed_at > 30d → cleanup candidate + EBS volume attached=false for 7d → unattached EBS classify + snapshot created_at > 90d + size > 100GB → stale snapshot classify)
- F30.3-4 database idle detection 결정 wire (RDS instance connection_count_p95 = 0 for 30d → idle RDS classify + connection_count_p95 < 5 for 30d → low utilization RDS classify + snapshot created_at > 90d + storage < 100GB → stale RDS snapshot classify + Phase 6 wire `24e1cd7` audit_log_archive EXTENSION 정합)
- F30.3-5 network idle detection 결정 wire (EIP associated=false for 7d → idle EIP classify + NAT gateway bytes_out_p95 = 0 for 30d → idle NAT gateway classify + Load balancer request_count_p95 < 100/day for 30d → idle load balancer classify + VPC endpoint unused for 30d → idle VPC endpoint classify)
- F30.3-6 container idle detection 결정 wire (EKS node group desired_count × max_utilization_p95 < 30% → downsize 권고 + pod CPU request/limit 합리화 분석 Phase 7 wire `59b56cd` business_calculations_total EXTENSION + pod memory request/limit 합리화 분석 + per-deployment resource utilization 30d 분석 결정 wire)
- F30.3-7 `IdleResource` TypedDict 13 fields 결정 wire (idle_resource_id UUID PK + tenant_id UUID + resource_id TEXT + resource_type enum compute/storage/database/network/container + idle_reason TEXT low_cpu + low_network + unattached + zero_connections + low_request_count + idle_duration_days int + current_cost_krw_per_month NUMERIC(20, 2) + potential_savings_krw_per_month NUMERIC(20, 2) + idle_severity enum low/medium/high + action enum terminate/downsize/review + detection_method enum z_score/threshold/heuristic + detection_window_days int + generated_at TIMESTAMPTZ + trace_id TEXT 결정 wire)
- F30.3-8 z-score idle detection 결정 wire (Phase 12 wire `f3c0e63` anomaly_detection 의 z-score EXTENSION + z_score = (utilization_p95 - mean_utilization_30d) / std_utilization_30d + z_score < -2.0 → idle classify + Phase 12 wire 의 multi-method voting consensus 3 of 4 methods agree EXTENSION 결정 wire)
- F30.3-9 severity classification 결정 wire (potential_savings_krw_per_month < 10000 KRW → low severity / 10000~100000 → medium / ≥ 100000 → high + per-tenant override severity_threshold_krw default 10000 + severity_threshold_per_tenant override JSONB 결정 wire)
- F30.3-10 action recommendation 결정 wire (idle_severity=low → action='review' 수동 검토 권고 + medium → 'downsize' 축소 권고 + high → 'terminate' 종료 권고 + per-tenant override action_policy 자동 terminate 허용 tenant 명시 + 자동 terminate 시 Epic 12 2FA 챌린지 보존 결정 wire)
- F30.3-11 audit-first INSERT `idle_resource_detected` 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_OPTIMIZATION + emit_audit_typed BEFORE idle resource detection + per-tenant RLS 자동 적용 + multi-tenant isolation test)
- F30.3-12 typed exception envelope CR 12-5 D-14 verbatim 결정 wire (3 NEW typed exception classes: `IdleResourceDetectionError(500)` + `IdleSeverityClassificationError(500)` + `IdleMetricUnavailableError(404)`)

### §F30.4 RI / SP commitment recommendations (12 sub-ACs)
- F30.4-1 `apps/api/modules/finops/commitment_recommender.py` NEW (~+150 LOC + `recommend_commitments(tenant_id, baseline_period) -> List[CommitmentRecommendation]` + 1-year / 3-year Reserved Instance RI / Savings Plans SP commitment 권고 + break-even months calculation + projected savings calculation 결정 wire + Phase 13 wire `8b98030` forecast 의 12-month baseline EXTENSION)
- F30.4-2 commitment_type enum 결정 wire (ec2_ri EC2 Reserved Instance standard/convertible + rds_ri RDS Reserved Instance + ec2_sp EC2 Savings Plans Compute Savings Plans + s3_sp S3 Storage Savings Plans + redshift_sp Redshift Reserved Instance + dynamodb_sp DynamoDB Reserved Capacity + per-tenant override commitment_type_allowlist JSONB 결정 wire)
- F30.4-3 commitment_term enum 결정 wire (1_year 1-year term default break-even 8 months + 3_year 3-year term default break-even 18 months + commitment_term default = composite 1y/3y 비교 후 최적 + per-tenant override JSONB 결정 wire)
- F30.4-4 break-even calculation 결정 wire (`break_even_months = upfront_cost / monthly_savings` + 1-year commitment 시 break_even_months ≤ 8mo 이면 commit_1y 권고 + 3-year commitment 시 break_even_months ≤ 18mo 이면 commit_3y 권고 + 그 외 → on-demand 유지 권고 + break_even calculation Phase 13 forecast accuracy EXTENSION 정합)
- F30.4-5 utilization_forecast 기반 권고 결정 wire (Phase 13 wire `8b98030` forecast_engine 의 12-month forward forecast 활용 + forecast_p50 >= on_demand_cost × 0.7 → RI/SP 권고 + forecast_p50 < on_demand_cost × 0.5 → on-demand 유지 권고 + forecast_p50 변동성 std/mean > 30% → 1y 권고 3y 변동성 위험 회피 결정 wire)
- F30.4-6 ROI calculation 결정 wire (`roi_pct = (total_3y_savings - upfront_cost) / upfront_cost × 100` + ROI > 100% → high severity / 50~100% → medium / < 50% → low + per-tenant override roi_threshold_pct default 50% 결정 wire)
- F30.4-7 `CommitmentRecommendation` TypedDict 12 fields 결정 wire (recommendation_id UUID PK + tenant_id UUID + commitment_type enum + commitment_term enum 1_year/3_year + resource_pattern TEXT instance type pattern e.g. m5.large + current_on_demand_cost_krw_per_month NUMERIC(20, 2) + projected_commit_cost_krw_per_month NUMERIC(20, 2) + projected_savings_pct NUMERIC(8, 4) + projected_savings_krw NUMERIC(20, 2) over commitment_term + upfront_cost_krw NUMERIC(20, 2) + break_even_months int + roi_pct NUMERIC(8, 4) + recommendation_severity enum low/medium/high + generated_at TIMESTAMPTZ + trace_id TEXT 결정 wire)
- F30.4-8 pricing data source 결정 wire (AWS Pricing API 의 on-demand price + RI/SP discount rate 1y ~40% discount + 3y ~60% discount + Phase 8 wire `60d4ea1` 의 cost-engine 12-period benchmark EXTENSION + Phase 13 wire `8b98030` forecast 의 12-month baseline pricing source EXTENSION 결정 wire)
- F30.4-9 commitment simulation 결정 wire (1y / 3y 두 가지 시나리오 동시 계산 + 더 높은 projected_savings_pct scenario 권고 + 단, break_even_months 제약 적용 1y ≤ 8mo / 3y ≤ 18mo + on-demand 유지 옵션 fallback + Phase 11 wire `e020ad0` chargeback 의 markup scenario EXTENSION 정합)
- F30.4-10 per-tenant override JSONB 결정 wire (`tenant_settings.commitment_overrides` TypedDict 10 fields commitment_type_allowlist + commitment_term_default + break_even_threshold_1y_months default 8 + break_even_threshold_3y_months default 18 + roi_threshold_pct default 50 + upfront_cost_budget_krw default 1000000 + min_monthly_savings_krw default 10000 + auto_apply_enabled default false + approval_required default true + notification_recipients + policy evaluation precedence tenant override > industry baseline > system default)
- F30.4-11 audit-first INSERT `commitment_recommended` 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_OPTIMIZATION + emit_audit_typed BEFORE commitment recommendation + per-tenant RLS 자동 적용 + multi-tenant isolation test + 자동 apply 시 Epic 12 2FA 챌린지 보존 결정 wire)
- F30.4-12 typed exception envelope CR 12-5 D-14 verbatim 결정 wire (3 NEW typed exception classes: `CommitmentRecommendationError(500)` + `PricingDataUnavailableError(404)` + `BreakEvenCalculationError(500)`)

### §F30.5 optimization accuracy tracking (12 sub-ACs)
- F30.5-1 `apps/api/modules/finops/optimization_accuracy_tracker.py` NEW (~+120 LOC + Phase 13 wire `8b98030` forecast_accuracy_tracker EXTENSION + per-(tenant_id + resource_type + optimization_strategy) granularity + optimization applied vs rejected tracking 결정 wire)
- F30.5-2 precision 정밀도 결정 wire (TP / (TP + FP) = applied recommendations 중 actual savings >= 50% of projected savings 인 비율 + precision ≥ 80% → high accuracy / 60~80% → moderate / < 60% → low accuracy 결정 wire)
- F30.5-3 recall 재현율 결정 wire (TP / (TP + FN) = applicable opportunities 중 recommendations 이 cover 한 비율 + recall ≥ 80% → high coverage / 60~80% → moderate / < 60% → low coverage 결정 wire)
- F30.5-4 realized_savings tracking 결정 wire (`realized_savings_krw_per_month = sum(actual_cost_reduction after applying recommendation)` + Phase 11 wire `e020ad0` showback 의 period selector EXTENSION current/previous month 비교 + per-(tenant_id + resource_type + optimization_strategy) granularity 결정 wire)
- F30.5-5 projected_vs_realized_savings 결정 wire (`accuracy_score = realized_savings / projected_savings × 100` 단위 % + accuracy_score ≥ 80% → high accuracy / 50~80% → moderate / < 50% → low accuracy + per-tenant override accuracy_threshold default 70% 결정 wire)
- F30.5-6 false_positive tracking 결정 wire (recommendation apply 후 actual savings < 50% projected savings → false positive + `false_positive_reasons` enum overestimation + performance_degradation + business_growth + seasonality_mismatch + application_change + Phase 12 wire `f3c0e63` anomaly_detection 의 false_positive EXTENSION 정합)
- F30.5-7 false_negative tracking 결정 wire (applicable opportunity detection miss → false negative + Phase 13 wire `8b98030` capacity_headroom_report 의 utilization baseline EXTENSION 정합 + idle detection miss EXTENSION + commit opportunity miss EXTENSION 결정 wire)
- F30.5-8 `OptimizationAccuracyReport` TypedDict 10 fields 결정 wire (report_id UUID PK + tenant_id UUID + resource_type enum + optimization_strategy enum + total_recommendations int + applied_recommendations int + precision NUMERIC(8, 4) + recall NUMERIC(8, 4) + realized_savings_krw NUMERIC(20, 2) + projected_savings_krw NUMERIC(20, 2) + accuracy_score NUMERIC(8, 4) + generated_at TIMESTAMPTZ + trace_id TEXT 결정 wire)
- F30.5-9 model_performance_degradation_detection 결정 wire (accuracy_score < 70% for 3 consecutive months → recommendation engine retraining trigger + Phase 13 wire `8b98030` model_retraining_triggered EXTENSION + retraining cron KST 매주 일요일 04:00 UTC 19:00 Phase 12 anomaly detection isolation forest retraining cron EXTENSION + Phase 13 forecast retraining cron `0 3 * * 0` EXTENSION 정합 결정 wire)
- F30.5-10 recommended_action audit-first INSERT EXTENSION 결정 wire (`optimization_recommended_action` 1 NEW action + ActionClass.FINOPS_OPTIMIZATION + emit_audit_typed BEFORE recommended action apply + per-tenant RLS 자동 적용 + multi-tenant isolation test)
- F30.5-11 model_version tracking 결정 wire (rightsizing_engine + idle_resource_detector + commitment_recommender 3 engine 모두 semantic versioning MAJOR.MINOR.PATCH + model_version JSONB metadata training_date + training_data_window + training_samples_count + algorithm_hyperparameters + cross_validation_score + Phase 13 wire `8b98030` forecast_model_registry EXTENSION 결정 wire)
- F30.5-12 typed exception envelope CR 12-5 D-14 verbatim 결정 wire (3 NEW typed exception classes: `OptimizationAccuracyTrackingError(500)` + `OptimizationRetrainingTriggerError(500)` + `OptimizationPerformanceDegradationError(500)`)

### §F30.6 optimization dashboard UI (10 sub-ACs)
- F30.6-1 `apps/web/app/[locale]/(dashboard)/admin/finops/optimization/page.tsx` NEW (~+150 LOC + 5 components 결정 wire: OptimizationStrategySelector + RightsizingRecommendationTable + IdleResourcePanel + CommitmentRecommendationPanel + OptimizationAccuracyPanel + owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 보존 결정 wire)
- F30.6-2 `OptimizationStrategySelector` component 결정 wire (7 strategy 옵션 radio button rightsize_down + rightsize_up + idle_terminate + commit_1y + commit_3y + storage_tier_down + composite + 5 resource_type 옵션 compute + storage + database + network + container + 5 baseline_period 옵션 last_7d + last_30d + last_90d + last_180d + last_365d + owner-only ack prompt AD-22 verbatim 결정 wire)
- F30.6-3 `RightsizingRecommendationTable` component 결정 wire (Phase 13 wire `8b98030` forecast 기반 권고 표시 + 14 columns recommendation_id + resource_id + resource_type + current_instance_type + recommended_instance_type + current_cost_krw + recommended_cost_krw + projected_savings_pct + projected_savings_amount + confidence_score + severity + apply button + reject button + apply 시 Epic 12 2FA 챌린지 + audit-first INSERT `recommendation_generated` CR 1-1 verbatim + Recharts 2.12.7 AD-14 stack pin 결정 wire)
- F30.6-4 `IdleResourcePanel` component 결정 wire (Phase 12 wire `f3c0e63` anomaly detection z-score 기반 idle 표시 + 13 columns idle_resource_id + resource_id + resource_type + idle_reason + idle_duration_days + current_cost_krw_per_month + potential_savings_krw_per_month + idle_severity + action + detection_method + terminate button + downsize button + severity color coding low=blue + medium=yellow + high=red + RTL render discipline CR 11-4 D-003 verbatim 결정 wire)
- F30.6-5 `CommitmentRecommendationPanel` component 결정 wire (Phase 13 wire `8b98030` forecast 12-month baseline 기반 RI/SP 권고 표시 + 12 columns recommendation_id + commitment_type + commitment_term + resource_pattern + current_on_demand_cost + projected_commit_cost + projected_savings_pct + break_even_months + roi_pct + severity + apply button + simulation toggle + 1y/3y 비교 차트 Recharts 2.12.7 AD-14 stack pin 결정 wire)
- F30.6-6 ko-KR.json `finops_optimization.*` namespace EXTENSION ~30 keys 결정 wire (CR 11-4 D-002 verbatim SSOT) + `finops_optimization.strategy.rightsize_down` + `finops_optimization.strategy.idle_terminate` + `finops_optimization.strategy.commit_1y` + `finops_optimization.resource.compute` + `finops_optimization.resource.storage` + `finops_optimization.resource.database` + `finops_optimization.resource.network` + `finops_optimization.resource.container` + `finops_optimization.severity.low` + `finops_optimization.severity.medium` + `finops_optimization.severity.high` + `finops_optimization.action.terminate` + `finops_optimization.action.downsize` + `finops_optimization.action.review` 등 결정 wire)
- F30.6-7 ARIA labels WCAG 2.1 AA + Epic 12 2FA 챌린지 보존 결정 wire (ko-KR inline ARIA + i18n SSOT + keyboard navigation Tab + Enter + Arrow keys + screen reader 지원 + Phase 14 Epic 1 UX v1.0 locked decision Dark MVP / WCAG AA / Professional / ko-KR verbatim 보존)
- F30.6-8 toast notification 결정 wire (recommendation_generated 시 toast 자동 표시 severity=low → blue + 5초 / medium → yellow + 10초 / high → red + 15초 + idle_resource_detected 시 toast severity 별 색상 + duration + commitment_recommended 시 toast 결정 wire)
- F30.6-9 Vitest RTL render discipline CR 11-4 D-003 verbatim 적용 결정 wire (Phase 13 wire `8b98030` anomaly-dashboard.test.tsx pattern verbatim 미러)
- F30.6-10 FinOps optimization dashboard parity CR 12-5 D-PARITY-01 결정 wire (TS mirror `apps/web/lib/finops-optimization/finops-optimization-client.ts` NEW ~+150 LOC + `tests/web/test_finops_optimization_dashboard_parity.py` NEW ~+10 cases + 1-line ko-KR reject 결정 wire)

### §F30.7 Capability matrix v1.40 EXTENSION (12 sub-ACs)
- F30.7-1 Capability matrix v1.39 → v1.40 EXTENSION 결정 wire (1 NEW row FINOPS_OPTIMIZATION industry-agnostic 4-industry grants ✅/✅/✅/✅ CR 12-1 L4 precedent 미러)
- F30.7-2 `apps/api/core/capability.py` MODIFIED 결정 wire (Capability.FINOPS_OPTIMIZATION = "finops_optimization" 1 NEW enum + 4 `_INDUSTRY_CAPABILITIES` blocks EXTENSION industry-agnostic ✅/✅/✅/✅)
- F30.7-3 `apps/api/dependencies/capability.py` MODIFIED 결정 wire (require_finops_optimization 1 NEW dep + `__all__` EXTENSION)
- F30.7-4 `docs/capability-matrix.md` MODIFIED 결정 wire (capability matrix v1.39 → v1.40 EXTENSION + 1 NEW row FINOPS_OPTIMIZATION industry-agnostic 4-industry grants ✅/✅/✅/✅ + FINOPS_OPTIMIZATION section 신규 추가)
- F30.7-5 `apps/api/modules/finops/optimization/__init__.py` NEW + `apps/api/modules/finops/optimization/serializers.py` NEW 결정 wire (Phase 13 wire `8b98030` m21_finops_forecast EXTENSION pattern verbatim 미러 + m22_finops_optimization module 결정 wire)
- F30.7-6 미허용 tenant 의 optimization 진입 차단 결정 wire (require_finops_optimization dep + capability gate per-tenant on/off + 403 Forbidden + FORBIDDEN_KO message 결정 wire ("FinOps Optimization & Rightsizing capability 미허용 tenant") + Epic 12 2FA 챌린지 보존 + AD-22 owner-only RBAC 정합)
- F30.7-7 phase_13 carry-over 진입 차단 결정 wire (optimization 진입 시 phase_13 FINOPS_FORECASTING_CAPACITY_PLANNING capability 도 동시에 검증 + optimization 가 FINOPS_OPTIMIZATION 만 있고 FINOPS_FORECASTING_CAPACITY_PLANNING 없는 경우 403 Forbidden 결정 wire)
- F30.7-8 drift detector 8 NEW pytest cases 결정 wire (`tests/integration/test_capability_matrix_v1_40_drift.py` NEW + Phase 13 wire `8b98030` `test_capability_matrix_v1_39_drift.py` 패턴 verbatim 미러)
- F30.7-9 m22_finops_optimization module 결정 wire (apps/api/modules/finops/__init__.py EXTENSION + m22_finops_optimization.optimization_serializers NEW 결정 wire + Phase 13 wire `8b98030` m21_finops_forecast.finops_forecast_serializers EXTENSION pattern verbatim 미러)
- F30.7-10 SSOT RED→GREEN EXTENSION + A36 SDR 검증 4-step 자동 적용 결정 wire (capability matrix v1.40 신규 1 row + capability.py EXTENSION 1 NEW enum + require_finops_optimization 1 NEW dep 결정 wire + drift detector EXTENSION)
- F30.7-11 CR 12-1 L4 industry-agnostic capability 결정 wire (FINOPS_OPTIMIZATION industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire manufacturing + service + manufacturing_service + manufacturing_service_other 모두 허용)
- F30.7-12 capability gate 의 fail-closed 결정 wire (미허용 tenant 의 optimization 진입 차단 + capability matrix v1.40 row 부재 시 fail-closed + Capability enum 부재 시 fail-closed + AD-22 owner-only RBAC 정합 + Epic 12 2FA 챌린지 보존 + NFR4 PII minimization 정합 보존)

### §F30.8 dry-run + Tests + wire scope T1~T8 (12 sub-ACs)
- F30.8-1 dry-run mode 결정 wire (`--finops-optimization-dry-run` + `--finops-rightsizing-dry-run` + `--finops-idle-resource-dry-run` + `--finops-commitment-dry-run` 4 CLI flag + optimization definition dry-run parameter + rightsizing dry-run parameter + idle resource dry-run parameter + commitment dry-run parameter + dry-run 시 actual `optimization_definition_updated` audit-first INSERT skip + dry-run 시 actual `recommendation_generated` audit-first INSERT skip + dry-run 시 actual `idle_resource_detected` audit-first INSERT skip + dry-run 시 actual `commitment_recommended` audit-first INSERT skip 결정 wire)
- F30.8-2 dry-run 의 preview 결과 결정 wire (phase_14_finops_optimization_preview + phase_14_finops_rightsizing_preview + phase_14_finops_idle_resource_preview + phase_14_finops_commitment_preview 4 table 결정 wire + preview_id UUID PK + tenant_id UUID + preview_type enum + period_key TEXT + preview_data JSONB + computed_at TIMESTAMPTZ DEFAULT NOW() + trace_id TEXT + RLS 자동 적용 CR 0-2 verbatim 결정 wire + audit-first INSERT `optimization_dry_run_executed` CR 1-1 verbatim 결정 wire)
- F30.8-3 dry-run 의 CLI flag 결정 wire (`--finops-optimization-dry-run` + `--finops-rightsizing-dry-run` + `--finops-idle-resource-dry-run` + `--finops-commitment-dry-run` 4 NEW CLI flag + Phase 13 wire `8b98030` `--finops-forecast-dry-run` + `--finops-capacity-dry-run` + `--finops-burnrate-dry-run` 패턴 verbatim 미러)
- F30.8-4 tests ~+56 NEW pytest PASS 결정 wire (optimization_definition 6 + rightsizing_engine 8 + idle_resource_detector 8 + commitment_recommender 8 + optimization_accuracy_tracker 5 + alembic 0046 5 + audit action 8 + capability matrix v1.40 8 = ~+56 NEW pytest PASS)
- F30.8-5 vitest tests ~+6 NEW vitest PASS 결정 wire (OptimizationStrategySelector 1 + RightsizingRecommendationTable owner-only ack prompt AD-22 verbatim 1 + IdleResourcePanel RTL render 1 + CommitmentRecommendationPanel 1 + ko-KR SSOT 2 + finops optimization dashboard parity CR 12-5 D-PARITY-01 1 = ~+7 NEW vitest PASS)
- F30.8-6 ruff + tsc 0 NEW + SDR drift gate 결정 wire (0 NEW ruff + 0 NEW tsc + 0 regressions + SDR drift gate PASS 결정 wire + A36 SDR 검증 4-step 자동 적용)
- F30.8-7 wire scope T1~T8 결정 wire (~+30-37 files estimate = ~+20 NEW + ~+12 MODIFIED atomic single sprint = Phase 13 wire `8b98030` 의 ~30 files pattern verbatim 미러)
- F30.8-8 A19 cohesion pattern 9 surface EXTENSION PASS 결정 wire (FinOps Optimization & Rightsizing surface NEW = F30.1~F30.8 + spec surface EXTENSION + test surface EXTENSION + docs surface EXTENSION)
- F30.8-9 CR lessons applied 14종 결정 wire (CR 0-2 + CR 1-1 + CR 4-3/4-4 + CR 1-1 ContextVar + CR 1-1 RSC boundary + CR 9-6 + CR 11-3 + CR 11-4 + CR 12-1 + CR 12-5 D-14 + CR 12-5 D-PARITY-01 + CR 12-5 D-GATE-01 + A19 cohesion + A36 SDR 검증)
- F30.8-10 D-DEFER-* honestly 결정 wire (D-FINOPS-4 honestly preserved → Phase 14 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire + D-FINOPS-3 ✅ RESOLVED + D-FINOPS-2 ✅ RESOLVED + D-FINOPS-1 ✅ RESOLVED + D-SLO-1 ✅ RESOLVED + D-CHAOS-1 ✅ RESOLVED + D-PERFORMANCE-1 ✅ RESOLVED + D-OBSERVABILITY-1 ✅ RESOLVED + D-RETENTION-1 ✅ RESOLVED + D-EPIC-17-WIRE-DEFER-T2-T3-UI ✅ RESOLVED + D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED + D-EPIC-16-REVIEW-DEFER-2~6 ✅ RESOLVED + D-1-1-DEFER-1/2/3 ✅ RESOLVED 모두 보존)
- F30.8-11 Epic 1 ~ Epic 17 + Phase 3 ~ Phase 13 + 1st release cycle 정합 보존 결정 wire (cj-style 117번째 wire entry 모두 DONE 진입 정합 보존 + Phase 14 PRD entry `0e3f8d9` + Phase 13 close-out retro `850b4f8` + Phase 13 atomic wire T1~T8 `8b98030` + Phase 13 spec entry `77ed55f` + Phase 13 PRD entry `d31dfc8` 모두 정합)
- F30.8-12 partial wire 시도 0건 + single sprint atomic docs-only wire 1 진입점 결정 wire (cj-style 118번째 epic 연속 정직 회복 Phase 14 spec entry atomic docs-only wire 5 files atomic single sprint 결정 wire)

## 8 tasks (T1~T8) + 68 subtasks

### T1: optimization_definition + optimization_dsl module (10 subtasks)
- T1.1: `apps/api/modules/finops/optimization_definition.py` NEW (~+150 LOC + define_optimization builder + AST 5 levels + parser 검증 3 layer + 4 industries baseline + per-tenant override EXTENSION + OPTIMIZATION_DEFAULTS constants 결정 wire)
- T1.2: OptimizationDefinition TypedDict 11 fields 결정 wire (optimization_id + tenant_id + resource_type enum + optimization_strategy enum + target_metric enum + baseline_period enum + status enum + created_at + updated_at + trace_id)
- T1.3: 5 resource_type 옵션 결정 wire (compute + storage + database + network + container + per-tenant override EXTENSION)
- T1.4: 6 optimization_strategy 옵션 + 1 composite default 결정 wire (rightsize_down + rightsize_up + idle_terminate + commit_1y + commit_3y + storage_tier_down + composite default)
- T1.5: optimization definition pure validator CR 11-4 P-015 verbatim 적용 결정 wire (parse_optimization_definition 함수 + 6 validation rules + 5 layer defense + OptimizationDefinitionInvalidError(400) CR 12-5 D-14 envelope)
- T1.6: 6 NEW pytest cases 결정 wire (TypedDict validation + 5 resource_type 옵션 + 6 optimization_strategy 옵션 + 4 target_metric 옵션 + 5 baseline_period 옵션 + 4 industries baseline + audit-first INSERT + owner-only RBAC + dry_run default)
- T1.7: optimization_definition DSL audit-first INSERT `optimization_definition_updated` 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_OPTIMIZATION + emit_audit_typed BEFORE optimization definition update + per-tenant RLS 자동 적용)
- T1.8: optimization_definition owner-only RBAC AD-22 결정 wire (optimization definition 모두 owner-only + Epic 12 2FA 챌린지 + governance_required=True mandatory)
- T1.9: optimization_definition dry-run mode default 결정 wire (dry_run=True flag + audit-first INSERT `optimization_dry_run_executed` + no actual optimization definition update)
- T1.10: optimization_definition CR 0-2 RLS verbatim 적용 결정 wire + tenant_id selector + cross-tenant isolation 검증 + phase_14_finops_optimization_definition table 결정 wire

### T2: rightsizing_engine + 5 resource types + optimization_dsl module (10 subtasks)
- T2.1: `apps/api/modules/finops/rightsizing_engine.py` NEW (~+200 LOC + recommend_rightsizing 함수 + 5 resource types parallel run + Phase 13 wire `8b98030` capacity_headroom_report EXTENSION 결정 wire + CR 12-5 D-PARITY-01 verbatim)
- T2.2: RightsizingRecommendation TypedDict 14 fields 결정 wire (recommendation_id + tenant_id + resource_id + resource_type enum + current_instance_type + recommended_instance_type + current_cost_krw + recommended_cost_krw + projected_savings_pct + projected_savings_amount_krw + confidence_score + recommendation_severity + model_version + generated_at + trace_id)
- T2.3: 5 resource types 결정 wire (compute EC2 + storage S3 EBS + database RDS + network EIP NAT LB + container EKS + Phase 13 wire `8b98030` capacity_headroom_report 의 90일 lookahead forecast EXTENSION)
- T2.4: instance type mapping table 결정 wire (INSTANCE_TYPE_DOWNGRADE_MAP 80+ AWS EC2 mapping + INSTANCE_TYPE_UPGRADE_MAP reverse + per-family mapping general_purpose + compute_optimized + memory_optimized + storage_optimized + GCP/Azure mapping JSONB)
- T2.5: compute + storage + database + network + container individual rightsizing 결정 wire (compute max_expected_utilization_pct < 70% → downsize / storage 3 tier mapping Standard → IA → Glacier / database connection_count_p95 + CPU + memory 3 metric 기반 / network EIP unattached + NAT bytes=0 + LB request < 100/day / container EKS node group desired_count 조정)
- T2.6: projected_savings calculation 결정 wire (projected_savings_krw_per_month = current_cost_krw - recommended_cost_krw + annualized × 12 + Phase 11 wire `e020ad0` chargeback cost allocation EXTENSION)
- T2.7: confidence_score calculation 결정 wire (Phase 13 wire `8b98030` forecast_accuracy 의 MAPE 기반 + confidence_score = (1 - normalized_mape) × 100 + confidence_score < 70% → low severity + 70~90% → medium + ≥ 90% → high)
- T2.8: audit-first INSERT `recommendation_generated` 결정 wire (CR 1-1 verbatim 적용 + ActionClass.FINOPS_OPTIMIZATION + emit_audit_typed BEFORE recommendation generation + per-tenant RLS 자동 적용)
- T2.9: typed exception envelope CR 12-5 D-14 verbatim 결정 wire (3 NEW typed exception classes: RightsizingEngineError + InstanceTypeMappingError + RecommendationConfidenceLowError)
- T2.10: 8 NEW pytest cases 결정 wire (5 resource types + instance type mapping + projected_savings calculation + confidence_score calculation + audit-first INSERT + typed exception envelope)

### T3: idle_resource_detector + z-score based detection + commitment_recommender (10 subtasks)
- T3.1: `apps/api/modules/finops/idle_resource_detector.py` NEW (~+180 LOC + detect_idle_resources 함수 + 5 resource type idle 정의 + Phase 12 wire `f3c0e63` anomaly_detection 의 z-score < -2.0 EXTENSION 결정 wire + CR 12-5 D-PARITY-01 verbatim)
- T3.2: IdleResource TypedDict 13 fields 결정 wire (idle_resource_id + tenant_id + resource_id + resource_type enum + idle_reason + idle_duration_days + current_cost_krw_per_month + potential_savings_krw_per_month + idle_severity enum + action enum + detection_method enum + detection_window_days + generated_at + trace_id)
- T3.3: compute + storage + database + network + container 5 idle 정의 결정 wire (compute: P95 CPU < 5% + memory < 10% for 30d / storage: S3 last_accessed > 30d + EBS unattached + snapshot > 90d / database: connection_count_p95 = 0 for 30d / network: EIP associated=false + NAT bytes=0 + LB request < 100/day / container: EKS desired_count × utilization < 30%)
- T3.4: z-score idle detection + severity classification 결정 wire (z_score = (utilization_p95 - mean_30d) / std_30d + z_score < -2.0 → idle classify + Phase 12 wire `f3c0e63` multi-method voting consensus 3 of 4 methods agree EXTENSION + potential_savings_krw < 10000 → low / 10000~100000 → medium / ≥ 100000 → high)
- T3.5: action recommendation 결정 wire (idle_severity=low → action='review' / medium → 'downsize' / high → 'terminate' + per-tenant override action_policy + 자동 terminate 시 Epic 12 2FA 챌린지 보존)
- T3.6: `apps/api/modules/finops/commitment_recommender.py` NEW (~+150 LOC + recommend_commitments 함수 + commitment_type enum 6 + commitment_term enum 2 + break-even calculation + Phase 13 wire `8b98030` forecast 12-month baseline EXTENSION)
- T3.7: CommitmentRecommendation TypedDict 12 fields + ROI calculation 결정 wire (recommendation_id + tenant_id + commitment_type enum + commitment_term enum + resource_pattern + current_on_demand_cost_krw + projected_commit_cost_krw + projected_savings_pct + projected_savings_krw + upfront_cost_krw + break_even_months + roi_pct + recommendation_severity + generated_at + trace_id + roi_pct = (total_3y_savings - upfront_cost) / upfront_cost × 100)
- T3.8: break-even calculation + 1y/3y 시뮬레이션 결정 wire (break_even_months = upfront_cost / monthly_savings + 1y ≤ 8mo / 3y ≤ 18mo threshold + 1y/3y 두 가지 시나리오 동시 계산 + on-demand 유지 옵션 fallback)
- T3.9: typed exception envelope CR 12-5 D-14 verbatim 결정 wire (6 NEW typed exception classes: IdleResourceDetectionError + IdleSeverityClassificationError + IdleMetricUnavailableError + CommitmentRecommendationError + PricingDataUnavailableError + BreakEvenCalculationError)
- T3.10: 8 NEW pytest cases 결정 wire (5 idle 정의 + z-score detection + severity classification + 6 commitment_type + 1y/3y break-even + ROI calculation + audit-first INSERT + typed exception envelope)

### T4: optimization_accuracy_tracker + Phase 13 forecast_accuracy_tracker EXTENSION (10 subtasks)
- T4.1: `apps/api/modules/finops/optimization_accuracy_tracker.py` NEW (~+120 LOC + track_optimization_accuracy 함수 + per-(tenant_id + resource_type + optimization_strategy) granularity + Phase 13 wire `8b98030` forecast_accuracy_tracker EXTENSION chain 결정 wire)
- T4.2: precision + recall + realized_savings 3 metrics 결정 wire (precision = TP / (TP + FP) + recall = TP / (TP + FN) + realized_savings_krw_per_month + Phase 11 wire `e020ad0` showback 의 period selector EXTENSION current/previous month 비교)
- T4.3: projected_vs_realized_savings + accuracy_score calculation 결정 wire (accuracy_score = realized_savings / projected_savings × 100 + accuracy_score ≥ 80% → high / 50~80% → moderate / < 50% → low + per-tenant override accuracy_threshold default 70%)
- T4.4: false_positive + false_negative tracking 결정 wire (false_positive_reasons enum overestimation + performance_degradation + business_growth + seasonality_mismatch + application_change + Phase 12 wire `f3c0e63` anomaly_detection false_positive EXTENSION 정합 + false_negative = applicable opportunity detection miss EXTENSION)
- T4.5: OptimizationAccuracyReport TypedDict 10 fields 결정 wire (report_id + tenant_id + resource_type + optimization_strategy + total_recommendations + applied_recommendations + precision + recall + realized_savings_krw + projected_savings_krw + accuracy_score + generated_at + trace_id)
- T4.6: model_performance_degradation_detection 결정 wire (accuracy_score < 70% for 3 consecutive months → recommendation engine retraining trigger + Phase 13 wire `8b98030` model_retraining_triggered EXTENSION + retraining cron KST 매주 일요일 04:00 UTC 19:00)
- T4.7: recommended_action audit-first INSERT EXTENSION 결정 wire (`optimization_recommended_action` 1 NEW action + ActionClass.FINOPS_OPTIMIZATION + emit_audit_typed BEFORE recommended action apply + per-tenant RLS 자동 적용)
- T4.8: model_version tracking 결정 wire (rightsizing_engine + idle_resource_detector + commitment_recommender 3 engine 모두 semantic versioning MAJOR.MINOR.PATCH + model_version JSONB metadata + Phase 13 wire `8b98030` forecast_model_registry EXTENSION)
- T4.9: typed exception envelope CR 12-5 D-14 verbatim 결정 wire (3 NEW typed exception classes: OptimizationAccuracyTrackingError + OptimizationRetrainingTriggerError + OptimizationPerformanceDegradationError)
- T4.10: 5 NEW pytest cases 결정 wire (precision + recall + realized_savings + projected_vs_realized + false_positive + false_negative + model_performance_degradation_detection + model retraining trigger + audit-first INSERT + typed exception envelope)

### T5: alembic 0046 phase_14_optimization (8 subtasks)
- T5.1: `apps/api/alembic/versions/0046_phase_14_optimization.py` NEW (~+250 LOC + 5 tables CREATE + indexes + RLS policies + down_revision "0045_phase_13_forecasting" 결정 wire)
- T5.2: phase_14_finops_optimization_definition table 12 columns 결정 wire (optimization_id UUID PK + tenant_id UUID + resource_type TEXT enum + optimization_strategy TEXT enum + target_metric TEXT enum + baseline_period TEXT enum + status TEXT enum + created_at TIMESTAMPTZ + updated_at TIMESTAMPTZ + trace_id TEXT + tenant_id_resource_type_baseline_period UNIQUE constraint + JSONB metadata)
- T5.3: phase_14_finops_rightsizing_recommendation table 15 columns 결정 wire (recommendation_id UUID PK + tenant_id UUID + resource_id TEXT + resource_type TEXT enum + current_instance_type TEXT + recommended_instance_type TEXT + current_cost_krw NUMERIC(20, 2) + recommended_cost_krw NUMERIC(20, 2) + projected_savings_pct NUMERIC(8, 4) + projected_savings_amount_krw NUMERIC(20, 2) + confidence_score NUMERIC(8, 4) + recommendation_severity TEXT enum + model_version TEXT + generated_at TIMESTAMPTZ + trace_id TEXT)
- T5.4: phase_14_finops_idle_resource table 14 columns 결정 wire (idle_resource_id UUID PK + tenant_id UUID + resource_id TEXT + resource_type TEXT enum + idle_reason TEXT + idle_duration_days INTEGER + current_cost_krw_per_month NUMERIC(20, 2) + potential_savings_krw_per_month NUMERIC(20, 2) + idle_severity TEXT enum + action TEXT enum + detection_method TEXT enum + detection_window_days INTEGER + generated_at TIMESTAMPTZ + trace_id TEXT)
- T5.5: phase_14_finops_commitment_recommendation table 13 columns 결정 wire (recommendation_id UUID PK + tenant_id UUID + commitment_type TEXT enum + commitment_term TEXT enum + resource_pattern TEXT + current_on_demand_cost_krw NUMERIC(20, 2) + projected_commit_cost_krw NUMERIC(20, 2) + projected_savings_pct NUMERIC(8, 4) + projected_savings_krw NUMERIC(20, 2) + upfront_cost_krw NUMERIC(20, 2) + break_even_months INTEGER + roi_pct NUMERIC(8, 4) + generated_at TIMESTAMPTZ + trace_id TEXT)
- T5.6: phase_14_finops_optimization_accuracy table 11 columns 결정 wire (report_id UUID PK + tenant_id UUID + resource_type TEXT enum + optimization_strategy TEXT enum + total_recommendations INTEGER + applied_recommendations INTEGER + precision NUMERIC(8, 4) + recall NUMERIC(8, 4) + realized_savings_krw NUMERIC(20, 2) + projected_savings_krw NUMERIC(20, 2) + accuracy_score NUMERIC(8, 4) + generated_at TIMESTAMPTZ + trace_id TEXT)
- T5.7: 5 tables RLS policies 결정 wire (CR 0-2 verbatim + tenant_id = current_setting('app.tenant_id')::uuid + Phase 13 wire `8b98030` phase_13_finops_* table 정합 + Phase 12 wire `f3c0e63` phase_12_finops_* table 정합 + Phase 11 wire `e020ad0` phase_11_finops_* table 정합 + Phase 10 wire `ac5d6c5` phase_10_slo_* table 정합)
- T5.8: 5 indexes 결정 wire (idx_phase_14_finops_optimization_definition_tenant_id_resource_type + idx_phase_14_finops_rightsizing_recommendation_tenant_id_resource_type + idx_phase_14_finops_idle_resource_tenant_id_resource_type + idx_phase_14_finops_commitment_recommendation_tenant_id_commitment_type + idx_phase_14_finops_optimization_accuracy_tenant_id_resource_type) + alembic migration 5 NEW pytest cases + multi-tenant isolation test 결정 wire (`tests/integration/test_finops_optimization_tenant_isolation.py` NEW + Phase 13 wire `8b98030` `test_finops_forecast_tenant_isolation.py` 패턴 verbatim 미러)

### T6: audit action EXTENSION 8 NEW + typed exception envelope 14 NEW (8 subtasks)
- T6.1: `apps/api/core/audit_action.py` MODIFIED 결정 wire (ActionClass.FINOPS_OPTIMIZATION 1 NEW class 신규 정의 + FinopsOptimizationAction Literal 8 NEW values + _ActionRegistry FINOPS_OPTIMIZATION entry 신규 1개 등록 + __all__ EXTENSION + AuditAction Union EXTENSION)
- T6.2: ActionClass.FINOPS_OPTIMIZATION = 'finops_optimization' 신규 정의 결정 wire (CR 12-1 L4 precedent 미러 FINOPS_FORECASTING_CAPACITY_PLANNING Phase 13 wire + FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire + FINOPS_SHOWBACK + FINOPS_CHARGEBACK Phase 11 wire + SLO_ENGINEERING Phase 10 wire + CHAOS_ENGINEERING Phase 9 wire + PERFORMANCE_TESTING Phase 8 wire + OBSERVABILITY_TRACES + OBSERVABILITY_METRICS Phase 7 wire pattern verbatim bind)
- T6.3: FinopsOptimizationAction Literal 8 NEW values 결정 wire = `optimization_definition_updated` + `recommendation_generated` + `idle_resource_detected` + `commitment_recommended` + `optimization_recommended_action` + `optimization_dry_run_executed` + `optimization_accuracy_degraded` + `optimization_retraining_triggered` (CR 1-1 verbatim 적용)
- T6.4: _ActionRegistry FINOPS_OPTIMIZATION entry 신규 1개 등록 결정 wire (resource_table "phase_14_finops_*" + action_class=FINOPS_OPTIMIZATION + 8 NEW actions acceptance + reject)
- T6.5: emit_audit_typed BEFORE/AFTER FinOps Optimization event CR 1-1 verbatim 적용 결정 wire (optimization_definition_updated 의 audit_first INSERT 가 optimization definition 직전에 실행 + recommendation_generated AFTER recommendation generation + idle_resource_detected AFTER idle resource detection + commitment_recommended AFTER commitment recommendation + optimization_recommended_action BEFORE recommended action apply + optimization_dry_run_executed AFTER dry-run + optimization_accuracy_degraded BEFORE model retraining trigger + optimization_retraining_triggered AFTER retraining trigger + trace_id propagation + actor_id capture + tenant_id capture)
- T6.6: multi-tenant isolation 결정 wire (8 NEW action 의 tenant_id 가 RLS 와 정합 + cross-tenant audit log leak 방지 결정 wire)
- T6.7: typed exception envelope CR 12-5 D-14 verbatim 결정 wire (14 NEW typed exception classes: OptimizationDefinitionInvalidError(400) + OptimizationScopeInvalidError(404) + OptimizationInventoryUnavailableError(422) + RightsizingEngineError(500) + InstanceTypeMappingError(500) + RecommendationConfidenceLowError(422) + IdleResourceDetectionError(500) + IdleSeverityClassificationError(500) + IdleMetricUnavailableError(404) + CommitmentRecommendationError(500) + PricingDataUnavailableError(404) + BreakEvenCalculationError(500) + OptimizationAccuracyTrackingError(500) + OptimizationRetrainingTriggerError(500) + OptimizationPerformanceDegradationError(500))
- T6.8: 8 NEW pytest cases 결정 wire (AuditAction Literal 값 검증 + ActionClass.FINOPS_OPTIMIZATION enum value + resource_table + emit_audit_typed BEFORE/AFTER FinOps Optimization event CR 1-1 verbatim 적용 + multi-tenant isolation + trace_id propagation + typed exception envelope + dry-run default)

### T7: capability v1.40 EXTENSION + frontend finops optimization dashboard (8 subtasks)
- T7.1: `apps/api/core/capability.py` MODIFIED 결정 wire (Capability.FINOPS_OPTIMIZATION 1 NEW enum + 4 `_INDUSTRY_CAPABILITIES` blocks EXTENSION industry-agnostic ✅/✅/✅/✅ CR 12-1 L4 precedent 미러)
- T7.2: `apps/api/dependencies/capability.py` MODIFIED 결정 wire (require_finops_optimization 1 NEW dep + __all__ EXTENSION 결정 wire)
- T7.3: capability matrix v1.39 → v1.40 EXTENSION title update + v1.40 changelog entry prepend + 1 NEW row FINOPS_OPTIMIZATION industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire
- T7.4: `tests/integration/test_capability_matrix_v1_40_drift.py` NEW 8 NEW pytest cases 결정 wire (Capability.FINOPS_OPTIMIZATION enum + 4 industries grants + v1.39 + v1.38 + v1.37 + v1.36 + v1.35 + v1.34 + v1.33 + v1.32 + v1.31 + v1.30 + v1.29 preservation + Phase 5 v1.29 + Epic 16 v1.28 + Epic 17 v1.30 + Phase 6 v1.31 + Phase 7 v1.32 + Phase 8 v1.33 + Phase 9 v1.34 + Phase 10 v1.35 + Phase 11 v1.36 + Phase 12 v1.37 + Phase 13 v1.38 + Phase 13 v1.39 pattern verbatim)
- T7.5: `docs/capability-matrix.md` MODIFIED v1.39 → v1.40 EXTENSION 결정 wire (1 NEW row FINOPS_OPTIMIZATION industry-agnostic 4-industry grants + FINOPS_OPTIMIZATION section 신규 추가)
- T7.6: 미허용 tenant 의 FinOps Optimization 진입 차단 결정 wire (require_finops_optimization dep + capability gate per-tenant on/off + phase_13 carry-over 검증)
- T7.7: `apps/web/app/[locale]/(dashboard)/admin/finops/optimization/page.tsx` NEW (~+150 LOC + 5 components 결정 wire: OptimizationStrategySelector + RightsizingRecommendationTable + IdleResourcePanel + CommitmentRecommendationPanel + OptimizationAccuracyPanel + owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 보존)
- T7.8: SSOT RED→GREEN EXTENSION 결정 wire (capability matrix v1.40 신규 1 row + capability.py EXTENSION 1 NEW enum + require_finops_optimization 1 NEW dep wire + drift detector EXTENSION + frontend finops optimization dashboard wire)

### T8: atomic commit (4 subtasks)
- T8.1: 3중 게이트 impact NONE 결정 wire (ruff scoped 0 NEW + pytest 0 NEW failures + vitest 0 NEW failures + tsc 0 NEW errors)
- T8.2: A19 cohesion pattern 9 surface EXTENSION PASS 결정 wire (FinOps Optimization & Rightsizing surface NEW = F30.1~F30.8)
- T8.3: atomic commit via `git commit -F <file>` 결정 wire (CR 9-6 D5 prevention + PowerShell here-string 회피)
- T8.4: sprint-status.yaml `phase-14-spec-entry: backlog → done` transition 결정 wire

## Dev Notes (CR lessons applied 14종)

- **CR 0-2 RLS lesson ✅ APPLIED**: Phase 14 wire 시점에 phase_14_finops_optimization_definition + phase_14_finops_rightsizing_recommendation + phase_14_finops_idle_resource + phase_14_finops_commitment_recommendation + phase_14_finops_optimization_accuracy + phase_14_finops_optimization_preview + phase_14_finops_rightsizing_preview + phase_14_finops_idle_resource_preview + phase_14_finops_commitment_preview 9 tables 모두 RLS 자동 적용 + multi-tenant isolation test 결정 wire + tenant-scoped result_hash 결정 wire + Phase 13 wire `8b98030` phase_13_finops_* table 정합 + Phase 12 wire `f3c0e63` phase_12_finops_* table 정합 + Phase 11 wire `e020ad0` phase_11_finops_* table 정합 + Phase 10 wire `ac5d6c5` phase_10_slo_* table 정합 + Phase 5 wire `f093f8c` phase_5_replication_lag table 정합
- **CR 1-1 audit-first INSERT ✅ APPLIED**: ActionClass.FINOPS_OPTIMIZATION 신규 정의 + 8 NEW audit log entries (`optimization_definition_updated` + `recommendation_generated` + `idle_resource_detected` + `commitment_recommended` + `optimization_recommended_action` + `optimization_dry_run_executed` + `optimization_accuracy_degraded` + `optimization_retraining_triggered`) 결정 wire + emit_audit_typed BEFORE/AFTER FinOps Optimization event CR 1-1 verbatim 적용
- **CR 4-3/4-4 lessons carry ✅ APPLIED**: optimization baseline + idle detection baseline + commitment baseline + golden_diff pattern verbatim 미러 + tenant-scoped result_hash 결정 wire + Epic 8 wire `e117e09` capability drift detector 정합 패턴 + Phase 13 wire `8b98030` forecast accuracy baseline result_hash 패턴 verbatim + Phase 12 wire `f3c0e63` optimization accuracy baseline result_hash 패턴 verbatim
- **CR 1-1 ContextVar lesson ✅ APPLIED**: trace_id request-scoped ContextVar 바인딩 + 비동기 trace context 보존 CR 1-1 verbatim 적용 + FinOps Optimization event 의 trace_id propagation 결정 wire
- **CR 1-1 RSC boundary lesson ✅ APPLIED**: `apps/web/app/[locale]/(dashboard)/admin/finops/optimization/page.tsx` Client-only + finops optimization dashboard server-only delegation 결정 wire + CR 1-1 verbatim 적용
- **CR 9-6 commit message discipline ✅ APPLIED**: `git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention 결정 wire
- **CR 11-3 honest-DEFER discipline ✅ APPLIED**: 118번째 epic 연속 정직 회복 결정 wire (D-1-1-DEFER-* + D-EPIC-16-REVIEW-DEFER-* + D-PHASE-4-DR-DEFER-* + D-EPIC-17-WIRE-DEFER-T2-T3-UI + D-RETENTION-1 + D-OBSERVABILITY-1 + D-PERFORMANCE-1 + D-CHAOS-1 + D-SLO-1 + D-FINOPS-1 + D-FINOPS-2 + D-FINOPS-3 모두 ✅ ALL RESOLVED 보존 + D-FINOPS-4 honestly DEFER 보존 진입 결정 wire)
- **CR 11-4 D-001~D-005 + P-015 lessons carry ✅ APPLIED**: dry-run mode UI 진입 시 frontend territory 정합 sweep 결정 wire + ko-KR.json SSOT only + vitest RTL render discipline + owner-only RBAC + unknown state reject + ko-KR.json SSOT drift detector 결정 wire
- **CR 12-1 L4 industry-agnostic capability ✅ APPLIED**: FINOPS_OPTIMIZATION industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire + capability matrix v1.40 EXTENSION 결정 wire
- **CR 12-5 D-14 typed exception envelope ✅ APPLIED**: 14 NEW typed exception classes (OptimizationDefinitionInvalidError(400) + OptimizationScopeInvalidError(404) + OptimizationInventoryUnavailableError(422) + RightsizingEngineError(500) + InstanceTypeMappingError(500) + RecommendationConfidenceLowError(422) + IdleResourceDetectionError(500) + IdleSeverityClassificationError(500) + IdleMetricUnavailableError(404) + CommitmentRecommendationError(500) + PricingDataUnavailableError(404) + BreakEvenCalculationError(500) + OptimizationAccuracyTrackingError(500) + OptimizationRetrainingTriggerError(500) + OptimizationPerformanceDegradationError(500)) 결정 wire + apps/api/main.py EXTENSION 결정 wire
- **CR 12-5 D-PARITY-01 inversion ✅ APPLIED**: Python FastAPI backend optimization_definition.py + rightsizing_engine.py + idle_resource_detector.py + commitment_recommender.py + optimization_accuracy_tracker.py TypedDict ↔ TypeScript Next.js frontend finops-optimization-client.ts interface parity 결정 wire + vitest CR 12-5 D-PARITY-01 검증 결정 wire
- **CR 12-5 D-GATE-01 inversion ✅ APPLIED**: FINOPS_OPTIMIZATION capability gate per-tenant on/off + owner-only RBAC AD-22 결정 wire + gate 적용 대상 명시 결정 wire
- **A19 cohesion pattern 9 surface EXTENSION PASS ✅**: FinOps Optimization & Rightsizing surface NEW = F30.1~F30.8 FinOps Optimization & Rightsizing territory 결정 wire + spec surface EXTENSION + test surface EXTENSION + docs surface EXTENSION 결정 wire
- **A36 SDR 검증 4-step 자동 적용 ✅**: commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS 결정 wire
- **AD-14 stack pin ✅ APPLIED**: Recharts 2.12.7 + slack-sdk==3.23.0 + pdpyras==5.2.0 (Phase 13 wire statsmodels==0.14.1 + prophet==1.1.5 + tensorflow==2.15.0 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 + Recharts 2.12.7 EXTENSION 결정 wire + Phase 12 wire sklearn==1.4.0 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 + Recharts 2.12.7 EXTENSION 결정 wire)
- **AD-22 owner-only RBAC ✅ APPLIED**: optimization definition update + recommendation generation + idle resource detection + commitment recommendation + optimization recommended action + optimization accuracy tracking trigger 모두 owner-only RBAC AD-22 + Epic 12 2FA 챌린지 보존 결정 wire
- **NFR4 PII minimization ✅ PRESERVED**: optimization data 는 사업 metric + cost amount 만 포함, PII 미포함 결정 wire

## Architecture Alignment (cj-style ALLOWED sweep — Phase 13 wire 정합)

**ALLOWED_SERVICE_SUBMODULES sweep CR 11-3 D-2 verbatim** (Phase 5 wire `f093f8c` + Phase 7 wire `59b56cd` + Phase 8 wire `60d4ea1` + Phase 9 wire `e7670e1` + Phase 10 wire `ac5d6c5` + Phase 11 wire `e020ad0` + Phase 12 wire `f3c0e63` + Phase 13 wire `8b98030` 정합):

### Backend (FastAPI, Python 3.12)
- ✅ `apps/api/modules/finops/` (MODIFIED EXTENSION): `optimization_definition.py` + `rightsizing_engine.py` + `idle_resource_detector.py` + `commitment_recommender.py` + `optimization_accuracy_tracker.py` + `optimization/__init__.py` NEW + `optimization/serializers.py` NEW + `__init__.py` EXTENSION + `serializers.py` EXTENSION
- ✅ `apps/api/core/capability.py` (MODIFIED): Capability.FINOPS_OPTIMIZATION enum EXTENSION + 4 INDUSTRY_CAPABILITIES EXTENSION
- ✅ `apps/api/dependencies/capability.py` (MODIFIED): require_finops_optimization EXTENSION
- ✅ `apps/api/core/audit_action.py` (MODIFIED): ActionClass.FINOPS_OPTIMIZATION + FinopsOptimizationAction Literal 8 NEW + _ActionRegistry FINOPS_OPTIMIZATION entry 1 신규 등록 + __all__ EXTENSION
- ✅ `apps/api/core/errors.py` (MODIFIED): 14 NEW typed exception classes CR 12-5 D-14 verbatim
- ✅ `apps/api/alembic/versions/0046_phase_14_optimization.py` (NEW): 5 tables + 4 preview tables + indexes + RLS policies
- ✅ `apps/api/main.py` (MODIFIED): /admin/finops/optimization/* endpoints EXTENSION (CR 1-1 RSC boundary 적용)

### Frontend (Next.js 15.x, TypeScript 5.x)
- ✅ `apps/web/app/[locale]/(dashboard)/admin/finops/optimization/page.tsx` (NEW): RSC + finops optimization dashboard
- ✅ `apps/web/app/[locale]/(dashboard)/admin/finops/optimization/layout.tsx` (NEW): RTL section wrapper
- ✅ `apps/web/components/finops/FinopsOptimizationDashboardPanel.tsx` (NEW): 5 components (OptimizationStrategySelector + RightsizingRecommendationTable + IdleResourcePanel + CommitmentRecommendationPanel + OptimizationAccuracyPanel)
- ✅ `apps/web/lib/finops-optimization/finops-optimization-client.ts` (NEW): OptimizationDefinition + RightsizingRecommendation + IdleResource + CommitmentRecommendation + OptimizationAccuracyReport TypedDict CR 12-5 D-PARITY-01 verbatim + 5 fetch wrappers + FinopsOptimizationApiError class
- ✅ `apps/web/messages/ko-KR.json` (MODIFIED): EXTENSION `finops_optimization.*` namespace ~30 keys 결정 wire

### Tests
- ✅ `tests/api/core/test_phase_14_optimization_definition.py` (NEW): ~6 NEW pytest
- ✅ `tests/api/core/test_phase_14_rightsizing_engine.py` (NEW): ~8 NEW pytest
- ✅ `tests/api/core/test_phase_14_idle_resource_detector.py` (NEW): ~8 NEW pytest
- ✅ `tests/api/core/test_phase_14_commitment_recommender.py` (NEW): ~8 NEW pytest
- ✅ `tests/api/core/test_phase_14_optimization_accuracy_tracker.py` (NEW): ~5 NEW pytest
- ✅ `tests/api/core/test_phase_14_audit_action.py` (NEW): ~8 NEW pytest
- ✅ `tests/integration/test_finops_optimization_tenant_isolation.py` (NEW): multi-tenant isolation CR 0-2 verbatim
- ✅ `tests/integration/test_capability_matrix_v1_40_drift.py` (NEW): 8 NEW pytest cases
- ✅ `apps/web/__tests__/finops-optimization/finops-optimization-dashboard.test.tsx` (NEW): ~5 NEW vitest
- ✅ `apps/web/__tests__/i18n/finops-optimization-i18n-ssot.test.ts` (NEW): SSOT drift NFR18 ko-KR 정합
- ✅ `tests/web/test_finops_optimization_dashboard_parity.py` (NEW): ~10 cases CR 12-5 D-PARITY-01 verification

### Docs
- ✅ `docs/finops-optimization-rightsizing.md` (NEW): ~+200 LOC 14 sections runbook 결정 wire
- ✅ `docs/capability-matrix.md` (MODIFIED): v1.39 → v1.40 EXTENSION

## Files Affected (estimate)

- **~20 NEW**: `apps/api/modules/finops/{optimization_definition,rightsizing_engine,idle_resource_detector,commitment_recommender,optimization_accuracy_tracker}.py` (5 files) + `apps/api/modules/finops/optimization/{__init__,serializers}.py` (2 files) + `apps/api/alembic/versions/0046_phase_14_optimization.py` + `apps/web/app/[locale]/(dashboard)/admin/finops/optimization/{page,layout}.tsx` (2 files) + `apps/web/components/finops/FinopsOptimizationDashboardPanel.tsx` + `apps/web/lib/finops-optimization/finops-optimization-client.ts` + tests (10 files) + `docs/finops-optimization-rightsizing.md`
- **~12 MODIFIED**: `apps/api/core/capability.py` + `apps/api/dependencies/capability.py` + `apps/api/core/audit_action.py` + `apps/api/core/errors.py` + `apps/api/main.py` + `apps/api/modules/finops/__init__.py` + `apps/api/modules/finops/serializers.py` + `apps/web/messages/ko-KR.json` + `docs/capability-matrix.md` + `_bmad-output/implementation-artifacts/sprint-status.yaml` + `tests/integration/conftest.py` + `apps/api/alembic/versions/script.py.mako`
- **Total**: ~32 files atomic single sprint

## Test Coverage

- **~56 NEW pytest PASS 결정 wire**:
  - `tests/api/core/test_phase_14_optimization_definition.py` (6 cases): TypedDict validation + 5 resource_type 옵션 + 6 optimization_strategy 옵션 + 4 target_metric 옵션 + 5 baseline_period 옵션 + 4 industries baseline + audit-first INSERT + owner-only RBAC + dry_run default
  - `tests/api/core/test_phase_14_rightsizing_engine.py` (8 cases): 5 resource_types + instance type mapping + projected_savings calculation + confidence_score calculation + audit-first INSERT + typed exception envelope
  - `tests/api/core/test_phase_14_idle_resource_detector.py` (8 cases): 5 idle 정의 + z-score detection + severity classification + audit-first INSERT + typed exception envelope
  - `tests/api/core/test_phase_14_commitment_recommender.py` (8 cases): 6 commitment_type + 1y/3y break-even + ROI calculation + per-tenant override + audit-first INSERT + typed exception envelope
  - `tests/api/core/test_phase_14_optimization_accuracy_tracker.py` (5 cases): precision + recall + realized_savings + projected_vs_realized + false_positive + false_negative + model_performance_degradation_detection + model retraining trigger + audit-first INSERT + typed exception envelope
  - `tests/api/core/test_phase_14_audit_action.py` (8 cases): 8 NEW audit log entries + ActionClass.FINOPS_OPTIMIZATION + emit_audit_typed CR 1-1
  - `tests/integration/test_finops_optimization_tenant_isolation.py` (5 cases): cross-tenant isolation + optimization definition isolation + rightsizing recommendation isolation + idle resource isolation + commitment recommendation isolation
  - `tests/integration/test_capability_matrix_v1_40_drift.py` (8 cases): FINOPS_OPTIMIZATION enum + 4-industry grants + v1.39 + v1.38 + ... preservation
  - **Subtotal**: ~56 NEW pytest PASS

- **~7 NEW vitest PASS 결정 wire**:
  - `apps/web/__tests__/finops-optimization/finops-optimization-dashboard.test.tsx` (5 cases): OptimizationStrategySelector + RightsizingRecommendationTable owner-only ack prompt AD-22 verbatim + IdleResourcePanel RTL render + CommitmentRecommendationPanel + OptimizationAccuracyPanel
  - `apps/web/__tests__/i18n/finops-optimization-i18n-ssot.test.ts` (1 cases): ko-KR SSOT drift detection + CR 12-5 D-PARITY-01 verification
  - `tests/web/test_finops_optimization_dashboard_parity.py` (10 cases): TS mirror parity CR 12-5 D-PARITY-01 verification
  - **Subtotal**: ~16 NEW vitest PASS (5 dashboard + 1 i18n + 10 parity = 16)

- **0 NEW ruff 결정 wire** (apps/api backend 결정 wire + 기존 ruff scoped 0 NEW 정합 보존)
- **0 NEW tsc 결정 wire** (apps/web frontend 결정 wire + 기존 tsc 0 NEW 정합 보존)
- **0 regressions 결정 wire** (3중 게이트 FINAL CLEAN + ruff scoped 0 NEW + pytest 0 NEW failures + vitest 0 NEW failures + tsc 0 NEW errors)

## Notes

- `apps/api/main.py` EXTENSION 시 /admin/finops/optimization/* endpoints EXTENSION + require_finops_optimization dep 적용
- `apps/api/core/errors.py` EXTENSION 시 14 NEW typed exception classes + envelope CR 11-4 P-015 적용
- `apps/api/core/audit_action.py` EXTENSION 시 ActionClass.FINOPS_OPTIMIZATION + FinopsOptimizationAction Literal 8 NEW values + _ActionRegistry FINOPS_OPTIMIZATION entry 1 신규 등록
- m22_finops_optimization.optimization_serializers NEW Phase 14 EXTENSION 결정 wire (Phase 13 wire `8b98030` m21_finops_forecast.finops_forecast_serializers EXTENSION pattern verbatim 미러, wire 시점에 sprint-status.yaml action_items EXTENSION)
- Phase 13 wire `8b98030` 의 forecast accuracy tracker MAE/MAPE/RMSE + capacity headroom analysis compute/storage/network 90일 lookahead + budget burn-rate projection + FinOps Forecasting & Capacity Planning territory 의 natural backend ACTIONABLE RECOMMENDATION LAYER EXTENSION 결정 wire (forecast → action)
- Phase 12 wire `f3c0e63` 의 anomaly detection baseline last 30d/90d/YTD → idle detection z-score < -2.0 EXTENSION territory 자연스러운 EXTENSION 결정 wire
- Phase 11 wire `e020ad0` 의 showback period selector (current/previous/last 3/6 months/YTD) 의 자연스러운 carry-over chain 결정 wire
- Phase 8 wire `60d4ea1` 의 cost-engine V8 골든 fixture + 12-period benchmark 의 자연스러운 carry-over chain (historical baseline ⇒ forward forecast EXTENSION 12-month prediction with 95% CI + capacity headroom 90일 lookahead + budget burn-rate EXTENSION) 결정 wire
- Phase 10 wire `ac5d6c5` 의 4 SLIs 자연스러운 EXTENSION 결정 wire + Phase 9 wire `e7670e1` chaos_experiment baseline EXTENSION 결정 wire
- Phase 7 wire `59b56cd` observability 의 Prometheus custom metrics + Slack channel EXTENSION 결정 wire + alert routing 정합
- Epic 12 2FA 챌린지 mandatory 결정 wire (optimization definition update + recommendation generation + idle resource detection + commitment recommendation + optimization recommended action apply + optimization accuracy tracking trigger 모두 Epic 12 2FA 챌린지 mandatory)
- AD-22 owner-only RBAC 보존 결정 wire (optimization definition update + recommendation generation + idle resource detection + commitment recommendation + optimization recommended action apply + optimization accuracy tracking trigger 모두 owner-only)
- AD-14 stack pin 결정 wire (Recharts 2.12.7 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0)
- NFR4 PII minimization PRESERVED (optimization data 는 사업 metric + cost amount 만 포함, PII 미포함)
- 3중 게이트 impact NONE (cj-style 118번째 spec entry 진입 표준 = docs only 변경): ruff scoped 0 NEW + pytest 0 NEW + vitest 0 NEW + tsc 0 NEW
- 8 ACs PRD §F30.1~§F30.8 verbatim → 92 sub-ACs (12+12+12+12+12+10+12+12 = 92 sub-ACs) satisfied pre-flight 정합 sweep 결정 wire

## Cross-References

- Phase 14 PRD entry `0e3f8d9` (cj-style 117번째) — FinOps Optimization & Rightsizing territory 정합
- Phase 13 close-out retro `850b4f8` (cj-style 116번째) — D-FINOPS-4 honestly DEFER 보존 해소
- Phase 13 atomic wire T1~T8 `8b98030` (cj-style 115번째) — FinOps Forecasting & Capacity Planning territory 정합
- Phase 13 spec entry `77ed55f` (cj-style 114번째)
- Phase 13 PRD entry `d31dfc8` (cj-style 113번째)
- Phase 12 close-out retro `3354e83` (cj-style 112번째)
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
- AD-14 stack pin — Recharts 2.12.7 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0
- AD-22 owner-only RBAC — optimization definition update + recommendation generation + idle resource detection + commitment recommendation + optimization recommended action apply + optimization accuracy tracking trigger
- AD-41 FinOps Optimization & Rightsizing 신규
- NFR18 ko-KR — SSOT only invariant
- NFR4 PII minimization — optimization data PII 미포함
- CR 0-2 RLS lesson, CR 1-1 audit-first INSERT, CR 4-3/4-4 lessons carry, CR 1-1 ContextVar, CR 1-1 RSC boundary, CR 9-6 commit message, CR 11-3 honest-DEFER, CR 11-4 D-001~D-005 + P-015, CR 12-1 L4 industry-agnostic capability, CR 12-5 D-14 envelope, CR 12-5 D-PARITY-01, CR 12-5 D-GATE-01, A19 cohesion 9 surface EXTENSION PASS, A36 SDR 검증 4-step 자동 적용
- m22_finops_optimization.optimization_serializers NEW Phase 14 EXTENSION 결정 wire (wire 시점에)

## 결정 wire 일자

2026-08-25 (KST)

## next (wire 진입 시)

옵션 (a) Phase 14 bmad-dev-story atomic wire T1~T8 진입 (cj-style 119번째 wire 진입 시점) 결정 wire 진입 / 옵션 (b) Phase 14 close-out retro 진입 (cj-style 120번째) / 옵션 (c) Phase 15+ 진입 / 옵션 (d) Epic 18+ 진입 / 옵션 (e) D-DEFER-* follow-up 진입 결정 wire 보류.
