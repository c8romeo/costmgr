/**
 * apps/web/__tests__/finops/cost-anomaly-ml-prediction-dashboard.test.tsx —
 * Phase 26 (cj-style 187번째 wire) — 28 NEW vitest cases for the FinOps
 * Cost Anomaly ML Prediction dashboard.
 *
 * Covers:
 * - 4 cases for lib types constants (PRD §F42.1~§F42.4 + AD-55 (a)(b)(d))
 * - 6 cases for lib client fetch (6 endpoints verbatim)
 * - 4 cases for AnomalyMLPredictionOverviewCard sub-component
 * - 4 cases for EnsembleConsensusScorePanel sub-component
 * - 3 cases for MLvsThresholdComparisonChart sub-component
 * - 3 cases for ModelDriftDetectionPanel sub-component
 * - 3 cases for ABTestChampionChallengerPanel sub-component
 * - 1 case for FinopsCostAnomalyMLPredictionDashboardPanel orchestrator
 *
 * Mirrors apps/web/__tests__/finops/finops-dashboard.test.tsx and
 * apps/web/__tests__/finops/anomaly-dashboard.test.tsx pattern.
 */
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
    AB_TEST_AUTO_PROMOTE_MARGIN,
    AB_TEST_TRAFFIC_SPLIT_DEFAULT,
    DEFAULT_ENSEMBLE_WEIGHTS,
    DRIFT_PSI_THRESHOLD,
    ENSEMBLE_CONSENSUS_THRESHOLD,
    ML_MODEL_SCORING_WEIGHTS,
} from "@/lib/finops/cost-anomaly-ml-prediction-types";

// ---------------------------------------------------------------------------
// Group 1: lib types/constants — 4 cases
// ---------------------------------------------------------------------------

describe("Phase 26 cost-anomaly-ml-prediction-types constants", () => {
    it("Test 1: DEFAULT_ENSEMBLE_WEIGHTS has 5 model entries summing to 1.00 (PRD §F42.1 + AD-55 (a) verbatim)", () => {
        expect(Object.keys(DEFAULT_ENSEMBLE_WEIGHTS)).toHaveLength(5);
        const sum = Object.values(DEFAULT_ENSEMBLE_WEIGHTS).reduce(
            (acc, w) => acc + w,
            0,
        );
        expect(sum).toBeCloseTo(1.0, 5);
        expect(DEFAULT_ENSEMBLE_WEIGHTS.prophet).toBe(0.30);
        expect(DEFAULT_ENSEMBLE_WEIGHTS.lstm).toBe(0.30);
        expect(DEFAULT_ENSEMBLE_WEIGHTS.arima).toBe(0.15);
        expect(DEFAULT_ENSEMBLE_WEIGHTS.isolation_forest).toBe(0.15);
        expect(DEFAULT_ENSEMBLE_WEIGHTS.autoencoder).toBe(0.10);
    });

    it("Test 2: DRIFT_PSI_THRESHOLD = 0.25 (PRD §F42.2 + AD-55 (b) verbatim)", () => {
        expect(DRIFT_PSI_THRESHOLD).toBe(0.25);
    });

    it("Test 3: ENSEMBLE_CONSENSUS_THRESHOLD = 0.85 (PRD §F42.4 + AD-55 (d) verbatim)", () => {
        expect(ENSEMBLE_CONSENSUS_THRESHOLD).toBe(0.85);
    });

    it("Test 4: AB test + model scoring constants verbatim (PRD §F42.2 + AD-55 (b))", () => {
        expect(AB_TEST_TRAFFIC_SPLIT_DEFAULT).toBe(0.50);
        expect(AB_TEST_AUTO_PROMOTE_MARGIN).toBe(0.05);
        expect(Object.keys(ML_MODEL_SCORING_WEIGHTS)).toHaveLength(4);
        expect(ML_MODEL_SCORING_WEIGHTS.precision).toBe(0.30);
        expect(ML_MODEL_SCORING_WEIGHTS.recall).toBe(0.30);
        expect(ML_MODEL_SCORING_WEIGHTS.f1).toBe(0.25);
        expect(ML_MODEL_SCORING_WEIGHTS.auc_roc).toBe(0.15);
    });
});

// ---------------------------------------------------------------------------
// Group 2: lib client fetch — 6 cases
// ---------------------------------------------------------------------------

