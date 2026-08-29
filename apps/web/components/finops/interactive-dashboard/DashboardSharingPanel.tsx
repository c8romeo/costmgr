"use client";

/**
 * DashboardSharingPanel — Phase 28 T2 Dashboard Sharing Panel sub-component.
 *
 * Epic 28 T2 frontend follow-up wire (cj-style 197번째) — PRD §F44.5
 * verbatim + AD-57 (a) verbatim. Provides 4 sharing scope radio
 * (private + tenant + tenant_owner + cross_tenant) + RBAC:
 * only tenant_owner can grant `cross_tenant` scope + sharing expires
 * default 30 days + Epic 12 2FA 챌린지 mandatory for high-value grants.
 *
 * Capability gate: require_finops_interactive_dashboard
 * (Phase 28 capability matrix v1.53 EXTENSION).
 */

import { useState } from "react";

import { shareDashboard } from "@/lib/finops/interactive-dashboard-client";
import {
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    SHARING_EXPIRES_DEFAULT_DAYS,
} from "@/lib/finops/interactive-dashboard-types";
import type { DashboardSharingScope } from "@/lib/finops/interactive-dashboard-types";

interface DashboardSharingPanelProps {
    dryRun: boolean;
    periodKey: string;
    isOwner: boolean;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    impactKrwPerYear: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    savedViewCount: number;
}

const SCOPE_OPTIONS: ReadonlyArray<{
    value: DashboardSharingScope;
    label: string;
    description: string;
    ownerOnly: boolean;
}> = [
    {
        value: "private",
        label: "Private (본인만)",
        description: "Sharing 비활성",
        ownerOnly: false,
    },
    {
        value: "tenant",
        label: "Tenant (테넌트 전체)",
        description: "테넌트 내 모든 사용자 접근 가능",
        ownerOnly: false,
    },
    {
        value: "tenant_owner",
        label: "Tenant Owner",
        description: "테넌트 owner + executive viewer",
        ownerOnly: false,
    },
    {
        value: "cross_tenant",
        label: "Cross-Tenant",
        description: "다른 테넌트로 공유 (owner-only RBAC)",
        ownerOnly: true,
    },
];

