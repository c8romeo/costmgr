"use client";

/**
 * AnomalyMLPredictionOverviewCard — Phase 26 Cost Anomaly ML Prediction Overview.
 *
 * Phase 26 wire (cj-style 186번째) — PRD §F42.1 + AD-55 (a) verbatim.
 * KPI tiles for: active predictions count, registered models count,
 * drift alerts count, ensemble consensus score gauge.
 *
 * Composes inputs from fetchPredictions + fetchModels + fetchEnsembleSummary.
 * Capability gate: require_finops_cost_anomaly_ml_prediction
 * (Phase 26 capability matrix v1.52 EXTENSION).
 */

import { useEffect, useState } from "react";

import {
    fetchEnsembleSummary,
    fetchModels,
    fetchPredictions,
} from "@/lib/finops/cost-anomaly-ml-prediction-client";
import type {
    AnomalyMLPrediction,
    ModelRegistryEntry,
} from "@/lib/finops/cost-anomaly-ml-prediction-types";
import {
    DEFAULT_ENSEMBLE_WEIGHTS,
    ENSEMBLE_CONSENSUS_THRESHOLD,
} from "@/lib/finops/cost-anomaly-ml-prediction-types";

interface AnomalyMLPredictionOverviewCardProps {
    dryRun: boolean;
    periodKey: string;
}

export function AnomalyMLPredictionOverviewCard({
    dryRun,
    periodKey,
}: AnomalyMLPredictionOverviewCardProps) {
    const [predictions, setPredictions] = useState<AnomalyMLPrediction[]>([]);
    const [models, setModels] = useState<ModelRegistryEntry[]>([]);
    const [ensembleScore, setEnsembleScore] = useState<number>(0);
    const [consensusDetected, setConsensusDetected] = useState<boolean>(false);
    const [driftDetected, setDriftDetected] = useState<boolean>(false);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        async function load() {
            setLoading(true);
            setError(null);
            try {
                const [predRes, modelRes, ensembleRes] = await Promise.all([
                    fetchPredictions(periodKey),
                    fetchModels(),
                    fetchEnsembleSummary(periodKey),
                ]);
                if (cancelled) return;
                setPredictions(predRes.predictions || []);
                setModels(modelRes.models || []);
                setEnsembleScore(ensembleRes.ensemble_score);
                setConsensusDetected(ensembleRes.consensus_detected);
                setDriftDetected(ensembleRes.drift_detected);
            } catch (err) {
                if (cancelled) return;
                setError(
                    err instanceof Error
                        ? err.message
                        : "anomaly_ml_prediction_load_failed",
                );
            } finally {
                if (!cancelled) setLoading(false);
            }
        }
        void load();
        return () => {
            cancelled = true;
        };
    }, [periodKey]);

    if (loading) {
        return (
            <div className="text-slate-400">
                이상탐지 ML 예측 데이터를 불러오는 중...
            </div>
        );
    }
    if (error) {
        return (
            <div className="text-rose-400" role="alert">
                Error: {error}
            </div>
        );
    }

    const activePredictions = predictions.filter(
        (p) => p.status === "active",
    ).length;
    const activeModels = models.filter((m) => m.status === "active").length;
    const driftAlerts = predictions.filter(
        (p) => p.predicted_anomaly_score >= ENSEMBLE_CONSENSUS_THRESHOLD,
    ).length;
    const totalEnsembleWeight = Object.values(DEFAULT_ENSEMBLE_WEIGHTS).reduce(
        (sum, w) => sum + w,
        0,
    );

    return (
        <section
            aria-label="Anomaly ML prediction overview"
            className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
        >
            <header className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900">
                    이상탐지 ML 예측 개요
                </h2>
                <span
                    className={`rounded-full px-3 py-1 text-xs font-medium ${
                        dryRun
                            ? "bg-amber-100 text-amber-700"
                            : "bg-blue-100 text-blue-700"
                    }`}
                >
                    {dryRun ? "Dry-run" : "Live"}
                </span>
            </header>

            <dl className="mt-4 grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
                <div className="rounded-lg bg-slate-50 p-4">
                    <dt className="font-medium text-slate-700">
                        활성 예측 (Active Predictions)
                    </dt>
                    <dd className="mt-1 text-2xl font-bold text-slate-900">
                        {activePredictions}
                    </dd>
                    <p className="mt-1 text-xs text-slate-500">
                        전체 {predictions.length}개 중
                    </p>
                </div>
                <div className="rounded-lg bg-slate-50 p-4">
                    <dt className="font-medium text-slate-700">
                        등록 모델 (Registered Models)
                    </dt>
                    <dd className="mt-1 text-2xl font-bold text-emerald-600">
                        {activeModels}
                    </dd>
                    <p className="mt-1 text-xs text-slate-500">
                        5-모델 앙상블 가중치 합 {totalEnsembleWeight.toFixed(2)}
                    </p>
                </div>
                <div className="rounded-lg bg-slate-50 p-4">
                    <dt className="font-medium text-slate-700">
                        이상 경보 (Anomaly Drift Alerts)
                    </dt>
                    <dd
                        className={`mt-1 text-2xl font-bold ${
                            driftAlerts > 0 ? "text-rose-600" : "text-slate-900"
                        }`}
                    >
                        {driftAlerts}
                    </dd>
                    <p className="mt-1 text-xs text-slate-500">
                        임계값 {ENSEMBLE_CONSENSUS_THRESHOLD.toFixed(2)} 이상
                    </p>
                </div>
                <div className="rounded-lg bg-slate-50 p-4">
                    <dt className="font-medium text-slate-700">
                        앙상블 합의 점수 (Ensemble Consensus)
                    </dt>
                    <dd
                        className={`mt-1 text-2xl font-bold ${
                            consensusDetected
                                ? "text-rose-600"
                                : "text-emerald-600"
                        }`}
                    >
                        {ensembleScore.toFixed(4)}
                    </dd>
                    <p className="mt-1 text-xs text-slate-500">
                        {consensusDetected ? "합의 감지됨" : "정상 범위"}
                        {driftDetected && " · 드리프트 감지"}
                    </p>
                </div>
            </dl>
        </section>
    );
}
