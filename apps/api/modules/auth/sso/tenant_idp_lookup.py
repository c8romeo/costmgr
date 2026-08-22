"""apps.api.modules.auth.sso.tenant_idp_lookup — Per-tenant IdP config lookup.

Epic 16 (cj-style 69번째 epic 연속 정직 회복 wire) — T5 (AC #5.1~#5.5) — F19.5.

SAML response validation now reads the tenant's IdP X509 cert dynamically
from the `tenant_idps` table (alembic 0038) instead of the Epic 15
hardcoded placeholder. The SAML request store lookup yields a tenant_slug;
this module resolves the corresponding IdP row.

Capability-gated: per-tenant `enabled` flag is honored — a disabled IdP
row blocks `/login` and `/acs` with a typed envelope.

CR 0-2 RLS lesson: tenant_id is enforced via `current_setting('app.tenant_id')`
GUC set by the dependency tree. Direct queries without GUC set must NOT
bypass RLS — so we use the SECURITY DEFINER pattern from `apps.api.core.db`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ── Typed exceptions ─────────────────────────────────────────────────


class TenantIdPLookupError(Exception):
    """Base class for per-tenant IdP lookup failures."""


class TenantIdPDisabledError(TenantIdPLookupError):
    """IdP row found but enabled=FALSE."""


class TenantIdPConfigMissingError(TenantIdPLookupError):
    """No IdP row for this tenant."""


# ── Return type ──────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class TenantIdPRow:
    """Per-tenant IdP config snapshot (read-only)."""

    tenant_id: str
    tenant_slug: str
    idp_entity_id: str
    idp_sso_url: str
    idp_slo_url: str | None
    idp_x509_cert_pem: str
    name_id_format: str | None
    acs_url: str | None
    enabled: bool


# ── Public API ───────────────────────────────────────────────────────


async def load_tenant_idp(
    session: AsyncSession,
    tenant_slug: str,
) -> TenantIdPRow:
    """Load a tenant's IdP config by slug.

    Resolution order:
      1. SELECT tenant_id from public.tenants WHERE slug = :slug
      2. SELECT tenant_idps WHERE tenant_id = :tenant_id
      3. If missing row → TenantIdPConfigMissingError
      4. If enabled=FALSE → TenantIdPDisabledError
      5. Return TenantIdPRow

    The query is read-only and respects the RLS policy on tenant_idps
    (CR 0-2 verbatim: `current_setting('app.tenant_id')`).
    """
    # Step 1: resolve tenant_id from slug.
    tenant_row = (
        await session.execute(
            text("SELECT id FROM public.tenants WHERE slug = :slug LIMIT 1"),
            {"slug": tenant_slug},
        )
    ).first()
    if tenant_row is None:
        raise TenantIdPConfigMissingError(f"tenant_not_found: {tenant_slug}")

    tenant_id = str(tenant_row[0])

    # Step 2: read tenant_idps row.
    idp_row = (
        await session.execute(
            text(
                """
                SELECT idp_entity_id, idp_sso_url, idp_slo_url,
                       idp_x509_cert, name_id_format, acs_url, enabled
                FROM public.tenant_idps
                WHERE tenant_id = :tenant_id
                LIMIT 1
                """
            ),
            {"tenant_id": tenant_id},
        )
    ).first()

    if idp_row is None:
        raise TenantIdPConfigMissingError(f"idp_not_configured: {tenant_slug}")

    enabled = bool(idp_row[6])
    if not enabled:
        raise TenantIdPDisabledError(f"idp_disabled: {tenant_slug}")

    return TenantIdPRow(
        tenant_id=tenant_id,
        tenant_slug=tenant_slug,
        idp_entity_id=idp_row[0],
        idp_sso_url=idp_row[1],
        idp_slo_url=idp_row[2],
        idp_x509_cert_pem=idp_row[3],
        name_id_format=idp_row[4],
        acs_url=idp_row[5],
        enabled=enabled,
    )


__all__ = [
    "TenantIdPLookupError",
    "TenantIdPDisabledError",
    "TenantIdPConfigMissingError",
    "TenantIdPRow",
    "load_tenant_idp",
]
