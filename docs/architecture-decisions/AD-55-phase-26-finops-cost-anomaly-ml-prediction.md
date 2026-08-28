# AD-55 Phase 26 FinOps Cost Anomaly ML Prediction

> **Status:** Active (forward-lock target: Phase 26 FinOps territory maintenance)
> **Deciders:** kjw
> **Date:** 2026-08-28 (Phase 26 PRD entry cj-style 179번째)
> **Source PRD:** §F42 (Phase 26 territory 신규) + Phase 11~25 FinOps territory chain

## Context

Phase 11~25 wire cycles delivered 17-capability FinOps territory chain
(`FINOPS_SHOWBACK` + `FINOPS_CHARGEBACK` + `FINOPS_ANOMALY_DETECTION` +
`FINOPS_BUDGET_ALERT` + `FINOPS_FORECASTING_CAPACITY_PLANNING` +
`FINOPS_OPTIMIZATION` + `FINOPS_TAG_GOVERNANCE` + `FINOPS_REPORTING` +
`FINOPS_SUSTAINABILITY` + `FINOPS_COMMITMENT` + `FINOPS_PRICING` +
`FINOPS_MULTI_CLOUD_UNIFIED_RECONCILIATION` +
`FINOPS_RESERVED_CAPACITY_PLANNING` + `FINOPS_CHARGEBACK_SETTLEMENT` +
`FINOPS_UNIT_ECONOMICS` + `FINOPS_BUDGET_PLANNING` +
`FINOPS_VENDOR_MANAGEMENT`)
— covering showback/chargeback, anomaly detection, forecasting,
optimization, tagging, sustainability, commitment, pricing,
multi-cloud reconciliation, reserved capacity planning,
chargeback settlement, unit economics, budget planning,
and vendor management.

Audit-fixes sprint close-out retro `d9c358f` (cj-style 178번째) verified
the chain is wired (Phase 11~25 17-capability FinOps territory chain
✅ ALL WIRED INTEGRATED via Phase 25 wire `de1b69d` + retroactive
correction `1fc8302` + Phase 25 close-out retro `6119791` + audit-fixes
sprint wire `05e936e` + retroactive correction `c84ce55`). All 65
`emit_audit_typed` call sites verified canonical signature applied
via AST-walk universal drift detector. Phase 26 PRD entry
(cj-style 179번째) extends the chain with the **ML-driven cost
anomaly prediction layer** — the ML-driven counterpart to Phase 12
rule-based `FINOPS_ANOMALY_DETECTION`. Where Phase 12 operates on
threshold-based detection (z_score + IQR + EWMA + isolation_forest
with multi-method voting consensus), Phase 26 operates on ML-driven
time-series forecasting with 5 model types ensemble (prophet +
lstm + arima + isolation_forest + autoencoder) + drift detection +
A/B testing champion/challenger pattern.

Phase 11 showback time-series + Phase 12 anomaly training data +
Phase 13 forecasting capacity planning + Phase 14 optimization
recommendations + Phase 18 commitment utilization + Phase 19 pricing
rate cards + Phase 22 settlement time-series + Phase 23
unit_economics ledger + Phase 24 budget_vs_actual variance + Phase 25
vendor spend attribution → Phase 26 anomaly_ml_prediction_engine +
anomaly_ml_model_registry + anomaly_ml_training_pipeline +
anomaly_ml_scoring 결정 wire.

## Decision

AD-55 specifies 7 sub-decisions for Phase 26 FinOps Cost Anomaly
ML Prediction:

### (a) anomaly_ml_prediction_engine + 5 model types ensemble decision

