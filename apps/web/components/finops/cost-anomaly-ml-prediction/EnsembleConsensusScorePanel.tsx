"use client";

/**
 * EnsembleConsensusScorePanel — Phase 26 Cost Anomaly ML Prediction
 * Ensemble Consensus Score breakdown.
 *
 * Phase 26 wire (cj-style 186번째) — PRD §F42.1 + §F42.4 + AD-55 (a)
 * verbatim. 5 model types (prophet/lstm/arima/isolation_forest/autoencoder)
 * weighted ensemble + consensus threshold gauge.
 *
 * Default 5-model weights: prophet 0.30 + lstm 0.30 + arima 0.15 +
 * isolation_forest 0.15 + autoencoder 0.10.
 */

import { useEffect, useState } from "react";

import { fetchEnsembleSummary } from "@/lib/finops/cost-anomaly-ml-prediction-client";
import {
    DEFAULT_ENSEMBLE_WEIGHTS,
    ENSEMBLE_CONSENSUS_THRESHOLD,
    type ModelType,
} from "@/lib/finops/cost-anomaly-ml-prediction-types";

interface EnsembleConsensusScorePanelProps {
    dryRun: boolean;
    periodKey: string;
}

const MODEL_LABELS: Record<ModelType, string> = {
    prophet: "Prophet",
    lstm: "LSTM",
    arima: "ARIMA",
    isolation_forest: "Isolation Forest",
    autoencoder: "Autoencoder",
};

export function EnsembleConsensusScorePanel({
    dryRun,
    periodKey,
}: EnsembleConsensusScorePanelProps) {
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    const [ensembleScore, setEnsembleScore] = useState<number>(0);
    const [modelBreakdown, setModelBreakdown] = useState<
        // eslint-disable-next-line @typescript-eslint/no-restricted-types
        Record<string, number>
    >({});
    const [consensusDetected, setConsensusDetected] = useState<boolean>(false);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        async function load() {
            setLoading(true);
            setError(null);
            try {
                const res = await fetchEnsembleSummary(periodKey);
                if (cancelled) return;
                setEnsembleScore(res.ensemble_score);
                setModelBreakdown(res.model_breakdown || {});
                setConsensusDetected(res.consensus_detected);
            } catch (err) {
                if (cancelled) return;
                setError(
                    err instanceof Error
                        ? err.message
                        : "ensemble_summary_load_failed",
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
                앙상블 합의 점수를 불러오는 중...
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

    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    const formatPercent = (v: number) => `${(v * 100).toFixed(2)}%`;

    return (
        <section
            aria-label="Ensemble consensus score"
            className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
        >
            <header className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900">
                    5-모델 앙상블 합의 점수
                </h2>
                <span
                    className={`rounded-full px-3 py-1 text-xs font-medium ${
                        consensusDetected
                            ? "bg-rose-100 text-rose-700"
                            : "bg-emerald-100 text-emerald-700"
                    }`}
                >
                    {consensusDetected ? "합의 감지" : "정상"}
                </span>
            </header>

            <div className="mt-4">
                <div className="flex items-baseline justify-between">
                    <span className="text-sm font-medium text-slate-700">
                        합의 점수 (Ensemble Score)
                    </span>
                    <span
                        className={`text-2xl font-bold ${
                            consensusDetected
                                ? "text-rose-600"
                                : "text-emerald-600"
                        }`}
                    >
                        {ensembleScore.toFixed(4)}
                    </span>
                </div>
                <div
                    className="mt-2 h-3 w-full overflow-hidden rounded-full bg-slate-200"
                    role="progressbar"
                    aria-valuenow={Math.round(ensembleScore * 100)}
                    aria-valuemin={0}
                    aria-valuemax={100}
                >
                    <div
                        className={`h-full ${
                            consensusDetected ? "bg-rose-500" : "bg-emerald-500"
                        }`}
                        style={{ width: `${Math.min(ensembleScore * 100, 100)}%` }}
                    />
                </div>
                <p className="mt-1 text-xs text-slate-500">
                    합의 임계값: {ENSEMBLE_CONSENSUS_THRESHOLD.toFixed(2)} ·{" "}
                    {dryRun ? "Dry-run preview" : "Live scoring"}
                </p>
            </div>

            <div className="mt-6">
                <h3 className="text-sm font-medium text-slate-700">
                  모델별 가중치 및 점수 (Weighted Model Breakdown)
                </h3>
                <ul className="mt-2 divide-y divide-slate-100">
                    {(Object.keys(DEFAULT_ENSEMBLE_WEIGHTS) as ModelType[]).map(
                        (modelType) => {
                            const weight = DEFAULT_ENSEMBLE_WEIGHTS[modelType];
                            const score = modelBreakdown[modelType] ?? 0;
                            const weighted = weight * score;
                            return (
                                <li
                                    key={modelType}
                                    className="flex items-center justify-between py-2 text-sm"
                                >
                                    <div className="flex items-center gap-2">
                                        <span className="w-32 font-medium text-slate-900">
                                            {MODEL_LABELS[modelType]}
                                        </span>
                                        <span className="text-xs text-slate-500">
                                            가중치 {weight.toFixed(2)}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <span className="text-xs text-slate-500">
                                            점수 {score.toFixed(4)}
                                        </span>
                                        <span className="w-20 text-right font-mono font-medium text-slate-900">
                                            {formatPercent(weighted)}
                                        </span>
                                    </div>
                                </li>
                            );
                        },
                    )}
                </ul>
            </div>
        </section>
    );
}
