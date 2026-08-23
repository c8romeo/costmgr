# SLO/SLI Definitions — Phase 8 Performance/Load Testing territory

> **Phase 8 (cj-style 95번째 epic 연속 정직 회복 atomic docs-and-source wire)**
> — Performance/Load Testing territory (PRD §F24.2 + AC #2.1~#2.12).
>
> **Baseline_commit**: `ced452f` (Phase 8 PRD entry)
> **Story**: phase-8-performance-load-testing-wire
> **Drift detector**: tests/api/core/test_phase_8_slo_sli.py (4 NEW pytest cases PASS)

## Purpose

This document is the **single source of truth (SSOT)** for SLO/SLI definitions
that gate the Phase 8 Performance/Load Testing territory. Each SLA below
maps to one of the 4 canonical k6 scenarios (see `apps/api/tests/load/k6/`)
and one of the alert rules in `apps/api/config/alert_rules.yaml` (Phase 7
wire `59b56cd` carry-over).

## SLO/SLI table

| SLA | Endpoint / Surface | Target | Window | Error Budget | Alert Rule |
|-----|--------------------|--------|--------|--------------|------------|
| **SLA-1** | Cost calculation (`POST /api/v1/cost-engine/compute`) | **p99 < 5s** | 30d rolling | 5% (1.5h/month burn) | `SLOBurnRate` (Phase 7 alert wiring) |
| **SLA-2** | Audit log query (`GET /api/v1/audit-log`) | **p99 < 2s** | 30d rolling | 5% (1.5h/month burn) | `SLOBurnRate` |
| **SLA-3** | Login (`POST /api/v1/auth/login`) | **p99 < 1s** | 30d rolling | 5% (1.5h/month burn) | `SLOBurnRate` |
| **SLA-4** | Multi-region failover (RTO) | **RTO < 30s** | 30d rolling | 5% (1.5h/month burn) | `FailoverStuck` (Phase 5 wire carry-over) |

All 4 SLAs share the **30-day rolling window** measurement cadence.
The 95% target over 30 days = 5% error budget = 1.5h/month of permitted
burn before `SLOBurnRate` critical alert fires.

## SLA details

### SLA-1 — Cost calculation p99 < 5s

**Endpoint**: `POST /api/v1/cost-engine/compute` (Epic 9 m3_calculate +
m9_abc dual-route per AD-19).

**Baseline source**: Phase 7 wire `59b56cd` Prometheus histogram
`business_cost_engine_duration_seconds{engine,tenant_size_bucket}`
p99 baseline (verbatim migrate).

**Measurement**: k6 scenario `cost-calculation.js` (50 VU ramp 60s +
sustain 60s + drain 10s) runs every night at 02:00 KST via
`.github/workflows/load-test.yml` schedule trigger.

**Owner**: Phase 8 owner-only RBAC (AD-22 + Epic 12 2FA 챌린지 보존)
for manual SLO modify via `POST /api/v1/performance-testing/slo/modify`.

**Audit trail**: `slo_modified` action_class=`PERFORMANCE_TEST` audit-first
INSERT BEFORE any manual SLO target change (CR 1-1 verbatim).

### SLA-2 — Audit log query p99 < 2s

**Endpoint**: `GET /api/v1/audit-log` (Epic 17 wire `2ada2ec` carry-over).

**Baseline source**: Epic 17 wire `2ada2ec` `audit_log_query` benchmark
result_hash + Phase 6 wire `24e1cd7` retention integration.

**Measurement**: k6 scenario `audit-log-query.js` (20 VU ramp 30s).

**Owner**: Phase 8 owner-only RBAC.

**Audit trail**: `slo_modified` audit-first INSERT.

### SLA-3 — Login p99 < 1s

**Endpoint**: `POST /api/v1/auth/login` (Phase 3 wire `1db21d2` auth
contract + Epic 15 wire `5f9e37f` Magic link + OAuth + SSO unified).

**Baseline source**: Phase 3 wire `1db21d2` auth contract baseline.

**Measurement**: k6 scenario `auth-login.js` (100 VU ramp 30s).

**Owner**: Phase 8 owner-only RBAC.

**Audit trail**: `slo_modified` audit-first INSERT.

### SLA-4 — Multi-region failover RTO < 30s

**Endpoint**: `GET /api/v1/admin/health/multi-region` (Phase 5 wire
`f093f8c` multi-region observability carry-over).

**Baseline source**: Phase 5 wire `f093f8c` `replication_lag_seconds`
Prometheus histogram baseline (verbatim migrate).

**Measurement**: k6 scenario `multi-region-failover.js` (10 VU ramp
120s + sustain 120s).

**Owner**: Phase 8 owner-only RBAC.

**Audit trail**: `slo_modified` audit-first INSERT.

## Error budget burn rate alerts

Per SRE handbook (SRE Workbook Chapter 5 — "Alerting on SLOs"), the
canonical `SLOBurnRate` rule fires when the burn rate exceeds 14x the
30-day error budget over a 1-hour window (i.e. the entire error budget
would be exhausted in 2 days if the current rate continued).

The Phase 7 wire `59b56cd` alerting framework is the canonical delivery
mechanism (`alert_rules.yaml` SLOBurnRate rule → Prometheus AlertManager
→ Slack `#bizup-alerts` + PagerDuty owner-only manual trigger AD-22).

## SLO modification flow

1. Owner triggers `POST /api/v1/performance-testing/slo/modify` with
   the new target value + justification text.
2. Capability gate `PERFORMANCE_TESTING` (industry-agnostic, CR 12-1
   L4 precedent) + role gate `require_role("owner")` + Epic 12 2FA
   챌린지 보존 (AD-22).
3. **Audit-first INSERT** `slo_modified` action_class=`PERFORMANCE_TEST`
   with the previous value + new value + justification payload.
4. New target committed + drift detector
   (`tests/api/core/test_phase_8_slo_sli.py`) refreshed.

## Dry-run mode

The SLO dashboard (`GET /api/v1/performance-testing/slo/dashboard`)
supports a `dry_run=True` flag that returns synthetic baseline metrics
without performing any actual measurement (mirrors Phase 7
`OTEL_SDK_DISABLED` no-op fallback). Useful for:

- Local dev worktree verification (no production load generated).
- Pre-deploy smoke verification (CI gate without burning real budget).
- Owner-only SLO review without committing a measurement window.

## Baseline freeze

The SLO baselines (Phase 7 wire `59b56cd` Prometheus histogram
verbatim) are frozen at Phase 8 wire entry time. Re-baselining requires
a new Phase 8+ wire entry with explicit `baseline_commit` reference.

## Cross-references

- `apps/api/core/load_test_runner.py` — k6 scenario orchestrator (T1)
- `apps/api/tests/load/k6/{auth-login,cost-calculation,onboarding-flow,audit-log-query,multi-region-failover}.js` — 5 k6 scenarios
- `.github/workflows/load-test.yml` — nightly + manual load test trigger
- `apps/api/config/alert_rules.yaml` — `SLOBurnRate` rule (Phase 7 wire)
- `docs/capability-matrix.md` v1.33 — `PERFORMANCE_TESTING` capability row
- PRD §F24.2 — original 4 SLA definitions verbatim
