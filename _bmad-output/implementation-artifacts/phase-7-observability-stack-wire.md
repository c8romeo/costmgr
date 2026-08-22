---
baseline_commit: 916a541
epic_number: phase-7
status: ready-for-dev
wire_target: phase-7-observability-stack-wire
created: 2026-08-23
cj_style_entry_point: 90
---

# Story: Phase 7 — Observability Stack 강화 Wire (cj-style 90번째 epic 연속 정직 회복 atomic docs-only wire)

## Story

**As a** operations team / SRE / enterprise onboarding lead
**I want** OpenTelemetry distributed tracing + Prometheus custom metrics + Grafana dashboards + Alerting system (AlertManager + Slack + PagerDuty) + Frontend performance tracing (Browser RUM + Web Vitals)
**so that** we satisfy enterprise SLA 99.95% 가시성 (multi-region failover + cross-region request flow 추적) + NFR4/GDPR/SOX observability 요구 + Phase 4 Sentry `tracesSampleRate=0.1` carry-over EXTENSION + Phase 5 multi-region observability (`phase_5_replication_lag`) carry-over chain + Phase 6 retention purge 가시성 (`RetentionPurgeFailed` alert rule)

## Context (Phase 7 territory verbatim)

Phase 7 (Observability Stack 강화 territory)는 Phase 4 deployment wire `71a033a`의 Sentry observability (Sentry browser SSR-safe + Sentry FastAPI server integration + `tracesSampleRate=0.1`) + Phase 5 atomic wire `f093f8c`의 multi-region observability (§F20.5 multi-region health observability + `phase_5_replication_lag` table + Supabase primary Seoul + secondary Tokyo replica) + Phase 6 atomic wire `24e1cd7`의 audit log retention purge job (KST cron 02:00) carry-over chain의 natural next 진입 territory.

**Phase 7 PRD entry commit**: `916a541` (master PRD v3.7 → v3.8 atomic edit + capability matrix v1.31 → v1.32 EXTENSION OBSERVABILITY_TRACES + OBSERVABILITY_METRICS 2 NEW rows)

**Phase 7 territory 결정 wire** = OpenTelemetry distributed tracing + Prometheus custom metrics + Grafana dashboards 4종 + Alerting system 5 NEW alert rules + Frontend performance tracing (Browser RUM + Web Vitals) + 2 NEW AuditAction Literal values + ActionClass.OBSERVABILITY 신규 정의 + capability matrix v1.32 EXTENSION 2 NEW rows

**D-OBSERVABILITY-1 honestly RESOLVED 진입 wire** — 1st release close-out retro §6 + Epic 17 close-out retro §11 + Phase 6 close-out retro §13의 "observability stack 강화 결정 wire 보류, Phase 7+ 진입 시점" verbatim 해소.

---

## Acceptance Criteria (7 ACs PRD §F23.1~§F23.7 verbatim)

### §F23.1 OpenTelemetry distributed tracing (12 ACs)
1. `apps/api/core/tracing.py` NEW (~200 LOC) — OpenTelemetry Python SDK 초기화 + TracerProvider + span processor 결정 wire
2. **OTLP HTTP exporter** 결정 wire = `opentelemetry-exporter-otlp-proto-http` AD-14 stack pin (`opentelemetry-api==1.27.0` + `opentelemetry-sdk==1.27.0` + `opentelemetry-exporter-otlp-proto-http==1.27.0`) 결정 wire 보존 (Phase 5 wire `f093f8c`의 Sentry SDK pin 정합)
3. **W3C Trace Context propagation** 결정 wire = `traceparent` + `tracestate` HTTP header 추출/주입 결정 wire
4. FastAPI middleware `TraceContextMiddleware` NEW 결정 wire + 비동기 trace context 보존 (CR 1-1 ContextVar 정합 — request-scoped ContextVar에 trace_id 바인딩)
5. **span enrichment** 결정 wire = `tenant_id` + `user_id` + `trace_id` + `request_id` + `client_ip` 자동 span attribute 추가 결정 wire (Epic 17 audit_log의 trace_id 정합 보존)
6. `apps/api/core/observability.py` MODIFIED — Sentry SDK 초기화와 OpenTelemetry TracerProvider 공존 결정 wire (중복 span 방지)
7. **auto-instrumentation** 결정 wire = `opentelemetry-instrumentation-fastapi` + `opentelemetry-instrumentation-sqlalchemy` + `opentelemetry-instrumentation-httpx` + `opentelemetry-instrumentation-asyncpg` 4 instrumentors 결정 wire
8. **span attributes** 결정 wire = `http.method` + `http.route` + `http.status_code` + `db.system` + `db.statement` + `tenant.id` + `user.id` + `request.path` 결정 wire
9. **sampling** 결정 wire = head_based sampler ratio 1.0 dev + 0.1 prod 결정 wire (Phase 4 wire `71a033a`의 `tracesSampleRate=0.1` Sentry 정합)
10. **trace export** 결정 wire = OTLP HTTP endpoint `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318` env 결정 wire (Phase 5 multi-region Seoul + Tokyo replica 동일 collector)
11. `db.statement` span attribute는 SQL 파라미터 값을 포함하지 않음 결정 wire (NFR4 PII minimization verbatim — statement template only)
12. Tracing 비활성 환경 (`OTEL_SDK_DISABLED=true`) 에서 no-op TracerProvider fallback + 앱 부팅 실패 없음 결정 wire (Phase 4 Sentry conditional init pattern 미러)