The anomaly ML prediction engine manages CRUD operations for ML
prediction records. Each prediction has (prediction_id UUID PK +
tenant_id UUID + model_id UUID FK + model_type enum prophet/lstm/
arima/isolation_forest/autoencoder + period_key TEXT + horizon_days
INT default 7 + features JSONB + predicted_values JSONB +
actual_values JSONB nullable + confidence_lower JSONB +
confidence_upper JSONB + predicted_anomaly_score NUMERIC(5,4) +
threshold_anomaly_score NUMERIC(5,4) + ensemble_consensus_score
NUMERIC(5,4) + prediction_method enum supervised/unsupervised/
ensemble + status enum training/deploying/active/deprecated/retired +
computed_at + trace_id + actor_id). 5 model types parallel training
+ ensemble weighted consensus (DEFAULT_ENSEMBLE_WEIGHTS =
{prophet: 0.30, lstm: 0.30, arima: 0.15, isolation_forest: 0.15,
autoencoder: 0.10}). Lifecycle transitions: `training` → `deploying`
→ `active` (production serving) → `deprecated` (shadow mode) →
`retired` (archived). Audit-first INSERT `prediction_created` +
`prediction_updated` + `prediction_status_changed` +
`prediction_retired` CR 1-1 verbatim 결정 wire. Multi-tenant RLS via
`tenant_id` column CR 0-2 verbatim 결정 wire. Feature engineering
uses Phase 11 showback + Phase 12 anomaly baseline + Phase 13
forecasting + Phase 14 optimization + Phase 22 settlement + Phase 23
unit_economics + Phase 24 budget_vs_actual → 7 multi-phase feature
sources 결정 wire.

### (b) model_registry + version control + A/B testing + drift detection decision

Model registry provides versioning + A/B testing champion/challenger
+ 3 drift detection types (data + concept + prediction PSI metrics
threshold 0.25). Versioning: semver MAJOR.MINOR.PATCH (MAJOR =
incompatible change, MINOR = backward-compatible feature, PATCH =
bug fix / retraining). A/B testing: champion vs challenger with
traffic_split default 50/50, duration default 14 days, auto-promote
criterion (challenger composite_score >= champion composite_score +
0.05 margin for 7 consecutive days). 4-dim model scoring: precision
0.30 + recall 0.30 + F1 0.25 + AUC-ROC 0.15 = Phase 25 vendor
performance_evaluation 4-dim weighted scoring pattern verbatim
EXTENSION. Drift detection: data drift (input feature distribution
shift) + concept drift (target variable distribution shift) +
prediction drift (model output distribution shift). PSI threshold
0.25 (above = drift detected → auto-retraining trigger). Audit-first
INSERT `model_version_registered` + `model_drift_detected` +
`ab_test_champion_promoted` + `ab_test_challenger_promoted` CR
1-1 verbatim 결정 wire. Reuses Phase 22 isolation_forest retraining
cadence pattern verbatim EXTENSION + per-tenant override
`tenant_settings.ml_prediction_overrides.{horizon_days,
ensemble_threshold, ab_traffic_split, drift_psi_threshold,
hyperparameters, bootstrap_samples}` EXTENSION chain 결정 wire.

### (c) training_pipeline + 8 features + scheduled retraining + drift-triggered retraining decision

