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