### §F23.2 Prometheus custom metrics + Grafana dashboards (12 ACs)
1. `apps/api/core/metrics.py` NEW (~180 LOC) — Counter + Histogram + Summary + Gauge 4 metric types registry 결정 wire
2. **Counter metrics** 결정 wire = `business_signups_total{industry,plan}` Counter 결정 wire
3. **Counter metrics** 결정 wire = `business_logins_total{method,outcome}` Counter (method=magic_link/oauth_google/oauth_naver/oauth_kakao/sso_saml/password, outcome=success/failure) 결정 wire (Epic 15 wire 정합)
4. **Counter metrics** 결정 wire = `business_calculations_total{engine,outcome}` Counter (engine=traditional/abc/tdabc, outcome=success/validation_failure) 결정 wire
5. **Counter metrics** 결정 wire = `business_audit_log_purge_total{action_class,outcome}` Counter (action_class=audit/auth/data/security, outcome=success/failure) 결정 wire (Phase 6 wire `24e1cd7` 정합)
6. **Histogram metrics** 결정 wire = `business_cost_engine_duration_seconds{engine,tenant_size_bucket}` Histogram (bucket boundaries 0.1s + 0.5s + 1s + 2s + 5s + 10s + 30s) 결정 wire
7. **Histogram metrics** 결정 wire = `business_ai_extraction_duration_seconds{model,outcome}` Histogram 결정 wire
8. **Gauge metrics** 결정 wire = `business_active_tenants_gauge` (현재 활성 tenant 수) + `business_db_replication_lag_seconds{region}` 결정 wire (Phase 5 wire `f093f8c`의 `phase_5_replication_lag` table 정합)
9. **`/metrics` endpoint** 결정 wire = `GET /api/v1/metrics` Prometheus exposition format 결정 wire (`prometheus-client==0.20.0` AD-14 stack pin + FastAPI Response class `media_type=CONTENT_TYPE_LATEST`)
10. **label cardinality limit** 결정 wire = label 값 집합은 enum-bound (industry 4 + plan 3 + method 6 + engine 3 + outcome 2 + region 2) — free-form `tenant_id` label 금지 결정 wire (Prometheus cardinality explosion 방지)
11. **Grafana dashboards** 결정 wire = `docs/grafana-dashboards.md` NEW 4 dashboards JSON 결정: (1) **business-signups** (signups rate + logins by method + active tenants) / (2) **cost-engine-performance** (calculations rate + cost engine p50/p95/p99 latency + engine comparison) / (3) **auth-flow** (logins by method + 2FA challenge rate + SSO SAML rate) / (4) **audit-log-purge** (purge rate by action_class + retention policy + audit log row count) 결정 wire
12. **Grafana provisioning** 결정 wire = `docs/grafana-dashboards.md` 내 provisioning datasource + dashboard provider YAML 결정 wire + 각 dashboard panel의 PromQL query가 §F23.2 metric 이름과 정합 결정 wire

### §F23.3 Alerting system (12 ACs)
1. `apps/api/core/alerting.py` NEW (~120 LOC) — `AlertManagerClient` class 결정 wire
2. **Prometheus AlertManager integration** 결정 wire = AlertManager webhook receiver `POST /api/v1/internal/alertmanager-webhook` 결정 wire + `ALERTMANAGER_URL` env 결정 wire
3. **Sentry alert routing EXTENSION** 결정 wire = `apps/api/core/observability.py` MODIFIED + alert webhook handler + Sentry SDK `before_send_transaction` + alert severity mapping (info → warning → error → critical) 결정 wire
4. **Slack webhook integration** 결정 wire = `SLACK_WEBHOOK_URL` env + `#bizup-alerts` channel + Slack `attachments` JSON with severity color + trace_id link to Sentry + tenant_id link to admin dashboard 결정 wire
5. **PagerDuty integration** 결정 wire = owner-only manual trigger `POST /api/v1/admin/pagerduty/test` 결정 wire + `PAGERDUTY_INTEGRATION_KEY` env 결정 wire + AD-22 RBAC + Epic 12 2FA 챌린지 보존 결정 wire
6. **alert rule 1** 결정 wire = `config/alert_rules.yaml` NEW **`HighErrorRate`**: `rate(http_requests_total{status=~"5.."}[5m]) > 0.05` for 5m, severity=critical
7. **alert rule 2** 결정 wire = **`SlowCalc`**: `histogram_quantile(0.99, business_cost_engine_duration_seconds_bucket) > 5` for 10m, severity=warning
8. **alert rule 3** 결정 wire = **`FailoverStuck`**: `business_db_replication_lag_seconds > 30` for 5m, severity=critical (Phase 5 wire `f093f8c` `phase_5_replication_lag` table 정합)
9. **alert rule 4** 결정 wire = **`RetentionPurgeFailed`**: `time() - business_audit_log_purge_last_success_timestamp > 26 * 3600` , severity=warning (Phase 6 wire `24e1cd7`의 KST cron 02:00 정합, 24h + buffer)
10. **alert rule 5** 결정 wire = **`MultiRegionDown`**: `up{job="bizup-api"} == 0` for 1m (primary + secondary 둘 다 down), severity=critical
11. **audit-first INSERT `alert_fired`** 결정 wire = CR 1-1 verbatim 적용 (action_class='OBSERVABILITY' + action='alert_fired' + actor_id='system' + alert_name + severity + tenant_id='system' + trace_id + payload_json) — audit-first INSERT BEFORE Slack notification + Sentry alert routing chain 결정 wire
12. `apps/api/core/audit_action.py` MODIFIED 결정 wire + AlertManager webhook payload 검증 실패 시 `AlertWebhookPayloadInvalidError(400)` 1 NEW error class CR 12-5 D-14 envelope 결정 wire