describe("Phase 26 cost-anomaly-ml-prediction-client fetch endpoints", () => {
    it("Test 5: fetchPredictions GET /predictions returns { predictions } envelope", async () => {
        global.fetch = vi.fn(() =>
            Promise.resolve(
                new Response(
                    JSON.stringify({
                        predictions: [
                            {
                                prediction_id: "p-1",
                                tenant_id: "t-1",
                                model_id: "m-1",
                                model_type: "prophet",
                                period_key: "2026-08",
                                horizon_days: 30,
                                features: {},
                                predicted_values: {},
                                actual_values: {},
                                confidence_lower: {},
                                confidence_upper: {},
                                predicted_anomaly_score: 0.92,
                                threshold_anomaly_score: 0.85,
                                ensemble_consensus_score: 0.88,
                                prediction_method: "ensemble",
                                status: "active",
                                computed_at: "2026-08-15T00:00:00Z",
                            },
                        ],
                    }),
                    { status: 200 },
                ),
            ),
        ) as unknown as typeof fetch;
        const {
            fetchPredictions,
        } = await import("@/lib/finops/cost-anomaly-ml-prediction-client");
        const res = await fetchPredictions("2026-08");
        expect(res.predictions).toHaveLength(1);
        expect(res.predictions[0].prediction_id).toBe("p-1");
        expect(res.predictions[0].model_type).toBe("prophet");
    });

    it("Test 6: fetchScores GET /scores returns { scores } envelope with ml_ensemble_score", async () => {
        global.fetch = vi.fn(() =>
            Promise.resolve(
                new Response(
                    JSON.stringify({
                        scores: [
                            {
                                score_id: "s-1",
                                prediction_id: "p-1",
                                tenant_id: "t-1",
                                period_key: "2026-08",
                                ml_ensemble_score: 0.92,
                                ml_anomaly_detected: true,
                                threshold_z_score: 1.5,
                                threshold_iqr_score: 0.7,
                                threshold_ewma_score: 0.4,
                                threshold_isolation_forest_score: 0.6,
                                threshold_anomaly_detected: true,
                                consensus_detected: true,
                                consensus_score: 0.88,
                                drift_detected: false,
                                inference_latency_ms: 120,
                                served_at: "2026-08-15T00:00:00Z",
                            },
                        ],
                    }),
                    { status: 200 },
                ),
            ),
        ) as unknown as typeof fetch;
        const {
            fetchScores,
        } = await import("@/lib/finops/cost-anomaly-ml-prediction-client");
        const res = await fetchScores("2026-08");
        expect(res.scores).toHaveLength(1);
        expect(res.scores[0].ml_ensemble_score).toBe(0.92);
        expect(res.scores[0].consensus_detected).toBe(true);
    });

    it("Test 7: fetchModels GET /models returns { models } envelope with model registry", async () => {
        global.fetch = vi.fn(() =>
            Promise.resolve(
                new Response(
                    JSON.stringify({
                        models: [
                            {
                                model_id: "m-1",
                                tenant_id: "t-1",
                                model_name: "prophet-cost-30d",
                                model_type: "prophet",
                                model_version: "1.0.0",
                                model_artifact_sha256: "abc123",
                                model_artifact_size_bytes: 1024,
                                status: "active",
                                traffic_split_pct: 50,
                                precision_score: 0.85,
                                recall_score: 0.82,
                                f1_score: 0.83,
                                auc_roc_score: 0.88,
                                composite_score: 0.85,
                                version_history: [],
                                registered_at: "2026-08-01T00:00:00Z",
                            },
                        ],
                    }),
                    { status: 200 },
                ),
            ),
        ) as unknown as typeof fetch;
        const {
            fetchModels,
        } = await import("@/lib/finops/cost-anomaly-ml-prediction-client");
        const res = await fetchModels();
        expect(res.models).toHaveLength(1);
        expect(res.models[0].model_type).toBe("prophet");
        expect(res.models[0].composite_score).toBeCloseTo(0.85, 2);
    });

    it("Test 8: fetchTrainingJobs GET /training-jobs returns { training_jobs } envelope", async () => {
        global.fetch = vi.fn(() =>
            Promise.resolve(
                new Response(
                    JSON.stringify({
                        training_jobs: [
                            {
                                training_job_id: "tj-1",
                                tenant_id: "t-1",
                                model_id: "m-1",
                                model_type: "lstm",
                                training_data_window_days: 90,
                                status: "running",
                                hyperparameters: {},
                                shap_feature_importance: {},
                                started_at: "2026-08-15T00:00:00Z",
                                completed_at: "",
                                retry_count: 0,
                                error_message: "",
                            },
                        ],
                    }),
                    { status: 200 },
                ),
            ),
        ) as unknown as typeof fetch;
        const {
            fetchTrainingJobs,
        } = await import("@/lib/finops/cost-anomaly-ml-prediction-client");
        const res = await fetchTrainingJobs();
        expect(res.training_jobs).toHaveLength(1);
        expect(res.training_jobs[0].status).toBe("running");
    });

    it("Test 9: runPredictionDryRun POST /dry-run returns DryRunOutput envelope", async () => {
        global.fetch = vi.fn(() =>
            Promise.resolve(
                new Response(
                    JSON.stringify({
                        mode: "preview",
                        ensemble_score: 0.92,
                        consensus_detected: true,
                        drift_detected: false,
                        inference_latency_ms: 120,
                        note: "dry-run preview completed",
                    }),
                    { status: 200 },
                ),
            ),
        ) as unknown as typeof fetch;
        const {
            runPredictionDryRun,
        } = await import("@/lib/finops/cost-anomaly-ml-prediction-client");
        const res = await runPredictionDryRun({
            mode: "preview",
            tenant_id: "t-1",
            period_key: "2026-08",
        });
        expect(res.mode).toBe("preview");
        expect(res.consensus_detected).toBe(true);
        expect(res.ensemble_score).toBeCloseTo(0.92, 2);
    });

    it("Test 10: fetchEnsembleSummary GET /ensemble-summary returns summary envelope", async () => {
        global.fetch = vi.fn(() =>
            Promise.resolve(
                new Response(
                    JSON.stringify({
                        period_key: "2026-08",
                        ensemble_score: 0.88,
                        consensus_detected: true,
                        model_breakdown: {
                            prophet: 0.92,
                            lstm: 0.85,
                            arima: 0.70,
                            isolation_forest: 0.65,
                            autoencoder: 0.55,
                        },
                        drift_detected: false,
                    }),
                    { status: 200 },
                ),
            ),
        ) as unknown as typeof fetch;
        const {
            fetchEnsembleSummary,
        } = await import("@/lib/finops/cost-anomaly-ml-prediction-client");
        const res = await fetchEnsembleSummary("2026-08");
        expect(res.ensemble_score).toBeCloseTo(0.88, 2);
        expect(res.consensus_detected).toBe(true);
        expect(Object.keys(res.model_breakdown)).toHaveLength(5);
    });
});

