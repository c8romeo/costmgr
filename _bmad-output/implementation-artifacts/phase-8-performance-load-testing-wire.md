---
baseline_commit: ced452f
status: ready-for-dev
cj_style_entry_point: 94
story_key: phase-8-performance-load-testing-wire
---

# Phase 8 Performance/Load Testing wire spec (cj-style 94번째 epic 연속 정직 회복)

## Story

**As a** operations team / SRE / enterprise onboarding lead
**I want** performance/load testing territory 결정 wire (k6 load testing + SLO/SLI definitions + p99 latency budget per endpoint + latency regression detector + performance regression gate CI + cost-engine benchmark V8 golden fixture)
**so that** Epic 17 wire `2ada2ec` audit log query latency p99 SLO 보강 + Phase 5 wire `f093f8c` multi-region failover latency 보강 + Phase 7 wire `59b56cd` observability metrics carry-over 의 자연스러운 next territory 진입 결정 wire + Epic 12 2FA 챌린지 보존 + AD-22 owner-only RBAC 보존 + 1st release close-out retro §6 + Epic 17 close-out retro §11 + Phase 6 close-out retro §13 + Phase 7 close-out retro §10 verbatim territory 해소 결정 wire 보존.

## Context

cj-style Phase 8 2번째 진입점 (cj-style 94번째) 진입 결정 wire 진입 완료:
- Phase 8 PRD entry `ced452f` (cj-style 93번째) DONE 진입 정합 보존
- Phase 7 close-out retro `326fa9f` (cj-style 92번째) + Phase 7 atomic wire T1~T8 `59b56cd` (cj-style 91번째) + Phase 7 spec entry (cj-style 90번째) + Phase 7 PRD entry `916a541` (cj-style 89번째) 결정 wire 모두 DONE 진입 정합 보존
- D-PERFORMANCE-1 honestly DEFER 보존 1 NEW 결정 wire (1st release close-out retro §6 + Epic 17 close-out retro §11 + Phase 6 close-out retro §13 + Phase 7 close-out retro §10 verbatim 해소) 결정 wire 보존
- D-OBSERVABILITY-1 ✅ RESOLVED 보존 진입 결정 wire
- Phase 8 PRD entry 의 7 ACs §F24.1~§F24.7 verbatim 결정 wire 보존

## 7 ACs (PRD §F24.1~§F24.7 verbatim) → 78 detailed sub-ACs

### §F24.1 k6 Load Testing (12 sub-ACs)
- F24.1-1 `apps/api/tests/load/k6/` NEW 디렉토리 결정 wire (k6 scripts SSOT 디렉토리)
- F24.1-2 k6 script `auth-login.js` 결정 wire (Supabase Magic link + OAuth + SSO 4종 통합 부하 테스트 + 동시 100 VU ramp 30s 결정 wire)
- F24.1-3 k6 script `cost-calculation.js` 결정 wire (Epic 9 ABC/TDABC + Epic 7 Story 7-2 projection 통합 부하 + 동시 50 VU 95p curl `< 5s` 결정 wire)
- F24.1-4 k6 script `onboarding-flow.js` 결정 wire (Epic 1 onboarding/industry + Phase 3 wire `1db21d2` auth contract 통합 부하 + 동시 30 VU 결정 wire)
- F24.1-5 k6 script `audit-log-query.js` 결정 wire (Epic 17 wire `2ada2ec` audit_log_query + Epic 12 2FA + Phase 6 wire `24e1cd7` retention 통합 부하 + 동시 20 VU 결정 wire)
- F24.1-6 k6 script `multi-region-failover.js` 결정 wire (Phase 5 wire `f093f8c` multi-region observability carry-over + Seoul region primary + Tokyo replica failover 부하 + 동시 10 VU 결정 wire)
- F24.1-7 k6 scenario summary thresholds 결정 wire (p95/p99 latency + RPS + error rate 임계값 + k6 `thresholds` config)
- F24.1-8 k6 load test runner 결정 wire (`apps/api/core/load_test_runner.py` NEW + k6 subprocess wrapper + k6 JSON output parser)
- F24.1-9 k6 CI integration 결정 wire (GitHub Actions workflow `.github/workflows/load-test.yml` NEW + manual trigger + nightly schedule 결정 wire)
- F24.1-10 k6 scenarios CR 1-1 audit-first INSERT 결정 wire (`performance_test_started` + `performance_test_completed` 2 NEW action_class=PERFORMANCE_TEST)
- F24.1-11 k6 load test owner-only RBAC 결정 wire (manual trigger AD-22 + Epic 12 2FA 챌린지 보존 + `require_role("owner")` 결정 wire)
- F24.1-12 k6 dry-run mode 결정 wire (기본 0 VU + dry-run UI 진입 시 dry_run=True flag)