### §F23.4 Frontend performance tracing (Browser RUM + W3C Trace Context propagation server → client) (10 ACs)
1. `apps/web/lib/tracing.ts` NEW (~150 LOC) — **Browser RUM via OpenTelemetry web SDK** 결정 wire = `@opentelemetry/sdk-trace-web` + `@opentelemetry/exporter-trace-otlp-http` AD-14 stack pin 결정 wire
2. **W3C Trace Context propagation server → client** 결정 wire = `apps/web/lib/api-fetch.ts` MODIFIED + trace context propagation `traceparent` header server response → client storage (sessionStorage `traceparent` key) → next request propagation 결정 wire (CR 1-1 ContextVar 정합)
3. **Web Vitals auto-collection** 결정 wire = `web-vitals` library AD-14 stack pin + LCP + FID + CLS + INP + TTFB auto-collection → OpenTelemetry span attributes (`web.lcp` + `web.fid` + `web.cls` + `web.inp` + `web.ttfb`) 결정 wire
4. **custom span attributes** 결정 wire = `user.tenant_id` + `user.role` + `user.industry` + `route.path` + `route.locale` 결정 wire
5. **API client fetch instrumentation** 결정 wire = `apps/web/lib/api-fetch.ts` MODIFIED + auto-instrumentation `fetch()` calls + span attributes `http.method` + `http.url` + `http.status_code` + `tenant.id` 결정 wire
6. **Next.js instrumentation hook** 결정 wire = `apps/web/instrumentation.ts` NEW + Next.js `register()` hook 결정 wire
7. **Next.js node SDK init** 결정 wire = `apps/web/instrumentation-node.ts` NEW + on server start OpenTelemetry node SDK initialization 결정 wire
8. **trace context sampling** 결정 wire = head_based sampler ratio 1.0 dev + 0.1 prod 결정 wire (backend §F23.1 정합)
9. **NFR18 ko-KR 정합** 결정 wire = trace_id 표시 시 ko-KR label "추적 ID" 사용 + alert UI 시 ko-KR 메시지 ("서비스에 문제가 발생했습니다. 잠시 후 다시 시도해주세요") 결정 wire + `apps/web/messages/ko-KR.json` `observability.*` namespace EXTENSION 결정 wire
10. **RSC boundary 정합** 결정 wire = `apps/web/lib/tracing.ts` 는 Client-only (`"use client"` 경계 준수, CR 1-1 RSC boundary lesson verbatim) + `instrumentation-node.ts` 는 server-only 결정 wire

### §F23.5 audit-first INSERT 2 NEW actions (ActionClass.OBSERVABILITY 신규 정의) (8 ACs)
1. **ActionClass.OBSERVABILITY 신규 정의** 결정 wire = `apps/api/core/audit_action.py` MODIFIED + `_ActionRegistry` EXTENSION ActionClass.OBSERVABILITY 신규 정의 + action_class values 결정 wire (Phase 6 wire `24e1cd7`의 ActionClass.AUDIT pattern 미러)
2. **AuditAction Literal value 1** 결정 wire = `alert_fired` (action_class='OBSERVABILITY' + action='alert_fired' + actor_id='system' + tenant_id='system' + alert_name + severity + trace_id + payload_json{alert_rule + threshold + current_value + runbook_url}) 결정 wire
3. **AuditAction Literal value 2** 결정 wire = `trace_sampled` (action_class='OBSERVABILITY' + action='trace_sampled' + actor_id='system' + tenant_id + decision='sampled'|'dropped' + sampling_ratio + trace_id) 결정 wire
4. `apps/api/core/audit_action.py` MODIFIED 결정 wire = AuditAction Literal 신규 2 values EXTENSION 결정 wire (Phase 6 wire `24e1cd7`의 5 NEW AuditAction Literal EXTENSION pattern verbatim 적용)
5. AuditAction Union EXTENSION 2 NEW + `_ActionRegistry` OBSERVABILITY entry 신규 2개 등록 + `__all__` EXTENSION 결정 wire
6. **resource_table** 결정 wire = `_ActionRegistry` OBSERVABILITY entry의 resource_table = `"observability_alerts"` 결정 wire
7. **audit-first INSERT BEFORE alerting trace** 결정 wire = CR 1-1 verbatim 적용 — alert 발동 시 audit-first INSERT + 이후 Slack notification + Sentry alert routing chain 결정 wire (CR 1-1 audit-first BEFORE actual mutation discipline)
8. **immutable observability audit log** 결정 wire = observability audit log 도 immutable (Phase 6 wire `24e1cd7`의 `audit_log_archive` 결정 wire 보존) — observability alert row 는 audit_log table + audit_log_archive EXTENSION 결정 wire

### §F23.6 Capability gates OBSERVABILITY_TRACES + OBSERVABILITY_METRICS (8 ACs)
1. `apps/api/core/capability.py` MODIFIED + `Capability.OBSERVABILITY_TRACES = "observability_traces"` + `Capability.OBSERVABILITY_METRICS = "observability_metrics"` 2 NEW enum 추가 결정 wire
2. **2 _INDUSTRY_CAPABILITIES blocks EXTENSION** 결정 wire = 4 industries grants ✅/✅/✅/✅ 결정 wire (manufacturing + service + 겸영 + 겸영+기타 industry-agnostic, CR 12-1 L4 precedent 미러 — AUDIT_LOG_RETENTION Phase 6 wire + AUDIT_LOG_VIEW Epic 17 wire + MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY Epic 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern verbatim bind)
3. `require_observability_traces = require_capability(Capability.OBSERVABILITY_TRACES)` + `require_observability_metrics = require_capability(Capability.OBSERVABILITY_METRICS)` 결정 wire + `apps/api/dependencies/capability.py` EXTENSION + `__all__` EXTENSION 결정 wire
4. **gate 적용 대상** 결정 wire = `require_observability_metrics` → `GET /api/v1/metrics` + Grafana embed endpoint / `require_observability_traces` → trace_id lookup endpoint + alert ack endpoint 결정 wire
5. **owner-only RBAC AD-22** 결정 wire = manual alert ack + manual trace_id lookup + manual metric dashboard view + manual Grafana embed 모두 owner role required (Epic 12 2FA 챌린지 보존 결정 wire)
6. **capability matrix v1.32** 결정 wire = `docs/capability-matrix.md` v1.31 → v1.32 EXTENSION 2 NEW rows + v1.32 changelog entry + `__all__` EXTENSION 결정 wire (PRD entry `916a541`에서 이미 wire DONE — spec entry는 정합 검증 결정 wire)
7. **drift detector** 결정 wire = `tests/integration/test_capability_matrix_v1_32_drift.py` NEW (~140 LOC, Phase 6 wire `24e1cd7`의 `tests/integration/test_capability_matrix_v1_31_drift.py` 패턴 verbatim 적용 — capability matrix v1.32 EXTENSION 2 NEW rows 정합 검증 + 4-industry grants + named gate dep 2 NEW + AUDIT_LOG_RETENTION + MULTI_REGION_BACKUP/FAILOVER + AUDIT_LOG_VIEW preservation 결정 wire)
8. 미허용 tenant의 observability 진입 차단 결정 wire CR 12-5 D-GATE-01 inversion 결정 wire

