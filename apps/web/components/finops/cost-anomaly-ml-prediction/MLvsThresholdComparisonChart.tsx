"use client";

/**
 * MLvsThresholdComparisonChart — Phase 26 Cost Anomaly ML Prediction
 * ML vs Phase 12 Threshold Comparison Chart.
 *
 * Phase 26 wire (cj-style 186번째) — PRD §F42.4 + AD-55 (d) verbatim.
 * Bar/area chart comparing ML ensemble score (Phase 26 pre-detection)
 * vs Phase 12 rule-based threshold scores (z_score / iqr / ewma /
 * isolation_forest) over a period range.
 *
 * Complementary ledger: Phase 26 ML-driven pre-detection + Phase 12
 * rule-based 사후 detection.
 */

import { useEffect, useMemo, useState } from "react";

import { fetchScores } from "@/lib/finops/cost-anomaly-ml-prediction-client";
import type { AnomalyMLScoreResult } from "@/lib/finops/cost-anomaly-ml-prediction-types";
import { ENSEMBLE_CONSENSUS_THRESHOLD } from "@/lib/finops/cost-anomaly-ml-prediction-types";

interface MLvsThresholdComparisonChartProps {
    dryRun: boolean;
    periodKey: string;
}

interface ScoreRow {
    period: string;
    ml: number;
    z: number;
    iqr: number;
    ewma: number;
    iso: number;
}

const MAX_BAR_HEIGHT_PX = 200;

export function MLvsThresholdComparisonChart({
    dryRun,
    periodKey,
}: MLvsThresholdComparisonChartProps) {
    const [scores, setScores] = useState<AnomalyMLScoreResult[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        async function load() {
            setLoading(true);
            setError(null);
            try {
                const res = await fetchScores(periodKey);
                if (cancelled) return;
                setScores(res.scores || []);
            } catch (err) {
                if (cancelled) return;
                setError(
                    err instanceof Error
                        ? err.message
                        : "scores_load_failed",
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

    const rows: ScoreRow[] = useMemo(() => {
        return scores.slice(0, 12).map((s) => ({
            period: s.period_key,
            ml: s.ml_ensemble_score,
            z: s.threshold_z_score,
            iqr: s.threshold_iqr_score,
            ewma: s.threshold_ewma_score,
            iso: s.threshold_isolation_forest_score,
        }));
    }, [scores]);

    if (loading) {
        return (
            <div className="text-slate-400">
                ML vs 임계값 비교 데이터를 불러오는 중...
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

    return (
        <section
            aria-label="ML vs threshold comparison"
            className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
        >
            <header className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900">
                    ML 예측 vs Phase 12 임계값 비교
                </h2>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    {dryRun ? "Dry-run" : "Live"}
                </span>
            </header>

            <p className="mt-1 text-xs text-slate-500">
                5-모델 앙상블 ML 점수와 Phase 12 4-방식(z_score / iqr / ewma /
                isolation_forest) 임계값 점수 비교. 합의 임계값{" "}
                {ENSEMBLE_CONSENSUS_THRESHOLD.toFixed(2)} 이상 시 이상탐지
                사전경보 발송.
            </p>

            <div className="mt-4 overflow-x-auto">
                <table className="w-full text-xs">
                    <thead>
                        <tr className="border-b border-slate-200 text-slate-700">
                            <th className="px-2 py-2 text-left font-medium">
                                기간
                            </th>
                            <th className="px-2 py-2 text-left font-medium">
                                ML 앙상블
                            </th>
                            <th className="px-2 py-2 text-left font-medium">
                                z_score
                            </th>
                            <th className="px-2 py-2 text-left font-medium">
                                iqr
                            </th>
                            <th className="px-2 py-2 text-left font-medium">
                                ewma
                            </th>
                            <th className="px-2 py-2 text-left font-medium">
                                isolation_forest
                            </th>
                            <th className="px-2 py-2 text-left font-medium">
                                합의
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows.length === 0 ? (
                            <tr>
                                <td
                                    colSpan={7}
                                    className="px-2 py-4 text-center text-slate-500"
                                >
                                    비교 데이터가 없습니다.
                                </td>
                            </tr>
                        ) : (
                            rows.map((row) => (
                                <tr
                                    key={row.period}
                                    className="border-b border-slate-100"
                                >
                                    <td className="px-2 py-2 font-mono text-slate-700">
                                        {row.period}
                                    </td>
                                    {(
                                        [
                                            { label: "ml", value: row.ml },
                                            { label: "z", value: row.z },
                                            { label: "iqr", value: row.iqr },
                                            { label: "ewma", value: row.ewma },
                                            { label: "iso", value: row.iso },
                                        ] as const
                                    ).map(({ label, value }) => (
                                        <td
                                            key={label}
                                            className="px-2 py-2"
                                        >
                                            <div className="flex items-center gap-1">
                                                <div
                                                    className={`h-2 rounded-full ${
                                                        value >=
                                                        ENSEMBLE_CONSENSUS_THRESHOLD
                                                            ? "bg-rose-500"
                                                            : "bg-emerald-500"
                                                    }`}
                                                    style={{
                                                        width: `${Math.min(
                                                            value *
                                                                MAX_BAR_HEIGHT_PX,
                                                            MAX_BAR_HEIGHT_PX,
                                                        )}px`,
                                                        maxWidth: `${MAX_BAR_HEIGHT_PX}px`,
                                                    }}
                                                />
                                                <span className="font-mono text-slate-700">
                                                    {value.toFixed(3)}
                                                </span>
                                            </div>
                                        </td>
                                    ))}
                                    <td className="px-2 py-2">
                                        {row.ml >=
                                        ENSEMBLE_CONSENSUS_THRESHOLD ? (
                                            <span className="rounded bg-rose-100 px-2 py-0.5 text-xs font-medium text-rose-700">
                                                이상
                                            </span>
                                        ) : (
                                            <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
                                                정상
                                            </span>
                                        )}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </section>
    );
}
