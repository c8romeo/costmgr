"""
apps/api/dependencies/capability.py — FastAPI dependency helpers for capability gates.

Epic 17 (cj-style 82번째 epic 연속 정직 회복 wire) — T6 (AC #6.3) — F21.6.

Re-exports `require_capability` from `apps.api.core.capability` plus
Epic-15/16/17-specific named dependencies:

Epic 15:
  - `require_launch_landing()` — gates `/api/v1/launch/landing` (1st release)
  - `require_launch_tos()` — gates `/api/v1/launch/tos-acceptance` (1st release)
  - `require_launch_support()` — gates `/api/v1/launch/support-tickets` (1st release)
  - `require_launch_monitoring()` — gates `/api/v1/launch/*` (1st release)

Epic 16:
  - `require_tenant_idp_management()` — gates `/api/v1/admin/tenant/{slug}/idp`

Epic 17:
  - `require_audit_log_view()` — gates `/api/v1/audit-log[/...]` + `/audit-log/export`

Phase 6:
  - `require_audit_log_retention()` — gates `/api/v1/audit-log/retention[/...]` + `/audit-log/erase`

Phase 7:
  - `require_observability_traces()` — gates `/api/v1/observability/traces/lookup` + `/observability/alerts/ack` + PagerDuty integration
  - `require_observability_metrics()` — gates `/api/v1/metrics` Prometheus exposition + Grafana embed

Phase 8:
  - `require_performance_testing()` — gates `/api/v1/performance-testing/load-tests[/...]` (k6 manual trigger + status) + `/api/v1/performance-testing/slo/dashboard` + `/performance-testing/latency-regression/invalidate` + `/performance-testing/cost-engine-benchmark/invalidate`

Phase 9:
  - `require_chaos_engineering()` — gates `/api/v1/admin/chaos[/...]` (chaos experiment trigger + manual abort + auto-rollback + continuous chaos toggle) + `/chaos/game-day[/...]` + `/chaos/rollbacks[/...]`

Phase 10:
  - `require_slo_engineering()` — gates `/api/v1/admin/slo[/...]` (SLO definition create/update/delete + multi-region aggregation + tenant-scoped override + error budget freeze/unfreeze + governance review + SLO breach auto-rollback trigger + dry-run mode)

Phase 11:
  - `require_finops_showback()` + `require_finops_chargeback()` — FinOps showback + chargeback capability gates

Phase 12:
  - `require_finops_anomaly_detection()` + `require_finops_budget_alert()` — FinOps anomaly + budget alert capability gates

Phase 13:
  - `require_finops_forecast()` — FinOps Forecasting & Capacity Planning capability gate

Phase 14:
  - `require_finops_optimization()` — FinOps Optimization & Rightsizing capability gate

Phase 15:
  - `require_finops_tag_governance()` — FinOps Tag Governance & Cost Allocation capability gate

Phase 16:
  - `require_finops_reporting()` — FinOps Reporting & Executive Dashboard capability gate

Industry-agnostic (all 4 industries get these), CR 12-1 L4 precedent.
"""
from __future__ import annotations

from apps.api.core.capability import (
    Capability,
    require_capability,
)

# Re-export the canonical helper for `from apps.api.dependencies.capability import require_capability`
__all__ = [
    "Capability",
    "require_capability",
    "require_launch_landing",
    "require_launch_tos",
    "require_launch_support",
    "require_launch_monitoring",
    "require_tenant_idp_management",
    "require_audit_log_view",
    "require_audit_log_retention",
    "require_observability_traces",
    "require_observability_metrics",
    "require_performance_testing",
    "require_chaos_engineering",
    "require_slo_engineering",
    "require_finops_showback",
    "require_finops_chargeback",
    # Phase 12 (cj-style 111번째 wire) — BACKFILL Phase 12 capability
    # gate dependencies (Phase 12 wire skipped dep helpers, this is
    # honest recovery per cj-style 115번째 atomic commit).
    "require_finops_anomaly_detection",
    "require_finops_budget_alert",
    # Phase 13 (cj-style 115번째 wire) — FinOps Forecasting & Capacity
    # Planning capability (F29.6 + AC #6.3 + AD-39 (g) sub-decision).
    # Gates the FinOps forecast routes in apps/api/modules/finops/
    # (forecast definition + forecast generation + capacity headroom +
    # budget burn-rate + forecast accuracy + model retraining + dry-run).
    "require_finops_forecast",
    "require_finops_optimization",  # NEW — Phase 14 (FinOps Optimization & Rightsizing)
    "require_finops_tag_governance",  # NEW — Phase 15 (FinOps Tag Governance & Cost Allocation)
    "require_finops_reporting",  # NEW — Phase 16 (FinOps Reporting & Executive Dashboard)
    "require_finops_sustainability",  # NEW — Phase 17 (FinOps Sustainability & Carbon Reporting)
    "require_finops_commitment",  # NEW — Phase 18 (FinOps Cloud Commitment Management RIs/SPs/CUDs)
    "require_finops_pricing",  # NEW — Phase 19 (FinOps Pricing, Rate Card & TCO Modeling)
    "require_finops_multi_cloud",  # NEW — Phase 20 (FinOps Multi-Cloud Cost Unified Reconciliation)
    "require_finops_reserved_capacity",  # NEW — Phase 21 (FinOps Reserved Capacity Planning)
    "require_finops_chargeback_settlement",  # NEW — Phase 22 (FinOps Chargeback Settlement)
    "require_finops_unit_economics",  # NEW — Phase 23 (FinOps Unit Economics)
    "require_finops_budget_planning",  # NEW — Phase 24 (FinOps Budget Planning)
    "require_finops_vendor_management",  # NEW — Phase 25 (FinOps Vendor Management)
    "require_finops_cost_anomaly_ml_prediction",  # NEW — Phase 26 (FinOps Cost Anomaly ML Prediction)
]