### §F23.7 Tests + wire scope T1~T8 (16 ACs)
1. **T1 OpenTelemetry tracing module** 결정 wire = `apps/api/core/tracing.py` NEW ~+200 LOC + `apps/api/core/observability.py` MODIFIED + 6 NEW pytest cases (W3C Trace Context propagation + span enrichment tenant_id + auto-instrumentation FastAPI + auto-instrumentation SQLAlchemy + sampling decision head_based + OTLP HTTP exporter 결정 wire)
2. **T2 Prometheus metrics module** 결정 wire = `apps/api/core/metrics.py` NEW ~+180 LOC + `GET /api/v1/metrics` endpoint + `apps/api/main.py` MODIFIED + 6 NEW pytest cases (Counter increment + Histogram observation + Gauge set + /metrics endpoint format + label cardinality limit + metric naming convention 결정 wire)
3. **T3 Alerting module + 5 alert rules** 결정 wire = `apps/api/core/alerting.py` NEW ~+120 LOC + `config/alert_rules.yaml` NEW + `apps/api/core/observability.py` MODIFIED Slack + Sentry + PagerDuty integration + 4 NEW pytest cases (alert webhook payload format + alert severity mapping + Slack message format + audit-first INSERT `alert_fired` CR 1-1 verbatim 결정 wire)
4. **T4 Grafana dashboards** 결정 wire = `docs/grafana-dashboards.md` NEW 4 dashboards JSON + Grafana provisioning + 2 NEW pytest cases (dashboard JSON validation + dashboard panel metric query 정합 결정 wire)
5. **T5 capability v1.32** 결정 wire = capability matrix v1.31 → v1.32 EXTENSION OBSERVABILITY_TRACES + OBSERVABILITY_METRICS 2 NEW rows + 4-industry grants industry-agnostic ✅/✅/✅/✅ + drift detector `tests/integration/test_capability_matrix_v1_32_drift.py` NEW 8 NEW pytest cases 결정 wire
6. **T6 audit action EXTENSION 2 NEW** 결정 wire = `apps/api/core/audit_action.py` MODIFIED + AuditAction Literal 2 NEW EXTENSION + `_ActionRegistry` OBSERVABILITY entry 신규 2개 등록 + `__all__` EXTENSION + ActionClass.OBSERVABILITY 신규 정의 + 2 NEW pytest cases (AuditAction Literal 값 검증 + ActionClass.OBSERVABILITY enum value + resource_table "observability_alerts" 결정 wire)
7. **T7 frontend tracing** 결정 wire = `apps/web/lib/tracing.ts` NEW ~+150 LOC + `apps/web/lib/api-fetch.ts` MODIFIED + `apps/web/instrumentation.ts` NEW + `apps/web/instrumentation-node.ts` NEW + W3C Trace Context propagation server → client + Web Vitals auto-collection LCP + FID + CLS + INP + TTFB + 5 NEW vitest cases (W3C Trace Context propagation + Web Vitals span attributes + API fetch instrumentation + Next.js instrumentation hook + ko-KR SSOT 검증 결정 wire)
8. **T8 atomic commit** 결정 wire = `git commit -F <file>` (CR 9-6 D5 prevention) + commit-msg file 신규 + handoff memory 신규 + MEMORY.md hook index 신규 EXTENSION + sprint-status.yaml MODIFIED (`phase-7-spec-entry: backlog → done` + A228~A232 action_items block 5 entries + `last_updated_note` v3.8 Phase 7 spec entry prepend 결정 wire)
9. **estimated pytest** 결정 wire = ~+30 NEW pytest PASS (tracing 6 + metrics 6 + alerting 4 + grafana 2 + audit action 2 + capability matrix v1.32 8 + integration e2e 2 = ~+30 NEW pytest PASS)
10. **estimated vitest** 결정 wire = ~+10 NEW vitest PASS (frontend tracing 5 + SSOT drift 2 + ko-KR SSOT 검증 3 = ~+10 NEW vitest PASS) + 0 NEW ruff + 0 regressions 결정 wire 보존
11. Test cases include RLS isolation 정합 CR 0-2 verbatim (span enrichment `tenant.id`가 요청 tenant 로만 바인딩 + cross-tenant span attribute 누출 0건)
12. Test cases include audit-first INSERT verification CR 1-1 verbatim (`alert_fired` audit log이 Slack notification BEFORE emit)
13. Test cases include label cardinality guard (free-form `tenant_id` label 주입 시도 → expect rejection/assert enum-bound labels only)
14. Test cases include NFR4 PII minimization guard (`db.statement` span attribute에 파라미터 값 미포함 assert)
15. Test cases include capability matrix drift detector (modify enum → expect drift detector FAIL) + 미허용 tenant 차단 CR 12-5 D-GATE-01 inversion
16. **3중 게이트 retro verification FINAL CLEAN** 결정 wire = (1) pytest focused ~30/30 NEW PASS / (2) vitest focused ~10/10 NEW PASS + i18n SSOT drift detector PASS / (3) ruff scoped all checks passed / (4) tsc scoped 0 NEW errors (pre-existing baseline errors preserved per cj-style discipline) / (5) SDR drift gate PASS / (6) commit_consistency gate PASS (CR 9-6 + A36 SDR 검증 4-step 자동 적용) / (7) D-DEFER-* grep guard PASS (CR 11-3 honest-DEFER discipline 90번째 epic 연속 정직 회복 검증 보존)

---

## Tasks (T1~T8)

