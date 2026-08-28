"use client";

/**
 * SavedViewManager — Phase 28 T2 Saved View Manager sub-component.
 *
 * Epic 28 T2 frontend follow-up wire (cj-style 197번째) — PRD §F44.2
 * verbatim + AD-57 (a) verbatim. Provides 5 CRUD UI
 * (create / read / update / delete / execute) for the 12 pre-defined
 * view templates + 7-dim granularity selector (minute/hour/day/week/
 * month/quarter/year).
 *
 * Capability gate: require_finops_interactive_dashboard
 * (Phase 28 capability matrix v1.53 EXTENSION).
 */

import { useEffect, useState } from "react";

import {
    createSavedView,
    deleteSavedView,
    executeSavedView,
    listPredefinedTemplates,
    readSavedView,
    updateSavedView,
} from "@/lib/finops/interactive-dashboard-client";
import {
    MAX_SAVED_VIEWS_PER_TENANT,
    PREDEFINED_VIEW_TEMPLATES,
} from "@/lib/finops/interactive-dashboard-types";
import type {
    DrillDownGranularity,
    SavedView,
} from "@/lib/finops/interactive-dashboard-types";

interface SavedViewManagerProps {
    dryRun: boolean;
    periodKey: string;
}

const GRANULARITY_OPTIONS: ReadonlyArray<{
    value: DrillDownGranularity;
    label: string;
}> = [
    { value: "minute", label: "분 (minute)" },
    { value: "hour", label: "시간 (hour)" },
    { value: "day", label: "일 (day)" },
    { value: "week", label: "주 (week)" },
    { value: "month", label: "월 (month)" },
    { value: "quarter", label: "분기 (quarter)" },
    { value: "year", label: "년 (year)" },
];

