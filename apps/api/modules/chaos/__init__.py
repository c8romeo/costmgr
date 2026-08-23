"""apps.api.modules.chaos — Phase 9 Chaos Engineering / Game Day module.

Phase 9 (cj-style 99번째 wire) — Chaos Engineering / Game Day territory
(PRD §F25 + AD-36 (a)~(g) sub-decisions). This package provides the
backend module authority for chaos experiment definition + fault
injection types 10 categories + game day runbook + blast radius
control 5 levels + continuous chaos vs scheduled game day +
tenant-scoped + multi-region chaos + auto-rollback + safety
mechanisms 6 layers.

Submodules:
- chaos_experiment.py — ChaosExperiment TypedDict (13 fields) + 5 blast
  radius levels + 4 abort conditions + AbortCondition TypedDict + 10
  fault types registry (PRD §F25.1 verbatim).
- fault_injection.py — 10 fault types implementation: latency / error /
  resource / network partition / disk I/O / DB connection pool / cache
  failure / DNS failure / process kill / clock skew (PRD §F25.2 verbatim).
- auto_rollback.py — Auto-rollback 4 strategies + safety mechanisms
  6 layers (PRD §F25.6 verbatim).
- tenant_scoping.py — Tenant-scoped chaos + multi-region chaos
  decision helpers (PRD §F25.5 verbatim).

CR lessons applied:
- CR 0-2 RLS: every chaos experiment is scoped to a single tenant_id
  (multi-tenant isolation preserved).
- CR 1-1 audit-first INSERT: emit_audit_typed() with action_class=
  ActionClass.CHAOS_ENGINEERING BEFORE chaos experiment starts.
- CR 4-3/4-4: chaos_experiment baseline freeze pattern + tenant-scoped
  result_hash for golden_diff comparison.
- AD-22 owner-only RBAC: L3~L5 blast radius + manual abort + 2FA 챌린지
  Epic 12 정합.

Industry-agnostic per CR 12-1 L4 precedent (mirrors PERFORMANCE_TESTING
Phase 8 wire + OBSERVABILITY_* Phase 7 wire + AUDIT_LOG_RETENTION
Phase 6 wire pattern verbatim). All 4 industries get CHAOS_ENGINEERING
capability (operational resilience baseline).
"""
from __future__ import annotations

__all__ = [
    "ChaosExperiment",
    "AbortCondition",
    "BLAST_RADIUS_L1",
    "BLAST_RADIUS_L2",
    "BLAST_RADIUS_L3",
    "BLAST_RADIUS_L4",
    "BLAST_RADIUS_L5",
    "VALID_BLAST_RADII",
    "VALID_FAULT_TYPES",
    "FAULT_TYPE_LATENCY",
    "FAULT_TYPE_ERROR",
    "FAULT_TYPE_RESOURCE",
    "FAULT_TYPE_NETWORK",
    "FAULT_TYPE_DISK_IO",
    "FAULT_TYPE_DB_POOL",
    "FAULT_TYPE_CACHE",
    "FAULT_TYPE_DNS",
    "FAULT_TYPE_PROCESS",
    "FAULT_TYPE_CLOCK_SKEW",
    "INTENSITY_LOW",
    "INTENSITY_MEDIUM",
    "INTENSITY_HIGH",
    "ROLLBACK_AUTOMATIC",
    "ROLLBACK_MANUAL",
    "ROLLBACK_HYBRID",
    "ROLLBACK_SCHEDULED",
    "MAX_DURATION_SECONDS",
    "validate_chaos_experiment",
    "ChaosExperimentInvalidBlastRadiusError",
    "ChaosExperimentOwnerOnlyForbiddenError",
]
