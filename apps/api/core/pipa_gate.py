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

import os
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
    # EU = "EU"  # post-MVP — when Anthropic ships EU-hosted inference  # noqa: ERA001
    # US = "US"  # explicitly NOT allowed under MVP PIPA rules  # noqa: ERA001


_PIPA_ALLOWED_REGIONS: Final[frozenset[PipaRegion]] = frozenset({PipaRegion.KR})


# ── Operations kill-switch (Epic 1 회고 A3 + Epic 3 회고 A1) ─────
# When `PIPA_REVIEW_COMPLETED=false`, the gate is FORCE-CLOSED regardless
# of per-tenant consent. This is the operations-level safety switch the
# team can flip before/after a legal review of cross-border AI processing.
# Default behavior: unset / "true" / "1" → fall through to per-tenant check
# (backward compatible). Explicit "false" / "0" → 503 PIPA_REVIEW_REQUIRED
# for all M10 routes.
PIPA_REVIEW_COMPLETED_ENV: Final[str] = "PIPA_REVIEW_COMPLETED"
_PIPA_KILL_SWITCH_VALUES: Final[frozenset[str]] = frozenset({"false", "0", "False", "FALSE"})


def pipa_review_completed() -> bool:
    """Pure helper — is the operations-level PIPA review flag ON?

    Reads `PIPA_REVIEW_COMPLETED` env var at call time. Returns True
    unless the value is explicitly a kill-switch value (`false`/`0`).

    Called by `require_pipa_review` BEFORE the per-tenant check so
    operations can disable cross-border AI processing fleet-wide.

    The env-var is read at function call time (not module load) so
    tests can monkey-patch `os.environ` without re-importing.
    """
    raw = os.environ.get(PIPA_REVIEW_COMPLETED_ENV, "true").strip()
    return raw not in _PIPA_KILL_SWITCH_VALUES


# ── Typed exceptions (mapped to 451 / 503 by main.py) ──────────
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


class PipaReviewRequiredError(Exception):
    """503 PIPA_REVIEW_REQUIRED — operations kill-switch ON.

    Raised when `PIPA_REVIEW_COMPLETED=false` is set at the operations
    level. The PIPA review has not been completed (or has been suspended)
    so cross-border AI processing is denied fleet-wide regardless of
    per-tenant consent. Operators set this when:
    - DPA negotiations are in progress with the AI provider.
    - A legal review is required before resuming processing.
    - An incident requires pausing cross-border AI.
    """

    def __init__(self, *, trace_id: str) -> None:
        super().__init__("PIPA review not completed (operations kill-switch ON)")
        self.trace_id = trace_id


# ── Public dependency ───────────────────────────────────────
async def require_pipa_review(
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> TenantContext:
    """FastAPI dependency — gate the M10 routes on PIPA consent + region.

    Two-layer check:
    1. **Operations kill-switch** (`PIPA_REVIEW_COMPLETED=false`) — 503
       `PIPA_REVIEW_REQUIRED` if set. Fleet-wide safety switch.
    2. **Per-tenant consent** — reads `tenant_settings.onboarding.pipa_consent`
       and `pipa_region`. Both must be present and consent must be True;
       region must be in `_PIPA_ALLOWED_REGIONS`. 451 otherwise.

    Returns the `TenantContext` so the route can use it directly.
    Raises `PipaReviewRequiredError` (503) or `PipaConsentMissingError`
    (451) otherwise.
    """
    trace_id = str(uuid.uuid4())

    # ── Layer 1: operations kill-switch (Epic 1 회고 A3 + Epic 3 회고 A1) ──
    if not pipa_review_completed():
        raise PipaReviewRequiredError(trace_id=trace_id)

    # ── Layer 2: per-tenant consent (Story 1.3) ────────────────
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
