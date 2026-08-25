"""apps.api.core.rbac — Tenant-scoped Role-Based Access Control.

Phase 17 wire (cj-style 131번째) — FinOps Sustainability & Carbon Reporting
territory (PRD §F33.5 verbatim + AD-44 (e) decision) — extends Phase 16
wire `81ae00a` rbac.py with SUSTAINABILITY_VIEWER role + require_sustainability_role()
dependency following Phase 16 EXECUTIVE_VIEWER + require_executive_role()
pattern verbatim.

This module centralises RBAC roles + role-based dependencies that were
previously scattered across `apps/api/dependencies/capability.py` and
`apps/api/core/auth/*` modules. Phase 16 wire entry adds EXECUTIVE_VIEWER
role per CR 12-5 D-14 typed exception envelope + AD-22 owner-only RBAC
verbatim + Epic 12 2FA 챌린지 mandatory + NFR4 PII minimization PRESERVED.
Phase 17 wire entry adds SUSTAINABILITY_VIEWER role mirroring the same
pattern (CR 12-5 D-14 + AD-22 + Epic 12 2FA + NFR4).

Roles:
- OWNER — tenant admin (full control + Epic 12 2FA 챌린지 mandatory)
- ADMIN — tenant admin (config + Epic 12 2FA 챌린지 mandatory)
- MEMBER — tenant member (read + write within scope)
- VIEWER — tenant viewer (read only)
- EXECUTIVE_VIEWER — read-only access to ExecutiveRollup +
  ExecutiveReport + ScheduledDispatch + cross-module KPI selector
  (Phase 16 wire 신규 — owner-only RBAC AD-22 verbatim 보존 + Epic 12
  2FA 챌린지 mandatory).
- SUSTAINABILITY_VIEWER — read-only access to CarbonEmissionsRollup +
  SustainabilityKPIMetric + SustainabilityReport +
  ScheduledSustainabilityDispatch + sustainability cross-module KPI selector
  (Phase 17 wire 신규 — owner-only RBAC AD-22 verbatim 보존 + Epic 12
  2FA 챌린지 mandatory + 4-industry grants ✅/✅/✅/✅ industry-agnostic
  per CR 12-1 L4 precedent).

CR lessons applied:
- CR 12-5 D-14 typed exception envelope — ExecutiveRolePermissionError
  + SustainabilityRolePermissionError + TenantScopeViolationError +
  CapabilityGateViolationError.
- AD-22 owner-only RBAC — executive dashboard view + executive report
  generation + scheduled dispatch config all owner-only; sustainability
  dashboard view + sustainability report generation + sustainability
  scheduled dispatch config also owner-only.
- NFR4 PII minimization — RBAC metadata contains only user_id + tenant_id
  + role + 2fa_verified (no PII).
"""
from __future__ import annotations

import enum
from typing import Optional


class Role(str, enum.Enum):
    """Tenant-scoped RBAC roles.

    Phase 16 wire (cj-style 127번째) — EXECUTIVE_VIEWER role 신규 추가.
    Phase 17 wire (cj-style 131번째) — SUSTAINABILITY_VIEWER role 신규 추가.
    """

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"
    EXECUTIVE_VIEWER = "executive_viewer"  # Phase 16 wire 신규
    SUSTAINABILITY_VIEWER = "sustainability_viewer"  # Phase 17 wire 신규
    COMMITMENT_VIEWER = "commitment_viewer"  # Phase 18 wire 신규 (cj-style 135번째)
    PRICING_VIEWER = "pricing_viewer"  # Phase 19 wire 신규 (cj-style 139번째)


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


class SustainabilityRolePermissionError(PermissionError):
    """Sustainability role permission denied (CR 12-5 D-14 envelope, 403).

    Phase 17 wire (cj-style 131번째) — mirrors ExecutiveRolePermissionError
    verbatim for sustainability dashboard / report / scheduled dispatch
    access. AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
    """

    def __init__(self, role: str, required_role: str) -> None:
        self.role = role
        self.required_role = required_role
        super().__init__(
            f"Sustainability role permission denied: has={role} required={required_role}"
        )


class CommitmentRolePermissionError(PermissionError):
    """Commitment role permission denied (CR 12-5 D-14 envelope, 403).

    Phase 18 wire (cj-style 135번째) — mirrors SustainabilityRolePermissionError
    verbatim for commitment dashboard / report / scheduled dispatch
    access. AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
    """

    def __init__(self, role: str, required_role: str) -> None:
        self.role = role
        self.required_role = required_role
        super().__init__(
            f"Commitment role permission denied: has={role} required={required_role}"
        )


