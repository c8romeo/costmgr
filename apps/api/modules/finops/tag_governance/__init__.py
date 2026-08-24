"""apps.api.modules.finops.tag_governance — FinOps Tag Governance & Cost Allocation territory.

Phase 15 (cj-style 123번째 wire) — FinOps Tag Governance & Cost
Allocation territory (PRD §F31.1~§F31.8 + AD-42 (a)~(g) 7 sub-decisions).

This subpackage provides:
- `serializers` — m23_finops_tag_governance.tag_governance_serializers
  module version SSOT (CR 12-5 D-PARITY-01 Python ↔ TypeScript mirror).

CR lessons applied:
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity verification (verifiable via apps/web/lib/finops-tag-governance/
  finops-tag-governance-client.ts).
- CR 11-4 P-015 — pure validator pattern.

AD-42 FinOps Tag Governance & Cost Allocation 신규 (Phase 15) —
7 sub-decisions (a)~(g):
(a) TagPolicy DSL schema + 6 resource_types + 4 enforcement_levels +
    tag_key validation + audit-first INSERT `tag_policy_updated`.
(b) UntaggedResource detector — 6 resource_types parallel run + Phase 14
    idle_resource_detector EXTENSION.
(c) AllocationRule engine — 5 rule_types (tag_match / percentage_split /
    weighted / conditional / fallback) + rule precedence.
(d) ComplianceReport + audit + 3 NEW audit actions (compliance_report_
    generated + compliance_alert_sent + compliance_remediation_initiated).
(e) ChargebackAllocationReconciliation — 3 reconciliation strategy +
    variance calculation + 5 NEW audit actions (reconciliation_initiated +
    reconciliation_report_generated + reconciliation_investigation_
    triggered + reconciliation_approved + reconciliation_resolved).
(f) Owner-only RBAC AD-22 + Epic 12 2FA 챌린지 mandatory.
(g) L4 industry-agnostic capability FINOPS_TAG_GOVERNANCE with
    4-industry grants ✅/✅/✅/✅ (CR 12-1 verbatim pattern).
"""
from __future__ import annotations

from apps.api.modules.finops.tag_governance.serializers import (
    m23_finops_tag_governance,
    tag_governance_deserialize,
    tag_governance_serializers,
)

__all__ = [
    "m23_finops_tag_governance",
    "tag_governance_serializers",
    "tag_governance_deserialize",
]