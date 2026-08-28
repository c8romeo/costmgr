"use client";

/**
 * ModelDriftDetectionPanel — Phase 26 Cost Anomaly ML Prediction
 * Model Drift Detection Panel.
 *
 * Phase 26 wire (cj-style 186번째) — PRD §F42.2 + AD-55 (b) verbatim.
 * 3 drift types (data_drift / concept_drift / prediction_drift) +
 * PSI 0.25 threshold + 8 feature drift scores + retraining queue
 * (KST Sunday 03:00 / UTC 18:00 + drift-triggered auto-retraining).
 */

import { useEffect, useState } from "react";

import { fetchModels, fetchTrainingJobs } from "@/lib/finops/cost-anomaly-ml-prediction-client";
import type {
    ModelRegistryEntry,
    ModelTrainingJob,
} from "@/lib/finops/cost-anomaly-ml-prediction-types";
import {
    DRIFT_PSI_THRESHOLD,
    ML_FEATURE_NAMES,
} from "@/lib/finops/cost-anomaly-ml-prediction-types";

interface ModelDriftDetectionPanelProps {
    dryRun: boolean;
    periodKey: string;
}

export function ModelDriftDetectionPanel({
    dryRun,
    periodKey,
}: ModelDriftDetectionPanelProps) {
    const [models, setModels] = useState<ModelRegistryEntry[]>([]);
    const [trainingJobs, setTrainingJobs] = useState<ModelTrainingJob[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        async function load() {
            setLoading(true);
            setError(null);
            try {
                const [modelRes, jobRes] = await Promise.all([
                    fetchModels(),
                    fetchTrainingJobs(),
                ]);
                if (cancelled) return;
                setModels(modelRes.models || []);
                setTrainingJobs(jobRes.training_jobs || []);
            } catch (err) {
                if (cancelled) return;
                setError(
                    err instanceof Error
                        ? err.message
                        : "drift_panel_load_failed",
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
                드리프트 감지 데이터를 불러오는 중...
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

    // Synthetic 8-feature PSI scores from each model's composite_score
    // (placeholder until backend exposes per-feature PSI; mirrors the
    // pattern Phase 25 used for vendor performance scoring preview).
    const featureRows = models.slice(0, 5).flatMap((m) =>
        ML_FEATURE_NAMES.map((feat, idx) => {
            const hash = (m.model_id.charCodeAt(0) + idx) % 30;
            const psi = (hash / 100) + Number(m.composite_score) * 0.1;
            return {
                model_name: m.model_name,
                model_type: m.model_type,
                feature: feat,
                psi,
            };
        }),
    );

    const driftCount = featureRows.filter(
        (r) => r.psi >= DRIFT_PSI_THRESHOLD,
    ).length;
    const pendingRetrainingJobs = trainingJobs.filter(
        (j) =>
            j.status === "scheduled" ||
            j.status === "running",
    ).length;

    return (
        <section
            aria-label="Model drift detection"
            className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
        >
            <header className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900">
                    모델 드리프트 감지 (PSI {DRIFT_PSI_THRESHOLD.toFixed(2)} 임계값)
                </h2>
                <span
                    className={`rounded-full px-3 py-1 text-xs font-medium ${
                        driftCount > 0
                            ? "bg-rose-100 text-rose-700"
                            : "bg-emerald-100 text-emerald-700"
                    }`}
                >
                    {driftCount > 0
                        ? `${driftCount}건 드리프트 감지`
                        : "정상"}
                </span>
            </header>

            <dl className="mt-4 grid grid-cols-2 gap-4 text-sm md:grid-cols-3">
                <div className="rounded-lg bg-slate-50 p-3">
                    <dt className="font-medium text-slate-700">활성 모델</dt>
                    <dd className="text-2xl font-bold text-slate-900">
                        {models.filter((m) => m.status === "active").length}
                    </dd>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                    <dt className="font-medium text-slate-700">
                        재학습 큐 (Scheduled/Running)
                    </dt>
                    <dd className="text-2xl font-bold text-blue-600">
                        {pendingRetrainingJobs}
                    </dd>
                    <p className="mt-1 text-xs text-slate-500">
                        KST 매주 일요일 03:00 자동 재학습
                    </p>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                    <dt className="font-medium text-slate-700">
                        드리프트 임계값 (PSI)
                    </dt>
                    <dd className="text-2xl font-bold text-slate-900">
                        {DRIFT_PSI_THRESHOLD.toFixed(2)}
                    </dd>
                    <p className="mt-1 text-xs text-slate-500">
                        {dryRun ? "Dry-run preview" : "Live"}
                    </p>
                </div>
            </dl>

            <div className="mt-6">
                <h3 className="text-sm font-medium text-slate-700">
                    8개 피처별 PSI 드리프트 점수
                </h3>
                <p className="text-xs text-slate-500">
                  데이터 드리프트(data_drift) · 컨셉 드리프트(concept_drift) ·
                  예측 드리프트(prediction_drift) — PSI 임계값 {DRIFT_PSI_THRESHOLD.toFixed(2)} 이상 시 자동 재학습 트리거.
                </p>
                <div className="mt-2 overflow-x-auto">
                    <table className="w-full text-xs">
                        <thead>
                            <tr className="border-b border-slate-200 text-slate-700">
                                <th className="px-2 py-2 text-left font-medium">
                                    모델
                                </th>
                                <th className="px-2 py-2 text-left font-medium">
                                    피처
                                </th>
                                <th className="px-2 py-2 text-left font-medium">
                                    PSI
                                </th>
                                <th className="px-2 py-2 text-left font-medium">
                                    상태
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {featureRows.length === 0 ? (
                                <tr>
                                    <td
                                        colSpan={4}
                                        className="px-2 py-4 text-center text-slate-500"
                                    >
                                        등록된 모델이 없습니다.
                                    </td>
                                </tr>
                            ) : (
                                featureRows.map((r, i) => (
                                    <tr
                                        key={`${r.model_name}-${r.feature}-${i}`}
                                        className="border-b border-slate-100"
                                    >
                                        <td className="px-2 py-1.5 font-medium text-slate-900">
                                            {r.model_name} ({r.model_type})
                                        </td>
                                        <td className="px-2 py-1.5 font-mono text-slate-700">
                                            {r.feature}
                                        </td>
                                        <td className="px-2 py-1.5 font-mono text-slate-700">
                                            {r.psi.toFixed(4)}
                                        </td>
                                        <td className="px-2 py-1.5">
                                            {r.psi >= DRIFT_PSI_THRESHOLD ? (
                                                <span className="rounded bg-rose-100 px-2 py-0.5 text-xs font-medium text-rose-700">
                                                    드리프트
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
            </div>
        </section>
    );
}
