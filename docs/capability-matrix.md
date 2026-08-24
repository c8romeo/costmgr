# Capability Matrix (v1.41)

> **v1.41 (2026-08-25, Phase 15 PRD entry)** — FinOps Tag Governance & Cost Allocation capability gate 1 NEW row: `FINOPS_TAG_GOVERNANCE` (`apps/api/modules/finops/tag_policy.py` NEW ~+150 LOC + `parse_tag_policy(definition_text)` parser + `validate_tag_policy_scope(tenant_id, scope)` validator + `TagPolicy` TypedDict 11 fields (policy_id + tenant_id + tag_key TEXT + tag_value_pattern TEXT + tag_value_required boolean + enforcement_level enum required/recommended/optional/blocked + scope enum tenant/department/cost_center/product_line/env/service + compliance_threshold_pct NUMERIC(5,2) + apply_to_existing_resources boolean + status enum active/paused/expired + created_at + updated_at) + 5 layer defense (syntax + semantic + tenant-scope RLS + tag_key validation + AWS Resource Explorer integration availability) + `TAG_POLICY_DEFAULTS = {'enforcement_level': 'recommended', 'scope': 'tenant', 'compliance_threshold_pct': 80.0, 'tag_value_required': True}` constants + audit-first INSERT `tag_policy_updated` CR 1-1 verbatim 결정 wire) + `apps/api/modules/finops/untagged_resource_detector.py` NEW ~+180 LOC + `detect_untagged_resources(tenant_id, tag_key, lookback_days) -> List[UntaggedResource]` + 6 resource types (EC2 + RDS + S3 + Lambda + EKS + VPC) + 4 untagged states (missing_tag + empty_tag + invalid_tag + policy_violation) + UntaggedResource TypedDict 12 fields (untagged_resource_id + tenant_id + resource_id TEXT + resource_type enum ec2/rds/s3/lambda/eks/vpc + tag_key TEXT + tag_value TEXT + untagged_state enum missing/empty/invalid/violation + detection_method enum resource_explorer/cost_explorer/cloudtrail + current_monthly_cost_krw NUMERIC(20,2) + detected_at + trace_id + remediation_action enum auto_tag/manual_review/skip) + Phase 14 wire `e904485` idle_resource_detector pattern verbatim EXTENSION + Phase 11 wire `e020ad0` showback period carry-over + audit-first INSERT `untagged_resource_detected` CR 1-1 verbatim + `allocation_rules_engine` `apps/api/modules/finops/allocation_rules_engine.py` NEW ~+180 LOC + `apply_allocation_rules(tenant_id, cost_item, tag_values) -> CostAllocation` + 5 rule types (tag_match + percentage_split + weighted + conditional + fallback) + 100% allocation guarantee (unallocated fallback to default_cost_center) + AllocationRule TypedDict 13 fields (rule_id + tenant_id + rule_type enum tag_match/percentage_split/weighted/conditional/fallback + tag_key + tag_value_match TEXT + allocation_pct NUMERIC(8,4) + priority int + scope enum department/cost_center/product_line + active boolean + created_at + updated_at + created_by + trace_id) + Phase 14 wire `e904485` rightsizing recommendation pattern verbatim EXTENSION + Phase 11 wire `e020ad0` chargeback engine EXTENSION + audit-first INSERT `allocation_rule_applied` CR 1-1 verbatim + `allocation_audit_compliance` `apps/api/modules/finops/allocation_audit_compliance.py` NEW ~+150 LOC + `audit_allocation_compliance(tenant_id, period_key) -> ComplianceReport` + 6 compliance metrics (coverage_rate + unallocated_pct + policy_violation_count + worst_department + audit_trail_count + rollback_count) + ComplianceReport TypedDict 10 fields (report_id + tenant_id + period_key + coverage_pct + unallocated_cost_krw NUMERIC(20,2) + policy_violation_count + worst_department TEXT + audit_trail_evaluated + rollback_triggered + evaluated_at) + 4 industries baseline + per-tenant override EXTENSION + audit-first INSERT `allocation_compliance_evaluated` + `allocation_policy_violation` 2 NEW actions + `chargeback_allocation_reconciliation` `apps/api/modules/finops/chargeback_allocation_reconciliation.py` NEW ~+120 LOC + `reconcile_chargeback_allocation(tenant_id, period_key) -> ReconciliationResult` + 5-step reconciliation pipeline (extract_untagged + transform_tag_values + map_to_cost_center + validate_allocation_sum + post_chargeback) + ReconciliationResult TypedDict 11 fields (reconciliation_id + tenant_id + period_key + total_chargeback_krw NUMERIC(20,2) + allocated_amount_krw NUMERIC(20,2) + unallocated_amount_krw NUMERIC(20,2) + coverage_pct NUMERIC(5,2) + reconciliation_status enum matched/partial/mismatch/manual_review + mismatch_count + reconciled_at + trace_id) + Phase 11 wire `e020ad0` chargeback_engine EXTENSION 정합 + Phase 14 wire `e904485` optimization_accuracy_tracker EXTENSION 패턴 verbatim + audit-first INSERT `chargeback_allocation_reconciled` CR 1-1 verbatim + 14 NEW typed exceptions (`TagPolicyInvalidError(400)` + `TagPolicyScopeInvalidError(404)` + `TagPolicyPatternError(400)` + `UntaggedDetectionError(500)` + `UntaggedResourceExplorerUnavailableError(503)` + `AllocationRuleInvalidError(400)` + `AllocationSumMismatchError(422)` + `AllocationRulePriorityError(409)` + `AllocationAuditError(500)` + `ComplianceCoverageBelowThresholdError(422)` + `ComplianceReportUnavailableError(404)` + `ReconciliationMismatchError(422)` + `ReconciliationSequenceError(500)` + `FinopsTagGovernanceCapabilityDeniedError(403)`) CR 12-5 D-14 envelope + `apps/web/app/[locale]/(dashboard)/admin/finops/tags/page.tsx` NEW ~+150 LOC + 4 components (`TagPolicyEditor` + `UntaggedResourcePanel` + `AllocationRuleBuilder` + `ComplianceDashboard`) + owner-only RBAC AD-22 + Epic 12 2FA 챌린지 + ko-KR.json `finops_tag_governance.*` namespace EXTENSION ~30 keys CR 11-4 D-002 verbatim SSOT + dry-run mode UI 결정 wire). industry-agnostic 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4 precedent like `FINOPS_OPTIMIZATION` Phase 14 PRD entry baseline `850b4f8` (cj-style 117번째) + `FINOPS_FORECASTING_CAPACITY_PLANNING` Phase 13 wire `8b98030` + `FINOPS_ANOMALY_DETECTION` + `FINOPS_BUDGET_ALERT` Phase 12 wire `f3c0e63` + `FINOPS_SHOWBACK` + `FINOPS_CHARGEBACK` Phase 11 wire `e020ad0` + `SLO_ENGINEERING` Phase 10 wire `ac5d6c5` + `CHAOS_ENGINEERING` Phase 9 wire + `PERFORMANCE_TESTING` Phase 8 wire + `OBSERVABILITY_TRACES` + `OBSERVABILITY_METRICS` Phase 7 wire + `AUDIT_LOG_RETENTION` Phase 6 wire + `AUDIT_LOG_VIEW` Epic 17 wire + `MULTI_REGION_BACKUP` + `MULTI_REGION_FAILOVER` Phase 5 wire + `TENANT_IDP_MANAGEMENT` Epic 16 wire + `SSO_ENTERPRISE` Epic 15 wire + `LISTEN_NOTIFY_*` Epic 13/14 wire + `AUTH_MIDDLEWARE` Phase 3 wire + `LAUNCH_*` 1st release wire + `DEPLOYMENT_*` Phase 4 wire pattern verbatim bind). AD-42 FinOps Tag Governance & Cost Allocation 신규 (Phase 14 close-out retro `5b367d9` (cj-style 120번째 wire entry) + Phase 14 atomic wire T1~T8 `e904485` (cj-style 119번째) + Phase 14 spec entry `30637f6` (cj-style 118번째) + Phase 14 PRD entry `0e3f8d9` (cj-style 117번째) 결정 wire 모두 DONE 진입 정합 보존 후 옵션 5종 중 옵션 (a) Phase 15+ 진입 + 옵션 (a) FinOps Tag Governance & Cost Allocation (Recommended) 결정 wire 진입 — tag policy DSL 4 enforcement_level (required/recommended/optional/blocked) + untagged resource detector 6 resource types (EC2/RDS/S3/Lambda/EKS/VPC) + allocation rules engine 5 rule types (tag_match/percentage_split/weighted/conditional/fallback) + allocation audit + compliance + chargeback allocation reconciliation 5-step pipeline + 100% allocation guarantee + tag governance dashboard UI + audit-first INSERT 6 NEW + Capability FINOPS_TAG_GOVERNANCE 1 NEW + dry-run mode + tests + wire scope T1~T8 territory 결정, Phase 14 wire `e904485` 의 FinOps Optimization & Rightsizing territory (idle resource detector pattern + rightsizing recommendation structure) + Phase 13 wire `8b98030` 의 forecast accuracy tracker + Phase 12 wire `f3c0e63` 의 anomaly detection baseline + Phase 11 wire `e020ad0` 의 chargeback engine + 12-period showback baseline 의 자연스러운 carry-over chain (untagged resource detection → allocation rules → compliance audit → chargeback reconciliation chain 정직 회복) 결정). Phase 15 wire scope 결정 보존 T1~T8 (T1 tag_policy + tag_policy_dsl module + T2 untagged_resource_detector + 6 resource types + T3 allocation_rules_engine + 5 rule types + T4 allocation_audit_compliance + reconciliation + Phase 11/14 carry-over + T5 alembic 0047 phase_15_tag_governance + T6 audit action EXTENSION 6 NEW + T7 capability v1.41 EXTENSION 1 NEW row + frontend finops tag governance dashboard + T8 3중 게이트 FINAL CLEAN atomic commit 결정 wire 보류, cj-style Phase 15 3번째 진입점 진입 시점). wire_commit = TBD (cj-style Phase 15 3번째 진입점 진입 시점, expected cj-style 123번째 epic 연속 정직 회복). Phase 14 close-out retro `5b367d9` + Phase 14 wire `e904485` + Phase 14 spec entry `30637f6` + Phase 14 PRD entry `0e3f8d9` + Phase 13 close-out retro `850b4f8` + Phase 13 wire `8b98030` + Phase 12 close-out retro `3354e83` + Phase 12 wire `f3c0e63` + Phase 11 close-out retro `80df15b` + Phase 11 wire `e020ad0` + Phase 10 close-out retro `733d428` + Phase 10 wire `ac5d6c5` + Phase 9 close-out retro `634427d` + Phase 9 wire `e7670e1` + Phase 8 close-out retro `ab495a8` + Phase 8 wire `60d4ea1` + Phase 7 close-out retro `326fa9f` + Phase 7 wire `59b56cd` + Phase 6 close-out retro `f9f006c` + Phase 6 wire `24e1cd7` + Epic 17 close-out retro `be8f3bd` + Epic 17 wire `2ada2ec` + Epic 16 close-out retro + Epic 16 wire `e117e09` + 1st release cycle 정합 보존 후 옵션 5종 "FinOps Tag Governance & Cost Allocation 결정 wire 보류, Phase 15+ 진입 시점" verbatim 해소 결정 wire. D-FINOPS-5 신규 honestly DEFER 보존 → Phase 15 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire 진입 + CR 11-3 honest-DEFER discipline 121번째 epic 연속 정직 회복 검증 보존.

> **v1.40 (2026-08-25, Phase 14 PRD entry)** — FinOps Optimization & Rightsizing capability gate 1 NEW row: `FINOPS_OPTIMIZATION` (`apps/api/modules/finops/optimization_definition.py` NEW ~+150 LOC + `parse_optimization_definition(definition_text)` parser + `validate_optimization_scope(tenant_id, target_resource)` validator + `OptimizationDefinition` TypedDict 12 fields (optimization_id + tenant_id + target_resource_type enum compute_instance/storage_volume/database/load_balancer/cdn/reserved_capacity/serverless + target_metric enum cost/utilization/idle_time/waste_pct + dimension_value + strategy enum rightsize/idle_detect/ri_sp_commit/auto_scale/instance_type_change + confidence_level enum low/medium/high + estimated_savings_threshold_pct + lookback_days + status enum active/paused/expired + created_at + updated_at) + 5 layer defense (syntax + semantic + tenant-scope RLS + target_metric validation + history data availability) + `OPTIMIZATION_DEFAULTS = {'lookback_days': 30, 'confidence_level': 'high', 'estimated_savings_threshold_pct': 5.0, 'strategy': 'rightsize'}` constants + audit-first INSERT `optimization_definition_updated` CR 1-1 verbatim 결정 wire) + `apps/api/modules/finops/rightsizing_engine.py` NEW ~+200 LOC + `recommend_rightsizing(tenant_id, resource_type, lookback_days) -> List[RightsizingRecommendation]` + 4 utilization analysis methods parallel run (P95 CPU utilization + P95 memory utilization + average IOPS + average network throughput) + recommendation 4종 (downsize 1 tier + downsize 2 tiers + upgrade tier + no-change verdict) + recommendation confidence_level enum low/medium/high (computed via utilization stability score) + estimated_monthly_savings_pct 계산 (target_metric=utilization 일 때) + safety guard `MINIMUM_UTILIZATION_PCT = 20.0` (downsize 시 minimum 20% utilization 유지) + estimated_savings_threshold_pct < 5.0% 인 경우 skip recommendation 결정 wire (CR 12-5 D-14 envelope 정합) + RightsizingRecommendation TypedDict 14 fields (recommendation_id + tenant_id + resource_id + resource_type + current_instance_type + recommended_instance_type + current_monthly_cost_krw + estimated_monthly_cost_krw + estimated_monthly_savings_pct + utilization_p95 + utilization_stability_score + confidence_level + recommendation_status enum pending/approved/rejected/applied + generated_at) + Phase 12 wire `f3c0e63` anomaly detection + Phase 13 wire `8b98030` forecast accuracy tracker EXTENSION 결정 wire + audit-first INSERT `recommendation_generated` CR 1-1 verbatim + `optimization_recommended_action` 1 NEW action 결정 wire + `apps/api/modules/finops/idle_resource_detector.py` NEW ~+180 LOC + `detect_idle_resources(tenant_id, lookback_days) -> List[IdleResourceResult]` + idle 정의 (P95 CPU utilization < 5% AND memory utilization < 5% for >= 30 consecutive days) + 4 detection filters (CPU threshold + memory threshold + network throughput threshold + storage IOPS threshold) + IdleResourceResult TypedDict 12 fields (resource_id + tenant_id + resource_type + idle_since_date + idle_duration_days + current_monthly_cost_krw + potential_monthly_savings_pct + idle_reasons List + detection_method + recommended_action enum terminate/snapshot_then_terminate/keep_with_alert/resize_down + trace_id + detected_at) + Phase 12 wire `f3c0e63` anomaly detection baseline EXTENSION 정합 (CPU utilization distribution baseline) + audit-first INSERT `idle_resource_detected` CR 1-1 verbatim + `apps/api/modules/finops/commitment_recommender.py` NEW ~+180 LOC + `recommend_commitments(tenant_id, lookback_days) -> List[CommitmentRecommendation]` + RI/SP 3종 (EC2 Instance Savings Plans + RDS Reserved Instances + ElastiCache Reserved Nodes) + 3 analysis horizon (1-year commit + 3-year commit + mix-commit 1y+3y portfolio) + payback_period_months 계산 + break-even utilization_pct 계산 (default 70%) + estimated_annual_savings_pct 계산 + recommendation guard `MINIMUM_SAVINGS_PCT = 10.0` (10% 미만 skip) + CommitmentRecommendation TypedDict 14 fields (recommendation_id + tenant_id + service enum ec2/rds/elasticache + commitment_term enum 1_year/3_year + commitment_type enum no_upfront/partial_upfront/all_upfront + current_on_demand_cost_krw + estimated_commitment_cost_krw + estimated_annual_savings_pct + payback_period_months + break_even_utilization_pct + coverage_pct + risk_score enum low/medium/high + recommended_action + generated_at) + Phase 11 wire `e020ad0` chargeback allocation pattern EXTENSION + audit-first INSERT `commitment_recommended` CR 1-1 verbatim + `apps/api/modules/finops/optimization_accuracy_tracker.py` NEW ~+120 LOC + Phase 13 wire `8b98030` forecast_accuracy_tracker EXTENSION pattern + per-recommendation accuracy tracking (per tenant_id + recommendation_id + applied_at granularity) + 3 metrics (applied_savings_krw vs estimated_savings_krw accuracy + utilization_improvement_pct + optimization_completion_rate_pct) + optimization recommendation degradation detection (accuracy < 60% for 5 consecutive recommendations) → model retraining trigger + retraining cron KST 매주 화요일 03:30 UTC 18:30 (Phase 13 forecast accuracy tracker KST 일요일 03:00 EXTENSION 정합) + audit-first INSERT `optimization_accuracy_degraded` + `optimization_retraining_triggered` 2 NEW action 결정 wire + ActionClass.FINOPS_OPTIMIZATION 신규 정의 + `apps/api/core/audit_action.py` MODIFIED AuditAction Literal EXTENSION 8 NEW values (`optimization_definition_updated` + `recommendation_generated` + `idle_resource_detected` + `commitment_recommended` + `optimization_recommended_action` + `optimization_dry_run_executed` + `optimization_accuracy_degraded` + `optimization_retraining_triggered`) + `_ActionRegistry` FINOPS_OPTIMIZATION entry 신규 8개 등록 + `__all__` EXTENSION 결정 wire + `apps/api/alembic/versions/0046_phase_14_optimization.py` NEW + 4 NEW tables (`phase_14_finops_optimization_definition` 12 columns + `phase_14_finops_rightsizing_recommendation` 14 columns + `phase_14_finops_idle_resource` 12 columns + `phase_14_finops_commitment_recommendation` 14 columns + `phase_14_finops_optimization_accuracy` 10 columns = 5 tables) + RLS policy `tenant_id = current_setting('app.tenant_id')::uuid` CR 0-2 verbatim + down_revision "0045_phase_13_forecasting" + dry-run mode `--finops-optimization-dry-run` + `--finops-rightsizing-dry-run` + `--finops-idle-detector-dry-run` + `--finops-commitment-dry-run` 4 CLI flags 결정 wire + 14 NEW typed exceptions (`OptimizationDefinitionInvalidError(400)` + `OptimizationScopeInvalidError(404)` + `OptimizationHistoryUnavailableError(404)` + `RightsizingEngineError(500)` + `RecommendationGenerationError(500)` + `RecommendationConfidenceError(500)` + `IdleResourceDetectionError(500)` + `IdleThresholdBreachError(500)` + `IdleMetricUnavailableError(404)` + `CommitmentRecommendationError(500)` + `CommitmentPaybackPeriodError(500)` + `OptimizationAccuracyTrackingError(500)` + `OptimizationRetrainingTriggerError(500)` + `OptimizationAccuracyDegradationError(500)`) CR 12-5 D-14 envelope + `apps/web/app/[locale]/(dashboard)/admin/finops/optimization/page.tsx` NEW ~+150 LOC + 5 components (`OptimizationStrategySelector` 5 strategy enum + `RightsizingRecommendationList` + `IdleResourceDetectionPanel` + `CommitmentRecommendationChart` Recharts 2.12.7 AD-14 stack pin + `OptimizationAccuracyPanel`) + `apps/web/lib/finops-optimization/finops-optimization-client.ts` NEW + ko-KR.json `finops_optimization.*` namespace EXTENSION ~30 keys (CR 11-4 D-002 verbatim SSOT) + dry-run mode UI 결정 wire). industry-agnostic 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4 precedent like `FINOPS_FORECASTING_CAPACITY_PLANNING` + `FINOPS_ANOMALY_DETECTION` + `FINOPS_BUDGET_ALERT` Phase 12 wire `f3c0e63` + `FINOPS_SHOWBACK` + `FINOPS_CHARGEBACK` Phase 11 wire `e020ad0` + `SLO_ENGINEERING` Phase 10 wire `ac5d6c5` + `CHAOS_ENGINEERING` Phase 9 wire `e7670e1` + `PERFORMANCE_TESTING` Phase 8 wire `60d4ea1` + `OBSERVABILITY_TRACES` + `OBSERVABILITY_METRICS` Phase 7 wire `59b56cd` + `AUDIT_LOG_RETENTION` Phase 6 wire `24e1cd7` + `AUDIT_LOG_VIEW` Epic 17 wire + `MULTI_REGION_BACKUP` + `MULTI_REGION_FAILOVER` Phase 5 wire + `TENANT_IDP_MANAGEMENT` Epic 16 wire + `SSO_ENTERPRISE` Epic 15 wire + `LISTEN_NOTIFY_*` Epic 13/14 wire + `AUTH_MIDDLEWARE` Phase 3 wire + `LAUNCH_*` 1st release wire + `DEPLOYMENT_*` Phase 4 wire pattern verbatim bind). AD-41 FinOps Optimization & Rightsizing 신규 (Phase 13 close-out retro `850b4f8` (cj-style 116번째 wire entry) + Phase 13 atomic wire T1~T8 `8b98030` (cj-style 115번째) + Phase 13 spec entry `77ed55f` (cj-style 114번째) + Phase 13 PRD entry `d31dfc8` (cj-style 113번째) 결정 wire 모두 DONE 진입 정합 보존 후 옵션 5종 중 옵션 (a) Phase 14+ 진입 + 옵션 (a) FinOps Optimization & Rightsizing (Recommended) 결정 wire 진입 — optimization definition DSL + rightsizing engine 4 utilization analysis methods + idle resource detection 4 idle 정의 + RI/SP commitment recommendations 3 service + recommendation accuracy tracking + retraining trigger + optimization dashboard UI + audit-first INSERT 8 NEW + Capability FINOPS_OPTIMIZATION 1 NEW + dry-run mode + tests + wire scope T1~T8 territory 결정, Phase 13 wire `8b98030` 의 forecast accuracy tracker MAE/MAPE/RMSE + Phase 12 wire `f3c0e63` 의 anomaly detection baseline last 30d/90d/YTD + Phase 11 wire `e020ad0` showback period selector + Phase 8 wire `60d4ea1` cost-engine 12-period benchmark 의 자연스러운 carry-over chain (historical baseline ⇒ forecast ⇒ cost optimization recommendation EXTENSION accuracy tracking chain) 결정). Phase 14 wire scope 결정 보존 T1~T8 (T1 optimization_definition + optimization_dsl module + T2 rightsizing_engine + 4 utilization methods + T3 idle_resource_detector + 4 idle 정의 + T4 commitment_recommender + 3 service RI/SP + optimization_accuracy_tracker module + T5 alembic 0046 phase_14_optimization + T6 audit action EXTENSION 8 NEW + T7 capability v1.40 EXTENSION 1 NEW row + frontend finops optimization dashboard + T8 3중 게이트 FINAL CLEAN atomic commit 결정 wire 보류, cj-style Phase 14 3번째 진입점 진입 시점). wire_commit = TBD (cj-style Phase 14 3번째 진입점 진입 시점, expected cj-style 119번째 epic 연속 정직 회복). Phase 13 close-out retro `850b4f8` + Phase 12 close-out retro `3354e83` + Phase 11 close-out retro `80df15b` + Phase 10 close-out retro `733d428` + Phase 9 close-out retro `634427d` + Phase 8 close-out retro `ab495a8` + Phase 7 close-out retro `326fa9f` + Phase 6 close-out retro `f9f006c` + Epic 17 close-out retro `be8f3bd` "FinOps Optimization & Rightsizing 결정 wire 보류, Phase 14+ 진입 시점" verbatim 해소 결정 wire. D-FINOPS-4 신규 honestly DEFER 보존 → Phase 14 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire 진입 + CR 11-3 honest-DEFER discipline 117번째 epic 연속 정직 회복 검증 보존.

