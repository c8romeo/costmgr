/**
 * finops-tag-governance-client — Phase 15 FinOps Tag Governance TS mirror.
 *
 * Phase 15 (cj-style 123번째 wire) — CR 12-5 D-PARITY-01 Python
 * TypedDict ↔ TypeScript interface parity. Mirrors apps/api/modules/
 * finops/tag_policy_dsl.py + untagged_resource_detector.py +
 * allocation_rules_engine.py + allocation_audit.py +
 * chargeback_allocation_reconciliation.py TypedDict definitions.
 */

// ── TagPolicy ──
export interface TagPolicy {
  policy_id: string;
  tenant_id: string;
  resource_type: "ec2" | "rds" | "s3" | "lambda" | "eks" | "vpc";
  tag_key: string;
  enforcement_level:
    | "required"
    | "recommended"
    | "optional"
    | "blocked";
  default_value: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  compliance_threshold_pct: number;
  remediation_action:
    | "notify_only"
    | "auto_remediate"
    | "block_provisioning";
  status: "active" | "paused" | "expired";
  created_at: string;
  updated_at: string;
  trace_id: string;
}

// ── UntaggedResource ──
export interface UntaggedResource {
  detection_id: string;
  tenant_id: string;
  resource_id: string;
  resource_arn: string;
  resource_type: "ec2" | "rds" | "s3" | "lambda" | "eks" | "vpc";
  untagged_tags: string[];
  detection_window: "7d" | "30d" | "90d";
  detection_method: "z_score" | "threshold" | "heuristic";
  severity: "low" | "medium" | "high" | "critical";
  action_recommendation:
    | "notify_only"
    | "auto_remediate"
    | "block_provisioning"
    | "manual_review";
  detected_at: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  remediation_sla_hours: number;
  trace_id: string;
}

// ── AllocationRule ──
export interface AllocationRule {
  rule_id: string;
  tenant_id: string;
  rule_type:
    | "tag_match"
    | "percentage_split"
    | "weighted"
    | "conditional"
    | "fallback";
  scope_resource_types: string[];
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  precedence: number;
  parameters: Record<string, unknown>;
  effective_from: string;
  effective_to: string;
  audit_required: boolean;
  status: "active" | "paused" | "expired" | "draft";
  created_at: string;
  updated_at: string;
  trace_id: string;
}

// ── ComplianceReport ──
export interface ComplianceReport {
  report_id: string;
  tenant_id: string;
  report_type:
    | "tag_policy_compliance"
    | "untagged_resource_summary"
    | "allocation_rule_audit"
    | "chargeback_reconciliation";
  period_start: string;
  period_end: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  total_resources_scanned: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  compliant_resources: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  non_compliant_resources: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  compliance_pct: number;
  status: "ok" | "warning" | "breach" | "remediating";
  export_format: "csv" | "pdf" | "json";
  trace_id: string;
}

// ── Reconciliation ──
export interface Reconciliation {
  reconciliation_id: string;
  tenant_id: string;
  strategy: "chargeback_only" | "tag_allocation_only" | "hybrid_blended";
  period_start: string;
  period_end: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  chargeback_amount_usd: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  tag_allocation_amount_usd: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  variance_amount_usd: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  variance_pct: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  delta_threshold_pct: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  auto_approve_below_pct: number;
  status: "pending" | "investigating" | "approved" | "resolved";
  trace_id: string;
}

// ── Error class (CR 12-5 D-GATE-01) ──
export class FinopsTagGovernanceApiError extends Error {
  constructor(
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "FinopsTagGovernanceApiError";
  }
}

// ── API client functions ──
export async function fetchTagPolicies(
  resourceType?: string,
): Promise<TagPolicy[]> {
  const params = resourceType
    ? `?resource_type=${encodeURIComponent(resourceType)}`
    : "";
  const response = await fetch(
    `/api/v1/admin/finops/tag-governance/policies${params}`,
    { credentials: "include" },
  );
  if (!response.ok) {
    throw new FinopsTagGovernanceApiError(
      response.status,
      "TAG_POLICY_FETCH_FAILED",
      `태그 정책 조회 실패: ${response.statusText}`,
    );
  }
  return response.json() as Promise<TagPolicy[]>;
}

export async function fetchUntaggedResources(
  detectionWindow?: string,
): Promise<UntaggedResource[]> {
  const params = detectionWindow
    ? `?detection_window=${encodeURIComponent(detectionWindow)}`
    : "";
  const response = await fetch(
    `/api/v1/admin/finops/tag-governance/untagged-resources${params}`,
    { credentials: "include" },
  );
  if (!response.ok) {
    throw new FinopsTagGovernanceApiError(
      response.status,
      "UNTAGGED_RESOURCE_FETCH_FAILED",
      `언태그드 리소스 조회 실패: ${response.statusText}`,
    );
  }
  return response.json() as Promise<UntaggedResource[]>;
}

export async function fetchAllocationRules(): Promise<AllocationRule[]> {
  const response = await fetch(
    "/api/v1/admin/finops/tag-governance/allocation-rules",
    { credentials: "include" },
  );
  if (!response.ok) {
    throw new FinopsTagGovernanceApiError(
      response.status,
      "ALLOCATION_RULE_FETCH_FAILED",
      `할당 규칙 조회 실패: ${response.statusText}`,
    );
  }
  return response.json() as Promise<AllocationRule[]>;
}

export async function fetchComplianceReports(
  reportType?: string,
): Promise<ComplianceReport[]> {
  const params = reportType
    ? `?report_type=${encodeURIComponent(reportType)}`
    : "";
  const response = await fetch(
    `/api/v1/admin/finops/tag-governance/compliance-reports${params}`,
    { credentials: "include" },
  );
  if (!response.ok) {
    throw new FinopsTagGovernanceApiError(
      response.status,
      "COMPLIANCE_REPORT_FETCH_FAILED",
      `컴플라이언스 보고서 조회 실패: ${response.statusText}`,
    );
  }
  return response.json() as Promise<ComplianceReport[]>;
}

export async function fetchReconciliations(): Promise<Reconciliation[]> {
  const response = await fetch(
    "/api/v1/admin/finops/allocation/reconciliations",
    { credentials: "include" },
  );
  if (!response.ok) {
    throw new FinopsTagGovernanceApiError(
      response.status,
      "RECONCILIATION_FETCH_FAILED",
      `정산 조회 실패: ${response.statusText}`,
    );
  }
  return response.json() as Promise<Reconciliation[]>;
}