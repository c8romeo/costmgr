"use client";

/**
 * ABTestChampionChallengerPanel — Phase 26 Cost Anomaly ML Prediction
 * A/B Testing Champion/Challenger Panel.
 *
 * Phase 26 wire (cj-style 186번째) — PRD §F42.2 + AD-55 (b) verbatim.
 * 50/50 traffic split (AB_TEST_TRAFFIC_SPLIT_DEFAULT) + 4-dim scoring
 * (precision 0.30 + recall 0.30 + F1 0.25 + AUC-ROC 0.15) + auto-promote
 * (challenger >= champion + 0.05 margin, 7-day consecutive).
 *
 * Phase 25 vendor management verbatim EXTENSION pattern.
 */

import { useEffect, useState } from "react";

import { fetchModels } from "@/lib/finops/cost-anomaly-ml-prediction-client";
import type { ModelRegistryEntry } from "@/lib/finops/cost-anomaly-ml-prediction-types";
import {
    AB_TEST_AUTO_PROMOTE_MARGIN,
    AB_TEST_TRAFFIC_SPLIT_DEFAULT,
    ML_MODEL_SCORING_WEIGHTS,
} from "@/lib/finops/cost-anomaly-ml-prediction-types";

interface ABTestChampionChallengerPanelProps {
    dryRun: boolean;
    periodKey: string;
}