### T1. OpenTelemetry tracing module (13 subtasks)
1.1. Create `apps/api/core/tracing.py` (~200 LOC) with TracerProvider + BatchSpanProcessor 초기화
1.2. Add AD-14 stack pin to `apps/api/requirements.txt`: `opentelemetry-api==1.27.0` + `opentelemetry-sdk==1.27.0` + `opentelemetry-exporter-otlp-proto-http==1.27.0`
1.3. Add 4 instrumentor pins: `opentelemetry-instrumentation-fastapi` + `opentelemetry-instrumentation-sqlalchemy` + `opentelemetry-instrumentation-httpx` + `opentelemetry-instrumentation-asyncpg`
1.4. Implement OTLP HTTP exporter with `OTEL_EXPORTER_OTLP_ENDPOINT` env (default `http://otel-collector:4318`)
1.5. Implement `TraceContextMiddleware` FastAPI middleware — `traceparent` + `tracestate` 추출/주입
1.6. Bind trace_id to request-scoped ContextVar (CR 1-1 ContextVar 정합)
1.7. Implement `enrich_span(span, tenant_id, user_id, request_id, client_ip)` span enrichment helper
1.8. Implement head_based sampler: ratio 1.0 dev + 0.1 prod via `OTEL_TRACES_SAMPLER_ARG` env
1.9. Add `OTEL_SDK_DISABLED=true` no-op TracerProvider fallback (Phase 4 Sentry conditional init pattern 미러)
1.10. Strip SQL parameter values from `db.statement` span attribute (NFR4 PII minimization)
1.11. Modify `apps/api/core/observability.py` — Sentry SDK + OpenTelemetry TracerProvider 공존 (중복 span 방지)
1.12. Wire tracing init in `apps/api/main.py` lifespan hook + `TraceContextMiddleware` add_middleware
1.13. Add 6 NEW pytest cases in `tests/api/core/test_tracing.py`

### T2. Prometheus metrics module (10 subtasks)
2.1. Add AD-14 stack pin `prometheus-client==0.20.0` to `apps/api/requirements.txt`
2.2. Create `apps/api/core/metrics.py` (~180 LOC) with CollectorRegistry
2.3. Define 4 Counter metrics: `business_signups_total` + `business_logins_total` + `business_calculations_total` + `business_audit_log_purge_total`
2.4. Define 2 Histogram metrics: `business_cost_engine_duration_seconds` (7 buckets) + `business_ai_extraction_duration_seconds`
2.5. Define 2 Gauge metrics: `business_active_tenants_gauge` + `business_db_replication_lag_seconds{region}`
2.6. Implement enum-bound label validation helper `_validate_labels()` (free-form `tenant_id` label 금지)
2.7. Implement `GET /api/v1/metrics` endpoint with `CONTENT_TYPE_LATEST` media_type + `require_observability_metrics` gate
2.8. Modify `apps/api/main.py` — metrics router include_router
2.9. Wire metric emission call sites: signup + login + calculation + purge job (Phase 6 wire `24e1cd7` 정합) + replication lag (Phase 5 wire `f093f8c` 정합)
2.10. Add 6 NEW pytest cases in `tests/api/core/test_metrics.py`

### T3. Alerting module + 5 alert rules (12 subtasks)
3.1. Create `apps/api/core/alerting.py` (~120 LOC) with `AlertManagerClient` class
3.2. Implement `POST /api/v1/internal/alertmanager-webhook` receiver + payload validation
3.3. Add `AlertWebhookPayloadInvalidError(400)` CR 12-5 D-14 envelope + `apps/api/main.py` exception handler
3.4. Implement alert severity mapping (info → warning → error → critical)
3.5. Implement Slack webhook integration: `SLACK_WEBHOOK_URL` env + `#bizup-alerts` channel + `attachments` JSON with severity color + trace_id Sentry link + tenant_id admin link
3.6. Implement Sentry alert routing EXTENSION in `apps/api/core/observability.py` (`before_send_transaction`)
3.7. Implement PagerDuty `POST /api/v1/admin/pagerduty/test` owner-only manual trigger + `PAGERDUTY_INTEGRATION_KEY` env + AD-22 RBAC + Epic 12 2FA 챌린지
3.8. Add audit-first INSERT `alert_fired` CR 1-1 verbatim BEFORE Slack notification
3.9. Create `config/alert_rules.yaml` NEW with `HighErrorRate` + `SlowCalc` rules
3.10. Add `FailoverStuck` (Phase 5 `phase_5_replication_lag` 정합) + `RetentionPurgeFailed` (Phase 6 KST cron 02:00 정합, 26h threshold) rules
3.11. Add `MultiRegionDown` rule (`up{job="bizup-api"} == 0` for 1m)
3.12. Add 4 NEW pytest cases in `tests/api/core/test_alerting.py`

### T4. Grafana dashboards (6 subtasks)
4.1. Create `docs/grafana-dashboards.md` NEW with provisioning datasource + dashboard provider YAML
4.2. Add **business-signups** dashboard JSON (signups rate + logins by method + active tenants)
4.3. Add **cost-engine-performance** dashboard JSON (calculations rate + p50/p95/p99 latency + engine comparison)
4.4. Add **auth-flow** dashboard JSON (logins by method + 2FA challenge rate + SSO SAML rate)
4.5. Add **audit-log-purge** dashboard JSON (purge rate by action_class + retention policy + audit log row count)
4.6. Add 2 NEW pytest cases in `tests/integration/test_grafana_dashboards.py` (dashboard JSON validation + panel PromQL query ↔ §F23.2 metric name 정합)

