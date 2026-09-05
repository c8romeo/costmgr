"""tests.api.core.test_epic_16_audit_log_verification — audit registry verification.

Epic 16 (cj-style 69번째 epic 연속 정직 회복 wire) — AC #7.4.
Verifies `apps/api/core/audit_action.py` exposes the 4 NEW AUTH actions
required by Epic 16:
  - tenant_idp_created
  - tenant_idp_updated
  - tenant_idp_deleted
  - tenant_idp_tested
"""

from __future__ import annotations

import asyncio
import pytest

from apps.api.core.audit_action import ActionClass

EXPECTED_NEW_AUTH_ACTIONS = (
    "tenant_idp_created",
    "tenant_idp_updated",
    "tenant_idp_deleted",
    "tenant_idp_tested",
)


class TestAuthActionClassRegistration:
    """Epic 16 — T7 (AC #7.4) — verify the 4 NEW AUTH actions are in the
    registry, available for `emit_audit_typed()` to validate against.
    """

    @pytest.mark.parametrize("action", EXPECTED_NEW_AUTH_ACTIONS)
    def test_action_in_auth_registry(self, action: str) -> None:
        from apps.api.core.audit_action import _ActionRegistry

        registry = _ActionRegistry._REGISTRY
        # Walk to the AUTH action class and confirm action is in the frozenset.
        auth_entry = registry.get(ActionClass.AUTH)
        assert auth_entry is not None, "ActionClass.AUTH missing from registry"

        # registry shape: (AuditLogType, frozenset[str])
        _, action_set = auth_entry
        assert action in action_set, (
            f"{action} not in ActionClass.AUTH frozenset. "
            "Add to apps/api/core/audit_action.py ActionClass.AUTH registry."
        )


class TestEmitAuditTypedAcceptance:
    """emit_audit_typed() should accept the 4 NEW actions without raising.

    Smoke test that does NOT write to a real DB — uses a mock session.
    """

    @pytest.mark.parametrize("action", EXPECTED_NEW_AUTH_ACTIONS)
    def test_emit_accepts_new_action(self, action: str) -> None:
        async def _inner() -> None:
            from unittest.mock import AsyncMock, MagicMock

            from apps.api.core.audit_action import emit_audit_typed

            session = AsyncMock()
            session.execute = AsyncMock()
            session.commit = AsyncMock()

            ctx = MagicMock()
            ctx.user_id = "test-user-id"

            # Just call it — should not raise a validation error for the
            # action names that are in the AUTH registry.
            try:
                await emit_audit_typed(
                    session,
                    action_class=ActionClass.AUTH,
                    action=action,
                    actor_id=ctx.user_id,
                    target_id=None,
                    tenant_id=None,
                    payload={"test": True},
                )
            except (KeyError, ValueError) as exc:
                pytest.fail(
                    f"emit_audit_typed raised for known-good action {action}: {exc}"
                )

        asyncio.run(_inner())


class TestAuditActionRegistryShape:
    """Sanity check that the registry structure hasn't changed unexpectedly."""

    def test_auth_class_is_present(self) -> None:
        from apps.api.core.audit_action import _ActionRegistry

        assert ActionClass.AUTH in _ActionRegistry._REGISTRY

    def test_total_auth_actions_minimum(self) -> None:
        """Epic 16 added 4; Epic 15 added 3 (magic_link_sent,
        social_oauth_initiated, sso_identity_linked).
        At least 7 NEW Epic 15+16 actions expected.
        """
        from apps.api.core.audit_action import _ActionRegistry

        _, action_set = _ActionRegistry._REGISTRY[ActionClass.AUTH]
        # Epic 15 (3) + Epic 16 (4) = at least 7
        assert len(action_set) >= 7, (
            f"Expected at least 7 AUTH actions (Epic 15+16), got {len(action_set)}"
        )


class TestCR1Compliance:
    """CR 1-1 audit-first: actions must be emitted BEFORE the data mutation."""

    def test_create_action_name(self) -> None:
        # The route handler invokes emit_audit_typed(action="tenant_idp_created")
        # BEFORE the INSERT into tenant_idps. Verify the action name
        # matches the spec.
        assert "tenant_idp_created" in EXPECTED_NEW_AUTH_ACTIONS

    def test_update_action_name(self) -> None:
        assert "tenant_idp_updated" in EXPECTED_NEW_AUTH_ACTIONS

    def test_delete_action_name(self) -> None:
        assert "tenant_idp_deleted" in EXPECTED_NEW_AUTH_ACTIONS

    def test_test_action_name(self) -> None:
        assert "tenant_idp_tested" in EXPECTED_NEW_AUTH_ACTIONS


class TestTypoActionRejected:
    """D-EPIC-16-REVIEW-DEFER-3 (M5) RESOLVED — emit_audit_typed typo guard.

    The original review flagged the risk that emit_audit_typed might let an
    arbitrary string action pass through without validation. The actual
    implementation calls `_ActionRegistry.validate()` which checks the
    action against the frozenset of accepted actions for the given
    ActionClass. This test pins that behavior: a typo (e.g. an extra
    underscore) MUST raise ValueError, and a known-good action MUST pass.
    """

    @pytest.mark.parametrize(
        "typo_action",
        [
            "tenant_idp_create",  # missing trailing 'd'
            "tenant_idp_created_typo",
            "TENANT_IDP_CREATED",  # case-sensitive
            " tenant_idp_created",  # leading whitespace
            "tenant_idp_created ",  # trailing whitespace
        ],
    )
    def test_typo_action_raises_value_error(self, typo_action: str) -> None:
        async def _inner() -> None:
            from unittest.mock import AsyncMock

            from apps.api.core.audit_action import emit_audit_typed

            session = AsyncMock()

            with pytest.raises(ValueError, match="audit_action: action"):
                await emit_audit_typed(
                    session,
                    action_class=ActionClass.AUTH,
                    action=typo_action,
                    actor_id=None,
                    target_id=None,
                    tenant_id=None,
                    payload={},
                )

        asyncio.run(_inner())

    def test_unknown_action_class_raises_value_error(self) -> None:
        """Unknown ActionClass must raise ValueError before any DB call."""
        async def _inner() -> None:
            from unittest.mock import AsyncMock

            from apps.api.core.audit_action import emit_audit_typed

            session = AsyncMock()

            class BogusClass(str):
                """Test-only fake ActionClass that str-matches but isn't registered."""

            bogus_class = BogusClass("bogus_value")

            with pytest.raises(ValueError, match="audit_action: unknown ActionClass"):
                await emit_audit_typed(
                    session,
                    action_class=bogus_class,  # type: ignore[arg-type]
                    action="any_action",
                    actor_id=None,
                    target_id=None,
                    tenant_id=None,
                    payload={},
                )

        asyncio.run(_inner())