require_launch_landing = require_capability(Capability.LAUNCH_LANDING)
require_launch_tos = require_capability(Capability.LAUNCH_TOS)
require_launch_support = require_capability(Capability.LAUNCH_SUPPORT)
require_launch_monitoring = require_capability(Capability.LAUNCH_MONITORING)
# Epic 16 — Tenant IdP admin management capability (F19.6 + AC #6.3).
# Gates the 5 CRUD routes in apps/api/modules/auth/sso/idp_admin_routes.py
# (GET/POST/PUT/DELETE/TEST). Industry-agnostic per CR 12-1 L4 precedent
# (mirrors SSO_ENTERPRISE / LISTEN_NOTIFY / AUTH_MIDDLEWARE / DEPLOYMENT_*
# / LAUNCH_* pattern). All 4 industries can manage their tenant IdP.
require_tenant_idp_management = require_capability(Capability.TENANT_IDP_MANAGEMENT)
# Epic 17 — Audit log viewer capability (F21.6 + AC #6.3 + AD-32 (g)).
# Gates the audit log viewer routes in
# apps/api/modules/audit/audit_log_routes.py (audit_log list / count /
# entry lookup / CSV export).
# (the activity route is NOT gated — activity stream is intentionally
# broad like Slack presence; PRD §F21.3 verbatim.) Industry-agnostic per
# CR 12-1 L4 precedent (mirrors MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER
# Phase 5 wire pattern + TENANT_IDP_MANAGEMENT Epic 16 wire +
# SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY 13/14 wire +
# AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire +
# DEPLOYMENT_* Phase 4 wire pattern verbatim). All 4 industries get
# audit log viewer capability.
require_audit_log_view = require_capability(Capability.AUDIT_LOG_VIEW)
# Phase 6 — Audit log retention capability (F22.6 + AC #6.3 + AD-33 (f)
# sub-decision). Gates the audit log retention routes in
# apps/api/modules/audit/retention/retention_routes.py (retention policy
# DSL CRUD + automatic purge job trigger + cold-archive action +
# GDPR Article 17 erasure endpoint). Industry-agnostic per CR 12-1 L4
# precedent (mirrors MULTI_REGION_BACKUP/FAILOVER Phase 5 wire +
# AUDIT_LOG_VIEW Epic 17 wire + TENANT_IDP_MANAGEMENT Epic 16 wire +
# SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY 13/14 wire +
# AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire +
# DEPLOYMENT_* Phase 4 wire pattern verbatim). All 4 industries get
# audit log retention capability (compliance baseline).
require_audit_log_retention = require_capability(Capability.AUDIT_LOG_RETENTION)
# Phase 7 — Observability stack capability (F23.6 + AC #6.3 + AD-34 (f)
# sub-decision). Gates the observability stack routes:
# - `require_observability_traces` — gates trace_id lookup + alert ack +
#   PagerDuty owner-only manual trigger routes (F23.1 + F23.3 + AD-22).
# - `require_observability_metrics` — gates /api/v1/metrics Prometheus
#   exposition format endpoint + Grafana dashboard embed routes (F23.2).
# Industry-agnostic per CR 12-1 L4 precedent (mirrors AUDIT_LOG_RETENTION
# Phase 6 wire + AUDIT_LOG_VIEW Epic 17 wire + MULTI_REGION_BACKUP/
# FAILOVER Phase 5 wire + TENANT_IDP_MANAGEMENT Epic 16 wire +
# SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY 13/14 wire +
# AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire +
# DEPLOYMENT_* Phase 4 wire pattern verbatim). All 4 industries get
# observability traces + metrics capabilities (operational observability
# baseline, not industry-specific).
require_observability_traces = require_capability(Capability.OBSERVABILITY_TRACES)
require_observability_metrics = require_capability(Capability.OBSERVABILITY_METRICS)
# Phase 8 — Performance / Load Testing capability (F24.6 + AC #6.3 +
# AD-35 (g) sub-decision). Gates the performance / load testing routes
# in apps/api/modules/performance_testing/performance_routes.py:
# - `POST /api/v1/performance-testing/load-tests` — manual k6 load test
#   trigger (AD-22 owner-only RBAC + Epic 12 2FA 챌린지 보존)
# - `GET /api/v1/performance-testing/load-tests/{run_id}` — k6 load test
#   status lookup
# - `GET /api/v1/performance-testing/slo/dashboard` — SLO dashboard view
# - `POST /api/v1/performance-testing/slo/modify` — SLO manual modify
#   (AD-22 owner-only RBAC + Epic 12 2FA 챌린지 보존)
# - `POST /api/v1/performance-testing/latency-regression/invalidate` —
#   latency regression manual trigger (AD-22 owner-only RBAC + Epic 12
#   2FA 챌린지 보존)
# - `POST /api/v1/performance-testing/cost-engine-benchmark/invalidate` —
#   cost-engine benchmark V8 manual invalidate (AD-22 owner-only RBAC +
#   Epic 12 2FA 챌린지 보존)
# Industry-agnostic per CR 12-1 L4 precedent (mirrors OBSERVABILITY_*
# Phase 7 wire + AUDIT_LOG_RETENTION Phase 6 wire + AUDIT_LOG_VIEW Epic
# 17 wire + MULTI_REGION_BACKUP/FAILOVER Phase 5 wire +
# TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire +
# LISTEN_NOTIFY 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_*
# 1st release wire + DEPLOYMENT_* Phase 4 wire pattern verbatim).
# All 4 industries get PERFORMANCE_TESTING capability (performance /
# observability baseline, not industry-specific). Drift detector lives
# at tests/integration/test_capability_matrix_v1_33_drift.py.
require_performance_testing = require_capability(Capability.PERFORMANCE_TESTING)
# Phase 9 — Chaos Engineering capability (F25.6 + AC #6.3 + AD-36 (g)
# sub-decision). Gates the chaos engineering routes in
# apps/api/modules/chaos/ routes (chaos experiment trigger + manual
# abort + auto-rollback + chaos_game_day + continuous_chaos +
# multi-region chaos + tenant-scoped chaos). Industry-agnostic per
# CR 12-1 L4 precedent (mirrors PERFORMANCE_TESTING Phase 8 wire +
# OBSERVABILITY_* Phase 7 wire + AUDIT_LOG_RETENTION Phase 6 wire +
# AUDIT_LOG_VIEW Epic 17 wire + MULTI_REGION_BACKUP/FAILOVER Phase 5
# wire + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15
# wire + LISTEN_NOTIFY 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire +
# LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern
# verbatim). All 4 industries get CHAOS_ENGINEERING capability
# (operational resilience baseline, not industry-specific). Drift
# detector lives at tests/integration/test_capability_matrix_v1_34_drift.py.
require_chaos_engineering = require_capability(Capability.CHAOS_ENGINEERING)
# Phase 10 — SLO Engineering / Error Budget Management capability
# (F26.6 + AC #6.3 + AD-37 (g) sub-decision). Gates the SLO routes in
# apps/api/modules/slo/ routes (SLO definition create/update/delete +
# multi-region aggregation + tenant-scoped override + error budget
# freeze/unfreeze + governance review + SLO breach auto-rollback
# trigger + dry-run mode). Industry-agnostic per CR 12-1 L4 precedent
# (mirrors CHAOS_ENGINEERING Phase 9 wire + PERFORMANCE_TESTING Phase 8
# wire + OBSERVABILITY_* Phase 7 wire + AUDIT_LOG_RETENTION Phase 6 wire
# + AUDIT_LOG_VIEW Epic 17 wire + MULTI_REGION_BACKUP/FAILOVER Phase 5
# wire pattern verbatim). All 4 industries get SLO_ENGINEERING
# capability (operational resilience baseline, not industry-specific).
# Drift detector lives at
# tests/integration/test_capability_matrix_v1_35_drift.py.
require_slo_engineering = require_capability(Capability.SLO_ENGINEERING)
# Phase 11 — FinOps Showback / Chargeback capability (F27.6 + AC #6.3
# + AD-38 (g) sub-decision). Gates the FinOps routes in
# apps/api/modules/finops/ (showback generation + department mapping
# update + chargeback calculation + CSV/PDF export + dry-run mode).
# Industry-agnostic per CR 12-1 L4 precedent (mirrors SLO_ENGINEERING
# Phase 10 wire + CHAOS_ENGINEERING Phase 9 wire + PERFORMANCE_TESTING
# Phase 8 wire + OBSERVABILITY_* Phase 7 wire + AUDIT_LOG_RETENTION
# Phase 6 wire + AUDIT_LOG_VIEW Epic 17 wire +
# MULTI_REGION_BACKUP/FAILOVER Phase 5 wire pattern verbatim). All 4
# industries get FINOPS_SHOWBACK + FINOPS_CHARGEBACK capability
# (financial reporting baseline, not industry-specific). Drift detector
# lives at tests/integration/test_capability_matrix_v1_36_drift.py.
require_finops_showback = require_capability(Capability.FINOPS_SHOWBACK)
require_finops_chargeback = require_capability(Capability.FINOPS_CHARGEBACK)
# Phase 12 (cj-style 111번째 wire) — BACKFILL FinOps anomaly + budget
# alert capability gate dependencies (Phase 12 wire added Capability
# enum entries but skipped dep helpers; this is honest recovery per
# cj-style 115번째 atomic commit). Industry-agnostic per CR 12-1 L4
# precedent (mirrors FINOPS_SHOWBACK + FINOPS_CHARGEBACK Phase 11 wire +
# OBSERVABILITY_* Phase 7 wire + SLO_ENGINEERING Phase 10 wire pattern
# verbatim). Gates the FinOps anomaly + budget alert routes in
# apps/api/modules/finops/ (anomaly detection + budget definition +
# budget alert routing).
require_finops_anomaly_detection = require_capability(Capability.FINOPS_ANOMALY_DETECTION)
require_finops_budget_alert = require_capability(Capability.FINOPS_BUDGET_ALERT)
# Phase 13 (cj-style 115번째 wire) — FinOps Forecasting & Capacity
# Planning capability (F29.6 + AC #6.3 + AD-39 (g) sub-decision).
# Gates the FinOps forecast routes in apps/api/modules/finops/
# (forecast_definition + forecast_engine + capacity_headroom +
# budget_burnrate + forecast_accuracy_tracker). Industry-agnostic per
# CR 12-1 L4 precedent (mirrors FINOPS_ANOMALY_DETECTION +
# FINOPS_BUDGET_ALERT Phase 12 wire + FINOPS_SHOWBACK +
# FINOPS_CHARGEBACK Phase 11 wire + SLO_ENGINEERING Phase 10 wire
# pattern verbatim). All 4 industries get FINOPS_FORECASTING_CAPACITY_
# PLANNING capability (financial forecasting baseline, not industry-
# specific). Drift detector lives at
# tests/integration/test_capability_matrix_v1_39_drift.py.
require_finops_forecast = require_capability(Capability.FINOPS_FORECASTING_CAPACITY_PLANNING)

