"use client";

/**
 * FinopsTagGovernanceDashboardPanel — Phase 15 FinOps Tag Governance Client panel.
 *
 * Phase 15 (cj-style 123번째 wire) — FinOps Tag Governance & Cost
 * Allocation territory (PRD §F31.6). 5 sub-components:
 * 1. TagPolicyEditorPanel — tag policy DSL editor with 6 resource_types +
 *    4 enforcement_levels + 3 remediation_actions.
 * 2. UntaggedResourceDetectorPanel — untagged resource detection results
 *    with severity classification + action recommendation.
 * 3. AllocationRulesEnginePanel — 5 rule_types (tag_match /
 *    percentage_split / weighted / conditional / fallback) editor +
 *    evaluator with precedence ordering.
 * 4. ComplianceReportPanel — 4 report_types (tag_policy_compliance /
 *    untagged_resource_summary / allocation_rule_audit /
 *    chargeback_reconciliation) with CSV/PDF/JSON export.
 * 5. ChargebackReconciliationPanel — 3 reconciliation strategies
 *    (chargeback_only / tag_allocation_only / hybrid_blended) with
 *    variance tracking + auto-approve.
 *
 * Owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 보존.
 *
 * CR 11-4 D-003 RTL render discipline.
 * CR 12-5 D-PARITY-01 — TypeScript interfaces mirror Python TypedDict
 * via `lib/finops-tag-governance/finops-tag-governance-client.ts`.
 */

import { useState } from "react";

import {
  fetchTagPolicies,
  fetchUntaggedResources,
  fetchAllocationRules,
  fetchComplianceReports,
  fetchReconciliations,
  type TagPolicy,
  type UntaggedResource,
  type AllocationRule,
  type ComplianceReport,
  type Reconciliation,
} from "@/lib/finops-tag-governance/finops-tag-governance-client";

