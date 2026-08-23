---
baseline_commit: 0b2d2f3
status: ready-for-dev
cj_style_entry_point: 98
story_key: phase-9-chaos-engineering-wire
---

# Phase 9 Chaos Engineering / Game Day wire spec (cj-style 98번째 epic 연속 정직 회복)

## Story

**As a** operations team / SRE / enterprise onboarding lead
**I want** chaos engineering / game day territory 결정 wire (chaos experiment definition + fault injection types 10 categories + game day runbook + blast radius control 5 levels + continuous chaos vs scheduled game day + tenant-scoped + multi-region chaos + auto-rollback + safety mechanisms 6 layers)
**so that** Phase 8 wire `60d4ea1` 의 k6 부하 테스트 5 scenarios + SLO/SLI 정의 4 metrics + p99 latency budget 5s + Latency regression detector + Cost-engine benchmark V8 골든 + Performance regression gate CI 의 natural backend carry-over chain 진입 territory 가 §F24.* 의 자연스러운 EXTENSION territory (Phase 9 = §F25 신규 territory) 의 natural next 진입 + Phase 5 wire `f093f8c` multi-region failover + Phase 7 wire `59b56cd` observability stack + Phase 8 wire `60d4ea1` performance / load testing 의 자연스러운 carry-over chain 의 자연스러운 next territory 진입 결정 wire + Epic 12 2FA 챌린지 보존 + AD-22 owner-only RBAC 보존 + Phase 8 close-out retro §10 + Phase 7 close-out retro §10 verbatim territory 해소 결정 wire 보존.

## Context

cj-style Phase 9 2번째 진입점 (cj-style 98번째) 진입 결정 wire 진입 완료:
- Phase 9 PRD entry `0b2d2f3` (cj-style 97번째) DONE 진입 정합 보존
- Phase 8 close-out retro `ab495a8` (cj-style 96번째) + Phase 8 atomic wire T1~T8 `60d4ea1` (cj-style 95번째) + Phase 8 spec entry `5ae0f4e` (cj-style 94번째) + Phase 8 PRD entry `ced452f` (cj-style 93번째) + Build fixes sprint `eaee198` 결정 wire 모두 DONE 진입 정합 보존
- D-CHAOS-1 honestly DEFER 보존 1 NEW 결정 wire (Phase 8 close-out retro §10 + Phase 7 close-out retro §10 verbatim 해소) 결정 wire 보존
- D-PERFORMANCE-1 ✅ RESOLVED 보존 진입 결정 wire
- D-OBSERVABILITY-1 ✅ RESOLVED 보존 진입 결정 wire
- Phase 9 PRD entry 의 7 ACs §F25.1~§F25.7 verbatim 결정 wire 보존

## 7 ACs (PRD §F25.1~§F25.7 verbatim) → 78 detailed sub-ACs

### §F25.1 chaos experiment definition (12 sub-ACs)
- F25.1-1 `apps/api/modules/chaos/chaos_experiment.py` NEW (~+150 LOC + ChaosExperiment TypedDict 13 fields 결정 wire)
- F25.1-2 ChaosExperiment TypedDict 필드 13개 결정 wire = `experiment_id: str` + `name: str` + `description: str` + `steady_state_metric: str` + `hypothesis: str` + `fault_type: Literal[10 values]` + `target_service: str` + `target_endpoint: str | None` + `blast_radius: Literal[5 levels]` + `duration_seconds: int` (max 600s = 10min) + `intensity: Literal["low", "medium", "high"]` + `abort_conditions: list[AbortCondition]` + `rollback_strategy: Literal["automatic", "manual", "hybrid"]` + `owner_only: bool = True` AD-22 RBAC + `dry_run: bool = True` default
- F25.1-3 Steady state hypothesis 결정 wire = Phase 8 wire `60d4ea1` 의 `business_cost_engine_duration_seconds{engine,tenant_size_bucket}` p99 < 5s SLA + `business_signups_total` success_rate > 99% + `business_logins_total` p99 < 1s + `business_audit_log_purge_total` success_rate > 99.9% 4 SLO 의 자연스러운 carry-over chain 결정 wire + chaos experiment 의 steady state 정의 = hypothesis 검증 의 SSOT 결정 wire
- F25.1-4 Blast radius control 5 levels 결정 wire = L1 `single_request` (1 request 만 영향) + L2 `single_tenant` (1 tenant 만 영향, 기본값) + L3 `all_tenants` (모든 tenant 영향, owner-only + 2FA 챌린지 Epic 12 정합) + L4 `single_region` (1 region 만 영향, Phase 5 multi-region 정합) + L5 `multi_region` (multi-region 영향, Phase 5 failover drill 정합) 결정 wire + L3~L5 는 owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 보존 결정 wire
- F25.1-5 Abort conditions 4 rules 결정 wire = (a) steady_state_metric > 1.5x baseline (auto-abort) + (b) error_rate > 5% (auto-abort) + (c) experiment_duration > max (auto-abort) + (d) external abort signal via `POST /api/v1/admin/chaos/{experiment_id}/abort` (manual abort, owner-only AD-22 + 2FA 챌린지 Epic 12 정합) 결정 wire
- F25.1-6 AbortCondition TypedDict 결정 wire = `metric: str` (Prometheus metric name) + `threshold: float` + `comparison: Literal[">", ">=", "<", "<="]` + `window_seconds: int` + `severity: Literal["warning", "critical"]` 결정 wire
- F25.1-7 chaos_experiment audit-first INSERT 결정 wire (`chaos_experiment_started` 1 NEW action + ActionClass.CHAOS_ENGINEERING 결정 wire + CR 1-1 verbatim 적용 + emit_audit_typed BEFORE chaos_experiment 시작)
- F25.1-8 chaos_experiment owner-only RBAC 결정 wire (L3~L5 blast radius + manual abort + 2FA 챌린지 Epic 12 정합 + `require_role("owner")` 결정 wire)
- F25.1-9 chaos_experiment dry-run mode default 결정 wire (dry_run=True flag + audit-first INSERT `chaos_experiment_dryrun` 결정 wire + no actual fault injection)
- F25.1-10 chaos_experiment TypedDict validation 결정 wire (pydantic v2 model_validator + blast_radius enum 검증 + intensity enum 검증 + abort_conditions list min 1 max 4 검증 + duration_seconds 1~600 검증)
- F25.1-11 chaos_experiment baseline freeze 결정 wire (Phase 8 wire `60d4ea1` 의 baseline freeze pattern verbatim 미러 + steady_state_metric baseline 30d rolling)
- F25.1-12 chaos_experiment CR 1-1 ContextVar verbatim 적용 결정 wire (trace_id request-scoped ContextVar 바인딩 + 비동기 trace context 보존)

