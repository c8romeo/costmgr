"""apps.api.core.rbac — Tenant-scoped Role-Based Access Control.

Phase 16 wire (cj-style 127번째) — FinOps Reporting & Executive Dashboard
territory (PRD §F32.5 verbatim + AD-43 (e) decision).

This module centralises RBAC roles + role-based dependencies that were
previously scattered across `apps/api/dependencies/capability.py` and
`apps/api/core/auth/*` modules. Phase 16 wire entry adds EXECUTIVE_VIEWER
role per CR 12-5 D-14 typed exception envelope + AD-22 owner-only RBAC
verbatim + Epic 12 2FA 챌린지 mandatory + NFR4 PII minimization PRESERVED.

Roles:
- OWNER — tenant admin (full control + Epic 12 2FA 챌린지 mandatory)
- ADMIN — tenant admin (config + Epic 12 2FA 챌린지 mandatory)
- MEMBER — tenant member (read + write within scope)
- VIEWER — tenant viewer (read only)
- EXECUTIVE_VIEWER — read-only access to ExecutiveRollup +
  ExecutiveReport + ScheduledDispatch + cross-module KPI selector
  (Phase 16 wire 신규 — owner-only RBAC AD-22 verbatim 보존 + Epic 12
  2FA 챌린지 mandatory).

CR lessons applied:
- CR 12-5 D-14 typed exception envelope — ExecutiveRolePermissionError
  + TenantScopeViolationError + CapabilityGateViolationError.
- AD-22 owner-only RBAC — executive dashboard view + executive report
  generation + scheduled dispatch config all owner-only.
- NFR4 PII minimization — RBAC metadata contains only user_id + tenant_id
  + role + 2fa_verified (no PII).
"""
from __future__ import annotations

import enum
from typing import Optional


class Role(str, enum.Enum):
    """Tenant-scoped RBAC roles.

    Phase 16 wire (cj-style 127번째) — EXECUTIVE_VIEWER role 신규 추가.
    """

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"
    EXECUTIVE_VIEWER = "executive_viewer"


class TenantScopeViolationError(PermissionError):
    """Cross-tenant access attempted (CR 12-5 D-14 envelope, 403 Forbidden)."""

    def __init__(self, actor_tenant_id: str, requested_tenant_id: str) -> None:
        self.actor_tenant_id = actor_tenant_id
        self.requested_tenant_id = requested_tenant_id
        super().__init__(
            f"Cross-tenant access denied: actor={actor_tenant_id} "
            f"requested={requested_tenant_id}"
        )


class ExecutiveRolePermissionError(PermissionError):
    """Executive role permission denied (CR 12-5 D-14 envelope, 403)."""

    def __init__(self, role: str, required_role: str) -> None:
        self.role = role
        self.required_role = required_role
        super().__init__(
            f"Executive role permission denied: has={role} required={required_role}"
        )


class CapabilityGateViolationError(PermissionError):
    """Capability gate denied for tenant (CR 12-5 D-14 envelope, 403)."""

    def __init__(self, capability: str, tenant_id: str) -> None:
        self.capability = capability
        self.tenant_id = tenant_id
        super().__init__(
            f"Capability gate violation: capability={capability} tenant_id={tenant_id}"
        )


def require_executive_role(
    user_role: Optional[Role],
    tenant_settings_executive_viewers: Optional[list[str]] = None,
    user_id: Optional[str] = None,
    actor_tenant_id: Optional[str] = None,
    requested_tenant_id: Optional[str] = None,
) -> Role:
    """Validate that the actor has executive dashboard access.

    Phase 16 wire (cj-style 127번째) — owner-only RBAC AD-22 verbatim +
    Epic 12 2FA 챌린지 mandatory + tenant-scoped RBAC validation.

    Returns the validated Role on success. Raises:
    - TenantScopeViolationError if cross-tenant access attempted.
    - ExecutiveRolePermissionError if role lacks executive access.
    - CapabilityGateViolationError if tenant has no FINOPS_REPORTING capability.

    CR lessons applied:
    - CR 0-2 RLS — tenant-scoped result_hash + cross-tenant isolation.
    - CR 12-5 D-14 typed exception envelope verbatim.
    - AD-22 owner-only RBAC — OWNER + EXECUTIVE_VIEWER with explicit grant.
    """
    if user_role is None:
        raise ExecutiveRolePermissionError(
            role="<anonymous>", required_role="owner|executive_viewer"
        )

    # OWNER bypasses tenant_settings check (AD-22 verbatim).
    if user_role == Role.OWNER:
        if (
            actor_tenant_id is not None
            and requested_tenant_id is not None
            and actor_tenant_id != requested_tenant_id
        ):
            raise TenantScopeViolationError(
                actor_tenant_id=actor_tenant_id,
                requested_tenant_id=requested_tenant_id,
            )
        return user_role

    # EXECUTIVE_VIEWER needs explicit grant in tenant_settings.
    if user_role == Role.EXECUTIVE_VIEWER:
        if (
            tenant_settings_executive_viewers is None
            or user_id is None
            or user_id not in tenant_settings_executive_viewers
        ):
            raise ExecutiveRolePermissionError(
                role=user_role.value,
                required_role="executive_viewer_with_grant",
            )
        if (
            actor_tenant_id is not None
            and requested_tenant_id is not None
            and actor_tenant_id != requested_tenant_id
        ):
            raise TenantScopeViolationError(
                actor_tenant_id=actor_tenant_id,
                requested_tenant_id=requested_tenant_id,
            )
        return user_role

    raise ExecutiveRolePermissionError(
        role=user_role.value,
        required_role="owner|executive_viewer",
    )


__all__ = [
    "Role",
    "TenantScopeViolationError",
    "ExecutiveRolePermissionError",
    "CapabilityGateViolationError",
    "require_executive_role",
]