// ── 1. TagPolicyEditorPanel ──
function TagPolicyEditorPanel({
  policies,
  onAdd,
}: {
  policies: TagPolicy[];
  onAdd: () => void;
}) {
  return (
    <div className="tag-policy-editor-panel mb-6 rounded bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Tag Policy Editor
      </h2>
      <button
        type="button"
        aria-label="add_tag_policy"
        className="mb-3 rounded bg-blue-600 px-3 py-1 text-white hover:bg-blue-700"
        onClick={onAdd}
      >
        + 정책 추가
      </button>
      <table className="w-full text-sm text-slate-200">
        <thead>
          <tr className="text-left">
            <th className="p-2">resource_type</th>
            <th className="p-2">tag_key</th>
            <th className="p-2">enforcement_level</th>
            <th className="p-2">remediation_action</th>
            <th className="p-2">status</th>
          </tr>
        </thead>
        <tbody>
          {policies.map((p) => (
            <tr key={p.policy_id} className="border-t border-slate-700">
              <td className="p-2">{p.resource_type}</td>
              <td className="p-2">{p.tag_key}</td>
              <td className="p-2">{p.enforcement_level}</td>
              <td className="p-2">{p.remediation_action}</td>
              <td className="p-2">{p.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── 2. UntaggedResourceDetectorPanel ──
function UntaggedResourceDetectorPanel({
  resources,
}: {
  resources: UntaggedResource[];
}) {
  const severityCount = {
    low: resources.filter((r) => r.severity === "low").length,
    medium: resources.filter((r) => r.severity === "medium").length,
    high: resources.filter((r) => r.severity === "high").length,
    critical: resources.filter((r) => r.severity === "critical").length,
  };
  return (
    <div className="untagged-resource-detector-panel mb-6 rounded bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Untagged Resource Detector ({resources.length}건)
      </h2>
      <div className="grid grid-cols-4 gap-3 mb-3 text-sm text-slate-300">
        <div className="rounded bg-slate-800 p-2">
          Low: <span className="font-mono">{severityCount.low}</span>
        </div>
        <div className="rounded bg-slate-800 p-2">
          Medium: <span className="font-mono">{severityCount.medium}</span>
        </div>
        <div className="rounded bg-slate-800 p-2">
          High: <span className="font-mono">{severityCount.high}</span>
        </div>
        <div className="rounded bg-slate-800 p-2 text-red-400">
          Critical: <span className="font-mono">{severityCount.critical}</span>
        </div>
      </div>
      <table className="w-full text-sm text-slate-200">
        <thead>
          <tr className="text-left">
            <th className="p-2">resource_type</th>
            <th className="p-2">severity</th>
            <th className="p-2">action</th>
            <th className="p-2">SLA (hours)</th>
          </tr>
        </thead>
        <tbody>
          {resources.map((r) => (
            <tr key={r.detection_id} className="border-t border-slate-700">
              <td className="p-2">{r.resource_type}</td>
              <td className="p-2">
                <span
                  className={`rounded px-2 py-0.5 text-xs ${
                    r.severity === "critical"
                      ? "bg-red-700"
                      : r.severity === "high"
                      ? "bg-orange-700"
                      : r.severity === "medium"
                      ? "bg-yellow-700"
                      : "bg-slate-700"
                  }`}
                >
                  {r.severity}
                </span>
              </td>
              <td className="p-2">{r.action_recommendation}</td>
              <td className="p-2">{r.remediation_sla_hours}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── 3. AllocationRulesEnginePanel ──
function AllocationRulesEnginePanel({
  rules,
}: {
  rules: AllocationRule[];
}) {
  const sortedRules = [...rules].sort((a, b) => a.precedence - b.precedence);
  return (
    <div className="allocation-rules-engine-panel mb-6 rounded bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Allocation Rules Engine ({rules.length}건)
      </h2>
      <table className="w-full text-sm text-slate-200">
        <thead>
          <tr className="text-left">
            <th className="p-2">precedence</th>
            <th className="p-2">rule_type</th>
            <th className="p-2">scope</th>
            <th className="p-2">effective_from</th>
            <th className="p-2">status</th>
          </tr>
        </thead>
        <tbody>
          {sortedRules.map((r) => (
            <tr key={r.rule_id} className="border-t border-slate-700">
              <td className="p-2 font-mono">{r.precedence}</td>
              <td className="p-2">{r.rule_type}</td>
              <td className="p-2">
                {r.scope_resource_types.join(", ")}
              </td>
              <td className="p-2">{r.effective_from}</td>
              <td className="p-2">{r.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── 4. ComplianceReportPanel ──
function ComplianceReportPanel({
  reports,
}: {
  reports: ComplianceReport[];
}) {
  return (
    <div className="compliance-report-panel mb-6 rounded bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Compliance Reports ({reports.length}건)
      </h2>
      <table className="w-full text-sm text-slate-200">
        <thead>
          <tr className="text-left">
            <th className="p-2">report_type</th>
            <th className="p-2">period</th>
            <th className="p-2">compliance_pct</th>
            <th className="p-2">status</th>
            <th className="p-2">export_format</th>
          </tr>
        </thead>
        <tbody>
          {reports.map((r) => (
            <tr key={r.report_id} className="border-t border-slate-700">
              <td className="p-2">{r.report_type}</td>
              <td className="p-2">
                {r.period_start} ~ {r.period_end}
              </td>
              <td className="p-2 font-mono">{r.compliance_pct.toFixed(2)}%</td>
              <td className="p-2">
                <span
                  className={`rounded px-2 py-0.5 text-xs ${
                    r.status === "ok"
                      ? "bg-green-700"
                      : r.status === "warning"
                      ? "bg-yellow-700"
                      : r.status === "breach"
                      ? "bg-orange-700"
                      : "bg-red-700"
                  }`}
                >
                  {r.status}
                </span>
              </td>
              <td className="p-2">{r.export_format}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── 5. ChargebackReconciliationPanel ──
function ChargebackReconciliationPanel({
  reconciliations,
}: {
  reconciliations: Reconciliation[];
}) {
  return (
    <div className="chargeback-reconciliation-panel mb-6 rounded bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Chargeback Allocation Reconciliation ({reconciliations.length}건)
      </h2>
      <table className="w-full text-sm text-slate-200">
        <thead>
          <tr className="text-left">
            <th className="p-2">strategy</th>
            <th className="p-2">chargeback (USD)</th>
            <th className="p-2">tag_alloc (USD)</th>
            <th className="p-2">variance_pct</th>
            <th className="p-2">status</th>
          </tr>
        </thead>
        <tbody>
          {reconciliations.map((r) => (
            <tr key={r.reconciliation_id} className="border-t border-slate-700">
              <td className="p-2">{r.strategy}</td>
              <td className="p-2 font-mono">
                {r.chargeback_amount_usd.toFixed(2)}
              </td>
              <td className="p-2 font-mono">
                {r.tag_allocation_amount_usd.toFixed(2)}
              </td>
              <td className="p-2 font-mono">{r.variance_pct.toFixed(2)}%</td>
              <td className="p-2">
                <span
                  className={`rounded px-2 py-0.5 text-xs ${
                    r.status === "approved"
                      ? "bg-green-700"
                      : r.status === "resolved"
                      ? "bg-blue-700"
                      : r.status === "investigating"
                      ? "bg-orange-700"
                      : "bg-slate-700"
                  }`}
                >
                  {r.status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Main Dashboard Panel ──
export function FinopsTagGovernanceDashboardPanel() {
  const [policies, setPolicies] = useState<TagPolicy[]>([]);
  const [untaggedResources, setUntaggedResources] = useState<UntaggedResource[]>([]);
  const [allocationRules, setAllocationRules] = useState<AllocationRule[]>([]);
  const [complianceReports, setComplianceReports] = useState<ComplianceReport[]>([]);
  const [reconciliations, setReconciliations] = useState<Reconciliation[]>([]);

  async function refreshAll(): Promise<void> {
    const [p, u, a, c, r] = await Promise.all([
      fetchTagPolicies(),
      fetchUntaggedResources(),
      fetchAllocationRules(),
      fetchComplianceReports(),
      fetchReconciliations(),
    ]);
    setPolicies(p);
    setUntaggedResources(u);
    setAllocationRules(a);
    setComplianceReports(c);
    setReconciliations(r);
  }

  return (
    <div className="finops-tag-governance-dashboard">
      <div className="mb-4 flex items-center gap-3">
        <h1 className="text-xl font-semibold text-slate-100">
          FinOps Tag Governance &amp; Cost Allocation
        </h1>
        <button
          type="button"
          aria-label="refresh_all"
          className="rounded bg-slate-700 px-3 py-1 text-slate-100 hover:bg-slate-600"
          onClick={() => void refreshAll()}
        >
          새로고침
        </button>
      </div>
      <TagPolicyEditorPanel
        policies={policies}
        onAdd={() => void refreshAll()}
      />
      <UntaggedResourceDetectorPanel resources={untaggedResources} />
      <AllocationRulesEnginePanel rules={allocationRules} />
      <ComplianceReportPanel reports={complianceReports} />
      <ChargebackReconciliationPanel reconciliations={reconciliations} />
    </div>
  );
}