### §F25.2 fault injection types 10 categories (12 sub-ACs)
- F25.2-1 `apps/api/modules/chaos/fault_injection.py` NEW (~+200 LOC + fault type registry + 10 fault types implementation 결정 wire)
- F25.2-2 (1) latency injection 결정 wire = `inject_latency(target, delay_ms, jitter_ms, percentage)` 함수 + HTTP middleware `LatencyFaultMiddleware` 결정 wire + delay_ms 100~5000ms configurable + jitter_ms ±20% + percentage 0~100% (default 10%) + Phase 8 wire `60d4ea1` 의 p99 latency budget 5s 와의 정합 결정 wire
- F25.2-3 (2) error injection 결정 wire = `inject_error(target, http_status, percentage)` 함수 + HTTP middleware `ErrorFaultMiddleware` 결정 wire + http_status 500/502/503/504 configurable + percentage 0~100% (default 5%) + Sentry breadcrumb 결정 wire
- F25.2-4 (3) resource exhaustion (CPU + memory) 결정 wire = `stress_cpu(target, cores)` + `stress_memory(target, mb)` 함수 + `cgroups` 또는 `resource` library AD-14 stack pin 결정 wire + cores 1~N configurable + mb 100~N configurable + OS-level fault injection 결정 wire
- F25.2-5 (4) network partition (latency + drop + bandwidth) 결정 wire = `network_partition(target, delay_ms, drop_pct, bandwidth_kbps)` 함수 + Linux `tc netem` AD-14 stack pin 결정 wire + target service 간 traffic 제어 결정 wire + Phase 5 wire `f093f8c` multi-region network chaos EXTENSION 결정 wire
- F25.2-6 (5) disk I/O stress 결정 wire = `disk_io_stress(target, iops_limit, read_pct)` 함수 + `fio` AD-14 stack pin 결정 wire + iops_limit 100~10000 configurable + read_pct 0~100% 결정 wire
- F25.2-7 (6) database connection pool exhaustion 결정 wire = `db_connection_pool_exhaust(target, max_connections)` 함수 + PostgreSQL `max_connections` + connection pool size 동적 조정 결정 wire + Alembic migration 통한 connection pool config 결정 wire
- F25.2-8 (7) cache failure (Redis + Supabase cache) 결정 wire = `cache_failure(target, operation: Literal["read_miss", "write_fail", "eviction_burst"])` 함수 + Supabase cache eviction burst 결정 wire + Phase 7 wire `59b56cd` observability 정합 결정 wire
- F25.2-9 (8) DNS failure 결정 wire = `dns_failure(target, domains: list[str])` 함수 + `/etc/hosts` 또는 DNS resolver 조작 결정 wire + Supabase auth + Sentry + Slack DNS 의존도 정합 결정 wire
- F25.2-10 (9) process kill 결정 wire = `kill_process(target, signal: Literal["SIGTERM", "SIGKILL", "SIGSTOP"])` 함수 + FastAPI worker process target 결정 wire + auto-restart via Railway `restartPolicyType=ON_FAILURE` Phase 4 wire 정합 결정 wire
- F25.2-11 (10) clock skew 결정 wire = `clock_skew(target, offset_seconds)` 함수 + `libfaketime` AD-14 stack pin 결정 wire + offset_seconds ±86400 configurable + JWT `exp` + audit log timestamp 영향 검증 결정 wire
- F25.2-12 fault injection CR 0-2 RLS verbatim 적용 결정 wire + chaos experiment 의 tenant_id selector + cross-tenant isolation 검증 결정 wire

### §F25.3 game day runbook + blast radius control (12 sub-ACs)
- F25.3-1 `docs/chaos-engineering.md` NEW (~+200 LOC 14 sections runbook 결정 wire)
- F25.3-2 Quarterly game day schedule 결정 wire = Phase 5 wire `f093f8c` 의 DR drill quarterly schedule (Q1 January + Q2 April + Q3 July + Q4 October, KST 1st Sunday 03:00 = UTC 18:00 cron) 의 자연스러운 EXTENSION 결정 wire + chaos game day + DR drill 통합 quarterly schedule 결정 wire
- F25.3-3 `apps/api/jobs/chaos_game_day.py` NEW (~+150 LOC + cron KST 1st Sunday 03:00 = UTC 18:00 + 8 game day steps 결정 wire)
- F25.3-4 Game day 8 steps 결정 wire = (1) experiment selection + (2) tenant scoping (L2 single_tenant default, staging tenant only) + (3) blast radius confirmation (owner-only + 2FA 챌린지 Epic 12 정합) + (4) steady state baseline 측정 (Phase 8 wire 의 baseline capture 5min) + (5) fault injection + (6) observation (Phase 7 wire `59b56cd` 의 OpenTelemetry + Prometheus + Sentry + Slack + PagerDuty) + (7) auto-rollback (F25.6 결정) + (8) post-mortem report
- F25.3-5 Post-mortem report `docs/chaos-game-day-{yyyymmdd}.md` NEW 결정 wire + 5 sections (experiment summary + observed metrics + auto-rollback performance + blast radius assessment + follow-up actions)
- F25.3-6 Game day runbook 14 sections 결정 wire = (1) 목적 + (2) 책임자 (owner + SRE on-call) + (3) 사전 준비 (tenant scoping + blast radius + 2FA 챌린지) + (4) communication channel (Slack `#chaos-game-day` channel + PagerDuty escalation) + (5) experiment schedule + (6) abort conditions + (7) rollback strategy + (8) observation checklist + (9) post-mortem template + (10) lessons learned archive + (11) quarterly review + (12) safety mechanisms + (13) compliance & audit (audit-first INSERT 4 NEW actions CR 1-1 verbatim) + (14) continuous improvement
- F25.3-7 Blast radius control 5 levels implementation 결정 wire = L1 single_request (테스트 환경 only) + L2 single_tenant (staging tenant only, 기본값) + L3 all_tenants (production 환경, owner-only + 2FA 챌린지 필수, audit-first INSERT `chaos_experiment_started` with payload `{blast_radius: "all_tenants", two_factor_challenge: true}`) + L4 single_region (Phase 5 multi-region 정합, primary Seoul 만 chaos) + L5 multi_region (DR drill 정합, primary Seoul + secondary Tokyo 동시 chaos, audit-first INSERT + Sentry critical alert)
- F25.3-8 game day audit-first INSERT 결정 wire (4 NEW actions: `chaos_experiment_started` + `chaos_experiment_completed` + `chaos_experiment_aborted` + `chaos_rollback_triggered` CR 1-1 verbatim)
- F25.3-9 game day owner-only RBAC 결정 wire (L3~L5 blast radius + manual abort + 2FA 챌린지 Epic 12 정합 + AD-22 verbatim)
- F25.3-10 game day dry-run mode 결정 wire (game day dry_run=True flag + audit-first INSERT `chaos_experiment_dryrun` 결정 wire)
- F25.3-11 game day Phase 7 wire `59b56cd` observability integration 결정 wire (OpenTelemetry distributed tracing + Prometheus custom metrics + Sentry breadcrumb + Slack `#chaos-game-day` channel + PagerDuty integration)
- F25.3-12 game day post-mortem report generation 결정 wire (markdown template + owner review + audit-first INSERT `chaos_post_mortem_generated` 결정 wire)

