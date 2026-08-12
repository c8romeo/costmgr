"""tests.api.m12_account.test_handlers_role_gate — Story 12.5 role gate tests.

AC #2 self-enrollment role gate (Story 12.5):
- POST /api/v1/account/2fa/setup     → require_any_role("owner", "member")
- POST /api/v1/account/2fa/verify    → require_any_role("owner", "member")
- POST /api/v1/account/2fa/challenge → require_any_role("owner", "member")  (already)
- POST /api/v1/account/2fa/challenge-tokens → require_any_role("owner", "member")  (NEW)
- POST /api/v1/account/2fa/disable   → require_role("owner")  (12-4 P-14 keep)
- POST /api/v1/account/2fa/recovery  → require_role("owner")  (12-4 P-14 keep)

5 NEW test cases verify:
1. `owner` role passes setup/verify/challenge/challenge-tokens allowlist gates.
2. `member` role passes setup/verify/challenge/challenge-tokens allowlist gates
   (member is M2-eligible per PRD §F12.1 — Story 12.5 atomic wire guarantees
   member self-enrollment does NOT trigger permanent M2 lock-out).
3. `viewer` role rejected (403 ForbiddenRoleError) on the four allowlist gates.
4. `consultant_proxy` role rejected (403 ForbiddenRoleError) on the four gates.
5. `member` is rejected (403) on disable + recovery owner-only gates; `owner`
   passes both. Viewer/consultant_proxy also 403'd on disable + recovery.

Approach: directly invoke `require_role(role)` and `require_any_role(*roles)`
dependency factories with stubbed `get_tenant_context`. This avoids the
FastAPI TestClient + DB engine startup which is heavyweight for these
pure-gate tests. Roles + AD-10 semantics are the test target, not routing.

The corresponding routes are wired in `apps/api/modules/m12_account/handlers.py`
(see `test_handlers_route_shape.py` for route-level coverage).
"""

from __future__ import annotations

import asyncio
import uuid

import pytest

from apps.api.core.capability import (
    ForbiddenRoleError,
    require_any_role,
    require_role,
)
from apps.api.core.tenant_context import TenantContext


def _stub_tenant(role: str) -> TenantContext:
    """Build a TenantContext stub with the given role."""
    tid = uuid.uuid4()
    return TenantContext(
        tenant_id=tid,
        user_id=uuid.uuid4(),
        role=role,
        industry="manufacturing_service",
    )


async def _run_dependency(dep, role: str) -> TenantContext:
    """Invoke a FastAPI dependency callable directly with a stubbed context.

    The dependency factories `require_role` / `require_any_role` close over
    a `get_tenant_context` sub-dependency via `Depends(...)`. To bypass that,
    we construct an instance-bound coroutine that returns our tenant stub.

    Note: rather than mocking FastAPI's dependency chain, we invoke the dep
    closure's inner _dep function with a fresh TenantContext — equivalent to
    what FastAPI would pass after the upstream dependency resolved.
    """
    # The dep factories return an inner async function `_dep`. For our
    # allowlist/role gates, the inner function only depends on the
    # `get_tenant_context` parameter, which we replicate below.
    ctx = _stub_tenant(role)
    # Find the inner coroutine — it's the only callable returned by the factory.
    # Pattern: require_role(role) returns _dep with signature
    # `(ctx: TenantContext = Depends(get_tenant_context)) -> TenantContext:`.
    # We can't simply call _dep(ctx=ctx) because Depends() needs to be resolved,
    # but FastAPI's mechanism unwraps that and passes the resolved value.
    # The dependency chain is `_dep(ctx=ctx)` after Depends() resolves to ctx.
    inner = dep  # this is the _dep coroutine from the factory
    # FastAPI Depends() resolves to a fresh TenantContext; for unit testing
    # we call the inner coroutine directly with kwargs.
    try:
        return await inner(ctx=ctx)
    except TypeError:
        # Some FastAPI versions require positional arg.
        return await inner(ctx)