Training pipeline supports offline batch retraining with 8 features
extracted from multi-phase ledger: (1) cost_total_krw (Phase 11
showback) + (2) cost_per_unit (Phase 23 unit_economics) + (3)
variance_pct (Phase 24 budget_vs_actual) + (4) budget_consumption_pct
(Phase 24 budget_plan) + (5) settlement_3way_match_score (Phase 22
settlement) + (6) optimization_savings_amount (Phase 14 optimization)
+ (7) month_seasonality dummy 0-11 (Phase 13 forecasting) + (8)
holiday_flag bool. Feature importance via SHAP (SHapley Additive
exPlanations). Per-model_type default hyperparameters: prophet
(changepoint_prior_scale=0.05, seasonality_mode=additive,
yearly_seasonality=True, weekly_seasonality=True) + lstm
(epochs=50, batch_size=32, learning_rate=0.001, sequence_length=30)
+ arima (order=(p=2, d=1, q=2), seasonal_order=(P=1, D=1, Q=1, s=7))
+ isolation_forest (n_estimators=100, contamination=0.1,
random_state=42) + autoencoder (encoding_dim=8, hidden_layers=[16,
8], epochs=50, batch_size=32). Scheduled retraining cadence KST
매주 일요일 03:00 UTC 18:00 (Phase 12 isolation_forest retraining
cadence 와 동일) + auto-retraining trigger condition
(drift_detected OR weekly_schedule OR manual_trigger). Training
failure recovery: exponential backoff retry (max 3 retries, base 60s,
max 600s) + Slack DM notification to data_science_team + email
notification. Audit-first INSERT `training_scheduled` +
`training_started` + `training_completed` + `training_failed` +
`training_promotion_decision` CR 1-1 verbatim 결정 wire.
CR 12-5 D-14 typed exception envelope 16 NEW typed exception
classes (AnomalyMLPredictionNotFoundError 404 + ModelRegistryEntry
NotFoundError 404 + ModelArtifactChecksumMismatchError 500 + Model
StatusTransitionError 409 + ModelArtifactSizeError 413 + Model
TrainingJobNotFoundError 404 + ModelTrainingFailedError 500 + Model
TrainingDataInsufficientError 400 + ModelTrainingTimeoutError 408 +
AnomalyMLScoringError 500 + AnomalyMLInferenceTimeoutError 504 +
AnomalyMLFeatureExtractionError 500 + AnomalyMLComparisonError 500
+ AnomalyMLEnsembleConsensusError 500 + AnomalyMLPredictionStatus
TransitionError 409 + AnomalyMLPredictionComplianceViolationError
403) 결정 wire.

### (d) anomaly_ml_scoring + real-time + batch inference + threshold comparison decision

ML scoring supports both real-time inference (per-call latency
target < 200ms P95) + batch inference (nightly KST 02:00 UTC 17:00
batch prediction for next 7 days, batch latency target < 60s per
1000 predictions). Per-call workflow: feature_extraction
(cost_total_krw + variance_pct + budget_consumption_pct + settle
ment_3way_match_score + optimization_savings_amount + month_season
ality dummy + holiday_flag) → 5 model parallel inference → ensemble
weighted average → threshold check (>= 0.85) → score_id INSERT +
audit-first INSERT `prediction_served` CR 1-1 verbatim. Confidence
interval: bootstrap sampling B=1000, 5th percentile lower +
95th percentile upper NUMERIC(18,2) KRW currency. Ensemble score
threshold comparison vs Phase 12 rule-based detection:
AnomalyScoreComparison TypedDict 12 fields
(tenant_id + period_key + ml_ensemble_score + ml_anomaly_detected +
threshold_z_score + threshold_iqr_score + threshold_ewma_score +
threshold_isolation_forest_score + threshold_anomaly_detected +
consensus_detected + consensus_score + drift_detected). Inference
performance optimization: model artifact in-memory LRU cache (max
100 models) + feature_extraction async parallel + ensemble
inference vectorized numpy operations. Audit-first INSERT
`prediction_latency_audit` CR 1-1 verbatim (monthly aggregate
latency metrics for performance monitoring) 결정 wire.

### (e) NFR4 PII minimization preserved decision

NFR4 PII minimization is preserved across all 4 modules:
anomaly_ml_prediction_engine (only feature vectors + prediction
metadata, no employee data beyond tenant_owner UUIDs) + model_registry
(only model metadata + 4-dim scoring metrics, no employee data) +
training_pipeline (only feature vectors + hyperparameters + SHAP
feature_importance, no employee data beyond actor_id UUIDs) +
anomaly_ml_scoring (only ensemble scores + confidence intervals +
model_versions, no employee data). All audit log entries
(`prediction_created` + `prediction_updated` + `prediction_status
_changed` + `prediction_retired` + `prediction_served` + `batch
_prediction_executed` + `model_version_registered` + `model_drift
_detected` + `ab_test_champion_promoted` + `ab_test_challenger
_promoted` + `training_scheduled` + `cost_anomaly_ml_prediction
_dry_run_executed`) carry only `actor_id` (UUID) + `tenant_id`
(UUID) + prediction metadata + scoring metrics — no raw PII.
`Cache-Control: no-store` header on all cost_anomaly_ml_prediction
endpoints.