### §F25.4 continuous chaos vs scheduled game day (10 sub-ACs)
- F25.4-1 `apps/api/jobs/continuous_chaos.py` NEW (~+120 LOC + continuous chaos decision 결정 wire)
- F25.4-2 Continuous chaos (production-safe) 결정 wire = L1 single_request blast radius 만 + low intensity + 5% traffic + dry_run default + auto-rollback 30s 이내 결정 wire + 4 production-safe experiment candidates: (a) `cost-engine-latency-injection-100ms` (Phase 8 SLA p99 < 5s 의 2%) + (b) `auth-error-injection-1pct` (Phase 8 login p99 < 1s 정합) + (c) `audit-log-query-latency-injection-50ms` (Phase 8 audit log p99 < 2s SLA 의 2.5%) + (d) `multi-region-replication-lag-injection` (Phase 5 replication lag 100MB threshold 정합) 결정 wire
- F25.4-3 Scheduled game day 결정 wire = quarterly cron KST 1st Sunday 03:00 = UTC 18:00 (Phase 5 DR drill schedule 정합) + multi-experiment 동시 실행 (latency + error + resource + network partition 4 types) + L2~L5 blast radius (owner-only + 2FA 챌린지 Epic 12 정합) + Slack `#chaos-game-day` channel 실시간 communication + PagerDuty integration owner-only AD-22 RBAC 결정 wire
- F25.4-4 Production-safe guard 4 rules 결정 wire = (a) blast radius L1 only (single_request) + (b) intensity low only + (c) percentage ≤ 5% traffic + (d) duration ≤ 60s + (e) auto-rollback ≤ 30s + (f) dry_run default (audit-first INSERT `chaos_experiment_dryrun`) + (g) Sentry breadcrumb + Slack notification 결정 wire
- F25.4-5 Continuous chaos statistics 결정 wire = Prometheus custom metrics (Phase 7 wire `59b56cd` 의 `business_chaos_experiments_total{experiment_name, blast_radius, outcome}` Counter + `business_chaos_auto_rollback_total{experiment_name, trigger}` Counter + `business_chaos_observations_seconds` Histogram 결정 wire) + 5% traffic 의 production 환경 의미 있는 chaos data 수집 + graph: chaos experiments per day + auto-rollback time p99 + experiment success rate
- F25.4-6 continuous_chaos audit-first INSERT 결정 wire (`chaos_experiment_started` 1 NEW action + ActionClass.CHAOS_ENGINEERING 결정 wire + CR 1-1 verbatim 적용)
- F25.4-7 continuous_chaos owner-only RBAC 결정 wire (continuous chaos toggle + experiment selection + intensity + percentage 모두 owner-only AD-22 RBAC + Epic 12 2FA 챌린지 보존 결정 wire)
- F25.4-8 continuous_chaos dry-run mode 결정 wire (dry_run=True flag default + audit-first INSERT `chaos_experiment_dryrun` + no actual fault injection)
- F25.4-9 continuous_chaos per-tenant on/off 결정 wire (capability gate CHAOS_ENGINEERING per-tenant on/off + tenant_settings.chaos_engineering_enabled JSONB override)
- F25.4-10 continuous_chaos baseline freeze 결정 wire (Phase 8 wire `60d4ea1` 의 baseline freeze pattern verbatim 미러 + steady_state_metric baseline 30d rolling)

### §F25.5 tenant-scoped + multi-region chaos (10 sub-ACs)
- F25.5-1 `apps/api/modules/chaos/tenant_scoping.py` NEW (~+80 LOC + multi-region chaos decision 결정 wire)
- F25.5-2 Tenant-scoped chaos 결정 wire = `tenant_id` UUID RLS 자동 적용 (CR 0-2 RLS lesson 적용) + L2 single_tenant blast radius 의 tenant_id selector 결정 wire + cross-tenant isolation test (Epic 1 carry-over 정합) + audit-first INSERT `chaos_experiment_started` 에 tenant_id 포함 결정 wire + 미허용 tenant 의 chaos 진입 차단 결정 wire
- F25.5-3 Multi-region chaos 결정 wire = Phase 5 wire `f093f8c` 의 multi-region failover (cj-style 75번째) 정합 + `region: Literal["seoul", "tokyo", "all"]` selector + L4 single_region + L5 multi_region blast radius 결정 wire + cross-region chaos 시 primary Seoul → secondary Tokyo failover 자동 트리거 검증 (Phase 5 failover_orchestrator 정합) + audit-first INSERT `chaos_experiment_started` 에 `from_region` + `to_region` 포함 결정 wire
- F25.5-4 `apps/api/alembic/versions/0041_phase_9_chaos_engineering.py` NEW (~+150 LOC + `phase_9_chaos_experiments` table 결정 wire)
- F25.5-5 phase_9_chaos_experiments table 14 columns 결정 wire = BIGSERIAL id + tenant_id UUID FK + experiment_id TEXT UNIQUE + experiment_name TEXT + fault_type TEXT enum 10 values + blast_radius TEXT enum 5 values + region TEXT enum seoul/tokyo/all + steady_state_metric TEXT + hypothesis TEXT + duration_seconds INTEGER + intensity TEXT enum low/medium/high + status TEXT enum pending/running/completed/aborted/failed + dry_run BOOLEAN DEFAULT TRUE + started_at TIMESTAMPTZ + completed_at TIMESTAMPTZ + actor_id UUID FK users(id) + trace_id TEXT + created_at TIMESTAMPTZ DEFAULT NOW()
- F25.5-6 phase_9_chaos_experiments table indexes 결정 wire = 3 indexes (tenant_id+status+started_at DESC + experiment_id UNIQUE + region+status+started_at DESC)
- F25.5-7 phase_9_chaos_experiments table CHECK constraints 결정 wire = 2 CHECK constraints (fault_type enum + blast_radius enum)
- F25.5-8 phase_9_chaos_experiments RLS policy 결정 wire (CR 0-2 verbatim + `tenant_id = current_setting('app.tenant_id')::uuid` + Phase 5 wire `f093f8c` phase_5_replication_lag table 정합)
- F25.5-9 Multi-tenant isolation test 결정 wire = `tests/integration/test_chaos_tenant_isolation.py` NEW + Phase 5 wire 의 `tests/integration/test_multi_region_replication_lag.py` + Phase 7 wire 의 `tests/integration/test_observability_tenant_isolation.py` 패턴 verbatim 적용 + L2 single_tenant chaos 가 다른 tenant 에 영향 없음 검증 + L3 all_tenants chaos 가 명시적 tenant 에만 영향 검증 결정 wire
- F25.5-10 Multi-region chaos failover verification 결정 wire = Phase 5 wire `f093f8c` failover_orchestrator 자동 트리거 검증 + cross-region chaos 시 primary Seoul → secondary Tokyo failover 자동 트리거 + RPO 1h / RTO 4h 정합 결정 wire