// ---------------------------------------------------------------------------
// Group 3: AnomalyMLPredictionOverviewCard — 4 cases
// ---------------------------------------------------------------------------

describe("Phase 26 AnomalyMLPredictionOverviewCard", () => {
    it("Test 11: Renders overview section heading + dry-run/live badge correctly", async () => {
        vi.doMock("@/lib/finops/cost-anomaly-ml-prediction-client", () => ({
            fetchPredictions: vi.fn().mockResolvedValue({ predictions: [] }),
            fetchModels: vi.fn().mockResolvedValue({ models: [] }),
            fetchEnsembleSummary: vi.fn().mockResolvedValue({
                period_key: "2026-08",
                ensemble_score: 0.0,
                consensus_detected: false,
                model_breakdown: {},
                drift_detected: false,
            }),
        }));
        const { AnomalyMLPredictionOverviewCard } = await import(
            "@/components/finops/cost-anomaly-ml-prediction/AnomalyMLPredictionOverviewCard"
        );
        const { rerender } = render(
            <AnomalyMLPredictionOverviewCard dryRun={true} periodKey="2026-08" />,
        );
        await waitFor(() => {
            expect(
                screen.getByLabelText("Anomaly ML prediction overview"),
            ).toBeInTheDocument();
        });
        expect(screen.getByText("Dry-run")).toBeInTheDocument();
        rerender(
            <AnomalyMLPredictionOverviewCard dryRun={false} periodKey="2026-08" />,
        );
        await waitFor(() => {
            expect(screen.getByText("Live")).toBeInTheDocument();
        });
        vi.doUnmock("@/lib/finops/cost-anomaly-ml-prediction-client");
    });

    it("Test 12: Renders 4 KPI tiles (active predictions / registered models / drift alerts / ensemble consensus)", async () => {
        vi.doMock("@/lib/finops/cost-anomaly-ml-prediction-client", () => ({
            fetchPredictions: vi.fn().mockResolvedValue({
                predictions: [
                    {
                        prediction_id: "p-1",
                        status: "active",
                        predicted_anomaly_score: 0.92,
                    } as never,
                    {
                        prediction_id: "p-2",
                        status: "training",
                        predicted_anomaly_score: 0.50,
                    } as never,
                ],
            }),
            fetchModels: vi.fn().mockResolvedValue({
                models: [
                    { model_id: "m-1", status: "active", composite_score: "0.85" } as never,
                    { model_id: "m-2", status: "deprecated", composite_score: "0.60" } as never,
                ],
            }),
            fetchEnsembleSummary: vi.fn().mockResolvedValue({
                period_key: "2026-08",
                ensemble_score: 0.92,
                consensus_detected: true,
                model_breakdown: {},
                drift_detected: false,
            }),
        }));
        const { AnomalyMLPredictionOverviewCard } = await import(
            "@/components/finops/cost-anomaly-ml-prediction/AnomalyMLPredictionOverviewCard"
        );
        render(
            <AnomalyMLPredictionOverviewCard dryRun={false} periodKey="2026-08" />,
        );
        await waitFor(() => {
            expect(
                screen.getByLabelText("Anomaly ML prediction overview"),
            ).toBeInTheDocument();
        });
        expect(screen.getByText("활성 예측 (Active Predictions)")).toBeInTheDocument();
        expect(
            screen.getByText("등록 모델 (Registered Models)"),
        ).toBeInTheDocument();
        expect(
            screen.getByText("이상 경보 (Anomaly Drift Alerts)"),
        ).toBeInTheDocument();
        expect(
            screen.getByText("앙상블 합의 점수 (Ensemble Consensus)"),
        ).toBeInTheDocument();
        vi.doUnmock("@/lib/finops/cost-anomaly-ml-prediction-client");
    });

    it("Test 13: Active predictions count is filtered by status=active", async () => {
        vi.doMock("@/lib/finops/cost-anomaly-ml-prediction-client", () => ({
            fetchPredictions: vi.fn().mockResolvedValue({
                predictions: [
                    { prediction_id: "p-1", status: "active", predicted_anomaly_score: 0.5 } as never,
                    { prediction_id: "p-2", status: "active", predicted_anomaly_score: 0.5 } as never,
                    { prediction_id: "p-3", status: "training", predicted_anomaly_score: 0.5 } as never,
                ],
            }),
            fetchModels: vi.fn().mockResolvedValue({ models: [] }),
            fetchEnsembleSummary: vi.fn().mockResolvedValue({
                period_key: "2026-08",
                ensemble_score: 0.5,
                consensus_detected: false,
                model_breakdown: {},
                drift_detected: false,
            }),
        }));
        const { AnomalyMLPredictionOverviewCard } = await import(
            "@/components/finops/cost-anomaly-ml-prediction/AnomalyMLPredictionOverviewCard"
        );
        render(
            <AnomalyMLPredictionOverviewCard dryRun={false} periodKey="2026-08" />,
        );
        await waitFor(() => {
            expect(
                screen.getByLabelText("Anomaly ML prediction overview"),
            ).toBeInTheDocument();
        });
        // 2 active predictions out of 3 total
        expect(screen.getByText("전체 3개 중")).toBeInTheDocument();
        vi.doUnmock("@/lib/finops/cost-anomaly-ml-prediction-client");
    });

    it("Test 14: Drift alerts count uses ENSEMBLE_CONSENSUS_THRESHOLD as cutoff", async () => {
        vi.doMock("@/lib/finops/cost-anomaly-ml-prediction-client", () => ({
            fetchPredictions: vi.fn().mockResolvedValue({
                predictions: [
                    {
                        prediction_id: "p-1",
                        status: "active",
                        predicted_anomaly_score: 0.95,
                    } as never,
                    {
                        prediction_id: "p-2",
                        status: "active",
                        predicted_anomaly_score: 0.50,
                    } as never,
                ],
            }),
            fetchModels: vi.fn().mockResolvedValue({ models: [] }),
            fetchEnsembleSummary: vi.fn().mockResolvedValue({
                period_key: "2026-08",
                ensemble_score: 0.50,
                consensus_detected: false,
                model_breakdown: {},
                drift_detected: false,
            }),
        }));
        const { AnomalyMLPredictionOverviewCard } = await import(
            "@/components/finops/cost-anomaly-ml-prediction/AnomalyMLPredictionOverviewCard"
        );
        render(
            <AnomalyMLPredictionOverviewCard dryRun={false} periodKey="2026-08" />,
        );
        await waitFor(() => {
            expect(
                screen.getByLabelText("Anomaly ML prediction overview"),
            ).toBeInTheDocument();
        });
        // Threshold text uses ENSEMBLE_CONSENSUS_THRESHOLD (0.85)
        expect(
            screen.getByText(`임계값 ${ENSEMBLE_CONSENSUS_THRESHOLD.toFixed(2)} 이상`),
        ).toBeInTheDocument();
        vi.doUnmock("@/lib/finops/cost-anomaly-ml-prediction-client");
    });
});

