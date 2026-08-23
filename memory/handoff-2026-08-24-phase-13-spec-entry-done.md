---
name: handoff-2026-08-24-phase-13-spec-entry-done
description: Phase 13 spec entry DONE (cj-style 114번째). FinOps Forecasting & Capacity Planning territory 결정 wire + 5 files atomic docs-only wire + 8 ACs §F29.1~§F29.8 verbatim → 92 sub-ACs + T1~T8 68 subtasks + ~30 files estimate + ~51 NEW pytest + ~5 NEW vitest + 0 NEW ruff + 0 regressions. A399~A403.
metadata:
  type: project
---

# Phase 13 bmad-create-story atomic spec entry DONE

## 결정 wire 핵심
- **cj-style 진입점**: 114번째 (Phase 13 2번째 진입점 = spec entry 진입점)
- **territory**: FinOps Forecasting & Capacity Planning
- **baseline_commit**: `d31dfc8` (Phase 13 PRD entry tip = cj-style 113번째 wire DONE 진입 시점)
- **wire scope**: 3 NEW + 2 MODIFIED = 5 files atomic single sprint (docs only)
- **sprint-status**: v3.25 → v3.26 EXTENSION (A399~A403 action_items 신규 block 5 entries)

## 옵션 진입 결정 wire
- **옵션 (a)** Phase 13 bmad-create-story spec entry 진입 (Recommended) — Phase 13 PRD entry 진입 직후 자연스러운 next
- **rationale 5종**:
  1. cj-style discipline 회피 위험 방지 = 113번째 Phase 13 PRD entry 진입 직후 자연스러운 spec entry 진입 결정 wire (105~113번째 누적 9-entry-point cycle 모두 wire DONE 진입 정합 보존 + Phase 12 close-out retro `3354e83` 112번째 + Phase 12 atomic wire T1~T8 `f3c0e63` 111번째 + Phase 12 spec entry `8c5f374` 110번째 + Phase 12 PRD entry `344c7eb` 109번째 + Phase 11 close-out retro `80df15b` 108번째 + Phase 11 atomic wire T1~T8 `e020ad0` 107번째 + Phase 11 spec entry `82c93a8` 106번째 + Phase 11 PRD entry `16d7698` 105번째 패턴 verbatim 미러)
  2. FinOps Forecasting & Capacity Planning territory 결정 wire = Phase 12 wire `f3c0e63` Cost Anomaly Detection & Budget Alerting territory (anomaly detection baseline last 30d/90d/YTD + forecast accuracy tracking MAE/MAPE/RMSE) 의 natural backend FORECASTING & PLANNING LAYER EXTENSION (historical baseline → forward forecast EXTENSION 12-month prediction with 95% CI + budget overrun linear extrapolation → ARIMA/Prophet/LSTM time series forecast + forecast accuracy 의 MAE/MAPE/RMSE → forward-looking forecasting engine + capacity planning 의 compute/storage/network saturation 90일 lookahead + budget burn-rate projection territory 의 natural next) + Phase 11 wire `e020ad0` showback period selector (current/previous/last 3/6 months/YTD) + Phase 8 wire `60d4ea1` cost-engine 12-period benchmark 의 자연스러운 carry-over chain 정합 보존 + Epic 12 2FA 챌린지 보존 + AD-22 owner-only RBAC 보존 + D-FINOPS-3 honestly DEFER 보존 진입 결정 wire + Phase 12 close-out retro `3354e83` §13 verbatim 해소 결정 wire
  3. Epic 1 ~ Epic 17 + Phase 3 ~ Phase 12 + 1st release cycle 모두 wire DONE 정합 보존 후 spec entry 진입 결정 wire
  4. Phase 13 spec 8 ACs PRD §F29.1~§F29.8 verbatim → 92 sub-ACs + T1~T8 + 68 subtasks + Dev Notes 14종 + Architecture Alignment cj-style ALLOWED sweep 결정 wire 보존
  5. AD-22 owner-only RBAC + Epic 12 2FA 챌린지 보존 + AD-14 stack pin + NFR4 PII minimization ✅ PRESERVED

## F29.1~F29.8 8 ACs + 92 sub-ACs 결정 wire

