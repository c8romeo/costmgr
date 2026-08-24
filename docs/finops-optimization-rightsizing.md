# FinOps Optimization & Rightsizing (Phase 14)

> **Phase 14 (cj-style 119번째 wire)** — FinOps Optimization & Rightsizing territory.

## §1. Introduction

This runbook covers the FinOps Optimization & Rightsizing system
introduced in Phase 14 (cj-style 119번째 wire). It extends the Phase 13
FinOps Forecasting & Capacity Planning territory with an ACTIONABLE
RECOMMENDATION LAYER — converting predictions into concrete rightsizing,
idle-termination, and RI/SP commitment recommendations.

PRD §F30.1~§F30.8 (8 ACs → 92 sub-ACs).

## §2. Capability Gate

`Capability.FINOPS_OPTIMIZATION` is granted to all 4
industries (manufacturing + service + manufacturing_service +
manufacturing_service_other) per CR 12-1 L4 industry-agnostic precedent.

Dependency helper: `require_finops_optimization` in
`apps/api/dependencies/capability.py`.

## §3. Optimization Definition DSL

The `OptimizationDefinition` TypedDict has 11 fields:

- `optimization_id` (UUID)
- `tenant_id` (UUID)
- `resource_type` (5 options: compute / storage / database / network / container)
- `optimization_strategy` (7 options: rightsize_down / rightsize_up /
  idle_terminate / commit_1y / commit_3y / storage_tier_down / composite)
- `target_metric` (4 options: cost_saving_pct / cost_saving_amount /
  utilization_target / commit_break_even_months)
- `baseline_period` (5 options: last_7d / last_30d / last_90d /
  last_180d / last_365d)
- `status` (3 options: active / paused / expired)
- `created_at` (ISO 8601)
- `updated_at` (ISO 8601)
- `trace_id` (ContextVar CR 1-1 verbatim)
- `metadata` (JSONB dict)

The `parse_optimization_definition()` pure validator enforces 6
validation rules (CR 11-4 P-015 verbatim).

## §4. Rightsizing Engine

`recommend_rightsizing()` provides actionable instance-type
recommendations for 5 resource types:

- **compute** — 80+ AWS EC2 instance type mapping across 4 families
  (general_purpose / compute_optimized / memory_optimized /
  storage_optimized). `INSTANCE_TYPE_DOWNGRADE_MAP` carries the
  downgrade matrix. `INSTANCE_TYPE_UPGRADE_MAP` carries the
  upgrade matrix for rightsize_up strategy.
- **storage** — `STORAGE_TIER_DOWNGRADE_MAP` from gp2 → gp3 → sc1 → st1
  → standard-ia → glacier tier transitions.
- **database** — RDS instance class downgrade matrix (db.t3 → db.t4g
  family transitions) + Aurora capacity unit adjustments.
- **network** — NAT Gateway → VPC Endpoint / CloudFront / S3
  Transfer Acceleration transitions.
- **container** — ECS task size / Fargate vCPU+memory right-sizing.

`RIGHTSIZING_ENGINE_MODEL_VERSION = "1.0.0"` (SEMVER Phase 13
registry convention extended).

## §5. Idle Resource Detection

`detect_idle_resources()` identifies resources where utilization
falls below 3 thresholds:

- **z-score** — `IDLE_Z_SCORE_THRESHOLD = -2.0` (Phase 12 EXTENSION).
  Resources whose trailing 30-day mean utilization is at least 2σ below
  the historical baseline are flagged.
- **threshold** — `IDLE_CPU_THRESHOLD_PCT = 5.0`. Resources whose CPU
  utilization is below 5% for the trailing 7 days are flagged.
- **heuristic** — Pattern-based: zero network I/O for 30d AND zero
  read requests for 30d.

Three severity levels: `low` (review), `medium` (downsize), `high`
(terminate). Three detection methods: `z_score` / `threshold` /
`heuristic`. Detection window: 30 days default.

## §6. Commitment Recommender