# Phase 14 (cj-style 119번째 wire) — FINOPS_OPTIMIZATION dependency
# (optimization_definition + rightsizing_engine + idle_resource_detector
# + commitment_recommender + optimization_accuracy_tracker). Gates
# /admin/finops/optimization/* endpoints. Industry-agnostic (CR 12-1 L4
# precedent mirrors FINOPS_FORECASTING_CAPACITY_PLANNING Phase 13 wire
# + FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire +
# FINOPS Phase 11 wire pattern verbatim). All 4 industries get
# FINOPS_OPTIMIZATION capability (ACTIONABLE RECOMMENDATION LAYER
# EXTENSION of Phase 13 forecast baseline). Drift detector lives at
# tests/integration/test_capability_matrix_v1_40_drift.py.
require_finops_optimization = require_capability(Capability.FINOPS_OPTIMIZATION)

# Phase 15 (cj-style 123번째 wire) — FINOPS_TAG_GOVERNANCE dependency
# (tag_policy_dsl + untagged_resource_detector + allocation_rules_engine
# + allocation_audit + chargeback_allocation_reconciliation). Gates
# /admin/finops/tag-governance/* + /admin/finops/allocation/* endpoints.
# Industry-agnostic (CR 12-1 L4 precedent mirrors FINOPS_OPTIMIZATION
# Phase 14 wire + FINOPS_FORECASTING_CAPACITY_PLANNING Phase 13 wire +
# FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire + FINOPS
# Phase 11 wire pattern verbatim). All 4 industries get
# FINOPS_TAG_GOVERNANCE capability (financial cost allocation baseline).
# Drift detector lives at tests/integration/test_capability_matrix_v1_41_drift.py.
require_finops_tag_governance = require_capability(Capability.FINOPS_TAG_GOVERNANCE)