### §F24.2 SLO/SLI Definitions (12 sub-ACs)
- F24.2-1 `docs/slo-sli.md` NEW 결정 wire (4 SLAs SSOT + NFR22 latency budget 정합 결정 wire)
- F24.2-2 SLA-1 Cost calculation p99 < 5s (95% of requests must complete under 5s in 30d 결정 wire + Epic 7 wire `59b56cd` 의 Prometheus histogram `business_cost_engine_duration_seconds` p99 baseline 정합)
- F24.2-3 SLA-2 Audit log query p99 < 2s (Epic 17 wire `2ada2ec` `audit_log_query` carry-over + Epic 12 2FA 챌린지 보존 + 95% of requests must complete under 2s in 30d 결정 wire)
- F24.2-4 SLA-3 Login p99 < 1s (Epic 1 carry-over + Phase 3 wire `1db21d2` auth contract + Epic 15 wire `5f9e37f` Magic link + OAuth + SSO 통합 부하 + 95% of requests must complete under 1s in 30d 결정 wire)
- F24.2-5 SLA-4 Multi-region failover RTO < 30s (Phase 5 wire `f093f8c` multi-region observability carry-over + 95% of failovers must complete under 30s in 30d 결정 wire)
- F24.2-6 SLO error budget burn rate 알림 결정 wire (Phase 7 wire `59b56cd` alerting.py + alert_rules.yaml 정합 + SLOBurnRate alert rule NEW + error budget 14x burn rate 시 critical alert 결정 wire)
- F24.2-7 SLA window 30d rolling 결정 wire (SLO 측정 주기 결정 wire + 30일 rolling window + 95% target)
- F24.2-8 SLO document owner-only RBAC 결정 wire (SLO 수동 변경 AD-22 owner + Epic 12 2FA 챌린지 보존 + audit-first INSERT `slo_modified` 결정 wire)
- F24.2-9 SLO i18n NFR18 ko-KR 정합 결정 wire (ko-KR SLO dashboard UI label 결정 wire + `apps/web/messages/ko-KR.json` EXTENSION `slo.*` namespace)
- F24.2-10 SLO/SLI GitHub Actions integration 결정 wire (PR 진입 시 SLO 회귀 검증 + nightly SLO evaluation 결정 wire)
- F24.2-11 SLO dry-run mode 결정 wire (slo-sli.md dashboard 진입 시 dry_run=True flag + 0 actual SLO measurement)
- F24.2-12 SLO baseline freeze 결정 wire (Epic 7 wire `59b56cd` Prometheus histogram baseline verbatim migrate + SLO target baseline 30d measurement 결정 wire)

### §F24.3 p99 Latency Budget per endpoint (10 sub-ACs)
- F24.3-1 p99 latency budget config `apps/api/core/latency_budget.py` NEW (~80 LOC + per-endpoint budget DSL 결정 wire)
- F24.3-2 Cost engine per-engine p99 budget 결정 wire (`apps/api/modules/abc` + `apps/api/modules/tdabc` + `apps/api/modules/ai/extraction.py` decision-engine 의 per-engine p99 budget 결정 wire)
- F24.3-3 ESLint v9 rule `apps/api/eslint/latency-budget-rule.js` NEW (latency budget regression detector ESLint rule + CR 12-1 L4 industry-agnostic 정합 결정 wire)
- F24.3-4 Latency budget linter test 결정 wire (`tests/eslint/test_latency_budget_linter.py` NEW + 4 NEW pytest cases PASS 결정 wire)
- F24.3-5 Backend p99 latency budget enforcement 결정 wire (FastAPI middleware `LatencyBudgetMiddleware` 결정 wire + `apps/api/main.py` EXTENSION 결정 wire)
- F24.3-6 Latency budget dry-run mode 결정 wire (dry-run UI 진입 시 latency budget violation logging only, no block 결정 wire)
- F24.3-7 Latency budget per-tenant override 결정 wire (Phase 8 territory 정합 + tenant_settings.latency_budget JSONB override 결정 wire + capability gate PERFORMANCE_TESTING per-tenant on/off)
- F24.3-8 Latency budget audit-first INSERT 결정 wire (`latency_budget_violated` 1 NEW action_class=PERFORMANCE_TEST + CR 1-1 verbatim)
- F24.3-9 Latency budget i18n NFR18 ko-KR 정합 결정 wire (ko-KR latency budget UI label 결정 wire + `apps/web/messages/ko-KR.json` EXTENSION `latency_budget.*` namespace)
- F24.3-10 Latency budget CI gate 결정 wire (CI 진입 시 latency budget regression > 20% 시 PR block 결정 wire)