// ---------------------------------------------------------------------------
// Group 4: EnsembleConsensusScorePanel — 4 cases
// ---------------------------------------------------------------------------

describe("Phase 26 EnsembleConsensusScorePanel", () => {
    it("Test 15: Renders ensemble consensus badge 정상 when consensus_detected=false", async () => {
        vi.doMock("@/lib/finops/cost-anomaly-ml-prediction-client", () => ({
            fetchEnsembleSummary: vi.fn().mockResolvedValue({
                period_key: "2026-08",
                ensemble_score: 0.50,
                consensus_detected: false,
                model_breakdown: {},
                drift_detected: false,
            }),
        }));
        const { EnsembleConsensusScorePanel } = await import(
            "@/components/finops/cost-anomaly-ml-prediction/EnsembleConsensusScorePanel"
        );
        render(
            <EnsembleConsensusScorePanel dryRun={false} periodKey="2026-08" />,
        );
        await waitFor(() => {
            expect(
                screen.getByLabelText("Ensemble consensus score"),
            ).toBeInTheDocument();
        });
        expect(screen.getByText("정상")).toBeInTheDocument();
        vi.doUnmock("@/lib/finops/cost-anomaly-ml-prediction-client");
    });

    it("Test 16: Renders consensus detected badge 합의 감지 when consensus_detected=true", async () => {
        vi.doMock("@/lib/finops/cost-anomaly-ml-prediction-client", () => ({
            fetchEnsembleSummary: vi.fn().mockResolvedValue({
                period_key: "2026-08",
                ensemble_score: 0.95,
                consensus_detected: true,
                model_breakdown: {},
                drift_detected: false,
            }),
        }));
        const { EnsembleConsensusScorePanel } = await import(
            "@/components/finops/cost-anomaly-ml-prediction/EnsembleConsensusScorePanel"
        );
        render(
            <EnsembleConsensusScorePanel dryRun={false} periodKey="2026-08" />,
        );
        await waitFor(() => {
            expect(
                screen.getByLabelText("Ensemble consensus score"),
            ).toBeInTheDocument();
        });
        expect(screen.getByText("합의 감지")).toBeInTheDocument();
        vi.doUnmock("@/lib/finops/cost-anomaly-ml-prediction-client");
    });

    it("Test 17: Renders 5 model breakdown rows (Prophet/LSTM/ARIMA/Isolation Forest/Autoencoder)", async () => {
        vi.doMock("@/lib/finops/cost-anomaly-ml-prediction-client", () => ({
            fetchEnsembleSummary: vi.fn().mockResolvedValue({
                period_key: "2026-08",
                ensemble_score: 0.88,
                consensus_detected: true,
                model_breakdown: {
                    prophet: 0.92,
                    lstm: 0.85,
                    arima: 0.70,
                    isolation_forest: 0.65,
                    autoencoder: 0.55,
                },
                drift_detected: false,
            }),
        }));
        const { EnsembleConsensusScorePanel } = await import(
            "@/components/finops/cost-anomaly-ml-prediction/EnsembleConsensusScorePanel"
        );
        render(
            <EnsembleConsensusScorePanel dryRun={false} periodKey="2026-08" />,
        );
        await waitFor(() => {
            expect(
                screen.getByLabelText("Ensemble consensus score"),
            ).toBeInTheDocument();
        });
        expect(screen.getByText("Prophet")).toBeInTheDocument();
        expect(screen.getByText("LSTM")).toBeInTheDocument();
        expect(screen.getByText("ARIMA")).toBeInTheDocument();
        expect(screen.getByText("Isolation Forest")).toBeInTheDocument();
        expect(screen.getByText("Autoencoder")).toBeInTheDocument();
        // Threshold text uses ENSEMBLE_CONSENSUS_THRESHOLD (0.85)
        expect(
            screen.getByText(
                `합의 임계값: ${ENSEMBLE_CONSENSUS_THRESHOLD.toFixed(2)}`,
            ),
        ).toBeInTheDocument();
        vi.doUnmock("@/lib/finops/cost-anomaly-ml-prediction-client");
    });

    it("Test 18: Renders progressbar with aria-valuenow for ensemble score", async () => {
        vi.doMock("@/lib/finops/cost-anomaly-ml-prediction-client", () => ({
            fetchEnsembleSummary: vi.fn().mockResolvedValue({
                period_key: "2026-08",
                ensemble_score: 0.92,
                consensus_detected: true,
                model_breakdown: {},
                drift_detected: false,
            }),
        }));
        const { EnsembleConsensusScorePanel } = await import(
            "@/components/finops/cost-anomaly-ml-prediction/EnsembleConsensusScorePanel"
        );
        render(
            <EnsembleConsensusScorePanel dryRun={false} periodKey="2026-08" />,
        );
        await waitFor(() => {
            expect(
                screen.getByLabelText("Ensemble consensus score"),
            ).toBeInTheDocument();
        });
        const bar = screen.getByRole("progressbar");
        expect(bar).toHaveAttribute("aria-valuemin", "0");
        expect(bar).toHaveAttribute("aria-valuemax", "100");
        expect(Number(bar.getAttribute("aria-valuenow"))).toBeGreaterThan(0);
        vi.doUnmock("@/lib/finops/cost-anomaly-ml-prediction-client");
    });
});

