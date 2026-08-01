"""apps.api.core.pipa_gate — Korean PIPA cross-border AI processing gate.

Story 1.3 — Task 2.4.

Korean PIPA (Personal Information Protection Act) restricts cross-border
transfer of personal data without explicit consent. Since Story 1.3
uploads user documents to Anthropic's API (US-hosted), the M10 routes
MUST enforce that:

1. The tenant has `onboarding.pipa_consent=true` AND
2. The tenant is in a `pipa_allowed_region` (MVP: KR-only — operators
   can later extend the allow-list as Anthropic adds EU regions).

Without the consent, the upload is rejected with 451 LEGAL_REASONS
(HTTP "Unavailable for Legal Reasons") — the typed envelope is AD-15
compliant.

Anti-pattern guards:
- The gate is a FastAPI DEPENDENCY (not a check inside the handler)
  so cross-border processing is rejected at the FIRST line of defense
  before the body is even parsed.
- The dependency reads `tenant_settings.onboarding.pipa_consent` so
  consent is auditable and tied to the same settings_version as
  industry / fiscal-year-start.
- The dependency fails closed — `pipa_consent` missing OR False is the
  same: deny.

Future work (out of scope for Story 1.3):
- Per-document consent (vs per-tenant).
- Cross-region fallback (EU-hosted Anthropic).
- DPA storage + rotation reminders.
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Final

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.db import get_session
from apps.api.core.tenant_context import TenantContext, get_tenant_context


# ── Allow-list ───────────────────────────────────────────────
class PipaRegion(str, Enum):
    """Regions where PIPA allows cross-border AI processing.

    MVP: KR only. The tenant's `onboarding.pipa_region` is checked
    against this set.
    """

    KR = "KR"
    # EU = "EU"  # post-MVP — when Anthropic ships EU-hosted inference
    # US = "US"  # explicitly NOT allowed under MVP PIPA rules


_PIPA_ALLOWED_REGIONS: Final[frozenset[PipaRegion]] = frozenset({PipaRegion.KR})


# ── Typed exception (mapped to 451 by handlers.py) ─────────
class PipaConsentMissingError(Exception):
    """451 PIPA_CONSENT_MISSING — tenant has not consented to cross-border AI."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        trace_id: str,
        reason: str,  # 'consent_missing' | 'region_not_allowed'
    ) -> None:
        super().__init__(f"PIPA gate denied: {reason}")
        self.tenant_id = tenant_id
        self.trace_id = trace_id
        self.reason = reason


# ── Public dependency ───────────────────────────────────────
async def require_pipa_review(
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> TenantContext:
    """FastAPI dependency — gate the M10 routes on PIPA consent + region.

    Reads `tenant_settings.onboarding.pipa_consent` and
    `tenant_settings.onboarding.pipa_region`. Both must be present and
    consent must be True; region must be in `_PIPA_ALLOWED_REGIONS`.

    Returns the `TenantContext` so the route can use it directly.
    Raises `PipaConsentMissingError` (451 LEGAL_REASONS) otherwise.
    """
    trace_id = str(uuid.uuid4())

    # Lazy import — settings_service may not exist at import time
    # in tests that only exercise this module.
    from apps.api.modules.m0_onboarding.services.settings_service import (
        SettingsService,
        TenantSettingsNotFoundError,
    )

    service = SettingsService(session, trace_id=trace_id)
    try:
        row = await service.get_tenant_settings(tenant_id=ctx.tenant_id)
    except TenantSettingsNotFoundError as err:
        # No settings row → no consent → deny. Fails closed.
        raise PipaConsentMissingError(
            tenant_id=ctx.tenant_id,
            trace_id=trace_id,
            reason="consent_missing",
        ) from err

    onboarding = dict(row.onboarding or {})
    consent = bool(onboarding.get("pipa_consent", False))
    region_raw = onboarding.get("pipa_region")
    if not consent:
        raise PipaConsentMissingError(
            tenant_id=ctx.tenant_id,
            trace_id=trace_id,
            reason="consent_missing",
        )
    if region_raw is None:
        raise PipaConsentMissingError(
            tenant_id=ctx.tenant_id,
            trace_id=trace_id,
            reason="region_not_allowed",
        )
    try:
        region = PipaRegion(region_raw)
    except ValueError as err:
        raise PipaConsentMissingError(
            tenant_id=ctx.tenant_id,
            trace_id=trace_id,
            reason="region_not_allowed",
        ) from err
    if region not in _PIPA_ALLOWED_REGIONS:
        raise PipaConsentMissingError(
            tenant_id=ctx.tenant_id,
            trace_id=trace_id,
            reason="region_not_allowed",
        )
    return ctx


def pipa_region_allowed(region: PipaRegion) -> bool:
    """Pure helper — is this region in the cross-border allow-list?"""
    return region in _PIPA_ALLOWED_REGIONS