### T5. Capability v1.32 EXTENSION + drift detector (6 subtasks)
5.1. Modify `apps/api/core/capability.py` EXTENSION `Capability.OBSERVABILITY_TRACES` + `Capability.OBSERVABILITY_METRICS` 2 NEW enum
5.2. EXTENSION 4 `_INDUSTRY_CAPABILITIES` blocks (manufacturing + service + 겸영 + 겸영+기타) with 2 NEW grants ✅
5.3. Modify `apps/api/dependencies/capability.py` EXTENSION `require_observability_traces` + `require_observability_metrics` + `__all__` EXTENSION
5.4. Verify `docs/capability-matrix.md` v1.32 EXTENSION 2 NEW rows 정합 (PRD entry `916a541`에서 wire DONE — 정합 검증만)
5.5. Apply gates: `require_observability_metrics` → `/api/v1/metrics` + Grafana embed / `require_observability_traces` → trace_id lookup + alert ack (owner-only AD-22)
5.6. Create `tests/integration/test_capability_matrix_v1_32_drift.py` NEW 8 NEW pytest cases (Phase 6 `test_capability_matrix_v1_31_drift.py` 패턴 verbatim)

### T6. Audit action EXTENSION 2 NEW + ActionClass.OBSERVABILITY (5 subtasks)
6.1. Modify `apps/api/core/audit_action.py` — ActionClass.OBSERVABILITY 신규 정의
6.2. Add 2 NEW AuditAction Literal values: `alert_fired` + `trace_sampled`
6.3. Add AuditAction Union EXTENSION 2 NEW + `_ActionRegistry` OBSERVABILITY entry 신규 2개 등록 (resource_table `"observability_alerts"`)
6.4. Add `__all__` EXTENSION 2 NEW names
6.5. Add 2 NEW pytest cases in `tests/api/core/test_phase_7_audit_action.py`

### T7. Frontend tracing (12 subtasks)
7.1. Add AD-14 stack pin to `apps/web/package.json`: `@opentelemetry/sdk-trace-web` + `@opentelemetry/exporter-trace-otlp-http` + `web-vitals`
7.2. Create `apps/web/lib/tracing.ts` (~150 LOC) Client-only (`"use client"` 경계 준수, CR 1-1 RSC boundary lesson)
7.3. Implement WebTracerProvider + OTLP HTTP exporter + head_based sampler (1.0 dev / 0.1 prod)
7.4. Implement Web Vitals auto-collection LCP + FID + CLS + INP + TTFB → span attributes `web.lcp` + `web.fid` + `web.cls` + `web.inp` + `web.ttfb`
7.5. Implement custom span attributes `user.tenant_id` + `user.role` + `user.industry` + `route.path` + `route.locale`
7.6. Modify `apps/web/lib/api-fetch.ts` — `traceparent` header server response → sessionStorage → next request propagation
7.7. Modify `apps/web/lib/api-fetch.ts` — `fetch()` auto-instrumentation span attributes `http.method` + `http.url` + `http.status_code` + `tenant.id`
7.8. Create `apps/web/instrumentation.ts` NEW Next.js `register()` hook
7.9. Create `apps/web/instrumentation-node.ts` NEW server-only OpenTelemetry node SDK init
7.10. Modify `apps/web/messages/ko-KR.json` — `observability.*` namespace EXTENSION (추적 ID label + alert ko-KR 메시지 NFR18 정합)
7.11. Add 5 NEW vitest cases (W3C Trace Context propagation + Web Vitals span attributes + API fetch instrumentation + Next.js instrumentation hook + ko-KR SSOT 검증)
7.12. Verify tsc scoped 0 NEW errors (pre-existing baseline errors preserved per cj-style discipline)

### T8. Atomic commit via `git commit -F <file>` (4 subtasks)
8.1. Create `_bmad-output/implementation-artifacts/commit-msg-phase-7-observability-stack-wire.txt` commit message file
8.2. Create `memory/handoff-2026-08-23-phase-7-spec-entry-done.md` handoff memory
8.3. Update `_bmad-output/implementation-artifacts/sprint-status.yaml`: `phase-7-spec-entry: backlog → done` + A228~A232 action_items + `last_updated_note` v3.8 Phase 7 spec entry prepend
8.4. Update `memory/MEMORY.md` hook index EXTENSION + atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention)

---

## Dev Notes

### CR Lessons Applied (14종 결정 wire)

