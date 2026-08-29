"use client";

/**
 * ExportConfigPanel — Phase 28 T2 Export Configuration Panel sub-component.
 *
 * Epic 28 T2 frontend follow-up wire (cj-style 197번째) — PRD §F44.4
 * verbatim + AD-57 (a) verbatim. Provides 5 export format radio
 * (pdf + xlsx + csv + json + png) + max_export_size 50MB guard
 * display + 3 auto-retries indicator + 5-state status lifecycle
 * (pending + in_progress + completed + failed + cancelled).
 *
 * Capability gate: require_finops_interactive_dashboard
 * (Phase 28 capability matrix v1.53 EXTENSION).
 */

import { useEffect, useState } from "react";

import { startExportJob, getExportJobStatus } from "@/lib/finops/interactive-dashboard-client";
import {
    EXPORT_MAX_RETRIES,
    MAX_EXPORT_SIZE_BYTES,
} from "@/lib/finops/interactive-dashboard-types";
import type {
    ExportFormat,
    ExportJob,
    ExportJobStatus,
} from "@/lib/finops/interactive-dashboard-types";

interface ExportConfigPanelProps {
    dryRun: boolean;
    periodKey: string;
}

const FORMAT_OPTIONS: ReadonlyArray<{
    value: ExportFormat;
    label: string;
}> = [
    { value: "pdf", label: "PDF (재사용: Phase 17 sustainability report generator)" },
    { value: "xlsx", label: "XLSX (재사용: Phase 22 chargeback invoice generator)" },
    { value: "csv", label: "CSV" },
    { value: "json", label: "JSON" },
    { value: "png", label: "PNG" },
];

const STATUS_LABELS: Record<ExportJobStatus, string> = {
    pending: "대기 중 (pending)",
    in_progress: "진행 중 (in_progress)",
    completed: "완료 (completed)",
    failed: "실패 (failed)",
    cancelled: "취소됨 (cancelled)",
};

const STATUS_COLORS: Record<ExportJobStatus, string> = {
    pending: "bg-slate-100 text-slate-700",
    in_progress: "bg-blue-100 text-blue-700",
    completed: "bg-emerald-100 text-emerald-700",
    failed: "bg-rose-100 text-rose-700",
    cancelled: "bg-amber-100 text-amber-700",
};

export function ExportConfigPanel({
    dryRun,
    periodKey,
}: ExportConfigPanelProps) {
    const [format, setFormat] = useState<ExportFormat>("pdf");
    const [viewId, setViewId] = useState<string>("demo-view-001");
    const [job, setJob] = useState<ExportJob | null>(null);
    const [status, setStatus] = useState<ExportJobStatus | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!job?.tenant_id || !loading) return;
        const timer = setInterval(() => {
            void (async () => {
                try {
                    const fresh = await getExportJobStatus(job.tenant_id);
                    setJob(fresh);
                    setStatus((fresh as unknown as { status?: ExportJobStatus }).status ?? null);
                } catch {
                    /* noop */
                }
            })();
        }, 2000);
        return () => clearInterval(timer);
    }, [job, loading]);

    async function handleStart(): Promise<void> {
        setLoading(true);
        setError(null);
        try {
            const started = await startExportJob({
                tenant_id: "demo-tenant",
                view_id: viewId,
                format,
            });
            setJob(started);
            setStatus(
                (started as unknown as { status?: ExportJobStatus }).status ??
                    "pending"
            );
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "export_job_start_failed"
            );
        } finally {
            setLoading(false);
        }
    }

    return (
        <section
            className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
            aria-label="Export Configuration Panel"
        >
            <header className="mb-4">
                <h2 className="text-xl font-bold text-slate-900">
                    Export Configuration
                </h2>
                <p className="mt-1 text-sm text-slate-600">
                    5 export formats · max{" "}
                    {(MAX_EXPORT_SIZE_BYTES / 1_048_576).toFixed(0)} MB ·{" "}
                    {EXPORT_MAX_RETRIES} auto-retries
                    {dryRun && (
                        <span className="ml-2 rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
                            DRY-RUN
                        </span>
                    )}
                </p>
            </header>

            <fieldset className="mb-4">
                <legend className="text-sm font-medium text-slate-700">
                    Export format
                </legend>
                <div className="mt-2 space-y-1">
                    {FORMAT_OPTIONS.map((opt) => (
                        <label
                            key={opt.value}
                            className="flex items-center gap-2 text-sm"
                        >
                            <input
                                type="radio"
                                name="export-format"
                                value={opt.value}
                                checked={format === opt.value}
                                onChange={() => setFormat(opt.value)}
                                data-testid={`format-${opt.value}`}
                            />
                            {opt.label}
                        </label>
                    ))}
                </div>
            </fieldset>

            <div className="mb-4">
                <label
                    htmlFor="view-id-input"
                    className="block text-sm font-medium text-slate-700"
                >
                    Saved view ID
                </label>
                <input
                    id="view-id-input"
                    data-testid="view-id-input"
                    type="text"
                    value={viewId}
                    onChange={(e) => setViewId(e.target.value)}
                    className="mt-1 block w-full rounded border border-slate-300 px-3 py-2 text-sm"
                />
            </div>

            <div className="mb-4">
                <button
                    type="button"
                    onClick={() => void handleStart()}
                    disabled={loading}
                    className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                    data-testid="start-export"
                >
                    {loading ? "시작 중..." : "Export Job 시작"}
                </button>
            </div>

            {error && (
                <div
                    className="mb-4 rounded bg-rose-50 px-3 py-2 text-sm text-rose-700"
                    role="alert"
                >
                    Error: {error}
                </div>
            )}

            {status && (
                <div
                    className="rounded border border-slate-200 bg-slate-50 p-3"
                    data-testid="export-status"
                >
                    <div className="text-xs font-medium uppercase text-slate-500">
                        Status
                    </div>
                    <div className="mt-1">
                        <span
                            className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[status]}`}
                        >
                            {STATUS_LABELS[status]}
                        </span>
                    </div>
                    <div className="mt-2 text-xs text-slate-500">
                        5-state lifecycle: pending → in_progress → completed /
                        failed / cancelled
                    </div>
                </div>
            )}
        </section>
    );
}