### §F24.4 Latency Regression Detector (12 sub-ACs)
- F24.4-1 `tests/integration/test_performance_regression.py` NEW CI gate 결정 wire
- F24.4-2 Latency regression detector baseline 결정 wire (Epic 8 wire `e117e09` capability drift detector 정합 패턴 verbatim + Epic 17 wire `2ada2ec` audit_log_query baseline benchmark result_hash 패턴 verbatim)
- F24.4-3 Latency regression detector golden_diff 결정 wire (Epic 7 wire `59b56cd` Prometheus histogram baseline verbatim migrate + golden_diff detector + regression threshold 결정 wire)
- F24.4-4 Latency regression detector run mode 결정 wire (CI 진입 시 자동 + manual trigger AD-22 owner-only RBAC 결정 wire + Epic 12 2FA 챌린지 보존)
- F24.4-5 Latency regression detector audit-first INSERT 결정 wire (`p99_regression_detected` 1 NEW action_class=PERFORMANCE_TEST + CR 1-1 verbatim)
- F24.4-6 Latency regression detector i18n NFR18 ko-KR 정합 결정 wire (ko-KR latency regression UI label 결정 wire + `apps/web/messages/ko-KR.json` EXTENSION `latency_regression.*` namespace)
- F24.4-7 Latency regression detector dry-run mode 결정 wire (dry-run UI 진입 시 dry_run=True flag + 0 actual regression detection)
- F24.4-8 Latency regression detector per-tenant on/off 결정 wire (capability gate PERFORMANCE_TESTING per-tenant on/off)
- F24.4-9 Latency regression detector Sentry integration 결정 wire (Phase 4 wire `71a033a` Sentry `tracesSampleRate=0.1` carry-over + Sentry breadcrumb capture_message 결정 wire)
- F24.4-10 Latency regression detector Slack integration 결정 wire (Phase 7 wire `59b56cd` `#bizup-alerts` channel carry-over + alert notification 결정 wire)
- F24.4-11 Latency regression detector regression threshold 20% 결정 wire (CI 진입 시 p99 regression > 20% 시 PR block 결정 wire + Epic 17 wire `2ada2ec` audit_log_query baseline 정합)
- F24.4-12 Latency regression detector baseline freeze 결정 wire (Epic 7 wire `59b56cd` Prometheus histogram baseline verbatim migrate + 30d rolling baseline 결정 wire)

### §F24.5 Performance Regression Gate CI (8 sub-ACs)
- F24.5-1 `.github/workflows/perf-regression.yml` NEW GitHub Actions workflow 결정 wire
- F24.5-2 Performance regression gate trigger 결정 wire (CI 진입 시 자동 + manual trigger AD-22 owner-only RBAC 결정 wire + Epic 12 2FA 챌린지 보존)
- F24.5-3 Performance regression gate PR block 결정 wire (p99 regression > 20% 시 PR block 결정 wire + `p99_regression_detected` alert 결정 wire)
- F24.5-4 Performance regression gate Sentry integration 결정 wire (Phase 4 wire `71a033a` Sentry `tracesSampleRate=0.1` carry-over + alert routing 결정 wire)
- F24.5-5 Performance regression gate Slack integration 결정 wire (Phase 7 wire `59b56cd` `#bizup-alerts` channel carry-over + PR block notification 결정 wire)
- F24.5-6 Performance regression gate audit-first INSERT 결정 wire (`performance_regression_pr_blocked` 1 NEW action_class=PERFORMANCE_TEST + CR 1-1 verbatim)
- F24.5-7 Performance regression gate dry-run mode 결정 wire (dry-run UI 진입 시 dry_run=True flag + 0 actual PR block)
- F24.5-8 Performance regression gate i18n NFR18 ko-KR 정합 결정 wire (ko-KR performance regression UI label 결정 wire + `apps/web/messages/ko-KR.json` EXTENSION `perf_regression.*` namespace)