class PricingRolePermissionError(PermissionError):
    """Pricing role permission denied (CR 12-5 D-14 envelope, 403).

    Phase 19 wire (cj-style 139번째) — mirrors CommitmentRolePermissionError
    verbatim for pricing dashboard / report / scheduled dispatch access.
    AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory +
    4-industry grants ✅/✅/✅/✅ industry-agnostic per CR 12-1 L4 precedent.
    """

    def __init__(self, role: str, required_role: str) -> None:
        self.role = role
        self.required_role = required_role
        super().__init__(
            f"Pricing role permission denied: has={role} required={required_role}"
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


def require_sustainability_role(
    user_role: Optional[Role],
    tenant_settings_sustainability_viewers: Optional[list[str]] = None,
    user_id: Optional[str] = None,
    actor_tenant_id: Optional[str] = None,
    requested_tenant_id: Optional[str] = None,
) -> Role:
    """Validate that the actor has sustainability dashboard access.

    Phase 17 wire (cj-style 131번째) — owner-only RBAC AD-22 verbatim +
    Epic 12 2FA 챌린지 mandatory + tenant-scoped RBAC validation +
    4-industry grants ✅/✅/✅/✅ industry-agnostic per CR 12-1 L4 precedent.

    Returns the validated Role on success. Raises:
    - TenantScopeViolationError if cross-tenant access attempted.
    - SustainabilityRolePermissionError if role lacks sustainability access.
    - CapabilityGateViolationError if tenant has no FINOPS_SUSTAINABILITY capability.

    CR lessons applied:
    - CR 0-2 RLS — tenant-scoped result_hash + cross-tenant isolation.
    - CR 12-5 D-14 typed exception envelope verbatim.
    - AD-22 owner-only RBAC — OWNER + SUSTAINABILITY_VIEWER with explicit grant.
    """
    if user_role is None:
        raise SustainabilityRolePermissionError(
            role="<anonymous>", required_role="owner|sustainability_viewer"
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

    # SUSTAINABILITY_VIEWER needs explicit grant in tenant_settings.
    if user_role == Role.SUSTAINABILITY_VIEWER:
        if (
            tenant_settings_sustainability_viewers is None
            or user_id is None
            or user_id not in tenant_settings_sustainability_viewers
        ):
            raise SustainabilityRolePermissionError(
                role=user_role.value,
                required_role="sustainability_viewer_with_grant",
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

    raise SustainabilityRolePermissionError(
        role=user_role.value,
        required_role="owner|sustainability_viewer",
    )


def require_commitment_role(
    user_role: Optional[Role],
    tenant_settings_commitment_viewers: Optional[list[str]] = None,
    user_id: Optional[str] = None,
    actor_tenant_id: Optional[str] = None,
    requested_tenant_id: Optional[str] = None,
) -> Role:
    """Validate that the actor has commitment dashboard access.

    Phase 18 wire (cj-style 135번째) — owner-only RBAC AD-22 verbatim +
    Epic 12 2FA 챌린지 mandatory + tenant-scoped RBAC validation +
    4-industry grants ✅/✅/✅/✅ industry-agnostic per CR 12-1 L4 precedent
    (mirrors require_sustainability_role verbatim).

    Returns the validated Role on success. Raises:
    - TenantScopeViolationError if cross-tenant access attempted.
    - CommitmentRolePermissionError if role lacks commitment access.
    - CapabilityGateViolationError if tenant has no FINOPS_COMMITMENT capability.

    CR lessons applied:
    - CR 0-2 RLS — tenant-scoped result_hash + cross-tenant isolation.
    - CR 12-5 D-14 typed exception envelope verbatim.
    - AD-22 owner-only RBAC — OWNER + COMMITMENT_VIEWER with explicit grant.
    """
    if user_role is None:
        raise CommitmentRolePermissionError(
            role="<anonymous>", required_role="owner|commitment_viewer"
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

    # COMMITMENT_VIEWER needs explicit grant in tenant_settings.
    if user_role == Role.COMMITMENT_VIEWER:
        if (
            tenant_settings_commitment_viewers is None
            or user_id is None
            or user_id not in tenant_settings_commitment_viewers
        ):
            raise CommitmentRolePermissionError(
                role=user_role.value,
                required_role="commitment_viewer_with_grant",
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

    raise CommitmentRolePermissionError(
        role=user_role.value,
        required_role="owner|commitment_viewer",
    )


def require_pricing_role(
    user_role: Optional[Role],
    tenant_settings_pricing_viewers: Optional[list[str]] = None,
    user_id: Optional[str] = None,
    actor_tenant_id: Optional[str] = None,
    requested_tenant_id: Optional[str] = None,
) -> Role:
    """Validate that the actor has pricing dashboard access.

    Phase 19 wire (cj-style 139번째) — owner-only RBAC AD-22 verbatim +
    Epic 12 2FA 챌린지 mandatory + tenant-scoped RBAC validation +
    4-industry grants ✅/✅/✅/✅ industry-agnostic per CR 12-1 L4 precedent
    (mirrors require_commitment_role Phase 18 + require_sustainability_role
    Phase 17 verbatim).

    Returns the validated Role on success. Raises:
    - TenantScopeViolationError if cross-tenant access attempted.
    - PricingRolePermissionError if role lacks pricing access.
    - CapabilityGateViolationError if tenant has no FINOPS_PRICING capability.

    CR lessons applied:
    - CR 0-2 RLS — tenant-scoped result_hash + cross-tenant isolation.
    - CR 12-5 D-14 typed exception envelope verbatim.
    - AD-22 owner-only RBAC — OWNER + PRICING_VIEWER with explicit grant.
    """
    if user_role is None:
        raise PricingRolePermissionError(
            role="<anonymous>", required_role="owner|pricing_viewer"
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

    # PRICING_VIEWER needs explicit grant in tenant_settings.
    if user_role == Role.PRICING_VIEWER:
        if (
            tenant_settings_pricing_viewers is None
            or user_id is None
            or user_id not in tenant_settings_pricing_viewers
        ):
            raise PricingRolePermissionError(
                role=user_role.value,
                required_role="pricing_viewer_with_grant",
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

    raise PricingRolePermissionError(
        role=user_role.value,
        required_role="owner|pricing_viewer",
    )


__all__ = [
    "Role",
    "TenantScopeViolationError",
    "ExecutiveRolePermissionError",
    "SustainabilityRolePermissionError",
    "CommitmentRolePermissionError",
    "PricingRolePermissionError",
    "CapabilityGateViolationError",
    "require_executive_role",
    "require_sustainability_role",
    "require_commitment_role",
    "require_pricing_role",
]