# Phase 16 (cj-style 127번째 wire) — FINOPS_REPORTING dependency
# (executive_dashboard_aggregator + cross_module_kpi +
# executive_report_generator + scheduled_executive_dispatch +
# executive_report_delivery). Gates /admin/finops/executive-dashboard/*
# endpoints (dashboard view + KPI selector + report generation panel +
# scheduled dispatch config + compliance trend). Industry-agnostic
# (CR 12-1 L4 precedent mirrors FINOPS_TAG_GOVERNANCE Phase 15 wire +
# FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING_CAPACITY_PLANNING
# Phase 13 wire + FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12
# wire + FINOPS Phase 11 wire pattern verbatim). All 4 industries get
# FINOPS_REPORTING capability (financial reporting baseline). Drift
# detector lives at tests/integration/test_capability_matrix_v1_42_drift.py.
require_finops_reporting = require_capability(Capability.FINOPS_REPORTING)


# Phase 17 (cj-style 131번째 wire) — FINOPS_SUSTAINABILITY dependency
# (carbon_emissions_aggregator + sustainability_kpi_selector +
# sustainability_report_generator + scheduled_sustainability_dispatch +
# sustainability_report_archive). Gates /admin/finops/sustainability/*
# endpoints (dashboard view + KPI selector + report generation panel +
# scheduled dispatch config + compliance trend). Industry-agnostic
# (CR 12-1 L4 precedent mirrors FINOPS_REPORTING Phase 16 wire +
# FINOPS_TAG_GOVERNANCE Phase 15 wire + FINOPS_OPTIMIZATION Phase 14 wire
# + FINOPS_FORECASTING_CAPACITY_PLANNING Phase 13 wire +
# FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire + FINOPS
# Phase 11 wire pattern verbatim). All 4 industries get
# FINOPS_SUSTAINABILITY capability (sustainability & carbon reporting
# baseline — EU CSRD + SEC Climate Disclosure + EU Taxonomy + IFRS S2 +
# 한국 KSSB regulatory driver industry-agnostic). Drift detector lives
# at tests/integration/test_capability_matrix_v1_43_drift.py.
require_finops_sustainability = require_capability(Capability.FINOPS_SUSTAINABILITY)
# Phase 18 (cj-style 135번째 wire) — require_finops_commitment
# (industry-agnostic per CR 12-1 L4 precedent + FINOPS_SUSTAINABILITY
# Phase 17 wire + FINOPS_REPORTING Phase 16 wire +
# FINOPS_TAG_GOVERNANCE Phase 15 wire + FINOPS_OPTIMIZATION Phase 14 wire
# + FINOPS_FORECASTING_CAPACITY_PLANNING Phase 13 wire +
# FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire + FINOPS
# Phase 11 wire pattern verbatim). All 4 industries get
# FINOPS_COMMITMENT capability (cloud commitment management baseline —
# FinOps Foundation + AWS Cost Optimization Pillar + Azure Cost
# Optimization + GCP Cost Optimization + 한국 조달청 클라우드 commitment
# 가이드라인 regulatory driver industry-agnostic). Drift detector lives
# at tests/integration/test_capability_matrix_v1_44_drift.py.
require_finops_commitment = require_capability(Capability.FINOPS_COMMITMENT)

