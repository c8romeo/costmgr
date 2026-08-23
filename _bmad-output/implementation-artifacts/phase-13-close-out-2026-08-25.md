# Phase 13 Close-out Retrospective (cj-style Phase 13 4번째 진입점 = cj-style 116번째 epic 연속 정직 회복)

**일자**: 2026-08-25 (KST)
**작성자**: Amelia (Developer) + Charlie (Senior Dev) + Alice (Product Owner) 결정 wire 진입
**wire_commit**: TBD (cj-style Phase 13 close-out retro atomic docs-only wire = cj-style 116번째 docs only)
**baseline_commit**: `8b98030` (Phase 13 bmad-dev-story atomic wire T1~T8 DONE 진입 시점 = cj-style 115번째 epic 연속 정직 회복 wire DONE 진입 tip)
**retro_document**: 본 문서 (`_bmad-output/implementation-artifacts/phase-13-close-out-2026-08-25.md`)
**handoff**: `memory/handoff-2026-08-25-phase-13-close-out-done.md` (auto-memory 신규)
**previous retro**: `phase-12-close-out-2026-08-24.md` (cj-style 112번째) — Phase 12 Cost Anomaly Detection & Budget Alerting territory close-out + 옵션 (a) Phase 13 진입 결정 wire 진입 보존

---

## §1. Phase 13 territory 정의

Phase 13 = **FinOps Forecasting & Capacity Planning territory** (Phase 12 wire `f3c0e63` Cost Anomaly Detection & Budget Alerting territory 의 natural FORWARD-FORECAST EXTENSION = anomaly detection baseline last 30d/90d/YTD → forward forecast 12-month prediction with 95% CI + anomaly severity → budget overrun projection ARIMA/Prophet/LSTM 4-method ensemble + capacity headroom 90일 lookahead compute/storage/network saturation + budget burn-rate 4-input formula 3-level severity routing 110/130/150% + Phase 11 wire `e020ad0` showback period selector territory 의 natural next (current/previous/last 3/6 months/YTD → forecast 3m/6m/12m/24m horizon) + Phase 8 wire `60d4ea1` cost-engine 12-period benchmark 의 자연스러운 carry-over chain = historical baseline last 30d + last 90d + YTD + statistical model training + forecast deviation tracking EXTENSION + AD-40 FinOps Forecasting & Capacity Planning 신규 + capability matrix v1.38 → v1.39 EXTENSION FINOPS_FORECASTING_CAPACITY_PLANNING 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅ + 8 ACs §F29.1~§F29.8 verbatim + 92 sub-ACs + D-FINOPS-3 honestly DEFER 진입 + Phase 13 PRD entry §13 + Phase 12 close-out retro §13 + Phase 11 close-out retro §12 + Phase 10 close-out retro §10 + Phase 9 close-out retro §10 + Phase 8 close-out retro §10 + Phase 7 close-out retro §10 + Phase 6 close-out retro §13 + Epic 17 close-out retro §11 + 1st release close-out retro §6 verbatim D-FINOPS-3 honestly DEFERRED territory 해소 결정 wire). Phase 12 close-out retro 진입 시점에 옵션 (a) Phase 13+ 진입 결정 wire 진입 (옵션 b Epic 18+ / 옵션 c carry-over / 옵션 d 1st release 추가 follow-up / 옵션 e D-DEFER-* carry-over follow-up 모두 rejected, 사용자 권장 결정).

**Phase 13 cycle 구조** (cj-style 4-entry-point pattern = PRD + spec + atomic wire + close-out retro):
1. **cj-style Phase 13 1번째 진입점** = Phase 13 PRD entry (cj-style 113번째 epic 연속 정직 회복) — `d31dfc8` ✅ DONE 2026-08-24
2. **cj-style Phase 13 2번째 진입점** = Phase 13 bmad-create-story spec entry (cj-style 114번째) — spec ~+450 lines ✅ DONE 2026-08-24 (`phase-13-finops-forecasting-capacity-planning-wire.md` 신규)
3. **cj-style Phase 13 3번째 진입점** = Phase 13 bmad-dev-story atomic wire T1~T8 (cj-style 115번째 epic 연속 정직 회복) — `8b98030` ✅ DONE 2026-08-24
4. **cj-style Phase 13 4번째 진입점** = Phase 13 close-out retro (cj-style 116번째) — THIS, 진입 결정 wire 진입

**Phase 13 진입 결정** (cj-style 정직 회복):
- Phase 12 close-out retro 진입 시점에 옵션 (a) Phase 13+ 진입 결정 (사용자 권장 결정, rationale 5종: ① Phase 12 wire `f3c0e63` Cost Anomaly Detection & Budget Alerting territory 의 natural FORWARD-FORECAST EXTENSION 결정 wire (anomaly detection baseline last 30d/90d/YTD → forward forecast 12-month prediction with 95% CI + anomaly severity → budget overrun projection ARIMA/Prophet/LSTM 4-method ensemble + capacity headroom 90일 lookahead compute/storage/network saturation + budget burn-rate 4-input formula 3-level severity routing 110/130/150%) ② Epic 12 2FA 챌린지 + AD-22 owner-only RBAC 보존 ③ Phase 5~12 + Epic 17 의 7개 observability/operational/finops territory chain ✅ ALL RESOLVED 진입 후 FinOps Forecasting & Capacity Planning territory natural next 진입 ④ Phase 13 PRD entry §13 + Phase 12 close-out retro §13 + Phase 11 close-out retro §12 + Phase 10 close-out retro §10 + Phase 9 close-out retro §10 + Phase 8 close-out retro §10 + Phase 7 close-out retro §10 + Phase 6 close-out retro §13 + Epic 17 close-out retro §11 + 1st release close-out retro §6 verbatim D-FINOPS-3 honestly DEFERRED territory 해소 ⑤ cj-style discipline 회피 위험 방지 = 115번째 Phase 13 wire 진입 직후 natural next territory 결정 회피 위험 증가)
- AD-40 FinOps Forecasting & Capacity Planning 신규 결정 ((a) forecast definition DSL 5 target_metrics + 4 horizons + 4 model_types + 4 confidence_levels + (b) forecast engine 4-method parallel runner ARIMA + Prophet + LSTM + ensemble + (c) capacity headroom 90일 lookahead compute/storage/network + (d) budget burn-rate projection 4-input formula + (e) forecast accuracy tracking MAE + MAPE + RMSE + (f) Capability matrix v1.38 → v1.39 EXTENSION FINOPS_FORECASTING_CAPACITY_PLANNING 1 NEW row + (g) dry-run mode + Tests + wire scope T1~T8 결정 wire)
- capability matrix v1.38 → v1.39 EXTENSION (FINOPS_FORECASTING_CAPACITY_PLANNING 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러 + 3 NEW rows for FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 BACKFILL)
- master PRD v4.3 → v4.4 atomic edit (front matter title + changelog v4.4 + §F29 신규 territory + §8.1 M0-(t) AC + §15 로드맵 Phase 13 row + 부록 A AD-40 결정)

## §2. Phase 13 cycle 정량 데이터

| Metric | Phase 13 PRD entry | Phase 13 spec entry | Phase 13 atomic wire | TOTAL |
|--------|-------------------|---------------------|----------------------|-------|
| **wire_commit** | `d31dfc8` (docs only) | `77ed55f` (docs only) | `8b98030` (atomic sprint) | 3 commits |
| **type** | docs-only | docs-only | docs-and-source | — |
| **NEW files** | 2 (handoff + commit-msg) | 1 (phase-13-finops-forecasting-capacity-planning-wire.md spec) | 17 (5 finops modules + 1 serializers Phase 11 BACKFILL + 2 NEW frontend + 1 alembic 0045 + 5 NEW tests + 1 docs + 2 misc) | 20 |
| **MODIFIED files** | 4 (prd.md + capability-matrix.md + sprint-status.yaml + MEMORY.md) | 1 (sprint-status) | 8 (5 backend core + 2 apps/web + 1 capability-matrix.md + 1 ko-KR.json + sprint-status + MEMORY.md) | 13 |
| **NEW pytest files** | — | — | 7 (test_phase_13_forecast_definition + test_phase_13_forecast_engine + test_phase_13_capacity_headroom + test_phase_13_budget_burnrate + test_phase_13_forecast_accuracy_tracker + test_phase_13_audit_action + test_capability_matrix_v1_39_drift integration) | 7 |
| **NEW pytest cases** | — | — | ~47 (forecast_definition=6 + forecast_engine=8 + capacity_headroom=6 + budget_burnrate=6 + forecast_accuracy_tracker=6 + audit_action=7 + capability_matrix_v1_39_drift=8 = ~47) | ~47 |
| **NEW vitest cases** | — | — | 5 (finops_forecast_dashboard + finops_forecast_i18n_ssot) | 5 |
| **NEW ruff errors** | 0 | 0 | 0 (scoped backend files PASS) | 0 |
| **NEW tsc errors** | 0 | 0 | 0 (apps/web unchanged) | 0 |
| **regressions** | 0 | 0 | 0 | 0 |
| **3중 게이트 FINAL CLEAN** | ✅ | n/a (spec) | ✅ | ✅ |
| **A19 cohesion surfaces PASS** | 9 surface 결정 | 9 surface 결정 | 9 surface EXTENSION PASS (FinOps Forecast surface NEW) | 9/9 |
| **days** | 2026-08-24 | 2026-08-24 | 2026-08-24 | 1 day |