### §F25.6 auto-rollback + safety mechanisms (10 sub-ACs)
- F25.6-1 `apps/api/modules/chaos/auto_rollback.py` NEW (~+150 LOC + safety mechanisms 결정 wire)
- F25.6-2 Auto-rollback 4 strategies 결정 wire = (a) **automatic** (abort condition trigger 시 30s 이내 fault 제거 + steady state 복귀 검증) / (b) **manual** (owner-only + 2FA 챌린지 Epic 12 정합, `POST /api/v1/admin/chaos/{experiment_id}/abort` endpoint + audit-first INSERT `chaos_experiment_aborted` CR 1-1 verbatim) / (c) **hybrid** (5min 이상 진행 시 manual confirm 필요) / (d) **scheduled abort** (duration_seconds 만료 시 자동 abort) 결정 wire
- F25.6-3 Safety mechanisms 6 layers 결정 wire = (1) abort conditions 4 rules (F25.1 결정) + (2) blast radius 5 levels (F25.1 결정) + (3) owner-only RBAC AD-22 (L3~L5 blast radius + manual abort + 2FA 챌린지 Epic 12 정합) + (4) dry-run mode default (audit-first INSERT `chaos_experiment_dryrun` action, no actual fault injection) + (5) steady state verification (auto-rollback 후 5min baseline recovery 검증) + (6) circuit breaker (5 consecutive experiments failure 시 1h cool-down + Sentry alert + Slack `#bizup-alerts` channel 결정 wire)
- F25.6-4 Audit-first INSERT 4 NEW actions 결정 wire (CR 1-1 verbatim + ActionClass.CHAOS_ENGINEERING 신규 정의 + 4 NEW AuditAction Literal values: `chaos_experiment_started` + `chaos_experiment_completed` + `chaos_experiment_aborted` + `chaos_rollback_triggered` + apps/api/core/audit_action.py MODIFIED AuditAction Literal EXTENSION 4 NEW values + _ActionRegistry CHAOS_ENGINEERING entry 신규 4개 등록 + __all__ EXTENSION + emit_audit_typed BEFORE chaos experiment CR 1-1 verbatim 적용)
- F25.6-5 Integration with Phase 5 failover + Phase 7 alerting 결정 wire = L5 multi_region chaos 시 Phase 5 wire `f093f8c` failover_orchestrator 자동 트리거 검증 + Phase 7 wire `59b56cd` 의 Prometheus AlertManager + Sentry alert routing + Slack `#bizup-alerts` channel + PagerDuty integration EXTENSION + Phase 8 wire `60d4ea1` 의 p99 latency budget 5s 와의 정합 (chaos experiment 중 p99 > 5s 시 auto-abort 결정 wire)
- F25.6-6 auto_rollback audit-first INSERT 결정 wire (`chaos_rollback_triggered` 1 NEW action + ActionClass.CHAOS_ENGINEERING 결정 wire + CR 1-1 verbatim 적용 + emit_audit_typed BEFORE rollback 실행)
- F25.6-7 auto_rollback owner-only RBAC 결정 wire (manual abort + rollback strategy selection + duration override 모두 owner-only AD-22 RBAC + Epic 12 2FA 챌린지 보존 결정 wire)
- F25.6-8 auto_rollback dry-run mode 결정 wire (dry_run=True flag default + audit-first INSERT `chaos_rollback_dryrun` + no actual rollback execution)
- F25.6-9 auto_rollback Sentry integration 결정 wire (Phase 4 wire `71a033a` Sentry `tracesSampleRate=0.1` carry-over + Sentry breadcrumb capture_message 결정 wire)
- F25.6-10 auto_rollback Slack integration 결정 wire (Phase 7 wire `59b56cd` `#bizup-alerts` channel carry-over + rollback notification + circuit breaker alert 결정 wire)

### §F25.7 dry-run + Tests + wire scope (12 sub-ACs)
- F25.7-1 Phase 9 wire scope T1~T8 결정 wire (T1 chaos_experiment + fault_injection module + T2 chaos_game_day job + T3 continuous_chaos job + T4 alembic 0041 phase_9_chaos_engineering + T5 audit action EXTENSION 4 NEW + T6 capability v1.34 EXTENSION + T7 frontend chaos dashboard + T8 atomic commit 결정 wire)
- F25.7-2 Phase 9 wire estimated files ~16 NEW + ~9 MODIFIED = ~25 files atomic single sprint 결정 wire
- F25.7-3 Phase 9 wire backend tests 결정 wire (~30 NEW pytest PASS 결정 wire: chaos_experiment TypedDict 5 + fault_injection 4 + chaos_game_day 4 + continuous_chaos 4 + alembic 0041 3 + audit action 6 + capability matrix v1.34 4 = ~30 NEW pytest PASS)
- F25.7-4 Phase 9 wire frontend tests 결정 wire (~5 NEW vitest PASS 결정 wire: chaos dashboard 3 + SSOT drift 2 = ~5 NEW vitest PASS)
- F25.7-5 Phase 9 wire 0 NEW ruff 결정 wire (apps/api backend 결정 wire + 기존 ruff scoped 0 NEW 정합 보존)
- F25.7-6 Phase 9 wire 0 NEW tsc 결정 wire (apps/web frontend 결정 wire + 기존 tsc 0 NEW 정합 보존)
- F25.7-7 Phase 9 wire 0 regressions 결정 wire (3중 게이트 FINAL CLEAN + ruff scoped 0 NEW + pytest 0 NEW failures + vitest 0 NEW failures + tsc 0 NEW errors)
- F25.7-8 Phase 9 wire dry-run mode 결정 wire (dry-run UI 진입 시 dry_run=True flag + 0 actual chaos_experiment + 0 actual fault_injection + 0 actual auto_rollback)
- F25.7-9 Phase 9 wire audit-first INSERT 결정 wire (4 NEW audit log entries 결정 wire: `chaos_experiment_started` + `chaos_experiment_completed` + `chaos_experiment_aborted` + `chaos_rollback_triggered` + ActionClass.CHAOS_ENGINEERING 신규 정의)
- F25.7-10 Phase 9 wire capability gate CHAOS_ENGINEERING 결정 wire (capability matrix v1.33 → v1.34 EXTENSION 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅ + drift detector `tests/integration/test_capability_matrix_v1_34_drift.py` NEW 결정 wire)
- F25.7-11 Phase 9 wire atomic commit via `git commit -F <file>` 결정 wire (CR 9-6 D5 prevention + PowerShell here-string 회피 결정 wire)
- F25.7-12 Phase 9 wire scope T1~T8 정합 sweep 결정 wire (Epic 1 ~ Epic 17 + Phase 3 ~ Phase 8 + 1st release cycle 정합 보존 + 결정 회피 0건 보장 + CR lessons applied 14종 + D-DEFER-* tracking 결정 wire)

## 8 tasks (T1~T8) + 68 subtasks