# Phase 19 (cj-style 139번째 wire) — require_finops_pricing
# (industry-agnostic per CR 12-1 L4 precedent + FINOPS_COMMITMENT Phase
# 18 wire + FINOPS_SUSTAINABILITY Phase 17 wire + FINOPS_REPORTING
# Phase 16 wire + FINOPS_TAG_GOVERNANCE Phase 15 wire +
# FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING_CAPACITY_PLANNING
# Phase 13 wire + FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT
# Phase 12 wire + FINOPS Phase 11 wire pattern verbatim). All 4
# industries get FINOPS_PRICING capability (pricing & TCO modeling
# baseline — FinOps Foundation + AWS Pricing Models EDP + Azure Pricing
# Calculator EA + GCP Pricing Calculator CUD + 한국 공공 조달 가격
# 가이드라인 regulatory driver industry-agnostic). Drift detector lives
# at tests/integration/test_capability_matrix_v1_45_drift.py.
require_finops_pricing = require_capability(Capability.FINOPS_PRICING)

# Phase 20 (cj-style 144번째 wire) — require_finops_multi_cloud
# (industry-agnostic per CR 12-1 L4 precedent + FINOPS_PRICING Phase 19
# wire + FINOPS_COMMITMENT Phase 18 wire + FINOPS_SUSTAINABILITY Phase 17
# wire + FINOPS_REPORTING Phase 16 wire + FINOPS_TAG_GOVERNANCE Phase 15
# wire + FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING Phase 13
# wire + FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire +
# FINOPS Phase 11 wire pattern verbatim). All 4 industries get
# FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION capability (multi-cloud
# cost unified reconciliation baseline — FinOps Foundation Multi-Cloud
# Cost Management pillar + 5 cloud provider cross-rollup + 5 marketplace
# source pattern + AWS EDP + Azure EA + GCP CUD Pricing + Naver Cloud
# Volume Tier + KT Cloud Volume Tier regulatory driver industry-agnostic).
# Drift detector lives at
# tests/integration/test_capability_matrix_v1_46_drift.py.
require_finops_multi_cloud = require_capability(
    Capability.FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION
)