### F29.1 forecast definition DSL (12 sub-ACs, A401 결정)
- F29.1.1: `apps/api/modules/finops/forecast_definition.py` NEW ~+150 LOC + define_forecast builder + AST 5 levels
- F29.1.2: ForecastDefinition TypedDict 11 fields (forecast_id + tenant_id + target_metric enum + dimension_value + horizon_months enum + model_type enum + confidence_level enum + retraining_cron + status enum + created_at + updated_at)
- F29.1.3: 5 target_metrics 옵션 (department + cost_center + product_line + service + tenant_total)
- F29.1.4: 4 horizon_months 옵션 (3m + 6m + 12m + 24m)
- F29.1.5: FORECAST_DEFAULTS constants (horizon_months=12 + model_type='ensemble' + confidence_level=95 + retraining_cron='0 3 * * 0')
- F29.1.6: 4 industries baseline industry-agnostic
- F29.1.7: parse_forecast_definition pure validator CR 11-4 P-015 verbatim
- F29.1.8: audit-first INSERT `forecast_definition_updated` CR 1-1 verbatim
- F29.1.9: typed exception envelope CR 12-5 D-14 (3 NEW typed exception classes: ForecastDefinitionInvalidError(400) + ForecastScopeInvalidError(400) + ForecastHistoryUnavailableError(422))
- F29.1.10: RLS 자동 적용 CR 0-2 verbatim
- F29.1.11: dry-run mode `--finops-forecast-dry-run` CLI flag
- F29.1.12: V8 determinism byte-identical 테스트

### F29.2 forecast engine 4 methods (12 sub-ACs, A401 결정)
- F29.2.1: `apps/api/modules/finops/forecast_engine.py` NEW ~+200 LOC + generate_forecast builder + 4 time series models parallel run
- F29.2.2: 4 forecast methods (ARIMA + Prophet + LSTM + ensemble) + multi-method voting consensus 4-way
- F29.2.3: ForecastResult TypedDict 10 fields
- F29.2.4: historical baseline source (last 12-month from phase_11_finops_showback + phase_12_finops_anomaly_detection)
- F29.2.5: seasonality detection (weekly + monthly + quarterly + yearly) + STL decomposition + 8 KST holidays
- F29.2.6: ARIMA model statsmodels==0.14.1
- F29.2.7: Prophet model prophet==1.1.5 + 8 KST holidays
- F29.2.8: LSTM model tensorflow==2.15.0
- F29.2.9: ensemble voting consensus (3-of-4 agree)
- F29.2.10: model_version tracking (semantic versioning + JSONB metadata)
- F29.2.11: typed exception envelope CR 12-5 D-14 (3 NEW typed exception classes: ForecastEngineError(500) + ForecastModelTrainingError(500) + ForecastSeasonalityDetectionError(500))
- F29.2.12: dry-run mode `--finops-forecast-dry-run` CLI flag

### F29.3 capacity headroom analyzer 3 resource types + 90일 lookahead (12 sub-ACs, A401 결정)
- F29.3.1: `apps/api/modules/finops/capacity_headroom.py` NEW ~+180 LOC + analyze_capacity_headroom builder + 3 resource type + 90일 lookahead
- F29.3.2: CapacityHeadroomReport TypedDict 14 fields
- F29.3.3: compute resource type (CPU + memory + instance_count + 90일 LSTM primary)
- F29.3.4: storage resource type (DB size + backup storage + 90일 Prophet primary)
- F29.3.5: network resource type (egress + ingress bandwidth + 90일 ARIMA primary)
- F29.3.6: 3 saturation levels (OK + WARNING + CRITICAL)
- F29.3.7: critical threshold alerting (headroom < 20% → Slack + PagerDuty)
- F29.3.8: warning threshold alerting (headroom < 40% → Slack only)
- F29.3.9: capacity metrics source (Prometheus custom metrics + LISTEN/NOTIFY)
- F29.3.10: audit-first INSERT `capacity_headroom_analyzed` CR 1-1 verbatim
- F29.3.11: typed exception envelope CR 12-5 D-14 (3 NEW typed exception classes: CapacityHeadroomAnalysisError(500) + CapacityThresholdBreachError(500) + CapacityMetricUnavailableError(404))
- F29.3.12: dry-run mode `--finops-capacity-dry-run` CLI flag

### F29.4 budget burn-rate projection (12 sub-ACs, A401 결정)
- F29.4.1: `apps/api/modules/finops/budget_burnrate.py` NEW ~+150 LOC + project_budget_consumption builder + 4-input formula
- F29.4.2: 4-input formula (current_consumption + period_elapsed_days + period_total_days + historical_consumption_rate)
- F29.4.3: BurnRateProjection TypedDict 12 fields
- F29.4.4: BudgetOverrunPrediction TypedDict 8 fields
- F29.4.5: 3-level severity routing (warning > 110% + critical > 130% + exceeded > 150%)
- F29.4.6: Phase 12 wire `f3c0e63` budget_alert linear extrapolation EXTENSION
- F29.4.7: ARIMA-based 7/30-day rolling projection
- F29.4.8: alert routing (warning → Slack / critical → Slack + PagerDuty / exceeded → Slack + PagerDuty + Email)
- F29.4.9: alert deduplication 24h
- F29.4.10: audit-first INSERT `budget_burn_rate_projected` CR 1-1 verbatim
- F29.4.11: typed exception envelope CR 12-5 D-14 (2 NEW typed exception classes: BudgetBurnRateProjectionError(500) + BudgetOverrunPredictionError(500))
- F29.4.12: dry-run mode `--finops-burnrate-dry-run` CLI flag

