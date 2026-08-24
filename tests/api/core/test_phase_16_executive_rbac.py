"""tests.api.core.test_phase_16_executive_rbac — Phase 16 executive RBAC tests.

Phase 16 (cj-style 127번째 wire) — FinOps Reporting & Executive Dashboard
territory (PRD §F32.5 verbatim + AD-43 (e) decision). Owner-only RBAC
AD-22 verbatim + Epic 12 2FA 챌린지 mandatory + tenant-scoped RBAC.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

import uuid

from apps.api.core.rbac import (
    Role,
    TenantScopeViolationError,
    ExecutiveRolePermissionError,
    CapabilityGateViolationError,
    require_executive_role,
)


TENANT_ID = str(uuid.uuid4())
USER_ID = str(uuid.uuid4())


# ── 4 NEW pytest cases ──────────────────────────────────────
def test_role_enum_has_executive_viewer() -> None:
    """Test 1: Role.EXECUTIVE_VIEWER = 'executive_viewer' registered."""
    assert Role.EXECUTIVE_VIEWER.value == "executive_viewer"
    assert hasattr(Role, "EXECUTIVE_VIEWER")


def test_owner_bypasses_tenant_settings_check() -> None:
    """Test 2: OWNER bypasses tenant_settings.executive_viewers check."""
    validated = require_executive_role(
        user_role=Role.OWNER,
        tenant_settings_executive_viewers=None,
        user_id=USER_ID,
        actor_tenant_id=TENANT_ID,
        requested_tenant_id=TENANT_ID,
    )
    assert validated == Role.OWNER


def test_executive_viewer_with_grant_passes() -> None:
    """Test 3: EXECUTIVE_VIEWER with explicit grant in tenant_settings passes."""
    validated = require_executive_role(
        user_role=Role.EXECUTIVE_VIEWER,
        tenant_settings_executive_viewers=[USER_ID],
        user_id=USER_ID,
        actor_tenant_id=TENANT_ID,
        requested_tenant_id=TENANT_ID,
    )
    assert validated == Role.EXECUTIVE_VIEWER


def test_executive_viewer_without_grant_raises() -> None:
    """Test 4: EXECUTIVE_VIEWER without explicit grant raises ExecutiveRolePermissionError."""
    import pytest
    with pytest.raises(ExecutiveRolePermissionError):
        require_executive_role(
            user_role=Role.EXECUTIVE_VIEWER,
            tenant_settings_executive_viewers=["other-user-id"],
            user_id=USER_ID,
            actor_tenant_id=TENANT_ID,
            requested_tenant_id=TENANT_ID,
        )


def test_cross_tenant_access_raises_violation() -> None:
    """Test 5 (extra): cross-tenant access raises TenantScopeViolationError."""
    import pytest
    other_tenant_id = str(uuid.uuid4())
    with pytest.raises(TenantScopeViolationError):
        require_executive_role(
            user_role=Role.OWNER,
            user_id=USER_ID,
            actor_tenant_id=TENANT_ID,
            requested_tenant_id=other_tenant_id,
        )


def test_viewer_role_denied() -> None:
    """Test 6 (extra): VIEWER role is denied executive access."""
    import pytest
    with pytest.raises(ExecutiveRolePermissionError):
        require_executive_role(
            user_role=Role.VIEWER,
            user_id=USER_ID,
            actor_tenant_id=TENANT_ID,
            requested_tenant_id=TENANT_ID,
        )