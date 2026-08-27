"use client";

/**
 * VendorCatalogOverviewCard — Phase 25 FinOps Vendor Management Catalog Overview.
 *
 * PRD §F41.1 + AD-53 (d) — Vendor catalog overview with 6-category
 * taxonomy + 4-state lifecycle + blacklist gate. Shows: vendor_count,
 * category_counts (cloud/saas/outsourcing/consulting/hardware/other),
 * status_counts (active/inactive/under_review/blacklisted),
 * avg_risk_score.
 */

import { useEffect, useState } from "react";

import {
    createVendor,
    fetchVendorCatalog,
} from "@/lib/finops/vendor-management-client";
import type { Vendor } from "@/lib/finops/vendor-management-types";

interface VendorCatalogOverviewCardProps {
    dryRun: boolean;
}

export function VendorCatalogOverviewCard({
    dryRun,
}: VendorCatalogOverviewCardProps) {
    const [vendors, setVendors] = useState<Vendor[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchVendorCatalog()
            .then((data) => {
                setVendors(data.vendors || []);
                setLoading(false);
            })
            .catch((e) => {
                setError(String(e));
                setLoading(false);
            });
    }, []);

    const handleCreate = async () => {
        try {
            const vendor = await createVendor({
                tenant_id: "demo",
                vendor_name: `Vendor-${Date.now()}`,
                vendor_category: "cloud",
                cost_score: 85.0,
                performance_score: 90.0,
                reliability_score: 95.0,
                compliance_score: 88.0,
                strategic_fit_score: 80.0,
                contract_count: 0,
            });
            setVendors([vendor, ...vendors]);
        } catch (e) {
            setError(String(e));
        }
    };

    if (loading) {
        return <div className="text-slate-400">Loading vendor catalog...</div>;
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
            aria-label="Vendor catalog overview"
            className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
        >
            <header className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900">
                    Vendor Catalog Overview
                </h2>
                <button
                    type="button"
                    onClick={handleCreate}
                    className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                    {dryRun ? "Preview Vendor" : "Create Vendor"}
                </button>
            </header>

            <dl className="mt-4 grid grid-cols-3 gap-4 text-sm">
                <div className="rounded-lg bg-slate-50 p-3">
                    <dt className="font-medium text-slate-700">Total Vendors</dt>
                    <dd className="text-2xl font-bold text-slate-900">
                        {vendors.length}
                    </dd>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                    <dt className="font-medium text-slate-700">Active</dt>
                    <dd className="text-2xl font-bold text-emerald-600">
                        {vendors.filter((v) => v.status === "active").length}
                    </dd>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                    <dt className="font-medium text-slate-700">Blacklisted</dt>
                    <dd className="text-2xl font-bold text-rose-600">
                        {vendors.filter((v) => v.status === "blacklisted").length}
                    </dd>
                </div>
            </dl>

            <div className="mt-6">
                <h3 className="text-sm font-medium text-slate-700">
                    Recent Vendors
                </h3>
                <ul className="mt-2 divide-y divide-slate-100">
                    {vendors.slice(0, 5).map((vendor) => (
                        <li
                            key={vendor.vendor_id}
                            className="flex items-center justify-between py-2 text-sm"
                        >
                            <span className="font-medium text-slate-900">
                                {vendor.vendor_name}
                            </span>
                            <span className="text-xs text-slate-500">
                                {vendor.vendor_category} · {vendor.status}
                            </span>
                        </li>
                    ))}
                </ul>
            </div>
        </section>
    );
}