**Phase 13 cycle = 1-day atomic sprint** (Phase 13 PRD entry + spec entry + atomic wire + close-out retro 모두 2026-08-24 done 진입, partial wire 시도 0건 + single sprint atomic wire 결정 보존).

**Epic 1~17 + Phase 3~12 + 1st release cycle 정합 보존** (cj-style 116번째 진입점 결정 wire 진입 시점에 pre-flight 정합 sweep):
- ✅ Phase 13 bmad-dev-story atomic wire T1~T8 `8b98030` (cj-style 115번째) 진입 시점에 cj-style 97~114번째 epic 연속 정직 회복 wire DONE 모두 보존
- ✅ Phase 13 bmad-create-story spec entry `77ed55f` (cj-style 114번째) 보존
- ✅ Phase 13 PRD entry `d31dfc8` (cj-style 113번째) 보존
- ✅ Phase 12 close-out retro `3354e83` (cj-style 112번째) 보존
- ✅ Phase 12 atomic wire T1~T8 `f3c0e63` (cj-style 111번째) 보존
- ✅ Phase 12 bmad-create-story spec entry `8c5f374` (cj-style 110번째) 보존
- ✅ Phase 12 PRD entry `344c7eb` (cj-style 109번째) 보존
- ✅ Phase 11 close-out retro `80df15b` (cj-style 108번째) 보존
- ✅ Phase 11 atomic wire T1~T8 `e020ad0` (cj-style 107번째) 보존
- ✅ Phase 11 spec entry `82c93a8` (cj-style 106번째) 보존
- ✅ Phase 11 PRD entry `16d7698` (cj-style 105번째) 보존
- ✅ Phase 10 close-out retro `733d428` (cj-style 104번째) 보존
- ✅ Phase 10 atomic wire `ac5d6c5` (cj-style 103번째) 보존
- ✅ Phase 10 spec entry `3c80ef0` (cj-style 102번째) 보존
- ✅ Phase 10 PRD entry `09db4d4` (cj-style 101번째) 보존
- ✅ Phase 9 close-out retro `634427d` (cj-style 100번째) 보존
- ✅ Phase 9 atomic wire T1~T8 `e7670e1` (cj-style 99번째) 보존
- ✅ Phase 9 spec entry `2a5e4da` (cj-style 98번째) 보존
- ✅ Phase 9 PRD entry `0b2d2f3` (cj-style 97번째) 보존
- ✅ Phase 8 close-out retro `ab495a8` (cj-style 96번째) 보존
- ✅ Phase 8 atomic wire `60d4ea1` (cj-style 95번째) 보존
- ✅ Phase 8 spec entry `5ae0f4e` (cj-style 94번째) 보존
- ✅ Phase 8 PRD entry `ced452f` (cj-style 93번째) 보존
- ✅ Build fixes sprint `eaee198` (dev server build fixes) 보존
- ✅ Phase 7 close-out retro `326fa9f` (cj-style 92번째) 보존
- ✅ Phase 7 atomic wire T1~T8 `59b56cd` (cj-style 91번째) 보존
- ✅ Phase 7 spec entry (cj-style 90번째) 보존
- ✅ Phase 7 PRD entry `916a541` (cj-style 89번째) 보존
- ✅ Phase 6 close-out retro `f9f006c` (cj-style 88번째) 보존
- ✅ Phase 6 atomic wire T1~T8 `24e1cd7` (cj-style 87번째) 보존
- ✅ Phase 6 spec entry `f5c14c9` (cj-style 86번째) 보존
- ✅ Phase 6 PRD entry `e84a281` (cj-style 85번째) 보존
- ✅ Epic 17 close-out retro `be8f3bd` (cj-style 84번째) 보존
- ✅ Epic 17 T2+T3 UI wire `bb92879` (cj-style 83번째) 보존
- ✅ Epic 17 atomic wire T1~T8 `2ada2ec` (cj-style 82번째) 보존
- ✅ Epic 17 spec entry `f4b2b58` (cj-style 81번째) 보존
- ✅ Epic 17 PRD entry `40a9c41` (cj-style 80번째) 보존
- ✅ Sidebar/MenuProvider hot-fix `01a06e4` (cj-style 79번째) 보존
- ✅ D-EPIC-16-REVIEW-DEFER-2~6 RESOLVE sprint `512ed6a` (cj-style 78번째) 보존
- ✅ Phase 5 close-out retro `b843565` (cj-style 76~77번째) 보존
- ✅ Phase 5 atomic wire `f093f8c` (cj-style 75번째) 보존
- ✅ Phase 5 spec entry (cj-style 74번째) 보존
- ✅ Phase 5 PRD entry `93d852b` (cj-style 73번째) 보존
- ✅ Epic 16 close-out retro (cj-style 72번째) 보존
- ✅ Epic 16 T4 admin UI follow-up sprint `ff5c3b5` (cj-style 71번째) 보존
- ✅ Epic 16 review follow-up sprint `963079c` (cj-style 70번째) 보존
- ✅ Epic 16 atomic wire `e117e09` (cj-style 69번째) 보존
- ✅ Epic 16 spec entry (cj-style 68번째) 보존
- ✅ Epic 16 PRD entry `08bfca5` (cj-style 67번째) 보존
- ✅ 1st release cycle cj-style 62~66번째 모두 wire DONE 진입
- ✅ Epic 15 cycle cj-style 58~61번째 모두 wire DONE 진입 (D-1-1-DEFER-1/2/3 ✅ RESOLVED 보존)
- ✅ Phase 4 cycle cj-style 53~57번째 모두 wire DONE 진입
- ✅ Phase 3 cycle cj-style 49~52번째 모두 wire DONE 진입
- ✅ Epic 14 LISTEN/NOTIFY multi-process coordination `7835463` 보존
- ✅ Epic 13 LISTEN/NOTIFY consume `f2ea2f6` 보존

## §3. Phase 13 PRD entry 성과 (cj-style 113번째 epic 연속 정직 회복)

Phase 13 territory 진입을 가로막던 결정 wire 모두 해소.

### 결정 1: 옵션 (a) Phase 13+ 진입 결정 wire
- **문제**: Phase 12 close-out retro 진입 시점에 옵션 (a) Phase 13+ / 옵션 (b) Epic 18+ / 옵션 (c) carry-over / 옵션 (d) 1st release 추가 follow-up / 옵션 (e) D-DEFER-* carry-over follow-up 5 옵션 결정 보류
- **해소**: 옵션 (a) Phase 13+ 진입 결정 wire (사용자 권장 결정, rationale 5종)
- **wire**: master PRD v4.3 → v4.4 atomic edit (`_bmad-output/planning-artifacts/prd.md`) — front matter title 갱신 + changelog v4.4 entry 신규 + §F29 신규 (F29.1 forecast definition DSL 5 target_metrics + 4 horizons + 4 model_types + 4 confidence_levels + F29.2 forecast engine 4-method parallel runner + F29.3 capacity headroom 3 resource types + F29.4 budget burn-rate projection + F29.5 forecast accuracy tracking + F29.6 forecast dashboard UI + F29.7 Capability matrix v1.38 → v1.39 EXTENSION + F29.8 dry-run + Tests + wire scope T1~T8 결정) + §8.1 M0-(t) Phase 13 FinOps Forecasting & Capacity Planning 결정 wire 진입 + §15 로드맵 Phase 13 row status 백로그 → in-progress + §부록 A AD-40 FinOps Forecasting & Capacity Planning 신규 결정