### T1: chaos_experiment + fault_injection module (13 subtasks)
- T1.1: `apps/api/modules/chaos/` NEW 디렉토리 + chaos modules SSOT 디렉토리 결정 wire
- T1.2: `apps/api/modules/chaos/chaos_experiment.py` NEW (~+150 LOC + ChaosExperiment TypedDict 13 fields + 5 blast_radius levels + 4 abort conditions + AbortCondition TypedDict + 10 fault types registry 결정 wire)
- T1.3: `apps/api/modules/chaos/fault_injection.py` NEW (~+200 LOC + 10 fault types implementation + LatencyFaultMiddleware + ErrorFaultMiddleware + resource stress + network partition + disk I/O + DB connection pool + cache failure + DNS failure + process kill + clock skew 결정 wire)
- T1.4: chaos_experiment TypedDict validation 결정 wire (pydantic v2 model_validator + blast_radius enum 검증 + intensity enum 검증 + abort_conditions list 검증 + duration_seconds 1~600 검증)
- T1.5: fault_injection 10 types SSOT 결정 wire (latency + error + resource + network partition + disk I/O + DB connection pool + cache failure + DNS failure + process kill + clock skew)
- T1.6: chaos_experiment audit-first INSERT 결정 wire (`chaos_experiment_started` 1 NEW action + ActionClass.CHAOS_ENGINEERING + CR 1-1 verbatim)
- T1.7: chaos_experiment owner-only RBAC 결정 wire (L3~L5 blast radius + manual abort + 2FA 챌린지 Epic 12 정합 + `require_role("owner")` 결정 wire)
- T1.8: chaos_experiment dry-run mode default 결정 wire (dry_run=True flag + audit-first INSERT `chaos_experiment_dryrun` + no actual fault injection)
- T1.9: fault_injection CR 0-2 RLS verbatim 적용 결정 wire + tenant_id selector + cross-tenant isolation 검증 결정 wire
- T1.10: fault_injection AD-14 stack pin 결정 wire (cgroups/resource lib + tc netem + fio + libfaketime + AD-14 verbatim stack pin)
- T1.11: chaos_experiment baseline freeze 결정 wire (Phase 8 wire `60d4ea1` 의 baseline freeze pattern verbatim 미러 + 30d rolling baseline)
- T1.12: chaos_experiment CR 1-1 ContextVar lesson verbatim 적용 결정 wire (trace_id request-scoped ContextVar 바인딩 + 비동기 trace context 보존)
- T1.13: chaos_experiment TypedDict 5 NEW pytest cases 결정 wire (TypedDict validation + blast_radius enum + abort_conditions rules + dry_run default + owner_only RBAC)

### T2: chaos_game_day job (10 subtasks)
- T2.1: `apps/api/jobs/chaos_game_day.py` NEW (~+150 LOC + quarterly cron KST 1st Sunday 03:00 = UTC 18:00 + 8 game day steps + post-mortem report generation 결정 wire)
- T2.2: `docs/chaos-engineering.md` NEW (~+200 LOC + 14 sections runbook 결정 wire)
- T2.3: Quarterly game day schedule 결정 wire = Phase 5 wire `f093f8c` DR drill quarterly schedule (Q1 January + Q2 April + Q3 July + Q4 October, KST 1st Sunday 03:00 = UTC 18:00 cron) 의 자연스러운 EXTENSION 결정 wire
- T2.4: Game day 8 steps 결정 wire (experiment selection + tenant scoping + blast radius confirmation + steady state baseline 측정 + fault injection + observation + auto-rollback + post-mortem report)
- T2.5: Post-mortem report `docs/chaos-game-day-{yyyymmdd}.md` NEW 결정 wire (5 sections: experiment summary + observed metrics + auto-rollback performance + blast radius assessment + follow-up actions)
- T2.6: Game day runbook 14 sections 결정 wire (목적 + 책임자 + 사전 준비 + communication channel + experiment schedule + abort conditions + rollback strategy + observation checklist + post-mortem template + lessons learned archive + quarterly review + safety mechanisms + compliance & audit + continuous improvement)
- T2.7: Blast radius control 5 levels implementation 결정 wire (L1~L5 + L3~L5 owner-only + 2FA 챌린지 Epic 12 정합)
- T2.8: Game day audit-first INSERT 결정 wire (4 NEW actions: `chaos_experiment_started` + `chaos_experiment_completed` + `chaos_experiment_aborted` + `chaos_rollback_triggered` CR 1-1 verbatim)
- T2.9: Game day Phase 7 wire `59b56cd` observability integration 결정 wire (OpenTelemetry + Prometheus + Sentry + Slack + PagerDuty integration 결정 wire)
- T2.10: Game day 4 NEW pytest cases 결정 wire (game day steps execution + abort conditions trigger + post-mortem generation + blast radius confirmation)

### T3: continuous_chaos job (8 subtasks)
- T3.1: `apps/api/jobs/continuous_chaos.py` NEW (~+120 LOC + 4 production-safe experiment candidates + 5% traffic + auto-rollback 30s + Prometheus custom metrics 결정 wire)
- T3.2: Continuous chaos (production-safe) 결정 wire = L1 single_request blast radius 만 + low intensity + 5% traffic + dry_run default + auto-rollback 30s 이내 결정 wire
- T3.3: 4 production-safe experiment candidates 결정 wire (`cost-engine-latency-injection-100ms` + `auth-error-injection-1pct` + `audit-log-query-latency-injection-50ms` + `multi-region-replication-lag-injection`)
- T3.4: Production-safe guard 4 rules 결정 wire (blast radius L1 only + intensity low only + percentage ≤ 5% + duration ≤ 60s + auto-rollback ≤ 30s + dry_run default + Sentry + Slack notification)
- T3.5: Continuous chaos statistics 결정 wire = Prometheus custom metrics (`business_chaos_experiments_total` + `business_chaos_auto_rollback_total` + `business_chaos_observations_seconds` + 5% traffic chaos data 수집 + graph dashboards)
- T3.6: continuous_chaos audit-first INSERT 결정 wire (`chaos_experiment_started` 1 NEW action + ActionClass.CHAOS_ENGINEERING + CR 1-1 verbatim)
- T3.7: continuous_chaos owner-only RBAC 결정 wire (continuous chaos toggle + experiment selection + intensity + percentage 모두 owner-only AD-22 + Epic 12 2FA 챌린지 보존)
- T3.8: continuous_chaos 4 NEW pytest cases 결정 wire (continuous chaos statistics + production-safe guard 4 rules + Prometheus metrics emission + auto-rollback timing)