### §F24.6 Cost Engine Benchmark V8 Golden (12 sub-ACs)
- F24.6-1 `tests/performance/golden/cost-engine-v8.json` NEW 결정 wire (Epic 7 wire `59b56cd` Prometheus histogram baseline verbatim 미러 + tenant-scoped result_hash)
- F24.6-2 Cost engine benchmark fixture 결정 wire (Epic 7 wire `59b56cd` ABC + TDABC + AI extraction 1000 calculations per fixture tenant baseline + Epic 9 wire ABC/TDABC + Phase 6 wire `24e1cd7` retention 정합)
- F24.6-3 Cost engine benchmark golden_diff detector 결정 wire (CR 4-3/4-4 lessons carry verbatim + Epic 8 wire `e117e09` capability drift detector 정합 패턴)
- F24.6-4 Cost engine benchmark regression threshold 5% 결정 wire (V8 golden diff > 5% 시 `cost_engine_benchmark_invalidated` alert 결정 wire + AD-22 owner-only RBAC verbatim)
- F24.6-5 Cost engine benchmark CI gate 결정 wire (`.github/workflows/cost-engine-benchmark.yml` NEW + CI 진입 시 자동 + manual trigger)
- F24.6-6 Cost engine benchmark audit-first INSERT 결정 wire (`cost_engine_benchmark_invalidated` 1 NEW action_class=PERFORMANCE_TEST + CR 1-1 verbatim)
- F24.6-7 Cost engine benchmark dry-run mode 결정 wire (dry-run UI 진입 시 dry_run=True flag + 0 actual benchmark invalidate)
- F24.6-8 Cost engine benchmark i18n NFR18 ko-KR 정합 결정 wire (ko-KR cost engine benchmark UI label 결정 wire + `apps/web/messages/ko-KR.json` EXTENSION `cost_engine_benchmark.*` namespace)
- F24.6-9 Cost engine benchmark Sentry integration 결정 wire (Phase 4 wire `71a033a` Sentry `tracesSampleRate=0.1` carry-over + alert routing 결정 wire)
- F24.6-10 Cost engine benchmark Slack integration 결정 wire (Phase 7 wire `59b56cd` `#bizup-alerts` channel carry-over + alert notification 결정 wire)
- F24.6-11 Cost engine benchmark owner-only RBAC 결정 wire (manual benchmark invalidate AD-22 + Epic 12 2FA 챌린지 보존)
- F24.6-12 Cost engine benchmark baseline freeze 결정 wire (Epic 7 wire `59b56cd` Prometheus histogram baseline verbatim migrate + V8 golden snapshot taken at release 결정 wire)

### §F24.7 dry-run + Tests + wire scope (12 sub-ACs)
- F24.7-1 Phase 8 wire scope T1~T8 결정 wire (T1 k6 load testing 5 scenarios + T2 SLO/SLI docs + T3 p99 latency budget per endpoint + T4 latency regression detector CI gate + T5 performance regression gate + T6 cost engine benchmark V8 golden + T7 tests + T8 atomic commit 결정 wire)
- F24.7-2 Phase 8 wire estimated files ~20 NEW + ~11 MODIFIED = ~31 files atomic single sprint 결정 wire
- F24.7-3 Phase 8 wire backend tests 결정 wire (~25 NEW pytest PASS 결정 wire: k6 load test runner 8 + latency regression detector 6 + p99 budget linter 4 + SLO/SLI spec test 4 + drift detector 3)
- F24.7-4 Phase 8 wire frontend tests 결정 wire (~10 NEW vitest PASS 결정 wire: SLO dashboard 3 + latency regression UI 2 + SSOT drift 2 + ko-KR SSOT 검증 3)
- F24.7-5 Phase 8 wire 0 NEW ruff 결정 wire (apps/api backend 결정 wire + 기존 ruff scoped 0 NEW 정합 보존)
- F24.7-6 Phase 8 wire 0 NEW tsc 결정 wire (apps/web frontend 결정 wire + 기존 tsc 0 NEW 정합 보존)
- F24.7-7 Phase 8 wire 0 regressions 결정 wire (3중 게이트 FINAL CLEAN + ruff scoped 0 NEW + pytest 0 NEW failures + vitest 0 NEW failures + tsc 0 NEW errors)
- F24.7-8 Phase 8 wire dry-run mode 결정 wire (dry-run UI 진입 시 dry_run=True flag + 0 actual k6 load test + 0 actual latency regression detection + 0 actual benchmark invalidate)
- F24.7-9 Phase 8 wire audit-first INSERT 결정 wire (4 NEW audit log entries 결정 wire: `performance_test_started` + `performance_test_completed` + `p99_regression_detected` + `cost_engine_benchmark_invalidated` + ActionClass.PERFORMANCE_TEST 신규 정의)
- F24.7-10 Phase 8 wire capability gate PERFORMANCE_TESTING 결정 wire (capability matrix v1.32 → v1.33 EXTENSION 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅ + drift detector `tests/integration/test_capability_matrix_v1_33_drift.py` NEW 결정 wire)
- F24.7-11 Phase 8 wire atomic commit via `git commit -F <file>` 결정 wire (CR 9-6 D5 prevention + PowerShell here-string 회피 결정 wire)
- F24.7-12 Phase 8 wire scope T1~T8 정합 sweep 결정 wire (Epic 1 ~ Epic 17 + Phase 3 ~ Phase 7 + 1st release cycle 정합 보존 + 결정 회피 0건 보장 + CR lessons applied 14종 + D-DEFER-* tracking 결정 wire)

## 8 tasks (T1~T8) + 68 subtasks