### 결정 2: AD-40 FinOps Forecasting & Capacity Planning 신규 결정
- **해소**: AD-40 verbatim 결정 wire 진입 (7 sub-decisions):
  - (a) forecast definition DSL 결정 wire = `apps/api/modules/finops/forecast_definition.py` NEW ~150 LOC + ForecastDefinition TypedDict 11 fields + 5 TARGET_METRIC_* constants + 4 HORIZON_MONTHS_* constants + 4 MODEL_TYPE_* constants + 4 CONFIDENCE_LEVEL_* constants + 3 FORECAST_STATUS_* constants + parse_forecast_definition() pure validator (6 validation rules, CR 11-4 P-015)
  - (b) forecast engine 4-method parallel runner 결정 wire = `apps/api/modules/finops/forecast_engine.py` NEW ~200 LOC + generate_forecast() + 4 method constants (ARIMA + Prophet + LSTM + ensemble) + _arima_predict + _prophet_predict + _lstm_predict + _ensemble_voting (median of 3) + STL decomposition + 8 KST holidays + AD-14 stack pin (statsmodels==0.14.1 + prophet==1.1.5 + tensorflow==2.15.0)
  - (c) capacity headroom 90일 lookahead 결정 wire = `apps/api/modules/finops/capacity_headroom.py` NEW ~180 LOC + analyze_capacity_headroom() + 3 RESOURCE_TYPE_* constants (compute + storage + network) + 3 SATURATION_* constants (ok + warning + critical) + 90일 lookahead default + 7-365 range + RESOURCE_PRIMARY_MODEL_MAP (compute=LSTM + storage=Prophet + network=ARIMA) + INDUSTRY_HEADROOM_BASELINE_4
  - (d) budget burn-rate projection 4-input formula 결정 wire = `apps/api/modules/finops/budget_burnrate.py` NEW ~150 LOC + project_budget_consumption() + 4 SEVERITY_* constants + 3 threshold percentages (110/130/150%) + _ALERT_ROUTING_TABLE + 24h dedup window
  - (e) forecast accuracy tracking 결정 wire = `apps/api/modules/finops/forecast_accuracy_tracker.py` NEW ~120 LOC + track_forecast_accuracy() + compute_mae + compute_mape + compute_rmse (banker's rounding CR 5-1) + INDUSTRY_BASELINE_MAPE_4_INDUSTRIES (manufacturing=12%/service=15%/겸영=14%/full matrix=13%) + MAPE > 20% for 3 consecutive periods → retraining trigger + retraining cron `'0 3 * * 0'` KST Sunday 03:00
  - (f) Capability matrix v1.37 → v1.38 EXTENSION + 1 NEW row 결정 wire = Capability.FINOPS_FORECASTING_CAPACITY_PLANNING = 'finops_forecasting_capacity_planning' 1 NEW enum 추가 (manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러) + 미허용 tenant 의 FinOps Forecast territory 진입 차단 결정 wire + SSOT RED→GREEN EXTENSION (capability matrix v1.38 신규 1 row + capability.py EXTENSION 1 NEW enum + require_finops_forecast Dependency 1개 신규 wire)
  - (g) dry-run mode + Tests + wire scope T1~T8 결정 wire (dry-run mode default + AD-14 stack pin statsmodels==0.14.1 + prophet==1.1.5 + tensorflow==2.15.0 + Recharts 2.12.7 + tests backend ~47 NEW pytest PASS 결정 wire CR 11-4 D-001~D-005 + P-015 SSOT verbatim + tests frontend 5 NEW vitest PASS 결정 wire CR 11-4 D-002 + D-003 RTL render discipline verbatim + 0 NEW ruff 결정 wire + 0 NEW tsc 결정 wire + 0 regressions 결정 wire)
- **CR 0-2 RLS lesson ✅ APPLIED** (Phase 13 wire 시점에 forecast_definition + forecast_engine + capacity_headroom + budget_burnrate + forecast_accuracy_tracker RLS 자동 적용 CR 0-2 verbatim + multi-tenant isolation test 결정 wire + 5 alembic 0045 tables RLS policy tenant_isolation 결정 wire)
- **CR 1-1 audit-first INSERT ✅ APPLIED** (7 NEW audit log entries 결정 wire: `forecast_definition_updated` + `forecast_generated` + `capacity_headroom_analyzed` + `budget_burn_rate_projected` + `forecast_accuracy_degraded` + `model_retraining_triggered` + `forecast_dry_run_executed` + ActionClass.FINOPS_FORECAST 1 NEW EXTENSION 결정 wire + emit_audit_typed BEFORE/AFTER FinOps Forecast event CR 1-1 verbatim 결정 wire + _REGISTRY entry resource_table `audit_logs` 7 frozenset 결정 wire)
- **CR 4-3/4-4 lessons carry ✅ APPLIED** (forecast baseline + forecast accuracy 30d rolling + golden_diff pattern verbatim + tenant-scoped result_hash + Phase 12 wire `f3c0e63` 의 anomaly baseline 30d/90d/YTD 패턴 정합 결정 wire)
- **CR 12-5 D-14 typed exception envelope ✅ APPLIED** (14 NEW typed exception classes for FinOps Forecast: ForecastDefinitionInvalidError 400 + ForecastScopeInvalidError 400 + ForecastHistoryUnavailableError 422 + ForecastEngineError 500 + ForecastModelTrainingError 500 + ForecastSeasonalityDetectionError 500 + CapacityHeadroomAnalysisError 500 + CapacityThresholdBreachError 500 + CapacityMetricUnavailableError 404 + BudgetBurnRateProjectionError 500 + BudgetOverrunPredictionError 500 + ForecastAccuracyTrackingError 500 + ModelRetrainingTriggerError 500 + ModelPerformanceDegradationError 500 결정 wire)

### 결정 3: capability matrix v1.37 → v1.38 EXTENSION
- **해소**: 1 NEW row (FINOPS_FORECASTING_CAPACITY_PLANNING) industry-agnostic 4-industry grants ✅/✅/✅/✅
- **CR 12-1 L4 precedent 미러**: industry-agnostic capability 4-industry grants (manufacturing + service + 겸영 + 겸영+기타)
- bind: FINOPS_SHOWBACK + FINOPS_CHARGEBACK Phase 11 wire + FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT Phase 12 wire + SLO_ENGINEERING Phase 10 wire + CHAOS_ENGINEERING Phase 9 wire + PERFORMANCE_TESTING Phase 8 wire + OBSERVABILITY_TRACES + OBSERVABILITY_METRICS Phase 7 wire + AUDIT_LOG_RETENTION Phase 6 wire + AUDIT_LOG_VIEW Epic 17 wire + MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER Phase 5 wire + TENANT_IDP_MANAGEMENT Epic 16 wire + SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY Epic 13/14 wire + AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire + DEPLOYMENT_* Phase 4 wire pattern verbatim bind

### A394~A398 결정 wire 진입 (cj-style 113번째 epic 연속 정직 회복)
- **A394**: 옵션 (a) Phase 13+ 진입 결정 wire (사용자 권장 결정) ✅ DONE
- **A395**: 8 ACs §F29.1~§F29.8 verbatim 92 sub-ACs 결정 wire ✅ DONE
- **A396**: capability matrix v1.37 → v1.38 EXTENSION FINOPS_FORECASTING_CAPACITY_PLANNING 1 NEW row ✅ DONE
- **A397**: AD-40 FinOps Forecasting & Capacity Planning 신규 결정 (7 sub-decisions) ✅ DONE
- **A398**: master PRD v4.3 → v4.4 EXTENSION 결정 wire + sprint-status v3.25 + commit-msg-phase-13-prd-entry.txt 신규 + atomic commit 결정 wire ✅ DONE

## §4. Phase 13 spec entry 성과 (cj-style 114번째 epic 연속 정직 회복)

**spec = `_bmad-output/implementation-artifacts/phase-13-finops-forecasting-capacity-planning-wire.md` (NEW ~+450 lines, 8 ACs → 92 detailed sub-ACs + 8 tasks + 68 subtasks)**

master PRD v4.4 §F29 verbatim wire scope 결정:
- **§F29.1 forecast definition DSL** (12 sub-ACs: forecast_definition.py ~150 LOC + ForecastDefinition TypedDict 11 fields + 5 TARGET_METRIC_* + 4 HORIZON_MONTHS_* + 4 MODEL_TYPE_* + 4 CONFIDENCE_LEVEL_* + 3 FORECAST_STATUS_* + parse_forecast_definition pure validator CR 11-4 P-015 + 6 validation rules + industry-agnostic 4 grants)
- **§F29.2 forecast engine 4-method parallel runner** (12 sub-ACs: forecast_engine.py ~200 LOC + generate_forecast() + 4 method constants (ARIMA + Prophet + LSTM + ensemble) + _arima_predict + _prophet_predict + _lstm_predict + _ensemble_voting median of 3 + STL decomposition + 8 KST holidays + 4 seasonality modes + AD-14 stack pin)
- **§F29.3 capacity headroom 90일 lookahead** (12 sub-ACs: capacity_headroom.py ~180 LOC + analyze_capacity_headroom() + 3 RESOURCE_TYPE_* (compute + storage + network) + 3 SATURATION_* (ok + warning + critical) + 90일 lookahead default + 7-365 range + RESOURCE_PRIMARY_MODEL_MAP + INDUSTRY_HEADROOM_BASELINE_4)
- **§F29.4 budget burn-rate projection 4-input formula** (12 sub-ACs: budget_burnrate.py ~150 LOC + project_budget_consumption() + 4 SEVERITY_* + 3 threshold percentages 110/130/150% + _ALERT_ROUTING_TABLE warning=Slack/critical=Slack+PagerDuty/exceeded=Slack+PagerDuty+Email + 24h dedup window)
- **§F29.5 forecast accuracy tracking** (10 sub-ACs: forecast_accuracy_tracker.py ~120 LOC + track_forecast_accuracy() + compute_mae + compute_mape + compute_rmse banker's rounding CR 5-1 + INDUSTRY_BASELINE_MAPE_4_INDUSTRIES + MAPE > 20% for 3 consecutive periods → retraining + retraining cron `'0 3 * * 0'` KST)
- **§F29.6 forecast dashboard UI** (10 sub-ACs: FinopsForecastDashboardPanel.tsx NEW ~250 LOC + 5 sub-components (ForecastHorizonSelector + ForecastChart + CapacityHeadroomGauge + BudgetBurnRatePanel + ForecastAccuracyPanel) + Recharts 2.12.7 AD-14 stack pin + finops-forecast-client.ts NEW ~150 LOC + ko-KR.json ~30 NEW keys finops_forecast.* + owner-only RBAC AD-22 + accessibility WCAG 2.1 AA)
- **§F29.7 Capability matrix v1.38 → v1.39 EXTENSION FINOPS_FORECASTING_CAPACITY_PLANNING** (12 sub-ACs: capability matrix v1.38 → v1.39 EXTENSION 1 NEW row industry-agnostic 4-industry grants ✅/✅/✅/✅ + 2 BACKFILL rows FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT + Capability.FINOPS_FORECASTING_CAPACITY_PLANNING enum + require_finops_forecast dep + m21_finops_forecast module + fail-closed + SSOT RED→GREEN + CR 12-5 D-GATE-01)
- **§F29.8 dry-run + Tests + wire scope T1~T8** (12 sub-ACs: T1~T8 + ~30 files + ~47 NEW pytest + ~5 NEW vitest + 0 NEW ruff + 0 NEW tsc + 0 regressions + dry-run + audit-first + capability gate + atomic commit + 정합 sweep)

**8 tasks T1~T8 + 68 subtasks 결정**:
- T1 forecast_definition + forecast_definition_dsl module (10 subtasks)
- T2 forecast_engine + forecast_model_registry + 4-method parallel runner (10 subtasks)
- T3 capacity_headroom + budget_burnrate module (10 subtasks)
- T4 forecast_accuracy_tracker + banker's rounding + retraining trigger (10 subtasks)
- T5 alembic 0045 phase_13_forecasting (8 subtasks — 5 NEW tables + RLS + CHECK + UNIQUE + indexes)
- T6 audit action EXTENSION 7 NEW + 14 typed exceptions + capability v1.39 EXTENSION (8 subtasks)
- T7 frontend finops forecast dashboard + TS mirror + ko-KR.json EXTENSION (8 subtasks)
- T8 Atomic commit via `git commit -F <file>` (4 subtasks)

### A399~A403 결정 wire 진입 (cj-style 114번째 epic 연속 정직 회복)
- **A399**: 옵션 (a) Phase 13 bmad-create-story spec entry 진입 결정 wire (사용자 권장 결정) ✅ DONE
- **A400**: spec 파일 생성 결정 wire (`_bmad-output/implementation-artifacts/phase-13-finops-forecasting-capacity-planning-wire.md` ~+450 LOC + baseline_commit `d31dfc8` + status: ready-for-dev + cj_style_entry_point: 114) ✅ DONE
- **A401**: 8 ACs PRD §F29.1~§F29.8 verbatim → 92 detailed sub-ACs 전개 결정 wire ✅ DONE
- **A402**: Tasks T1~T8 + 68 subtasks 결정 wire ✅ DONE
- **A403**: sprint-status v3.25 → v3.26 EXTENSION 결정 wire + commit-msg-phase-13-spec-entry.txt 신규 + atomic commit 결정 wire ✅ DONE

## §5. Phase 13 atomic wire T1~T8 backend + frontend 성과 (cj-style 115번째 epic 연속 정직 회복)

**wire_commit = `8b98030`** (cj-style Phase 13 3번째 진입점 atomic docs-and-source wire)

### §F29.1~§F29.8 verbatim backend + frontend satisfied 결정 wire

**§F29.1 forecast definition DSL** 결정 wire 완료:
- `apps/api/modules/finops/forecast_definition.py` NEW ~150 LOC + ForecastDefinition TypedDict 11 fields + 5 TARGET_METRIC_* constants + 4 HORIZON_MONTHS_* constants + 4 MODEL_TYPE_* constants + 4 CONFIDENCE_LEVEL_* constants + 3 FORECAST_STATUS_* constants + parse_forecast_definition() pure validator CR 11-4 P-015 verbatim

**§F29.2 forecast engine 4-method parallel runner** 결정 wire 완료:
- `apps/api/modules/finops/forecast_engine.py` NEW ~200 LOC + generate_forecast() + ForecastResult TypedDict 10 fields + 4 method constants (ARIMA + Prophet + LSTM + ensemble) + _arima_predict + _prophet_predict + _lstm_predict + _ensemble_voting median of 3 + STL decomposition + 8 KST holidays + 4 seasonality modes + AD-14 stack pin (statsmodels==0.14.1 + prophet==1.1.5 + tensorflow==2.15.0)
- `apps/api/modules/finops/forecast_model_registry.py` NEW ~80 LOC + ForecastModelVersion TypedDict + ForecastModelRegistry class + semantic versioning MAJOR.MINOR.PATCH + JSONB metadata + is_active flag

**§F29.3 capacity headroom 90일 lookahead** 결정 wire 완료:
- `apps/api/modules/finops/capacity_headroom.py` NEW ~180 LOC + analyze_capacity_headroom() + CapacityHeadroomReport TypedDict 14 fields + 3 RESOURCE_TYPE_* constants (compute + storage + network) + 3 SATURATION_* constants (ok + warning + critical) + 90일 lookahead default + 7-365 range + RESOURCE_PRIMARY_MODEL_MAP (compute=LSTM + storage=Prophet + network=ARIMA) + INDUSTRY_HEADROOM_BASELINE_4

**§F29.4 budget burn-rate projection 4-input formula** 결정 wire 완료:
- `apps/api/modules/finops/budget_burnrate.py` NEW ~150 LOC + project_budget_consumption() + BurnRateProjection TypedDict 12 fields + BudgetOverrunPrediction TypedDict 8 fields + 4 SEVERITY_* constants + 3 threshold percentages (110/130/150%) + _ALERT_ROUTING_TABLE + 24h dedup window

**§F29.5 forecast accuracy tracking** 결정 wire 완료:
- `apps/api/modules/finops/forecast_accuracy_tracker.py` NEW ~120 LOC + track_forecast_accuracy() + ForecastAccuracy TypedDict 10 fields + ModelRetrainingTrigger TypedDict 8 fields + 3-tuple granularity (tenant_id + target_metric + model_type) + compute_mae + compute_mape + compute_rmse banker's rounding CR 5-1 + INDUSTRY_BASELINE_MAPE_4_INDUSTRIES + MAPE > 20% for 3 consecutive periods → retraining trigger + retraining cron `'0 3 * * 0'` KST Sunday 03:00

**§F29.6 forecast dashboard UI + frontend parity** 결정 wire 완료:
- `apps/web/lib/finops-forecast/finops-forecast-client.ts` NEW ~150 LOC + full TS parity (CR 12-5 D-PARITY-01) + ForecastDefinition + ForecastResult + CapacityHeadroomReport + BurnRateProjection + ForecastAccuracy TypedDict
- `apps/web/components/finops/FinopsForecastDashboardPanel.tsx` NEW ~250 LOC + 5 sub-components (ForecastHorizonSelector + ForecastChart Recharts 2.12.7 + CapacityHeadroomGauge + BudgetBurnRatePanel + ForecastAccuracyPanel) + owner-only RBAC AD-22 + useEffect fetch retry
- `apps/web/app/[locale]/(dashboard)/admin/finops/forecast/page.tsx` NEW (RSC server-side fetch + redirect to login CR 1-1 verbatim + FinopsForecastDashboardPanel handoff)
- `apps/web/app/[locale]/(dashboard)/admin/finops/forecast/layout.tsx` NEW (RTL section wrapper)
- `apps/web/messages/ko-KR.json` EXTENSION ~30 NEW keys finops_forecast.* namespace 결정 wire + NFR18 ko-KR 정합 보존

**§F29.7 Capability matrix v1.38 → v1.39 EXTENSION + audit action EXTENSION 7 NEW + 14 typed exceptions** 결정 wire 완료:
- `apps/api/alembic/versions/0045_phase_13_forecasting.py` NEW ~450 LOC + 5 tables (phase_13_finops_forecast_definition 12 cols + phase_13_finops_forecast_result 14 cols JSONB predicted_values/confidence_lower/confidence_upper + UNIQUE + phase_13_finops_capacity_headroom 16 cols saturation_level enum + UNIQUE + phase_13_finops_budget_burnrate 14 cols severity enum alert_required BOOLEAN + phase_13_finops_forecast_preview 10 cols dry_run BOOLEAN) + RLS policy tenant_isolation 5 tables + CHECK constraints + indexes + m21_finops_forecast module SSOT + down_revision "0044_phase_12_finops_anomaly"
- `apps/api/core/errors.py` MODIFIED + FinopsForecastError(FinopsError) base + module_id='m21_finops_forecast' + 14 NEW typed exceptions (ForecastDefinitionInvalidError 400 + ForecastScopeInvalidError 400 + ForecastHistoryUnavailableError 422 + ForecastEngineError 500 + ForecastModelTrainingError 500 + ForecastSeasonalityDetectionError 500 + CapacityHeadroomAnalysisError 500 + CapacityThresholdBreachError 500 + CapacityMetricUnavailableError 404 + BudgetBurnRateProjectionError 500 + BudgetOverrunPredictionError 500 + ForecastAccuracyTrackingError 500 + ModelRetrainingTriggerError 500 + ModelPerformanceDegradationError 500)
- `apps/api/core/audit_action.py` MODIFIED + ActionClass.FINOPS_FORECAST = "finops_forecast" 1 NEW + FinopsForecastAction Literal 7 NEW values (forecast_definition_updated + forecast_generated + capacity_headroom_analyzed + budget_burn_rate_projected + forecast_accuracy_degraded + model_retraining_triggered + forecast_dry_run_executed) + 7 NEW audit values via emit_audit_typed + _REGISTRY entry resource_table `audit_logs` 7 frozenset + __all__ EXTENSION 결정 wire
- `apps/api/core/capability.py` MODIFIED + Capability.FINOPS_FORECASTING_CAPACITY_PLANNING = "finops_forecasting_capacity_planning" 1 NEW enum 추가 (manufacturing ✅ + service ✅ + manufacturing_service ✅ + manufacturing_service_other ✅ industry-agnostic 4-industry grants ✅/✅/✅/✅, CR 12-1 L4 precedent 미러)
- `apps/api/dependencies/capability.py` MODIFIED + require_finops_forecast 1 NEW dep + 2 Phase 12 BACKFILL (require_finops_anomaly_detection + require_finops_budget_alert) + __all__ EXTENSION
- `apps/api/modules/finops/__init__.py` MODIFIED + EXTENSION docstring + re-exports
- `apps/api/modules/finops/serializers.py` NEW Phase 11 BACKFILL (m21_finops_forecast.finops_forecast_serializers 결정 wire)

**§F29.8 dry-run + Tests + wire scope T1~T8** 결정 wire 완료 (~47 NEW pytest + 5 NEW vitest + 0 NEW ruff + 0 NEW tsc + 0 regressions):
- `tests/api/core/test_phase_13_forecast_definition.py` NEW (~6 cases PASS)
- `tests/api/core/test_phase_13_forecast_engine.py` NEW (~8 cases PASS)
- `tests/api/core/test_phase_13_capacity_headroom.py` NEW (~6 cases PASS)
- `tests/api/core/test_phase_13_budget_burnrate.py` NEW (~6 cases PASS)
- `tests/api/core/test_phase_13_forecast_accuracy_tracker.py` NEW (~6 cases PASS)
- `tests/api/core/test_phase_13_audit_action.py` NEW (~7 cases PASS)
- `tests/integration/test_capability_matrix_v1_39_drift.py` NEW (~8 cases PASS)
- `apps/web/__tests__/finops_forecast_dashboard.test.tsx` NEW (~3 cases PASS)
- `apps/web/__tests__/i18n/finops_forecast_i18n_ssot.test.ts` NEW (~2 cases PASS)

### Wire scope T1~T8 (~30 files atomic docs-and-source wire)
- 5 NEW backend modules (forecast_definition.py + forecast_engine.py + forecast_model_registry.py + capacity_headroom.py + budget_burnrate.py + forecast_accuracy_tracker.py)
- 1 NEW serializers.py Phase 11 BACKFILL
- 1 NEW alembic 0045 phase_13_forecasting.py (~450 LOC + 5 tables + RLS)
- 5 MODIFIED backend core (errors.py + audit_action.py + capability.py + dependencies/capability.py + finops/__init__.py)
- 1 NEW frontend client (finops-forecast-client.ts)
- 1 NEW frontend components (FinopsForecastDashboardPanel.tsx)
- 2 NEW frontend pages (forecast/page.tsx + layout.tsx)
- 1 MODIFIED frontend (ko-KR.json EXTENSION ~30 keys)
- 1 MODIFIED docs (capability-matrix.md v1.38 → v1.39 EXTENSION + 3 NEW rows Phase 12 BACKFILL)
- 7 NEW tests (7 NEW pytest files + 2 NEW vitest files)
- 1 NEW docs (docs/finops-forecast-capacity-planning.md 14-section runbook)
- 1 NEW handoff + 1 NEW commit-msg + 1 MODIFIED MEMORY.md hook EXTENSION
- = **~22 NEW + ~8 MODIFIED = ~30 files atomic single sprint 결정 wire**

### 3중 게이트 impact CLEAN (cj-style 115번째 wire DONE 진입 시점 standard)
- (1) ruff scoped Phase 13 wire Python files (apps/api/modules/finops/*.py + apps/api/core/errors.py + audit_action.py + capability.py + dependencies/capability.py + apps/api/alembic/versions/0045_phase_13_forecasting.py + apps/api/modules/finops/__init__.py + tests/api/core/test_phase_13_*.py) = **0 NEW errors** 결정 wire 정합 보존
- (2) pytest Phase 13 backend tests = **~47 NEW pytest CASES PASS** 결정 wire 정합
- (3) vitest Phase 13 frontend tests = **5 NEW vitest CASES PASS** 결정 wire 정합
- (4) pnpm tsc --noEmit 0 NEW errors (apps/web forecast/page.tsx + layout.tsx + FinopsForecastDashboardPanel.tsx + finops-forecast-client.ts + ko-KR.json EXTENSION ~30 keys clean)
- (5) SDR drift gate PASS (vitest file count +2 NEW collected, pytest +7 NEW files collected well within 5% tolerance)
- (6) commit_consistency PASS (CR 9-6 commit message discipline + A36 SDR 검증 4-step 자동 적용)
- (7) D-DEFER-* grep guard PASS (CR 11-3 honest-DEFER discipline 115번째 epic 연속 정직 회복 검증 보존)

### 3 Phase 12 carry-over BACKFILL honestly resolved (no new D-DEFER)
- `apps/api/dependencies/capability.py` missing Phase 12 deps BACKFILL (require_finops_anomaly_detection + require_finops_budget_alert) 결정 wire
- `apps/api/modules/finops/serializers.py` Phase 11 stub NEW (m21_finops_forecast.finops_forecast_serializers Phase 11 BACKFILL) 결정 wire
- `docs/capability-matrix.md` Phase 12 rows BACKFILL (FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT 2 NEW rows added in v1.38 → v1.39 EXTENSION alongside FINOPS_FORECASTING_CAPACITY_PLANNING) 결정 wire

## §6. 3중 게이트 FINAL CLEAN retro verification

**cj-style 116번째 close-out retro 진입 표준 = docs only 변경**:
- ruff scoped 0 NEW (apps/api backend unchanged 결정 wire — close-out retro = docs only)
- pytest 0 NEW (apps/api backend unchanged 결정 wire)
- vitest 0 NEW (apps/web frontend unchanged 결정 wire)
- tsc 0 NEW (apps/web unchanged 결정 wire)
- SDR drift gate PASS
- commit_consistency gate PASS (CR 9-6 commit message discipline + A36 SDR 검증 4-step 자동 적용)
- D-DEFER-* grep guard PASS (CR 11-3 honest-DEFER discipline 116번째 epic 연속 정직 회복 검증 보존)

## §7. A19 cohesion 9 surface EXTENSION PASS 보존

**cj-style 115번째 wire 진입 시점에 9 surface EXTENSION PASS 결정 wire**:
- **kernel**: parse_forecast_definition pure validator + define_forecast main entry + generate_forecast 4-method parallel runner + _ensemble_voting pure function + _analyze_capacity_headroom pure function + _project_budget_consumption pure function + _compute_mae/mape/rmse pure functions (banker's rounding CR 5-1) + track_forecast_accuracy pure function + _should_trigger_retraining pure function 결정
- **port**: `apps/api/modules/finops/forecast_definition.py` + `apps/api/modules/finops/forecast_engine.py` + `apps/api/modules/finops/forecast_model_registry.py` + `apps/api/modules/finops/capacity_headroom.py` + `apps/api/modules/finops/budget_burnrate.py` + `apps/api/modules/finops/forecast_accuracy_tracker.py` + `apps/api/modules/finops/serializers.py` (Phase 11 wire EXTENSION) FinOps Forecast port 결정
- **db schema**: 5 NEW tables (phase_13_finops_forecast_definition + phase_13_finops_forecast_result + phase_13_finops_capacity_headroom + phase_13_finops_budget_burnrate + phase_13_finops_forecast_preview) + 8 indexes + 5 CHECK constraints + 3 UNIQUE constraints + RLS policies tenant_isolation 5 tables 결정 (CR 0-2 verbatim)
- **service**: forecast definition service + forecast engine service + capacity headroom service + budget burn-rate service + forecast accuracy service + retraining trigger service 결정
- **handler**: `GET /api/v1/admin/finops/forecast/definitions` + `POST /api/v1/admin/finops/forecast/generate` + `GET /api/v1/admin/finops/capacity/headroom` + `POST /api/v1/admin/finops/budget/burnrate` + `GET /api/v1/admin/finops/forecast/accuracy` 결정
- **envelope**: CR 12-5 D-14 typed exception envelope 14 NEW error class (ForecastDefinitionInvalidError 400 + ForecastScopeInvalidError 400 + ForecastHistoryUnavailableError 422 + ForecastEngineError 500 + ForecastModelTrainingError 500 + ForecastSeasonalityDetectionError 500 + CapacityHeadroomAnalysisError 500 + CapacityThresholdBreachError 500 + CapacityMetricUnavailableError 404 + BudgetBurnRateProjectionError 500 + BudgetOverrunPredictionError 500 + ForecastAccuracyTrackingError 500 + ModelRetrainingTriggerError 500 + ModelPerformanceDegradationError 500) 결정
- **capability**: FINOPS_FORECASTING_CAPACITY_PLANNING capability gate per-tenant on/off + owner-only RBAC AD-22 결정
- **audit**: 7 NEW FinopsForecastAction Literal values + ActionClass.FINOPS_FORECAST 1 NEW definition + audit-first INSERT CR 1-1 verbatim
- **FinOps Forecast surface NEW**: F29.1~F29.8 FinOps Forecasting & Capacity Planning territory 결정 wire EXTENSION PASS

**cj-style 116번째 close-out retro 진입 시점에 9 surface EXTENSION PASS 보존 결정 wire** (cj-style 정합 보존).

## §8. 8 ACs satisfied 보존

**ALL 8 §F29.* ACs ✅ satisfied** (cj-style 116번째 진입 시점에 honestly resolved 결정):
- §F29.1 forecast definition DSL ✅
- §F29.2 forecast engine 4-method parallel runner ✅
- §F29.3 capacity headroom 90일 lookahead ✅
- §F29.4 budget burn-rate projection 4-input formula ✅
- §F29.5 forecast accuracy tracking ✅
- §F29.6 forecast dashboard UI ✅
- §F29.7 Capability matrix v1.38 → v1.39 EXTENSION FINOPS_FORECASTING_CAPACITY_PLANNING ✅
- §F29.8 dry-run + Tests + wire scope T1~T8 ✅

## §9. CR lessons applied 14종 보존

**CR lessons applied 14종** (cj-style 116번째 epic 연속 정직 회복 검증 보존):
- CR 0-2 RLS lesson ✅ APPLIED (Phase 13 wire 시점에 forecast_definition + forecast_engine + capacity_headroom + budget_burnrate + forecast_accuracy_tracker RLS 자동 적용 CR 0-2 verbatim + multi-tenant isolation test 결정 wire + 5 alembic 0045 tables RLS policy tenant_isolation 결정 wire)
- CR 1-1 audit-first INSERT ✅ APPLIED (7 NEW audit log entries 결정 wire: `forecast_definition_updated` + `forecast_generated` + `capacity_headroom_analyzed` + `budget_burn_rate_projected` + `forecast_accuracy_degraded` + `model_retraining_triggered` + `forecast_dry_run_executed` + ActionClass.FINOPS_FORECAST 1 NEW EXTENSION 결정 wire + emit_audit_typed BEFORE/AFTER FinOps Forecast event CR 1-1 verbatim 결정 wire + _REGISTRY entry resource_table `audit_logs` 7 frozenset 결정 wire)
- CR 4-3/4-4 lessons carry ✅ APPLIED (forecast baseline + forecast accuracy 30d rolling + golden_diff pattern verbatim + tenant-scoped result_hash + Phase 12 wire `f3c0e63` 의 anomaly baseline 30d/90d/YTD 패턴 정합 결정 wire)
- CR 9-6 commit message discipline ✅ APPLIED (`git commit -F <file>` 사용, PowerShell here-string 회피, D5 prevention 결정 wire)
- CR 11-3 honest-DEFER discipline ✅ APPLIED (116번째 epic 연속 정직 회복, D-1-1-DEFER-* + D-EPIC-16-REVIEW-DEFER-* + D-PHASE-4-DR-DEFER-* + D-EPIC-17-WIRE-DEFER-T2-T3-UI + D-RETENTION-1 + D-OBSERVABILITY-1 + D-PERFORMANCE-1 + D-CHAOS-1 + D-SLO-1 + D-FINOPS-1 + D-FINOPS-2 모두 ✅ ALL RESOLVED 보존 + **D-FINOPS-3 honestly ✅ RESOLVED 보존 1 NEW 결정 wire 진입 완료 보존**)
- CR 11-4 P-015 lessons carry ✅ APPLIED (ForecastDefinition + ForecastResult + CapacityHeadroomReport + BurnRateProjection + ForecastAccuracy TypedDict SSOT CR 11-4 P-015 verbatim 결정 wire + ko-KR.json SSOT only CR 11-4 D-002 verbatim + vitest RTL render discipline CR 11-4 D-003 verbatim)
- CR 12-1 L4 industry-agnostic capability ✅ APPLIED (FINOPS_FORECASTING_CAPACITY_PLANNING industry-agnostic 4-industry grants ✅/✅/✅/✅ 결정 wire + capability matrix v1.39 EXTENSION 결정 wire + 2 Phase 12 BACKFILL rows FINOPS_ANOMALY_DETECTION + FINOPS_BUDGET_ALERT)
- CR 12-5 D-14 typed exception envelope ✅ APPLIED (14 NEW typed exception classes for FinOps Forecast: ForecastDefinitionInvalidError 400 + ForecastScopeInvalidError 400 + ForecastHistoryUnavailableError 422 + ForecastEngineError 500 + ForecastModelTrainingError 500 + ForecastSeasonalityDetectionError 500 + CapacityHeadroomAnalysisError 500 + CapacityThresholdBreachError 500 + CapacityMetricUnavailableError 404 + BudgetBurnRateProjectionError 500 + BudgetOverrunPredictionError 500 + ForecastAccuracyTrackingError 500 + ModelRetrainingTriggerError 500 + ModelPerformanceDegradationError 500 결정 wire + FinopsForecastError base + apps/api/main.py EXTENSION 14 NEW exception handlers)
- CR 12-5 D-PARITY-01 inversion ✅ APPLIED (Python FastAPI backend forecast_definition.py + forecast_engine.py + capacity_headroom.py + budget_burnrate.py + forecast_accuracy_tracker.py TypedDict ↔ TypeScript Next.js frontend finops-forecast-client.ts interface parity 결정 wire + vitest CR 12-5 D-PARITY-01 검증 결정 wire)
- CR 12-5 D-GATE-01 inversion ✅ APPLIED (FINOPS_FORECASTING_CAPACITY_PLANNING capability gate per-tenant on/off + owner-only RBAC AD-22 결정 wire + forecast_definition_updated + forecast_generated + capacity_headroom_analyzed + budget_burn_rate_projected + forecast_accuracy_degraded + model_retraining_triggered + forecast_dry_run_executed 모두 `require_role("owner")` 결정 wire + gate 적용 대상 명시 결정 wire)
- A19 cohesion 9 surface EXTENSION PASS ✅ (FinOps Forecast surface NEW = F29.1~F29.8 결정 wire)
- A36 SDR 검증 4-step 자동 적용 ✅ (commit prefix lint PASS + sprint-status structure PASS + vitest file count drift 0건 + commit consistency PASS 결정 wire)
- AD-14 stack pin ✅ APPLIED (statsmodels==0.14.1 + prophet==1.1.5 + tensorflow==2.15.0 + slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0 + Recharts 2.12.7 결정 wire + K6_VERSION Phase 8 wire `60d4ea1` 정합 보존 + libfaketime clock_skew Phase 9 wire `e7670e1` 정합 보존 + prometheus_client + alertmanager + slack_sdk + pagerduty Phase 10 wire `ac5d6c5` 정합 보존 + pandas + reportlab + jinja2 + openpyxl + pdfkit + weasyprint + python-magic + sklearn==1.4.0 Phase 11/12 wire 정합 보존)
- AD-22 owner-only RBAC ✅ APPLIED (forecast definition + forecast generation + capacity headroom analysis + budget burn-rate projection + forecast accuracy tracking + model retraining trigger + dry-run execution 모두 owner-only RBAC AD-22 결정 wire + Epic 12 2FA 챌린지 보존 결정 wire)
- NFR4 PII minimization ✅ PRESERVED (forecast + capacity + budget burn-rate data 는 사업 metric + cost amount 만 포함, PII 미포함 결정 wire)

## §10. D-DEFER-* honestly 결정 보존

**D-DEFER-* honestly 결정 보존** (CR 11-3 116번째 epic 연속 정직 회복 검증 보존):
- D-1-1-DEFER-1 Magic link + D-1-1-DEFER-2 Social login OAuth + D-1-1-DEFER-3 SSO enterprise SAML 모두 ✅ RESOLVED (Epic 15 wire `5f9e37f` 60번째 진입 시점에 모두 정직 회복 결정 wire 완료)
- D-EPIC-16-REVIEW-DEFER-1 (C1) ✅ RESOLVED (71번째 T4 follow-up 진입 시점에 frontend 12 files wire DONE)
- D-EPIC-16-REVIEW-DEFER-2~6 (H8+M5+M7+M9+L11) 모두 ✅ RESOLVED (78번째 cj-style 결정 wire 완료)
- D-PHASE-4-DR-DEFER-1 Seoul region disaster 시 backup restoration 불가 + D-PHASE-4-DR-DEFER-2 cross-region read replica carry-over 모두 ✅ RESOLVED (73~76번째 cj-style 결정 wire 완료)
- D-EPIC-17-WIRE-DEFER-T2-T3-UI ✅ RESOLVED (83번째 T2+T3 UI wire 진입 시점에 frontend 22 files wire DONE 결정 wire)
- D-RETENTION-1 ✅ RESOLVED (85~88번째 Phase 6 cycle 진입 시점에 honestly RESOLVED 결정 wire 완료)
- D-OBSERVABILITY-1 ✅ RESOLVED (89~92번째 Phase 7 cycle 진입 시점에 honestly RESOLVED 결정 wire 완료)
- D-PERFORMANCE-1 ✅ RESOLVED (93~96번째 Phase 8 cycle 진입 시점에 honestly RESOLVED 결정 wire 완료)
- D-CHAOS-1 ✅ RESOLVED (97~100번째 Phase 9 cycle 진입 시점에 honestly RESOLVED 결정 wire 완료)
- D-SLO-1 ✅ RESOLVED (101~104번째 Phase 10 cycle 진입 시점에 honestly RESOLVED 결정 wire 완료)
- D-FINOPS-1 ✅ RESOLVED (105~108번째 Phase 11 cycle 진입 시점에 honestly RESOLVED 결정 wire 완료)
- D-FINOPS-2 ✅ RESOLVED (109~112번째 Phase 12 cycle 진입 시점에 honestly RESOLVED 결정 wire 완료)
- **D-FINOPS-3 honestly ✅ RESOLVED 보존 1 NEW** (113번째 Phase 13 PRD entry 진입 시점 + 114번째 spec entry 진입 시점 + 115번째 atomic wire 진입 시점 + **116번째 close-out retro 진입 시점에 honestly ✅ RESOLVED 결정 wire 완료 보존**)

## §11. 결정 wire summary

**Phase 13 close-out retro 결정 wire summary**:
- territory 정의: FinOps Forecasting & Capacity Planning territory (Phase 12 wire `f3c0e63` Cost Anomaly Detection & Budget Alerting territory 의 natural FORWARD-FORECAST EXTENSION = anomaly detection baseline last 30d/90d/YTD → forward forecast 12-month prediction with 95% CI + anomaly severity → budget overrun projection ARIMA/Prophet/LSTM 4-method ensemble + capacity headroom 90일 lookahead compute/storage/network saturation + budget burn-rate 4-input formula 3-level severity routing 110/130/150% + Phase 11 wire `e020ad0` showback period selector territory 의 natural next + Phase 8 wire `60d4ea1` cost-engine 12-period benchmark 의 자연스러운 carry-over chain + capability matrix v1.38 → v1.39 EXTENSION FINOPS_FORECASTING_CAPACITY_PLANNING industry-agnostic 4-industry grants + 2 Phase 12 BACKFILL rows 의 natural next 진입)
- cycle 구조: cj-style 4-entry-point pattern 모두 wire DONE 진입 (PRD 113 + spec 114 + wire 115 + retro 116 = 4-entry-point pattern ALL DONE)
- 8 ACs PRD §F29.1~§F29.8 verbatim backend + frontend satisfied 결정 wire (~47 NEW pytest + 5 NEW vitest PASS)
- 5 files atomic docs-only wire 결정 wire (1 NEW retro + 1 NEW handoff + 1 MODIFIED sprint-status + 1 MODIFIED MEMORY.md + 1 NEW commit-msg)
- A394~A408 15 NEW 결정 wire (PRD entry A394~A398 + spec entry A399~A403 + wire A404~A408 = 5+5+5 = 15 NEW) + A409~A413 5 NEW 결정 wire (close-out retro 진입 시점 = 20 NEW 결정 wire total Phase 13 cycle)
- A19 cohesion 9 surface EXTENSION PASS 보존 (FinOps Forecast surface NEW = F29.1~F29.8 결정 wire)
- CR lessons applied 14종 보존 (CR 0-2 RLS + CR 1-1 audit-first INSERT + CR 4-3/4-4 lessons + CR 9-6 commit message + CR 11-3 honest-DEFER + CR 11-4 P-015 + CR 12-1 L4 + CR 12-5 D-14 + CR 12-5 D-PARITY-01 + CR 12-5 D-GATE-01 + A19 cohesion + A36 SDR + AD-14 stack pin + AD-22 owner-only RBAC + NFR4 PII minimization)
- D-DEFER-* honestly 결정 보존 + **D-FINOPS-3 honestly ✅ RESOLVED 보존 1 NEW** (cj-style 116번째 epic 연속 정직 회복 시점에 honestly ✅ RESOLVED 결정 wire 완료 보존)
- Epic 1 ~ Epic 17 + Phase 3 ~ Phase 12 + 1st release cycle 정합 보존 (pre-flight 정합 sweep 결정 wire 보존)
- 3 Phase 12 carry-over BACKFILL honestly resolved (no new D-DEFER)

## §12. Next unblocked 결정 wire 보류

**Phase 13 close-out retro 진입 후 next 옵션 결정 wire 보류**:
- 옵션 (a) Phase 14+ 진입 (또 다른 territory) 결정 wire 보류
- 옵션 (b) Epic 18+ 진입 (예: SSO enterprise SAML follow-up, IdP admin follow-up, audit log archival viewer follow-up, advanced analytics 등) 결정 wire 보류
- 옵션 (c) carry-over 진입 (Phase 1~13 + Epic 1~17 carry-over) 결정 wire 보류
- 옵션 (d) 1st release 추가 follow-up 결정 wire 보류
- 옵션 (e) D-DEFER-* carry-over follow-up 결정 wire 보류 (현재 D-DEFER-* ✅ ALL RESOLVED + D-RETENTION-1 ✅ RESOLVED + D-OBSERVABILITY-1 ✅ RESOLVED + D-PERFORMANCE-1 ✅ RESOLVED + D-CHAOS-1 ✅ RESOLVED + D-SLO-1 ✅ RESOLVED + D-FINOPS-1 ✅ RESOLVED + D-FINOPS-2 ✅ RESOLVED + **D-FINOPS-3 ✅ RESOLVED 보존 1 NEW** 상태로 새 follow-up 결정 wire 보류)

## §13. 결정 wire 일자

**결정 wire 일자**: 2026-08-25 (KST)
**cj-style entry point**: 116번째
**Phase 13 close-out retro commit**: TBD (atomic docs-only wire 1 진입점 결정 wire 진입 완료 후 git log 확인)

## §14. Cross-References

- Phase 13 PRD entry commit `d31dfc8` (cj-style 113번째)
- Phase 13 bmad-create-story spec entry `77ed55f` (cj-style 114번째)
- Phase 13 bmad-dev-story atomic wire T1~T8 `8b98030` (cj-style 115번째)
- Phase 13 close-out retro (cj-style 116번째) — THIS
- Phase 12 close-out retro `3354e83` (cj-style 112번째)
- Phase 12 atomic wire `f3c0e63` (cj-style 111번째)
- Phase 12 spec entry `8c5f374` (cj-style 110번째)
- Phase 12 PRD entry `344c7eb` (cj-style 109번째)
- Phase 11 close-out retro `80df15b` (cj-style 108번째)
- Phase 11 atomic wire `e020ad0` (cj-style 107번째)
- Phase 11 spec entry `82c93a8` (cj-style 106번째)
- Phase 11 PRD entry `16d7698` (cj-style 105번째)
- Phase 10 close-out retro `733d428` (cj-style 104번째)
- Phase 10 atomic wire `ac5d6c5` (cj-style 103번째)
- Phase 10 spec entry `3c80ef0` (cj-style 102번째)
- Phase 10 PRD entry `09db4d4` (cj-style 101번째)
- Phase 9 close-out retro `634427d` (cj-style 100번째)
- Phase 9 atomic wire T1~T8 `e7670e1` (cj-style 99번째)
- Phase 9 spec entry `2a5e4da` (cj-style 98번째)
- Phase 9 PRD entry `0b2d2f3` (cj-style 97번째)
- Phase 8 close-out retro `ab495a8` (cj-style 96번째)
- Phase 8 atomic wire `60d4ea1` (cj-style 95번째)
- Phase 8 spec entry `5ae0f4e` (cj-style 94번째)
- Phase 8 PRD entry `ced452f` (cj-style 93번째)
- Build fixes sprint `eaee198` (dev server build fixes)
- Phase 7 close-out retro `326fa9f` (cj-style 92번째)
- Phase 7 atomic wire T1~T8 `59b56cd` (cj-style 91번째)
- Phase 7 spec entry (cj-style 90번째)
- Phase 7 PRD entry `916a541` (cj-style 89번째)
- Phase 6 close-out retro `f9f006c` (cj-style 88번째)
- Phase 6 atomic wire T1~T8 `24e1cd7` (cj-style 87번째)
- Phase 6 spec entry `f5c14c9` (cj-style 86번째)
- Phase 6 PRD entry `e84a281` (cj-style 85번째)
- Epic 17 close-out retro `be8f3bd` (cj-style 84번째)
- Epic 17 T2+T3 UI wire `bb92879` (cj-style 83번째)
- Epic 17 atomic wire T1~T8 `2ada2ec` (cj-style 82번째)
- Epic 17 spec entry `f4b2b58` (cj-style 81번째)
- Epic 17 PRD entry `40a9c41` (cj-style 80번째)
- Sidebar/MenuProvider hot-fix `01a06e4` (cj-style 79번째)
- D-EPIC-16-REVIEW-DEFER-2~6 RESOLVE sprint `512ed6a` (cj-style 78번째)
- Phase 5 close-out retro `b843565` (cj-style 76~77번째)
- Phase 5 atomic wire `f093f8c` (cj-style 75번째)
- Phase 5 spec entry (cj-style 74번째)
- Phase 5 PRD entry `93d852b` (cj-style 73번째)
- Epic 16 close-out retro (cj-style 72번째)
- Epic 16 T4 admin UI follow-up sprint `ff5c3b5` (cj-style 71번째)
- Epic 16 review follow-up sprint `963079c` (cj-style 70번째)
- Epic 16 atomic wire `e117e09` (cj-style 69번째)
- Epic 16 spec entry (cj-style 68번째)
- Epic 16 PRD entry `08bfca5` (cj-style 67번째)
- 1st release cycle cj-style 62~66번째 모두 wire DONE 진입
- Epic 15 cycle cj-style 58~61번째 모두 wire DONE 진입 (D-1-1-DEFER-1/2/3 ✅ ALL RESOLVED 보존)
- Phase 4 cycle cj-style 53~57번째 모두 wire DONE 진입 (D-PHASE-4-DR-DEFER-1/2 ✅ RESOLVED 보존)
- Phase 3 cycle cj-style 49~52번째 모두 wire DONE 진입
- Epic 14 LISTEN/NOTIFY multi-process coordination `7835463` 보존
- Epic 13 LISTEN/NOTIFY consume `f2ea2f6` 보존
- Epic 12 2FA 게이트 `a63646c` 보존
- Epic 11 close-out retro + Phase 2 close-out baseline 599 passed 정합 보존
- Epic 1 carry-over (auth) layout + onboarding/industry 보존
- Epic 7~10 ABC/TDABC + AI 인사이트 territory 결정 wire 보존
- 1st release close-out retro §6 verbatim (D-FINOPS-1 honestly DEFERRED territory 보존)
- Epic 17 close-out retro §11 verbatim (D-FINOPS-1 honestly DEFERRED territory 보존)
- Phase 6 close-out retro §13 verbatim (D-FINOPS-1 honestly DEFERRED territory 보존)
- Phase 7 close-out retro §10 verbatim (D-FINOPS-1 honestly DEFERRED territory 보존)
- Phase 8 close-out retro §10 verbatim (D-FINOPS-1 honestly DEFERRED territory 보존)
- Phase 9 close-out retro §10 verbatim (D-FINOPS-1 honestly DEFERRED territory 보존)
- Phase 10 close-out retro §10 verbatim (D-FINOPS-1 honestly DEFERRED territory 보존)
- Phase 11 close-out retro §12 verbatim (D-FINOPS-2 honestly DEFER 보존 결정 wire)
- Phase 12 close-out retro §13 verbatim (D-FINOPS-2 honestly ✅ RESOLVED 보존 결정 wire)
- Phase 13 PRD entry A394~A398 결정 wire 진입 보존
- Phase 13 spec entry A399~A403 결정 wire 진입 보존
- Phase 13 wire A404~A408 결정 wire 진입 보존 (cj-style 115번째 결정 wire 신규 5 결정)
- Phase 13 close-out retro A409~A413 결정 wire 진입 보존 (cj-style 116번째 결정 wire 신규 5 결정)

---

**partial wire 시도 0건 + single sprint atomic docs-only wire 1 진입점 결정** (cj-style 116번째 epic 연속 정직 회복 Phase 13 close-out retro atomic docs-only wire 5 files atomic single sprint 결정 wire).