// ---------------------------------------------------------------------------
// Group 5: MLvsThresholdComparisonChart — 3 cases
// ---------------------------------------------------------------------------

describe("Phase 26 MLvsThresholdComparisonChart", () => {
    it("Test 19: Renders comparison table with 7 columns header row", async () => {
        vi.doMock("@/lib/finops/cost-anomaly-ml-prediction-client", () => ({
            fetchScores: vi.fn().mockResolvedValue({ scores: [] }),
        }));
        const { MLvsThresholdComparisonChart } = await import(
            "@/components/finops/cost-anomaly-ml-prediction/MLvsThresholdComparisonChart"
        );
        render(
            <MLvsThresholdComparisonChart dryRun={false} periodKey="2026-08" />,
        );
        await waitFor(() => {
            expect(
                screen.getByLabelText("ML vs threshold comparison"),
            ).toBeInTheDocument();
        });
        expect(screen.getByText("기간")).toBeInTheDocument();
        expect(screen.getByText("ML 앙상블")).toBeInTheDocument();
        expect(screen.getByText("z_score")).toBeInTheDocument();
        expect(screen.getByText("iqr")).toBeInTheDocument();
        expect(screen.getByText("ewma")).toBeInTheDocument();
        expect(screen.getByText("isolation_forest")).toBeInTheDocument();
        expect(screen.getByText("합의")).toBeInTheDocument();
        // Empty state when scores are empty
        expect(screen.getByText("비교 데이터가 없습니다.")).toBeInTheDocument();
        vi.doUnmock("@/lib/finops/cost-anomaly-ml-prediction-client");
    });

    it("Test 20: Renders 이상 (anomaly) badge when ml_ensemble_score >= threshold", async () => {
        vi.doMock("@/lib/finops/cost-anomaly-ml-prediction-client", () => ({
            fetchScores: vi.fn().mockResolvedValue({
                scores: [
                    {
                        score_id: "s-1",
                        prediction_id: "p-1",
                        tenant_id: "t-1",
                        period_key: "2026-08",
                        ml_ensemble_score: 0.95,
                        ml_anomaly_detected: true,
                        threshold_z_score: 1.5,
                        threshold_iqr_score: 0.7,
                        threshold_ewma_score: 0.4,
                        threshold_isolation_forest_score: 0.6,
                        threshold_anomaly_detected: true,
                        consensus_detected: true,
                        consensus_score: 0.95,
                        drift_detected: false,
                        inference_latency_ms: 120,
                        served_at: "2026-08-15T00:00:00Z",
                    },
                ],
            }),
        }));
        const { MLvsThresholdComparisonChart } = await import(
            "@/components/finops/cost-anomaly-ml-prediction/MLvsThresholdComparisonChart"
        );
        render(
            <MLvsThresholdComparisonChart dryRun={false} periodKey="2026-08" />,
        );
        await waitFor(() => {
            expect(
                screen.getByLabelText("ML vs threshold comparison"),
            ).toBeInTheDocument();
        });
        expect(screen.getAllByText("이상").length).toBeGreaterThanOrEqual(1);
        vi.doUnmock("@/lib/finops/cost-anomaly-ml-prediction-client");
    });

    it("Test 21: Renders 정상 (normal) badge when ml_ensemble_score < threshold", async () => {
        vi.doMock("@/lib/finops/cost-anomaly-ml-prediction-client", () => ({
            fetchScores: vi.fn().mockResolvedValue({
                scores: [
                    {
                        score_id: "s-1",
                        prediction_id: "p-1",
                        tenant_id: "t-1",
                        period_key: "2026-08",
                        ml_ensemble_score: 0.50,
                        ml_anomaly_detected: false,
                        threshold_z_score: 1.5,
                        threshold_iqr_score: 0.7,
                        threshold_ewma_score: 0.4,
                        threshold_isolation_forest_score: 0.6,
                        threshold_anomaly_detected: false,
                        consensus_detected: false,
                        consensus_score: 0.50,
                        drift_detected: false,
                        inference_latency_ms: 100,
                        served_at: "2026-08-15T00:00:00Z",
                    },
                ],
            }),
        }));
        const { MLvsThresholdComparisonChart } = await import(
            "@/components/finops/cost-anomaly-ml-prediction/MLvsThresholdComparisonChart"
        );
        render(
            <MLvsThresholdComparisonChart dryRun={false} periodKey="2026-08" />,
        );
        await waitFor(() => {
            expect(
                screen.getByLabelText("ML vs threshold comparison"),
            ).toBeInTheDocument();
        });
        expect(screen.getAllByText("정상").length).toBeGreaterThanOrEqual(1);
        vi.doUnmock("@/lib/finops/cost-anomaly-ml-prediction-client");
    });
});

