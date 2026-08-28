/**
 * cost-anomaly-ml-prediction-types — Phase 26 TypeScript types for
 * FinOps Cost Anomaly ML Prediction.
 *
 * Phase 26 wire (cj-style 186번째) — Mirrors Python TypedDicts in
 * `apps/api/modules/finops/cost_anomaly_ml_prediction/serializers.py`.
 * CR 12-5 D-PARITY-01 inversion — Python TypedDict ↔ TypeScript
 * interface parity preserved.
 *
 * Provides:
 * - PredictionStatus (5-state lifecycle: training/deploying/active/deprecated/retired)
 * - ModelType (5 model types: prophet/lstm/arima/isolation_forest/autoencoder)
 * - PredictionMethod (3 methods: supervised/unsupervised/ensemble)
 * - DriftType (3 drift types: data_drift/concept_drift/prediction_drift)
 * - TrainingJobStatus (5-state lifecycle)
 * - AnomalyMLDryRunMode (3 modes: actual/preview/skip)
 * - AnomalyMLPrediction (18 fields, PRD §F42.1 verbatim)
 * - AnomalyMLScoreResult (14 fields, PRD §F42.4 verbatim)
 * - ModelRegistryEntry (16 fields, PRD §F42.2 verbatim)
 * - ModelTrainingJob (12 fields, PRD §F42.3 verbatim)
 * - DEFAULT_ENSEMBLE_WEIGHTS, DRIFT_PSI_THRESHOLD, ENSEMBLE_CONSENSUS_THRESHOLD,
 *   AB_TEST_TRAFFIC_SPLIT_DEFAULT, AB_TEST_AUTO_PROMOTE_MARGIN
 */

export type PredictionStatus =
    | "training"
    | "deploying"
    | "active"
    | "deprecated"
    | "retired";

export type ModelType =
    | "prophet"
    | "lstm"
    | "arima"
    | "isolation_forest"
    | "autoencoder";

export type PredictionMethod = "supervised" | "unsupervised" | "ensemble";

export type DriftType = "data_drift" | "concept_drift" | "prediction_drift";

export type TrainingJobStatus =
    | "scheduled"
    | "running"
    | "completed"
    | "failed"
    | "cancelled";

export type AnomalyMLDryRunMode = "actual" | "preview" | "skip";

/** 5-model ensemble weights (PRD §F42.1 + AD-55 (a) verbatim) */
export const DEFAULT_ENSEMBLE_WEIGHTS: Record<ModelType, number> = {
    prophet: 0.30,
    lstm: 0.30,
    arima: 0.15,
    isolation_forest: 0.15,
    autoencoder: 0.10,
};

/** Drift detection PSI threshold (PRD §F42.2 + AD-55 (b) verbatim) */
export const DRIFT_PSI_THRESHOLD = 0.25;

/** Ensemble consensus threshold (PRD §F42.4 + AD-55 (d) verbatim) */
export const ENSEMBLE_CONSENSUS_THRESHOLD = 0.85;

/** A/B testing traffic split default (PRD §F42.2 + AD-55 (b) verbatim) */
export const AB_TEST_TRAFFIC_SPLIT_DEFAULT = 0.50;

/** A/B auto-promote margin (PRD §F42.2 + AD-55 (b) verbatim) */
export const AB_TEST_AUTO_PROMOTE_MARGIN = 0.05;

/** A/B auto-promote consecutive days required (PRD §F42.2 + AD-55 (b)) */
export const AB_TEST_AUTO_PROMOTE_CONSECUTIVE_DAYS = 7;

/** 4-dim model scoring weights (PRD §F42.2 + AD-55 (b) verbatim —
 * precision 0.30 + recall 0.30 + F1 0.25 + AUC-ROC 0.15) */
export const ML_MODEL_SCORING_WEIGHTS: Record<string, number> = {
    precision: 0.30,
    recall: 0.30,
    f1: 0.25,
    auc_roc: 0.15,
};

/** Real-time inference latency target P95 (PRD §F42.4) */
export const ML_INFERENCE_P95_LATENCY_MS = 200.0;

/** 8 features extracted from multi-phase ledger (PRD §F42.1 verbatim) */
export const ML_FEATURE_NAMES: readonly string[] = Object.freeze([
    "cost_baseline_30d",
    "cost_volatility_30d",
    "budget_consumption_pct",
    "forecast_accuracy_mape",
    "vendor_count_active",
    "anomaly_detections_30d",
    "commitment_utilization_pct",
    "tagging_compliance_pct",
]);

export interface AnomalyMLPrediction {
    prediction_id: string;
    tenant_id: string;
    model_id: string;
    model_type: ModelType;
    period_key: string;
    horizon_days: number;
    features: Record<string, unknown>;
    predicted_values: Record<string, unknown>;
    actual_values: Record<string, unknown>;
    confidence_lower: Record<string, unknown>;
    confidence_upper: Record<string, unknown>;
    predicted_anomaly_score: number;
    threshold_anomaly_score: number;
    ensemble_consensus_score: number;
    prediction_method: PredictionMethod;
    status: PredictionStatus;
    computed_at: string;
}

export interface AnomalyMLScoreResult {
    score_id: string;
    prediction_id: string;
    tenant_id: string;
    period_key: string;
    ml_ensemble_score: number;
    ml_anomaly_detected: boolean;
    threshold_z_score: number;
    threshold_iqr_score: number;
    threshold_ewma_score: number;
    threshold_isolation_forest_score: number;
    threshold_anomaly_detected: boolean;
    consensus_detected: boolean;
    consensus_score: number;
    drift_detected: boolean;
    inference_latency_ms: number;
    served_at: string;
}

export interface ModelRegistryEntry {
    model_id: string;
    tenant_id: string;
    model_name: string;
    model_type: ModelType;
    model_version: string;
    model_artifact_sha256: string;
    model_artifact_size_bytes: number;
    status: PredictionStatus;
    traffic_split_pct: number;
    precision_score: number;
    recall_score: number;
    f1_score: number;
    auc_roc_score: number;
    composite_score: number;
    version_history: Array<Record<string, unknown>>;
    registered_at: string;
}

export interface ModelTrainingJob {
    training_job_id: string;
    tenant_id: string;
    model_id: string;
    model_type: ModelType;
    training_data_window_days: number;
    status: TrainingJobStatus;
    hyperparameters: Record<string, unknown>;
    shap_feature_importance: Record<string, unknown>;
    started_at: string;
    completed_at: string;
    retry_count: number;
    error_message: string;
}

export interface DryRunInput {
    mode: AnomalyMLDryRunMode;
    tenant_id: string;
    period_key: string;
}

export interface DryRunOutput {
    mode: AnomalyMLDryRunMode;
    ensemble_score: number;
    consensus_detected: boolean;
    drift_detected: boolean;
    inference_latency_ms: number;
    note: string;
}