### T4: alembic 0041 phase_9_chaos_engineering (8 subtasks)
- T4.1: `apps/api/alembic/versions/0041_phase_9_chaos_engineering.py` NEW (~+150 LOC + phase_9_chaos_experiments table 결정 wire)
- T4.2: phase_9_chaos_experiments table 14 columns 결정 wire (BIGSERIAL id + tenant_id UUID FK + experiment_id TEXT UNIQUE + experiment_name TEXT + fault_type TEXT enum 10 values + blast_radius TEXT enum 5 values + region TEXT enum seoul/tokyo/all + steady_state_metric TEXT + hypothesis TEXT + duration_seconds INTEGER + intensity TEXT enum low/medium/high + status TEXT enum 5 values + dry_run BOOLEAN DEFAULT TRUE + started_at TIMESTAMPTZ + completed_at TIMESTAMPTZ + actor_id UUID FK users(id) + trace_id TEXT + created_at TIMESTAMPTZ DEFAULT NOW())
- T4.3: phase_9_chaos_experiments table 3 indexes 결정 wire (tenant_id+status+started_at DESC + experiment_id UNIQUE + region+status+started_at DESC)
- T4.4: phase_9_chaos_experiments table 2 CHECK constraints 결정 wire (fault_type enum + blast_radius enum)
- T4.5: phase_9_chaos_experiments RLS policy 결정 wire (CR 0-2 verbatim + `tenant_id = current_setting('app.tenant_id')::uuid` + Phase 5 wire `f093f8c` phase_5_replication_lag table 정합)
- T4.6: `tests/integration/test_chaos_tenant_isolation.py` NEW multi-tenant isolation test 결정 wire (Phase 5 wire `tests/integration/test_multi_region_replication_lag.py` + Phase 7 wire `tests/integration/test_observability_tenant_isolation.py` 패턴 verbatim)
- T4.7: Multi-region chaos failover verification 결정 wire (Phase 5 wire `f093f8c` failover_orchestrator 자동 트리거 검증 + RPO 1h / RTO 4h 정합)
- T4.8: alembic migration 3 NEW pytest cases 결정 wire (alembic migration + RLS policy + CHECK constraints)

### T5: audit action EXTENSION 4 NEW (9 subtasks)
- T5.1: `apps/api/core/audit_action.py` MODIFIED (ActionClass.CHAOS_ENGINEERING 신규 정의 + ChaosAction Literal 4 NEW values + _ActionRegistry CHAOS_ENGINEERING entry 신규 4개 등록 + __all__ EXTENSION + AuditAction Union EXTENSION 결정 wire)
- T5.2: ActionClass.CHAOS_ENGINEERING = 'chaos_engineering' 신규 정의 결정 wire (CR 12-1 L4 precedent 미러 PERFORMANCE_TESTING + OBSERVABILITY_TRACES + OBSERVABILITY_METRICS + AUDIT_LOG_RETENTION + AUDIT_LOG_VIEW + MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER + TENANT_IDP_MANAGEMENT + SSO_ENTERPRISE + LISTEN_NOTIFY + AUTH_MIDDLEWARE + LAUNCH_* + DEPLOYMENT_* pattern verbatim bind)
- T5.3: ChaosAction Literal 4 NEW values 결정 wire = `chaos_experiment_started` + `chaos_experiment_completed` + `chaos_experiment_aborted` + `chaos_rollback_triggered` (CR 1-1 verbatim 적용 + payload structure 정의)
- T5.4: _ActionRegistry CHAOS_ENGINEERING entry 신규 4개 등록 결정 wire (resource_table "chaos_experiments" + action_class=CHAOS_ENGINEERING + 4 NEW actions acceptance + reject 결정 wire)
- T5.5: AuditAction Union EXTENSION 결정 wire (apps/api/core/audit_action.py MODIFIED + ChaosAction Union 추가 + type alias update 결정 wire)
- T5.6: emit_audit_typed BEFORE chaos experiment CR 1-1 verbatim 적용 결정 wire (chaos_experiment_started 의 audit_first INSERT 가 chaos experiment 시작 직전에 실행 + trace_id propagation + actor_id capture + tenant_id capture)
- T5.7: multi-tenant isolation 결정 wire (chaos_experiment_started 의 tenant_id 가 RLS 와 정합 + cross-tenant audit log leak 방지 결정 wire)
- T5.8: AuditAction Literal EXTENSION 검증 결정 wire (apps/api/main.py EXTENSION + chaos endpoints 의 audit_first INSERT 호출 + typed exception envelope CR 12-5 D-14 적용)
- T5.9: 6 NEW pytest cases 결정 wire (AuditAction Literal 값 검증 + ActionClass.CHAOS_ENGINEERING enum value + resource_table "chaos_experiments" + emit_audit_typed BEFORE chaos experiment CR 1-1 verbatim 적용 + multi-tenant isolation + trace_id propagation)

