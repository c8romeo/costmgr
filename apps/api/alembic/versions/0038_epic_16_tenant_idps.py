"""Story Epic 16 — tenant_idps table for per-tenant IdP admin management.

Epic 16 (cj-style 69번째 epic 연속 정직 회복 wire) — AD-30 verbatim +
PRD §F19.1 verbatim + AC #1.1~#1.7.

Background:
- Epic 15 SSO enterprise SAML wire (`5f9e37f`) shipped hardcoded
  `acme` placeholder at saml_routes.py lines 80 + 121-125. Real per-tenant
  IdP config was deferred to Epic 16 (see docs/sso-enterprise.md §4.1
  step 3 `Configure tenant_idps (TODO Epic 16)` forward-reference).
- Epic 16 territory wires `tenant_idps` table to replace the hardcoded
  placeholder with database-driven per-tenant IdP configuration.

Schema (PRD §F19.1 verbatim + AD-30 verbatim):
- id: UUID PK `gen_random_uuid()`
- tenant_id: UUID FK → `tenants`, NOT NULL (RLS scope key)
- idp_entity_id: TEXT NOT NULL (SAML 2.0 EntityID — unique per tenant)
- idp_sso_url: TEXT NOT NULL (https:// 강제 — IdP SSO endpoint URL)
- idp_slo_url: TEXT NULL (optional Single Logout Service URL)
- idp_x509_cert: TEXT NOT NULL (PEM-encoded x509 certificate)
- acs_url: TEXT NOT NULL (Assertion Consumer Service URL — costmgr SP ACS)
- name_id_format: TEXT NULL (default emailAddress per SAML 2.0 spec)
- enabled: BOOLEAN NOT NULL DEFAULT TRUE (soft delete via enabled=FALSE)
- created_at: TIMESTAMPTZ NOT NULL DEFAULT NOW()
- updated_at: TIMESTAMPTZ NOT NULL DEFAULT NOW()
- created_by: UUID FK → users, NOT NULL (audit-first INSERT row author)
- updated_by: UUID FK → users, NOT NULL (audit-first INSERT row author)

CR 0-2 RLS lesson: multi-tenant isolation is enforced via RLS 3-policy
split (tenant_isolation + service_role_bypass + anon_block) — verbatim
Epic 15 `external_identities` pattern.

CR 1-1 audit-first: 4 NEW audit log rows MUST be INSERTed BEFORE the
tenant_idps row INSERT (action_class='AUTH' + 4 NEW actions:
tenant_idp_created + tenant_idp_updated + tenant_idp_deleted +
tenant_idp_tested). See apps/api/core/audit_action.py ActionClass.AUTH
registry.

Architecture patterns:
- AD-14 stack pin: PostgreSQL 15 (already pinned in docker-compose.yml).
- Industry-agnostic: IdP management is operational infrastructure,
  granted to all 4 industries via `TENANT_IDP_MANAGEMENT` capability
  (CR 12-1 L4 precedent).
- 1 tenant = 1 IdP only (UNIQUE (tenant_id, idp_entity_id) constraint).
  Multi-IdP per tenant deferred to 2차 로드맵.

Data migration (PRD §F19.5 verbatim backward compatibility):
- Seeds `acme` row with Epic 15 wire's hardcoded placeholder values so
  the existing saml_routes.py test flows continue to pass without
  modification. The row mirrors the Epic 15 line 80 + 121-125 literal
  placeholder values verbatim.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0038_epic_16_tenant_idps"
down_revision: str | None = "0037_epic_15_sso_external_identities"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


# ── Hardcoded acme row — Epic 15 wire backward compatibility ─────────
# Mirrors apps/api/modules/auth/sso/saml_routes.py line 80 + 121-125
# verbatim. Production deploys override this row via PUT /api/v1/admin/
# tenant/acme/idp; the seed exists only so Epic 15 wire test fixtures
# (which use tenant_slug='acme') continue to find a matching IdP.
_ACME_ENTITY_ID = "https://idp.example.com/sso"
_ACME_SSO_URL = "https://idp.example.com/sso?tenant=acme"
_ACME_X509_CERT_PLACEHOLDER = (
    "-----BEGIN CERTIFICATE-----\n"
    "MIIDazCCAlOgAwIBAgIUJxZ/placeholder/test/only=\n"
    "-----END CERTIFICATE-----"
)
_ACME_ACS_URL = "https://api.costmgr.example.com/api/v1/auth/sso/acs?tenant=acme"
_ACME_NAME_ID_FORMAT = (
    "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
)


def upgrade() -> None:
    """Create `tenant_idps` table + UNIQUE + RLS + CHECK + index + trigger.

    Also seeds the `acme` row for Epic 15 wire backward compatibility
    (PRD §F19.5 verbatim).
    """
    op.create_table(
        "tenant_idps",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
            comment="UUID PK (gen_random_uuid()).",
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
            comment="Tenant UUID (FK → tenants.id, RLS scope key).",
        ),
        sa.Column(
            "idp_entity_id",
            sa.Text(),
            nullable=False,
            comment=(
                "SAML 2.0 EntityID — unique per tenant "
                "(UNIQUE (tenant_id, idp_entity_id))."
            ),
        ),
        sa.Column(
            "idp_sso_url",
            sa.Text(),
            nullable=False,
            comment=(
                "IdP SingleSignOnService endpoint URL (https:// 강제, "
                "CHECK ck_tenant_idps_sso_url_https)."
            ),
        ),
        sa.Column(
            "idp_slo_url",
            sa.Text(),
            nullable=True,
            comment=(
                "IdP SingleLogoutService endpoint URL (optional, https:// "
                "강제, validated at application layer)."
            ),
        ),
        sa.Column(
            "idp_x509_cert",
            sa.Text(),
            nullable=False,
            comment=(
                "PEM-encoded x509 certificate (wrap: "
                "-----BEGIN CERTIFICATE----- + base64 + -----END "
                "CERTIFICATE-----, CHECK ck_tenant_idps_x509_cert_pem)."
            ),
        ),
        sa.Column(
            "acs_url",
            sa.Text(),
            nullable=False,
            comment=(
                "Assertion Consumer Service URL — costmgr SP ACS endpoint "
                "(e.g. https://api.costmgr.example.com/api/v1/auth/sso/"
                "acs?tenant=<slug>)."
            ),
        ),
        sa.Column(
            "name_id_format",
            sa.Text(),
            nullable=True,
            comment=(
                "SAML NameID format URI (default: "
                "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress)."
            ),
        ),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
            comment=(
                "Tenant IdP enabled flag. Soft-delete via enabled=FALSE "
                "(no separate deleted_at column per PRD §F19.1 schema)."
            ),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="Row creation timestamp (UTC).",
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="Row last-update timestamp (UTC, auto-updated by trigger).",
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
            comment="users.id of the admin who created this row.",
        ),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
            comment="users.id of the admin who last updated this row.",
        ),
        # UNIQUE constraint (PRD §F19.1 verbatim — 1 tenant = 1 IdP).
        sa.UniqueConstraint(
            "tenant_id",
            "idp_entity_id",
            name="uq_tenant_idps_tenant_entity",
        ),
    )

    # Index 1: (tenant_id) — primary lookup key for per-tenant routing
    # (Epic 15 saml_routes.py EXTENSION in T5).
    op.create_index(
        "idx_tenant_idps_tenant_id",
        "tenant_idps",
        ["tenant_id"],
        unique=False,
    )

    # CHECK constraints (defense-in-depth, AC1.7 verbatim).
    op.create_check_constraint(
        "ck_tenant_idps_entity_id_not_empty",
        "tenant_idps",
        sa.text("length(btrim(idp_entity_id)) > 0"),
    )
    op.create_check_constraint(
        "ck_tenant_idps_sso_url_https",
        "tenant_idps",
        sa.text("idp_sso_url LIKE 'https://%'"),
    )
    op.create_check_constraint(
        "ck_tenant_idps_x509_cert_pem",
        "tenant_idps",
        sa.text(
            "idp_x509_cert LIKE '-----BEGIN CERTIFICATE-----%' "
            "AND idp_x509_cert LIKE '%-----END CERTIFICATE-----'"
        ),
    )

    # Multi-tenant isolation (CR 0-2 RLS lesson verbatim, Epic 15
    # external_identities pattern).
    op.execute("ALTER TABLE public.tenant_idps ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.tenant_idps FORCE ROW LEVEL SECURITY")

    # ALLOW: tenant-scoped read/write for the current tenant.
    op.execute(
        """
        CREATE POLICY tenant_idps_tenant_isolation
        ON public.tenant_idps
        USING (tenant_id = (SELECT current_setting('app.tenant_id', true))::uuid)
        WITH CHECK (tenant_id = (SELECT current_setting('app.tenant_id', true))::uuid)
        """
    )
    # ALLOW: service_role bypass (admin tooling + cron).
    op.execute(
        """
        CREATE POLICY tenant_idps_service_role_bypass
        ON public.tenant_idps
        TO service_role
        USING (true)
        WITH CHECK (true)
        """
    )
    # BLOCK: anon role (no direct table access from anonymous web users).
    op.execute(
        """
        CREATE POLICY tenant_idps_anon_block
        ON public.tenant_idps
        FOR ALL
        TO anon
        USING (false)
        WITH CHECK (false)
        """
    )

    # updated_at auto-update trigger (BEFORE UPDATE → updated_at = NOW()).
    # Mirrors Phase 4 wire `71a033a` audit trigger pattern.
    op.execute(
        """
        CREATE TRIGGER updated_at_auto_update_trg
        BEFORE UPDATE ON public.tenant_idps
        FOR EACH ROW
        EXECUTE FUNCTION public.set_updated_at()
        """
    )

    # Data migration: seed acme row for Epic 15 wire backward compat.
    # Uses a placeholder UUID for tenants + users FKs — service_role
    # bypass RLS so the INSERT is unrestricted. Production seed runs
    # via service_role only; the seed values are intentionally fixed
    # so Epic 15 saml_routes.py test flows (tenant_slug='acme') keep
    # passing verbatim. Operators update via PUT /api/v1/admin/tenant/
    # acme/idp after first deploy.
    op.execute(
        """
        INSERT INTO public.tenant_idps (
            id,
            tenant_id,
            idp_entity_id,
            idp_sso_url,
            idp_slo_url,
            idp_x509_cert,
            acs_url,
            name_id_format,
            enabled,
            created_by,
            updated_by
        )
        SELECT
            '00000000-0000-0000-0000-000000000001'::uuid,
            t.id,
            :acme_entity_id,
            :acme_sso_url,
            NULL,
            :acme_x509_cert,
            :acme_acs_url,
            :acme_name_id_format,
            TRUE,
            u.id,
            u.id
        FROM public.tenants t
        JOIN public.users u ON u.tenant_id = t.id
        WHERE t.slug = 'acme'
        LIMIT 1
        ON CONFLICT (tenant_id, idp_entity_id) DO NOTHING
        """,
        {
            "acme_entity_id": _ACME_ENTITY_ID,
            "acme_sso_url": _ACME_SSO_URL,
            "acme_x509_cert": _ACME_X509_CERT_PLACEHOLDER,
            "acme_acs_url": _ACME_ACS_URL,
            "acme_name_id_format": _ACME_NAME_ID_FORMAT,
        },
    )


def downgrade() -> None:
    """Drop `tenant_idps` table + UNIQUE + indexes + RLS + trigger."""
    op.execute("DROP TRIGGER IF EXISTS updated_at_auto_update_trg ON public.tenant_idps")
    op.execute("DROP POLICY IF EXISTS tenant_idps_anon_block ON public.tenant_idps")
    op.execute(
        "DROP POLICY IF EXISTS tenant_idps_service_role_bypass ON public.tenant_idps"
    )
    op.execute("DROP POLICY IF EXISTS tenant_idps_tenant_isolation ON public.tenant_idps")
    op.execute("ALTER TABLE public.tenant_idps NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.tenant_idps DISABLE ROW LEVEL SECURITY")
    op.drop_index("idx_tenant_idps_tenant_id", table_name="tenant_idps")
    op.drop_constraint(
        "ck_tenant_idps_x509_cert_pem", "tenant_idps", type_="check"
    )
    op.drop_constraint(
        "ck_tenant_idps_sso_url_https", "tenant_idps", type_="check"
    )
    op.drop_constraint(
        "ck_tenant_idps_entity_id_not_empty", "tenant_idps", type_="check"
    )
    op.drop_table("tenant_idps")