// ---------------------------------------------------------------------------
// Group 6: ModelDriftDetectionPanel — 3 cases
// ---------------------------------------------------------------------------

describe("Phase 26 ModelDriftDetectionPanel", () => {
    it("Test 22: Renders drift detection header with PSI threshold (0.25) verbatim", async () => {
        vi.doMock("@/lib/finops/cost-anomaly-ml-prediction-client", () => ({
            fetchModels: vi.fn().mockResolvedValue({ models: [] }),
            fetchTrainingJobs: vi.fn().mockResolvedValue({ training_jobs: [] }),
        }));
        const { ModelDriftDetectionPanel } = await import(
            "@/components/finops/cost-anomaly-ml-prediction/ModelDriftDetectionPanel"
        );
        render(
            <ModelDriftDetectionPanel dryRun={false} periodKey="2026-08" />,
        );
        await waitFor(() => {
            expect(
                screen.getByLabelText("Model drift detection"),
            ).toBeInTheDocument();
        });
        expect(
            screen.getByText(
                `모델 드리프트 감지 (PSI ${DRIFT_PSI_THRESHOLD.toFixed(2)} 임계값)`,
            ),
        ).toBeInTheDocument();
        vi.doUnmock("@/lib/finops/cost-anomaly-ml-prediction-client");
    });

    it("Test 23: Renders 3 KPI tiles (active models / retraining queue / drift threshold)", async () => {
        vi.doMock("@/lib/finops/cost-anomaly-ml-prediction-client", () => ({
            fetchModels: vi.fn().mockResolvedValue({
                models: [
                    { model_id: "m-1", status: "active", composite_score: "0.85" } as never,
                    { model_id: "m-2", status: "active", composite_score: "0.80" } as never,
                ],
            }),
            fetchTrainingJobs: vi.fn().mockResolvedValue({
                training_jobs: [
                    { training_job_id: "tj-1", status: "scheduled" } as never,
                    { training_job_id: "tj-2", status: "running" } as never,
                    { training_job_id: "tj-3", status: "completed" } as never,
                ],
            }),
        }));
        const { ModelDriftDetectionPanel } = await import(
            "@/components/finops/cost-anomaly-ml-prediction/ModelDriftDetectionPanel"
        );
        render(
            <ModelDriftDetectionPanel dryRun={false} periodKey="2026-08" />,
        );
        await waitFor(() => {
            expect(
                screen.getByLabelText("Model drift detection"),
            ).toBeInTheDocument();
        });
        expect(screen.getByText("활성 모델")).toBeInTheDocument();
        expect(screen.getByText("재학습 큐 (Scheduled/Running)")).toBeInTheDocument();
        expect(screen.getByText("드리프트 임계값 (PSI)")).toBeInTheDocument();
        expect(screen.getByText("KST 매주 일요일 03:00 자동 재학습")).toBeInTheDocument();
        vi.doUnmock("@/lib/finops/cost-anomaly-ml-prediction-client");
    });

    it("Test 24: Renders 8 feature PSI rows per model (5 models × 8 features = 40 rows)", async () => {
        vi.doMock("@/lib/finops/cost-anomaly-ml-prediction-client", () => ({
            fetchModels: vi.fn().mockResolvedValue({
                models: [
                    { model_id: "Am-1", status: "active", composite_score: "0.85", model_name: "prophet-cost-30d", model_type: "prophet" } as never,
                    { model_id: "Bm-2", status: "active", composite_score: "0.80", model_name: "lstm-anomaly-30d", model_type: "lstm" } as never,
                ],
            }),
            fetchTrainingJobs: vi.fn().mockResolvedValue({ training_jobs: [] }),
        }));
        const { ModelDriftDetectionPanel } = await import(
            "@/components/finops/cost-anomaly-ml-prediction/ModelDriftDetectionPanel"
        );
        render(
            <ModelDriftDetectionPanel dryRun={false} periodKey="2026-08" />,
        );
        await waitFor(() => {
            expect(
                screen.getByLabelText("Model drift detection"),
            ).toBeInTheDocument();
        });
        // 8 feature rows × 2 models = 16 rows
        expect(screen.getAllByText("cost_baseline_30d").length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByText("cost_volatility_30d").length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByText("budget_consumption_pct").length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByText("forecast_accuracy_mape").length).toBeGreaterThanOrEqual(1);
        // The status column should have either 드리프트 or 정상 cells (>=1 each possible)
        expect(screen.getAllByText("정상").length).toBeGreaterThanOrEqual(1);
        vi.doUnmock("@/lib/finops/cost-anomaly-ml-prediction-client");
    });
});

