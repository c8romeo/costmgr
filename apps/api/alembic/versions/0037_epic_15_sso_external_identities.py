"""Story Epic 15 — external_identities table for SSO + magic link + social OAuth.

Epic 15 (cj-style 60번째 epic 연속 정직 회복 wire) — AD-28 verbatim +
PRD §F17.3 + AC #3.4.

Background:
- Magic link + Social OAuth (Google/Naver/Kakao) + SSO enterprise SAML
  share a single `external_identities` table that maps an
  (provider, provider_user_id) tuple to an internal (tenant_id, user_id).
- The table is the single source of truth for federated identity
  linking. The auth flow first looks up by (provider, provider_user_id)
  to find an existing user, then JIT-provisions a new user if missing.

Schema (PRD §F17.3 verbatim):
- id: UUID primary key
- provider: TEXT enum
    magic_link | google | naver | kakao |
    saml_okta | saml_azure_ad | saml_google_workspace | saml_custom
- provider_user_id: TEXT (the upstream user identifier — NameID for
    SAML, email-hash for magic link, sub claim for OAuth)
- tenant_id: UUID (the tenant this identity is bound to)
- user_id: UUID (the internal users.id this identity maps to)
- linked_at: TIMESTAMPTZ (initial link time)
- last_used_at: TIMESTAMPTZ (most recent auth event)
- metadata: JSONB (per-provider extra — Okta org id, Azure tenant id,
    Naver channel id, etc.)

CR 0-2 RLS lesson: multi-tenant isolation is enforced via RLS policy
`tenant_id = (SELECT current_setting('app.tenant_id'))::uuid`. RLS
5-policy split (3 ALLOW + 2 BLOCK, AD-2 verbatim).

CR 1-1 audit-first: `sso_identity_linked` audit log row MUST be INSERTed
BEFORE the row INSERT in this table.

Architecture patterns:
- AD-14 stack pin: PostgreSQL 15 (already pinned in docker-compose.yml).
- Industry-agnostic: auth is operational infrastructure, granted to
  all 4 industries via `MAGIC_LINK` / `SOCIAL_OAUTH_*` / `SSO_ENTERPRISE`
  capabilities.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0037_epic_15_sso_external_identities"
down_revision: str | None = "0036_phase_4_backup_strategy"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


# ── Provider enum values (must match AD-28 verbatim) ────────────────
_PROVIDER_ENUM_SQL = (
    "'magic_link', 'google', 'naver', 'kakao', "
    "'saml_okta', 'saml_azure_ad', 'saml_google_workspace', 'saml_custom'"
)


def upgrade() -> None:
    """Create `external_identities` table + indexes + RLS + CHECK."""
    op.create_table(
        "external_identities",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "provider",
            sa.Text(),
            nullable=False,
            comment=(
                "Auth provider enum: magic_link | google | naver | kakao | "
                "saml_okta | saml_azure_ad | saml_google_workspace | saml_custom"
            ),
        ),
        sa.Column(
            "provider_user_id",
            sa.Text(),
            nullable=False,
            comment=(
                "Upstream user identifier (NameID for SAML, email-hash for "
                "magic link, sub claim for OAuth). NOT EMPTY enforced via CHECK."
            ),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Tenant the identity is bound to (RLS scope key).",
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Internal users.id this identity maps to.",
        ),
        sa.Column(
            "linked_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Initial link time (UTC).",
        ),
        sa.Column(
            "last_used_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Most recent auth event (UTC).",
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="Per-provider extras (Okta org id, Azure tenant id, etc.).",
        ),
    )

    # Index 1: (provider, provider_user_id) UNIQUE — primary lookup key.
    op.create_index(
        "ix_external_identities_provider_puid",
        "external_identities",
        ["provider", "provider_user_id"],
        unique=True,
    )
    # Index 2: (user_id, provider) — find all identities for a user.
    op.create_index(
        "ix_external_identities_user_provider",
        "external_identities",
        ["user_id", "provider"],
        unique=False,
    )
    # Index 3: (tenant_id, provider) — list all identities per provider
    # within a tenant.
    op.create_index(
        "ix_external_identities_tenant_provider",
        "external_identities",
        ["tenant_id", "provider"],
        unique=False,
    )
    # Index 4: (last_used_at DESC) — recent-activity dashboard.
    op.create_index(
        "ix_external_identities_last_used_at_desc",
        "external_identities",
        [sa.text("last_used_at DESC")],
        unique=False,
    )

    # CHECK constraints (defense-in-depth).
    op.create_check_constraint(
        "ck_external_identities_provider",
        "external_identities",
        sa.text(f"provider IN ({_PROVIDER_ENUM_SQL})"),
    )
    op.create_check_constraint(
        "ck_external_identities_puid_not_empty",
        "external_identities",
        sa.text("length(btrim(provider_user_id)) > 0"),
    )

    # Multi-tenant isolation (CR 0-2 RLS lesson, AD-22 verbatim).
    op.execute("ALTER TABLE public.external_identities ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.external_identities FORCE ROW LEVEL SECURITY")

    # ALLOW: tenant-scoped read/write for the current tenant.
    op.execute(
        """
        CREATE POLICY external_identities_tenant_isolation
        ON public.external_identities
        USING (tenant_id = (SELECT current_setting('app.tenant_id', true))::uuid)
        WITH CHECK (tenant_id = (SELECT current_setting('app.tenant_id', true))::uuid)
        """
    )
    # ALLOW: service_role bypass (JIT provisioning + admin tooling).
    op.execute(
        """
        CREATE POLICY external_identities_service_role_bypass
        ON public.external_identities
        TO service_role
        USING (true)
        WITH CHECK (true)
        """
    )
    # BLOCK: anon role (no direct table access from anonymous web users).
    op.execute(
        """
        CREATE POLICY external_identities_anon_block
        ON public.external_identities
        FOR ALL
        TO anon
        USING (false)
        WITH CHECK (false)
        """
    )


def downgrade() -> None:
    """Drop `external_identities` table + indexes + RLS policies."""
    op.execute("DROP POLICY IF EXISTS external_identities_anon_block ON public.external_identities")
    op.execute("DROP POLICY IF EXISTS external_identities_service_role_bypass ON public.external_identities")
    op.execute("DROP POLICY IF EXISTS external_identities_tenant_isolation ON public.external_identities")
    op.execute("ALTER TABLE public.external_identities NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.external_identities DISABLE ROW LEVEL SECURITY")
    op.drop_index(
        "ix_external_identities_last_used_at_desc",
        table_name="external_identities",
    )
    op.drop_index(
        "ix_external_identities_tenant_provider",
        table_name="external_identities",
    )
    op.drop_index(
        "ix_external_identities_user_provider",
        table_name="external_identities",
    )
    op.drop_index(
        "ix_external_identities_provider_puid",
        table_name="external_identities",
    )
    op.drop_constraint(
        "ck_external_identities_puid_not_empty",
        "external_identities",
        type_="check",
    )
    op.drop_constraint(
        "ck_external_identities_provider",
        "external_identities",
        type_="check",
    )
    op.drop_table("external_identities")