`recommend_commitment()` produces RI/SP commitment recommendations for
6 commitment types:

- `ec2_ri` (EC2 Reserved Instance)
- `rds_ri` (RDS Reserved Instance)
- `ec2_sp` (EC2 Savings Plan)
- `s3_sp` (S3 Savings Plan-style)
- `redshift_sp` (Redshift Savings Plan)
- `dynamodb_sp` (DynamoDB Reserved Capacity)

Two commitment terms: `1_year` (RI_SP_DISCOUNT_1Y=0.40) /
`3_year` (RI_SP_DISCOUNT_3Y=0.60).

`compute_break_even_months()` and `compute_roi_pct()` calculate the
break-even and ROI for each commitment.

## §7. Optimization Accuracy Tracking

`compute_precision()` / `compute_recall()` / `compute_accuracy_score()`
track the quality of optimization recommendations against realized
outcomes:

- **precision** = applied_recommendations / total_recommendations
  (of recommendations that were applied, what fraction produced
  expected savings?)
- **recall** = detected_savings_opportunities / actual_savings_opportunities
  (of opportunities that existed, what fraction did we catch?)
- **accuracy_score** = harmonic_mean(precision, recall) weighted by
  realized_savings / projected_savings ratio.
- **realized_savings_krw** — sum of actual savings displayed.

When `accuracy_score < ACCURACY_SCORE_RETRAINING_THRESHOLD_PCT (70.0%)`,
`check_accuracy_degradation()` triggers a retraining event with
`RETRAINING_CRON_DEFAULT = "0 3 * * 0"`.

## §8. Database Schema (alembic 0046)

alembic version `0046_phase_14_optimization` creates 6 NEW tables:

- `phase_14_finops_optimization_definition` — tenant_id, resource_type,
  optimization_strategy, target_metric, baseline_period, status + RLS +
  CHECK + UNIQUE constraints + indexes.
- `rightsizing_recommendation` — recommendation_id, tenant_id,
  resource_id, resource_type, current_instance_type,
  recommended_instance_type, current_cost_krw, recommended_cost_krw,
  projected_savings_pct, projected_savings_amount_krw,
  confidence_score, recommendation_severity, model_version,
  generated_at + RLS + CHECK + indexes.
- `idle_resource` — idle_resource_id, tenant_id, resource_id,
  resource_type, idle_reason, idle_duration_days,
  current_cost_krw_per_month, potential_savings_krw_per_month,
  idle_severity, action, detection_method, detection_window_days,
  generated_at + RLS + CHECK + indexes.
- `commitment_recommendation` — recommendation_id, tenant_id,
  commitment_type, commitment_term, resource_pattern,
  current_on_demand_cost_krw_per_month, projected_commit_cost_krw_per_month,
  projected_savings_pct, projected_savings_krw, upfront_cost_krw,
  break_even_months, roi_pct, recommendation_severity, generated_at +
  RLS + CHECK + indexes.
- `optimization_accuracy` — report_id, tenant_id, resource_type,
  optimization_strategy, total_recommendations, applied_recommendations,
  precision, recall, realized_savings_krw, projected_savings_krw,
  accuracy_score, generated_at + RLS + CHECK + indexes.
- `optimization_preview` — preview_id, tenant_id, recommendation_id,
  dry_run_output, applied_by, applied_at + RLS + CHECK + indexes.

All tables include `tenant_id` for RLS (CR 0-2 verbatim) + audit-first
INSERT triggers.

## §9. Audit Actions (8 NEW)

8 NEW audit actions under `ActionClass.FINOPS_OPTIMIZATION`:

- `optimization_definition_updated` — emitted on OptimizationDefinition
  create/update.
- `recommendation_generated` — emitted on rightsizing/idle/commitment
  recommendation generation.
- `idle_resource_detected` — emitted on idle resource detection.
- `commitment_recommended` — emitted on RI/SP commitment recommendation.
- `optimization_recommended_action` — emitted on owner applying a
  recommendation.