### T1: k6 Load Testing module (13 subtasks)
- T1.1: `apps/api/tests/load/k6/` NEW 디렉토리 + k6 scripts SSOT 디렉토리
- T1.2: k6 script `auth-login.js` 결정 wire (Supabase Magic link + OAuth + SSO 4종 통합 부하 + 동시 100 VU ramp 30s)
- T1.3: k6 script `cost-calculation.js` 결정 wire (Epic 9 ABC/TDABC + Epic 7 Story 7-2 projection 통합 부하 + 동시 50 VU 95p curl `< 5s`)
- T1.4: k6 script `onboarding-flow.js` 결정 wire (Epic 1 onboarding/industry + Phase 3 wire `1db21d2` auth contract 통합 부하 + 동시 30 VU)
- T1.5: k6 script `audit-log-query.js` 결정 wire (Epic 17 wire `2ada2ec` audit_log_query + Epic 12 2FA + Phase 6 wire `24e1cd7` retention 통합 부하 + 동시 20 VU)
- T1.6: k6 script `multi-region-failover.js` 결정 wire (Phase 5 wire `f093f8c` multi-region observability carry-over + 동시 10 VU)
- T1.7: k6 scenario summary thresholds 결정 wire (p95/p99 latency + RPS + error rate)
- T1.8: `apps/api/core/load_test_runner.py` NEW (~80 LOC + k6 subprocess wrapper + k6 JSON output parser)
- T1.9: `.github/workflows/load-test.yml` NEW GitHub Actions workflow
- T1.10: k6 audit-first INSERT 결정 wire (2 NEW audit logs + ActionClass.PERFORMANCE_TEST)
- T1.11: k6 owner-only RBAC 결정 wire (manual trigger AD-22 + Epic 12 2FA 챌린지 보존)
- T1.12: k6 dry-run mode 결정 wire (dry_run=True flag)
- T1.13: k6 baseline freeze 결정 wire (Epic 7 wire `59b56cd` Prometheus histogram baseline verbatim migrate)

### T2: SLO/SLI docs (10 subtasks)
- T2.1: `docs/slo-sli.md` NEW (~120 LOC + 4 SLAs SSOT + NFR22 latency budget 정합)
- T2.2: SLA-1 Cost calculation p99 < 5s 결정 wire (95% in 30d rolling window)
- T2.3: SLA-2 Audit log query p99 < 2s 결정 wire (Epic 17 wire `2ada2ec` audit_log_query carry-over)
- T2.4: SLA-3 Login p99 < 1s 결정 wire (Epic 1 + Phase 3 + Epic 15 통합 부하)
- T2.5: SLA-4 Multi-region failover RTO < 30s 결정 wire (Phase 5 wire `f093f8c` carry-over)
- T2.6: SLO error budget burn rate 알림 결정 wire (Phase 7 wire `59b56cd` alerting.py 정합)
- T2.7: SLA window 30d rolling 결정 wire
- T2.8: SLO owner-only RBAC 결정 wire (AD-22 owner + Epic 12 2FA 챌린지 보존 + audit-first INSERT `slo_modified`)
- T2.9: SLO i18n NFR18 ko-KR 정합 결정 wire (ko-KR SLO dashboard UI label + `apps/web/messages/ko-KR.json` EXTENSION `slo.*` namespace)
- T2.10: SLO dry-run mode + baseline freeze 결정 wire

### T3: p99 latency budget per endpoint (8 subtasks)
- T3.1: `apps/api/core/latency_budget.py` NEW (~80 LOC + per-endpoint budget DSL)
- T3.2: Cost engine per-engine p99 budget 결정 wire (Epic 9 ABC/TDABC + Epic 7 Story 7-2 projection + Epic 8 AI extraction)
- T3.3: ESLint v9 rule `apps/api/eslint/latency-budget-rule.js` NEW (latency budget regression detector)
- T3.4: `apps/api/main.py` EXTENSION (LatencyBudgetMiddleware + latency_budget_violated exception handler)
- T3.5: Latency budget per-tenant override 결정 wire (tenant_settings.latency_budget JSONB override + capability gate PERFORMANCE_TESTING per-tenant on/off)
- T3.6: Latency budget audit-first INSERT 결정 wire (`latency_budget_violated` 1 NEW action + ActionClass.PERFORMANCE_TEST)
- T3.7: Latency budget i18n NFR18 ko-KR 정합 결정 wire (ko-KR latency budget UI label + `apps/web/messages/ko-KR.json` EXTENSION `latency_budget.*` namespace)
- T3.8: Latency budget CI gate + dry-run mode 결정 wire

### T4: Latency regression detector CI gate (8 subtasks)
- T4.1: `tests/integration/test_performance_regression.py` NEW CI gate 결정 wire
- T4.2: Latency regression detector baseline 결정 wire (Epic 8 wire `e117e09` capability drift detector 정합 패턴)
- T4.3: Latency regression detector golden_diff 결정 wire (Epic 7 wire `59b56cd` Prometheus histogram baseline verbatim migrate + regression threshold)
- T4.4: Latency regression detector run mode 결정 wire (CI 진입 시 자동 + manual trigger AD-22 owner-only RBAC)
- T4.5: Latency regression detector audit-first INSERT 결정 wire (`p99_regression_detected` 1 NEW action + ActionClass.PERFORMANCE_TEST)
- T4.6: Latency regression detector i18n NFR18 ko-KR 정합 결정 wire (ko-KR latency regression UI label + `apps/web/messages/ko-KR.json` EXTENSION `latency_regression.*` namespace)
- T4.7: Latency regression detector Sentry + Slack integration 결정 wire (Phase 4 wire `71a033a` Sentry + Phase 7 wire `59b56cd` Slack carry-over)
- T4.8: Latency regression detector per-tenant on/off + baseline freeze 결정 wire (capability gate PERFORMANCE_TESTING + 30d rolling baseline)