### T6: capability v1.34 EXTENSION (8 subtasks)
- T6.1: `apps/api/core/capability.py` MODIFIED (Capability.CHAOS_ENGINEERING = 'chaos_engineering' 1 NEW enum + 4 `_INDUSTRY_CAPABILITIES` blocks EXTENSION industry-agnostic ✅/✅/✅/✅ CR 12-1 L4 precedent 미러)
- T6.2: `apps/api/dependencies/capability.py` MODIFIED (require_chaos_engineering 1 NEW dep + __all__ EXTENSION 결정 wire)
- T6.3: capability matrix v1.33 → v1.34 EXTENSION title update + v1.34 changelog entry prepend + 1 NEW row CHAOS_ENGINEERING industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire
- T6.4: `tests/integration/test_capability_matrix_v1_34_drift.py` NEW 4 NEW pytest cases 결정 wire (Capability.CHAOS_ENGINEERING enum + 4 industries grants + v1.33 + v1.32 + v1.31 preservation + Phase 5 v1.29 + Epic 16 v1.28 + Epic 17 v1.30 + Phase 6 v1.31 + Phase 7 v1.32 + Phase 8 v1.33 pattern verbatim)
- T6.5: `docs/capability-matrix.md` MODIFIED v1.33 → v1.34 EXTENSION 결정 wire (1 NEW row CHAOS_ENGINEERING industry-agnostic 4-industry grants)
- T6.6: 미허용 tenant 의 chaos engineering 진입 차단 결정 wire (require_chaos_engineering dep + capability gate per-tenant on/off)
- T6.7: chaos engineering capability gate 적용 대상 명시 결정 wire (require_chaos_engineering → /admin/chaos/* endpoints + chaos_game_day cron + continuous_chaos cron)
- T6.8: SSOT RED→GREEN EXTENSION 결정 wire (capability matrix v1.34 신규 1 row + capability.py EXTENSION 1 NEW enum + require_capability() Dependency 1개 신규 wire + drift detector EXTENSION)

### T7: frontend chaos dashboard (8 subtasks)
- T7.1: `apps/web/app/[locale]/(dashboard)/admin/chaos/page.tsx` NEW (~+150 LOC + 4 components: ChaosExperimentList + ChaosExperimentTriggerButton + ChaosGameDayCalendar + ChaosRollbackLog 결정 wire)
- T7.2: `apps/web/messages/ko-KR.json` MODIFIED (EXTENSION `chaos.*` namespace ~25 keys: sla_dashboard_title + chaos_section_label + chaos_experiment_label + chaos_trigger_button + chaos_game_day_label + chaos_blast_radius_label + chaos_dry_run_label + chaos_abort_button + chaos_rollback_log_label + chaos_observation_label + chaos_post_mortem_label + chaos_safety_mechanisms_label + chaos_tenant_scope_label + chaos_region_selector_label + chaos_intensity_label + chaos_duration_label + chaos_abort_conditions_label + chaos_steady_state_label + chaos_hypothesis_label + chaos_success_rate_label + chaos_auto_rollback_label + loading_chaos + error_chaos_failed + error_owner_only + empty_state 결정 wire)
- T7.3: ChaosExperimentTriggerButton 결정 wire (owner-only ack prompt AD-22 verbatim + 2FA 챌린지 Epic 12 정합 + blast radius selector + intensity selector + dry_run toggle)
- T7.4: ChaosGameDayCalendar 결정 wire (quarterly schedule + KST 1st Sunday 03:00 = UTC 18:00 cron 시각화 + post-mortem report link 결정 wire)
- T7.5: ChaosRollbackLog 결정 wire (auto-rollback history + audit-first INSERT entries RTL render + trace_id propagation display 결정 wire)
- T7.6: chaos dashboard i18n NFR18 ko-KR 정합 결정 wire (CR 11-4 D-002 verbatim SSOT only + page_title='카오스 대시보드' verbatim invariant + all keys non-empty 검증 결정 wire)
- T7.7: chaos dashboard CR 12-5 D-PARITY-01 verbatim 검증 결정 wire (Python FastAPI backend chaos_experiment.py TypedDict ↔ TypeScript Next.js frontend chaos-dashboard.tsx interface parity 결정 wire + vitest CR 12-5 D-PARITY-01 검증 결정 wire)
- T7.8: 5 NEW vitest cases 결정 wire (ChaosExperimentTriggerButton owner-only ack prompt AD-22 verbatim + ChaosGameDayCalendar ko-KR SSOT + ChaosRollbackLog RTL render + chaos dashboard parity CR 12-5 D-PARITY-01 + SSOT drift detection)

### T8: atomic commit (4 subtasks)
- T8.1: 3중 게이트 impact NONE 결정 wire (ruff scoped 0 NEW + pytest 0 NEW failures + vitest 0 NEW failures + tsc 0 NEW errors)
- T8.2: A19 cohesion pattern 9 surface EXTENSION PASS 결정 wire (chaos engineering surface NEW = F25.1~F25.7)
- T8.3: atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention + PowerShell here-string 회피)
- T8.4: sprint-status.yaml `phase-9-spec-entry: backlog → done` transition 결정 wire

## Dev Notes (CR lessons applied 14종)

- **CR 0-2 RLS lesson ✅ APPLIED**: Phase 9 wire 시점에 chaos_experiment 결과 RLS 자동 적용 + multi-region RLS isolation 결정 wire + multi-tenant isolation test 결정 wire + tenant_id selector L2 single_tenant + Phase 5 wire 의 phase_5_replication_lag table 정합
- **CR 1-1 audit-first INSERT ✅ APPLIED**: ActionClass.CHAOS_ENGINEERING 신규 정의 + 4 NEW audit log entries (`chaos_experiment_started` + `chaos_experiment_completed` + `chaos_experiment_aborted` + `chaos_rollback_triggered`) 결정 wire + emit_audit_typed BEFORE chaos_experiment 시작 CR 1-1 verbatim 적용
- **CR 4-3/4-4 lessons carry ✅ APPLIED**: chaos_experiment baseline + steady_state_metric baseline 30d rolling + golden_diff pattern verbatim 미러 + tenant-scoped result_hash 결정 wire + Epic 8 wire `e117e09` capability drift detector 정합 패턴 + Epic 17 wire `2ada2ec` audit_log_query baseline benchmark result_hash 패턴 verbatim
- **CR 1-1 ContextVar lesson ✅ APPLIED**: trace_id request-scoped ContextVar 바인딩 + 비동기 trace context 보존 CR 1-1 verbatim 적용 + chaos experiment 의 trace_id propagation 결정 wire
- **CR 1-1 RSC boundary lesson ✅ APPLIED**: `apps/web/app/[locale]/(dashboard)/admin/chaos/page.tsx` Client-only + chaos dashboard server-only delegation 결정 wire + CR 1-1 verbatim 적용
- **CR 9-6 commit message discipline ✅ APPLIED**: `git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention 결정 wire
- **CR 11-3 honest-DEFER discipline ✅ APPLIED**: 98번째 epic 연속 정직 회복 결정 wire (D-1-1-DEFER-* + D-EPIC-16-REVIEW-DEFER-* + D-PHASE-4-DR-DEFER-* + D-EPIC-17-WIRE-DEFER-T2-T3-UI + D-RETENTION-1 + D-OBSERVABILITY-1 + D-PERFORMANCE-1 모두 ✅ ALL RESOLVED 보존 + D-CHAOS-1 honestly DEFER 보존 진입 결정)
- **CR 11-4 D-001~D-005 + P-015 lessons carry ✅ APPLIED**: dry-run mode UI 진입 시 frontend territory 정합 sweep 결정 wire + ko-KR.json SSOT only + vitest RTL render discipline + owner-only RBAC + unknown state reject + ko-KR.json SSOT drift detector 결정 wire
- **CR 12-1 L4 industry-agnostic capability ✅ APPLIED**: CHAOS_ENGINEERING industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire + capability matrix v1.34 EXTENSION 결정 wire
- **CR 12-5 D-14 typed exception envelope ✅ APPLIED**: ChaosExperimentInvalidBlastRadiusError(400) + ChaosExperimentOwnerOnlyForbiddenError(403) + ChaosRollbackTriggerFailedError(409) + ContinuousChaosProductionUnsafeError(422) 결정 wire + apps/api/main.py EXTENSION 결정 wire
- **CR 12-5 D-PARITY-01 inversion ✅ APPLIED**: Python FastAPI backend chaos_experiment.py TypedDict ↔ TypeScript Next.js frontend chaos-dashboard.tsx interface parity 결정 wire + vitest CR 12-5 D-PARITY-01 검증 결정 wire
- **CR 12-5 D-GATE-01 inversion ✅ APPLIED**: CHAOS_ENGINEERING capability gate per-tenant on/off + owner-only RBAC AD-22 결정 wire + gate 적용 대상 명시 결정 wire
- **A19 cohesion pattern 9 surface EXTENSION PASS ✅**: chaos engineering surface NEW + spec surface EXTENSION + test surface EXTENSION 결정 wire 보존
- **A36 SDR 검증 4-step 자동 적용 ✅**: commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS 결정 wire
- **AD-14 stack pin ✅ APPLIED**: cgroups/resource lib + tc netem + fio + libfaketime + 기존 webpack esbuild 결정 wire
- **AD-22 owner-only RBAC ✅ APPLIED**: chaos_experiment trigger + manual abort + rollback strategy selection + duration override + chaos_game_day + continuous_chaos toggle + experiment selection + intensity + percentage 모두 owner-only RBAC AD-22 결정 wire + Epic 12 2FA 챌린지 보존 결정 wire
- **NFR4 PII minimization ✅ PRESERVED**: chaos experiment payload 의 PII 마스킹 결정 wire + AES-256-GCM NFR6 PII data masking 결정 wire + audit log payload encryption at rest 결정 wire

## Architecture Alignment (cj-style ALLOWED sweep)

ALLOWED_SERVICE_SUBMODULES sweep 결정 wire (CR 11-3 D-2 verbatim + Epic 9 + Epic 16 + Phase 5 wire 정합):
- `m3_calculate.services.calculation_serializers` (Epic 3 wire)
- `m4_abc.abc_allocation_serializers` (Epic 9 wire)
- `m4_tdabc.tdabc_allocation_serializers` (Epic 9 wire)
- `m5_ai_extraction.extraction_serializers` (Epic 10 wire)
- `m7_audit.audit_log_serializers` (Epic 17 wire)
- `m8_budget.budget_pre_standard_serializers` (Epic 8 wire)
- `m9_abc.abc_allocation_serializers` (Epic 9 wire)
- `m10_ai_extraction.extraction_serializers` (Epic 10 wire)
- `m13_audit.audit_log_query_serializers` (Epic 17 wire)
- `m14_audit.audit_log_retention_serializers` (Phase 6 wire)
- `m15_audit.audit_log_query_serializers` (Phase 7 wire)
- `m16_performance_testing.performance_testing_serializers` (Phase 8 wire)
- **`m17_chaos_engineering.chaos_engineering_serializers`** (NEW Phase 9)

## Files Affected (estimated ~25 files atomic single sprint)

### ~16 NEW files
1. `apps/api/modules/chaos/chaos_experiment.py` (T1.2)
2. `apps/api/modules/chaos/fault_injection.py` (T1.3)
3. `apps/api/modules/chaos/auto_rollback.py` (F25.6)
4. `apps/api/modules/chaos/tenant_scoping.py` (T1.1, F25.5)
5. `apps/api/jobs/chaos_game_day.py` (T2.1)
6. `apps/api/jobs/continuous_chaos.py` (T3.1)
7. `apps/api/alembic/versions/0041_phase_9_chaos_engineering.py` (T4.1)
8. `docs/chaos-engineering.md` (T2.2)
9. `apps/api/core/test_phase_9_chaos_experiment.py` (T1.13, 5 NEW pytest)
10. `apps/api/core/test_phase_9_fault_injection.py` (T1.13, 4 NEW pytest)
11. `apps/api/core/test_phase_9_chaos_game_day.py` (T2.10, 4 NEW pytest)
12. `apps/api/core/test_phase_9_continuous_chaos.py` (T3.8, 4 NEW pytest)
13. `apps/api/core/test_phase_9_audit_action.py` (T5.9, 6 NEW pytest)
14. `tests/integration/test_capability_matrix_v1_34_drift.py` (T6.4, 4 NEW pytest)
15. `tests/integration/test_chaos_tenant_isolation.py` (T4.6, 3 NEW pytest)
16. `apps/web/app/[locale]/(dashboard)/admin/chaos/page.tsx` (T7.1)
17. `apps/web/__tests__/chaos-dashboard.test.tsx` (T7.8, 3 NEW vitest)
18. `apps/web/__tests__/i18n/chaos-i18n-ssot.test.ts` (T7.8, 2 NEW vitest)

### ~9 MODIFIED files
1. `apps/api/core/audit_action.py` (ActionClass.CHAOS_ENGINEERING + 4 NEW actions) (T5.1-T5.5)
2. `apps/api/core/capability.py` (CHAOS_ENGINEERING + INDUSTRY_CAPABILITIES EXTENSION) (T6.1)
3. `apps/api/dependencies/capability.py` (require_chaos_engineering) (T6.2)
4. `apps/api/main.py` (chaos endpoints + 4 NEW exception handlers) (T5.8)
5. `apps/api/pyproject.toml` (libfaketime + tc netem + fio + cgroups stack pin) (T1.10)
7. `apps/web/messages/ko-KR.json` (EXTENSION `chaos.*` namespace ~25 keys) (T7.2)
8. `docs/capability-matrix.md` (v1.33 → v1.34 EXTENSION) (T6.5)
9. `_bmad-output/planning-artifacts/prd.md` (master PRD v3.9 → v4.0 ALREADY DONE in cj-style 97번째)
10. `_bmad-output/implementation-artifacts/sprint-status.yaml` (phase-9-spec-entry: backlog → done + A288~A292) (T8.4)
11. `memory/MEMORY.md` (handoff hook EXTENSION) (T8)
12. `_bmad-output/implementation-artifacts/commit-msg-phase-9-spec-entry.txt` (NEW commit message file) (T8)

= **18 NEW + 12 MODIFIED = ~30 files atomic single sprint** (cj-style 98번째 standard docs-only)

## Test Coverage (estimated)

- **Backend**: ~30 NEW pytest PASS (chaos_experiment 5 + fault_injection 4 + chaos_game_day 4 + continuous_chaos 4 + alembic 0041 3 + audit action 6 + capability matrix v1.34 4 = ~30 NEW pytest PASS)
- **Frontend**: ~5 NEW vitest PASS (chaos dashboard 3 + SSOT drift 2 = ~5 NEW vitest PASS)
- **0 NEW ruff + 0 NEW tsc + 0 regressions**
- **SDR drift gate**: PASS (pytest +6 NEW files collected, vitest +3 NEW files collected)

## Story Header

- story_key: phase-9-chaos-engineering-wire
- baseline_commit: 0b2d2f3 (Phase 9 PRD entry commit)
- status: ready-for-dev
- cj_style_entry_point: 98

## Dev Agent Record

(To be filled in by bmad-dev-story)

## Cross-references

- Phase 9 PRD entry: `memory/handoff-2026-08-24-phase-9-prd-entry-done.md`
- Phase 8 PRD entry: `memory/handoff-2026-08-24-phase-8-prd-entry-done.md`
- Phase 8 spec entry: `memory/handoff-2026-08-24-phase-8-spec-entry-done.md`
- Phase 8 atomic wire: `memory/handoff-2026-08-24-phase-8-wire-done.md`
- Phase 8 close-out retro: `memory/handoff-2026-08-24-phase-8-close-out-done.md`
- Phase 7 PRD entry: `memory/handoff-2026-08-23-phase-7-prd-entry-done.md`
- Phase 7 spec entry: `memory/handoff-2026-08-23-phase-7-spec-entry-done.md`
- Phase 7 atomic wire: `memory/handoff-2026-08-23-phase-7-wire-done.md`
- Phase 7 close-out retro: `memory/handoff-2026-08-23-phase-7-close-out-done.md`
- Phase 6 close-out retro: `memory/handoff-2026-08-22-phase-6-close-out-done.md`
- Phase 5 close-out retro: `memory/handoff-2026-08-22-phase-5-close-out-done.md`
- Phase 5 wire (multi-region failover carry-over): `memory/handoff-2026-08-22-phase-5-multi-region-backup-wire-done.md`
- Phase 7 wire (observability stack carry-over): `memory/handoff-2026-08-23-phase-7-wire-done.md`
- Phase 8 wire (performance / load testing carry-over): `memory/handoff-2026-08-24-phase-8-wire-done.md`
- Epic 17 wire (audit_log_query baseline carry-over): `memory/handoff-2026-08-22-epic-17-wire-done.md`