# Phase 21 (cj-style 151번째 wire) — require_finops_reserved_capacity
# (industry-agnostic per CR 12-1 L4 precedent + FINOPS_MULTI_CLOUD
# Phase 20 wire + FINOPS_PRICING Phase 19 wire + FINOPS_COMMITMENT
# Phase 18 wire + FINOPS_SUSTAINABILITY Phase 17 wire +
# FINOPS_REPORTING Phase 16 wire + FINOPS_TAG_GOVERNANCE Phase 15 wire +
# FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING Phase 13 wire +
# FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire +
# FINOPS Phase 11 wire pattern verbatim). All 4 industries get
# FINOPS_RESERVED_CAPACITY_PLANNING capability (reserved capacity
# planning baseline — FinOps Foundation Reserved Capacity Planning
# pillar + 5-module composition layer pattern industry-agnostic).
# Gates the FinOps reserved capacity routes in
# apps/api/modules/finops/reserved_capacity/reserved_capacity_routes.py
# (healthcheck + demand-forecast + capacity-plan +
# commitment-recommendation + orchestrate + dispatches +
# cadence-preview + dry-run). Drift detector lives at
# tests/integration/test_capability_matrix_v1_47_drift.py.
require_finops_reserved_capacity = require_capability(
    Capability.FINOPS_RESERVED_CAPACITY_PLANNING
)

# Phase 22 (cj-style 160번째 wire) — require_finops_chargeback_settlement
# (industry-agnostic per CR 12-1 L4 precedent + FINOPS_RESERVED_CAPACITY
# Phase 21 wire + FINOPS_MULTI_CLOUD Phase 20 wire + FINOPS_PRICING Phase 19
# wire + FINOPS_COMMITMENT Phase 18 wire + FINOPS_SUSTAINABILITY Phase 17 wire +
# FINOPS_REPORTING Phase 16 wire + FINOPS_TAG_GOVERNANCE Phase 15 wire +
# FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING Phase 13 wire +
# FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire + FINOPS
# Phase 11 wire pattern verbatim). All 4 industries get
# FINOPS_CHARGEBACK_SETTLEMENT capability (settlement layer wiring is a
# business-level FinOps pillar per FinOps Foundation + 5-module cross-join
# composition layer + 5-dim weighted allocation + PDF/XLSX/CSV invoice
# generation + 3-way match reconciliation + scheduled dispatch + dry-run
# mode + Epic 12 2FA 챌린지 mandatory). Gates the FinOps chargeback
# settlement routes in
# apps/api/modules/finops/chargeback_settlement/chargeback_settlement_routes.py
# (settlement-rules CRUD + allocation compute + invoice generation +
# reconciliation + dispatch + cadence-preview + dry-run). Drift detector
# lives at tests/integration/test_capability_matrix_v1_48_drift.py.
require_finops_chargeback_settlement = require_capability(
    Capability.FINOPS_CHARGEBACK_SETTLEMENT
)

# Phase 23 (cj-style 164번째 wire) — require_finops_unit_economics
# (industry-agnostic per CR 12-1 L4 precedent + FINOPS_CHARGEBACK_SETTLEMENT
# Phase 22 wire + FINOPS_RESERVED_CAPACITY Phase 21 wire + FINOPS_MULTI_CLOUD
# Phase 20 wire + FINOPS_PRICING Phase 19 wire + FINOPS_COMMITMENT Phase 18
# wire + FINOPS_SUSTAINABILITY Phase 17 wire + FINOPS_REPORTING Phase 16
# wire + FINOPS_TAG_GOVERNANCE Phase 15 wire + FINOPS_OPTIMIZATION Phase 14
# wire + FINOPS_FORECASTING Phase 13 wire + FINOPS_ANOMALY_DETECTION +
# FINOPS_BUDGET_ALERT Phase 12 wire + FINOPS Phase 11 wire pattern verbatim).
# All 4 industries get FINOPS_UNIT_ECONOMICS capability (unit economics
# derived metric layer is a business-level FinOps pillar per FinOps Foundation
# + 4-NEW-module composition layer: unit_economics_engine +
# cost_per_business_unit + cost_per_transaction + margin_analysis +
# scheduled_unit_economics_calculation_job — derived from Phase 22
# allocation_lines ledger data via 5-dim cross-join + ledger-key dedup +
# 5-dim rollup + 3 NEW tag filter dimensions + OPTIONAL margin analysis
# + dry-run mode + 1 NEW CLI flag `--finops-unit-economics-dry-run` +
# Epic 12 2FA 챌린지 mandatory for high-value margin positive ≥ 10M
# KRW/year + cost_per_transaction override ≥ 10M KRW/year). Gates the
# FinOps unit economics routes in
# apps/api/modules/finops/unit_economics/unit_economics_routes.py
# (compute-unit-economics + refresh-cost-per-business-unit +
# compute-cost-per-transaction + execute-margin-analysis + dry-run +
# trend + healthcheck + cadence-preview). Drift detector lives at
# tests/integration/test_capability_matrix_v1_49_drift.py.
require_finops_unit_economics = require_capability(
    Capability.FINOPS_UNIT_ECONOMICS
)