### F29.5 forecast accuracy tracker + model retraining trigger (10 sub-ACs, A401 결정)
- F29.5.1: `apps/api/modules/finops/forecast_accuracy_tracker.py` NEW ~+120 LOC + track_forecast_accuracy builder + per-model accuracy tracking
- F29.5.2: per-model accuracy tracking (per tenant_id + target_metric + model_type 3-tuple granularity)
- F29.5.3: MAE (Mean Absolute Error)
- F29.5.4: MAPE (Mean Absolute Percentage Error) < 10% high accuracy + HIGH_ACCURACY_THRESHOLD 0.10
- F29.5.5: RMSE (Root Mean Squared Error)
- F29.5.6: ensemble vs individual model comparison
- F29.5.7: model performance degradation detection (MAPE > 20% for 3 consecutive periods + RETRAIN_TRIGGER_THRESHOLD 0.20)
- F29.5.8: model retraining trigger (KST 매주 일요일 03:00 UTC 18:00)
- F29.5.9: typed exception envelope CR 12-5 D-14 (3 NEW typed exception classes: ForecastAccuracyTrackingError(500) + ModelRetrainingTriggerError(500) + ModelPerformanceDegradationError(500))
- F29.5.10: ModelRetrainingTrigger TypedDict 8 fields

### F29.6 forecast dashboard UI (10 sub-ACs, A401 결정)
- F29.6.1: `apps/web/app/[locale]/(dashboard)/admin/finops/forecast/page.tsx` NEW ~+150 LOC + 5 components
- F29.6.2: ForecastHorizonSelector component (4 horizon options radio button)
- F29.6.3: ForecastChart component (Recharts 2.12.7 AD-14 stack pin + 95% CI shading)
- F29.6.4: CapacityHeadroomGauge component (Gauge chart + 3 saturation levels)
- F29.6.5: BudgetBurnRatePanel component (3-level severity visualization)
- F29.6.6: ForecastAccuracyPanel component (3 metrics + per-model accuracy table)
- F29.6.7: ko-KR.json `finops_forecast.*` namespace EXTENSION ~30 keys
- F29.6.8: ARIA labels WCAG 2.1 AA + Epic 12 2FA 챌린지 보존
- F29.6.9: toast notification (warning yellow / critical red / exceeded purple)
- F29.6.10: Vitest RTL render discipline CR 11-4 D-003 verbatim

### F29.7 Capability matrix v1.38 EXTENSION (12 sub-ACs, A401 결정)
- F29.7.1: capability matrix v1.37 → v1.38 EXTENSION
- F29.7.2: Capability.FINOPS_FORECASTING_CAPACITY_PLANNING 1 NEW enum
- F29.7.3: `apps/api/dependencies/capability.py` MODIFIED + 1 NEW dep
- F29.7.4: industry-agnostic 4-industry grants ✅/✅/✅/✅ (CR 12-1 L4 precedent 미러)
- F29.7.5: 미허용 tenant 의 forecast 진입 차단 결정 wire
- F29.7.6: drift detector 10 NEW pytest cases
- F29.7.7: m21_finops_forecast module 결정 wire
- F29.7.8: SSOT RED→GREEN EXTENSION + A36 SDR 검증 4-step
- F29.7.9: CR 12-1 L4 industry-agnostic capability
- F29.7.10: capability gate 의 fail-closed 결정 wire
- F29.7.11: capability matrix 의 version 결정 wire v1.37 → v1.38
- F29.7.12: FINOPS_FORECAST section 신규 추가