> **v1.39 (2026-08-24, Phase 13 wire DONE)** — FinOps Forecasting & Capacity Planning capability wire DONE (cj-style 115번째 epic 연속 정직 회복 atomic docs-and-source wire). baseline_commit `77ed55f` (Phase 13 spec entry tip). 1 NEW row `FINOPS_FORECASTING_CAPACITY_PLANNING` + 2 BACKFILL Phase 12 rows (`FINOPS_ANOMALY_DETECTION` + `FINOPS_BUDGET_ALERT`) wire DONE (Phase 12 wire `f3c0e63` left these rows missing from the table — honest recovery per cj-style 115번째 atomic commit, no new D-DEFER). territory wire scope T1~T8 (T1 forecast_definition + forecast_dsl module NEW ~+150 LOC + T2 forecast_engine + forecast_model_registry NEW ~+280 LOC + 4 time series models parallel run ARIMA + Prophet + LSTM + ensemble voting consensus + T3 capacity_headroom NEW ~+180 LOC + 3 resource types compute/storage/network + 90일 lookahead + budget_burnrate NEW ~+150 LOC + 4-input burn-rate formula + 3-level severity routing + 24h dedup window + T4 forecast_accuracy_tracker NEW ~+120 LOC + MAE/MAPE/RMSE banker's rounding CR 5-1 + INDUSTRY_BASELINE_MAPE_4_INDUSTRIES + MAPE > 20% for 3 consecutive periods → retraining trigger + T5 alembic 0045 phase_13_forecasting NEW + 5 NEW tables (phase_13_finops_forecast_definition 12 columns + phase_13_finops_forecast_result 14 columns + phase_13_finops_capacity_headroom 16 columns + phase_13_finops_budget_burnrate 14 columns + phase_13_finops_forecast_preview 10 columns) + RLS policy tenant_id = current_setting('app.tenant_id')::uuid CR 0-2 verbatim + down_revision "0044_phase_12_finops_anomaly" + T6 14 NEW typed exceptions FinopsForecastError base + ForecastDefinitionInvalidError(400) + ForecastScopeInvalidError(400) + ForecastAccuracyInvalidError(400) + ForecastHistoryUnavailableError(422) + ForecastEngineError(500) + ForecastModelTrainingError(500) + ForecastSeasonalityDetectionError(500) + CapacityHeadroomAnalysisError(500) + CapacityThresholdBreachError(500) + CapacityMetricUnavailableError(404) + BudgetBurnRateProjectionError(500) + BudgetOverrunPredictionError(500) + ForecastAccuracyTrackingError(500) + ModelRetrainingTriggerError(500) + ModelPerformanceDegradationError(500) CR 12-5 D-14 envelope + ActionClass.FINOPS_FORECAST 신규 정의 + AuditAction Literal EXTENSION 7 NEW values (forecast_definition_updated + forecast_generated + capacity_headroom_analyzed + budget_burn_rate_projected + forecast_accuracy_degraded + model_retraining_triggered + forecast_dry_run_executed) CR 1-1 verbatim + apps/api/dependencies/capability.py EXTENSION 3 NEW deps (require_finops_anomaly_detection + require_finops_budget_alert BACKFILL Phase 12 + require_finops_forecast NEW Phase 13) + apps/api/modules/finops/serializers.py NEW BACKFILL Phase 11 stub + apps/api/modules/finops/__init__.py EXTENSION 6 NEW re-exports (forecast_definition + forecast_engine + forecast_model_registry + capacity_headroom + budget_burnrate + forecast_accuracy_tracker) + T7 capability v1.39 EXTENSION 1 NEW row + 2 BACKFILL Phase 12 rows wire DONE 진입 정합 + apps/web/app/[locale]/(dashboard)/admin/finops/forecast/page.tsx NEW RSC + layout.tsx NEW + components/finops/FinopsForecastDashboardPanel.tsx NEW Client (5 sub-components: ForecastHorizonSelector + ForecastChart Recharts 2.12.7 AD-14 stack pin + CapacityHeadroomGauge + BudgetBurnRatePanel + ForecastAccuracyPanel) + apps/web/lib/finops-forecast/finops-forecast-client.ts NEW + ko-KR.json finops_forecast.* namespace EXTENSION ~30 keys CR 11-4 D-002 verbatim SSOT + T8 3중 게이트 FINAL CLEAN atomic commit territory 결정 wire). industry-agnostic 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4 precedent like FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire f3c0e63 + FINOPS_SHOWBACK + FINOPS_CHARGEBACK Phase 11 wire e020ad0 + SLO_ENGINEERING Phase 10 wire ac5d6c5 + CHAOS_ENGINEERING Phase 9 wire e7670e1 + PERFORMANCE_TESTING Phase 8 wire 60d4ea1 + OBSERVABILITY_TRACES + OBSERVABILITY_METRICS Phase 7 wire 59b56cd + AUDIT_LOG_RETENTION Phase 6 wire 24e1cd7 + AUDIT_LOG_VIEW Epic 17 wire + MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY_* Epic 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern verbatim bind). 3중 게이트 impact CLEAN (ruff scoped Phase 13 wire Python files = 0 NEW errors + pytest ~51 NEW cases PASS + vitest ~5 NEW cases PASS + pnpm tsc --noEmit 0 NEW errors + 0 regressions). CR lessons applied 14종 (CR 0-2 RLS 5 tables + CR 1-1 audit-first INSERT 7 NEW + CR 1-1 ContextVar trace_id + CR 1-1 RSC boundary forecast/page.tsx + CR 4-3/4-4 forecast baseline + golden_diff pattern verbatim + CR 5-1 banker's rounding parity MAE/MAPE/RMSE + CR 9-6 commit message + CR 11-3 honest-DEFER + CR 11-4 P-015 pure validator pattern + CR 12-1 L4 industry-agnostic + CR 12-5 D-14 typed exception envelope 14 NEW + CR 12-5 D-PARITY-01 inversion + CR 12-5 D-GATE-01 inversion + A19 cohesion 10 surface + A36 SDR + AD-14 stack pin statsmodels==0.14.1 + prophet==1.1.5 + tensorflow==2.15.0 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 + Recharts 2.12.7 + AD-22 owner-only RBAC + Epic 12 2FA 챌린지 + NFR4 PII minimization). **Phase 12 wire f3c0e63 carry-over 3 gaps BACKFILL honestly 보존 진입 wire 결정** (cj-style 115번째 wire DONE 진입 시점에 honestly preserved 결정 wire 완료 보존): (1) apps/api/dependencies/capability.py missing Phase 12 require_finops_anomaly_detection + require_finops_budget_alert — BACKFILL 결정 wire, (2) apps/api/modules/finops/serializers.py Phase 11 stub — NEW 결정 wire BACKFILL, (3) docs/capability-matrix.md table missing FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT rows — BACKFILL (this v1.39 entry + 3 NEW rows) 결정 wire. wire_commit = TBD (cj-style Phase 13 3번째 진입점 진입 시점, cj-style 115번째 epic 연속 정직 회복). Phase 12 close-out retro 3354e83 + Phase 11 close-out retro 80df15b + Phase 10 close-out retro 733d428 + Phase 9 close-out retro 634427d + Phase 8 close-out retro ab495a8 "FinOps Forecasting & Capacity Planning 결정 wire 보류, Phase 13+ 진입 시점" verbatim 해소 결정 wire. D-FINOPS-3 honestly DEFER 보존 진입 wire 결정 + CR 11-3 honest-DEFER discipline 115번째 epic 연속 정직 회복 검증 보존.

> **v1.38 (2026-08-24, Phase 13 PRD entry)** — FinOps Forecasting & Capacity Planning capability gate 1 NEW row: `FINOPS_FORECASTING_CAPACITY_PLANNING` (`apps/api/modules/finops/forecast_definition.py` NEW ~+150 LOC + `parse_forecast_definition(definition_text)` parser + `validate_forecast_scope(tenant_id, target_metric)` validator + `ForecastDefinition` TypedDict 10 fields (forecast_id + tenant_id + target_metric enum department/cost_center/product_line/service/tenant_total + dimension_value + horizon_months enum 3m/6m/12m/24m + model_type enum arima/prophet/lstm/ensemble + confidence_level enum 80/90/95/99 + retraining_cron + status enum active/paused/expired + created_at + updated_at) + 5 layer defense (syntax + semantic + tenant-scope RLS + target_metric validation + history data availability) + `FORECAST_DEFAULTS = {'horizon_months': 12, 'model_type': 'ensemble', 'confidence_level': 95, 'retraining_cron': '0 3 * * 0'}` constants + audit-first INSERT `forecast_definition_updated` CR 1-1 verbatim) + `apps/api/modules/finops/forecast_engine.py` NEW ~+200 LOC + `generate_forecast(tenant_id, target_metric, horizon_months) -> ForecastResult` + 4 time series models parallel run (ARIMA p=2,d=1,q=2 + Prophet seasonality_mode='multiplicative' + LSTM hidden_layers=50 + ensemble voting consensus) + statsmodels==0.14.1 + prophet==1.1.5 + tensorflow==2.15.0 AD-14 stack pin 결정 wire + ForecastResult TypedDict 10 fields (forecast_id + tenant_id + target_metric + horizon_months + predicted_values List + confidence_lower List + confidence_upper List + model_type + model_version + generated_at) + last 12-month historical baseline data source = phase_11_finops_showback table (Phase 11 wire 정합) + phase_12_finops_anomaly_detection table (Phase 12 wire 정합) + seasonality detection (weekly + monthly + quarterly + yearly) + trend decomposition (STL) + holiday calendar KST 8 holidays (신정 + 설날 + 삼일절 + 어린이날 + 현충일 + 광복절 + 개천절 + 圣诞节) + model_registry `apps/api/modules/finops/forecast_model_registry.py` NEW + audit-first INSERT `forecast_generated` CR 1-1 verbatim 결정 wire + `apps/api/modules/finops/capacity_headroom.py` NEW ~+180 LOC + `analyze_capacity_headroom(tenant_id, resource_type) -> CapacityHeadroomReport` + 3 resource type (compute CPU + memory utilization 90일 lookahead LSTM primary + storage DB size + backup storage 90일 lookahead Prophet primary + network egress + ingress bandwidth 90일 lookahead ARIMA primary) + headroom_pct = (1 - saturation_pct) × 100 + critical threshold headroom < 20% → Slack + PagerDuty + warning threshold headroom < 40% → Slack + CapacityHeadroomReport TypedDict 14 fields + Phase 8 wire `60d4ea1` k6 부하 테스트 EXTENSION + Phase 7 wire `59b56cd` Prometheus EXTENSION + Phase 5 wire `f093f8c` cross-region replica EXTENSION 정합 + audit-first INSERT `capacity_headroom_analyzed` CR 1-1 verbatim 결정 wire + `apps/api/modules/finops/budget_burnrate.py` NEW ~+150 LOC + `project_budget_consumption(tenant_id, period_key) -> BurnRateProjection` + Phase 12 wire `f3c0e63` budget_alert linear extrapolation EXTENSION + ARIMA-based projection + 7/30-day rolling projection + BurnRateProjection TypedDict 12 fields + predicted_overrun_pct > 110% warning alert + predicted_overrun_pct > 130% critical alert + audit-first INSERT `budget_burn_rate_projected` CR 1-1 verbatim 결정 wire + `apps/api/modules/finops/forecast_accuracy_tracker.py` NEW ~+120 LOC + Phase 12 wire `f3c0e63` forecast_accuracy.py EXTENSION + per-model accuracy tracking (per tenant_id + target_metric + model_type granularity) + MAE + MAPE + RMSE 3 metrics + ensemble vs individual model comparison + model performance degradation detection (MAPE > 20% for 3 consecutive periods) → model retraining trigger + retraining cron KST 매주 일요일 03:00 UTC 18:00 (Phase 12 anomaly detection isolation forest retraining cron EXTENSION 정합) + audit-first INSERT `forecast_accuracy_degraded` CR 1-1 verbatim + `model_retraining_triggered` 1 NEW action 결정 wire + ActionClass.FINOPS_FORECAST 신규 정의 + `apps/api/core/audit_action.py` MODIFIED AuditAction Literal EXTENSION 7 NEW values (`forecast_definition_updated` + `forecast_generated` + `capacity_headroom_analyzed` + `budget_burn_rate_projected` + `forecast_accuracy_degraded` + `model_retraining_triggered` + `forecast_dry_run_executed`) + `_ActionRegistry` FINOPS_FORECAST entry 신규 1개 등록 + `__all__` EXTENSION 결정 wire + `apps/api/alembic/versions/0045_phase_13_forecasting.py` NEW + 5 NEW tables (`phase_13_finops_forecast_definition` 12 columns + `phase_13_finops_forecast_result` 14 columns + `phase_13_finops_capacity_headroom` 16 columns + `phase_13_finops_budget_burnrate` 14 columns + `phase_13_finops_forecast_preview` 7 columns) + RLS policy `tenant_id = current_setting('app.tenant_id')::uuid` CR 0-2 verbatim + down_revision "0044_phase_12_finops_anomaly" + dry-run mode `--finops-forecast-dry-run` + `--finops-capacity-dry-run` + `--finops-burnrate-dry-run` 3 CLI flags 결정 wire + 14 NEW typed exceptions (`ForecastDefinitionInvalidError(400)` + `ForecastScopeInvalidError(404)` + `ForecastHistoryUnavailableError(404)` + `ForecastEngineError(500)` + `ForecastModelTrainingError(500)` + `ForecastSeasonalityDetectionError(500)` + `CapacityHeadroomAnalysisError(500)` + `CapacityThresholdBreachError(500)` + `CapacityMetricUnavailableError(404)` + `BudgetBurnRateProjectionError(500)` + `BudgetOverrunPredictionError(500)` + `ForecastAccuracyTrackingError(500)` + `ModelRetrainingTriggerError(500)` + `ModelPerformanceDegradationError(500)`) CR 12-5 D-14 envelope + `apps/web/app/[locale]/(dashboard)/admin/finops/forecast/page.tsx` NEW ~+150 LOC + 4 components (`ForecastHorizonSelector` + `ForecastChart` Recharts 2.12.7 AD-14 stack pin + `CapacityHeadroomGauge` + `BudgetBurnRatePanel`) + `apps/web/lib/finops-forecast/finops-forecast-client.ts` NEW + ko-KR.json `finops_forecast.*` namespace EXTENSION ~30 keys (CR 11-4 D-002 verbatim SSOT) + dry-run mode UI 결정 wire). industry-agnostic 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4 precedent like `FINOPS_ANOMALY_DETECTION` + `FINOPS_BUDGET_ALERT` Phase 12 wire `f3c0e63` + `FINOPS_SHOWBACK` + `FINOPS_CHARGEBACK` Phase 11 wire `e020ad0` + `SLO_ENGINEERING` Phase 10 wire `ac5d6c5` + `CHAOS_ENGINEERING` Phase 9 wire `e7670e1` + `PERFORMANCE_TESTING` Phase 8 wire `60d4ea1` + `OBSERVABILITY_TRACES` + `OBSERVABILITY_METRICS` Phase 7 wire `59b56cd` + `AUDIT_LOG_RETENTION` Phase 6 wire `24e1cd7` + `AUDIT_LOG_VIEW` Epic 17 wire + `MULTI_REGION_BACKUP` + `MULTI_REGION_FAILOVER` Phase 5 wire + `TENANT_IDP_MANAGEMENT` Epic 16 wire + `SSO_ENTERPRISE` Epic 15 wire + `LISTEN_NOTIFY_*` Epic 13/14 wire + `AUTH_MIDDLEWARE` Phase 3 wire + `LAUNCH_*` 1st release wire + `DEPLOYMENT_*` Phase 4 wire pattern verbatim bind). AD-40 FinOps Forecasting & Capacity Planning 신규 (Phase 12 close-out retro `3354e83` (cj-style 112번째 wire entry) + Phase 12 atomic wire T1~T8 `f3c0e63` (cj-style 111번째) + Phase 12 spec entry `8c5f374` (cj-style 110번째) + Phase 12 PRD entry `344c7eb` (cj-style 109번째) 결정 wire 모두 DONE 진입 정합 보존 후 옵션 5종 중 옵션 (a) Phase 13+ 진입 + 옵션 (a) FinOps Forecasting & Capacity Planning (Recommended) 결정 wire 진입 — forecast definition DSL + cost forecasting engine 4 time series models ARIMA + Prophet + LSTM + ensemble + capacity headroom analysis compute + storage + network + budget burn-rate projection + forecast accuracy tracking + model retraining trigger + forecasting dashboard UI + audit-first INSERT 7 NEW + Capability FINOPS_FORECASTING_CAPACITY_PLANNING 1 NEW + dry-run mode + tests + wire scope T1~T8 territory 결정, Phase 12 wire `f3c0e63` 의 anomaly detection baseline last 30d/90d/YTD + forecast accuracy tracking MAE/MAPE/RMSE + Phase 11 wire `e020ad0` showback period selector + Phase 8 wire `60d4ea1` cost-engine 12-period benchmark 의 자연스러운 carry-over chain (historical baseline ⇒ forward forecast EXTENSION 12-month prediction with 95% CI + capacity headroom 90일 lookahead + budget burn-rate EXTENSION 정직 회복 chain) 결정). Phase 13 wire scope 결정 보존 T1~T8 (T1 forecast_definition + forecast_dsl module + T2 forecast_engine + 4 time series models + T3 capacity_headroom + compute/storage/network + T4 budget_burnrate + Phase 12 budget_alert carry-over + forecast_accuracy_tracker module + T5 alembic 0045 phase_13_forecasting + T6 audit action EXTENSION 7 NEW + T7 capability v1.38 EXTENSION 1 NEW row + frontend finops forecast dashboard + T8 3중 게이트 FINAL CLEAN atomic commit 결정 wire 보류, cj-style Phase 13 3번째 진입점 진입 시점). wire_commit = TBD (cj-style Phase 13 3번째 진입점 진입 시점, expected cj-style 115번째 epic 연속 정직 회복). Phase 12 close-out retro `3354e83` + Phase 11 close-out retro `80df15b` + Phase 10 close-out retro `733d428` + Phase 9 close-out retro `634427d` + Phase 8 close-out retro `ab495a8` + Phase 7 close-out retro `326fa9f` + Phase 6 close-out retro `f9f006c` + Epic 17 close-out retro `be8f3bd` "FinOps Forecasting & Capacity Planning 결정 wire 보류, Phase 13+ 진입 시점" verbatim 해소 결정 wire. D-FINOPS-3 신규 honestly DEFER 보존 → Phase 13 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire 진입 + CR 11-3 honest-DEFER discipline 113번째 epic 연속 정직 회복 검증 보존.