- `optimization_dry_run_executed` — emitted on dry-run preview.
- `optimization_accuracy_degraded` — emitted when accuracy_score < 70%.
- `optimization_retraining_triggered` — emitted when retraining cron
  fires.

## §10. Typed Exceptions (14 NEW)

14 NEW typed exceptions in `apps/api/core/errors.py` under
`FinopsOptimizationError` (base) + module_id `m22_finops_optimization`:

- `OptimizationDefinitionInvalidError` (400)
- `OptimizationScopeInvalidError` (404)
- `OptimizationInventoryUnavailableError` (422)
- `RightsizingEngineError` (500)
- `InstanceTypeMappingError` (500)
- `RecommendationConfidenceLowError` (422)
- `IdleResourceDetectionError` (500)
- `IdleSeverityClassificationError` (500)
- `IdleMetricUnavailableError` (404)
- `CommitmentRecommendationError` (500)
- `PricingDataUnavailableError` (404)
- `BreakEvenCalculationError` (500)
- `OptimizationAccuracyTrackingError` (500)
- `OptimizationRetrainingTriggerError` (500)
- `OptimizationPerformanceDegradationError` (500)

CR 12-5 D-14 typed exception envelope pattern verbatim.

## §11. Frontend Dashboard

Route: `/[locale]/(dashboard)/admin/finops/optimization`
- `page.tsx` (RSC) — main entry
- `layout.tsx` — RTL section wrapper (CR 11-4 D-003)
- `FinopsOptimizationDashboardPanel.tsx` (Client) — 5 sub-components:
  OptimizationStrategySelector + RightsizingRecommendationTable +
  IdleResourcePanel + CommitmentRecommendationPanel +
  OptimizationAccuracyPanel (Recharts 2.12.7 AD-14 stack pin)
- `lib/finops-optimization/finops-optimization-client.ts` —
  CR 12-5 D-PARITY-01 Python TypedDict ↔ TypeScript interface mirror.
- `messages/ko-KR.json` — `finops_optimization.*` namespace (~30 keys,
  CR 11-4 D-002 verbatim SSOT).

## §12. RBAC + 2FA

AD-22 owner-only RBAC — all optimization operations (definition create,
recommendation apply, dry-run, retraining trigger) are owner-only.
Epic 12 2FA 챌린지 is mandatory when `governance_required=True`.

## §13. Test Coverage

~56 NEW pytest cases across 7 files (Phase 13 wire pattern verbatim):

- `test_phase_14_optimization_definition.py` — 7 cases
- `test_phase_14_rightsizing_engine.py` — 9 cases
- `test_phase_14_idle_resource_detector.py` — 9 cases
- `test_phase_14_commitment_recommender.py` — 9 cases
- `test_phase_14_optimization_accuracy_tracker.py` — 7 cases
- `test_phase_14_audit_action.py` — 8 cases
- `test_capability_matrix_v1_40_drift.py` (integration) — 8 cases

~7 NEW vitest cases for the dashboard panel + client (Phase 13 wire
pattern verbatim).

## §14. Architecture Alignment

Phase 14 wire preserves all 11 CR lessons + AD-22 + AD-41:
- CR 0-2 RLS — every table carries tenant_id selector.
- CR 1-1 audit-first INSERT — 8 NEW audit actions.
- CR 1-1 ContextVar — trace_id propagation.
- CR 1-1 RSC boundary — page.tsx RSC + Client panel.
- CR 11-3 honest-DEFER — D-FINOPS-4 honestly DEFER 보존.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope — 14 NEW.
- CR 12-5 D-PARITY-01 — Python ↔ TS mirror.
- CR 12-5 D-GATE-01 — capability gate fail-closed.
- AD-22 — owner-only RBAC.
- AD-41 — FinOps Optimization & Rightsizing 신규.
- NFR4 PII minimization PRESERVED — only cost metrics + savings.
- A19 cohesion — 9 surface EXTENSION PASS.