### (f) NFR18 ko-KR SSOT decision

All UI strings in `apps/web/messages/ko-KR.json` under the
`finops_cost_anomaly_ml_prediction.*` namespace (~30 NEW keys):
predictions + ensemble + comparison + drift + ab_test + dashboard +
alerts + retraining. Korean font: `noto-sans-cjk-kr` (AD-14 stack
pin). Error messages in Korean only
(`AnomalyMLPredictionNotFoundError("ML 예측을 찾을 수 없습니다")`
pattern). Audit log action names in English (SSOT for
cross-system queryability) but UI labels in Korean (NFR18 ko-KR
SSOT).

### (g) Epic 12 2FA 챌린지 mandatory + owner-only decision

ML prediction model artifact upload / retire for high-value
configurations (≥ 10M KRW impact forecast) requires Epic 12 2FA
챌린지 mandatory (RFC 6238 TOTP) + tenant_owner approval chain
(Slack DM + 2FA + approval_chain) per Phase 18 commitment
high-value pattern and Phase 19 pricing TCO high-value pattern and
Phase 22 settlement high-value pattern and Phase 24 budget_plan
high-value pattern and Phase 25 vendor_contract high-value pattern.
ML prediction auto-retraining trigger for drift_detected requires
owner-only manual ack (CR 11-3 honest-DEFER discipline 179번째 epic
연속 정직 회복). 2FA 미설정 tenant 의 경우
`/account/security?reason=2fa_required` redirect. Owner-only RBAC
(AD-22 verbatim) on all cost_anomaly_ml_prediction endpoints + Epic
12 M12-a 2FA 챌린지 mandatory. `AnomalyMLPredictionCompliance
ViolationError(403)` for tenant with denied ML prediction access.

## Consequences

### Positive

- Closes the pre-detection gap: ML prediction (Phase 26) →
  threshold detection (Phase 12) → budget alert (Phase 12) →
  investigation → remediation chain
- ML-driven prediction enhances Phase 12 rule-based detection
  (precision/recall improvement via supervised learning) while
  preserving Phase 12 backward compatibility (Phase 12 detection
  continues independently)
- Reuses Phase 11 showback + Phase 12 anomaly + Phase 13 forecasting
  + Phase 14 optimization + Phase 22 settlement + Phase 23
  unit_economics + Phase 24 budget_plan ledger data (no new ledger
  ingestion required) — pure ML layer that adds predictive
  capability on top of existing baseline
- A/B testing champion/challenger pattern + drift detection
  auto-retraining preserves prediction accuracy over time
- 5 model ensemble (prophet + lstm + arima + isolation_forest +
  autoencoder) covers diverse cost anomaly patterns (seasonal +
  trend + outlier + reconstruction error)
- Shadow mode + dry-run mode + per-tenant override chain enables
  gradual rollout without disrupting existing Phase 12 detection
- Industry-agnostic (4-industry grants ✅/✅/✅/✅) — same as
  Phase 11~25 FinOps territory chain
- Pure function computation (tenant_id in + predicted + confidence
  out, model_id in + composite_score out, ledger in + features out)
  — easy to test, easy to verify, low risk of drift
- Sequential retraining + drift-triggered retraining + A/B testing
  gives robustness for prediction accuracy over time
- Comparison view (ML vs Phase 12 rule-based) gives tenant_owner
  transparency on prediction confidence

### Negative / Risks honestly DEFERred