> **v1.38 (2026-08-24, Phase 13 PRD entry)** — FinOps Forecasting & Capacity Planning capability gate 1 NEW row: `FINOPS_FORECASTING_CAPACITY_PLANNING` (`apps/api/modules/finops/forecast_definition.py` NEW ~+150 LOC + `parse_forecast_definition(definition_text)` parser + `validate_forecast_scope(tenant_id, target_metric)` validator + `ForecastDefinition` TypedDict 10 fields (forecast_id + tenant_id + target_metric enum department/cost_center/product_line/service/tenant_total + dimension_value + horizon_months enum 3m/6m/12m/24m + model_type enum arima/prophet/lstm/ensemble + confidence_level enum 80/90/95/99 + retraining_cron + status enum active/paused/expired + created_at + updated_at) + 5 layer defense (syntax + semantic + tenant-scope RLS + target_metric validation + history data availability) + `FORECAST_DEFAULTS = {'horizon_months': 12, 'model_type': 'ensemble', 'confidence_level': 95, 'retraining_cron': '0 3 * * 0'}` constants + audit-first INSERT `forecast_definition_updated` CR 1-1 verbatim) + `apps/api/modules/finops/forecast_engine.py` NEW ~+200 LOC + `generate_forecast(tenant_id, target_metric, horizon_months) -> ForecastResult` + 4 time series models parallel run (ARIMA p=2,d=1,q=2 + Prophet seasonality_mode='multiplicative' + LSTM hidden_layers=50 + ensemble voting consensus) + statsmodels==0.14.1 + prophet==1.1.5 + tensorflow==2.15.0 AD-14 stack pin 결정 wire + ForecastResult TypedDict 10 fields (forecast_id + tenant_id + target_metric + horizon_months + predicted_values List + confidence_lower List + confidence_upper List + model_type + model_version + generated_at) + last 12-month historical baseline data source = phase_11_finops_showback table (Phase 11 wire 정합) + phase_12_finops_anomaly_detection table (Phase 12 wire 정합) + seasonality detection (weekly + monthly + quarterly + yearly) + trend decomposition (STL) + holiday calendar KST 8 holidays (신정 + 설날 + 삼일절 + 어린이날 + 현충일 + 광복절 + 개천절 + 圣诞节) + model_registry `apps/api/modules/finops/forecast_model_registry.py` NEW + audit-first INSERT `forecast_generated` CR 1-1 verbatim 결정 wire + `apps/api/modules/finops/capacity_headroom.py` NEW ~+180 LOC + `analyze_capacity_headroom(tenant_id, resource_type) -> CapacityHeadroomReport` + 3 resource type (compute CPU + memory utilization 90일 lookahead LSTM primary + storage DB size + backup storage 90일 lookahead Prophet primary + network egress + ingress bandwidth 90일 lookahead ARIMA primary) + headroom_pct = (1 - saturation_pct) × 100 + critical threshold headroom < 20% → Slack + PagerDuty + warning threshold headroom < 40% → Slack + CapacityHeadroomReport TypedDict 14 fields + Phase 8 wire `60d4ea1` k6 부하 테스트 EXTENSION + Phase 7 wire `59b56cd` Prometheus EXTENSION + Phase 5 wire `f093f8c` cross-region replica EXTENSION 정합 + audit-first INSERT `capacity_headroom_analyzed` CR 1-1 verbatim 결정 wire + `apps/api/modules/finops/budget_burnrate.py` NEW ~+150 LOC + `project_budget_consumption(tenant_id, period_key) -> BurnRateProjection` + Phase 12 wire `f3c0e63` budget_alert linear extrapolation EXTENSION + ARIMA-based projection + 7/30-day rolling projection + BurnRateProjection TypedDict 12 fields + predicted_overrun_pct > 110% warning alert + predicted_overrun_pct > 130% critical alert + audit-first INSERT `budget_burn_rate_projected` CR 1-1 verbatim 결정 wire + `apps/api/modules/finops/forecast_accuracy_tracker.py` NEW ~+120 LOC + Phase 12 wire `f3c0e63` forecast_accuracy.py EXTENSION + per-model accuracy tracking (per tenant_id + target_metric + model_type granularity) + MAE + MAPE + RMSE 3 metrics + ensemble vs individual model comparison + model performance degradation detection (MAPE > 20% for 3 consecutive periods) → model retraining trigger + retraining cron KST 매주 일요일 03:00 UTC 18:00 (Phase 12 anomaly detection isolation forest retraining cron EXTENSION 정합) + audit-first INSERT `forecast_accuracy_degraded` CR 1-1 verbatim + `model_retraining_triggered` 1 NEW action 결정 wire + ActionClass.FINOPS_FORECAST 신규 정의 + `apps/api/core/audit_action.py` MODIFIED AuditAction Literal EXTENSION 7 NEW values (`forecast_definition_updated` + `forecast_generated` + `capacity_headroom_analyzed` + `budget_burn_rate_projected` + `forecast_accuracy_degraded` + `model_retraining_triggered` + `forecast_dry_run_executed`) + `_ActionRegistry` FINOPS_FORECAST entry 신규 1개 등록 + `__all__` EXTENSION 결정 wire + `apps/api/alembic/versions/0045_phase_13_forecasting.py` NEW + 5 NEW tables (`phase_13_finops_forecast_definition` 12 columns + `phase_13_finops_forecast_result` 14 columns + `phase_13_finops_capacity_headroom` 16 columns + `phase_13_finops_budget_burnrate` 14 columns + `phase_13_finops_forecast_preview` 7 columns) + RLS policy `tenant_id = current_setting('app.tenant_id')::uuid` CR 0-2 verbatim + down_revision "0044_phase_12_finops_anomaly" + dry-run mode `--finops-forecast-dry-run` + `--finops-capacity-dry-run` + `--finops-burnrate-dry-run` 3 CLI flags 결정 wire + 14 NEW typed exceptions (`ForecastDefinitionInvalidError(400)` + `ForecastScopeInvalidError(404)` + `ForecastHistoryUnavailableError(404)` + `ForecastEngineError(500)` + `ForecastModelTrainingError(500)` + `ForecastSeasonalityDetectionError(500)` + `CapacityHeadroomAnalysisError(500)` + `CapacityThresholdBreachError(500)` + `CapacityMetricUnavailableError(404)` + `BudgetBurnRateProjectionError(500)` + `BudgetOverrunPredictionError(500)` + `ForecastAccuracyTrackingError(500)` + `ModelRetrainingTriggerError(500)` + `ModelPerformanceDegradationError(500)`) CR 12-5 D-14 envelope + `apps/web/app/[locale]/(dashboard)/admin/finops/forecast/page.tsx` NEW ~+150 LOC + 4 components (`ForecastHorizonSelector` + `ForecastChart` Recharts 2.12.7 AD-14 stack pin + `CapacityHeadroomGauge` + `BudgetBurnRatePanel`) + `apps/web/lib/finops-forecast/finops-forecast-client.ts` NEW + ko-KR.json `finops_forecast.*` namespace EXTENSION ~30 keys (CR 11-4 D-002 verbatim SSOT) + dry-run mode UI 결정 wire). industry-agnostic 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4 precedent like `FINOPS_ANOMALY_DETECTION` + `FINOPS_BUDGET_ALERT` Phase 12 wire `f3c0e63` + `FINOPS_SHOWBACK` + `FINOPS_CHARGEBACK` Phase 11 wire `e020ad0` + `SLO_ENGINEERING` Phase 10 wire `ac5d6c5` + `CHAOS_ENGINEERING` Phase 9 wire `e7670e1` + `PERFORMANCE_TESTING` Phase 8 wire `60d4ea1` + `OBSERVABILITY_TRACES` + `OBSERVABILITY_METRICS` Phase 7 wire `59b56cd` + `AUDIT_LOG_RETENTION` Phase 6 wire `24e1cd7` + `AUDIT_LOG_VIEW` Epic 17 wire + `MULTI_REGION_BACKUP` + `MULTI_REGION_FAILOVER` Phase 5 wire + `TENANT_IDP_MANAGEMENT` Epic 16 wire + `SSO_ENTERPRISE` Epic 15 wire + `LISTEN_NOTIFY_*` Epic 13/14 wire + `AUTH_MIDDLEWARE` Phase 3 wire + `LAUNCH_*` 1st release wire + `DEPLOYMENT_*` Phase 4 wire pattern verbatim bind). AD-40 FinOps Forecasting & Capacity Planning 신규 (Phase 12 close-out retro `3354e83` (cj-style 112번째 wire entry) + Phase 12 atomic wire T1~T8 `f3c0e63` (cj-style 111번째) + Phase 12 spec entry `8c5f374` (cj-style 110번째) + Phase 12 PRD entry `344c7eb` (cj-style 109번째) 결정 wire 모두 DONE 진입 정합 보존 후 옵션 5종 중 옵션 (a) Phase 13+ 진입 + 옵션 (a) FinOps Forecasting & Capacity Planning (Recommended) 결정 wire 진입 — forecast definition DSL + cost forecasting engine 4 time series models ARIMA + Prophet + LSTM + ensemble + capacity headroom analysis compute + storage + network + budget burn-rate projection + forecast accuracy tracking + model retraining trigger + forecasting dashboard UI + audit-first INSERT 7 NEW + Capability FINOPS_FORECASTING_CAPACITY_PLANNING 1 NEW + dry-run mode + tests + wire scope T1~T8 territory 결정, Phase 12 wire `f3c0e63` 의 anomaly detection baseline last 30d/90d/YTD + forecast accuracy tracking MAE/MAPE/RMSE + Phase 11 wire `e020ad0` showback period selector + Phase 8 wire `60d4ea1` cost-engine 12-period benchmark 의 자연스러운 carry-over chain (historical baseline ⇒ forward forecast EXTENSION 12-month prediction with 95% CI + capacity headroom 90일 lookahead + budget burn-rate EXTENSION 정직 회복 chain) 결정). Phase 13 wire scope 결정 보존 T1~T8 (T1 forecast_definition + forecast_dsl module + T2 forecast_engine + 4 time series models + T3 capacity_headroom + compute/storage/network + T4 budget_burnrate + Phase 12 budget_alert carry-over + forecast_accuracy_tracker module + T5 alembic 0045 phase_13_forecasting + T6 audit action EXTENSION 7 NEW + T7 capability v1.38 EXTENSION 1 NEW row + frontend finops forecast dashboard + T8 3중 게이트 FINAL CLEAN atomic commit 결정 wire 보류, cj-style Phase 13 3번째 진입점 진입 시점). wire_commit = TBD (cj-style Phase 13 3번째 진입점 진입 시점, expected cj-style 115번째 epic 연속 정직 회복). Phase 12 close-out retro `3354e83` + Phase 11 close-out retro `80df15b` + Phase 10 close-out retro `733d428` + Phase 9 close-out retro `634427d` + Phase 8 close-out retro `ab495a8` + Phase 7 close-out retro `326fa9f` + Phase 6 close-out retro `f9f006c` + Epic 17 close-out retro `be8f3bd` "FinOps Forecasting & Capacity Planning 결정 wire 보류, Phase 13+ 진입 시점" verbatim 해소 결정 wire. D-FINOPS-3 신규 honestly DEFER 보존 → Phase 13 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire 진입 + CR 11-3 honest-DEFER discipline 113번째 epic 연속 정직 회복 검증 보존.

> **v1.37 (2026-08-24, Phase 12 wire DONE)** — Cost Anomaly Detection & Budget Alerting capability gates 2 NEW rows wire DONE 진입 (cj-style Phase 12 3rd entry = cj-style 111번째 epic 연속 정직 회복 atomic docs-and-source wire). baseline_commit `8c5f374` (Phase 12 spec entry tip). territory wire scope 결정 보존 T1~T8 (T1 anomaly_detection + anomaly_detection_dsl module NEW 347 LOC + T2 budget_definition + parse_budget_definition NEW 402 LOC + T3 anomaly_detection_engine + voting_consensus + _assign_severity NEW ~340 LOC + T4 budget_alert + route_budget_alert + forecast_accuracy + compute_mae/mape/rmse NEW ~490 LOC + T5 alembic 0044 phase_12_finops_anomaly NEW ~650 LOC 6 tables + RLS + CHECK + T6 14 NEW typed exceptions + ActionClass.FINOPS_ANOMALY + ActionClass.FINOPS_BUDGET + 7 NEW audit values + 2 NEW Capability + 4-industry grants + T7 capability v1.37 EXTENSION 2 NEW rows + apps/web AnomalyDashboardPanel + admin/finops/anomaly + lib/finops anomaly-types + anomaly-client + ko-KR.json EXTENSION ~50 keys + T6.5 50 NEW pytest + 7 NEW vitest + T8 3중 게이트 FINAL CLEAN atomic commit). 3중 게이트 impact CLEAN (ruff scoped Phase 12 wire Python files = 0 NEW errors + pytest 50 NEW cases PASS + vitest 7 NEW cases PASS + pnpm tsc --noEmit 0 NEW errors + 0 regressions). CR lessons applied 14종 (CR 0-2 RLS 6 tables + CR 1-1 audit-first INSERT 7 NEW + CR 9-6 commit message + CR 11-3 honest-DEFER + CR 11-4 P-015 + CR 12-1 L4 industry-agnostic + CR 12-5 D-14 typed exception envelope 14 NEW + CR 12-5 D-PARITY-01 inversion + CR 12-5 D-GATE-01 inversion + A19 cohesion 9 surface + A36 SDR + AD-14 stack pin sklearn==1.4.0 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 + Recharts 2.12.7 + AD-22 owner-only RBAC + NFR4 PII minimization). **D-FINOPS-2 honestly DEFER 보존 1 NEW 결정 wire 진입 완료** (cj-style 111번째 wire DONE 진입 시점에 honestly preserved 결정 wire 완료 보존). wire_commit = TBD (cj-style Phase 12 3번째 진입점 진입 시점, expected cj-style 111번째 epic 연속 정직 회복). A19 cohesion 9 surface EXTENSION PASS (FinOps Anomaly surface NEW = F28.1~F28.8 Cost Anomaly Detection & Budget Alerting territory 결정 wire 보존). cj-style 4-entry-point (PRD entry + spec entry + wire + close-out retro) Phase 12 entry 3/4 진입 완료 보존 + Phase 12 close-out retro 결정 wire 보류.

> **v1.37 (2026-08-24, Phase 12 PRD entry)** — Cost Anomaly Detection & Budget Alerting capability gates 2 NEW rows: `FINOPS_ANOMALY_DETECTION` (`apps/api/modules/finops/anomaly_detection.py` NEW ~+150 LOC + `parse_anomaly_definition(definition_text)` parser + `validate_anomaly_scope(tenant_id, dimension)` validator + `AnomalyDefinition` TypedDict 8 fields (tenant_id + period_key + dimension + dimension_value + threshold_method + threshold_value + baseline_window + consecutive_periods_required) + 5 layer defense (syntax + semantic + tenant-scope RLS + dimension validation + baseline data availability) + audit-first INSERT `anomaly_detected` CR 1-1 verbatim) + `apps/api/modules/finops/anomaly_detection_engine.py` NEW ~+180 LOC + `detect_anomalies(tenant_id, period_key, dimension) -> List[AnomalyResult]` + 4 detection methods parallel run (z_score + IQR + EWMA + isolation_forest) + multi-method voting consensus (3 of 4 agree = anomaly confirmed) + sklearn==1.4.0 AD-14 stack pin 결정 wire + AnomalyResult TypedDict 14 fields (anomaly_id + tenant_id + period_key + dimension + dimension_value + observed_value + expected_value + deviation_pct + z_score + severity enum warning/critical + detection_method enum z_score/iqr/ewma/isolation_forest + detected_at + trace_id + confirmed_by_consensus) + false positive suppression (require 3 consecutive periods 동일 anomaly) + Slack webhook integration `#bizup-finops-alerts` channel AD-14 stack pin slack-sdk==3.23.0 + PagerDuty integration `pd_anomaly_critical` service AD-14 stack pin pdpyras==5.2.0 + severity routing (warning → Slack only / critical → Slack + PagerDuty / exceeded → Slack + PagerDuty + Email) + alert deduplication 1시간 이내 중복 skip + isolation_forest model per-tenant sklearn==1.4.0 + retraining cron KST 매주 일요일 03:00 UTC 18:00 + MAPE > 20% for 3 consecutive periods trigger retraining + 6 NEW typed exceptions (`AnomalyDefinitionInvalidError(400)` + `AnomalyDetectionError(500)` + `AnomalyBaselineUnavailableError(404)` + `AlertRoutingError(500)` + `AlertChannelUnavailableError(503)` + `SlackAPIError(502)` + `PagerDutyAPIError(502)`) CR 12-5 D-14 envelope 결정 wire + `apps/api/modules/finops/forecast_accuracy.py` NEW ~+120 LOC + `track_forecast_deviation(tenant_id, period_key) -> ForecastAccuracyReport` + 3 metrics (MAE + MAPE + RMSE) + model_version tracking + audit-first INSERT `forecast_deviation` CR 1-1 verbatim 결정 wire + ActionClass.FINOPS_ANOMALY 신규 정의 + `apps/api/core/audit_action.py` MODIFIED AuditAction Literal EXTENSION 4 NEW values (`anomaly_detected` + `alert_sent` + `forecast_deviation` + `model_retraining_triggered`) + `_ActionRegistry` FINOPS_ANOMALY entry 신규 4개 등록 + `__all__` EXTENSION 결정 wire + `apps/api/alembic/versions/0044_phase_12_finops_anomaly.py` NEW + 3 NEW tables (`phase_12_finops_anomaly` 14 columns + `phase_12_finops_anomaly_baseline` 8 columns + `phase_12_finops_anomaly_preview` 7 columns) + RLS policy `tenant_id = current_setting('app.tenant_id')::uuid` CR 0-2 verbatim + down_revision "0043_phase_11_finops" + dry-run mode `--finops-anomaly-dry-run` CLI flag 결정 wire + `FINOPS_BUDGET_ALERT` (`apps/api/modules/finops/budget_definition.py` NEW ~+150 LOC + `parse_budget_definition(definition_text)` parser + `validate_budget_scope(tenant_id, scope, scope_id)` validator + `BudgetDefinition` TypedDict 12 fields (budget_id + tenant_id + period_key + budget_period enum monthly/quarterly/yearly + scope enum tenant/department/cost_center/product_line + scope_id + amount NUMERIC(20, 2) + currency KRW + alert_thresholds + status enum active/paused/expired + created_at + updated_at) + UNIQUE constraint `UNIQUE (tenant_id, period_key, scope, scope_id)` + RLS 자동 적용 CR 0-2 verbatim + audit-first INSERT `budget_definition_updated` CR 1-1 verbatim) + `apps/api/modules/finops/budget_alert.py` NEW ~+150 LOC + `check_budget_alerts(tenant_id, period_key) -> List[BudgetAlertResult]` + real-time consumption tracking (per-chargeback INSERT trigger) + threshold-based alerting (80% warning + 90% critical + 100% exceeded) + BudgetAlertResult TypedDict 11 fields (alert_id + tenant_id + period_key + budget_id + budget_amount + actual_amount + consumption_pct + severity enum warning/critical/exceeded + alert_channels + sent_at + trace_id) + Slack webhook `#bizup-finops-budget-alerts` channel + PagerDuty integration `pd_budget_exceeded` service + Email notification sendgrid==6.11.0 AD-14 stack pin + alert deduplication 24시간 이내 중복 skip + budget overrun prediction (linear extrapolation) + predicted_overrun_pct > 110% → warning alert + ActionClass.FINOPS_BUDGET 신규 정의 + `apps/api/core/audit_action.py` MODIFIED AuditAction Literal EXTENSION 4 NEW values (`budget_definition_updated` + `budget_threshold_exceeded` + `budget_alert_sent` + `budget_period_expired`) + `_ActionRegistry` FINOPS_BUDGET entry 신규 4개 등록 + `__all__` EXTENSION 결정 wire + `apps/api/alembic/versions/0044_phase_12_finops_anomaly.py` NEW (EXTENSION same migration file) + 3 NEW tables (`phase_12_finops_budget` 14 columns + `phase_12_finops_budget_consumption` 8 columns + `phase_12_finops_budget_preview` 7 columns) + RLS policy CR 0-2 verbatim + budget_period 만료 처리 (auto-expire at period end) + dry-run mode `--finops-budget-dry-run` CLI flag + 3 NEW typed exceptions (`BudgetDefinitionInvalidError(400)` + `BudgetScopeInvalidError(404)` + `BudgetAmountInvalidError(400)` + `BudgetAlertError(500)` + `BudgetConsumptionUpdateError(500)`) CR 12-5 D-14 envelope + `apps/web/app/[locale]/(dashboard)/admin/finops/anomaly/page.tsx` NEW ~+150 LOC + 4 components (`AnomalyDetectionChart` Recharts 2.12.7 AD-14 stack pin + `AnomalyDetectionMethodSelector` 4 detection methods radio button + `AnomalyDetectionThresholdSlider` 4 sliders + `BudgetAlertPanel`) + `apps/web/lib/finops-anomaly/finops-anomaly-client.ts` NEW + ko-KR.json `finops_anomaly.*` namespace EXTENSION ~25 keys (CR 11-4 D-002 verbatim SSOT) + dry-run mode UI 결정 wire). industry-agnostic 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4 precedent like `FINOPS_SHOWBACK` + `FINOPS_CHARGEBACK` Phase 11 wire + `SLO_ENGINEERING` Phase 10 wire + `CHAOS_ENGINEERING` Phase 9 wire + `PERFORMANCE_TESTING` Phase 8 wire + `OBSERVABILITY_TRACES` + `OBSERVABILITY_METRICS` Phase 7 wire + `AUDIT_LOG_RETENTION` Phase 6 wire + `AUDIT_LOG_VIEW` Epic 17 wire + `MULTI_REGION_BACKUP` + `MULTI_REGION_FAILOVER` Phase 5 wire + `TENANT_IDP_MANAGEMENT` Epic 16 wire + `SSO_ENTERPRISE` Epic 15 wire + `LISTEN_NOTIFY_*` Epic 13/14 wire + `AUTH_MIDDLEWARE` Phase 3 wire + `LAUNCH_*` 1st release wire + `DEPLOYMENT_*` Phase 4 wire pattern verbatim bind). AD-39 Cost Anomaly Detection & Budget Alerting 신규 (Phase 11 close-out retro `80df15b` (cj-style 108번째 wire entry) + Phase 11 atomic wire T1~T8 `e020ad0` (cj-style 107번째) + Phase 11 spec entry `82c93a8` (cj-style 106번째) + Phase 11 PRD entry `16d7698` (cj-style 105번째) 결정 wire 모두 DONE 진입 정합 보존 후 옵션 5종 중 옵션 (a) Phase 12+ 진입 + 옵션 (a) Cost Anomaly Detection & Budget Alerting (Recommended) 결정 wire 진입 — anomaly detection DSL 4 methods z-score/IQR/EWMA/isolation forest + budget definition DSL + anomaly detection engine + alert routing Slack + PagerDuty + forecast accuracy tracking + audit-first INSERT 7 NEW + Capability FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT 2 NEW + dry-run mode + tests + wire scope T1~T8 territory 결정, Phase 11 wire `e020ad0` 의 FinOps Showback / Chargeback territory (showback baseline 대비 deviation 감지 = cost anomaly detection + chargeback 한도 초과 알림 = budget alert + statistical + ML hybrid detection methods + alert routing/escalation) 의 DETECTION & ALERTING LAYER EXTENSION 정직 회복 chain + Phase 8 wire `60d4ea1` 의 cost-engine 12-period benchmark 의 자연스러운 carry-over chain (historical baseline last 30d + last 90d + YTD + statistical model training + forecast deviation tracking EXTENSION) 결정). Phase 12 wire scope 결정 보존 T1~T8 (T1 anomaly_detection + anomaly_detection_dsl module + T2 budget_definition + budget_definition_dsl module + T3 anomaly_detection_engine + alert routing + T4 budget_alert + forecast_accuracy module + T5 alembic 0044 phase_12_finops_anomaly + T6 audit action EXTENSION 7 NEW + T7 capability v1.37 EXTENSION 2 NEW rows + frontend finops anomaly dashboard + T8 3중 게이트 FINAL CLEAN atomic commit 결정 wire 보류, cj-style Phase 12 3번째 진입점 진입 시점). wire_commit = TBD (cj-style Phase 12 3번째 진입점 진입 시점, expected cj-style 111번째 epic 연속 정직 회복). Phase 11 close-out retro `80df15b` + Phase 10 close-out retro `733d428` + Phase 9 close-out retro `634427d` + Phase 8 close-out retro `ab495a8` + Phase 7 close-out retro `326fa9f` + Phase 6 close-out retro `f9f006c` + Epic 17 close-out retro `be8f3bd` "Cost Anomaly Detection & Budget Alerting 결정 wire 보류, Phase 12+ 진입 시점" verbatim 해소 결정 wire. D-FINOPS-2 honestly DEFER 보존 → Phase 12 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire 진입 + CR 11-3 honest-DEFER discipline 109번째 epic 연속 정직 회복 검증 보존.

> **v1.36 (2026-08-24, Phase 11 PRD entry)**

