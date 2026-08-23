# Grafana Dashboards — Observability Stack

Phase 7 (cj-style 91번째 wire) — Observability Stack 강화 territory.
PRD §F23.2 + AC #2 + AD-34 (b) sub-decision.

This document specifies the 4 NEW Grafana dashboards wired to the
Prometheus custom metrics exposed at `/api/v1/metrics` (apps/api/core/metrics.py).

**Label cardinality invariant (CRITICAL):** only enum-bound labels are
allowed. Free-form `tenant_id` labels are EXPLICITLY FORBIDDEN
(Prometheus cardinality explosion + NFR4 PII minimization + tenant info
leakage prevention). See `apps/api/core/metrics.py:_validate_labels()`.

---

## Dashboard 1: `business-signups.json`

Tenant signup velocity across industry × plan.

**Panels:**

| Row | Panel | Type | Query |
|-----|-------|------|-------|
| 1 | Signups by Industry | piechart | `sum by (industry) (business_signups_total)` |
| 1 | Signups by Plan | barchart | `sum by (plan) (business_signups_total)` |
| 1 | Signup Velocity (last 24h) | timeseries | `sum(increase(business_signups_total[24h]))` |
| 2 | Industry × Plan Heatmap | heatmap | `sum by (industry, plan) (increase(business_signups_total[1h]))` |

**Refresh interval:** 30s
**Alerting rule:** none (read-only dashboard).

---

## Dashboard 2: `cost-engine-performance.json`

Cost engine execution latency + outcome distribution.

**Panels:**

| Row | Panel | Type | Query |
|-----|-------|------|-------|
| 1 | p50/p95/p99 Latency | timeseries | `histogram_quantile(0.5/0.95/0.99, sum by (le) (rate(business_cost_engine_duration_seconds_bucket[5m])))` |
| 1 | Latency by Engine | timeseries | `histogram_quantile(0.95, sum by (le, engine) (rate(business_cost_engine_duration_seconds_bucket[5m])))` |
| 1 | Latency by Tenant Size Bucket | timeseries | `histogram_quantile(0.95, sum by (le, tenant_size_bucket) (rate(business_cost_engine_duration_seconds_bucket[5m])))` |
| 2 | Calc Outcome Distribution | piechart | `sum by (engine, outcome) (business_calculations_total)` |
| 2 | Calc Throughput | timeseries | `sum(rate(business_calculations_total[1m]))` |
| 2 | p95 vs SLO (30s) | stat | `histogram_quantile(0.95, sum by (le) (rate(business_cost_engine_duration_seconds_bucket[5m])))` |
| 3 | SlowCalc Alert Status | stat | `ALERTS{alertname="SlowCalc", alertstate="firing"}` |

**Refresh interval:** 10s
**Alerting rule:** `SlowCalc` (PRD §F23.3) — fires at p99 > 5s for 10m.

---

## Dashboard 3: `auth-flow.json`

Login events across method × outcome.

**Panels:**

| Row | Panel | Type | Query |
|-----|-------|------|-------|
| 1 | Login Success Rate | stat | `sum(rate(business_logins_total{outcome="success"}[5m])) / sum(rate(business_logins_total[5m]))` |
| 1 | Logins by Method | barchart | `sum by (method) (business_logins_total)` |
| 1 | Failed Login Spike | timeseries | `sum(rate(business_logins_total{outcome="failure"}[1m]))` |
| 2 | Magic Link vs Password | piechart | `sum by (method) (business_logins_total{outcome="success"})` |
| 2 | SSO/SAML Adoption | stat | `sum(increase(business_logins_total{method="sso_saml"}[24h]))` |
| 2 | Service Role Bypass Rate | timeseries | `sum(rate(business_logins_total{method="service_role"}[5m]))` |
| 3 | HighErrorRate Alert Status | stat | `ALERTS{alertname="HighErrorRate", alertstate="firing"}` |

**Refresh interval:** 30s
**Alerting rule:** `HighErrorRate` (PRD §F23.3) — fires at 5xx > 5% for 5m.

---

## Dashboard 4: `audit-log-purge.json`

Audit log retention purge cadence (Phase 6 wire `24e1cd7` carry-over).

**Panels:**

| Row | Panel | Type | Query |
|-----|-------|------|-------|
| 1 | Purge Events by Action Class | barchart | `sum by (action_class) (business_audit_log_purge_total)` |
| 1 | Purge Velocity (last 7d) | timeseries | `sum(increase(business_audit_log_purge_total[7d]))` |
| 1 | Last Purge Success | stat | `time() - phase_6_audit_purge_last_success_timestamp` |
| 2 | Audit Log Retention Cohort | timeseries | `audit_log_count_by_retention_class` (Phase 6 carry-over) |
| 2 | Archive Storage Growth | timeseries | `sum(audit_log_archive_count) by (region)` (Phase 6 + Phase 5 multi-region) |
| 2 | GDPR Erasure Events | stat | `sum(increase(business_audit_log_purge_total{action_class="audit"}[24h]))` |
| 3 | RetentionPurgeFailed Alert Status | stat | `ALERTS{alertname="RetentionPurgeFailed", alertstate="firing"}` |

**Refresh interval:** 1m
**Alerting rule:** `RetentionPurgeFailed` (PRD §F23.3) — fires at last success > 26h.

---

## Multi-Region Carry-over

Both `cost-engine-performance.json` and `audit-log-purge.json` dashboards
include panels that reference Phase 5 wire `f093f8c` multi-region
metrics (`phase_5_replication_lag_seconds` + `up{job="supabase-primary/
secondary"}`). The `MultiRegionDown` alert (PRD §F23.3) is wired
across both dashboards as a top-level banner.

---

## Active Tenants (cross-dashboard widget)

A single `business_active_tenants_gauge` stat widget appears in the
header of all 4 dashboards to provide cross-cutting tenant count context
(no PII — aggregate count only).

---

## Endpoints

- `/api/v1/metrics` — Prometheus exposition format (apps/api/main.py EXTENSION).
- `/api/v1/observability/alerts/webhook` — AlertManager ingress
  (apps/api/main.py EXTENSION).
- `/api/v1/observability/alerts/ack` — alert ack route
  (gated by `require_observability_traces`).

---

## Drift Detection

`tests/api/core/test_phase_7_metrics.py` (T7 backend test) enforces:

1. BusinessMetric enum ↔ Prometheus collector parity (7 metrics).
2. Label cardinality allow-list enforcement (7 sets).
3. OTEL_SDK_DISABLED no-op TracerProvider fallback mirror.
4. render_metrics() returns (bytes, content_type) tuple correctly.

`tests/integration/test_capability_matrix_v1_32_drift.py` (T5
integration test) enforces capability matrix v1.32 EXTENSION 2 NEW rows
(`OBSERVABILITY_TRACES` + `OBSERVABILITY_METRICS`) parity.