### T5: Performance regression gate CI (6 subtasks)
- T5.1: `.github/workflows/perf-regression.yml` NEW GitHub Actions workflow
- T5.2: Performance regression gate trigger 결정 wire (CI 진입 시 자동 + manual trigger AD-22 owner-only RBAC)
- T5.3: Performance regression gate PR block 결정 wire (p99 regression > 20% 시 PR block + `p99_regression_detected` alert)
- T5.4: Performance regression gate Sentry + Slack integration 결정 wire (Phase 4 + Phase 7 carry-over)
- T5.5: Performance regression gate audit-first INSERT 결정 wire (`performance_regression_pr_blocked` 1 NEW action + ActionClass.PERFORMANCE_TEST)
- T5.6: Performance regression gate dry-run mode + i18n NFR18 ko-KR 정합 결정 wire

### T6: Cost engine benchmark V8 golden (10 subtasks)
- T6.1: `tests/performance/golden/cost-engine-v8.json` NEW 결정 wire (Epic 7 wire `59b56cd` Prometheus histogram baseline verbatim 미러 + tenant-scoped result_hash)
- T6.2: Cost engine benchmark fixture 결정 wire (Epic 7 wire `59b56cd` ABC + TDABC + AI extraction 1000 calculations per fixture tenant baseline)
- T6.3: Cost engine benchmark golden_diff detector 결정 wire (CR 4-3/4-4 lessons carry verbatim + Epic 8 wire `e117e09` capability drift detector 정합 패턴)
- T6.4: Cost engine benchmark regression threshold 5% 결정 wire (V8 golden diff > 5% 시 `cost_engine_benchmark_invalidated` alert)
- T6.5: `.github/workflows/cost-engine-benchmark.yml` NEW CI gate
- T6.6: Cost engine benchmark audit-first INSERT 결정 wire (`cost_engine_benchmark_invalidated` 1 NEW action + ActionClass.PERFORMANCE_TEST)
- T6.7: Cost engine benchmark dry-run mode 결정 wire
- T6.8: Cost engine benchmark i18n NFR18 ko-KR 정합 결정 wire (ko-KR cost engine benchmark UI label + `apps/web/messages/ko-KR.json` EXTENSION `cost_engine_benchmark.*` namespace)
- T6.9: Cost engine benchmark Sentry + Slack integration 결정 wire (Phase 4 + Phase 7 carry-over)
- T6.10: Cost engine benchmark owner-only RBAC + baseline freeze 결정 wire (AD-22 + Epic 12 2FA 챌린지 보존 + V8 golden snapshot)

### T7: Tests (9 subtasks)
- T7.1: `apps/api/core/test_phase_8_load_test_runner.py` NEW (8 NEW pytest cases PASS)
- T7.2: `apps/api/core/test_phase_8_latency_regression.py` NEW (6 NEW pytest cases PASS)
- T7.3: `apps/api/core/test_phase_8_p99_budget.py` NEW (4 NEW linter cases PASS)
- T7.4: `apps/api/core/test_phase_8_slo_sli.py` NEW (4 NEW spec test cases PASS)
- T7.5: `tests/integration/test_capability_matrix_v1_33_drift.py` NEW (3 NEW pytest cases PASS)
- T7.6: `apps/web/__tests__/slo-dashboard.test.tsx` NEW (3 NEW vitest cases PASS)
- T7.7: `apps/web/__tests__/latency-regression.test.tsx` NEW (2 NEW vitest cases PASS)
- T7.8: `apps/web/__tests__/i18n/performance-i18n-ssot.test.ts` NEW (2 NEW vitest SSOT drift cases PASS)
- T7.9: `apps/web/__tests__/i18n/performance-ko-KR-ssot.test.ts` NEW (3 NEW vitest ko-KR SSOT cases PASS)

### T8: atomic commit (4 subtasks)
- T8.1: 3중 게이트 impact NONE 결정 wire (ruff scoped 0 NEW + pytest 0 NEW failures + vitest 0 NEW failures + tsc 0 NEW errors)
- T8.2: A19 cohesion pattern 9 surface EXTENSION PASS 결정 wire (performance/load testing surface NEW)
- T8.3: atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention + PowerShell here-string 회피)
- T8.4: sprint-status.yaml `phase-8-wire: in-progress → done` transition 결정 wire

