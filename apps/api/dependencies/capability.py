"""
apps/api/dependencies/capability.py — FastAPI dependency helpers for capability gates.

Epic 17 (cj-style 82번째 epic 연속 정직 회복 wire) — T6 (AC #6.3) — F21.6.

Re-exports `require_capability` from `apps.api.core.capability` plus
Epic-15/16/17-specific named dependencies:

Epic 15:
  - `require_launch_landing()` — gates `/api/v1/launch/landing` (1st release)
  - `require_launch_tos()` — gates `/api/v1/launch/tos-acceptance` (1st release)
  - `require_launch_support()` — gates `/api/v1/launch/support-tickets` (1st release)
  - `require_launch_monitoring()` — gates `/api/v1/launch/*` (1st release)

Epic 16:
  - `require_tenant_idp_management()` — gates `/api/v1/admin/tenant/{slug}/idp`

Epic 17:
  - `require_audit_log_view()` — gates `/api/v1/audit-log[/...]` + `/audit-log/export`

Phase 6:
  - `require_audit_log_retention()` — gates `/api/v1/audit-log/retention[/...]` + `/audit-log/erase`

Industry-agnostic (all 4 industries get these), CR 12-1 L4 precedent.
"""
from __future__ import annotations

from apps.api.core.capability import (
    Capability,
    require_capability,
)

# Re-export the canonical helper for `from apps.api.dependencies.capability import require_capability`
__all__ = [
    "Capability",
    "require_capability",
    "require_launch_landing",
    "require_launch_tos",
    "require_launch_support",
    "require_launch_monitoring",
    "require_tenant_idp_management",
    "require_audit_log_view",
    "require_audit_log_retention",
]


require_launch_landing = require_capability(Capability.LAUNCH_LANDING)
require_launch_tos = require_capability(Capability.LAUNCH_TOS)
require_launch_support = require_capability(Capability.LAUNCH_SUPPORT)
require_launch_monitoring = require_capability(Capability.LAUNCH_MONITORING)
# Epic 16 — Tenant IdP admin management capability (F19.6 + AC #6.3).
# Gates the 5 CRUD routes in apps/api/modules/auth/sso/idp_admin_routes.py
# (GET/POST/PUT/DELETE/TEST). Industry-agnostic per CR 12-1 L4 precedent
# (mirrors SSO_ENTERPRISE / LISTEN_NOTIFY / AUTH_MIDDLEWARE / DEPLOYMENT_*
# / LAUNCH_* pattern). All 4 industries can manage their tenant IdP.
require_tenant_idp_management = require_capability(Capability.TENANT_IDP_MANAGEMENT)
# Epic 17 — Audit log viewer capability (F21.6 + AC #6.3 + AD-32 (g)).
# Gates the audit log viewer routes in
# apps/api/modules/audit/audit_log_routes.py (audit_log list / count /
# entry lookup / CSV export).
# (the activity route is NOT gated — activity stream is intentionally
# broad like Slack presence; PRD §F21.3 verbatim.) Industry-agnostic per
# CR 12-1 L4 precedent (mirrors MULTI_REGION_BACKUP + MULTI_REGION_FAILOVER
# Phase 5 wire pattern + TENANT_IDP_MANAGEMENT Epic 16 wire +
# SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY 13/14 wire +
# AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire +
# DEPLOYMENT_* Phase 4 wire pattern verbatim). All 4 industries get
# audit log viewer capability.
require_audit_log_view = require_capability(Capability.AUDIT_LOG_VIEW)
# Phase 6 — Audit log retention capability (F22.6 + AC #6.3 + AD-33 (f)
# sub-decision). Gates the audit log retention routes in
# apps/api/modules/audit/retention/retention_routes.py (retention policy
# DSL CRUD + automatic purge job trigger + cold-archive action +
# GDPR Article 17 erasure endpoint). Industry-agnostic per CR 12-1 L4
# precedent (mirrors MULTI_REGION_BACKUP/FAILOVER Phase 5 wire +
# AUDIT_LOG_VIEW Epic 17 wire + TENANT_IDP_MANAGEMENT Epic 16 wire +
# SSO_ENTERPRISE Epic 15 wire + LISTEN_NOTIFY 13/14 wire +
# AUTH_MIDDLEWARE Phase 3 wire + LAUNCH_* 1st release wire +
# DEPLOYMENT_* Phase 4 wire pattern verbatim). All 4 industries get
# audit log retention capability (compliance baseline).
require_audit_log_retention = require_capability(Capability.AUDIT_LOG_RETENTION)