- **CR 0-2 RLS lesson** ✅ APPLIED: span enrichment `tenant.id` 는 요청 tenant 로만 바인딩 + cross-tenant span attribute 누출 0건 결정 wire + Prometheus label 에 tenant_id free-form 금지 (cardinality + tenant 정보 누출 동시 방지) CR 0-2 verbatim
- **CR 1-1 audit-first INSERT** ✅ APPLIED: 2 NEW audit log entries (`alert_fired` + `trace_sampled`) + ActionClass.OBSERVABILITY 신규 정의 + `emit_audit_typed` BEFORE Slack notification + Sentry alert routing chain CR 1-1 verbatim
- **CR 1-1 ContextVar lesson** ✅ APPLIED: trace_id 를 request-scoped ContextVar 에 바인딩 + 비동기 trace context 보존 결정 wire (FastAPI ContextVar lesson verbatim)
- **CR 1-1 RSC boundary lesson** ✅ APPLIED: `apps/web/lib/tracing.ts` Client-only (`"use client"`) + `apps/web/instrumentation-node.ts` server-only 경계 준수 결정 wire
- **CR 9-6 commit message discipline** ✅ APPLIED: `git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention + commit message file 결정 wire
- **CR 11-3 honest-DEFER discipline** ✅ APPLIED: 90번째 epic 연속 정직 회복, D-1-1-DEFER-* ✅ RESOLVED 보존 + D-EPIC-16-REVIEW-DEFER-2~6 ✅ RESOLVED 보존 + D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED 보존 + D-EPIC-17-WIRE-DEFER-T2-T3-UI ✅ RESOLVED 보존 + D-RETENTION-1 ✅ RESOLVED 보존 + **D-OBSERVABILITY-1 honestly RESOLVED 진입 wire** (1st release close-out retro §6 + Epic 17 close-out retro §11 + Phase 6 close-out retro §13 verbatim 해소) + D-LAUNCH-1-DEFER-1 honestly preserved
- **CR 11-4 D-001~D-005 + P-015 lessons carry** ✅ APPLIED: frontend territory 정합 sweep 결정 wire (ko-KR.json `observability.*` namespace EXTENSION + NFR18 ko-KR "추적 ID" label 결정 wire)
- **CR 12-1 L4 industry-agnostic capability** ✅ APPLIED: OBSERVABILITY_TRACES + OBSERVABILITY_METRICS industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire (AUDIT_LOG_RETENTION Phase 6 wire + AUDIT_LOG_VIEW Epic 17 wire + MULTI_REGION_BACKUP/FAILOVER Phase 5 wire + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY Epic 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern verbatim bind)
- **CR 12-5 D-14 typed exception envelope** ✅ APPLIED: 1 NEW error class (`AlertWebhookPayloadInvalidError` 400) 결정 wire + `apps/api/main.py` 1 NEW exception handler
- **CR 12-5 D-PARITY-01 inversion** ✅ APPLIED: Python backend span attribute 이름 (`tenant.id` + `user.id` + `http.method` + `http.status_code`) ↔ TypeScript frontend `apps/web/lib/tracing.ts` span attribute 이름 parity 결정 wire + vitest cross-language drift 검증
- **CR 12-5 D-GATE-01 inversion** ✅ APPLIED: OBSERVABILITY_TRACES + OBSERVABILITY_METRICS capability gate per-tenant on/off + owner-only RBAC AD-22 결정 wire + PagerDuty test trigger `require_role("owner")` 결정 wire
- **A19 cohesion pattern 9 surface EXTENSION PASS** ✅ APPLIED: observability surface NEW = F23.1~F23.7 observability stack territory 결정 wire + spec surface EXTENSION + test surface EXTENSION
- **A36 SDR 검증 4-step 자동 적용** ✅ APPLIED: commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS 결정 wire
- **AD-14 stack pin** ✅ APPLIED: `opentelemetry-api==1.27.0` + `opentelemetry-sdk==1.27.0` + `opentelemetry-exporter-otlp-proto-http==1.27.0` + `prometheus-client==0.20.0` + `@opentelemetry/sdk-trace-web` + `@opentelemetry/exporter-trace-otlp-http` + `web-vitals` 결정 wire (Phase 4 wire `71a033a` Sentry SDK pin 정합)
- **AD-22 owner-only RBAC** ✅ APPLIED: manual alert ack + manual trace_id lookup + manual metric dashboard view + manual Grafana embed + PagerDuty test trigger 모두 owner role required 결정 wire + Epic 12 2FA 챌린지 보존
- **NFR4 PII minimization** ✅ PRESERVED: `db.statement` span attribute 에 SQL 파라미터 값 미포함 (statement template only) + Prometheus label 에 free-form tenant_id 금지 + trace payload PII 최소화 결정 wire

### Architecture Alignment (cj-style architecture ALLOWED sweep)
- **kernel**: sampler decision pure function + severity mapping pure function + label validation pure function
- **port**: `apps/api/core/tracing.py` + `apps/api/core/metrics.py` + `apps/api/core/alerting.py` observability port 결정 wire
- **db schema**: NO new tables 결정 wire (observability alert row 는 audit_log table + audit_log_archive EXTENSION — Phase 6 wire `24e1cd7` 결정 wire 보존)
- **service**: tracing service + metrics service + alerting service 결정 wire
- **handler**: `GET /api/v1/metrics` + `POST /api/v1/internal/alertmanager-webhook` + `POST /api/v1/admin/pagerduty/test` 결정 wire
- **envelope**: CR 12-5 D-14 typed exception envelope 1 NEW error class 결정 wire
- **capability**: OBSERVABILITY_TRACES + OBSERVABILITY_METRICS capability gate per-tenant on/off + owner-only RBAC AD-22 결정 wire
- **audit**: 2 NEW AuditAction Literal values + ActionClass.OBSERVABILITY 신규 정의 + audit-first INSERT CR 1-1 verbatim
- **observability surface NEW**: F23.1~F23.7 observability stack territory 결정 wire EXTENSION PASS (A19 cohesion 9 surface EXTENSION)

### Files Affected (Estimated ~20 NEW + ~9 MODIFIED)
**NEW files (estimated)**:
- `apps/api/core/tracing.py` (~200 LOC)
- `apps/api/core/metrics.py` (~180 LOC)
- `apps/api/core/alerting.py` (~120 LOC)
- `config/alert_rules.yaml` (5 NEW alert rules)
- `docs/grafana-dashboards.md` (4 dashboards JSON + provisioning)
- `apps/web/lib/tracing.ts` (~150 LOC, Client-only)
- `apps/web/instrumentation.ts` (Next.js `register()` hook)
- `apps/web/instrumentation-node.ts` (server-only node SDK init)
- 6 NEW pytest files (`tests/api/core/test_tracing.py` + `tests/api/core/test_metrics.py` + `tests/api/core/test_alerting.py` + `tests/integration/test_grafana_dashboards.py` + `tests/api/core/test_phase_7_audit_action.py` + `tests/integration/test_capability_matrix_v1_32_drift.py`)
- 3 NEW vitest files (`tracing.test.ts` + `api-fetch-tracing.test.ts` + `i18n/observability-ssot.test.ts`)
- 1 NEW handoff memory (`memory/handoff-2026-08-23-phase-7-spec-entry-done.md`)
- 1 NEW commit-msg file (`_bmad-output/implementation-artifacts/commit-msg-phase-7-observability-stack-wire.txt`)

**MODIFIED files (estimated)**:
- `apps/api/main.py` (tracing lifespan hook + `TraceContextMiddleware` + metrics router + alerting router + 1 NEW exception handler)
- `apps/api/core/observability.py` (Sentry + OpenTelemetry 공존 + Sentry alert routing `before_send_transaction`)
- `apps/api/core/audit_action.py` (ActionClass.OBSERVABILITY 신규 정의 + 2 NEW AuditAction Literal values + `_ActionRegistry` EXTENSION + `__all__` EXTENSION)
- `apps/api/core/capability.py` (2 NEW Capability enum + 4 `_INDUSTRY_CAPABILITIES` blocks EXTENSION)
- `apps/api/dependencies/capability.py` (`require_observability_traces` + `require_observability_metrics` EXTENSION + `__all__` EXTENSION)
- `apps/api/requirements.txt` (AD-14 stack pin 4 NEW + 4 instrumentors)
- `apps/web/lib/api-fetch.ts` (`traceparent` propagation + `fetch()` auto-instrumentation)
- `apps/web/package.json` (AD-14 stack pin 3 NEW)
- `apps/web/messages/ko-KR.json` (`observability.*` namespace EXTENSION)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (`phase-7-spec-entry` entry + A228~A232 action_items + `last_updated_note` prepend)
- `memory/MEMORY.md` (handoff hook index EXTENSION)

**Total**: ~20 NEW + ~11 MODIFIED = ~31 files atomic single sprint

### Test Coverage (cj-style 정합)
- pytest: ~30 NEW CASES (tracing 6 + metrics 6 + alerting 4 + grafana 2 + audit action 2 + capability matrix v1.32 drift 8 + integration e2e 2)
- vitest: ~10 NEW CASES (frontend tracing 5 + SSOT drift 2 + ko-KR SSOT 검증 3)
- ruff: 0 NEW errors
- tsc: 0 NEW errors (pre-existing baseline errors preserved per cj-style discipline)
- regressions: 0 NEW
- 3중 게이트 FINAL CLEAN 보존 결정 wire

### References (16)
1. `_bmad-output/planning-artifacts/prd.md` §F23 (master PRD v3.8 §F23 territory)
2. `_bmad-output/planning-artifacts/prd.md` §8.1 M0-(p) Phase 7 observability stack 강화 AC
3. `_bmad-output/planning-artifacts/prd.md` §15 로드맵 Phase 7 row (백로그 → in-progress)
4. `_bmad-output/planning-artifacts/prd.md` 부록 A AD-34 Observability Stack 강화 (7 sub-decisions)
5. `docs/capability-matrix.md` v1.32 EXTENSION OBSERVABILITY_TRACES + OBSERVABILITY_METRICS rows
6. Phase 7 PRD entry commit `916a541` — master PRD v3.7 → v3.8 + capability matrix v1.31 → v1.32
7. Phase 4 deployment wire `71a033a` — Sentry observability (`tracesSampleRate=0.1`) carry-over chain
8. Phase 5 atomic wire `f093f8c` — multi-region observability + `phase_5_replication_lag` table carry-over chain
9. Phase 6 atomic wire `24e1cd7` — audit log retention purge job KST cron 02:00 + ActionClass.AUDIT EXTENSION pattern 미러
10. Phase 6 spec entry `phase-6-audit-log-retention-wire.md` — 7 ACs verbatim + T1~T8 pattern 미러
11. Phase 6 close-out retro `f9f006c` §13 verbatim — D-OBSERVABILITY-1 honestly RESOLVED 진입 결정 wire
12. Epic 17 close-out retro §11 verbatim — D-OBSERVABILITY-1 honestly RESOLVED 진입 결정 wire
13. 1st release close-out retro §6 verbatim — D-OBSERVABILITY-1 honestly RESOLVED 진입 결정 wire
14. CR 1-1 lessons (audit-first INSERT + FastAPI ContextVar + RSC boundary)
15. CR 11-3 honest-DEFER discipline (90번째 epic 연속 정직 회복)
16. CR 12-1 L4 industry-agnostic capability precedent (capability matrix v1.32 EXTENSION)

### Story Header
- **Story ID**: phase-7
- **Story Title**: Observability Stack 강화 Wire
- **Created**: 2026-08-23
- **cj-style entry point**: 90
- **baseline_commit**: 916a541 (Phase 7 PRD entry commit)
- **PRD section**: §F23 (master PRD v3.8)
- **AC count**: 7 ACs (PRD §F23.1~§F23.7 verbatim)
- **Sub-AC count**: 78 detailed sub-ACs (12 + 12 + 12 + 10 + 8 + 8 + 16)
- **Task count**: 8 (T1~T8)
- **Subtask count**: 68 (T1:13 + T2:10 + T3:12 + T4:6 + T5:6 + T6:5 + T7:12 + T8:4)
- **Estimated wire scope**: ~20 NEW + ~11 MODIFIED = ~31 files atomic single sprint
- **Estimated pytest**: ~30 NEW CASES
- **Estimated vitest**: ~10 NEW CASES

### Dev Agent Record
- **Agent**: Amelia (Developer)
- **Wire target**: phase-7-observability-stack-wire
- **Wire commit**: pending (T8 atomic commit)
- **3중 게이트**: pending (T7/T8 verification)
- **A19 cohesion**: pending (9 surface EXTENSION PASS — observability surface NEW)
- **CR lessons applied**: 14종 결정 wire
- **D-DEFER-* honestly 결정**: D-OBSERVABILITY-1 ✅ RESOLVED + D-RETENTION-1 ✅ RESOLVED + D-1-1-DEFER-* ✅ RESOLVED + D-EPIC-16-REVIEW-DEFER-2~6 ✅ RESOLVED + D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED + D-EPIC-17-WIRE-DEFER-T2-T3-UI ✅ RESOLVED + D-LAUNCH-1-DEFER-1 honestly preserved

---

**Why/How to apply**: cj-style discipline 회피 위험 방지 — Phase 7 spec entry 진입 시점에 4-entry-point pattern 두 번째 진입점 결정 (PRD 89 → spec 90 → atomic wire T1~T8 91 → close-out retro 92). D-OBSERVABILITY-1 honestly RESOLVED 결정 wire 진입. 7 ACs PRD §F23.1~§F23.7 verbatim + 8 tasks T1~T8 + 68 subtasks + ~31 files estimated wire scope + 14종 CR lessons applied. Epic 1~17 + Phase 3~6 + 1st release cycle 정합 보존 검증 결정 wire 보존.