export function DashboardSharingPanel({
    dryRun,
    periodKey,
    isOwner,
    impactKrwPerYear,
    savedViewCount,
}: DashboardSharingPanelProps) {
    const [scope, setScope] = useState<DashboardSharingScope>("private");
    const [viewId, setViewId] = useState<string>("demo-view-001");
    const [grantedToUserId, setGrantedToUserId] =
        useState<string>("demo-grantee");
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const isHighValue =
        scope === "cross_tenant" ||
        savedViewCount >= 100 ||
        impactKrwPerYear >= HIGH_VALUE_THRESHOLD_KRW_PER_YEAR;
    const requires2FA = isHighValue;
    const requiresOwner = scope === "cross_tenant" && !isOwner;

    async function handleShare(): Promise<void> {
        setError(null);
        setSuccess(null);
        if (requiresOwner) {
            setError(
                "DashboardSharingScopeError: cross_tenant sharing requires tenant_owner role (AD-22 owner-only RBAC)."
            );
            return;
        }
        if (requires2FA) {
            setError(
                "InteractiveDashboardSharing2FARequiredError: 2FA 챌린지 필요 (Epic 12 mandatory). RFC 6238 TOTP 인증 후 재시도."
            );
            return;
        }
        try {
            await shareDashboard({
                tenant_id: "demo-tenant",
                view_id: viewId,
                scope,
                granted_to_user_id: grantedToUserId,
            });
            setSuccess(
                `Sharing grant created (scope=${scope}, expires in ${SHARING_EXPIRES_DEFAULT_DAYS} days).`
            );
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "dashboard_sharing_failed"
            );
        }
    }

    return (
        <section
            className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
            aria-label="Dashboard Sharing Panel"
        >
            <header className="mb-4">
                <h2 className="text-xl font-bold text-slate-900">
                    Dashboard Sharing
                </h2>
                <p className="mt-1 text-sm text-slate-600">
                    4 sharing scopes · expires default{" "}
                    {SHARING_EXPIRES_DEFAULT_DAYS} days · tenant isolation
                    {dryRun && (
                        <span className="ml-2 rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
                            DRY-RUN
                        </span>
                    )}
                </p>
            </header>

            <fieldset className="mb-4">
                <legend className="text-sm font-medium text-slate-700">
                    Sharing scope
                </legend>
                <div className="mt-2 space-y-2">
                    {SCOPE_OPTIONS.map((opt) => {
                        const disabled = opt.ownerOnly && !isOwner;
                        return (
                            <label
                                key={opt.value}
                                className={`flex items-start gap-2 text-sm ${
                                    disabled ? "opacity-50" : ""
                                }`}
                                data-testid={`scope-${opt.value}`}
                            >
                                <input
                                    type="radio"
                                    name="sharing-scope"
                                    value={opt.value}
                                    checked={scope === opt.value}
                                    disabled={disabled}
                                    onChange={() => setScope(opt.value)}
                                />
                                <span>
                                    <span className="font-medium">
                                        {opt.label}
                                    </span>
                                    <span className="ml-2 text-xs text-slate-500">
                                        {opt.description}
                                    </span>
                                    {opt.ownerOnly && !isOwner && (
                                        <span className="ml-2 rounded bg-rose-100 px-1.5 py-0.5 text-xs font-medium text-rose-700">
                                            owner-only
                                        </span>
                                    )}
                                </span>
                            </label>
                        );
                    })}
                </div>
            </fieldset>

            <div className="mb-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                    <label
                        htmlFor="share-view-id"
                        className="block text-sm font-medium text-slate-700"
                    >
                        Saved view ID
                    </label>
                    <input
                        id="share-view-id"
                        data-testid="share-view-id"
                        type="text"
                        value={viewId}
                        onChange={(e) => setViewId(e.target.value)}
                        className="mt-1 block w-full rounded border border-slate-300 px-3 py-2 text-sm"
                    />
                </div>
                <div>
                    <label
                        htmlFor="granted-to-user-id"
                        className="block text-sm font-medium text-slate-700"
                    >
                        Granted to user ID
                    </label>
                    <input
                        id="granted-to-user-id"
                        data-testid="granted-to-user-id"
                        type="text"
                        value={grantedToUserId}
                        onChange={(e) =>
                            setGrantedToUserId(e.target.value)
                        }
                        className="mt-1 block w-full rounded border border-slate-300 px-3 py-2 text-sm"
                    />
                </div>
            </div>

            {isHighValue && (
                <div
                    className="mb-4 rounded bg-amber-50 px-3 py-2 text-sm text-amber-800"
                    data-testid="two-fa-required-notice"
                    role="alert"
                >
                    <strong>2FA 챌린지 mandatory:</strong> 공유 scope가
                    high-value 임계값(
                    {HIGH_VALUE_THRESHOLD_KRW_PER_YEAR.toLocaleString(
                        "ko-KR"
                    )}{" "}
                    KRW/년) 이상이거나 saved view 100개 이상입니다. Epic 12
                    RFC 6238 TOTP 인증이 필요합니다.
                </div>
            )}

            <div className="mb-4">
                <button
                    type="button"
                    onClick={() => void handleShare()}
                    className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                    data-testid="share-dashboard"
                >
                    Sharing Grant 생성
                </button>
            </div>

            {error && (
                <div
                    className="mb-4 rounded bg-rose-50 px-3 py-2 text-sm text-rose-700"
                    role="alert"
                    data-testid="share-error"
                >
                    {error}
                </div>
            )}

            {success && (
                <div
                    className="rounded bg-emerald-50 px-3 py-2 text-sm text-emerald-700"
                    data-testid="share-success"
                >
                    {success}
                </div>
            )}

            <footer className="mt-4 text-xs text-slate-400">
                period_key={periodKey} · saved_views={savedViewCount} ·{" "}
                impact≈{impactKrwPerYear.toLocaleString("ko-KR")} KRW/년
            </footer>
        </section>
    );
}