## Dev Notes (CR lessons applied 14종)

- **CR 0-2 RLS lesson ✅ APPLIED**: Phase 8 wire 시점에 k6 load testing 결과 RLS 자동 적용 + multi-region RLS isolation 결정 wire + multi-tenant isolation test 결정 wire
- **CR 1-1 audit-first INSERT ✅ APPLIED**: ActionClass.PERFORMANCE_TEST 신규 정의 + 4 NEW audit log entries (`performance_test_started` + `performance_test_completed` + `p99_regression_detected` + `cost_engine_benchmark_invalidated`) 결정 wire + emit_audit_typed BEFORE alerting trace verbatim 적용
- **CR 4-3/4-4 lessons carry ✅ APPLIED**: cost-engine benchmark V8 golden fixture + tenant-scoped result_hash + golden_diff detector 결정 wire + Epic 7 wire `59b56cd` Prometheus histogram baseline verbatim migrate
- **CR 1-1 ContextVar lesson ✅ APPLIED**: trace_id request-scoped ContextVar 바인딩 + 비동기 trace context 보존 CR 1-1 verbatim 적용
- **CR 1-1 RSC boundary lesson ✅ APPLIED**: `apps/web/__tests__/slo-dashboard.test.tsx` Client-only + `instrumentation-node.ts` server-only 정합 결정 wire
- **CR 9-6 commit message discipline ✅ APPLIED**: `git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention 결정 wire
- **CR 11-3 honest-DEFER discipline ✅ APPLIED**: 94번째 epic 연속 정직 회복 결정 wire (D-1-1-DEFER-* + D-EPIC-16-REVIEW-DEFER-* + D-PHASE-4-DR-DEFER-* + D-EPIC-17-WIRE-DEFER-T2-T3-UI + D-RETENTION-1 + D-OBSERVABILITY-1 모두 ✅ ALL RESOLVED 보존 + D-PERFORMANCE-1 honestly DEFER 보존 진입 결정)
- **CR 11-4 D-001~D-005 + P-015 lessons carry ✅ APPLIED**: dry-run mode UI 진입 시 frontend territory 정합 sweep 결정 wire + ko-KR.json SSOT only + vitest RTL render discipline + owner-only RBAC + unknown state reject + ko-KR.json SSOT drift detector 결정 wire
- **CR 12-1 L4 industry-agnostic capability ✅ APPLIED**: PERFORMANCE_TESTING industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire + capability matrix v1.33 EXTENSION 결정 wire
- **CR 12-5 D-14 typed exception envelope ✅ APPLIED**: LoadTestRunnerInvalidScenarioError(400) + LatencyRegressionThresholdExceededError(422) + CostEngineBenchmarkInvalidatedError(409) 결정 wire + apps/api/main.py EXTENSION 결정 wire
- **CR 12-5 D-PARITY-01 inversion ✅ APPLIED**: Python FastAPI backend latency_budget.py TypedDict ↔ TypeScript Next.js frontend slo-dashboard.tsx interface parity 결정 wire + vitest CR 12-5 D-PARITY-01 검증 결정 wire
- **CR 12-5 D-GATE-01 inversion ✅ APPLIED**: PERFORMANCE_TESTING capability gate per-tenant on/off + owner-only RBAC AD-22 결정 wire + gate 적용 대상 명시 결정 wire
- **A19 cohesion pattern 9 surface EXTENSION PASS ✅**: performance/load testing surface NEW + spec surface EXTENSION + test surface EXTENSION 결정 wire 보존
- **A36 SDR 검증 4-step 자동 적용 ✅**: commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS 결정 wire
- **AD-14 stack pin ✅ APPLIED**: k6==0.45.0 + 기존 webpack esbuild 결정 wire
- **AD-22 owner-only RBAC ✅ APPLIED**: k6 load test trigger + SLO manual 변경 + latency regression manual trigger + performance regression gate manual trigger + cost engine benchmark invalidate owner-only RBAC AD-22 결정 wire + Epic 12 2FA 챌린지 보존 결정 wire
- **NFR4 PII minimization ✅ PRESERVED**: benchmark fixture payload 의 PII 마스킹 결정 wire + AES-256-GCM NFR6 PII data masking 결정 wire + audit log payload encryption at rest 결정 wire

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
- **`m16_performance_testing.performance_testing_serializers`** (NEW Phase 8)

## Files Affected (estimated ~31 files atomic single sprint)

### ~20 NEW files
1. `apps/api/tests/load/k6/auth-login.js` (T1.2)
2. `apps/api/tests/load/k6/cost-calculation.js` (T1.3)
3. `apps/api/tests/load/k6/onboarding-flow.js` (T1.4)
4. `apps/api/tests/load/k6/audit-log-query.js` (T1.5)
5. `apps/api/tests/load/k6/multi-region-failover.js` (T1.6)
6. `apps/api/core/load_test_runner.py` (T1.8)
7. `apps/api/core/latency_budget.py` (T3.1)
8. `apps/api/eslint/latency-budget-rule.js` (T3.3)
9. `docs/slo-sli.md` (T2.1)
10. `tests/integration/test_performance_regression.py` (T4.1)
11. `tests/performance/golden/cost-engine-v8.json` (T6.1)
12. `.github/workflows/load-test.yml` (T1.9)
13. `.github/workflows/perf-regression.yml` (T5.1)
14. `.github/workflows/cost-engine-benchmark.yml` (T6.5)
15. `apps/api/core/test_phase_8_load_test_runner.py` (T7.1)
16. `apps/api/core/test_phase_8_latency_regression.py` (T7.2)
17. `apps/api/core/test_phase_8_p99_budget.py` (T7.3)
18. `apps/api/core/test_phase_8_slo_sli.py` (T7.4)
19. `tests/integration/test_capability_matrix_v1_33_drift.py` (T7.5)
20. `apps/web/__tests__/slo-dashboard.test.tsx` (T7.6)
21. `apps/web/__tests__/latency-regression.test.tsx` (T7.7)
22. `apps/web/__tests__/i18n/performance-i18n-ssot.test.ts` (T7.8)
23. `apps/web/__tests__/i18n/performance-ko-KR-ssot.test.ts` (T7.9)

### ~11 MODIFIED files
1. `apps/api/core/audit_action.py` (ActionClass.PERFORMANCE_TEST + 4 NEW actions)
2. `apps/api/core/capability.py` (PERFORMANCE_TESTING + INDUSTRY_CAPABILITIES EXTENSION)
3. `apps/api/dependencies/capability.py` (require_performance_testing)
4. `apps/api/main.py` (LatencyBudgetMiddleware + 3 NEW exception handlers)
5. `apps/api/pyproject.toml` (k6==0.45.0 AD-14 stack pin)
6. `apps/web/messages/ko-KR.json` (EXTENSION `slo.*` + `latency_budget.*` + `latency_regression.*` + `perf_regression.*` + `cost_engine_benchmark.*` namespaces ~25 keys)
7. `docs/capability-matrix.md` (v1.32 → v1.33 EXTENSION)
8. `_bmad-output/planning-artifacts/prd.md` (master PRD v3.8 → v3.9 ALREADY DONE in cj-style 93번째)
9. `_bmad-output/implementation-artifacts/sprint-status.yaml` (phase-8-wire: in-progress → done + A263~A272)
10. `memory/MEMORY.md` (handoff hook EXTENSION)
11. `_bmad-output/implementation-artifacts/commit-msg-phase-8-wire.txt` (NEW commit message file)

= **23 NEW + 11 MODIFIED = ~34 files atomic single sprint** (cj-style 95번째 standard docs-and-source)

## Test Coverage (estimated)

- **Backend**: ~25 NEW pytest PASS (k6 load test runner 8 + latency regression detector 6 + p99 budget linter 4 + SLO/SLI spec test 4 + drift detector 3)
- **Frontend**: ~10 NEW vitest PASS (SLO dashboard 3 + latency regression UI 2 + SSOT drift 2 + ko-KR SSOT 검증 3)
- **0 NEW ruff + 0 NEW tsc + 0 regressions**
- **SDR drift gate**: PASS (pytest +6 NEW files collected, vitest +5 NEW files collected)

## Story Header

- story_key: phase-8-performance-load-testing-wire
- baseline_commit: ced452f (Phase 8 PRD entry commit)
- status: ready-for-dev
- cj_style_entry_point: 94

## Dev Agent Record

(To be filled in by bmad-dev-story)

## Cross-references

- Phase 8 PRD entry: `memory/handoff-2026-08-24-phase-8-prd-entry-done.md`
- Phase 7 PRD entry: `memory/handoff-2026-08-23-phase-7-prd-entry-done.md`
- Phase 7 spec entry: `memory/handoff-2026-08-23-phase-7-spec-entry-done.md`
- Phase 7 atomic wire: `memory/handoff-2026-08-23-phase-7-wire-done.md`
- Phase 7 close-out retro: `memory/handoff-2026-08-23-phase-7-close-out-done.md`
- Phase 6 close-out retro: `memory/handoff-2026-08-22-phase-6-close-out-done.md`
- Phase 5 close-out retro: `memory/handoff-2026-08-22-phase-5-close-out-done.md`
- Epic 17 wire (audit_log_query baseline carry-over): `memory/handoff-2026-08-22-epic-17-wire-done.md`
- Phase 5 wire (multi-region observability carry-over): `memory/handoff-2026-08-22-phase-5-multi-region-backup-wire-done.md`
- Phase 7 wire (observability metrics carry-over): `memory/handoff-2026-08-23-phase-7-wire-done.md`