### F29.8 dry-run + Tests + wire scope T1~T8 (12 sub-ACs)
- F29.8.1: dry-run mode (`--finops-forecast-dry-run` + `--finops-capacity-dry-run` + `--finops-burnrate-dry-run`)
- F29.8.2: dry-run 의 preview 결과 (phase_13_finops_forecast_preview table alembic 0045 신규)
- F29.8.3: dry-run 의 CLI flag 결정 wire
- F29.8.4: tests ~+51 NEW pytest PASS 결정 wire
- F29.8.5: vitest tests ~+5 NEW vitest PASS 결정 wire
- F29.8.6: ruff + tsc 0 NEW + SDR drift gate 결정 wire
- F29.8.7: wire scope T1~T8 결정 wire (~+30 files)
- F29.8.8: A19 cohesion pattern 9 surface EXTENSION PASS 결정 wire
- F29.8.9: CR lessons applied 14종 결정 wire
- F29.8.10: D-DEFER-* honestly 결정 wire (D-FINOPS-3 honestly preserved)
- F29.8.11: Epic 1 ~ Epic 17 + Phase 3 ~ Phase 12 + 1st release cycle 정합 보존
- F29.8.12: partial wire 시도 0건 + single sprint atomic docs-only wire 1 진입점 결정 wire

## A399~A403 5 NEW 결정 wire
- A399 = 옵션 (a) Phase 13 bmad-create-story spec entry 진입 결정 wire (cj-style 114번째)
- A400 = spec 파일 생성 결정 wire = `phase-13-finops-forecasting-capacity-planning-wire.md` (~+450 LOC + baseline_commit `d31dfc8` + status `ready-for-dev` + cj_style_entry_point 114 + Story + 8 ACs §F29.1~§F29.8 verbatim → 92 detailed sub-ACs + T1~T8 + 68 subtasks + Dev Notes 14종 + Architecture Alignment ALLOWED sweep + Files Affected ~30 files estimate)
- A401 = 8 ACs §F29.1~§F29.8 verbatim → 92 sub-ACs 전개 결정 wire
- A402 = Tasks T1~T8 + 68 subtasks 결정 wire
- A403 = sprint-status v3.25 → v3.26 EXTENSION 결정 wire + commit-msg-phase-13-spec-entry.txt 신규 + 5 files atomic docs-only wire

## CR lessons applied 14종 결정 wire 보존
- CR 0-2 RLS lesson ✅ APPLIED (forecast + capacity + accuracy tables RLS 자동 적용)
- CR 1-1 audit-first INSERT ✅ APPLIED (7 NEW audit log entries + ActionClass.FINOPS_FORECAST)
- CR 1-1 ContextVar lesson ✅ APPLIED
- CR 1-1 RSC boundary lesson ✅ APPLIED (admin/finops/forecast page RSC + Client Component delegation)
- CR 4-3/4-4 lessons carry ✅ APPLIED (forecast + capacity baseline + golden_diff pattern verbatim)
- CR 9-6 commit message discipline ✅ APPLIED (git commit -F <file> D5 prevention)
- CR 11-3 honest-DEFER discipline ✅ APPLIED (cj-style 114번째 epic 연속 정직 회복)
- CR 11-4 D-001~D-005 + P-015 ✅ APPLIED (ko-KR.json SSOT only)
- CR 12-1 L4 industry-agnostic capability ✅ APPLIED (FINOPS_FORECASTING_CAPACITY_PLANNING 4-industry grants ✅/✅/✅/✅)
- CR 12-5 D-14 typed exception envelope ✅ APPLIED (14 NEW typed exceptions)
- CR 12-5 D-PARITY-01 inversion ✅ APPLIED
- CR 12-5 D-GATE-01 inversion ✅ APPLIED
- A19 cohesion 9 surface EXTENSION PASS ✅ (FinOps Forecasting & Capacity Planning surface NEW)
- A36 SDR 검증 4-step 자동 적용 ✅
- AD-14 stack pin ✅ APPLIED (statsmodels==0.14.1 + prophet==1.1.5 + tensorflow==2.15.0 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 + Recharts 2.12.7)
- AD-22 owner-only RBAC ✅ APPLIED (forecast definition + forecast generation + capacity headroom + budget burn-rate + model retraining 모두 owner-only RBAC AD-22 + Epic 12 2FA 챌린지 보존)
- NFR4 PII minimization ✅ PRESERVED

## D-DEFER-* honestly 결정 wire 보존
- D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존 60~114번째
- D-EPIC-16-REVIEW-DEFER-2~6 ✅ RESOLVED 보존 78~114번째
- D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED 보존 73~114번째
- D-EPIC-17-WIRE-DEFER-T2-T3-UI ✅ RESOLVED 보존 83~114번째
- D-RETENTION-1 ✅ RESOLVED 보존 85~114번째
- D-OBSERVABILITY-1 ✅ RESOLVED 보존 89~114번째
- D-PERFORMANCE-1 ✅ RESOLVED 보존 93~114번째
- D-CHAOS-1 ✅ RESOLVED 보존 100~114번째
- D-SLO-1 ✅ RESOLVED 보존 101~114번째
- D-FINOPS-1 ✅ RESOLVED 보존 105~114번째
- D-FINOPS-2 ✅ RESOLVED 보존 109~114번째
- **D-FINOPS-3 honestly preserved 보존 → Phase 13 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire 진입 완료**