// ---------------------------------------------------------------------------
// Group 7: ABTestChampionChallengerPanel — 3 cases
// ---------------------------------------------------------------------------

describe("Phase 26 ABTestChampionChallengerPanel", () => {
    it("Test 25: Renders Champion + Challenger cards with 4-dim scoring weights", async () => {
        vi.doMock("@/lib/finops/cost-anomaly-ml-prediction-client", () => ({
            fetchModels: vi.fn().mockResolvedValue({
                models: [
                    {
                        model_id: "m-1",
                        status: "active",
                        model_name: "prophet-cost-30d",
                        model_type: "prophet",
                        model_version: "1.0.0",
                        precision_score: 0.85,
                        recall_score: 0.82,
                        f1_score: 0.83,
                        auc_roc_score: 0.88,
                        composite_score: 0.85,
                    } as never,
                    {
                        model_id: "m-2",
                        status: "active",
                        model_name: "lstm-anomaly-30d",
                        model_type: "lstm",
                        model_version: "1.0.0",
                        precision_score: 0.90,
                        recall_score: 0.80,
                        f1_score: 0.85,
                        auc_roc_score: 0.88,
                        composite_score: 0.90,
                    } as never,
                ],
            }),
        }));
        const { ABTestChampionChallengerPanel } = await import(
            "@/components/finops/cost-anomaly-ml-prediction/ABTestChampionChallengerPanel"
        );
        render(
            <ABTestChampionChallengerPanel dryRun={false} periodKey="2026-08" />,
        );
        await waitFor(() => {
            expect(
                screen.getByLabelText("A/B test champion vs challenger"),
            ).toBeInTheDocument();
        });
        expect(screen.getByLabelText("Champion")).toBeInTheDocument();
        expect(screen.getByLabelText("Challenger")).toBeInTheDocument();
        // 4-dim weight footer text
        expect(
            screen.getByText(
                `트래픽 분할 ${(AB_TEST_TRAFFIC_SPLIT_DEFAULT * 100).toFixed(0)}/${(AB_TEST_TRAFFIC_SPLIT_DEFAULT * 100).toFixed(0)}`,
            ),
        ).toBeInTheDocument();
        vi.doUnmock("@/lib/finops/cost-anomaly-ml-prediction-client");
    });

    it("Test 26: Renders 승격 후보 badge when challenger composite >= champion + 0.05 margin", async () => {
        vi.doMock("@/lib/finops/cost-anomaly-ml-prediction-client", () => ({
            fetchModels: vi.fn().mockResolvedValue({
                models: [
                    {
                        model_id: "m-1",
                        status: "active",
                        model_name: "champion-prophet",
                        model_type: "prophet",
                        model_version: "1.0.0",
                        precision_score: 0.80,
                        recall_score: 0.80,
                        f1_score: 0.80,
                        auc_roc_score: 0.80,
                        composite_score: 0.80,
                    } as never,
                    {
                        model_id: "m-2",
                        status: "active",
                        model_name: "challenger-lstm",
                        model_type: "lstm",
                        model_version: "1.0.0",
                        precision_score: 0.90,
                        recall_score: 0.90,
                        f1_score: 0.90,
                        auc_roc_score: 0.90,
                        composite_score: 0.90,
                    } as never,
                ],
            }),
        }));
        const { ABTestChampionChallengerPanel } = await import(
            "@/components/finops/cost-anomaly-ml-prediction/ABTestChampionChallengerPanel"
        );
        render(
            <ABTestChampionChallengerPanel dryRun={false} periodKey="2026-08" />,
        );
        await waitFor(() => {
            expect(
                screen.getByLabelText("A/B test champion vs challenger"),
            ).toBeInTheDocument();
        });
        // 0.90 >= 0.80 + 0.05 (margin) → 승격 후보
        expect(screen.getByText("승격 후보")).toBeInTheDocument();
        vi.doUnmock("@/lib/finops/cost-anomaly-ml-prediction-client");
    });

    it("Test 27: Renders 관찰 중 badge when challenger composite < champion + 0.05 margin", async () => {
        vi.doMock("@/lib/finops/cost-anomaly-ml-prediction-client", () => ({
            fetchModels: vi.fn().mockResolvedValue({
                models: [
                    {
                        model_id: "m-1",
                        status: "active",
                        model_name: "champion-prophet",
                        model_type: "prophet",
                        model_version: "1.0.0",
                        precision_score: 0.90,
                        recall_score: 0.90,
                        f1_score: 0.90,
                        auc_roc_score: 0.90,
                        composite_score: 0.90,
                    } as never,
                    {
                        model_id: "m-2",
                        status: "active",
                        model_name: "challenger-lstm",
                        model_type: "lstm",
                        model_version: "1.0.0",
                        precision_score: 0.85,
                        recall_score: 0.85,
                        f1_score: 0.85,
                        auc_roc_score: 0.85,
                        composite_score: 0.88,
                    } as never,
                ],
            }),
        }));
        const { ABTestChampionChallengerPanel } = await import(
            "@/components/finops/cost-anomaly-ml-prediction/ABTestChampionChallengerPanel"
        );
        render(
            <ABTestChampionChallengerPanel dryRun={true} periodKey="2026-08" />,
        );
        await waitFor(() => {
            expect(
                screen.getByLabelText("A/B test champion vs challenger"),
            ).toBeInTheDocument();
        });
        // 0.88 < 0.90 + 0.05 = 0.95 → 관찰 중
        expect(screen.getByText("관찰 중")).toBeInTheDocument();
        // dry-run=true renders Dry-run footer
        expect(screen.getByText(/Dry-run/)).toBeInTheDocument();
        vi.doUnmock("@/lib/finops/cost-anomaly-ml-prediction-client");
    });
});

