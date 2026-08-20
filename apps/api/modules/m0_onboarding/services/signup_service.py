"""apps.api.modules.m0_onboarding.services.signup_service — atomic tenant creation.

Phase 3-0 (cj-style Epic 14 carry-over 2번째, "fix" 종류) — auth 계약
수직 슬라이스 진입 결정 wire. PRD §F15.2 가 요구하는
"atomic transaction: users + tenants + user_tenants + tenant_settings +
audit_logs" 의 백엔드 측 wire.

이 모듈이 하는 일:

1. `complete_signup()` — 한 트랜잭션에서:
   - `users` 에 auth.users row 와 동일한 id 의 row 를 만든다 (이미
     있으면 그대로 둠 — 멱등성).
   - `tenants` 에 새 row 를 만든다 (이름 + 업종).
   - `tenant_memberships` 에 (tenant, user, role='owner') row 를 만든다.
   - `tenant_settings` 에 빈 JSONB row 를 만든다 (settings_version=1).
   - `audit_logs` 에 `tenant_signup_completed` 1 row 를 INSERT 한다.
   - 모든 INSERT 가 같은 트랜잭션이므로, 어느 하나라도 실패하면
     전부 롤백 (PRD §F15.2 원자성 요구).

2. `get_existing_membership_for_user()` — 사용자가 이미 tenant 에 속해
   있는지를 검사. 중복 signup 방지 (A11 axiom — 한 user 가 두 테넌트의
   owner 가 되는 사고 방지). 속해 있으면 `AlreadyHasTenantError` 발생.

3. `get_or_create_user_row()` — `auth.users` 의 id 와 동일한 `users`
   row 가 있는지 확인하고 없으면 만든다. signup 시점에 이 user 의
   `users` row 가 없을 수 있다 (auth 와 우리 스키마는 별개).

**알려진 한계 (다음 sprint):**
- `users.email` 이 Supabase 의 `auth.users.email` 과 일치하는지 강제
  하지는 않는다 (현재 `auth.users` 에 JOIN 불가능). Story 0.2 의
  `users.email` UNIQUE 제약이 같은 이메일로 두 번 가입하는 것을 막아주지만,
  다른 경로로 동일 user_id 의 row 가 email 을 바꾸는 시나리오는
  audit log 로만 추적한다.

Anti-pattern guards (A11 axiom 적용):
- audit row 는 settings INSERT 와 같은 트랜잭션이지만, settings 가
  성공한 "후" 에 emit 한다 (CR 1.1 verbatim — "audit-first" 라는
  이름이지만 실제로는 같은 트랜잭션 내 emit 임).
- `tenant_id` 는 서버에서 생성 (`gen_random_uuid()`), 절대 요청에서 받지
  않는다 (AD-3 verbatim).
- `actor_id` = user_id from JWT, 절대 스푸핑 불가.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from apps.api.core.db_models import (
    Tenant,
    TenantMembership,
    TenantSettings,
    User,
)
from packages.services.m0_onboarding.industry_menu import Industry

# ── Typed exceptions ────────────────────────────────────────


class AlreadyHasTenantError(Exception):
    """409 ALREADY_HAS_TENANT — 사용자가 이미 tenant 에 속해 있어
    signup-completion 을 거부한다.

    1 user 가 여러 tenant 의 owner 가 되면 정합성이 깨진다 (audit log 가
    어느 테넌트 기준인지 모호해짐). A11 axiom — 한 user 의 tenant
    membership 은 1개로 제한.

    예외: `consultant_proxy` 는 여러 tenant 의 멤버가 될 수 있다
    (PRD §F15.2 verbatim "consultant_proxy" 시나리오). 그러나 signup
    직후 첫 tenant 는 항상 `owner` 여야 하므로 이 한계는 적용되지
    않는다.
    """

    def __init__(
        self,
        *,
        user_id: uuid.UUID,
        existing_tenant_id: uuid.UUID,
        existing_role: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"user {user_id} already has membership in tenant {existing_tenant_id} as {existing_role}"
        )
        self.user_id = user_id
        self.existing_tenant_id = existing_tenant_id
        self.existing_role = existing_role
        self.trace_id = trace_id


class TenantNameValidationError(Exception):
    """422 TENANT_NAME_INVALID — `tenant_name` 이 너무 짧거나 (after
    trim) 너무 긴 경우.
    """

    def __init__(self, *, reason: str, trace_id: str) -> None:
        super().__init__(f"invalid tenant name: {reason}")
        self.reason = reason
        self.trace_id = trace_id


# ── Return value (success envelope) ─────────────────────────


@dataclass(frozen=True)
class SignupCompletion:
    """Successful signup completion — pure value object."""

    tenant_id: uuid.UUID
    role: str
    industry: Industry
    settings_version: int
    trace_id: str


# ── Service ─────────────────────────────────────────────────


class SignupService:
    """Atomic tenant creation for fresh signups (Phase 3-0).

    All writes happen in a single SQLAlchemy session.transaction()
    block. Either all 4 rows are persisted + 1 audit row, or none.
    """

    def __init__(self, session: AsyncSession, *, trace_id: str) -> None:
        self._session = session
        self._trace_id = trace_id

    async def complete_signup(
        self,
        *,
        user_id: uuid.UUID,
        user_email: str | None,
        tenant_name: str,
        industry: Industry,
    ) -> SignupCompletion:
        """Atomically: ensure `users` row, create `tenants` + membership + settings, audit.

        Raises:
            TenantNameValidationError: tenant_name is empty/too long.
            AlreadyHasTenantError: user already has a tenant_membership
                (signup-completion can only mint the FIRST tenant).
            IntegrityError: a DB-level constraint failed (e.g., UNIQUE
                email race). The handler maps this to 409.
        """
        # 1. Validate inputs
        name_clean = tenant_name.strip()
        if not name_clean:
            raise TenantNameValidationError(
                reason="empty_after_trim", trace_id=self._trace_id
            )
        if len(name_clean) > 200:
            raise TenantNameValidationError(
                reason="too_long", trace_id=self._trace_id
            )

        # 2. Check the user is not already a member of any tenant.
        existing = await self._session.execute(
            select(TenantMembership)
            .where(TenantMembership.user_id == user_id)
            .limit(1)
        )
        existing_membership = existing.scalar_one_or_none()
        if existing_membership is not None:
            raise AlreadyHasTenantError(
                user_id=user_id,
                existing_tenant_id=existing_membership.tenant_id,
                existing_role=existing_membership.role,
                trace_id=self._trace_id,
            )

        # 3. Ensure a `users` row exists for this auth.users id.
        #    Supabase owns auth.users; we own public.users. The mapping
        #    is by id. If the row doesn't exist, create it.
        await self._get_or_create_user_row(user_id=user_id, user_email=user_email)

        # 4. Create the tenant.
        tenant_id = uuid.uuid4()
        tenant = Tenant(
            id=tenant_id,
            name=name_clean,
            industry=industry.value,
            created_at=datetime.now(UTC),
        )
        self._session.add(tenant)

        # 5. Create the membership (user becomes owner).
        membership = TenantMembership(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            role="owner",
            joined_at=datetime.now(UTC),
        )
        self._session.add(membership)

        # 6. Create the empty tenant_settings row.
        settings = TenantSettings(
            tenant_id=tenant_id,
            settings_version=1,
            onboarding={},
            baseline={},
            abc={},
            ai={},
            payroll={},
            updated_at=datetime.now(UTC),
        )
        self._session.add(settings)

        # 7. Flush to surface any DB-level errors BEFORE the audit log.
        #    If the tenant INSERT fails (e.g., industry CHECK violation,
        #    name too long) we want the failure visible without an audit
        #    row dangling in the ledger.
        try:
            await self._session.flush()
        except IntegrityError as e:
            # Map to typed error; handler converts to 409.
            raise IntegrityError(
                statement=e.statement,
                params=e.params,
                orig=e.orig,
            ) from e

        # 8. Audit log (CR 1.1 verbatim — same transaction, after the
        #    state change is flushed but before COMMIT).
        await emit_audit_typed(
            session=self._session,
            action_class=ActionClass.TENANT,
            action="tenant_signup_completed",
            tenant_id=tenant_id,
            actor_id=user_id,
            target_table="tenants",
            target_id=tenant_id,
            reason="phase-3-0 atomic signup",
            payload={
                "tenant_name": name_clean,
                "industry": industry.value,
                "owner_user_id": str(user_id),
            },
        )

        # 9. COMMIT happens at session scope (handlers.py uses the
        #    get_session dep which manages commit/rollback).

        return SignupCompletion(
            tenant_id=tenant_id,
            role="owner",
            industry=industry,
            settings_version=1,
            trace_id=self._trace_id,
        )

    async def _get_or_create_user_row(
        self,
        *,
        user_id: uuid.UUID,
        user_email: str | None,
    ) -> None:
        """Ensure a `public.users` row exists for the given auth.users id.

        Idempotent: if the row already exists, no-op. If not, INSERT
        with role='owner' (default for fresh signups) and email from
        Supabase JWT (or a placeholder if unavailable — required NOT NULL).
        """
        existing = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        if existing.scalar_one_or_none() is not None:
            return  # already provisioned

        # users.email is NOT NULL UNIQUE. If we don't have an email
        # (shouldn't happen — Supabase always provides one), fall back
        # to a placeholder that includes the user_id to avoid collisions
        # across multiple no-email signups in tests/dev.
        email = user_email or f"unknown-{user_id}@signup.invalid"
        user_row = User(
            id=user_id,
            tenant_id=None,  # cross-tenant user; set via membership only
            email=email,
            role="owner",
            twofa_enabled=False,
            created_at=datetime.now(UTC),
        )
        self._session.add(user_row)
        await self._session.flush()