# Phase 24 (cj-style 169번째 wire) — require_finops_budget_planning
# (industry-agnostic per CR 12-1 L4 precedent + FINOPS_UNIT_ECONOMICS
# Phase 23 wire + FINOPS_CHARGEBACK_SETTLEMENT Phase 22 wire +
# FINOPS_RESERVED_CAPACITY Phase 21 wire + FINOPS_MULTI_CLOUD Phase 20
# wire + FINOPS_PRICING Phase 19 wire + FINOPS_COMMITMENT Phase 18
# wire + FINOPS_SUSTAINABILITY Phase 17 wire + FINOPS_REPORTING Phase 16
# wire + FINOPS_TAG_GOVERNANCE Phase 15 wire + FINOPS_OPTIMIZATION
# Phase 14 wire + FINOPS_FORECASTING Phase 13 wire +
# FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire +
# FINOPS Phase 11 wire pattern verbatim). All 4 industries get
# FINOPS_BUDGET_PLANNING capability (budget planning pre-allocation
# layer is a business-level FinOps pillar per FinOps Foundation +
# 5-NEW-module composition layer: budget_plan_engine +
# budget_allocation + budget_approval_workflow + budget_vs_actual +
# budget_alert + scheduled_budget_planning_job — derived from Phase 22
# allocation_lines ledger + Phase 23 unit_economics_results ledger
# data via 5-dim cross-join + 5-dim weighted allocation + sequential
# approval chain + Epic 12 2FA 챌린지 mandatory for high-value ≥ 10M
# KRW/year + over-budget detection warning 10% + critical 25% +
# auto-escalation chain + dry-run mode + 2 NEW CLI flags
# `--finops-budget-planning-dry-run` +
# `--finops-budget-planning-over-budget-alert-dry-run`). Gates the
# FinOps budget planning routes in
# apps/api/modules/finops/budget_planning/budget_planning_routes.py
# (create-plan + list-plans + get-plan + update-plan + allocate +
# submit-approval + approve-step + vs-actual + alert-trigger). Drift
# detector lives at
# tests/integration/test_capability_matrix_v1_50_drift.py.
require_finops_budget_planning = require_capability(
    Capability.FINOPS_BUDGET_PLANNING
)

# Phase 25 (cj-style 174th follow-up wire) — require_finops_vendor_management
# (industry-agnostic per CR 12-1 L4 precedent + FINOPS_BUDGET_PLANNING
# Phase 24 wire + FINOPS_UNIT_ECONOMICS Phase 23 wire +
# FINOPS_CHARGEBACK_SETTLEMENT Phase 22 wire + FINOPS_RESERVED_CAPACITY
# Phase 21 wire + FINOPS_MULTI_CLOUD Phase 20 wire + FINOPS_PRICING Phase
# 19 wire + FINOPS_COMMITMENT Phase 18 wire + FINOPS_SUSTAINABILITY Phase
# 17 wire + FINOPS_REPORTING Phase 16 wire + FINOPS_TAG_GOVERNANCE Phase
# 15 wire + FINOPS_OPTIMIZATION Phase 14 wire + FINOPS_FORECASTING Phase
# 13 wire + FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire
# + FINOPS Phase 11 wire pattern verbatim). All 4 industries get
# FINOPS_VENDOR_MANAGEMENT capability (vendor management post-budget-
# allocation close-loop layer is a business-level FinOps pillar per
# FinOps Foundation + 5-NEW-module composition layer:
# vendor_catalog_engine + vendor_selection_engine +
# vendor_contract_lifecycle_engine + vendor_performance_evaluation +
# vendor_spend_attribution + scheduled_vendor_management_jobs — derived
# from Phase 14 optimization + Phase 18 commitment + Phase 19 pricing +
# Phase 22 settlement + Phase 23 unit_economics + Phase 24 budget_plan
# ledger data via 5-dim weighted vendor selection scoring (cost 0.30 +
# performance 0.25 + reliability 0.20 + compliance 0.15 + strategic_fit
# 0.10) + 4-dim vendor performance scoring (sla_compliance 0.30 +
# cost_efficiency 0.25 + support_quality 0.25 + innovation 0.20) +
# sequential contract lifecycle (draft → pending_approval → approved →
# active → expiring_soon → renewed/expired/terminated) + Epic 12 2FA
# 챌린지 mandatory for high-value ≥ 10M KRW/year + vendor_blacklist
# compliance gate + cross-budget reconciliation + 4 cadence KST pytz +
# dry-run mode + 1 NEW CLI flag `--finops-vendor-management-dry-run` +
# 12 NEW audit actions + 16 NEW typed exceptions + 9 NEW endpoints).
# Gates the FinOps vendor management routes in
# apps/api/modules/finops/vendor_management/vendor_management_routes.py
# (create-vendor + list-vendors + get-vendor + update-vendor + blacklist
# + run-selection + create-contract + advance-contract + dry-run).
# Drift detector lives at
# tests/integration/test_capability_matrix_v1_51_drift.py.
require_finops_vendor_management = require_capability(
    Capability.FINOPS_VENDOR_MANAGEMENT
)

