/**
 * cost-anomaly-ml-prediction-client — Phase 26 TypeScript fetch client
 * for FinOps Cost Anomaly ML Prediction.
 *
 * Phase 26 wire (cj-style 186번째) — Mirrors FastAPI router endpoints
 * in `apps/api/modules/finops/cost_anomaly_ml_prediction/`.
 *
 * 6 endpoints:
 * 1. fetchPredictions — GET /api/finops/cost-anomaly-ml-prediction/predictions
 * 2. fetchScores — GET /api/finops/cost-anomaly-ml-prediction/scores
 * 3. fetchModels — GET /api/finops/cost-anomaly-ml-prediction/models
 * 4. fetchTrainingJobs — GET /api/finops/cost-anomaly-ml-prediction/training-jobs
 * 5. runPredictionDryRun — POST /api/finops/cost-anomaly-ml-prediction/dry-run
 * 6. fetchEnsembleSummary — GET /api/finops/cost-anomaly-ml-prediction/ensemble-summary
 *
 * CR 1-1 RSC boundary + CR 12-5 D-PARITY-01 + AD-22 owner-only RBAC.
 */

import type {
    AnomalyMLPrediction,
    AnomalyMLScoreResult,
    ModelRegistryEntry,
    ModelTrainingJob,
    DryRunInput,
    DryRunOutput,
} from "./cost-anomaly-ml-prediction-types";

const API_BASE = "/api/finops/cost-anomaly-ml-prediction";

async function get<T>(path: string): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
    });
    if (!res.ok) {
        throw new Error(`GET ${path} failed: ${res.statusText}`);
    }
    return res.json();
}

async function post<T, B>(path: string, body: B): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        throw new Error(`POST ${path} failed: ${res.statusText}`);
    }
    return res.json();
}

export async function fetchPredictions(
    periodKey?: string,
    status?: string
): Promise<{ predictions: AnomalyMLPrediction[] }> {
    const params = new URLSearchParams();
    if (periodKey) params.set("period_key", periodKey);
    if (status) params.set("status_filter", status);
    const qs = params.toString();
    return get(`/predictions${qs ? `?${qs}` : ""}`);
}

export async function fetchScores(
    periodKey?: string
): Promise<{ scores: AnomalyMLScoreResult[] }> {
    const params = new URLSearchParams();
    if (periodKey) params.set("period_key", periodKey);
    const qs = params.toString();
    return get(`/scores${qs ? `?${qs}` : ""}`);
}

export async function fetchModels(
    status?: string
): Promise<{ models: ModelRegistryEntry[] }> {
    const params = new URLSearchParams();
    if (status) params.set("status_filter", status);
    const qs = params.toString();
    return get(`/models${qs ? `?${qs}` : ""}`);
}

export async function fetchTrainingJobs(
    status?: string
): Promise<{ training_jobs: ModelTrainingJob[] }> {
    const params = new URLSearchParams();
    if (status) params.set("status_filter", status);
    const qs = params.toString();
    return get(`/training-jobs${qs ? `?${qs}` : ""}`);
}

export async function runPredictionDryRun(
    input: DryRunInput
): Promise<DryRunOutput> {
    return post<DryRunOutput, DryRunInput>("/dry-run", input);
}

export async function fetchEnsembleSummary(
    periodKey: string
): Promise<{
    period_key: string;
    ensemble_score: number;
    consensus_detected: boolean;
    model_breakdown: Record<string, number>;
    drift_detected: boolean;
}> {
    return get(`/ensemble-summary?period_key=${encodeURIComponent(periodKey)}`);
}