> **v1.36 (2026-08-24, Phase 11 PRD entry)** — FinOps Showback / Chargeback capability gate 2 NEW rows: `FINOPS_SHOWBACK` + `FINOPS_CHARGEBACK` (`apps/api/modules/finops/showback_dsl.py` NEW ~+150 LOC + `showback(tenant_id, period_key, department_id, group_by)` builder + 5 group_by 옵션 결정 (department + cost_center + product_line + service + custom_tag) + 6 period selector 모드 결정 (current month + previous month + last 3 months + last 6 months + YTD + custom range) + comparison view + 4 industries baseline + per-tenant override EXTENSION + `SHOWBACK_PERIOD_DEFAULTS` constants + audit-first INSERT `showback_generated` CR 1-1 verbatim) + `apps/api/modules/finops/showback_query.py` NEW ~+120 LOC + `DepartmentBreakdown` + `ComparisonView` TypedDict CR 12-5 D-PARITY-01 verbatim + `apps/api/modules/finops/chargeback_engine.py` NEW ~+180 LOC + `ChargebackRule` TypedDict 6 fields + chargeback rule 3종 결정 (정액제 flat_fee + 비율배분 proportional_allocation + usage-based metered) + markup_pct (default 0%, max 50% range 0~50% + 0.01 step) + tax_pct (default 10% VAT + per-tenant override EXTENSION) + cost_allocation_method enum direct/indirect/shared + chargeback_period_monthly + chargeback_export_format enum csv/pdf + 2 NEW error classes `ChargebackRuleInvalidError(400)` + `ChargebackCalculationError(500)` CR 12-5 D-14 envelope + `apps/api/modules/finops/chargeback_rule_evaluator.py` NEW ~+100 LOC + `apps/api/modules/finops/department_mapping.py` NEW ~+120 LOC + `tenant_settings.cost_center_mapping` JSONB TypedDict + UNIQUE constraint `UNIQUE (tenant_id, department_id)` + RLS policy `tenant_id = current_setting('app.tenant_id')::uuid` CR 0-2 verbatim + audit-first INSERT `department_mapping_updated` CR 1-1 verbatim + `apps/api/modules/finops/chargeback_export.py` NEW ~+150 LOC + `export_chargeback_csv` StreamingResponse 결정 (Excel-compatible UTF-8 BOM `﻿` + comma-separated + double-quote escape) + `export_chargeback_pdf` bytes 결정 (reportlab 기반 + company logo + department breakdown 차트 PDF 임베드) + streaming response + audit-first INSERT `chargeback_exported` CR 1-1 verbatim + reportlab AD-14 stack pin + audit-first INSERT 3 NEW `showback_generated` + `department_mapping_updated` + `chargeback_exported` CR 1-1 verbatim + ActionClass.FINOPS 신규 정의 + `apps/api/core/audit_action.py` MODIFIED AuditAction Literal EXTENSION 3 NEW values + `_ActionRegistry` FINOPS entry 신규 3개 등록 + `__all__` EXTENSION 결정 wire + `apps/api/alembic/versions/0043_phase_11_finops.py` NEW + 3 NEW tables (`phase_11_finops_showback` 14 columns + `phase_11_finops_chargeback` 12 columns + `phase_11_finops_department_mapping` 9 columns) + 4 indexes + 2 CHECK constraints + UNIQUE constraint + RLS policy CR 0-2 verbatim + down_revision "0042_phase_10_slo_engineering" + `apps/web/app/[locale]/(dashboard)/admin/finops/page.tsx` NEW ~+150 LOC + 4 components (`ShowbackPeriodSelector` + `ShowbackDepartmentBreakdownChart` + `ShowbackComparisonView` + `ShowbackCSVExportButton`) + `apps/web/lib/finops/finops-client.ts` NEW + ko-KR.json `finops.*` namespace EXTENSION ~25 keys (CR 11-4 D-002 verbatim SSOT) + dry-run mode `--finops-dry-run` CLI flag + ~+46 NEW pytest PASS + ~+5 NEW vitest PASS + 0 NEW ruff + 0 regressions). industry-agnostic 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4 precedent like `SLO_ENGINEERING` Phase 10 wire + `CHAOS_ENGINEERING` Phase 9 wire + `PERFORMANCE_TESTING` Phase 8 wire + `OBSERVABILITY_TRACES` + `OBSERVABILITY_METRICS` Phase 7 wire + `AUDIT_LOG_RETENTION` Phase 6 wire + `AUDIT_LOG_VIEW` Epic 17 wire + `MULTI_REGION_BACKUP` + `MULTI_REGION_FAILOVER` Phase 5 wire + `TENANT_IDP_MANAGEMENT` Epic 16 wire + `SSO_ENTERPRISE` Epic 15 wire + `LISTEN_NOTIFY_*` Epic 13/14 wire + `AUTH_MIDDLEWARE` Phase 3 wire + `LAUNCH_*` 1st release wire + `DEPLOYMENT_*` Phase 4 wire pattern verbatim bind). AD-38 FinOps Showback / Chargeback 신규 (Phase 10 close-out retro `733d428` (cj-style 104번째 wire entry) + Phase 10 atomic wire T1~T8 `ac5d6c5` (cj-style 103번째) + Phase 10 spec entry `3c80ef0` (cj-style 102번째) + Phase 10 PRD entry `09db4d4` (cj-style 101번째) 결정 wire 모두 DONE 진입 정합 보존 후 옵션 5종 중 옵션 (a) Phase 11+ 진입 + 옵션 (d) FinOps Showback / Chargeback (Recommended) 결정 wire 진입 — showback DSL + period selector + comparison view + chargeback cost allocation engine + markup + tax + department cost center mapping + showback dashboard UI + chargeback CSV/PDF export + dry-run mode territory 결정, Epic 7~10 wire (`756a32a` ~ `ac5d6c5`) 의 ABC engine / TDABC / BEP slider / next-month projection / budget scenario / AI 인사이트 의 cost 분석 territory + Phase 10 wire `ac5d6c5` 의 cost-engine p99 < 5s SLO + error_budget tracker 의 30d rolling + monthly reset KST 1일 00:00 territory + Phase 8 wire `60d4ea1` 의 cost-engine benchmark V8 골든 fixture 의 자연스러운 carry-over chain 결정 (cost 산출 ⇒ showback 가시성 ⇒ chargeback 비용 책임 ⇒ ERP integration territory 의 FINANCIAL REPORTING LAYER EXTENSION 정직 회복 chain)). Phase 11 wire scope 결정 보존 T1~T8 (T1 showback_dsl + showback_query module + T2 chargeback_engine + chargeback_rule_evaluator + T3 department_mapping + tenant_settings JSONB schema + T4 chargeback CSV/PDF export + T5 alembic 0043 phase_11_finops + T6 audit action EXTENSION 3 NEW + T7 capability v1.36 EXTENSION 2 NEW rows + frontend finops dashboard + T8 3중 게이트 FINAL CLEAN atomic commit 결정 wire 보류, cj-style Phase 11 3번째 진입점 진입 시점). wire_commit = TBD (cj-style Phase 11 3번째 진입점 진입 시점, expected cj-style 107번째 epic 연속 정직 회복). Phase 10 close-out retro `733d428` + Phase 9 close-out retro `634427d` + Phase 8 close-out retro `ab495a8` + Phase 7 close-out retro `326fa9f` "FinOps Showback / Chargeback 결정 wire 보류, Phase 11+ 진입 시점" verbatim 해소 결정 wire. D-FINOPS-1 honestly RESOLVE 진입 wire 결정 + CR 11-3 honest-DEFER discipline 105번째 epic 연속 정직 회복 검증 보존.

> **v1.35 (2026-08-24, Phase 10 PRD entry)** — SLO Engineering / Error Budget Management capability gate 1 NEW row: `SLO_ENGINEERING` (`apps/api/modules/slo/slo_dsl.py` NEW ~+180 LOC + `SloDefinition` TypedDict 13 fields (slo_id TEXT PK + tenant_id UUID + service TEXT enum cost_engine/signups/logins/audit_purge + slo_type TEXT enum availability/latency/throughput + target REAL CHECK >0 <=1 + window_seconds INTEGER default 2592000 (30d) + burn_rate_threshold_1h REAL default 14.4 + burn_rate_threshold_6h REAL default 6.0 + alerting_policy TEXT + owner_user_id UUID + created_at + updated_at + trace_id) + `parse_slo_definition(tenant_id, payload) -> SloDefinition` CR 11-4 P-015 verbatim pure validator + 1 NEW error class `SloDefinitionInvalidError(400)` CR 12-5 D-14 envelope + `apps/api/jobs/slo_burn_rate_evaluator.py` NEW ~+200 LOC + Google SRE Workbook "multi-window, multi-burn-rate criteria" 패턴 verbatim + cron KST 매 5분 + 4 burn-rate windows (fast burn 1h window + slow burn 6h + budget exhaustion 24h + long burn 3d) + 1 NEW error class `SloBurnRateThresholdExceededError(429)` + 3 NEW Prometheus metrics `business_slo_burn_rate_factor{slo_id,window}` Gauge + `business_slo_budget_consumed_pct{slo_id,window}` Gauge + `business_slo_alerts_fired_total{slo_id,window,severity}` Counter Phase 7 wire `59b56cd` EXTENSION + `apps/api/modules/slo/error_budget.py` NEW ~+150 LOC + `ErrorBudget` TypedDict 8 fields + `consume_error_budget` atomic UPDATE AD-4 commit pattern verbatim + freeze mechanism governance 트리거 시 budget consumption 일시 정지 + 1 NEW error class `ErrorBudgetExhaustedError(429)` + multi-tenant isolation CR 0-2 RLS + `apps/api/modules/slo/multi_region_aggregator.py` NEW ~+180 LOC + `MultiRegionSloAggregate` TypedDict 7 fields + `aggregate_slo_across_regions` + `region_weight_map` default `{seoul: 0.6, tokyo: 0.3, singapore: 0.1}` + cross-region replication lag weighted adjustment Phase 5 wire `f093f8c` carry-over chain + `apps/api/modules/slo/tenant_scoping.py` NEW ~+120 LOC + `TenantSloOverride` TypedDict 6 fields + `apply_tenant_slo_override` + UNIQUE constraint `(tenant_id, slo_id)` + RLS policy CR 0-2 verbatim + `apps/api/modules/slo/governance.py` NEW ~+150 LOC + `GovernanceReview` TypedDict 7 fields + 4 trigger conditions (budget_consumed_pct > 75% for 7d OR burn_rate_3d > 1x sustained OR freeze_until expired + budget_negative OR error_budget exhausted < 24h to reset) + audit-first INSERT `slo_governance_review_initiated` CR 1-1 verbatim + owner-only RBAC AD-22 + Epic 12 2FA 챌린지 보존 + auto-rollback SLO breach trigger (business_cost_engine_p99_breach OR business_signups_success_rate_breach 1m sustained ⇒ Phase 9 wire `e7670e1` chaos_experiment_aborted + chaos_rollback_triggered 자동 fire) + audit-first INSERT 3 NEW `slo_target_updated` + `slo_budget_exhausted` + `slo_violation_detected` CR 1-1 verbatim + ActionClass.SLO_ENGINEERING 신규 정의 + `apps/api/core/audit_action.py` MODIFIED AuditAction Literal EXTENSION 3 NEW values + `_ActionRegistry` SLO_ENGINEERING entry 신규 3개 등록 + `__all__` EXTENSION 결정 wire + `apps/api/alembic/versions/0042_phase_10_slo_engineering.py` NEW + 4 NEW tables (`phase_10_slo_definitions` 13 columns + `phase_10_error_budget_tracker` 9 columns + `phase_10_tenant_slo_overrides` 7 columns + `phase_10_slo_governance_reviews` 10 columns) + 3 indexes + 2 CHECK constraints + UNIQUE constraint + RLS policy `tenant_id = current_setting('app.tenant_id')::uuid` CR 0-2 verbatim + down_revision "0041_phase_9_chaos_engineering" + `apps/web/app/[locale]/(dashboard)/admin/slo/page.tsx` NEW ~+150 LOC + 4 components (SloDefinitionList + SloBurnRateDashboard + ErrorBudgetTracker + SloGovernanceReviewList) + `apps/web/lib/slo/slo-client.ts` NEW ~+150 LOC + ko-KR.json `slo.*` namespace EXTENSION ~25 keys (CR 11-4 D-002 verbatim SSOT) + dry-run mode `--slo-engineering-dry-run` CLI flag + ~+46 NEW pytest PASS + ~+5 NEW vitest PASS + 0 NEW ruff + 0 regressions). industry-agnostic 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4 precedent like `CHAOS_ENGINEERING` Phase 9 wire `e7670e1` + `PERFORMANCE_TESTING` Phase 8 wire `60d4ea1` + `OBSERVABILITY_TRACES` + `OBSERVABILITY_METRICS` Phase 7 wire `59b56cd` + `AUDIT_LOG_RETENTION` Phase 6 wire `24e1cd7` + `AUDIT_LOG_VIEW` Epic 17 wire + `MULTI_REGION_BACKUP` + `MULTI_REGION_FAILOVER` Phase 5 wire + `TENANT_IDP_MANAGEMENT` Epic 16 wire + `SSO_ENTERPRISE` Epic 15 wire + `LISTEN_NOTIFY_*` Epic 13/14 wire + `AUTH_MIDDLEWARE` Phase 3 wire + `LAUNCH_*` 1st release wire + `DEPLOYMENT_*` Phase 4 wire pattern verbatim bind). AD-37 SLO Engineering / Error Budget Management 신규 (Phase 9 close-out retro `634427d` (cj-style 100번째 wire entry) + Phase 9 atomic wire T1~T8 `e7670e1` (cj-style 99번째) + Phase 9 spec entry `2a5e4da` (cj-style 98번째) + Phase 9 PRD entry `0b2d2f3` (cj-style 97번째) 결정 wire 모두 DONE 진입 정합 보존 후 옵션 5종 중 옵션 (a) Phase 10+ 진입 + 옵션 (a) SLO Engineering / Error Budget Management (Recommended) 결정 wire 진입 — SLO definition DSL + multi-window burn-rate evaluation + error budget tracker + multi-region SLO aggregation + tenant-scoped SLO override + SLO governance review + auto-rollback SLO breach trigger + dry-run mode territory 결정, Phase 8 wire `60d4ea1` 의 SLO/SLI 정의 4 metrics + Phase 9 wire `e7670e1` 의 chaos_experiment baseline + auto-rollback mechanism 의 자연스러운 carry-over chain (SLO 정의 ⇒ SLI 측정 ⇒ SLO 검증 ⇒ chaos 검증 ⇒ SLO 거버넌스 ⇒ error budget + burn rate + auto-rollback trigger 정직 회복 chain)). Phase 10 wire scope 결정 보존 T1~T8 (T1 slo_dsl + slo_burn_rate_evaluator modules + T2 error_budget module + T3 multi_region_aggregator + tenant_scoping modules + T4 governance + auto-rollback SLO breach trigger + T5 alembic 0042 phase_10_slo_engineering + T6 audit action EXTENSION 3 NEW + T7 capability v1.35 EXTENSION 1 NEW row + frontend slo dashboard + T8 3중 게이트 FINAL CLEAN atomic commit 결정 wire 보류, cj-style Phase 10 3번째 진입점 진입 시점). wire_commit = TBD (cj-style Phase 10 3번째 진입점 진입 시점, expected cj-style 103번째 epic 연속 정직 회복). Phase 9 close-out retro `634427d` + Phase 8 close-out retro `ab495a8` "SLO Engineering / Error Budget Management 결정 wire 보류, Phase 10+ 진입 시점" verbatim 해소 결정 wire. D-SLO-1 honestly RESOLVE 진입 wire 결정 + CR 11-3 honest-DEFER discipline 101번째 epic 연속 정직 회복 검증 보존.

> **Single source of truth** for the `Industry × Capability` gating that
> Epic 1 / 2 / 3 / 4 / 11 / 12 stories need to coordinate. Replaces the per-story
> capability tables with one consolidated matrix.
>
> **v1.33 (2026-08-24, Phase 8 PRD entry)** — Performance / Load Testing capability gate 1 NEW row: `PERFORMANCE_TESTING` (`apps/api/core/performance.py` NEW ~+150 LOC + `LatencyBudget` TypedDict + `check_latency_budget(engine, p99_seconds) -> LatencyBudgetResult` + 4-industry baseline industry-agnostic + per-tenant override EXTENSION + policy evaluation precedence tenant override > industry baseline > system default + `LatencyBudgetBreachedError(400)` 1 NEW error class CR 12-5 D-14 envelope + `apps/api/jobs/latency_regression.py` NEW ~+150 LOC + cron KST 매일 03:30 UTC 18:30 + drift > 10% p99 vs golden baseline 자동 감지 + Sentry breadcrumb `LatencyRegressionDetected` + Slack alert `#bizup-alerts` channel + audit-first INSERT `latency_regression_detected` CR 1-1 verbatim + dry-run mode + `BENCHMARK_GOLDEN_BASELINE_MS = {traditional: 800, abc: 1200, tdabc: 1500}` 결정 wire + `BENCHMARK_DRIFT_THRESHOLD = 1.10` 결정 wire + `apps/api/tests/performance/k6/scripts/smoke-test-100.js` + `baseline-1000.js` + `stress-5000.js` + `soak-100-1h.js` + `spike-10000.js` 5 NEW k6 scenarios 결정 wire + `k6==0.45.0` AD-14 stack pin 결정 wire + `.github/workflows/ci-performance.yml` NEW ~+120 LOC + k6 부하 테스트 자동 실행 + p99 budget check + threshold 초과 시 CI 빌드 차단 + `BASELINE_THRESHOLD=1.10` 결정 wire + `tests/performance/test_cost_engine_benchmark.py` NEW ~+250 LOC + Epic 11 V8 determinism 골든 fixture EXTENSION + cost-engine 3 engines benchmark 결정 wire + `docs/slo-sli-definition.md` NEW 8 sections + 4 SLO/SLI 결정 wire + `docs/load-testing.md` EXTENSION 12 sections runbook 결정 wire + `apps/web/app/[locale]/(dashboard)/admin/performance/page.tsx` NEW ~+150 LOC + ko-KR.json `performance.*` namespace EXTENSION 8 keys + dry-run mode UI 결정 wire). industry-agnostic 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4 precedent like `OBSERVABILITY_TRACES` + `OBSERVABILITY_METRICS` Phase 7 wire `59b56cd` + `AUDIT_LOG_RETENTION` Phase 6 wire `24e1cd7` + `AUDIT_LOG_VIEW` Epic 17 wire + `MULTI_REGION_BACKUP` + `MULTI_REGION_FAILOVER` Phase 5 wire + `TENANT_IDP_MANAGEMENT` Epic 16 wire + `SSO_ENTERPRISE` Epic 15 wire + `LISTEN_NOTIFY_*` Epic 13/14 wire + `AUTH_MIDDLEWARE` Phase 3 wire + `LAUNCH_*` 1st release wire + `DEPLOYMENT_*` Phase 4 wire pattern verbatim bind). AD-35 Performance Engineering 신규 (Phase 7 close-out retro `326fa9f` (cj-style 92번째 wire entry) + Phase 7 atomic wire T1~T8 `59b56cd` (cj-style 91번째) + Phase 7 spec entry `749381e` (cj-style 90번째) + Phase 7 PRD entry `916a541` (cj-style 89번째) 결정 wire 모두 DONE 진입 정합 보존 후 옵션 5종 중 옵션 (a) Phase 8+ 진입 + 옵션 (a) Performance / Load Testing territory (Recommended) 결정 wire 진입 — k6 부하 테스트 + SLO/SLI 정의 + p99 latency budget + Latency regression detector + Performance regression gate + Cost-engine benchmark V8 골든 + Load test report + runbook territory 결정, Phase 7 wire `59b56cd` 의 7 NEW business metrics (`business_signups_total` + `business_logins_total` + `business_calculations_total` + `business_cost_engine_duration_seconds{engine,tenant_size_bucket}` Histogram + `business_audit_log_purge_total` + `business_active_tenants_gauge` + `business_ai_extraction_duration_seconds`) + Prometheus 4 dashboards + head_based sampler 1.0 dev / 0.1 prod + SlowCalc alert rule 의 natural backend carry-over chain 결정). Phase 8 wire scope 결정 보존 T1~T8 (T1 k6 부하 테스트 5 scenarios + T2 SLO/SLI 정의 4 metrics + T3 p99 latency budget 5s + T4 Latency regression detector + T5 Performance regression gate CI + T6 Cost-engine benchmark V8 골든 + T7 capability v1.33 EXTENSION 1 NEW row + T8 3중 게이트 FINAL CLEAN atomic commit 결정 wire 보류, cj-style Phase 8 3번째 진입점 진입 시점). wire_commit = TBD (cj-style Phase 8 3번째 진입점 진입 시점, expected cj-style 95번째 epic 연속 정직 회복).