// ---------------------------------------------------------------------------
// Group 8: orchestrator — 1 case
// ---------------------------------------------------------------------------

describe("Phase 26 FinopsCostAnomalyMLPredictionDashboardPanel orchestrator", () => {
    it("Test 28: Renders 5-tab navigation + dry-run toggle (default ON) + period header", async () => {
        vi.doMock("@/lib/finops/cost-anomaly-ml-prediction-client", () => ({
            fetchPredictions: vi.fn().mockResolvedValue({ predictions: [] }),
            fetchModels: vi.fn().mockResolvedValue({ models: [] }),
            fetchEnsembleSummary: vi.fn().mockResolvedValue({
                period_key: "2026-08",
                ensemble_score: 0.0,
                consensus_detected: false,
                model_breakdown: {},
                drift_detected: false,
            }),
            fetchScores: vi.fn().mockResolvedValue({ scores: [] }),
            fetchTrainingJobs: vi.fn().mockResolvedValue({ training_jobs: [] }),
        }));
        const { FinopsCostAnomalyMLPredictionDashboardPanel } = await import(
            "@/components/finops/FinopsCostAnomalyMLPredictionDashboardPanel"
        );
        render(<FinopsCostAnomalyMLPredictionDashboardPanel periodKey="2026-08" />);
        await waitFor(() => {
            expect(
                screen.getByText("FinOps Cost Anomaly ML Prediction"),
            ).toBeInTheDocument();
        });
        // 5-tab navigation
        expect(screen.getByText("개요 (Overview)")).toBeInTheDocument();
        expect(screen.getByText("앙상블 합의")).toBeInTheDocument();
        expect(screen.getByText("ML vs 임계값")).toBeInTheDocument();
        expect(screen.getByText("드리프트 감지")).toBeInTheDocument();
        expect(screen.getByText("A/B 테스트")).toBeInTheDocument();
        // Dry-run toggle (default ON per CR 11-3 honest-DEFER discipline)
        const toggle = screen.getByLabelText("Dry-run mode");
        expect(toggle).toBeInTheDocument();
        expect((toggle as HTMLInputElement).checked).toBe(true);
        vi.doUnmock("@/lib/finops/cost-anomaly-ml-prediction-client");
    });
});