export function SavedViewManager({
    dryRun,
    periodKey,
}: SavedViewManagerProps) {
    const [templates, setTemplates] = useState<string[]>([]);
    const [savedViews, setSavedViews] = useState<SavedView[]>([]);
    const [selectedTemplate, setSelectedTemplate] = useState<string>(
        PREDEFINED_VIEW_TEMPLATES[0]
    );
    const [selectedGranularity, setSelectedGranularity] =
        useState<DrillDownGranularity>("month");
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        async function load() {
            setLoading(true);
            setError(null);
            try {
                const list = await listPredefinedTemplates();
                if (cancelled) return;
                setTemplates(list);
                setSavedViews([]);
            } catch (err) {
                if (cancelled) return;
                setError(
                    err instanceof Error
                        ? err.message
                        : "saved_view_load_failed"
                );
            } finally {
                if (!cancelled) setLoading(false);
            }
        }
        void load();
        return () => {
            cancelled = true;
        };
    }, []);

    async function handleCreate(): Promise<void> {
        try {
            const created = await createSavedView({
                tenant_id: "demo-tenant",
                view_config: {
                    template_id: selectedTemplate,
                    granularity: selectedGranularity,
                },
                template_id: selectedTemplate,
                view_name: `${selectedTemplate} (${selectedGranularity})`,
                created_by_user_id: "demo-user",
            });
            setSavedViews((prev) => [...prev, created]);
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "saved_view_create_failed"
            );
        }
    }

    async function handleRead(viewId: string): Promise<void> {
        try {
            const view = await readSavedView(viewId, "demo-tenant");
            setSavedViews((prev) =>
                prev.map((v) => (v.saved_view_id === viewId ? view : v))
            );
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "saved_view_read_failed"
            );
        }
    }

    async function handleUpdate(viewId: string): Promise<void> {
        try {
            const updated = await updateSavedView(viewId, {
                tenant_id: "demo-tenant",
                view_name: `${selectedTemplate} (updated)`,
            });
            setSavedViews((prev) =>
                prev.map((v) =>
                    v.saved_view_id === viewId ? updated : v
                )
            );
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "saved_view_update_failed"
            );
        }
    }

    async function handleDelete(viewId: string): Promise<void> {
        try {
            await deleteSavedView(viewId, "demo-tenant");
            setSavedViews((prev) =>
                prev.filter((v) => v.saved_view_id !== viewId)
            );
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "saved_view_delete_failed"
            );
        }
    }

    async function handleExecute(viewId: string): Promise<void> {
        try {
            await executeSavedView(viewId, {
                tenant_id: "demo-tenant",
                period_key: periodKey,
            });
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "saved_view_execute_failed"
            );
        }
    }

    if (loading) {
        return (
            <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                <div className="text-slate-400">
                    Saved View 템플릿을 불러오는 중...
                </div>
            </section>
        );
    }

    return (
        <section
            className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
            aria-label="Saved View Manager"
        >
            <header className="mb-4">
                <h2 className="text-xl font-bold text-slate-900">
                    Saved View Manager
                </h2>
                <p className="mt-1 text-sm text-slate-600">
                    {templates.length} pre-defined view templates · max{" "}
                    {MAX_SAVED_VIEWS_PER_TENANT} views/tenant
                    {dryRun && (
                        <span className="ml-2 rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
                            DRY-RUN
                        </span>
                    )}
                </p>
            </header>

            <div className="mb-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                    <label
                        htmlFor="template-select"
                        className="block text-sm font-medium text-slate-700"
                    >
                        Pre-defined view template
                    </label>
                    <select
                        id="template-select"
                        data-testid="template-select"
                        value={selectedTemplate}
                        onChange={(e) =>
                            setSelectedTemplate(e.target.value)
                        }
                        className="mt-1 block w-full rounded border border-slate-300 px-3 py-2 text-sm"
                    >
                        {(templates.length > 0
                            ? templates
                            : PREDEFINED_VIEW_TEMPLATES
                        ).map((tpl) => (
                            <option key={tpl} value={tpl}>
                                {tpl}
                            </option>
                        ))}
                    </select>
                </div>
                <div>
                    <label
                        htmlFor="granularity-select"
                        className="block text-sm font-medium text-slate-700"
                    >
                        Granularity
                    </label>
                    <select
                        id="granularity-select"
                        data-testid="granularity-select"
                        value={selectedGranularity}
                        onChange={(e) =>
                            setSelectedGranularity(
                                e.target.value as DrillDownGranularity
                            )
                        }
                        className="mt-1 block w-full rounded border border-slate-300 px-3 py-2 text-sm"
                    >
                        {GRANULARITY_OPTIONS.map((g) => (
                            <option key={g.value} value={g.value}>
                                {g.label}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            <div className="mb-4">
                <button
                    type="button"
                    onClick={() => void handleCreate()}
                    className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                    data-testid="create-saved-view"
                >
                    새 Saved View 생성
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

            {savedViews.length > 0 && (
                <table
                    className="w-full text-sm"
                    aria-label="Saved views table"
                >
                    <thead>
                        <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-500">
                            <th className="py-2">View Name</th>
                            <th className="py-2">Template</th>
                            <th className="py-2">Granularity</th>
                            <th className="py-2 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {savedViews.map((view) => (
                            <tr
                                key={view.saved_view_id}
                                className="border-b border-slate-100"
                            >
                                <td className="py-2">{view.view_name}</td>
                                <td className="py-2">
                                    {view.template_id ?? "—"}
                                </td>
                                <td className="py-2">—</td>
                                <td className="space-x-1 py-2 text-right">
                                    <button
                                        type="button"
                                        onClick={() =>
                                            void handleRead(view.saved_view_id)
                                        }
                                        className="rounded border border-slate-300 px-2 py-1 text-xs"
                                    >
                                        Read
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() =>
                                            void handleUpdate(
                                                view.saved_view_id
                                            )
                                        }
                                        className="rounded border border-slate-300 px-2 py-1 text-xs"
                                    >
                                        Update
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() =>
                                            void handleExecute(
                                                view.saved_view_id
                                            )
                                        }
                                        className="rounded border border-slate-300 px-2 py-1 text-xs"
                                    >
                                        Execute
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() =>
                                            void handleDelete(
                                                view.saved_view_id
                                            )
                                        }
                                        className="rounded border border-rose-300 px-2 py-1 text-xs text-rose-700"
                                    >
                                        Delete
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </section>
    );
}