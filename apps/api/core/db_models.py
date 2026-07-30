"""apps.api.core.db_models — SQLAlchemy 2.0 ORM models (Story 0.2).

Mapped tables (defined in `apps/api/alembic/versions/0001_*.py`):
- tenants, users, tenant_memberships, tenant_settings, audit_logs

Per AD-1/AD-11: this module is in `apps/api/` (infra layer). It does NOT
import `packages.cost_engine` directly. Modules write through services.

Per AD-15: snake_case column names; UUID v7 for new business entities (the
initial schema uses `gen_random_uuid()` v4 — UUID v7 is added in a later
migration per ADR).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Common ORM base for all apps/api models."""


# ── tenants ────────────────────────────────────────────────
class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    industry: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "industry IN ('manufacturing', 'manufacturing_retail', 'service', 'mixed')",
            name="tenants_industry_check",
        ),
    )


# ── users ──────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    # tenant_id is NULLABLE for cross-tenant users (e.g. consultant_proxy
    # before they join a tenant). RLS policy filters to current tenant when
    # tenant_id IS NOT NULL.
    tenant_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
    )
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    twofa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "role IN ('owner', 'member', 'viewer', 'consultant_proxy')",
            name="users_role_check",
        ),
    )


# ── tenant_memberships ─────────────────────────────────────
class TenantMembership(Base):
    __tablename__ = "tenant_memberships"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(Text, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="tenant_memberships_tenant_user_key"),
    )


# ── tenant_settings (AD-23) ───────────────────────────────
class TenantSettings(Base):
    __tablename__ = "tenant_settings"

    tenant_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        primary_key=True,
    )
    settings_version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=1
    )  # F-17: BigInteger to prevent int4 overflow on long-lived tenants
    onboarding: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    baseline: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    abc: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    ai: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


# ── audit_logs (AD-2) ─────────────────────────────────────
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    target_table: Mapped[str] = mapped_column(Text, nullable=False)
    target_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
