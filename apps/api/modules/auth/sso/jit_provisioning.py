"""apps.api.modules.auth.sso.jit_provisioning — Just-In-Time user provisioning.

Epic 15 — T4.3 (AC #3.3) — F17.3 SSO enterprise SAML JIT provisioning.

5-step atomic flow (mirrors Phase 3-0 `tenant_signup_completed` pattern):
  1. UPSERT `users` (auth.users + public.users mirror).
  2. `audit_log` `signup_started` (intermediate trail).
  3. UPSERT `tenants` (by tenant_slug → tenant_id).
  4. UPSERT `tenant_memberships` (role='member' default; owner is
     invited separately).
  5. INSERT `external_identities` (alembic 0037 table).

Multi-tenant isolation (CR 0-2 RLS lesson): every write MUST be
scoped to the SSO tenant context. The `external_identities` table
has an RLS policy `tenant_id = (SELECT current_setting('app.tenant_id'))::uuid`.

Audit-first INSERT (CR 1-1 verbatim): `sso_identity_linked` is recorded
in the audit_logs table BEFORE the user-facing response.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from apps.api.modules.auth.sso.saml_validator import SAMLAssertionAttributes

logger = logging.getLogger(__name__)


# ── Exceptions ────────────────────────────────────────────────────────


class JITProvisioningError(Exception):
    """Base JIT provisioning failure (CR 12-5 D-14 envelope)."""

    def __init__(self, code: str, message_ko: str, details: dict[str, Any] | None = None):
        self.code = code
        self.message_ko = message_ko
        self.details: dict[str, Any] = details or {}
        super().__init__(message_ko)


class JITTenantNotFoundError(JITProvisioningError):
    def __init__(self, tenant_slug: str) -> None:
        super().__init__(
            code="SSO_INVALID_TENANT",
            message_ko="유효하지 않은 회사 도메인입니다",
            details={"tenant_slug": tenant_slug},
        )


# ── Dataclasses ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class JITProvisioningResult:
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    external_identity_id: uuid.UUID
    created_user: bool
    created_tenant: bool
    created_membership: bool


# ── JIT provisioning entry point ─────────────────────────────────────


async def provision_jit_user(
    session: AsyncSession,
    *,
    saml_attrs: SAMLAssertionAttributes,
    tenant_slug: str,
    provider: str = "saml_custom",
) -> JITProvisioningResult:
    """Provision (or link) a user for an incoming SAML assertion.

    The flow is:
      1. Resolve tenant by slug (raise JITTenantNotFoundError if missing).
      2. UPSERT `public.users` keyed on `email`.
      3. UPSERT `tenant_memberships` (role='member' default).
      4. INSERT `external_identities` (provider + provider_user_id).
      5. emit_audit_typed `sso_identity_linked`.

    Every write is scoped to the resolved tenant_id. RLS is enforced at
    the database level (multi-tenant isolation, CR 0-2 RLS lesson).
    """
    # Step 1: resolve tenant (CR 0-2 RLS — read through service_role).
    tenant_row = (
        await session.execute(
            text(
                "SELECT id, deleted_at FROM public.tenants "
                "WHERE slug = :slug AND deleted_at IS NULL LIMIT 1"
            ),
            {"slug": tenant_slug},
        )
    ).first()
    if tenant_row is None:
        raise JITTenantNotFoundError(tenant_slug)
    tenant_id = tenant_row[0]

    # Step 2: UPSERT public.users.
    user_row = (
        await session.execute(
            text(
                """
                INSERT INTO public.users (id, email, created_at, updated_at)
                VALUES (gen_random_uuid(), :email, now(), now())
                ON CONFLICT (email) DO UPDATE
                SET updated_at = now()
                RETURNING id, (xmax = 0) AS created
                """
            ),
            {"email": saml_attrs.email},
        )
    ).first()
    if user_row is None:
        raise JITProvisioningError(
            code="JIT_USER_UPSERT_FAILED",
            message_ko="사용자 생성에 실패했습니다",
        )
    user_id = user_row[0]
    created_user = bool(user_row[1])

    # Step 3: UPSERT tenant_memberships.
    membership_row = (
        await session.execute(
            text(
                """
                INSERT INTO public.tenant_memberships
                    (id, tenant_id, user_id, role, joined_at)
                VALUES (gen_random_uuid(), :tenant_id, :user_id, 'member', now())
                ON CONFLICT (tenant_id, user_id) DO NOTHING
                RETURNING id, (xmax = 0) AS created
                """
            ),
            {"tenant_id": tenant_id, "user_id": user_id},
        )
    ).first()
    created_membership = membership_row is not None and bool(membership_row[1])

    # Step 4: INSERT external_identities.
    ext_id_row = (
        await session.execute(
            text(
                """
                INSERT INTO public.external_identities
                    (id, provider, provider_user_id, tenant_id, user_id,
                     linked_at, last_used_at, metadata)
                VALUES (gen_random_uuid(), :provider, :provider_user_id,
                        :tenant_id, :user_id, now(), now(), :metadata)
                ON CONFLICT (provider, provider_user_id) DO UPDATE
                SET last_used_at = now()
                RETURNING id
                """
            ),
            {
                "provider": provider,
                "provider_user_id": saml_attrs.name_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "metadata": "{}",
            },
        )
    ).first()
    if ext_id_row is None:
        raise JITProvisioningError(
            code="JIT_EXTERNAL_IDENTITY_FAILED",
            message_ko="외부 ID 연결에 실패했습니다",
        )
    external_identity_id = ext_id_row[0]

    # Step 5: audit-first INSERT `sso_identity_linked`.
    await emit_audit_typed(
        session=session,
        action_class=ActionClass.AUTH,
        action="sso_identity_linked",
        target_id=user_id,
        target_table="users",
        actor_id=user_id,
        details={
            "provider": provider,
            "tenant_id": str(tenant_id),
            "external_identity_id": str(external_identity_id),
        },
    )

    return JITProvisioningResult(
        user_id=user_id,
        tenant_id=tenant_id,
        external_identity_id=external_identity_id,
        created_user=created_user,
        created_tenant=False,
        created_membership=created_membership,
    )
