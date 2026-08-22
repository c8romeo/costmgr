"""apps.api.modules.auth.audit_routes — Auth audit-first INSERT endpoints.

Epic 15 — auth audit endpoint (AC #1.5, #2.5, #3.7) — F17.1+F17.2.

The frontend wrappers (magic-link.ts, social.ts) call these endpoints
to record CR 1-1 audit-first INSERT events in `audit_logs`. The
endpoints accept minimal payloads (target_email for magic link,
provider for social OAuth) and emit a typed `AUTH` audit row.

Security:
  - Endpoints are mounted under `/api/v1/auth/audit/*` (no Supabase
    JWT required at the gateway level — the backend service role is
    used to write to audit_logs, mirroring the m0_onboarding signup
    pattern).
  - The `target_email` is hashed in the audit row's `details` to
    avoid PII leakage in the audit log.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from apps.api.core.db import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth/audit", tags=["auth-audit"])


# ── Pydantic schemas ────────────────────────────────────────────────


class MagicLinkAuditRequest(BaseModel):
    target_email: str = Field(..., min_length=3, max_length=320)


class SocialOAuthAuditRequest(BaseModel):
    provider: str = Field(..., min_length=1, max_length=32)


def _email_fingerprint(email: str) -> str:
    """Stable but non-reversible fingerprint of an email for the audit row.

    We do NOT store the raw email in the audit log — PII minimization
    (NFR4) is preserved. The fingerprint lets us correlate multiple
    audit events for the same user without exposing the address.
    """
    salt = b"costmgr-auth-audit-salt"
    return hashlib.sha256(salt + email.strip().lower().encode("utf-8")).hexdigest()[:16]


# ── POST /magic-link-sent ────────────────────────────────────────────


@router.post("/magic-link-sent")
async def record_magic_link_sent(
    payload: MagicLinkAuditRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Record the `magic_link_sent` audit-first INSERT (AC #1.5).

    The audit row carries a non-reversible email fingerprint + the
    client IP. We never store the raw email in the audit log.
    """
    client_ip = request.client.host if request.client else "unknown"
    fingerprint = _email_fingerprint(payload.target_email)
    await emit_audit_typed(
        session=session,
        action_class=ActionClass.AUTH,
        action="magic_link_sent",
        target_id=uuid.UUID(int=0),  # no specific user yet (link not clicked)
        target_table="auth_event",
        actor_id=None,
        details={
            "email_fingerprint": fingerprint,
            "client_ip": client_ip,
        },
    )
    return {"code": "OK", "message_ko": "감사 로그 기록 완료"}


# ── POST /social-oauth-initiated ─────────────────────────────────────


@router.post("/social-oauth-initiated")
async def record_social_oauth_initiated(
    payload: SocialOAuthAuditRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Record the `social_oauth_initiated` audit-first INSERT (AC #2.5)."""
    client_ip = request.client.host if request.client else "unknown"
    await emit_audit_typed(
        session=session,
        action_class=ActionClass.AUTH,
        action="social_oauth_initiated",
        target_id=uuid.UUID(int=0),
        target_table="auth_event",
        actor_id=None,
        details={
            "provider": payload.provider,
            "client_ip": client_ip,
        },
    )
    return {"code": "OK", "message_ko": "감사 로그 기록 완료"}