# ── Case 1: owner passes allowlist gates ─────────────────────────
def test_owner_passes_setup_verify_challenge_allowlist() -> None:
    """owner role → require_any_role("owner", "member") passes for owner.

    Story 12.5 atomic wire guarantee: owner is in the allowlist for
    setup/verify/challenge/challenge-tokens.
    """
    for factory in [
        require_any_role("owner", "member"),
        require_any_role("owner", "member"),
    ]:
        # Same factory used by all 4 allowlist routes.
        ctx = asyncio.run(_run_dependency(factory, "owner"))
        assert ctx.role == "owner"


# ── Case 2: member passes allowlist gates (M2 entry 보장) ─────────
def test_member_passes_setup_verify_challenge_allowlist() -> None:
    """member role → require_any_role("owner", "member") passes for member.

    Without this case, a member user could never set up 2FA and would be
    permanently locked out of M2 (PRD §F12.1 + §M12-a). Story 12.5 atomic
    wire guarantee: member is in the allowlist.
    """
    factory = require_any_role("owner", "member")
    ctx = asyncio.run(_run_dependency(factory, "member"))
    assert ctx.role == "member"


# ── Case 3: viewer rejected (403) on all allowlist gates ──────────
def test_viewer_rejected_on_all_allowlist_gates() -> None:
    """viewer role → ForbiddenRoleError on require_any_role("owner", "member").

    Viewer cannot self-enroll 2FA because they cannot enter M2 to begin with
    (PRD §F12.1 — read-only role). Rejecting 2FA setup prevents them from
    acquiring a challenge token for routes they cannot use.
    """
    factory = require_any_role("owner", "member")
    with pytest.raises(ForbiddenRoleError) as excinfo:
        asyncio.run(_run_dependency(factory, "viewer"))
    assert excinfo.value.role == "viewer"
    assert "owner" in excinfo.value.required_role
    assert "member" in excinfo.value.required_role


# ── Case 4: consultant_proxy rejected (403) on all allowlist gates ─
def test_consultant_proxy_rejected_on_all_allowlist_gates() -> None:
    """consultant_proxy role → ForbiddenRoleError on require_any_role.

    consultant_proxy is an external auditor (read-only, time-boxed). They
    must NOT be able to set up 2FA because the recovery codes + secret
    are sensitive (NFR6 column-level encryption applies), and a compromised
    proxy must not be able to attach 2FA to a user they only audit.
    """
    factory = require_any_role("owner", "member")
    with pytest.raises(ForbiddenRoleError) as excinfo:
        asyncio.run(_run_dependency(factory, "consultant_proxy"))
    assert excinfo.value.role == "consultant_proxy"


# ── Case 5: owner-only gates (disable + recovery) reject member + viewer ─
def test_disable_and_recovery_owner_only_rejects_member_viewer_consultant() -> None:
    """owner-only on disable + recovery (12-4 P-14 keep).

    disable + recovery carry sensitive destructive operations
    (disable permanently removes 2FA; recovery burns 1 of 8 codes).
    Both must remain owner-only even though setup/verify are open to member.
    """
    factory = require_role("owner")

    # 5a: owner passes
    ctx = asyncio.run(_run_dependency(factory, "owner"))
    assert ctx.role == "owner"

    # 5b: member rejected
    with pytest.raises(ForbiddenRoleError) as excinfo:
        asyncio.run(_run_dependency(factory, "member"))
    assert excinfo.value.role == "member"
    assert excinfo.value.required_role == "owner"

    # 5c: viewer rejected
    with pytest.raises(ForbiddenRoleError) as excinfo:
        asyncio.run(_run_dependency(factory, "viewer"))
    assert excinfo.value.role == "viewer"

    # 5d: consultant_proxy rejected
    with pytest.raises(ForbiddenRoleError) as excinfo:
        asyncio.run(_run_dependency(factory, "consultant_proxy"))
    assert excinfo.value.role == "consultant_proxy"
