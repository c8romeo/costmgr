"""
apps/api/dependencies/capability.py — FastAPI dependency helpers for capability gates.

Epic 16 (cj-style 69번째 epic 연속 정직 회복 wire) — T6 (AC #6.3) — F19.6.

Re-exports `require_capability` from `apps.api.core.capability` plus 5
Epic-16-specific named dependencies for the IdP admin territory gates:

  - `require_launch_landing()` — gates `/api/v1/launch/landing` (1st release)
  - `require_launch_tos()` — gates `/api/v1/launch/tos-acceptance` (1st release)
  - `require_launch_support()` — gates `/api/v1/launch/support-tickets` (1st release)
  - `require_launch_monitoring()` — gates `/api/v1/launch/*` (1st release)
  - `require_tenant_idp_management()` — gates `/api/v1/admin/tenant/{slug}/idp` (Epic 16)

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