## Epic 1 ~ Epic 17 + Phase 3 ~ Phase 12 + 1st release cycle 정합 보존
cj-style 114번째 epic 연속 정직 회복 pre-flight 정합 sweep 결정 wire 보존:
- ✅ Phase 13 PRD entry `d31dfc8` (cj-style 113번째)
- ✅ Phase 12 close-out retro `3354e83` (cj-style 112번째)
- ✅ Phase 12 atomic wire T1~T8 `f3c0e63` (cj-style 111번째)
- ✅ Phase 12 spec entry `8c5f374` (cj-style 110번째)
- ✅ Phase 12 PRD entry `344c7eb` (cj-style 109번째)
- ✅ Phase 11 close-out retro `80df15b` (cj-style 108번째)
- ✅ Phase 11 atomic wire T1~T8 `e020ad0` (cj-style 107번째)
- ✅ Phase 11 spec entry `82c93a8` (cj-style 106번째)
- ✅ Phase 11 PRD entry `16d7698` (cj-style 105번째)
- ✅ Phase 10 close-out retro `733d428` (cj-style 104번째)
- ✅ Phase 10 atomic wire T1~T8 `ac5d6c5` (cj-style 103번째)
- ✅ Phase 10 spec entry `3c80ef0` (cj-style 102번째)
- ✅ Phase 10 PRD entry `09db4d4` (cj-style 101번째)
- ✅ Phase 9 close-out retro `634427d` (cj-style 100번째)
- ✅ Phase 9 atomic wire T1~T8 `e7670e1` (cj-style 99번째)
- ✅ Build fixes sprint
- ✅ Phase 8/7/6/5 cycle 모두 wire DONE 진입
- ✅ Epic 17/16/15/14/13 cycle 모두 wire DONE 진입
- ✅ 1st release cycle wire DONE 진입
- ✅ Epic 12 2FA 챌린지 보존 + AD-22 owner-only RBAC 보존
- ✅ Phase 2 close-out baseline 599 passed
- ✅ Epic 1 carry-over + Epic 7~10 ABC/TDABC + AI 인사이트 territory 보존

## 5 files atomic single sprint 결정 wire
1. **NEW** `_bmad-output/implementation-artifacts/phase-13-finops-forecasting-capacity-planning-wire.md` — spec file (~+450 LOC + 8 ACs §F29.1~§F29.8 + 92 sub-ACs + T1~T8 68 subtasks)
2. **MODIFIED** `_bmad-output/implementation-artifacts/sprint-status.yaml` — v3.25 → v3.26 EXTENSION (last_updated_note prepend + A399~A403 action_items 신규 block 5 entries + `phase-13-spec-entry: backlog → done` 신규 entry)
3. **NEW** `_bmad-output/implementation-artifacts/commit-msg-phase-13-spec-entry.txt` — commit message file for atomic sprint (CR 9-6 commit message discipline)
4. **NEW** `memory/handoff-2026-08-24-phase-13-spec-entry-done.md` — this handoff memory file
5. **MODIFIED** `memory/MEMORY.md` — hook index EXTENSION (Phase 13 spec entry hook 신규 + 4-entry-point pattern Phase 13 PRD entry DONE + spec entry DONE 진입 정합 보존)

## next 옵션 5종 결정 wire 보류
- (a) Phase 13 bmad-dev-story atomic wire T1~T8 진입 (cj-style Phase 13 3rd entry = cj-style 115th)
- (b) Phase 13 close-out retro 진입 (cj-style 116th)
- (c) Phase 14+ 진입
- (d) Epic 18+ 진입
- (e) D-DEFER-* follow-up 결정 wire 보류

**Why**: cj-style 114번째 spec entry DONE 진입 완료. Phase 13 2-entry-point pattern (PRD entry DONE + spec entry DONE) 진입 정합 보존. FinOps Cost Anomaly Detection & Budget Alerting territory 의 natural backend FORECASTING & PLANNING LAYER EXTENSION 결정 wire 진입.
**How to apply**: 다음 옵션 (a)~(e) 결정 wire 진입 시점에 본 handoff 참조 + sprint-status v3.26 + MEMORY.md hook index EXTENSION 참조.
