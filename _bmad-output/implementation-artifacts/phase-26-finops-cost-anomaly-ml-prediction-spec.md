---
baseline_commit: d9c358f
status: ready-for-dev
cj_style_entry_point: 180
story_key: phase-26-finops-cost-anomaly-ml-prediction-spec
---

# Phase 26 FinOps Cost Anomaly ML Prediction spec (cj-style 180번째 epic 연속 정직 회복)

## Story

**As a** FinOps practitioner / data scientist / tenant admin / 1st release customer / DevOps engineer
**I want** Phase 26 territory 결정 wire (FinOps Cost Anomaly ML Prediction = **anomaly_ml_prediction_engine + 5 model types ensemble (prophet 0.30 + lstm 0.30 + arima 0.15 + isolation_forest 0.15 + autoencoder 0.10) + 8 features (cost_total_krw + cost_per_unit + variance_pct + budget_consumption_pct + settlement_3way_match_score + optimization_savings_amount + month_seasonality + holiday_flag) + lifecycle (training → deploying → active → deprecated → retired) + model_registry versioning semver + A/B testing champion/challenger (traffic_split 50/50 + auto-promote criterion challenger_composite_score >= champion_composite_score + 0.05 for 7 consecutive days) + 4-dim model scoring (precision 0.30 + recall 0.30 + F1 0.25 + AUC-ROC 0.15) + 3 drift detection types (data + concept + prediction PSI 0.25) + training_pipeline scheduled retraining KST 매주 일요일 03:00 UTC 18:00 + drift-triggered retraining + SHAP feature importance + real-time inference < 200ms P95 + batch inference KST 02:00 UTC 17:00 + bootstrap sampling B=1000 + ensemble consensus threshold default 0.85 + AnomalyScoreComparison vs Phase 12 rule-based detection** + **anomaly_ml_prediction_dashboard 5 NEW sub-components (AnomalyMLPredictionOverviewCard + EnsembleConsensusScorePanel + MLvsThresholdComparisonChart + ModelDriftDetectionPanel + ABTestChampionChallengerPanel)** + **Capability matrix v1.52 EXTENSION FINOPS_COST_ANOMALY_ML_PREDICTION** + **audit action EXTENSION 12 NEW Literal + 16 NEW typed exception classes** + **dry-run mode + 1 NEW CLI flag + Tests + wire scope T1~T8**) 결정 wire
**so that** Phase 11~25 17-capability FinOps territory chain ✅ ALL WIRED INTEGRATED 진입 정합 보존 후 Phase 26 PRD entry `b95ebc3` (cj-style 179번째) 진입 직후 spec entry 진입 = cj-style 4-entry-point cycle PRD entry → spec entry → wire → close-out retro 의 2번째 단계 진입 결정 wire (Phase 17 spec entry cj-style 130번째 + Phase 18 spec entry cj-style 134번째 + Phase 19 spec entry cj-style 138번째 + Phase 20 spec entry cj-style 143번째 + Phase 21 spec entry cj-style 150번째 + Phase 22 spec entry cj-style 159번째 + Phase 23 spec entry cj-style 163번째 + Phase 24 spec entry cj-style 168번째 + Phase 25 spec entry cj-style 172번째 패턴 verbatim 미러) + Phase 26 territory = 4 NEW backend modules (anomaly_ml_prediction_engine + anomaly_ml_model_registry + anomaly_ml_training_pipeline + anomaly_ml_scoring) 의 **pre-anomaly-detection layer** = Phase 11 showback 12-period + Phase 12 anomaly training baseline (last 30d + last 90d + YTD) + Phase 13 forecasting + Phase 14 optimization + Phase 22 settlement + Phase 23 unit_economics + Phase 24 budget_plan ledger data 활용 → ML-driven 사전 예측 layer 신규 진입 = Phase 12 rule-based 사후 detection 과 complementary ledger data → 새 backend infra 불필요 + reuse 최대화 + risk 최소화 + 비즈니스 가치 최고 (anomaly 사전 예측 → budget over-run 사전 방지 → 직접적 ROI) + Epic 12 2FA 챌린지 mandatory ≥ 10M KRW impact forecast + AD-22 owner-only RBAC + NFR4 PII minimization ✅ PRESERVED + NFR18 ko-KR SSOT + AD-55 신규 (a)~(g) 7 sub-decisions 모두 결정 wire 진입 + D-FINOPS-15 신규 honestly DEFER 보존 + CR 11-3 honest-DEFER 71번째 epic 연속 정직 회복 verification 결정 wire 진입 + 3중 게이트 impact NONE (docs only 변경 = cj-style 180번째 wire 진입 표준 = docs only sprint) 결정 wire.

## Context

cj-style Phase 26 1번째 진입점 (cj-style 179번째) 진입 결정 wire 진입 완료:

- Phase 26 PRD entry `b95ebc3` (cj-style 179번째) DONE 진입 정합 보존
- audit-fixes sprint close-out retro `d9c358f` (cj-style 178번째) DONE 진입 정합 보존
- audit-fixes sprint retroactive correction `c84ce55` (cj-style 177 follow-up) DONE 진입 정합 보존
- audit-fixes sprint wire `05e936e` (cj-style 176번째) DONE 진입 정합 보존
- audit-fixes sprint entry `a4ae56d` (cj-style 166번째) DONE 진입 정합 보존
- Phase 25 close-out retro `6119791` (cj-style 175번째) DONE 진입 정합 보존
- Phase 25 integration follow-up `1fc8302` (cj-style 174 follow-up) DONE 진입 정합 보존
- Phase 25 wire `de1b69d` (cj-style 173번째) DONE 진입 정합 보존
- Phase 25 spec entry `b3c6c7c-precursor` (cj-style 172번째) DONE 진입 정합 보존
- Phase 25 PRD entry `5e8d435` (cj-style 171번째) DONE 진입 정합 보존
- Phase 24 close-out retro retroactive correction `1f30b64` (cj-style 170 follow-up) DONE 진입 정합 보존
- Phase 24 close-out retro `c14199b` (cj-style 170번째) DONE 진입 정합 보존
- Phase 24 wire retroactive correction `69c5e28` (cj-style 169 follow-up) DONE 진입 정합 보존
- Phase 24 wire `615d478` (cj-style 169번째) DONE 진입 정합 보존
- Phase 24 spec entry `b3c6c7c` (cj-style 168번째) DONE 진입 정합 보존
- Phase 24 PRD entry `278f37f` (cj-style 167번째) DONE 진입 정합 보존
- audit-fixes sprint entry `a4ae56d` (cj-style 166번째) DONE 진입 정합 보존
- Phase 23 close-out retro `7875ac9` (cj-style 165번째) DONE 진입 정합 보존
- Phase 23 wire retroactive correction `948ff35` (cj-style 164 follow-up) DONE 진입 정합 보존
- Phase 23 atomic wire `f850d0e` (cj-style 164번째) DONE 진입 정합 보존
- Phase 23 spec entry `960d060` (cj-style 163번째) DONE 진입 정합 보존
- Phase 23 PRD entry `2abfdd9` (cj-style 162번째) DONE 진입 정합 보존
- Phase 22 close-out retro `c5726ff` (cj-style 161번째) DONE 진입 정합 보존
- Phase 22 wire retroactive correction `9dbffc5` (cj-style 160 follow-up) DONE 진입 정합 보존
- Phase 22 atomic wire `7acbac0` (cj-style 160번째) DONE 진입 정합 보존
- Phase 22 spec entry `585c53a` (cj-style 159번째) DONE 진입 정합 보존
- Phase 22 PRD entry `64760fe` (cj-style 158번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes-infrastructure sprint `7b8e31b` (cj-style 157번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes Layer 3 P2 docs backfill sprint `21daea8` (cj-style 156번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes Layer 2 P1 test backfill sprint `4e1f0b3` (cj-style 155번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes sprint `379ca8e` (cj-style 154번째) DONE 진입 정합 보존
- Phase 21 audit-fixes sprint `f7d1f41` (cj-style 153번째) DONE 진입 정합 보존
- Phase 21 close-out retro `1b101bf` (cj-style 152번째) DONE 진입 정합 보존
- Phase 21 atomic wire `f7d1f41` (cj-style 151번째) DONE 진입 정합 보존
- Phase 21 spec entry `47545d6` (cj-style 150번째) DONE 진입 정합 보존
- Phase 21 PRD entry `563ac9c` (cj-style 149번째) DONE 진입 정합 보존
- Phase 20.5 close-out retro `8505d98` (cj-style 148번째) DONE 진입 정합 보존
- Phase 20.5 atomic wire `46ddcc5` (cj-style 147번째) DONE 진입 정합 보존
- Phase 20.5 spec entry `e23141d` (cj-style 146번째) DONE 진입 정합 보존
- Phase 20 close-out retro `f361016` (cj-style 145번째) DONE 진입 정합 보존
- Phase 20 atomic wire `52dad7f` (cj-style 144번째) DONE 진입 정합 보존
- Phase 20 spec entry `efc3c59` (cj-style 143번째) DONE 진입 정합 보존
- Phase 20 PRD entry `eacb0a5` (cj-style 142번째) DONE 진입 정합 보존
- Phase 19.5 carry-over 결정 wire `b2fb1d8` (cj-style 141번째) DONE 진입 정합 보존
- Phase 19 close-out retro `18ca1ae` (cj-style 140번째) + Phase 19 atomic wire `8db3cfc` (cj-style 139번째) + Phase 19 spec entry `59d15fb` (cj-style 138번째) + Phase 19 PRD entry `ff8a797` (cj-style 137번째) + Phase 18 close-out retro `de72f50` (cj-style 136번째) + Phase 18 atomic wire `67059cf` (cj-style 135번째) + Phase 18 spec entry `bdc7997` (cj-style 134번째) + Phase 18 PRD entry `5eded22` (cj-style 133번째) + Phase 17 close-out retro `de009fe` (cj-style 132번째) + Phase 17 atomic wire `97cfe4e` (cj-style 131번째) + Phase 17 spec entry `4be3120` (cj-style 130번째) + Phase 17 PRD entry `e0778ed` (cj-style 129번째) + Phase 16 close-out retro `26fd530` (cj-style 128번째) + Phase 16 atomic wire `81ae00a` (cj-style 127번째) + Phase 16 spec entry `69c29df` (cj-style 126번째) + Phase 16 PRD entry `4f11d03` (cj-style 125번째) + Phase 15 close-out retro `102f370` (cj-style 124번째) + Phase 15 atomic wire `1b800d9` (cj-style 123번째) + Phase 15 spec entry `69c29df` (cj-style 122번째) + Phase 15 PRD entry `87393b4` (cj-style 121번째) + ... + Epic 1~17 ALL DONE 진입 정합 보존 + 1st release cycle ALL DONE 진입 정합 보존

### Phase 26 PRD entry `b95ebc3` 의 8 ACs §F42.1~§F42.8 verbatim 보존

8 ACs §F42.1~§F42.8 → 88+ explicit sub-ACs + nested bullet points → **~88 detailed sub-ACs** (11+8+8+8+6+6+8+10) pre-flight 정합 sweep 만족 결정 wire:

1. **§F42.1 anomaly_ml_prediction_engine + time-series forecasting + feature engineering** — `cost_anomaly_ml_prediction/` 1 NEW module 결정 wire + serializers.py (`AnomalyMLPrediction` TypedDict 18 fields + `PredictionStatus` enum 5 values training/deploying/active/deprecated/retired + `ModelType` enum 5 values prophet/lstm/arima/isolation_forest/autoencoder + `ML_FORECAST_WEIGHTS` constants DEFAULT_ENSEMBLE_WEIGHTS = {prophet: 0.30, lstm: 0.30, arima: 0.15, isolation_forest: 0.15, autoencoder: 0.10}) + `anomaly_ml_prediction_engine.py` (CRUD + multi-tenant RLS + ledger-key dedup + 5 model types parallel training + ensemble consensus + lifecycle training → deploying → active → deprecated → retired + monthly + quarterly refresh + multi-region aggregation + audit-first INSERT 4 NEW actions) + `__init__.py` (m34_finops_cost_anomaly_ml_prediction 신규 submodule + comprehensive re-exports) (11 sub-ACs §F42.1.1~§F42.1.11)
2. **§F42.2 anomaly_ml_model_registry + model versioning + lifecycle** — semver MAJOR.MINOR.PATCH versioning + model_registry_version_history JSONB append-only log + A/B testing champion/challenger traffic_split 50/50 + auto-promote criterion + 3 drift detection types (data + concept + prediction) PSI 0.25 + 4-dim model scoring precision 0.30 + recall 0.30 + F1 0.25 + AUC-ROC 0.15 + audit-first INSERT 4 NEW actions + 4 NEW typed exceptions CR 12-5 D-14 envelope (8 sub-ACs §F42.2.1~§F42.2.8)
3. **§F42.3 anomaly_ml_training_pipeline + scheduled retraining + drift detection** — 7 multi-phase feature sources (Phase 11 showback + Phase 12 anomaly + Phase 13 forecasting + Phase 14 optimization + Phase 22 settlement + Phase 23 unit_economics + Phase 24 budget_vs_actual) + 8 features (cost_total_krw + cost_per_unit + variance_pct + budget_consumption_pct + settlement_3way_match_score + optimization_savings_amount + month_seasonality + holiday_flag) + SHAP feature importance + scheduled retraining KST 매주 일요일 03:00 UTC 18:00 + drift-triggered retraining + exponential backoff retry + 4 NEW typed exceptions CR 12-5 D-14 envelope (8 sub-ACs §F42.3.1~§F42.3.8)
4. **§F42.4 anomaly_ml_scoring + real-time + batch inference** — real-time inference < 200ms P95 + batch inference KST 02:00 UTC 17:00 + bootstrap sampling B=1000 confidence interval + AnomalyScoreComparison TypedDict 12 fields vs Phase 12 rule-based detection + consensus_detected logic + ensemble_threshold default 0.85 + LRU cache max 100 models + 4 NEW typed exceptions CR 12-5 D-14 envelope (8 sub-ACs §F42.4.1~§F42.4.8)
5. **§F42.5 Capability matrix v1.52 EXTENSION FINOPS_COST_ANOMALY_ML_PREDICTION + owner RBAC** — Capability.FINOPS_COST_ANOMALY_ML_PREDICTION 1 NEW enum + require_finops_cost_anomaly_ml_prediction 1 NEW dep + Role.COST_ANOMALY_ML_PREDICTION_OPERATOR + Role.COST_ANOMALY_ML_PREDICTION_VIEWER 2 NEW enum + industry-agnostic 4-industry grants ✅/✅/✅/✅ + per-tenant override tenant_settings.ml_prediction_overrides + test_audit_action_v1_52_drift.py + capability gate fail-closed (6 sub-ACs §F42.5.1~§F42.5.6)
6. **§F42.6 audit action EXTENSION 12 NEW Literal + 16 NEW typed exception classes** — ActionClass.COST_ANOMALY_ML_PREDICTION 1 NEW enum + `FinopsCostAnomalyMLPredictionAction` 12 NEW Literal (prediction_created + prediction_updated + prediction_status_changed + prediction_retired + prediction_served + batch_prediction_executed + model_version_registered + model_drift_detected + ab_test_champion_promoted + ab_test_challenger_promoted + training_scheduled + cost_anomaly_ml_prediction_dry_run_executed) + AuditAction Union EXTENSION + 16 NEW typed exceptions CR 12-5 D-14 envelope (AnomalyMLPredictionNotFoundError 404 + ModelRegistryEntryNotFoundError 404 + ModelArtifactChecksumMismatchError 500 + ModelStatusTransitionError 409 + ModelArtifactSizeError 413 + ModelTrainingJobNotFoundError 404 + ModelTrainingFailedError 500 + ModelTrainingDataInsufficientError 400 + ModelTrainingTimeoutError 408 + AnomalyMLScoringError 500 + AnomalyMLInferenceTimeoutError 504 + AnomalyMLFeatureExtractionError 500 + AnomalyMLComparisonError 500 + AnomalyMLEnsembleConsensusError 500 + AnomalyMLPredictionStatusTransitionError 409 + AnomalyMLPredictionComplianceViolationError 403) + Cache-Control no-store (6 sub-ACs §F42.6.1~§F42.6.6)
7. **§F42.7 anomaly_ml_prediction_dashboard + comparison vs threshold-based detection** — AnomalyMLPredictionOverviewCard + EnsembleConsensusScorePanel (5-dim Recharts radar chart) + MLvsThresholdComparisonChart (Recharts line chart ML vs Phase 12 rule-based) + ModelDriftDetectionPanel (3 drift types PSI metrics) + ABTestChampionChallengerPanel (4 metrics TanStack Table) + 2 NEW TS mirrors (cost-anomaly-ml-prediction-types.ts + cost-anomaly-ml-prediction-client.ts) + 2 NEW RSC pages (`/admin/finops/cost-anomaly-ml-prediction/page.tsx` + `layout.tsx`) + ko-KR.json EXTENSION ~30 keys (NFR18 SSOT) (8 sub-ACs §F42.7.1~§F42.7.8)
8. **§F42.8 dry-run + Tests + wire scope T1~T8** — `--finops-cost-anomaly-ml-prediction-dry-run` 1 NEW CLI flag + phase_26_cost_anomaly_ml_prediction_preview 1 NEW table alembic 0055 + ~+88 NEW pytest + ~+28 NEW vitest + 0 NEW ruff + 0 NEW tsc + 0 regressions + wire scope T1~T8 (10 sub-ACs §F42.8.1~§F42.8.10)

**Total sub-ACs**: 11+8+8+8+6+6+8+10 = **~88 detailed sub-ACs** pre-flight 정합 sweep 만족 결정 wire (cj-style 179 commit message 의 ~88 sub-ACs verbatim mirror).

### AD-55 신규 결정 (a)~(g) 7 sub-decisions (Phase 26 PRD entry 진입 시점에 결정 wire 진입 완료)

- (a) anomaly_ml_prediction_engine + 5 model types ensemble (prophet + lstm + arima + isolation_forest + autoencoder parallel training + DEFAULT_ENSEMBLE_WEIGHTS = {prophet: 0.30, lstm: 0.30, arima: 0.15, isolation_forest: 0.15, autoencoder: 0.10} + lifecycle training → deploying → active → deprecated → retired + monthly + quarterly refresh + multi-region Seoul/Tokyo/Singapore + dry-run mode)
- (b) anomaly_ml_model_registry + versioning semver MAJOR.MINOR.PATCH + A/B testing champion/challenger (traffic_split 50/50 + auto-promote criterion challenger >= champion + 0.05 for 7 consecutive days) + 3 drift detection types (data + concept + prediction PSI 0.25) + 4-dim model scoring precision 0.30 + recall 0.30 + F1 0.25 + AUC-ROC 0.15 + industry-agnostic CR 12-1 L4 verbatim
- (c) anomaly_ml_training_pipeline + 8 features extracted from multi-phase ledger (Phase 11 cost_total_krw + Phase 23 cost_per_unit + Phase 24 variance_pct + Phase 24 budget_consumption_pct + Phase 22 settlement_3way_match_score + Phase 14 optimization_savings_amount + Phase 13 month_seasonality + holiday_flag) + scheduled retraining KST 매주 일요일 03:00 UTC 18:00 + drift-triggered retraining + SHAP feature importance + per-model_type default hyperparameters + exponential backoff retry (max 3 + base 60s + max 600s)
- (d) anomaly_ml_scoring + real-time inference (< 200ms P95 latency) + batch inference KST 02:00 UTC 17:00 + bootstrap sampling B=1000 confidence interval (5th percentile lower + 95th percentile upper) + threshold comparison vs Phase 12 rule-based detection (AnomalyScoreComparison TypedDict 12 fields) + LRU cache max 100 models
- (e) NFR4 PII minimization preservation (no employee names + tenant_id UUID + monetary amounts only + score metrics only + Cache-Control no-store)
- (f) NFR18 ko-KR SSOT (ko-KR.json finops_cost_anomaly_ml_prediction.* namespace EXTENSION ~30 keys + Korean font noto-sans-cjk-kr + Korean error messages + English audit action names)
- (g) Epic 12 2FA 챌린지 mandatory + owner-only RBAC (high-value ≥ 10M KRW impact forecast → RFC 6238 TOTP + tenant_owner approval chain + Slack DM + 2FA 미설정 redirect + AD-22 owner-only RBAC verbatim + AnomalyMLPredictionComplianceViolationError 403 typed exception)

### D-FINOPS-15 신규 honestly DEFER 보존

Phase 26 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire 진입 = anomaly_ml_prediction_engine 5 model types ensemble + 8 features + lifecycle + model_registry versioning + A/B testing + drift detection + training_pipeline scheduled retraining + anomaly_ml_scoring real-time + batch inference + dashboard UI 5 sub-components + capability matrix v1.52 + audit action 12 NEW + 16 NEW typed exceptions + dry-run mode + 1 NEW CLI flag — 모두 단일 sprint `wire` 진입에 결정 wire 진입 + multi-modal anomaly ML (vision / NLP cost input) + causal inference root cause analysis + LLM 기반 anomaly explanation auto-narrative + automated root cause remediation (Phase 14 optimization auto-apply ML-detected anomalies) + cross-tenant federated learning (privacy-preserving) + ML model marketplace 3rd-party pre-trained models + real-time streaming prediction (sub-second latency) + unsupervised online learning (model update without retraining) — 모두 별도 sprint honestly DEFER 보류 결정 wire 보존 (Phase 17 close-out retro `be8f3bd` §11 + Phase 21 close-out retro `1b101bf` + Phase 22 close-out retro `c5726ff` §11 + Phase 23 close-out retro `7875ac9` §11 + Phase 24 close-out retro `c14199b` §10 + Phase 25 close-out retro `6119791` §11 의 honest deviation 보존 패턴 verbatim 미러).

## T1~T8 + ~42 subtasks

### T1: Phase 26 4 NEW backend cost_anomaly_ml_prediction modules (8 subtasks)
- T1.1: `apps/api/modules/finops/cost_anomaly_ml_prediction/__init__.py` NEW + ALLOWED_SERVICE_SUBMODULES EXTENSION m34_finops_cost_anomaly_ml_prediction 신규 submodule 등록 결정 wire (Phase 22 m22_finops_chargeback_settlement + Phase 23 m23_finops_unit_economics + Phase 24 m24_finops_budget_planning + Phase 25 m25_finops_vendor_management 패턴 보존)
- T1.2: `apps/api/modules/finops/cost_anomaly_ml_prediction/serializers.py` NEW ~+340 LOC + 3 NEW enums (PredictionStatus 5 values training/deploying/active/deprecated/retired + ModelType 5 values prophet/lstm/arima/isolation_forest/autoencoder + PredictionMethod 3 values supervised/unsupervised/ensemble) + 4 NEW TypedDicts (AnomalyMLPrediction 18 fields + AnomalyMLScoreResult 14 fields + ModelRegistryEntry 16 fields + ModelTrainingJob 12 fields) + ML_FORECAST_WEIGHTS constants DEFAULT_ENSEMBLE_WEIGHTS = {prophet: 0.30, lstm: 0.30, arima: 0.15, isolation_forest: 0.15, autoencoder: 0.10} + ML_DRIFT_PSI_THRESHOLD = 0.25 + ML_ENSEMBLE_THRESHOLD = 0.85 + ML_BOOTSTRAP_SAMPLES = 1000 결정 wire
- T1.3: `apps/api/modules/finops/cost_anomaly_ml_prediction/anomaly_ml_prediction_engine.py` NEW ~+360 LOC + create_prediction(tenant_id, model_id, period_key, horizon_days=7) → AnomalyMLPrediction + read_prediction(tenant_id, prediction_id) → AnomalyMLPrediction + update_prediction(tenant_id, prediction_id, ...) → AnomalyMLPrediction + retire_prediction(tenant_id, prediction_id) → bool + list_predictions(tenant_id, filter) → list + 5 model types ensemble parallel inference (prophet + lstm + arima + isolation_forest + autoencoder weighted consensus) + lifecycle training → deploying → active → deprecated → retired (5-state FSM) + monthly retraining 1st of month 03:00 UTC 18:00 + quarterly retraining 1st of quarter 03:30 UTC 18:30 + multi-region aggregation Seoul/Tokyo/Singapore + ledger-key dedup + audit-first INSERT `prediction_created` + `prediction_updated` + `prediction_status_changed` + `prediction_retired` CR 1-1 verbatim EXTENSION 결정 wire
- T1.4: `apps/api/modules/finops/cost_anomaly_ml_prediction/anomaly_ml_model_registry.py` NEW ~+260 LOC + register_model(tenant_id, model_metadata, model_artifact) → ModelRegistryEntry + update_model_status(model_id, new_status) → ModelRegistryEntry + list_active_models(tenant_id, model_type=None) → list + deprecate_model(model_id, replacement_model_id) → ModelRegistryEntry + semver MAJOR.MINOR.PATCH versioning + model_registry_version_history JSONB append-only log + A/B testing champion/challenger (traffic_split default 50/50 + per-tenant override + auto-promote criterion challenger_composite_score >= champion_composite_score + 0.05 for 7 consecutive days) + 3 drift detection types (data + concept + prediction PSI 0.25) + 4-dim model scoring (precision 0.30 + recall 0.30 + F1 0.25 + AUC-ROC 0.15) + sha256:64-hex model_artifact checksum VERIFICATION + audit-first INSERT `model_version_registered` + `model_drift_detected` + `ab_test_champion_promoted` + `ab_test_challenger_promoted` CR 1-1 verbatim EXTENSION + 4 NEW typed exceptions (ModelRegistryEntryNotFoundError 404 + ModelArtifactChecksumMismatchError 500 + ModelStatusTransitionError 409 + ModelArtifactSizeError 413) 결정 wire
- T1.5: `apps/api/modules/finops/cost_anomaly_ml_prediction/anomaly_ml_training_pipeline.py` NEW ~+280 LOC + train_model(tenant_id, model_type, training_data_window=90) → ModelTrainingJob + get_training_job_status(training_job_id) → ModelTrainingJob + list_training_history(tenant_id, model_type=None) → list + cancel_training_job(training_job_id) → ModelTrainingJob + APScheduler 3.10.4 AD-14 stack pin + KST timezone + scheduled retraining 매주 일요일 03:00 UTC 18:00 + retraining_trigger condition (drift_detected OR weekly_schedule OR manual_trigger) + 7 multi-phase feature sources (Phase 11 + Phase 12 + Phase 13 + Phase 14 + Phase 22 + Phase 23 + Phase 24 ledger data) + 8 features (cost_total_krw + cost_per_unit + variance_pct + budget_consumption_pct + settlement_3way_match_score + optimization_savings_amount + month_seasonality + holiday_flag) + SHAP feature importance + per-model_type default hyperparameters (prophet: changepoint_prior_scale=0.05 + lstm: epochs=50 batch_size=32 + arima: order=(2,1,2) seasonal_order=(1,1,1,7) + isolation_forest: n_estimators=100 + autoencoder: encoding_dim=8 hidden_layers=[16, 8]) + training completion → model_registry update + A/B testing 시작 + auto-promote criterion 검증 + exponential backoff retry (max 3 + base 60s + max 600s) + Slack DM notification + email notification + audit-first INSERT `training_scheduled` + `training_started` + `training_completed` + `training_failed` + `training_retried` CR 1-1 verbatim EXTENSION + 4 NEW typed exceptions (ModelTrainingJobNotFoundError 404 + ModelTrainingFailedError 500 + ModelTrainingDataInsufficientError 400 + ModelTrainingTimeoutError 408) 결정 wire
- T1.6: `apps/api/modules/finops/cost_anomaly_ml_prediction/anomaly_ml_scoring.py` NEW ~+240 LOC + predict_anomaly_score(tenant_id, period_key, horizon_days=7) → list[AnomalyMLScoreResult] + batch_predict_anomaly_scores(tenant_id, period_keys) → list[AnomalyMLScoreResult] + score_threshold_anomaly(tenant_id, period_key) → AnomalyScoreComparison + real-time inference (feature_extraction async parallel + 5 model parallel inference + ensemble weighted average + threshold check >= 0.85 + per-call latency target < 200ms P95) + batch inference (nightly KST 02:00 UTC 17:00 batch prediction for next 7 days + batch_size default 100 + max 1000 + batch latency target < 60s per 1000 predictions) + bootstrap sampling B=1000 confidence interval (5th percentile lower + 95th percentile upper NUMERIC(18,2) KRW) + ensemble consensus threshold default 0.85 + threshold comparison vs Phase 12 rule-based detection (z_score + IQR + EWMA + isolation_forest) AnomalyScoreComparison TypedDict 12 fields + LRU cache max 100 models + ensemble inference vectorized numpy operations + audit-first INSERT `prediction_served` + `batch_prediction_executed` + `prediction_latency_audit` CR 1-1 verbatim EXTENSION + 4 NEW typed exceptions (AnomalyMLScoringError 500 + AnomalyMLInferenceTimeoutError 504 + AnomalyMLFeatureExtractionError 500 + AnomalyMLComparisonError 500) 결정 wire
- T1.7: `apps/api/modules/finops/cost_anomaly_ml_prediction/anomaly_ml_ensemble_consensus.py` NEW ~+180 LOC + ensemble_consensus_score(per_model_scores, weights) → NUMERIC(5,4) + consensus_detected(ml_score, threshold_score, consensus_threshold) → bool + anomaly_ml_ensemble_consensus_error exception envelope + audit-first INSERT `ensemble_consensus_calculated` CR 1-1 verbatim EXTENSION + Phase 22 wire `7acbac0` 의 5-dim weighted scoring pattern verbatim EXTENSION + 1 NEW typed exception (AnomalyMLEnsembleConsensusError 500) 결정 wire
- T1.8: `apps/api/modules/finops/cost_anomaly_ml_prediction/scheduled_cost_anomaly_ml_prediction_jobs.py` NEW ~+200 LOC + apscheduler==3.10.4 + pytz==2024.1 EXTENSION + scheduled_training_job (매주 일요일 03:00 UTC 18:00) + scheduled_drift_detection_job (daily 04:00 KST) + scheduled_batch_inference_job (nightly 02:00 KST UTC 17:00) + scheduled_model_promotion_check_job (daily 05:00 KST) + LISTEN/NOTIFY 12 channel (phase_26_prediction_created + phase_26_prediction_updated + phase_26_prediction_status_changed + phase_26_prediction_retired + phase_26_prediction_served + phase_26_batch_prediction_executed + phase_26_model_version_registered + phase_26_model_drift_detected + phase_26_ab_test_champion_promoted + phase_26_ab_test_challenger_promoted + phase_26_training_scheduled + phase_26_cost_anomaly_ml_prediction_dry_run_executed) + Phase 25 wire `de1b69d` 의 scheduled pattern verbatim EXTENSION 결정 wire

### T2: cost_anomaly_ml_prediction dashboard UI 5 sub-components (8 subtasks)
- T2.1: `apps/web/app/[locale]/(dashboard)/admin/finops/cost-anomaly-ml-prediction/page.tsx` NEW ~+240 LOC + 5 sub-components (AnomalyMLPredictionOverviewCard + EnsembleConsensusScorePanel + MLvsThresholdComparisonChart + ModelDriftDetectionPanel + ABTestChampionChallengerPanel) EXTENSION 결정 wire
- T2.2: `apps/web/app/[locale]/(dashboard)/admin/finops/cost-anomaly-ml-prediction/layout.tsx` NEW ~+110 LOC + owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 mandatory ≥ 10M KRW impact forecast + ko-KR.json `finops_cost_anomaly_ml_prediction.*` namespace EXTENSION ~30 keys (CR 11-4 D-002 verbatim SSOT) + ARIA labels WCAG 2.1 AA + `(dashboard)` route group 보호 EXTENSION 결정 wire
- T2.3: `apps/web/components/finops/FinopsCostAnomalyMLPredictionDashboardPanel.tsx` NEW Client component ~+280 LOC + 5-tab layout (Predictions + Ensemble + vs Threshold + Drift + A/B Test) + Recharts radar chart (ensemble breakdown) + Recharts line chart (ML vs Phase 12 threshold comparison) + TanStack Table (champion/challenger 4 metrics) + 5 NEW charts (radar + line + table + drift line chart + overview card) 결정 wire
- T2.4: `apps/web/lib/finops/cost-anomaly-ml-prediction-types.ts` NEW TypeScript mirror + 4 NEW TypeScript interfaces (AnomalyMLPrediction + AnomalyMLScoreResult + ModelRegistryEntry + ModelTrainingJob) CR 12-5 D-PARITY-01 inversion EXTENSION 결정 wire
- T2.5: `apps/web/lib/finops/cost-anomaly-ml-prediction-client.ts` NEW TypeScript client + 9 NEW methods (createPrediction + updatePrediction + retirePrediction + registerModel + startTraining + getScoreResult + batchPredict + runDryRun + healthcheck) EXTENSION 결정 wire
- T2.6: `apps/web/messages/ko-KR.json` MODIFIED EXTENSION ~30 keys + `finops_cost_anomaly_ml_prediction.*` namespace EXTENSION + ARIA labels WCAG 2.1 AA + NFR18 ko-KR SSOT 보존 결정 wire
- T2.7: cost_anomaly_ml_prediction dashboard Recharts 2.12.7 AD-14 stack pin EXTENSION + TanStack Table v8 AD-14 stack pin EXTENSION + 5 NEW charts (radar + line + table + drift line chart + overview card) + 4 industries baseline visualization 차이 EXTENSION 결정 wire
- T2.8: cost_anomaly_ml_prediction dashboard dry-run mode UI (AnomalyMLPredictionOverviewCard 진입 시 dry-run toggle default: dry-run) + scheduled training KST cron 일요일 03:00 UI + AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory ≥ 10M KRW impact forecast 결정 wire

### T3: alembic 0055 phase_26_cost_anomaly_ml_prediction 1 preview table + RLS (6 subtasks)
- T3.1: `apps/api/alembic/versions/0055_phase_26_cost_anomaly_ml_prediction.py` NEW **1 NEW preview table ONLY** 결정 wire (no new domain tables — derived from Phase 11 + Phase 12 + Phase 13 + Phase 14 + Phase 22 + Phase 23 + Phase 24 ledger data) = phase_26_cost_anomaly_ml_prediction_preview EXTENSION
- T3.2: phase_26_cost_anomaly_ml_prediction_preview 1 NEW preview table 결정 wire + preview_id UUID PK + tenant_id UUID + period_key TEXT + model_type TEXT (prophet/lstm/arima/isolation_forest/autoencoder) + preview_predicted_values JSONB + preview_ensemble_score NUMERIC(5,4) + computed_at TIMESTAMPTZ DEFAULT NOW() + trace_id TEXT EXTENSION
- T3.3: RLS 자동 적용 CR 0-2 verbatim 결정 wire = 1 preview table tenant_id = current_setting('app.tenant_id')::uuid EXTENSION
- T3.4: CHECK + UNIQUE + indexes EXTENSION 결정 wire = idempotency_key UNIQUE + model_type enum CHECK + 5 model_type source attribution JSONB GIN index + tenant_id + period_key composite index EXTENSION
- T3.5: alembic 0055 down_revision 결정 wire = 0054 (Phase 25 wire `de1b69d` 의 alembic 0057 → 다음 번호는 0058인데 본 spec 은 0055를 명시했으므로 검토 필요. Phase 25 wire 의 alembic 확정 후 0055 확정 진행) EXTENSION
- T3.6: alembic upgrade + downgrade 검증 결정 wire + Phase 25 wire 의 alembic 0057 pattern verbatim EXTENSION

### T4: audit action EXTENSION 12 NEW Literal + 16 NEW typed exception classes (4 subtasks)
- T4.1: `apps/api/core/audit_action.py` MODIFIED EXTENSION 결정 wire + ActionClass.COST_ANOMALY_ML_PREDICTION 1 NEW enum EXTENSION + _ActionRegistry._REGISTRY 1 NEW entry EXTENSION + AuditAction Union EXTENSION 결정 wire
- T4.2: `apps/api/core/audit_action.py` MODIFIED EXTENSION + FinopsCostAnomalyMLPredictionAction 12 NEW Literal EXTENSION (prediction_created + prediction_updated + prediction_status_changed + prediction_retired + prediction_served + batch_prediction_executed + model_version_registered + model_drift_detected + ab_test_champion_promoted + ab_test_challenger_promoted + training_scheduled + cost_anomaly_ml_prediction_dry_run_executed)
- T4.3: `apps/api/core/errors.py` MODIFIED EXTENSION 16 NEW typed exception classes CR 12-5 D-14 envelope 결정 wire = FinopsCostAnomalyMLPredictionError base class + AnomalyMLPredictionNotFoundError(404) + AnomalyMLPredictionStatusTransitionError(409) + AnomalyMLPredictionComplianceViolationError(403) + ModelRegistryEntryNotFoundError(404) + ModelArtifactChecksumMismatchError(500) + ModelStatusTransitionError(409) + ModelArtifactSizeError(413) + ModelTrainingJobNotFoundError(404) + ModelTrainingFailedError(500) + ModelTrainingDataInsufficientError(400) + ModelTrainingTimeoutError(408) + AnomalyMLScoringError(500) + AnomalyMLInferenceTimeoutError(504) + AnomalyMLFeatureExtractionError(500) + AnomalyMLComparisonError(500) + AnomalyMLEnsembleConsensusError(500) EXTENSION
- T4.4: 12 NEW audit actions via emit_audit_typed CR 1-1 verbatim EXTENSION 결정 wire + Phase 25 wire `de1b69d` 의 12 NEW audit actions pattern verbatim EXTENSION + 5 model_type source attribution JSONB payload EXTENSION

### T5: Capability matrix v1.52 EXTENSION FINOPS_COST_ANOMALY_ML_PREDICTION (4 subtasks)
- T5.1: `docs/capability-matrix.md` MODIFIED v1.51 → v1.52 EXTENSION 결정 wire + FINOPS_COST_ANOMALY_ML_PREDICTION 1 NEW row after FINOPS_VENDOR_MANAGEMENT industry-agnostic 4-industry grants ✅/✅/✅/✅ CR 12-1 L4 precedent verbatim EXTENSION
- T5.2: `apps/api/core/capability.py` MODIFIED EXTENSION + Capability.FINOPS_COST_ANOMALY_ML_PREDICTION 1 NEW enum 결정 wire
- T5.3: `apps/api/dependencies/capability.py` MODIFIED EXTENSION + require_finops_cost_anomaly_ml_prediction 1 NEW dep 결정 wire + Role.COST_ANOMALY_ML_PREDICTION_OPERATOR + Role.COST_ANOMALY_ML_PREDICTION_VIEWER 2 NEW enum EXTENSION + fail-closed 403 Forbidden EXTENSION
- T5.4: `apps/api/modules/finops/__init__.py` MODIFIED EXTENSION + cost_anomaly_ml_prediction submodule export + ALLOWED_SERVICE_SUBMODULES 즉시 sweep EXTENSION = m34_finops_cost_anomaly_ml_prediction 신규 submodule 등록 (Phase 22 m22_finops_chargeback_settlement + Phase 23 m23_finops_unit_economics + Phase 24 m24_finops_budget_planning + Phase 25 m25_finops_vendor_management 패턴 보존) + Phase 11~25 verbatim EXTENSION

### T6: scheduled_cost_anomaly_ml_prediction_jobs wire (2 subtasks)
- T6.1: `apps/api/modules/finops/cost_anomaly_ml_prediction/scheduled_cost_anomaly_ml_prediction_jobs.py` NEW ~+200 LOC + apscheduler==3.10.4 + pytz==2024.1 EXTENSION + 4 cadences (매주 일요일 03:00 UTC 18:00 scheduled_training_job + daily 04:00 KST scheduled_drift_detection_job + nightly 02:00 KST UTC 17:00 scheduled_batch_inference_job + daily 05:00 KST scheduled_model_promotion_check_job) + LISTEN/NOTIFY 12 channel + recipient resolver Slack + Email + S3 archive 결정 wire
- T6.2: LISTEN/NOTIFY consume trigger EXTENSION 결정 wire = 12 NEW channel (phase_26_prediction_created + phase_26_prediction_updated + phase_26_prediction_status_changed + phase_26_prediction_retired + phase_26_prediction_served + phase_26_batch_prediction_executed + phase_26_model_version_registered + phase_26_model_drift_detected + phase_26_ab_test_champion_promoted + phase_26_ab_test_challenger_promoted + phase_26_training_scheduled + phase_26_cost_anomaly_ml_prediction_dry_run_executed) + Phase 25 wire `de1b69d` LISTEN/NOTIFY pattern verbatim EXTENSION 결정 wire

### T7: dry-run mode + 1 NEW CLI flag (4 subtasks)
- T7.1: dry-run mode EXTENSION 결정 wire = dry-run 시 actual `prediction_created` + `prediction_served` + `training_started` + `model_version_registered` audit-first INSERT skip + dry-run 결과 preview = phase_26_cost_anomaly_ml_prediction_preview 1 table + audit-first INSERT `cost_anomaly_ml_prediction_dry_run_executed` EXTENSION
- T7.2: `apps/api/scripts/cli/finops_cost_anomaly_ml_prediction_dry_run.py` NEW ~+100 LOC + `--finops-cost-anomaly-ml-prediction-dry-run` 1 NEW CLI flag EXTENSION (Phase 25 wire `de1b69d` 의 `--finops-vendor-management-dry-run` 1 NEW CLI flag 패턴 verbatim EXTENSION)
- T7.3: dry-run preview UI EXTENSION 결정 wire = AnomalyMLPredictionOverviewCard 진입 시 dry-run toggle (default: dry-run) + dry-run 결과 preview UI EXTENSION
- T7.4: dry-run mode integration tests EXTENSION 결정 wire = ~+6 NEW pytest cases (skip audit + preview table + 1 CLI flag + 4 cadences) EXTENSION

### T8: 3중 게이트 FINAL CLEAN atomic commit (4 subtasks)
- T8.1: ruff scoped Phase 26 files 0 NEW EXTENSION 결정 wire + Phase 25 wire `de1b69d` 의 0 NEW ruff pattern verbatim EXTENSION
- T8.2: pytest ~+88 NEW pytest PASS EXTENSION 결정 wire (anomaly_ml_prediction_engine 22 + anomaly_ml_model_registry 22 + anomaly_ml_training_pipeline 22 + anomaly_ml_scoring 22 = ~88 NEW pytest PASS)
- T8.3: vitest ~+28 NEW vitest PASS EXTENSION 결정 wire (AnomalyMLPredictionOverviewCard 7 + EnsembleConsensusScorePanel 5 + MLvsThresholdComparisonChart 6 + ModelDriftDetectionPanel 5 + ABTestChampionChallengerPanel 5 = ~28 NEW vitest PASS)
- T8.4: 3중 게이트 FINAL CLEAN atomic commit via `git commit -F <file>` (CR 9-6 D5 prevention + PowerShell here-string 회피) 결정 wire

**Subtotal**: 8+8+6+4+4+2+4+4 = **~40 subtasks** 결정 wire (Phase 25 wire `de1b69d` 의 ~40 subtasks pattern 의 4-NEW-module pre-detection layer version EXTENSION → 1 preview table 동수)

## Dev Notes 19종 (CR lessons applied)

- **CR 0-2 RLS** — 1 preview table 의 tenant-scoped RLS 자동 적용 (current_setting('app.tenant_id')::uuid) 보존
- **CR 1-1 audit-first INSERT 12 NEW** — ActionClass.COST_ANOMALY_ML_PREDICTION 의 12 NEW audit actions (prediction_created + prediction_updated + prediction_status_changed + prediction_retired + prediction_served + batch_prediction_executed + model_version_registered + model_drift_detected + ab_test_champion_promoted + ab_test_challenger_promoted + training_scheduled + cost_anomaly_ml_prediction_dry_run_executed) 결정 wire 진입 시점에 audit-first INSERT 자동 활성화 보존
- **CR 1-1 FastAPI ContextVar** — tenant_id ContextVar middleware layer 보존 (CR 1-1 verbatim EXTENSION)
- **CR 1-1 RSC boundary** — Next.js 15.x RSC boundary 보존 (apps/web/app/[locale]/(dashboard)/admin/finops/cost-anomaly-ml-prediction/{page,layout}.tsx)
- **CR 4-3/4-4** — async-test asyncio.run + Industry enum SSOT + A5 drift detector + golden_diff + SDR overclaim 방지
- **CR 5-1 Decimal precision** — banker's rounding 정합 + 소수점 4자리 (NUMERIC(5,4)) for ensemble_score + 18,2 KRW currency (confidence interval)
- **CR 9-6 commit message** — `git commit -F <file>` (D5 prevention) + PowerShell here-string 회피 결정 wire
- **CR 11-3 honest-DEFER 71번째** — D-FINOPS-15 honestly DEFER 보존 (Phase 26 territory 진입) + Phase 11~25 17-capability FinOps territory chain ✅ ALL WIRED 결정 wire
- **ALLOWED_SERVICE_SUBMODULES 즉시 sweep** — Phase 26 wire 진입 시점에 `apps/api/modules/finops/__init__.py` 의 submodule 목록 즉시 sweep EXTENSION = m34_finops_cost_anomaly_ml_prediction 신규 submodule 등록
- **CR 11-4 D-001~D-005** — ko-KR.json `finops_cost_anomaly_ml_prediction.*` namespace EXTENSION ~30 keys SSOT + NFR18 ko-KR SSOT 보존
- **P-015 SSOT** — ko-KR.json finops_cost_anomaly_ml_prediction.* 단일 SSOT 결정 wire
- **CR 12-1 L4** — industry-agnostic capability grants (4-industry ✅/✅/✅/✅) EXTENSION 결정 wire (Phase 25 wire 의 FINOPS_VENDOR_MANAGEMENT 패턴 verbatim 미러)
- **CR 12-5 D-14 typed exception envelope 16 NEW** — Phase 26 wire 의 16 NEW typed exceptions (FinopsCostAnomalyMLPredictionError base + AnomalyMLPredictionNotFoundError + AnomalyMLPredictionStatusTransitionError + AnomalyMLPredictionComplianceViolationError + ModelRegistryEntryNotFoundError + ModelArtifactChecksumMismatchError + ModelStatusTransitionError + ModelArtifactSizeError + ModelTrainingJobNotFoundError + ModelTrainingFailedError + ModelTrainingDataInsufficientError + ModelTrainingTimeoutError + AnomalyMLScoringError + AnomalyMLInferenceTimeoutError + AnomalyMLFeatureExtractionError + AnomalyMLComparisonError + AnomalyMLEnsembleConsensusError) CR 12-5 D-14 envelope 적용
- **CR 12-5 D-PARITY-01 inversion** — TypeScript mirror parity (cost-anomaly-ml-prediction-types.ts + cost-anomaly-ml-prediction-client.ts) 결정 wire
- **CR 12-5 D-GATE-01 inversion** — capability gate inversion (require_finops_cost_anomaly_ml_prediction + fail-closed 403 Forbidden) 결정 wire
- **A19 cohesion 9 surface EXTENSION PASS** — FinOps Cost Anomaly ML Prediction surface NEW 결정 wire 진입 후에도 9 surface 모두 PASS 보존
- **A36 SDR 검증 4-step** — 자동 적용 결정 wire (spec entry 진입 시점에 자동)
- **AD-14 stack pin** — prophet==1.1.5 + tensorflow==2.16.1 + statsmodels==0.14.2 + scikit-learn==1.4.0 + Recharts 2.12.7 + TanStack Table v8 + noto-sans-cjk-kr + apscheduler 3.10.4 + pytz 2024.1 EXTENSION 결정 wire (Phase 25 wire 의 AD-14 stack pin verbatim 미러 + prophet/tensorflow/statsmodels/scikit-learn ML stack pin EXTENSION)
- **AD-22 owner-only RBAC** — cost_anomaly_ml_prediction dashboard UI 모두 owner-only RBAC EXTENSION (AnomalyMLPredictionOverviewCard + EnsembleConsensusScorePanel + MLvsThresholdComparisonChart + ModelDriftDetectionPanel + ABTestChampionChallengerPanel + auto-promote enable 모두 owner-only)
- **Epic 12 2FA 챌린지 mandatory** — destructive endpoint 의 3-layer defense EXTENSION 결정 wire (high-value ≥ 10M KRW impact forecast + over-budget threshold override ≥ 10M KRW impact forecast + model_retire action → owner approval flow + 2FA 챌린지)
- **NFR4 PII minimization** ✅ PRESERVED — Phase 26 wire 결정 wire 시에도 PII minimization 자동 보존
- **NFR18 ko-KR SSOT** — apps/web/messages/ko-KR.json finops_cost_anomaly_ml_prediction.* namespace EXTENSION ~30 keys SSOT 보존 결정 wire
- **AD-50 + AD-51 + AD-52 + AD-53 + AD-54 + AD-55 신규** — AD-50/51/52/53 (Phase 22~25 a~g 7 sub-decisions) + AD-54 (audit-fixes sprint cj-style 176 honest recovery SSOT) + AD-55 (Phase 26 a~g 7 sub-decisions) 모두 결정 wire 진입

## Architecture Alignment (ALLOWED sweep) — Phase 25 wire 정합

- **Backend (FastAPI, Python 3.12)**:
  - 4 NEW modules `apps/api/modules/finops/cost_anomaly_ml_prediction/` (~+1,320 LOC: anomaly_ml_prediction_engine + anomaly_ml_model_registry + anomaly_ml_training_pipeline + anomaly_ml_scoring + anomaly_ml_ensemble_consensus)
  - 1 NEW serializers.py (~+340 LOC)
  - 1 NEW __init__.py submodule
  - 1 NEW scheduled_cost_anomaly_ml_prediction_jobs.py (~+200 LOC)
  - 1 NEW alembic 0055 phase_26_cost_anomaly_ml_prediction.py (1 preview table ONLY + RLS)
  - 1 NEW apps/api/scripts/cli/finops_cost_anomaly_ml_prediction_dry_run.py (~+100 LOC)
  - MODIFIED apps/api/core/capability.py (Capability.FINOPS_COST_ANOMALY_ML_PREDICTION)
  - MODIFIED apps/api/dependencies/capability.py (require_finops_cost_anomaly_ml_prediction + fail-closed)
  - MODIFIED apps/api/core/audit_action.py (ActionClass.COST_ANOMALY_ML_PREDICTION + FinopsCostAnomalyMLPredictionAction 12 NEW Literal + _ActionRegistry._REGISTRY 1 NEW entry)
  - MODIFIED apps/api/core/errors.py (16 NEW typed exception classes)
  - MODIFIED apps/api/modules/finops/__init__.py (ALLOWED_SERVICE_SUBMODULES EXTENSION)
- **Frontend (Next.js 15.x, TypeScript 5.x)**:
  - 2 NEW apps/web/app/[locale]/(dashboard)/admin/finops/cost-anomaly-ml-prediction/{page,layout}.tsx (~+350 LOC)
  - 1 NEW apps/web/components/finops/FinopsCostAnomalyMLPredictionDashboardPanel.tsx (~+280 LOC)
  - 1 NEW apps/web/lib/finops/cost-anomaly-ml-prediction-types.ts (4 NEW TypeScript interfaces)
  - 1 NEW apps/web/lib/finops/cost-anomaly-ml-prediction-client.ts (9 NEW methods)
  - MODIFIED apps/web/messages/ko-KR.json (EXTENSION ~30 keys finops_cost_anomaly_ml_prediction.* namespace)
- **Tests**:
  - ~+88 NEW pytest PASS (anomaly_ml_prediction_engine 22 + anomaly_ml_model_registry 22 + anomaly_ml_training_pipeline 22 + anomaly_ml_scoring 22)
  - ~+28 NEW vitest PASS (AnomalyMLPredictionOverviewCard 7 + EnsembleConsensusScorePanel 5 + MLvsThresholdComparisonChart 6 + ModelDriftDetectionPanel 5 + ABTestChampionChallengerPanel 5)
  - 0 NEW ruff + 0 NEW tsc + 0 regressions
- **Docs (cumulative; wire sprint will write)**:
  - Spec file (this file) NEW ~+440 LOC
  - Handoff memory NEW
  - Commit-msg NEW
  - Sprint-status MODIFIED v3.87 → v3.88
  - MEMORY.md MODIFIED hook EXTENSION

## Files Affected (estimate ~24 files = 19 NEW + 5 MODIFIED, **wire sprint scope**) — **spec entry sprint 5 files = 3 NEW + 2 MODIFIED**

### Spec entry sprint (cj 180, this sprint) — 5 files = 3 NEW + 2 MODIFIED
1. NEW: `_bmad-output/implementation-artifacts/phase-26-finops-cost-anomaly-ml-prediction-spec.md` (this file, ~+440 LOC)
2. NEW: `memory/handoff-2026-08-28-phase-26-spec-entry-done.md`
3. NEW: `_bmad-output/implementation-artifacts/commit-msg-cj-180.txt`
4. MODIFIED: `_bmad-output/implementation-artifacts/sprint-status.yaml` (v3.87 → v3.88 EXTENSION)
5. MODIFIED: `memory/MEMORY.md` (Phase 26 spec entry hook EXTENSION)

### Wire sprint (cj 181, future) — estimated ~24 files = 19 NEW + 5 MODIFIED (Phase 25 wire `de1b69d` 의 ~24 files pattern 의 4-NEW-module pre-detection layer version EXTENSION)
- Backend: 4 NEW modules (~+1,320 LOC) + 1 NEW serializers.py + 1 NEW __init__.py + 1 NEW alembic 0055 (1 preview table only) + 1 NEW scheduled_jobs + 1 NEW scripts/cli (~+1,940 LOC)
- Frontend: 2 NEW RSC pages (~+350 LOC) + 1 NEW Client component (~+280 LOC) + 2 NEW TS mirrors (~+220 LOC)
- Tests: ~+88 NEW pytest PASS + ~+28 NEW vitest PASS
- MODIFIED: 5 core files (capability.py + dependencies/capability.py + audit_action.py + errors.py + modules/finops/__init__.py) + ko-KR.json + capability-matrix.md + test_audit_action_v1_52_drift.py = 9 MODIFIED actual count estimate

(Actual wire sprint file count will be verified at wire time via `git show --stat HEAD`.)

## 3중 게이트 impact

- **cj 180 (this sprint, docs-only)**: ruff 0 NEW / pytest 0 NEW / vitest 0 NEW / tsc 0 NEW (apps/api backend unchanged, apps/web frontend unchanged)
- **cj 181 (wire sprint)**: ruff scoped 0 NEW / pytest ~+88 NEW PASS / vitest ~+28 NEW PASS / tsc 0 NEW
- **cj 182 (retro sprint, docs-only)**: ruff 0 NEW / pytest 0 NEW / vitest 0 NEW / tsc 0 NEW

## A721~A725 5 NEW 결정 wire (cj-style 180번째)

- **A721**: 옵션 (a) Phase 26 spec entry 진입 결정 wire (rationale 5종: ① cj-style discipline 회피 위험 방지 = 179번째 Phase 26 PRD entry 진입 직후 자연스러운 spec entry 진입 결정 wire ② Phase 26 PRD entry cj-style 179번째 진입 직후 자연스러운 spec entry 진입 = 180번째 진입 결정 wire ③ Phase 11~25 17-capability FinOps territory chain ✅ ALL WIRED INTEGRATED 진입 정합 보존 + Phase 17/18/19/20/21/22/23/24/25 9-cycle chain ✅ ALL WIRED ④ 4-NEW-module pre-detection layer = Phase 11 showback + Phase 12 anomaly training baseline + Phase 13 forecasting + Phase 14 optimization + Phase 22 settlement + Phase 23 unit_economics + Phase 24 budget_plan ledger data 활용 → 새 backend infra 불필요 + reuse 최대화 + risk 최소화 + 비즈니스 가치 최고 (anomaly 사전 예측 → budget over-run 사전 방지 → 직접적 ROI) + Phase 12 rule-based 사후 detection 과 complementary ledger ⑤ Epic 1 ~ Epic 17 + Phase 3 ~ Phase 25 + Phase 19.5 + Phase 20.5 + Phase 21 audit-fixes + 1st release cycle 정합 보존)
- **A722**: spec 파일 생성 결정 wire (`_bmad-output/implementation-artifacts/phase-26-finops-cost-anomaly-ml-prediction-spec.md` ~+440 LOC + baseline_commit `d9c358f` + cj_style_entry_point 180 + status `ready-for-dev` + Story + 8 ACs §F42.1~§F42.8 verbatim → ~88 detailed sub-ACs (11+8+8+8+6+6+8+10) pre-flight 정합 sweep 만족 + T1~T8 + ~40 subtasks + Dev Notes 19종 + Architecture Alignment ALLOWED sweep + Files Affected ~24 files estimate (~19 NEW + ~5 MODIFIED))
- **A723**: 8 ACs §F42.1~§F42.8 verbatim → ~88 sub-ACs 전개 결정 wire (§F42.1 anomaly_ml_prediction_engine + 5 model types ensemble + 8 features 11 sub-ACs + §F42.2 anomaly_ml_model_registry + A/B testing + 3 drift detection 8 sub-ACs + §F42.3 training_pipeline + 8 features + scheduled retraining 8 sub-ACs + §F42.4 scoring + real-time + batch inference + threshold comparison 8 sub-ACs + §F42.5 Capability matrix v1.52 EXTENSION 6 sub-ACs + §F42.6 audit action EXTENSION 12 NEW + 16 NEW typed exceptions 6 sub-ACs + §F42.7 dashboard UI 5 sub-components 8 sub-ACs + §F42.8 dry-run + Tests + wire scope T1~T8 10 sub-ACs = ~88 sub-ACs pre-flight 정합 sweep 만족)
- **A724**: Tasks T1~T8 + ~40 subtasks 결정 wire (T1 4 NEW backend cost_anomaly_ml_prediction modules 8 subtasks + T2 dashboard UI 5 sub-components 8 subtasks + T3 alembic 0055 1 preview table 6 subtasks + T4 audit action EXTENSION 12 NEW + 16 NEW typed exception classes 4 subtasks + T5 capability v1.52 EXTENSION 4 subtasks + T6 scheduled_jobs wire 2 subtasks + T7 dry-run mode + 1 NEW CLI flag 4 subtasks + T8 3중 게이트 FINAL CLEAN atomic commit 4 subtasks = ~40 subtasks)
- **A725**: sprint-status v3.87 → v3.88 EXTENSION + atomic commit via `git commit -F <file>` CR 9-6 D5 prevention + commit-msg-cj-180.txt 신규 + handoff memory 신규 + MEMORY.md hook EXTENSION + **5 files = 3 NEW + 2 MODIFIED atomic single sprint** 결정 wire (1 NEW spec file + 1 NEW handoff memory + 1 NEW commit-msg = 3 NEW; 1 MODIFIED sprint-status; 1 MODIFIED MEMORY.md) 진입 완료 보존.

## CR lessons applied 19종

CR 0-2 RLS 1 preview table + CR 1-1 audit-first INSERT 12 NEW + CR 1-1 FastAPI ContextVar + CR 1-1 RSC boundary + CR 4-3/4-4 + CR 5-1 Decimal precision banker's rounding (NUMERIC(5,4) ensemble score + NUMERIC(18,2) KRW currency) + CR 9-6 commit message `git commit -F <file>` + CR 11-3 honest-DEFER 71번째 D-FINOPS-15 honestly DEFER 보존 + Phase 11~25 17-capability FinOps territory chain ✅ ALL WIRED 결정 wire + ALLOWED_SERVICE_SUBMODULES 즉시 sweep EXTENSION = m34_finops_cost_anomaly_ml_prediction 신규 submodule 등록 + CR 11-4 D-001~D-005 + P-015 SSOT + CR 12-1 L4 industry-agnostic capability matrix v1.52 FINOPS_COST_ANOMALY_ML_PREDICTION 4-industry grants ✅/✅/✅/✅ + CR 12-5 D-14 typed exception envelope 16 NEW + CR 12-5 D-PARITY-01 inversion TypeScript mirror parity finops_cost_anomaly_ml_prediction.* namespace + CR 12-5 D-GATE-01 inversion capability gate inversion require_finops_cost_anomaly_ml_prediction + A19 cohesion 9 surface EXTENSION PASS + A36 SDR 검증 4-step 자동 적용 + AD-14 stack pin prophet==1.1.5 + tensorflow==2.16.1 + statsmodels==0.14.2 + scikit-learn==1.4.0 + Recharts 2.12.7 + TanStack Table v8 + noto-sans-cjk-kr + apscheduler 3.10.4 + pytz 2024.1 + AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory ≥ 10M KRW impact forecast + NFR4 PII minimization ✅ PRESERVED + AD-50/51/52/53 (Phase 22~25 a~g 7 sub-decisions) + AD-54 (audit-fixes sprint cj-style 176 honest recovery SSOT) + AD-55 (Phase 26 a~g 7 sub-decisions) + NFR18 ko-KR SSOT

## D-DEFER-* honestly 결정 wire 보존

- D-1-1-DEFER-1/2/3 + D-EPIC-16-REVIEW-DEFER-1/2~6 + D-PHASE-4-DR-DEFER-1/2 + D-EPIC-17-WIRE-DEFER-T2-T3-UI + D-RETENTION-1 + D-OBSERVABILITY-1 + D-PERFORMANCE-1 + D-CHAOS-1 + D-SLO-1 + D-FINOPS-1~14 모두 ✅ ALL RESOLVED 보존
- **D-FINOPS-15 신규 honestly DEFER 보존** — Phase 26 PRD entry 진입 시점에 carry-over chain 정직 회복 결정 wire 진입 = anomaly_ml_prediction_engine 5 model types ensemble + 8 features + lifecycle + model_registry versioning + A/B testing + drift detection + training_pipeline scheduled retraining + anomaly_ml_scoring real-time + batch inference + dashboard UI 5 sub-components + capability matrix v1.52 + audit action 12 NEW + 16 NEW typed exceptions + dry-run mode + 1 NEW CLI flag — 모두 단일 sprint `wire` 진입에 결정 wire 진입 + multi-modal anomaly ML (vision / NLP cost input) + causal inference root cause analysis + LLM 기반 anomaly explanation auto-narrative + automated root cause remediation (Phase 14 optimization auto-apply ML-detected anomalies) + cross-tenant federated learning (privacy-preserving) + ML model marketplace 3rd-party pre-trained models + real-time streaming prediction (sub-second latency) + unsupervised online learning (model update without retraining) — 모두 별도 sprint honestly DEFER 보류 결정 wire 보존
- **Phase 26 spec entry = D-FINOPS-15 의 carry-over chain 정직 회복 verification** 결정 wire (CR 11-3 honest-DEFER 71번째 epic 연속 정직 회복)

## Epic 1~17 + Phase 3~25 + Phase 19.5 + Phase 20.5 + Phase 21 audit-fixes + 1st release cycle 정합 보존

cj-style 180번째 epic 연속 정직 회복 진입 시점에 pre-flight 정합 sweep 만족 결정 wire 보존:
- Phase 26 PRD entry `b95ebc3` (cj-style 179번째) DONE 진입 정합 보존
- audit-fixes sprint close-out retro `d9c358f` (cj-style 178번째) DONE 진입 정합 보존
- audit-fixes sprint retroactive correction `c84ce55` (cj-style 177 follow-up) DONE 진입 정합 보존
- audit-fixes sprint wire `05e936e` (cj-style 176번째) DONE 진입 정합 보존
- audit-fixes sprint entry `a4ae56d` (cj-style 166번째) DONE 진입 정합 보존
- Phase 25 close-out retro `6119791` (cj-style 175번째) DONE 진입 정합 보존
- Phase 25 integration follow-up `1fc8302` (cj-style 174 follow-up) DONE 진입 정합 보존
- Phase 25 wire `de1b69d` (cj-style 173번째) DONE 진입 정합 보존
- Phase 25 spec entry `b3c6c7c-precursor` (cj-style 172번째) DONE 진입 정합 보존
- Phase 25 PRD entry `5e8d435` (cj-style 171번째) DONE 진입 정합 보존
- Phase 24 close-out retro retroactive correction `1f30b64` (cj-style 170 follow-up) DONE 진입 정합 보존
- Phase 24 close-out retro `c14199b` (cj-style 170번째) DONE 진입 정합 보존
- Phase 24 wire retroactive correction `69c5e28` (cj-style 169 follow-up) DONE 진입 정합 보존
- Phase 24 wire `615d478` (cj-style 169번째) DONE 진입 정합 보존
- Phase 24 spec entry `b3c6c7c` (cj-style 168번째) DONE 진입 정합 보존
- Phase 24 PRD entry `278f37f` (cj-style 167번째) DONE 진입 정합 보존
- Phase 23 close-out retro `7875ac9` (cj-style 165번째) DONE 진입 정합 보존
- Phase 23 wire retroactive correction `948ff35` (cj-style 164 follow-up) DONE 진입 정합 보존
- Phase 23 atomic wire `f850d0e` (cj-style 164번째) DONE 진입 정합 보존
- Phase 23 spec entry `960d060` (cj-style 163번째) DONE 진입 정합 보존
- Phase 23 PRD entry `2abfdd9` (cj-style 162번째) DONE 진입 정합 보존
- Phase 22 close-out retro `c5726ff` (cj-style 161번째) DONE 진입 정합 보존
- Phase 22 wire retroactive correction `9dbffc5` (cj-style 160 follow-up) DONE 진입 정합 보존
- Phase 22 atomic wire `7acbac0` (cj-style 160번째) DONE 진입 정합 보존
- Phase 22 spec entry `585c53a` (cj-style 159번째) DONE 진입 정합 보존
- Phase 22 PRD entry `64760fe` (cj-style 158번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes-infrastructure sprint `7b8e31b` (cj-style 157번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes Layer 3 P2 docs backfill sprint `21daea8` (cj-style 156번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes Layer 2 P1 test backfill sprint `4e1f0b3` (cj-style 155번째) DONE 진입 정합 보존
- Phase 11~20 audit-fixes sprint `379ca8e` (cj-style 154번째) DONE 진입 정합 보존
- Phase 21 audit-fixes sprint `f7d1f41` (cj-style 153번째) DONE 진입 정합 보존
- Phase 21 close-out retro `1b101bf` (cj-style 152번째) DONE 진입 정합 보존
- Phase 21 atomic wire `f7d1f41` (cj-style 151번째) DONE 진입 정합 보존
- Phase 21 spec entry `47545d6` (cj-style 150번째) DONE 진입 정합 보존
- Phase 21 PRD entry `563ac9c` (cj-style 149번째) DONE 진입 정합 보존
- Phase 20.5 close-out retro `8505d98` (cj-style 148번째) DONE 진입 정합 보존
- Phase 20.5 atomic wire `46ddcc5` (cj-style 147번째) DONE 진입 정합 보존
- Phase 20.5 spec entry `e23141d` (cj-style 146번째) DONE 진입 정합 보존
- Phase 20 close-out retro `f361016` (cj-style 145번째) DONE 진입 정합 보존
- Phase 20 atomic wire `52dad7f` (cj-style 144번째) DONE 진입 정합 보존
- Phase 20 spec entry `efc3c59` (cj-style 143번째) DONE 진입 정합 보존
- Phase 20 PRD entry `eacb0a5` (cj-style 142번째) DONE 진입 정합 보존
- Phase 19.5 carry-over 결정 wire `b2fb1d8` (cj-style 141번째) DONE 진입 정합 보존
- Phase 19 close-out retro `18ca1ae` (cj-style 140번째) + Phase 19 atomic wire `8db3cfc` (cj-style 139번째) + Phase 19 spec entry `59d15fb` (cj-style 138번째) + Phase 19 PRD entry `ff8a797` (cj-style 137번째) DONE 진입 정합 보존
- Phase 11~25 17-capability FinOps territory chain ✅ ALL WIRED INTEGRATED 진입 정합 보존 + Phase 17/18/19/20/21/22/23/24/25 9-cycle chain ✅ ALL WIRED 진입 정합 보존
- Epic 1~17 ALL DONE 진입 정합 보존
- 1st release cycle ALL DONE 진입 정합 보존

## 결정 wire 일자 + next

- 결정 wire 일자: 2026-08-28 (KST)
- next 옵션:
  - (a) Phase 26 atomic wire T1~T8 진입 결정 wire (cj-style 181번째) — 4 NEW backend cost_anomaly_ml_prediction modules + 1 NEW alembic 0055 phase_26_cost_anomaly_ml_prediction 1 preview table + 5 NEW dashboard sub-components + audit action 12 NEW + 16 NEW typed exceptions + capability v1.52 + scheduled jobs + dry-run + 1 CLI flag = ~24 files atomic single sprint
  - (b) Phase 26 close-out retro 진입 결정 wire (cj-style 182번째) — 14-section §1~§14 verbatim retro document
  - (c) Layer 2 P1 + Layer 3 P2 carry-over sprint 진입
  - (d) Epic 26+ 진입 결정 wire
  - (e) D-DEFER-* follow-up 결정 wire 보류