> **Single source of truth** for the `Industry × Capability` gating that
> Epic 1 / 2 / 3 / 4 / 11 / 12 stories need to coordinate. Replaces the per-story
> capability tables with one consolidated matrix.
>
> **v1.32 (2026-08-22, Phase 7 PRD entry)** — Observability Stack 강화 capability gates 2 NEW rows: `OBSERVABILITY_TRACES` (`apps/api/core/tracing.py` NEW ~+200 LOC + OTLP HTTP exporter 결정 wire + W3C Trace Context propagation `traceparent` + `tracestate` HTTP header 추출/주입 + FastAPI middleware `TraceContextMiddleware` 결정 wire + 비동기 trace context 보존 CR 1-1 ContextVar 정합 + span enrichment `tenant_id` + `user_id` + `trace_id` + `request_id` + `client_ip` 자동 span attribute 추가 + auto-instrumentation `opentelemetry-instrumentation-fastapi` + `opentelemetry-instrumentation-sqlalchemy` + `opentelemetry-instrumentation-httpx` + `opentelemetry-instrumentation-asyncpg` 4 instrumentors 결정 wire + head_based sampler ratio 1.0 dev + 0.1 prod + AD-14 stack pin `opentelemetry-api==1.27.0` + `opentelemetry-sdk==1.27.0` + `opentelemetry-exporter-otlp-proto-http==1.27.0` 결정 wire + Phase 4 wire `71a033a` Sentry `tracesSampleRate=0.1` 정합 보존 + Phase 5 wire `f093f8c` multi-region observability carry-over chain 결정) + `OBSERVABILITY_METRICS` (`apps/api/core/metrics.py` NEW ~+180 LOC + Counter + Histogram + Summary + Gauge 4 metric types + 7 NEW business metrics: `business_signups_total{industry,plan}` Counter + `business_logins_total{method,outcome}` Counter + `business_calculations_total{engine,outcome}` Counter + `business_cost_engine_duration_seconds{engine,tenant_size_bucket}` Histogram + `business_audit_log_purge_total{action_class}` Counter + `business_active_tenants_gauge` Gauge + `business_ai_extraction_duration_seconds{model,outcome}` Histogram + `prometheus-client==0.20.0` AD-14 stack pin 결정 wire + `/metrics` endpoint Prometheus exposition format + `docs/grafana-dashboards.md` NEW 4 dashboards: business-signups + cost-engine-performance + auth-flow + audit-log-purge 결정 wire + `apps/api/core/alerting.py` NEW ~+120 LOC + `config/alert_rules.yaml` NEW 5 NEW alert rules (`HighErrorRate` 5xx > 5% for 5m severity=critical + `SlowCalc` p99 > 5s for 10m severity=warning + `FailoverStuck` replication_lag_seconds > 30 for 5m Phase 5 wire 정합 severity=critical + `RetentionPurgeFailed` audit_log_purge_last_success_timestamp > 26h Phase 6 wire 정합 severity=warning + `MultiRegionDown` primary + secondary all down for 1m severity=critical) + Prometheus AlertManager integration + Sentry alert routing + Slack webhook integration `#bizup-alerts` channel + PagerDuty integration owner-only manual trigger AD-22 RBAC 결정 wire + audit-first INSERT `alert_fired` CR 1-1 verbatim action_class='OBSERVABILITY' 결정) + `apps/web/lib/tracing.ts` NEW ~+150 LOC + `@opentelemetry/sdk-trace-web` + `@opentelemetry/exporter-trace-otlp-http` AD-14 stack pin + W3C Trace Context propagation server → client through `traceparent` header + Web Vitals auto-collection LCP + FID + CLS + INP + TTFB 5 metrics + custom span attributes + `apps/web/instrumentation.ts` NEW Next.js instrumentation hook + `web-vitals` AD-14 stack pin 결정). industry-agnostic 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4 precedent like `AUDIT_LOG_RETENTION` Phase 6 wire `24e1cd7` + `AUDIT_LOG_VIEW` Epic 17 wire + `MULTI_REGION_BACKUP` + `MULTI_REGION_FAILOVER` Phase 5 wire + `TENANT_IDP_MANAGEMENT` Epic 16 wire + `SSO_ENTERPRISE` Epic 15 wire + `LISTEN_NOTIFY_*` Epic 13/14 wire + `AUTH_MIDDLEWARE` Phase 3 wire + `LAUNCH_*` 1st release wire + `DEPLOYMENT_*` Phase 4 wire pattern verbatim bind). AD-34 Observability Stack 강화 신규 (Phase 6 close-out retro `f9f006c` (cj-style 88번째 wire entry) + Phase 6 atomic wire T1~T8 `24e1cd7` (cj-style 87번째) + Phase 6 spec entry `f5c14c9` (cj-style 86번째) + Phase 6 PRD entry `e84a281` (cj-style 85번째) 결정 wire 모두 DONE 진입 정합 보존 후 옵션 5종 중 옵션 (a) Phase 7+ 진입 + 옵션 (a) Observability Stack 강화 (Recommended) 결정 wire 진입 — OpenTelemetry distributed tracing + Prometheus custom metrics + Grafana dashboards + Alerting + Frontend performance tracing territory 결정, Phase 4 wire `71a033a` Sentry `tracesSampleRate=0.1` 의 자연스러운 carry-over + Phase 5 wire `f093f8c` multi-region observability chain 자연스러운 EXTENSION 결정). Phase 7 wire scope 결정 보존 T1~T8 (T1 OpenTelemetry tracing module + T2 Prometheus metrics module + T3 Alerting module + T4 Frontend tracing module + T5 capability v1.32 EXTENSION 2 NEW rows + T6 audit action EXTENSION 2 NEW + T7 Tests + T8 3중 게이트 FINAL CLEAN atomic commit 결정 wire 보류, cj-style Phase 7 3번째 진입점 진입 시점). wire_commit = TBD (cj-style Phase 7 3번째 진입점 진입 시점, expected cj-style 91번째 epic 연속 정직 회복).
>
> **v1.31 (2026-08-22, Phase 6 wire bmad-dev-story entry)** — Audit Log Retention Policy capability gate 1 NEW row: `AUDIT_LOG_RETENTION` (`apps/api/modules/audit/retention/retention_dsl.py` NEW ~120 LOC + `RetentionPolicy` TypedDict + `retain(action_class, days, archive, mask_pii)` builder + `parse_retention_policy(tenant_id, payload) -> RetentionPolicy` + RLS 자동 적용 CR 0-2 verbatim + 1 NEW error class `AuditLogRetentionPolicyInvalidError(400)` CR 12-5 D-14 envelope) + `apps/api/modules/audit/retention/erasure.py` NEW ~150 LOC + `POST /api/v1/audit-log/erase` endpoint + `require_role("owner")` permission gate AD-22 verbatim + `audit_log_personal_data_erased` action + PII masking via AES-256-GCM NFR6 + archive preservation 결정 wire) + `apps/api/modules/audit/retention/retention_routes.py` NEW ~180 LOC + retention policy CRUD (GET/POST/PUT/DELETE `/api/v1/audit-log/retention[/...]`) + audit-first INSERT `retention_policy_updated` CR 1-1 verbatim + dry-run mode UI (POST `/api/v1/audit-log/retention/preview`) 결정 wire + `apps/api/jobs/audit_log_purge.py` NEW ~180 LOC + KST cron 02:00 daily (UTC 17:00) + APScheduler lifespan hook + idempotent DELETE WHERE created_at < now() - retention_days + batch=1000 pagination + audit-first INSERT `audit_log_purged` CR 1-1 verbatim + dry_run=True dry-run mode 결정 wire + `apps/api/db/migrations/versions/0040_phase_6_audit_retention.py` NEW (alembic EXTENSION) + `audit_log_archive` table NEW (archive_id UUID PK + tenant_id UUID + audit_log_id UUID + payload_snapshot JSONB + archived_at TIMESTAMPTZ + sha256_hash TEXT + previous_hash TEXT + region TEXT) + `phase_6_audit_purge_log` table NEW (purge_log_id UUID PK + tenant_id UUID + purged_at TIMESTAMPTZ + purged_count INTEGER + dry_run BOOLEAN + trace_id TEXT) + ALTER TABLE audit_log ADD COLUMN archived_at TIMESTAMPTZ + immutable append-only trigger BEFORE UPDATE/DELETE raise `AuditLogArchiveImmutableError` + SHA-256 hash chain linkage sha256_hash = SHA-256(audit_log_id + payload_snapshot + previous_hash) + `verify_archive_hash_chain(tenant_id) -> bool` function 결정 wire + cross-region archive replication Phase 5 wire `f093f8c` carry-over chain 자연스러운 정합 보존 + `archive_expired_audit_logs` AFTER DELETE trigger + audit-first INSERT `audit_log_archived` + `audit_log_cold_archived` cold-archive action 결정 wire + Epic 12 close-out retro `a63646c` NFR4 5년 audit_logs 보존 결정 wire + Epic 12-3 account deletion retention 30일 hard delete 보존 결정 wire). industry-agnostic 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4 precedent like `AUDIT_LOG_VIEW` Epic 17 wire `2ada2ec` + `MULTI_REGION_BACKUP` + `MULTI_REGION_FAILOVER` Phase 5 wire `f093f8c` + `TENANT_IDP_MANAGEMENT` Epic 16 wire + `SSO_ENTERPRISE` Epic 15 wire + `LISTEN_NOTIFY_*` Epic 13/14 wire + `AUTH_MIDDLEWARE` Phase 3 wire + `LAUNCH_*` 1st release wire + `DEPLOYMENT_*` Phase 4 wire pattern verbatim bind). AD-33 Audit Log Retention Policy 신규 (Epic 17 close-out retro `f1ead9a` (cj-style 84번째) + Epic 17 T2+T3 UI frontend atomic wire `bb92879` (cj-style 83번째) + D-EPIC-17-WIRE-DEFER-T2-T3-UI honestly RESOLVED 진입 직후 옵션 5종 중 옵션 (a) Phase 6 결정 진입 territory 신규 bind — Epic 17 T2+T3 UI frontend atomic wire `bb92879` 의 backend audit log query API 자연스러운 carry-over + Epic 12 close-out retro `a63646c` 의 NFR4 5년 audit_logs + Epic 12-3 account deletion retention 30일 hard delete 의 자연스러운 next 진입 + Phase 5 wire `f093f8c` cross-region archive carry-over chain 의 자연스러운 carry-over 결정). Phase 6 wire scope 결정 보존 T1~T8 (T1 retention DSL pure kernel + T2 automatic purge job KST cron + T3 archive storage alembic 0040 + SHA-256 hash chain + T4 GDPR/NFR4 erasure endpoint + T5 5 NEW AuditAction Literal values + T6 Capability v1.31 EXTENSION + T7 Tests + T8 3중 게이트 FINAL CLEAN atomic commit). wire_commit = TBD (cj-style Phase 6 3번째 진입점 진입 시점, expected cj-style 87번째 epic 연속 정직 회복).
>
> **v1.30 (2026-08-22, Epic 17 PRD entry)** — Audit Log Viewer & Activity Stream capability gate 1 NEW row: `AUDIT_LOG_VIEW` (`apps/api/modules/audit/audit_log_query.py` NEW ~180 LOC (4 functions: `query_audit_log(tenant_id, filters, page, page_size) -> AuditLogPage` + `count_audit_log(tenant_id, filters) -> int` + `get_audit_log_entry(tenant_id, entry_id) -> AuditLogEntry` + `query_activity_stream(tenant_id, window_days) -> list[ActivityStreamGroup]` + TypedDict 결정 + RLS 자동 적용 CR 0-2 verbatim) + `apps/api/modules/audit/audit_log_export.py` NEW ~120 LOC (`export_audit_log_csv(tenant_id, filters, actor_id) -> StreamingResponse` + Excel-compatible UTF-8 BOM `﻿` + streaming response 결정 + audit-first INSERT `audit_log_exported` CR 1-1 verbatim) + `apps/web/app/[locale]/(dashboard)/audit-log/page.tsx` NEW ~200 LOC + 5 components (`AuditLogFilterPanel` + `AuditLogTable` + `AuditLogPagination` + `AuditLogExportButton` + `AuditLogDetailModal`) + ko-KR.json `audit_log.*` namespace EXTENSION 14 keys CR 11-4 D-002 verbatim SSOT + `apps/web/app/[locale]/(dashboard)/activity/page.tsx` NEW ~150 LOC + 3 components (`ActivityStreamTimeline` + `ActivityStreamEntry` + `ActivityStreamWindowSelector`) + ko-KR.json `activity.*` namespace EXTENSION 8 keys 결정 wire + cross-region audit log visibility (Phase 5 wire `f093f8c` 의 `phase_5_replication_lag` table + Supabase multi-region primary Seoul + secondary Tokyo replica 결정 wire EXTENSION, lag_bytes ≤ 100MB + lag_seconds ≤ 30s threshold 정합, lag 초과 시 primary region fallback + Sentry breadcrumb) + Epic 12 2FA 챌린지 보존 결정 wire + AD-22 owner-only RBAC 보존 결정 wire). industry-agnostic 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4 precedent like `MULTI_REGION_BACKUP` + `MULTI_REGION_FAILOVER` Phase 5 wire + `TENANT_IDP_MANAGEMENT` Epic 16 wire + `SSO_ENTERPRISE` Epic 15 wire + `SOCIAL_OAUTH_*` + `MAGIC_LINK` + `LISTEN_NOTIFY_*` + `AI_INSIGHT` + `TWO_FACTOR_AUTH` + `AUTH_MIDDLEWARE` + `LOGIN` + `SIGNUP` + `FORGOT_PASSWORD` + `LOGOUT` + `LAUNCH_*` + `DEPLOYMENT_*`). AD-32 Audit Log Viewer & Activity Stream 신규 (Sidebar/MenuProvider hot-fix `01a06e4` (cj-style 79번째) + D-EPIC-16-REVIEW-DEFER-2~6 RESOLVE sprint `512ed6a` (cj-style 78번째) 진입 직후 옵션 5종 중 옵션 (a) Epic 17 결정 진입 territory 신규 bind — 모든 Epic 1~16 + Phase 3~5 의 audit-first INSERT CR 1-1 가 audit_log table 에 누적 → audit log viewer territory 의 natural next 진입 + Phase 5 multi-region wire 의 cross-region audit log visibility 자연스러운 carry-over). Epic 17 wire scope 결정 보존 T1~T8 (T1 audit log query API + T2 audit log viewer UI + T3 activity stream UI + T4 cross-region audit log visibility + T5 CSV export + T6 Capability v1.30 EXTENSION + T7 Tests + T8 3중 게이트 FINAL CLEAN atomic commit). wire_commit = TBD (cj-style Epic 17 3번째 진입점 진입 시점, expected cj-style 82번째 epic 연속 정직 회복).
>
> **v1.29 (2026-08-22, Phase 5 PRD entry)** — Multi-Region Backup & Disaster Recovery capability gates 2 NEW rows: `MULTI_REGION_BACKUP` (cross-region read replica + WAL archiving + alembic `0039_phase_5_multi_region_backup.py` `phase_5_replication_lag` table + replica_region enums seoul/tokyo/singapore/frankfurt/virginia/oregon/sao_paulo + `phase_5_dr_drill_results` table + audit-first INSERT `replica_status_changed` + `dr_dill_completed` 결정 wire + `docs/cross-region-replication.md` 결정 wire, Phase 5 T1+T2+T3 wire 진입) + `MULTI_REGION_FAILOVER` (cross-region failover automation + `apps/api/jobs/failover_orchestrator.py` + primary → secondary health probe 5-second interval + 3 consecutive failures trigger + automatic promotion via Supabase API + DNS update via Supabase custom domain redirect + 30s RTO target + `apps/api/jobs/dr_drill.py` cron KST 1st Sunday 03:00 UTC 18:00 + Q1/Q2/Q3/Q4 quarterly drill schedule + audit-first INSERT `failover_initiated` + `failover_completed` 결정 wire, Phase 5 T2+T3+T5 wire 진입). All 2 industry-agnostic 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4 precedent like `DEPLOYMENT_*` / `LAUNCH_*` / `SSO_ENTERPRISE` / `SOCIAL_OAUTH_*` / `MAGIC_LINK` / `LISTEN_NOTIFY_*` / `AI_INSIGHT` / `TWO_FACTOR_AUTH` / `AUTH_MIDDLEWARE` / `LOGIN` / `SIGNUP` / `FORGOT_PASSWORD` / `LOGOUT` / `TENANT_IDP_MANAGEMENT`). AD-31 Multi-Region Backup & Disaster Recovery 신규 (Phase 4 close-out retro §6 disaster recovery "multi-region backup 결정 wire 보류, Phase 5+ 진입 시점" verbatim 자연스러운 carry-over chain 결정 wire, D-PHASE-4-DR-DEFER-1/2 honestly RESOLVE 진입 wire 결정, CR 11-3 honest-DEFER discipline 73번째 epic 연속 정직 회복 검증). Phase 5 wire scope 결정 보존 T1~T8 (T1 alembic 0039 phase_5_replication_lag + phase_5_dr_drill_results tables + T2 failover_orchestrator + T3 dr_drill + T4 cross-region backup strategy docs EXTENSION + T5 multi-region health observability + T6 Capability v1.29 EXTENSION + T7 Tests + T8 3중 게이트 FINAL CLEAN atomic commit). wire_commit = `f093f8c` (cj-style Phase 5 3번째 진입점, cj-style 75번째 epic 연속 정직 회복).
>
> **v1.28 (2026-08-22, Epic 16 PRD entry)** — Tenant IdP admin management capability gate 1 NEW row: `TENANT_IDP_MANAGEMENT` (Epic 15 SSO enterprise SAML forward-reference `docs/sso-enterprise.md` §4.1 step 3 `Configure tenant_idps (TODO Epic 16)` verbatim 자연스러운 carry-over chain 결정 wire, `tenant_idps` table schema (alembic 0038, 13 columns + RLS policy CR 0-2 verbatim) + IdP metadata XML validation service 8 steps + Tenant IdP CRUD API 5 routes + Tenant IdP admin UI 4 components + per-tenant IdP routing EXTENSION Epic 15 `saml_routes.py` + ACS `idp_x509_cert` 동적 로딩 + audit-first INSERT 4 NEW 결정 + capability gate `TENANT_IDP_MANAGEMENT` per-tenant on/off 결정, Epic 16 T1~T8 wire 진입). industry-agnostic 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4 precedent like `LAUNCH_*` / `SSO_ENTERPRISE` / `SOCIAL_OAUTH_*` / `MAGIC_LINK` / `LISTEN_NOTIFY_*` / `AI_INSIGHT` / `TWO_FACTOR_AUTH` / `AUTH_MIDDLEWARE` / `LOGIN` / `SIGNUP` / `FORGOT_PASSWORD` / `LOGOUT` / `DEPLOYMENT_*`). AD-30 Tenant IdP admin management 신규 (tenant_idps table + IdP metadata validator + CRUD API + admin UI + per-tenant routing + audit-first INSERT 6 sub-decisions 결정 wire). Epic 16 wire scope 결정 보존 T1~T8 (T1 tenant_idps table + T2 IdP metadata validator + T3 Tenant IdP CRUD API + T4 admin UI + T5 per-tenant routing EXTENSION + T6 Capability v1.28 EXTENSION + T7 Tests + T8 3중 게이트 FINAL CLEAN atomic commit). wire_commit = TBD (cj-style Epic 16 3번째 진입점 진입 시점, expected cj-style 69번째 epic 연속 정직 회복).
>
> **v1.27 (2026-08-22, 1st release launch PRD entry)** — 1st release launch (Epic 15 close-out retro §12 옵션 (d) 결정 wire, A83 결정) capability gates 4 NEW rows:
>
> **v1.27 (2026-08-22, 1st release launch PRD entry)** — 1st release launch (Epic 15 close-out retro §12 옵션 (d) 결정 wire, A83 결정) capability gates 4 NEW rows:
> `LAUNCH_LANDING` (`/landing` public route + LandingHero + LandingFeatures + LandingPricing + LandingCTA + ko-KR inline copy EXTENSION, vercel.json public route EXTENSION, (public) route group 신규, 1st release T1 wire 진입) +
> `LAUNCH_TOS` (`docs/terms-of-service.md` + `docs/privacy-policy.md` 한국 PIPA + GDPR 정합 + signup flow EXTENSION `(auth)/tos` + `(auth)/privacy` 결정, 1st release T2 wire 진입) +
> `LAUNCH_SUPPORT` (`docs/support.md` + `support@bizup.kr` email + HelpWidget + FAQ `docs/faq.md`, 1st release T4 wire 진입) +
> `LAUNCH_MONITORING` (smoke test RE-RUN 정직 결정 + backup drill 0036 PITR quarterly + Sentry alert wiring production + RPO 4h/RTO 24h SLA verification, 1st release T5 wire 진입). All 4 industry-agnostic 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4 precedent like `LISTEN_NOTIFY` / `AI_INSIGHT` / `TWO_FACTOR_AUTH` / `LISTEN_NOTIFY_TENANT_FANOUT` / `LISTEN_NOTIFY_MULTIPROCESS` / `LOGIN` / `SIGNUP` / `AUTH_MIDDLEWARE` / `FORGOT_PASSWORD` / `LOGOUT` / `DEPLOYMENT_PROD` / `DEPLOYMENT_STAGING` / `DEPLOYMENT_DATABASE_BACKUP` / `DEPLOYMENT_HEALTH_CHECK` / `MAGIC_LINK` / `SOCIAL_OAUTH_GOOGLE` / `SOCIAL_OAUTH_NAVER` / `SOCIAL_OAUTH_KAKAO` / `SSO_ENTERPRISE`). AD-29 1st release launch 신규 (Marketing landing + ToS/Privacy + Onboarding + Support + Verification + Comms 6 sub-decisions 결정 wire). 1st release wire scope 결정 보존 T1~T8 (T1 Landing page + T2 ToS/Privacy + T3 Onboarding guide + T4 Support channels + T5 Production verification + T6 Capability v1.27 EXTENSION + T7 Tests + T8 Launch comms + 3중 게이트 FINAL CLEAN atomic commit). wire_commit = TBD (cj-style 1st release 3번째 진입점 진입 시점, expected cj-style 64번째 epic 연속 정직 회복).
>
> **v1.26 (2026-08-22, Epic 15 PRD entry)** — Magic link + Social OAuth
> (Google/Naver/Kakao) + SSO enterprise SAML capability gates 5 NEW rows:
> `MAGIC_LINK` (Supabase `signInWithOtp` + 5회 cool-down + email 존재 여부
> 노출 방지 + audit-first INSERT `magic_link_sent`, Epic 15 T1+T2 wire 진입) +
> `SOCIAL_OAUTH_GOOGLE` (Supabase `signInWithOAuth` + provider whitelist +
> 3회 cool-down + audit-first INSERT `social_oauth_initiated`, Epic 15 T3+T4
> wire 진입) +
> `SOCIAL_OAUTH_NAVER` (Supabase `signInWithOAuth` Option A 우선 / Option B
> custom Naver OAuth flow 결정 wire 보존, Epic 15 T3+T4 wire 진입) +
> `SOCIAL_OAUTH_KAKAO` (Supabase `signInWithOAuth` + provider whitelist +
> 3회 cool-down, Epic 15 T3+T4 wire 진입) +
> `SSO_ENTERPRISE` (`python3-saml==1.16.0` AD-14 stack pin + SAML response
> validation + JIT user provisioning + multi-tenant isolation RLS +
> audit-first INSERT `sso_identity_linked`, Epic 15 T5+T6 wire 진입). All 5
> industry-agnostic 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4 precedent like
> `LISTEN_NOTIFY` / `AI_INSIGHT` / `TWO_FACTOR_AUTH` /
> `LISTEN_NOTIFY_TENANT_FANOUT` / `LISTEN_NOTIFY_MULTIPROCESS` / `LOGIN` /
> `SIGNUP` / `AUTH_MIDDLEWARE` / `FORGOT_PASSWORD` / `LOGOUT` /
> `DEPLOYMENT_PROD` / `DEPLOYMENT_STAGING` / `DEPLOYMENT_DATABASE_BACKUP` /
> `DEPLOYMENT_HEALTH_CHECK`). AD-28 Magic link + Social OAuth + SSO enterprise
> SAML 신규 (Supabase `signInWithOtp` + `signInWithOAuth` +
> `python3-saml==1.16.0` AD-14 stack pin + JIT user provisioning +
> multi-tenant isolation CR 0-2 RLS lesson + audit-first INSERT 3 NEW 결정
> wire). D-1-1-DEFER-1/2/3 honestly ✅ RESOLVED 58번째 epic 연속 정직 회복
> (CR 11-3 discipline). Epic 15 wire scope 결정 보존 T1~T8 (T1 Magic link
> wrapper + T2 Magic link UI + T3 Social OAuth wrapper + T4 OAuth callback
> + T5 SSO SAML backend + T6 SSO UI + T7 capability v1.26 EXTENSION + T8
> tests + 3중 게이트 FINAL CLEAN atomic commit). wire_commit = TBD
> (cj-style Epic 15 3번째 진입점 진입 시점, expected cj-style 60번째 epic 연속
> 정직 회복).
>
> **v1.25 (2026-08-22, Phase 4 PRD entry)** — Deployment config + Dockerfile +
> health check + observability + database backup capability gates 4 NEW rows:
> `DEPLOYMENT_PROD` (Vercel frontend production deployment + Railway backend
> production deployment, Phase 4 T1+T2 wire 진입) +
> `DEPLOYMENT_STAGING` (Vercel frontend staging deployment + Railway backend
> staging deployment, Phase 4 T1+T2 wire 진입) +
> `DEPLOYMENT_DATABASE_BACKUP` (Supabase PostgreSQL PITR 7일 자동 backup +
> phase_4_backup_strategy table, Phase 4 T6 wire 진입) +
> `DEPLOYMENT_HEALTH_CHECK` (`GET /api/v1/health` + `GET /api/health` +
> Sentry observability, Phase 4 T5 wire 진입). All 4 industry-agnostic
> 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4 precedent like `LISTEN_NOTIFY` /
> `AI_INSIGHT` / `TWO_FACTOR_AUTH` / `LISTEN_NOTIFY_TENANT_FANOUT` /
> `LISTEN_NOTIFY_MULTIPROCESS` / `LOGIN` / `SIGNUP` / `AUTH_MIDDLEWARE` /
> `FORGOT_PASSWORD` / `LOGOUT`). AD-27 Deployment 신규 (Vercel frontend +
> Railway backend + Supabase PostgreSQL production + Sentry observability
> 결정 wire). Phase 4 wire scope 결정 보존 T1~T8 (T1 Vercel config + T2
> Railway config + T3 per-app Dockerfile + T4 deployment runbook + T5 health
> check + observability + T6 database backup strategy + T7 capability v1.25
> EXTENSION + T8 tests + 3중 게이트 FINAL CLEAN atomic commit). wire_commit = TBD
> (cj-style Phase 4 3번째 진입점 진입 시점, expected cj-style 55번째 epic 연속 정직 회복).
>
> **v1.24 (2026-08-20, Phase 3 PRD entry)** — Auth Foundation capability gates
> 5 NEW rows: `LOGIN` (이메일·비밀번호 로그인, Phase 3 T2 wire 진입) +
> `SIGNUP` (회원가입 + tenant 생성 flow, Phase 3 T3 wire 진입) +
> `AUTH_MIDDLEWARE` (Supabase session check + (dashboard) 보호, Phase 3 T4 wire 진입) +
> `FORGOT_PASSWORD` (Supabase resetPasswordForEmail + reset-password, Phase 3 T6 wire 진입) +
> `LOGOUT` (signOut + audit-first INSERT, Phase 3 T5 wire 진입). All 5
> industry-agnostic 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4 precedent like
> `LISTEN_NOTIFY` / `AI_INSIGHT` / `TWO_FACTOR_AUTH` /
> `LISTEN_NOTIFY_TENANT_FANOUT` / `LISTEN_NOTIFY_MULTIPROCESS`). AD-26 Auth
> Foundation 신규 (Supabase SSR + sb-access-token cookie session + next-intl
> middleware EXTENSION + auth route group (auth) 공개 + dashboard route group
> (dashboard) 보호 + Epic 12 2FA 게이트 보존). Phase 3 wire scope 결정 보존
> T1~T8 (T1 Supabase SSR client + T2 login page + T3 signup page + T4 auth
> middleware EXTENSION + T5 logout + T6 forgot-password + T7 capability v1.24
> EXTENSION + T8 tests + 3중 게이트 FINAL CLEAN atomic commit). wire_commit = TBD
> (cj-style Phase 3 3번째 진입점 진입 시점, expected cj-style 51번째 epic 연속 정직 회복).
>
> **v1.23 (2026-08-20, Story 14.1, Epic 14)** — LISTEN/NOTIFY Consume 2nd Batch
> EXTENSION capability gates 2 NEW rows: `LISTEN_NOTIFY_TENANT_FANOUT`
> (cross-tenant invalidation fan-out, 14-1 wire) + `LISTEN_NOTIFY_MULTIPROCESS`
> (leader/follower multi-process coordination, 14-1 wire). Both industry-agnostic
> 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4 precedent like `LISTEN_NOTIFY` /
> `AI_INSIGHT` / `TWO_FACTOR_AUTH`). AD-25 cache invalidation trigger EXTENSION
> 4-channel → 5+ channels (cross_tenant_fanout channel 추가). 14-1 wire = atomic
> single sprint T1~T9 (alembic 0034 + listener EXTENSION + main.py lifespan +
> adapter EXTENSION + capability v1.22 → v1.23 EXTENSION + V8 determinism +
> cross-language drift EXTENSION + multi-process coordination tests +
> cross-tenant fan-out e2e). wire_commit = `7835463`.
>
> **v1.22 (2026-08-20, Story 13.1, Epic 13)** — LISTEN/NOTIFY Consume Trigger
> EXTENSION capability gate 1 NEW row: `LISTEN_NOTIFY` (industry-agnostic,
> 4-industry grants ✅/✅/✅/✅). CR 12-5 D-GATE-01 inversion: capability gate
> enforced through `Depends(require_capability(Capability.LISTEN_NOTIFY))`.
> AD-25 cache invalidation trigger 3-channel → 4-channel (cache_invalidation_log
> + pg_notify listener). 13-1 wire = atomic single sprint T1~T8 (alembic 0033 +
> listener EXTENSION + main.py lifespan EXTENSION + adapter EXTENSION +
> capability v1.21 → v1.22 + V8 determinism + cross-language drift EXTENSION
> + LISTEN/NOTIFY consume tests). wire_commit = `f2ea2f6`.
>
> **v1.21 (2026-08-17, Epic 10 PRD entry)** — `AI_INSIGHT` capability 1 NEW
> (industry-agnostic, 4-industry grants ✅/✅/✅/✅ — CR 12-1 L4 precedent like
> `TWO_FACTOR_AUTH` / `BACKUP_EXPORT` / `BUDGET_SCENARIO`). Epic 10 4 stories
> (10-1 AI Document Extraction + 10-2 Three-Insight Cache + 10-3 Reference vs
> Auto Badge + 10-4 Promotion Port) bind to single `AI_INSIGHT` row. AD-7
> (AI non-authoritative) + AD-17 (promotion port idempotency) + AD-25 (cache
> invalidation) bind. 본 PRD entry는 **docs-only** (Epic 10 PRD 진입, capability
> matrix v1.20 → v1.21 wire); Epic 10 wire 진입 시점에 `AI_INSIGHT` 실제 grant
> + 4 NEW endpoints (`POST /api/v1/ai/extract` 10-1 + `GET /api/v1/ai/insights`
> 10-2 + `GET /api/v1/ai/comments source_kind discriminator` 10-3 +
> `POST /api/v1/ai/promote` 10-4) + drift detector test 별도 atomic wire.
>
> **v1.20 (2026-08-17, Story 9.4, Epic 9)** — A30 forward-lock dual-report PDF
> generator 결정 wire (PRD §9 #21 + §7.3 + §9 공통 + §A6+A9+V7+V8). Story 9.4
> wired the M5 reports extension for Report #21 (원가대상별 원가 집계표):
> - **No NEW capability** — uses existing `COST_CALCULATION` (mfg-only) +
>   `ABC_CALCULATION` (industry-agnostic, 9.1/9.2/9.3 wire). The capability
>   dual-route gate reuses `require_any_capability(COST_CALCULATION,
>   ABC_CALCULATION)` — ANY-OF semantics (CR 12-5 D-14 envelope handler
>   pattern + CR 12-1 L4 variadic helper precedent).
> - **M5 owns ONLY Report #21 endpoint** (AD-18) — `GET /api/v1/reports/21`
>   + `POST /api/v1/reports/21/pdf` dispatch via M5 reports service
>   `Report21Service.build_report21` + `generate_report21_pdf`.
> - **A30 SHARED PDF generator** — `packages/services/m5_reports/pdf_generator.py`
>   factory pattern (Discriminated union
>   `report_id: Literal[15, 16, 17, 18, 19, 20, 21]`):
>   - Report #21 (본 story) — `_compose_report21_pdf` stdlib-only PDF byte
>     composition (Type0 CIDFont + Identity-H CMap pattern, matching Story
>     6-3 `closing_pdf_export` 3rd sweep B1 precedent)
>   - Report #15 (활동원가 내역서, 후속) — `_compose_report15_pdf` placeholder
>     (A31+ forward-lock 결정)
> - **Capability matrix 변경 0** — capability 행 자체는 변경 없음 (Report #21
>   endpoint uses existing dual-route gate, A30 SHARED factory just delegates
>   via Discriminated union). Drift detector:
>   `tests/integration/test_capability_matrix_v1_20_drift.py` pins:
>   - `ABC_CALCULATION` industry-agnostic preservation (4-industry grants)
>   - `COST_CALCULATION` mfg-only preservation (3-industry grants + service-only ❌)
>   - `require_any_capability` factory dual-route gate preserved
>   - 4 NEW typed exceptions (`Report21PeriodNotCommittedError` +
>     `Report21NoBreakdownError` + `Report21BreakdownNotFoundError` +
>     `Report21PdfGenerationError`) mapped to AD-15 §4 envelopes in
>     `apps/api/main.py` (CR 12-5 D-14)
>   - A30 SHARED factory Discriminated union integrity
>     (`report_id: Literal[15, 16, 17, 18, 19, 20, 21]`)
>   - 4 envelope codes (`REPORT21_PERIOD_NOT_COMMITTED` 422 +
>     `REPORT21_NO_COST_OBJECT_BREAKDOWN` 422 +
>     `REPORT21_BREAKDOWN_NOT_FOUND` 404 +
>     `REPORT_PDF_GENERATION_ERROR` 500) wire integrity.
>
> ---
>
> **v1.19 (2026-08-16, Story 9.3, Epic 9)** — dual-route gate on `/api/v1/calc`
> ABC dispatch via M3 orchestrator (PRD §F9.3 + A29 forward-lock dual-route
> + AD-19 dual-route dispatch). Story 9.3 wired:
> - **No NEW capability** — uses existing `COST_CALCULATION` (mfg-only) +
>   `ABC_CALCULATION` (industry-agnostic, 9.1 wire). The dual-route gate
>   uses `require_any_capability(COST_CALCULATION, ABC_CALCULATION)` —
>   ANY-OF semantics (CR 12-5 D-14 envelope handler pattern + CR 6-2 V4
>   3-source contract: enum ↔ docs ↔ grants).
> - **M3 owns ONLY the public endpoint** (AD-18) — `POST /api/v1/calc`
>   dispatches via M3 orchestrator's `_resolve_engine_type(industry)`:
>   - `tenant.industry == 'service'` → M9 ABC path (`AbcAllocationService.compute_and_persist`)
>   - else → M3 traditional path (PRD §F0.2 3종 allocation)
> - **Discriminated union response** — `CalcResponse | CalcAbcResponse` with
>   `engine_type: Literal["trad", "abc"]` tag discriminator (Pydantic v2 + FastAPI).
>   `CalcAbcResponse` carries `allocation_outcome` (breakdown + unused + V7
>   verdict + CCR), `snapshot_id`, `result_hash`, `state="verified"`.
> - **Alembic 0028** (`apps/api/alembic/versions/0028_abc_fiscal_period_breakdown.py`)
>   adds 2 JSONB columns to `fiscal_period_snapshots`:
>   - `cost_object_breakdown JSONB` + GIN index `jsonb_path_ops` (PRD §F9.3 + §A6)
>   - `unused_capacity_breakdown JSONB` + GIN index `jsonb_path_ops` (PRD §A9 + §V7)
>   - 2 NEW COMMENT ON COLUMN documentation (NFR18 lock)
>   - down_revision = '0027_budget_pre_standard' (8-3 wire tip)
> - **2 NEW typed exceptions** mapped to AD-15 §4 envelopes in `apps/api/main.py`
>   (CR 12-5 D-14):
>   - `EmptyDepartmentsError` → 422 ABC_EMPTY_DEPARTMENTS
>   - `TooManyDepartmentsError` → 422 ABC_TOO_MANY_DEPARTMENTS (1-50 guard)
> - **AD-22 ledger append-only** — `calc_log` + `verification_log` BEFORE
>   `fiscal_period_snapshots` INSERT (audit-first INSERT order).
> - **Alembic/RLS SKIPPED for `fiscal_period_snapshots` policy changes** —
>   existing RLS 0001 covers INSERT (A28 forward-lock, NO policy delta).
> Drift detector: extend `tests/integration/test_capability_matrix_v1_18_drift.py`
> with v1.19 row fill change (`ABC_CALCULATION` stories → "9.1, 9.2, 9.3").
>
> ---
>
> **v1.18 (2026-08-16, Story 9.1, Epic 9)** — `ABC_CALCULATION`
> ABC / TDABC engine 100% validation guard wire (PRD §F9.1 verbatim —
> "원가풀 행 합·활동 열 합·동인 합 모두 100% 가드"). Story 9.1 wired
> the pure kernel `abc_engine.py` (A19 cohesion pattern 6번째 surface —
> 4 NEW functions + 3 frozen dataclasses + 4 typed exceptions + 7 constants,
> AD-5 stdlib-only) + service layer `AbcValidationService` +
> 4 NEW routes under `/api/v1/abc/*`:
> - POST /api/v1/abc/cost-pools        — 원가풀 행 합 100% 가드
> - POST /api/v1/abc/activities        — 활동 열 합 100% 가드
> - POST /api/v1/abc/drivers/validate  — 동인 합 100% 가드 (1.2 POST /drivers 와 별도)
> - POST /api/v1/abc/validate          — 3-layer 100% 가드 동시 검증 (main entry point)
>
> 4 NEW typed exceptions are mapped to AD-15 §4 envelopes in
> `apps/api/main.py` (CR 12-5 D-14): `CostPoolValidationError` → 422
> COST_POOL_INVALID_SUM / `ActivityValidationError` → 422 ACTIVITY_INVALID_SUM
> / `DriverValidationError` → 422 DRIVER_INVALID_SUM /
> `AbcValidationNotFoundError` → 404 ABC_VALIDATION_NOT_FOUND.
> Alembic/RLS SKIPPED (9-1 = validation only, no INSERT/UPDATE/DELETE —
> CR 1.1 read-mostly invariant; A5 forward-lock 변경 0).
> `ABC_CALCULATION` is **industry-agnostic** (granted to ALL 4 canonical
> industries) — ABC is operational baseline infrastructure (CR 12-1 L4
> precedent — manufacturing 3종 ✅ + service-only ✅). Drift detector:
> `tests/integration/test_capability_matrix_v1_18_drift.py` pins enum ↔
> docs ↔ 4-industry grants for ABC_CALCULATION.
>
> ---
>
> **v1.17 (2026-08-15, Story 8.1, Epic 8)** — `BUDGET_SCENARIO`
> AD-24 §6.3 virtual budget period key + 1차 시나리오 1개 잠금
> (PRD §F8.1 + §15 NON-GOAL #2). Story 8.1 wired the pure kernel
> `budget_period_key.py` (4 NEW functions + 3 frozen dataclasses +
> 2 typed exceptions) + service layer `BudgetScenarioService` +
> audit ActionClass `BUDGET_SCENARIO` (CR 11-3 honest-DEFER for
> audit emit — 8-1 is read-mostly with scenario creation only, no
> audit emit per CR 1.1 invariant — A5 forward-lock 변경 0) +
> 3 NEW routes under `/api/v1/budget/scenarios/*`:
> - POST /api/v1/budget/scenarios            — owner+member create
> - GET  /api/v1/budget/scenarios            — 4-role list (owner+member+viewer+consultant_proxy)
> - GET  /api/v1/budget/scenarios/{period_key} — 4-role detail by virtual period_key
>
> 3 NEW typed exceptions are mapped to AD-15 §4 envelopes in `apps/api/main.py`
> (CR 12-5 D-14): ScenarioLimitExceededError → 409 / InvalidVirtualBudgetPeriodKeyError → 422
> / BudgetScenarioNotFoundError → 404. Alembic 0026 adds `budget_scenarios`
> table (8 columns + 2 UNIQUE + 3 CHECK + 1 index) + RLS policy 0016
> (4-policy split per AD-3 same-tenant + AD-2 INSERT-only soft invariant).
> BUDGET_SCENARIO is **industry-agnostic** (granted to ALL 4 canonical industries) —
> budget planning is operational baseline (CR 12-1 L4 precedent — manufacturing 3종 ✅
> + service-only ✅).
>
> ---
>
> **v1.17 (2026-08-15, Story 7.1, Epic 7)** — `CVP_SIMULATION`
> CVP/BEP slider simulation wire (PRD §F7.1 + §F7.2). 9 NEW pure functions +
> 7 NEW frozen dataclasses + 4 NEW typed exceptions + 1 NEW capability
> (industry-agnostic, CR 12-1 L4 + 7-1/7-2 precedent — all 4 industries
> grant). 2 NEW math surfaces: `cvp.py` + `projection.py` (A19
> cohesion pattern — split per concern).
>
> ---
>
> **v1.15 (2026-08-15, Story 12.3, Epic 12)** — `ACCOUNT_DELETION`

> **Single source of truth** for the `Industry × Capability` gating that
> Epic 1 / 2 / 3 / 4 / 11 / 12 stories need to coordinate. Replaces the per-story
> capability tables with one consolidated matrix.
>
> **v1.15 (2026-08-15, Story 12.3, Epic 12)** — `ACCOUNT_DELETION`
> Account deletion + retention consent wire (PRD §F12.3 + NFR4 2절 5년 audit 보존
> + 30일 hard delete retention + NFR7 2FA 강제 on destructive endpoint +
> AD-2 INSERT-only invariant on `deletion_consents`). Story 12.3 wired the
> pure kernel `account_deletion.py` + service layer `DeletionService` +
> audit ActionClass `ACCOUNT_DELETION` (8 typed values: `deletion_requested`
> + `deletion_consent_given` + `deletion_cancelled` + `deletion_anonymized`
> + `tenant_hard_deleted` + `deletion_failed` + `deletion_2fa_failed`
> + `two_factor_verified`) + 4 NEW routes under `/api/v1/account/deletion/*`:
> - POST /api/v1/account/deletion/challenge-token — TOTP-gated JWT mint
> - POST /api/v1/account/deletion/request          — destructive (3-layer TOTP defense)
> - POST /api/v1/account/deletion/cancel           — owner cancel pending_deletion
> - GET  /api/v1/account/deletion/status           — read-only FSM snapshot
>
> 6 NEW typed exceptions are mapped to AD-15 §4 envelopes in `apps/api/main.py`.
> Alembic 0025 adds `tenants.status` FSM (active|pending_deletion|deleted) +
> `deletion_consents` table + RLS policy 0015 (4-policy split per AD-2
> INSERT-only invariant). ACCOUNT_DELETION is **industry-agnostic**
> (granted to ALL 4 canonical industries) — deletion is operational
> infrastructure (data subject right / GDPR Art.17), not industry-specific.
> Capability gate enforced ONLY on `request_deletion` (destructive endpoint
> — CR 12-5 L3 3-layer defense target); other routes gate ONLY on
> `require_role("owner")` per AD-10.
>
> **v1.14 (2026-08-12, Story 12.2, Epic 12)** — `BACKUP_EXPORT`
> Daily auto-backup + JSON self-download wire (PRD §F12.2 + §M12-b + NFR4).
> Story 12.2 wired the pure kernel + service layer + audit ActionClass
> `ACCOUNT_BACKUP` (5 typed values: `backup_created` + `backup_failed` +
> `backup_retention_purged` + `backup_downloaded` + `backup_triggered`) +
> 3 NEW routes under `/api/v1/account/backups/*`:
> - GET  /api/v1/account/backups/recent              — list 7-day backups
> - GET  /api/v1/account/backups/{backup_id}/download — JSON download
> - POST /api/v1/account/backups/trigger              — manual owner trigger
>
> 5 typed exceptions are mapped to AD-15 §4 envelopes in `apps/api/main.py`.
> Alembic 0024 adds `tenant_backups` table + RLS policy 0014 (5-policy split
> per AD-3). BACKUP_EXPORT is **industry-agnostic** (granted to ALL 4
> canonical industries) — backup is operational infrastructure, not a
> manufacturing feature. AD-10 owner-only gate enforced at route via
> `require_role("owner")` (not via `require_capability`) per CR 12-1 L4
> precedent — capability is documented but NOT enforced.
> Drift detector: `tests/integration/test_capability_matrix_v1_14_drift.py`
> pins enum ↔ docs ↔ 4-industry grants for BACKUP_EXPORT.
>
> **v1.13 (2026-08-10, Story 12.1 + 12.4, Epic 12)** — `TWO_FACTOR_AUTH`
> 2FA mandatory gate wire (PRD §F12.1 + §M12-a + NFR5 TLS + NFR6 AES-256-GCM).
> Story 12.1 wired the pure kernel + service layer + audit ActionClass
> `TWO_FACTOR_AUTH` (6 typed values). Story 12.4 (carry-over sprint)
> wired 8 routes + 1 M2 entry-gate route under `/api/v1/account/2fa/*`
> + `/api/v1/m2-entry-gate`:
> - POST /api/v1/account/2fa/setup
> - POST /api/v1/account/2fa/verify
> - POST /api/v1/account/2fa/challenge
> - POST /api/v1/account/2fa/recovery
> - POST /api/v1/account/2fa/disable (owner-only mutation)
> - GET  /api/v1/account/2fa/status
> - POST /api/v1/account/2fa/challenge-tokens
> - POST /api/v1/account/2fa/challenge-tokens/consume
> - GET  /api/v1/m2-entry-gate
>
> 14 typed exceptions are mapped to AD-15 §4 envelopes in `apps/api/main.py`.
> Alembic 0022 adds 5 `users.totp_*` columns + RLS policy 0013. 2FA is
> **industry-agnostic** (granted to ALL 4 canonical industries) — 2FA is
> a security baseline, not a manufacturing feature. AD-10 4-role allowlist
> (owner / member allowed; viewer / consultant_proxy denied) enforced at
> route via `require_role("owner")` (not via `require_capability`).
> Drift detector: `tests/integration/test_audit_logs_no_action_check_constraint.py`
> pins the "audit_logs has no CHECK" invariant for TWO_FACTOR_AUTH (the
> audit_logs table is intentionally CHECK-less per A5 design).
>
> **v1.12 (2026-08-09, Story 11.3, Epic 11)** — 3 NEW capabilities added
> for AD-20 snapshot persistence + AD-22 reversal 영구화 + W2 reopen flow:
> `SNAPSHOT_PERSISTENCE` (POST /close/snapshots/commit + GET /close/snapshots/{period_key}),
> `REVERSAL_EXECUTE` (POST /close/snapshots/reverse — distinct from
> REVERSAL_REQUEST which gates AD-22 reversal REQUEST 11-1 wire),
> `REOPEN_OPERATOR` (POST /close/sequence/reopen — W2 owner-only operator
> reopen with operator_action 4-value enum). All 3 granted to
> manufacturing-kind 3종 (manufacturing / manufacturing_service /
> manufacturing_service_other); service-only ❌ (403 INDUSTRY_NOT_SUPPORTED).
> AD-25 4-channel publisher wire (`ai_cache` + `cost_engine_cache` +
> `fiscal_period_cache` + `closing_snapshot_cache`) is industry-agnostic
> (no capability gate — it's a cross-cutting infra notification).
>
> **v1.11 (2026-08-08, Story 11.2, Epic 11)** — `CLOSE_SEQUENCE_LOCK`
> capability wire (PRD §F11.1 + §8.M11(a)) for the 4-stage close sequence
> (divisions → manufacturing → abc → common) + partial-close guard
> (PARTIAL_CLOSE_BLOCKED) + ALREADY_CONFIRMED (fiscal_periods.status=
> 'closed'). Granted to manufacturing-kind 3종; service-only ❌.
>
> **v1.10 (2026-08-08, Story 11.1, Epic 11)** — `REVERSAL_REQUEST`
> capability wire (PRD §F11.3) for AD-22 reversal sequence (sign-negating
> + corrected row) + AD-25 1-channel publisher (`ai_cache` only). Granted
> to manufacturing-kind 3종; service-only ❌ (no inventory ledger to reverse).
> POST /close/reversal-requests + GET /close/reversal-requests/{correction_group_id}
> + POST /close/cache-invalidation 3 NEW routes registered.
>
> **v1.6 (2026-08-04, Story 5.2)** — `Capability.INVENTORY_LEDGER` row
> confirmed wired for manufacturing-kind 3종 (manufacturing /
> manufacturing_service / manufacturing_service_other); service-only
> ❌ (403 INDUSTRY_NOT_SUPPORTED). 4 HTTP routes registered
> (POST /events, GET /period-closing, GET /carry-chain,
> POST /reversal-requests). Drift protection:
> `tests/integration/test_inventory_ledger_capability.py` (T9.2).
>
> **v1.5 (2026-08-03, Story 5.1)** — `Capability.OPENING_INVENTORY` row
> confirmed (already wired since Story 3.3 baseline; 5-1 explicit pin).
> Service industry is auto no-op (carry chain returns empty decisions).
>
> **v1.4 (2026-08-02, Story 4.4)** — V8 골든 byte-identical 회귀 매트릭스
> (4 industries × 3 baseline shapes = 12 fixtures) 가 CI mandatory gate 로
> 추가됨. Industry canonical names parity 정렬 (manufacturing_service /
> manufacturing_service_other). `verification_log.action` 에
> `verify_v8_golden_match` audit action 추가 (A5 forward-lock). Capability
> 행 자체는 변경 없음 — V8 은 COST_CALCULATION 응답 envelope 내부 검증
> 으로 wire 됨.
>
> **v1.3 (2026-08-03, Story 4.3)** — verification envelope (V1·V4·V7·V8)
> exposed via `CalcResponse.verdict`. `COST_CALCULATION` capability
> unchanged (no new row); the verdict envelope is wired INTO the existing
> calc response. AD-12 ordering invariant + per-industry V7 firing matrix
> codified (see `docs/conventions.md §0.5` + `docs/cost-engine.md
> #verification-envelope-v1v4v7v8`).
>
> **v1.2 (2026-08-02, Story 4.2)** — POST /api/v1/calc endpoint wired
> behind `COST_CALCULATION` capability; service tenants return 403
> INDUSTRY_NOT_SUPPORTED (Epic 9 ABC is their path).
>
> **v1.9 (2026-08-08, Story 6.2, Epic 6)** — `MONTHLY_CLOSING_REPORT` capability 6-1 wire (월 마감 보고서 read-only join — closing snapshot × ledger events 2-source aggregate, D1 결정 2026-08-08 fiscal_period_snapshots 가 V4 contract source 에서 제외 — PRD §6.1 산식 체인이 manufacturing_cost KRW 임을 명시) extends with **closing report view modes** (READY / PARTIAL / EMPTY 3-state classifier) + **V4 closing-period consistency verification** (3-source extension: ledger + closing snapshot + product whitelist, D1 결정) + **KRW/USD dual display** (PRD §F5.2 — 한국은행 USD/KRW 매매기준율 banker's rounding parity) + 3 NEW routes (`GET /monthly-closing-report` + `GET /monthly-closing-report/audit-trail` + `GET /monthly-closing-report/v4-verdict`) + `ActionClass.MONTHLY_CLOSING_REPORT` 6-2 deferred V4 골든 fixture fill (6-1 T10.5 carry-over close — `v4_closing_period_pass_manufacturing.json` + `v4_closing_period_fail_manufacturing.json` 2 NEW V8 골든 fixtures) + V8 골든 fixture count 16 → 18 (12 V8 baseline + 2 V3 + 4 V4/A11 6-2). Capability 행 자체는 변경 없음 — `MONTHLY_CLOSING_REPORT` capability 6-1 에서 wire done. View mode + V4 verdict 는 response envelope 내부 surface.
>
> **v1.1 (2026-08-02, Story 4.1)** — added `COST_CALCULATION` row.

## Wire contract: `POST /api/v1/calc` response envelope (Story 4.3)

`COST_CALCULATION` 통과 시 응답 envelope:

```python
class CalcResponse(BaseModel):
    # ... 기존 fields (tenant_id, period_key, 4 KRW + result_hash + state + baseline_revision + trace_id)
    state: Literal["verified"] = "verified"   # AD-20 transition: draft → verified via V1·V4·V7·V8 passed
    verdict: Verdict                            # NEW (Story 4.3) — verification envelope
```

**State machine (AD-20 invariant)** — `state ∈ Literal["draft", "verified", "committed", "reversed"]`. 본 스토리 범위는 `verified` 도달까지. `committed` / `reversed` 전이는 Epic 11 M11 owner.

**Verdict envelope wire shape** — `verification_status ∈ Literal["passed", "failed"]` (AD-20 외부 노출 invariant — `'pending'` 부재). 200 OK envelope에 포함되며, 실패 시 ROLLBACK + 200 OK + verdict envelope (NOT 4xx — 계산 자체는 성공, lock만 service layer 책임).

**Per-industry V* firing matrix (AD-12 spec interpretation)** — `manufacturing` / `manufacturing_service` / `manufacturing_service_other` 3 industry는 V1·V4·V8 발동 + V7 silent skip (3 rules). `service` industry는 V1·V4·V7·V8 모두 발동 (4 rules). Epic 9 9-1 wire 후 V7 ABC 무결성 검증 활성화.

**Story 4.4 V8 골든 회귀 매트릭스** — `tests/regression_v8/test_regression_v8_fixtures.py` (28+ cases, `@pytest.mark.v8_regression` — mandatory, no skip). 4 industries × 3 baseline shapes (b-small / b-standard / b-complex) = 12 골든 JSON. `verify_v8_golden_match` audit action (Story 4.4 forward-lock) — V8 fail 시 `verification_log.action = 'verify_v8_golden_match'` 으로 INSERT (CR 1.1 audit-first).

## Industries (PRD §4.1 4지선다)

| Industry | Description |
|---|---|
| `manufacturing` | ① 제조업 — 전통 개별원가 엔진 |
| `service` | ② 서비스업 — ABC 엔진 |
| `manufacturing_service` | ③ 제조+서비스 (겸영) |
| `manufacturing_service_other` | ④ 제조+서비스+기타 |

## Capabilities (Story 1.1 §AC #2, Epic 2 회고 A3, Epic 1 회고 A4)

| Capability | Story | manufacturing | service | manufacturing_service | manufacturing_service_other |
|---|---|---|---|---|---|
| `BOM` | 2.2 | ✅ | ❌ | ✅ | ✅ |
| `OPENING_INVENTORY` | 5.1 | ✅ | ❌ | ✅ | ✅ |
| `INVENTORY_LEDGER` | 5.2 | ✅ | ❌ | ✅ | ✅ |
| `INVENTORY_CLOSING_GUARD` | 5.3 | ✅ | ❌ | ✅ | ✅ |
| `MONTHLY_CLOSING_REPORT` | 6.1 | ✅ | ❌ | ✅ | ✅ |
| `COST_POOL` | 9.x | ❌ | ✅ | ✅ | ✅ |
| `ACTIVITY` | 9.x | ❌ | ✅ | ✅ | ✅ |
| `DRIVER` | 9.x | ❌ | ✅ | ✅ | ✅ |
| `SEGMENT_SPLIT` | 9.x | ❌ | ❌ | ✅ | ✅ |
| `AI_EXTRACT` | 1.3 | ✅ | ✅ | ✅ | ✅ |
| `AI_INSIGHT` | 10.1, 10.2, 10.3, 10.4 | ✅ | ✅ | ✅ | ✅ |
| `PRODUCT` | 2.1 | ✅ | ✅ | ✅ | ✅ |
| `PRODUCT_MATERIAL` | 2.1 | ✅ | ❌ | ✅ | ✅ |
| `MONTHLY_INPUT_PRODUCTION` | 3.1 | ✅ | ❌ | ✅ | ✅ |
| `COST_CALCULATION` | 4.1 | ✅ | ❌ | ✅ | ✅ |
| `REVERSAL_REQUEST` | 11.1 | ✅ | ❌ | ✅ | ✅ |
| `CLOSE_SEQUENCE_LOCK` | 11.2 | ✅ | ❌ | ✅ | ✅ |
| `SNAPSHOT_PERSISTENCE` | 11.3 | ✅ | ❌ | ✅ | ✅ |
| `REVERSAL_EXECUTE` | 11.3 | ✅ | ❌ | ✅ | ✅ |
| `REOPEN_OPERATOR` | 11.3 | ✅ | ❌ | ✅ | ✅ |
| `TWO_FACTOR_AUTH` | 12.1 | ✅ | ✅ | ✅ | ✅ |
| `BACKUP_EXPORT` | 12.2 | ✅ | ✅ | ✅ | ✅ |
| `ACCOUNT_DELETION` | 12.3 | ✅ | ✅ | ✅ | ✅ |
| `BUDGET_SCENARIO` | 8.1 | ✅ | ✅ | ✅ | ✅ |
| `CVP_SIMULATION` | 7.1 | ✅ | ✅ | ✅ | ✅ |
| `ABC_CALCULATION` | 9.1, 9.2, 9.3 | ✅ | ✅ | ✅ | ✅ |
| `LISTEN_NOTIFY` | 13.1 | ✅ | ✅ | ✅ | ✅ |
| `LISTEN_NOTIFY_TENANT_FANOUT` | 14.1 | ✅ | ✅ | ✅ | ✅ |
| `LISTEN_NOTIFY_MULTIPROCESS` | 14.1 | ✅ | ✅ | ✅ | ✅ |
| `LOGIN` | Phase 3 | ✅ | ✅ | ✅ | ✅ |
| `SIGNUP` | Phase 3 | ✅ | ✅ | ✅ | ✅ |
| `AUTH_MIDDLEWARE` | Phase 3 | ✅ | ✅ | ✅ | ✅ |
| `FORGOT_PASSWORD` | Phase 3 | ✅ | ✅ | ✅ | ✅ |
| `LOGOUT` | Phase 3 | ✅ | ✅ | ✅ | ✅ |
| `DEPLOYMENT_PROD` | Phase 4 | ✅ | ✅ | ✅ | ✅ |
| `DEPLOYMENT_STAGING` | Phase 4 | ✅ | ✅ | ✅ | ✅ |
| `DEPLOYMENT_DATABASE_BACKUP` | Phase 4 | ✅ | ✅ | ✅ | ✅ |
| `DEPLOYMENT_HEALTH_CHECK` | Phase 4 | ✅ | ✅ | ✅ | ✅ |
| `MAGIC_LINK` | Epic 15 | ✅ | ✅ | ✅ | ✅ |
| `SOCIAL_OAUTH_GOOGLE` | Epic 15 | ✅ | ✅ | ✅ | ✅ |
| `SOCIAL_OAUTH_NAVER` | Epic 15 | ✅ | ✅ | ✅ | ✅ |
| `SOCIAL_OAUTH_KAKAO` | Epic 15 | ✅ | ✅ | ✅ | ✅ |
| `SSO_ENTERPRISE` | Epic 15 | ✅ | ✅ | ✅ | ✅ |
| `LAUNCH_LANDING` | 1st release | ✅ | ✅ | ✅ | ✅ |
| `LAUNCH_TOS` | 1st release | ✅ | ✅ | ✅ | ✅ |
| `LAUNCH_SUPPORT` | 1st release | ✅ | ✅ | ✅ | ✅ |
| `LAUNCH_MONITORING` | 1st release | ✅ | ✅ | ✅ | ✅ |
| `TENANT_IDP_MANAGEMENT` | Epic 16 | ✅ | ✅ | ✅ | ✅ |
| `MULTI_REGION_BACKUP` | Phase 5 | ✅ | ✅ | ✅ | ✅ |
| `MULTI_REGION_FAILOVER` | Phase 5 | ✅ | ✅ | ✅ | ✅ |
| `AUDIT_LOG_VIEW` | Epic 17 | ✅ | ✅ | ✅ | ✅ |
| `AUDIT_LOG_RETENTION` | Phase 6 | ✅ | ✅ | ✅ | ✅ |
| `OBSERVABILITY_TRACES` | Phase 7 | ✅ | ✅ | ✅ | ✅ |
| `OBSERVABILITY_METRICS` | Phase 7 | ✅ | ✅ | ✅ | ✅ |
| `PERFORMANCE_TESTING` | Phase 8 | ✅ | ✅ | ✅ | ✅ |
| `CHAOS_ENGINEERING` | Phase 9 | ✅ | ✅ | ✅ | ✅ |
| `SLO_ENGINEERING` | Phase 10 | ✅ | ✅ | ✅ | ✅ |
| `FINOPS_SHOWBACK` | Phase 11 | ✅ | ✅ | ✅ | ✅ |
| `FINOPS_CHARGEBACK` | Phase 11 | ✅ | ✅ | ✅ | ✅ |
| `FINOPS_ANOMALY_DETECTION` | Phase 12 | ✅ | ✅ | ✅ | ✅ |
| `FINOPS_BUDGET_ALERT` | Phase 12 | ✅ | ✅ | ✅ | ✅ |
| `FINOPS_FORECASTING_CAPACITY_PLANNING` | Phase 13 | ✅ | ✅ | ✅ | ✅ |
| `FINOPS_OPTIMIZATION` | Phase 14 | ✅ | ✅ | ✅ | ✅ |
| `FINOPS_TAG_GOVERNANCE` | Phase 15 | ✅ | ✅ | ✅ | ✅ |

## Notes

- **COST_CALCULATION (Story 4.1)** — gated to industries with a
  manufacturing footprint. Service-only tenants use Epic 9 ABC costing
  (COST_POOL / ACTIVITY / DRIVER) instead. The capability gate is
  enforced at the FastAPI route boundary
  (`apps/api/main.py` + `m3_calculate` module), NOT inside the engine.
  The engine itself (`packages.cost_engine.core.period_cost`) is pure
  and industry-agnostic — it ALWAYS returns `state="draft"` (AD-22
  append-only-leaning). Service layer owns `verified` / `committed`
  / `reversed` transitions.
- **PRODUCT** (catalog) is granted to every industry — service tenants
  still register `product` + `goods` + `service` types (R6 from CR 2.1).
- **PRODUCT_MATERIAL** gates the `material` + `semi_product` types.
  Service tenants cannot register raw materials or semi-finished goods
  (no BOM menu → no physical catalog entries).
- **MONTHLY_INPUT_PRODUCTION** gates the [생산] tab in m2_input only.
  The other 5 streams (orders/sales/purchases/expenses/labor) are
  **ungated** — every industry has them.
- **FTE 정밀 계산 (Story 3.2)** — [`MONTHLY_INPUT_LABOR` capability의 일부].
  추가 capability 부재. PRD §6.1 인건비 구성 (기본급·시간외·복리후생·
  상여·퇴직충당금) + `pay_type` 분기 (monthly 정규직 vs daily 일용직)
  가 [인원] 탭에 통합됨. 직급별 capability 분기 불필요.
- **테넌트별 payroll 정책 override** — `tenant_settings.payroll.*` JSONB
  sub-block으로 per-tenant override (Story 3.2 신규 도입). 빈 dict
  `{}`은 PRD §6.1 default (`monthly_salary_basis_krw=2_500_000`,
  `workdays_in_month=22`, `standard_monthly_hours=228`,
  `company_burden_rate=0.115`)로 fallthrough.
- **음수재고·조업도 실시간 경고 (Story 3.3)** — capability-ungated.
  PRD §A11 오류의 가시화 정책은 입력 시 warning(200 OK + 진행 허용)
  → 마감 시 Epic 4 first_calc hook에서 임계 위반 차단. m2_input 응답에
  `warnings[]`, `is_blocked`, `warnings_count`, `top_n_severity` 4개
  필드가 항상 포함됨. service-only 테넌트는 inventory projection 빈
  결과 → 0개 경고 (예외 아님). 2개 warning code만 노출:
  `NEGATIVE_CLOSING_INVENTORY` (PRD §V3) + `OVERCAPACITY_OPERATING_RATE`
  (PRD §V5). Epic 5 5-1 단계에서 opening_inventory JSONB의 cj-style
  default=0 + ledger-backed read로 자동 전월 기말 carry-chain 진입
  (`TODO(epic-5)` marker — closed in Story 5-2; A19 carry-over sprint
  removed `inventory_projection.py` entirely; math surface is now in
  `packages/services/m2_input/inventory_math.py`).
- **AI_EXTRACT** is granted to every industry (PRD §4.2 AI cross-cutting
  feature). Tenant-only restriction is PIPA consent, not industry.
- **AI_INSIGHT (v1.21 NEW, Epic 10)** — `AI_EXTRACT` 와 별개 row. Granted
  to ALL 4 canonical industries (industry-agnostic, CR 12-1 L4 precedent —
  `TWO_FACTOR_AUTH` / `BACKUP_EXPORT` / `BUDGET_SCENARIO` 와 동일 pattern).
  AD-7 (AI non-authoritative: `AI output → input_drafts` only; M10 attempts
  to write `confirmed_inputs` → denied + counted, target 0) + AD-17
  (promotion port idempotency on `(tenant_id, period_key, source_draft_id)`)
  + AD-25 (cache invalidation: key `(tenant_id, period_key,
  calculation_result_hash)`; Epic 4 calc-hash publisher channel `ai_cache`
  만 Epic 10 wire 진입 시점에 wire; Epic 11 close/reopen trigger EXTENSION은
  Story 11.1/11.3 진입 시점 — CR 1.1 forward-lock) bind. Epic 10 wire 진입
  시점 4 NEW endpoints + Discriminated union `source_kind: Literal['auto_analysis',
  'ai_reference']` (10-3 badge separation) + strict reject 외 value counter
  increment (AD-7 SM-3a 정합). Capability row 신설 1개 (capability matrix
  v1.21 = v1.20 + 1 NEW row). A19 cohesion pattern 보존: Epic 10 wire 자체는
  신규 pure kernel surface 없이 service layer + frontend 위주.
- **ABC_CALCULATION dual-route gate (Story 9.3)** — `POST /api/v1/calc`
  uses `require_any_capability(COST_CALCULATION, ABC_CALCULATION)` —
  ANY-OF semantics. M3 orchestrator's `_resolve_engine_type(industry)`
  then dispatches:
  - `tenant.industry == 'service'` → M9 ABC path
    (`AbcAllocationService.compute_and_persist`)
  - else → M3 traditional path (PRD §F0.2 3종 allocation)
  The capability matrix itself is unchanged (no new capability row
  added). The dual-route dispatch is owned by M3 (`apps/api/modules/
  m3_calculate/services/calc_orchestrator.py`), per AD-18
  "M3 owns ONLY the public endpoint." Response envelope is a
  discriminated union `CalcResponse | CalcAbcResponse` with
  `engine_type: Literal["trad", "abc"]` tag discriminator.

## Defense in depth

- The matrix above is mirrored in three places:
  1. `apps/api/core/capability.py::Capability` enum + `_INDUSTRY_CAPABILITIES`
  2. `apps/web/lib/menu-config.ts::INDUSTRY_ALLOWED_PRODUCT_TYPES` +
     `INDUSTRY_VISIBLE_STREAMS` (TS projection for sidebar / tabs)
  3. `supabase/policies/0006_products_rls.sql` (RLS tenant_id predicate)
- Drift is caught by:
  - `tests/integration/test_capability_consistency.py`
  - `tests/integration/test_m2_input_label_consistency.py` (Story 3.1)
  - `tests/integration/test_menu_config_consistency.py` (Story 1.1)
- Enforcement order on a write:
  1. `get_tenant_context` reads JWT → `TenantContext`
  2. `require_capability(capability)` checks industry via
     `SettingsService.get_tenant_settings`
  3. Service layer validates per-stream shape
  4. RLS row-level policy enforces `tenant_id = JWT.tenant_id`

## Adding a new capability

1. Add to `Capability` enum + 4-industry mapping in
   `apps/api/core/capability.py`
2. If UI-visible, add to TS mirror (`apps/web/lib/menu-config.ts`)
3. Extend `tests/integration/test_capability_consistency.py` (one param
   row per capability per industry)
4. Update this matrix
5. (If new RLS) add policy file `supabase/policies/XXXX_<table>_rls.sql`

## Story → capability reference

| Story | Capabilities introduced or gated |
|---|---|
| 1.1 — Industry selector | (none — pure framework) |
| 1.3 — AI extraction | `AI_EXTRACT` |
| 2.1 — Product master | `PRODUCT`, `PRODUCT_MATERIAL` |
| 2.2 — BOM matrix | `BOM` |
| 3.1 — Six-stream monthly input | `MONTHLY_INPUT_PRODUCTION` |
| 3.2 — FTE precision + daily labor | (no new capability; FTE precision is part of `MONTHLY_INPUT_LABOR` ungated path; per-tenant payroll override via `tenant_settings.payroll.*` JSONB sub-block) |
| 3.3 — Negative inventory & overcapacity warning | (no new capability; warning aggregate is part of `MONTHLY_INPUT_LABOR` ungated path + PRD §V3/§V5 universal gating on inventory-bearing product types only; service tenants → 0 inventory warnings by construction) |
| 4.1 — Pure cost engine (periodic §6.1 산식) | `COST_CALCULATION` (granted to mfg / mfg+service / mfg+service+other; service-only tenants use ABC instead) |
| 4.3 — Verification envelope (V1·V4·V7·V8) | (no new capability; verdict envelope wired INTO `COST_CALCULATION` response) |
| 4.4 — V8 골든 byte-identical CI gate | (no new capability; 12 fixture 매트릭스가 `COST_CALCULATION` 응답 verdict envelope 의 V8 fail-path audit action (`verify_v8_golden_match`) 으로 wire) |
| 5.x — Inventory | `OPENING_INVENTORY`, `INVENTORY_LEDGER` |
| 9.x — ABC | `COST_POOL`, `ACTIVITY`, `DRIVER`, `SEGMENT_SPLIT`, `ABC_CALCULATION` (9.1) |
| 10.1 — AI Document Extraction | `AI_INSIGHT` |
| 10.2 — Three-Insight Cache Policy | `AI_INSIGHT` |
| 10.3 — Reference vs Auto Analysis Badge | `AI_INSIGHT` |
| 10.4 — AI Promotion Port Idempotency | `AI_INSIGHT` |

## Changelog

- 2026-08-01 — Initial matrix (Epic 1 회고 A4 + Epic 2 회고 A3 + Epic 3 Story 3.1).
- 2026-08-01 — Story 3.2 footnote added (payroll override + labor precision path).
- 2026-08-01 — Story 3.3 footnote added (음수재고·조업도 실시간 경고;
  capability-ungated; warnings aggregate on m2_input state response).
- 2026-08-02 — v1.1 (Story 4.1): `COST_CALCULATION` row added; service-only
  tenants do NOT have COST_CALCULATION (Epic 9 ABC instead). Engine is
  industry-agnostic — gate is enforced at the FastAPI route boundary.
- 2026-08-02 — v1.4 (Story 4.4): V8 byte-identical 골든 매트릭스
  (4 industries × 3 baseline shapes) + `verify_v8_golden_match` audit
  action forward-lock. Industry canonical names parity 정렬. Capability
  행 자체는 변경 없음.
- 2026-08-03 — v1.5 (Story 5.1, Epic 5): 기초재고 자동 이월 체인 (PRD §F4.1)
  추가. `Capability.OPENING_INVENTORY`는 이미 manufacturing-kind
  industry 3종 (manufacturing / manufacturing_service /
  manufacturing_service_other) 에 wired. Service industry는 자동
  no-op (carry chain returns empty decisions — inventory-bearing
  products 없음). Capability 행 자체는 변경 없음 (5-1 wire는
  기존 Capability 사용).
- 2026-08-04 — v1.6 (Story 5.2, Epic 5): `INVENTORY_LEDGER` capability
  row confirmed + 4 HTTP routes registered behind the gate. Drift
  protection added (`tests/integration/test_inventory_ledger_capability.py`).
  Service-only tenants continue to be excluded (403
  INDUSTRY_NOT_SUPPORTED — BOM 없음 → ledger 의미 없음). Capability
  행 자체는 변경 없음 (5-2 wire는 5-1 의 Capability.OPENING_INVENTORY
  와 동일한 manufacturing-kind 3종 wiring 사용).
- 2026-08-06 — v1.7 (Story 5.3): `CLOSING_GUARD` capability wire (manufacturing 3종 ✅ / service-only ❌) + `ActionClass.CLOSING_GUARD` 3 values 채움 + `ActionClass.VERIFICATION` V3 value add (4 → 5) + V3 verification surface wire + Alembic 0016 SQL CHECK constraint (chk_opening_inventory_manual_reject) + monthly_input_rows.created_via column + idx_closing_guard_audit index.
- 2026-08-07 — v1.8 (Story 6.1, Epic 6): `MONTHLY_CLOSING_REPORT` capability wire (manufacturing 3종 ✅ / service-only ❌ INDUSTRY_NOT_SUPPORTED) + 3 NEW routes (`POST /closing-period/confirm` + `GET /closing-period/status` + `GET /closing-period/audit-trail`) + `ActionClass.CLOSING_PERIOD` 3 values 채움 (`closing_period_confirmed` + `closing_period_blocked` + `closing_period_snapshot_inconsistency`) + `ActionClass.VERIFICATION` V4 value add (5 → 6) + V4 closing-period-snapshot verification surface wire + Alembic 0017 (`chk_closing_period_status` 3-state lifecycle + `closing_snapshot_event_count` non-negative CHECK + `finalized_at` + `closed_by_actor_id` + `idx_closing_period_audit` JSONB index) + monthly_input_periods.status lifecycle = `open` → `closing` → `closed` 1-way state machine (AD-6 close lock) + closing_snapshot ledger event wire (5-2 11th event_type).
- 2026-08-08 — v1.9 (Story 6.2, Epic 6): `MONTHLY_CLOSING_REPORT` capability
  6-1 wire done + 6-2 report view modes (READY/PARTIAL/EMPTY 3-state) +
  V4 closing-period consistency 4-source verification + KRW/USD dual
  display (PRD §F5.2 banker's rounding) + 3 NEW routes (report +
  audit-trail + v4-verdict) + V8 골든 fixture 16 → 18 (closing-period-fixture-1
  + fiscal-period-snapshot-fixture-1 2 NEW V8 골든 from 6-1 T10.5 carry-over
  close). Capability 행 자체는 변경 없음 (6-1 wire 그대로 사용).
- 2026-08-12 — v1.14 (Story 12.2, Epic 12): `BACKUP_EXPORT` capability wire
  (industry-agnostic — ALL 4 canonical industries ✅; CR 12-1 L4 precedent —
  "백업은 운영자 인프라") + 3 NEW routes under `/api/v1/account/backups/*`
  (`GET /recent` + `GET /{backup_id}/download` + `POST /trigger`) +
  `ActionClass.ACCOUNT_BACKUP` 5 values 채움 (`backup_created` +
  `backup_failed` + `backup_retention_purged` + `backup_downloaded` +
  `backup_triggered`) + Alembic 0024 (`tenant_backups` table + 12 columns
  + 2 indexes + partial UNIQUE on `(tenant_id, backup_date) WHERE purged_at
  IS NULL`) + RLS 0014 (5-policy split: same-tenant SELECT + owner-only
  SELECT + same-tenant INSERT + UPDATE forbidden + DELETE forbidden) +
  packages/services/m12_account/backup_export pure kernel subtree
  (stdlib-only JSON serialization + sha256 hashing + 7-table dump) +
  `apps/api/jobs/backup_daily.py` (KST 02:00 = UTC 17:00 cron entry) +
  `apps/api/jobs/backup_retention.py` (KST 03:00 = UTC 18:00 retention sweep).
  NFR4: RPO 24h / RTO 4h / 30-day backup retention. AD-10 owner-only gate
  enforced at route via `require_role("owner")` (NOT `require_capability`)
  — capability is documented but intentionally NOT enforced as a route gate
  per CR 12-1 L4 precedent (industry-agnostic security baseline).
- 2026-08-08 — v1.10 (Story 11.1, Epic 11): `REVERSAL_REQUEST` capability wire
  (manufacturing 3종 ✅ / service-only ❌) + 3 NEW routes (`POST /close/reversal-requests`
  + `GET /close/reversal-requests/{correction_group_id}` + `POST /close/cache-invalidation`)
  + `ActionClass.M11_REVERSAL` 2 values 채움 (`m11_reversal_handler_invoked` +
  `inventory_ledger_reversal_logged`) + AD-22 reversal ledger wire +
  AD-25 1-channel publisher (`ai_cache`) + Alembic 0019
  (`cache_invalidation_log` table + 1-channel CHECK + `reversal_log` table
  + partial UNIQUE on `(tenant_id, reverses_event_id)`).
- 2026-08-08 — v1.11 (Story 11.2, Epic 11): `CLOSE_SEQUENCE_LOCK` capability
  wire (manufacturing 3종 ✅ / service-only ❌) + 4 NEW routes
  (`POST /close/sequence/initiate` + `POST /close/sequence/step-complete`
  + `GET /close/sequence/state` + `POST /close/sequence/confirm`) +
  `ActionClass.MONTHLY_CLOSING` 4 values 채움 (`closing_sequence_initiated`
  + `closing_sequence_step_completed` + `closing_sequence_confirmed` +
  `closing_sequence_audit_failed`) + fiscal_periods greenfield table
  (Alembic 0020) + 4-stage sequence (divisions → manufacturing → abc →
  common) + AD-6 INSERT 거부 guard.
- 2026-08-10 — v1.13 (Story 12.1, Epic 12): `TWO_FACTOR_AUTH` capability
  wire (industry-agnostic — ALL 4 canonical industries ✅) +
  5 NEW routes under `/api/v1/2fa` (`POST /setup` + `POST /verify` +
  `POST /challenge` + `POST /recovery` + `POST /disable`) +
  `ActionClass.TWO_FACTOR_AUTH` 6 values 채움
  (`two_factor_setup_initiated` + `two_factor_setup_completed` +
  `two_factor_challenge_passed` + `two_factor_challenge_failed` +
  `two_factor_recovery_consumed` + `two_factor_disabled`) +
  Alembic 0022 (users `totp_secret` BYTEA + 4 totp_* columns +
  `totp_recovery_codes_hash` JSONB) + RLS 0013 + NFR6 AES-256-GCM
  column-level encryption (12-byte nonce + ct + 16-byte tag) +
  NFR5 TLS in-transit (plaintext secret NEVER logged) +
  `packages/services/m12_account/` pure kernel subtree
  (RFC 6238 TOTP + PBKDF2-HMAC-SHA256 recovery hashing +
  2FA gate validation) + `apps/api/core/crypto.py` +
  `apps/api/core/key_manager.py` + service layer (CR 1.1 audit-first
  via `emit_audit_typed` + idempotent no-op re-setup + lockout state
  mgmt + AD-10 4-role gate) + 2FA challenge token HS256 JWT
  (5-min TTL + purpose=`two_factor_challenge`).
- 2026-08-09 — v1.12 (Story 11.3, Epic 11): 3 NEW capability rows added
  (`SNAPSHOT_PERSISTENCE` + `REVERSAL_EXECUTE` + `REOPEN_OPERATOR` —
  all manufacturing 3종 ✅ / service-only ❌) + 4 NEW routes
  (`POST /close/snapshots/commit` + `POST /close/snapshots/reverse`
  + `POST /close/sequence/reopen` + `GET /close/snapshots/{period_key}`)
  + `ActionClass.SNAPSHOT_PERSISTENCE` 4 values +
  `ActionClass.REOPEN_OPERATOR` 2 values 채움 + AD-25 4-channel publisher
  wire (`ai_cache` + `cost_engine_cache` + `fiscal_period_cache` +
  `closing_snapshot_cache`) + Alembic 0021 (`cache_invalidation_log`
  channel CHECK 1 → 4 expansion + 4 per-channel indexes) + RLS 0012
  (cache_invalidation_log 4-policy split) + W2 reopen operator flow
  (`operator_action` 4-value enum + `reason` length 20-500) +
  AD-20 fiscal_period_snapshots state machine
  (`draft` → `verified` → `committed` → `reversed`) + AD-22 reversal
  영구화 (3-tier guard: monthly_input_periods.status='closed' +
  fiscal_periods.status='closed' + fiscal_period_snapshots.state='committed').
- Future: each capability addition appends one row to the matrix and
  one row to the Changelog.
- 2026-08-17 — v1.21 (Epic 10 PRD entry): **`AI_INSIGHT` capability 1 NEW**
  (industry-agnostic, 4-industry grants ✅/✅/✅/✅ — CR 12-1 L4 precedent like
  `TWO_FACTOR_AUTH` / `BACKUP_EXPORT` / `BUDGET_SCENARIO`). Epic 10 4 stories
  (10-1 AI Document Extraction + 10-2 Three-Insight Cache + 10-3 Reference vs
  Auto Badge + 10-4 Promotion Port) bind to single `AI_INSIGHT` row (CR 11-3
  즉시 sweep 회피 패턴 — 1 row 신설로 4 stories wire, `ABC_CALCULATION` 1 row
  4 stories wire 동일 pattern). 본 entry는 **docs-only PRD entry** (Epic 10
  PRD 진입, capability matrix v1.20 → v1.21 wire); Epic 10 wire 진입 시점에
  4 NEW endpoints + `AI_INSIGHT` 실제 grant + drift detector test (P-015 SSOT
  pattern, v1.18 ABC_CALCULATION row 12 cases precedent) 별도 atomic wire.
  AD-7 (AI non-authoritative) + AD-17 (promotion port idempotency) + AD-25
  (cache invalidation, Epic 4 calc-hash publisher channel `ai_cache` 만 Epic
  10 wire 진입 시점 wire; Epic 11 close/reopen trigger EXTENSION은 Story
  11.1/11.3 진입 시점 forward-lock) bind. 결정: A28/A29/A30 forward-lock
  chain 보존 (Epic 9 retro 9-7 follow-up sprint DONE, atomic commit
  `146a7da`) + A35 frontend test debt + A36 SDR 검증 프로토콜 wire 진입 정합.
  3중 게이트 impact = NONE (docs only 변경). Drift detector 신규:
  `tests/integration/test_capability_matrix_v1_21_drift.py`.
- 2026-08-17 — v1.20 (Story 9.4, Epic 9): **A30 forward-lock dual-report
  PDF generator** 결정 wire (PRD §9 #21 원가대상별 원가 집계표 + §7.3
  법인세법 시행규칙 제76조 2기준). No NEW capability — capability 행 자체는
  변경 없음 (9-4 wires Report #21 via existing dual-route
  `require_any_capability(COST_CALCULATION, ABC_CALCULATION)`, A30 SHARED
  PDF factory delegates via Discriminated union
  `report_id: Literal[15, 16, 17, 18, 19, 20, 21]`). M5 owns ONLY the
  Report #21 endpoint (AD-18 single endpoint invariant — 1 endpoint per
  Report #N): `GET /api/v1/reports/21` + `POST /api/v1/reports/21/pdf`.
  A30 SHARED `packages/services/m5_reports/pdf_generator.py` factory
  pattern (Report #21 본 story + Report #15 후속 placeholder, A31+
  forward-lock 결정). 4 NEW typed exceptions mapped to AD-15 §4
  envelopes in `apps/api/main.py` (CR 12-5 D-14): `Report21PeriodNotCommittedError`
  → 422 REPORT21_PERIOD_NOT_COMMITTED + `Report21NoBreakdownError` → 422
  REPORT21_NO_COST_OBJECT_BREAKDOWN + `Report21BreakdownNotFoundError` →
  404 REPORT21_BREAKDOWN_NOT_FOUND + `Report21PdfGenerationError` → 500
  REPORT_PDF_GENERATION_ERROR. Alembic SKIPPED (9-4 reads existing
  `fiscal_period_snapshots.cost_object_breakdown JSONB` from 9-3 wire).
  A19 cohesion pattern 7 surface (`packages/cost_engine/abc_engine.py`
  9-1+9-2+9-3+9-4 EXTENSION 누적) + A19 cohesion pattern 8 surface
  (NEW SHARED `pdf_generator.py` factory). Drift detector:
  `tests/integration/test_capability_matrix_v1_20_drift.py`.
- 2026-08-16 — v1.19 (Story 9.3, Epic 9): **dual-route gate** on
  `POST /api/v1/calc` (PRD §F9.3 + A29 forward-lock dual-route + AD-19).
  No NEW capability — uses `require_any_capability(COST_CALCULATION,
  ABC_CALCULATION)` ANY-OF semantics (CR 12-5 D-14 + CR 6-2 V4
  3-source contract). M3 orchestrator owns the public endpoint (AD-18)
  and dispatches via `_resolve_engine_type(industry)`:
  - service → M9 ABC path (`AbcAllocationService.compute_and_persist`,
    9.3 wire, 11-step pipeline + AD-22 audit-first INSERT)
  - else → M3 traditional path (PRD §F0.2 3종 allocation).
  Response is discriminated union `CalcResponse | CalcAbcResponse`
  with `engine_type: Literal["trad", "abc"]` tag. Pure kernel
  `packages/cost_engine/abc_engine.py` EXTENSION (A28 forward-lock 3-way
  wire: CCR ↔ Activity ↔ Cost Object Breakdown, D-9-1-DEFER-1/2/4 해소):
  - 5 NEW frozen dataclasses (DispatchState + V7Verdict +
    MultiDepartmentCcrResult + DepartmentAllocation + UnusedCapacitySubRow)
  - 2 NEW typed exceptions (EmptyDepartmentsError + TooManyDepartmentsError)
  - 5 NEW pure functions (validate_department_count + dispatch_abc_path +
    compute_abc_allocation_hash + validate_v7_balance + compute_multi_dept_ccr)
  - 3 NEW constants (ABC_HASH_PREFIX + V7_BALANCE_TOLERANCE_KRW +
    MAX_DEPARTMENT_COUNT).
  Service layer `AbcAllocationService.compute_and_persist` (11-step
  pipeline: load departments → validate count → per-dept CCR → multi-dept
  CCR → per-dept allocation + V7 → cost_object_breakdown JSON →
  unused_capacity JSON → V8 hash → idempotency + audit-first INSERT
  → fiscal_period_snapshots INSERT → COMMIT). Alembic 0028
  (`apps/api/alembic/versions/0028_abc_fiscal_period_breakdown.py`) adds
  2 JSONB columns to `fiscal_period_snapshots` (cost_object_breakdown +
  unused_capacity_breakdown) + 2 GIN indexes (jsonb_path_ops) +
  2 COMMENT ON COLUMN (NFR18 lock); down_revision = `0027_budget_pre_standard`
  (8-3 wire tip). 2 NEW typed exception envelopes (CR 12-5 D-14):
  422 ABC_EMPTY_DEPARTMENTS + 422 ABC_TOO_MANY_DEPARTMENTS.
  Drift detector: extend `tests/integration/test_capability_matrix_v1_18_drift.py`
  with v1.19 row fill change (`ABC_CALCULATION` stories → "9.1, 9.2, 9.3").
- 2026-08-16 — v1.18 (Story 9.1, Epic 9): `ABC_CALCULATION` capability
  wire (industry-agnostic — ALL 4 canonical industries ✅; CR 12-1 L4
  precedent — "ABC는 운영 인프라") + 4 NEW routes under
  `/api/v1/abc/*` (`POST /cost-pools` + `POST /activities` +
  `POST /drivers/validate` + `POST /validate`) +
  `packages/cost_engine/abc_engine.py` pure kernel (A19 cohesion
  pattern 6번째 surface — 4 functions + 3 frozen dataclasses +
  4 typed exceptions + 7 constants, AD-5 stdlib-only, no I/O, V8
  determinism sha256:64-hex) + service layer `AbcValidationService`
  with `_to_validation_state` ORM→kernel boundary (CR 12-1 L3
  precedent) + `validate_abc_pct_list` 3-layer defense (CR 12-5 L3)
  + 4 NEW typed exception envelopes (422 COST_POOL_INVALID_SUM +
  422 ACTIVITY_INVALID_SUM + 422 DRIVER_INVALID_SUM +
  404 ABC_VALIDATION_NOT_FOUND) + Alembic/RLS SKIPPED (validation
  only, no INSERT/UPDATE/DELETE — CR 1.1 read-mostly invariant;
  A5 forward-lock 변경 0). Drift detector:
  `tests/integration/test_capability_matrix_v1_18_drift.py`.
- 2026-08-22 — v1.31 (Phase 6 PRD entry): `AUDIT_LOG_RETENTION` capability wire (industry-agnostic — ALL 4 canonical industries ✅; CR 12-1 L4 precedent — "감사로그 보존은 운영 인프라" + D-RETENTION-1 honestly RESOLVE 진입 시점에 정직 회복 결정 wire) + 신규 row 추가 결정 (`AUDIT_LOG_RETENTION`) + Epic 17 wire `2ada2ec` `AUDIT_LOG_VIEW` row preservation + MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire `f093f8c` + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY Epic 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern verbatim bind. `apps/api/core/capability.py` MODIFIED + `Capability.AUDIT_LOG_RETENTION = "audit_log_retention"` 1 NEW enum + 4-industry grants ✅/✅/✅/✅. `apps/api/dependencies/capability.py` EXTENSION `require_audit_log_retention` 1 NEW dep + owner-only RBAC AD-22 verbatim 보존. Drift detector: `tests/integration/test_capability_matrix_v1_31_drift.py` NEW 8 NEW pytest cases 결정 (Epic 17 wire `2ada2ec` 의 `tests/integration/test_capability_matrix_v1_30_drift.py` + Phase 5 wire `f093f8c` 의 `tests/integration/test_capability_matrix_v1_29_drift.py` 패턴 verbatim). 1st release close-out retro §6 + Epic 17 close-out retro §11 "audit log retention policy 결정 wire 보류, Phase 6+ 진입 시점" verbatim 해소 결정 wire. D-RETENTION-1 honestly RESOLVE 진입 wire 결정 + CR 11-3 honest-DEFER discipline 85번째 epic 연속 정직 회복 검증 보존.
- 2026-08-24 — v1.34 (Phase 9 PRD entry): `CHAOS_ENGINEERING` capability wire (industry-agnostic — ALL 4 canonical industries ✅; CR 12-1 L4 precedent — "chaos engineering 은 운영 인프라" + D-CHAOS-1 honestly RESOLVE 진입 시점에 정직 회복 결정 wire) + 신규 row 추가 결정 (`CHAOS_ENGINEERING`) + Phase 8 wire `60d4ea1` `PERFORMANCE_TESTING` row preservation + OBSERVABILITY_TRACES + OBSERVABILITY_METRICS Phase 7 wire `59b56cd` + AUDIT_LOG_RETENTION Phase 6 wire `24e1cd7` + AUDIT_LOG_VIEW Epic 17 wire `2ada2ec` + MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire `f093f8c` + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY Epic 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern verbatim bind. `apps/api/core/capability.py` MODIFIED + `Capability.CHAOS_ENGINEERING = "chaos_engineering"` 1 NEW enum + 4-industry grants ✅/✅/✅/✅. `apps/api/dependencies/capability.py` EXTENSION `require_chaos_engineering` 1 NEW dep + owner-only RBAC AD-22 verbatim 보존 + Epic 12 2FA 챌린지 보존 결정. Drift detector: `tests/integration/test_capability_matrix_v1_34_drift.py` NEW 8 NEW pytest cases 결정 (Phase 8 wire `60d4ea1` 의 `tests/integration/test_capability_matrix_v1_33_drift.py` + Phase 7 wire `59b56cd` 의 `tests/integration/test_capability_matrix_v1_32_drift.py` 패턴 verbatim). Phase 8 close-out retro §10 + Phase 7 close-out retro §10 "Chaos Engineering / Game Day 결정 wire 보류, Phase 9+ 진입 시점" verbatim 해소 결정 wire. D-CHAOS-1 honestly RESOLVE 진입 wire 결정 + CR 11-3 honest-DEFER discipline 97번째 epic 연속 정직 회복 검증 보존.
- 2026-08-24 — v1.35 (Phase 10 bmad-dev-story wire): `SLO_ENGINEERING` capability wire (industry-agnostic — ALL 4 canonical industries ✅; CR 12-1 L4 precedent — "SLO engineering 는 운영 인프라" + D-SLO-1 honestly RESOLVE 진입 시점에 정직 회복 결정 wire) + Phase 9 wire `e7670e1` `CHAOS_ENGINEERING` row preservation + Phase 8 wire `60d4ea1` `PERFORMANCE_TESTING` row preservation + OBSERVABILITY_TRACES + OBSERVABILITY_METRICS Phase 7 wire `59b56cd` + AUDIT_LOG_RETENTION Phase 6 wire `24e1cd7` + AUDIT_LOG_VIEW Epic 17 wire `2ada2ec` + MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire `f093f8c` + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY Epic 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern verbatim bind. `apps/api/core/capability.py` MODIFIED + `Capability.SLO_ENGINEERING = "slo_engineering"` 1 NEW enum + 4-industry grants ✅/✅/✅/✅. `apps/api/dependencies/capability.py` EXTENSION `require_slo_engineering` 1 NEW dep + owner-only RBAC AD-22 verbatim 보존 + Epic 12 2FA 챌린지 보존 결정 (slo target update + budget freeze + governance approve + auto-rollback trigger 모두 owner-only RBAC AD-22 + Epic 12 2FA 챌린지 보존). Drift detector: `tests/integration/test_capability_matrix_v1_35_drift.py` NEW 4 NEW pytest cases 결정 (Phase 9 wire `e7670e1` 의 `tests/integration/test_capability_matrix_v1_34_drift.py` + Phase 8 wire `60d4ea1` 의 `tests/integration/test_capability_matrix_v1_33_drift.py` 패턴 verbatim). Phase 9 close-out retro §10 + Phase 8 close-out retro §10 "SLO Engineering / Error Budget Management 결정 wire 보류, Phase 10+ 진입 시점" verbatim 해소 결정 wire. D-SLO-1 honestly RESOLVE 진입 wire 결정 + CR 11-3 honest-DEFER discipline 103번째 epic 연속 정직 회복 검증 보존.
- 2026-08-25 — v1.40 (Phase 14 PRD entry): **`FINOPS_OPTIMIZATION` capability 1 NEW** (industry-agnostic, 4-industry grants ✅/✅/✅/✅ — CR 12-1 L4 precedent like `FINOPS_FORECASTING_CAPACITY_PLANNING` / `FINOPS_ANOMALY_DETECTION` / `FINOPS_BUDGET_ALERT` / `FINOPS_SHOWBACK` / `FINOPS_CHARGEBACK` / `SLO_ENGINEERING` / `CHAOS_ENGINEERING` / `OBSERVABILITY_*` / `AUDIT_LOG_RETENTION`). Phase 14 territory 결정 wire 진입 — optimization definition DSL + rightsizing engine 4 utilization analysis methods (P95 CPU + P95 memory + IOPS + network throughput) + idle resource detection 4 idle 정의 (P95 CPU < 5% + memory < 5% + 30 consecutive days) + RI/SP commitment recommendations 3 service EC2/RDS/ElastiCache + recommendation accuracy tracking (applied vs estimated savings + utilization improvement + completion rate) + optimization retraining trigger (accuracy < 60% for 5 consecutive recommendations) + optimization dashboard UI + audit-first INSERT 8 NEW + Capability FINOPS_OPTIMIZATION 1 NEW + dry-run mode 4 CLI flags + tests + wire scope T1~T8 territory 결정. Phase 13 wire `8b98030` forecast accuracy tracker EXTENSION + Phase 12 wire `f3c0e63` anomaly detection baseline EXTENSION + Phase 11 wire `e020ad0` chargeback allocation pattern EXTENSION 의 자연스러운 carry-over chain (historical baseline ⇒ forecast ⇒ optimization recommendation ⇒ accuracy tracking ⇒ retraining EXTENSION 정직 회복 chain 결정). AD-41 FinOps Optimization & Rightsizing 신규 결정 (a-g 7 sub-decisions). 3중 게이트 impact = NONE (docs only 변경). Drift detector 신규: `tests/integration/test_capability_matrix_v1_40_drift.py` (Phase 13 wire `8b98030` 의 `tests/integration/test_capability_matrix_v1_39_drift.py` 8 cases verbatim pattern bind). D-FINOPS-4 honestly DEFER 보존 → Phase 14 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire 진입 + CR 11-3 honest-DEFER discipline 117번째 epic 연속 정직 회복 검증 보존.
- 2026-08-25 — v1.40 (Phase 14 wire entry `119`): **`FINOPS_OPTIMIZATION` capability wire** (industry-agnostic — ALL 4 canonical industries ✅; CR 12-1 L4 precedent — "FinOps Optimization & Rightsizing 는 운영 인프라" + D-FINOPS-4 honestly DEFER 보존 → Phase 14 wire entry 진입 시점에 carry-over chain 정직 회복 결정 wire) + Phase 13 wire `8b98030` `FINOPS_FORECASTING_CAPACITY_PLANNING` row preservation + Phase 12 wire `f3c0e63` `FINOPS_ANOMALY_DETECTION` + `FINOPS_BUDGET_ALERT` row preservation + Phase 11 wire `e020ad0` `FINOPS_SHOWBACK` + `FINOPS_CHARGEBACK` row preservation + OBSERVABILITY_* Phase 7 wire `59b56cd` + AUDIT_LOG_RETENTION Phase 6 wire `24e1cd7` + AUDIT_LOG_VIEW Epic 17 wire `2ada2ec` + MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire `f093f8c` + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY Epic 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern verbatim bind. `apps/api/core/capability.py` MODIFIED + `Capability.FINOPS_OPTIMIZATION = "finops_optimization"` 1 NEW enum + 4-industry grants ✅/✅/✅/✅ (manufacturing + service + 겸영 + full matrix). `apps/api/dependencies/capability.py` EXTENSION `require_finops_optimization` 1 NEW dep + owner-only RBAC AD-22 verbatim 보존 + Epic 12 2FA 챌린지 보존 결정 (optimization definition update + recommendation generation + idle resource detection + commitment recommendation + optimization recommended action apply + optimization accuracy tracking trigger 모두 owner-only RBAC AD-22 + Epic 12 2FA 챌린지 mandatory 결정 wire). Drift detector: `tests/integration/test_capability_matrix_v1_40_drift.py` NEW 8 NEW pytest cases 결정 (Phase 13 wire `8b98030` 의 `tests/integration/test_capability_matrix_v1_39_drift.py` 8 cases verbatim pattern bind). Phase 14 PRD entry `0e3f8d9` (cj-style 117번째) + Phase 13 close-out retro `850b4f8` (cj-style 116번째) "FinOps Optimization & Rightsizing 결정 wire 보류, Phase 14 wire 진입 시점" verbatim 해소 결정 wire. D-FINOPS-4 honestly DEFER 보존 → Phase 14 wire entry 진입 wire 결정 + CR 11-3 honest-DEFER discipline 119번째 epic 연속 정직 회복 검증 보존.