- **D-FINOPS-15 신규 honestly DEFER**: cost_anomaly_ml_prediction
  의 5 model types backend detail + ensemble consensus detail +
  model_registry versioning + A/B testing champion/challenger
  detail + 3 drift detection types detail + training_pipeline 8
  features + scheduled retraining + drift-triggered retraining
  detail + real-time + batch inference detail + Phase 12
  threshold comparison detail — 모두 Phase 26 wire cycle 진입
  시점에 honestly DEFER 결정 wire 보존 (spec entry cj-style 180번째
  진입 시점에 detail 결정 wire 진입, wire cycle cj-style 181번째
  진입 시점에 implementation 결정 wire 진입, retro cj-style
  182번째 진입 시점에 close-out 결정 wire 진입)
- **Multi-modal anomaly ML DEFERred**: vision / NLP cost input
  (graph + text description) for anomaly ML 시 별도 epic 필요
- **Causal inference root cause analysis DEFERred**: ML anomaly
  detected 후 자동 root cause 분석 (인과관계 inference + 원인
  variable 식별) 시 별도 epic 필요
- **LLM 기반 anomaly explanation DEFERred**: anomaly detected 후
  LLM (Claude API) 이 자연어 explanation 자동 생성 (tenant_owner
  dashboard 에 auto-narrative) 시 별도 epic 필요
- **Automated root cause remediation DEFERred**: ML-detected
  anomaly 시 Phase 14 optimization 의 rightsizing recommendation
  자동 apply (manual owner approval 없이) 시 별도 epic 필요
- **Cross-tenant federated learning DEFERred**: multi-tenant
  privacy-preserving federated learning (각 tenant 모델은
  local training, aggregate 만 공유) 시 별도 epic 필요
- **ML model marketplace DEFERred**: 3rd-party pre-trained
  anomaly ML 모델 marketplace integration (AWS Lookout for
  Metrics, Azure Anomaly Detector 등) 시 별도 epic 필요
- **Real-time streaming prediction DEFERred**: sub-second latency
  (< 100ms) streaming prediction (Kafka + Flink) integration 시
  별도 epic 필요
- **Unsupervised online learning DEFERred**: model online update
  (incremental learning without full retraining) 시 별도 epic 필요

## Related

- [[AD-53]] Phase 25 vendor management
- [[AD-52]] Phase 24 budget planning
- [[AD-51]] Phase 23 unit economics
- [[AD-50]] Phase 22 chargeback settlement
- [[AD-49]] Phase 11~20 audit-fixes canonical signature recovery
- [[AD-54]] Audit-fixes sprint cj-style 176 honest recovery
- [[handoff-2026-08-27-phase-25-prd-entry-done]] (cj 171)
- [[handoff-2026-08-28-phase-25-close-out-done]] (cj 175)
- [[handoff-2026-08-28-audit-fixes-cj-176-wire-done]] (cj 176)
- [[handoff-2026-08-28-audit-fixes-retroactive-correction-cj-177]] (cj 177)
- [[handoff-2026-08-28-audit-fixes-cj-178-close-out-done]] (cj 178)
- Phase 26 PRD entry §F42 (master PRD v11.0 → v12.0 EXTENSION)
- Phase 26 spec entry cj-style 180 진입 대기
- Phase 26 atomic wire T1~T8 cj-style 181 진입 대기
- Phase 26 close-out retro cj-style 182 진입 대기

## Date

2026-08-28 (KST) — Phase 26 PRD entry 결정 wire 진입 시점

## Next

옵션 (a) Phase 26 spec entry 진입 결정 wire (cj-style 180번째) / 옵션 (b) Phase 26 atomic wire T1~T8 진입 결정 wire (cj-style 181번째) / 옵션 (c) Phase 26 close-out retro 진입 결정 wire (cj-style 182번째) / 옵션 (d) Layer 2 P1 + Layer 3 P2 carry-over sprint 진입 / 옵션 (e) Epic 26+ 진입 결정 wire / 옵션 (f) D-DEFER-* follow-up 결정 wire 보류.