# Phase 26 (cj-style 185번째 wire) — require_finops_cost_anomaly_ml_prediction
# (industry-agnostic per CR 12-1 L4 precedent + FINOPS_VENDOR_MANAGEMENT
# Phase 25 wire + FINOPS_BUDGET_PLANNING Phase 24 wire +
# FINOPS_UNIT_ECONOMICS Phase 23 wire + FINOPS_CHARGEBACK_SETTLEMENT Phase
# 22 wire + FINOPS_RESERVED_CAPACITY_PLANNING Phase 21 wire +
# FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION Phase 20 wire +
# FINOPS_PRICING Phase 19 wire + FINOPS_COMMITMENT Phase 18 wire +
# FINOPS_SUSTAINABILITY Phase 17 wire + FINOPS_REPORTING Phase 16 wire +
# FINOPS_TAG_GOVERNANCE Phase 15 wire + FINOPS_OPTIMIZATION Phase 14 wire
# + FINOPS_FORECASTING_CAPACITY_PLANNING Phase 13 wire +
# FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire + FINOPS
# Phase 11 wire pattern verbatim). All 4 industries get
# FINOPS_COST_ANOMALY_ML_PREDICTION capability (ML-driven pre-detection
# layer is a business-level FinOps pillar per FinOps Foundation + Phase 11
# showback + Phase 12 anomaly + Phase 13 forecasting + Phase 14
# optimization + Phase 22 settlement + Phase 23 unit_economics + Phase 24
# budget_vs_actual + Phase 25 vendor spend attribution ledger data reuse
# 최대화 → 새 backend infra 불필요). 4-NEW-module composition layer
# (anomaly_ml_prediction_engine + anomaly_ml_model_registry +
# anomaly_ml_training_pipeline + anomaly_ml_scoring +
# anomaly_ml_ensemble_consensus) + 5 model types ensemble (prophet 0.30 +
# lstm 0.30 + arima 0.15 + isolation_forest 0.15 + autoencoder 0.10) +
# model_registry semver + A/B testing champion/challenger traffic_split
# default 50/50 + 3 drift detection types (data + concept + prediction
# PSI threshold 0.25) + training_pipeline 8 features +
# scheduled retraining KST 매주 일요일 03:00 + drift-triggered
# auto-retraining + real-time inference P95 < 200ms + batch inference
# nightly KST 02:00 + ML vs Phase 12 threshold detection comparison view
# + audit-first INSERT 12 NEW Literal + 16 NEW typed exceptions CR 12-5
# D-14 envelope + dry-run mode + 1 NEW CLI flag
# `--finops-cost-anomaly-ml-prediction-dry-run` + Epic 12 2FA 챌린지
# mandatory (high-value threshold 10M KRW/year AD-55 (g)). Gates the
# FinOps cost anomaly ML prediction routes in
# apps/api/modules/finops/cost_anomaly_ml_prediction/ (healthcheck +
# predict-anomaly-score + batch-predict + register-model +
# update-model-status + train-model + drift-detection + ab-test +
# dry-run + cadence-preview + ensemble-consensus). Drift detector lives
# at tests/integration/test_capability_matrix_v1_52_drift.py.
require_finops_cost_anomaly_ml_prediction = require_capability(
    Capability.FINOPS_COST_ANOMALY_ML_PREDICTION
)