export function ABTestChampionChallengerPanel({
    dryRun,
    periodKey,
}: ABTestChampionChallengerPanelProps) {
    const [models, setModels] = useState<ModelRegistryEntry[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        async function load() {
            setLoading(true);
            setError(null);
            try {
                const res = await fetchModels();
                if (cancelled) return;
                setModels(res.models || []);
            } catch (err) {
                if (cancelled) return;
                setError(
                    err instanceof Error
                        ? err.message
                        : "ab_test_panel_load_failed",
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
                A/B 테스트 데이터를 불러오는 중...
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

    // Pair each active model with itself as "challenger" view — in real
    // Phase 26 traffic_split will assign 50/50 between paired models.
    const activeModels = models.filter((m) => m.status === "active");
    const champion = activeModels[0];
    const challenger = activeModels[1] ?? activeModels[0];
    const promoteEligible =
        champion &&
        challenger &&
        Number(challenger.composite_score) >=
            Number(champion.composite_score) + AB_TEST_AUTO_PROMOTE_MARGIN;

    return (
        <section
            aria-label="A/B test champion vs challenger"
            className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
        >
            <header className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900">
                    A/B 테스트 챔피언 vs 챌린저
                </h2>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    트래픽 분할 {(AB_TEST_TRAFFIC_SPLIT_DEFAULT * 100).toFixed(0)}/
                    {(AB_TEST_TRAFFIC_SPLIT_DEFAULT * 100).toFixed(0)}
                </span>
            </header>

            <p className="mt-1 text-xs text-slate-500">
                4-차원 가중치: 정밀도 {ML_MODEL_SCORING_WEIGHTS.precision} +
                재현율 {ML_MODEL_SCORING_WEIGHTS.recall} + F1{" "}
                {ML_MODEL_SCORING_WEIGHTS.f1} + AUC-ROC{" "}
                {ML_MODEL_SCORING_WEIGHTS.auc_roc} · 자동 승격 마진{" "}
                {AB_TEST_AUTO_PROMOTE_MARGIN.toFixed(2)} (7일 연속).
            </p>

            <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                <article
                    aria-label="Champion"
                    className="rounded-lg border-2 border-emerald-300 bg-emerald-50 p-4"
                >
                    <header className="flex items-center justify-between">
                        <h3 className="text-sm font-semibold text-emerald-900">
                            챔피언 (Champion)
                        </h3>
                        <span className="rounded bg-emerald-200 px-2 py-0.5 text-xs font-medium text-emerald-800">
                            운영 중
                        </span>
                    </header>
                    {champion ? (
                        <dl className="mt-2 space-y-1 text-xs">
                            <div className="flex justify-between">
                                <dt className="text-emerald-800">모델명</dt>
                                <dd className="font-mono text-emerald-900">
                                    {champion.model_name}
                                </dd>
                            </div>
                            <div className="flex justify-between">
                                <dt className="text-emerald-800">유형</dt>
                                <dd className="font-mono text-emerald-900">
                                    {champion.model_type} · v
                                    {champion.model_version}
                                </dd>
                            </div>
                            <div className="flex justify-between">
                                <dt className="text-emerald-800">정밀도</dt>
                                <dd className="font-mono text-emerald-900">
                                    {champion.precision_score.toFixed(4)}
                                </dd>
                            </div>
                            <div className="flex justify-between">
                                <dt className="text-emerald-800">재현율</dt>
                                <dd className="font-mono text-emerald-900">
                                    {champion.recall_score.toFixed(4)}
                                </dd>
                            </div>
                            <div className="flex justify-between">
                                <dt className="text-emerald-800">F1</dt>
                                <dd className="font-mono text-emerald-900">
                                    {champion.f1_score.toFixed(4)}
                                </dd>
                            </div>
                            <div className="flex justify-between">
                                <dt className="text-emerald-800">AUC-ROC</dt>
                                <dd className="font-mono text-emerald-900">
                                    {champion.auc_roc_score.toFixed(4)}
                                </dd>
                            </div>
                            <div className="mt-2 flex justify-between border-t border-emerald-200 pt-1.5">
                                <dt className="font-semibold text-emerald-900">
                                    종합 점수
                                </dt>
                                <dd className="font-mono text-base font-bold text-emerald-900">
                                    {champion.composite_score.toFixed(4)}
                                </dd>
                            </div>
                        </dl>
                    ) : (
                        <p className="mt-2 text-xs text-emerald-800">
                            챔피언 모델이 등록되지 않았습니다.
                        </p>
                    )}
                </article>

                <article
                    aria-label="Challenger"
                    className="rounded-lg border-2 border-blue-300 bg-blue-50 p-4"
                >
                    <header className="flex items-center justify-between">
                        <h3 className="text-sm font-semibold text-blue-900">
                            챌린저 (Challenger)
                        </h3>
                        <span
                            className={`rounded px-2 py-0.5 text-xs font-medium ${
                                promoteEligible
                                    ? "bg-amber-200 text-amber-800"
                                    : "bg-blue-200 text-blue-800"
                            }`}
                        >
                            {promoteEligible ? "승격 후보" : "관찰 중"}
                        </span>
                    </header>
                    {challenger ? (
                        <dl className="mt-2 space-y-1 text-xs">
                            <div className="flex justify-between">
                                <dt className="text-blue-800">모델명</dt>
                                <dd className="font-mono text-blue-900">
                                    {challenger.model_name}
                                </dd>
                            </div>
                            <div className="flex justify-between">
                                <dt className="text-blue-800">유형</dt>
                                <dd className="font-mono text-blue-900">
                                    {challenger.model_type} · v
                                    {challenger.model_version}
                                </dd>
                            </div>
                            <div className="flex justify-between">
                                <dt className="text-blue-800">정밀도</dt>
                                <dd className="font-mono text-blue-900">
                                    {challenger.precision_score.toFixed(4)}
                                </dd>
                            </div>
                            <div className="flex justify-between">
                                <dt className="text-blue-800">재현율</dt>
                                <dd className="font-mono text-blue-900">
                                    {challenger.recall_score.toFixed(4)}
                                </dd>
                            </div>
                            <div className="flex justify-between">
                                <dt className="text-blue-800">F1</dt>
                                <dd className="font-mono text-blue-900">
                                    {challenger.f1_score.toFixed(4)}
                                </dd>
                            </div>
                            <div className="flex justify-between">
                                <dt className="text-blue-800">AUC-ROC</dt>
                                <dd className="font-mono text-blue-900">
                                    {challenger.auc_roc_score.toFixed(4)}
                                </dd>
                            </div>
                            <div className="mt-2 flex justify-between border-t border-blue-200 pt-1.5">
                                <dt className="font-semibold text-blue-900">
                                    종합 점수
                                </dt>
                                <dd className="font-mono text-base font-bold text-blue-900">
                                    {challenger.composite_score.toFixed(4)}
                                </dd>
                            </div>
                        </dl>
                    ) : (
                        <p className="mt-2 text-xs text-blue-800">
                            챌린저 모델이 등록되지 않았습니다.
                        </p>
                    )}
                </article>
            </div>

            <footer className="mt-4 rounded-lg bg-slate-50 p-3 text-xs text-slate-700">
                {dryRun ? (
                    <span>
                        <strong>Dry-run:</strong> 승격 결정은 preview 모드에서
                        시뮬레이션만 실행되며 실제 운영 모델은 변경되지 않습니다.
                    </span>
                ) : (
                    <span>
                        승격 조건: 챌린저 종합 점수 ≥ 챔피언 +{" "}
                        {AB_TEST_AUTO_PROMOTE_MARGIN.toFixed(2)} (7일 연속).
                    </span>
                )}
            </footer>
        </section>
    );
}
